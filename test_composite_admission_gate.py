"""§7.4 + §6.2a: the two gates between a model's assertion and a score, and what each can prove.

WHY ONE FILE FOR TWO SECTIONS. They land on the same function and the same downstream consumer
because they are the same boundary asked twice -- §7.4 asks WHICH SOURCES may move a number,
§6.2a asks WHO HAS TO AGREE before one does. Testing them apart would let each look sufficient.

THE PROPERTY THAT MATTERS MOST is the one in `NothingIsSuppressedTests`: neither gate deletes,
hides, or edits anything. The ruling was *allowlist what feeds the composite; prose stays free*,
and a gate that quietly became a filter on what the panel can say would be a different decision
than the one that was made.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import bot_research
import data_merger as dm
import source_policy

_HERE = Path(__file__).parent


class _Store(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, bot_research, "FINDINGS_PATH", self._orig)


class BothGatesAreRequiredTests(_Store):
    """AND, not OR. Each of the three ways to fail is asserted separately, because they are
    different facts about the finding and a caller has to be able to tell them apart."""

    def _impact(self, source, rank, confirm):
        finding_id = bot_research.add_finding("Some Player", source, "a claim", rank=rank)
        if confirm:
            bot_research.confirm_finding(finding_id)
        return bot_research.load_findings()[0]["composite_impact"]

    def test_allowlisted_and_confirmed_is_the_only_combination_that_counts(self):
        self.assertEqual(self._impact("ESPN", 3, True), "low-weight input")

    def test_allowlisted_but_unconfirmed_does_not_count(self):
        self.assertEqual(self._impact("ESPN", 3, False),
                         "none -- awaiting a second adjudication")

    def test_confirmed_but_not_allowlisted_does_not_count(self):
        self.assertEqual(self._impact("an anonymous forum post", 3, True),
                         "none -- cited source is not on the composite allowlist")

    def test_a_qualitative_claim_is_unchanged_by_either_gate(self):
        """It never had a number to gate. The reason it reads "none" is the reason it always
        was, and conflating that with a refusal would misdescribe the row."""
        self.assertEqual(self._impact("ESPN", None, True), "none")


class TheFilterReachesTheComposite(_Store):
    """The gates are only worth anything if `load_bot_research_as_external` honours them --
    otherwise they are a label on a row that still feeds a score."""

    def test_an_unconfirmed_finding_never_enters_external_values(self):
        bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        self.assertTrue(dm.load_bot_research_as_external().empty)

    def test_a_finding_citing_an_unlisted_source_never_enters_external_values(self):
        finding_id = bot_research.add_finding("Some Player", "totally-not-a-real-site.example",
                                              "a claim", rank=3)
        bot_research.confirm_finding(finding_id)
        self.assertTrue(dm.load_bot_research_as_external().empty)

    def test_a_finding_that_clears_both_does_enter_so_the_two_above_are_not_vacuous(self):
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        bot_research.confirm_finding(finding_id)
        frame = dm.load_bot_research_as_external()
        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.iloc[0]["rank"], 3)

    def test_eligibility_is_recomputed_not_read_off_the_stored_label(self):
        """A row written under an older rule must not carry its old eligibility forward just
        because the string is still sitting in the file. Same discipline as recomputing a
        manifest rather than believing it."""
        bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        entries = bot_research.load_findings()
        entries[0]["composite_impact"] = "low-weight input"  # a lie, planted directly
        bot_research._save(bot_research.FINDINGS_PATH, entries)
        self.assertFalse(bot_research.feeds_composite(entries[0]))
        self.assertTrue(dm.load_bot_research_as_external().empty)


class NothingIsSuppressedTests(_Store):
    """'Prose stays free.' A blocked finding is still a full member of the research record."""

    def test_a_blocked_finding_is_still_stored_in_full(self):
        bot_research.add_finding("Some Player", "an anonymous forum post",
                                 "a specific claim worth reading", rank=3)
        entry = bot_research.load_findings()[0]
        self.assertEqual(entry["claim"], "a specific claim worth reading")
        self.assertEqual(entry["source"], "an anonymous forum post")
        self.assertEqual(entry["rank"], 3, "the number is kept, it just does not count")

    def test_a_blocked_finding_still_reaches_the_panel_as_context(self):
        """The chairs read findings_for_context. If the gate filtered that too, it would be
        censoring the debate rather than the arithmetic -- a different decision entirely."""
        bot_research.add_finding("Some Player", "an anonymous forum post", "a claim", rank=3)
        self.assertEqual(len(bot_research.findings_for_context()), 1)

    def test_comparisons_are_untouched_by_either_gate(self):
        """A relative claim has no absolute number, so there is nothing for either gate to hold
        back -- and adding one would be scope the ruling did not grant."""
        import inspect
        source = inspect.getsource(bot_research.add_comparison)
        self.assertNotIn("composite_eligibility", source)
        self.assertNotIn("source_policy", source)


class TheThreeStatesOfAdjudicationTests(_Store):
    def test_a_row_predating_the_gate_is_unrecorded_not_unconfirmed(self):
        """#112's distinction again: 'never adjudicated' and 'adjudicated and not confirmed' are
        different facts. Both block, and a reader must still be able to tell them apart."""
        legacy = {"id": 1, "ts": 1.0, "date": "2026-01-01", "player_name": "P",
                  "source": "ESPN", "claim": "c", "rank": 3}
        self.assertIsNone(legacy.get("adjudication"))
        self.assertIs(bot_research.ADJUDICATION_UNRECORDED, None)
        self.assertFalse(bot_research.feeds_composite(legacy))

    def test_confirming_records_who_and_when_without_claiming_verification(self):
        """#89's rule: a stored field may not claim a certainty its writing path cannot
        establish. Nothing here checked the source, so nothing here says "verified"."""
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        entry = bot_research.confirm_finding(finding_id)
        self.assertEqual(entry["confirmed_by"], "human")
        self.assertIn("confirmed_at", entry)
        for overclaim in ("verified", "validated", "true", "correct"):
            self.assertNotIn(overclaim, entry)


class TheGateDoesNotAssumeADeploymentTests(unittest.TestCase):
    """WARPATH's standing rule: build the mechanism, do not let it imply the deployment. Both
    sections are partial answers to ROADMAP's self-declared biggest unresolved tension, and the
    vendor defaults this session unwound are what accretion looks like."""

    def test_the_second_adjudicator_is_a_person_and_no_automatic_path_exists(self):
        """A stronger model or a corroboration threshold is a legitimate future adjudicator --
        ROADMAP names four candidates and picks none. Adding one here would settle the
        deployment question sideways."""
        source = (_HERE / "bot_research.py").read_text()
        for forbidden in ("auto_confirm", "confirm_all", "def confirm_findings("):
            self.assertNotIn(forbidden, source, forbidden)

    def test_nothing_in_the_gate_reads_or_writes_anything_shared(self):
        """It behaves identically on a local install and a hosted one, which is the test of
        whether a mechanism has smuggled in a deployment assumption."""
        import inspect
        for fn in (bot_research.composite_eligibility, bot_research.feeds_composite,
                   bot_research.confirm_finding, source_policy.admits):
            with self.subTest(fn=fn.__name__):
                body = inspect.getsource(fn)
                for forbidden in ("requests", "urlopen", "http", "upload", "sync"):
                    self.assertNotIn(forbidden, body, f"{fn.__name__}: {forbidden}")


if __name__ == "__main__":
    unittest.main()


class RetractionIsNotDeletionTests(_Store):
    """§6's missing lifecycle half, and the floor under every future relaxation of the gate.

    6.2a's gate is safe because its default is to WITHHOLD -- a number does not count until
    somebody says so. The moment anything accepts without a person (a provisional "assume this
    for my next pick", a second panel, a threshold), the default flips to ADMIT, and a system
    that can admit without a person and cannot un-admit has no floor. That is why this ships
    ahead of any acceptance automation rather than after it.
    """

    def _confirmed(self, source="ESPN", rank=3):
        finding_id = bot_research.add_finding("Some Player", source, "a claim", rank=rank)
        bot_research.confirm_finding(finding_id)
        return finding_id

    def test_a_retracted_finding_stops_counting(self):
        finding_id = self._confirmed()
        self.assertTrue(bot_research.feeds_composite(bot_research.load_findings()[0]))
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        row = bot_research.load_findings()[0]
        self.assertFalse(bot_research.feeds_composite(row))
        self.assertEqual(row["composite_impact"], "none -- retracted (rejected)")

    def test_the_claim_itself_survives_intact(self):
        """Retraction is not deletion. A claim that turned out to be wrong is information, and
        deleting it makes the same mistake re-acceptable by the next person who looks."""
        finding_id = self._confirmed()
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_SUPERSEDED)
        row = bot_research.load_findings()[0]
        self.assertEqual(row["claim"], "a claim")
        self.assertEqual(row["rank"], 3)
        self.assertEqual(row["source"], "ESPN")
        self.assertEqual(len(bot_research.load_findings()), 1)

    def test_retraction_is_orthogonal_to_adjudication_and_preserves_the_history(self):
        """The distinction a single collapsed state would destroy: "confirmed, then rejected" and
        "never confirmed" are different histories, and the first is the one worth knowing."""
        finding_id = self._confirmed()
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        row = bot_research.load_findings()[0]
        self.assertEqual(row["adjudication"], bot_research.ADJUDICATION_HUMAN_CONFIRMED)
        self.assertEqual(row["retracted"]["reason"], bot_research.RETRACTED_REJECTED)

    def test_a_retracted_finding_leaves_the_pending_queue(self):
        """It is not waiting on anybody. Leaving it there would ask a person to adjudicate
        something already decided against."""
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        self.assertEqual(len(bot_research.findings_awaiting_adjudication()), 1)
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        self.assertEqual(bot_research.findings_awaiting_adjudication(), [])
        self.assertEqual([f["id"] for f in bot_research.retracted_findings()], [finding_id])

    def test_an_unrecognised_reason_is_refused_rather_than_stored(self):
        """"Retracted for reasons unknown" is the row that gets re-accepted later by somebody
        who cannot tell what went wrong."""
        finding_id = self._confirmed()
        self.assertIsNone(bot_research.retract_finding(finding_id, "because"))
        self.assertNotIn("retracted", bot_research.load_findings()[0])
        self.assertTrue(bot_research.feeds_composite(bot_research.load_findings()[0]))

    def test_it_records_who_and_when_and_an_optional_note(self):
        finding_id = self._confirmed()
        row = bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED,
                                           by="server", note="second panel disagreed")
        self.assertEqual(row["retracted"]["by"], "server")
        self.assertEqual(row["retracted"]["note"], "second panel disagreed")
        self.assertIn("at", row["retracted"])

    def test_retracting_something_that_does_not_exist_is_a_no_op(self):
        self.assertIsNone(bot_research.retract_finding(9999, bot_research.RETRACTED_REJECTED))


class RestoringIsNotGrantingTests(_Store):
    def test_restore_returns_a_finding_to_the_state_it_already_held(self):
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        bot_research.confirm_finding(finding_id)
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_WITHDRAWN)
        row = bot_research.restore_finding(finding_id)
        self.assertNotIn("retracted", row)
        self.assertEqual(row["composite_impact"], "low-weight input")

    def test_restoring_an_unconfirmed_finding_does_NOT_make_it_count(self):
        """The trap: "undo" must only touch the axis the retraction took away. A restore that
        also confirmed would be a grant wearing an undo's clothes."""
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        row = bot_research.restore_finding(finding_id)
        self.assertEqual(row["composite_impact"], "none -- awaiting a second adjudication")
        self.assertFalse(bot_research.feeds_composite(row))

    def test_restoring_something_not_retracted_is_a_no_op(self):
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        self.assertIsNone(bot_research.restore_finding(finding_id))


class TheRecomputePathIsTheOrdinaryOneTests(_Store):
    """There is deliberately no cache invalidation to keep in sync -- because there is no cache.
    Every DataMerger construction re-reads the store through `feeds_composite`, so a retraction
    propagates by the same route an addition does."""

    def test_a_retraction_removes_the_row_from_external_values_on_the_next_build(self):
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        bot_research.confirm_finding(finding_id)
        self.assertEqual(len(dm.load_bot_research_as_external()), 1)
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        self.assertTrue(dm.load_bot_research_as_external().empty)

    def test_and_a_restore_brings_it_back_by_the_same_route(self):
        finding_id = bot_research.add_finding("Some Player", "ESPN", "a claim", rank=3)
        bot_research.confirm_finding(finding_id)
        bot_research.retract_finding(finding_id, bot_research.RETRACTED_REJECTED)
        bot_research.restore_finding(finding_id)
        self.assertEqual(len(dm.load_bot_research_as_external()), 1)


class RetractionReachesTheScreenTests(unittest.TestCase):
    def test_the_panel_offers_retraction_and_lists_what_is_retracted(self):
        app = (_HERE / "app.py").read_text()
        self.assertIn("bot_research.retract_finding(", app)
        self.assertIn("bot_research.retracted_findings()", app)
        self.assertIn("bot_research.restore_finding(", app)

    def test_retracted_findings_are_shown_rather_than_hidden(self):
        """A retraction nobody can see is indistinguishable from a deletion, which defeats the
        reason for retracting instead of deleting."""
        app = (_HERE / "app.py").read_text()
        self.assertIn("Retracted (", app)
