"""#303: the instrument that makes a new place-to-decline argue for itself.

Synthetic trees throughout. Pointing these at the real suite would only exercise the passing
branch -- the registry is current by construction after a `--write` -- and the failing branch is
the whole point, so it has to be built.

The one assertion that touches the real tree checks that this file and `assertion_floors` agree
about what the suite IS, for the reason `suite_reach` does: two instruments disagreeing about the
population is how a module ends up held by neither.
"""

import pathlib
import tempfile
import unittest

import assertion_floors
import skip_gates

DECORATED = """import unittest


@unittest.skipUnless(False, "a reason")
class T(unittest.TestCase):
    def test_a(self):
        pass
"""

RUNTIME = """import unittest


class T(unittest.TestCase):
    def test_a(self):
        if True:
            self.skipTest("a runtime reason")
"""

SKIPIF = """import unittest


class T(unittest.TestCase):
    @unittest.skipIf(True, "a third spelling")
    def test_a(self):
        pass
"""

CLEAN = """import unittest


class T(unittest.TestCase):
    def test_a(self):
        pass
"""


class _Tree(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, body):
        (self.root / f"{name}.py").write_text(body)

    def registry(self):
        return self.root / "SKIP_GATES.json"


class AllThreeSpellingsAreFound(_Tree):
    def test_a_decorator_gate_is_found(self):
        self.write("test_x", DECORATED)
        self.assertEqual(skip_gates.scan(self.root), {"test_x.py": 1})

    def test_a_RUNTIME_skipTest_is_found_too(self):
        """The spelling `#299`'s own AST census missed, which is how a decorator count got
        mistaken for a skip measurement and published as 16 when the truth was 15."""
        self.write("test_x", RUNTIME)
        self.assertEqual(skip_gates.scan(self.root), {"test_x.py": 1})

    def test_skipIf_is_found(self):
        self.write("test_x", SKIPIF)
        self.assertEqual(skip_gates.scan(self.root), {"test_x.py": 1})

    def test_a_module_with_no_gate_is_omitted_not_recorded_as_zero(self):
        self.write("test_x", CLEAN)
        self.assertEqual(skip_gates.scan(self.root), {})

    def test_an_unparseable_module_does_not_take_the_scan_down(self):
        self.write("test_x", "def (:::")
        self.assertEqual(skip_gates.scan(self.root), {})


class GrowthFailsAndShrinkageIsFree(_Tree):
    def test_a_new_gate_in_a_registered_module_is_reported(self):
        self.write("test_x", DECORATED)
        skip_gates.write(self.root, self.registry())
        self.write("test_x", DECORATED + RUNTIME.split("import unittest")[1])
        grew = skip_gates.widened(self.root, self.registry())
        self.assertEqual(len(grew), 1, grew)
        self.assertIn("test_x.py", grew[0])
        self.assertIn("1 registered, 2 present", grew[0])

    def test_a_gate_in_a_WHOLLY_NEW_module_is_reported(self):
        """The `#299` shape: nobody edits a registered file, a new one simply arrives carrying a
        gate. `assertion_floors` deliberately ignores a new module because adding tests must be
        free; a new place to DECLINE is the opposite -- it is the thing being rationed."""
        self.write("test_x", DECORATED)
        skip_gates.write(self.root, self.registry())
        self.write("test_new", DECORATED)
        grew = skip_gates.widened(self.root, self.registry())
        self.assertEqual(len(grew), 1, grew)
        self.assertIn("test_new.py", grew[0])
        self.assertIn("0 registered", grew[0])

    def test_removing_a_module_s_LAST_gate_is_free(self):
        self.write("test_x", DECORATED)
        skip_gates.write(self.root, self.registry())
        self.write("test_x", CLEAN)
        self.assertEqual(skip_gates.widened(self.root, self.registry()), [])

    def test_removing_ONE_OF_SEVERAL_gates_is_also_free(self):
        """A distinct code path, and the only one that proves the comparison is `>` and not `!=`.

        When the LAST gate goes the module drops out of `scan()` entirely -- it is omitted, not
        recorded as 0 -- so the loop never visits it and a `!=` comparison would look correct.
        Going from two gates to one keeps the module present with a smaller number, which is
        where the direction of the comparison actually shows. A mutation to `!=` survived until
        this test existed.
        """
        self.write("test_x", DECORATED + SKIPIF.split("import unittest")[1])
        self.assertEqual(skip_gates.scan(self.root), {"test_x.py": 2})
        skip_gates.write(self.root, self.registry())
        self.write("test_x", DECORATED)
        self.assertEqual(skip_gates.scan(self.root), {"test_x.py": 1})
        self.assertEqual(skip_gates.widened(self.root, self.registry()), [])

    def test_an_unchanged_tree_reports_nothing(self):
        self.write("test_x", DECORATED)
        self.write("test_y", RUNTIME)
        skip_gates.write(self.root, self.registry())
        self.assertEqual(skip_gates.widened(self.root, self.registry()), [])


class ADamagedRegistryHoldsNothingAndSaysSo(_Tree):
    def test_a_missing_registry_loads_as_empty(self):
        self.assertEqual(skip_gates.load(self.root / "nope.json"), {})

    def test_a_damaged_registry_loads_as_empty_rather_than_raising(self):
        p = self.registry()
        p.write_text("{not json")
        self.assertEqual(skip_gates.load(p), {})

    def test_everything_reads_as_new_against_an_empty_registry(self):
        """Which is why `--check` refuses to pass on one, rather than reporting no growth."""
        self.write("test_x", DECORATED)
        self.assertEqual(len(skip_gates.widened(self.root, self.registry())), 1)


class ItReportsWhereAndWhat(_Tree):
    def test_each_gate_comes_back_with_its_line_and_its_condition(self):
        self.write("test_x", DECORATED)
        rows = skip_gates.gates_in(self.root / "test_x.py")
        self.assertEqual(len(rows), 1)
        line, what = rows[0]
        self.assertEqual(line, 4)
        self.assertIn("skipUnless", what)
        self.assertIn("False", what)


class ThePopulationHasOneHome(unittest.TestCase):
    def test_the_glob_is_the_same_object_assertion_floors_uses(self):
        self.assertIs(skip_gates.TEST_GLOB, assertion_floors.TEST_GLOB)

    def test_the_real_registry_is_current(self):
        """Not a tautology: it fails if someone adds a gate and does not regenerate."""
        self.assertEqual(skip_gates.widened(), [])


if __name__ == "__main__":
    unittest.main()
