"""#201: resolving a name is a pure function, and the battery was paying for it 168 times.

`build_available_pool` calls `merge_player` for every player on EVERY board build. Nothing
about a draft in progress can change that answer -- the vendor table is fixed, and a player's
name, position and team do not move between picks -- yet a 168-pick simulated draft asked the
same questions 168 times, and the answer for a MISS runs difflib's fuzzy search over the whole
table before concluding nothing fits.

Invisible until #201 pointed the battery at the real Sleeper universe, because the vendor
reconstruction was only 764 players. Measured on one board build of the same format:

    pool                       rows    first build   warm build
    vendor reconstruction  764  280        0.60s        0.18s
    real Sleeper capture  6595 1111       13.19s        0.49s

13.55s per board x 168 picks x 33 arms put a full battery near 21 hours, which is the
difference between a gate that gets run and one that does not.

WHY A MEMO IS SAFE HERE AND WHERE IT STOPS. The key is (name, position, team) and it lives on
the merger, cleared in `_load` -- the single place the tables it describes are rebuilt, which
`reload()` and `set_league_format()` both route through. Three deliberate limits, each with a
test below: a caller-supplied `df` is never cached (an ad hoc table this merger knows nothing
about); the cached dict is COPIED out (build_roster_table does row.update() straight onto its
result, so handing back the cached object would let one caller's mutation become another's
input); and MISSES are cached too, since the miss is the expensive path.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import unittest

import pandas as pd

import data_merger as dm


class TheAnswerIsTheSameEitherWayTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_a_repeated_lookup_returns_an_equal_answer(self):
        first = self.merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        again = self.merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        self.assertEqual(first, again)
        self.assertTrue(first.get("matched"))

    def test_a_miss_is_cached_too_because_the_miss_is_the_expensive_path(self):
        name = "Nobody Whatsoever Iii"
        before = len(self.merger._merge_memo)
        self.merger.merge_player(name, position="WR", team="MIN")
        self.merger.merge_player(name, position="WR", team="MIN")
        self.assertIn((name, "WR", "MIN"), self.merger._merge_memo)
        self.assertGreater(len(self.merger._merge_memo), before)

    def test_the_key_separates_queries_that_must_not_share_an_answer(self):
        """(name, position, team) is the whole key, and each part has to matter -- #196's two
        Byron Youngs differ only by club, and its Jermar Jefferson case only by position."""
        phi = self.merger.merge_player("Byron Young", position="DL", team="PHI")
        lar = self.merger.merge_player("Byron Young", position="DL", team="LAR")
        self.assertNotEqual(phi.get("matched"), lar.get("matched"))
        rb = self.merger.merge_player("Jermar Jefferson", position="RB", team="MIN")
        wr = self.merger.merge_player("Jermar Jefferson", position="WR", team="MIN")
        self.assertNotEqual(rb.get("matched"), wr.get("matched"))


class TheCallerOwnsWhatItReceivesTests(unittest.TestCase):

    def test_two_calls_hand_back_distinct_objects(self):
        merger = dm.DataMerger()
        first = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        again = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        self.assertIsNot(first, again)

    def test_mutating_a_result_cannot_poison_the_next_caller(self):
        """build_roster_table does row.update() straight onto this dict. Returning the cached
        object would make one caller's edit another caller's input -- a defect that would look
        like data corruption arriving from nowhere."""
        merger = dm.DataMerger()
        got = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        original = got.get("trade_value")
        got["trade_value"] = 99999.0
        got["matched"] = False
        fresh = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        self.assertEqual(fresh.get("trade_value"), original)
        self.assertTrue(fresh.get("matched"))

    def test_mutating_a_result_that_CAME_FROM_the_cache_is_also_safe(self):
        """The hole the first version of this file left open, found by mutation.

        Copying only on the write path passes every test that mutates the FIRST result -- that
        one is always a fresh dict. The exposure is the second call onward: if the cache hands
        back its own object then, the third caller inherits the second caller's edits. So the
        mutation happens here on a result that is definitely a cache HIT."""
        merger = dm.DataMerger()
        merger.merge_player("Bijan Robinson", position="RB", team="ATL")   # populate
        from_cache = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        original = from_cache.get("trade_value")
        from_cache["trade_value"] = 12345.0
        third = merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        self.assertEqual(third.get("trade_value"), original)
        self.assertIsNot(from_cache, third)


class AStaleAnswerIsWorseThanASlowOneTests(unittest.TestCase):

    def test_changing_the_league_format_clears_it(self):
        """set_league_format picks a DIFFERENT rankings export -- the measurement skill calls
        this the biggest fixture hazard in the repo. A memo that survived it would serve
        answers from the previous format's table."""
        merger = dm.DataMerger()
        merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        self.assertGreater(len(merger._merge_memo), 0)
        merger.set_league_format({"scoring": "ppr", "superflex": True, "te_premium": False})
        self.assertEqual(len(merger._merge_memo), 0)

    def test_an_explicit_reload_clears_it(self):
        merger = dm.DataMerger()
        merger.merge_player("Bijan Robinson", position="RB", team="ATL")
        merger.reload()
        self.assertEqual(len(merger._merge_memo), 0)

    def test_a_caller_supplied_table_is_never_cached(self):
        """An ad hoc frame this merger knows nothing about. Keying on it would be a
        correctness bet for no gain -- these callers ask once."""
        merger = dm.DataMerger()
        before = dict(merger._merge_memo)
        frame = pd.DataFrame([{"name": "Someone", "norm_name": "someone",
                               "position": "WR", "team": "MIN", "trade_value": 5.0}])
        merger.merge_player("Someone", position="WR", team="MIN", df=frame)
        self.assertEqual(merger._merge_memo, before)


# MUTATIONS -- each applied to data_merger.py, this file re-run, the named test observed to
# FAIL, then reverted:
#   1. return the cached dict itself instead of dict(hit)  [SURVIVED the first version]
#        -> TheCallerOwnsWhatItReceives.test_mutating_a_result_that_CAME_FROM_the_cache_is_also_safe
#           FAILED, once that test existed. It did NOT exist at first, and the mutation passed:
#           every test then mutated the FIRST result, which is a fresh dict on the write path
#           regardless. Recorded rather than smoothed over -- a copy on one side only is a real
#           defect and the suite could not see it.
#   2. store the row itself and return it (no copy on the write side either)
#        -> ...test_mutating_a_result_cannot_poison_the_next_caller FAILED
#   3. _load does not reset _merge_memo (initialise it in __init__ instead)
#        -> AStaleAnswerIsWorseThanASlowOne.test_changing_the_league_format_clears_it FAILED
#           and ...test_an_explicit_reload_clears_it FAILED
#   4. memo_key computed ignoring `df`, so an ad hoc table is cached under the same key
#        -> ...test_a_caller_supplied_table_is_never_cached FAILED
#   5. memo_key drops `team` from the tuple
#        -> TheAnswerIsTheSameEitherWay.test_the_key_separates_queries_that_must_not_share...
#           FAILED
#   6. misses are not written to the memo
#        -> ...test_a_miss_is_cached_too_because_the_miss_is_the_expensive_path FAILED
if __name__ == "__main__":
    unittest.main()
