"""Why does the engine take a TE in round 15? Rebuild the exact board it saw.
REAL capture universe (#201), season sums under this league's scoring (#204)."""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP=json.load(open("data/league_captures/fourth_and_forever.json"))
LEAGUE={"roster_positions":CAP["roster_positions"],
        "scoring_settings":{k:v["value"] for k,v in CAP["scoring_settings_observed"].items()},
        "total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season=rdb.season_projections_from_capture()
def f(x):
    try: return float(x)
    except: return None

te_picks=[p for p in D if p["position"]=="TE" and p["round"] in (15,16)]
print("TE picks in rounds 15-16:", len(te_picks))
AT=te_picks[0]["overall"]
prior=D[:AT-1]; me=D[AT-1]["roster_id"]
mine=[p for p in prior if p["roster_id"]==me]
print(f"\n=== pick {AT} (round {D[AT-1]['round']}), seat {me}. Engine took a {D[AT-1]['position']}.")
print("    my roster:", dict(collections.Counter(p['position'] for p in mine)), f"({len(mine)} players)")
rows=dr.compute_draft_board(merger, players_db,
      [{"player_id":p["player_id"],"roster_id":p["roster_id"]} for p in prior], me, LEAGUE,
      sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
rows=[r for r in rows if f(r.get("final_score")) is not None]
rows.sort(key=lambda r:-f(r["final_score"]))
print(f"\n    {'pos':4}{'proj':>7}{'bpa':>9}{'need':>7}{'depth':>7}{'disp':>8}{'FINAL':>9}")
for r in rows[:10]:
    print(f"    {r['position']:4}{(f(r.get('projected_points')) or 0):>7.0f}{(f(r.get('bpa')) or 0):>9.1f}"
          f"{(f(r.get('need_bonus')) or 0):>7.1f}{(f(r.get('depth_exposure')) or 0):>7.1f}"
          f"{(f(r.get('displacement_adj')) or 0):>8.1f}{(f(r.get('final_score')) or 0):>9.1f}")
print("\n    top-40 composition:", dict(collections.Counter(r["position"] for r in rows[:40])))
print("    remaining pool     :", dict(collections.Counter(r["position"] for r in rows)))
lv=dr.replacement_levels(pd.DataFrame(rows),"projected_points",LEAGUE["roster_positions"],12)
print("    replacement levels :", {k:round(v,1) for k,v in lv.items()})
print("    shared alternatives:", {k:round(v,1) for k,v in dr.shared_slot_alternatives(lv,LEAGUE["roster_positions"]).items()})
