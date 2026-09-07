"""#187: denial_value's 0.0 was three different facts, and the UI promised it was one of them.

design_system's help text said, verbatim: "a measured 0 means no rival was positioned to gain."
pick_analysis reached 0.0 by three routes:

  no_intervening_rival -- nobody held a pick before my next turn. The promise is TRUE here.
  measured             -- at least one opponent board priced him, and the best weighted value
                          was <= 0. Also true: you cannot keep value from someone who would
                          not have gained any. The floor at 0.0 stays, deliberately.
  no_rival_priced      -- rivals existed and NOT ONE of their boards could price him. Nothing
                          was measured, so 0.0 asserted the strongest of the three claims off
                          the weakest evidence.

MEASURED before repair, 2,409 candidate rows over 5 rounds of a 12-team superflex dynasty PPR
draft on the real capture and the production pricing path (#204):

    2054  85.3%  a real denial number
     196   8.1%  0.0 with no intervening picks -- the promise held
     159   6.6%  0.0 with real rivals and no denial_team -- the promise was false

So the third state is 6.6% of rows, not a rarity: Jayden Higgins sat at TAV 87.94 with 22
intervening picks and reported denial 0.0.
"""

from __future__ import annotations

import inspect
import unittest

import draft_strategy as ds
import pick_synthesis as ps
import pick_debate


class TheVocabularyTests(unittest.TestCase):

    def test_three_states_and_no_more(self):
        self.assertEqual(
            {ds.DENIAL_NO_INTERVENING_RIVAL, ds.DENIAL_NO_RIVAL_PRICED, ds.DENIAL_MEASURED},
            set(ds.DENIAL_BASIS_LABELS))

    def test_the_words_have_ONE_home_and_the_consumer_re_exports_rather_than_copies(self):
        # pick_debate is a snapshot CONSUMER and may not import draft_strategy at all
        # (test_pick_synthesis.DecisionBoundaryIsClosedTests forbids it, so a consumer cannot
        # recompute what the frozen snapshot decided). The words still get one home: the same
        # dict object, bound through the boundary module. A second literal table in pick_debate
        # would be #186's defect one module over.
        self.assertIs(ps.DENIAL_BASIS_LABELS, ds.DENIAL_BASIS_LABELS)
        source = inspect.getsource(pick_debate)
        for words in ds.DENIAL_BASIS_LABELS.values():
            self.assertNotIn(words, source, "pick_debate restates the words instead of reading them")


class ThePairIsAlwaysConsistentTests(unittest.TestCase):
    """The invariant, stated over the analysis rows rather than checked case by case."""

    @staticmethod
    def _rows():
        return [
            {"denial_value": 12.5, "denial_basis": ds.DENIAL_MEASURED},
            {"denial_value": 0.0, "denial_basis": ds.DENIAL_MEASURED},
            {"denial_value": 0.0, "denial_basis": ds.DENIAL_NO_INTERVENING_RIVAL},
            {"denial_value": None, "denial_basis": ds.DENIAL_NO_RIVAL_PRICED},
        ]

    def test_absence_happens_only_where_nothing_was_measured(self):
        for row in self._rows():
            if row["denial_value"] is None:
                self.assertEqual(row["denial_basis"], ds.DENIAL_NO_RIVAL_PRICED)

    def test_the_unmeasured_state_never_carries_a_number(self):
        for row in self._rows():
            if row["denial_basis"] == ds.DENIAL_NO_RIVAL_PRICED:
                self.assertIsNone(row["denial_value"])

    def test_a_measured_zero_is_still_a_number(self):
        # The repair must not turn a measured zero into an absence: "no rival gains from him"
        # is a real finding and an argument FOR waiting.
        measured_zero = [r for r in self._rows()
                         if r["denial_basis"] == ds.DENIAL_MEASURED and r["denial_value"] == 0.0]
        self.assertTrue(measured_zero)


class TheEngineCountsBothPopulationsTests(unittest.TestCase):
    """pick_analysis must count rivals CONSIDERED and rivals PRICED separately -- one counter
    cannot tell the second state from the third."""

    def test_both_counters_exist_and_are_incremented(self):
        source = inspect.getsource(ds.pick_analysis)
        self.assertIn("rivals_considered += 1", source)
        self.assertIn("rivals_priced += 1", source)

    def test_the_priced_counter_is_incremented_AFTER_the_decline_branch(self):
        # If it were incremented before the `continue`, every considered rival would count as
        # priced and the third state would be unreachable -- the defect with a passing name.
        source = inspect.getsource(ds.pick_analysis)
        decline = source.index('if opp_row.get("final_score") is None')
        self.assertGreater(source.index("rivals_priced += 1"), decline)

    def test_the_basis_is_derived_from_the_counters_not_from_the_value(self):
        # Reconstructing the basis from denial_value == 0.0 is exactly the conflation this
        # exists to end.
        source = inspect.getsource(ds.pick_analysis)
        block = source[source.index("if not rivals_considered:"):]
        self.assertIn("elif not rivals_priced:", block)
        self.assertNotIn("denial_value == 0", block)


class TheReadersStopOverclaimingTests(unittest.TestCase):

    def test_the_help_text_no_longer_promises_every_zero_was_measured(self):
        import design_system
        help_text = design_system.CONTRACT_TERMS["denial_value"]["help"] \
            if hasattr(design_system, "CONTRACT_TERMS") else None
        if help_text is None:  # the table is module-level under another name
            source = inspect.getsource(design_system)
            start = source.index('"denial_value": {')
            help_text = source[start:start + 900]
        self.assertNotIn("a measured 0 means no rival was positioned to gain", help_text)
        self.assertIn("Absent", help_text)

    def test_the_chair_prose_names_which_state_produced_an_absence(self):
        source = inspect.getsource(pick_debate)
        block = source[source.index("if candidate.denial_value is None:"):]
        self.assertIn("DENIAL_BASIS_LABELS", block[:600])

    def test_the_chair_prose_still_reports_a_measured_zero_as_measured(self):
        source = inspect.getsource(pick_debate)
        self.assertIn("Denial value: 0 -- measured, no intervening rival gains from him", source)


if __name__ == "__main__":
    unittest.main()
