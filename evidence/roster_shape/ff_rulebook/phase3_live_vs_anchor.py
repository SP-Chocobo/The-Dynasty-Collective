"""#50 INPUT: what information is discarded when a level switches live -> PREDRAFT?

Not "which produces nicer rosters". Only: where both exist, how far apart are they, and
what does the live one know that the anchor cannot?

INSTRUMENT RULE (earned by the sixteenth withdrawal): replacement_levels is called more
than once per board -- the LIVE call from compute_draft_board and the anchor's own call
inside predraft_replacement_anchor. Every capture below is TAGGED by which invocation it
was, identified from the arguments, never assumed. Run from the repo root.
"""
import json, collections
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP=json.load(open("data/league_captures/fourth_and_forever.json")); RP=CAP["roster_positions"]
SC={k:v["value"] for k,v in CAP["scoring_settings_observed"].items()}
L={"roster_positions":RP,"scoring_settings":SC,"total_rosters":12,"settings":{"type":2}}
D=json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
m=dm.DataMerger(); players_db,_=rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L))
season=rdb.season_projections_from_capture()

CALLS=[]
real_rl=dr.replacement_levels
def rl_spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
           startable_floors=None, truncated_out=None, flex_occupancy=None):
    out=real_rl(pool, value_col, roster_positions, num_teams, remaining_demand,
                startable_floors, truncated_out, flex_occupancy)
    # CALL IDENTITY, from the arguments -- not from call order.
    if remaining_demand is None and flex_occupancy is not None: tag="ANCHOR(predraft, full pool)"
    elif remaining_demand is not None and value_col=="_points": tag="LIVE(points, remaining pool)"
    elif value_col=="trade_value": tag="LIVE(trade_value)"
    else: tag=f"OTHER(demand={remaining_demand is not None}, col={value_col})"
    CALLS.append({"tag":tag,"col":value_col,"n_pool":len(pool),"out":dict(out)})
    return out
dr.replacement_levels=rl_spy

FINAL={}
real_da=dr.displacement_adjustments
def da_spy(roster_players, roster_positions, levels, unpriced_eligible=None):
    FINAL.clear(); FINAL.update(dict(levels))
    return real_da(roster_players, roster_positions, levels, unpriced_eligible)
dr.displacement_adjustments=da_spy

print("what the LIVE level knows that the PRE-DRAFT anchor cannot: a drained pool.\n")
for AT in (109,157,182,206):
    CALLS.clear()
    prior=D[:AT-1]
    rows=dr.compute_draft_board(m,players_db,
        [{"player_id":q["player_id"],"roster_id":q["roster_id"]} for q in prior],"12",L,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    basis={}
    for r in rows:
        basis.setdefault(r["position"], r.get("replacement_basis"))
    live=next((c for c in CALLS if c["tag"].startswith("LIVE(points")), None)
    anch=next((c for c in CALLS if c["tag"].startswith("ANCHOR")), None)
    anchor_vals = anch["out"] if anch else dr.predraft_replacement_anchor(
        m, players_db, {"QB","RB","WR","TE"}, RP, 12, "_points",
        sleeper_projections=season, scoring_settings=SC,
        sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
        startable_floors=({"QB": dr.qb_startable_floor(m)} if "SUPER_FLEX" in RP else None))
    print(f"=== pick {AT}   calls: {[c['tag'] for c in CALLS]}")
    print(f"    {'pos':4}{'LIVE':>10}{'ANCHOR':>10}{'delta':>10}{'board used':>16}{'basis':>18}")
    for p in ("QB","RB","WR","TE"):
        lv=(live["out"].get(p) if live else None); an=anchor_vals.get(p); fin=FINAL.get(p)
        d=(f"{lv-an:+.2f}" if (lv is not None and an is not None) else "--")
        used=("LIVE" if (lv is not None and fin is not None and abs(fin-lv)<0.01)
              else "ANCHOR" if (an is not None and fin is not None and abs(fin-an)<0.01)
              else ("absent" if fin is None else "?"))
        print(f"    {p:4}{(f'{lv:.2f}' if lv is not None else 'omitted'):>10}"
              f"{(f'{an:.2f}' if an is not None else 'none'):>10}{d:>10}{used:>16}{str(basis.get(p)):>18}")
dr.replacement_levels=real_rl; dr.displacement_adjustments=real_da
