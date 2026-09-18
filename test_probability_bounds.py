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
