"""#18: is the board's K/DEF projection the same artifact as Sleeper's weekly one? No network.

Run from the repo root. Needs the 2026 projections capture, because the board's CSVs are dated
2026-08-25 and only a SAME-SEASON comparison can speak to lineage -- comparing a 2026 CSV against
2024 weekly projections would report the difference between two seasons and call it a difference
between two sources.

WHY IT MATTERS. `measure_projection_accuracy` measures /projections/nfl. The board prices K and DEF
from two committed CSVs (draft_room.KDST_SEEDED_SOURCE_FILES). The module's docstring asserted for
a long time that these are the same source, so every K and DEF reliability number ever produced was
taken to be about the board's input. If they are different artifacts, none of them were.

TWO QUESTIONS, AND THEY HAVE DIFFERENT ANSWERS.

  1. Are the two artifacts the same? Pearson r between the CSV's projection and the weekly sum,
     joined player by player. Same artifact (or a rescale of one) gives r ~ 1.0.
  2. Does a projection predict ORDERING inside the starting band -- the only band a draft
     discriminates in? Spearman rank correlation of projected against REALIZED, over seasons that
     have finished. This one is about the sport, not about lineage, and it is the question #18 was
     really asking all along.

READ THE STANDARD ERRORS. A rank correlation over a twelve-player band has se ~ 1/sqrt(n-3) ~ 0.33.
Two seasons of it is two numbers. Nothing here separates 0.2 from 0.5, and the report prints the
se next to the estimate so that no one reads a gap that size as a finding.
"""

from __future__ import annotations

import collections
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import player_universe as pu
import run_draft_battery as rdb

CSV_DIR = Path("data/baseline/rankings")
CSV_FILES = {"DEF": "sleeper_dst_projections.csv", "K": "sleeper_kicker_projections.csv"}

#: The CSV vintage. Hardcoded as the season to compare against because the comparison is only
#: meaningful within one season, and reading it off the file's own source_date column would let a
#: silent re-export move the comparison without anyone noticing which season it now describes.
CSV_SEASON = "2026"

#: Seasons that have finished, so a projection can be scored against a result.
COMPLETED_SEASONS = ("2023", "2024")

#: Replacement rank per position in 12T_ppr_K_DEF -- the starting band. Quoted rather than derived
#: here because this probe must not depend on building a board; the board-derived numbers live in
#: INSTRUMENT.md and agree with these.
STARTING_BAND = {"QB": 12, "RB": 32, "WR": 32, "TE": 20, "K": 12, "DEF": 12}


def season_totals(season: str, kind: str, scoring: dict) -> dict[str, float]:
    totals: dict[str, float] = collections.defaultdict(float)
    for _week, lines in cwl.load_season(season, kind).items():
        for pid, stats in lines.items():
            totals[pid] += pu.score_projection(stats, scoring)
    return dict(totals)


def pearson(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    if not den:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den


def spearman(xs, ys):
    """Rank correlation. Ties are broken by position in the descending sort rather than averaged,
    which is adequate here and stated rather than hidden: kicker totals tie constantly, and an
    averaged-rank implementation would change the third decimal of a number whose standard error
    is 0.33."""
    def ranks(values):
        order = sorted(range(len(values)), key=lambda i: -values[i])
        out = [0] * len(values)
        for place, index in enumerate(order):
            out[index] = place + 1
        return out
    return pearson(ranks(xs), ranks(ys))


def csv_projections(position: str) -> dict:
    """{join key: projection} from the board's own seed file.

    DEF joins on TEAM, because Sleeper's DEF player ids are team abbreviations. K joins on
    (last name, team), because the CSV abbreviates first names -- "B Aubrey" -- and a full-name
    join returns ZERO matches out of 37 while looking like a legitimate empty result.
    """
    rows = [r for r in csv.DictReader((CSV_DIR / CSV_FILES[position]).open())
            if r.get("projection")]
    if position == "DEF":
        return {r["team"].strip().upper(): float(r["projection"]) for r in rows}
    return {(r["name"].strip().split()[-1].lower(), r["team"].strip().upper()):
            float(r["projection"]) for r in rows}


def weekly_keys(position: str, totals: dict, players_db: dict) -> dict:
    out = {}
    for pid, value in totals.items():
        info = players_db.get(pid) or {}
        if pu.player_position(info) != position:
            continue
        if position == "DEF":
            out[str(pid).strip().upper()] = value
        else:
            last = (info.get("last_name")
                    or pu.player_name(info, pid).split()[-1]).strip().lower()
            out[(last, (info.get("team") or "").upper())] = value
    return out


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()

    print(f"QUESTION 1: is the board's CSV the same artifact as the weekly sum? ({CSV_SEASON})")
    weekly = season_totals(CSV_SEASON, "projections", scoring)
    if not weekly:
        print(f"  no {CSV_SEASON} projections capture on disk -- cannot answer")
    for position in ("DEF", "K"):
        seed = csv_projections(position)
        live = weekly_keys(position, weekly, players_db)
        shared = [k for k in seed if k in live]
        pairs = sorted(((seed[k], live[k]) for k in shared), reverse=True)
        print(f"\n  {position}: csv n={len(seed)}  weekly n={len(live)}  joined={len(pairs)}")
        print(f"    {'band':<10}{'n':>4}{'r':>8}{'se~':>7}{'ratio med':>11}{'ratio sd':>10}")
        for depth in (STARTING_BAND[position], 20, None):
            band = pairs[:depth] if depth else pairs
            if len(band) < 5:
                continue
            ratios = [w / c for c, w in band if c]
            value = pearson([c for c, _ in band], [w for _, w in band])
            label = f"top {depth}" if depth else "whole pool"
            print(f"    {label:<10}{len(band):>4}{value:>8.3f}{1/((len(band)-3)**0.5):>7.2f}"
                  f"{statistics.median(ratios):>11.3f}{statistics.pstdev(ratios):>10.3f}")

    print("\n\nQUESTION 2: does a projection predict ORDERING inside the starting band?")
    print("Spearman, projected vs REALIZED, over seasons that have finished.\n")
    print(f"  {'pos':<5}{'band':>6}" + "".join(f"{s:>8}" for s in COMPLETED_SEASONS) + f"{'se~':>8}")
    for position, rank in STARTING_BAND.items():
        row = f"  {position:<5}{rank:>6}"
        for season in COMPLETED_SEASONS:
            projected = season_totals(season, "projections", scoring)
            actual = season_totals(season, "stats", scoring)
            pool = sorted(((projected[pid], actual[pid]) for pid in projected
                           if pid in actual
                           and pu.player_position(players_db.get(pid) or {}) == position),
                          reverse=True)[:rank]
            value = spearman([x for x, _ in pool], [y for _, y in pool]) if len(pool) >= 5 else None
            row += f"{value:>8.2f}" if value is not None else f"{'--':>8}"
        print(row + f"{1/((rank - 3) ** 0.5):>8.2f}")
    print("\n  se is the standard error of ONE estimate. Two seasons is two draws. A gap smaller")
    print("  than about two se is not a difference between positions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
