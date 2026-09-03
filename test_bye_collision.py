"""#142 / #138 / #139: bye weeks as a measured absence, and the decision not to price them.

Two things are covered, and the second is the one that will look wrong to a later reader:

  THE MECHANISM. bye_collision removes every player on a given bye SIMULTANEOUSLY and re-solves
  the lineup. Simultaneous loss is not the sum of separate losses -- the bench covers the first
  hole and has nothing left for the second -- which is exactly what depth_exposure's
  one-at-a-time removal cannot express and what a headcount gets backwards.

  THE REFUSAL. It feeds no valuation. That was measured, not assumed: the engine's own drafted
  rosters already sit at the pigeonhole floor for an 8-starter shape, and no swap within 10
  universal_value points improves them. A term that cannot improve the outcome it targets is
  the write-only defect (#138) with the arrow reversed -- built, read by the scorer, and
  changing nothing worth changing.
"""

from __future__ import annotations

import unittest

import data_merger as dm
import lineup_optimizer as lo

ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN"]


def _p(pid, value, position, bye=None):
    return {"id": pid, "value": value, "eligible": {position}, "bye": bye}


class ValueLostNotBodiesLostTests(unittest.TestCase):
    """The distinction the whole function exists for. A headcount ranks these two backwards."""

    def test_a_covered_absence_costs_nothing(self):
        """Three starters out, a genuinely equal body behind each: the lineup is untouched. A
        headcount would call this the worst week on the roster.

        The bench has to be deep enough to refill the FLEX too, which is what makes this a
        real cover rather than a partial one -- a first draft of this fixture carried two spare
        players against three absences and cost 25, correctly."""
        players = [_p("q1", 30, "QB", 7), _p("q2", 30, "QB", 9),
                   _p("r1", 25, "RB", 7), _p("r2", 25, "RB", 9),
                   _p("r3", 25, "RB", 11), _p("r4", 25, "RB", 12),
                   _p("w1", 20, "WR", 7), _p("w2", 20, "WR", 9), _p("w3", 20, "WR", 11),
                   _p("t1", 15, "TE", 13)]
        weeks = lo.bye_collision(players, ROSTER)
        self.assertEqual(weeks[7]["players_out"], 3)
        self.assertEqual(weeks[7]["starters_out"], 3)
        self.assertEqual(weeks[7]["value_lost"], 0.0,
                         "three absences fully covered from the bench cost nothing")

    def test_a_single_uncovered_absence_costs_a_great_deal(self):
        """One starter out, nobody behind him. Fewer bodies, far more damage."""
        players = [_p("q1", 30, "QB", 7), _p("r1", 25, "RB", 9), _p("r2", 24, "RB", 10),
                   _p("w1", 20, "WR", 11), _p("w2", 19, "WR", 13), _p("t1", 15, "TE", 14)]
        weeks = lo.bye_collision(players, ROSTER)
        self.assertEqual(weeks[7]["players_out"], 1)
        self.assertEqual(weeks[7]["value_lost"], 30.0)
        self.assertGreater(weeks[7]["value_lost"], 0)

    def test_simultaneous_loss_is_not_the_sum_of_separate_losses(self):
        """The property that makes this a different function from depth_exposure rather than a
        loop over it. One backup covers whichever RB goes down alone; it cannot cover both."""
        # EIGHT players against seven starting slots, so exactly one is genuinely benched. He
        # covers either RB going down alone -- each separate loss is only the gap between them
        # -- and cannot cover both, so losing the pair empties a slot outright.
        #
        # The bench has to be REAL for this property to exist at all. Two earlier drafts of
        # this fixture measured 49 against 49, both because every rostered player was starting:
        # first with seven players, then with seven again after the FLEX slot quietly absorbed
        # the spare. With no surplus each removal costs exactly that player's value and the two
        # measurements are additive by construction -- lineup_optimizer's EXPOSURE_NO_SURPLUS
        # regime, arrived at here from the other direction.
        players = [_p("q1", 30, "QB", 5),
                   _p("r1", 25, "RB", 7), _p("r2", 24, "RB", 7),
                   _p("r3", 23, "RB", 13), _p("r4", 22, "RB", 14),
                   _p("w1", 20, "WR", 9), _p("w2", 19, "WR", 10), _p("t1", 15, "TE", 11)]
        together = lo.bye_collision(players, ROSTER)[7]["value_lost"]
        separately = sum(
            lo.optimize_lineup(players, lo.slots_from_roster_positions(ROSTER))["total_value"]
            - lo.optimize_lineup([p for p in players if p["id"] != pid],
                                 lo.slots_from_roster_positions(ROSTER))["total_value"]
            for pid in ("r1", "r2")
        )
        self.assertGreater(together, separately,
                           "losing both RBs at once must cost MORE than the two one-at-a-time "
                           "losses added up -- otherwise depth_exposure already answers this "
                           "and the function is redundant")


class AbsenceIsNotZeroTests(unittest.TestCase):
    """The contract this codebase has repaired repeatedly: a number computed over partial data
    must say so, rather than reading as a clean measurement."""

    def test_an_unresolvable_bye_downgrades_EVERY_week_not_just_one(self):
        """A player whose bye is unknown could be out in any week, so no week is verified. A
        basis that marked only the colliding weeks would imply the quiet ones were checked."""
        players = [_p("q1", 30, "QB", 7), _p("r1", 25, "RB", 9), _p("r2", 24, "RB", None),
                   _p("w1", 20, "WR", 11), _p("w2", 19, "WR", 13), _p("t1", 15, "TE", 14)]
        weeks = lo.bye_collision(players, ROSTER)
        self.assertTrue(weeks)
        for week, row in weeks.items():
            with self.subTest(week=week):
                self.assertEqual(row["basis"], lo.BYE_PARTIAL)

    def test_a_fully_resolved_roster_is_measured(self):
        players = [_p("q1", 30, "QB", 7), _p("r1", 25, "RB", 9), _p("r2", 24, "RB", 10),
                   _p("w1", 20, "WR", 11), _p("w2", 19, "WR", 13), _p("t1", 15, "TE", 14)]
        for row in lo.bye_collision(players, ROSTER).values():
            self.assertEqual(row["basis"], "measured")

    def test_no_known_byes_at_all_returns_NOTHING_rather_than_a_clean_sheet(self):
        """An empty result and a result full of zeros are different claims. Only the first is
        true when nothing could be resolved."""
        players = [_p("q1", 30, "QB"), _p("r1", 25, "RB"), _p("w1", 20, "WR")]
        self.assertEqual(lo.bye_collision(players, ROSTER), {})

    def test_an_empty_roster_measures_nothing(self):
        self.assertEqual(lo.bye_collision([], ROSTER), {})


class TeamDerivedResolutionTests(unittest.TestCase):
    """A bye belongs to an NFL team. Reading it per player was why coverage looked poor."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_every_nfl_team_resolves(self):
        byes = self.merger.bye_week_by_team()
        self.assertEqual(len(byes), 32, "expected all 32 NFL teams to carry a bye week")

    def test_no_team_disagrees_with_itself(self):
        """The integrity property, and the reason the map is derived rather than trusted. Two
        players on one team reporting different byes would mean rows are attached to the wrong
        players -- the failure #77 and #78 already found on this path, and one that would be
        invisible downstream because every consumer would just see a plausible week."""
        self.assertEqual(self.merger.bye_week_conflicts(), {})

    def test_the_weeks_are_real_nfl_bye_weeks(self):
        weeks = set(self.merger.bye_week_by_team().values())
        self.assertTrue(weeks <= set(range(4, 15)),
                        f"bye weeks outside the plausible NFL range: {sorted(weeks)}")

    def test_deriving_from_TEAM_covers_more_than_reading_per_PLAYER(self):
        """The non-vacuity check for the whole approach. If the team map did not beat the
        per-player column, the derivation would be complexity for nothing."""
        external, projections = self.merger.external_values, self.merger.projections
        per_player = external[external["bye_week"].notna()][["_name_key", "bye_week"]]
        joined = projections.merge(per_player.drop_duplicates(subset=["_name_key"]),
                                   on="_name_key", how="left")["bye_week"].notna().sum()
        byes = self.merger.bye_week_by_team()
        via_team = projections["team"].isin(byes).sum()
        self.assertGreater(via_team, joined,
                           f"team-derived ({via_team}) must beat per-player ({joined})")


class ItIsDeliberatelyNotAValuationTermTests(unittest.TestCase):
    """The refusal, asserted so it reads as a ruling rather than an oversight -- and so that
    someone wiring it later has to delete a test that explains why not."""

    def test_no_scoring_module_reads_it(self):
        import ast
        from pathlib import Path
        here = Path(__file__).parent
        for module in ("draft_room.py", "pick_synthesis.py", "draft_strategy.py"):
            with self.subTest(module=module):
                tree = ast.parse((here / module).read_text())
                names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
                names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
                self.assertNotIn(
                    "bye_collision", names,
                    f"{module} now reads bye_collision. Measured on the committed baseline: "
                    "the engine's rosters already sit at the pigeonhole floor for an 8-starter "
                    "shape and no swap within 10 universal_value points improves them. If that "
                    "has changed, re-measure and record it -- do not just wire the term.")

    def test_but_something_DOES_read_it(self):
        """The other half. 'Not scored' must not slide into 'not used', which is the exact
        write-only defect (#138) this work was auditing for."""
        import roster_diagnostics
        self.assertIn("bye_collision", roster_diagnostics.TeamDiagnostics.__dataclass_fields__)

    def test_the_function_records_why_it_is_not_scored(self):
        """So the boundary survives someone reading only lineup_optimizer."""
        self.assertIn("not a valuation term", (lo.bye_collision.__doc__ or "").lower())


if __name__ == "__main__":
    unittest.main()
