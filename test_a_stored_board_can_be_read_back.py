"""MANDATE 1.7 / `#92` (the last limb, owner-delegated): `draft_history` was write-only IN THE APP.

The module's readers — `load_snapshot_record`, `list_snapshot_records`, `snapshot_ids` — have always
worked. `app.py` called `record_snapshot` and nothing else, so a store the Prytaneum was told gave it
"explicit visibility of which Draft PickSnapshots exist" was visible to nobody.

The mandate called closing it properly a FEATURE, not a defect fix, because it needed a product
decision: may a replayed board look like a live one? The owner delegated the call and the answer built
here is NO, unconditionally. `draft_history_ui` lists what is stored with each board's staleness
verdict for this moment, and shows one board's candidate table on request. No panel is replayed, no
debate re-runs, nothing is recomputed.

What these tests hold is the three places a reader could quietly lie about a record:

  * by reimplementing the staleness rule instead of asking `stamp_is_current`;
  * by letting a record that CANNOT answer a stamp question answer it with silence;
  * by dropping an unreadable file and showing a shorter list.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import draft_history
import draft_history_ui as dhui
import pick_synthesis


class _Merger:
    """The one thing `stamp_is_current` asks a merger: `freshest_date`, as an attribute."""

    def __init__(self, date="2026-09-01"):
        self.freshest_date = date


def _candidate(**over):
    row = {name: None for name in draft_history._CANDIDATE_EVIDENCE_FIELDS}
    row.update({"player_id": "1", "name": "A Player", "position": "WR", "team": "KC"})
    row.update(over)
    return row


def _record(snapshot_id="s1", *, schema=3, picks_consumed=10, date="2026-09-01",
            pool_scope="capture", players_db_stamp="abc", candidates=None, ts=1.0):
    evidence = {
        "evidence_schema_version": schema,
        "snapshot_id": snapshot_id,
        "pick_label": "1.05",
        "round": 1,
        "my_roster_id": "3",
        "decision_regime": "balanced",
        "user_selected_player_id": None,
        "picks_consumed": picks_consumed,
        "data_freshest_date": date,
        "candidate_count": len(candidates or []),
        "candidates": candidates or [],
    }
    if schema >= 3:
        evidence["pool_scope"] = pool_scope
        evidence["players_db_stamp"] = players_db_stamp
    return {"snapshot_id": snapshot_id, "league_id": "L1", "draft_id": "D1", "ts": ts,
            "date": "2026-09-02", "evidence": evidence}


class TheVerdictIsNotReimplementedHere(unittest.TestCase):
    """A second copy of a staleness rule that is supposed to agree with the first is the drift class
    this app keeps finding. `stamp_is_current` exists so a restored record can ask the live
    question, and this reader has to be the thing that calls it."""

    def setUp(self):
        self.merger = _Merger("2026-09-01")
        self.picks = [{"player_id": str(i)} for i in range(10)]

    def test_a_record_matching_the_world_reads_as_current(self):
        row = dhui.record_summary(_record(), self.picks, self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="abc")
        self.assertTrue(row["current"], row["reason"])
        self.assertIsNone(row["reason"])

    def test_a_new_pick_makes_it_stale_with_the_reason_the_engine_gives(self):
        row = dhui.record_summary(_record(), self.picks + [{"player_id": "99"}], self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="abc")
        self.assertFalse(row["current"])
        expected = pick_synthesis.stamp_is_current(
            10, "2026-09-01", self.picks + [{"player_id": "99"}], self.merger,
            pool_scope="capture", live_pool_scope="capture",
            players_db_stamp="abc", live_players_db_stamp="abc")[1]
        self.assertEqual(row["reason"], expected,
                         "the reason was reworded here instead of being passed through")

    def test_it_really_delegates(self):
        """Structural, not behavioural: the verdict must come FROM that function. A reader that
        happened to agree today could stop agreeing the day the rule gains a fourth comparison."""
        with mock.patch.object(pick_synthesis, "stamp_is_current",
                               return_value=(False, "sentinel reason")) as spy:
            row = dhui.record_summary(_record(), self.picks, self.merger)
        self.assertTrue(spy.called)
        self.assertEqual(row["reason"], "sentinel reason")

    def test_a_moved_player_universe_is_caught_for_a_schema_3_record(self):
        row = dhui.record_summary(_record(), self.picks, self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="DIFFERENT")
        self.assertFalse(row["current"])


class ARecordThatCannotAnswerSaysSo(unittest.TestCase):
    """`stamp_is_current` skips a comparison it has no live counterpart for, which is correct and
    SILENT. Silence about "did the pool change" reads as "the pool did not change"."""

    def setUp(self):
        self.merger = _Merger("2026-09-01")
        self.picks = [{"player_id": str(i)} for i in range(10)]

    def test_a_complete_record_has_nothing_it_cannot_be_asked(self):
        row = dhui.record_summary(_record(schema=3), self.picks, self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="abc")
        self.assertEqual(row["unanswerable"], [])

    def test_a_record_from_before_the_stamp_was_completed_names_both_gaps(self):
        row = dhui.record_summary(_record(schema=2), self.picks, self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="abc")
        self.assertEqual(sorted(row["unanswerable"]), sorted([
            dhui.STAMP_QUESTIONS["pool_scope"], dhui.STAMP_QUESTIONS["players_db_stamp"]]))

    def test_and_it_does_not_read_as_stale_for_lacking_them(self):
        """The gap is a gap, not a change. Reporting an old record as STALE would be the mirror
        error -- asserting the world moved on no evidence either way."""
        row = dhui.record_summary(_record(schema=2), self.picks, self.merger,
                                  live_pool_scope="capture", live_players_db_stamp="abc")
        self.assertTrue(row["current"])
        self.assertTrue(row["unanswerable"])

    def test_every_stamp_field_has_a_question_a_reader_can_read(self):
        """Non-vacuity: the map has to cover the stamp, or a future field goes unreported."""
        for field in ("picks_consumed", "data_freshest_date", "pool_scope", "players_db_stamp"):
            self.assertIn(field, dhui.STAMP_QUESTIONS)
            self.assertTrue(dhui.STAMP_QUESTIONS[field].strip())


class AnUnreadableRecordIsCountedNotDropped(unittest.TestCase):
    """`list_snapshot_records` skipping a damaged file is right — a corrupt history must not take
    down a live draft — and invisible. The caller sees a shorter list, not a problem."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        patcher = mock.patch.object(draft_history, "HISTORY_DIR", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.merger = _Merger("2026-09-01")
        self.picks = [{"player_id": str(i)} for i in range(10)]

    def _write(self, snapshot_id, payload):
        directory = draft_history._scope_dir("L1")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{snapshot_id}.json").write_text(payload)

    def test_a_league_with_no_history_is_empty_not_missing(self):
        out = dhui.league_history("L1", self.picks, self.merger)
        self.assertEqual(out["rows"], [])
        self.assertEqual(out["stored_count"], 0)
        self.assertEqual(out["unreadable_count"], 0)

    def test_two_good_records_come_back_newest_first(self):
        self._write("older", json.dumps(_record("older", ts=1.0)))
        self._write("newer", json.dumps(_record("newer", ts=2.0)))
        out = dhui.league_history("L1", self.picks, self.merger)
        self.assertEqual([r["snapshot_id"] for r in out["rows"]], ["newer", "older"])
        self.assertEqual(out["unreadable_count"], 0)

    def test_a_damaged_file_is_reported_rather_than_vanishing(self):
        self._write("good", json.dumps(_record("good")))
        self._write("broken", "{not json at all")
        out = dhui.league_history("L1", self.picks, self.merger)
        self.assertEqual([r["snapshot_id"] for r in out["rows"]], ["good"])
        self.assertEqual(out["stored_count"], 2)
        self.assertEqual(out["unreadable_count"], 1,
                         "the damaged record was dropped silently, which is what this exists for")

    def test_a_limit_shortens_the_display_without_changing_the_count(self):
        for i in range(4):
            self._write(f"s{i}", json.dumps(_record(f"s{i}", ts=float(i))))
        out = dhui.league_history("L1", self.picks, self.merger, limit=2)
        self.assertEqual(len(out["rows"]), 2)
        self.assertEqual(out["stored_count"], 4,
                         "a display limit must not be reported as how much is stored")


class AStoredBoardNeverLooksLive(unittest.TestCase):
    """The product question 1.7 left open, answered in one unconditional string and in what the
    table is allowed to contain."""

    def test_the_notice_says_it_is_stored_and_that_nothing_was_recomputed(self):
        notice = dhui.STORED_BOARD_NOTICE
        self.assertIn("STORED", notice)
        self.assertIn("recomputed", notice)
        self.assertIn("not advice", notice)

    def test_the_rows_keep_the_order_they_were_recorded_in(self):
        """Re-sorting a stored table would make it a NEW board. It is what was on the screen."""
        record = _record(candidates=[
            _candidate(player_id="1", name="First", team_acquisition_value=10.0),
            _candidate(player_id="2", name="Second", team_acquisition_value=99.0),
        ])
        rows = dhui.stored_candidate_rows(record)
        self.assertEqual([r["Player"] for r in rows], ["First", "Second"])

    def test_an_absent_quantity_keeps_the_absence_mark_and_never_becomes_a_zero(self):
        record = _record(candidates=[_candidate(need_bonus=None, positional_forfeit=None)])
        row = dhui.stored_candidate_rows(record)[0]
        self.assertEqual(row["Need"], dhui.ABSENT)
        self.assertEqual(row["Forfeit"], dhui.ABSENT)
        self.assertNotIn("0.00", (row["Need"], row["Forfeit"]))

    def test_a_measured_zero_is_still_shown_as_a_zero(self):
        """The other side of `#187`: absence and a measured zero must not collapse either way."""
        record = _record(candidates=[_candidate(need_bonus=0.0)])
        self.assertEqual(dhui.stored_candidate_rows(record)[0]["Need"], "0.00")

    def test_a_withheld_quantity_is_withheld_coming_off_disk_too(self):
        record = _record(candidates=[_candidate(survival_probability=0.42)])
        with mock.patch.object(pick_synthesis, "withheld_fields",
                               return_value=frozenset({"survival_probability"})):
            row = dhui.stored_candidate_rows(record)[0]
        self.assertEqual(row["Survival"], pick_synthesis.WITHHELD_CARD_TEXT)
        self.assertNotIn("0.42", row["Survival"])

    def test_and_shown_when_it_is_not_withheld(self):
        """Non-vacuity for the test above: the withheld arm must not be the only arm."""
        record = _record(candidates=[_candidate(survival_probability=0.42)])
        with mock.patch.object(pick_synthesis, "withheld_fields", return_value=frozenset()):
            row = dhui.stored_candidate_rows(record)[0]
        self.assertEqual(row["Survival"], "0.420")

    def test_a_record_with_no_candidates_yields_no_rows_rather_than_raising(self):
        self.assertEqual(dhui.stored_candidate_rows(_record()), [])
        self.assertEqual(dhui.stored_candidate_rows({}), [])

    def test_every_displayed_column_is_a_field_the_store_actually_keeps(self):
        """A column naming a field `candidate_evidence` does not store would render as absent
        forever and read as an unmeasured quantity."""
        stored = set(draft_history._CANDIDATE_EVIDENCE_FIELDS)
        for field, _heading, _digits in dhui.CANDIDATE_COLUMNS:
            self.assertIn(field, stored, f"{field} is displayed but never recorded")


class TheSURFACEActuallyCallsIt(unittest.TestCase):
    """The whole defect was that the readers had no caller. A module full of green unit tests and no
    call site would close nothing, so this reads the UI surface -- through `ui_source`, never by
    naming a file, because the read stops covering anything the moment a view is extracted."""

    @classmethod
    def setUpClass(cls):
        import ui_source
        cls.source = ui_source.text()
        cls.code = ui_source.code_text() if hasattr(ui_source, "code_text") else cls.source

    def test_the_draft_room_asks_for_this_leagues_stored_boards(self):
        self.assertIn("draft_history_ui.league_history(", self.source)

    def test_it_shows_the_stored_board_notice_rather_than_composing_its_own(self):
        self.assertIn("draft_history_ui.STORED_BOARD_NOTICE", self.source,
                      "the surface wrote its own wording, so the one that is tested is not the one "
                      "a person reads")

    def test_it_renders_the_stored_rows_through_the_module(self):
        self.assertIn("draft_history_ui.stored_candidate_rows(", self.source)

    def test_it_passes_the_LIVE_pool_scope_and_player_universe(self):
        """A staleness verdict is only a comparison if both sides are supplied. The two-field stamp
        era is exactly what `unanswerable` exists to report; a surface that held the live values and
        did not pass them would manufacture that silence."""
        self.assertIn("live_pool_scope=", self.source)
        self.assertIn("live_players_db_stamp=", self.source)

    def test_it_reports_the_records_it_could_not_read(self):
        self.assertIn("unreadable_count", self.source)

    def test_it_names_what_an_older_record_cannot_be_asked(self):
        self.assertIn("unanswerable", self.source)


class WhatTheRenderTraceCoversAndWhatItCannot(unittest.TestCase):
    """The reader is REACHED -- the trace proves that, which a source check cannot. What the trace
    cannot do is exercise the populated table, and saying so is the point of this class.

    `draft_history` reads records off disk, not out of session state, so the trace fixture's league
    has no stored boards and the instrument records the EMPTY branch: the expander, and the caption
    that says nothing is stored yet. Seeding a record would mean writing a history file into the
    repository to make an instrument look better, which is the wrong trade.

    So the populated path is covered by this module's unit tests over `stored_candidate_rows` and by
    the source checks above, and the trace covers that the surface exists and opens. Three partial
    instruments whose boundaries are written down beat one that is assumed to be total."""

    @classmethod
    def setUpClass(cls):
        cls.trace = json.loads(Path("RENDER_TRACE.json").read_text())
        cls.calls = cls.trace["calls"] if isinstance(cls.trace, dict) else cls.trace

    def test_the_draft_room_really_renders_the_stored_boards_expander(self):
        hits = [c for c in self.calls if "Boards stored for this league" in c]
        self.assertTrue(hits, "the reader is not reached on any traced pass")
        self.assertTrue(all("Draft Room" in c for c in hits),
                        "the reader appeared outside the Draft Room, which is not where it is wired")

    def test_the_traced_pass_is_the_EMPTY_one_and_that_is_recorded_here(self):
        """If this ever fails because the trace gained the populated table, that is good news and
        this test is what tells you the coverage boundary moved -- rewrite it, do not delete it."""
        self.assertFalse([c for c in self.calls if "Stored board" in c],
                         "the trace now covers the populated path; update this class's docstring")


if __name__ == "__main__":
    unittest.main()
