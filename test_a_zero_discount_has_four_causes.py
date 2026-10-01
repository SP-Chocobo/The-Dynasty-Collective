"""`risk_adj == 0.0` has four causes and only one of them means the designation is unpriced.

Two repairs that were each correct alone produced a false sentence together. `A-F2`/`B-F1` made
`health_penalty`'s absent-projection branch return `0.0` instead of NaN. `C-F1`/`E-F1` gave the
chair a three-way branch keyed on `risk_adj != 0.0`. After both, a row priced on the trade-value
fallback -- real `bpa`, no projection -- reached the third branch and the chair was told "this
engine does not price this designation" about a player discounted at `HEALTH_DISCOUNT_RATE`.
Measured on a HEAVY_IDP board built without season projections: DeShon Elliott (IR, bpa 15.0) and
Harold Landry (PUP, bpa 2.0).

The repair is the companion (`#166`): `health_basis` travels beside `health_penalty`, computed at
the same site from the same inputs, so a consumer reads a verdict instead of inferring one.

Answers to `#166`, `#174` (the number crossed the boundary and its companion did not), `#187`
(an absent measurement is None, never a measured zero) and `#126` (one home for the rule).
"""
from __future__ import annotations

import math
import unittest

import draft_room as dr
import player_universe as pu

_ALL = (dr.HEALTH_BASIS_IN_PROJECTION, dr.HEALTH_BASIS_UNPRICED,
        dr.HEALTH_BASIS_NO_PROJECTION, dr.HEALTH_BASIS_CHARGED)


def _cases():
    """Every basis, built from `HEALTH_DISCOUNT_RATE` itself rather than a remembered list."""
    priced = sorted(k for k, v in dr.HEALTH_DISCOUNT_RATE.items() if v is not None and k)
    assert priced, "HEALTH_DISCOUNT_RATE is empty; this module is vacuous"
    for status in priced:
        yield status, pu.RULE_FLOOR, 100.0, dr.HEALTH_BASIS_IN_PROJECTION
        yield status, None, 100.0, dr.HEALTH_BASIS_CHARGED
        yield status, None, float("nan"), dr.HEALTH_BASIS_NO_PROJECTION
        yield status, None, None, dr.HEALTH_BASIS_NO_PROJECTION
    yield None, None, 100.0, dr.HEALTH_BASIS_UNPRICED
    yield "NotARealDesignation", None, 100.0, dr.HEALTH_BASIS_UNPRICED


class TheBasisNamesWhichPathProducedTheNumber(unittest.TestCase):

    def test_every_basis_is_reachable(self):
        """NON-VACUITY. A pairing test that never exercises a branch proves nothing about it."""
        seen = {dr.health_basis(s, a, p) for s, a, p, _ in _cases()}
        self.assertEqual(set(_ALL), seen, "a declared basis is unreachable from real inputs")

    def test_the_basis_agrees_with_the_penalty_on_every_case(self):
        for status, basis, points, expected in _cases():
            with self.subTest(status=status, basis=basis, points=points):
                self.assertEqual(expected, dr.health_basis(status, basis, points))

    def test_each_basis_is_consistent_with_HEALTH_DISCOUNT_RATE_itself(self):
        """Checked against the AUTHORITY, not against a restatement of the branches."""
        for status, basis, points, _ in _cases():
            got = dr.health_basis(status, basis, points)
            rate = dr.HEALTH_DISCOUNT_RATE.get(status)
            penalty = dr.health_penalty(status, basis, points)
            with self.subTest(status=status, basis=got):
                if got == dr.HEALTH_BASIS_UNPRICED:
                    self.assertIsNone(rate, "unpriced claimed while a rate exists")
                    self.assertEqual(0.0, penalty)
                elif got == dr.HEALTH_BASIS_CHARGED:
                    self.assertIsNotNone(rate)
                    self.assertAlmostEqual(rate * points, penalty, places=9)
                elif got == dr.HEALTH_BASIS_NO_PROJECTION:
                    self.assertIsNotNone(rate, "a rate must exist, or this is UNPRICED")
                    self.assertTrue(points is None or math.isnan(points))
                    self.assertEqual(0.0, penalty)
                else:
                    self.assertEqual(pu.RULE_FLOOR, basis)
                    self.assertEqual(0.0, penalty)

    def test_a_zero_penalty_does_not_mean_the_designation_is_unpriced(self):
        """THE DEFECT, STATED AS AN ASSERTION. Three of the four bases return 0.0, so the float
        cannot distinguish them -- which is exactly what the old consumer tried to do."""
        zeros = {dr.health_basis(s, a, p) for s, a, p, _ in _cases()
                 if dr.health_penalty(s, a, p) == 0.0}
        self.assertGreater(len(zeros), 1,
                           "if only one basis yields 0.0 the old inference was sound and this "
                           "module is about nothing")
        self.assertIn(dr.HEALTH_BASIS_NO_PROJECTION, zeros)
        self.assertIn(dr.HEALTH_BASIS_UNPRICED, zeros)

    def test_a_priced_designation_with_no_projection_is_not_called_unpriced(self):
        """The two real rows, by shape: IR and PUP on the trade-value fallback."""
        for status in ("IR", "PUP"):
            if dr.HEALTH_DISCOUNT_RATE.get(status) is None:
                continue
            self.assertEqual(dr.HEALTH_BASIS_NO_PROJECTION,
                             dr.health_basis(status, None, float("nan")),
                             f"{status} with no projection must not read as unpriced")


if __name__ == "__main__":
    unittest.main()
