"""D8 / `#56` / `#126` / `#187` -- the health discount was a constant whose MEANING changed.

`RISK_ADJ` held flat points: `{IR: -18.0, PUP: -18.0, Out: -10.0, Doubtful: -5.0}`. Those were sized
against a `bpa` that was `clip(vor / max(vor) * 100, 0, 100)`, where -18 meant *18% of a bounded
scale*. `_scale_vor_to_bpa` is now the identity, so -18 means *18 projected points*, and one
designation began charging unequally:

    a 173-point player      -18 is 10.4% of him
    a 400-point player      -18 is  4.5% of him

That is the distinction D8 draws between the caps and this table. The caps inherited a scale; this
one inherited a **unit**, and became REGRESSIVE IN THE PLAYER'S OWN VALUE with nothing in the code
saying so. Measured on the real capture: the flat table charged two IR players with **0.0 projected
points** a full -18.0 each -- an infinite proportional penalty on a man projected to score nothing.

THE DERIVATION WAS ALREADY IN THE TREE, WHICH IS WHY THIS IS NOT A CALIBRATION.
`availability_factor` already turns a rule floor into a discount: `playable / projected_games`.
`health_penalty` exists only for the rows where that cannot be computed, because the feed reports no
games-played -- and it was substituting an invented flat number where the same proportion was
available. The rate is `games_missed / SEASON_GAMES`, read off the one priced-games vocabulary, so
`#56` is satisfied with **no new number** except the single `Doubtful` assumption, which
`player_universe.ASSUMED_GAMES_MISSED` names as chosen and preserves at the ratio the flat
magnitudes already stated (-5 against Out's -10, so half a game).

THE CHECK THAT SAYS THE DERIVATION IS RIGHT AND NOT MERELY TIDIER -- the two paths agree
EXACTLY AT A FULL SLATE, and the scope is the claim. One fact ("this man is on IR"), reached two
ways, shown at `gp == SEASON_GAMES`:

    gp known    points cut to 13/17 before bpa; penalty stands down (`#191`)
    gp absent   points uncut; penalty = -(4/17) * points

BELOW A FULL SLATE THEY DIVERGE, BY DESIGN (`A-F1`). `availability_factor` divides by the games
actually played and `HEALTH_DISCOUNT_RATE` divides by `SEASON_GAMES`; the mixed denominators are
deliberate, because the naive `(gp - missed)/gp` keeps removing the same games forever and would
charge an absence twice once the feed zeroes the weeks already missed. What is pinned is the
DIRECTION and the BOUND, measured at up to 2.25 points, not equality. An earlier version of this
docstring claimed equality unscoped, twelve lines above a method renamed `..._AT_A_FULL_SLATE` to
scope exactly that -- the module contradicted itself.

    universal_value, both:   0.765 * points - replacement + time_horizon_adj

MEASURED, both paths in one process, replacement 120.0 and time_horizon_adj 2.0:

    status     points    gp-known    gp-absent        gap
    IR            173      14.294       14.294     -0.000
    IR            400     187.882      187.882      0.000
    Out           173      44.824       44.824     -0.000
    Doubtful      400     270.235      270.235      0.000

Before D8 the same two readings differed by **-22.71 points** for a 173-point IR player and
**-76.12** for a 400-point one. It was not a unit wart; it was a 76-point contradiction about one
fact, which is `#126`'s "one concept, one answer" measured in points.

RENAMED, NOT REPURPOSED. `RISK_ADJ` is deleted rather than left holding a fraction, because a name
that outlives its unit is the whole mechanism of this defect. Tier 4's precedent, applied to the
item that proves why the precedent is right.
"""

from __future__ import annotations

import math
import unittest

import data_merger as dm
import draft_room as dr
import draft_battery as dbat
import player_universe as pu
import run_draft_battery as rdb

#: Something for a proportion to be a proportion of. Not a measurement, and nothing below turns on
#: its value -- two different projections are used wherever the POINT is that the share is equal.
REFERENCE_PROJECTION = 200.0


class TheRateIsDerivedNotChosenTests(unittest.TestCase):

    def test_the_old_points_table_is_gone_rather_than_holding_a_fraction(self):
        self.assertFalse(hasattr(dr, "RISK_ADJ"),
                         "a name that says RISK_ADJ while holding a share of a projection is the "
                         "exact trap D8 exists to remove")

    def test_every_rate_is_the_games_it_is_priced_at_over_the_season(self):
        self.assertTrue(dr.HEALTH_DISCOUNT_RATE, "the table is empty; nothing is priced at all")
        for designation, games in pu.GAMES_MISSED_PRICED.items():
            with self.subTest(designation):
                self.assertAlmostEqual(dr.HEALTH_DISCOUNT_RATE[designation],
                                       -(games / pu.SEASON_GAMES), places=9)

    def test_the_priced_set_and_the_rate_set_cannot_drift_apart(self):
        """`#126`. The PUP hole was two hand-listed vocabularies with different membership; the rate
        table is now COMPUTED from the priced-games table, so the two cannot disagree by
        construction rather than by anyone remembering to keep them in step."""
        self.assertEqual(set(dr.HEALTH_DISCOUNT_RATE), set(pu.GAMES_MISSED_PRICED))

    def test_every_designation_with_a_rule_floor_is_priced(self):
        unpriced = sorted(set(pu.GAMES_MISSED_FLOOR) - set(dr.HEALTH_DISCOUNT_RATE))
        self.assertEqual(unpriced, [], f"{unpriced} cost games and carry no discount")

    def test_the_only_chosen_number_is_the_one_declared_chosen(self):
        """`#56` held to its narrowest reading: exactly one magnitude in this vocabulary was picked
        rather than read off an NFL rule, and it is named in its own constant so a second cannot
        arrive quietly beside it."""
        assumed = sorted(set(dr.HEALTH_DISCOUNT_RATE) - set(pu.GAMES_MISSED_FLOOR))
        self.assertEqual(assumed, sorted(pu.ASSUMED_GAMES_MISSED))
        self.assertEqual(assumed, ["Doubtful"])

    def test_the_doubtful_assumption_keeps_the_ratio_the_flat_table_stated(self):
        """What makes it a unit conversion of an existing decision instead of a new decision: the
        old table said -5.0 against Out's -10.0, and half a game is that ratio."""
        self.assertAlmostEqual(pu.ASSUMED_GAMES_MISSED["Doubtful"],
                               pu.GAMES_MISSED_FLOOR["Out"] / 2.0, places=9)

    def test_designations_sharing_a_cost_share_a_rate(self):
        by_games: dict[float, set[float]] = {}
        for designation, games in pu.GAMES_MISSED_PRICED.items():
            by_games.setdefault(games, set()).add(dr.HEALTH_DISCOUNT_RATE[designation])
        shared = [rates for games, rates in by_games.items() if len(rates) > 1]
        self.assertEqual(shared, [], "two designations priced at the same games cost differently")
        self.assertLess(len(by_games), len(pu.GAMES_MISSED_PRICED),
                        "vacuous: no two designations share a games cost (IR and PUP should)")

    def test_a_steeper_cost_never_charges_less(self):
        ordered = sorted(pu.GAMES_MISSED_PRICED.items(), key=lambda pair: pair[1])
        for (small, _), (large, _) in zip(ordered, ordered[1:]):
            self.assertLessEqual(dr.HEALTH_DISCOUNT_RATE[large], dr.HEALTH_DISCOUNT_RATE[small])

    def test_an_unrecognised_designation_is_not_priced_at_all(self):
        for designation in ("Sus", "DNR", "NA", "Cromulent"):
            self.assertNotIn(designation, dr.HEALTH_DISCOUNT_RATE)
            self.assertEqual(dr.health_penalty(designation, None, REFERENCE_PROJECTION), 0.0)


class OneFactReachedTwoWaysGivesOneAnswerTests(unittest.TestCase):
    """The convergence property. This is the test that would have caught the original defect, and
    it is stated over the two functions rather than over a board, so a failure names the seam."""

    REPLACEMENT = 120.0
    TIME_HORIZON = 2.0

    def _universal(self, status, points, projected_games):
        factor, basis = pu.availability_factor(status, projected_games)
        adjusted = factor * points
        return adjusted - self.REPLACEMENT + self.TIME_HORIZON + dr.health_penalty(
            status, basis, adjusted)

    def test_the_haircut_path_and_the_penalty_path_agree_AT_A_FULL_SLATE(self):
        """Exact agreement holds when `gp == SEASON_GAMES`, and the method name now says so.

        A-F1: this only ever called the helper with 17.0, while the FEED REPORTS gp=16 for most IR
        players -- measured on the real capture: IR/None 103 rows, IR/16 20, PUP/None 9, PUP/17 8,
        PUP/16 4, IR/17 3, and 0 of the 13 rule-floor IR rows satisfy the equality. So the claim
        "the two paths agree exactly", which is D8's sole stated validation, was pinned only on
        the minority `gp` value."""
        for status in sorted(pu.GAMES_MISSED_PRICED):
            for points in (50.0, 173.0, 400.0):
                with self.subTest(status=status, points=points):
                    self.assertAlmostEqual(self._universal(status, points, pu.SEASON_GAMES),
                                           self._universal(status, points, None), places=6)

    def test_below_a_full_slate_THEY_DIVERGE_AND_MUST(self):
        """AND THAT DIVERGENCE IS THE DESIGN WORKING, not the seam leaking.

        `availability_factor` is anchored to the SEASON and divided by `gp`, deliberately: the
        naive `(gp - missed) / gp` keeps removing the same four games forever, so once Sleeper
        zeroes out the weeks a man has already missed, the engine would charge that absence a
        second time. The committed form is self-limiting -- as `gp` falls the cut SHRINKS, because
        the feed has already done part of the work.

        The penalty path cannot see any of that; it fires only when `gp` is absent. So at gp < 17
        the gp-KNOWN path holds strictly more information, and the two readings are not supposed
        to match. What must hold is the direction and the bound, which is what this checks."""
        points = 173.0
        full = self._universal("IR", points, pu.SEASON_GAMES)
        previous = None
        for gp in (17.0, 16.0, 15.0, 14.0):
            value = self._universal("IR", points, gp)
            self.assertGreaterEqual(value, full - 1e-9,
                                    f"at gp={gp} the haircut cuts MORE than the penalty path; the "
                                    f"self-limiting form must only ever cut less")
            if previous is not None:
                self.assertGreaterEqual(value, previous - 1e-9,
                                        "the cut must shrink monotonically as gp falls, or the "
                                        "double-charge this form exists to prevent is back")
            previous = value
        # AND IT STOPS: at gp <= SEASON_GAMES - missed there is nothing left to remove.
        factor, _basis = pu.availability_factor("IR", 13.0)
        self.assertEqual(factor, 1.0)

    def test_the_two_paths_are_genuinely_different_code(self):
        """Non-vacuity, and it matters more than usual: if both arms took the same branch the
        equality above would be trivially true and would prove nothing about the seam."""
        _f, known = pu.availability_factor("IR", 17.0)
        _g, absent = pu.availability_factor("IR", None)
        self.assertEqual(known, pu.RULE_FLOOR)
        self.assertEqual(absent, pu.NO_GAMES_REPORTED)
        self.assertEqual(dr.health_penalty("IR", known, REFERENCE_PROJECTION), 0.0)
        self.assertLess(dr.health_penalty("IR", absent, REFERENCE_PROJECTION), 0.0)

    def test_the_old_flat_table_did_NOT_agree_with_itself(self):
        """The defect, restated as arithmetic so the convergence above reads as a repair rather than
        a coincidence. Not a claim about current code -- a record of what was replaced."""
        for points, expected_gap in ((173.0, -22.71), (400.0, -76.12)):
            with self.subTest(points=points):
                haircut = (13 / 17) * points - self.REPLACEMENT + self.TIME_HORIZON
                flat = points - self.REPLACEMENT + self.TIME_HORIZON - 18.0
                self.assertAlmostEqual(haircut - flat, expected_gap, places=2)


class ThePenaltyScalesWithThePlayerTests(unittest.TestCase):

    def test_the_same_designation_takes_the_same_share_of_everyone(self):
        shares = {points: dr.health_penalty("IR", None, points) / points
                  for points in (25.0, 100.0, 173.0, 400.0)}
        self.assertAlmostEqual(min(shares.values()), max(shares.values()), places=9,
                               msg=f"the share varies across players: {shares}")

    def test_the_more_valuable_player_loses_more_points(self):
        self.assertLess(dr.health_penalty("IR", None, 400.0),
                        dr.health_penalty("IR", None, 100.0))

    def test_a_player_projected_to_score_nothing_is_charged_nothing(self):
        self.assertEqual(dr.health_penalty("IR", None, 0.0), 0.0)

    def test_a_below_replacement_player_is_never_REWARDED_for_an_injury(self):
        """Why the rate scales the PROJECTION and not `bpa`. `bpa` is negative for most of the pool,
        so a proportional penalty on it would flip sign and pay players to be hurt. Stated as a test
        because the wrong choice here is easy, local, and silent."""
        for points in (5.0, 40.0, 120.0):
            self.assertLessEqual(dr.health_penalty("IR", None, points), 0.0)

    def test_an_absent_projection_is_absent_rather_than_free(self):
        """`#187` at the one place D8 could have reopened the PUP hole -- RESTATED at the v4 blind
        pass, which showed the original reading of it was wrong.

        This asserted NaN, on the reasoning that 0.0 would read as "measured, this designation
        costs nothing". Two lenses found what that cost: a row priced on the TRADE-VALUE branch has
        a real `bpa` and no projection, so it reached here, took the NaN, and left the board with
        its price DELETED and no `absence_kind` beside the blank. Charging NaN did not express
        "unknown"; it discarded a price the engine had computed.

        The distinction the original missed: `#187` forbids reporting an ABSENT MEASUREMENT as a
        measured zero. There is no absent measurement here. The discount is a SHARE OF A
        PROJECTION, and where no projection exists the share of it this designation costs is
        genuinely nothing -- the row's price came from trade value, which this rate was never a
        proportion of. So 0.0 is the measured answer, and the PUP hole this class guards stays shut
        by the two assertions below it rather than by deleting a price."""
        self.assertEqual(dr.health_penalty("IR", None, None), 0.0)
        self.assertEqual(dr.health_penalty("IR", None, float("nan")), 0.0)
        #: The hole itself, still shut: a designation with a projection is still charged for it.
        self.assertLess(dr.health_penalty("IR", None, 100.0), 0.0)
        self.assertLess(dr.health_penalty("PUP", None, 100.0), 0.0)


class OnTheRealBoardTests(unittest.TestCase):
    """The blast radius, measured rather than asserted, because D8 moves real prices."""

    @classmethod
    def setUpClass(cls):
        merger = dm.DataMerger()
        players_db, _provenance = rdb.build_players_db_from_capture()
        league = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
                                      + ["BN"] * 11,
                  "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {}}
        merger.set_league_format(dbat.league_format_hint(league))
        cls.board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                           league=league, mode="balanced")

    def _charged(self):
        return [r for r in self.board
                if r.get("injury_status") in pu.GAMES_MISSED_PRICED
                and r.get("risk_adj") is not None
                and r.get("risk_adj") == r.get("risk_adj")
                and r.get("risk_adj") != 0.0]

    def test_the_population_is_not_empty(self):
        """Non-vacuity: with nobody designated and priced, everything below is free."""
        self.assertTrue(self._charged(),
                        "no row on the real board carries a health discount, so this class "
                        "observes nothing")

    def test_every_charged_row_is_charged_its_own_share(self):
        for row in self._charged():
            points = row.get("projected_points")
            if points is None or points != points or points <= 0:
                continue
            expected = dr.HEALTH_DISCOUNT_RATE[row["injury_status"]] * points
            with self.subTest(name=row.get("name")):
                #: `<=` and not `==`: dynasty scaling multiplies this down by up to 70% for a
                #: positive trajectory (experiment D), so the share is a CEILING on what is charged.
                self.assertLessEqual(abs(row["risk_adj"]) - 1e-6, abs(expected),
                                     "a row is charged MORE than its own share, which dynasty "
                                     "scaling can only reduce")
                self.assertLess(row["risk_adj"], 0.0)

    def test_no_priced_row_is_charged_against_an_absent_projection(self):
        """The pairing `#166` asks for: the number and the thing that gives it meaning travel
        together, so a discount never exists without a projection to be a share of."""
        for row in self._charged():
            points = row.get("projected_points")
            self.assertIsNotNone(points, f"{row.get('name')} is discounted with no projection")
            self.assertEqual(points, points)


if __name__ == "__main__":
    unittest.main()
