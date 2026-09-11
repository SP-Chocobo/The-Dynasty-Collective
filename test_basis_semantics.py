"""#188's ruling, enforced -- including the condition it was made subject to.

The ruling: adopt `partial` as the shared CONCEPT, keep `rule_floor` distinct, leave
`provider_meter.TRUNCATED` out. The condition: **enumerate the actual emitters and make sure the
new shared state is reachable in each intended vocabulary** -- do not turn a vocabulary cleanup
into another unreachable-predicate exercise (the 18th withdrawal's shape).

So the reachability half is not asserted in prose here. Every BOUNDED_INPUT member is either
DRIVEN INTO ITS STATE below and observed, or declared `dormant_by_design` and required to name a
live wiring guard. A member that is neither fails.
"""
from __future__ import annotations

import unittest

import basis_semantics as bs
import draft_room as dr
import lineup_optimizer as lo
import player_universe as pu

ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"]


def _p(pid, value, position, bye=None):
    """The shape lineup_optimizer actually takes -- id/value/eligible/bye. Copied from
    test_bye_collision rather than invented; a hand-rolled {player_id, position} dict returns
    an empty result and a KeyError one call later, which is how this fixture was first wrong."""
    return {"id": pid, "value": float(value), "eligible": {position}, "bye": bye}


class TheRulingIsWhatIsEncoded(unittest.TestCase):

    def test_rule_floor_is_a_bound_but_NOT_a_bounded_input_one(self):
        """The whole point of the split. An IR designation is not partially known: the evidence
        is complete and the RULEBOOK yields a floor. Folding it in with the partial-input states
        would tell a consumer that more data could sharpen it, which is false."""
        self.assertIn(pu.RULE_FLOOR, bs.BOUNDED_BY_RULE)
        self.assertNotIn(pu.RULE_FLOOR, bs.BOUNDED_INPUT)
        self.assertTrue(bs.is_bounded(pu.RULE_FLOOR))
        self.assertIs(bs.would_more_evidence_sharpen(pu.RULE_FLOOR), False)

    def test_the_partial_input_states_say_more_evidence_would_sharpen_them(self):
        for token in sorted(bs.BOUNDED_INPUT):
            with self.subTest(token):
                self.assertIs(bs.would_more_evidence_sharpen(token), True)

    def test_the_two_classes_are_disjoint(self):
        self.assertEqual(bs.BOUNDED_INPUT & bs.BOUNDED_BY_RULE, frozenset())

    def test_the_payload_token_stays_out_and_says_why(self):
        """provider_meter.TRUNCATED describes a cut-off response, not a bounded quantity.
        Admitting it is the category error the split exists to prevent, so its exclusion is
        recorded with a reason rather than left to be re-litigated."""
        import provider_meter as pm
        self.assertNotIn(pm.TRUNCATED, bs.BOUNDED_INPUT)
        self.assertNotIn(pm.TRUNCATED, bs.BOUNDED_BY_RULE)
        self.assertFalse(bs.is_bounded(pm.TRUNCATED))
        self.assertIn(pm.TRUNCATED, bs.EXCLUDED_WITH_REASON)
        self.assertTrue(bs.EXCLUDED_WITH_REASON[pm.TRUNCATED].strip())

    def test_a_measured_basis_is_not_a_bound_and_the_question_does_not_apply(self):
        """Three-state, deliberately: `would_more_evidence_sharpen` returns None rather than
        False for a measured number, because False would assert it cannot be improved."""
        for token in (lo.BYE_MEASURED, lo.DISPLACEMENT_MEASURED, dr.APPETITE_MEASURED, None):
            with self.subTest(token):
                self.assertFalse(bs.is_bounded(token))
                self.assertIsNone(bs.bound_kind(token))
                self.assertIsNone(bs.would_more_evidence_sharpen(token))


class EveryClassifiedStateIsReachable(unittest.TestCase):
    """The condition the ruling was made subject to, enforced rather than promised."""

    def test_the_population_is_not_empty(self):
        """A rate over an empty set is not a rate; an invariant over an empty set is not an
        invariant. If a rename empties these, every test below would pass vacuously."""
        self.assertTrue(bs.BOUNDED_INPUT)
        self.assertTrue(bs.BOUNDED_BY_RULE)

    def test_every_classified_token_has_a_recorded_reachability(self):
        for token in sorted(bs.BOUNDED_INPUT | bs.BOUNDED_BY_RULE):
            with self.subTest(token):
                self.assertIn(token, bs.REACHABILITY,
                              "a classified state with no recorded reachability is exactly the "
                              "unreachable-predicate risk this ruling was conditioned on")
                self.assertIn(bs.REACHABILITY[token], ("exercised", "dormant_by_design"))

    def test_bye_partial_is_emitted_when_a_bye_is_unknown(self):
        players = [_p("q1", 30, "QB", 7), _p("r1", 25, "RB", 7), _p("r2", 25, "RB", 9),
                   _p("w1", 20, "WR", 7), _p("w2", 20, "WR", 9), _p("t1", 15, "TE", 13),
                   _p("r3", 24, "RB", None)]
        bases = {w["basis"] for w in lo.bye_collision(players, ROSTER).values()}
        self.assertIn(lo.BYE_PARTIAL, bases)
        known = [_p(p["id"], p["value"], next(iter(p["eligible"])), p["bye"] or 7) for p in players]
        control = {w["basis"] for w in lo.bye_collision(known, ROSTER).values()}
        self.assertNotIn(lo.BYE_PARTIAL, control, "the control must NOT reach the partial state")

    def test_displacement_roster_partial_is_emitted_when_an_eligible_is_unpriced(self):
        out = lo.displacement_level([_p("x", 50, "RB")], ROSTER, "RB", 40.0,
                                    unpriced_eligible=[{"RB"}])
        self.assertEqual(out["basis"], lo.DISPLACEMENT_ROSTER_PARTIAL)
        control = lo.displacement_level([_p("x", 50, "RB")], ROSTER, "RB", 40.0,
                                        unpriced_eligible=None)
        self.assertNotEqual(control["basis"], lo.DISPLACEMENT_ROSTER_PARTIAL)

    def test_rule_floor_is_emitted_for_a_designation_with_a_rulebook_floor(self):
        factor, basis = pu.availability_factor("IR", 17)
        self.assertEqual(basis, pu.RULE_FLOOR)
        self.assertLess(factor, 1.0, "a floor that removes nothing is not a floor")
        for status, games in (("IR", None), (None, 17), ("Zzz", 17)):
            with self.subTest(status=status, games=games):
                self.assertNotEqual(pu.availability_factor(status, games)[1], pu.RULE_FLOOR)

    def test_the_dormant_member_names_a_live_wiring_guard(self):
        """`pool_truncated` binds at no position on real data, so behaviour cannot reach it.
        That is dormant-by-design, NOT dead -- and the distinction only holds while something
        keeps the path wired. test_replacement_basis_vocabulary asserts the `truncated_out`
        collector is handed over ON THE CALL NODE for exactly that reason. If that guard is
        ever deleted, this state becomes genuinely unreachable and must leave the vocabulary."""
        dormant = [t for t, how in bs.REACHABILITY.items() if how == "dormant_by_design"]
        self.assertEqual(dormant, [dr.REPLACEMENT_BASIS_POOL_TRUNCATED])

        import ast, inspect
        tree = ast.parse(inspect.getsource(dr.compute_draft_board).lstrip())
        wired = [c for c in ast.walk(tree)
                 if isinstance(c, ast.Call)
                 and getattr(c.func, "id", None) == "replacement_levels"
                 and any(k.arg == "truncated_out" for k in c.keywords)]
        self.assertTrue(wired,
                        "the collector is no longer passed, so pool_truncated can never be "
                        "stamped -- it is now unreachable and must be removed from "
                        "BOUNDED_INPUT rather than left as dead vocabulary")


if __name__ == "__main__":
    unittest.main()
