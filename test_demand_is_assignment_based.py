"""MANDATE 2.6 / `#172` (the counting half, OWNER-RULED): starter demand is SOLVED, not subtracted.

`team_filled_by_position` counted every pick under its PRIMARY LABEL and fed both consumers of "what
has this team got": league-wide `remaining_starter_demand` -> `replacement_levels` -> every price,
and `need_bonus` on my own roster. A DL/LB dual paid down DL demand and left LB demand standing at
its full height, so LBs were priced as though more LB slots needed filling than did — measured on
`HEAVY_IDP`, 20.0 where 13.0 were genuinely open after round five.

NEITHER AVAILABLE READING WAS CORRECT, which is why this went to the owner rather than being chosen
here. By label, demand at one of his positions is overstated. By eligibility, he pays down BOTH,
which claims one player fills two slots. The ruling is BY ASSIGNMENT: solve which slot he occupies.

That makes demand a solved quantity, and `remaining_starter_demand`'s docstring rested on being
"EXACT and BOUNDED ... carries no prior, no estimate", which it says is "what make[s] it usable as
the domain test for a valuation anchor". These tests are that claim, re-established over the new
definition rather than inherited: the bound, the zero, the order-invariance, and the monotonicity —
including the one part of it that is no longer a proof (see the last class).

Evidence: `evidence/multi_eligible_counting/`.
"""
from __future__ import annotations

import itertools
import random
import unittest

import draft_room as dr
import lineup_optimizer as lo
import player_universe as pu


IDP_ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "DL", "DL", "LB", "LB", "DB", "IDP_FLEX",
              "BN", "BN", "BN"]


def _db(rows: dict[str, list[str]]) -> dict[str, dict]:
    """A players_db whose rows carry ONLY what the counting reads: a primary label that DISAGREES
    with the fantasy list wherever that matters, so a test cannot pass by accident on the label."""
    return {pid: {"player_id": pid, "full_name": f"P{pid}", "position": listed[0],
                  "fantasy_positions": listed} for pid, listed in rows.items()}


def _picks(assignment: list[tuple[str, str]]) -> list[dict]:
    return [{"pick_no": i + 1, "roster_id": roster, "player_id": pid}
            for i, (roster, pid) in enumerate(assignment)]


class TheDualPaysDownExactlyOneSlot(unittest.TestCase):
    """The whole ruling, at its smallest: one player, two positions, one slot."""

    def setUp(self):
        self.roster_positions = ["DL", "LB", "BN"]
        self.db = _db({"dual": ["DL", "LB"], "dual2": ["DL", "LB"],
                       "dl": ["DL"], "lb": ["LB"]})

    def _demand(self, picks):
        return dr.remaining_starter_demand(self.roster_positions, 1, picks, self.db)

    def test_an_empty_league_needs_both_slots(self):
        demand = self._demand([])
        self.assertEqual(demand["DL"], 1.0)
        self.assertEqual(demand["LB"], 1.0)

    def test_a_dual_pays_down_one_slot_not_two(self):
        demand = self._demand(_picks([("1", "dual")]))
        self.assertEqual(demand["DL"] + demand["LB"], 1.0,
                         "one player cannot fill two starting slots")

    def test_and_not_zero_slots(self):
        """The label reading's failure, stated as the thing that must not happen: by label he is a
        DL, so LB demand would stand at 1.0 with DL demand at 0.0 -- total 1.0 as well. What
        separates the two readings is a SECOND dual, below."""
        demand = self._demand(_picks([("1", "dual"), ("1", "dual2")]))
        self.assertEqual(demand["DL"] + demand["LB"], 0.0,
                         "two duals cover both slots; by primary label they pay down DL twice "
                         "and leave the LB slot reading as unfilled")


class TheLabelReadingIsWhatChanged(unittest.TestCase):
    """The census survives (it is still a real question), so the difference is DIRECTLY measurable
    rather than argued: same picks, both formulas, one number apart."""

    def setUp(self):
        self.roster_positions = ["DL", "LB", "BN"]
        self.db = _db({"a": ["DL", "LB"], "b": ["DL", "LB"]})
        self.picks = _picks([("1", "a"), ("1", "b")])

    def test_the_census_still_reads_them_both_as_DL(self):
        census = dr.team_filled_by_position(self.picks, self.db)
        self.assertEqual(census["1"], {"DL": 2},
                         "the primary label is what the census reads -- that is the defect, pinned")

    def test_the_assignment_reads_one_of_each(self):
        solved = dr.team_slots_filled(self.picks, self.db, self.roster_positions)
        self.assertEqual(solved["1"], {"DL": 1, "LB": 1})

    def test_and_so_the_LB_slot_stops_reading_as_unfilled(self):
        demand = dr.remaining_starter_demand(self.roster_positions, 1, self.picks, self.db)
        self.assertEqual(demand["LB"], 0.0)
        self.assertEqual(demand["DL"], 0.0)


class TheStatedPropertiesOfTheAnchorsDomainTest(unittest.TestCase):
    """`remaining_starter_demand` is the domain test `replacement_levels` rests on. Every property
    its docstring claims, re-established over the SOLVED definition."""

    def setUp(self):
        self.db = _db({
            "qb": ["QB"], "rb1": ["RB"], "rb2": ["RB"], "wr1": ["WR"], "wr2": ["WR"], "wr3": ["WR"],
            "te": ["TE"], "dl": ["DL"], "lb": ["LB"], "db": ["DB"],
            "dual_dl_lb": ["DL", "LB"], "dual_db_lb": ["DB", "LB"], "wr_rb": ["WR", "RB"],
        })
        self.everyone = list(self.db)

    def test_it_is_bounded_by_the_leagues_own_capacity(self):
        capacity = dr.starter_slot_counts(IDP_ROSTER)
        for held in range(0, len(self.everyone) + 1):
            picks = _picks([("1", pid) for pid in self.everyone[:held]])
            demand = dr.remaining_starter_demand(IDP_ROSTER, 3, picks, self.db)
            for position, value in demand.items():
                self.assertGreaterEqual(value, 0.0, f"{position} demand went negative at {held}")
                self.assertLessEqual(round(value, 6), round(3 * capacity[position], 6),
                                     f"{position} demand exceeded three teams' capacity")

    def test_it_reaches_exactly_zero_when_every_slot_is_covered(self):
        roster_positions = ["QB", "RB", "WR", "TE", "BN"]
        filled = _picks([(team, pid) for team in ("1", "2")
                         for pid in ("qb", "rb1", "wr1", "te")])
        # Two rosters, both complete -- ONE pick each for every slot, no flex to apportion.
        demand = dr.remaining_starter_demand(roster_positions, 2, filled, self.db)
        self.assertEqual(sum(demand.values()), 0.0, demand)

    def test_it_does_not_depend_on_the_order_the_picks_arrived_in(self):
        picks = _picks([("1", "dual_dl_lb"), ("2", "dl"), ("1", "lb"), ("2", "dual_db_lb"),
                        ("1", "wr_rb"), ("2", "wr1"), ("1", "te"), ("2", "qb")])
        baseline = dr.remaining_starter_demand(IDP_ROSTER, 2, picks, self.db)
        shuffler = random.Random(20260928)
        for _ in range(12):
            reordered = picks[:]
            shuffler.shuffle(reordered)
            self.assertEqual(dr.remaining_starter_demand(IDP_ROSTER, 2, reordered, self.db),
                             baseline, "demand read differently from the same SET of picks")

    def test_total_demand_never_rises_as_picks_accumulate(self):
        """The monotonicity that is still a proof: a maximum matching cannot shrink when a player is
        added, so total covered slots never falls and total demand never rises."""
        previous = None
        for held in range(0, len(self.everyone) + 1):
            picks = _picks([("1", pid) for pid in self.everyone[:held]])
            total = round(sum(dr.remaining_starter_demand(IDP_ROSTER, 2, picks, self.db).values()), 6)
            if previous is not None:
                self.assertLessEqual(total, previous, f"total demand ROSE at {held} picks")
            previous = total

    def test_a_foreign_roster_universe_is_still_refused(self):
        picks = _picks([("1", "qb"), ("2", "rb1"), ("3", "wr1")])
        with self.assertRaises(ValueError):
            dr.remaining_starter_demand(IDP_ROSTER, 2, picks, self.db)


class WhatTheAssignmentDoesAndDoesNotSettle(unittest.TestCase):
    """`slot_coverage`'s three-part objective, and the one part of it that is a CONVENTION."""

    def setUp(self):
        self.slots = lo.slots_from_roster_positions(IDP_ROSTER)

    def _fill(self, eligibilities, slots=None):
        players = [{"id": f"p{i}", "eligible": set(e)} for i, e in enumerate(eligibilities)]
        return lo.slot_coverage(players, slots if slots is not None else self.slots)["filled_labels"]

    def test_a_dedicated_slot_is_filled_before_a_flex_slot_that_would_take_him(self):
        self.assertEqual(self._fill([{"WR"}]), {"WR": 1},
                         "the only WR went to FLEX, leaving a dedicated slot need_bonus weighs 4:1")

    def test_flex_takes_the_overflow_once_the_dedicated_slots_are_full(self):
        self.assertEqual(self._fill([{"WR"}, {"WR"}, {"WR"}]), {"WR": 2, "FLEX": 1})

    def test_the_narrower_flex_slot_is_filled_first(self):
        slots = lo.slots_from_roster_positions(["SUPER_FLEX", "FLEX", "BN"])
        self.assertEqual(self._fill([{"RB"}], slots), {"FLEX": 1},
                         "FLEX accepts three positions and SUPER_FLEX four; the narrower goes first")

    def test_coverage_is_never_traded_for_a_preferred_arrangement(self):
        """The preferences only decide AMONG assignments covering the same number of slots -- the
        one thing a weighted solve can get wrong. Five IDPs over three dedicated IDP slots plus an
        IDP_FLEX must cover four slots, whatever the preference order would rather do."""
        filled = self._fill([{"DL"}, {"DL"}, {"LB"}, {"LB"}, {"DB"}, {"DB", "LB"}])
        self.assertEqual(sum(filled.values()), 6,
                         f"the roster can cover six IDP slots; it covered {filled}")

    def test_a_player_eligible_nowhere_this_league_starts_is_benched_not_forced(self):
        result = lo.slot_coverage([{"id": "ol", "eligible": {"OL"}}], self.slots)
        self.assertEqual(result["filled_labels"], {})
        self.assertEqual(result["benched"], ["ol"])

    def test_the_declaration_ORDER_is_the_tie_break_and_it_is_a_convention(self):
        """The residual tie the objective cannot settle on merit: one dual, two equally restrictive
        slots, nobody else for either. Which position he is credited to is ARBITRARY, and the
        league's own roster_positions order is the answer -- stable and auditable, not correct.
        Pinned so that a change of tie-break is a decision someone took, not a drift."""
        self.assertEqual(lo.slot_coverage([{"id": "d", "eligible": {"DL", "LB"}}],
                                          lo.slots_from_roster_positions(["DL", "LB", "BN"])
                                          )["filled_labels"], {"DL": 1})
        self.assertEqual(lo.slot_coverage([{"id": "d", "eligible": {"DL", "LB"}}],
                                          lo.slots_from_roster_positions(["LB", "DL", "BN"])
                                          )["filled_labels"], {"LB": 1})

    def test_it_is_a_function_of_the_SET_of_players(self):
        eligibilities = [{"DL", "LB"}, {"DB", "LB"}, {"WR", "RB"}, {"WR"}, {"QB"}]
        players = [{"id": f"p{i}", "eligible": set(e)} for i, e in enumerate(eligibilities)]
        baseline = lo.slot_coverage(players, self.slots)["filled_labels"]
        for permutation in itertools.islice(itertools.permutations(players), 24):
            self.assertEqual(lo.slot_coverage(list(permutation), self.slots)["filled_labels"],
                             baseline)


class PerPositionMonotonicityIsTESTEDNotPROVEN(unittest.TestCase):
    """THE ONE PROPERTY THIS REPAIR CANNOT HAND BACK AS A PROOF.

    The subtraction it replaced made per-position monotonicity trivial: demand at a position fell by
    one whenever a pick landed there and could never rise. A solved assignment has no such argument
    available. Adding a player can RE-ROUTE a dual-eligible one, and in general matroid terms a
    weighted-greedy basis need not contain the previous one, so a position's demand rising while the
    total falls is not obviously impossible.

    So it is searched for, exhaustively over a bounded space, rather than asserted. The space is
    every multiset of up to three eligibility shapes from a ten-shape vocabulary that includes the
    real IDP duals, each extended by every one of the ten -- and per-label fill never once decreased.
    That is evidence, not a proof, and it is recorded as evidence: if a counterexample exists it is
    outside this space, and finding one is a change to what `remaining_starter_demand` may claim.
    """

    SHAPES = [{"WR"}, {"RB"}, {"TE"}, {"DL"}, {"LB"}, {"DB"},
              {"DL", "LB"}, {"DB", "LB"}, {"WR", "RB"}, {"RB", "TE"}]

    def test_no_slot_label_ever_loses_its_occupant_when_a_player_is_added(self):
        slots = lo.slots_from_roster_positions(["WR", "RB", "FLEX", "DL", "LB", "IDP_FLEX"])

        def filled(shapes):
            return lo.slot_coverage(
                [{"id": f"p{i}", "eligible": set(s)} for i, s in enumerate(shapes)], slots,
            )["filled_labels"]

        checked = 0
        for size in range(0, 4):
            for combination in itertools.combinations_with_replacement(range(len(self.SHAPES)), size):
                before = filled([self.SHAPES[i] for i in combination])
                for added in range(len(self.SHAPES)):
                    after = filled([self.SHAPES[i] for i in combination] + [self.SHAPES[added]])
                    checked += 1
                    for label, occupied_before in before.items():
                        self.assertGreaterEqual(
                            after.get(label, 0), occupied_before,
                            f"{label} lost an occupant: {combination} + {self.SHAPES[added]}")
        self.assertGreater(checked, 2000, "the search space shrank; it is the evidence here")


class BothConsumersReadTheOneAssignment(unittest.TestCase):
    """`need_bonus` and league-wide demand were one census apart, and are now one assignment apart.
    The identity the board's arithmetic relies on: my unfilled share at a position, minus its
    dedicated part, IS the flex part -- so `need_bonus` needs no separate `flex_already_used` term."""

    def setUp(self):
        self.db = _db({"wr1": ["WR"], "wr2": ["WR"], "wr3": ["WR"], "dual": ["DL", "LB"]})

    def test_my_row_is_the_leagues_own_term_read_for_one_team(self):
        picks = _picks([("1", "wr1"), ("1", "wr2"), ("2", "wr3")])
        per_team = dr.team_slots_filled(picks, self.db, IDP_ROSTER)
        mine = dr._team_starters_filled(picks, self.db, "1", IDP_ROSTER)
        self.assertEqual(mine, per_team["1"])
        one_team = dr.unfilled_slot_share(IDP_ROSTER, per_team["1"])
        two_teams = dr.remaining_starter_demand(IDP_ROSTER, 2, picks, self.db)
        self.assertAlmostEqual(
            two_teams["WR"],
            one_team["WR"] + dr.unfilled_slot_share(IDP_ROSTER, per_team["2"])["WR"], places=6)

    def test_the_dedicated_part_of_my_share_is_exactly_the_dedicated_need(self):
        dedicated = dr.dedicated_slot_counts(IDP_ROSTER)
        for held in ([], ["wr1"], ["wr1", "wr2"], ["wr1", "wr2", "wr3"], ["dual"]):
            picks = _picks([("1", pid) for pid in held])
            mine = dr._team_starters_filled(picks, self.db, "1", IDP_ROSTER)
            share = dr.unfilled_slot_share(IDP_ROSTER, mine)
            for position in pu.FANTASY_POSITIONS:
                needed = max(dedicated.get(position, 0) - mine.get(position, 0), 0)
                self.assertGreaterEqual(
                    round(share.get(position, 0.0) - needed, 6), 0.0,
                    f"{position}: the flex remainder went negative holding {held}")

    def test_a_slot_the_league_does_not_declare_contributes_nothing(self):
        share = dr.unfilled_slot_share(["QB", "RB", "BN"], {})
        self.assertEqual(share["WR"], 0.0)
        self.assertEqual(share["QB"], 1.0)


if __name__ == "__main__":
    unittest.main()
