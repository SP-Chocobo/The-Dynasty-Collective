"""§19.4 / §16.3: an upload is a set of files with one story, and precedence stops guessing.

THE DEAD BRANCH THIS EXISTS TO REVIVE. `_order_by_precedence` sorts on `_negated_date`, which
has always had the correct handling for a file with no date -- *"sorts after any digit-complement,
so undated rows lose to dated ones"*. That branch was **unreachable in production**:
`load_projection_file` filled any absent source_date from the file's mtime, so nothing was ever
undated and the safe path never ran. Measured before removing it: **0 of the committed baseline
files rely on the fallback** -- every one declares its own date -- so it existed purely to guess
on behalf of uploads, which is exactly where guessing is worst and where a user can be asked.

WHY THE BATCH IS THE UNIT, and where that stops being true, is in upload_batches' own docstring.
The short version for a reader here: name/note/as-of are one true statement about a set of files;
FORMAT is not, and stays per-file, because differing by format is the entire purpose of uploading
several at once.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import data_merger as dm
import upload_batches as ub


class _Store(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.dir = Path(self._tmp)
        self._real = ub.BATCHES_PATH
        ub.BATCHES_PATH = self.dir / "_uploads.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmp, ignore_errors=True))
        self.addCleanup(setattr, ub, "BATCHES_PATH", self._real)


class TheThreeDateStatesTests(unittest.TestCase):
    def test_a_stated_date_outranks_one_declared_in_the_file(self):
        """A person who looked at the file outranks a column, because the column can be a
        template default or a copy of a neighbouring export's header -- and the person is the
        one who can be asked about it."""
        self.assertEqual(ub.resolve_source_date("2026-08-28", "2026-08-18"), "2026-08-28")
        self.assertEqual(ub.date_basis("2026-08-28", "2026-08-18"), ub.DATE_STATED)

    def test_a_declared_date_is_used_when_nobody_stated_one(self):
        self.assertEqual(ub.resolve_source_date(None, "2026-08-18"), "2026-08-18")
        self.assertEqual(ub.date_basis(None, "2026-08-18"), ub.DATE_DECLARED)

    def test_no_date_resolves_to_None_and_is_NOT_invented(self):
        """The whole point. None is a real answer the caller must not fill in."""
        self.assertIsNone(ub.resolve_source_date(None, None))
        self.assertEqual(ub.date_basis(None, None), ub.DATE_UNKNOWN)

    def test_an_empty_string_counts_as_absent_not_as_a_date(self):
        self.assertIsNone(ub.resolve_source_date("", ""))
        self.assertEqual(ub.date_basis("", ""), ub.DATE_UNKNOWN)


class TheDeadBranchIsNowReachableTests(_Store):
    """Non-vacuity for the whole change: a file with no date must actually arrive undated."""

    def _undated_csv(self) -> Path:
        path = self.dir / "export(3).csv"
        path.write_text("name,position,team,rank,trade_value\nA Player,WR,CIN,1,90\n")
        return path

    def test_a_file_with_no_date_and_no_batch_loads_undated(self):
        df, _ = dm.load_projection_file(self._undated_csv())
        self.assertEqual(df["source_date"].iloc[0], "")
        self.assertEqual(df["source_date_basis"].iloc[0], ub.DATE_UNKNOWN)

    def test_the_empty_string_is_deliberate_because_load_all_stringifies_it(self):
        """A None here would arrive downstream as the string "None" -- truthy, and therefore
        treated as a date. "" is the only spelling of "no date" that survives that round trip."""
        df, _ = dm.load_projection_file(self._undated_csv())
        self.assertNotEqual(str(df["source_date"].iloc[0]), "None")
        self.assertFalse(str(df["source_date"].iloc[0]))

    def test_stating_a_date_at_upload_reaches_the_loaded_frame(self):
        path = self._undated_csv()
        ub.record(name="Week 3 refresh", as_of="2026-08-28",
                  files=[dm._relative_to_cwd(path)])
        df, _ = dm.load_projection_file(path)
        self.assertEqual(df["source_date"].iloc[0], "2026-08-28")
        self.assertEqual(df["source_date_basis"].iloc[0], ub.DATE_STATED)

    def test_an_undated_row_loses_a_precedence_tie_to_a_dated_one(self):
        """The behaviour `_negated_date` always described and never got to perform."""
        self.assertGreater(dm._negated_date(""), dm._negated_date("2026-08-18"))

    def test_the_committed_baseline_does_not_depend_on_the_removed_fallback(self):
        """Measured, not assumed: every committed file declares its own date, so removing the
        mtime guess changed nothing about the shared baseline."""
        df, _ = dm.load_projection_file(
            Path("data/baseline/rankings/dynasty_ppr_rankings.csv"))
        self.assertEqual(df["source_date_basis"].iloc[0], ub.DATE_DECLARED)
        self.assertTrue(df["source_date"].iloc[0])

    def test_mtime_is_no_longer_consulted_anywhere_in_the_loader(self):
        """EXECUTABLE lines only. The loader's own comment explains what was removed and why,
        and a scan that counted prose would fail on the documentation of the fix -- which is
        both useless and an active incentive to delete the explanation."""
        source = Path("data_merger.py").read_text()
        loader = source[source.index("def load_projection_file("):]
        loader = loader[:loader.index("\ndef ")]
        code = [line.split("#", 1)[0] for line in loader.splitlines()]
        self.assertNotIn("st_mtime", "\n".join(code))
        # Non-vacuity: the explanation IS still there, in the comment the scan now skips.
        self.assertIn("st_mtime", loader)


class TheBatchRecordTests(_Store):
    def test_a_batch_round_trips_with_its_files_and_story(self):
        batch_id = ub.record(name="Week 3 refresh", note="scraped Wednesday",
                             as_of="2026-08-28", files=["a.csv", "b.csv"])
        batch = ub.batches()[0]
        self.assertEqual(batch["id"], batch_id)
        self.assertEqual(batch["name"], "Week 3 refresh")
        self.assertEqual(batch["note"], "scraped Wednesday")
        self.assertEqual(batch["as_of"], "2026-08-28")
        self.assertEqual(batch["files"], ["a.csv", "b.csv"])

    def test_uploaded_at_is_recorded_separately_from_as_of(self):
        """Two different facts. DynastyProcess's own ATTRIBUTION already draws this line: the
        source's scrape_date is not the date the copy was pulled."""
        ub.record(name="x", as_of="2026-01-01", files=["a.csv"])
        batch = ub.batches()[0]
        self.assertEqual(batch["as_of"], "2026-01-01")
        self.assertNotEqual(batch["uploaded_at"], batch["as_of"])

    def test_a_batch_with_no_date_is_still_accepted_and_stays_honest(self):
        """A required date field gets typed through, and a wrong date is worse than an absent
        one because precedence acts on it and is then confidently wrong."""
        ub.record(name="no idea when", files=["a.csv"])
        self.assertIsNone(ub.batches()[0]["as_of"])
        self.assertIsNone(ub.stated_as_of("a.csv"))

    def test_an_unnamed_batch_gets_a_placeholder_rather_than_being_refused(self):
        ub.record(name="   ", files=["a.csv"])
        self.assertEqual(ub.batches()[0]["name"], "Untitled upload")

    def test_batches_come_back_newest_first(self):
        ub.record(name="older", files=["a.csv"])
        ub.record(name="newer", files=["b.csv"])
        self.assertEqual([b["name"] for b in ub.batches()], ["newer", "older"])

    def test_a_re_uploaded_filename_resolves_to_the_newer_batch(self):
        """Re-uploading the same name is a real thing users do, and the later upload is the one
        that describes what is on disk now."""
        ub.record(name="older", as_of="2026-01-01", files=["a.csv"])
        ub.record(name="newer", as_of="2026-08-28", files=["a.csv"])
        self.assertEqual(ub.stated_as_of("a.csv"), "2026-08-28")

    def test_a_file_in_no_batch_has_no_stated_date(self):
        self.assertIsNone(ub.stated_as_of("never-uploaded.csv"))


class ForgetIsTheUndoUnitTests(_Store):
    def test_forget_returns_the_batch_so_the_caller_can_delete_its_files(self):
        batch_id = ub.record(name="x", files=["a.csv", "b.csv"])
        removed = ub.forget(batch_id)
        self.assertEqual(removed["files"], ["a.csv", "b.csv"])
        self.assertEqual(ub.batches(), [])

    def test_forget_does_not_touch_the_filesystem_itself(self):
        """This module owns a record, not a directory. A store that deletes data on another
        layer's behalf makes an undo hard to reason about."""
        source = Path("upload_batches.py").read_text()
        for filesystem in ("unlink", "rmtree", "os.remove"):
            self.assertNotIn(filesystem, source, filesystem)

    def test_forgetting_an_unknown_id_is_a_no_op(self):
        ub.record(name="x", files=["a.csv"])
        self.assertIsNone(ub.forget("nope"))
        self.assertEqual(len(ub.batches()), 1)


class ProseGatesNothingTests(unittest.TestCase):
    def test_the_name_and_note_never_reach_precedence(self):
        """A display name containing "superflex" must not quietly become a format claim -- a
        user would then have to guess a regex's vocabulary to be understood. Stated facts get
        their own field; prose stays prose."""
        source = Path("upload_batches.py").read_text()
        for parsing in ("_detect_rankings_format", "superflex", "te_premium", "scoring"):
            self.assertNotIn(parsing, source.split('"""', 2)[2], parsing)

    def test_format_is_deliberately_not_a_batch_field(self):
        """Differing by format is the entire purpose of uploading several files at once."""
        import inspect
        self.assertNotIn("format", inspect.signature(ub.record).parameters)


if __name__ == "__main__":
    unittest.main()
