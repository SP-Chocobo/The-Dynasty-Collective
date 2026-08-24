"""roster_diagnostics must stay decomposable -- these tests pin that every field traces to an
existing mechanism (lineup_optimizer, depth_ratings, draft_room.replacement_levels), that it
never invents a single power score, and that it doesn't mutate its inputs.
"""

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_simulation import simulate_full_draft
from roster_diagnostics import TeamDiagnostics, compute_team_diagnostics


def _build_pool_players_db(positions=("QB", "RB", "WR", "TE")):
    merger = dm.DataMerger()
    proj = merger.projections
    players_db = {}
    pid = 0
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return merger, players_db


class ComputeTeamDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=3)  # 12 picks
        cls.trajectory = simulate_full_draft(cls.merger, cls.players_db, cls.league, pick_order)
        cls.league_before = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in cls.league.items()}
        cls.players_db_before = {k: dict(v) for k, v in cls.players_db.items()}
        cls.diagnostics = compute_team_diagnostics(cls.merger, cls.players_db, cls.league, cls.trajectory)

    def test_one_diagnostics_entry_per_team(self):
        self.assertEqual(set(self.diagnostics), {"1", "2", "3", "4"})

    def test_accumulated_value_is_the_plain_sum_of_uv(self):
        rid = "1"
        expected = round(sum(
            next(c for c in rec.snapshot["candidates"] if c["id"] == rec.chosen_player_id)["uv"]
            for rec in self.trajectory.picks if rec.roster_id == rid
        ), 2)
        self.assertAlmostEqual(self.diagnostics[rid].accumulated_value, expected, places=1)

    def test_starting_lineup_value_never_exceeds_accumulated_value(self):
        # A team can never start more value than it actually rostered -- the optimizer can only
        # select a subset (bounded by real slot counts), never invent extra value.
        for d in self.diagnostics.values():
            self.assertLessEqual(d.starting_lineup_value, d.accumulated_value + 1e-6)

    def test_bench_surplus_is_accumulated_minus_starting(self):
        for d in self.diagnostics.values():
            self.assertAlmostEqual(d.bench_surplus_value, round(d.accumulated_value - d.starting_lineup_value, 2), places=1)
            self.assertGreaterEqual(d.bench_surplus_value, -1e-6)

    def test_positional_counts_sum_to_total_picks_per_team(self):
        for rid, d in self.diagnostics.items():
            team_picks = sum(1 for rec in self.trajectory.picks if rec.roster_id == rid)
            self.assertEqual(sum(d.positional_counts.values()), team_picks)

    def test_thin_positions_only_named_from_positions_actually_rostered(self):
        for d in self.diagnostics.values():
            for pos in d.thin_positions:
                self.assertIn(pos, d.positional_counts)

    def test_structural_holes_are_usable_positions_with_zero_players(self):
        for d in self.diagnostics.values():
            for pos in d.structural_holes:
                self.assertNotIn(pos, d.positional_counts)

    def test_no_single_aggregate_power_score_field_exists(self):
        # The hard contract: every field is a named, decomposable measurement -- there must be
        # no field that reads as one rolled-up "team strength" number.
        fields = TeamDiagnostics.__dataclass_fields__.keys()
        for banned in ("power_score", "strength_score", "team_score", "overall_score", "rating"):
            self.assertNotIn(banned, fields)

    def test_does_not_mutate_league_or_players_db(self):
        self.assertEqual(self.league, self.league_before)
        self.assertEqual(self.players_db, self.players_db_before)


if __name__ == "__main__":
    unittest.main()
