"""D1 / `#193` / `#187` -- `rival_premium_basis` is `denial_basis`, and that has to stay honest.

THE DECISION THIS PINS. 2.5 found six absence-contract breaks and repaired five. The sixth is
`rival_premium`, whose basis string is not its own: `pick_analysis` emits
`"rival_premium_basis": denial_basis` verbatim, a value computed for a DIFFERENT quantity in the
same loop. The owner ruled **keep the borrow and pin it** (D1(a)) rather than build the term its own
four-state vocabulary (D1(b)) or withdraw the label and report absence (D1(c)).

Correcting my own write-up, because the correction is why (a) won: I first presented the borrow as a
*proposed* fix. It is the CURRENT STATE and has shipped, and the comment beside it presents it as
deliberate -- *"the companion, same vocabulary denial_basis uses"*. So (c) was never "leave it
alone"; it was a removal of a string that is correct today.

WHAT MAKES THE BORROW TRUE, and it is not a matter of taste. `denial_basis` is derived from two
counters and nothing else:

    rivals_considered == 0  ->  no_intervening_rival
    rivals_priced     == 0  ->  no_rival_priced
    otherwise               ->  measured

and `rival_premium` is assigned only inside the same loop, on the line after `rivals_priced += 1`,
under `if rival_premium is None or premium > rival_premium` -- so the first priced rival always
assigns it. That yields one biconditional:

    rival_premium is not None   <->   denial_basis == measured

While that holds, the borrowed string is a TRUE statement about `rival_premium`'s own provenance and
`#193` is satisfied -- an absent number is never handed a basis claiming it was measured. The day it
stops holding, the borrow becomes a lie that no consumer can detect, which is the whole risk D1
weighed. This module is what makes that day loud.

MEASURED on six real board states of a 12-team superflex-free dynasty PPR draft, every one of my
turns in each region, priced and unpriced candidates both -- 144 rows:

    measured              rival_premium present   48
    no_intervening_rival  rival_premium ABSENT    72
    no_rival_priced       rival_premium ABSENT    24
    violations                                     0

All three states are reached, so the biconditional below is checked against a population that
contains both of its directions rather than asserted over one arm.

WHAT THIS MODULE DOES NOT CLAIM. It does not say the borrow is the right long-term design; D1(b)
stays recorded in `OWNER_DECISIONS_PENDING.md` as the shape to build when the term is next opened.
It says the deferral is SAFE, which is a different and checkable claim.
"""

from __future__ import annotations

import inspect
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds

ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
ROSTER_IDS = [str(i) for i in range(1, NUM_TEAMS + 1)]

#: The regions of the draft sampled. Two-round windows so that BOTH a back-to-back snake turn
#: (which produces no_intervening_rival) and a mid-round turn (which produces measured) are drawn
#: from the same board -- the biconditional is only interesting where both arms occur.
ROUNDS = (0, 2, 4, 6, 8, 10)


class _RealRows(unittest.TestCase):
    """Real analysis rows, because a hand-built row can be made to satisfy any invariant. The
    population has to be the one `pick_analysis` actually produces."""

    rows: list = []

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            for _, row in proj[proj["position"] == position].sort_values(
                    "trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        opening = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id="1",
                                        league=DYNASTY, mode="balanced")
        pick_order = ds.generate_pick_order(ROSTER_IDS, 24, "snake")

        cls.rows = []
        for rounds in ROUNDS:
            taken = rounds * NUM_TEAMS
            picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                      "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                     for i, r in enumerate(opening[:taken])]
            board = dr.compute_draft_board(cls.merger, cls.players_db, picks, my_roster_id="1",
                                           league=DYNASTY, mode="balanced")
            priced = [r for r in board if r.get("final_score") is not None]
            unpriced = [r for r in board if r.get("final_score") is None]
            #: Unpriced candidates are included ON PURPOSE. They are the population that reaches
            #: no_rival_priced, and a sample of priced rows alone would leave that state unvisited
            #: and this module's central assertion half-tested.
            candidates = [r["player_id"] for r in priced[:8]] + [r["player_id"] for r in unpriced[:4]]
            if not candidates:
                continue
            for index in [i for i in range(rounds * NUM_TEAMS,
                                           min((rounds + 2) * NUM_TEAMS, len(pick_order)))
                          if pick_order[i] == "1"]:
                cls.rows += ds.pick_analysis(
                    cls.merger, cls.players_db, picks, pick_order, index, "1", DYNASTY,
                    candidates, mode="balanced")


class TheBorrowedBasisDescribesItsOwnNumberTests(_RealRows):

    def test_the_population_reaches_every_basis_state(self):
        """Non-vacuity, and the strongest of the three: a run that never reaches an absent state
        would satisfy the biconditional trivially in one direction."""
        seen = {row["denial_basis"] for row in self.rows}
        self.assertEqual(seen, set(ds.DENIAL_BASIS_LABELS),
                         f"only {sorted(seen)} reached; the invariant below is half-tested")

    def test_a_premium_exists_exactly_where_the_basis_says_measured(self):
        """THE INVARIANT. While this holds the borrowed string is a true statement about
        rival_premium's own provenance; when it stops, no consumer can tell."""
        for row in self.rows:
            with self.subTest(name=row.get("name"), basis=row["denial_basis"]):
                self.assertEqual(row["rival_premium"] is not None,
                                 row["denial_basis"] == ds.DENIAL_MEASURED,
                                 "rival_premium's presence and denial_basis have diverged, so the "
                                 "borrowed rival_premium_basis is now describing a different "
                                 "quantity than the one it is attached to (see D1)")

    def test_the_emitted_companion_is_the_same_string_not_a_recomputation(self):
        for row in self.rows:
            self.assertEqual(row["rival_premium_basis"], row["denial_basis"])

    def test_an_absent_premium_is_never_labelled_measured(self):
        """`#193` stated at the one place it could break: an admission on evidence with no
        number. Implied by the biconditional, kept separate because it is the FAILURE, and a
        failure deserves to be named rather than inferred."""
        for row in self.rows:
            if row["rival_premium"] is None:
                self.assertNotEqual(row["rival_premium_basis"], ds.DENIAL_MEASURED)

    def test_a_measured_premium_may_legitimately_be_zero(self):
        """The contract's other half (`#187`): 0.0 is a measurement, not an absence, so the
        repair must never be 'turn zeros into None'. Recorded as an allowance rather than
        asserted as present -- a board where no rival premium happens to be 0.0 is not a defect."""
        measured = [r for r in self.rows if r["rival_premium_basis"] == ds.DENIAL_MEASURED]
        self.assertTrue(measured, "no measured rows; the allowance below is untested")
        for row in measured:
            self.assertIsNotNone(row["rival_premium"])
            self.assertGreaterEqual(row["rival_premium"], 0.0)


class TheTwoAreComputedFromOneScanTests(unittest.TestCase):
    """The structural half. The biconditional above is a consequence of `rival_premium` being
    assigned inside the same rival loop the counters are incremented in; these guard the shape that
    makes it true, so a refactor that separates them fails here with a reason rather than failing
    the behavioural test with a puzzle."""

    @classmethod
    def setUpClass(cls):
        cls.source = inspect.getsource(ds.pick_analysis)

    def test_the_premium_is_assigned_inside_the_loop_that_counts_priced_rivals(self):
        priced = self.source.index("rivals_priced += 1")
        assigned = self.source.index("rival_premium = premium")
        basis = self.source.index("if not rivals_considered:")
        self.assertLess(priced, assigned,
                        "rival_premium is assigned before the priced counter, so a rival that "
                        "cannot be priced could still set it")
        self.assertLess(assigned, basis,
                        "the basis is decided before the scan finishes assigning the premium")

    def test_the_first_priced_rival_always_assigns_it(self):
        """`premium > rival_premium` alone would leave it None whenever every premium is <= 0,
        and `measured` would then travel with an absent number. The `is None` arm is what makes
        the biconditional hold rather than nearly hold."""
        self.assertIn("if rival_premium is None or premium > rival_premium:", self.source)

    def test_the_premium_starts_absent_rather_than_at_zero(self):
        """`#207`. If it started at 0.0 there would be no absent state to keep honest and the
        whole of D1 would be moot -- in the wrong direction."""
        self.assertIn("rival_premium = None", self.source)

    def test_the_companion_is_emitted_as_the_borrowed_name(self):
        """D1(a) is explicitly a decision to KEEP a borrow. If someone later computes a separate
        string and happens to make it agree, the behavioural test above still passes while the
        thing this module was asked to pin has silently been replaced by D1(b) half-done."""
        self.assertIn('"rival_premium_basis": denial_basis,', self.source)

    def test_no_second_basis_vocabulary_has_appeared(self):
        """The other half of that: D1(b) is a decision the owner has not taken, and a
        RIVAL_PREMIUM_* vocabulary appearing without one is the drift this guards."""
        names = [n for n in dir(ds) if n.startswith("RIVAL_PREMIUM")]
        self.assertEqual(names, [],
                         f"{names} looks like rival_premium's own basis vocabulary; that is "
                         f"D1(b) and needs the owner, not a quiet arrival")


if __name__ == "__main__":
    unittest.main()
