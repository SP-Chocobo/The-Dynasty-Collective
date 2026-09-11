"""#224 (#126 landmine): `bench_capacity` names TWO different quantities, and neither is wrong.

    lineup_optimizer.bench_capacity(roster_positions) -> int
        How many BN slots this league gives EACH TEAM. `sum(1 for slot in ... if slot == "BN")`.
        Per-team. A count of SLOTS. Static -- it depends on the league's shape and on nothing
        else, so it cannot change as a draft proceeds.

    draft_room.estimated_bench_demand's local `bench_capacity` -> float
        How many further PICKS the whole draft can still spend on bench spots:
        `max(remaining_draft_capacity(...) - sum(remaining_starter_demand(...).values()), 0.0)`.
        League-wide. A budget of PICKS. Draining -- it falls toward 0.0 as picks land, which is
        the entire reason it replaced the share-of-remaining-picks model (#59: a quantity that
        could not express "this position is finished").

Different unit, different scope, different arity, different behaviour in time. On this fixture
they are **3 and 36** -- a 12x gap, and only one of them moves.

WHY THIS IS FILED AND NOT FIXED. There is no live crossed wire: `draft_room` imports
`lineup_optimizer as lo`, so the module-level function is only ever reachable as
`lo.bench_capacity` and the local never shadows it. Both are correct where they stand. Renaming
either is a cosmetic change to constrained source and buys no behaviour.

WHAT THESE TESTS ARE FOR. The hazard is a future refactor that sees a bare `bench_capacity`
being computed by hand, notices a function of that exact name one attribute access away, and
"deduplicates" them. That substitution type-checks, reads as a cleanup, and would silently
replace a draining league-wide pick budget with a static per-team slot count. These pin the two
properties that make the substitution impossible to make quietly: the magnitudes differ, and
only the demand quantity responds to the draft.
"""
from __future__ import annotations

import unittest

import pandas as pd

import draft_room as dr
import lineup_optimizer as lo

# 12 teams, 2 RB + 1 K starting, 3 bench -> 72 total picks. Shared shape with
# test_draft_horizon so the two files describe the same league.
ROSTER = ["RB", "RB", "K", "BN", "BN", "BN"]
TEAMS = 12
DB = {f"{pos}{i}": {"position": pos, "fantasy_positions": [pos]}
      for pos in ("RB", "K") for i in range(1, 200)}


def _pool() -> pd.DataFrame:
    """A scored pool with a real gradient at both positions, so appetite is measurable."""
    rows = []
    for position, values in (("RB", [300 - 2.7 * i for i in range(100)]),
                             ("K", [110 - 0.15 * i for i in range(100)])):
        rows.extend({"player_id": f"{position}{i}", "position": position, "_v": v}
                    for i, v in enumerate(values))
    return pd.DataFrame(rows)


def _picks(counts: dict[str, int]) -> list[dict]:
    out: list[dict] = []
    for position, n in counts.items():
        for i in range(int(n)):
            out.append({"player_id": f"{position}{i + 1}",
                        "roster_id": str(len(out) % TEAMS + 1),
                        "round": len(out) // TEAMS + 1, "pick_no": len(out) + 1})
    return out


def _bench_budget(picks: list[dict]) -> float:
    """The draft_room quantity, recomputed here the way the function computes it."""
    starter = dr.remaining_starter_demand(ROSTER, TEAMS, picks, DB)
    capacity = dr.remaining_draft_capacity(ROSTER, TEAMS, picks)
    return max(capacity - sum(starter.values()), 0.0)


class TheTwoBenchCapacitiesAreDifferentQuantities(unittest.TestCase):

    def test_the_slot_count_is_per_team_and_the_budget_is_league_wide(self):
        slots = lo.bench_capacity(ROSTER)
        budget = _bench_budget([])
        self.assertEqual(slots, 3, "three BN entries in this league's roster_positions")
        self.assertEqual(budget, 36.0, "12 teams x 3 bench spots, as PICKS, before any pick")
        self.assertNotEqual(float(slots), budget,
                            "if these ever coincide the fixture has stopped separating them")

    def test_only_the_budget_responds_to_the_draft(self):
        """The property that makes the substitution unsafe. The slot count takes no picks
        argument at all, so it CANNOT drain; the budget must."""
        early = _bench_budget([])
        late = _bench_budget(_picks({"RB": 48}))
        self.assertLess(late, early, "the bench pick budget must fall as picks land")
        self.assertEqual(lo.bench_capacity(ROSTER), 3,
                         "the per-team slot count is a league-shape fact and never moves")

    def test_the_raw_difference_really_does_go_negative(self):
        """Establishes that the floor in estimated_bench_demand is REACHABLE, so the test
        below is not guarding a branch that can never be taken. A draft that spends its
        capacity on one position while another's starters are still owed gets there by
        ordinary means -- no adversarial fixture needed."""
        late = _picks({"RB": 72})
        capacity = dr.remaining_draft_capacity(ROSTER, TEAMS, late)
        starter = sum(dr.remaining_starter_demand(ROSTER, TEAMS, late, DB).values())
        self.assertLess(capacity - starter, 0.0,
                        "capacity 0.0 against 12.0 of K starter demand still owed")


class TheDemandFunctionTracksTheBudgetItComputes(unittest.TestCase):
    """estimated_bench_demand had NO direct tests before this file. These pin that its output
    is the bench BUDGET split by appetite -- i.e. that it carries the draining quantity, not
    the static one."""

    def _total(self, picks: list[dict]) -> float:
        bench = dr.estimated_bench_demand(_pool(), "_v", ROSTER, TEAMS, picks, DB)
        self.assertFalse(any(v is None for v in bench.values()),
                         "this fixture has a measurable gradient, so the split is defined")
        return sum(bench.values())

    def test_the_split_sums_to_the_bench_budget(self):
        for label, picks in (("opening", []), ("mid", _picks({"RB": 24}))):
            with self.subTest(label):
                self.assertAlmostEqual(self._total(picks), _bench_budget(picks), places=6,
                                       msg="the shares are the budget redistributed, not a "
                                           "separate quantity")

    def test_the_total_falls_as_the_draft_proceeds(self):
        self.assertLess(self._total(_picks({"RB": 48})), self._total([]),
                        "substituting the static slot count here would flatten this")

    def test_the_budget_never_goes_negative_through_the_real_function(self):
        """#59, and the floor is load-bearing rather than defensive. In a state where the raw
        difference is -12.0 (see above), dropping `max(..., 0.0)` would make every position's
        bench demand NEGATIVE -- the shares are `budget * appetite / total`, so the sign
        propagates to all of them. A negative count of expected further picks is not a
        quantity this engine can mean.

        Asserted through estimated_bench_demand itself. An earlier version of this test called
        the module-local `_bench_budget` helper, which re-implements the floor -- so it passed
        against a mutated engine and caught nothing. That is the vacuous-test failure mode this
        repo mutation-checks for, committed here by me and caught by the mutation pass."""
        bench = dr.estimated_bench_demand(_pool(), "_v", ROSTER, TEAMS, _picks({"RB": 72}), DB)
        measured = {k: v for k, v in bench.items() if v is not None}
        self.assertTrue(measured, "this fixture must produce a measured split, not all-absent")
        for position, value in measured.items():
            with self.subTest(position):
                self.assertGreaterEqual(value, 0.0, "bench demand cannot be negative")

    def test_a_finished_draft_reports_exactly_zero(self):
        """#59, the property the whole decomposition exists for: the quantity this replaced
        was strictly positive for any position ever drafted, and so could not say "this
        position is finished". Zero is a real measured zero here, not an absence -- the keys
        are present and the values are 0.0, which is what a consumer needs to distinguish
        "no more expected" from "nobody looked".

        Flooring at anything above zero would break that: every position's share would carry
        a sliver of phantom demand forever."""
        bench = dr.estimated_bench_demand(_pool(), "_v", ROSTER, TEAMS, _picks({"RB": 72}), DB)
        self.assertEqual(set(bench), set(dr.FANTASY_POSITIONS),
                         "every position keeps a key -- a finished draft is measured, not absent")
        for position, value in bench.items():
            with self.subTest(position):
                self.assertIsNotNone(value, "0.0 here is measured, so it must not be None")
                self.assertEqual(value, 0.0)

    def test_the_total_is_never_the_per_team_slot_count(self):
        """The exact confusion #224 names, stated as an assertion."""
        self.assertNotAlmostEqual(self._total([]), float(lo.bench_capacity(ROSTER)), places=6)


if __name__ == "__main__":
    unittest.main()
