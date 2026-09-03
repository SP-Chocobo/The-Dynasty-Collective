"""#142 / #138 / #139: bye weeks as a measured absence, and the decision not to price them.

Two things are covered, and the second is the one that will look wrong to a later reader:

  THE MECHANISM. bye_collision removes every player on a given bye SIMULTANEOUSLY and re-solves
  the lineup. Simultaneous loss is not the sum of separate losses -- the bench covers the first
  hole and has nothing left for the second -- which is exactly what depth_exposure's
  one-at-a-time removal cannot express and what a headcount gets backwards.

  THE REFUSAL. It feeds no valuation, and the reason is a CATEGORY argument rather than the
  magnitude one this file originally carried. Bye weeks are reassigned every season, so a
  collision belongs to the (player, season) pair and dissolves in months while the dynasty
  asset outlives it. A quantity whose lifetime is shorter than the asset's horizon cannot price
  that asset at ANY magnitude -- which is why the measured effect (worst-week losses of 41-127
  trade_value, a reachable tail near 7 bpa) does not reopen the question.

  That also rules out a draft-time FLAG, which an earlier version of this work was about to
  recommend: a flag describes a transient property of a permanent decision, and in a startup
  draft it invites trading multi-year asset value for one season's tidiness. A candidate-level
  penalty function was built for that flag and then deleted with it.

  Where the quantity legitimately lives is a single-season surface: roster_diagnostics, whose
  questions are this-season questions.
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
                    f"{module} now reads bye_collision. This is excluded on a CATEGORY rule, "
                    "not a magnitude one, so a new measurement showing a large effect does not "
                    "reopen it: the NFL reassigns bye weeks every season, so a collision is a "
                    "property of the (player, season) pair and dissolves in months while a "
                    "dynasty asset does not. A quantity whose lifetime is shorter than the "
                    "asset's horizon cannot price that asset at any magnitude. See "
                    "CDME_CONTRACTS.md's team_acquisition_value invariants.")

    def test_but_something_DOES_read_it(self):
        """The other half. 'Not scored' must not slide into 'not used', which is the exact
        write-only defect (#138) this work was auditing for."""
        import roster_diagnostics
        self.assertIn("bye_collision", roster_diagnostics.TeamDiagnostics.__dataclass_fields__)

    def test_the_function_records_why_it_is_not_scored(self):
        """So the boundary survives someone reading only lineup_optimizer."""
        self.assertIn("not a valuation term", (lo.bye_collision.__doc__ or "").lower())



class StaggeredVersusLayeredTests(unittest.TestCase):
    """The mechanism underneath the shape, in the owner's own terms.

    "If you spread out byes, you're either playing your starters, or your first-up depth. If
    there's more byes in one week, you need to use deeper, less producing assets."

    That is why concentration costs more than a headcount suggests, and it is not an assumption
    -- bench value decays with rank, so reaching to depth 3 once is worse than reaching to
    depth 1 three times, even though both are three absences. The assignment solver already
    knows which bodies get promoted; these tests pin that it SAYS so."""

    # Same players, same values, same total absences -- only the WEEKS differ.
    BASE = [(30, "QB"), (25, "RB"), (24, "RB"), (20, "WR"), (19, "WR"), (15, "TE"), (14, "RB")]
    BENCH = [(13, "RB"), (9, "WR"), (4, "RB")]

    def _roster(self, byes):
        return [{"id": f"p{i}", "value": value, "eligible": {position}, "bye": bye}
                for i, ((value, position), bye) in enumerate(zip(self.BASE + self.BENCH, byes))]

    STAGGERED = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    LAYERED = [7, 7, 7, 8, 9, 10, 11, 12, 13, 14]

    def test_staggered_byes_never_reach_past_first_up_depth(self):
        weeks = lo.bye_collision(self._roster(self.STAGGERED), ROSTER)
        for week, row in weeks.items():
            with self.subTest(week=week):
                self.assertLessEqual(row["bench_used"], 1,
                                     "a spread bye profile should promote at most one body "
                                     "per week -- that is what spreading it buys")

    def test_layering_the_same_absences_consumes_several_at_once(self):
        weeks = lo.bye_collision(self._roster(self.LAYERED), ROSTER)
        self.assertEqual(weeks[7]["starters_out"], 3)
        self.assertGreater(weeks[7]["bench_used"], 1)

    def test_and_that_costs_more_than_the_same_absences_spread_out(self):
        """The claim the whole distinction rests on. Identical players, identical number of
        absences, worse outcome -- purely from when they land."""
        staggered = lo.bye_collision(self._roster(self.STAGGERED), ROSTER)
        layered = lo.bye_collision(self._roster(self.LAYERED), ROSTER)
        self.assertGreater(max(r["value_lost"] for r in layered.values()),
                           max(r["value_lost"] for r in staggered.values()))

    def test_a_week_that_promotes_nobody_consumes_no_bench(self):
        """No promotion is not a cheap promotion. The QB has no backup here, so his week costs
        full value and consumes nothing -- both facts, separately reported."""
        weeks = lo.bye_collision(self._roster(self.STAGGERED), ROSTER)
        self.assertEqual(weeks[5]["bench_used"], 0)
        self.assertEqual(weeks[5]["bench_value_used"], 0.0)
        self.assertEqual(weeks[5]["value_lost"], 30.0)

    def test_consuming_your_best_body_and_your_worst_are_different_depletions(self):
        """Why a count alone is not enough: one promotion can spend a near-starter or a scrub,
        and the roster is in different shape afterwards."""
        weeks = lo.bye_collision(self._roster(self.LAYERED), ROSTER)
        self.assertGreater(weeks[7]["bench_value_used"], 0)
        self.assertEqual(weeks[7]["bench_used"], 2)


class FlexChainsAreHandledAndNoDepthRankIsClaimedTests(unittest.TestCase):
    """The owner's correction, and the field it removed.

    "Just because your bye is a wr, a rb sometimes can cover in a flex, shift a prior flexed wr
    up to the wr slot."

    That is exactly right and the solver already does it -- which is why value_lost is sound
    and why a DEPTH RANK is not. Two rank definitions were built and both were unsound: a
    per-position rank calls the covering RB "depth 1 among RBs" when he is not covering an RB
    hole at all, and a global rank calls him "depth 2" whenever a better bench body went
    unused, implying waste an optimal solve did not commit."""

    ROSTER_ROWS = [
        {"id": "qb", "value": 30, "eligible": {"QB"}, "bye": 5},
        {"id": "rb1", "value": 25, "eligible": {"RB"}, "bye": 6},
        {"id": "rb2", "value": 24, "eligible": {"RB"}, "bye": 7},
        {"id": "wr1", "value": 22, "eligible": {"WR"}, "bye": 9},
        {"id": "wr2", "value": 21, "eligible": {"WR"}, "bye": 10},
        {"id": "te", "value": 15, "eligible": {"TE"}, "bye": 11},
        {"id": "wr3", "value": 18, "eligible": {"WR"}, "bye": 12},
        {"id": "bench_rb3", "value": 17, "eligible": {"RB"}, "bye": 13},
        {"id": "bench_wr4", "value": 6, "eligible": {"WR"}, "bye": 14},
    ]

    def test_a_WR_hole_is_covered_through_the_flex_by_an_RB(self):
        """The chain itself: wr3 slides FLEX -> WR, and a bench RB takes the vacated FLEX."""
        slots = lo.slots_from_roster_positions(ROSTER)
        without = lo.optimize_lineup(
            [p for p in self.ROSTER_ROWS if p["id"] != "wr1"], slots)
        placed = {a["player_id"]: a["slot_id"] for a in without["assignments"]}
        self.assertIn("bench_rb3", placed, "the bench RB should be used to cover a WR absence")
        self.assertTrue(placed["bench_rb3"].startswith("FLEX"))
        self.assertTrue(placed["wr3"].startswith("WR"),
                        "the flexed WR should shift up into the vacated WR slot")

    def test_the_chain_makes_the_week_far_cheaper_than_the_naive_reading(self):
        """Naive: best bench WR is worth 6, so losing a 22 costs 16. Actual: 5."""
        week = lo.bye_collision(self.ROSTER_ROWS, ROSTER)[9]
        self.assertEqual(week["value_lost"], 5.0)
        self.assertLess(week["value_lost"], 22.0 - 6.0)

    def test_no_depth_rank_is_reported_at_all(self):
        """The removal, asserted so it is not helpfully restored. Both definitions tried were
        plausible numbers with no sound meaning under flex substitution."""
        week = lo.bye_collision(self.ROSTER_ROWS, ROSTER)[9]
        for field in week:
            self.assertNotIn("depth", field,
                             "a depth RANK is undefined once FLEX chains route coverage across "
                             "positions -- report the count and value consumed instead")


class ConcentrationSeparatesShapeFromSeverityTests(unittest.TestCase):
    """Two rosters can lose the same total and be in completely different trouble."""

    def _roster(self, byes):
        rows = [(30, "QB"), (25, "RB"), (24, "RB"), (20, "WR"), (19, "WR"), (15, "TE"), (14, "RB")]
        return [{"id": f"p{i}", "value": value, "eligible": {position}, "bye": bye}
                for i, ((value, position), bye) in enumerate(zip(rows, byes))]

    def test_layering_raises_concentration_at_an_identical_total(self):
        staggered = lo.bye_concentration(self._roster([5, 6, 7, 8, 9, 10, 11]), ROSTER)
        layered = lo.bye_concentration(self._roster([7, 7, 7, 8, 9, 10, 11]), ROSTER)
        self.assertEqual(staggered["total_loss"], layered["total_loss"],
                         "the fixtures must hold total damage fixed, or this measures severity")
        self.assertGreater(layered["concentration"], staggered["concentration"])

    def test_it_names_the_week_rather_than_only_scoring_the_shape(self):
        """Traceability is the point. A recommendation that cannot say WHICH week is not
        actionable, and a bare ratio is not a reason."""
        result = lo.bye_concentration(self._roster([7, 7, 7, 8, 9, 10, 11]), ROSTER)
        self.assertEqual(result["worst_week"], 7)
        self.assertIn(7, result["weeks"])

    def test_a_roster_with_no_bye_damage_has_NO_shape_rather_than_a_flat_one(self):
        """None, not 0.0. Zero concentration would rank a roster with nothing at stake as
        perfectly staggered -- a claim about a distribution that does not exist."""
        rows = [{"id": "a", "value": 10, "eligible": {"QB"}}]
        self.assertIsNone(lo.bye_concentration(rows, ROSTER)["concentration"])
        self.assertEqual(lo.bye_concentration([], ROSTER)["basis"], lo.BYE_UNKNOWN)

if __name__ == "__main__":
    unittest.main()
