"""Measure ONE real draft arm at whichever commit's tree this runs in.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/profile_draft.py <arm_label> <tag> [opts]

    opts:  --no-profile     wall-clock only; the headline s/pick number comes from this
           --profile        cProfile the run and dump a cumulative-time table + .prof
           --board-only     one board build at the OPENING state instead of a draft
           --picks N        stop the draft after N picks (keeps a long arm affordable)

Run from the REPO ROOT of the commit being measured -- `DataMerger()` resolves `data/baseline`
relative to cwd, and a `cd` into a scratch dir loads an empty frame that crashes three calls
later with KeyError: 'position'.

RUN ALONE ON THE BOX. This container has 4 cores. The 6.03 s/pick figure under investigation
is the SUM of three concurrent shard processes' wall clocks, so any arm measured beside another
is a number about the contention, not the engine.

RAW FIRST (#215): the trajectory is dumped before a single derived figure is computed.
"""
import cProfile
import json
import os
import pstats
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "evidence/performance/probes")
import perf_fixture as pf                                    # noqa: E402
import draft_room as dr                                      # noqa: E402
import draft_simulation                                      # noqa: E402
import pick_synthesis as ps                                  # noqa: E402

OUT = os.environ.get(
    "PERF_OUT",
    "/tmp/claude-0/-home-user-The-Dynasty-Collective/10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf")


def _table(st, elapsed, n_units, unit):
    rows = []
    for func, (cc, nc, tt, ct, callers) in st.stats.items():
        fn, ln, name = func
        rows.append((ct, tt, nc, f"{os.path.basename(fn)}:{ln}({name})"))
    rows.sort(reverse=True)
    print(f"\n=== n_{unit}s={n_units} total={elapsed:.3f}s "
          f"per_{unit}={elapsed/max(n_units,1):.4f}s ===", flush=True)
    print(f"{'cumul_s':>9} {'tottime_s':>9} {'ncalls':>10} {'calls/'+unit:>11}  function")
    for ct, tt, nc, where in rows[:45]:
        print(f"{ct:9.3f} {tt:9.3f} {nc:10d} {nc/max(n_units,1):11.1f}  {where}")
    return rows


def main():
    label, tag = sys.argv[1], sys.argv[2]
    do_profile = "--profile" in sys.argv
    board_only = "--board-only" in sys.argv
    limit = None
    if "--picks" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--picks") + 1])
    os.makedirs(OUT, exist_ok=True)
    suffix = f"{tag}_{label}" + ("_board" if board_only else "") + ("_prof" if do_profile else "")

    merger, players_db, season, universe = pf.fixture()
    entry = pf.arm(label)
    kw = pf.board_inputs(merger, players_db, season, entry)
    pick_order = kw.pop("pick_order")
    merger_, pdb_, league = kw.pop("merger"), kw.pop("players_db"), kw.pop("league")
    if limit:
        pick_order = pick_order[:limit]
    mode = entry.get("mode", "auto")
    print(f"ARM {label} teams={entry['teams']} rounds={entry['rounds']} "
          f"n_pick_slots={len(pick_order)} mode={mode} "
          f"upside_rule={entry.get('upside_rule', dr.UPSIDE_RULE_ROUND)} profile={do_profile}",
          flush=True)

    prof = cProfile.Profile() if do_profile else None
    t0 = time.time()
    if board_only:
        # THE OPENING BOARD, and it is not a preview of the draft: with every dedicated slot
        # open, displacement_adj is structurally 0.00 on every priced row and depth_exposure is
        # not `measured` until a bench exists (round 9). Reported as the opening state only.
        if prof: prof.enable()
        snap = ps.build_snapshot(merger_, pdb_, [], pick_order, 0, str(pick_order[0]), league,
                                 pick_label="1.01", mode=mode,
                                 upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
                                 **kw)
        if prof: prof.disable()
        elapsed = time.time() - t0
        n_units, unit = 1, "board"
        json.dump({"tag": tag, "label": label, "seconds": elapsed,
                   "n_candidates": len(snap.candidates)},
                  open(f"{OUT}/RAW_{suffix}.json", "w"))
        print(f"RAW SAVED: opening board n_candidates={len(snap.candidates)} "
              f"seconds={elapsed:.3f}", flush=True)
    else:
        if prof: prof.enable()
        traj = draft_simulation.simulate_full_draft(
            merger_, pdb_, league, pick_order, mode=mode, config_label=entry["label"],
            upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
            opponent_noise=entry.get("opponent_noise"), **kw)
        if prof: prof.disable()
        elapsed = time.time() - t0
        json.dump([{"pick": i, "roster": p.roster_id, "player": p.chosen_player_id}
                   for i, p in enumerate(traj.picks, 1)], open(f"{OUT}/RAW_{suffix}.json", "w"))
        n_units, unit = len(traj.picks), "pick"
        print(f"RAW SAVED: n_picks={n_units} seconds={elapsed:.3f} "
              f"s_per_pick={elapsed/max(n_units,1):.4f}", flush=True)

    out = {"tag": tag, "label": label, "board_only": board_only, "profiled": do_profile,
           "seconds": elapsed, "n_units": n_units, "unit": unit,
           "per_unit": elapsed / max(n_units, 1)}
    if prof:
        prof.dump_stats(f"{OUT}/PROF_{suffix}.prof")
        st = pstats.Stats(prof)
        st.sort_stats("cumulative")
        rows = _table(st, elapsed, n_units, unit)
        out["rows"] = [{"cumul": ct, "tottime": tt, "ncalls": nc, "where": w}
                       for ct, tt, nc, w in rows]
    json.dump(out, open(f"{OUT}/STATS_{suffix}.json", "w"))
    print(f"\nWROTE {OUT}/STATS_{suffix}.json", flush=True)


if __name__ == "__main__":
    main()
