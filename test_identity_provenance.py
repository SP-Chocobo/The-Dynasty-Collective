"""§16.3 / #107: a board row says how its identity was established, or the numbers lie by omission.

THE DEFECT, AS MEASURED. `merge_player` reports `match_path` honestly. `build_available_pool`
carries it onto every pool row. And both of `compute_draft_board`'s output column lists dropped
it -- confirmed by AST over the board's own subscript lists, not by grep. Both `_match_path` and
`_match_verified` were **write-only in production**: nothing read either one, anywhere.

WHAT THAT COST. §16.3 demonstrated aliasing an unmatched Sleeper name onto `J Chase` moving that
row's `trade_value` 41.0 -> 100.0 and its `projection` 202.0 -> 339.0 -- and doing so OVER a
correct automatic match (`match_path` was `"key"`, `match_verified` True, before the alias
existed). The alias branch deliberately bypasses `_contradicted`'s team/position rejection,
because overriding the guards is what an override IS. What was wrong is not that it happens; it
is that nothing downstream could tell it had.

WHY THREE STATES AND NOT A FLAG. "Is this yours" is not the only question. An automatic match
where several rows fit and the first won is neither your override nor a clean match, and
`_resolve` has always known the difference -- `_find_match` is `_resolve(...)[0]`, the row with
that flag discarded. `ambiguous` is that discarded flag, arriving where a reader can act on it.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import data_merger as dm
import draft_room as dr

POSITIONS = ("QB", "RB", "WR", "TE")
STANDARD_LEAGUE = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                       te_premium=False, dynasty=True)


def _players_db(merger: dm.DataMerger, limit: int = 40) -> dict[str, dict]:
    """A small real-baseline players_db, same reconstruction the other board tests use."""
    proj, players_db, pid = merger.projections, {}, 0
    for pos in POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(limit)
        for _, row in sub.iterrows():
            pid += 1
            players_db[str(pid)] = {
                "full_name": row["name"], "position": pos,
                "team": row.get("team") or "", "injury_status": None,
            }
    return players_db


class TheMappingIsHonestAboutEachCaseTests(unittest.TestCase):
    def test_an_alias_is_a_user_override_regardless_of_verification(self):
        """Not gated on match_verified. An alias bypasses the team/position guards on purpose,
        so "verified" means something different on that path, and reporting it as a clean match
        is exactly the mislabel #107 named."""
        for verified in (True, False):
            with self.subTest(verified=verified):
                self.assertEqual(dr.identity_basis("alias", verified), dr.IDENTITY_USER_OVERRIDE)

    def test_an_unambiguous_automatic_match_is_matched(self):
        for path in ("exact", "key"):
            with self.subTest(path=path):
                self.assertEqual(dr.identity_basis(path, True), dr.IDENTITY_MATCHED)

    def test_an_automatic_match_where_several_fit_is_ambiguous_not_matched(self):
        """The state nobody could see. `_resolve` reports candidates>1 and verified=False;
        `_find_match` drops the flag. Collapsing it into `matched` invents a certainty."""
        for path in ("key", "fuzzy"):
            with self.subTest(path=path):
                self.assertEqual(dr.identity_basis(path, False), dr.IDENTITY_AMBIGUOUS)

    def test_an_unrecorded_path_is_None_and_not_a_synonym_for_matched(self):
        """The fourth state. A row whose provenance was never recorded must not be labelled
        `matched` -- that claims clean identity for a row nothing checked. Absence is not a
        value, and this is the same rule replacement_basis and horizon_basis already follow."""
        self.assertIsNone(dr.identity_basis(None, False))
        self.assertIsNone(dr.identity_basis(None, True))

    def test_a_nan_path_is_also_None_because_pandas_will_produce_one(self):
        """A missing column read through pandas arrives as NaN, not None, and `NaN == "alias"`
        is False -- so without this the row would fall through to `matched`/`ambiguous` on the
        strength of a value that means "absent"."""
        self.assertIsNone(dr.identity_basis(float("nan"), True))


class ItReachesTheBoardInBothModesTests(unittest.TestCase):
    """The half that was actually broken: the label existed and never arrived. Asserted for BOTH
    branches, because the two returning different row schemas with nothing declaring it is a
    defect this module has already been bitten by once (see its universal_value comment)."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _players_db(cls.merger)

    def _board(self, mode):
        return dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1",
                                      league=STANDARD_LEAGUE, mode=mode)

    def test_every_row_carries_identity_basis_in_balanced_mode(self):
        board = self._board("balanced")
        self.assertTrue(board)
        for row in board:
            self.assertIn("identity_basis", row)

    def test_every_row_carries_identity_basis_in_upside_mode(self):
        board = self._board("upside")
        self.assertTrue(board)
        for row in board:
            self.assertIn("identity_basis", row)

    def test_the_committed_baseline_resolves_to_the_states_this_module_declares(self):
        """Non-vacuity against real data: the column is not uniformly None, and every value it
        takes is one this module named."""
        board = self._board("balanced")
        seen = {row["identity_basis"] for row in board}
        self.assertTrue(seen - {None}, "identity_basis is uniformly absent -- the column is dead")
        self.assertEqual(seen - {None, dr.IDENTITY_USER_OVERRIDE, dr.IDENTITY_MATCHED,
                                 dr.IDENTITY_AMBIGUOUS}, set())


class AnAliasIsVisibleOnTheBoardItMovedTests(unittest.TestCase):
    """#107's own scenario, end to end. §16.3 proved the alias moves the numbers; this proves the
    board now says so."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._real = dm.ALIASES_PATH
        dm.ALIASES_PATH = Path(self._tmpdir) / "player_aliases.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, dm, "ALIASES_PATH", self._real)

    def test_a_row_priced_through_an_alias_is_labelled_user_override(self):
        merger = dm.DataMerger()
        players_db = _players_db(merger)
        target_id, target = next(iter(players_db.items()))
        # Alias a name the pool does not carry onto a name it does -- the same shape of override
        # §16.3 measured, and the reason overrides exist at all.
        players_db = dict(players_db)
        players_db[target_id] = dict(target, full_name="Zzz Unmatchable Name")
        dm.save_alias("Zzz Unmatchable Name", target["full_name"])
        merger.reload()

        board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                       league=STANDARD_LEAGUE, mode="balanced")
        row = next((r for r in board if r["player_id"] == target_id), None)
        self.assertIsNotNone(row, "the aliased player should still be priced -- that is the point")
        self.assertEqual(row["identity_basis"], dr.IDENTITY_USER_OVERRIDE)

    def test_and_without_the_alias_the_same_row_is_not_labelled_that_way(self):
        """Non-vacuity: the label tracks the alias rather than being stuck on."""
        merger = dm.DataMerger()
        players_db = _players_db(merger)
        target_id = next(iter(players_db))
        board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1",
                                       league=STANDARD_LEAGUE, mode="balanced")
        row = next(r for r in board if r["player_id"] == target_id)
        self.assertNotEqual(row["identity_basis"], dr.IDENTITY_USER_OVERRIDE)


class TheFieldsAreNoLongerWriteOnlyTests(unittest.TestCase):
    """The literal finding: grepped across the whole repo, both fields were write-only. This is
    the assertion that fails if a future edit drops the column again -- which is exactly how the
    original defect happened, since the label was always produced and only the OUTPUT list
    forgot it."""

    def test_both_output_column_lists_carry_identity_basis(self):
        source = (Path(__file__).parent / "draft_room.py").read_text()
        self.assertEqual(source.count('"identity_basis",'), 2,
                         "both branches' output lists must emit it, or the two modes return "
                         "different row schemas again")

    def test_the_board_is_the_reader_the_match_fields_never_had(self):
        source = (Path(__file__).parent / "draft_room.py").read_text()
        self.assertIn("identity_basis(path, verified)", source)


if __name__ == "__main__":
    unittest.main()
