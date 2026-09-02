"""#102: the read-modify-write discipline every JSON store now shares.

TWO FAILURES, BOTH DEMONSTRATED BEFORE ANYTHING WAS BUILT. §7.8's standing rule is that this
programme does not make production changes for undemonstrated failures, and one half of #102 was
recorded as undemonstrated -- so it was demonstrated first, on real files, through the real
functions, and then repaired.

  LOST UPDATE. Re-measured on the PRODUCTION call path rather than the audit's hand-interleaved
  one -- 8 concurrent processes calling the real public functions 25 times each. Before:
  todo_log.add_todo kept 6 of 200 and data_merger.save_alias kept 9 of 200. Not an edge case
  under contention: 97% and 95% loss. After: 200 of 200 for both.

  TORN READ -- newly demonstrated, and the worse half. One process rewriting a 718 KB store while
  three read it: of 98,405 reads, 3,920 were clean; the rest raised JSONDecodeError or read an
  empty file, because write_text truncates before it writes. Every _load in this tree swallowed
  that and returned [], and the next ordinary write persisted the empty view -- measured end to
  end, a store holding five objectives held exactly one after a single torn read and one
  add_todo. No race between two writers required. After: 0 torn reads in the same harness.

WHAT THIS FILE PINS. The primitive's own contract. The end-to-end demonstrations above are
process-level and live in POST_AUDIT_PLAN; what is here is cheap, deterministic, and fails if any
of the three mechanisms (atomic replace, the lock, the do-not-overwrite-damage guard) is removed.
"""

import inspect
import json
import multiprocessing as mp
import tempfile
import threading
import unittest
from pathlib import Path

import store_io
import ui_source


def _tmp(name="store.json"):
    directory = tempfile.TemporaryDirectory()
    return directory, Path(directory.name) / name


class ReadWriteContractTests(unittest.TestCase):
    def setUp(self):
        self._dir, self.path = _tmp()
        store_io.clear_unreadable()

    def tearDown(self):
        self._dir.cleanup()
        store_io.clear_unreadable()

    def test_a_missing_file_and_an_empty_file_are_both_the_default(self):
        """Neither is damage: "nothing stored yet" is a legitimate state, and treating it as
        damage would refuse every first write this app ever makes."""
        self.assertEqual(store_io.read(self.path, []), [])
        self.path.write_text("")
        self.assertEqual(store_io.read(self.path, {"a": 1}), {"a": 1})
        self.assertEqual(store_io.unreadable_stores(), {})

    def test_a_round_trip_preserves_the_value(self):
        store_io.write(self.path, [{"id": 1}, {"id": 2}])
        self.assertEqual(store_io.read(self.path, []), [{"id": 1}, {"id": 2}])

    def test_the_write_leaves_no_temp_file_behind(self):
        store_io.write(self.path, [1])
        leftovers = [p.name for p in self.path.parent.iterdir()
                     if ".tmp-" in p.name]
        self.assertEqual(leftovers, [])

    def test_the_temp_file_is_written_in_the_same_directory_as_its_target(self):
        """os.replace is only atomic within one filesystem. A temp file in the system temp dir
        would silently degrade the whole mechanism to a copy, on exactly the machines where
        /tmp is a different mount -- and nothing would report it."""
        body = inspect.getsource(store_io._write_unlocked)
        self.assertIn("path.with_name(", body)
        self.assertNotIn("tempfile", body)


class DamagedStoreTests(unittest.TestCase):
    """The guard that turns a transient failure back into a transient one."""

    def setUp(self):
        self._dir, self.path = _tmp()
        store_io.clear_unreadable()

    def tearDown(self):
        self._dir.cleanup()
        store_io.clear_unreadable()

    def test_an_unparseable_store_is_reported_rather_than_silently_empty(self):
        self.path.write_text("[{'half a fi")
        self.assertEqual(store_io.read(self.path, []), [])
        self.assertIn(str(self.path), store_io.unreadable_stores())

    def test_an_unparseable_store_is_not_overwritten_by_a_later_write(self):
        """The measured failure, inverted. Before: a store of five objectives became a store of
        one, because the empty view was written back. Losing the item being added beats losing
        everything already there, and the bytes stay recoverable."""
        self.path.write_text("[{'half a fi")
        store_io.read(self.path, [])
        store_io.write(self.path, ["a brand new one-element store"])
        self.assertEqual(self.path.read_text(), "[{'half a fi")

    def test_mutate_also_declines_to_write_over_damage(self):
        self.path.write_text("not json at all")
        with store_io.mutate(self.path, []) as entries:
            entries.append({"id": 1})
        self.assertEqual(self.path.read_text(), "not json at all")
        self.assertIn(str(self.path), store_io.unreadable_stores())

    def test_the_mark_clears_when_the_file_parses_again(self):
        """A mark that outlived its cause would keep refusing writes to a file that is now fine
        -- which would turn a one-off corruption into a permanently read-only store."""
        self.path.write_text("broken")
        store_io.read(self.path, [])
        self.assertTrue(store_io.unreadable_stores())
        self.path.write_text("[1, 2]")
        self.assertEqual(store_io.read(self.path, []), [1, 2])
        self.assertEqual(store_io.unreadable_stores(), {})
        store_io.write(self.path, [3])
        self.assertEqual(store_io.read(self.path, []), [3])


class MutateTests(unittest.TestCase):
    def setUp(self):
        self._dir, self.path = _tmp()
        store_io.clear_unreadable()

    def tearDown(self):
        self._dir.cleanup()

    def test_it_loads_yields_and_writes_back(self):
        with store_io.mutate(self.path, []) as entries:
            entries.append({"id": 1})
        with store_io.mutate(self.path, []) as entries:
            entries.append({"id": 2})
        self.assertEqual(store_io.read(self.path, []), [{"id": 1}, {"id": 2}])

    def test_it_works_on_a_dict_store_too(self):
        with store_io.mutate(self.path, {}) as data:
            data["a"] = 1
        with store_io.mutate(self.path, {}) as data:
            data.pop("a", None)
            data["b"] = 2
        self.assertEqual(store_io.read(self.path, {}), {"b": 2})

    def test_it_takes_the_load_away_from_the_caller_on_purpose(self):
        """The lost update was never a missing lock so much as a LOAD THAT HAPPENED OUTSIDE ONE.
        A caller that cannot read separately cannot reintroduce it -- which is why this is a
        context manager that yields the loaded value rather than a lock a caller wraps."""
        signature = inspect.signature(store_io.mutate)
        self.assertEqual(list(signature.parameters), ["path", "default"])


class LockingTests(unittest.TestCase):
    def setUp(self):
        self._dir, self.path = _tmp()
        store_io.clear_unreadable()

    def tearDown(self):
        self._dir.cleanup()

    def test_concurrent_threads_all_survive(self):
        """Streamlit serves many browser tabs from ONE process, so the common multi-tab case is
        threads, not processes. Each worker does the full read-modify-write the stores do."""
        def worker(n):
            with store_io.mutate(self.path, []) as entries:
                entries.append(n)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(store_io.read(self.path, [])), list(range(40)))

    def test_the_lock_is_reentrant_within_one_thread(self):
        """Not belt-and-braces: these stores nest. A public function holds the lock for its whole
        body (see `atomic`) and the read and write inside it take it again. A plain Lock
        deadlocks on the second acquire, and flock on a SECOND descriptor for the same file
        deadlocks even though this thread already holds it."""
        with store_io.locked(self.path):
            with store_io.locked(self.path):
                store_io.write(self.path, [1])
                self.assertEqual(store_io.read(self.path, []), [1])

    def test_atomic_holds_one_lock_across_a_whole_decorated_function(self):
        path = self.path

        @store_io.atomic(lambda n: path)
        def add(n):
            entries = store_io.read(path, [])
            entries.append(n)
            store_io.write(path, entries)

        threads = [threading.Thread(target=add, args=(n,)) for n in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(store_io.read(path, [])), list(range(40)))

    def test_the_platform_lock_that_actually_engaged_is_named(self):
        """A lock is advisory and a network filesystem may not honour it. LOCKING says what
        really engaged so a caller can report the truth rather than assume the strong case."""
        self.assertIn(store_io.LOCKING, ("fcntl", "msvcrt", "threads-only"))


def _hammer(path_str, worker, per_worker):
    for i in range(per_worker):
        with store_io.mutate(Path(path_str), []) as entries:
            entries.append(f"w{worker}-{i}")


class CrossProcessTests(unittest.TestCase):
    """The case a thread lock alone cannot cover: a second `streamlit run`, or a phone and a
    laptop against a synced directory."""

    def test_concurrent_processes_all_survive(self):
        directory, path = _tmp()
        try:
            workers, per_worker = 4, 15
            procs = [mp.Process(target=_hammer, args=(str(path), w, per_worker))
                     for w in range(workers)]
            for p in procs:
                p.start()
            for p in procs:
                p.join()
            self.assertEqual(len(store_io.read(path, [])), workers * per_worker)
        finally:
            directory.cleanup()

    def test_a_reader_never_sees_a_prefix_of_a_write_in_progress(self):
        """The torn read, at unit scale. Before the repair this harness produced JSONDecodeError
        on the majority of reads; os.replace makes a reader see the complete old file or the
        complete new one, never a partial one."""
        directory, path = _tmp()
        try:
            payload = [{"id": i, "text": "x" * 100} for i in range(2000)]
            store_io.write(path, payload)
            torn = []

            def reader():
                for _ in range(200):
                    try:
                        json.loads(path.read_text())
                    except (json.JSONDecodeError, OSError) as exc:
                        torn.append(str(exc))

            writers = [threading.Thread(target=lambda: [store_io.write(path, payload)
                                                        for _ in range(50)]) for _ in range(2)]
            readers = [threading.Thread(target=reader) for _ in range(3)]
            for t in writers + readers:
                t.start()
            for t in writers + readers:
                t.join()
            self.assertEqual(torn, [], "a reader saw a partial file")
        finally:
            directory.cleanup()


class EveryStoreGoesThroughItTests(unittest.TestCase):
    """The coverage guard. A repair that fixed nine stores and left the tenth to be written
    unprotected next month has bought a year, not a property -- and the tenth would look exactly
    like the nine did, because the flat `path.write_text(json.dumps(...))` shape is the obvious
    thing to type.

    Scanned rather than enumerated on purpose: a hand-kept list of protected stores is a list
    someone has to remember to extend, which is the same failure one level up."""

    #: Files whose JSON writes are deliberately NOT store_io's, each with its reason. Anything
    #: else that writes JSON to disk must go through store_io or this test fails.
    ALLOWED = {
        "store_io.py": "it IS the mechanism -- the atomic write lives here",
        "draft_history.py": "already wrote atomically, and write-if-absent means it never "
                            "read-modify-writes: snapshots are immutable once written",
        "sleeper_client.py": "a replaceable cache of a remote API, not user data -- a lost "
                             "write costs one re-fetch, and there is no read-modify-write",
        "bot_benchmark.py": "developer-run measurement output, never touched by the app",
    }

    def test_no_module_writes_a_json_store_outside_store_io(self):
        offenders = []
        for path in sorted(Path(__file__).parent.glob("*.py")):
            if path.name.startswith(("test_", "run_", "compare_")) or path.name in self.ALLOWED:
                continue
            source = path.read_text()
            for lineno, line in enumerate(source.splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "write_text(json.dumps" in stripped:
                    offenders.append(f"{path.name}:{lineno}")
        self.assertEqual(offenders, [],
                         "a JSON store is being written outside store_io -- route it through "
                         "store_io.write/mutate, or add it to ALLOWED with its reason")

    def test_the_allowances_are_reasons_and_not_just_names(self):
        """A named exemption with no stated reason is how an exemption list rots."""
        for name, reason in self.ALLOWED.items():
            with self.subTest(name=name):
                self.assertGreater(len(reason), 25, f"{name}'s exemption needs a real reason")

    def test_the_stores_this_repair_covered_all_import_it(self):
        """Non-vacuity for the scan above: it would also pass on a tree where nothing writes
        JSON at all. These nine are the ones #102 named."""
        for name in ("todo_log.py", "decision_log.py", "pinned_messages.py", "attachments.py",
                     "league_prefs.py", "league_format.py", "bot_config.py", "bot_research.py",
                     "data_merger.py"):
            with self.subTest(module=name):
                self.assertIn("import store_io", (Path(__file__).parent / name).read_text())


class TheGuardIsSurfacedTests(unittest.TestCase):
    """An unreadable store the app quietly works around is the "looks handled" failure this
    codebase keeps finding -- the same shape as an annotation nothing reads. store_io declining
    to overwrite damage is only half the repair; the other half is telling the user that the
    store is empty-to-the-app and not being saved.

    app.py is source-scanned rather than imported, as every app-level contract here is."""

    APP = ui_source.text()

    def test_the_app_reads_the_unreadable_register_and_reports_it(self):
        self.assertIn("def warn_about_unreadable_stores(", self.APP)
        self.assertIn("store_io.unreadable_stores()", self.APP)
        self.assertGreaterEqual(self.APP.count("warn_about_unreadable_stores"), 2,
                                "the helper is defined but never called")

    def test_the_notice_says_what_the_app_is_actually_doing_about_it(self):
        """Three facts a user needs and would otherwise have to infer: the file was left alone,
        the app is running on an empty view, and writes are not landing."""
        notice = self.APP.split("def warn_about_unreadable_stores(")[1].split("\ndef ")[0]
        self.assertIn("left exactly as it is", notice)
        self.assertIn("empty view", notice)
        self.assertIn("NOT saving", notice)

    def test_it_is_once_per_store_and_not_once_per_rerun(self):
        """A persistent condition re-announced on every Streamlit rerun spams the activity log
        instead of informing anyone -- the same reason maybe_nudge_stale_free_agents is keyed."""
        notice = self.APP.split("def warn_about_unreadable_stores(")[1].split("\ndef ")[0]
        self.assertIn("unreadable_stores_warned", notice)
        self.assertIn("if path in seen", notice)


if __name__ == "__main__":
    unittest.main()
