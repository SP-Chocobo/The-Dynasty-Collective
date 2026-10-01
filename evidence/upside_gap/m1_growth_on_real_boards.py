"""M1 — does the growth tilt actually contribute on real drained boards, and does the upside board
still discriminate?

Pre-registered in evidence/upside_gap/PREREGISTRATION.md. Run from the REPO ROOT.

WHAT THE STATES ARE. Not a fixture. Each state is reconstructed from a committed VDS arm's own
`pick_sequence` plus the pick order that produced it, in exactly the shape `simulate_full_draft`
appends ({pick_no, round, roster_id, player_id}), and the reconstruction is CHECKED at every state:
`build_snapshot(mode="upside").candidates[0]` must be the player the arm actually took. If it is
not, the state is not the state the arm was in and nothing measured on it is about that draft.
(#221 was withdrawn for measuring a drain that a fixture-shaped picks list had faked.)

WHAT IS READ. `snap.candidates` is the list the draft loop picks from -- narrow_candidates re-sorts
every board through its own key, so reading compute_draft_board's row order instead would measure a
different ordering than the one that chose. Per state, in UPSIDE mode:

  - the chosen candidate's `bpa`, `growth_signal` and `final_score`
  - `growth_points = final_score - bpa`, cross-checked against clamp(0.5 x growth_signal, +/-10)
  - the TIE SIZE at the top: how many candidates share the top candidate's final_score inside the
    same (fills_required_slot, cannot_be_fielded) group, because the sort is
    ["_feasible", "_unfieldable", "final_score", "player_id"] and only within a group does
    final_score decide. Tie size > 1 means `player_id` decided the pick, not value.
  - how many candidates carry growth_signal > 0 at all

and the same tie-size reading in BALANCED mode at the identical state, as the contrast.

Plus, once per format, a POOL-level pass off the full board at pick 1: the share of rows with a
vendor 3-year outlook (`_has_3yr` is `proj_3yr.notna()`), and the distribution of the growth tilt
over every row -- because "the chosen picks had no growth" and "no row had any growth" are different
claims and only the second one is about the model.

Absence is counted separately from zero throughout (#187): a row with no `growth_signal` at all is
not a row whose growth measured 0.0.
"""
import collections, json, os, sys

assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

import pandas as pd
import run_draft_battery as rdb, draft_battery as db, vds_battery as vb
import data_merger as dm, draft_room as dr, draft_strategy as ds, pick_synthesis
import player_universe as pu

scoring = rdb.scoring_settings_from_capture()
players_db, _prov = rdb.build_players_db_from_capture()
season_projections = rdb.season_projections_from_capture()
weekly_projections = rdb.weekly_projections_from_capture()
merger = dm.DataMerger()
rep = json.load(open("evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json"))
arms = {a["label"]: a for a in rep["results"]}
matrix = {e["label"]: e for e in db.league_matrix(scoring)}

CLAMP = dr.TIME_HORIZON_CLAMP
WEIGHT = dr.UPSIDE_GROWTH_WEIGHT


def value_of(c):
    """The quantity the ordering actually uses. `pick_synthesis._board_order` sorts board rows on
    `final_score` and candidate rows on `team_acquisition_value` -- its own docstring: "ONE KEY,
    TWO KEY NAMES, NOT TWO KEYS (#126) ... build_snapshot renames it at the boundary". A
    CandidateSnapshot has no `final_score` attribute at all, which is what the first run of this
    instrument died on. In upside mode the three team-specific terms are 0.0, so this is
    `final_score` exactly; in balanced mode it is the full acquisition value, and each mode's tie
    count below is computed against its own operative quantity.
    """
    return c.team_acquisition_value


def tie_size(cands):
    """How many of the leading candidates are tied with the top one on value alone."""
    top = cands[0]
    group = [c for c in cands
             if bool(getattr(c, "fills_required_slot", False)) == bool(getattr(top, "fills_required_slot", False))
             and bool(getattr(c, "cannot_be_fielded", False)) == bool(getattr(top, "cannot_be_fielded", False))]
    return sum(1 for c in group if value_of(c) == value_of(top)), len(group)


out = {"_doc": __doc__, "constants": {"UPSIDE_GROWTH_WEIGHT": WEIGHT,
                                     "TIME_HORIZON_CLAMP": list(CLAMP)}, "formats": {}}

for fmt in vb.FORMATS:
    entry = matrix[fmt]
    league = entry["league"]
    merger.set_league_format(db.league_format_hint(league))
    rids = [str(i) for i in range(1, entry["teams"] + 1)]
    order = ds.generate_pick_order(rids, entry["rounds"], "snake")
    seq = arms[f"{fmt}__sharp_upside"]["pick_sequence"]
    assert len(seq) == len(order)

    # ---- pool-level pass, off the FULL upside board at pick 1 (nothing drafted yet)
    board = dr.compute_draft_board(
        merger, players_db, [], my_roster_id=rids[0], league=league, mode="upside",
        sleeper_projections=season_projections, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
        upside_rule=dr.UPSIDE_RULE_ROUND, weekly_projections=weekly_projections)
    bf = pd.DataFrame(board)
    gs = bf["growth_signal"]
    tilt = bf["final_score"] - bf["bpa"]
    pool_stats = {
        "rows": int(len(bf)),
        "growth_signal_absent": int(gs.isna().sum()),
        "growth_signal_zero": int((gs == 0).sum()),
        "growth_signal_positive": int((gs > 0).sum()),
        "growth_signal_positive_share": round(float((gs > 0).mean()), 4),
        "growth_signal_max": (None if gs.dropna().empty else round(float(gs.max()), 1)),
        "tilt_points_max": (None if tilt.dropna().empty else round(float(tilt.max()), 2)),
        "tilt_points_mean_over_positive": (
            None if not (gs > 0).any() else round(float(tilt[gs > 0].mean()), 2)),
        "rows_where_tilt_ge_1pt": int((tilt >= 1.0).sum()),
        # Does the tilt ever change the argmax? The top row by final_score versus the top row by
        # bpa alone -- if they are the same player at every state, the tilt reorders nothing.
        "top_by_final_score": str(bf.sort_values(["final_score", "player_id"],
                                                 ascending=[False, True]).iloc[0]["player_id"]),
        "top_by_bpa": str(bf.sort_values(["bpa", "player_id"],
                                         ascending=[False, True]).iloc[0]["player_id"]),
    }

    states, mismatches = [], 0
    for rnd in range(1, entry["rounds"] + 1):
        idx = (rnd - 1) * entry["teams"]
        picks = [{"pick_no": i + 1, "round": i // entry["teams"] + 1,
                  "roster_id": order[i], "player_id": seq[i]} for i in range(idx)]
        common = dict(merger=merger, players_db=players_db, picks=picks, pick_order=order,
                      current_index=idx, my_roster_id=order[idx], league=league,
                      pick_label=f"{rnd}.01", upside_rule=dr.UPSIDE_RULE_ROUND,
                      sleeper_projections=season_projections,
                      sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
                      weekly_projections=weekly_projections)
        up = pick_synthesis.build_snapshot(mode="upside", **common)
        bal = pick_synthesis.build_snapshot(mode="balanced", **common)
        if not up.candidates or not bal.candidates:
            continue
        top = up.candidates[0]
        ok = str(top.player_id) == str(seq[idx])
        mismatches += 0 if ok else 1
        tied, group = tie_size(up.candidates)
        btied, bgroup = tie_size(bal.candidates)
        g = getattr(top, "growth_signal", None)
        states.append({
            "round": rnd, "reproduces_arm_pick": ok,
            "candidates": len(up.candidates),
            "chosen_bpa": round(float(top.bpa), 2) if top.bpa is not None else None,
            "chosen_growth_signal": (None if g is None else round(float(g), 1)),
            "chosen_final_score": (None if value_of(top) is None else round(float(value_of(top)), 2)),
            "chosen_tilt_points": (None if top.bpa is None or value_of(top) is None
                                   else round(float(value_of(top)) - float(top.bpa), 2)),
            "upside_tie_at_top": tied, "upside_group": group,
            "balanced_tie_at_top": btied, "balanced_group": bgroup,
            "candidates_with_growth_positive": sum(
                1 for c in up.candidates
                if getattr(c, "growth_signal", None) is not None and c.growth_signal > 0),
        })
        print(f"  {fmt:22} R{rnd:<3} cands={len(up.candidates):>3} "
              f"bpa={states[-1]['chosen_bpa']!s:>8} growth={states[-1]['chosen_growth_signal']!s:>6} "
              f"tilt={states[-1]['chosen_tilt_points']!s:>6} "
              f"tie_up={tied}/{group} tie_bal={btied}/{bgroup} "
              f"{'' if ok else 'PICK MISMATCH'}", flush=True)

    out["formats"][fmt] = {"pool_at_pick_1": pool_stats, "states": states,
                           "state_count": len(states), "pick_mismatches": mismatches}
    print(f"{fmt:22} pool rows={pool_stats['rows']} growth>0={pool_stats['growth_signal_positive']} "
          f"({pool_stats['growth_signal_positive_share']*100:.1f}%) max_tilt={pool_stats['tilt_points_max']} "
          f"tilt>=1pt rows={pool_stats['rows_where_tilt_ge_1pt']} "
          f"top_by_final=={pool_stats['top_by_final_score']} top_by_bpa=={pool_stats['top_by_bpa']} "
          f"| states={len(states)} mismatches={mismatches}", flush=True)

path = "evidence/upside_gap/M1_GROWTH_ON_REAL_BOARDS.json"
with open(path, "w") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
print("wrote", path)
