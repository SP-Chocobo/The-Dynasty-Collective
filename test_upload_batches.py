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


class AMalformedDateMustNotOUTRANKARealOneTests(unittest.TestCase):
    """The defect this parser exists for, measured on the real sort key rather than argued.

    `_negated_date` complements each digit of a date so newer sorts first as a plain string.
    Hand it something that is not an ISO date and it does not fail -- it produces a key that
    lands somewhere arbitrary, and arbitrary is frequently FIRST. Which means a malformed date
    does not merely fail to help: it silently beats every correctly dated source, on a field
    that decides which of two files prices a player.
    """

    def test_the_measurement_that_motivated_this(self):
        """Kept as an executable record, because the numbers are the entire argument. If
        `_negated_date` ever changes, this says loudly that the reasoning needs redoing."""
        import data_merger as dm
        beats_a_real_date = [dm._negated_date(bad) < dm._negated_date("2026-08-18")
                             for bad in ("8/28/26", "202-08-18")]
        self.assertEqual(beats_a_real_date, [True, True],
                         "these malformed dates outrank a correct one -- which is why they are "
                         "refused before they can be stored")

    def test_every_shape_that_is_not_iso_is_refused_rather_than_guessed(self):
        for bad in ("8/28/26", "202-08-18", "last Tuesday", "2026/08/18", "18-08-2026"):
            with self.subTest(raw=bad):
                value, error = ub.parse_as_of(bad)
                self.assertIsNone(value)
                self.assertTrue(error)

    def test_an_impossible_calendar_date_is_refused(self):
        self.assertIsNone(ub.parse_as_of("2026-02-30")[0])

    def test_a_future_date_is_refused_because_it_would_win_forever(self):
        value, error = ub.parse_as_of("2099-01-01")
        self.assertIsNone(value)
        self.assertIn("future", error)

    def test_a_real_iso_date_passes_through_unchanged(self):
        self.assertEqual(ub.parse_as_of("2026-08-18"), ("2026-08-18", None))

    def test_blank_is_not_an_error_it_is_an_answer(self):
        """"I don't know" is a legitimate response and must not be reported as a mistake."""
        for blank in ("", "   ", None):
            with self.subTest(raw=blank):
                self.assertEqual(ub.parse_as_of(blank), (None, None))

    def test_the_ambiguous_case_is_refused_ON_PURPOSE_not_by_omission(self):
        """8/9/26 is August 9th to a US reader and September 8th to most of the world, and
        nothing in the string says which. A parser that guessed would be inventing the exact
        value this field exists to stop inventing -- confidently, on a precedence decision."""
        self.assertIsNone(ub.parse_as_of("8/9/26")[0])
        self.assertIn("two different days", ub.parse_as_of("8/9/26")[1])


class TheStoreItselfRefusesGarbageTests(_Store):
    """Validated at the data layer as well as the UI. The store is what precedence reads, so a
    caller that skipped the form must not be able to poison a tiebreak."""

    def test_an_unparseable_date_is_stored_as_unknown_never_raw(self):
        ub.record(name="x", as_of="8/28/26", files=["a.csv"])
        self.assertIsNone(ub.batches()[0]["as_of"])
        self.assertIsNone(ub.stated_as_of("a.csv"))

    def test_a_valid_date_still_stores(self):
        ub.record(name="x", as_of="2026-08-18", files=["a.csv"])
        self.assertEqual(ub.stated_as_of("a.csv"), "2026-08-18")

    def test_a_poisoning_string_can_never_reach_the_sort_key(self):
        """End to end: the thing the measurement above proved dangerous cannot get in."""
        import data_merger as dm
        ub.record(name="x", as_of="8/28/26", files=["a.csv"])
        stored = ub.batches()[0]["as_of"] or ""
        self.assertGreater(dm._negated_date(stored), dm._negated_date("2026-08-18"),
                           "an unknown date must LOSE to a real one, not beat it")


class TheDateFieldIsAPickerNotATypedStringTests(unittest.TestCase):
    APP = Path("app.py").read_text()

    def test_the_ui_offers_a_picker_so_the_format_question_mostly_disappears(self):
        self.assertIn("st.date_input(", self.APP)

    def test_the_picker_is_paired_with_an_explicit_unknown(self):
        """A bare date_input has no empty state -- it defaults to today, so a field that cannot
        be left blank is a required field wearing an optional label. And today is the one value
        this must never assume, since it would outrank every real source."""
        self.assertIn("I don't know when this data is from", self.APP)

    def test_the_picker_cannot_select_a_future_date(self):
        self.assertIn("max_value=datetime.now().date()", self.APP)

    def test_a_refused_date_is_reported_rather_than_silently_downgraded(self):
        """Dropping quietly to "unknown" would leave a user believing they had dated their
        upload when they had not -- and that belief is load-bearing, because an undated file
        behaves differently in a tiebreak."""
        self.assertIn("Date not recorded —", self.APP)


class TheUploaderAsksForTheBatchNotThePieceTests(unittest.TestCase):
    """The two fields on the way in, and the properties that keep them honest."""

    APP = Path("app.py").read_text()

    def test_the_uploader_takes_several_files_at_once(self):
        self.assertIn("accept_multiple_files=True", self.APP)

    def test_it_asks_what_this_is_and_when_it_is_from(self):
        self.assertIn("What is this? (a name for this set of files)", self.APP)
        self.assertIn("As of what date is this data?", self.APP)

    def test_the_date_field_is_optional_and_says_what_blank_costs(self):
        """A required date gets typed through, and a wrong date is worse than none. Saying what
        blank actually costs is what makes leaving it blank an informed choice rather than a
        shrug. (The field is now a picker plus an explicit unknown -- this asserts the PROPERTY,
        not the widget, which is what the first version of it got wrong.)"""
        self.assertIn("I don't know when this data is from", self.APP)
        self.assertIn("lose a tie to a dated ", self.APP)

    def test_it_asks_for_the_sources_date_not_todays(self):
        self.assertIn("published or computed it", self.APP)
        self.assertIn("not the date you are ", self.APP)

    def test_one_record_is_written_for_the_whole_batch(self):
        self.assertIn("upload_batches.record(", self.APP)
        self.assertEqual(self.APP.count("upload_batches.record("), 1,
                         "one record per upload, written after the loop -- not one per file")

    def test_the_undated_case_is_stated_at_upload_rather_than_discovered_later(self):
        self.assertIn("where these disagree with a dated source, the dated one wins", self.APP)


class TheAmbiguityQueueTests(unittest.TestCase):
    """A single upload can now carry several files, and more than one can need a human call."""

    APP = Path("app.py").read_text()

    def test_pending_uploads_is_a_queue_not_a_slot(self):
        """Assigning to one slot would have silently dropped every ambiguous file but the last
        -- the exact shape of loss this app refuses everywhere else."""
        self.assertIn("st.session_state.pending_uploads.append(", self.APP)
        self.assertNotIn("st.session_state.pending_upload =", self.APP)

    def test_the_queue_is_resolved_oldest_first_one_at_a_time(self):
        self.assertIn("_pending_queue[0] if _pending_queue else None", self.APP)
        self.assertIn("st.session_state.pending_uploads = _pending_queue[1:]", self.APP)

    def test_the_user_is_told_more_are_waiting(self):
        """Discovering a second decision on the next rerun is how the wrong button gets
        pressed."""
        self.assertIn("files from this upload need a decision", self.APP)


class TheReviewSectionGroupsByBatchTests(unittest.TestCase):
    APP = Path("app.py").read_text()

    def test_uploads_are_listed_by_batch_with_their_own_story(self):
        self.assertIn("upload_batches.batches()", self.APP)
        self.assertIn("Your uploads", self.APP)

    def test_a_batch_shows_its_as_of_date_or_says_it_has_none(self):
        self.assertIn("no as-of date", self.APP)
        self.assertIn("loses ties to dated sources", self.APP)

    def test_the_batch_is_the_undo_unit(self):
        self.assertIn("upload_batches.forget(", self.APP)
        self.assertIn("Remove this upload", self.APP)

    def test_files_no_batch_claims_are_named_separately_not_folded_in(self):
        """"I put this here" and "this shipped with the app" are different facts, and the
        committed baseline must not read as something the user uploaded."""
        self.assertIn("Not from any recorded upload", self.APP)

    def test_a_batch_whose_files_are_gone_is_still_shown(self):
        """"I uploaded that and it is not here any more" is a real question, and a silently
        vanished batch cannot answer it."""
        self.assertIn("files no longer on disk", self.APP)

    def test_only_pooled_files_are_recorded_in_a_batch(self):
        """Reference material does not feed precedence, so recording it would make the batch
        claim a scope it does not have."""
        self.assertIn("_batch_files.append(_pool_relpath(", self.APP)
        self.assertNotIn("_batch_files.append(uploaded.name)", self.APP)

    def test_both_ends_agree_on_the_path_spelling(self):
        """A stated as-of date is looked up by path. If app.py and data_merger spell it
        differently the lookup silently never matches, and the date the user typed does
        nothing."""
        self.assertIn("relative_to(Path.cwd().resolve()).as_posix()", self.APP)
        self.assertIn("relative_to(Path.cwd().resolve()).as_posix()",
                      Path("data_merger.py").read_text())
