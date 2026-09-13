"""Every board a PERSON drafts against is priced the way the league's own scoring prices it.

`#253`. `sleeper_projections` is the per-player season stat line that lets the league's own
scoring reach a price (`#180`/`#192`). Production built a board at four live sites and passed it
at one. Measured on the same league and the same 180-pick board, with the pricing path as the
only variable:

    DRAFT ROOM pricing   481 priced -> 301   3 positions measurable at EVERY sample
    MOCK DRAFT pricing   256 priced ->  86   measurable 3 -> 2 -> 1 -> 0 by pick 108

Pick 108 of 180 is round 10 of 15, and from there the draft-horizon layer placed no floor at
all. The estimator was never at fault; half the board was never priced.

WHY THE CALL-SITE SCAN IS DERIVED RATHER THAN A LIST. The defect was not a wrong value at a
known place -- it was a place nobody had enumerated. `build_snapshot`'s own comment recorded the
reasoning that produced it: *"Passing None keeps the previous behaviour exactly, which is what
every offline caller and every test does."* Three of the four were not offline callers. A test
that hand-listed today's sites would pass forever while a fifth surface was added beside them,
so these read `app.py`'s OWN syntax tree and hold every call they find (`#126`: one home for a
vocabulary, derived, never hand-listed).

`app.py` is the live surface by construction -- it is the Streamlit script a person interacts
with. Measurement harnesses (`draft_counterfactual`, `roster_diagnostics`, the `run_*` probes)
legitimately build unpriced boards for their own purposes and are not scanned, which is why the
scan is scoped to the file rather than to the function names globally.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

import draft_room as dr

APP = Path(__file__).with_name("app.py")

#: The live board builders. A call to either of these from app.py puts a board in front of a
#: person, so each one must carry the league's own pricing.
LIVE_BUILDERS = ("build_snapshot", "simulate_opponent_picks")

PRICING_KWARG = "sleeper_projections"


def live_calls(tree: ast.AST) -> list[tuple[str, int, set[str]]]:
    """(builder name, line, kwargs supplied) for every call to a LIVE_BUILDERS function."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in LIVE_BUILDERS:
            out.append((name, node.lineno, {kw.arg for kw in node.keywords if kw.arg}))
    return out


class EveryLiveBoardIsPricedByTheLeaguesOwnScoring(unittest.TestCase):
    """The ratchet. It reads app.py's real syntax tree, so a new surface is covered the day it
    is written rather than the day someone remembers to add it here."""

    @classmethod
    def setUpClass(cls):
        cls.calls = live_calls(ast.parse(APP.read_text(encoding="utf-8")))

    def test_the_scan_finds_the_live_builders_at_all(self):
        """Non-vacuity. A scan that matched nothing would pass every assertion below while
        defending nothing -- the vacuous-test shape this repo's mutation passes exist to find."""
        self.assertGreaterEqual(len(self.calls), 4, f"found only {self.calls}")
        found = {name for name, _, _ in self.calls}
        self.assertEqual(found, set(LIVE_BUILDERS))

    def test_every_live_board_call_passes_the_pricing(self):
        """The claim itself. Before #253 this failed on three of four calls."""
        missing = [(n, ln) for n, ln, kws in self.calls if PRICING_KWARG not in kws]
        self.assertEqual(missing, [], f"app.py builds an unpriced live board at {missing}")

    def test_every_live_board_call_also_states_its_basis(self):
        """A season-summed stat line read as a weekly one is off by a factor of the season's
        length. The projections and the basis travel together or neither is meaningful."""
        missing = [(n, ln) for n, ln, kws in self.calls if "sleeper_basis" not in kws]
        self.assertEqual(missing, [], f"pricing passed without its basis at {missing}")


class TheScanWouldActuallyCatchAnUnpricedSite(unittest.TestCase):
    """Non-vacuity for the ratchet above, proven against synthetic trees rather than by
    trusting that the real file happens to exercise both branches."""

    def test_a_call_without_the_kwarg_is_reported_missing(self):
        tree = ast.parse("pick_synthesis.build_snapshot(a, b, league=L)")
        calls = live_calls(tree)
        self.assertEqual(len(calls), 1)
        self.assertNotIn(PRICING_KWARG, calls[0][2])

    def test_a_call_with_the_kwarg_is_reported_present(self):
        tree = ast.parse("pick_synthesis.build_snapshot(a, sleeper_projections=p)")
        calls = live_calls(tree)
        self.assertEqual(len(calls), 1)
        self.assertIn(PRICING_KWARG, calls[0][2])

    def test_an_unrelated_call_is_not_matched(self):
        self.assertEqual(live_calls(ast.parse("compute_draft_board(a, b)")), [])


class SimulateOpponentPicksForwardsThePricing(unittest.TestCase):
    """The behavioural half. The AST scan proves app.py HANDS OVER the projections;
    this proves simulate_opponent_picks does not then drop them on the floor -- which is
    exactly what it did before #253, one function call below a correct caller."""

    def test_the_projections_and_basis_reach_compute_draft_board(self):
        seen = []
        real = dr.compute_draft_board
        dr.compute_draft_board = lambda *a, **k: (seen.append(k), [])[1]
        try:
            dr.simulate_opponent_picks(
                [], ["1", "2"], my_roster_id="2", num_teams=2, merger=None, players_db={},
                league={"roster_positions": ["QB"], "total_rosters": 2},
                sleeper_projections={"99": {"pass_yd": 4000}},
                sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            )
        finally:
            dr.compute_draft_board = real
        self.assertEqual(len(seen), 1, "no board was built; the forwarding was never exercised")
        self.assertEqual(seen[0].get("sleeper_projections"), {"99": {"pass_yd": 4000}})
        self.assertEqual(seen[0].get("sleeper_basis"), dr.SLEEPER_BASIS_SEASON_SUM)

    def test_absent_projections_stay_absent_rather_than_becoming_a_default(self):
        """The absence contract at the parameter boundary: a caller that supplies nothing must
        reach the board as None, not as an empty dict that reads like 'measured, and empty'."""
        seen = []
        real = dr.compute_draft_board
        dr.compute_draft_board = lambda *a, **k: (seen.append(k), [])[1]
        try:
            dr.simulate_opponent_picks(
                [], ["1", "2"], my_roster_id="2", num_teams=2, merger=None, players_db={},
                league={"roster_positions": ["QB"], "total_rosters": 2},
            )
        finally:
            dr.compute_draft_board = real
        self.assertEqual(len(seen), 1)
        self.assertIsNone(seen[0].get("sleeper_projections"))


if __name__ == "__main__":
    unittest.main()
