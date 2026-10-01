"""depth_ratings is a pure, relocated judgment -- these tests pin the exact thresholds already
shipped in the Trade Calculator (>=1.3x Strong, <=0.7x Weak) so the extraction (Fable's League
review, F3) can't quietly drift from what was already live."""

import unittest
from pathlib import Path

import depth_ratings
import lineup_readiness
import ui_source
from depth_ratings import depth_label


def _cell(count, value=None):
    return {"count": count, "value": value}


class DepthLabelTests(unittest.TestCase):
    def test_no_peer_data_returns_none(self):
        self.assertIsNone(depth_label(_cell(3, 100), []))

    def test_zero_count_reads_as_none_rostered(self):
        peers = [_cell(3, 100), _cell(0, None)]
        self.assertEqual(depth_label(_cell(0, None), peers), "None — no rostered players here")

    def test_strong_at_exactly_the_threshold(self):
        # avg = (130+100+100)/3 = 110; 130/110 = 1.1818... not strong yet at count 130.
        # Use a cleaner boundary: avg=100, cell=130 -> ratio exactly 1.3.
        peers = [_cell(1, 100), _cell(1, 100), _cell(1, 100)]
        self.assertEqual(depth_label(_cell(1, 130), peers), "Strong")

    def test_weak_at_exactly_the_threshold(self):
        peers = [_cell(1, 100), _cell(1, 100), _cell(1, 100)]
        self.assertEqual(depth_label(_cell(1, 70), peers), "Weak")

    def test_average_between_the_thresholds(self):
        peers = [_cell(1, 100), _cell(1, 100), _cell(1, 100)]
        self.assertEqual(depth_label(_cell(1, 100), peers), "Average")

    def test_falls_back_to_count_when_any_peer_lacks_a_value(self):
        peers = [_cell(3, 100), _cell(1, None)]  # one peer has no value data
        # avg over counts: (3+1)/2 = 2; cell count=3 -> ratio 1.5 -> Strong
        self.assertEqual(depth_label(_cell(3, 100), peers), "Strong")

    def test_zero_average_returns_none_rather_than_dividing_by_zero(self):
        # count=1 (nonzero) so the "zero rostered" guard doesn't fire first; the peer
        # value-average is genuinely zero, which is the branch this test targets.
        peers = [_cell(1, 0), _cell(1, 0)]
        self.assertIsNone(depth_label(_cell(1, 0), peers))

    def test_own_cell_included_in_the_average_baseline(self):
        # Matches the original behavior: the average is over every team INCLUDING the one
        # being rated, not just its peers.
        peers = [_cell(1, 200)]  # only entry is the cell itself
        self.assertEqual(depth_label(_cell(1, 200), peers), "Average")


class LabelVocabularyTests(unittest.TestCase):
    """One vocabulary, owned by the producer, with no re-spelled copies anywhere downstream.

    The literal "None — no rostered players here" (em dash) existed in FOUR places: this
    module, two app.py sites, and lineup_readiness. They fail ASYMMETRICALLY under a rename:
    the two membership tests go quietly silent (no thin position is ever flagged again), while
    the Trade Calculator's _DEPTH_RANK lookup silently reclassifies every empty position room
    as a measured, mid-league "Average" and feeds that into a trade verdict."""

    def test_the_label_returned_is_the_named_constant_itself(self):
        peers = [_cell(3, 100), _cell(0, None)]
        self.assertIs(depth_label(_cell(0, None), peers), depth_ratings.NO_PLAYERS_LABEL)

    def test_every_rating_is_drawn_from_the_declared_vocabulary(self):
        peers = [_cell(4, 400), _cell(1, 50), _cell(2, 150)]
        for cell in (_cell(4, 400), _cell(1, 50), _cell(2, 150), _cell(0, None)):
            self.assertIn(depth_label(cell, peers), depth_ratings.LABELS)

    def test_the_docstring_no_longer_disagrees_with_the_string_it_describes(self):
        # The module docstring wrote the label with an ASCII "--" while the code returned an
        # em dash -- the vocabulary drifting inside a single file, before any consumer.
        source = Path(depth_ratings.__file__).read_text()
        self.assertNotIn("None -- no rostered players here", source)

    def test_the_thin_reader_consumes_the_producers_tuple_rather_than_copying_it(self):
        self.assertIs(lineup_readiness._THIN_LABELS, depth_ratings.THIN_LABELS)

    def test_no_owned_consumer_respells_the_literal(self):
        # Scoped to the consumers this pass owns. roster_diagnostics.py carries a FIFTH copy of
        # the same literal and is outside this file-ownership boundary -- reported, not edited.
        surfaces = {
            "lineup_readiness.py": Path(lineup_readiness.__file__).read_text(),
            "the UI surface": ui_source.text(),
        }
        for name, source in surfaces.items():
            self.assertNotIn(depth_ratings.NO_PLAYERS_LABEL, source, f"{name} respells the label")


if __name__ == "__main__":
    unittest.main()
