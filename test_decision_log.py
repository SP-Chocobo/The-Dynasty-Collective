import shutil
import tempfile
import unittest
from pathlib import Path

import decision_log


class DecisionLogTests(unittest.TestCase):
    """Points DECISIONS_DIR at a throwaway temp directory for the duration of each test,
    never touching real per-league data under data/decisions/ -- that's gitignored,
    per-user application state, not test fixtures."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = decision_log.DECISIONS_DIR
        decision_log.DECISIONS_DIR = Path(self._tmpdir)
        self.league_id = "league123"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, decision_log, "DECISIONS_DIR", self._orig_dir)

    # -- log_decision ---------------------------------------------------------------------

    def test_log_decision_round_trips_every_verdict_field(self):
        verdict = {
            "recommendation": "SELL", "conviction": "Majority", "reason": "Price too rich",
            "dissent": "Quant disagreed", "risk": "Miss the return", "recon": "",
            "price_ceiling": "a 2nd", "alternative": "Target Player Y instead",
        }
        decision_log.log_decision(self.league_id, "Should I sell Player X?", verdict, "full text")
        entries = decision_log.load_decisions(self.league_id)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["question"], "Should I sell Player X?")
        self.assertEqual(entry["recommendation"], "SELL")
        self.assertEqual(entry["alternative"], "Target Player Y instead")
        self.assertEqual(entry["moderator_text"], "full text")
        self.assertEqual(entry["outcome"], "")
        self.assertIsNone(entry["outcome_date"])

    def test_missing_verdict_fields_default_to_empty_string(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "text")
        entry = decision_log.load_decisions(self.league_id)[0]
        self.assertEqual(entry["alternative"], "")
        self.assertEqual(entry["dissent"], "")
        self.assertEqual(entry["price_ceiling"], "")

    def test_no_op_without_a_league_id(self):
        decision_log.log_decision("", "q", {"recommendation": "BUY"}, "text")
        self.assertEqual(decision_log.load_decisions(""), [])

    def test_no_op_without_a_verdict(self):
        decision_log.log_decision(self.league_id, "q", {}, "text")
        self.assertEqual(decision_log.load_decisions(self.league_id), [])

    def test_entries_accumulate_across_multiple_calls(self):
        decision_log.log_decision(self.league_id, "q1", {"recommendation": "BUY"}, "t1")
        decision_log.log_decision(self.league_id, "q2", {"recommendation": "SELL"}, "t2")
        self.assertEqual(len(decision_log.load_decisions(self.league_id)), 2)

    def test_leagues_are_independent(self):
        decision_log.log_decision("league_a", "q", {"recommendation": "BUY"}, "t")
        self.assertEqual(decision_log.load_decisions("league_a"), decision_log.load_decisions("league_a"))
        self.assertEqual(decision_log.load_decisions("league_b"), [])

    # -- set_outcome ------------------------------------------------------------------------

    def test_set_outcome_updates_the_matching_entry(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "t")
        ts = decision_log.load_decisions(self.league_id)[0]["ts"]
        ok = decision_log.set_outcome(self.league_id, ts, "Worked", "Traded up big later")
        self.assertTrue(ok)
        entry = decision_log.load_decisions(self.league_id)[0]
        self.assertEqual(entry["outcome"], "Worked")
        self.assertEqual(entry["outcome_note"], "Traded up big later")
        self.assertIsNotNone(entry["outcome_date"])

    def test_set_outcome_on_unknown_ts_returns_false(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "t")
        self.assertFalse(decision_log.set_outcome(self.league_id, 999999.0, "Worked"))

    def test_set_outcome_strips_whitespace_from_note(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "t")
        ts = decision_log.load_decisions(self.league_id)[0]["ts"]
        decision_log.set_outcome(self.league_id, ts, "Mixed", "  had some good, some bad  ")
        self.assertEqual(decision_log.load_decisions(self.league_id)[0]["outcome_note"], "had some good, some bad")

    # -- search_decisions_with_outcomes ------------------------------------------------------

    def test_search_finds_keyword_overlap_in_question_or_reason(self):
        decision_log.log_decision(self.league_id, "Should I trade Bijan Robinson?", {"recommendation": "HOLD", "reason": "elite RB1"}, "t")
        ts = decision_log.load_decisions(self.league_id)[0]["ts"]
        decision_log.set_outcome(self.league_id, ts, "Worked")
        results = decision_log.search_decisions_with_outcomes(self.league_id, "considering trading Bijan Robinson")
        self.assertEqual(len(results), 1)

    def test_search_excludes_entries_with_no_recorded_outcome(self):
        decision_log.log_decision(self.league_id, "Should I trade Bijan Robinson?", {"recommendation": "HOLD"}, "t")
        # No set_outcome call -- this entry has nothing to teach a future decision.
        results = decision_log.search_decisions_with_outcomes(self.league_id, "Bijan Robinson trade")
        self.assertEqual(results, [])

    def test_search_with_no_word_overlap_returns_nothing(self):
        decision_log.log_decision(self.league_id, "Should I trade Bijan Robinson?", {"recommendation": "HOLD"}, "t")
        ts = decision_log.load_decisions(self.league_id)[0]["ts"]
        decision_log.set_outcome(self.league_id, ts, "Worked")
        results = decision_log.search_decisions_with_outcomes(self.league_id, "completely unrelated waiver pickup")
        self.assertEqual(results, [])

    def test_search_with_blank_query_returns_nothing(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "t")
        self.assertEqual(decision_log.search_decisions_with_outcomes(self.league_id, ""), [])
        self.assertEqual(decision_log.search_decisions_with_outcomes(self.league_id, "   "), [])

    def test_search_results_ranked_by_overlap_count(self):
        decision_log.log_decision(self.league_id, "Should I trade my quarterback for picks", {"recommendation": "HOLD"}, "t")
        ts1 = decision_log.load_decisions(self.league_id)[0]["ts"]
        decision_log.set_outcome(self.league_id, ts1, "Worked")
        decision_log.log_decision(self.league_id, "Trade quarterback picks now for future value", {"recommendation": "SELL"}, "t")
        ts2 = decision_log.load_decisions(self.league_id)[1]["ts"]
        decision_log.set_outcome(self.league_id, ts2, "Didn't Work")
        results = decision_log.search_decisions_with_outcomes(self.league_id, "trade quarterback for picks now")
        self.assertEqual(len(results), 2)
        # The second entry shares more words with the query -- it should rank first.
        self.assertEqual(results[0]["ts"], ts2)

    def test_search_respects_limit(self):
        for i in range(10):
            decision_log.log_decision(self.league_id, f"Trade quarterback deal number {i}", {"recommendation": "HOLD"}, "t")
            ts = decision_log.load_decisions(self.league_id)[i]["ts"]
            decision_log.set_outcome(self.league_id, ts, "Worked")
        results = decision_log.search_decisions_with_outcomes(self.league_id, "trade quarterback deal", limit=3)
        self.assertEqual(len(results), 3)

    # -- forget_decisions ---------------------------------------------------------------------

    def test_forget_decisions_deletes_the_league_file(self):
        decision_log.log_decision(self.league_id, "q", {"recommendation": "BUY"}, "t")
        self.assertEqual(len(decision_log.load_decisions(self.league_id)), 1)
        decision_log.forget_decisions(self.league_id)
        self.assertEqual(decision_log.load_decisions(self.league_id), [])

    def test_forget_decisions_on_a_league_with_no_file_is_a_safe_no_op(self):
        decision_log.forget_decisions("never_had_any_decisions")  # should not raise


if __name__ == "__main__":
    unittest.main()
