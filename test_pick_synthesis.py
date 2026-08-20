"""
Covers pick_synthesis.py's real job: turning draft_room.py/draft_strategy.py's numbers into one
frozen, fully decomposed snapshot without inventing or recomputing any of them, plus the two
genuinely new pieces this module adds (positional_cliff, expected_value_of_waiting) and the
structured audit-trail diff (diff_snapshots) the whole "Debate My Pick" feature was built to
support.
"""

import unittest

import dataclasses

import data_merger as dm
import draft_strategy as ds
import pick_synthesis as ps

LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}


def _row(player_id, position, bpa):
    return {"player_id": player_id, "position": position, "bpa": bpa}


class DetectPositionalCliffTests(unittest.TestCase):
    def test_a_big_gap_relative_to_the_positions_typical_gap_is_a_high_cliff(self):
        board = [
            _row("1", "WR", 95.0), _row("2", "WR", 60.0),  # 35-point gap here
            _row("3", "WR", 57.0), _row("4", "WR", 54.0), _row("5", "WR", 51.0),  # ~3-point typical gaps
        ]
        result = ps.detect_positional_cliff(board, "1")
        self.assertEqual(result["tier"], "HIGH")
        self.assertAlmostEqual(result["gap"], 35.0)

    def test_a_gap_in_line_with_the_positions_typical_gap_is_low(self):
        board = [_row(str(i), "RB", 90.0 - i * 3) for i in range(6)]  # perfectly uniform 3-point gaps
        result = ps.detect_positional_cliff(board, "0")
        self.assertEqual(result["tier"], "LOW")

    def test_none_when_the_player_is_the_last_one_left_at_his_position(self):
        board = [_row("1", "TE", 40.0), _row("2", "TE", 10.0), _row("3", "TE", 5.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "3"))

    def test_none_when_too_few_players_remain_at_the_position(self):
        board = [_row("1", "TE", 40.0), _row("2", "TE", 10.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "1"))

    def test_none_when_the_player_is_not_on_the_board(self):
        board = [_row("1", "WR", 90.0), _row("2", "WR", 80.0), _row("3", "WR", 70.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "999"))


class ExpectedValueOfWaitingTests(unittest.TestCase):
    def test_none_when_survival_is_unknown(self):
        self.assertIsNone(ps.expected_value_of_waiting(90.0, None))

    def test_scales_universal_value_by_survival_probability(self):
        self.assertEqual(ps.expected_value_of_waiting(90.0, 0.2), 18.0)

    def test_certain_survival_returns_full_universal_value(self):
        self.assertEqual(ps.expected_value_of_waiting(90.0, 1.0), 90.0)


class NarrowCandidatesTests(unittest.TestCase):
    def _board(self):
        return [{"player_id": str(i), "final_score": 100 - i, "position": "WR"} for i in range(10)]

    def test_takes_the_top_n_by_final_score(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3)
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])

    def test_appends_a_user_selected_player_not_already_in_the_top_slice(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="7")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2", "7"])

    def test_does_not_duplicate_a_user_selected_player_already_in_the_top_slice(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="1")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])

    def test_a_user_selected_player_not_on_the_board_at_all_is_silently_skipped(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="does-not-exist")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])


class BuildSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(40)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_snapshot_is_narrowed_and_ranked_by_team_acquisition_value(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5,
        )
        self.assertEqual(len(snap.candidates), 5)
        values = [c.team_acquisition_value for c in snap.candidates]
        self.assertEqual(values, sorted(values, reverse=True), "candidates must be ranked by team_acquisition_value")

    def test_every_candidate_carries_the_full_real_decomposition(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3,
        )
        for c in snap.candidates:
            self.assertIsInstance(c.universal_value, float)
            self.assertIsInstance(c.team_acquisition_value, float)
            self.assertIsNotNone(c.survival_probability)
            self.assertIsNotNone(c.opportunity_cost)
            self.assertIsNotNone(c.expected_value_of_waiting)
            # team_acquisition_value must equal the documented sum -- the same invariant
            # test_draft_room.py enforces end-to-end, re-checked here since this module is
            # the one actually handing these numbers to the LLM debate layer.
            self.assertAlmostEqual(
                c.team_acquisition_value, c.universal_value + c.need_bonus + c.eligibility_bonus, places=2,
            )

    def test_snapshot_is_genuinely_frozen(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=2,
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap.pick_label = "2.01"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap.candidates[0].universal_value = 999.0

    def test_position_run_detected_matches_draft_strategys_own_signal(self):
        # Draft 3 of the last 4 picks at the same real position -- a genuine run by
        # draft_strategy.detect_positional_run's own definition, not a synthetic flag.
        rb_ids = [pid for pid, info in self.players_db.items() if info["position"] == "RB"][:3]
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"][:1]
        picks = [{"roster_id": "2", "player_id": pid, "round": 1} for pid in (rb_ids[:2] + wr_ids + rb_ids[2:3])]
        run_position = ds.detect_positional_run(picks, self.players_db)
        self.assertEqual(run_position, "RB", "fixture didn't actually produce a real RB run -- test setup is wrong")

        snap = ps.build_snapshot(
            self.merger, self.players_db, picks, self.pick_order, current_index=len(picks), my_roster_id="1",
            league=LEAGUE, pick_label="1.05", top_n=8,
        )
        for c in snap.candidates:
            self.assertEqual(c.position_run_detected, c.position == "RB")

    def test_a_user_selected_player_outside_the_top_n_is_still_included(self):
        board_snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3,
        )
        top_ids = {c.player_id for c in board_snap.candidates}
        far_pick = next(pid for pid, info in self.players_db.items() if pid not in top_ids and info["position"] == "TE")
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3, user_selected_player_id=far_pick,
        )
        self.assertIn(far_pick, {c.player_id for c in snap.candidates})
        self.assertEqual(snap.user_selected_player_id, far_pick)


class DiffSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("RB", "WR"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(30)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_a_candidate_present_in_both_snapshots_reports_real_deltas(self):
        before = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=8,
        )
        # Draft away the current #1 candidate -- a real board-state change, not a synthetic one.
        top_id = before.candidates[0].player_id
        picks = [{"roster_id": "2", "player_id": top_id, "round": 1}]
        after = ps.build_snapshot(
            self.merger, self.players_db, picks, self.pick_order, current_index=1, my_roster_id="1",
            league=LEAGUE, pick_label="1.02", top_n=8,
        )
        diffs = ps.diff_snapshots(before, after)
        by_id = {d["player_id"]: d for d in diffs}
        # The drafted player no longer appears in the "after" snapshot's own candidate pool.
        self.assertIn(top_id, by_id)
        self.assertFalse(by_id[top_id]["entered"])
        # At least one remaining real candidate should show an actual, non-empty delta --
        # replacement level shifted for everyone at that position once a real pick landed.
        real_deltas = [d for d in diffs if d.get("entered") is None and d["deltas"]]
        self.assertTrue(real_deltas, "expected at least one candidate to show a real component delta after a pick")

    def test_identical_snapshots_produce_no_deltas(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5,
        )
        diffs = ps.diff_snapshots(snap, snap)
        for d in diffs:
            self.assertIsNone(d.get("entered"))
            self.assertEqual(d["rank_delta"], 0)
            self.assertEqual(d["deltas"], {})


if __name__ == "__main__":
    unittest.main()
