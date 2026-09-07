"""trade_ledger_ui is a pure formatting layer -- these tests pin exactly that: every function
returns a direct textual reshaping of its arguments, never a new computed value."""

import unittest

import design_system
import trade_ledger_ui as ui


class FreshnessPillTests(unittest.TestCase):
    def test_a_measured_zero_day_age_reads_current(self):
        # A real, measured "loaded today" -- the positive green assertion is earned here.
        self.assertIn("Values current", ui.freshness_pill(False, 0))
        self.assertIn("tl-pill fresh", ui.freshness_pill(False, 0))

    def test_unknown_age_is_its_own_state_not_the_green_current_pill(self):
        # data_merger._compute_freshness returns (None, None, False) for an empty frame or one
        # with no source_date column -- "we do not know how old this is." That used to fall
        # through to "Values current", turning an absence into a positive assertion on two
        # surfaces whose captions tell the reader to check this pill when something looks off.
        html = ui.freshness_pill(False, None)
        self.assertIn("age unknown", html)
        self.assertIn("tl-pill unknown", html)
        self.assertNotIn("Values current", html)
        self.assertNotIn("tl-pill fresh", html)

    def test_stale_with_known_age_shows_the_day_count(self):
        html = ui.freshness_pill(True, 9)
        self.assertIn("Values 9d stale", html)
        self.assertIn("tl-pill stale", html)

    def test_stale_with_unknown_age_reads_unknown_not_current(self):
        # Nothing to report a day count against. It is not "stale" (no number to state) and it
        # is certainly not "current" -- it is unknown, which is what it now says.
        html = ui.freshness_pill(True, None)
        self.assertIn("age unknown", html)
        self.assertNotIn("Values current", html)

    def test_the_fresh_tint_is_mixed_from_the_token_never_a_hand_copied_literal(self):
        # rgba(22,163,74,.12) is #16a34a; TOKENS["emerald"] is #1a9e4b -- the literal had
        # already drifted off the token it was meant to be. The stale rule beside it was
        # already color-mixed from its own token, with a comment saying why.
        self.assertIn("color-mix(in srgb, var(--emerald) 12%, transparent)", ui.TRADE_LEDGER_CSS)
        self.assertNotIn("rgba(22,163,74", ui.TRADE_LEDGER_CSS)

    def test_the_type_stack_is_the_shared_one_not_a_hand_copy(self):
        # Same class of defect as the tint above: a stack copied per rule is a stack that can
        # lose its fallback in one place and not the others.
        self.assertIn(design_system.FONT_MONO, ui.TRADE_LEDGER_CSS)
        self.assertNotIn("__DESIGN_SYSTEM_FONT_MONO__", ui.TRADE_LEDGER_CSS)
        self.assertEqual(ui.TRADE_LEDGER_CSS.count("DejaVu Sans Mono"), 2)

    def test_never_names_a_vendor(self):
        for html in (ui.freshness_pill(True, 5), ui.freshness_pill(False, 0)):
            for vendor in ("Draft Sharks", "Trade Value Chart", "Dynasty Rankings"):
                self.assertNotIn(vendor, html)


class AssetLabelHtmlTests(unittest.TestCase):
    def test_player_with_team(self):
        html = ui.asset_label_html("Ja'Marr Chase", "WR", "CIN", is_pick=False)
        self.assertIn("Ja'Marr Chase", html)
        self.assertIn("WR · CIN", html)
        self.assertNotIn("tl-pickbadge", html)

    def test_player_without_team(self):
        html = ui.asset_label_html("Free Agent Guy", "RB", None, is_pick=False)
        self.assertIn("RB", html)
        self.assertNotIn("·", html)

    def test_pick_shows_badge_and_skips_team(self):
        html = ui.asset_label_html("2027 Rd 1 (via Roster 9)", "PICK", None, is_pick=True)
        self.assertIn("tl-pickbadge", html)
        self.assertIn("PICK", html)


class ValueHtmlTests(unittest.TestCase):
    def test_present_value_formatted_to_whole_number(self):
        self.assertIn("92", ui.value_html(92.4))

    def test_none_value_renders_dim_dash_not_zero(self):
        html = ui.value_html(None)
        self.assertIn("—", html)
        self.assertIn("tl-dim", html)
        self.assertNotIn("0", html)


class SelectedTagHtmlTests(unittest.TestCase):
    def test_send_side(self):
        self.assertIn("SENDING", ui.selected_tag_html("send"))

    def test_receive_side(self):
        self.assertIn("RECEIVING", ui.selected_tag_html("receive"))


class OverallSynthesisTests(unittest.TestCase):
    def test_both_directional_and_matching_reads_as_agreement(self):
        result = ui.overall_synthesis("favorable", "favorable")
        self.assertIn("agree", result)
        self.assertIn("favorable", result)

    def test_both_directional_and_opposite_reads_as_depends_on_objective(self):
        result = ui.overall_synthesis("favorable", "unfavorable")
        self.assertIn("Depends on your objective", result)

    def test_balanced_and_neutral_is_the_fully_even_case(self):
        result = ui.overall_synthesis("Balanced", "neutral")
        self.assertIn("essentially even", result)

    def test_directional_raw_with_neutral_fit_credits_raw_alone(self):
        result = ui.overall_synthesis("favorable", "neutral")
        self.assertIn("numbers alone", result)

    def test_balanced_raw_with_directional_fit_credits_fit_alone(self):
        result = ui.overall_synthesis("Balanced", "unfavorable")
        self.assertIn("roster construction alone", result)

    def test_missing_raw_verdict_returns_none(self):
        self.assertIsNone(ui.overall_synthesis(None, "favorable"))

    def test_missing_fit_verdict_returns_none(self):
        self.assertIsNone(ui.overall_synthesis("favorable", None))

    def test_both_missing_returns_none(self):
        self.assertIsNone(ui.overall_synthesis(None, None))

    def test_never_treats_either_verdict_as_the_master_read(self):
        # Symmetry check: swapping which side is "favorable" and which is "unfavorable"
        # produces the same disagreement framing either way, not a different message
        # depending on which argument position carries the stronger verdict.
        a = ui.overall_synthesis("favorable", "unfavorable")
        b = ui.overall_synthesis("unfavorable", "favorable")
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
