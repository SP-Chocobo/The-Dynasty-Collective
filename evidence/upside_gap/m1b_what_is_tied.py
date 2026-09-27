"""M1b — WHO is tied at the top of a flat upside board, and what separates them in balanced mode.

M1 established that 8 of 87 states have the upside top decided by the `player_id` tiebreak among
candidates tied at value 0.00, against 0 of 87 in balanced mode at the same states. This asks the
next question, because "tied" and "equivalent" are not the same claim: it prints the tied
candidates with their positions, their `bpa`, and the balanced board's value for the same players at
the same state.

The mechanism this tests, stated before running it: after `#35`, a capped position's level IS the
best remaining player's own points, so that player's `bpa` is EXACTLY 0.00 -- and with several
positions capped, several different "best remaining at position X" rows land on exactly 0.00
together. Before `#35` the stale pre-draft anchor sat ABOVE the remaining pool, so every remaining
player at an exhausted position priced NEGATIVE and no such tie existed. If that is right, the tied
set is one row per capped position, and `replacement_level_capped` is True on them.

Run from the REPO ROOT.
"""
import collections, json, os, sys

assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

import run_draft_battery as rdb, draft_battery as db, vds_battery as vb
import data_merger as dm, draft_room as dr, draft_strategy as ds, pick_synthesis

FMT, ROUND = "12T_ppr_K_DEF", 12

scoring = rdb.scoring_settings_from_capture()
players_db, _ = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly_projections = rdb.weekly_projections_from_capture()
merger = dm.DataMerger()
rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arm = {a["label"]: a for a in rep["results"]}[f"{FMT}__sharp_upside"]
entry = {e["label"]: e for e in db.league_matrix(scoring)}[FMT]
league = entry["league"]
merger.set_league_format(db.league_format_hint(league))
rids = [str(i) for i in range(1, entry["teams"] + 1)]
order = ds.generate_pick_order(rids, entry["rounds"], "snake")
idx = (ROUND - 1) * entry["teams"]
picks = [{"pick_no": i + 1, "round": i // entry["teams"] + 1,
          "roster_id": order[i], "player_id": arm["pick_sequence"][i]} for i in range(idx)]
common = dict(merger=merger, players_db=players_db, picks=picks, pick_order=order,
              current_index=idx, my_roster_id=order[idx], league=league,
              pick_label=f"{ROUND}.01", upside_rule=dr.UPSIDE_RULE_ROUND,
              sleeper_projections=season_projections,
              sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM, weekly_projections=weekly_projections)

up = pick_synthesis.build_snapshot(mode="upside", **common)
bal = pick_synthesis.build_snapshot(mode="balanced", **common)
assert str(up.candidates[0].player_id) == str(arm["pick_sequence"][idx]), "not the arm's state"

bal_by_id = {str(c.player_id): c for c in bal.candidates}
top = up.candidates[0]
tied = [c for c in up.candidates if c.team_acquisition_value == top.team_acquisition_value]
print(f"{FMT} R{ROUND}: seat {order[idx]} on the clock, {len(up.candidates)} candidates")
print(f"the arm took {top.name} ({top.position}), player_id {top.player_id}")
print(f"tied at the top on value {top.team_acquisition_value}: {len(tied)} candidates\n")
print(f"  {'player_id':>10} {'name':22} {'pos':>4} {'bpa':>8} {'upside_tav':>11} "
      f"{'capped':>7} {'balanced_tav':>13} {'bal_rank':>9}")
bal_rank = {str(c.player_id): i for i, c in enumerate(bal.candidates)}
for c in sorted(tied, key=lambda c: str(c.player_id)):
    b = bal_by_id.get(str(c.player_id))
    print(f"  {str(c.player_id):>10} {c.name[:22]:22} {c.position:>4} "
          f"{c.bpa!s:>8} {c.team_acquisition_value!s:>11} "
          f"{getattr(c, 'replacement_level_capped', 'n/a')!s:>7} "
          f"{(b.team_acquisition_value if b else None)!s:>13} "
          f"{bal_rank.get(str(c.player_id), 'not in top')!s:>9}")
print()
print("positions in the tied set:", dict(collections.Counter(c.position for c in tied)))
print("one row per position:", len({c.position for c in tied}) == len(tied))
print(f"balanced mode's own top candidate at this state: {bal.candidates[0].name} "
      f"({bal.candidates[0].position}) tav={bal.candidates[0].team_acquisition_value}")
