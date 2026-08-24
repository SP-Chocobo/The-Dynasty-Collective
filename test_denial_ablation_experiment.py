"""Fidelity tests for run_denial_ablation_experiment.py's own three-condition necessity
scorer -- the FULL condition must reproduce compute_pick_necessity's real output exactly, ZERO
must match cdme_force_ablation.necessity_score(drop="denial"), and FILTERED must behave
correctly at both ends of the credible-path boolean, before any experimental finding built on
this scorer is trusted.
"""

from __future__ import annotations

import unittest

import pick_synthesis as ps
from cdme_force_ablation import necessity_score
from run_denial_ablation_experiment import _score


class ThreeConditionScorerFidelityTests(unittest.TestCase):
    def _raw(self, rival_premium: float) -> list[dict]:
        return [
            {
                "player_id": "a", "team_acquisition_value": 100.0, "need_bonus": 2.0,
                "eligibility_bonus": 1.0, "survival_probability": 0.6,
                "positional_cliff": None, "position_run_detected": False,
                "rival_premium": rival_premium,
            },
            {
                "player_id": "b", "team_acquisition_value": 90.0, "need_bonus": 0.0,
                "eligibility_bonus": 0.0, "survival_probability": 0.8,
                "positional_cliff": None, "position_run_detected": False,
                "rival_premium": 0.0,
            },
        ]

    def test_full_condition_matches_compute_pick_necessity_exactly(self):
        raw = self._raw(rival_premium=9.0)
        real_results = ps.compute_pick_necessity([dict(c) for c in raw], round_num=3)
        scores = _score(raw, round_num=3, credible={"a": True, "b": False})
        for c, (real_score, _real_label) in zip(raw, real_results):
            self.assertEqual(scores["full"][c["player_id"]], real_score)

    def test_zero_condition_matches_the_certified_ablation_modules_own_drop_denial(self):
        raw = self._raw(rival_premium=9.0)
        tavs = [c["team_acquisition_value"] for c in raw]
        scores = _score(raw, round_num=3, credible={"a": True, "b": False})
        for i, c in enumerate(raw):
            others = [v for j, v in enumerate(tavs) if j != i]
            expected = necessity_score(c, others, round_num=3, drop="denial")
            self.assertEqual(scores["zero"][c["player_id"]], expected)

    def test_filtered_condition_matches_full_when_credible_path_is_true(self):
        raw = self._raw(rival_premium=9.0)
        scores = _score(raw, round_num=3, credible={"a": True, "b": False})
        self.assertEqual(scores["filtered"]["a"], scores["full"]["a"])

    def test_filtered_condition_matches_zero_when_credible_path_is_false(self):
        raw = self._raw(rival_premium=9.0)
        scores = _score(raw, round_num=3, credible={"a": False, "b": False})
        self.assertEqual(scores["filtered"]["a"], scores["zero"]["a"])

    def test_zero_rival_premium_makes_all_three_conditions_identical(self):
        raw = self._raw(rival_premium=0.0)
        scores = _score(raw, round_num=3, credible={"a": False, "b": False})
        self.assertEqual(scores["full"]["b"], scores["zero"]["b"])
        self.assertEqual(scores["full"]["b"], scores["filtered"]["b"])


if __name__ == "__main__":
    unittest.main()
