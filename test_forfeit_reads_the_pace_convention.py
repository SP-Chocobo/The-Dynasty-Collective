"""positional_forfeits reads the pace convention estimate_survival already trusts (#52).

THE SAME TWO FUNCTIONS HAVE NOW DIVERGED TWICE. `positional_forfeits`' own docstring records
the first: `#206` normalised the take model, applied it to `estimate_survival`, and "THIS
CONSUMER WAS NOT CONVERTED". Then `_pace_based_take_probability` was built -- for a case its
docstring says the rank model "structurally cannot handle" -- and the same consumer was missed
again.

Two accidents with one shape is a pull, not luck: the functions answer adjacent questions off
one model, and the position-level half had no name of its own to reach for. `position_pace_
probability` is that name, and these tests are what make the third occurrence fail loudly
rather than surface as a roster that quietly stops drafting quarterbacks.
"""

from __future__ import annotations

import unittest

import draft_strategy as ds


SF = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX"] + ["BN"] * 6
ONE_QB = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"] + ["BN"] * 6
PLAYERS = {str(i): {"position": "QB", "fantasy_positions": ["QB"]} for i in range(1, 40)}


def _picks(n_qb: int) -> list[dict]:
    return [{"player_id": str(i + 1)} for i in range(n_qb)]


class ThePositionLevelPaceHasOneHome(unittest.TestCase):
    """It is step 1 of _pace_based_take_probability, extracted because it has two consumers."""

    def test_a_position_behind_its_documented_pace_carries_a_probability(self):
        p = ds.position_pace_probability("QB", 24, _picks(2), PLAYERS, SF)
        self.assertIsNotNone(p)
        self.assertGreater(p, 0.0)

    def test_a_position_AHEAD_of_pace_carries_none_of_it(self):
        """The half that shows this is reading a convention rather than boosting a favourite.
        Measured on a real superflex draft: by round 5, seventeen QBs are gone against a
        documented pace of ~12.8, and the correction correctly contributes nothing."""
        ahead = ds.position_pace_probability("QB", 24, _picks(30), PLAYERS, SF)
        self.assertEqual(0.0, ahead)

    def test_no_documented_convention_is_absence_not_zero(self):
        """None, never 0.0 (#187). A caller must be able to tell "the convention says this pick
        is not going here" from "there is no convention for this position at all" -- the first
        is a measurement and the second is silence, and only the first may lower a forfeit."""
        self.assertIsNone(ds.position_pace_probability("QB", 24, _picks(2), PLAYERS, ONE_QB))
        self.assertIsNone(ds.position_pace_probability("RB", 24, _picks(2), PLAYERS, SF))

    def test_past_the_last_anchor_there_is_no_convention_to_extrapolate(self):
        last = ds.SUPERFLEX_QB_PACE_ANCHORS[-1][0]
        self.assertIsNone(ds.position_pace_probability("QB", last, _picks(2), PLAYERS, SF))

    def test_both_consumers_read_the_same_function(self):
        """THE WIRING GUARD, and the reason this file exists. Proving the function correct
        proves nothing about whether `positional_forfeits` calls it -- which is exactly how the
        first divergence survived."""
        import ast, pathlib
        tree = ast.parse(pathlib.Path("draft_strategy.py").read_text())
        callers = {n.name for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)
                   and any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                           and c.func.id == "position_pace_probability"
                           for c in ast.walk(n))}
        self.assertIn("positional_forfeits", callers,
                      "positional_forfeits no longer reads the pace convention -- this is the "
                      "third occurrence of the divergence this file was written for")
        self.assertIn("_pace_based_take_probability", callers,
                      "the per-player path stopped reading the shared step, so the two can "
                      "drift apart again")


class TheConventionOnlyEverRaisesTheRankEstimate(unittest.TestCase):
    """Not an average and not a replacement: the rank model is a real estimate that is merely
    BLIND to a convention-driven position, so the convention can only raise it."""

    #: A board the RANK model can actually score. The first version of these tests used an
    #: empty one, so the rank estimate was 0.0 and "the convention only RAISES it" could not be
    #: distinguished from "the convention REPLACES it" -- a mutant that swapped max for
    #: replacement survived untouched. An assertion about which of two numbers wins is vacuous
    #: unless the losing one is non-zero.
    BOARD = {"rank_by_id": {"1": 1, "2": 2},
             "by_id": {"1": {"position": "QB"}, "2": {"position": "QB"}}}

    @staticmethod
    def _forfeits(board=None, **kw):
        curves = {"QB": [100.0, 90.0, 80.0, 70.0, 60.0]}
        boards = {"2": dict(board if board is not None else {"rank_by_id": {}, "by_id": {}})}
        return ds.positional_forfeits(curves, boards, ["2"], None, **kw)

    def test_without_league_context_the_previous_behaviour_is_exact(self):
        """The four parameters are optional TOGETHER. A caller that cannot supply them -- every
        existing fixture -- must draft as before rather than silently lose the rank model."""
        self.assertEqual(0.0, self._forfeits()["QB"]["expected_taken"])

    def test_with_a_position_behind_pace_the_expectation_rises(self):
        behind = self._forfeits(picks=_picks(2), players_db=PLAYERS,
                                roster_positions=SF, picks_made_now=24)
        self.assertGreater(behind["QB"]["expected_taken"], 0.0)

    def test_a_position_ahead_of_pace_is_left_where_the_rank_model_put_it(self):
        """Over a board the rank model SCORES, so the two candidate rules give different
        answers: max() keeps the rank estimate, replacement would lower it to the convention's
        zero. Run against an empty board this assertion held either way and proved nothing."""
        rank_only = self._forfeits(board=self.BOARD)["QB"]["expected_taken"]
        self.assertGreater(rank_only, 0.0, "the rank model scored nothing -- nothing is at risk")
        ahead = self._forfeits(board=self.BOARD, picks=_picks(30), players_db=PLAYERS,
                               roster_positions=SF, picks_made_now=24)
        self.assertEqual(rank_only, ahead["QB"]["expected_taken"],
                         "an ahead-of-pace convention LOWERED the rank estimate; it may only "
                         "ever raise it")


if __name__ == "__main__":
    unittest.main()
