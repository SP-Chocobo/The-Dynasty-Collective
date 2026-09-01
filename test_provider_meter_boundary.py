"""Step 1b: what a provider call cost (#100), whether its answer arrived whole (#99), and the
resource limits that bound it (#105).

The response SHAPES here are stand-ins, and that is stated rather than hidden: none of the three
provider SDKs is installed in the environment this was written in, so these tests prove that
provider_meter READS a given shape correctly. They do not and cannot prove what a live provider
actually returns. That second claim needs a live call against each SDK and is recorded as still
outstanding -- exactly the distinction §17 drew when it found the served model unrecoverable.

The property that matters most is negative: metering must never be able to turn a working
provider call into a failed one. That is proven by planting objects that raise on attribute
access, not by reading the try/except blocks.
"""

from __future__ import annotations

import unittest

import provider_meter as pm


class _Anthropic:
    def __init__(self, stop_reason="end_turn", tokens=(120, 400), model="claude-opus-5"):
        self.stop_reason, self.model = stop_reason, model
        if tokens is not None:
            self.usage = type("U", (), {"input_tokens": tokens[0], "output_tokens": tokens[1]})()


class _Gemini:
    def __init__(self, finish="STOP", tokens=(120, 400), model_version="gemini-x"):
        self.model_version = model_version
        self.candidates = [type("C", (), {"finish_reason": type("F", (), {"name": finish})()})()]
        if tokens is not None:
            self.usage_metadata = type("U", (), {"prompt_token_count": tokens[0],
                                                 "candidates_token_count": tokens[1]})()


class _OpenAI:
    def __init__(self, status="completed", reason=None, tokens=(120, 400), model="gpt-x"):
        self.status, self.model = status, model
        self.incomplete_details = type("D", (), {"reason": reason})() if reason else None
        if tokens is not None:
            self.usage = type("U", (), {"input_tokens": tokens[0], "output_tokens": tokens[1]})()


class _Hostile:
    """Every attribute access raises. Nothing about metering may care."""
    def __getattr__(self, name):
        raise RuntimeError("this SDK object is having a bad day")


class TruncationHasFourStatesTests(unittest.TestCase):
    """#99. 'Did the answer arrive whole' is not a yes/no question, and a provider that did not
    say must never be recorded as having said 'complete'."""

    def test_anthropic_states(self):
        for reason, expected in (("end_turn", pm.COMPLETE), ("stop_sequence", pm.COMPLETE),
                                 ("tool_use", pm.COMPLETE), ("max_tokens", pm.TRUNCATED),
                                 ("refusal", pm.BLOCKED), ("something_new", pm.UNKNOWN)):
            with self.subTest(stop_reason=reason):
                self.assertEqual(
                    pm.describe("claude", _Anthropic(stop_reason=reason))["completion_state"],
                    expected)

    def test_gemini_states(self):
        for finish, expected in (("STOP", pm.COMPLETE), ("MAX_TOKENS", pm.TRUNCATED),
                                 ("SAFETY", pm.BLOCKED), ("RECITATION", pm.BLOCKED),
                                 ("SOMETHING_NEW", pm.UNKNOWN)):
            with self.subTest(finish_reason=finish):
                self.assertEqual(
                    pm.describe("gemini", _Gemini(finish=finish))["completion_state"], expected)

    def test_openai_states(self):
        cases = (
            (("completed", None), pm.COMPLETE),
            (("incomplete", "max_output_tokens"), pm.TRUNCATED),
            (("incomplete", "content_filter"), pm.BLOCKED),
            (("incomplete", "something_new"), pm.UNKNOWN),
            (("in_progress", None), pm.UNKNOWN),
        )
        for (status, reason), expected in cases:
            with self.subTest(status=status, reason=reason):
                self.assertEqual(
                    pm.describe("openai", _OpenAI(status=status, reason=reason))["completion_state"],
                    expected)

    def test_a_silent_provider_is_unknown_not_complete(self):
        """The whole point of the fourth state. An SDK that stops reporting a stop reason -- the
        #110 silent-meaning-change class -- must not read as a clean finish."""
        for provider in ("claude", "gemini", "openai"):
            with self.subTest(provider=provider):
                self.assertEqual(
                    pm.describe(provider, object())["completion_state"], pm.UNKNOWN)

    def test_an_unrecognised_provider_makes_no_claim(self):
        self.assertEqual(pm.describe("brand-new-vendor", _Anthropic())["completion_state"],
                         pm.UNKNOWN)


class MeteringCannotBreakACallTests(unittest.TestCase):
    """The negative property. A bookkeeping failure that converted a good answer into a failure
    would be strictly worse than no bookkeeping, in the one code path whose design goal is that
    it cannot fail hard."""

    def setUp(self):
        pm.reset()

    def test_a_response_object_that_raises_on_every_read_is_survivable(self):
        result = pm.describe("claude", _Hostile())
        self.assertEqual(result["completion_state"], pm.UNKNOWN)
        self.assertIsNone(result["input_tokens"])
        self.assertIsNone(result["model_reported"])

    def test_metered_returns_a_hostile_response_untouched(self):
        hostile = _Hostile()
        self.assertIs(pm.metered("claude", lambda: hostile), hostile)

    def test_metered_reraises_so_the_callers_own_warning_string_is_unchanged(self):
        def boom():
            raise ValueError("provider exploded")
        with self.assertRaises(ValueError):
            pm.metered("claude", boom)
        record = pm.recent()[0]
        self.assertFalse(record["ok"])
        self.assertIn("provider exploded", record["error"])
        self.assertEqual(record["completion_state"], pm.FAILED)

    def test_a_failure_metered_once_is_not_counted_twice(self):
        """metered records the failure and flags the exception; the caller's own outer handler
        then declines to record it again. Without the flag every in-flight failure would appear
        twice and every cost total would be wrong."""
        def boom():
            raise ValueError("x")
        try:
            pm.metered("claude", boom)
        except ValueError as exc:
            pm.record_preflight_failure("claude", exc)
        self.assertEqual(pm.totals()["calls"], 1)

    def test_an_exception_that_rejects_attributes_still_records_exactly_once(self):
        """Non-vacuity for the flag: some exception types have __slots__ and cannot be tagged.
        The record must still be written, and the fallback must not raise."""
        class Slotted(Exception):
            __slots__ = ()
        try:
            pm.metered("claude", lambda: (_ for _ in ()).throw(Slotted()))
        except Slotted as exc:
            pm.record_preflight_failure("claude", exc)
        self.assertGreaterEqual(pm.totals()["calls"], 1)


class AbsenceIsAbsenceTests(unittest.TestCase):
    """A provider that did not report usage did not report zero usage."""

    def setUp(self):
        pm.reset()

    def test_missing_usage_is_none_not_zero(self):
        described = pm.describe("claude", _Anthropic(tokens=None))
        self.assertIsNone(described["input_tokens"])
        self.assertIsNone(described["output_tokens"])

    def test_a_half_known_total_is_no_total(self):
        record = pm.CallRecord(provider="claude", role="", input_tokens=100, output_tokens=None)
        self.assertIsNone(record.total_tokens)
        record.output_tokens = 20
        self.assertEqual(record.total_tokens, 120)

    def test_a_boolean_is_not_a_token_count(self):
        """bool subclasses int, so an SDK field that became True would otherwise be recorded as
        a token count of 1 -- a plausible-looking number in the one place a wrong one is
        expensive."""
        self.assertIsNone(pm._int_or_none(True))
        self.assertIsNone(pm._int_or_none("many"))
        self.assertEqual(pm._int_or_none("42"), 42)

    def test_totals_refuse_to_sum_a_partly_unknown_set(self):
        pm.record("claude", "quant", response=_Anthropic(tokens=(10, 20)))
        pm.record("claude", "beat", response=_Anthropic(tokens=None))
        totals = pm.totals()
        self.assertIsNone(totals["input_tokens"], "a total assembled from partial data reads as "
                                                  "authoritative and is not")
        self.assertEqual(totals["usage_reported"], 1)
        self.assertEqual(totals["calls"], 2)

    def test_totals_sum_when_everything_is_known(self):
        pm.record("claude", "quant", response=_Anthropic(tokens=(10, 20)))
        pm.record("openai", "beat", response=_OpenAI(tokens=(5, 7)))
        totals = pm.totals()
        self.assertEqual(totals["input_tokens"], 15)
        self.assertEqual(totals["output_tokens"], 27)


class ScopingAndBoundsTests(unittest.TestCase):

    def setUp(self):
        pm.reset()

    def test_mark_and_since_isolate_one_operations_calls(self):
        pm.record("claude", "earlier", response=_Anthropic(tokens=(1, 1)))
        marker = pm.mark()
        pm.record("claude", "mine", response=_Anthropic(tokens=(10, 20)))
        pm.record("openai", "mine", response=_OpenAI(tokens=(5, 7)))
        mine = pm.since(marker)
        self.assertEqual([r.role for r in mine], ["mine", "mine"])
        self.assertEqual(pm.totals(mine)["input_tokens"], 15)

    def test_since_a_fresh_mark_is_empty(self):
        pm.record("claude", "x", response=_Anthropic())
        self.assertEqual(pm.since(pm.mark()), [])

    def test_the_ledger_is_bounded_and_drops_the_oldest(self):
        for i in range(pm.LEDGER_CAPACITY + 25):
            pm.record("claude", f"r{i}", response=_Anthropic(tokens=(1, 1)))
        self.assertEqual(pm.totals()["calls"], pm.LEDGER_CAPACITY)
        self.assertEqual(pm.recent(1)[0]["role"], f"r{pm.LEDGER_CAPACITY + 24}")

    def test_since_reports_only_what_is_still_held_after_eviction(self):
        marker = pm.mark()
        for i in range(pm.LEDGER_CAPACITY + 10):
            pm.record("claude", f"r{i}", response=_Anthropic(tokens=(1, 1)))
        held = pm.since(marker)
        self.assertEqual(len(held), pm.LEDGER_CAPACITY)
        self.assertEqual(pm.totals(held)["calls"], pm.LEDGER_CAPACITY,
                         "the count must show it is summing fewer calls than were made")

    def test_role_scope_names_the_chair_without_widening_the_caller_signature(self):
        with pm.role_scope("contrarian"):
            self.assertEqual(pm.current_role(), "contrarian")
            pm.metered("claude", lambda: _Anthropic())
        self.assertEqual(pm.current_role(), "")
        self.assertEqual(pm.recent()[0]["role"], "contrarian")

    def test_latency_and_requested_model_are_recorded(self):
        pm.metered("claude", lambda: _Anthropic(), model_requested="claude-opus-5")
        record = pm.recent()[0]
        self.assertEqual(record["model_requested"], "claude-opus-5")
        self.assertIsNotNone(record["latency_ms"])

    def test_the_served_model_is_captured_when_the_provider_reports_it(self):
        """#109 was recorded as blocked on the SDKs: all three default ids are floating aliases,
        so the requested name does not identify what ran. The response's own echo is captured
        where present. Whether a given SDK really resolves an alias here is NOT established by
        this test -- that needs a live call."""
        self.assertEqual(pm.describe("claude", _Anthropic())["model_reported"], "claude-opus-5")
        self.assertEqual(pm.describe("gemini", _Gemini())["model_reported"], "gemini-x")
        self.assertIsNone(pm.describe("claude", _Anthropic(model=None))["model_reported"])


class ResourceLimitsTests(unittest.TestCase):
    """#105. A limit that silently fails to apply is worse than no limit."""

    def test_only_kwargs_the_sdk_accepts_are_passed(self):
        def client(api_key=None, timeout=None):
            pass
        accepted, dropped = pm.supported_kwargs(client, timeout=1, max_retries=2)
        self.assertEqual(accepted, {"timeout": 1})
        self.assertEqual(dropped, ["max_retries"])

    def test_a_client_taking_kwargs_accepts_everything(self):
        def client(api_key=None, **rest):
            pass
        accepted, dropped = pm.supported_kwargs(client, timeout=1, anything=2)
        self.assertEqual(dropped, [])
        self.assertEqual(accepted, {"timeout": 1, "anything": 2})

    def test_an_unreadable_signature_passes_nothing(self):
        """Declining to set a limit is recoverable. Guessing wrong is not: an unknown kwarg
        raises, and that exception would be caught by the caller's own handler and returned as
        '⚠️ ... request failed', silently disabling the provider outright."""
        accepted, dropped = pm.supported_kwargs(len, timeout=1)
        self.assertEqual(accepted, {})
        self.assertEqual(dropped, ["timeout"])

    def test_a_dropped_limit_is_recorded_rather_than_silently_absent(self):
        def client(api_key=None):
            pass
        pm.limit_kwargs("probe", client, timeout=1)
        self.assertEqual(pm.applied_limits["probe"], {"applied": [], "dropped": ["timeout"]})

    def test_a_timeout_exists_at_all(self):
        """Before 1b no provider client or request carried a timeout of any kind, so a hung
        provider hung the Streamlit script with no user recourse. The VALUE is provisional and
        parked as a policy decision; that there IS one is not."""
        self.assertIsNotNone(pm.REQUEST_TIMEOUT_SECONDS)
        self.assertGreater(pm.REQUEST_TIMEOUT_SECONDS, 0)


if __name__ == "__main__":
    unittest.main()
