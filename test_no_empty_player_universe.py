"""#52 phase 7.5 / J-13, ruled: an absent player universe is refused, not returned as `{}`.

`get_players` had two problems that compound. It wrote the ~10 MB cache with `write_text` --
the exact pattern `store_io`'s own docstring measures at **91,956 empty reads of 98,405** under
one concurrent writer, because `write_text` truncates before it writes. And when the live fetch
failed AND the cache was unusable it returned `{}`: a player universe indistinguishable from a
league with no players, handed to callers that build boards and roster tables from it.

Together: a torn read forces a refetch, the refetch fails, and every downstream surface
computes against an empty universe and reports the result as an answer. `app.py` calls
`get_players()` at top level on every rerun, and Streamlit serves many tabs from one process,
so the concurrent reader is not hypothetical.

The write is now atomic and the absence is now refused. The cache deliberately does NOT get
`store_io.write`'s damaged-bytes protection -- see `replace_atomically`, and the test below that
pins the distinction.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import sleeper_client as sc


class _Client(sc.SleeperClient):
    """A client whose only network call is controllable."""

    def __init__(self, cache_dir, fetch):
        super().__init__(cache_dir=cache_dir)
        self._fetch = fetch

    def _get(self, path, base=sc.BASE_URL):
        return self._fetch(path)


class AnAbsentUniverseIsRefusedTests(unittest.TestCase):

    def setUp(self):
        self._dir = TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)
        self.cache = self.root / sc.PLAYERS_CACHE_FILENAME

    def _client(self, fetch):
        return _Client(str(self.root), fetch)

    def test_a_live_fetch_returns_the_players_and_caches_them(self):
        """Non-vacuity: the happy path has to work, or every refusal below is trivially true."""
        client = self._client(lambda p: {"1": {"position": "RB"}})
        self.assertEqual(client.get_players(), {"1": {"position": "RB"}})
        self.assertEqual(json.loads(self.cache.read_text()), {"1": {"position": "RB"}})

    def test_a_failed_fetch_falls_back_to_the_cache(self):
        """Also non-vacuity, and the behaviour that must SURVIVE the change: a usable cache is
        still an answer. Refusing here would turn every offline session into an error."""
        self.cache.write_text(json.dumps({"7": {"position": "WR"}}))
        def boom(path):
            raise sc.SleeperAPIError("down")
        self.assertEqual(self._client(boom).get_players(), {"7": {"position": "WR"}})

    def test_no_fetch_and_no_cache_raises_instead_of_returning_an_empty_universe(self):
        def boom(path):
            raise sc.SleeperAPIError("down")
        with self.assertRaises(sc.SleeperAPIError) as caught:
            self._client(boom).get_players()
        message = str(caught.exception)
        self.assertIn("no player universe", message)
        self.assertIn("refuses", message,
                      "the message has to say this is a refusal, not a transport failure -- "
                      "they call for different things from the person reading it")

    def test_no_fetch_and_a_DAMAGED_cache_raises_too(self):
        """The case that made `{}` dangerous rather than merely wrong: a torn read leaves bytes
        that do not parse, the client correctly treats that as a miss, and the refetch then
        fails. That is the exact sequence store_io measured 91,956 times."""
        self.cache.write_text("{not json")
        def boom(path):
            raise sc.SleeperAPIError("down")
        with self.assertRaises(sc.SleeperAPIError):
            self._client(boom).get_players()

    def test_an_empty_response_from_sleeper_is_not_treated_as_a_universe(self):
        """Sleeper returning `{}` is a failed pull, not a league with no players."""
        with self.assertRaises(sc.SleeperAPIError):
            self._client(lambda p: {}).get_players()


class TheCacheIsWrittenAtomicallyTests(unittest.TestCase):

    def setUp(self):
        self._dir = TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)

    def test_the_players_cache_never_passes_through_a_truncating_write(self):
        """`write_text` truncates first, so a reader mid-write sees an empty file. Asserted by
        watching the call, not by reading the source: the point is that the bytes never appear
        at the real path until they are all there."""
        seen = []
        real = sc.store_io.replace_atomically
        with mock.patch.object(sc.store_io, "replace_atomically",
                               side_effect=lambda p, t: (seen.append(Path(p).name), real(p, t))[1]):
            client = _Client(str(self.root), lambda p: {"1": {"position": "RB"}})
            client.get_players()
        self.assertIn(sc.PLAYERS_CACHE_FILENAME, seen)

    def test_both_snapshot_writes_are_atomic_too(self):
        """`_latest.json` is read on every rerun while a sync may be rewriting it, and a torn
        read of it looks exactly like a league that has never been synced."""
        seen = []
        real = sc.store_io.replace_atomically
        client = _Client(str(self.root), lambda p: None)
        with mock.patch.object(sc.store_io, "replace_atomically",
                               side_effect=lambda p, t: (seen.append(Path(p).name), real(p, t))[1]):
            client._write_snapshot("L1", {"synced_at": 1730000000, "league": {}})
        self.assertIn("L1_latest.json", seen)
        self.assertEqual(len(seen), 2, f"both snapshot files must be atomic, saw {seen}")

    def test_no_truncating_write_is_left_in_the_client(self):
        """The derived half: any NEW cache write added here would reintroduce the same defect,
        so the rule is stated over the module rather than over the three sites known today."""
        from test_source_scan import code_text
        code = code_text(Path(sc.__file__))
        self.assertNotIn(".write_text(", code,
                         "sleeper_client writes files that are read concurrently; route them "
                         "through store_io.replace_atomically rather than write_text")


if __name__ == "__main__":
    unittest.main()
