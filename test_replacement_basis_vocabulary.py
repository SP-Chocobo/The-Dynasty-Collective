"""#185 + #186: which authority set this row's replacement level, and does the reader hear it?

#185 -- replacement_levels has two arms. The `startable_floors` arm counts how many remaining
players clear a projection threshold and NEVER READS `demand` at all. Every superflex QB row
was nonetheless labelled "live_starter_demand". That is #166's shape at the point a person
reads it, and it fails toward the STRONGER claim: "this league's starter demand set this
price" asserts more than "a startability threshold did".

#186 -- the words for that token were written TWICE: once implicitly in Python, once as a
hand-written ternary in the board's JS:

    c.replacementBasis === 'predraft_anchor' ? 'pre-draft anchor' : 'live starter demand'

so every token the JS did not know about rendered as "live starter demand". These two cannot
ship apart: adding a third token on the Python side while that ternary stands would print the
strongest claim in the vocabulary on exactly the rows that earned the weakest one.

Measured on the real capture, 12-team dynasty PPR: 39 QB rows move in superflex, and the 1QB
control is unchanged (475 basis-carrying rows before and after, 436 + 39).
"""

from __future__ import annotations

import collections
import re
import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_board_ui
import draft_room as dr
import run_draft_battery as rdb

CAPTURE = Path("data/fixtures/sleeper_capture.json")


class TheVocabularyHasOneHomeTests(unittest.TestCase):

    def test_every_token_the_engine_can_emit_has_words(self):
        emitted = {dr.REPLACEMENT_BASIS_LIVE_DEMAND, dr.REPLACEMENT_BASIS_PREDRAFT,
                   dr.REPLACEMENT_BASIS_STARTABLE_FLOOR}
        self.assertEqual(emitted, set(dr.REPLACEMENT_BASIS_LABELS))

    def test_absence_is_not_a_key(self):
        # A row with no price has no basis to state. Giving None a label here would invite a
        # caller to render one.
        self.assertNotIn(None, dr.REPLACEMENT_BASIS_LABELS)

    def test_the_engine_writes_tokens_through_the_named_constants_not_literals(self):
        # The literals are what let the vocabulary drift apart in the first place.
        source = Path("draft_room.py").read_text(encoding="utf-8")
        body = source.split("REPLACEMENT_BASIS_LABELS = {", 1)[1].split("}", 1)[1]
        for literal in ('"live_starter_demand"', '"predraft_anchor"', '"startable_floor"'):
            self.assertNotIn(f'= {literal}', body,
                             f"{literal} is assigned as a bare string outside the table")


class TheBoundaryCarriesTheVocabularyTests(unittest.TestCase):
    """#186: the JS must not restate the words, and must not invent them."""

    def test_the_payload_carries_the_labels(self):
        source = Path("draft_board_ui.py").read_text(encoding="utf-8")
        self.assertIn('"replacementBasisLabels": dict(REPLACEMENT_BASIS_LABELS)', source)
        # And it must arrive by a NAMED import, never `import draft_room` -- a snapshot
        # consumer that can reach the module can reach compute_draft_board, which
        # test_pick_synthesis.DecisionBoundaryIsClosedTests exists to forbid. That guard
        # caught this file's first draft.
        self.assertNotIn("\nimport draft_room\n", source)

    def test_the_hand_written_ternary_is_gone(self):
        source = Path("draft_board_ui.py").read_text(encoding="utf-8")
        self.assertNotIn("'predraft_anchor' ? 'pre-draft anchor' : 'live starter demand'",
                         source)

    def test_no_basis_WORDS_are_written_in_the_javascript_at_all(self):
        # The real invariant, not just the absence of one known line: the human-readable
        # phrases must exist only in Python's table. A future edit that reintroduces any of
        # them into the JS fails here.
        source = Path("draft_board_ui.py").read_text(encoding="utf-8")
        js = source.split("const ABSENT", 1)[1]
        for words in dr.REPLACEMENT_BASIS_LABELS.values():
            self.assertNotIn(words, js, f"the JS restates {words!r} instead of reading the table")

    def test_an_unrecognised_token_falls_back_to_ITSELF_not_to_a_claim(self):
        # The whole point of #186. Read the fallback branch and require that it returns the
        # token, never a member of the vocabulary.
        source = Path("draft_board_ui.py").read_text(encoding="utf-8")
        fn = re.search(r"function basisLabel\(token\)\s*\{(.*?)\n\}", source, re.S)
        self.assertIsNotNone(fn, "basisLabel is gone")
        body = fn.group(1)
        self.assertIn("hasOwnProperty", body, "the lookup does not distinguish known from unknown")
        self.assertIn("token", body.rsplit(":", 1)[-1], "the fallback is not the token itself")
        for words in dr.REPLACEMENT_BASIS_LABELS.values():
            self.assertNotIn(words, body)


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class OnTheRealBoardTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db, _ = rdb.build_players_db_from_capture()
        cls.season = rdb.season_projections_from_capture()
        cls.sf = cls._board(cls, superflex=True)
        cls.one_qb = cls._board(cls, superflex=False)

    def _board(self, superflex: bool):
        league = dr.build_mock_league(teams=12, superflex=superflex, scoring="ppr",
                                      te_premium=False, dynasty=True)
        self.merger.set_league_format(db.league_format_hint(league))
        return dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=league, mode="balanced",
            sleeper_projections=self.season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

    @staticmethod
    def _bases(board, position=None):
        return collections.Counter(
            row.get("replacement_basis") for row in board
            if position is None or row["position"] == position)

    def test_superflex_QB_rows_say_the_floor_priced_them(self):
        qb = self._bases(self.sf, "QB")
        self.assertGreater(qb[dr.REPLACEMENT_BASIS_STARTABLE_FLOOR], 0,
                           "the floor branch runs but no row says so")
        self.assertEqual(qb[dr.REPLACEMENT_BASIS_LIVE_DEMAND], 0,
                         "a floor-priced QB still claims live starter demand")

    def test_a_1QB_league_still_prices_QBs_on_demand_and_says_so(self):
        # The control. No SUPER_FLEX slot means no floor is ever built, so nothing here may
        # change -- if it did, the derivation is reaching further than the branch it describes.
        qb = self._bases(self.one_qb, "QB")
        self.assertGreater(qb[dr.REPLACEMENT_BASIS_LIVE_DEMAND], 0)
        self.assertEqual(qb[dr.REPLACEMENT_BASIS_STARTABLE_FLOOR], 0)

    def test_no_NON_QB_row_is_touched_in_either_league(self):
        # Blast radius, proven rather than asserted: only the position that was handed a floor
        # may carry the new token.
        for board in (self.sf, self.one_qb):
            offenders = [r["name"] for r in board
                         if r["position"] != "QB"
                         and r.get("replacement_basis") == dr.REPLACEMENT_BASIS_STARTABLE_FLOOR]
            self.assertEqual(offenders[:5], [])

    def test_the_total_basis_carrying_population_is_unchanged_by_the_relabel(self):
        # A relabel must move rows BETWEEN buckets, never create or destroy one.
        sf_stated = sum(v for k, v in self._bases(self.sf).items() if k is not None)
        one_stated = sum(v for k, v in self._bases(self.one_qb).items() if k is not None)
        self.assertEqual(sf_stated, one_stated)

    def test_an_unpriced_row_still_states_no_basis_at_all(self):
        for board in (self.sf, self.one_qb):
            offenders = [r["name"] for r in board
                         if r.get("universal_value") is None
                         and r.get("replacement_basis") is not None]
            self.assertEqual(offenders[:5], [])

    def test_every_basis_on_a_real_board_is_in_the_vocabulary(self):
        for board in (self.sf, self.one_qb):
            for row in board:
                basis = row.get("replacement_basis")
                if basis is not None:
                    self.assertIn(basis, dr.REPLACEMENT_BASIS_LABELS, row["name"])


if __name__ == "__main__":
    unittest.main()
