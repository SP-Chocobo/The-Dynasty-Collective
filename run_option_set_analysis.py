"""Driver for the adversarial research pass's chosen experiment: does the engine's narrowed
option set ever exclude the true best available player (BPA), and does that set represent
genuine strategic diversity? Runs option_set_analysis.analyze_option_sets against the real
baseline-12chair-v1 trajectories (standard_1qb, superflex -- reversed_slots is a confirmed
statistical duplicate of standard_1qb and is skipped here for the same reason prior phases
skipped it).

Pre-declared thresholds (stated before this ever ran, not fit to the result):
  - bpa_visible_rate >= 0.95, with immaterial average uv_gap_vs_narrowed_floor among the
    remaining misses -> KEEP the option-set construction as-is; FORMALIZE this metric as a
    permanent instrumentation check for future validation passes.
  - bpa_visible_rate < 0.90, or misses concentrated in a recurring pattern (same position(s)
    repeatedly) -> narrow_candidates has a real, systematic blind spot -> MODIFY candidate
    (a proposal, not an immediate edit -- still subject to the same Phase 5 discipline as the
    rest of this validation work).
  - Between 0.90 and 0.95: inconclusive: EXPAND VALIDATION (more independent trials) before
    drawing a conclusion either way.

Requires data/draft_simulation_trials/*.json to already exist (run_draft_validation.py).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import draft_room as dr
from draft_counterfactual import compare_trajectory
from option_set_analysis import analyze_option_sets
from run_counterfactual_analysis import TRIAL_LEAGUE_CONFIG, _build_pool_players_db, _load_trajectory

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "option_set_summary.json"
LABELS = ("standard_1qb", "superflex")


def main() -> None:
    merger, players_db = _build_pool_players_db()
    summary: dict = {}

    for label in LABELS:
        league_cfg = TRIAL_LEAGUE_CONFIG[label]
        print(f"Loading trajectory '{label}'...")
        trajectory = _load_trajectory(label)
        league = dr.build_mock_league(**league_cfg)

        comparisons = compare_trajectory(merger, players_db, league, trajectory)
        records = analyze_option_sets(comparisons, trajectory)

        n = len(records)
        visible = [r for r in records if r.bpa_visible]
        invisible = [r for r in records if not r.bpa_visible]
        bpa_visible_rate = round(len(visible) / n, 4) if n else None

        invisible_gaps = [r.uv_gap_vs_narrowed_floor for r in invisible]
        invisible_by_position = {}
        for r, nc in zip(records, comparisons):
            if not r.bpa_visible:
                invisible_by_position[nc.bpa_position] = invisible_by_position.get(nc.bpa_position, 0) + 1

        avg_option_set_size = round(sum(r.option_set_size for r in records) / n, 2) if n else None
        avg_distinct_positions = round(sum(r.distinct_positions for r in records) / n, 2) if n else None
        avg_tav_spread = round(sum(r.tav_spread for r in records) / n, 2) if n else None

        # Cross-check against Phase 2's own "unsupported deviation" nodes: was BPA at least
        # visible in the option set at those specific nodes (a human could have overridden to
        # it), or was it invisible too (the human never had that option to begin with)?
        unsupported_pick_nos = {nc.pick_no for nc in comparisons if nc.deviation_supported is False}
        unsupported_bpa_visibility = [
            {"pick_label": r.pick_label, "bpa_visible": r.bpa_visible}
            for r in records if r.pick_no in unsupported_pick_nos
        ]

        summary[label] = {
            "total_picks": n,
            "bpa_visible_count": len(visible),
            "bpa_invisible_count": len(invisible),
            "bpa_visible_rate": bpa_visible_rate,
            "avg_uv_gap_when_invisible": round(sum(invisible_gaps) / len(invisible_gaps), 3) if invisible_gaps else None,
            "max_uv_gap_when_invisible": round(max(invisible_gaps), 3) if invisible_gaps else None,
            "invisible_misses_by_bpa_position": invisible_by_position,
            "avg_option_set_size": avg_option_set_size,
            "avg_distinct_positions_in_set": avg_distinct_positions,
            "avg_tav_spread_in_set": avg_tav_spread,
            "unsupported_deviation_bpa_visibility": unsupported_bpa_visibility,
        }
        print(f"  {label}: bpa_visible_rate={bpa_visible_rate} ({len(visible)}/{n}), "
              f"avg_set_size={avg_option_set_size}, avg_distinct_positions={avg_distinct_positions}")

        nodes_path = TRIALS_DIR / f"{label}_option_set_nodes.json"
        nodes_path.write_text(json.dumps([dataclasses.asdict(r) for r in records], indent=2))
        print(f"  wrote {nodes_path}")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
