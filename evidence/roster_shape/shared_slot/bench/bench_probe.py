"""At the PURE-BENCH state, is the board taking receivers because nothing else is left,
or because it prices them above what is left? (#216 / #221)

Both arms take the SAME six receivers in rounds 10-15 of 12T_ppr_SF seat 1, so whatever
produces the bench is common to the shipped engine and the shared alternative. This dumps
the board at rounds 10 and 13 in BOTH arms, top rows plus the best remaining body at every
position, so "the tail is receivers" can be told apart from "receivers are overpriced".
"""
import collections, sys
from unittest import mock
import data_merger as dm, draft_battery as db, draft_room as dr, draft_strategy as ds
import lineup_optimizer as lo, pick_synthesis as ps
import run_216_bench_probe as bench, run_draft_battery as rdb, run_roster_proof as rp

scoring = rdb.scoring_settings_from_capture(); merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture(); season = rdb.season_projections_from_capture()
league, dt = bench.build_league("12T_ppr_SF", scoring)
merger.set_league_format(db.league_format_hint(league))
points = rp.scoreable_pool(merger, players_db, league, season)
rpos = league["roster_positions"]; T = league["total_rosters"]; rounds = len(rpos)
slots = lo.slots_from_roster_positions(rpos)
order = ds.generate_pick_order([str(i) for i in range(1, T+1)], rounds, dt)
STOPS = (10, 13)
HDR = f"{'pos':4}{'name':24}{'proj':>7}{'bpa':>8}{'disp':>8}{'need':>6}{'elig':>6}{'depth':>7}{'FINAL':>8}"

def row(r, tag=""):
    return (f"{r['position']:4}{str(r['name'])[:22]:24}{r['projected_points']:7.1f}"
            f"{(r.get('bpa') or 0):8.1f}{(r.get('displacement_adj') or 0):8.1f}"
            f"{(r.get('need_bonus') or 0):6.1f}{(r.get('eligibility_bonus') or 0):6.1f}"
            f"{(r.get('depth_exposure') or 0):7.1f}{(r.get('final_score') or 0):8.1f}  {tag}")

def run(arm):
    print(f"\n{'='*100}\nARM {arm}\n{'='*100}")
    ctx = (mock.patch.object(dr, "board_slot_alternatives", dr.shared_slot_alternatives)
           if arm == "SHARED" else mock.patch.object(dr, "board_slot_alternatives",
                                                     dr.board_slot_alternatives))
    dr.reset_anchor_caches()
    with ctx:
        picks, taken, mine = [], set(), collections.defaultdict(list)
        for idx in range(min(len(order), rounds * T)):
            who = str(order[idx]); rnd = idx // T + 1
            free = [p for p in points if p not in taken]
            if who != "1":
                chosen = rp.control_pick(free, points, mine[who], players_db, slots)
            else:
                board = dr.compute_draft_board(merger, players_db, picks, "1", league, mode="balanced",
                                               sleeper_projections=season,
                                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
                live = [r for r in board if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
                ranked = sorted(live, key=ps._board_order)
                if rnd in STOPS:
                    held = collections.Counter(players_db[p]["position"] for p in mine["1"])
                    print(f"\n--- round {rnd}, roster {dict(held)} ---")
                    print(HDR)
                    for r in ranked[:8]:
                        print(row(r))
                    seen = set()
                    for r in ranked:
                        p = r["position"]
                        if p not in seen and p not in {x["position"] for x in ranked[:8]}:
                            seen.add(p); print(row(r, "<- best remaining at this position"))
                    if rnd == STOPS[-1]:
                        return
                chosen = str(ranked[0]["player_id"])
            taken.add(str(chosen)); mine[who].append(str(chosen))
            picks.append({"pick_no": idx + 1, "round": rnd, "roster_id": who, "player_id": str(chosen)})

for arm in ("SELF", "SHARED"):
    run(arm)
