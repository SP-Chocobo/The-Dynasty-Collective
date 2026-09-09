"""The ordering verdict must not prefer a roster nobody would build (#216, #219).

`WR >= RB > TE` is the owner's rule, and it is trivially satisfied at TE 0. In his real league --
no dedicated TE slot, three flexes -- that is not a technicality: the unfixed engine scores 3/3
there BY DRAFTING NO TIGHT ENDS, against his own roster which carries two and against an optimal
fielding of that league which uses about 1.5 per team.

He gave the rule for that case himself, before any of it was measured: *"with no TE slot, but
flex that can field them, the TE act as de-facto WR."* These tests pin that the second reading
exists, that the LEAGUE'S RULEBOOK decides when it applies rather than anything invented here,
and -- most important -- that the original keys never move, so every verdict already recorded
stays comparable with every verdict recorded after.
"""
import unittest

import run_216_bench_probe as bench

TE_SLOT = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 6
NO_TE_SLOT = ["QB", "WR", "WR", "RB", "RB", "FLEX", "FLEX", "WRRB_FLEX", "SUPER_FLEX"] + ["BN"] * 5


class TheOriginalVerdictIsUnchangedTests(unittest.TestCase):
    def test_without_a_rulebook_only_the_original_keys_come_back(self):
        verdict = bench.ordering_verdict({"WR": 7, "RB": 4, "TE": 2, "QB": 1})
        self.assertEqual(set(verdict), {"WR>=RB", "RB>TE", "RB>=TE", "QB<=4",
                                        "pass_strict", "pass_tendency"})

    def test_not_asked_and_asked_and_no_are_different_answers(self):
        # The absence contract on a boolean: a caller that never supplied a rulebook must not be
        # handed a False it cannot distinguish from a measurement.
        self.assertNotIn("te_is_de_facto_receiver", bench.ordering_verdict({"WR": 1}))
        self.assertIs(bench.ordering_verdict({"WR": 1}, TE_SLOT)["te_is_de_facto_receiver"], False)

    def test_the_original_verdict_never_moves_when_a_rulebook_is_supplied(self):
        for rpos in (TE_SLOT, NO_TE_SLOT):
            for comp in ({"WR": 7, "RB": 4, "TE": 2, "QB": 1}, {"WR": 6, "RB": 6, "TE": 0, "QB": 2},
                         {"WR": 5, "RB": 3, "TE": 4, "QB": 2}, {"QB": 9}):
                bare = bench.ordering_verdict(comp)
                withrules = bench.ordering_verdict(comp, rpos)
                for key, value in bare.items():
                    self.assertEqual(withrules[key], value, msg=f"{key} {comp} {rpos[:3]}")


class TheDeFactoReceiverReadingTests(unittest.TestCase):
    def test_the_rulebook_decides_when_it_applies_not_this_function(self):
        self.assertTrue(bench.ordering_verdict({}, NO_TE_SLOT)["te_is_de_facto_receiver"])
        self.assertFalse(bench.ordering_verdict({}, TE_SLOT)["te_is_de_facto_receiver"])
        self.assertNotIn("pass_flex_te", bench.ordering_verdict({}, TE_SLOT))

    def test_the_zero_tight_end_roster_stops_being_the_winner(self):
        """THE DEFECT, in one assertion. Both rosters come from the owner's own league; the first
        is what the unfixed engine drafts there and the second is closer to what he built."""
        none_at_te = {"QB": 2, "RB": 6, "WR": 6, "TE": 0}
        his_shape = {"QB": 2, "RB": 6, "WR": 4, "TE": 2}
        self.assertTrue(bench.ordering_verdict(none_at_te, NO_TE_SLOT)["pass_strict"])
        self.assertFalse(bench.ordering_verdict(his_shape, NO_TE_SLOT)["pass_strict"])
        # Under the reading he actually described, both pass -- the rule stops discriminating
        # against the tight ends it is supposed to be agnostic about.
        self.assertTrue(bench.ordering_verdict(none_at_te, NO_TE_SLOT)["pass_flex_te"])
        self.assertTrue(bench.ordering_verdict(his_shape, NO_TE_SLOT)["pass_flex_te"])

    def test_it_still_fails_a_roster_that_is_genuinely_short_at_receiver(self):
        # Not a rubber stamp: folding TE into the receiving side must not pass a back-heavy
        # roster. WR 2 + TE 1 = 3 against RB 8.
        verdict = bench.ordering_verdict({"QB": 2, "RB": 8, "WR": 2, "TE": 1}, NO_TE_SLOT)
        self.assertFalse(verdict["WR+TE>=RB"])
        self.assertFalse(verdict["pass_flex_te"])

    def test_the_quarterback_ceiling_still_binds_under_the_second_reading(self):
        verdict = bench.ordering_verdict({"QB": 5, "RB": 2, "WR": 4, "TE": 2}, NO_TE_SLOT)
        self.assertTrue(verdict["WR+TE>=RB"])
        self.assertFalse(verdict["pass_flex_te"])      # QB <= 4 is still part of it


# ---------------------------------------------------------------------------------------
# MUTATION RESULTS
# ---------------------------------------------------------------------------------------
# O1 fold TE into the receiving side in EVERY league (drop the rulebook test)   CAUGHT
# O2 drop the QB ceiling from pass_flex_te                                      CAUGHT
# O3 report te_is_de_facto_receiver as False instead of omitting it             CAUGHT
# O4 let the second reading overwrite pass_strict                               CAUGHT
