"""One slot, one alternative (#216, #221).

A phantom in `displacement_level` stands for what a slot gets if I pass. For a DEDICATED slot
that is a free player at its one position. For a FLEX it is the best free player among every
position the slot admits. Filling a flex phantom with the CANDIDATE'S OWN positional level
instead prices two players against two different alternatives for the same slot -- which is
#216 in both of its directions.

These tests pin the construction, the invariant it replaces, and the two directions.

MUTATION RESULTS AT THE BOTTOM.
"""
import unittest

import draft_room as dr
import lineup_optimizer as lo

TE_SLOT = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
NO_TE_SLOT = ["QB", "WR", "WR", "RB", "RB", "FLEX", "FLEX", "WRRB_FLEX", "SUPER_FLEX"]
#: A pool where TE is scarce at its own rank and RB is deep -- the owner's league's shape.
LEVELS = {"QB": 300.0, "RB": 100.0, "WR": 207.0, "TE": 258.0}


def _p(i, value, position):
    return {"id": f"p{i}", "value": value, "eligible": {position}}


class SharedSlotAlternativesTests(unittest.TestCase):
    def test_a_dedicated_slot_is_worth_its_own_positions_level(self):
        alts = dr.shared_slot_alternatives(LEVELS, TE_SLOT)
        self.assertEqual(alts["QB_0"], 300.0)
        self.assertEqual(alts["RB_1"], 100.0)
        self.assertEqual(alts["WR_3"], 207.0)
        self.assertEqual(alts["TE_5"], 258.0)

    def test_a_flex_is_worth_the_BEST_of_what_it_admits(self):
        # max, not min and not a blend: the alternative to taking this candidate is the best
        # thing still freely available for the slot.
        alts = dr.shared_slot_alternatives(LEVELS, TE_SLOT)
        self.assertEqual(alts["FLEX_6"], 258.0)                       # max(RB 100, WR 207, TE 258)
        alts_no_te = dr.shared_slot_alternatives(LEVELS, NO_TE_SLOT)
        self.assertEqual(alts_no_te["WRRB_FLEX_7"], 207.0)            # max(RB 100, WR 207)

    def test_a_slot_nothing_can_be_priced_at_is_OMITTED_not_given_a_number(self):
        # Absence travels. An invented value here would be the absence-read-as-a-value defect.
        alts = dr.shared_slot_alternatives({"QB": 300.0}, TE_SLOT)
        # Only the slots a priced position can reach get a value. The flexes admit RB/WR/TE,
        # none of which has a level here, so they are absent -- and displacement_level then uses
        # the candidate's own free_alternative for them, which is the pre-#216 behaviour and the
        # only honest answer when nothing at that slot can be priced.
        self.assertEqual(alts, {"QB_0": 300.0})

    def test_a_missing_level_is_skipped_not_read_as_zero(self):
        alts = dr.shared_slot_alternatives({"RB": 100.0, "WR": None, "TE": float("nan")}, TE_SLOT)
        self.assertEqual(alts["FLEX_6"], 100.0)      # WR/TE contribute nothing, not 0.0
        self.assertNotIn("WR_3", alts)


class TheInvariantThatReplacedTheOldOneTests(unittest.TestCase):
    """The old wording was "reduces to the league anchor exactly on an empty roster". That is no
    longer true for a position with NO dedicated slot -- which is the point of the change. What
    holds instead is stronger where it matters and is stated as the replacement."""

    def test_an_open_dedicated_slot_deducts_exactly_nothing_on_any_roster(self):
        alts = dr.shared_slot_alternatives(LEVELS, TE_SLOT)
        rosters = [
            [],
            [_p(1, 260.0, "RB")],
            [_p(1, 260.0, "RB"), _p(2, 280.0, "WR"), _p(3, 300.0, "QB")],
        ]
        for roster in rosters:
            held = {e["eligible"].copy().pop() for e in roster}
            for position in ("QB", "RB", "WR", "TE"):
                if position in held:
                    continue          # its dedicated slot may now be taken; that is a real case
                result = lo.displacement_level(roster, TE_SLOT, position, LEVELS[position],
                                               slot_alternatives=alts)
                self.assertEqual(result["adjustment"], 0.0,
                                 msg=f"{position} with an open dedicated slot, roster {len(roster)}")

    def test_omitting_slot_alternatives_reproduces_the_shipped_behaviour_exactly(self):
        roster = [_p(1, 260.0, "RB"), _p(2, 240.0, "RB"), _p(3, 300.0, "QB")]
        for rpos in (TE_SLOT, NO_TE_SLOT):
            for position in ("QB", "RB", "WR", "TE"):
                bare = lo.displacement_level(roster, rpos, position, LEVELS[position])
                uniform = lo.displacement_level(
                    roster, rpos, position, LEVELS[position],
                    slot_alternatives={s["slot_id"]: LEVELS[position]
                                       for s in lo.slots_from_roster_positions(rpos)})
                self.assertEqual(bare, uniform, msg=f"{position} {rpos[:3]}")


class TheTwoDirectionsTests(unittest.TestCase):
    def test_no_TE_slot_the_deep_position_stops_being_free_at_the_flex(self):
        """The owner's league. Both RB slots held; three flexes open. Today a running back is
        priced against RB39 and a tight end against a top-10 tight end AT THE SAME SLOT, which is
        why the engine fields six running backs and no tight ends there."""
        alts = dr.shared_slot_alternatives(LEVELS, NO_TE_SLOT)
        roster = [_p(1, 260.0, "RB"), _p(2, 240.0, "RB"), _p(3, 300.0, "QB"),
                  _p(4, 280.0, "WR"), _p(5, 270.0, "WR")]
        priced = {}
        for position in ("RB", "WR", "TE"):
            new = lo.displacement_level(roster, NO_TE_SLOT, position, LEVELS[position],
                                        slot_alternatives=alts)
            old = lo.displacement_level(roster, NO_TE_SLOT, position, LEVELS[position])
            priced[position] = (250.0 - LEVELS[position] + old["adjustment"],
                                250.0 - LEVELS[position] + new["adjustment"])
        # Today: the running back carries a 107-point head start over the receiver and 158 over
        # the tight end, at a slot all three are competing for.
        self.assertGreater(priced["RB"][0] - priced["WR"][0], 100.0)
        self.assertGreater(priced["RB"][0] - priced["TE"][0], 150.0)
        # Under the shared alternative they are within a tight end's own scarcity of each other,
        # and the running back's advantage is gone entirely.
        self.assertEqual(priced["RB"][1], priced["WR"][1])
        self.assertLess(priced["RB"][1] - priced["TE"][1], 20.0)

    def test_one_TE_slot_the_surplus_tight_end_stops_being_cheap_at_the_flex(self):
        """12T_ppr. The TE slot is held by a better tight end, so a further tight end can only
        reach a flex -- where he must be priced against the same alternative the receiver is."""
        levels = {"QB": 300.0, "RB": 150.0, "WR": 207.0, "TE": 177.0}
        alts = dr.shared_slot_alternatives(levels, TE_SLOT)
        roster = [_p(1, 250.0, "TE"), _p(2, 300.0, "QB"),
                  _p(3, 280.0, "WR"), _p(4, 270.0, "WR")]
        te_new = lo.displacement_level(roster, TE_SLOT, "TE", levels["TE"], slot_alternatives=alts)
        te_old = lo.displacement_level(roster, TE_SLOT, "TE", levels["TE"])
        self.assertEqual(te_old["adjustment"], 0.0)          # today: the flex looks free at TE177
        self.assertEqual(te_new["adjustment"], -30.0)        # 177 - 207, the receiver's anchor
        wr_new = lo.displacement_level(roster, TE_SLOT, "WR", levels["WR"], slot_alternatives=alts)
        # Same slot, same alternative: a 250-point tight end and a 250-point receiver now carry
        # the identical price. That equality IS the repair.
        self.assertEqual(250.0 - levels["TE"] + te_new["adjustment"],
                         250.0 - levels["WR"] + wr_new["adjustment"])


class TheBoardAsksForItTests(unittest.TestCase):
    def test_displacement_adjustments_passes_the_shared_alternative_through(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(dr.displacement_adjustments).lstrip())
        called = {n.func.id for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("shared_slot_alternatives", called)
        kwargs = {kw.arg for n in ast.walk(tree) if isinstance(n, ast.Call) for kw in n.keywords}
        self.assertIn("slot_alternatives", kwargs)


# ---------------------------------------------------------------------------------------
# MUTATION RESULTS -- filled in by the pass; see evidence/roster_shape/shared_slot/mutations/
# ---------------------------------------------------------------------------------------
