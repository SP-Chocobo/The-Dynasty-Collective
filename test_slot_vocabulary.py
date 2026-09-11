"""The slot vocabulary's two questions, pinned against the captures that establish them.

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


class TheRoundCountSwitchIsANoOpOnEveryBatteryArm(unittest.TestCase):
    """The switch from len(roster_positions) to draftable_slots must not silently restate the
    battery. No mock league carries IR, so the two agree on every arm -- and this test is what
    says so rather than my having checked once. If build_mock_league ever gains an IR slot, the
    battery's round count changes, and that must be a deliberate visible event, not a surprise.
    """

    def test_no_battery_arm_carries_an_undrafted_slot(self):
        """The no-op is a property of the ROSTER SHAPES, not of any arm's round count -- one arm
        (SHORT_DRAFT) sets its rounds deliberately short and never derived them at all. Asserting
        the round count here instead was my first version of this test, and it failed on that arm,
        which is the distinction being recorded."""
        matrix = db.league_matrix()
        self.assertGreater(len(matrix), 0)
        for arm in matrix:
            rp = arm["league"]["roster_positions"]
            self.assertEqual(len(lc.draftable_slots(rp)), len(rp), arm["label"])

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
