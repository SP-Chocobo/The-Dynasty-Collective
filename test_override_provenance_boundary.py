"""§16 — human-in-the-loop override provenance.

Three separate guarantees, measured rather than assumed:

  1. When the panel proposes that an objective is done and the USER overrules it, that
     exchange survives in the record. This is the one place in the app where a human
     directly overturns an AI conclusion, and until R13 it erased itself -- reopen_todo
     cleared the only copy of the proposal, leaving an entry byte-identical to one no bot
     had ever spoken about (demonstrated before the repair; see CDME_CONTRACTS.md §16).

  2. Every user-supplied section of the Prytaneum's context announces that it is
     user-supplied. build_context already did this for reference material, past decision
     outcomes and pinned messages; the manual league-format override -- the single
     highest-consequence user override in the app, since it can switch off whole
     categories of advice -- was the one exception (R14).

  3. Characterization of the override path that is NOT repaired here, so a future change to
     it is visible rather than silent: a manual alias re-prices a player and the fact that
     it did never reaches the decision boundary (#107). That test pins today's behavior and
     cites the register item; it is not an endorsement of it.

     #106 -- a research finding that could not say whether it came from a chair's live search
     or the user's own captioned screenshot -- WAS a second characterization here and is now
     settled. Its test is INVERTED rather than deleted (its own earlier note said to delete
     it, and that was wrong: a test that recorded a defect is the exact test that should
     assert the repair). A finding now carries what the provider responses reported
     retrieving, read off their own grounding metadata -- never asked of the model, which
     would have produced a citation whether or not it had one.

app.py is a top-level Streamlit script and cannot be imported (see
test_debate_chip_wiring.py's docstring), so the build_context checks are AST-scoped to that
one function rather than a substring scan of the whole 6,000-line file -- a bare `in`
against the module text would pass on a match anywhere, including a comment.
"""

import ast
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import data_merger as dm
import draft_room
import league_format
import todo_log
import bot_research


_APP_SOURCE = Path(__file__).with_name("app.py").read_text()


def _function_source(name: str) -> str:
    """The source of exactly one top-level function in app.py, by AST span."""
    tree = ast.parse(_APP_SOURCE)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(_APP_SOURCE, node) or ""
    raise AssertionError(f"app.py has no top-level function named {name!r}")


def _string_constants(source: str) -> list[str]:
    return [
        n.value for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
    ]


class _TodoStoreTestCase(unittest.TestCase):
    """Each test gets its own TODOS_DIR -- todo_log writes straight to a module-level path."""

    def setUp(self):
        self._real_dir = todo_log.TODOS_DIR
        self._tmp = tempfile.TemporaryDirectory()
        todo_log.TODOS_DIR = Path(self._tmp.name)
        self.league = "league-under-test"

    def tearDown(self):
        todo_log.TODOS_DIR = self._real_dir
        self._tmp.cleanup()

    def _entry(self, todo_id: int) -> dict:
        entries = todo_log._load(self.league)
        entry = next((e for e in entries if e["id"] == todo_id), None)
        self.assertIsNotNone(entry, f"objective {todo_id} vanished from the store")
        return entry


class ProposalRecordTests(_TodoStoreTestCase):
    def test_a_proposal_is_recorded_with_its_own_timestamp_and_reason(self):
        tid = todo_log.add_todo(self.league, "Trade the 2027 1st", source="moderator")
        todo_log.mark_likely_resolved(self.league, tid, "The pick already moved in a completed trade.")
        proposals = self._entry(tid)["proposals"]
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0]["outcome"], "pending")
        self.assertEqual(proposals[0]["reason"], "The pick already moved in a completed trade.")
        # A proposal with no time of its own cannot answer "when did the panel claim this",
        # which is half of what makes the rejection below meaningful later.
        self.assertIsInstance(proposals[0]["ts"], float)
        self.assertTrue(proposals[0]["date"])

    def test_a_new_objective_starts_with_an_empty_proposal_history(self):
        tid = todo_log.add_todo(self.league, "Stream a DEF in week 12")
        self.assertEqual(self._entry(tid)["proposals"], [])

    def test_user_rejection_is_preserved_not_erased(self):
        tid = todo_log.add_todo(self.league, "Trade the 2027 1st", source="moderator")
        todo_log.mark_likely_resolved(self.league, tid, "Roster data shows this is done.")
        todo_log.reopen_todo(self.league, tid)

        entry = self._entry(tid)
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry["resolution_reason"], "")  # live slot cleared, as before
        # ...but the exchange itself is still readable: what was claimed, when, and that the
        # user said no. This is the assertion that failed before R13.
        self.assertEqual(len(entry["proposals"]), 1)
        self.assertEqual(entry["proposals"][0]["outcome"], "rejected")
        self.assertEqual(entry["proposals"][0]["reason"], "Roster data shows this is done.")
        self.assertTrue(entry["proposals"][0]["closed_date"])

    def test_user_acceptance_is_distinguishable_from_user_rejection(self):
        accepted = todo_log.add_todo(self.league, "A", source="moderator")
        rejected = todo_log.add_todo(self.league, "B", source="moderator")
        todo_log.mark_likely_resolved(self.league, accepted, "looks done")
        todo_log.mark_likely_resolved(self.league, rejected, "looks done")
        todo_log.resolve_todo(self.league, accepted)
        todo_log.reopen_todo(self.league, rejected)
        self.assertEqual(self._entry(accepted)["proposals"][0]["outcome"], "accepted")
        self.assertEqual(self._entry(rejected)["proposals"][0]["outcome"], "rejected")

    def test_dismissal_of_a_proposed_item_is_its_own_outcome(self):
        # "No longer relevant" is a different claim about the world than "yes, that's done."
        tid = todo_log.add_todo(self.league, "Chase the WR2", source="moderator")
        todo_log.mark_likely_resolved(self.league, tid, "looks done")
        todo_log.dismiss_todo(self.league, tid, "Target signed elsewhere.")
        self.assertEqual(self._entry(tid)["proposals"][0]["outcome"], "superseded_by_dismissal")

    def test_repeated_proposals_accumulate_rather_than_overwrite(self):
        tid = todo_log.add_todo(self.league, "Trade the 2027 1st", source="moderator")
        todo_log.mark_likely_resolved(self.league, tid, "first read")
        todo_log.reopen_todo(self.league, tid)
        todo_log.mark_likely_resolved(self.league, tid, "second read, new evidence")
        todo_log.resolve_todo(self.league, tid)
        proposals = self._entry(tid)["proposals"]
        self.assertEqual([p["reason"] for p in proposals], ["first read", "second read, new evidence"])
        self.assertEqual([p["outcome"] for p in proposals], ["rejected", "accepted"])

    def test_closing_an_item_that_was_never_proposed_fabricates_nothing(self):
        # Absent means "no bot ever claimed this was done", never an invented outcome.
        tid = todo_log.add_todo(self.league, "Manual objective", source="manual")
        todo_log.resolve_todo(self.league, tid, "did it myself")
        self.assertEqual(self._entry(tid)["proposals"], [])

    def test_reopen_from_plain_active_fabricates_nothing(self):
        tid = todo_log.add_todo(self.league, "Manual objective")
        todo_log.reopen_todo(self.league, tid)
        self.assertEqual(self._entry(tid)["proposals"], [])

    def test_a_record_written_before_proposals_existed_still_closes_cleanly(self):
        # Every persisted entry in a live install predates this field. Reading one back must
        # neither crash nor invent a proposal history it never had.
        todo_log.TODOS_DIR.mkdir(parents=True, exist_ok=True)
        legacy = {
            "id": 7, "ts": 1.0, "date": "2025-01-01", "text": "legacy", "source": "moderator",
            "question": "", "decision_ts": None, "status": "likely_resolved",
            "resolution_reason": "bot thought so", "resolution_date": None,
            "revisions": [], "notes": [],
        }
        todo_log._path(self.league).write_text(json.dumps([legacy]))
        self.assertTrue(todo_log.reopen_todo(self.league, 7))
        entry = self._entry(7)
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry.get("proposals", []), [])

    def test_proposal_handling_never_touches_the_revision_history(self):
        # revisions tracks the objective's own TEXT changing; proposals track claims about
        # whether it is finished. Two different records, deliberately not one stretched shape.
        tid = todo_log.add_todo(self.league, "original text", source="moderator")
        todo_log.revise_todo(self.league, tid, "revised text", "new info")
        todo_log.mark_likely_resolved(self.league, tid, "looks done")
        todo_log.reopen_todo(self.league, tid)
        entry = self._entry(tid)
        self.assertEqual(len(entry["revisions"]), 1)
        self.assertEqual(entry["revisions"][0]["text"], "original text")
        self.assertEqual(len(entry["proposals"]), 1)

    def test_the_archived_record_can_still_answer_who_what_when_why(self):
        tid = todo_log.add_todo(self.league, "Trade the 2027 1st", source="moderator", question="what now?")
        todo_log.mark_likely_resolved(self.league, tid, "Roster data shows the pick moved.")
        todo_log.resolve_todo(self.league, tid)
        entry = self._entry(tid)
        self.assertEqual(entry["source"], "moderator")                    # who raised it
        self.assertEqual(entry["text"], "Trade the 2027 1st")             # what
        self.assertTrue(entry["resolution_date"])                          # when it closed
        self.assertTrue(entry["proposals"][0]["date"])                     # when it was proposed
        self.assertTrue(entry["resolution_reason"])                        # why it closed
        self.assertEqual(entry["proposals"][0]["outcome"], "accepted")     # who had the last word


class UserSuppliedContextIsLabelledTests(unittest.TestCase):
    """Every user-supplied section of build_context says so in the context itself."""

    @classmethod
    def setUpClass(cls):
        cls.source = _function_source("build_context")
        cls.strings = _string_constants(cls.source)

    def _assert_phrase(self, needle: str):
        self.assertTrue(
            any(needle in s for s in self.strings),
            f"no string constant inside build_context contains {needle!r}",
        )

    def test_reference_material_is_marked_as_the_users_own_caption(self):
        self._assert_phrase("captioned by hand")
        self._assert_phrase("not verified fact")

    def test_past_decision_outcomes_are_marked_user_recorded(self):
        self._assert_phrase("user-recorded, not a guess")

    def test_pinned_messages_are_marked_manual_and_denied_priority(self):
        self._assert_phrase("the user manually flagged these")
        self._assert_phrase("pinning doesn't mean elevated priority")

    def test_the_manual_format_override_is_marked_as_a_user_setting(self):
        # R14. Every other field on build_context's League line is Sleeper's own answer;
        # this one is the user's, and it can switch off whole categories of advice.
        self._assert_phrase("MANUAL SETTING")
        self._assert_phrase("not something detected from Sleeper")

    def test_the_format_label_is_emitted_only_when_an_override_is_actually_set(self):
        # A standing "the user may have set a format" line on every league would be noise,
        # and worse, would describe an override that isn't there.
        tree = ast.parse(self.source)
        guarded = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "special_format"
            and any("MANUAL SETTING" in s for s in _string_constants(ast.unparse(n)))
        ]
        self.assertEqual(len(guarded), 1, "the user-set format label is not guarded by `if special_format:`")

    def test_the_label_precedes_the_strategic_guidance_it_qualifies(self):
        # FORMAT_GUIDANCE speaks in flat imperatives ("never suggest or evaluate a trade
        # here"). The caveat has to arrive first, or the model reads the instruction as
        # established fact and only afterwards learns who supplied it.
        self.assertLess(
            self.source.index("MANUAL SETTING"),
            self.source.index("FORMAT_GUIDANCE[special_format]"),
        )


class FormatOverrideStoreTests(unittest.TestCase):
    def setUp(self):
        self._real = league_format.FORMATS_PATH
        self._tmp = tempfile.TemporaryDirectory()
        league_format.FORMATS_PATH = Path(self._tmp.name) / "league_formats.json"

    def tearDown(self):
        league_format.FORMATS_PATH = self._real
        self._tmp.cleanup()

    def test_no_override_reads_as_absent_not_as_standard(self):
        self.assertIsNone(league_format.get_format_override("lg"))

    def test_setting_standard_clears_rather_than_stores_it(self):
        league_format.set_format_override("lg", league_format.BEST_BALL)
        league_format.set_format_override("lg", league_format.STANDARD)
        self.assertIsNone(league_format.get_format_override("lg"))

    def test_one_leagues_override_never_leaks_into_another(self):
        league_format.set_format_override("lg-a", league_format.CHOPPED)
        self.assertEqual(league_format.get_format_override("lg-a"), league_format.CHOPPED)
        self.assertIsNone(league_format.get_format_override("lg-b"))

    def test_only_non_standard_formats_carry_strategic_guidance(self):
        self.assertNotIn(league_format.STANDARD, league_format.FORMAT_GUIDANCE)
        self.assertTrue(set(league_format.FORMAT_GUIDANCE) <= set(league_format.FORMAT_OPTIONS))


class AliasOverrideReachTests(unittest.TestCase):
    """A manual alias is a real valuation override: it bypasses the automatic matcher's own
    team/position rejection (deliberately -- overriding those guards is the point) and prices
    the player off whatever row the user named. Measured on a synthetic pool so the numbers
    can't drift with a baseline refresh."""

    def setUp(self):
        self._real_path = dm.ALIASES_PATH
        self._tmp = tempfile.TemporaryDirectory()
        dm.ALIASES_PATH = Path(self._tmp.name) / "player_aliases.json"
        self.table = pd.DataFrame([
            {"name": "A Star", "norm_name": dm.normalize_name("A Star"), "team": "CIN",
             "position": "WR", "trade_value": 100.0, "projection": 339.0},
            {"name": "B Backup", "norm_name": dm.normalize_name("B Backup"), "team": "CLE",
             "position": "WR", "trade_value": 41.0, "projection": 202.0},
        ])

    def tearDown(self):
        dm.ALIASES_PATH = self._real_path
        self._tmp.cleanup()

    def _merger(self) -> dm.DataMerger:
        merger = dm.DataMerger.__new__(dm.DataMerger)
        merger.aliases = dm.load_aliases()
        return merger

    def test_an_alias_repoints_a_player_at_a_different_row_and_says_so(self):
        dm.save_alias("B Backup", "A Star")
        match = self._merger().merge_player("B Backup", position="WR", team="CLE", df=self.table)
        self.assertEqual(match["match_path"], "alias")
        self.assertEqual(match["trade_value"], 100.0)   # not 41.0
        self.assertEqual(match["team"], "CIN")          # the alias overrode the team guard

    def test_removing_the_alias_restores_automatic_matching(self):
        dm.save_alias("B Backup", "A Star")
        dm.remove_alias("B Backup")
        match = self._merger().merge_player("B Backup", position="WR", team="CLE", df=self.table)
        self.assertNotEqual(match["match_path"], "alias")
        self.assertEqual(match["trade_value"], 41.0)

    def test_an_alias_naming_a_row_that_does_not_exist_falls_through_rather_than_missing(self):
        dm.save_alias("B Backup", "Nobody At All")
        match = self._merger().merge_player("B Backup", position="WR", team="CLE", df=self.table)
        self.assertTrue(match["matched"])
        self.assertNotEqual(match["match_path"], "alias")

    def test_CHARACTERIZATION_the_override_marker_is_dropped_before_the_decision_boundary(self):
        """#107. build_available_pool carries _match_path onto every pool row, and
        compute_draft_board's explicit output column list drops it -- so a candidate whose
        price rests on a manual alias is indistinguishable, at the decision boundary and in
        every debate downstream of it, from one the matcher resolved on its own.

        Pinned, not endorsed: carrying it through changes the PickSnapshot candidate schema,
        which is an architectural decision parked in the register, not a mechanical repair.
        Delete this test when #107 is settled -- do not "fix" it by loosening the assertion.
        """
        source = Path(__file__).with_name("draft_room.py").read_text()
        tree = ast.parse(source)
        board = next(
            n for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "compute_draft_board"
        )
        emitted: set[str] = set()
        for node in ast.walk(board):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.List):
                emitted.update(
                    e.value for e in node.slice.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)
                )
        # Non-vacuity: this really is reading the board's own output column lists.
        self.assertIn("bpa_source", emitted)
        self.assertIn("universal_value", emitted)
        self.assertNotIn("_match_path", emitted)
        self.assertNotIn("_match_verified", emitted)


class ResearchFindingOriginTests(unittest.TestCase):
    def setUp(self):
        self._real = bot_research.FINDINGS_PATH
        self._tmp = tempfile.TemporaryDirectory()
        bot_research.FINDINGS_PATH = Path(self._tmp.name) / "bot_research.json"

    def tearDown(self):
        bot_research.FINDINGS_PATH = self._real
        self._tmp.cleanup()

    def test_a_findings_composite_impact_is_stated_not_inferred(self):
        """The property is that the row SAYS its impact rather than leaving a reader to infer it
        from whether `rank` is null. 6.2a widened the answer from two to four; each still names
        its own reason, which is the property holding, not an exception to it."""
        numeric = bot_research.add_finding("A Star", "ESPN", "ESPN has him WR4", rank=4)
        qualitative = bot_research.add_finding("B Backup", "ESPN", "ESPN likes the usage trend")
        by_id = {f["id"]: f for f in bot_research.load_findings()}
        self.assertEqual(by_id[numeric]["composite_impact"],
                         "none -- awaiting a second adjudication")
        bot_research.confirm_finding(numeric)
        after = {f["id"]: f for f in bot_research.load_findings()}
        self.assertEqual(after[numeric]["composite_impact"], "low-weight input")
        self.assertEqual(by_id[qualitative]["composite_impact"], "none")

    def test_a_finding_now_records_its_own_origin_INVERTING_the_106_characterization(self):
        """#106, SETTLED -- and this test inverted rather than deleted, which its own earlier
        instruction ("delete this when #106 is settled") got wrong. A test that recorded a defect
        is the exact test that should assert the repair; deleting it leaves the repair unguarded
        by the one check written by someone who understood the failure.

        WHAT IT USED TO SAY. MODERATOR_SYSTEM_PROMPT admits a finding from either a chair's live
        search or the user's own hand-captioned reference material -- explicitly, in the same
        breath ("Whichever way it entered the debate") -- and the stored record had no field for
        which. A rank-bearing finding feeds composite_player_score and the store is git-tracked,
        so a user's own claim could become a durable numeric input attributed only to the outlet
        it cited.

        WHAT SETTLED IT, and why it is not the field this test's old note predicted. The old note
        assumed recording the origin meant adding a field to the Moderator's structured contract
        -- asking the model. That would have been the wrong repair: a chair asked for a citation
        produces one whether or not it has one. What is recorded instead is what the PROVIDER
        RESPONSES reported retrieving, read off their own grounding metadata. No chair contract
        changed.
        """
        fid = bot_research.add_finding(
            "A Star", "ESPN", "ESPN has him WR4", rank=4,
            debate_sources=[{"url": "https://espn.com/x", "title": "X"}])
        stored = next(f for f in bot_research.load_findings() if f["id"] == fid)
        # 7.4 + 6.2a added two fields beside composite_impact, and they belong in this exact
        # list rather than being waved through: this assertion is what stops a finding quietly
        # growing a field nobody decided on.
        self.assertEqual(
            sorted(stored),
            sorted(["id", "ts", "date", "player_name", "source", "claim", "rank",
                    "cited_source_admitted", "adjudication", "composite_impact",
                    "conviction", "question", "league_id", "evidence"]),
        )
        self.assertEqual(stored["evidence"]["origin"], bot_research.ORIGIN_PANEL_RETRIEVED)

    def test_the_rank_bearing_composite_input_is_the_row_that_most_needed_this(self):
        """The specific danger the characterization named: a rank-bearing finding is the one that
        becomes a durable numeric input. Both origins are now legible on exactly that row."""
        retrieved = bot_research.add_finding(
            "A Star", "ESPN", "ESPN has him WR4", rank=4,
            debate_sources=[{"url": "https://espn.com/x", "title": "X"}])
        unattributed = bot_research.add_finding("B Star", "ESPN", "ESPN has him WR9", rank=9)
        bot_research.confirm_finding(retrieved)
        bot_research.confirm_finding(unattributed)
        by_id = {f["id"]: f for f in bot_research.load_findings()}
        self.assertEqual(by_id[retrieved]["composite_impact"], "low-weight input")
        self.assertEqual(by_id[unattributed]["composite_impact"], "low-weight input")
        # The point of the row: origin and composite eligibility are INDEPENDENT. Confirming a
        # finding says a person looked at it; it says nothing about whether the panel reported
        # retrieving a page for it, and 6.2a's gate deliberately does not conflate the two.
        self.assertNotEqual(by_id[retrieved]["evidence"]["origin"],
                            by_id[unattributed]["evidence"]["origin"])


class AiAuthoredStoresCarryTimeTests(unittest.TestCase):
    """Whatever else a record does or doesn't say, it says when it was written. Checked
    against the real function bodies rather than a live write, so a store that quietly stops
    stamping itself is caught even if no test happens to exercise that path."""

    def _writes_a_timestamp(self, module_file: str, func: str) -> bool:
        """True only when a clock call actually lands in a FIELD of a record the function
        builds. Merely calling datetime.now() somewhere in the body isn't enough -- almost
        every one of these functions does that for an unrelated `today`/comparison, so a
        function-wide substring scan would keep passing after the stamp itself was deleted
        (verified by planting exactly that mutation)."""
        source = Path(__file__).with_name(module_file).read_text()
        node = next(
            n for n in ast.walk(ast.parse(source))
            if isinstance(n, ast.FunctionDef) and n.name == func
        )
        clocks = ("time.time()", "datetime.now()")
        for sub in ast.walk(node):
            # A record built as a dict literal: {"ts": time.time(), ...}
            if isinstance(sub, ast.Dict):
                if any(v is not None and any(c in ast.unparse(v) for c in clocks) for v in sub.values):
                    return True
            # ...or assigned field by field: entry["outcome_date"] = datetime.now()...
            if isinstance(sub, ast.Assign) and any(
                isinstance(t, ast.Subscript) for t in sub.targets
            ):
                if any(c in ast.unparse(sub.value) for c in clocks):
                    return True
        return False

    def test_every_ai_authored_record_stamps_itself(self):
        for module_file, func in (
            ("todo_log.py", "add_todo"),
            ("todo_log.py", "mark_likely_resolved"),
            ("todo_log.py", "revise_todo"),
            ("decision_log.py", "log_decision"),
            ("decision_log.py", "set_outcome"),
            ("bot_research.py", "add_finding"),
            ("attachments.py", "save_attachment"),
        ):
            with self.subTest(module=module_file, func=func):
                self.assertTrue(
                    self._writes_a_timestamp(module_file, func),
                    f"{module_file}:{func} writes a record with no time on it",
                )


if __name__ == "__main__":
    unittest.main()
