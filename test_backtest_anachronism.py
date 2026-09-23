"""The backtest's anachronism guard: a later rookie must not be draftable in an earlier season.

WHY THIS FILE EXISTS. The confound it guards was invisible for two full runs of
`run_backtest_grade`, and it did not announce itself as a crash -- it announced itself as the
engine drafting Brock Bowers in round 2 of a 2023 draft and realizing 0.0 for him. The mechanism
is a fallback working exactly as designed: `draft_room.build_available_pool` treats a projection
that scores to zero as NO projection (`sleeper_points = scored if scored != 0 else None`), and a
player who did not exist in the backtested season has a row of zeros, so the board reaches for the
2026 vendor export and prices him at the top of the draft.

These tests pin the guard's BEHAVIOUR on synthetic data, and one pins the mechanism itself against
the real `draft_room` source so the guard cannot silently stop matching the fallback it guards.
"""

from __future__ import annotations

import unittest

import run_backtest_grade as bg

#: A PPR-ish rulebook, small enough to reason about by hand.
SCORING = {"rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0}


class ThePeriodCorrectPoolTests(unittest.TestCase):

    def test_a_player_with_no_projection_that_season_is_dropped(self):
        """The whole point: a row of zeros means he was not in the league, not that he was bad."""
        points = {"real": 250.0, "ghost": 259.0}
        projections = {"real": {"rec": 90, "rec_yd": 1200, "rec_td": 8},
                       "ghost": {"rec": 0, "rec_yd": 0, "rec_td": 0}}
        kept, dropped = bg.period_correct_pool(points, projections, SCORING)
        self.assertEqual(sorted(kept), ["real"])
        self.assertEqual(dropped, ["ghost"])

    def test_the_ghost_carried_a_top_of_board_price_before_the_guard(self):
        """NON-VACUITY. If the dropped player were priced at nothing the guard would be pointless.

        This is the measured shape: in the real 2023 pool the dropped players were priced as high
        as 340.0, ABOVE most of the players who actually played that season.
        """
        points = {"real": 250.0, "ghost": 340.0}
        projections = {"real": {"rec": 90, "rec_yd": 1200, "rec_td": 8}, "ghost": {}}
        self.assertGreater(points["ghost"], points["real"])
        kept, _ = bg.period_correct_pool(points, projections, SCORING)
        self.assertNotIn("ghost", kept)

    def test_a_player_missing_from_the_projection_dict_entirely_is_dropped(self):
        """`None` and an all-zero row are the same claim -- no projection -- and both must go."""
        kept, dropped = bg.period_correct_pool({"absent": 300.0}, {}, SCORING)
        self.assertEqual(kept, {})
        self.assertEqual(dropped, ["absent"])

    def test_a_real_player_keeps_his_board_price_not_his_projection(self):
        """The guard is a FILTER, never a re-pricing. Changing the price would change the arm."""
        points = {"real": 250.0}
        projections = {"real": {"rec": 90, "rec_yd": 1200, "rec_td": 8}}
        kept, _ = bg.period_correct_pool(points, projections, SCORING)
        self.assertEqual(kept["real"], 250.0)

    def test_a_faint_but_real_projection_survives(self):
        """A deep bench player projected for almost nothing still EXISTED. Only zero is absence.

        The guard must not become a quality filter: that would narrow the pool on a judgement
        nobody made, and both arms would then draft from a board this instrument invented.
        """
        points = {"faint": 4.0}
        kept, dropped = bg.period_correct_pool(points, {"faint": {"rec": 1}}, SCORING)
        self.assertEqual(sorted(kept), ["faint"])
        self.assertEqual(dropped, [])


class TheGuardMatchesTheFallbackItGuardsTests(unittest.TestCase):
    """If `draft_room`'s zero test changes, the guard stops lining up with the confound.

    Pinned against the real source rather than restated, because a restated constant is a second
    home for one rule (#126) and would drift silently.
    """

    def test_the_board_still_treats_a_zero_scored_projection_as_no_projection(self):
        import inspect
        import draft_room as dr
        source = inspect.getsource(dr.build_available_pool)
        self.assertIn("scored if scored != 0 else None", source,
                      "the board no longer nulls a zero projection -- re-derive the backtest "
                      "anachronism guard against whatever replaced it")

    def test_the_guard_uses_the_same_zero_test(self):
        import inspect
        source = inspect.getsource(bg.period_correct_pool)
        self.assertIn("!= 0.0", source)


if __name__ == "__main__":
    unittest.main()
