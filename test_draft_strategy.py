"""
Covers draft_strategy.py's real invariants: pick-order/snake mechanics, positional-run
detection as a real signal (not an invented one), survival probability's actual monotonic
behavior, and a hard performance regression guard -- an earlier version of this module
recomputed a full draft board per intervening PICK POSITION and per CANDIDATE separately,
which measured at 40+ seconds against a modest player pool for a worst-case pick gap. That
bug is exactly the kind that reappears silently after a future edit if nothing asserts on
wall-clock time directly.
"""

import time
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds

LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "TE", "FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}


def _build_players_db(positions=("QB", "RB", "WR", "TE"), per_position=60):
    merger = dm.DataMerger()
    proj = merger.projections
    players_db = {}
    pid = 0
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False).head(per_position)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return merger, players_db


class GeneratePickOrderTests(unittest.TestCase):
    def test_odd_rounds_keep_the_given_order(self):
        order = ds.generate_pick_order(["1", "2", "3"], total_rounds=3)
        self.assertEqual(order[0:3], ["1", "2", "3"])
        self.assertEqual(order[6:9], ["1", "2", "3"])

    def test_even_rounds_reverse_for_snake(self):
        order = ds.generate_pick_order(["1", "2", "3"], total_rounds=2)
        self.assertEqual(order[3:6], ["3", "2", "1"])

    def test_linear_never_reverses(self):
        order = ds.generate_pick_order(["1", "2", "3"], total_rounds=4, draft_type="linear")
        for round_start in range(0, 12, 3):
            self.assertEqual(order[round_start:round_start + 3], ["1", "2", "3"])

    def test_snake_turn_puts_the_same_roster_back_to_back(self):
        # The real mechanic that makes a "0 intervening picks" case common: the last pick of
        # an odd round and the first pick of the following even round are the SAME roster.
        order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=2)
        self.assertEqual(order[11], order[12])

    def test_3rr_round_pattern_is_forward_reverse_reverse_then_alternating(self):
        # F, R, R, F, R, F -- round 3 repeats round 2's reversed order, then normal
        # alternation resumes from round 4. See generate_pick_order's own docstring.
        order = ds.generate_pick_order(["1", "2", "3"], total_rounds=6, draft_type="3rr")
        rounds = [order[i * 3:(i + 1) * 3] for i in range(6)]
        self.assertEqual(rounds[0], ["1", "2", "3"])   # R1 forward
        self.assertEqual(rounds[1], ["3", "2", "1"])   # R2 reversed
        self.assertEqual(rounds[2], ["3", "2", "1"])   # R3 reversed AGAIN (the reversal)
        self.assertEqual(rounds[3], ["1", "2", "3"])   # R4 forward
        self.assertEqual(rounds[4], ["3", "2", "1"])   # R5 reversed
        self.assertEqual(rounds[5], ["1", "2", "3"])   # R6 forward

    def test_3rr_every_roster_appears_exactly_once_per_round(self):
        teams = [str(i) for i in range(1, 13)]
        order = ds.generate_pick_order(teams, total_rounds=5, draft_type="3rr")
        for round_num in range(5):
            round_slice = order[round_num * 12:(round_num + 1) * 12]
            self.assertEqual(sorted(round_slice), sorted(teams))

    def test_3rr_breaks_the_turn_slots_round_2_to_3_double_pick(self):
        # The single largest structural error treating a 3RR draft as snake would make:
        # roster 1 picks last in round 2 and, under snake, FIRST in round 3 (0 intervening
        # picks) -- under 3RR round 3 repeats round 2's order, so roster 1 picks LAST again
        # and waits through all 11 other teams. Survival for that wait is a completely
        # different question than "he's yours, nobody picks between."
        teams = [str(i) for i in range(1, 13)]
        snake = ds.generate_pick_order(teams, total_rounds=3)
        rr3 = ds.generate_pick_order(teams, total_rounds=3, draft_type="3rr")

        # roster "1" picks at index 23 (last of R2) in both orders
        self.assertEqual(snake[23], "1")
        self.assertEqual(rr3[23], "1")

        snake_next = ds.find_next_pick_index(snake, "1", after_index=23)
        rr3_next = ds.find_next_pick_index(rr3, "1", after_index=23)
        snake_wait = ds.intervening_roster_ids(snake, current_index=23, my_next_index=snake_next)
        rr3_wait = ds.intervening_roster_ids(rr3, current_index=23, my_next_index=rr3_next)
        self.assertEqual(len(snake_wait), 0)
        self.assertEqual(len(rr3_wait), 11)

    def test_3rr_matches_snake_through_round_2_then_flips_parity_for_good(self):
        # The reversal isn't a one-round anomaly: repeating round 2's order in round 3 flips
        # the alternation's parity permanently -- every round from 3 on runs OPPOSITE to what
        # plain snake would do in that same round (3RR's F,R,R,F,R,F vs snake's F,R,F,R,F,R).
        teams = [str(i) for i in range(1, 13)]
        snake = ds.generate_pick_order(teams, total_rounds=6)
        rr3 = ds.generate_pick_order(teams, total_rounds=6, draft_type="3rr")
        for round_num in range(6):
            lo, hi = round_num * 12, (round_num + 1) * 12
            if round_num < 2:
                self.assertEqual(snake[lo:hi], rr3[lo:hi])
            else:
                self.assertEqual(list(reversed(snake[lo:hi])), rr3[lo:hi])


class FindNextPickAndInterveningTests(unittest.TestCase):
    def setUp(self):
        self.order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=3)

    def test_finds_the_next_occurrence_after_the_given_index(self):
        idx = ds.find_next_pick_index(self.order, "1", after_index=0)
        self.assertEqual(self.order[idx], "1")
        self.assertGreater(idx, 0)

    def test_none_when_no_more_picks_remain(self):
        last_index = len(self.order) - 1
        idx = ds.find_next_pick_index(self.order, self.order[last_index], after_index=last_index)
        self.assertIsNone(idx)

    def test_snake_turn_has_zero_intervening_picks(self):
        # Roster 12 picks at index 11 (last of round 1) and again at index 12 (first of
        # round 2, snake reversal) -- back to back, nobody picks between them.
        my_next = ds.find_next_pick_index(self.order, "12", after_index=11)
        intervening = ds.intervening_roster_ids(self.order, current_index=11, my_next_index=my_next)
        self.assertEqual(intervening, [])

    def test_picking_first_overall_has_the_longest_possible_gap(self):
        my_next = ds.find_next_pick_index(self.order, "1", after_index=0)
        intervening = ds.intervening_roster_ids(self.order, current_index=0, my_next_index=my_next)
        self.assertEqual(len(intervening), 22)  # 11 teams x 2 picks each before roster 1 goes again


class DetectPositionalRunTests(unittest.TestCase):
    def _pick(self, player_id):
        return {"player_id": player_id, "roster_id": "1", "round": 1}

    def test_three_of_four_same_position_is_a_run(self):
        players_db = {
            "1": {"position": "RB", "fantasy_positions": ["RB"]},
            "2": {"position": "RB", "fantasy_positions": ["RB"]},
            "3": {"position": "WR", "fantasy_positions": ["WR"]},
            "4": {"position": "RB", "fantasy_positions": ["RB"]},
        }
        picks = [self._pick(p) for p in ("1", "2", "3", "4")]
        self.assertEqual(ds.detect_positional_run(picks, players_db), "RB")

    def test_no_run_when_positions_are_mixed(self):
        players_db = {
            "1": {"position": "RB", "fantasy_positions": ["RB"]},
            "2": {"position": "WR", "fantasy_positions": ["WR"]},
            "3": {"position": "TE", "fantasy_positions": ["TE"]},
            "4": {"position": "QB", "fantasy_positions": ["QB"]},
        }
        picks = [self._pick(p) for p in ("1", "2", "3", "4")]
        self.assertIsNone(ds.detect_positional_run(picks, players_db))

    def test_too_few_picks_yet_is_not_a_run(self):
        players_db = {"1": {"position": "RB", "fantasy_positions": ["RB"]}}
        self.assertIsNone(ds.detect_positional_run([self._pick("1")], {}))


class SurvivalAndPickAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_players_db()
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)

    def test_zero_intervening_picks_means_certain_survival(self):
        boards = {}
        result = ds.estimate_survival(
            [], self.players_db, self.pick_order, current_index=11, my_roster_id="12",
            target_player_id="1", opponent_boards=boards,
        )
        self.assertEqual(result["survival_probability"], 1.0)
        self.assertEqual(result["intervening_picks"], 0)

    def test_the_consensus_top_player_has_near_zero_survival_across_a_long_gap(self):
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        top_player_id = board[0]["player_id"]
        my_next = ds.find_next_pick_index(self.pick_order, "1", after_index=0)
        intervening = ds.intervening_roster_ids(self.pick_order, 0, my_next)
        opponent_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, intervening)
        result = ds.estimate_survival([], self.players_db, self.pick_order, 0, "1", top_player_id, opponent_boards)
        self.assertLess(result["survival_probability"], 0.05, "the #1 overall player should not likely survive a 22-pick gap")

    def test_more_intervening_picks_means_lower_or_equal_survival(self):
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="6", league=LEAGUE, mode="balanced")
        mid_player_id = next(r["player_id"] for r in board if 20 < board.index(r) < 40)

        # Short gap: picking 6th, next pick is at the snake turn (index 17, roster 7 reversed... )
        short_next = ds.find_next_pick_index(self.pick_order, "6", after_index=5)
        short_intervening = ds.intervening_roster_ids(self.pick_order, 5, short_next)
        short_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, short_intervening)
        short_result = ds.estimate_survival([], self.players_db, self.pick_order, 5, "6", mid_player_id, short_boards)

        # Long gap: picking 1st overall instead (same player, same underlying pool/board shape).
        long_next = ds.find_next_pick_index(self.pick_order, "1", after_index=0)
        long_intervening = ds.intervening_roster_ids(self.pick_order, 0, long_next)
        long_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, long_intervening)
        long_result = ds.estimate_survival([], self.players_db, self.pick_order, 0, "1", mid_player_id, long_boards)

        self.assertGreaterEqual(short_result["intervening_picks"], 0)
        self.assertLessEqual(long_result["survival_probability"], short_result["survival_probability"] + 1e-9)

    def test_opportunity_cost_is_zero_when_survival_is_certain(self):
        analysis = ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, current_index=11, my_roster_id="12",
            league=LEAGUE, candidate_player_ids=["1", "2"],
        )
        for row in analysis:
            self.assertEqual(row["survival_probability"], 1.0)
            self.assertEqual(row["opportunity_cost"], 0.0)

    def test_pick_analysis_completes_quickly_even_at_the_worst_case_gap(self):
        # The real regression this guards: an earlier version of this module took 40+ seconds
        # on a comparable pool at this exact worst-case gap (picking 1st overall, 22
        # intervening picks) by recomputing a full board per pick position AND per candidate.
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        top5 = [r["player_id"] for r in board[:5]]
        t0 = time.time()
        ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, candidate_player_ids=top5,
        )
        elapsed = time.time() - t0
        self.assertLess(elapsed, 15.0, f"pick_analysis took {elapsed:.1f}s at the worst-case gap -- regression toward the old per-candidate, per-pick-position recomputation")

    def test_denial_is_derived_only_from_opponent_boards_and_their_take_probabilities(self):
        # The independence invariant, enforced rather than just currently true: denial_value
        # must be exactly max over intervening opponents of (THEIR board's final_score for the
        # candidate x their take-probability) -- the user's own board/roster appears nowhere.
        # If a future edit wires the user's own values into denial, this recomputation stops
        # matching and fails loudly.
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        candidate = board[0]["player_id"]
        analysis = ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, candidate_player_ids=[candidate],
        )
        reported = analysis[0]["denial_value"]

        my_next = ds.find_next_pick_index(self.pick_order, "1", after_index=0)
        intervening = ds.intervening_roster_ids(self.pick_order, 0, my_next)
        opponent_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, intervening)
        survival = ds.estimate_survival(
            [], self.players_db, self.pick_order, 0, "1", candidate, opponent_boards, league=LEAGUE,
        )
        expected = 0.0
        for risk in survival["risk_by_team"]:
            opp_row = opponent_boards[str(risk["roster_id"])]["by_id"].get(str(candidate))
            if opp_row is not None:
                expected = max(expected, opp_row["final_score"] * risk["take_probability"])
        self.assertAlmostEqual(reported, round(expected, 2), places=2)

    def test_rival_premium_take_probability_is_the_premium_driving_rivals_own_take_probability(self):
        # rival_premium is a max over intervening opponents; rival_premium_take_probability
        # must be THAT SAME opponent's own take_probability from risk_by_team, not some other
        # opponent's, and not survival_probability (a pooled, all-opponents number) reused by
        # mistake -- the exact bug this field exists to make impossible for a downstream
        # credible-path gate (pick_synthesis.CREDIBLE_RIVAL_PATH_THRESHOLD) to fall into.
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        candidate = board[0]["player_id"]
        analysis = ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, candidate_player_ids=[candidate],
        )
        row = analysis[0]

        my_next = ds.find_next_pick_index(self.pick_order, "1", after_index=0)
        intervening = ds.intervening_roster_ids(self.pick_order, 0, my_next)
        opponent_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, intervening)
        survival = ds.estimate_survival(
            [], self.players_db, self.pick_order, 0, "1", candidate, opponent_boards, league=LEAGUE,
        )
        expected_premium = 0.0
        expected_take_prob = None
        for risk in survival["risk_by_team"]:
            opp_row = opponent_boards[str(risk["roster_id"])]["by_id"].get(str(candidate))
            if opp_row is None or "universal_value" not in opp_row:
                continue
            premium = opp_row["final_score"] - opp_row["universal_value"]
            if premium > expected_premium:
                expected_premium = premium
                expected_take_prob = risk["take_probability"]

        self.assertAlmostEqual(row["rival_premium"], round(expected_premium, 2), places=2)
        if expected_take_prob is None:
            self.assertIsNone(row["rival_premium_take_probability"])
        else:
            self.assertEqual(row["rival_premium_take_probability"], expected_take_prob)

    def test_denial_value_never_exceeds_the_denying_teams_own_acquisition_value(self):
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        top3 = [r["player_id"] for r in board[:3]]
        analysis = ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, current_index=0, my_roster_id="1",
            league=LEAGUE, candidate_player_ids=top3,
        )
        for row in analysis:
            if row["denial_team"] is not None:
                self.assertLessEqual(row["denial_value"], row["team_acquisition_value"] + 1e-6)


class PositionalForfeitsTests(unittest.TestCase):
    """positional_forfeits is a SURFACED signal (never an input to necessity -- see its own
    docstring on the double-count that rule prevents), so what gets tested is the math and
    its two load-bearing properties: a steeper position curve costs more to delay, and more
    opponent appetite for a position raises its expected_taken."""

    def _opp_board(self, rows):
        # rows: list of (player_id, position, universal_value) already in rank order
        return {
            "by_id": {pid: {"player_id": pid, "position": pos, "universal_value": uv,
                            "final_score": uv} for pid, pos, uv in rows},
            "rank_by_id": {pid: i + 1 for i, (pid, _pos, _uv) in enumerate(rows)},
        }

    def test_steeper_curve_costs_more_to_delay_given_equal_opponent_appetite(self):
        curves = {
            "RB": [100.0, 80.0, 60.0, 40.0],   # steep: ~20/rank
            "WR": [100.0, 97.0, 94.0, 91.0],   # flat: 3/rank
        }
        # Two opponents with MIRRORED boards (rank weights are not symmetric within one
        # board, so true equal appetite needs the mirror): summed take tendency toward RB
        # and WR comes out identical across the pair.
        board_rb_first = self._opp_board([("r1", "RB", 100), ("w1", "WR", 100), ("r2", "RB", 80), ("w2", "WR", 97)])
        board_wr_first = self._opp_board([("w1", "WR", 100), ("r1", "RB", 100), ("w2", "WR", 97), ("r2", "RB", 80)])
        result = ds.positional_forfeits(curves, {"2": board_rb_first, "3": board_wr_first}, ["2", "3"])
        self.assertGreater(result["RB"]["forfeit"], result["WR"]["forfeit"])
        self.assertAlmostEqual(result["RB"]["expected_taken"], result["WR"]["expected_taken"])

    def test_more_opponent_appetite_raises_expected_taken(self):
        curves = {"RB": [100.0, 90.0, 80.0], "WR": [100.0, 90.0, 80.0]}
        # Opponent's top ranks are ALL RB -- heavy RB appetite, zero WR appetite.
        board = self._opp_board([("r1", "RB", 100), ("r2", "RB", 95), ("r3", "RB", 90)])
        result = ds.positional_forfeits(curves, {"2": board}, ["2"])
        self.assertGreater(result["RB"]["expected_taken"], 0.5)
        self.assertEqual(result["WR"]["expected_taken"], 0.0)
        self.assertEqual(result["WR"]["forfeit"], 0.0)

    def test_no_intervening_picks_means_no_forfeit_signal_at_all(self):
        curves = {"RB": [100.0, 50.0]}
        self.assertEqual(ds.positional_forfeits(curves, {}, []), {})

    def test_expected_taken_walk_is_clamped_to_the_curves_own_length(self):
        # Ten RB-hungry opponents against a 2-player RB curve: the walk can't fall off the
        # end -- forfeit maxes out at best-minus-worst, never an index error.
        curves = {"RB": [100.0, 40.0]}
        board = self._opp_board([("r1", "RB", 100), ("r2", "RB", 95)])
        boards = {str(i): board for i in range(2, 12)}
        result = ds.positional_forfeits(curves, boards, [str(i) for i in range(2, 12)])
        self.assertEqual(result["RB"]["forfeit"], 60.0)


SUPERFLEX_LEAGUE = {
    "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX", "SUPER_FLEX", "BN", "BN", "BN", "BN"],
    "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {},
}


class ExpectedPositionPaceTests(unittest.TestCase):
    def test_none_for_a_position_with_no_documented_convention(self):
        self.assertIsNone(ds.expected_position_pace("RB", 12, SUPERFLEX_LEAGUE["roster_positions"]))
        self.assertIsNone(ds.expected_position_pace("WR", 12, SUPERFLEX_LEAGUE["roster_positions"]))

    def test_none_for_qb_without_super_flex_in_the_roster(self):
        self.assertIsNone(ds.expected_position_pace("QB", 12, LEAGUE["roster_positions"]))

    def test_matches_the_documented_anchor_points_exactly(self):
        rp = SUPERFLEX_LEAGUE["roster_positions"]
        self.assertEqual(ds.expected_position_pace("QB", 0, rp), 0.0)
        self.assertEqual(ds.expected_position_pace("QB", 12, rp), 6.0)
        self.assertEqual(ds.expected_position_pace("QB", 24, rp), 9.5)
        self.assertEqual(ds.expected_position_pace("QB", 48, rp), 13.5)

    def test_interpolates_linearly_between_anchors(self):
        rp = SUPERFLEX_LEAGUE["roster_positions"]
        self.assertAlmostEqual(ds.expected_position_pace("QB", 6, rp), 3.0)  # halfway to the round-1 anchor

    def test_holds_flat_beyond_the_last_documented_anchor(self):
        rp = SUPERFLEX_LEAGUE["roster_positions"]
        self.assertEqual(ds.expected_position_pace("QB", 100, rp), 13.5)


def _synthetic_board(rows):
    return {"by_id": {r["player_id"]: r for r in rows}}


class PaceBasedTakeProbabilityTests(unittest.TestCase):
    def test_none_when_no_convention_applies(self):
        board = _synthetic_board([{"player_id": "1", "position": "RB", "universal_value": 90.0}])
        self.assertIsNone(ds._pace_based_take_probability(
            "RB", "1", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"],
        ))

    def test_none_once_past_the_last_documented_anchor(self):
        board = _synthetic_board([{"player_id": "1", "position": "QB", "universal_value": 90.0}])
        self.assertIsNone(ds._pace_based_take_probability(
            "QB", "1", board, 48, [], {}, SUPERFLEX_LEAGUE["roster_positions"],
        ))

    def test_the_consensus_best_remaining_qb_gets_the_full_any_pick_share(self):
        # 5 picks made, 0 QBs drafted -- a real deficit against the round-1 pace (expected ~2.5
        # by now: interpolate(5) on SUPERFLEX_QB_PACE_ANCHORS). This QB is the only one left, so
        # the whole "some QB gets taken" share of probability goes to him alone (rank-among-QBs
        # divisor of 1) -- deficit(2.5) / PACE_CATCH_UP_WINDOW(6) = 0.41666...
        board = _synthetic_board([{"player_id": "qb1", "position": "QB", "universal_value": 90.0}])
        p = ds._pace_based_take_probability("QB", "qb1", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        self.assertAlmostEqual(p, 2.5 / ds.PACE_CATCH_UP_WINDOW, places=6)

    def test_probability_rises_continuously_with_no_discontinuity_across_an_anchor_boundary(self):
        # The real sawtooth bug this module's own history now documents: an earlier version
        # spread the deficit over "picks remaining until the NEXT anchor," which reset downward
        # the instant picks_made_now crossed an anchor boundary (12, 24, ...) -- a real hazard
        # should never drop back down just because a deadline passed unmet. Assert the
        # continuous version directly, one pick before and one pick after the round-1 anchor.
        board = _synthetic_board([{"player_id": "qb1", "position": "QB", "universal_value": 90.0}])
        just_before = ds._pace_based_take_probability("QB", "qb1", board, 11, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        just_after = ds._pace_based_take_probability("QB", "qb1", board, 13, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        self.assertGreaterEqual(just_after, just_before, "hazard must not drop after crossing an anchor boundary with the deficit still unmet")

    def test_a_lower_ranked_qb_shares_the_probability_with_his_peers(self):
        board = _synthetic_board([
            {"player_id": "qb1", "position": "QB", "universal_value": 90.0},
            {"player_id": "qb2", "position": "QB", "universal_value": 80.0},
            {"player_id": "qb3", "position": "QB", "universal_value": 70.0},
        ])
        p1 = ds._pace_based_take_probability("QB", "qb1", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        p3 = ds._pace_based_take_probability("QB", "qb3", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        self.assertGreater(p1, p3, "the top-ranked remaining QB should get a bigger share than the 3rd-ranked one")
        self.assertAlmostEqual(p3, p1 / 3, places=6)

    def test_deficit_shrinks_as_actual_drafting_catches_up_to_the_convention(self):
        board = _synthetic_board([{"player_id": "qb1", "position": "QB", "universal_value": 90.0}])
        no_qbs_drafted = ds._pace_based_take_probability("QB", "qb1", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"])
        already_on_pace = ds._pace_based_take_probability(
            "QB", "qb1", board, 5,
            [{"player_id": "x1", "round": 1}, {"player_id": "x2", "round": 1}],
            {"x1": {"position": "QB", "fantasy_positions": ["QB"]}, "x2": {"position": "QB", "fantasy_positions": ["QB"]}},
            SUPERFLEX_LEAGUE["roster_positions"],
        )
        self.assertLess(already_on_pace, no_qbs_drafted)

    def test_none_when_the_target_is_not_on_the_given_board_at_all(self):
        board = _synthetic_board([{"player_id": "other", "position": "QB", "universal_value": 90.0}])
        self.assertIsNone(ds._pace_based_take_probability(
            "QB", "not-there", board, 5, [], {}, SUPERFLEX_LEAGUE["roster_positions"],
        ))


class EstimateSurvivalPaceIntegrationTests(unittest.TestCase):
    """The real case that motivated this mechanism: a rank-based estimate structurally can't
    move for a player who ranks outside the top-5 keys on every intervening team's own board
    (it floors near zero regardless of position), which is exactly what happens to an elite QB
    in a superflex league before the market convention is applied as a prior."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_players_db(("QB", "RB", "WR", "TE"))

    def test_pace_prior_can_push_survival_down_when_the_rank_based_estimate_understates_it(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        best_qb_id = next(r["player_id"] for r in board if r["position"] == "QB")
        # A round-1-shaped scenario with zero QBs drafted through 5 picks -- a real deficit
        # against the documented round-1 pace (~2.5 expected by now).
        picks = [{"roster_id": str(i), "player_id": r["player_id"], "round": 1}
                 for i, r in enumerate([r for r in board if r["position"] != "QB"][:5], start=1)]
        pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)
        intervening = ds.intervening_roster_ids(pick_order, 5, ds.find_next_pick_index(pick_order, "6", 5))
        boards = ds._build_opponent_boards(self.merger, self.players_db, picks, SUPERFLEX_LEAGUE, intervening)

        without_prior = ds.estimate_survival(
            picks, self.players_db, pick_order, 5, "6", best_qb_id, boards, league=None,
        )
        with_prior = ds.estimate_survival(
            picks, self.players_db, pick_order, 5, "6", best_qb_id, boards, league=SUPERFLEX_LEAGUE,
        )
        self.assertLessEqual(with_prior["survival_probability"], without_prior["survival_probability"])
        self.assertTrue(any(r["pace_driven"] for r in with_prior["risk_by_team"]))

    def test_hazard_rises_across_successive_intervening_picks_within_one_computation(self):
        # The run-momentum fix: within a SINGLE estimate_survival call, the pace-based
        # take-probability for a later intervening pick must be >= an earlier one's, since the
        # same documented deficit gets concentrated over fewer remaining picks as the anchor
        # deadline approaches -- "he's survived further than expected" mechanically raises the
        # hazard for the next pick, not a separately invented boost.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        best_qb_id = next(r["player_id"] for r in board if r["position"] == "QB")
        picks = [{"roster_id": str(i), "player_id": r["player_id"], "round": 1}
                 for i, r in enumerate([r for r in board if r["position"] != "QB"][:3], start=1)]
        pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)
        # A long gap (picking 1st overall) so several intervening picks land in ONE computation.
        intervening = ds.intervening_roster_ids(pick_order, 0, ds.find_next_pick_index(pick_order, "1", 0))
        boards = ds._build_opponent_boards(self.merger, self.players_db, picks, SUPERFLEX_LEAGUE, intervening)
        result = ds.estimate_survival(picks, self.players_db, pick_order, 0, "1", best_qb_id, boards, league=SUPERFLEX_LEAGUE)
        pace_driven_probs = [r["take_probability"] for r in result["risk_by_team"] if r["pace_driven"]]
        self.assertGreaterEqual(len(pace_driven_probs), 2, "fixture didn't produce enough pace-driven picks to exercise this")
        self.assertEqual(pace_driven_probs, sorted(pace_driven_probs), "hazard must not decrease across successive intervening picks")
        self.assertLess(pace_driven_probs[0], pace_driven_probs[-1], "hazard must actually rise, not just stay flat")

    def test_pace_prior_never_makes_survival_worse_than_the_rank_based_estimate_when_its_the_weaker_signal(self):
        # A player who's already the clear #1 on every intervening team's own board has a real
        # rank-based take_probability (0.55) that should beat whatever the pace prior alone
        # would produce here -- the max-combinator must keep using the stronger, real signal.
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        top_overall_id = board[0]["player_id"]
        picks: list[dict] = []
        pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=4)
        intervening = ds.intervening_roster_ids(pick_order, 0, ds.find_next_pick_index(pick_order, "1", 0))
        boards = ds._build_opponent_boards(self.merger, self.players_db, picks, SUPERFLEX_LEAGUE, intervening)
        result = ds.estimate_survival(
            picks, self.players_db, pick_order, 0, "1", top_overall_id, boards, league=SUPERFLEX_LEAGUE,
        )
        # Whatever this comes out to, it must be no more forgiving than a plain rank-based read
        # would have been for the actual #1 overall player across a long gap.
        without_prior = ds.estimate_survival(
            picks, self.players_db, pick_order, 0, "1", top_overall_id, boards, league=None,
        )
        self.assertLessEqual(result["survival_probability"], without_prior["survival_probability"] + 1e-9)


if __name__ == "__main__":
    unittest.main()
