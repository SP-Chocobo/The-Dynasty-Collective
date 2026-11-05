"""`#315`. The behaviour of `build_pick_ledger`, which had none tested.

THE GAP THIS CLOSES. Before `#315` the only test naming `build_pick_ledger` was
`test_league_view_wiring`, and it asserts the literal STRING
`"pick_ledger = build_pick_ledger(snapshot)"` appears once in a source block. That is a wiring
assertion: it never calls the function. So a function at three call sites, producing what a
documentation review called "the single dynasty fact the product most needs", could have returned
anything at all and the suite would have stayed green.

`#300` set the precedent when it lifted `build_freshness_manifest` out of the same hull: a lifted
module gets its own behaviour test (`test_freshness.py`). Lifting is the moment the gap becomes
visible, because a function inside a 5,800-line Streamlit hull is hard to call and a module is not.

WHAT THE LEDGER DELIBERATELY IS NOT. A full inventory. Sleeper lists a pick under `traded_picks`
only once it has actually moved, so an untouched pick is assumed to sit with its original roster
and is not worth listing. The ledger is the DIFFS. A test that demanded every hypothetical future
pick appear would be asserting a different function into existence.
"""
from __future__ import annotations

import unittest

from pick_ledger import build_pick_ledger


def _snap(*picks):
    return {"traded_picks": list(picks)}


def _pick(original, current, season="2027", rnd=1):
    return {"roster_id": original, "owner_id": current, "season": season, "round": rnd}


class AMovedPickIsRecordedOnBothSidesTests(unittest.TestCase):
    def test_the_new_owner_acquired_it_and_the_original_gave_it_away(self):
        ledger = build_pick_ledger(_snap(_pick(3, 7)))
        self.assertEqual([p["owner_id"] for p in ledger[7]["acquired"]], [7])
        self.assertEqual([p["roster_id"] for p in ledger[3]["given_away"]], [3])
        # and neither side is credited with the other's half
        self.assertEqual(ledger[7]["given_away"], [])
        self.assertEqual(ledger[3]["acquired"], [])

    def test_both_rosters_appear_even_though_only_one_row_describes_the_trade(self):
        """One `traded_picks` row is TWO facts. A ledger that recorded only the acquiring side
        would leave a roster unable to see what it no longer holds."""
        ledger = build_pick_ledger(_snap(_pick(3, 7)))
        self.assertEqual(sorted(ledger), [3, 7])

    def test_several_picks_accumulate_rather_than_replace(self):
        ledger = build_pick_ledger(_snap(_pick(3, 7, rnd=1), _pick(3, 7, rnd=2), _pick(5, 7)))
        self.assertEqual(len(ledger[7]["acquired"]), 3)
        self.assertEqual(len(ledger[3]["given_away"]), 2)
        self.assertEqual(len(ledger[5]["given_away"]), 1)


class AnUntouchedPickIsNotAnEntryTests(unittest.TestCase):
    """`#187`-shaped: the ledger is the DIFFS, and 'no entry' means 'never moved', which is not
    the same claim as 'moved to nobody'."""

    def test_a_pick_still_with_its_original_roster_is_skipped(self):
        self.assertEqual(build_pick_ledger(_snap(_pick(4, 4))), {})

    def test_a_roster_with_only_untouched_picks_does_not_appear_at_all(self):
        ledger = build_pick_ledger(_snap(_pick(4, 4), _pick(9, 2)))
        self.assertNotIn(4, ledger)
        self.assertEqual(sorted(ledger), [2, 9])


class AbsenceIsNotZeroTests(unittest.TestCase):
    def test_a_missing_original_or_owner_is_skipped_not_defaulted(self):
        """A row with a missing side cannot be split into two facts. Defaulting either end to 0
        would invent a roster, and roster ids are real -- `#187`."""
        self.assertEqual(build_pick_ledger(_snap({"owner_id": 7})), {})
        self.assertEqual(build_pick_ledger(_snap({"roster_id": 3})), {})
        self.assertEqual(build_pick_ledger(_snap({})), {})

    def test_roster_zero_is_a_roster_and_not_a_missing_value(self):
        """The guard is `is None`, not falsiness. A `0` roster id is a real roster, and an
        `if not original:` would have silently dropped it."""
        ledger = build_pick_ledger(_snap(_pick(0, 5)))
        self.assertEqual(sorted(ledger), [0, 5])
        self.assertEqual(len(ledger[0]["given_away"]), 1)

    def test_no_traded_picks_key_and_an_explicit_none_both_give_an_empty_ledger(self):
        self.assertEqual(build_pick_ledger({}), {})
        self.assertEqual(build_pick_ledger({"traded_picks": None}), {})
        self.assertEqual(build_pick_ledger({"traded_picks": []}), {})


class TheRowItselfIsHandedBackTests(unittest.TestCase):
    def test_the_stored_entry_is_the_vendor_row_not_a_reduction_of_it(self):
        """Callers price these (`merger.pick_value`), so season and round have to survive. A
        ledger that kept only ids would have forced every caller back to the snapshot."""
        row = _pick(3, 7, season="2028", rnd=4)
        ledger = build_pick_ledger(_snap(row))
        self.assertEqual(ledger[7]["acquired"][0]["season"], "2028")
        self.assertEqual(ledger[7]["acquired"][0]["round"], 4)


if __name__ == "__main__":
    unittest.main()
