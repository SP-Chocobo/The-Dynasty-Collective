"""CDME certification battery, priority 5: cross-signal dependency / double-counting audit.

pick_synthesis.py's own module docstring already documents one such check, done once by hand:
survival_probability and rival_premium were measured at r=+0.82 (residual correlation, after
already being split to share no term) across simulated draft states, an ACCEPTED property
("both respond to the same real market fact... through independent pathways -- shared cause,
not shared measurement"), not an oversight to fix.

This script verifies that claim against the CURRENT real baseline-12chair-v1 data (rather
than trusting the historical measurement forever), and checks every OTHER pair of
compute_pick_necessity's six named components for a correlation nobody has documented yet --
a pair moving together strongly enough could mean two terms are quietly counting the same
underlying scarcity signal twice, additively, without either one's own docstring saying so.

Reuses cdme_force_ablation._components (no new formula, no production code touched) against
the same saved baseline-12chair-v1 candidate data run_force_ablation_analysis.py already reads.
"""

from __future__ import annotations

import itertools
import json
import statistics
from pathlib import Path

from cdme_force_ablation import COMPONENTS, _components

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "dependency_audit_summary.json"
LABELS = ("standard_1qb", "superflex")

# A pair moving together this strongly is worth a human looking at, even if it turns out to be
# an accepted shared-cause property (like survival/denial already is) rather a real bug.
FLAG_THRESHOLD = 0.5


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov / (var_x ** 0.5 * var_y ** 0.5)


def _node_candidates(pick: dict) -> list[dict]:
    return [
        {
            "team_acquisition_value": c["tav"],
            "need_bonus": c.get("needBonus", 0.0),
            "eligibility_bonus": c.get("eligBonus", 0.0),
            "survival_probability": c.get("survival"),
            "positional_cliff": {"tier": c["cliffTier"]} if c.get("cliffTier") else None,
            "position_run_detected": False,  # same data-availability gap as run_force_ablation_analysis.py
            "rival_premium": c.get("rivalPremium") or 0.0,
        }
        for c in pick["snapshot"]["candidates"]
    ]


def main() -> None:
    summary: dict = {}
    for label in LABELS:
        data = json.loads((TRIALS_DIR / f"{label}.json").read_text())
        component_values: dict[str, list[float]] = {c: [] for c in COMPONENTS}
        for pick in data["picks"]:
            candidates = _node_candidates(pick)
            tavs = [c["team_acquisition_value"] for c in candidates]
            for i, c in enumerate(candidates):
                others = [v for j, v in enumerate(tavs) if j != i]
                parts = _components(c, others)
                for comp in COMPONENTS:
                    component_values[comp].append(parts[comp])

        correlations: dict[str, float] = {}
        flagged: list[dict] = []
        for a, b in itertools.combinations(COMPONENTS, 2):
            r = round(_pearson(component_values[a], component_values[b]), 3)
            key = f"{a}__{b}"
            correlations[key] = r
            if abs(r) >= FLAG_THRESHOLD:
                flagged.append({"pair": key, "r": r})

        summary[label] = {"n_candidates": len(component_values[COMPONENTS[0]]), "correlations": correlations, "flagged_pairs": flagged}
        print(f"{label}: {summary[label]['n_candidates']} candidates")
        for pair in flagged:
            print(f"  FLAGGED {pair['pair']}: r={pair['r']}")
        if not flagged:
            print("  no pair reached the |r| >= 0.5 flag threshold")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
