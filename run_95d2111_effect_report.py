"""The 95d2111 before/after receipt: for every one of the 120 real picks (both trial formats)
where block_opportunity fired on at least one candidate under the OLD (pre-95d2111) code, find
every candidate whose flag actually changed under the NEW (credible-path-gated) code, and
report the full decision context for each -- rival_premium, the premium-driving rival's own
take_probability, necessity_label, TAV, and whether that specific candidate was the player
actually drafted at that pick.

Answers four things, per the user's request:
  1. Which nodes are affected (flag changed) vs merely re-confirmed (flag unchanged).
  2. For every affected node: did the actual recommendation (candidates[0], TAV-argmax) change?
     Structurally it cannot (draft_simulation.py's own selection reads only TAV, never
     block_opportunity) -- this checks that empirically against every real affected node rather
     than asserting it.
  3. Of the flags REMOVED (old=True, new=False -- the only direction possible, since the new
     rule is old AND credible, never a superset), how implausible was the "denied" rival really:
     bucketed by the premium-driving rival's own take_probability, including the check that
     zero removed flags still had a credible path (that bucket existing at all would mean a
     logic bug, not a calibration question).
  4. The existing Engine/BPA/ADP state-node agreement dataset, reshaped into the five buckets
     asked for (Engine=BPA, Engine=ADP, Engine departs both, Engine departs BPA supported by
     TAV/necessity signal, Engine departs BPA unsupported) -- read from the already-computed
     Phase 1/2 counterfactual nodes (draft_counterfactual.compare_trajectory), which reuses
     necessity_label/near_tie_with_leader and therefore never depended on block_opportunity in
     the first place; reported here from the PRESERVED pre-95d2111 baseline since that dataset
     is unaffected by this change (confirmed independently by compare_baseline_pre_post_
     95d2111.py's byte-identical counterfactual-node check).

Uses cdme_denial_semantics_audit.audit_candidates (fidelity-tested against the real production
functions) to recompute rival_premium/block_opportunity/take_probability against CURRENT code
for the exact same picks-so-far state the old trajectory already recorded -- cheaper and more
precise than a full re-simulation for isolating what changed at the flag layer, while
compare_baseline_pre_post_95d2111.py separately confirms the full re-simulated trajectory
matches at the top level.
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from cdme_denial_semantics_audit import audit_candidates
from draft_simulation import DraftTrajectory, PickRecord

TRIALS_DIR = Path("data/draft_simulation_trials")
OLD_DIR = TRIALS_DIR / "baseline_pre_95d2111"
OUT_PATH = TRIALS_DIR / "denial_boundary_before_after_report.json"
POSITIONS = ("QB", "RB", "WR", "TE")
NUM_TEAMS = 12
NUM_ROUNDS = 12
BORDERLINE_FLOOR = 0.06  # RANK_TAKE_PROBABILITY[5] -- below this, a rival is barely on the board at all

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
}


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


def _load(path: Path) -> DraftTrajectory:
    data = json.loads(path.read_text())
    picks = tuple(PickRecord(**p) for p in data["picks"])
    return DraftTrajectory(config=data["config"], picks=picks)


def _agreement_buckets(nodes_path: Path) -> dict:
    if not nodes_path.exists():
        return {}
    nodes = json.loads(nodes_path.read_text())
    n = len(nodes)
    equals_bpa = sum(1 for x in nodes if x["equals_bpa"])
    adp_available = sum(1 for x in nodes if x["adp_available"])
    equals_adp = sum(1 for x in nodes if x.get("equals_adp"))
    supported = sum(1 for x in nodes if x.get("deviation_supported") is True)
    unsupported = sum(1 for x in nodes if x.get("deviation_supported") is False)
    differs_both = sum(1 for x in nodes if not x["equals_bpa"] and x["adp_available"] and not x.get("equals_adp"))
    return {
        "total_nodes": n,
        "engine_equals_bpa": equals_bpa,
        "adp_available_count": adp_available,
        "engine_equals_adp": equals_adp,
        "engine_differs_from_both_bpa_and_adp": differs_both,
        "engine_neq_bpa_but_tav_necessity_supports_it": supported,
        "engine_neq_bpa_and_unsupported": unsupported,
        # sanity identity: every non-BPA pick is either supported or unsupported (equals_bpa
        # picks have deviation_supported=None -- nothing to classify).
        "consistency_check_equals_bpa_plus_supported_plus_unsupported_eq_total": (
            equals_bpa + supported + unsupported == n
        ),
    }


def main() -> None:
    merger, players_db = _build_pool_players_db()
    pick_order = ds.generate_pick_order([str(i) for i in range(1, NUM_TEAMS + 1)], total_rounds=NUM_ROUNDS)

    full_report: dict = {}
    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        print(f"\n=== {label} ===")
        league = dr.build_mock_league(**league_cfg)
        traj = _load(OLD_DIR / f"{label}.json")

        picks_so_far: list[dict] = []
        node_diffs: list[dict] = []
        removed_take_probs: list = []
        picks_with_block_seen = 0

        for pick_rec in traj.picks:
            candidates_saved = pick_rec.snapshot["candidates"]
            has_block = any("block" in (c.get("forces") or []) for c in candidates_saved)
            cur_picks = list(picks_so_far)

            if has_block:
                picks_with_block_seen += 1
                candidate_ids = [c["id"] for c in candidates_saved]
                audits = audit_candidates(
                    merger, players_db, cur_picks, pick_order, pick_rec.pick_no - 1, pick_rec.roster_id,
                    league, candidate_ids,
                )
                audits_by_id = {a.player_id: a for a in audits}

                for c in candidates_saved:
                    old_block = "block" in (c.get("forces") or [])
                    a = audits_by_id.get(c["id"])
                    new_block = bool(a.block_opportunity) if a is not None else False
                    if old_block == new_block:
                        continue  # unaffected -- most candidates land here
                    node_diffs.append({
                        "pick_label": pick_rec.pick_label,
                        "roster_id": pick_rec.roster_id,
                        "candidate_id": c["id"],
                        "candidate_name": c.get("name"),
                        "old_block_opportunity": old_block,
                        "new_block_opportunity": new_block,
                        "rival_premium": a.rival_premium if a is not None else c.get("rivalPremium"),
                        "premium_team_take_probability": a.premium_team_take_probability if a is not None else None,
                        "necessity_label": c.get("necessity"),  # untouched by this change -- same before/after
                        "tav": c.get("tav"),
                        "was_the_actual_pick": (c["id"] == pick_rec.chosen_player_id),
                        "actual_chosen_player_id": pick_rec.chosen_player_id,
                    })
                    if old_block and not new_block:
                        removed_take_probs.append(a.premium_team_take_probability if a is not None else None)

            picks_so_far.append({
                "pick_no": pick_rec.pick_no, "round": pick_rec.round,
                "roster_id": pick_rec.roster_id, "player_id": pick_rec.chosen_player_id,
            })

        # Recommendation-change check: for EVERY pick (not just affected ones), the actually
        # drafted player must be the TAV-argmax of that pick's saved candidate set -- confirms
        # empirically, node by node, that the recorded recommendation never depended on
        # block_opportunity (draft_simulation.py's own selection rule, unchanged).
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

        cf_summary = _agreement_buckets(OLD_DIR / f"{label}_counterfactual_nodes.json")

        affected_where_chosen = sum(1 for d in node_diffs if d["was_the_actual_pick"])
        result = {
            "picks_with_at_least_one_old_block_flag": picks_with_block_seen,
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

        print(f"picks with >=1 old block flag: {picks_with_block_seen}")
        print(f"candidates whose flag actually changed: {len(node_diffs)} (of which {affected_where_chosen} were the actual pick)")
        print(f"recommendation anomalies: {len(recommendation_anomalies)} (expected 0)")
        print("removed-flag credibility breakdown:", json.dumps(result["removed_flag_credibility_breakdown"], indent=2))
        print("engine/BPA/ADP agreement:", json.dumps(cf_summary, indent=2))

    OUT_PATH.write_text(json.dumps(full_report, indent=2))
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
