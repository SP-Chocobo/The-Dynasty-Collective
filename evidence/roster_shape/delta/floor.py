"""Owner: "would you rather get a stab te projecting 8, or a wr8 for your bench projecting 3?"

That is a claim about the BENCH MARGIN: once starters are covered, is the best remaining tight
end meaningfully better than the best remaining receiver? Measured off the real pool, at each
round, as picks come off the board -- not asserted.

Season points here, so divide by 17 for the per-game numbers the question is stated in.
"""
import collections, sys
import data_merger as dm, draft_battery as db, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, run_216_bench_probe as bench, run_draft_battery as rdb, run_roster_proof as rp

scoring = rdb.scoring_settings_from_capture(); merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture(); season = rdb.season_projections_from_capture()
for fmt in ("12T_ppr", "OWNER_3RR_SF_noTE"):
    league, dt = bench.build_league(fmt, scoring)
    merger.set_league_format(db.league_format_hint(league))
    points = rp.scoreable_pool(merger, players_db, league, season)
    rpos = league["roster_positions"]; T = league["total_rosters"]; rounds = len(rpos)
    slots = lo.slots_from_roster_positions(rpos)
    order = ds.generate_pick_order([str(i) for i in range(1, T + 1)], rounds, dt)
    print(f"\n=== {fmt}  ({T} teams, {rounds} rounds, "
          f"{sum(1 for p in rpos if p != 'BN')} starters) ===")
    print(f"{'rnd':>4}  " + "".join(f"{p:>18}" for p in ("QB", "RB", "WR", "TE")) + "   TE-WR/gm")
    taken, mine = set(), collections.defaultdict(list)
    for idx in range(rounds * T):
        who = str(order[idx]); rnd = idx // T + 1
        if idx % T == 0:
            best = {}
            for p in ("QB", "RB", "WR", "TE"):
                cands = [pid for pid in points
                         if pid not in taken and (players_db.get(pid) or {}).get("position") == p]
                best[p] = max((points[c] for c in cands), default=float("nan"))
            gap = (best["TE"] - best["WR"]) / 17.0
            print(f"{rnd:>4}  " + "".join(f"{best[p]:>10.1f} ({best[p]/17:4.1f})" for p in ("QB","RB","WR","TE"))
                  + f"   {gap:+6.2f}")
        free = [p for p in points if p not in taken]
        if not free:
            break
        chosen = rp.control_pick(free, points, mine[who], players_db, slots)
        taken.add(str(chosen)); mine[who].append(str(chosen))
