"""#30: does a STREAMING replacement level actually improve REALIZED outcomes? Repo root.

THE EXPERIMENT. `replacement_levels` prices K and DEF against the (teams x slots)-th best player
by projection, held all season. This arm replaces that with the DERIVED streaming baseline for the
drafted season -- each week, the best wire player by THAT WEEK's projection, summed -- and grades
both arms on the season's realized outcomes through `run_backtest_grade`.

NO HINDSIGHT ENTERS THE LEVEL. Weekly projections are published before the games. The realized
stats are used only to SCORE, never to choose.

IT IS AN EXPERIMENT, NOT A SHIPPED CHANGE. `dr.replacement_levels` is wrapped for the treated arm
and restored afterwards. A shipped version would need weekly projections to reach the board in
production, which they currently do not (`app.py` passes season sums) -- that plumbing is the
reason this is measured before it is built rather than after.

WHAT IT CANNOT SETTLE. The counterfactual measured an early K/DST pick at +81.4 realized points if
deferred, and the valuation arms measured that correcting DEF's price alone saturates at round 10.
So a null result here would mean "this lever is too small", not "the cost is not real". Both
findings stand independently of this one.
"""

from __future__ import annotations

import collections
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import capture_weekly_lines as cwl
import draft_battery as db
import draft_room as dr
import player_universe as pu
import run_backtest_grade as bg
import run_draft_battery as rdb

import argparse

#: Season to derive the level from AND grade on. The two must MATCH: a live implementation
#: derives the streaming baseline from the season it is drafting, so deriving on one season and
#: grading on another would measure transfer of a stale level, not the method.
SEASON = "2024"
ARM = "12T_ppr_K_DEF"
#: Read from draft_room's own scope decision rather than restated, so this experiment
#: cannot disagree with the engine about which positions are streamed (#126).
STREAMED = dr.STREAMABLE_POSITIONS

#: Filled from the arm's own league in main(); a module default would be a second source of
#: truth about the format this experiment drafts.
ROSTER_POSITIONS: list = []
OUT_TEMPLATE = "evidence/kdst_streaming/STREAMING_ARM_{season}.json"


def streaming_levels(season: str, scoring: dict, players_db: dict,
                     teams: int, starters: dict) -> dict[str, float]:
    """Per streamed position, the season total a WIRE-STREAMER would have been projected to get.

    NOW A THIN WRAPPER OVER THE SHIPPED FUNCTION (`#126`). This module derived the level itself
    while it was an experiment and the engine had no such concept. `draft_room` has one now --
    `streaming_replacement_levels`, wired into `compute_draft_board` behind `weekly_projections`
    -- and a second copy here would be a second home for the derivation, which is exactly the
    arrangement where the copy nobody is watching drifts. Verified identical before the swap:
    both produce K 164.50 / DEF 146.05 on 2024.

    `starters` is accepted and unused, kept so every existing call site still reads correctly;
    the shipped function derives slot counts from `roster_positions` itself.
    """
    return dr.streaming_replacement_levels(
        cwl.load_season(season, "projections"), scoring, players_db,
        STREAMED, ROSTER_POSITIONS, teams,
    )


def main(argv=None) -> int:
    global SEASON
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default=SEASON,
                        help="derive the level from AND grade on this season -- a HOLDOUT is a "
                             "different season entirely, not a different grading year")
    parser.add_argument("--seats", type=int, default=0,
                        help="grade only the first N seats -- a diagnostic that yields a ROSTER "
                             "in a tenth of the time, never an answer")
    parsed = parser.parse_args(argv)
    SEASON, seats = parsed.season, parsed.seats
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    global ROSTER_POSITIONS
    ROSTER_POSITIONS = arm["league"]["roster_positions"]
    starters = dr.starter_slot_counts(ROSTER_POSITIONS, None, arm["teams"])
    levels = streaming_levels(SEASON, scoring, players_db, arm["teams"], starters)
    print(f"derived streaming levels ({SEASON}): {levels}", flush=True)

    real = dr.replacement_levels

    def streaming_replacement(*args, **kwargs):
        got = real(*args, **kwargs)
        for position, level in levels.items():
            # RAISE ONLY. The streaming baseline is what you get for free, so it can only ever be
            # a FLOOR under the replacement level -- never a reason to price a position as more
            # scarce than the draft already says it is.
            if position in got and level > got[position]:
                got[position] = level
        return got

    report = {"_comment": ("#30: base vs a DERIVED streaming replacement level for K/DEF, both "
                           "graded on realized outcomes. Experiment, not a shipped change -- see "
                           "streaming_arm_experiment.py."),
              "season": SEASON, "arm": ARM, "streaming_levels": levels, "arms": {}}

    for name, patched in (("base", False), ("streaming", True)):
        if patched:
            dr.replacement_levels = streaming_replacement
        try:
            print(f"\n=== arm: {name} ===", flush=True)
            code = bg.main(["--season", SEASON]
                           + (["--seats", str(seats)] if seats else [])
                           + ["--out",
                            f"/tmp/claude-0/-home-user-The-Dynasty-Collective/"
                              f"90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
                              f"bt_{name}{'_s' + str(seats) if seats else ''}.json"])
            if code != 0:
                print(f"arm {name} failed", file=sys.stderr)
                return code
        finally:
            dr.replacement_levels = real
        loaded = json.loads(Path(f"/tmp/claude-0/-home-user-The-Dynasty-Collective/"
                                 f"90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
                                 f"bt_{name}{'_s' + str(seats) if seats else ''}.json").read_text())
        block = loaded["results"][0]
        report["arms"][name] = {
            "wins": block["wins"], "seats": block["seats_graded"],
            "distinct": block["distinct_engine_rosters"],
            "mean_delta": block["mean_delta"], "median_delta": block["median_delta"],
            "mean_delta_distinct": block["mean_delta_distinct"],
            "first_kdst_rounds": sorted({r["engine_first_kdst_round"] for r in block["rows"]}),
            "engine_totals": [r["engine_realized"] for r in block["rows"]],
        }

    base, stream = report["arms"]["base"], report["arms"]["streaming"]
    paired = [s - b for b, s in zip(base["engine_totals"], stream["engine_totals"])]
    report["paired_engine_delta_mean"] = round(statistics.fmean(paired), 2)
    report["paired_engine_delta_median"] = round(statistics.median(paired), 2)
    report["seats_improved"] = sum(1 for d in paired if d > 0)
    out = Path(OUT_TEMPLATE.format(season=SEASON)
               if not seats else
               f"/tmp/claude-0/-home-user-The-Dynasty-Collective/"
               f"90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/STREAMING_ARM_{SEASON}_s{seats}.json")
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print(f"\n=== STREAMING REPLACEMENT vs BASE, graded on {SEASON} realized ===")
    print(f"{'arm':<11}{'wins':>6}{'mean':>9}{'median':>9}  first K/DST rounds")
    for name in ("base", "streaming"):
        a = report["arms"][name]
        print(f"{name:<11}{a['wins']:>3}/{a['seats']:<2}{a['mean_delta']:>9.1f}"
              f"{a['median_delta']:>9.1f}  {a['first_kdst_rounds']}")
    print(f"\nPAIRED engine total, streaming minus base, per seat:")
    print(f"   mean {report['paired_engine_delta_mean']:+.1f} | "
          f"median {report['paired_engine_delta_median']:+.1f} | "
          f"improved {report['seats_improved']} of {len(paired)}")
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
