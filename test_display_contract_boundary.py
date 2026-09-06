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

REPAIRED (D10 option A, the one option independent of #58): nothing is normalised and no
number changes, but every surface now says what its number IS. The vocabulary lives in
design_system.DISPLAY_CONTRACT / VALUE_UNIT / VALUE_UNIT_SHORT, and the two Draft Room panels
render their cards through ONE function (app._render_pick_metrics) rather than two copies of
identical copy. The tests below were inverted from the pinning form they had before the
repair, not deleted; the mechanical half (TheScaleIsNotAPointsTotalTests) is unchanged.

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


def _scanned_sources():
    """Every production module that could format an engine quantity -- NOT just the ones that
    import streamlit.

    THE ORIGINAL SCOPE WAS `ui_source.text()`, which resolves to ['app.py'] alone, and that is
    how the seventh crash site survived the fix that closed the other six. `screen_context.py`
    formats team_acquisition_value with no guard and reaches the Draft Room through
    render_debate_chip -- but it draws no widgets, so it imports no streamlit, so a scope keyed
    on "is this a UI file" could not see it. The scope was chosen by an INCIDENTAL property.

    Formatting an absent value raises wherever it happens, so the scan covers every production
    module and lets the AST decide. A curated list would only move the blind spot to whichever
    file is forgotten next."""
    for path in sorted(_HERE.glob("*.py")):
        if path.name.startswith("test_") or path.name == "conftest.py":
            continue
        yield path.name, path.read_text()


class TheTwoUnitsAreToldApartTests(unittest.TestCase):
    """INVERTED on repair. The cards used to sit UV / projected points / TAV in one row, all
    `.0f`, with only the middle one naming a unit. They still share a format spec -- that was
    never the defect -- but every label now carries its unit and every card a help sentence,
    all from design_system.DISPLAY_CONTRACT, and both panels render through one function."""

    def _renderer(self):
        return ui_source.block("def _render_pick_metrics(rec)", until="\n\n\ndef ")

    def test_both_draft_panels_render_through_one_function(self):
        """One definition, two call sites (live Draft Room and its Mock Draft twin). The old
        pin counted two copies of the label; a shared renderer is what makes "repaired
        together" a property of the code rather than of a test's vigilance."""
        self.assertEqual(_APP.count("def _render_pick_metrics("), 1)
        self.assertIn("_render_pick_metrics(rec)", _APP)
        self.assertIn("_render_pick_metrics(mock_rec)", _APP)
        for bare in ('"Universal Value"', '"Your Acquisition Value"', '"Denial Value"',
                     '"Opportunity Cost of Waiting"', '"Expected Value If You Wait"'):
            with self.subTest(label=bare):
                self.assertNotIn(bare, _APP, "a bare, unit-less label came back")

    def test_every_card_takes_its_label_and_help_from_the_contract(self):
        import design_system as ds
        block = self._renderer()
        for quantity in ds.DISPLAY_CONTRACT:
            with self.subTest(quantity=quantity):
                self.assertIn(f'label("{quantity}")', block)
                self.assertIn(f'help=note("{quantity}")', block)

    def test_every_value_label_names_the_value_unit_and_the_points_label_names_season(self):
        import design_system as ds
        for quantity, entry in ds.DISPLAY_CONTRACT.items():
            with self.subTest(quantity=quantity):
                if entry["unit"] == ds.VALUE_UNIT:
                    self.assertIn(f"({ds.VALUE_UNIT_SHORT})", entry["label"])
                    self.assertIn(ds.VALUE_UNIT, entry["help"].lower(),
                                  "the help sentence must spell the short label out")
                else:
                    self.assertNotIn(ds.VALUE_UNIT_SHORT, entry["label"])
        self.assertIn("(season)", ds.DISPLAY_CONTRACT["projected_points"]["label"])
        self.assertIn("NOT fantasy points", ds.DISPLAY_CONTRACT["universal_value"]["help"])

    def test_the_format_specs_are_still_identical_which_is_now_fine(self):
        """The two numbers are STILL rendered `.0f` side by side. The repair is the label,
        not the number -- D10 option B (rescaling) waits on #58 and must not be smuggled in."""
        block = self._renderer()
        self.assertIn("rec.universal_value:.0f", block)
        self.assertIn("rec.projected_points:.0f", block)
        self.assertIn("rec.team_acquisition_value:.0f", block)

    def test_a_measured_zero_denial_value_is_a_number_not_a_dash(self):
        """Found while repairing: `rec.denial_value if rec.denial_value else "—"` rendered a
        real 0.0 -- no rival positioned to gain -- as the same dash an unmeasured value gets.
        The absence contract in the other direction."""
        block = self._renderer()
        self.assertIn("if rec.denial_value is not None else", block)
        self.assertNotIn("if rec.denial_value else", block)

    def test_a_measured_no_run_is_a_word_not_a_dash(self):
        block = self._renderer()
        self.assertIn('"DETECTED" if rec.position_run_detected else "NONE"', block)

    def test_the_best_alternative_line_carries_its_unit(self):
        import design_system as ds
        block = ui_source.block("def _best_alternative_line(alt)", until="\n\n\n")
        self.assertIn("design_system.VALUE_UNIT_SHORT", block)
        self.assertEqual(_APP.count("_best_alternative_line("), 3, "def + two call sites")

    def test_the_diff_drawer_deltas_carry_their_unit(self):
        import design_system as ds
        import pick_synthesis as ps
        self.assertIn("design_system.DIFF_UNITS.get(k, '')", _APP)
        missing = [f for f in ps._DIFF_FIELDS if f not in ds.DIFF_UNITS]
        self.assertEqual(missing, [], "diff fields with no unit in the drawer")


class AbsenceReachesTheMetricCardsTests(unittest.TestCase):
    """Two of the six cards in `metric_row1` used to format an Optional field with `:.0f` and
    no guard, which raises TypeError on None and takes the whole Draft Room render with it.

    The pattern was not random. In the SAME row, `projected_points` and `survival_probability`
    were guarded, while `universal_value` and `team_acquisition_value` -- the two the absence
    contract explicitly says WILL be None when a position has no replacement level -- were not.
    The guard had been applied to the fields that rarely need it and skipped on the fields the
    contract names.

    REACHABILITY is the part worth recording: `_board_order` sorts None-scored rows last, so a
    None leader looks impossible. But #154's feasibility backstop sorts `_feasible` AHEAD of
    `final_score`, so an unpriced candidate that fills a REQUIRED slot is promoted over priced
    candidates that do not -- measured directly as
    `unpriced QB, feasibility BINDING -> ['qb1','qb2','rb1','wr1']`. Tier 3 is what made this
    reachable; the backstop and the card were each correct alone.

    This is a CLASS test on purpose. Pinning the four repaired sites would not stop the next
    Optional field from being rendered bare."""

    #: Fields the dataclass itself declares can be absent. Derived, so a new Optional field is
    #: covered the day it is added rather than the day someone remembers to extend a list.
    def _optional_snapshot_fields(self):
        import typing
        import pick_synthesis
        hints = typing.get_type_hints(pick_synthesis.CandidateSnapshot)
        out = set()
        for name, hint in hints.items():
            if type(None) in typing.get_args(hint):
                out.add(name)
        return out

    def test_the_dataclass_really_does_declare_these_optional(self):
        # Non-vacuity: if this returned an empty set the scan below would pass trivially.
        optional = self._optional_snapshot_fields()
        self.assertIn("universal_value", optional)
        self.assertIn("team_acquisition_value", optional)
        self.assertGreater(len(optional), 5)

    def test_no_optional_field_is_formatted_without_a_none_guard(self):
        """AST, not regex: find every f-string that applies a format spec to `<x>.<field>` for
        an Optional field, and require the enclosing expression to test that same field against
        None. A conditional whose test names a DIFFERENT field does not count."""
        import ast
        optional = self._optional_snapshot_fields()
        unguarded = []
        for module_name, module_src in _scanned_sources():
            unguarded.extend(self._unguarded_in(ast.parse(module_src), optional, module_name))
        self.assertEqual(unguarded, [], "Optional field formatted with no `is not None` guard")

    #: Sites that are SAFE for a reason no static scan can see, each with that reason. Kept
    #: deliberately tiny: an allowlist is a place defects hide, so an entry earns its place only
    #: by naming an invariant a reader can check.
    _TRANSITIVELY_GUARDED = {
        # draft_board_ui._waiting_note returns early when `waiting_cost is None`, and
        # waiting_cost IS projected_points minus horizon_floor (draft_room.py:1379/:1406) --
        # so projected_points cannot be None past that guard. The protection is real but
        # TRANSITIVE: the field is guarded by testing something derived FROM it, which no
        # reasonable AST check can follow. If waiting_cost ever stops deriving from
        # projected_points, this entry becomes a live crash and must be deleted.
        ("draft_board_ui.py", "projected_points"),
    }

    def _unguarded_in(self, tree, optional, module_name):
        import ast

        unguarded = []
        # An enclosing `if <field> is None: return` guards every later line in that function.
        # The original scan saw only ternary guards, so it called four safe board sites unsafe
        # the moment its file scope widened -- a scan that cries wolf gets switched off, which
        # would cost more than the blind spot it replaced.
        early_returned = set()
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            names = set()
            for stmt in fn.body:
                if not isinstance(stmt, ast.If):
                    continue
                if not any(isinstance(n, ast.Return) for n in stmt.body):
                    continue
                names.update(n.attr for n in ast.walk(stmt.test) if isinstance(n, ast.Attribute))
            for node in ast.walk(fn):
                if isinstance(node, ast.JoinedStr):
                    early_returned.add((id(node), frozenset(names)))
        early_map = {}
        for node_id, names in early_returned:
            early_map.setdefault(node_id, set()).update(names)
        guarded_by = {}   # id(JoinedStr) -> set of attribute names tested against None
        for node in ast.walk(tree):
            if isinstance(node, ast.IfExp):
                tested = {n.attr for n in ast.walk(node.test) if isinstance(n, ast.Attribute)}
                for branch in (node.body, node.orelse):
                    for sub in ast.walk(branch):
                        if isinstance(sub, ast.JoinedStr):
                            guarded_by.setdefault(id(sub), set()).update(tested)

        unguarded = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.JoinedStr):
                continue
            for part in node.values:
                if not (isinstance(part, ast.FormattedValue) and part.format_spec is not None):
                    continue
                if not isinstance(part.value, ast.Attribute):
                    continue
                field = part.value.attr
                if field not in optional:
                    continue
                if field in guarded_by.get(id(node), set()):
                    continue
                if field in early_map.get(id(node), set()):
                    continue
                if (module_name, field) in self._TRANSITIVELY_GUARDED:
                    continue
                unguarded.append(f"{module_name}:{part.lineno} {field}")
        return unguarded


class TheBoardsProseQualifiesItsUnitEverywhereTests(unittest.TestCase):
    """§20.8's count, re-derived here so it cannot drift out of date -- INVERTED on repair.
    The two "-point" shortenings are gone, the focus metrics carry a unit suffix, and a legend
    line states both scales once above the board."""

    def test_one_phrase_names_the_full_unit(self):
        self.assertIn("universal-value points", _BOARD)

    def test_the_two_shortened_phrases_now_name_their_full_unit(self):
        self.assertNotIn("-point gap to the next best", _BOARD)
        self.assertIn("universal-value points of drop-off to the next best", _BOARD)
        self.assertNotIn("-point rival premium", _BOARD)
        self.assertIn("acquisition-value points, not routine need", _BOARD)

    def test_the_unit_vocabulary_is_the_contracts_not_the_boards_own(self):
        """The JS interpolates PAYLOAD.valueUnitShort rather than spelling "UV pts" itself, and
        serialize_snapshot takes it from design_system -- one source, no drift."""
        self.assertIn('"valueUnitShort": design_system.VALUE_UNIT_SHORT', _BOARD)
        self.assertGreaterEqual(_BOARD.count("${PAYLOAD.valueUnitShort}"), 6)

    def test_the_focus_metrics_carry_a_unit_suffix(self):
        for needle in ('UV <b>', 'ACQ <b>', 'PROJ <b>'):
            with self.subTest(needle=needle):
                self.assertIn(needle, _BOARD)
        self.assertIn('<span class="unit">season pts</span>', _BOARD)
        self.assertIn('<span class="unit">${PAYLOAD.valueUnitShort}</span>', _BOARD)

    def test_the_legend_states_both_scales(self):
        self.assertIn('id="legend"', _BOARD)
        self.assertIn("not fantasy points", _BOARD)
        self.assertIn("season points per week", _BOARD)

    def test_no_phrase_says_only_points(self):
        """These three phrases used to say bare "points" about a UV/TAV-family quantity. In a
        fantasy app, unqualified "points" is the domain's own word for a season scoring total
        -- which this same panel renders a few lines away -- so the bare wording did not merely
        omit a unit, it asserted the wrong one. The third phrase is why #116's original count
        was low: the decisive-branch forfeit chip -- the sentence shown for the LEADER -- was
        not in it."""
        qualified = (
            ("point(s) off the board leader", "acquisition-value"),
            ("points</b> of context lift", "acquisition-value"),
            ("pts if you wait", None),
        )
        for phrase, unit in qualified:
            with self.subTest(phrase=phrase):
                if unit is None:
                    self.assertNotIn(phrase, _BOARD, "the bare 'pts' form came back")
                    continue
                lines = [ln for ln in _BOARD.splitlines() if phrase in ln]
                self.assertEqual(len(lines), 1, "phrase moved or was duplicated")
                self.assertIn(unit, lines[0], "this phrase lost its unit again")

    def test_the_forfeit_chip_names_the_unit_it_is_measured_in(self):
        self.assertIn("universal-value points if you wait", _BOARD)

    def test_the_same_panel_also_renders_real_season_points_and_says_so(self):
        """`_waiting_note` renders projected_points and horizon_floor -- genuinely season
        fantasy points -- in the same surface as the universal-value phrases above. Both units
        are present in one panel, which is what made the bare 'points' ambiguous; each now
        says which it is."""
        self.assertIn("c.projected_points:.0f", _BOARD)
        self.assertIn("c.horizon_floor:.0f", _BOARD)
        self.assertIn("season points against", _BOARD)
        self.assertIn("season points per week", _BOARD)
        self.assertIn('"label": f"{per_week:.2f} pts/wk"', _BOARD)


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
        # 41 -> 42 (2026-09-06): fills_required_slot, #154's feasibility backstop. The two
        # questions, and this one inverts the usual answer:
        #
        #   SCALE. A bool. It implies no unit at all, because it is not a value -- it is an
        #   ORDERING fact. pick_synthesis._board_order leads with it, ahead of final_score, so
        #   it can place a candidate above better-scoring candidates.
        #
        #   SHOULD THE CARD RENDER IT? Not the metric row -- that row is for quantities, and a
        #   bool in it would be the unit-borrowing problem in a new costume. But unlike every
        #   previous addition, the answer is not "no, leave it to the drawer": this field MUST
        #   reach a surface, because it silently REORDERS the board and no surface said so. A
        #   reordering the user cannot see is a reordering the user cannot audit. It renders as
        #   a marker on the row itself, next to the rank it changed, which is also where the
        #   same invisibility let an unpriced leader reach an unguarded format string.
        self.assertEqual(
            len(dataclasses.fields(ps.CandidateSnapshot)), 42,
            "CandidateSnapshot's field count changed. That is fine and often correct -- but "
            "confirm the new field does not imply a scale the card cannot support, decide "
            "whether the card should render it, then update this number.")

    def test_no_clamp_or_rescale_stands_between_the_engine_and_the_card(self):
        """Non-vacuity for the whole file: if the number were normalised into a 0-100 band on
        the way out, none of the above would matter. It is not -- the card renders the engine's
        own value with a format specifier and nothing else."""
        block = ui_source.block("def _render_pick_metrics(rec)", until="\n\n\ndef ")
        self.assertIn("rec.universal_value:.0f", block, "non-vacuity: the card is in this block")
        self.assertNotRegex(block, r"(min|max|clamp)\(|/ *100")
        self.assertNotIn("normalize_display", _APP)


if __name__ == "__main__":
    unittest.main()
