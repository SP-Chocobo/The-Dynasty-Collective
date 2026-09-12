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



class TheDraftIsNotAsLongAsTheRosterTests(unittest.TestCase):
    """#161. Every test in this module -- and every one of the 5,244 picks in #150's battery --
    was written with `rounds == len(roster_positions)`, which is the exact assumption the
    backstop's arithmetic makes. A harness that fixes a variable cannot test a defect in that
    variable, so the defect was structurally invisible to its own final gate.

    Sleeper carries `settings.rounds` separately from roster size, and benches are routinely
    filled from waivers rather than drafted. On the repo's one real league (33 roster_positions,
    29 draftable) the old arithmetic made the backstop unable to bind at ANY point of the draft.
    """

    def _fixture(self, made):
        rp = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"] + ["BN"] * 7   # 14 slots
        players_db = {f"p{i}": {"player_id": f"p{i}", "position": pos, "full_name": f"P{i}"}
                      for i, pos in enumerate(["QB", "RB", "RB", "WR", "WR", "WR",
                                               "RB", "QB", "WR"])}
        picks = [{"pick_no": i + 1, "round": i + 1, "roster_id": "3", "player_id": f"p{i}"}
                 for i in range(made)]
        scored = pd.DataFrame([{"player_id": "te1", "position": "TE"},
                               {"player_id": "wr9", "position": "WR"}])
        return scored, picks, players_db, rp

    def test_a_ten_round_draft_of_a_fourteen_slot_roster_binds_on_the_last_pick(self):
        # 9 picks made, no TE, ONE pick left. The roster cannot finish legal unless the last
        # pick is a TE, so the backstop must promote it.
        scored, picks, players_db, rp = self._fixture(made=9)
        out = dr.feasibility_first(scored, picks, players_db, "3", rp, draft_rounds=10)
        self.assertEqual(list(out), [0, 1], "the required TE must be promoted")

    def test_the_same_state_without_the_round_count_cannot_bind(self):
        """The defect, pinned. Absent draft_rounds the fallback assumes rounds == slots and
        computes 5 picks left instead of 1, so it does not bind and the roster finishes
        illegal. Kept as a characterization of the FALLBACK, not a blessing of it: callers that
        know the round count must pass it."""
        scored, picks, players_db, rp = self._fixture(made=9)
        out = dr.feasibility_first(scored, picks, players_db, "3", rp)
        self.assertEqual(list(out), [1, 1])

    def test_the_fallback_is_exactly_the_old_behaviour(self):
        # Non-regression: where rounds is unknown nothing changes, so this repair cannot have
        # altered any board the battery already measured.
        scored, picks, players_db, rp = self._fixture(made=9)
        self.assertEqual(list(dr.feasibility_first(scored, picks, players_db, "3", rp)),
                         list(dr.feasibility_first(scored, picks, players_db, "3", rp,
                                                   draft_rounds=len(rp))))

    def test_a_draft_longer_than_the_roster_does_not_bind_early(self):
        # The other direction: more rounds than slots must not make the backstop fire sooner.
        scored, picks, players_db, rp = self._fixture(made=9)
        out = dr.feasibility_first(scored, picks, players_db, "3", rp, draft_rounds=20)
        self.assertEqual(list(out), [1, 1])


class TheFlexHoleTests(unittest.TestCase):
    """#247. This is the case the backstop could not see, and the reason it could not.

    It counted DEDICATED slots only, on the premise that a flex slot is fillable from several
    positions and so is never the one at risk. The 2026-09-12 battery reached the exception
    twice in 5,340 picks: a full roster, every NAMED slot filled, and an empty FLEX -- because
    the roster owned no spare of ANY flex-eligible position. One chair had drafted eight
    quarterbacks in a one-QB league.
    """

    #: A one-QB league with a flex. Deliberately the shape the failures had.
    ROSTER = ["QB", "RB", "WR", "TE", "FLEX", "BN"]
    PLAYERS = {
        "qb1": {"position": "QB"}, "qb2": {"position": "QB"}, "qb3": {"position": "QB"},
        "rb1": {"position": "RB"}, "wr1": {"position": "WR"}, "te1": {"position": "TE"},
    }
    BOARD = pd.DataFrame({"position": ["QB", "RB"], "final_score": [99.0, 1.0]})

    def test_a_flex_hole_binds_when_no_eligible_body_is_spare(self):
        """Every named slot filled, one pick left, and the FLEX unfillable from what is owned.
        Before #247 this returned all 1s -- a no-op -- and the roster finished unfieldable."""
        picks = _picks("qb1", "rb1", "wr1", "te1", "qb2")      # 5 made of 6
        out = dr.feasibility_first(self.BOARD, picks, self.PLAYERS, "1", self.ROSTER,
                                   draft_rounds=6)
        # The RB can fill the flex; a third QB cannot.
        self.assertEqual([1, 0], list(out))

    def test_a_spare_flex_body_means_no_hole_and_no_bind(self):
        """Non-vacuity for the test above. Same slots, same count of picks made -- the only
        difference is that one of them is flex-eligible, so the lineup solves and this must be
        a no-op. Without this, the test above would also pass if the function simply always
        bound once the roster was nearly full."""
        picks = _picks("qb1", "rb1", "wr1", "te1", "rb2")      # rb2 fills the FLEX
        players = dict(self.PLAYERS, rb2={"position": "RB"})
        out = dr.feasibility_first(self.BOARD, picks, players, "1", self.ROSTER,
                                   draft_rounds=6)
        self.assertEqual([1, 1], list(out))

    def test_it_does_not_bind_while_picks_remain_to_spare(self):
        """The backstop half: the same unfillable flex, but three picks left for one hole. A
        roster with room to take value now and fill later is not in danger, and this must stay
        out of the way -- the exact failure mode the old scope was drawn to avoid."""
        picks = _picks("qb1", "rb1", "wr1")                    # 3 made of 8
        out = dr.feasibility_first(self.BOARD, picks, self.PLAYERS, "1", self.ROSTER,
                                   draft_rounds=8)
        self.assertEqual([1, 1], list(out))

    def test_a_flex_chain_is_solved_not_counted(self):
        """Counting positions gets this wrong where the solver does not: the spare RB fills the
        FLEX and frees nothing, but a naive per-position tally would see two RBs against one RB
        slot and report a hole that does not exist."""
        picks = _picks("qb1", "rb1", "rb2", "wr1", "te1")
        players = dict(self.PLAYERS, rb2={"position": "RB"})
        out = dr.feasibility_first(self.BOARD, picks, players, "1", self.ROSTER,
                                   draft_rounds=6)
        self.assertEqual([1, 1], list(out))

    def test_multi_position_eligibility_is_honoured(self):
        """fantasy_positions, not position, decides what can fill a slot (#172). A player listed
        WR/RB fills the flex even though his primary position slot is already taken."""
        players = dict(self.PLAYERS,
                       hybrid={"position": "WR", "fantasy_positions": ["WR", "RB"]})
        picks = _picks("qb1", "rb1", "wr1", "te1", "hybrid")
        out = dr.feasibility_first(self.BOARD, picks, players, "1", self.ROSTER,
                                   draft_rounds=6)
        self.assertEqual([1, 1], list(out))


if __name__ == "__main__":
    unittest.main()
