"""Adversarial research pass, post-baseline-12chair-v1: does the engine's presented option set
-- the narrowed candidate list a human actually reasons over, not just its top pick -- ever
exclude the true best available player, and does that set represent genuine strategic
diversity or a near-duplicate cluster?

Motivation: every prior validation phase (draft_counterfactual.py's Phase 1/2 divergence
measurement, roster_diagnostics.py's Phase 4 diagnostics) only checks the engine's SINGLE
recommended pick against alternatives. The product philosophy this app has committed to
throughout ("a hand of strong options to a human drafter, never an autonomous drafter") makes
the option set itself -- not just its top entry -- the thing that actually matters, and no
prior phase measured it. This module closes that specific gap.

narrow_candidates (pick_synthesis.py) already documents that its "best at position" inclusion
rule is TAV-based, not UV-based, meaning the true pool-wide UV-argmax (BPA) is not guaranteed
to appear in a narrowed candidate list at all -- draft_counterfactual.py's own docstring
flagged this as the reason it recomputes the full board rather than trusting a stored
snapshot. This module asks the next, previously-unasked question: when BPA is missing from
the narrowed set, is that a real, material miss (a human genuinely could not have seen or
chosen the best player) or a trivial one (BPA barely misses inclusion by a hair)? And,
separately, is the narrowed set actually diverse (multiple positions, real value spread) or
does it collapse to near-duplicates?

Every number here is read directly off already-computed data: draft_counterfactual.py's own
NodeComparison (bpa_player_id, bpa_uv) and the trajectory's own recorded PickSnapshot
candidates (rec.snapshot["candidates"], draft_board_ui.serialize_candidate's shape). No new
board recomputation, no new heuristic, and no mutation of either input.
"""

from __future__ import annotations

from dataclasses import dataclass

from draft_counterfactual import NodeComparison
from draft_simulation import DraftTrajectory


@dataclass(frozen=True)
class OptionSetRecord:
    pick_no: int
    pick_label: str
    roster_id: str
    option_set_size: int
    distinct_positions: int
    tav_spread: float
    bpa_visible: bool
    bpa_uv: float
    narrowed_floor_uv: float
    uv_gap_vs_narrowed_floor: float  # bpa_uv - min(uv in narrowed set); <=0 whenever bpa_visible


def analyze_option_sets(
    node_comparisons: list[NodeComparison], trajectory: DraftTrajectory,
) -> list[OptionSetRecord]:
    """One OptionSetRecord per pick. `node_comparisons` must be the result of calling
    draft_counterfactual.compare_trajectory on this same `trajectory` (same order, one entry
    per pick) -- this function does not recompute BPA itself, it only reads NodeComparison's
    already-computed bpa_player_id/bpa_uv against the trajectory's own recorded narrowed
    candidate list. Read-only: mutates neither argument."""
    if len(node_comparisons) != len(trajectory.picks):
        raise ValueError(
            "node_comparisons must be one-to-one with trajectory.picks -- pass the exact "
            "output of compare_trajectory(..., trajectory) for this same trajectory."
        )

    records: list[OptionSetRecord] = []
    for nc, rec in zip(node_comparisons, trajectory.picks):
        candidates = rec.snapshot["candidates"]
        ids = {str(c["id"]) for c in candidates}
        uvs = [c["uv"] for c in candidates]
        tavs = [c["tav"] for c in candidates]
        positions = {c["pos"] for c in candidates}

        narrowed_floor_uv = round(min(uvs), 3) if uvs else 0.0
        records.append(OptionSetRecord(
            pick_no=nc.pick_no, pick_label=nc.pick_label, roster_id=nc.roster_id,
            option_set_size=len(candidates), distinct_positions=len(positions),
            tav_spread=round(max(tavs) - min(tavs), 3) if tavs else 0.0,
            bpa_visible=nc.bpa_player_id in ids, bpa_uv=nc.bpa_uv,
            narrowed_floor_uv=narrowed_floor_uv,
            uv_gap_vs_narrowed_floor=round(nc.bpa_uv - narrowed_floor_uv, 3) if uvs else 0.0,
        ))
    return records
