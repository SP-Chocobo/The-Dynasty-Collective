"""Per-position shape of the acting_now_value regret term, take model held FIXED.

Isolates curve steepness from expected_taken: for n = 1..8 players taken, report
curve[0] - _curve_at(curve, n) on the SAME final_score curve acting_now_value reads.
If the WR/TE inversion is structural, TE's decay must exceed WR's at equal n.
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

SPECS = [
    ("12T_ppr",    dict(teams=12, superflex=False, scoring="ppr",      te_premium=False, dynasty=True)),
    ("12T_ppr_SF", dict(teams=12, superflex=True,  scoring="ppr",      te_premium=False, dynasty=True)),
    ("12T_standard", dict(teams=12, superflex=False, scoring="standard", te_premium=False, dynasty=True)),
]
POS = ["QB", "RB", "WR", "TE", "K", "DEF"]

for label, kw in SPECS:
    league = dr.build_mock_league(**kw)
    merger.set_league_format(db.league_format_hint(league))
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    by_id = {str(r["player_id"]): r for r in board}
    curves = ds._curves_on(by_id, "final_score")
    print("=" * 74)
    print(f"{label}   final_score curve decay from the top, by players taken")
    print(f"{'pos':<5}{'rows':>6}{'best':>9}" + "".join(f"{('n='+str(n)):>8}" for n in (1, 2, 3, 4, 6, 8)))
    for p in POS:
        c = curves.get(p)
        if not c:
            print(f"{p:<5}{'-':>6}"); continue
        cells = "".join(f"{c[0] - ds._curve_at(c, n):>8.2f}" for n in (1, 2, 3, 4, 6, 8))
        print(f"{p:<5}{len(c):>6}{c[0]:>9.2f}{cells}")
