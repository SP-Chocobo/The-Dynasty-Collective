"""#52 / J-12, ruled NARROW: draft_history records a snapshot when a debate ran on it.

The finding was that this module is **wired to nothing**. Its own docstring calls it "the
substrate for all three (#92)" and "what gives the Prytaneum explicit visibility of which Draft
PickSnapshots exist"; `grep -l draft_history *.py` over non-test files returned only itself.

The sharpest part is what that did to a guard. `test_cdme_ingestion_boundary._NEVER_IMPORTED`
lists this module among those CDME must never import -- correctly, since a stored record read
back into the computation that produced it is a feedback loop. But that assertion was
**trivially true of a store nothing wrote**: a guard passing because its subject is absent,
which is the same shape as an absence assertion passing because the quantity was never
computed. Wiring a writer is what makes that guard mean something, so this file and that one
are a pair.

NARROW, and the alternative is the reason: the Draft Room rebuilds a snapshot on EVERY rerun,
including reruns caused by an unrelated button elsewhere on the page. Recording each one fills
the store with boards nobody looked at. A board someone put to the debate is a decision; a
board that merely rendered is not.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import draft_history
import pick_synthesis as ps
import ui_source


def _candidate(pid: str, name: str):
    """A CandidateSnapshot built from the dataclass's own fields, so this fixture cannot fall
    behind the class the way a hand-written kwargs list does."""
    import dataclasses
    defaults = {"player_id": pid, "name": name, "position": "RB", "team": "PHI"}
    values = {}
    for field in dataclasses.fields(ps.CandidateSnapshot):
        if field.name in defaults:
            values[field.name] = defaults[field.name]
        elif field.default is not dataclasses.MISSING:
            values[field.name] = field.default
        else:
            values[field.name] = 0.0 if field.type in ("float", "Optional[float]") else None
    return ps.CandidateSnapshot(**values)


def _snapshot(label="2.03"):
    return ps.PickSnapshot(
        pick_label=label, round=2, my_roster_id="3",
        candidates=(_candidate("1", "A"), _candidate("2", "B")),
        picks_consumed=14, data_freshest_date="2026-09-01",
    )


class TheStoreHasAWriterTests(unittest.TestCase):
    """Behaviour first: the module works when called. Everything above it was already tested;
    what was missing was anything calling it."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig = draft_history.HISTORY_DIR
        draft_history.HISTORY_DIR = Path(self._tmp.name) / "draft_history"
        self.addCleanup(setattr, draft_history, "HISTORY_DIR", self._orig)

    def test_a_recorded_snapshot_comes_back_under_its_own_identity(self):
        snap = _snapshot()
        sid = ps.snapshot_identity(snap)
        self.assertEqual(draft_history.record_snapshot("L1", snap, sid), sid)
        record = draft_history.load_snapshot_record("L1", sid)
        self.assertIsNotNone(record)
        self.assertEqual(record["evidence"]["pick_label"], "2.03")
        self.assertEqual(record["evidence"]["snapshot_id"], sid)

    def test_recording_the_same_board_twice_adds_nothing(self):
        """Idempotent by content: a rerun that rebuilds an identical board must not grow the
        store, or the narrow rule would leak back into the broad one."""
        snap = _snapshot()
        sid = ps.snapshot_identity(snap)
        draft_history.record_snapshot("L1", snap, sid)
        draft_history.record_snapshot("L1", snap, sid)
        self.assertEqual(draft_history.snapshot_ids("L1"), {sid})

    def test_a_different_board_is_a_different_record(self):
        """Non-vacuity for the test above: the store must still distinguish two real boards, or
        'adds nothing' would be true because it never adds anything."""
        a, b = _snapshot("2.03"), _snapshot("2.04")
        draft_history.record_snapshot("L1", a, ps.snapshot_identity(a))
        draft_history.record_snapshot("L1", b, ps.snapshot_identity(b))
        self.assertEqual(len(draft_history.snapshot_ids("L1")), 2)

    def test_leagues_do_not_share_a_history(self):
        snap = _snapshot()
        sid = ps.snapshot_identity(snap)
        draft_history.record_snapshot("L1", snap, sid)
        self.assertEqual(draft_history.snapshot_ids("L2"), set())


class TheWriterIsOnTheDebATEPathTests(unittest.TestCase):
    """The wiring, over the UI's own syntax tree. A behavioural test cannot reach this: app.py
    runs into session state on import, and the point is WHERE the call sits, not that the
    function works."""

    #: Parsed per UNIT, over the whole surface, so an absent writer is an empty result rather
    #: than an exception. `unit_containing` RAISES when its needle is missing, which made the
    #: unwired case die in setUpClass -- a kill, but the wrong one: the test written to say "no
    #: UI surface writes to draft_history" never ran, and the reader got a lookup error instead
    #: of the sentence. Found by mutation, not by review.
    @classmethod
    def setUpClass(cls):
        cls.trees = {name: ast.parse(src) for name, src in ui_source.units().items()}

    def _first_call(self):
        """The one writer, or a failure that says WHY rather than an IndexError. Three tests
        need it, and an unwired store should read the same in all three."""
        calls = self._calls()
        self.assertTrue(calls, "no UI surface writes to draft_history")
        return calls[0]

    def _calls(self):
        return [(unit, node)
                for unit, tree in sorted(self.trees.items())
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and getattr(node.func, "attr", None) == "record_snapshot"]

    def test_the_ui_records_a_snapshot_at_all(self):
        """The finding itself, inverted. This is the assertion that would have failed for the
        whole life of the module."""
        self.assertTrue(self._calls(), "no UI surface writes to draft_history")

    def test_it_is_recorded_exactly_once_and_not_on_every_board_build(self):
        """NARROW. Two call sites would mean the broad rule crept back in beside the narrow one,
        which is how a store fills with boards nobody looked at."""
        self.assertEqual(len(self._calls()), 1,
                         "draft_history should be written from the debate path only")

    def test_the_call_carries_the_snapshot_identity_rather_than_a_new_name(self):
        """record_snapshot takes the id from its caller on purpose -- so the identity a record
        is filed under is provably the one the caller bound its own result to. Passing anything
        else would file the board under a name nothing else uses."""
        _, call = self._first_call()
        rendered = ast.unparse(call)
        self.assertIn("snapshot_identity", rendered)

    def test_the_record_cannot_take_down_a_live_draft(self):
        """The module's stated contract is that a damaged history file must not break a draft.
        The same has to hold for a failed WRITE: a draft in progress is not the place to
        discover the disk is full."""
        unit, call = self._first_call()
        guarded = [n for n in ast.walk(self.trees[unit])
                   if isinstance(n, ast.Try)
                   and any(c is call for c in ast.walk(n))]
        self.assertTrue(guarded, "the record_snapshot call must be inside a try block")

    def test_the_ingestion_guard_is_no_longer_trivially_satisfied(self):
        """The pair. test_cdme_ingestion_boundary forbids CDME importing this module; that was
        true of a store nothing wrote. It now has a writer, so the ban is a real constraint --
        and CDME still must not import it."""
        import test_cdme_ingestion_boundary as boundary
        self.assertIn("draft_history", boundary._NEVER_IMPORTED)
        for module in boundary._CDME_MODULES:
            self.assertNotIn("import draft_history", Path(module).read_text())


if __name__ == "__main__":
    unittest.main()
