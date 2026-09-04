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
import ui_source

_HERE = Path(__file__).parent
_APP = ui_source.text()
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
        # 38 -> 39 (2026-09-03): depth_exposure, #139's third team-specific term inside
        # team_acquisition_value. The two questions this test exists to force, answered rather
        # than skipped past:
        #
        #   SCALE. It is on the same bpa-anchored scale as need_bonus and eligibility_bonus,
        #   bounded [0, DEPTH_EXPOSURE_MAX] and never negative. It implies no unit this file
        #   has not already measured, and cannot by itself make a TAV negative -- the mechanical
        #   fact the rest of this module rests on is untouched.
        #
        #   SHOULD THE CARD RENDER IT? No, and for the reason the card already does not render
        #   need_bonus or eligibility_bonus: the metric row shows the three headline quantities,
        #   and the decomposition of TAV belongs in the "What changed?" drawer, where this term
        #   now appears with a display label. Adding a fourth adjacent identically-formatted
        #   card would deepen exactly the unit-borrowing problem documented above, not fix it.
        # 39 -> 41 (2026-09-04): replacement_basis and growth_signal, #138's last two
        # write-only quantities, carried from the board row so the retained decision record can
        # read them. The same two questions, and for growth_signal the answer is NOT routine:
        #
        #   SCALE. replacement_basis is a string enum -- "live_starter_demand" |
        #   "predraft_anchor" -- and implies no unit at all.
        #
        #   growth_signal DOES imply one, and it is the wrong one for this card. It is a
        #   PERCENTILE DIFFERENCE (proj3yr_pct - season_pct, clamped at 0), so it lives on
        #   exactly the 0-100 band this whole file exists to say the engine's values do NOT
        #   live on. Measured range on real upside boards: 0 to 87.5. Rendering it beside
        #   universal_value -- raw projected points, unbounded and signed -- in matching
        #   formatting is precisely the unit-borrowing this module documents, and would be
        #   worse than the cases above because here the borrowed unit really is 0-100 and would
        #   look authoritative.
        #
        #   SHOULD THE CARD RENDER THEM? Neither, and for growth_signal the question is
        #   currently moot rather than merely declined: all three build_snapshot call sites in
        #   app.py omit `mode`, and build_snapshot forces "balanced", where growth_signal is
        #   always None. The card cannot render a quantity its own regime never computes. If
        #   #115 ever routes upside mode to a human board, the scale hazard above has to be
        #   settled BEFORE the field reaches a metric row, not after.
        #
        #   replacement_basis is a qualifier on a price rather than a number, so it belongs
        #   with horizon_basis in the explanation drawer rather than the metric row -- #36/#137
        #   territory, and deliberately not done here.
        self.assertEqual(
            len(dataclasses.fields(ps.CandidateSnapshot)), 41,
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
