"""Why does the TE deduction reset to -51.7 at 7 tight ends held?"""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import lineup_optimizer as lo

CAP=json.load(open("data/league_captures/fourth_and_forever.json"))
RP=CAP["roster_positions"]
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

for AT in (109, 180, 205, 229):
    prior=D[:AT-1]; me=D[AT-1]["roster_id"]
    mine=[p for p in prior if p["roster_id"]==me]
    rows=dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], me, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows=[r for r in rows if f(r.get("final_score")) is not None]
    lv=dr.replacement_levels(pd.DataFrame(rows),"projected_points",RP,12)
    alts=dr.shared_slot_alternatives(lv,RP)
    te=[r for r in rows if r["position"]=="TE"]
    adj=f(te[0].get("displacement_adj")) if te else None
    basis=te[0].get("displacement_basis") if te else None
    n_te=sum(1 for p in mine if p["position"]=="TE")
    print(f"pick {AT:>4} seat {me:>2} | roster {len(mine):>2} ({dict(collections.Counter(p['position'] for p in mine))})")
    print(f"           TE held {n_te} | levels {({k:round(v,1) for k,v in lv.items()})}")
    print(f"           TE_5 alt {alts.get('TE_5')} FLEX alt {alts.get('FLEX_6')} | adj {adj} | basis {basis}")
    if te: print(f"           level_TE - TE_5alt = {round(lv.get('TE',0)-alts.get('TE_5',0),1)}"
                 f"   level_TE - FLEXalt = {round(lv.get('TE',0)-alts.get('FLEX_6',0),1)}")
    print()
