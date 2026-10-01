"""§10 (ARCHITECTURE_AUDIT Pass 7): auditability, provenance and causal reconstruction.

The guide's §10 mandate: *a material recommendation should be reproducible as a causal artifact,
not merely recoverable as a piece of prose.*

Today it is recoverable as prose and not reproducible as an artifact, and this file is honest
about which half is which.

  ENFORCEMENT — what a record must carry. Every AI result that is persisted or returned must
  say what actually answered it: provider AND model, recorded on the result rather than
  re-derived from live configuration, because a role can be re-pointed later and an old record
  must keep showing who answered it. `app.append_message` already applied that rule to chat
  messages; the §10 repair applied it to the two debate results and the decision row, and these
  tests keep it applied.

  CHARACTERIZATION — where the causal chain breaks. Measured link by link against the guide's
  own chain, 4 of 10 links survive for a Prytaneum verdict and 1 of 10 for a Draft Room pick.
  Invert these when the chain is closed; do not delete them.

No provider is called anywhere in this file.
"""

import inspect
import json
import re
import tempfile
import unittest
from pathlib import Path

import decision_log
import llm_engine
import pick_debate
import ui_source

_HERE = Path(__file__).parent
_APP = ui_source.text()


def _stub_provider(response: str):
    def _call(system_prompt, user_prompt, api_key=None, model=None):
        return response
    return _call


class AResultRecordsWhatAnsweredItTests(unittest.TestCase):
    """The rule app.append_message states, applied everywhere a result is produced."""

    def test_the_prytaneum_result_records_provider_and_model_per_chair(self):
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub_provider("RECOMMENDATION: HOLD")
        try:
            result = llm_engine.run_debate(
                "CONTEXT", "QUESTION",
                role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
                api_keys={"claude": "k"},
                role_models={"quant": "small-model", "moderator": "big-model"},
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        self.assertEqual(result.role_models["quant"], "small-model")
        self.assertEqual(result.role_models["moderator"], "big-model")
        # Non-vacuity: the provider half was already recorded, and still is.
        self.assertEqual(result.role_providers["quant"], "claude")

    def test_a_same_provider_model_swap_is_visible_in_the_record(self):
        """Why provider alone is not enough: two chairs can share a provider and differ only by
        model, which a provider-only record cannot distinguish at all."""
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub_provider("RECOMMENDATION: HOLD")
        try:
            result = llm_engine.run_debate(
                "CONTEXT", "QUESTION",
                role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
                api_keys={"claude": "k"},
                role_models={"quant": "cheap", "moderator": "expensive"},
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        self.assertEqual(len(set(result.role_providers.values())), 1)
        self.assertNotEqual(result.role_models["quant"], result.role_models["moderator"])

    def test_the_draft_room_result_records_provider_and_model_per_chair(self):
        original = dict(pick_debate.PROVIDER_CALLERS)
        for name in list(pick_debate.PROVIDER_CALLERS):
            pick_debate.PROVIDER_CALLERS[name] = _stub_provider("RECOMMENDATION: Somebody")
        try:
            snapshot = _minimal_snapshot()
            result = pick_debate.debate_pick(
                snapshot, api_keys={"claude": "k", "gemini": "k", "openai": "k"},
                role_models={"caller": "big-model"},
            )
        finally:
            pick_debate.PROVIDER_CALLERS.update(original)
        self.assertEqual(result.role_models.get("caller"), "big-model")
        self.assertTrue(result.role_providers, "the provider half must still be recorded")

    def test_an_unset_model_records_as_absent_not_as_a_guess(self):
        """Absent must mean 'ran on the provider default', never a fabricated model name."""
        original = dict(llm_engine.PROVIDER_CALLERS)
        llm_engine.PROVIDER_CALLERS["claude"] = _stub_provider("RECOMMENDATION: HOLD")
        try:
            result = llm_engine.run_debate(
                "CONTEXT", "QUESTION",
                role_providers={r: "claude" for r in ("quant", "beat", "contrarian", "moderator")},
                api_keys={"claude": "k"},
            )
        finally:
            llm_engine.PROVIDER_CALLERS.update(original)
        self.assertEqual(result.role_models, {})

    def test_a_decision_row_records_what_produced_the_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = decision_log.DECISIONS_DIR
            decision_log.DECISIONS_DIR = Path(tmp)
            try:
                decision_log.log_decision(
                    "L1", "Should I trade?", {"recommendation": "HOLD"}, "prose",
                    provider="claude", model="big-model",
                )
                row = decision_log.load_decisions("L1")[0]
                self.assertEqual(row["provider"], "claude")
                self.assertEqual(row["model"], "big-model")
            finally:
                decision_log.DECISIONS_DIR = saved

    def test_an_unstamped_decision_row_is_still_valid_and_says_nothing_rather_than_guessing(self):
        """Rows written before the stamp existed, and callers that genuinely do not know."""
        with tempfile.TemporaryDirectory() as tmp:
            saved = decision_log.DECISIONS_DIR
            decision_log.DECISIONS_DIR = Path(tmp)
            try:
                decision_log.log_decision("L1", "Q", {"recommendation": "BUY"}, "prose")
                row = decision_log.load_decisions("L1")[0]
                self.assertEqual(row["provider"], "")
                self.assertEqual(row["model"], "")
            finally:
                decision_log.DECISIONS_DIR = saved

    def test_both_app_call_sites_pass_what_answered_rather_than_leaving_it_blank(self):
        """A stamp nothing populates is worse than no stamp -- it reads as 'unknown' when the
        information was in scope the whole time."""
        self.assertIn('provider=role_providers["moderator"]', _APP)
        self.assertIn('model=role_models.get("moderator") or ""', _APP)
        # Count CALL sites, not the definition -- "process_moderator_output(" matches `def
        # process_moderator_output(` too, which is how this first read 3 where 2 was meant.
        calls = _APP.count("process_moderator_output(") - _APP.count("def process_moderator_output(")
        self.assertEqual(calls, 2)
        # Every call site passes both halves; none leaves the stamp to its default.
        self.assertEqual(_APP.count('model=role_models.get("moderator") or ""'), 2)


class CausalChainIsIncompleteTests(unittest.TestCase):
    """KNOWN GAPS — characterization. Invert when the chain closes; do not delete."""

    def test_no_debate_result_from_the_draft_room_ever_reaches_disk(self):
        """The surface with the strongest canonical state has the weakest audit trail: the
        frozen PickSnapshot, the three chair reports and the verdict all live in session state
        and are gone when the session ends."""
        for module in (pick_debate,):
            source = inspect.getsource(module)
            for writer in ("write_text", "json.dump", "open("):
                self.assertNotIn(writer, source, f"{module.__name__} now persists -- invert this test.")
        self.assertIn("st.session_state.draft_room_debate_result = debate_result", _APP)
        self.assertNotIn("save_debate_result", _APP)

    def test_the_context_supplied_to_a_seat_is_never_recorded(self):
        """§3.6's finding, still true and still the first broken link in §10's chain."""
        source = inspect.getsource(decision_log.log_decision)
        for field in ("context", "prompt", "snapshot"):
            self.assertNotIn(field, source)

    def test_the_operational_activity_log_is_session_only(self):
        """§10 asks to distinguish operational logs from user-facing decision history. Both
        exist; only the decision history survives a restart."""
        self.assertIn("st.session_state.activity_log.insert(0,", _APP)
        self.assertNotIn("save_activity_log", _APP)

    def test_no_cost_token_or_retry_accounting_exists_anywhere(self):
        """§10 asks whether every AI expenditure can be attributed to user, operation, chair,
        model, provider, retry and tool call. None of those quantities is recorded."""
        import bot_benchmark
        for module in (llm_engine, pick_debate, bot_benchmark, decision_log):
            source = inspect.getsource(module)
            # Word-bounded: "output_tokens=" matches `max_output_tokens=MAX_TOKENS`, which is
            # the OUTPUT CAP (§9), not usage accounting -- the exact substring artifact this
            # programme has now caught six times.
            for marker in (r"(?<![a-z_])input_tokens", r"(?<![a-z_])output_tokens\b(?!\s*=\s*MAX)",
                           r"\.usage\b", r"(?<![a-z_])retry_count"):
                self.assertIsNone(
                    re.search(marker, source),
                    f"{module.__name__} gained accounting ({marker}) -- invert this test.",
                )


def _minimal_snapshot():
    from pick_synthesis import CandidateSnapshot, PickSnapshot
    import dataclasses
    fields = {f.name: f for f in dataclasses.fields(CandidateSnapshot)}
    kwargs = {}
    for name, f in fields.items():
        if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
            continue
        kwargs[name] = {"player_id": "1", "name": "Somebody", "position": "WR"}.get(name, 0.0)
    candidate = CandidateSnapshot(**kwargs)
    snap_fields = {f.name: f for f in dataclasses.fields(PickSnapshot)}
    snap_kwargs = {}
    for name, f in snap_fields.items():
        if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
            continue
        snap_kwargs[name] = {
            "pick_label": "1.01", "round": 1, "my_roster_id": "1", "candidates": [candidate],
        }.get(name, None)
    return PickSnapshot(**snap_kwargs)


class FindingOriginReachesTheContextTests(unittest.TestCase):
    """#97/§6.5 + #106, at the consumer. An evidence snapshot nothing reads is worse than no
    snapshot -- it looks handled. The named consumer is build_context's PANEL-VETTED FINDINGS
    block, the one place a stored finding is put in front of a model.

    app.py is source-scanned rather than imported here, the same way every other app-level
    contract in this suite is checked -- importing it pulls in streamlit and a live session.
    """

    def test_the_context_no_longer_hedges_every_finding_as_search_or_reference_material(self):
        """The sentence this replaces said the app could not tell a bot's live search from the
        user's own captioned upload. That was true and is the thing #106 recorded. It is no
        longer the only thing the app can say, so the blanket hedge is gone."""
        self.assertNotIn("whether that was a bot's live search or the user's own reference material", _APP)

    def test_all_three_origin_states_are_rendered_distinctly(self):
        self.assertIn("_finding_origin_note", _APP)
        self.assertIn("panel retrieved", _APP)
        self.assertIn("no retrieval reported", _APP)

    def test_a_row_with_no_evidence_key_is_left_unlabelled_rather_than_called_unattributed(self):
        """The third state, and the one a two-way conditional would silently lose. A row written
        before the snapshot existed NEVER CHECKED; a row that recorded no sources CHECKED AND
        FOUND NONE. Stamping the first with the second's label is a provenance claim about rows
        that predate the mechanism."""
        source = _APP.split("def _finding_origin_note(")[1].split("\ndef ")[0]
        self.assertIn('if not isinstance(evidence, dict):', source)
        self.assertIn('return ""', source)
        self.assertIn("#112", source, "the never-checked distinction names where it comes from")

    def test_the_prompt_tells_the_model_the_tag_is_debate_scoped_and_not_a_citation(self):
        """The single most dangerous misreading available here: treating a debate-level page list
        as the citation for one claim. The block says so in the model's own reading order."""
        block = _APP.split("PANEL-VETTED FINDINGS")[1].split("PANEL-VETTED PLAYER COMPARISONS")[0]
        self.assertIn("DEBATE-level", block)
        self.assertIn("not this", block)
        self.assertIn("UNKNOWN", block)

    def test_both_moderator_paths_hand_over_their_own_retrieval_window(self):
        """A fresh debate reads run_debate's window; a follow-up marks and reads its own. The
        follow-up runs ONE chair, so reusing the original debate's four-chair window would
        overstate what that reply rested on."""
        self.assertIn("debate_sources=result.sources_retrieved", _APP)
        self.assertIn("_followup_meter_at = provider_meter.mark()", _APP)
        self.assertIn("debate_sources=provider_meter.sources_since(_followup_meter_at)", _APP)


if __name__ == "__main__":
    unittest.main()
