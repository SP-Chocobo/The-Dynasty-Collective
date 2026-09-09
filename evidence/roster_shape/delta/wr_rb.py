"""WR:RB BALANCE ONLY. Owner: "in the context of wr vs rb exclusively. te is kinda its own
animal" -- and "10 of one position and 2 of another is too far off... 7 vs 4 is about the ratio
i'd say is the lower edge."

7/4 = 1.75. Read as ONE-SIDED, because he has separately ruled that WR >= RB need not hold and
that RB-heavy is defensible allocation: the constraint is on WR OVER RB, not on RB over WR.
Both directions are reported anyway so the asymmetry is visible rather than assumed.

TE and QB are deliberately NOT scored here. TE is its own animal (floor/pressure-release, his
words); QB is governed by superflex vs 1QB and by his separately stated 2-3-4 band.
"""
import collections, json, pathlib, sys
EDGE = 7 / 4
rows = []
for root in sys.argv[1:]:
    for f in sorted(pathlib.Path(root).glob("*.json")):
        d = json.load(open(f))
        for r in d["drafts"]:
            c = r.get("composition") or {}
            wr, rb = c.get("WR", 0), c.get("RB", 0)
            rows.append((d["format"], r["seat"], r["arm"], wr, rb,
                         (wr / rb) if rb else float("inf")))

for arm in ("SELF", "SHARED"):
    sel = [x for x in rows if x[2] == arm]
    over = [x for x in sel if x[5] > EDGE]
    under = [x for x in sel if x[5] < 1 / EDGE]
    worst = max(sel, key=lambda x: x[5])
    print(f"{arm:7} n={len(sel):>3}   WR/RB over {EDGE:.2f}: {len(over):>3} "
          f"({100*len(over)/len(sel):4.1f}%)   RB/WR over {EDGE:.2f}: {len(under):>3}   "
          f"worst WR/RB {worst[3]}/{worst[4]} in {worst[0]}")

print(f"\nEVERY SEAT THE WIRED ENGINE PUTS OVER {EDGE:.2f}, worst first:")
bad = sorted([x for x in rows if x[2] == "SHARED" and x[5] > EDGE], key=lambda x: -x[5])
for fmt, seat, arm, wr, rb, ratio in bad:
    print(f"  {fmt:22} seat {seat:>2}   WR {wr:>2} / RB {rb:>2}  = {ratio:.2f}")
print(f"\n  ({len(bad)} of {len([x for x in rows if x[2]=='SHARED'])} wired seats)")

print(f"\nAND WHAT THE SHIPPED ENGINE DID, same rule:")
bad2 = sorted([x for x in rows if x[2] == "SELF" and x[5] > EDGE], key=lambda x: -x[5])
for fmt, seat, arm, wr, rb, ratio in bad2[:12]:
    print(f"  {fmt:22} seat {seat:>2}   WR {wr:>2} / RB {rb:>2}  = {ratio:.2f}")
print(f"  ({len(bad2)} of {len([x for x in rows if x[2]=='SELF'])} shipped seats)")
