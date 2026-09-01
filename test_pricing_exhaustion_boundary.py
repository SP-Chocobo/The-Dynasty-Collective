"""1c / #114: what the board does once nothing on it can be priced.

MEASURED, on one 12-team x 18-round draft against the committed baseline (216 picks):

  * Unpriced rows appear long before they matter -- 139 of a 203-row pool by pick 131 -- and
    are correctly ordered last, so they change nothing while any priced row remains.
  * Pricing dies COMPLETELY at pick 155 (round 13): zero priced rows out of 179. From there
    every remaining pick in the draft is decided by the player_id tiebreak alone.
  * 78 of 216 picks (36.1%) had a tied top score. Two distinct regimes hide under that one
    number: rounds 6-9 show small genuine score collisions (tie groups of 2-4, mostly
    DEF/K/QB, with REAL final_score values), and rounds 13-18 show total exhaustion (tie group
    == the entire pool, final_score is None).

THE MECHANISM is deliberate and documented. `replacement_levels` omits a position once its
remaining starter demand is exhausted; `compute_draft_board` then leaves `_vor` NaN for every
player at that position, so bpa -> universal_value -> final_score are all None. The engine is
refusing to price a player against a replacement level that no longer exists, which is the
right refusal: draft_room's own rule is that absent data must not become a fabricated number.

WHAT IS NOT DECIDED is what to do next, and `_board_order`'s docstring says so in as many
words: *"it does not decide what the board SHOULD do once nothing on it can be priced; that is
an open product decision."* This file pins the current answer so a change to it is visible.

SIGNAL DOES SURVIVE, and this matters for the decision. On the fully-unpriced board every row
still carries a real, differing `projected_points` (measured: 64, 52, 43, 43, 53, ... 319, 312,
169 for the first fifteen rows in board order), plus `confidence` and `bpa_source`. The board
is not choosing between indistinguishable players; it is choosing between distinguishable
players using none of what distinguishes them. Whether projected_points SHOULD order them is
the open question -- season points are not comparable across positions the way VOR is -- and
this file deliberately does not answer it.

INVERT these tests on repair. Do not delete them.
"""

from __future__ import annotations

import dataclasses
import unittest

import pick_synthesis as ps
from pick_synthesis import _board_order


def _row(player_id, score=None, projected_points=None, position="RB"):
    return {"player_id": player_id, "final_score": score,
            "projected_points": projected_points, "position": position}


class UnpricedNeverOutranksPricedTests(unittest.TestCase):
    """The half of the contract that IS settled, and is correct."""

    def test_a_priced_row_always_sorts_above_an_unpriced_one(self):
        rows = [_row("1", None), _row("2", -999.0), _row("3", None), _row("4", 0.0)]
        ordered = [r["player_id"] for r in sorted(rows, key=_board_order)]
        self.assertEqual(ordered[:2], ["4", "2"], "priced rows first, best score first")
        self.assertEqual(set(ordered[2:]), {"1", "3"})

    def test_an_absent_score_is_never_substituted_with_zero(self):
        """A row whose position has no replacement level has no value. Ranking it where 'worth
        exactly zero' ranks would be a claim the engine has no basis for."""
        rows = [_row("a", None), _row("b", 0.0), _row("c", -5.0)]
        ordered = [r["player_id"] for r in sorted(rows, key=_board_order)]
        self.assertEqual(ordered, ["b", "c", "a"],
                         "an unpriced row sorts below even a NEGATIVE priced one")


class TerminalOrderIsAStringSortTests(unittest.TestCase):
    """CHARACTERIZATION of the undecided half. Every assertion here describes behaviour that a
    repair is expected to change."""

    def test_when_nothing_is_priced_the_order_is_player_id_ascending(self):
        rows = [_row("3"), _row("1"), _row("2")]
        self.assertEqual([r["player_id"] for r in sorted(rows, key=_board_order)],
                         ["1", "2", "3"])

    def test_the_sort_is_lexicographic_not_numeric(self):
        """Measured on the real board: ['100','101',...,'110','112','12','13','144'] -- player
        '12' ranks below '110' because the key is `str(player_id)`. Nothing about a player's id
        is a statement about the player, so this is arbitrary in the strict sense: it is
        deterministic, and it carries no information."""
        rows = [_row("12"), _row("110"), _row("9"), _row("100")]
        ordered = [r["player_id"] for r in sorted(rows, key=_board_order)]
        self.assertEqual(ordered, ["100", "110", "12", "9"])
        self.assertNotEqual(ordered, sorted([r["player_id"] for r in rows], key=int),
                            "if this ever matches numeric order the key changed -- re-read it")

    def test_a_far_better_projected_player_can_rank_last(self):
        """THE CONSEQUENCE, reproduced from the real measurement. Once pricing is gone the board
        recommends a 36-point player over a 319-point player, because '110' < '12' as strings --
        while still CARRYING both projections on the very rows it is ordering.

        It compounds: the board stops recommending the better players, so they stay in the pool,
        so it keeps not recommending them."""
        rows = [_row("110", projected_points=36.0), _row("12", projected_points=319.0)]
        ordered = sorted(rows, key=_board_order)
        self.assertEqual(ordered[0]["player_id"], "110")
        self.assertEqual(ordered[0]["projected_points"], 36.0)
        self.assertEqual(ordered[-1]["projected_points"], 319.0)

    def test_projected_points_is_present_and_ignored(self):
        """Non-vacuity for the test above: the engine HAS the distinguishing number on the row
        and the sort key does not read it. Reversing the projections must not change the order."""
        a = [_row("110", projected_points=36.0), _row("12", projected_points=319.0)]
        b = [_row("110", projected_points=319.0), _row("12", projected_points=36.0)]
        self.assertEqual([r["player_id"] for r in sorted(a, key=_board_order)],
                         [r["player_id"] for r in sorted(b, key=_board_order)])

    def test_a_priced_board_is_unaffected_by_any_of_this(self):
        """Non-vacuity for the whole file: while pricing exists, score decides and the id
        tiebreak is inert. These tests are describing a terminal regime, not the normal one."""
        rows = [_row("1", 10.0), _row("2", 30.0), _row("3", 20.0)]
        self.assertEqual([r["player_id"] for r in sorted(rows, key=_board_order)],
                         ["2", "3", "1"])


class TheSnapshotTypeDisagreesWithTheDataTests(unittest.TestCase):
    """A contract inconsistency found while measuring #114, recorded rather than repaired.

    In the exhausted regime `CandidateSnapshot` really does carry None for bpa,
    universal_value and team_acquisition_value -- a probe crashed on exactly that. The BEHAVIOUR
    is correct and is the absence contract working as intended. The ANNOTATIONS are what is
    wrong: all three say `float`, so the declared meaning and the actual meaning diverge, which
    is the §17.5/#110 class seen in a type hint rather than a rename.

    Not repaired here: 1c is scoped to measurement, and widening these to Optional touches the
    same fields #119 is parked on. INVERT when the annotations are corrected."""

    def test_three_fields_are_annotated_float_but_are_none_when_pricing_is_gone(self):
        annotations = {f.name: f.type for f in dataclasses.fields(ps.CandidateSnapshot)}
        for field in ("bpa", "universal_value", "team_acquisition_value"):
            with self.subTest(field=field):
                self.assertEqual(annotations[field], "float",
                                 "annotation corrected -- invert this test")

    def test_the_absence_itself_is_representable_and_survives(self):
        """The behaviour half, which is right: None flows through the ordering contract without
        being coerced, so the engine's refusal to price is preserved end to end."""
        rows = [_row("b", None), _row("a", None)]
        ordered = sorted(rows, key=_board_order)
        self.assertTrue(all(r["final_score"] is None for r in ordered))


if __name__ == "__main__":
    unittest.main()
