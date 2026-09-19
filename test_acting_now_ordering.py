"""The board orders on what acting NOW is worth, not on what the player is worth (#52).

The blind pass found positional_forfeit computed on every candidate of every board, rendered
to the user, folded into pick_necessity -- and read by neither ordering authority. The first
defense of a 16-round draft went in round 5 on a row carrying tav 34.47 and forfeit 0.13 in
the same snapshot. These tests hold the repair, and the load-bearing assumption under it.
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


class TheOrderKeepsWhatTheOldOneGuaranteed(unittest.TestCase):
    """_acting_now_order is a THIRD ordering authority (#155). It may re-rank priced rows; it
    may not reverse the feasibility backstop or promote an unpriced row."""

    @staticmethod
    def row(pid, acting=None, tav=None, fills=False):
        return {"player_id": pid, "acting_now_value": acting,
                "team_acquisition_value": tav, "fills_required_slot": fills}

    def ordered(self, rows):
        return [r["player_id"] for r in sorted(rows, key=ps._acting_now_order)]

    def test_the_feasibility_backstop_still_leads(self):
        rows = [self.row("rich", acting=99.0, tav=99.0),
                self.row("backstop", acting=-50.0, tav=-50.0, fills=True)]
        self.assertEqual(self.ordered(rows)[0], "backstop")

    def test_an_unpriced_row_never_outranks_a_priced_one(self):
        rows = [self.row("unpriced"), self.row("priced", acting=-99.0, tav=-99.0)]
        self.assertEqual(self.ordered(rows), ["priced", "unpriced"])

    def test_a_measured_row_leads_an_unmeasured_one_even_when_it_scores_lower(self):
        # An absent acting_now_value is not a low one. The block that has no measurement sorts
        # after the block that does, rather than being handed a number to compete with.
        rows = [self.row("measured", acting=-20.0, tav=-20.0),
                self.row("unmeasured", acting=None, tav=500.0)]
        self.assertEqual(self.ordered(rows), ["measured", "unmeasured"])

    def test_unmeasured_rows_keep_the_previous_key_among_themselves(self):
        # THE UPSIDE-MODE PRESERVATION. draft_strategy builds no curves there, so every row
        # lands in this block and the order must be exactly the one this repair replaced.
        rows = [self.row("low", tav=1.0), self.row("high", tav=9.0), self.row("mid", tav=5.0)]
        self.assertEqual(self.ordered(rows), ["high", "mid", "low"])

    def test_exact_ties_break_on_player_id_not_on_arrival_order(self):
        # The same determinism gap _board_order and draft_room's own sort both close.
        forward = self.ordered([self.row("b", acting=5.0, tav=5.0),
                                self.row("a", acting=5.0, tav=5.0)])
        backward = self.ordered([self.row("a", acting=5.0, tav=5.0),
                                 self.row("b", acting=5.0, tav=5.0)])
        self.assertEqual(forward, backward)
        self.assertEqual(forward, ["a", "b"])


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


class TheOrderIsActuallyWiredIntoTheSnapshot(unittest.TestCase):
    """Every test above this one passes with the sort line deleted.

    The key and the derivation are pure functions; proving them correct proves nothing about
    whether build_snapshot calls them. That gap is the same shape as the defect this whole
    repair addresses -- a quantity computed correctly and read by nobody -- so it is closed
    here rather than assumed.

    Scans the CODE, not the source text (#200): a guard that greps for a string passes on a
    line inside a comment and fails on an idiom that wraps across two lines.
    """

    @staticmethod
    def _build_snapshot_body():
        tree = ast.parse(pathlib.Path("pick_synthesis.py").read_text())
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "build_snapshot"), None)
        assert fn is not None, "build_snapshot is gone -- this guard is measuring nothing"
        return fn

    def test_build_snapshot_sorts_its_candidates_on_the_acting_now_key(self):
        sorts = [n for n in ast.walk(self._build_snapshot_body())
                 if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute) and n.func.attr == "sort"
                 and any(kw.arg == "key" and isinstance(kw.value, ast.Name)
                         and kw.value.id == "_acting_now_order" for kw in n.keywords)]
        self.assertEqual(len(sorts), 1, (
            "build_snapshot must order its narrowed candidates on _acting_now_order exactly "
            "once -- deleting it silently restores the round-5 defense"))

    def test_the_key_is_applied_before_necessity_reads_the_list_as_ranked(self):
        # compute_pick_necessity, near_tie_flags ("near tie with the LEADER") and
        # decision_regime all read raw_candidates as already ranked. Sorting after any of them
        # leaves the snapshot describing one leader and recommending another.
        body = self._build_snapshot_body()
        def line_of(pred):
            return min((n.lineno for n in ast.walk(body) if pred(n)), default=None)
        sort_line = line_of(lambda n: isinstance(n, ast.Call)
                            and isinstance(n.func, ast.Attribute) and n.func.attr == "sort"
                            and any(kw.arg == "key" and isinstance(kw.value, ast.Name)
                                    and kw.value.id == "_acting_now_order" for kw in n.keywords))
        for reader in ("compute_pick_necessity", "near_tie_flags", "decision_regime"):
            reader_line = line_of(lambda n, r=reader: isinstance(n, ast.Call)
                                  and isinstance(n.func, ast.Name) and n.func.id == r)
            self.assertIsNotNone(reader_line, f"{reader} is no longer called here")
            self.assertLess(sort_line, reader_line,
                            f"{reader} reads the candidate list before it has been ordered")

    def test_every_candidate_carries_the_two_numbers_the_key_reads(self):
        # A field the dataclass does not carry cannot reach the key, and the failure would be
        # a silently absent measurement rather than an error.
        import dataclasses
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("acting_now_value", names)
        self.assertIn("position_next_turn_value", names)


if __name__ == "__main__":
    unittest.main()
