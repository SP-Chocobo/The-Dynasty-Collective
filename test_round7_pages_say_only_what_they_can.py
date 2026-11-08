"""`#347` / `#350` — the round-7 landing page and in-league dashboard.

THE CENTRAL TEST HERE IS `test_no_python_repr_reaches_the_page`, and it exists because the same
defect shipped TWICE in one session from two unrelated causes:

  * `checks_summary` returns a dict BY DESIGN (`#338`: the surface never derives its own counts)
    and a draft interpolated it straight into a league row, printing
    `{'ran': 3, 'clean': ['holes', 'byes', 'depth'], ...}` on the page.
  * `fx["league"]` is the league CONFIG, not a name, and `str(fx.get("league") or "")` printed
    `{'roster_positions': [...], 'starting_slots': 10}` into the dashboard header.

Both were found by LOOKING at a render. Neither would have been caught by any test that asserted
on the composition, because the composition was correct in both cases -- the defect was entirely
in the handoff to the page. A page is a string, so the cheapest possible guard is to read that
string for the fingerprints of a Python value that escaped its formatter, and that guard
generalises to every future one of these.

These tests assert on PAGES THE BUILDERS PRODUCE AT TEST TIME, not on the committed .html files.
A test that reads the committed artifact passes forever once the artifact is committed, however
broken the builder becomes (`#332`'s stale-page defect in miniature).
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
R7 = ROOT / "ui_explore" / "round7"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pages():
    """Build all four pages in-process, so what is asserted on is what the code makes NOW."""
    landing = _load("r7_landing", R7 / "build_landing.py")
    dash = _load("r7_dashboard", R7 / "build_dashboard.py")
    fx = json.loads(landing.FIXTURE.read_text())
    import glob
    seats = glob.glob(landing.SEATS)
    out = {
        "landing": landing.build(fx, seats),
        "landing_unsynced": landing.build_unsynced(fx),
    }
    for label, fixture in (("dashboard", dash.LOUD), ("dashboard_quiet", dash.QUIET)):
        out[label] = dash.build(json.loads(fixture.read_text()))
    return out


class NoPythonValueEscapesItsFormatter(unittest.TestCase):

    #: A Python container's repr has punctuation HTML almost never produces legitimately:
    #: `{'` opens a dict with a quoted key, `['` a list of strings. Both are what a str()'d
    #: container looks like, and neither occurs in prose or in this project's markup.
    REPRS = (("{'", "a dict repr"), ("['", "a list-of-strings repr"),
             ("dict_keys(", "a dict_keys repr"), ("<built-in", "a builtin repr"),
             ("set()", "an empty-set repr"), ("None", "a bare None"))

    def test_no_python_repr_reaches_the_page(self):
        """The guard that would have caught both of this session's dict leaks."""
        for name, html in _pages().items():
            # Inline <script>/<style> may legitimately carry braces; the visible page may not.
            visible = re.sub(r"<(script|style)\b.*?</\1>", "", html, flags=re.S | re.I)
            for needle, what in self.REPRS:
                self.assertNotIn(
                    needle, visible,
                    f"{name}: {what} reached the page -- a Python value escaped its formatter. "
                    f"Context: {visible[max(0, visible.find(needle) - 90):visible.find(needle) + 90]!r}")

    def test_absences_are_labelled_and_never_bare(self):
        """`#187`: an absence renders as an em dash CARRYING ITS REASON, never blank, never 0.

        An em dash with no reason is indistinguishable from a broken template, which is the
        whole point of the contract.
        """
        for name, html in _pages().items():
            for m in re.finditer(r'<span class="absent"([^>]*)>', html):
                self.assertIn("title=", m.group(1),
                              f"{name}: an absent marker with no reason attached")


class TheChromeIsIntact(unittest.TestCase):

    def test_every_room_tab_is_named_even_when_its_label_is_hidden(self):
        """On phones the labels are hidden and the glyph IS the button (`#350`).

        A button whose text is `font-size:0` is unreachable by a screen reader unless it is
        named another way, so the name must be on the element, not only in the visible text.
        """
        for name, html in _pages().items():
            tabs = re.findall(r'<a class="room[^"]*"([^>]*)>', html)
            self.assertGreaterEqual(len(tabs), 6, f"{name}: expected the full room bar")
            for attrs in tabs:
                self.assertIn("aria-label=", attrs, f"{name}: an unnamed room tab")

    def test_exactly_one_tab_is_current(self):
        for name, html in _pages().items():
            self.assertEqual(len(re.findall(r'class="room on"', html)), 1,
                             f"{name}: a page must mark exactly one room as current")

    def test_the_dashboard_is_in_a_room_and_the_landing_page_is_not(self):
        pages = _pages()
        self.assertIn('aria-label="Matchup"', pages["dashboard"])
        self.assertIn('<a class="room on" title="Matchup"', pages["dashboard"])
        self.assertIn('<a class="room on" title="Home"', pages["landing"])


class TheDashboardComputesNothing(unittest.TestCase):
    """`#338`: every figure on the page is the engine's, arranged but never derived."""

    def test_the_lead_figure_is_the_engines_own(self):
        dash = _load("r7_dashboard_b", R7 / "build_dashboard.py")
        import front_claims as fc
        fx = json.loads(dash.LOUD.read_text())
        band = fc.compose(fx)
        lead = band["shown"][0]
        html = dash.build(fx)
        figure = dash.claim_parts(lead)["figure"]
        self.assertIn(f'<span class="big">{figure}</span>', html,
                      "the page's hero figure is not the one compose produced")

    def test_a_truncated_provenance_record_renders_as_an_absence(self):
        """The capture stores 200 characters of a str()'d dict; the page must not guess.

        Decoding is legitimate, guessing is not: `ast.literal_eval` refuses a truncated repr,
        and the page then says so rather than regexing a date out of damaged text (`#222`).
        """
        dash = _load("r7_dashboard_c", R7 / "build_dashboard.py")
        self.assertIsNone(dash.capture_date("{'captured_at': '2026-09-07T08:14"),
                          "a truncated record was parsed anyway")
        self.assertIsNone(dash.capture_date(None))
        self.assertIsNone(dash.capture_date("not a dict at all"))
        self.assertEqual(dash.capture_date("{'captured_at': '2026-09-07T08:14:10+00:00'}"),
                         "2026-09-07", "a WHOLE record must still decode")

    def test_the_capture_date_is_a_date_and_never_an_age(self):
        """A built file has no clock, so it must not imply one (`#345d`'s restraint, kept)."""
        dash = _load("r7_dashboard_d", R7 / "build_dashboard.py")
        got = dash.capture_date("{'captured_at': '2026-09-07T08:14:10.990206+00:00'}")
        self.assertEqual(got, "2026-09-07")
        self.assertNotIn("ago", str(got))


class TheBuildGatesCanActuallyFail(unittest.TestCase):
    """A gate that cannot fail on the file it guards is the session's recurring defect."""

    def test_type_floor_fires_on_a_sub_floor_size(self):
        landing = _load("r7_landing_b", R7 / "build_landing.py")
        with self.assertRaises(SystemExit):
            landing.assert_type_floor(".x{font-size:.6rem}")

    def test_type_floor_refuses_em(self):
        landing = _load("r7_landing_c", R7 / "build_landing.py")
        with self.assertRaises(SystemExit):
            landing.assert_type_floor(".x{font-size:0.9em}")

    def test_var_gate_fires_on_an_undefined_variable(self):
        """The silent one: an unresolvable var() inside a `font:` shorthand drops the rule."""
        landing = _load("r7_landing_d", R7 / "build_landing.py")
        with self.assertRaises(SystemExit):
            landing.assert_vars_resolve(".x{font:600 1rem/1 var(--nope)}")

    def test_the_real_stylesheets_pass_their_own_gates(self):
        landing = _load("r7_landing_e", R7 / "build_landing.py")
        dash = _load("r7_dashboard_e", R7 / "build_dashboard.py")
        import design_system as ds
        landing.assert_marks_are_visible()
        landing.assert_type_floor(landing.css())
        landing.assert_type_floor(landing.css() + dash.dash_css())
        landing.assert_vars_resolve(ds.root_css_block(), landing.font_vars(),
                                    ds.position_pill_css_block(), landing.css(), dash.dash_css())


class PagesRebuildIdentically(unittest.TestCase):
    """The committed .html must be what the builder makes, or the record is a fiction."""

    def test_every_committed_page_matches_its_builder(self):
        built = _pages()
        for name, html in built.items():
            path = R7 / f"{name}.html"
            self.assertTrue(path.exists(), f"{name}.html is not committed")
            self.assertEqual(path.read_text(), html,
                             f"{name}.html on disk differs from what the builder produces now "
                             f"-- regenerate it, or the page is stale (`#332`)")


if __name__ == "__main__":
    unittest.main()
