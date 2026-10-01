"""#222 / #241 / #215 / #170: eight report fields whose values were not the quantity their names
promised — the v2 audit's `0.7`.

Cited against the register items whose own fields these are: #222 defined `picks_by_mode` and
`upside_from_round`, #241 defined `format_axes`, #215 defined the resume join and the
`produced_at_commit` stamp that blinded `duplicate_arms`, and #170 defined the coverage block
`tav_margin_profile` sits beside. Each of those items shipped a field; none of them shipped a check
that the field still means its name.

Every one was individually plausible and collectively made the batteries' reports describe
something other than what a reader thought. They are pinned together because they are one defect
with eight instances, and because a report field is only as good as something failing when it
drifts from its name again.

    draftable_rounds        the STARTING-SLOT count. Said 8 where the arm drafts 14, 10 where
                            Fourth & Forever drafts 26, 11 where the owner league drafts 25 --
                            35 of 36 arms disagreed.
    duplicate_arms          blind on a resumed run, because main() stamps produced_at_commit and
                            carried_forward onto every arm BEFORE the fingerprint is taken. So
                            independent_formats was overstated exactly when --resume was used,
                            which is the documented normal way a three-hour battery finishes.
    trajectory provenance   mode, noise seed, pricing path and upside rule all recorded by
                            simulate_full_draft "so two trajectories are not mistaken as
                            comparable", then read by nobody.
    picks_by_mode           computed from UPSIDE_MODE_DEFAULT_ROUND regardless of upside_rule,
                            which is false on every crossing arm.
    VDS strategy findings   an inert arm reproduces its control byte for byte, so the control's
                            finding was counted again under the inert arm's strategy name.
    VDS join disclosure     absent, so a resumed run could mix commits while INERT_ARMS compared
                            a carried control against a fresh arm.
    format_axes             computed from the LIVE matrix, matched to carried arms by label only.
    tav_margin_profile      the top two tav rows, not the chosen candidate and its runner-up.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import draft_battery as db
import draft_room as dr
import draft_simulation as ds
import league_config as lc
import resume_join
import run_draft_battery as rdb
import run_vds_battery as rv
import vds_battery as vb

CAPTURE = rdb.CAPTURE_PATH


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class DraftableRoundsIsTheRoundCount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = db.league_matrix(rdb.scoring_settings_from_capture())

    def test_it_equals_the_rounds_the_arm_actually_drafts(self):
        for entry in self.matrix:
            with self.subTest(entry["label"]):
                self.assertEqual(entry["rounds"],
                                 db.roster_shape_axes(entry["league"])["draftable_rounds"])

    def test_the_short_draft_arm_is_the_one_that_proves_it(self):
        """`12T_ppr_SHORT_DRAFT` drafts 8 rounds off a 14-slot roster. It is the single arm where
        `league_config.draftable_slots` -- the obvious substitute, and the one I reached for first
        -- gives the wrong answer, which is why the round count comes from the league instead."""
        entry = next(e for e in self.matrix if e["label"] == "12T_ppr_SHORT_DRAFT")
        axes = db.roster_shape_axes(entry["league"])
        self.assertEqual(8, axes["draftable_rounds"])
        self.assertEqual(14, len(lc.draftable_slots(entry["league"]["roster_positions"])),
                         "if this stops being 14 the arm changed, not the bug")

    def test_the_old_quantity_survives_under_its_true_name(self):
        for entry in self.matrix:
            with self.subTest(entry["label"]):
                self.assertEqual(
                    len(lc.starting_slots(entry["league"]["roster_positions"])),
                    db.roster_shape_axes(entry["league"])["starting_slots"])

    def test_both_axes_reach_the_advertised_set(self):
        axes = db.advertised_format_axes(self.matrix[0]["league"])
        self.assertIn("draftable_rounds", axes)
        self.assertIn("starting_slots", axes)


class DuplicateArmsSurvivesAResume(unittest.TestCase):
    ARM = {"label": "a", "seconds": 1.0, "findings": [], "teams": 12, "shape": {"QB": 1}}

    def test_the_run_stamps_are_excluded_from_the_fingerprint(self):
        for field in (resume_join.PRODUCED_AT, resume_join.CARRIED, "seconds", "label"):
            with self.subTest(field):
                self.assertIn(field, db._FINGERPRINT_EXCLUDES)

    def test_two_identical_arms_are_flagged_across_a_resume_boundary(self):
        carried = dict(self.ARM, **{resume_join.PRODUCED_AT: "aaaaaaa",
                                    resume_join.CARRIED: True})
        fresh = dict(self.ARM, label="b", **{resume_join.PRODUCED_AT: "bbbbbbb",
                                            resume_join.CARRIED: False})
        self.assertEqual([{"label": "b", "duplicates": "a"}],
                         db.duplicate_arms([carried, fresh]))

    def test_a_genuinely_different_arm_is_not_flagged(self):
        carried = dict(self.ARM, **{resume_join.PRODUCED_AT: "aaaaaaa",
                                    resume_join.CARRIED: True})
        other = dict(self.ARM, label="c", teams=10,
                     **{resume_join.PRODUCED_AT: "aaaaaaa", resume_join.CARRIED: False})
        self.assertEqual([], db.duplicate_arms([carried, other]))

    def test_provenance_is_a_run_descriptor_and_does_not_hide_a_duplicate(self):
        """A1. The third field to be learned the hard way, after `seconds` and the resume stamps.

        `provenance` records how an arm was CONFIGURED, so two arms can agree on every pick and
        disagree on it -- which is exactly the condition this detector exists to find. When it
        joined the arm row it silently took the detector's only live finding with it: `12T_ppr`
        and `12T_ppr_mode_balanced` produce a byte-identical 112-pick sequence, differ in no key
        but `label`, `seconds` and `provenance`, and stopped being reported. Every committed
        report predating that field flagged the pair; the one published with it says
        `independent_formats: 53` where the answer is 52.

        Built in the SHAPE THE REAL PAIR HAS, not an abstract one: same picks, same findings,
        different mode."""
        a = dict(self.ARM, provenance={"mode": "auto", "upside_from_round": 15})
        b = dict(self.ARM, label="b", provenance={"mode": "balanced", "upside_from_round": None})
        self.assertNotEqual(a["provenance"], b["provenance"],
                            "non-vacuity: the two arms must actually differ in provenance")
        self.assertEqual([{"label": "b", "duplicates": "a"}], db.duplicate_arms([a, b]),
                         "a field describing the RUN hid two byte-identical arms")


class PicksByModeRefusesToStateWhatItCannotKnow(unittest.TestCase):
    """Under the crossing rule the board flips wherever `_vor` is exhausted, and nothing records
    the effective mode per pick. `#187`: an unknown crosses as None, never as a plausible number."""

    def test_the_round_rule_still_reports_a_split(self):
        self.assertEqual({"balanced": 168, "upside": 144},
                         ds._picks_by_mode("auto", 312, 12, dr.UPSIDE_RULE_ROUND))

    def test_the_crossing_rule_reports_None(self):
        self.assertIsNone(ds._picks_by_mode("auto", 312, 12, dr.UPSIDE_RULE_CROSSING),
                          "a split computed from a round constant is false under the crossing rule")

    def test_an_explicit_mode_is_knowable_under_either_rule(self):
        for rule in dr.UPSIDE_RULES:
            with self.subTest(rule):
                self.assertEqual({"balanced": 0, "upside": 9},
                                 ds._picks_by_mode("upside", 9, 3, rule))
                self.assertEqual({"balanced": 9, "upside": 0},
                                 ds._picks_by_mode("balanced", 9, 3, rule))

    def test_the_rule_itself_is_recorded_in_the_config(self):
        """Its absence is why the two fields above were false: a config that omits the rule cannot
        distinguish two trajectories on the axis the rule controls."""
        import inspect
        source = inspect.getsource(ds.simulate_full_draft)
        self.assertIn('"upside_rule": upside_rule', source)


class TheVDSReportDoesNotCreditInertArms(unittest.TestCase):
    """An inert arm reproduces its control byte for byte. The report's own INERT_ARMS line exists
    to say such an arm is not evidence about its strategy; the findings blocks then counted it as
    exactly that."""

    def _three_arms_two_inert(self):
        seq = ["p1", "p2", "p3"]
        ctrl = vb.CONTROL_STRATEGY
        return [
            {"label": f"F__{ctrl}", "format": "F", "strategy": ctrl,
             "pick_sequence": seq, "findings": [{"k": 1}]},
            {"label": "F__sharp_upside", "format": "F", "strategy": "sharp_upside",
             "pick_sequence": seq, "findings": [{"k": 1}]},
            {"label": "F__crossing", "format": "F", "strategy": "crossing",
             "pick_sequence": seq, "findings": [{"k": 1}]},
        ]

    def setUp(self):
        self.report = rv._report({}, self._three_arms_two_inert(), 0.0, complete=True)

    def test_the_inert_arms_are_identified(self):
        self.assertEqual(["F__crossing", "F__sharp_upside"], self.report["INERT_ARMS"])

    def test_the_raw_total_still_says_what_the_run_produced(self):
        self.assertEqual(3, self.report["findings_total"])

    def test_the_effective_total_counts_the_control_finding_once(self):
        self.assertEqual(1, self.report["findings_total_effective"])

    def test_no_inert_strategy_is_credited_with_the_controls_finding(self):
        eff = self.report["findings_by_strategy_effective"]
        self.assertEqual(0, eff["sharp_upside"])
        self.assertEqual(0, eff["crossing"])
        self.assertEqual(1, eff[vb.CONTROL_STRATEGY])

    def test_a_finding_shared_by_every_effective_arm_is_not_strategy_specific(self):
        self.assertEqual({}, self.report["STRATEGY_SPECIFIC_FINDINGS"],
                         "listing all three strategies was the defect -- it reported 'the shape "
                         "#22 had' over a property of the control")

    def test_the_denominator_is_the_strategies_that_RAN(self):
        """`len(vds_battery.STRATEGIES)` is the code's list, not the run's. On a partial or mid-run
        file -- what a reader usually holds -- a finding under every strategy that ran read as
        strategy-specific because fewer ran than exist."""
        arms = self._three_arms_two_inert()
        arms[1]["pick_sequence"] = ["p9"]          # make one arm effective
        arms[2]["pick_sequence"] = ["p8"]          # and the other
        report = rv._report({}, arms, 0.0, complete=True)
        self.assertEqual(sorted({a["strategy"] for a in arms}), report["strategies_that_ran"])
        self.assertEqual({}, report["STRATEGY_SPECIFIC_FINDINGS"])

    def test_the_join_disclosure_is_present(self):
        for key in ("commit", "commits_present", "carried_forward"):
            with self.subTest(key):
                self.assertIn(key, self.report)


class FormatAxesDescribeWhatTheArmsDrafted(unittest.TestCase):
    MATRIX = [{"label": "A",
               "league": {"roster_positions": ["QB", "RB", "WR", "TE", "BN"],
                          "draft_rounds": 5, "scoring_settings": {}}}]

    def test_an_arm_drafted_under_a_changed_league_is_named(self):
        other = db.advertised_format_axes(
            {"roster_positions": ["QB", "RB", "WR", "TE", "K", "BN"],
             "draft_rounds": 6, "scoring_settings": {}})
        report = db.format_axes_exercised(
            self.MATRIX, {"A"}, results=[{"label": "A", "format_axes": other}])
        self.assertEqual(["A"], report["arms_whose_league_changed_under_the_same_label"])
        self.assertEqual("arms", report["axes_source"])

    def test_an_older_report_without_recorded_axes_still_aggregates(self):
        report = db.format_axes_exercised(self.MATRIX, {"A"})
        self.assertEqual("matrix", report["axes_source"])
        self.assertEqual([], report["arms_whose_league_changed_under_the_same_label"])


class TavMarginIsAboutTheChosenPick(unittest.TestCase):
    """`zero_margin_share` is described as how decisively THE PICK was made. It measured the gap
    between the top two `tav` rows regardless of who was taken -- and the chosen row is not the
    top row whenever a backstop demotes it (feasibility, fieldability) or `opponent_noise` is on,
    which is every arm those apply to. Reported under that name it was a real number about a
    different question."""

    class _Traj:
        def __init__(self, picks):
            self.picks = picks
            self.config = {"label": "t"}

    def _pick(self, chosen, rows):
        return ds.PickRecord(
            pick_no=1, round=1, roster_id="1", pick_label="1.01",
            chosen_player_id=chosen, decision_regime="normal",
            snapshot={"candidates": rows})

    ROWS = [{"id": "top", "tav": 100.0}, {"id": "mid", "tav": 90.0}, {"id": "low", "tav": 10.0}]

    def test_when_the_top_row_is_taken_the_margin_is_top_minus_second(self):
        profile = db.tav_margin_profile(self._Traj([self._pick("top", self.ROWS)]))
        self.assertEqual(1, profile["picks_measured"])
        self.assertEqual(0, profile["zero_margin_picks"])

    def test_when_a_DEMOTED_row_is_taken_the_margin_is_negative_not_the_top_gap(self):
        """The case the old code could not express. A backstop took `low` over `top`; the honest
        margin is 10 - 100 = -90, and the old code reported 100 - 90 = +10 -- a comfortable
        positive margin for a pick made against the ordering."""
        profile = db.tav_margin_profile(self._Traj([self._pick("low", self.ROWS)]))
        self.assertEqual(1, profile["picks_measured"])
        self.assertEqual(1, profile["zero_margin_picks"],
                         "a pick taken below the best alternative has a non-positive margin")

    def test_a_pick_whose_chosen_row_has_no_tav_is_counted_as_unmeasurable(self):
        """Not silently skipped: `picks_measured` would otherwise hide the gap, and a margin that
        cannot be computed is not a zero margin."""
        profile = db.tav_margin_profile(self._Traj([self._pick("absent", self.ROWS)]))
        self.assertEqual(0, profile["picks_measured"])
        self.assertEqual(1, profile["picks_whose_margin_is_unmeasurable"])

    def test_the_basis_is_stated_in_the_report(self):
        profile = db.tav_margin_profile(self._Traj([self._pick("top", self.ROWS)]))
        self.assertIn("chosen candidate", profile["margin_basis"])


class TheTrajectorysProvenanceReachesTheReport(unittest.TestCase):
    """simulate_full_draft records mode, pool_scope, opponent_noise, upside_rule and the pricing
    path into config explicitly "so two trajectories are not mistaken as comparable".
    audit_trajectory read one key of it, so no per-arm entry carried any of them: a carried arm
    produced under a different seed was indistinguishable from a fresh one."""

    def test_audit_trajectory_copies_the_whole_config_except_the_label(self):
        import inspect
        source = inspect.getsource(db.audit_trajectory)
        self.assertIn('"provenance"', source)
        self.assertIn('if k != "label"', source)

    def test_and_records_the_axes_the_arm_was_drafted_under(self):
        source = __import__("inspect").getsource(db.audit_trajectory)
        self.assertIn('"format_axes": advertised_format_axes(league)', source)
