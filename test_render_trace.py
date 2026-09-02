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

    def test_every_view_appears_in_the_recorded_trace(self):
        for view in render_trace.VIEWS:
            with self.subTest(view=view):
                self.assertTrue([c for c in self.recorded if c.startswith(f"[{view}]")], view)

    def test_no_view_stops_at_the_no_league_guard(self):
        """st.stop() halting early is a real state, but if a VIEW's trace ends there the trace
        is covering the empty screen rather than the view."""
        for view in render_trace.VIEWS:
            with self.subTest(view=view):
                calls = [c for c in self.recorded if c.startswith(f"[{view}]")]
                self.assertNotIn("<st.stop>", calls[-1])

    def test_each_view_renders_a_substantial_number_of_calls(self):
        """A floor, not an exact count -- this is a smoke check that a view actually rendered,
        not a pin on how much UI it happens to draw."""
        for view in render_trace.VIEWS:
            with self.subTest(view=view):
                calls = [c for c in self.recorded if c.startswith(f"[{view}]")]
                self.assertGreater(len(calls), 50, f"{view} barely rendered")

    def test_the_draft_room_trace_contains_its_own_furniture(self):
        """Non-vacuity: the Draft Room's trace must contain Draft-Room things, or the nav
        steering silently failed and every view traced the same default screen."""
        draft = " ".join(c for c in self.recorded if c.startswith("[📋 Draft Room]"))
        self.assertIn("Draft Room mode", draft)


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
        self.assertEqual(render_trace._shape("x" * 200), "str[200]")
        self.assertEqual(render_trace._shape("Retract"), "str:Retract")


if __name__ == "__main__":
    unittest.main()
