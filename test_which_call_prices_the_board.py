"""#28 WITHDRAWN, and the guard that keeps it withdrawn for an honest reason.

#28 said the board compares Draft Sharks against Sleeper-seeded CSVs on one bpa scale, with
nothing establishing the two vendors' point scales agree. Measured, that comparison happens only in
a board built with NO sleeper_projections argument -- which neither app.py (4927, 5006, 5066, 5431)
nor run_draft_battery (425) builds. The finding came from a board I built myself without the
argument and then described as "the live board".

The same phantom configuration produced a second published error: it was used to "correct"
KDST_VALUATION.md's QB 43.9 / K 12.6 / DEF 30.5 as stale. They were not stale -- in the BATTERY
configuration they reproduce exactly, and the correction was the mistake.

So these tests pin the two facts that make both of those checkable rather than assumable:
the un-synced path really does mix vendors (so #28 described something real, in a place nothing
calls), and the configurations that ARE called price every starting-band row from ONE source.

If K/DEF ever silently fall back to the seeded CSVs on a synced board, the second class fails --
which is the regression that would quietly resurrect #28 as a live problem.
"""

from __future__ import annotations

import collections
import unittest

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

ARM = "12T_ppr_K_DEF"
POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def _band_sources(**kwargs) -> dict[str, collections.Counter]:
    """bpa_source counts across each position's STARTING BAND, for one way of calling the board.

    The starting band, not the whole board: most of a board is an unpriced tail whose modal source
    is no_priceable_input in every configuration, so a whole-board count answers nothing about
    which vendor prices the rows a draft actually chooses between.
    """
    scoring = rdb.scoring_settings_from_capture()
    players_db, _ = rdb.build_players_db_from_capture()
    arm = next(a for a in db.league_matrix(scoring) if a["label"] == ARM)
    starters = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])
    merger = dm.DataMerger()
    # Never skipped: scoring reaches offensive valuation by FILE SELECTION, not through
    # scoring_settings, so a board built without this is drafting the wrong export.
    merger.set_league_format(db.league_format_hint(arm["league"]))
    rows = dr.compute_draft_board(merger, players_db, [], 1, arm["league"], **kwargs)
    by_position = collections.defaultdict(list)
    for row in rows:
        by_position[row.get("position")].append(row)
    out = {}
    for position in POSITIONS:
        rank = max(1, int(round(arm["teams"] * starters.get(position, 0.0))))
        band = sorted(by_position[position], key=lambda r: -(r.get("bpa") or 0.0))[:rank]
        out[position] = collections.Counter(r.get("bpa_source") for r in band)
    return out


class TheSyncedBoardPricesEveryPositionFromOneSourceTests(unittest.TestCase):
    """The configuration run_draft_battery actually builds."""

    @classmethod
    def setUpClass(cls):
        cls.bands = _band_sources(
            sleeper_projections=rdb.season_projections_from_capture(),
            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

    def test_every_position_prices_from_the_season_scored_source(self):
        for position in POSITIONS:
            with self.subTest(position=position):
                self.assertEqual(list(self.bands[position]), ["points_vor_sleeper_season_scored"],
                                 f"{position}'s starting band is no longer priced from one "
                                 f"source: {dict(self.bands[position])}")

    def test_K_and_DEF_do_NOT_fall_back_to_the_seeded_csvs_here(self):
        """The specific regression that would resurrect #28 as a live problem, named rather than
        left implicit in the test above."""
        for position in ("K", "DEF"):
            with self.subTest(position=position):
                self.assertNotIn("points_vor_sleeper_seeded", self.bands[position])

    def test_the_bands_are_non_empty(self):
        """Non-vacuity. A band that came back empty would satisfy 'no seeded rows' forever."""
        for position in POSITIONS:
            with self.subTest(position=position):
                self.assertGreater(sum(self.bands[position].values()), 0)


class TheUnsyncedBoardReallyDoesMixVendorsTests(unittest.TestCase):
    """#28 described something real. It is characterised, not denied -- what was wrong was calling
    it the live board. Kept as a test so the withdrawal rests on WHERE the mixing happens rather
    than on a claim that it never does."""

    @classmethod
    def setUpClass(cls):
        cls.bands = _band_sources()

    def test_offence_comes_from_the_vendor_here(self):
        for position in ("QB", "RB", "WR", "TE"):
            with self.subTest(position=position):
                self.assertEqual(list(self.bands[position]), ["points_vor_draftsharks"])

    def test_and_K_DEF_come_from_the_seeded_csvs(self):
        for position in ("K", "DEF"):
            with self.subTest(position=position):
                self.assertEqual(list(self.bands[position]), ["points_vor_sleeper_seeded"])

    def test_so_the_two_bands_disagree_on_source_which_is_what_28_saw(self):
        self.assertNotEqual(list(self.bands["QB"]), list(self.bands["DEF"]),
                            "the un-synced board no longer mixes vendors -- #28's description is "
                            "stale and its withdrawal needs rewriting, not silently keeping")


if __name__ == "__main__":
    unittest.main()
