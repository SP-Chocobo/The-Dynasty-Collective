"""§11 (ARCHITECTURE_AUDIT Pass 8): temporal consistency, concurrency, stale results.

The section's finding is not that this app cannot tell whether a frozen snapshot is still
current. It can, precisely, and says so: `PickSnapshot` carries an explicit INPUT-STATE STAMP
(`picks_consumed` + `data_freshest_date`), and `pick_synthesis.snapshot_is_current` turns that
stamp into a `(bool, reason)` answer with a documented "unknown provenance is not known current"
posture. The finding is that **it has no production caller**, while the Draft Room guards its
displayed result on `pick_label` — which cannot distinguish two boards at the same pick.

  ENFORCEMENT. The stamp exists on the snapshot, the certifier behaves correctly at each of its
  boundaries, and (since the §11 repair) a debate result records the stamp it was generated
  against, so any consumer can put the result to the certifier.

  CHARACTERIZATION — invert on repair, do not delete. `snapshot_is_current` is called by nothing
  in production; both Draft Room result guards compare `pick_label`; and the per-league JSON
  stores lose an update under concurrent writers.

No provider is called anywhere in this file.
"""

import dataclasses
import inspect
import tempfile
import threading
import unittest
from pathlib import Path

import pick_debate
import pick_synthesis as ps
import todo_log
import ui_source

_HERE = Path(__file__).parent
_APP = ui_source.text()


class _FakeMerger:
    def __init__(self, freshest_date):
        self.freshest_date = freshest_date


def _candidate(player_id="1", name="Somebody"):
    fields = {f.name: f for f in dataclasses.fields(ps.CandidateSnapshot)}
    kwargs = {}
    for field_name, f in fields.items():
        if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
            continue
        kwargs[field_name] = {
            "player_id": player_id, "name": name, "position": "WR",
        }.get(field_name, 0.0)
    return ps.CandidateSnapshot(**kwargs)


def _snapshot(pick_label="3.05", candidates=None, picks_consumed=24, freshest="2026-08-25"):
    fields = {f.name: f for f in dataclasses.fields(ps.PickSnapshot)}
    kwargs = {}
    for field_name, f in fields.items():
        if f.default is not dataclasses.MISSING or f.default_factory is not dataclasses.MISSING:
            continue
        kwargs[field_name] = {
            "pick_label": pick_label, "round": 3, "my_roster_id": "1",
            "candidates": tuple(candidates or [_candidate()]),
        }.get(field_name)
    return ps.PickSnapshot(picks_consumed=picks_consumed, data_freshest_date=freshest, **kwargs)


class TheSnapshotCarriesAnInputStateStampTests(unittest.TestCase):
    """The mechanism §11 asks for, which already exists."""

    def test_a_built_snapshot_is_stamped_with_what_it_was_computed_from(self):
        snap = _snapshot()
        self.assertEqual(snap.picks_consumed, 24)
        self.assertEqual(snap.data_freshest_date, "2026-08-25")

    def test_the_certifier_accepts_an_unchanged_world(self):
        snap = _snapshot()
        ok, reason = ps.snapshot_is_current(snap, [{}] * 24, _FakeMerger("2026-08-25"))
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_the_certifier_rejects_new_picks_and_says_how_many(self):
        snap = _snapshot()
        ok, reason = ps.snapshot_is_current(snap, [{}] * 27, _FakeMerger("2026-08-25"))
        self.assertFalse(ok)
        self.assertIn("3 new pick(s)", reason)

    def test_the_certifier_rejects_changed_underlying_data(self):
        snap = _snapshot()
        ok, reason = ps.snapshot_is_current(snap, [{}] * 24, _FakeMerger("2026-08-26"))
        self.assertFalse(ok)
        self.assertIn("underlying player data changed", reason)

    def test_an_unstamped_snapshot_is_not_certifiable_rather_than_silently_current(self):
        """'Unknown provenance' and 'known current' are different claims -- the same
        don't-fabricate posture as the absence contract and §6's panel_undisputed rename."""
        snap = _snapshot(picks_consumed=None, freshest=None)
        ok, reason = ps.snapshot_is_current(snap, [], _FakeMerger(None))
        self.assertFalse(ok)
        self.assertIn("no input-state stamp", reason)


class ADebateResultRecordsTheStateItReasonedOverTests(unittest.TestCase):
    """§11 repair (R11), and the same rule as §10's R9/R10."""

    def _run(self, snapshot):
        original = dict(pick_debate.PROVIDER_CALLERS)
        for name in list(pick_debate.PROVIDER_CALLERS):
            pick_debate.PROVIDER_CALLERS[name] = (
                lambda system, user, api_key=None, model=None: "RECOMMENDATION: Somebody"
            )
        try:
            return pick_debate.debate_pick(snapshot, api_keys={"claude": "k", "openai": "k"})
        finally:
            pick_debate.PROVIDER_CALLERS.update(original)

    def test_the_result_carries_the_snapshots_input_state_stamp(self):
        result = self._run(_snapshot(picks_consumed=24, freshest="2026-08-25"))
        self.assertEqual(result.snapshot_picks_consumed, 24)
        self.assertEqual(result.snapshot_data_freshest_date, "2026-08-25")

    def test_an_unstamped_snapshot_yields_an_unstamped_result_rather_than_a_guess(self):
        result = self._run(_snapshot(picks_consumed=None, freshest=None))
        self.assertIsNone(result.snapshot_picks_consumed)
        self.assertIsNone(result.snapshot_data_freshest_date)

    def test_the_recorded_stamp_is_enough_to_reach_the_certifier(self):
        """The point of recording it: a consumer holding only the result can now ask the
        question, which before the repair it structurally could not."""
        snap = _snapshot(picks_consumed=24, freshest="2026-08-25")
        result = self._run(snap)
        rebuilt = _snapshot(picks_consumed=result.snapshot_picks_consumed,
                            freshest=result.snapshot_data_freshest_date)
        self.assertTrue(ps.snapshot_is_current(rebuilt, [{}] * 24, _FakeMerger("2026-08-25"))[0])
        self.assertFalse(ps.snapshot_is_current(rebuilt, [{}] * 27, _FakeMerger("2026-08-25"))[0])


class StalenessIsDetectableAndNotConsultedTests(unittest.TestCase):
    """KNOWN GAPS — characterization. Invert when repaired; do not delete."""

    def test_two_materially_different_boards_share_one_pick_label(self):
        """Why `pick_label` cannot be the staleness key: the user stays on the clock at one
        label while other rosters keep picking."""
        before = _snapshot(candidates=[_candidate("1", "A"), _candidate("2", "B"), _candidate("3", "C")],
                           picks_consumed=24)
        after = _snapshot(candidates=[_candidate("2", "B")], picks_consumed=27)
        self.assertEqual(before.pick_label, after.pick_label)
        self.assertNotEqual(before.picks_consumed, after.picks_consumed)
        self.assertNotEqual(len(before.candidates), len(after.candidates))

    def test_the_difference_is_fully_describable_by_machinery_that_already_exists(self):
        """`diff_snapshots` produces the structured delta -- it is folded into the NEXT debate's
        evidence, never used to invalidate or annotate the result already on screen."""
        before = _snapshot(candidates=[_candidate("1", "A"), _candidate("2", "B")], picks_consumed=24)
        after = _snapshot(candidates=[_candidate("2", "B")], picks_consumed=27)
        diffs = ps.diff_snapshots(before, after)
        self.assertTrue(any(d.get("entered") is False for d in diffs))
        source = inspect.getsource(pick_debate.debate_pick)
        self.assertIn("previous_snapshot", source)

    def test_snapshot_is_current_has_no_production_caller(self):
        """A purpose-built certifier for exactly §11's question, tested, documented, and
        stranded -- the same shape as marginal_lineup_value (H2)."""
        callers = []
        for path in _HERE.glob("*.py"):
            if path.name.startswith("test_") or path.name == "pick_synthesis.py":
                continue
            for line in path.read_text().splitlines():
                if "snapshot_is_current" in line and not line.strip().startswith("#"):
                    callers.append(f"{path.name}: {line.strip()}")
        self.assertEqual(callers, [], "snapshot_is_current gained a caller -- invert this test.")

    def test_both_draft_room_result_guards_compare_only_the_pick_label(self):
        self.assertIn("debate_result.pick_label == pick_label", _APP)
        self.assertIn("mock_debate_result.pick_label == mock_pick_label", _APP)
        self.assertNotIn("snapshot_is_current(", _APP)

    def test_the_snapshot_cache_already_keys_on_the_very_signals_the_guard_ignores(self):
        """The sharpest form of the gap: the board is REBUILT when these change, and the stale
        recommendation is then displayed beside the rebuilt board."""
        self.assertIn("len(draft_picks), merger.freshest_date,", _APP)


class ConcurrentWritersNoLongerLoseUpdatesTests(unittest.TestCase):
    """#102, REPAIRED -- and these tests inverted rather than deleted. §11 asked "can an older
    operation overwrite or contaminate a newer one?" and the answer was yes.

    THE OLD TEST HAD A FLAW WORTH RECORDING, because it is the reason the repair was measured
    twice. It interleaved todo_log._load and _save by hand. That was a fair model of the old
    code -- the public functions did exactly that, with nothing between them -- but it is not a
    model of any production path, and re-running it unchanged against the repair would have
    measured a route nothing takes. So the repair was measured on the PRODUCTION path instead:
    concurrent processes calling the real public functions.

    What that found was worse than the two-tab scenario suggested. Before the repair, 8
    processes calling todo_log.add_todo 25 times each kept 6 of 200 objectives, and
    data_merger.save_alias kept 9 of 200 -- 97% and 95% loss, not an edge case. After: 200 of
    200 for both.
    """

    def test_concurrent_writers_through_the_public_api_all_survive(self):
        """Threads rather than processes here on purpose: Streamlit serves many browser tabs
        from ONE process, so this is the common multi-tab case, and it is cheap enough to run in
        the suite. The cross-process case lives in test_store_io."""
        with tempfile.TemporaryDirectory() as tmp:
            saved = todo_log.TODOS_DIR
            todo_log.TODOS_DIR = Path(tmp)
            try:
                def writer(n):
                    todo_log.add_todo("L1", f"objective {n}")

                threads = [threading.Thread(target=writer, args=(n,)) for n in range(30)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                surviving = {e["text"] for e in todo_log.load_todos("L1")}
                self.assertEqual(surviving, {f"objective {n}" for n in range(30)})
            finally:
                todo_log.TODOS_DIR = saved

    def test_every_objective_still_gets_a_distinct_id_under_contention(self):
        """The quieter half of the same race. _next_id is max(existing) + 1, so two writers
        loading the same view mint the same id -- and a duplicate id is worse than a lost row,
        because resolve_todo/revise_todo address items BY id and would then hit whichever one
        _find happens to reach first."""
        with tempfile.TemporaryDirectory() as tmp:
            saved = todo_log.TODOS_DIR
            todo_log.TODOS_DIR = Path(tmp)
            try:
                threads = [threading.Thread(target=todo_log.add_todo, args=("L1", f"o{n}"))
                           for n in range(30)]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join()
                ids = [e["id"] for e in todo_log.load_todos("L1")]
                self.assertEqual(len(ids), len(set(ids)), "two objectives share an id")
            finally:
                todo_log.TODOS_DIR = saved

    def test_every_store_now_writes_through_the_one_mechanism(self):
        """The inversion of "no store uses a lock or an atomic replace". The scan that keeps this
        true for stores written in future lives in test_store_io."""
        import bot_research, decision_log, pinned_messages
        for module in (todo_log, decision_log, pinned_messages, bot_research):
            with self.subTest(module=module.__name__):
                source = inspect.getsource(module)
                self.assertIn("store_io", source)
                self.assertNotIn("write_text(json.dumps", source)

    def test_the_mechanism_really_is_a_lock_and_an_atomic_replace(self):
        """Non-vacuity for the test above: importing store_io proves nothing on its own."""
        import store_io
        source = inspect.getsource(store_io)
        self.assertIn("os.replace", source)
        self.assertIn("flock", source)


if __name__ == "__main__":
    unittest.main()
