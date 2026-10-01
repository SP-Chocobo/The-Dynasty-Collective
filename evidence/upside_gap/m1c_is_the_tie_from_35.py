"""M1c — is the flat upside board a consequence of `#35`, or was it there before?

M1b showed the tied set is one row per position, each at `bpa` exactly 0.00, and that balanced mode
ranks those same four 21st, 22nd, 23rd and off-board while preferring a DEF at +1.90. M1b's stated
prediction for WHY they sit at exactly 0.00 was `#35`: a capped position's level IS the best
remaining player's own points, so his `bpa` is exactly 0.00, and several capped positions land on
0.00 together. Before `#35` the stale pre-draft anchor sat ABOVE the remaining pool, so every
remaining player at an exhausted position priced NEGATIVE and no such tie could form.

That was a prediction, not a measurement. This measures it, the same way `shipped_cap_ab.py` does:
the identical state, built twice, with `cap_levels_at_best_remaining` no-op'd in one arm. Nothing
else changes, and the no-op is installed in memory rather than on disk.

Run from the REPO ROOT.
"""
import collections, json, os, sys

assert os.path.basename(os.getcwd()) == "The-Dynasty-Collective", os.getcwd()
sys.path.insert(0, os.getcwd())

import run_draft_battery as rdb, draft_battery as db
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


def report(tag, snap):
    top = snap.candidates[0]
    tied = [c for c in snap.candidates if c.team_acquisition_value == top.team_acquisition_value]
    zero = [c for c in snap.candidates if c.bpa is not None and c.bpa == 0.0]
    print(f"{tag:12} top={top.name} ({top.position}) tav={top.team_acquisition_value} "
          f"bpa={top.bpa}  tied_at_top={len(tied)}  candidates_with_bpa_exactly_0.00={len(zero)}")
    print(f"             top 6: " + ", ".join(
        f"{c.name.split()[-1]}/{c.position} bpa={c.bpa} tav={c.team_acquisition_value}"
        for c in snap.candidates[:6]))
    return len(tied), len(zero)


# DID THE CAP EVEN FIRE AT THIS STATE? Without this the comparison below could be vacuous --
# an identical board because the cap changed nothing, which says nothing about #35's role. Wrap
# the real function and record what it capped.
_calls, _capped = [], []
_real_cap = dr.cap_levels_at_best_remaining
def _recording_cap(levels, priced_pool, streaming_floors=None):
    before = dict(levels)
    out = _real_cap(levels, priced_pool, streaming_floors)
    _calls.append({p: (before.get(p), levels.get(p)) for p in out})
    _capped.extend(out)
    return out
dr.cap_levels_at_best_remaining = _recording_cap
try:
    shipped = pick_synthesis.build_snapshot(mode="upside", **common)
finally:
    dr.cap_levels_at_best_remaining = _real_cap
print(f"cap calls at this state: {len(_calls)}; positions capped: "
      f"{sorted(set(_capped)) or 'NONE -- the cap changed nothing here'}")
for c in _calls:
    for pos, (was, now) in c.items():
        print(f"    {pos}: level {was} -> {now}")

assert str(shipped.candidates[0].player_id) == str(arm["pick_sequence"][idx]), "not the arm's state"
t_ship, z_ship = report("SHIPPED", shipped)

real = dr.cap_levels_at_best_remaining
dr.cap_levels_at_best_remaining = lambda levels, priced_pool, streaming_floors=None: set()
try:
    capoff = pick_synthesis.build_snapshot(mode="upside", **common)
    t_off, z_off = report("CAP OFF", capoff)
finally:
    dr.cap_levels_at_best_remaining = real

print()
print(f"tied at the top:            shipped {t_ship}   cap_off {t_off}")
print(f"candidates at bpa == 0.00:  shipped {z_ship}   cap_off {z_off}")
print(f"same player chosen:         {str(shipped.candidates[0].player_id) == str(capoff.candidates[0].player_id)}")
