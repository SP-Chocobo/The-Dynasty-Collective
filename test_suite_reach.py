"""#298: the instrument that notices a test module the runner cannot reach.

Every test here runs against a SYNTHETIC tree in a temporary directory. Pointing them at the
real suite would make them circular -- the thing under test is "does this notice a broken
population", and the real population is (today) not broken, so it can only demonstrate the
passing branch. The failing branch is the whole point, so it has to be constructed.

The one assertion that does touch the real tree is deliberate: that `suite_reach` and
`assertion_floors` agree about what the suite IS. Two instruments disagreeing about the
population is how a module ends up held by neither.
"""

import sys
import tempfile
import unittest
from pathlib import Path

import assertion_floors
import suite_reach

GOOD = "import unittest\n\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n\n    def test_b(self):\n        pass\n"
NO_SUCH_DEPENDENCY = "import a_distribution_that_is_not_installed_anywhere\n"
EXITS_AT_IMPORT = "import sys\nsys.exit('module scope called sys.exit')\n"


class _Tree(unittest.TestCase):
    """A temporary directory of test modules, cleaned out of sys.modules afterwards."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._before = set(sys.modules)
        self._path_before = list(sys.path)

    def tearDown(self):
        for name in set(sys.modules) - self._before:
            del sys.modules[name]
        sys.path[:] = self._path_before
        self._tmp.cleanup()

    def write(self, name: str, body: str) -> None:
        (self.root / f"{name}.py").write_text(body)


class ThePopulationHasOneHome(unittest.TestCase):
    def test_the_glob_is_the_same_object_assertion_floors_uses(self):
        # Not merely equal. A restated "test_*.py" would be equal and would be a second source
        # of truth for what the suite is made of (#126); identity is what rules that out.
        self.assertIs(suite_reach.TEST_GLOB, assertion_floors.TEST_GLOB)

    def test_both_instruments_see_the_same_modules(self):
        floors = {Path(name).stem for name in assertion_floors.scan(Path("."))}
        self.assertEqual(set(suite_reach.population(Path("."))), floors)
        self.assertGreater(len(floors), 200, "the real suite should be here; is the cwd wrong?")


class AModuleTheRunnerCannotReachIsNamed(_Tree):
    def test_a_missing_dependency_is_reported_with_the_name_it_is_missing(self):
        self.write("test_srfix_reaches", GOOD)
        self.write("test_srfix_cannot", NO_SUCH_DEPENDENCY)
        dead = suite_reach.unreachable(self.root)
        self.assertEqual(set(dead), {"test_srfix_cannot"})
        self.assertIn("a_distribution_that_is_not_installed_anywhere", dead["test_srfix_cannot"])
        self.assertIn("ModuleNotFoundError", dead["test_srfix_cannot"])

    def test_a_module_that_exits_at_import_is_caught_not_propagated(self):
        # SystemExit is not an Exception. `except Exception` here would let a mis-run argparse
        # at module scope take down the check that exists to report it.
        self.write("test_srfix_exits", EXITS_AT_IMPORT)
        dead = suite_reach.unreachable(self.root)
        self.assertEqual(set(dead), {"test_srfix_exits"})
        self.assertIn("SystemExit", dead["test_srfix_exits"])

    def test_a_clean_tree_reports_nothing(self):
        self.write("test_srfix_one", GOOD)
        self.write("test_srfix_two", GOOD)
        self.assertEqual(suite_reach.unreachable(self.root), {})


class TheRootParameterIsActuallyRead(_Tree):
    def test_a_module_only_present_under_root_is_found_and_imported(self):
        # The first draft globbed `root` and then imported against sys.path, so a module that
        # exists ONLY under root was reported unreachable. That is a parameter half-honoured:
        # the caller is told it was read, and it was read for the listing but not the lookup.
        self.write("test_srfix_only_here", GOOD)
        self.assertEqual(suite_reach.unreachable(self.root), {})
        self.assertIn("test_srfix_only_here", sys.modules)

    def test_root_is_taken_back_off_sys_path(self):
        self.write("test_srfix_only_here", GOOD)
        before = list(sys.path)
        suite_reach.unreachable(self.root)
        self.assertEqual(sys.path, before, "the check left its own directory on sys.path")


class TheReportNamesTheThingToFix(_Tree):
    def test_it_names_the_interpreter_because_that_is_usually_the_cause(self):
        text = suite_reach.report({}, self.root, count_cases=False)
        self.assertIn(sys.executable, text)
        self.assertIn(sys.version.split()[0], text)

    def test_a_clean_tree_says_so_with_its_total(self):
        self.write("test_srfix_one", GOOD)
        text = suite_reach.report({}, self.root, count_cases=False)
        self.assertIn("every one of the 1 test modules imports", text)

    def test_a_broken_tree_lists_every_dead_module_and_its_reason(self):
        self.write("test_srfix_one", GOOD)
        self.write("test_srfix_cannot", NO_SUCH_DEPENDENCY)
        dead = suite_reach.unreachable(self.root)
        text = suite_reach.report(dead, self.root, count_cases=False)
        self.assertIn("1 of 2 test modules CANNOT BE IMPORTED", text)
        self.assertIn("does not run", text)
        self.assertIn("test_srfix_cannot", text)
        self.assertIn("a_distribution_that_is_not_installed_anywhere", text)


class TheReportAndTheExitCodeShareOneMeasurement(_Tree):
    def test_the_report_renders_the_measurement_it_is_handed(self):
        # `report` must not re-measure. An import that fails on the first pass can succeed on a
        # second once a sibling has populated sys.modules, and a report disagreeing with the
        # exit code printed beside it is worse than either alone.
        self.write("test_srfix_one", GOOD)
        text = suite_reach.report({"test_srfix_one": "RuntimeError: as measured earlier"},
                                  self.root, count_cases=False)
        self.assertIn("1 of 1 test modules CANNOT BE IMPORTED", text)
        self.assertIn("as measured earlier", text)


class ADeadModuleContributesNoTestCases(_Tree):
    def test_the_count_excludes_the_synthetic_failure_unittest_substitutes(self):
        # unittest replaces a module whose import died with ONE _FailedTest. Counting it would
        # report a suite that lost 20 tests as having lost 19, which is the failure mode this
        # whole item is about.
        self.write("test_srfix_two_tests", GOOD)
        self.write("test_srfix_cannot", NO_SUCH_DEPENDENCY)
        self.assertEqual(suite_reach.collected(self.root), 2)


class TheCommandLineFailsLoudly(_Tree):
    def test_check_exits_nonzero_on_a_module_that_cannot_be_imported(self):
        self.write("test_srfix_cannot", NO_SUCH_DEPENDENCY)
        import contextlib
        import io
        out = io.StringIO()
        cwd = Path.cwd()
        import os
        os.chdir(self.root)
        try:
            with contextlib.redirect_stdout(out):
                code = suite_reach.main(["--check", "--no-count"])
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 1)
        self.assertIn("CANNOT BE IMPORTED", out.getvalue())


if __name__ == "__main__":
    unittest.main()
