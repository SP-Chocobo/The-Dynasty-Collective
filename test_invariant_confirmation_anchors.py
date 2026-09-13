"""#214: the instruments could survive a restart but could not FINISH one. This one could not START.

`invariant_confirmation.py` breaks the engine on purpose and asks whether the suite notices. It
was committed at `e89201a` and has never produced a measurement -- and until it was repaired it
could not have. Its runner refused any anchor whose occurrence count was not exactly 1, and both
anchors occur TWICE in `draft_room.py`: once in `compute_draft_board`'s upside-mode branch, once
in its balanced branch. Checked against `e89201a` itself: twice there too. **Born broken, and
nothing said so because nothing ran it.**

A harness whose anchors have silently stopped matching the source is worse than no harness: it
reports ANCHOR FAILED, or -- the version of this that actually hurts -- mutates a source that no
longer compiles, fails every test, and calls that "caught". This module is what stops both,
without paying the harness's own ~1200s-per-arm cost.
"""

from __future__ import annotations

import ast
import types
import unittest
from pathlib import Path

import invariant_confirmation as ic


class EveryAnchorStillMatchesTheSource(unittest.TestCase):
    def test_the_mutation_table_is_not_empty(self):
        """Non-vacuity: every test below loops over MUTATIONS and would pass on an empty list."""
        self.assertGreaterEqual(len(ic.MUTATIONS), 2)

    def test_each_anchor_appears_at_least_once(self):
        for name, filename, anchor, _, _ in ic.MUTATIONS:
            with self.subTest(name):
                source = Path(filename).read_text(encoding="utf-8")
                self.assertGreaterEqual(
                    source.count(anchor), 1,
                    f"{name}: the anchor no longer appears in {filename}. The source moved; the "
                    f"harness would report ANCHOR FAILED and measure nothing.")

    def test_each_mutation_changes_every_site(self):
        """The repaired rule. Breaking one of two branches is not breaking the invariant -- the
        other branch goes on defending it, and a `caught` verdict would be about half the engine."""
        for name, filename, anchor, replacement, _ in ic.MUTATIONS:
            with self.subTest(name):
                source = Path(filename).read_text(encoding="utf-8")
                mutated, sites = ic.apply_mutation(source, anchor, replacement)
                self.assertEqual(sites, source.count(anchor))
                self.assertNotEqual(mutated, source, f"{name}: the mutation is a no-op")

    def test_both_branches_of_compute_draft_board_are_covered(self):
        """The specific fact that broke it, stated so a future split or merge of the two branches
        fails here rather than silently halving the harness's reach."""
        source = Path("draft_room.py").read_text(encoding="utf-8")
        for name, filename, anchor, _, _ in ic.MUTATIONS:
            if filename == "draft_room.py":
                with self.subTest(name):
                    self.assertEqual(source.count(anchor), 2,
                                     f"{name}: expected the upside-mode and balanced branches. If "
                                     f"compute_draft_board was refactored, re-derive this number "
                                     f"from the source rather than editing it to match.")

    def test_every_mutant_still_parses(self):
        """The failure mode with teeth. A mutant that does not compile fails EVERY test, and the
        runner's `rc != 0` would call that caught -- reporting the invariant defended when nothing
        about the invariant was exercised. The runner now parses first; this proves the mutants it
        would produce today are real code, not syntax errors."""
        for name, filename, anchor, replacement, _ in ic.MUTATIONS:
            with self.subTest(name):
                source = Path(filename).read_text(encoding="utf-8")
                mutated, _ = ic.apply_mutation(source, anchor, replacement)
                ast.parse(mutated, filename=filename)

    def test_indentation_is_taken_from_the_site_not_the_table(self):
        """The two sites sit at different block depths. A replacement carrying its own hard-coded
        indent lands a statement at the wrong level at one of them. Proven on a two-depth sample
        rather than asserted."""
        source = "    a = 1\n        a = 1\n"
        mutated, sites = ic.apply_mutation(source, "a = 1", "a = 1\n{indent}b = 2")
        self.assertEqual(sites, 2)
        self.assertEqual(mutated, "    a = 1\n    b = 2\n        a = 1\n        b = 2\n")


class TheDocstringDoesNotOverclaimItsCoverage(unittest.TestCase):
    def test_the_two_uncovered_targets_are_named_as_uncovered(self):
        """#133's defect in a new file: the docstring listed four targets and the table held two.
        Both uncovered names must still say so, or the file is claiming coverage it lacks."""
        doc = ic.__doc__ or ""
        self.assertIn("NAMED BUT NOT BUILT", doc)
        for target in ("narrow_candidates", "absence contract"):
            self.assertIn(target, doc)
        self.assertEqual(doc.count("NO MUTATION EXISTS"), 2)

    def test_the_built_targets_are_the_ones_in_the_table(self):
        """Non-vacuity for the above: the BUILT half has to correspond to something real."""
        names = " ".join(name for name, *_ in ic.MUTATIONS)
        self.assertIn("feasibility_first", names)
        self.assertIn("board order", names)


if __name__ == "__main__":
    unittest.main()


class AVerdictIsOnlyAFactAboutTheSuiteWhenTheMutantRanAndChangedSomething(unittest.TestCase):
    """`#254`. The harness's first execution produced two verdicts and NEITHER was usable.

    `board order ignores feasibility` was scored "caught" because pandas raised
    `ValueError: Length of ascending (3) != length of by (2)` before any board was built -- the
    mutant could not RUN, so every board-touching test errored for a reason that has nothing to
    do with the suite defending the invariant. `ast.parse` does not catch it; the mutant is
    valid Python whose defect is argument arity at runtime.

    `feasibility_first never binds` was scored "SURVIVED" after a full 1202.6s suite passed,
    on a mutation writing `scored["_feasible"] = 1` into a column measured uniformly 1 already
    (0 rows held 0 at any of 8 samples across a 312-pick board). The mutation changed nothing,
    so there was nothing to catch. `#245`: identical numbers are a broken instrument until
    proven otherwise.

    These tests hold the repair: both states are NAMED, and a run containing either refuses to
    report success."""

    def test_the_two_first_run_failure_modes_are_both_named(self):
        self.assertIn("MUTANT CANNOT BUILD A BOARD", ic.INCONCLUSIVE)
        self.assertIn("MUTATION IS INERT", ic.INCONCLUSIVE)

    def test_conclusive_and_inconclusive_do_not_overlap(self):
        """A verdict is about the suite or about the harness, never both."""
        self.assertEqual(ic.CONCLUSIVE & ic.INCONCLUSIVE, frozenset())

    def test_survived_is_conclusive_not_inconclusive(self):
        """The one verdict that must still fail the build. Folding it into INCONCLUSIVE would
        turn 'nothing defends this' into 'nothing to see here'."""
        self.assertIn("*** SURVIVED ***", ic.CONCLUSIVE)
        self.assertNotIn("*** SURVIVED ***", ic.INCONCLUSIVE)

    def test_the_fingerprint_builds_a_board_on_the_clean_tree(self):
        """Non-vacuity for the inertness guard: if the reference could not build, every mutant
        would compare against an empty string and every mutation would read as INERT."""
        ok, fingerprint, err = ic._board_fingerprint()
        self.assertTrue(ok, f"reference board failed to build: {err}")
        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")

    def test_the_fingerprint_is_stable_across_calls(self):
        """The comparison is only meaningful if an UNCHANGED tree fingerprints identically.
        A nondeterministic board would make every mutation look like a real change."""
        first = ic._board_fingerprint()
        second = ic._board_fingerprint()
        self.assertEqual(first[1], second[1])

    def test_a_subprocess_failure_is_reported_as_not_built(self):
        """The viability guard's own branch, exercised without breaking the tree."""
        real = ic.subprocess.run
        ic.subprocess.run = lambda *a, **k: types.SimpleNamespace(
            returncode=1, stdout="", stderr="ValueError: Length of ascending (3) != length of by (2)")
        try:
            ok, fingerprint, err = ic._board_fingerprint()
        finally:
            ic.subprocess.run = real
        self.assertFalse(ok)
        self.assertEqual(fingerprint, "")
        self.assertIn("Length of ascending", err)
