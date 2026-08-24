"""Out-of-sample follow-up to the baseline-12chair-v1 validation pass: does the engine's
divergence/option-set behavior hold on a materially different, real pick-order shape it has
never been measured against, or was baseline-12chair-v1's clean result specific to plain snake?

Runs a fourth, independent trial -- "standard_1qb_3rr" -- using Third Round Reversal, a real,
already-shipped draft type (draft_strategy.generate_pick_order's own docstring: "a real, live
format feature ... this is a structural correctness issue, not a preference: pick order feeds
intervening_roster_ids, which feeds survival/opportunity-cost/denial/necessity, and treating a
3RR draft as plain snake mis-sizes the round-2-to-3 waits worst of all"). Same standard 1QB
league as baseline-12chair-v1's own standard_1qb trial -- only the pick order differs -- so any
divergence in results traces to the pick-order shape itself, not a confounded league change.

This trial is deliberately NOT added to baseline-12chair-v1 (data/draft_simulation_trials/
standard_1qb.json etc. stay frozen, per the standing "do not modify the baseline" instruction)
-- it's a new, separately-labeled out-of-sample check, written to its own file.

No production decision logic is touched by this script under any outcome; it only measures.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_counterfactual import compare_trajectory
from draft_simulation import run_trials
from option_set_analysis import analyze_option_sets

OUT_DIR = Path("data/draft_simulation_trials")
OUT_PATH = OUT_DIR / "out_of_sample_summary.json"
NUM_TEAMS = 12
NUM_ROUNDS = 12
POSITIONS = ("QB", "RB", "WR", "TE")
LABEL = "standard_1qb_3rr"

# Baseline-12chair-v1's own standard_1qb numbers (data/draft_simulation_trials/
# counterfactual_summary.json / option_set_summary.json, both already committed) -- the
# reference this out-of-sample trial is compared against. Copied as literal values, not
# re-read from those files, so this script's pass/fail logic can never silently drift if
# someone regenerates the baseline files with different real data later.
BASELINE_STANDARD_1QB = {
    "equals_bpa_rate": 121 / 144,
    "deviation_unsupported": 0,
    "bpa_visible_rate": 1.0,
}

# Pre-declared thresholds, stated before this trial ever ran:
#   - equals_bpa_rate within +/-10 points of baseline, deviation_unsupported <= 2 (same order
#     of magnitude as superflex's own n=2/144), and bpa_visible_rate >= 0.95
#     -> signals are STABLE under a materially different pick-order shape; KEEP.
#   - a larger swing in any of these -> the 3RR pick-order shape exposes a real sensitivity in
#     survival/necessity/option-set construction -> EXPAND VALIDATION (more 3RR-shaped trials)
#     before treating it as a MODIFY candidate; still not an immediate engine change either way.
EQUALS_BPA_RATE_TOLERANCE = 0.10
DEVIATION_UNSUPPORTED_CEILING = 2
BPA_VISIBLE_RATE_FLOOR = 0.95


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


def classify_out_of_sample_result(
    equals_bpa_rate: float, deviation_unsupported: int, bpa_visible_rate: float,
) -> str:
    """Pure classification against the pre-declared thresholds above -- no new valuation, just
    a comparison of already-computed numbers. Isolated into its own function so it's directly
    unit-testable without running a real 12x12 trial."""
    rate_delta = abs(equals_bpa_rate - BASELINE_STANDARD_1QB["equals_bpa_rate"])
    stable = (
        rate_delta <= EQUALS_BPA_RATE_TOLERANCE
        and deviation_unsupported <= DEVIATION_UNSUPPORTED_CEILING
        and bpa_visible_rate >= BPA_VISIBLE_RATE_FLOOR
    )
    return "STABLE — KEEP" if stable else "SENSITIVITY DETECTED — EXPAND VALIDATION"


def main() -> None:
    merger, players_db = _build_pool_players_db()
    print(f"Loaded {len(players_db)} real baseline players across {POSITIONS}.")

    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    league = dr.build_mock_league(teams=NUM_TEAMS, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS, draft_type="3rr")

    cfg = {"label": LABEL, "league": league, "pick_order": pick_order}
    print(f"Running out-of-sample trial '{LABEL}' -- {NUM_TEAMS} teams x {NUM_ROUNDS} rounds, 3RR pick order...")
    t0 = time.time()
    trajectory = run_trials(merger, players_db, [cfg])[0]
    print(f"  done in {time.time() - t0:.1f}s, {len(trajectory.picks)} picks retained.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    traj_path = OUT_DIR / f"{LABEL}.json"
    traj_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
    print(f"  wrote {traj_path}")

    print("Running counterfactual comparison + option-set analysis...")
    comparisons = compare_trajectory(merger, players_db, league, trajectory)
    records = analyze_option_sets(comparisons, trajectory)

    n = len(comparisons)
    equals_bpa = sum(1 for c in comparisons if c.equals_bpa)
    deviation_supported = sum(1 for c in comparisons if c.deviation_supported is True)
    deviation_unsupported = sum(1 for c in comparisons if c.deviation_supported is False)
    equals_bpa_rate = round(equals_bpa / n, 4) if n else 0.0

    visible = sum(1 for r in records if r.bpa_visible)
    bpa_visible_rate = round(visible / n, 4) if n else 0.0

    unsupported_examples = [
        {
            "pick_label": c.pick_label, "roster_id": c.roster_id,
            "engine_player": c.engine_player_name, "engine_necessity": c.engine_necessity,
            "bpa_player": c.bpa_player_name, "regret_vs_bpa": c.regret_vs_bpa,
        }
        for c in comparisons if c.deviation_supported is False
    ]

    verdict = classify_out_of_sample_result(equals_bpa_rate, deviation_unsupported, bpa_visible_rate)

    summary = {
        "label": LABEL,
        "total_picks": n,
        "equals_bpa": equals_bpa,
        "equals_bpa_rate": equals_bpa_rate,
        "deviation_supported": deviation_supported,
        "deviation_unsupported": deviation_unsupported,
        "bpa_visible_count": visible,
        "bpa_visible_rate": bpa_visible_rate,
        "unsupported_deviation_examples": unsupported_examples,
        "baseline_standard_1qb_for_comparison": BASELINE_STANDARD_1QB,
        "verdict": verdict,
    }
    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"equals_bpa_rate={equals_bpa_rate} (baseline {BASELINE_STANDARD_1QB['equals_bpa_rate']:.4f}), "
          f"deviation_unsupported={deviation_unsupported}, bpa_visible_rate={bpa_visible_rate}")
    print(f"VERDICT: {verdict}")
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
