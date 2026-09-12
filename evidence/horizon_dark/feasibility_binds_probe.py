"""Does feasibility_first EVER bind? A mutation that survives an inert code path proves nothing
about the suite (#245: identical numbers are a broken instrument until proven otherwise)."""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
import draft_strategy as ds, lineup_optimizer as lo, run_roster_proof as rp

merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

cap = json.loads(open("data/league_captures/fourth_and_forever.json").read())
league = {"roster_positions": cap["roster_positions"],
          "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
          "total_rosters": 12, "settings": {"type": 2}}
league["draft_rounds"] = dr.draftable_slots_per_team(league["roster_positions"])
merger.set_league_format(db.league_format_hint(league))
rounds = int(league["draft_rounds"])
slots = lo.slots_from_roster_positions(league["roster_positions"])
seats = [str(i) for i in range(1, 13)]
pick_order = ds.generate_pick_order(seats, rounds, "snake")
points = rp.scoreable_pool(merger, players_db, league, season)

picks, taken, mine = [], set(), {}
for idx in range(rounds * 12):
    seat = str(pick_order[idx])
    free = [pid for pid in points if pid not in taken]
    chosen = rp.control_pick(free, points, mine.get(seat, []), players_db, slots) if free else None
    if chosen is None: break
    taken.add(str(chosen)); mine.setdefault(seat, []).append(str(chosen))
    picks.append({"pick_no": idx+1, "round": idx//12+1, "roster_id": seat, "player_id": str(chosen)})

print(f"board: {len(picks)} picks, rounds={rounds}\n")
print(f"{'picks':>6} {'seat':>5} {'rows':>6} {'_feasible==0':>13} {'==1':>6}   BINDS?")
for at in (0, 60, 120, 180, 240, 288, 300, 311):
    sofar = picks[:at]
    seat = str(pick_order[at]) if at < len(pick_order) else seats[0]
    drafted = {str(p["player_id"]) for p in sofar}
    pool = dr.build_available_pool(
        merger, players_db, drafted, dr.league_usable_positions(league["roster_positions"]),
        sleeper_projections=season, scoring_settings=league.get("scoring_settings"),
        pool_scope="all", sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    dr._derive_points_and_source(pool)
    f = dr.feasibility_first(pool, sofar, players_db, seat, league["roster_positions"],
                             draft_rounds=rounds)
    z, o = int((f == 0).sum()), int((f == 1).sum())
    print(f"{at:>6} {seat:>5} {len(pool):>6} {z:>13} {o:>6}   "
          f"{'YES -- reorders' if 0 < z < len(pool) else 'no (uniform column)'}")
