"""R19: four v4 repairs that reverting leaves the suite GREEN. One test each, mutation-checked.

An independent review reverted each of the twelve repairs in a worktree, ran the modules that
ought to notice, and restored. Eight failed as they should. These four did not -- so each could
silently come undone and nothing would say so, which is worse than a bug: a bug announces itself
once, an undefended repair announces itself never.

The failure shape is the same in three of the four: the suite pins that a FIELD EXISTS or that a
CONSUMER reads it, and never that the PRODUCER fills it. `test_the_snapshot_carries_eligibility_
at_all` checks `dataclasses.fields`; the view-filter tests build their snapshots by hand with
`eligible_positions=` supplied. Both pass with production's producer replaced by `frozenset()`.

Answers to `#254` (a guard that catches nothing is not a guard), `#172` (eligibility from
`fantasy_positions`, behind one reader), `#187` (absence is None, never a measured value) and
`#126`.
"""
from __future__ import annotations

import unittest

import draft_room as dr
import pick_synthesis as ps
import prose_names
import ui_source


class BuildSnapshotFillsEligibilityAndNotMerelyDeclaresIt(unittest.TestCase):
    """(a) `C-F3`. Replacing `_eligibility`'s body with `frozenset()` left four modules green."""

    def test_a_dual_eligible_candidate_arrives_with_both_positions(self):
        """Through the PRODUCTION producer, never a hand-built snapshot.

        The repaired half that IS defended is defended only because its tests supply
        `eligible_positions=` themselves. That pins the consumer. This pins the producer."""
        players_db = {"99": {"player_id": "99", "full_name": "Dual Man", "position": "DL",
                             "fantasy_positions": ["DL", "LB"]}}
        self.assertEqual({"DL", "LB"}, set(dr.player_eligible_positions(players_db["99"])),
                         "non-vacuity: the fixture must be genuinely dual-eligible, or this "
                         "test cannot tell a filled field from an empty one")

        got = ps.snapshot_eligibility({"player_id": "99", "position": "DL"}, players_db)
        self.assertEqual({"DL", "LB"}, set(got),
                         "the producer returned only the row's own label, so a dual-eligible "
                         "man would appear in one view instead of both")

    def test_a_row_the_pool_does_not_know_keeps_its_own_label(self):
        """The degrade path. An empty eligibility would remove the row from EVERY view, which is
        worse than placing it on its primary bucket."""
        self.assertEqual({"WR"}, set(ps.snapshot_eligibility({"position": "WR"}, {})))
        self.assertEqual(frozenset(), ps.snapshot_eligibility({}, {}),
                         "with neither a known player nor a label there is nothing to claim")

    def test_the_field_is_not_merely_declared(self):
        """The existing test asserts `eligible_positions` is a FIELD. That passes on an empty
        producer, which is exactly how this repair reverted unnoticed."""
        import dataclasses
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("eligible_positions", names)
        default = {f.name: f.default for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertEqual(frozenset(), default["eligible_positions"],
                         "the default is what a reverted producer yields; if this changes, the "
                         "reasoning in this module needs rechecking")


class TheDraftRoomPutsTheDraftsSeatsOnTheLeague(unittest.TestCase):
    """(b) `A-F5`. Deleting one line from `app.py` left four modules green.

    Read through `ui_source`, never off `app.py` directly -- that is `test_ui_source`'s own rule
    and the reason `D-F5` existed."""

    def test_the_seats_are_assigned_through_the_one_key(self):
        """Two assertions, and the second is the one with teeth.

        The site must name `PICK_ORDER_KEY`, and must NOT spell its value. A literal
        `"draft_pick_order"` in `app.py` would survive a rename of the constant and silently stop
        matching whatever `league_config` then means (`#126`). An earlier draft of this test had
        it backwards and asserted the literal WAS present, which would have passed only on the
        defect."""
        app = ui_source.text()
        import league_config as lc
        self.assertTrue(lc.PICK_ORDER_KEY,
                        "non-vacuity: the key must be a real non-empty constant")
        self.assertIn("PICK_ORDER_KEY", app,
                      "the Draft Room no longer puts the draft's seats on the league dict at "
                      "all -- deleting that one line leaves four modules green")
        self.assertNotIn(f'"{lc.PICK_ORDER_KEY}"', app,
                         "the key is spelled as a literal somewhere in the Draft Room, so a "
                         "rename of the constant would not reach it")


class PresentableTextChecksAbsenceBeforeWithholding(unittest.TestCase):
    """(c) `A-F1`/`E-F2`. Reverting the order left the suite green.

    Absence and withholding are different states and the absent one must win: a quantity that was
    never measured cannot also be "measured and not trusted" (`#187`)."""

    def test_an_absent_value_reads_as_absent_not_as_withheld(self):
        absent = ps.presentable_text("survival_probability", ps.ABSENT_FIGURE)
        self.assertEqual(ps.ABSENT_FIGURE, absent,
                         "an absent figure was relabelled as withheld, which asserts a "
                         "measurement that was never taken")

    def test_a_present_value_can_still_be_withheld(self):
        """NON-VACUITY the other way: if everything reads absent, the check above is free."""
        withheld = ps.presentable_text("survival_probability", "0.42")
        self.assertIn(withheld, (ps.WITHHELD_CARD_TEXT, "0.42"),
                      "a present value must still reach one of the two real outcomes")


class TheHistoryShieldIsParagraphScoped(unittest.TestCase):
    """(d) `D-F2`. Reverting paragraph scoping to block scoping left the suite green."""

    def test_a_marker_in_one_paragraph_does_not_shield_another(self):
        text = ("This paragraph is historical: the field was renamed.\n"
                "\n"
                "This paragraph names `SomeNameThatDoesNotExistAnywhere` with no marker at all.")
        self.assertTrue(prose_names.is_history(text),
                        "non-vacuity: the BLOCK must look historical, or block and paragraph "
                        "scope agree and this test distinguishes nothing")
        position = text.index("SomeNameThatDoesNotExistAnywhere")
        para = prose_names._paragraph_around(text, position)
        self.assertFalse(prose_names.is_history(para),
                         "the paragraph around an unmarked name inherited a marker from a "
                         "different paragraph -- the shield is block-scoped again")


if __name__ == "__main__":
    unittest.main()
