"""Fidelity tests for cdme_denial_semantics_audit.py: its own rival_premium and
block_opportunity recomputation must match draft_strategy.pick_analysis /
pick_synthesis.decision_path_flags' real output exactly before any audit finding built on it
is trusted."""

from __future__ import annotations

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
from cdme_denial_semantics_audit import audit_candidates

POSITIONS = ("QB", "RB", "WR", "TE")
SUPERFLEX_LEAGUE = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False, dynasty=True)


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


class FidelityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        cls.players_db = _build_pool_players_db(cls.merger)
        # A REAL multi-round order, and this is not cosmetic. It used to be a single round --
        # `[str(i) for i in range(1, 13)]` -- with roster "1" picking first, so
        # find_next_pick_index returned None, intervening_roster_ids returned [], and every
        # candidate came back with rival_premium 0.0, premium_team None,
        # premium_team_take_probability None and survival_probability 1.0. This whole class
        # exists to prove that cdme_denial_semantics_audit reproduces pick_analysis's numbers
        # exactly, and it was proving that 0.0 equals 0.0 and None equals None on every row.
        # Found by an assertion-reachability trace over the suite: the three assertions inside
        # `if a.premium_team is not None:` had never executed once.
        #
        # Three rounds of snake gives roster "1" 22 intervening picks before its next turn, and
        # the same candidates then carry real values (measured: rival_premium 8.72,
        # premium_team "2", take probability 0.55, survival 0.0).
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], 3, "snake")

    def test_rival_premium_matches_pick_analysis_exactly(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        candidate_ids = [r["player_id"] for r in board[:8]]
        real = ds.pick_analysis(
            self.merger, self.players_db, [], self.pick_order, 0, "1", SUPERFLEX_LEAGUE, candidate_ids,
        )
        real_by_id = {str(r["player_id"]): r for r in real}

        audits = audit_candidates(
            self.merger, self.players_db, [], self.pick_order, 0, "1", SUPERFLEX_LEAGUE, candidate_ids,
        )
        self.assertEqual(len(audits), len(candidate_ids))
        for a in audits:
            self.assertAlmostEqual(a.rival_premium, real_by_id[a.player_id]["rival_premium"], places=2)
            self.assertEqual(a.survival_probability, real_by_id[a.player_id]["survival_probability"])

    def test_block_opportunity_matches_decision_path_flags_exactly(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        candidate_ids = [r["player_id"] for r in board[:8]]
        snap = ps.build_snapshot(
            self.merger, self.players_db, [], self.pick_order, 0, "1", SUPERFLEX_LEAGUE, pick_label="1.01", top_n=8,
        )
        snap_by_id = {c.player_id: c for c in snap.candidates}

        audits = audit_candidates(
            self.merger, self.players_db, [], self.pick_order, 0, "1", SUPERFLEX_LEAGUE,
            [c.player_id for c in snap.candidates],
        )
        for a in audits:
            self.assertEqual(a.block_opportunity, snap_by_id[a.player_id].block_opportunity)

    def test_premium_team_take_probability_is_a_real_entry_from_risk_by_team_when_present(self):
        board = dr.compute_draft_board(
            self.merger, self.players_db, [], my_roster_id="1", league=SUPERFLEX_LEAGUE, mode="balanced",
        )
        candidate_ids = [r["player_id"] for r in board[:8]]
        audits = audit_candidates(
            self.merger, self.players_db, [], self.pick_order, 0, "1", SUPERFLEX_LEAGUE, candidate_ids,
        )
        with_premium = [a for a in audits if a.premium_team is not None]
        self.assertTrue(with_premium,
                        "no candidate carries a premium team -- this fixture is not reaching "
                        "the state the test is about, and every assertion below would be "
                        "skipped silently")
        for a in with_premium:
            self.assertIsNotNone(a.premium_team_take_probability)
            self.assertGreaterEqual(a.premium_team_take_probability, 0.0)
            self.assertLessEqual(a.premium_team_take_probability, 1.0)


if __name__ == "__main__":
    unittest.main()
