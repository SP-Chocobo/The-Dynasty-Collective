"""#190: a room's `count` and its `value` describe DIFFERENT SETS, in one cell.

positional_depth raises `count` for every rostered player and `value` only for the ones the
merger could price. They then travel together as if they were the same population, and the
League Depth Map renders `WR 7 (7)` -- seven receivers worth seven points -- when the truth was
seven receivers of whom ONE could be priced, at seven points.

MEASURED against the real capture on a synthetic 12-team league, 300 rostered players:

    cells fully priced (value IS the total)          7
    cells PARTIAL (value is a floor, shown as total) 33
    cells with nothing priced (value None, honest)  56
    players counted 300, contributing to value 90 (30.0%)

    worst: a 7-man WR room whose entire value came from one priced player.

THE 30% IS A FLOOR, NOT PRODUCTION'S RATE, and the test does not assert it. The synthetic
rosters take players off the top of the capture BY POSITION, which pulls in deep unmatched
players a real roster would not hold. What is established is the SHAPE -- partial cells exist
and were presented as totals -- which is what these tests pin.

WHY THE VALUE IS NOT WITHDRAWN. A partial sum is real evidence: three priced stars still
outrank three priced scrubs, and nulling the cell would destroy a measurement that was taken.
The repair is a companion, `valued_count`, so a consumer can say "at least" instead of "is".
Same shape as horizon_basis (#166), availability_basis (#191) and depth_basis (#174).
"""

from __future__ import annotations

import ast
import unittest

import ui_source


def _load_function(name: str):
    """Lift ONE function out of app.py and compile it alone.

    The UI surface is a top-level Streamlit script -- importing it executes page code and dies
    on a missing snapshot, which is why every other app-level test in this suite SOURCE-SCANS
    it rather than importing. Source-scanning proves a string is present; it cannot prove the
    arithmetic is right, and #190 is an arithmetic defect.

    So: parse the surface, take the single FunctionDef under test, and exec that one node in a
    clean namespace. It closes over nothing (its only collaborator is the merger it is handed),
    which is what makes this legitimate here and would not be for a function that reached for
    module state. The alternative -- moving it into an importable module -- is the hull
    extraction (#137), a tracked refactor a test file has no business doing on its own.

    READ THROUGH ui_source.text(), NEVER app.py OFF DISK. test_ui_source enforces that, and it
    caught the first version of this file: a test that reads app.py directly stops covering
    anything the moment #137 moves the view into its own module, and it does so silently.
    """
    tree = ast.parse(ui_source.text())
    fn = next(n for n in tree.body
              if isinstance(n, ast.FunctionDef) and n.name == name)
    fn.decorator_list = []          # @st.cache_data and friends need a live Streamlit
    ns: dict = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), "app.py", "exec"), ns)
    return ns[name]


positional_depth = _load_function("positional_depth")
depth_value_label = _load_function("depth_value_label")


class _Merger:
    """A merger that prices some names and declines others -- the whole point is the mixture."""

    is_loaded = True

    def __init__(self, priced: dict):
        self._priced = priced

    def merge_player(self, name, position=None, team=None):
        return {"trade_value": self._priced.get(name)}


def _universe(*rows):
    return [{"ownership": "ROSTERED", "owner_name": "Team A", "position": pos, "name": name,
             "team": "SF", "roster_id": 1} for name, pos in rows]


class TheCellStatesWhatItsValueCoversTests(unittest.TestCase):

    def test_a_fully_priced_room_reports_full_coverage(self):
        depth = positional_depth(
            _universe(("A", "WR"), ("B", "WR")), _Merger({"A": 10.0, "B": 5.0}))
        cell = depth["Team A"]["WR"]
        self.assertEqual((cell["count"], cell["valued_count"], cell["value"]), (2, 2, 15.0))

    def test_a_PARTIALLY_priced_room_reports_partial_coverage(self):
        depth = positional_depth(
            _universe(("A", "WR"), ("B", "WR"), ("C", "WR")), _Merger({"A": 10.0}))
        cell = depth["Team A"]["WR"]
        self.assertEqual(cell["count"], 3)
        self.assertEqual(cell["valued_count"], 1, "the scope of the sum is not recorded")
        self.assertEqual(cell["value"], 10.0, "the partial sum was withdrawn rather than scoped")

    def test_an_unpriced_room_keeps_value_absent_and_coverage_zero(self):
        depth = positional_depth(_universe(("A", "WR"), ("B", "WR")), _Merger({}))
        cell = depth["Team A"]["WR"]
        self.assertIsNone(cell["value"])
        self.assertEqual(cell["valued_count"], 0)

    def test_coverage_never_exceeds_the_count(self):
        depth = positional_depth(
            _universe(("A", "WR"), ("B", "RB")), _Merger({"A": 1.0, "B": 2.0}))
        for positions in depth.values():
            for cell in positions.values():
                self.assertLessEqual(cell["valued_count"], cell["count"])

    def test_a_cell_with_no_merger_loaded_states_zero_coverage_not_absence_of_the_field(self):
        # "work with whatever is loaded" still has to say what it worked with.
        class _Unloaded:
            is_loaded = False

            def merge_player(self, *a, **k):  # pragma: no cover - never called
                raise AssertionError("must not be consulted when unloaded")

        depth = positional_depth(_universe(("A", "WR")), _Unloaded())
        cell = depth["Team A"]["WR"]
        self.assertEqual(cell["count"], 1)
        self.assertIsNone(cell["value"])
        self.assertEqual(cell["valued_count"], 0)


class TheProseSaysAtLeastWhenItMeansAtLeastTests(unittest.TestCase):
    """The chair-facing half, exercising THE SHIPPED FUNCTION.

    A MUTATION SURVIVED THE FIRST VERSION OF THIS CLASS, and that is why the label now lives in
    a named function at all. The tests originally reproduced the label logic locally and pinned
    the shipped code with a source scan for the format string. A mutation that disabled the
    partial-coverage BRANCH -- so a partial sum rendered as a plain total again, the exact
    user-visible defect -- left the format string untouched and passed all nine tests. A guard
    that checks a string is present cannot see a branch go dead. The clause was extracted to
    depth_value_label so a test can call the real thing.
    """

    def test_full_coverage_reads_as_a_plain_total(self):
        self.assertEqual(depth_value_label({"count": 3, "value": 30.0, "valued_count": 3}), " (30)")

    def test_partial_coverage_reads_as_a_floor_and_names_the_gap(self):
        out = depth_value_label({"count": 7, "value": 7.0, "valued_count": 1})
        self.assertIn(">=7", out)
        self.assertIn("1 of 7 priced", out)
        self.assertNotEqual(out, " (7)", "a partial sum rendered as a plain total")

    def test_no_coverage_says_nothing_rather_than_zero(self):
        self.assertEqual(depth_value_label({"count": 3, "value": None, "valued_count": 0}), "")

    def test_a_cell_with_no_coverage_field_at_all_is_not_silently_called_complete(self):
        # An older cell shape reaching this label must not be upgraded to "total" by accident.
        self.assertEqual(depth_value_label({"count": 3, "value": 30.0}), " (30)")

    def test_the_screen_actually_calls_it(self):
        # The function must be WIRED, not merely present -- #57's lesson, one screen over.
        self.assertIn("depth_value_label(cell)", ui_source.text())


if __name__ == "__main__":
    unittest.main()
