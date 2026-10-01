"""§19.8's discipline applied to a refactor: the before/after instrument, shown to fail.

WHY THE SUITE CANNOT DO THIS JOB. Most of app.py's coverage is SOURCE SCANNING -- assertions
that a string appears in the file. Move a section into another module and those either fail for
an unrelated reason or, far worse, keep passing while covering nothing. That already happened in
miniature: a test sliced `app.py[start:start + 2000]` and silently stopped reaching the row it
guarded once the block above it grew.

So the extraction needs a BEHAVIOURAL reference, and this file is what proves the reference
works. A trace instrument that had only ever been run on unmodified code would be the exact
shape of thing this repository keeps finding: a check nobody has watched fail.
"""

import json
import re
import unittest
from pathlib import Path

import render_trace

_HERE = Path(__file__).parent


class TheTraceReachesEveryViewTests(unittest.TestCase):
    """The first version of this instrument recorded 79 calls and stopped at the "sync a Sleeper
    username" screen -- it never reached a single view, while looking like it had run. Seeding a
    synthetic league is what makes it cover the code actually being extracted."""

    @classmethod
    def setUpClass(cls):
        cls.recorded = json.loads((_HERE / "RENDER_TRACE.json").read_text())["calls"]

    #: Iterated over PASSES rather than VIEWS, because a view whose branches are chosen by a
    #: widget contributes one labelled pass per branch. Checking VIEWS would pass while an entire
    #: branch went untraced -- which is how the Mock Draft stayed uncovered.
    def _calls(self, label):
        return [c for c in self.recorded if c.startswith(f"[{label}]")]

    def test_every_pass_appears_in_the_recorded_trace(self):
        for label, _, _ in render_trace.TRACE_PASSES:
            with self.subTest(label=label):
                self.assertTrue(self._calls(label), label)

    def test_no_pass_stops_at_the_no_league_guard(self):
        """st.stop() halting early is a real state, but if a PASS's trace ends there the trace
        is covering the empty screen rather than the view."""
        for label, _, _ in render_trace.TRACE_PASSES:
            with self.subTest(label=label):
                self.assertNotIn("<st.stop>", self._calls(label)[-1])

    def test_each_pass_renders_a_substantial_number_of_calls(self):
        """A floor, not an exact count -- this is a smoke check that a view actually rendered,
        not a pin on how much UI it happens to draw."""
        for label, _, _ in render_trace.TRACE_PASSES:
            with self.subTest(label=label):
                self.assertGreater(len(self._calls(label)), 50, f"{label} barely rendered")

    def test_the_draft_room_trace_contains_its_own_furniture(self):
        """Non-vacuity: the Draft Room's trace must contain Draft-Room things, or the nav
        steering silently failed and every view traced the same default screen."""
        for label, _, _ in render_trace.TRACE_PASSES:
            if not label.startswith("📋 Draft Room"):
                continue
            with self.subTest(label=label):
                self.assertIn("Draft Room mode", " ".join(self._calls(label)))

    def test_both_draft_room_modes_are_traced_and_they_differ(self):
        """The recorded fixture once covered only the Live branch, because the mode radio lists it
        first and every stand-in widget returns options[0]. The Mock branch was not reported as
        uncovered -- it was simply absent, and it is the branch that shipped a TypeError."""
        live = self._calls("📋 Draft Room · Live")
        mock = self._calls("📋 Draft Room · Mock")
        self.assertTrue(live and mock, "one of the two Draft Room branches is missing")
        self.assertNotEqual(live, mock,
                            "both Draft Room passes recorded the same calls -- the mode steering "
                            "is not working and one branch is untraced")

    def test_each_draft_room_pass_reaches_THE_BOARD(self):
        """THE DEFECT THIS FIXTURE EXISTED WITHOUT NOTICING. Every view was traced in its EMPTY
        state: the seed carried `"rosters": [], "users": []`, so app.py found no roster and each
        view fell to its guard. Measured on the old fixture: 619 calls, 3 empty-state guard
        strings, and ZERO board, candidate or pick-synthesis calls. Breaking the live board left
        the trace BYTE-IDENTICAL, while the instrument reported five views and 619 calls.

        Verified by monkeypatching `compute_draft_board` to return nothing: the Live pass then
        loses 9 calls and the Mock pass 11, where both previously lost none. This pins the
        board's own furniture so the fixture cannot quietly return to covering empty screens."""
        for label in ("📋 Draft Room · Live", "📋 Draft Room · Mock"):
            joined = " ".join(self._calls(label))
            with self.subTest(label=label):
                self.assertIn("board_title_row", joined,
                              f"{label} never reaches the board container")

    def test_the_trace_carries_no_calendar_dependent_value(self):
        """The freshness grade is `recency_grade(now - oldest_source_date)`, so it turns over on a
        date with no UI change behind it -- this fixture was scheduled to go red on 2026-11-19 and
        had already churned once inside an unrelated commit. An instrument that emits a false diff
        on a timer teaches its readers to regenerate without looking."""
        for call in self.recorded:
            if "Data Freshness" in call:
                self.assertIn("&lt;grade&gt;", call,
                              "the freshness grade is recorded verbatim and will turn over with "
                              "the calendar")
                self.assertNotIn('class="status-ok"', call)
                self.assertNotIn('class="status-bad"', call)

    def test_no_ELAPSED_TIME_QUANTITY_of_any_kind_reaches_the_recorded_trace(self):
        """THE RULE, not the two instances of it. The test above pins the freshness grade and
        passed while a SECOND calendar-derived string escaped beside it -- `trade_ledger_ui`'s
        "Values 34d stale", a raw day count, so it turned over every midnight rather than at a
        grade boundary, and `--check` went red on 2026-09-29 with no code behind it.

        A test that names the strings it knows about cannot catch the next one. This one states
        what the trace may not contain: an elapsed-time quantity, in any unit. Long strings are
        blurred to `str[long]` before they get here, so a static caption mentioning a number of
        days is not in scope -- only the short, verbatim ones, which is exactly the population
        that turns over on a timer."""
        elapsed = re.compile(r"\b\d+\s*(?:d|day|days|hr|hrs|hour|hours|w|wk|weeks?|"
                             r"months?|yr|yrs|years?)\b")
        offenders = [call for call in self.recorded if elapsed.search(call)]
        self.assertEqual(offenders, [],
                         "an elapsed-time quantity is recorded verbatim and will turn over with "
                         "the calendar; blur it in _Recorder._CALENDAR_DEPENDENT")


class TheTraceIsCurrentTests(unittest.TestCase):
    def test_the_recorded_trace_matches_the_tree(self):
        """The check CI runs. A diff here during a refactor means the refactor changed
        behaviour; a diff during a deliberate UI change means regenerate it on purpose."""
        self.assertEqual(render_trace.main(["--check"]), 0,
                         "render trace is stale -- `python3 render_trace.py --write` if the UI "
                         "change was intended")


class TheStandInDoesNotInventPathsTests(unittest.TestCase):
    """Two places a permissive stub let app.py run down a path the real Streamlit never takes.
    Both were found by the app crashing, and both are pinned here so a future convenience does
    not quietly restore them."""

    def test_st_stop_halts_the_run_as_it_really_does(self):
        """A stub that returned from st.stop() traced 400 lines the app never executes -- worse
        than tracing nothing, because it would look like coverage."""
        source = (_HERE / "render_trace.py").read_text()
        self.assertIn("raise _Stopped()", source)

    def test_a_selectable_dataframe_returns_an_empty_selection(self):
        """Returning a generic truthy stub let app.py subscript a selection that, in a default
        render, has nothing in it."""
        self.assertEqual(render_trace._Selection().selection.rows, [])


class WhatItCannotSeeIsStatedTests(unittest.TestCase):
    """A check whose limits are unstated gets trusted past them."""

    def test_the_module_says_it_only_covers_the_default_render_path(self):
        source = (_HERE / "render_trace.py").read_text()
        self.assertIn("traces the DEFAULT render path only", source)
        self.assertIn("Branches behind a click are", source)

    def test_argument_values_are_blurred_so_the_trace_is_about_structure(self):
        """A trace that churned whenever a projection changed would be measuring the data, not
        the refactor."""
        self.assertEqual(render_trace._shape("x" * 200), "str[long]")
        self.assertEqual(render_trace._shape("Retract"), "str:Retract")

    def test_a_long_strings_own_length_is_not_recorded(self):
        """#151, as its exact signature. This trace used to emit `str[97]`, and a length is a
        VALUE -- so the committed reference went stale overnight on `str[97]` -> `str[98]`
        when the Data Sources caption ticked from "(9d ago)" to "(10d ago)". No UI changed.

        Asserted on _shape directly rather than by faking a clock, because a clock CANNOT be
        faked in this process: any C extension imported during a capture runs PyDateTime_IMPORT,
        which validates datetime's binary layout, so a subclass trips
        "RuntimeWarning: datetime.datetime size changed" whether it is installed at the source
        or behind a sys.modules shim. Two strings of different lengths that differ by nothing
        else must be indistinguishable here -- that is the whole property, and it is exactly
        testable without a clock."""
        self.assertEqual(render_trace._shape("x" * 97), render_trace._shape("x" * 98))
        self.assertEqual(render_trace._shape("updated 2026-08-26 (9d ago)" + "x" * 60),
                         render_trace._shape("updated 2026-08-26 (10d ago)" + "x" * 60))

    def test_the_boundary_between_kept_and_blurred_is_still_a_boundary(self):
        """Non-vacuity for the test above: if _shape blurred EVERYTHING, it would pass while
        the trace lost the labels and keys that are its actual structure."""
        self.assertEqual(render_trace._shape("x" * 60), "str:" + "x" * 60)
        self.assertEqual(render_trace._shape("x" * 61), "str[long]")

    def test_the_module_records_why_the_clock_cannot_be_frozen_instead(self):
        """The rejected option, kept in the source rather than only in a register entry -- the
        next person to look at this will reach for a clock freeze first, and the reason it
        fails is not guessable from the code."""
        source = (_HERE / "render_trace.py").read_text()
        self.assertIn("PyDateTime_IMPORT", source)
        self.assertIn("size changed", source)


if __name__ == "__main__":
    unittest.main()
