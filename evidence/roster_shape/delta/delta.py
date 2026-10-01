"""THREE-WAY DELTA: what the ENGINE produces, what the BAND targets, what the CONTROL reveals.

Two-way comparisons have been ambiguous all session. Engine-vs-band says the engine breaches;
band-vs-revealed says they agree only half the time; neither says WHICH of the three is wrong.
Three ways does, because the agreement pattern is diagnostic:

  all three agree            -> settled, leave it alone
  band + revealed vs engine  -> the ENGINE is off
  engine + revealed vs band  -> the BAND may be wrong
  engine + band vs revealed  -> most likely the CONTROL's own defect (it stacks what it cannot
                                field), since that is the one arm with a known failure mode
"""
import collections, json, pathlib, statistics, sys
import run_draft_battery as rdb
players_db, _ = rdb.build_players_db_from_capture()
POS = ("QB", "RB", "WR", "TE")

eng = collections.defaultdict(dict)      # fmt -> pos -> [engine counts]
ctl = collections.defaultdict(lambda: collections.defaultdict(list))
band = {}
for root in sys.argv[1:]:
    for f in sorted(pathlib.Path(root).glob("*.json")):
        d = json.load(open(f)); fmt = d["format"]
        for r in d["drafts"]:
            if r["arm"] != "SHARED":
                continue
            band.setdefault(fmt, (r.get("band") or {}).get("target_total") or {})
            for p in POS:
                eng[fmt].setdefault(p, []).append((r.get("composition") or {}).get(p, 0))
            for seat, ids in (r.get("all_rosters") or {}).items():
                if str(seat) == str(r["seat"]):
                    continue
                c = collections.Counter((players_db.get(str(i)) or {}).get("position") for i in ids)
                for p in POS:
                    ctl[fmt][p].append(c.get(p, 0))

import os
TOL = float(os.environ.get("TOL", "0.75"))
verdicts = collections.Counter()
rows = []
for fmt in sorted(eng):
    for p in POS:
        e = statistics.median(eng[fmt][p]); c = statistics.median(ctl[fmt][p]); b = band[fmt].get(p)
        if b is None:
            continue
        eb, ec, bc = abs(e - b) <= TOL, abs(e - c) <= TOL, abs(b - c) <= TOL
        if eb and ec and bc:      v = "settled"
        elif bc and not eb:       v = "ENGINE off"
        elif ec and not eb:       v = "BAND suspect"
        elif eb and not ec:       v = "control defect"
        else:                     v = "all three differ"
        verdicts[v] += 1
        rows.append((fmt, p, e, b, c, v))

print(f"{'verdict':18}{'n':>4}   what it means")
for v, n in verdicts.most_common():
    print(f"{v:18}{n:>4}")
print(f"\ntotal cells: {sum(verdicts.values())}  (format x position, {len(eng)} formats)\n")

for want in ("ENGINE off", "BAND suspect", "all three differ"):
    sel = [r for r in rows if r[5] == want]
    if not sel:
        continue
    print(f"--- {want} ({len(sel)}) ---")
    print(f"  {'format':22}{'pos':5}{'engine':>8}{'band':>8}{'control':>9}")
    for fmt, p, e, b, c, _ in sorted(sel, key=lambda r: -abs(r[2] - r[3])):
        print(f"  {fmt:22}{p:5}{e:>8.1f}{b:>8.1f}{c:>9.1f}")
    print()

print("AGGREGATE per position, median across formats:")
print(f"  {'pos':5}{'engine':>9}{'band':>9}{'control':>9}{'eng-band':>10}{'eng-ctl':>9}")
for p in POS:
    E = statistics.median([statistics.median(eng[f][p]) for f in eng])
    B = statistics.median([band[f][p] for f in eng if band[f].get(p) is not None])
    C = statistics.median([statistics.median(ctl[f][p]) for f in eng])
    print(f"  {p:5}{E:>9.2f}{B:>9.2f}{C:>9.2f}{E-B:>+10.2f}{E-C:>+9.2f}")


print("\nHOW BIG ARE THE ENGINE'S DISAGREEMENTS? (owner: the correct shape is FLUID, so a tight")
print("tolerance around a point target may be manufacturing defects. Sizes, not a verdict.)")
gaps = sorted((abs(e - b), fmt, pp, e, b, c) for fmt, pp, e, b, c, v in rows)
import collections as _c
buckets = _c.Counter()
for g, *_ in gaps:
    buckets["0 - 0.75 (inside tolerance)" if g <= 0.75 else
            "0.75 - 1.5" if g <= 1.5 else
            "1.5 - 2.5" if g <= 2.5 else
            "2.5 - 4" if g <= 4 else "4+"] += 1
for k in ("0 - 0.75 (inside tolerance)", "0.75 - 1.5", "1.5 - 2.5", "2.5 - 4", "4+"):
    print(f"  |engine - band| {k:30} {buckets[k]:>4} of {len(gaps)}")
print("\n  the largest, which no widening dissolves:")
for g, fmt, pp, e, b, c in gaps[-10:][::-1]:
    print(f"    {fmt:22}{pp:5} engine {e:>5.1f}  band {b:>5.1f}  control {c:>5.1f}   gap {g:>4.1f}")
