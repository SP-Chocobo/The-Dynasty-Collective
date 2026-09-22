"""A(#56) -- the constants contract, as executable invariants.

Three constants gate nine rules across six different quantities. Measured on the repaired
real-points unit:

    quantity                        p50      max    rule fires
    leader-second TAV margin        0.35    12.69      0.0%   <- "decisive"
    positional_forfeit             54.81   154.94     73.6%   <- cliff_protection
    TAV - UV (context)              6.12    13.21      7.8%   <- context_elevated (RETIRED #25)
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

The OTHER reuse -- context_elevated's threshold -- is GONE. That flag was RETIRED at the #25
ruling (2026-09-21): it fired on ONE row across all 36 battery formats while the quantity it read
has a mean of -3.46, so the open product decision this file used to record was answered by
removal rather than by a better number.
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

    def test_decisive_is_unreachable_while_survival_is_uncalibrated(self):
        """INVERTED, not deleted (#206). This asserted that "decisive" is REACHABLE, because an
        unreachable state carries no information. That reasoning still stands -- but the
        calibration evidence says the state's second condition rests on a quantity that loses
        to predicting the base rate, and loses WORST in exactly the band the threshold reads
        (0.0-0.1: predicted 0.028, observed 0.500 over 74 real pairs).

        So "decisive" is now unreachable ON PURPOSE, gated on SURVIVAL_IS_CALIBRATED, and this
        test pins the refusal.

        IT IS A TRIGGER, NOT A SILENCER. Flip SURVIVAL_IS_CALIBRATED to True and this test
        FAILS, which forces the reachability question to be re-answered against whatever
        evidence justified the flip -- rather than letting a repaired model quietly inherit a
        threshold nobody re-examined. Deleting the test would have lost that."""
        seen = set()
        for rounds, picks, _ in self._boards():
            index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                          if self.pick_order[i] == "1"), None)
            if index is None:
                continue
            snapshot = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order,
                                         index, "1", DYNASTY, pick_label=f"R{rounds + 1}")
            seen.add(snapshot.decision_regime)
        self.assertIn("contested", seen, "decision_regime produces neither of its states")
        self.assertFalse(
            ps.SURVIVAL_IS_CALIBRATED,
            "SURVIVAL_IS_CALIBRATED is True, so 'decisive' should be reachable again -- "
            "re-answer the reachability question against the evidence that justified the "
            "flip, and restore the reachability assertion below instead of this one")
        self.assertNotIn(
            "decisive", seen,
            "'decisive' fired while SURVIVAL_IS_CALIBRATED is False -- the calibration gate "
            "in decision_regime has been bypassed, and a UI state is now being driven by a "
            "survival estimate measured to lose to a constant predictor")

    def test_the_threshold_sits_below_the_leader_survival_floor(self):
        """WHY "decisive" is unreachable, measured rather than assumed -- and it is NOT the
        calibration gate.

        I added that gate and wrote that it was the cause. The vacuity check in this file
        disproved it: lift the gate and "decisive" STILL never fires on a real board. The
        actual cause is arithmetic, and it is a consequence of #206's own mass-conservation
        repair (364042a). Survival used to be far too LOW -- the symptom that opened #206 was
        0.00 for a player who then survived 60 picks. Normalising each opponent's take mass to
        sum to 1.0 raised it, and the leader's survival floor now sits ABOVE the threshold:

            leader survival across 8 real board states : min 0.212, max 0.925
            DECISIVE_SURVIVAL_THRESHOLD                : 0.15
            boards clearing the tie band               : 2 of 8   (not the blocker)
            boards with survival <= threshold          : 0 of 8   (the blocker)

        So the gate is belt-and-braces, and this is the load-bearing fact. Recorded here
        because a future reader who repairs calibration will flip the flag, find "decisive"
        still dead, and need to know the threshold was already below the distribution."""
        original = ps.SURVIVAL_IS_CALIBRATED
        try:
            ps.SURVIVAL_IS_CALIBRATED = True
            seen = set()
            for rounds, picks, _ in self._boards():
                index = next((i for i in range(rounds * NUM_TEAMS, len(self.pick_order))
                              if self.pick_order[i] == "1"), None)
                if index is None:
                    continue
                snapshot = ps.build_snapshot(self.merger, self.players_db, picks,
                                             self.pick_order, index, "1", DYNASTY,
                                             pick_label=f"R{rounds + 1}")
                seen.add(snapshot.decision_regime)
        finally:
            ps.SURVIVAL_IS_CALIBRATED = original
        self.assertIn("contested", seen,
                      "with the gate lifted the regime produces neither of its states, so "
                      "this probe is measuring nothing")
        self.assertNotIn(
            "decisive", seen,
            "'decisive' now fires with the gate lifted, so the threshold is no longer below "
            "the leader survival floor -- the arithmetic reason recorded in this docstring "
            "has gone stale and the reachability question is live again")


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

    #: A leader clear of the band with low survival. Used by both tests below, which ask two
    #: different questions of it: is the ARITHMETIC still right, and does the GATE still win.
    DECISIVE_SHAPED = [{"team_acquisition_value": 100.0, "survival_probability": 0.0},
                       {"team_acquisition_value": 100.0 - ps.NEAR_TIE_BAND * 2,
                        "survival_probability": 0.5}]

    def test_a_leader_clear_of_the_band_with_low_survival_is_decisive(self):
        """The ARITHMETIC, unchanged (#206). The calibration gate now short-circuits
        decision_regime before this logic runs, so the gate is lifted here deliberately --
        otherwise this test would pass for the gate's reason and stop testing the predicate it
        was written for, which is how a test quietly becomes a decoration."""
        original = ps.SURVIVAL_IS_CALIBRATED
        try:
            ps.SURVIVAL_IS_CALIBRATED = True
            self.assertEqual(ps.decision_regime(self.DECISIVE_SHAPED), "decisive")
        finally:
            ps.SURVIVAL_IS_CALIBRATED = original

    def test_the_calibration_gate_overrides_a_decisive_shaped_board(self):
        """And the gate wins over that same board while survival is uncalibrated. Paired with
        the test above so the two facts cannot drift: the predicate still says decisive, and
        production still refuses to."""
        self.assertFalse(ps.SURVIVAL_IS_CALIBRATED)
        self.assertEqual(ps.decision_regime(self.DECISIVE_SHAPED), "contested")

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
        # RE-MEASURED AFTER #216. This pinned `share > 0.5` ("fires for most candidates", 73.6%
        # in CDME_CONTRACTS.md), and the #216 term moved it: the top six rows of these boards
        # are no longer dominated by a hoarded position's steep tail, and the forfeit of the
        # receivers that replaced them clears the reference gap less often -- measured 17 of 48
        # (35.4%) on the same states. The threshold is exactly as borrowed as it was (the
        # constant did not change; the population it is compared against did), so the pin is
        # restated, not repaired: the flag is neither near-universal nor rare, and the
        # product decision about what SHOULD light it remains open. Both bounds below are the
        # measured value's neighbourhood, recorded so the next drift is noticed here as this
        # one was; neither is a claim about what the rate should be.
        self.assertGreater(share, 0.0, "cliff_protection never fires -- revisit the decision")
        self.assertLess(share, 0.5,
                        "cliff_protection is back to firing for most candidates -- the "
                        "measurement in CDME_CONTRACTS.md is stale, revisit the decision")



class TheTwoCappedTermsAreMutuallyExclusiveTests(_RealBoards):
    """6.1d.1. The structural fact that OUTLIVED the constant it was derived for.

    The threshold was `sum(TEAM_SPECIFIC_CAPS) / len(...)`, described in its own comment as
    "one term's worth of lift on a quantity that can hold three" -- and the comment claimed
    that expressing it that way made the relationship "stop being a coincidence". It did not:
    the mean equals the max here ONLY because the surviving caps happen to be equal, so a
    change to either one would silently move the threshold somewhere the quantity cannot reach.

    What is true is stronger and simpler. `need_bonus` is large when a slot at the position is
    EMPTY; `depth_exposure` requires SURPLUS there. Opposite roster states, so the two never
    carry value together -- and the gap's ceiling is therefore max(), not sum() and not mean().

    Measured across 4 formats x 8 in-draft board states, 10,887 priced rows (9,793 carrying a
    nonzero value on at least one term): ZERO rows carry both. This pins that over the boards
    this class already builds, so a change that lets them co-occur fails here rather than
    quietly making the threshold wrong.
    """

    def test_need_bonus_and_depth_exposure_never_both_carry_value(self):
        both, either = [], 0
        for rounds, _picks, board in self._boards():
            for row in board:
                nb = row.get("need_bonus") or 0.0
                de = row.get("depth_exposure") or 0.0
                if nb > 0 or de > 0:
                    either += 1
                if nb > 0 and de > 0:
                    both.append((rounds, row.get("name"), nb, de))
        self.assertGreater(either, 0, "no row carries either term; this test observed nothing")
        self.assertEqual(both[:5], [], (
            "need_bonus and depth_exposure now co-occur, so the gap's ceiling is no longer "
            "max(TEAM_SPECIFIC_CAPS), which NECESSITY_DENIAL_SATURATION's sibling "
            "derivation and any future reader of this tuple depend on"))

    #: Two tests lived here and went with the constant at #25: one asserting the threshold took
    #: the FORM max(TEAM_SPECIFIC_CAPS) rather than their mean, and its companion pinning that
    #: the two caps were still EQUAL -- so the day they diverged, the first assertion would start
    #: doing real work and the second would say so out loud. Both described a constant that no
    #: longer exists. Their names are not backticked here for the reason test_prose_names gives:
    #: backticks assert a live identifier, and this line failed that guard when it had them.
    #:
    #: The mutual-exclusion measurement they rested on is above and is UNAFFECTED -- it is about
    #: need_bonus and depth_exposure, not about anything that reads them, and
    #: NECESSITY_DENIAL_SATURATION still derives from the same tuple.


#: A ContextElevatedBecameReachableTests CLASS LIVED HERE AND IS RETIRED (#25, ruled
#: 2026-09-21). Deliberately NOT backticked: backticks in this repo assert a live
#: identifier, and test_prose_names failed on this line when it was written with them --
#: correctly, because the class is gone. A retired name is prose, not a reference.
#:
#: It carried the two expectedFailures that recorded the badge's deadness, and its own docstring
#: had already filed the warning that settled the ruling: "a number that became a discriminator
#: because the quantity underneath it grew is still a bound being read as a threshold (#56), and
#: the open product decision on what SHOULD light this badge is untouched."
#:
#: The decision came: RETIRE. `context_elevated` fired on ONE row across all 36 battery formats
#: -- a multi-eligible WR/DB lifted +79.44 by displacement_adj -- while the quantity it read has
#: a MEAN of -3.46 across 10,887 priced rows. The class is removed rather than left failing,
#: because an expectedFailure is a statement that something SHOULD become true again, and
#: nothing here should. The measurement is kept at
#: evidence/context_elevated/THE_CEILING_IS_MAX_NOT_SUM.md.
#:
#: What survives in this file is the fact underneath, one class up: the two capped terms are
#: mutually exclusive. That is a property of `need_bonus` and `depth_exposure` and outlives the
#: flag that happened to read them.
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

    # STILL AN EXPECTED FAILURE, and unlike the two above this one is genuine: the premium
    # really does not clear one term's cap on the corrected pool, so #144's premise is gone and
    # this class has lost its subject. Re-measured at #52 phase 6 after the canonical-key repair
    # put four withheld players back in the pool: max(rival_premium) = 10.57 against
    # NEED_BONUS_MAX 12.0, over 96 measured premiums. It was recorded here as 11.85, which was
    # measured before that repair -- the mark was right and its number had rotted, which is the
    # same decay the misquoted-constant guard exists to catch one file over.
    @unittest.expectedFailure
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
        rival_premium sums draft_room's capped team-specific terms, so its bound is their sum.
        A term added later moves this automatically -- which is exactly what did not happen
        when #139 added the third, and is the whole mechanism of the original defect.

        BOTH DIRECTIONS, since 6.1b. This docstring anticipated only ADDITION and the
        assertion hand-listed the three caps, so a term LEAVING failed it -- the saturation
        had tracked the removal correctly (36.0 -> 24.0) and the test's private copy of the
        list had not. Asserted against the tuple the constant is actually derived from, which
        moves in either direction without anyone editing this line."""
        self.assertAlmostEqual(ps.NECESSITY_DENIAL_SATURATION, sum(ps.TEAM_SPECIFIC_CAPS))
        self.assertTrue(ps.TEAM_SPECIFIC_CAPS, "no caps: the sum above asserts nothing")
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
