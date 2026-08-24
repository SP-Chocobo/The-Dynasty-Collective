"""Driver for draft_simulation.py -- runs a small battery of real trials against the committed
baseline and writes each DraftTrajectory to data/draft_simulation_trials/<label>.json.

Not part of the app or the fast test suite (a single build_snapshot call against the real
baseline runs ~1.4s, and a 12-team x 12-round trial is 144 such calls). Run this by hand
whenever pick_synthesis/draft_room's decision math changes meaningfully -- 678 green unit
tests confirm every individual function is correct in isolation, never whether twelve
competing chairs produce coherent, explainable divergence instead of convergence or emergent
nonsense. This script (and the analysis that reads its output) is the instrument that actually
answers that question.

Trials vary real inputs only -- draft slot order and league format -- never a random seed,
per draft_simulation.py's own determinism contract.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_simulation import run_trials

OUT_DIR = Path("data/draft_simulation_trials")
NUM_TEAMS = 12
NUM_ROUNDS = 12
POSITIONS = ("QB", "RB", "WR", "TE")


def _build_pool_players_db() -> tuple[dm.DataMerger, dict[str, dict]]:
    merger = dm.DataMerger()
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
    return merger, players_db


def main() -> None:
    merger, players_db = _build_pool_players_db()
    print(f"Loaded {len(players_db)} real baseline players across {POSITIONS}.")

    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    reversed_slots = list(reversed(forward_slots))

    standard_league = dr.build_mock_league(teams=NUM_TEAMS, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
    superflex_league = dr.build_mock_league(teams=NUM_TEAMS, superflex=True, scoring="ppr", te_premium=False, dynasty=True)

    configs = [
        {
            "label": "standard_1qb",
            "league": standard_league,
            "pick_order": ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS),
        },
        {
            "label": "superflex",
            "league": superflex_league,
            "pick_order": ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS),
        },
        {
            "label": "standard_1qb_reversed_slots",
            "league": standard_league,
            "pick_order": ds.generate_pick_order(reversed_slots, total_rounds=NUM_ROUNDS),
        },
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for cfg in configs:
        print(f"Running trial '{cfg['label']}' -- {NUM_TEAMS} teams x {NUM_ROUNDS} rounds ({NUM_TEAMS * NUM_ROUNDS} picks)...")
        t0 = time.time()
        trajectory = run_trials(merger, players_db, [cfg])[0]
        elapsed = time.time() - t0
        print(f"  done in {elapsed:.1f}s, {len(trajectory.picks)} picks retained.")
        out_path = OUT_DIR / f"{cfg['label']}.json"
        out_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
        print(f"  wrote {out_path}")

    print("All trials complete.")


if __name__ == "__main__":
    main()
