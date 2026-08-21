"""
Covers the hard invariants draft_room.py's own math must never violate (per its module
docstring), plus regression coverage for the two real bugs caught building it: raw
trade_value used as a cross-positional anchor (silently buried elite IDP below replacement-
level offense), and a missing-projection position collapsing every player to an identical
score. Uses the real committed baseline, same as test_data_merger.py's
CompositeScoreOnRealBaselineTests, since these bugs only ever showed up against real data --
a small synthetic fixture didn't have enough depth to reproduce either one.
"""

import time
import unittest

import pandas as pd

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

    def test_super_flex_slot_is_heavily_qb_weighted_not_split_evenly(self):
        # The real bug this constant fixes: splitting SUPER_FLEX evenly across QB/RB/WR/TE
        # (this module's original, generic flex-slot logic) badly understated real superflex
        # QB demand -- confirmed directly, the #1-projected QB by raw season points ranked
        # outside the top 30 overall on a real superflex board before this existed. A real
        # competitive superflex league fills that slot with a QB the vast majority of the
        # time, not a roughly-even split the way an ordinary RB/WR/TE FLEX slot behaves.
        counts = dr.starter_slot_counts(["QB", "SUPER_FLEX", "BN"])
        self.assertAlmostEqual(counts["QB"], 1.0 + dr.SUPER_FLEX_QB_SHARE)
        remaining_share = (1.0 - dr.SUPER_FLEX_QB_SHARE) / 3
        self.assertAlmostEqual(counts["RB"], remaining_share)
        self.assertAlmostEqual(counts["WR"], remaining_share)
        self.assertAlmostEqual(counts["TE"], remaining_share)

    def test_an_ordinary_flex_slot_still_splits_evenly_unlike_super_flex(self):
        # SUPER_FLEX is the one deliberate exception -- every other flex type must still
        # split evenly, since RB/WR/TE genuinely do compete roughly interchangeably for an
        # ordinary FLEX slot in real drafting behavior.
        counts = dr.starter_slot_counts(["RB", "WR", "TE", "FLEX", "BN"])
        self.assertAlmostEqual(counts["RB"], 1 + 1 / 3)
        self.assertAlmostEqual(counts["WR"], 1 + 1 / 3)
        self.assertAlmostEqual(counts["TE"], 1 + 1 / 3)


class ReplacementLevelMonotonicityTests(unittest.TestCase):
    """replacement_levels is the actual mechanism behind "a deep position gets a smaller
    scarcity bonus" -- the exact property the whole IDP-depth discussion needed proven, not
    just asserted. Pure, DataMerger-free synthetic DataFrames so each property is isolated
    from real-data noise: change exactly one thing, hold everything else constant."""

    def _pool(self, values: list[float], position: str = "RB") -> pd.DataFrame:
        return pd.DataFrame({"position": [position] * len(values), "value": values})

    def test_a_deeper_pool_of_good_players_raises_replacement_level(self):
        # Same replacement RANK (say, 24th), but the players sitting near that rank are
        # genuinely better in the deep pool -- so replacement level itself should rise.
        thin = self._pool([100 - i * 4 for i in range(30)])  # steep drop-off
        deep = self._pool([100 - i * 1 for i in range(30)])  # shallow drop-off, same length
        thin_level = dr.replacement_levels(thin, "value", ["RB"] * 2, num_teams=12)["RB"]
        deep_level = dr.replacement_levels(deep, "value", ["RB"] * 2, num_teams=12)["RB"]
        self.assertGreater(deep_level, thin_level)

    def test_a_stronger_replacement_level_shrinks_a_top_players_vor(self):
        # Same top-of-position value in both pools; only the depth behind them differs.
        # The top player's VOR (value - replacement) must be smaller against the deeper,
        # stronger replacement pool -- this is the actual "IDP is deep, so elite IDP's
        # scarcity premium should be smaller than an equally-thin offense position's" check.
        thin = self._pool([99] + [100 - i * 4 for i in range(1, 30)])
        deep = self._pool([99] + [100 - i * 1 for i in range(1, 30)])
        thin_level = dr.replacement_levels(thin, "value", ["RB"] * 2, num_teams=12)["RB"]
        deep_level = dr.replacement_levels(deep, "value", ["RB"] * 2, num_teams=12)["RB"]
        self.assertLess(99 - deep_level, 99 - thin_level)

    def test_more_starting_slots_at_a_position_raises_the_replacement_rank(self):
        # More usable slots at a position pushes the replacement rank deeper into the pool
        # (a worse player becomes "replacement"), which is what actually drives a heavier-IDP
        # league's real scarcity premium -- see test_draft_room's
        # test_heavier_idp_league_ranks_the_same_players_earlier for the full-pipeline version.
        pool = self._pool([100 - i for i in range(40)])
        light = dr.replacement_levels(pool, "value", ["RB"], num_teams=12)["RB"]
        heavy = dr.replacement_levels(pool, "value", ["RB"] * 3, num_teams=12)["RB"]
        self.assertLessEqual(heavy, light)


class PoolScopeTests(unittest.TestCase):
    """pool_scope's rookie detection is real source data (KeepTradeCut's own export already
    flags current-class rookies -- see _rookie_lookup), not a maintained list, so these run
    against the real committed baseline rather than a synthetic fixture."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("RB", "WR", "QB", "TE"))

    def test_rookies_only_and_veterans_only_partition_the_all_scope_pool(self):
        usable = {"QB", "RB", "WR", "TE"}
        all_pool = dr.build_available_pool(self.merger, self.players_db, set(), usable, pool_scope="all")
        rookies = dr.build_available_pool(self.merger, self.players_db, set(), usable, pool_scope="rookies_only")
        vets = dr.build_available_pool(self.merger, self.players_db, set(), usable, pool_scope="veterans_only")
        self.assertGreater(len(rookies), 0, "expected real rookies in the baseline")
        self.assertEqual(len(rookies) + len(vets), len(all_pool))
        self.assertEqual(set(rookies["player_id"]) & set(vets["player_id"]), set())

    def test_rookies_only_pool_is_usable_by_compute_draft_board(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE,
            mode="balanced", pool_scope="rookies_only",
        )
        self.assertGreater(len(board), 5, "expected a real rookie draft board")


class DataIntegrityTests(unittest.TestCase):
    """Sanity checks on the pool draft_room.py actually scores, decoupled from the scoring
    math itself -- a scoring-behavior test failing because the underlying data was thin or
    malformed is a different bug than the formula being wrong, and conflating the two is
    exactly what burned time earlier while building this (a suspicious IDP result that
    turned out to be a real, separate data gap -- see RealBaselineIDPBugRegressionTests)."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db()
        cls.pool = dr.build_available_pool(
            cls.merger, cls.players_db, set(), {"QB", "RB", "WR", "TE", "DL", "LB", "DB"},
        )

    def test_every_usable_position_has_enough_players_for_a_real_replacement_curve(self):
        counts = self.pool["position"].value_counts()
        for position in ("QB", "RB", "WR", "TE", "DL", "LB", "DB"):
            self.assertGreater(counts.get(position, 0), 20, f"{position} pool too thin to trust a replacement rank")

    def test_no_player_is_missing_a_position(self):
        self.assertTrue(self.pool["position"].notna().all())
        self.assertFalse((self.pool["position"] == "").any())

    def test_trade_value_is_numeric_and_non_negative(self):
        self.assertTrue(pd.api.types.is_numeric_dtype(self.pool["trade_value"]))
        self.assertTrue((self.pool["trade_value"].dropna() >= 0).all())

    def test_idp_positions_are_the_ones_actually_missing_projection_data(self):
        # Documents the real, current data gap this module works around (see
        # build_available_pool's docstring) as a live check -- if Draft Sharks' baseline
        # ever starts projecting IDP, this test should start failing, which is the signal
        # to remove the within-position-percentile fallback and simplify back to pure VOR.
        for position in ("DL", "LB", "DB"):
            self.assertFalse(self.pool.loc[self.pool["position"] == position, "projection"].notna().any())
        for position in ("RB", "WR"):
            self.assertTrue(self.pool.loc[self.pool["position"] == position, "projection"].notna().any())


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
        #
        # LIGHT_IDP_LEAGUE has exactly one IDP_FLEX slot -- real league-wide demand for IDP is
        # tiny (~4 total slots split three ways), so most of the pool genuinely sits AT OR
        # BELOW replacement level once VOR is computed honestly, and correctly clips to the
        # same ~0 score rather than being artificially spread out (see
        # test_heavier_idp_league_ranks_the_same_players_earlier below for the same pool
        # showing rich differentiation once real demand actually exists). The bar here is
        # "not literally the original identical-score bug", not "broadly differentiated
        # regardless of real demand" -- a low, deliberately un-generous threshold.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        idp_scores = {r["name"]: r["bpa"] for r in board if r["position"] in ("DL", "LB", "DB")}
        self.assertGreater(len(idp_scores), 20, "expected real IDP depth in the baseline")
        self.assertGreater(len(set(idp_scores.values())), 4, "IDP players collapsed to too few distinct scores")

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

    def test_three_idp_positions_top_player_do_not_all_tie_at_the_maximum_score(self):
        # The exact artifact an independent audit caught in the first working version: each
        # position's WITHIN-POSITION-percentile fallback pinned its own top player to bpa=100
        # regardless of real demand, so DL/LB/DB's three best remaining players all tied at
        # the identical maximum score and landed in the top 25 of the WHOLE light-IDP-league
        # board -- a pure normalization artifact, not real relative value. Fixed by folding
        # the trade_value fallback into the same shared linear VOR scale as the points-
        # anchored group, so a locally-renormalized small subgroup can't out-score real data.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        top_by_position = {}
        for pos in ("DL", "LB", "DB"):
            rows = [r for r in board if r["position"] == pos]
            if rows:
                top_by_position[pos] = max(r["bpa"] for r in rows)
        self.assertGreaterEqual(len(top_by_position), 2, "need at least two IDP positions represented")
        self.assertFalse(
            all(v == 100.0 for v in top_by_position.values()),
            f"every IDP position's top player pinned to the maximum score again: {top_by_position}",
        )


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

    def test_bpa_magnitude_tracks_the_real_vor_gap_not_a_percentile_rank(self):
        # An independent audit caught this directly: percentile-ranking VOR (rather than
        # scaling it linearly) threw away the actual SIZE of the gap between players -- a
        # real 60-point VOR gap between the #1 and #8 remaining players compressed to a
        # 2.8-point bpa gap, small enough that the additive adjustment terms below it (which
        # can swing several times that) ended up deciding the board instead of the anchor.
        # bpa must scale with the real gap: a much bigger VOR gap must produce a much bigger
        # bpa gap, not a roughly-equal one.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        top8 = board[:8]
        big_gap = top8[0]["bpa"] - top8[3]["bpa"]  # #1 vs #4: real tier gap expected
        small_gap = top8[3]["bpa"] - top8[7]["bpa"]  # #4 vs #8: shallower part of the pool
        self.assertGreater(top8[0]["bpa"] - top8[-1]["bpa"], 10.0, "fixture's spread too flat to exercise this")
        # Not a strict inequality in every possible fixture shape, but percentile-ranking
        # would make these two gaps nearly identical (rank-based spacing is ~uniform) --
        # linear VOR scaling should not.
        self.assertNotAlmostEqual(big_gap, small_gap, delta=0.5)

    def test_replacement_level_reflects_remaining_demand_not_static_league_demand(self):
        # An independent audit caught this directly: with a STATIC target rank (num_teams x
        # starters, held constant regardless of how many were already drafted), draining a
        # position past its real demand made replacement level collapse toward the bottom of
        # an ever-thinning pool -- which made every remaining player at that position look
        # artificially scarce right when nobody actually needed one anymore (confirmed live:
        # a 12-team 1-WR-slot-equivalent league ranked a deep, already-oversupplied position's
        # 19th-drafted player as a top-10 overall pick). Once real demand is exhausted, VOR
        # for the position must NOT climb back up -- it must stay flat/near its floor.
        board0 = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        rb_sorted = [r for r in board0 if r["position"] == "RB"]
        # Draft away far more RBs than this league's real starting demand for RB.
        rb_demand = round(LIGHT_IDP_LEAGUE["total_rosters"] * dr.starter_slot_counts(LIGHT_IDP_LEAGUE["roster_positions"])["RB"])
        overdrafted = rb_sorted[: rb_demand + 15]
        picks = [{"roster_id": str(i % 12 + 1), "player_id": r["player_id"], "round": 1} for i, r in enumerate(overdrafted)]
        board1 = dr.compute_draft_board(
            self.merger, self.players_db, picks, my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        best_remaining_rb = next(r for r in board1 if r["position"] == "RB")
        best_remaining_rank = board1.index(best_remaining_rb)
        # The original bug put an overdrafted position's best remainder near the TOP of the
        # whole board (single digits) -- it must instead stay buried, reflecting that real
        # demand for this position is already exhausted.
        self.assertGreater(best_remaining_rank, 20, "an overdrafted position's leftover climbed toward the top of the board")

    def test_need_bonus_favors_an_unfilled_dedicated_slot_over_already_satisfied_flex_demand(self):
        # An independent audit caught this directly: a flat per-slot rate scaled with how
        # many TOTAL roster slots a position has, so a team with ZERO players at a position
        # scored a smaller bonus than a team that already had its dedicated slots filled and
        # merely wanted one more for bench/flex depth -- confirmed live (a real league shape:
        # a team with zero QBs scored +3.0, a team wanting a fourth WR scored +9.0, backwards
        # from real draft urgency). An unfilled MANDATORY slot must outweigh already-satisfied
        # flex-only demand. Self-contained within this fixture's own RB/WR positions: fill
        # RB's dedicated slots exactly (no excess), leave WR's dedicated slots completely
        # empty, and confirm WR's need_bonus (an unfilled mandatory slot) beats what an
        # already-satisfied-plus-one RB would score.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        rb_dedicated = dr.dedicated_slot_counts(LIGHT_IDP_LEAGUE["roster_positions"])["RB"]
        rb_picks = [r["player_id"] for r in board if r["position"] == "RB"][:rb_dedicated + 1]  # one past dedicated
        picks = [{"roster_id": "1", "player_id": pid, "round": 1} for pid in rb_picks]
        board_after = dr.compute_draft_board(
            self.merger, self.players_db, picks, my_roster_id="1", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        excess_rb_need_bonus = next(r["need_bonus"] for r in board_after if r["position"] == "RB")
        empty_wr_need_bonus = next(r["need_bonus"] for r in board_after if r["position"] == "WR")
        self.assertGreater(empty_wr_need_bonus, excess_rb_need_bonus)

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

    def test_need_bonus_is_the_only_thing_that_differs_between_two_teams_at_the_same_draft_state(self):
        # universal_value has to be genuinely team-agnostic -- what ANY manager watching this
        # exact draft state would compute. Same picks list (so the same remaining pool, same
        # replacement levels) evaluated for two different rosters must produce identical
        # universal_value per player; only need_bonus (and therefore final_score) may differ.
        # Comparing the same team before/after ITS OWN picks doesn't isolate this, since
        # drafting also shrinks the shared pool for everyone -- this holds the pool fixed and
        # varies only which roster is asking.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        picks = [{"roster_id": "1", "player_id": r["player_id"], "round": 1} for r in board[:3]]

        team_a = {r["player_id"]: r for r in dr.compute_draft_board(
            self.merger, self.players_db, picks, my_roster_id="97", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )}
        team_b = {r["player_id"]: r for r in dr.compute_draft_board(
            self.merger, self.players_db, picks, my_roster_id="98", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )}
        for player_id, row_a in list(team_a.items())[:30]:
            row_b = team_b[player_id]
            self.assertEqual(row_a["universal_value"], row_b["universal_value"], player_id)

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


class EligibilityBonusWiringTests(unittest.TestCase):
    """End-to-end coverage for lineup_optimizer.py's wiring into team_acquisition_value --
    not just the standalone module (see test_lineup_optimizer.py's own suite), but through
    the real compute_draft_board pipeline: a real roster's actual drafted players, a real
    league's actual roster_positions, and a real Draft-Sharks-matched candidate."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("WR", "DB"))

    def test_multi_eligible_candidate_gets_a_positive_bonus_when_it_unlocks_an_open_idp_flex(self):
        league = {
            "roster_positions": ["WR", "WR", "FLEX", "IDP_FLEX", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"]
        # Fill WR, WR, FLEX with three ordinary single-position WRs -- no open WR/FLEX room left.
        roster_wrs = wr_ids[:3]
        picks = [{"roster_id": "1", "player_id": pid, "round": 1} for pid in roster_wrs]

        # A Travis-Hunter-shaped candidate: a real WR the app already has a Draft Sharks match
        # for, flagged (via a players_db copy, same isolation convention as
        # test_injury_never_increases_universal_value above) as also DB-eligible.
        candidate_id = wr_ids[3]
        control_id = wr_ids[4]  # an ordinary single-position WR, otherwise treated identically
        players_db = dict(self.players_db)
        players_db[candidate_id] = dict(players_db[candidate_id], fantasy_positions=["WR", "DB"])

        board = dr.compute_draft_board(
            self.merger, players_db, picks, my_roster_id="1", league=league, mode="balanced",
        )
        by_id = {r["player_id"]: r for r in board}
        self.assertGreater(
            by_id[candidate_id]["eligibility_bonus"], 0.0,
            "WR/DB eligibility should unlock the open IDP_FLEX slot a WR-only player of similar value could not reach",
        )
        self.assertEqual(by_id[control_id]["eligibility_bonus"], 0.0)
        # The wiring invariant itself: final_score must equal the documented three-term sum,
        # not a silently-dropped term.
        row = by_id[candidate_id]
        self.assertAlmostEqual(
            row["final_score"], row["universal_value"] + row["need_bonus"] + row["eligibility_bonus"], places=2,
        )

    def test_full_board_stays_fast_even_when_most_candidates_are_multi_eligible(self):
        # eligibility_bonus solves a real assignment problem per candidate row -- this guards
        # against the exact class of regression draft_strategy.py's own perf bug was (see that
        # module's docstring): a stress scenario where roughly a third of a ~175-player pool
        # is multi-eligible (skips eligibility_bonus's single-position fast path) against a
        # roster that already has 15 drafted players to optimize against.
        merger, players_db = self.merger, {}
        proj = merger.projections
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(80)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                fantasy_positions = ["RB", "WR", "TE"] if pos in ("RB", "WR", "TE") and pid % 3 == 0 else [pos]
                players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": fantasy_positions, "team": row.get("team"),
                }
        league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN", "BN", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
        }
        board_ids = list(players_db.keys())
        picks = [{"roster_id": "1", "player_id": pid, "round": 1} for pid in board_ids[:15]]
        t0 = time.time()
        dr.compute_draft_board(merger, players_db, picks, my_roster_id="1", league=league, mode="balanced")
        elapsed = time.time() - t0
        self.assertLess(elapsed, 15.0, f"compute_draft_board took {elapsed:.1f}s with heavy multi-eligibility -- eligibility_bonus regression")

    def test_eligibility_bonus_never_exceeds_the_candidates_own_trade_value(self):
        # Self-limiting by construction (see eligibility_bonus's own docstring) -- no
        # NEED_BONUS_MAX-style cap exists because the marginal contribution of a single
        # player can never exceed his own value. Assert that invariant directly against the
        # same open-IDP_FLEX scenario, where the bonus is at its largest plausible size.
        league = {
            "roster_positions": ["WR", "WR", "FLEX", "IDP_FLEX", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"]
        roster_wrs = wr_ids[:3]
        picks = [{"roster_id": "1", "player_id": pid, "round": 1} for pid in roster_wrs]
        candidate_id = wr_ids[3]
        players_db = dict(self.players_db)
        players_db[candidate_id] = dict(players_db[candidate_id], fantasy_positions=["WR", "DB"])

        board = dr.compute_draft_board(
            self.merger, players_db, picks, my_roster_id="1", league=league, mode="balanced",
        )
        row = next(r for r in board if r["player_id"] == candidate_id)
        match = self.merger.merge_player(row["name"], position="WR", team=row["team"])
        self.assertLessEqual(row["eligibility_bonus"], match["trade_value"] + 1e-6)


if __name__ == "__main__":
    unittest.main()
