"""The VDS battery's matrix contract -- the part that must stay fast.

The RUN is an instrument (36 real drafts, hours). What belongs in the suite is what would make a
run meaningless before it starts: a matrix missing the format the battery exists for, two
"different" strategies that are the same dict, or a control arm that is not the shipped behaviour.

The battery's own headline finding, measured before its first full run, is that a strategy can be
listed, forwarded, and exercise NOTHING -- `sharp_balanced` and `crossing` reproduced the control
byte-for-byte on an 8-round format. That cannot be asserted here (it needs real drafts), so what is
asserted here is that the detector for it exists and is wired.
"""

from __future__ import annotations

import unittest

import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb
import vds_battery as vds


class MatrixShapeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scoring = rdb.scoring_settings_from_capture()
        cls.matrix = vds.vds_matrix(cls.scoring)

    def test_every_format_crossed_with_every_strategy(self):
        self.assertEqual(len(self.matrix), len(vds.FORMATS) * len(vds.STRATEGIES))

    def test_the_control_strategy_is_in_the_sweep(self):
        """A battery without a control reports absolute numbers nobody can calibrate."""
        self.assertIn(vds.CONTROL_STRATEGY, vds.STRATEGIES)

    def test_the_control_is_the_SHIPPED_behaviour(self):
        """If the control drifts from what production does, every other arm is read against a
        baseline nobody runs -- which is the #28 mistake (a board no caller builds) in a
        battery."""
        control = vds.STRATEGIES[vds.CONTROL_STRATEGY]
        self.assertEqual(control["mode"], "auto")
        self.assertEqual(control["upside_rule"], dr.UPSIDE_RULE_ROUND)
        self.assertIsNone(control["opponent_noise"])

    def test_no_two_strategies_are_the_same_configuration(self):
        """Two identically-configured strategies would be one arm counted twice -- the duplicate
        problem the format battery already detects, caught here at matrix level where it is free."""
        seen = {}
        for name, config in vds.STRATEGIES.items():
            key = repr(sorted(config.items(), key=lambda kv: kv[0]))
            self.assertNotIn(key, seen,
                             f"{name} is configured identically to {seen.get(key)}")
            seen[key] = name

    def test_the_K_DEF_format_is_present(self):
        """The battery was asked for because of the K/DST take pattern. A sweep that dropped that
        format would be a clean report about everything except the reason it was run."""
        self.assertIn("12T_ppr_K_DEF", vds.FORMATS)

    def test_the_superflex_format_is_present(self):
        """#22 regressed superflex QB specifically, and the format battery missed it."""
        self.assertIn("12T_ppr_SF", vds.FORMATS)

    def test_arms_carry_the_axes_the_simulator_reads(self):
        for arm in self.matrix:
            with self.subTest(arm=arm["label"]):
                self.assertIn("mode", arm)
                self.assertIn("upside_rule", arm)
                self.assertIn("opponent_noise", arm)

    def test_every_format_resolves_to_a_real_league(self):
        """Non-vacuity: leagues come FROM league_matrix, never rebuilt here. #248 is what a
        hand-rebuilt capture costs."""
        for arm in self.matrix:
            with self.subTest(arm=arm["label"]):
                self.assertTrue(arm["league"].get("roster_positions"))
                self.assertGreater(arm["teams"], 0)

    def test_a_missing_format_is_REFUSED_rather_than_skipped(self):
        """A VDS run that quietly dropped the superflex format would report a clean strategy
        sweep while omitting the arm the battery exists for."""
        real = dict(vds.FORMATS)
        try:
            vds.FORMATS["NOT_A_REAL_FORMAT"] = "planted"
            with self.assertRaises(ValueError) as caught:
                vds.vds_matrix(self.scoring)
            self.assertIn("NOT_A_REAL_FORMAT", str(caught.exception))
        finally:
            vds.FORMATS.clear()
            vds.FORMATS.update(real)


class TheNoisyArmsAreSeededTests(unittest.TestCase):
    """A noisy arm without a recorded seed is not reproducible, and draft_simulation's docstring
    forbids substituting randomness for what should vary between trials."""

    def test_every_noisy_strategy_carries_a_seed(self):
        for name, config in vds.STRATEGIES.items():
            noise = config["opponent_noise"]
            if noise is not None:
                with self.subTest(strategy=name):
                    self.assertIn("seed", noise)
                    self.assertEqual(noise["seed"], vds.VDS_SEED)

    def test_the_swept_top_k_values_are_all_used(self):
        """#56: top_k must be SWEPT and reported across, never chosen. A constant declared in
        VDS_TOP_K but wired into no strategy would be a sweep that swept one value."""
        used = {c["opponent_noise"]["top_k"] for c in vds.STRATEGIES.values()
                if c["opponent_noise"] is not None}
        self.assertEqual(used, set(vds.VDS_TOP_K))


class TheArmLoopForwardsTheAxesTests(unittest.TestCase):
    """The VDS battery reuses draft_battery.run_battery rather than copying it (#126). That only
    works if the shared loop actually forwards the two axes the VDS arms carry -- otherwise every
    strategy arm silently drafts as the control and the report is six copies of one number."""

    def test_run_battery_forwards_upside_rule_and_opponent_noise(self):
        import inspect
        source = inspect.getsource(db.run_battery)
        self.assertIn('entry.get("upside_rule"', source)
        self.assertIn('entry.get("opponent_noise")', source)

    def test_the_format_matrix_carries_neither_so_its_arms_are_unchanged(self):
        """The extension must leave the format battery byte-identical to its committed runs."""
        for arm in db.league_matrix(rdb.scoring_settings_from_capture()):
            with self.subTest(arm=arm["label"]):
                self.assertNotIn("upside_rule", arm)
                self.assertNotIn("opponent_noise", arm)

    def test_the_arm_loop_carries_the_pick_sequence_for_inertness(self):
        """Inertness is DERIVED from what the draft did. Without the sequence the runner would
        have to assume a forwarded parameter had an effect -- which is the assumption that was
        false for two of six strategies."""
        import inspect
        self.assertIn("pick_sequence", inspect.getsource(db.run_battery))


if __name__ == "__main__":
    unittest.main()
