"""`#328`. The mockups' palette is DERIVED, and the built pages are guarded.

THE GAP THIS CLOSES, measured when it was found: **28 of 28 pages under `mockups/` carried
superseded hexes**, and `grep -c pill-IDP mockups/index.html` returned **0** — so every page was
a pre-`#311` output, drawing DL, LB and DB in one colour and omitting IDP entirely.

Two separate causes, both invisible because a page that is never rebuilt never fails:

1. `c_variants.py` spelled `const FACET = {...}` BY HAND, in source, so no rebuild could repair
   it. Four values were superseded, IDP was missing, and DL/LB/DB all sat on the old K neutral —
   re-implementing in code the exact defect `#311` was raised to end. Both of its call sites fell
   back to `FACET.K`, the KICKER's colour, which is the same hole `#325` closed in the
   prototype's `pc()`. `mockups/common.py`'s own first line claims this family takes "the design
   tokens (from design_system, never a second copy)"; that dict was the second copy.
2. `build.py`'s emit loop ran over `r_variants + s_variants` only, while `index_html()` put
   `cards(c_variants.VARIANTS)` and `cards(b_variants.VARIANTS)` straight into the index. **The
   index advertised nine pages the build could not regenerate**, with no recorded reason and no
   other module writing them.

This is the `#323`/`#324` lesson applied to the second surface: `#320` built an emitter for the
prototype and had no check on its OUTPUT, and a stale build slipped through within the hour. The
emitter here gets its output side at the same time as the emitter.
"""
from __future__ import annotations

import pathlib
import sys
import unittest

_MOCKUPS = pathlib.Path(__file__).parent / "mockups"
sys.path.insert(0, str(_MOCKUPS))

#: Committed pages no builder emits, so their inlined palette cannot be regenerated. Neither is
#: linked from `index.html` or from any other page; both are referenced only by `DRAFT_ROOM_UI.md`.
#: Hand-editing them to today's palette would be editing a record to make a test green, which is
#: the move `#323` declined for `_v1_ledger_rail_prev.html`. A COUNT-PINNED set, not an open
#: predicate: an exemption list that can grow quietly is not an exemption, it is a hole.
_HAND_WRITTEN = {"draft_rail.html", "draft_room_compass.html"}


class TheMockupsWearDesignSystemsPaletteTests(unittest.TestCase):

    def _pages(self):
        return [p for p in sorted(_MOCKUPS.glob("*.html")) if p.name not in _HAND_WRITTEN]

    def test_the_exemption_list_has_not_grown(self):
        self.assertEqual(len(_HAND_WRITTEN), 2,
                         f"the hand-written set is now {sorted(_HAND_WRITTEN)}; this rule exempts "
                         f"whatever is in it, so a change needs a reason on record")
        for name in _HAND_WRITTEN:
            self.assertTrue((_MOCKUPS / name).exists(),
                            f"{name} is exempted but does not exist; the exemption is stale")

    def test_every_built_page_carries_the_derived_pill_css_verbatim(self):
        import common
        expected = common.pill_css()
        self.assertEqual(len(expected.splitlines()), 10,
                         "pill_css should emit one rule per position; a second loop over "
                         "DL/LB/DB was removed at `#328` after `#311` made it dead")
        pages = self._pages()
        self.assertGreaterEqual(len(pages), 20,
                                f"only {len(pages)} built pages; this rule ranges over nothing")
        checked = 0
        for page in pages:
            text = page.read_text(encoding="utf-8")
            if ".pill-QB" not in text:
                continue          # a page that draws no pills is not this rule's business
            checked += 1
            with self.subTest(page=page.name):
                self.assertIn(expected, text,
                              f"{page.name}'s pill CSS is not design_system's. Either a hex was "
                              f"typed into a source file, or this page was not rebuilt -- "
                              f"`python3 build.py` in mockups/ is what applies it")
        self.assertGreaterEqual(checked, 20,
                                f"only {checked} pages carried pill rules at all")

    def test_a_page_that_declares_FACET_declares_the_derived_one(self):
        import common
        expected = common.facet_js()
        self.assertIn("IDP", expected, "the emitted FACET must carry all ten positions")
        self.assertIn("ABSENT", expected,
                      "FACET must name an absence colour, or a caller falls back to a real "
                      "position's hue -- both call sites used FACET.K before `#328`")
        declaring = [p for p in self._pages() if "const FACET" in p.read_text(encoding="utf-8")]
        self.assertGreaterEqual(len(declaring), 1,
                                "no built page declares FACET; this rule is measuring nothing")
        for page in declaring:
            with self.subTest(page=page.name):
                self.assertIn(expected, page.read_text(encoding="utf-8"),
                              f"{page.name} declares a FACET that is not common.facet_js()")

    def test_no_built_page_still_falls_back_to_the_kickers_colour(self):
        """`#325`'s hole, in its second home. `FACET[c.pos] || FACET.K` painted any position the
        fixture did not name in K's real colour."""
        for page in self._pages():
            text = page.read_text(encoding="utf-8")
            if "const FACET" not in text:
                continue
            with self.subTest(page=page.name):
                self.assertNotIn("FACET.K}", text,
                                 f"{page.name} falls back to FACET.K -- the KICKER's colour -- "
                                 f"where it should use FACET.ABSENT")


if __name__ == "__main__":
    unittest.main()
