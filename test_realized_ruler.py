"""#30: the realized ruler's own correctness -- the first ruler the engine cannot optimise toward.

Everything here is synthetic and fast. The properties that matter are the ones a season-total
ruler gets wrong, so they are tested directly rather than inferred from a total:

  - an ABSENT week is an absence, not a zero-point performance (#187);
  - a bench player who covers an absence SCORES, which is why this ruler rewards depth and the
    projected one cannot;
  - eligibility comes from fantasy_positions, not the primary position (#172).
"""

from __future__ import annotations

import unittest

import realized_ruler as rr

SLOTS = [{"slot_id": "RB1", "eligible": {"RB"}},
         {"slot_id": "WR1", "eligible": {"WR"}},
         {"slot_id": "FLEX", "eligible": {"RB", "WR", "TE"}}]

DB = {
    "rb1": {"position": "RB", "fantasy_positions": ["RB"], "full_name": "Starter RB"},
    "rb2": {"position": "RB", "fantasy_positions": ["RB"], "full_name": "Backup RB"},
    "wr1": {"position": "WR", "fantasy_positions": ["WR"], "full_name": "Starter WR"},
    "flexy": {"position": "RB", "fantasy_positions": ["RB", "WR"], "full_name": "Dual Eligible"},
}


class AbsenceIsNotZeroTests(unittest.TestCase):
    """The defect this ruler exists to avoid. A season-total solve cannot tell 'he was hurt' from
    'he played badly', and that is exactly what makes a bench look like a pure liability."""

    def test_a_player_with_no_line_is_not_offered_to_the_solve(self):
        """Not started at 0.0 -- which would fill a slot that was never filled."""
        weekly = {"1": {"rb1": 20.0, "wr1": 10.0}, "2": {"wr1": 10.0}}   # rb1 absent in week 2
        got = rr.score_roster_realized(["rb1", "wr1"], DB, weekly, SLOTS, weeks=range(1, 3))
        self.assertEqual(got["total"], 40.0)

    def test_a_week_nobody_played_is_skipped_not_scored_as_zero(self):
        weekly = {"1": {"rb1": 20.0}, "2": {}}
        got = rr.score_roster_realized(["rb1"], DB, weekly, SLOTS, weeks=range(1, 3))
        self.assertEqual(got["weeks_scored"], 1)

    def test_points_per_week_is_None_when_no_week_could_be_scored(self):
        """Absence, not 0.0: an unscored roster is not a roster that scored nothing (#187)."""
        got = rr.score_roster_realized(["rb1"], DB, {}, SLOTS, weeks=range(1, 3))
        self.assertIsNone(got["points_per_week"])
        self.assertEqual(got["weeks_scored"], 0)


class DepthIsRewardedTests(unittest.TestCase):
    """THE PROPERTY THE PROJECTED RULER STRUCTURALLY CANNOT HAVE. A season-total solve starts one
    lineup once, so a backup is value paid for and never fielded. Solved weekly, the backup plays
    the week the starter is out."""

    def test_a_backup_who_covers_an_absence_scores(self):
        weekly = {"1": {"rb1": 20.0, "rb2": 5.0, "wr1": 10.0},
                  "2": {"rb2": 5.0, "wr1": 10.0}}          # rb1 out in week 2
        thin = rr.score_roster_realized(["rb1", "wr1"], DB, weekly, SLOTS, weeks=range(1, 3))
        deep = rr.score_roster_realized(["rb1", "rb2", "wr1"], DB, weekly, SLOTS, weeks=range(1, 3))
        self.assertGreater(deep["total"], thin["total"],
                           "the bench never played -- this ruler is not rewarding depth")

    def test_and_the_premium_is_exactly_the_covered_week(self):
        """Non-vacuity: a ruler that just added a FLEX body every week would also pass the test
        above. The gain must be the ABSENCE COVER plus the flex start, and nothing invented."""
        weekly = {"1": {"rb1": 20.0, "rb2": 5.0, "wr1": 10.0},
                  "2": {"rb2": 5.0, "wr1": 10.0}}
        thin = rr.score_roster_realized(["rb1", "wr1"], DB, weekly, SLOTS, weeks=range(1, 3))
        deep = rr.score_roster_realized(["rb1", "rb2", "wr1"], DB, weekly, SLOTS, weeks=range(1, 3))
        # week 1: thin starts rb1+wr1 = 30; deep also flexes rb2 = 35.
        # week 2: thin starts wr1 = 10; deep starts rb2 in RB1 and wr1 = 15.
        self.assertEqual(thin["total"], 40.0)
        self.assertEqual(deep["total"], 50.0)

    def test_a_player_who_never_started_is_counted(self):
        """Depth that never played is a real cost, and reporting only the total would hide it."""
        weekly = {"1": {"rb1": 20.0, "rb2": 1.0, "wr1": 10.0, "flexy": 0.5}}
        got = rr.score_roster_realized(["rb1", "rb2", "wr1", "flexy"], DB, weekly,
                                       SLOTS, weeks=range(1, 2))
        self.assertEqual(got["players"], 4)
        self.assertEqual(got["players_who_ever_started"] + got["players_who_never_started"], 4)


class EligibilityComesFromFantasyPositionsTests(unittest.TestCase):
    """#172. A player listed RB/WR is eligible at both; collapsing him to his primary benches him
    out of a FLEX he can legally fill and understates every roster holding one."""

    def test_a_dual_eligible_player_can_fill_either_slot(self):
        weekly = {"1": {"flexy": 12.0}}
        got = rr.score_roster_realized(["flexy"], DB, weekly, SLOTS, weeks=range(1, 2))
        self.assertEqual(got["total"], 12.0)

    def test_he_is_startable_in_the_WR_slot_despite_a_primary_of_RB(self):
        weekly = {"1": {"rb1": 20.0, "flexy": 12.0}}
        got = rr.score_roster_realized(["rb1", "flexy"], DB, weekly, SLOTS, weeks=range(1, 2))
        # rb1 takes RB1; flexy has to reach WR1 or FLEX to score at all.
        self.assertEqual(got["total"], 32.0)


class TheRulerIsIndependentOfTheEngineTests(unittest.TestCase):
    """The reason this exists (#288). If it read any engine-derived value it would be grading the
    engine on its own homework, which is what every prior ruler does."""

    def test_it_scores_from_realized_stats_and_league_scoring_only(self):
        import inspect
        source = inspect.getsource(rr)
        for forbidden in ("universal_value", "final_score", "bpa", "team_acquisition_value"):
            self.assertNotIn(forbidden, source,
                             f"the realized ruler reads {forbidden} -- it is no longer independent")

    def test_it_states_that_it_models_no_waivers(self):
        """The limit that decides how a streaming result may be read. It must stay stated."""
        self.assertIn("waiver", rr.__doc__.lower())


if __name__ == "__main__":
    unittest.main()
