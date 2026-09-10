"""RESIDUAL5 -- read-only analysis of the four saved 312-pick artifacts.

INVOCATION: none. This script runs no engine code and builds no board. It reads
ff_draft.json / ff_draft_revseat.json / ff_draft_3rr.json / ff_draft_balanced.json,
already on disk, and derives (a) composition conservation under pick-order permutation
and (b) the lag-1 neighbour autocorrelation of TE counts on the snake lattice.

BASIS TAG: ARTIFACT-READ. Nothing here is a fresh measurement and nothing here bears
on the #218 reproduction gate.

The lag-1 statistic and its one-sided direction were specified by the Fable advisory
(ADVISORY_fable_symmetry_break.md) BEFORE this script existed. Run from the repo root.
"""
import json, random, statistics as st, pathlib

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
ARMS = ("ff_draft", "ff_draft_revseat", "ff_draft_3rr", "ff_draft_balanced")
SEED = 20260910
DRAWS = 200_000


def picks(name):
    return json.load(open(OUT / f"{name}.json"))["picks"]


def te_by_slot(p):
    """Slot is the ROUND-1 order, not the roster_id -- revseat proves the label is inert."""
    slot, count = {}, {}
    for r in p:
        if r["round"] == 1 and r["roster_id"] not in slot:
            slot[r["roster_id"]] = len(slot) + 1
        count[r["roster_id"]] = count.get(r["roster_id"], 0) + (r["position"] == "TE")
    return [count[rid] for rid, _ in sorted(slot.items(), key=lambda kv: kv[1])]


def lag1(v):
    """Pearson lag-1 on the LINEAR lattice. A snake has no wraparound: slot 12 picks twice
    at the turn, so 12 and 1 are not neighbours. Wrapping would invent an adjacency."""
    m = sum(v) / len(v)
    den = sum((x - m) ** 2 for x in v)
    if not den:
        return float("nan")
    return sum((v[i] - m) * (v[i + 1] - m) for i in range(len(v) - 1)) / den


def main():
    base = picks("ff_draft")
    print("=" * 72, "\nPART 1 -- composition under permutation\n")
    bset = set(r["player_id"] for r in base)
    for name in ARMS[1:]:
        arm = picks(name)
        aset = set(r["player_id"] for r in arm)
        same_overall = sum(1 for x, y in zip(base, arm) if x["player_id"] == y["player_id"])
        seatmap_b = {r["player_id"]: r["roster_id"] for r in base}
        seatmap_a = {r["player_id"]: r["roster_id"] for r in arm}
        same_seat = sum(1 for p in bset & aset if seatmap_b[p] == seatmap_a[p])
        # same_seat is VACUOUS for revseat -- that arm relabels the seats by construction,
        # so a roster_id match would mean the relabelling failed. Read the same_overall
        # column there instead; 312/312 is the determinism check.
        note = "  (same_seat vacuous: labels reversed)" if "revseat" in name else ""
        print(f"  base vs {name:20s} set_identical={bset == aset}  "
              f"same_overall={same_overall}/312  same_seat={same_seat}/{len(bset & aset)}{note}")

    print("\n" + "=" * 72, "\nPART 2 -- neighbour autocorrelation (statistic PRE-SPECIFIED)\n")
    random.seed(SEED)
    for name in ("ff_draft", "ff_draft_3rr", "ff_draft_balanced"):
        v = te_by_slot(picks(name))
        obs = lag1(v)
        vv, draws = list(v), []
        for _ in range(DRAWS):
            random.shuffle(vv)
            draws.append(lag1(vv))
        p = (sum(1 for d in draws if d <= obs) + 1) / (DRAWS + 1)
        print(f"  {name:20s} {v}")
        print(f"  {'':20s} r={obs:+.3f}  null={st.mean(draws):+.3f} ({st.pstdev(draws):.3f})"
              f"  P(perm <= obs)={p:.4f}")


if __name__ == "__main__":
    main()
