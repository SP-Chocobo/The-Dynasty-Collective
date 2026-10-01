"""#18: what the 2024 season ACTUALLY paid at each position's replacement rank.

Run from the repo root. Reads the committed 2024 actuals; no network.

WHAT THIS IS FOR. measure_projection_accuracy reports a ratio per position: how much of the
PROJECTED rank-1-to-replacement gap materialised. Its estimator is a two-player difference -- one
pair per position per season -- and this probe exists to show why that resolution is not enough,
using the only arm of the comparison that is available offline.

WHAT IT CANNOT SAY. Ranking by OUTCOME is hindsight, and a hindsight-ranked gap is inflated for
every position: the best realized scorer is a maximum over noise. So the absolute numbers here
are NOT a position's true spread and must never be read as one. What survives the inflation is
the comparison BETWEEN positions, and only in one direction -- see the evidence note.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys
from pathlib import Path

# `python evidence/w18_instrument/realized_spread.py` puts THIS directory on sys.path, not the
# repo root, so the engine modules are unimportable even though the working directory is right.
# The engine-measurement rule is "run from the repo root, never cd first" -- because DataMerger
# resolves its baselines against the working directory -- and this line is what lets both be true
# at once instead of making the caller remember a PYTHONPATH.
sys.path.insert(0, str(Path.cwd()))

import draft_battery as dbat
import draft_room as dr
import player_universe as pu
import run_draft_battery as rdb

ACTUALS = Path("sleeper_weekly_2024.json")
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def realized_totals(scoring: dict) -> tuple[dict[str, float], dict[str, str]]:
    totals: dict[str, float] = collections.defaultdict(float)
    position: dict[str, str] = {}
    for _week, rows in json.loads(ACTUALS.read_text()).items():
        for row in rows:
            pid = row["player_id"]
            position[pid] = (row.get("player") or {}).get("position")
            totals[pid] += pu.score_projection(row.get("stats") or {}, scoring)
    return dict(totals), position


#: A season long enough that a player's weekly standard deviation is about their scoring rather
#: than about their byes and their injuries. Not a tuning knob: it is "played most of the year",
#: and the measurement is reported for whatever population clears it, with n printed.
MIN_WEEKS_FOR_A_NOISE_ESTIMATE = 14

REGULAR_SEASON_WEEKS = range(1, 19)


def weekly_noise(scoring: dict) -> dict[str, float]:
    """Per position, the MEDIAN player's week-to-week standard deviation.

    Median rather than mean because one player who scored once and sat out is not the position.
    Restricted to players who appeared in most weeks, because a two-week sample's standard
    deviation is a statement about absence, not about scoring.
    """
    weekly: dict[str, dict[str, float]] = collections.defaultdict(dict)
    position: dict[str, str] = {}
    for week, rows in json.loads(ACTUALS.read_text()).items():
        for row in rows:
            pid = row["player_id"]
            position[pid] = (row.get("player") or {}).get("position")
            weekly[pid][week] = pu.score_projection(row.get("stats") or {}, scoring)
    out = {}
    for pos in POSITIONS:
        sds = [statistics.stdev(list(v.values())) for pid, v in weekly.items()
               if position.get(pid) == pos
               and len(v) >= MIN_WEEKS_FOR_A_NOISE_ESTIMATE
               and statistics.mean(v.values()) > 0]
        if sds:
            out[pos] = statistics.median(sds)
    return out


def main() -> int:
    scoring = rdb.scoring_settings_from_capture()
    arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])
    totals, position = realized_totals(scoring)

    print(f"{'pos':<5}{'rank':>5}{'r1':>9}{'r@rank':>9}{'gap':>9}{'ties@rank':>11}{'pool':>7}")
    gaps = {}
    for pos in POSITIONS:
        rank = max(1, int(round(arm["teams"] * starters.get(pos, 0.0))))
        values = sorted((v for pid, v in totals.items() if position.get(pid) == pos),
                        reverse=True)
        if len(values) <= rank:
            print(f"{pos:<5}{rank:>5}   unmeasurable, pool={len(values)}")
            continue
        top, repl = values[0], values[rank - 1]
        ties = sum(1 for v in values if abs(v - repl) < 1e-9)
        gaps[pos] = top - repl
        print(f"{pos:<5}{rank:>5}{top:>9.1f}{repl:>9.1f}{top - repl:>9.1f}"
              f"{ties:>11}{len(values):>7}")

    # The board's own projected gaps at the same ranks, as recorded in
    # evidence/blind_pass/KDST_VALUATION.md. Quoted rather than recomputed because that table is
    # what the audit finding was written against; recomputing it here would let the comparison
    # drift from the claim it is testing.
    board = {"QB": 43.9, "K": 12.6, "DEF": 30.5}
    noise = weekly_noise(scoring)
    print("\nshare of QB's rank1-to-replacement gap, board vs realized:")
    print(f"{'pos':<5}{'board':>9}{'realized':>10}{'overstated':>12}")
    for pos in ("K", "DEF"):
        b = board[pos] / board["QB"]
        r = gaps[pos] / gaps["QB"]
        print(f"{pos:<5}{b:>9.2f}{r:>10.2f}{b / r:>11.1f}x")

    # THE OBJECTION THAT WOULD KILL THE COMPARISON ABOVE, and its answer. Hindsight inflates
    # every position's gap, so the comparison only holds if it inflates QB at least as much as
    # K and DEF. Inflation rides on how much of a season total is week-to-week noise, so that
    # is what this measures: the median player's weekly standard deviation, carried to a season
    # total as sd * sqrt(weeks), against the gap it would have to inflate.
    print("\nhow much of each gap could be week-to-week noise:")
    print(f"{'pos':<5}{'weekly sd':>11}{'season sd':>11}{'gap':>9}{'sd/gap':>9}")
    for pos in POSITIONS:
        if pos not in noise or pos not in gaps:
            continue
        season_sd = noise[pos] * (len(REGULAR_SEASON_WEEKS) ** 0.5)
        print(f"{pos:<5}{noise[pos]:>11.2f}{season_sd:>11.1f}{gaps[pos]:>9.1f}"
              f"{season_sd / gaps[pos]:>9.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
