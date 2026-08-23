"""league_standings is a pure read over Sleeper's own roster.settings fields -- these tests
pin that every value is a direct, unmodified read (or an honest zero-default), and that
sorting follows the league's real record, never an invented rating."""

import unittest

from league_standings import team_standings


def _roster(roster_id, **settings_overrides) -> dict:
    settings = {"wins": 0, "losses": 0, "ties": 0, "fpts": 0, "fpts_decimal": 0,
                "fpts_against": 0, "fpts_against_decimal": 0}
    settings.update(settings_overrides)
    return {"roster_id": roster_id, "settings": settings}


class TeamStandingsTests(unittest.TestCase):
    def test_wins_losses_ties_pass_through_unmodified(self):
        rows = team_standings([_roster(1, wins=9, losses=4, ties=1)], {1: "Squad A"})
        self.assertEqual(rows[0]["wins"], 9)
        self.assertEqual(rows[0]["losses"], 4)
        self.assertEqual(rows[0]["ties"], 1)

    def test_team_label_resolved_from_owner_names(self):
        rows = team_standings([_roster(1)], {1: "The Sicko Six"})
        self.assertEqual(rows[0]["team"], "The Sicko Six")

    def test_missing_owner_name_falls_back_to_roster_label(self):
        rows = team_standings([_roster(7)], {})
        self.assertEqual(rows[0]["team"], "Roster 7")

    def test_points_combine_whole_and_decimal_fields(self):
        rows = team_standings([_roster(1, fpts=110, fpts_decimal=42)], {1: "X"})
        self.assertEqual(rows[0]["points_for"], 110.42)

    def test_points_against_also_combines_whole_and_decimal(self):
        rows = team_standings([_roster(1, fpts_against=98, fpts_against_decimal=7)], {1: "X"})
        self.assertEqual(rows[0]["points_against"], 98.07)

    def test_missing_settings_block_reads_as_all_zero_not_a_crash(self):
        rows = team_standings([{"roster_id": 1}], {1: "X"})
        self.assertEqual(rows[0]["wins"], 0)
        self.assertEqual(rows[0]["points_for"], 0)

    def test_sorted_by_wins_descending_first(self):
        rows = team_standings(
            [_roster(1, wins=5), _roster(2, wins=9), _roster(3, wins=7)], {1: "A", 2: "B", 3: "C"},
        )
        self.assertEqual([r["team"] for r in rows], ["B", "C", "A"])

    def test_points_for_is_the_tiebreak_when_wins_are_equal(self):
        rows = team_standings(
            [_roster(1, wins=6, fpts=1000), _roster(2, wins=6, fpts=1200)], {1: "A", 2: "B"},
        )
        self.assertEqual([r["team"] for r in rows], ["B", "A"])

    def test_never_computes_a_rating_or_score_field(self):
        rows = team_standings([_roster(1, wins=8, fpts=1100)], {1: "X"})
        self.assertEqual(
            set(rows[0].keys()),
            {"roster_id", "team", "wins", "losses", "ties", "points_for", "points_against"},
        )

    def test_empty_roster_list_returns_empty(self):
        self.assertEqual(team_standings([], {}), [])


if __name__ == "__main__":
    unittest.main()
