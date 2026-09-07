"""draft_counterfactual is measurement, never judgment -- these tests pin that it correctly
reconstructs historical state (never replaying/mutating the source trajectory), that BPA is
computed off the FULL undrafted board (not narrow_candidates' narrowed shortlist, which can
omit the true UV-argmax), that ADP is honestly reported unavailable for a 1QB league rather
than approximated, and that repeated runs against the same trajectory are deterministic.
"""

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_counterfactual import (
    _SUPPORTED_NECESSITY_LABELS, _near_tie, bpa_row, classify_deviation,
    compare_trajectory)
from draft_simulation import simulate_full_draft


def _build_pool_players_db(positions=("QB", "RB", "WR", "TE")):
    merger = dm.DataMerger()
    proj = merger.projections
    players_db = {}
    pid = 0
    for pos in positions:
        sub = proj[proj["position"] == pos].sort_values("trade_value", ascending=False)
        for _, row in sub.iterrows():
            pid += 1
            parts = row["norm_name"].split()
            players_db[str(pid)] = {
                "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
            }
    return merger, players_db


class CompareTrajectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league_1qb = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        cls.league_sf = dr.build_mock_league(teams=4, superflex=True, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=2)  # 8 picks
        cls.traj_1qb = simulate_full_draft(cls.merger, cls.players_db, cls.league_1qb, pick_order)
        cls.traj_sf = simulate_full_draft(cls.merger, cls.players_db, cls.league_sf, pick_order)
        cls.comparisons_1qb = compare_trajectory(cls.merger, cls.players_db, cls.league_1qb, cls.traj_1qb)
        cls.comparisons_sf = compare_trajectory(cls.merger, cls.players_db, cls.league_sf, cls.traj_sf)

    def test_one_comparison_per_pick(self):
        self.assertEqual(len(self.comparisons_1qb), len(self.traj_1qb.picks))

    def test_engine_player_matches_the_trajectorys_own_recorded_choice(self):
        for cmp_, rec in zip(self.comparisons_1qb, self.traj_1qb.picks):
            self.assertEqual(cmp_.engine_player_id, rec.chosen_player_id)
            self.assertEqual(cmp_.pick_no, rec.pick_no)
            self.assertEqual(cmp_.roster_id, rec.roster_id)

    def test_regret_vs_bpa_is_never_negative(self):
        # The engine always takes the TAV-argmax on its own board -- by construction, its TAV
        # can never be lower than the BPA player's TAV on that same board.
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            self.assertGreaterEqual(cmp_.regret_vs_bpa, -1e-6)

    def test_equals_bpa_implies_zero_regret(self):
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if cmp_.equals_bpa:
                self.assertAlmostEqual(cmp_.regret_vs_bpa, 0.0, places=2)

    def test_deviation_supported_is_none_only_when_equals_bpa(self):
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if cmp_.equals_bpa:
                self.assertIsNone(cmp_.deviation_supported)
            else:
                self.assertIn(cmp_.deviation_supported, (True, False))

    def test_adp_unavailable_for_1qb_league_with_a_stated_reason(self):
        # The real, honest limitation: no KTC consensus is loaded for a 1QB league by design.
        for cmp_ in self.comparisons_1qb:
            self.assertFalse(cmp_.adp_available)
            self.assertIsNone(cmp_.adp_player_id)
            self.assertIsNone(cmp_.equals_adp)
            self.assertIsNotNone(cmp_.adp_unavailable_reason)

    def test_bpa_is_uv_argmax_not_tav_argmax_on_a_synthetic_board(self):
        # Direct, deterministic proof of the property this module depends on -- doesn't rely on
        # a real draft happening to produce a case where UV-argmax and TAV-argmax diverge (the
        # small fixture used elsewhere in this file usually doesn't hit one).
        board = [
            {"player_id": "1", "name": "High UV, suppressed TAV", "universal_value": 99.0, "final_score": 10.0, "position": "RB"},
            {"player_id": "2", "name": "Lower UV, high TAV (need-boosted)", "universal_value": 50.0, "final_score": 90.0, "position": "WR"},
        ]
        self.assertEqual(bpa_row(board)["player_id"], "1")

    def test_an_unpriced_row_is_excluded_from_bpa_rather_than_killing_the_harness(self):
        """#61 invariant 15, REPAIRED at #193 -- and this test inverted, as its own previous
        version required.

        It used to assert the opposite: that bpa_row raised TypeError on any board carrying an
        unpriced row, pinned as a REACHABILITY FACT rather than as approval. That fact was what
        made the known limit recorded on _near_tie a limit rather than a live defect -- the
        harness could not reach a board on which an unknown near-tie existed, so repairing the
        false negative first would have been building for an unreachable state. The stated
        order was: invariant 15, then _near_tie.

        #193 forced invariant 15 to the front of that queue. Admission stopped requiring that
        someone had published a number, so unpriced rows became routine rather than a
        late-round curiosity, and the crash stopped being a theoretical guard and started
        killing this harness on ordinary boards. bpa_row now EXCLUDES unpriced rows from the
        argmax -- an unpriced player is not the best player available in any sense -- and
        returns None when nothing on the board is priced, which compare_trajectory treats as a
        node with no ruler and skips.

        The second half of the order is now UNBLOCKED and NOT DONE: see _near_tie's docstring,
        which no longer has an unreachability argument behind it."""
        mixed = [
            {"player_id": "1", "name": "Priced", "universal_value": 99.0, "final_score": 99.0, "position": "RB"},
            {"player_id": "2", "name": "Unpriced", "universal_value": None, "final_score": None, "position": "K"},
        ]
        self.assertEqual(bpa_row(mixed)["player_id"], "1")
        # ...and the unpriced row does not win merely by being the only survivor of a filter.
        self.assertIsNone(bpa_row([dict(mixed[1], player_id="3"), mixed[1]]))
        # A higher-valued priced row still wins on the merits, so the filter has not become the
        # whole decision.
        self.assertEqual(
            bpa_row(mixed + [dict(mixed[0], player_id="4", universal_value=120.0)])["player_id"],
            "4")


    def test_a_flagged_tie_reads_true(self):
        cands = [{"id": "1", "forces": ["tie"], "tav": 50.0}]
        self.assertIs(_near_tie(cands, "1"), True)

    def test_an_unflagged_but_PRICED_candidate_reads_a_measured_false(self):
        # He had a team_acquisition_value, so near_tie_flags DID compare him to the leader and
        # answered no. That is a measurement, and reporting it as False is correct.
        cands = [{"id": "1", "forces": ["cliff"], "tav": 50.0}]
        self.assertIs(_near_tie(cands, "1"), False)

    def test_an_unflagged_and_UNPRICED_candidate_reads_unknown(self):
        # near_tie_flags returns None for exactly one reason: an entry whose tav is None. The
        # forces list cannot show the difference (it lists what fired), so the payload's own
        # tav is what recovers it. This is the false negative #61 rule 5 exists to stop.
        cands = [{"id": "1", "forces": ["cliff"], "tav": None}]
        self.assertIsNone(_near_tie(cands, "1"))

    def test_a_candidate_this_harness_cannot_find_reads_unknown(self):
        self.assertIsNone(_near_tie([{"id": "other", "forces": [], "tav": 9.0}], "1"))

    def test_determinism_repeated_comparison_is_identical(self):
        again = compare_trajectory(self.merger, self.players_db, self.league_1qb, self.traj_1qb)
        for a, b in zip(self.comparisons_1qb, again):
            self.assertEqual(a, b)


class DeviationSupportCarriesItsBasisTests(unittest.TestCase):
    """deviation_supported's None now covers two different situations, so it travels with a
    companion that says which. Conflating "the engine took BPA, nothing to classify" with "the
    engine deviated and this harness could not tell" would let a consumer count the second as
    the first, or worse report it as unsupported."""

    def test_each_input_state_produces_a_DIFFERENT_verdict_and_basis(self):
        """Calls the production classifier. The previous version of this test reimplemented the
        branch inside the test body and therefore asserted nothing about the code -- a mutation
        that made an unmeasurable tie report "unsupported" passed it untouched (#195)."""
        cases = {
            ("MUST TAKE", False): (True, "necessity"),
            ("STRONG ACTION", None): (True, "necessity"),   # necessity wins before the tie is read
            ("PREFERRED", True): (True, "near_tie"),
            ("PREFERRED", None): (None, "unmeasurable_tie"),
            ("PREFERRED", False): (False, "neither"),
        }
        for (necessity, tie), expected in cases.items():
            with self.subTest(necessity=necessity, near_tie=tie):
                self.assertEqual(classify_deviation(necessity, tie), expected)
        # The two Nones in the value space are told apart by the basis, never by the value.
        self.assertEqual(len({b for _, b in cases.values()}), 4)

    def test_an_unmeasurable_tie_is_not_reported_as_unsupported(self):
        """The whole point. False would assert the engine deviated without support on the
        strength of a comparison nobody made."""
        # The classifier's own contract is pinned above. This is the WIRING check: the pair
        # actually reaches NodeComparison intact on a real draft, and no row carries a verdict
        # its basis cannot account for. It deliberately does NOT claim the fixture reaches the
        # unmeasurable branch -- whether it does is a property of the data, not of the code, and
        # asserting it here is what made the earlier version vacuous.
        merger, players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr",
                                      te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=2)
        traj = simulate_full_draft(merger, players_db, league, pick_order)
        comparisons = compare_trajectory(merger, players_db, league, traj)
        self.assertTrue(comparisons, "vacuous: no comparisons produced")
        for c in comparisons:
            with self.subTest(pick=c.pick_no):
                if c.equals_bpa:
                    self.assertIsNone(c.deviation_supported)
                    self.assertIsNone(c.deviation_support_basis)
                else:
                    self.assertIn(c.deviation_support_basis,
                                  ("necessity", "near_tie", "neither", "unmeasurable_tie"))
                    if c.deviation_support_basis == "unmeasurable_tie":
                        self.assertIsNone(c.deviation_supported)
                    else:
                        self.assertIn(c.deviation_supported, (True, False))



class NoMutationTests(unittest.TestCase):
    def test_does_not_mutate_the_trajectory_or_its_inputs(self):
        merger, players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=1)
        traj = simulate_full_draft(merger, players_db, league, pick_order)
        picks_before = tuple(traj.picks)
        league_before = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in league.items()}
        players_db_before = {k: dict(v) for k, v in players_db.items()}

        compare_trajectory(merger, players_db, league, traj)

        self.assertEqual(traj.picks, picks_before)
        self.assertEqual(league, league_before)
        self.assertEqual(players_db, players_db_before)


if __name__ == "__main__":
    unittest.main()
