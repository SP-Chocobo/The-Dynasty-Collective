"""lineup_readiness is a pure read of already-computed facts -- these tests pin that it never
invents a recommendation, never re-derives depth_ratings' own judgment, and handles the
no-team-resolved / no-depth-data edge cases without crashing."""

import unittest

from lineup_readiness import compute_readiness


def _row(**overrides) -> dict:
    base = dict(name="Ja'Marr Chase", position="WR", team="CIN", slot="Starter", injury_status=None)
    base.update(overrides)
    return base


def _cell(count, value=None):
    return {"count": count, "value": value}


class ComputeReadinessTests(unittest.TestCase):
    def test_total_starting_slots_passes_through_unmodified(self):
        result = compute_readiness([], {}, None, total_starting_slots=9)
        self.assertEqual(result["total_starting_slots"], 9)

    def test_filled_starting_slots_counts_only_starter_rows(self):
        roster = [_row(slot="Starter"), _row(slot="Starter"), _row(slot="Bench"), _row(slot="TAXI")]
        result = compute_readiness(roster, {}, None, total_starting_slots=9)
        self.assertEqual(result["filled_starting_slots"], 2)

    def test_starter_injury_flag_included(self):
        roster = [_row(slot="Starter", injury_status="Questionable")]
        result = compute_readiness(roster, {}, None, total_starting_slots=1)
        self.assertEqual(len(result["starter_injury_flags"]), 1)
        self.assertEqual(result["starter_injury_flags"][0]["name"], "Ja'Marr Chase")

    def test_bench_injury_is_not_a_starter_flag(self):
        roster = [_row(slot="Bench", injury_status="Questionable")]
        result = compute_readiness(roster, {}, None, total_starting_slots=1)
        self.assertEqual(result["starter_injury_flags"], [])

    def test_healthy_starter_produces_no_flag(self):
        roster = [_row(slot="Starter", injury_status=None)]
        result = compute_readiness(roster, {}, None, total_starting_slots=1)
        self.assertEqual(result["starter_injury_flags"], [])

    def test_thin_position_surfaces_using_shared_depth_ratings_judgment(self):
        # Team's WR cell (count=1) is well below peers (count=5 each) -- depth_ratings should
        # call this Weak, and that exact label should show up unmodified here.
        depth = {
            "My Team": {"WR": _cell(1, 50)},
            "Rival A": {"WR": _cell(5, 400)},
            "Rival B": {"WR": _cell(5, 400)},
        }
        result = compute_readiness([], depth, "My Team", total_starting_slots=9)
        self.assertEqual(len(result["thin_positions"]), 1)
        self.assertEqual(result["thin_positions"][0]["position"], "WR")
        self.assertEqual(result["thin_positions"][0]["label"], "Weak")

    def test_strong_position_never_flagged(self):
        depth = {
            "My Team": {"WR": _cell(5, 400)},
            "Rival A": {"WR": _cell(1, 50)},
        }
        result = compute_readiness([], depth, "My Team", total_starting_slots=9)
        self.assertEqual(result["thin_positions"], [])

    def test_unresolved_team_label_produces_no_thin_positions_not_a_crash(self):
        depth = {"Some Other Team": {"WR": _cell(1, 50)}}
        result = compute_readiness([], depth, None, total_starting_slots=9)
        self.assertEqual(result["thin_positions"], [])

    def test_team_absent_from_depth_produces_no_thin_positions_not_a_crash(self):
        depth = {"Some Other Team": {"WR": _cell(1, 50)}}
        result = compute_readiness([], depth, "My Team", total_starting_slots=9)
        self.assertEqual(result["thin_positions"], [])

    def test_empty_depth_produces_no_thin_positions(self):
        result = compute_readiness([], {}, "My Team", total_starting_slots=9)
        self.assertEqual(result["thin_positions"], [])

    def test_never_invents_a_start_sit_recommendation(self):
        # This module answers "is there a problem," never "what should I do about it" -- no
        # key names or produces a per-player "should_start"/"recommendation" verdict.
        roster = [_row(slot="Starter", injury_status="Questionable"), _row(name="B", slot="Bench")]
        depth = {"My Team": {"WR": _cell(1, 50)}, "Rival": {"WR": _cell(5, 400)}}
        result = compute_readiness(roster, depth, "My Team", total_starting_slots=1)
        banned = ("recommend", "should_start", "should_sit", "verdict")
        self.assertFalse(any(b in key.lower() for key in result for b in banned))
        for flag in result["starter_injury_flags"]:
            self.assertFalse(any(b in key.lower() for key in flag for b in banned))


if __name__ == "__main__":
    unittest.main()
