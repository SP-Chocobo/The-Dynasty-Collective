"""One full draft arm, timed PER PICK, at whichever commit's tree this runs in.

Per-pick timing is the point. `DataMerger.merge_player` is memoized per merger instance
(`_merge_memo`), so the FIRST board of an arm pays a cold-cache name resolution that every
later board gets free. A single board build is therefore NOT representative of a per-pick cost,
and the 1.12 / 6.03 figures under investigation are both per-pick rates over whole arms.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/draft_cost_curve.py <arm_label> <tag> [--picks N]

Run from the REPO ROOT of the commit being measured, ALONE on the box.

RAW FIRST (#215): per-pick seconds are appended to the raw file as they are measured, so a
reclaimed container cannot lose the run.
"""
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, "evidence/performance/probes")
import perf_fixture as pf                                     # noqa: E402
import draft_room as dr                                       # noqa: E402
import draft_simulation                                       # noqa: E402
import pick_synthesis                                         # noqa: E402

OUT = os.environ.get(
    "PERF_OUT",
    "/tmp/claude-0/-home-user-The-Dynasty-Collective/10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf")


def main():
    label, tag = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[sys.argv.index("--picks") + 1]) if "--picks" in sys.argv else None
    os.makedirs(OUT, exist_ok=True)
    suffix = f"{tag}_{label}" + (f"_n{limit}" if limit else "")
    raw_path = f"{OUT}/CURVE_{suffix}.json"

    merger, players_db, season, universe = pf.fixture()
    entry = pf.arm(label)
    kw = pf.board_inputs(merger, players_db, season, entry)
    pick_order = kw.pop("pick_order")
    merger_, pdb_, league = kw.pop("merger"), kw.pop("players_db"), kw.pop("league")
    if limit:
        pick_order = pick_order[:limit]
    mode = entry.get("mode", "auto")
    print(f"ARM {label} teams={entry['teams']} rounds={entry['rounds']} "
          f"n_pick_slots={len(pick_order)} mode={mode}", flush=True)

    # Time the PRODUCTION call, by wrapping it -- never a reconstruction of what it costs.
    per_pick = []
    real = pick_synthesis.build_snapshot
    def spy(*a, **k):
        t = time.time()
        try:
            return real(*a, **k)
        finally:
            per_pick.append(round(time.time() - t, 4))
            if len(per_pick) % 12 == 0:
                json.dump({"tag": tag, "label": label, "per_pick": per_pick},
                          open(raw_path, "w"))
                print(f"  pick {len(per_pick):4d}/{len(pick_order)} "
                      f"last={per_pick[-1]:7.3f}s  cum={sum(per_pick):9.1f}s", flush=True)
    pick_synthesis.build_snapshot = spy
    try:
        t0 = time.time()
        traj = draft_simulation.simulate_full_draft(
            merger_, pdb_, league, pick_order, mode=mode, config_label=entry["label"],
            upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
            opponent_noise=entry.get("opponent_noise"), **kw)
        elapsed = time.time() - t0
    finally:
        pick_synthesis.build_snapshot = real

    n = len(traj.picks)
    out = {"tag": tag, "label": label, "n_picks": n, "n_pick_slots": len(pick_order),
           "seconds": elapsed, "s_per_pick": elapsed / max(n, 1),
           "per_pick": per_pick,
           "first_pick_s": per_pick[0] if per_pick else None,
           "picks": [{"pick": i, "roster": p.roster_id, "player": p.chosen_player_id}
                     for i, p in enumerate(traj.picks, 1)]}
    json.dump(out, open(raw_path, "w"))
    print(f"\nRAW SAVED: {raw_path}", flush=True)
    print(f"ARM DONE {label} tag={tag} n_picks={n} seconds={elapsed:.1f} "
          f"s_per_pick={elapsed/max(n,1):.4f}", flush=True)
    if per_pick:
        warm = per_pick[1:]
        print(f"  first_board={per_pick[0]:.3f}s (cold merge memo)  "
              f"n_warm={len(warm)} warm_mean={sum(warm)/max(len(warm),1):.4f}s  "
              f"warm_min={min(warm):.3f}s warm_max={max(warm):.3f}s", flush=True)
        q = sorted(warm)
        if q:
            print(f"  warm median={q[len(q)//2]:.3f}s  "
                  f"first_quarter_mean={sum(warm[:len(warm)//4])/max(len(warm)//4,1):.3f}s  "
                  f"last_quarter_mean={sum(warm[-(len(warm)//4):])/max(len(warm)//4,1):.3f}s",
                  flush=True)


if __name__ == "__main__":
    main()
