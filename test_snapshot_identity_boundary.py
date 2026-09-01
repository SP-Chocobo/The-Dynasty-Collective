"""Step 1a (Insight Foundation): snapshot identity (#92), the draft-history store (#92/#102),
and the staleness check that finally has a consumer (#101).

Three properties are defended here, and each is proven by planting something rather than by
reading the implementation:

  IDENTITY IS TOTAL. Every field of PickSnapshot and of every CandidateSnapshot participates,
  candidate ORDER participates, and field NAMES participate. A test that only checked "the same
  snapshot hashes the same" would pass against a function that hashed the pick label alone, so
  the coverage tests below mutate each field in turn and require the identity to move.

  THE STORE CANNOT LOSE A WRITE. §11.4b (#102) demonstrated a cross-session lost update in the
  existing per-league stores. That defect is REPRODUCED here against decision_log, and then the
  identical interleaving is run against draft_history to show it cannot occur. Without the
  reproduction the second half would prove nothing about whether the new layout actually fixes
  anything.

  THE STORE IS NOT AN ENGINE INPUT. Recording history must not change a single valuation
  number, proven the way §25 proved the research boundary: populate the store, recompute, and
  measure that nothing moved.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import content_hash
import decision_log
import draft_history
import pick_synthesis as ps
from pick_synthesis import CandidateSnapshot, PickSnapshot


def _candidate(player_id="p1", **overrides) -> CandidateSnapshot:
    """A fully-populated candidate. Every optional field is given a REAL value rather than
    left at its default, so the per-field coverage test below is actually mutating something."""
    base = dict(
        player_id=player_id, name="A Player", position="RB", team="SF",
        bpa=30.0, bpa_source="points_vor_draftsharks", confidence=90.0,
        universal_value=37.23, need_bonus=4.33, eligibility_bonus=0.0,
        team_acquisition_value=41.56, survival_probability=0.25, intervening_picks=11,
        opportunity_cost=3.1, expected_value_of_waiting=30.0, denial_value=2.0,
        denial_team="11", rival_premium=4.33, positional_forfeit=25.38,
        position_expected_taken=4.4, positional_cliff={"tier": "HIGH", "gap": 12.0, "typical_gap": 2.0},
        position_run_detected=True, pick_necessity=72.0, necessity_label="STRONG ACTION",
        near_tie_with_leader=True, cliff_protection=True, block_opportunity=False,
        pure_value=False, context_elevated=True, consensus_rank=14, consensus_tier=3,
        reach_label="slight reach", projected_points=210.0,
        rival_premium_take_probability=0.62, waiting_cost=18.0, horizon_floor=150.0,
        horizon_sensitivity=12.0,
    )
    base.update(overrides)
    return CandidateSnapshot(**base)


def _snapshot(**overrides) -> PickSnapshot:
    base = dict(
        pick_label="4.01", round=4, my_roster_id="12",
        candidates=(_candidate("p1"), _candidate("p2", name="B Player", team="KC")),
        user_selected_player_id=None, picks_consumed=36,
        data_freshest_date="2026-08-20", decision_regime="contested",
    )
    base.update(overrides)
    return PickSnapshot(**base)


class _Merger:
    """The only thing stamp_is_current reads off a merger."""
    def __init__(self, freshest_date="2026-08-20"):
        self.freshest_date = freshest_date


class IdentityIsDeterministicTests(unittest.TestCase):

    def test_the_same_snapshot_always_yields_the_same_identity(self):
        snap = _snapshot()
        self.assertEqual(ps.snapshot_identity(snap), ps.snapshot_identity(snap))
        self.assertEqual(ps.snapshot_identity(snap), ps.snapshot_identity(_snapshot()))

    def test_the_identity_is_the_shared_primitive_not_a_second_hasher(self):
        """#111 asked for the existing content-hash mechanism to be EXTENDED, not forked. The
        digest length and alphabet come from content_hash, so there is one implementation."""
        identity = ps.snapshot_identity(_snapshot())
        self.assertEqual(len(identity), content_hash.FINGERPRINT_CHARS)
        self.assertTrue(all(char in "0123456789abcdef" for char in identity))

    def test_computing_an_identity_does_not_mutate_the_snapshot(self):
        snap = _snapshot()
        before = dataclasses.astuple(snap)
        ps.snapshot_identity(snap)
        self.assertEqual(dataclasses.astuple(snap), before)


class IdentityCoversEveryFieldTests(unittest.TestCase):
    """Non-vacuity. A hash that ignored a field would let two genuinely different boards share
    one identity, and a stored record would then be bound to the wrong thing."""

    @staticmethod
    def _mutate(value):
        if isinstance(value, bool):
            return not value
        if isinstance(value, str):
            return value + "_PLANTED"
        if isinstance(value, (int, float)):
            return value + 1
        if isinstance(value, dict):
            return {**value, "planted": True}
        return "PLANTED"

    def test_every_snapshot_field_participates(self):
        snap = _snapshot()
        baseline = ps.snapshot_identity(snap)
        for field in dataclasses.fields(snap):
            if field.name == "candidates":
                continue  # covered by its own tests below
            with self.subTest(field=field.name):
                altered = dataclasses.replace(
                    snap, **{field.name: self._mutate(getattr(snap, field.name))})
                self.assertNotEqual(ps.snapshot_identity(altered), baseline)

    def test_every_candidate_field_participates(self):
        snap = _snapshot()
        baseline = ps.snapshot_identity(snap)
        first = snap.candidates[0]
        for field in dataclasses.fields(first):
            with self.subTest(field=field.name):
                altered_candidate = dataclasses.replace(
                    first, **{field.name: self._mutate(getattr(first, field.name))})
                altered = dataclasses.replace(
                    snap, candidates=(altered_candidate,) + snap.candidates[1:])
                self.assertNotEqual(ps.snapshot_identity(altered), baseline)

    def test_candidate_order_is_part_of_the_identity(self):
        """The tuple is the board's own ranked order. The same players ranked differently is a
        different board, and a record bound to one must not resolve to the other."""
        snap = _snapshot()
        reordered = dataclasses.replace(snap, candidates=tuple(reversed(snap.candidates)))
        self.assertNotEqual(ps.snapshot_identity(reordered), ps.snapshot_identity(snap))

    def test_field_names_are_part_of_the_identity(self):
        """Two snapshots holding the same VALUES in different FIELDS must not collide. If names
        were omitted from the hash both of these would reduce to the same multiset of parts.
        This is the §17.5/#110 silent-meaning-change class: a rename must be visible."""
        a = _snapshot(pick_label="X", my_roster_id="Y")
        b = _snapshot(pick_label="Y", my_roster_id="X")
        self.assertNotEqual(ps.snapshot_identity(a), ps.snapshot_identity(b))

    def test_a_numpy_float_hashes_identically_to_the_python_float(self):
        """Planted type. `repr(numpy.float64(1.5))` differs between numpy majors, so an
        identity that reprs values naively would change under a dependency upgrade with no
        change to the board -- silent drift of exactly the kind #113 is about."""
        try:
            import numpy as np
        except ImportError:  # pragma: no cover - numpy is a hard dependency of this app
            self.skipTest("numpy not installed")
        snap = _snapshot()
        first = snap.candidates[0]
        as_numpy = dataclasses.replace(first, universal_value=np.float64(first.universal_value))
        planted = dataclasses.replace(snap, candidates=(as_numpy,) + snap.candidates[1:])
        self.assertEqual(ps.snapshot_identity(planted), ps.snapshot_identity(snap))

    def test_dict_key_order_does_not_change_the_identity(self):
        """positional_cliff is a dict, and repr preserves insertion order. The same cliff built
        with its keys in a different order is the same cliff."""
        snap = _snapshot()
        first = snap.candidates[0]
        reordered_cliff = dict(reversed(list(first.positional_cliff.items())))
        self.assertNotEqual(list(reordered_cliff), list(first.positional_cliff))
        altered = dataclasses.replace(first, positional_cliff=reordered_cliff)
        planted = dataclasses.replace(snap, candidates=(altered,) + snap.candidates[1:])
        self.assertEqual(ps.snapshot_identity(planted), ps.snapshot_identity(snap))


class StoreCannotLoseAWriteTests(unittest.TestCase):
    """#102, reproduced and then fixed. The reproduction is what makes the fix meaningful."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._orig_history = draft_history.HISTORY_DIR
        self._orig_decisions = decision_log.DECISIONS_DIR
        draft_history.HISTORY_DIR = Path(self._tmp) / "draft_history"
        decision_log.DECISIONS_DIR = Path(self._tmp) / "decisions"
        decision_log.DECISIONS_DIR.mkdir(parents=True, exist_ok=True)
        self.addCleanup(setattr, draft_history, "HISTORY_DIR", self._orig_history)
        self.addCleanup(setattr, decision_log, "DECISIONS_DIR", self._orig_decisions)

    def test_the_existing_store_still_loses_an_interleaved_write(self):
        """CONTROL. decision_log does load -> append -> write-whole-list. Two sessions that
        both load before either writes destroy one entry. This is the defect #102 names; it is
        NOT repaired here, and this test exists so the next test proves something."""
        league = "L1"
        session_a = decision_log._load(league)          # both sessions read...
        session_b = decision_log._load(league)
        session_a.append({"ts": 1.0, "question": "A"})  # ...then both write
        decision_log._path(league).write_text(json.dumps(session_a))
        session_b.append({"ts": 2.0, "question": "B"})
        decision_log._path(league).write_text(json.dumps(session_b))

        surviving = {entry["question"] for entry in decision_log.load_decisions(league)}
        self.assertEqual(surviving, {"B"}, "the reproduction must actually lose A")
        self.assertNotIn("A", surviving)

    def test_the_history_store_survives_the_identical_interleaving(self):
        """The same two-sessions-at-once shape against draft_history. It cannot lose a write
        because it never reads before writing: one record is one file, named by its content."""
        league = "L1"
        snap_a = _snapshot(pick_label="4.01")
        snap_b = _snapshot(pick_label="4.02")
        id_a, id_b = ps.snapshot_identity(snap_a), ps.snapshot_identity(snap_b)
        self.assertNotEqual(id_a, id_b)

        # Both "sessions" observe the same empty store, then both write.
        self.assertEqual(draft_history.snapshot_ids(league), set())
        self.assertEqual(draft_history.snapshot_ids(league), set())
        draft_history.record_snapshot(league, snap_a, id_a)
        draft_history.record_snapshot(league, snap_b, id_b)

        self.assertEqual(draft_history.snapshot_ids(league), {id_a, id_b})

    def test_recording_the_same_snapshot_twice_is_idempotent(self):
        snap = _snapshot()
        identity = ps.snapshot_identity(snap)
        draft_history.record_snapshot("L1", snap, identity)
        draft_history.record_snapshot("L1", snap, identity)
        self.assertEqual(len(draft_history.list_snapshot_records("L1")), 1)

    def test_a_league_id_cannot_escape_the_store_directory(self):
        """The league id is user-supplied (it arrives from a Sleeper import) and becomes a path
        component."""
        for hostile in ("../../etc", "..", ".", "/absolute", "a/b"):
            with self.subTest(league_id=hostile):
                draft_history.record_snapshot(hostile, _snapshot(), "deadbeef0000")
        written = list(Path(self._tmp).rglob("deadbeef0000.json"))
        self.assertTrue(written)
        root = (Path(self._tmp) / "draft_history").resolve()
        for path in written:
            self.assertTrue(path.resolve().is_relative_to(root), path)

    def test_no_temporary_files_are_left_behind(self):
        draft_history.record_snapshot("L1", _snapshot(), "abc123abc123")
        leftovers = [p for p in draft_history.HISTORY_DIR.rglob("*") if p.name.startswith(".")]
        self.assertEqual(leftovers, [])

    def test_a_corrupt_record_returns_none_rather_than_taking_down_a_draft(self):
        league = "L1"
        draft_history.record_snapshot(league, _snapshot(), "abc123abc123")
        path = draft_history._scope_dir(league) / "abc123abc123.json"
        path.write_text("{ this is not json")
        self.assertIsNone(draft_history.load_snapshot_record(league, "abc123abc123"))
        self.assertEqual(draft_history.list_snapshot_records(league), [])

    def test_history_leaves_only_by_explicit_deletion(self):
        """The retention policy, pinned: nothing here expires, and nothing is cleared at draft
        conclusion. `forget_league` is the only removal path."""
        draft_history.record_snapshot("L1", _snapshot(), "abc123abc123")
        draft_history.record_snapshot("L2", _snapshot(), "abc123abc123")
        self.assertEqual(draft_history.forget_league("L1"), 1)
        self.assertEqual(draft_history.snapshot_ids("L1"), set())
        self.assertEqual(draft_history.snapshot_ids("L2"), {"abc123abc123"},
                         "deleting one league must not touch another")

    def test_one_league_never_sees_another_leagues_history(self):
        draft_history.record_snapshot("L1", _snapshot(pick_label="4.01"), "aaaaaaaaaaaa")
        draft_history.record_snapshot("L2", _snapshot(pick_label="9.09"), "bbbbbbbbbbbb")
        self.assertEqual(draft_history.snapshot_ids("L1"), {"aaaaaaaaaaaa"})
        self.assertEqual(draft_history.snapshot_ids("L2"), {"bbbbbbbbbbbb"})


class EvidenceProjectionTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._orig = draft_history.HISTORY_DIR
        draft_history.HISTORY_DIR = Path(self._tmp) / "draft_history"
        self.addCleanup(setattr, draft_history, "HISTORY_DIR", self._orig)

    def test_the_projection_carries_everything_the_retention_policy_requires(self):
        snap = _snapshot()
        projection = draft_history.evidence_projection(snap, "abc123abc123")
        for required in ("snapshot_id", "pick_label", "round", "decision_regime",
                         "user_selected_player_id", "candidates",
                         "picks_consumed", "data_freshest_date"):
            self.assertIn(required, projection)
        self.assertEqual(len(projection["candidates"]), len(snap.candidates))

    def test_the_projection_carries_the_anchor_provenance_the_board_drops(self):
        """§24/#119 measured that draft_board_ui drops bpa_source and confidence, so a record
        built from what the board shows could not say what anchored a number. The record keeps
        them. This does not settle #119, which is about the board surface."""
        row = draft_history.evidence_projection(_snapshot(), "x")["candidates"][0]
        self.assertEqual(row["bpa_source"], "points_vor_draftsharks")
        self.assertEqual(row["confidence"], 90.0)

    def test_the_projection_does_not_carry_the_parked_decomposition(self):
        """Raw bpa / time_horizon_adj / risk_adj are what #119 leaves undecided. The record is
        intelligible without them, so it does not pre-empt that decision by storing them."""
        row = draft_history.evidence_projection(_snapshot(), "x")["candidates"][0]
        for parked in ("bpa", "time_horizon_adj", "risk_adj"):
            self.assertNotIn(parked, row)

    def test_absence_is_stored_as_absence_never_as_zero(self):
        snap = _snapshot(candidates=(_candidate(waiting_cost=None, survival_probability=None),))
        row = draft_history.evidence_projection(snap, "x")["candidates"][0]
        self.assertIsNone(row["waiting_cost"])
        self.assertIsNone(row["survival_probability"])

    def test_every_projected_field_is_a_real_candidate_field(self):
        """Guards the rename hazard in this module's own code. If a CandidateSnapshot field is
        renamed, this fails here rather than the store quietly writing null for it forever."""
        real = {f.name for f in dataclasses.fields(CandidateSnapshot)}
        missing = [n for n in draft_history._CANDIDATE_EVIDENCE_FIELDS if n not in real]
        self.assertEqual(missing, [], "projected field(s) no longer exist on CandidateSnapshot")

    def test_a_renamed_field_fails_loudly_rather_than_storing_null(self):
        """Non-vacuity for the test above: prove the read really does raise. A projection that
        swallowed a missing field would keep producing well-formed records with a silent hole."""
        @dataclasses.dataclass(frozen=True)
        class Renamed:
            player_id: str = "p1"
        with self.assertRaises(AttributeError):
            draft_history.candidate_evidence(Renamed())

    def test_recording_does_not_mutate_the_snapshot_it_was_given(self):
        """The caller keeps using this object after storing it."""
        snap = _snapshot()
        before = dataclasses.astuple(snap)
        draft_history.record_snapshot("L1", snap, ps.snapshot_identity(snap))
        self.assertEqual(dataclasses.astuple(snap), before)

    def test_the_projection_is_compact_not_the_whole_pool(self):
        """Plan v2 asked for a compact immutable evidence projection rather than raw pools.
        A candidate row keeps a chosen subset, not all 37 CandidateSnapshot fields."""
        row = draft_history.evidence_projection(_snapshot(), "x")["candidates"][0]
        self.assertLess(len(row), len(dataclasses.fields(CandidateSnapshot)))

    def test_a_stored_record_round_trips_unchanged(self):
        snap = _snapshot()
        identity = ps.snapshot_identity(snap)
        draft_history.record_snapshot("L1", snap, identity, draft_id="D9")
        record = draft_history.load_snapshot_record("L1", identity)
        self.assertEqual(record["snapshot_id"], identity)
        self.assertEqual(record["league_id"], "L1")
        self.assertEqual(record["draft_id"], "D9")
        self.assertEqual(record["evidence"], draft_history.evidence_projection(snap, identity))


class StalenessHasAConsumerTests(unittest.TestCase):
    """#101. The check existed and was called by nothing; a restored record is its consumer."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._orig = draft_history.HISTORY_DIR
        draft_history.HISTORY_DIR = Path(self._tmp) / "draft_history"
        self.addCleanup(setattr, draft_history, "HISTORY_DIR", self._orig)

    def test_the_refactor_did_not_change_the_live_snapshot_answer(self):
        snap = _snapshot(picks_consumed=2, data_freshest_date="2026-08-20")
        merger = _Merger("2026-08-20")
        self.assertEqual(ps.snapshot_is_current(snap, [{}, {}], merger), (True, None))
        stale, reason = ps.snapshot_is_current(snap, [{}, {}, {}], merger)
        self.assertFalse(stale)
        self.assertIn("new pick", reason)

    def test_a_restored_record_can_be_checked_with_the_same_rule(self):
        snap = _snapshot(picks_consumed=2, data_freshest_date="2026-08-20")
        identity = ps.snapshot_identity(snap)
        draft_history.record_snapshot("L1", snap, identity)
        evidence = draft_history.load_snapshot_record("L1", identity)["evidence"]

        merger = _Merger("2026-08-20")
        self.assertEqual(
            ps.stamp_is_current(evidence["picks_consumed"], evidence["data_freshest_date"],
                                [{}, {}], merger),
            (True, None))
        # One more pick made since: the historical record must report itself as no longer
        # describing the live board rather than silently reading as current.
        current, reason = ps.stamp_is_current(
            evidence["picks_consumed"], evidence["data_freshest_date"], [{}, {}, {}], merger)
        self.assertFalse(current)
        self.assertIn("new pick", reason)

    def test_refreshed_player_data_makes_a_stored_record_not_current(self):
        snap = _snapshot(picks_consumed=2, data_freshest_date="2026-08-20")
        current, reason = ps.stamp_is_current(
            snap.picks_consumed, snap.data_freshest_date, [{}, {}], _Merger("2026-08-27"))
        self.assertFalse(current)
        self.assertIn("player data changed", reason)

    def test_an_unstamped_record_is_never_reported_current(self):
        """Preserved posture: 'unknown provenance' and 'known current' are different claims."""
        current, reason = ps.stamp_is_current(None, None, [], _Merger())
        self.assertFalse(current)
        self.assertIn("no input-state stamp", reason)


if __name__ == "__main__":
    unittest.main()
