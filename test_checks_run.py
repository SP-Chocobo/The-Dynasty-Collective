"""`checks_run` / `CHECKS` / `checks_summary` -- what the band EXAMINED, not only what it
found (`#338`). Recorded as "CHECKS_RUN" in `#338` and by the owner; these are the three
identifiers that carry it, and `prose_names` rejected the invented spelling, correctly.

WHY THIS IS LOAD-BEARING AND NOT DECORATION. Most weeks the claim band is empty; the brief says
so and calls it the feature. When the band is empty this line is the ENTIRE content of the page.
So the most frequent state of the app's most important screen had nothing true to display, which
is precisely the condition that produced `#336b`: a surface with nothing true to say reaches for
something false.

AND WRITING IT DOWN CORRECTED THE SPEC THAT ASKED FOR IT. `VOICE.md` rule 5 says "Five checks,
all clean -- starters, holes, depth, byes, record". Two independent designers drew "Four checks".
Nothing computed either number. The honest count is THREE, because three is what `compose`
evaluates: readiness and standings never reach it, and the dashboard ruling puts record off the
front page as true-but-inert. A page claiming five would have overclaimed by two IN THE SENTENCE
MEANT TO MAKE IT AUDITABLE.
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import front_claims as fc
import lineup_optimizer as lo


def _measured_bye(**over):
    """A bye profile that carries the evidence of having been computed."""
    b = {"weeks": {}, "basis": lo.BYE_MEASURED, "worst_week": None, "worst_week_loss": None,
         "concentration": None}
    b.update(over)
    return b


def _quiet(**over):
    base = {"structural_holes": [], "thin_positions": [], "bye_profile": _measured_bye(),
            "current_week": 7}
    base.update(over)
    return base


class TheThreeStatesAreDistinctTests(unittest.TestCase):
    """`clean` / `fired` / `absent`. Collapsing any two is the defect."""

    def _states(self, fx):
        out = fc.compose(fx)
        return {c["name"]: c["state"] for c in out["checks"]}

    def test_a_measured_empty_result_is_CLEAN(self):
        self.assertEqual({"holes": fc.CHECK_CLEAN, "byes": fc.CHECK_CLEAN,
                          "depth": fc.CHECK_CLEAN}, self._states(_quiet()))

    def test_a_check_whose_rung_fired_is_FIRED_never_clean(self):
        st = self._states(_quiet(structural_holes=["K"]))
        self.assertEqual(fc.CHECK_FIRED, st["holes"])
        self.assertEqual(fc.CHECK_CLEAN, st["depth"])

    def test_a_missing_key_is_ABSENT_not_clean(self):
        """`#187` applied to a CHECK rather than a figure. Reporting an unmeasured check as clean
        tells the reader their roster was examined when it was not."""
        fx = _quiet()
        del fx["thin_positions"]
        self.assertEqual(fc.CHECK_ABSENT, self._states(fx)["depth"])

    def test_an_explicit_None_is_ABSENT_too(self):
        self.assertEqual(fc.CHECK_ABSENT, self._states(_quiet(thin_positions=None))["depth"])

    def test_an_EMPTY_LIST_is_clean_and_None_is_absent_and_they_differ(self):
        """The whole distinction, in one assertion. `#187`: a value that was not measured is
        None, never an empty default -- so `[]` is a measured empty result."""
        self.assertEqual(fc.CHECK_CLEAN, self._states(_quiet(structural_holes=[]))["holes"])
        self.assertEqual(fc.CHECK_ABSENT, self._states(_quiet(structural_holes=None))["holes"])

    def test_an_empty_bye_profile_is_ABSENT_not_a_measured_empty_profile(self):
        """`{}` carries no weeks and no basis. `bye_collision` stamps a real profile with its
        basis, which is the evidence that it ran."""
        self.assertEqual(fc.CHECK_ABSENT, self._states(_quiet(bye_profile={}))["byes"])

    def test_an_absent_check_carries_its_reason(self):
        fx = _quiet(bye_profile=None)
        byes = next(c for c in fc.compose(fx)["checks"] if c["name"] == "byes")
        self.assertTrue(byes["reason"], "an absence must carry why, never a bare state")
        self.assertIn("bye_profile", byes["reason"])

    def test_a_check_that_ran_carries_no_reason(self):
        for c in fc.compose(_quiet())["checks"]:
            self.assertIsNone(c["reason"])


class TheSummaryRefusesTheVacuousAllClearTests(unittest.TestCase):
    def test_all_clean_is_true_only_when_every_check_ran_and_none_fired(self):
        s = fc.checks_summary(fc.compose(_quiet())["checks"])
        self.assertTrue(s["all_clean"])
        self.assertEqual(3, s["ran"])

    def test_all_clean_is_FALSE_when_a_check_never_ran(self):
        """THE TRAP THIS GUARDS. With a check absent, `not fired` is still true, so a naive
        all-clear would print "all clean" about a roster it did not fully examine."""
        s = fc.checks_summary(fc.compose(_quiet(bye_profile=None))["checks"])
        self.assertFalse(s["all_clean"])
        self.assertEqual(["byes"], s["absent"])

    def test_all_clean_is_FALSE_when_every_check_is_absent(self):
        """The most dishonest sentence available to this page, refused explicitly."""
        s = fc.checks_summary(fc.compose(
            {"structural_holes": None, "thin_positions": None, "bye_profile": None})["checks"])
        self.assertFalse(s["all_clean"])
        self.assertEqual(0, s["ran"])

    def test_ran_is_not_the_number_of_checks_declared(self):
        """`ran` counts what ACTUALLY ran. A surface using `len(CHECKS)` would overclaim."""
        s = fc.checks_summary(fc.compose(_quiet(thin_positions=None))["checks"])
        self.assertEqual(2, s["ran"])
        self.assertNotEqual(len(fc.CHECKS), s["ran"])

    def test_a_fired_check_is_not_counted_clean(self):
        s = fc.checks_summary(fc.compose(_quiet(structural_holes=["K"]))["checks"])
        self.assertEqual(["holes"], s["fired"])
        self.assertNotIn("holes", s["clean"])
        self.assertEqual(3, s["ran"], "firing is still running")


class TheDeclaredChecksMatchTheLadderTests(unittest.TestCase):
    """The structural guard. Adding a rung the band can raise without adding a check would let
    the page report "all clean" while a whole category went unexamined."""

    def test_every_check_maps_to_a_rung_the_band_actually_produces(self):
        self.assertEqual(set(fc.RUNGS_PRODUCED_HERE), {rung for _, _, rung in fc.CHECKS},
                         "a produced rung has no check, or a check names a rung nothing raises")

    def test_the_checks_are_in_ladder_order(self):
        order = {kind: i for i, (kind, _) in enumerate(fc.LADDER)}
        rungs = [rung for _, _, rung in fc.CHECKS]
        self.assertEqual(sorted(rungs, key=lambda r: order[r]), rungs)

    def test_there_are_three_checks_not_the_five_the_voice_spec_claimed(self):
        """`VOICE.md` said five and named `starters` and `record`; two designers drew four.
        Neither number was computed by anything. Three is what `compose` evaluates."""
        self.assertEqual(3, len(fc.CHECKS))
        names = {name for name, _, _ in fc.CHECKS}
        self.assertEqual({"holes", "byes", "depth"}, names)
        self.assertNotIn("record", names)
        self.assertNotIn("starters", names)

    def test_the_names_are_unique(self):
        names = [name for name, _, _ in fc.CHECKS]
        self.assertEqual(len(set(names)), len(names))


class TheCheckStateIsDerivedNotRecomputedTests(unittest.TestCase):
    """`#126` / `#338`: a check cannot disagree with the rung it reports on."""

    def test_no_check_reports_clean_while_its_own_rung_is_in_the_band(self):
        fx = _quiet(structural_holes=["K", "DEF"],
                    bye_profile=_measured_bye(weeks={"9": 40.0}, worst_week=9,
                                              worst_week_loss=40.0),
                    thin_positions=[{"position": "TE", "label": "Weak", "count": 1,
                                     "valued_count": 1}])
        out = fc.compose(fx)
        fired_rungs = {c["kind"] for c in out["shown"] + out["hidden"]}
        for check in out["checks"]:
            rung = next(r for n, _, r in fc.CHECKS if n == check["name"])
            if rung in fired_rungs:
                self.assertEqual(fc.CHECK_FIRED, check["state"],
                                 f"{check['name']} says {check['state']} while {rung} fired")

    def test_a_claim_pushed_to_hidden_by_the_cap_still_counts_as_fired(self):
        """`CAP` is a display limit, not a measurement. A check whose claim was capped out of
        view still ran and still found something."""
        fx = _quiet(structural_holes=["K"],
                    bye_profile=_measured_bye(weeks={"9": 40.0}, worst_week=9,
                                              worst_week_loss=40.0),
                    thin_positions=[{"position": p, "label": "Weak", "count": 1,
                                     "valued_count": 1} for p in ("TE", "WR", "DEF")])
        out = fc.compose(fx)
        self.assertTrue(out["hidden"], "fixture must overflow the cap to test this")
        states = {c["name"]: c["state"] for c in out["checks"]}
        self.assertEqual(fc.CHECK_FIRED, states["depth"])


if __name__ == "__main__":
    unittest.main()
