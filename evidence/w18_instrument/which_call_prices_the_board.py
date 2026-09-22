"""Which vendor prices each position, as a function of HOW compute_draft_board is called.

Run from the repo root. No network.

WHY THIS EXISTS. Three published conclusions in this repository turned on which call was measured,
and two of them were wrong because the answer was assumed rather than checked:

  - #28 claimed the board compares Draft Sharks against Sleeper-seeded CSVs on one bpa scale. That
    comparison happens only in a board built with NO sleeper_projections argument, which no caller
    builds. Withdrawn.
  - A "correction" of KDST_VALUATION.md's QB 43.9 / K 12.6 / DEF 30.5 called them stale and
    replaced them with numbers from that same phantom configuration. They were not stale: in the
    BATTERY configuration they reproduce exactly. The correction was the error.

One wrong measurement, two published mistakes. `compute_draft_board` returns a perfectly good board
with no Sleeper argument and nothing says it is a board nobody builds, so this prints the answer
rather than leaving it to be assumed again.

THE THREE CONFIGURATIONS, and only the last two exist in practice:
  1. no sleeper_projections          -- no caller does this
  2. season_projections_from_capture -- run_draft_battery.py:425
  3. full Sleeper season sums        -- app.py:4927, 5006, 5066, 5431
"""

from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

ARM = "12T_ppr_K_DEF"
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")

#: The season whose weekly projections stand in for a live sync. Any captured season would do --
#: this is about which SOURCE LABEL each row gets, not about the numbers.
LIVE_SYNC_SEASON = "2026"


def season_sums(season: str) -> dict[str, dict]:
    """Per-CATEGORY season totals, the shape app.py passes as snapshot['season_projections'].

    Per category, never pre-scored: compute_draft_board scores them itself under the league's own
    rules, and handing it points would bake in one league's scoring -- the same rule
    outcome_record.py states for realized stats, applied to the projected side.
    """
    totals: dict[str, dict] = collections.defaultdict(lambda: collections.defaultdict(float))
    for _week, lines in cwl.load_season(season, "projections").items():
        for pid, stats in lines.items():
            for key, value in stats.items():
                try:
                    totals[pid][key] += float(value)
                except (TypeError, ValueError):
                    # A non-numeric stat field is not a zero (#187). Skipped, not defaulted.
                    continue
    return {pid: dict(stats) for pid, stats in totals.items()}


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])

    calls = [
        ("no sleeper_projections (NO CALLER)", {}),
        ("season_projections_from_capture (the BATTERY)",
         dict(sleeper_projections=rdb.season_projections_from_capture(),
              sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)),
        (f"full Sleeper season sums, {LIVE_SYNC_SEASON} (what APP.PY does)",
         dict(sleeper_projections=season_sums(LIVE_SYNC_SEASON),
              sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)),
    ]

    for label, kwargs in calls:
        merger = dm.DataMerger()
        # NEVER SKIP THIS -- scoring does not propagate into offensive valuation through
        # scoring_settings, it propagates by FILE SELECTION. A battery that omitted it once drafted
        # all 32 formats from one export and nine of thirteen findings were artifacts.
        merger.set_league_format(db.league_format_hint(arm["league"]))
        rows = dr.compute_draft_board(merger, players_db, [], 1, arm["league"], **kwargs)
        by_position = collections.defaultdict(list)
        for row in rows:
            by_position[row.get("position")].append(row)

        print(f"\n=== {label} ===   board rows={len(rows)}")
        print(f"  {'pos':<5}{'band':>6}{'bpa gap':>10}{'/QB':>7}  sources in the starting band")
        qb_gap = None
        for position in POSITIONS:
            rank = max(1, int(round(arm["teams"] * starters.get(position, 0.0))))
            band = sorted(by_position[position],
                          key=lambda r: -(r.get("bpa") or 0.0))[:rank]
            if len(band) < rank:
                print(f"  {position:<5}{rank:>6}  pool too small ({len(band)})")
                continue
            gap = (band[0].get("bpa") or 0.0) - (band[-1].get("bpa") or 0.0)
            if position == "QB":
                qb_gap = gap
            sources = collections.Counter(r.get("bpa_source") for r in band)
            share = f"{gap / qb_gap:.2f}" if qb_gap else "--"
            print(f"  {position:<5}{rank:>6}{gap:>10.1f}{share:>7}  "
                  + ", ".join(f"{k}={v}" for k, v in sources.most_common()))
    print("\nThe starting band is what a draft discriminates in, so the sources are counted there")
    print("rather than over the whole board -- most of a board is an unpriced tail, and its modal")
    print("source is no_priceable_input in every configuration, which answers nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
