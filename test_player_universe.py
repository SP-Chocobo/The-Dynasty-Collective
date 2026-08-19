import unittest

from player_universe import available_players, build_player_universe, matching_players


class PlayerUniverseTests(unittest.TestCase):
    def setUp(self):
        self.players = {
            "1": {"full_name": "Rostered Runner", "position": "RB", "team": "ATL", "active": True},
            "2": {"full_name": "Available Receiver", "position": "WR", "team": "BUF", "active": True},
            "3": {"full_name": "Retired Back", "position": "RB", "team": "FA", "active": False},
        }
        self.rosters = [{"roster_id": 4, "owner_id": "user-1", "players": ["1", "missing"], "starters": ["1"], "taxi": [], "reserve": ["missing"]}]

    def test_sleeper_players_exist_without_draft_sharks(self):
        universe = build_player_universe(self.players, self.rosters, users=[{"user_id": "user-1", "display_name": "Team One"}])
        by_id = {row["player_id"]: row for row in universe}
        self.assertEqual(by_id["2"]["ownership"], "FREE AGENT")
        self.assertTrue(by_id["2"]["available"])
        self.assertEqual(by_id["1"]["roster_slot"], "Starter")

    def test_rostered_player_survives_missing_sleeper_metadata(self):
        universe = build_player_universe(self.players, self.rosters)
        missing = next(row for row in universe if row["player_id"] == "missing")
        self.assertEqual(missing["ownership"], "ROSTERED")
        self.assertEqual(missing["roster_slot"], "IR")

    def test_native_projection_and_query_lookup_are_independent_of_enrichment(self):
        universe = build_player_universe(self.players, self.rosters, projections={"2": {"rec": 4, "rec_yd": 50}}, scoring_settings={"rec": 1, "rec_yd": .1})
        available = available_players(universe)
        receiver = next(row for row in available if row["player_id"] == "2")
        self.assertEqual(receiver["sleeper_proj"], 9.0)
        self.assertEqual([row["player_id"] for row in matching_players(universe, "Should I add Available Receiver?")], ["2"])

    def test_inactive_players_can_be_requested_for_audit(self):
        normal_ids = {row["player_id"] for row in build_player_universe(self.players, self.rosters)}
        all_ids = {row["player_id"] for row in build_player_universe(self.players, self.rosters, include_inactive=True)}
        self.assertNotIn("3", normal_ids)
        self.assertIn("3", all_ids)


if __name__ == "__main__":
    unittest.main()
