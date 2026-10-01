"""MANDATE 2.5 / `#126`: `build_context` shortened four things and told the reader about none of them.

It assembles the largest block of text a panel ever reads, and three of its sections presented a cut
thing as a whole one:

  * a pinned chat message at `[:400]` — stopping mid-sentence, so a model could reason from a
    conclusion whose qualifier was the part that got cut;
  * `projected_available[:15]` under a heading reading "Sleeper canonical player pool", so a panel
    asked "who else is out there" could answer from fifteen rows believing it had seen the pool;
  * `captioned[:20]` under "REFERENCE MATERIAL the user uploaded" — the worst of the three, because a
    panel can then tell the user they never mentioned something they did upload.

A cut list is the list-shaped case of the absence contract: silence about what was removed reads as
nothing having been removed.

AND THE CONVENTION ALREADY EXISTED, in `screen_context`, restated twice with two wordings, while the
one surface that needed it most had it nowhere. So the repair puts it in one home — `cut_note` for a
list, `cut_body` for a text body — and routes every site through it, which is `#126`'s whole point:
five sites cannot drift and a sixth inherits it.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import screen_context as sc
import ui_source


class TheVocabularyHasOneHome(unittest.TestCase):
    def test_a_list_that_was_not_cut_gets_NO_note(self):
        """None, not an empty string: `if note:` at a call site must mean "something was cut"."""
        self.assertIsNone(sc.cut_note(5, 5, "thing(s)"))
        self.assertIsNone(sc.cut_note(9, 3, "thing(s)"),
                          "a shown count above the total is not a cut and must not read as one")

    def test_a_cut_list_names_how_many_are_missing(self):
        self.assertEqual(sc.cut_note(15, 120, "free agent(s)"),
                         "...and 105 more free agent(s).")

    def test_a_body_that_fits_is_returned_UNCHANGED(self):
        self.assertEqual(sc.cut_body("short enough", 400), "short enough")
        self.assertEqual(sc.cut_body("", 400), "")
        self.assertEqual(sc.cut_body(None, 400), "")

    def test_a_cut_body_keeps_the_limit_and_names_the_remainder(self):
        out = sc.cut_body("x" * 500, 400)
        self.assertTrue(out.startswith("x" * 400))
        self.assertIn("100 more character(s)", out)

    def test_the_marker_gives_the_SIZE_and_not_merely_the_fact(self):
        """"there was more" and "there were 3,000 more characters" support different amounts of
        caution about what the remainder might have said."""
        self.assertIn("3000 more character(s)", sc.cut_body("y" * 3400, 400))

    def test_a_body_exactly_at_the_limit_is_not_marked(self):
        self.assertEqual(sc.cut_body("z" * 400, 400), "z" * 400)


class TheSitesThatAlreadyHadItStillReadTheSame(unittest.TestCase):
    """The two `screen_context` restatements are now calls. Their WORDING is unchanged, deliberately:
    this is a `#126` unification, not a rewrite, and two tests already pin those exact strings."""

    def test_the_draft_room_wording_survives(self):
        self.assertEqual(sc.cut_note(8, 12, "candidate(s) in the current pool/scope"),
                         "...and 4 more candidate(s) in the current pool/scope.")

    def test_the_free_agent_wording_survives(self):
        self.assertEqual(sc.cut_note(8, 12, "in the current filter"),
                         "...and 4 more in the current filter.")

    def test_neither_site_still_formats_its_own(self):
        """Read as PARSED code (`#200`): an f-string building that sentence inline is a second home,
        which is the thing being removed."""
        tree = ast.parse(Path("screen_context.py").read_text(encoding="utf-8"))
        # EVERYWHERE EXCEPT THE ONE HOME. `cut_note`'s own body builds this sentence -- that is what
        # makes it the home, so it is excluded BY IDENTITY. `ast.walk` is flat: skipping the
        # FunctionDef node does not skip its children, which is how the first version of this test
        # flagged the definition and could only have been satisfied by having no home at all.
        at_home = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in ("cut_note", "cut_body"):
                at_home.update(id(child) for child in ast.walk(node))
        inline = [
            ast.unparse(node) for node in ast.walk(tree)
            if isinstance(node, ast.JoinedStr) and id(node) not in at_home
            and "...and " in ast.unparse(node) and "more" in ast.unparse(node)
        ]
        self.assertEqual(inline, [], f"the sentence is still built inline somewhere: {inline}")

    def test_and_the_exclusion_is_not_doing_all_the_work(self):
        """Non-vacuity: prove the scan WOULD flag an inline restatement outside the home. Without
        this, a check that excluded everything would pass just as quietly."""
        tree = ast.parse("x = 1\ndef elsewhere():\n    n = 3\n    return f'...and {n} more rows.'\n")
        found = [ast.unparse(node) for node in ast.walk(tree)
                 if isinstance(node, ast.JoinedStr) and "...and " in ast.unparse(node)]
        self.assertTrue(found, "the scan cannot see an inline restatement at all")


class TheContextBuilderActuallyUsesIt(unittest.TestCase):
    """Read off the UI surface through `ui_source`, never by naming a file."""

    @classmethod
    def setUpClass(cls):
        cls.source = ui_source.text()

    def test_the_pinned_message_body_goes_through_cut_body(self):
        self.assertIn("screen_context.cut_body(", self.source)

    def test_no_raw_400_character_slice_survives(self):
        """The defect was the slice itself. A `[:400]` left anywhere here is the same silent cut."""
        self.assertNotIn("[:400]", ui_source.code_text() if hasattr(ui_source, "code_text")
                         else self.source)

    def test_the_player_pool_heading_says_it_is_not_the_whole_pool(self):
        self.assertIn("NOT THE WHOLE POOL", self.source,
                      "the heading still claims to be the pool when it is a fifteen-row slice")

    def test_the_uploaded_captions_report_what_was_not_shown(self):
        self.assertIn("caption(s) the user uploaded, not shown here", self.source)

    def test_every_cut_in_the_builder_is_announced_through_the_one_home(self):
        """Three sites, one vocabulary. Counted so a fourth cut added without a note is visible as a
        count that stopped matching rather than as nothing."""
        self.assertGreaterEqual(self.source.count("screen_context.cut_note("), 2)
        self.assertGreaterEqual(self.source.count("screen_context.cut_body("), 1)


if __name__ == "__main__":
    unittest.main()
