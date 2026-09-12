"""#213: an arm's rulebook must be able to price the players the arm drafts.

THE DEFECT. `build_mock_league` emitted a ONE-KEY scoring dict -- `{"rec": <0.0|0.5|1.0>}` --
and once #204 made the battery pass `sleeper_projections`, `score_projection` scored every stat
line against that single key. Measured on the committed capture:

    player                real rulebook   {"rec": 1.0}   {"rec": 0.0}
    Josh Allen (QB)              372.46            0.0            0.0
    C. McCaffrey (RB)            413.24    86.22 (= his catches)   0.0
    J. Smith-Njigba (WR)         395.69   123.88 (= his catches)   0.0
    Jack Campbell (LB)           171.88            0.0            0.0

    players priced                  835            431              0
    IDP priced                      299              1              0

So 27 of 33 battery arms measured a league in which quarterbacks score nothing and receivers
are paid one point per catch, on ONE shared replacement number line; the standard arms priced
nobody at all and silently fell back to vendor-only.

SCOPE. Harness only. The live Draft Room (app.py) passes the real league's scoring_settings and
was never affected. The Mock Draft sandbox uses the stub but never passes sleeper_projections,
so nothing there ever reaches score_projection -- it is inert, and `base_scoring=None` keeps it
byte-identical rather than changing a shipped surface to fix a harness bug.
"""

from __future__ import annotations

import unittest

import draft_battery as db
import draft_room as dr
import run_draft_battery as rdb


class TheSandboxIsUnchangedTests(unittest.TestCase):

    def test_without_a_base_the_league_is_exactly_what_it_always_was(self):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                      te_premium=False, dynasty=True)
        self.assertEqual(league["scoring_settings"], {"rec": 1.0},
                         "the sandbox never scores stat lines; changing it would be a shipped "
                         "behaviour change made to fix a harness defect")

    def test_te_premium_still_overlays_without_a_base(self):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                      te_premium=True, dynasty=True)
        self.assertEqual(league["scoring_settings"]["bonus_rec_te"], dr.MOCK_TE_PREMIUM_BONUS)


class TheOverlayIsTheOnlyThingThatVariesTests(unittest.TestCase):

    def test_the_base_rulebook_survives_and_rec_is_overlaid_on_top(self):
        base = {"pass_yd": 0.04, "pass_td": 4.0, "idp_tkl_solo": 1.0}
        league = dr.build_mock_league(teams=12, superflex=False, scoring="half_ppr",
                                      te_premium=False, dynasty=True, base_scoring=base)
        sc = league["scoring_settings"]
        self.assertEqual(sc["pass_td"], 4.0, "a QB must still be able to score")
        self.assertEqual(sc["idp_tkl_solo"], 1.0, "an IDP must still be able to score")
        self.assertEqual(sc["rec"], 0.5, "and the arm's own axis is what varies")

    def test_the_base_never_overrides_the_arms_own_axis(self):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="standard",
                                      te_premium=False, dynasty=True,
                                      base_scoring={"rec": 1.0, "pass_td": 4.0})
        self.assertEqual(league["scoring_settings"]["rec"], 0.0,
                         "a standard arm is standard even if the base league is PPR")

    def test_every_battery_arm_carries_the_real_rulebook(self):
        real = rdb.scoring_settings_from_capture()
        matrix = db.league_matrix(real)
        # CORRECTED (#251). This was `assertEqual(len(matrix), 33)`. The count is here for
        # non-vacuity -- so the loop below cannot pass over an empty matrix -- and an EQUALITY
        # made it something else: a standing prohibition on adding configuration coverage, which
        # is exactly what the owner's ruling requires. A floor does the non-vacuity job without
        # forbidding the thing the battery exists to grow.
        self.assertGreaterEqual(len(matrix), 33)
        for arm in matrix:
            sc = arm["league"]["scoring_settings"]
            self.assertGreater(len(sc), 10,
                               f"{arm['label']} is drafting on a stub rulebook ({len(sc)} keys)")
            self.assertIn("rec", sc)

    def test_the_hand_built_idp_arms_get_it_too(self):
        """These three are dicts written out in full, so they are where a base is easiest to
        forget -- and HEAVY_IDP is the arm whose findings were misread because of it."""
        real = rdb.scoring_settings_from_capture()
        matrix = {a["label"]: a for a in db.league_matrix(real)}
        for label in ("HEAVY_IDP", "LIGHT_IDP", "4WR_TE_PREMIUM"):
            sc = matrix[label]["league"]["scoring_settings"]
            self.assertGreater(len(sc), 10, f"{label} carries a stub rulebook")


class TheCensusRefusesARulebookThatCannotPriceTests(unittest.TestCase):

    def setUp(self):
        self.season = rdb.season_projections_from_capture()
        self.players_db, _ = rdb.build_players_db_from_capture()

    def test_the_real_rulebook_prices_every_position_that_has_stat_lines(self):
        census = rdb.pricing_census(self.season, self.players_db,
                                    rdb.scoring_settings_from_capture())
        self.assertEqual(rdb.positions_the_rulebook_cannot_price(census), [],
                         "the capture's own rulebook must be able to price the capture")

    def test_the_one_key_stub_is_refused_and_the_positions_are_named(self):
        census = rdb.pricing_census(self.season, self.players_db, {"rec": 1.0})
        bad = rdb.positions_the_rulebook_cannot_price(census)
        for pos in ("QB", "LB", "DL", "K", "DEF"):
            self.assertIn(pos, bad, f"{pos} scores nothing under a receptions-only rulebook")

    def test_the_standard_stub_prices_literally_nobody(self):
        census = rdb.pricing_census(self.season, self.players_db, {"rec": 0.0})
        bad = rdb.positions_the_rulebook_cannot_price(census)
        self.assertIn("WR", bad)
        self.assertIn("RB", bad)
        self.assertTrue(all(r["priced"] == 0 for r in census.values()))

    def test_the_census_separates_absence_from_a_measured_zero(self):
        """A position with NO stat lines is not a rulebook failure -- it is an empty pool, and
        the two must not be conflated (the absence contract, in the guard itself)."""
        census = rdb.pricing_census(self.season, self.players_db,
                                    rdb.scoring_settings_from_capture())
        for pos, row in census.items():
            self.assertIn("stat_lines", row)
            self.assertIn("priced", row)
            if row["stat_lines"] == 0:
                self.assertNotIn(pos, rdb.positions_the_rulebook_cannot_price(census),
                                 "an empty pool is not an unpriceable rulebook")

    def test_the_accessor_raises_rather_than_defaulting_to_an_empty_rulebook(self):
        import json, pathlib, tempfile
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "cap.json"
            p.write_text(json.dumps({"league_shape": {}}), encoding="utf-8")
            with self.assertRaises(ValueError):
                rdb.scoring_settings_from_capture(p)


class TheDriverRefusesTests(unittest.TestCase):

    def test_the_driver_refuses_rather_than_warning(self):
        import inspect
        src = inspect.getsource(rdb.main)
        self.assertIn("REFUSING TO RUN (#213)", src)
        self.assertIn("raise SystemExit", src,
                      "a warning would scroll past in a 14,000-second run; this must stop it")
        self.assertIn("scoring_settings_from_capture()", src)
        self.assertIn("pricing_census", src)


if __name__ == "__main__":
    unittest.main()
