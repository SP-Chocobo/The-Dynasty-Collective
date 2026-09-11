"""The captured F&F rulebook reproduces Sleeper's OWN numbers, on real box scores.

WHY THIS TEST IS DIFFERENT FROM EVERY OTHER SCORING TEST IN THE REPO. All of them are
self-referential: they assert that compute_points_from_stats returns what the repo believes the
rules to be. None of them could catch a mis-transcribed rulebook, because the rulebook is the
thing being asserted. `data/league_captures/fourth_and_forever.json` records its own
capture_method as "transcribed from Sleeper Scoring Settings screenshots supplied by the owner"
-- hand entry, which is exactly where a quiet error lives, and it had never been checked against
a number Sleeper computed.

These four lines were itemised by the Sleeper app itself and read off the owner's screen, with
the app's own total beside them. Agreement to the cent is therefore an EXTERNAL check on two
things at once: that the transcription is faithful, and that compute_points_from_stats -- the
function the whole scoring-aware path runs through (#192/#213) -- implements the rules Sleeper
actually applies.

PROVENANCE: Fourth and Forever, 2026 week 1, read from the live Sleeper app. Team SPChocobo
showed 79.60 from these four starters, which the totals assertion below reproduces.

COVERAGE, chosen because between them they exercise nearly every term the rulebook has:
  McCaffrey   rushing + receiving yardage, rush_fd, receptions, no scores
  Smith-Njigba receiving TD plus BOTH 40+ bonuses at once (rec_40p and rec_td_40p)
  Stevenson   rush_fd AND rec_fd in one line -- the 0.25 / 0.5 asymmetry
  Purdy       pass_cmp bonus, pass_yd at 0.04, pass_td at 4, pass_int at -2, rushing QB
"""
import json
import unittest

import sleeper_client as sc

CAPTURE = "data/league_captures/fourth_and_forever.json"

# (name, what the Sleeper app displayed, the line the Sleeper app itemised)
LIVE = [
    ("C. McCaffrey", 11.80,
     {"rush_att": 10, "rush_yd": 68, "rush_fd": 2, "rec": 5, "rec_yd": 20}),
    ("J. Smith-Njigba", 30.20,
     {"rec": 8, "rec_yd": 122, "rec_td": 1, "rec_fd": 4, "rec_40p": 1, "rec_td_40p": 1}),
    ("R. Stevenson", 13.00,
     {"rush_att": 18, "rush_yd": 51, "rush_fd": 2, "rec": 5, "rec_yd": 44, "rec_fd": 1}),
    ("B. Purdy", 24.60,
     {"pass_cmp": 25, "pass_att": 34, "pass_yd": 205, "pass_td": 3, "pass_int": 1,
      "rush_att": 5, "rush_yd": 29, "rush_fd": 4}),
]
APP_TOTAL = 79.60


def _ff_scoring():
    with open(CAPTURE) as fh:
        return {k: v["value"] for k, v in json.load(fh)["scoring_settings_observed"].items()}


class TheCaptureAgreesWithSleeper(unittest.TestCase):

    def test_every_live_line_reproduces_to_the_cent(self):
        scoring = _ff_scoring()
        for name, shown, line in LIVE:
            with self.subTest(player=name):
                got = sc.compute_points_from_stats(line, scoring)
                self.assertAlmostEqual(
                    got, shown, places=2,
                    msg=f"{name}: the capture scores {got:.2f}, the live app showed {shown:.2f}. "
                        f"Either the transcription in {CAPTURE} is wrong, or "
                        f"compute_points_from_stats no longer implements the rules Sleeper "
                        f"applies. Both are serious; neither is a test to relax.")

    def test_the_four_starters_sum_to_what_the_app_showed(self):
        """The per-player check could pass on compensating errors; the total could not."""
        scoring = _ff_scoring()
        total = sum(sc.compute_points_from_stats(line, scoring) for _, _, line in LIVE)
        self.assertAlmostEqual(total, APP_TOTAL, places=2)

    def test_the_asymmetry_the_rulebook_is_built_around(self):
        """rec_fd pays DOUBLE rush_fd. It is the most distinctive thing about this league and
        the easiest single value to mis-transcribe, so it is asserted directly rather than only
        implied by the totals above."""
        scoring = _ff_scoring()
        self.assertEqual(scoring["rec_fd"], 0.5)
        self.assertEqual(scoring["rush_fd"], 0.25)
        self.assertEqual(scoring["rec_fd"], 2 * scoring["rush_fd"])

    def test_a_wrong_rulebook_would_fail_this(self):
        """The control. Without it, 'the scorer ignores scoring_settings entirely' passes every
        assertion above. The battery's fixture league is a real, different rulebook -- full PPR,
        no TE bonus, no first-down scoring -- and must NOT reproduce these numbers."""
        import run_draft_battery as rdb
        fixture = rdb.scoring_settings_from_capture()
        differing = 0
        for name, shown, line in LIVE:
            if abs(sc.compute_points_from_stats(line, fixture) - shown) >= 0.005:
                differing += 1
        self.assertEqual(differing, len(LIVE),
                         "at least one line scored the same under a materially different "
                         "rulebook -- the scorer is not reading scoring_settings")


if __name__ == "__main__":
    unittest.main()
