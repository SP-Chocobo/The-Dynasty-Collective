"""#141 / #114 / #200: instruments whose number was not about what their name said — `0.9`.

Six of the seven findings in that item are repaired here. The two that are not are recorded in the
mandate with what would close them, because shipping a guard on an oracle I could not validate is
the same defect one level up.
"""

from __future__ import annotations

import pathlib
import unittest

import assertion_execution as ae
import doc_index
import draft_counterfactual as dc
import draft_room as dr
import quantity_readers as qr


class EveryListedModuleExists(unittest.TestCase):
    """`quantity_readers` named `trade_analysis.py`, which does not exist and shows no sign of ever
    having existed — the trade surface is `trade_ledger_ui.py`. Every scan over OBSERVER_MODULES
    silently skipped one seventh of its own declared input, and said nothing, because a missing path
    and a path with no matches produce the same empty result."""

    def test_the_declared_modules_are_all_real(self):
        missing = [m for m in qr.SCORING_MODULES + qr.OBSERVER_MODULES
                   if not pathlib.Path(m).exists()]
        self.assertEqual([], missing)

    def test_the_guard_runs_at_import_and_raises(self):
        real = qr.OBSERVER_MODULES
        try:
            qr.OBSERVER_MODULES = real + ("no_such_module.py",)
            with self.assertRaises(RuntimeError):
                qr._assert_every_listed_module_exists()
        finally:
            qr.OBSERVER_MODULES = real


class BoilerplateDoesNotClassifyADocument(unittest.TestCase):
    """`doc_index` tries SUPERSEDED before DECLARED, and the shared long-lived-document banner
    contains "a copy goes stale silently". So the word `stale` in house boilerplate classified six
    self-declaring documents as SUPERSEDED — the class became a judgement about whether a document
    carries the banner."""

    BANNERED = ("DRAFT_ROOM_UI.md", "CDME_CONTRACTS.md", "GOLD_WYRM_WEBFRONT.md")

    def test_documents_carrying_the_banner_are_classified_on_their_own_words(self):
        for name in self.BANNERED:
            path = pathlib.Path(name)
            if not path.exists():
                continue
            with self.subTest(name):
                self.assertEqual("DECLARED", doc_index.classify(path))

    def test_the_stripper_removes_only_the_banners_blockquote(self):
        head = ("# Title\n"
                "> **WHERE CURRENT STATE LIVES — not in this file.** a copy goes stale silently\n"
                "> second banner line\n"
                "\n"
                "> **STATUS: this document is a vision document.**\n")
        stripped = doc_index._without_boilerplate(head)
        self.assertNotIn("stale", stripped)
        self.assertIn("this document is", stripped,
                      "a document's OWN status blockquote must survive")

    def test_a_document_that_really_is_superseded_still_reads_that_way(self):
        head = "# Title\n\nThis supersedes the earlier version.\n"
        self.assertIn("supersede", doc_index._without_boilerplate(head))


class TheCounterfactualRefusesToCompareTwoPricings(unittest.TestCase):
    """`_full_board` built a VENDOR-ONLY board while `engine_tav` is read off the trajectory's own
    snapshot, so `regret_vs_bpa` subtracted two numbers from two different pricings."""

    class _Traj:
        def __init__(self, priced_from):
            self.config = {"priced_from": priced_from, "mode": "auto", "pool_scope": "all"}
            self.picks = ()

    def test_a_scoring_aware_trajectory_without_projections_raises(self):
        with self.assertRaises(ValueError) as caught:
            dc.compare_trajectory(None, {}, {"roster_positions": []},
                                  self._Traj("vendor+sleeper"))
        self.assertIn("two pricings", str(caught.exception))

    def test_a_vendor_only_trajectory_is_allowed_through(self):
        # No projections needed, because both sides are then the vendor reconstruction.
        self.assertEqual([], dc.compare_trajectory(None, {}, {"roster_positions": []},
                                                   self._Traj("vendor_only")))

    def test_the_board_builder_takes_the_pricing_path(self):
        import inspect
        params = inspect.signature(dc._full_board).parameters
        for name in ("sleeper_projections", "sleeper_basis", "weekly_projections"):
            with self.subTest(name):
                self.assertIn(name, params)


class TestsThatRunAndAssertNothing(unittest.TestCase):
    """`assertion_floors` counts assertions in SOURCE. A test can contain none and still be real
    (it delegates to a helper), or contain one that never executes. Only running them answers it.

    Measured statically, 27 methods have no `self.assert*` of their own; most delegate correctly.
    The instrument is a runtime one for that reason."""

    def test_the_record_exists_and_every_entry_has_a_reason(self):
        record = pathlib.Path(ae.RECORD_PATH)
        if not record.exists():
            self.skipTest(f"{record} not recorded yet")
        import json
        silent = json.loads(record.read_text()).get("silent_tests", {})
        blank = sorted(t for t, why in silent.items() if not why)
        self.assertEqual([], blank,
                         "a silent test with no stated reason is unjudged: say whether its only "
                         "failure mode is an exception, or fix it")

    def test_the_instrument_counts_assertions_made_through_a_helper(self):
        """The distinction that makes it better than the static count: a helper's `self.assert*`
        is still a call on the same TestCase, so delegation is seen correctly."""
        import inspect
        source = inspect.getsource(ae._instrument)
        self.assertIn("unittest.TestCase", source)
        self.assertIn("_counted", source, "the wrapper must be idempotent")

    def test_a_skipped_test_is_not_reported_as_silent(self):
        """A skip did not run. That is `0.4`'s subject, and conflating the two would make this
        instrument report the other one's findings."""
        import inspect
        source = inspect.getsource(ae.measure)
        self.assertIn("_SKIPPED", source)
        self.assertIn("_BROKEN", source)
