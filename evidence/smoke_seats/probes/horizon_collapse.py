"""Does LONG-HORIZON regret collapse to the v1 value key?

Reviewer's Option B: baseline at the starters-exhausted index k_exhaust rather than at
the next turn. But replacement_levels sets the replacement rank to exactly the league's
remaining starter demand -- teams x slots(P) -- and BPA is defined as
points - replacement_level(P). So BPA(k_exhaust) == 0 BY CONSTRUCTION, and therefore

    regret_longhorizon(i) = F(i) - F(k_exhaust)  ~=  F(i) - 0  =  F(i)

which IS v1's key. Measure F at k_exhaust to see how close to 0 it lands.
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb, draft_strategy as ds

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

SPECS = [
    ("12T_ppr",    dict(teams=12, superflex=False, scoring="ppr",      te_premium=False)),
    ("12T_ppr_SF", dict(teams=12, superflex=True,  scoring="ppr",      te_premium=False)),
    ("10T_ppr",    dict(teams=10, superflex=False, scoring="ppr",      te_premium=False)),
]

for label, kw in SPECS:
    league = dr.build_mock_league(**kw, dynasty=True)
    merger.set_league_format(db.league_format_hint(league))
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    rows = {str(r["player_id"]): r for r in board}
    teams = kw["teams"]
    slots = dr.starter_slot_counts(
        league.get("roster_positions") or [], num_teams=teams)
    fcurve = ds._curves_on(rows, "final_score")
    ucurve = ds._curves_on(rows, "universal_value")
    print(f"=== {label} ===")
    print(f"{'pos':<5}{'slots/tm':>9}{'k_exh':>7}{'rows':>6}"
          f"{'F(0)':>10}{'F(k_exh)':>11}{'U(k_exh)':>11}")
    for p in ("QB", "RB", "WR", "TE"):
        c, u = fcurve.get(p), ucurve.get(p)
        if not c:
            continue
        k = int(round(slots.get(p, 0) * teams))
        kk = min(k, len(c) - 1)
        print(f"{p:<5}{slots.get(p,0):>9.2f}{k:>7}{len(c):>6}"
              f"{c[0]:>10.2f}{c[kk]:>11.2f}{u[min(k,len(u)-1)]:>11.2f}")
    print()
