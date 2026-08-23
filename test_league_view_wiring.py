"""Structural regression checks for the League view (app.py, main_view == LEAGUE_VIEW).

Same constraint as the other *_wiring test files: app.py is a top-level Streamlit script, not
a cleanly importable module, so these are source-level checks. They exist to pin two things
found while propagating the shared Debate/context pattern into League:

1. The main nav used to be a plain if/elif/elif/else chain, where League was reached only by
   elimination (the bare else), not by an explicit `main_view == LEAGUE_VIEW` check. Turning
   that into an explicit elif is correct, but it exposed a latent gap: st.segmented_control
   without required=True can return None (clicking the already-active pill deselects it), which
   would now render nothing instead of silently falling into League. required=True closes that.
2. League's Debate chip and screen_context.build_league_context must consume the exact same
   row shape the roster table itself renders, not a second, independently-built read.
"""

import unittest
from pathlib import Path

_APP_SOURCE = Path(__file__).with_name("app.py").read_text()


class MainNavRequiredTests(unittest.TestCase):
    def test_main_view_segmented_control_is_required(self):
        start = _APP_SOURCE.index("main_view = st.segmented_control(")
        # A fixed window rather than index(")", start) -- the call's own explanatory comment
        # contains a literal ")" (part of a parenthetical), which would truncate the search
        # before reaching the real end of the call.
        call_text = _APP_SOURCE[start:start + 1200]
        self.assertIn("required=True", call_text)

    def test_league_view_is_reached_by_an_explicit_check(self):
        self.assertIn("elif main_view == LEAGUE_VIEW:", _APP_SOURCE)
        # The old bare "else:" catch-all for League must be gone -- explicit now, not
        # reached by eliminating the other three.
        self.assertNotIn("\nelse:\n    # ------------------------------------------------------------------ league rosters --", _APP_SOURCE)


class LeagueContextWiringTests(unittest.TestCase):
    def _league_block(self) -> str:
        start = _APP_SOURCE.index("elif main_view == LEAGUE_VIEW:")
        # The view block runs to end-of-file in practice (it's the last main_view branch),
        # but bound it at the debate-studio section marker to stay well inside the view.
        end = _APP_SOURCE.index("# ------------------------------------------------------------------ debate studio --", start)
        return _APP_SOURCE[start:end]

    def test_debate_chip_is_wired_via_the_shared_builder(self):
        block = self._league_block()
        self.assertIn("render_debate_chip(screen_context.build_league_context(selected_owner, context_rows), key=\"league\")", block)

    def test_context_rows_feed_both_the_table_and_the_context(self):
        block = self._league_block()
        # One shared list built once, reused by both pd.DataFrame(...) and
        # build_league_context(...) -- never two independently-constructed reads of the
        # same roster that could quietly drift apart.
        self.assertIn("context_rows = [", block)
        self.assertIn("pd.DataFrame(context_rows)", block)
        self.assertIn("build_league_context(selected_owner, context_rows)", block)

    def test_no_strength_score_language_anywhere_in_the_league_view(self):
        # The design-language reference's League hard contract: strength is an entry point,
        # never a conclusion. This view must never present a single rolled-up power number.
        block = self._league_block().lower()
        for banned in ("league strength score", "power score", "team strength rating"):
            self.assertNotIn(banned, block)


if __name__ == "__main__":
    unittest.main()
