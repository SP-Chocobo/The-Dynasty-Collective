"""Mandate 2.6: the counting difference where multi-eligible players actually get drafted."""
import sys, json; sys.path.insert(0, ".")
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import lineup_optimizer as lo, player_universe as pu, league_config as lc, run_draft_battery as rdb

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); weekly = rdb.weekly_projections_from_capture()
scoring = rdb.scoring_settings_from_capture()
PRICING = dict(sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
               weekly_projections=weekly)
arm = next(e for e in db.league_matrix(scoring) if e["label"] == "HEAVY_IDP")
league = arm["league"]; merger.set_league_format(db.league_format_hint(league))
teams, rounds = int(arm["teams"]), int(arm["rounds"])
order = ds.generate_pick_order(list(range(1, teams + 1)), total_rounds=rounds, draft_type="snake")
ROUNDS_PLAYED = 20
picks = []
for i in range(min(teams * ROUNDS_PLAYED, len(order))):
    rid = order[i]
    board = dr.compute_draft_board(merger, players_db, picks, my_roster_id=rid, league=league,
                                   mode="balanced", **PRICING)
    if not board:
        break
    picks.append({"pick_no": i + 1, "roster_id": str(rid), "player_id": board[0]["player_id"]})

roster_positions = league.get("roster_positions") or []
slots = lo.slots_from_roster_positions(roster_positions)
multi = [p for p in picks if len(pu.player_eligible_positions(players_db.get(str(p["player_id"])) or {})) > 1]
by_primary = dr.team_filled_by_position(picks, players_db)

# ASSIGNMENT-AWARE: solve each team's lineup over its own drafted players and count the slots
# actually filled. This is what "counted against eligibility" has to mean for a player who can
# only occupy one slot.
by_assignment = {}
for rid in sorted({str(p["roster_id"]) for p in picks}):
    roster = [{"id": str(p["player_id"]), "value": 1.0,
               "eligible": pu.player_eligible_positions(players_db.get(str(p["player_id"])) or {})}
              for p in picks if str(p["roster_id"]) == rid]
    solved = lo.optimize_lineup(roster, slots)
    counts = {}
    slot_eligible = {sl["slot_id"]: sl["eligible"] for sl in slots}
    for pair in (solved.get("assignments") or []):
        slot_id = pair["slot_id"]
        # A slot's NAME, from its own eligible set when it is a dedicated slot; a shared slot
        # (FLEX, SUPER_FLEX, IDP_FLEX) is counted under its own id, because a player filling one
        # is not filling a dedicated position at all -- which is the distinction the primary-label
        # count cannot make.
        elig = slot_eligible.get(slot_id) or set()
        base = next(iter(elig)) if len(elig) == 1 else str(slot_id).split("_")[0]
        counts[base] = counts.get(base, 0) + 1
    by_assignment[rid] = counts

positions = sorted({p for c in list(by_primary.values()) + list(by_assignment.values()) for p in c})
table = {}
for pos in positions:
    prim = sum(by_primary.get(r, {}).get(pos, 0) for r in by_primary)
    asg = sum(by_assignment.get(r, {}).get(pos, 0) for r in by_assignment)
    if prim != asg:
        table[pos] = {"counted_by_primary_label": prim, "counted_by_assignment": asg}
print(json.dumps({
    "arm": arm["label"], "rounds_played": ROUNDS_PLAYED, "picks": len(picks),
    "slot_count": len(slots),
    "multi_eligible_drafted": len(multi),
    "multi_eligible_pct_of_picks": round(100.0 * len(multi) / max(len(picks), 1), 1),
    "where_the_two_counts_differ": table,
    "demand_by_primary": {k: round(v, 2) for k, v in sorted(
        dr.remaining_starter_demand(roster_positions, teams, picks, players_db).items()) if v},
}, indent=2))
