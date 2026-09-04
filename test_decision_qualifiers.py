"""#138's second half: the two quantities that were computed, carried, and dropped.

`replacement_basis` and `growth_signal` were both produced by compute_draft_board, placed on
every board row, and then discarded at pick_synthesis's `raw_candidates` boundary -- so no
consumer could read them however much it wanted to. quantity_readers.py found them; this file
holds the repair.

The scanner proves a READER EXISTS. It cannot prove the value that arrives is the right one,
and those are different claims -- a carry that always delivered None would satisfy the scanner
and tell a reader nothing. So everything here is behavioural, against real boards.

WHY THESE TWO ARE WORTH CARRYING, measured rather than asserted:
  replacement_basis -- "live_starter_demand" vs "predraft_anchor" are two different STRENGTHS
    of claim about the same number. Once a position's league-wide starter demand is exhausted
    it keeps being priced against its PRE-DRAFT level, and a consumer that renders both
    identically states a live measurement it does not have.
  growth_signal -- upside mode's whole distinguishing output: final_score = bpa +
    UPSIDE_GROWTH_WEIGHT * growth. On real upside boards 43-52% of rows carry growth > 0
    (mean 11.1 early, 25.5 once the pool drains), and by round 15 it changes which player is
    taken. Without it a retained record says who was chosen but not on what kind of evidence.
"""

import unittest

import data_merger as dm
import draft_board_ui
import draft_room as dr
import draft_simulation
import draft_strategy as ds
import pick_synthesis as ps

NUM_TEAMS = 12
LEAGUE = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                               "BN", "BN", "BN", "BN", "BN"],
          "total_rosters": NUM_TEAMS, "settings": {"type": 2}, "scoring_settings": {}}


def _players_db(merger, positions=("QB", "RB", "WR", "TE")):
    proj = merger.projections
    out, pid = {}, 0
    for position in positions:
        for _, row in proj[proj["position"] == position].sort_values(
                "trade_value", ascending=False).iterrows():
            pid += 1
            parts = str(row["norm_name"]).split()
            out[str(pid)] = {"first_name": parts[0].upper(),
                             "last_name": " ".join(parts[1:]).title(),
                             "position": position, "fantasy_positions": [position],
                             "team": row.get("team")}
    return out


class _RealSnapshots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _players_db(cls.merger)
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, NUM_TEAMS + 1)], 20, "snake")
        cls.opening = dr.compute_draft_board(
            cls.merger, cls.players_db, [], my_roster_id="1", league=LEAGUE, mode="balanced")

    @classmethod
    def _snapshot(cls, taken, mode):
        picks = [{"player_id": r["player_id"], "roster_id": cls.pick_order[i],
                  "round": (i // NUM_TEAMS) + 1, "pick_no": i + 1}
                 for i, r in enumerate(cls.opening[:taken])]
        return ps.build_snapshot(
            cls.merger, cls.players_db, picks, cls.pick_order, taken,
            cls.pick_order[taken], LEAGUE, pick_label=f"{mode}-{taken}", mode=mode)


class ReplacementBasisReachesItsConsumersTests(_RealSnapshots):
    def test_every_candidate_carries_a_basis_in_both_modes(self):
        """A qualifier that is present for only some rows cannot be compared across rows, which
        is the one thing a consumer needs it for."""
        for mode in ("balanced", "upside"):
            with self.subTest(mode=mode):
                candidates = self._snapshot(24, mode).candidates
                self.assertTrue(candidates, "no candidates; this test observed nothing")
                missing = [c.name for c in candidates if c.replacement_basis is None]
                self.assertEqual([], missing, f"{len(missing)} candidates carry no basis")

    def test_both_states_are_reachable_through_the_snapshot_layer(self):
        """The board distinguishes the two; the point of carrying the field is that the
        SNAPSHOT distinguishes them too. Measured: predraft_anchor appears once demand is
        drained -- round 15 of this fixture, where one position has run out of live demand."""
        seen = set()
        for taken in (24, 96, 168):
            seen |= {c.replacement_basis for c in self._snapshot(taken, "upside").candidates}
        self.assertIn("live_starter_demand", seen)
        self.assertIn("predraft_anchor", seen,
                      "no candidate was ever priced off the pre-draft anchor, so the "
                      "distinction this field exists to make is untested here")

    def test_the_serializer_emits_it(self):
        candidate = self._snapshot(24, "balanced").candidates[0]
        self.assertEqual(draft_board_ui.serialize_candidate(candidate)["replacementBasis"],
                         candidate.replacement_basis)


class GrowthSignalReachesItsConsumersTests(_RealSnapshots):
    def test_it_is_absent_in_balanced_mode_rather_than_zero(self):
        """The absence contract, at the one boundary where it is easy to get wrong. Balanced
        boards never compute growth, and 0.0 would read as "measured, and this player has no
        trajectory" -- a claim, where there is no measurement at all."""
        for candidate in self._snapshot(24, "balanced").candidates:
            self.assertIsNone(candidate.growth_signal)

    def test_it_is_present_and_discriminating_in_upside_mode(self):
        candidates = self._snapshot(24, "upside").candidates
        values = [c.growth_signal for c in candidates]
        self.assertTrue(all(v is not None for v in values),
                        "upside mode dropped growth_signal for at least one candidate")
        self.assertGreater(len(set(values)), 1,
                           "every upside candidate carries the same growth_signal, so the "
                           "field separates nobody and carrying it buys nothing")

    def test_it_reconstructs_the_upside_score_it_decomposes(self):
        """The strongest available check that the value arriving is the RIGHT one rather than
        merely present: upside mode's own identity is
        final_score = bpa + UPSIDE_GROWTH_WEIGHT * growth_signal, so the carried field has to
        close that equation against the two numbers already on the snapshot."""
        for candidate in self._snapshot(24, "upside").candidates:
            if candidate.bpa is None:
                continue
            with self.subTest(player=candidate.name):
                self.assertAlmostEqual(
                    candidate.team_acquisition_value,
                    round(candidate.bpa + dr.UPSIDE_GROWTH_WEIGHT * candidate.growth_signal, 2),
                    places=1)

    def test_the_serializer_emits_it(self):
        candidate = self._snapshot(24, "upside").candidates[0]
        self.assertEqual(draft_board_ui.serialize_candidate(candidate)["growthSignal"],
                         candidate.growth_signal)


class TheRetainedRecordCarriesBothTests(unittest.TestCase):
    """draft_simulation.PickRecord calls itself "one pick's full retained decision context…
    so 'why did this chair take this player' is answerable later by reading this record". It
    was missing the term that decides late upside-mode picks. #150 reads these records."""

    @classmethod
    def setUpClass(cls):
        merger = dm.DataMerger()
        players_db = _players_db(merger)
        pick_order = ds.generate_pick_order([str(i) for i in range(1, NUM_TEAMS + 1)], 3, "snake")
        cls.trajectory = draft_simulation.simulate_full_draft(
            merger, players_db, LEAGUE, pick_order, mode="balanced", config_label="qualifiers")

    def test_every_pick_records_the_basis_its_price_rested_on(self):
        self.assertTrue(self.trajectory.picks, "no picks simulated; this test observed nothing")
        missing = [p.pick_label for p in self.trajectory.picks
                   if p.chosen_replacement_basis is None]
        self.assertEqual([], missing, f"{len(missing)} picks recorded no replacement basis")

    def test_the_recorded_basis_matches_the_chosen_candidate_on_the_retained_board(self):
        """Read off the chosen candidate, never re-derived -- so the record cannot disagree
        with the board stored beside it."""
        for pick in self.trajectory.picks:
            with self.subTest(pick=pick.pick_label):
                row = next(c for c in pick.snapshot["candidates"]
                           if c["id"] == pick.chosen_player_id)
                self.assertEqual(row["replacementBasis"], pick.chosen_replacement_basis)

    def test_balanced_picks_record_no_growth_signal(self):
        """The same absence rule one layer out: this trajectory ran balanced, so there is no
        trajectory term to record, and None says exactly that."""
        self.assertTrue(all(p.chosen_growth_signal is None for p in self.trajectory.picks))


if __name__ == "__main__":
    unittest.main()
