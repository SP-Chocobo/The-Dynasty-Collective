"""#18: the population estimator that replaces the two-player difference. No network.

Run from the repo root.

WHAT IT MEASURES. Per position, regress each player's REALIZED season total on their PROJECTED
season total across the whole pool, and report the slope. The slope is how much of a projected
point difference actually materialises: 1.0 means the projection's spread is real, 0.5 means half
of every projected gap evaporates, above 1.0 means the projection COMPRESSES a spread that reality
widens.

WHY A SLOPE AND NOT A RATIO OF TWO PLAYERS. The instrument this replaces took the player projected
at rank 1 and the player projected at replacement rank and divided their realized difference by
their projected one -- n = 1 pair per position per season. It failed at both positions the work
exists to fix: at K three players tied at exactly 133.0 realized points at the replacement rank,
so the ratio was a coin flip among them, and at DEF the projected gap was 6.7 points across a
season, so the ratio was a division by nearly zero. A slope uses every player in the pool (32 to
343 here), so a tie is one point among many and a small gap is not a denominator.

IT ALSO NEVER RANKS BY OUTCOME, which the realized-spread probe next door cannot avoid. That probe
has to sort by actuals to find "the best realized defense", and a maximum over noise is inflated,
differently per position. A regression has no maximum in it. This is the estimator that can carry
a derivation; that one can only bound a comparison.

WHAT IT STILL DOES NOT ANSWER. The board does not price K and DEF from these projections. It
prices them from two committed CSVs (draft_room.KDST_SEEDED_SOURCE_FILES), and
measure_projection_accuracy's docstring claiming those are "exactly the source this reads" is
FALSE -- measured, they are a different artifact with a different pool size and a different scale.
So a slope measured here is a statement about Sleeper's weekly projections, not about the board's
K/DEF input, until the two are shown to be the same artifact. See INSTRUMENT.md.
"""

from __future__ import annotations

import collections
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import player_universe as pu
import run_draft_battery as rdb

POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")
SEASONS = ("2023", "2024")

#: Pool depths to report the slope at. NOT a search for the flattering one -- the point is the
#: opposite, to show where the estimate STOPS moving. A slope that is 2.59 over twelve players and
#: 1.05 over the whole pool is telling you twelve players is not a population.
DEPTHS = (12, 24, 36, 48, 72, None)

#: Fewer than this and a slope is arithmetic rather than a measurement. Derived, not chosen: it is
#: the smallest pool for which the estimator has more points than the two the old one had, by the
#: same factor again -- and it gates REPORTING, never a value.
MIN_POOL_FOR_A_SLOPE = 5


def season_totals(season: str, kind: str, scoring: dict) -> dict[str, float]:
    totals: dict[str, float] = collections.defaultdict(float)
    for _week, lines in cwl.load_season(season, kind).items():
        for pid, stats in lines.items():
            totals[pid] += pu.score_projection(stats, scoring)
    return dict(totals)


def slope(pairs: list[tuple[float, float]]) -> float | None:
    """Ordinary least squares slope of realized on projected, or None for a degenerate pool.

    None rather than 0.0 (#187): a pool where every player carries the same projection has no
    slope to measure, which is not the same fact as a slope that measured zero.
    """
    if len(pairs) < 2:
        return None
    mean_x = statistics.fmean(x for x, _ in pairs)
    mean_y = statistics.fmean(y for _, y in pairs)
    sxx = sum((x - mean_x) ** 2 for x, _ in pairs)
    if not sxx:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in pairs) / sxx


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()

    header = f"{'pos':<5}{'season':<8}" + "".join(
        f"{('K=' + str(d) if d else 'pool'):>9}" for d in DEPTHS) + f"{'n':>7}"
    print(header)
    for season in SEASONS:
        projected = season_totals(season, "projections", scoring)
        actual = season_totals(season, "stats", scoring)
        if not projected or not actual:
            print(f"  {season}: no capture on disk; skipped")
            continue
        for position in POSITIONS:
            pool = sorted(((projected[pid], actual[pid]) for pid in projected
                           if pid in actual
                           and pu.player_position(players_db.get(pid) or {}) == position),
                          reverse=True)
            row = f"{position:<5}{season:<8}"
            for depth in DEPTHS:
                band = pool[:depth] if depth else pool
                if len(band) < MIN_POOL_FOR_A_SLOPE:
                    row += f"{'--':>9}"
                    continue
                value = slope(band)
                row += f"{value:>9.2f}" if value is not None else f"{'n/a':>9}"
            print(row + f"{len(pool):>7}")

    print("\nRead the last two columns, not the first. A slope that moves from 2.59 at twelve "
          "players to 1.05 over the pool\nis reporting that twelve players is not a population -- "
          "the same defect, one order of magnitude less severe,\nthat made the two-player "
          "estimator unusable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
