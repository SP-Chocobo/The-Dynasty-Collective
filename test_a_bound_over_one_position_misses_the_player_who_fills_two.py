"""MANDATE 3.2 / `#126` / `#56` -- the fieldability ceiling, counted over groups.

`fieldable_ceiling` answers one position at a time: at most `slots(P)` of them start in any week,
one spare covers the one bye, so `slots(P) + 1` is the most a roster can hold and still field. That
is exact, and it is not enough, because a player can be eligible at TWO ceilinged positions and so
consume a slot from either. `unfieldable_last` counted a pick only `if len(eligible) == 1`, on the
stated grounds that a player reaching a shared slot is not saturating a dedicated one -- true, but
not the question that test asks.

THE BATTERY MEASURED WHAT IT COST. On HEAVY_IDP, which fields DL/DL, LB/LB and DB/DB as dedicated
slots and therefore HAS a per-position ceiling of 3 at each, ten rosters carried more than the
ceiling, and every one was over by exactly its number of multi-eligible holdings:

    roster  2   LB 6 = 3 counted + 3 skipped
    roster  8   LB 5 = 3 + 2,  DB 4 = 3 + 1
    roster 11   LB 5 = 3 + 2

The backstop stopped each roster at exactly 3 and was then blind. The skipped players are edge
rushers eligible at {DL, LB} and one safety at {DB, LB}; HEAVY_IDP has no IDP_FLEX, so not one of
them reaches a shared slot.

THE JOINT BOUND IS DERIVED FROM THE SAME TWO FACTS (`#56`): players whose eligibility lies entirely
inside a group can only start in slots admitting some member of it, so at most that many start in a
week, and one spare covers the one bye.

    held(group) <= |slots admitting any member of the group| + 1

For a one-position group this IS `slots(P) + 1`, so the count widens and the bar does not move.

WHAT IS DELIBERATELY NOT DONE HERE, and it is an owner decision rather than an omission. 3.2 asks
for this bound on flex-reachable groups too. Measured on the battery's own rosters, that would flag
12 of 12 seats in 12T_ppr -- holding 12-13 players eligible within RB/WR/TE against `7 slots + 1`
-- and 9 of 12 in HEAVY_IDP. Those are ordinary rosters: a 14-round draft into 7 offensive slots
MUST carry about twelve. The `+ 1` rests on `#30`'s measured finding that the churn a spare buys is
free on the waiver wire, which holds for a flat dedicated position and plainly not for RB/WR, where
bench depth is the point. So the arithmetic is sound about ONE WEEK and needs a depth allowance
before it can be a backstop -- and an allowance is a number somebody chooses. The last class below
pins that the backstop still does NOT fire on an ordinary offence roster, so the day someone
extends it, this says so.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd

import draft_battery as batt
import draft_room as dr
import run_draft_battery as rdb
from player_universe import player_eligible_positions

# Dedicated DL/LB/DB, one shared FLEX over RB/WR/TE -- HEAVY_IDP's shape, small enough to reason
# about by hand.
IDP_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                         "DL", "DL", "LB", "LB", "DB", "DB", "BN", "BN", "BN"],
    "total_rosters": 12,
    "settings": {"type": 2},
}
CEILINGS = dr.fieldable_ceiling(IDP_LEAGUE["roster_positions"])


def _group(groups, *positions):
    wanted = frozenset(positions)
    return next((g for g in groups if g["positions"] == wanted), None)


class TheBoundReducesToTheOldOneForASinglePositionTests(unittest.TestCase):
    """The change must widen the COUNT without moving the BAR, or it is a new rule wearing the old
    rule's justification."""

    def test_the_per_position_ceilings_are_what_they_were(self):
        self.assertEqual(CEILINGS, {"QB": 2, "DL": 3, "LB": 3, "DB": 3})

    def test_a_group_of_one_has_exactly_that_positions_ceiling(self):
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"LB"}, {"LB"}, {"DB"}])
        for position, ceiling in CEILINGS.items():
            found = _group(groups, position)
            self.assertIsNotNone(found, f"{position} lost its group")
            self.assertEqual(found["ceiling"], ceiling,
                             f"{position}'s bound moved, so this is a new rule and not a wider count")

    def test_three_single_eligible_linebackers_are_at_the_bound_and_not_over(self):
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"LB"}] * 3)
        self.assertEqual(_group(groups, "LB")["held"], 3)
        self.assertEqual(_group(groups, "LB")["ceiling"], 3)


class APlayerEligibleAtTwoCeilingedPositionsJoinsThemTests(unittest.TestCase):
    def test_the_group_is_the_union_and_the_bound_is_the_summed_slots_plus_ONE(self):
        """One spare for the group, not one per position -- every team has exactly one bye."""
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"DL", "LB"}])
        joined = _group(groups, "DL", "LB")
        self.assertIsNotNone(joined, "a player eligible at both did not join DL and LB")
        self.assertEqual(joined["slots"], 4, "2 DL slots + 2 LB slots")
        self.assertEqual(joined["ceiling"], 5)

    def test_the_exact_roster_the_battery_flagged_is_now_over_its_bound(self):
        """HEAVY_IDP roster 2: three LB-only plus three edge rushers at {DL, LB}. Six players for
        four slots and one bye."""
        held = [{"LB"}, {"LB"}, {"LB"}, {"DL", "LB"}, {"DL", "LB"}, {"DL", "LB"}]
        joined = _group(dr.fieldable_ceiling_groups(CEILINGS, held), "DL", "LB")
        self.assertEqual(joined["held"], 6)
        self.assertEqual(joined["ceiling"], 5)
        self.assertGreater(joined["held"], joined["ceiling"])

    def test_the_old_count_saw_three_of_those_six(self):
        """Stated as a test so the defect cannot quietly return: under `len(eligible) == 1` only
        the three LB-only men were counted, which is exactly the ceiling, so nothing fired."""
        held = [{"LB"}, {"LB"}, {"LB"}, {"DL", "LB"}, {"DL", "LB"}, {"DL", "LB"}]
        old_count = sum(1 for eligible in held if len(eligible) == 1)
        self.assertEqual(old_count, 3)
        self.assertLessEqual(old_count, CEILINGS["LB"])

    def test_a_chain_of_eligibility_merges_three_positions(self):
        """{DL,LB} and {DB,LB} share LB, so all three compete for the same six slots."""
        held = [{"DL", "LB"}, {"DB", "LB"}]
        groups = dr.fieldable_ceiling_groups(CEILINGS, held)
        joined = _group(groups, "DL", "LB", "DB")
        self.assertIsNotNone(joined, "the chain did not merge")
        self.assertEqual(joined["slots"], 6)
        self.assertEqual(joined["ceiling"], 7)

    def test_positions_stay_separate_when_no_held_player_links_them(self):
        """Groups come from the ROSTER's own eligibility, not a fixed partition -- a roster with no
        edge rushers must see exactly the old, tighter, per-position bound."""
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"LB"}, {"DB"}, {"DL"}])
        for position in ("DL", "LB", "DB"):
            self.assertIsNotNone(_group(groups, position),
                                 f"{position} was merged with no player linking it")


class TheFlexExemptionSurvivesTests(unittest.TestCase):
    def test_a_player_reaching_a_position_with_no_ceiling_saturates_nothing(self):
        """The original exemption, asked as the right question: a spare RB fills the FLEX and frees
        a WR upward, so his depth is a valuation question and this bound has no opinion."""
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"RB"}] * 9 + [{"RB", "WR"}] * 3)
        self.assertTrue(all(group["held"] == 0 for group in groups),
                        "a flex-reachable player was counted against a ceiling")

    def test_a_player_eligible_at_one_ceilinged_and_one_flex_position_is_exempt(self):
        """He can always be fielded through the flex chain, so he saturates neither."""
        groups = dr.fieldable_ceiling_groups(CEILINGS, [{"LB", "RB"}] * 6)
        self.assertEqual(_group(groups, "LB")["held"], 0)

    def test_a_league_with_no_derivable_ceiling_yields_no_groups(self):
        """SUPER_FLEX is what makes QB flex-reachable too -- without it a dedicated QB slot keeps
        a ceiling of 2, which is how this test's first fixture was wrong rather than the code."""
        flex_only = ["RB", "WR", "FLEX", "SUPER_FLEX", "IDP_FLEX", "BN"]
        self.assertEqual(dr.fieldable_ceiling(flex_only), {},
                         "fixture is not ceiling-free, so the assertion below proves nothing")
        self.assertEqual(dr.fieldable_ceiling_groups(dr.fieldable_ceiling(flex_only), [{"LB"}]), [])


class TheSortKeyActsOnItTests(unittest.TestCase):
    ROSTER = [{"LB"}, {"LB"}, {"LB"}, {"DL", "LB"}, {"DL", "LB"}, {"DL", "LB"}]

    def _demoted(self, held_sets, candidate_positions, pool_scope="all"):
        players_db, picks = {}, []
        for i, eligible in enumerate(held_sets):
            pid = f"held{i}"
            players_db[pid] = {"position": sorted(eligible)[0],
                               "fantasy_positions": sorted(eligible)}
            picks.append({"player_id": pid, "roster_id": "7"})
        players_db["cand"] = {"position": sorted(candidate_positions)[0],
                              "fantasy_positions": sorted(candidate_positions)}
        scored = pd.DataFrame([{"player_id": "cand", "position": sorted(candidate_positions)[0],
                                "name": "probe"}]).set_index("player_id", drop=False)
        key = dr.unfieldable_last(scored, picks, players_db, "7",
                                  IDP_LEAGUE["roster_positions"], pool_scope=pool_scope)
        return int(key.iloc[0])

    def test_a_further_linebacker_is_demoted_once_the_group_is_saturated(self):
        self.assertEqual(self._demoted(self.ROSTER, {"LB"}), 1)

    def test_so_is_a_further_lineman_since_he_competes_for_the_same_slots(self):
        self.assertEqual(self._demoted(self.ROSTER, {"DL"}), 1)

    def test_a_safety_is_NOT_demoted_because_his_group_is_untouched(self):
        self.assertEqual(self._demoted(self.ROSTER, {"DB"}), 0,
                         "saturating DL/LB must not demote a position with slots of its own")

    def test_a_roster_at_the_bound_is_left_alone(self):
        """`feasibility_first`'s own test for a backstop: it must not bind on a roster that was
        never in danger. At the bound nothing is provably wasted."""
        at_bound = [{"LB"}, {"LB"}, {"LB"}, {"DL", "LB"}]
        self.assertEqual(self._demoted(at_bound[:3], {"LB"}), 1)   # 3 held, ceiling 3
        self.assertEqual(self._demoted([{"LB"}, {"LB"}], {"LB"}), 0)

    def test_a_rookie_draft_is_still_exempt(self):
        self.assertEqual(self._demoted(self.ROSTER, {"LB"}, pool_scope="rookies_only"), 0)


class TheBackstopStillDoesNotTouchAnOrdinaryOffenceRosterTests(unittest.TestCase):
    """The guard on the half deliberately left to the owner. If someone extends the bound to
    flex-reachable groups, this fails and says why."""

    def test_twelve_offence_players_draw_no_demotion(self):
        held = [{"RB"}] * 5 + [{"WR"}] * 5 + [{"TE"}] * 2
        players_db, picks = {}, []
        for i, eligible in enumerate(held):
            pid = f"o{i}"
            players_db[pid] = {"position": sorted(eligible)[0], "fantasy_positions": sorted(eligible)}
            picks.append({"player_id": pid, "roster_id": "7"})
        players_db["cand"] = {"position": "WR", "fantasy_positions": ["WR"]}
        scored = pd.DataFrame([{"player_id": "cand", "position": "WR", "name": "probe"}]
                              ).set_index("player_id", drop=False)
        key = dr.unfieldable_last(scored, picks, players_db, "7", IDP_LEAGUE["roster_positions"])
        self.assertEqual(int(key.iloc[0]), 0,
                         "the backstop fired on an ordinary offence roster -- a 14-round draft "
                         "into 7 offensive slots must carry about twelve, and the bye-week `+1` "
                         "does not justify a bound there (see this module's docstring)")


class TheEngineAndItsAuditAskTheSameQuestionTests(unittest.TestCase):
    """`#126`. The audit used to re-derive the bound and count by primary position; it reported
    HEAVY_IDP roster 2 at 6 LB against 3 while the engine counted 3. An audit that asks a different
    question cannot tell a defect from a disagreement."""

    @classmethod
    def setUpClass(cls):
        cls.players_db, _provenance = rdb.build_players_db_from_capture()
        report = Path("BATTERY_REPORT.json")
        cls.report = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None

    def test_the_audit_reports_groups_and_not_positions(self):
        traj = _TinyTrajectory({"1": ["a", "b", "c", "d", "e", "f"]})
        db = {"a": {"position": "LB", "fantasy_positions": ["LB"]},
              "b": {"position": "LB", "fantasy_positions": ["LB"]},
              "c": {"position": "LB", "fantasy_positions": ["LB"]},
              "d": {"position": "LB", "fantasy_positions": ["DL", "LB"]},
              "e": {"position": "LB", "fantasy_positions": ["DL", "LB"]},
              "f": {"position": "LB", "fantasy_positions": ["DL", "LB"]}}
        findings = batt.unfieldable_depth(traj, IDP_LEAGUE, db)
        self.assertEqual(len(findings), 1, findings)
        self.assertEqual(findings[0]["positions"], ["DL", "LB"])
        self.assertEqual(findings[0]["held"], 6)
        self.assertEqual(findings[0]["ceiling"], 5)
        self.assertEqual(findings[0]["unfieldable"], 1)
        self.assertNotIn("position", findings[0],
                         "the per-position key is gone; a caller reading it would see a group's "
                         "count under a single position's name")

    def test_the_audit_and_the_sort_key_agree_on_the_same_roster(self):
        db = {f"h{i}": {"position": "LB", "fantasy_positions": positions}
              for i, positions in enumerate([["LB"], ["LB"], ["LB"],
                                             ["DL", "LB"], ["DL", "LB"], ["DL", "LB"]])}
        ids = sorted(db)
        traj = _TinyTrajectory({"7": ids})
        over = bool(batt.unfieldable_depth(traj, IDP_LEAGUE, db))
        db_with_candidate = dict(db, cand={"position": "LB", "fantasy_positions": ["LB"]})
        scored = pd.DataFrame([{"player_id": "cand", "position": "LB", "name": "probe"}]
                              ).set_index("player_id", drop=False)
        key = dr.unfieldable_last(
            scored, [{"player_id": pid, "roster_id": "7"} for pid in ids],
            db_with_candidate, "7", IDP_LEAGUE["roster_positions"])
        self.assertEqual(over, bool(int(key.iloc[0])),
                         "the audit and the engine disagree about the same roster")


class _TinyTrajectory:
    """Just enough trajectory for the audit, which asks only for final_rosters()."""

    def __init__(self, rosters):
        self._rosters = rosters

    def final_rosters(self):
        return self._rosters


if __name__ == "__main__":
    unittest.main()
