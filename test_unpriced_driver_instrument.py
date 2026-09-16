"""#206 -- the instrument that WITHDRAWS a recommendation must not be able to withdraw it backwards.

evidence/take_model/unpriced_pick_drivers.py refutes a proposed mechanism with a one-sided
permutation test, and a one-sided test has exactly one way to be catastrophically wrong while
looking fine: the tail can be counted on the wrong side. Then a real effect reads as p=0.98 and
a null reads as p=0.02, and the conclusion inverts with nothing in the output to show it. This
repository has already paid for that class of error once -- `rival_premium` measured 0.00 for
269 of 269 candidates because the gap was taken behind the turn instead of ahead of it, and the
run looked like a clean null result.

So the sign is driven from populations whose answer is known by construction, not asserted from
the live data the instrument reports on.

WHAT IS NOT TESTED HERE: whether the withdrawal is CORRECT. That rests on the real board and is
recorded in the instrument's own JSON and docstring. This file only holds the arithmetic that
turns a difference into a p-value, so that the finding means what it says.
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("evidence/take_model")))
import unpriced_pick_drivers as upd  # noqa: E402


def _pool(unpriced_demands, priced_demands):
    return ([{"demand": d, "unpriced": True} for d in unpriced_demands]
            + [{"demand": d, "unpriced": False} for d in priced_demands])


class ThePermutationTestCountsTheCorrectTailTests(unittest.TestCase):
    """The instrument's hypothesis is that teams taking an UNPRICED player carry LESS remaining
    starter demand -- so the p-value must be small when the unpriced group sits LOWER."""

    def test_unpriced_clearly_lower_is_a_small_p(self):
        diff, p, k, n = upd._permutation_p(_pool([0, 0, 0, 0, 0], [9, 9, 9, 9, 9, 9, 9, 9, 9, 9]),
                                           random.Random(1))
        self.assertLess(diff, 0.0, "the observed difference lost its sign")
        self.assertLess(p, 0.01, "an unmistakable effect in the hypothesised direction "
                                 "did not produce a small p -- the tail is on the wrong side")

    def test_unpriced_clearly_HIGHER_is_a_large_p(self):
        """The inversion guard, and the one that actually fails when the tail is flipped."""
        diff, p, _, _ = upd._permutation_p(_pool([9, 9, 9, 9, 9], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]),
                                           random.Random(1))
        self.assertGreater(diff, 0.0)
        self.assertGreater(p, 0.99, "an effect OPPOSITE to the hypothesis produced a small p, "
                                    "so the instrument would 'confirm' a reversed finding")

    def test_no_difference_at_all_lands_mid_range(self):
        _, p, _, _ = upd._permutation_p(_pool([3, 3, 3], [3, 3, 3, 3, 3, 3]), random.Random(1))
        self.assertGreater(p, 0.2, f"a pool with no variation returned p={p}")

    def test_an_unevaluable_stratum_returns_absence_rather_than_a_number(self):
        """#187 where it would do the most damage: a stratum with no unpriced picks has NO
        p-value, and reporting 1.0 or 0.0 there would read as evidence."""
        diff, p, k, n = upd._permutation_p(_pool([], [1, 2, 3]), random.Random(1))
        self.assertIsNone(diff)
        self.assertIsNone(p)
        self.assertEqual((k, n), (0, 3))


class TheVerdictIsDrivenByTheNumbersTests(unittest.TestCase):

    def test_the_instrument_pins_its_seed_and_shuffle_count(self):
        """A seed searched over is a search. These are fixed in the module, so a rerun
        reproduces the published p-values exactly."""
        self.assertIsInstance(upd.SEED, int)
        self.assertGreaterEqual(upd.SHUFFLES, 10000,
                                "too few shuffles to resolve a p-value near 0.05")

    def test_the_published_verdict_reproduces(self):
        """The finding itself, re-derived from the committed JSON rather than restated: the
        pooled contrast is significant and BOTH strata are not, which is what makes it a
        mix artifact rather than a driver."""
        import json
        report = json.loads(upd.OUT.read_text())
        c = report["roster_state_contrast"]
        self.assertLess(c["late_all_positions"]["perm_p"], 0.05)
        self.assertGreaterEqual(c["late_QB_only"]["perm_p"], 0.05)
        self.assertGreaterEqual(c["late_non_QB"]["perm_p"], 0.05)
        self.assertTrue(report["roster_state_effect_dissolves_under_stratification"])
        self.assertIn("WITHDRAWN", report["VERDICT"])
        # And the positional signal the withdrawal redirects to.
        self.assertGreater(report["by_position"]["QB"]["rate"],
                           4 * report["by_position"]["WR"]["rate"],
                           "the QB-vs-rest gap that relocates this to a pricing question "
                           "is no longer in the data")


if __name__ == "__main__":
    unittest.main()
