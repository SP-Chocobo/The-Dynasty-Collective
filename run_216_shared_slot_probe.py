"""Does ONE SLOT, ONE ALTERNATIVE change what the engine drafts? (#216, #221)

One process, one code version, one thing toggled -- `draft_room.shared_slot_alternatives`, which
exists as a module-level function for exactly this reason:

    SELF    -- `board_slot_alternatives` patched to return {}, so every phantom is worth the
               CANDIDATE'S OWN positional level. That was the shipped engine BEFORE #221.
    SHARED  -- untouched: a flex slot's phantom is worth the best free player among the positions
               it admits. That is the SHIPPED engine from #221 onward.

**THE ARMS SWAPPED AT #221, WHEN THE CONSTRUCTION WAS WIRED.** Until then SELF was "untouched"
and SHARED was the patched arm; leaving it that way after wiring would have made both arms run
the identical code and every number in this file a null result that looked like a measurement
(engine-measurement skill: "if ON and OFF are identical, it did not fire"). `board_slot_alternatives`
is still exactly the seam -- one function, patched or not -- so the ablation is unchanged in kind,
only in which side carries the patch.

Everything else -- the drafting loop, the control, the rulers, the derived band, the ordering
verdict, the G9 asset numbers -- is `run_216_bench_probe`'s, imported rather than restated (#126).
Both anchor caches are dropped at every arm boundary, because an ablation defeats a fingerprinted
cache from outside (see draft_room.reset_anchor_caches).

Gates pre-registered at fc5ca5d, BEFORE this change existed.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from unittest import mock

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import resume_join
import run_216_bench_probe as bench
import run_draft_battery as rdb
import run_roster_proof as rp

ARMS = ("SELF", "SHARED")
FORMATS = ("12T_ppr", "12T_ppr_SF", bench.OWNER_LEAGUE["label"])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default=",".join(FORMATS))
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--seats", default="1,6,12")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args(argv)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "probe.log"

    def log(msg):
        print(msg, flush=True)
        with log_path.open("a") as fh:
            fh.write(msg + "\n")

    commit = resume_join.head_commit()
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    for fmt_label in args.formats.split(","):
        league, draft_type = bench.build_league(fmt_label, scoring)
        merger.set_league_format(db.league_format_hint(league))          # NEVER SKIP
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
        done = set()
        if args.resume and out_path.exists():
            prior = json.loads(out_path.read_text())
            if prior.get("commit") == commit and prior.get("format") == fmt_label:
                results["drafts"] = prior.get("drafts", [])
                done = {(d["arm"], str(d["seat"])) for d in results["drafts"]}
                log(f"resume {fmt_label}: carrying {len(done)} drafts")
        log(f"commit {commit} | {fmt_label} | pool {len(points)} | rounds {rounds}")
        for seat in args.seats.split(","):
            for arm in args.arms.split(","):
                if (arm, str(seat)) in done:
                    continue
                t0 = time.time()
                dr.reset_anchor_caches()
                # #221: SELF is now the PATCHED arm. See the module docstring -- the seam was
                # wired, so "untouched" is the shared alternative and it is SELF that has to be
                # switched back off to exist at all.
                if arm == "SELF":
                    with mock.patch.object(dr, "board_slot_alternatives", lambda *a, **k: {}):
                        d = bench.draft_one("B0", merger, players_db, league, pick_order, seat,
                                            points, season, rounds, slots, log, rulers, horizon_map)
                else:
                    d = bench.draft_one("B0", merger, players_db, league, pick_order, seat,
                                        points, season, rounds, slots, log, rulers, horizon_map)
                dr.reset_anchor_caches()
                d["arm"] = arm
                d["seconds"] = round(time.time() - t0, 1)
                results["drafts"].append(d)
                out_path.write_text(json.dumps(results, indent=1, default=str))
                v = d["verdict_full_roster"]
                log(f"  == {arm:6s} seat {seat:>2s}: {d['composition']} bench "
                    f"{d['bench_composition_by_pick_order']} "
                    f"order {v['pass_strict']}/{v.get('pass_flex_te')} "
                    f"lineup {d['lineup_points']} vs ctrl {d['control_lineup_points']} "
                    f"forced {d['forced']} unfillable {d['unfillable_starting_slots']} "
                    f"cdme {d['g9_engine']['cdme_total_value']} vs {d['g9_control']['cdme_total_value']} "
                    f"start {d['g9_engine']['cdme_starter_value']} ({d['seconds']}s)")
        log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
