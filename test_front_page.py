"""The unsynced front page's composition, and the wiring that puts it on screen.

WHY A WIRING TEST AND NOT ONLY A COMPOSITION TEST. `app.py` has 69 top-level Streamlit calls and
no `__main__` guard, so importing it runs the application -- no test in this repo can call the
empty-state branch. `test_maintenance_view_wiring` set the precedent for this: read `app.py`'s
SOURCE and assert the call is there. It is a weaker check than executing it and is named as one,
but the alternative is a composition that is perfectly tested and reachable by nobody, which is
the exact state this item exists to end.
"""
import ast
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import front_page as fp
from data_merger import recency_grade

FIXTURE = ROOT / "ui_explore" / "empty_fixture.json"


def _rows_of(fx):
    """The manifest rows a committed fixture was composed from, reconstructed from the fixture.

    THE REGRESSION ANCHOR IS TIME-INDEPENDENT, which is the point. The real ages move every day,
    so a test that called `build_freshness_manifest` and compared against the committed numbers
    would be stale tomorrow BY CONSTRUCTION -- `#305`'s defect exactly, where a bound was wrong
    the day after it was written because the thing it bounded decays against `date.today()`.
    Feeding the composition the rows implied by the fixture tests the JUDGMENT and nothing else.
    """
    rows = [(r["label"], r["as_of"], r["days"]) for r in fx["have"]]
    rows += [(f'{r["label"]} — {fp.reason_of(r["basis"])}', None, None) for r in fx["on_sync"]]
    return rows


class TheCompositionReproducesTheCommittedFixtureTests(unittest.TestCase):
    def test_the_committed_fixture_is_what_this_composition_produces(self):
        """`#334` moved this judgment out of `capture_empty_fixture.py`. This is the proof the
        move was behaviour-preserving, and it is why the capture script could be gutted."""
        fx = json.loads(FIXTURE.read_text())
        self.assertEqual(fx, fp.compose_unsynced(_rows_of(fx)))

    def test_the_composition_reads_no_clock_and_no_disk(self):
        """Pure in the rows. Called twice on the same input it must agree with itself, and it
        must not need a DataMerger, a file, or today's date to answer."""
        rows = [("A", "2026-01-01", 10), ("B — never fetched", None, None)]
        self.assertEqual(fp.compose_unsynced(rows), fp.compose_unsynced(rows))


class TheSplitIsTheWholeDesignDecisionTests(unittest.TestCase):
    def test_a_dated_row_is_on_disk_and_an_undated_row_arrives_with_the_sync(self):
        out = fp.compose_unsynced([("Rankings", "2026-08-25", 74),
                                   ("Sleeper players — never fetched", None, None)])
        self.assertEqual(["Rankings"], [r["label"] for r in out["have"]])
        self.assertEqual(["Sleeper players"], [r["label"] for r in out["on_sync"]])

    def test_an_absent_row_carries_its_reason_and_is_stamped_absent(self):
        """Not a dash in a table. Before a sync these are the EXPECTED state, not damage."""
        out = fp.compose_unsynced([("Sleeper players — never fetched on this machine", None, None)])
        self.assertEqual("ABSENT -- never fetched on this machine", out["on_sync"][0]["basis"])

    def test_on_disk_rows_are_ordered_freshest_first(self):
        out = fp.compose_unsynced([("old", "2026-01-01", 99), ("new", "2026-06-01", 7),
                                   ("mid", "2026-03-01", 50)])
        self.assertEqual([7, 50, 99], [r["days"] for r in out["have"]])


class TheGradeIsTakenFromTheWorstLoadedSourceTests(unittest.TestCase):
    def test_the_grade_reads_the_OLDEST_source_not_the_newest(self):
        """A grade over the freshest source would call a stale machine fresh."""
        out = fp.compose_unsynced([("new", "2026-06-01", 1), ("old", "2026-01-01", 400)])
        self.assertEqual(400, out["worst_days"])
        self.assertEqual(recency_grade(400), out["grade"])

    def test_the_grade_comes_from_recency_grades_ONE_home(self):
        """Derived, not re-banded here: the front page must not become a second opinion about
        what "Aging" means."""
        for days in (0, 3, 20, 76, 400):
            with self.subTest(days=days):
                out = fp.compose_unsynced([("x", "2026-01-01", days)])
                self.assertEqual(recency_grade(days), out["grade"])

    def test_with_nothing_dated_the_grade_is_ABSENT_and_never_a_number(self):
        """`#187`. A zero here would read as "brand new" for a machine that knows nothing."""
        out = fp.compose_unsynced([("Sleeper players — never fetched", None, None)])
        self.assertIsNone(out["grade"])
        self.assertIsNone(out["worst_days"])
        self.assertTrue(out["grade_basis"].startswith("ABSENT -- "))

    def test_an_empty_manifest_does_not_raise(self):
        out = fp.compose_unsynced([])
        self.assertEqual([], out["have"])
        self.assertEqual([], out["on_sync"])
        self.assertIsNone(out["grade"])


class TheStampParsersTests(unittest.TestCase):
    def test_a_label_without_the_em_dash_returns_itself_as_both_halves(self):
        """Fragile on purpose. A wrong reason reads as reassurance, which is worse than a
        clumsy one -- so it never invents one it does not have."""
        self.assertEqual(("Bare label", "Bare label"), fp.split_reason("Bare label"))

    def test_a_label_with_the_em_dash_splits_into_name_and_reason(self):
        self.assertEqual(("Sleeper players", "never fetched"),
                         fp.split_reason("Sleeper players — never fetched"))

    def test_reason_of_strips_the_engineering_token(self):
        self.assertEqual("never fetched", fp.reason_of("ABSENT -- never fetched"))
        self.assertEqual("read off the file", fp.reason_of("measured -- read off the file"))

    def test_reason_of_never_returns_an_empty_string(self):
        for stamp in ("", None, "ABSENT -- "):
            with self.subTest(stamp=stamp):
                self.assertEqual("No reason recorded.", fp.reason_of(stamp))


class TheAppActuallyRendersItTests(unittest.TestCase):
    """Source-read, because importing `app.py` runs the application. See the module docstring."""

    @classmethod
    def setUpClass(cls):
        cls.src = (ROOT / "app.py").read_text()
        cls.tree = ast.parse(cls.src)

    def test_app_imports_the_one_home(self):
        self.assertIn("import front_page", self.src)

    def test_the_empty_state_branch_calls_the_composition(self):
        """The wiring this whole item exists for. Without it the composition is perfectly tested
        and reachable by nobody -- which is exactly the state `front_claims` was in before
        `#333` and `positional_depth` before `#297`."""
        self.assertIn("front_page.compose_unsynced(", self.src)

    def test_the_composition_is_called_ABOVE_the_only_stop(self):
        """`app.py` has exactly one `st.stop()`, and everything below it is unreachable in the
        state this page exists to serve. A call that drifted below it would render nothing and
        fail no other test here."""
        stops = [n.lineno for n in ast.walk(self.tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "stop"]
        self.assertEqual(1, len(stops), f"app.py should have exactly one st.stop(); found {stops}")
        calls = [n.lineno for n in ast.walk(self.tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "compose_unsynced"]
        self.assertEqual(1, len(calls), "expected exactly one compose_unsynced call")
        self.assertLess(calls[0], stops[0],
                        "compose_unsynced is BELOW the st.stop(); it can never run")

    def test_the_sidebar_grade_is_suppressed_while_unsynced(self):
        """One grade on screen at a time. Wiring the front page put two copies of the same
        judgment on one screen; this is the gate that removed the second, and it was found by
        screenshotting the running app rather than by reading the diff."""
        self.assertIn("if _freshness_entries and st.session_state.league_snapshot:", self.src)


if __name__ == "__main__":
    unittest.main()
