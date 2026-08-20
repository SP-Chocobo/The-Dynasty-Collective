import shutil
import tempfile
import unittest
from pathlib import Path

import league_format as lf


class LeagueFormatOverrideTests(unittest.TestCase):
    """Points FORMATS_PATH at a throwaway temp file for the duration of each test, never
    touching real data/league_formats.json."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_path = lf.FORMATS_PATH
        lf.FORMATS_PATH = Path(self._tmpdir) / "league_formats.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, lf, "FORMATS_PATH", self._orig_path)

    def test_no_override_set_returns_none(self):
        self.assertIsNone(lf.get_format_override("league123"))

    def test_set_and_get_round_trips(self):
        lf.set_format_override("league123", lf.BEST_BALL)
        self.assertEqual(lf.get_format_override("league123"), lf.BEST_BALL)

    def test_setting_chopped_round_trips(self):
        lf.set_format_override("league123", lf.CHOPPED)
        self.assertEqual(lf.get_format_override("league123"), lf.CHOPPED)

    def test_setting_standard_clears_the_override(self):
        lf.set_format_override("league123", lf.BEST_BALL)
        lf.set_format_override("league123", lf.STANDARD)
        self.assertIsNone(lf.get_format_override("league123"))

    def test_setting_none_clears_the_override(self):
        lf.set_format_override("league123", lf.CHOPPED)
        lf.set_format_override("league123", None)
        self.assertIsNone(lf.get_format_override("league123"))

    def test_leagues_are_independent(self):
        lf.set_format_override("league_a", lf.BEST_BALL)
        self.assertIsNone(lf.get_format_override("league_b"))

    def test_format_guidance_exists_for_every_non_standard_option(self):
        for option in lf.FORMAT_OPTIONS:
            if option == lf.STANDARD:
                continue
            self.assertIn(option, lf.FORMAT_GUIDANCE, option)
            self.assertTrue(lf.FORMAT_GUIDANCE[option].strip(), option)


if __name__ == "__main__":
    unittest.main()
