"""Mandate 2.6, THE OWNER'S RULING: what assignment-based demand actually reprices.

ONE PROCESS, ONE CODE VERSION, one thing toggled -- the counting. The "before" arm rebuilds the
label-based formula this repair replaced (it is still computable: team_filled_by_position survives
as the census) and patches it into the board, so the two boards differ by the counting and by
nothing else. A fresh run against a saved baseline from different code would not be this.

Both arms read the EVEN-SPLIT flex share rather than the measured one, on both sides, because the
question is what the count does and the split is not what changed.
"""
import sys, json; sys.path.insert(0, ".")
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import lineup_optimizer as lo, player_universe as pu, run_draft_battery as rdb

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); weekly = rdb.weekly_projections_from_capture()
scoring = rdb.scoring_settings_from_capture()
PRICING = dict(sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
               weekly_projections=weekly)
ARM = sys.argv[1] if len(sys.argv) > 1 else "HEAVY_IDP"
CHECKPOINTS = [5, 10, 15]

arm = next(e for e in db.league_matrix(scoring) if e["label"] == ARM)
league = arm["league"]; merger.set_league_format(db.league_format_hint(league))
teams, rounds = int(arm["teams"]), int(arm["rounds"])
roster_positions = league.get("roster_positions") or []
order = ds.generate_pick_order(list(range(1, teams + 1)), total_rounds=rounds, draft_type="snake")

REAL_DEMAND = dr.remaining_starter_demand


def demand_by_label(rp, num_teams, picks, pdb, flex_occupancy=None):
    """THE FORMULA THIS REPAIR REPLACED, verbatim in effect: league slot capacity at a position
    minus that team's own picks whose PRIMARY LABEL is that position, floored at zero per team."""
    slot_counts = dr.starter_slot_counts(rp, flex_occupancy, num_teams)
    filled = dr.team_filled_by_position(picks, pdb)
    rosters = list(filled.values()) + [{}] * (num_teams - len(filled))
    return {pos: sum(max(slot_counts.get(pos, 0.0) - roster.get(pos, 0), 0.0)
                     for roster in rosters) for pos in pu.FANTASY_POSITIONS}


def board(picks, roster_id):
    return dr.compute_draft_board(merger, players_db, picks, my_roster_id=roster_id,
                                  league=league, mode="balanced", **PRICING)


def need_bonus_both(picks, roster_id):
    """need_bonus's own inputs, old and new, for one roster -- the second consumer of the count."""
    ded = dr.dedicated_slot_counts(roster_positions)
    slot_counts = dr.starter_slot_counts(roster_positions)
    census = dict(dr.team_filled_by_position(picks, players_db).get(str(roster_id), {}))
    solved = dict(dr.team_slots_filled(picks, players_db, roster_positions).get(str(roster_id), {}))
    open_share = dr.unfilled_slot_share(roster_positions, solved)
    out = {}
    for pos in sorted(pu.FANTASY_POSITIONS):
        d = ded.get(pos, 0)
        old_filled = census.get(pos, 0)
        old_need = max(d - old_filled, 0)
        old_flex = max(max(slot_counts.get(pos, 0) - d, 0) - max(old_filled - d, 0), 0)
        old = min(dr.NEED_BONUS_PER_DEDICATED_SLOT * old_need
                  + dr.NEED_BONUS_PER_FLEX_SHARE * min(old_flex, 1), dr.NEED_BONUS_MAX)
        new_need = max(d - solved.get(pos, 0), 0)
        new_flex = open_share.get(pos, 0.0) - new_need
        new = min(dr.NEED_BONUS_PER_DEDICATED_SLOT * new_need
                  + dr.NEED_BONUS_PER_FLEX_SHARE * min(new_flex, 1), dr.NEED_BONUS_MAX)
        if round(old, 2) != round(new, 2):
            out[pos] = {"old": round(old, 2), "new": round(new, 2)}
    return out


picks, report = [], []
for i in range(min(teams * max(CHECKPOINTS), len(order))):
    rid = order[i]
    rnd = i // teams + 1
    if i % teams == 0 and rnd in CHECKPOINTS:
        entry = {"after_round": rnd - 1, "picks": len(picks)}
        new_demand = REAL_DEMAND(roster_positions, teams, picks, players_db)
        old_demand = demand_by_label(roster_positions, teams, picks, players_db)
        entry["demand"] = {p: {"by_label": round(old_demand[p], 2), "by_assignment": round(new_demand[p], 2)}
                           for p in sorted(new_demand)
                           if round(old_demand[p], 2) != round(new_demand[p], 2)}
        entry["need_bonus_inputs_differ"] = need_bonus_both(picks, rid)
        # THE PRICES. Same picks, same roster, same everything but the count.
        after = board(picks, rid)
        try:
            dr.remaining_starter_demand = demand_by_label
            before = board(picks, rid)
        finally:
            dr.remaining_starter_demand = REAL_DEMAND
        by_id = {r["player_id"]: r for r in before}
        moved = []
        for rank, row in enumerate(after[:40]):
            was = by_id.get(row["player_id"])
            if not was:
                continue
            old_rank = next((k for k, r in enumerate(before) if r["player_id"] == row["player_id"]), None)
            dv = round(float(row["final_score"]) - float(was["final_score"]), 2)
            duv = round(float(row["universal_value"]) - float(was["universal_value"]), 2)
            if dv or (old_rank is not None and old_rank != rank):
                moved.append({"name": row.get("name"), "pos": row.get("position"),
                              "rank": [old_rank, rank], "final_score": dv,
                              "universal_value": duv})
        entry["top40_moved"] = moved[:12]
        entry["top40_moved_n"] = len(moved)
        entry["top_pick"] = {"by_label": before[0].get("name"), "by_assignment": after[0].get("name")}
        entry["multi_eligible_held"] = sum(
            1 for p in picks
            if len(pu.player_eligible_positions(players_db.get(str(p["player_id"])) or {})) > 1)
        report.append(entry)
        print(json.dumps(entry, indent=2), flush=True)
    b = board(picks, rid)
    if not b:
        break
    picks.append({"pick_no": i + 1, "roster_id": str(rid), "player_id": b[0]["player_id"]})

json.dump({"arm": ARM, "teams": teams, "roster_positions": roster_positions,
           "checkpoints": report}, open(f"evidence/multi_eligible_counting/ruling_ab_{ARM}.json", "w"),
          indent=2)
print("WROTE", ARM)
