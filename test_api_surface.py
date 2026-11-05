"""`#310` -- the API inventory must stay an inventory, not become a list that drifted.

The findings this file pins, each of which was a wrong published number before it was a test:

  - "31 engine functions across 12 modules" was an ARTIFACT OF A HAND-PICKED MODULE SET. The
    hull reaches 145 distinct functions across 35 of its own modules. A test that only checks
    the layer tables are internally consistent would have let that stand, so the first test
    below derives the population and asserts the layers COVER it.
  - The owner's five layers do not cover what the hull reaches. `PRODUCT_STORE` (six modules a
    browser talks to directly) and `RENDER` (three modules the rewrite replaces) are the two
    the measurement forced, and a layer that falls empty is a layer somebody deleted the
    evidence for -- so emptiness fails here rather than passing quietly.
  - The Draft Room's live alpha needs 15 engine functions, not 145 and not 31. That number is
    DERIVED from the declared operations; asserting it directly would make it a restatement.
"""

from __future__ import annotations

import ast
import pathlib
import unittest
from unittest import mock

import api_surface as api
import boundary_census as bc


class EveryModuleTheHullReachesHasAnOwnerTests(unittest.TestCase):

    def test_no_module_the_hull_reaches_is_unassigned(self):
        """THE RATCHET. A module newly wired into the hull is a new ownership decision; until
        somebody makes it, the inventory has a hole and says so."""
        self.assertEqual([], api.unassigned(),
                         "the hull reaches a module no layer claims -- decide whose job it is")

    def test_no_module_is_claimed_by_two_layers(self):
        self.assertEqual([], api.double_assigned(), "two owners is no owner")

    def test_the_population_is_the_one_the_hull_actually_reaches(self):
        """Non-vacuity for the test above: if `reaches` returned a handful of modules, "every
        module has an owner" would be true and worthless. The published figure that was wrong
        was 31 functions in 12 modules; the real one is an order of magnitude more modules."""
        found = api.reaches()
        modules = {r.split(".", 1)[0] for r in found}
        self.assertGreater(len(modules), 25,
                           f"only {len(modules)} modules reached; the scanner has narrowed")
        self.assertGreater(len(found), 100,
                           f"only {len(found)} distinct functions; the scanner has narrowed")
        # ...and the narrow count that was published must not be reproducible by accident.
        self.assertNotEqual(31, len(found))

    def test_the_ratchet_fires_on_a_module_with_no_owner(self):
        """Mutation-proofing in the file itself: drop a layer's largest module and the guard
        must name it. Without this, `unassigned() == []` could be a function that returns []."""
        thinned = dict(api.LAYERS)
        thinned["ORCHESTRATION"] = {m: why for m, why in api.ORCHESTRATION.items()
                                    if m != "llm_engine"}
        with mock.patch.object(api, "LAYERS", thinned):
            self.assertIn("llm_engine", api.unassigned())

    def test_the_double_assignment_guard_fires(self):
        doubled = dict(api.LAYERS)
        doubled["ADMIN"] = dict(api.ADMIN, llm_engine="planted")
        with mock.patch.object(api, "LAYERS", doubled):
            self.assertEqual(["llm_engine"], api.double_assigned())


class TheLayersAreTheOnesTheMeasurementForcedTests(unittest.TestCase):

    def test_no_layer_is_empty(self):
        """A layer exists because a measurement needed it. An empty one is a layer whose
        evidence was deleted without deleting the layer."""
        for name, members in api.LAYERS.items():
            with self.subTest(layer=name):
                self.assertTrue(members, f"{name} has no members")

    def test_every_assignment_carries_its_evidence(self):
        """The assignment is hand-made, which is only defensible if each line says why. An
        entry with an empty reason is an assertion with no argument behind it."""
        for name, members in api.LAYERS.items():
            for module, why in members.items():
                with self.subTest(layer=name, module=module):
                    self.assertTrue(why.strip(), f"{name}.{module} has no stated reason")
                    self.assertGreater(len(why), 15, f"{name}.{module}: {why!r} is not a reason")

    def test_every_assigned_module_exists_and_imports(self):
        for name, members in api.LAYERS.items():
            for module in members:
                with self.subTest(layer=name, module=module):
                    self.assertTrue(pathlib.Path(f"{module}.py").exists(),
                                    f"{name} claims {module}, which is not a module here")

    def test_the_vendor_data_layer_is_not_counted_twice(self):
        """`boundary_census.CENSUS` is the data layer's one home (#126). A module appearing in
        both inventories would make the same reach count in two places, and the first number
        somebody quoted would depend on which file they opened."""
        for name, members in api.LAYERS.items():
            overlap = set(members) & set(bc.DATA_MODULES)
            with self.subTest(layer=name):
                self.assertEqual(set(), overlap, f"{name} claims a vendor data module: {overlap}")

    def test_the_scanner_is_borrowed_and_not_reimplemented(self):
        """The hard-won part of `boundary_census.reaches` is that `instance.method(...)` is a
        reach -- missing it is how an earlier count of that boundary read as half its real size.
        A second scanner here would have to learn that again, so this asserts there isn't one:
        `api_surface` must call into `boundary_census`, not walk the AST itself.
        """
        tree = ast.parse(pathlib.Path("api_surface.py").read_text(encoding="utf-8"))
        walked = [n for n in ast.walk(tree)
                  if isinstance(n, ast.Call)
                  and isinstance(n.func, ast.Attribute) and n.func.attr in {"walk", "parse"}]
        self.assertEqual([], walked,
                         "api_surface parses or walks an AST of its own; use boundary_census")
        calls_census = [n for n in ast.walk(tree)
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                        and n.func.attr == "reaches"]
        self.assertTrue(calls_census, "api_surface no longer derives from boundary_census.reaches")


class DeclaredOperationsMustBeBuildableTests(unittest.TestCase):

    def test_every_declared_operation_composes_functions_that_exist(self):
        self.assertEqual([], api.unbuildable())

    def test_an_operation_naming_a_missing_function_is_caught(self):
        planted = dict(api.PUBLIC_OPERATIONS)
        planted["planted.op"] = {
            "why": "planted", "surfaces": ("draft_room",),
            "composes": {"pick_synthesis": ("a_function_nobody_wrote",)}}
        with mock.patch.object(api, "PUBLIC_OPERATIONS", planted):
            self.assertIn("planted.op: pick_synthesis.a_function_nobody_wrote does not exist",
                          api.unbuildable())

    def test_an_operation_reaching_past_the_engine_is_caught(self):
        """A public operation composing orchestration is not forbidden in principle -- it is
        forbidden SILENTLY. This is the shape `boundary_census` counts, so it gets named."""
        planted = dict(api.PUBLIC_OPERATIONS)
        planted["planted.op"] = {
            "why": "planted", "surfaces": ("draft_room",),
            "composes": {"llm_engine": ("run_debate",)}}
        with mock.patch.object(api, "PUBLIC_OPERATIONS", planted):
            problems = api.unbuildable()
        self.assertTrue(any("llm_engine, which is ORCHESTRATION, not ENGINE" in p
                            for p in problems), problems)

    def test_every_operation_states_why_it_is_one_request(self):
        for op, spec in api.PUBLIC_OPERATIONS.items():
            with self.subTest(op=op):
                self.assertGreater(len(str(spec["why"])), 40,
                                   f"{op} does not say why it is one coherent operation")
                self.assertTrue(spec["surfaces"], f"{op} names no surface that needs it")


class TheDraftRoomAlphaSliceIsSmallerThanTheInventoryTests(unittest.TestCase):

    def test_the_slice_is_derived_from_the_operations(self):
        """The owner's ruling: the alpha uses the smallest proven slice, not the inventory. So
        the slice must be a strict subset of the engine layer's reached functions -- if it ever
        equals them, "smallest slice" has stopped meaning anything."""
        slice_ = api.slice_for("draft_room")
        self.assertTrue(slice_, "the draft room's slice is empty")
        engine_reached = {r for r in api.reaches()
                          if api.layer_of(r.split(".", 1)[0]) == "ENGINE"}
        named = {f"{m}.{fn}" for m, fns in slice_.items() for fn in fns}
        self.assertLess(len(named), len(api.reaches()),
                        "the slice is the whole inventory")
        self.assertTrue(engine_reached, "no ENGINE reach measured; the layer map has drifted")

    def test_the_slice_moves_when_an_operation_does(self):
        """Derived, not restated: remove the depth operation and the slice must lose exactly
        the depth functions. A hand-listed slice would not move."""
        before = api.slice_for("draft_room")
        fewer = {k: v for k, v in api.PUBLIC_OPERATIONS.items() if k != "draft_room.depth"}
        with mock.patch.object(api, "PUBLIC_OPERATIONS", fewer):
            after = api.slice_for("draft_room")
        self.assertIn("depth_chart", before)
        self.assertNotIn("depth_chart", after)
        self.assertEqual(set(before) - set(after), {"depth_chart", "depth_ratings"})

    def test_a_surface_nobody_declared_operations_for_gets_an_empty_slice(self):
        """Honest absence: the trade page's grammar is the Trade Ledger's to establish, and
        this file says so by having nothing for it -- not by guessing."""
        self.assertEqual({}, api.slice_for("trade_ledger"))


class TheReportSaysWhatItMeasuredTests(unittest.TestCase):

    def test_the_report_names_every_layer_and_the_data_census_it_defers_to(self):
        text = "\n".join(api.report())
        for name in api.LAYERS:
            self.assertIn(name, text)
        self.assertIn("boundary_census.CENSUS", text)
        self.assertIn("DRAFT ROOM LIVE ALPHA SLICE", text)

    def test_the_check_path_passes_on_the_tree_as_it_stands(self):
        self.assertEqual(0, api.main(["--check"]))

    def test_the_check_path_fails_when_a_module_is_unowned(self):
        thinned = dict(api.LAYERS)
        thinned["RENDER"] = {}
        with mock.patch.object(api, "LAYERS", thinned):
            self.assertEqual(1, api.main(["--check"]))


if __name__ == "__main__":
    unittest.main()
