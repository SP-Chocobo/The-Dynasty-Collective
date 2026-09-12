"""#251: the certification claim is "invariants hold across the configuration space", and that
sentence is only meaningful if the split between the two halves cannot drift.

`#250` measured the same roster under two rulebooks and the verdict inverted. The correction is
NOT to crown Fourth and Forever as the canonical league in place of PPR -- it is to stop reading
any single configuration's outcome as evidence about the engine, and to say which claims were
ever configuration-free.

`config_space` derives that split from `draft_battery`'s own structure rather than declaring it.
These tests defend the derivation, the reasons attached to it, and the two ways the coverage
instrument has already been wrong.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import config_space as cs
import draft_battery as db


class TheSplitIsDerivedAndComplete(unittest.TestCase):
    def test_the_invariant_set_is_what_structural_findings_aggregates(self):
        """Not a list I wrote. `structural_findings`' contract is "a finding here is a DEFECT,
        not an observation", so whatever it calls IS the invariant set."""
        self.assertEqual(cs.invariant_audits(),
                         ["duplicate_picks", "undraftable_positions", "unfilled_starting_slots",
                          "unpriced_picks"])

    def test_every_invariant_states_the_domain_it_is_asserted_over(self):
        """An invariant with a precondition is still an invariant. An invariant with an UNSTATED
        precondition is a trap: `unfilled_starting_slots` cannot hold when the draft is shorter
        than the roster, and `structural_findings` already takes `audit_roster_fill` to say so."""
        for name, domain in cs.classification()["invariants"].items():
            with self.subTest(name):
                self.assertTrue(domain, f"{name} is asserted as configuration-free with no "
                                        f"stated domain")
                self.assertIn("configuration", domain.lower())

    def test_every_configuration_dependent_outcome_states_why_it_may_move(self):
        for name, reason in cs.classification()["configuration_dependent"].items():
            with self.subTest(name):
                self.assertTrue(reason, f"{name} is reported with no reason for why a different "
                                        f"league may legitimately produce a different number")

    def test_nothing_is_in_both_halves(self):
        cls = cs.classification()
        self.assertEqual(set(cls["invariants"]) & set(cls["configuration_dependent"]), set())

    def test_both_halves_are_non_empty(self):
        """Non-vacuity: every test above loops, and would pass over an empty mapping."""
        cls = cs.classification()
        self.assertGreaterEqual(len(cls["invariants"]), 4)
        self.assertGreaterEqual(len(cls["configuration_dependent"]), 5)

    def test_a_new_audit_with_no_declaration_fails_loudly(self):
        """The ratchet. Add an audit to `structural_findings` and forget to say why it is
        configuration-free, and this is what stops the certification claim from quietly
        widening to cover something nobody argued for."""
        real = cs.invariant_audits
        cs.invariant_audits = lambda: real() + ["an_undeclared_new_audit"]
        try:
            domains = cs.classification()["invariants"]
            self.assertIsNone(domains["an_undeclared_new_audit"],
                              "an undeclared audit must surface as having no domain")
        finally:
            cs.invariant_audits = real


class TheCoverageInstrumentIsHonest(unittest.TestCase):
    def test_the_matrix_is_built_the_way_the_battery_builds_it(self):
        """The bug this instrument shipped with, and the #241 failure mode in a new file.
        `league_matrix()` with no base_scoring produces arms carrying only `rec`, because #213's
        repair is to pass the captured rulebook IN. Measuring against the bare matrix reported
        sixty keys as uncovered that every real arm carries."""
        bare = db.league_matrix()
        real = db.league_matrix(__import__("run_draft_battery").scoring_settings_from_capture())
        self.assertLess(len(bare[0]["league"]["scoring_settings"]), 5)
        self.assertGreater(len(real[0]["league"]["scoring_settings"]), 30)
        cov = cs.coverage(reference_leagues=cs.reference_leagues())
        self.assertGreater(cov["axes"], 50,
                           "coverage measured against the bare matrix sees ~18 axes, not ~91")

    def test_an_absent_scoring_key_is_not_a_zero(self):
        """The absence contract (#61/#187) applied to configuration coordinates. `bonus_rec_te`
        missing means no TE premium; `bonus_rec_te: 0.0` means one declared worth nothing.
        Folding them made the TE-premium axis read CONSTANT across a matrix that varies it."""
        declared_zero = cs._league_axes({"scoring_settings": {"bonus_rec_te": 0.0}})
        absent = cs._league_axes({"scoring_settings": {}}, {"scoring:bonus_rec_te"})
        # THE PROPERTY IS THAT THE TWO DIFFER. Asserting each against its own expected value
        # passes when ABSENT is redefined AS 0.0 -- the exact mutation this guards, which
        # survived the first version of this test.
        self.assertNotEqual(declared_zero["scoring:bonus_rec_te"],
                            absent["scoring:bonus_rec_te"],
                            "a declared zero and an absent key must not collapse onto one value")
        self.assertEqual(declared_zero["scoring:bonus_rec_te"], 0.0)
        self.assertIn("scoring:bonus_rec_te",
                      cs.coverage(reference_leagues=cs.reference_leagues())["varied"])

    def test_the_fixture_covers_itself_and_that_is_the_point(self):
        """The tautology made visible. The matrix is built FROM the fixture capture, so the
        fixture has zero uncovered coordinates by construction -- which is exactly why its
        coverage was never evidence about anything else."""
        cov = cs.coverage(reference_leagues=cs.reference_leagues())
        fixture = cov["uncovered_by_reference_league"]["sleeper_fixture"]
        self.assertEqual(fixture["value_never_produced"], {})

    def test_the_captured_league_is_in_the_matrix_as_a_configuration_point(self):
        """INVERTED (#251). This test used to assert that F&F's coordinates were UNCOVERED --
        `rec_fd`, `rush_fd`, `bonus_rec_te`, `slot:TAXI`, 21 of them. It was a characterization
        of a gap, and the gap is closed by adding the capture as one arm. Inverted rather than
        deleted, as the repo's posture requires, because the pair of assertions is the record."""
        import run_draft_battery as rdb
        matrix = db.league_matrix(rdb.scoring_settings_from_capture())
        labels = [a["label"] for a in matrix]
        self.assertIn("CAPTURE_fourth_and_forever", labels)
        cov = cs.coverage(matrix=matrix, reference_leagues=cs.reference_leagues())
        gaps = cov["uncovered_by_reference_league"]["fourth_and_forever"]["value_never_produced"]
        self.assertEqual(gaps, {}, "the captured league must be covered by its own arm")

    def test_the_coverage_gain_comes_FROM_the_captured_arm(self):
        """Non-vacuity for the above, and the measurement that justifies the arm's cost: remove
        it and the coverage collapses. One real capture moves more axes than the other 33 arms
        put together, because those 33 are all built from one base rulebook."""
        import run_draft_battery as rdb
        full = db.league_matrix(rdb.scoring_settings_from_capture())
        without = [a for a in full if not a["label"].startswith("CAPTURE_")]
        refs = cs.reference_leagues()
        wide = cs.coverage(matrix=full, reference_leagues=refs)
        narrow = cs.coverage(matrix=without, reference_leagues=refs)
        self.assertGreater(len(wide["varied"]), len(narrow["varied"]) * 3,
                           "one captured arm should multiply the varied-axis count")
        reappeared = narrow["uncovered_by_reference_league"]["fourth_and_forever"]
        for axis in ("scoring:rec_fd", "scoring:rush_fd", "slot:TAXI"):
            self.assertIn(axis, reappeared["value_never_produced"],
                          f"{axis} must go back to uncovered when the capture arm is removed")

    def test_neither_league_is_treated_as_canonical(self):
        """The architectural commitment, stated where it can fail. Both real captures are
        configuration POINTS: each must appear in `reference_leagues`, and the matrix must
        contain arms that are neither of them."""
        refs = cs.reference_leagues()
        self.assertIn("fourth_and_forever", refs)
        self.assertIn("sleeper_fixture", refs)
        import run_draft_battery as rdb
        labels = {a["label"] for a in db.league_matrix(rdb.scoring_settings_from_capture())}
        self.assertGreater(len({l for l in labels if not l.startswith("CAPTURE_")}), 25,
                           "the synthetic region must remain covered, not be replaced")


class TheConfigurationLayerIsDemonstratedToWork(unittest.TestCase):
    """#250's pair, read as what it actually proves rather than as a league comparison.

    Across seven arms spanning two rulebooks, two flex counts and two roster sizes, EVERY
    INVARIANT HELD while the configuration-dependent outcome legitimately reversed sign. That is
    the configuration layer doing its job, and it is the first time this repository has evidence
    of the two halves behaving differently in the same run.
    """

    ARTIFACTS = ("evidence/roster_proof/ROSTER_PROOF_MISSING_CELL.json",
                 "evidence/roster_proof/ROSTER_PROOF_FLEX_CUT.json")

    def _arms(self):
        for name in self.ARTIFACTS:
            path = Path(name)
            if path.exists():
                for arm in json.loads(path.read_text(encoding="utf-8"))["arms"]:
                    yield name, arm

    def test_every_lineup_filled_and_every_pick_priced_in_every_configuration(self):
        seen = 0
        for name, arm in self._arms():
            for seat in arm["seats"]:
                points = seat["engine"]["points"]
                seen += 1
                self.assertEqual(points["starters_filled"], points["starting_slots"],
                                 f"{name}:{arm['label']} seat {seat['engine_seat']}")
                self.assertEqual(points["unpriced"], 0)
        self.assertGreaterEqual(seen, 60, "non-vacuity: the artifacts must actually be present")

    def test_the_dependent_outcome_really_did_reverse(self):
        """Without this the test above is consistent with nothing having varied at all."""
        margins = {arm["label"]: arm["summary"]["points"].get("margin")
                   for _, arm in self._arms() if "margin" in arm["summary"]["points"]}
        if not margins:
            self.skipTest("margin was added to the summary after the flex cut ran")
        self.assertLess(min(margins.values()), 0)
        self.assertGreater(max(margins.values()), 0)


if __name__ == "__main__":
    unittest.main()
