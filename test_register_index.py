"""`#355` — the register-completeness ratchet, and the rule that every ratchet must be able to fail.

TWO SUBJECTS, ONE FILE, BECAUSE THEY ARE THE SAME DEFECT AT TWO SCALES.

`register_index.py` exists because `#353` was a rule with no instrument: four items carried commits
and code citations with no register entry, and one of them -- `#351` -- was asserted to be recorded
BY A COMMITTED TEST while no entry existed. Nothing checked, so nothing noticed.

`EveryRatchetsBareInvocationRunsItsCheck` exists because the same shape was found one level up.
Running `skip_gates.py` with no arguments printed its help text and exited 0, and on the strength
of that I published "all 8 ratchets PASS" about a ratchet that had examined nothing. Measuring the
other seven found FIVE with a zero-exit path that verified nothing, and one -- `doc_index.py` --
that was actively self-defeating: bare invocation WROTE the artifact `--check` compares against, so
a bare run followed by a check passed unconditionally, whatever had drifted.

WHY THAT LAST TEST IS NOT VACUOUS, which is the question to ask of any test added in a green tree.
It compares bare OUTPUT against `--check` OUTPUT rather than exit codes. Exit codes would be
vacuous here: on a green tree a hollow ratchet and a sound one both exit 0, which is exactly why
the defect survived. Help text and a census listing do not equal a check's verdict line, so this
fires on the regression whatever colour the tree is.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import subprocess
import sys
import unittest
from unittest import mock

import register_index as ri

#: Every ratchet in the repo. A tenth must be added here, which is the point: the list is the
#: thing that makes the rule enforceable rather than remembered.
RATCHETS = ("assertion_floors", "boundary_census", "skip_gates", "suite_reach", "api_surface",
            "doc_index", "prose_names", "state_vocabulary", "register_index")


class RegisterIndexFiresOnANewUnmentionedCitation(unittest.TestCase):
    """The arms that prove the check can fail. Mutation-verified against the real tree too --
    5/5 arms, recorded in the commit -- but these run in the suite, so they patch rather than
    write, because a test that edits a tracked file races every other test reading it."""

    def test_a_citation_the_register_never_mentions_fails_the_check(self):
        """THE DEFECT THIS EXISTS FOR. Fails on the old behaviour: there was no check at all."""
        with mock.patch.object(ri, "cited", return_value={399: {"somefile.md"}}), \
             mock.patch.object(ri, "mentions", return_value=set()), \
             mock.patch.object(ri, "load", return_value={"items": {}}):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ri.main([])
            self.assertEqual(rc, 1, "a never-mentioned citation did not fail the check")
            self.assertIn("#399", buf.getvalue())

    def test_a_recorded_exception_does_not_fail_the_check(self):
        """Growth is the regression; a citation already in the baseline is not growth."""
        with mock.patch.object(ri, "cited", return_value={399: {"somefile.md"}}), \
             mock.patch.object(ri, "mentions", return_value=set()), \
             mock.patch.object(ri, "load", return_value={"items": {"399": ["somefile.md"]}}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ri.main([]), 0)

    def test_a_missing_baseline_fails_rather_than_holding_nothing(self):
        """An absent baseline is not the same fact as no citation having appeared (`#187`)."""
        with mock.patch.object(ri, "load", return_value={}):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ri.main([])
            self.assertEqual(rc, 1)
            self.assertIn("holding NOTHING", buf.getvalue())

    def test_shrinkage_is_free(self):
        """A citation that disappears must not fail the build -- `skip_gates`' bargain."""
        with mock.patch.object(ri, "cited", return_value={}), \
             mock.patch.object(ri, "mentions", return_value=set()), \
             mock.patch.object(ri, "load", return_value={"items": {"399": ["gone.md"]}}):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ri.main([]), 0)


class TheDigitBoundAndTheMentionTest(unittest.TestCase):
    """The two measurements that got this wrong twice before getting it right."""

    def test_a_six_digit_hex_colour_is_not_an_item(self):
        """`#755024`, `#141109` and `#171309` are colours in design documents.

        A six-digit match reads every one as a register item that does not exist, which is how
        the first estimate of the gap came out at 80.
        """
        self.assertEqual(ri.ITEM.findall("a swatch of `#755024` on obsidian"), [])
        self.assertEqual(ri.ITEM.findall("`#141109` and `#171309`"), [])

    def test_an_item_number_with_a_letter_suffix_resolves_to_its_number(self):
        self.assertEqual(ri.ITEM.findall("`#345b` and `#353b`"), ["345", "353"])

    def test_only_backticked_citations_count(self):
        """The repo's own convention, and the reason hex colours and issue numbers stay out."""
        self.assertEqual(ri.ITEM.findall("a bare #351 in prose"), [])
        self.assertEqual(ri.ITEM.findall("a backticked `#351`"), ["351"])

    def test_the_register_is_searched_for_MENTIONS_not_headings(self):
        """Attempt 2's error, pinned so nobody 'tightens' it back.

        Per-item headings are RECENT. Early items are recorded in prose and in tables -- `#187`
        is cited in 97 files and appears 30 times in the register with no heading anywhere. A
        heading test therefore measures the CONVENTION, not the record, and reported 80 where
        the honest answer is 0.
        """
        self.assertIn(187, ri.mentions("...nearly redoing closed work. #187 (`denial_value`)..."))
        self.assertIn(166, ri.mentions("Same family as #166 (`horizon_basis`), #174"))
        self.assertNotIn(755024, ri.mentions("a swatch of #755024"))


class EveryRatchetsBareInvocationRunsItsCheck(unittest.TestCase):
    """`#352`: a verification tool must have no zero-exit path that verifies nothing.

    FIVE OF THE EIGHT FAILED THIS WHEN IT WAS FIRST MEASURED. `skip_gates` printed help;
    `boundary_census`, `api_surface` and `state_vocabulary` printed a listing; `doc_index` WROTE
    the artifact its own check compares against.
    """

    def test_every_ratchet_module_exposes_main(self):
        for name in RATCHETS:
            with self.subTest(ratchet=name):
                self.assertTrue(callable(getattr(importlib.import_module(name), "main", None)),
                                f"{name} has no callable main")

    def test_bare_invocation_produces_the_checks_own_output(self):
        """Compares OUTPUT, not exit code, and goes through the REAL entry point.

        Exit codes would be vacuous: in a green tree a hollow ratchet and a sound one both exit
        0, which is precisely why the defect survived long enough to be published. Help text and
        a census listing do not equal a verdict line, so this fires whatever colour the tree is.

        It shells out rather than calling `main` in-process because the nine do not share a
        signature -- `prose_names.main()` takes no argv and reads `sys.argv` itself, while the
        other eight take `argv`. Calling them in-process would couple this test to that
        difference and, worse, would test a surface no caller uses. The command line IS the
        surface where the false pass happened.
        """
        for name in RATCHETS:
            with self.subTest(ratchet=name):
                bare = subprocess.run([sys.executable, f"{name}.py"],
                                      capture_output=True, text=True)
                checked = subprocess.run([sys.executable, f"{name}.py", "--check"],
                                         capture_output=True, text=True)
                self.assertEqual(
                    bare.stdout, checked.stdout,
                    f"{name}: bare invocation does not run its check. A zero exit from a tool "
                    f"that examined nothing is indistinguishable from a pass at the call site, "
                    f"which is how 'all 8 ratchets PASS' was published about a ratchet that had "
                    f"run its help text (`#352`).")
                self.assertEqual(bare.returncode, checked.returncode,
                                 f"{name}: bare and --check disagree on exit code")

    def test_no_ratchet_prints_usage_instead_of_checking(self):
        """The specific shape of the original defect, named so it cannot come back quietly."""
        for name in RATCHETS:
            with self.subTest(ratchet=name):
                out = subprocess.run([sys.executable, f"{name}.py"],
                                     capture_output=True, text=True)
                self.assertNotIn("usage:", (out.stdout + out.stderr).lower()[:400],
                                 f"{name} printed its usage text instead of checking anything")

    def test_the_ratchet_list_is_complete(self):
        """A tenth ratchet must be registered here, or the rule only binds the nine I remembered."""
        found = {p.stem for p in ri._tracked("*.py")
                 if "--check" in p.read_text(encoding="utf-8", errors="replace")
                 and "add_argument" in p.read_text(encoding="utf-8", errors="replace")
                 and p.stem.endswith(("_floors", "_census", "_gates", "_reach", "_surface",
                                      "_index", "_names", "_vocabulary"))
                 and not p.stem.startswith("test_")}
        self.assertEqual(found - set(RATCHETS), set(),
                         "a ratchet exists that this list does not hold to the rule")


if __name__ == "__main__":
    unittest.main()
