"""#183 -- the absence contract where a PERSON actually reads it.

The Draft Room is ruled to work fully with no API (POST_AUDIT_PLAN, "RULED: the debate layer"),
and for a customer without one the engine's own evidence IS the whole explanation. So a `None`
reaching `_format_candidate` is not cosmetic: it is the entire account of a pick, with a hole in
it, rendered where nobody can check it against the board.

SIX BREAKS WERE FOUND BY RENDERING, NOT BY READING, and this file keeps them shut. The freeze
checklist says #183 is "six defects" but never enumerated them; these six are what a sweep of
absent-field scenarios actually produced, and no claim is made that they are the original six.

REACHABILITY IS PART OF THE FINDING, because a break on a field that is never absent is a
hypothetical and this codebase does not spend repairs on those:

  * REACHABLE BY TYPE AND BY PATH -- universal_value, team_acquisition_value, opportunity_cost,
    expected_value_of_waiting, intervening_picks, position_expected_taken are all Optional, and
    an UNPRICED board row (final_score None) produces exactly the state that broke worst:
    `estimate_survival` deliberately still answers for such a player -- he is on a rival's board
    and can be taken, so he gets the module's floor -- while his price, and therefore his
    opportunity cost, stay absent. That combination printed a real percentage and the literal
    string "None" on the next line.
  * GUARDED BUT NOT CLAIMED LIVE -- need_bonus and eligibility_bonus are typed non-Optional.
    They reach the snapshot through `.get(key, 0.0)`, which substitutes the default for a MISSING
    key but passes an explicit None straight through, and a None there raised TypeError on the
    `:+` format. That is a caller contract violation, so the guard is defensive and this note
    says so rather than dressing it up as a live defect.
"""
from __future__ import annotations

import unittest

import pick_debate as pd
from pick_synthesis import CandidateSnapshot


def candidate(**over) -> CandidateSnapshot:
    """A fully-measured candidate, so every test below changes exactly one thing."""
    base = dict(
        player_id="9221", name="Test Player", position="RB", team="SF", bpa=50.0,
        bpa_source="points_vor_draftsharks", confidence=80.0, universal_value=50.0,
        need_bonus=6.0, eligibility_bonus=4.0, team_acquisition_value=60.0,
        survival_probability=0.4, survival_basis=None, intervening_picks=2, opportunity_cost=30.0,
        expected_value_of_waiting=20.0, denial_value=30.0, denial_basis="measured",
        rival_premium_basis=None, denial_team="4", rival_premium=6.0,
        positional_forfeit=None, position_expected_taken=None, positional_cliff=None,
        position_run_detected=False, pick_necessity=75.0, necessity_label="PREFERRED",
        near_tie_with_leader=False, cliff_protection=False, block_opportunity=False,
        pure_value=False, context_elevated=False, consensus_rank=None, consensus_tier=None,
        projected_points=None)
    base.update(over)
    return CandidateSnapshot(**base)


def rendered(**over) -> str:
    return pd._format_candidate(candidate(**over), None)


class NoAbsentQuantityIsEverPrintedAsAWord(unittest.TestCase):
    """The blunt property, checked the blunt way. `None` must not appear in prose a chair reads,
    because there it is indistinguishable from a name, a tier or a number."""

    #: Each entry is a reachable absence, named by what produces it.
    ABSENCES = {
        "unpriced row -- no price, no team value, no opportunity cost": dict(
            universal_value=None, team_acquisition_value=None,
            opportunity_cost=None, expected_value_of_waiting=None),
        "priced row whose survival was measured but cost was not": dict(
            team_acquisition_value=None, opportunity_cost=None,
            expected_value_of_waiting=None),
        "survival measured, intervening pick count absent": dict(intervening_picks=None),
        "cliff tier measured, its two magnitudes not": dict(
            positional_cliff={"tier": "HIGH", "gap": None, "typical_gap": None}),
        "forfeit measured, expected-taken count not": dict(
            positional_forfeit=12.0, position_expected_taken=None),
        "need_bonus absent -- a caller contract violation, guarded not claimed": dict(
            need_bonus=None),
    }

    def test_no_scenario_leaks_the_string_None(self):
        for label, over in self.ABSENCES.items():
            with self.subTest(label):
                for line in rendered(**over).splitlines():
                    self.assertNotIn("None", line, f"{label}: {line.strip()!r}")

    def test_no_scenario_raises(self):
        """`need_bonus=None` raised TypeError on the `:+` format -- the Dock did not misreport,
        it died, taking the whole explanation with it."""
        for label, over in self.ABSENCES.items():
            with self.subTest(label):
                rendered(**over)


class AnAbsenceSaysWhichKindItIs(unittest.TestCase):
    """Not leaking "None" is the floor, not the goal. A chair that reads a missing line as
    "the engine had nothing to say" draws the same false conclusion by a quieter route, so each
    absence states what was not measured and warns against the reading it invites."""

    def test_an_unpriced_player_says_NOT_PRICED_rather_than_going_silent(self):
        out = rendered(universal_value=None, team_acquisition_value=None,
                       opportunity_cost=None, expected_value_of_waiting=None)
        self.assertIn("NOT PRICED", out)
        self.assertIn("never as low", out)

    def test_an_absent_team_value_is_UNKNOWN_and_says_never_zero(self):
        out = rendered(team_acquisition_value=None, opportunity_cost=None,
                       expected_value_of_waiting=None)
        self.assertIn("NOT MEASURED", out)
        self.assertIn("never zero", out)

    def test_an_absent_opportunity_cost_denies_the_reading_that_waiting_is_free(self):
        """The dangerous inference, named at the site. An absent cost of waiting sits exactly
        where a measured 0.0 would, and 0.0 there is an argument FOR waiting."""
        out = rendered(team_acquisition_value=None, opportunity_cost=None,
                       expected_value_of_waiting=None)
        # INVERTED (#206). opportunity_cost is team_acquisition_value x (1 - survival), so it
        # travels with the withheld survival family rather than reporting its own absence.
        # The INFERENCE this test exists to deny -- "waiting is free" -- is still denied, now
        # by the withholding sentence. That is what must not regress; the wording is not.
        self.assertNotIn("Opportunity cost of waiting", out)
        self.assertIn("WITHHELD, not missing", out)
        # The denial USED to be a sentence ("Not 'waiting is free'") sitting where a 0.0 would
        # have been. It is now structural instead: no cost line is rendered at all, so there is
        # no number for a reader to misread as free. Assert the stronger form -- that nothing
        # in the output could be read as a zero cost of waiting -- rather than the old wording.
        self.assertNotIn("cost of waiting: 0", out.lower())
        self.assertNotIn("Expected value if you wait", out)

    def test_a_measured_zero_is_still_reported_as_a_measurement(self):
        """The other half of the contract, and the one a careless absence fix breaks: 0.0 is a
        finding. If this ever fails, the repair has started swallowing real zeros."""
        out = rendered(positional_forfeit=0.0)
        self.assertIn("measured 0", out)
        self.assertIn("no worse than now", out)

    def test_a_cliff_keeps_its_tier_when_its_magnitudes_are_absent(self):
        """Degrade, never abort: the tier is real evidence and survives on its own."""
        out = rendered(positional_cliff={"tier": "HIGH", "gap": None, "typical_gap": None})
        self.assertIn("Positional cliff: HIGH", out)
        self.assertIn("tier only", out)


class TheFullyMeasuredCaseIsUnCHANGED(unittest.TestCase):
    """A guard against fixing absence by degrading everything. The ordinary path must still
    render every number it always did."""

    def test_every_measured_quantity_still_appears(self):
        out = rendered(positional_forfeit=12.0, position_expected_taken=3.0,
                       positional_cliff={"tier": "HIGH", "gap": 12.0, "typical_gap": 2.0})
        for expected in ("Universal value: 50.0", "Team acquisition value: 60.0",
                         "universal_value 50.0 + need_bonus +6.0", "eligibility_bonus +4.0",
                         # INVERTED (#206): the survival family is withheld from the chairs,
                         # and the measured pick COUNT takes its place in the same line.
                         "Picks before your next selection: 2",
                         "gap to next at position: 12.0", "~3.0 RB pick(s)"):
            self.assertIn(expected, out)

    def test_the_decomposition_is_withheld_rather_than_shown_with_a_hole(self):
        """When one term is absent the WHOLE is still reported -- it is a real number -- but the
        arithmetic sentence is not, because a sum missing an addend shown to a model instructed
        never to recompute is worse than no sum at all."""
        out = rendered(need_bonus=None)
        self.assertIn("Team acquisition value: 60.0", out)
        self.assertIn("decomposition unavailable", out)
        self.assertNotIn("need_bonus", out)


if __name__ == "__main__":
    unittest.main()
