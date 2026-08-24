"""IDP extension of run_counterfactual_analysis.py -- part of priority 6 of the current audit
roadmap (decision-node divergence map before any full 100-draft simulation). The existing
counterfactual harness (run_counterfactual_analysis.py, from an earlier session phase) already
covers standard_1qb/superflex/standard_1qb_reversed_slots; it never covered the IDP trial
(standard_1qb_idp.json, added later this session -- see run_idp_draft_validation.py), since
build_mock_league has no IDP roster-slot support and the shared _build_pool_players_db only
built QB/RB/WR/TE. This script reuses the exact same compare_trajectory machinery and the exact
same IDP_LEAGUE/POSITIONS shape run_idp_draft_validation.py already established, and merges its
result into the same counterfactual_summary.json rather than starting a second summary file.

Measurement only -- computes no verdict about whether any node's choice was "right," and does
not touch pick_synthesis/draft_room/draft_counterfactual.
"""

from __future__ import annotations

import dataclasses
import json
from collections import Counter, defaultdict
from pathlib import Path

import data_merger as dm
from draft_counterfactual import compare_trajectory
from draft_simulation import DraftTrajectory, PickRecord
from run_idp_draft_validation import IDP_LEAGUE, POSITIONS

TRIALS_DIR = Path("data/draft_simulation_trials")
SUMMARY_PATH = TRIALS_DIR / "counterfactual_summary.json"
LABEL = "standard_1qb_idp"


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


def _load_trajectory(label: str) -> DraftTrajectory:
    data = json.loads((TRIALS_DIR / f"{label}.json").read_text())
    picks = tuple(PickRecord(**p) for p in data["picks"])
    return DraftTrajectory(config=data["config"], picks=picks)


def main() -> None:
    print(f"Loading trajectory '{LABEL}'...")
    trajectory = _load_trajectory(LABEL)
    merger = dm.DataMerger(league_format={"scoring": "ppr", "superflex": False, "te_premium": False})
    players_db = _build_pool_players_db(merger)

    print(f"  running counterfactual comparison over {len(trajectory.picks)} picks...")
    comparisons = compare_trajectory(merger, players_db, IDP_LEAGUE, trajectory)

    equals_bpa = sum(1 for c in comparisons if c.equals_bpa)
    equals_adp = sum(1 for c in comparisons if c.equals_adp)
    adp_available_count = sum(1 for c in comparisons if c.adp_available)
    deviation_supported = sum(1 for c in comparisons if c.deviation_supported is True)
    deviation_unsupported = sum(1 for c in comparisons if c.deviation_supported is False)
    differs_from_both = sum(
        1 for c in comparisons if not c.equals_bpa and c.adp_available and not c.equals_adp
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
            "engine_player": c.engine_player_name, "engine_position": c.engine_position,
            "engine_necessity": c.engine_necessity, "engine_uv": c.engine_uv, "engine_tav": c.engine_tav,
            "bpa_player": c.bpa_player_name, "bpa_position": c.bpa_position,
            "bpa_uv": c.bpa_uv, "bpa_tav": c.bpa_tav, "regret_vs_bpa": c.regret_vs_bpa,
        }
        for c in comparisons if c.deviation_supported is False
    ]

    # Extra, IDP-specific breakdown not in the base script -- how often the engine's chosen
    # deviation was itself at an IDP position, since that's the exact axis this extension exists
    # to watch (does the engine reach for IDP earlier/more speculatively than offense).
    idp_positions = {"DL", "LB", "DB"}
    supported_at_idp = sum(
        1 for c in comparisons if c.deviation_supported is True and c.engine_position in idp_positions
    )
    unsupported_at_idp = sum(
        1 for c in comparisons if c.deviation_supported is False and c.engine_position in idp_positions
    )

    result = {
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
        "deviation_supported_at_idp_position": supported_at_idp,
        "deviation_unsupported_at_idp_position": unsupported_at_idp,
    }
    print(f"  equals_bpa={equals_bpa}, equals_adp={equals_adp} (adp_available={adp_available_count}), "
          f"supported={deviation_supported}, unsupported={deviation_unsupported}, "
          f"idp_supported={supported_at_idp}, idp_unsupported={unsupported_at_idp}")

    nodes_path = TRIALS_DIR / f"{LABEL}_counterfactual_nodes.json"
    nodes_path.write_text(json.dumps([dataclasses.asdict(c) for c in comparisons], indent=2))
    print(f"  wrote {nodes_path}")

    summary = json.loads(SUMMARY_PATH.read_text()) if SUMMARY_PATH.exists() else {}
    summary[LABEL] = result
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Merged '{LABEL}' into {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
