"""B-F4 / C-F3 -- eligibility is the vocabulary, and it must reach BOTH SIDES of every comparison.

`#172` put eligibility behind one reader (`player_eligible_positions`) and MANDATE 2.6 ruled that
the engine decides positional questions by ASSIGNMENT rather than by the feed's primary label. Two
places were moved half-way and the halves then read different vocabularies (`#126`):

  B-F4  `feasibility_first` reads `player_eligible_positions` for the ROSTER and `scored["position"]`
        for the CANDIDATE. With an LB-only slot open, a DL/LB dual labelled DL scored `_feasible = 1`
        while a pure LB scored 0 -- the man who could fill the hole ranked behind the man who could,
        decided by which bucket the feed happened to name first. `_feasible` is the FIRST key of
        every board sort, so this is not a display question.

  C-F3  `position` was the only positional fact crossing the `CandidateSnapshot` boundary, so
        `filter_candidates_by_view` had nothing else to filter on and a dual-eligible candidate
        appeared in exactly ONE single-position view. Measured on the owner league at pick 1.01, a
        94-candidate snapshot: the LB view hid 8 eligible candidates including T.J. Watt, while the
        board's own `need_bonus` had already priced him with LB slots in the assignment. `#174`:
        the number crossed, its companion did not.

BOTH FALL BACK TO THE PRIMARY BUCKET and that is deliberate, not laxity. A candidate the pool has
no record of, and a stored board written before the snapshot carried eligibility, must behave
exactly as they did before -- an empty eligibility set must never promote everybody, and a replayed
board must replay.
"""

from __future__ import annotations

import dataclasses
import unittest

import pandas as pd

import draft_board_ui as ui
import draft_room as dr
import pick_synthesis as ps
from player_universe import FLEX_SLOT_POSITIONS

#: One QB slot and one LB slot. The QB is drafted, so the LB slot is the only hole.
ROSTER = ["QB", "LB"]
PLAYERS = {
    "1": {"first_name": "Q", "last_name": "B", "position": "QB", "fantasy_positions": ["QB"]},
    "10": {"first_name": "D", "last_name": "ual", "position": "DL",
           "fantasy_positions": ["DL", "LB"]},
    "11": {"first_name": "P", "last_name": "ure", "position": "LB", "fantasy_positions": ["LB"]},
    "12": {"first_name": "O", "last_name": "nlyDL", "position": "DL", "fantasy_positions": ["DL"]},
}
PICKS = [{"player_id": "1", "roster_id": "1", "round": 1, "pick_no": 1}]
SCORED = pd.DataFrame([{"player_id": "10", "position": "DL"},
                       {"player_id": "11", "position": "LB"},
                       {"player_id": "12", "position": "DL"}])


class FeasibilityFirstReadsEligibilityOnBothSidesTests(unittest.TestCase):

    def _key(self, players=None):
        return list(dr.feasibility_first(SCORED, PICKS, players if players is not None else PLAYERS,
                                         "1", ROSTER))

    def test_a_dual_labelled_elsewhere_is_promoted_for_the_hole_he_can_fill(self):
        """B-F4 itself. The DL/LB dual can start in the open LB slot, so he is feasible."""
        self.assertEqual(self._key()[0], 0,
                         "the DL/LB dual is not promoted for an LB-only hole, so the candidate "
                         "side is still reading the primary bucket")

    def test_the_pure_LB_is_still_promoted(self):
        """The half that already worked, kept so the repair cannot be 'promote everybody'."""
        self.assertEqual(self._key()[1], 0)

    def test_a_man_who_CANNOT_fill_the_hole_is_NOT_promoted(self):
        """NON-VACUITY, and the thing a sloppy fix breaks: a DL-only body fills no LB slot, so
        `_feasible` must stay 1. A key of all zeroes would pass both tests above and rank nothing."""
        self.assertEqual(self._key()[2], 1,
                         "a DL-only candidate is promoted for an LB-only hole -- the key no longer "
                         "distinguishes anyone")

    def test_the_key_is_not_uniform(self):
        """The same guard one level up, stated as a property of the whole key."""
        self.assertEqual(sorted(set(self._key())), [0, 1])

    def test_an_unknown_candidate_falls_back_to_his_primary_bucket(self):
        """A candidate the pool has no record of keeps the old behaviour exactly: judged on the
        label the board already carries, never promoted for want of information."""
        key = self._key(players={"1": PLAYERS["1"]})
        self.assertEqual(key, [1, 0, 1],
                         "an unknown candidate is not being judged on his board label")


class EligibilityCrossesTheSnapshotBoundaryTests(unittest.TestCase):
    """C-F3. Built through the real dataclass rather than a stub, so a field added or renamed on
    `CandidateSnapshot` fails here instead of quietly bypassing the check."""

    @staticmethod
    def _candidate(player_id, name, position, eligible=None):
        required = {f.name: None for f in dataclasses.fields(ps.CandidateSnapshot)
                    if f.default is dataclasses.MISSING
                    and f.default_factory is dataclasses.MISSING}
        required.update(player_id=player_id, name=name, position=position)
        if eligible is None:
            return ps.CandidateSnapshot(**required)
        return ps.CandidateSnapshot(**required, eligible_positions=frozenset(eligible))

    def setUp(self):
        self.watt = self._candidate("10", "TJ Watt", "DL", {"DL", "LB"})
        self.pure = self._candidate("11", "Pure LB", "LB", {"LB"})
        self.legacy = self._candidate("12", "Old Record", "DL")

    def _names(self, view, candidates=None):
        rows = candidates if candidates is not None else (self.watt, self.pure, self.legacy)
        return [c.name for c in ui.filter_candidates_by_view(rows, view)]

    def test_the_snapshot_carries_eligibility_at_all(self):
        self.assertIn("eligible_positions",
                      {f.name for f in dataclasses.fields(ps.CandidateSnapshot)},
                      "eligibility does not cross the snapshot boundary, so no view downstream "
                      "can filter on it")

    def test_the_LB_view_shows_a_dual_labelled_DL(self):
        """The finding, as a unit fact: T.J. Watt appears in the LB view."""
        self.assertIn("TJ Watt", self._names("LB"),
                      "the LB view still hides a candidate the board priced for LB slots")

    def test_the_LB_view_does_NOT_show_a_DL_only_candidate(self):
        """NON-VACUITY. A view that shows everyone passes the test above and is useless."""
        self.assertNotIn("Old Record", self._names("LB"))

    def test_a_dual_appears_in_BOTH_of_his_views(self):
        """The point of the repair -- one row, every view he can actually be started in."""
        self.assertIn("TJ Watt", self._names("DL"))
        self.assertIn("TJ Watt", self._names("LB"))

    def test_a_stored_board_without_the_field_replays_on_its_primary_bucket(self):
        """The compatibility half, and it is a real requirement rather than politeness: boards are
        stored and replayed, and a record written before this field must show what it showed."""
        self.assertIn("Old Record", self._names("DL"))
        self.assertNotIn("Old Record", self._names("LB"))

    def test_a_flex_view_admits_anyone_eligible_for_that_slot(self):
        """Flex views were already eligibility-shaped through `FLEX_SLOT_POSITIONS`; they must now
        read the candidate's eligibility too, or the two halves disagree again."""
        flex = next((name for name, positions in FLEX_SLOT_POSITIONS.items()
                     if "LB" in positions), None)
        if flex is None:
            self.skipTest("no flex slot in this vocabulary admits LB")
        self.assertIn("TJ Watt", self._names(flex))

    def test_the_ALL_view_still_shows_one_row_per_PRIMARY_bucket(self):
        """DELIBERATELY UNCHANGED. ALL reconstructs the curated overview -- top overall plus each
        position's own best -- and it keys on the primary bucket so a dual-eligible man does not
        occupy two of those slots. Eligibility belongs in the position views, not here."""
        names = self._names("ALL")
        self.assertIn("TJ Watt", names)
        self.assertEqual(len(names), len(set(names)), "a candidate appears twice in ALL")


if __name__ == "__main__":
    unittest.main()
