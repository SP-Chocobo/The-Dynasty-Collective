"""CDME certification battery, priority 4: force ablation / contribution analysis.

compute_pick_necessity (pick_synthesis.py) is a clean additive formula:

    raw_score = BASELINE + standout + survival + cliff + run + denial + roster_fit

This module answers, for real historical decision states: how often does each named
component actually move the necessity_label bucket a real candidate lands in, and how large
is its typical/max swing? Some forces could exist in the formula and almost never matter in
practice ("decorative"); this measures that directly instead of assuming every term earns its
keep just because it's present.

Deliberately a SEPARATE reimplementation of the formula, not a refactor of
compute_pick_necessity itself (per this whole program's "do not change production logic"
discipline) -- test_cdme_force_ablation.py proves this reimplementation is faithful (its own
no-ablation case must reproduce compute_pick_necessity's real output exactly) before trusting
any ablation result built on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import draft_room as dr
import pick_synthesis as ps

COMPONENTS = ("standout", "survival", "cliff", "run", "denial", "roster_fit")


def _components(candidate: dict, others_tav: list[float]) -> dict[str, float]:
    """The six named terms of compute_pick_necessity's own formula, computed identically --
    see that function's own body for the real definition each of these mirrors."""
    tav = candidate["team_acquisition_value"]
    if not others_tav:
        standout = ps.NECESSITY_STANDOUT_WEIGHT
    else:
        margin = tav - max(others_tav)
        normalized_margin = margin / ps.NECESSITY_STANDOUT_REFERENCE_GAP
        standout = max(0.0, min(1.0, normalized_margin)) * ps.NECESSITY_STANDOUT_WEIGHT

    survival = candidate.get("survival_probability")
    survival_c = (1 - survival) * ps.NECESSITY_SURVIVAL_WEIGHT if survival is not None else 0.0

    cliff = candidate.get("positional_cliff")
    cliff_c = ps.NECESSITY_CLIFF_POINTS.get(cliff["tier"], 0.0) if cliff else 0.0

    run_c = ps.NECESSITY_RUN_BONUS if candidate.get("position_run_detected") else 0.0

    rival_premium = candidate.get("rival_premium") or 0.0
    denial_c = (
        min(rival_premium / dr.NEED_BONUS_MAX, 1.0) * ps.NECESSITY_DENIAL_WEIGHT
    ) if rival_premium > 0 else 0.0

    roster_fit_c = (candidate.get("need_bonus", 0.0) + candidate.get("eligibility_bonus", 0.0)) * ps.NECESSITY_ROSTER_FIT_WEIGHT

    return {
        "standout": standout, "survival": survival_c, "cliff": cliff_c,
        "run": run_c, "denial": denial_c, "roster_fit": roster_fit_c,
    }


def necessity_score(candidate: dict, others_tav: list[float], round_num: int, drop: Optional[str] = None) -> float:
    """Recomputes compute_pick_necessity's own raw_score/late-round-cap pipeline exactly, with
    one named component's contribution zeroed out when `drop` names it. drop=None reproduces
    the real, unablated score -- the property test_cdme_force_ablation.py checks against the
    real function's own output."""
    parts = _components(candidate, others_tav)
    if drop is not None:
        if drop not in COMPONENTS:
            raise ValueError(f"unknown component {drop!r}")
        parts[drop] = 0.0
    raw_score = ps.NECESSITY_BASELINE + sum(parts.values())
    raw_score = max(0.0, min(100.0, raw_score))
    if round_num >= ps.LATE_ROUND_THRESHOLD:
        return round(raw_score * (ps.LATE_ROUND_NECESSITY_CAP / 100.0), 1)
    return round(raw_score, 1)


@dataclass(frozen=True)
class AblationRecord:
    pick_label: str
    player_id: str
    baseline_score: float
    baseline_label: str
    ablated_scores: dict  # component -> score with that component dropped
    ablated_labels: dict  # component -> necessity_label with that component dropped


def ablate_trajectory_candidates(nodes: list[dict]) -> list[AblationRecord]:
    """One AblationRecord per (pick, candidate) pair. `nodes` is a list of
    {"pick_label": str, "round": int, "candidates": list[dict]} -- candidates carry the same
    fields compute_pick_necessity itself needs (team_acquisition_value, need_bonus,
    eligibility_bonus, survival_probability, positional_cliff, position_run_detected,
    rival_premium), the exact shape a CandidateSnapshot serializes to."""
    records: list[AblationRecord] = []
    for node in nodes:
        candidates = node["candidates"]
        tavs = [c["team_acquisition_value"] for c in candidates]
        for i, c in enumerate(candidates):
            others = [v for j, v in enumerate(tavs) if j != i]
            baseline = necessity_score(c, others, node["round"])
            ablated_scores = {comp: necessity_score(c, others, node["round"], drop=comp) for comp in COMPONENTS}
            records.append(AblationRecord(
                pick_label=node["pick_label"], player_id=str(c.get("player_id", c.get("id", ""))),
                baseline_score=baseline, baseline_label=ps._necessity_label(baseline),
                ablated_scores=ablated_scores,
                ablated_labels={comp: ps._necessity_label(s) for comp, s in ablated_scores.items()},
            ))
    return records


def summarize(records: list[AblationRecord]) -> dict:
    """Per component: how often ablating it changes the necessity_label bucket, and the
    avg/max magnitude of its own raw contribution to the score."""
    n = len(records)
    summary: dict = {"total_candidates": n, "components": {}}
    for comp in COMPONENTS:
        label_changes = sum(1 for r in records if r.ablated_labels[comp] != r.baseline_label)
        magnitudes = [abs(r.baseline_score - r.ablated_scores[comp]) for r in records]
        summary["components"][comp] = {
            "label_changes": label_changes,
            "label_change_rate": round(label_changes / n, 4) if n else None,
            "avg_magnitude": round(sum(magnitudes) / n, 3) if n else None,
            "max_magnitude": round(max(magnitudes), 3) if magnitudes else None,
            "nonzero_count": sum(1 for m in magnitudes if m > 0),
        }
    return summary
