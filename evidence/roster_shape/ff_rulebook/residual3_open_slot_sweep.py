"""RESIDUAL3 -- does the DOCUMENTED open-slot mechanism separate hoarders from starvers?

NOT a hypothesis of mine. lineup_optimizer.displacement_level's own docstring states an
unfixed residual tight-end bias and names its mechanism:

    "A FOURTH tight end competing for a flex is priced against TE20 while the receiver beside
     him is priced against WR32 -- the ~30-point half of the bias that survives the
     displacement term, BECAUSE THE TERM REPORTS EXACTLY 0.0 WHENEVER THE SLOT IS MERELY OPEN."

And the invariant it is tested against: "the term is exactly 0.0 for any position with an OPEN
DEDICATED slot, on any roster." So whether a seat gets the deduction at all depends on that
seat's own slot occupancy -- which is roster-dependent, and therefore a candidate for the
path-dependence RESIDUAL1 found and RESIDUAL2 failed to explain.

RESIDUAL2 also established the constraint this must respect: at each seat's 9th own pick ALL
TWELVE seats hold exactly one tight end. The divergence is after that, so the sweep runs from
there.

FORKS, FIXED BEFORE THE RUN:
  A  hoarder seats spend materially MORE of picks 9-20 with TE adjustment == 0.0 (an open
     reachable slot, so no deduction) than starver seats. The documented mechanism is
     path-dependent and is a live candidate for the split.
  B  no material difference in the 0.0 rate. The open-slot mechanism does not separate them,
     and it joins the timing proxy and the deduction magnitude as withdrawn.
  C  starvers spend MORE picks at 0.0. Inverted -- the mechanism runs against the split, and
     the finding is that being un-deducted does not make a seat take the position.

Artifact risks, named now: groups were defined by the outcome; n = 4 and 5 seats in ONE draft;
and 0.0 is a CONSTRUCTION, not a measured zero, which is exactly why its RATE is the quantity
here rather than its magnitude. Per-seat rates are reported, not just group means.

Production-shaped picks, mode="balanced" to match the arm, displacement_adjustments' own
returned dict. Run from the repo root with PYTHONPATH=.
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
HOARD = {"2", "5", "9", "12"}; STARVE = {"1", "3", "8", "10", "11"}
FIRST, LAST = 9, 20

STATE = {}
_da = dr.displacement_adjustments
def da_spy(rp, rpos, levels, unpriced=None):
    out = _da(rp, rpos, levels, unpriced)
    STATE.clear()
    e = out.get("TE") or {}
    STATE.update({"adj": e.get("adjustment"), "disp": e.get("displaced"),
                  "basis": e.get("basis"), "level": levels.get("TE")})
    return out
dr.displacement_adjustments = da_spy

def prod_picks(upto):
    return [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
             "player_id": q["player_id"]} for i, q in enumerate(D[:upto])]
assert not ({"pick_no", "round", "roster_id", "player_id"} - set(prod_picks(5)[0]))

rows = []
for seat in sorted({q["roster_id"] for q in D}, key=int):
    idxs = [i for i, q in enumerate(D) if q["roster_id"] == seat]
    for n in range(FIRST, LAST + 1):
        if n > len(idxs): continue
        at = idxs[n - 1]
        held = sum(1 for q in D[:at] if q["roster_id"] == seat and q["position"] == "TE")
        took = D[at]["position"]
        STATE.clear()
        dr.compute_draft_board(m, players_db, prod_picks(at), seat, L, mode="balanced",
                               sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        rows.append({"seat": seat, "n": n, "te_held": held, "took": took,
                     "adj": STATE.get("adj"), "disp": STATE.get("disp"),
                     "level": STATE.get("level"), "basis": STATE.get("basis"),
                     "group": "HOARD" if seat in HOARD else "STARVE" if seat in STARVE else "mid"})
dr.displacement_adjustments = _da
json.dump(rows, open("evidence/roster_shape/ff_rulebook/residual3_raw.json", "w"), indent=1)
print(f"RAW SAVED: {len(rows)} observations (picks {FIRST}-{LAST}, 12 seats)\n")

FINAL = {}
for q in D:
    FINAL.setdefault(q["roster_id"], 0)
    if q["position"] == "TE": FINAL[q["roster_id"]] += 1

print(f"{'seat':>5}{'group':>8}{'final TE':>10}{'picks':>7}{'adj==0.0':>10}{'rate':>8}"
      f"{'mean adj when nonzero':>24}{'TEs taken in window':>21}")
per = {}
for seat in sorted({r["seat"] for r in rows}, key=int):
    mine = [r for r in rows if r["seat"] == seat]
    zeros = [r for r in mine if r["adj"] == 0.0]
    nz = [r["adj"] for r in mine if r["adj"] not in (None, 0.0)]
    took_te = sum(1 for r in mine if r["took"] == "TE")
    rate = len(zeros) / len(mine)
    per.setdefault(mine[0]["group"], []).append(rate)
    print(f"{seat:>5}{mine[0]['group']:>8}{FINAL[seat]:>10}{len(mine):>7}{len(zeros):>10}"
          f"{rate:>8.2f}{(st.mean(nz) if nz else float('nan')):>24.2f}{took_te:>21}")
print()
for g in ("HOARD", "STARVE", "mid"):
    if per.get(g):
        print(f"  {g:7} adj==0.0 rate per seat = {[f'{x:.2f}' for x in per[g]]}  "
              f"mean {st.mean(per[g]):.3f}")
