"""M1d — the same cap-on/cap-off test at EVERY state where the upside board went flat.

M1c ran the test at one state and found the board identical with the cap no-op'd -- but the
recording wrapper showed the cap was CALLED 13 times there and capped NOTHING, so that arm was
vacuous: an identical board because the thing under test never fired. It refuted my `#35`
prediction only for a state where `#35` does nothing. This runs all eight flat-board states from
M1, records whether the cap fired at each, and only then compares.

The honest question it answers: at the states where the upside board is decided by the `player_id`
tiebreak, is the tie at 0.00 there with or without `#35` doing anything?

Run from the REPO ROOT.
"""
import collections, json, os, sys

assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

import run_draft_battery as rdb, draft_battery as db
import data_merger as dm, draft_room as dr, draft_strategy as ds, pick_synthesis

STATES = [("12T_ppr", 13), ("12T_ppr", 14),
          ("12T_ppr_K_DEF", 12), ("12T_ppr_K_DEF", 13),
          ("12T_ppr_K_DEF", 14), ("12T_ppr_K_DEF", 15),
          ("4WR_TE_PREMIUM", 15), ("4WR_TE_PREMIUM", 16)]

scoring = rdb.scoring_settings_from_capture()
players_db, _ = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly_projections = rdb.weekly_projections_from_capture()
merger = dm.DataMerger()
rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arms = {a["label"]: a for a in rep["results"]}
matrix = {e["label"]: e for e in db.league_matrix(scoring)}
_real_cap = dr.cap_levels_at_best_remaining

out = {"_doc": __doc__, "states": []}
print(f"{'format':17} {'R':>3} {'cap_calls':>9} {'capped':>22} {'tie_on':>7} {'tie_off':>8} {'same_pick':>10}")
for fmt, rnd in STATES:
    entry = matrix[fmt]
    league = entry["league"]
    merger.set_league_format(db.league_format_hint(league))
    rids = [str(i) for i in range(1, entry["teams"] + 1)]
    order = ds.generate_pick_order(rids, entry["rounds"], "snake")
    seq = arms[f"{fmt}__sharp_upside"]["pick_sequence"]
    idx = (rnd - 1) * entry["teams"]
    picks = [{"pick_no": i + 1, "round": i // entry["teams"] + 1,
              "roster_id": order[i], "player_id": seq[i]} for i in range(idx)]
    common = dict(merger=merger, players_db=players_db, picks=picks, pick_order=order,
                  current_index=idx, my_roster_id=order[idx], league=league,
                  pick_label=f"{rnd}.01", upside_rule=dr.UPSIDE_RULE_ROUND,
                  sleeper_projections=season_projections,
                  sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM, weekly_projections=weekly_projections)

    calls, capped = [0], []
    def _recording(levels, priced_pool, streaming_floors=None, _c=calls, _k=capped):
        _c[0] += 1
        res = _real_cap(levels, priced_pool, streaming_floors)
        _k.extend(res)
        return res
    dr.cap_levels_at_best_remaining = _recording
    try:
        on = pick_synthesis.build_snapshot(mode="upside", **common)
    finally:
        dr.cap_levels_at_best_remaining = _real_cap
    dr.cap_levels_at_best_remaining = lambda levels, priced_pool, streaming_floors=None: set()
    try:
        off = pick_synthesis.build_snapshot(mode="upside", **common)
    finally:
        dr.cap_levels_at_best_remaining = _real_cap

    def tie(s):
        t = s.candidates[0]
        return sum(1 for c in s.candidates if c.team_acquisition_value == t.team_acquisition_value)
    t_on, t_off = tie(on), tie(off)
    same = str(on.candidates[0].player_id) == str(off.candidates[0].player_id)
    row = {"format": fmt, "round": rnd, "cap_calls": calls[0],
           "positions_capped": sorted(set(capped)), "tie_cap_on": t_on, "tie_cap_off": t_off,
           "same_pick": same, "reproduces_arm_pick": str(on.candidates[0].player_id) == str(seq[idx]),
           "top_bpa": on.candidates[0].bpa}
    out["states"].append(row)
    print(f"{fmt:17} {rnd:>3} {calls[0]:>9} "
          f"{(','.join(row['positions_capped']) or 'NONE'):>22} {t_on:>7} {t_off:>8} {str(same):>10}"
          f"{'' if row['reproduces_arm_pick'] else '   PICK MISMATCH'}")

fired = [s for s in out["states"] if s["positions_capped"]]
print()
print(f"states where the cap actually fired: {len(fired)} of {len(out['states'])}")
print(f"of those, tie size changed with the cap off: "
      f"{sum(1 for s in fired if s['tie_cap_on'] != s['tie_cap_off'])}")
print(f"of those, the CHOSEN PLAYER changed with the cap off: "
      f"{sum(1 for s in fired if not s['same_pick'])}")
with open("evidence/upside_gap/M1D_TIE_STATES.json", "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote evidence/upside_gap/M1D_TIE_STATES.json")
