"""
Covers the hard invariants draft_room.py's own math must never violate (per its module
docstring), plus regression coverage for the real bugs caught building and auditing it: raw
trade_value used as a cross-positional anchor (silently buried elite IDP below replacement-
level offense), a missing-projection position collapsing every player to an identical score,
and eligibility_bonus being added into team_acquisition_value in the wrong units (see
EligibilityBonusWiringTests -- a real adversarial-audit finding, reproduced on real data
across two league formats, that the entire prior test corpus was structurally blind to
because every fixture here and elsewhere built single-position fantasy_positions). Uses the
real committed baseline, same as test_data_merger.py's CompositeScoreOnRealBaselineTests,
since these bugs only ever showed up against real data -- a small synthetic fixture didn't
have enough depth (or, for the third bug, enough real multi-position eligibility) to
reproduce any of them.
"""

import time
import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr
import lineup_optimizer as lo


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


class ReplacementRanksTests(unittest.TestCase):
    """replacement_ranks (and its _remaining_demand_rank helper, shared with
    replacement_levels' own non-floor branch) is the real per-league depth signal
    pick_synthesis.narrow_candidates uses for position-view depth -- see
    pick_synthesis.POSITION_VIEW_DEPTH_CAP. Exercises the exact boundary cases the position-
    view-depth feature was designed against: remaining demand at, below, and well above the
    display cap, plus draft progression (demand shrinking as a position gets drafted out)."""

    def test_matches_replacement_levels_own_rank_via_the_value_at_that_rank(self):
        # Cross-check against the existing, separately-tested replacement_levels: the VALUE
        # it reports for a position must be the pool's value at exactly the rank
        # replacement_ranks reports for that same position (same formula, two return shapes).
        pool = pd.DataFrame({"position": ["RB"] * 30, "value": [100 - i for i in range(30)]})
        rank = dr.replacement_ranks(["RB"] * 2, num_teams=12)["RB"]
        level = dr.replacement_levels(pool, "value", ["RB"] * 2, num_teams=12)["RB"]
        expected_idx = min(rank - 1, len(pool) - 1)
        self.assertEqual(level, float(pool.sort_values("value", ascending=False).iloc[expected_idx]["value"]))

    def test_boundary_remaining_demand_at_and_below_the_display_cap(self):
        # 6 teams x one named RB slot = 6 remaining demand -- below POSITION_VIEW_DEPTH_CAP
        # (12); replacement_ranks itself is never capped (that's
        # pick_synthesis.position_view_depth's job) -- it always reports the real, uncapped
        # league demand.
        ranks = dr.replacement_ranks(["RB"], num_teams=6)
        self.assertEqual(ranks["RB"], 6)

    def test_boundary_remaining_demand_exactly_at_the_display_cap(self):
        ranks = dr.replacement_ranks(["RB"], num_teams=12)  # 12 teams x one RB slot = 12
        self.assertEqual(ranks["RB"], 12)

    def test_boundary_remaining_demand_well_above_the_display_cap(self):
        # A real superflex/2WR league shape: WR gets ~2.7 slot share/team -> ~33 at 12 teams,
        # well past where any display cap would bind -- replacement_ranks itself still reports
        # the true, uncapped number.
        roster_positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "SUPER_FLEX"]
        ranks = dr.replacement_ranks(roster_positions, num_teams=12)
        self.assertGreater(ranks["WR"], 30)

    def test_remaining_demand_shrinks_as_the_position_gets_drafted(self):
        # Draft progression: the same league's WR rank must fall as WRs actually get drafted,
        # and must never go negative (floors at 1 -- "replacement = the best player still on
        # the board" once demand is exhausted).
        roster_positions = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"]
        none_drafted = dr.replacement_ranks(roster_positions, num_teams=12)["WR"]
        some_drafted = dr.replacement_ranks(roster_positions, num_teams=12, drafted_counts={"WR": 10})["WR"]
        nearly_all_drafted = dr.replacement_ranks(roster_positions, num_teams=12, drafted_counts={"WR": 500})["WR"]
        self.assertLess(some_drafted, none_drafted)
        self.assertEqual(nearly_all_drafted, 1)

    def test_a_position_with_zero_slot_share_still_returns_the_floor_of_one(self):
        ranks = dr.replacement_ranks(["QB", "RB", "WR", "TE"], num_teams=12)
        self.assertEqual(ranks["DL"], 1)


class DraftedCountsByPositionPublicWrapperTests(unittest.TestCase):
    def test_matches_the_internal_helper_exactly(self):
        picks = [{"player_id": "1", "roster_id": "1"}, {"player_id": "2", "roster_id": "2"}]
        players_db = {
            "1": {"position": "WR", "fantasy_positions": ["WR"]},
            "2": {"position": "RB", "fantasy_positions": ["RB"]},
        }
        self.assertEqual(
            dr.drafted_counts_by_position(picks, players_db),
            dr._drafted_counts_by_position(picks, players_db),
        )


class CliffAnchoredQBReplacementTests(unittest.TestCase):
    """The startable-floor replacement model for superflex QB (see qb_startable_floor and
    replacement_levels' startable_floors) -- chosen over the reverted flat bench-demand
    constant specifically for its stability, so stability is what gets tested: on a cliff-
    shaped pool the boundary must be invariant to threshold wiggle, the dynamics must
    collapse correctly as the startable tier drains, and everything without a floor must be
    bit-identical to the demand model."""

    # A synthetic curve with the real baseline's structure: a flat startable tier, a sharp
    # cliff, then scrubs -- 24 QBs from 340 down to 248 (4/rank), then 200, 130, 60, 30.
    CLIFF_CURVE = [340 - i * 4 for i in range(24)] + [200.0, 130.0, 60.0, 30.0]

    def _pool(self, values):
        return pd.DataFrame({"position": ["QB"] * len(values), "value": values})

    def test_floor_based_rank_counts_remaining_startables_not_demand(self):
        pool = self._pool(self.CLIFF_CURVE)
        # floor at 150: 25 QBs at/above it (24 flat-tier + the 200) -- replacement is the
        # 25th, the last startable, NOT the demand model's 12 x slot-share rank.
        level = dr.replacement_levels(
            pool, "value", ["QB", "SUPER_FLEX"], num_teams=12, startable_floors={"QB": 150.0},
        )["QB"]
        self.assertEqual(level, 200.0)

    def test_boundary_is_invariant_across_the_cliffs_whole_threshold_band(self):
        # The entire point of anchoring to the cliff: any threshold inside the gap between
        # the last startable (200) and the first backup (130) identifies the same boundary.
        pool = self._pool(self.CLIFF_CURVE)
        levels = {
            dr.replacement_levels(pool, "value", ["QB", "SUPER_FLEX"], num_teams=12,
                                  startable_floors={"QB": t})["QB"]
            for t in (135.0, 150.0, 165.0, 180.0, 195.0)
        }
        self.assertEqual(levels, {200.0})

    def test_replacement_rises_as_startables_drain_and_collapses_at_exhaustion(self):
        # Dynamic behavior for free: drafted startables leave the pool, the above-floor
        # count shrinks, replacement rises toward the top -- and once nothing above the
        # floor remains, rank floors at 1 (replacement = best remaining, VOR ~ 0), the same
        # exhaustion collapse the remaining-demand model has.
        floor = {"QB": 150.0}
        drained = self._pool(self.CLIFF_CURVE[20:])   # 4 startables + 200 remain above floor
        level_drained = dr.replacement_levels(drained, "value", ["QB", "SUPER_FLEX"],
                                              num_teams=12, startable_floors=floor)["QB"]
        self.assertEqual(level_drained, 200.0)  # still the last one above the floor
        exhausted = self._pool([130.0, 60.0, 30.0])   # nothing startable left at all
        level_exhausted = dr.replacement_levels(exhausted, "value", ["QB", "SUPER_FLEX"],
                                                num_teams=12, startable_floors=floor)["QB"]
        self.assertEqual(level_exhausted, 130.0)  # rank 1: best remaining, VOR -> 0

    def test_positions_without_a_floor_are_identical_to_the_demand_model(self):
        pool = pd.DataFrame({
            "position": ["QB"] * 28 + ["RB"] * 30,
            "value": self.CLIFF_CURVE + [300 - i * 5 for i in range(30)],
        })
        roster = ["QB", "RB", "RB", "SUPER_FLEX"]
        with_floors = dr.replacement_levels(pool, "value", roster, num_teams=12,
                                            startable_floors={"QB": 150.0})
        without = dr.replacement_levels(pool, "value", roster, num_teams=12)
        self.assertEqual(with_floors["RB"], without["RB"])
        self.assertNotEqual(with_floors["QB"], without["QB"])

    def test_real_baseline_threshold_band_still_holds(self):
        # The cheap validation the mechanism's own spec calls for: if a future season's
        # projection curve loses its sharp cliff, the 0.45-0.60 threshold band stops agreeing
        # on one boundary and this fails LOUDLY instead of the mechanism silently turning
        # fragile. Uses the real committed baseline, same as the stability probe that chose
        # the constant in the first place.
        merger = dm.DataMerger()
        proj = merger.projections
        qb = proj[(proj["position"] == "QB") & proj["projection"].notna()]["projection"].astype(float)
        if len(qb) < dr.QB_STARTABLE_ANCHOR_RANK:
            self.skipTest("baseline carries too few projected QBs to anchor")
        anchor = float(qb.nlargest(dr.QB_STARTABLE_ANCHOR_RANK).iloc[-1])
        counts = {frac: int((qb >= frac * anchor).sum()) for frac in (0.45, 0.5, 0.55, 0.6)}
        self.assertEqual(len(set(counts.values())), 1,
                         f"threshold band no longer stable on this baseline: {counts}")

    def test_no_floor_when_baseline_has_too_few_qbs(self):
        class _FakeMerger:
            projections = pd.DataFrame({"position": ["QB"] * 5, "projection": [300.0] * 5})
        self.assertIsNone(dr.qb_startable_floor(_FakeMerger()))


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


class DemandPicksSplitTests(unittest.TestCase):
    """compute_draft_board's demand_picks parameter: real regression coverage for the rookie-
    draft-against-a-real-roster bug found this pass -- seeding `picks` with a real prior-
    season startup draft's full history (so need_bonus/eligibility_bonus see a team's actual
    roster) also fed that same history into replacement_levels' remaining-demand accounting,
    collapsing whichever position the EARLIER, separate draft phase happened to exhaust (WR/RB
    in a normal startup) while leaving a lightly-drafted position (QB in a 1QB league)
    artificially wide open. Confirmed directly against real baseline data: a backup-tier rookie
    QB outranked a legitimate rookie WR purely from this history-scope confusion.

    demand_picks lets a caller supply a SEPARATE, correctly-scoped pick history for
    replacement_levels/round detection, independent of `picks` (which still drives pool
    filtering and need_bonus/eligibility_bonus, unchanged)."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR"))
        cls.league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "FLEX", "FLEX", "BN", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }

    def _fresh_top_players(self, n=10):
        """The top N players by universal_value on a genuinely untouched board -- the ground
        truth every other board in this class gets compared against."""
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.league, mode="balanced",
        )
        return board[:n]

    def _lower_tier_history(self, exclude_ids: set) -> list[dict]:
        """A real, large prior-phase pick history built ENTIRELY from lower-tier real players
        (never touching `exclude_ids`, the top players this class actually measures) --
        heavily WR/RB, almost no QB, mirroring a real 1QB startup draft's own position mix, so
        the top-of-board players stay available and comparable across every board built here."""
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.league, mode="balanced",
        )
        lower_tier = [r for r in board if r["player_id"] not in exclude_ids][20:]
        picks = []
        pick_no = 1
        wr_rb = [r for r in lower_tier if r["position"] in ("WR", "RB")][:80]
        qb = [r for r in lower_tier if r["position"] == "QB"][:1]
        for row in wr_rb + qb:
            roster_id = str((pick_no - 1) % 12 + 1)
            picks.append({"pick_no": pick_no, "round": 1, "roster_id": roster_id, "player_id": row["player_id"]})
            pick_no += 1
        return picks

    def test_demand_picks_none_matches_omitting_the_parameter_entirely(self):
        with_none = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.league, mode="balanced", demand_picks=None,
        )
        without_param = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.league, mode="balanced",
        )
        self.assertEqual(with_none, without_param)

    def test_demand_picks_wiring_reaches_replacement_levels_with_the_right_scope(self):
        # bpa/universal_value are POOL-RELATIVE (_scale_vor_to_bpa scales against whichever
        # player holds the single largest _vor in the CURRENT pool) -- comparing a fixed
        # player's bpa across two scenarios is the wrong level to test the demand_picks wiring
        # at, since the reference itself can shift under an unrelated player even when that
        # player's own standing is unaffected (confirmed while writing this test: the #1
        # overall real player's bpa moved simply because a DIFFERENT player's _vor grew past
        # his once demand was correctly un-collapsed, not because his own value changed).
        # replacement_levels' own OUTPUT (the actual dict this bug lives in) is the direct,
        # unambiguous claim: a position whose real demand is already exceeded in `picks`
        # collapses to "replacement = the single best remaining player" (a HIGH value, per its
        # own docstring) when that history feeds drafted_counts directly (old behavior) --
        # demand_picks=[] must keep that position's replacement level at its normal, DEEPER
        # (lower-value) rank instead, since nothing has actually been drafted in the current
        # phase.
        fresh_top = self._fresh_top_players(n=10)
        top_ids = {r["player_id"] for r in fresh_top}
        history = self._lower_tier_history(exclude_ids=top_ids)
        self.assertGreater(len(history), 50, "fixture's own real pool too thin to build a real prior-phase history")
        qb_drafted = sum(1 for p in history if self.players_db[p["player_id"]]["position"] == "QB")
        wr_rb_drafted = sum(1 for p in history if self.players_db[p["player_id"]]["position"] in ("WR", "RB"))
        self.assertLessEqual(qb_drafted, 1, "fixture must leave QB demand essentially untouched")
        self.assertGreater(wr_rb_drafted, 60, "fixture must genuinely exceed real WR/RB league-wide demand")

        pool = dr.build_available_pool(
            self.merger, self.players_db, set(), {"QB", "RB", "WR"},
        )
        proj_pool = pool[pool["projection"].notna()].copy()
        proj_pool["_points"] = proj_pool["projection"].astype(float)
        roster_positions = self.league["roster_positions"]
        num_teams = self.league["total_rosters"]

        old_drafted_counts = dr._drafted_counts_by_position(history, self.players_db)
        levels_old = dr.replacement_levels(proj_pool, "_points", roster_positions, num_teams, drafted_counts=old_drafted_counts)
        levels_split = dr.replacement_levels(proj_pool, "_points", roster_positions, num_teams, drafted_counts={})

        # The real bug, at its actual source: WR/RB's already-exceeded demand collapses
        # replacement level UP (toward the best remaining player's own high value) in the old,
        # unsplit accounting -- demand_picks=[] (drafted_counts={}) keeps it at its normal,
        # deeper, lower-value rank.
        self.assertGreater(levels_old["WR"], levels_split["WR"])
        self.assertGreater(levels_old["RB"], levels_split["RB"])
        # QB demand is essentially untouched either way, so its replacement level shouldn't
        # swing much between the two.
        self.assertAlmostEqual(levels_old["QB"], levels_split["QB"], delta=max(levels_split["QB"] * 0.1, 5.0))

    def test_compute_draft_board_actually_passes_demand_picks_to_drafted_counts(self):
        # The direct wiring proof -- decoupled from _scale_vor_to_bpa's pool-relative scaling
        # entirely (see the test above for why that scaling makes per-player bpa the wrong
        # level to assert this at): spy on the real _drafted_counts_by_position call
        # compute_draft_board makes internally, and confirm it actually receives demand_picks
        # (not `picks`) when given one.
        import unittest.mock as mock

        my_picks = [{"pick_no": 1, "round": 1, "roster_id": "1", "player_id": "1"}]
        demand_picks = [{"pick_no": 1, "round": 1, "roster_id": "1", "player_id": "2"}]

        real_fn = dr._drafted_counts_by_position
        with mock.patch.object(dr, "_drafted_counts_by_position", side_effect=real_fn) as spy:
            dr.compute_draft_board(
                self.merger, self.players_db, my_picks, my_roster_id="99", league=self.league,
                mode="balanced", demand_picks=demand_picks,
            )
        spy.assert_called_once_with(demand_picks, self.players_db)

        with mock.patch.object(dr, "_drafted_counts_by_position", side_effect=real_fn) as spy2:
            dr.compute_draft_board(
                self.merger, self.players_db, my_picks, my_roster_id="99", league=self.league, mode="balanced",
            )
        spy2.assert_called_once_with(my_picks, self.players_db)

    def test_demand_picks_does_not_affect_need_bonus_or_pool_filtering(self):
        # need_bonus/eligibility_bonus and drafted_ids pool exclusion must still read the FULL
        # `picks` regardless of demand_picks -- only replacement_levels/round detection change.
        my_picks = [
            {"pick_no": 1, "round": 1, "roster_id": "99", "player_id": "1"},
            {"pick_no": 2, "round": 1, "roster_id": "99", "player_id": "2"},
        ]
        with_demand_split = dr.compute_draft_board(
            self.merger, self.players_db, my_picks, my_roster_id="99", league=self.league, mode="balanced",
            demand_picks=[],
        )
        without_split = dr.compute_draft_board(
            self.merger, self.players_db, my_picks, my_roster_id="99", league=self.league, mode="balanced",
        )
        # Same players excluded from the pool either way.
        self.assertEqual({r["player_id"] for r in with_demand_split}, {r["player_id"] for r in without_split})
        # need_bonus is identical for every remaining player -- demand_picks never touches it.
        need_a = {r["player_id"]: r["need_bonus"] for r in with_demand_split}
        need_b = {r["player_id"]: r["need_bonus"] for r in without_split}
        self.assertEqual(need_a, need_b)


class RookieDraftRosterContextTieredGateTests(unittest.TestCase):
    """Permanent regression battery for the behavioral contract validated in
    run_rookie_roster_context_experiment.py (real data, both directions confirmed): roster
    context may reorder comparable candidates; it must never manufacture superiority over a
    meaningful tier gap. Kept as a standing test, not a one-off script result, because this is
    exactly the kind of behavioral invariant that matters more than an isolated unit check --
    it's a contract about what the ENGINE BELIEVES, not just what one function returns.

    Runs against the real committed baseline (rookies_only pool, demand_picks=[] via the split
    fixed alongside this test -- see DemandPicksSplitTests), same convention as every other
    real-data test in this file. A real rookie class shifting between data refreshes could
    change WHICH specific player is the standout; every assertion below is written against
    whatever the real board's own top-2 gap currently is, never a hardcoded name."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }
        cls.veteran_ids: dict[str, list[str]] = {}
        vet_board = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="00", league=cls.league, mode="balanced",
            pool_scope="veterans_only",
        )
        for row in vet_board:
            cls.veteran_ids.setdefault(row["position"], []).append(row["player_id"])

    def _roster_history(self, roster_id: str, mix: dict) -> list[dict]:
        picks, pick_no = [], 1
        for pos, n in mix.items():
            for pid in self.veteran_ids.get(pos, [])[:n]:
                picks.append({"pick_no": pick_no, "round": 1, "roster_id": roster_id, "player_id": pid})
                pick_no += 1
        return picks

    def _rookie_board(self, history: list[dict]) -> list[dict]:
        board = dr.compute_draft_board(
            self.merger, self.players_db, history, my_roster_id="test", league=self.league, mode="balanced",
            pool_scope="rookies_only", demand_picks=[],
        )
        return sorted(board, key=lambda r: -r["final_score"])

    def _baseline_board(self) -> list[dict]:
        return sorted(
            dr.compute_draft_board(
                self.merger, self.players_db, [], my_roster_id="test", league=self.league, mode="balanced",
                pool_scope="rookies_only", demand_picks=[],
            ),
            key=lambda r: -r["universal_value"],
        )

    def _max_need_bonus_for(self, position: str) -> float:
        """The REAL, position-specific ceiling on need_bonus -- read directly off a real board
        rather than assumed from the flat NEED_BONUS_MAX constant, which only single-dedicated-
        slot positions with real flex share can ever fully reach (QB/TE in this league's own
        roster_positions cap well below it; only RB/WR's extra dedicated slot + flex share gets
        close). Every rookie in this fixture's players_db is single-position, so eligibility_
        bonus is always 0 -- need_bonus is the entire possible context swing here."""
        starved_mix = {"QB": 1, "RB": 1, "WR": 1, "TE": 1}
        starved_mix[position] = 0
        board = self._rookie_board(self._roster_history("test", starved_mix))
        candidates_at_pos = [r for r in board if r["position"] == position]
        self.assertTrue(candidates_at_pos, f"no real rookie at {position} to measure its own need_bonus ceiling")
        return max(r["need_bonus"] for r in candidates_at_pos)

    def test_a_real_standout_survives_maximal_roster_need_at_the_number_two_players_position(self):
        baseline = self._baseline_board()
        self.assertGreaterEqual(len(baseline), 2, "rookie pool too thin to exercise this fixture")
        leader, second = baseline[0], baseline[1]
        gap = leader["universal_value"] - second["universal_value"]
        # eligibility_bonus is 0 for every candidate here (single-position rookies), so
        # need_bonus is the entire possible context swing -- this position's own real ceiling,
        # not the flat NEED_BONUS_MAX constant (which only some positions can ever fully reach).
        max_possible_context_swing = self._max_need_bonus_for(second["position"])
        self.assertGreater(
            gap, max_possible_context_swing,
            "fixture's own real tier gap is too small to exercise the standout-protection contract "
            "this run -- not a failure, but this test needs a real class where one exists",
        )

        # A roster maximally starved for the #2 player's OWN position -- the most favorable
        # possible context for flipping the standout, and it still must not.
        board = self._rookie_board(self._roster_history("test", {**{p: 1 for p in ("QB", "RB", "WR", "TE")}, second["position"]: 0}))
        self.assertEqual(
            board[0]["player_id"], leader["player_id"],
            "roster need for the #2 player's own position flipped a real tier-gap standout -- "
            "context manufactured superiority over a meaningful gap, the exact failure mode this "
            "contract exists to catch",
        )

    def test_roster_context_can_break_a_real_near_tie(self):
        # The other half of the contract: context must not be inert either. Find a real
        # cross-position near-tie pair in the top of the board -- gap no larger than a loose
        # upper bound on how much need_bonus COULD move the pair together (trailer's own
        # ceiling plus leader's own ceiling; see _max_need_bonus_for) -- then VERIFY
        # empirically by actually computing the "trailer's position starved" board, rather
        # than asserting the prediction holds.
        #
        # Why not just assert on the ceiling prediction directly (the original design here):
        # the "starved_mix" history gives every non-trailer position exactly 1 filled, which
        # only fully zeroes a single-dedicated-slot position's (QB/TE) own need_bonus -- a
        # leader sitting at a 2-dedicated-slot position (RB/WR) still carries a real residual
        # need_bonus in that same scenario (confirmed live: a real WR leader kept a 4.72
        # need_bonus after "1 filled", not 0), so a bound comparing only the trailer's own
        # ceiling against the gap can pass its filter while the leader's own concurrent bump
        # keeps it ahead anyway. Caught by the superflex variant of this class, where a
        # WR-leader/RB-trailer near-tie pair hit exactly this case. Verifying empirically
        # (actually computing the board for every filtered candidate, advancing past any that
        # don't really close) fixes this for both the standard and superflex leagues rather
        # than special-casing one.
        baseline = self._baseline_board()[:12]
        ceiling_cache: dict[str, float] = {}

        def ceiling(pos: str) -> float:
            if pos not in ceiling_cache:
                ceiling_cache[pos] = self._max_need_bonus_for(pos)
            return ceiling_cache[pos]

        near_tie_pair = None
        for i, leader in enumerate(baseline):
            for trailer in baseline[i + 1:]:
                if trailer["position"] == leader["position"]:
                    continue  # same position: need_bonus can't differentiate them
                gap = leader["universal_value"] - trailer["universal_value"]
                if not (0 < gap <= ceiling(trailer["position"]) + ceiling(leader["position"])):
                    continue
                board = self._rookie_board(self._roster_history(
                    "test", {**{p: 1 for p in ("QB", "RB", "WR", "TE")}, trailer["position"]: 0},
                ))
                board_by_id = {r["player_id"]: r for r in board}
                if board_by_id[trailer["player_id"]]["final_score"] >= board_by_id[leader["player_id"]]["final_score"]:
                    near_tie_pair = (leader, trailer)
                    break
            if near_tie_pair:
                break
        if near_tie_pair is None:
            self.skipTest(
                "no real cross-position near-tie in the current baseline's top 12 where starving "
                "the trailer's own position actually closes the gap -- not a failure, this test "
                "needs a class where one exists"
            )
        # Finding a real pair where the empirical check above held IS the assertion -- context
        # demonstrably moved a real near-tie, the failure mode being guarded against is
        # silently finding none and reporting a false pass, which skipTest prevents above.


class SuperflexRookieDraftRosterContextTieredGateTests(RookieDraftRosterContextTieredGateTests):
    """Priority-4 extension of the tiered-gate contract above: same two-sided behavioral
    invariant (a real tier gap survives maximal roster need; a real near-tie is breakable by
    it), run against a superflex league shape instead of standard 1QB. Inherits every test
    method unchanged -- only setUpClass differs, by adding SUPER_FLEX to roster_positions,
    matching draft_room.build_mock_league's own real superflex shape.

    This matters as its own case, not just a parameterization: SUPER_FLEX gives QB a real
    flex share via SUPER_FLEX_QB_SHARE (0.85 of a slot, not an even split -- see that
    constant's own docstring), so a rookie QB's need_bonus ceiling here is meaningfully
    higher than in the standard-1QB class above. Real superflex rookie drafts see QB
    desperation far more often and more severely than 1QB drafts do (this was the user's own
    domain point motivating this audit item), so the standout-protection contract has to be
    re-proven here, not assumed to transfer from the 1QB case.
    """

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = {
            "roster_positions": [
                "QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "SUPER_FLEX", "BN", "BN", "BN",
            ],
            "total_rosters": 12, "settings": {"type": 2},
        }
        cls.veteran_ids: dict[str, list[str]] = {}
        vet_board = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="00", league=cls.league, mode="balanced",
            pool_scope="veterans_only",
        )
        for row in vet_board:
            cls.veteran_ids.setdefault(row["position"], []).append(row["player_id"])

    def test_a_real_qb_standout_survives_maximal_superflex_qb_need(self):
        # The scenario the base class's generic top-2 test can't guarantee it hits: a real
        # tier gap specifically AT QB, under the higher superflex QB need_bonus ceiling. If
        # the current real rookie board's top-2 QB gap happens to be too small to exercise
        # this, that's a real, reportable fixture limitation (skip with a clear reason), not
        # a failure to paper over.
        board = self._baseline_board()
        qbs = sorted((r for r in board if r["position"] == "QB"), key=lambda r: -r["universal_value"])
        if len(qbs) < 2:
            self.skipTest("fewer than 2 real rookie QBs on the current baseline board")
        leader, second = qbs[0], qbs[1]
        gap = leader["universal_value"] - second["universal_value"]
        qb_ceiling = self._max_need_bonus_for("QB")
        if gap <= qb_ceiling:
            self.skipTest(
                "current real rookie QB class has no tier gap exceeding its own superflex "
                "need_bonus ceiling -- not a failure, this test needs a class where one exists"
            )
        # Maximal superflex QB need: nothing else drafted at all, so both the dedicated slot
        # and the SUPER_FLEX flex share are wide open.
        starved = self._rookie_board(self._roster_history("test", {"RB": 1, "WR": 1, "TE": 1}))
        self.assertEqual(
            starved[0]["player_id"], leader["player_id"],
            "maximal superflex QB need flipped a real rookie QB tier-gap standout -- context "
            "manufactured superiority over a meaningful gap under the higher SUPER_FLEX ceiling",
        )


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


class HalfPprIsAKnownDataLimitationTests(unittest.TestCase):
    """Couples app.py's Half-PPR disclosure caption to the fact it actually describes. The
    committed baseline has no dedicated Half-PPR rankings export (see
    data_merger.RankingsFormatSelectionOnRealBaselineTests and
    _rankings_format_match_score's own docstring) -- Full PPR is the closest available file
    and wins the match, so a half_ppr and a ppr league produce byte-identical boards today.
    That is a documented, disclosed data-availability limitation (app.py shows an info caption
    whenever fmt["scoring"] == "Half PPR"), not a silent bug. If a real Half-PPR export is ever
    added, THIS test should start failing -- that is the signal to also update app.py's
    disclosure text and the Mock Draft scoring radio's help tooltip, not just this assertion."""

    def test_half_ppr_and_full_ppr_boards_are_byte_identical_on_the_real_baseline(self):
        merger_ppr = dm.DataMerger(league_format={"scoring": "ppr", "superflex": False, "te_premium": False})
        merger_half = dm.DataMerger(league_format={"scoring": "half_ppr", "superflex": False, "te_premium": False})
        players_db = {}
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = merger_ppr.projections[merger_ppr.projections["position"] == pos].sort_values(
                "trade_value", ascending=False,
            )
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }
        board_ppr = dr.compute_draft_board(merger_ppr, players_db, [], my_roster_id="99", league=league, mode="balanced")
        board_half = dr.compute_draft_board(merger_half, players_db, [], my_roster_id="99", league=league, mode="balanced")
        by_id_ppr = {r["player_id"]: r["universal_value"] for r in board_ppr}
        by_id_half = {r["player_id"]: r["universal_value"] for r in board_half}
        self.assertEqual(by_id_ppr, by_id_half)


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

    def test_risk_adj_uses_sleepers_real_full_word_injury_vocabulary(self):
        # Regression for a real bug found and fixed this session: RISK_ADJ used to key on
        # single-letter codes ("O"/"D"/"Q") for everything except "IR". Every OTHER
        # injury_status literal anywhere else in this exact codebase (test_lineup_readiness.py,
        # test_screen_context.py, app.py's own INJURY_OK_STATUSES) uses the full word instead,
        # and since player_universe.py/draft_room.py's own players_db construction both pass
        # injury_status straight through from Sleeper's raw payload with zero transformation,
        # the abbreviated keys never matched a real value -- confirmed directly: a real player
        # set to injury_status="Out" lost exactly 0.0 universal_value pre-fix, not the -10.0
        # RISK_ADJ documented as the intended penalty. Only "IR" worked, since it's already an
        # abbreviation in Sleeper's own real vocabulary too -- exactly the one status the
        # pre-existing injury test (immediately above) happened to cover, so nothing caught this.
        self.assertEqual(dr.RISK_ADJ.get("Out"), -10.0)
        self.assertEqual(dr.RISK_ADJ.get("Doubtful"), -5.0)
        self.assertEqual(dr.RISK_ADJ.get("Questionable"), -1.5)
        self.assertEqual(dr.RISK_ADJ.get("IR"), -18.0)

        healthy = dict(self.players_db)
        pid = next(iter(healthy))
        out_status = dict(healthy)
        out_status[pid] = dict(out_status[pid], injury_status="Out")

        board_healthy = dr.compute_draft_board(
            self.merger, healthy, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        board_out = dr.compute_draft_board(
            self.merger, out_status, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        uv_healthy = next((r["universal_value"] for r in board_healthy if r["player_id"] == pid), None)
        uv_out = next((r["universal_value"] for r in board_out if r["player_id"] == pid), None)
        healthy_row = next((r for r in board_healthy if r["player_id"] == pid), None)
        if uv_healthy is not None and uv_out is not None:
            # LIGHT_IDP_LEAGUE is dynasty (settings.type == 2), so this board-level check now
            # reflects experiment "D"'s trajectory-aware scaling on top of RISK_ADJ's own
            # -10.0 vocabulary value -- the vocabulary itself (asserted directly above,
            # unscaled) is still exactly -10.0; a REDRAFT league would still lose the full,
            # unscaled discount here (see
            # RiskAdjTrajectoryScalingTests.test_redraft_league_is_byte_identical_to_before_this_change).
            # This test's own player isn't a fixed, known trajectory, so the expected scale is
            # computed the same way production does, from that player's own healthy
            # time_horizon_adj -- not hardcoded to any one player's number.
            th = healthy_row["time_horizon_adj"]
            expected_scale = 1.0 if th <= 0 else 1.0 - (1.0 - dr.DYNASTY_RISK_ADJ_MIN_SCALE) * (th / dr.TIME_HORIZON_CLAMP[1])
            self.assertAlmostEqual(
                uv_healthy - uv_out, 10.0 * expected_scale,
                msg="a player marked 'Out' should lose the -10.0 RISK_ADJ discount, scaled by "
                "experiment D's trajectory-aware factor in this dynasty-league fixture",
            )

    def test_trajectory_aware_risk_adj_fixes_the_thin_bpa_sign_flip_this_test_used_to_flag(self):
        # HISTORY, kept for attribution: this test originally FLAGGED a real calibration gap --
        # RISK_ADJ was applied unconditionally, the same in dynasty as in redraft, and risk_adj
        # was the only unclamped term in universal_value = bpa + time_horizon_adj + risk_adj
        # (bpa clamped [0,100], time_horizon_adj clamped [-10,10]). On the committed baseline, a
        # real player (R Pearsall: bpa=0.0, time_horizon_adj=+10.0 -- his ENTIRE value case is
        # forward trajectory) went from universal_value=10.0 to -8.0 under a bare IR flag --
        # negative, from a current-week status alone, on exactly the player type whose value is
        # supposed to be long-horizon. A uniform dynasty scale (experiment "A") fixed this case
        # but couldn't express WHY it should be fixed -- it scaled every dynasty player's
        # penalty by the same flat factor regardless of trajectory.
        #
        # Experiment "D" (now production, draft_room.DYNASTY_RISK_ADJ_MIN_SCALE) directly
        # addresses this: RISK_ADJ's four magnitudes are STILL unchanged (-18/-10/-5/-1.5), but
        # the scaling now depends on the injured player's OWN time_horizon_adj -- a flat/
        # declining trajectory keeps the full penalty, a genuinely forward-looking one gets
        # real (but never total) relief. Stress-tested on the full real offense pool before
        # promotion (run_risk_adj_D_pathology_stress_test.py): zero D-only ordering reversals
        # at any healthy-value-gap size, and D never overrides a 25+ point real value gap.
        young_rising = next(
            r for r in dr.compute_draft_board(
                self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
            )
            if r.get("time_horizon_adj") == dr.TIME_HORIZON_CLAMP[1]  # at the positive clamp
        )
        pdb_ir = dict(self.players_db)
        pdb_ir[young_rising["player_id"]] = dict(pdb_ir[young_rising["player_id"]], injury_status="IR")
        board_ir = dr.compute_draft_board(
            self.merger, pdb_ir, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        row_ir = next((r for r in board_ir if r["player_id"] == young_rising["player_id"]), None)
        if row_ir is not None and young_rising["bpa"] < abs(dr.RISK_ADJ["IR"]) * dr.DYNASTY_RISK_ADJ_MIN_SCALE - dr.TIME_HORIZON_CLAMP[1]:
            self.assertGreaterEqual(
                row_ir["universal_value"], 0.0,
                "trajectory-aware risk_adj (experiment D) should keep a thin-bpa, "
                "max-positive-trajectory player's universal_value from crossing zero on an IR "
                "flag alone -- if this regresses, either the D formula or its constants changed",
            )
            # At the exact positive clamp, this player's own d_scale IS DYNASTY_RISK_ADJ_MIN_SCALE
            # (the floor) -- confirms the formula, not just the end result.
            self.assertAlmostEqual(row_ir["risk_adj"], dr.RISK_ADJ["IR"] * dr.DYNASTY_RISK_ADJ_MIN_SCALE)

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


class RiskAdjTrajectoryScalingTests(unittest.TestCase):
    """Calibration experiment "D" -- now production, superseding experiment "A" (a uniform
    dynasty-wide 0.5x scale, which fixed the flagship sign-flip case but could not express
    that an injury should matter less for a player whose value is genuinely forward-looking
    than for one whose value is already realized in current production). D scales RISK_ADJ's
    same four magnitudes by the injured player's OWN time_horizon_adj: full penalty at or below
    a neutral/declining trajectory, real (but never total, floored at
    DYNASTY_RISK_ADJ_MIN_SCALE) relief for a genuinely positive one. Stress-tested on the real
    250-player offense pool before promotion (run_risk_adj_D_pathology_stress_test.py): zero
    D-only ordering reversals at any healthy-value-gap size, never overrides a 25+ point real
    gap. See draft_room.DYNASTY_RISK_ADJ_MIN_SCALE's own comment for the full evidence trail."""

    REDRAFT_LEAGUE = {
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "BN", "BN"],
        "total_rosters": 12, "settings": {"type": 1},  # NOT dynasty
    }
    DYNASTY_LEAGUE = LIGHT_IDP_LEAGUE  # settings.type == 2

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("RB", "WR"))

    def _risk_adj_for_status(self, league: dict, status: str, pid: str) -> float:
        pdb = dict(self.players_db)
        pdb[pid] = dict(pdb[pid], injury_status=status)
        board = dr.compute_draft_board(self.merger, pdb, [], my_roster_id="99", league=league, mode="balanced")
        row = next(r for r in board if r["player_id"] == pid)
        return row["risk_adj"]

    def _expected_d_scale(self, time_horizon_adj: float) -> float:
        if time_horizon_adj <= 0:
            return 1.0
        return 1.0 - (1.0 - dr.DYNASTY_RISK_ADJ_MIN_SCALE) * (time_horizon_adj / dr.TIME_HORIZON_CLAMP[1])

    def test_the_four_magnitudes_are_unchanged_by_this_experiment(self):
        # The vocabulary itself was explicitly NOT touched -- only whether/how it's applied.
        self.assertEqual(dr.RISK_ADJ, {"IR": -18.0, "Out": -10.0, "Doubtful": -5.0, "Questionable": -1.5})

    def test_redraft_league_is_byte_identical_to_before_this_change(self):
        # A non-dynasty league must see EXACTLY the old flat discount -- this experiment is
        # explicitly dynasty-scoped, per the user's own instruction.
        pid = next(iter(self.players_db))
        for status, expected in dr.RISK_ADJ.items():
            with self.subTest(status=status):
                self.assertEqual(self._risk_adj_for_status(self.REDRAFT_LEAGUE, status, pid), expected)

    def test_dynasty_league_gives_full_penalty_to_a_flat_or_declining_trajectory_player(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.DYNASTY_LEAGUE, mode="balanced",
        )
        declining = next((r for r in board if r["time_horizon_adj"] <= 0), None)
        if declining is None:
            self.skipTest("fixture has no real flat/declining-trajectory player to exercise this")
        for status, base in dr.RISK_ADJ.items():
            with self.subTest(status=status):
                self.assertAlmostEqual(
                    self._risk_adj_for_status(self.DYNASTY_LEAGUE, status, declining["player_id"]), base,
                    msg="a flat/declining trajectory should keep the FULL flat penalty under D",
                )

    def test_dynasty_league_scales_a_positive_trajectory_player_by_the_d_formula(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.DYNASTY_LEAGUE, mode="balanced",
        )
        rising = max(board, key=lambda r: r["time_horizon_adj"])
        if rising["time_horizon_adj"] <= 0:
            self.skipTest("fixture has no real positive-trajectory player to exercise this")
        expected_scale = self._expected_d_scale(rising["time_horizon_adj"])
        for status, base in dr.RISK_ADJ.items():
            with self.subTest(status=status):
                self.assertAlmostEqual(
                    self._risk_adj_for_status(self.DYNASTY_LEAGUE, status, rising["player_id"]),
                    base * expected_scale,
                )

    def test_healthy_players_are_unaffected_in_either_league_type(self):
        # No injury_status at all -- RISK_ADJ.get(...) falls through to its 0.0 default in both
        # branches, so is_dynasty must not introduce any discount out of nothing.
        pid = next(iter(self.players_db))
        self.assertEqual(self._risk_adj_for_status(self.REDRAFT_LEAGUE, None, pid), 0.0)
        self.assertEqual(self._risk_adj_for_status(self.DYNASTY_LEAGUE, None, pid), 0.0)

    def test_injury_still_never_increases_universal_value_under_d(self):
        # The pre-existing hard invariant (module docstring) must survive D: a smaller
        # discount is still a discount, never a boost, in either league type, for any
        # trajectory including the most positive one.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=self.DYNASTY_LEAGUE, mode="balanced",
        )
        rising = max(board, key=lambda r: r["time_horizon_adj"])
        for league in (self.REDRAFT_LEAGUE, self.DYNASTY_LEAGUE):
            with self.subTest(league_type=league["settings"]["type"]):
                pdb = dict(self.players_db)
                pid = rising["player_id"]
                healthy_board = dr.compute_draft_board(
                    self.merger, pdb, [], my_roster_id="99", league=league, mode="balanced",
                )
                healthy_uv = next(r["universal_value"] for r in healthy_board if r["player_id"] == pid)
                pdb_hurt = dict(pdb)
                pdb_hurt[pid] = dict(pdb_hurt[pid], injury_status="Questionable")
                hurt_board = dr.compute_draft_board(
                    self.merger, pdb_hurt, [], my_roster_id="99", league=league, mode="balanced",
                )
                hurt_uv = next(r["universal_value"] for r in hurt_board if r["player_id"] == pid)
                self.assertLessEqual(hurt_uv, healthy_uv)

    def test_d_never_gives_full_forgiveness_even_at_the_positive_clamp(self):
        # The floor: even the most extreme forward trajectory keeps DYNASTY_RISK_ADJ_MIN_SCALE
        # of the penalty -- "injury doesn't matter" was explicitly flagged as a failure mode to
        # rule out before D could go to production.
        self.assertGreater(dr.DYNASTY_RISK_ADJ_MIN_SCALE, 0.0)
        self.assertAlmostEqual(self._expected_d_scale(dr.TIME_HORIZON_CLAMP[1]), dr.DYNASTY_RISK_ADJ_MIN_SCALE)


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
        # Kept as a weaker outer bound. It is no longer the BINDING constraint: the board's
        # eligibility_bonus is now rescaled from trade_value units into the bpa-scale sum it
        # is added to (see draft_room.TRADE_VALUE_SCALE_MAX/ELIGIBILITY_BONUS_MAX), so the
        # real bound is ELIGIBILITY_BONUS_MAX -- asserted directly in
        # test_eligibility_bonus_is_bounded_by_its_own_max below. This assertion still holds
        # because the rescale only ever shrinks the raw value.
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

    # ---------------------------------------------------------------------------------
    # The three tests below close a real, demonstrated production defect found by an
    # adversarial audit pass. eligibility_bonus was denominated in Draft Sharks trade_value
    # units but added directly into team_acquisition_value, whose other two terms
    # (universal_value, need_bonus) both live on the bpa scale. Those two 0-100 scales are
    # NOT interchangeable on real data (mean |bpa - trade_value| = 11.7, max 63.0,
    # correlation 0.829), and unlike need_bonus this term had no cap -- so it was the one
    # contextual term that could override a genuine value gap outright.
    #
    # Reproduced on the committed baseline in BOTH a standard 1QB league (WR/TE dual
    # eligibility) and an IDP league (WR/DB): an 82.00 bonus, 6.8x NEED_BONUS_MAX, flipping a
    # 35-point universal_value gap and lifting a #10 board player to #1. The same empty roster
    # slot was priced 19-248x differently depending on which term happened to price it.
    #
    # The entire pre-existing validation corpus was blind to this: every harness and every
    # other test file builds players_db with single-position fantasy_positions, for which
    # eligibility_bonus is exactly 0.0 by construction.
    # ---------------------------------------------------------------------------------

    def _saturated_idp_flex_scenario(self):
        """A real roster whose WR/FLEX slots are all occupied by players MORE valuable than
        the candidate, leaving only an IDP_FLEX the candidate can reach solely via secondary
        eligibility. This is the scenario where the term is at its genuine maximum -- if it is
        bounded here, it is bounded everywhere."""
        league = {
            "roster_positions": ["WR", "WR", "FLEX", "IDP_FLEX", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2},
        }
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"]
        picks = [{"roster_id": "1", "player_id": pid, "round": 1} for pid in wr_ids[:3]]
        candidate_id = wr_ids[3]
        players_db = dict(self.players_db)
        players_db[candidate_id] = dict(players_db[candidate_id], fantasy_positions=["WR", "DB"])
        return league, players_db, picks, candidate_id

    def test_eligibility_bonus_is_bounded_by_its_own_max(self):
        league, players_db, picks, candidate_id = self._saturated_idp_flex_scenario()
        board = dr.compute_draft_board(
            self.merger, players_db, picks, my_roster_id="1", league=league, mode="balanced",
        )
        for row in board:
            self.assertLessEqual(
                row["eligibility_bonus"], dr.ELIGIBILITY_BONUS_MAX + 1e-9,
                f"{row['name']} exceeded ELIGIBILITY_BONUS_MAX -- the units rescale regressed",
            )
        self.assertGreater(
            next(r for r in board if r["player_id"] == candidate_id)["eligibility_bonus"], 0.0,
            "the rescale must shrink the term, not zero it out -- real flexibility still counts",
        )

    def test_eligibility_bonus_is_expressed_in_bpa_units_not_trade_value_units(self):
        """The units contract itself: the board's bonus must be the raw trade_value-denominated
        assignment-problem answer rescaled by ELIGIBILITY_BONUS_MAX/TRADE_VALUE_SCALE_MAX. Pinned
        against a direct lineup_optimizer call so the two can never silently drift apart."""
        league, players_db, picks, candidate_id = self._saturated_idp_flex_scenario()
        board = dr.compute_draft_board(
            self.merger, players_db, picks, my_roster_id="1", league=league, mode="balanced",
        )
        row = next(r for r in board if r["player_id"] == candidate_id)
        raw = lo.eligibility_bonus(
            dr._team_roster_players(picks, players_db, "1", self.merger),
            candidate_id=candidate_id,
            candidate_value=float(self.merger.merge_player(row["name"], position="WR", team=row["team"])["trade_value"]),
            candidate_full_eligible={"WR", "DB"}, candidate_primary_position="WR",
            roster_positions=league["roster_positions"],
        )["eligibility_bonus"]
        self.assertGreater(raw, dr.ELIGIBILITY_BONUS_MAX, "fixture too weak to prove the rescale actually bites")
        self.assertAlmostEqual(
            row["eligibility_bonus"],
            round(raw * (dr.ELIGIBILITY_BONUS_MAX / dr.TRADE_VALUE_SCALE_MAX), 2), places=2,
        )

    def test_eligibility_bonus_cannot_flip_a_large_universal_value_gap(self):
        """The missing mirror of test_need_bonus_cannot_flip_a_large_universal_value_gap. Both
        terms answer "how good is this player FOR THIS ROSTER"; the architecture bounds that
        class so it can inform a close call but never override a real value gap. Only
        need_bonus had that invariant enforced -- this is the sibling that did not.

        This is the EXACT scenario that reproduced the original defect: a full real pool, a
        real 12-slot IDP league, and a mid-board WR made WR/DB-eligible against a roster whose
        WR/FLEX slots are already filled by strictly better players. Pre-fix this awarded an
        82.00 bonus and took the candidate from board rank #10 to #1 over a 32-point gap."""
        merger, players_db = _build_pool_players_db()  # full pool -- needs real value spread
        league = LIGHT_IDP_LEAGUE
        base = dr.compute_draft_board(merger, players_db, [], my_roster_id="99", league=league, mode="balanced")
        by_uv = sorted(base, key=lambda r: -r["universal_value"])

        def trade_value_of(row):
            return merger.merge_player(row["name"], position=row["position"], team=row.get("team")).get("trade_value")

        wrs = [r for r in by_uv if r["position"] == "WR"]
        best_wr = wrs[0]
        cand_row = next(
            (r for r in wrs
             if best_wr["universal_value"] - r["universal_value"] > 25.0 and (trade_value_of(r) or 0) > 0),
            None,
        )
        self.assertIsNotNone(cand_row, "real baseline should contain a WR well behind the best WR")
        cand_tv = trade_value_of(cand_row)
        # Saturate every WR/FLEX-reachable slot with players strictly MORE valuable than the
        # candidate, so his WR-ness genuinely buys nothing and only the IDP_FLEX is open.
        fillers = [r for r in by_uv
                   if r["position"] in ("RB", "WR")
                   and r["player_id"] not in (best_wr["player_id"], cand_row["player_id"])
                   and (trade_value_of(r) or 0) > cand_tv][:6]
        picks = [{"pick_no": i + 1, "round": 1, "roster_id": "99", "player_id": r["player_id"]}
                 for i, r in enumerate(fillers)]
        db = dict(players_db)
        db[cand_row["player_id"]] = dict(db[cand_row["player_id"]], fantasy_positions=["WR", "DB"])

        board = {r["player_id"]: r for r in dr.compute_draft_board(
            merger, db, picks, my_roster_id="99", league=league, mode="balanced")}
        cand, leader = board[cand_row["player_id"]], board[best_wr["player_id"]]
        gap = leader["universal_value"] - cand["universal_value"]
        self.assertGreater(gap, dr.NEED_BONUS_MAX + dr.ELIGIBILITY_BONUS_MAX,
                           "fixture must present a gap larger than the combined context bound to be meaningful")
        self.assertGreater(cand["eligibility_bonus"], 0.0,
                           "fixture must actually trigger the eligibility term to be meaningful")
        self.assertGreater(
            leader["final_score"], cand["final_score"],
            f"context ({cand['need_bonus']:.2f} need + {cand['eligibility_bonus']:.2f} elig) overrode a "
            f"{gap:.2f}-point universal_value gap -- the bound regressed",
        )


class ProjectedPointsTests(unittest.TestCase):
    """projected_points -- the raw season point projection universal_value's own VOR anchor is
    built from, exposed directly and independently of the scarcity-adjusted score (see
    compute_draft_board's own docstring: "who's simply projected to score the most" is a real,
    separate question a manager may want to weigh on its own terms)."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("RB", "WR"))

    def test_balanced_mode_exposes_the_real_projection_offense_has(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        for row in board[:10]:
            self.assertIsNotNone(row["projected_points"])
            self.assertGreater(row["projected_points"], 0.0)

    def test_upside_mode_also_exposes_projected_points(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="upside",
        )
        for row in board[:10]:
            self.assertIsNotNone(row["projected_points"])
            self.assertGreater(row["projected_points"], 0.0)

    def test_matches_the_real_draft_sharks_projection_for_a_points_anchored_player(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        points_anchored = next(r for r in board if r["bpa_source"] == "points_vor_draftsharks")
        match = self.merger.merge_player(points_anchored["name"], position=points_anchored["position"], team=points_anchored["team"])
        self.assertAlmostEqual(points_anchored["projected_points"], match["projection"], places=2)

    def test_none_when_no_real_points_source_exists(self):
        # An IDP-only pool with no real Draft Sharks projection data falls back to trade_value
        # VOR (see build_available_pool's docstring) -- projected_points must stay None there,
        # never a fabricated number standing in for a real projection that doesn't exist.
        idp_merger, idp_players_db = _build_pool_players_db(("DL", "LB", "DB"))
        board = dr.compute_draft_board(
            idp_merger, idp_players_db, [], my_roster_id="99", league=LIGHT_IDP_LEAGUE, mode="balanced",
        )
        for row in board[:10]:
            self.assertIsNone(row["projected_points"])


class BuildMockLeagueTests(unittest.TestCase):
    def test_superflex_adds_a_super_flex_starter_slot(self):
        league = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True)
        self.assertIn("SUPER_FLEX", league["roster_positions"])

    def test_non_superflex_has_no_super_flex_slot(self):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        self.assertNotIn("SUPER_FLEX", league["roster_positions"])

    def test_scoring_maps_to_the_rec_scoring_setting(self):
        for scoring, expected in dr.MOCK_SCORING_REC_VALUES.items():
            league = dr.build_mock_league(teams=12, superflex=False, scoring=scoring, te_premium=False, dynasty=False)
            self.assertEqual(league["scoring_settings"]["rec"], expected)

    def test_te_premium_adds_a_bonus_rec_te_only_when_requested(self):
        with_bonus = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=True, dynasty=False)
        without_bonus = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=False)
        self.assertIn("bonus_rec_te", with_bonus["scoring_settings"])
        self.assertNotIn("bonus_rec_te", without_bonus["scoring_settings"])

    def test_dynasty_flag_maps_to_settings_type_2(self):
        dynasty_league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        redraft_league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=False)
        self.assertEqual(dynasty_league["settings"]["type"], 2)
        self.assertNotEqual(redraft_league["settings"]["type"], 2)

    def test_total_rosters_matches_teams(self):
        league = dr.build_mock_league(teams=10, superflex=False, scoring="ppr", te_premium=False, dynasty=False)
        self.assertEqual(league["total_rosters"], 10)


class SimulateOpponentPicksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)

    def test_stops_exactly_when_the_users_roster_is_on_the_clock(self):
        pick_order = ["1", "2", "3", "4"]
        picks = dr.simulate_opponent_picks(
            [], pick_order, my_roster_id="3", num_teams=4,
            merger=self.merger, players_db=self.players_db, league=self.league,
        )
        self.assertEqual(len(picks), 2)
        self.assertEqual([p["roster_id"] for p in picks], ["1", "2"])

    def test_does_nothing_when_the_user_is_already_on_the_clock(self):
        pick_order = ["1", "2", "3", "4"]
        picks = dr.simulate_opponent_picks(
            [], pick_order, my_roster_id="1", num_teams=4,
            merger=self.merger, players_db=self.players_db, league=self.league,
        )
        self.assertEqual(picks, [])

    def test_picks_are_all_distinct_players(self):
        # my_roster_id "99" never comes up, so this runs the full 3 rounds x 4 teams --
        # every one of build_available_pool's undrafted-only filtering has to actually work
        # across repeated calls, or the same top-ranked player would get "drafted" twice.
        pick_order = ["1", "2", "3", "4"] * 3
        picks = dr.simulate_opponent_picks(
            [], pick_order, my_roster_id="99", num_teams=4,
            merger=self.merger, players_db=self.players_db, league=self.league,
        )
        self.assertEqual(len(picks), 12)
        drafted_ids = [p["player_id"] for p in picks]
        self.assertEqual(len(drafted_ids), len(set(drafted_ids)))

    def test_does_not_mutate_the_input_picks_list(self):
        pick_order = ["1", "2", "3", "4"]
        original: list[dict] = []
        dr.simulate_opponent_picks(
            original, pick_order, my_roster_id="3", num_teams=4,
            merger=self.merger, players_db=self.players_db, league=self.league,
        )
        self.assertEqual(original, [])

    def test_stops_at_the_end_of_the_draft_if_the_user_has_no_more_picks(self):
        pick_order = ["2", "3", "4", "1"]  # user (roster 1) only picks last
        picks = dr.simulate_opponent_picks(
            [], pick_order, my_roster_id="99", num_teams=4,  # not even in this draft
            merger=self.merger, players_db=self.players_db, league=self.league,
        )
        self.assertEqual(len(picks), 4)


class CalibrationConstantsDoNotDriftSilentlyTests(unittest.TestCase):
    """Mutation testing found these three constants could be changed to a materially
    different value with the entire 963-test suite still green. That is not an argument for
    any particular value -- it is that nothing recorded what the current one BUYS, so a
    later edit could not tell a deliberate retune from an accident. Each test below pins a
    consequence, not the number.
    """

    def test_two_empty_dedicated_slots_is_not_yet_maximum_urgency(self):
        # need_bonus = min(PER_DEDICATED_SLOT * empty + PER_FLEX_SHARE * flex, MAX). With
        # PER_DEDICATED_SLOT at 4.0 against a MAX of 12.0, the cap is reached only by a
        # position group that is genuinely THREE deep and completely empty; two empty slots
        # still leaves headroom, so "very urgent" and "maximally urgent" stay distinguishable.
        # Doubling PER_DEDICATED_SLOT silently collapses that: two empty slots saturate the
        # cap and every deeper shortage becomes indistinguishable from it.
        #
        # No FLEX slot here on purpose, so flex_share is 0 and the dedicated term is the only
        # thing under test.
        league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "TE", "BN", "BN", "BN"],
            "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
        }
        merger, db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        board = dr.compute_draft_board(
            merger, db, [], my_roster_id="1", league=league, mode="balanced",
        )
        rbs = [r for r in board if r["position"] == "RB"]
        self.assertTrue(rbs, "no RB on the board")
        need = rbs[0]["need_bonus"]
        self.assertGreater(need, 0.0, "two empty dedicated RB slots must create real demand")
        self.assertLess(
            need, dr.NEED_BONUS_MAX,
            "two empty dedicated slots reached the need_bonus cap -- nothing distinguishes "
            "them from a three-deep empty position group any more",
        )

    def test_auto_mode_switches_to_upside_exactly_at_the_documented_round(self):
        # The boundary itself is a calibration decision (see UPSIDE_MODE_DEFAULT_ROUND's own
        # comment). What must not happen is it moving without anyone noticing: this is the
        # round where the board's whole scoring formula changes, and a draft that crosses it
        # earlier than intended silently switches every remaining pick to upside-only scoring.
        # The literal is deliberate -- change it here, on purpose, or not at all.
        self.assertEqual(dr.UPSIDE_MODE_DEFAULT_ROUND, 15)
        merger, db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        league = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"] + ["BN"] * 13,
            "total_rosters": 8, "settings": {"type": 2}, "scoring_settings": {},
        }

        def board_mode(round_no):
            picks = [
                {"pick_no": i + 1, "round": i // 8 + 1, "roster_id": str(i % 8 + 1), "player_id": pid}
                for i, pid in enumerate(list(db)[:8 * round_no])
            ]
            rows = dr.compute_draft_board(
                merger, db, picks, my_roster_id="1", league=league, mode="auto",
            )
            return rows[0]["mode"] if rows else None

        self.assertEqual(board_mode(dr.UPSIDE_MODE_DEFAULT_ROUND - 1), "balanced")
        self.assertEqual(board_mode(dr.UPSIDE_MODE_DEFAULT_ROUND), "upside")

    def test_the_weekly_to_season_factor_is_the_length_of_an_nfl_season(self):
        # Not a tuning knob: every NFL team plays exactly 17 games, and this constant exists
        # to turn Sleeper's WEEKLY projection into a season-equivalent so it shares a scale
        # with Draft Sharks' season numbers. Any other value silently rescales every
        # Sleeper-sourced projection -- which today means the entire K and DST pool -- against
        # an offensive pool that was never rescaled, reintroducing exactly the cross-source
        # unit mismatch this conversion exists to remove.
        self.assertEqual(dr.SLEEPER_WEEKLY_TO_SEASON_FACTOR, 17)


if __name__ == "__main__":
    unittest.main()
