"""Final narrowing of the asset-character measurement, per the user's explicit scope-down:
only two badges survive -- Win-Now Lean (value disproportionately tied to present production)
and Age Risk (age materially unfavorable for this position's own observed curve), combinable
as "Win-Now Lean + Age Risk" when both independently hold. Consensus/certainty, "speculative",
and any "failing prodigy" idea are explicitly out of scope now -- not measured here.

The earlier orthogonality check used per-position TERCILES (each bucket ~1/3 of the pool) as a
statistical convenience to test correlation robustly -- that was never a proposed real
threshold, and a badge that fires on a third of the league is noise, not signal (the user's own
"resist expanding the taxonomy... fewer badges, more meaningful" point applies just as much to
OVER-FIRING a single badge as it does to adding new ones). This script checks SELECTIVITY at a
stricter, more defensible cut (top/bottom quartile on each axis, not thirds) and reports exactly
how many real players would actually qualify, so the two badges stay reserved for genuinely
notable cases rather than a routine label. Measurement only -- no UI, no scoring change.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import data_merger as dm
from run_asset_character_measurement import OFFENSE_POSITIONS, build_dataset

OUT_PATH = Path("data/draft_simulation_trials") / "win_now_age_risk_selectivity_check.json"

NAMED_EXAMPLES = {
    "davante adams": "user's own win-now example",
    "derrick henry": "user's own win-now example",
    "matthew stafford": "user's own win-now example",
    "jamarr chase": "elite + young -- should get NEITHER badge",
    "bijan robinson": "elite + young -- should get NEITHER badge",
    "marvin harrison": "spitball example only -- not a target category; reported for completeness, not tracked as a real case",
}


def main() -> None:
    merger = dm.DataMerger()
    all_players = build_dataset(merger)
    aged = all_players[all_players["age"].notna()].copy()

    # Quartile cut, per position -- selective (top/bottom 25%), not thirds. Win-Now Lean also
    # requires REAL current standing (season_proj_pct >= its own position median) -- a player
    # with a declining trajectory AND weak current production isn't "win-now," he's just
    # declining, a different (and out-of-scope) story.
    def _q(df, col):
        return df.groupby("position")[col].transform(lambda s: pd.qcut(s.rank(method="first"), 4, labels=[1, 2, 3, 4]))

    aged["_horizon_quartile"] = _q(aged, "_time_horizon_delta")  # 1 = most declining
    aged["_age_quartile"] = _q(aged, "_age_pct_within_position")  # 4 = oldest-for-position
    aged["_season_median_by_pos"] = aged.groupby("position")["_season_proj_pct"].transform("median")

    aged["win_now_lean"] = (aged["_horizon_quartile"] == 1) & (aged["_season_proj_pct"] >= aged["_season_median_by_pos"])
    aged["age_risk"] = aged["_age_quartile"] == 4
    aged["both"] = aged["win_now_lean"] & aged["age_risk"]

    n = len(aged)
    report: dict = {
        "n_players": n,
        "definition": {
            "win_now_lean": "bottom quartile of position-relative time_horizon_delta (most declining trajectory) AND season_proj_pct at or above this position's own median (real current standing, not just decline)",
            "age_risk": "top quartile of position-relative age (oldest for the position)",
            "combined": "both conditions independently true -- NOT a new computed score, just both flags present",
        },
        "selectivity": {
            "win_now_lean_only_pct": round(100 * (aged["win_now_lean"] & ~aged["age_risk"]).sum() / n, 1),
            "age_risk_only_pct": round(100 * (aged["age_risk"] & ~aged["win_now_lean"]).sum() / n, 1),
            "both_pct": round(100 * aged["both"].sum() / n, 1),
            "neither_pct": round(100 * (~aged["win_now_lean"] & ~aged["age_risk"]).sum() / n, 1),
            "both_count": int(aged["both"].sum()),
        },
        "selectivity_by_position": {
            pos: {
                "n": int((aged["position"] == pos).sum()),
                "both_count": int((aged["both"] & (aged["position"] == pos)).sum()),
                "both_pct": round(100 * (aged["both"] & (aged["position"] == pos)).sum() / max((aged["position"] == pos).sum(), 1), 1),
            }
            for pos in OFFENSE_POSITIONS
        },
    }

    named = {}
    for key, label in NAMED_EXAMPLES.items():
        match = aged[aged["_key"] == dm.name_key(key)]
        if match.empty:
            named[key] = {"label": label, "found": False}
            continue
        r = match.iloc[0]
        badge = "Win-Now Lean + Age Risk" if r["both"] else ("Win-Now Lean" if r["win_now_lean"] else ("Age Risk" if r["age_risk"] else "no badge"))
        named[key] = {
            "label": label, "found": True, "position": r["position"], "age": r["age"],
            "season_proj_pct": r["_season_proj_pct"], "time_horizon_delta": round(r["_time_horizon_delta"], 2),
            "badge": badge,
        }
    report["named_examples"] = named

    # A sanity list of who ELSE gets the combined badge, beyond the user's own named cases --
    # is the "both" group a small, sensible, recognizable set, or does it sweep in players who
    # don't obviously belong (a signal the cut is too loose)?
    both_players = aged[aged["both"]].sort_values("_season_proj_pct", ascending=False)
    report["real_players_getting_the_combined_badge"] = [
        {"name": r["name"], "position": r["position"], "age": r["age"], "season_proj_pct": r["_season_proj_pct"]}
        for _, r in both_players.iterrows()
    ]

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
