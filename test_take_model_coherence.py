"""A CHARACTERIZATION of a known defect, not a statement of desired behaviour.

`draft_strategy._take_probability` maps a rank on an opponent's board to "how likely is that team
to take this player". A team takes exactly ONE player, so summing that map across a whole board
asks how many players the model thinks the team drafts. On a real 256-row board the answer is
6.23 (evidence/take_model/README.md); on Fourth and Forever's own 481-row board it is 10.73
(evidence/survival_mechanism/collapse_decomposition.json). Both are real boards -- the total is
a FUNCTION OF THE POOL, not a fixed miscalibration, which is why no single figure is under test.

#206 HAS A SECOND HALF, and it now has evidence too. The mass defect above is one cause of the
0.00; the other is that every opponent board is built by the SAME valuation, so the engine's own
#1 is rank 1 on all of them at once and survival multiplies 0.55 by itself. The last class in
this file pins that half through `estimate_survival` itself.

THE TWO CAUSES ARE NOT TWO ROUTES TO ONE ANSWER, and the last class is written to stop that
reading. At the measured turn -- 22 intervening picks, 11 distinct rivals each picking twice --
normalising the mass lifts survival from 2.3e-8 to 0.314 in one step. Agreement cannot be moved
to the same place from either side: with every rival disagreeing it is 0.641, and a SINGLE rival
holding the top opinion already drops it to 0.135, because that opinion applies to two picks.
Agreement is superlinear (three agreeing rivals force 0.006), so one shared valuation supplies
far more of it than the collapse requires.

WHEN THIS FILE GOES RED IT IS PROBABLY GOOD NEWS. It pins the defect so the defect cannot change
size quietly; a coherent replacement SHOULD fail it, and the repair is to rewrite these
assertions deliberately, with the modelling decision recorded. What must never happen is the
number drifting while both symptoms it causes (#206's 0.00, and survival_probability's d=1 at
exhaustion) stay in the register as separate mysteries.

NO BOARD IS BUILT HERE. The property is arithmetic over two module constants and a row count, so
the suite pays nothing for it. The 256 comes from the recorded measurement and is used only as a
realistic size, never as a value under test -- every assertion below holds for any large board.
"""

from __future__ import annotations

import unittest

import draft_strategy as ds

#: Rows on one real opponent board, measured once (evidence/take_model/README.md). Used as a
#: realistic magnitude; every assertion is written to hold for any board this size or larger.
MEASURED_BOARD_ROWS = 256


def expected_picks(rows: int) -> float:
    """What the model says about how many players ONE team drafts."""
    return sum(ds._take_probability(rank, False) for rank in range(1, rows + 1))


class ATeamDraftsOnePlayer(unittest.TestCase):
    def test_the_model_says_a_team_drafts_far_more_than_one(self):
        total = expected_picks(MEASURED_BOARD_ROWS)
        self.assertAlmostEqual(total, 6.23, places=2)
        self.assertGreater(total, 1.0, "if this passes, the model became coherent -- rewrite this file")

    def test_the_incoherence_grows_with_the_board_and_has_no_ceiling(self):
        """Not a fixed miscalibration: a deeper pool makes it strictly worse, because the floor
        is applied per row with no domain limit."""
        small, large = expected_picks(50), expected_picks(500)
        self.assertLess(small, large)
        self.assertAlmostEqual(large - small, ds.RANK_TAKE_PROBABILITY_FLOOR * 450, places=6)


class TheFloorIsTheDefectNotTheTable(unittest.TestCase):
    """The five-rank table is a documented, deliberately-uncertain prior and behaves like one.
    Blaming it would send a repair to the wrong place."""

    def test_the_table_alone_is_nearly_coherent(self):
        table = sum(ds.RANK_TAKE_PROBABILITY.values())
        self.assertAlmostEqual(table, 1.21, places=2)
        self.assertLess(table, 1.5)

    def test_the_floor_carries_almost_all_of_the_excess(self):
        total = expected_picks(MEASURED_BOARD_ROWS)
        floor_part = ds.RANK_TAKE_PROBABILITY_FLOOR * (MEASURED_BOARD_ROWS
                                                       - len(ds.RANK_TAKE_PROBABILITY))
        self.assertGreater(floor_part / (total - 1.0), 0.9)

    def test_rank_6_and_rank_251_are_assigned_the_same_probability(self):
        """The mechanism in one line: `.get(rank, FLOOR)` has no domain limit."""
        self.assertEqual(ds._take_probability(6, False), ds._take_probability(251, False))
        self.assertEqual(ds._take_probability(6, False), ds.RANK_TAKE_PROBABILITY_FLOOR)


class WhatTheFloorCanAndCannotExplain(unittest.TestCase):
    """Guards the scope statement in the evidence record, so the finding cannot be overclaimed
    later as the explanation of #206."""

    @staticmethod
    def _survival(p: float, opponents: int) -> float:
        return (1 - p) ** opponents

    def test_a_floored_player_does_NOT_read_as_zero_even_over_sixty_picks(self):
        """If this ever failed, the floor WOULD explain #206 and the evidence record's scope
        statement would be wrong."""
        survival = self._survival(ds.RANK_TAKE_PROBABILITY_FLOOR, 60)
        self.assertGreater(survival, 0.25)
        self.assertGreater(round(survival, 3), 0.0)

    def test_only_a_high_TABLE_rank_can_produce_a_reported_zero(self):
        survival = self._survival(ds.RANK_TAKE_PROBABILITY[1], 11)
        self.assertEqual(round(survival, 3), 0.0)

    def test_the_floor_gives_every_deep_bench_candidate_the_same_survival(self):
        """The d=1 collapse recorded in POST_AUDIT_PLAN, as arithmetic: past the table, rank
        carries no information at all, so no two candidates can be told apart."""
        deep = [ds._take_probability(r, False) for r in range(6, 60)]
        self.assertEqual(len(set(deep)), 1)


#: Other priced rows on each synthetic rival board. Chosen to sit inside the real measured
#: range (481 priced rows at the opening board, draining to 361 by pick 120 --
#: evidence/take_mass/mass_per_opponent.json), not tuned to produce any particular survival.
POOL = 400


def _boards(rivals, target: str, agreeing: int, rank: int = 1) -> dict:
    """One board per DISTINCT intervening roster, shaped the way `_build_opponent_boards`
    returns them. The first `agreeing` of them rank `target` at `rank`; the rest bury him past
    the table's last key, where `_take_probability` hands out only the floor.

    WHY PER ROSTER AND NOT PER PICK, which is the fixture error this signature exists to stop.
    A snake turn is 22 intervening PICKS but only 11 distinct rivals, each picking twice, and
    `estimate_survival` consults one board per pick -- so a rival's opinion is applied TWICE and
    agreement cannot be varied one pick at a time. Keying this fixture by pick would build
    boards under ids nobody looks up and quietly answer a different question.

    THE BOARD NOW CARRIES A REALISTIC POOL, AND THAT IS A CONSEQUENCE OF THE #206 REPAIR rather
    than a cosmetic change. This fixture used to build a board holding exactly ONE row -- the
    target -- on the stated premise that "the property under test is what estimate_survival does
    with a set of ranks". That premise held only while take probability was read off the rank
    alone. Normalising the take mass makes it a DISTRIBUTION over the board, so board SIZE is
    now load-bearing: on a one-row board the rival's only option is the target, so the repaired
    model correctly says they take him with probability 1.0, and every number below would be
    about a board nobody ever faces. A rival with three players left really is likelier to take
    your man than one with four hundred, and the old model could not express that at all.

    `POOL` is the count of OTHER priced rows on each rival's board. Ranks past the table's last
    key carry the floor, which is what the real deep pool contributes (measured at 476 priced
    tail rows plus 638 unpriced on the real board -- evidence/take_mass/).

    That these ranks are what the real boards produce is measured separately and not assumed
    here (evidence/survival_mechanism/rank_agreement.json)."""
    deep = max(ds.RANK_TAKE_PROBABILITY) + 500
    boards = {}
    for i, r in enumerate(rivals):
        rank_by_id = {target: rank if i < agreeing else deep}
        by_id = {target: {}}
        for k in range(POOL):
            other = f"filler_{k}"
            rank_by_id[other] = deep + 1 + k
            by_id[other] = {}
        boards[str(r)] = {"by_id": by_id, "rank_by_id": rank_by_id, "unpriced_ids": set()}
    return boards


class EveryRivalHoldsTheSameOpinion(unittest.TestCase):
    """#206's second half: the boards do not disagree, so survival has nothing to multiply but
    the same number. LIKE THE REST OF THIS FILE, A CHARACTERIZATION -- if these go red because
    rival boards started to differ, that is the repair landing, and the assertions get rewritten
    against the new model rather than restored."""

    TARGET = "9221"          # the engine's own #1 in the measured run; any id behaves the same
    TEAMS = 12

    def setUp(self):
        self.order = ds.generate_pick_order([str(i) for i in range(1, self.TEAMS + 1)], 2)
        nxt = ds.find_next_pick_index(self.order, "1", 0)
        self.picks = ds.intervening_roster_ids(self.order, 0, nxt)
        self.rivals = sorted(set(self.picks), key=int)

    def _survival(self, agreeing: int, rank: int = 1) -> float:
        boards = _boards(self.rivals, self.TARGET, agreeing, rank)
        return ds.estimate_survival([], {}, self.order, 0, "1", self.TARGET,
                                    boards, league=None)["survival_probability"]

    def test_the_turn_really_is_the_long_one_and_each_rival_is_consulted_twice(self):
        """Guards the fixture itself. If this shape ever changes, every number below is about a
        different turn and the ones that look unchanged would be the dangerous ones."""
        self.assertEqual(len(self.picks), 22)
        self.assertEqual(len(self.rivals), 11)
        self.assertTrue(all(self.picks.count(r) == 2 for r in self.rivals))

    def test_one_distinct_take_probability_across_every_intervening_pick(self):
        """The structural half still holds after the repair: one shared valuation still means
        one number, applied 22 times. What CHANGED is the number -- it is no longer the raw
        table key, because the key is now a weight in a distribution rather than a probability
        on its own."""
        boards = _boards(self.rivals, self.TARGET, len(self.rivals))
        rows = ds.estimate_survival([], {}, self.order, 0, "1", self.TARGET,
                                    boards, league=None)["risk_by_team"]
        self.assertEqual(len(rows), 22)
        distinct = {r["take_probability"] for r in rows}
        self.assertEqual(len(distinct), 1, "agreement should still collapse to one number")
        only = distinct.pop()
        self.assertAlmostEqual(only, 0.064, places=3)
        self.assertLess(only, ds.RANK_TAKE_PROBABILITY[1],
                        "the raw table key is a weight now, not a probability")

    def test_the_reported_zero_is_GONE(self):
        """INVERTED ON REPAIR (#206, 2026-09-16). This test used to assert
        `self._survival(len(self.rivals)) == 0.0` and then prove the zero was real rather than
        rounded -- 2.3e-8, seven orders below the 0.0005 that would round there. That WAS the
        defect: an impossibility the model had no way to express, for a player the draft then
        let survive.

        Unanimous agreement across all 11 rivals over 22 intervening picks now leaves **0.232**.
        The player survives, which is what the real draft did. Kept as an inversion rather than
        deleted, because the number it used to assert is the record of what was wrong."""
        survival = self._survival(len(self.rivals))
        self.assertGreater(survival, 0.2)
        self.assertAlmostEqual(survival, 0.232, places=3)
        self.assertGreater(survival, 0.0005,
                           "above the rounding floor -- a low probability, not an impossibility")

    def test_agreement_still_costs_but_no_longer_annihilates(self):
        """INVERTED ON REPAIR. The old numbers were 0.641 / 0.135 / 0.029 / 0.006 -- one
        agreeing rival cost an order of magnitude and three effectively ended it. Agreement is
        still monotone and still expensive, but it now DEGRADES instead of collapsing: no amount
        of agreement reachable on this turn drives survival below 0.2.

        The mechanism of the old collapse is worth keeping in view: a rival's opinion applies to
        TWO picks, so agreement compounded superlinearly against a per-pick probability that was
        already ~9x too large."""
        self.assertAlmostEqual(self._survival(0), 0.947, places=3)
        self.assertAlmostEqual(self._survival(1), 0.833, places=3)
        self.assertAlmostEqual(self._survival(2), 0.733, places=3)
        self.assertAlmostEqual(self._survival(3), 0.645, places=3)
        reachable = [self._survival(a) for a in range(len(self.rivals) + 1)]
        self.assertEqual(reachable, sorted(reachable, reverse=True), "must stay monotone")
        self.assertGreater(min(reachable), 0.2)

    def test_the_repaired_rate_lands_near_the_rate_real_drafters_showed(self):
        """THE POINT OF THE WHOLE REPAIR, and the reason it satisfies #56.

        Nothing here was fitted to a league. The constraint is arithmetic -- one team makes one
        pick, so their take probabilities are mutually exclusive and must sum to <= 1.0 over
        their board. Applying only that puts the rank-1 take probability at **6.4%** on this
        fixture, against **3.0%** measured from 270 real human picks (evidence/take_model/) and
        **55%** in the unrepaired model.

        Same order of magnitude as reality, from a constraint rather than a calibration. My own
        recommended head-only repair, which WAS shaped toward the measurement, was off by 15x
        and is withdrawn (30th). That contrast is the whole argument for deriving over tuning,
        so it is asserted rather than left in prose."""
        boards = _boards(self.rivals, self.TARGET, len(self.rivals))
        rows = ds.estimate_survival([], {}, self.order, 0, "1", self.TARGET,
                                    boards, league=None)["risk_by_team"]
        p = rows[0]["take_probability"]
        self.assertLess(p, 0.15, "nowhere near the unrepaired 0.55")
        self.assertGreater(p, 0.01, "and not driven to nothing either")
        self.assertLess(abs(p - 0.030), 0.05, "within a few points of the measured rate")

    def test_a_ranked_row_deep_in_the_table_is_safer_than_the_top_of_it(self):
        """Rank 5 is inside the table and agreed on by everyone, and it stays far safer than
        rank 1 -- 0.848 against 0.232. The ORDERING property the old test asserted survives the
        repair; only the magnitudes moved."""
        deepest = max(ds.RANK_TAKE_PROBABILITY)
        deep_survival = self._survival(len(self.rivals), rank=deepest)
        self.assertAlmostEqual(deep_survival, 0.848, places=3)
        self.assertGreater(deep_survival, self._survival(len(self.rivals), rank=1))

    def test_a_positional_run_REDISTRIBUTES_mass_it_does_not_manufacture_it(self):
        """THE GAP MY OWN MUTATION PASS FOUND. Two mutations survived the first round -- removing
        the run boost from the weight entirely, and keying the per-board cache on "" so a run
        query gets the no-run answer. Both survived because every other test here runs with
        `league=None` and no picks, so no run is ever detected and the boosted branch was
        unexercised. A repair whose boost path no test reaches is a repair half-checked.

        THE PROPERTY, and it is the reason the boost is applied to the WEIGHT rather than to the
        finished probability: a run means rivals are likelier to take THAT position and
        correspondingly less likely to take anything else. So the run player's share rises, every
        other share falls, and the total is still exactly 1.0. Boosting an already-normalised
        probability would instead re-break the mass the normalisation just imposed."""
        target, other = self.TARGET, "filler_0"
        board = _boards(self.rivals, target, 1)[self.rivals[0]]
        board["by_id"][target] = {"position": "WR"}

        plain = ds.board_take_mass(board)
        boosted = ds.board_take_mass(board, "WR")
        self.assertGreater(boosted["total_weight"], plain["total_weight"],
                           "the run raises the running position's WEIGHT")

        def share(mass, run):
            return ds._take_probability(board["rank_by_id"][target], run, mass["total_weight"])

        self.assertGreater(share(boosted, True), share(plain, False),
                           "a run makes the running position's player likelier to be taken")
        self.assertLess(
            ds._take_probability(board["rank_by_id"][other], False, boosted["total_weight"]),
            ds._take_probability(board["rank_by_id"][other], False, plain["total_weight"]),
            "and correspondingly makes everyone else LESS likely -- redistribution, not inflation")

        # Mass still exactly 1.0 under the run, which is what "redistributes" has to mean.
        total = 0.0
        for pid, rank in board["rank_by_id"].items():
            is_run = board["by_id"].get(pid, {}).get("position") == "WR"
            total += ds._take_probability(rank, is_run, boosted["total_weight"])
        self.assertAlmostEqual(total, 1.0, places=9)

    def test_the_per_board_cache_does_not_serve_one_run_positions_answer_to_another(self):
        """The other survivor. The normaliser is memoised ON the board dict for speed, so a cache
        keyed on anything less than the run position hands a WR-run answer to a QB-run query --
        silently, and only under a run, which is exactly when the number matters most."""
        board = _boards(self.rivals, self.TARGET, 1)[self.rivals[0]]
        board["by_id"][self.TARGET] = {"position": "WR"}
        no_run = ds._board_take_mass_cached(board, None)["total_weight"]
        wr_run = ds._board_take_mass_cached(board, "WR")["total_weight"]
        qb_run = ds._board_take_mass_cached(board, "QB")["total_weight"]
        self.assertNotAlmostEqual(wr_run, no_run, msg="a WR run must change the WR board's mass")
        self.assertAlmostEqual(qb_run, no_run, places=9,
                               msg="a QB run must not, on a board whose only positioned row is WR")
        # And re-asking must still give each its own answer, not whichever was cached first.
        self.assertAlmostEqual(ds._board_take_mass_cached(board, "WR")["total_weight"], wr_run)
        self.assertAlmostEqual(ds._board_take_mass_cached(board, None)["total_weight"], no_run)

    def test_the_mass_sums_to_one_which_is_the_invariant_the_repair_exists_for(self):
        """THE CONSTRAINT ITSELF, asserted directly rather than inferred from survival numbers.

        Measured before repair on a real board: 23.49 (evidence/take_mass/). A team that makes
        one pick cannot take 23 players."""
        board = _boards(self.rivals, self.TARGET, 1)[self.rivals[0]]
        mass = ds.board_take_mass(board)
        total_p = sum(
            ds._take_probability(rank, False, mass["total_weight"])
            for rank in board["rank_by_id"].values()
        )
        self.assertAlmostEqual(total_p, 1.0, places=9)
        self.assertGreater(mass["priced_rows"], 100, "a realistic board, not a degenerate one")


if __name__ == "__main__":
    unittest.main()
