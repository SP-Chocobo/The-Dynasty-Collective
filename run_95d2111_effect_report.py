"""The 95d2111 before/after receipt, v2 -- rebuilt to avoid the two-trajectory-comparison
pitfall the first version fell into (see compare_baseline_pre_post_95d2111.py's module
docstring for the full story: comparing two SEPARATELY GENERATED trajectories risked mixing in
unrelated contamination -- the tie-order-determinism fix, and a DataMerger league_format
harness bug -- neither caused by 95d2111). This version needs only ONE trajectory (the current,
harness-fixed baseline-12chair-v1) and computes BOTH the OLD and NEW block_opportunity value
for every real candidate from the SAME real rival_premium/take_probability numbers, by applying
the two competing FORMULAS rather than diffing two separately-simulated runs:
  OLD (pre-95d2111): rival_premium >= 2 * NEED_BONUS_PER_DEDICATED_SLOT
  NEW (95d2111):      OLD AND premium_team_take_probability >= CREDIBLE_RIVAL_PATH_THRESHOLD
This is strictly more precise than the original version: there is no second trajectory to
drift out of sync with, so every reported number here is free of cross-run contamination by
construction, not merely "confirmed free of it" after the fact.

Still answers the same four things:
  1. Which nodes are affected (old formula fires, new formula doesn't -- the only direction
     possible, since NEW is OLD AND an extra condition, never a superset).
  2. For every affected node: did the actual recommendation (candidates[0], TAV-argmax) change?
     Structurally it cannot (draft_simulation.py's own selection reads only TAV, never
     block_opportunity) -- checked empirically against every node in the trajectory, not just
     asserted.
  3. Of the flags the new rule would remove, how implausible was the "denied" rival really:
     bucketed by the premium-driving rival's own take_probability.
  4. The Engine/BPA/ADP state-node agreement dataset, reshaped into the five buckets asked for.

Uses cdme_denial_semantics_audit.audit_candidates (fidelity-tested against the real production
functions) to get real rival_premium/take_probability per candidate -- never reimplements that
math.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
from cdme_denial_semantics_audit import audit_candidates
from draft_counterfactual import compare_trajectory
from draft_simulation import DraftTrajectory, PickRecord

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "denial_boundary_before_after_report.json"
POSITIONS = ("QB", "RB", "WR", "TE")
NUM_TEAMS = 12
NUM_ROUNDS = 12
BORDERLINE_FLOOR = 0.06  # RANK_TAKE_PROBABILITY[5] -- below this, a rival is barely on the board at all
OLD_PREMIUM_THRESHOLD = 8.0  # 2 * NEED_BONUS_PER_DEDICATED_SLOT (draft_room.py), the pre-95d2111 rule

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
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


def _load(path: Path) -> DraftTrajectory:
    data = json.loads(path.read_text())
    picks = tuple(PickRecord(**p) for p in data["picks"])
    return DraftTrajectory(config=data["config"], picks=picks)


def _agreement_buckets(nodes) -> dict:
    n = len(nodes)
    equals_bpa = sum(1 for x in nodes if x.equals_bpa)
    adp_available = sum(1 for x in nodes if x.adp_available)
    equals_adp = sum(1 for x in nodes if x.equals_adp)
    supported = sum(1 for x in nodes if x.deviation_supported is True)
    unsupported = sum(1 for x in nodes if x.deviation_supported is False)
    differs_both = sum(1 for x in nodes if not x.equals_bpa and x.adp_available and not x.equals_adp)
    return {
        "total_nodes": n,
        "engine_equals_bpa": equals_bpa,
        "adp_available_count": adp_available,
        "engine_equals_adp": equals_adp,
        "engine_differs_from_both_bpa_and_adp": differs_both,
        "engine_neq_bpa_but_tav_necessity_supports_it": supported,
        "engine_neq_bpa_and_unsupported": unsupported,
        "consistency_check_equals_bpa_plus_supported_plus_unsupported_eq_total": (
            equals_bpa + supported + unsupported == n
        ),
    }


def main() -> None:
    pick_order = ds.generate_pick_order([str(i) for i in range(1, NUM_TEAMS + 1)], total_rounds=NUM_ROUNDS)

    full_report: dict = {}
    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        print(f"\n=== {label} ===")
        merger = dm.DataMerger(league_format={
            "scoring": league_cfg["scoring"], "superflex": league_cfg["superflex"], "te_premium": league_cfg["te_premium"],
        })
        players_db = _build_pool_players_db(merger)
        league = dr.build_mock_league(**league_cfg)
        traj = _load(TRIALS_DIR / f"{label}.json")

        picks_so_far: list[dict] = []
        node_diffs: list[dict] = []
        removed_take_probs: list = []
        picks_with_old_flag_seen = 0

        for pick_rec in traj.picks:
            candidates_saved = pick_rec.snapshot["candidates"]
            candidate_ids = [c["id"] for c in candidates_saved]
            cur_picks = list(picks_so_far)

            if candidate_ids:
                audits = audit_candidates(
                    merger, players_db, cur_picks, pick_order, pick_rec.pick_no - 1, pick_rec.roster_id,
                    league, candidate_ids,
                )
                has_old_flag = any(a.rival_premium >= OLD_PREMIUM_THRESHOLD for a in audits)
                if has_old_flag:
                    picks_with_old_flag_seen += 1

                for a in audits:
                    old_block = a.rival_premium >= OLD_PREMIUM_THRESHOLD
                    new_block = bool(a.block_opportunity)
                    if old_block == new_block:
                        continue
                    c = next(cc for cc in candidates_saved if cc["id"] == a.player_id)
                    node_diffs.append({
                        "pick_label": pick_rec.pick_label,
                        "roster_id": pick_rec.roster_id,
                        "candidate_id": a.player_id,
                        "candidate_name": c.get("name"),
                        "old_block_opportunity": old_block,
                        "new_block_opportunity": new_block,
                        "rival_premium": a.rival_premium,
                        "premium_team_take_probability": a.premium_team_take_probability,
                        "necessity_label": c.get("necessity"),
                        "tav": c.get("tav"),
                        "was_the_actual_pick": (a.player_id == pick_rec.chosen_player_id),
                        "actual_chosen_player_id": pick_rec.chosen_player_id,
                    })
                    if old_block and not new_block:
                        removed_take_probs.append(a.premium_team_take_probability)

            picks_so_far.append({
                "pick_no": pick_rec.pick_no, "round": pick_rec.round,
                "roster_id": pick_rec.roster_id, "player_id": pick_rec.chosen_player_id,
            })

        recommendation_anomalies = [
            {"pick_label": p.pick_label, "chosen": p.chosen_player_id,
             "tav_argmax": max(p.snapshot["candidates"], key=lambda c: c["tav"])["id"]}
            for p in traj.picks
            if p.snapshot["candidates"] and
            max(p.snapshot["candidates"], key=lambda c: c["tav"])["id"] != p.chosen_player_id
        ]

        implausible = sum(1 for t in removed_take_probs if t is not None and t <= BORDERLINE_FLOOR)
        borderline = sum(1 for t in removed_take_probs if t is not None and BORDERLINE_FLOOR < t < 0.10)
        no_board_presence = sum(1 for t in removed_take_probs if t is None)
        still_credible_removed = sum(1 for t in removed_take_probs if t is not None and t >= 0.10)

        cf_nodes = compare_trajectory(merger, players_db, league, traj)
        cf_summary = _agreement_buckets(cf_nodes)

        affected_where_chosen = sum(1 for d in node_diffs if d["was_the_actual_pick"])
        result = {
            "picks_with_at_least_one_old_block_flag": picks_with_old_flag_seen,
            "affected_candidates_flag_changed": len(node_diffs),
            "affected_candidates": node_diffs,
            "affected_candidates_that_were_the_actual_pick": affected_where_chosen,
            "recommendation_anomalies_detected": recommendation_anomalies,  # expected: []
            "removed_flag_credibility_breakdown": {
                "total_removed": len(removed_take_probs),
                "genuinely_implausible_take_prob_le_0.06": implausible,
                "borderline_0.06_to_0.10": borderline,
                "no_opponent_board_presence_at_all": no_board_presence,
                "still_had_credible_path_but_removed_WOULD_BE_A_BUG": still_credible_removed,
            },
            "engine_bpa_adp_agreement": cf_summary,
        }
        full_report[label] = result

        print(f"picks with >=1 old-formula block flag: {picks_with_old_flag_seen}")
        print(f"candidates whose flag actually changed: {len(node_diffs)} (of which {affected_where_chosen} were the actual pick)")
        print(f"recommendation anomalies: {len(recommendation_anomalies)} (expected 0)")
        print("removed-flag credibility breakdown:", json.dumps(result["removed_flag_credibility_breakdown"], indent=2))
        print("engine/BPA/ADP agreement:", json.dumps(cf_summary, indent=2))

    OUT_PATH.write_text(json.dumps(full_report, indent=2))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
