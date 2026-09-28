"""The assertion nothing made: `compute_draft_board`'s OWN ROW ORDER honours both backstops.

WHY THIS FILE EXISTS. `invariant_confirmation.py` applies three mutations that make the two
backstops advisory -- forcing `_feasible` to a constant, or substituting a constant column for
`_feasible` or `_unfieldable` in the sort. A dedicated audit pass applied each one and ran 482
tests over fifteen board- and backstop-touching modules: ALL THREE SURVIVED. The two "caught"
verdicts in the committed evidence were `test_invariant_confirmation_anchors.py` failing on its
own anchor text, which a mutation necessarily replaces -- the harness's self-test, not the engine.

Why the existing tests could not see it, stated so this file is not duplicated later:

  test_feasibility_backstop.py   calls `feasibility_first` directly and then does ITS OWN sort,
                                 so it measures the function, never the board's order.
  test_unfieldable_backstop.py   tests `pick_synthesis._board_order` on plain dicts.
  test_draft_room.py             98 tests, and zero references to `_feasible`,
                                 `fills_required_slot`, `_unfieldable` or `cannot_be_fielded`.

Nothing anywhere asserted on the row order that `sort_values` produces. That is what this does.

THE ORACLE, AND WHY THE MUTATIONS CANNOT REACH IT. `fills_required_slot` and `cannot_be_fielded`
are assigned from the TRUE backstop values (`_feasible == 0`, `_unfieldable == 1`) on the lines
ABOVE the sort, and travel on every row because narrow_candidates re-sorts every board it
receives (#155). All three mutations corrupt only the SORT KEYS. So the flags on the row remain
truthful while the order stops matching them, and comparing the two catches every mutation
without this file needing to know what any of them does.

NOT A SIGNATURE CHECK, AND NOT A STUB. A real capture, a real board, and a roster state chosen so
both backstops BIND -- 3 QB held against a one-QB roster puts every remaining QB over the
fieldable ceiling of 2, while 6 of 7 picks spent leaves fewer picks than unfilled named slots.
A fixture where a backstop is uniform makes every assertion about it vacuous and every mutation
of it inert, which is #245 and the reason the first two verdicts meant nothing. So the binding
itself is asserted first, in its own test, before anything is concluded from the order.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb

#: The harness's own constant, NEVER a hand-written path. The first version of this file spelled
#: the filename by hand, got it wrong, and every test in it SKIPPED while the module reported OK
#: -- which is `0.4` (assertion_floors cannot see a test that stops running) reproduced inside the
#: repair for `0.2`. A skipUnless over a literal path is a silent-skip waiting to happen.
CAPTURE = rdb.CAPTURE_PATH

#: One QB slot and no SUPER_FLEX, so `fieldable_ceiling` is {'QB': 2} -- measured, not assumed
#: (the test below asserts it). RB is flex-reachable and therefore EXEMPT from any ceiling, which
#: is why the harness's own 6-RB fixture leaves `cannot_be_fielded` uniformly False and cannot
#: judge the fieldability mutation at all. A dedicated position is required to make it bind.
ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class BoardOrderHonoursTheBackstops(unittest.TestCase):
    """Both boards are built ONCE: each is a real board build against the real capture."""

    @classmethod
    def setUpClass(cls):
        merger = dm.DataMerger()
        players_db, _ = rdb.build_players_db_from_capture()
        season = rdb.season_projections_from_capture()
        scoring = rdb.scoring_settings_from_capture()
        league = {"roster_positions": ROSTER, "total_rosters": 12, "settings": {"type": 2},
                  "scoring_settings": scoring, "draft_rounds": len(ROSTER)}
        merger.set_league_format(db.league_format_hint(league))    # never skipped: #204
        pool = dr.build_available_pool(
            merger, players_db, set(), dr.league_usable_positions(ROSTER),
            sleeper_projections=season, scoring_settings=scoring, pool_scope="all",
            sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        dr._derive_points_and_source(pool)
        held = ([str(x) for x in pool.loc[pool["position"] == "QB", "player_id"].head(3)]
                + [str(x) for x in pool.loc[pool["position"] == "RB", "player_id"].head(3)])
        picks = [{"pick_no": i + 1, "round": i + 1, "roster_id": "1", "player_id": pid}
                 for i, pid in enumerate(held)]
        cls.roster_positions = ROSTER
        # BOTH BRANCHES. compute_draft_board sorts in two places -- the balanced branch and the
        # upside-mode branch -- and each mutation is applied to both sites, deliberately: a
        # mutation that leaves one branch intact has not broken the invariant, because the other
        # branch goes on defending it. A test covering one branch would let half a mutation pass.
        cls.boards = {
            "balanced": dr.compute_draft_board(
                merger, players_db, picks, my_roster_id="1", league=league,
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM),
            "upside": dr.compute_draft_board(
                merger, players_db, picks, my_roster_id="1", league=league, mode="upside",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM),
        }

    # -- non-vacuity first, because an assertion over a uniform column proves nothing (#245) --

    def test_the_ceiling_that_makes_the_second_backstop_bind_is_what_we_think(self):
        self.assertEqual(dr.fieldable_ceiling(ROSTER), {"QB": 2},
                         "the fixture's binding argument rests on this ceiling")

    def test_both_backstops_actually_bind_on_this_fixture(self):
        for mode, board in self.boards.items():
            with self.subTest(mode):
                self.assertTrue(board, "no board was built")
                for flag in ("fills_required_slot", "cannot_be_fielded"):
                    n_true = sum(1 for row in board if row.get(flag))
                    self.assertTrue(
                        0 < n_true < len(board),
                        f"{flag} is uniform ({n_true} of {len(board)}) on this fixture, so every "
                        f"assertion below it is vacuous and any mutation of it reads INERT. "
                        f"Re-derive the roster state; do not weaken the assertions.")

    # -- the order itself --

    def _assert_partitioned(self, rows, flag, first_value, label):
        """Every row whose `flag` is `first_value` must precede every row where it is not.

        Reported as the first violating index with both rows' scores, because "the order is
        wrong" is not actionable and "row 12 (promoted, score 41.2) sits below row 11 (demoted,
        score 195.2)" names the defect.
        """
        seen_other = None
        for i, row in enumerate(rows):
            if bool(row.get(flag)) is not first_value:
                if seen_other is None:
                    seen_other = i
            elif seen_other is not None:
                self.fail(
                    f"{label}: row {i} has {flag}={first_value!r} but sits BELOW row "
                    f"{seen_other}, which does not. The backstop is no longer reaching the "
                    f"order. row {i}: {rows[i].get('name')!r} score "
                    f"{rows[i].get('final_score')}; row {seen_other}: "
                    f"{rows[seen_other].get('name')!r} score {rows[seen_other].get('final_score')}")

    def test_feasibility_partitions_the_whole_board(self):
        # `_feasible` is the FIRST sort key, ascending, and fills_required_slot is (_feasible == 0)
        # -- so every row that fills a required slot precedes every row that does not, across the
        # entire board rather than within any group.
        for mode, board in self.boards.items():
            with self.subTest(mode):
                self._assert_partitioned(board, "fills_required_slot", True, f"{mode} board")

    def test_fieldability_partitions_within_each_feasibility_group(self):
        # `_unfieldable` is the SECOND key, so it orders only inside a feasibility group. Asserted
        # per group for that reason: asserting it board-wide would be a stricter claim than the
        # sort makes, and would fail correctly-ordered boards.
        for mode, board in self.boards.items():
            for fills in (True, False):
                group = [r for r in board if bool(r.get("fills_required_slot")) is fills]
                with self.subTest(mode=mode, fills_required_slot=fills):
                    self._assert_partitioned(group, "cannot_be_fielded", False,
                                             f"{mode} board, fills_required_slot={fills}")

    def test_the_backstops_outrank_value_rather_than_merely_agreeing_with_it(self):
        """The partition tests would also pass if the backstops happened to agree with the score
        order. This is what makes them evidence: a DEMOTED row outscores a PROMOTED one, so the
        order above can only be produced by the backstop and not by `final_score`."""
        for mode, board in self.boards.items():
            with self.subTest(mode):
                promoted = [r["final_score"] for r in board
                            if r.get("fills_required_slot") and r.get("final_score") is not None]
                demoted = [r["final_score"] for r in board
                           if not r.get("fills_required_slot") and r.get("final_score") is not None]
                self.assertTrue(promoted and demoted, "one side of the partition is empty")
                self.assertGreater(
                    max(demoted), min(promoted),
                    "no demoted row outscores any promoted row, so this board cannot distinguish "
                    "the backstop's ordering from plain score ordering -- the fixture proves "
                    "nothing even though it passes")
