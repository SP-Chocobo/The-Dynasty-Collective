"""#52 phase 7.4c: the anchor cache key must cover every input the anchor reads.

`predraft_replacement_anchor` memoises a whole second pool build (~544 ms) in a process-wide
`_ANCHOR_CACHE`, keyed by `anchor_cache_key`. An input the anchor reads and the key omits means
two different leagues, formats or player universes share one cached answer -- and because the
cache is process-wide, the wrong answer outlives the board that produced it.

MEASURED FIRST, AND THE FINDING IS ALREADY CLOSED. The audit listed the anchor fingerprint as
incomplete; compared parameter by parameter against the function it keys, it is complete today
-- all eleven, nothing extra. So this file is not a repair. It is the guard that makes the
completeness survive, because the sibling key that did NOT have one (the Draft Room's snapshot
cache, phase 7.4a) drifted to six hand-written dimensions in front of a fifteen-input call
while nobody was looking. The difference between the two keys was never care; it was that one
of them could fall behind silently.

WHAT THIS CANNOT SEE, stated because the key's own docstring states it and a test that implied
otherwise would be worse than no test. `anchor_cache_key` is derived from ARGUMENTS. A module
constant that moves the anchor is not an argument and cannot appear here -- #184 is the
cautionary case: `SUPER_FLEX_QB_SHARE` moves this anchor, is not in the key, and silently
served one arm the other's anchor during an in-process A/B. An argument has no such excuse;
a constant needs a different guard.
"""

from __future__ import annotations

import inspect
import unittest

import pandas as pd

import draft_room as dr


class _FakeMerger:
    """Only the frames the fingerprinter reads. The key is computed, never the anchor."""

    def __init__(self, salt: int = 0):
        for name in dr._ANCHOR_FRAMES:
            setattr(self, name, pd.DataFrame({"v": [salt, salt + 1]}))


def _base() -> dict:
    return dict(
        merger=_FakeMerger(0),
        players_db={"1": {"position": "RB", "team": "PHI", "fantasy_positions": ["RB"]}},
        usable_positions={"QB", "RB"},
        roster_positions=["QB", "RB", "FLEX"],
        num_teams=12,
        value_col="_points",
        sleeper_projections=None,
        scoring_settings={"rec": 1.0},
        pool_scope="all",
        startable_floors=None,
        sleeper_basis=dr.SLEEPER_BASIS_WEEKLY,
    )


#: One materially different value per parameter. Keys asserted equal to the signature, so a new
#: argument to the anchor cannot ship until someone says here what a change to it looks like.
ALTERNATES = {
    "merger": _FakeMerger(9),
    "players_db": {"1": {"position": "WR", "team": "PHI", "fantasy_positions": ["WR"]}},
    "usable_positions": {"QB", "RB", "TE"},
    "roster_positions": ["QB", "RB", "RB", "FLEX"],
    "num_teams": 10,
    "value_col": "trade_value",
    "sleeper_projections": {"1": {"rec": 5.0}},
    "scoring_settings": {"rec": 0.5},
    "pool_scope": "rookies",
    "startable_floors": {"QB": 250.0},
    "sleeper_basis": dr.SLEEPER_BASIS_SEASON_SUM,
}


class TheKeyCoversTheFunctionItKeysTests(unittest.TestCase):

    def test_the_key_takes_exactly_the_anchors_parameters(self):
        """Parity, in both directions.

        A parameter the key does not take is an input it cannot see. A parameter the key takes
        and the anchor does not is a dimension that splits the cache for nothing -- less
        dangerous, but it means the two have stopped describing the same call, and that is the
        state the snapshot cache was in.
        """
        anchor = list(inspect.signature(dr.predraft_replacement_anchor).parameters)
        key = list(inspect.signature(dr.anchor_cache_key).parameters)
        self.assertEqual(anchor, key)

    def test_the_alternates_table_covers_the_signature_exactly(self):
        """The ratchet: everything below loops over this table."""
        self.assertEqual(set(ALTERNATES),
                         set(inspect.signature(dr.predraft_replacement_anchor).parameters))

    def test_changing_any_single_input_changes_the_key(self):
        base = dr.anchor_cache_key(**_base())
        unmoved = [name for name, alternate in ALTERNATES.items()
                   if dr.anchor_cache_key(**{**_base(), name: alternate}) == base]
        self.assertEqual(unmoved, [],
                         "these inputs move the anchor and cannot move its key, so a "
                         "process-wide cache serves one league's anchor to another")

    def test_no_two_inputs_are_interchangeable(self):
        keys = {name: dr.anchor_cache_key(**{**_base(), name: alternate})
                for name, alternate in ALTERNATES.items()}
        self.assertEqual(len(set(keys.values())), len(keys), keys)

    def test_the_same_inputs_key_the_same_way_twice(self):
        """Or the memo never hits and the ~544 ms second pool build is paid every time."""
        self.assertEqual(dr.anchor_cache_key(**_base()), dr.anchor_cache_key(**_base()))

    def test_a_fresh_but_equal_merger_keys_the_same_way(self):
        """CONTENT, not object identity -- the merger is rebuilt on every league switch."""
        self.assertEqual(dr.anchor_cache_key(**{**_base(), "merger": _FakeMerger(0)}),
                         dr.anchor_cache_key(**_base()))

    def test_an_unordered_input_keys_the_same_way_whatever_order_it_arrives_in(self):
        """`usable_positions` is a membership collection: WHICH positions, not in what order.
        Order must not reach the key, or the memo misses at random and the cache becomes a
        no-op that still costs a hash.

        TESTED THROUGH AN ORDERED TYPE, and the first version of this test was vacuous for
        exactly the reason that matters. It compared `{"QB","RB","TE"}` with `{"TE","QB","RB"}`
        and asserted the keys matched -- but two equal Python sets of the same small strings
        iterate identically whatever order they were written in, so the assertion held with or
        without the `sorted()` it was written to protect. Removing that `sorted()` survived the
        whole file.

        A set's iteration order cannot be controlled from here, so the property is exercised
        with lists, where it can: two orderings of the same positions must key the same way.
        """
        a = dr.anchor_cache_key(**{**_base(), "usable_positions": ["QB", "RB", "TE"]})
        b = dr.anchor_cache_key(**{**_base(), "usable_positions": ["TE", "QB", "RB"]})
        self.assertEqual(a, b)
        self.assertNotEqual(
            a, dr.anchor_cache_key(**{**_base(), "usable_positions": ["QB", "RB"]}),
            "non-vacuity: order-insensitive must not mean content-insensitive")

    def test_roster_positions_keys_on_ORDER_because_the_anchor_reads_it_as_a_list(self):
        """The mirror of the test above, and the reason neither can be inferred from the other:
        a set's order is noise, a roster's order is data (`SUPER_FLEX` placement, flex
        expansion). Sorting this one would collapse two real leagues onto one key."""
        a = dr.anchor_cache_key(**{**_base(), "roster_positions": ["QB", "RB", "FLEX"]})
        b = dr.anchor_cache_key(**{**_base(), "roster_positions": ["FLEX", "QB", "RB"]})
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
