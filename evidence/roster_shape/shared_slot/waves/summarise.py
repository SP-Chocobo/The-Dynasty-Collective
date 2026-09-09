"""Wave summary: band breaches, ordering verdict and lineup points, SELF vs SHARED (#221).

The ordering verdict is COARSE -- WR10/RB2/TE1 passes `WR >= RB > TE` -- so the band is
reported beside it rather than instead of it, and both are reported rather than one chosen.
"""
import json, math, pathlib, sys

roots = [pathlib.Path(p) for p in sys.argv[1:]]
rows = []
for root in roots:
    for f in sorted(root.glob("*.json")):
        d = json.load(open(f))
        for r in d["drafts"]:
            band = (r.get("band") or {}).get("target_total") or {}
            comp = r.get("composition") or {}
            breaches, dist = 0, 0.0
            for pos, target in band.items():
                if target is None:
                    continue
                n = comp.get(pos, 0)
                lo, hi = math.floor(target), math.ceil(target)
                if n < lo:
                    breaches += 1; dist += lo - n
                elif n > hi:
                    breaches += 1; dist += n - hi
            v = r.get("verdict_full_roster") or {}
            rows.append({
                "format": d["format"], "seat": r["seat"], "arm": r["arm"], "comp": comp,
                "breaches": breaches, "dist": round(dist, 2),
                "strict": v.get("pass_strict"), "owner": v.get("pass_flex_te", v.get("pass_tendency")),
                "lineup": r.get("lineup_points"),
                "unfillable": len(r.get("unfillable_starting_slots") or []),
                "forced": r.get("forced", 0),
            })

key = lambda r: (r["format"], r["seat"])
pairs = {}
for r in rows:
    pairs.setdefault(key(r), {})[r["arm"]] = r

print(f"{'format':22}{'seat':>5}  {'SELF comp':30}{'br':>3}{'d':>5}{'ord':>6} | "
      f"{'SHARED comp':30}{'br':>3}{'d':>5}{'ord':>6} | {'lineup d':>9}")
tot = {"SELF": [0, 0.0, 0], "SHARED": [0, 0.0, 0]}
n = wins = losses = 0
for k in sorted(pairs):
    p = pairs[k]
    if "SELF" not in p or "SHARED" not in p:
        continue
    n += 1
    a, b = p["SELF"], p["SHARED"]
    for arm, r in (("SELF", a), ("SHARED", b)):
        tot[arm][0] += r["breaches"]; tot[arm][1] += r["dist"]
        tot[arm][2] += 1 if (r["strict"] or r["owner"]) else 0
    oa = "PASS" if (a["strict"] or a["owner"]) else "fail"
    ob = "PASS" if (b["strict"] or b["owner"]) else "fail"
    if oa == "fail" and ob == "PASS": wins += 1
    if oa == "PASS" and ob == "fail": losses += 1
    ca = "/".join(f"{q}{a['comp'].get(q,0)}" for q in ("QB", "RB", "WR", "TE"))
    cb = "/".join(f"{q}{b['comp'].get(q,0)}" for q in ("QB", "RB", "WR", "TE"))
    flag = "  <== REGRESSION" if (oa == "PASS" and ob == "fail") else ""
    print(f"{k[0]:22}{k[1]:>5}  {ca:30}{a['breaches']:>3}{a['dist']:>5.0f}{oa:>6} | "
          f"{cb:30}{b['breaches']:>3}{b['dist']:>5.0f}{ob:>6} | "
          f"{(b['lineup'] or 0) - (a['lineup'] or 0):>9.1f}{flag}")
print()
print(f"n = {n} format/seat pairs")
for arm in ("SELF", "SHARED"):
    print(f"  {arm:7} band breaches {tot[arm][0]:>4}   band distance {tot[arm][1]:>7.1f}   ordering passes {tot[arm][2]:>3}/{n}")
print(f"  ordering: {wins} fail->PASS, {losses} PASS->fail")
delta = sum((pairs[k]["SHARED"]["lineup"] or 0) - (pairs[k]["SELF"]["lineup"] or 0)
            for k in pairs if "SELF" in pairs[k] and "SHARED" in pairs[k])
base = sum((pairs[k]["SELF"]["lineup"] or 0) for k in pairs if "SELF" in pairs[k] and "SHARED" in pairs[k])
print(f"  lineup points SHARED - SELF: {delta:+.1f} over {base:.0f} ({100*delta/base:+.2f}%)")
bad = [r for r in rows if r["unfillable"] or r["forced"]]
print(f"  illegal or forced rosters: {len(bad)} of {len(rows)}"
      + ("" if not bad else " -- " + "; ".join(f"{r['format']}/{r['seat']}/{r['arm']}" for r in bad)))
