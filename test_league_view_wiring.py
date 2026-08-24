"""Structural regression checks for the League view (app.py, main_view == LEAGUE_VIEW).

Same constraint as the other *_wiring test files: app.py is a top-level Streamlit script, not
a cleanly importable module, so these are source-level checks. They exist to pin:

1. The main nav used to be a plain if/elif/elif/else chain, where League was reached only by
   elimination (the bare else), not by an explicit `main_view == LEAGUE_VIEW` check. Turning
   that into an explicit elif is correct, but it exposed a latent gap: st.segmented_control
   without required=True can return None (clicking the already-active pill deselects it), which
   would now render nothing instead of silently falling into League. required=True closes that.
2. League's Debate chip and screen_context.build_league_context must consume the exact same
   row shape the roster table itself renders, not a second, independently-built read.
3. Fable's League design review (F1-F6): the Standings Ladder (A) and Depth Map (B) must read
   as ONE decision surface, not two dashboards -- asymmetric home/secondary lens, one shared
   decomposition panel, continuous team selection across the toggle, and no invented score at
   any level (team strength, positional strength, or a record/asset composite).
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
        self.assertIn('render_debate_chip(screen_context.build_league_context(team_label, context_rows), key="league")', block)

    def test_context_rows_feed_both_the_table_and_the_context(self):
        block = self._league_block()
        # One shared list built once, reused by both pd.DataFrame(...) and
        # build_league_context(...) -- never two independently-constructed reads of the
        # same roster that could quietly drift apart.
        self.assertIn("context_rows = [", block)
        self.assertIn("pd.DataFrame(context_rows)", block)
        self.assertIn("build_league_context(team_label, context_rows)", block)

    def test_no_strength_score_language_anywhere_in_the_league_view(self):
        # The design-language reference's League hard contract: strength is an entry point,
        # never a conclusion. This view must never present a single rolled-up power number.
        block = self._league_block().lower()
        for banned in ("league strength score", "power score", "team strength rating"):
            self.assertNotIn(banned, block)


class AntiTwoDashboardContractTests(unittest.TestCase):
    """Pins the three structural properties Fable's review named as the difference between
    one coherent A/B surface and two dashboards bolted together."""

    def _league_block(self) -> str:
        start = _APP_SOURCE.index("elif main_view == LEAGUE_VIEW:")
        end = _APP_SOURCE.index("# ------------------------------------------------------------------ debate studio --", start)
        return _APP_SOURCE[start:end]

    def test_asymmetry_home_lens_follows_a_real_fact_not_a_third_mode(self):
        block = self._league_block()
        # The home lens is decided by games_played_total (a real fact), not a standalone
        # third UI mode, and Standings is the default once games exist.
        self.assertIn("games_played_total = sum(", block)
        self.assertIn('LADDER_LENS if season_started else DEPTH_LENS', block)
        # Exactly one toggle control choosing between the two lenses -- not two separately
        # rendered, co-equal, always-visible panels.
        self.assertEqual(block.count('st.segmented_control(\n        "League lens"'), 1)

    def test_zero_zero_state_is_named_honestly(self):
        block = self._league_block()
        self.assertIn("0-0", block)
        self.assertIn("season_started", block)

    def test_both_lenses_route_selection_into_one_shared_state_key(self):
        block = self._league_block()
        # Ladder (row click) and Depth Map (cell click) both write the SAME session_state key
        # -- the mechanism that makes selection continuous across the toggle. Both branches
        # assign to it, and there's no separate lens-specific selection key anywhere.
        self.assertEqual(block.count("st.session_state.league_selected_team = clicked_team"), 2)
        self.assertNotIn("ladder_selected_team", block)
        self.assertNotIn("depth_map_selected_team", block)

    def test_decomposition_panel_is_not_duplicated_per_lens(self):
        block = self._league_block()
        # The team decomposition (divergence read, pick capital, roster table, debate chip,
        # crosslink) appears once, driven by the shared selection -- not once per lens branch.
        self.assertEqual(block.count("pick_ledger = build_pick_ledger(snapshot)"), 1)
        self.assertEqual(block.count("render_debate_chip(screen_context.build_league_context"), 1)
        self.assertEqual(block.count('st.button("↔ Open in Trade Calculator"'), 1)

    def test_depth_map_reuses_the_shared_depth_ratings_module(self):
        block = self._league_block()
        # F3: the Depth Map's cell coloring must consume the exact same judgment the Trade
        # Calculator uses -- not a second, independently-tuned opinion.
        self.assertIn("depth_ratings.depth_label(cell, peer_cells)", block)

    def test_divergence_read_is_a_rank_comparison_not_a_new_score(self):
        block = self._league_block()
        # F2: compares two already-existing facts (win rank, asset-value rank) and only ever
        # prints a sentence -- never assigns the comparison to a persisted/composite score field.
        self.assertIn("win_rank_order = [row[\"team\"] for row in standings]", block)
        self.assertIn("value_rank_order = sorted(", block)
        self.assertNotIn("composite_score", block)
        self.assertNotIn("power_score", block)

    def test_pick_capital_reuses_existing_ledger_and_pricing_machinery(self):
        block = self._league_block()
        # F4: no second inventory system -- reuses build_pick_ledger and merger.pick_value
        # exactly as the Trade Calculator and LLM context builder already do.
        self.assertIn("pick_ledger = build_pick_ledger(snapshot)", block)
        self.assertIn("merger.pick_value(", block)

    def test_crosslink_is_the_one_navigation_mechanism_reusing_trade_calculator(self):
        block = self._league_block()
        # F6: exactly one crosslink, reusing the Trade Calculator's own partner selectbox key
        # -- never a second, competing handoff/navigation system.
        self.assertIn("st.session_state.trade_calc_partner = team_label", block)
        self.assertIn("st.session_state.pending_main_view = MAINTENANCE_VIEW", block)
        self.assertIn('team_label != my_team_label', block)

    def test_pending_main_view_is_consumed_before_the_widget_is_instantiated(self):
        # The crosslink can't set st.session_state.main_view directly from inside another
        # view's branch (that branch runs after main_view's own segmented_control has already
        # been instantiated this run -- Streamlit forbids writing a widget's key after
        # instantiation). Pin that the consumption happens strictly before that widget call.
        consume_at = _APP_SOURCE.index('st.session_state.main_view = st.session_state.pop("pending_main_view")')
        widget_at = _APP_SOURCE.index('main_view = st.segmented_control(')
        self.assertLess(consume_at, widget_at)


if __name__ == "__main__":
    unittest.main()
