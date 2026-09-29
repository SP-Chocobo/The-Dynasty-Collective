"""MANDATE 2.2, second half / `#187` -- a board priced on an unreadable league must say so.

The mandate rules one part of 2.2 out as a design question: *a board built on a config the gate
would refuse should not be silently priced.* It was. `league_config.ambiguities` had zero
production callers, so a board built on a league this app could not read cleanly was priced
exactly like one built on a league it could, and nothing downstream -- no surface, no stored
record, no debate -- could tell the two apart.

The verdict now travels ON THE SNAPSHOT, which is where mandate 1.7 put the same kind of fact for
the same reason: written by `build_snapshot` from its own arguments, so it cannot disagree with the
board it qualifies. From there it reaches the person (a warning above the board), the archive (the
stored record), and the chairs (the debate prompt).

TWO THINGS THIS MODULE PINS THAT ARE EASY TO GET WRONG LATER:

  * THREE STATES, NOT TWO (`#187`). `None` means nobody asked. `()` means asked and clean. A
    populated tuple means asked and doubtful. "Nothing was found" and "nothing was checked" are
    opposite claims about whether a board's numbers can be trusted, and a consumer that renders
    them identically tells someone their board is fine when nobody looked.

  * IT IS NOT A STALENESS STAMP. The four stamp fields answer "is this board still CURRENT". This
    answers "may this board be TRUSTED AT ALL". They have different remedies -- rebuild the board
    versus fix the league -- so `stamp_is_current` does not see it, and a board with an unreadable
    config is still correctly reported as current when nothing else has moved.

The POLICY (warn, refuse, or withhold only the terms that depend on the missing key) is the
owner's, recorded as D2 in OWNER_DECISIONS_PENDING.md. `decision_config` still raises for a caller
that wants the hard line. Nothing here asserts which policy is right -- only that the verdict
arrives.
"""

from __future__ import annotations

import ast
import copy
import inspect
import json
import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_history as dh
import draft_history_ui as dhu
import league_config as lc
import pick_debate as pdb
import pick_synthesis as ps
import run_draft_battery as rdb
import ui_source

class _Fixture:
    """Built once: the real capture universe is the only pool that can express a real league."""

    built = False

    @classmethod
    def build(cls):
        if cls.built:
            return
        cls.merger = dm.DataMerger()
        cls.players_db, _provenance = rdb.build_players_db_from_capture()
        capture = json.loads(Path(rdb.CAPTURE_PATH).read_text(encoding="utf-8"))
        scoring = (capture.get("league_shape") or {}).get("scoring_settings")
        cls.clean = next(arm["league"] for arm in db.league_matrix(scoring)
                         if arm["label"] == "12T_ppr")
        cls.merger.set_league_format(db.league_format_hint(cls.clean))
        # TWO ambiguities of DIFFERENT kinds, deliberately: one about a slot the solver cannot
        # fill, one about a key with no safe default. A single-kind fixture would not show that
        # the whole list travels.
        cls.broken = copy.deepcopy(cls.clean)
        cls.broken["settings"] = {}
        cls.broken["roster_positions"] = list(cls.broken["roster_positions"]) + ["OP"]
        cls.pick_order = [str(i) for i in range(1, 13)] * 15
        cls.snap_clean = cls._snap(cls.clean, "1.01")
        cls.snap_broken = cls._snap(cls.broken, "1.02")
        cls.built = True

    @classmethod
    def _snap(cls, league, label):
        return ps.build_snapshot(cls.merger, cls.players_db, [], cls.pick_order, 0, "1", league,
                                 pick_label=label, top_n=4)


def setUpModule():
    _Fixture.build()


def _hand_built():
    """A snapshot nobody built through build_snapshot -- the only kind entitled to say None."""
    return ps.PickSnapshot(pick_label="x", round=1, my_roster_id="1", candidates=())


class TheVerdictIsOnTheSnapshotTests(unittest.TestCase):
    def test_a_readable_league_records_that_it_was_CHECKED_and_clean(self):
        self.assertEqual(_Fixture.snap_clean.config_ambiguities, ())
        self.assertIsNotNone(_Fixture.snap_clean.config_ambiguities,
                             "an empty tuple, never None: this board WAS checked")

    def test_an_unreadable_league_records_every_reason(self):
        found = _Fixture.snap_broken.config_ambiguities
        self.assertTrue(found, "vacuous: the broken fixture produced no ambiguity at all")
        self.assertEqual({kind for kind, _detail in found}, {"unknown_slot", "missing_format_keys"},
                         "the whole list must travel, not just the first finding")
        for _kind, detail in found:
            self.assertTrue(detail.strip(), "an ambiguity reached the snapshot with no explanation")

    def test_it_agrees_exactly_with_the_gate_it_reports(self):
        """Never a second derivation (`#126`): the snapshot must carry what league_config says
        about the same league, or the two can drift and only one of them is wired to a person."""
        for league, snap in ((_Fixture.clean, _Fixture.snap_clean),
                             (_Fixture.broken, _Fixture.snap_broken)):
            self.assertEqual(
                tuple((item["kind"], item["detail"]) for item in lc.ambiguities(league)),
                snap.config_ambiguities)

    def test_a_hand_built_snapshot_says_NOBODY_ASKED(self):
        self.assertIsNone(_hand_built().config_ambiguities)

    def test_the_three_states_are_distinguishable(self):
        """The whole point of the field's type. If `None` and `()` were both falsy-and-equal there
        would be no way to tell an unchecked board from a clean one."""
        never_asked = _hand_built().config_ambiguities
        asked_clean = _Fixture.snap_clean.config_ambiguities
        asked_doubtful = _Fixture.snap_broken.config_ambiguities
        self.assertIsNone(never_asked)
        self.assertEqual(asked_clean, ())
        self.assertTrue(asked_doubtful)
        self.assertNotEqual(never_asked, asked_clean)
        self.assertIsNot(asked_clean, None)

    def test_build_snapshot_writes_it_and_no_caller_can_pass_it(self):
        """Matching 1.7's rule for the stamp fields: a verdict a caller supplies is a verdict that
        can disagree with the league the board was priced on."""
        self.assertNotIn("config_ambiguities",
                         inspect.signature(ps.build_snapshot).parameters)


class ItIsNotAStalenessStampTests(unittest.TestCase):
    def test_stamp_is_current_does_not_take_the_config_verdict(self):
        params = inspect.signature(ps.stamp_is_current).parameters
        self.assertNotIn("config_ambiguities", params)
        self.assertNotIn("live_config_ambiguities", params)

    def test_a_board_on_a_doubtful_config_is_still_CURRENT_when_nothing_moved(self):
        """Because the two questions have different remedies. Reporting this board as stale would
        send a person to rebuild it, which changes nothing -- the league is what needs fixing."""
        current, reason = ps.stamp_is_current(
            _Fixture.snap_broken.picks_consumed,
            _Fixture.snap_broken.data_freshest_date, [], _Fixture.merger,
            pool_scope=_Fixture.snap_broken.pool_scope,
            live_pool_scope=_Fixture.snap_broken.pool_scope,
            players_db_stamp=_Fixture.snap_broken.players_db_stamp,
            live_players_db_stamp=_Fixture.snap_broken.players_db_stamp,
        )
        self.assertTrue(current, f"a doubtful config was reported as staleness: {reason}")
        self.assertIsNone(reason)


class TheArchiveKeepsItTests(unittest.TestCase):
    """A stored board is a board someone reads prices from, so the caveat has to survive the
    write -- otherwise a replay silently loses the one thing qualifying every number in it."""

    @staticmethod
    def _projection(snapshot, snapshot_id):
        for name in ("snapshot_evidence", "snapshot_projection", "evidence_projection"):
            if hasattr(dh, name):
                return getattr(dh, name)(snapshot, snapshot_id)
        raise AssertionError("draft_history exposes no snapshot projection function")

    def test_the_schema_version_moved_rather_than_the_old_records(self):
        """A floor, not an equality: a version-4 record has no such KEY at all, which is what lets
        a reader tell "never captured" from "captured as clean"."""
        self.assertGreaterEqual(dh.EVIDENCE_SCHEMA_VERSION, 5)
        record = self._projection(_Fixture.snap_clean, "sid-clean")
        self.assertEqual(record["evidence_schema_version"], dh.EVIDENCE_SCHEMA_VERSION,
                         "a record must carry the version the module declares")

    def test_all_three_states_survive_the_write_distinguishably(self):
        clean = self._projection(_Fixture.snap_clean, "sid-clean")["config_ambiguities"]
        doubtful = self._projection(_Fixture.snap_broken, "sid-bad")["config_ambiguities"]
        unasked = self._projection(_hand_built(), "sid-hand")["config_ambiguities"]
        self.assertEqual(clean, [], "a checked-and-clean board must store an empty list")
        self.assertIsNone(unasked, "an unchecked board must store null, not an empty list")
        self.assertTrue(doubtful)

    def test_each_stored_ambiguity_is_a_NAMED_object_not_a_bare_pair(self):
        """JSON cannot tell a two-element tuple from a two-element list on the way back, so the
        shape is explicit. Reshaped for the medium, never recomputed."""
        stored = self._projection(_Fixture.snap_broken, "sid-bad")["config_ambiguities"]
        for item in stored:
            self.assertEqual(sorted(item), ["detail", "kind"])
        self.assertEqual([item["kind"] for item in stored],
                         [kind for kind, _ in _Fixture.snap_broken.config_ambiguities])

    def test_the_record_is_json_round_trippable(self):
        record = self._projection(_Fixture.snap_broken, "sid-bad")
        again = json.loads(json.dumps(record))
        self.assertEqual(again["config_ambiguities"], record["config_ambiguities"])


class TheStoredBoardReaderSurfacesItTests(unittest.TestCase):
    @staticmethod
    def _summary(snapshot):
        projection = TheArchiveKeepsItTests._projection(snapshot, "sid")
        return dhu.record_summary({"snapshot_id": "sid", "evidence": projection},
                                  [], _Fixture.merger)

    def test_a_doubtful_stored_board_reports_its_reasons(self):
        row = self._summary(_Fixture.snap_broken)
        self.assertTrue(row["config_ambiguities"])
        self.assertEqual([item["kind"] for item in row["config_ambiguities"]],
                         [kind for kind, _ in _Fixture.snap_broken.config_ambiguities])

    def test_a_clean_stored_board_reports_an_empty_list_and_not_None(self):
        self.assertEqual(self._summary(_Fixture.snap_clean)["config_ambiguities"], [])

    def test_a_record_written_before_the_check_existed_reports_None(self):
        self.assertIsNone(self._summary(_hand_built())["config_ambiguities"])


class TheChairsAreToldTests(unittest.TestCase):
    def test_the_prompt_carries_the_warning_and_every_reason(self):
        block = pdb.format_snapshot_for_llm(_Fixture.snap_broken)
        self.assertIn("DID NOT PARSE CLEANLY", block)
        for _kind, detail in _Fixture.snap_broken.config_ambiguities:
            self.assertIn(detail, block, "a reason reached the snapshot but not the debate")

    def test_the_warning_sits_above_the_candidates_it_qualifies(self):
        """It qualifies every number below it, so a chair must meet it before the first one."""
        block = pdb.format_snapshot_for_llm(_Fixture.snap_broken)
        self.assertLess(block.index("DID NOT PARSE CLEANLY"), block.index("CANDIDATE:"))

    def test_a_clean_config_says_nothing(self):
        self.assertNotIn("DID NOT PARSE CLEANLY",
                         pdb.format_snapshot_for_llm(_Fixture.snap_clean))

    def test_an_UNCHECKED_snapshot_also_says_nothing(self):
        """Silent for the opposite reason: there is no standing to reassure. The absence of a
        warning is not a claim that the config was read."""
        self.assertNotIn("DID NOT PARSE CLEANLY",
                         pdb.format_snapshot_for_llm(_hand_built()))


class ThePersonSeesItAboveTheBoardTests(unittest.TestCase):
    """Read from the AST rather than the text (`#200`): a substring search would be satisfied by
    the field's name appearing in a comment.

    Through `ui_source.units`, never `app.py` off disk. The UI is one module today, so the two are
    the same bytes -- but a view extracted into its own file tomorrow would silently drop out of an
    app.py read, and this check would go on passing while covering nothing. Each unit is parsed
    separately because `ui_source.text` joins them with boundary markers that are not Python."""

    @classmethod
    def setUpClass(cls):
        cls.trees = {name: ast.parse(source)
                     for name, source in ui_source.units().items()}

    def _nodes(self):
        for name, tree in self.trees.items():
            for node in ast.walk(tree):
                yield name, node

    def test_the_draft_room_reads_the_verdict_off_the_snapshot(self):
        reads = [name for name, node in self._nodes()
                 if isinstance(node, ast.Attribute) and node.attr == "config_ambiguities"]
        self.assertTrue(reads,
                        "no UI module reads config_ambiguities, so a board priced on an unreadable "
                        "league is still silently priced")

    def test_it_is_read_from_a_snapshot_and_not_rederived_in_the_view(self):
        """The view must not call the gate itself -- a second call site is a second answer that
        can disagree with the board actually on screen (`#126`)."""
        called = [f"{name}: {node.func.attr}" for name, node in self._nodes()
                  if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and node.func.attr in ("ambiguities", "admits_decision")]
        self.assertEqual(called, [],
                         f"a UI module derives the config verdict itself instead of reading the one "
                         f"the snapshot was built with: {called}")


if __name__ == "__main__":
    unittest.main()
