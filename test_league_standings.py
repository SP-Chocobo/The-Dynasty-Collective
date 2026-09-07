"""league_standings is a pure read over Sleeper's own roster.settings fields -- these tests
pin that every value is a direct, unmodified read (or an honest zero-default), and that
sorting follows the league's real record, never an invented rating."""

import unittest

from league_standings import has_record, team_standings


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

    def test_missing_settings_block_reads_as_absent_not_as_a_zero_record(self):
        # Was `assertEqual(rows[0]["wins"], 0)`: a roster Sleeper reported no settings for
        # rendered identically to a team that has played and stands at 0-0-0, and the League
        # view then STATED "no games played yet this season (0-0 across the board)" off it.
        rows = team_standings([{"roster_id": 1}], {1: "X"})
        self.assertIsNone(rows[0]["wins"])
        self.assertIsNone(rows[0]["losses"])
        self.assertIsNone(rows[0]["ties"])
        self.assertIsNone(rows[0]["points_for"])
        self.assertFalse(has_record(rows[0]))

    def test_a_measured_zero_record_is_still_a_zero_not_an_absence(self):
        # The other half of the same contract: 0-0-0 with points reported is a real, measured
        # standing and must keep rendering as the number 0.
        rows = team_standings([_roster(1)], {1: "X"})
        self.assertEqual(rows[0]["wins"], 0)
        self.assertEqual(rows[0]["points_for"], 0.0)
        self.assertTrue(has_record(rows[0]))

    def test_an_explicit_null_field_is_absent_not_zero(self):
        # `.get(k, 0) or 0` collapsed an explicit null the same way it collapsed a missing key.
        rows = team_standings([{"roster_id": 1, "settings": {"wins": None, "losses": 2, "ties": 0}}], {1: "X"})
        self.assertIsNone(rows[0]["wins"])
        self.assertEqual(rows[0]["losses"], 2)
        self.assertFalse(has_record(rows[0]))

    def test_a_reported_whole_with_no_decimal_remainder_keeps_the_total_it_has(self):
        rows = team_standings([{"roster_id": 1, "settings": {"fpts": 88}}], {1: "X"})
        self.assertEqual(rows[0]["points_for"], 88.0)

    def test_teams_with_no_record_order_last_and_never_outrank_a_measured_one(self):
        rows = team_standings(
            [{"roster_id": 1}, _roster(2, wins=0, losses=1), {"roster_id": 3}],
            {1: "Zeta", 2: "Beaten", 3: "Alpha"},
        )
        # The 0-1 team is measured and outranks both unreported ones, which sort last
        # alphabetically among themselves rather than being compared as numbers.
        self.assertEqual([r["team"] for r in rows], ["Beaten", "Alpha", "Zeta"])

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
