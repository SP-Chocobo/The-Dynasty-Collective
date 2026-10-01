"""RESIDUAL2 — does the TE deduction PREDICT which seats hoard?

Runs the pre-registration in RESIDUAL2_PREREGISTRATION.md. Forks A/B/C were fixed before this
file existed. Reads displacement_adjustments' OWN returned dict; nothing reconstructed.
Run from the repo root with PYTHONPATH=.
"""
import json, statistics as st
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
L = {"roster_positions": RP,
     "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
     "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft_balanced.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()

# Groups fixed in the pre-registration, from the published RESIDUAL1 counts.
HOARD = {"2", "5", "9", "12"}
STARVE = {"1", "3", "8", "10", "11"}
CHECKPOINTS = (5, 7, 9)

STATE = {}
_da = dr.displacement_adjustments
def da_spy(rp, rpos, levels, unpriced=None):
    out = _da(rp, rpos, levels, unpriced)
    STATE.clear()
    STATE["level_TE"] = levels.get("TE")
    e = out.get("TE") or {}
    STATE["adj"] = e.get("adjustment"); STATE["disp"] = e.get("displaced")
    STATE["basis"] = e.get("basis")
    return out
dr.displacement_adjustments = da_spy

def prod_picks(upto):
    """Production SHAPE, not just production values -- mode reads `round` (doctrine)."""
    return [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
             "player_id": q["player_id"]} for i, q in enumerate(D[:upto])]

REQUIRED = {"pick_no", "round", "roster_id", "player_id"}
_probe = prod_picks(10)
assert not (REQUIRED - set(_probe[0])), f"pick records missing {REQUIRED - set(_probe[0])}"

rows = []
for seat in sorted({q["roster_id"] for q in D}, key=int):
    idxs = [i for i, q in enumerate(D) if q["roster_id"] == seat]
    for n in CHECKPOINTS:
        if n > len(idxs): continue
        at = idxs[n - 1]                       # the board this seat faced for its nth own pick
        prior = D[:at]
        held = sum(1 for q in prior if q["roster_id"] == seat and q["position"] == "TE")
        STATE.clear()
        dr.compute_draft_board(m, players_db, prod_picks(at), seat, L, mode="balanced",
                               sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rows.append({"seat": seat, "n": n, "te_held": held,
                     "adj": STATE.get("adj"), "disp": STATE.get("disp"),
                     "level": STATE.get("level_TE"), "basis": STATE.get("basis"),
                     "group": "HOARD" if seat in HOARD else "STARVE" if seat in STARVE else "mid"})
dr.displacement_adjustments = _da
json.dump(rows, open("evidence/roster_shape/ff_rulebook/residual2_raw.json", "w"), indent=1)
print(f"RAW SAVED: {len(rows)} observations\n")

FINAL = {}
for q in D:
    FINAL.setdefault(q["roster_id"], 0)
    if q["position"] == "TE": FINAL[q["roster_id"]] += 1

for n in CHECKPOINTS:
    print(f"=== at each seat's {n}th own pick")
    print(f"  {'seat':>5}{'group':>8}{'final TE':>10}{'TE held here':>14}"
          f"{'TE adj':>10}{'displaced':>11}{'level':>9}{'basis':>12}")
    for r in sorted([x for x in rows if x["n"] == n], key=lambda x: int(x["seat"])):
        f = lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else str(v)
        print(f"  {r['seat']:>5}{r['group']:>8}{FINAL[r['seat']]:>10}{r['te_held']:>14}"
              f"{f(r['adj']):>10}{f(r['disp']):>11}{f(r['level']):>9}{str(r['basis'])[:11]:>12}")
    grp = {}
    for g in ("HOARD", "STARVE"):
        vals = [x["adj"] for x in rows if x["n"] == n and x["group"] == g and x["adj"] is not None]
        zero = sum(1 for v in vals if v == 0.0)
        real = [v for v in vals if v != 0.0]
        grp[g] = (real, zero)
        print(f"    {g:7} n={len(vals)}  adjustment==0.0 (open slot, a CONSTRUCTION) in {zero}"
              f"   mean of the rest = {st.mean(real):.2f}" if real else
              f"    {g:7} n={len(vals)}  all {zero} are 0.0 -- nothing to average")
    held = {g: [x["te_held"] for x in rows if x["n"] == n and x["group"] == g] for g in ("HOARD","STARVE")}
    print(f"    DIVERGED YET? TE held -- HOARD {held['HOARD']}  STARVE {held['STARVE']}")
    print()
