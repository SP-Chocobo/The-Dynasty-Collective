import shutil
import tempfile
import unittest
from pathlib import Path

import league_prefs as lp


class LeaguePrefsTests(unittest.TestCase):
    """Points PREFS_PATH at a throwaway temp file for the duration of each test, never
    touching real data/league_prefs.json."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_path = lp.PREFS_PATH
        lp.PREFS_PATH = Path(self._tmpdir) / "league_prefs.json"
        self.user_id = "user123"
        self.leagues = [
            {"league_id": "a", "name": "League A"},
            {"league_id": "b", "name": "League B"},
            {"league_id": "c", "name": "League C"},
        ]
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, lp, "PREFS_PATH", self._orig_path)

    def test_no_prefs_yet_returns_empty_defaults(self):
        self.assertEqual(lp.get_prefs(self.user_id), {"order": [], "archived": []})

    def test_sorted_leagues_with_no_prefs_returns_discovery_order_all_visible(self):
        visible, archived = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "b", "c"])
        self.assertEqual(archived, [])

    def test_toggle_archive_moves_a_league_to_archived(self):
        lp.toggle_archive(self.user_id, "b")
        visible, archived = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "c"])
        self.assertEqual([lg["league_id"] for lg in archived], ["b"])

    def test_toggle_archive_again_unarchives_it(self):
        lp.toggle_archive(self.user_id, "b")
        lp.toggle_archive(self.user_id, "b")
        visible, archived = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "b", "c"])
        self.assertEqual(archived, [])

    def test_move_league_earlier(self):
        lp.move_league(self.user_id, self.leagues, "c", -1)
        visible, _ = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "c", "b"])

    def test_move_league_later(self):
        lp.move_league(self.user_id, self.leagues, "a", 1)
        visible, _ = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["b", "a", "c"])

    def test_move_league_past_the_edge_is_a_no_op(self):
        lp.move_league(self.user_id, self.leagues, "a", -1)  # already first
        visible, _ = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "b", "c"])
        lp.move_league(self.user_id, self.leagues, "c", 1)  # already last
        visible, _ = lp.sorted_leagues(self.user_id, self.leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "b", "c"])

    def test_newly_discovered_league_appends_to_the_end(self):
        lp.move_league(self.user_id, self.leagues, "c", -1)  # order becomes a, c, b
        new_leagues = self.leagues + [{"league_id": "d", "name": "League D"}]
        visible, _ = lp.sorted_leagues(self.user_id, new_leagues)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "c", "b", "d"])

    def test_a_league_no_longer_discovered_is_dropped_from_the_order(self):
        remaining = self.leagues[:2]  # "c" no longer returned by Sleeper
        visible, _ = lp.sorted_leagues(self.user_id, remaining)
        self.assertEqual([lg["league_id"] for lg in visible], ["a", "b"])

    def test_forget_league_removes_it_from_order_and_archived(self):
        lp.move_league(self.user_id, self.leagues, "a", 1)  # persists a real "order" list
        self.assertIn("b", lp.get_prefs(self.user_id)["order"])  # sanity: "b" is really in there
        lp.toggle_archive(self.user_id, "b")
        lp.forget_league(self.user_id, "b")
        prefs = lp.get_prefs(self.user_id)
        self.assertNotIn("b", prefs["order"])
        self.assertNotIn("b", prefs["archived"])

    def test_users_are_independent(self):
        lp.toggle_archive("user_a", "b")
        self.assertEqual(lp.get_prefs("user_b"), {"order": [], "archived": []})


if __name__ == "__main__":
    unittest.main()
