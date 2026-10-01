"""
Covers draft_strategy.py's real invariants: pick-order/snake mechanics, positional-run
detection as a real signal (not an invented one), survival probability's actual monotonic
behavior, and a hard performance regression guard -- an earlier version of this module
recomputed a full draft board per intervening PICK POSITION and per CANDIDATE separately,
which measured at 40+ seconds against a modest player pool for a worst-case pick gap. That
bug is exactly the kind that reappears silently after a future edit if nothing asserts on
wall-clock time directly.
"""

import inspect
import math
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

    def test_the_consensus_top_player_is_unlikely_to_survive_a_long_gap_but_not_impossible(self):
        """INVERTED ON REPAIR (#206, 2026-09-16), on a REAL board rather than a fixture.

        This asserted `survival < 0.05` for the #1 overall across 22 intervening picks, and the
        engine delivered ~2.3e-8 -- not a low probability but an impossibility the model had no
        way to express, for a player the real draft then let survive 60 straight picks. That
        assertion WAS the defect, written down as intent.

        Normalising the take mass (one team, one pick, so the probabilities are mutually
        exclusive and sum to 1.0 across the board) leaves **0.092**. Still unlikely -- the #1
        overall usually does go -- but now a number a person can reason about, and one that can
        be wrong in a way the old answer could not."""
        board = dr.compute_draft_board(self.merger, self.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")
        top_player_id = board[0]["player_id"]
        my_next = ds.find_next_pick_index(self.pick_order, "1", after_index=0)
        intervening = ds.intervening_roster_ids(self.pick_order, 0, my_next)
        opponent_boards = ds._build_opponent_boards(self.merger, self.players_db, [], LEAGUE, intervening)
        result = ds.estimate_survival([], self.players_db, self.pick_order, 0, "1", top_player_id, opponent_boards)
        survival = result["survival_probability"]
        self.assertLess(survival, 0.25, "the #1 overall still should not be expected to survive")
        self.assertGreater(survival, 0.01, "but it is a probability now, not an impossibility")

        # THE INVARIANT THE REPAIR EXISTS FOR, checked on this real board rather than assumed.
        one_board = opponent_boards[intervening[0]]
        mass = ds.board_take_mass(one_board)
        total = sum(ds._take_probability(rank, False, mass["total_weight"])
                    for rank in one_board["rank_by_id"].values())
        total += mass["unpriced_rows"] * ds._take_probability(None, False, mass["total_weight"])
        self.assertAlmostEqual(total, 1.0, places=9,
                               msg="a team makes one pick; its take mass must sum to 1.0")

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
        # This fixture always produces a premium-bearing opponent, so the None branch below is
        # unreachable HERE and is asserted to be, rather than sitting as a dead conditional an
        # assertion-reachability trace flags every run. The None case is real and is covered
        # where it actually occurs -- an unpriced candidate no opponent can price, in
        # test_absence_survives_consumers.LateBoardIntegrationTests.
        self.assertIsNotNone(expected_take_prob,
                             "fixture no longer produces a premium-bearing opponent; the "
                             "branch this test exercises has moved")
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
    """positional_forfeits IS a pick_necessity input (weight 10 of 100) and reaches the debate
    prompt; it has no selection authority, because the pick sorts on final_score alone. This
    docstring previously said "never an input to necessity", which was false from `7655fb1`
    onward -- corrected 2026-09-16 after an independent review traced the dataflow.

    What gets tested is the math and its load-bearing properties: a steeper position curve
    costs more to delay, more opponent appetite raises expected_taken, and a fractional
    expectation is no longer quantised to a whole player."""

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

    def test_within_one_pick_summation_order_cannot_reach_the_decision(self):
        """The site backlog B flagged: `for player_id, rank in rank_by_id.items()` accumulating
        into a float. rank_by_id is built as {pid: i+1 for i, r in enumerate(priced)}, so it
        ALWAYS iterates in ascending rank -- there is exactly one realizable order. This proves
        the stronger property anyway: even handed a permuted dict, the rounded outputs are
        identical, because no subset of ranks 1..DEPTH has an order-dependent round().

        Ranks (1, 2, 4) are used deliberately: their sum is one of the twelve that IS
        order-dependent in raw float (0.97 vs 0.9700000000000001). The assertion is that the
        difference cannot survive to the output."""
        import itertools
        ranks_with_target = (1, 2, 4)
        rows = []
        for r in range(1, max(ds.RANK_TAKE_PROBABILITY) + 1):
            rows.append((f"p{r}", "QB" if r in ranks_with_target else "RB", 100.0 - r))
        raw_sums = set()
        for perm in itertools.permutations(ranks_with_target):
            acc = 0.0
            for r in perm:
                acc += ds.RANK_TAKE_PROBABILITY[r]
            raw_sums.add(acc)
        self.assertGreater(len(raw_sums), 1,
                           "fixture no longer exercises an order-dependent sum -- pick another "
                           "rank subset or this test proves nothing")

        curves = {"QB": [80.0, 70.0, 60.0, 55.0], "RB": [50.0, 40.0]}
        results = set()
        for perm in itertools.permutations(range(len(rows))):
            permuted = [rows[i] for i in perm]
            ranks = {pid: i + 1 for i, (pid, _p, _v) in enumerate(rows)}
            board = {
                "by_id": {pid: {"player_id": pid, "position": pos, "universal_value": uv,
                                "final_score": uv} for pid, pos, uv in permuted},
                "rank_by_id": {pid: ranks[pid] for pid, _p, _v in permuted},
                "unpriced_ids": set(),
            }
            out = ds.positional_forfeits(curves, {"2": board}, ["2"])
            results.add(tuple(sorted((p, d["expected_taken"], d["forfeit"])
                                     for p, d in out.items())))
        self.assertEqual(len(results), 1,
                         "permuting rank_by_id's insertion order changed the forfeit output")

    def test_the_round_boundary_IS_GONE_and_float_noise_no_longer_decides(self):
        """REPLACES `test_KNOWN_SENSITIVITY_the_round_boundary_is_decided_by_float_noise`, which
        pinned the rounding as a KNOWN, DEFERRED sensitivity and instructed whoever fixed the
        rule to rewrite it here rather than delete it quietly. #86 fixed the rule.

        The old test's adversarial fixture is KEPT EXACTLY -- three boards contributing
        0.24 + 0.60 + 0.66, whose sum is 1.5 in one order and 1.5 - 1ulp in the other. That was
        the sharpest construction anyone found for this mechanism and it stays the probe; only
        the expectation moves. Under `round()` the two orders returned 20.0 and 10.0 while both
        REPORTED `expected_taken` as 1.5, so the surfaced explanation could not distinguish them.
        Reading the curve at a fractional index makes the two orders agree to within a float
        ulp, because a 1ulp difference in the input can now only move the output by ~1ulp."""
        table = ds.RANK_TAKE_PROBABILITY

        def board_with_qb_at(target_ranks):
            rows = []
            for r in range(1, max(ds.RANK_TAKE_PROBABILITY) + 1):
                pos = "QB" if r in target_ranks else "RB"
                rows.append({"player_id": f"p{r}", "position": pos,
                             "final_score": 100.0 - r, "universal_value": 100.0 - r})
            return {"by_id": {r["player_id"]: r for r in rows},
                    "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(rows)},
                    "unpriced_ids": set()}

        want = {"A": (3, 5), "B": (2, 3, 4), "C": (2, 3, 4, 5)}   # 0.24, 0.60, 0.66 -> 1.5
        self.assertAlmostEqual(sum(sum(table[r] for r in v) for v in want.values()), 1.5,
                               places=9, msg="fixture no longer sums to the round() boundary")
        boards = {k: board_with_qb_at(v) for k, v in want.items()}
        curves = {"QB": [80.0, 70.0, 60.0, 55.0]}
        forfeits, reported = set(), set()
        for order in (["A", "B", "C"], ["C", "B", "A"]):
            d = ds.positional_forfeits(curves, boards, order)["QB"]
            forfeits.add(d["forfeit"])
            reported.add(d["expected_taken"])
        # THE CLAIM, UNTOUCHED BY THE MODEL CHANGE (#52 phase 7.2): accumulation order does not
        # move the answer. Under round() the two orders returned forfeits of 20.0 and 10.0 while
        # both REPORTED the same expected_taken, so the surfaced explanation could not
        # distinguish them. That is the defect. The raw fixture still sums to the 1.5 boundary,
        # which is what makes it adversarial and is asserted above -- but positional_forfeits
        # now reads the NORMALISED model, so what it reports off this fixture is 1.24, not 1.5.
        # The exact value is the fixture; the invariance is the claim.
        self.assertEqual(len(reported), 1,
                         f"accumulation order changes the reported take: {sorted(reported)}")
        self.assertEqual(len(forfeits), 1,
                         f"accumulation order still changes the forfeit: {sorted(forfeits)}")

    def test_the_curve_read_is_stable_across_a_one_ulp_step_at_a_rounding_boundary(self):
        """The mechanism itself, tested where it lives and independently of the take model.

        The test above can only reach the boundary while the take model happens to put it
        there, and #52 phase 7.2 moved the model, which moved the fixture off 1.5. The property
        being defended is a property of the CURVE READ: a 1ulp difference in the index may move
        the output by about 1ulp, never by a curve step. Asserted directly, so it survives the
        next model change too."""
        curve = [80.0, 70.0, 60.0, 55.0]
        at = ds._curve_at(curve, 1.5)
        # Halfway between curve[1]=70 and curve[2]=60. Stated as arithmetic rather than as a
        # recorded output, so this catches a curve read that is stable but wrong.
        self.assertEqual(at, 65.0)
        for neighbour in (math.nextafter(1.5, 0.0), math.nextafter(1.5, 2.0)):
            self.assertLess(abs(ds._curve_at(curve, neighbour) - at), 1e-9,
                            "a one-ulp step in the index moved the curve read by a real amount "
                            "-- the round() boundary is back")

    def test_a_fractional_expectation_is_not_quantised_to_a_whole_player(self):
        """THE DEFECT #86 ACTUALLY FIXED, and it is not the float-noise one the appendix led
        with. `round()` sent every `expected_taken` below 0.5 to drop=0, so the forfeit came
        back as EXACTLY 0.00 while the model expected a fraction of a player to go. Measured on
        Fourth and Forever: 4 of 44 observations, every one at WR, where 0.48 reported 0.00 and
        0.60 reported 9.44.

        0.00 in this engine means "measured, and the cost is nothing", so reporting it while a
        fraction of a receiver was expected to go is an absence-contract breach reached by
        arithmetic rather than by a substituted default -- the #187 class.

        THIS NAME WAS "never reports a forfeit of zero" AND THAT WAS FALSE OF THE SHIPPED
        FUNCTION (corrected 2026-09-16, independent review). `positional_forfeits` rounds its
        output to 2dp, so a near-flat curve still returns exactly 0.0 for a fractional
        expectation -- `positional_forfeits({'WR': [100.0, 99.95, 80.0]}, ...)` gives
        `expected_taken=0.06, forfeit=0.0`. That is harmless, because the cost really is under
        half a cent, but "never" was a universal this code does not deliver. The property it
        DOES deliver is the one now in the name, and it is the one the defect was about.

        TWO MORE CORRECTIONS TO THIS TEST'S OWN EVIDENCE. The 44 observations are ONE pre-draft
        board state read at 11 gap lengths, not 44 independent data points -- every nonzero
        `expected_taken` there is 0.06n or 0.9n. And "the true statement was about 4.5 points"
        overstates: linear interpolation reads the curve at the MEAN count, curve[E[N]], while
        the honest expectation is E[curve[N]]. On that same row the exact Poisson-binomial is
        5.48, not 4.53, with P(no WR taken) = 0.61. Interpolation is a better approximation
        than 0.00, not the truth."""
        curve = [100.0, 90.0, 80.0]
        for taken in (0.12, 0.24, 0.36, 0.48):
            got = ds._curve_at(curve, taken)
            self.assertLess(got, curve[0],
                            f"expected_taken={taken} left the best player untouched")
            self.assertAlmostEqual(curve[0] - got, 10.0 * taken, places=9)

    def test_the_curve_read_is_monotone_and_clamped_to_real_players(self):
        """Two properties the rounded form did not have. MONOTONE: more players expected gone
        can never mean a smaller forfeit, which `round()` satisfied only in steps. CLAMPED: a
        position cannot lose more players than it has, so no extrapolation past the data -- the
        last entry is the worst player actually priced there."""
        curve = [100.0, 90.0, 80.0, 75.0]
        vals = [ds._curve_at(curve, t / 10) for t in range(0, 31)]
        self.assertEqual(vals, sorted(vals, reverse=True))
        self.assertEqual(ds._curve_at(curve, 99.0), curve[-1])
        self.assertEqual(ds._curve_at(curve, -5.0), curve[0])
        self.assertEqual(ds._curve_at([], 1.0), 0.0)

    def test_expected_taken_cannot_exceed_the_picks_available_to_take_them(self):
        """THE CONSERVATION LAW, which nothing checked (#52 phase 7.2; J-03 and K-02 found it
        independently). One pick takes exactly one player, so summed over positions and over
        intervening picks, expected_taken cannot exceed the number of picks.

        The old model capped at RUN_TAKE_PROBABILITY_CAP PER POSITION, which conserves nothing:
        four positions each capped at 0.90 permit 3.6 players from a single pick. Measured on a
        real superflex board across five consecutive turns it returned 22.80/20, 21.78/18,
        19.36/16 and 16.94/14 -- arithmetically impossible -- while turn 0's 22.00/22 conserved
        only by coincidence, RB saturating at 0.90 x 22.

        Built on a hand-made board where the bound is checkable by eye, so this does not depend
        on a capture; the same law is measured against real boards in the evidence run."""
        positions = ("QB", "RB", "WR", "TE")
        rows = []
        for i in range(40):
            rows.append({"player_id": f"p{i}", "position": positions[i % 4],
                         "final_score": 100.0 - i, "universal_value": 100.0 - i})
        board = {"by_id": {r["player_id"]: r for r in rows},
                 "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(rows)},
                 "unpriced_ids": set()}
        curves = {p: [100.0 - j for j in range(10)] for p in positions}
        for n_picks in (1, 3, 8, 20):
            intervening = [str(i) for i in range(2, 2 + n_picks)]
            boards = {r: board for r in intervening}
            out = ds.positional_forfeits(curves, boards, intervening)
            total = sum(v["expected_taken"] for v in out.values())
            # The tolerance is the REPORTING precision, derived rather than chosen: each
            # position's expected_taken is rounded to 2dp for display, so a sum over P positions
            # can exceed the true total by up to P x 0.005. Measured at 3 picks: 3.01. The law
            # holds on the unrounded quantity; this is the most it can be obscured by.
            slack = 0.005 * len(out)
            with self.subTest(picks=n_picks):
                self.assertLessEqual(
                    total, n_picks + slack,
                    f"{total:.2f} players expected taken from {n_picks} pick(s) -- beyond what "
                    f"2dp rounding over {len(out)} positions can account for ({slack:.3f})")
                # Non-vacuity in the other direction: a model that returns zero everywhere also
                # satisfies the bound, and that is the failure mode the top-5 cut produced.
                self.assertGreater(total, 0.0, "nothing is ever expected to be taken")

    def test_on_a_fully_priced_board_the_takes_sum_to_EXACTLY_the_pick_count(self):
        """The equality case, and the one that catches a window.

        Conservation as an inequality is satisfied by any model that undercounts, including the
        one this replaced in the other direction: normalising but keeping the old top-5 cut
        reports **1.19 expected takes across 22 picks**, because `#206` measured the five named
        keys at 1.21 of a 23.49 board total and the floor-weighted tail carries the rest. An
        upper bound cannot see that, and a lower bound would be a threshold nobody derived.

        The equality is derived and needs no constant: the model normalises over the WHOLE
        board, so if every row is priced, the probabilities of one pick sum to exactly 1.0
        across all positions -- that pick takes somebody. Over N picks the total is N. Any row
        the sum skips, for any reason, shows up here immediately.

        On a real board the total is strictly less, and the shortfall is the expected number of
        UNPRICED takes -- which is why this fixture prices everything."""
        positions = ("QB", "RB", "WR", "TE")
        rows = [{"player_id": f"p{i}", "position": positions[i % 4],
                 "final_score": 100.0 - i, "universal_value": 100.0 - i} for i in range(40)]
        board = {"by_id": {r["player_id"]: r for r in rows},
                 "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(rows)},
                 "unpriced_ids": set()}
        self.assertEqual(board["unpriced_ids"], set(), "the equality needs a fully priced board")
        curves = {p: [100.0 - j for j in range(10)] for p in positions}
        for n_picks in (1, 4, 11):
            intervening = [str(i) for i in range(2, 2 + n_picks)]
            out = ds.positional_forfeits(curves, {r: board for r in intervening}, intervening)
            total = sum(v["expected_taken"] for v in out.values())
            with self.subTest(picks=n_picks):
                self.assertAlmostEqual(
                    total, float(n_picks), delta=0.005 * len(out),
                    msg=f"{total:.2f} of {n_picks} pick(s) accounted for -- the sum is skipping "
                        f"board rows, which is what a depth window does")

    def test_no_position_on_a_full_board_is_expected_to_lose_nobody(self):
        """The consequence the chairs were shown. With the raw table capped per position, RB
        saturated and starved the rest: measured on a real superflex board, TE came back 0.00
        on every one of five turns and QB on two -- and pick_debate renders an exactly-zero
        forfeit as "Cost of delaying QB entirely: measured 0", the strongest evidence for
        waiting, while survival (which says those QBs are gone) is withheld."""
        positions = ("QB", "RB", "WR", "TE")
        rows = []
        for i in range(40):
            rows.append({"player_id": f"p{i}", "position": positions[i % 4],
                         "final_score": 100.0 - i, "universal_value": 100.0 - i})
        board = {"by_id": {r["player_id"]: r for r in rows},
                 "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(rows)},
                 "unpriced_ids": set()}
        curves = {p: [100.0 - j for j in range(10)] for p in positions}
        intervening = [str(i) for i in range(2, 12)]
        out = ds.positional_forfeits(curves, {r: board for r in intervening}, intervening)
        self.assertEqual(sorted(out), sorted(positions), "a position vanished from the report")
        for position, data in sorted(out.items()):
            with self.subTest(position=position):
                self.assertGreater(
                    data["expected_taken"], 0.0,
                    f"{position} is on every rival board and is expected to lose nobody across "
                    f"{len(intervening)} picks")

    def test_both_consumers_of_the_take_table_read_it_through_one_model(self):
        """REPLACES `test_the_forfeit_depth_and_the_take_probability_table_stay_coupled`, and
        the replacement is the point (#52 phase 7.2).

        That test existed because the two consumers read the table with DIFFERENT defaults --
        `positional_forfeits` took `.get(rank, 0.0)` and `_take_probability` took
        `.get(rank, RANK_TAKE_PROBABILITY_FLOOR)` -- and it guarded the coupling that kept the
        0.0 unreachable. The divergence is now REMOVED rather than guarded: both consumers go
        through `_take_probability`, which is the body of `_board_take_probability`, the home
        the take model's own docstring already claimed to be ("there is exactly ONE take model
        in production and this is its only home"). That claim was false for as long as this
        second consumer existed beside it.

        What is pinned now is the unification, which is stronger than the coupling it replaces:
        there is no second default left to drift."""
        self.assertFalse(
            hasattr(ds, "FORFEIT_OPPONENT_BOARD_DEPTH"),
            "the depth cut is back -- the forfeit sum is reading a window of the board again")
        source = inspect.getsource(ds.positional_forfeits)
        self.assertIn("_take_probability(", source,
                      "positional_forfeits stopped reading the shared take model")
        self.assertNotIn("RANK_TAKE_PROBABILITY.get(", source,
                         "positional_forfeits is reading the raw table directly again")
        # ...and the shared model's default for an untabulated rank is the floor, never a
        # silent 0.0, which is an absence spelled as a number.
        beyond = max(ds.RANK_TAKE_PROBABILITY) + 1
        self.assertEqual(ds._take_weight(beyond, False), ds.RANK_TAKE_PROBABILITY_FLOOR)
        self.assertGreater(ds.RANK_TAKE_PROBABILITY_FLOOR, 0.0)

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


class TakeProbabilityTableStructureTests(unittest.TestCase):
    """Mutation testing raised RANK_TAKE_PROBABILITY_FLOOR from 0.02 to 0.50 -- a 25x change
    to how likely an unranked player is to be taken, compounded across every intervening
    pick -- with the whole suite still green. Nothing pinned the table's SHAPE, only its
    use."""

    def test_the_table_falls_off_monotonically_by_rank(self):
        ranks = sorted(ds.RANK_TAKE_PROBABILITY)
        values = [ds.RANK_TAKE_PROBABILITY[r] for r in ranks]
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)), "ranks must be 1..N with no gaps")
        for earlier, later in zip(values, values[1:]):
            self.assertGreater(earlier, later, "a worse board rank must not be likelier to be taken")

    def test_an_untabulated_rank_is_less_likely_than_the_worst_tabulated_one(self):
        # The floor covers everyone past the table -- players no opponent has near the top of
        # their board. It has to sit clearly BELOW the last tabulated entry, or "nobody rates
        # this player" starts reading as "somebody is about to take him," and survival
        # probability collapses across a full round of intervening picks.
        worst_tabulated = ds.RANK_TAKE_PROBABILITY[max(ds.RANK_TAKE_PROBABILITY)]
        self.assertLess(ds.RANK_TAKE_PROBABILITY_FLOOR, worst_tabulated / 2.0)

    def test_survival_stays_meaningful_across_a_full_round_of_unranked_picks(self):
        # The consequence that actually matters, stated as compounding: a player outside
        # every opponent's top ranks must still be more likely than not to survive a full
        # 11-pick round. At the real floor that is ~0.80; at 0.50 it is ~0.0005.
        survives_one = 1.0 - ds.RANK_TAKE_PROBABILITY_FLOOR
        self.assertGreater(survives_one ** 11, 0.5)

    def test_the_tail_past_the_table_is_where_most_of_a_boards_mass_lives(self):
        """WITHDRAWN AND INVERTED (#52 phase 7.2). This asserted FORFEIT_OPPONENT_BOARD_DEPTH
        equals the table's depth, on the reasoning that "ranks past it carry only the flat floor
        and would add noise, not signal".

        That is true of the RAW table and false of the normalised one, which is the only model
        left. `#206` measured a real board at 23.49 total weight, of which the five named keys
        were 1.21 -- so the floor-weighted tail is not noise, it is 95% of the signal, and
        cutting at the table's depth reports 1.19 expected takes across 22 picks. The constant
        is deleted; what replaces this is the measurement that made the cut indefensible."""
        # DERIVED, not a guessed row count. The first version of this assertion picked 40 tail
        # rows out of the air and failed, because 40 x 0.02 = 0.80 is less than the named keys'
        # 1.21 -- which was my arithmetic being wrong, not the claim. The honest quantity is the
        # CROSSOVER: how many floor-weighted rows it takes to outweigh the named keys at all.
        named = sum(ds.RANK_TAKE_PROBABILITY.values())
        crossover = named / ds.RANK_TAKE_PROBABILITY_FLOOR
        # A real opponent board carries on the order of a thousand rows (#206 measured 23.49
        # total weight against named 1.21, tail 9.52 and unpriced 12.76), so a crossover this
        # low means the tail dominates on every board the engine has ever built.
        self.assertLess(
            crossover, 100,
            f"it now takes {crossover:.0f} floor rows to outweigh the {len(ds.RANK_TAKE_PROBABILITY)} "
            f"named keys ({named}); the tail may no longer dominate a real board, so the depth "
            f"cut may be defensible again and this test is the place to re-argue it")
        self.assertGreater(crossover, 1, "the floor alone outweighs the whole named table")


if __name__ == "__main__":
    unittest.main()
