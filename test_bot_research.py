import shutil
import tempfile
import unittest
from pathlib import Path

import bot_research


class BotResearchTests(unittest.TestCase):
    """Points FINDINGS_PATH/COMPARISONS_PATH at a throwaway temp directory for the duration of
    each test, never touching the real committed data/baseline/bot_research.json or
    bot_comparisons.json -- these are real, git-tracked application data, not test fixtures."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_findings_path = bot_research.FINDINGS_PATH
        self._orig_comparisons_path = bot_research.COMPARISONS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"
        bot_research.COMPARISONS_PATH = Path(self._tmpdir) / "bot_comparisons.json"

    def tearDown(self):
        bot_research.FINDINGS_PATH = self._orig_findings_path
        bot_research.COMPARISONS_PATH = self._orig_comparisons_path
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    # -- findings --------------------------------------------------------------------------

    def test_load_findings_on_missing_file_is_empty_list(self):
        self.assertEqual(bot_research.load_findings(), [])

    def test_add_finding_with_rank_round_trips(self):
        new_id = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1, conviction="Unanimous")
        self.assertIsNotNone(new_id)
        findings = bot_research.load_findings()
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["player_name"], "Maxx Crosby")
        self.assertEqual(findings[0]["rank"], 1)
        # 6.2a: a rank-bearing finding is NOT born feeding the composite any more. It used to
        # read "low-weight input" here, on the Moderator's own say-so.
        self.assertEqual(findings[0]["composite_impact"], "none -- awaiting a second adjudication")
        self.assertEqual(findings[0]["adjudication"], bot_research.ADJUDICATION_PANEL_ONLY)

    def test_a_confirmed_finding_becomes_a_low_weight_composite_input(self):
        """The other side of the gate, so the test above is not just measuring a refusal."""
        new_id = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        updated = bot_research.confirm_finding(new_id)
        self.assertEqual(updated["composite_impact"], "low-weight input")
        self.assertEqual(updated["adjudication"], bot_research.ADJUDICATION_HUMAN_CONFIRMED)
        self.assertEqual(updated["confirmed_by"], "human")
        self.assertTrue(bot_research.feeds_composite(bot_research.load_findings()[0]))

    def test_confirming_an_unlisted_cited_source_still_does_not_admit_it(self):
        """7.4 and 6.2a are AND, not OR. A person confirming a finding does not promote the
        source it cites -- the allowlist is a policy about sources, not about diligence."""
        new_id = bot_research.add_finding("Maxx Crosby", "an anonymous forum post",
                                          "ranked #1 DL", rank=1)
        updated = bot_research.confirm_finding(new_id)
        self.assertIsNone(updated["cited_source_admitted"])
        self.assertEqual(updated["composite_impact"],
                         "none -- cited source is not on the composite allowlist")
        self.assertFalse(bot_research.feeds_composite(updated))

    def test_confirming_an_unknown_id_is_a_no_op_rather_than_an_error(self):
        self.assertIsNone(bot_research.confirm_finding(9999))

    def test_confirming_twice_is_idempotent(self):
        """The caller is a UI button; a double-click is not a fact about the finding."""
        new_id = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        first = bot_research.confirm_finding(new_id)
        second = bot_research.confirm_finding(new_id)
        self.assertEqual(first["composite_impact"], second["composite_impact"])
        self.assertEqual(len(bot_research.load_findings()), 1)

    def test_the_pending_queue_holds_only_rank_bearing_findings_that_do_not_count(self):
        """A qualitative claim was never going to feed the composite, so it is not WAITING for
        anything -- putting it in the queue would ask a person to adjudicate a number that does
        not exist."""
        blocked = bot_research.add_finding("A", "ESPN", "ranked #4", rank=4)
        bot_research.add_finding("B", "ESPN", "trending up", rank=None)
        unlisted = bot_research.add_finding("C", "some blog", "ranked #9", rank=9)
        confirmed = bot_research.add_finding("D", "ESPN", "ranked #2", rank=2)
        bot_research.confirm_finding(confirmed)
        self.assertEqual({f["id"] for f in bot_research.findings_awaiting_adjudication()},
                         {blocked, unlisted})

    def test_add_finding_without_rank_marks_no_composite_impact(self):
        bot_research.add_finding("Maxx Crosby", "ESPN", "trending up lately", rank=None)
        findings = bot_research.load_findings()
        self.assertEqual(findings[0]["composite_impact"], "none")

    def test_add_finding_rejects_blank_fields(self):
        self.assertIsNone(bot_research.add_finding("", "ESPN", "claim"))
        self.assertIsNone(bot_research.add_finding("Player", "", "claim"))
        self.assertIsNone(bot_research.add_finding("Player", "ESPN", "   "))
        self.assertEqual(bot_research.load_findings(), [])

    def test_ids_increment_and_never_reused(self):
        id1 = bot_research.add_finding("A", "ESPN", "claim1")
        id2 = bot_research.add_finding("B", "ESPN", "claim2")
        self.assertEqual(id2, id1 + 1)

    def test_findings_for_context_is_newest_first_and_capped(self):
        for i in range(5):
            bot_research.add_finding(f"Player {i}", "ESPN", f"claim {i}")
        capped = bot_research.findings_for_context(limit=2)
        self.assertEqual(len(capped), 2)
        self.assertEqual(capped[0]["player_name"], "Player 4")
        self.assertEqual(capped[1]["player_name"], "Player 3")

    def test_findings_are_append_only_not_overwritten(self):
        bot_research.add_finding("Maxx Crosby", "ESPN", "old claim", rank=5)
        bot_research.add_finding("Maxx Crosby", "ESPN", "new claim", rank=1)
        self.assertEqual(len(bot_research.load_findings()), 2)

    def test_exact_same_day_duplicate_is_a_noop_not_a_second_row(self):
        # The bug this exists to prevent: process_moderator_output runs on every Moderator
        # reply, including a follow-up reacting to the same debate -- a re-run /debate or a
        # follow-up restating its own finding would otherwise append an identical row each
        # time, inflating this finding's weight in the composite's percentile pool.
        first_id = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        second_id = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        self.assertEqual(first_id, second_id)
        self.assertEqual(len(bot_research.load_findings()), 1)

    def test_a_genuinely_different_finding_for_the_same_player_still_gets_its_own_row(self):
        bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1)
        bot_research.add_finding("Maxx Crosby", "FantasyPros", "ranked #1 DL", rank=1)
        bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #2 DL", rank=2)
        self.assertEqual(len(bot_research.load_findings()), 3)

    # -- comparisons -------------------------------------------------------------------------

    def test_load_comparisons_on_missing_file_is_empty_list(self):
        self.assertEqual(bot_research.load_comparisons(), [])

    def test_add_comparison_round_trips_with_evidence(self):
        new_id = bot_research.add_comparison(
            "Maxx Crosby", "Aidan Hutchinson", ">", "ESPN",
            context="IDP/DL", evidence="ranked ahead in every analyst ballot",
        )
        self.assertIsNotNone(new_id)
        comparisons = bot_research.load_comparisons()
        self.assertEqual(len(comparisons), 1)
        entry = comparisons[0]
        self.assertEqual(entry["subject"], "Maxx Crosby")
        self.assertEqual(entry["compared_to"], "Aidan Hutchinson")
        self.assertEqual(entry["direction"], ">")
        # The bug caught and fixed this session: evidence text itself must actually be stored,
        # not just the constant evidence_type label.
        self.assertEqual(entry["evidence"], "ranked ahead in every analyst ballot")
        self.assertEqual(entry["composite_impact"], "none")
        # Renamed from "validated" (see add_comparison): the record states what the
        # Moderator asserted, not a verification this code performed.
        self.assertTrue(entry["panel_undisputed"])
        self.assertNotIn("validated", entry)

    def test_exact_same_day_duplicate_comparison_is_a_noop(self):
        first_id = bot_research.add_comparison("Maxx Crosby", "Aidan Hutchinson", ">", "ESPN")
        second_id = bot_research.add_comparison("Maxx Crosby", "Aidan Hutchinson", ">", "ESPN")
        self.assertEqual(first_id, second_id)
        self.assertEqual(len(bot_research.load_comparisons()), 1)

    def test_add_comparison_rejects_invalid_direction(self):
        self.assertIsNone(bot_research.add_comparison("A", "B", "?", "ESPN"))
        self.assertEqual(bot_research.load_comparisons(), [])

    def test_add_comparison_rejects_blank_fields(self):
        self.assertIsNone(bot_research.add_comparison("", "B", ">", "ESPN"))
        self.assertIsNone(bot_research.add_comparison("A", "", ">", "ESPN"))
        self.assertIsNone(bot_research.add_comparison("A", "B", ">", ""))

    def test_comparisons_for_context_is_newest_first_and_capped(self):
        for i in range(5):
            bot_research.add_comparison(f"Player {i}", "Someone Else", ">", "ESPN")
        capped = bot_research.comparisons_for_context(limit=2)
        self.assertEqual(len(capped), 2)
        self.assertEqual(capped[0]["subject"], "Player 4")

    def test_findings_and_comparisons_are_independent_stores(self):
        bot_research.add_finding("A", "ESPN", "claim")
        bot_research.add_comparison("A", "B", ">", "ESPN")
        self.assertEqual(len(bot_research.load_findings()), 1)
        self.assertEqual(len(bot_research.load_comparisons()), 1)


class FindingEvidenceSnapshotTests(unittest.TestCase):
    """#97 / §6.5's evidence snapshot, at the scope the evidence actually supports -- and #106's
    origin field, which turns out to be the same mechanism.

    §6 asked for a URL, a retrieved-at, and an excerpt on every stored finding, so a claim stays
    checkable after its source changes or disappears. The obvious implementation -- add a URL
    field to the Moderator's SOURCE FINDING line -- is the wrong one, and the reason is the whole
    point of the section: a chair ASKED for a citation will produce one whether or not it has
    one. That manufactures provenance rather than recording it, in a store whose ranks feed the
    composite score.

    What is recorded instead is what the PROVIDER RESPONSES reported retrieving, read off their
    own grounding metadata by provider_meter.sources. Two consequences, both deliberate:

      1. The scope is the DEBATE, never the claim. Which page backs a given SOURCE FINDING line
         is a join nothing in this system can make -- the line carries no citation.
      2. "No sources" is UNATTRIBUTED, not "unsourced". It covers a chair reasoning from its
         given context, from its training, a grounding shape this app could not read, and a call
         that never searched. Four different things, and nothing separates them.
    """

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig = bot_research.FINDINGS_PATH
        bot_research.FINDINGS_PATH = Path(self._tmpdir) / "bot_research.json"

    def tearDown(self):
        bot_research.FINDINGS_PATH = self._orig
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _only(self):
        findings = bot_research.load_findings()
        self.assertEqual(len(findings), 1)
        return findings[0]

    def test_a_finding_from_a_debate_that_retrieved_pages_records_them(self):
        pages = [{"url": "https://espn.com/x", "title": "X"},
                 {"url": "https://pff.com/y", "title": "Y"}]
        bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1,
                                 debate_sources=pages)
        evidence = self._only()["evidence"]
        self.assertEqual(evidence["origin"], bot_research.ORIGIN_PANEL_RETRIEVED)
        self.assertEqual(evidence["debate_sources"], pages)
        self.assertTrue(evidence["retrieved_at"])

    def test_a_finding_from_a_debate_that_retrieved_nothing_says_unattributed_not_none(self):
        """The absence rule this whole codebase runs on, at one more boundary: the field is
        present and says UNKNOWN, rather than being omitted or set to an empty claim."""
        for sources in (None, []):
            with self.subTest(sources=sources):
                bot_research.FINDINGS_PATH.unlink(missing_ok=True)
                bot_research.add_finding("A Player", "ESPN", "a claim", debate_sources=sources)
                evidence = self._only()["evidence"]
                self.assertEqual(evidence["origin"], bot_research.ORIGIN_UNATTRIBUTED)
                self.assertEqual(evidence["debate_sources"], [])

    def test_the_two_origins_are_distinguishable_which_is_the_entire_point_of_106(self):
        self.assertNotEqual(bot_research.ORIGIN_PANEL_RETRIEVED,
                            bot_research.ORIGIN_UNATTRIBUTED)

    def test_the_stored_sources_are_a_copy_so_a_later_mutation_cannot_rewrite_history(self):
        pages = [{"url": "https://espn.com/x", "title": "X"}]
        bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", debate_sources=pages)
        pages[0]["url"] = "https://somewhere-else.com"
        self.assertEqual(self._only()["evidence"]["debate_sources"][0]["url"],
                         "https://espn.com/x")

    def test_evidence_is_not_part_of_the_same_day_dedup_key(self):
        """Two identical findings on one day stay one row even if the second debate happened to
        retrieve different pages. The dedup key is the CLAIM; provenance is a property of the
        row, not a second identity for it -- otherwise a re-run /debate would inflate the
        finding's weight in the composite, which is the exact thing the dedup exists to stop."""
        first = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1,
                                         debate_sources=[{"url": "https://a.com", "title": ""}])
        second = bot_research.add_finding("Maxx Crosby", "ESPN", "ranked #1 DL", rank=1,
                                          debate_sources=[{"url": "https://b.com", "title": ""}])
        self.assertEqual(first, second)
        self.assertEqual(len(bot_research.load_findings()), 1)

    def test_a_caller_that_passes_nothing_still_gets_a_well_formed_row(self):
        """Backwards compatibility in the direction that matters: every existing call site keeps
        working, and the row it writes is honest about knowing nothing rather than silently
        lacking the field."""
        bot_research.add_finding("A Player", "ESPN", "a claim")
        self.assertEqual(self._only()["evidence"]["origin"], bot_research.ORIGIN_UNATTRIBUTED)


if __name__ == "__main__":
    unittest.main()
