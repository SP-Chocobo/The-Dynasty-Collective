"""#301: the empty-state front page -- the one the app actually shows today.

WHY THIS PAGE IS TESTED SEPARATELY FROM `front.html`. `app.py` has exactly one `st.stop()`, at
3667, guarded by `if not snapshot`. The five-option view picker and all five views sit BELOW it,
so with no league synced none of the synced page's claims -- lineup holes, bye damage, thin
positions -- has a subject to be about. Rendering them with absent stamps would be a dashboard of
em dashes, which is `#187` used as an excuse rather than honoured: the absence contract is for a
quantity that could not be measured, not for one that does not yet have a subject.

THE ONE THING THESE TESTS ARE REALLY FOR. The two pending rows must not read as damage. Before a
sync, "never fetched on this machine" is the EXPECTED state of a machine with no league; after one
it would be a defect. A page that renders them identically in both states is lying in one of them.
"""

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

import build_empty
import build_front


def _fx(**over):
    base = {
        "state": "no_league_synced",
        "grade": "Aging",
        "grade_basis": "measured -- recency_grade over the oldest LOADED source (76d)",
        "worst_days": 76,
        "have": [{"label": "Draft Sharks Dynasty Rankings", "as_of": "2026-08-25", "days": 71,
                  "basis": "measured -- read off the file on disk, as-of 2026-08-25"}],
        "on_sync": [{"label": "Sleeper player database",
                     "basis": "ABSENT -- never fetched on this machine"}],
        "action": "Sync a Sleeper username in the sidebar",
        "action_cost": "Until then the board cannot price to your league's rules.",
    }
    base.update(over)
    return base


class ThePendingRowsDoNotReadAsDamage(unittest.TestCase):
    def test_the_reason_is_VISIBLE_text_not_only_a_tooltip(self):
        """A hover-only reason is unreachable on a phone, and on this page the reason is the
        whole point of the row."""
        page = build_empty.build(_fx())
        self.assertIn("never fetched on this machine", page)
        self.assertNotIn('title="never fetched on this machine"', page)

    def test_a_pending_row_is_not_stamped_with_the_word_absent(self):
        """The section heading already says what these are. Stamping each one `absent` repeats
        the heading and makes an early state look like a broken one."""
        page = build_empty.build(_fx())
        pending = page[page.index("Arrives when you sync"):]
        self.assertNotIn('class="prov">absent', pending)

    def test_the_section_heading_says_what_they_are_waiting_for(self):
        self.assertIn("Arrives when you sync", build_empty.build(_fx()))


class TheVerdictGradesOnlyWhatIsOnDisk(unittest.TestCase):
    def test_the_grade_comes_from_the_fixture_not_from_the_page(self):
        self.assertIn("Aging", build_empty.build(_fx()))
        self.assertIn("Stale", build_empty.build(_fx(grade="Stale")))

    def test_with_nothing_dated_it_declines_to_grade_rather_than_inventing_one(self):
        page = build_empty.build(_fx(grade=None, worst_days=None, have=[],
                                     grade_basis="ABSENT -- no loaded source carries a date"))
        self.assertIn("nothing to grade", page)
        self.assertIn("no loaded source carries a date", page)

    def test_an_absent_worst_day_count_is_not_painted_as_a_number(self):
        page = build_empty.build(_fx(worst_days=None))
        self.assertNotIn("None", page)
        self.assertIn("age not recorded", page)

    def test_a_fractional_age_goes_through_ds_figure_rather_than_str(self):
        """Measured divergence: `ds.figure(76.5, 0)` is "77" and `str(76.5)` is "76.5". The
        mutation that swapped one for the other survived until this test existed, because the
        fixture's own 76 renders identically either way -- a test that only exercises the
        agreeing input proves nothing about which function ran."""
        page = build_empty.build(_fx(worst_days=76.5))
        self.assertIn("77 days old", page)
        self.assertNotIn("76.5", page)

    def test_a_NaN_age_declines_rather_than_painting_the_word_nan(self):
        """`ds.figure` returns None for NaN and inf BY DESIGN, so the caller picks the absence
        wording (#187). Stringifying instead puts the machine word `nan` on the page, which is
        the same family as the four call sites that once painted `None`."""
        for bad in (float("nan"), float("inf")):
            with self.subTest(worst_days=bad):
                page = build_empty.build(_fx(worst_days=bad))
                self.assertIn("age not recorded", page)
                self.assertNotIn("nan", page)
                self.assertNotIn("inf", page)


class NoMachineWordReachesTheReader(unittest.TestCase):
    def test_the_raw_state_key_is_not_shown(self):
        """`no_league_synced` is an identifier. It was on the page, and it is machine-speak."""
        self.assertNotIn("no_league_synced", build_empty.build(_fx()))

    def test_no_literal_None_or_NaN_anywhere(self):
        for over in ({}, {"worst_days": None}, {"grade": None}, {"have": []}, {"on_sync": []}):
            with self.subTest(over=over):
                page = build_empty.build(_fx(**over))
                self.assertNotIn(">None<", page)
                self.assertNotIn("NaN", page)


class HostileFixturesDoNotCrashOrInject(unittest.TestCase):
    def test_every_top_level_key_can_be_missing(self):
        for key in list(_fx()):
            with self.subTest(missing=key):
                fx = _fx()
                del fx[key]
                build_empty.build(fx)        # must not raise

    def test_an_empty_fixture_still_renders(self):
        build_empty.build({})

    def test_a_label_cannot_inject_markup(self):
        page = build_empty.build(_fx(have=[{"label": "<script>x</script>", "as_of": "x",
                                            "days": 1, "basis": "measured -- x"}]))
        self.assertNotIn("<script>x</script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_a_non_numeric_day_count_does_not_take_the_page_down(self):
        page = build_empty.build(_fx(have=[{"label": "weird", "as_of": "x", "days": "many",
                                            "basis": "measured -- x"}]))
        self.assertIn("weird", page)


class ItWearsTheSamePalette(unittest.TestCase):
    def test_the_stylesheet_is_the_one_front_page_uses_not_a_second_copy(self):
        """`_palette.py` measured 26 of 27 shared token names drifting when two surfaces
        hand-wrote their own `:root`. Two STATES of one page would drift the same way."""
        self.assertIn(build_front.style_css(), build_empty.build(_fx()))

    def test_the_palette_is_derived_from_the_app_not_spelled_here(self):
        import design_system as ds
        self.assertIn(ds.root_css_block(), build_empty.build(_fx()))


if __name__ == "__main__":
    unittest.main()
