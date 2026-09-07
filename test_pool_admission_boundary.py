"""Who gets a row in the draft pool at all -- the owner's five-clause union (#193).

This is the boundary the paid vendor used to own. The old rule admitted a player only if a
ranking export had both matched him and published a number, which made a third party's
coverage decision the outer edge of this app's player universe -- not a pricing limit, an
EXISTENCE limit. Measured against the captured Sleeper universe it dropped 451-466 players
carrying a real league-scored projection, overwhelmingly players whose situation changed after
the vendor file was cut.

The union that replaced it is deliberately generous, and the tests here are the contract:
every clause admits ON ITS OWN, a not-currently-playing status is a freshness rule rather than
a gate, and a player admitted with nothing to price him is a legitimate row that says so.

Every test in this file was mutation-checked -- see MUTATIONS at the bottom.
"""
import unittest

import draft_room as dr


class _StubMerger:
    """A merger that matches nobody. Isolates the four LIVE clauses from the vendor clause:
    with every merge failing, anything admitted here got in on Sleeper's own fields, which is
    exactly the property the widening exists to provide."""

    def __init__(self, matched=False, trade_value=None, projection=None):
        self._m = {"matched": matched, "trade_value": trade_value, "projection": projection}

    def merge_player(self, name, position=None, team=None):
        return dict(self._m)


def _match(matched=False, trade_value=None, projection=None):
    return {"matched": matched, "trade_value": trade_value, "projection": projection}


class EachClauseAdmitsOnItsOwnTests(unittest.TestCase):
    """A union means any one signal is sufficient. Each test holds the other three off."""

    def test_a_league_scored_projection_admits(self):
        info = {"position": "WR", "status": "Active", "years_exp": 6, "team": None}
        self.assertTrue(dr._admits_to_pool(info, 142.5, _match()))

    def test_a_rookie_admits_with_no_team_and_no_number(self):
        # The owner's case: a rookie cut to a practice squad has no NFL team listed and no
        # projection, and in a dynasty league is one of the most taxi-relevant players alive.
        info = {"position": "RB", "status": "Active", "years_exp": 0, "team": None}
        self.assertTrue(dr._admits_to_pool(info, None, _match()))

    def test_being_on_an_nfl_team_admits(self):
        info = {"position": "LB", "status": "Active", "years_exp": 4, "team": "KC"}
        self.assertTrue(dr._admits_to_pool(info, None, _match()))

    def test_a_vendor_number_still_admits(self):
        # The OLD rule, retained as a clause so the change is purely widening.
        info = {"position": "TE", "status": "Active", "years_exp": 3, "team": None}
        self.assertTrue(dr._admits_to_pool(info, None, _match(True, trade_value=12.0)))
        self.assertTrue(dr._admits_to_pool(info, None, _match(True, projection=88.0)))

    def test_nothing_at_all_is_not_admitted(self):
        # Non-vacuity for every test above: the union is not simply "yes".
        info = {"position": "WR", "status": "Active", "years_exp": 5, "team": None}
        self.assertFalse(dr._admits_to_pool(info, None, _match()))
        self.assertFalse(dr._admits_to_pool(info, None, _match(True)))


class AbsenceIsNotRookieTests(unittest.TestCase):
    def test_a_missing_years_exp_is_read_as_neither_rookie_nor_veteran(self):
        """42 of the 6,595 players in the captured universe carry years_exp None. That is "not
        reported", and reading it as 0 would admit every one of them as a rookie."""
        info = {"position": "WR", "status": "Active", "years_exp": None, "team": None}
        self.assertFalse(dr._admits_to_pool(info, None, _match()))
        # ...and the other clauses still decide on their own.
        self.assertTrue(dr._admits_to_pool(dict(info, team="SF"), None, _match()))


class StatusIsAFreshnessRuleNotAGateTests(unittest.TestCase):
    """The owner's re-entry case: a retired player un-retires and must be able to come back.

    The status check used to run in build_available_pool BEFORE any evidence was read -- the
    #180 defect one layer up, a gate standing in front of the facts. Measured against the
    captured universe it was vetoing 304 players carrying a positive signal, including a
    Philadelphia tight end projected for 32.92 points while marked Inactive.
    """

    def test_a_live_projection_beats_a_stale_not_playing_status(self):
        info = {"position": "TE", "status": "Inactive", "years_exp": 4, "team": "PHI"}
        self.assertTrue(dr._admits_to_pool(info, 32.92, _match()))

    def test_being_rostered_beats_a_stale_not_playing_status(self):
        info = {"position": "DL", "status": "Inactive", "years_exp": 2, "team": "MIN"}
        self.assertTrue(dr._admits_to_pool(info, None, _match()))

    def test_a_rookie_beats_a_stale_not_playing_status(self):
        info = {"position": "WR", "status": "Inactive", "years_exp": 0, "team": None}
        self.assertTrue(dr._admits_to_pool(info, None, _match()))

    def test_a_stale_vendor_number_does_NOT_beat_it(self):
        """The one clause status wins against, and the reason the rule is FRESHNESS rather than
        'status never matters'. A vendor file cut weeks ago is the older statement; without it
        losing here, a genuinely retired player would sit in the pool forever on the strength of
        a trade value nobody has revisited."""
        info = {"position": "RB", "status": "Retired", "years_exp": 11, "team": None}
        self.assertFalse(dr._admits_to_pool(info, None, _match(True, trade_value=9.0)))
        # Same player, still retired, but now on a roster again -> back in, no code change.
        self.assertTrue(dr._admits_to_pool(dict(info, team="LAR"), None, _match(True, trade_value=9.0)))

    def test_an_unrecognised_status_is_not_read_as_not_playing(self):
        """Sleeper does not send 'Retired' in the captured universe at all; the observed
        vocabulary is Inactive / Active / Injured Reserve / Physically Unable to Perform /
        Practice Squad / None. A status this code has not been taught about must not silently
        acquire veto power (#110)."""
        for status in ("Injured Reserve", "Physically Unable to Perform", "Practice Squad", None):
            with self.subTest(status=status):
                info = {"position": "RB", "status": status, "years_exp": 6, "team": None}
                self.assertTrue(dr._admits_to_pool(info, None, _match(True, trade_value=9.0)),
                                f"{status!r} vetoed a vendor-priced player")

    def test_an_injury_status_never_removes_a_player(self):
        """Dynasty, not redraft: a player hurt this month is still an asset, and #191 measured
        that the injury is already inside the projected number rather than a separate penalty."""
        info = {"position": "RB", "status": "Injured Reserve", "years_exp": 3, "team": "DET"}
        self.assertTrue(dr._admits_to_pool(info, None, _match()))


class TheUnimplementableClauseIsRecordedTests(unittest.TestCase):
    def test_the_2025_production_clause_is_written_down_where_it_will_attach(self):
        """The owner's rule has four positive clauses; one of them -- 2025 production -- cannot
        be evaluated because the owner ruled "measure first" on fetching last season's actuals,
        so this app holds no 2025 stat line. It is recorded rather than dropped so the gap is a
        NAMED MISSING INPUT rather than a clause that evaporated between the decision and the
        code. This test exists so deleting that record is a failing test, not a silent edit."""
        doc = dr._admits_to_pool.__doc__ or ""
        self.assertIn("2025 PRODUCTION", doc)
        self.assertIn("NOT YET IMPLEMENTED", doc)


class TheRuleIsPositionBlindTests(unittest.TestCase):
    def test_no_position_is_special_cased(self):
        """A standing constraint: no K/DST/IDP special case. A position with thin vendor
        coverage is admitted by the same five clauses as every other position."""
        for position in ("QB", "RB", "WR", "TE", "K", "DEF", "DB", "DL", "LB"):
            with self.subTest(position=position):
                on_team = {"position": position, "status": "Active", "years_exp": 4, "team": "NE"}
                nothing = {"position": position, "status": "Active", "years_exp": 4, "team": None}
                self.assertTrue(dr._admits_to_pool(on_team, None, _match()))
                self.assertFalse(dr._admits_to_pool(nothing, None, _match()))


# MUTATIONS -- each was applied to draft_room.py, the file re-run, and the named test observed
# to FAIL, then the mutation reverted:
#   1. `if sleeper_points is not None` -> `if False`
#        -> EachClauseAdmitsOnItsOwn.test_a_league_scored_projection_admits FAILED
#   2. `info.get("years_exp") == ROOKIE_YEARS_EXP` -> `... is not None`
#        -> AbsenceIsNotRookie.test_a_missing_years_exp... FAILED
#   3. `if info.get("team")` clause deleted
#        -> EachClauseAdmitsOnItsOwn.test_being_on_an_nfl_team_admits FAILED
#   4. status check moved ABOVE the live clauses (the pre-#193 ordering)
#        -> StatusIsAFreshnessRule.test_a_live_projection_beats_a_stale... FAILED
#   5. status check deleted entirely
#        -> StatusIsAFreshnessRule.test_a_stale_vendor_number_does_NOT_beat_it FAILED
#   6. NOT_CURRENTLY_PLAYING widened to include "Injured Reserve"
#        -> StatusIsAFreshnessRule.test_an_injury_status_never_removes_a_player FAILED
if __name__ == "__main__":
    unittest.main()
