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
