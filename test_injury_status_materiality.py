"""#191: "Questionable" is not injury information, so the engine neither prices it nor says it.

THE MEASUREMENT THAT SETTLED IT, in the order it actually went, including the part I got wrong.

I first reported that Sleeper's projection already degrades with injury_status (10-23% across
four trade-value bands) and that risk_adj therefore double-counted the same fact. That was
WRONG, and the retraction is part of the record. Measured per status against nearest-trade-
value healthy peers, the HEALTHY control's own IQR is 0.82-1.47 -- Questionable's 0.85 sits
inside its own noise floor, and IR had n=3. The bands had manufactured a clean effect out of a
mostly-Questionable sample.

What settled it was not a ratio at all. Sleeper publishes a projected GAMES PLAYED:

    status          n     gp
    (none)        700     overwhelmingly 17
    Questionable  100     95 x gp=17,  5 x gp=16
    IR             23     20 x gp=16,  3 x gp=17
    PUP            12      4 x gp=16,  8 x gp=17

Sleeper projects injured players for a FULL SEASON. There is no degradation to double-count,
and there never was. The whole apparent effect is a one-game 17->16 shift.

WHY QUESTIONABLE SPECIFICALLY GOES. Two independent reasons that happen to agree:
  - the owner's, which is about football: anything can inspire a Questionable tag, and its use
    around the league is close to strategic. It is not a report on a player's health.
  - the engine's own ablation: its -1.5 moved 99 of 2084 board rows, by at most SIX ranks,
    never touching the top 50. It was priced precision on a signal that is not there.

AND OUT OF THE PROSE TOO, which is the harder half and the owner's explicit ruling. The obvious
half-measure -- stop pricing it, keep mentioning it -- was ruled against: raising a designation
to a person asserts that it matters, and repeating one the engine has just measured as
meaningless spends the reader's attention on noise. Silence is the honest output. It may return
only with historical backing, applied case-specifically to a player whose own record supports
it; never as a blanket constant (#56).

WHAT THIS IS NOT. It is not a claim that the surviving magnitudes are right -- see #202, where
PUP/NA/Sus/DNR occur in the real feed with no entry at all while "Doubtful" never occurs once.
And it does not touch PASSIVE DISPLAY: a roster table showing what Sleeper says is reporting
the feed, not the engine speaking.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import unittest

import draft_room as dr
import lineup_readiness
import player_universe as pu
import screen_context


class TheRulingIsStatedOnceTests(unittest.TestCase):
    """Four modules act on this, so the vocabulary lives in one place (#126)."""

    def test_questionable_is_named_immaterial(self):
        self.assertIn("Questionable", pu.IMMATERIAL_INJURY_STATUSES)

    def test_a_real_designation_is_material(self):
        for status in ("IR", "Out", "Doubtful", "PUP"):
            with self.subTest(status=status):
                self.assertTrue(pu.is_material_injury_status(status))

    def test_absence_and_immateriality_answer_the_same_way(self):
        """One predicate on purpose. A caller must not be able to treat "he is Questionable" as
        more actionable than "nothing is known about him" -- which is the state it is nearest."""
        self.assertFalse(pu.is_material_injury_status("Questionable"))
        self.assertFalse(pu.is_material_injury_status(None))
        self.assertFalse(pu.is_material_injury_status(""))


class ItIsNotPricedTests(unittest.TestCase):

    def test_risk_adj_no_longer_carries_it(self):
        self.assertNotIn("Questionable", dr.RISK_ADJ)

    def test_the_designations_that_survived_are_untouched(self):
        # Non-vacuity: the ruling removed ONE key, it did not empty the table or rescale it.
        self.assertEqual(dr.RISK_ADJ, {"IR": -18.0, "Out": -10.0, "Doubtful": -5.0})


class ItIsNotSpokenTests(unittest.TestCase):
    """The half the owner ruled on explicitly: out of the prose, not just out of the price."""

    @staticmethod
    def _row(**kw):
        base = {"name": "A Player", "position": "WR", "team": "MIN", "slot": "Starter",
                "injury_status": None, "sleeper_proj": 18.4, "tier": 1, "vorp": 5.0}
        base.update(kw)
        return base

    def test_a_questionable_starter_is_not_raised_as_a_lineup_problem(self):
        result = lineup_readiness.compute_readiness(
            [self._row(injury_status="Questionable")], {}, None, total_starting_slots=1)
        self.assertEqual(result["starter_injury_flags"], [])

    def test_an_IR_starter_still_is(self):
        # Non-vacuity for the test above: readiness has not simply stopped flagging injuries.
        result = lineup_readiness.compute_readiness(
            [self._row(injury_status="IR")], {}, None, total_starting_slots=1)
        self.assertEqual(len(result["starter_injury_flags"]), 1)

    def test_no_chair_facing_builder_repeats_it(self):
        """All THREE emission sites, named individually. screen_context formats injury_status
        in three separate builders and patching two of them left the third live -- found by a
        test, which is why this asserts against each rather than against one sample."""
        row = self._row(injury_status="Questionable")
        for label, ctx in (
            ("matchup", screen_context.build_matchup_context([row])),
            ("league", screen_context.build_league_context("X", [row])),
            ("free agents", screen_context.build_free_agents_context([row], None, None)),
        ):
            with self.subTest(builder=label):
                self.assertNotIn("Questionable", ctx.evidence)

    def test_and_a_material_one_still_reaches_every_one_of_them(self):
        row = self._row(injury_status="IR")
        for label, ctx in (
            ("matchup", screen_context.build_matchup_context([row])),
            ("league", screen_context.build_league_context("X", [row])),
            ("free agents", screen_context.build_free_agents_context([row], None, None)),
        ):
            with self.subTest(builder=label):
                self.assertIn("IR", ctx.evidence)


# MUTATIONS -- each applied to the source, this file re-run, the named test observed to FAIL,
# then reverted:
#   1. player_universe: IMMATERIAL_INJURY_STATUSES = ()
#        -> TheRulingIsStatedOnce.test_questionable_is_named_immaterial FAILED
#           and every ItIsNotSpoken test FAILED with it
#   2. player_universe: is_material_injury_status returns bool(status), dropping the set check
#        -> ...test_absence_and_immateriality_answer_the_same_way FAILED
#   3. player_universe: is_material_injury_status returns `status not in IMMATERIAL...`,
#      dropping the absence half, so None reads as material
#        -> ...test_absence_and_immateriality_answer_the_same_way FAILED
#   4. draft_room: restore "Questionable": -1.5 to RISK_ADJ
#        -> ItIsNotPriced.test_risk_adj_no_longer_carries_it FAILED
#   5. draft_room: RISK_ADJ = {} (over-application of the ruling)
#        -> ItIsNotPriced.test_the_designations_that_survived_are_untouched FAILED
#   6. lineup_readiness: revert the filter to `and r.get("injury_status")`
#        -> ItIsNotSpoken.test_a_questionable_starter_is_not_raised_as_a_lineup_problem FAILED
#   7. lineup_readiness: filter to `False`, flagging nobody
#        -> ...test_an_IR_starter_still_is FAILED
#   8. screen_context: revert ONE of the three sites (each in turn)
#        -> ...test_no_chair_facing_builder_repeats_it FAILED on that builder's subTest
if __name__ == "__main__":
    unittest.main()
