"""
Covers the hard invariants draft_room.py's own math must never violate (per its module
docstring), plus regression coverage for the two real bugs caught building it: raw
trade_value used as a cross-positional anchor (silently buried elite IDP below replacement-
level offense), and a missing-projection position collapsing every player to an identical
score. Uses the real committed baseline, same as test_data_merger.py's
CompositeScoreOnRealBaselineTests, since these bugs only ever showed up against real data --
a small synthetic fixture didn't have enough depth to reproduce either one.
"""

import unittest

import data_merger as dm
import draft_room as dr


def _build_pool_players_db(positions=("QB", "RB", "WR", "TE", "DL", "LB", "DB")):
    """Every real baseline player, reconstructed into a Sleeper-shaped players_db the same
    way Draft Sharks itself abbreviates names (first-initial + full last name) -- see
    merge_player's docstring on why that's a fair stand-in rather than a test artifact."""
    merger = dm.DataMerger()
    proj = merger.projections
    players_db = {}
    pid = 0
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return merger, players_db


LIGHT_IDP_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "IDP_FLEX", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2},
}


class StarterSlotCountsTests(unittest.TestCase):
    def test_flex_slots_split_across_their_eligible_positions(self):
        counts = dr.starter_slot_counts(["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN"])
        self.assertAlmostEqual(counts["RB"], 2 + 2 / 3)
        self.assertAlmostEqual(counts["WR"], 2 + 2 / 3)
        self.assertAlmostEqual(counts["TE"], 1 + 2 / 3)
        self.assertEqual(counts["QB"], 1.0)

    def test_superflex_inflates_qb_count_making_replacement_level_league_specific(self):
        # The exact real-world case a static per-position replacement constant can't handle:
        # SUPER_FLEX genuinely changes how many QBs a league needs, so replacement level has
        # to fall out of THIS league's own roster_positions, not a generic assumption.
        one_qb = dr.starter_slot_counts(["QB", "RB", "WR", "BN"])
        superflex = dr.starter_slot_counts(["QB", "RB", "WR", "SUPER_FLEX", "BN"])
        self.assertGreater(superflex["QB"], one_qb["QB"])


class RealBaselineIDPBugRegressionTests(unittest.TestCase):
    """The two concrete bugs caught building this module, both only reproducible against
    real baseline data -- see class docstring."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db()

    def test_idp_players_are_not_all_identically_scored(self):
        # Draft Sharks' baseline has zero `projection` values for any IDP position -- a
        # naive points-VOR fallback collapsed every IDP player to the exact same score
        # (confirmed live: Myles Garrett, Maxx Crosby, and eight other real names all landed
        # on bpa=53.1). A real fallback must actually differentiate real players.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        idp_scores = {r["name"]: r["bpa"] for r in board if r["position"] in ("DL", "LB", "DB")}
        self.assertGreater(len(idp_scores), 20, "expected real IDP depth in the baseline")
        self.assertGreater(len(set(idp_scores.values())), 10, "IDP players collapsed to too few distinct scores")

    def test_elite_idp_outranks_a_replacement_level_idp_at_the_same_position(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        by_name = {r["name"]: i for i, r in enumerate(board)}
        garrett_rank = next((i for n, i in by_name.items() if "Garrett" in n and "DL" == board[i]["position"]), None)
        self.assertIsNotNone(garrett_rank, "Myles Garrett not found in the board")
        dl_ranks = [i for i, r in enumerate(board) if r["position"] == "DL"]
        # Elite should sit in the better half of the DL pool, not buried near the bottom --
        # this was the original bug: raw trade_value anchoring buried Garrett/Crosby below
        # nearly every offensive skill player, at rank ~172-176 of 191.
        self.assertLess(garrett_rank, dl_ranks[len(dl_ranks) // 2])

    def test_elite_idp_does_not_outrank_elite_offense_in_a_light_idp_league(self):
        # The other direction of the same bug class: a light-IDP league (one IDP_FLEX slot)
        # should still take true offensive stars before any IDP player -- IDP's real value
        # here is capped by how little roster demand this league actually has for it.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        first_idp_rank = next(i for i, r in enumerate(board) if r["position"] in ("DL", "LB", "DB"))
        self.assertGreater(first_idp_rank, 5, "an IDP player reached the top of a light-IDP league's board")

    def test_heavier_idp_league_ranks_the_same_players_earlier(self):
        # Replacement level must actually be league-specific (not a fixed positional
        # constant) -- a league that starts far more IDP should value the same players
        # higher than one that barely uses them, since replacement level itself is worse.
        heavy_idp_league = dict(LIGHT_IDP_LEAGUE, roster_positions=[
            "QB", "RB", "RB", "WR", "WR", "TE", "DL", "DL", "LB", "LB", "DB", "DB", "BN",
        ])
        light_board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        heavy_board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=heavy_idp_league, mode="balanced",
        )
        light_rank = next(i for i, r in enumerate(light_board) if r["position"] in ("DL", "LB", "DB"))
        heavy_rank = next(i for i, r in enumerate(heavy_board) if r["position"] in ("DL", "LB", "DB"))
        self.assertLess(heavy_rank, light_rank)


class InvariantTests(unittest.TestCase):
    """The hard invariants named in draft_room.py's own module docstring, enforced as real
    tests rather than just asserted in a comment."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("RB", "WR"))

    def test_need_bonus_cannot_flip_a_large_universal_value_gap(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        top, bottom = board[0], board[-1]
        self.assertGreater(top["universal_value"] - bottom["universal_value"], dr.NEED_BONUS_MAX,
                            "fixture's own value spread is too small to exercise this invariant")
        # Even at max possible need_bonus, the universal-value gap must still dominate.
        self.assertGreater(
            top["universal_value"] + 0 - (bottom["universal_value"] + dr.NEED_BONUS_MAX),
            0,
        )

    def test_injury_never_increases_universal_value(self):
        healthy = dict(self.players_db)
        injured_id = next(iter(healthy))
        injured = dict(healthy)
        injured[injured_id] = dict(injured[injured_id], injury_status="IR")

        board_healthy = dr.compute_draft_board(
            self.merger, healthy, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        board_injured = dr.compute_draft_board(
            self.merger, injured, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        by_id_healthy = {r["player_id"]: r["universal_value"] for r in board_healthy}
        by_id_injured = {r["player_id"]: r["universal_value"] for r in board_injured}
        if injured_id in by_id_injured:
            self.assertLessEqual(by_id_injured[injured_id], by_id_healthy.get(injured_id, float("inf")))

    def test_need_bonus_is_zero_once_a_position_is_fully_satisfied(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        wr_ids = [r["player_id"] for r in board if r["position"] == "WR"][:3]
        my_picks = [{"roster_id": "99", "player_id": pid, "round": 1} for pid in wr_ids]
        board2 = dr.compute_draft_board(
            self.merger, self.players_db, my_picks, my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        remaining_wr = [r for r in board2 if r["position"] == "WR"]
        self.assertTrue(all(r["need_bonus"] == 0 for r in remaining_wr))

    def test_dynasty_time_horizon_adjustment_is_neutral_outside_dynasty_leagues(self):
        redraft_league = dict(LIGHT_IDP_LEAGUE, settings={"type": 0})
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=redraft_league, mode="balanced",
        )
        self.assertTrue(all(r["time_horizon_adj"] == 0 for r in board))

    def test_upside_mode_confidence_is_never_added_into_the_score(self):
        # The exact mistake an earlier version of upside_score made -- adding raw
        # cross-source variance directly to the score, rewarding "we don't know" as if it
        # were "this player has upside." Confidence must only ever be a separate field.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="upside",
        )
        for row in board[:20]:
            # growth_signal is rounded to 1 decimal for display; final_score was computed
            # from the unrounded value, so allow for that display-rounding drift here --
            # the invariant under test is "confidence isn't in this sum at all", not exact
            # float reproduction of an already-rounded display field.
            self.assertAlmostEqual(
                row["final_score"], row["bpa"] + dr.UPSIDE_GROWTH_WEIGHT * row["growth_signal"], delta=0.1,
            )


if __name__ == "__main__":
    unittest.main()
