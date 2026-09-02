"""The contract for `lineup_optimizer.marginal_lineup_value` -- an existing roster-context
primitive that is computed on every board row and consumed by nothing.

It is investigated and pinned here rather than wired, because the measured answer to "should it
influence decisions" is NO, for a reason that only shows up under a correct gate.

WHAT IT MEASURES. The best startable lineup WITH this candidate minus the best startable lineup
without him -- his incremental contribution to the eleven (here nine) players who actually score.
Not his value; the part of his value the lineup can currently use.

WHAT UNIT. Whatever currency the caller supplies, by construction. The function is
basis-agnostic: draft_room happens to feed it `trade_value` (see _team_roster_players), so the
number reaching eligibility_bonus is denominated in Draft Sharks' dynasty market scale, NOT the
board's projected points. Measured, a projected-points variant is constructible and has strictly
better coverage: at round 20 `projection` prices 20 of 20 rostered players while `trade_value`
drops 2 -- and per _team_roster_players' own comment, 339 of 415 IDP baseline rows carry no
trade value at all. A dropped player takes his lineup CONSTRAINT with him, so the solve runs
against a roster emptier than it really is.

WHEN IT IS INFORMATIVE, AND WHEN IT IS NECESSARILY DEGENERATE. Two regimes, distinguishable
exactly -- no heuristic -- from what optimize_lineup already returns:

  * FILLS AN EMPTY SLOT: the assignment count RISES when he is added. His marginal is his own
    full value. Ordering by it is ordering by raw projected points, which is not comparable
    across positions -- precisely what VOR exists to correct.
  * DISPLACES A STARTER: the assignment count is unchanged. His marginal is a true increment,
    his value minus the starter he benches. This is the informative regime.

Measured share of candidates in the degenerate regime, by round: 92% at rd 4, 42% at rd 8, 22%
at rd 10, 15% at rd 14, 0% from rd 16. Note the roster can hold 14 players while only 8 of 9
slots are used, so "roster size >= slot count" is NOT a sufficient gate -- the condition is
per-candidate.

HOW IT RELATES TO need_bonus. Complementary in time, not duplicative. need_bonus is keyed to
UNFILLED REACHABLE SLOTS and reaches 0.00 once a position is covered -- exactly when this signal
stops being degenerate. Where need_bonus is silent, this separates an elite who would displace a
starter from a depth piece who would not: on a roster with four RBs, J Gibbs scores 20.0 and
D Henry and J Brooks score 0.0, while need_bonus gives all three 0.00.

WHAT DECISIONS IT MAY INFLUENCE: none, on the present evidence. Tested as a comparator inside
the near-tie band -- an architecture that introduces no coefficient and adds nothing to any
value, only ordering a set the engine has already declared equivalent. Measured across real
board states (rounds 10-18, native projected-points basis, all three gates in one pass): it would
change 2 of 25 tie decisions (8%) ungated, the SAME 2 of 25 gated on roster size -- that gate is
inert, since every roster already holds 9+ players by round 10 -- and **0 of 14 under the correct
per-candidate displacement gate.** Both ungated changes are the artifact in plain sight: the
comparator's pick wins on 202.0 and 171.0 raw projected points from an empty slot, against a
leader whose 0.0 is a genuine increment. In the regime where the signal is informative it never
disagrees with team_acquisition_value; in the regime where it disagrees it is not informative.

So it stays an observable. These tests pin the primitive so that conclusion can be re-checked
rather than re-derived, and so a future change to the optimizer cannot silently invalidate it.
"""
import unittest

import lineup_optimizer as lo


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
SLOTS = lo.slots_from_roster_positions(ROSTER)


def _p(pid, value, *positions):
    return {"id": pid, "value": float(value), "eligible": set(positions)}


class TheTwoRegimesAreExactlyDistinguishableTests(unittest.TestCase):
    """The gate is a fact about the assignment, not a heuristic about the round."""

    def _regime(self, roster, candidate):
        before = lo.optimize_lineup(roster, SLOTS)
        after = lo.optimize_lineup(roster + [candidate], SLOTS)
        return ("fills" if len(after["assignments"]) > len(before["assignments"])
                else "displaces")

    def test_an_empty_slot_makes_the_marginal_his_own_full_value(self):
        roster = [_p("qb", 300, "QB")]                       # no RB rostered at all
        candidate = _p("rb1", 200, "RB")
        self.assertEqual(self._regime(roster, candidate), "fills")
        result = lo.marginal_lineup_value(roster, candidate, ROSTER)
        self.assertEqual(result["marginal_value"], 200.0,
                         "filling an empty slot must return the candidate's whole value")

    def test_a_full_position_makes_the_marginal_a_true_increment(self):
        roster = [_p("qb", 300, "QB"),
                  _p("rb1", 200, "RB"), _p("rb2", 190, "RB"), _p("rb3", 180, "RB"),
                  _p("wr1", 170, "WR"), _p("wr2", 160, "WR"), _p("te1", 150, "TE"),
                  _p("k1", 100, "K"), _p("d1", 100, "DEF")]
        candidate = _p("rb4", 195, "RB")
        self.assertEqual(self._regime(roster, candidate), "displaces")
        result = lo.marginal_lineup_value(roster, candidate, ROSTER)
        self.assertGreater(result["marginal_value"], 0.0)
        self.assertLess(result["marginal_value"], candidate["value"],
                        "a displacement marginal must be strictly less than his own value")

    def test_both_regimes_are_reachable_so_neither_test_above_is_vacuous(self):
        # If the fixture ever stopped producing one of the two, the pair above would still pass
        # while observing only half the contract.
        empty_roster = [_p("qb", 300, "QB")]
        full_roster = [_p("qb", 300, "QB"),
                       _p("rb1", 200, "RB"), _p("rb2", 190, "RB"), _p("rb3", 180, "RB"),
                       _p("wr1", 170, "WR"), _p("wr2", 160, "WR"), _p("te1", 150, "TE"),
                       _p("k1", 100, "K"), _p("d1", 100, "DEF")]
        candidate = _p("rbX", 195, "RB")
        self.assertEqual({self._regime(empty_roster, candidate),
                          self._regime(full_roster, candidate)}, {"fills", "displaces"})


class MarginalDeclinesWithCoverageTests(unittest.TestCase):
    """The covered-vs-saturated behaviour, isolated: same candidate, richer roster."""

    def _roster(self, rb_count):
        base = [_p("qb", 300, "QB"), _p("wr1", 170, "WR"), _p("wr2", 160, "WR"),
                _p("te1", 150, "TE"), _p("k1", 100, "K"), _p("d1", 100, "DEF")]
        return base + [_p(f"rb{i}", 200 - i, "RB") for i in range(rb_count)]

    def test_marginal_never_rises_as_the_position_fills(self):
        candidate = _p("cand", 150, "RB")
        previous = None
        for held in range(0, 7):
            value = lo.marginal_lineup_value(self._roster(held), candidate, ROSTER)["marginal_value"]
            if previous is not None:
                self.assertLessEqual(value, previous + 1e-9,
                                     f"holding {held} RBs bought MORE marginal value than {held-1}")
            previous = value

    def test_an_elite_candidate_keeps_positive_marginal_on_a_saturated_roster(self):
        # The exemption that matters: a saturated position must not make every player from it
        # irrelevant. An elite asset still cracks the lineup; a depth piece does not.
        saturated = self._roster(6)
        elite = _p("elite", 400, "RB")
        depth = _p("depth", 50, "RB")
        self.assertGreater(lo.marginal_lineup_value(saturated, elite, ROSTER)["marginal_value"], 0.0)
        self.assertEqual(lo.marginal_lineup_value(saturated, depth, ROSTER)["marginal_value"], 0.0)


class TheFunctionIsCurrencyAgnosticTests(unittest.TestCase):
    """Its docstring promises it returns "whatever currency its caller supplied". That is what
    makes the basis a CALL-SITE choice rather than a property of the primitive -- and therefore
    what makes a projected-points variant constructible without touching this function."""

    def test_scaling_every_input_scales_the_answer_by_the_same_factor(self):
        roster = [_p("qb", 300, "QB"), _p("rb1", 200, "RB"), _p("rb2", 190, "RB"),
                  _p("rb3", 180, "RB"), _p("wr1", 170, "WR"), _p("wr2", 160, "WR"),
                  _p("te1", 150, "TE"), _p("k1", 100, "K"), _p("d1", 100, "DEF")]
        candidate = _p("cand", 195, "RB")
        base = lo.marginal_lineup_value(roster, candidate, ROSTER)["marginal_value"]
        k = 7.5
        scaled_roster = [dict(p, value=p["value"] * k) for p in roster]
        scaled_candidate = dict(candidate, value=candidate["value"] * k)
        scaled = lo.marginal_lineup_value(scaled_roster, scaled_candidate, ROSTER)["marginal_value"]
        self.assertAlmostEqual(scaled, base * k, places=6,
                               msg="the primitive is not currency-agnostic; a basis change would "
                                   "alter more than the unit")
        self.assertGreater(base, 0.0, "fixture must produce a non-zero marginal to scale")


class ItReportsBothLineupsNotJustTheDeltaTests(unittest.TestCase):
    """Deliberate transparency, per the function's own docstring -- a human auditing a
    recommendation can see the two totals rather than trusting one subtracted number."""

    def test_the_two_totals_are_returned_and_reconcile_to_the_delta(self):
        roster = [_p("qb", 300, "QB"), _p("rb1", 200, "RB")]
        candidate = _p("cand", 195, "RB")
        result = lo.marginal_lineup_value(roster, candidate, ROSTER)
        self.assertIn("with_candidate", result)
        self.assertIn("without_candidate", result)
        self.assertAlmostEqual(result["marginal_value"],
                               result["with_candidate"] - result["without_candidate"], places=6)


if __name__ == "__main__":
    unittest.main()
