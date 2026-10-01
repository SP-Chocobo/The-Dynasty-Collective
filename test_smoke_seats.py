"""#285: the smoke-seat field has to be a FIELD, not the engine wearing four hats.

Every guard here defends a property the measurement depends on, and three of them defend against
a mistake this harness actually made rather than one it might make.
"""

from __future__ import annotations

import pathlib
import unittest

import run_roster_proof as rp
import run_smoke_seats as ss


class EveryStyleDraftsFromTheFullPool(unittest.TestCase):
    """THE PROPERTY THAT MAKES THEM CONTROLS AT ALL.

    `evidence/survival_calibration/calibrate.py` has five varied policies that choose from
    `build_snapshot`'s NARROWED shortlist. Reusing those here was the cheap path and would have
    been fatal: opponents restricted to the engine's own shortlist can never punish it for
    undervaluing someone, because the engine already removed everyone it judged not worth
    considering. "Is the engine good at picking from its own shortlist" is close to a tautology.
    """

    @staticmethod
    def _names_used(fn):
        """Every identifier a function's CODE touches, docstrings and comments excluded.

        SCANNING RAW TEXT IS THE MISTAKE `#200` ALREADY RECORDS, and both of this class's
        guards made it on the first attempt: they matched `build_snapshot` and `board[0]`
        inside the very docstrings EXPLAINING why those must not be called, so a passing
        implementation failed its own test. A guard that reads prose is testing the comments.
        """
        import ast
        import inspect
        import textwrap
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used.add(node.id)
            elif isinstance(node, ast.Attribute):
                used.add(node.attr)
        return used

    def test_no_style_reaches_the_engine_or_a_narrowed_board(self):
        for name, fn in sorted(ss.STYLES.items()):
            used = self._names_used(fn)
            for forbidden in ("build_snapshot", "candidates", "board"):
                self.assertNotIn(forbidden, used,
                                 f"style {name!r} touches {forbidden!r}: it is no longer an "
                                 f"independent control, it is the engine in a different hat")

    def test_the_run_follower_fallback_is_policy_native(self):
        """calibrate.py's equivalent falls back to `board[0]` -- the ENGINE's own top candidate.
        A control that defers to the thing under test whenever its own rule does not fire is
        partly that thing, and it inflates agreement."""
        used = self._names_used(ss._style_run_follower)
        self.assertIn("_style_points_need", used, "its fallback must be a policy, not the engine")
        self.assertNotIn("board", used)


class TheAdmissionGateIsEnforcedAndNotJustLogged(unittest.TestCase):
    """THE BUG THIS FILE EXISTS FOR. The gate ran, printed `excluded ['run_follower']`, and then
    `style_by_seat` dealt from all of STYLES anyway -- so a style the gate had rejected for being
    unable to field a legal lineup sat in the field regardless, contaminating a measured 8/12.
    A gate whose verdict nothing consumes is a log line."""

    def test_only_admitted_styles_are_dealt(self):
        seats = [str(i) for i in range(1, 13)]
        assigned = ss.style_by_seat(seats, "1", admitted=["adp", "points_need"])
        self.assertEqual(set(assigned.values()), {"adp", "points_need"})
        self.assertNotIn("run_follower", set(assigned.values()))

    def test_the_engine_seat_is_never_dealt_a_style(self):
        seats = [str(i) for i in range(1, 13)]
        assigned = ss.style_by_seat(seats, "7", admitted=sorted(ss.STYLES))
        self.assertNotIn("7", assigned)
        self.assertEqual(len(assigned), 11, "every non-engine seat gets exactly one style")

    def test_an_empty_field_refuses_rather_than_reporting_a_number(self):
        """If the gate excludes everything there is no field left, and any number produced would
        be about the styles rather than about the engine."""
        with self.assertRaises(SystemExit):
            ss.style_by_seat(["1", "2"], "1", admitted=[])


class TheUndraftedSentinelIsExcluded(unittest.TestCase):
    """4,506 of 5,346 capture entries carry only an ADP field, frequently the 18000.0 'undrafted'
    marker. Ranking on it unfiltered sorts undrafted players as the most desirable in the draft,
    which is the easiest way to build a strawman opponent by accident."""

    def test_the_sentinel_never_enters_the_ranking(self):
        season = {"a": {"adp_dd_ppr": 12.5}, "b": {"adp_dd_ppr": ss.ADP_UNDRAFTED_SENTINEL},
                  "c": {"adp_dd_ppr": 300.0}, "d": {"gp": 17}}
        table, excluded = ss.adp_table(season)
        self.assertEqual(set(table), {"a", "c"})
        self.assertEqual(excluded, 1)

    def test_a_row_with_no_adp_is_absent_not_zero(self):
        """#187: absence is not a value. A missing ADP must not rank as the best ADP."""
        table, _ = ss.adp_table({"d": {"gp": 17}})
        self.assertEqual(table, {})


class TheHarnessIsReusedNotReimplemented(unittest.TestCase):
    """#126: one home for a vocabulary. The pool restriction, the rulers, the lineup solve and
    the comparison all already exist in run_roster_proof and are imported."""

    def test_rulers_and_comparison_come_from_the_proof(self):
        self.assertEqual(rp.RULERS, ("cdme", "points"))
        self.assertEqual(rp.COMPARE_ON["points"], "starter_value")
        source = pathlib.Path("run_smoke_seats.py").read_text(encoding="utf-8")
        self.assertNotIn("def score_roster", source, "the lineup solve has one home")
        self.assertNotIn("def compare(", source, "the comparison has one home")
        self.assertIn("import run_roster_proof as rp", source)

    def test_the_incumbent_control_is_still_in_the_field(self):
        """`points_need` IS run_roster_proof's control, delegated to rather than reimplemented.
        Its presence is what makes this run comparable to #205/#245 instead of a fresh scale."""
        import inspect
        self.assertIn("rp.control_pick", inspect.getsource(ss._style_points_need))


class TheStarterFloorExists(unittest.TestCase):
    """Rule 6, earned: a projection-only control took 24 CONSECUTIVE QBs in a 1QB league and the
    engine "beat" it by +503%, measuring nothing except that one arm knew what a lineup was."""

    def test_the_floor_never_empties_the_pool(self):
        """It restricts, and when the restriction would leave NOTHING it returns the pool
        unrestricted -- a floor that can empty the board is a crash, not a floor.

        THE FIRST VERSION OF THIS TEST WAS A DECORATION, and mutation found it. It passed
        `slots=[]`, so `unmet_slot_positions` returned an empty set, the function took its early
        return, and the `eligible or available` line it claims to guard was never reached --
        replacing that line with a bare `eligible` left the whole suite green. The slot list
        below is non-empty and UNFILLABLE from the pool, which is the only arrangement that
        actually exercises the fallback.
        """
        db = {"y": {"position": "RB"}}
        slots = [{"slot_id": "QB1", "eligible": {"QB"}}]
        need = rp.unmet_slot_positions([], db, slots)
        self.assertEqual(need, {"QB"}, "non-vacuity: the need must be real, or the floor is idle")
        out = ss._cover_starters_first(["y"], [], db, slots)
        self.assertEqual(out, ["y"],
                         "no RB fills a QB slot, so the restriction empties -- and the floor "
                         "must hand back the unrestricted pool rather than nothing")

    def test_the_floor_does_restrict_when_it_can(self):
        """The other half: when the need IS fillable the pool is genuinely narrowed, otherwise
        the previous test would pass against a floor that does nothing at all."""
        db = {"x": {"position": "QB"}, "y": {"position": "RB"}}
        slots = [{"slot_id": "QB1", "eligible": {"QB"}}]
        out = ss._cover_starters_first(["x", "y"], [], db, slots)
        self.assertEqual(out, ["x"], "only the QB fills the unmet QB slot")

    def test_multi_position_eligibility_is_honoured(self):
        """#172: a player listed RB/WR is eligible at both; collapsing him to his primary would
        bench him out of a FLEX he can legally fill."""
        db = {"z": {"fantasy_positions": ["RB", "WR"], "position": "RB"}}
        self.assertEqual(ss._positions_of("z", db), {"RB", "WR"})


class TheFieldsPicksAreAttributableToAStyle(unittest.TestCase):
    """#285 RULE 6: a pooled round-one counter cannot say WHOSE picks those were, and that is
    the one question that separates a real win from beating a strawman."""

    PICKS = [
        {"round": 1, "style": "cdme", "position": "RB"},
        {"round": 1, "style": "adp", "position": "WR"},
        {"round": 1, "style": "points_need", "position": "QB"},
        {"round": 2, "style": "cdme", "position": "WR"},
        {"round": 2, "style": "adp", "position": "QB"},
        {"round": 2, "style": "points_need", "position": "QB"},
    ]

    def test_every_style_that_picked_appears(self):
        comp = ss.composition_by_style(self.PICKS)
        self.assertEqual(sorted(comp), ["adp", "cdme", "points_need"])

    def test_the_engine_is_attributed_like_any_other_seat(self):
        """The engine's picks carry the style name `cdme`, so its composition is readable
        beside the field's rather than being a special case."""
        comp = ss.composition_by_style(self.PICKS)
        self.assertEqual(comp["cdme"]["round_one"], {"RB": 1})
        self.assertEqual(comp["cdme"]["all_rounds"], {"RB": 1, "WR": 1})
        self.assertEqual(comp["cdme"]["picks"], 2)

    def test_round_one_is_a_subset_of_all_rounds_not_a_copy(self):
        """The regression this guards: `adp` takes WR in round one and QB in round two. A
        round-one counter that quietly counted every round would report QB for it, and the
        strawman check would read the exact opposite of the truth."""
        comp = ss.composition_by_style(self.PICKS)
        self.assertEqual(comp["adp"]["round_one"], {"WR": 1})
        self.assertEqual(comp["adp"]["all_rounds"], {"WR": 1, "QB": 1})

    def test_pooling_sums_across_seat_runs_and_invents_nothing(self):
        one = ss.composition_by_style(self.PICKS)
        pooled = ss.pool_composition([one, one, one])
        self.assertEqual(sorted(pooled), sorted(one))
        for style, rec in pooled.items():
            self.assertEqual(rec["picks"], one[style]["picks"] * 3)
            for field in ("round_one", "all_rounds"):
                self.assertEqual(rec[field],
                                 {p: n * 3 for p, n in one[style][field].items()})

    def test_the_report_actually_carries_it(self):
        """Computing it and not writing it down is how this gap opened the first time: the
        run recorded a pooled round-one counter and the attribution was unrecoverable."""
        source = pathlib.Path("run_smoke_seats.py").read_text(encoding="utf-8")
        self.assertIn('"composition_by_style": pool_composition(composition)', source)


if __name__ == "__main__":
    unittest.main()
