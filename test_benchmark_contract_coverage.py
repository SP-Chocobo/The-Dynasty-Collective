"""§5 (ARCHITECTURE_AUDIT Pass 3): does the model benchmark measure the job the chair
actually has to do in production?

`bot_benchmark.py` is a real model-selection methodology — a fixed battery per chair, a
weighted per-chair rubric, and a judge that is never told which model wrote the answer it is
grading. This file does two different things to it, and the difference matters:

  ENFORCEMENT (tests that must always pass). The blind-judge property is the module's own
  stated key safeguard — "the judge is never told which model or provider produced the answer
  it's grading, which is the one safeguard that actually matters here." That was convention.
  JudgeBlindnessTests makes it enforced. BenchmarkCoverageTests likewise pins which chairs the
  battery covers, so a chair added without a battery is a test failure rather than a silent
  hole.

  CHARACTERIZATION (a test that pins a KNOWN GAP, deliberately asserting today's behavior).
  ModeratorContractIsNotBenchmarkedTests records that the one chair whose output is
  machine-parsed in production is scored on four prose dimensions that never check whether the
  output parses. This is not a test of desired behavior. It exists so the gap cannot widen
  unnoticed and so a repair has somewhere to land. **When that gap is repaired, these
  assertions must be inverted, not deleted** — same posture as the round-boundary
  characterization in test_draft_strategy.py.

No provider is called anywhere in this file; every check runs the real production parsers or
a stubbed caller.
"""

import inspect
import unittest

import bot_benchmark
import llm_engine
import pick_debate


# A fluent, on-topic, entirely plausible Moderator answer that simply does not end with the
# structured block MODERATOR_SYSTEM_PROMPT demands. This is the realistic failure: not a
# refusal, not an error, just a model that answers well in its own format.
ARTICULATE_BUT_UNPARSEABLE = (
    "All three analysts are circling the same tension. The Quant's fair-value read is sound on "
    "the raw math, but it treats two late-firsts as a single blended number, which papers over "
    "the variance the Contrarian is right to flag. The Beat's soft-tissue history is the "
    "deciding input.\n\n"
    "My call is to hold. The picks do not clear the bar over a proven producer at this price."
)

# The same answer, ending with the block. Present so the assertions below cannot pass
# vacuously against a parser that returns {} for everything.
SAME_ANSWER_WITH_BLOCK = ARTICULATE_BUT_UNPARSEABLE + (
    "\n\nRECOMMENDATION: HOLD\n"
    "CONVICTION: Majority\n"
    "REASON: The injury history is already priced into what you would be offered.\n"
    "DISSENT: Quant, who reads the trade as fair value on the raw points.\n"
    "RISK: A snap-share collapse would strand you holding a declining asset.\n"
)


class JudgeBlindnessTests(unittest.TestCase):
    """The module's own stated key safeguard, made enforced."""

    def _capture_judge_prompt(self, response_text: str) -> tuple[str, str]:
        captured = {}

        def _stub(system_prompt, user_prompt, api_key=None, model=None):
            captured["system"] = system_prompt
            captured["user"] = user_prompt
            return "SYNTHESIS: 80\nDISAGREEMENT_HANDLING: 70\nCLARITY: 90\nACTIONABILITY: 60\nNOTES: fine"

        original = llm_engine.PROVIDER_CALLERS.get("claude")
        llm_engine.PROVIDER_CALLERS["claude"] = _stub
        try:
            bot_benchmark._judge_response(
                "moderator", "Weigh these three reports.", response_text,
                "claude", "key", "judge-model-name",
            )
        finally:
            llm_engine.PROVIDER_CALLERS["claude"] = original
        return captured["system"], captured["user"]

    def test_the_judge_is_never_told_which_model_wrote_the_answer(self):
        # A response deliberately produced by a named candidate; the judge must see the text
        # and the task, and nothing identifying the author.
        system, user = self._capture_judge_prompt("A perfectly ordinary answer about dynasty value.")
        for identifier in ("gemini", "openai", "anthropic", "claude-opus", "gpt-4o", "candidate-model-7"):
            self.assertNotIn(identifier, user.lower(), f"The judge prompt leaks {identifier!r}.")
            self.assertNotIn(identifier, system.lower(), f"The judge system prompt leaks {identifier!r}.")

    def test_the_judge_prompt_carries_the_task_and_the_response_and_the_rubric(self):
        """Non-vacuity for the test above: a judge prompt that leaked nothing because it
        contained nothing would pass blindness trivially."""
        _, user = self._capture_judge_prompt("A perfectly ordinary answer about dynasty value.")
        self.assertIn("Weigh these three reports.", user)
        self.assertIn("A perfectly ordinary answer about dynasty value.", user)
        for key, _, _ in bot_benchmark.RUBRIC["moderator"]:
            self.assertIn(key.upper(), user)

    def test_run_benchmark_passes_no_model_identity_into_the_judge_call(self):
        """The judge signature itself is the boundary: _judge_response takes the role, the
        question, the response, and the JUDGE's own provider/model -- never the candidate's."""
        params = list(inspect.signature(bot_benchmark._judge_response).parameters)
        self.assertEqual(
            params,
            ["role", "question_prompt", "response_text",
             "judge_provider", "judge_api_key", "judge_model"],
            "The judge's parameter list changed. Any new parameter must be checked for "
            "candidate identity before this test is updated.",
        )


class BenchmarkCoverageTests(unittest.TestCase):
    """Which chairs the model-selection methodology actually covers."""

    def _draft_room_chairs(self) -> set[str]:
        return {
            attr[: -len("_SYSTEM_PROMPT")].lower()
            for attr in dir(pick_debate) if attr.endswith("_SYSTEM_PROMPT")
        }

    def test_the_battery_covers_every_prytaneum_chair(self):
        self.assertEqual(set(bot_benchmark.BENCHMARK_BATTERY), set(llm_engine.ROLE_SYSTEM_PROMPTS))

    def test_the_draft_room_chairs_have_no_battery_and_that_set_is_pinned(self):
        """Not an aspiration -- a guard. The Draft Room's three chairs are deliberately outside
        bot_config's persisted routing (see pick_debate.debate_pick's docstring), so they have
        no model-selection methodology at all. Pinned so that adding a fourth Draft Room chair,
        or moving one under bot_config, is a visible change rather than a silent one."""
        uncovered = self._draft_room_chairs() - set(bot_benchmark.BENCHMARK_BATTERY)
        self.assertEqual(uncovered, {"strategist", "skeptic", "caller"})

    def test_the_battery_runs_under_the_production_chair_prompt_not_a_copy(self):
        """A benchmark that graded models against a drifted copy of the chair contract would
        rank them on a job nobody holds."""
        source = inspect.getsource(bot_benchmark.run_benchmark)
        self.assertIn("llm_engine.ROLE_SYSTEM_PROMPTS[role]", source)

    def test_the_report_shape_is_pinned_so_absent_fields_stay_visible(self):
        """The report records what ran and how it scored -- not the battery version, the chair
        prompt it ran against, or any cost. Pinned so that adding one of those is deliberate,
        and so their absence is stated rather than assumed."""
        captured = {}

        def _stub(system_prompt, user_prompt, api_key=None, model=None):
            return "SYNTHESIS: 50\nDISAGREEMENT_HANDLING: 50\nCLARITY: 50\nACTIONABILITY: 50\nNOTES: ok"

        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub
        try:
            report = bot_benchmark.run_benchmark(
                "moderator", [("claude", "some-model")], {"claude": "key"}, judge_provider="claude",
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        captured = set(report)
        self.assertEqual(captured, {"role", "ran_at", "judge_provider", "judge_model", "candidates"})
        for absent in ("battery_version", "rubric_version", "contract_version", "cost", "chair_prompt"):
            self.assertNotIn(absent, captured)

    def test_saving_a_report_replaces_rather_than_appends(self):
        """Pins why degradation of an existing model cannot be detected: there is one report
        per role, never a series. Characterization of a known limitation, not a preference."""
        source = inspect.getsource(bot_benchmark.save_report)
        self.assertIn("all_reports[role] = report", source)
        self.assertNotIn("append", source)


class ModeratorContractIsNotBenchmarkedTests(unittest.TestCase):
    """KNOWN GAP — characterization. Invert these when the gap is repaired; do not delete.

    The Moderator is the only Prytaneum chair whose output is consumed by machine rather than
    only read by a human. Its system prompt -- the exact one the benchmark runs models under --
    requires a structured block, and four production consumers depend on it. The rubric that
    decides which model wins the chair scores none of that.
    """

    def test_the_production_prompt_the_benchmark_uses_demands_the_structured_block(self):
        prompt = llm_engine.ROLE_SYSTEM_PROMPTS["moderator"]
        self.assertIn("RECOMMENDATION:", prompt)
        self.assertIn("CONVICTION:", prompt)

    def test_no_moderator_rubric_dimension_scores_that_block(self):
        haystack = " ".join(
            f"{key} {desc}" for key, _, desc in bot_benchmark.RUBRIC["moderator"]
        ).lower()
        for concept in ("format", "structur", "block", "field", "label", "parse"):
            self.assertNotIn(concept, haystack)

    def test_no_moderator_rubric_dimension_scores_factual_grounding(self):
        """Separately worth pinning: unlike quant and beat, the moderator rubric has no
        accuracy dimension at all -- it scores synthesis, disagreement handling, clarity and
        actionability, all of which a fluent and entirely wrong answer can win."""
        keys = {key for key, _, _ in bot_benchmark.RUBRIC["moderator"]}
        self.assertEqual(keys, {"synthesis", "disagreement_handling", "clarity", "actionability"})
        self.assertIn("accuracy", {key for key, _, _ in bot_benchmark.RUBRIC["quant"]})
        self.assertIn("accuracy", {key for key, _, _ in bot_benchmark.RUBRIC["beat"]})

    def test_no_battery_prompt_asks_the_model_for_the_block(self):
        for question in bot_benchmark.BENCHMARK_BATTERY["moderator"]:
            self.assertNotIn("RECOMMENDATION", question["prompt"])

    def test_the_benchmark_never_runs_the_production_parser_over_a_response(self):
        source = inspect.getsource(bot_benchmark)
        for parser in ("parse_moderator_verdict", "parse_todo_directives",
                       "parse_source_findings", "parse_source_comparisons"):
            self.assertNotIn(parser, source)

    def test_a_fluent_block_less_answer_yields_nothing_for_four_consumers(self):
        """What the winner of that rubric can still do in production."""
        self.assertEqual(llm_engine.parse_moderator_verdict(ARTICULATE_BUT_UNPARSEABLE), {})
        self.assertEqual(
            llm_engine.parse_todo_directives(ARTICULATE_BUT_UNPARSEABLE),
            {"updates": [], "likely_resolved": []},
        )
        self.assertEqual(llm_engine.parse_source_findings(ARTICULATE_BUT_UNPARSEABLE), [])
        self.assertEqual(llm_engine.parse_source_comparisons(ARTICULATE_BUT_UNPARSEABLE), [])

    def test_the_same_answer_with_the_block_parses_so_the_gap_is_real_not_a_dead_parser(self):
        """Non-vacuity. Without this, the test above would pass equally against a parser that
        never returns anything, and the finding would be about the parser rather than the
        benchmark."""
        verdict = llm_engine.parse_moderator_verdict(SAME_ANSWER_WITH_BLOCK)
        self.assertEqual(verdict.get("recommendation"), "HOLD")
        self.assertEqual(verdict.get("conviction"), "Majority")
        self.assertTrue(verdict.get("reason"))

    def test_the_benchmark_user_message_is_not_the_shape_production_sends(self):
        """A smaller mismatch in the same family: every production ask_* wraps the user
        message as 'League/roster context:\\n{context}\\n\\nQuestion: {question}'. The
        benchmark sends the bare scenario string, so a model is graded on a message shape it
        will never actually receive."""
        for chair in ("quant", "beat"):
            production = inspect.getsource(getattr(llm_engine, f"ask_{chair}"))
            self.assertIn("League/roster context:", production)
        benchmark = inspect.getsource(bot_benchmark.run_benchmark)
        self.assertIn('q["prompt"]', benchmark)
        self.assertNotIn("League/roster context:", benchmark)


class ToolGrantIsUniformAcrossChairsTests(unittest.TestCase):
    """§5 asks whether evaluation separates raw reasoning from tool-use and research ability.
    It cannot, because the grant is not per-chair: every provider caller enables live web
    search unconditionally, including for the chair whose prompt forbids fetching."""

    def test_every_provider_caller_grants_web_search_unconditionally(self):
        for caller in (llm_engine._call_claude, llm_engine._call_gemini, llm_engine._call_openai):
            source = inspect.getsource(caller)
            self.assertIn("tools=", source, f"{caller.__name__} does not pass tools at all.")
            # The grant is a literal in the request, never inside a role branch. Checked by
            # confirming the callers take no role parameter to branch on in the first place.
            self.assertNotIn("role", list(inspect.signature(caller).parameters))

    def test_the_quant_is_told_not_to_fetch_while_holding_the_same_grant(self):
        self.assertIn("go fetch outside market consensus yourself", llm_engine.QUANT_SYSTEM_PROMPT)
        self.assertIn("Use live search", llm_engine.BEAT_SYSTEM_PROMPT)

    def test_no_beat_battery_scenario_requires_a_lookup(self):
        """So discovery -- the first thing §5 names for Beat -- is never exercised even though
        the capability is present."""
        for question in bot_benchmark.BENCHMARK_BATTERY["beat"]:
            text = question["prompt"]
            self.assertTrue(
                any(text.strip().startswith(opener) for opener in
                    ("Given this report", "A team signs", "You see two posts")),
                f"{question['label']} may no longer be self-contained -- re-check the coverage claim.",
            )


if __name__ == "__main__":
    unittest.main()
