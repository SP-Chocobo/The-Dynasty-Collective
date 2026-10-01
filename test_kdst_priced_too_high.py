"""CHARACTERIZATION (#52) -- invert on repair, do not delete. K and DST price into the early rounds.

Found by the `12T_ppr_K_DEF` arm, which exists because `has_defense` was constant across every
other arm and `format_axes_exercised` said outright that "the battery's results are not evidence
about team-defense drafting". They now are, and the first thing they say is that the engine
drafts a team defense about five rounds too early.

Measured through the battery's own mechanism (simulate_full_draft, mode="auto"): first DEF taken
in round 5, first K in round 7, both with median round 10, against an owner target of the bottom
25-30% of a 16-round draft.

WHAT THIS FILE PINS IS THE MECHANISM, NOT THE DRAFT. A full draft is ~10 minutes and has no
place in the suite; one board build is seconds and carries the whole defect: `bpa` is raw VOR in
season points compared across positions with no normalisation, so a shallow pool's spread reads
as ownable as a deep pool's.

WHY IT IS CHARACTERIZED RATHER THAN FIXED. Three candidate levers were measured
(evidence/blind_pass/KDST_VALUATION.md): positional_forfeit never reaches the board;
waiting_cost points the WRONG WAY (deferring the top DEF "costs" 35.90, more than its VOR); and
every sane replacement choice sits in a six-point band that leaves VOR near 30. A discount
multiplier cannot substitute -- the factor required to reach round 13 is NEGATIVE, because
zeroing K/DEF bpa entirely still leaves them at +4.00 while round-13 skill players are at -55.73.

The real gap is that every valuation term trusts the projection and nothing measures whether a
position's projections come true. Closing it needs prior-season projections against actuals,
which is not reachable from the audit sandbox.

So: when a predictiveness term lands, these assertions fail. That failure is the point. Re-derive
them against the new behaviour and record the measurement -- do not loosen them.
"""

from __future__ import annotations

import unittest

import pandas as pd

import draft_battery as dbat
import draft_room as dr


def _board():
    import data_merger as dm, run_draft_battery as rdb
    merger = dm.DataMerger()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    scoring = rdb.scoring_settings_from_capture()
    arm = next(a for a in dbat.league_matrix(scoring) if a["label"] == "12T_ppr_K_DEF")
    merger.set_league_format(dbat.league_format_hint(arm["league"]))
    board = pd.DataFrame(dr.compute_draft_board(
        merger, players_db, [], my_roster_id=None, league=arm["league"], mode="balanced",
        sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM))
    board["rank"] = range(1, len(board) + 1)
    return board, arm


class TheArmThatFoundItIsWellFormedTests(unittest.TestCase):
    """Non-vacuity for everything below: a misconfigured arm would make the defect an artifact.
    This was a live suspicion and is checked rather than assumed."""

    def test_the_arm_exists_and_carries_both_slots(self):
        import run_draft_battery as rdb
        arm = next(a for a in dbat.league_matrix(rdb.scoring_settings_from_capture())
                   if a["label"] == "12T_ppr_K_DEF")
        self.assertIn("K", arm["league"]["roster_positions"])
        self.assertIn("DEF", arm["league"]["roster_positions"])

    def test_both_slots_generate_real_starter_demand(self):
        """The failure mode feared: slots appended after the bench being read as bench. They are
        not -- starter_slot_counts is position-keyed and order-independent."""
        import run_draft_battery as rdb
        arm = next(a for a in dbat.league_matrix(rdb.scoring_settings_from_capture())
                   if a["label"] == "12T_ppr_K_DEF")
        counts = dr.starter_slot_counts(arm["league"]["roster_positions"], None, arm["teams"])
        self.assertEqual(counts.get("K"), 1.0)
        self.assertEqual(counts.get("DEF"), 1.0)


class KAndDstPriceIntoTheEarlyRoundsTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.board, cls.arm = _board()

    def _best(self, position):
        rows = self.board[self.board["position"] == position]
        self.assertTrue(len(rows), f"no {position} on the board -- the arm changed shape")
        return rows.nsmallest(1, "rank").iloc[0]

    def test_a_team_defense_outranks_a_real_starting_receiver(self):
        """THE DEFECT, in one comparison. The Rams' bpa (30.47) exceeds Ladd McConkey's (28.02)
        because DEF1-DEF12 is 30.5 season points while that receiver is 28.0 above his own
        replacement -- even though he outproduces the defense by more than a hundred points."""
        best_def = self._best("DEF")
        board_rank = int(best_def["rank"])
        self.assertLess(board_rank, 12 * 8,
                        "a defense no longer prices inside the first eight rounds -- if a "
                        "predictiveness term landed, re-derive this file against it")

    def test_the_defect_is_the_unnormalised_cross_position_VOR(self):
        """Named precisely so a repair can be checked against the CAUSE and not the symptom:
        the defense's bpa really is larger than a mid-board skill player's."""
        best_def = self._best("DEF")
        neighbours = self.board[
            (self.board["rank"] > int(best_def["rank"]) - 4)
            & (self.board["rank"] < int(best_def["rank"]))
            & (~self.board["position"].isin(["K", "DEF"]))]
        self.assertTrue(len(neighbours), "no skill players adjacent to the top defense")
        self.assertGreater(
            float(best_def["bpa"]), float(neighbours["bpa"].min()),
            "the defense's raw VOR no longer exceeds an adjacent skill player's")
        self.assertLess(
            float(best_def["projected_points"]), float(neighbours["projected_points"].min()),
            "non-vacuity: the defense must still be producing FEWER points than the players it "
            "is outranking, or this comparison is not the defect it was written for")

    def test_waiting_cost_points_the_wrong_way(self):
        """Recorded because it is counter-intuitive and cost real time to establish. The term
        whose stated job is 'what does deferring this position cost' says deferring the top
        defense costs MORE than its VOR -- so wiring it into the score would push defenses up."""
        best_def = self._best("DEF")
        self.assertIsNotNone(best_def["waiting_cost"])
        self.assertGreater(float(best_def["waiting_cost"]), float(best_def["bpa"]))

    def test_forfeiture_cannot_be_the_lever(self):
        """The first hypothesis, and a static fact rather than a measurement: the term never
        reaches the board at all."""
        from test_source_scan import code_text
        from pathlib import Path
        self.assertNotIn("positional_forfeit", code_text(Path(dr.__file__)))


if __name__ == "__main__":
    unittest.main()
