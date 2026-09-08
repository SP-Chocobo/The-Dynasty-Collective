"""Guards on the #205 roster-proof instrument itself -- the harness, not the engine.

WHY AN INSTRUMENT GETS TESTS. Both defects in this harness's first draft were invisible to
reading and obvious to running: a control that took 24 consecutive QBs, and a ruler that was
the engine's own objective function. Neither crashed. Both produced confident numbers about a
different question, which is this project's named failure mode. #177's harness had no tests and
no commit, and its result now cannot be defended (#208). These are the tests that would have
caught both before the numbers were quoted.

MUTATION-CHECKED. Every test below was confirmed to FAIL against a deliberate re-introduction
of the defect it describes; the survivors are recorded at the bottom of this file.
"""

from __future__ import annotations

import inspect
import unittest

import run_roster_proof as rp


def _db(**positions):
    """A players_db of {player_id: {"position", "fantasy_positions"}} from pid->pos kwargs."""
    return {pid: {"position": pos, "fantasy_positions": [pos]} for pid, pos in positions.items()}


ONE_QB_SLOTS = [
    {"slot_id": "QB_0", "label": "QB", "eligible": {"QB"}},
    {"slot_id": "RB_1", "label": "RB", "eligible": {"RB"}},
    {"slot_id": "WR_2", "label": "WR", "eligible": {"WR"}},
]


class ControlIsSomebodySomeoneWouldPlayTests(unittest.TestCase):
    """The strawman that produced +503%: a projection ranking with no idea what a lineup is."""

    def test_the_control_does_not_take_a_second_qb_while_rb_and_wr_sit_empty(self):
        # QBs out-project everyone, which is exactly why the naive rule took 24 of them.
        db = _db(qb1="QB", qb2="QB", rb1="RB", wr1="WR")
        points = {"qb1": 380.0, "qb2": 340.0, "rb1": 210.0, "wr1": 200.0}
        chosen = rp.control_pick(["qb2", "rb1", "wr1"], points, ["qb1"], db, ONE_QB_SLOTS)
        self.assertNotEqual(chosen, "qb2",
                            "the control took a second QB with its RB and WR slots empty -- "
                            "this is the strawman that made the engine look +503% better")
        self.assertEqual(chosen, "rb1", "should take the best projection at an unfilled slot")

    def test_the_control_still_ranks_by_projection_within_what_it_needs(self):
        db = _db(rb1="RB", rb2="RB", wr1="WR")
        points = {"rb1": 150.0, "rb2": 260.0, "wr1": 200.0}
        # Both RB and WR slots are open; rb2 is the best projection among eligible fills.
        self.assertEqual(rp.control_pick(["rb1", "rb2", "wr1"], points, [], db, ONE_QB_SLOTS),
                         "rb2")

    def test_once_every_starting_slot_is_covered_the_control_takes_best_available(self):
        db = _db(qb1="QB", rb1="RB", wr1="WR", qb2="QB", rb2="RB")
        points = {"qb1": 380.0, "rb1": 210.0, "wr1": 200.0, "qb2": 340.0, "rb2": 100.0}
        chosen = rp.control_pick(["qb2", "rb2"], points, ["qb1", "rb1", "wr1"], db, ONE_QB_SLOTS)
        self.assertEqual(chosen, "qb2",
                         "with the lineup covered, depth by projection is the honest baseline")

    def test_unmet_slots_is_empty_exactly_when_the_lineup_is_covered(self):
        db = _db(qb1="QB", rb1="RB", wr1="WR")
        self.assertEqual(
            rp.unmet_slot_positions(["qb1", "rb1", "wr1"], db, ONE_QB_SLOTS), set())
        self.assertEqual(
            rp.unmet_slot_positions(["qb1"], db, ONE_QB_SLOTS), {"RB", "WR"})
        self.assertEqual(
            rp.unmet_slot_positions([], db, ONE_QB_SLOTS), {"QB", "RB", "WR"})

    def test_a_multi_position_player_covers_a_slot_only_his_SECONDARY_position_can_fill(self):
        """#172, and the case that actually discriminates.

        The first version of this test put an RB/WR against separate RB and WR slots -- where
        he fills exactly one slot whether or not his second eligibility is seen, so collapsing
        eligibility to the primary position gave the identical answer and the test passed a
        mutation that broke the code. It survived the mutation pass and is rewritten here.

        The discriminating shape is a player whose PRIMARY position has no slot at all and
        whose SECONDARY position does: seen properly he covers the lineup, collapsed he is
        invisible and the slot reads as unmet.
        """
        wr_only = [{"slot_id": "WR_0", "label": "WR", "eligible": {"WR"}}]
        db = {"flexy": {"position": "RB", "fantasy_positions": ["RB", "WR"]}}
        self.assertEqual(rp.unmet_slot_positions(["flexy"], db, wr_only), set(),
                         "an RB/WR covers a WR slot; reading only his primary hides that")

    def test_a_multi_position_player_is_started_in_a_slot_only_his_SECONDARY_fills(self):
        """The same collapse in score_roster's own solve, which is a separate code path."""
        wr_only = [{"slot_id": "WR_0", "label": "WR", "eligible": {"WR"}}]
        db = {"flexy": {"position": "RB", "fantasy_positions": ["RB", "WR"]}}
        picks = [{"roster_id": "1", "player_id": "flexy"}]
        out = rp.score_roster(picks, "1", db, {"cdme": {"flexy": 9.0},
                                               "points": {"flexy": 90.0}}, wr_only)
        self.assertEqual(out["cdme"]["starter_value"], 9.0,
                         "he must be startable at WR, not benched at a value of zero")
        self.assertEqual(out["cdme"]["starters_filled"], 1)


class TwoRulersNeverCollapsedTests(unittest.TestCase):
    """Scoring on one ruler hands the win to whoever optimises it."""

    def test_more_than_one_ruler_exists(self):
        self.assertGreater(len(rp.RULERS), 1,
                           "a single ruler is the engine grading its own objective")

    def test_the_engines_objective_is_not_the_only_ruler(self):
        self.assertIn("cdme", rp.RULERS)
        self.assertIn("points", rp.RULERS,
                      "the control's own objective must be one of the rulers, or a win on "
                      "cdme alone reads as a result instead of a tautology")

    def test_score_roster_reports_every_ruler_separately(self):
        db = _db(rb1="RB", wr1="WR")
        picks = [{"roster_id": "1", "player_id": "rb1"},
                 {"roster_id": "1", "player_id": "wr1"}]
        rulers = {"cdme": {"rb1": 10.0, "wr1": 5.0}, "points": {"rb1": 100.0, "wr1": 250.0}}
        out = rp.score_roster(picks, "1", db, rulers, ONE_QB_SLOTS)
        self.assertEqual(out["cdme"]["starter_value"], 15.0)
        self.assertEqual(out["points"]["starter_value"], 350.0)
        self.assertNotEqual(out["cdme"]["starter_value"], out["points"]["starter_value"],
                            "the two rulers must be able to disagree, or they are one ruler")

    def test_the_harness_emits_no_single_collapsed_verdict(self):
        """A one-number answer would silently pick a ruler, and the pick would be invisible."""
        src = inspect.getsource(rp.main)
        self.assertIn("for name in RULERS", src)
        self.assertNotIn("overall_win_rate", src)
        self.assertNotIn("engine_is_better", src)


class ARulerIsComparedOnAQuantityItCanCarryTests(unittest.TestCase):
    """The category error that inverted the first full-depth run from +176% to -171.7%."""

    def test_the_optimizer_is_forced_to_start_a_negative_player(self):
        """The premise. If this ever stops being true, COMPARE_ON's reasoning is void."""
        import lineup_optimizer as lo
        slots = [{"slot_id": "RB_0", "eligible": {"RB"}}, {"slot_id": "WR_1", "eligible": {"WR"}}]
        solved = lo.optimize_lineup(
            [{"id": "goodwr", "value": 50.0, "eligible": {"WR"}},
             {"id": "badrb", "value": -80.0, "eligible": {"RB"}}], slots)
        self.assertEqual(solved["total_value"], -30.0,
                         "the solver has no 'leave it empty' move -- it starts the -80 rather "
                         "than skipping the slot, so a starting-lineup SUM can go negative")

    def test_cdme_is_not_compared_on_a_starting_lineup_sum(self):
        """universal_value is an asset LEVEL, not a rate that starting a player realises."""
        self.assertEqual(rp.COMPARE_ON["cdme"], "total_value")
        self.assertNotEqual(rp.COMPARE_ON["cdme"], "starter_value")

    def test_points_IS_compared_on_the_starting_lineup(self):
        """Projected points is exactly the quantity a lineup realises -- here the sum is right."""
        self.assertEqual(rp.COMPARE_ON["points"], "starter_value")

    def test_every_ruler_has_a_declared_quantity(self):
        for name in rp.RULERS:
            self.assertIn(name, rp.COMPARE_ON,
                          "a ruler with no declared quantity would silently take a default")

    def test_no_percentage_is_reported_against_a_near_zero_denominator(self):
        """(eng - ctl)/|ctl| manufactures a huge number from a tiny gap when ctl approaches 0."""
        runs = [{"engine_seat": "1",
                 "engine": {"cdme": {"total_value": -0.4}},
                 "controls": [{"cdme": {"total_value": 0.0001}}]}]
        out = rp.compare(runs, "cdme")
        self.assertEqual(out["comparable_runs"], 1, "the run itself is still comparable")
        self.assertEqual(out["advantage_population"], 0,
                         "but no ratio may be quoted against that denominator")
        self.assertIsNone(out["mean_advantage_pct"])
        self.assertIsNotNone(out["mean_gap"], "the ABSOLUTE gap is always reportable")

    def test_the_absolute_numbers_are_always_present(self):
        """A percentage must never be the only number on offer."""
        runs = [{"engine_seat": "1",
                 "engine": {"points": {"starter_value": 120.0}},
                 "controls": [{"points": {"starter_value": 100.0}}]}]
        out = rp.compare(runs, "points")
        self.assertEqual(out["engine_mean"], 120.0)
        self.assertEqual(out["control_mean"], 100.0)
        self.assertEqual(out["mean_gap"], 20.0)
        self.assertEqual(out["compared_on"], "starter_value")


class APartialRunIsStillReadableTests(unittest.TestCase):

    def test_the_report_is_written_after_every_format_not_once_at_the_end(self):
        src = inspect.getsource(rp.main)
        self.assertIn("complete=False", src,
                      "a 45-minute run that writes only on its last line reproduces exactly "
                      "the durability hole this item exists to close")
        self.assertIn("complete=True", src)

    def test_a_partial_report_says_it_is_partial(self):
        src = inspect.getsource(rp._write_report)
        self.assertIn('"complete": complete', src)
        self.assertIn('"formats_done"', src,
                      "a reader must be able to tell a partial file from a finished one")

    def test_the_known_contamination_travels_in_the_report(self):
        src = inspect.getsource(rp._write_report)
        self.assertIn("known_contamination", src,
                      "the cdme total sums below-replacement negatives (#155/#165, reserved); "
                      "a report that omits that reads as a clean roster-worth number")


class AbsenceIsCountedNotImputedTests(unittest.TestCase):

    def test_an_unpriced_player_is_counted_per_ruler_and_never_becomes_a_measured_zero(self):
        db = _db(rb1="RB", wr1="WR")
        picks = [{"roster_id": "1", "player_id": "rb1"},
                 {"roster_id": "1", "player_id": "wr1"}]
        # Priced under points, unpriced under cdme -- the IDP-shaped case.
        rulers = {"cdme": {"rb1": 10.0}, "points": {"rb1": 100.0, "wr1": 250.0}}
        out = rp.score_roster(picks, "1", db, rulers, ONE_QB_SLOTS)
        self.assertEqual(out["cdme"]["unpriced"], 1)
        self.assertFalse(out["cdme"]["values_are_totals"],
                         "with a player unpriced the totals are floors and must say so")
        self.assertEqual(out["points"]["unpriced"], 0)
        self.assertTrue(out["points"]["values_are_totals"])

    def test_a_measured_zero_is_not_reported_as_absence(self):
        """`is not None` and `> 0` are different questions -- rule 5, in the instrument."""
        db = _db(rb1="RB")
        picks = [{"roster_id": "1", "player_id": "rb1"}]
        out = rp.score_roster(picks, "1", db, {"cdme": {"rb1": 0.0}, "points": {"rb1": 0.0}},
                              ONE_QB_SLOTS)
        self.assertEqual(out["cdme"]["unpriced"], 0,
                         "a player priced at exactly 0.0 was measured, not missing")
        self.assertTrue(out["cdme"]["values_are_totals"])

    def test_compare_never_quotes_a_rate_over_runs_it_could_not_evaluate(self):
        runs = [{"engine_seat": "1",
                 "engine": {"cdme": {"total_value": 100.0}},
                 "controls": [{"cdme": {"total_value": None}}]}]
        out = rp.compare(runs, "cdme")
        self.assertEqual(out["comparable_runs"], 0)
        self.assertIsNone(out["win_rate"], "a rate over an empty set is not a rate")

    def test_compare_counts_a_win_against_the_mean_of_the_controls_actually_faced(self):
        runs = [{"engine_seat": "1",
                 "engine": {"cdme": {"total_value": 120.0}},
                 "controls": [{"cdme": {"total_value": 100.0}},
                              {"cdme": {"total_value": 100.0}}]}]
        out = rp.compare(runs, "cdme")
        self.assertEqual(out["comparable_runs"], 1)
        self.assertEqual(out["engine_wins"], 1)
        self.assertAlmostEqual(out["mean_advantage_pct"], 20.0)


class RoundCountIsDerivedTests(unittest.TestCase):

    def test_the_round_count_defaults_to_derivation_not_a_hand_set_number(self):
        """A hand-set count is a second source of truth about roster size. The old default of
        15 drafted a 15th player into this repo's 14-slot mock roster."""
        src = inspect.getsource(rp.main)
        self.assertIn('ap.add_argument("--rounds", type=int, default=0)', src)
        self.assertIn('args.rounds or len(league.get("roster_positions")', src)

    def test_the_report_records_which_depth_was_actually_drafted(self):
        src = inspect.getsource(rp.main)
        self.assertIn('"rounds": rounds', src)
        self.assertIn('"roster_slots"', src,
                      "a reader must be able to see a short run for what it is -- at 8 of 14 "
                      "the points ruler measured front-loading, not roster quality")


# MUTATION PASS: 7 mutations, 6 caught on the first attempt, 1 SURVIVOR found and closed.
#
#   M1 naive projection-only control_pick ................................ caught
#   M2 RULERS reduced to ("cdme",) ....................................... caught
#   M3 measured 0.0 folded into absence (`if not values.get(pid)`) ....... caught
#   M4 compare() imputing 0.0 for a None control ......................... caught
#   M5 --rounds default restored to 15 ................................... caught
#   M6a eligibility collapsed to primary in unmet_slot_positions ......... SURVIVED, now caught
#   M6b eligibility collapsed to primary in score_roster's solve ......... caught after rewrite
#
# THE SURVIVOR IS THE INTERESTING ONE and it is recorded rather than quietly fixed. The first
# #172 test placed an RB/WR against SEPARATE RB and WR slots -- where he fills exactly one slot
# whether or not his second eligibility is read, so collapsing eligibility to the primary
# position produced the identical answer and the test passed against broken code. A test can be
# about the right subject and still measure nothing; the shape that discriminates is a player
# whose primary position has no slot at all. Both eligibility sites are separate code paths and
# are now mutated separately, because catching one said nothing about the other.

if __name__ == "__main__":
    unittest.main()
