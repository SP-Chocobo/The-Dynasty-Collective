"""Structural regression checks for Maintenance's Attention Ledger (app.py, main_view ==
MAINTENANCE_VIEW's opening section).

Same constraint as the other *_wiring test files: app.py is a top-level Streamlit script, not
a cleanly importable module, so these are source-level checks. They pin the settled Maintenance
concept: N-C (one lightweight strip, existing sections unchanged beneath it) is the baseline,
and its one real risk -- the strip quietly growing into a second ranking/opinion engine -- is
guarded against explicitly.
"""

import unittest
from pathlib import Path

_APP_SOURCE = Path(__file__).with_name("app.py").read_text()


def _ledger_block() -> str:
    start = _APP_SOURCE.index("elif main_view == MAINTENANCE_VIEW:")
    end = _APP_SOURCE.index("# ------------------------------------------------------------------ free agents --", start)
    return _APP_SOURCE[start:end]


class AttentionLedgerWiringTests(unittest.TestCase):
    def test_ledger_sits_before_free_agents_not_inside_it(self):
        # The strip is page-level framing, not a Free Agents feature -- it must render before
        # that section's own subheader, not be threaded into it.
        ledger_start = _APP_SOURCE.index("elif main_view == MAINTENANCE_VIEW:")
        free_agents_subheader = _APP_SOURCE.index('st.subheader("Free Agents")')
        self.assertLess(ledger_start, free_agents_subheader)

    def test_existing_three_sections_are_not_restructured(self):
        # N-B (tabbed lanes) was explicitly set aside -- Free Agents, Trade Calculator, and
        # Reference Material must still all render unconditionally in sequence, never behind
        # a segmented_control/tab picker.
        self.assertIn('st.subheader("Free Agents")', _APP_SOURCE)
        self.assertIn('hcol1.subheader("Trade Calculator")', _APP_SOURCE)
        self.assertIn('st.subheader("Reference Material")', _APP_SOURCE)

    def test_fa_staleness_chip_reuses_the_existing_merger_flags(self):
        block = _ledger_block()
        self.assertIn("merger.is_free_agents_loaded and merger.free_agents_is_stale", block)
        self.assertIn("merger.free_agents_staleness_days", block)

    def test_uncaptioned_count_reuses_list_attachments_not_a_new_reader(self):
        block = _ledger_block()
        self.assertIn("list_attachments()", block)
        self.assertIn('not a["caption"].strip()', block)

    def test_thin_position_reuses_shared_depth_ratings_judgment(self):
        block = _ledger_block()
        self.assertIn("depth_ratings.depth_label(", block)
        self.assertIn("positional_depth(player_universe, merger)", block)

    def test_thin_position_phrasing_matches_matchups_shared_grammar(self):
        # Same "Thin at X" phrasing Matchup's readiness strip uses -- one shared vocabulary
        # for the same judgment, not a second wording invented for this surface.
        block = _ledger_block()
        self.assertIn('f"Thin at {', block)

    def test_never_ranks_or_names_a_specific_top_free_agent(self):
        # The guardrail from the concept doc: this strip may state facts (staleness, a count,
        # a thin-position label) but must never pick a "best" free agent -- that would be a
        # ranking invented for the queue, not a read of an existing one. Checking for actual
        # code patterns, not the bare phrase -- this block's own comment legitimately names
        # "top FA by need" while explaining that it's NOT what this code does.
        block = _ledger_block().lower()
        for banned in ("top_fa", "best_available", "priority_score", "queue_score", "sort_rows_by_column"):
            self.assertNotIn(banned, block)

    def test_ledger_is_conditional_on_having_something_to_say(self):
        # An empty ledger renders nothing rather than an empty strip -- N-C's own "quiet unless
        # there's something to say" framing.
        block = _ledger_block()
        self.assertIn("if _attn_chips:", block)


if __name__ == "__main__":
    unittest.main()
