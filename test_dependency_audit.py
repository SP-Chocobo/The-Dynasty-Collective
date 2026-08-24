"""Correctness tests for run_dependency_audit.py's own Pearson-correlation helper -- the
measurement tool itself must be right before its output (a real, reported finding, not a
pass/fail assertion about the world) can be trusted."""

from __future__ import annotations

import unittest

from run_dependency_audit import _pearson


class PearsonHelperTests(unittest.TestCase):
    def test_a_series_against_itself_is_perfectly_correlated(self):
        xs = [1.0, 4.0, 2.0, 9.0, 5.0]
        self.assertAlmostEqual(_pearson(xs, xs), 1.0, places=6)

    def test_a_series_against_its_own_negation_is_perfectly_anticorrelated(self):
        xs = [1.0, 4.0, 2.0, 9.0, 5.0]
        self.assertAlmostEqual(_pearson(xs, [-x for x in xs]), -1.0, places=6)

    def test_a_constant_series_has_zero_correlation_with_anything(self):
        # No variance to correlate -- must not divide by zero or return a bogus value.
        self.assertEqual(_pearson([5.0, 5.0, 5.0], [1.0, 2.0, 3.0]), 0.0)

    def test_fewer_than_two_points_is_zero_not_an_error(self):
        self.assertEqual(_pearson([1.0], [2.0]), 0.0)
        self.assertEqual(_pearson([], []), 0.0)

    def test_known_linear_relationship_is_exactly_one(self):
        xs = [0.0, 1.0, 2.0, 3.0, 4.0]
        ys = [10.0, 12.0, 14.0, 16.0, 18.0]  # y = 2x + 10, exact
        self.assertAlmostEqual(_pearson(xs, ys), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
