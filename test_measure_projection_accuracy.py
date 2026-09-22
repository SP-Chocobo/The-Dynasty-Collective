"""The predictiveness harness's own correctness, checked offline against synthetic seasons.

`measure_projection_accuracy` cannot be exercised end to end from the audit sandbox -- it needs
Sleeper, which is unreachable here. What CAN be checked, and is the part that would be wrong in a
way nobody noticed, is `accuracy_by_position`: the function that decides what "how much of the
projected spread materialised" means.

The property that matters most is the ranking direction. Ranking by OUTCOME and then measuring
the outcome gap reports a spread that is real but unownable -- nobody drafts with hindsight. The
projection has to pick the players and the season has to say what they were worth. A test that
only fed it well-behaved data would pass either way, so the noise case below is built so the two
directions give visibly different answers.
"""

from __future__ import annotations

import unittest

from measure_projection_accuracy import accuracy_by_position


def _db(ids, position):
    return {pid: {"position": position, "fantasy_positions": [position],
                  "full_name": f"{position}{i}"} for i, pid in enumerate(ids)}


class WhatTheHarnessMeasuresTests(unittest.TestCase):

    def test_a_position_whose_projections_hold_keeps_its_whole_spread(self):
        """The control. If projections were perfect the realised share is 1.0, and any term
        derived from this would leave such a position's VOR untouched."""
        ids = [str(i) for i in range(1, 21)]
        projected = {pid: 200.0 - 5 * i for i, pid in enumerate(ids)}
        actual = dict(projected)                       # projections came true exactly
        out = accuracy_by_position(projected, actual, _db(ids, "RB"), 12, {"RB": 1.0})["RB"]
        self.assertTrue(out["measurable"])
        self.assertEqual(out["replacement_rank"], 12)
        self.assertEqual(out["realised_share"], 1.0)

    def test_a_position_whose_projections_are_noise_keeps_none_of_it(self):
        """The case K and DST are suspected of. Everyone was projected apart and everyone scored
        the same, so the projected gap was real and the realised gap is zero."""
        ids = [str(i) for i in range(1, 21)]
        projected = {pid: 200.0 - 5 * i for i, pid in enumerate(ids)}
        actual = {pid: 120.0 for pid in ids}           # projection told you nothing
        out = accuracy_by_position(projected, actual, _db(ids, "DEF"), 12, {"DEF": 1.0})["DEF"]
        self.assertEqual(out["projected_gap"], 55.0)
        self.assertEqual(out["realised_gap"], 0.0)
        self.assertEqual(out["realised_share"], 0.0)

    def test_the_ranks_come_from_the_PROJECTION_and_not_the_result(self):
        """THE DESIGN PROPERTY. Here the projection is exactly BACKWARDS -- the player projected
        best finished worst. Ranking by projection therefore yields a NEGATIVE realised gap,
        which is the honest answer: believing the projection actively cost you. Ranking by
        outcome would report a large positive spread and call a useless projection excellent.
        """
        ids = [str(i) for i in range(1, 21)]
        projected = {pid: 200.0 - 5 * i for i, pid in enumerate(ids)}
        actual = {pid: 100.0 + 5 * i for i, pid in enumerate(ids)}     # perfectly inverted
        out = accuracy_by_position(projected, actual, _db(ids, "K"), 12, {"K": 1.0})["K"]
        self.assertGreater(out["projected_gap"], 0)
        self.assertLess(out["realised_gap"], 0,
                        "an inverted projection must produce a NEGATIVE realised gap -- a "
                        "positive one means the ranking was taken from the outcome")
        self.assertLess(out["realised_share"], 0)

    def test_a_pool_too_small_to_reach_replacement_rank_is_refused(self):
        """Absence, not a number. Eight kickers cannot answer a question about the 12th-best
        kicker, and a spread computed off the end of the list would be exactly the clamp #214
        exists to refuse."""
        ids = [str(i) for i in range(1, 9)]
        projected = {pid: 100.0 - i for i, pid in enumerate(ids)}
        out = accuracy_by_position(projected, dict(projected), _db(ids, "K"), 12, {"K": 1.0})["K"]
        self.assertFalse(out["measurable"])
        self.assertIn("replacement rank", out["why"])

    def test_a_zero_projected_gap_yields_None_rather_than_zero(self):
        """#187 at the one place it would be easiest to miss: a share of 0.0 reads as 'none of
        it materialised', which is a finding. An undefined ratio is an absence."""
        ids = [str(i) for i in range(1, 21)]
        projected = {pid: 100.0 for pid in ids}        # no projected spread at all
        actual = {pid: 100.0 + i for i, pid in enumerate(ids)}
        out = accuracy_by_position(projected, actual, _db(ids, "DEF"), 12, {"DEF": 1.0})["DEF"]
        self.assertEqual(out["projected_gap"], 0.0)
        self.assertIsNone(out["realised_share"])

    def test_a_player_with_no_result_is_excluded_rather_than_scored_zero(self):
        """A player who did not play is not a player who scored nothing. Counting him as 0.0
        would manufacture a spread out of absence -- the same defect the engine's own absence
        contract exists to prevent."""
        ids = [str(i) for i in range(1, 21)]
        projected = {pid: 200.0 - 5 * i for i, pid in enumerate(ids)}
        actual = {pid: v for pid, v in projected.items() if pid != "1"}   # the best never played
        out = accuracy_by_position(projected, actual, _db(ids, "RB"), 12, {"RB": 1.0})["RB"]
        self.assertEqual(out["pool"], 19)
        self.assertEqual(out["best"], "RB1", "the excluded player must not be ranked first")


if __name__ == "__main__":
    unittest.main()


class TheRatioReportsItsOwnResolutionTests(unittest.TestCase):
    """#18: the first real run was over-read, and these are the two numbers that would have
    stopped it.

    A two-player difference is n = 1 pair. When the replacement rank sits on a TIE, the ratio is
    decided by which tied player the projection happened to rank there; when the projected gap is
    a rounding error, the ratio is a division by nearly zero. Both happened on live data, at
    exactly the two positions the work exists to fix. Neither is a bug in the arithmetic, so
    neither could be caught by a test of the arithmetic -- they are missing DIAGNOSTICS, and these
    pin them.
    """

    def test_the_row_says_it_rests_on_ONE_pair(self):
        """The engine-measurement rule is to print `n`. Here `n` is 1 and the instrument never
        said so, which is most of why a table of twelve ratios read as twelve measurements."""
        row = accuracy_by_position({"a": 30.0, "b": 20.0, "c": 10.0},
                                   {"a": 30.0, "b": 20.0, "c": 10.0},
                                   _db(["a", "b", "c"], "K"), 2, {"K": 1.0})["K"]
        self.assertEqual(row["pairs"], 1)

    def test_a_tie_at_the_replacement_rank_is_counted(self):
        """Measured on real 2024 data: THREE kickers finished at exactly 133.0 at the replacement
        rank, because kicker totals are integers -- a field goal is 3, an extra point is 1. The
        reported ratio was whichever of the three the projection ranked twelfth."""
        projected = {"a": 30.0, "b": 20.0, "c": 19.0, "d": 18.0}
        actual = {"a": 30.0, "b": 25.0, "c": 25.0, "d": 25.0}
        row = accuracy_by_position(projected, actual, _db(["a", "b", "c", "d"], "K"),
                                   2, {"K": 1.0})["K"]
        self.assertEqual(row["realised_ties_at_replacement_rank"], 3)

    def test_no_tie_reports_the_replacement_player_alone(self):
        """Non-vacuity: a counter that always returned 3 would pass the test above."""
        projected = {"a": 30.0, "b": 20.0, "c": 10.0}
        actual = {"a": 30.0, "b": 20.0, "c": 5.0}
        row = accuracy_by_position(projected, actual, _db(["a", "b", "c"], "K"),
                                   2, {"K": 1.0})["K"]
        self.assertEqual(row["realised_ties_at_replacement_rank"], 1)

    def test_a_player_with_no_result_cannot_be_counted_as_a_tie(self):
        """The tie count has to be over the same population the ratio is, or it describes a
        different set than the number it is attached to."""
        projected = {"a": 30.0, "b": 20.0, "c": 10.0, "ghost": 25.0}
        actual = {"a": 30.0, "b": 20.0, "c": 20.0}
        row = accuracy_by_position(projected, actual, _db(["a", "b", "c", "ghost"], "K"),
                                   2, {"K": 1.0})["K"]
        self.assertEqual(row["realised_ties_at_replacement_rank"], 2)

    def test_the_negligible_gap_bound_is_one_point_a_game(self):
        """DERIVED, not chosen (#56). DEF 2024 projected a 6.7-point gap across a whole season and
        the instrument divided by it. The bound is the smallest per-game difference this scoring
        can express -- one point over seventeen games -- and it gates a WARNING, never a value."""
        from measure_projection_accuracy import NEGLIGIBLE_PROJECTED_GAP
        self.assertEqual(NEGLIGIBLE_PROJECTED_GAP, 17.0)
        self.assertGreater(NEGLIGIBLE_PROJECTED_GAP, 6.7,
                           "the measured DEF 2024 projected gap must fall inside the bound, or "
                           "the bound would not have caught the case it was derived from")
