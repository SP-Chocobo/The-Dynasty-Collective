"""MANDATE 1.7 / `#101`: the diff said WHAT changed and never WHICH two boards, or what happened
between them.

`diff_snapshots` reports per-candidate deltas under the heading "WHAT CHANGED SINCE THE LAST
SNAPSHOT", and neither the heading nor the rows named the span. So the single largest cause of
movement on that list -- the reader's OWN pick, which removes a player from every candidate list and
re-prices every roster-aware term against a roster that now has one more player on it -- arrived
looking exactly like the market moving around them.

The anchor is derived from the two snapshots and nothing is passed in. The load-bearing derivation is
`your_own_turn_passed`, and it is measured rather than argued: a snapshot's `pick_label` is the
READER's own next selection, so it moves when and only when their own pick was made. Driven below
through `generate_pick_order` and `find_next_pick_index` themselves over 29 consecutive picks of a
12-team snake -- the label moves at exactly the three picks that were the reader's, and at no others.
"""
from __future__ import annotations

import unittest

import draft_strategy as ds
import pick_debate as pd
import pick_synthesis as ps
import ui_source
from test_pick_debate import _candidate, _snapshot


def _snap(pick_label="1.01", picks_consumed=0, pool_scope="all", stamp="UNIVERSE-A", names=("A",)):
    base = _snapshot([_candidate(str(i + 1), name) for i, name in enumerate(names)])
    return ps.PickSnapshot(
        pick_label=pick_label, round=int(pick_label.split(".")[0]),
        my_roster_id=base.my_roster_id, candidates=base.candidates,
        picks_consumed=picks_consumed, data_freshest_date="2026-09-07",
        pool_scope=pool_scope, players_db_stamp=stamp)


class TheLabelMovesWhenAndONLYWhenYourOwnPickIsMadeTests(unittest.TestCase):
    """The derivation the anchor rests on, driven through the engine's own pick-order functions
    rather than asserted from reasoning about them."""

    TEAMS = 12
    ME = 3

    def _label_after(self, order, picks_made):
        nxt = ds.find_next_pick_index(order, self.ME, picks_made - 1)
        if nxt is None:
            return None
        return f"{nxt // self.TEAMS + 1}.{nxt % self.TEAMS + 1:02d}"

    def test_over_a_whole_snake_the_label_moves_exactly_at_your_own_picks(self):
        order = ds.generate_pick_order(list(range(1, self.TEAMS + 1)), total_rounds=4,
                                       draft_type="snake")
        moved_at, mine_at = [], []
        previous = self._label_after(order, 0)
        for made in range(1, 30):
            if order[made - 1] == self.ME:
                mine_at.append(made)
            current = self._label_after(order, made)
            if current != previous:
                moved_at.append(made)
            previous = current
        self.assertTrue(mine_at, "the fixture never reaches this roster's turn")
        self.assertEqual(mine_at, moved_at,
                         "pick_label does not track the reader's own turn, so the anchor's "
                         "your_own_turn_passed is not derivable this way -- re-derive it")

    def test_it_holds_under_third_round_reversal_too(self):
        """3RR is the format that mis-sizes waits worst of all, per generate_pick_order's own
        docstring, so it is the one where a claim about turn order most needs checking."""
        order = ds.generate_pick_order(list(range(1, self.TEAMS + 1)), total_rounds=5,
                                       draft_type="3rr")
        moved_at, mine_at = [], []
        previous = self._label_after(order, 0)
        for made in range(1, 40):
            if order[made - 1] == self.ME:
                mine_at.append(made)
            current = self._label_after(order, made)
            if current != previous:
                moved_at.append(made)
            previous = current
        self.assertEqual(mine_at, moved_at)


class TheAnchorNamesTheSpanTests(unittest.TestCase):
    def test_it_counts_the_picks_between_the_two_boards(self):
        anchor = ps.diff_anchor(_snap(picks_consumed=14), _snap("2.10", picks_consumed=29))
        self.assertEqual(15, anchor["picks_between"])

    def test_an_unstamped_pair_says_so_rather_than_implying_zero(self):
        """#187: a count of zero and a count nobody took are different facts."""
        unstamped = ps.PickSnapshot(pick_label="1.01", round=1, my_roster_id="3", candidates=())
        anchor = ps.diff_anchor(unstamped, _snap(picks_consumed=14))
        self.assertIsNone(anchor["picks_between"])
        self.assertIn("could not be established", ps.diff_anchor_sentence(anchor))

    def test_your_own_pick_is_called_out_in_capitals_when_it_happened(self):
        """It is the largest single mover on the list and the one the reader can most easily
        mistake for the market."""
        sentence = ps.diff_anchor_sentence(
            ps.diff_anchor(_snap("1.03", picks_consumed=2), _snap("2.10", picks_consumed=21)))
        self.assertIn("YOUR OWN PICK IS AMONG THEM", sentence)
        self.assertIn("1.03", sentence)
        self.assertIn("2.10", sentence)

    def test_and_is_explicitly_denied_when_it_did_not(self):
        """NON-VACUITY: a sentence that always warned would be worth nothing."""
        sentence = ps.diff_anchor_sentence(
            ps.diff_anchor(_snap("1.03", picks_consumed=2), _snap("1.03", picks_consumed=8)))
        self.assertIn("none of them yours", sentence)
        self.assertNotIn("YOUR OWN PICK", sentence)

    def test_one_pick_is_singular(self):
        sentence = ps.diff_anchor_sentence(
            ps.diff_anchor(_snap("1.03", picks_consumed=2), _snap("1.03", picks_consumed=3)))
        self.assertIn("1 pick has been made", sentence)

    def test_a_pool_scope_change_says_the_two_lists_are_not_one_population(self):
        """Otherwise "entered the candidate pool" is a false claim about the market -- the player
        was never eligible before."""
        anchor = ps.diff_anchor(_snap(pool_scope="rookies_only"), _snap(pool_scope="all"))
        self.assertTrue(anchor["pool_scope_changed"])
        sentence = ps.diff_anchor_sentence(anchor)
        self.assertIn("not the same population", sentence)
        self.assertIn("rookies only", sentence)

    def test_a_universe_change_says_the_movement_may_not_be_the_market(self):
        anchor = ps.diff_anchor(_snap(stamp="UNIVERSE-A"), _snap(stamp="UNIVERSE-B"))
        self.assertTrue(anchor["player_universe_changed"])
        self.assertIn("rather than the market", ps.diff_anchor_sentence(anchor))

    def test_an_unstamped_universe_is_not_reported_as_changed(self):
        """A stamp compared against nothing is not a comparison."""
        self.assertFalse(ps.diff_anchor(_snap(stamp=None), _snap(stamp="B"))["player_universe_changed"])

    def test_the_quiet_case_says_nothing_extra(self):
        sentence = ps.diff_anchor_sentence(
            ps.diff_anchor(_snap("1.03", picks_consumed=2), _snap("1.03", picks_consumed=4)))
        self.assertNotIn("population", sentence)
        self.assertNotIn("underneath", sentence)


class BothSurfacesReadTheSameSentenceTests(unittest.TestCase):
    """One derivation, one sentence, two renderers. A second derivation at a surface is a second
    answer (`#126`)."""

    def test_the_chairs_block_carries_the_anchor_above_the_rows(self):
        # The two boards must actually DIFFER, or `diffs` is empty, the WHAT CHANGED block is not
        # emitted at all, and this test would be about a heading that never appears. B is gone from
        # the later board -- which is exactly the case the anchor exists to explain, since the
        # reader may well be the one who took him.
        before = _snap("1.03", picks_consumed=2, names=("A", "B"))
        after = _snap("2.10", picks_consumed=21, names=("A",))
        text = pd.format_snapshot_for_llm(after, ps.diff_snapshots(before, after),
                                          ps.diff_anchor(before, after))
        self.assertIn("WHAT CHANGED SINCE THE LAST SNAPSHOT:", text)
        self.assertIn("YOUR OWN PICK IS AMONG THEM", text)
        self.assertLess(text.index("WHAT CHANGED"), text.index("YOUR OWN PICK"),
                        "the anchor belongs under the heading it qualifies")

    def test_a_caller_with_no_previous_board_is_unchanged(self):
        after = _snap("1.03", picks_consumed=2, names=("A", "B"))
        self.assertNotIn("Since your board", pd.format_snapshot_for_llm(after))

    def test_the_result_carries_the_anchor_for_the_ui_to_render(self):
        self.assertIn("diff_anchor", pd.PickDebateResult.__dataclass_fields__)
        source = ui_source.text()
        self.assertIn("pick_synthesis.diff_anchor_sentence(", source)
        drawer = source[source.index("What changed since your last debate?"):][:900]
        self.assertIn("diff_anchor_sentence", drawer)
        self.assertLess(drawer.index("diff_anchor_sentence"), drawer.index("for d in debate_result.diff"),
                        "the anchor must be rendered before the rows it qualifies")

    def test_the_debate_computes_the_anchor_wherever_it_computes_the_diff(self):
        """Held together at one call site, so a consumer cannot get one without the other."""
        from pathlib import Path
        source = Path("pick_debate.py").read_text()
        self.assertIn("anchor = (ps.diff_anchor(previous_snapshot, snapshot)", source)
        self.assertIn("diff_anchor=anchor", source)


if __name__ == "__main__":
    unittest.main()
