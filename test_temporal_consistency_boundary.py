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
import unittest
from pathlib import Path

import pick_debate
import pick_synthesis as ps
import todo_log

_HERE = Path(__file__).parent
_APP = (_HERE / "app.py").read_text()


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


class ConcurrentWritersLoseUpdatesTests(unittest.TestCase):
    """KNOWN GAP — characterization. §11: can an older operation overwrite a newer one?"""

    def test_two_sessions_on_one_league_lose_an_update(self):
        with tempfile.TemporaryDirectory() as tmp:
            saved = todo_log.TODOS_DIR
            todo_log.TODOS_DIR = Path(tmp)
            try:
                todo_log.add_todo("L1", "written by tab A")
                stale_view = todo_log._load("L1")          # tab B reads
                todo_log.add_todo("L1", "written by tab A, second")
                stale_view.append({"id": 99, "text": "written by tab B", "status": "active",
                                   "date": "2026-08-31", "ts": 1.0})
                todo_log._save("L1", stale_view)           # tab B writes its stale view
                surviving = [e["text"] for e in todo_log._load("L1")]
                self.assertIn("written by tab A", surviving)
                self.assertIn("written by tab B", surviving)
                self.assertNotIn(
                    "written by tab A, second", surviving,
                    "The lost update was fixed -- invert this test.",
                )
            finally:
                todo_log.TODOS_DIR = saved

    def test_no_store_uses_a_lock_or_an_atomic_replace(self):
        """Recorded rather than repaired: a torn write is undemonstrated here, and this
        programme does not make production changes for undemonstrated failures (§7.8)."""
        import bot_research, decision_log, pinned_messages
        for module in (todo_log, decision_log, pinned_messages, bot_research):
            source = inspect.getsource(module)
            self.assertIn("write_text", source)
            for marker in ("os.replace", "flock", "FileLock", "NamedTemporaryFile"):
                self.assertNotIn(marker, source, f"{module.__name__} gained write safety -- invert this test.")


if __name__ == "__main__":
    unittest.main()
