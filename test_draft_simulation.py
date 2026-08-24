"""draft_simulation is an engine-VALIDATION harness -- it must never become a second decision
engine. These tests pin exactly the properties that make it trustworthy as a diagnostic
instrument rather than a simulator that just happens to produce plausible-looking output:
determinism under identical inputs, real trial variation under genuinely different inputs
(never randomness), that every pick actually goes through the same production build_snapshot
call a human's own turn would use, that the full decision context survives per pick (not just
who was taken), and that nothing here mutates the merger/league/players_db it was handed.

Uses the real committed baseline (same DataMerger() pattern as test_draft_room.py) rather than
a synthetic fixture -- a multi-team draft needs real depth at every position or it runs out of
distinct players well before the engine's behavior says anything meaningful.

A single build_snapshot call against the real baseline runs ~1.4s (confirmed by direct timing
-- this is real pick_analysis/survival math over the real player pool, not something to fake
out for test speed, since that's the whole point of exercising the actual engine). Every class
below computes its trajectory/trajectories exactly ONCE in setUpClass and shares them across
assertion methods, and draft sizes are kept deliberately small (a handful of teams/rounds) --
enough to exercise every property this suite needs to pin, not a full 12x15 draft, which is
reserved for the separate, occasional trial-running step this harness exists to support.
"""

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
from draft_simulation import DraftTrajectory, PickRecord, run_trials, simulate_full_draft


def _build_pool_players_db(positions=("QB", "RB", "WR", "TE")):
    """Same reconstruction test_draft_room.py's own fixture uses: every real baseline player,
    Sleeper-shaped, first-initial + full last name (matching Draft Sharks' own abbreviation)."""
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


class SimulateFullDraftDeterminismTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=4, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        cls.pick_order = ds.generate_pick_order(["1", "2", "3", "4"], total_rounds=2)  # 8 picks
        # Computed exactly twice, here, for the whole class -- every test method below just
        # asserts against these, rather than each re-running the (real, ~1.4s/pick) engine.
        cls.traj_a = simulate_full_draft(cls.merger, cls.players_db, cls.league, cls.pick_order)
        cls.traj_b = simulate_full_draft(cls.merger, cls.players_db, cls.league, cls.pick_order)

    def test_identical_inputs_produce_an_identical_trajectory(self):
        picks_a = [(p.roster_id, p.chosen_player_id) for p in self.traj_a.picks]
        picks_b = [(p.roster_id, p.chosen_player_id) for p in self.traj_b.picks]
        self.assertEqual(picks_a, picks_b)
        self.assertEqual(len(picks_a), len(self.pick_order))

    def test_identical_inputs_produce_identical_full_snapshots_too(self):
        # Not just "same player chosen" -- the entire retained decision context (necessity,
        # candidate order, decision_regime) must match too, or the harness isn't actually
        # deterministic, just its final output happens to look stable.
        for rec_a, rec_b in zip(self.traj_a.picks, self.traj_b.picks):
            self.assertEqual(rec_a.snapshot, rec_b.snapshot)
            self.assertEqual(rec_a.decision_regime, rec_b.decision_regime)


class SimulateFullDraftRealEngineTests(unittest.TestCase):
    """Twelve chairs specifically (not a smaller stand-in) -- the property under test is
    real-engine behavior across the actual chair count this harness exists for."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=1)  # 12 picks
        cls.traj = simulate_full_draft(cls.merger, cls.players_db, cls.league, cls.pick_order)

    def test_twelve_distinct_chairs_all_pick(self):
        roster_ids_seen = {p.roster_id for p in self.traj.picks}
        self.assertEqual(roster_ids_seen, {str(i) for i in range(1, 13)})
        self.assertEqual(len(self.traj.picks), 12)

    def test_no_player_is_drafted_twice_across_all_twelve_chairs(self):
        chosen = [p.chosen_player_id for p in self.traj.picks]
        self.assertEqual(len(chosen), len(set(chosen)))

    def test_every_pick_is_a_real_top_candidate_not_a_second_selection_rule(self):
        # The production contract (draft_room.simulate_opponent_picks' own): the chosen player
        # is the single highest team_acquisition_value ("tav") candidate on that pick's board.
        for rec in self.traj.picks:
            candidates = rec.snapshot["candidates"]
            top = max(candidates, key=lambda c: c["tav"])
            self.assertEqual(rec.chosen_player_id, top["id"])

    def test_full_snapshot_is_retained_not_just_the_chosen_player(self):
        first = self.traj.picks[0]
        self.assertIn("candidates", first.snapshot)
        self.assertGreater(len(first.snapshot["candidates"]), 1)
        # Real per-candidate decision signals, not just id/name -- this is what makes "why
        # was this chosen" answerable later.
        sample = first.snapshot["candidates"][0]
        for field in ("necessity", "tav", "uv", "survival"):
            self.assertIn(field, sample)

    def test_final_rosters_derive_cleanly_from_picks(self):
        rosters = self.traj.final_rosters()
        self.assertEqual(set(rosters), {str(i) for i in range(1, 13)})
        for roster_id, player_ids in rosters.items():
            self.assertEqual(len(player_ids), 1)  # 1 round each


class TrialVariationTests(unittest.TestCase):
    """Trials vary by changing REAL inputs -- draft slot/order, league format -- never by
    injecting randomness into an otherwise-deterministic engine. Two rounds (not one) so a
    reversed draft order genuinely gives later picks a different accumulated roster to react
    to, not just a relabeled single round."""

    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        standard_league = dr.build_mock_league(teams=3, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        superflex_league = dr.build_mock_league(teams=3, superflex=True, scoring="ppr", te_premium=False, dynasty=True)
        cls.order_a = ds.generate_pick_order(["1", "2", "3"], total_rounds=2)  # 6 picks
        cls.order_b = ds.generate_pick_order(["3", "2", "1"], total_rounds=2)  # 6 picks
        # One run_trials call covering all three comparisons this class needs -- never three
        # separate simulate_full_draft calls for the same underlying question.
        cls.trials = run_trials(cls.merger, cls.players_db, [
            {"league": standard_league, "pick_order": cls.order_a, "label": "order_a"},
            {"league": standard_league, "pick_order": cls.order_b, "label": "order_b"},
            {"league": superflex_league, "pick_order": cls.order_a, "label": "superflex_order_a"},
        ])

    def test_different_pick_order_changes_the_trajectory(self):
        picks_a = [(p.roster_id, p.chosen_player_id) for p in self.trials[0].picks]
        picks_b = [(p.roster_id, p.chosen_player_id) for p in self.trials[1].picks]
        self.assertNotEqual(picks_a, picks_b)

    def test_different_league_format_changes_the_trajectory(self):
        # Superflex materially changes QB demand -- a real, legitimate input difference, not a
        # random seed standing in for "make the trial look different."
        picks_standard = [(p.roster_id, p.chosen_player_id) for p in self.trials[0].picks]
        picks_superflex = [(p.roster_id, p.chosen_player_id) for p in self.trials[2].picks]
        self.assertNotEqual(picks_standard, picks_superflex)

    def test_run_trials_reflects_each_configs_own_inputs(self):
        self.assertEqual(self.trials[0].config["label"], "order_a")
        self.assertEqual(self.trials[1].config["label"], "order_b")
        self.assertEqual(self.trials[0].config["pick_order"], [str(r) for r in self.order_a])
        self.assertEqual(self.trials[1].config["pick_order"], [str(r) for r in self.order_b])


class NoMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger, cls.players_db = _build_pool_players_db(("QB", "RB", "WR", "TE"))
        cls.league = dr.build_mock_league(teams=3, superflex=False, scoring="ppr", te_premium=False, dynasty=True)
        cls.pick_order = ds.generate_pick_order(["1", "2", "3"], total_rounds=1)  # 3 picks
        cls.league_before = {k: (v.copy() if isinstance(v, (list, dict)) else v) for k, v in cls.league.items()}
        cls.pick_order_before = list(cls.pick_order)
        cls.players_db_before = {k: dict(v) for k, v in cls.players_db.items()}
        # One real call checks all three inputs for mutation at once -- no need for three
        # separate (expensive) engine runs to check three different objects.
        simulate_full_draft(cls.merger, cls.players_db, cls.league, cls.pick_order)

    def test_does_not_mutate_the_league_dict(self):
        self.assertEqual(self.league, self.league_before)

    def test_does_not_mutate_the_input_pick_order_list(self):
        self.assertEqual(self.pick_order, self.pick_order_before)

    def test_does_not_mutate_players_db(self):
        self.assertEqual(self.players_db, self.players_db_before)


class DraftTrajectoryShapeTests(unittest.TestCase):
    def test_pick_record_and_trajectory_are_frozen(self):
        # Immutability isn't a style preference here -- a trajectory is meant to be recorded
        # and diffed later; a caller quietly mutating it would silently break both.
        rec = PickRecord(
            pick_no=1, round=1, roster_id="1", pick_label="1.01",
            chosen_player_id="p1", decision_regime="contested", snapshot={},
        )
        with self.assertRaises(Exception):
            rec.chosen_player_id = "p2"
        traj = DraftTrajectory(config={}, picks=(rec,))
        with self.assertRaises(Exception):
            traj.config = {}


if __name__ == "__main__":
    unittest.main()
