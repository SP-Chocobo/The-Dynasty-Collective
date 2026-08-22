import unittest

import sleeper_client as sc


class ComputePointsFromStatsTests(unittest.TestCase):
    def test_weighted_sum_matches_sleepers_own_math(self):
        stats = {"pass_yd": 300, "pass_td": 2, "rec": 5}
        scoring = {"pass_yd": 0.04, "pass_td": 4, "rec": 1}
        # 300*0.04 + 2*4 + 5*1 = 12 + 8 + 5 = 25
        self.assertAlmostEqual(sc.compute_points_from_stats(stats, scoring), 25.0)

    def test_missing_stat_category_contributes_zero(self):
        stats = {"pass_yd": 100}
        scoring = {"pass_yd": 0.04, "rec": 1}  # no "rec" in stats at all
        self.assertAlmostEqual(sc.compute_points_from_stats(stats, scoring), 4.0)

    def test_zero_stat_value_contributes_nothing(self):
        stats = {"fum_lost": 0, "pass_yd": 100}
        scoring = {"fum_lost": -2, "pass_yd": 0.04}
        self.assertAlmostEqual(sc.compute_points_from_stats(stats, scoring), 4.0)

    def test_none_stats_or_scoring_is_a_safe_zero(self):
        self.assertEqual(sc.compute_points_from_stats(None, {"rec": 1}), 0.0)
        self.assertEqual(sc.compute_points_from_stats({"rec": 5}, None), 0.0)
        self.assertEqual(sc.compute_points_from_stats(None, None), 0.0)

    def test_result_is_rounded_to_two_decimals(self):
        stats = {"rush_yd": 33}
        scoring = {"rush_yd": 0.1}
        self.assertEqual(sc.compute_points_from_stats(stats, scoring), 3.3)


class FindRosterForUserTests(unittest.TestCase):
    def test_finds_the_matching_roster(self):
        rosters = [{"owner_id": "111", "roster_id": 1}, {"owner_id": "222", "roster_id": 2}]
        self.assertEqual(sc.find_roster_for_user(rosters, "222")["roster_id"], 2)

    def test_no_match_returns_none(self):
        rosters = [{"owner_id": "111", "roster_id": 1}]
        self.assertIsNone(sc.find_roster_for_user(rosters, "999"))

    def test_empty_roster_list_returns_none(self):
        self.assertIsNone(sc.find_roster_for_user([], "111"))


class LeagueFormatSummaryTests(unittest.TestCase):
    def _league(self, **overrides):
        base = {
            "name": "Test League",
            "season": "2026",
            "settings": {"type": 2, "num_teams": 12, "taxi_slots": 2},
            "scoring_settings": {"rec": 1.0},
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN"],
            "total_rosters": 12,
        }
        base.update(overrides)
        return base

    def test_dynasty_type_detected(self):
        self.assertEqual(sc.league_format_summary(self._league())["type"], "Dynasty")

    def test_keeper_and_redraft_types(self):
        self.assertEqual(sc.league_format_summary(self._league(settings={"type": 1}))["type"], "Keeper")
        self.assertEqual(sc.league_format_summary(self._league(settings={"type": 0}))["type"], "Redraft")

    def _format_with_positions(self, positions):
        return sc.league_format_summary(self._league(roster_positions=positions))

    def test_superflex_detected_from_super_flex_slot(self):
        fmt = self._format_with_positions(["QB", "SUPER_FLEX", "RB", "WR"])
        self.assertTrue(fmt["superflex"])

    def test_superflex_detected_from_two_qb_slots(self):
        fmt = self._format_with_positions(["QB", "QB", "RB", "WR"])
        self.assertTrue(fmt["superflex"])

    def test_single_qb_is_not_superflex(self):
        fmt = self._format_with_positions(["QB", "RB", "WR", "FLEX"])
        self.assertFalse(fmt["superflex"])

    def test_full_ppr_scoring_label(self):
        fmt = sc.league_format_summary(self._league(scoring_settings={"rec": 1.0}))
        self.assertEqual(fmt["scoring"], "Full PPR")

    def test_half_ppr_scoring_label(self):
        fmt = sc.league_format_summary(self._league(scoring_settings={"rec": 0.5}))
        self.assertEqual(fmt["scoring"], "Half PPR")

    def test_standard_scoring_label(self):
        fmt = sc.league_format_summary(self._league(scoring_settings={"rec": 0}))
        self.assertEqual(fmt["scoring"], "Standard")
        fmt2 = sc.league_format_summary(self._league(scoring_settings={}))
        self.assertEqual(fmt2["scoring"], "Standard")

    def test_te_premium_detected_from_bonus_rec_te(self):
        fmt = sc.league_format_summary(self._league(scoring_settings={"rec": 1.0, "bonus_rec_te": 0.5}))
        self.assertTrue(fmt["te_premium"])

    def test_no_te_premium_when_bonus_absent_or_zero(self):
        self.assertFalse(sc.league_format_summary(self._league(scoring_settings={"rec": 1.0}))["te_premium"])
        no_bonus = self._league(scoring_settings={"rec": 1.0, "bonus_rec_te": 0})
        self.assertFalse(sc.league_format_summary(no_bonus)["te_premium"])

    def test_taxi_slots_and_teams_pass_through(self):
        fmt = sc.league_format_summary(self._league())
        self.assertEqual(fmt["taxi_slots"], 2)
        self.assertEqual(fmt["teams"], 12)


if __name__ == "__main__":
    unittest.main()
