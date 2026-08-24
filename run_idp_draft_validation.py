"""IDP (Individual Defensive Player) counterpart to run_draft_validation.py -- closes the gap
flagged directly: every 12-chair trial this session (baseline-12chair-v1, 3RR, rookie draft)
hardcodes POSITIONS = ("QB","RB","WR","TE") and has never included DL/LB/DB at all, despite
IDP being a real, generically-supported position category in production (player_universe.
FANTASY_POSITIONS, FLEX_SLOT_POSITIONS["IDP_FLEX"]) with its own documented history of a real
bug (draft_room.py's own comments describe a first-pass IDP fallback-VOR ranking bug, already
found and fixed once -- exactly the kind of area that deserves standing validation coverage,
not a one-time fix and never checked again).

A quick single-board smoke test (not committed, run by hand) confirmed IDP players surface on
compute_draft_board without exception, with two real, already-existing signals worth watching
for in this trial's results:
  - bpa_source == "position_relative_trade_value_vor" for IDP rows, not "points_vor_
    draftsharks" -- Draft Sharks has no real point projections for IDP at all (see
    draft_room.py's own module docstring), so IDP falls back to a trade-value-based VOR proxy.
  - confidence == 35.0 for IDP rows vs ~80.0 for offensive skill positions -- the app already
    flags IDP valuations as meaningfully less trustworthy, not something this trial invents.

build_mock_league itself has no IDP roster-slot support (its `starters` list is hardcoded
offense-only), so this script builds the league dict directly in the same plain shape
compute_draft_board already expects from any real Sleeper league.

No production code touched; measurement only, same discipline as every other harness script.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import data_merger as dm
import draft_strategy as ds
from draft_simulation import run_trials

OUT_DIR = Path("data/draft_simulation_trials")
NUM_TEAMS = 12
NUM_ROUNDS = 12
POSITIONS = ("QB", "RB", "WR", "TE", "DL", "LB", "DB")

# A real, plausible IDP league shape: standard offensive starters plus dedicated DL/LB/DB slots
# and one IDP_FLEX (see player_universe.FLEX_SLOT_POSITIONS["IDP_FLEX"] = {"DL","LB","DB"}) --
# not a maximal defense-heavy config, a realistic one real leagues actually run.
IDP_LEAGUE = {
    "roster_positions": (
        ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "DL", "DL", "LB", "LB", "DB", "DB", "IDP_FLEX"]
        + ["BN"] * 8
    ),
    "scoring_settings": {"rec": 1.0},
    "total_rosters": NUM_TEAMS,
    "settings": {"type": 2},
}


def _build_pool_players_db(merger: dm.DataMerger) -> dict[str, dict]:
    proj = merger.projections
    players_db: dict[str, dict] = {}
    pid = 0
    for pos in POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return players_db


def main() -> None:
    label = "standard_1qb_idp"
    # league_format's three tracked axes (scoring/superflex/te_premium) don't cover IDP at all
    # -- same hint shape as the standard_1qb trial, since nothing about IDP inclusion changes
    # which offensive Dynasty Rankings file should win a same-player tiebreak.
    merger = dm.DataMerger(league_format={"scoring": "ppr", "superflex": False, "te_premium": False})
    players_db = _build_pool_players_db(merger)
    print(f"Loaded {len(players_db)} real baseline players across {POSITIONS} for '{label}'.")

    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS)
    cfg = {"label": label, "league": IDP_LEAGUE, "pick_order": pick_order}

    print(f"Running IDP trial '{label}' -- {NUM_TEAMS} teams x {NUM_ROUNDS} rounds ({NUM_TEAMS * NUM_ROUNDS} picks)...")
    t0 = time.time()
    trajectory = run_trials(merger, players_db, [cfg])[0]
    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s, {len(trajectory.picks)} picks retained.")
    out_path = OUT_DIR / f"{label}.json"
    out_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
    print(f"  wrote {out_path}")
    print("IDP trial complete.")


if __name__ == "__main__":
    main()
