"""PHASE 2 (#222): what does the WR replacement level MEAN in production?

Steps 1-2 of the agreed sequence. FLEX has no level of its own -- shared_slot_alternatives
prices a flex as max(level) over its eligible positions -- so FLEX_8's phantom IS the WR
level and the two questions collapse into one read.

Intercepts replacement_levels to capture the exact pool and arguments production hands it,
then locates the player the returned level lands on BY IDENTITY. Nothing reconstructed.
Run from the repo root.
"""
import json
import pandas as pd
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP=json.load(open("data/league_captures/fourth_and_forever.json")); RP=CAP["roster_positions"]
SC={k:v["value"] for k,v in CAP["scoring_settings_observed"].items()}
LEAGUE={"roster_positions":RP,"scoring_settings":SC,"total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
merger=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
merger.set_league_format(db.league_format_hint(LEAGUE))
season=rdb.season_projections_from_capture()
SEAT="12"

CALLS=[]
real=dr.replacement_levels
def spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
        startable_floors=None, truncated_out=None, flex_occupancy=None):
    out=real(pool, value_col, roster_positions, num_teams, remaining_demand,
             startable_floors, truncated_out, flex_occupancy)
    CALLS.append({"pool":pool, "col":value_col, "demand":remaining_demand,
                  "floors":startable_floors, "occ":flex_occupancy, "out":dict(out)})
    return out
dr.replacement_levels=spy

states=[]
for i,p in enumerate(D):
    prior=D[:i]
    n=sum(1 for q in prior if q["roster_id"]==SEAT and q["position"]=="TE")
    if n in (2,7,8) and not any(s[0]==n for s in states): states.append((n,i+1,prior))

slot_counts=dr.starter_slot_counts(RP)
print("league starter demand (12 teams):", {k:round(v*12,1) for k,v in slot_counts.items() if v})
for n,AT,prior in states:
    CALLS.clear()
    dr.compute_draft_board(merger, players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior], SEAT, LEAGUE,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    # the call whose output the board's point_replacement came from: the LAST one carrying WR
    withwr=[x for x in CALLS if "WR" in x["out"]]
    if not withwr:
        print(f"\n{'='*76}\n{n} TE held, pick {AT}: NO call returned a WR level.")
        print("   calls this board:", [sorted(x["out"]) for x in CALLS])
        continue
    c=withwr[-1]
    pool, col, out = c["pool"], c["col"], c["out"]
    print(f"\n{'='*76}\n{n} TE held, pick {AT}.  replacement_levels called {len(CALLS)}x this board")
    print(f"  remaining_demand passed: {c['demand']}   startable_floors: "
          f"{ {k: round(v,1) for k,v in (c['floors'] or {}).items()} }")
    print(f"  levels returned: { {k: round(v,2) for k,v in sorted(out.items())} }")
    for pos in ("WR","TE"):
        sub=pool[pool["position"]==pos].copy()
        sub[col]=pd.to_numeric(sub[col], errors="coerce")
        sub=sub.dropna(subset=[col]).sort_values(col, ascending=False).reset_index(drop=True)
        lvl=out.get(pos)
        if lvl is None: continue
        hit=sub.index[sub[col].round(2)==round(lvl,2)]
        r=int(hit[0]) if len(hit) else None
        print(f"  {pos}: remaining pool {len(sub)}   level {lvl:.2f}   "
              f"lands at RANK {r+1 if r is not None else '?'}"
              f"   demand rank would be {12*slot_counts.get(pos,0):.1f}")
        if r is not None:
            row=sub.iloc[r]
            print(f"      that player: {row.get('name')}  ({row['position']})  {row[col]:.2f}")
        print(f"      pool top5: {[round(float(v),1) for v in sub[col].head(5)]}"
              f"  … rank30-40: {[round(float(v),1) for v in sub[col].iloc[29:40]]}")
dr.replacement_levels=real
