"""The slot vocabulary's two questions, pinned against the captures that establish them.

Register: #242 (the two questions), #126 (one home for a vocabulary).

WHAT THIS FILE DEFENDS. `len(roster_positions)` was used as a startup draft's round count by
every instrument in this repository. It is right only for a league with no IR slot -- which is
exactly what data/fixtures/sleeper_capture.json is, which is why nothing noticed. The rule that
replaces it is not asserted here; it is RE-DERIVED from each capture's own recorded numbers, so
a third league that disagrees fails this file rather than being absorbed by it.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import draft_battery as db
import league_config as lc

CAPTURES = Path("data/league_captures")


def _capture(name: str) -> dict:
    return json.loads((CAPTURES / name).read_text(encoding="utf-8"))


class TheTwoQuestionsAreDistinct(unittest.TestCase):
    def test_bench_and_taxi_are_drafted_but_never_start(self):
        """The whole point of splitting the vocabulary. If these collapse, there is one question."""
        for slot in ("BN", "TAXI"):
            self.assertIn(slot, lc.NON_STARTING_SLOTS, f"{slot} should not start")
            self.assertNotIn(slot, lc.UNDRAFTED_SLOTS, f"{slot} IS filled by the draft")

    def test_ir_answers_no_to_both(self):
        self.assertIn("IR", lc.NON_STARTING_SLOTS)
        self.assertIn("IR", lc.UNDRAFTED_SLOTS)

    def test_the_sets_are_not_the_same_set(self):
        self.assertNotEqual(set(lc.NON_STARTING_SLOTS), set(lc.UNDRAFTED_SLOTS))

    def test_the_legacy_name_is_an_alias_not_a_second_definition(self):
        """#126: one home. `==` would pass for two hand-typed copies that later drift; `is` will not."""
        self.assertIs(lc.NON_PLAYING_SLOTS, lc.NON_STARTING_SLOTS)


class ThereIsExactlyOneHome(unittest.TestCase):
    """#126. draft_battery carried its own identical copy; `is` is what makes the merge real."""

    def test_draft_battery_does_not_define_its_own(self):
        self.assertIs(db.NON_STARTING_SLOTS, lc.NON_STARTING_SLOTS)

    def test_draft_batterys_helper_is_the_shared_one(self):
        self.assertIs(db._starting_slots, lc.starting_slots)


class TheCapturesReproduceTheirOwnDraftLength(unittest.TestCase):
    """Non-vacuity: these numbers are read off the captures, not restated from the constant."""

    def _check(self, filename: str):
        cap = _capture(filename)
        rp = cap["roster_positions"]
        recorded = cap["draft_math"]["draftable_slots_per_team"]
        self.assertEqual(len(lc.draftable_slots(rp)), recorded,
                         f"{filename}: derived round count disagrees with the capture's own")
        # And the count it replaces is genuinely different, or this file proves nothing.
        self.assertNotEqual(len(rp), recorded,
                            f"{filename} has no IR slot -- it cannot witness the difference")

    def test_fourth_and_forever(self):
        self._check("fourth_and_forever.json")

    def test_greatest_show_on_paper_2(self):
        self._check("greatest_show_on_paper_2.json")

    def test_fourth_and_forever_was_confirmed_against_a_real_board(self):
        """26 is not arithmetic here -- the startup actually ran 26 rounds. Keep that visible."""
        cap = _capture("fourth_and_forever.json")
        self.assertIn("26", cap["draft_math"]["ROUND_COUNT_CHECK"])
        self.assertEqual(len(lc.draftable_slots(cap["roster_positions"])), 26)


class TheFixtureLeagueIsWhyNobodyNoticed(unittest.TestCase):
    def test_the_fixture_league_has_no_ir_so_the_old_rule_looks_correct(self):
        shape = json.loads(
            Path("data/fixtures/sleeper_capture.json").read_text(encoding="utf-8")
        )["league_shape"]
        rp = shape["roster_positions"]
        self.assertNotIn("IR", rp)
        self.assertEqual(len(lc.draftable_slots(rp)), len(rp))


class TheRoundCountSwitchIsNoLongerANoOpOnEveryBatteryArm(unittest.TestCase):
    """INVERTED (#251), and the inversion is the finding.

    This class asserted that the #242 switch from `len(roster_positions)` to `draftable_slots`
    was a NO-OP on every battery arm, because no mock league carries IR. Its own docstring named
    the condition under which that would end: *"If build_mock_league ever gains an IR slot, the
    battery's round count changes, and that must be a deliberate visible event, not a surprise."*

    This is that event, arriving by a better route than an IR slot bolted onto a mock league: a
    REAL captured league entered the matrix as a configuration point. Fourth and Forever has 29
    roster positions, 3 of them IR, so it drafts 26 rounds.

    **#242's repair was correct and, at battery scale, UNEXERCISED until now.** Every arm agreed
    with the defect it fixed. That is the same shape as #161's SHORT_DRAFT arm -- a harness that
    fixes a variable cannot falsify a defect in that variable -- and it is the third time in one
    day that adding one real configuration falsified an assumption invisible while the matrix was
    synthetic-only.
    """

    def test_the_synthetic_arms_still_carry_no_undrafted_slot(self):
        """The original property, narrowed to the population it was ever about. Mock leagues have
        no IR, so the switch remains a no-op for them -- and if `build_mock_league` ever gains an
        IR slot, this still says so."""
        matrix = [a for a in db.league_matrix() if not a["label"].startswith("CAPTURE_")]
        self.assertGreater(len(matrix), 25)
        for arm in matrix:
            rp = arm["league"]["roster_positions"]
            self.assertEqual(len(lc.draftable_slots(rp)), len(rp), arm["label"])

    def test_a_captured_arm_makes_the_switch_load_bearing(self):
        """The inversion. At least one arm must now DISAGREE, or #242's repair is back to being
        untested at battery scale."""
        captured = [a for a in db.league_matrix() if a["label"].startswith("CAPTURE_")]
        self.assertTrue(captured, "no captured league is in the matrix; #242 is unexercised again")
        disagreeing = [a["label"] for a in captured
                       if len(lc.draftable_slots(a["league"]["roster_positions"]))
                       != len(a["league"]["roster_positions"])]
        self.assertTrue(disagreeing,
                        "a captured arm must exercise the draftable/total distinction")
        for arm in captured:
            rp = arm["league"]["roster_positions"]
            with self.subTest(arm["label"]):
                self.assertEqual(arm["rounds"], len(lc.draftable_slots(rp)),
                                 "the arm's round count must come from draftable_slots, not len")

    def test_a_real_league_is_where_the_two_disagree(self):
        """Non-vacuity for the test above: the equality is a property of mock leagues, not of
        draftable_slots. Without this, the test above would also pass if the function were
        `len`."""
        rp = _capture("fourth_and_forever.json")["roster_positions"]
        self.assertNotEqual(len(lc.draftable_slots(rp)), len(rp))


class StartingSlotsStillAnswersQ1(unittest.TestCase):
    def test_fourth_and_forever_starts_ten(self):
        rp = _capture("fourth_and_forever.json")["roster_positions"]
        self.assertEqual(len(lc.starting_slots(rp)), 10)

    def test_order_is_preserved(self):
        rp = ["QB", "BN", "RB", "IR", "WR", "TAXI"]
        self.assertEqual(lc.starting_slots(rp), ["QB", "RB", "WR"])
        self.assertEqual(lc.draftable_slots(rp), ["QB", "BN", "RB", "WR", "TAXI"])

    def test_empty_and_none_are_not_crashes(self):
        for empty in (None, []):
            self.assertEqual(lc.starting_slots(empty), [])
            self.assertEqual(lc.draftable_slots(empty), [])


if __name__ == "__main__":
    unittest.main()
