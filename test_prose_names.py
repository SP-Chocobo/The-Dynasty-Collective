"""#182: the prose has to keep naming things that exist.

`prose_names.py` reads every comment and docstring in this repository and asks whether the
backticked names in them still exist anywhere. On its first run it found three, and the split is
the whole reason the checker is shaped the way it is:

  `PANEL_ONLY`                              A TYPO. The constant is ADJUDICATION_PANEL_ONLY,
                                            defined two lines below the comment naming it.
  `ValidatedFlagIsUnconditional`            NAMED, NEVER WRITTEN. A module docstring listed it as
                                            one of two characterization guards. It was introduced
                                            with the file at 4136118 and no such class has ever
                                            existed -- so the docstring told every reader a gap
                                            was watched that nothing watched.
  `TheConstructionIsStrandedOnPurposeTests` CORRECT. Its own sentence says "This class WAS
                                            `TheConstructionIsStrandedOnPurposeTests`". Naming
                                            what no longer exists is REQUIRED by this repo's
                                            discipline of striking claims in place.

So absence alone is not the defect. The rule is "the name exists, or the prose says it is
history", and that third case is what these tests defend against a checker that would flag every
correction this repository has ever written.
"""

from __future__ import annotations

import unittest

import prose_names


class NoProseNamesTheRepositoryLost(unittest.TestCase):
    def test_every_backticked_name_in_prose_still_exists(self):
        dead = prose_names.dead_names()
        self.assertEqual(dead, {},
                         "a comment or docstring names something that exists nowhere. Either the "
                         "name is wrong, or the thing was renamed and its explanation was not.")


class TheCheckerIsNotVacuous(unittest.TestCase):
    """Three ways this could pass while checking nothing, each closed."""

    def test_it_reads_a_real_and_substantial_amount_of_prose(self):
        blocks = prose_names.prose_blocks()
        self.assertGreater(len(blocks), 2000, "the comment/docstring walk collapsed")
        self.assertTrue(any("draft_room" in str(p) for p, _, _ in blocks))

    def test_the_haystack_excludes_the_prose_itself(self):
        """The subtle vacuity: if the search corpus included comments and docstrings, every name
        would vouch for itself by being mentioned, and nothing could ever be dead."""
        universe = prose_names.words(prose_names.haystack())
        self.assertNotIn("ValidatedFlagIsUnconditional", universe,
                         "this name appears ONLY in a docstring; if it reaches the haystack the "
                         "checker is searching its own input")
        self.assertIn("ADJUDICATION_PANEL_ONLY", universe,
                      "non-vacuity the other way: real code names must survive the strip")

    def test_it_finds_a_name_that_does_not_exist(self):
        """Planted, end to end through the real walk."""
        real = prose_names.haystack
        prose_names.haystack = lambda: "nothing here resembles a name"
        try:
            dead = prose_names.dead_names()
        finally:
            prose_names.haystack = real
        self.assertGreater(len(dead), 50,
                           "against an empty corpus almost every backticked name must read dead")

    def test_a_name_marked_as_history_is_allowed(self):
        """The case that makes a naive absence check useless here. Proven by exercising the same
        allowance the repository's own correction style relies on."""
        self.assertTrue(prose_names.HISTORICAL_MARKERS)
        for marker in ("was ", "renamed", "no longer"):
            self.assertIn(marker, prose_names.HISTORICAL_MARKERS)

    def test_the_historical_allowance_is_load_bearing_right_now(self):
        """Not a hypothetical: with the allowance removed, a name this repository deliberately
        quotes as history goes red. If this ever stops failing, the allowance has stopped doing
        anything and should be deleted rather than carried."""
        real = prose_names.HISTORICAL_MARKERS
        prose_names.HISTORICAL_MARKERS = ()
        try:
            dead = prose_names.dead_names()
        finally:
            prose_names.HISTORICAL_MARKERS = real
        self.assertIn("TheConstructionIsStrandedOnPurposeTests", dead)


if __name__ == "__main__":
    unittest.main()
