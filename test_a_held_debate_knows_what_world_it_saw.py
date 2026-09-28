"""MANDATE 1.7 / ARCHITECTURE_AUDIT §11.3a: the staleness stamp could not see most of what makes a
board, so a debate was presented as current across changes that rebuild it entirely.

`PickSnapshot` stamped two things -- how many picks had been made, and the merger's freshest source
date -- and `staleness_note` compared exactly those. The Draft Room's reuse gate is `pick_label`, and
`PickDebateResult`'s own comment already said why that is not enough: "the user stays on the clock at
one label while other rosters keep picking, so two materially different boards share a label
routinely". Two worlds it could not tell apart:

  * THE PLAYER POOL. `pool_scope` decides who is in the pool at all (all / rookies only / veterans
    only) and nothing carried it, so a debate reasoned over 59 rookies was shown as current beside a
    970-row all-players board.
  * THE PLAYER UNIVERSE. `data_freshest_date` is the MERGER's date. A Sleeper sync that changes an
    injury status does not move it -- and moves the board by 24.11 points at its own leader
    (measured in test_snapshot_input_key).

ANNOTATE, NEVER DISCARD, unchanged: #101's ruling stands, and these tests check that the sentence
appears, not that the analysis is thrown away. A debate over a board four picks old is usually still
worth reading; what the reader cannot afford is not knowing that is what they are reading.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import pick_debate as pd
import pick_synthesis as ps
import ui_source
from test_pick_debate import _candidate, _snapshot


class _FrozenMerger:
    """Just the one field the staleness check reads, held still so the two new comparisons are the
    only thing that can move."""
    freshest_date = "2026-09-07"


def _result(**overrides):
    """A debate result carrying a world, with nothing else in it that could go stale."""
    fields = dict(pick_label="1.01", snapshot_picks_consumed=0,
                  snapshot_data_freshest_date=_FrozenMerger.freshest_date,
                  snapshot_pool_scope="all", snapshot_players_db_stamp="STAMP-A")
    fields.update(overrides)
    return pd.PickDebateResult(**fields)


class TheSnapshotCarriesTheWholeWorldItWasBuiltFromTests(unittest.TestCase):
    def test_the_snapshot_declares_both_new_fields(self):
        fields = ps.PickSnapshot.__dataclass_fields__
        self.assertIn("pool_scope", fields)
        self.assertIn("players_db_stamp", fields)

    def test_build_snapshot_writes_them_from_its_own_arguments(self):
        """Not from a caller. A stamp a caller supplies is a stamp that can disagree with the board
        it is stapled to, which is the whole class of defect 1.7 is about."""
        source = Path("pick_synthesis.py").read_text()
        build = source[source.index("def build_snapshot("):]
        build = build[:build.index("\ndef ")]
        self.assertIn("pool_scope=pool_scope", build)
        self.assertIn("players_db_stamp=dr._players_db_fingerprint(players_db)", build)

    def test_the_debate_result_copies_them_off_the_snapshot(self):
        source = Path("pick_debate.py").read_text()
        self.assertIn("snapshot_pool_scope=snapshot.pool_scope", source)
        self.assertIn("snapshot_players_db_stamp=snapshot.players_db_stamp", source)


class TheTwoWorldsTheStampCouldNotSeeTests(unittest.TestCase):
    """Value-based, both directions, for each of the two additions."""

    def test_a_pool_scope_change_is_reported(self):
        note = pd.staleness_note(_result(), [], _FrozenMerger(),
                                 live_pool_scope="rookies_only",
                                 live_players_db=None)
        self.assertIsNotNone(note, "a debate run over a different player pool read as current")
        self.assertIn("player pool", note)
        self.assertIn("rookies only", note, "the sentence must name the scope a person recognises")

    def test_the_same_pool_scope_is_not_reported(self):
        """NON-VACUITY: if this also warned, the test above would be about nothing."""
        self.assertIsNone(pd.staleness_note(_result(), [], _FrozenMerger(),
                                            live_pool_scope="all", live_players_db=None))

    def test_a_player_universe_change_is_reported(self):
        stale = _result(snapshot_players_db_stamp="STAMP-FROM-AN-EARLIER-SYNC")
        note = pd.staleness_note(stale, [], _FrozenMerger(), live_pool_scope="all",
                                 live_players_db={"1": {"position": "QB", "injury_status": "Out"}})
        self.assertIsNotNone(note, "a player sync read as current")
        self.assertIn("player universe", note)

    def test_the_same_universe_is_not_reported(self):
        db = {"1": {"position": "QB", "injury_status": None}}
        fresh = _result(snapshot_players_db_stamp=ps.players_db_stamp(db))
        self.assertIsNone(pd.staleness_note(fresh, [], _FrozenMerger(),
                                            live_pool_scope="all", live_players_db=db))

    def test_an_injury_status_change_alone_is_a_different_universe(self):
        """The field the merger's own date cannot see, which is why this exists at all."""
        healthy = {"1": {"position": "QB", "injury_status": None}}
        hurt = {"1": {"position": "QB", "injury_status": "Out"}}
        self.assertNotEqual(ps.players_db_stamp(healthy), ps.players_db_stamp(hurt))
        result = _result(snapshot_players_db_stamp=ps.players_db_stamp(healthy))
        self.assertIsNotNone(pd.staleness_note(result, [], _FrozenMerger(),
                                              live_pool_scope="all", live_players_db=hurt))

    def test_a_caller_that_supplies_no_live_world_asks_exactly_what_it_used_to(self):
        """A stamp with nothing to compare it against is not a comparison, and this function does
        not pretend otherwise -- a draft-history record written before these fields existed must not
        start reading as stale for a world it cannot describe."""
        self.assertIsNone(pd.staleness_note(_result(), [], _FrozenMerger()))
        self.assertIsNone(pd.staleness_note(_result(snapshot_pool_scope=None), [], _FrozenMerger(),
                                            live_pool_scope="rookies_only"))

    def test_the_existing_two_checks_still_fire_and_still_come_first(self):
        """The new comparisons are added, not substituted: a pick made since the debate ran is
        still the first thing said, because it is the one the reader is most likely acting on."""
        note = pd.staleness_note(_result(), [{"player_id": "1"}], _FrozenMerger(),
                                 live_pool_scope="rookies_only", live_players_db=None)
        self.assertIn("new pick(s) made", note)


class TheUIHandsOverTheLiveWorldTests(unittest.TestCase):
    """Both surfaces that hold a debate open: the Draft Room and its Mock Draft twin. Source
    checks, because `app.py`'s import executes the page -- the behaviour they are about is proved
    by value in the class above."""

    def setUp(self):
        self.app = ui_source.text()

    def test_both_call_sites_pass_the_live_pool_scope_and_universe(self):
        calls = [i for i, line in enumerate(self.app.splitlines())
                 if "pick_debate.staleness_note(" in line]
        self.assertEqual(2, len(calls), "a third holder of a debate result appeared -- read it")
        lines = self.app.splitlines()
        for at in calls:
            window = "\n".join(lines[at:at + 5])
            with self.subTest(line=at + 1):
                self.assertIn("live_pool_scope=", window)
                self.assertIn("live_players_db=players_db", window)

    def test_each_site_passes_its_OWN_scope_control(self):
        """The Draft Room and the Mock Draft have separate scope controls, which is exactly why
        crossing them would be worse than not checking at all."""
        self.assertIn("live_pool_scope=st.session_state.draft_room_pool_scope", self.app)
        self.assertIn("live_pool_scope=st.session_state.mock_draft_pool_scope", self.app)


class AStoredRecordCanBeAskedTheSameQuestionTests(unittest.TestCase):
    """MANDATE 1.7, the last of this item's stamp work. `evidence_projection`'s docstring says the
    stamp is "what lets a reader ask snapshot_is_current of a RESTORED record, not just a live one"
    -- and it carried two of the stamp's four fields, so a restored record could be asked whether
    picks had been made and whether the merger's date had moved, and could not be asked whether it
    described the same POPULATION or the same player universe. Two-thirds of a claim.

    `stamp_is_current` already takes those two as optional PAIRS, so a version-2 record on disk asks
    exactly the question it used to rather than reading as stale for a world it cannot describe."""

    def _projection(self):
        import draft_history
        snap = _snap_with_world()
        return draft_history.evidence_projection(snap, "test-identity")

    def test_all_four_stamp_fields_are_in_the_record(self):
        projection = self._projection()
        for field in ("picks_consumed", "data_freshest_date", "pool_scope", "players_db_stamp"):
            with self.subTest(field=field):
                self.assertIn(field, projection)

    def test_they_are_copied_rather_than_recomputed(self):
        """The one thing that function's docstring promises it cannot do is disagree with the board
        it describes, and a re-derived stamp is how that would happen."""
        snap = _snap_with_world()
        import draft_history
        projection = draft_history.evidence_projection(snap, "test-identity")
        self.assertEqual(snap.pool_scope, projection["pool_scope"])
        self.assertEqual(snap.players_db_stamp, projection["players_db_stamp"])

    def test_the_schema_version_moved_rather_than_the_old_records(self):
        """A version-2 record has no such KEY, which is what lets a reader tell "never captured"
        from "captured as absent" -- the distinction that constant exists for."""
        import draft_history
        self.assertEqual(3, draft_history.EVIDENCE_SCHEMA_VERSION)
        self.assertEqual(3, self._projection()["evidence_schema_version"])

    def test_a_restored_record_can_now_be_put_to_the_whole_question(self):
        """End to end, by value: a record written under one world, checked against another."""
        projection = self._projection()
        current, reason = ps.stamp_is_current(
            projection["picks_consumed"], projection["data_freshest_date"], [], _FrozenMerger(),
            pool_scope=projection["pool_scope"], live_pool_scope="rookies_only",
            players_db_stamp=projection["players_db_stamp"],
            live_players_db_stamp=projection["players_db_stamp"])
        self.assertFalse(current)
        self.assertIn("player pool", reason)

    def test_a_record_written_before_these_fields_asks_what_it_used_to(self):
        """NON-VACUITY in the safe direction: an older record must not start reading as stale for a
        world it never captured."""
        current, reason = ps.stamp_is_current(
            0, _FrozenMerger.freshest_date, [], _FrozenMerger(),
            pool_scope=None, live_pool_scope="rookies_only",
            players_db_stamp=None, live_players_db_stamp="ANYTHING")
        self.assertTrue(current, reason)


def _snap_with_world():
    base = _snapshot([_candidate("1", "Brock Purdy")])
    return ps.PickSnapshot(
        pick_label="1.01", round=1, my_roster_id=base.my_roster_id, candidates=base.candidates,
        picks_consumed=0, data_freshest_date=_FrozenMerger.freshest_date,
        pool_scope="all", players_db_stamp="UNIVERSE-A")


if __name__ == "__main__":
    unittest.main()
