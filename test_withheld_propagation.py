"""THE PROPAGATION RULE, enforced at every presentation boundary (#52 phase 7.1).

A quantity withheld from presentation must not reach a person, on any surface, under any name,
as itself or as a delta of itself. `pick_synthesis.withheld_fields()` names what is withheld;
this file asks every boundary whether it honours that.

WHY THE CHECK IS VALUE-BASED AND NOT LABEL-BASED. The obvious test -- "the word survival does not
appear" -- is wrong in both directions, and the first version of this probe proved it by reporting
a leak that was not one: `format_snapshot_for_llm` prints "The survival probability is WITHHELD,
not missing: ... do not estimate one yourself", which is the REFUSAL and must stay. Meanwhile a
surface could leak the number under any other label and a word search would miss it. So each
withheld field is given a distinctive sentinel value and the boundaries are searched for every
plausible RENDERING of that value -- the raw float, the rounded percentage, the rounded integer.

EVERY ASSERTION HAS A NON-VACUITY ARM. A boundary that renders nothing at all passes a
"the number is absent" check trivially, which is exactly how a guard rots into decoration. So
each test runs twice: once withheld (the number must be gone) and once with the family
presentable (the number must be THERE), and the second is what proves the first can see.
"""
from __future__ import annotations

import json
import unittest
from unittest import mock

import draft_board_ui as ui
import pick_debate as pd
import pick_synthesis as ps
import screen_context as sc
from test_pick_debate import _candidate, _snapshot

#: Deliberately ugly, so a match is this value and not a coincidence of the fixture.
SURVIVAL = 0.8137


def _renderings(value: float) -> list[str]:
    """Every way a surface in this app has been seen to render a probability."""
    return [
        f"{value}",                         # the raw float, e.g. in a JSON payload
        f"{round(value * 100)}",            # the percentage the board and the seed both use
        f"{round(value * 100)}%",
        f"{value:.2f}",
        f"{round(value, 2)}",
    ]


def _leaks(haystack: str, value: float) -> list[str]:
    return [r for r in _renderings(value) if r in haystack]


class _Boundary(unittest.TestCase):
    """Each boundary rendered twice: withheld, then presentable."""

    def _render(self, presentable: bool) -> str:
        raise NotImplementedError

    def assert_honours_the_rule(self):
        self.assertFalse(ps.survival_is_presentable(),
                         "this suite assumes the shipped state is WITHHELD; if calibration "
                         "passed, these tests are stale and the whole family is presentable")
        withheld = self._render(presentable=False)
        self.assertEqual(
            _leaks(withheld, SURVIVAL), [],
            f"{type(self).__name__}: the withheld survival estimate reached this surface")
        # NON-VACUITY: the same boundary, with the family presentable, must SHOW the number --
        # otherwise the assertion above is about a surface that renders nothing.
        shown = self._render(presentable=True)
        self.assertTrue(
            _leaks(shown, SURVIVAL),
            f"{type(self).__name__}: the number is absent even when presentable, so the check "
            f"above proves nothing about withholding")


def _two_snapshots():
    """Two snapshots differing ONLY in the withheld family, which is the case that must produce
    no reportable delta -- and a presentable companion field so the diff is not empty by
    construction."""
    before = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
    after = _snapshot([_candidate("1", "Brock Purdy", survival_probability=0.2)])
    return before, after


class TheDiffDoesNotReportAWithheldDeltaTests(unittest.TestCase):
    """W4-16. A DELTA of a withheld quantity IS that quantity: "survival_probability: -0.08"
    printed beneath a block saying the estimate is withheld gives a reader its direction and its
    size. Measured before the repair on a real 1.01 -> 1.02 diff: survival_probability -0.08 and
    opportunity_cost +17.22, into the chairs' WHAT CHANGED and the Draft Room's diff drawer,
    which labels them "Survival probability" and "Opportunity cost"."""

    def test_a_survival_only_change_produces_no_reportable_delta(self):
        before, after = _two_snapshots()
        diffs = ps.diff_snapshots(before, after)
        leaked = sorted({k for d in diffs for k in d.get("deltas", {})
                         if k in ps.SURVIVAL_DERIVED_FIELDS})
        self.assertEqual(leaked, [], "a withheld field was reported as a delta")

    def test_the_same_change_IS_reported_when_the_family_is_presentable(self):
        """Non-vacuity, and the forward compatibility check in one: the day calibration passes,
        these deltas come back with no edit to _DIFF_FIELDS."""
        before, after = _two_snapshots()
        with mock.patch.object(ps, "SURVIVAL_IS_CALIBRATED", True):
            diffs = ps.diff_snapshots(before, after)
        leaked = sorted({k for d in diffs for k in d.get("deltas", {})
                         if k in ps.SURVIVAL_DERIVED_FIELDS})
        self.assertIn("survival_probability", leaked,
                      "the diff cannot report survival even when it is presentable, so the "
                      "test above is passing for the wrong reason")

    def test_a_presentable_field_still_diffs_while_the_family_is_withheld(self):
        """The filter is scoped to the family, not applied to the frame."""
        before = _snapshot([_candidate("1", "Brock Purdy", team_acquisition_value=100.0)])
        after = _snapshot([_candidate("1", "Brock Purdy", team_acquisition_value=88.0)])
        diffs = ps.diff_snapshots(before, after)
        self.assertEqual(diffs[0]["deltas"].get("team_acquisition_value"), -12.0)


class TheChairPromptDoesNotCarryItTests(_Boundary):
    """W4-16 at the surface that reads the diff."""

    def _render(self, presentable):
        # ALWAYS the snapshot carrying the sentinel. The first version rendered `after` in the
        # presentable arm -- a snapshot whose survival is 0.2, not the sentinel -- so the
        # non-vacuity check looked for a number that was never in the input and reported the
        # guard as blind. It was the probe that was blind.
        before, after = _two_snapshots()
        with mock.patch.object(ps, "SURVIVAL_IS_CALIBRATED", presentable):
            return pd.format_snapshot_for_llm(before, ps.diff_snapshots(before, after))

    def test_the_withheld_estimate_never_reaches_a_chair(self):
        self.assert_honours_the_rule()

    def test_the_refusal_ITSELF_still_reaches_the_chair(self):
        """The half a word search would break. The prompt must keep SAYING the number is
        withheld -- that sentence is the guard, and deleting it to make a naive "no mention of
        survival" check pass would remove the only thing telling the model not to invent one."""
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
        text = pd.format_snapshot_for_llm(snap)
        self.assertIn("WITHHELD, not missing", text)
        self.assertIn("do not estimate one yourself", text)
        self.assertIn("Picks before your next selection", text)


class TheSystemPromptsDoNotInviteItTests(unittest.TestCase):
    """W4-04. The leak into the INSTRUCTIONS rather than the evidence: all three prompts listed
    the family among "real, already-computed numbers", and the Caller's output template offered
    "19% survival with a QB run detected" as a worked KEY FACTOR and "survival_probability for
    Player X" as a worked DISAGREE -- while the evidence block beneath told the same model the
    estimate is WITHHELD. A prompt that names a number, demonstrates citing it, and then refuses
    to supply it is an invitation to fabricate, aimed at the one participant that cannot check."""

    PROMPTS = ("STRATEGIST_SYSTEM_PROMPT", "SKEPTIC_SYSTEM_PROMPT", "CALLER_SYSTEM_PROMPT")

    def test_no_prompt_presents_a_withheld_field_as_a_number_it_is_given(self):
        for name in self.PROMPTS:
            text = getattr(pd, name)
            with self.subTest(prompt=name):
                for field in ps.withheld_fields():
                    self.assertNotIn(
                        field, text,
                        f"{name} names {field} as a number the chair is given, and it is not")
                self.assertNotIn("19% survival", text, "the worked example cites the withheld number")

    #: Only these two ENUMERATE the numbers the chair is given. The Skeptic is handed the
    #: Strategist's case and told to pressure-test it; it never listed the family, so requiring
    #: the substitute in it would be asserting a sentence nobody wrote.
    PROMPTS_THAT_LIST_THE_NUMBERS = ("STRATEGIST_SYSTEM_PROMPT", "CALLER_SYSTEM_PROMPT")

    def test_the_prompts_name_the_measured_substitute_instead(self):
        """Non-vacuity: they must still say what the chair DOES get, or the repair has removed
        the instruction rather than corrected it."""
        for name in self.PROMPTS_THAT_LIST_THE_NUMBERS:
            with self.subTest(prompt=name):
                self.assertIn("intervening_picks", getattr(pd, name))

    def test_the_skeptic_is_not_told_to_pressure_test_a_model_it_cannot_see(self):
        """The softer form of the same invitation. The Skeptic was told to test "whether the
        survival model's own assumptions actually hold here" -- and it is given no survival
        figure to test. The parenthetical that follows is about a DETECTED RUN, which it does
        get, so the substance was always sound and the framing named the wrong thing."""
        self.assertNotIn("survival model", pd.SKEPTIC_SYSTEM_PROMPT)
        self.assertIn("positional run", pd.SKEPTIC_SYSTEM_PROMPT)

    def test_no_placeholder_survived_substitution(self):
        for name in self.PROMPTS:
            with self.subTest(prompt=name):
                self.assertNotIn("{", getattr(pd, name).replace("{}", ""))


class ThePrytaneumSeedDoesNotCarryItTests(_Boundary):
    """I-05. The surface furthest from the gate, and it printed "survival 31%" unconditionally."""

    def _render(self, presentable):
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
        with mock.patch.object(ps, "SURVIVAL_IS_CALIBRATED", presentable):
            return sc.build_draft_room_context(snap).to_prompt_seed()

    def test_the_withheld_estimate_never_reaches_the_seed(self):
        self.assert_honours_the_rule()

    def test_the_measured_pick_count_takes_its_place(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
        seed = sc.build_draft_room_context(snap).to_prompt_seed()
        self.assertIn("picks until your turn", seed)


class TheBoardPayloadShipsThePolicyWithTheValueTests(unittest.TestCase):
    """The surface that was ALREADY right, pinned so it stays right -- and because it is the
    model the rest of this repair follows. It carries the number and the policy together and
    redacts at render, deliberately: "a payload that quietly transforms is a second place for
    the UI and the engine to disagree"."""

    def test_the_payload_carries_the_withheld_flag(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
        payload = ui.serialize_snapshot(snap, pick_header="ON THE CLOCK", state_tags=[])
        candidates = payload.get("candidates") or []
        self.assertTrue(candidates)
        self.assertTrue(candidates[0]["survivalWithheld"],
                        "the policy stopped travelling with the value")

    def test_the_flag_follows_the_policy_rather_than_being_hardcoded(self):
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=SURVIVAL)])
        with mock.patch.object(ps, "SURVIVAL_IS_CALIBRATED", True):
            payload = ui.serialize_snapshot(snap, pick_header="ON THE CLOCK", state_tags=[])
        self.assertFalse(payload["candidates"][0]["survivalWithheld"])

    def test_the_renderer_gates_on_the_flag_and_not_on_the_value(self):
        """The JS is the thing that actually withholds here, so the gate is asserted in it."""
        source = ui.render_board_html(
            ui.serialize_snapshot(_snapshot([_candidate("1", "Brock Purdy")]),
                                  pick_header="x", state_tags=[]))
        self.assertIn("survivalWithheld", source)
        self.assertIn("!c.survivalWithheld && num(c.survival)", source)


if __name__ == "__main__":
    unittest.main()
