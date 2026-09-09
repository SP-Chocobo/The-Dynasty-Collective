"""Does displacement_adj GROW as a roster accumulates tight ends?

If it does, the engine has a brake and something else is wrong. If it does not, the
engine literally cannot say "enough" -- the 3rd TE and the 9th TE are charged the same,
and the only thing that ever stops it is the pool running out.
"""
import json, collections, pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

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

# every pick where the seat on the clock ALREADY held N tight ends, N = 2..8
seen={}
for i,p in enumerate(D):
    prior=D[:i]; me=p["roster_id"]
    n_te=sum(1 for q in prior if q["roster_id"]==me and q["position"]=="TE")
    if n_te not in seen and 2<=n_te<=8 and p["position"]=="TE":
        seen[n_te]=(i+1, me, prior)
print("TEs already held -> displacement_adj charged to the NEXT tight end\n")
print(f"{'held':>5}{'pick':>6}{'seat':>5}{'TE disp_adj':>14}{'TE bpa':>10}{'TE final':>10}{'top row pos':>13}")
for n in sorted(seen):
    AT, me, prior = seen[n]
    rows=dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], me, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows=[r for r in rows if f(r.get("final_score")) is not None]
    rows.sort(key=lambda r:-f(r["final_score"]))
    te=[r for r in rows if r["position"]=="TE"]
    if not te: continue
    t=te[0]
    print(f"{n:>5}{AT:>6}{me:>5}{(f(t.get('displacement_adj')) or 0):>14.1f}"
          f"{(f(t.get('bpa')) or 0):>10.1f}{(f(t.get('final_score')) or 0):>10.1f}{rows[0]['position']:>13}")
