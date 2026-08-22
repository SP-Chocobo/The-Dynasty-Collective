import shutil
import tempfile
import unittest
from pathlib import Path

import pinned_messages as pm


class PinnedMessagesTests(unittest.TestCase):
    """Points PINS_DIR at a throwaway temp directory for the duration of each test, never
    touching real data/pins/."""

    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._orig_dir = pm.PINS_DIR
        pm.PINS_DIR = Path(self._tmpdir)
        self.league_id = "league123"
        self.addCleanup(lambda: shutil.rmtree(self._tmpdir, ignore_errors=True))
        self.addCleanup(setattr, pm, "PINS_DIR", self._orig_dir)

    # -- toggle_pin / load_pinned_ts ---------------------------------------------------------

    def test_nothing_pinned_yet_returns_empty_set(self):
        self.assertEqual(pm.load_pinned_ts(self.league_id), set())

    def test_toggle_pin_pins_a_new_message(self):
        now_pinned = pm.toggle_pin(self.league_id, 123.456)
        self.assertTrue(now_pinned)
        self.assertEqual(pm.load_pinned_ts(self.league_id), {123.456})

    def test_toggle_pin_again_unpins_it(self):
        pm.toggle_pin(self.league_id, 123.456)
        now_pinned = pm.toggle_pin(self.league_id, 123.456)
        self.assertFalse(now_pinned)
        self.assertEqual(pm.load_pinned_ts(self.league_id), set())

    def test_multiple_pins_accumulate(self):
        pm.toggle_pin(self.league_id, 1.0)
        pm.toggle_pin(self.league_id, 2.0)
        pm.toggle_pin(self.league_id, 3.0)
        self.assertEqual(pm.load_pinned_ts(self.league_id), {1.0, 2.0, 3.0})

    def test_leagues_are_independent(self):
        pm.toggle_pin("league_a", 1.0)
        self.assertEqual(pm.load_pinned_ts("league_b"), set())

    # -- forget_pins ----------------------------------------------------------------------

    def test_forget_pins_clears_everything(self):
        pm.toggle_pin(self.league_id, 1.0)
        pm.forget_pins(self.league_id)
        self.assertEqual(pm.load_pinned_ts(self.league_id), set())

    def test_forget_pins_on_a_league_with_none_is_a_safe_no_op(self):
        pm.forget_pins("never_pinned_anything")  # should not raise

    # -- find_relevant ----------------------------------------------------------------------

    def _messages(self):
        return [
            {"ts": 1.0, "role": "beat", "content": "Bijan Robinson trade value is climbing fast this week"},
            {"ts": 2.0, "role": "quant", "content": "Josh Allen projects well under superflex scoring rules"},
            {"ts": 3.0, "role": "user", "content": "unrelated message about waiver wire depth"},
        ]

    def test_finds_a_pinned_message_with_enough_word_overlap(self):
        messages = self._messages()
        results = pm.find_relevant(messages, {1.0}, "what's Bijan Robinson trade value doing")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["ts"], 1.0)

    def test_only_pinned_messages_are_ever_candidates(self):
        messages = self._messages()
        # ts=2.0 (Josh Allen) has plenty of word overlap but was never pinned.
        results = pm.find_relevant(messages, {1.0}, "Josh Allen superflex scoring projection")
        self.assertEqual(results, [])

    def test_requires_at_least_two_overlapping_words_not_just_one(self):
        messages = self._messages()
        # Only "week" overlaps -- a single common word shouldn't surface a pin (unlike
        # decision_log's search, which accepts overlap>=1).
        results = pm.find_relevant(messages, {1.0}, "how was my team last week")
        self.assertEqual(results, [])

    def test_two_overlapping_words_is_enough(self):
        messages = self._messages()
        results = pm.find_relevant(messages, {1.0}, "checking on Bijan Robinson news")
        self.assertEqual(len(results), 1)

    def test_apostrophes_dont_break_matching(self):
        messages = [{"ts": 1.0, "role": "beat", "content": "Golden's usage rate is trending up big time"}]
        # "Golden's" -> tokenized without stripping the apostrophe would become "golden's",
        # never overlapping a query that just says "Golden" -- confirmed this doesn't happen.
        results = pm.find_relevant(messages, {1.0}, "is Golden trending up in usage")
        self.assertEqual(len(results), 1)

    def test_no_pins_at_all_returns_nothing(self):
        results = pm.find_relevant(self._messages(), set(), "Bijan Robinson trade value")
        self.assertEqual(results, [])

    def test_blank_query_returns_nothing(self):
        self.assertEqual(pm.find_relevant(self._messages(), {1.0}, ""), [])
        self.assertEqual(pm.find_relevant(self._messages(), {1.0}, "   "), [])

    def test_results_ranked_by_overlap_and_respect_limit(self):
        messages = [
            {"ts": 1.0, "role": "beat", "content": "trade value trending up fast this week"},
            {"ts": 2.0, "role": "beat", "content": "trade value trending up fast this week for real"},
        ]
        results = pm.find_relevant(messages, {1.0, 2.0}, "trade value trending up fast this week", limit=1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
