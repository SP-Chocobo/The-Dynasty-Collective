"""#143 / #52 / #88: fetching what actually happened, and refusing to pretend when it didn't.

The realized half of the forward test. Everything here is covered against MOCKED responses
because api.sleeper.app is unreachable from the container this was written in (HTTP 000) --
so these tests establish that the parsing and the record contract are right, and establish
nothing whatsoever about whether the URL is. That distinction is the point of the last class.

The two properties that matter most are refusals:
  - an EMPTY week is refused, because "nothing downloaded" and "nobody scored" are the same
    bytes and only one of them should ever reach a scorer;
  - a stat CORRECTION is allowed but leaves a trail, because an outcome legitimately changes
    where a prediction never may.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import outcome_record as orec
import sleeper_client as sc

_HERE = Path(__file__).parent

WEEK_STATS = {
    "4034": {"rush_yd": 88.0, "rush_td": 1.0, "rec": 3.0, "rec_yd": 24.0, "pts_ppr": 21.2},
    "6794": {"rec": 9.0, "rec_yd": 141.0, "rec_td": 1.0, "pts_ppr": 29.1},
}


class FetchParsingTests(unittest.TestCase):
    """Sleeper returns either a {player_id: entry} map or a list of entries, depending on the
    endpoint and the week. Both shapes appear in the projections sibling, so both are handled
    here rather than assuming today's shape is permanent."""

    def _client_returning(self, payload):
        client = sc.SleeperClient(cache_dir=tempfile.mkdtemp())
        client._get = mock.Mock(return_value=payload)
        return client

    def test_a_dict_payload_is_parsed(self):
        client = self._client_returning({pid: {"stats": s} for pid, s in WEEK_STATS.items()})
        self.assertEqual(client.get_weekly_stats("2026", 1), WEEK_STATS)

    def test_a_bare_dict_without_a_stats_key_is_still_parsed(self):
        client = self._client_returning(dict(WEEK_STATS))
        self.assertEqual(client.get_weekly_stats("2026", 1), WEEK_STATS)

    def test_a_list_payload_is_parsed(self):
        client = self._client_returning(
            [{"player_id": pid, "stats": s} for pid, s in WEEK_STATS.items()])
        self.assertEqual(client.get_weekly_stats("2026", 1), WEEK_STATS)

    def test_an_empty_payload_is_an_empty_dict_not_a_crash(self):
        self.assertEqual(self._client_returning(None).get_weekly_stats("2026", 1), {})

    def test_season_type_goes_in_the_PATH_here(self):
        """The opposite of get_weekly_projections, which puts it in the query string. That
        module's own comment records the asymmetry as a real bug it already paid for, so this
        pins the shape rather than leaving it to be re-guessed."""
        client = self._client_returning({})
        client.get_weekly_stats("2026", 3, season_type="regular")
        path = client._get.call_args[0][0]
        self.assertIn("/stats/nfl/regular/2026/3", path)
        self.assertNotIn("?season_type", path)

    def test_it_RAISES_rather_than_returning_empty_when_the_api_is_unreachable(self):
        """Its projections sibling fails soft, correctly -- a missing projection degrades a
        board gracefully. A missing OUTCOME does not: an empty result is indistinguishable
        from 'nobody scored'."""
        client = sc.SleeperClient(cache_dir=tempfile.mkdtemp())
        client._get = mock.Mock(side_effect=sc.SleeperAPIError("no route to host"))
        with self.assertRaises(sc.SleeperAPIError):
            client.get_weekly_stats("2026", 1)


class RefusingAnEmptyWeekTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_an_empty_capture_is_refused(self):
        with self.assertRaises(ValueError) as caught:
            orec.capture({}, "2026", 1, root=self.root)
        self.assertIn("never downloaded", str(caught.exception))

    def test_and_nothing_is_written(self):
        """Non-vacuity: the refusal must happen BEFORE the write, not after."""
        with self.assertRaises(ValueError):
            orec.capture({}, "2026", 1, root=self.root)
        self.assertFalse(orec.record_path("2026", 1, self.root).exists())


class CorrectionsAreVisibleTests(unittest.TestCase):
    """An outcome legitimately changes -- the NFL issues stat corrections days later. So unlike
    a prediction, re-capture is allowed. The guarantee is that it is not SILENT."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.first = orec.capture(WEEK_STATS, "2026", 1, root=self.root)

    def test_a_first_capture_has_no_revisions(self):
        self.assertEqual(self.first["revisions"], [])

    def test_recapturing_IDENTICAL_stats_adds_no_revision(self):
        """A re-run that changes nothing is not a correction, and logging one would make the
        trail meaningless by filling it with noise."""
        again = orec.capture(WEEK_STATS, "2026", 1, root=self.root)
        self.assertEqual(again["revisions"], [])
        self.assertEqual(again["fingerprint"], self.first["fingerprint"])

    def test_a_real_correction_is_recorded(self):
        corrected = {**WEEK_STATS, "4034": {**WEEK_STATS["4034"], "rush_yd": 91.0}}
        after = orec.capture(corrected, "2026", 1, root=self.root)
        self.assertEqual(len(after["revisions"]), 1)
        self.assertEqual(after["revisions"][0]["fingerprint"], self.first["fingerprint"])
        self.assertNotEqual(after["fingerprint"], self.first["fingerprint"])

    def test_successive_corrections_accumulate_rather_than_replace(self):
        orec.capture({**WEEK_STATS, "4034": {"rush_yd": 91.0}}, "2026", 1, root=self.root)
        third = orec.capture({**WEEK_STATS, "4034": {"rush_yd": 95.0}}, "2026", 1, root=self.root)
        self.assertEqual(len(third["revisions"]), 2)


class StatsNotPointsTests(unittest.TestCase):
    """The record stores stats so one fetch serves every scoring format. Storing points would
    bake in one league's rules -- and this owner plays several."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        orec.capture(WEEK_STATS, "2026", 1, root=self.root)

    def test_the_record_holds_raw_stats(self):
        record = orec.load("2026", 1, self.root)
        self.assertIn("rush_yd", record["stats"]["4034"])

    def test_two_scoring_formats_give_two_different_answers_from_ONE_capture(self):
        ppr = orec.points_for("2026", 1, {"rec": 1.0, "rec_yd": 0.1}, root=self.root)
        half = orec.points_for("2026", 1, {"rec": 0.5, "rec_yd": 0.1}, root=self.root)
        self.assertGreater(ppr["6794"], half["6794"],
                           "full PPR must score a 9-reception game above half PPR")

    def test_a_missing_week_yields_no_points_rather_than_zeros(self):
        self.assertEqual(orec.points_for("2026", 17, {"rec": 1.0}, root=self.root), {})


class TheLivePathIsUnverifiedTests(unittest.TestCase):
    """Everything above runs against mocks. None of it establishes that the URL is right, and
    the module must keep saying so until someone runs it against the real API."""

    def test_the_module_states_that_the_request_path_has_never_executed(self):
        source = (_HERE / "outcome_record.py").read_text()
        self.assertIn("never executed", source)

    def test_the_cli_tells_the_first_runner_to_check_against_a_box_score(self):
        """The instruction has to live in the tool's own output, not in a conversation nobody
        will find six months from now."""
        source = (_HERE / "outcome_record.py").read_text()
        self.assertIn("box score", source)

    def test_no_outcome_has_been_captured_yet(self):
        """A characterization, not a requirement. When the first real week lands this fails,
        and that failure is the prompt to verify it by eye and then delete this test."""
        self.assertEqual(orec.weeks(), [],
                         "an outcome record now exists -- check it against a real box score, "
                         "then remove this test")


if __name__ == "__main__":
    unittest.main()
