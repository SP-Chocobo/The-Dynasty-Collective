"""Driver for the denial-semantics audit: measures, against every real pick in
baseline-12chair-v1 where the current block_opportunity ("⚔ denies a rival") flag fired on at
least one candidate, whether that flag's own stricter-definition credible-path criterion
(does the specific rival driving the premium have a real chance of actually taking the
player) is actually satisfied.

Scoped to only the picks where block_opportunity already fired on the SAVED baseline data
(42/144 standard_1qb, 78/144 superflex) -- the expensive opponent-board recomputation
(cdme_denial_semantics_audit.audit_candidates) only needs to run for those pick states, not
every pick, since a candidate that was never flagged in the first place isn't part of this
specific audit's question.

Also measures, for every candidate at those same picks: does dropping "denial" from
compute_pick_necessity's own formula change which candidate has the HIGHEST necessity (not
just whether a label moved) -- the direct measure of "how often denial actually changes the
final decision" the mandate asked for.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from cdme_denial_semantics_audit import audit_candidates
from cdme_force_ablation import necessity_score
from run_dependency_audit import _pearson

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "denial_semantics_summary.json"
POSITIONS = ("QB", "RB", "WR", "TE")
NUM_TEAMS = 12
NUM_ROUNDS = 12

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
}

# Operational threshold for "credible path" -- the specific premium-driving rival's own
# take_probability. RANK_TAKE_PROBABILITY's own values are {1: .55, 2: .32, 3: .18, 4: .10,
# 5: .06}, floor .02 -- .10 (rank-4-ish or better) is a defensible, stated-up-front bar for
# "this rival plausibly gets him," not an arbitrary post-hoc pick.
CREDIBLE_PATH_THRESHOLD = 0.10


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


def main() -> None:
    merger, players_db = _build_pool_players_db()
    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS)

    summary: dict = {}
    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        league = dr.build_mock_league(**league_cfg)
        data = json.loads((TRIALS_DIR / f"{label}.json").read_text())

        picks_so_far: list[dict] = []
        block_flagged_total = 0
        credible_path_satisfied = 0
        credible_path_take_probs: list[float] = []
        argmax_flips = 0
        argmax_checked = 0
        denial_values_all: list[float] = []
        roster_fit_values_all: list[float] = []
        denial_high_path: list[float] = []
        roster_fit_high_path: list[float] = []
        denial_low_path: list[float] = []
        roster_fit_low_path: list[float] = []

        for pick in data["picks"]:
            candidates_saved = pick["snapshot"]["candidates"]
            has_block = any("block" in (c.get("forces") or []) for c in candidates_saved)
            cur_picks = list(picks_so_far)  # snapshot before this pick, for audit + necessity

            if has_block:
                candidate_ids = [c["id"] for c in candidates_saved]
                audits = audit_candidates(
                    merger, players_db, cur_picks, pick_order, pick["pick_no"] - 1, pick["roster_id"],
                    league, candidate_ids,
                )
                audits_by_id = {a.player_id: a for a in audits}

                raw = [{
                    "player_id": c["id"], "team_acquisition_value": c["tav"],
                    "need_bonus": c.get("needBonus", 0.0), "eligibility_bonus": c.get("eligBonus", 0.0),
                    "survival_probability": audits_by_id[c["id"]].survival_probability if c["id"] in audits_by_id else c.get("survival"),
                    "positional_cliff": {"tier": c["cliffTier"]} if c.get("cliffTier") else None,
                    "position_run_detected": False,
                    "rival_premium": audits_by_id[c["id"]].rival_premium if c["id"] in audits_by_id else (c.get("rivalPremium") or 0.0),
                } for c in candidates_saved]
                tavs = [c["team_acquisition_value"] for c in raw]

                baseline_scores = {}
                ablated_scores = {}
                for i, c in enumerate(raw):
                    others = [v for j, v in enumerate(tavs) if j != i]
                    baseline_scores[c["player_id"]] = necessity_score(c, others, pick["round"])
                    ablated_scores[c["player_id"]] = necessity_score(c, others, pick["round"], drop="denial")

                if len(baseline_scores) >= 2:
                    argmax_checked += 1
                    baseline_argmax = max(baseline_scores, key=baseline_scores.get)
                    ablated_argmax = max(ablated_scores, key=ablated_scores.get)
                    if baseline_argmax != ablated_argmax:
                        argmax_flips += 1

                for c in raw:
                    a = audits_by_id.get(c["player_id"])
                    others = [v for j, v in enumerate(tavs) if raw[j]["player_id"] != c["player_id"]]
                    from cdme_force_ablation import _components
                    parts = _components(c, others)
                    denial_values_all.append(parts["denial"])
                    roster_fit_values_all.append(parts["roster_fit"])
                    if a is not None and a.premium_team_take_probability is not None:
                        if a.premium_team_take_probability >= CREDIBLE_PATH_THRESHOLD:
                            denial_high_path.append(parts["denial"])
                            roster_fit_high_path.append(parts["roster_fit"])
                        else:
                            denial_low_path.append(parts["denial"])
                            roster_fit_low_path.append(parts["roster_fit"])

                for c in candidates_saved:
                    if "block" in (c.get("forces") or []):
                        block_flagged_total += 1
                        a = audits_by_id.get(c["id"])
                        if a is not None and a.premium_team_take_probability is not None:
                            credible_path_take_probs.append(a.premium_team_take_probability)
                            if a.premium_team_take_probability >= CREDIBLE_PATH_THRESHOLD:
                                credible_path_satisfied += 1

            chosen = pick["chosen_player_id"]
            picks_so_far.append({"pick_no": pick["pick_no"], "round": pick["round"], "roster_id": pick["roster_id"], "player_id": chosen})

        summary[label] = {
            "block_flagged_candidates": block_flagged_total,
            "credible_path_satisfied": credible_path_satisfied,
            "credible_path_rate": round(credible_path_satisfied / block_flagged_total, 4) if block_flagged_total else None,
            "avg_premium_team_take_probability": round(sum(credible_path_take_probs) / len(credible_path_take_probs), 4) if credible_path_take_probs else None,
            "min_premium_team_take_probability": round(min(credible_path_take_probs), 4) if credible_path_take_probs else None,
            "max_premium_team_take_probability": round(max(credible_path_take_probs), 4) if credible_path_take_probs else None,
            "necessity_argmax_flips_when_denial_dropped": argmax_flips,
            "necessity_argmax_checked": argmax_checked,
            "necessity_argmax_flip_rate": round(argmax_flips / argmax_checked, 4) if argmax_checked else None,
            "denial_roster_fit_correlation_overall": round(_pearson(denial_values_all, roster_fit_values_all), 3),
            "denial_roster_fit_correlation_high_credible_path": round(_pearson(denial_high_path, roster_fit_high_path), 3) if len(denial_high_path) >= 2 else None,
            "denial_roster_fit_correlation_low_credible_path": round(_pearson(denial_low_path, roster_fit_low_path), 3) if len(denial_low_path) >= 2 else None,
            "n_high_credible_path": len(denial_high_path),
            "n_low_credible_path": len(denial_low_path),
        }
        print(f"{label}: {json.dumps(summary[label], indent=2)}")

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
