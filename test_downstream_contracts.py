"""Downstream contracts as executable invariants, before any downstream repair.

Written against the REPAIRED canonical dataset (identity, parser and reconciliation boundaries
all landed). Two kinds of test live here, deliberately separated:

  * INVARIANTS -- contracts that are sound today and must survive every downstream change.
    These pin the architecture that is working, so a repair cannot quietly trade one defect
    for another.
  * KNOWN GAPS -- contracts that are sound but NOT met today, written as the contract and
    marked expectedFailure with the finding that owns them. They are executable statements of
    what is still wrong. When a repair lands, the suite reports an UNEXPECTED SUCCESS and the
    marker has to be removed deliberately -- a defect cannot be fixed by accident and left
    undocumented, and it cannot be entrenched by a test that asserts the broken behaviour.

The doctrine's category split is what these are organised around: a player property must not
depend on decision context, and decision context must not masquerade as a player property.
"""
import math
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
REDRAFT = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 0}, "scoring_settings": {}}


def _is_absent(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


class _BoardFixture(unittest.TestCase):
    """One real board off the repaired canonical data, shared by the contract tests."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            rows = proj[proj["position"] == position]
            for _, row in rows.sort_values("trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="1", league=DYNASTY, mode="balanced")


class BpaIsAPlayerPropertyTests(_BoardFixture):
    """BPA answers "what is this player's cross-position production surplus". It may not vary
    with who is picking -- that is decision context, and the whole point of the split."""

    def test_bpa_is_identical_for_every_team_at_the_same_board_state(self):
        other = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="7",
                                       league=DYNASTY, mode="balanced")
        mine = {r["player_id"]: r.get("bpa") for r in self.board}
        theirs = {r["player_id"]: r.get("bpa") for r in other}
        self.assertEqual(set(mine), set(theirs))
        for pid, value in mine.items():
            if _is_absent(value):
                self.assertTrue(_is_absent(theirs[pid]), pid)
            else:
                self.assertEqual(value, theirs[pid], pid)

    def test_universal_value_is_also_team_agnostic(self):
        other = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="7",
                                       league=DYNASTY, mode="balanced")
        mine = {r["player_id"]: r.get("universal_value") for r in self.board}
        for row in other:
            value, expected = row.get("universal_value"), mine[row["player_id"]]
            if _is_absent(expected):
                self.assertTrue(_is_absent(value), row["player_id"])
            else:
                self.assertEqual(value, expected, row["player_id"])

    def test_need_and_eligibility_are_context_and_do_vary_by_team(self):
        # The converse of the two above: if these did NOT move with the roster, the split would
        # be decorative. Needs real picks -- on an empty board every roster is identical, so
        # identical need is correct there and proves nothing either way.
        picks = self._picks_giving_two_teams_different_rosters()
        mine = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                      league=DYNASTY, mode="balanced")
        other = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="2",
                                       league=DYNASTY, mode="balanced")
        baseline = {r["player_id"]: (r.get("need_bonus"), r.get("eligibility_bonus"))
                    for r in mine}
        differing = [r["player_id"] for r in other
                     if (r.get("need_bonus"), r.get("eligibility_bonus")) != baseline[r["player_id"]]]
        self.assertTrue(differing, "roster context should move need/eligibility for someone")

    def _picks_giving_two_teams_different_rosters(self):
        """Roster 1 takes quarterbacks, roster 2 takes running backs -- so their remaining
        needs genuinely differ."""
        picks, pick_no = [], 0
        for position, roster_id in (("QB", "1"), ("RB", "2")):
            taken = 0
            for pid, info in self.players_db.items():
                if info["position"] != position or taken >= 2:
                    continue
                pick_no += 1
                taken += 1
                picks.append({"player_id": pid, "roster_id": roster_id,
                              "round": 1, "pick_no": pick_no})
        return picks


class ValueIdentityTests(_BoardFixture):
    """The two decompositions the whole architecture rests on."""

    def test_universal_value_is_exactly_bpa_plus_the_two_nudges(self):
        # Tolerance of one cent, not sloppiness: the emitted record rounds time_horizon_adj to
        # 2dp while score_row sums the unrounded value, so re-adding the PUBLISHED terms can
        # land a cent away from the published total. Worth pinning at exactly one cent -- any
        # larger drift means a term entered universal_value that the decomposition does not
        # show, which is the whole thing this identity exists to make impossible.
        for row in self.board:
            bpa = row.get("bpa")
            if _is_absent(bpa):
                continue
            expected = bpa + row.get("time_horizon_adj", 0.0) + row.get("risk_adj", 0.0)
            self.assertAlmostEqual(row["universal_value"], expected, delta=0.011,
                                   msg=row["name"])

    def test_team_acquisition_value_is_exactly_universal_value_plus_context(self):
        for row in self.board:
            if _is_absent(row.get("universal_value")):
                continue
            expected = (row["universal_value"] + row.get("need_bonus", 0.0)
                        + row.get("eligibility_bonus", 0.0))
            self.assertAlmostEqual(row["final_score"], expected, delta=0.011, msg=row["name"])


class AbsenceIsNotAValueTests(_BoardFixture):
    """A missing valuation is an absence of knowledge, not a zero. This is the invariant the
    unpriced-register work established, and every downstream change has to keep it."""

    def test_an_unpriced_row_carries_absence_not_zero(self):
        unpriced = [r for r in self.board if _is_absent(r.get("bpa"))]
        for row in unpriced:
            self.assertTrue(_is_absent(row.get("universal_value")), row["name"])
            self.assertTrue(_is_absent(row.get("final_score")), row["name"])

    def test_a_priced_zero_and_an_unpriced_row_are_distinguishable(self):
        priced_zero = [r for r in self.board if r.get("bpa") == 0.0]
        unpriced = [r for r in self.board if _is_absent(r.get("bpa"))]
        if priced_zero and unpriced:
            self.assertNotEqual(priced_zero[0].get("bpa"), unpriced[0].get("bpa"))


class HorizonIsGatedOnRealDataTests(_BoardFixture):
    """time_horizon_adj must be zero when there is no multi-year outlook -- absence must never
    become a signal -- and must not fire at all in a redraft league."""

    def test_a_row_without_a_multi_year_outlook_gets_exactly_zero(self):
        # proj_3yr is not carried on the emitted board record, so the presence of a multi-year
        # outlook has to be read from the canonical table the row was scored from.
        proj = self.merger.projections
        horizon_by_name = dict(zip(proj["name"], proj["proj_3yr"]))
        checked = 0
        for row in self.board:
            outlook = horizon_by_name.get(row["name"])
            if outlook is None or _is_absent(outlook):
                self.assertEqual(row.get("time_horizon_adj", 0.0), 0.0, row["name"])
                checked += 1
        self.assertTrue(checked, "no rows without an outlook -- the gate would be untested")

    def test_redraft_applies_no_time_horizon_adjustment_at_all(self):
        redraft = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1",
                                         league=REDRAFT, mode="balanced")
        for row in redraft:
            self.assertEqual(row.get("time_horizon_adj", 0.0), 0.0, row["name"])

    def test_the_horizon_state_the_upstream_repair_produced_is_reachable(self):
        proj = self.merger.projections
        self.assertEqual(set(proj[proj["position"] == "DEF"]["proj_3yr_state"]),
                         {"not_applicable"})
        self.assertEqual(set(proj[proj["position"] == "K"]["proj_3yr_state"]), {"unknown"})


class SelectionLayerContractTests(_BoardFixture):
    """The board is one ordered list, and its order must be decidable and deterministic."""

    def test_the_board_is_ordered_by_acquisition_value_with_unpriced_last(self):
        priced_seen_after_unpriced = False
        seen_unpriced = False
        for row in self.board:
            if _is_absent(row.get("final_score")):
                seen_unpriced = True
            elif seen_unpriced:
                priced_seen_after_unpriced = True
        self.assertFalse(priced_seen_after_unpriced,
                         "a priced row appears after an unpriced one")

    def test_the_ordering_is_deterministic_across_identical_calls(self):
        again = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1",
                                       league=DYNASTY, mode="balanced")
        self.assertEqual([r["player_id"] for r in self.board], [r["player_id"] for r in again])


# --------------------------------------------------------------------------- known gaps --
# Each of these states a contract this codebase has established and does NOT currently meet.
# They are marked expectedFailure so the suite stays honest without entrenching the defect:
# when the repair lands the runner reports an unexpected success and the marker must be
# removed deliberately.

class KnownGapBpaUnitStability(_BoardFixture):
    """#75/#76. bpa's reference is max(VOR) over the live pool, so its unit moves as the pool
    drains: measured, the reference carries 94.6% of all bpa movement, and a player whose
    projection never changes reads 0.0 -> 88.9 -> 0.0. A player property may not move because
    a different player was drafted."""

    @unittest.expectedFailure
    def test_a_players_bpa_does_not_move_when_other_players_are_drafted(self):
        # Deliberately NOT the top row. The pool's best player IS the reference, so his bpa is
        # 100.0 by construction and cannot move -- picking him would make this pass while
        # proving nothing. A mid-pool player is where the moving ruler shows up.
        priced = [r for r in self.board if not _is_absent(r.get("bpa")) and r["bpa"] > 0]
        target = priced[len(priced) // 2]
        drafted = [{"player_id": r["player_id"], "roster_id": "2", "round": 1, "pick_no": i + 1}
                   for i, r in enumerate(self.board[:24]) if r["player_id"] != target["player_id"]]
        later = dr.compute_draft_board(self.merger, self.players_db, drafted, my_roster_id="1",
                                       league=DYNASTY, mode="balanced")
        moved = next(r for r in later if r["player_id"] == target["player_id"])
        self.assertAlmostEqual(moved["bpa"], target["bpa"], places=1)


class KnownGapClippedNegativeIsDestroyed(_BoardFixture):
    """#73/#74. A below-replacement measurement is flattened to 0.0 by the clip, so a genuine
    boundary zero, a clipped negative and a degenerate anchor are one indistinguishable value.
    Measured: 95%+ of all zeros are clipped negatives."""

    @unittest.expectedFailure
    def test_a_below_replacement_player_keeps_a_signed_measurement(self):
        zeros = [r for r in self.board if r.get("bpa") == 0.0]
        self.assertTrue(zeros)
        self.assertTrue(any(r.get("bpa", 0.0) < 0 for r in zeros),
                        "no clipped negative retains its sign")


class KnownGapSurvivalAnswersOnAnUnpricedBoard(_BoardFixture):
    """#61. estimate_survival is purely rank-based and never reads a value, so it keeps
    returning a confident probability for a player whose ordering on every opponent board is
    the player_id tiebreak. Confirmed live before the repair phase: an unpriced leader at
    round 17 carried the identical 0.202 an unpriced leader at round 13 did.

    Asserted against draft_strategy, not the board record -- survival is computed a layer up
    and compute_draft_board does not carry it. An earlier version of this test looked for the
    field on the board, found nothing, and skipped: a test that cannot observe its subject
    proves nothing about it."""

    def _late_round_state(self):
        board = self.board
        picks = [{"player_id": r["player_id"], "roster_id": str((i % 12) + 1),
                  "round": (i // 12) + 1, "pick_no": i + 1}
                 for i, r in enumerate(board[:12 * 16])]
        return picks

    @unittest.expectedFailure
    def test_survival_declines_when_the_target_is_unpriced_on_every_opponent_board(self):
        picks = self._late_round_state()
        drafted = {p["player_id"] for p in picks}
        late = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                      league=DYNASTY, mode="balanced")
        unpriced = [r for r in late if _is_absent(r.get("final_score"))]
        self.assertTrue(unpriced, "late-round board should contain unpriced rows")
        pick_order = [(str((i % 12) + 1), (i // 12) + 1) for i in range(len(picks) + 24)]
        opponent_boards = ds._build_opponent_boards(
            self.merger, self.players_db, picks, drafted, DYNASTY, "1")
        result = ds.estimate_survival(
            picks, self.players_db, pick_order, len(picks), "1",
            unpriced[0]["player_id"], opponent_boards, league=DYNASTY)
        self.assertIsNone(result.get("survival_probability"))


if __name__ == "__main__":
    unittest.main()
