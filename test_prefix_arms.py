"""#276. The third duplicate detector: arms whose whole pick sequence is a prefix of another's.

The defect these pin is not hypothetical. `#271` published a six-arm bench ladder as six
independent nulls; `#276` found the six were one 408-pick draft sampled at six lengths, and the
two existing detectors could not see it by construction. These tests hold that shape visible.

Each test states what it would catch. A test that cannot fail is worse than no test (#38).
"""
from __future__ import annotations

import unittest

import draft_battery as db


class PrefixArmsFindsNestedEvidence(unittest.TestCase):
    def test_the_276_shape_is_reported(self):
        """The real case: strictly growing sequences from one draft, sampled at six lengths."""
        full = [f"p{i}" for i in range(408)]
        seqs = {f"BN{n}": full[:n] for n in (168, 216, 264, 312, 360, 408)}
        found = {r["label"]: r["prefix_of"] for r in db.prefix_arms(seqs)}
        # Five of six are contained; the longest contains and is contained by nothing.
        self.assertEqual(len(found), 5)
        self.assertNotIn("BN408", found)
        for label in ("BN168", "BN216", "BN264", "BN312", "BN360"):
            self.assertEqual(found[label], "BN408",
                             "each nested arm should name the LONGEST container, not any container")

    def test_independent_arms_are_not_flagged(self):
        """Two real leagues that share an opening run but then diverge are independent evidence.

        Catches a detector that used "shares a long opening" instead of STRICT PREFIX -- the
        calibrated-threshold version this docstring's sibling in draft_battery.py rejects.
        """
        a = [f"p{i}" for i in range(50)]
        b = a[:40] + [f"q{i}" for i in range(10)]
        self.assertEqual(db.prefix_arms({"A": a, "B": b}), [])

    def test_equal_length_identical_arms_are_left_to_duplicate_arms(self):
        """Reporting one collapse from two detectors would double-count it."""
        a = [f"p{i}" for i in range(30)]
        self.assertEqual(db.prefix_arms({"A": list(a), "B": list(a)}), [])

    def test_container_is_the_longest_not_the_first_found(self):
        """Catches a detector that stops at the first container it meets.

        Iteration order would otherwise decide the answer, which makes the report depend on dict
        ordering rather than on the evidence.
        """
        seqs = {"short": ["a", "b"], "mid": ["a", "b", "c"], "long": ["a", "b", "c", "d"]}
        found = {r["label"]: r["prefix_of"] for r in db.prefix_arms(seqs)}
        self.assertEqual(found["short"], "long")
        self.assertEqual(found["mid"], "long")

    def test_empty_and_single_arm_inputs_are_not_errors(self):
        self.assertEqual(db.prefix_arms({}), [])
        self.assertEqual(db.prefix_arms({"only": [1, 2, 3]}), [])

    def test_row_carries_both_lengths_so_the_report_can_say_how_much_was_reused(self):
        """A bare label pair cannot tell a reader that 168 of 408 picks were the whole arm."""
        full = [f"p{i}" for i in range(100)]
        row = db.prefix_arms({"small": full[:25], "big": full})[0]
        self.assertEqual((row["picks"], row["container_picks"]), (25, 100))

    def test_an_arm_is_never_its_own_container(self):
        full = [f"p{i}" for i in range(10)]
        self.assertEqual([r["label"] for r in db.prefix_arms({"x": full})], [])


class PrefixArmsAgreesWithTheRealRecordedBattery(unittest.TestCase):
    """Run against the committed depth-battery evidence, not a fixture built to pass.

    This is the test that would have caught #276 before it was published.
    """

    def test_the_committed_depth_battery_ladder_is_nested(self):
        import json
        from pathlib import Path
        path = Path("evidence/mode_boundary/depth_battery.json")
        if not path.exists():                      # evidence file is not a code dependency
            self.skipTest("depth_battery.json not present")
        arms = json.loads(path.read_text())["arms"]
        seqs = {}
        for label, entry in arms.items():
            rule = entry["rules"].get("crossing")
            if rule is None:
                continue
            flat = [(e["pick_no"], e["pid"])
                    for picks in rule["per_seat"].values() for e in picks]
            flat.sort()
            seqs[label] = [pid for _, pid in flat]
        nested = {r["label"] for r in db.prefix_arms(seqs)}
        ladder = {"12T_ppr_BN6", "12T_ppr_BN10", "12T_ppr_BN14", "12T_ppr_BN22"}
        self.assertTrue(ladder <= nested,
                        f"the #276 bench ladder must be reported as nested; got {sorted(nested)}")
        # Different team counts are genuinely different drafts and must NOT be flagged.
        for label in ("8T_ppr_BN18", "10T_ppr_BN18", "14T_ppr_BN18"):
            self.assertNotIn(label, nested,
                             f"{label} is a different league, not a truncation")


if __name__ == "__main__":
    unittest.main()
