"""#201: the battery certifies the engine, so it must draft from the universe the engine gets.

`run_draft_battery.build_players_db` reconstructed every player from the VENDOR projections
table -- first initial, surname, position, team. That table has no health column, so every
player in it carried `injury_status: None`, `risk_adj` was 0.00 for all of them, and the
battery's whole life was spent certifying a board with no health signal on it.

HOW IT WAS FOUND, because the shape of the discovery is the argument for this test. A four-arm
risk_adj ablation came back "0 players moved" in every arm -- a clean, plausible null result.
It was not a null result: the status counter on the board was EMPTY. Nothing had been ablated
because nothing was there. A null finding and an unexercised instrument are indistinguishable
from the outside, and only naming the population apart tells them apart (the measurement skill's
own rule: print `n`, and if ON and OFF are identical, find out why before concluding).

WHAT ELSE WAS UNEXERCISED, not just risk_adj: `fantasy_positions` was a single-element list per
player, so #172's multi-position eligibility could not fire; `years_exp` and `status` were absent
entirely, so #193's rookie and not-currently-playing admission clauses were never reached.
Every battery arm's claim about those is a claim about a pool that could not express them.

THE OLD BUILDER IS KEPT, NOT DELETED. run_demand_reach_audit.py recorded its results against
that pool, and silently re-pointing it at a different universe would make a recorded experiment
describe something else under the same name -- the hazard test_measurement_script_boundary
enforces for RISK_ADJ. It keeps its name and gains a docstring saying what it cannot express.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import ast
import json
import os
import tempfile
import unittest
from pathlib import Path

import run_draft_battery as rdb

_HERE = os.path.dirname(os.path.abspath(__file__))


class TheBatteryDraftsFromTheRealUniverseTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.players, cls.provenance = rdb.build_players_db_from_capture()

    def test_the_pool_carries_a_health_signal_at_all(self):
        """The one property whose absence made every previous battery arm health-blind."""
        statuses = {info.get("injury_status") for info in self.players.values()}
        self.assertTrue(statuses - {None},
                        "the battery pool has no injury_status on any player -- #201, again")

    def test_it_carries_the_designations_the_engine_actually_prices(self):
        present = set(self.provenance["injury_statuses_present"])
        self.assertIn("IR", present)
        # And the ones #202 says have no RISK_ADJ entry are present too, which is what makes
        # that item measurable at all rather than a claim about a pool nobody drafted from.
        self.assertIn("PUP", present)

    def test_it_carries_the_other_fields_that_were_never_exercised(self):
        sample = next(iter(self.players.values()))
        for field in ("fantasy_positions", "years_exp", "status", "team"):
            with self.subTest(field=field):
                self.assertIn(field, sample)

    def test_multi_position_players_exist_in_it(self):
        # #172 cannot fire on a pool where every fantasy_positions list has one element.
        multi = [p for p in self.players.values() if len(p.get("fantasy_positions") or []) > 1]
        self.assertGreater(len(multi), 0)


class TheOldBuilderIsTheContrastNotTheDefaultTests(unittest.TestCase):
    """Non-vacuity for everything above: the two builders must genuinely differ, or the repair
    is decoration."""

    def test_the_vendor_reconstruction_still_has_no_health_signal(self):
        import data_merger as dm
        players = rdb.build_players_db(dm.DataMerger())
        statuses = {info.get("injury_status") for info in players.values()}
        self.assertEqual(statuses - {None}, set(),
                         "if the old builder now carries status, this test's premise is stale")

    def test_the_battery_entry_point_uses_the_CAPTURE_builder(self):
        """Statically, so a revert cannot pass quietly. The unit tests above would all still
        pass if main() went back to the reconstruction -- they exercise the function, not the
        wiring, and that gap is exactly how the original defect survived."""
        with open(os.path.join(_HERE, "run_draft_battery.py"), encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        main = next(n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        called = {n.func.id for n in ast.walk(main)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        self.assertIn("build_players_db_from_capture", called)
        self.assertNotIn("build_players_db", called)


class AMissingCaptureIsLoudTests(unittest.TestCase):

    def test_it_raises_rather_than_falling_back(self):
        """No silent fallback, deliberately. Degrading to the reconstruction is precisely how
        this stayed invisible: the battery went on emitting plausible reports about a universe
        nobody had chosen."""
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with self.assertRaises(FileNotFoundError):
                rdb.build_players_db_from_capture(path=missing)


class TheRunRecordsWhichUniverseItUsedTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _, cls.provenance = rdb.build_players_db_from_capture()

    def test_the_provenance_names_the_source_and_its_date(self):
        for field in ("source", "captured_at", "players_in_capture", "players_in_pool"):
            with self.subTest(field=field):
                self.assertIsNotNone(self.provenance.get(field))

    def test_the_report_carries_the_universe_block(self):
        """A battery is a dated measurement against a dated pool. #201 is what happens when
        that goes unrecorded, so the report says it."""
        with open(os.path.join(_HERE, "run_draft_battery.py"), encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source)
        # Scans main AND the report builder it delegates to. #213b moved the report dict out
        # of main into _battery_report so the mid-run and end-of-run writes share one shape;
        # a scan pinned to main alone then found an empty set and reported the universe block
        # missing when it had simply moved.
        owners = [n for n in tree.body
                  if isinstance(n, ast.FunctionDef) and n.name in ("main", "_battery_report")]
        self.assertTrue(owners, "neither main nor _battery_report was found")
        keys = set()
        for owner in owners:
          for node in ast.walk(owner):
            if isinstance(node, ast.Dict):
                keys |= {k.value for k in node.keys
                         if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        self.assertIn("universe", keys)


# MUTATIONS -- each applied, this file re-run, the named test observed to FAIL, then reverted:
#   1. build_players_db_from_capture strips injury_status from each row
#        -> TheBatteryDraftsFromTheRealUniverse.test_the_pool_carries_a_health_signal_at_all FAILED
#   2. main() reverted to build_players_db(merger)
#        -> TheOldBuilderIsTheContrastNotTheDefault.test_the_battery_entry_point_uses... FAILED
#      (and NOTHING else failed -- which is the whole reason that test is static)
#   3. build_players_db_from_capture falls back to {} instead of raising on a missing file
#        -> AMissingCaptureIsLoud.test_it_raises_rather_than_falling_back FAILED
#   4. the "universe" key dropped from the report dict
#        -> TheRunRecordsWhichUniverseItUsed.test_the_report_carries_the_universe_block FAILED
#   5. build_players_db (old) given a synthetic injury_status
#        -> TheOldBuilderIsTheContrastNotTheDefault.test_the_vendor_reconstruction_still... FAILED
if __name__ == "__main__":
    unittest.main()
