"""CORRECTED #23 / V2_MECHANISM section 5. Supersedes horizon_collapse.py.

The first version computed k_exhaust as `teams x slots(P)` -- the LIVE STARTER DEMAND model --
and applied it to every position. Superflex QB does not use that model: replacement_levels
switches it to `startable_floors` (the count of remaining QBs above an absolute points
threshold), which the board reports per row as `replacement_basis`. So the +82.28 recorded as
an anomaly was the demand model being asked about a position that does not use it.

The claim under test is not about slot counts at all. It is: bpa is DEFINED as
`projected_points - replacement_level(P)`, so bpa is 0 at whatever rank the board's own
replacement sits at -- and therefore `F(i) - F(replacement_rank)` is the value key itself,
whichever model chose that rank. Measured against each position's ACTUAL basis.
"""
import data_merger as dm, draft_room as dr, draft_battery as db
import run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _prov = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()

SPECS = [
    ("12T_ppr",    dict(teams=12, superflex=False, scoring="ppr",      te_premium=False)),
    ("12T_ppr_SF", dict(teams=12, superflex=True,  scoring="ppr",      te_premium=False)),
    ("10T_ppr",    dict(teams=10, superflex=False, scoring="ppr",      te_premium=False)),
    ("10T_ppr_SF", dict(teams=10, superflex=True,  scoring="ppr",      te_premium=False)),
]
print(f"{'format':<12}{'pos':<5}{'basis':<22}{'repl rank':>10}{'bpa@rank':>10}"
      f"{'U@rank':>9}{'F@rank':>9}")
worst = 0.0
for label, kw in SPECS:
    league = dr.build_mock_league(**kw, dynasty=True)
    merger.set_league_format(db.league_format_hint(league))
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id="1", league=league, mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    for p in ("QB", "RB", "WR", "TE"):
        rows = [r for r in board if r.get("position") == p
                and r.get("bpa") is not None and r.get("projected_points") is not None]
        if not rows:
            continue
        rows.sort(key=lambda r: -r["projected_points"])
        # The board's OWN replacement rank: where its bpa crosses zero.
        k = next((i for i, r in enumerate(rows) if r["bpa"] <= 0), None)
        if k is None:
            print(f"{label:<12}{p:<5}{'(never crosses 0)':<22}")
            continue
        r = rows[k]
        f = r.get("final_score")
        worst = max(worst, abs(r["bpa"]))
        print(f"{label:<12}{p:<5}{str(r.get('replacement_basis')):<22}{k:>10}"
              f"{r['bpa']:>10.2f}{r['universal_value']:>9.2f}"
              f"{(f if f is not None else float('nan')):>9.2f}")
print(f"\nworst |bpa| at any position's own replacement rank: {worst:.2f}")
