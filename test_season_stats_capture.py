"""#282 -- `get_season_stats`, the realized counterpart to `get_season_projections`.

Guards the four properties that make a prior season safe to carry beside a projection: it asks
the YEAR IT WAS GIVEN (#79), an absent player has NO KEY rather than zeros (#174, #187), a
failed week is recorded instead of summed as nothing, and both season builders run the SAME
summing construction (#126).
"""
from unittest import mock
import json
import tempfile
import unittest
from pathlib import Path

import sleeper_client as sc
import sleeper_import_report as sir


def _client():
    return sc.SleeperClient()


class SeasonStatsAsksTheYearItIsGiven(unittest.TestCase):
    def test_the_requested_season_reaches_the_url_and_the_coverage_record(self):
        client = _client()
        client.get_weekly_stats = mock.Mock(return_value={"p1": {"rush_yd": 10}})
        totals, coverage = client.get_season_stats("2025", weeks=3)
        self.assertEqual(coverage["season"], "2025")
        for call in client.get_weekly_stats.call_args_list:
            self.assertEqual(call[0][0], "2025")
        self.assertEqual(totals["p1"]["rush_yd"], 30)

    def test_a_prior_season_and_a_projection_season_stay_distinguishable(self):
        """#79: a record that does not carry its own season cannot be told from another's."""
        client = _client()
        client.get_weekly_stats = mock.Mock(return_value={"p1": {"rush_yd": 1}})
        client.get_weekly_projections = mock.Mock(return_value={"p1": {"rush_yd": 9}})
        _, realized = client.get_season_stats("2025", weeks=1)
        _, projected = client.get_season_projections("2026", weeks=1)
        self.assertNotEqual(realized["season"], projected["season"])


class AnAbsentPriorSeasonIsNotAZero(unittest.TestCase):
    def test_a_player_with_no_rows_gets_no_key_at_all(self):
        """Every ROOKIE lands here. A key with zeros would make each one the worst player at
        his position instantly -- the defect class #174 and #187 were opened for."""
        client = _client()
        client.get_weekly_stats = mock.Mock(return_value={"veteran": {"rush_yd": 5}})
        totals, _ = client.get_season_stats("2025", weeks=2)
        self.assertIn("veteran", totals)
        self.assertNotIn("rookie", totals)
        self.assertIsNone(totals.get("rookie"))

    def test_a_non_numeric_category_is_skipped_never_coerced_to_zero(self):
        client = _client()
        client.get_weekly_stats = mock.Mock(
            return_value={"p1": {"rush_yd": 4, "team": "BUF"}})
        totals, _ = client.get_season_stats("2025", weeks=1)
        self.assertEqual(totals["p1"], {"rush_yd": 4.0})


class AFailedWeekIsRecordedNotSummedAsZeros(unittest.TestCase):
    def test_an_empty_week_lands_in_weeks_failed_and_costs_nothing(self):
        client = _client()
        client.get_weekly_stats = mock.Mock(
            side_effect=[{"p1": {"rush_yd": 10}}, {}, {"p1": {"rush_yd": 10}}])
        totals, coverage = client.get_season_stats("2025", weeks=3)
        self.assertEqual(coverage["weeks_answered"], [1, 3])
        self.assertEqual(coverage["weeks_failed"], [2])
        self.assertEqual(totals["p1"]["rush_yd"], 20)
        self.assertEqual(coverage["weeks_present_by_player"]["p1"], 2)


class BothSeasonBuildersShareOneConstruction(unittest.TestCase):
    def test_they_run_the_same_summing_code_against_different_endpoints(self):
        """#126: one home for the construction. If these diverge, every property above has to
        be re-proved on the copy -- which is exactly how one of them ends up wrong."""
        client = _client()
        client.get_weekly_stats = mock.Mock(return_value={"p": {"x": 2}})
        client.get_weekly_projections = mock.Mock(return_value={"p": {"x": 2}})
        with mock.patch.object(sc.SleeperClient, "_sum_weeks",
                               wraps=client._sum_weeks) as shared:
            client.get_season_stats("2025", weeks=1)
            client.get_season_projections("2026", weeks=1)
        self.assertEqual(shared.call_count, 2)
        self.assertIs(shared.call_args_list[0][0][0], client.get_weekly_stats)
        self.assertIs(shared.call_args_list[1][0][0], client.get_weekly_projections)


class FakeClient:
    """Enough of a client to exercise write_fixture without touching the network."""

    def __init__(self, stats=None, raises=False):
        self._stats = stats if stats is not None else {"vet": {"rush_yd": 100}}
        self._raises = raises
        self.asked = []

    def get_nfl_state(self):
        return {"season": "2026"}

    def get_players(self):
        return {"vet": {"position": "RB", "full_name": "A Vet"},
                "rook": {"position": "RB", "full_name": "A Rookie"}}

    def get_season_projections(self, season, *a, **k):
        return ({"vet": {"rush_yd": 90}, "rook": {"rush_yd": 40}},
                {"weeks_requested": 18, "weeks_answered": list(range(1, 19)), "weeks_failed": []})

    def get_season_stats(self, season, *a, **k):
        self.asked.append(season)
        if self._raises:
            raise sc.SleeperAPIError("no route to host")
        return (self._stats,
                {"weeks_requested": 18, "weeks_answered": list(range(1, 19)), "weeks_failed": []})

    def get_league(self, league_id):
        return {}


def _write(client, prior_season=None):
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "cap.json")
        summary = sir.write_fixture(client, None, path, prior_season=prior_season)
        return json.loads(Path(path).read_text()), summary


class TheFixtureCarriesThePriorSeasonUnderItsOwnYear(unittest.TestCase):
    def test_it_defaults_to_the_year_before_the_projection_season(self):
        fx, summary = _write(FakeClient())
        self.assertEqual(fx["season"], "2026")
        self.assertEqual(fx["prior_season_production"]["season"], "2025")
        self.assertEqual(summary["prior_season"], "2025")

    def test_an_explicit_year_overrides_the_default(self):
        client = FakeClient()
        fx, _ = _write(client, prior_season="2023")
        self.assertEqual(fx["prior_season_production"]["season"], "2023")
        self.assertEqual(client.asked, ["2023"])

    def test_production_is_stored_beside_the_projections_not_mixed_into_them(self):
        fx, _ = _write(FakeClient())
        self.assertEqual(fx["season_projections"]["vet"], {"rush_yd": 90})
        self.assertEqual(fx["prior_season_production"]["totals"]["vet"], {"rush_yd": 100})


class ARookieHasNoPriorSeasonAndThatIsNotZero(unittest.TestCase):
    def test_a_player_absent_from_the_prior_year_gets_no_entry(self):
        fx, _ = _write(FakeClient())
        prod = fx["prior_season_production"]["totals"]
        self.assertIn("vet", prod)
        self.assertNotIn("rook", prod)          # never {"rush_yd": 0}
        self.assertIn("rook", fx["season_projections"])   # still projected, just no history


class AFailedStatsFetchDoesNotCostTheCapture(unittest.TestCase):
    def test_the_projections_still_write_and_the_failure_is_recorded(self):
        fx, summary = _write(FakeClient(raises=True))
        self.assertTrue(fx["season_projections"])            # DEGRADE, NEVER ABORT
        self.assertEqual(fx["prior_season_production"]["totals"], {})
        self.assertIn("SleeperAPIError", fx["prior_season_production"]["error"])
        self.assertIsNotNone(summary["prior_season_error"])

    def test_a_successful_fetch_records_no_error(self):
        fx, _ = _write(FakeClient())
        self.assertIsNone(fx["prior_season_production"]["error"])


if __name__ == "__main__":
    unittest.main()
