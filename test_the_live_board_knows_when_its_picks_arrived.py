"""MANDATE 1.4 / `#52` blind pass G, finding 1: the Live Draft Room never fetched its own picks,
and labelled the board live anyway.

`get_draft_picks` had exactly ONE call site in `app.py`, behind the `↻ Refresh Picks` button. So a
live draft in round 4 opened showing **"ON THE CLOCK — 1.0X"**, every already-drafted player still a
candidate, "0 pick(s) made", and nothing anywhere saying the picks had never been pulled. A COMPLETED
draft rendered as live round 1. It recurred on every league switch, because the picks cache is
correctly cleared and never refilled.

TWO THINGS WERE WRONG AND BOTH ARE FIXED, because either alone leaves a person misled.
  * Nothing fetched. The view now pulls on load, once per draft per session, through the same call
    and the same exception handling as the button.
  * Nothing DISTINGUISHED "no picks have been made" from "nobody ever asked". `len(draft_picks)` is
    0 in both cases, and `is_live` is derived from it -- so the board could only ever have got this
    right by accident. A fetch stamp is the fact that separates them, and the board now refuses to
    call itself live without one.

The tests are source checks, for the reason every app-level guard in this repository is: `app.py` is
a Streamlit script whose import executes the page. The structural claim -- that picks cannot enter
the store without a stamp -- is read off the AST rather than grepped, so moving the writes does not
silently lose it.
"""
from __future__ import annotations

import ast
import re
import unittest

import ui_source

_APP = ui_source.text()
_LINES = _APP.splitlines()


def _draft_room_block() -> str:
    """From the Draft Room's session defaults to the end of the live board's render."""
    start = _APP.index('st.session_state.setdefault("draft_room_picks_by_draft"')
    end = _APP.index("draft_board_ui.render_board_html(board_payload)")
    return _APP[start:end]


class PicksCannotEnterTheStoreWithoutAStampTests(unittest.TestCase):
    """The structural half. A stamp that only some writers set is a stamp the board cannot trust,
    and the board's live label now rests on it."""

    def _write_lines(self, store: str) -> list[int]:
        """1-indexed lines assigning into `st.session_state.<store>[...]`."""
        found = []
        for node in ast.walk(ast.parse(_APP)):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if (isinstance(target, ast.Subscript)
                        and store in ast.unparse(target.value)):
                    found.append(node.lineno)
        return sorted(found)

    def test_there_are_exactly_two_ways_picks_enter_the_store(self):
        """NON-VACUITY for the test below: the button and the load-time pull. If this grows, the
        pairing check below has a new site to cover and should be read again rather than trusted."""
        self.assertEqual(2, len(self._write_lines("draft_room_picks_by_draft")),
                         "a third writer of the picks store appeared")

    def test_every_write_of_the_picks_is_paired_with_a_write_of_the_stamp(self):
        picks = self._write_lines("draft_room_picks_by_draft")
        stamps = self._write_lines("draft_room_picks_fetched_at")
        self.assertTrue(stamps)
        for line in picks:
            with self.subTest(line=line):
                self.assertTrue(any(0 < stamp - line <= 2 for stamp in stamps),
                                f"app.py:{line} puts picks in the store with no fetch stamp "
                                f"beside it -- the board cannot then tell them from picks nobody "
                                f"pulled")


class TheViewFetchesOnLoadTests(unittest.TestCase):
    def test_get_draft_picks_is_reached_from_more_than_the_button(self):
        self.assertGreater(_APP.count("draft_client.get_draft_picks(draft_id)"), 1,
                           "the only path to Sleeper's picks is still a button press")

    def test_the_load_time_pull_is_guarded_by_the_cache_miss(self):
        """Once per draft, not once per rerun: Streamlit reruns this script on every widget
        interaction."""
        block = _draft_room_block()
        self.assertIn("if (draft_id not in st.session_state.draft_room_picks_by_draft", block)

    def test_a_failed_pull_hands_the_retry_to_the_button_rather_than_looping(self):
        """A persistent failure must not re-hit Sleeper on every rerun behind the user's back."""
        block = _draft_room_block()
        self.assertIn("draft_room_picks_autofetch_failed.add(draft_id)", block)
        self.assertIn("and draft_id not in st.session_state.draft_room_picks_autofetch_failed",
                      block)

    def test_the_failure_is_reported_and_not_swallowed(self):
        block = _draft_room_block()
        self.assertRegex(block, r"except SleeperAPIError as exc:\s*\n\s*st\.session_state"
                                r"\.draft_room_picks_autofetch_failed\.add\(draft_id\)\s*\n\s*"
                                r'notify\("error"')


class TheBoardWillNotCallItselfLiveWithoutAStampTests(unittest.TestCase):
    def test_on_the_clock_requires_the_stamp(self):
        block = _draft_room_block()
        header = re.search(r"board_header = \((.|\n)*?\)\n", block)
        self.assertIsNotNone(header, "the board header is no longer assembled here")
        self.assertIn("picks_pulled_at is not None", header.group(0),
                      "the board can still call itself live on picks nobody pulled")

    def test_the_board_carries_a_picks_as_of_tag_either_way(self):
        """Not only when the stamp exists: the absent case is the one that was silent."""
        block = _draft_room_block()
        self.assertIn("PICKS AS OF", block)
        self.assertIn("PICKS NOT PULLED", block)

    def test_the_hover_caveat_says_pulled_rather_than_made(self):
        """"N pick(s) made" is a claim about the DRAFT; what this view knows is a claim about a
        FETCH. They differ by exactly the case that was wrong."""
        block = _draft_room_block()
        self.assertIn("pick(s) pulled from Sleeper at", block)
        self.assertNotIn("pick(s) made ·", block)

    def test_the_unfetched_sentence_tells_the_user_what_to_do(self):
        block = _draft_room_block()
        self.assertIn("press ↻ Refresh Picks", block)


if __name__ == "__main__":
    unittest.main()
