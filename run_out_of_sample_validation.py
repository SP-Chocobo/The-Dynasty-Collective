"""Out-of-sample follow-up to the baseline-12chair-v1 validation pass: does CDME's
divergence/option-set behavior hold on a materially different, real pick-order shape it has
never been measured against, or was baseline-12chair-v1's clean result specific to plain snake?

Runs two independent trials -- "standard_1qb_3rr" and "superflex_3rr" -- using Third Round
Reversal, a real, already-shipped draft type (draft_strategy.generate_pick_order's own
docstring: "a real, live format feature ... this is a structural correctness issue, not a
preference: pick order feeds intervening_roster_ids, which feeds survival/opportunity-cost/
denial/necessity, and treating a 3RR draft as plain snake mis-sizes the round-2-to-3 waits
worst of all"). Same standard 1QB / superflex leagues as baseline-12chair-v1's own two distinct
trials -- only the pick order differs -- so any divergence traces to the pick-order shape
itself, not a confounded league change.

The superflex_3rr trial specifically targets baseline-12chair-v1's own open question: 2 of
144 superflex picks (1.4%) landed in the "unsupported deviation" bucket, too few to call a
recurring pattern on their own (see the baseline divergence report's Phase 5). A materially
different pick-order shape is real, independent evidence toward whether that rate is a stable
property of this league format or an artifact of one specific trial.

These trials are deliberately NOT added to baseline-12chair-v1 (data/draft_simulation_trials/
standard_1qb.json etc. stay frozen, per the standing "do not modify the baseline" instruction)
-- each is a new, separately-labeled out-of-sample check, written to its own file.

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

# Baseline-12chair-v1's own numbers (data/draft_simulation_trials/counterfactual_summary.json /
# option_set_summary.json, both already committed) -- the reference each out-of-sample trial is
# compared against. Copied as literal values, not re-read from those files, so this script's
# pass/fail logic can never silently drift if someone regenerates the baseline files later.
# Refreshed after the DataMerger league_format harness fix (see run_draft_validation.py's own
# module docstring) -- baseline-12chair-v1 was regenerated under the corrected harness, and
# these numbers now match its real counterfactual_summary.json exactly (121->123 equals_bpa for
# standard_1qb, 112->110 equals_bpa and 2->1 deviation_unsupported for superflex).
BASELINES = {
    "standard_1qb": {"equals_bpa_rate": 123 / 144, "deviation_unsupported": 0, "bpa_visible_rate": 1.0},
    "superflex": {"equals_bpa_rate": 110 / 144, "deviation_unsupported": 1, "bpa_visible_rate": 1.0},
}

# One trial per league format, same 3RR pick order applied to each -- isolates the pick-order
# variable the same way the original standard_1qb_3rr trial did, just repeated for superflex.
TRIALS = [
    {"label": "standard_1qb_3rr", "superflex": False, "baseline_key": "standard_1qb"},
    {"label": "superflex_3rr", "superflex": True, "baseline_key": "superflex"},
]

# Pre-declared thresholds, stated before either trial ever ran:
#   - equals_bpa_rate within +/-10 points of ITS OWN baseline family, deviation_unsupported <=
#     2 (same order of magnitude as superflex's own n=2/144), and bpa_visible_rate >= 0.95
#     -> signals are STABLE under a materially different pick-order shape; KEEP.
#   - a larger swing in any of these -> the 3RR pick-order shape exposes a real sensitivity in
#     survival/necessity/option-set construction -> EXPAND VALIDATION (more 3RR-shaped trials)
#     before treating it as a MODIFY candidate; still not an immediate engine change either way.
EQUALS_BPA_RATE_TOLERANCE = 0.10
DEVIATION_UNSUPPORTED_CEILING = 2
BPA_VISIBLE_RATE_FLOOR = 0.95


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


def classify_out_of_sample_result(
    equals_bpa_rate: float, deviation_unsupported: int, bpa_visible_rate: float,
    baseline_equals_bpa_rate: float,
) -> str:
    """Pure classification against the pre-declared thresholds above -- no new valuation, just
    a comparison of already-computed numbers against the baseline family this trial belongs to
    (standard_1qb_3rr is judged against standard_1qb's own rate, superflex_3rr against
    superflex's own -- never cross-compared). Isolated into its own function so it's directly
    unit-testable without running a real 12x12 trial."""
    rate_delta = abs(equals_bpa_rate - baseline_equals_bpa_rate)
    stable = (
        rate_delta <= EQUALS_BPA_RATE_TOLERANCE
        and deviation_unsupported <= DEVIATION_UNSUPPORTED_CEILING
        and bpa_visible_rate >= BPA_VISIBLE_RATE_FLOOR
    )
    return "STABLE — KEEP" if stable else "SENSITIVITY DETECTED — EXPAND VALIDATION"


def main() -> None:
    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS, draft_type="3rr")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    summary: dict = {}

    for trial in TRIALS:
        label = trial["label"]
        baseline = BASELINES[trial["baseline_key"]]
        # Fresh, format-hinted DataMerger per trial -- standard_1qb_3rr and superflex_3rr need
        # DIFFERENT hints, so one merger was never going to be correct for both even before
        # this had a hint at all. See run_draft_validation.py's own module docstring for the
        # bug this mirrors: without a hint, a player in more than one format-specific Dynasty
        # Rankings export resolves by raw file mtime, not by this trial's own real format.
        merger = dm.DataMerger(league_format={
            "scoring": "ppr", "superflex": trial["superflex"], "te_premium": False,
        })
        players_db = _build_pool_players_db(merger)
        print(f"Loaded {len(players_db)} real baseline players across {POSITIONS} for '{label}'.")
        league = dr.build_mock_league(
            teams=NUM_TEAMS, superflex=trial["superflex"], scoring="ppr", te_premium=False, dynasty=True,
        )

        print(f"Running out-of-sample trial '{label}' -- {NUM_TEAMS} teams x {NUM_ROUNDS} rounds, 3RR pick order...")
        t0 = time.time()
        trajectory = run_trials(merger, players_db, [{"label": label, "league": league, "pick_order": pick_order}])[0]
        print(f"  done in {time.time() - t0:.1f}s, {len(trajectory.picks)} picks retained.")

        traj_path = OUT_DIR / f"{label}.json"
        traj_path.write_text(json.dumps(dataclasses.asdict(trajectory), indent=2))
        print(f"  wrote {traj_path}")

        print("  running counterfactual comparison + option-set analysis...")
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

        verdict = classify_out_of_sample_result(
            equals_bpa_rate, deviation_unsupported, bpa_visible_rate, baseline["equals_bpa_rate"],
        )

        summary[label] = {
            "total_picks": n,
            "equals_bpa": equals_bpa,
            "equals_bpa_rate": equals_bpa_rate,
            "deviation_supported": deviation_supported,
            "deviation_unsupported": deviation_unsupported,
            "bpa_visible_count": visible,
            "bpa_visible_rate": bpa_visible_rate,
            "unsupported_deviation_examples": unsupported_examples,
            "baseline_for_comparison": baseline,
            "verdict": verdict,
        }
        print(f"  equals_bpa_rate={equals_bpa_rate} (baseline {baseline['equals_bpa_rate']:.4f}), "
              f"deviation_unsupported={deviation_unsupported}, bpa_visible_rate={bpa_visible_rate}")
        print(f"  VERDICT: {verdict}")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
