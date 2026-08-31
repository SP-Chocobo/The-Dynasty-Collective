"""
Covers rookie_draft.py's real-money invariants: worse records must produce earlier (more
valuable) slots, record signal must fade as the target draft gets further away, and the
whole pipeline must actually differentiate two teams with different records rather than
collapsing them to Draft Sharks' old flat per-round number.
"""

import unittest

import data_merger as dm
import rookie_draft as rd


class EstimatePickSlotTests(unittest.TestCase):
    def test_worse_record_produces_an_earlier_slot(self):
        worst = rd.estimate_pick_slot(wins=0, losses=10, ties=0, num_teams=12)
        best = rd.estimate_pick_slot(wins=10, losses=0, ties=0, num_teams=12)
        self.assertLess(worst, best)

    def test_undefeated_team_gets_the_last_slot(self):
        self.assertAlmostEqual(rd.estimate_pick_slot(10, 0, 0, 12), 12.0)

    def test_winless_team_gets_the_first_slot(self):
        self.assertAlmostEqual(rd.estimate_pick_slot(0, 10, 0, 12), 1.0)

    def test_no_games_played_yet_returns_the_middle_slot(self):
        self.assertAlmostEqual(rd.estimate_pick_slot(0, 0, 0, 12), 6.5)

    def test_ties_count_as_half_a_win(self):
        # 5-5-0 and 5-4-2 should land very close (5 wins + 1 tie-equivalent vs. 5 wins +
        # 1 real tie) -- ties shouldn't just be dropped or double-counted.
        a = rd.estimate_pick_slot(5, 5, 0, 12)
        b = rd.estimate_pick_slot(5, 4, 1, 12)
        self.assertAlmostEqual(a, b, delta=0.6)


class EstimateFuturePickValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_returns_none_without_a_loaded_trade_value_chart(self):
        empty_merger = dm.DataMerger.__new__(dm.DataMerger)
        import pandas as pd
        empty_merger.trade_values = pd.DataFrame(columns=["name", "value", "asset_type"])
        result = rd.estimate_future_pick_value(
            empty_merger, wins=0, losses=10, ties=0, num_teams=12, round_num=1, seasons_until_draft=0,
        )
        self.assertIsNone(result)

    def test_a_worse_team_this_years_pick_prices_higher_than_a_better_teams(self):
        worst = rd.estimate_future_pick_value(
            self.merger, wins=0, losses=10, ties=0, num_teams=12, round_num=1, seasons_until_draft=0,
        )
        best = rd.estimate_future_pick_value(
            self.merger, wins=10, losses=0, ties=0, num_teams=12, round_num=1, seasons_until_draft=0,
        )
        self.assertIsNotNone(worst)
        self.assertIsNotNone(best)
        self.assertGreater(worst["value"], best["value"])

    def test_record_signal_fades_the_further_out_the_draft_is(self):
        # Same record (worst possible), different distance from the actual draft -- the
        # record-based estimate must count for less the further out the target year is,
        # so the blended value should drift toward the flat generic price, not stay pinned
        # to the full record-based number regardless of how speculative that is.
        generic = 29.0  # matches Draft Sharks' real "2027 Random Rd 1" flat price in the baseline
        this_year = rd.estimate_future_pick_value(
            self.merger, wins=0, losses=10, ties=0, num_teams=12, round_num=1,
            seasons_until_draft=0, generic_future_value=generic,
        )
        far_out = rd.estimate_future_pick_value(
            self.merger, wins=0, losses=10, ties=0, num_teams=12, round_num=1,
            seasons_until_draft=3, generic_future_value=generic,
        )
        # This year's estimate (fully trusting a 0-10 record) should be far above the flat
        # generic price; three years out should sit much closer to it.
        self.assertGreater(this_year["value"], far_out["value"])
        self.assertLess(abs(far_out["value"] - generic), abs(this_year["value"] - generic))

    def test_flat_generic_price_is_untouched_when_no_generic_value_given(self):
        # Without a generic_future_value to blend toward, the estimate is pure record-based
        # regardless of distance -- there's nothing else honest to fall back on.
        result = rd.estimate_future_pick_value(
            self.merger, wins=0, losses=10, ties=0, num_teams=12, round_num=1, seasons_until_draft=3,
        )
        self.assertEqual(result["value"], result["record_based_value"])

    def test_real_baseline_produces_a_meaningfully_different_price_for_two_records(self):
        # End-to-end against the real committed baseline (not a synthetic fixture) -- the
        # actual bug this module fixes: Draft Sharks' own flat future-pick price treats a
        # last-place team's next 1st and a championship team's identically.
        worst = rd.estimate_future_pick_value(
            self.merger, wins=1, losses=11, ties=0, num_teams=12, round_num=1, seasons_until_draft=0,
        )
        best = rd.estimate_future_pick_value(
            self.merger, wins=11, losses=1, ties=0, num_teams=12, round_num=1, seasons_until_draft=0,
        )
        self.assertGreater(worst["value"] - best["value"], 15.0, "the two records should price meaningfully apart")


class ReachabilityAndKnownDefectsTests(unittest.TestCase):
    """CHARACTERIZATION, not approval. Each test below pins behaviour the audit measured and
    recorded as a DEFECT in rookie_draft.py's own module note. They exist so the defects are
    executable rather than only prose, and so that anyone who fixes one is forced to read the
    note: a failure here means somebody changed the primitive, which is fine -- delete the test
    that failed and update the module note in the same change.

    The tests above this class are all sound unit tests of the function AS WRITTEN. What the
    audit found is that they exercise it at seasons_until_draft=0 and 3, and production can
    reach neither: the current year's draft is priced by exact slot rather than as a flat
    future pick, and the vendor publishes no flat row three years out. See the last test here."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_DEFECT_sample_size_is_ignored_so_one_game_equals_a_whole_season(self):
        # 0-1 in week one and 0-14 after a full season are different amounts of evidence by a
        # factor of fourteen. estimate_pick_slot divides them into the same win percentage and
        # returns the same answer, so the valuation is at its most extreme on its thinnest
        # evidence. Only the zero-games case is special-cased.
        after_one_game = rd.estimate_pick_slot(wins=0, losses=1, ties=0, num_teams=12)
        after_a_season = rd.estimate_pick_slot(wins=0, losses=14, ties=0, num_teams=12)
        self.assertEqual(after_one_game, after_a_season)
        self.assertAlmostEqual(after_one_game, 1.0)
        # And it propagates all the way to the price, identically.
        one = rd.estimate_future_pick_value(
            self.merger, 0, 1, 0, 12, 1, 1, generic_future_value=29.0)
        season = rd.estimate_future_pick_value(
            self.merger, 0, 14, 0, 12, 1, 1, generic_future_value=29.0)
        self.assertEqual(one["value"], season["value"])

    def test_DEFECT_slot_is_ordinal_but_is_computed_cardinally_without_the_league(self):
        # A rookie draft slot is reverse order of finish AMONG THIS LEAGUE'S TEAMS -- exactly
        # one team gets 1.01 no matter what the records look like. estimate_pick_slot maps a
        # team's own win percentage onto 1..num_teams in isolation, so in a league with no
        # extreme records it puts everybody near the middle and finds nobody's real slot.
        #
        # This league is legal and unremarkable: four teams at 5-9, four at 7-7, four at 9-5.
        # Its worst teams hold 1.01 through 1.04 and are worth 83/40/36/33.
        worst_record_in_this_league = rd.estimate_pick_slot(
            wins=5, losses=9, ties=0, num_teams=12)
        self.assertGreater(
            worst_record_in_this_league, 4.0,
            "if this now returns ~1.0 the primitive has been made league-relative -- good; "
            "delete this test and update rookie_draft.py's module note")
        # The population it would need is already available to the app.
        import league_standings
        rosters = [{"roster_id": i, "settings": {"wins": w, "losses": 14 - w}}
                   for i, w in enumerate([5, 5, 5, 5, 7, 7, 7, 7, 9, 9, 9, 9], start=1)]
        standings = league_standings.team_standings(rosters, {})
        self.assertEqual(len(standings), 12)
        self.assertEqual(min(r["wins"] for r in standings), 5,
                         "team_standings already returns every roster's record; the primitive "
                         "simply never asks for it")

    def test_the_existing_suite_only_exercises_distances_production_cannot_reach(self):
        """The reachability result, pinned. A flat future-pick price is the ONLY thing this
        primitive can improve on, and the vendor publishes one only one and two seasons out."""
        import datetime
        year = datetime.date.today().year
        flat_by_distance = {
            yrs: self.merger.pick_value(f"{year + yrs} Random Rd 1") for yrs in range(0, 4)
        }
        reachable = sorted(y for y, v in flat_by_distance.items() if v is not None)
        self.assertTrue(reachable, "no flat future-pick row at any distance -- the baseline "
                                   "this test reasons about is missing, so it would prove "
                                   "nothing; failing instead")
        self.assertNotIn(0, reachable,
                         "distance 0 now has a flat row; the current-year draft used to be "
                         "priced by exact slot instead, which is what made the estimator "
                         "unnecessary there")
        # The current year IS priced, exactly, slot by slot -- no estimate required.
        self.assertIsNotNone(self.merger.pick_value("1.01"))
        self.assertIsNotNone(self.merger.pick_value("1.12"))
        # And at the reachable distances the module's own headline claim does not hold: the
        # test above asserts a >15.0 spread between 1-11 and 11-1, measured at distance 0.
        for yrs in reachable:
            flat = flat_by_distance[yrs]
            worst = rd.estimate_future_pick_value(
                self.merger, 1, 11, 0, 12, 1, yrs, generic_future_value=flat)
            best = rd.estimate_future_pick_value(
                self.merger, 11, 1, 0, 12, 1, yrs, generic_future_value=flat)
            self.assertLess(
                worst["value"] - best["value"], 15.0,
                f"at {yrs} season(s) out the spread now clears the 15.0 materiality bar the "
                f"suite above uses; re-run the reach measurement before trusting it")


if __name__ == "__main__":
    unittest.main()
