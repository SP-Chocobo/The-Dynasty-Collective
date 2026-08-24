"""Phase 1/2 driver: runs draft_counterfactual.compare_trajectory against the already-completed
baseline-12chair-v1 trajectories (data/draft_simulation_trials/*.json) and writes a summary
JSON for the Phase 2 baseline divergence report. Measurement only -- computes no verdict about
whether any node's choice was "right," and does not touch pick_synthesis/draft_room.

Requires data/draft_simulation_trials/*.json to already exist (run_draft_validation.py).
"""

from __future__ import annotations

import dataclasses
import json
from collections import Counter, defaultdict
from pathlib import Path

import data_merger as dm
import draft_room as dr
from draft_counterfactual import compare_trajectory
from draft_simulation import DraftTrajectory, PickRecord

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = Path("data/draft_simulation_trials/counterfactual_summary.json")
POSITIONS = ("QB", "RB", "WR", "TE")

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
    "standard_1qb_reversed_slots": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
}


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


def _load_trajectory(label: str) -> DraftTrajectory:
    data = json.loads((TRIALS_DIR / f"{label}.json").read_text())
    picks = tuple(PickRecord(**p) for p in data["picks"])
    return DraftTrajectory(config=data["config"], picks=picks)


def main() -> None:
    merger, players_db = _build_pool_players_db()
    summary: dict = {}

    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        print(f"Loading trajectory '{label}'...")
        trajectory = _load_trajectory(label)
        league = dr.build_mock_league(**league_cfg)

        print(f"  running counterfactual comparison over {len(trajectory.picks)} picks...")
        comparisons = compare_trajectory(merger, players_db, league, trajectory)

        equals_bpa = sum(1 for c in comparisons if c.equals_bpa)
        equals_adp = sum(1 for c in comparisons if c.equals_adp)
        adp_available_count = sum(1 for c in comparisons if c.adp_available)
        deviation_supported = sum(1 for c in comparisons if c.deviation_supported is True)
        deviation_unsupported = sum(1 for c in comparisons if c.deviation_supported is False)
        differs_from_both = sum(
            1 for c in comparisons
            if not c.equals_bpa and c.adp_available and not c.equals_adp
        )

        regret_vs_bpa_values = [c.regret_vs_bpa for c in comparisons]
        regret_vs_adp_values = [c.regret_vs_adp for c in comparisons if c.regret_vs_adp is not None]

        by_round_supported = defaultdict(Counter)
        for c, rec in zip(comparisons, trajectory.picks):
            if c.deviation_supported is not None:
                by_round_supported[rec.round]["supported" if c.deviation_supported else "unsupported"] += 1

        unsupported_examples = [
            {
                "pick_label": c.pick_label, "roster_id": c.roster_id,
                "engine_player": c.engine_player_name, "engine_necessity": c.engine_necessity,
                "engine_uv": c.engine_uv, "engine_tav": c.engine_tav,
                "bpa_player": c.bpa_player_name, "bpa_uv": c.bpa_uv, "bpa_tav": c.bpa_tav,
                "regret_vs_bpa": c.regret_vs_bpa,
            }
            for c in comparisons if c.deviation_supported is False
        ]

        summary[label] = {
            "total_picks": len(comparisons),
            "equals_bpa": equals_bpa,
            "equals_adp": equals_adp,
            "adp_available_count": adp_available_count,
            "adp_unavailable_reason": comparisons[0].adp_unavailable_reason if adp_available_count == 0 else None,
            "deviation_supported": deviation_supported,
            "deviation_unsupported": deviation_unsupported,
            "differs_from_both_bpa_and_adp": differs_from_both,
            "avg_regret_vs_bpa": round(sum(regret_vs_bpa_values) / len(regret_vs_bpa_values), 3) if regret_vs_bpa_values else None,
            "max_regret_vs_bpa": round(max(regret_vs_bpa_values), 3) if regret_vs_bpa_values else None,
            "avg_regret_vs_adp": round(sum(regret_vs_adp_values) / len(regret_vs_adp_values), 3) if regret_vs_adp_values else None,
            "unsupported_deviation_examples": unsupported_examples[:15],
            "by_round_supported_vs_unsupported": {r: dict(c) for r, c in sorted(by_round_supported.items())},
        }
        print(f"  equals_bpa={equals_bpa}, equals_adp={equals_adp} (adp_available={adp_available_count}), "
              f"supported={deviation_supported}, unsupported={deviation_unsupported}")

        # Full per-node comparisons, for anyone who wants to trace a specific pick later.
        nodes_path = TRIALS_DIR / f"{label}_counterfactual_nodes.json"
        nodes_path.write_text(json.dumps([dataclasses.asdict(c) for c in comparisons], indent=2))
        print(f"  wrote {nodes_path}")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
