"""The front page must render what the BASIS says, and never a number it does not have.

WHY THIS FILE EXISTS, and it is not a formality. The page it guards shipped a screenshot whose
every figure came from a hand-written demo fixture, under a footer reading "measured" -- because
the footer was hardcoded prose and the renderer consulted two of five basis stamps, both only
into tooltips. Three adversarial passes found that independently, along with a fixture generator
that could not run at all, a `None` concentration rendering as a measured "0%", and the literal
word "None" painted where a figure was absent.

Every test below fails on the behaviour as it was. That is the point: the repo's own precedent is
`test_board_renders_absence.py`, which exists because "a correct behaviour with no test is one
edit from becoming the recorded defect", and it carries the two lessons that apply here verbatim
-- static HTML proves nothing, and the degenerate case has to be CONSTRUCTED rather than waited
for. Each of these is a constructed degenerate case.

Run from the repo root:  python3 -m unittest ui_explore.round3.test_front_renders_its_basis
"""
from __future__ import annotations

import copy
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import build_front

BASE = {
    "_provenance": {"format": "12T_ppr", "strategy": "sharp_auto", "seat": 1, "universe_rows": 5357,
                    "basis": {"thin_positions": "measured -- positional_depth",
                              "structural_holes": "measured -- slot_coverage",
                              "bye_profile": "measured -- bye_concentration",
                              "starters": "CONSTRUCTED -- optimize_lineup's best legal lineup",
                              "record": "ABSENT -- no capture holds a result"}},
    "league": {"roster_positions": ["QB", "RB", "WR", "TE", "K", "DEF"], "starting_slots": 6},
    "thin_positions": [{"position": "TE", "label": "Weak", "count": 2, "valued_count": 2,
                        "value_label": " (41)"}],
    "structural_holes": [],
    "bye_profile": {"concentration": 0.401, "worst_week": 6, "worst_week_loss": 95.0,
                    "total_loss": 237.0, "weeks": {"6": 95.0, "9": 40.0}, "basis": "measured",
                    "unknown_byes": 0, "worst_week_detail": {"starters_out": 2}},
    "starters": ["1", "2", "3", "4", "5", "6"], "roster": [], "record": None,
}


def render(**overrides):
    fx = copy.deepcopy(BASE)
    for path, value in overrides.items():
        node, *rest = path.split("__")
        if rest:
            fx[node][rest[0]] = value
        else:
            fx[node] = value
    return build_front.build(fx)


class TheBasisDecidesTheRendering(unittest.TestCase):

    def test_a_constructed_field_is_marked_wherever_it_appears(self):
        self.assertIn("constructed", render())

    def test_stamping_a_measured_field_CONSTRUCTED_changes_the_page(self):
        """The exact attack an adversarial pass used: stamp the measured fields CONSTRUCTED and
        see whether anything moves. It did not, because the footer was prose."""
        basis = copy.deepcopy(BASE["_provenance"]["basis"])
        basis["bye_profile"] = "CONSTRUCTED -- invented for a demo"
        basis["thin_positions"] = "CONSTRUCTED -- invented for a demo"
        promoted = render(_provenance={**BASE["_provenance"], "basis": basis})
        self.assertNotEqual(promoted, render(),
                            "stamping two measured fields CONSTRUCTED changed nothing on the page")
        self.assertNotIn("bye profile, thin positions are <b>measured</b>", promoted)

    def test_the_footer_never_calls_a_constructed_field_measured(self):
        basis = {k: "CONSTRUCTED -- all of it invented" for k in BASE["_provenance"]["basis"]}
        html = render(_provenance={**BASE["_provenance"], "basis": basis})
        tail = html[html.index('class="prov"'):]
        self.assertNotIn("<b>measured</b>", tail,
                         "the footer claims measurement for a page with no measured field")

    def test_an_absent_field_is_a_dash_carrying_its_reason(self):
        html = render()
        self.assertIn("&mdash;", html)
        self.assertIn("no capture holds a result", html)


class NoNumberItDoesNotHave(unittest.TestCase):

    def test_a_null_concentration_is_not_rendered_as_zero_percent(self):
        """bye_concentration: "It is None, never 0.0 ... reporting 0.0 would rank it as maximally
        staggered, which is a claim about a distribution that does not exist"."""
        bp = {**BASE["bye_profile"], "concentration": None}
        html = render(bye_profile=bp)
        self.assertNotIn("0% of your season", html)
        self.assertIn("no shape", html)

    def test_no_absent_figure_is_painted_as_the_word_None(self):
        for field, value in (("total_loss", None), ("worst_week_loss", None)):
            bp = {**BASE["bye_profile"], field: value}
            self.assertNotIn(">None<", render(bye_profile=bp), f"{field} rendered as 'None'")
        self.assertNotIn("of None", render(league={"roster_positions": [], "starting_slots": None}))

    def test_a_partial_bye_basis_marks_every_week_as_a_floor(self):
        """bye_collision: under a partial basis EVERY week is a floor, not only the colliding ones
        -- "marking only the weeks that happen to have a collision would imply the clean-looking
        weeks were verified, and they were not"."""
        bp = {**BASE["bye_profile"], "basis": "partial", "unknown_byes": 2}
        html = render(bye_profile=bp)
        self.assertGreaterEqual(html.count("&ge;"), 2, "the week strip carries no floor marker")
        self.assertIn("no known bye", html)

    def test_a_partial_depth_sum_scopes_the_verdict_not_just_the_number(self):
        thin = [{"position": "WR", "label": "Weak", "count": 7, "valued_count": 1,
                 "value_label": " (>=12, 1 of 7 priced)"}]
        self.assertIn("floor", render(thin_positions=thin))


class HostileFixturesDoNotCrashOrInject(unittest.TestCase):

    def test_a_non_numeric_bye_week_key_does_not_take_the_page_down(self):
        bp = {**BASE["bye_profile"], "weeks": {"6": 95.0, "bye": 3.0}}
        self.assertIn("wk", render(bye_profile=bp))

    def test_a_missing_basis_key_does_not_raise(self):
        self.assertIn("class=\"prov\"", render(_provenance={**BASE["_provenance"], "basis": {}}))

    def test_mixed_types_in_a_sort_key_do_not_raise(self):
        thin = [{"position": "TE", "label": "Weak", "count": "2"},
                {"position": "QB", "label": "Weak", "count": 1}]
        self.assertIn("Thin at", render(thin_positions=thin))

    def test_a_position_code_from_a_capture_cannot_inject(self):
        for holes in (["K<script>alert(1)</script>"],
                      ["K<script>alert(1)</script>", "DEF"]):
            html = render(structural_holes=holes)
            self.assertNotIn("<script>alert(1)</script>", html,
                             "an unescaped position code reached the document")

    def test_every_top_level_key_can_be_missing(self):
        for key in ("starters", "league", "thin_positions", "structural_holes", "bye_profile"):
            fx = copy.deepcopy(BASE)
            fx.pop(key)
            try:
                build_front.build(fx)
            except Exception as exc:                      # noqa: BLE001 - that is the assertion
                self.fail(f"a fixture missing {key!r} crashed the builder: {exc!r}")



class TheLadderKnowsWhatWeekItIs(unittest.TestCase):
    """The bye rung justifies itself on futurity -- "a known FUTURE week ... planning only works
    in advance" -- and the first version of this page had no concept of now, so it would rank a
    week already played second-highest. Nothing erodes a triage surface faster."""

    WEEKS = {"5": 11.0, "6": 95.0, "9": 40.0, "13": 60.0}

    def _bye(self, **over):
        return {**BASE["bye_profile"], "weeks": dict(self.WEEKS), "worst_week": 6,
                "worst_week_loss": 95.0, **over}

    def test_with_a_known_week_it_ranks_the_worst_week_still_AHEAD(self):
        html = render(bye_profile=self._bye(), current_week=10)
        self.assertIn("Week <b>13</b>", html, "it did not re-rank onto the worst remaining week")
        self.assertNotIn("Week <b>6</b>", html, "it named a week already played")

    def test_a_past_week_is_dropped_from_the_strip_entirely(self):
        html = render(bye_profile=self._bye(), current_week=10)
        self.assertIn("wk 13", html)
        for dead in ("wk 5", "wk 6", "wk 9"):
            self.assertNotIn(dead, html, f"{dead} is behind us and still on the page")

    def test_with_every_bye_behind_us_the_claim_does_not_fire(self):
        html = render(bye_profile=self._bye(), current_week=14)
        self.assertNotIn("costs you", html, "it claimed a bye cost with no bye week left")

    def test_without_a_known_week_it_says_so_instead_of_implying_a_deadline(self):
        html = render(bye_profile=self._bye(), current_week=None)
        self.assertIn("does not know today's week", html)

    def test_the_page_says_whose_it_is(self):
        html = render(team="Team 1", league_name=None)
        self.assertIn("Team 1", html)
        self.assertIn('class="who"', html)

if __name__ == "__main__":
    unittest.main()
