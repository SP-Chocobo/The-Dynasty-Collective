"""The flex share is MEASURED, and the assumed one cannot pass for it.

`starter_slot_counts` used to split a flex slot evenly across the positions it admits, and
defended that in its own docstring with a claim about the world. `fielded_flex_occupancy` asks
the data instead. These tests pin the three things that can go wrong:

  1. the measurement itself (who occupies which slot type, and REFUSING rather than guessing);
  2. the arithmetic that turns occupancy into a per-team slot count (the divisor is the one
     place a plausible wrong answer hides -- a league with two FLEX slots double-counts if the
     appearance count is dropped);
  3. the boundary: a caller that supplies nothing still gets today's even split, and cannot tell
     itself it measured something.

MUTATION SURVIVORS ARE RECORDED AT THE BOTTOM OF THIS FILE.
"""
import unittest
from unittest import mock

import draft_room as dr


def _db(rows):
    """{player_id: sleeper-shaped info} from (id, position) pairs."""
    return {pid: {"player_id": pid, "position": pos, "fantasy_positions": [pos],
                  "first_name": pid, "last_name": pos} for pid, pos in rows}


class FieldedFlexOccupancyTests(unittest.TestCase):
    def test_a_flex_goes_to_the_position_that_actually_wins_it(self):
        # One team, one WR slot and one FLEX. The two best players are receivers, so the FLEX is
        # a receiver's -- the even split would have called it a third of a tight end.
        db = _db([("w1", "WR"), ("w2", "WR"), ("t1", "TE")])
        points = {"w1": 300.0, "w2": 280.0, "t1": 100.0}
        occupancy = dr.fielded_flex_occupancy(points, db, ["WR", "FLEX"], 1)
        self.assertEqual(occupancy["FLEX"], {"WR": 1})

    def test_the_same_pool_hands_the_flex_to_a_tight_end_when_nothing_else_consumes_them(self):
        # The owner's league in miniature: NO dedicated TE slot, so the tight end is not consumed
        # and he outscores the second receiver. Same pool, same code, opposite answer -- which is
        # the whole point, and is what an even split cannot express.
        db = _db([("w1", "WR"), ("w2", "WR"), ("t1", "TE")])
        points = {"w1": 300.0, "w2": 100.0, "t1": 280.0}
        occupancy = dr.fielded_flex_occupancy(points, db, ["WR", "FLEX"], 1)
        self.assertEqual(occupancy["FLEX"], {"TE": 1})

    def test_every_team_is_fielded_not_just_one(self):
        db = _db([(f"w{i}", "WR") for i in range(6)] + [("t1", "TE")])
        points = {f"w{i}": 300.0 - i for i in range(6)}
        points["t1"] = 1.0
        occupancy = dr.fielded_flex_occupancy(points, db, ["WR", "FLEX"], 3)
        self.assertEqual(occupancy["WR"], {"WR": 3})
        self.assertEqual(occupancy["FLEX"], {"WR": 3})

    def test_a_multi_eligible_player_is_fielded_on_his_full_eligibility(self):
        """#172. A WR/TE listed player can occupy a TE slot; collapsing him to one bucket would
        leave that slot to somebody worse and mis-state who wins the flex behind it. He is
        COUNTED under his primary bucket, deliberately, because that is the population
        replacement_levels ranks over -- eligibility decides where he can go, `position` decides
        whose demand he is."""
        db = _db([("w1", "WR"), ("t1", "TE")])
        db["h1"] = {"player_id": "h1", "position": "WR", "fantasy_positions": ["WR", "TE"],
                    "first_name": "h", "last_name": "1"}
        points = {"h1": 300.0, "w1": 250.0, "t1": 10.0}
        occupancy = dr.fielded_flex_occupancy(points, db, ["WR", "TE"], 1)
        self.assertEqual(occupancy["WR"], {"WR": 1})
        self.assertEqual(occupancy["TE"], {"WR": 1})     # h1 fills the TE slot, counted as a WR

    def test_it_refuses_when_the_league_cannot_be_fully_fielded(self):
        # Four league slots, three players. A PARTIAL fielding would under-count exactly the
        # position that ran out, so it is not returned as a measurement at all.
        db = _db([("w1", "WR"), ("w2", "WR"), ("t1", "TE")])
        points = {"w1": 300.0, "w2": 280.0, "t1": 100.0}
        self.assertIsNone(dr.fielded_flex_occupancy(points, db, ["WR", "FLEX"], 2))

    def test_it_refuses_on_an_empty_pool_and_on_a_league_with_no_starting_slots(self):
        db = _db([("w1", "WR")])
        self.assertIsNone(dr.fielded_flex_occupancy({}, db, ["WR"], 1))
        self.assertIsNone(dr.fielded_flex_occupancy({"w1": 1.0}, db, ["BN", "BN"], 1))
        self.assertIsNone(dr.fielded_flex_occupancy({"w1": 1.0}, db, ["WR"], 0))

    def test_no_fielded_player_can_lack_a_position_and_here_is_why(self):
        """The guard against a None-keyed bucket is UNREACHABLE, and this proves the implication
        it rests on rather than the branch.

        A player only reaches the solve when player_eligible_positions is non-empty, and that
        function returns either a subset of FANTASY_POSITIONS (in which case player_position
        returns one of them) or {player_position(info)} for a truthy primary. So non-empty
        eligibility implies a non-None position, and the branch cannot fire today. It stays in
        the code as a refusal rather than a bucket keyed by None, because the thing it prevents
        -- a phantom position quietly becoming a share of somebody's starter demand -- is
        exactly the absence-read-as-a-value defect this repository keeps having to repair. It is
        a RECORDED mutation survivor, not an untested path nobody noticed."""
        from player_universe import player_eligible_positions, player_position
        shapes = [
            {"position": "WR"},
            {"fantasy_positions": ["WR", "TE"]},
            {"position": "FS", "fantasy_positions": ["DB"]},
            {"position": "DE", "fantasy_positions": ["DE"]},   # neither is a roster bucket
            {"position": "WR", "fantasy_positions": []},
            {"fantasy_positions": ["NOT_A_POSITION"], "position": "RB"},
        ]
        for info in shapes:
            if player_eligible_positions(info):
                self.assertIsNotNone(player_position(info), msg=repr(info))
        # ... and a record with nothing at all is dropped BEFORE the solve, not bucketed.
        db = _db([("w1", "WR")])
        db["x1"] = {"player_id": "x1"}
        occupancy = dr.fielded_flex_occupancy({"x1": 500.0, "w1": 1.0}, db, ["WR"], 1)
        self.assertEqual(occupancy, {"WR": {"WR": 1}})


class SlotCountsFromMeasuredOccupancyTests(unittest.TestCase):
    LEAGUE = ["QB", "WR", "WR", "RB", "RB", "FLEX", "FLEX", "WRRB_FLEX", "SUPER_FLEX"]

    def test_without_an_occupancy_the_answer_is_todays_even_split(self):
        counts = dr.starter_slot_counts(["WR", "FLEX"])
        self.assertAlmostEqual(counts["WR"], 1.0 + 1.0 / 3)
        self.assertAlmostEqual(counts["TE"], 1.0 / 3)
        self.assertAlmostEqual(counts["RB"], 1.0 / 3)

    def test_an_occupancy_without_num_teams_is_not_a_measurement(self):
        # Half the inputs is not a measurement, and must fall back rather than divide by None.
        counts = dr.starter_slot_counts(["WR", "FLEX"], {"FLEX": {"WR": 12}}, None)
        self.assertAlmostEqual(counts["TE"], 1.0 / 3)

    def test_a_position_that_wins_no_flex_gets_no_flex_share(self):
        counts = dr.starter_slot_counts(["WR", "FLEX"], {"FLEX": {"WR": 12}}, 12)
        self.assertAlmostEqual(counts["WR"], 2.0)
        self.assertEqual(counts["TE"], 0.0)
        self.assertEqual(counts["RB"], 0.0)

    def test_two_appearances_of_one_flex_type_are_not_double_counted(self):
        # THE DIVISOR. 24 FLEX slots across 12 teams IS two slots per team; adding the whole
        # per-team occupancy once per appearance would say four.
        counts = dr.starter_slot_counts(["FLEX", "FLEX"], {"FLEX": {"TE": 18, "WR": 6}}, 12)
        self.assertAlmostEqual(counts["TE"], 1.5)
        self.assertAlmostEqual(counts["WR"], 0.5)
        self.assertAlmostEqual(counts["TE"] + counts["WR"], 2.0)

    def test_a_slot_type_missing_from_the_occupancy_falls_back_for_that_slot_alone(self):
        # An UNMEASURED slot type is not an EMPTY one. The measured FLEX keeps its measurement;
        # the unmeasured WRRB_FLEX keeps the even split.
        counts = dr.starter_slot_counts(["FLEX", "WRRB_FLEX"], {"FLEX": {"TE": 12}}, 12)
        self.assertAlmostEqual(counts["TE"], 1.0)
        self.assertAlmostEqual(counts["WR"], 0.5)
        self.assertAlmostEqual(counts["RB"], 0.5)

    def test_a_measured_superflex_does_not_consult_the_hand_set_constant(self):
        # SUPER_FLEX_QB_SHARE was the one place the even split already admitted it was wrong, and
        # it admitted it with a hand-set 0.85. Under a measurement it is not consulted at all.
        measured = dr.starter_slot_counts(["SUPER_FLEX"], {"SUPER_FLEX": {"QB": 12}}, 12)
        self.assertEqual(measured["QB"], 1.0)
        self.assertEqual(measured["RB"], 0.0)
        assumed = dr.starter_slot_counts(["SUPER_FLEX"])
        self.assertAlmostEqual(assumed["QB"], dr.SUPER_FLEX_QB_SHARE)
        self.assertNotAlmostEqual(measured["QB"], assumed["QB"])

    def test_dedicated_slots_are_untouched_by_any_occupancy(self):
        for occupancy in (None, {"FLEX": {"WR": 12}}):
            counts = dr.starter_slot_counts(["QB", "RB", "RB"], occupancy, 12)
            self.assertEqual(counts["QB"], 1.0)
            self.assertEqual(counts["RB"], 2.0)


class SlotShareBasisTests(unittest.TestCase):
    def test_the_basis_says_which_answer_the_caller_will_get(self):
        self.assertEqual(dr.slot_share_basis({"FLEX": {"WR": 12}}, 12), dr.SLOT_SHARE_FIELDED)
        self.assertEqual(dr.slot_share_basis(None, 12), dr.SLOT_SHARE_EVEN_SPLIT)
        self.assertEqual(dr.slot_share_basis({}, 12), dr.SLOT_SHARE_EVEN_SPLIT)
        self.assertEqual(dr.slot_share_basis({"FLEX": {"WR": 12}}, None), dr.SLOT_SHARE_EVEN_SPLIT)

    def test_the_basis_agrees_with_what_starter_slot_counts_actually_did(self):
        # One home for the condition (#186): a second statement of it is how a vocabulary drifts
        # toward the stronger claim. This proves the two cannot disagree.
        for occupancy, teams in ((None, 12), ({}, 12), ({"FLEX": {"WR": 12}}, 12),
                                 ({"FLEX": {"WR": 12}}, None), ({"FLEX": {"WR": 12}}, 0)):
            measured = dr.starter_slot_counts(["FLEX"], occupancy, teams)
            even = dr.starter_slot_counts(["FLEX"])
            basis = dr.slot_share_basis(occupancy, teams)
            if basis == dr.SLOT_SHARE_EVEN_SPLIT:
                self.assertEqual(measured, even, msg=f"{occupancy!r}/{teams!r}")
            else:
                self.assertNotEqual(measured, even, msg=f"{occupancy!r}/{teams!r}")

    def test_every_basis_token_has_words_a_person_reads(self):
        for token in (dr.SLOT_SHARE_FIELDED, dr.SLOT_SHARE_EVEN_SPLIT):
            self.assertIn(token, dr.SLOT_SHARE_LABELS)
            self.assertTrue(dr.SLOT_SHARE_LABELS[token].strip())


class DemandReadsTheMeasuredShareTests(unittest.TestCase):
    def test_remaining_starter_demand_carries_the_occupancy_through(self):
        # The whole point of the change: the demand that sets every replacement RANK moves.
        rpos = ["WR", "FLEX"]
        even = dr.remaining_starter_demand(rpos, 12, [], {})
        measured = dr.remaining_starter_demand(rpos, 12, [], {}, {"FLEX": {"WR": 12}})
        self.assertAlmostEqual(even["TE"], 4.0)
        self.assertEqual(measured["TE"], 0.0)
        self.assertAlmostEqual(measured["WR"], 24.0)

    def test_replacement_levels_default_demand_reads_it_too(self):
        import pandas as pd
        pool = pd.DataFrame([{"player_id": f"w{i}", "position": "WR", "v": 100.0 - i}
                             for i in range(40)])
        rpos = ["WR", "FLEX"]
        even = dr.replacement_levels(pool, "v", rpos, 12)
        measured = dr.replacement_levels(pool, "v", rpos, 12, flex_occupancy={"FLEX": {"WR": 12}})
        # even split: 12 x (1 + 1/3) = 16 -> WR16; measured: 12 x 2 = 24 -> WR24.
        self.assertAlmostEqual(even["WR"], 100.0 - 15)
        self.assertAlmostEqual(measured["WR"], 100.0 - 23)

    def test_a_supplied_remaining_demand_is_not_overridden_by_an_occupancy(self):
        # The caller has already applied the share; applying it again here would be two sources
        # of one truth, and the second would win silently.
        import pandas as pd
        pool = pd.DataFrame([{"player_id": f"w{i}", "position": "WR", "v": 100.0 - i}
                             for i in range(40)])
        given = {"WR": 5.0}
        with_occ = dr.replacement_levels(pool, "v", ["WR", "FLEX"], 12, given,
                                         flex_occupancy={"FLEX": {"WR": 12}})
        self.assertAlmostEqual(with_occ["WR"], 100.0 - 4)


class TheMeasurementIsStrandedOnPurposeTests(unittest.TestCase):
    """MEASURED, NOT WIRED (#50), the standing #84 gives marginal_lineup_value.

    Two things have to stay true at once and they pull in opposite directions, which is why both
    are pinned here. The board must be byte-identical to the even split, so nothing ships that
    failed its gates. And the wiring must be LIVE -- reachable, and able to change the answer --
    so this is stranded code rather than dead code, and so the ablation that judged it is
    measuring the thing it claims to.
    """

    def test_the_seam_returns_nothing_so_every_board_keeps_the_even_split(self):
        self.assertIsNone(dr.board_flex_share({"w1": 1.0}, _db([("w1", "WR")]), ["WR", "FLEX"], 1))

    def test_the_board_asks_the_seam_and_not_the_measurement_directly(self):
        """The ablation patches ONE function. If compute_draft_board called
        fielded_flex_occupancy itself, patching the seam would silently do nothing and the
        FIELDED arm would be a second copy of the EVEN arm -- a probe that measures nothing while
        looking like it measures something, which is this repository's most expensive failure
        mode."""
        import ast
        import inspect
        for func in (dr.compute_draft_board, dr.predraft_replacement_anchor):
            tree = ast.parse(inspect.getsource(func).lstrip())
            called = {n.func.id for n in ast.walk(tree)
                      if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
            self.assertIn("board_flex_share", called, msg=func.__name__)
            self.assertNotIn("fielded_flex_occupancy", called, msg=func.__name__)

    def test_patching_the_seam_actually_moves_the_demand(self):
        """Stranded, not dead. Swap the seam for the measurement and the starter demand that sets
        every replacement rank has to change -- otherwise the whole ablation was vacuous."""
        db = _db([("w1", "WR"), ("w2", "WR"), ("t1", "TE")])
        points = {"w1": 300.0, "w2": 280.0, "t1": 100.0}
        rpos = ["WR", "FLEX"]
        even = dr.remaining_starter_demand(
            rpos, 1, [], db, dr.board_flex_share(points, db, rpos, 1))
        with mock.patch.object(dr, "board_flex_share", dr.fielded_flex_occupancy):
            measured = dr.remaining_starter_demand(
                rpos, 1, [], db, dr.board_flex_share(points, db, rpos, 1))
        self.assertAlmostEqual(even["TE"], 1.0 / 3)
        self.assertEqual(measured["TE"], 0.0)


# ---------------------------------------------------------------------------------------
# MUTATION RESULTS -- recorded, including survivors.
# ---------------------------------------------------------------------------------------
# Filled in by the mutation pass; see evidence/roster_shape/flex_share/mutations.md.
