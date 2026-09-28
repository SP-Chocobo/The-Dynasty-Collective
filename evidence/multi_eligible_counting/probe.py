"""Mandate 2.6: what the LABEL-vs-ELIGIBILITY reading is worth in demand, on one IDP draft.

Same formula both ways -- sum over teams of max(slots[pos] - that team's count at pos, 0) -- with
only the COUNT changing: the primary label, versus every position the held player can be started at.
That isolates the question the ruling is about, which my first probe did not: it compared a raw pick
census against slots-filled, two different quantities, and the difference was mostly capacity.
"""
import sys, json; sys.path.insert(0, ".")
import data_merger as dm, draft_room as dr, draft_battery as db, draft_strategy as ds
import player_universe as pu, run_draft_battery as rdb

merger = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture(); weekly = rdb.weekly_projections_from_capture()
scoring = rdb.scoring_settings_from_capture()
PRICING = dict(sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
               weekly_projections=weekly)
arm = next(e for e in db.league_matrix(scoring) if e["label"] == "HEAVY_IDP")
league = arm["league"]; merger.set_league_format(db.league_format_hint(league))
teams, rounds = int(arm["teams"]), int(arm["rounds"])
roster_positions = league.get("roster_positions") or []
order = ds.generate_pick_order(list(range(1, teams + 1)), total_rounds=rounds, draft_type="snake")
slot_counts = dr.starter_slot_counts(roster_positions) if hasattr(dr, "starter_slot_counts") else None
picks = []
snapshots = {}
for i in range(min(teams * 20, len(order))):
    rid = order[i]
    board = dr.compute_draft_board(merger, players_db, picks, my_roster_id=rid, league=league,
                                   mode="balanced", **PRICING)
    if not board:
        break
    picks.append({"pick_no": i + 1, "roster_id": str(rid), "player_id": board[0]["player_id"]})
    if len(picks) in (teams * 5, teams * 10, teams * 15, teams * 20):
        snapshots[f"round_{len(picks)//teams}"] = list(picks)

def demand_by_label(pk):
    return dr.remaining_starter_demand(roster_positions, teams, pk, players_db)

def demand_by_eligibility(pk):
    """The same formula with the count widened to every position the held player can start at."""
    counts = {}
    for p in pk:
        info = players_db.get(str(p["player_id"])) or {}
        for pos in pu.player_eligible_positions(info):
            counts.setdefault(str(p["roster_id"]), {}).setdefault(pos, 0)
            counts[str(p["roster_id"])][pos] += 1
    base = demand_by_label(pk)
    out = {}
    for pos in base:
        slots_per_team = None
        # recover the per-team slot count from the label demand at zero picks
        out[pos] = None
    # recompute directly: slots per team from the empty-draft demand divided by teams
    empty = demand_by_label([])
    for pos, total in empty.items():
        per_team = total / teams
        out[pos] = round(sum(max(per_team - counts.get(str(r), {}).get(pos, 0), 0)
                             for r in range(1, teams + 1)), 2)
    return out

rows = {}
for name, pk in snapshots.items():
    lab, elig = demand_by_label(pk), demand_by_eligibility(pk)
    multi = sum(1 for p in pk
                if len(pu.player_eligible_positions(players_db.get(str(p["player_id"])) or {})) > 1)
    rows[name] = {
        "picks": len(pk), "multi_eligible_held": multi,
        "demand_by_label": {k: round(v, 2) for k, v in sorted(lab.items()) if v or elig.get(k)},
        "demand_by_eligibility": {k: v for k, v in sorted(elig.items()) if v or lab.get(k)},
        "difference": {k: round(elig.get(k, 0) - lab.get(k, 0), 2)
                       for k in sorted(set(lab) | set(elig))
                       if round(elig.get(k, 0) - lab.get(k, 0), 2)},
    }
print(json.dumps({"arm": arm["label"], "teams": teams, "by_round": rows}, indent=2))
