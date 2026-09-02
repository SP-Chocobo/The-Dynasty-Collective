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
        self.assertEqual(self.check(), ["test_thing.py: self.assertEqual 2 -> 1"])

    def test_a_deleted_assertion_is_caught(self):
        self.given(_STRONG)
        self.record()
        self.given(_STRONG.replace('        self.assertIn("x", "xy")\n', ""))
        self.assertEqual(self.check(), ["test_thing.py: self.assertIn 1 -> 0"])

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
        self.assertEqual(self.check(), ["test_thing.py: self.assertIsNotNone 1 -> 0"])


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
