"""A CHARACTERIZATION of a known defect, not a statement of desired behaviour.

`draft_strategy._take_probability` maps a rank on an opponent's board to "how likely is that team
to take this player". A team takes exactly ONE player, so summing that map across a whole board
asks how many players the model thinks the team drafts. On a real 256-row board the answer is
6.23 (evidence/take_model/README.md); on Fourth and Forever's own 481-row board it is 10.73
(evidence/survival_mechanism/collapse_decomposition.json). Both are real boards -- the total is
a FUNCTION OF THE POOL, not a fixed miscalibration, which is why no single figure is under test.

#206 HAS A SECOND HALF, and it now has evidence too. The mass defect above is one cause of the
0.00; the other is that every opponent board is built by the SAME valuation, so the engine's own
#1 is rank 1 on all of them at once and survival multiplies 0.55 by itself. The last class in
this file pins that half through `estimate_survival` itself.

THE TWO CAUSES ARE NOT TWO ROUTES TO ONE ANSWER, and the last class is written to stop that
reading. At the measured turn -- 22 intervening picks, 11 distinct rivals each picking twice --
normalising the mass lifts survival from 2.3e-8 to 0.314 in one step. Agreement cannot be moved
to the same place from either side: with every rival disagreeing it is 0.641, and a SINGLE rival
holding the top opinion already drops it to 0.135, because that opinion applies to two picks.
Agreement is superlinear (three agreeing rivals force 0.006), so one shared valuation supplies
far more of it than the collapse requires.

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


def _boards(rivals, target: str, agreeing: int, rank: int = 1) -> dict:
    """One board per DISTINCT intervening roster, shaped the way `_build_opponent_boards`
    returns them. The first `agreeing` of them rank `target` at `rank`; the rest bury him past
    the table's last key, where `_take_probability` hands out only the floor.

    WHY PER ROSTER AND NOT PER PICK, which is the fixture error this signature exists to stop.
    A snake turn is 22 intervening PICKS but only 11 distinct rivals, each picking twice, and
    `estimate_survival` consults one board per pick -- so a rival's opinion is applied TWICE and
    agreement cannot be varied one pick at a time. Keying this fixture by pick would build
    boards under ids nobody looks up and quietly answer a different question.

    NO REAL BOARD IS BUILT: the property under test is what `estimate_survival` does with a set
    of ranks. That these ranks are what the real boards produce is measured separately and not
    assumed here (evidence/survival_mechanism/rank_agreement.json)."""
    deep = max(ds.RANK_TAKE_PROBABILITY) + 500
    return {str(r): {"by_id": {target: {}}, "rank_by_id": {target: rank if i < agreeing else deep},
                     "unpriced_ids": set()}
            for i, r in enumerate(rivals)}


class EveryRivalHoldsTheSameOpinion(unittest.TestCase):
    """#206's second half: the boards do not disagree, so survival has nothing to multiply but
    the same number. LIKE THE REST OF THIS FILE, A CHARACTERIZATION -- if these go red because
    rival boards started to differ, that is the repair landing, and the assertions get rewritten
    against the new model rather than restored."""

    TARGET = "9221"          # the engine's own #1 in the measured run; any id behaves the same
    TEAMS = 12

    def setUp(self):
        self.order = ds.generate_pick_order([str(i) for i in range(1, self.TEAMS + 1)], 2)
        nxt = ds.find_next_pick_index(self.order, "1", 0)
        self.picks = ds.intervening_roster_ids(self.order, 0, nxt)
        self.rivals = sorted(set(self.picks), key=int)

    def _survival(self, agreeing: int, rank: int = 1) -> float:
        boards = _boards(self.rivals, self.TARGET, agreeing, rank)
        return ds.estimate_survival([], {}, self.order, 0, "1", self.TARGET,
                                    boards, league=None)["survival_probability"]

    def test_the_turn_really_is_the_long_one_and_each_rival_is_consulted_twice(self):
        """Guards the fixture itself. If this shape ever changes, every number below is about a
        different turn and the ones that look unchanged would be the dangerous ones."""
        self.assertEqual(len(self.picks), 22)
        self.assertEqual(len(self.rivals), 11)
        self.assertTrue(all(self.picks.count(r) == 2 for r in self.rivals))

    def test_one_distinct_take_probability_across_every_intervening_pick(self):
        boards = _boards(self.rivals, self.TARGET, len(self.rivals))
        rows = ds.estimate_survival([], {}, self.order, 0, "1", self.TARGET,
                                    boards, league=None)["risk_by_team"]
        self.assertEqual(len(rows), 22)
        self.assertEqual({r["take_probability"] for r in rows}, {ds.RANK_TAKE_PROBABILITY[1]})

    def test_the_reported_zero_is_not_a_rounding_artifact(self):
        """0.00 invites the reading "small, but measured". It is seven orders below the 0.0005
        that would round there -- the difference between a low probability and an impossibility
        the model has no way to express."""
        self.assertEqual(self._survival(len(self.rivals)), 0.0)
        exact = (1 - ds.RANK_TAKE_PROBABILITY[1]) ** 22
        self.assertLess(exact, 1e-7)
        self.assertLess(exact * 1000, 0.0005)

    def test_a_single_agreeing_rival_already_costs_an_order_of_magnitude(self):
        """Agreement is superlinear, and this is the asymmetry that makes this half of #206 the
        hard one. ONE rival holding the top opinion -- 2 of the 22 picks -- takes survival from
        0.641 to 0.135; three take it to 0.006. A shared valuation supplies far more agreement
        than the collapse needs, so the collapse cannot be repaired by consulting fewer boards."""
        self.assertAlmostEqual(self._survival(0), 0.641, places=3)
        self.assertAlmostEqual(self._survival(1), 0.135, places=3)
        self.assertAlmostEqual(self._survival(2), 0.029, places=3)
        self.assertAlmostEqual(self._survival(3), 0.006, places=3)

    def test_no_amount_of_disagreement_reproduces_the_mass_normalised_answer(self):
        """The two candidate repairs on ONE scale, which is the whole point of measuring both.
        Renormalising the take mass -- arithmetic forced by "one team, one pick", a bound rather
        than a threshold (#56) -- gives 0.314 on this turn. Varying agreement cannot land there
        from either side: total disagreement overshoots at 0.641, and a single agreeing rival
        undershoots at 0.135, because a rival's opinion moves two picks at once. 0.314 is not a
        target to tune toward; it is the yardstick that shows these are different repairs, not
        two routes to one answer."""
        reachable = [self._survival(a) for a in range(len(self.rivals) + 1)]
        self.assertEqual(reachable, sorted(reachable, reverse=True))
        self.assertFalse(any(abs(v - 0.314) < 0.05 for v in reachable))
        above = [v for v in reachable if v > 0.314]
        self.assertEqual(above, [0.641])

    def test_the_collapse_needs_the_top_of_the_table_not_merely_a_ranked_row(self):
        """Rank 5 is still inside the table and still agreed on by everyone, and it does NOT
        reach zero. So "every board ranks him" is not sufficient on its own -- the defect is
        every board ranking him AT THE TOP, which is exactly what one shared valuation
        guarantees for the player the engine itself likes best."""
        deepest = max(ds.RANK_TAKE_PROBABILITY)
        self.assertGreater(self._survival(len(self.rivals), rank=deepest), 0.0)


if __name__ == "__main__":
    unittest.main()
