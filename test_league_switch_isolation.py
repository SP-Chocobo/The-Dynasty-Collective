"""#52 phase 7.4d / L-06: Draft Room state must not survive a league switch.

`activate_league` reset chat history, the league snapshot and the merger, and left every
`draft_room_*` key in place -- and nothing else in app.py ever set `draft_room_debate_result`,
`draft_room_last_snapshot` or `draft_room_snapshot_cache` back to None. Three keys with no
reset path anywhere.

The scenario: league A at 2.03 with 14 picks, run the debate, switch to league B also at 2.03
with 14 picks. A's debate renders under B's board with no staleness note, and A's snapshot
feeds B's next diff. Nothing downstream catches it: the Draft Room's result guard compares
`pick_label`, which cannot tell two boards at one label apart (see
test_temporal_consistency_boundary), and the staleness note compares a pick COUNT and a data
date, both of which two leagues can share.

These tests drive the real function against a dict standing in for st.session_state, rather
than asserting on app.py's source text -- a source assertion would pass on a function that is
never called, which is the defect it would be pinning.
"""

from __future__ import annotations

import ast
import unittest

import draft_state
import ui_source

#: The UI surface as one text, via ui_source rather than a direct read of app.py. The Draft
#: Room is slated to move out of app.py by view, and a test that read that one file would go on
#: passing while the code it scans lived somewhere else -- which is the exact failure ui_source
#: exists to prevent, and which test_ui_source enforces.
UI_SOURCE = ui_source.text()


def _state_from_a_finished_draft() -> dict:
    """One league's worth of Draft Room state, as it stands after a debate has been run."""
    return {
        "draft_room_snapshot_cache": ("league-A-key", "A's board"),
        "draft_room_last_snapshot": "A's snapshot",
        "draft_room_debate_result": "A's debate",
        "draft_room_picks_by_draft": {"draftA": [{"player_id": "1"}]},
        "draft_room_context": "A's screen context",
        "mock_draft": "A's mock",
        "mock_draft_last_snapshot": "A's mock snapshot",
        "mock_draft_debate_result": "A's mock debate",
        "draft_room_pool_scope": "rookies",
        "draft_room_position_view": "RB",
        "mock_draft_pool_scope": "rookies",
        "selected_league_id": "A",
        "chat_history": ["A's chat"],
    }


class NothingComputedFromOneLeagueSurvivesTheSwitchTests(unittest.TestCase):

    def _cleared(self) -> dict:
        state = _state_from_a_finished_draft()
        draft_state.clear_league_derived(state)
        return state

    def test_the_three_keys_with_no_reset_path_anywhere_are_gone(self):
        """The finding, named key by key."""
        state = self._cleared()
        for key in ("draft_room_snapshot_cache", "draft_room_last_snapshot",
                    "draft_room_debate_result"):
            self.assertNotIn(key, state, key)

    def test_the_picks_and_the_screen_context_go_too(self):
        """A pick list and a rendered context are league data as much as a board is."""
        state = self._cleared()
        self.assertNotIn("draft_room_picks_by_draft", state)
        self.assertNotIn("draft_room_context", state)

    def test_the_mock_draft_goes_with_it(self):
        """A mock is built from one league's settings and format; carrying it into another
        league is the same leak wearing different clothes."""
        state = self._cleared()
        for key in ("mock_draft", "mock_draft_last_snapshot", "mock_draft_debate_result"):
            self.assertNotIn(key, state, key)

    def test_display_preferences_survive(self):
        """The non-vacuity arm, and the thing that makes this a repair rather than a reset
        button: a sweep that cleared everything would pass every assertion above while making
        a person re-pick their filters on every league switch."""
        state = self._cleared()
        self.assertEqual(state["draft_room_pool_scope"], "rookies")
        self.assertEqual(state["draft_room_position_view"], "RB")
        self.assertEqual(state["mock_draft_pool_scope"], "rookies")

    def test_state_outside_the_draft_room_is_not_touched(self):
        """activate_league owns chat and the league snapshot separately; this function must not
        reach past its own prefixes."""
        state = self._cleared()
        self.assertEqual(state["selected_league_id"], "A")
        self.assertEqual(state["chat_history"], ["A's chat"])

    def test_a_key_nobody_classified_is_cleared_rather_than_kept(self):
        """FAIL-SAFE BY DEFAULT, which is the property that makes this survive its author.

        A list of keys to delete is a second statement of what the Draft Room keeps, and it
        falls behind the first time a key is added -- which is exactly how three keys came to
        have no reset path at all. Clearing by prefix with a preference allowlist inverts that:
        a key added tomorrow is cleared without anyone remembering this file. The cost of
        getting it wrong runs the harmless way, a re-picked filter rather than a leaked board.
        """
        state = _state_from_a_finished_draft()
        state["draft_room_a_feature_invented_after_this_test"] = "league A's"
        draft_state.clear_league_derived(state)
        self.assertNotIn("draft_room_a_feature_invented_after_this_test", state)

    def test_clearing_an_already_clear_state_is_not_an_error(self):
        """activate_league runs on first load too, before any of this exists."""
        state = {"selected_league_id": "A"}
        self.assertEqual(draft_state.clear_league_derived(state), [])
        self.assertEqual(state, {"selected_league_id": "A"})


class TheResetIsActuallyWiredTests(unittest.TestCase):
    """A reset function nothing calls is the same defect with a nicer name."""

    def test_activate_league_calls_it(self):
        tree = ast.parse(ui_source.unit_containing("def activate_league("))
        activate = next(n for n in ast.walk(tree)
                        if isinstance(n, ast.FunctionDef) and n.name == "activate_league")
        called = {getattr(c.func, "attr", getattr(c.func, "id", None))
                  for c in ast.walk(activate) if isinstance(c, ast.Call)}
        self.assertIn("clear_league_derived", called)

    def test_every_preference_on_the_allowlist_is_under_a_swept_prefix(self):
        """An allowlist entry that no prefix would have caught is dead text -- it exempts
        nothing, and reading it would misdescribe what this function does."""
        stray = [k for k in draft_state.DRAFT_STATE_PREFERENCES
                 if not k.startswith(draft_state.DRAFT_STATE_PREFIXES)]
        self.assertEqual(stray, [])

    def test_every_preference_on_the_allowlist_is_a_real_key_in_app(self):
        """And an entry naming a key the UI does not use is a rename that left this behind,
        which would silently start leaking the renamed key."""
        missing = [k for k in draft_state.DRAFT_STATE_PREFERENCES if f'"{k}"' not in UI_SOURCE]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
