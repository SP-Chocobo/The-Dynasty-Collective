"""#168 SHARPENED: the engine can price NO quarterback for most of a superflex draft.

WHAT THIS PINS AND WHY IT IS NOT A DECORATION. `#168` records the behaviour as "bounded to
superflex QB tails". Measured on the real capture, that phrasing understates it by a lot: priced
QBs fall 42 -> 0 by round 12 of a 30-round draft, so the engine is blind to QB across 60% of the
draft at the position the format makes most valuable. A characterisation that specific goes
stale silently -- a baseline refresh, a floor-constant edit, or a change to which rows reach
pricing all move it, and nothing would say so. These tests fail when it moves.

THE MECHANISM IS ARITHMETIC, and each step is asserted separately so a failure says WHICH part
moved rather than just that the number changed:

    39 baseline QBs carry a projection
    28 of them clear the startable floor (QB_STARTABLE_FLOOR_FRACTION x QB12 = 162.00)
    by round 12, 32 QBs have been drafted -- more than clear the floor
    therefore every remaining QB is below the floor and none can be priced

NOT ASSERTED HERE: that this is a DEFECT, or that the floor's constant is wrong. The constant has
a documented stability-basin derivation and `#56` is not engaged. The open design question --
the floor asks "startable AS A QB" while the slot that makes a superflex QB draftable is
SUPER_FLEX, whose occupant competes against flex-eligible non-QBs -- is Phase 3 (`#50`) and is
recorded in the instrument, not decided in a test.

ALSO PINNED: the CORRECTION to `VALUE_MODEL_RESULT.md`. The unpriced block is two populations,
and the claim that mattered is that the non-QB core is CONSTANT across draft depth -- that is
what makes it a vendor-coverage gap rather than anything the startable floor causes.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import data_merger as dm
import draft_room as dr

RECORD = Path("evidence/take_model/unpriced_block_composition.json")


class TheStartableFloorStillSitsWhereTheFindingSaysTests(unittest.TestCase):
    """Driven from the live baseline, not from the record -- so a baseline refresh that moves
    the floor fails here rather than leaving a published number quietly wrong."""

    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text())
        cls.merger = dm.DataMerger()

    def test_the_floor_is_still_the_published_value(self):
        floor = dr.qb_startable_floor(self.merger)
        self.assertIsNotNone(floor, "no floor at all -- replacement_levels silently fell back")
        self.assertAlmostEqual(floor, self.record["qb_startable_floor"], places=2,
                               msg="the QB startable floor moved; the cliff round in "
                                   f"{RECORD} is stale and must be re-measured")

    def test_the_qb_supply_either_side_of_the_floor_is_unchanged(self):
        proj = self.merger.projections
        qb = proj[(proj["position"] == "QB") & proj["projection"].notna()]["projection"].astype(float)
        self.assertEqual(len(qb), self.record["qbs_with_a_projection"])
        floor = dr.qb_startable_floor(self.merger)
        self.assertEqual(int((qb >= floor).sum()), self.record["qbs_clearing_the_floor"])

    def test_more_qbs_are_drafted_than_ever_clear_the_floor(self):
        """The mechanism in one line. If this ever stops holding, the cliff cannot happen and
        the whole finding is void -- which is the useful thing for it to say."""
        drafted_by_end = max(r["qb_drafted"] for r in self.record["qb_cliff"])
        self.assertGreater(drafted_by_end, self.record["qbs_clearing_the_floor"],
                           "fewer QBs are drafted than clear the floor, so the engine would "
                           "never run out of priceable QBs -- the finding no longer applies")


class TheEngineGoesBlindToQBAndTheRecordSaysWhenTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(RECORD.read_text())

    def test_there_is_a_round_after_which_no_qb_can_be_priced(self):
        first = self.record["first_round_with_no_priceable_qb"]
        self.assertIsNotNone(first, "the instrument found no blind round -- if that is real, "
                                    "#168's sharpening is withdrawn, not silently dropped")
        self.assertLess(first, self.record["draft_rounds"],
                        "the blind round is past the end of the draft, which is not a finding")

    def test_the_blindness_covers_the_majority_of_the_draft_not_a_tail(self):
        """The word #168 uses is 'tails'. This is the assertion that says it is not one."""
        first = self.record["first_round_with_no_priceable_qb"]
        rounds = self.record["draft_rounds"]
        self.assertGreater((rounds - first) / rounds, 0.5,
                           f"blind for rounds {first}-{rounds}, which is a minority of the "
                           "draft -- 'tails' would then be fair and this file overstates it")

    def test_once_blind_it_never_recovers(self):
        """A dip that recovers is a different phenomenon and would need a different account."""
        first = self.record["first_round_with_no_priceable_qb"]
        after = [r for r in self.record["qb_cliff"] if r["round"] >= first]
        self.assertTrue(after)
        for row in after:
            self.assertEqual(row["qb_priced"], 0,
                             f"round {row['round']} prices {row['qb_priced']} QBs again")


class TheUnpricedBlockIsTwoPopulationsTests(unittest.TestCase):
    """The CORRECTION, pinned. `VALUE_MODEL_RESULT.md` first attributed the whole block to the
    pricing gap; the block is 82% a never-priced non-QB core."""

    @classmethod
    def setUpClass(cls):
        cls.comp = json.loads(RECORD.read_text())["composition"]

    def test_the_non_qb_core_does_not_move_with_draft_depth(self):
        """Constancy is the whole argument: rows that were never priceable cannot be what the
        startable floor produced, because the floor only bites as the pool drains."""
        cores = {d: c["non_qb_unpriced"] for d, c in self.comp.items()}
        self.assertEqual(len(set(cores.values())), 1,
                         f"the non-QB unpriced core varies with depth {cores} -- it is not a "
                         "static coverage gap and the correction's reasoning fails")

    def test_the_core_is_the_majority_of_the_block(self):
        for depth, c in self.comp.items():
            with self.subTest(depth=depth):
                self.assertGreater(c["non_qb_unpriced"] / c["unpriced"], 0.5,
                                   f"round {depth}: the non-QB core is not the majority, so "
                                   "'82% vendor coverage' no longer holds")

    def test_the_qb_share_of_the_block_is_the_minority_at_every_depth(self):
        for depth, c in self.comp.items():
            with self.subTest(depth=depth):
                qb = c["unpriced_by_position"].get("QB", 0)
                self.assertLess(qb / c["unpriced"], 0.5,
                                f"round {depth}: QB is now most of the block, which would make "
                                "the ORIGINAL claim right and this correction wrong")


if __name__ == "__main__":
    unittest.main()
