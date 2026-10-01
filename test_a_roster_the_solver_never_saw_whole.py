"""MANDATE 3.4 / `#187` / `#126` -- depth answered for a roster one body emptier than the real one.

`_team_roster_players` prices a roster through Draft Sharks' `trade_value`, and a man it cannot
price is DROPPED -- he keeps his roster spot in reality and vanishes from the solve. The module
already knows this and records two candidate repairs as unchosen, which is a `#184` design call and
is not what this module is about. What it is about is that the CONSEQUENCE travelled silently:
`depth_exposure` went on answering, and its basis claimed a full measurement either way.

`displacement_adjustments` got `DISPLACEMENT_ROSTER_PARTIAL` for this exact hole. Depth got nothing.

MEASURED, over a complete 216-pick HEAVY_IDP draft: **48 of 216 rostered players are dropped**,
every one of them IDP (DL 10, LB 18, DB 20).

THE TWO TERMS FAIL IN OPPOSITE DIRECTIONS, which is why the labels cannot borrow each other's
wording. A missing occupant makes DISPLACEMENT under-count (an open slot deducts nothing), so its
number is a FLOOR. It makes DEPTH over-count, because a hole with no cover costs more than one a
spare would have filled, so that number is a CEILING. Hand-built, two LB starters:

    bench LB priced      worst_loss 13    depth_exposure 1.56
    bench LB dropped     worst_loss 28    depth_exposure 3.36

AND WHAT IT REPLACES WAS A FALSE CLAIM, not merely an imprecise one. Where the dropped man was the
only spare, the basis read `no_surplus` -- "some starter here has no cover" -- and where he would
have been the only man at the position it read `vacant` -- "you hold no starter at this position to
insure". Both are statements about the ROSTER that the engine is in no position to make: the player
exists, and all that happened is that nobody could price him.

THE NUMBER IS NOT SPENT UNDER THE NEW TOKEN, and this is the one place the displacement precedent is
deliberately NOT followed. `displacement_adj` crosses in every basis state because it is one
quantity throughout. `worst_loss` is not: under `measured` it is what a backup would have to cover,
and under `no_surplus` it is a starter's whole value, on a different scale and explicitly not a
depth price. `EXPOSURE_ROSTER_PARTIAL` and `DISPLACEMENT_ROSTER_PARTIAL` can override either, so under
either of them the quantity stops being
identifiable -- and spending an unidentifiable number is how a starter's whole value would get
charged as depth.

MEASURED CONSEQUENCE ON REAL DATA -- and my first statement of this was too strong, which one of
the tests below caught. At a mid-draft state (13 of 18 rounds) 453-816 board rows per roster gain the
truthful basis and `depth_exposure` changes on **zero** rows, so I wrote that the repair moves no
price. On the COMPLETE 216-pick draft it does. Over all twelve final rosters, 32 cells are
relabelled:

    26   were `no_surplus`   -- a false label, number already withheld
     4   were `vacant`       -- a false label, number already withheld
     2   were `measured`     -- a spent number, now withdrawn

The two are roster 7's LB (depth_exposure 2.16) and roster 11's LB (1.44). Both are withdrawals of a
CEILING: those rosters held a dropped LB, so the hole was priced as though nothing covered it. So the
repair fixes 30 false labels and removes 2 over-credits worth 3.60 TAV points in total.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import lineup_optimizer as lo
import run_draft_battery as rdb

IDP_SLOTS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
             "DL", "DL", "LB", "LB", "DB", "DB", "BN", "BN", "BN"]


def _row(name, position, value):
    return {"id": name, "value": value, "eligible": {position}}


def _full_roster():
    return [_row("qb", "QB", 80), _row("rb1", "RB", 70), _row("rb2", "RB", 60),
            _row("wr1", "WR", 75), _row("wr2", "WR", 65), _row("te", "TE", 50),
            _row("flex", "RB", 40),
            _row("dl1", "DL", 45), _row("dl2", "DL", 42),
            _row("lb1", "LB", 48), _row("lb2", "LB", 44),
            _row("db1", "DB", 40), _row("db2", "DB", 38)]


class TheDropLeavesARecordTests(unittest.TestCase):
    """The out-parameter, shaped like `data_merger.load_all`'s `skipped` (MANDATE 2.4), because
    _team_roster_players has callers that want only the players."""

    @classmethod
    def setUpClass(cls):
        cls.players_db = {
            "priced": {"position": "RB", "fantasy_positions": ["RB"]},
            "edge": {"position": "LB", "fantasy_positions": ["DL", "LB"]},
        }

    def _drop(self, merger):
        unpriced = []
        picks = [{"player_id": pid, "roster_id": "1"} for pid in self.players_db]
        dr._team_roster_players(picks, self.players_db, "1", merger, frozenset(),
                               unpriced=unpriced)
        return unpriced

    def test_the_parameter_is_optional_so_no_existing_caller_changes(self):
        """A changed return shape would have touched every caller; several want only the list."""
        import inspect
        parameter = inspect.signature(dr._team_roster_players).parameters["unpriced"]
        self.assertIs(parameter.default, None)

    def test_a_dropped_man_is_recorded_by_ELIGIBILITY_not_by_his_primary_bucket(self):
        """`#172`. A dual DL/LB man could have covered a slot at either, so both positions'
        answers describe a roster missing him."""
        unpriced = []
        players_db = {"edge": {"position": "LB", "fantasy_positions": ["DL", "LB"]}}
        merger = dm.DataMerger()
        dr._team_roster_players([{"player_id": "edge", "roster_id": "1"}], players_db, "1",
                               merger, frozenset(), unpriced=unpriced)
        if unpriced:   # only if this merger cannot price him, which is the case under test
            self.assertEqual(unpriced[0], {"DL", "LB"},
                             "recorded at one position, so the other position's answer still "
                             "claims a roster it did not solve against")


class TheBasisSaysTheRosterWasNotWholeTests(unittest.TestCase):
    def test_a_position_a_dropped_man_could_cover_is_stamped(self):
        out = lo.depth_exposure(_full_roster(), IDP_SLOTS,
                                unpriced_eligibilities=[{"LB"}])
        self.assertEqual(out["LB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)

    def test_a_dual_eligible_dropped_man_stamps_BOTH_positions(self):
        out = lo.depth_exposure(_full_roster(), IDP_SLOTS,
                                unpriced_eligibilities=[{"DL", "LB"}])
        self.assertEqual(out["DL"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)
        self.assertEqual(out["LB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)

    def test_positions_he_could_NOT_cover_are_untouched(self):
        out = lo.depth_exposure(_full_roster(), IDP_SLOTS,
                                unpriced_eligibilities=[{"LB"}])
        self.assertNotEqual(out["DB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)
        self.assertNotEqual(out["RB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)

    def test_nothing_is_stamped_when_the_roster_was_fully_priced(self):
        plain = lo.depth_exposure(_full_roster(), IDP_SLOTS)
        self.assertNotIn(lo.EXPOSURE_ROSTER_PARTIAL,
                         {cell["basis"] for cell in plain.values()})

    def test_NOT_APPLICABLE_is_never_overridden(self):
        """It is a fact about the LEAGUE -- no slot admits the position -- and no roster can
        change it. Overriding it would replace a true statement with a weaker one."""
        offence_only = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN"]
        out = lo.depth_exposure(
            [_row("qb", "QB", 80), _row("rb1", "RB", 70), _row("rb2", "RB", 60)],
            offence_only, unpriced_eligibilities=[{"LB"}, {"DB"}])
        for position in ("LB", "DB"):
            self.assertEqual(out[position]["basis"], lo.EXPOSURE_NOT_APPLICABLE,
                             f"{position} has no slot in this league; the roster cannot change that")

    def test_it_replaces_the_no_surplus_claim_which_was_FALSE(self):
        """Dropping the only spare used to read "some starter here has no cover" -- and the cover
        exists, it just could not be priced."""
        roster = _full_roster() + [_row("lb3", "LB", 35)]
        without_him = [row for row in roster if row["id"] != "lb3"]
        self.assertEqual(lo.depth_exposure(without_him, IDP_SLOTS)["LB"]["basis"],
                         lo.EXPOSURE_NO_SURPLUS, "fixture no longer reproduces the false claim")
        repaired = lo.depth_exposure(without_him, IDP_SLOTS,
                                     unpriced_eligibilities=[{"LB"}])
        self.assertEqual(repaired["LB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)

    def test_it_replaces_the_vacant_claim_too(self):
        """"You hold no starter at this position to insure" is the same kind of false statement."""
        no_idp = [row for row in _full_roster()
                  if row["eligible"] not in ({"DL"}, {"LB"}, {"DB"})]
        self.assertEqual(lo.depth_exposure(no_idp, IDP_SLOTS)["LB"]["basis"], lo.EXPOSURE_VACANT)
        repaired = lo.depth_exposure(no_idp, IDP_SLOTS, unpriced_eligibilities=[{"LB"}])
        self.assertEqual(repaired["LB"]["basis"], lo.EXPOSURE_ROSTER_PARTIAL)


class TheNumberIsNotSpentUnderItTests(unittest.TestCase):
    def test_the_token_has_words_of_its_own(self):
        words = lo.EXPOSURE_BASIS_LABELS[lo.EXPOSURE_ROSTER_PARTIAL]
        #: RESTATED at the v4 blind pass, where three lenses found the same thing. This required
        #: the word "ceiling", and "ceiling" described `worst_loss` -- a number the BOARD never
        #: emits under this token, because `score_row` prices depth only under MEASURED. What a
        #: person reads beside this label is 0.0, and "a ceiling of 0.0" asserts no exposure at all
        #: about the position the engine knows least about. The label must now say that the number
        #: shown is NOT the measured one, which is the job the word "ceiling" was doing wrongly.
        self.assertIn("not charged", words)
        self.assertIn("NOT the 0.0", words,
                      "the label must say the figure beside it is not the exposure that was "
                      "measured -- otherwise 0.0 reads as 'no exposure here'")
        self.assertNotIn("a ceiling", words,
                         "'a ceiling' describes worst_loss, which never reaches the board under "
                         "this token")

    def test_the_board_prices_worst_loss_ONLY_under_measured(self):
        """Read from the source because the consumer is inside a long per-row closure. The gate is
        what keeps an unidentifiable quantity out of team_acquisition_value: under this token the
        number could be a backup's job or a starter's whole value, and those are different scales."""
        source = (Path(__file__).parent / "draft_room.py").read_text(encoding="utf-8")
        self.assertIn('if depth_basis == lo.EXPOSURE_MEASURED and depth.get("worst_loss") is not None:',
                      source)

    def test_the_dropped_body_really_does_inflate_the_number(self):
        """The direction, measured rather than asserted -- and the reason the label says ceiling.
        With a second spare behind him the state stays `measured`, so the number is spent, and it
        is spent too high."""
        roster = _full_roster() + [_row("lb3", "LB", 35), _row("lb4", "LB", 20)]
        whole = lo.depth_exposure(roster, IDP_SLOTS)["LB"]
        partial = lo.depth_exposure([row for row in roster if row["id"] != "lb3"],
                                    IDP_SLOTS)["LB"]
        self.assertEqual(whole["basis"], lo.EXPOSURE_MEASURED)
        self.assertEqual(partial["basis"], lo.EXPOSURE_MEASURED)
        self.assertGreater(partial["worst_loss"], whole["worst_loss"],
                           "dropping a spare must make the hole look MORE expensive, not less -- "
                           "if this reverses, the label's word 'ceiling' is wrong")


class OnRealDataItMovesNoPriceTests(unittest.TestCase):
    """The claim this repair is allowed to make, measured on a real draft rather than argued."""

    @classmethod
    def setUpClass(cls):
        cls.players_db, _provenance = rdb.build_players_db_from_capture()
        capture = json.loads(Path(rdb.CAPTURE_PATH).read_text(encoding="utf-8"))
        scoring = (capture.get("league_shape") or {}).get("scoring_settings")
        cls.league = next(arm["league"] for arm in db.league_matrix(scoring)
                          if arm["label"] == "HEAVY_IDP")
        cls.merger = dm.DataMerger()
        cls.merger.set_league_format(db.league_format_hint(cls.league))
        report = Path("BATTERY_REPORT.json")
        cls.picks = None
        if report.exists():
            data = json.loads(report.read_text(encoding="utf-8"))
            arm = next((a for a in data.get("results", [])
                        if a["label"] == "HEAVY_IDP"), None)
            if arm and arm.get("pick_sequence"):
                ids = [str(i) for i in range(1, arm["teams"] + 1)]
                order = []
                for round_index in range(arm["rounds"]):
                    order.extend(ids if round_index % 2 == 0 else list(reversed(ids)))
                cls.picks = [{"player_id": str(pid), "roster_id": order[i]}
                             for i, pid in enumerate(arm["pick_sequence"]) if i < len(order)]

    def setUp(self):
        if self.picks is None:
            self.skipTest("no HEAVY_IDP battery trajectory available to replay")

    def test_the_drop_population_is_not_empty(self):
        """Without this the rest of the class proves nothing."""
        dropped = 0
        for roster_id in {p["roster_id"] for p in self.picks}:
            unpriced = []
            dr._team_roster_players(self.picks, self.players_db, roster_id, self.merger,
                                    frozenset(), unpriced=unpriced)
            dropped += len(unpriced)
        self.assertGreater(dropped, 20,
                           "almost no rostered player is dropped on this trajectory, so the hole "
                           "this module is about has no population here")

    def _relabelled(self):
        """Every cell the stamp touches, with the state it was in before."""
        out = []
        for roster_id in sorted({p["roster_id"] for p in self.picks}):
            unpriced = []
            players = dr._team_roster_players(self.picks, self.players_db, roster_id,
                                              self.merger, frozenset(), unpriced=unpriced)
            if not unpriced:
                continue
            before = lo.depth_exposure(players, self.league["roster_positions"])
            after = lo.depth_exposure(players, self.league["roster_positions"],
                                      unpriced_eligibilities=unpriced)
            covered = set()
            for eligible in unpriced:
                covered |= set(eligible)
            for position in sorted(covered):
                cell = before.get(position)
                if cell is not None:
                    out.append((roster_id, position, cell, after[position]))
        return out

    def test_almost_every_relabelled_cell_was_ALREADY_withholding_its_number(self):
        """MY FIRST VERSION OF THIS ASSERTED *EVERY* CELL AND WAS WRONG, which is recorded rather
        than quietly widened: it passed at a mid-draft state and failed on the complete rosters,
        where two `measured` cells are relabelled. So the claim is the proportion, not the absolute
        -- this is a labelling repair that also removes a couple of over-credits, and if that ever
        stops being true the repair has become something else."""
        cells = self._relabelled()
        self.assertGreater(len(cells), 10, "vacuous: too few relabelled cells to support a claim")
        already_withheld = [c for c in cells
                            if c[2]["basis"] in (lo.EXPOSURE_NO_SURPLUS, lo.EXPOSURE_VACANT,
                                                 lo.EXPOSURE_NOT_APPLICABLE)]
        self.assertGreater(len(already_withheld), len(cells) * 0.75,
                           f"only {len(already_withheld)} of {len(cells)} relabelled cells were "
                           f"already withholding -- this has stopped being mainly a labelling "
                           f"repair and is now moving prices at scale")

    def test_the_cells_that_WERE_measured_carried_a_false_label_at_no_point(self):
        """The ones that move a price. Their previous label was correct as far as it went -- the
        solve did measure something -- and the number was a CEILING, because the dropped man would
        have covered the hole. Withdrawing it removes an over-credit, which is the intended
        direction; a test that let it stand would be blessing the over-credit."""
        for roster_id, position, before, after in self._relabelled():
            if before["basis"] != lo.EXPOSURE_MEASURED:
                continue
            self.assertEqual(after["basis"], lo.EXPOSURE_ROSTER_PARTIAL,
                             f"roster {roster_id} {position}")
            # And the board's gate is what withholds it -- pinned separately in
            # TheNumberIsNotSpentUnderItTests.

    def test_no_relabelled_cell_ends_up_in_a_state_that_still_claims_a_measurement(self):
        for roster_id, position, before, after in self._relabelled():
            if before["basis"] == lo.EXPOSURE_NOT_APPLICABLE:
                continue
            self.assertEqual(after["basis"], lo.EXPOSURE_ROSTER_PARTIAL,
                             f"roster {roster_id} {position} kept a basis that claims more than "
                             f"the solve can support")


if __name__ == "__main__":
    unittest.main()
