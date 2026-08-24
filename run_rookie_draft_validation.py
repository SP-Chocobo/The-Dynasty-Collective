"""Rookie-draft counterpart to run_draft_validation.py -- v3, corrected from two real modeling
gaps found in v1 and v2:

v1 ran pool_scope="rookies_only" against 12 EMPTY starting rosters -- structurally closer to a
rookies-only startup draft than an actual annual rookie draft: every team had maximum,
undifferentiated need at every position, so the roster-fit signal that makes CDME's contextual
layer interesting had nothing real to read.

v2 seeded rosters from baseline-12chair-v1 (pool_scope="all") before running the rookie phase
-- real, differentiated rosters, but baseline-12chair-v1's own startup draft ALSO drafts from
the rookie class (pool_scope="all" doesn't distinguish them), so most of the ~52 real rookies
in this baseline were already rostered by the time the "rookie phase" began. Confirmed
directly: only 13/24 rookie picks landed (of a nominal 48) before the board ran dry --
the rookie class was already mostly gone, not a realistic rookie-draft setup at all.

v3 seeds rosters from a FRESH pool_scope="veterans_only" startup draft instead (a real,
already-shipped production mode -- see build_available_pool's own docstring: "veterans_only"
excludes rookies entirely, "the exact toggle a redraft/keeper league that excludes rookies
entirely" would use) -- 12 real, differentiated veteran-only rosters, with the full, untouched
rookie class still available for the actual rookie-draft phase on top. This is the correct
analog of how an ongoing dynasty league's annual rookie draft actually works: rosters already
exist from prior seasons, and THIS year's incoming rookie class has never been touched by
anyone yet.

Mirrors draft_simulation.simulate_full_draft's own loop (never modifies it) so this stays an
analysis script, not a change to production simulation code: every pick, in both the veteran
seed phase and the rookie phase, still calls the real pick_synthesis.build_snapshot and takes
candidates[0], nothing simulation-specific substituted.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import data_merger as dm
import draft_board_ui
import draft_room as dr
import draft_strategy as ds
import pick_synthesis
from draft_simulation import DraftTrajectory, PickRecord, run_trials

TRIALS_DIR = Path("data/draft_simulation_trials")
NUM_TEAMS = 12
VETERAN_ROUNDS = 12  # same depth as baseline-12chair-v1, veterans-only this time
ROOKIE_ROUNDS = 4
POSITIONS = ("QB", "RB", "WR", "TE")

CONFIGS = [
    ("standard_1qb_rookie_draft", False, False, "ppr"),
    ("superflex_rookie_draft", True, False, "ppr"),
]


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

    for label, superflex, te_premium, scoring in CONFIGS:
        league_format = {"scoring": scoring, "superflex": superflex, "te_premium": te_premium}
        merger = dm.DataMerger(league_format=league_format)
        players_db = _build_pool_players_db(merger)
        league = dr.build_mock_league(teams=NUM_TEAMS, superflex=superflex, scoring=scoring, te_premium=te_premium, dynasty=True)

        veteran_pick_order = ds.generate_pick_order(forward_slots, total_rounds=VETERAN_ROUNDS)
        print(f"Running a fresh veterans_only startup draft to seed real rosters for '{label}' "
              f"-- {NUM_TEAMS} teams x {VETERAN_ROUNDS} rounds, pool_scope=veterans_only...")
        t_seed = time.time()
        veteran_trajectory = run_trials(
            merger, players_db,
            [{"label": f"{label}_veteran_seed", "league": league, "pick_order": veteran_pick_order, "pool_scope": "veterans_only"}],
        )[0]
        print(f"  veteran seed done in {time.time() - t_seed:.1f}s, {len(veteran_trajectory.picks)} picks retained.")
        seed_picks = [
            {"pick_no": p.pick_no, "round": p.round, "roster_id": p.roster_id, "player_id": p.chosen_player_id}
            for p in veteran_trajectory.picks
        ]

        rookie_pick_order = ds.generate_pick_order(forward_slots, total_rounds=ROOKIE_ROUNDS)
        picks: list[dict] = list(seed_picks)
        records: list[PickRecord] = []
        next_pick_no = max(p["pick_no"] for p in seed_picks) + 1

        print(f"Running rookie-draft phase '{label}' on top of it -- {NUM_TEAMS} teams x {ROOKIE_ROUNDS} nominal rounds, pool_scope=rookies_only...")
        t0 = time.time()
        for idx in range(len(rookie_pick_order)):
            roster_id = str(rookie_pick_order[idx])
            round_no = idx // NUM_TEAMS + 1
            pick_label = f"RD{round_no}.{(idx % NUM_TEAMS) + 1:02d}"
            snap = pick_synthesis.build_snapshot(
                merger, players_db, picks, rookie_pick_order, idx, roster_id, league,
                pick_label=pick_label, mode="auto", pool_scope="rookies_only",
            )
            if not snap.candidates:
                break
            chosen = snap.candidates[0]
            picks.append({"pick_no": next_pick_no, "round": round_no, "roster_id": roster_id, "player_id": chosen.player_id})
            records.append(PickRecord(
                pick_no=next_pick_no, round=round_no, roster_id=roster_id, pick_label=pick_label,
                chosen_player_id=chosen.player_id, decision_regime=snap.decision_regime,
                snapshot=draft_board_ui.serialize_snapshot(snap, pick_header=pick_label, state_tags=[]),
            ))
            next_pick_no += 1
        elapsed = time.time() - t0

        trajectory = DraftTrajectory(
            config={"pick_order": [str(r) for r in rookie_pick_order], "mode": "auto", "pool_scope": "rookies_only", "label": label},
            picks=tuple(records),
        )
        print(f"  done in {elapsed:.1f}s, {len(records)} rookie picks retained (nominal {NUM_TEAMS * ROOKIE_ROUNDS}).")
        out_path = TRIALS_DIR / f"{label}.json"
        out_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
        print(f"  wrote {out_path}")

    print("All rookie-draft trials complete.")


if __name__ == "__main__":
    main()
