"""What each arm puts on the PURE BENCH, from the recorded drafts (#216 / #221).

`pure_bench` is the probe's own flag for a state where every starting slot is already
filled, so the pick is depth and nothing else. Reading the two arms side by side there
separates what the shared alternative changed from what it inherited.
"""
import collections, json, pathlib, sys

OUT = []
for fmt in ("12T_ppr", "12T_ppr_SF", "OWNER_3RR_SF_noTE"):
    d = json.load(open(pathlib.Path(__file__).resolve().parents[1] / "drafts" / f"{fmt}.json"))
    by = {(r["arm"], r["seat"]): r for r in d["drafts"]}
    OUT.append(f"== {fmt}")
    tally = {"SELF": collections.Counter(), "SHARED": collections.Counter()}
    for seat in sorted({s for (_, s) in by}):
        for arm in ("SELF", "SHARED"):
            r = by[(arm, seat)]
            picks = [(s["chosen"].get("position"), str(s["chosen"].get("name"))[:18])
                     for s in r["states"] if s["pure_bench"]]
            tally[arm].update(p for p, _ in picks)
            OUT.append(f"  seat {seat:>2} {arm:<7} " + " ".join(f"{p}:{n}" for p, n in picks))
    for arm in ("SELF", "SHARED"):
        t = tally[arm]; n = sum(t.values())
        OUT.append(f"  TOTAL {arm:<7} {dict(t)}  WR share {t['WR']}/{n}")
    OUT.append("")
print("\n".join(OUT))
