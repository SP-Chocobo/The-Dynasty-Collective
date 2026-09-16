"""#206: survival_probability had TWO facts sharing one number, and 1.0 was the wrong one.

`estimate_survival` returned 1.0 both when the seat picks again immediately (genuinely certain)
and when the seat has NO further pick at all (no answer exists). Owner's ruling, 2026-09-16:
"if you physically do not have another pick in the draft then it returning an error stating
that there's issues calculating the chance of survival to your next pick is valid."

These tests drive the REAL producer. A fixture that hand-builds the return dict would pass
against a broken estimate_survival, which is the defect class this repo keeps finding in its
own tests.
"""
import unittest

import draft_strategy as ds


class SurvivalAbsenceContractTests(unittest.TestCase):
    #: seat "3" picks at index 2 and index 5. Index 5 is its LAST pick in the draft.
    ORDER = ["1", "2", "3", "1", "2", "3"]

    def _est(self, index, seat, order=None):
        return ds.estimate_survival([], {}, order or self.ORDER, index, seat, "p", {})

    def test_no_next_pick_is_None_not_one_point_zero(self):
        """The defect itself. 1.0 asserts 'certain to still be there' about a turn that will
        never come; None says the question does not arise."""
        r = self._est(5, "3")
        self.assertIsNone(r["survival_probability"])
        self.assertEqual(r["survival_basis"], ds.SURVIVAL_NO_NEXT_PICK)

    def test_no_next_pick_reports_no_gap_rather_than_a_gap_of_zero(self):
        """0 intervening picks is a MEASUREMENT (back-to-back). There is no gap to measure when
        there is no next turn, so the count is absent too."""
        self.assertIsNone(self._est(5, "3")["intervening_picks"])

    def test_back_to_back_is_still_a_real_one_point_zero(self):
        """The repair must not swallow the legitimate case: consecutive picks by the same seat
        mean every candidate survives BY ARITHMETIC. Distinguished only by its basis."""
        r = self._est(0, "9", order=["9", "9", "1"])
        self.assertEqual(r["survival_probability"], 1.0)
        self.assertEqual(r["survival_basis"], ds.SURVIVAL_NO_INTERVENING_PICKS)
        self.assertEqual(r["intervening_picks"], 0)

    def test_the_two_one_point_zero_cases_are_distinguishable(self):
        """Before the repair BOTH returned 1.0 with nothing to tell them apart -- that is the
        whole defect, so it gets its own test rather than living inside another assertion."""
        no_next = self._est(5, "3")
        back_to_back = self._est(0, "9", order=["9", "9", "1"])
        self.assertNotEqual(no_next["survival_basis"], back_to_back["survival_basis"])

    def test_opportunity_cost_is_absent_rather_than_zero_when_there_is_no_next_pick(self):
        """THE CONSEQUENCE THAT MADE THIS URGENT. opportunity_cost is tav * (1 - survival), so a
        forced 1.0 rendered 0.00 -- 'waiting costs you nothing' -- at the one moment waiting
        costs you the player permanently."""
        self.assertIsNone(ds._opportunity_cost(100.0, self._est(5, "3")["survival_probability"]))
        # and the arithmetic that WOULD have been shown, to make the inversion concrete
        self.assertEqual(ds._opportunity_cost(100.0, 1.0), 0.0)

    def test_every_returned_basis_token_has_a_human_label(self):
        """#126: one home for the vocabulary. A token with no label reaches a UI as a raw
        identifier, which is how a vocabulary silently grows a second home."""
        seen = {self._est(5, "3")["survival_basis"],
                self._est(0, "9", order=["9", "9", "1"])["survival_basis"],
                self._est(0, "1")["survival_basis"]}
        self.assertEqual(seen, set(ds.SURVIVAL_BASIS_LABELS))

    def test_a_measured_estimate_still_says_it_was_measured(self):
        r = self._est(0, "1")
        self.assertEqual(r["survival_basis"], ds.SURVIVAL_MEASURED)
        self.assertEqual(r["intervening_picks"], 2)


if __name__ == "__main__":
    unittest.main()
