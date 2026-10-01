"""Does the superflex QB adjustment survive the subtraction in acting_now_value?

replacement_level enters BPA as `projected_points - replacement_level(P)`, so moving it
shifts every QB by the SAME amount. A level shift is invisible to a difference. If that
is what superflex is, then v2's key cannot see superflex at all.

Compare the QB final_score curve in 1QB vs SUPERFLEX, same pool, same everything else.
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

def qb_curve(superflex):
    league = dr.build_mock_league(teams=12, superflex=superflex, scoring="ppr",
                                  te_premium=False, dynasty=True)
    merger.set_league_format(db.league_format_hint(league))
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    return ds._curves_on({str(r["player_id"]): r for r in board}, "final_score")["QB"]

one, sf = qb_curve(False), qb_curve(True)
n = min(len(one), len(sf))

print("QB final_score curve, 12T_ppr (1QB) vs 12T_ppr_SF (superflex)")
print(f"{'k':>3}{'1QB val':>11}{'SF val':>11}{'LEVEL diff':>12}"
      f"{'1QB reg':>10}{'SF reg':>10}{'SLOPE diff':>12}")
for k in (0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 30):
    if k + 1 >= n:
        break
    r1 = one[k] - ds._curve_at(one, k + 1.0)
    rs = sf[k] - ds._curve_at(sf, k + 1.0)
    print(f"{k:>3}{one[k]:>11.2f}{sf[k]:>11.2f}{sf[k]-one[k]:>12.2f}"
          f"{r1:>10.2f}{rs:>10.2f}{rs-r1:>12.2f}")

lvl = [sf[k] - one[k] for k in range(n)]
slp = [(sf[k] - ds._curve_at(sf, k + 1.0)) - (one[k] - ds._curve_at(one, k + 1.0))
       for k in range(n - 1)]
print(f"\nrows compared: {n}")
print(f"LEVEL shift  mean {sum(lvl)/len(lvl):>9.2f}   min {min(lvl):>9.2f}   max {max(lvl):>9.2f}")
print(f"SLOPE change mean {sum(slp)/len(slp):>9.2f}   min {min(slp):>9.2f}   max {max(slp):>9.2f}")
