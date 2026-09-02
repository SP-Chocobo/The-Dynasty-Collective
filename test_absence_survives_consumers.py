"""D4 -- absence must survive every consumer of the board.

compute_draft_board normalizes an unpriced row's bpa / universal_value / final_score to None
(_records_with_normalized_nan). That is the contract this codebase chose deliberately, and it is
the right one: a row whose position has no replacement level has no value, and writing 0.0 there
would rank it exactly where "worth nothing" ranks, which is a claim rather than an absence.

The contract stopped at the board. Every consumer downstream then did arithmetic or ordering on
the field directly, so the moment a real board contained an unpriced row the strategic layer
raised TypeError -- not a wrong number, a hard crash, at the app's own entry point.

MEASURED, on a real 12-team dynasty startup: unpriced rows first appear at round 15, and from
that round on `pick_synthesis.build_snapshot` -- what the Draft Room calls to build the debate
dock -- raised

    TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'

from draft_strategy.pick_analysis's `curve.sort(reverse=True)`. That is the last quarter of
every 20-round draft.

THE RULE, and it is not invented here -- all three halves of it already had precedent in this
codebase before this file existed:

  1. EXCLUDE. A row with no value is left out of a computation defined over values (a curve, a
     maximum, a margin, a gap distribution). Being excluded is not the same as scoring low.
  2. PROPAGATE. A quantity derived from an absent input is itself absent.
     `expected_value_of_waiting` already returns None when survival is absent; this applies the
     same rule to its other operand.
  3. ORDER LAST. An ordering places absent rows last, deterministically, and never compares
     them as numbers -- exactly what pick_synthesis._board_order already does for the board.

No consumer substitutes a number for absence. The one place a neutral number IS used --
compute_pick_necessity's standout component -- is documented at its test below, and follows the
rule that function already applies three times over for its own absent inputs.
"""
import math
import inspect
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps


ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"] + ["BN"] * 11
NUM_TEAMS = 12
DYNASTY = {"roster_positions": ROSTER, "total_rosters": NUM_TEAMS,
           "settings": {"type": 2}, "scoring_settings": {}}
# LateBoardIntegrationTests runs SUPERFLEX. Since predraft_replacement_anchor landed, a
# position whose league-wide starter demand is exhausted keeps being priced against its
# pre-draft level, so a 1QB board carries no unpriced row at ANY depth (measured: 0 at rounds
# 16/18/20) and this file's whole subject becomes unreachable there. The one absence the
# repair deliberately does NOT revive is the startable_floors decline -- "no remaining QB
# clears the startability threshold", which is a different fact from "demand is filled" --
# and that is reachable only in superflex (11 unpriced QBs at round 16).
SUPERFLEX_ROSTER = (
    ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"] + ["BN"] * 10
)
DYNASTY_SUPERFLEX = {"roster_positions": SUPERFLEX_ROSTER, "total_rosters": NUM_TEAMS,
                     "settings": {"type": 2}, "scoring_settings": {}}
ROSTER_IDS = [str(i) for i in range(1, NUM_TEAMS + 1)]


def _row(player_id, position, value, name=None):
    """A board row shaped the way compute_draft_board emits one. value=None is an unpriced row:
    bpa, universal_value and final_score all absent together, which is how the board writes it."""
    return {
        "player_id": str(player_id), "name": name or f"P{player_id}", "position": position,
        "team": "XX", "bpa": value, "universal_value": value, "final_score": value,
        "need_bonus": 0.0, "eligibility_bonus": 0.0, "projected_points": 100.0,
    }


# --------------------------------------------------------------- unit-level, hand-built --

class PositionCurveExcludesUnpricedTests(unittest.TestCase):
    """Rule 1. pick_analysis walks each position's remaining value curve to size the cost of
    delaying that position. A row with no value has no place on a value curve -- and sorting a
    list containing None is the crash itself."""

    def test_a_curve_built_from_a_mixed_board_sorts(self):
        board = {"1": _row(1, "RB", 50.0), "2": _row(2, "RB", None), "3": _row(3, "RB", 10.0)}
        curves = ds._position_curves(board)
        self.assertEqual(curves["RB"], [50.0, 10.0])

    def test_a_position_with_nothing_priced_yields_no_curve_rather_than_an_empty_lie(self):
        board = {"1": _row(1, "K", None), "2": _row(2, "K", None)}
        curves = ds._position_curves(board)
        self.assertNotIn("K", curves)


class OpportunityCostPropagatesAbsenceTests(unittest.TestCase):
    """Rule 2. "What do I lose by waiting" is team_acquisition_value x (1 - survival). With no
    acquisition value there is no loss to state, and 0.0 would claim there is none."""

    def test_absent_value_gives_absent_cost(self):
        self.assertIsNone(ds._opportunity_cost(None, 0.5))

    def test_a_real_value_is_unchanged(self):
        self.assertEqual(ds._opportunity_cost(100.0, 0.25), 75.0)

    def test_absent_survival_also_gives_absent_cost(self):
        self.assertIsNone(ds._opportunity_cost(100.0, None))


class ExpectedValueOfWaitingPropagatesBothOperandsTests(unittest.TestCase):
    """Rule 2, symmetry. This function already returned None for an absent survival; it must do
    the same for an absent universal_value rather than raising on the multiply."""

    def test_absent_survival_still_returns_none(self):
        self.assertIsNone(ps.expected_value_of_waiting(100.0, None))

    def test_absent_universal_value_returns_none(self):
        self.assertIsNone(ps.expected_value_of_waiting(None, 0.5))

    def test_both_present_is_unchanged(self):
        self.assertEqual(ps.expected_value_of_waiting(100.0, 0.5), 50.0)


class NearTieFlagsSayUnknownTests(unittest.TestCase):
    """Rule 1 + rule 3, and #61 RULE 5, which INVERTS the four assertions this class first made.

    The original rule was right about the mechanics and wrong about the answer. A row with no
    value must not join the band and must not become the leader -- that stands. But it used to
    come back False, and `False` here is a claim with a measurement behind it: "compared to the
    leader, not close to him". The board never made that comparison.

    near_tie_flags' own docstring refuses to flag a lone leader because that would hand the
    debate layer a false "these are tied". Handing it a false "these are NOT tied" is the same
    argument, and it was being applied in one direction only. Three states now: True / False /
    None."""

    def test_an_absent_entry_is_unknown_not_negative(self):
        flags = ps.near_tie_flags([100.0, None, 99.5])
        self.assertEqual(flags, [True, None, True])
        self.assertIsNone(flags[1], "None, not False -- the comparison was never made")

    def test_absence_cannot_become_the_leader(self):
        # max() over a list containing None used to raise; a None that sorted first would also
        # silently make every real row look far behind the "leader".
        flags = ps.near_tie_flags([None, 100.0, 99.5])
        self.assertEqual(flags, [None, True, True])

    def test_an_all_absent_field_answers_nothing_rather_than_answering_no(self):
        self.assertEqual(ps.near_tie_flags([None, None, None]), [None, None, None])

    def test_a_lone_priced_row_among_absent_ones_keeps_both_states_apart(self):
        """The collapse branch (fewer than two in band) is where the two states are easiest to
        conflate, because it returns a uniform list. The priced row really was measured and
        really is in no tie group -- that is False. The unpriced ones stay unknown."""
        flags = ps.near_tie_flags([100.0, None, None])
        self.assertEqual(flags, [False, None, None])
        self.assertIs(flags[0], False)
        self.assertIsNone(flags[1])

    def test_the_priced_only_behaviour_is_unchanged(self):
        self.assertEqual(ps.near_tie_flags([100.0, 99.5, 50.0]), [True, True, False])
        self.assertEqual(ps.near_tie_flags([100.0, 50.0]), [False, False])
        self.assertEqual(ps.near_tie_flags([]), [])

    def test_no_priced_row_ever_comes_back_unknown(self):
        """The converse of the rule, so the widening cannot be satisfied by returning None
        everywhere: a row that HAS a value always gets a real answer."""
        for values in ([100.0, 99.5, 50.0], [100.0, None, 99.5], [100.0, None, None],
                       [100.0, 50.0], [None, 100.0, 99.5]):
            for value, flag in zip(values, ps.near_tie_flags(values)):
                with self.subTest(values=values, value=value):
                    self.assertEqual(flag is None, value is None)


class DecisionRegimeExcludesUnpricedTests(unittest.TestCase):
    """Rule 1. The regime is decided by the margin between the best and second-best candidate.
    An unpriced candidate is neither, and the function's own rule for a field with fewer than
    two measurable members already exists: "contested"."""

    def _c(self, tav, survival=0.0):
        return {"team_acquisition_value": tav, "survival_probability": survival}

    def test_a_decisive_field_stays_decisive_when_an_unpriced_row_is_added(self):
        priced = [self._c(200.0), self._c(100.0)]
        self.assertEqual(ps.decision_regime(priced), "decisive")
        self.assertEqual(ps.decision_regime(priced + [self._c(None)]), "decisive")

    def test_one_priced_candidate_among_unpriced_ones_is_contested(self):
        self.assertEqual(ps.decision_regime([self._c(200.0), self._c(None), self._c(None)]),
                         "contested")

    def test_an_all_unpriced_field_is_contested(self):
        self.assertEqual(ps.decision_regime([self._c(None), self._c(None)]), "contested")

    def test_decisive_is_read_off_a_measured_false_and_never_off_an_unknown(self):
        """#61 invariant 8, made structural by rule 5. decision_regime asks near_tie_flags for
        the leader's flag; it must test that flag for a measured False, not merely for
        falsiness, or an UNKNOWN margin would produce "decisive" -- the one verdict this
        function is not allowed to reach without a measurement.

        The guard is unreachable through decision_regime's public path today (it ranks the
        priced rows only, so the leader always has a value), which is exactly why it is pinned
        here at the seam rather than left to a future caller to rediscover."""
        source = inspect.getsource(ps.decision_regime)
        self.assertIn("leader_in_tie_group is False", source)
        self.assertNotIn("not leader_in_tie_group", source)
        # And the behaviour the guard protects, driven directly.
        self.assertEqual(ps.decision_regime([self._c(200.0), self._c(100.0)]), "decisive")


class NecessityExcludesUnpricedFromTheFieldTests(unittest.TestCase):
    """Rule 1 for the comparison, and the function's own existing rule for the candidate.

    The standout component asks "how far ahead of the rest of the field is he". Rows with no
    value are not part of that field and must not enter max(others).

    For a candidate who is HIMSELF unpriced, his standout component is the neutral 0.0 -- and
    that is not a number substituted for absence. This function already assigns exactly 0.0 for
    an absent survival, an absent cliff and an absent rival premium, and its own docstring
    argues the standout floor is neutral ("not the single best option on the board right now is
    neutral, not itself evidence of low urgency"). His survival, cliff and run components are
    still real evidence, and reporting urgency from the evidence that exists -- with the
    unmeasurable term neutral -- is what the function already does everywhere else."""

    def _c(self, tav):
        return {"team_acquisition_value": tav, "need_bonus": 0.0, "eligibility_bonus": 0.0,
                "survival_probability": None, "positional_cliff": None,
                "position_run_detected": False, "rival_premium": 0.0}

    def test_an_unpriced_row_does_not_join_the_field_a_leader_is_measured_against(self):
        without = ps.compute_pick_necessity([self._c(200.0), self._c(100.0)], round_num=1)
        with_absent = ps.compute_pick_necessity(
            [self._c(200.0), self._c(100.0), self._c(None)], round_num=1)
        self.assertEqual(with_absent[0], without[0])
        self.assertEqual(with_absent[1], without[1])

    def test_an_unpriced_candidate_still_gets_a_score_rather_than_raising(self):
        results = ps.compute_pick_necessity([self._c(200.0), self._c(None)], round_num=1)
        self.assertEqual(len(results), 2)
        for score, label in results:
            self.assertIsInstance(score, float)
            self.assertIsInstance(label, str)

    def test_a_sole_unpriced_candidate_does_not_read_as_the_only_option(self):
        # "no alternative exists at all" awards the full standout weight. An unpriced candidate
        # in a field of one is not evidence that he is irreplaceable; it is evidence of nothing.
        alone_priced = ps.compute_pick_necessity([self._c(200.0)], round_num=1)[0][0]
        alone_absent = ps.compute_pick_necessity([self._c(None)], round_num=1)[0][0]
        self.assertLess(alone_absent, alone_priced)


class PositionalCliffExcludesUnpricedTests(unittest.TestCase):
    """Rule 1. The cliff is a drop measured in bpa against that position's own gap
    distribution. Rows with no bpa are not in the distribution."""

    def _board(self):
        rows = [_row(i, "WR", float(100 - i * 5)) for i in range(1, 8)]
        rows += [_row(50 + i, "WR", None) for i in range(3)]
        return rows

    def test_a_mixed_position_still_produces_a_cliff_reading(self):
        result = ps.detect_positional_cliff(self._board(), "2")
        self.assertIsNotNone(result)
        self.assertIn(result["tier"], ("HIGH", "MEDIUM", "LOW"))

    def test_an_unpriced_target_has_no_cliff_question_to_answer(self):
        self.assertIsNone(ps.detect_positional_cliff(self._board(), "50"))


class OrderingPlacesAbsenceLastTests(unittest.TestCase):
    """Rule 3, and determinism with it. Ordering must never compare absence as a number, and
    two runs over differently-ordered input must agree."""

    def test_opportunity_cost_ordering_puts_absent_rows_last(self):
        rows = [{"player_id": "a", "opportunity_cost": None},
                {"player_id": "b", "opportunity_cost": 10.0},
                {"player_id": "c", "opportunity_cost": None},
                {"player_id": "d", "opportunity_cost": 50.0}]
        ordered = sorted(rows, key=ds._opportunity_cost_order)
        self.assertEqual([r["player_id"] for r in ordered], ["d", "b", "a", "c"])

    def test_the_ordering_does_not_depend_on_input_order(self):
        rows = [{"player_id": "a", "opportunity_cost": None},
                {"player_id": "b", "opportunity_cost": 10.0},
                {"player_id": "c", "opportunity_cost": None},
                {"player_id": "d", "opportunity_cost": 50.0}]
        forward = [r["player_id"] for r in sorted(rows, key=ds._opportunity_cost_order)]
        backward = [r["player_id"] for r in sorted(list(reversed(rows)),
                                                   key=ds._opportunity_cost_order)]
        self.assertEqual(forward, backward)


# ------------------------------------------------------------------ real-board integration --

class LateBoardIntegrationTests(unittest.TestCase):
    """The regression that matters: the real pipeline, at the real board states where this
    crashed. Rounds are chosen from the measurement -- unpriced rows appear at 15."""

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
                                             league=DYNASTY_SUPERFLEX, mode="balanced")
        cls.pick_order = ds.generate_pick_order(ROSTER_IDS, 22, "snake")

    def _state(self, rounds):
        taken = rounds * NUM_TEAMS
        picks = [{"player_id": r["player_id"], "roster_id": str((i % NUM_TEAMS) + 1),
                  "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                 for i, r in enumerate(self.opening[:taken])]
        board = dr.compute_draft_board(self.merger, self.players_db, picks, my_roster_id="1",
                                       league=DYNASTY_SUPERFLEX, mode="balanced")
        index = next(i for i in range(taken, len(self.pick_order))
                     if self.pick_order[i] == "1")
        return picks, board, index

    def test_the_fixture_reaches_a_board_that_cannot_price_everything(self):
        for rounds in (15, 16, 18):
            _, board, _ = self._state(rounds)
            unpriced = [r for r in board if r.get("final_score") is None]
            self.assertTrue(unpriced, f"round {rounds} produced no unpriced rows")

    def test_build_snapshot_survives_every_late_round(self):
        for rounds in (14, 15, 16, 18, 20):
            picks, board, index = self._state(rounds)
            if not board:
                continue
            snapshot = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order,
                                         index, "1", DYNASTY_SUPERFLEX, pick_label=f"R{rounds + 1}")
            self.assertTrue(snapshot.candidates, f"round {rounds} produced no candidates")

    def test_the_unknown_near_tie_state_is_reachable_on_a_real_board(self):
        """NON-VACUITY for #61 rule 5. The three-state widening is pinned by unit inputs
        elsewhere in this file; those prove near_tie_flags computes it, not that anything ever
        produces it. This drives the whole path -- real merger, real board, real narrowing --
        and fails if the late-round snapshots the rule was written for never actually carry a
        candidate whose tie comparison could not be made.

        If this ever goes quiet (an anchor repair prices the whole tail, say), the rule has lost
        its population and that is a finding about the rule, not a test to relax. Re-scope it
        the way #61 itself was re-scoped rather than deleting the check."""
        unknown_rounds, priced_seen = [], False
        for rounds in (15, 16, 18):
            picks, board, index = self._state(rounds)
            if not board:
                continue
            snapshot = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order,
                                         index, "1", DYNASTY_SUPERFLEX, pick_label=f"R{rounds + 1}")
            flags = [c.near_tie_with_leader for c in snapshot.candidates]
            if any(f is None for f in flags):
                unknown_rounds.append(rounds)
            priced_seen = priced_seen or any(f is not None for f in flags)
            # And the state always tracks pricing, on a real board and not just a synthetic list.
            for candidate in snapshot.candidates:
                self.assertEqual(candidate.near_tie_with_leader is None,
                                 candidate.team_acquisition_value is None,
                                 f"{candidate.name}: unknown-ness and unpriced-ness disagree")
        self.assertTrue(unknown_rounds,
                        "no real late-round snapshot carried an unknown near-tie -- rule 5 has "
                        "no population here; re-scope it rather than relaxing this")
        self.assertTrue(priced_seen, "every flag was unknown -- the fixture proves nothing")

    def test_pick_analysis_survives_unpriced_candidates(self):
        picks, board, index = self._state(16)
        priced = [r for r in board if r.get("final_score") is not None]
        unpriced = [r for r in board if r.get("final_score") is None]
        self.assertTrue(priced and unpriced)
        candidates = [priced[0]["player_id"], unpriced[0]["player_id"],
                      unpriced[len(unpriced) // 2]["player_id"]]
        results = ds.pick_analysis(self.merger, self.players_db, picks, self.pick_order, index,
                                   "1", DYNASTY_SUPERFLEX, candidates, mode="balanced")
        self.assertEqual(len(results), 3)
        by_id = {r["player_id"]: r for r in results}
        self.assertIsNone(by_id[unpriced[0]["player_id"]]["opportunity_cost"],
                          "an unpriced candidate was given a cost of waiting")
        self.assertIsNotNone(by_id[priced[0]["player_id"]]["opportunity_cost"])

    def test_an_unpriced_candidate_never_outranks_a_priced_one_in_the_analysis(self):
        picks, board, index = self._state(16)
        priced = [r for r in board if r.get("final_score") is not None]
        unpriced = [r for r in board if r.get("final_score") is None]
        candidates = [unpriced[0]["player_id"], priced[0]["player_id"]]
        results = ds.pick_analysis(self.merger, self.players_db, picks, self.pick_order, index,
                                   "1", DYNASTY_SUPERFLEX, candidates, mode="balanced")
        self.assertEqual(results[0]["player_id"], priced[0]["player_id"])

    def test_a_candidate_no_opponent_can_price_carries_no_rival_premium(self):
        # The other side of the denial loop, and a branch an assertion-reachability trace found
        # unexercised anywhere in the suite: pick_analysis's `rival_premium_take_probability`
        # is None when no intervening opponent's board yields a positive premium. An unpriced
        # candidate reaches that state for the honest reason -- no opponent board can price
        # him, so none of them is skipped for having a premium of zero, they are skipped for
        # having no value to take a premium over.
        picks, board, index = self._state(16)
        unpriced = [r for r in board if r.get("final_score") is None]
        self.assertTrue(unpriced)
        results = ds.pick_analysis(self.merger, self.players_db, picks, self.pick_order, index,
                                   "1", DYNASTY_SUPERFLEX, [unpriced[0]["player_id"]], mode="balanced")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["rival_premium"], 0.0)
        self.assertIsNone(results[0]["rival_premium_take_probability"])
        self.assertEqual(results[0]["denial_value"], 0.0)

    def test_the_snapshot_is_identical_across_repeated_builds(self):
        picks, board, index = self._state(16)
        first = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order, index,
                                  "1", DYNASTY_SUPERFLEX, pick_label="R17")
        second = ps.build_snapshot(self.merger, self.players_db, picks, self.pick_order, index,
                                   "1", DYNASTY_SUPERFLEX, pick_label="R17")
        self.assertEqual([c.player_id for c in first.candidates],
                         [c.player_id for c in second.candidates])


if __name__ == "__main__":
    unittest.main()
