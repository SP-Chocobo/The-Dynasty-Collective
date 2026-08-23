"""Structural regression checks for the Mock Draft interactive prototype (app.py's Draft Room
view, "🧪 Mock Draft" mode).

Same constraint as test_debate_chip_wiring.py: app.py is a top-level Streamlit script, not a
cleanly importable module, so these are source-level checks rather than behavioral ones. They
exist to guard the one hard requirement from the mock's own greenlight: this stays a UI
interaction prototype over the existing deterministic engine, never a second draft engine.
Specifically, they pin that:
  - pick/board/roster state all read through pick_synthesis.build_snapshot and
    draft_room.simulate_opponent_picks (the same calls Live Draft Room makes), never a
    parallel valuation/necessity/survival/roster-construction implementation living only here;
  - editing an earlier pick truncates and replays through those same functions rather than
    hand-rolling "what would change downstream";
  - the mock's board is the real draft_board_ui component, not a second, plainer table;
  - the mock's settings default from the active league's own normalized format (fmt/league),
    never a hardcoded generic default nor a second interpretation of what those settings mean.
"""

import re
import unittest
from pathlib import Path

_APP_SOURCE = Path(__file__).with_name("app.py").read_text()


def _extract_block(start_marker: str, end_marker: str) -> str:
    start = _APP_SOURCE.index(start_marker)
    end = _APP_SOURCE.index(end_marker, start)
    return _APP_SOURCE[start:end]


class MockDraftSettingsDefaultTests(unittest.TestCase):
    def test_team_count_defaults_from_the_active_league_format(self):
        self.assertIn("_default_teams = min(max(int(fmt[\"teams\"]), 4), 16)", _APP_SOURCE)

    def test_rounds_default_from_the_active_leagues_roster_positions(self):
        self.assertIn('league.get("roster_positions")', _APP_SOURCE)

    def test_scoring_superflex_te_premium_dynasty_still_read_from_fmt(self):
        # These were already correct before this pass -- pinned here so a future edit can't
        # silently regress them while touching the teams/rounds defaults added alongside.
        block = _extract_block('with st.form("mock_draft_settings_form"):', '"🏁 Start Mock Draft"')
        self.assertIn("index=_fmt_scoring_index", block)
        self.assertIn('value=fmt["superflex"]', block)
        self.assertIn('value=fmt["te_premium"]', block)
        self.assertIn('value=fmt["type"] == "Dynasty"', block)


class MockDraftEngineReuseTests(unittest.TestCase):
    """Pins that no new valuation/necessity/survival/roster logic was invented -- every board
    or roster read in the mock goes through the same functions Live Draft Room already calls."""

    def _mock_draft_block(self) -> str:
        return _extract_block('if draft_room_mode == "🧪 Mock Draft":', 'elif not roster:')

    def test_opponent_advancement_uses_the_shared_simulator(self):
        block = self._mock_draft_block()
        self.assertIn("draft_room.simulate_opponent_picks(", block)

    def test_both_the_live_board_and_the_edit_board_use_build_snapshot(self):
        block = self._mock_draft_block()
        self.assertEqual(block.count("pick_synthesis.build_snapshot("), 2)

    def test_editing_truncates_picks_rather_than_hand_editing_downstream_state(self):
        block = self._mock_draft_block()
        self.assertIn('md["picks"][:editing_index]', block)

    def test_no_second_necessity_or_survival_computation_in_the_mock(self):
        block = self._mock_draft_block()
        # These are real engine field NAMES read off a CandidateSnapshot (c.necessity_label,
        # c.survival_probability, ...) throughout this block -- fine. What must never appear is
        # a local function that COMPUTES one, e.g. "def necessity(" or "def survival(".
        self.assertNotRegex(block, r"\bdef\s+\w*(necessity|survival|team_acquisition)\w*\s*\(")

    def test_roster_display_is_a_plain_lookup_not_lineup_construction(self):
        # "Your Roster So Far" must read straight off already-drafted picks + players_db (name/
        # position lookups) -- never call into lineup_optimizer or invent a slot-assignment.
        # (The block's own comment names "lineup_optimizer" to explain what it deliberately
        # does NOT do -- checking for an actual call/import, not the bare word, avoids that
        # false positive.)
        roster_block = _extract_block("Your Roster So Far", "Change a previous pick")
        self.assertNotIn("lineup_optimizer.", roster_block)
        self.assertNotIn("import lineup_optimizer", roster_block)
        self.assertIn("player_position(", roster_block)


class MockDraftBoardComponentTests(unittest.TestCase):
    def test_on_the_clock_board_uses_the_real_draft_board_ui_component(self):
        block = _extract_block('if editing_index is None:', 'elif not roster:')
        self.assertIn("draft_board_ui.serialize_snapshot(", block)
        self.assertIn("draft_board_ui.render_board_html(", block)
        # The old plain st.dataframe candidate table must be gone from the "on the clock" path.
        self.assertNotIn("mock_table_rows", _APP_SOURCE)

    def test_edit_board_also_uses_the_real_draft_board_ui_component(self):
        block = _extract_block("editing an earlier pick", "if editing_index is None:")
        self.assertIn("draft_board_ui.serialize_snapshot(", block)
        self.assertIn("draft_board_ui.render_board_html(", block)

    def test_debate_chip_is_wired_on_both_the_live_and_edit_boards(self):
        block = _extract_block('if draft_room_mode == "🧪 Mock Draft":', 'elif not roster:')
        self.assertIn('render_debate_chip(screen_context.build_draft_room_context(mock_snap), key="mock_draft")', block)
        self.assertIn('render_debate_chip(screen_context.build_draft_room_context(edit_snap), key="mock_draft_edit")', block)


if __name__ == "__main__":
    unittest.main()
