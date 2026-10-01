"""Profile ONE board at a MID-DRAFT state, replayed from a real trajectory.

WHY THIS PROBE EXISTS AND THE OPENING BOARD IS NOT ENOUGH. On an opening board the two terms
the 5.4x was attributed to are structurally absent, so timing them there measures nothing:

  * `depth_exposure` is only `measured` once a bench exists (round 9) -- before that every
    position answers `vacant`/`no_surplus` and the per-position lineup re-solve has nothing to
    solve. Measured on the opening board of 12T_ppr: `lineup_optimizer.depth_exposure`, 13
    calls, **0.000 s cumulative**.
  * `displacement_adj` is identically 0.00 on every priced row of a board built with an empty
    roster -- with every dedicated slot open, each position's probe evicts its own phantom.

A term reading zero because the state cannot produce it is not evidence that it does not matter
(engine-measurement, "An empty roster is not a neutral roster"). So this builds the board at a
real mid/late-round state, replayed from a trajectory an actual draft produced.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/profile_middraft.py <arm> <tag> <traj.json> <at_pick> \
        [--no-profile]

`traj.json` is a CURVE_*.json written by draft_cost_curve.py. THE SAME trajectory file is used
for both commits, so both arms price the identical board state -- a state replayed from each
commit's own draft would differ if the drafts diverged, and the comparison would then be
between two different boards.

Run from the REPO ROOT of the commit being measured, ALONE on the box.
"""
import cProfile
import json
import os
import pstats
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "evidence/performance/probes")
import perf_fixture as pf                                     # noqa: E402
import draft_room as dr                                       # noqa: E402
import pick_synthesis as ps                                   # noqa: E402

OUT = os.environ.get(
    "PERF_OUT",
    "/tmp/claude-0/-home-user-The-Dynasty-Collective/10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf")

#: `mode="auto"` resolves upside-vs-balanced from `round`, which it reads off the picks. A pick
#: record missing it is not the same record with a field absent, it is a semantically different
#: record that silently selects the other valuation (#222). Schema-validated, not value-validated.
REQUIRED_PICK_FIELDS = {"pick_no", "round", "roster_id", "player_id"}


def main():
    label, tag, traj_path, at = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    do_profile = "--no-profile" not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    suffix = f"{tag}_{label}_at{at}"

    merger, players_db, season, universe = pf.fixture()
    entry = pf.arm(label)
    kw = pf.board_inputs(merger, players_db, season, entry)
    pick_order = kw.pop("pick_order")
    merger_, pdb_, league = kw.pop("merger"), kw.pop("players_db"), kw.pop("league")
    mode = entry.get("mode", "auto")
    num_teams = entry["teams"]

    src = json.load(open(traj_path))
    taken = src["picks"][:at]
    if len(taken) != at:
        raise RuntimeError(f"trajectory holds {len(src['picks'])} picks, asked for {at}")
    # Production's shape, copied from draft_simulation.simulate_full_draft's own append.
    picks = [{"pick_no": i + 1, "round": i // num_teams + 1,
              "roster_id": str(p["roster"]), "player_id": str(p["player"])}
             for i, p in enumerate(taken)]
    missing = REQUIRED_PICK_FIELDS - set(picks[0])
    assert not missing, f"pick records are missing {missing}; mode='auto' reads `round`"

    roster_id = str(pick_order[at])
    round_no = at // num_teams + 1
    pick_label = f"{round_no}.{(at % num_teams) + 1:02d}"
    # The universe check the skill demands of any probe that builds a board and a draft
    # separately: every replayed pick must exist in the pool this board is priced from.
    unknown = [p["player_id"] for p in picks if str(p["player_id"]) not in pdb_]
    print(f"REPLAY n_picks_replayed={len(picks)} at_index={at} round={round_no} "
          f"pick_label={pick_label} seat={roster_id} "
          f"n_replayed_ids_not_in_pool={len(unknown)}", flush=True)
    assert not unknown, f"{len(unknown)} replayed picks are outside this board's universe"

    prof = cProfile.Profile() if do_profile else None
    t0 = time.time()
    if prof: prof.enable()
    snap = ps.build_snapshot(merger_, pdb_, picks, pick_order, at, roster_id, league,
                             pick_label=pick_label, mode=mode,
                             upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND), **kw)
    if prof: prof.disable()
    el = time.time() - t0
    # Which terms are actually live at this state -- stated, not assumed.
    live = {"depth_measured": 0, "depth_other": 0, "displacement_nonzero": 0,
            "displacement_zero": 0, "n_candidates": len(snap.candidates)}
    for c in snap.candidates:
        if getattr(c, "depth_basis", None) == "measured":
            live["depth_measured"] += 1
        else:
            live["depth_other"] += 1
        d = getattr(c, "displacement_adj", None)
        if d is not None and d != 0:
            live["displacement_nonzero"] += 1
        else:
            live["displacement_zero"] += 1
    print(f"BOARD seconds={el:.3f} n_candidates={live['n_candidates']} "
          f"depth_basis_measured={live['depth_measured']} "
          f"depth_basis_other={live['depth_other']} "
          f"displacement_nonzero={live['displacement_nonzero']} "
          f"displacement_zero={live['displacement_zero']}", flush=True)

    out = {"tag": tag, "label": label, "at_pick": at, "seconds": el, "live": live,
           "n_picks_replayed": len(picks), "profiled": do_profile}
    if prof:
        prof.dump_stats(f"{OUT}/PROFMID_{suffix}.prof")
        st = pstats.Stats(prof); st.sort_stats("cumulative")
        rows = []
        for func, (cc, nc, tt, ct, callers) in st.stats.items():
            fn, ln, name = func
            rows.append((ct, tt, nc, f"{os.path.basename(fn)}:{ln}({name})"))
        rows.sort(reverse=True)
        print(f"\n{'cumul_s':>9} {'tottime_s':>9} {'ncalls':>9}  function")
        for ct, tt, nc, w in rows[:30]:
            print(f"{ct:9.3f} {tt:9.3f} {nc:9d}  {w}")
        print("\n--- the attributed terms, and the repeat candidates ---")
        want = ("depth_exposure", "displacement", "roster_points_lookup", "need_bonus",
                "_players_db_fingerprint", "anchor_cache_key", "build_available_pool",
                "compute_draft_board", "feasibility_first", "linear_sum_assignment",
                "slot_coverage", "estimated_bench_demand", "replacement_levels",
                "_merge_across_eligibility", "merge_player", "_resolve", "get_close_matches")
        for ct, tt, nc, w in rows:
            if any(x in w for x in want):
                print(f"{ct:9.3f} {tt:9.3f} {nc:9d}  {w}")
        out["rows"] = [{"cumul": ct, "tottime": tt, "ncalls": nc, "where": w}
                       for ct, tt, nc, w in rows]
    json.dump(out, open(f"{OUT}/MID_{suffix}.json", "w"))
    print(f"\nWROTE {OUT}/MID_{suffix}.json", flush=True)


if __name__ == "__main__":
    main()
