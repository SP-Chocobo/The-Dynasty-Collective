"""Counterfactual + option-set analysis for the rookie-draft trials (run_rookie_draft_
validation.py), with equals_adp promoted to a headline metric rather than a secondary one --
per the real domain expectation that rookie-draft ADP (KeepTradeCut's own rookie consensus)
should track actual outcomes closely: unlike veteran players, there is little differentiating
real-world information on unproven prospects, so who goes roughly when is consensus-driven far
more than in a startup/veteran draft. A rookie-draft engine that departs from ADP as often as
(or more than) the veteran trials would be a real, notable finding -- either the necessity/
denial layer is inventing volatility a human wouldn't expect here, or there's a genuine,
explainable roster-fit reason (need_bonus/eligibility_bonus) pulling picks off pure consensus.

Same real functions as run_counterfactual_analysis.py / run_option_set_analysis.py
(draft_counterfactual.compare_trajectory, option_set_analysis.analyze_option_sets) -- no new
scoring, measurement only.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
from draft_counterfactual import compare_trajectory
from draft_simulation import DraftTrajectory, PickRecord
from option_set_analysis import analyze_option_sets

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "rookie_draft_summary.json"
POSITIONS = ("QB", "RB", "WR", "TE")

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb_rookie_draft": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex_rookie_draft": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
}


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


def _load_trajectory(label: str) -> DraftTrajectory:
    data = json.loads((TRIALS_DIR / f"{label}.json").read_text())
    picks = tuple(PickRecord(**p) for p in data["picks"])
    return DraftTrajectory(config=data["config"], picks=picks)


def main() -> None:
    summary: dict = {}

    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        print(f"\n=== {label} ===")
        merger = dm.DataMerger(league_format={
            "scoring": league_cfg["scoring"], "superflex": league_cfg["superflex"], "te_premium": league_cfg["te_premium"],
        })
        players_db = _build_pool_players_db(merger)
        league = dr.build_mock_league(**league_cfg)
        trajectory = _load_trajectory(label)

        comparisons = compare_trajectory(merger, players_db, league, trajectory)
        records = analyze_option_sets(comparisons, trajectory)

        n = len(comparisons)
        equals_bpa = sum(1 for c in comparisons if c.equals_bpa)
        adp_available = sum(1 for c in comparisons if c.adp_available)
        equals_adp = sum(1 for c in comparisons if c.equals_adp)
        deviation_supported = sum(1 for c in comparisons if c.deviation_supported is True)
        deviation_unsupported = sum(1 for c in comparisons if c.deviation_supported is False)
        # Among picks where ADP data exists, how far off the engine's choice sat from ADP's own
        # consensus rank -- the real texture behind "departs from ADP," not just a yes/no.
        adp_rank_deltas = [
            (c.pick_no, c.engine_player_name, c.adp_player_name, c.adp_consensus_rank)
            for c in comparisons if c.adp_available and not c.equals_adp
        ]

        n_visible = len(records)
        visible = sum(1 for r in records if r.bpa_visible)
        bpa_visible_rate = round(visible / n_visible, 4) if n_visible else None

        unsupported_examples = [
            {
                "pick_label": c.pick_label, "roster_id": c.roster_id,
                "engine_player": c.engine_player_name, "engine_necessity": c.engine_necessity,
                "bpa_player": c.bpa_player_name, "adp_player": c.adp_player_name,
                "regret_vs_bpa": c.regret_vs_bpa,
            }
            for c in comparisons if c.deviation_supported is False
        ]

        summary[label] = {
            "total_picks": n,
            "equals_bpa": equals_bpa,
            "equals_bpa_rate": round(equals_bpa / n, 4) if n else None,
            "adp_available_count": adp_available,
            "adp_unavailable_reason": comparisons[0].adp_unavailable_reason if adp_available == 0 and n else None,
            "equals_adp": equals_adp,
            "equals_adp_rate_where_available": round(equals_adp / adp_available, 4) if adp_available else None,
            "deviation_supported": deviation_supported,
            "deviation_unsupported": deviation_unsupported,
            "bpa_visible_rate": bpa_visible_rate,
            "adp_departure_examples": [
                {"pick_no": pn, "engine_player": ep, "adp_player": ap, "adp_consensus_rank": rk}
                for pn, ep, ap, rk in adp_rank_deltas[:15]
            ],
            "unsupported_deviation_examples": unsupported_examples,
        }
        print(f"  total_picks={n}, equals_bpa_rate={summary[label]['equals_bpa_rate']}, "
              f"equals_adp_rate_where_available={summary[label]['equals_adp_rate_where_available']} "
              f"(adp_available={adp_available}/{n}), deviation_unsupported={deviation_unsupported}, "
              f"bpa_visible_rate={bpa_visible_rate}")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
