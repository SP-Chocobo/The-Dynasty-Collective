"""#142 / #50 / #56: the lifetime rule, enforced rather than written down.

CDME_CONTRACTS' team_acquisition_value invariant 5 says a quantity may enter a dynasty
valuation only if its lifetime is at least as long as the asset's horizon. This suite exists
because a rule that settles one case and then lives only in prose will not settle the next one.

The enforcing test is test_every_scoring_term_is_declared: it reads what compute_draft_board
actually emits and fails when a term is summed into the valuation without an entry in the
registry. A new term must state its lifetime to ship. The rest pin that the registry stays
honest about the terms already in it -- in particular that the one open finding is not quietly
downgraded to "mitigated" by adding prose.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

import term_lifetimes as tl

_HERE = Path(__file__).parent


class EveryScoringTermIsDeclaredTests(unittest.TestCase):
    """The enforcement. Derived from the source, not from a hand-kept list, so the registry
    cannot drift from the equation it describes."""

    def _summed_terms(self) -> set:
        """The names actually added together into team_acquisition_value, read out of the AST.

        Parsed rather than grepped: a name mentioned in a comment or a column list is not a
        term, and the whole point is to catch a term that is genuinely being SUMMED."""
        tree = ast.parse((_HERE / "draft_room.py").read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if "team_acquisition_value" not in targets:
                continue
            # round(a + b + c, 2) -- walk into the call to find the addition.
            names = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
            return {n for n in names if n not in ("round", "min", "max", "float")}
        self.fail("could not locate the team_acquisition_value assignment in draft_room.py")

    def test_every_summed_term_has_a_lifetime_entry(self):
        summed = self._summed_terms()
        # universal_value is the sub-sum, not a leaf; its own components are declared instead.
        summed.discard("universal_value")
        declared = set(tl.TERMS)
        # Local variable names differ slightly from the emitted column names.
        aliases = {"eligibility_bonus_value": "eligibility_bonus",
                   "depth_exposure_value": "depth_exposure"}
        summed = {aliases.get(name, name) for name in summed}
        missing = sorted(summed - declared)
        self.assertEqual(
            missing, [],
            f"these terms are summed into team_acquisition_value with no lifetime declared: "
            f"{missing}. A term must state how long the thing it measures stays true before it "
            f"can price a dynasty asset -- see CDME_CONTRACTS invariant 5 and term_lifetimes.py")

    def test_universal_values_own_components_are_declared_too(self):
        """The sub-sum is where the anchor lives, and the anchor is the open finding."""
        tree = ast.parse((_HERE / "draft_room.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "universal_value" for t in node.targets):
                names = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
                names -= {"round", "min", "max", "float"}
                if not names:
                    continue
                missing = sorted(names - set(tl.TERMS))
                self.assertEqual(missing, [], f"undeclared universal_value components: {missing}")
                return
        self.fail("could not locate the universal_value assignment")

    def test_the_registry_describes_no_term_that_does_not_exist(self):
        """Non-vacuity in the other direction: a registry full of retired terms would pass the
        test above while describing an engine that no longer exists."""
        source = (_HERE / "draft_room.py").read_text()
        for name in tl.TERMS:
            with self.subTest(term=name):
                self.assertIn(name, source, f"{name} is declared but appears nowhere in draft_room")


class TheRegistryStaysHonestTests(unittest.TestCase):
    def test_bpa_is_still_recorded_as_an_open_finding(self):
        """A characterization, and the one most likely to be silenced rather than fixed. If bpa
        gains a real mitigation this fails, and the right response is to update the test with
        what the mitigation IS -- not to delete the assertion."""
        open_terms = [item["term"] for item in tl.violations()]
        self.assertIn("bpa", open_terms,
                      "bpa is no longer listed as an open lifetime finding. If the anchor now "
                      "carries a multi-year component, say so here and cite the measurement.")

    def test_every_short_lived_term_either_has_a_mitigation_or_a_register_item(self):
        """The two honest states. What must never happen is a season- or week-scoped term
        sitting in the valuation with neither a fix nor a number to find it by."""
        for name, entry in tl.TERMS.items():
            if entry["lifetime"] in tl.ADMISSIBLE:
                continue
            with self.subTest(term=name):
                self.assertTrue(
                    entry["mitigation"] or entry["register"],
                    f"{name} outlives neither the horizon nor anyone's memory of it")

    def test_the_roster_state_carve_out_is_justified_not_just_asserted(self):
        """The rule would disqualify the whole engine if 'transient' were enough -- all three
        team-specific terms change constantly. The carve-out has to be stated where it is
        used, or the next reader applies the rule too broadly and deletes working terms."""
        source = (_HERE / "term_lifetimes.py").read_text()
        self.assertIn("DECISION number", source)
        for name in ("need_bonus", "eligibility_bonus", "depth_exposure"):
            with self.subTest(term=name):
                self.assertEqual(tl.TERMS[name]["lifetime"], tl.ROSTER_STATE)

    def test_an_excluded_quantity_records_why_rather_than_only_that(self):
        """bye_collision was excluded on this rule after real measurement. Without the reason
        travelling with the exclusion, someone re-measures it, finds a genuine effect, and
        wires it -- which is exactly the trap the category argument exists to close."""
        entry = tl.EXCLUDED["bye_collision"]
        self.assertIn("reassigns bye weeks", entry["why"])
        self.assertIn("ANY", entry["why"], "the exclusion must say it is magnitude-independent")

    def test_the_rule_is_stated_in_the_contracts_not_only_in_code(self):
        """Whitespace-normalized, because the phrase wraps across a line in the markdown and a
        literal search failed on exactly that -- a prose assertion that breaks the next time
        someone re-wraps a paragraph is a guard that will be deleted rather than fixed."""
        contracts = " ".join((_HERE / "CDME_CONTRACTS.md").read_text().split())
        self.assertIn("lifetime is at least as long as the asset's horizon", contracts)


if __name__ == "__main__":
    unittest.main()
