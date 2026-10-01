"""Is intervening_picks CONSTANT across every candidate at a turn?

test_rulings_are_not_silently_dropped records the real W1-07 blocker: the substitute is a
property of the TURN and (1 - survival) is a property of the PLAYER. If intervening_picks is
identical for every candidate in a snapshot, then no denominator can make it differentiate
candidates -- it shifts every necessity score by the SAME amount, which moves labels across
band thresholds (the 62%) while never reordering anything.

That is a prior objection to "which denominator", and it is the one I missed.
"""
import collections, statistics
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds, pick_synthesis as ps

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                             te_premium=False, dynasty=True)
merger.set_league_format(db.league_format_hint(league))
seats = [str(i) for i in range(1, 13)]
pick_order = [str(s) for s in ds.generate_pick_order(seats, 16, "snake")]

opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                mode="balanced", sleeper_projections=season,
                                sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

print(f"{'turn':>5}{'seat':>5}{'cands':>7}{'distinct intervening_picks':>28}"
      f"{'distinct survival':>19}")
for idx in (0, 5, 13, 25, 37):
    seat = pick_order[idx]
    picks = [{"player_id": r["player_id"], "roster_id": pick_order[i],
              "round": i // 12 + 1, "pick_no": i + 1}
             for i, r in enumerate(opening[:idx])]
    snap = ps.build_snapshot(merger, players_db, picks, pick_order, current_index=idx,
                            my_roster_id=seat, league=league,
                            pick_label=f"{idx//12+1}.{idx%12+1:02d}", top_n=12,
                            sleeper_projections=season,
                            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    ip = {c.intervening_picks for c in snap.candidates}
    sv = {round(c.survival_probability, 4) for c in snap.candidates
          if c.survival_probability is not None}
    print(f"{idx:>5}{seat:>5}{len(snap.candidates):>7}"
          f"{str(sorted(x for x in ip if x is not None)):>28}{len(sv):>19}")

print("\nIf the intervening_picks column holds ONE value per turn while survival holds many,")
print("the substitute cannot differentiate candidates under ANY denominator.")
