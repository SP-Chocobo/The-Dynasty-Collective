import shutil
import tempfile
import unittest
from pathlib import Path

import todo_log


class TodoLogTests(unittest.TestCase):
    """Points TODOS_DIR at a throwaway temp directory for the duration of each test, never
    touching real per-league data under data/todos/ -- that's gitignored, per-user application
    state, not test fixtures."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_todos_dir = todo_log.TODOS_DIR
        todo_log.TODOS_DIR = Path(self._tmpdir)
        self.league_id = "league123"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, todo_log, "TODOS_DIR", self._orig_todos_dir)

    # -- add_todo -----------------------------------------------------------------------

    def test_add_todo_round_trips_and_defaults_to_active(self):
        new_id = todo_log.add_todo(self.league_id, "Target a QB2", source="moderator", question="who to add?")
        self.assertIsNotNone(new_id)
        items = todo_log.load_todos(self.league_id)
        self.assertEqual(len(items), 1)
        entry = items[0]
        self.assertEqual(entry["id"], new_id)
        self.assertEqual(entry["text"], "Target a QB2")
        self.assertEqual(entry["source"], "moderator")
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry["revisions"], [])
        self.assertEqual(entry["notes"], [])

    def test_add_todo_rejects_blank_text_or_league(self):
        self.assertIsNone(todo_log.add_todo(self.league_id, "   "))
        self.assertIsNone(todo_log.add_todo("", "Real text"))
        self.assertEqual(todo_log.load_todos(self.league_id), [])

    def test_ids_increment_within_the_current_list(self):
        first = todo_log.add_todo(self.league_id, "First")
        second = todo_log.add_todo(self.league_id, "Second")
        self.assertEqual(second, first + 1)

    def test_next_id_is_based_on_the_current_max_not_a_persistent_counter(self):
        # _next_id looks at whatever's currently in the list, not a separate persisted
        # counter -- so deleting the highest-numbered entry (delete_todo's own docstring:
        # "meant for a mistaken/duplicate/spam entry") does let the next add reuse that
        # number. Documenting actual behavior here rather than assuming a guarantee that
        # doesn't exist -- in practice a freshly-created, immediately-deleted mistake
        # reusing its own slot number is harmless.
        first = todo_log.add_todo(self.league_id, "First")
        second = todo_log.add_todo(self.league_id, "Second")
        todo_log.delete_todo(self.league_id, second)
        third = todo_log.add_todo(self.league_id, "Third")
        self.assertEqual(third, second)
        self.assertEqual({e["id"] for e in todo_log.load_todos(self.league_id)}, {first, second})

    # -- add_note -----------------------------------------------------------------------

    def test_add_note_round_trips(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.add_note(self.league_id, todo_id, "checked in on this"))
        entry = todo_log.load_todos(self.league_id)[0]
        self.assertEqual(len(entry["notes"]), 1)
        self.assertEqual(entry["notes"][0]["text"], "checked in on this")

    def test_add_note_fails_soft_on_blank_text_or_missing_id(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertFalse(todo_log.add_note(self.league_id, todo_id, "   "))
        self.assertFalse(todo_log.add_note(self.league_id, 9999, "orphan note"))

    # -- revise_todo --------------------------------------------------------------------

    def test_revise_todo_keeps_old_text_in_revisions(self):
        todo_id = todo_log.add_todo(self.league_id, "Original objective")
        self.assertTrue(todo_log.revise_todo(self.league_id, todo_id, "Revised objective", reason="new info"))
        entry = todo_log.load_todos(self.league_id)[0]
        self.assertEqual(entry["text"], "Revised objective")
        self.assertEqual(len(entry["revisions"]), 1)
        self.assertEqual(entry["revisions"][0]["text"], "Original objective")
        self.assertEqual(entry["revisions"][0]["reason"], "new info")

    def test_revise_todo_fails_on_archived_item(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.resolve_todo(self.league_id, todo_id)
        self.assertFalse(todo_log.revise_todo(self.league_id, todo_id, "Too late"))

    def test_revise_todo_rejects_blank_new_text(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertFalse(todo_log.revise_todo(self.league_id, todo_id, "   "))

    # -- mark_likely_resolved / reopen ---------------------------------------------------

    def test_mark_likely_resolved_is_pending_not_final(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.mark_likely_resolved(self.league_id, todo_id, "looks done"))
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ACTIVE_STATUSES)[0]
        self.assertEqual(entry["status"], "likely_resolved")
        self.assertEqual(entry["resolution_reason"], "looks done")
        self.assertIsNone(entry["resolution_date"])  # not actually resolved yet

    def test_mark_likely_resolved_only_valid_from_active(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.mark_likely_resolved(self.league_id, todo_id, "first proposal")
        # Already likely_resolved, not active -- a second proposal should no-op.
        self.assertFalse(todo_log.mark_likely_resolved(self.league_id, todo_id, "second proposal"))

    def test_reopen_clears_the_proposal_and_returns_to_active(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.mark_likely_resolved(self.league_id, todo_id, "looks done")
        self.assertTrue(todo_log.reopen_todo(self.league_id, todo_id))
        entry = todo_log.load_todos(self.league_id)[0]
        self.assertEqual(entry["status"], "active")
        self.assertEqual(entry["resolution_reason"], "")

    def test_reopen_fails_on_an_already_archived_item(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.dismiss_todo(self.league_id, todo_id)
        self.assertFalse(todo_log.reopen_todo(self.league_id, todo_id))

    # -- mark_referenced ------------------------------------------------------------------

    def test_mark_referenced_stamps_without_touching_status(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.mark_referenced(self.league_id, todo_id))
        entry = todo_log.load_todos(self.league_id)[0]
        self.assertIn("last_referenced", entry)
        self.assertEqual(entry["status"], "active")

    def test_mark_referenced_fails_on_missing_id(self):
        self.assertFalse(todo_log.mark_referenced(self.league_id, 9999))

    # -- resolve_todo ---------------------------------------------------------------------

    def test_resolve_todo_directly_from_active(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.resolve_todo(self.league_id, todo_id, "trade completed"))
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)[0]
        self.assertEqual(entry["status"], "resolved")
        self.assertEqual(entry["resolution_reason"], "trade completed")
        self.assertIsNotNone(entry["resolution_date"])

    def test_resolve_todo_confirming_a_likely_resolved_proposal_keeps_its_reason(self):
        # reason=None (not just "") is what means "don't override the bot's proposed reason".
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.mark_likely_resolved(self.league_id, todo_id, "bot's proposed reason")
        self.assertTrue(todo_log.resolve_todo(self.league_id, todo_id, reason=None))
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)[0]
        self.assertEqual(entry["resolution_reason"], "bot's proposed reason")

    def test_resolve_todo_with_no_reason_and_no_prior_proposal_gets_a_default(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.resolve_todo(self.league_id, todo_id, reason=None)
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)[0]
        self.assertEqual(entry["resolution_reason"], "Marked done by user")

    def test_resolve_todo_fails_on_missing_id(self):
        self.assertFalse(todo_log.resolve_todo(self.league_id, 9999))

    # -- dismiss_todo ---------------------------------------------------------------------

    def test_dismiss_todo_archives_with_default_reason(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.dismiss_todo(self.league_id, todo_id))
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)[0]
        self.assertEqual(entry["status"], "dismissed")
        self.assertEqual(entry["resolution_reason"], "Dismissed by user")

    def test_dismiss_todo_with_blank_reason_falls_back_to_default(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.dismiss_todo(self.league_id, todo_id, reason="   ")
        entry = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)[0]
        self.assertEqual(entry["resolution_reason"], "Dismissed by user")

    # -- delete_todo ------------------------------------------------------------------------

    def test_delete_todo_removes_entirely_no_archive_trace(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        self.assertTrue(todo_log.delete_todo(self.league_id, todo_id))
        self.assertEqual(todo_log.load_todos(self.league_id), [])
        self.assertEqual(todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES), [])

    def test_delete_todo_returns_false_for_missing_id(self):
        self.assertFalse(todo_log.delete_todo(self.league_id, 9999))

    # -- load_todos filtering ---------------------------------------------------------------

    def test_load_todos_filters_by_status(self):
        active_id = todo_log.add_todo(self.league_id, "Active one")
        resolved_id = todo_log.add_todo(self.league_id, "Resolved one")
        todo_log.resolve_todo(self.league_id, resolved_id)
        active_only = todo_log.load_todos(self.league_id, statuses=todo_log.ACTIVE_STATUSES)
        archived_only = todo_log.load_todos(self.league_id, statuses=todo_log.ARCHIVED_STATUSES)
        self.assertEqual([e["id"] for e in active_only], [active_id])
        self.assertEqual([e["id"] for e in archived_only], [resolved_id])

    def test_load_todos_on_missing_file_is_empty_list(self):
        self.assertEqual(todo_log.load_todos("nonexistent-league"), [])

    # -- search_archived ----------------------------------------------------------------------

    def test_search_archived_finds_by_keyword_overlap(self):
        todo_id = todo_log.add_todo(self.league_id, "Target Maxx Crosby as a DL2 upgrade")
        todo_log.dismiss_todo(self.league_id, todo_id, reason="Team wasn't willing to trade")
        results = todo_log.search_archived(self.league_id, "Is Maxx Crosby available?")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], todo_id)

    def test_search_archived_ignores_active_items(self):
        todo_log.add_todo(self.league_id, "Target Maxx Crosby as a DL2 upgrade")  # stays active
        results = todo_log.search_archived(self.league_id, "Maxx Crosby")
        self.assertEqual(results, [])

    def test_search_archived_on_blank_query_returns_nothing(self):
        todo_id = todo_log.add_todo(self.league_id, "Objective")
        todo_log.dismiss_todo(self.league_id, todo_id)
        self.assertEqual(todo_log.search_archived(self.league_id, ""), [])
        self.assertEqual(todo_log.search_archived(self.league_id, "   "), [])

    def test_search_archived_ranks_more_overlap_first(self):
        weak_id = todo_log.add_todo(self.league_id, "Consider a trade")
        strong_id = todo_log.add_todo(self.league_id, "Target Maxx Crosby DL trade upgrade")
        todo_log.dismiss_todo(self.league_id, weak_id)
        todo_log.dismiss_todo(self.league_id, strong_id)
        results = todo_log.search_archived(self.league_id, "Target Maxx Crosby DL trade")
        self.assertEqual(results[0]["id"], strong_id)

    # -- forget_todos -------------------------------------------------------------------------

    def test_forget_todos_deletes_the_whole_file(self):
        todo_log.add_todo(self.league_id, "Objective")
        todo_log.forget_todos(self.league_id)
        self.assertEqual(todo_log.load_todos(self.league_id), [])
        self.assertFalse(todo_log._path(self.league_id).exists())

    def test_forget_todos_on_nonexistent_league_does_not_raise(self):
        todo_log.forget_todos("never-existed")  # just must not raise

    # -- corrupt-file resilience ---------------------------------------------------------------

    def test_corrupt_file_fails_soft_to_empty_list_not_a_crash(self):
        path = todo_log._path(self.league_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not valid json")
        self.assertEqual(todo_log.load_todos(self.league_id), [])

    # -- multi-league isolation -----------------------------------------------------------------

    def test_leagues_are_isolated_from_each_other(self):
        todo_log.add_todo("league_a", "A's objective")
        todo_log.add_todo("league_b", "B's objective")
        self.assertEqual(len(todo_log.load_todos("league_a")), 1)
        self.assertEqual(len(todo_log.load_todos("league_b")), 1)
        self.assertEqual(todo_log.load_todos("league_a")[0]["text"], "A's objective")


if __name__ == "__main__":
    unittest.main()
