"""Correctness tests for cdme_force_ablation.py's reimplementation of compute_pick_necessity's
formula -- proven faithful (drop=None reproduces the real function's own output exactly)
before any ablation result built on it is trusted. Real, committed-baseline data, same
builder pattern as the rest of this certification program.
"""

from __future__ import annotations

import unittest

import data_merger as dm
import draft_room as dr
import pick_synthesis as ps
from cdme_force_ablation import COMPONENTS, ablate_trajectory_candidates, necessity_score, summarize

POSITIONS = ("QB", "RB", "WR", "TE")
STANDARD_LEAGUE = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)


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


class ReimplementationFidelityTests(unittest.TestCase):
    """The single most important test in this file: the ablation module's own formula, with
    nothing dropped, must reproduce compute_pick_necessity's real production output exactly."""

    @classmethod
    def setUpClass(cls):
        merger = dm.DataMerger()
        players_db = _build_pool_players_db(merger)
        snap = ps.build_snapshot(
            merger, players_db, [], [str(i) for i in range(1, 13)], 0, "1",
            STANDARD_LEAGUE, pick_label="1.01",
        )
        cls.candidates = [
            {
                "player_id": c.player_id, "team_acquisition_value": c.team_acquisition_value,
                "need_bonus": c.need_bonus, "eligibility_bonus": c.eligibility_bonus,
                "survival_probability": c.survival_probability,
                "positional_cliff": c.positional_cliff,
                "position_run_detected": c.position_run_detected,
                "rival_premium": c.rival_premium,
            }
            for c in snap.candidates
        ]
        cls.round_num = snap.round

    def test_no_ablation_reproduces_the_real_function_exactly(self):
        raw = [dict(c) for c in self.candidates]
        real_results = ps.compute_pick_necessity(raw, self.round_num)
        tavs = [c["team_acquisition_value"] for c in self.candidates]
        for i, c in enumerate(self.candidates):
            others = [v for j, v in enumerate(tavs) if j != i]
            reimplemented_score = necessity_score(c, others, self.round_num, drop=None)
            self.assertEqual(reimplemented_score, real_results[i][0])

    def test_unknown_component_name_raises(self):
        tavs = [c["team_acquisition_value"] for c in self.candidates]
        with self.assertRaises(ValueError):
            necessity_score(self.candidates[0], tavs[1:], self.round_num, drop="not-a-real-component")


class AblationMechanicsTests(unittest.TestCase):
    def test_ablating_a_zero_contribution_component_never_changes_the_score(self):
        # A candidate with no survival data, no cliff, no run, no denial -- dropping any of
        # those four should be a strict no-op regardless of round.
        candidate = {
            "team_acquisition_value": 100.0, "need_bonus": 0.0, "eligibility_bonus": 0.0,
            "survival_probability": None, "positional_cliff": None,
            "position_run_detected": False, "rival_premium": 0.0,
        }
        baseline = necessity_score(candidate, [90.0], round_num=1, drop=None)
        for comp in ("survival", "cliff", "run", "denial"):
            self.assertEqual(necessity_score(candidate, [90.0], round_num=1, drop=comp), baseline)

    def test_ablate_trajectory_candidates_and_summarize_end_to_end(self):
        merger = dm.DataMerger()
        players_db = _build_pool_players_db(merger)
        snap = ps.build_snapshot(
            merger, players_db, [], [str(i) for i in range(1, 13)], 0, "1",
            STANDARD_LEAGUE, pick_label="1.01",
        )
        node = {
            "pick_label": "1.01", "round": snap.round,
            "candidates": [
                {
                    "player_id": c.player_id, "team_acquisition_value": c.team_acquisition_value,
                    "need_bonus": c.need_bonus, "eligibility_bonus": c.eligibility_bonus,
                    "survival_probability": c.survival_probability,
                    "positional_cliff": c.positional_cliff,
                    "position_run_detected": c.position_run_detected,
                    "rival_premium": c.rival_premium,
                }
                for c in snap.candidates
            ],
        }
        records = ablate_trajectory_candidates([node])
        self.assertEqual(len(records), len(snap.candidates))
        summary = summarize(records)
        self.assertEqual(set(summary["components"].keys()), set(COMPONENTS))
        self.assertEqual(summary["total_candidates"], len(snap.candidates))


if __name__ == "__main__":
    unittest.main()
