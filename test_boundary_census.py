"""The boundary ratchet, tested for the failure that would make it decorative (`#254`).

A census that cannot detect a new reach is a comment. This module's whole value is that the
number cannot rise quietly while the contract is being designed, so the tests that matter are the
ones that plant a widening and require it to be caught -- not the one that observes today's hull
passing, which would also pass if the scan matched nothing at all.

Cited register items: `#126` (one home for the walk -- the report and the guard read the same
function), `#254` (a guard that catches nothing is not a guard), `#245` (a count nobody can
move is a broken instrument until proven otherwise).
"""

from __future__ import annotations

import pathlib
import tempfile
import unittest

import boundary_census as bc


def _hull(body: str) -> pathlib.Path:
    #: NOT NAMED `app.py`, deliberately. `reaches()` takes the path and parses whatever is there --
    #: the filename reaches no branch of it, so naming this fixture after the hull carried no
    #: information. What it DID do was build an `app.py` path inside a test module, which is the
    #: exact construct `test_ui_source.offends` polices; the certifying suite reported this file as
    #: the one offender. Exempting it would have put a third name on an allowlist whose two
    #: entries are what proves that guard still catches something (`#254`), and would have made
    #: that guard's own prose -- "the two modules that genuinely build an `app.py` path are
    #: exactly the two already in `ALLOWED`" -- false (`#133`). So the construct is gone instead.
    path = pathlib.Path(tempfile.mkdtemp()) / "synthetic_hull.py"
    path.write_text(body, encoding="utf-8")
    return path


class TheScanSeesBothShapesTests(unittest.TestCase):
    """Module calls AND instance calls. Missing the second reads this boundary as half its size:
    23 of the real 44 call sites are `merger.X(...)` / `client.X(...)`."""

    def test_a_module_level_call_is_counted(self):
        found = bc.reaches(_hull("import data_merger\n"
                                 "x = data_merger.recency_grade(1)\n"))
        self.assertEqual(1, found["data_merger.recency_grade"])

    def test_a_from_import_call_is_counted(self):
        found = bc.reaches(_hull("from data_merger import recency_grade\n"
                                 "x = recency_grade(1)\n"))
        self.assertEqual(1, found["data_merger.recency_grade"])

    def test_an_INSTANCE_method_call_is_counted(self):
        found = bc.reaches(_hull("merger = object()\n"
                                 "x = merger.merge_player('a')\n"))
        self.assertEqual(1, found["merger.merge_player"])

    def test_an_aliased_module_is_followed(self):
        found = bc.reaches(_hull("import data_merger as dm\n"
                                 "x = dm.recency_grade(1)\n"))
        self.assertEqual(1, found["data_merger.recency_grade"])

    def test_a_NON_data_module_is_not_counted(self):
        """Non-vacuity in the other direction: a scan that counted everything would pass every
        test above while saying nothing about the boundary."""
        found = bc.reaches(_hull("import pick_synthesis\n"
                                 "x = pick_synthesis.build_snapshot()\n"))
        self.assertEqual(0, sum(found.values()))


class TheRatchetCatchesAWideningTests(unittest.TestCase):
    """THE POINT. Each of these plants a widening and requires it to be reported."""

    def test_a_brand_new_reach_is_reported_as_new(self):
        grew = bc.widened(_hull("merger = object()\n"
                                "x = merger.a_method_nobody_registered()\n"))
        self.assertTrue(grew, "a reach absent from the census was not reported")
        self.assertIn("NEW REACH", grew[0])
        self.assertIn("a_method_nobody_registered", grew[0])

    def test_MORE_calls_to_a_registered_reach_are_reported(self):
        body = "merger = object()\n" + "x = merger.list_free_agents()\n" * 3
        grew = bc.widened(_hull(body))
        self.assertTrue(grew, "a registered reach called more often was not reported")
        self.assertIn("list_free_agents", grew[0])
        self.assertIn("1 -> 3", grew[0])

    def test_FEWER_calls_are_NOT_reported(self):
        """Shrinkage is the project working, not a regression. Phase 6 drives this to zero."""
        self.assertEqual([], bc.widened(_hull("merger = object()\n"
                                              "x = merger.list_free_agents()\n")))

    def test_an_empty_hull_passes_because_zero_is_the_goal(self):
        self.assertEqual([], bc.widened(_hull("x = 1\n")))


class TheRealHullMatchesItsCensusTests(unittest.TestCase):
    """The measurement this file was built from, pinned so the document beside it cannot go
    stale without something saying so."""

    def test_the_hull_has_not_widened(self):
        grew = bc.widened()
        self.assertEqual([], grew, f"the boundary widened: {grew}")

    def test_the_census_is_not_empty(self):
        """Non-vacuity: every test above would pass over an empty census and an empty scan."""
        self.assertGreater(len(bc.CENSUS), 20)
        self.assertGreater(sum(bc.CENSUS.values()), 40)

    def test_the_scan_actually_finds_reaches_in_the_real_hull(self):
        """And the same non-vacuity for the scan. A walk that matched nothing would report the
        boundary as perfectly clean, which is the shape `#245` warns about."""
        found = bc.reaches()
        self.assertGreater(sum(found.values()), 40,
                           "the scan found almost nothing in app.py -- suspect the scan")

    def test_every_census_key_names_an_owner_and_a_function(self):
        for reach in bc.CENSUS:
            with self.subTest(reach=reach):
                owner, _, func = reach.partition(".")
                self.assertTrue(owner and func, f"{reach} is not owner.function")
                self.assertTrue(owner in bc.DATA_MODULES or owner in bc.DATA_INSTANCES,
                                f"{owner} is neither a data module nor a data instance")


if __name__ == "__main__":
    unittest.main()
