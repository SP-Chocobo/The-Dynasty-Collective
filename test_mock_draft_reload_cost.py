"""CHARACTERIZATION (#52, K-07) -- invert on repair. The mock draft reloads the merger twice
per rerun, and each reload throws away every merged row.

`DataMerger.set_league_format` is a cheap no-op when the format is unchanged and a full
`reload()` when it is not. The UI asserts a format at two places:

  * once at the top of EVERY rerun, with the active real league's format;
  * once inside the Mock Draft view, with the mock's own chosen format.

Those two formats differ whenever the mock is configured differently from the live league --
which is the ordinary case, since configuring a different format is what the mock is for. So a
single rerun in that view pays `reload()` twice: once going in, once coming back.

MEASURED, on the committed baseline:

  unchanged format (the no-op)     0.0 ms
  format change -> reload()      333.2 ms
  change back   -> reload()      319.3 ms
  ONE mock-view rerun            652.5 ms   against 0.0 ms for the same rerun elsewhere

And the reload is only the visible half. `_load()` reinstates an empty `_merge_memo`, verified
here rather than assumed, so every merged row computed for the previous board is discarded and
the next board is built cold. The original finding measured that downstream cost at **0.87 s
warm against 18.0-18.9 s cold**, paid on every button click in the view.

WHY THIS IS PINNED RATHER THAN FIXED. It is latency, not a truth defect: no number the engine
reports is wrong because of it. The fix lives in Streamlit rerun sequencing, which cannot be
executed or verified from the audit sandbox, and a wrong fix silently breaks the mock draft --
a real regression traded for a speedup. The owner ruled it a gate for `v2-freeze` as a PIN:
convert a known defect into a guarded one, at a fraction of the risk of repairing it blind.

What a repair would look like, so this file names its own exit: assert the mock's format once
and let the top-of-rerun assertion see it (or scope a second merger to the mock view), so a
rerun performs at most one reload. When that lands, `test_the_ui_asserts_two_different_formats_
per_rerun` fails -- which is the signal, not a nuisance.
"""

from __future__ import annotations

import ast
import unittest

import data_merger as dm
import ui_source


class TheReloadMechanismTests(unittest.TestCase):
    """The behaviour the cost rests on, checked against the real class rather than described."""

    def setUp(self):
        self.merger = dm.DataMerger()
        self.real = {"scoring": "ppr", "superflex": False, "te_premium": False}
        self.mock = {"scoring": "half_ppr", "superflex": True, "te_premium": True}

    def test_an_unchanged_format_is_a_no_op(self):
        """The property that makes calling it every rerun safe -- and the reason the SECOND
        call site is what costs, not the first."""
        self.merger.set_league_format(self.real)
        loaded = self.merger.projections
        self.merger.set_league_format(self.real)
        self.assertIs(self.merger.projections, loaded,
                      "an unchanged format must not rebuild anything")

    def test_a_changed_format_reloads(self):
        """Non-vacuity for the test above: it must not be a no-op for everything."""
        self.merger.set_league_format(self.real)
        loaded = self.merger.projections
        self.merger.set_league_format(self.mock)
        self.assertIsNot(self.merger.projections, loaded)

    def test_the_reload_discards_every_merged_row(self):
        """The half that costs 18 seconds downstream, verified rather than inferred from the
        finding: the memo is not invalidated selectively, it is replaced empty."""
        self.merger.set_league_format(self.real)
        self.merger.merge_player("Justin Jefferson")
        self.assertGreater(len(self.merger._merge_memo), 0,
                           "nothing was memoised -- this test would then prove nothing")
        self.merger.set_league_format(self.mock)
        self.assertEqual(len(self.merger._merge_memo), 0)


class TheUiPaysItTwicePerRerunTests(unittest.TestCase):
    """The wiring, over the UI's own syntax tree. This is what changes when the defect is fixed."""

    @classmethod
    def setUpClass(cls):
        cls.calls = [(unit, node)
                     for unit, src in sorted(ui_source.units().items())
                     for node in ast.walk(ast.parse(src))
                     if isinstance(node, ast.Call)
                     and getattr(node.func, "attr", None) == "set_league_format"]

    def test_the_ui_asserts_two_different_formats_per_rerun(self):
        """THE CHARACTERIZATION. Two call sites, reached in the same rerun in the mock view,
        carrying different formats -- so the second reloads going in and the first reloads
        coming back on the next rerun.

        A repair makes this ONE, and this assertion fails. That is the signal it exists for.
        Three would be a new call site nobody costed, which is the other direction it guards.
        """
        self.assertEqual(len(self.calls), 2,
                         f"expected exactly two set_league_format call sites in the UI, found "
                         f"{[f'{u}:{n.lineno}' for u, n in self.calls]}")

    def test_one_of_them_carries_the_mock_drafts_own_settings(self):
        """Which of the two is the costly one, named so a reader can find it. The mock's call
        takes its scoring from the mock settings dict, not from the live league."""
        rendered = [ast.unparse(node) for _, node in self.calls]
        mock_calls = [r for r in rendered if "settings[" in r]
        self.assertEqual(len(mock_calls), 1,
                         f"exactly one call should read the mock's own settings: {rendered}")

    def test_the_other_is_the_unconditional_top_of_rerun_assertion(self):
        """And the cheap one, which is only cheap while nothing else has moved the format."""
        rendered = [ast.unparse(node) for _, node in self.calls]
        self.assertTrue(any("_scoring_key" in r for r in rendered),
                        f"the top-of-rerun call should assert the live league's format: {rendered}")


if __name__ == "__main__":
    unittest.main()
