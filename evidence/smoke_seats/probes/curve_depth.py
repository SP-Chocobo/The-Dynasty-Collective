"""Is acting_now_value SCALE-FREE with respect to absolute value?

v1 could never take TE6: his final_score is low. v2 takes him if the TE curve is
locally steep at his depth. So measure regret DOWN the curve, not just at the top:
for depth k, regret(k) = curve[k] - _curve_at(curve, k + E[N]), alongside the
absolute final_score at that depth. If regret stays high where value is low, the
key has discarded value.
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

# Table C's measured expected_taken over a 22-pick gap, from positional_forfeits' docstring.
E = {"QB": 0.82, "RB": 3.48, "WR": 3.96, "TE": 2.26}

league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                              te_premium=False, dynasty=True)
merger.set_league_format(db.league_format_hint(league))
board = dr.compute_draft_board(
    merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
    sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
curves = ds._curves_on({str(r["player_id"]): r for r in board}, "final_score")

print("12T_ppr  --  value vs regret at depth k, expected_taken held at table C")
print(f"{'k':>3}" + "".join(f"{p+' val':>10}{p+' reg':>10}" for p in ("QB", "RB", "WR", "TE")))
for k in (0, 2, 4, 6, 8, 12, 16, 20, 30):
    cells = ""
    for p in ("QB", "RB", "WR", "TE"):
        c = curves[p]
        if k >= len(c):
            cells += f"{'-':>10}{'-':>10}"; continue
        cells += f"{c[k]:>10.2f}{c[k] - ds._curve_at(c, k + E[p]):>10.2f}"
    print(f"{k:>3}" + cells)
