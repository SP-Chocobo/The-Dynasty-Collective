"""The fieldability backstop: `fieldable_ceiling` + `unfieldable_last` (draft_room).

WHY IT EXISTS, in one line: graded on 2024 REALIZED outcomes the engine finished a 12-team PPR
draft with NINE DEFENSES and one receiver in a league with one DEF slot, and lost 0 of 12 seats
by a mean of 641 points. `evidence/kdst_streaming/ROOT_CAUSE.md` has the full derivation.

The properties tested here are the ones that decide whether this is admissible at all:

  - the ceiling is DERIVED from the slot list and the one bye every team has (`#56`);
  - a flex-reachable position has NO ceiling, so ordinary depth is never touched;
  - it is a BACKSTOP, not a preference -- it cannot bind on a roster that is not provably
    carrying a player it can never field (`feasibility_first`'s own admissibility test);
  - it reaches the PICK, not just the board, because `pick_synthesis._board_order` re-sorts
    every board it is handed (`#155`) and a backstop expressed only as row order is discarded.
"""

from __future__ import annotations

import unittest

import pandas as pd

import draft_room as dr
import pick_synthesis as ps

#: One dedicated DEF, one K, one QB, and a FLEX reaching RB/WR/TE -- the measured format's shape.
ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX",
                    "BN", "BN", "BN", "BN", "BN", "BN", "K", "DEF"]

PLAYERS = {
    "d1": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "d2": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "d3": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "r1": {"position": "RB", "fantasy_positions": ["RB"]},
    "r2": {"position": "RB", "fantasy_positions": ["RB"]},
    "r3": {"position": "RB", "fantasy_positions": ["RB"]},
    "r4": {"position": "RB", "fantasy_positions": ["RB"]},
    "w1": {"position": "WR", "fantasy_positions": ["WR"]},
    "dual": {"position": "DB", "fantasy_positions": ["DB", "WR"]},
}


def _picks(ids, roster_id="1"):
    return [{"player_id": pid, "roster_id": roster_id, "round": n + 1, "pick_no": n + 1}
            for n, pid in enumerate(ids)]


def _scored(positions, ids=None):
    """A board frame with the two columns the backstop reads. `ids` defaults to a player at each
    position taken from PLAYERS, so the eligibility lookup the backstop does has something real
    to find -- a frame with fabricated ids would make every demotion vacuously zero."""
    positions = list(positions)
    if ids is None:
        first_at = {}
        for pid, info in PLAYERS.items():
            first_at.setdefault(info["position"], pid)
        ids = [first_at.get(p, f"unknown-{p}") for p in positions]
    return pd.DataFrame({"position": positions, "player_id": list(ids)},
                        index=range(len(positions)))


class TheCeilingIsDerivedTests(unittest.TestCase):

    def test_a_dedicated_position_gets_its_slots_plus_the_one_bye(self):
        ceilings = dr.fieldable_ceiling(ROSTER_POSITIONS)
        self.assertEqual(2, ceilings["DEF"])
        self.assertEqual(2, ceilings["K"])
        self.assertEqual(2, ceilings["QB"])

    def test_a_flex_reachable_position_has_no_ceiling_at_all(self):
        """ABSENCE, not a large number. A spare RB fills a FLEX and frees a WR upward, so its
        useful depth is a real valuation question this function has no opinion about."""
        ceilings = dr.fieldable_ceiling(ROSTER_POSITIONS)
        for position in ("RB", "WR", "TE"):
            self.assertNotIn(position, ceilings)

    def test_two_dedicated_slots_raise_the_ceiling_by_exactly_one_each(self):
        ceilings = dr.fieldable_ceiling(["QB", "QB", "DEF"])
        self.assertEqual(3, ceilings["QB"])
        self.assertEqual(2, ceilings["DEF"])

    def test_an_empty_slot_list_yields_no_ceilings_rather_than_an_empty_opinion(self):
        self.assertEqual({}, dr.fieldable_ceiling([]))


class TheBackstopBindsOnlyWhenItIsProvableTests(unittest.TestCase):

    def test_a_third_defense_is_demoted(self):
        got = dr.unfieldable_last(_scored(["DEF", "WR", "RB"]), _picks(["d1", "d2"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([1, 0, 0], list(got))

    def test_the_bye_backup_is_NOT_demoted(self):
        """The ceiling is the largest count that is not PROVABLY wasted. One spare covers the
        one bye, so flagging it would make this a preference rather than a backstop."""
        got = dr.unfieldable_last(_scored(["DEF", "WR"]), _picks(["d1"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0], list(got))

    def test_a_fourth_running_back_is_never_demoted(self):
        """The flex exemption, end to end. This is the test that keeps it from firing on every
        sane roster in the battery."""
        got = dr.unfieldable_last(_scored(["RB", "WR"]), _picks(["r1", "r2", "r3", "r4"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0], list(got))

    def test_an_empty_roster_demotes_nobody(self):
        got = dr.unfieldable_last(_scored(["DEF", "K", "QB"]), [], PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0, 0], list(got))

    def test_another_seats_defenses_do_not_saturate_mine(self):
        """Read off MY roster only. Counting the league's would turn a backstop into a scarcity
        signal, which is replacement_levels' job and not this one's."""
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"], roster_id="7"),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0], list(got))

    def test_a_multi_eligible_player_saturates_no_dedicated_position(self):
        """#172 in the counting direction: a player who reaches a shared slot is not consuming
        a dedicated one, so he is counted at no ceilinged position."""
        got = dr.unfieldable_last(_scored(["WR"]), _picks(["dual", "dual2"]),
                                  dict(PLAYERS, dual2={"position": "DB",
                                                       "fantasy_positions": ["DB", "WR"]}),
                                  "1", ROSTER_POSITIONS)
        self.assertEqual([0], list(got))

    def test_no_roster_id_is_a_no_op(self):
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"]),
                                  PLAYERS, None, ROSTER_POSITIONS)
        self.assertEqual([0], list(got))


class ItAsksEligibilityNotThePrimaryBucketTests(unittest.TestCase):
    """#172, in the demotion direction. Reading `position` alone sinks a dual-eligible player on
    a label rather than on what he can actually fill."""

    #: Both RB and WR dedicated, no flex anywhere -- so BOTH carry a ceiling and the subset test
    #: is the only thing separating a demotion from a mistake.
    NO_FLEX = ["QB", "RB", "RB", "WR", "WR", "DEF"]

    def test_a_dual_eligible_player_survives_while_one_of_his_positions_is_open(self):
        players = dict(PLAYERS, rbwr={"position": "RB", "fantasy_positions": ["RB", "WR"]})
        # Three RBs held: RB is saturated (2 slots + bye = 3 -> held 3 >= 3). WR is not.
        got = dr.unfieldable_last(_scored(["RB"], ids=["rbwr"]),
                                  _picks(["r1", "r2", "r3"]), players, "1", self.NO_FLEX)
        self.assertEqual([0], list(got),
                         "a WR-eligible player was demoted for being labelled RB")

    def test_a_single_position_player_at_the_same_position_IS_demoted(self):
        """The control for the test above: same board, same roster, one eligibility."""
        got = dr.unfieldable_last(_scored(["RB"], ids=["r4"]),
                                  _picks(["r1", "r2", "r3"]), PLAYERS, "1", self.NO_FLEX)
        self.assertEqual([1], list(got))

    def test_a_dual_eligible_player_is_demoted_once_BOTH_are_saturated(self):
        players = dict(PLAYERS, rbwr={"position": "RB", "fantasy_positions": ["RB", "WR"]},
                       w2={"position": "WR", "fantasy_positions": ["WR"]},
                       w3={"position": "WR", "fantasy_positions": ["WR"]})
        got = dr.unfieldable_last(_scored(["RB"], ids=["rbwr"]),
                                  _picks(["r1", "r2", "r3", "w1", "w2", "w3"]),
                                  players, "1", self.NO_FLEX)
        self.assertEqual([1], list(got))

    def test_a_row_whose_eligibility_cannot_be_read_is_not_demoted(self):
        """Absence is not evidence of surplus (#187's shape, in the selection layer)."""
        got = dr.unfieldable_last(_scored(["RB"], ids=["nobody-knows-him"]),
                                  _picks(["r1", "r2", "r3"]), PLAYERS, "1", self.NO_FLEX)
        self.assertEqual([0], list(got))


class ItReachesThePickAndNotOnlyTheBoardTests(unittest.TestCase):
    """#155. `_board_order` re-sorts every board it is handed, so a backstop that lives only in
    draft_room's row order is thrown away before a pick is made. Tier 3 was measured promoting a
    QB correctly on the board while the chair still took its seventh RB, for exactly this reason.
    """

    def test_board_order_sinks_an_unfieldable_row_below_a_worse_scoring_one(self):
        unfieldable = {"player_id": "d3", "final_score": 100.0, "cannot_be_fielded": True}
        ordinary = {"player_id": "w1", "final_score": 1.0, "cannot_be_fielded": False}
        self.assertEqual(["w1", "d3"],
                         [r["player_id"] for r in sorted([unfieldable, ordinary],
                                                         key=ps._board_order)])

    def test_the_feasibility_backstop_still_outranks_it(self):
        """Order of the two backstops: filling a slot you cannot otherwise fill beats avoiding a
        spot you cannot field. A roster in BOTH states must still draft the legal lineup."""
        required = {"player_id": "a", "final_score": 1.0,
                    "fills_required_slot": True, "cannot_be_fielded": False}
        unfieldable = {"player_id": "b", "final_score": 500.0,
                       "fills_required_slot": False, "cannot_be_fielded": True}
        self.assertEqual(["a", "b"],
                         [r["player_id"] for r in sorted([unfieldable, required],
                                                         key=ps._board_order)])

    def test_a_row_without_the_flag_is_treated_as_fieldable(self):
        """Every caller that predates the flag must keep working, and absence must read as 'not
        demoted' rather than as a demotion nobody computed."""
        a = {"player_id": "a", "final_score": 5.0}
        b = {"player_id": "b", "final_score": 1.0}
        self.assertEqual(["a", "b"],
                         [r["player_id"] for r in sorted([b, a], key=ps._board_order)])

    def test_the_column_is_emitted_on_both_boards(self):
        """A companion that reaches only one serialization is the #174 defect."""
        self.assertIn("cannot_be_fielded", dr.BALANCED_BOARD_COLUMNS)
        self.assertIn("cannot_be_fielded", dr.UPSIDE_BOARD_COLUMNS)


if __name__ == "__main__":
    unittest.main()
