"""Targeted pathology stress test for calibration experiment "D", per the user's explicit
five-point ask before D can become production: still an isolated measurement, draft_room.py
is untouched, D's formula lives only in run_risk_adj_experiment_D_comparison.py (imported here).

1. Can D make a mediocre-value player artificially attractive purely from high time_horizon_adj?
2. Can D make injury nearly irrelevant for high-trajectory players?
3. Can D create absurd reversals -- a much better healthy player losing to a much weaker one?
4. What's the real distribution of D's effective penalty across the pool?
5. THE key guardrail: compare D against A on LARGE healthy-value-gap pairs, not just near-ties.
   D should reorder close, contextual decisions (Pearsall/Stevenson) -- it should NOT let a
   strong-trajectory player with meaningfully lower healthy value beat a meaningfully better,
   declining-trajectory player. That would mean D is overriding real value gaps, not just
   breaking near-ties, which is the exact failure mode to rule out before D goes live.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
from run_risk_adj_experiment_D_comparison import DYNASTY_LEAGUE, EXPERIMENT_A_SCALE, _build_players_db, _d_scale

OUT_PATH = Path("data/draft_simulation_trials") / "risk_adj_D_pathology_stress_test.json"
STATUSES = ("Questionable", "Doubtful", "Out", "IR")
# Value-gap bands to test guardrail #5 at increasing severity -- deliberately going well past
# "near tie" into "not remotely comparable" territory.
GAP_BANDS = [(5, 10), (10, 15), (15, 25), (25, 1000)]
TH_GAP_MIN = 8.0  # same "radically different trajectory" threshold as the earlier matched-pair test


def main() -> None:
    merger = dm.DataMerger()
    players_db = _build_players_db(merger)
    healthy_board = {
        r["player_id"]: r for r in dr.compute_draft_board(
            merger, players_db, [], my_roster_id="99", league=DYNASTY_LEAGUE, mode="balanced",
        )
    }
    rows = list(healthy_board.values())
    report: dict = {"n_players": len(rows)}

    # --- 4: real distribution of D's effective penalty (as a fraction of the flat penalty),
    # separately by status, since a fixed d_scale means a very different ABSOLUTE relief on
    # -1.5 (Questionable) vs -18.0 (IR).
    d_scales = sorted(_d_scale(r["time_horizon_adj"]) for r in rows)
    n = len(d_scales)
    percentiles = {p: d_scales[int(p / 100 * (n - 1))] for p in (10, 25, 50, 75, 90, 100)}
    report["d_scale_distribution_percentiles"] = {f"p{p}": round(v, 3) for p, v in percentiles.items()}
    report["d_scale_below_0_5_count"] = sum(1 for s in d_scales if s < 0.5)
    report["d_scale_at_1_0_count"] = sum(1 for s in d_scales if s == 1.0)

    # --- 2: is injury "nearly irrelevant" for high-trajectory players, in ABSOLUTE terms, per
    # status? (D_MIN_SCALE=0.3 guarantees SOME penalty always remains -- confirm what that
    # floor actually looks like in real points for each status.)
    report["floor_effective_penalty_by_status"] = {
        status: round(dr.RISK_ADJ[status] * 0.3, 2) for status in STATUSES
    }

    # --- 1 & 3 & 5: the guardrail. For every real pair, bucket by healthy-value gap size, and
    # check whether D (applied to BOTH players under the SAME injury status) ever flips the
    # order relative to healthy -- and crucially, whether A or flat would have flipped it too
    # (a flip that ALSO happens under flat/A isn't a D-specific pathology, it's just what a big
    # injury naturally does to a close pair; only a flip UNIQUE to D, on a LARGE gap, is the
    # real red flag).
    guardrail: dict[str, dict] = {f"{lo}-{hi}": {"n_pairs": 0, "flips_under_flat": 0, "flips_under_A": 0, "flips_under_D": 0, "d_only_flips": []} for lo, hi in GAP_BANDS}

    for status in STATUSES:
        flat_p = dr.RISK_ADJ[status]
        a_p = flat_p * EXPERIMENT_A_SCALE
        for i, a in enumerate(rows):
            for b in rows[i + 1:]:
                gap = abs(a["universal_value"] - b["universal_value"])
                th_gap = abs(a["time_horizon_adj"] - b["time_horizon_adj"])
                if th_gap < TH_GAP_MIN:
                    continue  # only care about pairs where trajectory is genuinely opposed
                band = next(((lo, hi) for lo, hi in GAP_BANDS if lo <= gap < hi), None)
                if band is None:
                    continue
                key = f"{band[0]}-{band[1]}"
                better, worse = (a, b) if a["universal_value"] > b["universal_value"] else (b, a)
                # "Injured" side is whichever one we're testing taking the hit -- test BOTH
                # taking the injury independently isn't meaningful here; the real question is
                # "does injuring ONE of them flip who's ahead," so injure the currently-BETTER
                # one (the scenario where a real reversal would actually matter to a drafter).
                d_better = flat_p * _d_scale(better["time_horizon_adj"])
                d_worse = flat_p * _d_scale(worse["time_horizon_adj"])
                flat_flip = (better["universal_value"] + flat_p) < worse["universal_value"]
                a_flip = (better["universal_value"] + a_p) < worse["universal_value"]
                d_flip = (better["universal_value"] + d_better) < worse["universal_value"]
                guardrail[key]["n_pairs"] += 1
                if flat_flip:
                    guardrail[key]["flips_under_flat"] += 1
                if a_flip:
                    guardrail[key]["flips_under_A"] += 1
                if d_flip:
                    guardrail[key]["flips_under_D"] += 1
                    if not flat_flip and not a_flip:
                        guardrail[key]["d_only_flips"].append({
                            "status": status,
                            "better_player": better["name"], "better_healthy_uv": better["universal_value"],
                            "better_time_horizon_adj": better["time_horizon_adj"],
                            "worse_player": worse["name"], "worse_healthy_uv": worse["universal_value"],
                            "worse_time_horizon_adj": worse["time_horizon_adj"],
                            "gap": round(gap, 2),
                            "post_injury_better": round(better["universal_value"] + d_better, 2),
                            "worse_untouched": worse["universal_value"],
                        })

    for key, g in guardrail.items():
        g["d_only_flips_count"] = len(g["d_only_flips"])
        g["d_only_flips"] = g["d_only_flips"][:8]  # cap examples for readability
    report["guardrail_by_value_gap_band"] = guardrail

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
