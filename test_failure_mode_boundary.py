"""§14 (ARCHITECTURE_AUDIT Pass 10): failure modes, partial completion, fallbacks.

Every provider call in this app fails soft — a "⚠️ …" string, never a raised exception — so one
dead provider cannot take out the whole panel, and the deterministic board is untouched either
way. That is the section's strongest property and it was undefended.

  ENFORCEMENT.
  * Every provider caller returns a ⚠️ string rather than raising, for a missing key and for a
    thrown exception alike.
  * A failed chair is collected into `errors` and surfaced.
  * A failed chair's output never reaches the Moderator's verdict parser.
  * **R12**: a failed chair's error text no longer occupies the next chair's evidence slot. It
    is replaced by an explicit unavailability marker that also says absence is not evidence of
    absence — and the raw provider exception is not forwarded into another provider's prompt.

  CHARACTERIZATION — invert on repair, do not delete. Four distinct causes (provider down, bad
  key, quota/429, context overflow) collapse into one signal; there are no retries, no resume,
  and no bounded backoff; and a debate that fails completely writes nothing to the decision log.

No provider is called anywhere in this file.
"""

import inspect
import tempfile
import unittest
from pathlib import Path

import decision_log
import llm_engine
import pick_debate

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()

_FAILURE = "⚠️ Claude request failed: Connection reset by peer"


def _stub(response, captured=None, key=None):
    def _call(system_prompt, user_prompt, api_key=None, model=None):
        if captured is not None:
            captured[key] = user_prompt
        return response
    return _call


class EveryCallFailsSoftTests(unittest.TestCase):
    """One dead provider must not take out the panel, and must never raise."""

    def test_a_missing_key_returns_a_warning_string_rather_than_raising(self):
        for caller, marker in (
            (llm_engine._call_claude, "ANTHROPIC_API_KEY"),
            (llm_engine._call_gemini, "GEMINI_API_KEY"),
            (llm_engine._call_openai, "OPENAI_API_KEY"),
            (pick_debate._call_claude, "ANTHROPIC_API_KEY"),
        ):
            result = caller("system", "user", api_key="")
            self.assertTrue(result.startswith("⚠️"), caller.__module__ + "." + caller.__name__)
            self.assertIn(marker, result)

    def test_every_provider_caller_catches_broadly_rather_than_propagating(self):
        for module in (llm_engine, pick_debate):
            for name in ("_call_claude", "_call_gemini", "_call_openai"):
                source = inspect.getsource(getattr(module, name))
                self.assertIn("except Exception as exc", source, f"{module.__name__}.{name}")
                self.assertIn('return f"⚠️', source, f"{module.__name__}.{name}")

    def test_a_failed_chair_is_collected_and_surfaced(self):
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub(_FAILURE)
        try:
            result = llm_engine.run_debate(
                "CTX", "Q",
                role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
                api_keys={"claude": "k"},
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        self.assertEqual(len(result.errors), 4)
        self.assertTrue(all(e.startswith(("quant:", "beat:", "contrarian:", "moderator:")) for e in result.errors))
        self.assertIn("Debate finished with issues", _APP)

    def test_a_failed_moderator_never_reaches_the_verdict_parser(self):
        self.assertEqual(llm_engine.parse_moderator_verdict(_FAILURE), {})
        self.assertIn('if not moderator_text.startswith("⚠️") else {}', _APP)

    def test_the_deterministic_board_is_built_independently_of_any_ai_call(self):
        """§14: can an AI operation degrade while preserving deterministic CDME output?
        `debate_pick` receives an already-built snapshot; it cannot influence one."""
        signature = inspect.signature(pick_debate.debate_pick)
        self.assertEqual(list(signature.parameters)[0], "snapshot")
        source = inspect.getsource(pick_debate)
        for engine_call in ("compute_draft_board", "build_snapshot"):
            self.assertNotIn(engine_call, source)


class AFailedChairIsNotHandedOnAsEvidenceTests(unittest.TestCase):
    """R12. A missing thing must be represented as missing, never as a value."""

    def _contrarian_prompt(self, quant, beat):
        captured = {}
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["openai"] = _stub("out", captured, "prompt")
        try:
            llm_engine.ask_contrarian("CTX", "Q", quant, beat, provider="openai", api_key="k")
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        return captured["prompt"]

    def test_a_failed_upstream_report_is_replaced_by_an_explicit_unavailability_marker(self):
        prompt = self._contrarian_prompt(_FAILURE, "a real beat report")
        self.assertIn(llm_engine.UNAVAILABLE_REPORT, prompt)
        self.assertNotIn("Connection reset by peer", prompt)
        self.assertNotIn("⚠️", prompt)

    def test_a_real_report_passes_through_untouched(self):
        """Non-vacuity: the rewrite is scoped to failures, not applied to everything."""
        prompt = self._contrarian_prompt("a real quant report", "a real beat report")
        self.assertIn("a real quant report", prompt)
        self.assertIn("a real beat report", prompt)
        self.assertNotIn(llm_engine.UNAVAILABLE_REPORT, prompt)

    def test_the_marker_says_absence_is_not_evidence_of_absence(self):
        """§14 asks whether missing research is ever treated as negative evidence. A bare
        'unavailable' invites exactly that from a chair whose job is finding what others
        missed, so the marker says so explicitly."""
        self.assertIn("MISSING", llm_engine.UNAVAILABLE_REPORT)
        self.assertIn("never as a finding", llm_engine.UNAVAILABLE_REPORT)

    def test_the_raw_provider_exception_is_not_forwarded_to_another_provider(self):
        prompt = self._contrarian_prompt(_FAILURE, _FAILURE)
        self.assertNotIn("Connection reset", prompt)

    def test_the_failure_still_reaches_the_user_intact(self):
        """The rewrite is model-facing only: the real error is still on the result."""
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub(_FAILURE)
        try:
            result = llm_engine.run_debate(
                "CTX", "Q",
                role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
                api_keys={"claude": "k"},
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        self.assertIn("Connection reset by peer", " ".join(result.errors))
        self.assertEqual(result.quant, _FAILURE)

    def test_the_draft_room_chairs_get_the_same_treatment(self):
        source = inspect.getsource(pick_debate.debate_pick)
        self.assertIn("_report_for_handoff(strategist_report)", source)
        self.assertIn("_report_for_handoff(skeptic_report)", source)
        self.assertNotIn("--- STRATEGIST'S CASE ---\\n{strategist_report}", source)


class FailureTaxonomyIsCoarseTests(unittest.TestCase):
    """KNOWN GAPS — characterization. Invert when repaired; do not delete."""

    def test_four_distinct_causes_collapse_into_one_signal(self):
        """§14: does the system distinguish 'provider unavailable' from 'model produced invalid
        output' from 'evidence unavailable'? Provider-down, bad key, quota/429 and context
        overflow all arrive as the same `⚠️ <provider> request failed: <exc>` string, separable
        only by reading the exception text."""
        for module in (llm_engine, pick_debate):
            source = inspect.getsource(module)
            for marker in ("status_code", "RateLimitError", "AuthenticationError", "429"):
                self.assertNotIn(marker, source, f"{module.__name__} now classifies -- invert this test.")

    def test_there_are_no_retries_and_no_resume(self):
        combined = inspect.getsource(llm_engine) + inspect.getsource(pick_debate)
        for marker in ("retry", "backoff", "max_retries", "resume", "idempot"):
            self.assertNotIn(marker, combined.lower(), f"{marker} appeared -- invert this test.")

    def test_a_completely_failed_debate_writes_nothing_to_the_decision_log(self):
        """§14: is complete failure state recorded? Only in the session-scoped activity log
        (§10.1), which does not survive a restart."""
        with tempfile.TemporaryDirectory() as tmp:
            saved = decision_log.DECISIONS_DIR
            decision_log.DECISIONS_DIR = Path(tmp)
            try:
                verdict = llm_engine.parse_moderator_verdict(_FAILURE)
                decision_log.log_decision("L1", "Q", verdict, _FAILURE)
                self.assertEqual(decision_log.load_decisions("L1"), [])
                # Non-vacuity: a real verdict does get written.
                decision_log.log_decision("L1", "Q", {"recommendation": "HOLD"}, "prose")
                self.assertEqual(len(decision_log.load_decisions("L1")), 1)
            finally:
                decision_log.DECISIONS_DIR = saved

    def test_no_fallback_provider_is_attempted_when_one_fails(self):
        source = inspect.getsource(llm_engine.run_debate)
        self.assertNotIn("fallback", source.lower())
        # Each role calls exactly the provider it was assigned, once.
        self.assertEqual(source.count("PROVIDER_CALLERS"), 0)
        self.assertIn("_key(", source)


if __name__ == "__main__":
    unittest.main()
