"""Structural regression checks for Maintenance's Attention Ledger (app.py, main_view ==
MAINTENANCE_VIEW's opening section).

Same constraint as the other *_wiring test files: app.py is a top-level Streamlit script, not
a cleanly importable module, so these are source-level checks. They pin the settled Maintenance
concept: N-C (one lightweight strip, existing sections unchanged beneath it) is the baseline,
and its one real risk -- the strip quietly growing into a second ranking/opinion engine -- is
guarded against explicitly.
"""

import unittest

import ui_source

_APP_SOURCE = ui_source.text()


def _ledger_block() -> str:
    return ui_source.block(
        "elif main_view == MAINTENANCE_VIEW:",
        "# ------------------------------------------------------------------ free agents --")


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


class TradeTotalsAbsenceTests(unittest.TestCase):
    """The Trade Calculator's metric cards must not price an unpriced side at zero.

    Reproduction, before the fix: one misspelled name in each box gave "0 / 0 / +0%" in cards
    labelled You send / You receive / Balance, directly beneath the caption that correctly
    said nothing had matched. `sum(... if r["value"] is not None)` returns 0 over an all-absent
    side, and the verdict line below was the only thing guarded."""

    def _calc_block(self) -> str:
        return ui_source.block('hcol1.subheader("Trade Calculator")', "def _describe_trade_side(")

    def test_a_side_total_is_absent_when_no_row_on_it_is_priced(self):
        block = self._calc_block()
        self.assertIn("trade_send_total = sum(send_priced) if send_priced else None", block)
        self.assertIn("trade_receive_total = sum(receive_priced) if receive_priced else None", block)
        # The bare sums that produced a zero out of nothing must not come back.
        self.assertNotIn('trade_send_total = sum(r["value"] for r in trade_send_rows', block)
        self.assertNotIn('trade_receive_total = sum(r["value"] for r in trade_receive_rows', block)

    def test_the_cards_render_the_absence_rather_than_a_number(self):
        block = self._calc_block()
        self.assertIn('mcol1.metric("You send", _side_total_text(trade_send_total))', block)
        self.assertIn('mcol2.metric("You receive", _side_total_text(trade_receive_total))', block)
        self.assertIn("if both_sides_priced else TRADE_BALANCE_NOT_COMPUTABLE", block)
        self.assertNotIn('mcol1.metric("You send", f"{trade_send_total:.0f}")', block)

    def test_a_measured_zero_still_renders_as_a_plain_number(self):
        # It is the LIST of priced rows that decides whether a total exists, never its sum --
        # a side whose priced assets really do add to 0 is measured, and prints 0.
        block = self._calc_block()
        self.assertIn('send_priced = [r["value"] for r in trade_send_rows if r["value"] is not None]', block)
        self.assertIn('return f"{total:.0f}" if total is not None else TRADE_SIDE_UNPRICED', block)

    def test_the_replacement_says_why_rather_than_blanking_the_card(self):
        block = self._calc_block()
        self.assertIn("Not computable — nothing on the", block)
        self.assertIn("is priced", block)

    def test_no_percentage_is_derived_from_a_side_that_has_no_total(self):
        block = self._calc_block()
        self.assertIn("larger_total = delta = delta_pct = None", block)
        self.assertNotIn("delta_pct = (abs(delta) / larger_total * 100) if larger_total else 0.0\n        favorable = delta > 0\n", block)


class DepthLabelVocabularyTests(unittest.TestCase):
    """depth_ratings owns the label vocabulary; this surface consumes it and never respells it.

    The literal "None — no rostered players here" lived in four places and failed
    ASYMMETRICALLY: rename the producer and the two membership tests go quietly silent, while
    _DEPTH_RANK's `.get(label, 2)` silently reclassifies every empty position room as a
    measured, mid-league "Average"."""

    def test_the_surface_never_respells_the_producers_labels(self):
        self.assertNotIn("None — no rostered players here", _APP_SOURCE)
        self.assertIn("depth_ratings.NO_PLAYERS_LABEL", _APP_SOURCE)
        self.assertIn("depth_ratings.THIN_LABELS", _APP_SOURCE)

    def test_an_unmeasurable_depth_is_excluded_from_fit_never_defaulted_to_average(self):
        block = ui_source.block('hcol1.subheader("Trade Calculator")', "def _describe_trade_side(")
        self.assertIn("before_rank = _DEPTH_RANK.get(before_label)", block)
        self.assertIn("after_rank = _DEPTH_RANK.get(after_label)", block)
        self.assertIn("if before_rank is None or after_rank is None:", block)
        # The default that turned a documented "cannot be measured" into a measured Average.
        self.assertNotIn("_DEPTH_RANK.get(before_label, 2)", block)
        self.assertNotIn("_DEPTH_RANK.get(after_label, 2)", block)

    def test_a_fit_verdict_is_withheld_when_nothing_was_measurable(self):
        block = ui_source.block('hcol1.subheader("Trade Calculator")', "def _describe_trade_side(")
        self.assertIn("if not measured_positions:", block)
        self.assertIn("⚪ Not computable — no league-wide depth data at", block)


if __name__ == "__main__":
    unittest.main()
