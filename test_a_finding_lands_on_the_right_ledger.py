"""V4-I1: a finding from an arm with no engine seat is not evidence about a strategy.

`run_vds_battery`'s report said in a comment that it skipped those arms. It did not. The guard
read `row["sharp_seats"]`, the value lives at `opponent_noise.sharp_seats` in the MATRIX, and the
serialized row carries no such key -- so the read always returned its truthy default and the guard
could not fire. `by_strategy_effective` never had the guard at all. When it was found, `noisy_k8`
held 16 of a run's 19 findings and every one was credited to it as a strategy property.

EVERY EXPECTATION HERE IS ASKED OF `vds_matrix`, NEVER WRITTEN AS A LITERAL. A hardcoded
`{"noisy_k3", "noisy_k8"}` would pass against the broken code the day someone renames a strategy,
and the whole defect class this cycle was about is an expectation that agrees with the bug.

Answers to `#126` (one home for the rule -- the matrix declares which arms use an engine seat, and
the report asks it rather than re-expressing it), `#166` (the row was never given the companion
needed to judge it, which is why the guard read an address that was never populated), and `#254`
(a guard that catches nothing is not a guard -- the tests below assert it FIRES, and that it still
credits an engine strategy, so it discriminates rather than zeroing the ledger).
"""
from __future__ import annotations

import unittest

import run_vds_battery as rvb
import vds_battery


def _no_engine_strategies() -> set:
    """The strategies the matrix says use no engine seat. The authority, asked rather than recalled."""
    return {arm["label"].partition("__")[2] for arm in vds_battery.vds_matrix()
            if not (arm.get("opponent_noise") or {}).get("sharp_seats", ["present"])}


def _arm(label, findings, picks):
    fmt, _, strategy = label.partition("__")
    return {"label": label, "format": fmt, "strategy": strategy,
            "findings": [{"kind": f} for f in findings], "pick_sequence": picks}


class TheGuardHasSomethingToGuard(unittest.TestCase):
    """NON-VACUITY. Every assertion below is empty if the matrix has no no-engine arm."""

    def test_the_matrix_declares_arms_with_no_engine_seat(self):
        arms = [a["label"] for a in vds_battery.vds_matrix()
                if not (a.get("opponent_noise") or {}).get("sharp_seats", ["present"])]
        self.assertTrue(arms, "no arm sets `sharp_seats: []`; this whole module is vacuous")
        self.assertTrue(_no_engine_strategies())

    def test_some_arms_do_use_the_engine(self):
        """The inverse vacuity: a guard that excludes EVERY arm is not a guard either (`#254`)."""
        total = len(vds_battery.vds_matrix())
        no_engine = sum(1 for a in vds_battery.vds_matrix()
                        if not (a.get("opponent_noise") or {}).get("sharp_seats", ["present"]))
        self.assertGreater(no_engine, 0)
        self.assertLess(no_engine, total, "every arm is no-engine; the report would attribute nothing")


class AFindingFromANoEngineArmIsOffEveryStrategyLedger(unittest.TestCase):
    """The repair. Asked of a report built from a fixture whose shape mirrors a real run."""

    def setUp(self):
        matrix = [a["label"] for a in vds_battery.vds_matrix()]
        labels = set(matrix)
        no_eng = _no_engine_strategies()

        def engine_strategies(fmt):
            return [lbl.partition("__")[2] for lbl in matrix
                    if lbl.partition("__")[0] == fmt
                    and lbl.partition("__")[2] not in no_eng
                    and lbl.partition("__")[2] != vds_battery.CONTROL_STRATEGY]

        # ONE FORMAT CARRYING ALL THREE KINDS: a control, a second engine strategy, and a
        # no-engine arm. Chosen from the matrix so the fixture cannot describe a shape no run has.
        self.fmt = next(f for f in sorted({lbl.partition("__")[0] for lbl in matrix})
                        if any(f"{f}__{s}" in labels for s in no_eng)
                        and f"{f}__{vds_battery.CONTROL_STRATEGY}" in labels
                        and engine_strategies(f))
        self.no_eng_strategy = next(s for s in sorted(no_eng) if f"{self.fmt}__{s}" in labels)
        self.engine_strategy = engine_strategies(self.fmt)[0]

    def _report(self, no_engine_row_claims_sharp_seats=False):
        no_eng = _arm(f"{self.fmt}__{self.no_eng_strategy}", ["unfilled_starting_slots"], ["x"])
        if no_engine_row_claims_sharp_seats:
            # the row LYING about it must not change the verdict: the matrix is the authority
            no_eng["sharp_seats"] = ["present"]
        results = [
            _arm(f"{self.fmt}__{vds_battery.CONTROL_STRATEGY}", [], ["c"]),
            _arm(f"{self.fmt}__{self.engine_strategy}", ["unfieldable_depth"], ["e"]),
            no_eng,
        ]
        return rvb._report({}, results, 0.0, complete=True)

    def test_the_no_engine_strategy_is_credited_zero(self):
        rep = self._report()
        self.assertEqual(rep["findings_by_strategy_effective"][self.no_eng_strategy], 0)

    def test_the_engine_strategy_is_still_credited(self):
        """Proves the guard discriminates instead of zeroing the whole ledger."""
        rep = self._report()
        self.assertEqual(rep["findings_by_strategy_effective"][self.engine_strategy], 1)

    def test_the_finding_is_not_hidden_only_re_addressed(self):
        """Dropping it from the total would trade a false attribution for a false total."""
        rep = self._report()
        self.assertEqual(rep["findings_total"], 2)
        self.assertEqual(rep["findings_in_no_engine_arms"], 1)
        self.assertIn(f"{self.fmt}__{self.no_eng_strategy}", rep["NO_ENGINE_ARMS"])

    def test_the_no_engine_strategy_is_not_called_strategy_specific(self):
        rep = self._report()
        named = rep["STRATEGY_SPECIFIC_FINDINGS"].get(self.fmt, [])
        self.assertNotIn(self.no_eng_strategy, named)

    def test_a_row_claiming_sharp_seats_does_not_overrule_the_matrix(self):
        """THE DEFECT, EXACTLY. The old guard believed the row; the row never carried the key."""
        rep = self._report(no_engine_row_claims_sharp_seats=True)
        self.assertEqual(rep["findings_by_strategy_effective"][self.no_eng_strategy], 0)
        self.assertEqual(rep["findings_in_no_engine_arms"], 1)

    def test_every_strategy_that_ran_still_has_a_key(self):
        """An absent key and a zero are different claims (`#187`)."""
        rep = self._report()
        for strategy in (self.no_eng_strategy, self.engine_strategy,
                         vds_battery.CONTROL_STRATEGY):
            self.assertIn(strategy, rep["findings_by_strategy_effective"])


if __name__ == "__main__":
    unittest.main()
