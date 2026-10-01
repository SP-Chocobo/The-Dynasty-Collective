"""The registry's own guard (#52 phase 6.3).

The registry exists because a green suite cannot tell "this invariant holds" from "no test
entered a domain where it fails", and the second is exactly what a green suite means when the
domain has just grown. So the thing being ratcheted here is the POPULATION SIZE, not the claim:
the claims are pinned by the real tests each entry names, and this file checks that those tests
exist, that the populations are non-empty, and that nothing has grown since the claim was last
verified against it.

A failure here is NOT a bug report. It is the notification this audit never got six times over.
The response is to re-verify the claim over the new population and then update the census -- in
that order, because updating the number first is how a registry becomes a rubber stamp.
"""
from __future__ import annotations

import importlib
import unittest

import invariant_registry as reg


class TheRegistryIsWellFormedTests(unittest.TestCase):
    def test_there_are_invariants_registered(self):
        self.assertTrue(reg.REGISTRY, "an empty registry passes every test below")

    def test_every_entry_states_a_claim_and_the_population_it_ranges_over(self):
        """A bare name is a hand-list wearing a ratchet's clothes. The population sentence is the
        load-bearing half: it is what tells the next reader what growing this number admits."""
        for entry in reg.REGISTRY:
            with self.subTest(invariant=entry.name):
                self.assertGreater(len(entry.claim), 80, "the claim is too short to be one")
                self.assertGreater(len(entry.population), 80,
                                   "the population is unstated, so the census means nothing")
                self.assertTrue(entry.pinned_by, "nothing pins this claim")

    def test_every_named_test_actually_exists(self):
        """A registry naming a test that was deleted or renamed is worse than no registry: it
        reports coverage that is not there."""
        for entry in reg.REGISTRY:
            for dotted in entry.pinned_by:
                with self.subTest(invariant=entry.name, pinned_by=dotted):
                    module_name, *rest = dotted.split(".")
                    obj = importlib.import_module(module_name)
                    for attribute in rest:
                        self.assertTrue(
                            hasattr(obj, attribute),
                            f"{dotted} does not exist -- the registry claims a test that is gone")
                        obj = getattr(obj, attribute)

    def test_no_population_is_empty(self):
        """Non-vacuity. A claim proven over nothing is proven over nothing, and a census of 0
        would ratchet happily forever."""
        for row in reg.census_report():
            with self.subTest(invariant=row["name"]):
                self.assertIsNone(row["error"], f"the enumerator failed: {row['error']}")
                self.assertGreater(row["observed"], 0)


class ThePopulationsHaveNotMovedTests(unittest.TestCase):
    """THE RATCHET. One assertion, and the failure message is the whole point of the file."""

    def test_every_registered_population_is_the_size_it_was_verified_against(self):
        moved = [r for r in reg.census_report() if r["moved"] or r["error"]]
        self.assertEqual(
            [], moved,
            "A registered invariant's POPULATION HAS CHANGED SIZE.\n"
            "  This is not a bug report -- it is the notification that an invariant proven over\n"
            "  one domain is now being asked to hold over a different one. Every finding in the\n"
            "  #52 audit that cost real work had exactly this shape, and nothing announced it.\n"
            "  Re-verify the claim over the NEW population, THEN update `census`. Updating the\n"
            "  number first is how a registry becomes a rubber stamp.\n"
            f"  moved: {[(r['name'], r['recorded'], r['observed']) for r in moved]}")


class TheRatchetActuallyRatchetsTests(unittest.TestCase):
    """The guard above is one assertion over generated data, which is the shape most likely to
    pass vacuously. These drive it rather than trusting it."""

    def test_a_grown_population_fails(self):
        real = reg.REGISTRY
        entry = real[0]
        grown = reg.Invariant(
            name=entry.name, claim=entry.claim, population=entry.population,
            members=lambda: list(entry.members()) + ["a_fifth_term"],
            census=entry.census, pinned_by=entry.pinned_by)
        reg.REGISTRY = (grown,) + real[1:]
        try:
            moved = [r for r in reg.census_report() if r["moved"]]
            self.assertEqual(len(moved), 1)
            self.assertEqual(moved[0]["observed"], entry.census + 1)
        finally:
            reg.REGISTRY = real

    def test_a_SHRUNK_population_fails_too(self):
        """Both directions. A term being REMOVED invalidates a bound just as surely as one being
        added -- #216's fourth term is the case that broke this, and removing it would leave the
        corrected claim describing a sum that no longer exists."""
        real = reg.REGISTRY
        entry = real[0]
        shrunk = reg.Invariant(
            name=entry.name, claim=entry.claim, population=entry.population,
            members=lambda: list(entry.members())[:-1],
            census=entry.census, pinned_by=entry.pinned_by)
        reg.REGISTRY = (shrunk,) + real[1:]
        try:
            self.assertEqual(len([r for r in reg.census_report() if r["moved"]]), 1)
        finally:
            reg.REGISTRY = real

    def test_an_enumerator_that_cannot_run_is_a_finding_not_a_pass(self):
        """The failure mode a try/except would create: a population that errors must not read as
        a population that did not move."""
        real = reg.REGISTRY
        entry = real[0]

        def broken():
            raise RuntimeError("the thing this counted no longer exists")

        reg.REGISTRY = (reg.Invariant(
            name=entry.name, claim=entry.claim, population=entry.population,
            members=broken, census=entry.census, pinned_by=entry.pinned_by),) + real[1:]
        try:
            rows = reg.census_report()
            self.assertIsNotNone(rows[0]["error"])
            self.assertIn("RuntimeError", rows[0]["error"])
            self.assertIsNone(rows[0]["observed"])
        finally:
            reg.REGISTRY = real

    def test_main_reports_nonzero_when_something_moved(self):
        """The CLI is how a person runs this outside the suite; it must not print `ok` and exit 0
        while an entry is stale."""
        real = reg.REGISTRY
        entry = real[0]
        reg.REGISTRY = (reg.Invariant(
            name=entry.name, claim=entry.claim, population=entry.population,
            members=lambda: list(entry.members()) + ["extra"],
            census=entry.census, pinned_by=entry.pinned_by),) + real[1:]
        try:
            self.assertEqual(reg.main(), 1)
        finally:
            reg.REGISTRY = real
        self.assertEqual(reg.main(), 0)


if __name__ == "__main__":
    unittest.main()
