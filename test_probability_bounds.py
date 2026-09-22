"""A quantity called a probability must be one, and the check must be able to notice when it is not.

THE DEFECT THIS EXISTS FOR, measured by mutation rather than by reading. Setting
`draft_strategy.RUN_TAKE_PROBABILITY_CAP` to **9.0** -- a cap on a probability, set to nine --
left all 51 tests in `test_draft_strategy` passing. The shipped value is 0.90 and is correct;
what was missing is anything that would notice if it stopped being.

WHY THE REPAIR IS NOT "CHANGE 9 TO 1". The value was never wrong. The bound was never stated as
an invariant, so it could be changed to anything and the suite would agree. A constant is only
as sound as the thing that would object to it moving, and until this file existed nothing would.

WHY THE CONSTANTS ARE DISCOVERED, NOT LISTED. A hand-written list of "the probability constants"
goes stale the first time someone adds one -- which is the same failure mode as a hand-listed
vocabulary anywhere else in this repository (#126). These are found by walking the module, and a
new probability constant is therefore covered on the day it is written rather than on the day
somebody remembers to add it here.

NOT IN SCOPE, deliberately. `positional_forfeits` produces an `expected_taken` that sums to 23.32
players over 22 intervening picks, which is a different defect -- two take models disagreeing --
and it belongs to the propagation phase. This file pins that a probability is a probability; it
does not pin that the take model is right.
"""
import unittest

import draft_strategy as ds


def _probability_constants(module):
    """Module-level constants whose NAME says they are a probability.

    `*_BOOST` is excluded on purpose and by name: a boost is a multiplier applied BEFORE a cap
    (`min(w * RUN_TAKE_PROBABILITY_BOOST, RUN_TAKE_PROBABILITY_CAP)`), so a value above 1 is
    what it is for. Excluding it by rule rather than by listing the others keeps this derived.
    """
    found = {}
    for name in dir(module):
        if "PROBABILITY" not in name or name.endswith("_BOOST"):
            continue
        value = getattr(module, name)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            found[name] = value
        elif isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, (int, float)) and not isinstance(item, bool):
                    found[f"{name}[{key!r}]"] = item
    return found


class AProbabilityConstantIsAProbability(unittest.TestCase):
    def test_the_module_actually_has_some_to_check(self):
        """Without this, every assertion below passes over an empty set."""
        found = _probability_constants(ds)
        self.assertGreaterEqual(len(found), 5,
                                f"only {len(found)} probability constants discovered, so the "
                                "bounds checks below are close to vacuous")

    def test_every_discovered_probability_constant_is_between_zero_and_one(self):
        """The planted mutation: RUN_TAKE_PROBABILITY_CAP = 9.0 passed 51 tests. It does not
        pass this one."""
        for name, value in sorted(_probability_constants(ds).items()):
            with self.subTest(constant=name):
                self.assertGreaterEqual(value, 0.0, f"{name} = {value} is a negative probability")
                self.assertLessEqual(value, 1.0,
                                     f"{name} = {value} is a probability greater than certainty")

    def test_the_boost_exclusion_is_narrow_and_deliberate(self):
        """The exclusion must not become a hole. A boost is a pre-cap multiplier, so it may
        exceed 1 -- but it must still be positive and finite, and there must be a cap for it to
        be multiplied against."""
        self.assertGreater(ds.RUN_TAKE_PROBABILITY_BOOST, 0.0)
        self.assertLess(ds.RUN_TAKE_PROBABILITY_BOOST, 100.0)
        self.assertLessEqual(ds.RUN_TAKE_PROBABILITY_CAP, 1.0,
                             "the boost is only safe because a cap bounds it; the cap is not "
                             "bounding anything")


class APerPickTakeProbabilityIsAProbability(unittest.TestCase):
    """The constants above are the input; these are the outputs, on the real rank table."""

    def test_the_rank_table_is_monotone_and_bounded(self):
        previous = 1.0
        for rank in sorted(ds.RANK_TAKE_PROBABILITY):
            value = ds.RANK_TAKE_PROBABILITY[rank]
            self.assertTrue(0.0 <= value <= 1.0, f"rank {rank} -> {value}")
            self.assertLessEqual(value, previous,
                                 f"rank {rank} is more likely to be taken than rank {rank - 1}")
            previous = value

    def test_a_boosted_run_probability_cannot_exceed_certainty(self):
        """The exact composition the cap exists to bound: every rank in the table, boosted."""
        for rank, base in sorted(ds.RANK_TAKE_PROBABILITY.items()):
            boosted = min(base * ds.RUN_TAKE_PROBABILITY_BOOST, ds.RUN_TAKE_PROBABILITY_CAP)
            self.assertLessEqual(boosted, 1.0,
                                 f"rank {rank} boosted to {boosted} -- a rival takes this "
                                 "player with more than certainty")


if __name__ == "__main__":
    unittest.main()


class TheTierDetectorDetectsRatherThanGreps(unittest.TestCase):
    """#52 phase 4. `suite_taxonomy.tier_of` was `"DataMerger()" in source` -- a substring, in a
    module whose own docstring promises detection "never declared ... cannot silently disagree
    with reality the way a hand-maintained list would". A substring is a grep: it calls a
    docstring MENTION a construction, and cannot see `DataMerger(league_dir=...)`.

    On today's tree the substring and the parse agree exactly, so this is a hole closed before
    it opened rather than a live defect -- and these tests plant both failure directions so it
    stays closed.
    """

    def setUp(self):
        import suite_taxonomy as st
        self.st = st

    def test_a_mere_mention_is_not_a_construction(self):
        """The false positive: prose naming the class would have been billed as expensive."""
        mention_only = '"""This module explains why DataMerger() is expensive."""\nx = 1\n'
        self.assertFalse(self.st._constructs_a_data_merger(mention_only),
                         "a docstring mentioning DataMerger() is classed as constructing one")

    def test_a_construction_with_arguments_is_still_a_construction(self):
        """The false negative, and the one that actually matters: the substring required empty
        parentheses, so every call carrying an argument was billed as cheap."""
        for source in ('m = DataMerger(league_dir=p)\n',
                       'm = dm.DataMerger(match_cutoff=0.9)\n',
                       'm = DataMerger()\n'):
            with self.subTest(source=source.strip()):
                self.assertTrue(self.st._constructs_a_data_merger(source),
                                f"{source.strip()} is not detected as constructing a merger")

    def test_the_census_is_live_rather_than_recited(self):
        """The stale-number defect. The docstring stated "53 fast modules, 845 tests, 1.5
        seconds" as measured fact while the suite grew to ~124 fast modules and ~205 seconds.
        A number worth stating is worth deriving, so it is derived now."""
        census = self.st.tier_census()
        self.assertIn("fast", census)
        self.assertIn("full", census)
        self.assertEqual(sum(census.values()), len(self.st.modules()),
                         "the census does not account for every module, so it is not a census")
        self.assertGreater(census["fast"], 0)

    # A fifth test here scanned the module docstring with a regex for the superseded counts.
    # It failed on the correction's own QUOTATION of them -- and a regex policing prose is the
    # text-scan-where-a-parse-exists pattern this audit spent six waves flagging. Deleted
    # rather than made cleverer: `tier_census()` existing, and the test above asserting it
    # accounts for every module, is what actually stops a number rotting in prose.


class AScaleIsMeasuredFromThePoolItScales(unittest.TestCase):
    """#52 phase 5, owner ruling. `FORFEIT_SCALE_MAX = 100.0` sat under a comment saying the
    scale "is CONSTRUCTED so 100 is the largest real VOR gap in the remaining pool". That
    construction was real until `_scale_vor_to_bpa` became the identity; the divisor was then
    calibrated against a band nothing produces. Measured on the owner's league, the largest real
    VOR gap is 446.05, so the forfeit term saturated for every scarce position.

    No number is chosen by the repair -- the scale is read off the same candidates the forfeit is
    computed for, which is the derivation the comment always claimed.
    """

    def test_the_scale_is_the_pools_own_spread(self):
        import pick_synthesis as ps
        pool = [{"team_acquisition_value": 220.56}, {"team_acquisition_value": -225.49}]
        self.assertAlmostEqual(446.05, ps._forfeit_scale(pool), places=2)

    def test_a_pool_that_cannot_answer_falls_back_rather_than_dividing_by_nothing(self):
        """Absence of a spread is not a spread of zero. Fewer than two priced candidates, or a
        flat pool, must not produce a divide-by-zero or a scale of 0."""
        import pick_synthesis as ps
        for pool in ([], [{"team_acquisition_value": 50.0}],
                     [{"team_acquisition_value": 7.0}] * 3,
                     [{"team_acquisition_value": None}, {"team_acquisition_value": None}]):
            with self.subTest(pool=pool):
                self.assertEqual(ps.FORFEIT_SCALE_MAX, ps._forfeit_scale(pool))

    def test_the_scale_is_not_the_literal_it_replaced(self):
        """Non-vacuity: if the derivation silently returned the fallback on a real pool, every
        test above would still pass while the defect stayed."""
        import pick_synthesis as ps
        real_pool = [{"team_acquisition_value": v} for v in (220.5, 100.0, 12.0, -225.4)]
        self.assertNotEqual(ps.FORFEIT_SCALE_MAX, ps._forfeit_scale(real_pool))


class OnePercentilePairHasOneConversionRate(unittest.TestCase):
    """#52 phase 5, owner ruling. `upside_score` added `0.5 x (proj3yr_pct - season_pct)` to raw
    points, UNCLAMPED -- up to 50 points -- while `time_horizon_adj` reads the same two columns
    and clamps to TIME_HORIZON_CLAMP (+/-10). Two readers of one input pair, five times apart.

    Clamped to the bound the other reader already uses rather than to a new number: #56 forbids
    calibrating a constant, and this one is not invented here.
    """

    def test_the_growth_term_cannot_exceed_the_bound_the_other_reader_uses(self):
        import draft_room as dr
        import pandas as pd
        ceiling = max(dr.TIME_HORIZON_CLAMP)
        # A maximal growth signal: bottom-percentile this season, top-percentile over three.
        row = pd.Series({"bpa": 0.0, "_has_3yr": True, "_season_proj_pct": 0.0,
                         "_proj3yr_pct": 100.0, "bpa_source": "points_vor_draftsharks"})
        scored = dr.upside_score(row)
        self.assertLessEqual(scored["final_score"], ceiling + 1e-9,
                             f"a percentile difference moved the score by "
                             f"{scored['final_score']}, past the {ceiling} bound this engine "
                             "already applies to the same percentile pair")

    def test_the_raw_growth_signal_is_still_reported_unclamped(self):
        """The clamp is on the CONVERSION, not on the measurement. growth_signal is an observed
        quantity and must keep saying what was observed."""
        import draft_room as dr
        import pandas as pd
        row = pd.Series({"bpa": 0.0, "_has_3yr": True, "_season_proj_pct": 0.0,
                         "_proj3yr_pct": 100.0, "bpa_source": "points_vor_draftsharks"})
        self.assertAlmostEqual(100.0, dr.upside_score(row)["growth_signal"], places=1)


class TheCapsTupleBoundsWhatItActuallyBounds(unittest.TestCase):
    """#52 phase 6 (W4-02). `sum(TEAM_SPECIFIC_CAPS)` was documented as "the UPPER bound on
    team_acquisition_value - universal_value", and two shipped constants -- the denial
    saturation point and the elevated-context threshold -- derive from it.

    The premise behind that claim was that `displacement_adj`, the fourth team term, "is
    non-positive by construction ... so it cannot raise the sum these caps bound". It is not
    non-positive: a multi-eligible player whose primary-position level exceeds his shared
    IDP_FLEX alternative gets LIFTED, measured at +79.44 with a gap of 87.82 against a claimed
    bound of 36.0 (24.0 since 6.1b -- see below; the gap is larger against the smaller bound,
    so the falsity is not softened by the retirement).

    These tests pin the structural facts, not the values. Re-deriving the two constants means
    choosing a saturation point and a threshold for a distribution nobody has argued for, which
    is #56's prohibition and a valuation change rather than a repair.

    6.1b RETIRED eligibility_bonus and its cap left this tuple, taking the SUM from 36.0 to
    24.0 -- which is not the prohibited re-derivation but the SAME derivation over an input
    that lost a member, and these tests are written to survive exactly that: they assert the
    tuple holds the caps of the capped terms and nothing else, deriving both sides, rather than
    counting members or naming constants that a later ruling can retire.
    """

    def test_the_uncapped_team_term_is_not_in_the_tuple(self):
        """The structural fact the claim rested on. If displacement_adj is ever added to
        TEAM_SPECIFIC_CAPS it will need a cap first, and this test should be the thing that
        makes someone notice.

        DERIVED ON BOTH SIDES, and that is the repair this test needed rather than a new count.
        It used to assert `3 == len(TEAM_SPECIFIC_CAPS)` and name each cap, so 6.1b retiring one
        term failed it for the wrong reason -- the tuple had not stopped bounding what it
        bounds, it had lost a member legitimately. A test that counts a population cannot tell
        a legitimate removal from a defect. This asks the question that actually matters: does
        the tuple hold the cap of every capped team term, and nothing else?"""
        import pick_synthesis as ps
        import draft_room as dr
        capped = {name.removesuffix("_MAX").lower(): getattr(dr, name)
                  for name in dir(dr) if name.endswith("_MAX")}
        # Only the caps of terms that are actually team-specific -- TRADE_VALUE_SCALE_MAX is a
        # scale bound on a different quantity and has never belonged here.
        expected = {v for k, v in capped.items() if k in dr.TEAM_SPECIFIC_TERMS}
        self.assertEqual(expected, set(ps.TEAM_SPECIFIC_CAPS),
                         "the caps tuple no longer holds exactly the caps of the capped "
                         "team-specific terms")
        self.assertNotIn("displacement_adj", capped,
                         "displacement_adj acquired a cap; it may now belong in the tuple, and "
                         "the constants derived from the tuple move if it is added")

    def test_that_derivation_is_not_vacuous(self):
        """The assertion above compares two derived sets, which would hold trivially if both
        came back empty -- the shape that let a guard pass while measuring nothing."""
        import pick_synthesis as ps
        self.assertGreaterEqual(len(ps.TEAM_SPECIFIC_CAPS), 2)

    def test_the_fourth_term_has_no_cap_to_be_bounded_by(self):
        """Why the tuple cannot bound the gap: there is no DISPLACEMENT_*_MAX to add to it."""
        import draft_room as dr
        capped = [name for name in dir(dr)
                  if name.startswith("DISPLACEMENT") and name.endswith("MAX")]
        self.assertEqual([], capped,
                         f"displacement_adj now has a cap ({capped}) -- if it is bounded, the "
                         "caps tuple and everything derived from it should be revisited")

    def test_the_derived_constant_still_derives_from_the_tuple(self):
        """Not a value assertion -- a wiring assertion. If someone hard-codes 24.0 to make a
        number behave, the derivation that makes the falsity traceable is gone.

        ONE CONSTANT NOW, NOT TWO. `CONTEXT_ELEVATED_THRESHOLD` was the second, and it went with
        its flag at #25 (ruled 2026-09-21) -- retired rather than re-thresholded, because it fired
        on one row across 36 formats. That leaves NECESSITY_DENIAL_SATURATION as the ONLY shipped
        constant reading this tuple, which makes the tuple easier to mistake for decorative. It
        is not, and this is the assertion that says so."""
        import pick_synthesis as ps
        self.assertEqual(sum(ps.TEAM_SPECIFIC_CAPS), ps.NECESSITY_DENIAL_SATURATION)
        self.assertFalse(hasattr(ps, "CONTEXT_ELEVATED_THRESHOLD"),
                         "CONTEXT_ELEVATED_THRESHOLD is back -- #25 retired it with its flag, "
                         "and a bound left in place with nothing reading it is the #56 companion "
                         "problem: the next reader takes it for a live threshold")
