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

The UI surface is the live surface by construction -- it is what a person interacts with.
Measurement harnesses (`draft_counterfactual`, `roster_diagnostics`, the `run_*` probes)
legitimately build unpriced boards for their own purposes and are not scanned, which is why the
scan is scoped to that surface rather than to the function names globally.

READ THROUGH `ui_source`, NOT OFF `app.py` (#52 phase 7.4). This read `app.py` directly, which
is the one file the Draft Room lives in today and is slated to move out of by view. A scan
pointed at a file the code has left covers nothing, and `test_ui_source` exists to stop exactly
that -- it did not catch this one, because the path and the read sat on two different lines and
its scan was per-line. Both are fixed: this file asks `ui_source` for the surface, and that scan
now reads code rather than lines.
"""

from __future__ import annotations

import ast
import unittest

import draft_room as dr
import ui_source

#: The live board builders. A call to either of these from app.py puts a board in front of a
#: person, so each one must carry the league's own pricing.
LIVE_BUILDERS = ("build_snapshot", "simulate_opponent_picks")

PRICING_KWARG = "sleeper_projections"


#: The sentinel a call gets when it forwards a **mapping this scan could not read. It is a
#: NAME no real parameter can have, so it satisfies no assertion below and every check reports
#: the call as missing whatever it was looking for. Silence would make `**anything` a universal
#: bypass of this whole file.
UNRESOLVED = "<unresolved **kwargs>"


def _mapping_keys(tree: ast.AST, name: str) -> set[str] | None:
    """The keys of a dict built as `name = dict(k=v, ...)` or `name = {"k": v, ...}`.

    None when the name has no such assignment in this tree, or has more than one -- two
    assignments mean the keys at the call depend on which ran, and a scan that picked either
    would be reporting on a call that may not happen. Unknown is reported as unknown.
    """
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        value = node.value
        if isinstance(value, ast.Dict):
            if not all(isinstance(k, ast.Constant) and isinstance(k.value, str)
                       for k in value.keys):
                return None          # a computed key is a key this scan cannot name
            found.append({k.value for k in value.keys})
        elif (isinstance(value, ast.Call)
              and getattr(value.func, "id", None) == "dict"
              and not value.args):
            if any(kw.arg is None for kw in value.keywords):
                return None          # dict(**other) -- one more layer than this reads
            found.append({kw.arg for kw in value.keywords})
        else:
            return None
    return found[0] if len(found) == 1 else None


def live_calls(tree: ast.AST, unit: str = "app.py") -> list[tuple[str, int, set[str]]]:
    """(builder name, line, kwargs supplied) for every call to a LIVE_BUILDERS function.

    FOLLOWS `**mapping` (#52 phase 7.4). The Draft Room's build_snapshot call now passes one
    dict that its cache key is derived from at the same time, so the arguments cannot be
    described one way for the key and another for the call. That is better code and this scan
    could not read it: `**d` is a keyword whose `arg` is None, so the call presented as having
    NO kwargs at all and both assertions below failed on a site that was passing the pricing
    correctly. A scan that made the code worse to stay green would be worth less than no scan.

    A mapping this cannot resolve yields UNRESOLVED rather than nothing, so the call still
    fails every check. The alternative -- treating an unreadable `**mapping` as satisfying the
    scan -- would turn the one shape this file cannot see into the one shape a future unpriced
    site could hide in.
    """
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in LIVE_BUILDERS:
            continue
        supplied = {kw.arg for kw in node.keywords if kw.arg}
        for keyword in node.keywords:
            if keyword.arg is not None:
                continue
            resolved = (_mapping_keys(tree, keyword.value.id)
                        if isinstance(keyword.value, ast.Name) else None)
            supplied |= resolved if resolved is not None else {UNRESOLVED}
        out.append((name, f"{unit}:{node.lineno}", supplied))
    return out


class EveryLiveBoardIsPricedByTheLeaguesOwnScoring(unittest.TestCase):
    """The ratchet. It reads app.py's real syntax tree, so a new surface is covered the day it
    is written rather than the day someone remembers to add it here."""

    @classmethod
    def setUpClass(cls):
        # Per UNIT, not over the concatenation: ui_source.text() joins the modules, and a line
        # number taken from the join names no line in any file a person can open. Each unit is
        # parsed on its own so a failure says which file and which line.
        cls.calls = [(name, lineno, kwargs)
                     for unit, source in sorted(ui_source.units().items())
                     for name, lineno, kwargs in live_calls(ast.parse(source), unit)]

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

    def test_a_kwarg_forwarded_through_a_dict_is_seen(self):
        """The shape app.py actually uses. Without this the real scan reported a correctly
        priced site as unpriced."""
        tree = ast.parse("d = dict(league=L, sleeper_projections=p, sleeper_basis=b)\n"
                         "pick_synthesis.build_snapshot(**d)\n")
        calls = live_calls(tree)
        self.assertEqual(len(calls), 1)
        self.assertIn(PRICING_KWARG, calls[0][2])
        self.assertIn("sleeper_basis", calls[0][2])

    def test_a_dict_literal_is_read_the_same_way(self):
        tree = ast.parse('d = {"sleeper_projections": p}\n'
                         "pick_synthesis.build_snapshot(**d)\n")
        self.assertIn(PRICING_KWARG, live_calls(tree)[0][2])

    def test_a_dict_that_omits_the_pricing_is_still_reported_missing(self):
        """The non-vacuity arm. Following the dict must not mean accepting every dict -- a
        forwarding shape that hid an unpriced call would be worse than the scan's blind spot,
        because it would look like coverage."""
        tree = ast.parse("d = dict(league=L)\npick_synthesis.build_snapshot(**d)\n")
        self.assertNotIn(PRICING_KWARG, live_calls(tree)[0][2])

    def test_an_unreadable_mapping_fails_the_scan_rather_than_passing_it(self):
        """`**anything` must not become a universal bypass. Each of these is a mapping this
        scan cannot name the keys of, and each must leave the call failing every assertion."""
        for source in (
            "pick_synthesis.build_snapshot(**somewhere_else)",          # no assignment here
            "d = build_it()\npick_synthesis.build_snapshot(**d)",        # not a literal
            "d = dict(**base)\npick_synthesis.build_snapshot(**d)",      # one layer deeper
            "d = {k: v}\npick_synthesis.build_snapshot(**d)",            # computed key
            "d = dict(sleeper_projections=p)\nd = dict(league=L)\n"
            "pick_synthesis.build_snapshot(**d)",                       # two assignments
        ):
            calls = live_calls(ast.parse(source))
            self.assertEqual(calls[0][2], {UNRESOLVED}, source)
            self.assertNotIn(PRICING_KWARG, calls[0][2], source)


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
