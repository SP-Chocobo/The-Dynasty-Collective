"""D3 GATE: prove the rank derivation against production draft state, before implementing.

The owner's condition, verbatim: "have Claude prove: current roster/pick state -> intervening
picks -> derived rank -> actual player/value at that rank for a handful of states, and verify
that it is not accidentally reusing the very anchor quantity we're trying to escape."

Four stages, in that order. Nothing is implemented in the engine; this only measures.
Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db
import draft_strategy as dstrat, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
SC = {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()}
L = {"roster_positions": RP, "scoring_settings": SC, "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
ANCHOR = json.load(open("evidence/roster_shape/ff_rulebook/phase2_crossing.json"))["anchor"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
POS = ("QB", "RB", "WR", "TE")
STATES = (105, 157, 193, 205, 241, 281)

def board(picks, me, **kw):
    return dr.compute_draft_board(m, players_db, picks, me, L,
                                  sleeper_projections=season,
                                  sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM, **kw)
def as_picks(rows):
    return [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in rows]

# ---- STAGE 1 -- is pick_order derivable, and does the derivation REPRODUCE this draft? -----
print("STAGE 1 -- pick_order derivation, validated against the observed sequence")
round1 = [p["roster_id"] for p in D[:12]]
ORDER = dstrat.generate_pick_order(round1, 26, "snake")
observed = [p["roster_id"] for p in D]
agree = sum(1 for a, b in zip(ORDER, observed) if str(a) == str(b))
print(f"  derived order length {len(ORDER)}, observed {len(observed)}, "
      f"agree on {agree}/{len(observed)} picks -> "
      f"{'REPRODUCES' if agree == len(observed) else 'DOES NOT REPRODUCE'}")
print("  NOTE: generate_pick_order needs round_1_order + total_rounds + draft_type.")
print("  compute_draft_board receives NONE of them -- it takes picks, my_roster_id, league.")
print(f"  pick_order in draft_room.py: {['line 3405 simulate_opponent_picks (a PARAMETER)']}\n")

# ---- STAGE 2/3 -- intervening picks -> derived rank -> the actual player at that rank ------
# The live pool is captured from the frame production hands replacement_levels: an observation
# of production's INPUT, not a reconstruction of its output.
POOL = {}
_rl = dr.replacement_levels
def rl_spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
           startable_floors=None, truncated_out=None, flex_occupancy=None):
    if remaining_demand is not None and value_col == "_points":
        POOL.clear()
        for p in POS:
            at = pool[(pool["position"] == p) & pool["_points"].notna()]
            POOL[p] = sorted((float(v) for v in at["_points"]), reverse=True)
    return _rl(pool, value_col, roster_positions, num_teams, remaining_demand,
               startable_floors, truncated_out, flex_occupancy)
dr.replacement_levels = rl_spy

print("STAGE 2+3 -- state -> intervening -> rank -> the player actually at that rank")
print("  k estimators.  E_share: intervening x (share of P among picks so far), pick history")
print("                          ONLY, touches no valuation.   E_zero: k=0, i.e. D1.\n")
rows = []
for AT in STATES:
    prior = D[:AT - 1]
    me = str(ORDER[AT - 1])
    nxt = dstrat.find_next_pick_index(ORDER, me, AT - 1)
    inter = dstrat.intervening_roster_ids(ORDER, AT - 1, nxt)
    board(as_picks(prior), me)                       # populates POOL from production
    counts = {p: sum(1 for q in prior if q["position"] == p) for p in POS}
    tot = max(len(prior), 1)
    print(f"  pick {AT}  seat {me}  next own pick at index {nxt} "
          f"-> {len(inter)} intervening")
    print(f"    {'pos':4}{'share':>8}{'k_share':>9}{'rank':>6}{'value at rank':>15}"
          f"{'anchor':>9}{'anchor - D3':>13}{'n left':>8}")
    for p in POS:
        curve = POOL.get(p) or []
        if not curve:
            print(f"    {p:4}{'--':>8}{'--':>9}{'--':>6}{'no priced player left':>15}")
            continue
        share = counts[p] / tot
        k = int(round(len(inter) * share))
        rank = min(k + 1, len(curve))
        val = curve[rank - 1]
        anc = ANCHOR.get(p)
        rows.append({"pick": AT, "pos": p, "k": k, "rank": rank, "d3": val, "anchor": anc,
                     "best_now": curve[0], "n": len(curve)})
        print(f"    {p:4}{share:>8.3f}{k:>9}{rank:>6}{val:>15.2f}"
              f"{anc:>9.2f}{anc - val:>+13.2f}{len(curve):>8}")
    print()
dr.replacement_levels = _rl

# ---- STAGE 4 -- the accidental-reuse check, both arms in ONE process --------------------
print("STAGE 4 -- does the RIVAL-MODEL estimator reuse the anchor we are escaping?")
print("  The alternative k estimator is positional_forfeits' expected_taken, which reads")
print("  opponent_boards -> build via compute_draft_board -> final_score/TAV -> _vor ->")
print("  point_replacement -> ANCHOR-FILLED. Toggling ONLY the anchor fill, same process:\n")
AT = 241
prior = as_picks(D[:AT - 1]); me = str(ORDER[AT - 1])
def top_ranks(**kw):
    b = [r for r in board(prior, me, **kw) if r.get("final_score") not in (None, "")]
    return [(r["player_id"], r["position"]) for r in b[:10]]
with_anchor = top_ranks()
_f = dr._fill_omitted_from_anchor
dr._fill_omitted_from_anchor = lambda levels, present, floors, build: set()
without_anchor = top_ranks()
dr._fill_omitted_from_anchor = _f
same = sum(1 for a, b in zip(with_anchor, without_anchor) if a == b)
print(f"  top-10 board rows WITH anchor fill : {[p for _, p in with_anchor]}")
print(f"  top-10 board rows WITHOUT it       : {[p for _, p in without_anchor]}")
print(f"  identical in {same}/10 positions -> the rival board's RANKS are "
      f"{'INDEPENDENT of' if same == 10 else 'DEPENDENT ON'} the anchor fill")
print("\n  RANK_TAKE_PROBABILITY is keyed on exactly those ranks, so expected_taken inherits")
print("  whatever dependence is shown above.")
