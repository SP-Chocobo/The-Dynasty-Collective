"""MANDATE 2.5 / `#187`: the one comparison whose job is to catch an absence change was blind to it.

`diff_snapshots` is the audit trail — "why did this candidate move" answered with the real per-term
deltas rather than a re-derived guess. It skipped any term where either side was `None`:

    if prev_val is None or curr_val is None:
        continue

So a `positional_forfeit` that went from unmeasurable to 14.2, or a survival estimate that stopped
being computable, produced NOTHING — and those are the largest move a term can make. The audit trail
was silent about exactly the transitions `#187` exists to keep visible, and the mandate's own wording
for it is that "the one comparison that exists to catch this cannot see it".

A TRANSITION IS NOT A DELTA, and the repair turns on that. There is no magnitude, so there is no unit
to attach (`#116`), and subtracting from `None` to manufacture one would be the very fabrication this
mandate item is about. It gets its own field, its own two-word vocabulary, and its own phrasing — and
both consumers had to change with it, because each gated on `deltas` and would have dropped a
candidate whose only change was a term crossing the boundary.
"""
from __future__ import annotations

import unittest
import unittest.mock

import pick_debate as pd
import pick_synthesis as ps
import ui_source
from test_pick_debate import _candidate, _snapshot


def _pair(field, before, after, *, name="A Player"):
    """Two snapshots identical but for ONE term on ONE candidate, so nothing else can explain a
    diff. `_candidate` is the suite's shared fixture rather than a second hand-rolled one."""
    previous = _snapshot([_candidate("1", name)])
    current = _snapshot([_candidate("1", name)])
    object.__setattr__(previous.candidates[0], field, before)
    object.__setattr__(current.candidates[0], field, after)
    return previous, current


class TheTransitionIsReportedAtAll(unittest.TestCase):
    """The defect, directly: a term crossing the measurability boundary produced no diff entry."""

    def test_a_term_that_became_measurable_is_reported(self):
        previous, current = _pair("positional_forfeit", None, 14.2)
        diffs = ps.diff_snapshots(previous, current)
        self.assertEqual(len(diffs), 1, f"the transition produced no entry: {diffs}")
        self.assertEqual(diffs[0]["transitions"],
                         {"positional_forfeit": ps.TRANSITION_BECAME_MEASURED})

    def test_a_term_that_stopped_being_measurable_is_reported(self):
        previous, current = _pair("positional_forfeit", 14.2, None)
        diffs = ps.diff_snapshots(previous, current)
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["transitions"],
                         {"positional_forfeit": ps.TRANSITION_STOPPED_BEING_MEASURED})

    def test_absent_on_both_sides_is_not_a_change(self):
        """Still absent is not a transition. Reporting it would fill the trail with non-events and
        teach a reader to skim the section."""
        previous, current = _pair("positional_forfeit", None, None)
        self.assertEqual(ps.diff_snapshots(previous, current), [])

    def test_a_transition_is_NOT_placed_among_the_deltas(self):
        """The shape matters as much as the reporting. A consumer formats every `deltas` value with
        `:+` and appends a unit; a word in there would render as a broken number."""
        previous, current = _pair("positional_forfeit", None, 14.2)
        entry = ps.diff_snapshots(previous, current)[0]
        self.assertEqual(entry["deltas"], {})
        for value in entry["deltas"].values():
            self.assertIsInstance(value, (int, float))

    def test_a_numeric_move_is_still_a_delta_and_not_a_transition(self):
        """Non-vacuity in the other direction: the repair must not reclassify ordinary movement."""
        previous, current = _pair("positional_forfeit", 10.0, 14.2)
        entry = ps.diff_snapshots(previous, current)[0]
        self.assertEqual(entry["deltas"], {"positional_forfeit": 4.2})
        self.assertEqual(entry["transitions"], {})

    def test_deltas_and_transitions_can_both_appear_on_one_candidate(self):
        previous = _snapshot([_candidate("1", "A Player")])
        current = _snapshot([_candidate("1", "A Player")])
        object.__setattr__(previous.candidates[0], "positional_forfeit", None)
        object.__setattr__(current.candidates[0], "positional_forfeit", 14.2)
        object.__setattr__(current.candidates[0], "universal_value", 95.0)
        entry = ps.diff_snapshots(previous, current)[0]
        self.assertIn("universal_value", entry["deltas"])
        self.assertIn("positional_forfeit", entry["transitions"])

    def test_a_withheld_term_is_excluded_from_transitions_as_it_is_from_deltas(self):
        """Same rule, same population. A delta of a withheld quantity IS that quantity (`#52` phase
        7.1), and so is the news that it became measurable."""
        previous, current = _pair("survival_probability", None, 0.42)
        with unittest.mock.patch.object(ps, "withheld_fields",
                                        return_value=frozenset({"survival_probability"})):
            diffs = ps.diff_snapshots(previous, current)
        self.assertEqual(diffs, [], f"a withheld term's transition was reported: {diffs}")

    def test_and_reported_when_it_is_not_withheld(self):
        previous, current = _pair("survival_probability", None, 0.42)
        with unittest.mock.patch.object(ps, "withheld_fields", return_value=frozenset()):
            diffs = ps.diff_snapshots(previous, current)
        self.assertEqual(diffs[0]["transitions"],
                         {"survival_probability": ps.TRANSITION_BECAME_MEASURED})


class TheVocabularyHasOneHome(unittest.TestCase):
    """`#126`: a renderer that composes its own wording is a second definition of the event."""

    def test_there_are_exactly_two_states_and_both_have_reader_facing_wording(self):
        self.assertEqual(
            sorted(ps.TRANSITION_PHRASES),
            sorted([ps.TRANSITION_BECAME_MEASURED, ps.TRANSITION_STOPPED_BEING_MEASURED]))
        for phrase in ps.TRANSITION_PHRASES.values():
            self.assertTrue(phrase.strip())

    def test_each_phrase_says_what_the_OTHER_side_was(self):
        """"now measured" alone reads as a statement about the value. The change is the point, so
        both phrases name both sides of it."""
        self.assertIn("was not", ps.TRANSITION_PHRASES[ps.TRANSITION_BECAME_MEASURED])
        self.assertIn("was before", ps.TRANSITION_PHRASES[ps.TRANSITION_STOPPED_BEING_MEASURED])

    def test_neither_phrase_reads_as_a_number_or_a_unit(self):
        for phrase in ps.TRANSITION_PHRASES.values():
            self.assertNotIn("+", phrase)
            self.assertFalse(any(ch.isdigit() for ch in phrase),
                             f"a transition phrase carries a figure: {phrase}")


class BothConsumersActuallyShowIt(unittest.TestCase):
    """A field computed and rendered by nothing is the same defect one layer along — and both
    renderers gated on `deltas`, so a transition-only candidate produced no line at all."""

    def setUp(self):
        self.previous, self.current = _pair("positional_forfeit", None, 14.2, name="Trent McDuffie")
        self.diffs = ps.diff_snapshots(self.previous, self.current)

    def test_the_chairs_are_told_in_words_and_never_in_a_fabricated_number(self):
        """Driven through the real `format_snapshot_for_llm`, which is where the diff block is
        composed. NO CONDITIONAL SKIP: 0.4's instrument is right that a test which skips itself
        when the shape is not what it guessed is a test that stops running silently."""
        block = pd.format_snapshot_for_llm(self.current, self.diffs)
        self.assertIn("Trent McDuffie", block,
                      "the transition-only candidate produced no line for the chairs")
        self.assertIn(ps.TRANSITION_PHRASES[ps.TRANSITION_BECAME_MEASURED], block)
        self.assertNotIn("positional_forfeit: +", block,
                         "a transition was rendered in the shape of a delta")

    def test_the_draft_room_drawer_renders_transitions_with_no_unit(self):
        """Read off the UI surface through `ui_source`, never by naming a file. A transition has no
        magnitude, so attaching `DIFF_UNITS` to it would assert a scale it does not have."""
        source = ui_source.text()
        self.assertIn("TRANSITION_PHRASES", source,
                      "the drawer does not render transitions, so the repair stops at the boundary")
        self.assertIn('d.get("transitions")', source,
                      "the drawer still gates on deltas alone, so a transition-only candidate is "
                      "dropped before it can be shown")

    def test_a_candidate_whose_ONLY_change_is_a_transition_still_gets_a_line(self):
        """The gate, behaviourally rather than by reading the source. Rank is unchanged and there is
        no delta, so before the repair this candidate had nothing to report and reported nothing."""
        entry = self.diffs[0]
        self.assertEqual(entry["rank_delta"], 0)
        self.assertEqual(entry["deltas"], {})
        self.assertIn("Trent McDuffie", pd.format_snapshot_for_llm(self.current, self.diffs))


if __name__ == "__main__":
    unittest.main()
