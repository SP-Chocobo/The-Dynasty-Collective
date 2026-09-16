"""#274: a pick was discarded over a field its resolver never reads.

WHAT WENT WRONG. `observed_take_distribution.resolve_picks` skipped any pick flagged
`illegible`. That flag does not mean "the name could not be read" -- the board's own
provenance says what it means:

    "All illegible cells are in slot 12 (MatttyyIce), the one column with no roster view.
     Names are legible in all but one (10.12, UI-truncated 'Jacory Croskey-M...'); what is
     missing is nfl_team/bye."

It marks a missing BYE WEEK. The resolver matches on (normalized name, position) and reads
neither `nfl_team` nor `bye`, so the skip discarded six legible picks -- Patrick Mahomes,
Bucky Irving, Mark Andrews, James Conner, DJ Giddens, Darren Waller.

WHY THAT IS NOT COSMETIC. An unresolved pick never reaches `engine_picks`, so the player is
never removed from later boards and haunts every one of them. Measured before the repair: up
to 10 phantoms sitting ahead of a measured pick, mean 5.56, against a priced pool falling to
~160 rows by round 30. Every rank recorded after a phantom was inflated by however many sat
above the player actually taken -- which biases the published `rank1_share` and `top5_share`
DOWNWARD, and those are the figures cited as evidence about the take model.

THE TRUNCATED PICK MUST STILL BE REJECTED, and by the right mechanism. "Jacory Croskey-M..."
normalises to a key no index entry equals, so it falls out as `unmatched` and is counted --
`#82`'s ambiguity-is-a-rejection doing the work, rather than a flag about a different field
standing in for it. A test that only checked the recovery would pass just as well if the
resolver had started guessing at truncated names, which is why both halves are here.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path("evidence/take_model")))
import observed_take_distribution as otd  # noqa: E402
import run_draft_battery as rdb  # noqa: E402

#: The six whose names the board prints legibly while flagging the cell for a missing bye.
RECOVERED = ("Patrick Mahomes", "Bucky Irving", "Mark Andrews",
             "James Conner", "DJ Giddens", "Darren Waller")
#: The one whose name the UI actually truncated.
TRUNCATED = "Jacory Croskey-M…"


class TheResolverSkipsOnTheNameNotOnTheByeFlagTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.board = json.loads(otd.BOARD.read_text())
        cls.picks = sorted(cls.board["picks"], key=lambda p: p["pick_no"])
        cls.players_db, _ = rdb.build_players_db_from_capture()
        cls.resolved, cls.ambiguous, cls.unmatched = otd.resolve_picks(cls.picks, cls.players_db)
        cls.by_no = {p["pick_no"]: p for p in cls.picks}

    def test_the_fixture_still_contains_illegible_cells_with_legible_names(self):
        """Non-vacuity. If the board is ever re-extracted without the flag, this file is
        testing nothing and should say so rather than passing quietly."""
        flagged = [p for p in self.picks if p.get("illegible")]
        self.assertTrue(flagged, "no illegible cells remain -- this guard is vacuous")
        legible = [p for p in flagged if p.get("raw_player") and p["raw_player"] != TRUNCATED]
        self.assertTrue(legible,
                        "every illegible cell is now truncated, so nothing is recoverable "
                        "and the repair this file guards has no subject")

    def test_every_legibly_named_illegible_pick_resolves(self):
        for name in RECOVERED:
            with self.subTest(name):
                hit = [p for p in self.picks if p.get("raw_player") == name]
                self.assertTrue(hit, f"{name} is no longer on the board")
                for p in hit:
                    self.assertTrue(p.get("illegible"),
                                    f"{name} is no longer flagged -- fixture drifted")
                    self.assertIn(p["pick_no"], self.resolved,
                                  f"{name} was discarded again; the skip is keyed on the "
                                  "bye flag rather than on the name")

    def test_the_truncated_name_is_still_rejected(self):
        hit = [p for p in self.picks if p.get("raw_player") == TRUNCATED]
        self.assertTrue(hit, "the truncated pick left the fixture")
        for p in hit:
            self.assertNotIn(p["pick_no"], self.resolved,
                             "a UI-truncated name resolved to a player -- the resolver is "
                             "guessing, which is exactly what #82 forbids")

    def test_the_truncated_name_is_COUNTED_as_unmatched_not_silently_dropped(self):
        """#187 in the instrument's own reporting: a rejection that is not counted is
        indistinguishable from a pick that never existed."""
        self.assertIn(TRUNCATED, self.unmatched)

    def test_rookie_placeholders_are_still_skipped(self):
        placeholders = [p for p in self.picks if p.get("is_rookie_pick_placeholder")]
        self.assertTrue(placeholders, "fixture carries no placeholders")
        for p in placeholders:
            self.assertNotIn(p["pick_no"], self.resolved,
                             "a rookie-draft placeholder resolved to a real player")

    def test_the_recovery_is_worth_what_the_finding_claims(self):
        """The magnitude, pinned. Six recovered picks is what takes the phantom count from 11
        to 5; a repair that recovered one would not have been worth the entry."""
        flagged_resolved = sum(1 for p in self.picks
                               if p.get("illegible") and p["pick_no"] in self.resolved)
        self.assertEqual(flagged_resolved, len(RECOVERED))
        self.assertGreaterEqual(len(self.resolved), 307,
                                f"resolved {len(self.resolved)}, expected at least 307 -- "
                                "the repair regressed")


if __name__ == "__main__":
    unittest.main()
