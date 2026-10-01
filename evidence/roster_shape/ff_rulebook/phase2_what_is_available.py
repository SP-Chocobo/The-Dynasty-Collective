"""What the anchor ASSERTS is freely available at a position, vs what actually is.

The anchor is a claim of the form "a free player at this position is worth X". Once
_fill_omitted_from_anchor supplies it, X is the PRE-DRAFT value. This reads the best
remaining player at each position out of the POOL PRODUCTION ITSELF HANDED to
replacement_levels -- an observation of production's own input, not a reconstruction of
its output. Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
SC = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
L = {"roster_positions": RP, "scoring_settings": SC, "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
A = json.load(open("evidence/roster_shape/ff_rulebook/phase2_crossing.json"))["anchor"]
POS = ("RB", "WR", "TE")

BEST = {}
_rl = dr.replacement_levels
def rl_spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
           startable_floors=None, truncated_out=None, flex_occupancy=None):
    if remaining_demand is not None and value_col == "_points":
        BEST.clear()
        for p in POS:
            at = pool[(pool["position"] == p) & pool["_points"].notna()]["_points"]
            BEST[p] = (float(at.max()), int(len(at))) if len(at) else (None, 0)
    return _rl(pool, value_col, roster_positions, num_teams, remaining_demand,
               startable_floors, truncated_out, flex_occupancy)
dr.replacement_levels = rl_spy

print("the anchor's claim vs the pool, at and after each crossing")
print(f"{'after':>6}{'pos':>5}{'anchor says free':>18}{'BEST remaining':>16}"
      f"{'overstated by':>15}{'n left':>8}")
for k in (104, 150, 192, 204, 240, 280, 311):
    dr.compute_draft_board(m, players_db,
        [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:k]], "12", L,
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    for p in POS:
        best, n = BEST.get(p, (None, 0))
        if best is None: continue
        print(f"{k:>6}{p:>5}{A[p]:>18.2f}{best:>16.2f}{A[p]-best:>+15.2f}{n:>8}")
    print()
dr.replacement_levels = _rl
