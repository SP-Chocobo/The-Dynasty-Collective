"""Regression guard for a real finding from the scoring-propagation audit (see
run_scoring_propagation_sweep.py and the roadmap discussion around it): sleeper_client's
compute_points_from_stats and player_universe's score_projection are two independently
maintained functions that implement the identical "weighted sum over matching stat
categories" formula, never sharing a call.

compute_points_from_stats(stats, scoring) is used once, at app.py's matchup/roster display
(row["sleeper_proj"]). score_projection(stats, scoring) is used by draft_room.py's IDP
live-scoring fallback (positions Draft Sharks doesn't project at all) and by
player_universe.py itself when building the roster's own "sleeper_proj" field.

They are mathematically equivalent today (confirmed by inspection: one iterates
scoring_settings.items() and looks up stats.get(category), the other iterates
stats.items() and looks up scoring_settings.get(category, 0) -- both reduce to "sum
value*weight over categories present in both dicts with a truthy stat value"). This is
exactly the kind of parallel-reimplementation risk flagged during the audit: nothing
stops the two from silently drifting apart the next time either one is touched. This test
is the tripwire -- it does not change production behavior, it only proves the two stay in
lockstep across a battery of real-shaped inputs.

If this test ever fails, that's not a bug in the test: it means someone edited one
function without updating the other, and every downstream consumer of whichever one
wasn't touched is now scoring off a formula the other module no longer agrees with.
"""

from __future__ import annotations

import unittest

import player_universe as pu
import sleeper_client as sc


class ComputePointsFromStatsAndScoreProjectionStayInLockstepTests(unittest.TestCase):
    def _assert_parity(self, stats: dict, scoring: dict) -> None:
        self.assertEqual(
            sc.compute_points_from_stats(stats, scoring),
            pu.score_projection(stats, scoring),
        )

    def test_offense_shaped_projection(self):
        self._assert_parity(
            {"pass_yd": 4200, "pass_td": 28, "pass_int": 10, "rush_yd": 150, "rush_td": 2},
            {"pass_yd": 0.04, "pass_td": 4, "pass_int": -1, "rush_yd": 0.1, "rush_td": 6},
        )

    def test_ppr_receiving_shaped_projection(self):
        self._assert_parity(
            {"rec": 95, "rec_yd": 1200, "rec_td": 9, "fum_lost": 1},
            {"rec": 1, "rec_yd": 0.1, "rec_td": 6, "fum_lost": -2},
        )

    def test_idp_shaped_projection(self):
        self._assert_parity(
            {"idp_tkl_solo": 4.2, "idp_tkl_ast": 1.1, "idp_sack": 0.4, "idp_int": 0.05},
            {"idp_tkl_solo": 1, "idp_tkl_ast": 0.5, "idp_sack": 4, "idp_int": 6},
        )

    def test_nonstandard_scoring_axes_projection(self):
        # The exact "unsupported by CDME today" axes from the scoring-propagation sweep --
        # parity must hold here too, since these are the categories most likely to be added
        # to one function's supported set without the other.
        self._assert_parity(
            {"bonus_rec_te": 3, "rec_first_down": 12, "rush_first_down": 4, "kr_yd": 180},
            {"bonus_rec_te": 0.5, "rec_first_down": 0.5, "rush_first_down": 0.5, "kr_yd": 0.02},
        )

    def test_category_present_only_in_stats_contributes_zero_on_both_sides(self):
        self._assert_parity({"pass_yd": 300, "made_up_category": 999}, {"pass_yd": 0.04})

    def test_category_present_only_in_scoring_contributes_zero_on_both_sides(self):
        self._assert_parity({"pass_yd": 300}, {"pass_yd": 0.04, "rec": 1})

    def test_zero_stat_value_contributes_nothing_on_both_sides(self):
        self._assert_parity({"fum_lost": 0, "pass_yd": 100}, {"fum_lost": -2, "pass_yd": 0.04})

    def test_empty_stats_is_zero_on_both_sides(self):
        self._assert_parity({}, {"pass_yd": 0.04, "rec": 1})

    def test_none_stats_is_a_safe_zero_on_both_sides(self):
        # score_projection's own `(stats or {}).items()` guard makes this safe -- unlike
        # scoring_settings (see the class docstring below), a None stats dict is defended
        # internally by both functions, not just by every current caller.
        self._assert_parity(None, {"pass_yd": 0.04})


class ScoreProjectionNoneScoringSettingsAsymmetryTests(unittest.TestCase):
    """Not a parity failure, but a real, deliberate asymmetry worth pinning down: unlike
    compute_points_from_stats, score_projection has no internal `(scoring_settings or {})`
    guard -- `scoring_settings.get(...)` is called directly. Confirmed harmless today only
    because every real call site guards it externally instead (draft_room.py:395 gates the
    call on `scoring_settings is not None`; player_universe.py's own internal call passes
    `scoring_settings or {}`). This test documents that a bare None currently raises, so a
    future caller that skips the external guard fails loudly instead of silently drifting
    from compute_points_from_stats' None-safe behavior."""

    def test_compute_points_from_stats_tolerates_none_scoring_settings(self):
        self.assertEqual(sc.compute_points_from_stats({"pass_yd": 100}, None), 0.0)

    def test_score_projection_raises_on_bare_none_scoring_settings(self):
        with self.assertRaises(AttributeError):
            pu.score_projection({"pass_yd": 100}, None)


if __name__ == "__main__":
    unittest.main()
