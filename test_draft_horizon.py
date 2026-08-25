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
# Same depth on both, so swapping the labels is a clean experiment.
STEEP = [300 - 2.7 * i for i in range(100)]   # 300 down to ~33
FLAT = [110 - 0.15 * i for i in range(100)]   # 110 down to ~95


class ShapeDrivenBehaviourTests(unittest.TestCase):
    """The whole thesis, on synthetic data whose decay curves are the only difference."""

    def setUp(self):
        self.pool = _pool({"RB": STEEP, "K": FLAT})

    def _horizon(self, drafted=None):
        return dr.horizon_replacement(self.pool, "_v", SYNTH_ROSTER, 12, drafted)

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
        swapped = dr.horizon_replacement(_pool({"RB": FLAT, "K": STEEP}), "_v", SYNTH_ROSTER, 12)
        normal = self._horizon()
        self.assertGreater(swapped["K"]["value"], normal["K"]["value"] * 1.5,
                           "a steep curve labelled K must behave like a steep curve")
        self.assertLess(swapped["RB"]["value"], normal["RB"]["value"],
                        "a flat curve labelled RB must behave like a flat curve")


class SelfCalibrationTests(unittest.TestCase):
    """The draft is the evidence: consumption starts from roster-slot priors and moves toward
    what this room is actually doing, with no ADP import."""

    def setUp(self):
        self.pool = _pool({"RB": STEEP, "K": FLAT})

    def _consumption(self, drafted=None):
        return dr.expected_positional_consumption(self.pool, "_v", SYNTH_ROSTER, 12, drafted)

    def test_consumption_totals_the_number_of_picks_the_draft_actually_has(self):
        self.assertAlmostEqual(sum(self._consumption().values()), 12 * len(SYNTH_ROSTER), places=6)

    def test_required_starters_are_demand_that_will_happen(self):
        # Every team must fill its starting slots, so the prior can never fall under them.
        prior = self._consumption()
        self.assertGreaterEqual(prior["RB"], 24)
        self.assertGreaterEqual(prior["K"], 12)

    def test_observed_picks_move_the_estimate(self):
        # A room hammering RBs should be expected to keep hammering RBs.
        base = self._consumption()
        after = self._consumption({"RB": 40, "K": 0})
        self.assertGreater(after["RB"], base["RB"])

    def test_the_estimate_never_falls_below_what_the_draft_has_already_done(self):
        after = self._consumption({"RB": 55, "K": 2})
        self.assertGreaterEqual(after["RB"], 55)

    def test_a_position_nobody_touches_gets_a_better_expected_floor(self):
        # "If nobody touches K, it barely moves" -- and in fact improves, because the picks
        # are going elsewhere, so a better kicker survives to the end.
        before = dr.horizon_replacement(self.pool, "_v", SYNTH_ROSTER, 12)["K"]["value"]
        drained = self.pool[~((self.pool["position"] == "RB") & (self.pool["_v"] > STEEP[29]))]
        after = dr.horizon_replacement(drained, "_v", SYNTH_ROSTER, 12, {"RB": 30})["K"]["value"]
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
            drained, "_v", SYNTH_ROSTER, 12, {position: taken})[position]["value"]
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
        h = dr.horizon_replacement(shallow, "_v", SYNTH_ROSTER, 12)["RB"]
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
        h = dr.horizon_replacement(pool, "_v", SYNTH_ROSTER, 12)
        self.assertGreater(h["RB"]["sensitivity"], h["K"]["sensitivity"] * 5)

    def test_sensitivity_is_absent_exactly_where_the_floor_is(self):
        shallow = _pool({"RB": STEEP[:10]})
        h = dr.horizon_replacement(shallow, "_v", SYNTH_ROSTER, 12)["RB"]
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
    """The four fields _waiting_note actually reads, off a real board row."""
    from types import SimpleNamespace
    return SimpleNamespace(
        name=row["name"], position=row["position"], projected_points=row["projected_points"],
        waiting_cost=row["waiting_cost"], horizon_floor=row["horizon_floor"],
        horizon_sensitivity=row["horizon_sensitivity"],
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
        for fn in (dr.horizon_replacement, dr.expected_positional_consumption,
                   dr.positional_bench_appetite, dr._attach_waiting_cost):
            src = inspect.getsource(fn)
            for literal in ('"K"', "'K'", '"DEF"', "'DEF'", '"DST"', "'DST'"):
                self.assertNotIn(literal, src, f"{fn.__name__} names a position directly")


if __name__ == "__main__":
    unittest.main()
