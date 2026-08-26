"""
Covers pick_synthesis.py's real job: turning draft_room.py/draft_strategy.py's numbers into one
frozen, fully decomposed snapshot without inventing or recomputing any of them, plus the two
genuinely new pieces this module adds (positional_cliff, expected_value_of_waiting) and the
structured audit-trail diff (diff_snapshots) the whole "Debate My Pick" feature was built to
support.
"""

import unittest

import dataclasses

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps

SUPERFLEX_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "SUPER_FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}

LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}


def _row(player_id, position, bpa):
    return {"player_id": player_id, "position": position, "bpa": bpa}


class DetectPositionalCliffTests(unittest.TestCase):
    def test_a_big_gap_relative_to_the_positions_typical_gap_is_a_high_cliff(self):
        board = [
            _row("1", "WR", 95.0), _row("2", "WR", 60.0),  # 35-point gap here
            _row("3", "WR", 57.0), _row("4", "WR", 54.0), _row("5", "WR", 51.0),  # ~3-point typical gaps
        ]
        result = ps.detect_positional_cliff(board, "1")
        self.assertEqual(result["tier"], "HIGH")
        self.assertAlmostEqual(result["gap"], 35.0)

    def test_a_gap_in_line_with_the_positions_typical_gap_is_low(self):
        board = [_row(str(i), "RB", 90.0 - i * 3) for i in range(6)]  # perfectly uniform 3-point gaps
        result = ps.detect_positional_cliff(board, "0")
        self.assertEqual(result["tier"], "LOW")

    def test_none_when_the_player_is_the_last_one_left_at_his_position(self):
        board = [_row("1", "TE", 40.0), _row("2", "TE", 10.0), _row("3", "TE", 5.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "3"))

    def test_none_when_too_few_players_remain_at_the_position(self):
        board = [_row("1", "TE", 40.0), _row("2", "TE", 10.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "1"))

    def test_none_when_the_player_is_not_on_the_board(self):
        board = [_row("1", "WR", 90.0), _row("2", "WR", 80.0), _row("3", "WR", 70.0)]
        self.assertIsNone(ps.detect_positional_cliff(board, "999"))

    def test_a_structural_cliffs_own_giant_gaps_cannot_inflate_the_typical_yardstick(self):
        # The contamination case measured on the real baseline: a position with a genuine
        # structural cliff carries that cliff's own giant gaps in its gap list, which pulled
        # the plain median up until the cliff's leading edge read LOW against a yardstick the
        # cliff itself had inflated. Trimming the largest ~10% first restores the yardstick.
        # 14 players: a tier of small 2-point gaps, a 6-point leading edge at "6", then a
        # scrub tail whose giant 30/25/20-point drops are the contamination.
        board = (
            [_row(str(i), "QB", 100.0 - i * 2) for i in range(7)]        # 100..88, 2-pt gaps
            + [_row("7", "QB", 80.0)]                                     # 6-pt leading edge
            + [_row("8", "QB", 78.0), _row("9", "QB", 76.0)]
            + [_row("10", "QB", 46.0), _row("11", "QB", 21.0),            # the cliff's own
               _row("12", "QB", 1.0), _row("13", "QB", 0.5)]              # giant gaps
        )
        result = ps.detect_positional_cliff(board, "6")  # the 88.0 player, 6-pt gap to 80.0
        # Plain median over the 12 other positive gaps is 2.0 -- but WITH the 30/25/20 tail
        # included the upper half shifts and a trimmed median must still call 6.0 vs 2.0 a
        # real (3x) HIGH cliff rather than letting the tail's giants make it look ordinary.
        self.assertEqual(result["tier"], "HIGH")
        self.assertAlmostEqual(result["typical_gap"], 2.0)

    def test_small_pools_keep_the_plain_median_unchanged(self):
        # Below the trim threshold there's no meaningful "largest 10%" to drop -- behavior
        # must be byte-identical to the untrimmed detector for small pools.
        board = [
            _row("1", "WR", 95.0), _row("2", "WR", 60.0),
            _row("3", "WR", 57.0), _row("4", "WR", 54.0), _row("5", "WR", 51.0),
        ]
        result = ps.detect_positional_cliff(board, "1")
        self.assertEqual(result["tier"], "HIGH")
        self.assertAlmostEqual(result["typical_gap"], 3.0)


class ExpectedValueOfWaitingTests(unittest.TestCase):
    def test_none_when_survival_is_unknown(self):
        self.assertIsNone(ps.expected_value_of_waiting(90.0, None))

    def test_scales_universal_value_by_survival_probability(self):
        self.assertEqual(ps.expected_value_of_waiting(90.0, 0.2), 18.0)

    def test_certain_survival_returns_full_universal_value(self):
        self.assertEqual(ps.expected_value_of_waiting(90.0, 1.0), 90.0)


class NarrowCandidatesTests(unittest.TestCase):
    def _board(self):
        return [{"player_id": str(i), "final_score": 100 - i, "position": "WR"} for i in range(10)]

    def test_takes_the_top_n_by_final_score(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3)
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])

    def test_appends_a_user_selected_player_not_already_in_the_top_slice(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="7")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2", "7"])

    def test_does_not_duplicate_a_user_selected_player_already_in_the_top_slice(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="1")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])

    def test_a_user_selected_player_not_on_the_board_at_all_is_silently_skipped(self):
        narrowed = ps.narrow_candidates(self._board(), top_n=3, user_selected_player_id="does-not-exist")
        self.assertEqual([r["player_id"] for r in narrowed], ["0", "1", "2"])

    def test_a_scarce_positions_best_player_is_included_even_outside_the_top_n(self):
        # The real fix: a thin position's single best remaining player used to be silently
        # EXCLUDED from the whole downstream strategic analysis whenever nobody at that
        # position cracked the raw top_n by value -- not just ranked low, literally never
        # handed to survival/denial/necessity at all. Best QB here (value 40) ranks outside
        # a top_n=3 WR/RB-dominated slice; he must still show up.
        board = [
            {"player_id": "rb1", "final_score": 100, "position": "RB"},
            {"player_id": "wr1", "final_score": 95, "position": "WR"},
            {"player_id": "rb2", "final_score": 90, "position": "RB"},
            {"player_id": "wr2", "final_score": 80, "position": "WR"},
            {"player_id": "qb1", "final_score": 40, "position": "QB"},
            {"player_id": "qb2", "final_score": 30, "position": "QB"},
        ]
        narrowed = ps.narrow_candidates(board, top_n=3)
        ids = [r["player_id"] for r in narrowed]
        self.assertIn("qb1", ids)
        self.assertNotIn("qb2", ids, "only the BEST remaining player at a position gets this guarantee, not the whole position")
        # Full list stays ranked by value even after the addition.
        values = [r["final_score"] for r in narrowed]
        self.assertEqual(values, sorted(values, reverse=True))

    def _multi_position_board(self):
        board = []
        for pos, count in (("RB", 8), ("WR", 8), ("QB", 4), ("TE", 3)):
            for i in range(count):
                board.append({"player_id": f"{pos}{i}", "final_score": 100 - i, "position": pos})
        return board

    def test_position_depth_none_preserves_the_original_single_best_per_position_behavior(self):
        # The whole existing test corpus (and every caller that predates this parameter) relies
        # on this default staying exactly what it always was.
        narrowed = ps.narrow_candidates(self._multi_position_board(), top_n=1, position_depth=None)
        ids = {r["player_id"] for r in narrowed}
        self.assertEqual(ids, {"RB0", "WR0", "QB0", "TE0"})

    def test_position_depth_surfaces_real_depth_at_the_requested_position(self):
        narrowed = ps.narrow_candidates(
            self._multi_position_board(), top_n=1, position_depth={"WR": 5, "RB": 1, "QB": 1, "TE": 1},
        )
        wr_ids = {r["player_id"] for r in narrowed if r["position"] == "WR"}
        self.assertEqual(wr_ids, {"WR0", "WR1", "WR2", "WR3", "WR4"})
        # A position with depth 1 stays at exactly its single best, same as the old default.
        self.assertEqual({r["player_id"] for r in narrowed if r["position"] == "QB"}, {"QB0"})

    def test_position_depth_larger_than_the_available_pool_just_takes_everything_there(self):
        narrowed = ps.narrow_candidates(
            self._multi_position_board(), top_n=1, position_depth={"TE": 50, "RB": 1, "WR": 1, "QB": 1},
        )
        te_ids = {r["player_id"] for r in narrowed if r["position"] == "TE"}
        self.assertEqual(te_ids, {"TE0", "TE1", "TE2"})

    def test_position_depth_does_not_duplicate_rows_already_in_the_top_n_slice(self):
        # top_n=3 already covers RB0/WR0/RB1 (values 100/100... use distinct scores for clarity)
        board = [
            {"player_id": "rb1", "final_score": 100, "position": "RB"},
            {"player_id": "rb2", "final_score": 99, "position": "RB"},
            {"player_id": "wr1", "final_score": 98, "position": "WR"},
        ]
        narrowed = ps.narrow_candidates(board, top_n=3, position_depth={"RB": 2, "WR": 1})
        ids = [r["player_id"] for r in narrowed]
        self.assertEqual(sorted(ids), ["rb1", "rb2", "wr1"], "no duplicate rows from the position_depth pass")

    def test_result_stays_ranked_by_final_score_with_position_depth_applied(self):
        narrowed = ps.narrow_candidates(
            self._multi_position_board(), top_n=1, position_depth={"WR": 6, "RB": 4, "QB": 2, "TE": 1},
        )
        values = [r["final_score"] for r in narrowed]
        self.assertEqual(values, sorted(values, reverse=True))


class PositionViewDepthTests(unittest.TestCase):
    """Position View Depth = min(league replacement demand for the position,
    POSITION_VIEW_DEPTH_CAP) -- the exact boundary behavior requested: a thin position's real
    demand passes through untouched, a deep one is capped at the ceiling, never expanded past
    its own real demand."""

    def test_replacement_below_the_cap_shows_the_full_replacement_count(self):
        self.assertEqual(ps.position_view_depth(6), 6)

    def test_replacement_exactly_at_the_cap_shows_exactly_the_cap(self):
        self.assertEqual(ps.position_view_depth(ps.POSITION_VIEW_DEPTH_CAP), ps.POSITION_VIEW_DEPTH_CAP)

    def test_replacement_well_above_the_cap_is_truncated_to_the_cap(self):
        self.assertEqual(ps.position_view_depth(20), ps.POSITION_VIEW_DEPTH_CAP)
        self.assertEqual(ps.position_view_depth(33), ps.POSITION_VIEW_DEPTH_CAP)


def _raw_candidate(team_acquisition_value, survival_probability=1.0, positional_cliff=None,
                    position_run_detected=False, rival_premium=0.0, need_bonus=0.0, eligibility_bonus=0.0):
    return {
        "team_acquisition_value": team_acquisition_value, "survival_probability": survival_probability,
        "positional_cliff": positional_cliff, "position_run_detected": position_run_detected,
        "rival_premium": rival_premium, "need_bonus": need_bonus, "eligibility_bonus": eligibility_bonus,
    }


class ComputePickNecessityTests(unittest.TestCase):
    def test_pick_necessity_is_never_just_universal_value_in_disguise(self):
        # The exact case the user built this feature to distinguish: a WORSE player (lower
        # team_acquisition_value) with severe scarcity pressure must be able to outscore a
        # BETTER player sitting in an uncontested, deep position.
        worse_player_facing_a_cliff = _raw_candidate(
            90.0, survival_probability=0.1, positional_cliff={"tier": "HIGH", "gap": 10, "typical_gap": 2},
            position_run_detected=True, rival_premium=8.0,
        )
        better_player_no_pressure_at_all = _raw_candidate(97.0, survival_probability=1.0)
        results = ps.compute_pick_necessity([worse_player_facing_a_cliff, better_player_no_pressure_at_all], round_num=3)
        self.assertGreater(results[0][0], results[1][0])

    def test_a_tightly_bunched_field_stays_near_the_close_call_baseline(self):
        # "Multiple valid directions are 50s" -- three candidates with near-identical
        # team_acquisition_value and no scarcity pressure at all should all land close to the
        # NECESSITY_BASELINE, not a manufactured spread.
        candidates = [_raw_candidate(100.0), _raw_candidate(99.5), _raw_candidate(99.0)]
        results = ps.compute_pick_necessity(candidates, round_num=3)
        for score, label in results:
            self.assertLess(abs(score - ps.NECESSITY_BASELINE), 15.0)
            self.assertIn(label, ("CLOSE CALL", "LOW URGENCY", "PREFERRED"))

    def test_a_real_standout_with_full_scarcity_pressure_reaches_must_take(self):
        standout = _raw_candidate(
            120.0, survival_probability=0.02, positional_cliff={"tier": "HIGH", "gap": 20, "typical_gap": 2},
            position_run_detected=True, rival_premium=12.0, need_bonus=10.0, eligibility_bonus=5.0,
        )
        distant_second = _raw_candidate(60.0)
        results = ps.compute_pick_necessity([standout, distant_second], round_num=3)
        self.assertGreaterEqual(results[0][0], 90.0)
        self.assertEqual(results[0][1], ps._necessity_label(results[0][0]))

    def test_the_sole_candidate_in_a_snapshot_gets_full_standout_credit(self):
        only_option = _raw_candidate(50.0)
        results = ps.compute_pick_necessity([only_option], round_num=3)
        self.assertGreaterEqual(results[0][0], ps.NECESSITY_BASELINE + ps.NECESSITY_STANDOUT_WEIGHT - 1e-6)

    def test_late_round_necessity_is_rescaled_into_a_low_band_not_a_flat_identical_number(self):
        # A late-round standout and a late-round toss-up must NOT collapse to one identical
        # value -- that's exactly the IDP-percentile-collapse failure mode this app's own
        # history already flagged as a real bug, not a stylistic nitpick.
        standout = _raw_candidate(120.0, survival_probability=0.05, positional_cliff={"tier": "HIGH", "gap": 20, "typical_gap": 2})
        toss_up = _raw_candidate(100.0)
        late_round = ps.LATE_ROUND_THRESHOLD
        results = ps.compute_pick_necessity([standout, toss_up], round_num=late_round)
        self.assertLessEqual(results[0][0], ps.LATE_ROUND_NECESSITY_CAP + 1e-6)
        self.assertLessEqual(results[1][0], ps.LATE_ROUND_NECESSITY_CAP + 1e-6)
        self.assertGreater(results[0][0], results[1][0], "a real late-round standout must still outscore a late-round toss-up")

    def test_necessity_label_thresholds_are_applied_correctly(self):
        self.assertEqual(ps._necessity_label(99.0), "MUST TAKE")
        self.assertEqual(ps._necessity_label(90.0), "STRONG ACTION")
        self.assertEqual(ps._necessity_label(70.0), "PREFERRED")
        self.assertEqual(ps._necessity_label(55.0), "CLOSE CALL")
        self.assertEqual(ps._necessity_label(35.0), "LOW URGENCY")
        self.assertEqual(ps._necessity_label(10.0), "DOESN'T MATTER MUCH")

    def test_trailing_the_leader_is_neutral_not_an_active_penalty(self):
        # The real bug this floor fixes, confirmed live: a genuinely strong QB1 sitting ~40
        # acquisition points behind the board's best RB, and a clearly weaker TE sitting ~60
        # points behind that same RB, both saturated to the identical -30 standout penalty --
        # collapsing two very different situations into nearly the same necessity score,
        # despite one of them still being a live, defensible pick. A candidate trailing the
        # leader must score no WORSE on this term than one exactly tied with the leader (0
        # contribution either way) -- trailing must never actively drag necessity down.
        # Differentiating "40 back" from "60 back" is intentionally NOT this term's job
        # anymore -- that's left to the other real signals (survival, cliff, run, denial,
        # roster fit), so with none of those set here the two trailing candidates come out
        # equal to each other, and equal to a candidate tied with the leader.
        leader = _raw_candidate(109.0)
        moderately_behind = _raw_candidate(69.63)   # ~39 back -- still a real, live option
        far_behind = _raw_candidate(50.41)          # ~59 back -- clearly a lesser pick
        tied_with_leader = _raw_candidate(109.0)
        results = ps.compute_pick_necessity(
            [leader, moderately_behind, far_behind, tied_with_leader], round_num=3,
        )
        moderately_score = results[1][0]
        far_score = results[2][0]
        tied_score = results[3][0]
        self.assertGreaterEqual(moderately_score, tied_score - 1e-6)
        self.assertGreaterEqual(far_score, tied_score - 1e-6)
        self.assertAlmostEqual(moderately_score, far_score, places=6)

    def test_denial_component_is_take_probability_free(self):
        # The double-count this fixed, measured at r = +0.82 between the survival and denial
        # components before the split: denial_value carried the same p_take that already
        # compounds into survival_probability. The necessity denial term now reads ONLY the
        # p_take-free rival_premium -- so two candidates with the identical premium but very
        # different survival must differ by exactly their survival components and nothing
        # else, and the premium itself caps at draft_room's own NEED_BONUS_MAX scale.
        import draft_room as dr
        same_premium_safe = _raw_candidate(100.0, survival_probability=1.0, rival_premium=6.0)
        same_premium_risky = _raw_candidate(100.0, survival_probability=0.5, rival_premium=6.0)
        results = ps.compute_pick_necessity([same_premium_safe, same_premium_risky], round_num=3)
        survival_delta = 0.5 * ps.NECESSITY_SURVIVAL_WEIGHT
        self.assertAlmostEqual(results[1][0] - results[0][0], survival_delta, places=6)

        # Premium scales the component linearly up to the NEED_BONUS_MAX cap, then saturates.
        half = _raw_candidate(100.0, rival_premium=dr.NEED_BONUS_MAX / 2)
        full = _raw_candidate(100.0, rival_premium=dr.NEED_BONUS_MAX)
        beyond = _raw_candidate(100.0, rival_premium=dr.NEED_BONUS_MAX * 10)
        r = ps.compute_pick_necessity([half, full, beyond], round_num=3)
        self.assertAlmostEqual(r[1][0] - r[0][0], ps.NECESSITY_DENIAL_WEIGHT / 2, places=6)
        self.assertAlmostEqual(r[2][0], r[1][0], places=6)

    def test_necessity_never_leaves_the_0_to_100_range(self):
        extreme = _raw_candidate(
            1000.0, survival_probability=0.0, positional_cliff={"tier": "HIGH", "gap": 999, "typical_gap": 1},
            position_run_detected=True, rival_premium=1000.0, need_bonus=50.0, eligibility_bonus=50.0,
        )
        results = ps.compute_pick_necessity([extreme, _raw_candidate(1.0)], round_num=3)
        for score, _label in results:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)


class NearTieFlagsTests(unittest.TestCase):
    """NEAR_TIE_BAND is data-derived (see its own comment: median adjacent tav gap 1.23,
    p75 2.26 on a real fresh superflex board) -- what these tests lock down is the SEMANTICS:
    band membership is measured against the leader, the leader belongs to his own tie group,
    and a leader nobody is close to is not 'in a tie' with anyone."""

    def test_candidates_within_the_band_of_the_leader_form_a_tie_group(self):
        flags = ps.near_tie_flags([100.0, 99.2, 98.1, 95.0])
        self.assertEqual(flags, [True, True, True, False])

    def test_a_clear_leader_alone_is_not_flagged_as_tied_with_himself(self):
        flags = ps.near_tie_flags([100.0, 95.0, 90.0])
        self.assertEqual(flags, [False, False, False])

    def test_band_is_measured_against_the_leader_not_chained_adjacency(self):
        # 100 / 98.5 / 97.0: each ADJACENT gap is 1.5 (inside the band), but 97.0 sits 3.0
        # behind the leader -- a chain of small steps must not stretch the tie group.
        flags = ps.near_tie_flags([100.0, 98.5, 97.0])
        self.assertEqual(flags, [True, True, False])

    def test_empty_and_singleton_inputs(self):
        self.assertEqual(ps.near_tie_flags([]), [])
        self.assertEqual(ps.near_tie_flags([50.0]), [False])


class DecisionPathFlagsTests(unittest.TestCase):
    """decision_path_flags reuses EXISTING engine constants as its boundaries -- these tests
    pin that reuse (each boundary is asserted against the constant itself, not a copied
    literal) and the rule that the flags classify without ever changing a score."""

    def _cand(self, uv, tav, forfeit=None, premium=0.0, take_prob=1.0):
        # take_prob defaults to 1.0 (fully credible) so every PRE-EXISTING test in this class
        # -- none of which cares about the credible-path gate -- keeps exercising exactly the
        # boundary it was written to test, undisturbed by that gate's addition.
        return {"universal_value": uv, "team_acquisition_value": tav,
                "positional_forfeit": forfeit, "rival_premium": premium,
                "rival_premium_take_probability": take_prob}

    def test_cliff_protection_at_the_standout_gap_boundary(self):
        below = self._cand(90, 95, forfeit=ps.NECESSITY_STANDOUT_REFERENCE_GAP - 0.1)
        at = self._cand(80, 85, forfeit=ps.NECESSITY_STANDOUT_REFERENCE_GAP)
        missing = self._cand(70, 75, forfeit=None)
        flags = ps.decision_path_flags([below, at, missing])
        self.assertFalse(flags[0]["cliff_protection"])
        self.assertTrue(flags[1]["cliff_protection"])
        self.assertFalse(flags[2]["cliff_protection"])

    def test_block_opportunity_at_the_two_dedicated_slots_premium_boundary(self):
        # 2x, not 1x, deliberately: one slot's worth of rival need fired for 73% of
        # candidates across the M13 backtest states (mid-draft, someone nearly always has a
        # single-slot need for any good player) -- an always-on flag carries no information.
        # Two slots' worth flags the genuinely gaping-hole rival, ~top-28% of cases.
        import draft_room as dr
        boundary = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        one_slot_routine_need = self._cand(90, 95, premium=dr.NEED_BONUS_PER_DEDICATED_SLOT)
        below = self._cand(85, 90, premium=boundary - 0.1)
        at = self._cand(80, 85, premium=boundary)
        flags = ps.decision_path_flags([one_slot_routine_need, below, at])
        self.assertFalse(flags[0]["block_opportunity"])
        self.assertFalse(flags[1]["block_opportunity"])
        self.assertTrue(flags[2]["block_opportunity"])

    def test_block_opportunity_requires_a_credible_rival_path_not_premium_magnitude_alone(self):
        # The REFINE production change: a premium big enough to clear the 2x-dedicated-slot
        # boundary is necessary but no longer sufficient -- the specific rival driving that
        # premium must ALSO have a credible real chance of taking the player
        # (take_probability >= CREDIBLE_RIVAL_PATH_THRESHOLD), per the denial-semantics audit
        # finding that ~1 in 5 premium-qualifying flags had no such rival path (both real
        # trial formats).
        import draft_room as dr
        boundary = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        no_path = self._cand(80, 85, premium=boundary + 5.0, take_prob=0.02)
        missing_take_prob = self._cand(80, 85, premium=boundary + 5.0, take_prob=None)
        at_threshold = self._cand(80, 85, premium=boundary + 5.0, take_prob=ps.CREDIBLE_RIVAL_PATH_THRESHOLD)
        just_below_threshold = self._cand(80, 85, premium=boundary + 5.0, take_prob=ps.CREDIBLE_RIVAL_PATH_THRESHOLD - 0.001)
        flags = ps.decision_path_flags([no_path, missing_take_prob, at_threshold, just_below_threshold])
        self.assertFalse(flags[0]["block_opportunity"], "high premium alone must not fire DENIAL without a credible rival path")
        self.assertFalse(flags[1]["block_opportunity"], "a missing take_probability must not default to credible")
        self.assertTrue(flags[2]["block_opportunity"], "the credible-path threshold itself is inclusive (>=)")
        self.assertFalse(flags[3]["block_opportunity"])

    def test_credible_gate_does_not_touch_rival_premiums_own_value(self):
        # The user's explicit constraint: the continuous rival_premium contribution (and the
        # necessity denial_component built from it) is untouched by this gate -- only the
        # human-facing block_opportunity boolean is filtered. decision_path_flags is read-only
        # over its input; the credible-path gate must not, and structurally cannot, mutate the
        # candidate's own rival_premium.
        import draft_room as dr
        boundary = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        credible = self._cand(80, 85, premium=boundary + 5.0, take_prob=1.0)
        not_credible = self._cand(80, 85, premium=boundary + 5.0, take_prob=0.0)
        ps.decision_path_flags([credible, not_credible])
        self.assertEqual(credible["rival_premium"], boundary + 5.0)
        self.assertEqual(not_credible["rival_premium"], boundary + 5.0)

        others = [70.0]
        necessity_credible = ps.compute_pick_necessity(
            [dict(credible, player_id="a", team_acquisition_value=85.0, need_bonus=0.0, eligibility_bonus=0.0,
                  survival_probability=0.5, positional_cliff=None, position_run_detected=False)], round_num=3,
        )
        necessity_not_credible = ps.compute_pick_necessity(
            [dict(not_credible, player_id="a", team_acquisition_value=85.0, need_bonus=0.0, eligibility_bonus=0.0,
                  survival_probability=0.5, positional_cliff=None, position_run_detected=False)], round_num=3,
        )
        self.assertEqual(necessity_credible, necessity_not_credible,
                          "pick_necessity's denial_component must be identical regardless of credible-path status -- "
                          "only rival_premium (unchanged here) feeds it, never rival_premium_take_probability")

    def test_pure_value_flags_the_buried_best_asset_only_beyond_the_noise_band(self):
        # Contextual leader (tav 100) holds uv 80; the uv-best candidate (uv 90) is ranked
        # below him -- flagged, because 90 - 80 = 10 > NEAR_TIE_BAND.
        leader = self._cand(80.0, 100.0)
        buried_best = self._cand(90.0, 92.0)
        flags = ps.decision_path_flags([leader, buried_best])
        self.assertFalse(flags[0]["pure_value"])
        self.assertTrue(flags[1]["pure_value"])

        # Same shape but the uv edge sits INSIDE the noise band -- no flag: a within-noise
        # uv lead is not a "materially better player."
        leader2 = self._cand(80.0, 100.0)
        barely_better = self._cand(80.0 + ps.NEAR_TIE_BAND, 92.0)
        flags2 = ps.decision_path_flags([leader2, barely_better])
        self.assertFalse(flags2[1]["pure_value"])

    def test_pure_value_never_flags_the_leader_himself(self):
        # When the tav leader IS the uv leader, there's no buried asset to surface.
        aligned_leader = self._cand(95.0, 100.0)
        second = self._cand(70.0, 90.0)
        flags = ps.decision_path_flags([aligned_leader, second])
        self.assertFalse(flags[0]["pure_value"])
        self.assertFalse(flags[1]["pure_value"])

    def test_empty_input(self):
        self.assertEqual(ps.decision_path_flags([]), [])

    def test_context_elevated_at_the_need_bonus_max_boundary(self):
        import draft_room as dr
        below = self._cand(70.0, 70.0 + dr.NEED_BONUS_MAX - 0.1)
        at = self._cand(70.0, 70.0 + dr.NEED_BONUS_MAX)
        flags = ps.decision_path_flags([below, at])
        self.assertFalse(flags[0]["context_elevated"])
        self.assertTrue(flags[1]["context_elevated"])

    def test_context_elevated_and_pure_value_are_independent_directions(self):
        # The two Context Gap directions are not mutually exclusive by construction (a
        # contrived case could technically satisfy both), but they answer different
        # questions and should each be computed on their own terms -- a candidate who is
        # both the field's best raw talent AND carries a huge roster-fit bonus gets both
        # flags rather than one silently overriding the other.
        import draft_room as dr
        leader = self._cand(80.0, 300.0)  # tav kept comfortably above "both"'s own
        both = self._cand(200.0, 200.0 + dr.NEED_BONUS_MAX)  # best uv AND huge fit bonus, still not the leader
        flags = ps.decision_path_flags([leader, both])
        self.assertTrue(flags[1]["pure_value"])
        self.assertTrue(flags[1]["context_elevated"])


class DecisionRegimeTests(unittest.TestCase):
    """decision_regime reads only margin-to-second and the leader's own survival -- these
    tests pin that it takes no round/pick input at all, and that BOTH bars (not either
    alone) are required for "decisive"."""

    def _cand(self, tav, survival=0.5):
        return {"team_acquisition_value": tav, "survival_probability": survival}

    def test_decisive_requires_both_a_real_margin_and_low_survival(self):
        leader = self._cand(100.0, survival=0.05)
        second = self._cand(100.0 - ps.NECESSITY_STANDOUT_REFERENCE_GAP, survival=0.5)
        self.assertEqual(ps.decision_regime([leader, second]), "decisive")

    def test_big_margin_alone_is_not_enough_if_survival_is_high(self):
        # A commanding lead that's still likely to survive isn't genuinely urgent --
        # there's no real risk of losing him, so conviction-first framing would overstate
        # the stakes even though the ranking gap is real.
        leader = self._cand(100.0, survival=0.6)
        second = self._cand(100.0 - ps.NECESSITY_STANDOUT_REFERENCE_GAP - 5, survival=0.5)
        self.assertEqual(ps.decision_regime([leader, second]), "contested")

    def test_low_survival_alone_is_not_enough_if_the_margin_is_thin(self):
        # Real risk of losing him, but he's barely ahead of the alternative -- that's a
        # genuine tiebreaker (near-tie territory), not a clear standout.
        leader = self._cand(100.0, survival=0.05)
        second = self._cand(99.0, survival=0.5)
        self.assertEqual(ps.decision_regime([leader, second]), "contested")

    def test_never_reads_round_or_pick_number(self):
        # No such parameter exists on the function at all -- calling it identically for a
        # "round 1" and "round 8" candidate set produces the identical verdict, proven by
        # there being no round/pick argument to vary in the first place.
        import inspect
        params = list(inspect.signature(ps.decision_regime).parameters)
        self.assertEqual(params, ["candidates"])

    def test_fewer_than_two_candidates_is_never_decisive(self):
        # No second place to measure a margin against -- "decisive" is a claim this
        # function can't support without a real comparison, so it isn't assumed by default.
        self.assertEqual(ps.decision_regime([]), "contested")
        self.assertEqual(ps.decision_regime([self._cand(100.0, survival=0.01)]), "contested")

    def test_missing_survival_on_the_leader_is_never_decisive(self):
        leader = self._cand(100.0, survival=None)
        second = self._cand(100.0 - ps.NECESSITY_STANDOUT_REFERENCE_GAP - 5)
        self.assertEqual(ps.decision_regime([leader, second]), "contested")

    def test_does_its_own_ranking_regardless_of_input_order(self):
        leader = self._cand(100.0, survival=0.05)
        second = self._cand(100.0 - ps.NECESSITY_STANDOUT_REFERENCE_GAP, survival=0.5)
        self.assertEqual(ps.decision_regime([second, leader]), "decisive")


class SnapshotIsCurrentTests(unittest.TestCase):
    """The input-state stamp: identity checks only, nothing recomputed, unstamped means
    not-certifiable (never silently current)."""

    class _FakeMerger:
        def __init__(self, freshest_date):
            self.freshest_date = freshest_date

    def _snapshot(self, picks_consumed, data_freshest_date):
        return ps.PickSnapshot(pick_label="3.07", round=3, my_roster_id="1", candidates=(),
                               picks_consumed=picks_consumed, data_freshest_date=data_freshest_date)

    def test_current_when_stamp_matches_live_state(self):
        snap = self._snapshot(24, "2026-08-18")
        ok, reason = ps.snapshot_is_current(snap, [{}] * 24, self._FakeMerger("2026-08-18"))
        self.assertTrue(ok)
        self.assertIsNone(reason)

    def test_stale_when_new_picks_landed(self):
        snap = self._snapshot(24, "2026-08-18")
        ok, reason = ps.snapshot_is_current(snap, [{}] * 27, self._FakeMerger("2026-08-18"))
        self.assertFalse(ok)
        self.assertIn("3 new pick(s)", reason)

    def test_stale_when_underlying_data_changed(self):
        snap = self._snapshot(24, "2026-08-18")
        ok, reason = ps.snapshot_is_current(snap, [{}] * 24, self._FakeMerger("2026-08-21"))
        self.assertFalse(ok)
        self.assertIn("data changed", reason)

    def test_unstamped_snapshot_is_not_certifiable(self):
        snap = self._snapshot(None, None)
        ok, reason = ps.snapshot_is_current(snap, [], self._FakeMerger(None))
        self.assertFalse(ok)
        self.assertIn("no input-state stamp", reason)


class BuildSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(40)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_snapshot_is_narrowed_and_ranked_by_team_acquisition_value(self):
        # At least top_n (can run longer -- narrow_candidates also guarantees the single best
        # remaining player at every position gets a look, even one that didn't crack the raw
        # top_n on value alone -- see narrow_candidates' own docstring for why).
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5,
        )
        self.assertGreaterEqual(len(snap.candidates), 5)
        values = [c.team_acquisition_value for c in snap.candidates]
        self.assertEqual(values, sorted(values, reverse=True), "candidates must be ranked by team_acquisition_value")

    def test_the_best_remaining_player_at_every_position_is_always_included(self):
        # The real fix this closes: a scarce position's best remaining player used to be
        # silently EXCLUDED from the whole survival/denial/necessity analysis whenever he
        # didn't crack the raw top_n by value alone -- not undervalued, literally invisible to
        # the strategic layer. A tiny top_n here (1) makes this unambiguous: the board's #1
        # overall player is RB/WR (this fixture's real baseline), so QB and TE would never
        # appear at all without the fix.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced",
        )
        best_qb_id = next(r["player_id"] for r in board if r["position"] == "QB")
        best_te_id = next(r["player_id"] for r in board if r["position"] == "TE")
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=1,
        )
        candidate_ids = {c.player_id for c in snap.candidates}
        self.assertIn(best_qb_id, candidate_ids)
        self.assertIn(best_te_id, candidate_ids)

    def test_a_deep_position_gets_real_replacement_depth_capped_at_the_display_ceiling(self):
        # End-to-end version of PositionViewDepthTests: LEAGUE has real WR demand (WR x3 +
        # FLEX, 12 teams) against a 40-deep real-baseline WR pool -- comfortably above
        # POSITION_VIEW_DEPTH_CAP, so this position's snapshot depth must land exactly at the
        # cap, not at the old single-best-only behavior and not uncapped either.
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=1,
        )
        wr_count = sum(1 for c in snap.candidates if c.position == "WR")
        self.assertEqual(wr_count, ps.POSITION_VIEW_DEPTH_CAP)

    def test_position_depth_shrinks_as_that_position_gets_drafted_out(self):
        # Draft progression: with 30 real WRs already off the board, LEAGUE's own remaining WR
        # demand drops below the display cap -- the snapshot's WR depth must follow it down,
        # not stay pinned at the cap.
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"][:30]
        picks = [{"player_id": pid, "roster_id": "2", "round": 1} for pid in wr_ids]
        snap = ps.build_snapshot(
            self.merger, self.players_db, picks, self.pick_order, current_index=len(picks), my_roster_id="1",
            league=LEAGUE, pick_label="3.01", top_n=1,
        )
        wr_count = sum(1 for c in snap.candidates if c.position == "WR")
        self.assertLess(wr_count, ps.POSITION_VIEW_DEPTH_CAP)

    def test_every_candidate_carries_the_full_real_decomposition(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3,
        )
        for c in snap.candidates:
            self.assertIsInstance(c.universal_value, float)
            self.assertIsInstance(c.team_acquisition_value, float)
            self.assertIsNotNone(c.survival_probability)
            self.assertIsNotNone(c.opportunity_cost)
            self.assertIsNotNone(c.expected_value_of_waiting)
            self.assertGreaterEqual(c.pick_necessity, 0.0)
            self.assertLessEqual(c.pick_necessity, 100.0)
            self.assertEqual(c.necessity_label, ps._necessity_label(c.pick_necessity))
            # team_acquisition_value must equal the documented sum -- the same invariant
            # test_draft_room.py enforces end-to-end, re-checked here since this module is
            # the one actually handing these numbers to the LLM debate layer.
            self.assertAlmostEqual(
                c.team_acquisition_value, c.universal_value + c.need_bonus + c.eligibility_bonus, places=2,
            )
            # projected_points is a real number here, never a fabricated one, since these are
            # all real Draft-Sharks-projected top players -- never a stray NaN leaking through
            # from the underlying pandas row (see build_snapshot's own NaN-normalization).
            self.assertIsNotNone(c.projected_points)
            self.assertGreater(c.projected_points, 0.0)

    def test_projected_points_matches_the_boards_own_raw_projection(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced",
        )
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3,
        )
        board_by_id = {r["player_id"]: r for r in board}
        for c in snap.candidates:
            self.assertAlmostEqual(c.projected_points, board_by_id[c.player_id]["projected_points"], places=2)

    def test_snapshot_is_genuinely_frozen(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=2,
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap.pick_label = "2.01"
        with self.assertRaises(dataclasses.FrozenInstanceError):
            snap.candidates[0].universal_value = 999.0

    def test_position_run_detected_matches_draft_strategys_own_signal(self):
        # Draft 3 of the last 4 picks at the same real position -- a genuine run by
        # draft_strategy.detect_positional_run's own definition, not a synthetic flag.
        rb_ids = [pid for pid, info in self.players_db.items() if info["position"] == "RB"][:3]
        wr_ids = [pid for pid, info in self.players_db.items() if info["position"] == "WR"][:1]
        picks = [{"roster_id": "2", "player_id": pid, "round": 1} for pid in (rb_ids[:2] + wr_ids + rb_ids[2:3])]
        run_position = ds.detect_positional_run(picks, self.players_db)
        self.assertEqual(run_position, "RB", "fixture didn't actually produce a real RB run -- test setup is wrong")

        snap = ps.build_snapshot(
            self.merger, self.players_db, picks, self.pick_order, current_index=len(picks), my_roster_id="1",
            league=LEAGUE, pick_label="1.05", top_n=8,
        )
        for c in snap.candidates:
            self.assertEqual(c.position_run_detected, c.position == "RB")

    def test_a_user_selected_player_outside_the_top_n_is_still_included(self):
        board_snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3,
        )
        top_ids = {c.player_id for c in board_snap.candidates}
        far_pick = next(pid for pid, info in self.players_db.items() if pid not in top_ids and info["position"] == "TE")
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=3, user_selected_player_id=far_pick,
        )
        self.assertIn(far_pick, {c.player_id for c in snap.candidates})
        self.assertEqual(snap.user_selected_player_id, far_pick)

    def test_upside_mode_snapshots_build_at_all(self):
        # Regression: upside-mode boards used to omit universal_value entirely (upside_score
        # returns only final_score/growth_signal/confidence), and build_snapshot read that
        # key unconditionally -- so ANY snapshot in upside mode raised KeyError. It went
        # unnoticed because every app.py call site takes build_snapshot's own "balanced"
        # default, and the one caller that passes mode="auto" (draft_simulation) only trips
        # it past UPSIDE_MODE_DEFAULT_ROUND, deeper than any test drove a simulation.
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5, mode="upside",
        )
        self.assertTrue(snap.candidates)

    def test_upside_mode_preserves_the_value_layer_identity(self):
        # team_acquisition_value == universal_value + need_bonus + eligibility_bonus is the
        # contract every consumer of a candidate reads. Upside mode has no separated need or
        # eligibility term at all, so the identity must hold with both at 0.0 -- which is
        # only true if universal_value falls back to the team-agnostic final_score, not to
        # some other number. This is what stops the KeyError fix from quietly turning into a
        # value fabrication.
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5, mode="upside",
        )
        for c in snap.candidates:
            self.assertEqual(c.need_bonus, 0.0, c.name)
            self.assertEqual(c.eligibility_bonus, 0.0, c.name)
            self.assertAlmostEqual(
                c.team_acquisition_value,
                c.universal_value + c.need_bonus + c.eligibility_bonus,
                places=6, msg=c.name,
            )

    def test_a_draft_deep_enough_to_flip_auto_mode_into_upside_completes(self):
        # The actual uncovered path: auto mode reads the current round off the PICKS ALREADY
        # MADE (compute_draft_board's own `current_round`), not off current_index, and flips
        # to upside scoring at UPSIDE_MODE_DEFAULT_ROUND. So reaching it needs a real draft
        # state that deep -- which no existing test had, since the only mode="auto" callers
        # are simulations and the rookie-draft validator never runs past round 4.
        #
        # 8 teams, not 12: this fixture's pool is 40 players x 4 positions, and 14 completed
        # rounds of 12 would drain it past what a round-15 board could still be built from.
        # The picks themselves are laid out in a fixed pool order rather than engine-chosen
        # -- what is under test is the board's SHAPE at depth, not the quality of the picks
        # that got there, and an engine-chosen 14-round trajectory costs minutes to build.
        teams = 8
        league = dict(LEAGUE, total_rosters=teams)
        # compute_draft_board derives the round as the MAX round among picks already made,
        # so the flip lands once a round-UPSIDE_MODE_DEFAULT_ROUND pick is on the board, not
        # when the next pick would open that round. This test takes that behavior as given
        # and drives past it -- it is not the place to relitigate the boundary.
        rounds_done = dr.UPSIDE_MODE_DEFAULT_ROUND
        drafted = list(self.players_db)[:teams * rounds_done]
        picks = [
            {"pick_no": i + 1, "round": i // teams + 1,
             "roster_id": str(i % teams + 1), "player_id": pid}
            for i, pid in enumerate(drafted)
        ]
        deep_order = ds.generate_pick_order(
            [str(i) for i in range(1, teams + 1)], total_rounds=dr.UPSIDE_MODE_DEFAULT_ROUND + 1,
        )
        snap = ps.build_snapshot(
            self.merger, self.players_db, picks, deep_order, current_index=len(picks),
            my_roster_id="1", league=league, pick_label=f"{dr.UPSIDE_MODE_DEFAULT_ROUND + 1}.01",
            top_n=3, mode="auto",
        )
        # Guard against the vacuous version of this test: nothing above forces upside
        # scoring, so if the round derivation ever stops flipping at this depth this test
        # would silently become a plain balanced-mode snapshot and prove nothing. Asserted on
        # the board's own mode field, NOT on the absence of universal_value -- that was the
        # original probe here and it broke the moment both modes started emitting the column,
        # which is exactly the coupling this whole fix removes.
        board = dr.compute_draft_board(
            self.merger, self.players_db, picks, my_roster_id="1", league=league, mode="auto",
        )
        self.assertEqual(board[0]["mode"], "upside", "board never entered upside mode")
        self.assertTrue(snap.candidates)


class UpsideSuperflexSurvivalTests(unittest.TestCase):
    """The SECOND crash on the same board-shape contract, found by scoping the first one
    rather than by a symptom. draft_strategy._pace_based_take_probability ranks a position's
    remaining players on an opponent's board by universal_value -- unguarded -- but only runs
    for superflex QB before the last documented pace anchor (48 picks). Upside mode normally
    arrives at round >= 15, long past that, so auto-mode drafts never reached it; forcing
    upside early in a superflex league does, and did raise KeyError."""

    @classmethod
    def setUpClass(cls):
        BuildSnapshotTests.setUpClass()
        cls.merger = BuildSnapshotTests.merger
        cls.players_db = BuildSnapshotTests.players_db

    def test_forced_upside_in_a_superflex_league_before_the_last_pace_anchor(self):
        superflex = dict(LEAGUE, roster_positions=[
            "QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "BN", "BN", "BN",
        ])
        order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)
        picks = [
            {"pick_no": i + 1, "round": 1, "roster_id": str(i + 1), "player_id": pid}
            for i, pid in enumerate(list(self.players_db)[:12])
        ]
        snap = ps.build_snapshot(
            self.merger, self.players_db, picks, order, current_index=12, my_roster_id="1",
            league=superflex, pick_label="2.01", top_n=5, mode="upside",
        )
        self.assertTrue(snap.candidates)


class BoardShapeContractTests(unittest.TestCase):
    """compute_draft_board returns two differently-shaped rows depending on mode, and for a
    long time nothing declared that. Five production sites indexed row["universal_value"]
    unguarded (draft_strategy x3, draft_counterfactual.bpa_row, pick_synthesis.build_snapshot)
    and roster_diagnostics passes the column NAME into replacement_levels -- so an absent
    column is a crash in every one of them, not a degraded reading. These tests pin the part
    of the shape that is shared, so a future third mode has to make the same promise."""

    @classmethod
    def setUpClass(cls):
        BuildSnapshotTests.setUpClass()
        cls.merger = BuildSnapshotTests.merger
        cls.players_db = BuildSnapshotTests.players_db

    def _board(self, mode):
        return dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode=mode,
        )

    def test_both_modes_carry_every_field_a_consumer_indexes_unguarded(self):
        required = {"player_id", "name", "position", "bpa", "universal_value", "final_score", "mode"}
        for mode in ("balanced", "upside"):
            board = self._board(mode)
            self.assertTrue(board, mode)
            for row in board[:25]:
                self.assertTrue(required <= set(row), f"{mode}: missing {required - set(row)}")

    def test_upside_universal_value_is_the_team_agnostic_score_itself(self):
        # Not an approximation and not a copy of the balanced number: upside_score reads
        # nothing off the roster, so its final_score IS the team-agnostic value.
        for row in self._board("upside")[:25]:
            self.assertEqual(row["universal_value"], row["final_score"], row["name"])

    def test_the_two_modes_are_not_claiming_to_be_the_same_valuation(self):
        # Guards the comment on the upside branch: universal_value fills the same ROLE in
        # both modes but is a different number, and must never be compared across them. If
        # this ever starts passing trivially (every player identical), the two modes have
        # collapsed into one and upside scoring has stopped doing anything.
        balanced = {r["player_id"]: r["universal_value"] for r in self._board("balanced")}
        upside = {r["player_id"]: r["universal_value"] for r in self._board("upside")}
        shared = set(balanced) & set(upside)
        self.assertTrue(shared)
        self.assertTrue(
            any(balanced[pid] != upside[pid] for pid in shared),
            "upside and balanced produced identical universal_value for every player",
        )

    def test_upside_boards_do_not_fabricate_a_decomposition_they_never_computed(self):
        # The deliberate other half of the fix: universal_value is emitted because consumers
        # need the role filled; time_horizon_adj/risk_adj are NOT, because upside_score never
        # computes them and a 0.0 would read as "measured, and it was zero."
        for row in self._board("upside")[:25]:
            self.assertNotIn("time_horizon_adj", row)
            self.assertNotIn("risk_adj", row)


class DiffSnapshotsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("RB", "WR"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(30)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_a_candidate_present_in_both_snapshots_reports_real_deltas(self):
        before = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=8,
        )
        # Draft away the current #1 candidate -- a real board-state change, not a synthetic one.
        top_id = before.candidates[0].player_id
        picks = [{"roster_id": "2", "player_id": top_id, "round": 1}]
        after = ps.build_snapshot(
            self.merger, self.players_db, picks, self.pick_order, current_index=1, my_roster_id="1",
            league=LEAGUE, pick_label="1.02", top_n=8,
        )
        diffs = ps.diff_snapshots(before, after)
        by_id = {d["player_id"]: d for d in diffs}
        # The drafted player no longer appears in the "after" snapshot's own candidate pool.
        self.assertIn(top_id, by_id)
        self.assertFalse(by_id[top_id]["entered"])
        # At least one remaining real candidate should show an actual, non-empty delta --
        # replacement level shifted for everyone at that position once a real pick landed.
        real_deltas = [d for d in diffs if d.get("entered") is None and d["deltas"]]
        self.assertTrue(real_deltas, "expected at least one candidate to show a real component delta after a pick")

    def test_identical_snapshots_produce_no_deltas(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5,
        )
        diffs = ps.diff_snapshots(snap, snap)
        for d in diffs:
            self.assertIsNone(d.get("entered"))
            self.assertEqual(d["rank_delta"], 0)
            self.assertEqual(d["deltas"], {})


class ConsensusLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_empty_when_not_superflex(self):
        # This app's committed baseline only carries KTC's superflex-format export -- using it
        # for a 1QB league would silently misrepresent that league's real market consensus.
        self.assertEqual(ps._consensus_lookup(self.merger, is_superflex=False), {})

    def test_real_data_present_for_superflex(self):
        lookup = ps._consensus_lookup(self.merger, is_superflex=True)
        self.assertGreater(len(lookup), 100, "expected KTC's real committed superflex export to be substantial")
        gibbs = lookup.get(("j", "gibbs"))
        self.assertIsNotNone(gibbs)
        self.assertEqual(gibbs["rank"], 1.0)
        self.assertEqual(gibbs["tier"], 1.0)

    def test_draft_pick_rows_are_excluded_not_just_ignored(self):
        # KTC's own export also lists draft picks ("2026 Early 1st" etc, position=NaN) --
        # these must never leak into a real-player lookup.
        lookup = ps._consensus_lookup(self.merger, is_superflex=True)
        self.assertNotIn(("2", "early 1st"), lookup)

    def test_a_name_key_collision_keeps_the_better_ranked_real_player(self):
        # A known, accepted limitation of the first-initial+last-name scheme -- Bijan Robinson
        # and Brian Robinson genuinely collide on (b, robinson). The far more prominent player
        # (much better rank) must be the one this lookup actually keeps.
        lookup = ps._consensus_lookup(self.merger, is_superflex=True)
        entry = lookup.get(("b", "robinson"))
        self.assertIsNotNone(entry)
        self.assertLess(entry["rank"], 50, "expected Bijan Robinson's much better rank to win the collision")


class ConsensusReachFreshnessBlindSpotTests(unittest.TestCase):
    """FLAGGED FINDING from the priority-7 information-freshness audit, not an asserted-correct
    invariant -- pins down a real gap so it doesn't get lost, exactly like the risk_adj
    calibration finding earlier in this same audit.

    DataMerger tracks staleness for exactly three sources (is_stale/staleness_days/
    freshest_date, and their free_agents_*/trade_values_* siblings) -- all three are Draft
    Sharks exports, and all three are cosmetic: confirmed by inspection that draft_room.py and
    pick_synthesis.py never read any of them for anything except pick_synthesis.py's own
    snapshot-identity check (build_snapshot/snapshot_is_current), which detects "did the data
    change since this snapshot was frozen," not "is this data too old to trust." Nothing in
    this app changes VALUATION behavior based on staleness, for any source.

    consensus_reach's reach_label/consensus_tier/consensus_rank are different in kind: they are
    real decision-support fields that reach CandidateSnapshot directly (every real "Debate My
    Pick" run sees them), sourced entirely from KeepTradeCut's external_values rows -- which
    have NO freshness tracking anywhere, not even the cosmetic kind Draft Sharks gets. The one
    freshness-aware code path that DOES touch external_values (composite_player_score's
    _recency_weight, a continuous per-row decay) is a completely separate call path that
    consensus_reach never touches. So a stale KTC export could silently feed a real per-pick
    "REACH"/"WITHIN CONSENSUS BAND" label with zero signal anywhere -- no is_stale flag, no UI
    pill, no debate-context mention -- that anything is out of date."""

    def test_data_merger_has_no_freshness_property_for_external_values(self):
        merger = dm.DataMerger()
        # The three real freshness properties this app has -- none of them are keyed to
        # external_values (KTC/FantasyPros/DynastyProcess/bot_research all live there).
        tracked_sources = (merger.projections, merger.free_agents, merger.trade_values)
        self.assertTrue(all(src is not merger.external_values for src in tracked_sources))
        self.assertFalse(hasattr(merger, "external_values_is_stale"))
        self.assertFalse(hasattr(merger, "external_values_staleness_days"))

    def test_consensus_reach_result_carries_no_date_or_freshness_field(self):
        by_key = {
            ("a", "player"): {"rank": 30, "tier": 3, "value": 5000},
            ("b", "here"): {"rank": 28, "tier": 3, "value": 5100},
        }
        result = ps.consensus_reach("A Player", 28, by_key)
        self.assertIsNotNone(result)
        self.assertNotIn("source_date", result)
        self.assertNotIn("is_stale", result)
        self.assertNotIn("staleness_days", result)


class ConsensusReachTests(unittest.TestCase):
    def test_none_when_no_consensus_data_is_loaded(self):
        self.assertIsNone(ps.consensus_reach("Anyone", 10, {}))

    def test_none_when_the_player_is_not_in_the_loaded_consensus_data(self):
        by_key = {("a", "known"): {"rank": 5, "tier": 1, "value": 9000}}
        self.assertIsNone(ps.consensus_reach("Unknown Player", 10, by_key))

    def test_within_consensus_band_when_tiers_match(self):
        by_key = {
            ("a", "player"): {"rank": 30, "tier": 3, "value": 5000},
            ("b", "here"): {"rank": 28, "tier": 3, "value": 5100},
        }
        result = ps.consensus_reach("A Player", 28, by_key)
        self.assertEqual(result["reach_label"], "WITHIN CONSENSUS BAND")
        self.assertEqual(result["tier_gap"], 0)

    def test_a_better_tier_than_normal_here_is_also_within_band_never_a_reach(self):
        # Taking a player from a BETTER tier than what's normally happening at this pick isn't
        # a reach at all -- great value, not a violation of consensus.
        by_key = {
            ("a", "elite"): {"rank": 5, "tier": 1, "value": 9500},
            ("b", "here"): {"rank": 28, "tier": 3, "value": 5100},
        }
        result = ps.consensus_reach("A Elite", 28, by_key)
        self.assertEqual(result["tier_gap"], 0)
        self.assertEqual(result["reach_label"], "WITHIN CONSENSUS BAND")

    def test_one_tier_worse_than_normal_here_is_a_modest_reach(self):
        by_key = {
            ("a", "player"): {"rank": 60, "tier": 4, "value": 3000},
            ("b", "here"): {"rank": 28, "tier": 3, "value": 5100},
        }
        result = ps.consensus_reach("A Player", 28, by_key)
        self.assertEqual(result["tier_gap"], 1)
        self.assertEqual(result["reach_label"], "MODEST REACH")

    def test_a_big_tier_gap_is_a_significant_reach(self):
        by_key = {
            ("a", "player"): {"rank": 200, "tier": 9, "value": 500},
            ("b", "here"): {"rank": 28, "tier": 3, "value": 5100},
        }
        result = ps.consensus_reach("A Player", 28, by_key)
        self.assertEqual(result["tier_gap"], 6)
        self.assertEqual(result["reach_label"], "SIGNIFICANT REACH")


class ConsensusReachEndToEndTests(unittest.TestCase):
    """Real KTC data, real board -- confirms the wiring, not just the isolated functions."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(60)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_a_1qb_league_never_gets_consensus_data(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, pick_label="1.01", top_n=5,
        )
        for c in snap.candidates:
            self.assertIsNone(c.consensus_rank)
            self.assertIsNone(c.reach_label)

    def test_a_superflex_league_gets_real_consensus_data_for_a_known_player(self):
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=SUPERFLEX_LEAGUE, pick_label="1.01", top_n=5,
        )
        gibbs = next((c for c in snap.candidates if "Gibbs" in c.name), None)
        self.assertIsNotNone(gibbs, "expected Gibbs to be a top-5 candidate at 1.01")
        self.assertEqual(gibbs.consensus_rank, 1)
        self.assertEqual(gibbs.consensus_tier, 1)
        self.assertIn(gibbs.reach_label, ("WITHIN CONSENSUS BAND",))


if __name__ == "__main__":
    unittest.main()
