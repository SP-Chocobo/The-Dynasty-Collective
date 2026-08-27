"""The demand decomposition's own invariants -- written BEFORE the implementation and required
to pass after it (see CDME_CONTRACTS.md, appendix "dependency map and the minimal
decomposition").

The defect these pin down: "remaining demand" was computed as a LEAGUE-WIDE subtraction
(num_teams x slots - drafted), which is not the sum of the per-team demands, because
max(., 0) does not distribute over a sum. One team hoarding at a position silently cancelled
another team's unmet need at the same position, and the result was then clamped to >= 1 so
that "no starter slot creates demand here" and "one slot still needs filling" produced the
identical replacement rank.

Every test here is about SEMANTICS, not tuning: each one fails for a reason that can be
stated in one sentence about what the number means.
"""

import math
import unittest

import pandas as pd

import draft_room as dr
import pick_synthesis as ps

NUM_TEAMS = 12
# One QB, two RB, two WR, one TE, one FLEX, one K, one DEF, then bench.
BASE_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
ROSTER_POSITIONS = BASE_SLOTS + ["BN"] * 11


def _players_db():
    """A synthetic players_db with plenty of depth at every position -- no DataMerger, so the
    demand arithmetic is isolated from real-data noise. id -> info; ids are "<POS><n>"."""
    db = {}
    for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
        for i in range(1, 61):
            db[f"{pos}{i}"] = {
                "first_name": pos, "last_name": str(i),
                "position": pos, "fantasy_positions": [pos], "team": "FA",
            }
    return db


def _picks(spec):
    """spec = list of (roster_id, position, n) -- n picks at that position by that team."""
    out, used = [], {}
    for roster_id, pos, n in spec:
        for _ in range(n):
            used[pos] = used.get(pos, 0) + 1
            out.append({
                "player_id": f"{pos}{used[pos]}", "roster_id": str(roster_id),
                "round": len(out) // NUM_TEAMS + 1, "pick_no": len(out) + 1,
            })
    return out


def _pool(values_by_position):
    """Minimal scored pool: position + value column + player_id (for the stable tiebreak)."""
    rows = []
    for position, values in values_by_position.items():
        for i, v in enumerate(values):
            rows.append({"position": position, "value": float(v), "player_id": f"{position}{i}"})
    return pd.DataFrame(rows)


class RemainingStarterDemandIsExactTests(unittest.TestCase):
    """remaining_starter_demand is the EXACT half: bounded, per-team, reaching exactly zero.
    These are the properties that make it usable as a valuation-anchor domain test."""

    def test_nobody_drafted_yet_is_full_league_demand(self):
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, [], _players_db())
        slots = dr.starter_slot_counts(ROSTER_POSITIONS)
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            self.assertAlmostEqual(demand[position], NUM_TEAMS * slots[position], places=6)

    def test_an_exhausted_position_reaches_exactly_zero(self):
        # Every team takes exactly its one QB slot. Nobody needs another starting QB.
        db = _players_db()
        picks = _picks([(t, "QB", 1) for t in range(1, NUM_TEAMS + 1)])
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        self.assertEqual(demand["QB"], 0.0)

    def test_an_untouched_position_keeps_its_full_demand(self):
        # 96 picks, none of them a DEF. Every team still needs a starting defense.
        db = _players_db()
        picks = _picks([(t, "WR", 8) for t in range(1, NUM_TEAMS + 1)])
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        self.assertEqual(demand["DEF"], float(NUM_TEAMS))

    def test_one_teams_surplus_cannot_satisfy_another_teams_unmet_demand(self):
        """THE defect, stated directly. Team 1 hoards twelve quarterbacks; the other eleven
        have none. League-wide subtraction reads 12 - 12 = 0 and declares QB satisfied. The
        truth is that eleven teams still need a starting QB."""
        db = _players_db()
        picks = _picks([(1, "QB", NUM_TEAMS)])
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        self.assertEqual(demand["QB"], float(NUM_TEAMS - 1))
        # And the old aggregate, for contrast, would have said zero.
        slots = dr.starter_slot_counts(ROSTER_POSITIONS)
        self.assertEqual(NUM_TEAMS * slots["QB"] - NUM_TEAMS, 0.0)

    def test_demand_never_goes_negative_however_hard_a_position_is_drafted(self):
        db = _players_db()
        picks = _picks([(t, "QB", 5) for t in range(1, NUM_TEAMS + 1)])  # 60 QBs, 12 slots
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        for position, value in demand.items():
            self.assertGreaterEqual(value, 0.0, position)

    def test_demand_is_bounded_above_by_league_wide_slot_capacity(self):
        db = _players_db()
        picks = _picks([(1, "RB", 3), (2, "WR", 2)])
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        slots = dr.starter_slot_counts(ROSTER_POSITIONS)
        for position, value in demand.items():
            self.assertLessEqual(value, NUM_TEAMS * slots.get(position, 0.0) + 1e-9, position)

    def test_demand_is_monotone_non_increasing_as_picks_accumulate(self):
        db = _players_db()
        picks = _picks([(t, pos, 2) for t in range(1, NUM_TEAMS + 1) for pos in ("RB", "WR")])
        previous = None
        for cut in range(0, len(picks) + 1, 12):
            demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks[:cut], db)
            if previous is not None:
                for position in demand:
                    self.assertLessEqual(demand[position], previous[position] + 1e-9, position)
            previous = demand

    def test_draft_order_does_not_alter_demand_for_the_same_final_roster_state(self):
        """Remaining demand cannot depend on the order past picks arrived in. This is the
        invariant a recency-windowed estimator destroys (measured: a 12-pick window swings
        57.6 between two orderings of the identical roster state)."""
        db = _players_db()
        spec = [(t, "K", 1) for t in range(1, NUM_TEAMS + 1)]
        offense = [(t, "WR", 2) for t in range(1, NUM_TEAMS + 1)]
        early = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, _picks(spec + offense), db)
        late = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, _picks(offense + spec), db)
        self.assertEqual(early, late)

    def test_satisfied_and_untouched_are_opposite_answers_not_the_same_one(self):
        """The pair every share-based estimator answered with the sign inverted: league A has
        a kicker on every roster, league B has none, and neither has taken a kicker recently."""
        db = _players_db()
        filler = [(t, "WR", 4) for t in range(1, NUM_TEAMS + 1)]
        a = dr.remaining_starter_demand(
            ROSTER_POSITIONS, NUM_TEAMS,
            _picks([(t, "K", 1) for t in range(1, NUM_TEAMS + 1)] + filler), db)
        b = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, _picks(filler), db)
        self.assertEqual(a["K"], 0.0)
        self.assertEqual(b["K"], float(NUM_TEAMS))

    def test_a_pick_at_a_position_with_no_slot_creates_no_demand_anywhere(self):
        db = _players_db()
        no_kicker = [s for s in ROSTER_POSITIONS if s != "K"] + ["BN"]
        picks = _picks([(t, "K", 1) for t in range(1, NUM_TEAMS + 1)])
        demand = dr.remaining_starter_demand(no_kicker, NUM_TEAMS, picks, db)
        self.assertEqual(demand["K"], 0.0)


class RemainingDraftCapacityTests(unittest.TestCase):
    def test_capacity_starts_at_every_draftable_slot_and_falls_by_one_per_pick(self):
        db = _players_db()
        total = NUM_TEAMS * dr.draftable_slots_per_team(ROSTER_POSITIONS)
        self.assertEqual(dr.remaining_draft_capacity(ROSTER_POSITIONS, NUM_TEAMS, []), float(total))
        picks = _picks([(t, "WR", 1) for t in range(1, NUM_TEAMS + 1)])
        for n in range(len(picks) + 1):
            self.assertEqual(
                dr.remaining_draft_capacity(ROSTER_POSITIONS, NUM_TEAMS, picks[:n]),
                float(total - n),
            )
        del db

    def test_capacity_counts_every_pick_including_positions_the_league_cannot_start(self):
        """The latent accounting defect: picks spent on a position with no starter slot still
        consumed a roster spot. Excluding them asserts they never happened."""
        no_kicker = [s for s in ROSTER_POSITIONS if s != "K"] + ["BN"]
        total = NUM_TEAMS * dr.draftable_slots_per_team(no_kicker)
        picks = _picks([(t, "K", 1) for t in range(1, NUM_TEAMS + 1)])
        self.assertEqual(
            dr.remaining_draft_capacity(no_kicker, NUM_TEAMS, picks), float(total - NUM_TEAMS),
        )

    def test_capacity_never_goes_negative(self):
        picks = _picks([(t, "WR", 40) for t in range(1, NUM_TEAMS + 1)])
        self.assertGreaterEqual(dr.remaining_draft_capacity(ROSTER_POSITIONS, NUM_TEAMS, picks), 0.0)


class ZeroDemandIsNotRankOneTests(unittest.TestCase):
    """The clamp this whole decomposition exists to remove. Two DIFFERENT states -- "no
    starter slot creates demand here" and "one slot still needs filling" -- previously
    produced the identical rank, and therefore the identical replacement level."""

    def test_zero_demand_yields_no_replacement_level_at_all(self):
        pool = _pool({"RB": [100 - i for i in range(30)]})
        levels = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
                                       remaining_demand={"RB": 0.0})
        self.assertNotIn("RB", levels)

    def test_demand_of_one_yields_the_best_remaining_player(self):
        pool = _pool({"RB": [100 - i for i in range(30)]})
        levels = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
                                       remaining_demand={"RB": 1.0})
        self.assertEqual(levels["RB"], 100.0)

    def test_zero_and_one_are_distinguishable(self):
        pool = _pool({"RB": [100 - i for i in range(30)]})
        at_zero = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
                                        remaining_demand={"RB": 0.0})
        at_one = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
                                       remaining_demand={"RB": 1.0})
        self.assertNotEqual(at_zero.get("RB"), at_one.get("RB"))

    def test_a_fractional_demand_below_one_is_not_rounded_up_into_a_replacement(self):
        # 0.7 of a starter slot is less than one whole player of demand. Rounding it to rank 1
        # would rebuild the exact conflation being removed.
        pool = _pool({"TE": [50 - i for i in range(20)]})
        levels = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
                                       remaining_demand={"TE": 0.7})
        self.assertNotIn("TE", levels)

    def test_replacement_ranks_reports_absence_rather_than_one(self):
        db = _players_db()
        picks = _picks([(t, "QB", 1) for t in range(1, NUM_TEAMS + 1)])
        ranks = dr.replacement_ranks(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        self.assertIsNone(ranks["QB"])
        self.assertIsNotNone(ranks["DEF"])

    def test_the_startable_floor_branch_closes_the_same_clamp(self):
        """A second, independent copy of the >= 1 clamp lived in the startable-floor branch:
        when NO remaining player clears the floor it also resolved to rank 1 = best available."""
        pool = _pool({"QB": [300, 280, 260]})
        none_startable = dr.replacement_levels(
            pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
            remaining_demand={"QB": 12.0}, startable_floors={"QB": 400.0})
        one_startable = dr.replacement_levels(
            pool, "value", ROSTER_POSITIONS, NUM_TEAMS,
            remaining_demand={"QB": 12.0}, startable_floors={"QB": 290.0})
        self.assertNotIn("QB", none_startable)
        self.assertEqual(one_startable["QB"], 300.0)


class MissingBenchEvidenceStaysMissingTests(unittest.TestCase):
    """The inferred half may be unknown, and unknown must not be spelled 0.0. The old code
    let an empty `rates` dict fall back to mean_rate = 0.0, which the caller then read as
    "no bench picks at all" and dropped the entire bench term."""

    def _thin_pool(self):
        # Far too few players at any position for a decay rate to be measurable (the function
        # needs 2x starter demand of depth), which is exactly the late-draft state.
        return _pool({"QB": [300, 280], "RB": [200, 190], "WR": [210, 205],
                      "TE": [180, 170], "K": [100, 95], "DEF": [98, 90]})

    def test_appetite_is_none_not_zero_when_no_position_is_measurable(self):
        appetite = dr.positional_bench_appetite(
            self._thin_pool(), "value", ROSTER_POSITIONS, NUM_TEAMS)
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            self.assertIsNone(appetite[position], position)

    def test_a_position_with_no_starter_slot_is_a_real_zero_not_an_unknown(self):
        no_kicker = [s for s in ROSTER_POSITIONS if s != "K"] + ["BN"]
        deep = _pool({p: [100 - i for i in range(60)] for p in ("QB", "RB", "WR", "TE", "DEF")}
                     | {"K": [100 - i for i in range(60)]})
        appetite = dr.positional_bench_appetite(deep, "value", no_kicker, NUM_TEAMS)
        self.assertEqual(appetite["K"], 0.0)

    def test_estimated_bench_demand_is_none_when_appetite_is_unknown(self):
        db = _players_db()
        bench = dr.estimated_bench_demand(
            self._thin_pool(), "value", ROSTER_POSITIONS, NUM_TEAMS, [], db)
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            self.assertIsNone(bench[position], position)

    def test_horizon_declines_rather_than_claiming_a_confident_floor(self):
        """Absent bench evidence made still_to_go 0, rank 1, and certain=True -- "this
        position is finished, and here is a confident floor." Two claims, neither earned."""
        db = _players_db()
        horizon = dr.horizon_replacement(
            self._thin_pool(), "value", ROSTER_POSITIONS, NUM_TEAMS, [], db)
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            self.assertFalse(horizon[position]["certain"], position)
            self.assertIsNone(horizon[position]["value"], position)


class BenchEvidenceCannotReachValuationTests(unittest.TestCase):
    """The isolation boundary, proven by mutation rather than asserted: drive the inferred
    quantity to arbitrary values and every anchor and every score must be byte-identical."""

    def test_replacement_levels_is_identical_under_any_bench_appetite(self):
        pool = _pool({p: [100 - i for i in range(40)] for p in ("QB", "RB", "WR", "TE")})
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, [], _players_db())
        before = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS, demand)
        original = dr.positional_bench_appetite
        try:
            dr.positional_bench_appetite = lambda *a, **k: {p: 999.0 for p in dr.FANTASY_POSITIONS}
            mutated = dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS, demand)
        finally:
            dr.positional_bench_appetite = original
        self.assertEqual(before, mutated)

    def test_replacement_levels_never_calls_the_inferred_branch_at_all(self):
        pool = _pool({p: [100 - i for i in range(40)] for p in ("QB", "RB", "WR", "TE")})
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, [], _players_db())
        calls = []
        original = dr.positional_bench_appetite
        try:
            def _spy(*a, **k):
                calls.append(a)
                return original(*a, **k)
            dr.positional_bench_appetite = _spy
            dr.replacement_levels(pool, "value", ROSTER_POSITIONS, NUM_TEAMS, demand)
        finally:
            dr.positional_bench_appetite = original
        self.assertEqual(calls, [])


class AbsenceSurvivesTheConsumersTests(unittest.TestCase):
    """The .get(..., default) layer: three of the four absence sites converted a missing key
    into a number before any consumer could notice it."""

    def test_a_player_with_no_anchor_gets_no_vor_rather_than_zero(self):
        vor = pd.Series([10.0, float("nan"), 5.0])
        bpa = dr._scale_vor_to_bpa(vor)
        self.assertTrue(math.isnan(bpa.iloc[1]))
        self.assertEqual(bpa.iloc[0], 100.0)

    def test_absence_survives_even_when_every_measurable_vor_is_at_or_below_zero(self):
        # The early-return path previously handed back 0.0 for EVERY row, absent ones included.
        vor = pd.Series([0.0, float("nan"), -3.0])
        bpa = dr._scale_vor_to_bpa(vor)
        self.assertTrue(math.isnan(bpa.iloc[1]))
        self.assertEqual(bpa.iloc[0], 0.0)

    def test_position_view_depth_handles_absent_demand_without_raising(self):
        self.assertEqual(ps.position_view_depth(None), 1)
        self.assertEqual(ps.position_view_depth(3), 3)
        self.assertEqual(ps.position_view_depth(999), ps.POSITION_VIEW_DEPTH_CAP)


class DemandPicksRosterUniverseTests(unittest.TestCase):
    """#68. Per-team demand makes a STRONGER claim than the league-wide subtraction did: it
    asserts knowledge of each team's roster. That claim is only valid when the history's
    roster universe is the league being modelled."""

    def test_an_empty_demand_history_means_nobody_has_drafted_not_nothing_is_known(self):
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, [], _players_db())
        slots = dr.starter_slot_counts(ROSTER_POSITIONS)
        self.assertAlmostEqual(demand["QB"], NUM_TEAMS * slots["QB"], places=6)

    def test_teams_that_have_not_picked_yet_are_treated_as_needing_their_starters(self):
        db = _players_db()
        picks = _picks([(1, "QB", 1), (2, "QB", 1)])  # only two of twelve teams have picked
        demand = dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)
        self.assertEqual(demand["QB"], float(NUM_TEAMS - 2))

    def test_a_history_from_a_larger_roster_universe_is_refused_not_guessed(self):
        """A pick history carrying more distinct rosters than the league has teams did not
        come from this league. The old aggregate could not detect that (it only ever summed
        a count); per-team demand can, and must not silently model the wrong league."""
        db = _players_db()
        picks = _picks([(t, "QB", 1) for t in range(1, NUM_TEAMS + 3)])
        with self.assertRaises(ValueError):
            dr.remaining_starter_demand(ROSTER_POSITIONS, NUM_TEAMS, picks, db)


if __name__ == "__main__":
    unittest.main()
