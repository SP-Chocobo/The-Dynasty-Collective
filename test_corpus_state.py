"""§19.4 reused, §16.3 surfaced: which body of data this session's numbers came from.

THREE LIGHTS AT TWO SCOPES, and getting the scopes right is most of the design.

  board scope   which CORPUS is feeding every price -- the shared baseline alone, or the
                baseline plus files this install added
  row scope     which single row was moved by an override the user wrote

An uploaded projections file belongs to the FIRST and not the second, and that is not a
presentation choice. It shifts replacement levels, a league-level quantity every player at that
position is measured against, so it moves prices for players the file never names. Marking it
per row would clear rows the upload did in fact move -- a lie of scope, not merely an imprecise
label. `_drop_contested_identities` already argues exactly this about phantom duplicates.

TONE IS PART OF THE CONTRACT. Uploading your own projections IS the product, so `INCLUDES_LOCAL`
is the normal state for most users and reads calmly. If the ordinary case is dressed as a
caution it becomes wallpaper, and it takes the genuinely loud marks down with it.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import baseline_manifest
import corpus_state

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()


class _Tree(unittest.TestCase):
    """A throwaway repo-shaped tree, so these never touch the real data directory."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.root = Path(self._tmp)
        (self.root / "data/baseline").mkdir(parents=True)
        (self.root / "data/baseline/a.csv").write_text("name\nx\n")
        self.addCleanup(lambda: shutil.rmtree(self._tmp, ignore_errors=True))
        self._real_manifest = baseline_manifest.MANIFEST_PATH
        baseline_manifest.MANIFEST_PATH = self.root / "data/baseline/INPUT_MANIFEST.json"
        self.addCleanup(setattr, baseline_manifest, "MANIFEST_PATH", self._real_manifest)

    def declare(self):
        baseline_manifest.write(self.root, baseline_manifest.MANIFEST_PATH)


class TheFourStatesTests(_Tree):
    def test_a_clean_declared_tree_is_doctrine_only(self):
        self.declare()
        self.assertEqual(corpus_state.assess(self.root)["state"], corpus_state.DOCTRINE_ONLY)

    def test_an_added_file_is_includes_local_and_is_named(self):
        self.declare()
        (self.root / "data/baseline/mine.csv").write_text("name\ny\n")
        result = corpus_state.assess(self.root)
        self.assertEqual(result["state"], corpus_state.INCLUDES_LOCAL)
        self.assertEqual(result["local_files"], ["data/baseline/mine.csv"])

    def test_an_altered_declared_file_is_diverged_not_includes_local(self):
        """A baseline that is not intact is a different and worse situation than a baseline with
        additions, and reporting the additions would bury it."""
        self.declare()
        (self.root / "data/baseline/a.csv").write_text("name\nCHANGED\n")
        (self.root / "data/baseline/mine.csv").write_text("name\ny\n")
        result = corpus_state.assess(self.root)
        self.assertEqual(result["state"], corpus_state.DIVERGED)
        self.assertEqual(result["changed"], ["data/baseline/a.csv"])

    def test_a_missing_declared_file_is_also_diverged(self):
        self.declare()
        (self.root / "data/baseline/a.csv").unlink()
        self.assertEqual(corpus_state.assess(self.root)["state"], corpus_state.DIVERGED)

    def test_no_manifest_is_unknown_and_not_doctrine_only(self):
        """The fourth state. "Nothing is declared" and "nothing was added" are opposite facts,
        and defaulting to DOCTRINE_ONLY would claim the stronger one on no evidence."""
        self.assertEqual(corpus_state.assess(self.root)["state"], corpus_state.UNKNOWN)


class TheToneIsDeliberateTests(_Tree):
    def test_the_normal_states_do_not_read_as_warnings(self):
        """Both DOCTRINE_ONLY and INCLUDES_LOCAL are normal. One is not a degraded version of
        the other, and neither may borrow the vocabulary the loud marks need."""
        for state, files in ((corpus_state.DOCTRINE_ONLY, []),
                             (corpus_state.INCLUDES_LOCAL, ["data/baseline/mine.csv"])):
            with self.subTest(state=state):
                icon, line = corpus_state.light(
                    {"state": state, "local_files": files, "missing": [], "changed": []})
                self.assertNotIn(icon, ("🔴", "⚠️"))
                for alarming in ("warning", "unverified", "not trusted", "invalid"):
                    self.assertNotIn(alarming, line.lower(), alarming)

    def test_includes_local_says_the_effect_is_league_wide_not_per_file(self):
        """The whole reason it is board scope. A user who thinks their upload only affects the
        players it names has the wrong model of what it did."""
        _, line = corpus_state.light({"state": corpus_state.INCLUDES_LOCAL,
                                      "local_files": ["x.csv"], "missing": [], "changed": []})
        self.assertIn("replacement levels", line)
        self.assertIn("league-wide", line)

    def test_includes_local_says_it_is_working_rather_than_broken(self):
        _, line = corpus_state.light({"state": corpus_state.INCLUDES_LOCAL,
                                      "local_files": ["x.csv"], "missing": [], "changed": []})
        self.assertIn("that is them working, not a problem", line)

    def test_only_diverged_raises_its_voice(self):
        icon, line = corpus_state.light({"state": corpus_state.DIVERGED, "local_files": [],
                                         "missing": ["a.csv"], "changed": []})
        self.assertEqual(icon, "🔴")
        self.assertIn("may not mean what this version says", line)

    def test_unknown_says_it_is_unrecorded_rather_than_clean(self):
        _, line = corpus_state.light({"state": corpus_state.UNKNOWN, "local_files": [],
                                      "missing": [], "changed": []})
        self.assertIn("not the same as knowing it is clean", line)

    def test_every_state_produces_a_light(self):
        for state in (corpus_state.DOCTRINE_ONLY, corpus_state.INCLUDES_LOCAL,
                      corpus_state.DIVERGED, corpus_state.UNKNOWN):
            with self.subTest(state=state):
                icon, line = corpus_state.light({"state": state, "local_files": ["x"],
                                                 "missing": ["y"], "changed": []})
                self.assertTrue(icon and line)


class OneDetectorNotTwoTests(unittest.TestCase):
    def test_it_borrows_the_manifest_rather_than_reimplementing_the_check(self):
        """#113 built `diff()` so a CI run could say whether it was reproducible, and its own
        docstring names this exact case: "the demonstrated case: a user's own upload". A second
        implementation would be a second thing to drift."""
        source = (_HERE / "corpus_state.py").read_text()
        self.assertIn("baseline_manifest.diff(", source)
        for reimplemented in ("hashlib", "sha256", "rglob"):
            self.assertNotIn(reimplemented, source, reimplemented)


class BothScopesReachTheDraftRoomTests(unittest.TestCase):
    def test_the_board_level_light_is_rendered(self):
        self.assertIn("corpus_state.assess()", _APP)
        self.assertIn("corpus_state.light(", _APP)

    def test_the_local_files_are_nameable_not_just_countable(self):
        """"Which file" is the first question, and a count that cannot be expanded is a number
        nobody can act on."""
        self.assertIn("Which files are yours", _APP)

    def test_the_row_level_override_warning_is_loud_and_separate(self):
        """Separate from the corpus light on purpose: an alias IS a per-row act, and it is the
        one thing here that can attach another player's numbers to this one."""
        self.assertIn("priced through your own name override", _APP)
        self.assertIn("bypasses the team and position checks", _APP)

    def test_the_override_warning_tells_the_user_how_to_undo_it(self):
        self.assertIn("Manual Aliases", _APP)


if __name__ == "__main__":
    unittest.main()
