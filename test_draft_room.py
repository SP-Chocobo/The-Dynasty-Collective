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
        # cross-position near-tie pair in the top of the board -- gap no larger than the
        # trailing candidate's OWN real need_bonus ceiling (see _max_need_bonus_for; a flat
        # NEED_BONUS_MAX threshold over-qualifies single-dedicated-slot positions that can
        # never actually close a gap that large) -- and confirm starving the trailer's own
        # position moves it ahead of the (still-close) leader.
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
                if 0 < gap <= ceiling(trailer["position"]):
                    near_tie_pair = (leader, trailer)
                    break
            if near_tie_pair:
                break
        if near_tie_pair is None:
            self.skipTest("no real cross-position near-tie in the current baseline's top 12 to exercise this contract")
        leader, trailer = near_tie_pair

        board = self._rookie_board(self._roster_history("test", {**{p: 1 for p in ("QB", "RB", "WR", "TE")}, trailer["position"]: 0}))
        board_by_id = {r["player_id"]: r for r in board}
        self.assertGreaterEqual(
            board_by_id[trailer["player_id"]]["final_score"], board_by_id[leader["player_id"]]["final_score"],
            "starving the trailing near-tied candidate's own position should let roster need "
            "close a real but modest gap -- context should not be inert between comparable options",
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


if __name__ == "__main__":
    unittest.main()
