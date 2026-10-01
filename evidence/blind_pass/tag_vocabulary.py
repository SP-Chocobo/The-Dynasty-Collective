"""What CATEGORICAL vocabularies does a candidate card already carry, and do they overlap?

"What should the lineup of tags be" cannot be answered by designing a nicer set, because the
card is not a blank page: `forces`, `waitNote`, `cliffTier`, `flagged` and the necessity label
are five categorical channels already on the payload. A sixth vocabulary, or a reshaped
necessity one, has to answer for what those already say -- otherwise it is #126 wearing a badge.

So: census every categorical field, and measure whether the necessity label is PREDICTABLE from
the others. If it is, the tag lineup is not short of categories; the card is long on them.

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json, math, collections

SC = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
picks = json.load(open(SC + "traj_treatment.json"))
rows = [c for p in picks for c in (p["snapshot"].get("candidates") or [])]
print("candidate rows: %d\n" % len(rows))

def entropy(counter):
    n = sum(counter.values())
    return -sum((c/n) * math.log2(c/n) for c in counter.values() if c) if n else 0.0

def cond_entropy(pairs):
    by = collections.defaultdict(collections.Counter)
    for g, l in pairs:
        by[g][l] += 1
    n = len(pairs)
    return sum((sum(c.values())/n) * entropy(c) for c in by.values())

print("=== the categorical channels already on a card ===")
CHANNELS = ("necClass", "cliffTier", "waitNote", "flagged", "replacementBasis",
            "depthBasis", "displacementBasis", "survivalBasis", "denialTeam")
for k in CHANNELS:
    vals = collections.Counter(
        (tuple(sorted(c[k])) if isinstance(c.get(k), list) else c.get(k)) for c in rows)
    present = sum(v for kk, v in vals.items() if kk not in (None, ()))
    top = [(str(kk)[:34], v) for kk, v in vals.most_common(4)]
    print("  %-20s populated %5d/%d (%3.0f%%)  distinct=%-3d  %s"
          % (k, present, len(rows), 100*present/len(rows), len(vals), top))

forces = collections.Counter()
for c in rows:
    for f in (c.get("forces") or []):
        forces[str(f)[:40]] += 1
print("\n=== `forces` -- the list of what FIRED, which is the reason channel that exists ===")
print("  rows carrying at least one force: %d (%.0f%%)"
      % (sum(1 for c in rows if c.get("forces")),
         100*sum(1 for c in rows if c.get("forces"))/len(rows)))
for k, v in forces.most_common(12):
    print("    %-42s %5d" % (k, v))

print("\n=== is the necessity label PREDICTABLE from the channels already shown? ===")
labelled = [c for c in rows if c.get("necClass")]
H = entropy(collections.Counter(c["necClass"] for c in labelled))
print("  H(necClass) = %.3f bits" % H)
for name, key in (("forces (as a set)", lambda c: tuple(sorted(str(f) for f in (c.get("forces") or [])))),
                  ("cliffTier", lambda c: c.get("cliffTier")),
                  ("waitNote", lambda c: c.get("waitNote")),
                  ("forces + cliffTier", lambda c: (tuple(sorted(str(f) for f in (c.get("forces") or []))), c.get("cliffTier")))):
    h = cond_entropy([(key(c), c["necClass"]) for c in labelled])
    print("  H(necClass | %-20s) = %.3f  -> explains %3.0f%%" % (name, h, 100*(1-h/H) if H else 0))
