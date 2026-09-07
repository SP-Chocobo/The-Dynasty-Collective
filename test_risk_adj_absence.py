"""#203: a health adjustment to a price that was never produced.

`bpa` is NaN for a row the pricing layer could not value, so `universal_value` is NaN and
every consumer reads it as absent. `risk_adj` was the one term in that decomposition that went
on answering anyway -- measured on the production-shaped board, 102 of 1,510 unpriced rows
carried a confident -18.0. That is #166's shape (a quantity crossing a layer without the thing
that gives it meaning) failing toward the STRONGER claim: -18.0 reads as "measured and
penalised", not "unpriced".

SCOPE, and it is deliberately narrow. The owner ruled the MAGNITUDES stay -- the five priced
rows where risk_adj does real work keep -18.0, and no re-weighting is derived from a five-row
sample (#56). Only the absence is repaired.

The other decomposition terms are NOT touched, and each for its own stated reason: the tests at
the bottom pin those reasons so a later pass does not "tidy" them into the same treatment and
destroy a real measurement.
"""

from __future__ import annotations

import json
import math
import unittest
from pathlib import Path

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

CAPTURE = Path("data/fixtures/sleeper_capture.json")


class HealthPenaltyIsUnchangedTests(unittest.TestCase):
    """The ruling: magnitudes stay. Pin them so the absence repair cannot drift into one."""

    def test_the_table_still_holds_the_measured_magnitudes(self):
        self.assertEqual(dr.RISK_ADJ, {"IR": -18.0, "Out": -10.0, "Doubtful": -5.0})

    def test_a_priced_IR_row_with_no_games_reported_still_takes_the_full_penalty(self):
        # availability_basis None = the #191 haircut could not reach him (Sleeper reports no
        # games-played figure), so the flat penalty is the only thing standing in for it.
        self.assertEqual(dr.health_penalty("IR", None), -18.0)

    def test_the_haircut_still_suppresses_the_penalty_where_it_DID_fire(self):
        import player_universe as pu
        self.assertEqual(dr.health_penalty("IR", pu.RULE_FLOOR), 0.0)


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class RiskAdjAbsenceOnTheRealBoardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(CAPTURE, encoding="utf-8") as handle:
            cap = json.load(handle)
        shape = cap["league_shape"]
        cls.league = {"roster_positions": shape["roster_positions"],
                      "scoring_settings": shape["scoring_settings"],
                      "total_rosters": shape["total_rosters"], "settings": {"type": 2}}
        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(cls.league))
        players_db, _ = rdb.build_players_db_from_capture()
        cls.board = dr.compute_draft_board(
            merger, players_db, [], my_roster_id="1", league=cls.league, mode="balanced",
            sleeper_projections=rdb.season_projections_from_capture(),
            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        cls.unpriced = [r for r in cls.board if r.get("universal_value") is None]
        cls.priced = [r for r in cls.board if r.get("universal_value") is not None]

    def test_the_population_is_not_vacuous(self):
        # A rate over an empty set is not a rate. Both halves have to exist for the rest of
        # this class to mean anything.
        self.assertGreater(len(self.unpriced), 100, "no unpriced rows -- tests below are vacuous")
        self.assertGreater(len(self.priced), 100, "no priced rows -- tests below are vacuous")

    def test_no_unpriced_row_carries_a_risk_adjustment(self):
        offenders = [(r["name"], r["injury_status"], r["risk_adj"])
                     for r in self.unpriced if r.get("risk_adj") is not None]
        self.assertEqual(offenders[:5], [],
                         f"{len(offenders)} unpriced rows explain a price that does not exist")

    def test_absence_is_None_and_never_a_float_nan(self):
        # NaN would satisfy the test above only if it were normalised; this is the guard that
        # the normalisation list actually carries risk_adj.
        floats = [r["name"] for r in self.unpriced
                  if isinstance(r.get("risk_adj"), float) and math.isnan(r["risk_adj"])]
        self.assertEqual(floats[:5], [])

    def test_every_priced_row_still_states_a_risk_adjustment(self):
        # The repair must not turn a measured 0.0 into an absence. A healthy priced player has
        # a MEASURED zero adjustment, which is information.
        missing = [r["name"] for r in self.priced if r.get("risk_adj") is None]
        self.assertEqual(missing[:5], [])

    def test_the_penalty_still_reaches_the_rows_it_is_for(self):
        real = [r for r in self.priced if r["risk_adj"] != 0.0]
        self.assertTrue(real, "risk_adj now fires on nothing -- the repair went too far")
        for row in real:
            self.assertIsNotNone(row["injury_status"], row["name"])
            self.assertLess(row["risk_adj"], 0.0, row["name"])

    def test_universal_value_and_risk_adj_are_absent_together_or_present_together(self):
        # The pair contract, stated as one invariant over the whole board rather than two
        # separate counts.
        for row in self.board:
            self.assertEqual(row.get("universal_value") is None, row.get("risk_adj") is None,
                             f"{row['name']}: uv and risk_adj disagree about being measured")


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class WhatWasDeliberatelyNotChangedTests(RiskAdjAbsenceOnTheRealBoardTests):
    """Three terms that LOOK like the same defect and are not. Pinned so a later pass does not
    'fix' them into destroying a real measurement."""

    @staticmethod
    def _is_a_real_number(value) -> bool:
        """MUTATION SURVIVOR M3, recorded rather than smoothed over.

        These three tests were first written as `if r.get(field)`, and a mutation that replaced
        need_bonus with float("nan") on every unpriced row PASSED ALL 18. The reason is that
        `bool(float("nan"))` is True in Python: a NaN is truthy, so a truthiness check cannot
        distinguish "a number was emitted" from "the column was destroyed". That is the same
        conflation the absence contract exists to forbid, committed inside the instrument that
        is supposed to police it -- exactly the hazard the measurement discipline names.
        """
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and not math.isnan(value))

    def test_need_bonus_survives_on_unpriced_rows_because_it_measures_the_ROSTER(self):
        # need_bonus answers "does THIS ROSTER have an unfilled slot at his position" -- true
        # or false regardless of whether anyone can price him. Nulling it would discard a
        # measurement that was genuinely taken. Whether an unpriced row should carry one at all
        # is a decision, not a defect, and it is not mine.
        carried = [r for r in self.unpriced
                   if self._is_a_real_number(r.get("need_bonus")) and r["need_bonus"] != 0.0]
        self.assertTrue(carried, "need_bonus was nulled on unpriced rows -- see #203's scope")

    def test_depth_basis_still_reports_vacant_because_that_IS_the_companion(self):
        # 'vacant' is depth_basis doing its job: it says the 0.0 beside it is "not measured
        # here", never "this position is safe". Removing it would remove the explanation, not
        # the overclaim.
        stated = [r for r in self.unpriced if isinstance(r.get("depth_basis"), str)]
        self.assertTrue(stated, "depth_basis was nulled -- the companion is the point")

    def test_time_horizon_adj_keeps_its_documented_zero(self):
        # "No multi-year dimension -> neither penalised nor rewarded" is a ruling with its own
        # docstring, not an unexamined default. Reopening it is a separate decision.
        zeros = [r for r in self.unpriced
                 if self._is_a_real_number(r.get("time_horizon_adj"))
                 and r["time_horizon_adj"] == 0.0]
        self.assertTrue(zeros)


if __name__ == "__main__":
    unittest.main()
