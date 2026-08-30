"""#61 -- the survival layer's ordinal register.

`_build_opponent_boards` numbers every row on an opponent's board `1..n` and hands that
mapping to two consumers, both of which read the number through RANK_TAKE_PROBABILITY, a
table whose keys mean "the consensus best player available", "the second best", and so on.

For a PRICED row that reading is right: the ordinal came from team_acquisition_value.
For an UNPRICED row -- one whose position has no replacement level to measure against, so
the board carries absence rather than a value -- the ordinal came from the deterministic
tiebreak that keeps the board's order stable. It is not a valuation, and it may not be
read as one. This is the same register error as the identity and horizon boundaries
upstream, in the one place it changes a number a user is shown.

Measured live before the repair, round 16 of a real 12x20 board: three unpriced targets --
a WR at board ordinal 79, a WR at 110, and the very last row on the board, a K at 141 of
141 -- all received the identical survival probability of 0.641, because all three fell
past the table's five keys onto RANK_TAKE_PROBABILITY_FLOOR. The number was not wrong.
The claim to have measured it was: the ordinal contributed nothing, and nothing in the
output said so.

WHAT THIS FILE FIXES AND WHAT IT DELIBERATELY LEAVES OPEN. It fixes the register: only
valuation ordinals reach the table. It does NOT decide what an unevidenced take-
probability should be. The floor is what production already produces for these rows, so
keeping it changes no number -- it only makes the basis explicit and labels it, so no
consumer can present it as a measurement. Whether an unpriced-but-draftable player should
instead be treated as zero-risk is a product decision with no evidence in this repository
to settle it, and it is recorded as such rather than guessed at here.
"""
import math
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
ROSTER_IDS = [str(i) for i in range(1, NUM_TEAMS + 1)]


def _is_absent(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


class _LateBoardFixture(unittest.TestCase):
    """A real board drained deep enough that whole positions stop being measurable -- the
    only state in which an unpriced row can reach the strategic layer at all, and one the
    real 12x20 board does reach (round 16: 63 unpriced of 141)."""

    ROUND = 16

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            for _, row in proj[proj["position"] == position].sort_values(
                    "trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        opening = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id="1",
                                        league=DYNASTY, mode="balanced")
        taken = cls.ROUND * NUM_TEAMS
        cls.picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                      "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                     for i, r in enumerate(opening[:taken])]
        cls.board = dr.compute_draft_board(cls.merger, cls.players_db, cls.picks,
                                           my_roster_id="1", league=DYNASTY, mode="balanced")
        cls.boards = ds._build_opponent_boards(cls.merger, cls.players_db, cls.picks,
                                               DYNASTY, ROSTER_IDS, mode="balanced")
        cls.pick_order = ds.generate_pick_order(ROSTER_IDS, cls.ROUND + 5, "snake")
        cls.current_index = next(i for i in range(taken, len(cls.pick_order))
                                 if cls.pick_order[i] == "1")

    def _split(self):
        priced = [r for r in self.board if not _is_absent(r.get("final_score"))]
        unpriced = [r for r in self.board if _is_absent(r.get("final_score"))]
        return priced, unpriced

    def _survival(self, player_id):
        return ds.estimate_survival(self.picks, self.players_db, self.pick_order,
                                    self.current_index, "1", player_id, self.boards,
                                    league=DYNASTY)


class FixtureReachesTheStateTests(_LateBoardFixture):
    """If the fixture cannot produce an unpriced row that a real caller would hand to the
    strategic layer, nothing below proves anything -- so that is asserted first."""

    def test_the_late_board_really_does_carry_unpriced_rows(self):
        priced, unpriced = self._split()
        self.assertTrue(priced, "a board with nothing priced would be a different defect")
        self.assertTrue(unpriced, "fixture did not reach the state this file is about")

    def test_a_whole_position_can_be_unpriced_which_is_how_one_reaches_the_layer(self):
        # pick_synthesis.narrow_candidates always adds the best remaining player at every
        # position the board covers, unconditionally. So a position with no priced rows left
        # hands an unpriced candidate straight to pick_analysis -> estimate_survival. This is
        # what makes the defect live rather than latent.
        by_position = {}
        for row in self.board:
            by_position.setdefault(row["position"], []).append(row)
        all_unpriced = [pos for pos, rows in by_position.items()
                        if rows and all(_is_absent(r.get("final_score")) for r in rows)]
        self.assertTrue(all_unpriced,
                        "no position is entirely unpriced, so best-at-position never "
                        "surfaces an unpriced candidate in this fixture")


class OrdinalRegisterTests(_LateBoardFixture):
    """rank_by_id is a VALUATION ordinal or it is nothing."""

    def test_rank_by_id_contains_no_unpriced_row(self):
        _, unpriced = self._split()
        unpriced_ids = {r["player_id"] for r in unpriced}
        for roster_id, board in self.boards.items():
            leaked = unpriced_ids & set(board["rank_by_id"])
            self.assertEqual(leaked, set(),
                             f"roster {roster_id}: unpriced rows carry a valuation ordinal")

    def test_every_row_is_either_ranked_or_declared_unpriced_never_both_and_never_neither(self):
        for roster_id, board in self.boards.items():
            ranked = set(board["rank_by_id"])
            unpriced = set(board["unpriced_ids"])
            self.assertEqual(ranked & unpriced, set(), f"roster {roster_id}: a row is both")
            self.assertEqual(ranked | unpriced, set(board["by_id"]),
                             f"roster {roster_id}: a row is neither")

    def test_the_ranks_that_remain_are_dense_and_start_at_one(self):
        for roster_id, board in self.boards.items():
            ranks = sorted(board["rank_by_id"].values())
            self.assertEqual(ranks, list(range(1, len(ranks) + 1)),
                             f"roster {roster_id}: valuation ordinals are not dense")


class UnevidencedRiskTests(_LateBoardFixture):
    """What the layer reports for a target it cannot value."""

    def _an_unpriced_target(self):
        _, unpriced = self._split()
        self.assertTrue(unpriced)
        return unpriced[0]

    def test_an_unpriced_target_is_still_at_risk_rather_than_silently_safe(self):
        # The opposite failure would be treating "no valuation" as "no one can take him".
        # An unpriced player is on the board and can absolutely be drafted.
        result = self._survival(self._an_unpriced_target()["player_id"])
        self.assertTrue(result["risk_by_team"], "an unpriced target drew no risk at all")
        self.assertLess(result["survival_probability"], 1.0)

    def test_every_take_probability_for_an_unpriced_target_is_the_floor(self):
        result = self._survival(self._an_unpriced_target()["player_id"])
        for risk in result["risk_by_team"]:
            self.assertAlmostEqual(risk["take_probability"], ds.RANK_TAKE_PROBABILITY_FLOOR)

    def test_the_unevidenced_rows_say_so_instead_of_reporting_a_rank(self):
        result = self._survival(self._an_unpriced_target()["player_id"])
        for risk in result["risk_by_team"]:
            self.assertFalse(risk["evidenced"],
                             "an unpriced target's risk row claims to be evidenced")
            self.assertIsNone(risk["rank_on_their_board"],
                              "an unpriced target's risk row reports a valuation ordinal")
        self.assertEqual(result["unevidenced_picks"], len(result["risk_by_team"]))

    def test_the_identical_answer_for_differently_placed_unpriced_targets_is_now_explicit(self):
        # The original measurement: a WR at board ordinal 79, a WR at 110 and the last row on
        # the board all returned 0.641. That is still what they return -- the repair does not
        # move a number -- but it now follows from a stated rule rather than from three
        # different tiebreak ordinals all missing the same table.
        _, unpriced = self._split()
        self.assertGreaterEqual(len(unpriced), 3)
        picks = [unpriced[0], unpriced[len(unpriced) // 2], unpriced[-1]]
        results = [self._survival(row["player_id"]) for row in picks]
        first = results[0]["survival_probability"]
        for row, result in zip(picks, results):
            self.assertEqual(result["survival_probability"], first, row["name"])
            self.assertEqual(result["unevidenced_picks"], len(result["risk_by_team"]))

    def test_the_pace_prior_does_not_run_on_an_unevidenced_target(self):
        # _pace_based_take_probability divides the position's pace deficit by the target's own
        # rank AMONG REMAINING PLAYERS AT HIS POSITION on that opponent's board -- another
        # valuation ordinal. An unpriced target has none, so the prior has no denominator.
        result = self._survival(self._an_unpriced_target()["player_id"])
        for risk in result["risk_by_team"]:
            self.assertFalse(risk["pace_driven"],
                             "the pace prior priced a target the board could not value")


class PacePriorDenominatorTests(unittest.TestCase):
    """The third site in this module reading the same register, and the one the real data
    cannot currently reach.

    _pace_based_take_probability divides the position's pace deficit by the target's rank AMONG
    REMAINING PLAYERS AT HIS POSITION, computed by sorting `board["by_id"]` on universal_value.
    An unpriced row's universal_value is NaN, and every comparison against NaN is False, so
    list.sort silently produces a NON-TOTAL order the moment one is present -- the resulting
    "rank" is not a rank, and which row lands where depends on input order.

    REACHABILITY, measured rather than assumed. The prior returns None past
    SUPERFLEX_QB_PACE_ANCHORS[-1][0] (48 picks, i.e. the first four rounds), and the real 12x20
    board's first unpriced row does not appear until round 15. So on today's data the two never
    overlap and this is a latent hazard, not a live defect -- which is exactly why the fixture
    below is CONSTRUCTED. A test that can only observe its subject on data that does not exist
    yet would report a pass while proving nothing, the failure mode this suite has hit before.
    The board dict is built by hand to the shape _build_opponent_boards emits."""

    ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"] + ["BN"] * 10

    def _board(self, priced_values, unpriced_count):
        rows, unpriced_ids = {}, set()
        for i, value in enumerate(priced_values):
            pid = f"p{i}"
            rows[pid] = {"player_id": pid, "name": f"Priced {i}", "position": "QB",
                         "universal_value": value, "final_score": value}
        for i in range(unpriced_count):
            pid = f"u{i}"
            rows[pid] = {"player_id": pid, "name": f"Unpriced {i}", "position": "QB",
                         "universal_value": float("nan"), "final_score": float("nan")}
            unpriced_ids.add(pid)
        ranked = [r for r in rows.values() if r["player_id"] not in unpriced_ids]
        ranked.sort(key=lambda r: -r["universal_value"])
        return {"by_id": rows,
                "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(ranked)},
                "unpriced_ids": unpriced_ids}

    def _probability(self, board, target):
        # Zero QBs actually drafted against the convention's own 6-by-round-1 anchor, so the
        # deficit is real and the prior returns a number rather than None.
        picks = [{"player_id": "x", "roster_id": "1", "round": 1, "pick_no": 1}]
        players_db = {"x": {"first_name": "A", "last_name": "B", "position": "RB",
                            "fantasy_positions": ["RB"]}}
        return ds._pace_based_take_probability("QB", target, board, 12, picks, players_db,
                                               self.ROSTER)

    def test_the_denominator_counts_only_players_the_board_could_value(self):
        # Eight unpriced QBs surrounding three priced ones. The worst priced QB is rank 3 of 3,
        # and his probability must be the best QB's divided by exactly 3 -- not by some larger
        # number produced by unpriced rows occupying places in the ordering.
        board = self._board([90.0, 60.0, 30.0], unpriced_count=8)
        best = self._probability(board, "p0")
        worst = self._probability(board, "p2")
        self.assertIsNotNone(best)
        self.assertIsNotNone(worst)
        self.assertAlmostEqual(best / worst, 3.0, places=9,
                               msg="unpriced rows are inflating the pace denominator")

    def test_an_unpriced_target_gets_no_pace_estimate_at_all(self):
        board = self._board([90.0, 60.0, 30.0], unpriced_count=8)
        self.assertIsNone(self._probability(board, "u0"),
                          "the pace prior ranked a player the board could not value")

    def test_the_ordering_does_not_depend_on_which_order_the_rows_arrived_in(self):
        # The NaN-sort symptom directly: reverse the dict's insertion order and the answer must
        # not move. Under a non-total comparison it does.
        board = self._board([90.0, 60.0, 30.0], unpriced_count=8)
        shuffled = dict(board)
        shuffled["by_id"] = dict(reversed(list(board["by_id"].items())))
        for target in ("p0", "p1", "p2"):
            self.assertAlmostEqual(self._probability(board, target),
                                   self._probability(shuffled, target), places=12,
                                   msg=f"{target}'s pace rank depends on row arrival order")


class PricedBehaviourIsUnchangedTests(_LateBoardFixture):
    """The repair separates registers; it must not touch the evidenced path."""

    def _a_priced_target(self):
        priced, _ = self._split()
        self.assertTrue(priced)
        return priced[0]

    def test_a_priced_target_still_draws_real_ranks_and_above_floor_risk(self):
        result = self._survival(self._a_priced_target()["player_id"])
        self.assertTrue(result["risk_by_team"])
        for risk in result["risk_by_team"]:
            self.assertTrue(risk["evidenced"])
            self.assertIsInstance(risk["rank_on_their_board"], int)
        self.assertTrue(any(r["take_probability"] > ds.RANK_TAKE_PROBABILITY_FLOOR
                            for r in result["risk_by_team"]),
                        "the board's best remaining player drew only floor risk")
        self.assertEqual(result["unevidenced_picks"], 0)

    def test_a_target_absent_from_an_opponents_pool_still_contributes_no_risk(self):
        # The third case, and the one that must stay distinct from "unpriced": a player who is
        # not in that team's usable-position pool at all cannot be taken by them.
        target = self._a_priced_target()
        boards = {rid: {"by_id": {k: v for k, v in b["by_id"].items()
                                  if k != target["player_id"]},
                        "rank_by_id": {k: v for k, v in b["rank_by_id"].items()
                                       if k != target["player_id"]},
                        "unpriced_ids": set(b["unpriced_ids"]) - {target["player_id"]}}
                  for rid, b in self.boards.items()}
        result = ds.estimate_survival(self.picks, self.players_db, self.pick_order,
                                      self.current_index, "1", target["player_id"], boards,
                                      league=DYNASTY)
        self.assertEqual(result["risk_by_team"], [])
        self.assertEqual(result["survival_probability"], 1.0)


class ForfeitReadsTheSameRegisterTests(_LateBoardFixture):
    """The second consumer of rank_by_id. expected_positional_forfeit sums
    RANK_TAKE_PROBABILITY over every row inside FORFEIT_OPPONENT_BOARD_DEPTH -- the same
    table, the same register error, and it is fixed by the same change rather than
    separately."""

    def test_no_unpriced_row_can_contribute_to_expected_taken(self):
        _, unpriced = self._split()
        unpriced_ids = {r["player_id"] for r in unpriced}
        for roster_id, board in self.boards.items():
            inside_depth = {pid for pid, rank in board["rank_by_id"].items()
                            if rank <= ds.FORFEIT_OPPONENT_BOARD_DEPTH}
            self.assertEqual(inside_depth & unpriced_ids, set(),
                             f"roster {roster_id}: an unpriced row sits inside the forfeit "
                             "window and is being read as a top-of-board valuation")


if __name__ == "__main__":
    unittest.main()
