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



class ATruncatedPoolSaysSoInsteadOfClaimingDemandTests(unittest.TestCase):
    """#214/F3: the demand rank can fall past the end of the priced list.

    `idx = min(rank - 1, len(at_pos) - 1)` then reads the WORST priced player and the board
    stamped `live_starter_demand` on it -- the strongest claim in the vocabulary, for a floor
    nobody measured demand against. `horizon_replacement` refuses this exact case on the record
    ("a floor read off the bottom of a short list would rebuild that same defect one layer up");
    its sibling did it silently.

    LIVE as of the W2-05 repair, and the route by which it went live is the second finding.
    It was first reported as active in HEAVY_IDP (DL rank 24 against 13 priced); that
    measurement was taken under #213's one-key rulebook, where almost no IDP could price, and
    on the real rulebook 86 DL, 85 LB and 130 DB price on the POINTS branch, where the clamp
    still binds at no position. The clamp was binding on the OTHER branch all along. The
    trade_value fallback prices the half of the pool with no projection, and it was calling
    replacement_levels without a collector -- so a rank that ran off the end of a two-row list
    was clamped, and the row went out stamped `live_starter_demand` because nothing recorded
    that it had been. Handing that branch the same collector moved two real rows (see
    test_the_measured_census_of_the_clamp_on_the_real_rulebook).

    The shape to carry forward: a recording argument omitted on ONE of two sibling calls is
    invisible to every behavioural test, because the branch that has it produces the evidence
    and the branch that lacks it produces silence, and silence is what a passing absence
    assertion looks like. That is why the wiring test below now demands the argument on EVERY
    call rather than on at least one.
    """

    def test_the_clamp_is_recorded_when_it_binds(self):
        import pandas as pd
        pool = pd.DataFrame([{"position": "DL", "_points": v} for v in (100.0, 50.0, 10.0)])
        truncated = set()
        levels = dr.replacement_levels(pool, "_points", ["DL"] * 24, 12, {"DL": 24.0},
                                       truncated_out=truncated)
        self.assertEqual(truncated, {"DL"}, "rank 24 against 3 priced rows -- the clamp binds")
        self.assertEqual(levels["DL"], 10.0, "and still returns the clamped value, unchanged")

    def test_a_rank_landing_exactly_on_the_last_priced_row_is_not_a_clamp(self):
        """THE BOUNDARY, which neither real board exercises.

        `rank - 1 > len(at_pos) - 1` loosened to `>=` flags the case where the demand rank
        lands exactly on the last priced player -- which is not a clamp at all: that player IS
        the player at replacement rank, and `min()` did not move the index. Neither real board
        has a position sitting exactly on that boundary, so the loosened condition produced an
        identical census on both and survived every behavioural test here. An off-by-one in a
        flag is still a false claim about what a price rests on.
        """
        import pandas as pd
        pool = pd.DataFrame([{"position": "DL", "_points": v} for v in (100.0, 50.0, 10.0)])
        truncated = set()
        levels = dr.replacement_levels(pool, "_points", ["DL"] * 3, 12, {"DL": 3.0},
                                       truncated_out=truncated)
        self.assertEqual(truncated, set(),
                         "rank 3 against 3 priced rows lands ON the last one -- no clamp")
        self.assertEqual(levels["DL"], 10.0,
                         "and the level is that same last row, which is why the flag would be "
                         "a lie rather than a harmless extra")
        # The non-vacuity arm: one more rank, same pool, and it IS a clamp.
        one_deeper = set()
        dr.replacement_levels(pool, "_points", ["DL"] * 4, 12, {"DL": 4.0},
                              truncated_out=one_deeper)
        self.assertEqual(one_deeper, {"DL"},
                         "rank 4 against the same 3 rows runs off the end, so the boundary "
                         "above is a boundary and not an empty assertion")

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

    def test_the_stamp_agrees_with_an_independent_recomputation_of_the_clamp(self):
        """The invariant, re-derived from the demand rank rather than read off the collector.

        The predecessor of this test asserted the clamp bound NOWHERE, and instructed its
        successor to re-derive rather than delete when that stopped being true. It stopped
        being true the moment the trade_value branch was handed a collector, so this is the
        re-derivation: recompute, from the league's own demand and a count of what each branch
        actually priced, which positions a rank ran off the end of -- and require the board's
        basis column to say exactly that set, no more and no less.

        This does not consult `truncated_out`. It recomputes the condition
        (`rank - 1 > len(at_pos) - 1`) from quantities the board publishes, so a collector
        that silently stopped collecting fails here.

        Compared as (position, BRANCH) pairs, not as positions. A position-set comparison is
        satisfied by a stamp that reaches the right position on the WRONG branch: dropping the
        `~has_proj` scope leaves the set identical while relabelling the 85 LB rows the points
        branch priced against 85 real players as "the bottom of a short priced list". That
        mutant survived a position-set version of this test.
        """
        for name, board, league in self.__class__._real_boards():
            expected = self.__class__._clamped_branches(board, league)
            stamped = {(r["position"], self.__class__._has_projection(r)) for r in board
                       if r.get("replacement_basis") == dr.REPLACEMENT_BASIS_POOL_TRUNCATED}
            self.assertEqual(
                stamped, expected,
                f"{name}: the board's pool_truncated stamp and an independent recomputation "
                f"of the clamp must name the same positions ON THE SAME BRANCH")

    def test_a_clamped_position_never_also_claims_live_demand_on_the_same_branch(self):
        """Completeness of the stamp, which set-equality above cannot see.

        The stamp is applied per POSITION, scoped to one branch. If the scope were wrong --
        `has_proj` where `~has_proj` was meant -- the set above would still match while the
        rows carrying the clamped price kept saying `live_starter_demand`. This checks the
        rows.
        """
        for name, board, league in self.__class__._real_boards():
            clamped = self.__class__._clamped_branches(board, league)
            if not clamped:
                continue
            offenders = [r["name"] for r in board
                         if (r["position"], self.__class__._has_projection(r)) in clamped
                         and r.get("replacement_basis") == dr.REPLACEMENT_BASIS_LIVE_DEMAND]
            self.assertEqual(offenders[:5], [], f"{name}: priced off a truncated list")

    def test_the_measured_census_of_the_clamp_on_the_real_rulebook(self):
        """The live measurement, pinned so that a change in it is a decision and not a drift.

        Today, on the real rulebook: the 1QB league's trade_value branch prices NOTHING (no
        remaining row carries a trade value once the projected half is taken out), so no rank
        can run off any list and the clamp binds nowhere. The IDP league's trade_value branch
        prices exactly two rows, both LB, against a league starter demand of 24 -- so every
        row that branch prices rests on the bottom of a two-long list, and before the repair
        every one of them said `live_starter_demand`.

        If this fails, the pool has moved. Re-derive it the way this one was derived -- the
        two tests above are the invariant and hold at any census -- and do not relax it to an
        inequality, which is what would let the next silent clamp through.
        """
        census = {name: sorted(
                      {r["position"] for r in board
                       if r.get("replacement_basis") == dr.REPLACEMENT_BASIS_POOL_TRUNCATED})
                  for name, board, _ in self.__class__._real_boards()}
        self.assertEqual(census, {"1QB_ppr_dynasty": [], "IDP": ["LB"]})

    #: The two real leagues this class measures. Built at most once per process: each is a
    #: full board construction, and four of the tests here want the same two boards.
    _BOARD_CACHE: list = []

    @staticmethod
    def _has_projection(row):
        """Which of the two pricing branches this row went through, as the BOARD reports it.

        compute_draft_board splits on an internal `_points` column; `projected_points` is what
        that column becomes on the board, and the split is exact -- measured on the IDP board,
        780 rows carry one and 1193 do not, matching the two branches' own row counts with no
        row on either side of the disagreement. Kept in one place because two tests need the
        same split and a second spelling of it would be a second rule.
        """
        return row.get("projected_points") is not None

    @classmethod
    def _clamped_branches(cls, board, league):
        """Which (position, branch) pairs' demand rank ran off the end of the list that priced
        them -- the pair, because a clamp is a fact about ONE branch's list.

        Recomputed from the board's own published rows -- a count of what each branch priced
        -- and the league's own demand, via the same helper replacement_levels uses for the
        rank. The CLAMP CONDITION itself is restated here on purpose: that is the thing under
        test, and asking the collector for it would be asking the defect to report itself.
        """
        num_teams = league.get("total_rosters")
        # PRECONDITION, asserted rather than assumed. compute_draft_board hands the points
        # branch a startable floor for exactly one case -- QB in a SUPER_FLEX league -- and a
        # floored position is ranked by a count of players clearing a points threshold, not by
        # demand at all. Neither league here is superflex, so the demand rank is the only rank
        # in play and comparing against it is sound. Add a superflex league to _real_boards and
        # this fires, which is the point: the recomputation has to grow with the population.
        assert "SUPER_FLEX" not in league["roster_positions"], (
            "this recomputation only models the demand rank; a superflex league also uses the "
            "startable-floor rank and needs that arm written before it can be measured here")
        demand = {p: num_teams * dr.starter_slot_counts(
                      league["roster_positions"], None, num_teams).get(p, 0.0)
                  for p in dr.FANTASY_POSITIONS}
        clamped = set()
        for position in dr.FANTASY_POSITIONS:
            rank = dr._remaining_demand_rank(position, demand)
            if rank is None:
                continue
            for priced_by_this_branch in (True, False):
                n = sum(1 for r in board
                        if r["position"] == position
                        and cls._has_projection(r) is priced_by_this_branch
                        and r.get("replacement_basis") is not None)
                # n == 0 is not a clamp -- it is a branch that priced nothing at this
                # position, and there is no list for a rank to run off the end of. Counting it
                # as one would make every position either league leaves unpriced a false
                # positive, which is 7 of 9 positions on the 1QB board's trade_value branch.
                if n and rank > n:
                    clamped.add((position, priced_by_this_branch))
        return clamped

    @classmethod
    def _real_boards(cls):
        if cls._BOARD_CACHE:
            return cls._BOARD_CACHE
        import data_merger as dm, draft_battery as dbat, run_draft_battery as rdb
        merger = dm.DataMerger()
        players_db, _ = rdb.build_players_db_from_capture()
        season = rdb.season_projections_from_capture()
        scoring = rdb.scoring_settings_from_capture()
        for name, league in (
            ("1QB_ppr_dynasty",
             dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=scoring)),
            ("IDP",
             {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                   "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
              "scoring_settings": {**scoring, "rec": 1.0},
              "total_rosters": 12, "settings": {"type": 2}}),
        ):
            merger.set_league_format(dbat.league_format_hint(league))
            cls._BOARD_CACHE.append((name, dr.compute_draft_board(
                merger, players_db, [], my_roster_id=None, league=league, mode="balanced",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM), league))
        return cls._BOARD_CACHE

    def test_the_board_actually_hands_the_collector_to_replacement_levels(self):
        """The WIRING, asserted on the call via AST.

        Behaviour cannot cover this on the points branch: the clamp binds at no position there
        on real data, so a board that never passes the collector produces identical output to
        one that does. Removing the argument survived a mutation pass against every
        behavioural test here. Asserted on the call node -- not a substring, which this
        session has twice seen satisfied by a function's own explanatory prose.

        EVERY call, not at least one (W2-05). The original form of this test accepted a single
        wired call, and compute_draft_board had two: the collector reached the points branch
        and not the trade_value branch, and both this test and every behavioural test here
        passed while a real board stamped `live_starter_demand` on a clamped price.
        """
        import ast
        tree = ast.parse(inspect.getsource(dr.compute_draft_board).lstrip())
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call)
                 and getattr(n.func, "id", None) == "replacement_levels"]
        self.assertTrue(calls, "compute_draft_board must call replacement_levels")
        unwired = [ast.unparse(c)[:90] for c in calls
                   if not any(k.arg == "truncated_out" for k in c.keywords)]
        self.assertEqual(unwired, [],
                         "every replacement_levels call in compute_draft_board must hand over "
                         "a collector; one that does not cannot stamp pool_truncated no "
                         "matter what happens, and its silence is indistinguishable from a "
                         "clamp that never bound")


if __name__ == "__main__":
    unittest.main()
