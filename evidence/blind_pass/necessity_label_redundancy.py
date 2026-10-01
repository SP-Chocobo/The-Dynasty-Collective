"""Does the necessity LABEL tell a reader anything the rest of the card has not already said?

The card already shows rank, tav, uv, the four team terms, forfeit, survival, cliff tier and a
forces list. If "STRONG ACTION" is a near-deterministic function of those, it is a fifth way of
saying what four other fields say -- and a label that restates its own inputs reads as
independent corroboration when it is not.

Measured on the stored snapshots of a real 192-pick draft, both arms, because the ordering
repair changed what rank MEANS and the question is about the post-repair card.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json, math, collections

SC = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"

def entropy(counter):
    n = sum(counter.values())
    return -sum((c / n) * math.log2(c / n) for c in counter.values() if c) if n else 0.0

def conditional_entropy(pairs):
    """H(label | given)."""
    by = collections.defaultdict(collections.Counter)
    for given, label in pairs:
        by[given][label] += 1
    n = len(pairs)
    return sum((sum(c.values()) / n) * entropy(c) for c in by.values())

for arm, name in (("traj_control.json", "before"), ("traj_treatment.json", "after")):
    picks = json.load(open(SC + arm))
    rows = []
    for p in picks:
        cands = p["snapshot"].get("candidates") or []
        for rank, c in enumerate(cands, start=1):
            if c.get("necessity") is None:
                continue
            rows.append({
                "rank": rank, "label": c.get("necClass") or c.get("necessity"),
                "score": float(c["necessity"]) if isinstance(c.get("necessity"), (int, float)) else None,
                "forfeit": c.get("forfeit"), "tav": c.get("tav"),
            })
    labels = collections.Counter(r["label"] for r in rows)
    print("=== %s ===  rows=%d  distinct labels=%d" % (name, len(rows), len(labels)))
    print("   label census: %s" % dict(labels.most_common()))

    H = entropy(labels)
    H_rank = conditional_entropy([(r["rank"], r["label"]) for r in rows])
    H_r3 = conditional_entropy([(min(r["rank"], 6), r["label"]) for r in rows])
    print("   H(label)            = %.3f bits" % H)
    print("   H(label | rank)     = %.3f bits   -> rank explains %.0f%% of it" % (H_rank, 100*(1-H_rank/H) if H else 0))
    print("   H(label | rank<=6)  = %.3f bits   -> %.0f%%" % (H_r3, 100*(1-H_r3/H) if H else 0))

    # The sharpest reading: does the label ever DISAGREE with the order it sits beside?
    disagree = same = 0
    for p in picks:
        cands = [c for c in (p["snapshot"].get("candidates") or [])
                 if isinstance(c.get("necessity"), (int, float))]
        if len(cands) < 2:
            continue
        top = cands[0]["necessity"]
        best_below = max((c["necessity"] for c in cands[1:]), default=None)
        if best_below is None:
            continue
        if best_below > top:
            disagree += 1
        else:
            same += 1
    tot = disagree + same
    print("   turns where a LOWER-ranked candidate scores HIGHER necessity: %d of %d (%.0f%%)"
          % (disagree, tot, 100 * disagree / tot if tot else 0))
    print()

# ---------------------------------------------------------------------------------------
# The payload carries the LABEL, not the score, so the disagreement check above measured
# nothing (it guarded on isinstance(..., float) and excluded every row). Redone ordinally.
ORDER = ["badge-necessity-low", "badge-necessity-close-call", "badge-necessity-preferred",
         "badge-necessity-strong", "badge-necessity-must-take"]
RANKOF = {k: i for i, k in enumerate(ORDER)}

print("=" * 70)
for arm, name in (("traj_treatment.json", "after"),):
    picks = json.load(open(SC + arm))
    disagree = same = turns = 0
    where = collections.Counter()
    louder_at = []
    for p in picks:
        cands = [c for c in (p["snapshot"].get("candidates") or []) if c.get("necClass")]
        if len(cands) < 2:
            continue
        turns += 1
        top = RANKOF.get(cands[0]["necClass"], -1)
        below = [(RANKOF.get(c["necClass"], -1), i) for i, c in enumerate(cands[1:], start=2)]
        best, at = max(below)
        if best > top:
            disagree += 1
            louder_at.append(at)
        else:
            same += 1
        for i, c in enumerate(cands, start=1):
            if c["necClass"] in ("badge-necessity-strong", "badge-necessity-must-take"):
                where[i] += 1
    print("=== %s: does the label ever point somewhere the rank does not? ===" % name)
    print("  turns examined: %d" % turns)
    print("  turns where a LOWER-ranked candidate carries a STRONGER label: %d (%.0f%%)"
          % (disagree, 100 * disagree / turns if turns else 0))
    if louder_at:
        print("  ranks it points to: %s" % dict(collections.Counter(louder_at).most_common(6)))
    print()
    print("  the two 'act now' labels fire at these board ranks: %s" % dict(where.most_common(8)))
    print("  total act-now labels: %d   at rank 1: %d" % (sum(where.values()), where.get(1, 0)))
