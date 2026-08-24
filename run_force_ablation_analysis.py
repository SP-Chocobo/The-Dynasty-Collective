"""Driver for cdme_force_ablation.py's priority-4 certification pass: runs force ablation
across every real pick in baseline-12chair-v1 (standard_1qb, superflex -- reversed_slots is
the confirmed statistical duplicate of standard_1qb, skipped here for the same reason prior
phases skipped it) and reports, per component, how often ablating it changes a real
candidate's necessity_label bucket and how large its typical/max contribution is.

Data-availability gap, reported not fabricated: the saved trajectory JSON stores each pick's
candidates in draft_board_ui.serialize_snapshot's UI-serialized shape (camelCase fields),
which does not carry position_run_detected at all (never serialized to the UI payload in the
first place). The "run" component is therefore held at its always-inactive default (False)
for this retrospective pass, rather than guessed at. A future pass wanting real run-component
data would need to recompute build_snapshot fresh at each historical index (the heavier path
draft_counterfactual.py deliberately avoids for its own, different purpose) rather than reading
the already-saved, already-lossy serialized snapshots this driver reuses.

Requires data/draft_simulation_trials/*.json to already exist (run_draft_validation.py).
"""

from __future__ import annotations

import json
from pathlib import Path

from cdme_force_ablation import ablate_trajectory_candidates, summarize

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "force_ablation_summary.json"
LABELS = ("standard_1qb", "superflex")


def _node_from_saved_pick(pick: dict) -> dict:
    candidates = [
        {
            "player_id": c["id"],
            "team_acquisition_value": c["tav"],
            "need_bonus": c.get("needBonus", 0.0),
            "eligibility_bonus": c.get("eligBonus", 0.0),
            "survival_probability": c.get("survival"),
            "positional_cliff": {"tier": c["cliffTier"]} if c.get("cliffTier") else None,
            "position_run_detected": False,  # data-availability gap -- see module docstring
            "rival_premium": c.get("rivalPremium") or 0.0,
        }
        for c in pick["snapshot"]["candidates"]
    ]
    return {"pick_label": pick["pick_label"], "round": pick["round"], "candidates": candidates}


def main() -> None:
    summary: dict = {}
    for label in LABELS:
        data = json.loads((TRIALS_DIR / f"{label}.json").read_text())
        nodes = [_node_from_saved_pick(p) for p in data["picks"]]
        records = ablate_trajectory_candidates(nodes)
        result = summarize(records)
        summary[label] = result
        print(f"{label}: {result['total_candidates']} candidates across {len(nodes)} picks")
        for comp, stats in result["components"].items():
            print(
                f"  {comp:12s} label_change_rate={stats['label_change_rate']:.4f} "
                f"avg_mag={stats['avg_magnitude']:.2f} max_mag={stats['max_magnitude']:.2f} "
                f"nonzero={stats['nonzero_count']}/{result['total_candidates']}"
            )

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
