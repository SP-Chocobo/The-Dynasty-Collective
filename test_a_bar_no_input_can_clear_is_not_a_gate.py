"""MANDATE 3.4 / `#206` / `#56` -- the credible-rival-path bar, and the scale that moved under it.

`block_opportunity` is the human-facing "Denies {team}" flag. It requires two things: a premium at
least `2 x NEED_BONUS_PER_DEDICATED_SLOT`, and the premium-driving rival having a credible path to
actually taking the player. The second half was `take_probability >= CREDIBLE_RIVAL_PATH_THRESHOLD`,
with the threshold at 0.10 and its own comment saying what that meant -- *"roughly rank-4-or-better
under draft_strategy's own RANK_TAKE_PROBABILITY"*, whose rank-4 entry is exactly 0.10.

THEN `#206` NORMALISED THE MODEL AND LEFT THE THRESHOLD IN RAW UNITS. A team makes one pick, so
their take probabilities are mutually exclusive and must sum to <= 1 across their board;
unnormalised they summed to 23.49. The threshold went on comparing against a number from the raw
table. Measured on a real mid-draft turn with 23 intervening picks:

    largest take_probability reaching the gate     0.028
    the bar it had to clear                        0.10
    rival_premium >= 2 x NEED_BONUS_PER_DEDICATED_SLOT    24 of 48 candidates
    block_opportunity True                          0 of 48

The premium half fired abundantly and the AND was always False, so the flag was dead and the label
it gates had never appeared. A bar no input can clear is not a gate -- it is a switch wired to off.

THE REPAIR RESTORES THE STATED BAR, IT DOES NOT CHOOSE A NEW ONE (`#56`). The bar is expressed as
the rank it was always described as, which cannot drift when the probability model is renormalised
again -- the entire lesson of the constant it replaces. `rival_premium_take_probability` survives as
an observable, because the magnitude is still worth having beside the rank; nothing gates on it.

After: the flag fires on 5 of those same 48 candidates.

THE FIRST TEST BELOW IS THE ONE THAT MATTERS. Everything else pins a boundary; that one pins that
the boundary is reachable, which is what nothing was checking.
"""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import run_draft_battery as rdb

_HERE = Path(__file__).parent


class _Turn:
    """One real mid-draft turn with real intervening picks ahead of it.

    The gap AHEAD is what rival_premium is computed over, so a turn chosen by the gap behind would
    measure the wrong thing (see the engine-measurement discipline).
    """

    built = False

    @classmethod
    def build(cls):
        if cls.built:
            return
        players_db, _provenance = rdb.build_players_db_from_capture()
        capture = json.loads(Path(rdb.CAPTURE_PATH).read_text(encoding="utf-8"))
        scoring = (capture.get("league_shape") or {}).get("scoring_settings")
        league = next(arm["league"] for arm in db.league_matrix(scoring)
                      if arm["label"] == "12T_ppr")
        merger = dm.DataMerger()
        merger.set_league_format(db.league_format_hint(league))
        teams = [str(i) for i in range(1, 13)]
        order = []
        for round_index in range(6):
            order.extend(teams if round_index % 2 == 0 else list(reversed(teams)))
        picks = []
        for index in range(24):
            board = dr.compute_draft_board(merger, players_db, picks,
                                           my_roster_id=order[index], league=league,
                                           mode="balanced")
            top = next((row for row in board if row.get("universal_value") is not None), None)
            if top is None:
                break
            picks.append({"player_id": top["player_id"], "roster_id": order[index]})
        index = 24
        nxt = next((j for j in range(index + 1, len(order)) if order[j] == order[index]), None)
        cls.gap_ahead = None if nxt is None else nxt - index
        cls.snapshot = ps.build_snapshot(merger, players_db, picks, order, index,
                                         order[index], league, pick_label="t24", top_n=12)
        cls.built = True


def setUpModule():
    _Turn.build()


class TheBarIsReachableTests(unittest.TestCase):
    """The test 3.4 found nobody was running."""

    def test_the_turn_really_has_rivals_ahead_of_it(self):
        self.assertIsNotNone(_Turn.gap_ahead, "no next turn, so no rival can be denied anything")
        self.assertGreater(_Turn.gap_ahead, 1,
                           "vacuous: no intervening picks, so rival_premium is 0 by construction")
        self.assertGreater(len(_Turn.snapshot.candidates), 10, "vacuous: too few candidates")

    def test_the_flag_fires_on_at_least_one_candidate(self):
        fired = [c for c in _Turn.snapshot.candidates if c.block_opportunity]
        self.assertTrue(fired,
                        "block_opportunity is False on every candidate at a turn with "
                        f"{_Turn.gap_ahead} intervening picks. A bar no input can clear is not a "
                        "gate -- this is how it was dead from `#206` until MANDATE 3.4.")

    def test_the_premium_half_alone_is_not_what_is_being_measured(self):
        """Non-vacuity in the other direction: if the premium bar were also never cleared, the
        flag's silence would say nothing about the credible-path half."""
        boundary = 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT
        clearing = [c for c in _Turn.snapshot.candidates
                    if (c.rival_premium or 0.0) >= boundary]
        self.assertTrue(clearing, "no candidate clears the premium boundary, so this turn cannot "
                                  "tell us anything about the credible-path gate")

    def test_the_OLD_threshold_would_still_be_unreachable_here(self):
        """Pinned so nobody restores the probability gate. The values are real and they are two
        orders of magnitude below the number that used to read them."""
        probabilities = [c.rival_premium_take_probability
                         for c in _Turn.snapshot.candidates
                         if c.rival_premium_take_probability is not None]
        self.assertTrue(probabilities, "vacuous: no take probabilities reached the snapshot")
        self.assertLess(max(probabilities), 0.10,
                        "the normalised take probabilities now reach 0.10, so the old threshold "
                        "would be reachable and this module's premise needs re-measuring")


class TheBarIsDerivedFromTheTableItWasQuotedFromTests(unittest.TestCase):
    def test_the_bar_is_the_rank_whose_raw_probability_was_the_old_threshold(self):
        """`#56`: derived, not chosen. The old constant was 0.10 and described itself as
        rank-4-or-better; 0.10 IS the rank-4 entry, so the rank carries the same bar."""
        self.assertEqual(ds.RANK_TAKE_PROBABILITY[ps.CREDIBLE_RIVAL_PATH_MAX_RANK], 0.10)

    def test_the_retired_constant_is_gone_rather_than_left_unread(self):
        """A constant nothing reads is a claim nothing checks, and this repository has already
        paid for carrying one (see draft_strategy's deleted FORFEIT_OPPONENT_BOARD_DEPTH)."""
        self.assertFalse(hasattr(ps, "CREDIBLE_RIVAL_PATH_THRESHOLD"))


class TheGateReadsTheRankAndNothingElseTests(unittest.TestCase):
    def _flags(self, **over):
        candidate = {"universal_value": 80.0, "team_acquisition_value": 85.0,
                     "positional_forfeit": None, "positional_cliff": None,
                     "rival_premium": 2 * dr.NEED_BONUS_PER_DEDICATED_SLOT + 5.0,
                     "rival_premium_take_probability": 0.001,
                     "rival_premium_take_rank": 1}
        candidate.update(over)
        return ps.decision_path_flags([candidate])[0]

    def test_a_rank_at_the_bar_is_credible(self):
        self.assertTrue(self._flags(rival_premium_take_rank=ps.CREDIBLE_RIVAL_PATH_MAX_RANK
                                    )["block_opportunity"])

    def test_a_rank_past_the_bar_is_not(self):
        self.assertFalse(self._flags(rival_premium_take_rank=ps.CREDIBLE_RIVAL_PATH_MAX_RANK + 1
                                     )["block_opportunity"])

    def test_an_absent_rank_is_not_credible_and_does_not_default_to_one(self):
        """`#187`: None means no rival board priced him at all, which is a different statement from
        'ranked badly' and must not be read as either credible or as rank zero."""
        self.assertFalse(self._flags(rival_premium_take_rank=None)["block_opportunity"])

    def test_a_tiny_take_probability_no_longer_suppresses_a_top_ranked_rival(self):
        """The defect, stated as a test. 0.001 is below every threshold anyone might restore, and a
        rank-1 rival is as credible as a rival gets."""
        self.assertTrue(self._flags(rival_premium_take_probability=0.001,
                                    rival_premium_take_rank=1)["block_opportunity"])

    def test_premium_magnitude_alone_still_does_not_fire_it(self):
        self.assertFalse(self._flags(rival_premium=1000.0,
                                     rival_premium_take_rank=40)["block_opportunity"])

    def test_the_gate_does_not_read_the_probability_at_all(self):
        """Read from the AST (`#200`): the probability is an observable now, and a second reader of
        it inside the gate would put the moved scale back in the decision path."""
        tree = ast.parse((_HERE / "pick_synthesis.py").read_text(encoding="utf-8"))
        gate = next(node for node in ast.walk(tree)
                    if isinstance(node, ast.FunctionDef) and node.name == "decision_path_flags")
        names = {child.value for child in ast.walk(gate)
                 if isinstance(child, ast.Constant) and isinstance(child.value, str)}
        self.assertIn("rival_premium_take_rank", names)
        self.assertNotIn("rival_premium_take_probability", names,
                         "decision_path_flags reads the take probability again -- that is the "
                         "scale `#206` moved, and the reason this bar is a rank")


class TheAuditStillMirrorsProductionTests(unittest.TestCase):
    """cdme_denial_semantics_audit exists to recompute this flag the way production does. An audit
    on the old gate would report a density production cannot produce."""

    def test_the_audit_reads_the_same_bar(self):
        source = (_HERE / "cdme_denial_semantics_audit.py").read_text(encoding="utf-8")
        self.assertIn("CREDIBLE_RIVAL_PATH_MAX_RANK", source)
        self.assertNotIn("CREDIBLE_RIVAL_PATH_THRESHOLD", source)

    def test_the_rank_reaches_the_audit_from_the_same_place_the_probability_does(self):
        source = (_HERE / "cdme_denial_semantics_audit.py").read_text(encoding="utf-8")
        self.assertIn("rank_on_their_board", source,
                      "the audit invents a rank instead of taking estimate_survival's own")


if __name__ == "__main__":
    unittest.main()
