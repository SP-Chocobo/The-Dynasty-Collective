"""The landing page (`#344`) may rank leagues by RUNG and count them, and may do nothing else.

WHY THIS SURFACE IS THE MOST DANGEROUS ONE IN THE APP. Its natural visual form is N rows plus a
summary, and that shape begs for a summary that cannot exist. A portfolio health score, a
worst-league ranking and a cross-league total are each one line of code away and all three are
unreachable -- so the refusals are asserted here rather than left to a reviewer's eye.

CROSS-LEAGUE MAGNITUDE IS NOT COMPARABLE, and that is the subtle one. A bye costing 95 in one
league and 95 in another are different units wearing the same label: `bye_collision` prices in
whatever currency its caller supplies, each league applies its own scoring, and
`set_league_format` selects a different rankings export per format (`#341`). The ladder RUNG
compares across leagues -- a hole is a hole. The FIGURE does not.
"""
from __future__ import annotations

import glob
import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui_explore" / "round5"))

import build_landing as bl
import front_claims as fc

PATHS = sorted(glob.glob(str(ROOT / "ui_explore/seats/seat*.json")))

#: The page's closing line NAMES the aggregates it refuses to draw.
REFUSAL = "A count of real things, never a score."


def _claims_region(page: str) -> str:
    """The page's CLAIMS -- provenance and refusal text removed before any forbidden-phrase ban.

    THE WORD IS NOT THE DEFECT; THE CLAIM IS. A naive ban over the whole document failed twice
    here, both times on honest text: the closing refusal ("no portfolio grade, no worst-league
    ranking and no cross-league total exists to show") and the stand-in stamp ("narrower than a
    real portfolio's"). A forbidden-phrase scan cannot tell an ASSERTION from its DENIAL, so an
    honest page that names what it refuses and what it constructed fails the same check as a
    dishonest one that asserts them.

    `stamp` and `absent` are this system's provenance grammar, and naming what is missing or
    constructed is their entire job. They are excluded by construction rather than case by case,
    and the refusal is excised by name. Both excisions assert their own target exists first, so
    a rename makes this LOUD rather than silently widening the loophole.
    """
    assert REFUSAL in page, "the refusal sentence is missing; the excision would be silent"
    body = page.split(REFUSAL)[0]
    assert 'class="stamp"' in body, "no provenance stamp found; the excision would be silent"
    body = re.sub(r'<(span|p)\s+class="stamp"[^>]*>.*?</\1>', " ", body, flags=re.S)
    return re.sub(r'<span class="absent"[^>]*>.*?</span>', " ", body, flags=re.S)


class TheOrderIsByRungNeverByFigureTests(unittest.TestCase):
    def test_there_are_leagues_to_rank(self):
        self.assertGreaterEqual(len(PATHS), 2, "the fixture set must exercise ordering")

    def test_rows_are_ordered_by_ladder_rung(self):
        rungs = [r["rung"] for r in bl.league_rows(PATHS)]
        self.assertEqual(sorted(rungs), rungs, "a lower rung appeared after a higher one")

    def test_a_quiet_league_sorts_last_and_is_not_dropped(self):
        rows = bl.league_rows(PATHS)
        quiet = [r for r in rows if not r["shown"]]
        self.assertTrue(quiet, "fixture set must contain a quiet league to test this")
        self.assertEqual(rows[-len(quiet):], quiet, "quiet leagues must sort last")
        page = bl.build(PATHS)
        for r in quiet:
            self.assertIn(str(r["fx"].get("team")), page, "a quiet league was filtered out")

    def test_a_quiet_league_states_what_it_checked(self):
        """`VOICE.md` rule 5. Seeing that a league wants nothing is the page's whole value, and
        "nothing open" without the checks is a pronouncement rather than a report."""
        page = bl.build(PATHS)
        self.assertIn("checks, all clean", page)

    def test_the_order_does_not_follow_the_figure(self):
        """NON-VACUITY. If the rows happened to be in figure order too, the ordering test above
        would pass for the wrong reason -- the `#333` hollow-fixture trap. This asserts the two
        orders genuinely differ on this fixture set."""
        rows = bl.league_rows(PATHS)
        def fig(r):
            top = r["top"]
            return -(top.get("worst_week_loss") or top.get("count") or 0) if top else 0
        self.assertNotEqual([id(r) for r in sorted(rows, key=fig)], [id(r) for r in rows],
                            "fixture is hollow: rung order and figure order agree on it")


class TheHeadlineIsACountNeverAGradeTests(unittest.TestCase):
    def test_the_tally_is_the_number_of_leagues_with_something_open(self):
        rows = bl.league_rows(PATHS)
        open_n = sum(1 for r in rows if r["shown"])
        page = bl.build(PATHS)
        self.assertIn(f"{open_n} of {len(rows)} have something open", page)

    def test_no_cross_league_aggregate_is_drawn(self):
        """CHECKED AGAINST THE CLAIMS, NOT THE WHOLE PAGE, and the reason is a test-design
        lesson worth keeping.

        The first version of this test banned these phrases across the entire document and
        FAILED -- on the page's own refusal. The closing line reads "no portfolio grade, no
        worst-league ranking and no cross-league total exists to show", so a naive substring ban
        trips on "portfolio" and on "league rank" inside "worst-league ranking". **A
        forbidden-phrase scan cannot tell an assertion from its denial**, which means an honest
        page that NAMES what it refuses fails the same check as a dishonest one that asserts it.

        So the ban runs over the claims region with the refusal excised, and
        `test_the_page_says_outright_that_no_score_exists` asserts the refusal separately. Both
        halves are needed: one that the page does not draw these, one that it says so.
        """
        page = _claims_region(bl.build(PATHS)).lower()
        for phrase in ("portfolio", "overall score", "health score", "total value",
                       "across all leagues:", "worst league", "best league", "league rank",
                       "combined", "aggregate"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, page, f"{phrase!r} is drawn as a claim")

    def test_the_page_says_outright_that_no_score_exists(self):
        self.assertIn("never a score", bl.build(PATHS))


class ForbiddenQuantitiesAppearNowhereTests(unittest.TestCase):
    def test_no_withheld_or_fabricated_quantity(self):
        page = _claims_region(bl.build(PATHS)).lower()
        for phrase in ("team rating", "playoff odds", "win probability", "% rostered",
                       "questionable", "power rank", "grade:", "letter grade"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, page)

    def test_no_rank_of_teams_within_a_position(self):
        page = _claims_region(bl.build(PATHS)).lower()
        for phrase in ("bottom of this league", "worst at", "last in the league"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, page)


class EveryRowIsTheEnginesJudgmentTests(unittest.TestCase):
    def test_each_row_carries_its_leagues_own_top_claim(self):
        for r in bl.league_rows(PATHS):
            with self.subTest(team=r["fx"].get("team")):
                expected = fc.compose(r["fx"])["shown"]
                self.assertEqual(expected[0] if expected else None, r["top"])

    def test_the_open_count_is_shown_plus_hidden(self):
        for r in bl.league_rows(PATHS):
            band = fc.compose(r["fx"])
            self.assertEqual(len(band["shown"]) + len(band["hidden"]), r["open"])


class TheStandInIsStampedTests(unittest.TestCase):
    """A constructed fixture that does not say so is a fabricated claim (`#187`)."""

    def test_the_page_says_the_data_is_a_stand_in(self):
        self.assertIn("constructed stand-in data", bl.build(PATHS))

    def test_the_stamp_says_why_the_spread_is_narrower_than_a_real_portfolio(self):
        self.assertIn("Real leagues differ in format", bl.STANDIN)


class AnAbsenceIsStatedOnceNotOncePerRowTests(unittest.TestCase):
    """The first render put a bare em dash at the top of all twelve rows, so the most prominent
    thing on a page about CHOOSING a league was the thing that was missing -- and then repeating
    it per row wrapped every meta line onto two. An absence identical on every row is noise, and
    the standing constraint already forbids that."""

    def test_the_missing_league_name_is_stated_once(self):
        rows = bl.league_rows(PATHS)
        if any(r["fx"].get("league_name") for r in rows):
            self.skipTest("fixture set carries league names; nothing to state once")
        page = bl.build(PATHS)
        self.assertEqual(1, page.count("no league names in this capture"))

    def test_each_row_is_named_by_its_team_when_the_league_name_is_absent(self):
        rows = bl.league_rows(PATHS)
        page = bl.build(PATHS)
        for r in rows:
            if not r["fx"].get("league_name"):
                with self.subTest(team=r["fx"].get("team")):
                    self.assertIn(f'class="lname">{r["fx"]["team"]}<', page)


if __name__ == "__main__":
    unittest.main()
