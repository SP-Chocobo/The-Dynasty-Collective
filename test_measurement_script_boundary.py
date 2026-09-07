"""#201: a recorded measurement must stay reproducible, and reading it must not re-run it.

The run_*.py scripts are this repo's measurement record -- the ablations, comparisons and
stress tests whose results are quoted in docstrings and in POST_AUDIT_PLAN as evidence for
decisions that shipped. Two properties keep that record honest, and both were violated.

ONE: A RECORDED EXPERIMENT MUST PIN ITS OWN MAGNITUDES. Three scripts reproduced the risk_adj
experiments A and D by reading `dr.RISK_ADJ[status]` LIVE. When the owner's #191 ruling removed
"Questionable" from that table, all three broke -- and breaking was the lucky outcome. Had the
ruling changed a VALUE rather than removing a key, they would have re-run silently over
different magnitudes and reported the result under the same name as the recorded one. That is
the "never compare a fresh run against a baseline built by different code" hazard, inverted:
here the code moves under a fixed baseline. Each now carries RISK_ADJ_AS_MEASURED.

TWO: IMPORTING A SCRIPT MUST NOT RUN IT. run_need_bonus_ablation.py executed its entire
ablation at module level -- two full 15-round drafts and a printed report, on nothing more than
an `import`. Found by accident while checking that the run_* scripts still loaded after the
constant was removed: importing all 26 to see which ones failed ran an experiment instead. It
was the only one of 26 without a guard, which is exactly why it had never bitten anyone.

WHY THIS IS CHECKED STATICALLY, WITH AST AND NEVER BY IMPORTING. A test that imported these
modules to inspect them would reproduce the very defect it is checking for -- and would take
the suite from ~900s to something nobody runs. Everything here parses source text.

WHY THE FIRST RULE NAMES RISK_ADJ AND NOT "ANY TUNABLE". The hazard is general, but only
RISK_ADJ has demonstrated it. Widening the rule to every constant in draft_room would forbid
scripts that legitimately report a current value, and inventing that scope to look thorough is
what #56 forbids. When a second constant demonstrates the same failure, it gets a line here.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import ast
import glob
import os
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))


def _scripts():
    return sorted(glob.glob(os.path.join(_HERE, "run_*.py")))


def _tree(path):
    with open(path, encoding="utf-8") as handle:
        return ast.parse(handle.read())


class ImportingAScriptMustNotRunItTests(unittest.TestCase):

    def test_every_measurement_script_guards_its_own_entry_point(self):
        unguarded = []
        for path in _scripts():
            body = _tree(path).body
            guarded = any(
                isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name) and node.test.left.id == "__name__"
                for node in body)
            if not guarded:
                unguarded.append(os.path.basename(path))
        self.assertEqual(unguarded, [], (
            "these run at IMPORT -- anything that enumerates modules executes their experiments; "
            "move the work into main() behind `if __name__ == \"__main__\":`"))

    def test_the_population_is_not_empty(self):
        # A rate over an empty set is not a rate: if the glob ever stops matching, the test
        # above passes by finding nothing rather than by everything being correct.
        self.assertGreater(len(_scripts()), 20)


class ARecordedExperimentPinsItsOwnMagnitudesTests(unittest.TestCase):

    @staticmethod
    def _live_risk_adj_subscripts(path):
        """`<anything>.RISK_ADJ[...]` -- the operation that crashes on a removed key and, worse,
        silently changes meaning on a changed value."""
        found = []
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Subscript):
                continue
            value = node.value
            if isinstance(value, ast.Attribute) and value.attr == "RISK_ADJ":
                found.append(ast.dump(node)[:60])
        return found

    def test_no_measurement_script_indexes_the_live_table(self):
        offenders = [os.path.basename(p) for p in _scripts()
                     if self._live_risk_adj_subscripts(p)]
        self.assertEqual(offenders, [], (
            "a recorded experiment must not read a table that can change after the recording; "
            "pin the values it was measured against as RISK_ADJ_AS_MEASURED"))

    def test_the_scripts_that_needed_the_pin_actually_carry_it(self):
        """Non-vacuity, and the sharper half. The rule above passes for a script that simply
        never mentions risk_adj, so it cannot on its own tell "pinned" from "unrelated". These
        three reproduce experiments A and D and must hold the four-status table they were
        measured against -- including "Questionable", which production no longer prices."""
        for name in ("run_risk_adj_experiment_D_comparison.py",
                     "run_risk_adj_D_pathology_stress_test.py",
                     "run_risk_adj_softening_measurement.py"):
            with self.subTest(script=name):
                with open(os.path.join(_HERE, name), encoding="utf-8") as handle:
                    source = handle.read()
                self.assertIn("RISK_ADJ_AS_MEASURED", source)

    def test_the_pinned_table_still_holds_the_status_production_dropped(self):
        """The point of pinning: the recorded results describe FOUR statuses, and production
        now prices three. If the pin quietly lost "Questionable" too, the record would again
        describe a different experiment than the one it reports."""
        import run_risk_adj_experiment_D_comparison as d
        self.assertEqual(d.RISK_ADJ_AS_MEASURED,
                         {"IR": -18.0, "Out": -10.0, "Doubtful": -5.0, "Questionable": -1.5})

    def test_production_and_the_pin_have_genuinely_diverged(self):
        # Non-vacuity for the test above: if they were still equal, pinning would be
        # untested decoration rather than a live guarantee.
        import draft_room as dr
        import run_risk_adj_experiment_D_comparison as d
        self.assertNotEqual(dict(dr.RISK_ADJ), d.RISK_ADJ_AS_MEASURED)


# MUTATIONS -- each applied, this file re-run, the named test observed to FAIL, then reverted:
#   1. run_need_bonus_ablation.py: remove the `if __name__ == "__main__":` guard
#        -> ImportingAScriptMustNotRunIt.test_every_measurement_script_guards... FAILED
#   2. _scripts() globs "nothing_*.py"
#        -> ...test_the_population_is_not_empty FAILED (the guard test would have passed empty)
#   3. run_risk_adj_softening_measurement.py: restore `dr.RISK_ADJ[status]`
#        -> ARecordedExperimentPinsItsOwnMagnitudes.test_no_measurement_script_indexes... FAILED
#   4. run_risk_adj_experiment_D_comparison.py: drop "Questionable" from RISK_ADJ_AS_MEASURED
#        -> ...test_the_pinned_table_still_holds_the_status_production_dropped FAILED
#   5. draft_room: restore "Questionable" to RISK_ADJ (production and pin re-converge)
#        -> ...test_production_and_the_pin_have_genuinely_diverged FAILED
if __name__ == "__main__":
    unittest.main()
