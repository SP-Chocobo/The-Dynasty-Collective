"""A(#56) -- the constants contract, as executable invariants.

Three constants gate nine rules across six different quantities. Measured on the repaired
real-points unit:

    quantity                        p50      max    rule fires
    leader-second TAV margin        0.35    12.69      0.0%   <- "decisive"
    positional_forfeit             54.81   154.94     73.6%   <- cliff_protection
    TAV - UV (context)              4.00     8.67      0.0%   <- context_elevated
    TAV adjacent gap                0.54    56.85     15.7%   <- near_tie
    bpa gap within a position       2.00    71.00     58.5%   <- CLIFF_MIN_MATERIAL_GAP

The same literal 15.0 gates two quantities whose medians differ by 150x. That is not one
contract with one number; it is several concepts that happen to share a literal.

THE ROOT PATTERN, and it is what these tests exist to prevent recurring. Two of the three
constants were chosen -- correctly -- as a BOUND or a REFERENCE:

  * NECESSITY_STANDOUT_REFERENCE_GAP is a normalizer's reference, and its own comment says it
    was deliberately placed "above the largest adjacent gap ever observed ... since full
    standout credit should demand something rare". Being unreachable is the POINT of a
    normalizer reference.
  * NEED_BONUS_MAX is a cap: 3 x NEED_BONUS_PER_DEDICATED_SLOT, the most a roster slot can
    ever contribute. A cap is an upper bound by definition.

Both were then reused as FIRING THRESHOLDS. A value deliberately placed at or above the top of
a distribution is correct as a reference and automatically dead as a threshold. That is the
whole defect, and it is a category error rather than a bad number:

    A BOUND SAYS "NEVER MORE THAN THIS". A THRESHOLD SAYS "MEANINGFUL ABOVE THIS".
    A VALUE CHOSEN AS ONE IS NOT AUTOMATICALLY VALID AS THE OTHER.

These tests assert reachability against real boards, so a threshold that can never fire fails
here rather than silently never lighting a badge.
"""
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
ROSTER_IDS = [str(i) for i in range(1, NUM_TEAMS + 1)]


class _RealBoards(unittest.TestCase):
    """Several real board states, so a reachability claim is made against the distribution a
    rule actually sees rather than against one hand-built pair."""

    ROUNDS = (0, 2, 4, 6, 8, 10, 12, 14)

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            for _, row in proj[proj["position"] == position].sort_values(
                    "trade_value", ascending=False).iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team"),
                }
        cls.opening = dr.compute_draft_board(cls.merger, cls.players_db, [], my_roster_id="1",
                                             league=DYNASTY, mode="balanced")
        cls.pick_order = ds.generate_pick_order(ROSTER_IDS, 24, "snake")

    @classmethod
    def _boards(cls):
        for rounds in cls.ROUNDS:
            taken = rounds * NUM_TEAMS
            picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                      "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                     for i, r in enumerate(cls.opening[:taken])]
            board = dr.compute_draft_board(cls.merger, cls.players_db, picks, my_roster_id="1",
                                           league=DYNASTY, mode="balanced")
            yield rounds, picks, board


class EveryFiringThresholdIsReachableTests(_RealBoards):
    """The invariant that would have caught all three defects at once."""

    def test_the_ordering_noise_band_is_reachable_in_both_directions(self):
        # NEAR_TIE_BAND is a THRESHOLD and must split its population, not sit outside it.
        inside = outside = 0
        for _, _, board in self._boards():
            values = [r["final_score"] for r in board if r.get("final_score") is not None]
            for i in range(len(values) - 1):
                if values[i] - values[i + 1] <= ps.NEAR_TIE_BAND:
                    inside += 1
                else:
                    outside += 1
        self.assertGreater(inside, 0, "NEAR_TIE_BAND never calls anything a tie")
        self.assertGreater(outside, 0, "NEAR_TIE_BAND calls everything a tie")

    def test_the_decisive_regime_is_reachable_on_a_real_board(self):
        # The defect this pins: the margin half used to be NECESSITY_STANDOUT_REFERENCE_GAP,
        # a normalizer reference placed above the observed maximum on purpose, so "decisive"
        # was produced at 0 of 24 measured board states.
        seen = set()
        for rounds, picks, _ in self._boards():
            index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                          if self.pick_order[i] == "1"), None)
            if index is None:
                continue
            snapshot = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order,
                                         index, "1", DYNASTY, pick_label=f"R{rounds + 1}")
            seen.add(snapshot.decision_regime)
        self.assertIn("decisive", seen,
                      "decision_regime never produces 'decisive' on any real board state -- "
                      "one of its two states is unreachable, so the signal carries no "
                      "information")
        self.assertIn("contested", seen, "decision_regime never produces 'contested' either")


class DecisiveIsTheComplementOfANearTieTests(_RealBoards):
    """The margin half of decision_regime is not a separate concept -- it is exactly the
    question near_tie_flags already answers about the leader.

    near_tie_flags marks the leader whenever a second candidate sits within NEAR_TIE_BAND of
    him, so "leader is flagged" and "leader-second margin <= NEAR_TIE_BAND" are the same
    predicate. Measured across 24 real board-state/roster pairs before the repair, the two
    agreed on every single one. Expressing it once, in one place, is what stops them drifting
    apart -- and is why decision_regime now asks near_tie_flags rather than re-deriving a
    margin against a constant borrowed from a different concept."""

    def test_a_leader_inside_the_band_is_never_decisive(self):
        candidates = [{"team_acquisition_value": 100.0, "survival_probability": 0.0},
                      {"team_acquisition_value": 100.0 - ps.NEAR_TIE_BAND / 2,
                       "survival_probability": 0.5}]
        self.assertEqual(ps.decision_regime(candidates), "contested")

    def test_a_leader_clear_of_the_band_with_low_survival_is_decisive(self):
        candidates = [{"team_acquisition_value": 100.0, "survival_probability": 0.0},
                      {"team_acquisition_value": 100.0 - ps.NEAR_TIE_BAND * 2,
                       "survival_probability": 0.5}]
        self.assertEqual(ps.decision_regime(candidates), "decisive")

    def test_exactly_at_the_band_is_a_tie_and_therefore_contested(self):
        # near_tie_flags is inclusive at the band, so the two agree at the boundary too.
        candidates = [{"team_acquisition_value": 100.0, "survival_probability": 0.0},
                      {"team_acquisition_value": 100.0 - ps.NEAR_TIE_BAND,
                       "survival_probability": 0.5}]
        self.assertEqual(ps.decision_regime(candidates), "contested")

    def test_survival_still_gates_it_independently(self):
        candidates = [{"team_acquisition_value": 100.0,
                       "survival_probability": ps.DECISIVE_SURVIVAL_THRESHOLD + 0.01},
                      {"team_acquisition_value": 100.0 - ps.NEAR_TIE_BAND * 2,
                       "survival_probability": 0.5}]
        self.assertEqual(ps.decision_regime(candidates), "contested")

    def test_the_two_predicates_agree_on_every_real_board_state(self):
        checked = 0
        for rounds, picks, _ in self._boards():
            index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                          if self.pick_order[i] == "1"), None)
            if index is None:
                continue
            snapshot = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order,
                                         index, "1", DYNASTY, pick_label=f"R{rounds + 1}")
            values = [c.team_acquisition_value for c in snapshot.candidates
                      if c.team_acquisition_value is not None]
            if len(values) < 2:
                continue
            leader_in_tie = ps.near_tie_flags(values)[0]
            survival_ok = (snapshot.candidates[0].survival_probability is not None
                           and snapshot.candidates[0].survival_probability
                           <= ps.DECISIVE_SURVIVAL_THRESHOLD)
            expected = "decisive" if (not leader_in_tie and survival_ok) else "contested"
            self.assertEqual(snapshot.decision_regime, expected, f"round {rounds}")
            checked += 1
        self.assertGreater(checked, 4, "too few real board states to make this claim")


class KnownUnreachableThresholdsTests(_RealBoards):
    """Two rules whose thresholds are still bounds borrowed as thresholds. These are recorded
    as executable measurements rather than repaired, because choosing what SHOULD fire them is
    a product decision and no evidence in this repository determines it. They are asserted to
    still be unreachable so that a future change to either constant is noticed here, and so the
    claim in CDME_CONTRACTS.md cannot silently rot."""

    def test_context_elevated_is_measurably_unreachable(self):
        worst = 0.0
        for _, _, board in self._boards():
            for row in board:
                if row.get("final_score") is None or row.get("universal_value") is None:
                    continue
                worst = max(worst, row["final_score"] - row["universal_value"])
        self.assertLess(worst, dr.NEED_BONUS_MAX,
                        "context_elevated has become reachable -- that is good news, but the "
                        "measurement recorded in CDME_CONTRACTS.md is now stale and the "
                        "open decision on it should be revisited")
        # And the reason: the cap is three dedicated slots' worth, this shape has at most two.
        self.assertAlmostEqual(dr.NEED_BONUS_MAX, 3 * dr.NEED_BONUS_PER_DEDICATED_SLOT)

    def test_cliff_protection_fires_for_most_candidates_rather_than_flagging_a_few(self):
        # The mirror-image failure: a threshold far BELOW its quantity's median, so the flag is
        # on almost always and carries nearly no information. positional_forfeit's median is
        # roughly 3.6x the threshold it is compared against.
        forfeits = []
        for rounds, picks, board in self._boards():
            index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                          if self.pick_order[i] == "1"), None)
            priced = [r for r in board if r.get("final_score") is not None]
            if index is None or len(priced) < 4:
                continue
            analysis = ds.pick_analysis(
                self.merger, self.players_db, picks, self.pick_order, index, "1", DYNASTY,
                [r["player_id"] for r in priced[:6]], mode="balanced")
            forfeits += [a["positional_forfeit"] for a in analysis
                         if a.get("positional_forfeit") is not None]
        self.assertTrue(forfeits, "no forfeits measured; this test observed nothing")
        share = sum(1 for f in forfeits
                    if f >= ps.NECESSITY_STANDOUT_REFERENCE_GAP) / len(forfeits)
        self.assertGreater(share, 0.5,
                           "cliff_protection has stopped firing for most candidates -- the "
                           "measurement in CDME_CONTRACTS.md is stale, revisit the decision")


if __name__ == "__main__":
    unittest.main()
