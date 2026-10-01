"""PHASE 1, done properly: INTERCEPT the real call. Nothing reconstructed, nothing inferred.

Wraps draft_room.displacement_adjustments so it records the exact arguments production
hands it -- the roster, the levels, the unpriced set -- and the exact answer, at every
board build. Run from the repo root.
"""
import json, collections
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP=json.load(open("data/league_captures/fourth_and_forever.json")); RP=CAP["roster_positions"]
SC={k:v["value"] for k,v in CAP["scoring_settings_observed"].items()}
LEAGUE={"roster_positions":RP,"scoring_settings":SC,"total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season=rdb.season_projections_from_capture()
SEAT="12"

CAPTURED={}
real=dr.displacement_adjustments
def spy(roster_players, roster_positions, levels, unpriced_eligible=None):
    out=real(roster_players, roster_positions, levels, unpriced_eligible)
    CAPTURED.clear()
    CAPTURED.update({"level_TE":levels.get("TE"), "n_priced":len(roster_players),
                     "n_unpriced":len(unpriced_eligible or []),
                     "te_vals":sorted([p["value"] for p in roster_players
                                       if "TE" in p["eligible"]], reverse=True),
                     "TE":out.get("TE")})
    return out
dr.displacement_adjustments=spy

states=[]
for i,p in enumerate(D):
    prior=D[:i]
    n=sum(1 for q in prior if q["roster_id"]==SEAT and q["position"]=="TE")
    if 2<=n<=8 and not any(s[0]==n for s in states): states.append((n,i+1,prior))

hdr=f"{'TE held':>7}{'pick':>6}{'level_TE':>10}{'displaced':>11}{'adj':>9}{'roster':>8}{'unpr':>6}"
print("INTERCEPTED from production. Nothing recomputed.\n"); print(hdr); print("-"*len(hdr))
for n,AT,prior in states:
    dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], SEAT, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    c=CAPTURED; te=c.get("TE") or {}
    lv=c.get("level_TE")
    print(f"{n:>7}{AT:>6}{(lv if lv is not None else float('nan')):>10.2f}"
          f"{(te.get('displaced') or float('nan')):>11.2f}{(te.get('adjustment') or 0):>9.2f}"
          f"{c.get('n_priced',0):>8}{c.get('n_unpriced',0):>6}")
    print(f"{'':>7}TE-eligible roster values: {[round(x) for x in c.get('te_vals',[])]}")
dr.displacement_adjustments=real
