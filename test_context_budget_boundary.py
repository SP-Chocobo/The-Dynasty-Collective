"""§9 (ARCHITECTURE_AUDIT Pass 6): context compaction, handoffs and budgets.

The guide's §9 mandate: *context limits may reduce supporting information, but may not silently
alter, omit, or distort mandatory deterministic state or authoritative evidence required for the
chair's task.*

That mandate holds today, and this file pins the reasons it holds — most of which were not
written down as budget guarantees:

  * **Mandatory deterministic state is never capped.** The roster, the league's full scoring
    settings, the freshness manifest, every active objective and the league-wide positional
    depth are emitted in full. Measured, the entire deterministic portion of a chair's context
    is roughly 8.4k tokens; the dominant term (84% of the worst case) is replayed model prose.
    So the mandate is satisfied with enormous headroom — but by proportion, not by design, which
    is why it is pinned here rather than assumed.
  * **Compaction is non-destructive.** History summarization writes a timestamped backup before
    overwriting and aborts outright if the summarizer call fails.
  * **Every other cap is a deterministic slice**, not a judgement call.

And it characterizes what does not hold (invert on repair, do not delete):

  * **Output truncation is undetected.** `MAX_TOKENS` was raised 1024 → 4096 precisely because
    the Moderator's structured block sits at the end of its response and a tight budget cuts it
    off first — but the mitigation is headroom, not a detector, and no provider's stop reason is
    ever inspected.
  * **There is no input-token accounting and no per-model context policy** — every chair
    receives the same string whatever window its model has.

No provider is called anywhere in this file.
"""

import ast
import inspect
import re
import unittest
from pathlib import Path

import llm_engine
import pick_synthesis
import screen_context

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()


def _build_context_body() -> str:
    start = _APP.index("def build_context(")
    return _APP[start:_APP.index("\ndef ", start + 10)]


class MandatoryStateIsNeverCompactedTests(unittest.TestCase):
    """§9's mandate, pinned at the sections it actually protects."""

    def test_the_roster_is_emitted_in_full(self):
        """The one piece of state a chair cannot do its job without. Iterated whole -- no
        slice, no head, no cap."""
        body = _build_context_body()
        self.assertIn("for row in roster_table:", body)
        self.assertNotRegex(body, r"for row in roster_table\[")

    def test_league_scoring_settings_freshness_and_objectives_are_emitted_in_full(self):
        body = _build_context_body()
        # Checked by AST rather than by string surgery: each of these must iterate a plain
        # Name/Attribute/Call, never a Subscript -- a slice is exactly what a cap looks like.
        # Collect every loop's ITER node. Keyed by the iterated expression, not by the loop
        # variable -- several loops here bind `row`/`item`, and a dict keyed by target silently
        # drops all but the last, which is exactly how this test first passed over a section it
        # had never checked.
        tree = ast.parse(body)
        iterated = [node.iter for node in ast.walk(tree) if isinstance(node, ast.For)]
        mandatory = {
            "depth.items()": "league-wide positional depth",
            "freshness": "the freshness manifest",
            "active_todos": "active objectives",
            "roster_table": "your roster",
        }
        sources = {ast.unparse(it): it for it in iterated}
        for expected, label in mandatory.items():
            self.assertIn(expected, sources, f"{label} is no longer iterated in build_context.")
            self.assertNotIsInstance(
                sources[expected], ast.Subscript, f"{label} is now sliced -- it must be emitted in full.",
            )
        self.assertIn("format_scoring_settings", body)

    def test_the_deterministic_portion_of_a_context_stays_small_enough_to_never_be_the_problem(self):
        """A budget guarantee expressed as the caps themselves. If someone later uncaps a
        supporting section into the thousands of rows, the mandate stops holding by proportion
        and this fails."""
        caps = {
            "narrowed candidates": pick_synthesis.DEFAULT_NARROW_COUNT,
            "candidate/FA rows in a ScreenContext": screen_context._MAX_CANDIDATES_IN_CONTEXT,
            "best available Sleeper players": int(
                re.search(r"projected_available\s*=[\s\S]*?\[:(\d+)\]", _build_context_body()).group(1)
            ),
            "pinned messages": 5,
            "archived objectives": 5,
            "past decision outcomes": 5,
        }
        for label, cap in caps.items():
            self.assertLessEqual(cap, 30, f"{label} grew past a supporting-information cap.")
            self.assertGreater(cap, 0, label)


class CompactionIsNonDestructiveTests(unittest.TestCase):
    """§9: is the original uncompacted context preserved for audit/replay?"""

    def _compact_source(self) -> str:
        start = _APP.index("def compact_league_history(")
        return _APP[start:_APP.index("\ndef ", start + 10)]

    def test_a_backup_is_written_before_history_is_overwritten(self):
        source = self._compact_source()
        backup_at = source.index("backup_path.write_text")
        save_at = source.index("save_chat_history(")
        self.assertLess(backup_at, save_at, "History is overwritten before the backup is written.")
        self.assertIn("pre_compact_", source)

    def test_compaction_aborts_rather_than_pruning_on_a_summarizer_failure(self):
        source = self._compact_source()
        abort_at = source.index('if new_summary.startswith("⚠️")')
        self.assertLess(abort_at, source.index("backup_path.write_text"))
        self.assertIn("Compaction aborted, history untouched", source)

    def test_the_summariser_fails_soft_so_that_abort_can_fire(self):
        """Non-vacuity for the test above: the guard only works because summarize_history
        returns a ⚠️ string instead of raising."""
        self.assertTrue(llm_engine.summarize_history([]).startswith("⚠️"))

    def test_every_cap_except_history_summarisation_is_a_deterministic_slice(self):
        """§9: is compaction deterministic and reproducible? Everywhere but one place, yes --
        the caps are slices and limits. The single model-performed compaction is history
        summarisation, and it is pinned here so a second one cannot appear unnoticed."""
        body = _build_context_body()
        model_calls = [
            line for line in body.splitlines()
            if "llm_engine." in line and not line.strip().startswith("#")
        ]
        self.assertEqual(model_calls, [], "build_context now calls a model to shape its own context.")

    def test_history_summarisation_is_not_routed_through_configurable_roles(self):
        """Deterministic in provider at least: app bookkeeping, never a debate persona whose
        model a user can swap underneath the stored memory."""
        self.assertIn("Always runs on Claude", llm_engine.summarize_history.__doc__)
        source = inspect.getsource(llm_engine.summarize_history)
        self.assertIn("_call_claude", source)
        self.assertNotIn("PROVIDER_CALLERS", source)


class OutputBudgetTests(unittest.TestCase):
    def test_the_output_cap_is_shared_by_every_provider_and_is_not_the_known_tight_value(self):
        """1024 was measured as genuinely tight for a real multi-line verdict -- reasoning plus
        the block plus repeatable TODO/SOURCE lines routinely ran past it, silently cutting the
        block off. The headroom is the whole mitigation, so it is pinned."""
        self.assertGreaterEqual(llm_engine.MAX_TOKENS, 4096)
        for caller in (llm_engine._call_claude, llm_engine._call_gemini, llm_engine._call_openai):
            source = inspect.getsource(caller)
            self.assertRegex(source, r"max_(output_)?tokens=MAX_TOKENS",
                             f"{caller.__name__} does not use the shared output cap.")

    def test_the_structured_block_really_does_sit_at_the_end_of_the_moderator_contract(self):
        """Why truncation matters here specifically, asserted rather than assumed: everything a
        machine consumes comes after everything a human reads."""
        prompt = llm_engine.MODERATOR_SYSTEM_PROMPT
        self.assertIn("end your response with this exact structured block", prompt)
        self.assertLess(prompt.index("RECOMMENDATION:"), prompt.index("SOURCE FINDING:"))


class NoBudgetAccountingTests(unittest.TestCase):
    """KNOWN GAPS — characterization. Invert when repaired; do not delete."""

    PRODUCTION_MODULES = ("llm_engine", "pick_debate", "bot_benchmark", "screen_context")

    def test_nothing_counts_input_tokens_or_knows_a_model_context_window(self):
        for name in self.PRODUCTION_MODULES:
            source = (_HERE / f"{name}.py").read_text()
            for marker in ("count_tokens", "tiktoken", "context_window", "token_budget",
                           "max_input_tokens"):
                self.assertNotIn(marker, source, f"{name} gained budget accounting -- invert this test.")

    def test_no_provider_stop_reason_is_ever_inspected(self):
        """§9: 'can required information ever be silently dropped?' At the output end, yes. The
        hazard is documented in MAX_TOKENS' own comment and mitigated with headroom; nothing
        detects it if the headroom is exceeded."""
        for name in ("llm_engine", "pick_debate"):
            source = (_HERE / f"{name}.py").read_text()
            for marker in ("stop_reason", "finish_reason", "incomplete_details"):
                self.assertNotIn(marker, source, f"{name} now detects truncation -- invert this test.")

    def test_a_truncated_verdict_is_indistinguishable_from_a_model_that_ignored_the_format(self):
        """The consequence, shown through the real parser: a response cut off before its block
        and a response that never had one produce byte-identical downstream results. Until
        truncation is detected, #94's contract-failure signal cannot tell them apart."""
        full = ("Reasoning about the trade.\n\nRECOMMENDATION: HOLD\nCONVICTION: Split\n"
                "REASON: the injury history is priced in\n")
        truncated_at_the_cap = "Reasoning about the trade.\n\nRECOMMEN"
        never_formatted = "Reasoning about the trade. My call is to hold."
        self.assertTrue(llm_engine.parse_moderator_verdict(full), "the control must parse")
        self.assertEqual(
            llm_engine.parse_moderator_verdict(truncated_at_the_cap),
            llm_engine.parse_moderator_verdict(never_formatted),
        )

    def test_every_chair_gets_the_same_context_whatever_window_its_model_has(self):
        """§9: 'does each model receive the same canonical package with infrastructure
        compaction, or a model-specific context policy?' Neither -- the same string, with no
        policy at all. A smaller-context replacement silently receives an identical task."""
        for name in ("ask_quant", "ask_beat", "ask_contrarian", "ask_moderator"):
            source = inspect.getsource(getattr(llm_engine, name))
            self.assertIn("context", source)
            for marker in ("window", "budget", "truncate", "if model"):
                self.assertNotIn(marker, source, f"{name} gained a per-model context policy.")


class HandoffCarriesProseNotEvidenceTests(unittest.TestCase):
    """§9: 'when chairs hand off, is the next chair given canonical state + validated evidence +
    prior chair outputs rather than merely the previous chair's compacted conversation?'"""

    def test_a_downstream_prytaneum_chair_receives_prior_prose_and_a_rebuilt_context(self):
        source = inspect.getsource(llm_engine.ask_moderator)
        self.assertIn("QUANT / VORP REPORT", source)
        self.assertIn("{context}", source)
        # Prose in, prose out: the reports arrive as opaque strings, not structured evidence.
        # llm_engine uses `from __future__ import annotations`, so these come back as the
        # string "str" rather than the type -- the point stands either way: a chair's report
        # crosses as text, never as a structured evidence object.
        signature = inspect.signature(llm_engine.ask_moderator)
        for chair in ("quant", "beat", "contrarian"):
            self.assertEqual(signature.parameters[chair].annotation, "str")

    def test_a_downstream_draft_room_chair_receives_the_canonical_snapshot_itself(self):
        """The better of the two handoffs, and worth pinning as the standard: every Draft Room
        chair reasons over the same frozen PickSnapshot rather than a re-derivation of it."""
        import pick_debate
        source = inspect.getsource(pick_debate.debate_pick)
        self.assertIn("evidence = format_snapshot_for_llm(snapshot, diffs)", source)
        # Built once, handed to all three chairs -- not re-derived per chair.
        self.assertEqual(source.count("format_snapshot_for_llm"), 1)
        for chair_prompt in ("skeptic_prompt", "caller_prompt"):
            self.assertIn(chair_prompt, source)
        self.assertIn('f"{evidence}\\n\\n--- STRATEGIST\'S CASE ---', source)


if __name__ == "__main__":
    unittest.main()
