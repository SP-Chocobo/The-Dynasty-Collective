"""ui_source's own coverage -- and the proof that the migration was worth doing.

Today `ui_source.text()` is byte-identical to `app.py`, so every migrated module passes for
the same reason it passed before, which proves nothing about the extraction it exists for.
These tests build a two-module UI surface in a temp directory and check the property that
actually matters: that a guard written against `app.py` keeps guarding after its subject
moves out of `app.py`.

`SilentVacuityTests` is the centre of the file. It runs the same `assertNotIn` twice against a
surface where the policed code has been extracted -- once the old way (read `app.py`) and once
through `ui_source` -- and shows the old way passing on nothing.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

import ui_source

_HERE = Path(__file__).parent

#: A minimal two-module UI surface: a hull plus one extracted view. `FORBIDDEN` is the kind of
#: thing an `assertNotIn` polices -- here, a raw secret read that must never appear in the UI.
FORBIDDEN = 'os.environ["ANTHROPIC_API_KEY"]'

_HULL_BEFORE = f'''\
import streamlit as st

def render_league():
    st.header("League")
    key = {FORBIDDEN}
    st.write(key)
'''

_HULL_AFTER = '''\
import streamlit as st
import view_league

view_league.render()
'''

_VIEW_AFTER = f'''\
import streamlit as st

def render():
    st.header("League")
    key = {FORBIDDEN}
    st.write(key)
'''


def _surface(**files: str) -> Path:
    """A temp directory holding a synthetic UI surface. Caller owns cleanup via addCleanup."""
    root = Path(tempfile.mkdtemp())
    for name, body in files.items():
        (root / name.replace("__", ".")).write_text(body)
    return root


class TodayThisIsANoOpTests(unittest.TestCase):
    """The migration must not change any assertion's meaning on the current tree.

    Twenty-two modules were rewritten in one pass. If `text()` differed from `app.py` by even
    a byte today, every one of those rewrites would be an unreviewed change to what a contract
    asserts, hidden inside a mechanical edit."""

    def test_the_surface_is_exactly_app_py(self):
        self.assertEqual(ui_source.modules(), ["app.py"],
                         "a second UI module appeared; this is the moment to check that every "
                         "migrated test still means what it meant")
        self.assertEqual(ui_source.text(), (_HERE / "app.py").read_text())

    def test_a_single_module_surface_carries_no_boundary_marker(self):
        """The separator is inserted only when there is something to separate."""
        self.assertNotIn("ui_source boundary", ui_source.text())


class SilentVacuityTests(unittest.TestCase):
    """THE POINT OF THIS MODULE. An absence-assertion must not go green by losing its subject.

    Eight `assertNotIn`s in this suite police the UI surface. Each one says "this forbidden
    pattern is nowhere in the UI." Read against `app.py` alone, extracting a view satisfies
    that sentence by removing the file the pattern was in -- not by removing the pattern. The
    test then passes forever, about nothing, and no failure ever announces it."""

    def setUp(self):
        self.before = _surface(app__py=_HULL_BEFORE)
        self.after = _surface(app__py=_HULL_AFTER, view_league__py=_VIEW_AFTER)

    def test_the_old_way_catches_it_before_the_extraction(self):
        """Baseline: reading app.py directly is a real guard while the code is still there."""
        self.assertIn(FORBIDDEN, (self.before / "app.py").read_text())

    def test_the_old_way_goes_silently_green_after_the_extraction(self):
        """The defect, demonstrated rather than asserted.

        The forbidden call still exists on the surface -- it just lives in view_league.py now.
        An `assertNotIn` against app.py alone would PASS here, and that pass is the bug."""
        app_only = (self.after / "app.py").read_text()
        self.assertNotIn(FORBIDDEN, app_only)          # the vacuous pass, made visible
        surface = "".join((self.after / n).read_text() for n in ("app.py", "view_league.py"))
        self.assertIn(FORBIDDEN, surface,
                      "the pattern really is still on the surface -- so the assertion above "
                      "passed by losing its subject, not by the subject being clean")

    def test_ui_source_still_catches_it_after_the_extraction(self):
        """The repair: the same guard, read through ui_source, still fires."""
        self.assertIn(FORBIDDEN, ui_source.text(root=self.after))

    def test_and_a_genuinely_clean_surface_still_passes(self):
        """Non-vacuity for the test above: it must not simply always find the pattern."""
        clean = _surface(app__py="import streamlit as st\nst.header('League')\n")
        self.assertNotIn(FORBIDDEN, ui_source.text(root=clean))


class TheModuleListIsDerivedTests(unittest.TestCase):
    """A hand-kept surface list rots the same way, one level up: extract a view, forget the
    list, and ui_source narrows back to app.py while every caller believes otherwise."""

    def test_a_new_streamlit_module_joins_the_surface_with_no_edit_here(self):
        root = _surface(app__py=_HULL_AFTER, view_league__py=_VIEW_AFTER)
        self.assertEqual(ui_source.modules(root=root), ["app.py", "view_league.py"])

    def test_app_py_leads_so_the_concatenation_order_is_stable(self):
        root = _surface(app__py=_HULL_AFTER, aaa_view__py=_VIEW_AFTER,
                        zzz_view__py=_VIEW_AFTER)
        self.assertEqual(ui_source.modules(root=root)[0], "app.py")

    def test_a_pure_module_is_not_part_of_the_surface(self):
        """The whole discipline this repo keeps -- one Streamlit importer, everything else
        pure -- is what makes the derivation rule sound."""
        root = _surface(app__py=_HULL_BEFORE, engine__py="def price(x):\n    return x * 2\n")
        self.assertEqual(ui_source.modules(root=root), ["app.py"])

    def test_tests_and_dev_scripts_are_not_the_surface(self):
        root = _surface(app__py=_HULL_BEFORE, test_thing__py=_HULL_BEFORE,
                        run_probe__py=_HULL_BEFORE, compare_two__py=_HULL_BEFORE)
        self.assertEqual(ui_source.modules(root=root), ["app.py"])

    def test_a_deferred_import_does_not_make_a_module_a_ui_surface(self):
        """Anchored at column zero on purpose: a module with a Streamlit call in some fallback
        path is not a view, and pulling it in would widen the surface silently."""
        root = _surface(app__py=_HULL_BEFORE,
                        helper__py="def maybe():\n    import streamlit as st\n    return st\n")
        self.assertEqual(ui_source.modules(root=root), ["app.py"])


class TheDerivationRulesPremiseTests(unittest.TestCase):
    """`ui_source` defines the UI surface as "imports Streamlit". That is only sound while
    rendering and importing Streamlit go together.

    The dodge the module's docstring named as a stated limitation -- a view that receives `st`
    as a parameter instead of importing it -- is enforced here instead of merely written down.
    Such a module would render UI, would be policed by nothing, and `ui_source` would never
    see it: the same silent narrowing this whole exercise exists to prevent, arriving through
    the one door the derivation cannot watch."""

    def _production_modules(self):
        for path in sorted(_HERE.glob("*.py")):
            if path.name.startswith(("test_", "run_", "compare_")):
                continue
            yield path

    def test_no_module_outside_the_surface_calls_streamlit(self):
        surface = set(ui_source.modules())
        offenders = []
        for path in self._production_modules():
            if path.name in surface:
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "st"):
                    offenders.append(f"{path.name}:{node.lineno} st.{node.attr}")
        self.assertEqual(offenders, [],
                         "a module renders UI without importing Streamlit, so ui_source cannot "
                         "see it and no source-scanning contract covers it. Import streamlit "
                         "in it, or stop rendering from it.")

    def test_the_scan_can_actually_see_a_streamlit_call(self):
        """Non-vacuity: the check above would also pass on a tree with no Streamlit anywhere."""
        found = []
        for node in ast.walk(ast.parse((_HERE / "app.py").read_text())):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "st"):
                found.append(node.attr)
        self.assertGreater(len(found), 100,
                           "the AST shape this scan looks for no longer matches how app.py "
                           "calls Streamlit, so the scan above is checking nothing")


class PositionIsAPerFileQuestionTests(unittest.TestCase):
    """Offsets into a concatenation are arithmetic on a ruler that does not exist."""

    def setUp(self):
        self.root = _surface(app__py=_HULL_AFTER, view_league__py=_VIEW_AFTER)

    def test_block_slices_the_file_holding_the_anchor(self):
        body = ui_source.block("def render():", root=self.root)
        self.assertIn(FORBIDDEN, body)
        self.assertNotIn("import view_league", body,
                         "the block reached into app.py, which does not contain its anchor")

    def test_a_block_cannot_run_past_the_end_of_its_own_module(self):
        body = ui_source.block("def render():", root=self.root)
        self.assertNotIn("ui_source boundary", body)

    def test_an_ambiguous_anchor_is_refused_rather_than_resolved(self):
        with self.assertRaises(AssertionError) as caught:
            ui_source.block("import streamlit as st", root=self.root)
        self.assertIn("cannot anchor a block", str(caught.exception))

    def test_a_missing_terminator_names_the_anchor_it_started_from(self):
        with self.assertRaises(AssertionError) as caught:
            ui_source.block("def render():", "# no such marker", root=self.root)
        self.assertIn("def render():", str(caught.exception))
        self.assertIn("view_league.py", str(caught.exception))

    def test_ordering_across_two_modules_is_refused_not_answered(self):
        with self.assertRaises(AssertionError) as caught:
            ui_source.offsets("import view_league", "def render():", root=self.root)
        self.assertIn("across UI modules", str(caught.exception))

    def test_ordering_within_one_module_still_works(self):
        first, second = ui_source.offsets("def render():", FORBIDDEN, root=self.root)
        self.assertLess(first, second)


class TheRealHullSurvivesARealSplitTests(unittest.TestCase):
    """The synthetic surface above proves the mechanism. This proves it on the actual file.

    A real block of `app.py` -- the Matchup view -- is carved into its own module in a temp
    directory, exactly as the extraction will do it, and every string the migrated suite
    asserts against the surface is looked for again on both sides of the change.

    The control does NOT go through `ui_source`: it is a plain read of the shrunken `app.py`,
    which is what the suite did before this module existed. Comparing ui_source against itself
    would measure nothing, and an instrument that shares code with its subject has stopped
    being an instrument."""

    #: A real boundary in app.py. If the extraction reaches Matchup first, these anchors move
    #: into the new view module and this test's setUp will fail loudly -- which is correct: it
    #: means the split it simulates has actually happened and the simulation needs a new seam.
    ANCHOR = "if main_view == MATCHUP_VIEW:"
    UNTIL = "elif main_view == MAINTENANCE_VIEW:"

    def setUp(self):
        app = (_HERE / "app.py").read_text()
        start = app.index(self.ANCHOR)
        end = app.index(self.UNTIL, start)
        self.carved = app[start:end]
        self.root = Path(tempfile.mkdtemp())
        (self.root / "app.py").write_text(app[:start] + app[end:] + "\nimport view_matchup\n")
        (self.root / "view_matchup.py").write_text(
            "import streamlit as st\n\n\n" + self.carved)

    def _surface_needles(self):
        """Every literal `assertIn` needle the migrated suite checks against the UI surface."""
        found = []
        for path in sorted(_HERE.glob("test_*.py")):
            source = path.read_text()
            if "import ui_source" not in source or path.name == Path(__file__).name:
                continue
            for node in ast.walk(ast.parse(source)):
                if not (isinstance(node, ast.Call)
                        and getattr(node.func, "attr", None) == "assertIn"
                        and node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)):
                    continue
                haystack = " ".join(ast.unparse(a) for a in node.args[1:])
                if any(k in haystack for k in ("ui_source.text()", "_APP", "app_source", "APP")):
                    found.append((f"{path.name}:{node.lineno}", node.args[0].value))
        return found

    def test_the_seam_this_simulation_uses_still_exists(self):
        """Non-vacuity: a carve of nothing would make every check below pass trivially."""
        self.assertGreater(len(self.carved), 2000,
                           "the Matchup block is gone or tiny -- pick a new seam")

    def test_the_suite_really_does_assert_against_the_surface(self):
        """Second non-vacuity guard: zero needles would also make both counts below zero."""
        self.assertGreater(len(self._surface_needles()), 40)

    def test_reading_app_py_alone_loses_coverage_when_a_view_moves(self):
        """The control, and the reason this whole module exists. Extracting ONE view already
        strands assertions -- and this is the loud half; the eight assertNotIns would have
        gone quiet instead."""
        app_only = (self.root / "app.py").read_text()
        lost = [where for where, needle in self._surface_needles() if needle not in app_only]
        self.assertGreater(len(lost), 0,
                           "no assertion was stranded by moving a whole view out of app.py, "
                           "which would mean the coverage this module protects is not there")

    def test_reading_through_ui_source_loses_none_of_it(self):
        surface = ui_source.text(root=self.root)
        lost = [f"{where} {needle[:60]!r}"
                for where, needle in self._surface_needles() if needle not in surface]
        self.assertEqual(lost, [],
                         "an assertion did not survive the split through ui_source, so the "
                         "migration does not do the one thing it was built for")


class NoTestReadsAppPyDirectlyTests(unittest.TestCase):
    """The guard that keeps the migration from rotting.

    Twenty-two modules were moved onto ui_source in one pass. Nothing stops the twenty-third
    from being written the old way -- `(_HERE / "app.py").read_text()` is still the obvious
    thing to type, and it would work perfectly until the day a view moves."""

    #: The one module allowed to read app.py off disk, with its reason -- same shape as
    #: test_store_io's ALLOWED, because a nameless self-exemption is how an exemption rots.
    ALLOWED = {
        "test_ui_source.py": "it demonstrates BOTH readings on purpose -- the old one to show "
                             "the vacuous pass, and app.py directly to prove today's migration "
                             "changed no assertion's meaning",
    }

    def test_the_allowance_states_a_reason(self):
        for name, reason in self.ALLOWED.items():
            with self.subTest(name=name):
                self.assertGreater(len(reason), 25, f"{name}'s exemption needs a real reason")

    def test_no_test_module_reads_app_py_off_disk(self):
        offenders = []
        for path in sorted(_HERE.glob("test_*.py")):
            if path.name in self.ALLOWED:
                continue
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "app.py" in stripped and "read_text" in stripped:
                    offenders.append(f"{path.name}:{lineno}")
        self.assertEqual(offenders, [],
                         "read the UI surface through ui_source.text() instead -- an app.py "
                         "read stops covering anything the moment a view is extracted")

    def test_the_migrated_modules_actually_import_it(self):
        """Non-vacuity for the scan above, which would also pass on a tree where no test
        looked at the UI at all. These are the modules the migration moved."""
        migrated = [
            "test_composite_admission_gate.py", "test_context_budget_boundary.py",
            "test_corpus_state.py", "test_cost_envelope_boundary.py",
            "test_data_semantics_boundary.py", "test_debate_chip_wiring.py",
            "test_display_contract_boundary.py", "test_failure_mode_boundary.py",
            "test_league_view_wiring.py", "test_maintenance_view_wiring.py",
            "test_matchup_view_wiring.py", "test_mock_draft_wiring.py",
            "test_override_provenance_boundary.py", "test_panel_independence.py",
            "test_prompt_constant_boundary.py", "test_provenance_boundary.py",
            "test_providers.py", "test_research_authority_boundary.py",
            "test_store_io.py", "test_temporal_consistency_boundary.py",
            "test_tenant_scope_boundary.py", "test_upload_batches.py",
        ]
        for name in migrated:
            with self.subTest(module=name):
                source = (_HERE / name).read_text()
                self.assertIn("import ui_source", source)
                self.assertIn("ui_source.", source)

    def test_no_migrated_module_subscripts_text_directly(self):
        """`ui_source.text()[a:b]` is the one way to reintroduce the bug through the fix: it
        looks migrated, and it slices across a boundary that will exist tomorrow."""
        offenders = []
        for path in sorted(_HERE.glob("test_*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Subscript):
                    continue
                inner = ast.unparse(node.value)
                if inner.endswith("ui_source.text()"):
                    offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(offenders, [],
                         "use ui_source.block() -- it slices the module holding the anchor, "
                         "instead of a concatenation whose offsets mean nothing")


if __name__ == "__main__":
    unittest.main()
