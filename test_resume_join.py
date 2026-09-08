"""#215: a long instrument must be FINISHABLE, and a joined report must not overstate itself.

MEASURED THREE TIMES on 2026-09-08. The container is reclaimed on OPERATOR inactivity, not on
the job's -- a backgrounded run does not hold it open. Two full-depth roster proofs were killed
67s and 45s into their SIXTH format after 45 and 30 minutes of work; the 33-arm battery was
killed twice, most recently 8 arms in. #213b made the partial output SURVIVABLE. It did not make
the run FINISHABLE: each next process began again at unit one, and a ~3-hour battery cannot fit
inside the reclaim window at all.

The join is only sound because the instrument is deterministic, and that is MEASURED here rather
than asserted -- see TheJoinRestsOnMeasuredDeterminismTests, which reads the two committed
evidence reports and requires them to agree.
"""

from __future__ import annotations

import ast
import inspect
import json
import tempfile
import unittest
from pathlib import Path

import resume_join
import run_draft_battery as rdb
import run_roster_proof as rp

EVIDENCE = Path(__file__).resolve().parent / "evidence" / "roster_proof"
RUN_A = EVIDENCE / "ROSTER_PROOF_2026-09-08_realrules_5of6_ef98dd9.json"
RUN_B = EVIDENCE / "ROSTER_PROOF_2026-09-08_realrules_5of6_cf0b283.json"


def _write(payload) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    handle.write(payload if isinstance(payload, str) else json.dumps(payload))
    handle.close()
    return handle.name


class TheJoinRestsOnMeasuredDeterminismTests(unittest.TestCase):
    """Joining units across processes is legitimate ONLY if a re-run reproduces them.

    This is the load-bearing assumption of the whole item, so it is pinned to the two reports
    actually produced today rather than to a claim in a docstring."""

    def setUp(self):
        for path in (RUN_A, RUN_B):
            if not path.exists():
                self.skipTest(f"determinism evidence missing: {path.name}")
        self.a = json.loads(RUN_A.read_text(encoding="utf-8"))
        self.b = json.loads(RUN_B.read_text(encoding="utf-8"))

    def test_the_two_runs_were_produced_at_different_commits(self):
        """A join across identical commits would prove nothing about a join across a change."""
        self.assertNotEqual(self.a["commit"], self.b["commit"])

    def test_the_two_runs_measured_the_same_formats_in_the_same_order(self):
        self.assertEqual([f["label"] for f in self.a["formats"]],
                         [f["label"] for f in self.b["formats"]])
        self.assertGreaterEqual(len(self.a["formats"]), 5)

    def test_every_measured_number_agrees_between_the_two_runs(self):
        """Wall clock is allowed to differ. Nothing else is."""
        for left, right in zip(self.a["formats"], self.b["formats"]):
            for key in left:
                if key == "seconds":
                    continue
                self.assertEqual(left[key], right.get(key),
                                 f"{left['label']}.{key} differs between two runs -- the "
                                 f"instrument is not deterministic and units may NOT be joined")

    def test_the_agreement_reaches_the_per_seat_detail_not_just_the_aggregates(self):
        """#177's aggregates survived and its detail did not. An aggregate can agree while the
        seats underneath it disagree, so the comparison above has to be reaching real depth."""
        for left in self.a["formats"]:
            self.assertTrue(left.get("per_seat"), f"{left['label']} carries no per-seat detail")
            self.assertGreaterEqual(len(left["per_seat"]), 10)


class AResumeThatCannotReadThePriorFileRecomputesTests(unittest.TestCase):

    def test_a_missing_file_carries_nothing(self):
        self.assertEqual(resume_join.carry_forward("/nonexistent/x.json", ["a"],
                                                   units_key="formats"), [])

    def test_no_path_at_all_carries_nothing(self):
        self.assertEqual(resume_join.carry_forward("", ["a"], units_key="formats"), [])

    def test_a_file_truncated_mid_write_carries_nothing_instead_of_guessing(self):
        path = _write('{"commit": "abc", "formats": [{"label": "a"')
        self.assertEqual(resume_join.carry_forward(path, ["a"], units_key="formats"), [])

    def test_a_json_document_that_is_not_a_report_carries_nothing(self):
        self.assertEqual(resume_join.carry_forward(_write([1, 2, 3]), ["a"],
                                                   units_key="formats"), [])


class OnlyTheWantedUnitsAreCarriedTests(unittest.TestCase):

    def test_a_unit_this_run_did_not_ask_for_is_not_carried(self):
        path = _write({"commit": "abc",
                       "formats": [{"label": "a"}, {"label": "b"}]})
        got = resume_join.carry_forward(path, ["a"], units_key="formats")
        self.assertEqual([u["label"] for u in got], ["a"])

    def test_the_units_key_selects_which_list_is_joined(self):
        """The battery's arms live under `results`, the proof's formats under `formats`. One
        function, told which -- not two copies that can drift."""
        path = _write({"commit": "abc", "results": [{"label": "a"}], "formats": []})
        self.assertEqual(len(resume_join.carry_forward(path, ["a"], units_key="results")), 1)
        self.assertEqual(len(resume_join.carry_forward(path, ["a"], units_key="formats")), 0)

    def test_a_malformed_unit_is_skipped_rather_than_carried(self):
        path = _write({"commit": "abc", "formats": ["not a dict", {"label": "a"}]})
        got = resume_join.carry_forward(path, ["a"], units_key="formats")
        self.assertEqual([u["label"] for u in got], ["a"])


class NoUnitTravelsWithoutItsOwnProvenanceTests(unittest.TestCase):

    def test_a_carried_unit_is_marked_carried(self):
        path = _write({"commit": "abc", "formats": [{"label": "a"}]})
        got = resume_join.carry_forward(path, ["a"], units_key="formats")
        self.assertIs(got[0][resume_join.CARRIED], True)

    def test_a_unit_keeps_the_commit_that_produced_it_not_the_one_reading_it(self):
        path = _write({"commit": "newer",
                       "commits_present": ["older"],
                       "formats": [{"label": "a", resume_join.PRODUCED_AT: "older"}]})
        got = resume_join.carry_forward(path, ["a"], units_key="formats")
        self.assertEqual(got[0][resume_join.PRODUCED_AT], "older")

    def test_a_pre_215_report_lends_its_own_commit_because_it_cannot_be_a_join(self):
        """Nothing could resume INTO a report written before this module, so every unit in one
        came from the single process that wrote it, at the commit that process recorded."""
        path = _write({"commit": "abc", "formats": [{"label": "a"}]})
        got = resume_join.carry_forward(path, ["a"], units_key="formats")
        self.assertEqual(got[0][resume_join.PRODUCED_AT], "abc")

    def test_a_JOINED_report_refuses_to_lend_its_commit_to_an_unstamped_unit(self):
        """There the report-level commit describes the LAST process only, so lending it would
        be a false claim about every unit an earlier process computed."""
        path = _write({"commit": "abc",
                       "commits_present": ["abc", "def"],
                       "formats": [{"label": "a"}]})
        self.assertEqual(resume_join.carry_forward(path, ["a"], units_key="formats"), [])

    def test_the_carried_forward_key_alone_also_marks_a_report_as_joined(self):
        path = _write({"commit": "abc",
                       resume_join.CARRIED: ["b"],
                       "formats": [{"label": "a"}]})
        self.assertEqual(resume_join.carry_forward(path, ["a"], units_key="formats"), [])


class TheDocumentNamesEveryCommitThatContributedTests(unittest.TestCase):

    def test_commits_present_reports_each_contributing_commit_once(self):
        units = [{resume_join.PRODUCED_AT: "b"}, {resume_join.PRODUCED_AT: "a"},
                 {resume_join.PRODUCED_AT: "b"}]
        self.assertEqual(resume_join.commits_present(units), ["a", "b"])

    def test_an_unstamped_unit_contributes_no_commit_rather_than_a_null(self):
        self.assertEqual(resume_join.commits_present([{"label": "a"}]), [])

    def test_commits_present_of_nothing_is_empty(self):
        self.assertEqual(resume_join.commits_present(None), [])


class BothInstrumentsStampWhatTheyComputeTests(unittest.TestCase):
    """The stamp is written where the unit is BUILT. Asserted on the AST of the assignment, not
    on source text -- a docstring mentioning the key would satisfy a grep."""

    def _assigned_keys(self, func, var):
        tree = ast.parse(inspect.getsource(func))
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if var in names:
                    found.extend(
                        k.attr for k in node.value.keys
                        if isinstance(k, ast.Attribute))
        return found

    def test_the_proof_stamps_each_format_block_it_computes(self):
        keys = self._assigned_keys(rp.main, "block")
        self.assertIn("PRODUCED_AT", keys)
        self.assertIn("CARRIED", keys)

    def test_the_battery_stamps_each_arm_it_drafts(self):
        src = inspect.getsource(rdb.main)
        tree = ast.parse(src)
        stamped = {
            node.targets[0].slice.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and isinstance(node.targets[0], ast.Subscript)
            and isinstance(node.targets[0].value, ast.Name)
            and node.targets[0].value.id == "audited"
            and isinstance(node.targets[0].slice, ast.Attribute)
        }
        self.assertIn("PRODUCED_AT", stamped)
        self.assertIn("CARRIED", stamped)


class AResumedReportIsTheSameDocumentAsAFreshOneTests(unittest.TestCase):

    def test_the_proof_consumes_carried_blocks_in_spec_order(self):
        """Appending carried blocks first would reorder the document between two runs that
        measured the same thing -- a difference a reader would read as a real one."""
        src = inspect.getsource(rp.main)
        loop = src[src.index("for spec in specs:"):]
        self.assertIn('if spec["label"] in carried:', loop)
        self.assertLess(src.index("for spec in specs:"), src.index("carried[spec"))

    def test_the_battery_consumes_carried_arms_in_matrix_order(self):
        src = inspect.getsource(rdb.main)
        self.assertIn('if entry["label"] in carried:', src)
        self.assertLess(src.index("for entry in matrix:"), src.index('carried[entry["label"]]'))

    def test_the_proof_prints_a_carried_format_through_the_same_builder(self):
        src = inspect.getsource(rp.main)
        self.assertEqual(src.count("console_line(block)"), 2,
                         "a carried format must print through the same builder as a fresh one")

    def test_the_battery_prints_a_carried_arm_through_the_same_builder(self):
        src = inspect.getsource(rdb.main)
        self.assertEqual(src.count("_arm_line(audited)"), 2)

    def test_a_carried_line_is_marked_as_carried_on_the_console(self):
        for builder in (rp.console_line, rdb._arm_line):
            with self.subTest(builder=builder.__name__):
                self.assertIn("carried from", inspect.getsource(builder))


class ResumeIsNeverSilentTests(unittest.TestCase):

    def test_neither_instrument_resumes_unless_asked(self):
        """A silent resume would let a stale file masquerade as a fresh measurement."""
        for module in (rp, rdb):
            with self.subTest(module=module.__name__):
                src = inspect.getsource(module.main)
                self.assertIn('"--resume", action="store_true"', src)

    def test_the_battery_refuses_only_together_with_resume(self):
        """--resume rewrites --out from the current matrix, so filtering it would DROP every
        carried arm outside the filter. A resume that destroys results is worse than none."""
        with self.assertRaises(SystemExit) as caught:
            rdb.main(["--only", "12T_ppr", "--resume", "--out", "/tmp/should_not_be_written"])
        self.assertIn("#215", str(caught.exception))

    def test_the_refusal_happens_before_anything_is_written(self):
        target = Path(tempfile.gettempdir()) / "resume_only_guard_probe.json"
        if target.exists():
            target.unlink()
        with self.assertRaises(SystemExit):
            rdb.main(["--only", "12T_ppr", "--resume", "--out", str(target)])
        self.assertFalse(target.exists(), "the refusal must precede any write to --out")


if __name__ == "__main__":
    unittest.main()
