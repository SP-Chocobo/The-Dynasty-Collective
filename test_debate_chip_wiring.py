"""Structural regression checks for the universal 💬 Debate chip's wiring in app.py.

app.py is not a cleanly importable module -- it's a top-level Streamlit script that requires
a live Sleeper/DataMerger session to execute past its own setup (confirmed: importing it runs
straight into a NoneType error the moment it reaches session-dependent state). These are
source-level checks, not behavioral ones, and exist specifically to catch a future edit that:
  - reverts a surface's Debate chip back to a hand-built context string instead of the shared
    screen_context builder (silently reintroducing the "panel re-derives the verdict blind"
    bug this whole contract exists to prevent), or
  - lets the universal chip start writing question_input directly (collapsing "open" and
    "ask" back into one action, which was the specific thing rejected during the mockup
    review), or
  - lets the two Debate-labeled help strings on Draft Room drift back together.

See test_screen_context.py's DebateHelpTextDistinctnessTests for the behavioral half of the
same guarantee (the help text CONSTANTS are distinct); this file only checks that app.py
actually uses them, and uses the right builder at each call site.
"""

import re
import unittest

import ui_source

_APP_SOURCE = ui_source.text()


class DebateChipWiringTests(unittest.TestCase):
    def test_trade_calculator_builds_its_context_via_the_shared_builder(self):
        self.assertIn("trade_context = screen_context.build_trade_context(", _APP_SOURCE)

    def test_trade_calculator_chip_is_wired_to_that_same_context_object(self):
        self.assertIn('render_debate_chip(trade_context, key="trade_calculator")', _APP_SOURCE)

    def test_draft_room_chip_is_wired_via_the_shared_builder(self):
        self.assertIn(
            'render_debate_chip(screen_context.build_draft_room_context(snap), key="draft_room")',
            _APP_SOURCE,
        )

    def test_matchup_chip_is_wired_via_the_shared_builder(self):
        self.assertIn("screen_context.build_matchup_context(", _APP_SOURCE)
        self.assertIn("roster_table, focus_position=st.session_state.matchup_expanded_position", _APP_SOURCE)
        self.assertIn('key="matchup",', _APP_SOURCE)

    def test_free_agents_chip_is_wired_via_the_shared_builder(self):
        self.assertIn(
            "screen_context.build_free_agents_context(fa_rows, fa_position_filter, fa_search)",
            _APP_SOURCE,
        )
        self.assertIn('key="free_agents"', _APP_SOURCE)

    def test_league_chip_is_wired_via_the_shared_builder(self):
        # Coverage for this call site otherwise lives only in test_league_view_wiring.py --
        # asserted here too so this file's own claim of being "the one place to check all
        # Debate wiring" (see module docstring) stays true for a reader who only opens this
        # file.
        self.assertIn(
            'render_debate_chip(screen_context.build_league_context(team_label, context_rows), key="league")',
            _APP_SOURCE,
        )

    def test_mock_draft_edit_chip_is_wired_via_the_shared_builder(self):
        # The re-drafting flow's own chip -- adjacent to the exact "board rebuilt, chip still
        # holds a stale context" bug class Draft Room's own chip was already fixed for once.
        self.assertIn(
            'render_debate_chip(screen_context.build_draft_room_context(edit_snap), key="mock_draft_edit")',
            _APP_SOURCE,
        )

    def test_mock_draft_on_the_clock_chip_is_wired_via_the_shared_builder(self):
        self.assertIn(
            'render_debate_chip(screen_context.build_draft_room_context(mock_snap), key="mock_draft")',
            _APP_SOURCE,
        )

    def test_two_debate_controls_reference_the_distinct_named_help_constants(self):
        self.assertIn("help=screen_context.UNIVERSAL_DEBATE_HELP", _APP_SOURCE)
        self.assertIn("help=screen_context.DRAFT_ROOM_PICK_DEBATE_HELP", _APP_SOURCE)

    def test_render_debate_chip_never_writes_question_input(self):
        # Opening and asking are two different actions on purpose -- render_debate_chip
        # attaches context and reveals the dock, it never seeds or submits a question itself.
        # (The docstring itself names "question_input" to explain what it deliberately does
        # NOT do -- checking for an actual assignment, not the bare word, avoids that false
        # positive.)
        body = _extract_function_body("render_debate_chip")
        self.assertNotIn('state["question_input"] =', body)
        self.assertNotIn("state.question_input =", body)

    def test_render_debate_chip_attaches_the_context_it_was_given(self):
        body = _extract_function_body("render_debate_chip")
        self.assertIn("st.session_state.debate_attached_context = context", body)

    def test_render_debate_chip_can_reveal_a_collapsed_dock(self):
        body = _extract_function_body("render_debate_chip")
        self.assertIn('"collapsed"', body)
        self.assertIn("st.rerun()", body)


def _extract_function_body(name: str) -> str:
    match = re.search(rf"\ndef {re.escape(name)}\(.*?(?=\ndef |\Z)", _APP_SOURCE, re.DOTALL)
    if match is None:
        raise AssertionError(f"{name} not found in app.py")
    return match.group(0)


if __name__ == "__main__":
    unittest.main()
