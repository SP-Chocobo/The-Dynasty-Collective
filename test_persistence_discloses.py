"""#52 phase 7.5: persistence must not manufacture a success or an absence.

Three findings, one rule. `store_io` declines to overwrite a store it has found damaged --
which is right, and is the repair #102 made -- and it declined IN SILENCE, so every layer above
it was free to report something that had not happened:

  L-11  `upload_batches.record` returned a batch id for a batch that never reached disk.
        Measured: id `5c94a18f5606` handed back, file unchanged, `batches()` unable to find
        that id, UI reporting success. The user's STATED as-of date went with it, which
        precedence acts on -- the file drops from "wins its tiebreaks" to "loses every tie".

  L-05  `outcome_record.load` did its own `json.loads` beside store_io and answered `None` for
        a damaged record and an absent one alike. The ambiguity was not the cost. The cost was
        that a hand-rolled read NEVER ARMS THE DAMAGE MARK, so store_io had nothing to refuse:
        measured on a truncated record holding one real correction, `capture` read
        `existing=None`, wrote `revisions=[]`, and the file was replaced. One revision to zero,
        under a module whose own guarantee is that "a correction is VISIBLE rather than
        silent".

  J-15  the consequence of a declined write was not stated anywhere a caller could read it.

`store_io.unreadable_stores`'s own docstring makes the argument these three break: *"a store
the app quietly works around is exactly the failure that looks handled."*

Every test here builds its own damage in a temp directory rather than asserting on prose.
"""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

import outcome_record
import store_io
import upload_batches

#: Bytes that exist and do not parse -- the shape a torn write or a crash leaves behind, and
#: the ONLY state store_io calls unreadable. Absent and empty are both honestly "nothing yet".
DAMAGED = '[{"id": "real-batch", "name": "Februa'


class _TempStore(unittest.TestCase):
    """A fresh directory and a clean damage registry per test. `_unreadable` is process-global
    by design -- it is what one read tells every later write -- so a test that left a mark
    behind would arm the next one."""

    def setUp(self):
        self._dir = TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)
        store_io.clear_unreadable()
        self.addCleanup(store_io.clear_unreadable)


class AWriteSaysWhetherItLandedTests(_TempStore):

    def test_a_write_to_a_healthy_store_reports_true_and_lands(self):
        path = self.root / "s.json"
        self.assertIs(store_io.write(path, [1, 2, 3]), True)
        self.assertEqual(json.loads(path.read_text()), [1, 2, 3])

    def test_a_write_to_a_damaged_store_reports_false_and_changes_nothing(self):
        path = self.root / "s.json"
        path.write_text(DAMAGED)
        store_io.read(path, [])                      # the read that arms the mark
        self.assertIs(store_io.write(path, [1, 2, 3]), False)
        self.assertEqual(path.read_text(), DAMAGED,
                         "the damaged bytes must survive -- refusing to overwrite is the whole "
                         "point, and the return value is how a caller learns it happened")

    def test_the_refusal_lifts_once_the_file_parses_again(self):
        """Non-vacuity, and the property that keeps this from being a one-way latch: a mark
        that outlived its cause would refuse writes to a file that is now fine."""
        path = self.root / "s.json"
        path.write_text(DAMAGED)
        store_io.read(path, [])
        self.assertIs(store_io.write(path, ["x"]), False)
        path.write_text("[]")                        # repaired out of band
        store_io.read(path, [])
        self.assertIs(store_io.write(path, ["x"]), True)
        self.assertEqual(json.loads(path.read_text()), ["x"])


class DamageAndAbsenceAreDifferentAnswersTests(_TempStore):

    def test_an_absent_store_is_readable(self):
        self.assertEqual(store_io.read_state(self.root / "nope.json", []), ([], True))

    def test_an_empty_store_is_readable(self):
        """An empty file is "nothing stored yet", not damage. Calling it damage would latch the
        refusal on every store that has only ever been touched."""
        path = self.root / "s.json"
        path.write_text("")
        self.assertEqual(store_io.read_state(path, []), ([], True))

    def test_a_damaged_store_is_not_readable(self):
        path = self.root / "s.json"
        path.write_text(DAMAGED)
        self.assertEqual(store_io.read_state(path, []), ([], False))

    def test_a_present_store_is_readable_and_returns_its_contents(self):
        path = self.root / "s.json"
        store_io.write(path, {"a": 1})
        self.assertEqual(store_io.read_state(path, None), ({"a": 1}, True))

    def test_read_and_read_state_cannot_disagree(self):
        """One parser. The finding under L-05 is what a SECOND one costs, so the two entry
        points here must not be able to drift."""
        for contents in (None, "", "[]", DAMAGED, '{"a": 1}'):
            with self.subTest(contents=contents):
                store_io.clear_unreadable()
                path = self.root / "drift.json"
                if contents is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_text(contents)
                state_value = store_io.read_state(path, "DEFAULT")[0]
                store_io.clear_unreadable()
                self.assertEqual(store_io.read(path, "DEFAULT"), state_value)


class AnUnstoredBatchHasNoIdTests(_TempStore):

    def setUp(self):
        super().setUp()
        self._saved = upload_batches.BATCHES_PATH
        upload_batches.BATCHES_PATH = self.root / "batches.json"
        self.addCleanup(setattr, upload_batches, "BATCHES_PATH", self._saved)

    def test_a_batch_that_reached_disk_gets_an_id_that_finds_it(self):
        """The non-vacuity arm, and the contract the id is FOR."""
        batch_id = upload_batches.record(name="March rankings", as_of="2026-03-01",
                                         files=["a.csv"], league_ids=["L1"])
        self.assertIsNotNone(batch_id)
        stored = [b for b in upload_batches.batches() if b["id"] == batch_id]
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["as_of"], "2026-03-01",
                         "the stated as-of date is the thing whose loss is not cosmetic")

    def test_a_batch_that_did_not_reach_disk_gets_no_id(self):
        upload_batches.BATCHES_PATH.write_text(DAMAGED)
        batch_id = upload_batches.record(name="March rankings", as_of="2026-03-01",
                                         files=["a.csv"], league_ids=["L1"])
        self.assertIsNone(batch_id,
                          "an id names a STORED batch; returning one for a batch that was "
                          "never stored is a value where there is an absence")
        self.assertEqual(upload_batches.BATCHES_PATH.read_text(), DAMAGED)

    def test_the_damage_is_surfaceable_rather_than_only_returned(self):
        """A return value only reaches the one caller. The app also needs to be able to TELL
        the person which file is broken, which is what unreadable_stores is for."""
        upload_batches.BATCHES_PATH.write_text(DAMAGED)
        upload_batches.record(name="x", files=["a.csv"])
        self.assertIn(str(upload_batches.BATCHES_PATH), store_io.unreadable_stores())


class ACaptureDoesNotEatTheRevisionTrailTests(_TempStore):

    def _damage(self, season="2026", week=1):
        path = outcome_record.record_path(season, week, self.root)
        path.write_text(path.read_text()[: len(path.read_text()) // 2])
        return path

    def test_a_correction_on_a_healthy_record_still_leaves_a_trail(self):
        """Non-vacuity for everything below: the trail has to exist before losing it can be a
        defect, and the repair must not block an ordinary correction."""
        outcome_record.capture({"p1": {"rec": 5}}, "2026", 1, root=self.root)
        second = outcome_record.capture({"p1": {"rec": 6}}, "2026", 1, root=self.root)
        self.assertEqual(len(second["revisions"]), 1)

    def test_an_absent_week_and_a_damaged_week_are_different_answers(self):
        self.assertEqual(outcome_record.load_state("2026", 9, self.root), (None, True))
        outcome_record.capture({"p1": {"rec": 5}}, "2026", 1, root=self.root)
        self._damage()
        self.assertEqual(outcome_record.load_state("2026", 1, self.root), (None, False))

    def test_reading_a_damaged_record_arms_the_mark_that_protects_it(self):
        """THE HALF THAT MATTERED. The ambiguity above is only uncomfortable; this is what made
        it destructive. store_io can refuse to overwrite only what it has been asked to read,
        and the old hand-rolled loads asked it nothing."""
        outcome_record.capture({"p1": {"rec": 5}}, "2026", 1, root=self.root)
        path = self._damage()
        outcome_record.load("2026", 1, self.root)
        self.assertIn(str(path), store_io.unreadable_stores())

    def test_capturing_over_damage_is_refused_and_the_bytes_survive(self):
        outcome_record.capture({"p1": {"rec": 5}}, "2026", 1, root=self.root)
        outcome_record.capture({"p1": {"rec": 6}}, "2026", 1, root=self.root)
        path = self._damage()
        damaged_bytes = path.read_text()
        with self.assertRaises(ValueError) as caught:
            outcome_record.capture({"p1": {"rec": 7}}, "2026", 1, root=self.root)
        self.assertIn("DAMAGED", str(caught.exception))
        self.assertIn(str(path), str(caught.exception),
                      "the refusal has to name the file, or it cannot be acted on")
        self.assertEqual(path.read_text(), damaged_bytes,
                         "the revision history is still IN those bytes -- that is what makes "
                         "overwriting them a loss rather than a reset")

    def test_an_empty_capture_is_still_refused(self):
        """The module's older refusal, re-run to prove the new one did not displace it."""
        with self.assertRaises(ValueError) as caught:
            outcome_record.capture({}, "2026", 1, root=self.root)
        self.assertIn("EMPTY", str(caught.exception))


class TheListingNamesDamageInsteadOfCrashingTests(_TempStore):

    def test_a_damaged_week_is_reported_and_healthy_weeks_still_list(self):
        """`main --list` raised `TypeError: 'NoneType' object is not subscriptable` on a
        damaged file, which took down the listing of every healthy week with it."""
        saved = outcome_record.RECORD_DIR
        outcome_record.RECORD_DIR = self.root
        self.addCleanup(setattr, outcome_record, "RECORD_DIR", saved)
        outcome_record.capture({"p1": {"rec": 5}}, "2026", 1, root=self.root)
        outcome_record.capture({"p2": {"rec": 9}}, "2026", 2, root=self.root)
        path = outcome_record.record_path("2026", 1, self.root)
        path.write_text(DAMAGED)

        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(outcome_record.main(["--list"]), 0)
        printed = out.getvalue()
        self.assertIn("wk01", printed)
        self.assertIn("DAMAGED", printed)
        self.assertIn("wk02", printed)
        self.assertIn("n=", printed, "the healthy week must still report its real contents")


if __name__ == "__main__":
    unittest.main()
