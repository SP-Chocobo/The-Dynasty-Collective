import shutil
import tempfile
import unittest
from pathlib import Path

import bot_benchmark as bb
import llm_engine


class RubricAndBatteryConsistencyTests(unittest.TestCase):
    """The weighted-score math in run_benchmark assumes every role's rubric weights sum to
    100 (stated explicitly in RUBRIC's own comment) -- a drifted rubric wouldn't crash
    (it divides by the actual weight_total), but would silently break the "0-100 scale"
    promise the judge prompt and the UI both rely on."""

    def test_every_roles_rubric_weights_sum_to_100(self):
        for role, dims in bb.RUBRIC.items():
            total = sum(weight for _, weight, _ in dims)
            self.assertEqual(total, 100, role)

    def test_every_role_with_a_rubric_has_a_benchmark_battery(self):
        self.assertEqual(set(bb.RUBRIC.keys()), set(bb.BENCHMARK_BATTERY.keys()))

    def test_every_role_has_exactly_three_battery_scenarios(self):
        for role, scenarios in bb.BENCHMARK_BATTERY.items():
            self.assertEqual(len(scenarios), 3, role)

    def test_every_role_has_a_system_prompt_to_run_it_under(self):
        for role in bb.RUBRIC:
            self.assertIn(role, llm_engine.ROLE_SYSTEM_PROMPTS)


class JudgeResponseParsingTests(unittest.TestCase):
    """_judge_response's own line-parsing logic, tested directly against a fake judge
    caller -- same fail-soft posture as llm_engine's parse_* functions: an unrecognized or
    malformed line is dropped, never a raised exception."""

    def setUp(self):
        self._orig_callers = dict(llm_engine.PROVIDER_CALLERS)
        self.addCleanup(lambda: llm_engine.PROVIDER_CALLERS.update(self._orig_callers))

    def _judge_returns(self, text):
        llm_engine.PROVIDER_CALLERS.update({
            "claude": lambda system_prompt, user_prompt, api_key, model: text,
        })

    def test_parses_every_rubric_dimension_and_notes(self):
        self._judge_returns(
            "ACCURACY: 85\nMETHODOLOGY: 70\nRELEVANCE: 90\nCONSISTENCY: 60\n"
            "NOTES: Solid but a bit generic in places."
        )
        scores, notes = bb._judge_response("quant", "question", "response", "claude", "key", None)
        self.assertEqual(scores, {"accuracy": 85, "methodology": 70, "relevance": 90, "consistency": 60})
        self.assertEqual(notes, "Solid but a bit generic in places.")

    def test_an_out_of_range_score_is_clamped_to_100(self):
        # The judge is only ever instructed to score 0-100, so this covers a model that
        # doesn't follow that instruction cleanly (e.g. outputs "150") rather than a
        # realistic negative case -- the regex extracts digits only, so a literal "-10"
        # parses as 10, not -10; not worth hardening against a shape the judge is never
        # actually asked to produce.
        self._judge_returns("ACCURACY: 150\nMETHODOLOGY: 50\nRELEVANCE: 50\nCONSISTENCY: 50\nNOTES: n/a")
        scores, _ = bb._judge_response("quant", "q", "r", "claude", "key", None)
        self.assertEqual(scores["accuracy"], 100)

    def test_missing_dimension_lines_are_simply_absent_not_defaulted(self):
        self._judge_returns("ACCURACY: 80\nNOTES: only scored one dimension")
        scores, notes = bb._judge_response("quant", "q", "r", "claude", "key", None)
        self.assertEqual(scores, {"accuracy": 80})
        self.assertEqual(notes, "only scored one dimension")

    def test_unparseable_response_yields_empty_scores_and_notes(self):
        self._judge_returns("Just some prose with no recognized format at all.")
        scores, notes = bb._judge_response("quant", "q", "r", "claude", "key", None)
        self.assertEqual(scores, {})
        self.assertEqual(notes, "")

    def test_bullet_prefixed_lines_still_parse(self):
        self._judge_returns("- ACCURACY: 80\n* METHODOLOGY: 70\n# RELEVANCE: 60\nCONSISTENCY: 50\nNOTES: fine")
        scores, _ = bb._judge_response("quant", "q", "r", "claude", "key", None)
        self.assertEqual(scores["accuracy"], 80)
        self.assertEqual(scores["methodology"], 70)
        self.assertEqual(scores["relevance"], 60)


class RunBenchmarkTests(unittest.TestCase):
    """run_benchmark's orchestration logic -- number of calls made, weighted-score math, a
    failed candidate response scoring 0 across the board rather than crashing the whole run,
    and results sorted best-to-worst."""

    def setUp(self):
        self._orig_callers = dict(llm_engine.PROVIDER_CALLERS)
        self.addCleanup(lambda: llm_engine.PROVIDER_CALLERS.update(self._orig_callers))

    def test_every_candidate_answers_every_battery_question(self):
        call_count = {"n": 0}

        def _fake_caller(system_prompt, user_prompt, api_key, model):
            call_count["n"] += 1
            return "an answer"

        def _fake_judge(system_prompt, user_prompt, api_key, model):
            return "ACCURACY: 80\nMETHODOLOGY: 80\nRELEVANCE: 80\nCONSISTENCY: 80\nNOTES: fine"

        llm_engine.PROVIDER_CALLERS.update({"claude": _fake_caller, "gemini": _fake_judge})
        report = bb.run_benchmark(
            "quant", candidates=[("claude", "model-a")], api_keys={"claude": "key"}, judge_provider="gemini",
        )
        # 3 battery questions for "quant" -- one candidate answer call each, plus the judge
        # call happens through the same PROVIDER_CALLERS dict but a different key ("gemini"),
        # so call_count only reflects the candidate's own 3 answers.
        self.assertEqual(call_count["n"], 3)
        self.assertEqual(len(report["candidates"]), 1)
        self.assertEqual(len(report["candidates"][0]["per_question"]), 3)

    def test_weighted_score_reflects_the_rubric_weights(self):
        def _fake_caller(system_prompt, user_prompt, api_key, model):
            return "an answer"

        def _fake_judge(system_prompt, user_prompt, api_key, model):
            # quant weights: accuracy 30, methodology 25, relevance 25, consistency 20
            return "ACCURACY: 100\nMETHODOLOGY: 0\nRELEVANCE: 0\nCONSISTENCY: 0\nNOTES: n/a"

        llm_engine.PROVIDER_CALLERS.update({"claude": _fake_caller, "gemini": _fake_judge})
        report = bb.run_benchmark(
            "quant", candidates=[("claude", "model-a")], api_keys={"claude": "key"}, judge_provider="gemini",
        )
        # Every question scores 100*0.30 = 30 weighted, so the candidate's average is 30.0.
        self.assertEqual(report["candidates"][0]["score"], 30.0)

    def test_a_failed_candidate_call_scores_zero_instead_of_crashing(self):
        def _failing_caller(system_prompt, user_prompt, api_key, model):
            return "⚠️ Claude request failed: no API key"

        def _fake_judge(system_prompt, user_prompt, api_key, model):
            raise AssertionError("the judge should never be called on a failed response")

        llm_engine.PROVIDER_CALLERS.update({"claude": _failing_caller, "gemini": _fake_judge})
        report = bb.run_benchmark(
            "quant", candidates=[("claude", "model-a")], api_keys={"claude": "key"}, judge_provider="gemini",
        )
        candidate = report["candidates"][0]
        self.assertTrue(candidate["any_failed"])
        self.assertEqual(candidate["score"], 0.0)
        self.assertTrue(all(q["failed"] for q in candidate["per_question"]))

    def test_results_sorted_best_to_worst(self):
        def _caller_factory(text):
            return lambda system_prompt, user_prompt, api_key, model: text

        def _fake_judge_for(score):
            return lambda system_prompt, user_prompt, api_key, model: (
                f"ACCURACY: {score}\nMETHODOLOGY: {score}\nRELEVANCE: {score}\nCONSISTENCY: {score}\nNOTES: n/a"
            )

        # claude candidate gets judged high, openai candidate gets judged low -- route each
        # candidate's answer call and the shared judge call through distinct fake providers.
        llm_engine.PROVIDER_CALLERS.update({
            "claude": _caller_factory("high quality answer"),
            "openai": _caller_factory("low quality answer"),
            "gemini": lambda sp, up, ak, m: (
                _fake_judge_for(90)(sp, up, ak, m) if "high quality" in up else _fake_judge_for(20)(sp, up, ak, m)
            ),
        })
        report = bb.run_benchmark(
            "quant", candidates=[("openai", "model-b"), ("claude", "model-a")],
            api_keys={"claude": "key", "openai": "key"}, judge_provider="gemini",
        )
        self.assertEqual(report["candidates"][0]["provider"], "claude")
        self.assertEqual(report["candidates"][1]["provider"], "openai")

    def test_on_progress_callback_fires_once_per_question(self):
        progress_calls = []

        def _fake_caller(system_prompt, user_prompt, api_key, model):
            return "an answer"

        def _fake_judge(system_prompt, user_prompt, api_key, model):
            return "ACCURACY: 80\nMETHODOLOGY: 80\nRELEVANCE: 80\nCONSISTENCY: 80\nNOTES: fine"

        llm_engine.PROVIDER_CALLERS.update({"claude": _fake_caller, "gemini": _fake_judge})
        bb.run_benchmark(
            "quant", candidates=[("claude", "model-a")], api_keys={"claude": "key"},
            judge_provider="gemini", on_progress=progress_calls.append,
        )
        self.assertEqual(len(progress_calls), 3)  # 3 battery questions for "quant"


class SaveLoadReportTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_path = bb.RESULTS_PATH
        bb.RESULTS_PATH = Path(self._tmpdir) / "benchmark_results.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bb, "RESULTS_PATH", self._orig_path)

    def test_no_report_saved_returns_none(self):
        self.assertIsNone(bb.load_report("quant"))

    def test_save_and_load_round_trips(self):
        report = {"role": "quant", "candidates": [{"provider": "claude", "score": 90.0}]}
        bb.save_report("quant", report)
        self.assertEqual(bb.load_report("quant"), report)

    def test_saving_a_different_role_does_not_clobber_an_existing_one(self):
        bb.save_report("quant", {"role": "quant", "candidates": []})
        bb.save_report("beat", {"role": "beat", "candidates": []})
        self.assertIsNotNone(bb.load_report("quant"))
        self.assertIsNotNone(bb.load_report("beat"))

    def test_saving_the_same_role_again_overwrites_the_old_report(self):
        bb.save_report("quant", {"role": "quant", "candidates": [{"score": 50.0}]})
        bb.save_report("quant", {"role": "quant", "candidates": [{"score": 90.0}]})
        self.assertEqual(bb.load_report("quant")["candidates"][0]["score"], 90.0)


if __name__ == "__main__":
    unittest.main()
