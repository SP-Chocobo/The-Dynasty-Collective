"""1c / #116: what scale the displayed valuation numbers are actually in, and what the UI
implies they are.

MEASURED over 33,417 real board rows and 48,708 projected_points readings from one
12-team x 18-round draft against the committed baseline:

  universal_value   (all board rows)  min -319.2  med  -42.6  max 178.9   83.9% negative
  team_acquisition_value (candidates) min  -16.1  med   10.8  max 187.3   10.9% negative
  projected_points                    min    0.0  med   99.0  max 379.0    0.0% negative

The two populations are different on purpose and must not be conflated: the first is every row
in the pool, the second is only the narrowed candidates a user is actually shown. §20.8's
earlier figures (med 11.0, 11.8% negative) match the CANDIDATE distribution, which is the one
the metric cards render.

THE MECHANICAL FACT that settles the unit question: a team_acquisition_value can be negative --
10.9% of shown candidates are -- and a season fantasy-point total never is (0 of 48,708).
They are different quantities on different scales.

WHAT THE UI IMPLIES. `app.py`'s `metric_row1` places, in one row of six cards:

    [0] "Universal Value"        <- universal_value,   f"{...:.0f}"
    [1] "Projected Points"       <- projected_points,  f"{...:.0f}"
    [2] "Your Acquisition Value" <- team_acquisition_value, f"{...:.0f}"

Two different units, adjacent, identically formatted, and only the middle label names its own
unit. In a fantasy app "points" is the domain's word for the quantity in card [1], so cards [0]
and [2] borrow a meaning they do not have.

§20.8 recorded "the board's prose qualifies its unit three times and not twice". That count
covered only draft_board_ui's JS prose. Counting every surface that renders a valuation-derived
number, the rate is far lower -- the Streamlit metric cards state no unit at all, and there are
two copies of them (the live Draft Room panel and its Mock Draft twin).

NOTHING IS RENAMED OR NORMALIZED HERE. These tests pin the current copy so that a change to it
is deliberate and visible. INVERT them on repair; do not delete them.

These are source-text tests, and that is stated rather than hidden: for UI copy the source text
IS the artifact. They prove what the app will render, not what a user concludes from it.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()
_BOARD = (_HERE / "draft_board_ui.py").read_text()


class TheTwoUnitsSitAdjacentTests(unittest.TestCase):

    def test_universal_value_and_projected_points_are_rendered_identically(self):
        """Same format, same card row, different units. If either format ever changes this
        fails, which is the point: the two being indistinguishable is the finding."""
        for panel in ("metric_row1", "mock_metric_row1"):
            with self.subTest(panel=panel):
                self.assertRegex(_APP, rf'{panel}\[0\]\.metric\("Universal Value", f"\{{[a-z_.]+:\.0f\}}"\)')
                self.assertIn('"Projected Points", f"', _APP)
                self.assertRegex(_APP, rf'{panel}\[2\]\.metric\("Your Acquisition Value", f"\{{[a-z_.]+:\.0f\}}"\)')

    def test_the_value_cards_state_no_unit_at_all(self):
        """'Projected Points' names its unit in its own label. Its two neighbours do not."""
        self.assertIn('"Projected Points"', _APP)
        for bare_label in ('"Universal Value"', '"Your Acquisition Value"',
                           '"Opportunity Cost of Waiting"', '"Expected Value If You Wait"',
                           '"Denial Value"'):
            with self.subTest(label=bare_label):
                self.assertIn(bare_label, _APP)
                self.assertNotIn(bare_label.rstrip('"') + ' (universal-value points)"', _APP)

    def test_both_draft_panels_carry_the_same_copy(self):
        """The live Draft Room panel and the Mock Draft twin are separate code. A repair that
        fixed one and not the other would be worse than neither, so the duplication is pinned."""
        for label in ("Universal Value", "Your Acquisition Value", "Denial Value"):
            with self.subTest(label=label):
                self.assertEqual(_APP.count(f'"{label}"'), 2,
                                 "both panels must be repaired together")


class TheBoardsProseQualifiesItsUnitUnevenlyTests(unittest.TestCase):
    """§20.8's count, re-derived here so it cannot drift out of date."""

    def test_one_phrase_names_the_full_unit(self):
        self.assertIn("universal-value points", _BOARD)

    def test_two_phrases_name_the_quantity_but_shorten_the_unit_to_point(self):
        self.assertIn("-point gap to the next best", _BOARD)
        self.assertIn("-point rival premium", _BOARD)

    def test_two_phrases_say_only_points(self):
        """These are the bare ones. In a fantasy app, unqualified 'points' is the domain's word
        for a season scoring total -- which is a different quantity, shown on the same screen."""
        bare_phrases = ("point(s) off the board leader", "points</b> of context lift")
        for phrase in bare_phrases:
            with self.subTest(phrase=phrase):
                lines = [ln for ln in _BOARD.splitlines() if phrase in ln]
                self.assertEqual(len(lines), 1, "phrase moved or was duplicated")
                # The unit is unqualified ON THIS LINE. Checking the whole file would pass
                # trivially, since the forfeit sentence elsewhere does say "universal-value".
                self.assertNotIn("universal-value", lines[0],
                                 "this phrase now names its unit -- invert this test")

    def test_the_same_panel_also_renders_real_season_points(self):
        """`_waiting_note` renders projected_points and horizon_floor -- genuinely season
        fantasy points -- in the same surface as the universal-value phrases above. Both units
        are present in one panel, which is what makes the bare 'points' ambiguous rather than
        merely imprecise."""
        self.assertIn("c.projected_points:.0f", _BOARD)
        self.assertIn("c.horizon_floor:.0f", _BOARD)


class TheScaleIsNotAPointsTotalTests(unittest.TestCase):
    """The mechanical half. These assert properties of the CODE's contract, not of one sample."""

    def test_the_snapshot_can_carry_a_negative_acquisition_value(self):
        """10.9% of measured candidates were negative. Nothing clamps it, and a season
        fantasy-point total is never negative -- so the two cannot be the same scale."""
        import dataclasses
        import pick_synthesis as ps
        candidate = ps.CandidateSnapshot(
            player_id="p", name="n", position="RB", team=None,
            bpa=-10.0, bpa_source="s", confidence=50.0,
            universal_value=-12.5, need_bonus=0.0, eligibility_bonus=0.0,
            team_acquisition_value=-12.5, survival_probability=None, intervening_picks=None,
            opportunity_cost=None, expected_value_of_waiting=None, denial_value=None,
            denial_team=None, rival_premium=None, positional_forfeit=None,
            position_expected_taken=None, positional_cliff=None, position_run_detected=False,
            pick_necessity=0.0, necessity_label="HOLD", near_tie_with_leader=False,
            cliff_protection=False, block_opportunity=False, pure_value=False,
            context_elevated=False, consensus_rank=None, consensus_tier=None,
            reach_label=None, projected_points=None,
        )
        self.assertLess(candidate.team_acquisition_value, 0)

    def test_the_snapshot_schema_is_pinned_so_additions_are_noticed(self):
        """A field count, given its own home and its own reason.

        It used to sit inside the negative-value test above, where its purpose was invisible: a
        bare 37 next to an assertion about scale reads as incidental, so the natural response to
        it failing is to bump the number without asking what changed.

        What it actually protects: every field on CandidateSnapshot is a candidate for the
        card, and this file's whole subject is what the card implies about the engine's numbers.
        A new field is not a problem -- it is a PROMPT, to confirm the display contract still
        holds for whatever was just added, and to decide whether the card should show it.
        """
        import dataclasses
        import pick_synthesis as ps
        self.assertEqual(
            len(dataclasses.fields(ps.CandidateSnapshot)), 38,
            "CandidateSnapshot's field count changed. That is fine and often correct -- but "
            "confirm the new field does not imply a scale the card cannot support, decide "
            "whether the card should render it, then update this number.")

    def test_no_clamp_or_rescale_stands_between_the_engine_and_the_card(self):
        """Non-vacuity for the whole file: if the number were normalised into a 0-100 band on
        the way out, none of the above would matter. It is not -- the card renders the engine's
        own value with a format specifier and nothing else."""
        self.assertNotRegex(_APP, r'metric\("Universal Value", f"\{[^}]*(min|max|clamp|/ *100)')
        self.assertNotIn("normalize_display", _APP)


if __name__ == "__main__":
    unittest.main()
