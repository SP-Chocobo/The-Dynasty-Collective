"""#180: does this league's OWN scoring reach an offensive player's price?

THE DEFECT THIS DEFENDS AGAINST. `_derive_points_and_source` used to select the league-scored
number with `no_ds_proj & has_sleeper` -- only where the vendor had NO projection. The vendor
projects every offensive player, so that mask was False for all of them and a number computed
correctly under the league's own scoring keys was discarded one line later. IDP/K/DST appeared
to route through scoring only because the vendor does not cover them. Measured against the
owner's real league before the repair: 390 of 391 offensive players (99.7%) priced from a total
their league's scoring cannot express, with 57 of 64 keys unreachable.

WHY THESE TESTS ARE SHAPED LIKE THIS. A routing repair has a specific, nasty failure mode: it
can look finished while still using the old path, because the numbers do not change and the
suite stays green. So none of these assert "a function was called". Each one plants a scoring
difference that CANNOT be produced by the old path and requires it to appear in the price, and
the mutation notes on each record which reverted defect it was proven to catch.
"""
from __future__ import annotations

import unittest

import pandas as pd

import draft_room as dr


class _Merger:
    """The narrowest thing build_available_pool actually consumes: merge_player, plus the
    frames the anchor fingerprint reads. Deliberately not a DataMerger -- a real one loads the
    committed baseline, and this test is about the SCORING path, not the join."""

    def __init__(self, vendor_points: float | None):
        self._vendor = vendor_points
        self.projections = pd.DataFrame()
        self.trade_values = pd.DataFrame()
        self.external_values = pd.DataFrame()
        self.free_agents = pd.DataFrame()

    def merge_player(self, name, position=None, team=None):
        return {
            "matched": True,
            "trade_value": 100.0,
            "projection": self._vendor,
            "proj_3yr": None,
            "source_file": "vendor.csv",
            "match_canonical_key": f"key::{name}",
            "match_path": "exact",
            "match_verified": True,
        }


PLAYERS = {"p1": {"first_name": "Test", "last_name": "Receiver", "position": "WR", "team": "KC"}}

#: One receiving line. Under a league that pays per reception this is worth a great deal more
#: than under one that does not -- that gap is the whole instrument.
SEASON_STATS = {"p1": {"rec": 100.0, "rec_yd": 1200.0, "rec_td": 8.0}}

PPR = {"rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0}
STANDARD = {"rec": 0.0, "rec_yd": 0.1, "rec_td": 6.0}


def _pool(vendor_points, stats, scoring, basis):
    return dr.build_available_pool(
        _Merger(vendor_points), PLAYERS, set(), {"WR"},
        sleeper_projections=stats, scoring_settings=scoring, sleeper_basis=basis,
    )


class ScoringReachesOffencePriceTests(unittest.TestCase):

    def test_a_season_scored_offensive_player_is_priced_from_the_league_scoring(self):
        """THE HEADLINE. The vendor has a projection AND the league-scored season total exists;
        the league-scored one must win. Under the old mask this was impossible by construction.

        Mutation proven to fail this: restoring `use_season = has_sleeper & no_ds_proj`.
        """
        pool = _pool(150.0, SEASON_STATS, PPR, dr.SLEEPER_BASIS_SEASON_SUM)
        dr._derive_points_and_source(pool)
        expected = 100.0 * 1.0 + 1200.0 * 0.1 + 8.0 * 6.0     # 268.0 under this league's keys
        self.assertAlmostEqual(pool["_points"].iloc[0], expected)
        self.assertEqual(pool["bpa_source"].iloc[0], "points_vor_sleeper_season_scored")

    def test_changing_only_the_leagues_scoring_changes_the_price(self):
        """The propagation claim itself, isolated: same player, same stats, same vendor number,
        one scoring key different. If the price does not move, scoring does not reach it."""
        ppr = _pool(150.0, SEASON_STATS, PPR, dr.SLEEPER_BASIS_SEASON_SUM)
        std = _pool(150.0, SEASON_STATS, STANDARD, dr.SLEEPER_BASIS_SEASON_SUM)
        dr._derive_points_and_source(ppr)
        dr._derive_points_and_source(std)
        self.assertNotEqual(ppr["_points"].iloc[0], std["_points"].iloc[0])
        # 100 receptions at 1.0 vs 0.0 -- the difference must be exactly the reception points,
        # not merely "different", or something else moved too.
        self.assertAlmostEqual(ppr["_points"].iloc[0] - std["_points"].iloc[0], 100.0)

    def test_a_season_total_is_never_multiplied_by_the_weekly_factor(self):
        """SLEEPER_WEEKLY_TO_SEASON_FACTOR applies to ONE WEEK. Applying it to a season sum
        would inflate every price 17x, and the symptom would read as a calibration problem
        rather than a unit error.

        Mutation proven to fail this: multiplying the season branch by the factor.
        """
        pool = _pool(None, SEASON_STATS, PPR, dr.SLEEPER_BASIS_SEASON_SUM)
        dr._derive_points_and_source(pool)
        self.assertAlmostEqual(pool["_points"].iloc[0], 268.0)
        self.assertNotAlmostEqual(pool["_points"].iloc[0], 268.0 * dr.SLEEPER_WEEKLY_TO_SEASON_FACTOR)

    def test_the_weekly_basis_keeps_its_old_narrower_role(self):
        """A weekly figure is NOT promoted over the vendor -- it still only fills a gap, and it
        is still scaled. Changing the season path must not quietly change this one."""
        with_vendor = _pool(150.0, SEASON_STATS, PPR, dr.SLEEPER_BASIS_WEEKLY)
        dr._derive_points_and_source(with_vendor)
        self.assertAlmostEqual(with_vendor["_points"].iloc[0], 150.0)      # vendor still wins
        self.assertEqual(with_vendor["bpa_source"].iloc[0], "points_vor_draftsharks")

        no_vendor = _pool(None, SEASON_STATS, PPR, dr.SLEEPER_BASIS_WEEKLY)
        dr._derive_points_and_source(no_vendor)
        self.assertAlmostEqual(no_vendor["_points"].iloc[0], 268.0 * dr.SLEEPER_WEEKLY_TO_SEASON_FACTOR)
        self.assertEqual(no_vendor["bpa_source"].iloc[0], "points_vor_sleeper_extrapolated")

    def test_the_offline_path_is_untouched(self):
        """THE INVARIANT. With no live sync there is no sleeper_points, so nothing in this
        repair may reach the number. Offline, rec/bonus_rec_te still propagate by FILE
        SELECTION, which this does not alter."""
        pool = _pool(150.0, None, None, dr.SLEEPER_BASIS_SEASON_SUM)
        dr._derive_points_and_source(pool)
        self.assertAlmostEqual(pool["_points"].iloc[0], 150.0)
        self.assertEqual(pool["bpa_source"].iloc[0], "points_vor_draftsharks")
        self.assertIsNone(pool["sleeper_basis"].iloc[0])

    def test_the_basis_travels_with_the_number_and_is_absent_when_it_is(self):
        """#166/#174's lesson applied before it bites: a quantity must not cross a layer
        without the companion that gives it meaning. sleeper_basis is None exactly when
        sleeper_points is None, so the pair can never disagree."""
        priced = _pool(None, SEASON_STATS, PPR, dr.SLEEPER_BASIS_SEASON_SUM)
        self.assertIsNotNone(priced["sleeper_points"].iloc[0])
        self.assertEqual(priced["sleeper_basis"].iloc[0], dr.SLEEPER_BASIS_SEASON_SUM)

        unpriced = _pool(150.0, {}, PPR, dr.SLEEPER_BASIS_SEASON_SUM)
        self.assertIsNone(unpriced["sleeper_points"].iloc[0])
        self.assertIsNone(unpriced["sleeper_basis"].iloc[0])

    def test_the_anchor_cache_key_separates_the_two_bases(self):
        """#184 is the cautionary case: a quantity that moves the anchor but is absent from its
        key silently serves one arm the other's answer. sleeper_basis moves the anchor, so it
        is in the key.

        Mutation proven to fail this: dropping repr(sleeper_basis) from the fingerprint.
        """
        args = (_Merger(150.0), PLAYERS, {"WR"}, ["WR", "BN"], 12, "_points",
                SEASON_STATS, PPR, "all", None)
        self.assertNotEqual(
            dr.anchor_cache_key(*args, dr.SLEEPER_BASIS_SEASON_SUM),
            dr.anchor_cache_key(*args, dr.SLEEPER_BASIS_WEEKLY),
            "#180: the two bases produce different anchors and must not share a cache entry")


if __name__ == "__main__":
    unittest.main()
