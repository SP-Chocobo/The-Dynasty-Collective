"""acting_now_value is COMPUTED and CARRIED, and it does not order the board (#22).

This file used to assert the opposite. The blind pass found positional_forfeit computed on
every candidate, rendered to the user, folded into pick_necessity -- and read by neither
ordering authority; the first defense of a 16-round draft went in round 5 on a row carrying
tav 34.47 and forfeit 0.13 in the same snapshot. The repair made that number the sort key, and
against a FIXED field of heuristic opponents it cost 6.090% of starting-lineup points across
six formats, winning 10 of 68 seats where the value order won 56.

The cause is structural, which is why these tests now guard the other direction.
`acting_now(i) = F(i) - F(i + expected_taken)` is a NUMERICAL DERIVATIVE: it carries a curve's
local SLOPE and discards its HEIGHT, so at depth 30 of a real board a quarterback worth -208.35
outranked a running back worth +4.68. See evidence/smoke_seats/V2_MECHANISM.md.

What is held here: the quantity's definition, its absence contract, the cancellation its first
implementation got wrong, the narrowing that puts a buried position in front of a person -- and
a guard that the number does not reach the order again.
"""

import ast
import pathlib
import unittest

import pick_synthesis as ps


class TheAlternativeIsMeasuredOrAbsent(unittest.TestCase):
    """acting_now_value's absence contract (#187), which is the whole reason it is Optional."""

    def test_it_is_the_gap_between_the_candidate_and_his_own_next_turn_alternative(self):
        self.assertAlmostEqual(ps.acting_now_value(34.47, 33.42), 1.05, places=2)

    def test_an_unknown_alternative_is_absent_not_zero(self):
        # 0.0 reads as "measured, and acting now gains exactly nothing" -- the strongest
        # possible argument for waiting, asserted from an absence. Upside mode and a
        # back-to-back turn both reach this branch legitimately.
        self.assertIsNone(ps.acting_now_value(34.47, None))

    def test_an_unpriced_candidate_is_absent_not_zero(self):
        self.assertIsNone(ps.acting_now_value(None, 33.42))

    def test_a_measured_zero_survives_as_a_number(self):
        # The companion to the two above, and the reason they cannot be written as `if not`:
        # a candidate worth exactly what his replacement is worth HAS been measured.
        self.assertEqual(ps.acting_now_value(12.5, 12.5), 0.0)


class TheTeamSpecificTermsCancel(unittest.TestCase):
    """The defect the first implementation of this repair shipped, pinned so it cannot return.

    Subtracting forfeit's team-AGNOSTIC curve from a team-relative candidate leaves the
    team-specific terms ADDED rather than cancelled. Measured on a real round-9 board, every
    kicker and defense then carried a flat +4.00 need_bonus for a dedicated slot that is still
    empty at the next turn -- so the replacement earns the same +4.00 and neither should be
    credited for it. Both operands must come from the same column.
    """

    def test_a_flat_slot_bonus_on_both_sides_does_not_reach_the_order(self):
        # Same player, same position, once with an empty dedicated slot and once without.
        # need_bonus moves team_acquisition_value AND the alternative by the same 4.00.
        without = ps.acting_now_value(30.47, 29.42)
        with_empty_slot = ps.acting_now_value(30.47 + 4.00, 29.42 + 4.00)
        self.assertAlmostEqual(without, with_empty_slot, places=6)

    def test_the_best_player_at_a_position_is_worth_exactly_his_positions_forfeit(self):
        # best_now - curve_at IS forfeit, so for the best player at a position the two
        # quantities coincide. That identity is what proves the cancellation is exact rather
        # than approximately right on the boards that happened to be measured.
        best_now, forfeit = 30.47, 1.05
        self.assertAlmostEqual(
            ps.acting_now_value(best_now, best_now - forfeit), forfeit, places=6)


class TheValueOrderRulesTheBoard(unittest.TestCase):
    """_board_order is the key again, read on the candidate dict's own name for the quantity.

    build_snapshot renames the board's `final_score` to `team_acquisition_value` at the
    boundary, so the candidate caller passes `value_key` rather than hand-listing a second copy
    of this tuple (#126). These assert it is the SAME key, not a lookalike.
    """

    @staticmethod
    def row(pid, tav=None, acting=None, fills=False):
        return {"player_id": pid, "team_acquisition_value": tav,
                "acting_now_value": acting, "fills_required_slot": fills}

    def ordered(self, rows):
        return [r["player_id"] for r in
                sorted(rows, key=lambda c: ps._board_order(c, "team_acquisition_value"))]

    def test_the_feasibility_backstop_still_leads(self):
        rows = [self.row("rich", tav=99.0), self.row("backstop", tav=-50.0, fills=True)]
        self.assertEqual(self.ordered(rows)[0], "backstop")

    def test_an_unpriced_row_never_outranks_a_priced_one(self):
        rows = [self.row("unpriced"), self.row("priced", tav=-99.0)]
        self.assertEqual(self.ordered(rows), ["priced", "unpriced"])

    def test_highest_value_leads(self):
        rows = [self.row("low", tav=1.0), self.row("high", tav=9.0), self.row("mid", tav=5.0)]
        self.assertEqual(self.ordered(rows), ["high", "mid", "low"])

    def test_exact_ties_break_on_player_id_not_on_arrival_order(self):
        forward = self.ordered([self.row("b", tav=5.0), self.row("a", tav=5.0)])
        backward = self.ordered([self.row("a", tav=5.0), self.row("b", tav=5.0)])
        self.assertEqual(forward, backward)
        self.assertEqual(forward, ["a", "b"])

    def test_a_steep_local_slope_does_not_promote_a_worthless_player(self):
        # THE MEASURED REGRESSION, as a unit. Real numbers from depth 30 of a 12T_ppr board:
        # the quarterback carries MORE acting_now_value than the running back and is worth 213
        # points less. Ordering on the derivative took him; ordering on value does not.
        rows = [self.row("qb_deep", tav=-208.35, acting=3.81),
                self.row("rb_ok", tav=4.68, acting=3.58)]
        self.assertEqual(self.ordered(rows)[0], "rb_ok")
        self.assertGreater(rows[0]["acting_now_value"], rows[1]["acting_now_value"],
                           "fixture is vacuous unless the worthless row really does carry more")

    def test_it_is_the_same_key_the_board_uses_under_the_other_name(self):
        # NON-VACUITY for value_key: the default and the override must agree on one row that
        # carries the quantity under both names, or this is two keys wearing one name.
        row = {"player_id": "x", "final_score": 7.0, "team_acquisition_value": 7.0}
        self.assertEqual(ps._board_order(row),
                         ps._board_order(row, "team_acquisition_value"))


class TheAssumptionTheRepairRestsOn(unittest.TestCase):
    """Re-sorting a set narrowed by a DIFFERENT key is cosmetic unless the candidate this order
    promotes is in the set at all.

    narrow_candidates admits the top `position_depth` rows at every position regardless of
    board rank, which is what puts a skill player the value order buried deep into the set this
    re-sorts. If that admission ever narrows to the value-ranked head alone, this repair stops
    working and every test above it goes on passing.
    """

    @staticmethod
    def board():
        # Twelve defenses hold the whole value-ranked head, exactly as the real round-9 board
        # measured in evidence/blind_pass/KDST_VALUATION.md does.
        rows = [{"player_id": f"def{i}", "position": "DEF", "name": f"D{i}",
                 "final_score": 34.0 - i} for i in range(12)]
        rows += [{"player_id": f"wr{i}", "position": "WR", "name": f"W{i}",
                  "final_score": -18.0 - i} for i in range(5)]
        return rows

    def test_the_best_player_at_a_buried_position_is_in_the_narrowed_set(self):
        board = self.board()
        narrowed = ps.narrow_candidates(board, top_n=5)
        ids = [r["player_id"] for r in narrowed]
        self.assertIn("wr0", ids,
                      "the best WR is outside the value-ranked top 5 and must still be admitted")

    def test_that_admission_is_doing_real_work_here(self):
        # NON-VACUITY. If the best WR were inside the value-ranked head anyway, the test above
        # would hold with or without the per-position admission it exists to protect.
        board = self.board()
        by_value = sorted(board, key=ps._board_order)[:5]
        self.assertNotIn("wr0", [r["player_id"] for r in by_value])


class TheObservableDoesNotReachTheOrder(unittest.TestCase):
    """Every test above this one passes with the sort line pointed back at acting_now_value.

    The key and the derivation are pure functions; proving them correct proves nothing about
    what build_snapshot sorts on. That gap is the same shape as the defect the original repair
    addressed -- a quantity computed correctly and read by nobody -- so it is closed here in
    both directions rather than assumed.

    Scans the CODE, not the source text (#200): a guard that greps for a string passes on a
    line inside a comment and fails on an idiom that wraps across two lines. This file is full
    of the phrase `acting_now_value` in prose, so a text guard here would be worse than none.
    """

    @staticmethod
    def _build_snapshot():
        tree = ast.parse(pathlib.Path("pick_synthesis.py").read_text())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "build_snapshot"), None)
        assert fn is not None, "build_snapshot is gone -- this guard is measuring nothing"
        return fn

    @staticmethod
    def _sort_calls(fn):
        return [n for n in ast.walk(fn)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "sort"]

    def test_build_snapshot_orders_its_candidates_on_the_value_key(self):
        calls = self._sort_calls(self._build_snapshot())
        keyed = [n for n in calls
                 for kw in n.keywords
                 if kw.arg == "key"
                 and any(isinstance(sub, ast.Name) and sub.id == "_board_order"
                         for sub in ast.walk(kw.value))]
        self.assertEqual(len(keyed), 1, (
            "build_snapshot must order its narrowed candidates on _board_order exactly once"))

    def test_no_sort_in_build_snapshot_reads_acting_now_value(self):
        # THE REGRESSION GUARD. Any sort key in this function that mentions the observable --
        # by function name or by dict key -- is the reverted ordering coming back.
        for call in self._sort_calls(self._build_snapshot()):
            for kw in call.keywords:
                if kw.arg != "key":
                    continue
                names = {sub.id for sub in ast.walk(kw.value) if isinstance(sub, ast.Name)}
                consts = {sub.value for sub in ast.walk(kw.value)
                          if isinstance(sub, ast.Constant) and isinstance(sub.value, str)}
                self.assertNotIn("_acting_now_order", names)
                self.assertNotIn("acting_now_value", names | consts, (
                    "a sort key in build_snapshot reads acting_now_value -- that ordering was "
                    "reverted at #22 and cost 6.090% of starting-lineup points"))

    def test_the_retired_ordering_key_is_gone_rather_than_merely_unused(self):
        # An unused key is an invitation. It was removed, not left dangling.
        self.assertFalse(hasattr(ps, "_acting_now_order"))

    def test_the_order_is_settled_before_necessity_reads_the_list_as_ranked(self):
        # compute_pick_necessity, near_tie_flags ("near tie with the LEADER") and
        # decision_regime all read raw_candidates as already ranked. Sorting after any of them
        # leaves the snapshot describing one leader and recommending another.
        fn = self._build_snapshot()
        def line_of(pred):
            return min((n.lineno for n in ast.walk(fn) if pred(n)), default=None)
        sort_line = line_of(lambda n: isinstance(n, ast.Call)
                            and isinstance(n.func, ast.Attribute) and n.func.attr == "sort"
                            and any(kw.arg == "key"
                                    and any(isinstance(sub, ast.Name) and sub.id == "_board_order"
                                            for sub in ast.walk(kw.value))
                                    for kw in n.keywords))
        self.assertIsNotNone(sort_line, "no _board_order sort found in build_snapshot")
        for reader in ("compute_pick_necessity", "near_tie_flags", "decision_regime"):
            reader_line = line_of(lambda n, r=reader: isinstance(n, ast.Call)
                                  and isinstance(n.func, ast.Name) and n.func.id == r)
            self.assertIsNotNone(reader_line, f"{reader} is no longer called here")
            self.assertLess(sort_line, reader_line,
                            f"{reader} reads the candidate list before it has been ordered")

    def test_every_candidate_still_carries_the_observable(self):
        # The revert removed the ordering, NOT the number. A field the dataclass does not carry
        # cannot reach the card, and the failure would be a silently absent measurement.
        import dataclasses
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("acting_now_value", names)
        self.assertIn("position_next_turn_value", names)


if __name__ == "__main__":
    unittest.main()
