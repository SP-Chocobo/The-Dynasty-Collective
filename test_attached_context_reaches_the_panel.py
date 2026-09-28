"""MANDATE 1.5 / ARCHITECTURE_AUDIT §3.3: the Debate chip's context was shown to the user
and sent to nobody.

§3.3 named it "The ScreenContext reach gap -- a canonical context that is built, displayed,
and dropped", and counted exactly two reads of the session key in the whole tree: the write
and a render. Two blind passes reached it independently afterwards. This module is the guard
that section asked for.

`render_debate_chip` writes a `ScreenContext` into `st.session_state.debate_attached_context`
(`app.py:1484`). The Prytaneum reads it, prints "💬 **Considering:** On the clock for pick 2.03"
and offers a "Full evidence" expander -- and that read was its ONLY consumer. `build_context` had no
parameter for it, so the panel then answered with no board, no candidates and no pick position, and
could name a player who was already drafted. The dock's own comment says the line is meant to read
as "Debate already understands what I was looking at."

WHY THESE ARE SOURCE CHECKS. `build_context` reads `st.session_state` and `app.py`'s import executes
the page, so it cannot be called from a test -- the same reason every other app-level boundary in
this repository is read rather than invoked (see `ui_source`'s own docstring). What a source check
proves is that the argument is passed and where it lands; the value half -- that what lands there
actually carries the board -- is checked against `screen_context` directly, which IS importable.

ONE CALL SITE, DELIBERATELY. `build_context` has two callers: the debate trigger, and the
condense-to-objective path. Only the first gets the attached screen. The second asks a different
question -- turn this chat message into a stored objective -- and feeding a screen into it would
write the board the user happened to be looking at into an objective's text.
"""
from __future__ import annotations

import ast
import unittest

import screen_context as sc
import ui_source
from test_pick_debate import _candidate, _snapshot


def _build_context_body() -> str:
    return ui_source.block("def build_context(", "\ndef ")


class TheParameterExistsAndIsReadTests(unittest.TestCase):
    def setUp(self):
        tree = ast.parse(ui_source.text())
        self.fn = next(n for n in ast.walk(tree)
                       if isinstance(n, ast.FunctionDef) and n.name == "build_context")

    def test_build_context_takes_the_attached_screen(self):
        names = [a.arg for a in self.fn.args.args + self.fn.args.kwonlyargs]
        self.assertIn("attached_context", names)

    def test_it_defaults_to_absent_so_every_existing_caller_is_unchanged(self):
        """The condense path and every test fixture keep working, and a session with no chip
        click adds nothing to the context."""
        defaults = self.fn.args.defaults
        self.assertTrue(defaults)
        self.assertIsNone(defaults[-1].value)

    def test_the_seed_is_what_reaches_the_context_not_a_second_rendering(self):
        """`to_prompt_seed` is the ScreenContext's own text block, already used by the Trade
        Calculator's anvil buttons. Re-describing the same object here would be a second place for
        the two to disagree."""
        body = _build_context_body()
        self.assertIn("attached_context.to_prompt_seed()", body)

    def test_an_empty_screen_adds_nothing(self):
        body = _build_context_body()
        self.assertIn("if seed.strip():", body)


class TheHeadingStaysOutsideTheFenceTests(unittest.TestCase):
    """The distinction the fencing rule exists for: the app's instruction is the app's voice, and
    the body is not necessarily ours -- a Trade Calculator context carries `trade_partner`, which
    is another Sleeper user's chosen display name."""

    def test_the_body_is_fenced(self):
        self.assertIn('untrusted.fence("screen-the-user-was-looking-at", seed)',
                      _build_context_body())

    def test_the_instruction_comes_before_the_fence_rather_than_inside_it(self):
        body = _build_context_body()
        self.assertLess(body.index("THE SCREEN THIS QUESTION CAME FROM"),
                        body.index('untrusted.fence("screen-the-user-was-looking-at"'),
                        "the app's own instruction was pulled inside the fence")

    def test_the_instruction_says_to_answer_about_it(self):
        """Passing it is only half the repair: a chair handed a screen with no instruction can
        still treat it as background."""
        self.assertIn("Answer about THIS", _build_context_body())


class TheDebateTriggerPassesItTests(unittest.TestCase):
    def test_the_trigger_call_site_passes_the_attached_screen(self):
        lines = ui_source.text().splitlines()
        # Found with a DEFAULT rather than a bare next(): a missing line should fail this test
        # with a sentence, not raise StopIteration. A crash signature is not a detection
        # (`0.4`), and it reads to the next person as a broken test rather than a broken app.
        at = next((i for i, line in enumerate(lines)
                   if "trigger_question, attached_context=" in line), None)
        self.assertIsNotNone(at, "the debate trigger no longer passes the attached screen")
        window = "\n".join(lines[max(0, at - 3):at + 1])
        self.assertIn("build_context(", window)

    def test_the_condense_path_is_the_one_that_does_not(self):
        """Pinned so the asymmetry is a decision rather than an oversight somebody later
        'fixes' without noticing what it would write into an objective."""
        app = ui_source.text()
        condense = app[app.index("condense_context = build_context("):][:400]
        self.assertNotIn("attached_context", condense)


class WhatIsActuallyBeingPassedTests(unittest.TestCase):
    """NON-VACUITY, by value, on the one half that can be run: the seed must carry the board. If
    `to_prompt_seed` produced an empty or contentless block, every source check above would pass
    while the panel still learned nothing."""

    def test_a_draft_room_screen_carries_the_pick_and_its_candidates(self):
        snap = _snapshot([_candidate("1", "Brock Purdy"), _candidate("2", "Justin Fields")])
        seed = sc.build_draft_room_context(snap).to_prompt_seed()
        self.assertIn(snap.pick_label, seed)
        self.assertIn("Brock Purdy", seed)
        self.assertIn("Draft Room", seed)

    def test_the_seed_still_honours_the_withheld_family(self):
        """The context now travels further than it did, so the propagation rule matters more, not
        less. `test_withheld_propagation` owns this boundary; this is the reminder that 1.5 widened
        its reach."""
        import pick_synthesis as ps
        snap = _snapshot([_candidate("1", "Brock Purdy", survival_probability=0.8137)])
        seed = sc.build_draft_room_context(snap).to_prompt_seed()
        self.assertFalse(ps.survival_is_presentable())
        self.assertNotIn("81%", seed)
        self.assertIn("picks until your turn", seed)


if __name__ == "__main__":
    unittest.main()
