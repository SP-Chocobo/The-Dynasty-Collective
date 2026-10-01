"""Which term decides, once the shared-slot alternative is on? (#221, the named next step)

Run from the WORKTREE ROOT with PYTHONPATH set; the file lives outside the repo on purpose,
because the full suite is running and editing the tree during a measurement is the oldest rule
in the engine-measurement checklist.

The shared alternative makes `displacement_adj` -- uncapped -- far larger, while the three older
team-specific terms stay capped at 12.0 each. So it does not merely correct the term; it may
change WHICH term decides the ordering. Five arms, one process per format, one thing toggled each:

    SELF         shipped (board_slot_alternatives -> {})
    SHARED       the shared alternative on
    SHARED_ND    ... and depth_exposure zeroed
    SHARED_NE    ... and eligibility_bonus zeroed
    SHARED_NN    ... and need_bonus's two constants zeroed

Zeroing need_bonus removes the positional GATE #87 measured as load-bearing, so an illegal or
unfillable roster in SHARED_NN is a FINDING about that arm, not a fault in the shared alternative.
"""
from __future__ import annotations

import argparse, json, time
from pathlib import Path
from unittest import mock

import data_merger as dm, draft_battery as db, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, resume_join
import run_216_bench_probe as bench, run_draft_battery as rdb, run_roster_proof as rp

ARMS = ("SELF", "SHARED", "SHARED_ND", "SHARED_NE", "SHARED_NN")


def arm_context(arm, stack):
    if arm == "SELF":
        return
    stack.enter_context(mock.patch.object(dr, "board_slot_alternatives", dr.shared_slot_alternatives))
    # THE KEYS THE BOARD ACTUALLY READS, checked in draft_room before patching. The first
    # version of this file zeroed a key named "exposure" that nothing reads, so SHARED_ND came
    # back byte-identical to SHARED and would have been reported as "depth_exposure is not the
    # cause" -- an unapplied mutation reading exactly like a survivor. And it returned a bare
    # float for eligibility_bonus, which the caller subscripts, so that arm crashed rather than
    # lying, which is the luckier of the two failures.
    if arm == "SHARED_ND":
        real_depth = lo.depth_exposure
        stack.enter_context(mock.patch.object(lo, "depth_exposure", lambda *a, **k: {
            p: {**v, "worst_loss": 0.0} for p, v in real_depth(*a, **k).items()}))
    elif arm == "SHARED_NE":
        real_elig = lo.eligibility_bonus
        stack.enter_context(mock.patch.object(lo, "eligibility_bonus", lambda *a, **k: {
            **real_elig(*a, **k), "eligibility_bonus": 0.0}))
    elif arm == "SHARED_NN":
        stack.enter_context(mock.patch.object(dr, "NEED_BONUS_PER_DEDICATED_SLOT", 0.0))
        stack.enter_context(mock.patch.object(dr, "NEED_BONUS_PER_FLEX_SHARE", 0.0))


def main(argv=None) -> int:
    import contextlib
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default="OWNER_3RR_SF_noTE,12T_ppr_SF,12T_ppr")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seats", default="1,6,12")
    args = ap.parse_args(argv)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    def log(msg):
        print(msg, flush=True)
        with (out_dir / "probe.log").open("a") as fh:
            fh.write(msg + "\n")
    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    for fmt_label in args.formats.split(","):
        league, draft_type = bench.build_league(fmt_label, scoring)
        merger.set_league_format(db.league_format_hint(league))
        points = rp.scoreable_pool(merger, players_db, league, season)
        values = db.reference_values(merger, players_db, league, sleeper_projections=season,
                                     sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rulers = {"cdme": values, "points": points}
        predraft = dr.compute_draft_board(merger, players_db, [], None, league, mode="balanced",
                                          sleeper_projections=season,
                                          sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        horizon_map = {str(r["player_id"]): r.get("time_horizon_adj") for r in predraft}
        seats = [str(i) for i in range(1, league["total_rosters"] + 1)]
        rounds = len(league["roster_positions"])
        slots = lo.slots_from_roster_positions(league["roster_positions"])
        pick_order = ds.generate_pick_order(seats, rounds, draft_type)
        out_path = out_dir / f"{fmt_label}.json"
        results = {"commit": commit, "format": fmt_label, "universe": universe,
                   "roster_positions": league["roster_positions"], "drafts": []}
        log(f"commit {commit} | {fmt_label} | rounds {rounds}")
        for seat in args.seats.split(","):
            for arm in args.arms.split(","):
                t0 = time.time()
                dr.reset_anchor_caches()
                with contextlib.ExitStack() as stack:
                    arm_context(arm, stack)
                    d = bench.draft_one("B0", merger, players_db, league, pick_order, seat,
                                        points, season, rounds, slots, log, rulers, horizon_map)
                dr.reset_anchor_caches()
                d["arm"] = arm; d["seconds"] = round(time.time() - t0, 1)
                results["drafts"].append(d)
                out_path.write_text(json.dumps(results, indent=1, default=str))
                v = d["verdict_full_roster"]
                log(f"  == {arm:10s} seat {seat:>2s}: {d['composition']} order "
                    f"{v['pass_strict']}/{v.get('pass_flex_te')} lineup {d['lineup_points']} "
                    f"forced {d['forced']} unfill {d['unfillable_starting_slots']} "
                    f"cdme {d['g9_engine']['cdme_total_value']} vs {d['g9_control']['cdme_total_value']} "
                    f"({d['seconds']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
