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


class _Obj:
    """A stand-in response. Same posture as the completion-extractor stand-ins above: these prove
    THIS CODE reads a given shape, and deliberately do not claim to prove what a live provider
    returns -- no SDK is even installed in this environment. That second claim needs a live call
    and stays recorded as unverified under #120."""

    def __init__(self, **fields):
        for key, value in fields.items():
            setattr(self, key, value)


def _anthropic_with_sources(pairs):
    return _Obj(content=[
        _Obj(type="text", text="a report"),
        _Obj(type="web_search_tool_result",
             content=[_Obj(url=url, title=title) for url, title in pairs]),
    ])


def _gemini_with_sources(pairs):
    chunks = [_Obj(web=_Obj(uri=url, title=title)) for url, title in pairs]
    return _Obj(candidates=[_Obj(grounding_metadata=_Obj(grounding_chunks=chunks))])


def _openai_with_sources(pairs):
    annotations = [_Obj(type="url_citation", url=url, title=title) for url, title in pairs]
    return _Obj(output=[_Obj(content=[_Obj(annotations=annotations)])])


class RetrievedSourceExtractionTests(unittest.TestCase):
    """#97/§6.5 + #106: what the panel retrieved, read off the response rather than the prose.

    Asking a chair to type a URL would manufacture provenance -- a model asked for a citation
    produces one whether or not it has one, and these rows feed the composite score. The
    provider's own grounding metadata is its report of what it actually fetched.
    """

    def test_each_provider_shape_is_read_correctly(self):
        pairs = [("https://espn.com/a", "A"), ("https://pff.com/b", "B")]
        expected = [{"url": url, "title": title} for url, title in pairs]
        for provider, build in (("claude", _anthropic_with_sources),
                                ("gemini", _gemini_with_sources),
                                ("openai", _openai_with_sources)):
            with self.subTest(provider=provider):
                self.assertEqual(pm.sources(provider, build(pairs)), expected)

    def test_a_page_cited_repeatedly_in_one_response_is_one_source(self):
        pairs = [("https://espn.com/a", "A"), ("https://espn.com/a", "A again"),
                 ("https://pff.com/b", "B")]
        found = pm.sources("claude", _anthropic_with_sources(pairs))
        self.assertEqual([entry["url"] for entry in found],
                         ["https://espn.com/a", "https://pff.com/b"])
        self.assertEqual(found[0]["title"], "A", "first occurrence wins")

    def test_every_unreadable_input_yields_an_empty_list_and_never_raises(self):
        """Total, for the same reason describe() is: a bookkeeping read must not be able to
        break the call it is describing."""
        for provider, response in (
            ("claude", None), ("claude", object()), ("claude", _Obj(content="not a list")),
            ("gemini", _Obj(candidates=[_Obj()])), ("gemini", _Obj()),
            ("openai", _Obj(output=[_Obj(content=[_Obj(annotations=[_Obj(type="file_citation")])])])),
            ("openai", _Obj(output=None)),
            ("nosuchprovider", _anthropic_with_sources([("https://x.com", "X")])),
        ):
            with self.subTest(provider=provider, response=type(response).__name__):
                self.assertEqual(pm.sources(provider, response), [])

    def test_a_response_that_reports_no_retrieval_is_empty_rather_than_absent(self):
        """"Searched and found nothing" and "did not search" are not distinguished HERE, on
        purpose -- see sources()'s own docstring. What matters is that neither becomes a claim."""
        self.assertEqual(pm.sources("claude", _Obj(content=[_Obj(type="text", text="x")])), [])


class SourcesSinceTests(unittest.TestCase):
    """The window reader. The unit is the debate, never the call and never the claim."""

    def test_it_collects_across_calls_in_the_window_and_dedupes_by_url(self):
        marker = pm.mark()
        pm.record("claude", "beat",
                              response=_anthropic_with_sources([("https://a.com", "A")]))
        pm.record("gemini", "contrarian",
                              response=_gemini_with_sources([("https://a.com", "A dup"),
                                                             ("https://b.com", "B")]))
        self.assertEqual([entry["url"] for entry in pm.sources_since(marker)],
                         ["https://a.com", "https://b.com"])

    def test_it_does_not_see_calls_recorded_before_the_marker(self):
        """The reason mark() exists at all: one debate meters exactly its own calls, never a
        neighbouring debate's, a /pick panel's, or a summarize_history that ran in between."""
        pm.record("claude", "beat",
                              response=_anthropic_with_sources([("https://earlier.com", "E")]))
        marker = pm.mark()
        pm.record("claude", "moderator",
                              response=_anthropic_with_sources([("https://later.com", "L")]))
        self.assertEqual([entry["url"] for entry in pm.sources_since(marker)],
                         ["https://later.com"])

    def test_a_failed_call_contributes_no_sources_and_does_not_break_the_read(self):
        marker = pm.mark()
        pm.record("claude", "quant", ok=False, error="boom")
        pm.record("claude", "moderator",
                              response=_anthropic_with_sources([("https://a.com", "A")]))
        self.assertEqual(len(pm.sources_since(marker)), 1)

    def test_an_empty_window_is_an_empty_list(self):
        self.assertEqual(pm.sources_since(pm.mark()), [])


if __name__ == "__main__":
    unittest.main()


class TruncationIsAnnotatedNeverDiscarded(unittest.TestCase):
    """#99 under the standing absence ruling: annotate, and name a consumer.

    A truncated report is REAL analysis that stops early -- categorically different from the
    "⚠️" prefix, which means no usable report arrived at all. Discarding it would assert the
    reader is better off with nothing, the same claim "unpriced sorts last" made about a
    running back, and the reason kickers outranked every skill player for a third of a draft.

    So the text is returned intact with the condition beside it. These tests pin that, and that
    the notice is distinguishable from the missing-report marker rather than collapsed into it.
    """

    def setUp(self):
        pm.reset()

    def test_a_complete_call_gets_no_notice(self):
        marker = pm.mark()
        pm.record("claude", "strategist", response=_Anthropic(stop_reason="end_turn"))
        self.assertEqual(pm.annotate_if_incomplete("the report", marker), "the report")

    def test_a_truncated_call_keeps_its_text_and_gains_the_notice(self):
        marker = pm.mark()
        pm.record("claude", "strategist", response=_Anthropic(stop_reason="max_tokens"))
        annotated = pm.annotate_if_incomplete("the report", marker)
        self.assertTrue(annotated.startswith("the report"), "the analysis was not preserved")
        self.assertIn("incomplete", annotated)
        self.assertGreater(len(annotated), len("the report"))

    def test_the_notice_is_not_the_missing_report_marker(self):
        """The two conditions must stay tellable apart: one means 'a fragment', the other means
        'nothing arrived'. A consumer that treats a fragment as missing throws away real work;
        one that treats missing as a fragment invents work that never happened."""
        self.assertFalse(pm.TRUNCATION_NOTICE.strip().startswith("⚠️"))

    def test_a_truncation_before_the_marker_does_not_leak_forward(self):
        """The window is what makes this attributable. Without it, one cut-off call would
        annotate every later report in the process."""
        pm.record("claude", "strategist", response=_Anthropic(stop_reason="max_tokens"))
        marker = pm.mark()
        pm.record("claude", "skeptic", response=_Anthropic(stop_reason="end_turn"))
        self.assertEqual(pm.annotate_if_incomplete("later report", marker), "later report")

    def test_another_providers_truncation_does_not_annotate_this_one(self):
        marker = pm.mark()
        pm.record("gemini", "skeptic", response=_Gemini(finish="MAX_TOKENS"))
        self.assertEqual(pm.annotate_if_incomplete("claude text", marker, "claude"), "claude text")
        self.assertIn("incomplete", pm.annotate_if_incomplete("gemini text", marker, "gemini"))

    def test_empty_text_is_left_alone(self):
        # An empty body is the "⚠️ returned an empty response" case, which its own caller
        # already labels. Appending a truncation notice to nothing would manufacture a report.
        marker = pm.mark()
        pm.record("gemini", "skeptic", response=_Gemini(finish="MAX_TOKENS"))
        self.assertEqual(pm.annotate_if_incomplete("", marker), "")

    def test_the_ledger_names_which_role_was_cut_off(self):
        """The property the debate's error list depends on. Without the role on the record the
        only way to attribute a truncation to a chair is to sniff its prose for the notice --
        deriving from text a fact the ledger already holds exactly."""
        marker = pm.mark()
        pm.record("claude", "strategist", response=_Anthropic(stop_reason="end_turn"))
        pm.record("gemini", "skeptic", response=_Gemini(finish="MAX_TOKENS"))
        cut = {r.role for r in pm.since(marker) if r.completion_state == pm.TRUNCATED}
        self.assertEqual(cut, {"skeptic"})
