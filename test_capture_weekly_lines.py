"""#18: capturing a season to a file so the measurement can be re-run without a network.

The instrument under repair needs many passes over the same data, and the data lives behind a
host the audit sandbox denies. These cover the two properties that make a capture trustworthy:
it REFUSES to write an empty season, and what it writes round-trips to the same stat lines it
was handed. Everything runs against a mocked client -- nothing here establishes that the URL is
right, which is the lesson #18 already paid for.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import capture_weekly_lines as cwl
import player_universe as pu
import sleeper_client as sc

#: EXACTLY the shape SleeperClient._weekly_stat_lines returns: player_id -> bare stat dict. The
#: `player` blob and the `stats` wrapper are both gone by the time a caller sees it, and a fixture
#: that kept them is what let a position field that could never be populated pass its own test.
LINES = {
    "4034": {"rush_yd": 88.0, "rush_td": 1.0},
    "6794": {"rec": 9.0, "rec_yd": 141.0},
}


def _client(**kwargs):
    client = sc.SleeperClient(cache_dir=tempfile.mkdtemp())
    for name, value in kwargs.items():
        setattr(client, name, value)
    return client


class ThinningKeepsWhatIsMeasuredTests(unittest.TestCase):
    """The shapes `thin` must survive are the ones the CLIENT emits, not the ones the raw API
    does. An earlier draft stored a position read off Sleeper's embedded `player` blob; the client
    strips that blob, so the field would have been None for every player in every week while every
    test here passed. These feed client-shaped input for that reason."""

    def test_the_stat_line_survives_intact(self):
        self.assertEqual(cwl.thin(LINES)["4034"], {"rush_yd": 88.0, "rush_td": 1.0})

    def test_a_line_that_still_carries_a_stats_key_is_unwrapped(self):
        """The ad-hoc 2024 capture in this repo is raw payload, one nesting level deeper than the
        client's output. One reader has to serve both."""
        self.assertEqual(cwl.thin({"7": {"stats": {"rec": 3.0}}})["7"], {"rec": 3.0})

    def test_nothing_but_the_stat_line_is_stored(self):
        """Position is deliberately absent -- it lives in players_db, and a capture-day copy would
        be a second source of truth that goes stale (#126, #26)."""
        raw = {"4034": {"stats": {"rush_yd": 88.0}, "player": {"position": "RB"}}}
        self.assertEqual(cwl.thin(raw)["4034"], {"rush_yd": 88.0})

    def test_every_stat_key_is_kept_rather_than_filtered_to_a_scoring_vocabulary(self):
        """score_projection sums over whatever keys a LEAGUE's settings name, so a key this
        capture judged useless is a key some other league scores. Filtering here would make the
        file silently wrong for a format it has never seen."""
        odd = {"9": {"idp_sack": 2.0, "bonus_rec_te": 1.0, "gp": 1.0}}
        self.assertEqual(set(cwl.thin(odd)["9"]), {"idp_sack", "bonus_rec_te", "gp"})


class RefusingAnEmptySeasonTests(unittest.TestCase):
    """outcome_record's refusal, generalised. An empty file measures as a season in which nobody
    scored, and that verdict is about the engine."""

    def test_a_season_that_returned_nothing_is_refused(self):
        client = _client(get_weekly_projections=mock.Mock(return_value={}))
        with self.assertRaises(ValueError) as caught:
            cwl.capture_season(client, "2024", "projections", log=lambda *a: None, spacing=0.0)
        self.assertIn("Nothing downloaded", str(caught.exception))

    def test_a_single_missing_week_is_skipped_not_refused(self):
        """A season that ran short is a real thing. Absence of one week is not absence of the
        season, and the skipped week is left OUT rather than stored as zeros (#187)."""
        answers = {3: dict(LINES)}
        client = _client(get_weekly_projections=mock.Mock(
            side_effect=lambda season, week: answers.get(week, {})))
        record = cwl.capture_season(client, "2024", "projections", log=lambda *a: None, spacing=0.0)
        self.assertEqual(list(record["weeks"]), ["3"])
        self.assertEqual(record["n_weeks"], 1)


class RoundTripTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        client = _client(get_weekly_stats=mock.Mock(return_value=dict(LINES)))
        self.record = cwl.capture_season(client, "2024", "stats", log=lambda *a: None, spacing=0.0)
        self.path = cwl.write(self.record, cwl.capture_path("2024", "stats", self.root))

    def test_what_comes_back_is_what_went_in(self):
        self.assertEqual(cwl.read(self.path)["weeks"]["1"], self.record["weeks"]["1"])

    def test_it_is_gzipped_rather_than_plain_json(self):
        """Ten megabytes a season a kind, four of them, is worth a compressor."""
        self.assertEqual(self.path.read_bytes()[:2], b"\x1f\x8b")

    def test_a_plain_json_capture_is_readable_too(self):
        """The ad-hoc 2024 actuals in this repo are uncompressed. One reader has to serve both,
        or the measurement grows a second code path for the file it already has."""
        plain = self.root / "weekly_stats_2024.json"
        plain.write_text('{"weeks": {"1": {}}}')
        self.assertEqual(cwl.read(plain), {"weeks": {"1": {}}})

    def test_the_captured_lines_still_score(self):
        """Non-vacuity, and it goes through capture_season rather than thin() directly -- the whole
        real path, from a client-shaped response to a scored number off the file."""
        week = cwl.read(self.path)["weeks"]["1"]
        self.assertGreater(pu.score_projection(week["6794"], {"rec": 1.0}), 0.0)

    def test_the_captured_ids_are_joinable_against_players_db(self):
        """Position is not in the file, so the ids are the only join key to it. A capture whose
        keys were not Sleeper player ids would be unbucketable and would look fine."""
        week = cwl.read(self.path)["weeks"]["1"]
        self.assertEqual(sorted(week), ["4034", "6794"])


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        client = _client(get_weekly_projections=mock.Mock(return_value=dict(LINES)))
        self.record = cwl.capture_season(client, "2023", "projections", log=lambda *a: None, spacing=0.0)

    def test_the_record_says_which_endpoint_and_season_type_it_read(self):
        """The ad-hoc capture this replaces recorded none of it, which is why nobody could tell
        whether it predated the URL fix."""
        self.assertIn("season_type=regular", self.record["source"])
        self.assertIn("projections", self.record["source"])

    def test_the_record_says_when(self):
        self.assertTrue(self.record["captured_at"].endswith("+00:00"))

    def test_the_record_says_it_holds_stats_not_points(self):
        self.assertIn("not points", self.record["_comment"])


if __name__ == "__main__":
    unittest.main()


class OneReaderForEveryCaptureShapeTests(unittest.TestCase):
    """`load_season` is the single reader, and it exists because this repo holds TWO incompatible
    capture shapes: what this script writes, and the ad-hoc raw payload that predates it.

    The failure it prevents is silent. A raw record's stat line sits one level deeper
    (`{"stats": {...}, "player": {...}}`), so reading it as though it were already thinned hands
    `score_projection` a dict of metadata keys -- `player`, `week`, `game_id` -- none of which
    appear in any scoring settings, so every player sums to exactly 0.0. A whole season of zeros
    and no error anywhere.
    """

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())

    def test_a_written_capture_is_found(self):
        client = _client(get_weekly_stats=mock.Mock(return_value=dict(LINES)))
        record = cwl.capture_season(client, "2024", "stats", log=lambda *a: None, spacing=0.0)
        cwl.write(record, cwl.capture_path("2024", "stats", self.root))
        self.assertEqual(cwl.load_season("2024", "stats", self.root)["1"], LINES)

    def test_an_absent_capture_is_empty_rather_than_an_error(self):
        """Absence is a fact the caller has to be able to act on -- measure_projection_accuracy
        skips a season it has no capture for rather than reporting it as a season of zeros."""
        self.assertEqual(cwl.load_season("1999", "projections", self.root), {})

    def test_the_legacy_raw_payload_is_unwrapped_to_the_same_shape(self):
        """The ad-hoc 2024 actuals. `{week: [record, ...]}` with the stat line nested, which has
        to come back looking exactly like a thinned capture or every consumer needs two paths."""
        legacy = self.root / "sleeper_weekly_2031.json"
        legacy.write_text(json.dumps({"1": [
            {"player_id": "4034", "stats": {"rush_yd": 88.0}, "player": {"position": "RB"}}]}))
        with mock.patch.object(cwl, "LEGACY_ACTUALS", str(legacy)):
            weeks = cwl.load_season("2031", "stats", self.root)
        self.assertEqual(weeks, {"1": {"4034": {"rush_yd": 88.0}}})

    def test_the_legacy_payload_is_only_consulted_for_stats(self):
        """It is an ACTUALS capture. Serving it as projections would compare a season against
        itself and report every projection perfect."""
        legacy = self.root / "sleeper_weekly_2031.json"
        legacy.write_text(json.dumps({"1": [{"player_id": "4034", "stats": {"rush_yd": 88.0}}]}))
        with mock.patch.object(cwl, "LEGACY_ACTUALS", str(legacy)):
            self.assertEqual(cwl.load_season("2031", "projections", self.root), {})

    def test_a_written_capture_wins_over_the_legacy_file(self):
        """Non-vacuity on the precedence: once a season is captured properly, the ad-hoc file must
        stop being read, or a re-capture would have no effect."""
        client = _client(get_weekly_stats=mock.Mock(
            side_effect=lambda season, week: {"9": {"rec": 1.0}} if week == 1 else {}))
        record = cwl.capture_season(client, "2031", "stats", log=lambda *a: None, spacing=0.0)
        cwl.write(record, cwl.capture_path("2031", "stats", self.root))
        legacy = self.root / "sleeper_weekly_2031.json"
        legacy.write_text(json.dumps({"1": [{"player_id": "4034", "stats": {"rush_yd": 88.0}}]}))
        with mock.patch.object(cwl, "LEGACY_ACTUALS", str(legacy)):
            self.assertEqual(cwl.load_season("2031", "stats", self.root), {"1": {"9": {"rec": 1.0}}})
