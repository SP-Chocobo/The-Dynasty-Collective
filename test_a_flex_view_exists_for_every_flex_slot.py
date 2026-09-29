"""MANDATE 4 / `#126` -- the flex vocabulary had four homes and two of them were short.

`player_universe.FLEX_SLOT_POSITIONS` spells five flex slot types: FLEX, SUPER_FLEX, WRRB_FLEX,
REC_FLEX, IDP_FLEX. `draft_board_ui._POSITION_VIEW_ORDER` hand-listed three of them, and
`app.FA_POSITION_FILTERS` hand-copied three of the eligible SETS with its own labels.

THE OMISSION WAS INVISIBLE BY CONSTRUCTION. `position_view_options` offers a flex view only when the
slot is in that league's own `roster_positions`, so a league without a REC_FLEX slot was never going
to show a REC_FLEX view and nothing looked wrong. A league WITH one got no view either, and the board
view is the only way to look at a single slot's candidates -- so for that league the slot could not be
examined at all.

TWO DIFFERENT REPAIRS, because the two homes were wrong in different ways, and the distinction is
the point:

  * `draft_board_ui` had a REAL GAP. The two missing names are added, and -- mattering more than the
    names -- any flex type in the vocabulary that this list does not mention is now appended rather
    than dropped, so the next one cannot repeat it.

  * `app.FA_POSITION_FILTERS` had a COPIED MEANING. Its labels ("FLEX", "SUPERFLEX", "IDP") and its
    order are this screen's own and stay chosen there; what each label MEANS now comes from the
    vocabulary. No filter row is added: `wanted & league_positions` would put WRRB_FLEX and REC_FLEX
    in front of nearly every league, since almost all of them use RB and WR, and a subset of a FLEX
    filter already on the list is noise rather than a missing capability. That is a product
    judgement, and the test below states it so it reads as a decision instead of another omission.

IT ALSO CLOSES THE SUPERFLEX SPELLING. `SUPERFLEX` appeared once, in that filter list, against
`SUPER_FLEX` everywhere else. It was harmless because it is a display label -- and it was the shape
the next reader would copy. With the set taken by its real key, the label is only a label.
"""

from __future__ import annotations

import unittest

import draft_board_ui as board_ui
import ui_source
from player_universe import FLEX_SLOT_POSITIONS


class EveryFlexSlotHasAViewTests(unittest.TestCase):
    def test_the_vocabulary_is_not_empty_or_trivial(self):
        self.assertGreater(len(FLEX_SLOT_POSITIONS), 3,
                           "vacuous: with three or fewer flex types the old hand-list was complete")

    def test_the_view_order_mentions_every_flex_type(self):
        missing = [slot for slot in FLEX_SLOT_POSITIONS
                   if slot not in board_ui._POSITION_VIEW_ORDER]
        self.assertEqual(missing, [],
                         f"{missing} exist as flex slots and have no board view, so a league that "
                         f"rosters one cannot look at its candidates")

    def test_a_league_rostering_each_flex_slot_is_offered_that_view(self):
        for slot, eligible in sorted(FLEX_SLOT_POSITIONS.items()):
            with self.subTest(slot=slot):
                options = board_ui.position_view_options(set(eligible),
                                                         ["QB", "RB", "WR", slot, "BN"])
                self.assertIn(slot, options)

    def test_a_league_NOT_rostering_the_slot_is_not_offered_it(self):
        """The guard that made the omission invisible, and it must survive the repair -- a view for
        a slot the league does not field is a view with nowhere to start anyone."""
        options = board_ui.position_view_options({"RB", "WR", "TE", "QB"},
                                                 ["QB", "RB", "WR", "TE", "FLEX", "BN"])
        for slot in FLEX_SLOT_POSITIONS:
            if slot != "FLEX":
                self.assertNotIn(slot, options)

    def test_a_rostered_slot_with_no_eligible_candidate_is_still_not_offered(self):
        """The second half of that guard: an empty view is as useless as an impossible one."""
        options = board_ui.position_view_options({"QB"}, ["QB", "IDP_FLEX", "BN"])
        self.assertNotIn("IDP_FLEX", options)

    def test_the_order_is_still_a_stated_display_order(self):
        """Membership comes from the vocabulary; SEQUENCE is a decision and stays in the view."""
        order = board_ui._POSITION_VIEW_ORDER
        self.assertLess(order.index("QB"), order.index("FLEX"))
        self.assertLess(order.index("FLEX"), order.index("SUPER_FLEX"),
                        "the broadest offence flex should come after the narrower ones")
        self.assertLess(order.index("DEF"), order.index("IDP_FLEX"))


class TheFreeAgentFilterTakesItsMeaningFromTheVocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ui_source.text()
        cls.filters = dict(_pair for _pair in _fa_filters())

    def test_each_flex_label_means_exactly_what_the_vocabulary_says(self):
        for label, slot in (("FLEX", "FLEX"), ("SUPERFLEX", "SUPER_FLEX"), ("IDP", "IDP_FLEX")):
            with self.subTest(label=label):
                self.assertEqual(self.filters[label], set(FLEX_SLOT_POSITIONS[slot]))

    def test_the_sets_are_no_longer_spelled_in_the_view(self):
        for literal in ('("FLEX", {"WR", "RB", "TE"})',
                        '("SUPERFLEX", {"QB", "WR", "RB", "TE"})',
                        '("IDP", {"DL", "LB", "DB"})'):
            self.assertNotIn(literal, self.source,
                             "a flex eligibility set is spelled in the view again")

    def test_the_two_flex_types_left_off_the_filter_are_left_off_DELIBERATELY(self):
        """Stated as a test so it reads as a product judgement rather than the same omission the
        board view had. If someone decides to offer them, this fails and they update the reason."""
        self.assertNotIn("WRRB_FLEX", self.filters)
        self.assertNotIn("REC_FLEX", self.filters)
        self.assertIn("MANDATE 4", self.source)

    def test_the_odd_spelling_survives_only_as_a_LABEL(self):
        """`SUPERFLEX` against `SUPER_FLEX` everywhere else. Harmless as a word a person reads;
        the risk was it being copied as a token, and the set is now keyed by the real one."""
        self.assertIn("SUPERFLEX", self.filters)
        self.assertNotIn("SUPERFLEX", FLEX_SLOT_POSITIONS,
                         "SUPERFLEX has become a vocabulary key, which is the drift this guards")


def _fa_filters():
    """app's filter list, read without importing app (which would start Streamlit)."""
    import ast
    tree = ast.parse(ui_source.unit_containing("FA_POSITION_FILTERS = ["))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and node.targets
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "FA_POSITION_FILTERS"):
            for element in node.value.elts:
                label = element.elts[0].value
                wanted = element.elts[1]
                if isinstance(wanted, ast.Constant) and wanted.value is None:
                    continue
                yield label, _resolve_set(wanted)
            return
    raise AssertionError("FA_POSITION_FILTERS not found in the UI source")


def _resolve_set(node):
    """A literal set, or set(FLEX_SLOT_POSITIONS["KEY"])."""
    import ast
    if isinstance(node, ast.Set):
        return {element.value for element in node.elts}
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "set":
        inner = node.args[0]
        return set(FLEX_SLOT_POSITIONS[inner.slice.value])
    raise AssertionError(f"unrecognised filter set shape: {ast.dump(node)}")


if __name__ == "__main__":
    unittest.main()
