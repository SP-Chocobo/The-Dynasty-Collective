"""`#346` — an unpriced player is not a player worth zero, and a cleared week has no loss.

Both defects were found by a subagent sent to DRAW a page, not by a test, and both had survived
every existing test because the suite watched what the engine computed and never what the
CAPTURE wrote down. These tests watch the capture's output contract and the reduction's output
shape, which is where both lived.

WHY THESE FAIL ON THE OLD CODE, which is the only property that makes them worth having:

  defect 1  the old fixtures carry no `priced` key at all, so every assertion about it raises
            KeyError / reads None on the pre-fix fixture.
  defect 2  `byes_ahead` returned `worst_week_loss` unchanged when it cleared `worst_week`, so
            `test_cleared_week_takes_its_loss_with_it` reads 68.0 where it wants None.
"""
from __future__ import annotations

import glob
import json
import pathlib
import unittest

import front_claims as fc
import lineup_optimizer as lo

ROOT = pathlib.Path(__file__).resolve().parent
FIXTURES = [ROOT / "ui_explore" / "front_fixture.json",
            ROOT / "ui_explore" / "quiet_fixture.json",
            *sorted(pathlib.Path(p) for p in glob.glob(str(ROOT / "ui_explore" / "seats" / "seat*.json")))]


def _rosters():
    for path in FIXTURES:
        fx = json.loads(path.read_text())
        yield path.name, (fx.get("roster") or [])


class PricedTravelsWithValue(unittest.TestCase):
    """DEFECT 1: `trade_value or 0.0` made "no price" and "priced at zero" the same number."""

    def test_every_rostered_player_carries_priced(self):
        """The field must exist on EVERY row, not only the interesting ones.

        A field that appears only when false is a field a reader cannot trust the absence of
        (`#187`): they could not tell "this player is priced" from "this capture predates the
        field". FAILS ON THE OLD FIXTURES, which have no `priced` key anywhere.
        """
        missing = [(name, p.get("name"))
                   for name, roster in _rosters() for p in roster if "priced" not in p]
        self.assertEqual(missing, [], f"rows with no `priced` field: {missing[:6]}")

    def test_priced_is_a_bool_and_never_a_stand_in(self):
        for name, roster in _rosters():
            for p in roster:
                self.assertIsInstance(
                    p.get("priced"), bool,
                    f"{name}: {p.get('name')} has priced={p.get('priced')!r}, not a bool")

    def test_value_is_always_a_number_because_the_solvers_negate_it(self):
        """NOT None, and this is the measured reason the fix is a companion field.

        `optimize_lineup` and `bye_collision` build a maximisation by negating the value, and
        both raise `TypeError: bad operand type for unary -: 'NoneType'` on a None. So the
        obvious repair -- write None when there is no price -- replaces a quiet wrong number
        with a crash. This test exists to stop a future reader making that repair.
        """
        for name, roster in _rosters():
            for p in roster:
                self.assertIsInstance(p.get("value"), (int, float),
                                      f"{name}: {p.get('name')} value={p.get('value')!r}")
                self.assertIsNotNone(p.get("value"))

    def test_unpriced_players_exist_and_are_not_merely_zero_valued(self):
        """The distinction has to be LIVE in the committed fixtures, not just supported.

        If no fixture carried an unpriced player, every other test here would pass vacuously
        and the field would be untested decoration -- the "measured and rejected" failure in
        miniature. Measured at the time of writing: 23 of 192 rows across the twelve seats.
        """
        unpriced = [(name, p.get("name"))
                    for name, roster in _rosters() for p in roster if p.get("priced") is False]
        self.assertGreater(len(unpriced), 0,
                           "no fixture carries an unpriced player, so this contract is untested")
        for name, who in unpriced:
            self.assertTrue(who, f"{name}: an unpriced row with no name")

    def test_a_zero_value_does_not_imply_unpriced(self):
        """The inverse error, which `or 0.0` would also have produced if reversed.

        A player measured at 0.0 IS priced. Any rule keyed on truthiness collapses the two
        again, so this asserts the two facts are independent rather than one deriving from the
        other.
        """
        for name, roster in _rosters():
            for p in roster:
                if p.get("priced") is False:
                    self.assertEqual(
                        p.get("value"), 0.0,
                        f"{name}: {p.get('name')} is unpriced but carries value "
                        f"{p.get('value')!r} -- an unpriced row must stand at the neutral 0.0 "
                        f"the solvers need, with `priced` carrying the real fact")

    def test_the_solvers_still_accept_the_row_shape(self):
        """An added field must not break the consumers it was added for.

        `bye_collision` is run over the real committed roster; it raises on a None value and is
        indifferent to extra keys. This is the check that the companion-field shape (`#190`) is
        actually compatible, rather than merely tidier on paper.
        """
        fx = json.loads((ROOT / "ui_explore" / "front_fixture.json").read_text())
        # `eligible` IS A STRING IN THE FIXTURE, not a set: the capture serializes with
        # `json.dumps(..., default=str)`, which silently turns a set into its repr. The solver
        # does `player["eligible"] & slot["eligible"]` and raises
        # `TypeError: unsupported operand type(s) for &: 'str' and 'set'`.
        #
        # So this test rebuilds the sets rather than trusting the file -- and the fact that it
        # HAS to is a separate finding, recorded as `#351`: the same `default=str` also
        # stringified `_provenance.players_db`, which is why the dashboard renders its capture
        # date as an absence. Not fixed here; fixing the serializer changes every fixture's
        # bytes and belongs in its own pass with its own suite run.
        roster = [dict(r, eligible={r.get("position")}) for r in fx["roster"]]
        slots = (fx.get("league") or {}).get("roster_positions") or []
        out = lo.bye_collision(roster, slots)
        # Keyed BY WEEK, each value a record carrying `value_lost`. Asserted against what the
        # function returns rather than what it sounded like it should return -- the first draft
        # of this test looked for a "weeks" key that does not exist, and would have passed on a
        # function that returned an empty dict.
        self.assertIsInstance(out, dict)
        self.assertTrue(out, "the solver returned nothing for a roster with known byes")
        for week, rec in out.items():
            self.assertIsInstance(rec.get("value_lost"), (int, float),
                                  f"week {week} has no numeric value_lost: {rec!r}")
        self.assertEqual(out[6]["value_lost"], 95.0,
                         "the solver's answer moved when only a companion field was added")


class ClearedWeekTakesItsLossWithIt(unittest.TestCase):
    """DEFECT 2: `byes_ahead` cleared `worst_week` and left `worst_week_loss` behind."""

    PROFILE = {"weeks": {"5": 10.0, "6": 68.0, "7": 12.0},
               "worst_week": 6, "worst_week_loss": 68.0,
               "worst_week_detail": {"starters_out": 2},
               "concentration": 0.4, "total_loss": 90.0}

    def test_cleared_week_takes_its_loss_with_it(self):
        """THE ACTUAL DEFECT. Fails on the old code, which returned worst_week_loss=68.0."""
        out = fc.byes_ahead(self.PROFILE, current_week=15)
        self.assertIsNone(out["worst_week"])
        self.assertIsNone(out["worst_week_loss"],
                          "a loss survived the week it belongs to being cleared")
        self.assertIsNone(out.get("worst_week_detail"))
        self.assertTrue(out["_ahead_only"])

    def test_a_week_still_ahead_keeps_its_figure(self):
        """The fix must not empty the field in the case that HAS an answer."""
        out = fc.byes_ahead(self.PROFILE, current_week=6)
        self.assertEqual(out["worst_week"], 6)
        self.assertEqual(out["worst_week_loss"], 68.0)
        self.assertEqual(set(out["weeks"]), {"6", "7"})

    def test_no_current_week_leaves_the_profile_alone(self):
        """With no clock there is no futurity to establish, so nothing is reduced or cleared."""
        out = fc.byes_ahead(self.PROFILE, current_week=None)
        self.assertEqual(out["worst_week"], 6)
        self.assertEqual(out["worst_week_loss"], 68.0)
        self.assertNotIn("_ahead_only", out)

    def test_the_season_shape_survives_so_a_surface_can_say_all_behind(self):
        """The documented asymmetry, pinned so it cannot be 'tidied' into a bug.

        With weeks ahead, `weeks` is reduced to them. With NONE ahead, `weeks` keeps the season
        so a surface can say "all seven are behind week 15" instead of rendering an empty
        ledger. Emptying it here would look more consistent and would silently blank the quiet
        state's best panel.
        """
        out = fc.byes_ahead(self.PROFILE, current_week=15)
        self.assertEqual(set(out["weeks"]), {"5", "6", "7"})

    def test_compose_never_emits_a_bye_claim_without_both_halves(self):
        """The end-to-end guard: no claim may carry a figure whose subject is None."""
        fx = {"bye_profile": self.PROFILE, "current_week": 15,
              "thin_positions": [], "structural_holes": []}
        band = fc.compose(fx)
        for c in band["shown"] + band["hidden"]:
            if c["kind"] == "bye":
                self.assertIsNotNone(c.get("worst_week"))
                self.assertIsNotNone(c.get("worst_week_loss"))
        bp = band["bye_profile"]
        if bp.get("worst_week") is None:
            self.assertIsNone(bp.get("worst_week_loss"),
                              "compose returned a profile carrying an orphaned loss")


if __name__ == "__main__":
    unittest.main()
