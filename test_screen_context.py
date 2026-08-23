"""screen_context is a pure assembly layer -- these tests pin that every field is a direct
reshaping of already-computed arguments, and that to_prompt_seed never drops or reorders the
evidence a surface handed over."""

import unittest

from screen_context import ScreenContext, build_trade_context


class ScreenContextToPromptSeedTests(unittest.TestCase):
    def test_includes_surface_looking_at_decision_and_evidence(self):
        ctx = ScreenContext(
            surface="Trade Calculator", looking_at="Evaluating a trade.",
            decision="You send: X\nYou receive: Y", evidence="Favorable.",
        )
        seed = ctx.to_prompt_seed()
        self.assertIn("Current context: Trade Calculator", seed)
        self.assertIn("Evaluating a trade.", seed)
        self.assertIn("You send: X", seed)
        self.assertIn("Favorable.", seed)

    def test_entities_are_appended_when_present(self):
        ctx = ScreenContext(
            surface="X", looking_at="l", decision="d", evidence="e",
            entities=("Ja'Marr Chase", "Bijan Robinson"),
        )
        self.assertIn("Involved: Ja'Marr Chase, Bijan Robinson", ctx.to_prompt_seed())

    def test_no_entities_produces_no_involved_line(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e")
        self.assertNotIn("Involved:", ctx.to_prompt_seed())

    def test_guidance_appended_last_when_present(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e", guidance="Watch the bye weeks.")
        seed = ctx.to_prompt_seed()
        self.assertIn("Watch the bye weeks.", seed)
        self.assertTrue(seed.strip().endswith("Watch the bye weeks."))

    def test_no_guidance_by_default(self):
        ctx = ScreenContext(surface="X", looking_at="l", decision="d", evidence="e")
        self.assertIsNone(ctx.guidance)


class BuildTradeContextTests(unittest.TestCase):
    def test_partner_named_when_specified(self):
        ctx = build_trade_context(
            trade_partner="Roster 9", send_description="  - Chase", receive_description="  - Bijan",
            entities=["Chase", "Bijan"], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("Roster 9", ctx.looking_at)

    def test_not_specified_partner_omitted_from_looking_at(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertNotIn("Not specified", ctx.looking_at)

    def test_send_and_receive_descriptions_pass_through_unmodified(self):
        ctx = build_trade_context(
            trade_partner="Not specified",
            send_description="  - Ja'Marr Chase (value: 92)",
            receive_description="  - Bijan Robinson (value: 88)",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("Ja'Marr Chase (value: 92)", ctx.decision)
        self.assertIn("Bijan Robinson (value: 88)", ctx.decision)

    def test_empty_side_reads_as_nothing_added_yet_not_blank(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="", receive_description="",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("nothing added yet", ctx.decision)

    def test_all_three_verdict_lines_included_when_present(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y", entities=[],
            raw_line="Raw: favorable", fit_line="Fit: neutral", overall="Overall: depends",
        )
        self.assertIn("Raw: favorable", ctx.evidence)
        self.assertIn("Fit: neutral", ctx.evidence)
        self.assertIn("Overall: depends", ctx.evidence)

    def test_no_verdicts_reads_as_no_priced_assets_yet(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="", receive_description="",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertIn("No priced assets to compare yet", ctx.evidence)

    def test_entities_pass_through_as_a_tuple(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=["A", "B", "C"], raw_line=None, fit_line=None, overall=None,
        )
        self.assertEqual(ctx.entities, ("A", "B", "C"))

    def test_surface_is_always_trade_calculator(self):
        ctx = build_trade_context(
            trade_partner="Not specified", send_description="x", receive_description="y",
            entities=[], raw_line=None, fit_line=None, overall=None,
        )
        self.assertEqual(ctx.surface, "Trade Calculator")

    def test_full_round_trip_reads_naturally_through_to_prompt_seed(self):
        ctx = build_trade_context(
            trade_partner="Roster 9", send_description="  - Ja'Marr Chase (value: 92)",
            receive_description="  - Bijan Robinson (value: 88)\n  - Puka Nacua (value: 79)",
            entities=["Ja'Marr Chase", "Bijan Robinson", "Puka Nacua"],
            raw_line="🟢 Materially favorable — you'd be receiving 45% more value.",
            fit_line="⚪ Roughly neutral — no meaningful shift in positional depth either way.",
            overall="↔️ Depends on your objective — Raw Value and Roster Fit point in different directions.",
        )
        seed = ctx.to_prompt_seed()
        self.assertIn("Current context: Trade Calculator", seed)
        self.assertIn("Roster 9", seed)
        self.assertIn("Ja'Marr Chase (value: 92)", seed)
        self.assertIn("Materially favorable", seed)
        self.assertIn("Depends on your objective", seed)
        self.assertIn("Involved: Ja'Marr Chase, Bijan Robinson, Puka Nacua", seed)


if __name__ == "__main__":
    unittest.main()
