"""#206 -- the take model has ONE home, and `estimate_survival` reaches it through one door.

WHY THIS FILE EXISTS. `_board_take_probability` was extracted so a calibration arm could score
the real `estimate_survival` against an alternative take model without re-implementing survival
beside it (evidence/survival_calibration/value_model_arm.py). An extraction like that has two
failure modes, and neither is loud:

  * THE SEAM GOES DECORATIVE. Someone inlines the arithmetic back into the loop "for clarity".
    The seam still exists, still has a docstring saying it is the only door, and no longer has
    any callers -- so every future arm silently measures production instead of its own model,
    and reports a difference of zero as a finding. `test_the_seam_is_load_bearing` fails that.
  * THE SEAM BECOMES A SWITCH. Someone gives it a module flag so production can "try" the other
    model. That is two take models in one engine (`#126`) and the thing the seam's own docstring
    forbids. `test_production_carries_exactly_one_take_model` fails that.

WHAT IS DELIBERATELY NOT ASSERTED HERE: which model is right. That is the calibration harness's
question and it is answered in evidence/survival_calibration/VALUE_MODEL_RESULT.md, where the
value-share arm beats the rank table on every board-rank band and still loses to a constant
because of the unpriced floor. This file only holds the SHAPE that lets that question keep
being asked honestly.
"""
from __future__ import annotations

import inspect
import unittest

import draft_strategy as ds


def _board(priced, unpriced=()):
    """A minimal opponent board in the shape `_build_opponent_boards` produces."""
    return {
        "rank_by_id": {pid: rank for pid, rank, _ in priced},
        "by_id": {pid: {"player_id": pid, "position": "RB", "final_score": score}
                  for pid, _, score in priced}
                 | {pid: {"player_id": pid, "position": "RB", "final_score": None}
                    for pid in unpriced},
        "unpriced_ids": tuple(unpriced),
    }


class TheSeamIsTheOnlyDoorTests(unittest.TestCase):

    def setUp(self):
        self.board = _board([("a", 1, 100.0), ("b", 2, 90.0), ("c", 3, 10.0)], unpriced=("z",))

    def test_the_seam_returns_what_the_inlined_arithmetic_returned(self):
        """Behaviour preservation, stated as arithmetic rather than as a golden number: the
        seam must equal the composition it replaced, so the extraction cannot have moved a
        value while every downstream test kept passing."""
        mass = ds.board_take_mass(self.board, None)
        for pid, rank in (("a", 1), ("b", 2), ("c", 3)):
            p, share = ds._board_take_probability(self.board, pid, rank, False, False, None)
            self.assertAlmostEqual(
                p, ds._take_probability(rank, False, mass["total_weight"]), places=12,
                msg=f"the seam moved the priced answer for rank {rank}")
            self.assertEqual(share, mass["unpriced_share"])
        p_unpriced, _ = ds._board_take_probability(self.board, "z", None, True, False, None)
        self.assertAlmostEqual(p_unpriced,
                               ds._take_probability(None, False, mass["total_weight"]), places=12)

    def test_the_seam_is_load_bearing_not_decorative(self):
        """The property an arm's validity rests on. Substituting the seam must change what
        `estimate_survival` returns -- if it does not, the arm measured production twice and
        would report a real difference as no difference at all."""
        pick_order = ["1", "2", "3", "1"]
        boards = {"2": self.board, "3": self.board}
        kwargs = dict(picks=[], players_db={}, pick_order=pick_order, current_index=0,
                      my_roster_id="1", target_player_id="a", opponent_boards=boards)
        before = ds.estimate_survival(**kwargs)["survival_probability"]

        original = ds._board_take_probability
        try:
            ds._board_take_probability = lambda *a, **k: (0.5, None)
            after = ds.estimate_survival(**kwargs)["survival_probability"]
        finally:
            ds._board_take_probability = original
        self.assertNotEqual(before, after,
                            "substituting the seam changed nothing -- estimate_survival is not "
                            "reaching the take model through it, so every calibration arm that "
                            "substitutes it is measuring production and calling it an arm")
        self.assertAlmostEqual(after, 0.25, places=9,
                               msg="two intervening picks at p=0.5 each must leave 0.25")
        self.assertEqual(ds.estimate_survival(**kwargs)["survival_probability"], before,
                         "the substitution outlived the block that installed it")

    def test_production_carries_exactly_one_take_model(self):
        """No flag chooses a model. A seam that reads a module global to decide what to be is a
        switch, and a switch is two take models in one engine -- which is what the whole
        `#206` measurement exists to avoid shipping."""
        source = inspect.getsource(ds._board_take_probability)
        for forbidden in ("TAKE_MODEL", "take_model", "USE_VALUE", "use_value", "MODEL_NAME"):
            self.assertNotIn(forbidden, source,
                             f"the seam reads {forbidden!r} -- it has become a switch")
        loop = inspect.getsource(ds.estimate_survival)
        self.assertIn("_board_take_probability(", loop,
                      "estimate_survival no longer calls the seam")
        self.assertNotIn("_take_probability(rank", loop,
                         "estimate_survival computes a take probability outside the seam, so "
                         "there are two doors and an arm can only substitute one of them")


if __name__ == "__main__":
    unittest.main()
