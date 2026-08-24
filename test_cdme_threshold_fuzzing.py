"""CDME certification battery, priority 2: threshold/boundary fuzzing.

For every consequential threshold CDME uses to flip a discrete regime, label, or flag, this
probes T-epsilon / T / T+epsilon and confirms: (a) the boundary is a clean, monotonic step --
no gap, no overlap, no off-by-one -- and (b) which side of "==" the threshold itself falls on
matches what the source actually implements (documented here as ">=" in every case checked,
since that's what each function's own comparison operator says).

These are unit-level tests against the classification functions directly (compute_pick_necessity's
_necessity_label, decision_regime, near_tie_flags, detect_positional_cliff), with hand-
constructed inputs sized to land exactly on each boundary -- real draft data can't be
steered to an exact ratio/margin/survival value on demand, and hitting a boundary exactly is
the entire point of this test class, so a synthetic input is the right tool here (per this
program's own "synthetic only to isolate a case real data can't reproduce" rule).

Meta-rule (same as test_cdme_certification.py): a surprising result gets classified, never
silently patched, as part of writing this file.
"""

from __future__ import annotations

import unittest

import draft_room as dr
import pick_synthesis as ps

EPS = 0.01


class NecessityLabelBoundaryTests(unittest.TestCase):
    """NECESSITY_LABEL_THRESHOLDS is a checked-top-down, first-match list -- must behave as a
    clean step function with no gaps or overlaps at any of its five internal boundaries."""

    def test_every_threshold_is_inclusive_the_score_at_the_threshold_gets_that_label(self):
        for threshold, label in ps.NECESSITY_LABEL_THRESHOLDS:
            self.assertEqual(ps._necessity_label(threshold), label)

    def test_just_below_each_threshold_falls_to_the_next_lower_label(self):
        # NECESSITY_LABEL_THRESHOLDS is sorted highest-first; the label just below threshold N
        # is whatever the NEXT entry in the list resolves to (its own >= check).
        for i in range(len(ps.NECESSITY_LABEL_THRESHOLDS) - 1):
            threshold, label = ps.NECESSITY_LABEL_THRESHOLDS[i]
            next_threshold, next_label = ps.NECESSITY_LABEL_THRESHOLDS[i + 1]
            self.assertEqual(
                ps._necessity_label(threshold - EPS), next_label,
                f"score just below {label}'s own threshold ({threshold}) should fall to {next_label!r}",
            )

    def test_just_above_each_threshold_keeps_the_same_label(self):
        for threshold, label in ps.NECESSITY_LABEL_THRESHOLDS:
            self.assertEqual(ps._necessity_label(threshold + EPS), label)

    def test_the_lowest_band_has_a_true_floor_no_score_falls_through(self):
        self.assertEqual(ps._necessity_label(-1000.0), ps.NECESSITY_LABEL_THRESHOLDS[-1][1])

    def test_thresholds_are_strictly_descending_no_duplicate_or_out_of_order_boundary(self):
        values = [t for t, _ in ps.NECESSITY_LABEL_THRESHOLDS]
        self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(len(values), len(set(values)), "a duplicate threshold would make one label unreachable")


class DecisionRegimeBoundaryTests(unittest.TestCase):
    """decision_regime is an AND-gate over two independent thresholds (margin >=
    NECESSITY_STANDOUT_REFERENCE_GAP, survival <= DECISIVE_SURVIVAL_THRESHOLD) -- both must
    hold for "decisive"; either alone must still read "contested", per the function's own
    docstring."""

    def _candidates(self, margin: float, survival: float) -> list[dict]:
        return [
            {"team_acquisition_value": 100.0 + margin, "survival_probability": survival},
            {"team_acquisition_value": 100.0, "survival_probability": 0.5},
        ]

    def test_both_thresholds_cleared_exactly_is_decisive(self):
        regime = ps.decision_regime(self._candidates(
            ps.NECESSITY_STANDOUT_REFERENCE_GAP, ps.DECISIVE_SURVIVAL_THRESHOLD,
        ))
        self.assertEqual(regime, "decisive")

    def test_margin_just_short_stays_contested_even_with_survival_cleared(self):
        regime = ps.decision_regime(self._candidates(
            ps.NECESSITY_STANDOUT_REFERENCE_GAP - EPS, ps.DECISIVE_SURVIVAL_THRESHOLD,
        ))
        self.assertEqual(regime, "contested")

    def test_survival_just_over_stays_contested_even_with_margin_cleared(self):
        regime = ps.decision_regime(self._candidates(
            ps.NECESSITY_STANDOUT_REFERENCE_GAP, ps.DECISIVE_SURVIVAL_THRESHOLD + EPS,
        ))
        self.assertEqual(regime, "contested")

    def test_both_thresholds_just_short_stays_contested(self):
        regime = ps.decision_regime(self._candidates(
            ps.NECESSITY_STANDOUT_REFERENCE_GAP - EPS, ps.DECISIVE_SURVIVAL_THRESHOLD + EPS,
        ))
        self.assertEqual(regime, "contested")

    def test_both_thresholds_cleared_with_room_to_spare_is_decisive(self):
        regime = ps.decision_regime(self._candidates(
            ps.NECESSITY_STANDOUT_REFERENCE_GAP + 10.0, ps.DECISIVE_SURVIVAL_THRESHOLD - 0.10,
        ))
        self.assertEqual(regime, "decisive")


class NearTieBoundaryTests(unittest.TestCase):
    def test_margin_exactly_at_band_is_in_tie_group(self):
        flags = ps.near_tie_flags([100.0, 100.0 - ps.NEAR_TIE_BAND])
        self.assertEqual(flags, [True, True])

    def test_margin_just_outside_band_is_not_a_tie(self):
        flags = ps.near_tie_flags([100.0, 100.0 - ps.NEAR_TIE_BAND - EPS])
        self.assertEqual(flags, [False, False])

    def test_margin_just_inside_band_is_a_tie(self):
        flags = ps.near_tie_flags([100.0, 100.0 - ps.NEAR_TIE_BAND + EPS])
        self.assertEqual(flags, [True, True])


class CliffTierBoundaryTests(unittest.TestCase):
    """detect_positional_cliff's tier boundary (ratio = this_gap / typical_gap, where
    typical_gap is the trimmed-median of every OTHER gap at that position) -- constructed as
    a small synthetic board sized to land the ratio exactly on CLIFF_HIGH_RATIO/
    CLIFF_MEDIUM_RATIO, which no real draft state can be steered to hit precisely on demand."""

    TYPICAL_GAP = 10.0  # by construction: other_gaps = [8, 10, 12], median (sorted, idx 1) = 10

    def _board(self, this_gap: float) -> list[dict]:
        # 5 QBs, sorted by bpa descending: P0 (tested, idx 0) .. P4. gaps = [this_gap, 12, 10, 8].
        bpa4 = 0.0
        bpa3 = bpa4 + 8.0
        bpa2 = bpa3 + 10.0
        bpa1 = bpa2 + 12.0
        bpa0 = bpa1 + this_gap
        return [
            {"player_id": "0", "position": "QB", "bpa": bpa0},
            {"player_id": "1", "position": "QB", "bpa": bpa1},
            {"player_id": "2", "position": "QB", "bpa": bpa2},
            {"player_id": "3", "position": "QB", "bpa": bpa3},
            {"player_id": "4", "position": "QB", "bpa": bpa4},
        ]

    def test_ratio_exactly_at_high_boundary_is_high_tier(self):
        result = ps.detect_positional_cliff(self._board(self.TYPICAL_GAP * ps.CLIFF_HIGH_RATIO), "0")
        self.assertEqual(result["typical_gap"], self.TYPICAL_GAP)
        self.assertEqual(result["tier"], "HIGH")

    def test_ratio_just_below_high_boundary_is_medium_tier(self):
        result = ps.detect_positional_cliff(self._board(self.TYPICAL_GAP * ps.CLIFF_HIGH_RATIO - EPS), "0")
        self.assertEqual(result["tier"], "MEDIUM")

    def test_ratio_exactly_at_medium_boundary_is_medium_tier(self):
        result = ps.detect_positional_cliff(self._board(self.TYPICAL_GAP * ps.CLIFF_MEDIUM_RATIO), "0")
        self.assertEqual(result["tier"], "MEDIUM")

    def test_ratio_just_below_medium_boundary_is_low_tier(self):
        result = ps.detect_positional_cliff(self._board(self.TYPICAL_GAP * ps.CLIFF_MEDIUM_RATIO - EPS), "0")
        self.assertEqual(result["tier"], "LOW")


class BlockOpportunityBoundaryTests(unittest.TestCase):
    """block_opportunity (decision_path_flags) fires at rival_premium >=
    2 * NEED_BONUS_PER_DEDICATED_SLOT -- checked directly against that exact multiple."""

    def _raw(self, premium: float) -> list[dict]:
        return [
            {"universal_value": 100.0, "team_acquisition_value": 100.0, "positional_forfeit": None, "rival_premium": premium},
            {"universal_value": 90.0, "team_acquisition_value": 90.0, "positional_forfeit": None, "rival_premium": 0.0},
        ]

    def test_premium_exactly_at_two_slots_fires(self):
        threshold = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        flags = ps.decision_path_flags(self._raw(threshold))
        self.assertTrue(flags[0]["block_opportunity"])

    def test_premium_just_below_two_slots_does_not_fire(self):
        threshold = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        flags = ps.decision_path_flags(self._raw(threshold - EPS))
        self.assertFalse(flags[0]["block_opportunity"])


if __name__ == "__main__":
    unittest.main()
