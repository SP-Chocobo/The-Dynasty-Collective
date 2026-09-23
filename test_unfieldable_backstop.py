"""The fieldability backstop: `fieldable_ceiling` + `unfieldable_last` (draft_room).

WHY IT EXISTS, in one line: graded on 2024 REALIZED outcomes the engine finished a 12-team PPR
draft with NINE DEFENSES and one receiver in a league with one DEF slot, and lost 0 of 12 seats
by a mean of 641 points. `evidence/kdst_streaming/ROOT_CAUSE.md` has the full derivation.

The properties tested here are the ones that decide whether this is admissible at all:

  - the ceiling is DERIVED from the slot list and the one bye every team has (`#56`);
  - a flex-reachable position has NO ceiling, so ordinary depth is never touched;
  - it is a BACKSTOP, not a preference -- it cannot bind on a roster that is not provably
    carrying a player it can never field (`feasibility_first`'s own admissibility test);
  - it reaches the PICK, not just the board, because `pick_synthesis._board_order` re-sorts
    every board it is handed (`#155`) and a backstop expressed only as row order is discarded.
"""

from __future__ import annotations

import unittest

import pandas as pd

import draft_room as dr
import pick_synthesis as ps

#: One dedicated DEF, one K, one QB, and a FLEX reaching RB/WR/TE -- the measured format's shape.
ROSTER_POSITIONS = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX",
                    "BN", "BN", "BN", "BN", "BN", "BN", "K", "DEF"]

PLAYERS = {
    "d1": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "d2": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "d3": {"position": "DEF", "fantasy_positions": ["DEF"]},
    "r1": {"position": "RB", "fantasy_positions": ["RB"]},
    "r2": {"position": "RB", "fantasy_positions": ["RB"]},
    "r3": {"position": "RB", "fantasy_positions": ["RB"]},
    "r4": {"position": "RB", "fantasy_positions": ["RB"]},
    "w1": {"position": "WR", "fantasy_positions": ["WR"]},
    "dual": {"position": "DB", "fantasy_positions": ["DB", "WR"]},
}


def _picks(ids, roster_id="1"):
    return [{"player_id": pid, "roster_id": roster_id, "round": n + 1, "pick_no": n + 1}
            for n, pid in enumerate(ids)]


def _scored(positions, ids=None):
    """A board frame with the two columns the backstop reads. `ids` defaults to a player at each
    position taken from PLAYERS, so the eligibility lookup the backstop does has something real
    to find -- a frame with fabricated ids would make every demotion vacuously zero."""
    positions = list(positions)
    if ids is None:
        first_at = {}
        for pid, info in PLAYERS.items():
            first_at.setdefault(info["position"], pid)
        ids = [first_at.get(p, f"unknown-{p}") for p in positions]
    return pd.DataFrame({"position": positions, "player_id": list(ids)},
                        index=range(len(positions)))


class TheCeilingIsDerivedTests(unittest.TestCase):

    def test_a_dedicated_position_gets_its_slots_plus_the_one_bye(self):
        ceilings = dr.fieldable_ceiling(ROSTER_POSITIONS)
        self.assertEqual(2, ceilings["DEF"])
        self.assertEqual(2, ceilings["K"])
        self.assertEqual(2, ceilings["QB"])

    def test_a_flex_reachable_position_has_no_ceiling_at_all(self):
        """ABSENCE, not a large number. A spare RB fills a FLEX and frees a WR upward, so its
        useful depth is a real valuation question this function has no opinion about."""
        ceilings = dr.fieldable_ceiling(ROSTER_POSITIONS)
        for position in ("RB", "WR", "TE"):
            self.assertNotIn(position, ceilings)

    def test_two_dedicated_slots_raise_the_ceiling_by_exactly_one_each(self):
        ceilings = dr.fieldable_ceiling(["QB", "QB", "DEF"])
        self.assertEqual(3, ceilings["QB"])
        self.assertEqual(2, ceilings["DEF"])

    def test_an_empty_slot_list_yields_no_ceilings_rather_than_an_empty_opinion(self):
        self.assertEqual({}, dr.fieldable_ceiling([]))


class TheBackstopBindsOnlyWhenItIsProvableTests(unittest.TestCase):

    def test_a_third_defense_is_demoted(self):
        got = dr.unfieldable_last(_scored(["DEF", "WR", "RB"]), _picks(["d1", "d2"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([1, 0, 0], list(got))

    def test_the_bye_backup_is_NOT_demoted(self):
        """The ceiling is the largest count that is not PROVABLY wasted. One spare covers the
        one bye, so flagging it would make this a preference rather than a backstop."""
        got = dr.unfieldable_last(_scored(["DEF", "WR"]), _picks(["d1"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0], list(got))

    def test_a_fourth_running_back_is_never_demoted(self):
        """The flex exemption, end to end. This is the test that keeps it from firing on every
        sane roster in the battery."""
        got = dr.unfieldable_last(_scored(["RB", "WR"]), _picks(["r1", "r2", "r3", "r4"]),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0], list(got))

    def test_an_empty_roster_demotes_nobody(self):
        got = dr.unfieldable_last(_scored(["DEF", "K", "QB"]), [], PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0, 0, 0], list(got))

    def test_another_seats_defenses_do_not_saturate_mine(self):
        """Read off MY roster only. Counting the league's would turn a backstop into a scarcity
        signal, which is replacement_levels' job and not this one's."""
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"], roster_id="7"),
                                  PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([0], list(got))

    def test_a_multi_eligible_player_saturates_no_dedicated_position(self):
        """#172 in the counting direction: a player who reaches a shared slot is not consuming
        a dedicated one, so he is counted at no ceilinged position."""
        got = dr.unfieldable_last(_scored(["WR"]), _picks(["dual", "dual2"]),
                                  dict(PLAYERS, dual2={"position": "DB",
                                                       "fantasy_positions": ["DB", "WR"]}),
                                  "1", ROSTER_POSITIONS)
        self.assertEqual([0], list(got))

    def test_no_roster_id_is_a_no_op(self):
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"]),
                                  PLAYERS, None, ROSTER_POSITIONS)
        self.assertEqual([0], list(got))


class AnUPGRADE_IsNotSurplusTests(unittest.TestCase):
    """The owner's objection, answered: a hard ceiling is a FORCED HOLD, and a derived bound does
    not have to be one. A candidate at a saturated position is demoted only when he would not
    improve on the worst thing already held there.

    Still arithmetic -- his projected points against my own rostered players' projected points,
    both already computed on the same basis (roster_points_lookup, #216). No constant enters.
    """

    #: My two defenses, valued in projected points, in the shape _team_roster_points_players
    #: returns.
    HELD = [{"id": "d1", "value": 121.5, "eligible": {"DEF"}},
            {"id": "d2", "value": 120.4, "eligible": {"DEF"}}]

    def _scored_with_values(self, ids, values):
        return pd.DataFrame({"position": ["DEF"] * len(ids), "player_id": list(ids),
                             "_points": list(values)})

    def test_a_worse_third_defense_is_still_demoted(self):
        """The nine-defense roster's actual shape: every one after the second was WORSE than
        what was held (121.5, 120.4, 119.9, 112.3, ...). The hole stays closed."""
        got = dr.unfieldable_last(self._scored_with_values(["d3"], [119.9]),
                                  _picks(["d1", "d2"]), PLAYERS, "1", ROSTER_POSITIONS,
                                  my_points_players=self.HELD)
        self.assertEqual([1], list(got))

    def test_a_BETTER_third_is_NOT_demoted(self):
        """The case the exemption exists for. He is takeable precisely when he is good enough to
        crack the two you would otherwise keep -- then the surplus body is the one he displaces."""
        got = dr.unfieldable_last(self._scored_with_values(["d3"], [140.0]),
                                  _picks(["d1", "d2"]), PLAYERS, "1", ROSTER_POSITIONS,
                                  my_points_players=self.HELD)
        self.assertEqual([0], list(got))

    def test_equal_to_my_worst_is_a_second_copy_not_an_upgrade(self):
        got = dr.unfieldable_last(self._scored_with_values(["d3"], [120.4]),
                                  _picks(["d1", "d2"]), PLAYERS, "1", ROSTER_POSITIONS,
                                  my_points_players=self.HELD)
        self.assertEqual([1], list(got))

    def test_without_the_rosters_prices_it_falls_back_to_the_COUNT(self):
        """"I cannot tell whether he is an upgrade" must not silently become "he is one"."""
        got = dr.unfieldable_last(self._scored_with_values(["d3"], [140.0]),
                                  _picks(["d1", "d2"]), PLAYERS, "1", ROSTER_POSITIONS)
        self.assertEqual([1], list(got))

    def test_an_unpriced_candidate_falls_back_to_the_count_too(self):
        got = dr.unfieldable_last(self._scored_with_values(["d3"], [None]),
                                  _picks(["d1", "d2"]), PLAYERS, "1", ROSTER_POSITIONS,
                                  my_points_players=self.HELD)
        self.assertEqual([1], list(got))

    def test_the_board_hands_its_roster_prices_to_the_backstop(self):
        """#200: asked of the CODE. A call site that forgot the argument would silently revert
        every roster to the forced-hold reading."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(dr.compute_draft_board))
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "unfieldable_last"]
        self.assertEqual(2, len(calls), "expected the balanced and upside branches")
        with_prices = [c for c in calls
                       if "my_points_players" in [kw.arg for kw in c.keywords]]
        self.assertEqual(1, len(with_prices),
                         "exactly the branch that computes roster prices should pass them; "
                         "the upside branch zeroes every team-specific term and has none")


class ARookieDraftIsExemptTests(unittest.TestCase):
    """The backstop's whole claim is about THIS SEASON's lineup -- a surplus body cannot be
    fielded, and the churn it buys is free on the wire. An annual rookie draft acquires future
    assets against a roster that already exists, and a team holding two quarterbacks has every
    reason to take a rookie third. Firing there would be the engine asserting a redraft
    objective inside the one draft phase that explicitly is not one.

    Scoped on `pool_scope`, not on `is_dynasty`: the question is which DRAFT this is, not which
    league. A dynasty STARTUP is a full draft and the backstop belongs in it.
    """

    def test_a_rookie_draft_demotes_nobody(self):
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"]), PLAYERS, "1",
                                  ROSTER_POSITIONS, pool_scope="rookies_only")
        self.assertEqual([0], list(got))

    def test_the_same_board_in_a_full_draft_DOES_demote(self):
        """The control. Without it the exemption could be hiding a backstop that never fires."""
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"]), PLAYERS, "1",
                                  ROSTER_POSITIONS, pool_scope="all")
        self.assertEqual([1], list(got))

    def test_a_veterans_only_draft_is_NOT_exempt(self):
        """Only the rookie phase carries the future-asset argument."""
        got = dr.unfieldable_last(_scored(["DEF"]), _picks(["d1", "d2"]), PLAYERS, "1",
                                  ROSTER_POSITIONS, pool_scope="veterans_only")
        self.assertEqual([1], list(got))

    def test_the_board_hands_its_scope_to_the_backstop(self):
        """#200: asked of the CODE, so a call site that forgot the argument fails here rather
        than silently defaulting a rookie draft back into scope."""
        import ast
        import inspect
        tree = ast.parse(inspect.getsource(dr.compute_draft_board))
        calls = [n for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "unfieldable_last"]
        self.assertEqual(2, len(calls), "expected the balanced and upside branches")
        for call in calls:
            self.assertIn("pool_scope", [kw.arg for kw in call.keywords])


class ItAsksEligibilityNotThePrimaryBucketTests(unittest.TestCase):
    """#172, in the demotion direction. Reading `position` alone sinks a dual-eligible player on
    a label rather than on what he can actually fill."""

    #: Both RB and WR dedicated, no flex anywhere -- so BOTH carry a ceiling and the subset test
    #: is the only thing separating a demotion from a mistake.
    NO_FLEX = ["QB", "RB", "RB", "WR", "WR", "DEF"]

    def test_a_dual_eligible_player_survives_while_one_of_his_positions_is_open(self):
        players = dict(PLAYERS, rbwr={"position": "RB", "fantasy_positions": ["RB", "WR"]})
        # Three RBs held: RB is saturated (2 slots + bye = 3 -> held 3 >= 3). WR is not.
        got = dr.unfieldable_last(_scored(["RB"], ids=["rbwr"]),
                                  _picks(["r1", "r2", "r3"]), players, "1", self.NO_FLEX)
        self.assertEqual([0], list(got),
                         "a WR-eligible player was demoted for being labelled RB")

    def test_a_single_position_player_at_the_same_position_IS_demoted(self):
        """The control for the test above: same board, same roster, one eligibility."""
        got = dr.unfieldable_last(_scored(["RB"], ids=["r4"]),
                                  _picks(["r1", "r2", "r3"]), PLAYERS, "1", self.NO_FLEX)
        self.assertEqual([1], list(got))

    def test_a_dual_eligible_player_is_demoted_once_BOTH_are_saturated(self):
        players = dict(PLAYERS, rbwr={"position": "RB", "fantasy_positions": ["RB", "WR"]},
                       w2={"position": "WR", "fantasy_positions": ["WR"]},
                       w3={"position": "WR", "fantasy_positions": ["WR"]})
        got = dr.unfieldable_last(_scored(["RB"], ids=["rbwr"]),
                                  _picks(["r1", "r2", "r3", "w1", "w2", "w3"]),
                                  players, "1", self.NO_FLEX)
        self.assertEqual([1], list(got))

    def test_a_row_whose_eligibility_cannot_be_read_is_not_demoted(self):
        """Absence is not evidence of surplus (#187's shape, in the selection layer)."""
        got = dr.unfieldable_last(_scored(["RB"], ids=["nobody-knows-him"]),
                                  _picks(["r1", "r2", "r3"]), PLAYERS, "1", self.NO_FLEX)
        self.assertEqual([0], list(got))


class WhereTheCeilingBINDS_AcrossRealFormatsTests(unittest.TestCase):
    """Measured against the real league matrix, not a fixture. A backstop whose reach nobody has
    looked at is a backstop nobody can predict.

        12T_ppr_SF             {}                              <- INERT
        12T_ppr_K_DEF          QB 2, K 2, DEF 2
        HEAVY_IDP              QB 2, DL 3, LB 3, DB 3
        4WR_TE_PREMIUM         QB 2
        12T_ppr                QB 2
        12T_ppr_SHORT_DRAFT    QB 2

    SUPERFLEX IS THE ONE THAT MATTERS. `#20`/`#22` was a superflex QB regression: an ordering
    change passed the format battery and then under-drafted quarterbacks. This backstop cannot
    repeat it, and not by being careful -- by construction. SUPER_FLEX admits QB alongside other
    positions, so QB is flex-reachable there, so it has no ceiling, so the whole function is a
    no-op in that format. Pinned here because "cannot happen by construction" is worth exactly
    as much as the test that proves the construction still holds.
    """

    def _ceilings(self, label):
        import draft_battery as db
        import run_draft_battery as rdb
        scoring = rdb.scoring_settings_from_capture()
        arm = next(a for a in db.league_matrix(scoring) if a["label"] == label)
        return dr.fieldable_ceiling(arm["league"]["roster_positions"])

    def test_superflex_has_no_ceilings_at_all(self):
        self.assertEqual({}, self._ceilings("12T_ppr_SF"),
                         "the backstop has reach in superflex -- that is the #22 regression's "
                         "own format and it must stay inert there")

    def test_the_kdst_format_ceilings_qb_k_and_def_at_two(self):
        self.assertEqual({"QB": 2, "K": 2, "DEF": 2}, self._ceilings("12T_ppr_K_DEF"))

    def test_a_two_slot_idp_position_gets_three(self):
        """Two dedicated slots plus the one bye. The arithmetic half, on a real roster."""
        self.assertEqual(3, self._ceilings("HEAVY_IDP")["LB"])

    def test_no_flex_reachable_position_is_ceilinged_in_any_format(self):
        """The exemption, asserted over every format the batteries run rather than one."""
        for label in ("12T_ppr_SF", "12T_ppr_K_DEF", "HEAVY_IDP", "4WR_TE_PREMIUM",
                      "12T_ppr", "12T_ppr_SHORT_DRAFT"):
            ceilings = self._ceilings(label)
            for position in ("RB", "WR", "TE"):
                self.assertNotIn(position, ceilings, f"{position} ceilinged in {label}")


class ItReachesThePickAndNotOnlyTheBoardTests(unittest.TestCase):
    """#155. `_board_order` re-sorts every board it is handed, so a backstop that lives only in
    draft_room's row order is thrown away before a pick is made. Tier 3 was measured promoting a
    QB correctly on the board while the chair still took its seventh RB, for exactly this reason.
    """

    def test_board_order_sinks_an_unfieldable_row_below_a_worse_scoring_one(self):
        unfieldable = {"player_id": "d3", "final_score": 100.0, "cannot_be_fielded": True}
        ordinary = {"player_id": "w1", "final_score": 1.0, "cannot_be_fielded": False}
        self.assertEqual(["w1", "d3"],
                         [r["player_id"] for r in sorted([unfieldable, ordinary],
                                                         key=ps._board_order)])

    def test_the_feasibility_backstop_still_outranks_it(self):
        """Order of the two backstops: filling a slot you cannot otherwise fill beats avoiding a
        spot you cannot field. A roster in BOTH states must still draft the legal lineup."""
        required = {"player_id": "a", "final_score": 1.0,
                    "fills_required_slot": True, "cannot_be_fielded": False}
        unfieldable = {"player_id": "b", "final_score": 500.0,
                       "fills_required_slot": False, "cannot_be_fielded": True}
        self.assertEqual(["a", "b"],
                         [r["player_id"] for r in sorted([unfieldable, required],
                                                         key=ps._board_order)])

    def test_a_row_without_the_flag_is_treated_as_fieldable(self):
        """Every caller that predates the flag must keep working, and absence must read as 'not
        demoted' rather than as a demotion nobody computed."""
        a = {"player_id": "a", "final_score": 5.0}
        b = {"player_id": "b", "final_score": 1.0}
        self.assertEqual(["a", "b"],
                         [r["player_id"] for r in sorted([b, a], key=ps._board_order)])

    def test_the_column_is_emitted_on_both_boards(self):
        """A companion that reaches only one serialization is the #174 defect."""
        self.assertIn("cannot_be_fielded", dr.BALANCED_BOARD_COLUMNS)
        self.assertIn("cannot_be_fielded", dr.UPSIDE_BOARD_COLUMNS)


if __name__ == "__main__":
    unittest.main()
