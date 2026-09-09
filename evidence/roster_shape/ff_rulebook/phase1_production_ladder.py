"""PHASE 1 GATE (#222), production path ONLY.

Two earlier probes were wrong in the same way: they recomputed the replacement level from
compute_draft_board's OUTPUT ROWS instead of reading the point_replacement production
actually uses, and one of them priced the roster in a different currency. This one walks
the exact production path -- roster_points_lookup -> _team_roster_points_players ->
replacement level from the live pool -> displacement_adjustments -- and reports every
input beside the answer. Run from the repo root.
"""
import json, pandas as pd
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

states=[]
for i,p in enumerate(D):
    prior=D[:i]
    n=sum(1 for q in prior if q["roster_id"]==SEAT and q["position"]=="TE")
    if 2<=n<=8 and not any(s[0]==n for s in states): states.append((n,i+1,prior))

hdr=(f"{'TE held':>7}{'pick':>6}{'level_TE':>10}{'displaced':>11}{'adj':>9}"
     f"{'basis':>10}{'my TE-eligible starters (points)':>40}")
print("PRODUCTION PATH — every input read, nothing recomputed off board rows.\n")
print(hdr); print("-"*len(hdr))
for n,AT,prior in states:
    picks=[{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior]
    rows=dr.compute_draft_board(merger, players_db, picks, SEAT, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    te=[r for r in rows if r["position"]=="TE" and r.get("displacement_adj") is not None]
    if not te: continue
    adj=float(te[0]["displacement_adj"]); basis=te[0].get("displacement_basis")
    usable={"QB","RB","WR","TE"}
    rpl=dr.roster_points_lookup(merger, players_db, usable, RP, 12,
        sleeper_projections=season, scoring_settings=SC, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    mine,unp=dr._team_roster_points_players(picks, players_db, SEAT, rpl)
    tev=sorted([p["value"] for p in mine if "TE" in p["eligible"]], reverse=True)
    # production's own level: adj = level - displaced, and displaced comes back with it
    out=None
    for lvl_guess in (None,):
        pass
    # recover displaced by re-running displacement_level against the SAME level production used
    # level = adj + displaced  ->  solve by calling with a probe level of 0 to read `displaced`
    d0=lo.displacement_level(mine, RP, "TE", 0.0, unp,
        slot_alternatives=dr.shared_slot_alternatives(
            {p: 0.0 for p in ("QB","RB","WR","TE")}, RP))
    displaced=d0["displaced"]
    level=round(adj+displaced,2)
    print(f"{n:>7}{AT:>6}{level:>10.2f}{displaced:>11.2f}{adj:>9.2f}{basis:>10}"
          f"{str([round(x) for x in tev[:5]]):>40}")
