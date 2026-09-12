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


class NoConstantIsQuotedWrongly(unittest.TestCase):
    """#56 says a bound is derived, never calibrated -- and this repository explains most of its
    constants in prose sitting right beside them. Change the constant and the explanation
    becomes a confident, specific lie that nothing reads."""

    def test_every_quoted_constant_value_matches_the_code(self):
        wrong = prose_names.misquoted_constants()
        self.assertEqual(wrong, [],
                         "prose states a constant's value and the code disagrees")

    def test_there_are_constants_to_check_and_they_are_single_homed(self):
        """Non-vacuity, and a #126 measurement in its own right: a constant defined twice with
        different values is two homes for one fact, and this check declines to guess which the
        prose meant. Measured: 92 constants, none conflicting."""
        consts = prose_names.numeric_constants()
        self.assertGreater(len(consts), 80)
        self.assertIn("NECESSITY_SURVIVAL_WEIGHT", consts)

    def test_a_wrong_value_is_actually_detected(self):
        """Planted through the real prose walk: move every constant and the quotations must go
        red. Without this, a QUOTED_VALUE pattern that matched nothing would pass forever."""
        def quotations_checked():
            names = set(prose_names.numeric_constants())
            n = 0
            for _, _, text in prose_names.prose_blocks():
                if any(m in text.lower() for m in prose_names.HISTORICAL_MARKERS):
                    continue
                for m in prose_names.QUOTED_VALUE.finditer(text):
                    if (m.group(1) or m.group(3)) in names:
                        n += 1
            return n

        baseline = quotations_checked()
        self.assertGreater(baseline, 0, "non-vacuity: the pattern must match something")
        real = prose_names.numeric_constants
        prose_names.numeric_constants = lambda: {k: v + 1 for k, v in real().items()}
        try:
            wrong = prose_names.misquoted_constants()
        finally:
            prose_names.numeric_constants = real
        self.assertEqual(len(wrong), baseline,
                         "move every constant and EVERY checked quotation must go red -- not a "
                         "chosen number, the count of what the pattern actually examines")

    def test_scientific_notation_is_read_as_one_number(self):
        """The specific trap. Two documented ablation arms force a cap to `1e9`; a number pattern
        without an exponent group reads that as "1" and reports the arm as a contradiction."""
        found = [(m.group(1) or m.group(3), float(m.group(2) or m.group(4)))
                 for m in prose_names.QUOTED_VALUE.finditer(
                     "`NEED_BONUS_MAX = 1e9` and SOME_TOLERANCE = 1e-9")]
        self.assertEqual(found, [("NEED_BONUS_MAX", 1e9), ("SOME_TOLERANCE", 1e-9)])

    def test_the_probe_allowance_is_load_bearing_right_now(self):
        """Not hypothetical: with the allowance removed, the real ablation arms documented in
        this repository go red. If this stops failing, the allowance has stopped doing anything
        and should be deleted rather than carried."""
        real = prose_names.HISTORICAL_MARKERS
        prose_names.HISTORICAL_MARKERS = ()
        try:
            wrong = prose_names.misquoted_constants()
        finally:
            prose_names.HISTORICAL_MARKERS = real
        self.assertTrue(any(name == "NEED_BONUS_MAX" for _, name, _, _ in wrong),
                        "the NEEDCAP ablation arm is the case this allowance exists for")


if __name__ == "__main__":
    unittest.main()
