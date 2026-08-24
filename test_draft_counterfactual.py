"""draft_counterfactual is measurement, never judgment -- these tests pin that it correctly
reconstructs historical state (never replaying/mutating the source trajectory), that BPA is
computed off the FULL undrafted board (not narrow_candidates' narrowed shortlist, which can
omit the true UV-argmax), that ADP is honestly reported unavailable for a 1QB league rather
than approximated, and that repeated runs against the same trajectory are deterministic.
"""

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_counterfactual import bpa_row, compare_trajectory
from draft_simulation import simulate_full_draft


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


class CompareTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league_1qb = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        cls.league_sf = dr.build_mock_league(teams=4, superflex=True, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=2)  # 8 picks
        cls.traj_1qb = simulate_full_draft(cls.merger, cls.players_db, cls.league_1qb, pick_order)
        cls.traj_sf = simulate_full_draft(cls.merger, cls.players_db, cls.league_sf, pick_order)
        cls.comparisons_1qb = compare_trajectory(cls.merger, cls.players_db, cls.league_1qb, cls.traj_1qb)
        cls.comparisons_sf = compare_trajectory(cls.merger, cls.players_db, cls.league_sf, cls.traj_sf)

    def test_one_comparison_per_pick(self):
        self.assertEqual(len(self.comparisons_1qb), len(self.traj_1qb.picks))

    def test_engine_player_matches_the_trajectorys_own_recorded_choice(self):
        for cmp_, rec in zip(self.comparisons_1qb, self.traj_1qb.picks):
            self.assertEqual(cmp_.engine_player_id, rec.chosen_player_id)
            self.assertEqual(cmp_.pick_no, rec.pick_no)
            self.assertEqual(cmp_.roster_id, rec.roster_id)

    def test_regret_vs_bpa_is_never_negative(self):
        # The engine always takes the TAV-argmax on its own board -- by construction, its TAV
        # can never be lower than the BPA player's TAV on that same board.
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            self.assertGreaterEqual(cmp_.regret_vs_bpa, -1e-6)

    def test_equals_bpa_implies_zero_regret(self):
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if cmp_.equals_bpa:
                self.assertAlmostEqual(cmp_.regret_vs_bpa, 0.0, places=2)

    def test_deviation_supported_is_none_only_when_equals_bpa(self):
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if cmp_.equals_bpa:
                self.assertIsNone(cmp_.deviation_supported)
            else:
                self.assertIn(cmp_.deviation_supported, (True, False))

    def test_adp_unavailable_for_1qb_league_with_a_stated_reason(self):
        # The real, honest limitation: no KTC consensus is loaded for a 1QB league by design.
        for cmp_ in self.comparisons_1qb:
            self.assertFalse(cmp_.adp_available)
            self.assertIsNone(cmp_.adp_player_id)
            self.assertIsNone(cmp_.equals_adp)
            self.assertIsNotNone(cmp_.adp_unavailable_reason)

    def test_bpa_is_uv_argmax_not_tav_argmax_on_a_synthetic_board(self):
        # Direct, deterministic proof of the property this module depends on -- doesn't rely on
        # a real draft happening to produce a case where UV-argmax and TAV-argmax diverge (the
        # small fixture used elsewhere in this file usually doesn't hit one).
        board = [
            {"player_id": "1", "name": "High UV, suppressed TAV", "universal_value": 99.0, "final_score": 10.0, "position": "RB"},
            {"player_id": "2", "name": "Lower UV, high TAV (need-boosted)", "universal_value": 50.0, "final_score": 90.0, "position": "WR"},
        ]
        self.assertEqual(bpa_row(board)["player_id"], "1")


    def test_determinism_repeated_comparison_is_identical(self):
        again = compare_trajectory(self.merger, self.players_db, self.league_1qb, self.traj_1qb)
        for a, b in zip(self.comparisons_1qb, again):
            self.assertEqual(a, b)


class NoMutationTests(unittest.TestCase):
    def test_does_not_mutate_the_trajectory_or_its_inputs(self):
        merger, players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=1)
        traj = simulate_full_draft(merger, players_db, league, pick_order)
        picks_before = tuple(traj.picks)
        league_before = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in league.items()}
        players_db_before = {k: dict(v) for k, v in players_db.items()}

        compare_trajectory(merger, players_db, league, traj)

        self.assertEqual(traj.picks, picks_before)
        self.assertEqual(league, league_before)
        self.assertEqual(players_db, players_db_before)


if __name__ == "__main__":
    unittest.main()
