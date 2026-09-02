"""suite_taxonomy must stay true about the suite it describes.

A taxonomy that quietly falls behind is worse than none: it answers coverage questions
confidently and wrongly, which is the exact defect class ENGINEERING_DOCTRINE's proof-case
section is about. These tests are what stop that -- every check here fails LOUDLY when a new
test module appears without a home, rather than letting it drop out of every query.
"""

import os
import unittest

import suite_taxonomy as tax


class EveryModuleHasAHome(unittest.TestCase):
    def test_the_suite_is_not_empty(self):
        # Guards every assertion below: an empty discovery would make them all vacuous.
        self.assertGreater(len(tax.modules()), 50)

    def test_every_module_resolves_to_a_subject_or_a_contract(self):
        homeless = [m for m in tax.modules()
                    if not tax.subject_of(m) and not tax.contracts_of(m)]
        self.assertEqual(homeless, [], (
            "these test modules answer to nothing -- give the module a docstring citing its "
            "audit section (§14) or register item (#114), or add a row to "
            "suite_taxonomy._UNMARKED"))

    def test_every_module_lands_in_exactly_one_tier(self):
        fast, full = set(tax.by_tier(tax.TIER_FAST)), set(tax.by_tier(tax.TIER_FULL))
        self.assertEqual(fast & full, set())
        self.assertEqual(fast | full, set(tax.modules()))

    def test_both_tiers_are_substantial(self):
        # A tier that collapses to nothing would make the CI split meaningless while still
        # reporting green, so the shape is pinned rather than assumed.
        self.assertGreater(len(tax.by_tier(tax.TIER_FAST)), 20)
        self.assertGreater(len(tax.by_tier(tax.TIER_FULL)), 10)

    def test_the_unmarked_table_carries_no_dead_rows(self):
        live = {m[5:] for m in tax.modules()}
        dead = sorted(set(tax._UNMARKED) - live)
        self.assertEqual(dead, [], "suite_taxonomy._UNMARKED names modules that no longer exist")

    def test_the_unmarked_table_holds_only_modules_that_need_it(self):
        # A row here for a module that already resolves on its own is a second, competing
        # answer to the same question -- the concept-duplication this repo fights everywhere.
        redundant = sorted(
            name for name in tax._UNMARKED
            if tax.subject_of(f"test_{name}")
            or tax._SECTION.search(_doc(f"test_{name}"))
            or tax._REGISTER.search(_doc(f"test_{name}")))
        self.assertEqual(redundant, [], "these resolve without the table; drop their rows")

    def test_a_named_subject_really_is_a_production_module(self):
        for module in tax.modules():
            subject = tax.subject_of(module)
            if subject is not None:
                self.assertTrue(os.path.exists(f"{subject}.py"), module)


def _doc(module):
    import ast
    path = f"{module}.py"
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        source = handle.read()
    try:
        return ast.get_docstring(ast.parse(source)) or ""
    except SyntaxError:
        return ""


class TierDetectionIsRealNotDeclared(unittest.TestCase):
    def test_a_module_building_a_real_merger_is_full_tier(self):
        # The detection rule itself, pinned against a known member of each tier so that a
        # change to the rule cannot silently reshuffle the suite.
        self.assertEqual(tax.tier_of("test_survival_evidence"), tax.TIER_FULL)
        self.assertEqual(tax.tier_of("test_suite_taxonomy"), tax.TIER_FAST)


if __name__ == "__main__":
    unittest.main()
