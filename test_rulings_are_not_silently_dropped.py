"""Every owner ruling is either IMPLEMENTED or STAGED WITH ITS REASON. Nothing is just forgotten.

`#52` produced seven engine-design decisions that `#56` and `#184` put with the owner. They were
ruled, recorded in `CDME_CONTRACTS.md`, and are being implemented one at a time -- and two of
them stopped partway, each because implementing the ruling faithfully turned out to force a
SECOND derivation the ruling did not cover:

  * `6.1b` unify -- the removal is written; 275 tests reference the retired field, 14 of them
    with real assertions, so it is its own pass.
  * `W1-07` substitute -- implemented and measured at a 62% label-flip rate against a ruling
    made on a 3.1% one, because `intervening_picks` is a property of the turn and
    `(1 - survival)` was a property of the player. It forces re-deriving five label thresholds.

A markdown note is not a guard. This file is, and it fires in BOTH directions:

  * a staged ruling whose patch has vanished fails here, so the work cannot be quietly dropped;
  * a staged ruling that someone IMPLEMENTS fails here too, so the record cannot silently go out
    of date with the code -- the exact `#166` shape this programme keeps closing.

To close a ruling: implement it, then move its entry from STAGED to IMPLEMENTED below and say
where the evidence lives. The test is what makes that a step rather than an intention.
"""

from __future__ import annotations

import unittest
from pathlib import Path

_HERE = Path(__file__).parent

#: One entry per ruling that is NOT yet in the engine. `witness` is a fact about the source that
#: is true while the ruling is unimplemented and false once it is -- so this table cannot drift
#: away from the tree it describes. `patch` is the staged work; `why` must be non-trivial,
#: because "staged" without a reason is indistinguishable from "abandoned".
STAGED = {
    "6.1b": {
        "witness": ("draft_room.py", "ELIGIBILITY_BONUS_MAX = NEED_BONUS_MAX"),
        "patch": "evidence/blind_pass/6_1b_removal.patch",
        "why": "275 tests reference the retired field -- 261 mechanically, 14 with real "
               "assertions. Its own pass, not the tail of another.",
    },
    "W1-07": {
        "witness": ("pick_synthesis.py", "NECESSITY_SURVIVAL_WEIGHT = 20.0"),
        "patch": "evidence/blind_pass/w1_07_substitute.patch",
        "why": "implementing it flips 62% of labels against a ruling made on 3.1%, because the "
               "substitute is a property of the TURN and the quantity it replaces was a "
               "property of the PLAYER. Forces re-deriving five label thresholds -- a second "
               "#56 exercise the ruling did not cover, and the owner's call.",
    },
}

#: Where a reader goes for the measurement behind each one. Checked for existence, not parsed:
#: this file's job is to make the pin fire, not to restate the evidence.
EVIDENCE = "evidence/blind_pass/RULINGS_EXECUTION.md"


class NoRulingIsSilentlyDroppedTests(unittest.TestCase):

    def test_every_staged_ruling_still_has_its_staged_work(self):
        """A patch that vanished is work lost, and the ruling would then look merely undone
        rather than three-quarters finished."""
        for ruling, entry in STAGED.items():
            with self.subTest(ruling=ruling):
                patch = _HERE / entry["patch"]
                self.assertTrue(patch.exists(), f"{ruling}: staged patch is gone ({patch})")
                self.assertGreater(len(patch.read_text().splitlines()), 20,
                                   f"{ruling}: the staged patch is empty or truncated")

    def test_every_staged_ruling_is_still_actually_unimplemented(self):
        """THE HALF THAT CATCHES THE OPPOSITE MISTAKE. If someone implements one of these, the
        witness disappears from the source and this fails -- which is the prompt to move the
        entry to IMPLEMENTED rather than leave a record that describes a tree that has moved on.
        A record outliving the thing it describes is the #166 shape, and a ruling table is a
        particularly bad place for it."""
        for ruling, entry in STAGED.items():
            module, witness = entry["witness"]
            with self.subTest(ruling=ruling):
                source = (_HERE / module).read_text()
                self.assertIn(
                    witness, source,
                    f"{ruling} appears to be IMPLEMENTED -- '{witness}' is gone from {module}. "
                    f"Move it out of STAGED in this file and record where the work landed.")

    def test_every_staged_ruling_states_why_it_stopped(self):
        """'Staged' with no reason is indistinguishable from 'abandoned' six months later."""
        for ruling, entry in STAGED.items():
            with self.subTest(ruling=ruling):
                self.assertGreater(len(entry["why"]), 60,
                                   f"{ruling}: say what stopped it, in a sentence a stranger "
                                   f"can act on")

    def test_the_rulings_are_recorded_where_a_reader_would_look(self):
        """The decisions live in the contracts file and the measurements in the evidence file.
        Both are checked for existence because this pin is worth nothing if the trail it points
        at has moved."""
        contracts = (_HERE / "CDME_CONTRACTS.md").read_text()
        self.assertIn("Owner rulings", contracts)
        for ruling in STAGED:
            self.assertIn(ruling, contracts, f"{ruling} is not in CDME_CONTRACTS.md")
        self.assertTrue((_HERE / EVIDENCE).exists(), f"{EVIDENCE} is missing")

    def test_the_seven_rulings_are_all_accounted_for(self):
        """Non-vacuity, and the thing that makes this a census rather than a note: all seven are
        named in the contracts file, and this file knows which are still outstanding. A ruling
        that appears in neither place is one nobody is tracking."""
        contracts = (_HERE / "CDME_CONTRACTS.md").read_text()
        for ruling in ("6.1b", "I-06/J-06", "6.1d.1", "W1-07", "W4-01", "J-12", "J-13"):
            with self.subTest(ruling=ruling):
                self.assertIn(ruling, contracts)


if __name__ == "__main__":
    unittest.main()
