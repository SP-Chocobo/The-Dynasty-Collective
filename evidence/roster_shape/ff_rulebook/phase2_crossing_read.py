"""Reads phase2_crossing.json. Every number here came from a production return value."""
import json
J = json.load(open("evidence/roster_shape/ff_rulebook/phase2_crossing.json"))
B, A = J["boards"], J["anchor"]
POS = ("QB", "RB", "WR", "TE")
print(f"anchor (predraft, production predraft_replacement_anchor): "
      f"{ {p: round(A[p],2) for p in POS if p in A} }")
print(f"startable floors: { {k: round(v,2) for k,v in (J['floors'] or {}).items()} }\n")

print("Q3 -- WHICH BASIS PRODUCTION SELECTS, observed from _fill_omitted_from_anchor's own return")
print(f"{'pos':5}{'first anchored at':>19}{'demand there':>14}{'demand before':>15}{'basis stamp':>18}")
cross = {}
for p in POS:
    first = next((b for b in B if b["filled_from_anchor"] and p in b["filled_from_anchor"]), None)
    if first is None:
        floored = any(b["floored"] and p in b["floored"] for b in B)
        print(f"{p:5}{'never':>19}{'':>14}{'':>15}"
              f"{('has startable floor -> not eligible' if floored else 'stayed live'):>18}")
        continue
    k = first["board_after_picks"]; cross[p] = k
    prev = B[k-1] if k else None
    d_now = (first["demand"] or {}).get(p)
    d_prev = (prev["demand"] or {}).get(p) if prev else None
    print(f"{p:5}{('after '+str(k)+' picks'):>19}{d_now:>14.10f}"
          f"{(f'{d_prev:.10f}' if d_prev is not None else '--'):>15}{str(first['basis'][p]):>18}")

print("\nQ4 -- WHAT CHANGES AT THE CROSSING: the LAST live level vs the anchor that replaces it")
print(f"{'pos':5}{'last live':>12}{'anchor':>10}{'jump':>10}{'as % of live':>14}"
      f"{'live pool n':>13}")
for p in POS:
    if p not in cross: continue
    k = cross[p]
    last = B[k-1]["live"].get(p) if (k and B[k-1]["live"]) else None
    if last is None:
        print(f"{p:5}{'none':>12}"); continue
    an = A[p]
    print(f"{p:5}{last:>12.2f}{an:>10.2f}{an-last:>+10.2f}{100*(an-last)/last:>13.1f}%"
          f"{B[k-1]['live_pool_n']:>13}")

print("\nQ1/Q2 -- THE LIVE TRAJECTORY against the fixed anchor (production LIVE(_points) call)")
print(f"{'after':>6} " + "".join(f"{p+' live':>12}{'d':>9}" for p in POS))
for b in B:
    k = b["board_after_picks"]
    if k % 26 and k not in cross.values() and not any(k == c-1 for c in cross.values()): continue
    cells = ""
    for p in POS:
        lv = (b["live"] or {}).get(p)
        if lv is None:
            anc = b["filled_from_anchor"] and p in b["filled_from_anchor"]
            cells += f"{('ANCHORED' if anc else 'omitted'):>12}{'':>9}"
        else:
            cells += f"{lv:>12.2f}{lv-A[p]:>+9.2f}"
    mark = "  <-" if (k in cross.values() or any(k == c-1 for c in cross.values())) else ""
    print(f"{k:>6} " + cells + mark)

print("\nIS THE LIVE LEVEL CONSTANT WHILE IN DOMAIN? (the anchor's stated justification)")
for p in POS:
    vals = [(b["board_after_picks"], b["live"][p]) for b in B
            if b["live"] and p in b["live"]]
    if not vals: print(f"  {p}: never live"); continue
    first_k, first_v = vals[0]; last_k, last_v = vals[-1]
    dev = max(abs(v - A[p]) for _, v in vals)
    print(f"  {p}: live at {len(vals)} boards, first(after {first_k})={first_v:.2f} "
          f"last(after {last_k})={last_v:.2f} anchor={A[p]:.2f}  "
          f"max|live-anchor|={dev:.2f}")
