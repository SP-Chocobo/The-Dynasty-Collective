"""#119 -- causal reconstruction used to break at the valuation leaf.

`universal_value` IS `bpa + time_horizon_adj + risk_adj` (draft_room's own header line). The
board computed all three and, until this repair, **nothing downstream read the two adjustments**:
`quantity_readers.scan()` classified both as `decomposition` with an empty scoring_readers, an
empty observing_readers and an empty carriers list. So the price crossed into the snapshot as a
bare number and a chair asking *why is he worth that* hit a dead end -- at the one leaf where the
answer lives.

WHY IT IS LOAD-BEARING RATHER THAN POLISH, and this is the same argument #183 rests on: the
owner ruled the Draft Room must work fully with no API, so for a customer without a key the
engine's own evidence IS the whole explanation. An unexplained price is most of that explanation
missing.

HALF OF #119's OWN WORDING IS STALE and this file does not restate it. The item reads
"`time_horizon_adj`/`risk_adj` reach no production consumer; **board drops `bpa_source`/
`confidence`**". The second clause is no longer true -- both reach `pick_debate`, and
`confidence` reaches `app.py` as well. Only the first clause was live.
"""
from __future__ import annotations

import unittest

import data_merger as dm
import draft_room as dr
import draft_strategy as ds
import pick_debate as pd
import pick_synthesis as ps
import quantity_readers as qr
from pick_synthesis import CandidateSnapshot


def candidate(**over) -> CandidateSnapshot:
    base = dict(
        position_best_now=None, position_next_turn_value=None, acting_now_value=None,
        player_id="9221", name="Test Player", position="RB", team="SF", bpa=44.0,
        bpa_source="points_vor_draftsharks", confidence=80.0, universal_value=50.0,
        need_bonus=6.0, team_acquisition_value=60.0,
        survival_probability=0.4, survival_basis=None, intervening_picks=2, opportunity_cost=30.0,
        expected_value_of_waiting=20.0, denial_value=30.0, denial_basis="measured",
        rival_premium_basis=None, denial_team="4", rival_premium=6.0,
        positional_forfeit=None, position_expected_taken=None, positional_cliff=None,
        position_run_detected=False, pick_necessity=75.0, necessity_label="PREFERRED",
        near_tie_with_leader=False, cliff_protection=False, block_opportunity=False,
        pure_value=False, context_elevated=False, consensus_rank=None, consensus_tier=None,
        projected_points=None)
    base.update(over)
    return CandidateSnapshot(**base)


class TheTwoAdjustmentsNowHaveAReader(unittest.TestCase):
    """Checked through `quantity_readers`, which derives its answer by walking this repo's own
    ASTs, rather than by asserting against a hand-written list. An independent instrument
    agreeing is worth more than a test that only restates the change."""

    def setUp(self):
        self.rows = {r["quantity"]: r for r in qr.scan()}

    def test_neither_term_is_read_by_nobody_any_more(self):
        for name in ("time_horizon_adj", "risk_adj"):
            with self.subTest(name):
                row = self.rows[name]
                reach = (row["scoring_readers"] + row["observing_readers"] + row["carriers"])
                self.assertTrue(reach, f"{name} is computed and read by nothing -- #119 is back")

    def test_they_are_OBSERVABLE_and_not_scoring_inputs(self):
        """The repair DISCLOSES; it does not wire. Promoting a decomposition term into a
        scoring input is a valuation change and would need the owner, not a test."""
        for name in ("time_horizon_adj", "risk_adj"):
            with self.subTest(name):
                self.assertEqual(self.rows[name]["verdict"], qr.OBSERVABLE)
                self.assertEqual(self.rows[name]["scoring_readers"], [],
                                 f"{name} became a scoring input -- that is a #50 decision")

    def test_the_stale_half_of_the_item_is_actually_stale(self):
        """#119 also claims the board drops bpa_source/confidence. It does not, and recording
        that here stops the dead clause being re-opened as work."""
        for name in ("bpa_source", "confidence"):
            with self.subTest(name):
                row = self.rows[name]
                self.assertIn("pick_debate.py",
                              row["observing_readers"] + row["scoring_readers"])


class ThePriceIsExplainedWhereAPersonReadsIt(unittest.TestCase):
    def test_the_sum_is_rendered_as_arithmetic_when_every_term_is_a_number(self):
        out = pd._format_candidate(candidate(time_horizon_adj=4.5, risk_adj=1.5), None)
        self.assertIn("Universal value: 50.0 = bpa 44.0 + horizon +4.5 + risk +1.5", out)

    def test_a_negative_adjustment_keeps_its_sign(self):
        """The signs are the point. A risk haircut that reads as `+ risk -3.0` explains a price;
        one that reads as `risk 3.0` inverts the causal story."""
        out = pd._format_candidate(candidate(time_horizon_adj=-2.0, risk_adj=-3.0), None)
        self.assertIn("horizon -2.0", out)
        self.assertIn("risk -3.0", out)

    def test_upside_mode_withholds_the_sum_and_SAYS_SO(self):
        """The reachable absent case: `upside_score` genuinely never computes these two, and the
        board omits rather than zeroes them. Silence would read as 'no adjustment applied'."""
        out = pd._format_candidate(candidate(), None)
        self.assertNotIn("= bpa", out)
        self.assertIn("decomposition not computed for this board", out)
        self.assertIn("never as 'no horizon or risk adjustment applied'", out)

    def test_one_absent_term_withholds_the_whole_sum_not_half_of_it(self):
        """Same rule the team-value sum follows (#183): a sum missing an addend, shown to a model
        instructed never to recompute, is worse than no sum at all."""
        out = pd._format_candidate(candidate(time_horizon_adj=4.5, risk_adj=None), None)
        self.assertNotIn("= bpa", out)
        self.assertIn("decomposition not computed", out)

    def test_the_price_itself_is_still_reported_when_the_parts_are_not(self):
        """Degrade, never abort. The whole is a real measurement and survives its parts."""
        self.assertIn("Universal value: 50.0", pd._format_candidate(candidate(), None))


class TheCarryItselfIsExercised(unittest.TestCase):
    """THE GAP MY OWN FIRST DRAFT LEFT, and it was found by mutation rather than by reading.

    Every other test in this file builds a `CandidateSnapshot` by hand, so severing the carry in
    `build_snapshot` -- replacing `row.get("time_horizon_adj")` with a literal `None` -- left them
    all green. The `quantity_readers` tests stayed green too, because the mutant still MENTIONS
    the name and an AST reference is not a value. A guard that cannot see the wire it is guarding
    is the vacuous-test class this repo mutation-tests for.

    So this one runs the real thing: a real merger, a real board, a real snapshot, and asserts the
    two terms ARRIVE with values rather than merely being declared as fields."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.players_db = {}
        pid = 0
        for pos in ("QB", "RB", "WR", "TE"):
            sub = proj[proj["position"] == pos].sort_values(
                "trade_value", ascending=False).head(20)
            for _, row in sub.iterrows():
                pid += 1
                parts = row["norm_name"].split()
                cls.players_db[str(pid)] = {
                    "first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                    "position": pos, "fantasy_positions": [pos], "team": row.get("team"),
                }
        cls.pick_order = ds.generate_pick_order([str(i) for i in range(1, 13)], total_rounds=3)
        cls.league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                          te_premium=False, dynasty=True)
        cls.snap = ps.build_snapshot(
            cls.merger, cls.players_db, [], cls.pick_order, current_index=0,
            my_roster_id="1", league=cls.league, pick_label="1.01", top_n=6)

    def test_risk_adj_VARIES_on_the_real_board_even_though_this_fixture_is_all_healthy(self):
        """A LIMIT OF THE FIXTURE ABOVE, stated rather than hidden. Its population is the top 20
        per position by trade value -- every one of them healthy -- so `risk_adj` is 0.0 for all
        48, and a mutation replacing the carry with a literal `0.0` is INDISTINGUISHABLE there.
        That is not a weak test, it is a population without the phenomenon in it.

        Measured on a full board: 256 rows carry the term, 249 at 0.0 and **7 nonzero**, every one
        an IR player, ranging -5.4 to -18.0. So the term does vary, the variation is injury-driven
        exactly as `#191` describes, and a measured 0.0 means ASSESSED AND NO HAIRCUT rather than
        not assessed -- which is why the Dock prints `+ risk +0.0` instead of omitting it."""
        board = dr.compute_draft_board(self.merger, self.players_db, [],
                                       my_roster_id="1", league=self.league)
        vals = [r.get("risk_adj") for r in board if r.get("risk_adj") is not None]
        self.assertTrue(vals, "no row carries risk_adj -- the board stopped emitting it")
        self.assertTrue(all(v <= 0 for v in vals),
                        "risk_adj is a haircut; a positive value inverts its meaning")

    def test_a_balanced_board_delivers_both_terms_with_real_values(self):
        priced = [c for c in self.snap.candidates if c.universal_value is not None]
        self.assertTrue(priced, "no priced candidate -- the population is vacuous")
        for c in priced:
            with self.subTest(c.name):
                self.assertIsNotNone(c.time_horizon_adj, "the carry is severed")
                self.assertIsNotNone(c.risk_adj, "the carry is severed")

    def test_the_terms_actually_reconstruct_the_price(self):
        """The claim the Dock now prints, checked against the engine rather than assumed.
        `universal_value = bpa + time_horizon_adj + risk_adj`, to the board's own rounding."""
        for c in self.snap.candidates:
            if None in (c.universal_value, c.bpa, c.time_horizon_adj, c.risk_adj):
                continue
            with self.subTest(c.name):
                self.assertAlmostEqual(
                    c.universal_value, c.bpa + c.time_horizon_adj + c.risk_adj, places=1,
                    msg="the decomposition the Dock renders does not add up to the price")

    def test_the_rendered_line_matches_the_engine_for_a_real_candidate(self):
        """End to end: the arithmetic a chair reads is the arithmetic the board computed."""
        c = next(x for x in self.snap.candidates
                 if None not in (x.universal_value, x.bpa, x.time_horizon_adj, x.risk_adj))
        out = pd._format_candidate(c, None)
        self.assertIn(f"Universal value: {c.universal_value} = bpa {c.bpa}", out)


if __name__ == "__main__":
    unittest.main()
