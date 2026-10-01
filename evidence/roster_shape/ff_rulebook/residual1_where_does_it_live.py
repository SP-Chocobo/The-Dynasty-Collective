"""RESIDUAL, first characterisation: with the mode effect REMOVED, where does the TE excess live?

The balanced-mode ablation arm is the cleanest dataset for this question -- mode is held at
"balanced" for all 26 rounds, so nothing here is the mode boundary. It still finished 21.8% TE
against the humans' 15.5%, and 29.2% across rounds 15-26.

This asks only: is that excess UNIFORM across seats and rounds, or CONCENTRATED? A uniform
excess points at a pricing bias every chair shares. A concentrated one points at something
path-dependent -- a feedback loop a seat falls into. They are different investigations, and
this decides which one is next. No new drafts, no board builds, no engine calls.
Run from the repo root with PYTHONPATH=.
"""
import json, statistics

def load(name):
    return json.load(open(f"evidence/roster_shape/ff_rulebook/{name}"))["picks"]
AUTO = load("ff_draft.json")
BAL = load("ff_draft_balanced.json")
POS = ("QB", "RB", "WR", "TE")
# The twelve real managers, from the same league. HANDOFF records 15.5% TE overall.
HUMAN_TE_PCT = 15.5

def by_seat(D, pos="TE"):
    seats = {}
    for r in D:
        seats.setdefault(r["roster_id"], 0)
        if r["position"] == pos:
            seats[r["roster_id"]] += 1
    return [seats[k] for k in sorted(seats, key=int)]

print("TE bodies per seat (26 picks each; the humans took 3-6)\n")
for label, D in (("AUTO  (mode=auto)", AUTO), ("BAL   (balanced x26)", BAL)):
    counts = by_seat(D)
    print(f"  {label:22} {counts}")
    print(f"  {'':22} min={min(counts)} max={max(counts)} "
          f"median={statistics.median(counts):.1f} stdev={statistics.pstdev(counts):.2f} "
          f"total={sum(counts)}")
print()

print("how concentrated? share of all TEs held by the top-3 seats\n")
for label, D in (("AUTO", AUTO), ("BAL", BAL)):
    c = sorted(by_seat(D), reverse=True)
    print(f"  {label:6} top3={sum(c[:3])}/{sum(c)} = {100*sum(c[:3])/sum(c):.0f}%   "
          f"bottom3={sum(c[-3:])}/{sum(c)} = {100*sum(c[-3:])/sum(c):.0f}%")
print("  (uniform would be 25% / 25%)\n")

print("BALANCED arm: TE share by round, and how many DISTINCT seats took a TE that round\n")
print(f"  {'round':>6}{'TE picks':>10}{'of 12':>8}{'distinct seats':>16}")
for rd in range(1, 27):
    rows = [r for r in BAL if r["round"] == rd]
    te = [r for r in rows if r["position"] == "TE"]
    print(f"  {rd:>6}{len(te):>10}{len(rows):>8}{len({r['roster_id'] for r in te}):>16}")

print("\nCONCENTRATED, so: what distinguishes a hoarder seat from a starver seat?")
print("Cheapest discriminator available from the draft alone -- WHEN a seat took its first TE.\n")
print(f"  {'seat':>5}{'TE total':>10}{'first TE at own pick #':>24}{'first TE round':>16}")
rows = []
for seat in sorted({r["roster_id"] for r in BAL}, key=int):
    mine = [r for r in BAL if r["roster_id"] == seat]
    total = sum(1 for r in mine if r["position"] == "TE")
    first = next((i + 1 for i, r in enumerate(mine) if r["position"] == "TE"), None)
    rnd = next((r["round"] for r in mine if r["position"] == "TE"), None)
    rows.append((seat, total, first, rnd))
    print(f"  {seat:>5}{total:>10}{str(first):>24}{str(rnd):>16}")

pairs = [(f, t) for _, t, f, _ in rows if f is not None]
if len(pairs) > 2:
    import statistics as st
    xs = [p[0] for p in pairs]; ys = [p[1] for p in pairs]
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in pairs)
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    print(f"\n  Pearson r(first-TE pick number, total TEs) = {num/den:+.3f}  n={len(pairs)}")
    print("  NOTE: n=12 seats in ONE draft. This is a DISCRIMINATOR SEARCH, not an estimate --")
    print("  it says which hypothesis is worth a pre-registered test, and nothing more.")
