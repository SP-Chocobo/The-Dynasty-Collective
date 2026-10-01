"""#241: the battery discloses which format axes its arms ACTUALLY exercise.

WHY THIS IS NOT COVERED BY duplicate_arms. That detector (#159) finds arms whose measured
content is byte-identical to another's. It cannot see an axis whose arms differ in scoring
VALUE while never varying the export selection those values are supposed to drive: the arms
genuinely differ, so nothing is flagged, and the matrix keeps advertising a dimension it no
longer has. That is #241 exactly -- since #213 correctly made the real (TE-premium) Fourth &
Forever rulebook every arm's base_scoring, `build_mock_league(te_premium=False)` can add a
bonus but cannot remove one, so every arm hints te_premium=True.

A correct repair flattened an advertised axis and nothing noticed. These tests are the noticing.
"""
import json
import unittest

import draft_battery as db
import run_draft_battery as rdb


def _base_scoring():
    """THE BATTERY'S OWN SOURCE, not a hand-rolled extraction.

    #241 was filed on a hand-built dict read from data/league_captures/fourth_and_forever.json
    -- a DIFFERENT captured league from the one run_draft_battery actually drafts
    (data/fixtures/sleeper_capture.json). F&F is half-PPR TE-premium; the battery's fixture is
    full-PPR with no TE bonus. Building the matrix from the wrong rulebook made every arm hint
    te_premium=True and produced a coverage "finding" that does not exist. Calling the
    production function is the whole fix, and it is the same rule as the battery fixture's
    "rdb.build_players_db, not a hand-rolled loop"."""
    return rdb.scoring_settings_from_capture()


class TheAxisNamesAreDerivedNotListed(unittest.TestCase):
    """#126 applied to the instrument: adding an axis upstream must not need an edit here."""

    def test_every_axis_league_format_hint_returns_is_reported(self):
        base = _base_scoring()
        matrix = db.league_matrix(base)
        # advertised_format_axes, not league_format_hint (#52 phase 6). There are TWO derived
        # vocabularies -- which export fits the league, and what shape the league is -- and the
        # report has always unioned them. This assertion named only the first, so it was itself
        # the hand-list it exists to forbid, one layer up: adding the roster-shape axes upstream
        # turned it red without anything going stale. Both now read the same single home.
        axis_keys = set(db.advertised_format_axes(matrix[0]["league"]))
        self.assertTrue(axis_keys, "advertised_format_axes returned nothing -- fixture is broken")
        reported = set(db.format_axes_exercised(matrix)["axes"])
        self.assertEqual(reported, axis_keys,
                         "the reported axes are not exactly the advertised ones, so this report "
                         "is a hand-list that will go stale")
        # ...and the union really does carry both vocabularies, or the check above would pass
        # against either one alone.
        self.assertTrue(set(db.league_format_hint(matrix[0]["league"])) < axis_keys)
        self.assertTrue(set(db.roster_shape_axes(matrix[0]["league"])) < axis_keys)

    def test_a_new_axis_appears_without_editing_this_module(self):
        """Drives the derivation rather than asserting it: patch the hint to emit one more axis
        and require it to surface. A hand-listed implementation passes the test above and fails
        this one."""
        base = _base_scoring()
        matrix = db.league_matrix(base)[:4]
        real = db.league_format_hint
        try:
            db.league_format_hint = lambda lg: {**real(lg), "invented_axis": lg["total_rosters"]}
            out = db.format_axes_exercised(matrix)
        finally:
            db.league_format_hint = real
        self.assertIn("invented_axis", out["axes"],
                      "an axis added to league_format_hint did not reach the report")


class AConstantAxisIsNamed(unittest.TestCase):

    def _matrix(self):
        return db.league_matrix(_base_scoring())

    def test_an_axis_with_one_observed_value_is_called_constant(self):
        matrix = self._matrix()
        out = db.format_axes_exercised(matrix)
        for axis, values in out["axes"].items():
            if len(values) == 1:
                self.assertIn(axis, out["constant_axes"], f"{axis} has one value but is not named")
            else:
                self.assertNotIn(axis, out["constant_axes"],
                                 f"{axis} has {len(values)} values but is called constant")

    def test_a_varying_axis_is_not_called_constant(self):
        """The control. Without it, 'names every axis constant' would pass the test above."""
        out = db.format_axes_exercised(self._matrix())
        self.assertGreater(len(out["axes"]["scoring"]), 1,
                           "fixture: scoring should vary across the full matrix")
        self.assertNotIn("scoring", out["constant_axes"])

    def test_one_arm_reports_no_constant_axes(self):
        """With a single arm every axis is trivially constant; saying so is noise, not news."""
        matrix = self._matrix()
        out = db.format_axes_exercised(matrix, {matrix[0]["label"]})
        self.assertEqual(out["arms"], 1)
        self.assertEqual(out["constant_axes"], [])

    def test_labels_scope_the_answer_to_the_arms_being_reported(self):
        """A --only or resumed report must describe ITSELF, not the matrix a fuller run had."""
        matrix = self._matrix()
        wanted = {"12T_ppr", "12T_standard"}
        out = db.format_axes_exercised(matrix, wanted)
        self.assertEqual(out["arms"], len(wanted))
        self.assertEqual(sum(out["axes"]["scoring"].values()), len(wanted))
        # These two arms are both 1QB, so superflex IS constant within them even though it
        # varies across the full matrix -- which is the whole point of scoping.
        self.assertIn("superflex", out["constant_axes"])
        self.assertNotIn("superflex", db.format_axes_exercised(matrix)["constant_axes"])


class TheReportCarriesIt(unittest.TestCase):

    def test_battery_report_includes_the_disclosure_scoped_to_its_results(self):
        matrix = db.league_matrix(_base_scoring())
        results = [{"label": matrix[0]["label"], "picks": 1, "findings": []},
                   {"label": matrix[1]["label"], "picks": 1, "findings": []}]
        report = rdb._battery_report({"players_in_pool": 1}, results, 0.0,
                                     complete=True, matrix=matrix)
        self.assertIn("format_axes", report)
        self.assertEqual(report["format_axes"]["arms"], 2,
                         "the report described more arms than it holds results for")
        self.assertEqual(set(report["format_axes"]["axes"]),
                         set(db.advertised_format_axes(matrix[0]["league"])))


class WhatTheMatrixActuallyExercises(unittest.TestCase):
    """A WITNESS. #241 claimed te_premium was constant; against the battery's REAL rulebook it
    is not, and the claim is withdrawn. What is pinned now is the true state, so that an axis
    which LATER goes constant announces itself instead of passing silently."""

    def test_every_constant_axis_is_a_REGISTERED_one(self):
        """The guard, now that an axis really is constant and the honest answer is to say so.

        It used to demand that NO axis be constant. That was right while the only axes were the
        export-selection ones, all of which vary. The roster-shape axes added in #52 phase 3
        brought a real hole with them: `has_defense` is False on all 35 arms, because
        build_mock_league emits no DEF slot and neither captured league has one. The test's own
        message said what to do about that -- "Register it before silencing it" -- and there was
        nowhere to register it, so this adds the register and reads it.

        It ratchets in BOTH directions: an unregistered constant axis fails because a gap
        appeared, and a REGISTERED axis that starts varying fails too, because the registration
        is now a false statement about the matrix and should be deleted.
        """
        out = db.format_axes_exercised(db.league_matrix(_base_scoring()))
        self.assertEqual(
            out["constant_axes"], sorted(db.UNCOVERED_AXES),
            "An advertised format axis changed coverage.\n"
            "  Constant and unregistered = a new coverage hole: the matrix crosses it in NAME "
            "while every arm resolves to one value, so the run is not evidence about that "
            "branch. Register it in draft_battery.UNCOVERED_AXES, with what would close it.\n"
            "  Registered but no longer constant = good news, and the registration is now false; "
            "delete the entry.\n"
            f"  observed: {out['axes']}")

    def test_every_registered_hole_says_what_would_close_it(self):
        """A register whose entries are bare names is a silencer with extra steps.

        EMPTY IS NOW THE HEALTHY STATE, and this used to assert the opposite. It required
        `UNCOVERED_AXES` to be non-empty, with the message "nothing registered -- delete the
        register instead" -- written when the register held the only known hole and an empty one
        was inconceivable. `has_defense` was then closed by adding a DEF-bearing arm, which is
        what its own entry said closing it would take, and this assertion turned into a demand
        that the matrix keep a coverage hole so the register would have something to hold.

        Deleting the register instead, as the old message advised, would delete the mechanism at
        the exact moment it first had nothing to report: the sibling test above compares the
        matrix's constant axes AGAINST this dict, so an empty one is what makes "no axis is
        constant" checkable. What is pinned here is the thing that actually matters -- every
        entry that EXISTS names a real advertised axis and says what would close it.
        """
        advertised = set(db.advertised_format_axes(db.league_matrix(_base_scoring())[0]["league"]))
        for axis, reason in db.UNCOVERED_AXES.items():
            with self.subTest(axis=axis):
                self.assertIn(axis, advertised, "a register entry names no advertised axis")
                self.assertGreater(len(reason), 120, "the reason is too short to be one")

    def test_te_premium_is_varied_which_is_what_withdrew_241(self):
        """The specific claim #241 made, now measured against the right source."""
        out = db.format_axes_exercised(db.league_matrix(_base_scoring()))
        self.assertEqual(set(out["axes"]["te_premium"]), {"False", "True"},
                         "te_premium no longer takes both values -- #241 would become true")
        self.assertGreater(out["axes"]["te_premium"]["True"], 0)
        self.assertGreater(out["axes"]["te_premium"]["False"], 0)


if __name__ == "__main__":
    unittest.main()
