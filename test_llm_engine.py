import time
import unittest

import llm_engine


class RunDebateParallelExecutionTests(unittest.TestCase):
    """Quant and Beat don't read each other's output (only Contrarian and Moderator have a
    real dependency on prior reports), so run_debate runs them concurrently instead of paying
    for two sequential network round-trips -- see run_debate's own comment for the reasoning.
    This proves it actually happens, not just that the code compiles."""

    def setUp(self):
        self._orig_callers = dict(llm_engine.PROVIDER_CALLERS)
        self.addCleanup(lambda: llm_engine.PROVIDER_CALLERS.update(self._orig_callers))

    def test_quant_and_beat_run_concurrently_not_sequentially(self):
        delay = 0.15

        def _caller(system_prompt, user_prompt, api_key, model):
            if system_prompt == llm_engine.QUANT_SYSTEM_PROMPT:
                time.sleep(delay)
                return "quant answer"
            if system_prompt == llm_engine.BEAT_SYSTEM_PROMPT:
                time.sleep(delay)
                return "beat answer"
            return "fast answer"  # contrarian/moderator -- not what this test is checking

        llm_engine.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})

        role_providers = {"quant": "claude", "beat": "gemini", "contrarian": "openai", "moderator": "claude"}
        api_keys = {"claude": "x", "gemini": "x", "openai": "x"}

        started = time.monotonic()
        result = llm_engine.run_debate("context", "question", role_providers=role_providers, api_keys=api_keys)
        elapsed = time.monotonic() - started

        self.assertEqual(result.quant, "quant answer")
        self.assertEqual(result.beat, "beat answer")
        # Sequential would need at least 2*delay just for quant+beat; concurrent finishes in
        # roughly one delay's worth (plus the near-instant contrarian/moderator calls after).
        self.assertLess(elapsed, delay * 1.8)

    def test_contrarian_and_moderator_still_see_the_quant_and_beat_reports(self):
        # Correctness check alongside the timing one above -- parallelizing quant/beat must
        # not break contrarian/moderator's real dependency on their actual output.
        def _caller(system_prompt, user_prompt, api_key, model):
            if system_prompt == llm_engine.QUANT_SYSTEM_PROMPT:
                return "QUANT_MARKER"
            if system_prompt == llm_engine.BEAT_SYSTEM_PROMPT:
                return "BEAT_MARKER"
            if "QUANT_MARKER" in user_prompt and "BEAT_MARKER" in user_prompt:
                return "saw both reports"
            return "MISSING A REPORT"

        llm_engine.PROVIDER_CALLERS.update({"claude": _caller, "gemini": _caller, "openai": _caller})
        role_providers = {"quant": "claude", "beat": "gemini", "contrarian": "openai", "moderator": "claude"}
        api_keys = {"claude": "x", "gemini": "x", "openai": "x"}

        result = llm_engine.run_debate("context", "question", role_providers=role_providers, api_keys=api_keys)
        self.assertEqual(result.contrarian, "saw both reports")
        self.assertEqual(result.moderator, "saw both reports")


if __name__ == "__main__":
    unittest.main()
