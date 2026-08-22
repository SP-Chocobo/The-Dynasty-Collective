"""
Covers lineup_optimizer.py's real correctness bar: the assignment must be the actual optimum,
not a greedy approximation that happens to work on easy cases. Includes a constructed case
where a naive greedy assignment (fill each slot with its single best available player, in
descending value order) provably gets the WRONG total -- the exact trap multi-position
eligibility creates and the reason this module uses scipy's exact solver instead.
"""

import unittest

import lineup_optimizer as lo


def _slot(label, eligible):
    return {"slot_id": label, "eligible": set(eligible)}


def _player(pid, value, eligible):
    return {"id": pid, "value": value, "eligible": set(eligible)}


class OptimizeLineupTests(unittest.TestCase):
    def test_single_eligible_position_is_a_trivial_assignment(self):
        players = [_player("qb1", 90, {"QB"}), _player("qb2", 40, {"QB"})]
        slots = [_slot("QB_0", {"QB"})]
        result = lo.optimize_lineup(players, slots)
        self.assertEqual(result["total_value"], 90)
        self.assertEqual(result["assignments"][0]["player_id"], "qb1")
        self.assertEqual(result["benched"], ["qb2"])

    def test_ineligible_player_is_never_forced_into_a_slot(self):
        players = [_player("qb1", 90, {"QB"})]
        slots = [_slot("RB_0", {"RB"})]
        result = lo.optimize_lineup(players, slots)
        self.assertEqual(result["total_value"], 0)
        self.assertEqual(result["assignments"], [])
        self.assertEqual(result["benched"], ["qb1"])

    def test_greedy_by_value_would_get_this_wrong_but_the_optimizer_does_not(self):
        # Constructed so naive greedy (fill each slot with its single best-value eligible
        # player, in descending value order, no look-ahead) provably picks a WORSE total than
        # the true optimum. Player A (value 100) is eligible for both slots (RB/WR). Player B
        # (value 95) is WR-only. Player C (value 90) is RB-only. There's one WR slot and one
        # RB slot -- no flex, so this isn't a tie: greedy processes players by value
        # descending, assigns A to whichever slot it's considered for first (say WR, since
        # it's eligible there and A is the best overall), then B can't take WR (taken) and C
        # takes RB, leaving B benched -- total 100 + 90 = 190. The true optimum is A->RB,
        # B->WR (C benched) = 100 + 95 = 195, strictly better. Unlike the A/B-only case this
        # replaced, there is exactly ONE optimal assignment here, so asserting the specific
        # by-slot pairing is safe regardless of the solver's internal tie-breaking.
        players = [
            _player("A_both", 100, {"RB", "WR"}),
            _player("B_wr_only", 95, {"WR"}),
            _player("C_rb_only", 90, {"RB"}),
        ]
        slots = [_slot("WR_0", {"WR"}), _slot("RB_0", {"RB"})]
        result = lo.optimize_lineup(players, slots)
        self.assertEqual(result["total_value"], 195)
        by_slot = {a["slot_id"]: a["player_id"] for a in result["assignments"]}
        self.assertEqual(by_slot["WR_0"], "B_wr_only")
        self.assertEqual(by_slot["RB_0"], "A_both")
        self.assertEqual(result["benched"], ["C_rb_only"])

    def test_multi_eligible_player_can_unlock_a_higher_total_than_either_single_slot_alone(self):
        # The actual Travis-Hunter-shaped case: one WR/DB-eligible player, a full WR room,
        # and one open IDP_FLEX slot. His flexibility should let the optimizer use him at
        # IDP_FLEX (his only real opening) while a stronger WR takes the WR slot -- something
        # a single-position-bucketed player could never do.
        players = [
            _player("hunter", 70, {"WR", "DB"}),
            _player("elite_wr", 95, {"WR"}),
            _player("replacement_db", 20, {"DB"}),
        ]
        slots = [_slot("WR_0", {"WR"}), _slot("IDP_FLEX_0", {"DL", "LB", "DB"})]
        result = lo.optimize_lineup(players, slots)
        by_slot = {a["slot_id"]: a["player_id"] for a in result["assignments"]}
        self.assertEqual(by_slot["WR_0"], "elite_wr")
        self.assertEqual(by_slot["IDP_FLEX_0"], "hunter")
        self.assertEqual(result["total_value"], 95 + 70)

    def test_empty_players_or_slots_is_a_safe_no_op(self):
        self.assertEqual(lo.optimize_lineup([], [_slot("QB_0", {"QB"})])["total_value"], 0.0)
        self.assertEqual(lo.optimize_lineup([_player("a", 10, {"QB"})], [])["benched"], ["a"])


class MarginalLineupValueTests(unittest.TestCase):
    def test_marginal_value_is_the_lineup_delta(self):
        roster = [_player("qb1", 80, {"QB"})]
        candidate = _player("qb2", 95, {"QB"})
        result = lo.marginal_lineup_value(roster, candidate, roster_positions=["QB", "BN"])
        # Best lineup was 80 (qb1 starts); adding a better QB flips who starts, net +15.
        self.assertEqual(result["without_candidate"], 80)
        self.assertEqual(result["with_candidate"], 95)
        self.assertEqual(result["marginal_value"], 15)

    def test_a_bench_quality_candidate_adds_zero_marginal_value(self):
        roster = [_player("qb1", 80, {"QB"})]
        candidate = _player("qb2", 20, {"QB"})  # worse than the current starter, one slot only
        result = lo.marginal_lineup_value(roster, candidate, roster_positions=["QB", "BN"])
        self.assertEqual(result["marginal_value"], 0)


class EligibilityBonusTests(unittest.TestCase):
    def test_single_position_player_gets_exactly_zero_bonus(self):
        # Both calls (full eligibility vs. primary-only) solve an IDENTICAL problem for a
        # single-position player -- the bonus must be exactly 0, never a rounding artifact.
        roster = [_player("wr1", 90, {"WR"})]
        result = lo.eligibility_bonus(
            roster, candidate_id="wr2", candidate_value=85, candidate_full_eligible={"WR"},
            candidate_primary_position="WR", roster_positions=["WR", "WR", "FLEX", "BN"],
        )
        self.assertEqual(result["eligibility_bonus"], 0.0)

    def test_multi_eligible_player_gets_a_real_positive_bonus_when_it_unlocks_a_scarce_slot(self):
        # A full WR room (no WR/FLEX opening) but an empty IDP_FLEX slot -- a WR/DB-eligible
        # player can fill that IDP_FLEX opening; a WR-only player of identical value could not.
        roster = [
            _player("wr_a", 90, {"WR"}), _player("wr_b", 85, {"WR"}), _player("wr_c", 80, {"WR"}),
        ]
        roster_positions = ["WR", "WR", "FLEX", "IDP_FLEX", "BN"]
        result = lo.eligibility_bonus(
            roster, candidate_id="hunter", candidate_value=70,
            candidate_full_eligible={"WR", "DB"}, candidate_primary_position="WR",
            roster_positions=roster_positions,
        )
        self.assertGreater(result["eligibility_bonus"], 0.0)
        self.assertEqual(result["marginal_value_primary_position_only"], 0.0, "WR-only, he shouldn't crack an already-full WR/FLEX room")
        self.assertEqual(result["marginal_value_full_eligibility"], 70.0, "DB eligibility should let him fill the open IDP_FLEX slot")

    def test_fast_path_for_single_position_players_still_reports_a_real_marginal_value(self):
        # candidate_full_eligible == {primary position} takes the short-circuit branch inside
        # eligibility_bonus (skips solving the assignment problem twice for an already-known
        # zero bonus) -- this must still report the real marginal value, not a stubbed 0.
        roster = [_player("qb1", 80, {"QB"})]
        result = lo.eligibility_bonus(
            roster, candidate_id="qb2", candidate_value=95, candidate_full_eligible={"QB"},
            candidate_primary_position="QB", roster_positions=["QB", "BN"],
        )
        self.assertEqual(result["eligibility_bonus"], 0.0)
        self.assertEqual(result["marginal_value_full_eligibility"], 15.0)
        self.assertEqual(result["marginal_value_primary_position_only"], 15.0)

    def test_bonus_is_zero_when_the_flexible_slot_is_already_taken(self):
        # Same player, but the IDP_FLEX slot is already filled by someone else on the roster
        # -- his DB eligibility shouldn't manufacture value that isn't actually there.
        roster = [
            _player("wr_a", 90, {"WR"}), _player("wr_b", 85, {"WR"}), _player("wr_c", 80, {"WR"}),
            _player("db_starter", 60, {"DB"}),
        ]
        roster_positions = ["WR", "WR", "FLEX", "IDP_FLEX", "BN"]
        result = lo.eligibility_bonus(
            roster, candidate_id="hunter", candidate_value=50,
            candidate_full_eligible={"WR", "DB"}, candidate_primary_position="WR",
            roster_positions=roster_positions,
        )
        self.assertEqual(result["eligibility_bonus"], 0.0)


if __name__ == "__main__":
    unittest.main()
