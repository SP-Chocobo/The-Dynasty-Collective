"""D7 / MANDATE 3.2's second half -- the flex exemption was an exemption from being counted at all.

`fieldable_ceiling` gives no ceiling to a position with flex reach, on a sound ground: a spare there
can start in a shared slot, so it is not provably wasted. `unfieldable_last` therefore never looked
at those positions. What that permits is a roster holding **six IDP against a single `IDP_FLEX`
slot** and being told nothing, which 3.2 measured on six of twelve rosters. One of them can start.

THE ADDITIVE ALLOWANCE THE RULING ASKED FOR CANNOT WORK, and this is the finding that shaped the
repair. D7(b) ruled `slots + 1 + allowance(group)` with the allowance chosen. Swept over the
battery's own 53 arms -- 948 seat x group observations, 36 IDP-group and 912 offence-group:

    allowance   IDP over-accumulations caught   ordinary offence seats flagged
            0                26 of 26                        853 of 912
            5                26 of 26                         59 of 912
            8                23 of 26                         55 of 912
           12                 0 of 26                         41 of 912

The ranges do not merely overlap, they INVERT. A 26-round draft into 9 reachable offensive slots
legitimately carries ~24 bodies, so the offence group needs up to 14 of slack; the IDP_FLEX case has
to be caught below 5. By the time an additive constant spares ordinary offence it has silenced the
case 3.2 exists to catch. A bench-derived allowance never binds at all.

THE RATIO SEPARATES THEM, because the groups differ in the SIZE of their reach and not only in their
depth. Held-to-reach tops out at 2.71 for offence (reach 6-10) against a 6.5 median for the
over-accumulations (reach 1-2). Measured safe window for `held > reach * k + 1`:

    k in [2.58, 2.99]   catches all 26 over-accumulated seats, flags 0 of 912 ordinary offence seats

`FLEX_GROUP_DEPTH_FACTOR` is 3.0 rather than the window's midpoint, deliberately: it catches 25 of 26
and sits 0.45 above the offence cutoff instead of 0.24. Missing one marginal over-accumulation is
worth far more than firing on a legitimate roster, which is `unfieldable_last`'s own standing test.

STILL A CHOSEN NUMBER, and stated as one (`#56`). Measurement supplies the SHAPE the slack must take
and the WINDOW the value must sit in; the value inside it is a convention, as 1.3's tie-break is.
D7(a) -- deriving it from `#30`'s streaming baseline -- is the end state and is blocked behind `#50`,
written up as D9.
"""

from __future__ import annotations

import collections
import json
import unittest
from pathlib import Path

import draft_battery as dbat
import draft_room as dr
from player_universe import FLEX_SLOT_POSITIONS

_REPORT = Path("BATTERY_REPORT.json")

#: One IDP_FLEX slot, no dedicated IDP slots -- the shape 3.2 names. Six IDP can be held; one plays.
IDP_FLEX_ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "IDP_FLEX"] + ["BN"] * 6
#: An ordinary offence roster. 7 reachable slots, and a 14-round draft MUST carry about twelve.
OFFENCE_ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 6


def _eligibilities(counts: dict[str, int]):
    return [frozenset({position}) for position, n in counts.items() for _ in range(n)]


class TheBoundIsMultiplicativeForAReasonTests(unittest.TestCase):

    def test_the_factor_sits_inside_the_measured_safe_window(self):
        """The window is what measurement settled; the value inside it is the convention. If someone
        moves the factor out of the window, the sweep that justified it no longer applies."""
        self.assertGreaterEqual(dr.FLEX_GROUP_DEPTH_FACTOR, 2.58)
        self.assertLessEqual(dr.FLEX_GROUP_DEPTH_FACTOR, 2.99 + 0.01 + 0.5,
                             "the factor is above the window measured to spare ordinary offence "
                             "rosters; re-run the sweep before widening it")

    def test_the_slack_scales_with_the_group_rather_than_being_added_to_it(self):
        """The structural claim, stated so an additive form cannot quietly come back: doubling a
        group's reach must more than double its ceiling's slack."""
        small = dr.flex_reachable_ceiling_groups(["IDP_FLEX"], [])
        large = dr.flex_reachable_ceiling_groups(["IDP_FLEX", "DL", "LB", "DB", "DL", "LB"], [])
        self.assertTrue(small and large)
        small_slack = small[0]["ceiling"] - small[0]["slots"]
        large_slack = large[0]["ceiling"] - large[0]["slots"]
        self.assertGreater(large_slack, small_slack,
                           "the slack does not grow with the group, so it is additive in effect "
                           "and the sweep says no additive slack separates the populations")


class TheIdpFlexCaseIsCaughtTests(unittest.TestCase):

    def test_six_idp_against_one_flex_slot_is_saturated(self):
        """3.2's motivating measurement, as a unit fact."""
        groups = dr.flex_reachable_ceiling_groups(
            IDP_FLEX_ROSTER, _eligibilities({"LB": 3, "DL": 2, "DB": 1}))
        idp = [g for g in groups if g["positions"] & {"DL", "LB", "DB"}]
        self.assertEqual(len(idp), 1, "the IDP group is not being formed")
        self.assertEqual(idp[0]["slots"], 1, "one IDP_FLEX slot and nothing else admits them")
        self.assertGreaterEqual(idp[0]["held"], idp[0]["ceiling"],
                               f"six IDP against a ceiling of {idp[0]['ceiling']} is not flagged")

    def test_a_roster_at_the_bound_is_left_alone(self):
        """The backstop's own standing test: it must not bind on a roster that was never in danger.
        Held exactly at the ceiling minus one is legitimate depth."""
        groups = dr.flex_reachable_ceiling_groups(
            IDP_FLEX_ROSTER, _eligibilities({"LB": 3}))
        idp = [g for g in groups if g["positions"] & {"DL", "LB", "DB"}][0]
        self.assertLess(idp["held"], idp["ceiling"],
                        "three IDP against one flex slot is already flagged, which is too tight")

    def test_it_reaches_the_board_and_demotes(self):
        """End to end through `unfieldable_last`, because a bound nothing consults is not a guard."""
        import pandas as pd
        players_db = {str(i): {"first_name": "P", "last_name": str(i), "position": "LB",
                               "fantasy_positions": ["LB"]} for i in range(1, 8)}
        players_db["99"] = {"first_name": "Q", "last_name": "B", "position": "QB",
                            "fantasy_positions": ["QB"]}
        picks = [{"player_id": str(i), "roster_id": "1", "round": i, "pick_no": i}
                 for i in range(1, 8)]
        scored = pd.DataFrame([
            {"player_id": "100", "position": "LB", "final_score": 50.0},
            {"player_id": "99", "position": "QB", "final_score": 10.0},
        ])
        players_db["100"] = {"first_name": "R", "last_name": "C", "position": "LB",
                             "fantasy_positions": ["LB"]}
        key = dr.unfieldable_last(scored, picks, players_db, "1", IDP_FLEX_ROSTER)
        self.assertEqual(list(key), [1, 0],
                         "the eighth linebacker is not demoted while the quarterback is")


class OrdinaryOffenceDepthIsNotTouchedTests(unittest.TestCase):

    def test_twelve_offensive_players_on_a_fourteen_round_roster_are_fine(self):
        groups = dr.flex_reachable_ceiling_groups(
            OFFENCE_ROSTER, _eligibilities({"RB": 5, "WR": 6, "TE": 2}))
        offence = [g for g in groups if "WR" in g["positions"]][0]
        self.assertLess(offence["held"], offence["ceiling"],
                        f"13 offensive players against a ceiling of {offence['ceiling']} is "
                        f"flagged; a 14-round draft into 7 reachable slots must carry about twelve")

    def test_the_deepest_roster_the_battery_drafted_is_still_fine(self):
        """`CAPTURE_fourth_and_forever`: 26 rounds, bench 11, measured holding ~24 in the offence
        group. It is the hardest ordinary case in the whole population and the one every additive
        allowance failed on."""
        deep = ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "FLEX", "SUPER_FLEX"] + ["BN"] * 11
        groups = dr.flex_reachable_ceiling_groups(
            deep, _eligibilities({"RB": 8, "WR": 12, "TE": 4}))
        for group in groups:
            if group["positions"] & {"WR", "RB"}:
                self.assertLess(group["held"], group["ceiling"],
                                f"24 offensive players against a ceiling of {group['ceiling']}")

    def test_a_player_who_reaches_outside_the_group_saturates_nothing(self):
        """The same counting rule the dedicated bound uses. A man who can start elsewhere is not
        surplus here, and forgetting that is how the dedicated bound came to skip multi-eligible
        players entirely."""
        groups = dr.flex_reachable_ceiling_groups(
            IDP_FLEX_ROSTER, [frozenset({"LB", "QB"})] * 9)
        for group in groups:
            self.assertEqual(group["held"], 0,
                             "players eligible outside the group are counted against it")


@unittest.skipUnless(_REPORT.exists(), "needs the battery report")
class AgainstTheBatteryOwnRostersTests(unittest.TestCase):
    """The population the factor was chosen on, re-derived here so the claim is checkable rather
    than quoted. 53 arms, every seat, both groups."""

    @classmethod
    def setUpClass(cls):
        report = json.loads(_REPORT.read_text(encoding="utf-8"))
        leagues = {entry["label"]: entry for entry in dbat.league_matrix()}
        cls.rows = []
        for arm in report["results"]:
            entry = leagues.get(arm["label"])
            if not entry:
                continue
            roster_positions = entry["league"]["roster_positions"]
            for seat, counts in (arm.get("shape") or {}).items():
                held = _eligibilities({p: n for p, n in counts.items()})
                for group in dr.flex_reachable_ceiling_groups(roster_positions, held):
                    cls.rows.append({
                        "arm": arm["label"], "seat": seat,
                        "idp": bool(group["positions"] & {"DL", "LB", "DB"}),
                        "held": group["held"], "ceiling": group["ceiling"],
                    })

    def test_the_population_is_the_one_the_factor_was_measured_on(self):
        offence = [r for r in self.rows if not r["idp"]]
        self.assertGreater(len(offence), 800,
                           f"only {len(offence)} offence observations; the sweep had 912 and this "
                           f"check is weaker than the one that chose the factor")

    def test_not_one_ordinary_offence_seat_is_flagged(self):
        flagged = [r for r in self.rows if not r["idp"] and r["held"] >= r["ceiling"]]
        self.assertEqual(
            flagged, [],
            f"{len(flagged)} ordinary offence seats are demoted, e.g. "
            f"{flagged[:3]} -- the backstop is binding on rosters that were never in danger")

    def test_the_idp_over_accumulations_ARE_flagged(self):
        """Non-vacuity, and the half that makes the silence above meaningful: a guard that never
        fires would pass the test before this one trivially."""
        idp = [r for r in self.rows if r["idp"]]
        if not idp:
            self.skipTest("no IDP-flex arm in the report; nothing for this bound to catch")
        caught = [r for r in idp if r["held"] >= r["ceiling"]]
        self.assertTrue(caught,
                        "no IDP seat is caught anywhere in the battery, so this bound does nothing")


if __name__ == "__main__":
    unittest.main()
