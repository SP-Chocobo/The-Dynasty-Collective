"""#174: depth_exposure crossed the snapshot boundary without the companion that reads it.

draft_room emits depth_exposure AND depth_basis on every board row. CandidateSnapshot carried
only the number, so every consumer past that boundary -- the chair prose, the board UI,
screen_context -- saw a 0.0 that could mean "measured, this position carries no exposure" or
"never measured" and had no way to tell. mockups/common.py documented the drop verbatim while
it was still live.

MEASURED on a real mid-draft board (12-team dynasty superflex from the capture, roster 1
deliberately STACKED to 4 RB / 4 WR / 2 QB so a surplus actually exists to measure):

    measured, exposure > 0                806 rows
    vacant,   exposure 0.0              1,218 rows
    measured, exposure 0.0                  0 rows

Not one measured zero. So every 0.0 any consumer ever saw meant "not measured", and every one
of them read as "no depth risk at this position".

THE FIRST VERSION OF THIS MEASUREMENT WAS WRONG and the correction is the point: a roster of
five players at five positions reported 2024/2024 "not measured", which is CORRECT for that
roster and says nothing about the engine. The population has to be able to produce the state
under test before a rate over it means anything.
"""

from __future__ import annotations

import dataclasses
import inspect
import unittest

import lineup_optimizer as lo
import pick_debate
import pick_synthesis as ps


class TheCompanionCrossesTheBoundaryTests(unittest.TestCase):

    def test_the_snapshot_carries_the_basis(self):
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("depth_exposure", names)
        self.assertIn("depth_basis", names, "the number crosses without its companion")

    def test_the_builder_actually_populates_it_from_the_board_row(self):
        source = inspect.getsource(ps.build_snapshot)
        self.assertIn('"depth_basis": row.get("depth_basis")', source)


class TheVocabularyHasOneHomeTests(unittest.TestCase):

    def test_every_basis_the_optimizer_can_emit_has_words(self):
        emitted = {lo.EXPOSURE_MEASURED, lo.EXPOSURE_VACANT,
                   lo.EXPOSURE_NO_SURPLUS, lo.EXPOSURE_NOT_APPLICABLE}
        self.assertEqual(emitted, set(lo.EXPOSURE_BASIS_LABELS))

    def test_the_consumer_re_exports_rather_than_copies(self):
        # lineup_optimizer is closed to snapshot consumers, so pick_debate cannot import it.
        # The words still get one home: the same objects, bound at the boundary module.
        self.assertIs(ps.EXPOSURE_BASIS_LABELS, lo.EXPOSURE_BASIS_LABELS)
        self.assertEqual(ps.EXPOSURE_MEASURED, lo.EXPOSURE_MEASURED)
        source = inspect.getsource(pick_debate)
        for words in lo.EXPOSURE_BASIS_LABELS.values():
            self.assertNotIn(words, source, "pick_debate restates the words")

    def test_the_consumer_does_not_spell_the_token_as_its_own_literal(self):
        source = inspect.getsource(pick_debate._depth_term)
        self.assertIn("EXPOSURE_MEASURED", source)
        self.assertNotIn('"measured"', source)


class TheChairProseQualifiesTheNumberTests(unittest.TestCase):

    class _C:
        def __init__(self, exposure, basis):
            self.depth_exposure, self.depth_basis = exposure, basis

    def test_a_measured_number_is_stated_plainly(self):
        out = pick_debate._depth_term(self._C(4.5, lo.EXPOSURE_MEASURED))
        self.assertIn("+4.5", out)
        self.assertNotIn("NOT a measurement", out)

    def test_a_measured_ZERO_is_still_stated_as_a_number(self):
        # The repair must not turn a measured zero into a disclaimer: "this position carries no
        # exposure" is a real finding.
        out = pick_debate._depth_term(self._C(0.0, lo.EXPOSURE_MEASURED))
        self.assertIn("+0.0", out)
        self.assertNotIn("NOT a measurement", out)

    def test_an_UNMEASURED_zero_says_so_and_names_which_state(self):
        out = pick_debate._depth_term(self._C(0.0, lo.EXPOSURE_VACANT))
        self.assertIn("NOT a measurement", out)
        self.assertIn(lo.EXPOSURE_BASIS_LABELS[lo.EXPOSURE_VACANT], out)

    def test_every_unmeasured_state_produces_a_distinct_sentence(self):
        seen = {pick_debate._depth_term(self._C(0.0, b))
                for b in (lo.EXPOSURE_VACANT, lo.EXPOSURE_NO_SURPLUS,
                          lo.EXPOSURE_NOT_APPLICABLE)}
        self.assertEqual(len(seen), 3, "two unmeasured states read identically")

    def test_an_absent_number_still_says_it_was_not_computed(self):
        out = pick_debate._depth_term(self._C(None, None))
        self.assertIn("not computed", out)

    def test_the_arithmetic_is_never_altered_by_the_qualification(self):
        # The clause qualifies the number; it must not change it. A model told the parts and
        # the whole has to be able to add them.
        for basis in (lo.EXPOSURE_MEASURED, lo.EXPOSURE_VACANT, lo.EXPOSURE_NO_SURPLUS):
            self.assertIn("+2.5", pick_debate._depth_term(self._C(2.5, basis)))


if __name__ == "__main__":
    unittest.main()
