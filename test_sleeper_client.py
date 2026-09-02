import tempfile
import unittest
from unittest import mock

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


class GetMatchupsTests(unittest.TestCase):
    """Unlike the rest of this client's thin HTTP wrappers (none of which are unit-tested --
    see get_rosters/get_traded_picks/etc.), this one gets its own test: it's a brand new,
    previously-unused endpoint, and an off-by-one in the URL path would otherwise be a
    completely silent failure (fails soft to [], same as a genuinely empty week)."""

    def _client(self) -> sc.SleeperClient:
        return sc.SleeperClient(cache_dir=tempfile.mkdtemp())

    def test_calls_the_documented_matchups_path(self):
        client = self._client()
        with mock.patch.object(client, "_get", return_value=[{"roster_id": 1}]) as mock_get:
            result = client.get_matchups("123456", 4)
        mock_get.assert_called_once_with("/league/123456/matchups/4")
        self.assertEqual(result, [{"roster_id": 1}])

    def test_none_response_is_a_safe_empty_list(self):
        client = self._client()
        with mock.patch.object(client, "_get", return_value=None):
            self.assertEqual(client.get_matchups("123456", 4), [])


class FindOpponentRosterIdTests(unittest.TestCase):
    def test_finds_the_paired_roster_on_either_side(self):
        matchups = [
            {"roster_id": 1, "matchup_id": 5}, {"roster_id": 2, "matchup_id": 5},
            {"roster_id": 3, "matchup_id": 6}, {"roster_id": 4, "matchup_id": 6},
        ]
        self.assertEqual(sc.find_opponent_roster_id(matchups, 1), 2)
        self.assertEqual(sc.find_opponent_roster_id(matchups, 4), 3)

    def test_null_matchup_id_reads_as_no_opponent(self):
        # Sleeper's own representation of "no matchup yet" (a bye, or preseason).
        matchups = [{"roster_id": 1, "matchup_id": None}, {"roster_id": 2, "matchup_id": None}]
        self.assertIsNone(sc.find_opponent_roster_id(matchups, 1))

    def test_roster_not_present_reads_as_no_opponent(self):
        matchups = [{"roster_id": 2, "matchup_id": 5}]
        self.assertIsNone(sc.find_opponent_roster_id(matchups, 1))

    def test_empty_matchups_reads_as_no_opponent(self):
        self.assertIsNone(sc.find_opponent_roster_id([], 1))

    def test_more_than_one_other_roster_sharing_a_matchup_id_is_left_unresolved(self):
        # A malformed/unusual payload -- never guess which of several is "the" opponent.
        matchups = [
            {"roster_id": 1, "matchup_id": 5}, {"roster_id": 2, "matchup_id": 5},
            {"roster_id": 3, "matchup_id": 5},
        ]
        self.assertIsNone(sc.find_opponent_roster_id(matchups, 1))


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


class BaselineProjectionRowsTests(unittest.TestCase):
    """The refresh path that regenerates a committed baseline rankings CSV from a live sync."""

    # One real league's kicking settings, from its own Sleeper scoring_settings.
    # A real league's scoring_settings is one flat map covering every position at once,
    # so the offensive weights sit alongside the kicking ones here too.
    KICKING = {
        "xpm": 1, "xpmiss": -1, "fgmiss": -1,
        "fgm_0_19": 3, "fgm_20_29": 3, "fgm_30_39": 3, "fgm_40_49": 4, "fgm_50p": 5,
        "rec": 1,
    }
    PLAYERS = {
        "1": {"first_name": "Brandon", "last_name": "Aubrey", "team": "DAL", "position": "K"},
        "2": {"first_name": "Cam", "last_name": "Little", "team": "JAC", "position": "K"},
        "3": {"first_name": "Some", "last_name": "Receiver", "team": "SEA", "position": "WR"},
        "4": {"first_name": "Retired", "last_name": "Kicker", "team": "", "position": "K"},
    }
    PROJ = {
        "1": {"xpm": 2.5, "fgm_40_49": 0.6, "fgm_50p": 0.4},
        "2": {"xpm": 2.0, "fgm_30_39": 0.7},
        "3": {"rec": 6.0},
        "4": {"xpm": 0.0},
    }

    def _rows(self, **kwargs):
        return sc.build_baseline_projection_rows(
            self.PROJ, self.PLAYERS, self.KICKING, season_factor=17,
            source_date="2026-08-25", **kwargs)

    def test_points_are_league_scored_and_extrapolated_to_a_season(self):
        row = next(r for r in self._rows(positions=["K"]) if r["name"] == "B Aubrey")
        # 2.5*1 + 0.6*4 + 0.4*5 = 2.5 + 2.4 + 2.0 = 6.9/week -> 117.3 over 17 weeks
        self.assertAlmostEqual(row["projection"], 117.3, places=1)

    def test_position_filter_is_a_plain_filter_not_a_special_case(self):
        # Same call, different filter: nothing about K is privileged in the code path.
        self.assertEqual({r["position"] for r in self._rows(positions=["K"])}, {"K"})
        self.assertEqual({r["position"] for r in self._rows(positions=["WR"])}, {"WR"})
        self.assertEqual({r["position"] for r in self._rows()}, {"K", "WR"})

    def test_nonpositive_projections_are_dropped(self):
        # A 0-point kicker is "no projection at all", not "projected to be bad" -- keeping
        # him would drag the position's replacement rank onto an undraftable player.
        self.assertNotIn("R Kicker", [r["name"] for r in self._rows(positions=["K"])])

    def test_rank_is_dense_and_ordered_by_projection(self):
        rows = self._rows(positions=["K"])
        self.assertEqual([r["rank"] for r in rows], [float(i) for i in range(1, len(rows) + 1)])
        points = [r["projection"] for r in rows]
        self.assertEqual(points, sorted(points, reverse=True))

    def test_multi_year_columns_are_left_empty_not_faked(self):
        # Sleeper supplies no multi-year outlook, and an empty proj_3yr is genuinely
        # neutral downstream -- a stand-in value would manufacture a growth signal.
        for row in self._rows(positions=["K"]):
            self.assertEqual(row["proj_3yr"], "")
            self.assertEqual(row["trade_value"], "")

    def test_name_uses_the_committed_baseline_initial_surname_convention(self):
        self.assertIn("B Aubrey", [r["name"] for r in self._rows(positions=["K"])])

    def test_unknown_player_ids_are_skipped_rather_than_guessed(self):
        rows = sc.build_baseline_projection_rows(
            {"999": {"xpm": 3.0}}, self.PLAYERS, self.KICKING, season_factor=17)
        self.assertEqual(rows, [])

    def test_write_round_trips_into_the_baseline_csv_shape(self):
        import csv as _csv
        from pathlib import Path
        rows = self._rows(positions=["K"])
        with tempfile.TemporaryDirectory() as tmp:
            path = sc.write_baseline_projection_csv(rows, Path(tmp) / "sub" / "k.csv")
            with path.open() as handle:
                back = list(_csv.DictReader(handle))
        self.assertEqual(list(back[0].keys()), sc.BASELINE_RANKINGS_COLUMNS)
        self.assertEqual(back[0]["name"], "B Aubrey")

    def test_empty_rows_refuse_to_truncate_a_committed_baseline(self):
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "k.csv"
            target.write_text("name,team\nB Aubrey,DAL\n")
            with self.assertRaises(ValueError):
                sc.write_baseline_projection_csv([], target)
            # the existing pool survived an unreachable-API day
            self.assertIn("Aubrey", target.read_text())


if __name__ == "__main__":
    unittest.main()
