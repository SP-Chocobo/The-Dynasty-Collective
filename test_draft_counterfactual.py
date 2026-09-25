"""draft_counterfactual is measurement, never judgment -- these tests pin that it correctly
reconstructs historical state (never replaying/mutating the source trajectory), that BPA is
computed off the FULL undrafted board (not narrow_candidates' narrowed shortlist, which can
omit the true UV-argmax), that ADP is honestly reported unavailable for a 1QB league rather
than approximated, and that repeated runs against the same trajectory are deterministic.
"""

import copy
import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import draft_counterfactual as dc
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

    def test_the_engine_is_the_tav_argmax_again(self):
        """This asserted regret >= 0 before the ordering repair, went routinely negative under
        it, and is restored with the revert (#22).

        MEASURED, NOT ASSUMED: on these fixtures no pick gives up tav at all. Two things could
        legitimately break it, and they are named so a future failure is diagnosable rather
        than mysterious -- (1) `_board_order` leads with the feasibility backstop, so a roster
        with as few picks left as it has unfillable named slots takes a lower-tav player on
        purpose; (2) `narrow_candidates` admits a top-N by tav, so a BPA argmax that falls
        outside it is not a candidate at all. Either turns this into a conditional, not a
        defect. What must never come back is a negative population produced by the ORDER.
        """
        # A node whose engine pick carried no price has NO regret to check (`#187`), so it is
        # skipped -- and the population is asserted non-empty afterwards, because a guard that
        # skipped everything would turn this test green by measuring nothing.
        checked = 0
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if cmp_.regret_vs_bpa is None:
                continue
            checked += 1
            self.assertGreaterEqual(
                cmp_.regret_vs_bpa, -1e-6,
                f"pick {cmp_.pick_no} gave up {-cmp_.regret_vs_bpa:.2f} tav -- see this test's "
                "docstring for the two legitimate causes before reading it as a regression")
        self.assertEqual(checked, len(self.comparisons_1qb) + len(self.comparisons_sf),
                         "these fixtures have no unpriced engine picks, so every node must have "
                         "been checked -- a skip here means the fixture changed, not that the "
                         "invariant holds")

    def test_nothing_deviates_silently(self):
        """The invariant that survives whichever way the sign goes: a pick that is not the BPA
        argmax must carry a basis naming what decided it. Held unconditionally, so it does not
        become vacuous if the population above ever empties."""
        for cmp_ in self.comparisons_1qb + self.comparisons_sf:
            if not cmp_.equals_bpa:
                self.assertIsNotNone(
                    cmp_.deviation_support_basis,
                    f"pick {cmp_.pick_no} is not the BPA argmax and says nothing about why")
                self.assertIn(cmp_.deviation_support_basis, dc.DEVIATION_BASES)

    def test_that_the_deviation_population_is_not_empty(self):
        """NON-VACUITY for the test above, which is trivially true if the engine never leaves
        BPA. It does: the team-specific terms move the tav argmax off the BPA argmax."""
        deviations = [c for c in self.comparisons_1qb + self.comparisons_sf
                      if not c.equals_bpa]
        self.assertGreater(len(deviations), 0,
                           "no pick deviates from BPA -- the assertion above proves nothing")

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

    def test_the_ordering_key_basis_is_gone_with_the_ordering_it_described(self):
        """It was added at #52 and removed at #22 with the sort it excused.

        While build_snapshot ordered on acting_now_value, a measured value there was a real
        basis: the key was live and had ranked the chosen player first. That ordering lost
        6.090% of starting-lineup points against a fixed field and was reverted, so the basis
        now names a mechanism the engine does not have. Removed rather than left returning
        False, because an unused basis is an invitation to wire it back up.
        """
        self.assertNotIn("ordering_key", dc.DEVIATION_BASES)
        # It cannot be reached by passing the number either -- the parameter is gone, so a
        # caller that still supplies it fails loudly instead of being silently ignored.
        with self.assertRaises(TypeError):
            classify_deviation("PREFERRED", False, 7.46)

    def test_an_ordinary_deviation_still_needs_a_basis(self):
        """Non-BPA picks did not stop at the revert, and the reason is not the ordering key.

        The board ranks on team_acquisition_value, which is BPA plus the team-specific terms,
        so the tav argmax and the BPA argmax differ whenever those terms differ across the head
        of the board. That deviation is ordinary and still has to be explained by necessity, a
        near tie, or neither -- never laundered into support by a fourth thing.
        """
        self.assertEqual(classify_deviation("PREFERRED", False), (False, "neither"))
        self.assertEqual(classify_deviation("PREFERRED", None), (None, "unmeasurable_tie"))

    def test_every_basis_the_classifier_can_return_is_in_the_published_vocabulary(self):
        produced = {classify_deviation(n, t)[1]
                    for n in ("MUST TAKE", "PREFERRED")
                    for t in (True, False, None)}
        self.assertTrue(produced <= set(dc.DEVIATION_BASES), produced - set(dc.DEVIATION_BASES))
        # Non-vacuity: the sweep must actually reach most of the vocabulary, or a basis could
        # be dropped from the classifier without this noticing.
        self.assertGreaterEqual(len(produced), 4)

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
                    # Read from the module, never restated here -- a private copy of this
                    # vocabulary is what made this test fail on a correct verdict once (#126).
                    self.assertIn(c.deviation_support_basis, dc.DEVIATION_BASES)
                    if c.deviation_support_basis in dc.DEVIATION_BASES_WITHOUT_VERDICT:
                        self.assertIsNone(c.deviation_supported)
                    else:
                        self.assertIn(c.deviation_supported, (True, False))



class AnUnpricedENGINEPickIsMeasuredAsAbsentNotAsZeroTests(unittest.TestCase):
    """`#187` at the one boundary on this path that never got the treatment.

    `_near_tie` already answers `None` for a candidate whose `tav` is None, and this file already
    pins that in three tests. `regret_vs_bpa` did not: it was `round(engine_tav - bpa_tav, 3)`
    with both fields annotated non-Optional `float`, so an unpriced ENGINE pick raised
    `TypeError` and took the whole harness down.

    NOT HYPOTHETICAL. The board legitimately carries unpriced rows -- `bpa_row` has its own
    documented filter for them, and `pick_synthesis._board_order` sorts them last so a sharp
    chair walks past them. An `opponent_noise` arm drawing from its own top-k does not: the
    trajectory that produced `#34` took Jake Haener at 15.08 and Stetson Bennett at 15.10, both
    with `final_score is None`. Running this harness over that trajectory crashed.

    The fix is absence, not a substitute: no engine price means no regret to report. A 0.0 there
    would be the worse failure, because it reads as "the engine gave up nothing" -- a measured
    verdict in the engine's favour, invented out of a missing number."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr",
                                         te_premium=False, dynasty=True)
        pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=2)
        cls.traj = simulate_full_draft(cls.merger, cls.players_db, cls.league, pick_order)

    def _trajectory_with_an_unpriced_engine_pick(self):
        """The same trajectory with the FIRST pick's chosen candidate de-priced, which is exactly
        the shape a noise arm's unpriced take arrives in. A copy -- the class fixture is shared."""
        traj = copy.deepcopy(self.traj)
        rec = traj.picks[0]
        found = [c for c in rec.snapshot["candidates"] if c["id"] == rec.chosen_player_id]
        self.assertTrue(found, "fixture broken: the chosen player is not among his own candidates")
        for cand in found:
            cand["tav"] = None
            cand["uv"] = None
        return traj

    def test_it_does_not_raise(self):
        # The regression itself. Before the guard this was a TypeError out of round().
        comparisons = compare_trajectory(self.merger, self.players_db, self.league,
                                         self._trajectory_with_an_unpriced_engine_pick())
        self.assertEqual(len(comparisons), len(self.traj.picks))

    def test_the_regret_is_absent_rather_than_zero(self):
        comparisons = compare_trajectory(self.merger, self.players_db, self.league,
                                         self._trajectory_with_an_unpriced_engine_pick())
        first = comparisons[0]
        self.assertIsNone(first.engine_tav, "the de-priced pick must carry no tav")
        self.assertIsNone(first.regret_vs_bpa,
                          "no engine price means no regret -- 0.0 would read as 'gave up nothing'")
        self.assertIsNone(first.regret_vs_adp,
                          "the ADP comparison has the same missing left-hand side")

    def test_the_bpa_side_is_still_reported(self):
        """Absence on one side of a difference does not erase what WAS measured. The board still
        had a best available player and his price is still a fact about this node."""
        first = compare_trajectory(self.merger, self.players_db, self.league,
                                   self._trajectory_with_an_unpriced_engine_pick())[0]
        self.assertIsNotNone(first.bpa_player_id)
        self.assertIsInstance(first.bpa_tav, float)

    def test_every_OTHER_node_is_untouched(self):
        """NON-VACUITY, and in the direction that matters: a guard that returned None everywhere
        would pass the three tests above and destroy the instrument."""
        patched = compare_trajectory(self.merger, self.players_db, self.league,
                                     self._trajectory_with_an_unpriced_engine_pick())
        clean = compare_trajectory(self.merger, self.players_db, self.league, self.traj)
        self.assertEqual(len(patched), len(clean))
        measured = [c for c in patched[1:] if c.regret_vs_bpa is not None]
        self.assertTrue(measured, "every node came back absent -- the guard swallowed the run")
        for a, b in zip(patched[1:], clean[1:]):
            self.assertEqual(a.regret_vs_bpa, b.regret_vs_bpa)


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
