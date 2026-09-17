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

import pathlib
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
        allowance the repository's own correction style relies on -- through is_history, not by
        reading the tuple, because how a marker is MATCHED is the half that was wrong."""
        self.assertTrue(prose_names.HISTORICAL_MARKERS)
        for marker in ("was", "renamed", "no longer"):
            self.assertIn(marker, prose_names.HISTORICAL_MARKERS)
        self.assertTrue(prose_names.is_history("This class was `SomethingElse`."))
        self.assertTrue(prose_names.is_history("`Foo` was renamed to `Bar`"))
        self.assertFalse(prose_names.is_history("`Foo` is the current name"))

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
            for _, _, text in (tuple(prose_names.prose_blocks())
                               + tuple(prose_names.markdown_blocks())):
                if prose_names.is_history(text):
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


class AMarkerHasToBeginAWord(unittest.TestCase):
    """The shield was matched as a bare substring, so it opened on the spelling of unrelated
    words. `arm` fired inside Spearman, harmless, harmonize, harmful, alarming and disarmed;
    `were` fired inside lowered and powered. Seven real blocks across the two corpora were
    shielded by letters, which means seven blocks of prose were never checked and nobody could
    have known which."""

    def test_a_marker_buried_inside_another_word_does_not_shield(self):
        for sentence in ("Spearman r = +0.62 between `waiting_cost` and `positional_cliff`",
                         "the join is harmless here",
                         "we harmonize `FLOOR` across the two registers",
                         "a harmful reading of `Questionable`",
                         "an alarming drop in `starter_value`",
                         "the guard is disarmed at this site",
                         "the value is lowered by the clamp",
                         "a powered-down chair"):
            self.assertFalse(prose_names.is_history(sentence),
                             f"a marker's letters inside another word shielded: {sentence!r}")

    def test_the_morphology_this_repository_writes_still_shields(self):
        """The opposite failure, which \\bword\\b would have caused: `staleness` alone accounts
        for 49 blocks, and an identifier-shaped mention like noise_arm has no word boundary at
        all because `_` is a word character."""
        for sentence in ("staleness is why this is recorded",
                         "both ablations agree",
                         "the probes disagree",
                         "two counterfactuals were run",
                         "the noise_arm forces it to 1e9",
                         "the arms were run in both directions"):
            self.assertTrue(prose_names.is_history(sentence),
                            f"a real history/probe marker stopped shielding: {sentence!r}")

    def test_the_word_start_rule_is_what_is_actually_running(self):
        """Non-vacuity: prove the two rules genuinely disagree on this repository's own prose,
        so the tests above are not describing a distinction with no instances."""
        substring = [b for b in prose_names.prose_blocks() + prose_names.markdown_blocks()
                     if any(m in b[2].lower() for m in prose_names.HISTORICAL_MARKERS)
                     and not prose_names.is_history(b[2])]
        self.assertGreater(len(substring), 0,
                           "no block in the tree distinguishes the rules -- if this is ever true, "
                           "the leak is gone from the prose and this guard can be retired")


class MarkdownProseDoesNotVouchForItself(unittest.TestCase):
    """haystack() read *.md whole, so a name written only in a memo was in the universe BECAUSE
    of that memo. Rename a constant, leave one document naming the old one, and every docstring
    still naming it goes on passing. Markdown now contributes its fenced code and nothing else,
    the same rule already applied to Python."""

    def test_a_name_living_only_in_markdown_prose_is_not_in_the_universe(self):
        """Derived rather than named, so it cannot rot: the set of words that appear in markdown
        PROSE and in no fenced block and in no other kind of file must be non-empty, and must be
        disjoint from the haystack."""
        prose = set()
        fenced = set()
        for path in prose_names._tracked("*.md"):
            blocks, code = prose_names.markdown_split(path)
            for _, _, text in blocks:
                prose |= prose_names.words(text)
            fenced |= prose_names.words(code)
        universe = prose_names.words(prose_names.haystack())
        prose_only = prose - fenced
        self.assertGreater(len(prose_only), 100, "the markdown prose/code split collapsed")
        self.assertTrue(prose_only - universe,
                        "every word of markdown prose is in the haystack -- the strip is inert")

    def test_a_name_inside_a_fenced_block_still_vouches(self):
        """The other direction. A fenced block is a QUOTATION of code, not a claim, so it belongs
        in the haystack -- and if it stopped arriving, real names would start reading dead."""
        fenced = set()
        for path in prose_names._tracked("*.md"):
            fenced |= prose_names.words(prose_names.markdown_split(path)[1])
        universe = prose_names.words(prose_names.haystack())
        self.assertGreater(len(fenced), 500, "no markdown fenced code reached the haystack")
        self.assertTrue(fenced <= universe)


class TheConstantCheckReadsTheDocumentsToo(unittest.TestCase):
    """#182 says audit every document. The dead-name half was measured over the markdown and
    declined on its false-positive rate; the constant half was measured and taken, because
    `NAME = 12.0` means one thing wherever it is written and the documents are where this
    repository explains its constants at length."""

    def test_the_markdown_walk_is_substantial(self):
        blocks = prose_names.markdown_blocks()
        self.assertGreater(len(blocks), 5000, "the markdown paragraph walk collapsed")
        self.assertTrue(any(str(path).endswith("CDME_CONTRACTS.md") for path, _, _ in blocks))

    def test_the_markdown_carries_most_of_the_checkable_quotations(self):
        """The number that justified the change: Python prose offers a handful, the documents
        offer several times as many. If this ever inverts, the asymmetry recorded in the module
        is no longer true and the reasoning beside it should be re-read."""
        def quotations(blocks):
            names = set(prose_names.numeric_constants())
            return sum(1 for _, _, text in blocks if not prose_names.is_history(text)
                       for m in prose_names.QUOTED_VALUE.finditer(text)
                       if (m.group(1) or m.group(3)) in names)

        in_python = quotations(prose_names.prose_blocks())
        in_markdown = quotations(prose_names.markdown_blocks())
        self.assertGreater(in_python, 0, "non-vacuity: Python still contributes")
        self.assertGreater(in_markdown, in_python,
                           "the documents were the larger population -- that was the whole point")

    def test_fenced_code_is_not_read_as_prose(self):
        """A fenced block quotes output and transcripts. Reading one as a claim would report
        every printed constant in every saved run as the prose contradicting the code."""
        blocks, code = prose_names.markdown_split(pathlib.Path("CDME_CONTRACTS.md"))
        self.assertTrue(code, "CDME_CONTRACTS.md has fenced blocks; none were separated")
        joined = "\n".join(text for _, _, text in blocks)
        self.assertNotIn(code.strip().splitlines()[0].strip(), joined,
                         "a fenced line reached the prose corpus")

    def test_a_heading_is_a_block_and_not_a_divider(self):
        """Six real quotations live inside a markdown heading — `NEAR_TIE_BAND = 2.0`,
        `NECESSITY_STANDOUT_REFERENCE_GAP = 15.0`, `NEED_BONUS_MAX = 12.0`, each written into an
        `### A1`/`A2`/`A3` heading twice over. The first draft of the walk DISCARDED headings,
        which exempted all six; all six agree with the code, so nothing would have said so."""
        names = set(prose_names.numeric_constants())
        headings = [b for b in prose_names.markdown_blocks() if b[2].startswith("#")]
        self.assertGreater(len(headings), 1000, "headings are not reaching the corpus at all")
        quoted = {m.group(1) or m.group(3)
                  for _, _, text in headings if not prose_names.is_history(text)
                  for m in prose_names.QUOTED_VALUE.finditer(text)
                  if (m.group(1) or m.group(3)) in names}
        self.assertTrue(quoted, "no heading carries a checkable constant quotation")
        self.assertIn("NEED_BONUS_MAX", quoted)

    def test_a_heading_does_not_shield_the_paragraph_beneath_it(self):
        """The other half of the same decision, measured and rejected: letting a heading supply
        marker context to what follows costs 4 of 35 checkable quotations and does not shield
        the case that motivated trying it. A heading governs itself only."""
        blocks = prose_names.markdown_blocks()
        index = {(str(path), line): text for path, line, text in blocks}
        self.assertIn(("POST_AUDIT_PLAN.md", 5518), index,
                      "the #178 pre-registration paragraph is the worked case; if this moves, "
                      "re-point it rather than deleting the guard")
        self.assertTrue(prose_names.is_history(index[("POST_AUDIT_PLAN.md", 5518)]),
                        "it shields on its own word 'registered', not on its heading")

    def test_the_markdown_is_deliberately_absent_from_the_dead_name_check(self):
        """Pinned so it cannot be added silently. It was measured -- 3,416 occurrences tested,
        50 system-shaped names reported, 0 of them defects -- and declined, and that reasoning
        lives in a comment beside dead_names() which this asserts is still there."""
        source = pathlib.Path("prose_names.py").read_text(encoding="utf-8")
        self.assertIn("THE DEAD-NAME CORPUS IS PYTHON PROSE", source)
        sites = [site for sites in prose_names.dead_names().values() for site in sites]
        self.assertFalse([s for s in sites if s.endswith(".md") or ".md:" in s],
                         "a markdown site reached the dead-name report")


class AModuleIsANameEvenWhenNothingImportsIt(unittest.TestCase):
    """#285: the exclusion that stops this checker vouching for itself also erased its own
    module name, and the first comment to cite `prose_names` was reported as dead."""

    def test_this_checkers_own_module_name_is_in_the_universe(self):
        """The regression case exactly. `prose_names` is imported by one file in the tree --
        test_prose_names.py -- and NOT_ITS_OWN_CORPUS removes that file, so nothing but the
        stem can put this name in the universe."""
        universe = prose_names.words(prose_names.haystack())
        self.assertIn("prose_names", universe,
                      "the checker cannot see its own module name")

    def test_a_module_nothing_imports_is_still_a_name(self):
        """Not a special case for this module: every tracked .py stem is importable, so every
        one of them is a name in the system whether or not any code spells it out."""
        stems = {path.stem for path in prose_names._tracked("*.py")}
        self.assertTrue(stems, "no tracked Python files -- the corpus is empty")
        universe = prose_names.words(prose_names.haystack())
        self.assertEqual(sorted(stems - universe), [],
                         "a tracked module's own name is missing from the universe")

    def test_a_stem_that_is_not_tracked_is_not_forgiven(self):
        """The widening is derived from the tree, so it must not forgive a name shaped like a
        module that no file provides. Without this, 'add every stem' could quietly become
        'add every word that looks like one'."""
        universe = prose_names.words(prose_names.haystack())
        self.assertNotIn("prose_names_that_never_existed", universe)


if __name__ == "__main__":
    unittest.main()
