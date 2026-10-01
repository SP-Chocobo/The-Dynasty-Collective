"""Structural regression checks for the Matchup view (app.py, main_view == MATCHUP_VIEW).

Same constraint as the other *_wiring test files: app.py is a top-level Streamlit script, not
a cleanly importable module, so these are source-level checks. They pin the settled Matchup
concept merge (readiness strip -> decomposed roster) and the Debate Scope committed-object
contract's application to this surface specifically:
  - lineup_readiness.compute_readiness is the one source of the readiness strip's facts --
    never a second, inline-recomputed judgment.
  - Exactly one shared, persistent session-state variable (matchup_expanded_position) is both
    what makes a position group "the committed object" and what the Debate chip reads to scope
    itself -- never a per-group independent flag, never inferred from hover/hover-adjacent state.
  - The default expansion is seeded once (setdefault) and never overridden on a later run, so a
    user's own toggle sticks.
"""

import re
import unittest

import ui_source

_APP_SOURCE = ui_source.text()


def _matchup_block() -> str:
    return ui_source.block("if main_view == MATCHUP_VIEW:", "elif main_view == MAINTENANCE_VIEW:")


class MatchupReadinessWiringTests(unittest.TestCase):
    def test_readiness_computed_via_the_shared_module(self):
        block = _matchup_block()
        self.assertIn("lineup_readiness.compute_readiness(roster_table, depth, my_team_label, total_starting_slots)", block)

    def test_total_starting_slots_reuses_lineup_optimizer_not_a_reinvented_count(self):
        block = _matchup_block()
        self.assertIn("lineup_optimizer.slots_from_roster_positions(", block)

    def test_never_invents_a_recommendation_in_the_readiness_strip(self):
        # Checking for actual code patterns, not the bare word -- this module's own docstring
        # legitimately explains what it does NOT do using the word "recommendation."
        block = _matchup_block().lower()
        for banned in ('"should_start"', '"should_sit"', "start him", "sit him", "= recommend"):
            self.assertNotIn(banned, block)

    def test_freshness_pill_is_present(self):
        block = _matchup_block()
        self.assertIn("trade_ledger_ui.freshness_pill(merger.is_stale, merger.staleness_days)", block)


class MatchupCommittedObjectWiringTests(unittest.TestCase):
    """The Debate Scope contract, applied: exactly one shared, persistent state variable
    decides both which position group is expanded AND what the Debate chip sees."""

    def test_single_shared_state_variable_governs_expansion(self):
        block = _matchup_block()
        # Same key used by the button-toggle logic and by the chip's focus_position -- not two
        # independently-tracked flags that could drift out of sync.
        self.assertIn('st.session_state.setdefault("matchup_expanded_position", default_position)', block)
        self.assertIn("st.session_state.matchup_expanded_position = None if is_open else position", block)
        self.assertIn("focus_position=st.session_state.matchup_expanded_position", block)

    def test_expansion_is_committed_via_click_and_rerun_not_a_transient_state(self):
        block = _matchup_block()
        # A real click (st.button) plus st.rerun() -- a persistent, deliberate state change --
        # never a hover/CSS-only affordance masquerading as commitment.
        match = re.search(r'if st\.button\(\s*f"\{arrow\}.*?st\.rerun\(\)', block, re.DOTALL)
        self.assertIsNotNone(match, "expected a button-driven toggle followed by st.rerun()")

    def test_default_expansion_is_seeded_once_not_reasserted_every_run(self):
        block = _matchup_block()
        # setdefault (not a plain assignment) is what lets a user's own later toggle stick --
        # a plain `=` here would silently snap back to the flagged default on every rerun.
        self.assertIn('st.session_state.setdefault("matchup_expanded_position"', block)
        self.assertNotIn('st.session_state.matchup_expanded_position = default_position', block)

    def test_default_expansion_prefers_a_flagged_position(self):
        block = _matchup_block()
        self.assertIn("flagged_positions = {p[\"position\"] for p in readiness[\"thin_positions\"]}", block)
        self.assertIn("default_position = next((p for p in positions_present if p in flagged_positions)", block)


class ReadinessSlotCountAbsenceTests(unittest.TestCase):
    """An all-clear may not be emitted from a slot count that was never computed.

    total_starting_slots is len(lineup_optimizer.slots_from_roster_positions(roster_positions)).
    An absent or empty roster_positions makes it 0, and `filled >= 0` is True for every roster
    that has ever existed -- so the most prominent element on this surface rendered an emerald
    "0/0 starting slots filled" all-clear off a quantity nothing had measured."""

    def test_the_slot_comparison_is_gated_on_the_count_being_measured(self):
        block = _matchup_block()
        self.assertIn('slots_measured = readiness["total_starting_slots"] > 0', block)
        self.assertIn("if slots_measured:", block)

    def test_an_unmeasured_slot_count_is_neither_ok_nor_bad(self):
        block = _matchup_block()
        # Not the emerald all-clear, and not a red failure either -- it is unknown, which is
        # its own tone with its own icon.
        self.assertIn('"unknown": "var(--muted)"', block)
        self.assertIn('"unknown": "❔"', block)
        self.assertIn("Starting slots not computable — this league reports no roster positions", block)

    def test_the_unguarded_always_true_comparison_cannot_come_back(self):
        block = _matchup_block()
        self.assertNotIn(
            'chips = [_readiness_chip(\n            f"{readiness[\'filled_starting_slots\']}/'
            '{readiness[\'total_starting_slots\']} starting slots filled",\n            '
            '"ok" if slots_ok else "bad",\n        )]',
            block,
        )
        # The comparison itself only exists inside the measured branch now.
        slots_ok_at = block.index('slots_ok = readiness["filled_starting_slots"] >=')
        guard_at = block.index("if slots_measured:")
        self.assertLess(guard_at, slots_ok_at)

    def test_the_count_it_does_know_is_still_reported(self):
        # Absence is stated, not substituted -- and the one figure that IS measured (how many
        # players sit in starting slots) still reaches the reader.
        block = _matchup_block()
        self.assertIn("players currently in starting slots", block)


if __name__ == "__main__":
    unittest.main()
