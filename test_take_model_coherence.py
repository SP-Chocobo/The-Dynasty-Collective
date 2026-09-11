"""A CHARACTERIZATION of a known defect, not a statement of desired behaviour.

`draft_strategy._take_probability` maps a rank on an opponent's board to "how likely is that team
to take this player". A team takes exactly ONE player, so summing that map across a whole board
asks how many players the model thinks the team drafts. On a real 256-row board the answer is
6.23 (evidence/take_model/README.md).

WHEN THIS FILE GOES RED IT IS PROBABLY GOOD NEWS. It pins the defect so the defect cannot change
size quietly; a coherent replacement SHOULD fail it, and the repair is to rewrite these
assertions deliberately, with the modelling decision recorded. What must never happen is the
number drifting while both symptoms it causes (#206's 0.00, and survival_probability's d=1 at
exhaustion) stay in the register as separate mysteries.

NO BOARD IS BUILT HERE. The property is arithmetic over two module constants and a row count, so
the suite pays nothing for it. The 256 comes from the recorded measurement and is used only as a
realistic size, never as a value under test -- every assertion below holds for any large board.
"""

from __future__ import annotations

import unittest

import draft_strategy as ds

#: Rows on one real opponent board, measured once (evidence/take_model/README.md). Used as a
#: realistic magnitude; every assertion is written to hold for any board this size or larger.
MEASURED_BOARD_ROWS = 256


def expected_picks(rows: int) -> float:
    """What the model says about how many players ONE team drafts."""
    return sum(ds._take_probability(rank, False) for rank in range(1, rows + 1))


class ATeamDraftsOnePlayer(unittest.TestCase):
    def test_the_model_says_a_team_drafts_far_more_than_one(self):
        total = expected_picks(MEASURED_BOARD_ROWS)
        self.assertAlmostEqual(total, 6.23, places=2)
        self.assertGreater(total, 1.0, "if this passes, the model became coherent -- rewrite this file")

    def test_the_incoherence_grows_with_the_board_and_has_no_ceiling(self):
        """Not a fixed miscalibration: a deeper pool makes it strictly worse, because the floor
        is applied per row with no domain limit."""
        small, large = expected_picks(50), expected_picks(500)
        self.assertLess(small, large)
        self.assertAlmostEqual(large - small, ds.RANK_TAKE_PROBABILITY_FLOOR * 450, places=6)


class TheFloorIsTheDefectNotTheTable(unittest.TestCase):
    """The five-rank table is a documented, deliberately-uncertain prior and behaves like one.
    Blaming it would send a repair to the wrong place."""

    def test_the_table_alone_is_nearly_coherent(self):
        table = sum(ds.RANK_TAKE_PROBABILITY.values())
        self.assertAlmostEqual(table, 1.21, places=2)
        self.assertLess(table, 1.5)

    def test_the_floor_carries_almost_all_of_the_excess(self):
        total = expected_picks(MEASURED_BOARD_ROWS)
        floor_part = ds.RANK_TAKE_PROBABILITY_FLOOR * (MEASURED_BOARD_ROWS
                                                       - len(ds.RANK_TAKE_PROBABILITY))
        self.assertGreater(floor_part / (total - 1.0), 0.9)

    def test_rank_6_and_rank_251_are_assigned_the_same_probability(self):
        """The mechanism in one line: `.get(rank, FLOOR)` has no domain limit."""
        self.assertEqual(ds._take_probability(6, False), ds._take_probability(251, False))
        self.assertEqual(ds._take_probability(6, False), ds.RANK_TAKE_PROBABILITY_FLOOR)


class WhatTheFloorCanAndCannotExplain(unittest.TestCase):
    """Guards the scope statement in the evidence record, so the finding cannot be overclaimed
    later as the explanation of #206."""

    @staticmethod
    def _survival(p: float, opponents: int) -> float:
        return (1 - p) ** opponents

    def test_a_floored_player_does_NOT_read_as_zero_even_over_sixty_picks(self):
        """If this ever failed, the floor WOULD explain #206 and the evidence record's scope
        statement would be wrong."""
        survival = self._survival(ds.RANK_TAKE_PROBABILITY_FLOOR, 60)
        self.assertGreater(survival, 0.25)
        self.assertGreater(round(survival, 3), 0.0)

    def test_only_a_high_TABLE_rank_can_produce_a_reported_zero(self):
        survival = self._survival(ds.RANK_TAKE_PROBABILITY[1], 11)
        self.assertEqual(round(survival, 3), 0.0)

    def test_the_floor_gives_every_deep_bench_candidate_the_same_survival(self):
        """The d=1 collapse recorded in POST_AUDIT_PLAN, as arithmetic: past the table, rank
        carries no information at all, so no two candidates can be told apart."""
        deep = [ds._take_probability(r, False) for r in range(6, 60)]
        self.assertEqual(len(set(deep)), 1)


if __name__ == "__main__":
    unittest.main()
