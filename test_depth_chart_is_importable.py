"""The depth chart has ONE home, and that home can be imported without a Streamlit session.

WHAT THESE PIN, AND WHY EACH COULD SILENTLY COME BACK. `positional_depth` and `depth_value_label`
lived in `app.py`, which has 69 top-level Streamlit calls and no `__main__` guard, so importing it
runs the application. A quantity three surfaces depend on therefore had no reader outside the app:
`test_positional_depth_coverage` reached it by parsing the surface and exec-ing one FunctionDef,
and `depth_value_label` existed as a named function rather than an inline ternary *because* that
was the only way a test could reach the behaviour at all. Both facts were written down as
workarounds in their own docstrings.

Moving the pair into `depth_chart.py` (a scoped piece of `#137`) removes the need for both. These
tests defend the three properties that purchase is made of, and none of them is self-evident:

  1. THE MODULE IMPORTS WITHOUT STREAMLIT. One `import streamlit` added to `depth_chart.py` --
     or an `import app` reached for in a hurry -- and every harness, fixture and prototype that
     can read this quantity stops being able to. Checked in a SUBPROCESS, because by the time
     this file runs in the full suite another module has long since imported Streamlit into
     `sys.modules` and an in-process check would pass on someone else's import.
  2. `app.py` DOES NOT DEFINE THEM AGAIN. The failure mode is not exotic: the next person who
     wants this logic in the hull writes a local copy, and now there are two implementations of
     one quantity (`#126`) that agree until one is fixed. A top-level `def` of either name
     anywhere on the UI surface is the thing to catch.
  3. ITS IMPORTS STAY AT ZERO. `draft_state.py` and `content_hash.py` take the same posture and
     say why: a module a test can import without standing anything up is the whole point. The
     runtime import list is asserted empty rather than merely small, because the first dependency
     is the one that makes the second look reasonable.
"""

from __future__ import annotations

import ast
import pathlib
import subprocess
import sys
import unittest

import ui_source

MODULE = pathlib.Path(__file__).parent / "depth_chart.py"
NAMES = ("positional_depth", "depth_value_label")


class DepthChartHasOneImportableHome(unittest.TestCase):

    def test_it_imports_without_pulling_in_streamlit(self):
        """A subprocess, so this measures OUR import and not the suite's accumulated state."""
        probe = ("import sys; import depth_chart; "
                 "bad = [m for m in ('streamlit', 'app') if m in sys.modules]; "
                 "print(','.join(bad))")
        out = subprocess.run([sys.executable, "-c", probe], cwd=str(MODULE.parent),
                             capture_output=True, text=True, timeout=120)
        self.assertEqual(out.returncode, 0, f"depth_chart did not import cleanly:\n{out.stderr}")
        self.assertEqual(out.stdout.strip(), "",
                         "importing depth_chart dragged in a module that needs a live session; "
                         "that is the whole property this module was extracted to have")

    def test_it_imports_nothing_at_runtime(self):
        tree = ast.parse(MODULE.read_text())
        runtime = []
        for node in tree.body:                       # top level only; the TYPE_CHECKING block is nested
            if isinstance(node, ast.Import):
                runtime += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module not in ("__future__",):
                runtime.append(node.module or "")
        self.assertEqual([m for m in runtime if m != "typing"], [],
                         f"depth_chart gained a runtime dependency ({runtime}); it is kept "
                         f"dependency-free so any harness can import it")

    def test_the_ui_surface_does_not_define_them_again(self):
        defined = [n.name for n in ast.walk(ast.parse(ui_source.text()))
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in NAMES]
        self.assertEqual(defined, [],
                         f"the UI surface defines {defined} again -- two implementations of one "
                         f"quantity is what moving it out was for (#126)")

    def test_the_ui_surface_imports_them_from_here(self):
        """Not defining them is half the claim; the hull must actually be using THIS home."""
        self.assertIn("from depth_chart import", ui_source.text())

    def test_both_names_are_reachable_and_callable(self):
        import depth_chart
        for name in NAMES:
            self.assertTrue(callable(getattr(depth_chart, name, None)),
                            f"depth_chart.{name} is not callable")


if __name__ == "__main__":
    unittest.main()
