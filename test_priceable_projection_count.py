"""#212: a supplied projection is not a priceable one, and reporting only the first overstates
coverage by 6.4x.

Measured: of 5,346 entries in the season-projection capture, 4,506 carry ONLY an ADP field --
usually `adp_dd_ppr: 18000.0`, the "undrafted" sentinel -- and no stat line whatsoever. ADP says
where the market drafted a player, not what he is projected to DO, so nothing downstream can
turn it into points. `season_projections_supplied: 5346` sat in a committed evidence file
reading as "5,346 players are priced by Sleeper"; the real figure is 840.

This is what actually explains #209 and #210, and it makes them ONE finding rather than two:
  #209  Jake Haener, taken at 14.02 with tav=None, has an entry -- `{'adp_dd_ppr': 18000.0}`.
        The scoring path REACHED him (my pre-registered falsifier said it had not, and was
        wrong); there was simply nothing in the entry to price. The board says
        bpa_source='no_priceable_input', which is the absence contract working.
  #210  1,817 of the ADP-only entries are IDP (LB 852, DB 723, DL 242). HEAVY_IDP did not shrink
        because Sleeper supplies those players without stats, not because it lacks them.
"""

from __future__ import annotations

import unittest

import run_draft_battery as rdb


class ADPIsNotAStatTests(unittest.TestCase):

    def test_an_adp_only_entry_is_not_priceable(self):
        """Jake Haener's actual entry, verbatim from the capture."""
        self.assertEqual(rdb.priceable_projection_count({"10215": {"adp_dd_ppr": 18000.0}}), 0)

    def test_the_positional_adp_field_is_also_not_a_stat(self):
        self.assertEqual(rdb.priceable_projection_count(
            {"x": {"adp_dd_ppr": 120.0, "pos_adp_dd_ppr": 14.0}}), 0)

    def test_a_real_stat_line_is_priceable(self):
        self.assertEqual(rdb.priceable_projection_count({"x": {"pass_yd": 4200.0}}), 1)

    def test_a_stat_line_alongside_adp_is_still_priceable(self):
        """ADP does not disqualify an entry -- only being ADP-ONLY does."""
        self.assertEqual(rdb.priceable_projection_count(
            {"x": {"adp_dd_ppr": 12.0, "rush_yd": 900.0}}), 1)

    def test_an_all_zero_stat_line_is_not_priceable(self):
        self.assertEqual(rdb.priceable_projection_count({"x": {"pass_yd": 0.0, "rec_yd": 0}}), 0)

    def test_empty_and_missing_entries_do_not_crash_or_count(self):
        self.assertEqual(rdb.priceable_projection_count({"a": {}, "b": None}), 0)
        self.assertEqual(rdb.priceable_projection_count({}), 0)
        self.assertEqual(rdb.priceable_projection_count(None), 0)

    def test_the_stat_names_are_not_hand_listed(self):
        """#126. A new Sleeper stat must count the day it appears, not the day someone
        remembers to add it to an allowlist here."""
        self.assertEqual(rdb.priceable_projection_count(
            {"x": {"some_stat_invented_next_season": 12.0}}), 1)


class AgainstTheRealCaptureTests(unittest.TestCase):

    def test_priceable_is_far_below_supplied_and_both_are_reported(self):
        season = rdb.season_projections_from_capture()
        priceable = rdb.priceable_projection_count(season)
        self.assertGreater(len(season), priceable,
                           "if these ever match, the ADP-only population is gone and this "
                           "test should be re-derived rather than deleted")
        self.assertGreater(priceable, 0, "a rate over an empty set is not a rate")
        # Pinned to the committed capture. A change here is a change in the INPUT and must be
        # read as one, not smoothed over.
        self.assertEqual(len(season), 5346)
        self.assertEqual(priceable, 840)

    def test_the_universe_block_carries_both_numbers(self):
        import inspect
        src = inspect.getsource(rdb.main)
        self.assertIn("season_projections_supplied", src)
        self.assertIn("season_projections_priceable", src,
                      "supplied alone reads as a coverage claim the data does not support")


if __name__ == "__main__":
    unittest.main()
