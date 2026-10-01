"""#206: the code CLAIMS survival is uncalibrated. This checks the claim against the evidence.

`pick_synthesis.SURVIVAL_IS_CALIBRATED = False` gates a user-facing state off, and the comment
above it cites Brier scores from two committed evidence files. A hand-written comment citing
numbers in a file it never reads is exactly how prose drifts away from the thing it describes
-- this repo has found that pattern repeatedly. So the declaration is DERIVED-CHECKED here:
the flag must agree with what the evidence actually says, and the evidence must still exist,
still be complete, and still have a sound scorer.

If someone flips the flag, this test decides whether they were entitled to.
"""
import json
import unittest
from pathlib import Path

import pick_synthesis as ps


class SurvivalCalibrationDeclarationTests(unittest.TestCase):
    def _arms(self):
        for name, rel in ps.SURVIVAL_CALIBRATION_EVIDENCE.items():
            path = Path(rel)
            self.assertTrue(path.exists(), f"{name} evidence is missing: {rel}")
            yield name, rel, json.loads(path.read_text())

    def test_both_cited_evidence_files_exist_and_are_complete_runs(self):
        """A partial run is instrument state, not a result. The declaration may not rest on
        one -- both arms checkpoint mid-run with complete:false."""
        seen = 0
        for name, rel, d in self._arms():
            self.assertTrue(d.get("complete"), f"{name} ({rel}) is a mid-run checkpoint")
            seen += 1
        self.assertEqual(seen, 2, "the declaration should cite both arms, not one")

    def test_every_arm_has_a_sound_scorer_before_its_verdict_is_believed(self):
        """The oracle control predicts the truth and must score exactly 0.0. If it does not,
        the arm's engine/constant comparison is noise and cannot justify the flag either way."""
        for name, _, d in self._arms():
            self.assertEqual(d["control_oracle"]["brier"], 0.0,
                             f"{name}: oracle is not 0.0, so this arm proves nothing")

    def test_the_flag_agrees_with_what_the_evidence_says(self):
        """THE ACTUAL CLAIM. SURVIVAL_IS_CALIBRATED must be False while any arm reports the
        engine losing to the constant predictor, and must not be False once none does."""
        losing = [name for name, _, d in self._arms() if not d.get("beats_constant")]
        if losing:
            self.assertFalse(
                ps.SURVIVAL_IS_CALIBRATED,
                f"SURVIVAL_IS_CALIBRATED is True but {sorted(losing)} still report the engine "
                "losing to a constant predictor -- the flag asserts something the committed "
                "evidence contradicts")
        else:
            self.assertTrue(
                ps.SURVIVAL_IS_CALIBRATED,
                "every arm now reports the engine beating the constant, so the gate is "
                "suppressing a signal that has earned its way back -- re-examine "
                "DECISIVE_SURVIVAL_THRESHOLD and flip the flag deliberately")

    def test_the_population_behind_each_verdict_is_not_vacuous(self):
        """A Brier comparison over a handful of pairs is not evidence. Print-the-n, applied to
        the numbers the declaration rests on."""
        for name, _, d in self._arms():
            self.assertGreater(d["engine"]["n"], 1000,
                               f"{name} scored only {d['engine']['n']} pairs")
            self.assertEqual(d.get("exclusions", {}).get("unmeasured", 0)
                             if "exclusions" in d else d.get("unmeasured_excluded", 0),
                             0, f"{name} silently dropped unmeasured pairs")

    def test_the_declared_threshold_sits_in_the_band_the_evidence_calls_worst(self):
        """WHY the flag is False, not merely THAT it is. DECISIVE_SURVIVAL_THRESHOLD reads the
        bottom of the distribution, and that is where the engine is least trustworthy -- the
        bucket containing the threshold observes a rate far above what it predicts."""
        real = json.loads(Path(ps.SURVIVAL_CALIBRATION_EVIDENCE["real"]).read_text())
        bucket = next(r for r in real["engine"]["curve"]
                      if r["n"] and r["predicted_mean"] is not None
                      and r["predicted_mean"] <= ps.DECISIVE_SURVIVAL_THRESHOLD)
        self.assertGreater(
            bucket["observed_rate"], bucket["predicted_mean"] * 3,
            "the band the threshold reads is no longer wildly miscalibrated -- the stated "
            "reason for the gate has gone stale even if the overall verdict has not")


if __name__ == "__main__":
    unittest.main()
