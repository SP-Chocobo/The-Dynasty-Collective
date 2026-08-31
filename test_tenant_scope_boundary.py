"""§12 (ARCHITECTURE_AUDIT Pass 9): tenant scope, cache leakage and context pollution.

§13.5 established that tenancy does not exist as deployed — single process, single filesystem,
no login. So §12's cross-*user* questions are prospective. Its cross-*league* questions are live
today, and they resolve better than the storage layout suggests, for reasons this file pins:

  ENFORCEMENT.
  * Four stores are league-scoped **by path**; two more are scoped **by key inside** a shared
    file (`league_format` by league, `league_prefs` by user) — both correctly, which is a
    correction to §13.5 (see 12.6).
  * Attachments carry a real scope list, and the filter is **actually wired into the prompt** —
    `build_context` calls `list_attachments(league_id=...)`. Unlike `snapshot_is_current`
    (§11.2), this protection is not stranded.
  * The one globally-shared league-derived store withholds its private field: a finding's
    `question` — the user's own free-text question — and its `league_id` reach neither another
    league's prompt nor the UI.
  * The only two cross-session caches take no arguments and load static assets.

  CHARACTERIZATION — invert on repair, do not delete. There is no way to scope a finding to its
  originating league, even though `league_id` is recorded on every one; the sharing is
  deliberate and disclosed in the UI, but it is not a per-item choice.

No provider is called anywhere in this file.
"""

import inspect
import json
import re
import tempfile
import unittest
from pathlib import Path

import attachments
import bot_research
import decision_log
import league_format
import league_prefs
import pinned_messages
import todo_log

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()


def _build_context_body() -> str:
    start = _APP.index("def build_context(")
    return _APP[start:_APP.index("\ndef ", start + 10)]


class StoresAreScopedToTheRightThingTests(unittest.TestCase):
    def test_the_four_conversation_stores_are_league_scoped_by_path(self):
        """A league id in the path is the strongest scoping available here: one league's file
        cannot be read without naming that league."""
        for module in (todo_log, decision_log, pinned_messages):
            source = inspect.getsource(module._path)
            self.assertIn("league_id", source, f"{module.__name__}._path dropped its league key.")
        self.assertIn("_history.json", _APP)
        self.assertIn("def save_chat_history(league_id: str", _APP)

    def test_league_format_is_keyed_by_league_and_league_prefs_by_user(self):
        """Both live in one shared file and are still correctly scoped — by key rather than by
        path. §13.5 recorded these as 'immediately wrong' under hosting; that was a misreading
        of the path constant, corrected in ARCHITECTURE_AUDIT 12.6."""
        self.assertIn("league_id", list(inspect.signature(league_format.get_format_override).parameters))
        self.assertIn("league_id", list(inspect.signature(league_format.set_format_override).parameters))
        self.assertIn("user_id", list(inspect.signature(league_prefs.get_prefs).parameters))

    def test_a_format_override_set_for_one_league_is_not_visible_from_another(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = league_format.FORMATS_PATH
            league_format.FORMATS_PATH = Path(tmp) / "formats.json"
            try:
                league_format.set_format_override("LEAGUE_A", "Chopped")
                self.assertEqual(league_format.get_format_override("LEAGUE_A"), "Chopped")
                self.assertIsNone(league_format.get_format_override("LEAGUE_B"))
            finally:
                league_format.FORMATS_PATH = saved


class AttachmentScopeIsWiredIntoThePromptTests(unittest.TestCase):
    """The protection §12 asks for, and — unlike §11's certifier — it is actually called."""

    def test_build_context_filters_attachments_by_the_selected_league(self):
        body = _build_context_body()
        self.assertIn("list_attachments(league_id=st.session_state.selected_league_id)", body)

    def test_the_unfiltered_call_sites_are_management_views_only(self):
        """An unfiltered call is fine where nothing reaches a model; pinned so a new unfiltered
        call inside the prompt path is visible."""
        body = _build_context_body()
        self.assertEqual(body.count("list_attachments()"), 0)
        self.assertGreaterEqual(_APP.count("list_attachments()"), 1)

    def test_the_filter_actually_filters(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved_dir, saved_captions = attachments.ATTACHMENTS_DIR, attachments.CAPTIONS_PATH
            attachments.ATTACHMENTS_DIR = Path(tmp)
            attachments.CAPTIONS_PATH = Path(tmp) / "captions.json"
            try:
                attachments.save_attachment("global.txt", b"x", caption="visible everywhere")
                attachments.save_attachment("a_only.txt", b"x", caption="league A", league_ids=["A"])
                attachments.save_attachment("b_only.txt", b"x", caption="league B", league_ids=["B"])

                from_a = {i["filename"] for i in attachments.list_attachments(league_id="A")}
                self.assertEqual(from_a, {"global.txt", "a_only.txt"})
                self.assertNotIn("b_only.txt", from_a)
                # Non-vacuity: unfiltered really does see all three.
                self.assertEqual(len(attachments.list_attachments()), 3)
            finally:
                attachments.ATTACHMENTS_DIR, attachments.CAPTIONS_PATH = saved_dir, saved_captions


class GlobalResearchWithholdsItsPrivateFieldTests(unittest.TestCase):
    """The one globally-shared league-derived store, measured by reach rather than by schema."""

    def _stored(self):
        with tempfile.TemporaryDirectory() as tmp:
            sf, sc = bot_research.FINDINGS_PATH, bot_research.COMPARISONS_PATH
            bot_research.FINDINGS_PATH = Path(tmp) / "f.json"
            bot_research.COMPARISONS_PATH = Path(tmp) / "c.json"
            try:
                bot_research.add_finding(
                    "Some Player", "ESPN", "ESPN has him WR3", rank=3, conviction="Majority",
                    question="Should I sell my WR1 given my 2-6 record?", league_id="LEAGUE_A",
                )
                bot_research.add_comparison(
                    "Player A", "Player B", ">", "ESPN", evidence="ahead in every ballot",
                    question="Who do I start in my must-win week 9?", league_id="LEAGUE_A",
                )
                return bot_research.load_findings()[0], bot_research.load_comparisons()[0]
            finally:
                bot_research.FINDINGS_PATH, bot_research.COMPARISONS_PATH = sf, sc

    def test_the_private_question_and_league_id_are_stored(self):
        """Non-vacuity for the two tests below: the fields do exist to be leaked."""
        finding, comparison = self._stored()
        self.assertIn("question", finding)
        self.assertIn("league_id", finding)
        self.assertEqual(finding["league_id"], "LEAGUE_A")
        self.assertIn("question", comparison)

    def test_neither_reaches_another_leagues_prompt(self):
        body = _build_context_body()
        for expression in ("f['question']", 'f["question"]', "f['league_id']", 'f["league_id"]',
                           "c['question']", 'c["question"]', "c['league_id']", 'c["league_id"]'):
            self.assertNotIn(expression, body, f"{expression} now reaches build_context.")
        # Non-vacuity: the fields that ARE meant to travel do appear.
        for expression in ("f['player_name']", "f['claim']", "c['subject']", "c['evidence']"):
            self.assertIn(expression, body)

    def test_neither_reaches_the_research_panel_in_the_ui(self):
        start = _APP.index("bot_findings = bot_research.load_findings()")
        panel = _APP[start:start + 2000]
        for expression in ('f["question"]', 'f["league_id"]', 'c["question"]', 'c["league_id"]',
                           'f.get("question")', 'f.get("league_id")'):
            self.assertNotIn(expression, panel)
        self.assertIn('f["claim"]', panel)

    def test_the_cross_league_sharing_is_disclosed_where_it_is_shown(self):
        """It is a deliberate design choice, not an accident -- and the UI says so in words."""
        self.assertIn("across every league", _APP)


class GlobalCachesHoldNoTenantDataTests(unittest.TestCase):
    def test_every_cross_session_cache_takes_no_arguments_and_loads_a_static_asset(self):
        """A `@st.cache_resource` is shared by every session on the server. One taking no
        arguments cannot be keyed by league or user, so it is safe only if what it returns
        contains no league or user data -- here, a page icon and a banner image."""
        cached = re.findall(r"@st\.cache_(?:resource|data)\s*\ndef (\w+)\(([^)]*)\)", _APP)
        self.assertEqual({name for name, _ in cached}, {"_page_icon", "_header_banner_data_uri"})
        for name, args in cached:
            self.assertEqual(args.strip(), "", f"{name} gained an argument -- re-check its scope.")
        for name in ("_page_icon", "_header_banner_data_uri"):
            start = _APP.index(f"def {name}(")
            body = _APP[start:start + 400]
            self.assertIn("ASSETS_DIR", body, f"{name} no longer loads a static asset.")
            for leak in ("league", "roster", "user_id", "session_state"):
                self.assertNotIn(leak, body, f"{name} touches {leak} -- a cross-session cache must not.")


class ResearchCannotBeScopedToItsLeagueTests(unittest.TestCase):
    """KNOWN GAP — characterization. Invert when repaired; do not delete."""

    def test_the_context_readers_cannot_filter_by_league(self):
        for reader in (bot_research.findings_for_context, bot_research.comparisons_for_context):
            params = list(inspect.signature(reader).parameters)
            self.assertEqual(params, ["limit"], f"{reader.__name__} gained a scope parameter.")

    def test_league_id_is_recorded_on_every_entry_and_read_by_nothing(self):
        """The field needed for a scope decision is already there; only the decision is
        missing. `attachments` demonstrates the exact pattern in the same codebase."""
        source = inspect.getsource(bot_research)
        self.assertIn('"league_id": league_id', source)
        readers = [
            line for line in source.splitlines()
            if "league_id" in line and ("get(" in line or "==" in line or "if " in line)
            and not line.strip().startswith("#")
        ]
        self.assertEqual(readers, [], "bot_research now reads league_id -- invert this test.")
        # The precedent it would follow:
        self.assertIn("league_id", list(inspect.signature(attachments.list_attachments).parameters))


if __name__ == "__main__":
    unittest.main()
