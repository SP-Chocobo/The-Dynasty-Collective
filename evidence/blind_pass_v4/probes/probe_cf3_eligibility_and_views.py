"""C-F3 (eligibility crosses the snapshot boundary) and the pick_debate health sentence, on the
one league shape where the populations both repairs name actually exist: HEAVY_IDP.

Checks, in one process, one code version:

  1. `CandidateSnapshot.eligible_positions` is populated by `build_snapshot`, and is not merely
     `{position}` for everyone (a uniform census would make the view filter a no-op).
  2. `draft_board_ui.filter_candidates_by_view` now returns dual-eligible candidates in a view
     their primary bucket does not name -- and the claim "the LB view hid 8 eligible candidates,
     T.J. Watt among them" is checked against the measured count rather than assumed.
  3. `feasibility_first` sees a `scored` frame that carries `player_id` in production, so the
     B-F4 repair's main path is live and its `"player_id" not in scored.columns` fallback is the
     test-only arm. Established by spying the PRODUCTION call.
  4. The health sentence `pick_debate._format_candidate` gives the two rows `health_penalty`'s
     own comment names (Harold Landry PUP, DeShon Elliott IR), with the field values taken FROM
     THE BOARD and placed on a CandidateSnapshot that `build_snapshot` itself produced.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_cf3_eligibility_and_views.py
"""
import collections
import dataclasses

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_board_ui as ui
import draft_room as dr
import draft_strategy as ds
import pick_debate as pdb
import pick_synthesis as ps
import run_draft_battery as rdb

merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
base = rdb.scoring_settings_from_capture()
league = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                               "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
          "scoring_settings": {**base, "rec": 1.0},
          "total_rosters": 12, "settings": {"type": 2}}
merger.set_league_format(db.league_format_hint(league))      # rule 4

seats = [str(i) for i in range(1, 13)]
pick_order = ds.generate_pick_order(seats, len(league["roster_positions"]), "snake")

# --- 3. spy the PRODUCTION feasibility_first call ---------------------------------
real_ff = dr.feasibility_first
ff_calls = []


def ff_spy(scored, *a, **k):
    ff_calls.append({"has_player_id": "player_id" in scored.columns,
                     "n": len(scored)})
    return real_ff(scored, *a, **k)


dr.feasibility_first = ff_spy
try:
    snap = ps.build_snapshot(merger, players_db, [], pick_order, 0, "1", league,
                             pick_label="1.01")
finally:
    dr.feasibility_first = real_ff

print("feasibility_first production calls:", ff_calls)
print("  -> B-F4's eligibility path is", "LIVE" if all(c["has_player_id"] for c in ff_calls)
      else "NOT reached; the primary-bucket fallback runs in production")

# --- 1. eligible_positions census -----------------------------------------------
cands = snap.candidates
print()
print("snapshot candidates n =", len(cands))
empty = [c for c in cands if not c.eligible_positions]
multi = [c for c in cands if len(c.eligible_positions or ()) > 1]
print("  eligible_positions EMPTY (fell back to position):", len(empty))
print("  eligible_positions multi-valued             :", len(multi))
print("  census of set sizes:",
      dict(collections.Counter(len(c.eligible_positions or ()) for c in cands)))
if len(set(frozenset(c.eligible_positions or {c.position}) for c in cands)) == 1:
    print("  !! UNIFORM census -- the view filter is a no-op on this snapshot")

# --- 2. the view filter, before/after, in one process ---------------------------
print()
for view in ("LB", "DL", "DB", "WR", "TE"):
    after = ui.filter_candidates_by_view(tuple(cands), view)
    before = [c for c in cands if c.position == view]          # the pre-repair rule
    extra = [c.name for c in after if c not in before]
    print(f"  view {view:<4} pre-repair {len(before):>3}  post-repair {len(after):>3}  "
          f"newly visible {len(extra)}: {extra[:6]}")

# --- 4. the health sentence on the two rows the comment names -------------------
board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, league=league,
                               mode="balanced")               # NO season projections
f = pd.DataFrame(board)
named = f[f["name"].isin(["Harold Landry", "DeShon Elliott"])]
template = cands[0]
print()
print("the two rows `health_penalty`'s comment names, as the board emits them:")
for _, row in named.iterrows():
    cand = dataclasses.replace(
        template, player_id=str(row["player_id"]), name=row["name"], position=row["position"],
        injury_status=row["injury_status"], risk_adj=row["risk_adj"],
        availability_basis=(None if pd.isna(row["availability_basis"])
                            else row["availability_basis"]),
        universal_value=row["universal_value"], bpa=row["bpa"],
        team_acquisition_value=row["final_score"])
    line = next(l for l in pdb._format_candidate(cand, None).splitlines()
                if "Injury designation" in l)
    rate = dr.HEALTH_DISCOUNT_RATE.get(row["injury_status"])
    print(f"  {row['name']:<17} {row['injury_status']:<5} bpa={row['bpa']:>6}  "
          f"risk_adj={row['risk_adj']!r}  basis={row['availability_basis']!r}")
    print(f"     HEALTH_DISCOUNT_RATE[{row['injury_status']}] = {rate}  "
          f"(None would mean the engine does not price it)")
    print(f"     pick_debate says ->{line.rstrip()[len('  Injury designation:'):]}")
