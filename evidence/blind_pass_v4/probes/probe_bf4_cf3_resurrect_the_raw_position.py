"""B-F4 / C-F3: the three new call sites undo MANDATE 2.6 / `#172` for the one row it is about.

`player_universe.player_eligible_positions` ALREADY applies the primary-bucket fallback, and its
docstring says precisely when it must NOT:

    TWO EMPTY SETS THAT MEAN DIFFERENT THINGS. ... `fantasy_positions` PRESENT and containing
    nothing startable is an ANSWER -- Sleeper saying this player is not startable anywhere -- and
    resurrecting the raw `position` overrides it with the very field `#172` says not to trust.
    Measured on the committed capture, this is ONE row of 6,595: Bradley Sowell, `position: TE`,
    `fantasy_positions: ["OL"]`.

All three sites added in this range test `not eligible` / `or`, which cannot tell that empty ANSWER
from a missing record -- even though each already handled the missing record separately:

  draft_room.feasibility_first._fills_a_hole    info checked, then `if not eligible: eligible = {position}`
  pick_synthesis.build_snapshot._eligibility    info checked, then `eligible or ({row["position"]} ...)`
  draft_board_ui._startable_at                  `candidate.eligible_positions or {candidate.position}`

And `feasibility_first`'s comment claims the opposite: "the primary bucket remains the FALLBACK,
for a candidate the pool has no record of: that is the same degradation
`player_eligible_positions` already applies."

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_bf4_cf3_resurrect_the_raw_position.py
"""
import dataclasses

import pandas as pd

import draft_board_ui as ui
import draft_room as dr
import pick_synthesis as ps
import run_draft_battery as rdb
from player_universe import FANTASY_POSITIONS, player_eligible_positions, player_position

players_db, _ = rdb.build_players_db_from_capture()
print("universe rows:", len(players_db))

# DERIVED, not hand-listed: every row where fantasy_positions is PRESENT and nothing in it is
# startable, so player_eligible_positions answers "nowhere".
answered_nowhere = {}
for pid, info in players_db.items():
    listed = info.get("fantasy_positions")
    if listed and not {p for p in listed if p in FANTASY_POSITIONS}:
        answered_nowhere[pid] = info
print("rows where `fantasy_positions` is PRESENT and nothing in it is startable:",
      len(answered_nowhere))
for pid, info in answered_nowhere.items():
    print(f"   {pid}  {info.get('first_name')} {info.get('last_name')}  "
          f"position={info.get('position')!r}  fantasy_positions={info.get('fantasy_positions')!r}")
    print(f"      player_eligible_positions -> {player_eligible_positions(info)!r}   "
          f"player_position -> {player_position(info)!r}")

# The same census on the RAW capture, which is where `#172`'s own measurement was taken.
import json
raw = json.load(open("data/fixtures/sleeper_capture.json"))["players"]
raw_nowhere = {pid: info for pid, info in raw.items()
               if info.get("fantasy_positions")
               and not {p for p in info["fantasy_positions"] if p in FANTASY_POSITIONS}}
print()
print("RAW capture rows:", len(raw), " of which startable NOWHERE:", len(raw_nowhere))
for pid, info in raw_nowhere.items():
    print(f"   {pid}  {info.get('first_name')} {info.get('last_name')}  "
          f"position={info.get('position')!r}  fantasy_positions={info.get('fantasy_positions')!r}"
          f"  -> player_eligible_positions {player_eligible_positions(info)!r}")
print("RAW rows with fantasy_positions ABSENT or empty:",
      sum(1 for i in raw.values() if not i.get("fantasy_positions")))
print()
print("SO, on this universe: the `or {position}` fallback inside all three new sites cannot fire")
print("for a row that IS in players_db -- every one of the", len(players_db),
      "admitted rows has a non-empty")
print("eligibility set. It fires only when `info` is None, which each site already tested for")
print("separately. The `#172` breach is LATENT: the one row it is about is filtered out of the")
print("pool before a board is built.")

#: Demonstrated on the row `#172`'s own docstring names, fed in directly, so the behaviour of the
#: three expressions is observed rather than argued.
pid, info = next(iter(raw_nowhere.items()))
primary = player_position(info)

print()
print("--- site 1: draft_room.feasibility_first, candidate side ---")
# One QB slot (drafted) and one TE slot, so the TE slot is the only hole and the backstop binds.
ROSTER = ["QB", "TE"]
db_small = {
    "1": {"first_name": "Q", "last_name": "B", "position": "QB", "fantasy_positions": ["QB"]},
    pid: info,
}
picks = [{"player_id": "1", "roster_id": "1", "round": 1, "pick_no": 1}]
scored = pd.DataFrame([{"player_id": pid, "position": primary}])
key = list(dr.feasibility_first(scored, picks, db_small, "1", ROSTER))
print(f"   open slot: TE.  candidate = the 'startable nowhere' row, board label {primary!r}")
print(f"   _feasible = {key}   -> {'PROMOTED for the TE hole' if key[0] == 0 else 'not promoted'}")
print(f"   `#172` answer was {player_eligible_positions(info)!r}; the site used {{{primary!r}}}")

print()
print("--- site 2: pick_synthesis.build_snapshot._eligibility (same expression, in isolation) ---")
row = {"player_id": pid, "position": primary}
eligible = player_eligible_positions(info) if info else None
as_built = frozenset(eligible or ({row["position"]} if row.get("position") else ()))
print(f"   eligible_positions written onto the snapshot: {set(as_built)!r}")

print()
print("--- site 3: draft_board_ui.filter_candidates_by_view ---")
required = {f.name: None for f in dataclasses.fields(ps.CandidateSnapshot)
            if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING}
required.update(player_id=pid, name="startable-nowhere row", position=primary)
cand = ps.CandidateSnapshot(**required, eligible_positions=frozenset())
shown = ui.filter_candidates_by_view((cand,), primary)
print(f"   with eligible_positions = frozenset() (the `#172` answer), the {primary} view shows: "
      f"{[c.name for c in shown]}")
print(f"   -> {'RESURRECTED the raw position' if shown else 'correctly hidden'}")
