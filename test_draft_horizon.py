"""Draft-horizon consumption and waiting_cost.

The question replacement_levels does not answer: not "what is this player worth over the guy
at starter-demand rank right now", but "what does deferring this position actually cost me,
given who will STILL be undrafted when the draft ends".

The contrast these tests exist to pin, in the engine's own terms and with no positional
constant anywhere: at the end of a draft you are picking over the dregs of a steep position
and over genuinely viable players at a flat one. Every position runs the identical
arithmetic; the split falls out of each position's own value decay.
"""

from __future__ import annotations

import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr
from test_kdst_integration import KDST_LEAGUE, _players_db


def _pool(spec: dict[str, list[float]]) -> pd.DataFrame:
    """A minimal scored pool: {position: [value, ...]} highest-first."""
    rows = []
    for position, values in spec.items():
        for i, value in enumerate(values):
            rows.append({"player_id": f"{position}{i}", "position": position, "_v": value})
    return pd.DataFrame(rows)


# 12 teams, 2 RB + 1 K starting, 3 bench -> 72 picks. Only two positions exist here, so the
# bench count is kept small deliberately: a 12-bench roster would funnel 144 picks into two
# positions and exhaust them, which tests the fixture rather than the code.
SYNTH_ROSTER = ["RB", "RB", "K", "BN", "BN", "BN"]
SYNTH_TEAMS = 12

# Remaining demand is now a PER-TEAM quantity, so these fixtures have to say which roster
# took what rather than only how many went league-wide -- the distinction the whole
# decomposition exists to preserve (see draft_room.remaining_starter_demand). Picks are
# spread round-robin, which is the realistic reading of "N of these have gone" and the one
# the league-wide subtraction used to assume implicitly.
_SYNTH_DB = {
    f"{pos}{i}": {"position": pos, "fantasy_positions": [pos]}
    for pos in ("RB", "K") for i in range(1, 200)
}


def _picks(counts=None):
    out = []
    for position, n in (counts or {}).items():
        for i in range(int(n)):
            out.append({"player_id": f"{position}{i + 1}",
                        "roster_id": str(len(out) % SYNTH_TEAMS + 1),
                        "round": len(out) // SYNTH_TEAMS + 1, "pick_no": len(out) + 1})
    return out
# Same depth on both, so swapping the labels is a clean experiment.
STEEP = [300 - 2.7 * i for i in range(100)]   # 300 down to ~33
FLAT = [110 - 0.15 * i for i in range(100)]   # 110 down to ~95


class ShapeDrivenBehaviourTests(unittest.TestCase):
    """The whole thesis, on synthetic data whose decay curves are the only difference."""

    def setUp(self):
        self.pool = _pool({"RB": STEEP, "K": FLAT})

    def _horizon(self, drafted=None):
        return dr.horizon_replacement(self.pool, "_v", SYNTH_ROSTER, 12, _picks(drafted), _SYNTH_DB)

    def test_a_flat_position_is_cheap_to_wait_on_and_a_steep_one_is_not(self):
        h = self._horizon()
        rb, k = h["RB"], h["K"]
        self.assertTrue(rb["certain"] and k["certain"])
        rb_wait = STEEP[0] - rb["value"]
        k_wait = FLAT[0] - k["value"]
        self.assertGreater(rb_wait, k_wait * 5,
                           f"steep position should cost far more to defer (RB {rb_wait:.1f} vs K {k_wait:.1f})")

    def test_the_flat_position_retains_almost_all_of_its_starter_value(self):
        # "At the end of the draft you're pulling from legitimately viable kickers."
        h = self._horizon()
        starter_k = FLAT[12 - 1]          # 12 teams x 1 starting slot
        self.assertGreater(h["K"]["value"] / starter_k, 0.90)
        starter_rb = STEEP[24 - 1]        # 12 teams x 2 starting slots
        self.assertLess(h["RB"]["value"] / starter_rb, 0.75)

    def test_nothing_here_reads_the_position_name(self):
        # Swap the two curves between the position labels and the answers swap with them.
        swapped = dr.horizon_replacement(
            _pool({"RB": FLAT, "K": STEEP}), "_v", SYNTH_ROSTER, 12, [], _SYNTH_DB)
        normal = self._horizon()
        self.assertGreater(swapped["K"]["value"], normal["K"]["value"] * 1.5,
                           "a steep curve labelled K must behave like a steep curve")
        self.assertLess(swapped["RB"]["value"], normal["RB"]["value"],
                        "a flat curve labelled RB must behave like a flat curve")


class RemainingDemandTests(unittest.TestCase):
    """What replaced SelfCalibration.

    The class that stood here tested expected_positional_consumption's observed-share blend:
    a room's LIFETIME share of picks at a position, applied to the picks still to come. That
    mechanism was removed rather than repaired, and two of its tests were assertions of the
    defect rather than of a property worth keeping:

      * "consumption totals the number of picks the draft actually has" -- the conservation
        property of a share. Measured across six completed boards, the total was always
        exactly right and the split always wrong, which is the signature of the wrong kind of
        quantity: a share divides, where demand is consumed and runs out.
      * "observed picks move the estimate -- a room hammering RBs should be expected to keep
        hammering RBs" -- reads a pick as EVIDENCE OF APPETITE when a pick is CONSUMPTION OF
        DEMAND. Those have opposite signs, and the inversion was measurable: for two leagues
        with no kicker taken in the last 48 picks, the old model predicted MORE kickers still
        to come for the league that already had twelve than for the one that had none.

    What is tested here instead is the pair that replaced it: an exact, bounded starter
    demand that can reach zero, and an inferred bench demand that is allowed to be unknown."""

    def setUp(self):
        self.pool = _pool({"RB": STEEP, "K": FLAT})

    def _starter(self, drafted=None):
        return dr.remaining_starter_demand(SYNTH_ROSTER, SYNTH_TEAMS, _picks(drafted), _SYNTH_DB)

    def test_required_starters_are_demand_that_will_happen(self):
        # Every team must fill its starting slots, so untouched demand is exactly that.
        demand = self._starter()
        self.assertEqual(demand["RB"], 24.0)
        self.assertEqual(demand["K"], 12.0)

    def test_drafting_a_position_consumes_its_demand_rather_than_predicting_more_of_it(self):
        base = self._starter()
        after = self._starter({"RB": 12})   # one per team
        self.assertLess(after["RB"], base["RB"])
        self.assertEqual(after["RB"], 12.0)

    def test_demand_reaches_exactly_zero_and_stops_there(self):
        self.assertEqual(self._starter({"RB": 24})["RB"], 0.0)
        self.assertEqual(self._starter({"RB": 60})["RB"], 0.0)

    def test_the_two_halves_are_reported_separately_not_fused(self):
        # The exact half is a number even when the inferred half has no evidence to offer.
        thin = _pool({"RB": STEEP[:3], "K": FLAT[:3]})
        starter = dr.remaining_starter_demand(SYNTH_ROSTER, SYNTH_TEAMS, [], _SYNTH_DB)
        bench = dr.estimated_bench_demand(thin, "_v", SYNTH_ROSTER, SYNTH_TEAMS, [], _SYNTH_DB)
        self.assertEqual(starter["RB"], 24.0)
        self.assertIsNone(bench["RB"])

    def test_total_capacity_is_bounded_by_the_draft_not_by_a_share(self):
        total = SYNTH_TEAMS * dr.draftable_slots_per_team(SYNTH_ROSTER)
        self.assertEqual(dr.remaining_draft_capacity(SYNTH_ROSTER, SYNTH_TEAMS, []), float(total))
        self.assertEqual(
            dr.remaining_draft_capacity(SYNTH_ROSTER, SYNTH_TEAMS, _picks({"RB": 12})),
            float(total - 12),
        )

    def test_a_position_nobody_touches_gets_a_better_expected_floor(self):
        # "If nobody touches K, it barely moves" -- and in fact improves, because the picks
        # are going elsewhere, so a better kicker survives to the end.
        before = dr.horizon_replacement(self.pool, "_v", SYNTH_ROSTER, 12, [], _SYNTH_DB)["K"]["value"]
        drained = self.pool[~((self.pool["position"] == "RB") & (self.pool["_v"] > STEEP[29]))]
        after = dr.horizon_replacement(
            drained, "_v", SYNTH_ROSTER, 12, _picks({"RB": 30}), _SYNTH_DB)["K"]["value"]
        self.assertGreaterEqual(after, before)


class SelfLimitingConsumptionTests(unittest.TestCase):
    """Draining a flat position can't manufacture urgency at it.

    When players do come off a flat board, the best one still available falls -- but so does
    the expected end-of-draft floor, by almost exactly as much, because they were
    interchangeable to begin with. The DISTANCE between "what I'd get now" and "what I'd get
    later" is what waiting_cost measures, and at a flat position that distance stays small no
    matter how many are taken. At a steep position it does not: the top of the board falls
    away much faster than the tail, so deferring keeps costing real production.
    """

    def _waiting_cost(self, position, curve, taken):
        pool = _pool({"RB": STEEP, "K": FLAT})
        survivors = sorted(pool.loc[pool["position"] == position, "_v"], reverse=True)[taken:]
        drained = pool[(pool["position"] != position) | (pool["_v"].isin(survivors))]
        floor = dr.horizon_replacement(
            drained, "_v", SYNTH_ROSTER, 12, _picks({position: taken}), _SYNTH_DB)[position]["value"]
        return (survivors[0] - floor) if floor is not None else None

    def test_draining_a_flat_position_barely_moves_its_waiting_cost(self):
        costs = [self._waiting_cost("K", FLAT, n) for n in (0, 5, 10, 15)]
        self.assertTrue(all(c is not None for c in costs))
        self.assertLess(max(costs) - min(costs), 2.0,
                        f"a flat position's waiting cost should stay flat as it drains: {costs}")

    def test_a_steep_position_keeps_a_real_waiting_cost_as_it_drains(self):
        costs = [self._waiting_cost("RB", STEEP, n) for n in (0, 5, 10, 15)]
        self.assertTrue(all(c is not None for c in costs))
        self.assertGreater(min(costs), max(self._waiting_cost("K", FLAT, n) for n in (0, 15)) * 5,
                           f"a steep position must stay expensive to defer: {costs}")


class ShallowPoolHonestyTests(unittest.TestCase):
    """The defect this must not rebuild: treating a truncated source's last row as though it
    were a real replacement level. That is exactly how K/DST were mispriced to begin with."""

    def test_a_horizon_past_the_end_of_the_pool_is_unknown_not_the_worst_loaded_player(self):
        shallow = _pool({"RB": STEEP[:10]})   # 10 RBs against 24+ of starter demand alone
        h = dr.horizon_replacement(shallow, "_v", SYNTH_ROSTER, 12, [], _SYNTH_DB)["RB"]
        self.assertFalse(h["certain"])
        self.assertIsNone(h["value"], "a short list must not answer with its own last row")
        self.assertEqual(h["pool_depth"], 10)

    def test_an_unmeasurable_position_does_not_forfeit_its_bench_picks(self):
        # Measured failure: a 40-deep RB pool scored 0.0 appetite, which handed RB's bench
        # picks to whichever positions loaded deeper and drove one of them to 66 of 180.
        appetite = dr.positional_bench_appetite(
            _pool({"RB": STEEP[:30], "K": FLAT}), "_v", SYNTH_ROSTER, 12)
        self.assertGreater(appetite["RB"], 0.0,
                           "an unmeasurable position must inherit the mean rate, not zero")


class CliffSensitivityTests(unittest.TestCase):
    """A floor is a point estimate on a curve, and positions do not share a curve.

    The estimate is only worth as much as the curve under it: a floor sitting on a plateau
    survives a normal miss in positional consumption, one sitting above a cliff does not.
    Measured on the real board, +/-6 ranks moves DEF by 12 points and QB by 63, because QB
    falls away hard a few ranks past its horizon.
    """

    def test_a_cliff_under_the_horizon_reports_a_wider_error_bar_than_a_plateau(self):
        pool = _pool({"RB": STEEP, "K": FLAT})
        h = dr.horizon_replacement(pool, "_v", SYNTH_ROSTER, 12, [], _SYNTH_DB)
        self.assertGreater(h["RB"]["sensitivity"], h["K"]["sensitivity"] * 5)

    def test_sensitivity_is_absent_exactly_where_the_floor_is(self):
        shallow = _pool({"RB": STEEP[:10]})
        h = dr.horizon_replacement(shallow, "_v", SYNTH_ROSTER, 12, [], _SYNTH_DB)["RB"]
        self.assertIsNone(h["value"])
        self.assertIsNone(h["sensitivity"], "no floor means no error bar to quote either")

    def test_a_flat_position_is_never_reported_as_unresolved(self):
        # The trap this rule has to avoid: judging the swing against the estimate's own
        # magnitude flags every candidate sitting near his position's floor -- which is the
        # interchangeable case the mechanism is MOST confident about. The swing only matters
        # if it could move the verdict across the "you cannot wait" boundary.
        import draft_board_ui as ui
        merger = dm.DataMerger()
        board = dr.compute_draft_board(
            merger, _players_db(merger), [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced")
        for row in board:
            if row["position"] not in ("K", "DEF") or row["waiting_cost"] is None:
                continue
            note = ui._waiting_note(_snapshot_stub(row))
            self.assertNotEqual(note["tone"], "unsettled",
                                f"{row['name']} ({row['position']}) is flat and settled")

    def test_a_player_below_his_own_positions_floor_is_told_waiting_is_better(self):
        import draft_board_ui as ui
        merger = dm.DataMerger()
        board = dr.compute_draft_board(
            merger, _players_db(merger), [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced")
        below = [r for r in board if r["waiting_cost"] is not None and r["waiting_cost"] < 0]
        self.assertTrue(below, "no below-floor players to check")
        note = ui._waiting_note(_snapshot_stub(below[0]))
        self.assertEqual(note["label"], "free")
        self.assertIn("buys nothing", note["title"])


def _snapshot_stub(row):
    """The fields _waiting_note actually reads, off a real board row.

    Read straight off `row` with [] rather than .get(): a stub that quietly supplies None for a
    field the board really carries would let this module keep passing while the UI lost an
    input, which is the "a default in a consumer is a contract change" rule applied to a test
    double. horizon_basis was added for #122 and belongs here for the same reason.
    """
    from types import SimpleNamespace
    return SimpleNamespace(
        name=row["name"], position=row["position"], projected_points=row["projected_points"],
        waiting_cost=row["waiting_cost"], horizon_floor=row["horizon_floor"],
        horizon_sensitivity=row["horizon_sensitivity"], horizon_basis=row["horizon_basis"],
    )


class RealBaselineTests(unittest.TestCase):
    """Against the committed baseline and the real board."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.db = _players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.db, [], my_roster_id="1", league=KDST_LEAGUE, mode="balanced")

    def _best(self, position):
        return next(r for r in self.board if r["position"] == position)

    def test_waiting_is_cheap_at_the_flat_positions(self):
        # Real league-scored data: the best player still undrafted at the end delivers
        # essentially a starter's production at K and DEF.
        for position in ("K", "DEF"):
            row = self._best(position)
            self.assertIsNotNone(row["waiting_cost"], f"{position} floor should be measurable")
            self.assertLess(row["waiting_cost"] / dr.SLEEPER_WEEKLY_TO_SEASON_FACTOR, 1.5,
                            f"{position} should be cheap to defer")

    def test_waiting_cost_is_none_not_zero_where_the_pool_runs_out(self):
        # Zero would read as "waiting is free" -- the most dangerous wrong answer available.
        for row in self.board:
            if row["horizon_floor"] is None:
                self.assertIsNone(row["waiting_cost"])

    def test_the_signal_is_observable_only_and_does_not_touch_acquisition_value(self):
        # team_acquisition_value is its three documented terms and nothing else. If
        # waiting_cost ever starts moving a decision, it will be because someone wired it in
        # deliberately, and this test will say so.
        for row in self.board:
            self.assertAlmostEqual(
                row["final_score"],
                round(row["universal_value"] + row["need_bonus"] + row["eligibility_bonus"], 2),
                places=2,
            )

    def test_the_draw_is_concentrated_at_the_top_of_a_flat_position_and_vanishes_below_it(self):
        # Being per-CANDIDATE rather than per-position, waiting_cost says something a
        # positional verdict never could: the peak of a flat position carries a real (if
        # small) reason to move early, and that reason decays to nothing a few players down.
        # Once the top tier is gone there is no draw left to take a mid-grade one early.
        for position in ("K", "DEF"):
            rows = sorted(
                (r for r in self.board if r["position"] == position and r["waiting_cost"] is not None),
                key=lambda r: -r["projected_points"],
            )
            self.assertGreater(len(rows), 6)
            costs = [r["waiting_cost"] for r in rows]
            self.assertEqual(costs, sorted(costs, reverse=True),
                             f"{position} waiting cost must fall monotonically down the board")
            self.assertGreater(costs[0], costs[6],
                               f"{position}'s best should carry more draw than its seventh")
            self.assertLessEqual(min(costs), 0.0,
                                 f"{position} waiting cost must reach zero at the floor")

    def test_the_horizon_helpers_carry_no_positional_special_cases(self):
        import inspect
        for fn in (dr.horizon_replacement, dr.estimated_bench_demand,
                   dr.remaining_starter_demand, dr.remaining_draft_capacity,
                   dr.positional_bench_appetite, dr._attach_waiting_cost):
            src = inspect.getsource(fn)
            for literal in ('"K"', "'K'", '"DEF"', "'DEF'", '"DST"', "'DST'"):
                self.assertNotIn(literal, src, f"{fn.__name__} names a position directly")


if __name__ == "__main__":
    unittest.main()


class BenchAppetiteSaysWhichKindOfNumberItGave(unittest.TestCase):
    """#122 -- positional_bench_appetite has three outcomes and used to expose only two.

    A position whose remaining pool reaches 2x league demand gets a MEASURED decay rate. One
    whose pool falls short gets the mean of the positions that could be measured -- a real
    number, same type, no marker. The imputation is a deliberate missing-information rule and
    it is the right rule; the defect was that a consumer could not tell it from a measurement.

    Why it is worth a marker rather than a footnote: unlike time_horizon_adj's neutral
    50th-percentile default, which resolves to roughly no opinion, an imputed appetite is a
    POSITIVE number competing for bench capacity against the measured ones. Measured on a real
    12-team 1QB draft it covers rounds 3-15, and four of six positions by round 10.
    """

    ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
    TEAMS = 12

    def _basis(self, spec):
        return dr.positional_bench_appetite_basis(_pool(spec), "_v", self.ROSTER, self.TEAMS)

    def _deep(self, position, count):
        return [100.0 - i * 0.5 for i in range(count)]

    def test_a_deep_pool_is_reported_as_measured(self):
        demand = round(self.TEAMS * dr.starter_slot_counts(self.ROSTER)["RB"])
        basis = self._basis({"RB": self._deep("RB", 2 * demand + 5)})
        self.assertEqual(basis["RB"], dr.APPETITE_MEASURED)

    def test_a_thin_position_beside_a_deep_one_is_reported_as_imputed(self):
        """The adversarial shape: one position unmeasurable while another still is. That is
        exactly the state where the mean-rate fallback fires and produces a number."""
        slots = dr.starter_slot_counts(self.ROSTER)
        rb_demand = round(self.TEAMS * slots["RB"])
        wr_demand = round(self.TEAMS * slots["WR"])
        basis = self._basis({
            "RB": self._deep("RB", 2 * rb_demand - 1),     # one short of measurable
            "WR": self._deep("WR", 2 * wr_demand + 5),     # comfortably measurable
        })
        self.assertEqual(basis["WR"], dr.APPETITE_MEASURED,
                         "vacuous: nothing was measurable, so nothing could be imputed FROM")
        self.assertEqual(basis["RB"], dr.APPETITE_IMPUTED)

    def test_nothing_measurable_anywhere_is_unavailable_not_imputed(self):
        # With no rates at all there is no mean to impute from, and the function returns None
        # rather than a number (#62). The basis must say that, not claim an imputation.
        basis = self._basis({"RB": [100.0, 99.0], "WR": [100.0, 99.0]})
        self.assertEqual(basis["RB"], dr.APPETITE_UNAVAILABLE)
        self.assertEqual(basis["WR"], dr.APPETITE_UNAVAILABLE)

    def test_the_basis_agrees_with_what_the_appetite_actually_returned(self):
        """The two functions must not drift apart -- they read one shared helper for exactly
        this reason, and this is what would catch it if that ever stopped being true."""
        slots = dr.starter_slot_counts(self.ROSTER)
        rb_demand = round(self.TEAMS * slots["RB"])
        wr_demand = round(self.TEAMS * slots["WR"])
        spec = {"RB": self._deep("RB", 2 * rb_demand - 1),
                "WR": self._deep("WR", 2 * wr_demand + 5)}
        appetite = dr.positional_bench_appetite(_pool(spec), "_v", self.ROSTER, self.TEAMS)
        basis = self._basis(spec)
        seen = set()
        for position, label in basis.items():
            seen.add(label)
            if label == dr.APPETITE_UNAVAILABLE:
                continue
            self.assertIsNotNone(appetite[position],
                                 f"{position} is labelled {label} but has no number")
        self.assertIn(dr.APPETITE_MEASURED, seen)
        self.assertIn(dr.APPETITE_IMPUTED, seen)
