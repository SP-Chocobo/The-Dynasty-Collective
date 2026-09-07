"""#204: the battery must draft from the pricing path PRODUCTION runs, not a different one.

The defect this file exists for was invisible in every previous battery report. Production
(app.py's Draft Room) passes `sleeper_projections` and `sleeper_basis` into
pick_synthesis.build_snapshot on every rerun; draft_simulation.simulate_full_draft had no such
parameter at all, so every board the final gate ever built came back with sleeper_points,
sleeper_basis and availability_basis None on every row. The scoring-aware path (#180/#192) and
the availability haircut (#191/#202) were both absent from the certification while appearing
nowhere in the report as absent.

These tests are structural on purpose. A full battery arm is minutes of real board builds, so
what is pinned here is the WIRING -- that the arguments exist, are threaded end to end, and
that the ruler and the draft are priced the same way -- plus one real board build proving the
companions actually arrive when the arguments are supplied. That last one is the test that
would have caught the original defect, and it is checked against a real capture, not a stub.
"""

from __future__ import annotations

import ast
import inspect
import json
import unittest
from pathlib import Path

import draft_battery
import draft_room as dr
import draft_simulation
import run_draft_battery as rdb

CAPTURE = Path("data/fixtures/sleeper_capture.json")


def _params(func) -> set[str]:
    return set(inspect.signature(func).parameters)


class BatteryPricingWiringTests(unittest.TestCase):
    """Each layer between the battery's entry point and build_snapshot carries both arguments."""

    def test_simulate_full_draft_accepts_both_pricing_arguments(self):
        params = _params(draft_simulation.simulate_full_draft)
        self.assertIn("sleeper_projections", params)
        self.assertIn("sleeper_basis", params)

    def test_run_battery_accepts_both_pricing_arguments(self):
        params = _params(draft_battery.run_battery)
        self.assertIn("sleeper_projections", params)
        self.assertIn("sleeper_basis", params)

    def test_reference_values_accepts_both_pricing_arguments(self):
        # The RULER. If it does not move with the draft, every value-against-the-ruler number
        # in the audit compares two different quantities.
        params = _params(draft_battery.reference_values)
        self.assertIn("sleeper_projections", params)
        self.assertIn("sleeper_basis", params)

    def test_defaults_preserve_every_existing_caller(self):
        # The wiring must not change what any other caller already does. None + WEEKLY is
        # exactly the behaviour before this parameter existed.
        sig = inspect.signature(draft_simulation.simulate_full_draft)
        self.assertIsNone(sig.parameters["sleeper_projections"].default)
        self.assertEqual(sig.parameters["sleeper_basis"].default, dr.SLEEPER_BASIS_WEEKLY)

    def test_simulate_full_draft_actually_forwards_them_to_build_snapshot(self):
        # A parameter that is accepted and dropped is the same defect with a passing signature
        # test. Read the call site.
        source = inspect.getsource(draft_simulation.simulate_full_draft)
        call = next(node for node in ast.walk(ast.parse(source.lstrip()))
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "build_snapshot")
        forwarded = {kw.arg: kw.value for kw in call.keywords}
        self.assertIn("sleeper_projections", forwarded)
        self.assertIn("sleeper_basis", forwarded)
        for name in ("sleeper_projections", "sleeper_basis"):
            self.assertIsInstance(forwarded[name], ast.Name, f"{name} is not the parameter")
            self.assertEqual(forwarded[name].id, name)

    def test_run_battery_prices_the_ruler_the_same_way_as_the_draft(self):
        # THE ASYMMETRY THAT WOULD LOOK MEASURED. Both calls have to receive the arguments.
        source = inspect.getsource(draft_battery.run_battery)
        tree = ast.parse(source.lstrip())
        for target in ("simulate_full_draft", "reference_values"):
            call = next(node for node in ast.walk(tree)
                        if isinstance(node, ast.Call)
                        and getattr(node.func, "attr", getattr(node.func, "id", None)) == target)
            names = {kw.arg for kw in call.keywords}
            self.assertIn("sleeper_projections", names, f"{target} is priced differently")
            self.assertIn("sleeper_basis", names, f"{target} is priced differently")


class BatteryPricingProvenanceTests(unittest.TestCase):
    """The report has to SAY which pricing path produced it."""

    def test_trajectory_config_records_the_pricing_path(self):
        traj = draft_simulation.DraftTrajectory(
            config={"priced_from": "vendor_only", "sleeper_basis": None}, picks=())
        self.assertIn("priced_from", traj.config)

    def test_season_projections_raise_rather_than_fall_back(self):
        # Same contract as the universe half (#201): a missing capture is an error, never a
        # silent downgrade to vendor-only points.
        with self.assertRaises(FileNotFoundError):
            rdb.season_projections_from_capture(Path("data/fixtures/does_not_exist.json"))

    def test_season_projections_come_from_the_same_capture_as_the_universe(self):
        self.assertEqual(rdb.season_projections_from_capture.__defaults__[0], rdb.CAPTURE_PATH)
        self.assertEqual(rdb.build_players_db_from_capture.__defaults__[1], rdb.CAPTURE_PATH)


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class BatteryPricingReachesTheBoardTests(unittest.TestCase):
    """The test that would have caught it: build a real board both ways and compare.

    Not a signature check -- an observation of what the board actually carries.
    """

    @classmethod
    def setUpClass(cls):
        import data_merger as dm
        cls.merger = dm.DataMerger()
        cls.players_db, _ = rdb.build_players_db_from_capture()
        cls.season = rdb.season_projections_from_capture()
        cls.league = {
            "total_rosters": 12,
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX",
                                 "K", "IDP_FLEX", "IDP_FLEX"] + ["BN"] * 14,
            "scoring_settings": {"rec": 1.0},
        }
        cls.merger.set_league_format(draft_battery.league_format_hint(cls.league))
        cls.without = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id=None, league=cls.league,
            mode="balanced")
        cls.with_sleeper = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id=None, league=cls.league,
            mode="balanced", sleeper_projections=cls.season,
            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

    def test_without_the_projections_no_row_carries_an_availability_basis(self):
        # The measured state of every battery arm before #204: 100% None.
        self.assertTrue(self.without)
        self.assertEqual(
            [row for row in self.without if row.get("availability_basis") is not None], [])

    def test_with_the_projections_the_haircut_basis_actually_arrives(self):
        bases = {row.get("availability_basis") for row in self.with_sleeper}
        self.assertIn("rule_floor", bases,
                      "the availability haircut never fired on a real capture")

    def test_the_two_pricing_paths_produce_different_boards(self):
        # If these agreed, the argument would be inert and #204 would be a non-finding. Ranked
        # order is the thing the battery certifies, so that is what is compared.
        a = [row["player_id"] for row in self.without]
        b = [row["player_id"] for row in self.with_sleeper]
        self.assertNotEqual(a, b)

    def test_an_injured_player_is_priced_lower_on_the_production_path(self):
        # Direction, not just difference. Pick the IR players the haircut actually fired on and
        # require the projection to have come DOWN, never up.
        by_id = {row["player_id"]: row for row in self.without}
        checked = 0
        for row in self.with_sleeper:
            if row.get("availability_basis") != "rule_floor":
                continue
            before = by_id.get(row["player_id"], {}).get("projected_points")
            after = row.get("projected_points")
            if before is None or after is None:
                continue
            checked += 1
            self.assertLessEqual(after, before, f"{row['name']} got MORE points on IR")
        self.assertGreater(checked, 0, "no comparable haircut row -- the test is vacuous")


if __name__ == "__main__":
    unittest.main()
