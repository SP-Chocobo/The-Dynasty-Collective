"""Measurement task requested directly by the user, in response to a proposed Draft Room UI
concept (annotating a player's TAV with "High Speculation" / "Win-Now Lean" / "Dynasty Core"
based on the COMPOSITION of their value, not a new ranking). Explicit instructions: identify
existing production/projection/trajectory/age-horizon/current-value signals available to
characterize a player's value composition; determine whether the codebase already has enough
evidence to distinguish production-grounded / speculative / win-now profiles WITHOUT inventing
a new valuation model; report candidate definitions, real distributions, and ambiguous cases.
Do not add UI or new scoring logic -- this script writes a JSON report only.

SIGNALS SURVEYED (what's actually already computed or already ingested):
  - _season_proj_pct / _proj3yr_pct (draft_room.py, internal to compute_draft_board -- this
    script recomputes them directly from merger.projections rather than modifying draft_room.py
    to expose them, since exposing them would itself be a production change): percentile rank
    of this-season projection vs. Draft Sharks' own 3-year-out projection, WITHIN each
    position's pool. time_horizon_adj (already public, already used) is exactly their delta,
    clamped +-10.
  - age (FantasyPros Dynasty PPR Rankings, offense only -- confirmed absent for IDP in the
    priority-5 audit; test_data_merger.py::FantasyProsAgeFieldAvailabilityTests).
  - std_dev / best / worst (same FantasyPros export): real EXPERT-PANEL DISAGREEMENT on a
    player's redraft-ish rank -- a genuine, evidence-based uncertainty signal, not a vibe.
  - bpa_source / confidence (draft_room.py, already public): which anchor actually produced
    bpa -- points_vor_draftsharks (trusted season number) vs points_vor_sleeper_extrapolated
    (weaker) vs position_relative_trade_value_vor (weakest, no real projection exists at all).
  - rookie / trend_30d: present in the FantasyPros dynasty CSV's own schema but confirmed
    ALWAYS NaN in the committed export -- listed here because they LOOK like exactly the right
    signals, but are not actually usable from this source today.

WHAT DOES NOT EXIST: no real trailing/historical production stat (games played, prior-season
points, career totals) anywhere in this app's ingested data -- confirmed directly against
merger.projections' own columns (name/team/position/rank/projection/proj_3yr/trade_value/
source_date only). Every "value" signal in this app is a projection of some kind (this season,
or 3 years out) or a market/expert opinion (trade_value, FantasyPros rank/tier) -- there is no
column anywhere that says "this player actually produced X in year Y." So "production-grounded"
in the strict sense the user described (demonstrated production vs. projected) is NOT directly
measurable today; the closest real proxies are AGE (a player old enough to have a real track
record) and _season_proj_pct (how much of the CURRENT valuation already reflects an
in-progress or completed season, as opposed to inferring from OFF-season or otherwise
unconfirmed trajectory).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import data_merger as dm
import draft_room as dr

OUT_PATH = Path("data/draft_simulation_trials") / "asset_character_measurement.json"
OFFENSE_POSITIONS = ("QB", "RB", "WR", "TE")

NAMED_EXAMPLES = {
    "davante adams": "user's own win-now example",
    "derrick henry": "user's own win-now example",
    "matthew stafford": "user's own win-now example",
    "marvin harrison": "user's own aspiring/dynasty example (MHJ)",
    "jamarr chase": "elite, both production and horizon -- candidate 'dynasty core'",
    "bijan robinson": "elite, both production and horizon -- candidate 'dynasty core'",
}


def _percentile_map(values: pd.Series) -> pd.Series:
    if values.empty:
        return values
    ranks = values.rank(pct=True, method="average")
    return (ranks * 100).round(2)


def main() -> None:
    merger = dm.DataMerger()
    proj = merger.projections
    fp = merger.external_values
    fp_dyn = fp[(fp["source_name"] == "fantasypros") & (fp["source_file"].str.contains("dynasty", na=False))].copy()
    fp_dyn = fp_dyn.drop_duplicates(subset="norm_name", keep="first")

    # Draft Sharks' own norm_name is first-initial + remaining name ("j chase"); FantasyPros'
    # is full-first-name ("jamarr chase") -- these NEVER collide on a raw string join (confirmed
    # live: 0 overlap on a naive merge). This is itself a real "same concept (a normalized
    # player identity), two representations" case -- the exact class of thing this session's
    # concept-representation pass has been hunting for, caught by this measurement task rather
    # than missed by it. Bridged the same way every other cross-vendor match in this app already
    # does it: dm.name_key(first-initial, remaining-name), not a second ad hoc scheme.
    proj = proj.copy()
    proj["_key"] = proj["norm_name"].map(lambda n: dm.name_key(n))
    fp_dyn["_key"] = fp_dyn["norm_name"].map(lambda n: dm.name_key(n))

    rows = []
    for pos in OFFENSE_POSITIONS:
        sub = proj[(proj["position"] == pos) & proj["projection"].notna()].copy()
        if sub.empty:
            continue
        sub["_season_proj_pct"] = _percentile_map(sub["projection"])
        sub["_proj3yr_pct"] = _percentile_map(
            sub["proj_3yr"].fillna(sub["proj_3yr"].min() if sub["proj_3yr"].notna().any() else 0)
        )
        sub["_time_horizon_delta"] = (sub["_proj3yr_pct"] - sub["_season_proj_pct"]).clip(
            dr.TIME_HORIZON_CLAMP[0] / dr.TIME_HORIZON_SLOPE, dr.TIME_HORIZON_CLAMP[1] / dr.TIME_HORIZON_SLOPE
        ) * dr.TIME_HORIZON_SLOPE
        fp_pos = fp_dyn[fp_dyn["position"] == pos][["_key", "age", "std_dev", "best", "worst", "avg"]].drop_duplicates(subset="_key", keep="first")
        merged = sub.merge(fp_pos, on="_key", how="left")
        # Position-relative age, not a hardcoded "RBs decline at 27" constant this app has no
        # sourced data to back -- per the user's own explicit steer ("age/years played vs
        # projected fall-off expected AVERAGE FOR THE POSITION"), and per this session's
        # standing measurement-only discipline: a real, computed percentile of THIS player's
        # age against every other real player at the SAME position in the SAME committed data,
        # rather than an invented biomechanical decline-age. RB/WR/TE/QB really do have
        # different real aging curves in this data (see the per-position report below) --
        # this captures that without asserting a number nothing in this codebase sources.
        if merged["age"].notna().any():
            merged["_age_pct_within_position"] = _percentile_map(merged["age"])
        else:
            merged["_age_pct_within_position"] = np.nan
        rows.append(merged)

    all_players = pd.concat(rows, ignore_index=True)
    has_age = all_players["age"].notna()
    has_spread = all_players["std_dev"].notna()

    report: dict = {
        "signals_surveyed": {
            "season_vs_3yr_percentile_delta": "already computed internally (draft_room.py's time_horizon_adj); recomputed here per-position from merger.projections directly",
            "age": "FantasyPros Dynasty PPR CSV, offense only",
            "expert_panel_std_dev": "FantasyPros Dynasty PPR CSV (best/worst/avg/std_dev)",
            "bpa_source_confidence": "draft_room.py, already public on every board row",
            "rookie_flag_and_trend_30d": "present in FantasyPros CSV schema but ALWAYS NaN in the committed export -- not usable today",
        },
        "no_real_trailing_production_stat_exists": True,
        "coverage": {
            "total_offense_players_with_a_real_projection": int(len(all_players)),
            "with_age_matched": int(has_age.sum()),
            "with_expert_spread_matched": int(has_spread.sum()),
        },
    }

    # Does age actually predict trajectory direction, as the user's real examples suggest?
    aged = all_players[has_age].copy()
    aged["age_bucket"] = pd.cut(aged["age"], bins=[0, 24, 27, 30, 99], labels=["<=24", "25-27", "28-30", "31+"])
    by_age_bucket = aged.groupby("age_bucket", observed=True).agg(
        n=("age", "size"),
        mean_time_horizon_delta=("_time_horizon_delta", "mean"),
        median_time_horizon_delta=("_time_horizon_delta", "median"),
        pct_declining=("_time_horizon_delta", lambda s: round(100 * (s < 0).mean(), 1)),
        pct_rising=("_time_horizon_delta", lambda s: round(100 * (s > 0).mean(), 1)),
    ).round(2)
    report["age_bucket_vs_time_horizon_direction"] = json.loads(by_age_bucket.to_json(orient="index"))
    report["age_time_horizon_correlation"] = (
        round(float(aged["age"].corr(aged["_time_horizon_delta"])), 3) if len(aged) > 5 else None
    )

    # Rookie flag: KeepTradeCut's real "rookie" column, already used in production to power
    # pool_scope="rookies_only"/"veterans_only" (draft_room._rookie_lookup) -- not a new
    # signal, an already-shipped one this measurement reuses rather than reinventing. Per the
    # user's explicit steer, this is kept as its OWN distinct flag, never folded into
    # "speculative": a rookie's uncertainty is structural (no NFL production history to
    # measure at all), not the same claim as an established player's thin/declining production.
    rookie_by_key = dr._rookie_lookup(merger)
    all_players["_is_rookie"] = all_players["_key"].map(lambda k: rookie_by_key.get(k, False))
    report["rookie_flag_source"] = "KeepTradeCut export, already used by production pool_scope filtering -- real, not new"
    report["rookie_count_by_position"] = {
        pos: int(all_players[(all_players["position"] == pos) & all_players["_is_rookie"]].shape[0])
        for pos in OFFENSE_POSITIONS
    }
    report["one_year_experience_tag_availability"] = (
        "NOT directly available. KTC's rookie flag only tags the CURRENT draft class (0-year). "
        "years_exp exists in Sleeper's raw /players/nfl payload (confirmed in the priority-5 "
        "audit) but is read out by NOTHING in this codebase -- player_universe.py's own row "
        "dict never includes it. A clean 'exactly 1 year in' tag would require adding a new "
        "field read (years_exp==1), which is itself a small, low-risk plumbing change of the "
        "same shape as the RISK_ADJ vocabulary fix earlier this session, not a new data source."
    )

    # Named real examples the user cited directly, plus a couple of "should read as dynasty
    # core" contrast cases.
    named = {}
    for key, label in NAMED_EXAMPLES.items():
        match = all_players[all_players["_key"] == dm.name_key(key)]
        if match.empty:
            named[key] = {"label": label, "found": False}
            continue
        r = match.iloc[0]
        named[key] = {
            "label": label, "found": True, "position": r["position"],
            "age": r.get("age"), "age_pct_within_position": r.get("_age_pct_within_position"),
            "std_dev": r.get("std_dev"), "is_rookie": bool(r["_is_rookie"]),
            "season_proj_pct": r["_season_proj_pct"], "proj3yr_pct": r["_proj3yr_pct"],
            "time_horizon_delta": round(r["_time_horizon_delta"], 2),
            "trade_value": r.get("trade_value"),
        }
    report["named_examples"] = named

    # THE DOUBLE-DIP CHECK the user explicitly flagged: ADP/rankings/trade_value are
    # expert-derived and may ALREADY price in age implicitly (an analyst ranking a 33-year-old
    # lower already reflects an age-aware judgment). An "age risk" annotation is only useful,
    # non-redundant information if age explains something about FUTURE trajectory that isn't
    # already fully captured by CURRENT standing. Three correlations, same real player pool:
    #   age vs trade_value / season_proj_pct -- how much is age already priced into the
    #     CURRENT number (if strongly negative, the vendor's own rank already "knows" a
    #     player is declining -- re-flagging that as new information would be a double-dip).
    #   age vs time_horizon_delta -- how much does age predict the FORWARD-LOOKING split
    #     Draft Sharks' own proj_3yr already encodes (this is what time_horizon_adj already
    #     uses -- if this correlation is already strong, an age annotation mostly restates it).
    # The gap between "age is priced into current value" and "age predicts forward trajectory"
    # is where a genuinely new, non-redundant annotation would have to live.
    report["double_dip_check"] = {
        "age_vs_trade_value_corr": round(float(aged["age"].corr(aged["trade_value"])), 3) if len(aged) > 5 else None,
        "age_vs_season_proj_pct_corr": round(float(aged["age"].corr(aged["_season_proj_pct"])), 3) if len(aged) > 5 else None,
        "age_vs_time_horizon_delta_corr": report["age_time_horizon_correlation"],
        "interpretation_note": (
            "If age_vs_time_horizon_delta is meaningfully weaker (closer to 0) than "
            "age_vs_trade_value/season_proj_pct, that means Draft Sharks' own proj_3yr split "
            "is NOT strongly age-aware -- age would carry real, non-redundant information "
            "beyond what time_horizon_adj already shows, and an annotation would be additive "
            "rather than a double-dip. If the two are similarly strong, age risk is likely "
            "mostly already reflected in the number the user sees."
        ),
    }

    # Candidate definitions -- measurement only, thresholds picked to be legible against the
    # real distribution below, NOT tuned or proposed as final. Every candidate is decomposable
    # from signals already surveyed above, per the user's explicit constraint.
    spread = all_players[has_spread]["std_dev"]
    spread_p75 = float(spread.quantile(0.75)) if not spread.empty else None

    def classify(r) -> str:
        speculative = r["_time_horizon_delta"] >= 5.0 and r["_season_proj_pct"] < 40
        win_now = r["_time_horizon_delta"] <= -5.0 and r["_season_proj_pct"] >= 50
        dynasty_core = r["_season_proj_pct"] >= 60 and r["_time_horizon_delta"] > -3.0
        tags = [t for t, cond in (("speculative", speculative), ("win_now", win_now), ("dynasty_core", dynasty_core)) if cond]
        if len(tags) > 1:
            return "AMBIGUOUS: " + "+".join(tags)
        return tags[0] if tags else "unclassified"

    all_players["_candidate_class"] = all_players.apply(classify, axis=1)
    class_counts = all_players["_candidate_class"].value_counts().to_dict()
    report["illustrative_threshold_example_NOT_A_PROPOSAL"] = {
        "note": "Purely to sanity-check the signals are even legible at some cutoff -- not proposed, not tuned. See age_quartile_vs_time_horizon_direction below for the threshold-FREE view the user asked for.",
        "speculative": "time_horizon_delta >= +5.0 (rising trajectory) AND season_proj_pct < 40 (little current standing)",
        "win_now": "time_horizon_delta <= -5.0 (declining trajectory) AND season_proj_pct >= 50 (real current standing)",
        "dynasty_core": "season_proj_pct >= 60 (strong current standing) AND time_horizon_delta > -3.0 (not clearly declining)",
        "distribution": {k: int(v) for k, v in class_counts.items()},
        "ambiguous_rate_pct": round(
            100 * sum(v for k, v in class_counts.items() if k.startswith("AMBIGUOUS")) / len(all_players), 1
        ),
    }

    # THRESHOLD-FREE view, per the user's explicit "let the data tell us whether these
    # categories naturally separate... without prescribing thresholds" -- quartiles of
    # position-relative age (not a global age cutoff, since a 28-year-old RB and a 28-year-old
    # TE are not the same proposition, per the user's own point) crossed against real
    # time_horizon_delta direction. If Q1 (youngest-for-position) and Q4 (oldest-for-position)
    # show a real, separated pattern in mean/median time_horizon_delta, that's natural evidence
    # an age-relative-to-position signal is real and not just noise -- reported, not asserted.
    aged_q = aged.copy()
    aged_q["_age_quartile_within_position"] = aged_q.groupby("position")["age"].transform(
        lambda s: pd.qcut(s, 4, labels=["Q1_youngest", "Q2", "Q3", "Q4_oldest"], duplicates="drop")
    )
    by_pos_quartile = aged_q.groupby(["position", "_age_quartile_within_position"], observed=True).agg(
        n=("age", "size"), age_range=("age", lambda s: f"{s.min():.0f}-{s.max():.0f}"),
        mean_time_horizon_delta=("_time_horizon_delta", "mean"),
        median_time_horizon_delta=("_time_horizon_delta", "median"),
    ).round(2)
    report["age_quartile_vs_time_horizon_direction_by_position"] = json.loads(
        by_pos_quartile.reset_index().to_json(orient="records")
    )

    # Real per-position age distribution -- does this data actually show RB/WR/TE/QB aging
    # curves differ, or is that assumption not borne out here?
    report["age_distribution_by_position"] = json.loads(
        aged.groupby("position")["age"].describe()[["count", "mean", "25%", "50%", "75%", "max"]].round(1).to_json(orient="index")
    )

    # Expert-panel-disagreement view: does std_dev actually separate the user's named win-now
    # veterans from a rising rookie, or is it a weaker signal than age for this purpose?
    report["expert_spread_p75_threshold"] = round(spread_p75, 2) if spread_p75 else None
    report["expert_spread_by_named_example"] = {
        k: v.get("std_dev") for k, v in named.items() if v.get("found")
    }

    OUT_PATH.write_text(json.dumps(report, indent=2, default=str))
    print(f"Wrote {OUT_PATH}")
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()
