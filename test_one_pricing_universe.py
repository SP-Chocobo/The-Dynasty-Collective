"""#214/F2: the strategic numbers must be priced the same way the value beside them is.

THE DEFECT. `build_snapshot` computes its board WITH `sleeper_projections`, then called
`pick_analysis`, which took no such argument and rebuilt BOTH "my board" and every rival board
VENDOR-ONLY. The snapshot then packaged `universal_value` / `team_acquisition_value` from the
scoring-aware world beside `survival_probability`, `opportunity_cost`, `denial_value`,
`rival_premium` and `positional_forfeit` from the vendor-only one, and presented the result as
one decomposition of one candidate.

MEASURED on the real capture, round one, 12-team PPR, production arguments:

    vendor-only (old)     19 of 19 comparable candidates disagreed, worst gap 65.16
    scoring-aware (fix)    0 of 20

This is #204's identical gap one layer up. #204 threaded pricing from the battery into
build_snapshot and stopped at the boundary where the measurement had been taken -- which is the
pattern this repair is really about.
"""

from __future__ import annotations

import inspect
import unittest

import draft_strategy as ds
import pick_synthesis


class PickAnalysisCanBePricedLikeItsCallerTests(unittest.TestCase):

    def test_pick_analysis_accepts_the_pricing_arguments(self):
        params = inspect.signature(ds.pick_analysis).parameters
        self.assertIn("sleeper_projections", params)
        self.assertIn("sleeper_basis", params)

    def test_opponent_boards_accept_them_too(self):
        """Rival boards decide denial_value and rival_premium. A rival board priced differently
        from my own answers 'what would HE pay' in a currency he does not use."""
        params = inspect.signature(ds._build_opponent_boards).parameters
        self.assertIn("sleeper_projections", params)
        self.assertIn("sleeper_basis", params)

    def test_both_board_builds_inside_pick_analysis_forward_the_pricing(self):
        src = inspect.getsource(ds.pick_analysis)
        self.assertIn("sleeper_projections=sleeper_projections", src)
        self.assertIn("sleeper_basis=sleeper_basis", src)
        self.assertEqual(src.count("sleeper_projections=sleeper_projections"), 2,
                         "my_board AND the opponent boards -- fixing one is the half-repair "
                         "this whole item is about")

    def test_the_opponent_board_builder_forwards_it_to_compute_draft_board(self):
        src = inspect.getsource(ds._build_opponent_boards)
        self.assertIn("sleeper_projections=sleeper_projections", src)
        self.assertIn("sleeper_basis=sleeper_basis", src)

    def test_the_default_is_still_vendor_only_so_no_caller_changes_silently(self):
        params = inspect.signature(ds.pick_analysis).parameters
        self.assertIsNone(params["sleeper_projections"].default)
        self.assertEqual(params["sleeper_basis"].default, ds.SLEEPER_BASIS_WEEKLY)


class TheSnapshotHandsItsPricingDownTests(unittest.TestCase):

    def test_build_snapshot_passes_its_own_pricing_to_pick_analysis(self):
        src = inspect.getsource(pick_synthesis.build_snapshot)
        call = src[src.index("ds.pick_analysis("):]
        call = call[:call.index(")")]
        self.assertIn("sleeper_projections=sleeper_projections", call,
                      "the snapshot's own board is priced with these; the strategic numbers "
                      "beside it must be too")
        self.assertIn("sleeper_basis=sleeper_basis", call)


if __name__ == "__main__":
    unittest.main()
