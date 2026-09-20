"""#112 -- "kind-of-absence stops at the board, and 'never checked' has no representation".

An unpriced row carried ONE token, `bpa_source = "no_priceable_input"`, for what the register
names as THREE different situations with three different answers to the ordering question:

  1. no replacement level for the position   structural absence.  unknown, NOT bad
  2. no projection from any source           a coverage gap.      unknown, NOT bad
  3. below every source's cutoff             weak evidence of genuinely low value

**Only (3) justifies ORDER LAST on its own merits**, and collapsing all three into one None
meant the board asserted the strongest of them about every unpriced row.

MEASURED ON A REAL BOARD, AND THE RESULT IS NOT WHAT THE ITEM ASSUMES. Of 1,119 rows, 638 are
unpriced -- and **every one of them is kind (2)**: no source put a number on him at all. So the
representation gap is real and the population is not. The one kind that is present is the kind
the register calls *unknown, not bad*, which is what makes the gap worth closing: ORDER LAST is
currently applied to a population containing NONE of the evidence that would justify it.

TWO OF THE THREE KINDS ARE NAMED AND PRODUCED BY NOBODY, deliberately.
  - (3) needs evidence the pool does not carry: that a source LISTS a player while declining to
    price him. Admission and pricing are separate questions here (#193), but a board row records
    only the outcome, not which sources were consulted, so the two cannot be distinguished from
    it. Producing (3) would require a new input, not a new predicate.
  - (1) is not a property of the pool at all -- replacement level is decided later, against the
    league's own demand.
Both are KEPT in the vocabulary anyway. Deleting an unpopulated kind makes the vocabulary
describe this dataset rather than the domain, and the next league with an unpriceable position
has nowhere to land -- which is how the collapse happened the first time.

MY FIRST IMPLEMENTATION OF THIS PUT AN ABSENCE KIND ON PRICED ROWS, and it is recorded here
because it is the shape that survives a green suite. It assigned kind (3) on
`no_points & trade_value.notna()`, reading that as "carried but unpriced". That predicate is the
TRADE-VALUE FALLBACK -- `position_relative_trade_value_vor`, confidence 35.0 in
`CONFIDENCE_BY_SOURCE` -- and those rows are priced. The field would have contradicted its own
contract, and no test could have caught it, because that branch has ZERO rows on every board
measured (0 of 1,119). A latent breach that only a reading of the branch, not a measurement of
it, could find. The classification is now derived from the source label itself, so "has a kind"
and "has no price" are the same question asked once.

A NEAR-MISS WORTH KEEPING. The first version of the population measurement matched board names
against the projections table with a hand-rolled normaliser and reported 0 of 643 present -- a
clean, tidy, completely false result. The control caught it: the same matcher found 0 of 475
PRICED rows too, because `norm_name` abbreviates first names (`a adebawore`) while board rows
carry full ones. The measurement above uses only fields the row already carries, so no matcher
is involved at all. `#245` -- identical numbers are a broken instrument until proven otherwise.
"""
from __future__ import annotations

import ast
import inspect
import unittest
from unittest import mock

import data_merger as dm
import draft_room as dr
import pick_debate as pdb
import pick_synthesis as ps
import quantity_readers as qr
from pick_synthesis import CandidateSnapshot

#: A real, rostered footballer nobody has priced -- clause 3 of `_admits_to_pool`. He is the
#: whole point of the fixture below: an unpriced row has to be REACHABLE on a real board before
#: any claim about how it is classified or carried means anything.
UNPRICED_ID = "999999"


def _fixture():
    """A small real board (~81 rows) that contains exactly one unpriced row.

    Small on purpose: the full capture pool takes a minute to price and proves nothing extra
    here. What it must NOT be is hand-made -- the mutations this file exists to catch both live
    between the board and the snapshot, and a hand-built row walks straight past them.
    """
    merger = dm.DataMerger()
    proj = merger.projections
    players_db, pid = {}, 0
    for pos in ("QB", "RB", "WR", "TE"):
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(20)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team")}
    players_db[UNPRICED_ID] = {"first_name": "Zzz", "last_name": "Unpricedman", "position": "WR",
                               "fantasy_positions": ["WR"], "team": "SF", "years_exp": 3}
    league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                 dynasty=True)
    return merger, players_db, league


class TheVocabularyIsThreeDistinctKinds(unittest.TestCase):
    def test_every_kind_is_distinct_and_none_is_the_priced_state(self):
        self.assertEqual(len(set(dr.ABSENCE_KINDS)), 3)
        self.assertNotIn(None, dr.ABSENCE_KINDS)

    def test_the_kinds_are_not_the_collapsed_token_they_replace(self):
        """`no_priceable_input` says THAT a row is unpriced. These say WHY. Reusing the old
        token as a kind would re-collapse the distinction this field exists to make."""
        self.assertNotIn(dr.NO_PRICEABLE_INPUT, dr.ABSENCE_KINDS)

    def test_the_tuple_is_derived_from_the_constants_not_typed_twice(self):
        """#126: one home. A hand-listed tuple drifts the first time a kind is added."""
        self.assertEqual(
            set(dr.ABSENCE_KINDS),
            {dr.ABSENCE_NO_INPUT, dr.ABSENCE_BELOW_SOURCE_CUTOFF, dr.ABSENCE_NO_REPLACEMENT})

    def test_every_kind_has_words_and_no_words_belong_to_a_dead_kind(self):
        """#126 in both directions: no kind renders nothing, and no phrase outlives its kind."""
        self.assertEqual(set(dr.ABSENCE_KIND_LABELS), set(dr.ABSENCE_KINDS))


class TheKindTravelsOnBothSerializations(unittest.TestCase):
    """#174's lesson applied before it could recur: a companion that reaches only one of the two
    board serializations is a number crossing a boundary its basis does not."""

    def test_both_column_lists_carry_it(self):
        from pathlib import Path
        src = Path(dr.__file__).read_text()
        self.assertGreaterEqual(src.count('"absence_kind",'), 2,
                                "absence_kind is missing from one of the two serializations")


class WhatTheFieldMayNotBecome(unittest.TestCase):
    """Guards against the ways this repair could rot into the defect it fixes."""

    def test_no_kind_is_spelled_as_a_number_or_a_bool(self):
        """A numeric kind would be orderable, and something would eventually order by it."""
        for kind in dr.ABSENCE_KINDS:
            with self.subTest(kind):
                self.assertIsInstance(kind, str)
                self.assertTrue(kind.strip())

    def test_the_kinds_nobody_produces_today_are_KEPT(self):
        """Two of three have no producer. Deleting them would make the vocabulary describe this
        dataset rather than the domain -- see the module docstring."""
        for kind in (dr.ABSENCE_NO_REPLACEMENT, dr.ABSENCE_BELOW_SOURCE_CUTOFF):
            with self.subTest(kind):
                self.assertIn(kind, dr.ABSENCE_KINDS)


class TheBoardClassifiesOnlyWhatItActuallyKnows(unittest.TestCase):
    """THE REGRESSION GUARD FOR MY OWN FIRST VERSION, which put an absence kind on priced rows.

    Run against a real board rather than a predicate, because the defect was a reading of the
    predicate: `no_points & trade_value.notna()` looks like "carried but unpriced" and is in
    fact the trade-value fallback, which prices the row."""

    @classmethod
    def setUpClass(cls):
        merger, players_db, league = _fixture()
        cls.board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                           league=league, mode="balanced")
        cls.by_id = {r["player_id"]: r for r in cls.board}

    def test_the_population_is_not_vacuous(self):
        """A rate over an empty set is not a rate. Both states must be present to compare."""
        kinds = [r.get("absence_kind") for r in self.board]
        self.assertGreater(sum(k is not None for k in kinds), 0, "no unpriced row on this board")
        self.assertGreater(sum(k is None for k in kinds), 0, "no priced row on this board")

    def test_a_kind_is_present_EXACTLY_when_the_row_has_no_price(self):
        """The contract as one statement over every row, not a claim about a branch."""
        for row in self.board:
            with self.subTest(row["player_id"]):
                self.assertEqual(row.get("absence_kind") is not None, row.get("bpa") is None)

    def test_no_priced_row_carries_a_kind(self):
        """Stated separately from the iff above because it is the half that was BROKEN, and a
        future edit that reintroduces it should fail a test that names it."""
        offenders = [r["player_id"] for r in self.board
                     if r.get("bpa") is not None and r.get("absence_kind") is not None]
        self.assertEqual(offenders, [], "an absence kind on a row that has a number")

    def test_the_unpriced_row_is_classified_as_the_coverage_gap(self):
        row = self.by_id[UNPRICED_ID]
        self.assertIsNone(row["bpa"])
        self.assertEqual(row["bpa_source"], dr.NO_PRICEABLE_INPUT)
        self.assertEqual(row["absence_kind"], dr.ABSENCE_NO_INPUT)

    def test_the_kind_is_derived_from_the_source_label_not_re_derived(self):
        """#126. Re-deriving `no points and no trade value` here is how the two questions
        drifted apart the first time; the source label already answers it."""
        src = inspect.getsource(dr._derive_points_and_source)
        assign = [line for line in src.splitlines() if '"absence_kind"' in line and "=" in line]
        self.assertTrue(any("bpa_source" in line for line in assign),
                        "the kind is assigned from something other than the source label")


class TheKindSurvivesTheBoundary(unittest.TestCase):
    """#174 again, one layer on: the board records the kind and the SNAPSHOT must carry it.

    Driven with a REAL board row rather than a hand-built CandidateSnapshot. That distinction is
    the whole reason this class exists -- when every test constructed its own snapshot, severing
    the carry in `build_snapshot` changed nothing anywhere and the mutation survived a full run.
    An AST reference is not a value (#119)."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db, cls.league = _fixture()
        cls.board = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id="1",
                                           league=cls.league, mode="balanced")
        cls.unpriced_row = next(r for r in cls.board if r["player_id"] == UNPRICED_ID)
        import draft_strategy as ds
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=2)

    def _snapshot_of(self, row):
        """Narrow the field to ONE real board row, then let build_snapshot do everything else."""
        with mock.patch.object(ps, "narrow_candidates", return_value=[row]):
            return ps.build_snapshot(
                self.merger, self.players_db, [], self.pick_order, current_index=0,
                my_roster_id="1", league=self.league, pick_label="1.01", top_n=1)

    def test_the_snapshot_carries_the_kind_off_a_real_unpriced_board_row(self):
        snap = self._snapshot_of(self.unpriced_row)
        candidate = snap.candidates[0]
        self.assertEqual(candidate.player_id, UNPRICED_ID)
        self.assertIsNone(candidate.universal_value, "fixture is not the state under test")
        self.assertEqual(candidate.absence_kind, dr.ABSENCE_NO_INPUT)

    def test_a_priced_row_reaches_the_snapshot_carrying_no_kind(self):
        """The other half of the iff, across the boundary: None here is the priced state, not a
        dropped field -- which is the failure this test would otherwise be unable to see."""
        priced = next(r for r in self.board if r.get("bpa") is not None)
        candidate = self._snapshot_of(priced).candidates[0]
        self.assertIsNotNone(candidate.universal_value)
        self.assertIsNone(candidate.absence_kind)


class TheVocabularyCrossesWithoutOpeningTheBoundary(unittest.TestCase):
    """FOUND BY THE MUTATION PASS, as a control failure rather than a surviving mutant.

    My first version imported `draft_room` into `pick_debate` to reach these names, and
    `test_pick_synthesis.DecisionBoundaryIsClosedTests` failed on it immediately -- correctly. A
    snapshot consumer that can import draft_room acquires `compute_draft_board` along with the
    vocabulary, and the debate layer's own instruction to the models ("do not recompute") stops
    being structural. The vocabulary crosses the way the other four do: re-exported by
    pick_synthesis, which IS the boundary rather than a consumer of it."""

    def test_pick_debate_does_not_import_draft_room(self):
        tree = ast.parse(inspect.getsource(pdb))
        reached = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                reached |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                reached.add(node.module.split(".")[0])
        self.assertNotIn("draft_room", reached,
                         "pick_debate can reach compute_draft_board and re-price a candidate")

    def test_the_re_export_is_the_same_object_not_a_copy(self):
        self.assertIs(ps.ABSENCE_KIND_LABELS, dr.ABSENCE_KIND_LABELS)
        self.assertIs(ps.ABSENCE_KINDS, dr.ABSENCE_KINDS)

    def test_the_consumer_does_not_restate_the_words(self):
        src = inspect.getsource(pdb)
        for words in dr.ABSENCE_KIND_LABELS.values():
            self.assertNotIn(words, src, "pick_debate keeps its own copy of the prose")


def _unpriced(**over) -> CandidateSnapshot:
    base = dict(
        position_best_now=None, position_next_turn_value=None, acting_now_value=None,
        player_id="1", name="T", position="RB", team="SF", bpa=None,
        bpa_source=dr.NO_PRICEABLE_INPUT, confidence=None, universal_value=None,
        need_bonus=6.0, team_acquisition_value=None,
        survival_probability=0.4, survival_basis=None, intervening_picks=2, opportunity_cost=None,
        expected_value_of_waiting=None, denial_value=None, denial_basis=None,
        rival_premium_basis=None, denial_team=None, rival_premium=None,
        positional_forfeit=None, position_expected_taken=None, positional_cliff=None,
        position_run_detected=False, pick_necessity=10.0, necessity_label="X",
        near_tie_with_leader=None, cliff_protection=False, block_opportunity=False,
        pure_value=False, context_elevated=False, consensus_rank=None, consensus_tier=None,
        projected_points=None)
    base.update(over)
    return CandidateSnapshot(**base)


class TheKindHasAREADER(unittest.TestCase):
    """THE HALF MY FIRST ATTEMPT MISSED, and the suite caught it. Recording the kind on the
    board and stopping there produced a write-only quantity -- exactly what #119 had just been
    opened for, and `test_quantity_readers.TheWriteOnlySetMustNotGrowTests` failed on it within
    the same pass. A distinction nobody reads is not a distinction."""

    def test_absence_kind_is_not_write_only(self):
        self.assertNotIn("absence_kind", {r["quantity"] for r in qr.write_only()},
                         "absence_kind is recorded and read by nobody -- #112 is half-done")

    def test_each_kind_says_something_DIFFERENT_to_a_person(self):
        """The whole point. Three kinds rendering one phrase would be the collapse again, in
        prose instead of in a token."""
        seen = set()
        for kind in dr.ABSENCE_KINDS:
            with self.subTest(kind):
                out = pdb._format_candidate(_unpriced(absence_kind=kind), None)
                line = next(l for l in out.splitlines() if "Universal value" in l)
                phrase = line.split("never as low.")[-1].strip()
                self.assertTrue(phrase, f"{kind} renders no explanation at all")
                seen.add(phrase)
        self.assertEqual(len(seen), len(dr.ABSENCE_KINDS), "two kinds render the same prose")

    def test_the_coverage_gap_denies_the_low_grade_reading(self):
        """The dangerous inference, refused at the site: an unpriced player is not a bad one.
        This is the kind that every unpriced row on a real board actually carries."""
        out = pdb._format_candidate(_unpriced(absence_kind=dr.ABSENCE_NO_INPUT), None)
        self.assertIn("COVERAGE GAP", out)
        self.assertIn("not a low grade", out)

    def test_only_the_cutoff_kind_is_called_evidence_of_low_value(self):
        """The register's own distinction: one of three justifies ORDER LAST; the others do not."""
        cut = pdb._format_candidate(_unpriced(absence_kind=dr.ABSENCE_BELOW_SOURCE_CUTOFF), None)
        self.assertIn("weak evidence of genuinely low value", cut)
        for other in (dr.ABSENCE_NO_INPUT, dr.ABSENCE_NO_REPLACEMENT):
            with self.subTest(other):
                self.assertNotIn("evidence of genuinely low value",
                                 pdb._format_candidate(_unpriced(absence_kind=other), None))

    def test_an_unrecorded_kind_stays_SILENT_rather_than_guessing(self):
        """A board that recorded no kind must not have one invented for it downstream -- that
        substitution is the defect this whole field exists to prevent."""
        out = pdb._format_candidate(_unpriced(absence_kind=None), None)
        line = next(l for l in out.splitlines() if "Universal value" in l)
        self.assertEqual(line.split("never as low.")[-1].strip(), "")

    def test_the_prose_table_is_keyed_on_the_vocabulary_not_a_parallel_list(self):
        """#126: one home. Every phrase key must be a real kind, so the table cannot carry an
        entry for a kind that no longer exists."""
        self.assertTrue(set(dr.ABSENCE_KIND_LABELS).issubset(set(dr.ABSENCE_KINDS)))


if __name__ == "__main__":
    unittest.main()
