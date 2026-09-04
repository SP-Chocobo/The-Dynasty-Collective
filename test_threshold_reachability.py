"""A(#56) -- the constants contract, as executable invariants.

Three constants gate nine rules across six different quantities. Measured on the repaired
real-points unit:

    quantity                        p50      max    rule fires
    leader-second TAV margin        0.35    12.69      0.0%   <- "decisive"
    positional_forfeit             54.81   154.94     73.6%   <- cliff_protection
    TAV - UV (context)              6.12    13.21      7.8%   <- context_elevated
    TAV adjacent gap                0.54    56.85     15.7%   <- near_tie
    bpa gap within a position       2.00    71.00     58.5%   <- CLIFF_MIN_MATERIAL_GAP

The same literal 15.0 gates two quantities whose medians differ by 150x. That is not one
contract with one number; it is several concepts that happen to share a literal.

The context row was re-measured 2026-09-03, after #139 added depth_exposure as a third
team-specific term: `TAV - UV` used to be capped near NEED_BONUS_MAX and fired 0.0% of the
time. It now clears it on 7.8% of priced rows. NOTHING WAS FIXED -- the constant never moved;
the quantity underneath it grew. See ContextElevatedBecameReachableTests, which is where that
distinction is kept from being forgotten.

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

ONE OF THE TWO REUSES IS NOW REPAIRED (#144, 2026-09-04). pick_necessity's denial ramp divided
by NEED_BONUS_MAX -- one term's cap -- while normalizing rival_premium, which SUMS three of
them. It now saturates at the sum, derived from draft_room's own caps so a fourth term moves it
automatically. The repair is narrower than the item proposed, and the measurement is why:
moving the divisor alone would have been a 3x DE-WEIGHTING of denial wearing a saturation
repair's clothes (478/7046 pairs reorder, 259 of them at a round where nothing clips). The
ceiling had to move with it. See TheDenialNormalizerSaturatesAtItsOwnBoundTests.

The OTHER reuse -- context_elevated's threshold at NEED_BONUS_MAX -- is untouched and still an
open product decision; see ContextElevatedBecameReachableTests for why its reachability is an
accident of the quantity growing rather than a number anyone chose.
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
    """Rules whose thresholds are still bounds borrowed as thresholds. These are recorded as
    executable measurements rather than repaired, because choosing what SHOULD fire them is a
    product decision and no evidence in this repository determines it. They are asserted to
    still be unreachable so that a future change to either constant is noticed here, and so the
    claim in CDME_CONTRACTS.md cannot silently rot.

    context_elevated USED TO LIVE HERE and no longer does -- see
    ContextElevatedBecameReachableTests below for what moved it and why the move is not a
    repair of the constant."""

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



class ContextElevatedBecameReachableTests(_RealBoards):
    """The one rule that escaped the class above, and NOT because anyone chose a better number.

    NEED_BONUS_MAX was always a cap on ONE term. When context_elevated was written, that term
    plus eligibility_bonus were the whole of `team_acquisition_value - universal_value`, so a
    threshold set at the cap of one of them was a threshold at roughly the ceiling of the
    quantity: measured at 0.0% firing, max gap 8.67, and recorded in CDME_CONTRACTS.md as dead.

    #139 added depth_exposure as a THIRD team-specific term. The gap's ceiling tripled, the
    constant did not move, and the same literal that was sitting at the top of the old
    distribution now sits inside the new one. That is the whole of what changed.

    So this is deliberately not filed as "the threshold is now correct". A number that became
    a discriminator because the quantity underneath it grew is still a bound being read as a
    threshold (#56), and the open product decision on what SHOULD light this badge is
    untouched. What HAS changed, and what is worth pinning, is that the two failure modes the
    module docstring names -- a threshold above its distribution (dead) and a threshold far
    below it (always on, no information) -- are both currently absent. Both directions are
    asserted, so drifting into either one fails here."""

    def _gaps(self):
        gaps = []
        for _, _, board in self._boards():
            gaps += [row["final_score"] - row["universal_value"] for row in board
                     if row.get("final_score") is not None
                     and row.get("universal_value") is not None]
        return gaps

    def test_it_fires_and_fires_selectively(self):
        gaps = self._gaps()
        self.assertTrue(gaps, "no priced rows measured; this test observed nothing")
        share = sum(1 for g in gaps if g >= dr.NEED_BONUS_MAX) / len(gaps)
        # Measured 2026-09-03: 7.8% of 1992 priced rows across the eight sampled board states,
        # concentrated entirely in rounds 6-8 -- the window where a bench exists for depth to
        # be a real question about and positional holes are still open. Both bounds below are
        # wide on purpose: they are there to catch a rule going dead or going always-on, not
        # to pin a rate nobody has argued for.
        self.assertGreater(share, 0.0,
                           "context_elevated is dead again -- the gap no longer reaches "
                           "NEED_BONUS_MAX on any real board, so the badge can never light")
        self.assertLess(share, 0.5,
                        "context_elevated now fires for most candidates -- the same failure "
                        "cliff_protection has, in the other direction: a flag that is almost "
                        "always on carries almost no information")

    def test_the_cap_no_longer_caps_the_quantity_it_is_compared_against(self):
        """The structural fact underneath the change, asserted rather than narrated: three
        additive team-specific terms now feed the gap, so a cap on one of them is no longer an
        upper bound on their sum. This is what makes the reachability real rather than a data
        wobble, and it fails if a term is ever removed without revisiting the threshold."""
        self.assertAlmostEqual(dr.NEED_BONUS_MAX, 3 * dr.NEED_BONUS_PER_DEDICATED_SLOT)
        self.assertGreater(max(self._gaps()), dr.NEED_BONUS_MAX)
        # The three terms, each independently capped at NEED_BONUS_MAX.
        self.assertAlmostEqual(dr.ELIGIBILITY_BONUS_MAX, dr.NEED_BONUS_MAX)
        self.assertAlmostEqual(dr.DEPTH_EXPOSURE_MAX, dr.NEED_BONUS_MAX)



class TheDenialNormalizerSaturatesAtItsOwnBoundTests(_RealBoards):
    """#144, CLOSED -- and the close is the opposite of what the item proposed.

    pick_necessity's denial term is a saturating ramp on rival_premium, which is
    `(rival TAV - rival UV)` computed on the RIVAL's own board -- the SUM of draft_room's
    team-specific terms. It picked up #139's third term automatically and correctly; the
    divisor did not follow, and NEED_BONUS_MAX (the cap on ONE term) stopped being an upper
    bound on the quantity. It clipped, and a clipped normalizer is not a smaller version of
    the same signal -- it is the SAME number for every candidate above the bar.

    The proposed repair was "divisor -> the sum of all three caps", held back because it
    "changes every round's denial contribution by 3x to fix a tail". THAT WAS THE RIGHT
    INSTINCT AND THE WRONG DIAGNOSIS. Below saturation the term is `premium x (WEIGHT/DIVISOR)`,
    so divisor and weight are ONE SLOPE. Moving the divisor alone is not a saturation repair at
    all; it is a 3x de-weighting of denial that happens to also remove the clip. Measured over
    six real turns, 272 candidates:

        divisor 36, weight held    478/7046 pairs reorder, 54/272 labels flip, mean necessity
                                   -3 to -4.5. 259 of those inversions are at ROUND 4, where
                                   NOTHING CLIPS -- proof it is re-weighting, not saturation.
        both scaled (shipped)        7/7046 pairs reorder, 1/272 labels flip, max change 0.9,
                                   and `rows changed` == `rows clipped` on every turn.

    So the ramp now saturates at the quantity's own bound while the rate stays exactly where it
    was calibrated. These tests pin BOTH halves: that the flat spot is gone, and that the rate
    did not move while removing it -- because either one alone is a way to get this wrong."""

    def _premiums(self):
        out = []
        for rounds, picks, board in self._boards():
            index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                          if self.pick_order[i] == "1"), None)
            priced = [r for r in board if r.get("final_score") is not None]
            if index is None or len(priced) < 4:
                continue
            analysis = ds.pick_analysis(
                self.merger, self.players_db, picks, self.pick_order, index, "1", DYNASTY,
                [r["player_id"] for r in priced[:12]], mode="balanced")
            out += [a.get("rival_premium") or 0.0 for a in analysis]
        return out

    def test_the_premium_still_exceeds_one_terms_cap(self):
        """Non-vacuity for the whole class. If rival_premium stopped clearing NEED_BONUS_MAX,
        the old divisor would be an upper bound again and none of this would be load-bearing --
        so the repair would be untestable rather than unnecessary, which is worth failing on."""
        premiums = self._premiums()
        self.assertTrue(premiums, "no rival premiums measured; this test observed nothing")
        # Measured 2026-09-03: max 16.21 against one term's cap of 12.0. Before #139: max 8.33.
        self.assertGreater(max(premiums), dr.NEED_BONUS_MAX,
                           "rival_premium no longer exceeds one team-term's cap -- #144's "
                           "premise is gone and this class has lost its subject")

    def test_the_flat_spot_is_gone(self):
        """The repair's actual claim. Nothing may sit at or above the saturation point, because
        everything there receives an identical denial contribution regardless of how much more
        a rival wants it."""
        premiums = self._premiums()
        clipped = [p for p in premiums if p >= ps.NECESSITY_DENIAL_SATURATION]
        self.assertEqual(
            [], clipped,
            f"{len(clipped)} of {len(premiums)} rival premiums reach the saturation point "
            f"({ps.NECESSITY_DENIAL_SATURATION}) and are again indistinguishable from each "
            f"other; the ramp has re-flattened and #144 is open again",
        )

    def test_the_saturation_point_is_derived_from_every_term_it_sums(self):
        """Why the flat spot went away, asserted structurally rather than left to the data.
        rival_premium sums draft_room's three team-specific terms, so its bound is their sum.
        A FOURTH term added later moves this automatically -- which is exactly what did not
        happen when #139 added the third, and is the whole mechanism of the original defect."""
        self.assertAlmostEqual(
            ps.NECESSITY_DENIAL_SATURATION,
            dr.NEED_BONUS_MAX + dr.ELIGIBILITY_BONUS_MAX + dr.DEPTH_EXPOSURE_MAX)
        self.assertGreater(ps.NECESSITY_DENIAL_SATURATION, max(self._premiums()))

    def test_removing_the_flat_spot_did_not_re_weight_the_term(self):
        """The other half, and the one an eager repair gets wrong. The ceiling and the
        saturation point are one slope; moving only the divisor would have cut denial's
        calibrated influence to a third while appearing to fix a tail (measured: 478 of 7046
        pairs reorder, 259 of them at a round where nothing clips at all)."""
        self.assertAlmostEqual(
            ps.NECESSITY_DENIAL_CEILING / ps.NECESSITY_DENIAL_SATURATION,
            ps.NECESSITY_DENIAL_WEIGHT / dr.NEED_BONUS_MAX, places=9,
            msg="the denial rate moved; the repair has become a re-weighting")


if __name__ == "__main__":
    unittest.main()
