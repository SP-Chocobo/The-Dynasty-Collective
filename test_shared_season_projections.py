"""One season fetch answers for every league (`#337`).

THE DEFECT. `sync_league` called `get_season_projections`, which sums EIGHTEEN weekly fetches,
once per league -- for a quantity that does not vary by league. Sleeper publishes projections per
player per week; this league's scoring is applied downstream, not baked in here. So a manager in
nine leagues paid 9 x 18 = 162 requests for one answer, and a manager in twenty paid 360. The
duplicated bytes were trivial; the duplicated WORK was not, and twenty copies of one quantity is
the same shape as one quantity with two homes.

WHAT IS SHARED IS THE FETCH, NOT THE TRUTH. The sums still land in every snapshot exactly as
before, so no consumer changed and `season_projection_freshness_entry` keeps reading the snapshot
it was written against.
"""
import json
import pathlib
import sys
import tempfile
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import sleeper_client as sc


# The week count the shared path keys on. Taken from the client rather than written as
# 18 here, so this file cannot disagree with the constant it is testing (`#126`).
WEEKS = sc.SleeperClient.REGULAR_SEASON_WEEKS


class _Counting(sc.SleeperClient):
    """A client that answers the eighteen-week sum without a network, and counts the asks."""

    def __init__(self, cache_dir, projections=None, error=None):
        self.cache_dir = pathlib.Path(cache_dir)
        self.calls = 0
        self._projections = {"p1": {"pts": 10.0}} if projections is None else projections
        self._error = error

    def get_season_projections(self, season, season_type="regular", weeks=None, weekly_out=None):
        self.calls += 1
        if weekly_out is not None:
            weekly_out["1"] = {"p1": {"pts": 1.0}}
        cov = {"weeks_answered": list(range(1, 19)), "weeks_failed": [], "error": self._error}
        return (self._projections if not self._error else {}), cov


class OneFetchAnswersForEveryLeagueTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_nine_leagues_cost_one_season_fetch_not_nine(self):
        """The whole point, in the units that hurt: eighteen weekly requests, not 162."""
        c = _Counting(self.dir)
        for _ in range(9):
            c.get_season_projections_shared("2026", "regular", weekly_out={})
        self.assertEqual(1, c.calls)

    def test_the_sums_are_identical_on_the_reused_path(self):
        """Sharing the FETCH must not change the ANSWER. A cache that returns something subtly
        different is worse than no cache -- it makes one league disagree with another."""
        c = _Counting(self.dir)
        first, _ = c.get_season_projections_shared("2026", "regular")
        second, _ = c.get_season_projections_shared("2026", "regular")
        self.assertEqual(first, second)

    def test_the_weekly_lines_survive_the_reused_path(self):
        """`weekly_out` is how `#30`'s per-week lines reach the board. A cache that dropped them
        would silently remove the streaming replacement level for K and DEF."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular", weekly_out={})
        again = {}
        c.get_season_projections_shared("2026", "regular", weekly_out=again)
        self.assertEqual({"1": {"p1": {"pts": 1.0}}}, again)

    def test_a_reader_can_tell_a_reused_file_from_a_fresh_fetch(self):
        """Provenance, not just speed. A snapshot whose sums came off disk six hours ago is a
        different claim from one fetched this minute, and the coverage record says which."""
        c = _Counting(self.dir)
        _, fresh = c.get_season_projections_shared("2026", "regular")
        _, reused = c.get_season_projections_shared("2026", "regular")
        self.assertFalse(fresh["reused_from_shared_cache"])
        self.assertTrue(reused["reused_from_shared_cache"])
        self.assertIsNotNone(reused["fetched_at"])


class TheCacheIsKeyedAndBoundedTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_two_seasons_do_not_answer_for_each_other(self):
        """Two figures with one home is the same defect as one figure with two, inverted."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        c.get_season_projections_shared("2025", "regular")
        self.assertEqual(2, c.calls)

    def test_two_season_types_do_not_answer_for_each_other(self):
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        c.get_season_projections_shared("2026", "post")
        self.assertEqual(2, c.calls)

    def test_a_file_past_the_window_is_refetched(self):
        """Six hours, so Tuesday's sums never answer for Thursday."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        stale = time.time() + sc.SEASON_PROJECTIONS_CACHE_MAX_AGE_SECONDS + 1
        c.get_season_projections_shared("2026", "regular", now=stale)
        self.assertEqual(2, c.calls)

    def test_age_is_None_when_nothing_was_ever_written(self):
        """`#187`. Absence is not a duration, and a never-written cache is not a fresh one."""
        self.assertIsNone(
            sc.season_projections_cache_age_seconds("2026", "regular", WEEKS, self.dir))


class AFailedFetchIsNeverSharedTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_an_errored_fetch_is_not_written_for_the_next_league_to_inherit(self):
        """Caching a failure hands the next eight leagues the outage instead of a retry."""
        c = _Counting(self.dir, error="HTTPError: 503")
        c.get_season_projections_shared("2026", "regular")
        c.get_season_projections_shared("2026", "regular")
        self.assertEqual(2, c.calls)
        self.assertIsNone(
            sc.season_projections_cache_age_seconds("2026", "regular", WEEKS, self.dir))

    def test_an_empty_result_is_not_written_either(self):
        c = _Counting(self.dir, projections={})
        c.get_season_projections_shared("2026", "regular")
        c.get_season_projections_shared("2026", "regular")
        self.assertEqual(2, c.calls)

    def test_a_torn_cache_file_falls_through_to_a_fetch_rather_than_serving_junk(self):
        """A hand-edited or half-written file must not become the answer nine leagues trust."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        sc.season_projections_cache_path(
            "2026", "regular", WEEKS, self.dir).write_text("{not json")
        proj, cov = c.get_season_projections_shared("2026", "regular")
        self.assertEqual(2, c.calls)
        self.assertEqual({"p1": {"pts": 10.0}}, proj)


class TheSyncPathUsesItTests(unittest.TestCase):
    def test_sync_league_calls_the_shared_path_not_the_per_league_one(self):
        """The wiring. Without it the module is correct and reaches nobody -- the state
        `front_claims` was in before `#333`."""
        src = (ROOT / "sleeper_client.py").read_text()
        body = src[src.index("def sync_league("):]
        self.assertIn("get_season_projections_shared(", body)
        self.assertNotIn("self.get_season_projections(", body)


class TheKeyCarriesTheWeekCountTests(unittest.TestCase):
    """An 11-week sum and an 18-week sum are different claims about the same player.

    `get_season_projections`' own docstring says a total summed from 11 of 18 weeks reads as a
    weak player. Nothing asks the shared path for a partial season today -- it takes no `weeks`
    -- so these tests guard the key rather than a live caller: the file must be UNFINDABLE by a
    caller wanting a different week count, not merely mislabelled for one. The payload's
    coverage record carries `weeks_requested`, but a cache HIT never reads it, which is why the
    week count has to be in the NAME. `#79` is the precedent: a canonical record that did not
    carry its own basis.
    """

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_two_week_counts_do_not_share_a_file(self):
        self.assertNotEqual(
            sc.season_projections_cache_path("2026", "regular", 11, self.dir),
            sc.season_projections_cache_path("2026", "regular", 18, self.dir))

    def test_the_shared_fetch_writes_where_the_clients_own_week_count_points(self):
        """The key and the quantity must agree, or the cache silently never hits."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        self.assertTrue(
            sc.season_projections_cache_path("2026", "regular", WEEKS, self.dir).exists())

    def test_a_cache_written_for_another_week_count_is_not_reused(self):
        """The property that matters, stated as behaviour rather than as a filename."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        self.assertEqual(1, c.calls)
        # Move the file to the key an 11-week sum would own. The 18-week caller must miss it.
        sc.season_projections_cache_path("2026", "regular", WEEKS, self.dir).rename(
            sc.season_projections_cache_path("2026", "regular", 11, self.dir))
        c.get_season_projections_shared("2026", "regular")
        self.assertEqual(2, c.calls)

    def test_the_written_payload_records_its_own_week_count(self):
        """`#79`. The body carries the basis too, so a reader holding the file alone can tell."""
        c = _Counting(self.dir)
        c.get_season_projections_shared("2026", "regular")
        held = json.loads(
            sc.season_projections_cache_path("2026", "regular", WEEKS, self.dir).read_text())
        self.assertEqual(WEEKS, held["weeks"])


if __name__ == "__main__":
    unittest.main()
