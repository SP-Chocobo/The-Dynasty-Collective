"""One-time real-data verification for the REFINE production change (block_opportunity now
gated on credible rival path): recomputes cdme_denial_semantics_audit.audit_candidates --
which now matches pick_synthesis.decision_path_flags exactly, per its own fidelity tests --
on the SAME 120 real baseline-12chair-v1 picks (both trial formats) run_denial_semantics_
audit.py already scoped and measured, and checks the new block_opportunity count against that
prior run's own already-saved credible_path_satisfied figure (108/142 standard_1qb/superflex,
data/draft_simulation_trials/denial_semantics_summary.json) -- since new block_opportunity =
old block_opportunity AND credible_rival_path, and block_flagged_total was already scoped to
old-block_opportunity-true candidates, the two counts should be identical by construction if
the production wiring is correct. Also confirms Superflex -- the format where real necessity-
argmax flips were shown to survive the stricter filter -- still has a non-zero, non-trivial
count of real DENIAL flags post-change (the "stricter semantics didn't eliminate the
legitimate cases" check), not just an algebraic identity.

Not part of the automated unittest suite (same convention as run_denial_semantics_audit.py /
run_denial_ablation_experiment.py: this needs the gitignored real trial JSON, which a fresh
clone won't have) -- a one-time confirmation run, printed and asserted here, referenced from
the commit message as the real-data evidence behind this change."""

from __future__ import annotations

import json
from pathlib import Path

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from cdme_denial_semantics_audit import audit_candidates

TRIALS_DIR = Path("data/draft_simulation_trials")
POSITIONS = ("QB", "RB", "WR", "TE")
NUM_TEAMS = 12
NUM_ROUNDS = 12

TRIAL_LEAGUE_CONFIG = {
    "standard_1qb": dict(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True),
    "superflex": dict(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True),
}
EXPECTED_CREDIBLE_PATH_SATISFIED = {"standard_1qb": 108, "superflex": 142}


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


def main() -> None:
    forward_slots = [str(i) for i in range(1, NUM_TEAMS + 1)]
    pick_order = ds.generate_pick_order(forward_slots, total_rounds=NUM_ROUNDS)

    all_ok = True
    for label, league_cfg in TRIAL_LEAGUE_CONFIG.items():
        league = dr.build_mock_league(**league_cfg)
        merger = dm.DataMerger(league_format={
            "scoring": league_cfg["scoring"], "superflex": league_cfg["superflex"], "te_premium": league_cfg["te_premium"],
        })
        players_db = _build_pool_players_db(merger)
        data = json.loads((TRIALS_DIR / f"{label}.json").read_text())

        picks_so_far: list[dict] = []
        new_block_opportunity_count = 0
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
                new_block_opportunity_count += sum(1 for a in audits if a.block_opportunity)

            chosen = pick["chosen_player_id"]
            picks_so_far.append({"pick_no": pick["pick_no"], "round": pick["round"], "roster_id": pick["roster_id"], "player_id": chosen})

        expected = EXPECTED_CREDIBLE_PATH_SATISFIED[label]
        ok = new_block_opportunity_count == expected
        all_ok = all_ok and ok
        print(f"{label}: new block_opportunity count = {new_block_opportunity_count} (expected {expected}) -- {'MATCH' if ok else 'MISMATCH'}")
        assert new_block_opportunity_count > 0, f"{label}: the stricter gate must not eliminate every legitimate denial flag"

    assert all_ok, "new block_opportunity count did not match the prior audit's own credible_path_satisfied figure"
    print("Verified: post-REFINE block_opportunity == pre-change credible_path_satisfied, both trials. Real legitimate DENIAL flags survive in both formats.")


if __name__ == "__main__":
    main()
