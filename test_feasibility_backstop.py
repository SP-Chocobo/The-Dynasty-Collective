"""#154 tier 3: the arithmetic backstop that keeps a roster fieldable.

Found by #150's battery: 13 rosters across 32 formats finished unable to fill a starting slot,
every one a positional monoculture -- nine RBs and no TE, ten WRs and one RB, seven TEs and no
QB. need_bonus could not prevent it because it reads roster STATE only, so a roster with zero
TEs applied the same 4.72 nudge in round 1 and in round 15 with one pick left.

WHAT IS BEING TESTED HERE IS MOSTLY THAT IT STAYS OUT OF THE WAY. A backstop that fires early
is not a backstop, it is a positional preference with a safety-flavoured name -- and this
repository's whole constants contract (#56) exists because that substitution keeps happening.
So the no-op cases outnumber the binding ones on purpose, and the binding condition is
arithmetic that invents no number: picks left, versus named slots this roster cannot fill.
"""

import unittest

import pandas as pd

import draft_room as dr

#: One named slot per position plus a bench: the simplest league where "did it fill its
#: starters" has an answer this file did not invent.
ROSTER = ["QB", "RB", "WR", "TE", "BN", "BN"]
PLAYERS = {
    "qb1": {"position": "QB"}, "rb1": {"position": "RB"}, "rb2": {"position": "RB"},
    "wr1": {"position": "WR"}, "te1": {"position": "TE"}, "wr2": {"position": "WR"},
}
BOARD = pd.DataFrame({"position": ["RB", "TE", "WR", "QB"],
                      "final_score": [40.0, 4.0, 30.0, 20.0]})


def _picks(*player_ids, roster_id="1"):
    return [{"roster_id": roster_id, "player_id": pid} for pid in player_ids]


class ItStaysOutOfTheWayTests(unittest.TestCase):
    def test_an_empty_roster_is_untouched(self):
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, [], PLAYERS, "1", ROSTER)))

    def test_it_does_not_bind_while_picks_outnumber_holes(self):
        """Four holes, six picks: there is still room to take value now and fill later, which
        is the entire reason this is a backstop and not a preference."""
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, _picks("rb1"), PLAYERS, "1", ROSTER)))

    def test_a_roster_with_every_named_slot_filled_is_untouched(self):
        picks = _picks("qb1", "rb1", "wr1", "te1", "rb2")
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", ROSTER)))

    def test_no_roster_context_means_no_opinion(self):
        """Opponent boards and the pre-draft reference board are built with my_roster_id None.
        A backstop that fired there would reorder a board that belongs to nobody."""
        picks = _picks("qb1", "rb1", "wr1", "rb2", "wr2")
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, None, ROSTER)))

    def test_another_teams_picks_do_not_count_as_mine(self):
        """The hole is MINE or it is nobody's -- reading the whole draft here would bind on a
        roster that is perfectly healthy."""
        theirs = _picks("qb1", "rb1", "wr1", "rb2", "wr2", roster_id="7")
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, theirs, PLAYERS, "1", ROSTER)))

    def test_an_empty_board_is_handled(self):
        empty = pd.DataFrame({"position": [], "final_score": []})
        self.assertEqual([], list(dr.feasibility_first(empty, [], PLAYERS, "1", ROSTER)))


class ItBindsWhenThePicksRunOutTests(unittest.TestCase):
    def test_one_pick_left_and_one_hole_promotes_only_that_position(self):
        """The exact state the battery caught: a full roster, one pick to come, and a named slot
        nothing on the roster can fill. TE is worth 4.0 against an RB worth 40.0 -- and the RB
        is the wrong pick, because the alternative is a lineup that cannot be fielded."""
        picks = _picks("qb1", "rb1", "wr1", "rb2", "wr2")
        self.assertEqual([1, 0, 1, 1],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", ROSTER)))

    def test_two_holes_and_two_picks_promotes_both(self):
        """Four picks used on RB/WR, so QB and TE are both unfilled with two picks left."""
        picks = _picks("rb1", "rb2", "wr1", "wr2")
        promoted = list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", ROSTER))
        self.assertEqual([1, 0, 1, 0], promoted, "expected TE and QB promoted, RB/WR not")

    def test_it_still_binds_when_already_short_more_holes_than_picks(self):
        """Past the point of rescue, it must still prefer the fillable positions rather than
        giving up and reverting to pure value."""
        roster = ["QB", "RB", "WR", "TE", "BN"]
        picks = _picks("rb1", "rb2", "wr1", "wr2")
        self.assertEqual([1, 0, 1, 0],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", roster)))


class ItCountsNamedSlotsOnlyTests(unittest.TestCase):
    def test_a_flex_slot_is_not_a_hole(self):
        """A FLEX is fillable from several positions, so it is not at risk the way a named slot
        is. Counting it would let this bind on a roster in no danger -- turning the backstop
        into the preference it must never become."""
        roster = ["QB", "RB", "FLEX", "BN"]
        picks = _picks("qb1", "rb1")
        self.assertEqual([1, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", roster)))

    def test_a_second_named_slot_at_one_position_is_two_holes(self):
        roster = ["RB", "RB", "BN"]
        picks = _picks("wr1")
        self.assertEqual([0, 1, 1, 1],
                         list(dr.feasibility_first(BOARD, picks, PLAYERS, "1", roster)))


class TheOrderingConsequenceTests(unittest.TestCase):
    """The key is only useful if sorting on it actually moves the pick."""

    def test_sorting_on_it_promotes_the_fillable_candidate_over_a_better_one(self):
        board = BOARD.copy()
        picks = _picks("qb1", "rb1", "wr1", "rb2", "wr2")
        board["_feasible"] = dr.feasibility_first(board, picks, PLAYERS, "1", ROSTER)
        ordered = board.sort_values(["_feasible", "final_score"], ascending=[True, False],
                                    kind="stable")
        self.assertEqual("TE", ordered.iloc[0]["position"])
        # And value still orders everything below the promoted row.
        self.assertEqual(["RB", "WR", "QB"], list(ordered["position"])[1:])

    def test_the_ordering_is_unchanged_when_it_does_not_bind(self):
        board = BOARD.copy()
        board["_feasible"] = dr.feasibility_first(board, [], PLAYERS, "1", ROSTER)
        ordered = board.sort_values(["_feasible", "final_score"], ascending=[True, False],
                                    kind="stable")
        by_value = BOARD.sort_values("final_score", ascending=False, kind="stable")
        self.assertEqual(list(by_value["position"]), list(ordered["position"]))


if __name__ == "__main__":
    unittest.main()
