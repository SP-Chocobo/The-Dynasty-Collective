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
