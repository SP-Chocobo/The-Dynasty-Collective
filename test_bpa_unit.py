"""BPA carries a stable unit (gap #1) and a signed measurement (gap #2).

THE DEFECT. bpa was `clip(vor / max(vor) * 100, 0, 100)`. Two consequences, both measured on
the real committed board:

  * THE UNIT MOVED. The reference is the largest VOR in the LIVE pool, so it shrinks as the
    pool drains -- 97 -> 72 -> 27 -> 16 -> 1 -> 0 across the draft. Decomposing every player's
    bpa change into "his own value moved" and "the ruler moved under him", the ruler carried
    94.6% of ALL bpa movement. Isaiah Likely, 186 projected points every single round, read
    0.0 -> 50.0 -> 61.5 -> 88.9 -> 0.0. A player property may not move because a different
    player was drafted.
  * THE MEASUREMENT WAS DESTROYED. A below-replacement player clipped to 0.0, so 95%+ of all
    zeros were real, measured, negative VOR flattened into the same value as a genuine
    boundary zero and a degenerate anchor. 141 distinguishable states became 20 at round 4.

THE CONTRACT THAT DETERMINES THE FIX. Four invariants already established, which jointly leave
only one answer:

  62  the draft state contextualizes a valuation; it never redefines the valuation's unit
  63  the normalization reference is never a property of a single other row
  64  a below-baseline measurement is preserved as a signed measurement
  65  bounded presentation is a rendering decision -- no information is destroyed in an
      underlying quantity to obtain a bounded range

Any max is a property of one row, so 63 rules out every "better reference". 65 removes the
reason to have one at all: measured across every consumer, ZERO require bpa <= 100, while five
read magnitude and need a stable unit. So bpa is VOR, in real points, unclipped. The fix
REMOVES a coefficient rather than inventing one, and closes both gaps in one change.

WHAT THIS DOES NOT DO. It does not touch NEAR_TIE_BAND, NECESSITY_STANDOUT_REFERENCE_GAP,
NEED_BONUS_MAX or TIME_HORIZON_CLAMP. Those keep their exact values. What changes is that they
now mean ONE thing instead of drifting 97x: at round 1 today's scale already makes
NEAR_TIE_BAND worth 1.94 real points, so keeping 2.0 preserves round-1 behaviour exactly and
stops the drift everywhere else. Whether 2.0 is the RIGHT tie band in real points is a
separate question that this fix makes answerable for the first time -- today the band has no
fixed meaning to evaluate.
"""
import math
import unittest

import pandas as pd

import data_merger as dm
import draft_room as dr


def _absent(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


class BpaIsVorInRealPointsTests(unittest.TestCase):
    """The unit, asserted directly on the scaling function so it holds regardless of which
    players happen to be in the baseline."""

    def test_a_positive_vor_passes_through_unchanged(self):
        vor = pd.Series([26.0, 5.0, 0.5])
        self.assertEqual(list(dr._scale_vor_to_bpa(vor)), [26.0, 5.0, 0.5])

    def test_a_negative_vor_keeps_its_sign_and_magnitude(self):
        vor = pd.Series([-135.0, -1.0])
        self.assertEqual(list(dr._scale_vor_to_bpa(vor)), [-135.0, -1.0])

    def test_absence_stays_absence_and_never_becomes_a_number(self):
        vor = pd.Series([10.0, float("nan")])
        result = dr._scale_vor_to_bpa(vor)
        self.assertEqual(result.iloc[0], 10.0)
        self.assertTrue(pd.isna(result.iloc[1]))

    def test_the_scale_does_not_depend_on_the_rest_of_the_pool(self):
        # The whole defect in one assertion: the same VOR must produce the same bpa whether
        # the pool's best player is still on the board or already drafted.
        with_star = dr._scale_vor_to_bpa(pd.Series([97.0, 26.0]))
        without = dr._scale_vor_to_bpa(pd.Series([26.0]))
        self.assertEqual(with_star.iloc[1], without.iloc[0])

    def test_gap_ratios_survive_which_was_the_original_purpose(self):
        result = dr._scale_vor_to_bpa(pd.Series([40.0, 20.0, 10.0]))
        self.assertEqual((result.iloc[0] - result.iloc[1]) / (result.iloc[1] - result.iloc[2]),
                         2.0)


class TheThreeZeroRoutesAreDistinguishableTests(unittest.TestCase):
    """Before this, a genuine boundary zero, a clipped negative and a degenerate anchor were
    one indistinguishable value. Only the first is actually zero."""

    def test_a_below_replacement_player_is_not_reported_as_at_replacement(self):
        result = dr._scale_vor_to_bpa(pd.Series([0.0, -135.0]))
        self.assertEqual(result.iloc[0], 0.0)
        self.assertNotEqual(result.iloc[1], 0.0)

    def test_two_different_negatives_stay_different(self):
        result = dr._scale_vor_to_bpa(pd.Series([-1.0, -135.0]))
        self.assertNotEqual(result.iloc[0], result.iloc[1])


class RealBoardBehaviourTests(unittest.TestCase):
    """On the repaired canonical data, end to end."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()
        proj = cls.merger.projections
        cls.db = {}
        pid = 0
        for position in ("QB", "RB", "WR", "TE", "K", "DEF"):
            rows = proj[proj["position"] == position].sort_values("trade_value", ascending=False)
            for _, row in rows.iterrows():
                pid += 1
                parts = str(row["name"]).split()
                cls.db[str(pid)] = {
                    "first_name": parts[0] if parts else "",
                    "last_name": " ".join(parts[1:]) or (parts[0] if parts else ""),
                    "position": position, "fantasy_positions": [position],
                    "team": row.get("team")}
        cls.league = {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
                                          + ["BN"] * 11,
                      "total_rosters": 12, "settings": {"type": 2}, "scoring_settings": {}}
        cls.board = dr.compute_draft_board(cls.merger, cls.db, [], my_roster_id="1",
                                           league=cls.league, mode="balanced")

    def test_the_board_carries_real_negative_measurements(self):
        negatives = [r for r in self.board if not _absent(r.get("bpa")) and r["bpa"] < 0]
        self.assertTrue(negatives, "no below-replacement player kept a signed measurement")

    def test_the_top_player_is_no_longer_pinned_to_a_round_number(self):
        priced = [r["bpa"] for r in self.board if not _absent(r.get("bpa"))]
        self.assertNotEqual(max(priced), 100.0,
                            "a top bpa of exactly 100.0 means the max-reference is still in play")

    def test_a_players_bpa_moves_only_by_what_the_anchor_moved(self):
        """The precise invariant, not a tolerance.

        bpa is still allowed to move when other players are drafted -- his position's
        REPLACEMENT LEVEL moves, and that is real market information the engine is supposed to
        carry (scarcity movement). What must no longer happen is movement from a rescaling
        RULER, which was 94.6% of it.

        So the assertion is exact: for a player whose own projection never changes, the whole
        of his bpa change must be accounted for by the change in his position's replacement
        level, to the cent. Any residual is a ruler.

        An earlier version of this test asserted "moved less than 25" and failed on a real RB
        who moved 24.0 -> 59.0 after 24 picks -- correctly, because RBs had been drafted and
        RB's replacement level genuinely fell. An arbitrary tolerance cannot tell an intended
        anchor move from an unintended ruler move; this can."""
        priced = [r for r in self.board if not _absent(r.get("bpa")) and r["bpa"] > 0]
        target = priced[len(priced) // 2]
        picks = [{"player_id": r["player_id"], "roster_id": "2", "round": 1, "pick_no": i + 1}
                 for i, r in enumerate(self.board[:24]) if r["player_id"] != target["player_id"]]
        later = dr.compute_draft_board(self.merger, self.db, picks, my_roster_id="1",
                                       league=self.league, mode="balanced")
        moved = next(r for r in later if r["player_id"] == target["player_id"])

        before = self._replacement_level(target["position"], [])
        after = self._replacement_level(target["position"], picks)
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        self.assertAlmostEqual(moved["bpa"] - target["bpa"], before - after, delta=0.011,
                               msg=(f"{target['name']} moved {target['bpa']} -> {moved['bpa']}; "
                                    f"replacement {before} -> {after}. A residual here is a ruler."))

    def _replacement_level(self, position, picks):
        drafted = {str(p["player_id"]) for p in picks}
        pool = dr.build_available_pool(self.merger, self.db, drafted,
                                       {"QB", "RB", "WR", "TE", "K", "DEF", "FLEX"})
        pool["_points"] = pool["projection"].astype(float)
        pool = pool[pool["_points"].notna()].copy()
        demand = dr.remaining_starter_demand(self.league["roster_positions"], 12, picks, self.db)
        levels = dr.replacement_levels(pool, "_points", self.league["roster_positions"], 12,
                                       remaining_demand=demand)
        return levels.get(position)

    def test_universal_value_still_decomposes_exactly(self):
        for row in self.board:
            if _absent(row.get("bpa")):
                continue
            expected = row["bpa"] + row.get("time_horizon_adj", 0.0) + row.get("risk_adj", 0.0)
            self.assertAlmostEqual(row["universal_value"], expected, delta=0.011, msg=row["name"])


if __name__ == "__main__":
    unittest.main()
