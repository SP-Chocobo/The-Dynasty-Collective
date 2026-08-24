"""Final measurement the user asked for before any UI/labels: given the three-axis annotation
framework that emerged from run_asset_character_measurement.py --

  1. Value horizon   (time_horizon_delta)       -> Win-Now Lean / Balanced / Dynasty Lean
  2. Age trajectory  (position-relative age)     -> Age Risk / Age Neutral / Age Advantage
  3. Value certainty (expert-panel std_dev)      -> Consensus Divided / Mid / High
  + Rookie (KeepTradeCut flag, kept separate per the user's own steer)

-- how often do these disagree with each other, and are they providing genuinely ORTHOGONAL
information rather than three names for the same thing? Measurement only: no UI, no scoring
change, no new valuation logic. Bucket boundaries are per-position TERCILES (not fixed cutoffs)
of each axis, matching the "let the data separate naturally" instruction and the finding that
these curves are genuinely position-relative (QB flat, RB/TE/WR each different).

Cramer's V is the standard normalized association measure for two categorical variables:
0 = fully independent (orthogonal), 1 = perfectly redundant (one always predicts the other).
Reported for every pair, plus the rookie flag's own distribution across the other three axes.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

import data_merger as dm
from run_asset_character_measurement import OFFENSE_POSITIONS, build_dataset

OUT_PATH = Path("data/draft_simulation_trials") / "asset_character_orthogonality_check.json"


def _position_tercile(df: pd.DataFrame, col: str, labels: tuple[str, str, str]) -> pd.Series:
    return df.groupby("position")[col].transform(
        lambda s: pd.qcut(s.rank(method="first"), 3, labels=labels) if s.notna().sum() >= 3 else pd.Series([np.nan] * len(s), index=s.index)
    )


def _cramers_v(a: pd.Series, b: pd.Series) -> float | None:
    """Bias-corrected Cramer's V (Bergsma 2013) between two categorical Series, NaN rows
    dropped pairwise. Returns None when there isn't enough data to say anything."""
    mask = a.notna() & b.notna()
    if mask.sum() < 20:
        return None
    ct = pd.crosstab(a[mask], b[mask])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return None
    chi2 = float(((ct - np.outer(ct.sum(axis=1), ct.sum(axis=0)) / ct.values.sum()) ** 2 / (np.outer(ct.sum(axis=1), ct.sum(axis=0)) / ct.values.sum())).values.sum())
    n = ct.values.sum()
    phi2 = chi2 / n
    r, k = ct.shape
    phi2_corr = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    r_corr = r - (r - 1) ** 2 / (n - 1)
    k_corr = k - (k - 1) ** 2 / (n - 1)
    denom = min(k_corr - 1, r_corr - 1)
    if denom <= 0:
        return 0.0
    return round(float(np.sqrt(phi2_corr / denom)), 3)


def main() -> None:
    merger = dm.DataMerger()
    all_players = build_dataset(merger)
    aged = all_players[all_players["age"].notna()].copy()

    aged["value_horizon"] = _position_tercile(aged, "_time_horizon_delta", ("Win-Now Lean", "Balanced", "Dynasty Lean"))
    aged["age_trajectory"] = _position_tercile(aged, "_age_pct_within_position", ("Age Advantage", "Age Neutral", "Age Risk"))
    aged["value_certainty"] = _position_tercile(aged, "std_dev", ("Consensus High", "Consensus Mid", "Consensus Divided"))

    axes = ["value_horizon", "age_trajectory", "value_certainty"]
    report: dict = {
        "n_players": int(len(aged)),
        "bucketing": "per-position terciles (roughly equal-count thirds within each position's own real pool), not fixed global cutoffs",
        "axis_distributions": {ax: aged[ax].value_counts().to_dict() for ax in axes},
    }

    pairwise = {}
    for a, b in combinations(axes, 2):
        v = _cramers_v(aged[a], aged[b])
        ct = pd.crosstab(aged[a], aged[b], normalize="index").round(3)
        pairwise[f"{a}__vs__{b}"] = {
            "cramers_v": v,
            "interpretation": (
                "near 0 = orthogonal (genuinely independent information)" if v is not None and v < 0.15 else
                "weak association -- mostly independent, some real overlap" if v is not None and v < 0.3 else
                "moderate-to-strong association -- meaningful redundancy, worth reconsidering as two separate axes" if v is not None else
                "insufficient data"
            ),
            "row_normalized_crosstab": json.loads(ct.to_json(orient="index")),
        }
    report["pairwise_association"] = pairwise

    # Rookie's relationship to each axis -- does being a rookie mechanically determine one of
    # the other three, which would make it redundant rather than a genuinely separate flag?
    rookie_breakdown = {}
    for ax in axes:
        ct = pd.crosstab(aged["_is_rookie"], aged[ax], normalize="index").round(3)
        rookie_breakdown[ax] = json.loads(ct.to_json(orient="index"))
    report["rookie_vs_each_axis"] = rookie_breakdown
    report["rookie_count"] = int(aged["_is_rookie"].sum())

    # The three concrete named cases the user specifically wants shown as tension, not resolved
    # -- do they land in DIFFERENT buckets across the three axes (proof the axes disagree in
    # exactly the informative way), or does one axis just predict the others for these players?
    named_keys = {
        "matthew stafford": "Stafford -- Age Risk expected, but real positive 3yr trajectory",
        "marvin harrison": "MHJ -- expected Age Advantage/Dynasty Lean, but data shows otherwise",
        "davante adams": "Adams -- clean Win-Now/Age-Risk case",
        "derrick henry": "Henry -- clean Win-Now/Age-Risk case",
        "jamarr chase": "Chase -- clean Dynasty Core / high consensus case",
        "bijan robinson": "Robinson -- clean Dynasty Core / high consensus case",
    }
    tension_cases = {}
    for key, label in named_keys.items():
        match = aged[aged["_key"] == dm.name_key(key)]
        if match.empty:
            continue
        r = match.iloc[0]
        tension_cases[key] = {
            "label": label,
            "value_horizon": r["value_horizon"], "age_trajectory": r["age_trajectory"],
            "value_certainty": r["value_certainty"], "is_rookie": bool(r["_is_rookie"]),
        }
    report["named_tension_cases"] = tension_cases

    # Headline verdict: what fraction of the real pool has all three axes point the same
    # direction (redundant-looking) vs. a genuine split (exactly the "surface the tension"
    # case the user wants the UI to support)?
    def _direction(row) -> str:
        h = {"Win-Now Lean": -1, "Balanced": 0, "Dynasty Lean": 1}.get(row["value_horizon"])
        a = {"Age Risk": -1, "Age Neutral": 0, "Age Advantage": 1}.get(row["age_trajectory"])
        if h is None or a is None:
            return "unknown"
        return "aligned" if h == a else ("neutral" if 0 in (h, a) else "split")

    aged["_horizon_age_relationship"] = aged.apply(_direction, axis=1)
    report["value_horizon_vs_age_trajectory_alignment_rate"] = aged["_horizon_age_relationship"].value_counts().to_dict()

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
