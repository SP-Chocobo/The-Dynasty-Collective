"""Does `displaced` equal the entity that actually left the lineup? (#222 Phase 1)

Fork pre-registered in PREREGISTRATION_displaced_contract.md before this ran.
Production path only: displacement_adjustments is intercepted to capture the exact roster,
levels and unpriced set production hands it; the two solves are then reproduced with the
SAME inputs and their assignment sets diffed. Run from the repo root.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import lineup_optimizer as lo

CAP=json.load(open("data/league_captures/fourth_and_forever.json")); RP=CAP["roster_positions"]
SC={k:v["value"] for k,v in CAP["scoring_settings_observed"].items()}
LEAGUE={"roster_positions":RP,"scoring_settings":SC,"total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season=rdb.season_projections_from_capture()
SEAT="12"

GRAB={}
real=dr.displacement_adjustments
def spy(roster_players, roster_positions, levels, unpriced_eligible=None):
    out=real(roster_players, roster_positions, levels, unpriced_eligible)
    GRAB.clear(); GRAB.update({"roster":[dict(p) for p in roster_players],
        "levels":dict(levels), "unpriced":unpriced_eligible, "out":out})
    return out
dr.displacement_adjustments=spy

def solve_pair(roster, levels):
    """Reproduce displacement_level's two solves with production's own inputs."""
    alts=dr.shared_slot_alternatives(levels, RP)
    free=float(levels["TE"])
    slots=lo.slots_from_roster_positions(RP)
    reach=[s for s in slots if "TE" in s["eligible"]]
    alt_of={s["slot_id"]: float(alts.get(s["slot_id"], free)) for s in slots}
    pin={s["slot_id"]: f"__pin_{s['slot_id']}" for s in slots}
    ss=[{**s,"eligible":set(s["eligible"])|{pin[s["slot_id"]]}} for s in slots]
    ph=[{"id":f"__free_{s['slot_id']}","value":alt_of[s["slot_id"]],
         "eligible":{pin[s["slot_id"]]}} for s in slots]
    base=lo.optimize_lineup(list(roster)+ph, ss)
    probe={"id":"__displacement_probe","value":lo._DISPLACEMENT_PROBE_VALUE,"eligible":{"TE"}}
    wp=lo.optimize_lineup(list(roster)+ph+[probe], ss)
    val={p["id"]:p["value"] for p in list(roster)+ph+[probe]}
    b={a["player_id"] for a in base["assignments"]}
    w={a["player_id"] for a in wp["assignments"]}
    left=sorted(b-w, key=lambda i:-val[i])
    return base, wp, left, val, [s["slot_id"] for s in reach], alt_of

states=[]
for i,p in enumerate(D):
    prior=D[:i]
    n=sum(1 for q in prior if q["roster_id"]==SEAT and q["position"]=="TE")
    if n in (2,5,7,8) and not any(s[0]==n for s in states): states.append((n,i+1,prior))

for n,AT,prior in states:
    dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], SEAT, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    roster, levels, out = GRAB["roster"], GRAB["levels"], GRAB["out"]["TE"]
    base, wp, left, val, reach, alt_of = solve_pair(roster, levels)
    print(f"\n{'='*78}\n{n} TE held, pick {AT}. level_TE={levels['TE']:.2f}  "
          f"displaced={out['displaced']:.2f}  adj={out['adjustment']:.2f}")
    print(f"  TE-reachable slots: {reach}")
    print(f"  base total {base['total_value']:.2f} -> with_probe {wp['total_value']:.2f}")
    print(f"  ENTITIES THAT LEFT THE LINEUP: {[(i, round(val[i],2)) for i in left] or 'NONE'}")
    tot=sum(val[i] for i in left)
    verdict = ("A (contract satisfied)" if len(left)==1 and abs(val[left[0]]-out['displaced'])<0.02
               else "C (ambiguous: %d left)"%len(left) if len(left)!=1
               else "B (MISMATCH)")
    print(f"  sum(left)={tot:.2f}   returned displaced={out['displaced']:.2f}   -> {verdict}")
    print("  lineup BEFORE:", sorted(((round(val[a['player_id']],1), a['slot_id'])
          for a in base["assignments"]), reverse=True))
    ph_in=[a['player_id'] for a in base["assignments"] if a['player_id'].startswith('__free_')]
    print(f"  CONSISTENCY -- roster handed in: {len(roster)} players; "
          f"phantoms in base lineup: {len(ph_in)} {ph_in}")
    print(f"  phantom values (alt_of): { {k: round(v,2) for k,v in sorted(alt_of.items())} }")
dr.displacement_adjustments=real
