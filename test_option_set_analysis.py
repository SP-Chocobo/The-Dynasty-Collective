import unittest

from draft_counterfactual import NodeComparison
from draft_simulation import DraftTrajectory, PickRecord
from option_set_analysis import analyze_option_sets


def _cand(id_, pos, uv, tav, necessity="NEUTRAL", forces=None):
    return {"id": id_, "name": f"Player {id_}", "pos": pos, "uv": uv, "tav": tav,
            "necessity": necessity, "forces": forces or []}


def _rec(pick_no, roster_id, chosen_id, candidates):
    return PickRecord(
        pick_no=pick_no, round=1, roster_id=roster_id, pick_label=f"1.{pick_no:02d}",
        chosen_player_id=chosen_id, decision_regime="contested",
        snapshot={"candidates": candidates},
    )


def _nc(pick_no, roster_id, bpa_id, bpa_name, bpa_pos, bpa_uv, equals_bpa):
    return NodeComparison(
        pick_no=pick_no, pick_label=f"1.{pick_no:02d}", roster_id=roster_id,
        engine_player_id="x", engine_player_name="Engine Pick", engine_position="RB",
        engine_uv=1.0, engine_tav=1.0, engine_necessity="NEUTRAL", engine_near_tie=False,
        bpa_player_id=bpa_id, bpa_player_name=bpa_name, bpa_position=bpa_pos,
        bpa_uv=bpa_uv, bpa_tav=bpa_uv,
        adp_available=False, adp_unavailable_reason="n/a", adp_player_id=None,
        adp_player_name=None, adp_consensus_rank=None, adp_tav=None,
        regret_vs_bpa=0.0, regret_vs_adp=None,
        equals_bpa=equals_bpa, equals_adp=None, deviation_supported=None,
    )


class AnalyzeOptionSetsTests(unittest.TestCase):
    def test_one_record_per_pick_in_order(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(
            _rec(1, "A", "1", candidates), _rec(2, "B", "2", candidates),
        ))
        comparisons = [
            _nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True),
            _nc(2, "B", "2", "Player 2", "WR", 9.0, equals_bpa=True),
        ]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertEqual([r.pick_no for r in records], [1, 2])

    def test_bpa_visible_true_when_bpa_id_is_in_the_narrowed_set(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertTrue(records[0].bpa_visible)

    def test_bpa_visible_false_when_bpa_id_is_excluded_from_the_narrowed_set(self):
        # BPA (id "99", uv=15.0) never made it into this pick's own narrowed candidate list --
        # this is exactly the blind-spot narrow_candidates' own docstring warns is possible.
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "99", "Player 99", "QB", 15.0, equals_bpa=False)]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertFalse(records[0].bpa_visible)

    def test_uv_gap_vs_narrowed_floor_measures_the_size_of_an_invisible_miss(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "99", "Player 99", "QB", 15.0, equals_bpa=False)]
        records = analyze_option_sets(comparisons, trajectory)
        # narrowed floor uv is min(10.0, 9.0) = 9.0; bpa uv is 15.0 -> gap 6.0
        self.assertEqual(records[0].narrowed_floor_uv, 9.0)
        self.assertEqual(records[0].uv_gap_vs_narrowed_floor, 6.0)

    def test_uv_gap_is_never_negative_when_bpa_is_visible(self):
        # When BPA is visible, it is itself a member of the narrowed set, so its own uv can
        # never be below that set's own floor (minimum) -- the gap must be >= 0.
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertGreaterEqual(records[0].uv_gap_vs_narrowed_floor, 0.0)

    def test_distinct_positions_counts_unique_positions_in_the_narrowed_set(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5), _cand("3", "RB", 8.0, 8.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertEqual(records[0].distinct_positions, 2)
        self.assertEqual(records[0].option_set_size, 3)

    def test_tav_spread_is_max_minus_min_tav_in_the_narrowed_set(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 4.0)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        records = analyze_option_sets(comparisons, trajectory)
        self.assertEqual(records[0].tav_spread, 6.0)

    def test_mismatched_lengths_between_comparisons_and_trajectory_raises(self):
        candidates = [_cand("1", "RB", 10.0, 10.0)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates), _rec(2, "A", "1", candidates)))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        with self.assertRaises(ValueError):
            analyze_option_sets(comparisons, trajectory)

    def test_determinism_repeated_analysis_is_identical(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "99", "Player 99", "QB", 15.0, equals_bpa=False)]
        first = analyze_option_sets(comparisons, trajectory)
        second = analyze_option_sets(comparisons, trajectory)
        self.assertEqual(first, second)

    def test_does_not_mutate_inputs(self):
        candidates = [_cand("1", "RB", 10.0, 10.0), _cand("2", "WR", 9.0, 9.5)]
        trajectory = DraftTrajectory(config={}, picks=(_rec(1, "A", "1", candidates),))
        comparisons = [_nc(1, "A", "1", "Player 1", "RB", 10.0, equals_bpa=True)]
        snapshot_before = trajectory.picks[0].snapshot["candidates"][0].copy()
        comparison_before = comparisons[0]
        analyze_option_sets(comparisons, trajectory)
        self.assertEqual(trajectory.picks[0].snapshot["candidates"][0], snapshot_before)
        self.assertEqual(comparisons[0], comparison_before)


if __name__ == "__main__":
    unittest.main()
