"""Regression guard for the DataMerger league_format harness bug (see run_draft_validation.py's
own module docstring for the full story: a merger built with no format hint resolves a player
appearing in more than one format-specific Dynasty Rankings export by raw file mtime, not by
the trial's own real league -- confirmed to actually flip a real trajectory pick with zero
production-code difference).

data_merger.py's own mechanism (_rankings_format_match_score, set_league_format, the format_hint
reordering in load_all) is already covered by test_data_merger.py -- what was missing, and what
this file exists to make impossible to silently reintroduce, is every simulation-harness
driver's OWN habit of building a merger and forgetting to pass the hint at all. Each fixed
driver's _build_pool_players_db helper was changed from a zero-arg function that built its own
un-hinted DataMerger internally to a function that REQUIRES a caller-supplied merger -- a
structural guarantee, not a style preference: it is no longer possible to call these helpers
without having already decided what format hint to use. This file pins that signature shape so
a future edit reverting to the old zero-arg pattern fails a test immediately instead of
silently reintroducing the exact bug that caused a real trajectory divergence."""

from __future__ import annotations

import inspect
import unittest

MODULES_WITH_A_FORMAT_HINTED_HELPER = (
    "run_draft_validation",
    "run_counterfactual_analysis",
    "run_denial_semantics_audit",
    "run_denial_ablation_experiment",
    "run_out_of_sample_validation",
    "verify_denial_boundary_change",
    "compare_baseline_pre_post_95d2111",
    "run_95d2111_effect_report",
)


class BuildPoolPlayersDbRequiresAMergerArgumentTests(unittest.TestCase):
    """Every harness driver's own _build_pool_players_db must take a merger as its first
    required positional argument -- the caller decides the DataMerger (and therefore its
    league_format), the helper never builds one internally. A helper callable with zero
    arguments is exactly the shape of the original bug."""

    def test_every_known_harness_module_requires_a_merger_argument(self):
        for mod_name in MODULES_WITH_A_FORMAT_HINTED_HELPER:
            with self.subTest(module=mod_name):
                mod = __import__(mod_name)
                self.assertTrue(
                    hasattr(mod, "_build_pool_players_db"),
                    f"{mod_name} no longer defines _build_pool_players_db -- update this test's module list",
                )
                sig = inspect.signature(mod._build_pool_players_db)
                params = list(sig.parameters.values())
                self.assertGreaterEqual(
                    len(params), 1,
                    f"{mod_name}._build_pool_players_db takes no arguments -- it can only be "
                    "building its own un-hinted DataMerger internally again, the exact bug "
                    "this test exists to catch.",
                )
                first = params[0]
                self.assertEqual(
                    first.default, inspect.Parameter.empty,
                    f"{mod_name}._build_pool_players_db's first parameter has a default, so it "
                    "can be called with zero arguments -- it must be required, forcing every "
                    "caller to supply a merger (and therefore decide its league_format) "
                    "explicitly.",
                )


if __name__ == "__main__":
    unittest.main()
