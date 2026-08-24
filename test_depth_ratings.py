"""depth_ratings is a pure, relocated judgment -- these tests pin the exact thresholds already
shipped in the Trade Calculator (>=1.3x Strong, <=0.7x Weak) so the extraction (Fable's League
review, F3) can't quietly drift from what was already live."""

import unittest

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


if __name__ == "__main__":
    unittest.main()
