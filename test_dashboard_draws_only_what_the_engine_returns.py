"""The assembled dashboard (`#343`) may draw only what the engine returns.

WHY THIS FILE AND NOT A LOOK AT THE PAGE. Round 4's three designs were hand-authored HTML, so
they could assert anything, and two independent adversaries per design were needed to find what
they asserted. One of them still shipped retired product terminology on BOTH halves of its pair,
caught today only because a committed-file scan finally reached `ui_explore/`. This page is
GENERATED from `front_claims.compose`, so the same questions become assertions.

The product adversary's four verdicts are the frame: REAL (a named function returns it),
REACHABLE (the data exists, nothing computes it), WITHHELD (computable and deliberately refused),
FABRICATED (no basis -- a defect, not a design choice).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui_explore" / "round5"))

import build_dashboard as bd
import design_system as ds
import front_claims as fc

LOUD = json.loads((ROOT / "ui_explore/front_fixture.json").read_text())
QUIET = json.loads((ROOT / "ui_explore/quiet_fixture.json").read_text())


class TheSeverityRampIsVISIBLETests(unittest.TestCase):
    """Round 4's single most repeated failure, now a build-time assertion.

    All three independent designs failed non-text contrast on their chart -- five of six bars
    between 1.25:1 and 2.30:1 against a 3:1 floor, measured by three separate adversaries. The
    shared cause, measured rather than guessed: a LOW value drawn as a DARK gold cannot clear the
    floor on near-black. `line` is 1.27:1 and `line-2` is 1.73:1, which brackets exactly what
    they found. I also failed to verify this myself four times, by eye and by probe, before
    reading the markup instead.
    """

    def test_every_step_of_the_ramp_clears_the_non_text_floor(self):
        for name, token in bd.SEVERITY:
            with self.subTest(step=name):
                self.assertGreaterEqual(ds.contrast_ratio(token, "bg"), bd.NON_TEXT_FLOOR)

    def test_the_ramp_rises_in_brightness_because_that_is_the_only_direction_that_works(self):
        ratios = [ds.contrast_ratio(t, "bg") for _, t in bd.SEVERITY]
        self.assertEqual(sorted(ratios), ratios, "severity must rise in contrast, not fall")

    def test_the_dark_golds_that_failed_round_4_would_still_fail(self):
        """The non-vacuity guard: if the floor ever stopped biting, this would go green."""
        for token in ("line", "line-2", "surface"):
            with self.subTest(token=token):
                self.assertLess(ds.contrast_ratio(token, "bg"), bd.NON_TEXT_FLOOR)

    def test_the_build_refuses_a_ramp_below_the_floor(self):
        real = bd.SEVERITY
        try:
            bd.SEVERITY = (("recede", "line"),) + real[1:]
            with self.assertRaises(SystemExit):
                bd._assert_ramp_is_visible()
        finally:
            bd.SEVERITY = real


class TheTypeFloorIsEnforcedAtBuildTimeTests(unittest.TestCase):
    def test_no_declared_size_is_below_twelve_px(self):
        css = bd.CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)
        sizes = {float(m.group(1))
                 for m in re.finditer(r"font(?:-size)?:[^;}]*?([\d.]+)rem", css)}
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), bd.TYPE_FLOOR_REM)

    def test_small_type_is_declared_in_rem_so_the_floor_needs_no_browser(self):
        """The em chain is what hid a 10.56px size from the first check I ran on this file."""
        css = bd.CSS.format(sans=ds.FONT_SANS, mono=ds.FONT_MONO, display=ds.FONT_DISPLAY)
        self.assertEqual([], re.findall(r"font-size:\s*[\d.]+em", css))

    def test_the_build_refuses_a_size_below_the_floor(self):
        real = bd.CSS
        try:
            bd.CSS = real.replace(".stamp{{font:400 .76rem", ".stamp{{font:400 .72rem")
            with self.assertRaises(SystemExit):
                bd._assert_type_floor()
        finally:
            bd.CSS = real


class ThePageDrawsTheEnginesClaimsAndNoOthersTests(unittest.TestCase):
    def test_every_claim_on_the_page_came_from_compose(self):
        page = bd.build(LOUD)
        shown = fc.compose(LOUD)["shown"]
        self.assertTrue(shown)
        for c in shown:
            with self.subTest(kind=c["kind"]):
                self.assertIn(f'class="claim {c["kind"]}"', page)

    def test_the_band_never_exceeds_the_cap(self):
        page = bd.build(LOUD)
        self.assertLessEqual(page.count('<article class="claim '), fc.CAP)

    def test_a_capped_claim_is_named_rather_than_dropped(self):
        fx = dict(LOUD)
        fx["structural_holes"] = ["K", "DEF"]
        out = fc.compose(fx)
        self.assertTrue(out["hidden"], "fixture must overflow the cap")
        self.assertIn("Also standing", bd.build(fx))

    def test_the_quiet_state_carries_the_engines_check_count_as_its_HERO_figure(self):
        """Updated with the design, not around it. The count used to sit in a sentence below the
        band; it is now the quiet page's `.big` figure, because a page whose only content was
        three small lines read as "too spartan" and was indistinguishable from unfinished. The
        FACT asserted is unchanged -- the number on the page is the engine's, not the renderer's.
        """
        page = bd.build(QUIET)
        summary = fc.checks_summary(fc.compose(QUIET)["checks"])
        self.assertTrue(summary["all_clean"])
        self.assertIn(f'class="big">{summary["ran"]}', page)
        self.assertIn("checks, all clean", page)
        # non-vacuity: a wrong count must not also pass
        self.assertNotIn(f'class="big">{summary["ran"] + 1}', page)

    def test_the_check_count_is_not_repeated_once_it_is_the_hero(self):
        """The standing constraint: the same fact twice is the failure it names."""
        page = bd.build(QUIET)
        self.assertEqual(1, page.count("checks, all clean"))


class ForbiddenQuantitiesAppearNowhereTests(unittest.TestCase):
    """`BRIEF.md`'s forbidden table, asserted instead of trusted. The most dangerous mock in the
    prior round was the densest and most professional one, with six invented panels."""

    FORBIDDEN = (
        "team rating", "team index", "playoff odds", "title odds", "win probability",
        "championship odds", "% rostered", "percent rostered", "trending add", "primary add",
        "questionable", "roster score", "power rank", "grade:",
    )

    def test_no_page_state_names_a_withheld_or_fabricated_quantity(self):
        for label, fx in (("loud", LOUD), ("quiet", QUIET)):
            page = bd.build(fx).lower()
            for phrase in self.FORBIDDEN:
                with self.subTest(state=label, phrase=phrase):
                    self.assertNotIn(phrase, page)

    def test_no_page_asserts_a_rank_the_engine_never_computes(self):
        """`#336b`, guarded from the start rather than after months in the tree."""
        for label, fx in (("loud", LOUD), ("quiet", QUIET)):
            page = bd.build(fx).lower()
            for phrase in ("bottom of this league", "worst at", "last in the league",
                           "ranks ", "best in the league"):
                with self.subTest(state=label, phrase=phrase):
                    self.assertNotIn(phrase, page)

    def test_the_page_does_not_flatter(self):
        """`VOICE.md` rule 3. A clean week is a fact, not a compliment."""
        for label, fx in (("loud", LOUD), ("quiet", QUIET)):
            page = bd.build(fx).lower()
            for phrase in ("all systems", "crushing it", "you're good", "great job",
                           "well done", "congratulations", "nothing needs you"):
                with self.subTest(state=label, phrase=phrase):
                    self.assertNotIn(phrase, page)


class FiveRoomsAndOneDockTests(unittest.TestCase):
    """Every round-4 design drew six identical doors and was wrong about one of them."""

    def test_the_five_real_views_are_the_only_rooms(self):
        page = bd.build(LOUD)
        self.assertEqual(5, len(bd.ROOMS))
        for room in bd.ROOMS:
            self.assertIn(f">{room}<", page)

    def test_rooms_that_do_not_exist_are_not_advertised(self):
        page = bd.build(LOUD)
        for absent_room in ("Player Compare", "Trade Finder", "Waiver Wire", "Pick Calculator",
                            "Roster Health", "League Notes", "Analytics"):
            with self.subTest(room=absent_room):
                self.assertNotIn(absent_room, page)

    def test_the_dock_is_marked_as_a_dock_and_not_a_sixth_room(self):
        page = bd.build(LOUD)
        self.assertIn("not a sixth room", page)
        rooms_block = page.split('class="rooms"')[1].split("</div>")[0]
        self.assertNotIn(bd.DOCK, rooms_block)


class TheCurrencyIsStampedOnTheFigureTests(unittest.TestCase):
    """`#341`: grading belongs in league points; the conversion is unbuilt, so the page says what
    the figure actually is rather than letting a reader assume it is their league's scoring."""

    def test_the_bye_figure_carries_a_currency_stamp(self):
        page = bd.build(LOUD)
        self.assertIn('class="currency"', page)
        self.assertIn("trade value", page)

    def test_the_stamp_says_it_is_not_the_leagues_points(self):
        self.assertIn("not this league's points", bd.CURRENCY_TRADE_VALUE)

    def test_a_quiet_page_with_no_bye_claim_needs_no_stamp_on_a_claim(self):
        """The stamp belongs to a figure, not to the page. No figure, no stamp."""
        self.assertEqual([], fc.compose(QUIET)["shown"])


class ExpansionsOnlyWhereTheEngineComputesASecondLayerTests(unittest.TestCase):
    def test_the_four_expandable_kinds_get_a_popover(self):
        fx = dict(LOUD)
        fx["structural_holes"] = ["K"]
        for c in fc.compose(fx)["shown"]:
            with self.subTest(kind=c["kind"]):
                self.assertTrue(bd.expansion(c, fx), f"{c['kind']} should expand")

    def test_an_injury_flag_does_not_expand_because_the_engine_has_no_second_layer(self):
        """`is_material_injury_status` returns a BOOLEAN. A drill-down would invent severity, and
        this is exactly where a designer would most want one."""
        self.assertEqual("", bd.expansion({"kind": "injury"}, LOUD))

    def test_the_popover_is_an_overlay_not_inline_disclosure(self):
        """The owner's ruling: a popout or pop-over, not in-line in the dashboard."""
        page = bd.build(LOUD)
        self.assertIn("popovertarget=", page)
        self.assertIn("popover>", page)
        self.assertNotIn("<details", page)


if __name__ == "__main__":
    unittest.main()
