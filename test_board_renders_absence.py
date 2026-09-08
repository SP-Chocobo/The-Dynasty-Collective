"""#173: what the board's JavaScript ACTUALLY renders for a player it cannot price.

The register recorded that the JS mirror renders `null`, `NaN` and `|| 0` for an unpriced
leader -- the exact state #154's feasibility backstop can produce. Measured here rather than
read: it does not, and has not for some time. This file exists because nothing PINNED that.
The register believed the behaviour was broken, so no test was ever written for it, and a
correct behaviour with no test is one edit from becoming the recorded defect.

TWO THINGS THIS FILE IS CAREFUL ABOUT, both learned by getting them wrong first:

1. THE STATIC HTML PROVES NOTHING. Every candidate row is built client-side by render(). The
   first version of this probe stripped <script> before searching for "null" -- which removes
   precisely the code under test, and reported a clean result about a document that contained
   no candidate rows at all. The board has to be EXECUTED.

2. AN UNPRICED LEADER MUST BE CONSTRUCTED, not waited for. Unpriced rows sort last by
   _board_order, so a natural board almost never puts one first. candidates[0] with no price
   is what the backstop produces in the degenerate late-draft regime, and it is the one case
   where every leader-relative calculation in the JS (`ordered[0].uv`, `ordered[0].tav`) has
   nothing to work with.
"""

from __future__ import annotations

import os
import re
import unittest

import draft_board_ui as ui
import pick_synthesis as ps

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def _has_browser() -> bool:
    if not os.path.exists(CHROME):
        return False
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


def _candidate(pid: str, name: str, *, priced: bool) -> ps.CandidateSnapshot:
    """A candidate that is either fully priced or fully unpriced -- no half states, because the
    half states are their own question and this one is about the total absence."""
    return ps.CandidateSnapshot(
        player_id=pid, name=name, position="RB", team="SF",
        bpa=(12.0 if priced else None), bpa_source="draft_sharks", confidence=80.0,
        universal_value=(12.0 if priced else None), need_bonus=0.0, eligibility_bonus=0.0,
        team_acquisition_value=(12.0 if priced else None),
        survival_probability=(0.5 if priced else None),
        intervening_picks=(11 if priced else None),
        opportunity_cost=None, expected_value_of_waiting=None,
        denial_value=None, denial_basis="no_rival_priced", denial_team=None,
        rival_premium=None, positional_forfeit=None, position_expected_taken=None,
        positional_cliff=None, position_run_detected=False,
        pick_necessity=50.0, necessity_label="CLOSE CALL", near_tie_with_leader=None,
        cliff_protection=False, block_opportunity=False, pure_value=False,
        context_elevated=False, consensus_rank=None, consensus_tier=None, reach_label=None,
        projected_points=(180.0 if priced else None),
    )


def _board_html(*candidates) -> str:
    snap = ps.PickSnapshot(
        pick_label="R19.01", round=19, my_roster_id="1", candidates=tuple(candidates),
        user_selected_player_id=None, picks_consumed=216,
        data_freshest_date="2026-09-07", decision_regime="contested",
    )
    return ui.render_board_html(ui.serialize_snapshot(snap, pick_header="R19.01", state_tags=[]))


class ThePayloadCarriesAbsenceAsNullTests(unittest.TestCase):
    """No browser needed: the boundary itself must not substitute a number."""

    def test_an_unpriced_candidate_crosses_as_null_never_as_zero(self):
        payload = ui.serialize_snapshot(
            ps.PickSnapshot(pick_label="R19.01", round=19, my_roster_id="1",
                            candidates=(_candidate("1", "Unpriced", priced=False),),
                            user_selected_player_id=None, picks_consumed=216,
                            data_freshest_date="2026-09-07", decision_regime="contested"),
            pick_header="R19.01", state_tags=[])
        row = payload["candidates"][0]
        for field in ("uv", "tav", "proj", "survival"):
            self.assertIsNone(row[field], f"{field} was substituted rather than carried absent")
            self.assertNotEqual(row[field], 0, f"{field} crossed the boundary as a zero")

    def test_the_javascript_contains_no_zero_coalescing_at_all(self):
        # `x || 0` is the single idiom that turns an absence into a measured zero in JS, and it
        # does so silently. Its total absence is the structural half of this guard.
        source = open("draft_board_ui.py", encoding="utf-8").read()
        js = source[source.index("const ABSENT"):]
        self.assertEqual(re.findall(r"\|\|\s*0[^\w]", js), [])


@unittest.skipUnless(_has_browser(), "needs the bundled Chromium")
class TheRenderedBoardShowsNoMachineWordsTests(unittest.TestCase):
    """THE ONE THAT MATTERS. Execute the page and read what a person would see."""

    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        import tempfile
        html = _board_html(_candidate("1", "Unpriced Leader", priced=False),
                           _candidate("2", "Priced Second", priced=True))
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as fh:
            fh.write(html)
            cls._path = fh.name
        cls._errors = []
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            page = browser.new_page()
            page.on("pageerror", lambda e: cls._errors.append(str(e)))
            page.on("console",
                    lambda m: cls._errors.append(f"console.{m.type}: {m.text}")
                    if m.type == "error" else None)
            page.goto(f"file://{cls._path}")
            page.wait_for_timeout(400)
            cls._rows = len(page.query_selector_all(".row"))
            rows = page.query_selector_all(".row")
            if rows:
                rows[0].click()          # expand the leader: the focus panel holds most numbers
                page.wait_for_timeout(300)
            cls._text = page.inner_text("body")
            browser.close()

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls._path)
        except OSError:
            pass

    def test_the_board_actually_rendered(self):
        # Non-vacuity: a page that failed to render has no machine words either.
        self.assertEqual(self._rows, 2, "the board did not render its rows -- nothing was tested")
        self.assertIn("Unpriced Leader", self._text)
        self.assertIn("Priced Second", self._text)

    def test_the_page_raised_nothing(self):
        self.assertEqual(self._errors, [])

    def test_no_machine_word_reaches_the_reader(self):
        for token in ("null", "NaN", "undefined", "Infinity"):
            with self.subTest(token=token):
                self.assertEqual(re.findall(rf"\b{token}\b", self._text), [],
                                 f"{token} rendered where a person can read it")

    def test_the_unpriced_leader_shows_the_absence_marker_on_every_metric(self):
        leader = self._text[:self._text.index("Priced Second")]
        for metric in ("UV", "ACQ", "PROJ", "SURV"):
            with self.subTest(metric=metric):
                self.assertRegex(leader, rf"{metric}\s*—",
                                 f"{metric} did not render as absent for an unpriced leader")

    def test_the_priced_row_still_shows_its_real_numbers(self):
        # The absence marker must not have eaten the measurements.
        second = self._text[self._text.index("Priced Second"):]
        self.assertIn("12", second)
        self.assertIn("180", second)
        self.assertIn("50%", second)

    def test_the_prose_declines_rather_than_inventing_a_survival(self):
        self.assertIn("isn't estimable right now", self._text)


if __name__ == "__main__":
    unittest.main()
