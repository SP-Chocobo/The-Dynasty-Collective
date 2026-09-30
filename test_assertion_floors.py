"""§19.8: the loosening detector, demonstrated on a loosening.

The doctrine's own rule applies to this file harder than to most: *a test that cannot fail proves
nothing.* A check for weakened tests that was itself only exercised on unweakened tests would be
the exact shape of thing it exists to find. So every test below plants a real edit and asserts
what the checker says about it.

THE CASE THAT MOTIVATES THE WHOLE DESIGN is `test_a_substituted_weaker_assertion_is_caught`:
identical test count, identical total assertion count, strictly less guarantee. A design counting
only totals reports green on it.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import assertion_floors

_STRONG = '''
import unittest
class T(unittest.TestCase):
    def test_a(self):
        self.assertEqual(compute(), 41.0)
    def test_b(self):
        self.assertEqual(other(), 7)
        self.assertIn("x", "xy")
'''


class _Sandbox(unittest.TestCase):
    """Each case gets its own directory and floors file -- this module must never read or write
    the repository's real ASSERTION_FLOORS.json, which the suite it is part of depends on."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.floors = self.root / "floors.json"
        self.addCleanup(self._tmp.cleanup)

    def given(self, source: str, name: str = "test_thing.py") -> None:
        (self.root / name).write_text(source)

    def record(self) -> None:
        assertion_floors.write(self.root, self.floors)

    def check(self) -> list[str]:
        return assertion_floors.drops(self.root, self.floors)


#: THE KEYS ARE QUALIFIED `Class.method` SINCE D-F4, and these expectations moved with them. The
#: bare method name collided: two classes in one module sharing a test name recorded only the last
#: one walked, so weakening the unrecorded twin -- netted against an addition elsewhere in the
#: module -- passed `drops()`. Five such names exist in this repository today
#: (`test_screen_context.py` four, `test_decision_qualifiers.py` one). The qualified key is what
#: closes that, and a message naming `T.test_b` rather than `test_b` is the visible half of it.
class ALooseningIsCaughtTests(_Sandbox):
    def test_a_substituted_weaker_assertion_is_caught(self):
        """assertEqual -> assertIsNotNone. Test count unchanged, TOTAL assertion count unchanged,
        and the engine is no longer held to a number. This is the case per-name counting exists
        for, and the one a total would miss."""
        self.given(_STRONG)
        self.record()
        before = json.loads(self.floors.read_text())["modules"]["test_thing.py"]
        self.given(_STRONG.replace("self.assertEqual(compute(), 41.0)",
                                   "self.assertIsNotNone(compute())"))
        after = assertion_floors.scan_module(self.root / "test_thing.py")
        self.assertEqual(before["test_methods"], after["test_methods"])
        self.assertEqual(sum(before["asserts"].values()), sum(after["asserts"].values()))
        found = self.check()
        self.assertIn("test_thing.py: self.assertEqual 2 -> 1", found)
        self.assertIn("test_thing.py: T.test_a self.assertEqual 1 -> 0", found)

    def test_a_deleted_assertion_is_caught(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG.replace('        self.assertIn("x", "xy")\n', ""))
        # Two lines now: the module-level drop and the method-level one that #52 phase 4
        # added. Asserting BOTH rather than relaxing to a substring -- the finer line is
        # the repair, and a test that stopped requiring it would let the repair rot.
        found = self.check()
        self.assertIn("test_thing.py: self.assertIn 1 -> 0", found)
        self.assertIn("test_thing.py: T.test_b self.assertIn 1 -> 0", found)

    def test_a_deleted_test_method_is_caught(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG.split("    def test_b")[0])
        self.assertIn("test_thing.py: test methods 2 -> 1", self.check())

    def test_a_deleted_module_is_caught(self):
        self.given(_STRONG)
        self.record()
        (self.root / "test_thing.py").unlink()
        self.assertEqual(self.check(),
                         ["test_thing.py: module is gone (floor recorded 2 test methods)"])

    def test_a_module_that_stops_parsing_is_caught(self):
        """A module that no longer imports is a module whose guarantees are not running, and the
        suite would report it as an error rather than a shrinking count -- but only if discovery
        reaches it. Counting it as zero is the honest read."""
        self.given(_STRONG)
        self.record()
        self.given(_STRONG + "\n    def broken(:\n")
        self.assertTrue(self.check())


class LegitimateChangesDoNotDemandARegenerationTests(_Sandbox):
    """The design constraint that makes the check worth having: if adding a test forced a
    `--write`, the repair would become reflexive and the check would stop being read."""

    def test_adding_assertions_passes(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG + '        self.assertGreater(1, 0)\n')
        self.assertEqual(self.check(), [])

    def test_adding_a_whole_test_method_passes(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG + '''
    def test_c(self):
        self.assertEqual(third(), 3)
''')
        self.assertEqual(self.check(), [])

    def test_a_brand_new_module_passes(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG, name="test_other.py")
        self.assertEqual(self.check(), [])

    def test_a_STRENGTHENING_also_fails_and_that_is_the_honest_cost(self):
        """The limit of per-name counting, pinned rather than papered over. This mechanism has no
        opinion about which assertions are stronger -- that ordering would be invented -- so
        assertIsNotNone -> assertEqual drops a per-name count exactly like the reverse, and fails
        exactly like it. The failure output names both sides, so a reviewer reads the direction
        in a glance; what never happens is a weakening passing unseen. The first draft of
        assertion_floors' own docstring claimed strengthening passed untouched. It does not, and
        this test is why that claim was corrected."""
        self.given(_STRONG.replace("self.assertEqual(other(), 7)", "self.assertIsNotNone(other())"))
        self.record()
        self.given(_STRONG)
        found = self.check()
        self.assertIn("test_thing.py: self.assertIsNotNone 1 -> 0", found)
        self.assertIn("test_thing.py: T.test_b self.assertIsNotNone 1 -> 0", found)


class WhatIsCountedTests(_Sandbox):
    def test_only_self_dotted_assertions_count(self):
        """A bare `assert` or another object's assert method is not a unittest assertion, and
        counting it would let a module inflate its own floor with statements the runner does not
        treat the same way."""
        self.given('''
import unittest
class T(unittest.TestCase):
    def test_a(self):
        assert True
        other.assertEqual(1, 1)
        self.assertEqual(1, 1)
''')
        counted = assertion_floors.scan_module(self.root / "test_thing.py")
        self.assertEqual(counted["asserts"], {"assertEqual": 1})

    def test_fail_counts_as_an_assertion(self):
        self.given('''
import unittest
class T(unittest.TestCase):
    def test_a(self):
        self.fail("unreachable")
''')
        self.assertEqual(assertion_floors.scan_module(self.root / "test_thing.py")["asserts"],
                         {"fail": 1})


class TheRepositorysOwnFloorsAreCurrentTests(unittest.TestCase):
    def test_nothing_in_this_repository_has_shrunk(self):
        """The check itself, run against the real tree -- the same thing CI runs, so a local run
        finds a drop before a push does."""
        self.assertEqual(assertion_floors.drops(), [])

    def test_the_floors_file_covers_this_module_too(self):
        """A detector exempt from its own detector is the shape of thing this repository keeps
        finding."""
        self.assertIn("test_assertion_floors.py", assertion_floors.load())


if __name__ == "__main__":
    unittest.main()


class ThePromisedGuaranteeIsActuallyKept(unittest.TestCase):
    """#52 phase 4. This module's docstring promises, without qualification, that "any
    substitution -- one assertion name swapped for another -- FAILS, either way", and separately
    states its own limits. An adversarial pass claimed four ways past it; two were the stated
    limits and two were real. These are the two real ones, each planted rather than described.
    """

    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="floors_"))
        self.floors = self.temp / "FLOORS.json"
        self.addCleanup(shutil.rmtree, self.temp, True)

    def _write_module(self, body):
        (self.temp / "test_planted.py").write_text(body)

    def test_a_substitution_that_nets_out_is_still_caught(self):
        """THE PLANTED DEFECT. Weaken one assertion and add another of the same name elsewhere
        in the same edit: every module-level count is unchanged, and the check used to return
        []. The guarantee was stated absolutely and could not be kept at module granularity."""
        self._write_module(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_one(self):\n"
            "        self.assertEqual(1, 1)\n"
            "    def test_two(self):\n"
            "        self.assertTrue(True)\n")
        assertion_floors.write(root=self.temp, path=self.floors)
        self.assertEqual([], assertion_floors.drops(root=self.temp, path=self.floors),
                         "the freshly written floors already report a drop")
        self._write_module(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_one(self):\n"
            "        self.assertIsNotNone(1)\n"          # weakened here
            "    def test_two(self):\n"
            "        self.assertTrue(True)\n"
            "    def test_three(self):\n"
            "        self.assertEqual(2, 2)\n")          # replaced here, netting to zero
        found = assertion_floors.drops(root=self.temp, path=self.floors)
        self.assertTrue(found,
                        "a weakened assertion offset by an addition elsewhere passed unseen -- "
                        "the module's own 'any substitution FAILS' promise is not kept")
        self.assertTrue(any("test_one" in line for line in found),
                        f"the drop was reported without naming the method it happened in: {found}")

    def test_a_check_holding_no_floors_does_not_report_success(self):
        """THE PLANTED DEFECT. `load()` returns {} for a missing or damaged file, deliberately,
        so `--write` can repair one. That is right for `load` and meant `--check` printed "no
        guarantee has shrunk (0 modules held to a floor)" and exited 0 while holding nothing."""
        (self.temp / "ASSERTION_FLOORS.json").write_text("{ this is not json")
        previous = os.getcwd()
        os.chdir(self.temp)
        try:
            exit_code = assertion_floors.main(["--check"])
        finally:
            os.chdir(previous)
        self.assertEqual(1, exit_code,
                         "--check exited 0 over a damaged floors file, reporting success while "
                         "enforcing nothing")

    def test_an_intact_check_still_passes(self):
        """The control. A check that failed unconditionally would satisfy the test above."""
        self._write_module(
            "import unittest\n"
            "class T(unittest.TestCase):\n"
            "    def test_one(self):\n"
            "        self.assertEqual(1, 1)\n")
        assertion_floors.write(root=self.temp, path=self.floors)
        self.assertEqual([], assertion_floors.drops(root=self.temp, path=self.floors))


class TheSilentDisableVectorsAreCountedAndRatcheted(unittest.TestCase):
    """`0.4`: a test does not have to lose an assertion to stop running.

    Four edits were applied to a scratch copy of a real test module and the module re-scanned.
    Each produced a scan byte-identical to baseline -- `@unittest.skip`, `@unittest.expectedFailure`,
    a leading `self.skipTest()`, and a leading `return`: nineteen test methods before and after,
    every assert count unchanged. The counts are taken from source text, and none of those four
    touches a `def test_` or an `assert*` call. `DISABLERS` closes that, and `drops` treats an
    INCREASE as the loss, which is the one place in this design where growth is the failure.
    """

    def _scan(self, body: str) -> dict:
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        path = temp / "test_scratch.py"
        path.write_text("import unittest\n\n\nclass T(unittest.TestCase):\n" + body)
        return assertion_floors.scan_module(path)

    BASE = ("    def test_one(self):\n        self.assertEqual(1, 1)\n")

    def test_the_baseline_module_has_no_disablers(self):
        self.assertEqual(dict.fromkeys(assertion_floors.DISABLERS, 0),
                         self._scan(self.BASE)["disabled"])

    def test_each_vector_is_seen(self):
        for body, key in (
            ("    @unittest.skip('flaky')\n" + self.BASE, "skip_decorators"),
            ("    @unittest.skipIf(True, 'nope')\n" + self.BASE, "skip_decorators"),
            ("    @unittest.skipUnless(False, 'needs a thing')\n" + self.BASE, "skip_decorators"),
            ("    @unittest.expectedFailure\n" + self.BASE, "expected_failures"),
            ("    def test_one(self):\n        self.skipTest('no')\n        self.assertEqual(1, 1)\n",
             "skipTest_calls"),
            ("    def test_one(self):\n        return\n        self.assertEqual(1, 1)\n",
             "early_returns"),
        ):
            with self.subTest(key):
                self.assertEqual(1, self._scan(body)["disabled"][key],
                                 f"{key} was not detected; this vector is invisible again")

    def test_a_class_level_skip_counts_once_per_test_it_silences(self):
        """A skip on the class silences every test in it. Counting the DECORATOR rather than the
        tests would show a reviewer +1 where the loss is however many tests the class holds."""
        body = ("    def test_one(self):\n        self.assertEqual(1, 1)\n"
                "    def test_two(self):\n        self.assertEqual(2, 2)\n"
                "    def test_three(self):\n        self.assertEqual(3, 3)\n")
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        path = temp / "test_scratch.py"
        path.write_text("import unittest\n\n\n@unittest.skip('all of it')\n"
                        "class T(unittest.TestCase):\n" + body)
        self.assertEqual(3, assertion_floors.scan_module(path)["disabled"]["skip_decorators"])

    def test_an_ordinary_return_inside_a_branch_is_not_counted(self):
        """A `return` under an `if` is control flow, not a disabled test. Counting it would flood
        the floors with false positives, and a check nobody reads defends nothing."""
        body = ("    def test_one(self):\n"
                "        if not self.maxDiff:\n            return\n"
                "        self.assertEqual(1, 1)\n")
        self.assertEqual(0, self._scan(body)["disabled"]["early_returns"])

    def test_growth_is_reported_as_a_drop(self):
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, ignore_errors=True)
        floors = temp / "FLOORS.json"
        path = temp / "test_scratch.py"
        path.write_text("import unittest\n\n\nclass T(unittest.TestCase):\n" + self.BASE)
        assertion_floors.write(root=temp, path=floors)
        self.assertEqual([], assertion_floors.drops(root=temp, path=floors))
        path.write_text("import unittest\n\n\nclass T(unittest.TestCase):\n"
                        "    @unittest.skip('quietly')\n" + self.BASE)
        reported = assertion_floors.drops(root=temp, path=floors)
        self.assertTrue(any("skip_decorators 0 -> 1" in line for line in reported), reported)


class TheFixtureThatSixtySKIPSDependOnIsPresent(unittest.TestCase):
    """The ratchet above counts SYNTACTIC disablers. It cannot see a CONDITION flipping.

    Measured on the committed tree: 20 of 197 test modules carry a silent-disable vector, and 84
    test methods sit behind one -- 60 skip decorators and 24 `skipTest` calls -- while the suite
    reports `skipped=1`. The difference is that the conditions are currently SATISFIED. Twelve of
    those modules gate on one predicate, `CAPTURE.exists()`, so a single missing file turns roughly
    57 passing tests into silent skips and the suite still prints OK. The decorator count does not
    move, so the ratchet says nothing.

    This converts that into ONE LOUD FAILURE. It is deliberately not a `skipUnless` itself: a guard
    that skips when the thing it guards is missing is the defect it exists to catch.

    Not hypothetical. A module added earlier in this same session hand-wrote this path, got it
    wrong, and reported OK while skipping all five of its tests.
    """

    def test_the_real_capture_exists(self):
        import run_draft_battery as rdb
        self.assertTrue(
            rdb.CAPTURE_PATH.exists(),
            f"{rdb.CAPTURE_PATH} is missing. Roughly 57 tests across 12 modules gate on this file "
            f"and would SKIP silently, leaving the suite green over a fraction of its coverage. "
            f"This one failure is standing in for all of them.")

    def test_modules_gate_on_the_harness_constant_rather_than_a_literal_path(self):
        """A hand-written path is a silent skip waiting to happen -- it was, twice. Any module
        spelling the capture filename itself can drift from the real location without a word."""
        import ast

        import run_draft_battery as rdb
        name = rdb.CAPTURE_PATH.name

        def docstring_constants(tree):
            """The Constant nodes that are DOCSTRINGS, so prose mentioning the fixture is not
            flagged as a hand-written path. The first version of this check counted them and
            reported a module whose only mention was a sentence in its own docstring."""
            found = set()
            for node in ast.walk(tree):
                body = getattr(node, "body", None)
                if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)) and body:
                    first = body[0]
                    if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                            and isinstance(first.value.value, str)):
                        found.add(id(first.value))
            return found

        offenders = []
        for q in sorted(Path(".").glob("test_*.py")):
            src = q.read_text()
            # NO MODULE-WIDE ESCAPE (D-F5). This read `or "CAPTURE_PATH" in src`, so ANY module
            # that mentioned the constant anywhere was skipped whole -- and
            # `test_battery_pricing_path.py` both defines a literal capture path AND mentions
            # `rdb.CAPTURE_PATH` in an unrelated assertion, so the one real offender was the one
            # module the guard refused to look at, and it reported zero. A module using the
            # constant properly has no reason to carry the filename as a string literal, so the
            # per-node check below is sufficient on its own.
            if name not in src:
                continue
            tree = ast.parse(src)
            skip = docstring_constants(tree)
            if any(isinstance(n, ast.Constant) and isinstance(n.value, str)
                   and name in n.value and id(n) not in skip for n in ast.walk(tree)):
                offenders.append(q.name)
        self.assertEqual([], offenders,
                         f"these modules spell the capture path by hand: {offenders}. Use "
                         f"rdb.CAPTURE_PATH so a moved fixture is an error, not a mass skip.")
