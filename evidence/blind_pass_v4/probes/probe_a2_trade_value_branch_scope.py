"""A-F2: is the repaired branch reachable "from any board built without season projections"?

`health_penalty`'s new comment claims:

    Measured on the real capture: Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR, bpa
    15.0), reachable from any board built without season projections.

The population it needs is a row with a real `bpa` and `_points` of NaN -- the trade-value
fallback (`position_relative_trade_value_vor`). `compute_draft_board`'s own comment, ~2,500
lines earlier in the same file, says of that branch: "that branch currently has zero rows (0 of
1,119)".

This probe builds the vendor-priced board on four league shapes and counts the population, and
on the shapes where it is non-empty it names the rows and reports the pick_debate sentence they
receive. The `health_penalty` call itself is SPIED, so the branch that fired is observed rather
than inferred from the row.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_a2_trade_value_branch_scope.py
"""
import collections

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import player_universe as pu
import run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
base = rdb.scoring_settings_from_capture()

SHAPES = {
    "12T_ppr (build_mock_league)": dr.build_mock_league(
        teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True,
        base_scoring=base),
    "HEAVY_IDP": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                       "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
                  "scoring_settings": {**base, "rec": 1.0},
                  "total_rosters": 12, "settings": {"type": 2}},
    "LIGHT_IDP": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "IDP_FLEX"]
                                      + ["BN"] * 6,
                  "scoring_settings": {**base, "rec": 1.0},
                  "total_rosters": 12, "settings": {"type": 2}},
}

real = dr.health_penalty

for label, league in SHAPES.items():
    merger.set_league_format(db.league_format_hint(league))     # rule 4, every format
    calls = []

    def spy(status, basis, points, _c=calls):
        if basis == pu.RULE_FLOOR:
            tag = "A.rule_floor"
        elif dr.HEALTH_DISCOUNT_RATE.get(status) is None:
            tag = "B.unpriced_designation"
        elif points is None or points != points:
            tag = "C.NO_PROJECTION (the v4 repair)"
        elif points == 0.0:
            tag = "D.projection_is_zero"
        else:
            tag = "E.charged"
        out = real(status, basis, points)
        _c.append((tag, status, basis, points, out))
        return out

    dr.health_penalty = spy
    try:
        board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                                       mode="balanced")      # NO season projections
    finally:
        dr.health_penalty = real
    f = pd.DataFrame(board)
    tv = f[f["bpa"].notna() & f["projected_points"].isna()]
    print("=" * 78)
    print(f"{label}:  rows={len(f)}  bpa notna={int(f['bpa'].notna().sum())}  "
          f"priced={int(f['final_score'].notna().sum())}")
    print("   bpa_source census:", f["bpa_source"].value_counts(dropna=False).to_dict())
    print("   TRADE-VALUE POPULATION (bpa notna & projected_points isna): n =", len(tv))
    print("   health_penalty branch census:", dict(collections.Counter(t for t, *_ in calls)))
    if len(tv):
        with_status = tv[tv["injury_status"].notna()]
        print("   ...of which carry a designation: n =", len(with_status))
        cols = ["name", "position", "injury_status", "bpa", "risk_adj", "universal_value",
                "final_score", "absence_kind"]
        print(with_status[cols].head(12).to_string(index=False))
