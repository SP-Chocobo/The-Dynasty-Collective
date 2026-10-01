"""How much of one snapshot's cost is the SAME question asked again?

Wraps the PRODUCTION functions (`DataMerger.merge_player`, `DataMerger._resolve`,
`draft_room.build_available_pool`, `draft_room.compute_draft_board`) and counts calls keyed on
their ARGUMENTS, never on call order -- order is an implementation detail a cache can change
(engine-measurement, "name WHICH CALL you captured"). Nothing is reconstructed: every number
here is a count of real production calls.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/repeat_work.py <arm_label> <tag>

Run from the REPO ROOT of the commit being measured, ALONE on the box.
"""
import json
import os
import sys
import time
from collections import Counter

sys.dont_write_bytecode = True
sys.path.insert(0, "evidence/performance/probes")
import perf_fixture as pf                                     # noqa: E402
import data_merger as dm                                      # noqa: E402
import draft_room as dr                                       # noqa: E402
import pick_synthesis as ps                                   # noqa: E402

OUT = os.environ.get(
    "PERF_OUT",
    "/tmp/claude-0/-home-user-The-Dynasty-Collective/10effc91-a7fc-5b98-9620-9430e59a7fac/scratchpad/perf")


def main():
    label, tag = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    merger, players_db, season, universe = pf.fixture()
    entry = pf.arm(label)
    kw = pf.board_inputs(merger, players_db, season, entry)
    pick_order = kw.pop("pick_order")
    merger_, pdb_, league = kw.pop("merger"), kw.pop("players_db"), kw.pop("league")
    mode = entry.get("mode", "auto")

    merge_keys, resolve_keys, pool_keys, board_keys = Counter(), Counter(), Counter(), Counter()

    real_merge = dm.DataMerger.merge_player
    def merge_spy(self, name, position=None, team=None, **k):
        merge_keys[(name, position, team)] += 1
        return real_merge(self, name, position=position, team=team, **k)

    real_resolve = dm.DataMerger._resolve
    def resolve_spy(self, full_name, position=None, team=None, df=None):
        # df identity, not contents: two calls with the same (name, position, team) against the
        # same table object are the same question.
        resolve_keys[(full_name, position, team, id(df))] += 1
        return real_resolve(self, full_name, position=position, team=team, df=df)

    real_pool = dr.build_available_pool
    def pool_spy(merger, players_db, drafted, usable, *a, **k):
        # The arguments that decide the pool's CONTENTS. drafted/usable as sorted tuples so
        # two calls that ask for the same pool collide on the same key.
        pool_keys[(tuple(sorted(drafted)), tuple(sorted(usable)),
                   k.get("pool_scope", a[2] if len(a) > 2 else "all"),
                   k.get("sleeper_basis"))] += 1
        return real_pool(merger, players_db, drafted, usable, *a, **k)

    real_board = dr.compute_draft_board
    def board_spy(*a, **k):
        board_keys[(k.get("my_roster_id"), k.get("mode"), len(k.get("picks") or []))] += 1
        return real_board(*a, **k)

    dm.DataMerger.merge_player = merge_spy
    dm.DataMerger._resolve = resolve_spy
    dr.build_available_pool = pool_spy
    dr.compute_draft_board = board_spy
    try:
        t0 = time.time()
        snap = ps.build_snapshot(merger_, pdb_, [], pick_order, 0, str(pick_order[0]), league,
                                 pick_label="1.01", mode=mode,
                                 upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
                                 **kw)
        elapsed = time.time() - t0
    finally:
        dm.DataMerger.merge_player = real_merge
        dm.DataMerger._resolve = real_resolve
        dr.build_available_pool = real_pool
        dr.compute_draft_board = real_board

    def report(name, c):
        total = sum(c.values())
        distinct = len(c)
        repeats = total - distinct
        # n printed for every population; a ratio over an empty set is not a ratio.
        print(f"\n{name}: n_calls={total} n_distinct_arg_tuples={distinct} "
              f"n_repeat_calls={repeats} "
              f"repeat_share={(repeats/total*100 if total else float('nan')):.1f}% "
              f"max_calls_for_one_tuple={max(c.values()) if c else 0}", flush=True)
        for k, v in c.most_common(4):
            print(f"    x{v:5d}  {str(k)[:150]}", flush=True)
        return {"n_calls": total, "n_distinct": distinct, "n_repeat": repeats,
                "max_for_one": max(c.values()) if c else 0}

    print(f"\n=== ONE OPENING SNAPSHOT, arm={label} tag={tag} "
          f"seconds={elapsed:.3f} n_candidates={len(snap.candidates)} ===", flush=True)
    out = {"tag": tag, "label": label, "seconds": elapsed,
           "n_candidates": len(snap.candidates),
           "compute_draft_board": report("compute_draft_board", board_keys),
           "build_available_pool": report("build_available_pool", pool_keys),
           "merge_player": report("DataMerger.merge_player", merge_keys),
           "_resolve": report("DataMerger._resolve", resolve_keys)}
    json.dump(out, open(f"{OUT}/REPEAT_{tag}_{label}.json", "w"), indent=1)
    print(f"\nWROTE {OUT}/REPEAT_{tag}_{label}.json", flush=True)


if __name__ == "__main__":
    main()
