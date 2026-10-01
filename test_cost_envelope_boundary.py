"""§15 (ARCHITECTURE_AUDIT Pass 11): economic and resource exhaustion.

The section's strongest property is that **every AI operation has a deterministic, small,
closed-form call envelope** — not because a limiter enforces one, but because nothing loops,
nothing retries, and no model output can trigger another model call. That is a real cost
guarantee and it was undefended: a single added retry or a chair that reacts to another chair
would change the bill without changing any number a test looks at.

  ENFORCEMENT.
  * Counted, by stubbing the real callers: `run_debate` = 4, `ask_moderator_followup` = 1,
    `debate_pick` = 3, `run_benchmark` = candidates x scenarios x 2.
  * No retry, no backoff, no loop around a provider call.
  * **No recursion**: `process_moderator_output` touches parsers and stores only, so parsing a
    model's output can never spend money.
  * Parallelism is bounded at 2 workers.
  * The benchmark discloses its cost before it is run.

  CHARACTERIZATION — invert on repair, do not delete. There is no budget, ceiling, quota,
  cooldown, debounce or throttle anywhere; provider-side tool calls inside one chair call are
  uncapped and invisible; and the benchmark's candidate list defaults to every model fetched.

No provider is called anywhere in this file.
"""

import ast
import dataclasses
import inspect
import re
import unittest
from pathlib import Path

import bot_benchmark
import llm_engine
import provider_meter
import pick_debate
import pick_synthesis as ps
import ui_source

_HERE = Path(__file__).parent
_APP = ui_source.text()

_VERDICT = "RECOMMENDATION: HOLD\nCONVICTION: Split\nREASON: x"
_JUDGE = "SYNTHESIS: 50\nDISAGREEMENT_HANDLING: 50\nCLARITY: 50\nACTIONABILITY: 50\nNOTES: ok"


def _counter(box):
    def _call(system_prompt, user_prompt, api_key=None, model=None):
        box["n"] += 1
        return _JUDGE if "Score this response on each dimension" in user_prompt else _VERDICT
    return _call


def _minimal_snapshot():
    fields = {f.name: f for f in dataclasses.fields(ps.CandidateSnapshot)}
    kwargs = {
        name: {"player_id": "1", "name": "Somebody", "position": "WR"}.get(name, 0.0)
        for name, f in fields.items()
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }
    candidate = ps.CandidateSnapshot(**kwargs)
    snap_fields = {f.name: f for f in dataclasses.fields(ps.PickSnapshot)}
    snap_kwargs = {
        name: {"pick_label": "1.01", "round": 1, "my_roster_id": "1",
               "candidates": (candidate,)}.get(name)
        for name, f in snap_fields.items()
        if f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
    }
    return ps.PickSnapshot(**snap_kwargs)


class TheCallEnvelopeIsDeterministicTests(unittest.TestCase):
    """§15: 'is there a deterministic maximum call/cost envelope for each operation type?'
    Counted rather than read, so a future loop or retry shows up here as a number change."""

    def _count(self, module, run):
        box = {"n": 0}
        original = dict(module.PROVIDER_CALLERS)
        for name in list(module.PROVIDER_CALLERS):
            module.PROVIDER_CALLERS[name] = _counter(box)
        try:
            run()
        finally:
            module.PROVIDER_CALLERS.update(original)
        return box["n"]

    def test_a_full_prytaneum_debate_costs_exactly_four_calls(self):
        n = self._count(llm_engine, lambda: llm_engine.run_debate(
            "CTX", "Q",
            role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
            api_keys={"claude": "k"},
        ))
        self.assertEqual(n, 4)
        self.assertEqual(n, len(llm_engine.ROLE_SYSTEM_PROMPTS))

    def test_a_moderator_followup_costs_exactly_one_call(self):
        n = self._count(llm_engine, lambda: llm_engine.ask_moderator_followup(
            "CTX", "Q", "quant", "beat", "contrarian", "prior verdict",
            provider="claude", api_key="k",
        ))
        self.assertEqual(n, 1)

    def test_a_draft_room_debate_costs_exactly_three_calls(self):
        n = self._count(pick_debate, lambda: pick_debate.debate_pick(
            _minimal_snapshot(), api_keys={"claude": "k", "openai": "k"},
        ))
        self.assertEqual(n, 3)
        self.assertEqual(n, len(pick_debate.DEFAULT_ROLE_PROVIDERS))

    def test_a_benchmark_costs_candidates_times_scenarios_times_two(self):
        """One model call plus one judge call per scenario -- the judge is the half that is
        easy to forget when reasoning about what a benchmark run costs."""
        battery = len(bot_benchmark.BENCHMARK_BATTERY["moderator"])
        for candidates in (1, 2, 3):
            n = self._count(llm_engine, lambda c=candidates: bot_benchmark.run_benchmark(
                "moderator", [("claude", f"m{i}") for i in range(c)], {"claude": "k"},
                judge_provider="claude",
            ))
            self.assertEqual(n, candidates * battery * 2, f"{candidates} candidates")


class NothingAmplifiesTheEnvelopeTests(unittest.TestCase):
    """The three ways a fixed envelope silently stops being fixed."""

    def test_no_retry_or_backoff_exists(self):
        """Deliberately cruder than NoBudgetPrimitivesExistTests below: a raw lowercased
        substring scan over the whole source, comments and docstrings included, not
        word-bounded. That is over-broad on purpose -- a comment that merely mentions retrying
        trips it, and being made to re-read the diff and confirm no retry semantics were added
        is worth more than the false positive costs. It has already earned that once (§17 R15's
        first draft described an SDK's "retry behavior" in a comment). Do not narrow it to
        code-only without deciding that the cheaper signal is no longer wanted."""
        combined = (inspect.getsource(llm_engine) + inspect.getsource(pick_debate)
                    + inspect.getsource(bot_benchmark)).lower()
        for marker in ("retry", "backoff", "max_retries", "tenacity"):
            self.assertNotIn(marker, combined, f"{marker} appeared -- the envelope is no longer fixed.")

    def test_the_limits_module_adds_no_retry_semantics_either(self):
        """provider_meter now sits directly on the provider call path, so the guard above has to
        reach it too. It is scanned differently on purpose: it DECLARES a retry knob (that is
        the point of #105's decision surface), so a raw substring scan would be meaningless
        here. What must remain true is that nothing loops and nothing backs off."""
        source = inspect.getsource(provider_meter).lower()
        for marker in ("backoff", "tenacity", "time.sleep", "while true"):
            self.assertNotIn(marker, source, f"{marker} appeared -- the envelope is no longer fixed.")

    def test_the_retry_knob_exists_and_is_off_so_the_envelope_is_unchanged(self):
        """§14/§15 concluded 'this app performs no retries'. What was actually established is
        narrower: this REPO contains no retry code. Whether retries HAPPEN was never measured,
        and the provider SDKs carry their own defaults, so the old claim was a property of the
        source text rather than of the running system -- the exact trap this audit kept naming.

        The knob is now explicit and deliberately OFF: None means nothing is passed, so runtime
        behaviour is byte-identical to before it existed. Choosing a value is a cost/latency
        policy decision and is parked."""
        self.assertIsNone(provider_meter.CLIENT_MAX_RETRIES)

        class _Client:
            def __init__(self, api_key=None, timeout=None, max_retries=None):
                pass

        off = provider_meter.client_limits("probe", _Client)
        self.assertNotIn("max_retries", off, "the knob is off; nothing may be passed")

        # Non-vacuity: the knob is real, not decorative. With a value set it IS passed, so the
        # test above is measuring an off switch rather than a missing wire.
        original = provider_meter.CLIENT_MAX_RETRIES
        provider_meter.CLIENT_MAX_RETRIES = 0
        try:
            on = provider_meter.client_limits("probe", _Client)
        finally:
            provider_meter.CLIENT_MAX_RETRIES = original
        self.assertEqual(on.get("max_retries"), 0)

    def test_no_loop_wraps_a_provider_call(self):
        for module in (llm_engine, pick_debate):
            source = inspect.getsource(module)
            self.assertIsNone(
                re.search(r"while [^\n]*:\n(?:[^\n]*\n)*?[^\n]*PROVIDER_CALLERS", source),
                f"{module.__name__} loops around a provider call.",
            )
        # bot_benchmark does loop, and its bounds are the two finite lists it iterates.
        bench = inspect.getsource(bot_benchmark.run_benchmark)
        self.assertIn("for provider, model in candidates:", bench)
        self.assertIn("for q in battery:", bench)
        self.assertNotIn("while ", bench)

    def test_parsing_a_models_output_can_never_spend_money(self):
        """§15: 'can recursive research or chair calls exceed a hard operation envelope?'
        `process_moderator_output` is the one place model output is acted on, and it reaches
        only parsers and stores -- so no verdict can trigger another call."""
        # Walked by AST with the docstring dropped, not by text: the docstring MENTIONS
        # ask_moderator_followup (explaining which callers can produce a verdict block), and a
        # line-prefix filter does not remove a docstring's body lines -- which is how this test
        # first reported a recursion path that does not exist.
        body = ui_source.block("def process_moderator_output(", "\ndef ")
        func = ast.parse(body).body[0]
        statements = func.body
        if (statements and isinstance(statements[0], ast.Expr)
                and isinstance(statements[0].value, ast.Constant)
                and isinstance(statements[0].value.value, str)):
            statements = statements[1:]
        called = {
            node.attr
            for statement in statements for node in ast.walk(statement)
            if isinstance(node, ast.Attribute) and getattr(node.value, "id", "") == "llm_engine"
        }
        self.assertTrue(called, "nothing parsed -- this assertion would be vacuous")
        self.assertTrue(
            all(name.startswith("parse_") for name in called),
            f"process_moderator_output reaches non-parser members: {called}",
        )

    def test_the_only_ask_call_sites_are_user_triggered(self):
        """Every provider-spending entry point sits behind a button or a submitted question,
        never behind another model's output."""
        spend_sites = re.findall(r"llm_engine\.(ask_\w+|run_debate)\(", _APP)
        self.assertEqual(
            sorted(set(spend_sites)),
            ["ask_beat", "ask_condense_to_objective", "ask_moderator_followup", "ask_quant", "run_debate"],
        )

    def test_parallelism_is_bounded(self):
        source = inspect.getsource(llm_engine.run_debate)
        match = re.search(r"max_workers=(\d+)", source)
        self.assertIsNotNone(match)
        self.assertLessEqual(int(match.group(1)), 4)


class NoBudgetPrimitivesExistTests(unittest.TestCase):
    """KNOWN GAPS — characterization. Invert when repaired; do not delete."""

    MODULES = ("llm_engine", "pick_debate", "bot_benchmark")

    def test_no_budget_ceiling_quota_cooldown_or_throttle_exists(self):
        """Checked word-bounded with comments and docstring prose excluded: a naive scan
        reports 'budget', 'ceiling' and 'spend' as present, and all three are prose --
        'per-pick LLM budget' in a docstring, PRICE CEILING as a verdict field, 'actually
        spend a full panel run' in a prompt."""
        for name in self.MODULES:
            source = (_HERE / f"{name}.py").read_text()
            code_lines = [l for l in source.splitlines() if not l.strip().startswith("#")]
            code = "\n".join(code_lines)
            for word in ("budget", "quota", "cooldown", "debounce", "throttle", "rate_limit",
                         "spend_cap", "cost_ceiling"):
                hits = [
                    l.strip() for l in code_lines
                    if re.search(rf"(?<![a-z_]){word}(?![a-z_])", l, re.I)
                    and "=" in l and not l.lstrip().startswith(('"', "'"))
                ]
                self.assertEqual(hits, [], f"{name} gained a {word} primitive -- invert this test.")

    def test_provider_side_tool_calls_are_uncapped(self):
        """Each chair call attaches a server-side web-search tool. How many searches the
        provider runs inside that one call is the provider's choice, is billed, and is
        invisible here -- so the CHAIR-call envelope is deterministic while the TOOL-call
        envelope is not."""
        source = inspect.getsource(llm_engine)
        self.assertIn("web_search", source, "the tool grant vanished -- re-check this test")
        for cap in ("max_uses", "max_tool_calls", "tool_choice", "max_searches"):
            self.assertNotIn(cap, source, f"{cap} appeared -- invert this test.")

    def test_the_benchmark_candidate_list_defaults_to_every_fetched_model(self):
        """The largest single-action spend in the app, defaulted to its maximum."""
        match = re.search(r"options=(\w+), default=(\w+),", _APP)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), match.group(2), "options and default diverged -- re-check.")

    def test_the_benchmark_discloses_its_cost_before_running(self):
        """Not a gap -- the mitigation that exists, pinned so it cannot quietly disappear."""
        self.assertIn("Real, billed API calls — nothing runs until you press Run.", _APP)
        self.assertIn("Run Benchmark ({len(_bench_candidates)} model(s)", _APP)
        self.assertIn("disabled=len(_bench_candidates) < 1", _APP)


if __name__ == "__main__":
    unittest.main()
