"""MANDATE 2.4 / `#187`: a load that silently discards a FILE has not succeeded.

`load_all` wraps every file in `except Exception: continue` and kept no record. Five files in, two
loaded, three skipped, `is_loaded` True, nothing anywhere saying the pool got smaller. The skipping
is CORRECT — one bad upload must not take the app down — and the silence is the defect.

Mitigated for a user upload, which the person just chose and can see is missing. NOT mitigated for a
committed baseline file that stops parsing after a library upgrade, where nobody changed anything and
every league's pool quietly shrinks. That is the case this exists for, which is why the record carries
WHICH DIRECTORY the file was in: `load_all` cannot know, and `DataMerger._load` is the only place all
three are named.

The module already had the argument written down, about a different quantity: `reconciliation_conflicts`
exists because "a merge that silently discards a value has not succeeded", and 1,084 of those were
being resolved per load with no record of any. Same argument, one level up, so the same out-parameter
shape rather than a second mechanism.

AND THE SLEEPER CLIENT HALF. `get_players` accepted any truthy 200 body and cached it for 24 hours, so
an error-shaped JSON poisoned the daily cache and every later page load read it back and raised with
no in-app refetch. A 200 with a non-JSON body escaped as `JSONDecodeError`, walking past every caller
that catches `SleeperAPIError` — so the methods documented to fail soft did not.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import data_merger as dm
import sleeper_client as sc
import ui_source


class LoadAllRecordsWhatItSkipped(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def _dir_with(self, *, good: int = 1, broken: int = 0) -> Path:
        directory = self.tmp / "rankings"
        directory.mkdir(parents=True, exist_ok=True)
        for source in sorted(Path("data/baseline/rankings").glob("*.csv"))[:good]:
            shutil.copy(source, directory / source.name)
        for i in range(broken):
            # NO NAME-LIKE COLUMN, which is what `load_projection_file` refuses on. My first
            # fixture header was "no,name,column" -- which contains a column literally called
            # `name`, so it parsed cleanly and four tests failed against working code. The fixture
            # has to actually break, or the test measures nothing.
            (directory / f"broken_{i}.csv").write_text("alpha,beta,gamma\n1,2,3\n")
        return directory

    def test_a_clean_directory_records_nothing(self):
        skipped = []
        dm.load_all(self._dir_with(good=1), skipped=skipped)
        self.assertEqual(skipped, [])

    def test_an_unparsable_file_is_recorded_with_its_name_and_error_TYPE(self):
        """The type as well as the message: "this CSV has a bad header row" and "pandas raised on a
        dtype it used to accept" are different problems with different fixes."""
        skipped = []
        dm.load_all(self._dir_with(good=1, broken=1), skipped=skipped)
        self.assertEqual(len(skipped), 1, skipped)
        self.assertEqual(skipped[0]["file"], "broken_0.csv")
        self.assertTrue(skipped[0]["error"])
        self.assertTrue(skipped[0]["detail"])

    def test_the_good_files_still_load(self):
        """The skip must stay a skip. A repair that turned one bad file into a failed load would be
        worse than the silence it replaced."""
        rankings, _, _ = dm.load_all(self._dir_with(good=1, broken=2))
        self.assertFalse(rankings.empty)

    def test_a_caller_that_passes_nothing_is_unchanged(self):
        """Optional out-parameter: the old behaviour, exactly, for every existing caller."""
        rankings, _, _ = dm.load_all(self._dir_with(good=1, broken=1))
        self.assertFalse(rankings.empty)

    def test_every_skip_is_recorded_not_just_the_first(self):
        skipped = []
        dm.load_all(self._dir_with(good=1, broken=3), skipped=skipped)
        self.assertEqual(len(skipped), 3)


class TheMergerSaysWHICHSourceLostAFile(unittest.TestCase):
    """A baseline failure and an upload failure are different events. `load_all` cannot tell them
    apart; the caller that chose the directory can."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        (self.tmp / "rankings").mkdir(parents=True)
        (self.tmp / "trade_value").mkdir(parents=True)
        for source in sorted(Path("data/baseline/rankings").glob("*.csv"))[:1]:
            shutil.copy(source, self.tmp / "rankings" / source.name)

    def test_a_real_baseline_load_records_nothing_today(self):
        """Non-vacuity in the honest direction: the committed baseline parses, so an empty list here
        is a measurement rather than a broken check. The test below proves the check can fire."""
        merger = dm.DataMerger()
        self.assertEqual(merger.unparsable_files, [])

    def test_a_broken_baseline_file_is_attributed_to_the_BASELINE(self):
        (self.tmp / "rankings" / "broken.csv").write_text("alpha,beta,gamma\n1,2,3\n")
        merger = dm.DataMerger(baseline_dir=self.tmp)
        names = [entry["file"] for entry in merger.unparsable_files]
        self.assertIn("broken.csv", names)
        entry = next(e for e in merger.unparsable_files if e["file"] == "broken.csv")
        self.assertEqual(entry["provenance"], dm.PROVENANCE_BASELINE)
        self.assertEqual(entry["provenance_label"], dm.PROVENANCE_LABELS[dm.PROVENANCE_BASELINE])

    def test_the_label_is_words_and_not_the_ordering_number(self):
        """`PROVENANCE_BASELINE` is literally 0. "provenance: 0" told a person nothing, so the tiers
        have reader-facing names in one place."""
        for tier, label in dm.PROVENANCE_LABELS.items():
            self.assertIsInstance(label, str)
            self.assertTrue(label.strip())
            self.assertNotEqual(label, str(tier))
        self.assertEqual(len(dm.PROVENANCE_LABELS), 3)

    def test_is_loaded_is_still_TRUE_which_is_exactly_why_the_record_is_needed(self):
        """The defect stated as a test. A partial load is still a load — the pool works, it is just
        smaller than the files on disk — so no boolean was ever going to carry this."""
        (self.tmp / "rankings" / "broken.csv").write_text("alpha,beta,gamma\n1,2,3\n")
        merger = dm.DataMerger(baseline_dir=self.tmp)
        self.assertTrue(merger.is_loaded)
        self.assertTrue(merger.unparsable_files)


class TheImportAuditShowsIt(unittest.TestCase):
    """Recorded and rendered nowhere is the same defect one layer along -- which is what happened to
    `reconciliation_conflicts`, read today by tests and by no surface."""

    def test_the_audit_view_reads_the_merger_s_record(self):
        self.assertIn("unparsable_files", ui_source.text())

    def test_it_says_the_pool_is_smaller_than_the_files_suggest(self):
        self.assertIn("smaller than the files on disk", ui_source.text())

    def test_it_names_the_source_rather_than_the_tier_number(self):
        self.assertIn("provenance_label", ui_source.text())


class ThePlayerCacheRefusesABodyItCannotBe(unittest.TestCase):
    def test_a_real_player_map_is_accepted(self):
        self.assertTrue(sc._looks_like_a_player_map({"4034": {"full_name": "A Player"}}))

    def test_an_error_shaped_object_is_refused(self):
        self.assertFalse(sc._looks_like_a_player_map({"error": "Not Found"}))

    def test_a_list_a_string_and_an_empty_dict_are_refused(self):
        for body in ([], [{"full_name": "x"}], "oops", {}, None, 0):
            with self.subTest(body=body):
                self.assertFalse(sc._looks_like_a_player_map(body))

    def test_it_samples_rather_than_walking_ten_megabytes(self):
        """A predicate that scanned all ~11,000 entries on every fetch would cost more than the
        defect. Proven by a body whose FIRST entries are valid and whose later ones are not: the
        sample accepts it, which is the documented trade rather than an oversight."""
        body = {str(i): {"full_name": f"P{i}"} for i in range(30)}
        body["late"] = "not a record"
        self.assertTrue(sc._looks_like_a_player_map(body))

    def test_a_poisoned_body_is_never_written_to_the_cache(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        client = sc.SleeperClient(cache_dir=tmp)
        with mock.patch.object(client, "_get", return_value={"error": "rate limited"}):
            try:
                client.get_players()
            except Exception:
                pass
        cache = tmp / sc.PLAYERS_CACHE_FILENAME
        if cache.exists():
            self.assertNotIn("rate limited", cache.read_text(),
                             "an error-shaped body was cached for 24 hours")

    def test_a_good_body_IS_written(self):
        """Non-vacuity: the refusal must not be a blanket stop on caching."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        client = sc.SleeperClient(cache_dir=tmp)
        with mock.patch.object(client, "_get", return_value={"1": {"full_name": "A Player"}}):
            client.get_players()
        cached = json.loads((tmp / sc.PLAYERS_CACHE_FILENAME).read_text())
        self.assertEqual(cached, {"1": {"full_name": "A Player"}})


class ANonJSONBodyFailsSOFT(unittest.TestCase):
    """Every method here is documented to fail soft and callers catch `SleeperAPIError`. A decode
    failure walked past all of them."""

    class _Resp:
        status_code = 200
        ok = True
        text = "<!DOCTYPE html><html>gateway error</html>"

        def json(self):
            raise json.JSONDecodeError("Expecting value", self.text, 0)

    def test_it_raises_SleeperAPIError_and_not_a_decode_error(self):
        client = sc.SleeperClient()
        with mock.patch.object(client.session, "get", return_value=self._Resp()):
            with self.assertRaises(sc.SleeperAPIError):
                client._get("/players/nfl")

    def test_the_message_carries_the_start_of_the_body(self):
        """"invalid JSON" and "invalid JSON that begins <!DOCTYPE html>" point at different causes --
        a bug in the response versus a captive portal or gateway in the way."""
        client = sc.SleeperClient()
        with mock.patch.object(client.session, "get", return_value=self._Resp()):
            try:
                client._get("/players/nfl")
                self.fail("no error raised")
            except sc.SleeperAPIError as exc:
                self.assertIn("DOCTYPE", str(exc))
                self.assertIn("not JSON", str(exc))

    def test_a_soft_failing_caller_now_actually_degrades(self):
        """End to end: `get_players` catches SleeperAPIError, so with the right type it falls through
        to the cache instead of crashing the page."""
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / sc.PLAYERS_CACHE_FILENAME).write_text(json.dumps({"9": {"full_name": "Cached"}}))
        client = sc.SleeperClient(cache_dir=tmp)
        with mock.patch.object(client.session, "get", return_value=self._Resp()):
            players = client.get_players(force_refresh=True)
        self.assertEqual(players, {"9": {"full_name": "Cached"}})


if __name__ == "__main__":
    unittest.main()
