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
import inspect
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
        # Hand-enumerated ON PURPOSE: this list is where a new token must be added
        # DELIBERATELY, which is what makes the guard catch one that gained a label without
        # gaining a meaning. #214/F3 added pool_truncated -- the WEAKEST claim in the
        # vocabulary, stamped when a position's demand rank runs past the end of the priced
        # list. It binds at no position on the real rulebook today.
        emitted = {dr.REPLACEMENT_BASIS_LIVE_DEMAND, dr.REPLACEMENT_BASIS_PREDRAFT,
                   dr.REPLACEMENT_BASIS_STARTABLE_FLOOR, dr.REPLACEMENT_BASIS_POOL_TRUNCATED}
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


class ATruncatedPoolSaysSoInsteadOfClaimingDemandTests(unittest.TestCase):
    """#214/F3: the demand rank can fall past the end of the priced list.

    `idx = min(rank - 1, len(at_pos) - 1)` then reads the WORST priced player and the board
    stamped `live_starter_demand` on it -- the strongest claim in the vocabulary, for a floor
    nobody measured demand against. `horizon_replacement` refuses this exact case on the record
    ("a floor read off the bottom of a short list would rebuild that same defect one layer up");
    its sibling did it silently.

    LATENT, NOT LIVE, and that distinction is the finding. It was reported as active in
    HEAVY_IDP (DL rank 24 against 13 priced) -- but that measurement was taken under #213's
    one-key rulebook, where almost no IDP could price. On the REAL rulebook 86 DL, 85 LB and
    130 DB price and the clamp binds at NO position in either a 1QB or an IDP league. So this
    changes no number today. It exists so that if the pool ever thins, the board says which
    claim it is making rather than making the strongest one silently.
    """

    def test_the_clamp_is_recorded_when_it_binds(self):
        import pandas as pd
        pool = pd.DataFrame([{"position": "DL", "_points": v} for v in (100.0, 50.0, 10.0)])
        truncated = set()
        levels = dr.replacement_levels(pool, "_points", ["DL"] * 24, 12, {"DL": 24.0},
                                       truncated_out=truncated)
        self.assertEqual(truncated, {"DL"}, "rank 24 against 3 priced rows -- the clamp binds")
        self.assertEqual(levels["DL"], 10.0, "and still returns the clamped value, unchanged")

    def test_a_deep_pool_is_not_flagged(self):
        """A measured floor and a truncated one are different facts, and only one is flagged."""
        import pandas as pd
        pool = pd.DataFrame([{"position": "DL", "_points": float(100 - i)} for i in range(40)])
        truncated = set()
        dr.replacement_levels(pool, "_points", ["DL"] * 2, 12, {"DL": 2.0},
                              truncated_out=truncated)
        self.assertEqual(truncated, set())

    def test_the_out_parameter_is_optional_so_no_existing_caller_changed(self):
        import pandas as pd
        pool = pd.DataFrame([{"position": "DL", "_points": v} for v in (100.0, 50.0, 10.0)])
        self.assertEqual(dr.replacement_levels(pool, "_points", ["DL"] * 24, 12, {"DL": 24.0}),
                         {"DL": 10.0})

    def test_the_weakest_claim_is_stamped_last_so_nothing_overwrites_it(self):
        src = inspect.getsource(dr.compute_draft_board)
        floor_at = src.index("REPLACEMENT_BASIS_STARTABLE_FLOOR")
        trunc_at = src.index("REPLACEMENT_BASIS_POOL_TRUNCATED")
        self.assertGreater(trunc_at, floor_at,
                           "pool_truncated is the weakest claim available; a stronger token "
                           "stamped after it would bury exactly the qualification it adds")

    def test_it_binds_at_no_position_on_the_real_board(self):
        """The measurement that makes this latent rather than live. If this ever fails, the
        pool has thinned and the finding has become active -- re-derive, do not delete."""
        for board in (self.__class__._real_boards()):
            bases = {r.get("replacement_basis") for r in board}
            self.assertNotIn(dr.REPLACEMENT_BASIS_POOL_TRUNCATED, bases)

    @classmethod
    def _real_boards(cls):
        import data_merger as dm, draft_battery as dbat, run_draft_battery as rdb
        merger = dm.DataMerger()
        players_db, _ = rdb.build_players_db_from_capture()
        season = rdb.season_projections_from_capture()
        scoring = rdb.scoring_settings_from_capture()
        for league in (
            dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                 dynasty=True, base_scoring=scoring),
            {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                  "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
             "scoring_settings": {**scoring, "rec": 1.0},
             "total_rosters": 12, "settings": {"type": 2}},
        ):
            merger.set_league_format(dbat.league_format_hint(league))
            yield dr.compute_draft_board(
                merger, players_db, [], my_roster_id=None, league=league, mode="balanced",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)

    def test_the_board_actually_hands_the_collector_to_replacement_levels(self):
        """The WIRING, asserted on the call via AST.

        Behaviour cannot cover this: the clamp binds nowhere on real data, so a board that
        never passes the collector produces identical output to one that does. Removing the
        argument survived a mutation pass against every behavioural test here. Asserted on the
        call node -- not a substring, which this session has twice seen satisfied by a
        function's own explanatory prose.
        """
        import ast
        tree = ast.parse(inspect.getsource(dr.compute_draft_board).lstrip())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and getattr(n.func, "id", None) == "replacement_levels"]
        self.assertTrue(calls, "compute_draft_board must call replacement_levels")
        wired = [c for c in calls
                 if any(k.arg == "truncated_out" for k in c.keywords)]
        self.assertTrue(wired,
                        "the points-replacement call must hand over a collector, or the "
                        "pool_truncated basis can never be stamped no matter what happens")
