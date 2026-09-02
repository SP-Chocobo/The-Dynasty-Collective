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
import provider_meter

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
        chair_errors = [e for e in result.errors
                        if e.startswith(("quant:", "beat:", "contrarian:", "moderator:"))]
        self.assertEqual(len(chair_errors), 4)
        # The fifth entry is #104's all-upstream-failed annotation, which is not a chair error
        # and deliberately carries no chair prefix -- it is about the verdict, not about a chair.
        # See AllUpstreamFailedTests.
        self.assertEqual(len(result.errors), 5)
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

    def test_the_marker_does_not_assert_why_the_report_is_missing(self):
        """§22 (R17). Every provider caller wraps its whole request in `except Exception`, which
        fires alike for a missing key (never executed), a connection error (never executed), a
        read timeout after the provider generated and billed a response (executed, not
        received), and a parse error on a response that did arrive. The marker therefore cannot
        say the call "did not complete" or that "no analysis was produced" -- it said both until
        §22 caught it, and in the timeout case both are false.

        The rule is the one #89 set for the alias branch and §6 R1 applied to "validated": a
        field may not claim a certainty its writing path cannot establish. What is known is that
        no usable report reached this chair, and the marker now says only that."""
        marker = llm_engine.UNAVAILABLE_REPORT.lower()
        for overclaim in ("did not complete", "no analysis was produced", "never ran,",
                          "failed to run", "was not executed"):
            with self.subTest(phrase=overclaim):
                # "never ran," with the comma is the enumeration in the honest wording; the bare
                # assertions are what must not appear.
                if overclaim == "never ran,":
                    self.assertIn(overclaim, marker, "the three-way ambiguity must be named")
                    continue
                self.assertNotIn(overclaim, marker)
        self.assertIn("is not known here", marker)

    def test_every_provider_caller_catches_a_class_that_spans_all_three_outcomes(self):
        """Non-vacuity for the test above: the marker's caution is only warranted because the
        catch really is that broad. If a caller ever narrowed to a pre-flight error class, the
        ambiguity would shrink and the wording should be revisited rather than kept."""
        import ast
        source = Path(__file__).with_name("llm_engine.py").read_text()
        tree = ast.parse(source)
        for name in ("_call_claude", "_call_gemini", "_call_openai"):
            fn = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == name)
            handlers = [h for n in ast.walk(fn) if isinstance(n, ast.Try) for h in n.handlers]
            self.assertTrue(
                any(isinstance(h.type, ast.Name) and h.type.id == "Exception" for h in handlers),
                f"{name} no longer catches bare Exception -- revisit UNAVAILABLE_REPORT's wording",
            )

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
        """PARTIALLY INVERTED (1b). The scan over these two modules still holds and still
        matters. What has been corrected is the conclusion drawn from it: this proves the REPO
        implements no retry or resume, which is not the same as proving none HAPPENS. The
        provider SDKs carry their own retry defaults that this app never set and never measured,
        so the running system's behaviour was never established by this test. See
        test_cost_envelope_boundary for the now-explicit, deliberately-off knob."""
        combined = inspect.getsource(llm_engine) + inspect.getsource(pick_debate)
        for marker in ("retry", "backoff", "max_retries", "resume", "idempot"):
            self.assertNotIn(marker, combined.lower(), f"{marker} appeared -- invert this test.")

    def test_a_never_attempted_call_is_no_longer_indistinguishable_from_a_failed_one(self):
        """PARTIALLY INVERTS the coarse-taxonomy test above (1b/#99/#100). Four causes still
        collapse into one ⚠️ STRING, but they no longer collapse in the RECORD: a call that
        never left this machine -- no key, or the SDK absent -- is now recorded as
        not_attempted with its own reason, separately from a request that was made and failed.

        This is the half of §14's collapse that can be separated with certainty. §22's
        unavailability marker still has to stay agnostic about a call that DID run."""
        provider_meter.reset()
        llm_engine._call_claude("system", "user", api_key="")          # never attempted: no key
        records = provider_meter.recent()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["completion_state"], provider_meter.NOT_ATTEMPTED)
        self.assertEqual(records[0]["completion_detail"], "api_key_missing")
        self.assertIsNone(records[0]["input_tokens"], "a call that never ran has no token cost")

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

    def test_the_panel_degrades_unconditionally_and_never_aborts(self):
        """#104, RESOLVED -- and this test kept, with the half that was a complaint removed.

        The measurement stands unchanged: across all eight failure combinations of the three
        upstream chairs the call count is 4 every time, the Moderator always runs, and it always
        produces a real verdict. What changed is the status of that behaviour. It used to be
        what merely fell out of calling four chairs in sequence -- this test said so, and said
        it "was never chosen". It is chosen now, as llm_engine.DEGRADE_NEVER_ABORT, with the
        reasoning written where the policy lives.

        The edge this test named is now handled rather than merely noted: with ALL THREE
        upstream chairs failed, the Moderator still synthesizes a verdict from three
        unavailability markers, and run_debate now appends an error saying exactly that. Its
        coverage lives in AllUpstreamFailedTests below; what remains here is the floor check.

        INVERT THIS TEST if a floor is ever introduced. Do not delete it."""
        import itertools
        roles = ("quant", "beat", "contrarian", "moderator")

        def run(failing):
            calls = []
            def make(role):
                def _call(system_prompt, user_prompt, api_key=None, model=None):
                    calls.append(role)
                    return _FAILURE if role in failing else f"{role} real report"
                return _call
            original = dict(llm_engine.PROVIDER_CALLERS)
            llm_engine.PROVIDER_CALLERS.update({r: make(r) for r in roles})
            try:
                result = llm_engine.run_debate(
                    "CTX", "Q", role_providers={r: r for r in roles},
                    api_keys={r: "k" for r in roles})
            finally:
                llm_engine.PROVIDER_CALLERS.clear()
                llm_engine.PROVIDER_CALLERS.update(original)
            return result, calls

        for count in range(4):
            for combo in itertools.combinations(("quant", "beat", "contrarian"), count):
                with self.subTest(failing=combo):
                    result, calls = run(set(combo))
                    self.assertEqual(len(calls), 4, "every chair is called regardless")
                    self.assertIn("moderator", calls, "the moderator always runs")
                    self.assertFalse(result.moderator.startswith("⚠️"))
                    # One error per failed chair, plus the all-upstream-failed annotation in the
                    # one combination that earns it (see AllUpstreamFailedTests).
                    expected = len(combo) + (1 if len(combo) == 3 else 0)
                    self.assertEqual(len(result.errors), expected)

        self.assertIs(llm_engine.DEGRADE_NEVER_ABORT, True,
                      "the policy constant is the thing a floor would have to flip")
        for module in (llm_engine, pick_debate):
            for lineno, line in enumerate(inspect.getsource(module).splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#") or "DEGRADE_NEVER_ABORT" in stripped:
                    continue  # the policy's own name and its written reasoning
                for threshold_word in ("abort", "quorum", "min_chairs"):
                    self.assertNotIn(threshold_word, stripped.lower(),
                                     f"{module.__name__}:{lineno} -- {threshold_word} in executable "
                                     f"code means a floor exists; invert this test.")

    def test_no_fallback_provider_is_attempted_when_one_fails(self):
        source = inspect.getsource(llm_engine.run_debate)
        self.assertNotIn("fallback", source.lower())
        # Each role calls exactly the provider it was assigned, once.
        self.assertEqual(source.count("PROVIDER_CALLERS"), 0)
        self.assertIn("_key(", source)


class _FakeAnthropicResponse:
    """The one field provider_meter._anthropic_completion reads to call a report a fragment.

    A stand-in, and the tests below say so: they prove run_debate reads the LEDGER correctly,
    not that a live Anthropic call sets stop_reason this way. That second claim needs a live
    call and is recorded as still unverified (#120)."""

    def __init__(self, stop_reason):
        self.stop_reason = stop_reason
        self.usage = None
        self.model = "stand-in"


class AllUpstreamFailedTests(unittest.TestCase):
    """#104: the panel degrades rather than aborting, and says what the degraded verdict rests on.

    DEGRADE_NEVER_ABORT keeps every chair's failure from stopping the panel. Its one dangerous
    case is a Moderator verdict synthesized from three unavailability markers and nothing else --
    which reads exactly like a verdict resting on three real reports. Under the standing absence
    ruling the answer is to annotate rather than suppress, and to name a consumer that reads the
    annotation. The consumer is DebateResult.errors, which app.py already renders.
    """

    ROLES = ("quant", "beat", "contrarian", "moderator")
    _MARKER = "resting on NO evidence"

    def _run(self, failing, *, truncating=()):
        def make(role):
            def _call(system_prompt, user_prompt, api_key=None, model=None):
                if role in truncating:
                    # Recorded under whatever role scope the caller opened -- which is the point
                    # of the assertions below, so this deliberately does NOT pass `role`.
                    provider_meter.record(
                        "claude", provider_meter.current_role(),
                        response=_FakeAnthropicResponse("max_tokens"))
                return _FAILURE if role in failing else f"{role} real report"
            return _call

        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS.update({r: make(r) for r in self.ROLES})
        try:
            return llm_engine.run_debate(
                "CTX", "Q", role_providers={r: r for r in self.ROLES},
                api_keys={r: "k" for r in self.ROLES})
        finally:
            llm_engine.PROVIDER_CALLERS.clear()
            llm_engine.PROVIDER_CALLERS.update(original)

    def test_a_verdict_built_from_three_unavailability_markers_says_so(self):
        result = self._run({"quant", "beat", "contrarian"})
        self.assertFalse(result.moderator.startswith("⚠️"),
                         "precondition: the moderator still produced a verdict")
        annotations = [e for e in result.errors if self._MARKER in e]
        self.assertEqual(len(annotations), 1, result.errors)
        # The wording has to survive: a reader who sees only the three chair errors can still
        # read the verdict as a fourth opinion that happens to be the only one that arrived.
        self.assertIn("every upstream chair failed", annotations[0])

    def test_the_annotation_does_not_fire_while_any_upstream_chair_reported(self):
        """Non-vacuity in the direction that matters. An annotation that fires on a partial
        panel would train the reader to ignore it, which is the same end state as not having it."""
        import itertools
        for count in range(3):
            for combo in itertools.combinations(("quant", "beat", "contrarian"), count):
                with self.subTest(failing=combo):
                    result = self._run(set(combo))
                    self.assertEqual([e for e in result.errors if self._MARKER in e], [])

    def test_a_failed_moderator_alone_does_not_trigger_it(self):
        """The claim is about what the VERDICT rests on. With three real reports in hand and only
        the Moderator down, there is no verdict to qualify -- just a chair that failed."""
        result = self._run({"moderator"})
        self.assertEqual([e for e in result.errors if self._MARKER in e], [])
        self.assertEqual(len(result.errors), 1)

    def test_a_truncated_chair_reaches_the_human_through_errors_not_through_prose(self):
        """#99's other half. The report text is annotated in place by annotate_if_incomplete;
        this is the ledger-side copy, so the human sees a fragment named as a fragment even if
        they never scroll to the end of the report."""
        result = self._run(set(), truncating={"contrarian"})
        cut_off = [e for e in result.errors if "cut off at the provider's output cap" in e]
        self.assertEqual(len(cut_off), 1, result.errors)
        self.assertTrue(cut_off[0].startswith("contrarian:"), cut_off[0])

    def test_every_chair_scopes_its_own_ledger_records_including_the_threaded_two(self):
        """The regression this protects: quant and beat run on a ThreadPoolExecutor worker, and
        a worker thread starts with a FRESH contextvars Context. A role scope opened around
        executor.submit in the calling thread would silently not reach them, and both would
        record under the default role -- leaving the truncation attribution above able to name
        only contrarian and moderator, with no test failing."""
        for role in self.ROLES:
            with self.subTest(role=role):
                marker = provider_meter.mark()
                self._run(set(), truncating={role})
                roles = [r.role for r in provider_meter.since(marker)]
                self.assertEqual(roles, [role], f"{role} recorded under {roles}")

    def test_the_policy_is_stated_where_it_is_enforced(self):
        """A constant nothing reads is documentation, so this pins the pair: the policy exists as
        a value, and the two obligations it names are both discharged in run_debate."""
        self.assertIs(llm_engine.DEGRADE_NEVER_ABORT, True)
        source = inspect.getsource(llm_engine.run_debate)
        self.assertIn("DEGRADE_NEVER_", source, "run_debate points back at the policy it enforces")
        self.assertIn("result.errors.append", source)


if __name__ == "__main__":
    unittest.main()
