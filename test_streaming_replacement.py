"""`#30` in production: the streaming replacement level, and the floor it puts under a position.

The experiment that established this is `evidence/kdst_streaming/`. What these tests pin is the
SHIPPED path — that the derivation is the one that was measured, that it reaches the board only
when a caller supplies weekly projections, that it can only ever raise a level, and that with no
weekly projections nothing moves at all.

Synthetic and fast. Two weeks, four defenses, hand-arithmetic totals.
"""

from __future__ import annotations

import unittest

import pandas as pd

import draft_room as dr

SCORING = {"pts_allow_0": 10.0, "sack": 1.0}

#: Four defenses. d1/d2 are the two the league's demand removes; d3/d4 are the wire.
PLAYERS = {f"d{i}": {"position": "DEF", "fantasy_positions": ["DEF"]} for i in range(1, 5)}

#: Week 1 the better wire defense is d3 (2 sacks); week 2 it is d4 (5 sacks). A streamer takes
#: the max EACH week, so his season is 2 + 5 = 7 -- strictly more than either one held all year
#: (d3: 2 + 1 = 3, d4: 1 + 5 = 6). That gap is the whole of #30.
WEEKLY = {
    "1": {"d1": {"sack": 9.0}, "d2": {"sack": 8.0}, "d3": {"sack": 2.0}, "d4": {"sack": 1.0}},
    "2": {"d1": {"sack": 9.0}, "d2": {"sack": 8.0}, "d3": {"sack": 1.0}, "d4": {"sack": 5.0}},
}

#: One DEF slot, two teams -> demand 2, so d1 and d2 are drafted and d3/d4 are the wire.
ROSTER_POSITIONS = ["QB", "DEF"]


class TheDerivationTests(unittest.TestCase):

    def test_the_streamer_takes_each_week_s_best_wire_player(self):
        got = dr.streaming_replacement_levels(WEEKLY, SCORING, PLAYERS, ("DEF",),
                                              ROSTER_POSITIONS, 2)
        self.assertEqual({"DEF": 7.0}, got)

    def test_that_beats_holding_either_wire_player_all_season(self):
        """NON-VACUITY. If the weekly max equalled the best season total, this whole idea would
        be measuring nothing, and the test above would pass on an accident of the fixture."""
        got = dr.streaming_replacement_levels(WEEKLY, SCORING, PLAYERS, ("DEF",),
                                              ROSTER_POSITIONS, 2)
        held_best = max(
            sum(dr.pu.score_projection(w.get(pid) or {}, SCORING) for w in WEEKLY.values())
            for pid in ("d3", "d4"))
        self.assertEqual(6.0, held_best)
        self.assertGreater(got["DEF"], held_best)

    def test_no_weekly_projections_means_no_opinion(self):
        self.assertEqual({}, dr.streaming_replacement_levels({}, SCORING, PLAYERS, ("DEF",),
                                                             ROSTER_POSITIONS, 2))

    def test_a_position_with_no_wire_left_is_omitted_not_zeroed(self):
        """Absence travels (#187). Two teams, two defenses -- demand consumes the whole pool."""
        two = {k: v for k, v in PLAYERS.items() if k in ("d1", "d2")}
        weekly = {w: {k: v for k, v in lines.items() if k in two}
                  for w, lines in WEEKLY.items()}
        got = dr.streaming_replacement_levels(weekly, SCORING, two, ("DEF",),
                                              ROSTER_POSITIONS, 2)
        self.assertNotIn("DEF", got)

    def test_a_week_that_did_not_answer_contributes_nothing_rather_than_zero(self):
        """A missing week must not drag the level down -- that would understate the wire by
        exactly that week, the same defect _sum_weeks refuses for a season total."""
        got = dr.streaming_replacement_levels({"1": WEEKLY["1"]}, SCORING, PLAYERS, ("DEF",),
                                              ROSTER_POSITIONS, 2)
        self.assertEqual({"DEF": 2.0}, got)


class TheFloorIsRaiseOnlyTests(unittest.TestCase):

    def _pool(self):
        return pd.DataFrame([
            {"player_id": "d1", "position": "DEF", "_points": 100.0},
            {"player_id": "d2", "position": "DEF", "_points": 80.0},
            {"player_id": "d3", "position": "DEF", "_points": 60.0},
        ])

    def test_a_higher_streaming_level_replaces_the_rank_based_one(self):
        base = dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2)
        raised = dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2,
                                       streaming_floors={"DEF": 95.0})
        self.assertLess(base["DEF"], 95.0)
        self.assertEqual(95.0, raised["DEF"])

    def test_a_lower_streaming_level_changes_nothing(self):
        """It can never make a position look SCARCER than the draft already says it is."""
        base = dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2)
        lowered = dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2,
                                        streaming_floors={"DEF": 1.0})
        self.assertEqual(base, lowered)

    def test_a_position_the_rank_math_DECLINED_stays_declined(self):
        """"No starter-demand replacement exists here" is a different fact from "the wire is
        worth this much". Filling one with the other would invent a domain just refused."""
        got = dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2,
                                    streaming_floors={"K": 500.0})
        self.assertNotIn("K", got)

    def test_none_is_the_previous_behaviour_exactly(self):
        self.assertEqual(dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2),
                         dr.replacement_levels(self._pool(), "_points", ROSTER_POSITIONS, 2,
                                               streaming_floors=None))


class TheFloorReachesTheANCHOR_PathTooTests(unittest.TestCase):
    """The gap this nearly shipped with, and the path where the floor matters MOST.

    `predraft_replacement_anchor` prices a position whose live starter demand is EXHAUSTED --
    and its own docstring says which positions those are: "Kickers and defenses are drafted
    last, so they are the last positions still carrying demand." So it is precisely in the late
    rounds, the ones `#30` exists for, that K and DEF are priced from the anchor rather than the
    live level. A floor wired only into the live call site would be silently dropped there.

    It was nearly wired that way. The experiment that established `#30` monkey-patched
    `replacement_levels` GLOBALLY, so it reached both paths; the first production wiring reached
    one. That is the class of defect where a shipped fix is not the fix that was measured.

    Asked of the CODE (`#200`), not of a run, so it cannot pass by the anchor never being built.
    """

    def _anchor_call(self):
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(dr.predraft_replacement_anchor))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "replacement_levels"):
                return node
        return None

    def test_the_anchor_forwards_the_streaming_floor(self):
        call = self._anchor_call()
        self.assertIsNotNone(call, "predraft_replacement_anchor no longer calls "
                                   "replacement_levels -- re-derive where its level comes from")
        self.assertIn("streaming_floors", [kw.arg for kw in call.keywords],
                      "the anchor drops the streaming floor, so K and DEF revert to the "
                      "un-floored level in exactly the rounds #30 exists for")

    def test_the_anchor_cache_key_covers_it(self):
        """Two boards differing only in the floor would otherwise collide on one cached anchor
        -- the SUPER_FLEX_QB_SHARE failure that key's own docstring records."""
        import inspect
        source = inspect.getsource(dr.anchor_cache_key)
        self.assertIn("streaming_floors", source)

    def test_the_key_actually_changes_when_the_floor_does(self):
        """Not just present in the source: it has to move the fingerprint."""
        import data_merger as dm
        merger = dm.DataMerger()
        args = (merger, {}, {"QB", "DEF"}, ["QB", "DEF"], 12, "_points", None, {}, "all", None)
        bare = dr.anchor_cache_key(*args)
        floored = dr.anchor_cache_key(*args, streaming_floors={"DEF": 146.05})
        self.assertNotEqual(bare, floored)

    def test_the_trade_value_branch_does_NOT_get_it(self):
        """A streaming baseline is a season POINT total; the trade_value branch prices on a
        vendor composite where a points figure means nothing -- the same reasoning that keeps
        startable_floors off it."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(dr.compute_draft_board))
        anchors = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                   and n.func.id == "_anchor"]
        self.assertTrue(anchors, "_anchor is no longer called -- re-derive this test")
        for call in anchors:
            first = call.args[0]
            if isinstance(first, ast.Constant) and first.value == "trade_value":
                self.assertLess(len(call.args), 3,
                                "the trade_value anchor was handed a streaming floor")


class AnEmptySlotListMustNotProduceAPlausibleLevelTests(unittest.TestCase):
    """The bug that invalidated the first 2023 holdout, pinned so it cannot recur silently.

    `demand` is `max(1, round(teams * starters[position]))`. With no slot list, starter counts
    are all zero, demand falls to the floor of 1, and the "wire" becomes everyone outside the
    top ONE rather than outside the top (teams x slots). The level then comes out INFLATED and
    entirely plausible -- 2023 read DEF 172.91 instead of 158.00 -- which is why this needs a
    test rather than a comment.

    The `max(1, ...)` floor is right for a position with a fractional slot share and must stay.
    What must not happen is a caller reaching it by passing nothing.
    """

    def test_an_empty_slot_list_gives_a_DIFFERENT_and_higher_level(self):
        with_slots = dr.streaming_replacement_levels(WEEKLY, SCORING, PLAYERS, ("DEF",),
                                                     ROSTER_POSITIONS, 2)
        without = dr.streaming_replacement_levels(WEEKLY, SCORING, PLAYERS, ("DEF",), [], 2)
        self.assertNotEqual(with_slots, without)
        self.assertGreater(without["DEF"], with_slots["DEF"],
                           "an empty slot list no longer inflates the level -- if the demand "
                           "floor changed, re-derive this test rather than deleting it")

    def test_the_experiment_wrapper_requires_the_slot_list(self):
        """No default, so a caller that has no slot list cannot silently get a plausible level.
        Asked of the SIGNATURE (#200), not of a run."""
        import inspect
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path("evidence/kdst_streaming").resolve()))
        import streaming_arm_experiment as sae
        params = inspect.signature(sae.streaming_levels).parameters
        self.assertIn("roster_positions", params)
        self.assertIs(inspect.Parameter.empty, params["roster_positions"].default,
                      "roster_positions has a default again -- that is how the holdout came to "
                      "be measured on an inflated level")

    def test_the_experiment_module_carries_no_slot_list_global(self):
        """The mechanism was a module global that only main() filled, read by a caller that
        never goes through main()."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path("evidence/kdst_streaming").resolve()))
        import streaming_arm_experiment as sae
        self.assertFalse(hasattr(sae, "ROSTER_POSITIONS"))


class TheScopeIsNamedAndArguableTests(unittest.TestCase):
    """`#184`: which positions are streamed is a DECISION with evidence, not a derived set. It
    must stay visible, and the experiment must not carry a second copy of it."""

    def test_k_and_def_are_the_scope(self):
        self.assertEqual(("K", "DEF"), dr.STREAMABLE_POSITIONS)

    def test_rb_and_wr_are_deliberately_out(self):
        """Measured, not assumed: the weekly-max premium came out LARGER for RB (+98) than for
        DEF (+31), which would push K/DST earlier -- the opposite of the defect."""
        for position in ("RB", "WR", "TE", "QB"):
            self.assertNotIn(position, dr.STREAMABLE_POSITIONS)

    def test_the_scope_and_the_falsification_are_both_written_down(self):
        import inspect
        source = inspect.getsource(dr)
        marker = source[source.index("STREAMABLE_POSITIONS = ") - 2000:
                        source.index("STREAMABLE_POSITIONS = ")]
        self.assertIn("FALSIFIED", marker,
                      "the measurement that keeps RB/WR out of the scope is no longer recorded "
                      "beside the scope -- restore it before anyone widens this set")


if __name__ == "__main__":
    unittest.main()
