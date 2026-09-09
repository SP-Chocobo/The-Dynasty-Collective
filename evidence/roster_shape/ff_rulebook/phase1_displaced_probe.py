"""PHASE 1 GATE (#222): read `displaced` OUT of displacement_level, don't infer it.

The -51.73 recurrence was arithmetic, not diagnosis. displacement_level already returns
{"displaced","adjustment","basis"} (lineup_optimizer.py:496) and the board only surfaces
`adjustment`. This calls it directly at the real saturation states and prints what the
probe actually evicted, alongside the roster it evicted it from.

Run from the repo root.
"""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import lineup_optimizer as lo

CAP=json.load(open("data/league_captures/fourth_and_forever.json")); RP=CAP["roster_positions"]
LEAGUE={"roster_positions":RP,
        "scoring_settings":{k:v["value"] for k,v in CAP["scoring_settings_observed"].items()},
        "total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season=rdb.season_projections_from_capture()
def f(x):
    try: return float(x)
    except: return None

SEAT="12"
states=[]
for i,p in enumerate(D):
    if p["roster_id"]!=SEAT: continue
    prior=D[:i]
    n=sum(1 for q in prior if q["roster_id"]==SEAT and q["position"]=="TE")
    if 2<=n<=8 and not any(s[0]==n for s in states):
        states.append((n,i+1,prior))

print(f"seat {SEAT}. `displaced` READ OUT, not inferred.\n")
hdr=f"{'TE held':>7}{'pick':>6}{'level_TE':>10}{'displaced':>11}{'adj':>9}{'basis':>18}{'floor(min alt)':>15}"
print(hdr); print("-"*len(hdr))
for n,AT,prior in states:
    rows=dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], SEAT, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows=[r for r in rows if f(r.get("final_score")) is not None]
    lv=dr.replacement_levels(pd.DataFrame(rows),"projected_points",RP,12)
    if "TE" not in lv: continue
    alts=dr.shared_slot_alternatives(lv,RP)
    # rebuild the roster exactly as compute_draft_board does: priced holdings, points currency
    mine=[q for q in prior if q["roster_id"]==SEAT]
    pts={str(r["player_id"]):f(r.get("projected_points")) for r in rows}
    # drafted players are OFF the board, so price them from the season projections directly
    sc={k:v["value"] for k,v in CAP["scoring_settings_observed"].items()}
    import player_universe as pu
    roster=[]
    for q in mine:
        v=pu.score_projection(season.get(q["player_id"]) or {}, sc)
        if v: roster.append({"id":q["player_id"],"value":float(v),
                             "eligible":set(pu.player_eligible_positions(players_db.get(q["player_id"]) or {}))})
    out=lo.displacement_level(roster, RP, "TE", float(lv["TE"]), slot_alternatives=alts)
    reach=[s for s in lo.slots_from_roster_positions(RP) if "TE" in s["eligible"]]
    floor=min(alts.get(s["slot_id"], lv["TE"]) for s in reach)
    print(f"{n:>7}{AT:>6}{lv['TE']:>10.2f}{out['displaced']:>11.2f}{out['adjustment']:>9.2f}"
          f"{out['basis']:>18}{floor:>15.2f}")
    tes=sorted((r["value"] for r in roster if r["eligible"]=={"TE"}), reverse=True)
    print(f"{'':>7}my TE values: {[round(x,1) for x in tes]}")
