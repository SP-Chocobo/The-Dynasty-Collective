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

A DataMerger is built FRESH PER CONFIG, with league_format set BEFORE players_db is built from
it, rather than one merger/players_db pair shared across every config. Found and fixed during
the 95d2111 before/after validation pass: this script used to build a single merger with no
format hint at all, same as app.py did before it started calling set_league_format() every
rerun (see app.py's own comment there -- "confirmed: one real player's trade_value swung ~2.7x
purely on that accident"). Without a hint, DataMerger.load_all falls back to "whichever
format-specific Dynasty Rankings export sorts last by (mtime, name) wins" for any player who
appears in more than one -- deterministic for a FIXED set of file mtimes, but not tied to
league format, and NOT stable across two separate regenerations if those mtimes shift in
between (confirmed directly: a real trajectory comparison across two otherwise-identical runs
diverged at pick 6 because Bowers' projection came from a different format export each time).
Superflex and standard_1qb also genuinely need DIFFERENT format hints, so sharing one merger
across configs was never going to be correct even after adding a hint -- each config now gets
its own merger/players_db pair, matching its own real league format exactly.
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
    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    reversed_slots = list(reversed(forward_slots))

    # (label, superflex, te_premium, scoring, pick_order) -- the same real params each config
    # already passed to build_mock_league, now doubling as that config's own DataMerger
    # league_format hint so the two can never drift apart.
    configs = [
        ("standard_1qb", False, False, "ppr", forward_slots),
        ("superflex", True, False, "ppr", forward_slots),
        ("standard_1qb_reversed_slots", False, False, "ppr", reversed_slots),
    ]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for label, superflex, te_premium, scoring, slots in configs:
        league_format = {"scoring": scoring, "superflex": superflex, "te_premium": te_premium}
        merger = dm.DataMerger(league_format=league_format)
        players_db = _build_pool_players_db(merger)
        print(f"Loaded {len(players_db)} real baseline players across {POSITIONS} for '{label}' (league_format={league_format}).")

        league = dr.build_mock_league(teams=NUM_TEAMS, superflex=superflex, scoring=scoring, te_premium=te_premium, dynasty=True)
        cfg = {"label": label, "league": league, "pick_order": ds.generate_pick_order(slots, total_rounds=NUM_ROUNDS)}

        print(f"Running trial '{label}' -- {NUM_TEAMS} teams x {NUM_ROUNDS} rounds ({NUM_TEAMS * NUM_ROUNDS} picks)...")
        t0 = time.time()
        trajectory = run_trials(merger, players_db, [cfg])[0]
        elapsed = time.time() - t0
        print(f"  done in {elapsed:.1f}s, {len(trajectory.picks)} picks retained.")
        out_path = OUT_DIR / f"{label}.json"
        out_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
        print(f"  wrote {out_path}")

    print("All trials complete.")


if __name__ == "__main__":
    main()
