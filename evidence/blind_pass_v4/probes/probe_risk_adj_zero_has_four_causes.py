"""`pick_debate`'s new three-way health sentence against the real causes of `risk_adj == 0.0`.

The repair's own comment says there are THREE states and names them: "already in the projection;
charged on top; and reported but deliberately not priced". The third branch fires on
`risk_adj == 0.0` with a non-RULE_FLOOR basis and says:

    "NO discount was applied for it -- this engine does not price this designation, so his
     value below is the value of a fully fit player"

`draft_room.health_penalty` has FOUR distinct returns, three of which are 0.0 for completely
different reasons. This probe SPIES THE PRODUCTION FUNCTION (no reconstruction) and tags each
0.0 by WHICH return produced it, derived from the arguments, then reports which pick_debate
sentence that row would receive.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_risk_adj_zero_has_four_causes.py
"""
import collections

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import player_universe as pu
import run_draft_battery as rdb

print("priced designations (HEALTH_DISCOUNT_RATE):", dr.HEALTH_DISCOUNT_RATE)

real = dr.health_penalty
seen = []


def tag_of(status, basis, points):
    """Derived from the ARGUMENTS, never from call order."""
    if basis == pu.RULE_FLOOR:
        return "A. rule_floor -- already inside the projection"
    if dr.HEALTH_DISCOUNT_RATE.get(status) is None:
        return "B. unpriced designation -- the engine has no rate for it"
    if points is None or points != points:
        return "C. NO PROJECTION -- the v4 repair's new 0.0 (was NaN)"
    if points == 0.0:
        return "D. projection is EXACTLY 0.0 -- rate * 0.0"
    return "E. charged"


def spy(status, basis, points):
    out = real(status, basis, points)
    seen.append((tag_of(status, basis, points), status, basis, points, out))
    return out


merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                             dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
merger.set_league_format(db.league_format_hint(league))
season = rdb.season_projections_from_capture()

for tag, kw in (("NO season projections (vendor-priced)", {}),
                ("WITH season projections", {"sleeper_projections": season,
                                             "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM})):
    seen.clear()
    dr.health_penalty = spy
    try:
        board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                                       mode="balanced", **kw)
    finally:
        dr.health_penalty = real
    frame = pd.DataFrame(board)
    print()
    print("=" * 78)
    print("ARM:", tag, "   board rows:", len(frame),
          "  priced:", int(frame["final_score"].notna().sum()))
    print("  health_penalty observed calls n =", len(seen))
    census = collections.Counter(t for t, *_ in seen)
    for key in sorted(census):
        print(f"    {census[key]:>5}  {key}")
    print()
    print("  WHICH pick_debate SENTENCE each 0.0 cause receives:")
    for key in sorted(census):
        if key.startswith("E."):
            continue
        rows = [r for r in seen if r[0] == key]
        statuses = collections.Counter(r[1] for r in rows)
        zero = sum(1 for r in rows if r[4] == 0.0)
        if key.startswith("A."):
            sentence = "1st: 'games ALREADY REMOVED from his projection'"
        else:
            sentence = "3rd: 'this engine does not price this designation'"
        priced_designations = {s for s in statuses
                               if dr.HEALTH_DISCOUNT_RATE.get(s) is not None}
        print(f"    {key}")
        print(f"       n={len(rows)} ({zero} returned exactly 0.0)  designations={dict(statuses)}")
        print(f"       -> {sentence}")
        if not key.startswith(("A.", "B.")) and priced_designations:
            print(f"       !! the engine DOES price {sorted(priced_designations)} "
                  f"-- the sentence is false about the designation")
