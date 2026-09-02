"""§17 — cross-version schema, provider and live-upgrade safety.

What this file actually guarantees, as opposed to what it merely records:

  ENFORCED
    * A benchmark report says what operating envelope it ran under -- the token budget and the
      installed provider-SDK versions (R15) -- and omits an SDK it cannot see rather than
      inventing one. A benchmark run is this app's only versioned audit event; if it cannot
      say what moved underneath it, "did this model get worse?" is unanswerable.
    * comparable_history still keys on the three fingerprints ALONE. R15 records the envelope
      without gating on it, and that restraint is deliberate enough to pin.
    * Every stored-record reader survives a record that predates every optional field it now
      expects. Old audit records staying interpretable is §17's fourth question, and today the
      answer is yes -- by defensive .get(), which is easy to lose one bracket at a time.
    * Every (source, file) pair in _EXTERNAL_PERCENTILE_RULES that names a real file still has
      that file on disk. A rule pointing at a vanished export is unambiguously stale.
    * A PickSnapshot that outlives its own class definition fails LOUDLY. Streamlit's
      LocalSourcesWatcher evicts edited local modules from sys.modules while st.session_state
      survives, so an object held across an edit is an instance of a class that no longer
      exists -- verified in streamlit 1.61's own source. Raising beats reading a default the
      old object never carried.

  CHARACTERIZED (pinned, not endorsed -- each cites its register item and should be deleted,
  not loosened, when that item is settled)
    * The provider callers return text and nothing else, so which model actually served a call
      is unrecoverable by construction (#109).
    * A stored to-do whose status is outside both vocabularies is invisible in every view
      (#110).
    * Dropping an external source's percentile rule silently moves composite scores (#110).

  One test sits in ENFORCED that a first reading would have put in CHARACTERIZED: no production
  module declares a hand-maintained version constant. That absence looks like §17's headline gap
  until you read bot_benchmark._fingerprint's own docstring, which rejects version numbers on
  the record in favour of content hashes -- so a constant appearing is a reversal of a decision,
  not progress on a gap, and the test guards the decision. #111 is about extending the hashing
  this repo already chose, not about introducing numbers it already declined.
"""

import ast
import dataclasses
import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from unittest import mock

import attachments
import bot_benchmark
import bot_research
import data_merger as dm
import decision_log
import draft_board_ui
import llm_engine
import pick_synthesis as ps
import todo_log


def _function(module_file: str, name: str) -> ast.FunctionDef:
    source = Path(__file__).with_name(module_file).read_text()
    return next(
        n for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == name
    )


class ProviderSdkVersionRecordingTests(unittest.TestCase):
    def test_an_uninstalled_sdk_is_omitted_never_placeheld(self):
        with mock.patch.object(bot_benchmark, "_PROVIDER_SDK_DISTRIBUTIONS",
                               ("definitely-not-a-real-distribution-xyz",)):
            self.assertEqual(bot_benchmark._provider_sdk_versions(), {})

    def test_an_installed_distribution_reports_its_real_version(self):
        # streamlit is a hard dependency of this app and is installed wherever the suite runs;
        # using it rather than a provider SDK keeps this test honest in environments where the
        # provider SDKs are deliberately absent (they are, here -- every provider call in this
        # suite is stubbed).
        with mock.patch.object(bot_benchmark, "_PROVIDER_SDK_DISTRIBUTIONS", ("streamlit",)):
            versions = bot_benchmark._provider_sdk_versions()
        self.assertEqual(list(versions), ["streamlit"])
        self.assertRegex(versions["streamlit"], r"^\d+\.\d+")

    def test_a_partially_reporting_environment_still_records_what_it_can(self):
        with mock.patch.object(bot_benchmark, "_PROVIDER_SDK_DISTRIBUTIONS",
                               ("streamlit", "not-installed-at-all")):
            versions = bot_benchmark._provider_sdk_versions()
        self.assertIn("streamlit", versions)
        self.assertNotIn("not-installed-at-all", versions)

    def test_a_metadata_lookup_that_explodes_never_costs_the_run(self):
        with mock.patch("importlib.metadata.version", side_effect=RuntimeError("boom")):
            self.assertEqual(bot_benchmark._provider_sdk_versions(), {})


class BenchmarkEnvelopeTests(unittest.TestCase):
    """run_benchmark with every provider call stubbed -- no network, no keys."""

    def _report(self) -> dict:
        # run_benchmark reads its battery and rubric from module constants, so they are patched
        # down to one question rather than passed in -- a full real battery is not what any of
        # these assertions are about.
        battery = {"quant": [{"label": "q1", "prompt": "a question"}]}
        rubric = {"quant": [("clarity", 1.0, "is it clear")]}
        with mock.patch.object(bot_benchmark, "BENCHMARK_BATTERY", battery), \
             mock.patch.object(bot_benchmark, "RUBRIC", rubric), \
             mock.patch.dict(
                 llm_engine.PROVIDER_CALLERS,
                 {"claude": lambda *a, **k: "an answer",
                  "gemini": lambda *a, **k: "clarity: 4\nAn adequate answer."},
                 clear=False,
             ):
            return bot_benchmark.run_benchmark(
                role="quant", candidates=[("claude", "claude-x")],
                api_keys={"claude": "k", "gemini": "k"},
                judge_provider="gemini", judge_api_key="k",
            )

    def test_the_report_records_the_token_budget_it_ran_under(self):
        self.assertEqual(self._report()["max_tokens"], llm_engine.MAX_TOKENS)

    def test_the_report_records_the_provider_sdk_versions_it_ran_under(self):
        report = self._report()
        self.assertIn("provider_sdk_versions", report)
        self.assertIsInstance(report["provider_sdk_versions"], dict)

    def test_the_envelope_survives_a_save_and_reload(self):
        real = bot_benchmark.RESULTS_PATH
        with tempfile.TemporaryDirectory() as tmp:
            bot_benchmark.RESULTS_PATH = Path(tmp) / "benchmark_results.json"
            try:
                bot_benchmark.save_report("quant", self._report())
                stored = bot_benchmark.load_report("quant")
            finally:
                bot_benchmark.RESULTS_PATH = real
        self.assertEqual(stored["max_tokens"], llm_engine.MAX_TOKENS)
        self.assertIn("provider_sdk_versions", stored)

    def test_the_envelope_is_recorded_but_not_gated_on(self):
        # Deciding that a token-budget or SDK change makes two runs incomparable is a judgment
        # about what counts as the same experiment. R15 deliberately does not make it -- if a
        # later change wants to, it should be a considered edit, not a drift.
        source = ast.unparse(_function("bot_benchmark.py", "comparable_history"))
        self.assertIn("battery_fingerprint", source)
        self.assertIn("rubric_fingerprint", source)
        self.assertIn("chair_prompt_fingerprint", source)
        self.assertNotIn("max_tokens", source)
        self.assertNotIn("provider_sdk_versions", source)

    def test_a_pre_fingerprint_report_is_not_silently_comparable(self):
        real = bot_benchmark.RESULTS_PATH
        with tempfile.TemporaryDirectory() as tmp:
            bot_benchmark.RESULTS_PATH = Path(tmp) / "benchmark_results.json"
            try:
                bot_benchmark.RESULTS_PATH.write_text(json.dumps({
                    bot_benchmark._history_key("quant"): [
                        {"role": "quant", "ran_at": 1.0, "candidates": []},  # predates fingerprints
                    ],
                }))
                bot_benchmark.save_report("quant", self._report())
                comparable = bot_benchmark.comparable_history("quant")
                history = bot_benchmark.load_history("quant")
            finally:
                bot_benchmark.RESULTS_PATH = real
        self.assertEqual(len(history), 2)      # nothing was dropped from the record
        self.assertEqual(len(comparable), 1)   # ...but the unfingerprinted run is not comparable


class OldRecordsStayReadableTests(unittest.TestCase):
    """§17's fourth question. Each store is handed the barest record a much older version could
    plausibly have written, and every reader has to cope without raising."""

    def test_a_minimal_legacy_todo_reads_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            real, todo_log.TODOS_DIR = todo_log.TODOS_DIR, Path(tmp)
            try:
                todo_log.TODOS_DIR.mkdir(parents=True, exist_ok=True)
                todo_log._path("lg").write_text(json.dumps([{"id": 1, "text": "bare", "status": "resolved"}]))
                self.assertEqual(len(todo_log.load_todos("lg")), 1)
                self.assertEqual(len(todo_log.load_todos("lg", statuses=todo_log.ARCHIVED_STATUSES)), 1)
                self.assertEqual(len(todo_log.search_archived("lg", "bare")), 1)
            finally:
                todo_log.TODOS_DIR = real

    def test_a_minimal_legacy_decision_reads_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            real, decision_log.DECISIONS_DIR = decision_log.DECISIONS_DIR, Path(tmp)
            try:
                decision_log.DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
                decision_log._path("lg").write_text(json.dumps([
                    {"ts": 1.0, "question": "was this worth it", "outcome": "good"},
                ]))
                hits = decision_log.search_decisions_with_outcomes("lg", "was this worth it")
                self.assertEqual(len(hits), 1)
                self.assertTrue(decision_log.set_outcome("lg", 1.0, "bad", "revised"))
            finally:
                decision_log.DECISIONS_DIR = real

    def test_a_minimal_legacy_finding_still_READS_but_no_longer_feeds_the_composite(self):
        """CHANGED DELIBERATELY by 6.2a, and the distinction is the whole point of this class.

        A legacy row -- one written before the adjudication gate existed, so carrying no
        `adjudication` key at all -- must still READ without raising, still reach the panel as
        context, and still be a full member of the record. That half is unchanged and is what
        this class exists to guarantee.

        What changed is that its NUMBER no longer reaches `composite_player_score`. An absent
        `adjudication` key is a third state -- never adjudicated, as distinct from adjudicated
        and not confirmed -- and under 6.2a's ruling both are held back. Reading it as "confirmed
        by default" would be exactly the silent-grandfathering this file is here to catch: an old
        record acquiring an authority nobody granted it, because the field that would have
        withheld it did not exist yet.

        Recovering it is a person confirming it, same as any other finding.
        """
        legacy = {"id": 1, "player_name": "A Star", "source": "ESPN", "claim": "WR4", "rank": 4}
        with tempfile.TemporaryDirectory() as tmp:
            real, bot_research.FINDINGS_PATH = bot_research.FINDINGS_PATH, Path(tmp) / "f.json"
            try:
                bot_research.FINDINGS_PATH.write_text(json.dumps([legacy]))
                # Unchanged: it reads, and it reaches the panel.
                self.assertEqual(len(bot_research.findings_for_context()), 1)
                self.assertEqual(len(bot_research.load_findings()), 1)
                # Changed: held back, and listed as awaiting a person rather than dropped.
                self.assertTrue(dm.load_bot_research_as_external().empty)
                self.assertEqual([f["id"] for f in bot_research.findings_awaiting_adjudication()],
                                 [1])
                # And recoverable, so this is a gate rather than a one-way loss.
                bot_research.confirm_finding(1)
                frame = dm.load_bot_research_as_external()
            finally:
                bot_research.FINDINGS_PATH = real
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["source_name"], "bot_research")

    def test_a_minimal_legacy_attachment_caption_reads_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            real, attachments.ATTACHMENTS_DIR = attachments.ATTACHMENTS_DIR, Path(tmp)
            try:
                real_captions, attachments.CAPTIONS_PATH = (
                    attachments.CAPTIONS_PATH, Path(tmp) / "captions.json",
                )
                attachments.ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)
                (attachments.ATTACHMENTS_DIR / "note.txt").write_bytes(b"x")
                attachments.CAPTIONS_PATH.write_text(json.dumps({"note.txt": {"caption": "a note"}}))
                items = attachments.list_attachments()
            finally:
                attachments.ATTACHMENTS_DIR = real
                attachments.CAPTIONS_PATH = real_captions
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["caption"], "a note")


class SnapshotOutlivingItsClassTests(unittest.TestCase):
    """Streamlit evicts an edited local module from sys.modules (verified in streamlit 1.61's
    LocalSourcesWatcher) while st.session_state survives, so a held PickSnapshot can be an
    instance of a class definition that no longer exists. What matters is that the mismatch is
    LOUD -- a consumer must never read a field the old object never carried as if it had."""

    @dataclass
    class _OlderPickSnapshot:
        pick_label: str
        round: int
        my_roster_id: str
        candidates: tuple
        user_selected_player_id: Optional[str] = None

    def _older(self):
        return self._OlderPickSnapshot(pick_label="1.05", round=1, my_roster_id="1", candidates=())

    def test_the_certifier_refuses_a_snapshot_that_predates_its_stamp_fields(self):
        class _Merger:
            freshest_date = "2026-08-01"
        with self.assertRaises(AttributeError):
            ps.snapshot_is_current(self._older(), [], _Merger())

    def test_the_board_serializer_refuses_a_snapshot_that_predates_its_regime_field(self):
        with self.assertRaises(AttributeError):
            draft_board_ui.serialize_snapshot(self._older(), pick_header="1.05", state_tags=[])

    def test_a_current_snapshot_passes_both_consumers(self):
        # Non-vacuity for the two above: they must be failing on the missing field, not on the
        # call shape.
        class _Merger:
            freshest_date = "2026-08-01"
        snap = ps.PickSnapshot(pick_label="1.05", round=1, my_roster_id="1", candidates=(),
                               picks_consumed=0, data_freshest_date="2026-08-01")
        self.assertEqual(ps.snapshot_is_current(snap, [], _Merger()), (True, None))
        payload = draft_board_ui.serialize_snapshot(snap, pick_header="1.05", state_tags=[])
        self.assertEqual(payload["decisionRegime"], "contested")

    def test_the_stamp_fields_carry_no_default_that_could_pass_for_a_real_value(self):
        # An unstamped snapshot reports None, and snapshot_is_current treats None as
        # not-certifiable rather than current -- the absence contract, at the one boundary
        # where a wrong default would read as "yes, still current".
        defaults = {f.name: f.default for f in dataclasses.fields(ps.PickSnapshot)}
        self.assertIsNone(defaults["picks_consumed"])
        self.assertIsNone(defaults["data_freshest_date"])


class ExternalPercentileRuleDriftTests(unittest.TestCase):
    def test_every_file_backed_rule_still_points_at_a_file_on_disk(self):
        # A rule naming an export that no longer exists is unambiguously stale: that source
        # silently stops feeding the composite while still appearing loaded.
        missing = [
            f"{src}/{name}" for (src, name) in dm._EXTERNAL_PERCENTILE_RULES
            if src != "bot_research" and not (dm.EXTERNAL_VALUES_DIR / src / name).exists()
        ]
        self.assertEqual(missing, [], f"percentile rules point at files that are not there: {missing}")

    def test_the_synthetic_research_pair_is_the_only_ruleless_file(self):
        # bot_research/findings is generated, not read off disk -- pinned so that a future
        # non-file rule has to be a deliberate addition rather than an unnoticed one.
        synthetic = [pair for pair in dm._EXTERNAL_PERCENTILE_RULES
                     if not (dm.EXTERNAL_VALUES_DIR / pair[0] / pair[1]).exists()]
        self.assertEqual(synthetic, [("bot_research", "findings")])

    def test_upload_targets_are_derived_from_the_rules_not_a_second_copy(self):
        targets = dm.external_upload_targets()
        self.assertNotIn("bot_research", targets)
        for source, filename in targets.items():
            self.assertIn((source, filename), dm._EXTERNAL_PERCENTILE_RULES)

    def test_CHARACTERIZATION_dropping_a_rule_moves_composites_with_no_error(self):
        """#110. The rule table is code and the export files are stored context; nothing
        reconciles the two. Renaming one tracked filename -- what happens when a vendor
        renames its export -- silently re-scores players: measured at 31 of 131 sampled
        composites moved, median |delta| 4.3 on a 0-100 scale, four disappearing outright,
        with no exception, warning or log. The file stays on disk and still counts as a
        loaded source; it just stops feeding the composite.

        Pinned, not endorsed. Recording the drift means deciding how to tell a deliberate
        exclusion (ESPN's redraft list, FantasyPros' best-ball list -- both documented as
        out of the composite on purpose) from an accidental orphan, which is a policy call.
        Delete this test when #110 is settled -- do not loosen it.
        """
        merger = dm.DataMerger()
        names = [n for n in merger.projections["name"].dropna().unique()[:400]]
        before = {n: merger.composite_player_score(n) for n in names}
        before = {n: round(c["score"], 2) for n, c in before.items() if c}
        self.assertGreater(len(before), 20, "sample too small to say anything")

        saved = dict(dm._EXTERNAL_PERCENTILE_RULES)
        try:
            dm._EXTERNAL_PERCENTILE_RULES.pop(("dynastyprocess", "players.csv"), None)
            dm._EXTERNAL_PERCENTILE_RULES[("dynastyprocess", "players_v2.csv")] = ("value_1qb", True)
            after_merger = dm.DataMerger()   # no error raised by the rename
            after = {n: after_merger.composite_player_score(n) for n in names}
            after = {n: round(c["score"], 2) for n, c in after.items() if c}
        finally:
            dm._EXTERNAL_PERCENTILE_RULES.clear()
            dm._EXTERNAL_PERCENTILE_RULES.update(saved)

        moved = [n for n in before if n in after and before[n] != after[n]]
        vanished = [n for n in before if n not in after]
        self.assertTrue(moved or vanished, "the rename had no measurable effect at all")


class ServedModelIsUnrecoverableTests(unittest.TestCase):
    def test_CHARACTERIZATION_the_provider_callers_return_text_and_nothing_else(self):
        """#109. All three default model ids are floating aliases -- CLAUDE_MODEL's own comment
        records that it replaced "a now-retired dated snapshot" -- so the string this app sends
        does not identify the weights that answer. Every provider response object carries the
        model that actually served it; all three callers extract text and discard the object,
        so §17's last question ("what happens if a provider silently aliases a model name to a
        newer underlying model?") has the answer: nothing notices, and every audit record reads
        identically before and after.

        Pinned, not endorsed. Capturing the served model means changing what PROVIDER_CALLERS
        returns -- today a plain str, which the whole fail-soft "⚠️ ..." convention depends on
        -- and verifying each provider's own field name against three SDKs that are
        deliberately not installed in this environment. Blocked on that, like #88.
        Delete this test when #109 is settled.
        """
        for func in ("_call_claude", "_call_gemini", "_call_openai"):
            with self.subTest(caller=func):
                node = _function("llm_engine.py", func)
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                self.assertTrue(returns)
                for ret in returns:
                    rendered = ast.unparse(ret.value)
                    # Every return is a string expression; none hands the response object out.
                    self.assertNotEqual(rendered.strip(), "response")
                    self.assertNotIn("response.model", rendered)

    def test_the_default_model_ids_are_aliases_rather_than_dated_snapshots(self):
        # A dated snapshot pins the weights; an alias is re-pointed by the provider. Pinning
        # which kind these are makes a switch to either a deliberate, visible edit.
        for value in (llm_engine.CLAUDE_MODEL, llm_engine.GEMINI_MODEL, llm_engine.OPENAI_MODEL):
            with self.subTest(model=value):
                self.assertNotRegex(value, r"-20\d{6}$")


class TodoStatusVocabularyTests(unittest.TestCase):
    def test_the_two_vocabularies_do_not_overlap(self):
        self.assertEqual(set(todo_log.ACTIVE_STATUSES) & set(todo_log.ARCHIVED_STATUSES), set())

    def test_CHARACTERIZATION_a_status_outside_both_vocabularies_is_invisible_everywhere(self):
        """#110. Every one of app.py's five load_todos calls passes a status filter, so a
        record whose status the running code does not recognise appears in no view at all --
        not the active list, not the archive, not the archive search, not the header count,
        not build_context. It is not deleted and raises nothing; it is simply gone. Two
        upgrades produce this: renaming a status, and reading a file written by a newer
        version.

        This sits against todo_log's own stated rule -- archived items are "kept, with a
        reason and date, never destroyed" -- and a record invisible in every view is
        functionally destroyed. Pinned rather than repaired because where an unrecognised
        record should SURFACE is a UI decision. Delete this test when #110 is settled.
        """
        with tempfile.TemporaryDirectory() as tmp:
            real, todo_log.TODOS_DIR = todo_log.TODOS_DIR, Path(tmp)
            try:
                todo_log.TODOS_DIR.mkdir(parents=True, exist_ok=True)
                todo_log._path("lg").write_text(json.dumps([
                    {"id": 1, "text": "known", "status": "active"},
                    {"id": 2, "text": "written by a later version", "status": "deferred"},
                ]))
                everything = todo_log.load_todos("lg")
                active = todo_log.load_todos("lg", statuses=todo_log.ACTIVE_STATUSES)
                archived = todo_log.load_todos("lg", statuses=todo_log.ARCHIVED_STATUSES)
            finally:
                todo_log.TODOS_DIR = real
        self.assertEqual(len(everything), 2)                       # still on disk
        self.assertEqual([e["id"] for e in active], [1])
        self.assertEqual([e["id"] for e in archived], [])          # and visible nowhere


class VersionIdentityShapeTests(unittest.TestCase):
    def test_no_module_declares_a_hand_maintained_version_constant(self):
        """#111, and NOT the gap it first looks like. Not one production module defines
        __version__, SCHEMA_VERSION, CDME_VERSION or anything equivalent, and not one stored
        record carries a version field -- but bot_benchmark._fingerprint states the reason
        outright: a content hash is used "deliberately ... rather than a hand-maintained version
        number: a number has to be remembered and drifts out of sync with the thing it names,
        whereas this cannot disagree with the battery, rubric, or chair prompt it was computed
        from."

        So this is an ENFORCED boundary, not a characterized defect: the version-number shape was
        considered and rejected for the one artifact that needed identity, and a constant
        appearing here would be a reversal of that decision rather than progress on it. What
        #111 actually asks is whether the fingerprint approach -- already the established answer
        -- should be extended to the CDME coefficient set, the record schemas and the chair
        contracts outside the benchmark, which today have no identity of any kind.
        """
        names = {"__version__", "SCHEMA_VERSION", "VERSION", "CDME_VERSION", "ENGINE_VERSION"}
        here = Path(__file__).parent
        offenders = []
        for path in sorted(here.glob("*.py")):
            if path.name.startswith(("test_", "run_", "compare_", "verify_", "cdme_")):
                continue
            for node in ast.walk(ast.parse(path.read_text())):
                targets = []
                if isinstance(node, ast.Assign):
                    targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    targets = [node.target.id]
                if names & set(targets):
                    offenders.append(f"{path.name}:{node.lineno}")
        self.assertEqual(
            offenders, [],
            "a hand-maintained version constant now exists, reversing the decision recorded in "
            f"bot_benchmark._fingerprint's docstring -- see #111 before keeping it: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
