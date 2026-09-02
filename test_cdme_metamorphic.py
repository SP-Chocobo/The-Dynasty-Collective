"""CDME certification battery, priority 3: metamorphic testing. Instead of one expected
answer, these define a transformation of a real input and check that CDME's output stays
invariant (or moves in a provably correct direction) under that transformation -- a class of
bug ordinary example-based tests miss, per the adversarial research program's own framing.

All perturbations start from the real committed baseline (same DataMerger()/players_db
builder used throughout this program), never a synthetic fixture, except where isolating one
specific mechanism (_take_probability's own rank monotonicity) needs a value real data can't
be steered to hit precisely.
"""

from __future__ import annotations

import random
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps

POSITIONS = ("QB", "RB", "WR", "TE")
STANDARD_LEAGUE = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)


def _build_pool_players_db(merger: dm.DataMerger) -> dict[str, dict]:
    proj = merger.projections
    players_db: dict[str, dict] = {}
    pid = 0
    for pos in POSITIONS:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return players_db


class IrrelevantAdditionTests(unittest.TestCase):
    """Adding something far below the decision's own event horizon must not perturb the
    decision -- a real player far below the candidate floor, or an unrelated roster slot."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)

    def test_adding_a_player_far_below_the_floor_does_not_change_the_top_pick(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=STANDARD_LEAGUE, mode="balanced",
        )
        top_before = ps.narrow_candidates(board, top_n=5)[0]["player_id"]

        # A row far below the real floor -- lower universal_value/final_score than anyone on
        # the real board -- appended, never removed or reordered.
        floor_score = min(r["final_score"] for r in board)
        irrelevant = dict(board[-1])
        irrelevant["player_id"] = "irrelevant-999999"
        irrelevant["final_score"] = floor_score - 1000.0
        irrelevant["universal_value"] = floor_score - 1000.0
        irrelevant["name"] = "Zzz Deep Bench Nobody"
        board_plus_one = board + [irrelevant]

        top_after = ps.narrow_candidates(board_plus_one, top_n=5)[0]["player_id"]
        self.assertEqual(top_before, top_after)

    def _boards_with_and_without_an_extra_bench_slot(self):
        before = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=STANDARD_LEAGUE, mode="balanced",
        )
        league_plus_bn = dict(STANDARD_LEAGUE)
        league_plus_bn["roster_positions"] = list(STANDARD_LEAGUE["roster_positions"]) + ["BN"]
        after = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=league_plus_bn, mode="balanced",
        )
        return before, after

    # This used to be one assertEqual over the whole board row. The valuation half of that is
    # the real metamorphic property and is unchanged below -- but the row now also carries
    # draft-horizon fields, and a bench slot is emphatically NOT irrelevant to those: one more
    # BN across 12 teams is 12 more picks, so 12 more players come off the board and the best
    # one left when the draft ends is genuinely worse. A whole-row equality would have
    # asserted the horizon estimator ignores draft depth, which would be the bug, not the fix.
    # Split into the two separate claims so both directions are actually pinned.
    VALUATION_FIELDS = ("player_id", "name", "position", "bpa", "bpa_source", "universal_value",
                        "need_bonus", "eligibility_bonus", "final_score", "projected_points")

    def test_adding_an_unrelated_bench_slot_does_not_change_universal_value_or_final_score(self):
        before, after = self._boards_with_and_without_an_extra_bench_slot()
        self.assertEqual(
            [{k: r[k] for k in self.VALUATION_FIELDS} for r in before],
            [{k: r[k] for k in self.VALUATION_FIELDS} for r in after],
        )

    def test_adding_a_bench_slot_does_deepen_the_draft_horizon(self):
        # The other half: a longer draft leaves a worse player undrafted, so the floor must
        # fall and the cost of waiting must rise. If this ever stops moving, the horizon has
        # gone blind to how many picks the league actually makes.
        before, after = self._boards_with_and_without_an_extra_bench_slot()
        pairs = [
            (b, a) for b, a in zip(before, after)
            if b["horizon_floor"] is not None and a["horizon_floor"] is not None
        ]
        self.assertTrue(pairs, "no measurable horizon floors to compare")
        self.assertTrue(
            any(a["horizon_floor"] < b["horizon_floor"] for b, a in pairs),
            "a deeper draft must lower the expected end-of-draft floor somewhere",
        )
        for b, a in pairs:
            self.assertLessEqual(a["horizon_floor"], b["horizon_floor"])
            self.assertGreaterEqual(a["waiting_cost"], b["waiting_cost"])


class OrderShuffleTests(unittest.TestCase):
    """The candidate set narrow_candidates returns, and the decision built on top of it, must
    not depend on the incoming board's own row order."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)
        cls.board = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="1", league=STANDARD_LEAGUE, mode="balanced",
        )

    def test_shuffling_the_incoming_board_row_order_does_not_change_narrow_candidates(self):
        shuffled = list(self.board)
        random.Random(7).shuffle(shuffled)
        narrowed_original = ps.narrow_candidates(list(self.board), top_n=5)
        narrowed_shuffled = ps.narrow_candidates(shuffled, top_n=5)
        self.assertEqual(
            [r["player_id"] for r in narrowed_original],
            [r["player_id"] for r in narrowed_shuffled],
        )

    def test_shuffling_narrowed_candidates_before_decision_path_flags_does_not_change_flags_per_player(self):
        narrowed = ps.narrow_candidates(self.board, top_n=8)
        raw = [{
            "universal_value": r["universal_value"], "team_acquisition_value": r["final_score"],
            "positional_forfeit": None, "rival_premium": None,
        } for r in narrowed]
        flags_original = dict(zip((r["player_id"] for r in narrowed), ps.decision_path_flags(raw)))

        order = list(range(len(narrowed)))
        random.Random(3).shuffle(order)
        raw_shuffled = [raw[i] for i in order]
        ids_shuffled = [narrowed[i]["player_id"] for i in order]
        flags_shuffled = dict(zip(ids_shuffled, ps.decision_path_flags(raw_shuffled)))

        self.assertEqual(flags_original, flags_shuffled)


class RivalNeedMonotonicityTests(unittest.TestCase):
    """Increasing an intervening rival's own roster need for a position must not DECREASE
    that rival's premium for a candidate at that position -- rival_premium is
    opp_row["final_score"] - opp_row["universal_value"] (draft_strategy.pick_analysis), and
    final_score's own need_bonus term only grows as a roster's unfilled dedicated slots at
    that position grow (draft_room.py's own ARCHITECTURE section)."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)

    def test_a_rival_with_zero_rostered_qbs_values_a_qb_at_least_as_much_as_one_with_a_full_room(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="99", league=STANDARD_LEAGUE, mode="balanced",
        )
        target_qb_id = next(r["player_id"] for r in board if r["position"] == "QB")

        # Rival A: no picks at all -- zero rostered QBs, real unfilled need.
        board_needy = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="rival_needy", league=STANDARD_LEAGUE, mode="balanced",
        )
        row_needy = next(r for r in board_needy if r["player_id"] == target_qb_id)

        # Rival B: already has a full room of other QBs (need satisfied), built from real
        # board data -- the next few best QBs behind the target, drafted onto rival B's own
        # roster before scoring rival B's own board.
        other_qb_ids = [r["player_id"] for r in board if r["position"] == "QB" and r["player_id"] != target_qb_id][:4]
        picks_for_rival_full = [
            {"roster_id": "rival_full", "player_id": pid, "round": 1} for pid in other_qb_ids
        ]
        board_full = dr.compute_draft_board(
            self.merger, self.players_db, picks_for_rival_full, my_roster_id="rival_full",
            league=STANDARD_LEAGUE, mode="balanced",
        )
        row_full = next(r for r in board_full if r["player_id"] == target_qb_id)

        premium_needy = row_needy["final_score"] - row_needy["universal_value"]
        premium_full = row_full["final_score"] - row_full["universal_value"]
        self.assertGreaterEqual(
            premium_needy, premium_full,
            "a rival with zero rostered QBs should value the same QB candidate at least as much "
            "as a rival who already has a full QB room -- need_bonus should not have DECREASED "
            "for the needier rival",
        )


class TakeProbabilityRankMonotonicityTests(unittest.TestCase):
    """Removing a same-position competitor who ranked ABOVE the target on an opponent's own
    board improves (numerically decreases) the target's rank there, which must not DECREASE
    that opponent's own take_probability for the target -- the direct, safe version of "remove
    a competing player -> urgency moves predictably," isolating _take_probability's own
    documented monotonicity (RANK_TAKE_PROBABILITY strictly decreases as rank increases)
    rather than constructing a full multi-team draft scenario with more moving parts than
    this one link needs."""

    def test_take_probability_never_increases_as_rank_number_increases(self):
        ranks = sorted(ds.RANK_TAKE_PROBABILITY.keys())
        probs = [ds._take_probability(r, is_run_position=False) for r in ranks]
        for earlier, later in zip(probs, probs[1:]):
            self.assertGreaterEqual(earlier, later)

    def test_a_rank_outside_the_table_never_exceeds_the_best_tabulated_rank(self):
        best_rank = min(ds.RANK_TAKE_PROBABILITY.keys())
        best_prob = ds._take_probability(best_rank, is_run_position=False)
        floor_prob = ds._take_probability(best_rank + 1000, is_run_position=False)
        self.assertLessEqual(floor_prob, best_prob)
        self.assertEqual(floor_prob, ds.RANK_TAKE_PROBABILITY_FLOOR)


if __name__ == "__main__":
    unittest.main()
