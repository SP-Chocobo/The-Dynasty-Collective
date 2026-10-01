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


class TheDeficitClosesAsTheWalkConsumesIt(unittest.TestCase):
    """MANDATE 1.3: the summed pace mass never subtracted what the walk itself had taken.

    `positional_forfeits` advances `picks_made_now` one hypothetical pick at a time, so
    `expected_now` climbs the convention's cumulative curve -- while `actual_now` is counted off a
    FIXED list of picks really made. Nothing removed what the gap itself was expected to consume,
    so the same deficit was charged again at every step, and a sum of per-pick hazards was then
    reported as an expected COUNT. Measured on a real superflex board (12T_ppr_SF, capture
    universe, season sums):

        state             gap   QB expected_taken   convention's increment   all positions
        1.01               22   15.54 -> 7.02                        8.92   26.15 -> 17.63
        after 24 picks     22    2.81 -> 1.45                        2.17   12.99 -> 11.63

    26.15 expected takes across 22 picks is not a large number, it is an impossible one, and
    `#206` had already repaired exactly that arithmetic from the other direction. RB, TE and WR
    are byte-identical across the repair: no convention is documented for them, so nothing
    outside the case it was built for moved.

    NOT A CAP, which `#56` would forbid. No number is introduced and no bound is chosen -- the
    quantity subtracted is the caller's own running expectation, and the convention supplies its
    own ceiling by arithmetic once the walk has consumed the deficit."""

    def test_the_deficit_is_reduced_by_what_the_walk_already_took(self):
        """The unit of the repair, with no board in it. At pick 12 the convention expects 6.0
        quarterbacks gone and none are, so the whole deficit spread over the catch-up window is
        the answer -- and a walk that has already expected to see those 6 must read 0.0."""
        full = ds.position_pace_probability("QB", 12, _picks(0), PLAYERS, SF)
        self.assertEqual(1.0, full)
        half = ds.position_pace_probability("QB", 12, _picks(0), PLAYERS, SF,
                                            expected_taken_in_gap=3.0)
        self.assertAlmostEqual(0.5, half)
        spent = ds.position_pace_probability("QB", 12, _picks(0), PLAYERS, SF,
                                             expected_taken_in_gap=6.0)
        self.assertEqual(0.0, spent)

    def test_a_walk_that_has_taken_more_than_the_convention_expected_does_not_go_negative(self):
        self.assertEqual(0.0, ds.position_pace_probability(
            "QB", 12, _picks(0), PLAYERS, SF, expected_taken_in_gap=99.0))

    def test_the_default_leaves_the_single_pick_caller_exactly_as_it_was(self):
        """`_pace_based_take_probability` asks about ONE next pick, so there is no gap to have
        consumed anything. Its call is unchanged, and this is what says so."""
        self.assertEqual(ds.position_pace_probability("QB", 24, _picks(2), PLAYERS, SF),
                         ds.position_pace_probability("QB", 24, _picks(2), PLAYERS, SF,
                                                      expected_taken_in_gap=0.0))

    def test_the_summed_pace_mass_stays_inside_the_conventions_own_increment(self):
        """The property the measured table is one instance of, on a board the RANK model cannot
        score, so the sum is pure convention: across a gap, the expected number taken cannot
        exceed what the convention itself says will be gone by the end of it.

        This is what the old code broke -- and it broke it by a factor of 1.7 at 1.01."""
        gap = 22
        curves = {"QB": [100.0 - 2.0 * i for i in range(40)]}
        # No QB rows on any opponent board, so the rank model contributes nothing and every bit
        # of expected_taken below comes from the convention.
        boards = {str(r): {"rank_by_id": {"w": 1}, "by_id": {"w": {"position": "WR"}}}
                  for r in range(2, 2 + gap)}
        result = ds.positional_forfeits(
            curves, boards, [str(r) for r in range(2, 2 + gap)], None,
            picks=_picks(0), players_db=PLAYERS, roster_positions=SF, picks_made_now=0)
        summed = result["QB"]["expected_taken"]
        by_the_end = ds.expected_position_pace("QB", gap, SF)
        self.assertGreater(summed, 0.0, "the convention contributed nothing -- nothing is bounded")
        self.assertLessEqual(summed, by_the_end,
                             f"the walk expects {summed} quarterbacks gone across {gap} picks "
                             f"while the convention it reads says {by_the_end}")

    def test_the_cross_position_total_CONSERVES(self):
        """INVERTED, as its own earlier form instructed. This test used to record that the total
        could exceed the gap and to say "invert when repaired"; the owner ruled that the convention
        wins and the other positions scale down, and it now conserves.

        The fixture is the hostile one deliberately: 22 opponents each holding exactly ONE priced
        WR, so the rank model spends a full 1.0 per pick on WR, with a superflex QB convention on
        top demanding room it cannot have. That is the board that produced 29.02 expected takes
        across 22 picks before the ruling. A gap of N picks cannot remove more than N players, and
        this is the arithmetic `#206` repaired once from the other direction."""
        gap = 22
        curves = {pos: [100.0 - 2.0 * i for i in range(40)] for pos in ("QB", "RB", "WR", "TE")}
        boards = {str(r): {"rank_by_id": {"w": 1}, "by_id": {"w": {"position": "WR"}}}
                  for r in range(2, 2 + gap)}
        result = ds.positional_forfeits(
            curves, boards, [str(r) for r in range(2, 2 + gap)], None,
            picks=_picks(0), players_db=PLAYERS, roster_positions=SF, picks_made_now=0)
        total = sum(v["expected_taken"] for v in result.values())
        self.assertGreater(total, 0.0, "the fixture measures nothing")
        self.assertLessEqual(total, gap,
                             f"{total} players expected gone across {gap} picks")

    def test_the_convention_is_what_yields_LAST(self):
        """The owner's ruling, as a property rather than a comment: when one pick cannot hold both
        the convention's demand and the rank model's, the rank model gives way first.

        Built so the two compete for the same pick: the rank model spends its whole mass on WR, and
        superflex QB is far enough behind its documented pace to want real room. If the scaling ran
        the other way, QB would be the one squeezed."""
        gap = 6
        curves = {pos: [100.0 - 2.0 * i for i in range(40)] for pos in ("QB", "WR")}
        boards = {str(r): {"rank_by_id": {"w": 1}, "by_id": {"w": {"position": "WR"}}}
                  for r in range(2, 2 + gap)}
        result = ds.positional_forfeits(
            curves, boards, [str(r) for r in range(2, 2 + gap)], None,
            picks=_picks(0), players_db=PLAYERS, roster_positions=SF, picks_made_now=12)
        qb, wr = result["QB"]["expected_taken"], result["WR"]["expected_taken"]
        self.assertGreater(qb, 0.0, "the convention got no room at all -- it is meant to win")
        self.assertLess(wr, float(gap),
                        "the rank model kept its whole mass, so nothing yielded and the total "
                        "cannot have conserved")
        self.assertLessEqual(qb + wr, gap + 0.01)

    def test_a_pick_nobody_contests_is_untouched(self):
        """NON-VACUITY for the scaling: when the total already fits in one pick, nothing is scaled
        and the rank model's own numbers survive exactly. A repair that quietly rescaled every
        board would be a valuation change wearing a conservation argument."""
        gap = 3
        curves = {"WR": [100.0 - 2.0 * i for i in range(40)]}
        # One priced WR at rank 5 -- real mass, nowhere near saturating the pick.
        boards = {str(r): {"rank_by_id": {"w": 5}, "by_id": {"w": {"position": "WR"}}}
                  for r in range(2, 2 + gap)}
        alone = ds.positional_forfeits(curves, boards, [str(r) for r in range(2, 2 + gap)], None)
        with_ctx = ds.positional_forfeits(
            curves, boards, [str(r) for r in range(2, 2 + gap)], None,
            picks=_picks(0), players_db=PLAYERS, roster_positions=ONE_QB, picks_made_now=0)
        self.assertGreater(alone["WR"]["expected_taken"], 0.0)
        self.assertEqual(alone["WR"]["expected_taken"], with_ctx["WR"]["expected_taken"],
                         "an uncontested pick was rescaled anyway")


if __name__ == "__main__":
    unittest.main()
