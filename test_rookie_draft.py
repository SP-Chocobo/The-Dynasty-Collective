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


if __name__ == "__main__":
    unittest.main()
