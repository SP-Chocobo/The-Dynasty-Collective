"""Does the DERIVED flex share change what the engine drafts, and in which direction?

One process, one code version, one thing toggled -- the discipline the engine-measurement
checklist demands. The only difference between the two arms is whether
`draft_room.fielded_flex_occupancy` is allowed to return its measurement:

    EVEN     -- untouched, so `board_flex_share` returns None and starter_slot_counts falls back
                to the even split. This is the SHIPPED engine (displacement term only).
    FIELDED  -- `board_flex_share` patched to return fielded_flex_occupancy's measurement.

`board_flex_share` exists as exactly this seam: the measurement is built and tested but NOT
WIRED (see its own comment and #50), so the shipped board is the EVEN arm and this probe is what
re-enables the other one, by patching one function and nothing else.

Everything else -- the drafting loop, the control, the rulers, the band, the ordering verdict,
the G9 asset numbers -- is `run_216_bench_probe`'s, imported rather than restated (#126). Arm
"B0" there is the shipped ordering with the displacement term on, which is exactly the base this
change sits on top of.

Three formats: the two lab formats and the OWNER'S REAL LEAGUE, which is the one where the
pre-registered gate H2 lives (his own roster carries two tight ends; the displacement-only
engine fields zero).

Writes after every single draft, so a container reclaimed mid-run costs one draft and not the
run; `--resume` skips (format, seat, arm) triples already present in the output file.
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

ARMS = ("EVEN", "FIELDED")
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
                                          sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
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
            # A resumed block is only reusable if it came from THIS commit; a stale one
            # masquerading as a fresh measurement is the failure #215 exists to prevent.
            if prior.get("commit") == commit and prior.get("format") == fmt_label:
                results["drafts"] = prior.get("drafts", [])
                done = {(d["arm"], str(d["seat"])) for d in results["drafts"]}
                log(f"resume {fmt_label}: carrying {len(done)} drafts from {out_path}")
        # The measured share, recorded once per format so the table can be read against the
        # instrument that predicted it without re-deriving anything.
        occupancy = dr.fielded_flex_occupancy(
            dr.roster_points_lookup(
                merger, players_db, dr.league_usable_positions(league["roster_positions"]),
                league["roster_positions"], league["total_rosters"],
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM),
            players_db, league["roster_positions"], league["total_rosters"])
        results["flex_occupancy"] = occupancy
        results["slot_share_basis"] = dr.slot_share_basis(occupancy, league["total_rosters"])
        results["slot_counts_fielded"] = dr.starter_slot_counts(
            league["roster_positions"], occupancy, league["total_rosters"])
        results["slot_counts_even"] = dr.starter_slot_counts(league["roster_positions"])
        log(f"commit {commit} | {fmt_label} | pool {len(points)} | rounds {rounds} | "
            f"basis {results['slot_share_basis']} | flex {occupancy}")
        for seat in args.seats.split(","):
            for arm in args.arms.split(","):
                if (arm, str(seat)) in done:
                    continue
                t0 = time.time()
                # THE ARM BOUNDARY. Both fingerprinted anchor caches are dropped here, because
                # the ablation changes the answer without changing any input the cache key
                # names -- so without this the EVEN arm reads the FIELDED arm's remembered
                # levels and the whole comparison is a measurement of nothing. This exact
                # contamination produced a 5-point error in the first rival_premium attribution
                # before it was caught; see draft_room.reset_anchor_caches.
                dr.reset_anchor_caches()
                if arm == "FIELDED":
                    with mock.patch.object(dr, "board_flex_share", dr.fielded_flex_occupancy):
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
                log(f"  == {arm:8s} seat {seat:>2s}: {d['composition']} bench "
                    f"{d['bench_composition_by_pick_order']} "
                    f"order {d['verdict_full_roster']['pass_strict']}/{d['verdict_full_roster']['pass_tendency']} "
                    f"lineup {d['lineup_points']} vs ctrl {d['control_lineup_points']} "
                    f"forced {d['forced']} unfillable {d['unfillable_starting_slots']} "
                    f"cdme {d['g9_engine']['cdme_total_value']} vs {d['g9_control']['cdme_total_value']} "
                    f"start {d['g9_engine']['cdme_starter_value']} vs {d['g9_control']['cdme_starter_value']} "
                    f"({d['seconds']}s)")
        log(f"-> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
