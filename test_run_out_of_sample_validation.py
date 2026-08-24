import unittest

from run_out_of_sample_validation import (
    BASELINES,
    BPA_VISIBLE_RATE_FLOOR,
    DEVIATION_UNSUPPORTED_CEILING,
    EQUALS_BPA_RATE_TOLERANCE,
    classify_out_of_sample_result,
)

_STANDARD_BASELINE_RATE = BASELINES["standard_1qb"]["equals_bpa_rate"]


class ClassifyOutOfSampleResultTests(unittest.TestCase):
    def test_exact_baseline_match_is_stable(self):
        verdict = classify_out_of_sample_result(_STANDARD_BASELINE_RATE, 0, 1.0, _STANDARD_BASELINE_RATE)
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_small_rate_swing_within_tolerance_is_stable(self):
        rate = _STANDARD_BASELINE_RATE - (EQUALS_BPA_RATE_TOLERANCE - 0.01)
        verdict = classify_out_of_sample_result(rate, 0, 1.0, _STANDARD_BASELINE_RATE)
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_rate_swing_beyond_tolerance_is_flagged(self):
        rate = _STANDARD_BASELINE_RATE - (EQUALS_BPA_RATE_TOLERANCE + 0.01)
        verdict = classify_out_of_sample_result(rate, 0, 1.0, _STANDARD_BASELINE_RATE)
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")

    def test_deviation_unsupported_at_ceiling_is_still_stable(self):
        verdict = classify_out_of_sample_result(
            _STANDARD_BASELINE_RATE, DEVIATION_UNSUPPORTED_CEILING, 1.0, _STANDARD_BASELINE_RATE,
        )
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_deviation_unsupported_over_ceiling_is_flagged(self):
        verdict = classify_out_of_sample_result(
            _STANDARD_BASELINE_RATE, DEVIATION_UNSUPPORTED_CEILING + 1, 1.0, _STANDARD_BASELINE_RATE,
        )
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")

    def test_bpa_visible_rate_at_floor_is_stable(self):
        verdict = classify_out_of_sample_result(
            _STANDARD_BASELINE_RATE, 0, BPA_VISIBLE_RATE_FLOOR, _STANDARD_BASELINE_RATE,
        )
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_bpa_visible_rate_below_floor_is_flagged(self):
        verdict = classify_out_of_sample_result(
            _STANDARD_BASELINE_RATE, 0, BPA_VISIBLE_RATE_FLOOR - 0.01, _STANDARD_BASELINE_RATE,
        )
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")

    def test_classification_is_relative_to_the_baseline_passed_in_not_a_fixed_constant(self):
        # A superflex-shaped trial must be judged against superflex's own baseline rate, not
        # standard_1qb's -- this is what makes the function reusable across trial families
        # instead of hardcoding one baseline internally.
        superflex_rate = BASELINES["superflex"]["equals_bpa_rate"]
        verdict = classify_out_of_sample_result(superflex_rate, 0, 1.0, superflex_rate)
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_both_baseline_families_are_registered(self):
        self.assertIn("standard_1qb", BASELINES)
        self.assertIn("superflex", BASELINES)


if __name__ == "__main__":
    unittest.main()
