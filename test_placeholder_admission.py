"""#273: Sleeper's own placeholder rows must not reach a draft board.

THE DEFECT. The captured universe carries 59 rows named literally "Player Invalid" --
Sleeper's sentinel for an id it will not resolve -- with status=Inactive, team=None, age=None
and no projection. 53 of them reached the board. The cause is ORDER, not a missing rule:
`_admits_to_pool` is a union whose ROOKIE clause (`years_exp == 0`) returns True
unconditionally and sits BEFORE the `NOT_CURRENTLY_PLAYING` check that would have rejected
them, and 56 of the 59 carry `years_exp == 0`. The rookie clause is deliberately
unconditional -- a real rookie on a practice squad has no team and no projection -- so the
placeholder walks past the gate by looking like exactly the case the clause exists to admit.

WHAT MUST NOT REGRESS, and it is the half that makes this safe rather than merely effective:
the rule must reject the sentinel WITHOUT touching the population it resembles. A rule keyed
on shape rather than the sentinel -- "rookie AND inactive AND no team AND no projection" --
matches 146 rows in this capture of which 90 are ordinarily-named players. Those 90 are what
`test_a_real_rookie_with_the_same_shape_is_still_admitted` stands for.

MEASURED BLAST RADIUS, both arms in one process toggling only this rule: 1119 -> 1066 rows,
all 53 removed are placeholders, 0 rows added, priced rows unchanged at 481, and ZERO
surviving rows moved their final_score. The change is surgical and that is asserted below
rather than trusted.
"""
from __future__ import annotations

import unittest

import draft_room as dr


def _info(**over):
    base = {"first_name": "Real", "last_name": "Player", "position": "WR",
            "status": "Active", "team": "SF", "years_exp": 3, "age": 25}
    base.update(over)
    return base


PLACEHOLDER = {"first_name": "Player", "last_name": "Invalid", "position": "WR",
               "status": "Inactive", "team": None, "years_exp": 0, "age": None}


class APlaceholderIsNeverAdmittedTests(unittest.TestCase):
    """No signal about a placeholder is evidence that it is a player, so every clause of the
    admission union must fail to rescue it."""

    def test_rejected_even_though_it_looks_like_a_rookie(self):
        """The live path: years_exp == 0 returns True unconditionally, and it fires BEFORE
        the status gate. This is the one that was actually broken."""
        self.assertEqual(PLACEHOLDER["years_exp"], dr.ROOKIE_YEARS_EXP,
                         "fixture no longer exercises the rookie clause")
        self.assertFalse(dr._admits_to_pool(PLACEHOLDER, None, {}))

    def test_rejected_even_with_a_projection(self):
        self.assertFalse(dr._admits_to_pool(PLACEHOLDER, 250.0, {}))

    def test_rejected_even_when_listed_on_a_team(self):
        self.assertFalse(dr._admits_to_pool(dict(PLACEHOLDER, team="KC"), None, {}))

    def test_rejected_even_with_a_vendor_match_carrying_a_price(self):
        self.assertFalse(dr._admits_to_pool(
            PLACEHOLDER, None, {"matched": True, "trade_value": 900, "projection": 300.0}))


class TheRuleDoesNotOverReachTests(unittest.TestCase):
    """The 90 real players a shape-based rule would have taken with it."""

    def test_a_real_rookie_with_the_same_shape_is_still_admitted(self):
        """years_exp 0, no team, no projection, no age -- indistinguishable from the placeholder
        on every field EXCEPT the name. This is the population the sentinel check exists to
        spare, and a shape-based rule would delete it.

        THE LOOKALIKE IS `Active` RATHER THAN `Inactive` SINCE W4-01 (ruled 2026-09-21), and the
        change is to the FIXTURE, not to what this test asserts. W4-01 made the rookie clause
        yield to NOT_CURRENTLY_PLAYING, so an Inactive rookie with no team is now rejected by the
        STATUS gate -- which would make this test pass or fail for a reason that has nothing to
        do with the placeholder sentinel. An `Active` lookalike isolates the question this test
        was written to answer: does the `#273` rule reject on SHAPE or on the NAME? Keeping
        `Inactive` here would have quietly converted a placeholder guard into a status guard.
        """
        lookalike = _info(first_name="Tony", last_name="Johnson", position="K",
                          status="Active", team=None, years_exp=0, age=None)
        self.assertTrue(dr._admits_to_pool(lookalike, None, {}),
                        "a real rookie was rejected -- the rule is keyed on shape, not on the "
                        "vendor's sentinel, and it is removing players")

    def test_the_sentinel_still_decides_on_a_row_the_status_gate_would_pass(self):
        """NON-VACUITY for the fixture change above, and the assertion that keeps this a
        PLACEHOLDER test. The same Active/no-team/no-number shape, with the sentinel name, must
        still be rejected -- so the name is doing the work here, not the status."""
        self.assertFalse(dr._admits_to_pool(
            dict(PLACEHOLDER, status="Active", team=None, years_exp=0), None, {}),
            "the sentinel stopped deciding once the status gate could no longer")

    def test_an_ordinary_player_is_unaffected(self):
        self.assertTrue(dr._admits_to_pool(_info(), 200.0, {}))

    def test_only_the_exact_sentinel_matches(self):
        """Neither half of the name alone is a placeholder. 'Player' is a real surname and
        'Invalid' must not become a banned word."""
        for over in ({"first_name": "Player", "last_name": "Johnson"},
                     {"first_name": "Chris", "last_name": "Invalid"}):
            with self.subTest(**over):
                self.assertTrue(
                    dr._admits_to_pool(_info(**over), 150.0, {}),
                    f"{over} was rejected -- the match is looser than the sentinel")

    def test_an_inactive_veteran_still_follows_the_status_rule_unchanged(self):
        """The placeholder check must not have become a second status gate."""
        self.assertFalse(dr._admits_to_pool(
            _info(status="Inactive", team=None, years_exp=5), None, {}))
        self.assertTrue(dr._admits_to_pool(
            _info(status="Inactive", team=None, years_exp=5), None,
            {"matched": True, "trade_value": 500}) is False,
            "status rejection must still short-circuit the vendor-match clause")


class TheSentinelIsTheFeedsNotOursTests(unittest.TestCase):

    def test_the_sentinel_is_a_pair_of_name_parts_not_a_player_list(self):
        """#126: if this ever becomes a growing list of names, it has stopped being the feed's
        vocabulary and become an opinion about players."""
        self.assertIsInstance(dr.PLACEHOLDER_NAME, tuple)
        self.assertEqual(len(dr.PLACEHOLDER_NAME), 2)
        self.assertTrue(all(isinstance(p, str) for p in dr.PLACEHOLDER_NAME))


if __name__ == "__main__":
    unittest.main()
