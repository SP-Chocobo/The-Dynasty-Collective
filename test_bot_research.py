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
        self.assertEqual(findings[0]["composite_impact"], "low-weight input")

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


if __name__ == "__main__":
    unittest.main()
