"""Two repeated computations inside ONE snapshot, each ablated in process, both arms here.

THE TWO CANDIDATES, each a MEASURED call count from probes/profile_draft.py and
probes/repeat_work.py on one opening snapshot of arm 12T_ppr (identical at eac7491 and HEAD):

  A. `draft_room.build_available_pool` -- 14 calls, 1 distinct argument tuple (92.9% repeat).
     The pool's contents are a function of (drafted_player_ids, usable_positions, pool_scope,
     sleeper_basis); `my_roster_id` is not among them. One `build_snapshot` builds 13 boards
     (mine, plus one per unique roster_id in `draft_strategy._build_opponent_boards`) and each
     rebuilds the identical pool.

  B. `draft_room._players_db_fingerprint` -- 27 calls. It hashes every field of all 6,594
     player rows. Its own docstring measures ONE call at a median 30.5 ms and costs it against
     "a snapshot key that cost 60 ms in total" -- i.e. as though it ran once. It runs 27 times
     (26 from `anchor_cache_key`, which every board calls for `_points` and again for
     `trade_value`, plus `snapshot_input_key`). `players_db` is read-only for the life of a
     draft (`simulate_full_draft`: "Reads merger/players_db/league only; never mutates them").

THE A/B IS ONE PROCESS, ONE CODE VERSION, TOGGLING THE SINGLE THING UNDER TEST
(engine-measurement, "Before/after comparisons"). Never a fresh run against a saved baseline.

ORDER IS CONTROLLED AND REPORTED. `DataMerger.merge_player` is memoized per merger instance, so
the first build of the process pays a cold name resolution every later build gets free. The
first build is always BASELINE and is excluded from every ratio; each arm is then measured
twice, in a sequence that does not advantage one.

BEHAVIOUR IS CHECKED, NOT ASSUMED. Each build's candidate count and top-5 player ids are
recorded; if an ablation changes the board it is not a no-op and the timings are not comparable.
That check is the thing that distinguishes this from "disabling it made it faster".

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
      python3 evidence/performance/probes/ablate_repeats.py <arm_label> <tag> \
        [<traj.json> <at_pick>]

With a trajectory and a pick index, the board is built at that MID-DRAFT state instead of the
opening one, replayed from a draft that really happened -- which is the only state where
`depth_exposure` is `measured` and `displacement_adj` is non-zero. Without them it is the
opening board, where the pool is at its largest and the pool figure is therefore an UPPER bound.

Run from the REPO ROOT of the commit being measured, ALONE on the box.
"""
import json
import os
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

REAL_POOL = dr.build_available_pool
REAL_FP = dr._players_db_fingerprint

#: `mode="auto"` reads `round` off the picks to resolve upside-vs-balanced, so a pick record
#: missing it silently selects the other valuation (#222). Schema-validated, not value-validated.
REQUIRED_PICK_FIELDS = {"pick_no", "round", "roster_id", "player_id"}

#: Build 0 is always the cold one and is always BASELINE, so it is the build that pays the cold
#: `_merge_memo` fill and is excluded from every ratio. After it, three full rotations of all
#: four arms in the same order: every arm gets n=3 at comparable cache warmth, and no arm sits
#: systematically earlier (warmer-trending) than another. A plan with n=1 on the baseline makes
#: the headline a difference against a single sample.
PLAN = [(False, False)] + [(False, False), (True, False), (False, True), (True, True)] * 3


def main():
    label, tag = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    merger, players_db, season, universe = pf.fixture()
    entry = pf.arm(label)
    kw = pf.board_inputs(merger, players_db, season, entry)
    pick_order = kw.pop("pick_order")
    merger_, pdb_, league = kw.pop("merger"), kw.pop("players_db"), kw.pop("league")
    mode = entry.get("mode", "auto")
    num_teams = entry["teams"]
    counts = {}

    picks, at = [], 0
    if len(sys.argv) > 4:
        at = int(sys.argv[4])
        src = json.load(open(sys.argv[3]))
        taken = src["picks"][:at]
        if len(taken) != at:
            raise RuntimeError(f"trajectory holds {len(src['picks'])} picks, asked for {at}")
        picks = [{"pick_no": i + 1, "round": i // num_teams + 1,
                  "roster_id": str(p["roster"]), "player_id": str(p["player"])}
                 for i, p in enumerate(taken)]
        missing = REQUIRED_PICK_FIELDS - set(picks[0])
        assert not missing, f"pick records are missing {missing}; mode='auto' reads `round`"
        unknown = [p["player_id"] for p in picks if str(p["player_id"]) not in pdb_]
        assert not unknown, f"{len(unknown)} replayed picks are outside this board's universe"
    seat = str(pick_order[at])
    round_no = at // num_teams + 1
    pick_label = f"{round_no}.{(at % num_teams) + 1:02d}"
    print(f"STATE n_picks_replayed={len(picks)} at_index={at} round={round_no} "
          f"pick_label={pick_label} seat={seat}", flush=True)

    def run(pool_memo_on, fp_memo_on):
        pool_memo, fp_memo = {}, {}
        counts.clear()
        counts.update(pool_calls=0, pool_builds=0, fp_calls=0, fp_computes=0)

        def pool_spy(merger, players_db, drafted, usable, *a, **k):
            counts["pool_calls"] += 1
            if not pool_memo_on:
                counts["pool_builds"] += 1
                return REAL_POOL(merger, players_db, drafted, usable, *a, **k)
            kk = (tuple(sorted(drafted)), tuple(sorted(usable)),
                  k.get("pool_scope", a[2] if len(a) > 2 else "all"), k.get("sleeper_basis"))
            if kk not in pool_memo:
                counts["pool_builds"] += 1
                pool_memo[kk] = REAL_POOL(merger, players_db, drafted, usable, *a, **k)
            # Callers own what they receive, so the cached frame is copied out. The copy is
            # paid on all 13 repeats, which makes the saving measured a LOWER BOUND.
            return pool_memo[kk].copy()

        def fp_spy(players_db):
            counts["fp_calls"] += 1
            if not fp_memo_on:
                counts["fp_computes"] += 1
                return REAL_FP(players_db)
            kk = id(players_db)
            if kk not in fp_memo:
                counts["fp_computes"] += 1
                fp_memo[kk] = REAL_FP(players_db)
            return fp_memo[kk]

        dr.build_available_pool = pool_spy
        dr._players_db_fingerprint = fp_spy
        try:
            t = time.time()
            snap = ps.build_snapshot(merger_, pdb_, picks, pick_order, at, seat,
                                     league, pick_label=pick_label, mode=mode,
                                     upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
                                     **kw)
            el = time.time() - t
        finally:
            dr.build_available_pool = REAL_POOL
            dr._players_db_fingerprint = REAL_FP
        return el, snap, dict(counts)

    rows = []
    print(f"\n{'#':>2} {'pool_memo':>9} {'fp_memo':>7} {'seconds':>8} "
          f"{'pool_calls':>10} {'pool_builds':>11} {'fp_calls':>8} {'fp_computes':>11} "
          f"{'n_cand':>6}", flush=True)
    for i, (pm, fm) in enumerate(PLAN):
        el, snap, c = run(pm, fm)
        ids = [cd.player_id for cd in snap.candidates]
        nm = sum(1 for cd in snap.candidates
                 if getattr(cd, "depth_basis", None) == "measured")
        rows.append({"i": i, "pool_memo": pm, "fp_memo": fm, "seconds": el,
                     "n_candidates": len(snap.candidates), "top5": ids[:5],
                     "n_depth_measured": nm, **c})
        print(f"{i:2d} {str(pm):>9} {str(fm):>7} {el:8.3f} "
              f"{c['pool_calls']:10d} {c['pool_builds']:11d} {c['fp_calls']:8d} "
              f"{c['fp_computes']:11d} {len(snap.candidates):6d}"
              f"  depth_measured={nm}", flush=True)

    warm = rows[1:]

    def mean(pm, fm):
        v = [r["seconds"] for r in warm if r["pool_memo"] == pm and r["fp_memo"] == fm]
        return (sum(v) / len(v) if v else None), len(v)

    base, nb = mean(False, False)
    pool, npl = mean(True, False)
    fp, nfp = mean(False, True)
    both, nbo = mean(True, True)
    print(f"\ncold_first_build={rows[0]['seconds']:.3f}s (BASELINE, excluded from every ratio)")
    print(f"n_warm_builds={len(warm)}")
    for nm, val, n in (("baseline        ", base, nb), ("pool memo       ", pool, npl),
                       ("fingerprint memo", fp, nfp), ("both            ", both, nbo)):
        if val is None:
            print(f"{nm}  n=0  NOT MEASURED")
        else:
            d = "" if base is None else f"  saves {base-val:7.3f}s  ({(base-val)/base*100:5.1f}%)"
            print(f"{nm}  n={n}  mean={val:7.3f}s{d}")

    tops = {tuple(r["top5"]) for r in rows}
    ncs = {r["n_candidates"] for r in rows}
    ok = len(tops) == 1 and len(ncs) == 1
    print(f"\nn_distinct_top5_across_{len(rows)}_builds={len(tops)}  "
          f"n_distinct_candidate_counts={len(ncs)}")
    print("BEHAVIOUR: " + ("IDENTICAL board on every build -- the ablations are no-ops in "
                           "output and the timings are comparable"
                           if ok else
                           "A BUILD DIFFERED -- an ablation changed the answer, so these "
                           "timings compare two different computations and must not be quoted"))
    json.dump({"tag": tag, "label": label, "at_pick": at, "n_picks_replayed": len(picks),
               "rows": rows, "behaviour_identical": ok,
               "means": {"baseline": base, "pool_memo": pool, "fp_memo": fp, "both": both}},
              open(f"{OUT}/ABLATE_{tag}_{label}_at{at}.json", "w"), indent=1)
    print(f"\nWROTE {OUT}/ABLATE_{tag}_{label}_at{at}.json", flush=True)


if __name__ == "__main__":
    main()
