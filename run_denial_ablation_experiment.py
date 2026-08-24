"""Leave-one-force-out downstream-quality experiment for denial -- but corrected in scope
from what was originally proposed, per a decisive architectural finding this script's own
preamble proves before measuring anything:

PREREQUISITE FINDING (verified two ways -- by formula inspection AND by a real, small
simulation ablating denial entirely): denial (rival_premium / the denial_component inside
compute_pick_necessity) has ZERO causal path to which player gets drafted, in this
simulation harness or in live Draft Room. team_acquisition_value (draft_room.py) --
the number that actually ranks the board and determines snap.candidates[0], the pick
draft_simulation.py always takes -- is universal_value + need_bonus + eligibility_bonus. No
rival_premium/denial term appears in it anywhere. Confirmed empirically: monkeypatching
compute_pick_necessity to zero every candidate's rival_premium changed every necessity score
(as expected) but produced a BYTE-IDENTICAL draft trajectory to the unablated baseline (same
picks, same rosters, same everything) on a real 4-team/3-round simulation.

Denial's entire causal footprint, fully characterized (also confirmed by inspection):
pick_necessity / necessity_label (compute_pick_necessity) and block_opportunity
(decision_path_flags) -- and NOTHING else. decision_regime reads only TAV-margin and
survival_probability (no denial term). narrow_candidates (which candidates enter the human-
facing hand at all) is purely TAV-based. near_tie_with_leader is purely TAV-based.

CONSEQUENCE FOR THE EXPERIMENT AS ORIGINALLY SPECIFIED: re-running full drafts denial-
ablated vs intact and measuring accumulated roster value, regret/opportunity cost vs BPA,
starting-lineup value, replacement surplus, positional thinness/structural holes, or
1QB-vs-superflex roster differences would trivially show ZERO difference on every one of
those metrics, in every trial, with certainty -- not as an empirical result, but as a
mathematical consequence of the formula above. Running the originally-specified full
12-chair re-simulation would burn significant real compute (multiple ~5-7 minute drafts) to
reconfirm what a single small real run already proved in seconds. Not run here for that
reason -- this is "evidence can justify a change; curiosity cannot" cutting the other way:
there is no further roster-outcome evidence left to gather, because the causal path doesn't
exist for it to reveal.

WHAT THIS SCRIPT ACTUALLY MEASURES INSTEAD: the only real question left is whether denial
earns its keep at the ONE layer it actually touches -- necessity_label / block_opportunity,
the human-facing urgency read. Three conditions, per the user's own request, adapted to this
scope:
  1. FULL   -- denial_component computed normally (today's real behavior).
  2. ZERO   -- denial_component always 0 (denial entirely removed).
  3. FILTERED -- denial_component only counted when the premium-driving rival's own
     take_probability clears the stricter "credible path" bar (>=0.10, the same
     pre-declared threshold used in the prior denial-semantics audit) -- otherwise 0.

Measured per condition, on the same 120 real baseline-12chair-v1 picks where
block_opportunity fired on at least one candidate (the same population
run_denial_semantics_audit.py already scoped, for the same reason: the expensive opponent-
board recomputation is not needed where denial was never active in the first place):
  - necessity_label distribution shift vs FULL (how many candidates change bucket)
  - necessity ARGMAX flip rate vs FULL (does the "most urgent" read change)
  - stratified by whether the original candidate's own block_opportunity had a credible path
  - stratified by decision_regime (contested vs decisive) at that pick
  - 1QB vs superflex, reported separately throughout
"""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from cdme_denial_semantics_audit import audit_candidates
from cdme_force_ablation import _components, COMPONENTS
import pick_synthesis as ps

TRIALS_DIR = Path("data/draft_simulation_trials")
OUT_PATH = TRIALS_DIR / "denial_ablation_experiment_summary.json"
POSITIONS = ("QB", "RB", "WR", "TE")
NUM_TEAMS = 12
NUM_ROUNDS = 12
CREDIBLE_PATH_THRESHOLD = 0.10  # same pre-declared bar as run_denial_semantics_audit.py

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


def _score(raw: list[dict], round_num: int, credible: dict) -> dict[str, float]:
    """Three necessity scores per candidate -- full / zero / filtered -- built from the same
    _components() the certified force-ablation module already proved faithful to
    compute_pick_necessity. `credible` maps player_id -> bool (was this candidate's own
    premium-driving rival's take_probability >= CREDIBLE_PATH_THRESHOLD)."""
    tavs = [c["team_acquisition_value"] for c in raw]
    full, zero, filtered = {}, {}, {}
    for i, c in enumerate(raw):
        others = [v for j, v in enumerate(tavs) if j != i]
        parts = _components(c, others)
        raw_full = ps.NECESSITY_BASELINE + sum(parts.values())
        parts_zero = dict(parts); parts_zero["denial"] = 0.0
        raw_zero = ps.NECESSITY_BASELINE + sum(parts_zero.values())
        parts_filtered = dict(parts)
        if not credible.get(c["player_id"], False):
            parts_filtered["denial"] = 0.0
        raw_filtered = ps.NECESSITY_BASELINE + sum(parts_filtered.values())

        def _finish(raw_score: float) -> float:
            raw_score = max(0.0, min(100.0, raw_score))
            if round_num >= ps.LATE_ROUND_THRESHOLD:
                return round(raw_score * (ps.LATE_ROUND_NECESSITY_CAP / 100.0), 1)
            return round(raw_score, 1)

        full[c["player_id"]] = _finish(raw_full)
        zero[c["player_id"]] = _finish(raw_zero)
        filtered[c["player_id"]] = _finish(raw_filtered)
    return {"full": full, "zero": zero, "filtered": filtered}


def main() -> None:
    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS)

    summary: dict = {}
    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        league = dr.build_mock_league(**league_cfg)
        merger = dm.DataMerger(league_format={
            "scoring": league_cfg["scoring"], "superflex": league_cfg["superflex"], "te_premium": league_cfg["te_premium"],
        })
        players_db = _build_pool_players_db(merger)
        data = json.loads((TRIALS_DIR / f"{label}.json").read_text())

        picks_so_far: list[dict] = []
        stats = {
            cond: {"label_changes_vs_full": 0, "argmax_flips_vs_full": 0, "n_candidates": 0}
            for cond in ("zero", "filtered")
        }
        argmax_checked = 0
        by_regime = {"decisive": {"zero_flips": 0, "filtered_flips": 0, "checked": 0}, "contested": {"zero_flips": 0, "filtered_flips": 0, "checked": 0}}
        by_credible = {"credible": {"zero_flips": 0, "filtered_flips": 0, "checked": 0}, "not_credible": {"zero_flips": 0, "filtered_flips": 0, "checked": 0}}

        for pick in data["picks"]:
            candidates_saved = pick["snapshot"]["candidates"]
            has_block = any("block" in (c.get("forces") or []) for c in candidates_saved)
            cur_picks = list(picks_so_far)

            if has_block:
                candidate_ids = [c["id"] for c in candidates_saved]
                audits = audit_candidates(
                    merger, players_db, cur_picks, pick_order, pick["pick_no"] - 1, pick["roster_id"],
                    league, candidate_ids,
                )
                audits_by_id = {a.player_id: a for a in audits}
                credible = {
                    pid: (a.premium_team_take_probability is not None and a.premium_team_take_probability >= CREDIBLE_PATH_THRESHOLD)
                    for pid, a in audits_by_id.items()
                }

                raw = [{
                    "player_id": c["id"], "team_acquisition_value": c["tav"],
                    "need_bonus": c.get("needBonus", 0.0), "eligibility_bonus": c.get("eligBonus", 0.0),
                    "survival_probability": audits_by_id[c["id"]].survival_probability if c["id"] in audits_by_id else c.get("survival"),
                    "positional_cliff": {"tier": c["cliffTier"]} if c.get("cliffTier") else None,
                    "position_run_detected": False,
                    "rival_premium": audits_by_id[c["id"]].rival_premium if c["id"] in audits_by_id else (c.get("rivalPremium") or 0.0),
                } for c in candidates_saved]

                scores = _score(raw, pick["round"], credible)
                full_argmax = max(scores["full"], key=scores["full"].get)
                regime_key = pick["decision_regime"] if pick.get("decision_regime") in ("decisive", "contested") else "contested"

                if len(raw) >= 2:
                    argmax_checked += 1
                    for cond in ("zero", "filtered"):
                        cond_argmax = max(scores[cond], key=scores[cond].get)
                        flipped = cond_argmax != full_argmax
                        if flipped:
                            stats[cond]["argmax_flips_vs_full"] += 1
                        by_regime[regime_key][f"{cond}_flips"] += 1 if flipped else 0
                    by_regime[regime_key]["checked"] += 1

                for pid in scores["full"]:
                    is_credible = credible.get(pid, False)
                    bucket = "credible" if is_credible else "not_credible"
                    by_credible[bucket]["checked"] += 1
                    full_label = ps._necessity_label(scores["full"][pid])
                    for cond in ("zero", "filtered"):
                        stats[cond]["n_candidates"] += 1
                        cond_label = ps._necessity_label(scores[cond][pid])
                        if full_label != cond_label:
                            stats[cond]["label_changes_vs_full"] += 1
                            by_credible[bucket][f"{cond}_label_changes"] = by_credible[bucket].get(f"{cond}_label_changes", 0) + 1

            chosen = pick["chosen_player_id"]
            picks_so_far.append({"pick_no": pick["pick_no"], "round": pick["round"], "roster_id": pick["roster_id"], "player_id": chosen})

        for cond in ("zero", "filtered"):
            n = stats[cond]["n_candidates"]
            stats[cond]["label_change_rate"] = round(stats[cond]["label_changes_vs_full"] / n, 4) if n else None
            stats[cond]["argmax_flip_rate"] = round(stats[cond]["argmax_flips_vs_full"] / argmax_checked, 4) if argmax_checked else None

        for bucket in by_credible.values():
            n = bucket["checked"]
            for cond in ("zero", "filtered"):
                changes = bucket.get(f"{cond}_label_changes", 0)
                bucket[f"{cond}_label_change_rate"] = round(changes / n, 4) if n else None

        summary[label] = {
            "argmax_checked": argmax_checked,
            "condition_vs_full": stats,
            "by_decision_regime": by_regime,
            "by_original_credible_path": by_credible,
        }
        print(f"{label}:")
        print(json.dumps(summary[label], indent=2))

    OUT_PATH.write_text(json.dumps(summary, indent=2))
    print(f"Wrote summary to {OUT_PATH}")


if __name__ == "__main__":
    main()
