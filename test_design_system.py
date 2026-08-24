import unittest

import design_system as ds


class TokenRgbaTests(unittest.TestCase):
    def test_converts_a_known_token_to_its_exact_rgb_triplet(self):
        # emerald = #16a34a -> (22, 163, 74), the same triplet BADGE_NECESSITY_CSS's
        # rgba(22,163,74,0.18) already spells out literally for "preferred".
        self.assertEqual(ds.token_rgba("emerald", 0.18), "rgba(22,163,74,0.18)")

    def test_a_different_token_produces_a_different_triplet(self):
        self.assertEqual(ds.token_rgba("crimson", 0.18), "rgba(185,28,28,0.18)")

    def test_alpha_is_passed_through_unchanged(self):
        self.assertEqual(ds.token_rgba("emerald", 0.5), "rgba(22,163,74,0.5)")

    def test_unknown_token_name_raises_rather_than_silently_producing_black(self):
        with self.assertRaises(KeyError):
            ds.token_rgba("not-a-real-token", 0.18)


if __name__ == "__main__":
    unittest.main()
