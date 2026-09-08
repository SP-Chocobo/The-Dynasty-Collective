"""#211: roster worth is what a chair OWNS, and the lineup total travels with its contamination.

The defect these pin: `starter_value` sums `universal_value` -- an asset LEVEL -- across a
STARTING LINEUP, while 83.8% of a typical pool's values are negative and `optimize_lineup` has
no "leave the slot empty" move. A roster thin at a position is forced to start deep negatives,
so the number ranks POSITIONAL BREADTH, not roster quality. The battery printed
`12T_ppr_mode_upside starters -205.4` and its docstring called that "the roster-quality number".

No finding changes. This is a reported line, not a verdict.
"""

from __future__ import annotations

import unittest

import draft_battery as db
import lineup_optimizer as lo


class _Trajectory:
    def __init__(self, rosters):
        self._rosters = rosters

    def final_rosters(self):
        return self._rosters


LEAGUE = {"roster_positions": ["RB", "WR", "BN"]}
DB = {"rb_good": {"position": "RB", "fantasy_positions": ["RB"]},
      "rb_bad": {"position": "RB", "fantasy_positions": ["RB"]},
      "wr_good": {"position": "WR", "fantasy_positions": ["WR"]}}


class TheOptimizerCannotDeclineToStartSomeoneTests(unittest.TestCase):
    """The premise. If this changes, everything below is void."""

    def test_a_below_replacement_player_is_started_rather_than_the_slot_left_empty(self):
        solved = lo.optimize_lineup(
            [{"id": "wr_good", "value": 50.0, "eligible": {"WR"}},
             {"id": "rb_bad", "value": -80.0, "eligible": {"RB"}}],
            [{"slot_id": "RB_0", "eligible": {"RB"}}, {"slot_id": "WR_1", "eligible": {"WR"}}])
        self.assertEqual(solved["total_value"], -30.0)


class RosterWorthIsWhatTheChairOwnsTests(unittest.TestCase):

    def test_the_roster_worth_basis_names_total_value_not_the_lineup(self):
        self.assertIn("total_value", db.ROSTER_WORTH_BASIS)
        self.assertIn("LEVEL", db.ROSTER_WORTH_BASIS)

    def test_strength_reports_a_total_value_spread_as_well_as_a_lineup_one(self):
        strength = db.roster_strength(
            _Trajectory({"1": ["rb_good", "wr_good"], "2": ["rb_bad", "wr_good"]}),
            LEAGUE, DB, {"rb_good": 40.0, "rb_bad": -80.0, "wr_good": 50.0})
        for key in ("total_value_min", "total_value_max", "total_value_spread",
                    "roster_worth_basis"):
            self.assertIn(key, strength, f"{key} is what answers 'what is this roster worth'")

    def test_the_forced_negative_starter_is_counted(self):
        strength = db.roster_strength(
            _Trajectory({"2": ["rb_bad", "wr_good"]}),
            LEAGUE, DB, {"rb_bad": -80.0, "wr_good": 50.0})
        per = strength["per_roster"]["2"]
        self.assertEqual(per["forced_negative_starters"], 1,
                         "the -80 RB was started because the slot could not be left empty")
        self.assertEqual(per["starter_value"], -30.0)
        self.assertEqual(per["total_value"], -30.0)

    def test_a_clean_lineup_reports_zero_forced_negatives_not_absence(self):
        """A measured zero and 'not measured' are different answers (the absence contract)."""
        strength = db.roster_strength(
            _Trajectory({"1": ["rb_good", "wr_good"]}),
            LEAGUE, DB, {"rb_good": 40.0, "wr_good": 50.0})
        self.assertEqual(strength["per_roster"]["1"]["forced_negative_starters"], 0)
        self.assertEqual(strength["per_roster"]["1"]["starter_value"], 90.0)

    def test_the_lineup_total_can_rank_a_worse_roster_higher(self):
        """The actual defect, demonstrated: breadth beats quality under starter_value.

        THE FIXTURE MATTERS AND MY FIRST ONE DID NOT WORK. With as many players as slots,
        total_value and starter_value are arithmetically the SAME NUMBER -- every player is
        started -- so no fixture of that shape can show them disagreeing. The divergence needs
        BENCH VALUE, which is the whole point: total counts what you own, the lineup does not.

        QUALITY owns four good WRs and one unplayable RB. It must field an RB, so the -250
        lands in its lineup total. BREADTH owns two mediocre players that exactly fill its two
        slots. QUALITY is worth 150 to BREADTH's 60 -- and starter_value ranks it 210 BELOW.
        """
        league = {"roster_positions": ["RB", "WR", "BN", "BN", "BN"]}
        players_db = {n: {"position": pos, "fantasy_positions": [pos]} for n, pos in (
            ("wr_a", "WR"), ("wr_b", "WR"), ("wr_c", "WR"), ("wr_d", "WR"),
            ("rb_unplayable", "RB"), ("rb_ok", "RB"), ("wr_ok", "WR"))}
        values = {"wr_a": 100.0, "wr_b": 100.0, "wr_c": 100.0, "wr_d": 100.0,
                  "rb_unplayable": -250.0, "rb_ok": 30.0, "wr_ok": 30.0}
        strength = db.roster_strength(
            _Trajectory({"quality": ["wr_a", "wr_b", "wr_c", "wr_d", "rb_unplayable"],
                         "breadth": ["rb_ok", "wr_ok"]}),
            league, players_db, values)
        q, b = strength["per_roster"]["quality"], strength["per_roster"]["breadth"]

        self.assertEqual(q["total_value"], 150.0)
        self.assertEqual(b["total_value"], 60.0)
        self.assertGreater(q["total_value"], b["total_value"],
                           "quality owns more -- that is the roster-worth answer")

        self.assertEqual(q["starter_value"], -150.0, "100 started at WR, -250 forced at RB")
        self.assertEqual(b["starter_value"], 60.0)
        self.assertLess(q["starter_value"], b["starter_value"],
                        "yet the LINEUP total ranks it lower -- that is #211, not a tie-break")

        self.assertEqual(q["forced_negative_starters"], 1,
                         "and the companion says exactly why the lineup number inverted")
        self.assertEqual(b["forced_negative_starters"], 0)


class TheConsoleLineCarriesTheCompanionTests(unittest.TestCase):

    def test_a_forced_negative_is_named_in_the_printed_clause(self):
        import run_draft_battery as rdb
        self.assertIn("#211", rdb._forced_clause({"forced_negative_starters": 3}))
        self.assertIn("3", rdb._forced_clause({"forced_negative_starters": 3}))

    def test_a_clean_lineup_adds_no_clause_and_an_unmeasured_one_says_so(self):
        import run_draft_battery as rdb
        self.assertEqual(rdb._forced_clause({"forced_negative_starters": 0}), "")
        self.assertIn("not measured", rdb._forced_clause({}))

    def test_the_printed_line_leads_with_roster_worth(self):
        import inspect
        import run_draft_battery as rdb
        src = inspect.getsource(rdb.main)
        self.assertIn("total_value_min", src, "the worth line must be printed")
        self.assertIn("_forced_clause(strength)", src,
                      "and the lineup number must never print without its companion")


# MUTATION PASS recorded after the guards were written -- see the commit message.

if __name__ == "__main__":
    unittest.main()
