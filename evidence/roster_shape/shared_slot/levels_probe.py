"""Do the anchors move at the same rate? One draft, every position's replacement level per round.

The four-quarterback seat traces to QB's level sitting at 207.5 at every round while other
positions' levels move. That is an ASSERTION until the other positions are measured beside it.
"""
import sys, collections
import data_merger as dm, draft_battery as db, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, pick_synthesis as ps
import run_216_bench_probe as bench, run_draft_battery as rdb, run_roster_proof as rp

label = sys.argv[1] if len(sys.argv) > 1 else "OWNER_3RR_SF_noTE"
seat = sys.argv[2] if len(sys.argv) > 2 else "1"
scoring = rdb.scoring_settings_from_capture()
merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league, draft_type = bench.build_league(label, scoring)
merger.set_league_format(db.league_format_hint(league))
points = rp.scoreable_pool(merger, players_db, league, season)
rpos = league["roster_positions"]; T = league["total_rosters"]
rounds = len(rpos); slots = lo.slots_from_roster_positions(rpos)
order = ds.generate_pick_order([str(i) for i in range(1, T + 1)], rounds, draft_type)
picks, taken, mine = [], set(), collections.defaultdict(list)
print(f"{label} seat {seat}")
print(f"{'rnd':>3} {'QB level':>9} {'RB level':>9} {'WR level':>9} {'TE level':>9} |"
      f" {'QB demand':>9} {'RB demand':>9} {'WR demand':>9} {'TE demand':>9}")
for idx in range(min(len(order), rounds * T)):
    who = str(order[idx]); free = [p for p in points if p not in taken]
    if not free: break
    if who != seat:
        chosen = rp.control_pick(free, points, mine[who], players_db, slots)
    else:
        board = dr.compute_draft_board(merger, players_db, picks, seat, league, mode="balanced",
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
        # level = projection - bpa, recovered from the row itself: true on BOTH the demand-rank
        # and startable-floor branches, because it is read from the answer.
        lvl = {}
        for pos in ("QB", "RB", "WR", "TE"):
            rows = [r for r in live if r["position"] == pos and r.get("bpa") is not None]
            if rows:
                r0 = max(rows, key=lambda r: r["projected_points"])
                lvl[pos] = r0["projected_points"] - r0["bpa"]
        dem = dr.remaining_starter_demand(rpos, T, picks, players_db)
        f = lambda v: f"{v:9.1f}" if v is not None else f"{'—':>9}"
        print(f"{idx // T + 1:>3} " + " ".join(f(lvl.get(p)) for p in ("QB", "RB", "WR", "TE")) +
              " |" + " ".join(f"{dem.get(p, 0):9.2f}" for p in ("QB", "RB", "WR", "TE")))
        chosen = str(sorted(live, key=ps._board_order)[0]["player_id"])
    taken.add(str(chosen)); mine[who].append(str(chosen))
    picks.append({"pick_no": idx + 1, "round": idx // T + 1, "roster_id": who, "player_id": str(chosen)})
