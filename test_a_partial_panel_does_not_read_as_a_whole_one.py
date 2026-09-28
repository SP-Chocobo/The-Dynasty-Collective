"""MANDATE 1.7 / ARCHITECTURE_AUDIT §11.3a: a debate that half-failed presented as one that did not.

Two findings, one shape -- a claim shown to a person with nothing qualifying it.

FAILED OR CUT-OFF CHAIRS were reported only through `notify()`, which is a one-rerun toast. The
recommendation panel persists across reruns; the toast does not. So a debate whose Skeptic never
answered showed a clean "## Recommendation: <name>" on every rerun after the first, with nothing
saying a third of the panel was missing. `debate_pick` builds that list carefully -- it separates an
outright failure from a report truncated at the provider's output cap, and says which -- and then it
reached a reader for one rerun.

CONFIDENCE was unvalidated. The Caller's contract admits exactly three values, and its prompt says in
so many words that "CONFIDENCE is never a percentage -- percentages from an LLM are fake precision".
Nothing checked. A model answering "85%" reached `PickDebateResult.confidence` unexamined and was
printed as "Confidence: 85%", which reads as a number this app produced.

The vocabulary now has ONE home and the prompt line is BUILT from it, the same way `_survival_clause`
is built from `withheld_fields()`: a vocabulary stated twice has two things to keep in step.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import pick_debate as pd
import ui_source


class TheConfidenceVocabularyHasOneHomeTests(unittest.TestCase):
    def test_the_prompt_line_is_built_from_the_tuple(self):
        """Not spelled a second time. The day a value is added or renamed, the prompt follows
        without anyone remembering it."""
        source = Path("pick_debate.py").read_text()
        self.assertIn('.replace("{confidence_values}", " / ".join(CALLER_CONFIDENCE_VALUES))', source)
        self.assertIn("CONFIDENCE: {confidence_values}", source,
                      "the prompt spells the values literally again")

    def test_the_placeholder_is_actually_substituted(self):
        """The import-time assertion covers this too; here it is as a test, because a prompt that
        shipped a literal brace to a model is the failure that reads plausibly."""
        self.assertNotIn("{confidence_values}", pd.CALLER_SYSTEM_PROMPT)
        self.assertIn(" / ".join(pd.CALLER_CONFIDENCE_VALUES), pd.CALLER_SYSTEM_PROMPT)

    def test_the_three_values_are_the_ones_the_prompt_explains(self):
        """NON-VACUITY: the tuple must be the contract, not an arbitrary triple. Each value has a
        sentence in the prompt defining it, and this fails if one loses its definition."""
        for value in pd.CALLER_CONFIDENCE_VALUES:
            with self.subTest(value=value):
                self.assertIn(f"{value} means", pd.CALLER_SYSTEM_PROMPT)


class WhatCountsAsAnAnswerTests(unittest.TestCase):
    def test_the_three_contract_values_pass_in_any_casing(self):
        for value in ("Unanimous", "lean", " SPLIT "):
            with self.subTest(value=value):
                self.assertTrue(pd.confidence_is_in_contract(value))

    def test_a_percentage_does_not(self):
        """The case the prompt forbids by name."""
        self.assertFalse(pd.confidence_is_in_contract("85%"))
        self.assertFalse(pd.confidence_is_in_contract("high"))
        self.assertFalse(pd.confidence_is_in_contract("Unanimous-ish"))

    def test_absence_is_not_an_answer_either(self):
        self.assertFalse(pd.confidence_is_in_contract(None))
        self.assertFalse(pd.confidence_is_in_contract(""))


class BothPanelsQualifyWhatTheyShowTests(unittest.TestCase):
    """The live Draft Room and its Mock Draft twin, through ONE pair of renderers -- #116 found
    those two as separate code carrying identical copy, and a shared function is what makes
    "repaired together" structural rather than a test's hope. Source checks: `app.py`'s import
    executes the page, and what the functions DECIDE is checked by value above."""

    def setUp(self):
        self.app = ui_source.text()

    def test_there_is_one_definition_of_each_and_two_call_sites(self):
        for name in ("_render_debate_integrity", "_render_confidence_caption"):
            with self.subTest(name=name):
                self.assertEqual(1, self.app.count(f"def {name}("))
                self.assertEqual(2, self.app.count(f"{name}(mock_current_debate)")
                                 + self.app.count(f"{name}(debate_result)"))

    def test_no_panel_prints_a_bare_confidence_any_more(self):
        self.assertNotIn('st.caption(f"Confidence: {debate_result.confidence}")', self.app)
        self.assertNotIn('st.caption(f"Confidence: {mock_current_debate.confidence}")', self.app)

    def test_an_out_of_contract_value_is_kept_and_labelled_rather_than_dropped(self):
        """It is the Caller's own words about its own certainty, which is worth reading; what it is
        not is a grade this app can interpret."""
        block = ui_source.block("def _render_confidence_caption(result)", until="\n\n\ndef ")
        self.assertIn("OUTSIDE the panel's own vocabulary", block)
        self.assertIn("{result.confidence}", block)
        self.assertIn("CALLER_CONFIDENCE_VALUES", block,
                      "the labelled sentence must name the vocabulary from its one home")

    def test_the_branch_IS_the_contract_check_and_not_merely_near_it(self):
        """READ THE CODE, NOT THE TEXT OF IT (`#200`). My first version of the test above only
        asserted the labelled sentence was present in the function -- and a mutation replacing the
        gate with `if True:` left that sentence sitting right there, unreachable, and the test
        passed. The condition is what decides, so the condition is what is read.

        Taken from the parsed function rather than by grep, so reformatting it is not a failure and
        bypassing it is."""
        import ast
        tree = ast.parse(ui_source.text())
        fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   and n.name == "_render_confidence_caption"), None)
        self.assertIsNotNone(fn, "the shared confidence renderer is gone")
        gates = [ast.unparse(node.test) for node in ast.walk(fn) if isinstance(node, ast.If)]
        self.assertIn("pick_debate.confidence_is_in_contract(result.confidence)", gates,
                      f"no branch in this function asks the contract; its tests are {gates}")

    def test_the_integrity_warning_sits_above_the_recommendation_it_qualifies(self):
        lines = self.app.splitlines()
        for call in ("_render_debate_integrity(debate_result)",
                     "_render_debate_integrity(mock_current_debate)"):
            at = next(i for i, line in enumerate(lines) if call in line)
            window = "\n".join(lines[at:at + 8])
            with self.subTest(call=call):
                self.assertIn("Recommendation:", window,
                              "the warning must be beside the recommendation, not somewhere else")

    def test_the_toast_is_kept_as_well(self):
        """The two say different things: one is "this just happened", the other is "this is what you
        are looking at". Removing the toast would lose the first.

        THREE, not two, and I expected two -- this test is how I found the third. The Prytaneum's
        chat debate reports its failed roles the same way, and its shape is different: those roles'
        error strings are APPENDED TO THE CHAT, so they persist by themselves. That surface's defect
        is therefore the opposite one, and it is repaired separately below."""
        self.assertEqual(3, self.app.count('notify("warning", "Debate finished with issues: "'))


class AFailedCallIsNotThatRolesAnalysisTests(unittest.TestCase):
    """The third surface, and the sub-finding that goes with it: the Prytaneum's chat debate appends
    a failed role's error text to the chat under that role, and CONVERSATION MEMORY replayed it to
    every later debate as `[quant] WARNING Claude request failed: ...`.

    A model reading that has been handed a provider outage as prior reasoning about its own league.
    The message STAYS in the chat -- a person should see that a chair failed -- and is stamped so it
    stays out of the analytical record, which is exactly the distinction `notice` messages already
    draw."""

    def test_the_marker_has_one_home_and_a_named_check(self):
        """Three readers was the point at which a bare literal needed a name (`#126`)."""
        import llm_engine
        self.assertEqual("\u26a0\ufe0f", llm_engine.FAILED_CALL_PREFIX)
        self.assertTrue(llm_engine.is_failed_call(
            llm_engine.FAILED_CALL_PREFIX + " Claude request failed: boom"))
        self.assertFalse(llm_engine.is_failed_call("A short but real report."))
        self.assertFalse(llm_engine.is_failed_call(None))
        self.assertFalse(llm_engine.is_failed_call(""))

    def test_every_soft_fail_return_in_llm_engine_carries_it(self):
        """The contract, checked rather than trusted: a provider caller that started returning an
        unmarked failure string would silently become analysis at every reader."""
        import llm_engine
        source = Path("llm_engine.py").read_text()
        returns = [line.strip() for line in source.splitlines()
                   if line.strip().startswith("return") and "request failed" in line]
        self.assertTrue(returns, "no soft-fail returns found -- this check has lost its subject")
        for line in returns:
            with self.subTest(line=line):
                self.assertIn(llm_engine.FAILED_CALL_PREFIX, line)

    def test_pick_debate_reads_the_named_check_rather_than_the_literal(self):
        source = Path("pick_debate.py").read_text()
        self.assertIn("if is_failed_call(text)]", source)
        self.assertNotIn('text.startswith("\u26a0\ufe0f")', source)

    def test_append_message_stamps_a_failed_call(self):
        block = ui_source.block("def append_message(", until="\n\n\ndef ")
        self.assertIn("if llm_engine.is_failed_call(content):", block)
        self.assertIn('msg["failed"] = True', block)

    def test_conversation_memory_drops_a_failed_message_in_both_windows(self):
        """Both branches: the tail of the history, and a window centred on one past message."""
        block = ui_source.block("def build_context(", "\ndef ")
        self.assertEqual(2, block.count('not m.get("failed")'),
                         "one of the two memory windows still replays failed calls")

    def test_the_message_is_kept_in_the_chat_rather_than_dropped(self):
        """NON-VACUITY in the other direction: a repair that stopped appending it would hide from a
        person the fact that a chair failed, which is the opposite error."""
        block = ui_source.block("def append_message(", until="\n\n\ndef ")
        self.assertIn("st.session_state.chat_history.append(msg)", block)
        self.assertNotIn("return", block.split('msg["failed"] = True')[1].split("chat_history.append")[0],
                         "a failed message now returns early instead of reaching the chat")


if __name__ == "__main__":
    unittest.main()
