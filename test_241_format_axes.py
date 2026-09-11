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
        hint_keys = set(db.league_format_hint(matrix[0]["league"]))
        self.assertTrue(hint_keys, "league_format_hint returned nothing -- fixture is broken")
        reported = set(db.format_axes_exercised(matrix)["axes"])
        self.assertEqual(reported, hint_keys,
                         "the reported axes are not exactly league_format_hint's own keys, so "
                         "this report is a hand-list that will go stale")

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
                         set(db.league_format_hint(matrix[0]["league"])))


class WhatTheMatrixActuallyExercises(unittest.TestCase):
    """A WITNESS. #241 claimed te_premium was constant; against the battery's REAL rulebook it
    is not, and the claim is withdrawn. What is pinned now is the true state, so that an axis
    which LATER goes constant announces itself instead of passing silently."""

    def test_no_advertised_axis_is_currently_constant(self):
        out = db.format_axes_exercised(db.league_matrix(_base_scoring()))
        self.assertEqual(
            out["constant_axes"], [],
            "An advertised format axis has stopped varying.\n"
            "  That is a coverage hole: the matrix crosses it in NAME while every arm resolves "
            "to one value, so the run is not evidence about that branch.\n"
            "  Register it before silencing it.\n"
            f"  observed: {out['axes']}")

    def test_te_premium_is_varied_which_is_what_withdrew_241(self):
        """The specific claim #241 made, now measured against the right source."""
        out = db.format_axes_exercised(db.league_matrix(_base_scoring()))
        self.assertEqual(set(out["axes"]["te_premium"]), {"False", "True"},
                         "te_premium no longer takes both values -- #241 would become true")
        self.assertGreater(out["axes"]["te_premium"]["True"], 0)
        self.assertGreater(out["axes"]["te_premium"]["False"], 0)


if __name__ == "__main__":
    unittest.main()
