"""#300: the freshness manifest, now that it can be CALLED rather than only read.

While `build_freshness_manifest` lived in `app.py`, the only way to hold it was to read its
source text -- `test_sleeper_client` did exactly that, through `ui_source`, and said in its
docstring that it was a stopgap until `#137` moved the function. Every test here is one that
source-reading could not express.

The empty-snapshot case is the one the front page depends on: `app.py` calls this with
`st.session_state.league_snapshot or {}` so the Data Freshness grade renders BEFORE any league is
synced, and that affordance had nothing holding it.
"""

import subprocess
import sys
import unittest
from datetime import datetime, timedelta
from unittest import mock

import freshness
import sleeper_client as sc


class _Merger:
    """A stand-in carrying only what the manifest reads off a DataMerger.

    Deliberately not a real `DataMerger`: constructing one loads vendor files from disk, and
    these tests are about which ROWS appear for a given set of flags, not about the loader.
    """

    def __init__(self, **kw):
        self.is_loaded = kw.get("loaded", False)
        self.is_free_agents_loaded = kw.get("free_agents", False)
        self.is_trade_values_loaded = kw.get("trade_values", False)
        self.freshest_date, self.staleness_days = "2026-11-01", 3
        self.free_agents_freshest_date, self.free_agents_staleness_days = "2026-10-30", 5
        self.trade_values_freshest_date, self.trade_values_staleness_days = "2026-10-28", 7


def _labels(entries):
    return [label for label, _, _ in entries]


class ItCanBeImportedWithoutTheUI(unittest.TestCase):
    """The guarantee the whole extraction exists for, and the only one worth a subprocess.

    Checked in a fresh interpreter because this test module's own imports would otherwise
    decide the answer -- `sys.modules` in THIS process says nothing about what importing
    `freshness` alone costs.
    """

    def _modules_after_importing_freshness(self) -> set[str]:
        code = "import sys, freshness; print(' '.join(sorted(sys.modules)))"
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             cwd=".", timeout=120)
        self.assertEqual(out.returncode, 0, out.stderr)
        return set(out.stdout.split())

    def test_importing_it_does_not_drag_in_streamlit_or_the_app(self):
        loaded = self._modules_after_importing_freshness()
        self.assertNotIn("streamlit", loaded)
        self.assertNotIn("app", loaded)

    def test_the_annotation_only_dependency_stays_deferred(self):
        """`DataMerger` is needed for the signature and nothing else, so it sits under
        TYPE_CHECKING. Importing it at runtime would pull the data layer into every caller --
        including a front-page fixture that only wants the dates."""
        self.assertNotIn("data_merger", self._modules_after_importing_freshness())


class TheEmptySnapshotCaseTheFrontPageNeeds(unittest.TestCase):
    def test_an_empty_snapshot_still_yields_the_two_unconditional_rows(self):
        entries = freshness.build_freshness_manifest({}, _Merger())
        self.assertEqual(len(entries), 2, _labels(entries))
        self.assertIn(sc.players_freshness_entry()[0], _labels(entries))

    def test_no_vendor_row_appears_when_nothing_is_loaded(self):
        labels = " ".join(_labels(freshness.build_freshness_manifest({}, _Merger())))
        self.assertNotIn("Draft Sharks", labels)

    def test_no_league_sync_row_without_a_synced_at(self):
        labels = " ".join(_labels(freshness.build_freshness_manifest({}, _Merger())))
        self.assertNotIn("Sleeper league sync", labels)


class EachRowIsBehindItsOwnCondition(unittest.TestCase):
    def test_each_vendor_flag_adds_exactly_its_own_row(self):
        for kw, expected in (({"loaded": True}, "Draft Sharks Dynasty Rankings"),
                             ({"free_agents": True}, "Draft Sharks Free Agent Finder"),
                             ({"trade_values": True}, "Draft Sharks Trade Value Chart")):
            with self.subTest(flag=kw):
                entries = freshness.build_freshness_manifest({}, _Merger(**kw))
                self.assertEqual(len(entries), 3, _labels(entries))
                self.assertIn(expected, _labels(entries))

    def test_all_three_flags_give_all_three_rows(self):
        entries = freshness.build_freshness_manifest(
            {}, _Merger(loaded=True, free_agents=True, trade_values=True))
        self.assertEqual(len(entries), 5, _labels(entries))

    def test_a_synced_at_adds_the_league_row_and_describes_its_age(self):
        now = datetime.now()
        entries = freshness.build_freshness_manifest(
            {"synced_at": now.timestamp()}, _Merger())
        sync = [e for e in entries if e[0].startswith("Sleeper league sync")]
        self.assertEqual(len(sync), 1, _labels(entries))
        self.assertEqual(sync[0][1], now.date().isoformat())


class TheOrderingIsTheWholePointOfTheSort(unittest.TestCase):
    def test_an_undated_row_sorts_last(self):
        with mock.patch.object(sc, "players_freshness_entry",
                               return_value=("Players (absent)", None, None)), \
             mock.patch.object(sc, "season_projection_freshness_entry",
                               return_value=("Season sums", "2026-11-01", 3)):
            entries = freshness.build_freshness_manifest({}, _Merger())
        self.assertIsNone(entries[-1][2])
        self.assertEqual(entries[0][0], "Season sums")

    def test_rows_are_freshest_first(self):
        entries = freshness.build_freshness_manifest(
            {}, _Merger(loaded=True, free_agents=True, trade_values=True))
        ages = [age for _, _, age in entries if age is not None]
        self.assertEqual(ages, sorted(ages), _labels(entries))


class TheSyncRowKeepsItsCalendarDayColumn(unittest.TestCase):
    """#140 pinned a deliberate split: the LABEL carries the real age at hours resolution, while
    the days column stays a calendar-date difference so it sorts against rows that only have a
    per-day date. Changing the column's unit for one row would make the sort compare two things.
    """

    def test_the_days_column_is_a_calendar_date_difference_not_an_elapsed_hours_value(self):
        eleven_hours_ago = datetime.now() - timedelta(hours=11)
        entries = freshness.build_freshness_manifest(
            {"synced_at": eleven_hours_ago.timestamp()}, _Merger())
        sync = next(e for e in entries if e[0].startswith("Sleeper league sync"))
        expected = (datetime.now().date() - eleven_hours_ago.date()).days
        self.assertEqual(sync[2], expected)
        self.assertIn("ago", sync[0], "the label is where the real age lives (#140)")


if __name__ == "__main__":
    unittest.main()
