import unittest

from run_out_of_sample_validation import (
    BASELINE_STANDARD_1QB,
    BPA_VISIBLE_RATE_FLOOR,
    DEVIATION_UNSUPPORTED_CEILING,
    EQUALS_BPA_RATE_TOLERANCE,
    classify_out_of_sample_result,
)


class ClassifyOutOfSampleResultTests(unittest.TestCase):
    def test_exact_baseline_match_is_stable(self):
        verdict = classify_out_of_sample_result(
            BASELINE_STANDARD_1QB["equals_bpa_rate"], 0, 1.0,
        )
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_small_rate_swing_within_tolerance_is_stable(self):
        rate = BASELINE_STANDARD_1QB["equals_bpa_rate"] - (EQUALS_BPA_RATE_TOLERANCE - 0.01)
        verdict = classify_out_of_sample_result(rate, 0, 1.0)
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_rate_swing_beyond_tolerance_is_flagged(self):
        rate = BASELINE_STANDARD_1QB["equals_bpa_rate"] - (EQUALS_BPA_RATE_TOLERANCE + 0.01)
        verdict = classify_out_of_sample_result(rate, 0, 1.0)
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")

    def test_deviation_unsupported_at_ceiling_is_still_stable(self):
        verdict = classify_out_of_sample_result(
            BASELINE_STANDARD_1QB["equals_bpa_rate"], DEVIATION_UNSUPPORTED_CEILING, 1.0,
        )
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_deviation_unsupported_over_ceiling_is_flagged(self):
        verdict = classify_out_of_sample_result(
            BASELINE_STANDARD_1QB["equals_bpa_rate"], DEVIATION_UNSUPPORTED_CEILING + 1, 1.0,
        )
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")

    def test_bpa_visible_rate_at_floor_is_stable(self):
        verdict = classify_out_of_sample_result(
            BASELINE_STANDARD_1QB["equals_bpa_rate"], 0, BPA_VISIBLE_RATE_FLOOR,
        )
        self.assertEqual(verdict, "STABLE — KEEP")

    def test_bpa_visible_rate_below_floor_is_flagged(self):
        verdict = classify_out_of_sample_result(
            BASELINE_STANDARD_1QB["equals_bpa_rate"], 0, BPA_VISIBLE_RATE_FLOOR - 0.01,
        )
        self.assertEqual(verdict, "SENSITIVITY DETECTED — EXPAND VALIDATION")


if __name__ == "__main__":
    unittest.main()
