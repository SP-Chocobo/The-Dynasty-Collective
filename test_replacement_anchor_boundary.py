"""The pre-draft replacement anchor's own boundary -- what the board may and may not do once
a position's league-wide starter demand is exhausted.

The defect these pin down. replacement_levels is defined only while a position still has a
whole starting slot unfilled and correctly OMITS the position below that. compute_draft_board
turned that omission into final_score=None, and _board_order sorts unpriced rows last -- so a
position whose starters were all filled had EVERY remaining player fall below every priced
row. Kickers and defenses are drafted last and are therefore the last positions still carrying
demand, which made the inversion structural rather than incidental: measured on a 12-team 1QB
board at round 15, K and DEF were 100% priced (37/37 and 32/32) while QB/RB/TE/WR were 100%
unpriced (0 of 15/36/24/9), and the top five candidates were four defenses and a kicker ahead
of every remaining skill player.

Every test here is about SEMANTICS. Each one fails for a reason that can be stated in one
sentence about what the number means, and each one is written so that it CAN fail: the
control arms below are asserted to actually differ before any comparison is trusted.
"""

import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr

NUM_TEAMS = 12
ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
SUPERFLEX_POSITIONS = (
    ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"] + ["BN"] * 10
)
LEAGUE = {
    "roster_positions": ROSTER_POSITIONS, "total_rosters": NUM_TEAMS,
    "settings": {"type": 2}, "scoring_settings": {},
}
SKILL = ("QB", "RB", "WR", "TE")


def _universe(merger):
    """A players_db over the merger's whole projection set, ordered by trade_value so a
    synthetic draft consumes the best players first the way a real one does."""
    players_db, by_position, next_id = {}, {}, 0
    for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
        rows = merger.projections[merger.projections["position"] == position]
        for _, row in rows.sort_values("trade_value", ascending=False).iterrows():
            next_id += 1
            parts = str(row["name"]).split()
            players_db[str(next_id)] = {
                "first_name": parts[0] if parts else "",
                "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                "position": position, "fantasy_positions": [position], "team": row.get("team"),
            }
            by_position.setdefault(position, []).append(str(next_id))
    return players_db, by_position


def _drain(by_position, rounds_by_position, num_teams=NUM_TEAMS):
    """Every team takes the requested count at each position -- enough to run a position's
    league-wide starter demand to zero, which is the state this whole module is about."""
    picks, taken = [], {}
    for position, count in rounds_by_position.items():
        for _ in range(count):
            index = taken.get(position, 0)
            for roster_id in range(1, num_teams + 1):
                if index >= len(by_position[position]):
                    break
                picks.append({
                    "player_id": by_position[position][index], "roster_id": str(roster_id),
                    "round": len(picks) // num_teams + 1, "pick_no": len(picks) + 1,
                })
                index += 1
            taken[position] = index
    return picks


class PreDraftAnchorEquivalence(unittest.TestCase):
    """The design rests on one measured equality: the last LIVE level equals the PRE-DRAFT
    level. That is what lets the anchor be a pure function of (player universe, league)
    instead of a memo of earlier calls -- a memo would have made a board's answer depend on
    which boards were built before it, breaking replacement_levels' own stated contract that
    nothing is cached across picks."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, cls.by_position = _universe(cls.merger)

    def test_anchor_matches_the_first_live_level_for_every_position(self):
        seen = {}
        original = dr.replacement_levels

        def spy(pool, value_col, roster_positions, num_teams, remaining_demand=None,
                startable_floors=None):
            levels = original(pool, value_col, roster_positions, num_teams, remaining_demand,
                              startable_floors)
            for position, level in levels.items():
                seen.setdefault((value_col, position), level)
            return levels

        dr.replacement_levels = spy
        try:
            dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1",
                                   league=LEAGUE, mode="balanced")
        finally:
            dr.replacement_levels = original

        self.assertTrue(seen, "vacuous: no replacement level was observed at all")
        anchor = dr.predraft_replacement_anchor(
            self.merger, self.players_db, dr.league_usable_positions(ROSTER_POSITIONS),
            ROSTER_POSITIONS, NUM_TEAMS, "_points",
        )
        self.assertTrue(anchor, "vacuous: the anchor produced no levels to compare against")
        compared = 0
        for (value_col, position), live in seen.items():
            if value_col != "_points":
                continue
            self.assertIn(position, anchor)
            self.assertAlmostEqual(anchor[position], live, places=9)
            compared += 1
        self.assertGreaterEqual(compared, 4, "vacuous: too few positions actually compared")

    def test_board_is_identical_when_built_twice_in_a_row(self):
        """No call-order state anywhere in the anchor path."""
        picks = _drain(self.by_position, {"WR": 4, "RB": 3, "TE": 2, "QB": 2})
        first = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                       league=LEAGUE, mode="balanced")
        second = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                        league=LEAGUE, mode="balanced")
        self.assertTrue(first, "vacuous: empty board")
        self.assertEqual([r["player_id"] for r in first], [r["player_id"] for r in second])
        self.assertEqual([r["final_score"] for r in first], [r["final_score"] for r in second])


class ExhaustedDemandKeepsItsPrice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, cls.by_position = _universe(cls.merger)
        # Deep enough that several positions' league-wide starter demand reaches zero.
        cls.picks = _drain(cls.by_position, {"WR": 5, "RB": 4, "TE": 3, "QB": 2})
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, cls.picks, my_roster_id="1", league=LEAGUE,
            mode="balanced",
        )

    def _control_board(self):
        """The same board with the anchor disabled -- i.e. the behaviour before this repair.
        Used as a control, and asserted to actually differ so nothing here passes vacuously."""
        original = dr.predraft_replacement_anchor
        dr.predraft_replacement_anchor = lambda *a, **k: {}
        try:
            return dr.compute_draft_board(
                self.merger, self.players_db, self.picks, my_roster_id="1", league=LEAGUE,
                mode="balanced",
            )
        finally:
            dr.predraft_replacement_anchor = original

    def test_the_control_really_does_lose_prices(self):
        """Guards every comparison below: if the control priced everything too, the repair
        would be untested and the rest of this class would prove nothing."""
        control = {r["player_id"]: r["final_score"] for r in self._control_board()}
        unpriced = [pid for pid, score in control.items() if score is None]
        self.assertGreater(len(unpriced), 0,
                           "vacuous: nothing was unpriced without the anchor, so this draft "
                           "state does not exercise the defect at all")

    def test_anchor_only_adds_prices_and_never_changes_one(self):
        control = {r["player_id"]: r["final_score"] for r in self._control_board()}
        after = {r["player_id"]: r["final_score"] for r in self.board}
        for player_id, before in control.items():
            if before is None:
                continue
            self.assertIsNotNone(after.get(player_id),
                                 f"{player_id} lost a price it already had")
            self.assertAlmostEqual(after[player_id], before, places=9,
                                   msg=f"{player_id}'s existing price changed")

    def test_every_row_records_which_anchor_its_price_rests_on(self):
        self.assertTrue(self.board)
        bases = {r.get("replacement_basis") for r in self.board}
        self.assertTrue(bases <= {"live_starter_demand", "predraft_anchor"}, bases)
        self.assertIn("predraft_anchor", bases,
                      "vacuous: no row in this state rests on the pre-draft anchor")

    def test_a_skill_position_is_no_longer_wholly_unpriced(self):
        by_position = {}
        for row in self.board:
            priced, unpriced = by_position.setdefault(row["position"], [0, 0])
            by_position[row["position"]] = (
                [priced + 1, unpriced] if row["final_score"] is not None
                else [priced, unpriced + 1]
            )
        exercised = 0
        for position in SKILL:
            if position not in by_position:
                continue
            priced, _ = by_position[position]
            self.assertGreater(priced, 0,
                               f"every remaining {position} is unpriced, so all of them sort "
                               f"below every kicker -- the inversion this repair exists for")
            exercised += 1
        self.assertGreaterEqual(exercised, 3, "vacuous: too few skill positions on the board")


class StartableFloorIsNeverRevived(unittest.TestCase):
    """The startable_floors branch declines for a DIFFERENT reason -- no remaining player
    clears the startability threshold -- and a stale anchor must not be used to assert that a
    startable replacement exists where the measurement says none does. Kept separate from the
    demand case on purpose; see #66 for the two-clamp history."""

    def test_fill_skips_a_position_the_floor_branch_declined(self):
        levels = {"RB": 100.0}
        filled = dr._fill_omitted_from_anchor(
            levels, {"RB", "QB"}, {"QB": 250.0}, {"QB": 999.0, "RB": 111.0},
        )
        self.assertEqual(filled, set(), "a floor-declined position was revived")
        self.assertNotIn("QB", levels)

    def test_fill_takes_a_position_whose_demand_merely_ran_out(self):
        levels = {"RB": 100.0}
        filled = dr._fill_omitted_from_anchor(levels, {"RB", "QB"}, None, {"QB": 42.0})
        self.assertEqual(filled, {"QB"})
        self.assertEqual(levels["QB"], 42.0)

    def test_fill_cannot_invent_a_level_the_anchor_does_not_have(self):
        levels = {}
        filled = dr._fill_omitted_from_anchor(levels, {"RB"}, None, {})
        self.assertEqual(filled, set())
        self.assertEqual(levels, {})

    def test_fill_never_overwrites_a_live_level(self):
        levels = {"RB": 100.0}
        dr._fill_omitted_from_anchor(levels, {"RB"}, None, {"RB": 999.0})
        self.assertEqual(levels["RB"], 100.0)


if __name__ == "__main__":
    unittest.main()
