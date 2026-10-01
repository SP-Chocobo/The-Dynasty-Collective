"""#35: no position's replacement level may exceed the best player actually left at it.

The correction, and why it lives on the ANCHOR rather than on the slot alternative, is in
`draft_room.cap_levels_at_best_remaining`. These pin the three things that make it safe:

  * it only ever LOWERS a level, and only where the level names a price the pool no longer offers;
  * it is EXEMPT from #30's streaming floor, which is an ASSIGNED value rather than a claim about
    any player -- capping it reverts #30, measured at 53-54 points a seat;
  * it needs no exemption for `startable_floors`, because THAT branch returns a remaining player's
    own points, so the cap is a no-op there by construction. The property test below is what turns
    "by construction" into something a future edit cannot quietly break.
"""

import unittest

import numpy as np
import pandas as pd

import data_merger as dm
import draft_room as dr
import lineup_optimizer as lo

UNPRICED_ID = "zzz-unpriced"


def _pool(rows):
    """A priced-pool frame shaped the way `cap_levels_at_best_remaining` reads it."""
    return pd.DataFrame([{"position": p, "_points": v} for p, v in rows])


class TheCapOnlyEverLowersAndOnlyWhereItShouldTests(unittest.TestCase):
    def test_a_level_above_the_best_remaining_is_pulled_down_to_him(self):
        """The measured round-14 case: WR's level was the stale pre-draft anchor at 216.25 while
        the best receiver left projected 173.00."""
        levels = {"WR": 216.25}
        capped = dr.cap_levels_at_best_remaining(levels, _pool([("WR", 173.0), ("WR", 160.0)]))
        self.assertEqual(capped, {"WR"})
        self.assertEqual(levels["WR"], 173.0)

    def test_a_level_at_or_below_the_best_remaining_is_untouched(self):
        levels = {"WR": 150.0, "RB": 173.0}
        capped = dr.cap_levels_at_best_remaining(levels, _pool([("WR", 173.0), ("RB", 173.0)]))
        self.assertEqual(capped, set())
        self.assertEqual(levels, {"WR": 150.0, "RB": 173.0})

    def test_it_never_RAISES_a_level(self):
        """A cap that could raise would be a different change wearing this one's name."""
        before = {"WR": 100.0, "RB": 50.0, "TE": 12.5}
        levels = dict(before)
        dr.cap_levels_at_best_remaining(levels, _pool([("WR", 300.0), ("RB", 55.0), ("TE", 9.0)]))
        for position, was in before.items():
            self.assertLessEqual(levels[position], was)

    def test_a_position_with_nothing_left_keeps_its_level(self):
        """No remaining player is not the same fact as a remaining player worth zero (#187)."""
        levels = {"WR": 216.25}
        self.assertEqual(dr.cap_levels_at_best_remaining(levels, _pool([("RB", 10.0)])), set())
        self.assertEqual(levels["WR"], 216.25)

    def test_an_absent_level_is_not_invented(self):
        levels = {"WR": None, "RB": float("nan")}
        self.assertEqual(dr.cap_levels_at_best_remaining(levels, _pool([("WR", 5.0), ("RB", 5.0)])),
                         set())
        self.assertIsNone(levels["WR"])
        self.assertTrue(pd.isna(levels["RB"]))

    def test_an_empty_pool_caps_nothing_rather_than_capping_everything(self):
        levels = {"WR": 216.25}
        self.assertEqual(dr.cap_levels_at_best_remaining(levels, _pool([])), set())
        self.assertEqual(dr.cap_levels_at_best_remaining(levels, None), set())
        self.assertEqual(levels["WR"], 216.25)


class TheStreamingFloorIsEXEMPTTests(unittest.TestCase):
    """#30's floor is the season sum of each week's best WIRE option -- larger than any one
    player's season projection ON PURPOSE. Capping it does not correct a stale anchor, it reverts
    #30: measured on the 2024 opening board, DEF 146.05 -> 121.49 and K 164.50 -> 159.88, before a
    single pick, costing 53-54 points a seat."""

    def test_a_level_that_IS_the_floor_is_left_alone(self):
        levels = {"DEF": 146.05, "K": 164.50}
        capped = dr.cap_levels_at_best_remaining(
            levels, _pool([("DEF", 121.49), ("K", 159.88)]),
            streaming_floors={"DEF": 146.05, "K": 164.50})
        self.assertEqual(capped, set(), "the cap reverted #30's floor")
        self.assertEqual(levels, {"DEF": 146.05, "K": 164.50})

    def test_the_exemption_is_NARROW_and_does_not_shelter_the_position_generally(self):
        """A streamable position whose level did NOT come from the floor is capped like any
        other. The exemption is about the LEVEL's provenance, not the position's name."""
        levels = {"DEF": 200.0}
        capped = dr.cap_levels_at_best_remaining(
            levels, _pool([("DEF", 121.49)]), streaming_floors={"DEF": 146.05})
        self.assertEqual(capped, {"DEF"})
        self.assertEqual(levels["DEF"], 121.49)

    def test_no_floors_at_all_is_not_read_as_every_level_being_a_floor(self):
        levels = {"DEF": 146.05}
        self.assertEqual(
            dr.cap_levels_at_best_remaining(levels, _pool([("DEF", 121.49)]), None), {"DEF"})


class TheStartableFloorBranchNeedsNoExemptionTests(unittest.TestCase):
    """THE PROPERTY THE MISSING EXEMPTION RESTS ON, pinned so a future edit to that branch fails
    here instead of silently mis-pricing.

    `replacement_levels`' startable_floors branch counts the remaining players clearing the
    threshold and returns `at_pos.iloc[rank - 1]` -- a REMAINING player's own points. So the level
    can never exceed the best remaining player at that position, and the cap is a no-op there by
    construction. My own derivation of this exemption was originally wrong: I called a startability
    threshold "not a pool reading", which is true of the THRESHOLD and false of the LEVEL.
    """

    def test_the_level_never_exceeds_the_best_remaining_player(self):
        pool = pd.DataFrame([
            {"player_id": str(i), "position": "QB", "_points": pts}
            for i, pts in enumerate([380.0, 300.0, 250.0, 210.0, 170.0, 90.0])
        ])
        roster = ["QB", "SUPER_FLEX", "BN"]
        for floor in (160.0, 200.0, 240.0, 300.0, 400.0):
            with self.subTest(floor=floor):
                levels = dr.replacement_levels(pool, "_points", roster, 2, {"QB": 1.0},
                                               startable_floors={"QB": floor})
                if "QB" not in levels:
                    continue          # declined: no level at all, so nothing to cap
                self.assertLessEqual(
                    levels["QB"], pool["_points"].max(),
                    "a startable_floor level rose above the best remaining player, so the cap's "
                    "missing exemption for this branch is no longer safe")

    def test_and_so_the_cap_is_a_no_op_on_such_a_level(self):
        pool = pd.DataFrame([{"position": "QB", "_points": p} for p in (380.0, 210.0, 90.0)])
        levels = {"QB": 210.0}
        self.assertEqual(dr.cap_levels_at_best_remaining(levels, pool), set())
        self.assertEqual(levels["QB"], 210.0)


def _fixture():
    """A small real board, the same construction test_absence_kind uses."""
    merger = dm.DataMerger()
    proj = merger.projections
    players_db, pid = {}, 0
    for pos in ("QB", "RB", "WR", "TE"):
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(20)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team")}
    league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                 dynasty=True)
    return merger, players_db, league


class OnARealDrainedBoardTests(unittest.TestCase):
    """The integration half. A board drained past its own anchors is where this fires at all."""

    @classmethod
    def setUpClass(cls):
        merger, players_db, league = _fixture()
        cls.merger, cls.players_db, cls.league = merger, players_db, league
        opening = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                                         mode="balanced")
        # DRAIN A POSITION'S DEMAND, not just the board's top. A level goes stale exactly when
        # `replacement_levels` omits the position for exhausted demand and
        # `_fill_omitted_from_anchor` installs the PRE-DRAFT anchor in its place -- a number
        # computed against the full pool, which by then names a player who is gone. Taking the
        # board's best 55 rows drains nobody's demand in a 12-team league and the cap correctly
        # did nothing; the non-vacuity test below is what caught that.
        by_pos = {}
        for r in opening:
            if r.get("projected_points") is not None:
                by_pos.setdefault(r["position"], []).append(r["player_id"])
        drafted = by_pos.get("QB", [])[:15] + by_pos.get("TE", [])[:15]
        cls.picks = [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": str(i % 12 + 1),
                      "player_id": pid} for i, pid in enumerate(drafted)]
        cls.board = dr.compute_draft_board(merger, players_db, cls.picks, my_roster_id="1",
                                           league=league, mode="balanced")

    def test_the_population_is_not_vacuous(self):
        """If nothing is capped on this board the three tests below guard nothing."""
        capped = {r["position"] for r in self.board if r.get("replacement_level_capped")}
        self.assertTrue(capped, "no position capped on a drained board -- the fixture stopped "
                                "draining, so this class has stopped guarding anything")

    def test_no_priced_level_exceeds_the_best_remaining_player_at_its_position(self):
        """The invariant the whole change exists to establish, read off the board itself:
        level = projected_points - bpa."""
        best, levels = {}, {}
        for r in self.board:
            pts, bpa = r.get("projected_points"), r.get("bpa")
            if pts is None or bpa is None:
                continue
            best[r["position"]] = max(best.get(r["position"], float("-inf")), float(pts))
            levels[r["position"]] = round(float(pts) - float(bpa), 6)
        self.assertTrue(levels, "no priced row on this board")
        for position, level in levels.items():
            with self.subTest(position):
                self.assertLessEqual(round(level, 4), round(best[position], 4))

    def test_a_capped_row_SAYS_SO_BESIDE_its_basis_rather_than_instead_of_it(self):
        """TWO FACTS, TWO FIELDS. The first version of this disclosure overwrote
        `replacement_basis` with a "best_remaining" token, and three tests in the suite caught it:
        `predraft_anchor` went UNREACHABLE on two real fixtures, because a position that gets the
        anchor is very nearly the same population whose anchor the pool has drained past. Which
        authority SELECTED the level and whether it was then CORRECTED are different facts and
        both are true of a capped anchor row."""
        capped = [r for r in self.board if r.get("replacement_level_capped")]
        self.assertTrue(capped)
        for r in capped:
            with self.subTest(r["player_id"]):
                self.assertIs(r["replacement_level_capped"], True)
                self.assertIn(r["replacement_basis"], dr.REPLACEMENT_BASIS_LABELS,
                              "the basis must still name the authority that selected the level")
        # And the flag is never absent: it is a bool the board always computes (#187's converse --
        # this is a measured fact about every row, not a quantity that can go missing).
        self.assertTrue(all(isinstance(r.get("replacement_level_capped"), bool)
                            for r in self.board))
        # NON-VACUITY in the other direction: an uncapped row must exist, or the flag says nothing.
        self.assertTrue([r for r in self.board if r.get("replacement_level_capped") is False])

    def test_the_flag_reaches_BOTH_serializations(self):
        """A companion that reaches only one board is the #174 defect."""
        self.assertIn("replacement_level_capped", dr.BALANCED_BOARD_COLUMNS)
        self.assertIn("replacement_level_capped", dr.UPSIDE_BOARD_COLUMNS)

    def test_displacement_adj_is_STILL_non_positive_for_a_single_position_row(self):
        """The registered invariant that capping the SLOT ALTERNATIVE would have inverted. Capping
        the anchor must leave it standing -- that is the entire reason this correction was put
        here instead of there."""
        offenders = [(r["player_id"], r["displacement_adj"]) for r in self.board
                     if r.get("displacement_adj") is not None
                     and not pd.isna(r["displacement_adj"])
                     and r["displacement_adj"] > 0
                     and len(lo.eligible_positions(self.players_db.get(r["player_id"]) or {})
                             if hasattr(lo, "eligible_positions") else [r["position"]]) == 1]
        self.assertEqual(offenders, [], "a single-position row was LIFTED by roster context")


if __name__ == "__main__":
    unittest.main()
