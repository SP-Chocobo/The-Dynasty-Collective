"""#172: a player is eligible where his league can start him, not where a list happens to begin.

Sleeper sends `fantasy_positions`, a LIST, and this app read only its first element. That was
right for grouping -- one bucket per player, used for tables and sorting -- and wrong for three
questions that are not grouping questions:

    ADMISSION   an offence-only league dropped Travis Hunter, a wide receiver, because his
                list begins "DB". Measured on the committed capture: 6 players excluded from
                an offence-only league while eligible at a slot it starts; 0 in a full IDP one.
    MATCHING    his vendor row is a WR row, so the coarse identity-namespace rejection
                correctly refused it against a DB query -- a season projection of 94 and a
                trade value of 8 discarded on the most prominent two-way player in football.
    VALUATION   and the bucket selects the REPLACEMENT LEVEL his points are measured against,
                so filing a receiver's 94 under DB would have made him the best defensive back
                alive off a number that describes a receiver. That is #166 exactly: a quantity
                crossing a layer without the companion that gives it meaning.

The three are one repair, because fixing any one alone produces the crossed wire. Measured
end to end on the capture, EXACTLY ONE pool row changes: Travis Hunter, DB -> WR, gaining a
trade value of 8 and a projection of 94. 2105 rows in, 2105 rows out, nobody added or lost.

Every test here was mutation-checked -- see MUTATIONS at the bottom.
"""
import os
import unittest

import data_merger as dm
import draft_room as dr


class _StubMerger:
    """A merger whose answer per position is dictated by the test, so the DECISION rules can be
    exercised without depending on what a real vendor export happens to contain today."""

    def __init__(self, by_position):
        self.by_position = by_position
        self.asked = []

    def merge_player(self, name, position=None, team=None, df=None):
        self.asked.append(position)
        return self.by_position.get(position, {
            "matched": False, "match_path": None, "match_candidates": 0,
            "match_verified": False})


def _hit(key, **extra):
    row = {"matched": True, "match_path": "key", "match_candidates": 1,
           "match_verified": True, "match_canonical_key": key}
    row.update(extra)
    return row


class ResolvingAcrossEligibilityTests(unittest.TestCase):

    def test_a_single_position_player_is_asked_exactly_one_question(self):
        """The regression guard for everyone else in the pool: 2104 of 2105 rows must take the
        identical path they took before this existed."""
        stub = _StubMerger({"WR": _hit(("j chase", "offense"), trade_value=99.0)})
        got = dr._merge_across_eligibility(stub, "Ja'Marr Chase", {"WR"}, "WR", "CIN")
        self.assertEqual(stub.asked, ["WR"])
        self.assertEqual(got.get("trade_value"), 99.0)

    def test_the_primary_is_asked_first_and_wins_when_both_resolve(self):
        """Same canonical row reached from two positions is ONE answer, not an ambiguity, and
        the primary's own result is the one returned.

        The returned POSITION is the assertion that bites. "DB" is only reachable if the
        primary's result was recorded before the loop ran; recording it afterwards, or keying
        the collection by anything but the canonical row, hands back the secondary's copy and
        silently moves the player's valuation bucket."""
        stub = _StubMerger({
            "DB": _hit(("t hunter", "offense"), trade_value=8.0, position="DB"),
            "WR": _hit(("t hunter", "offense"), trade_value=8.0, position="WR"),
        })
        got = dr._merge_across_eligibility(stub, "Travis Hunter", {"DB", "WR"}, "DB", "JAX")
        self.assertEqual(stub.asked[0], "DB")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("position"), "DB")

    def test_a_secondary_position_can_supply_a_match_the_primary_missed(self):
        stub = _StubMerger({"WR": _hit(("t hunter", "offense"), trade_value=8.0, projection=94.0)})
        got = dr._merge_across_eligibility(stub, "Travis Hunter", {"DB", "WR"}, "DB", "JAX")
        self.assertTrue(got.get("matched"))
        self.assertEqual(got.get("projection"), 94.0)

    def test_two_DIFFERENT_rows_across_eligibility_decline(self):
        """Built despite measuring ZERO occurrences on this capture. At most one of two
        distinct canonical rows is this player and nothing here can say which; taking whichever
        position sorted first would be a coin flip presented as a resolution."""
        stub = _StubMerger({
            "DB": _hit(("t hunter", "idp"), trade_value=3.0),
            "WR": _hit(("t hunter", "offense"), trade_value=8.0),
        })
        got = dr._merge_across_eligibility(stub, "Travis Hunter", {"DB", "WR"}, "DB", "JAX")
        self.assertFalse(got.get("matched"))
        self.assertIsNone(got.get("trade_value"))
        self.assertEqual(got.get("match_candidates"), 2,
                         "an ambiguity decline must be distinguishable from finding nothing")

    def test_finding_nothing_anywhere_returns_the_primarys_own_miss(self):
        stub = _StubMerger({})
        got = dr._merge_across_eligibility(stub, "Nobody At All", {"DB", "WR"}, "DB", None)
        self.assertFalse(got.get("matched"))
        self.assertEqual(got.get("match_candidates"), 0)

    def test_every_eligible_position_is_actually_asked(self):
        stub = _StubMerger({})
        dr._merge_across_eligibility(stub, "Someone", {"DB", "WR", "LB"}, "DB", None)
        self.assertEqual(stub.asked[0], "DB")
        self.assertEqual(sorted(stub.asked), ["DB", "LB", "WR"])


class TheBucketMustAgreeWithThePriceTests(unittest.TestCase):
    """_pool_position -- which replacement level this player's points are measured against."""

    def test_a_priced_match_at_an_eligible_position_sets_the_bucket(self):
        match = _hit(("t hunter", "offense"), position="WR", projection=94.0)
        self.assertEqual(dr._pool_position("DB", {"DB", "WR"}, match), "WR")

    def test_a_match_carrying_NO_price_does_not_move_the_bucket(self):
        """Five real IDP players moved DL -> LB on exactly this shape before the condition was
        added -- the known DL/LB vocabulary split relabelling a man, and with him the
        replacement level he is measured against, off a row with no number in it."""
        match = _hit(("d ezeiruaku", "idp"), position="LB")
        self.assertEqual(dr._pool_position("DL", {"DL", "LB"}, match), "DL")

    def test_each_vendor_field_on_its_own_counts_as_a_price(self):
        for field, value in (("trade_value", 8.0), ("projection", 94.0), ("proj_3yr", 210.0)):
            with self.subTest(field=field):
                match = _hit(("t hunter", "offense"), position="WR", **{field: value})
                self.assertEqual(dr._pool_position("DB", {"DB", "WR"}, match), "WR")

    def test_a_matched_position_outside_his_eligibility_does_not_move_the_bucket(self):
        match = _hit(("x y", "offense"), position="TE", projection=100.0)
        self.assertEqual(dr._pool_position("WR", {"WR", "RB"}, match), "WR")

    def test_with_no_match_the_bucket_is_his_own_primary(self):
        miss = {"matched": False, "match_path": None, "match_candidates": 0}
        self.assertEqual(dr._pool_position("DB", {"DB", "WR"}, miss), "DB")

    def test_a_primary_this_league_cannot_start_falls_to_a_slot_it_can(self):
        # `eligible` arrives already intersected with the league's usable positions, so a
        # primary missing from it means this league has no such slot.
        miss = {"matched": False, "match_path": None, "match_candidates": 0}
        self.assertEqual(dr._pool_position("DB", {"WR"}, miss), "WR")

    def test_the_fallback_is_ordered_so_a_bucket_never_depends_on_set_iteration(self):
        """ACROSS PROCESSES, with different hash seeds -- because that is the actual property.

        The first version of this test called _pool_position five times in one process and
        asserted it returned "RB" each time. It passed, and it caught the unsorted mutation
        once and then stopped catching it, because set iteration order is stable WITHIN a
        process and varies BETWEEN them: whether `next(iter({"WR","RB","TE"}))` happens to be
        "RB" is a property of that run's PYTHONHASHSEED. A test whose verdict depends on the
        hash seed is not a test of determinism, it is a coin flip about one.

        So the seeds are set explicitly and the answers compared. A player's valuation bucket
        must not change because the interpreter started differently."""
        import subprocess
        import sys
        program = ("import draft_room as dr;"
                   "print(dr._pool_position('DB', {'WR', 'RB', 'TE'},"
                   " {'matched': False, 'match_path': None, 'match_candidates': 0}))")
        answers = set()
        for seed in ("0", "1", "12345", "99999"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            out = subprocess.run([sys.executable, "-c", program], cwd=os.path.dirname(
                os.path.abspath(__file__)), capture_output=True, text=True, env=env)
            self.assertEqual(out.returncode, 0, out.stderr)
            answers.add(out.stdout.strip())
        self.assertEqual(answers, {"RB"},
                         f"the bucket moved with the hash seed: {sorted(answers)}")


class AdmissionFollowsEligibilityTests(unittest.TestCase):
    """The half a mutation caught as untested: filtering on the primary bucket alone."""

    @classmethod
    def setUpClass(cls):
        import json
        cls.capture = json.load(open("data/fixtures/sleeper_capture.json"))
        cls.merger = dm.DataMerger()

    def _pool(self, usable):
        return dr.build_available_pool(self.merger, self.capture["players"], set(), usable,
                                       sleeper_projections=self.capture.get("season_projections"))

    def test_an_offence_only_league_admits_a_receiver_whose_list_begins_DB(self):
        pool = self._pool({"QB", "RB", "WR", "TE", "K", "DEF"})
        hunter = pool[pool["name"] == "Travis Hunter"]
        self.assertEqual(len(hunter), 1,
                         "a wide receiver was excluded from a league that starts wide receivers")
        self.assertEqual(hunter.iloc[0]["position"], "WR")

    def test_he_is_valued_at_the_position_his_number_was_earned_at(self):
        # The crossed wire this exists to prevent: a receiver's projection measured against a
        # defensive back's replacement level.
        pool = self._pool({"QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"})
        hunter = pool[pool["name"] == "Travis Hunter"].iloc[0]
        self.assertEqual(hunter["position"], "WR")
        self.assertIsNotNone(hunter["projection"])

    def test_a_player_with_no_usable_eligibility_is_still_excluded(self):
        """Non-vacuity: the widening must not have turned the filter off. A pure defensive
        lineman has nothing an offence-only league can start."""
        pool = self._pool({"QB", "RB", "WR", "TE", "K", "DEF"})
        self.assertEqual(set(pool["position"]) - {"QB", "RB", "WR", "TE", "K", "DEF"}, set())


class ThroughTheRealMergerTests(unittest.TestCase):
    """The stubs above pin the rules; these pin that the rules meet real data."""

    @classmethod
    def setUpClass(cls):
        cls.merger = dm.DataMerger()

    def test_the_two_way_player_resolves_through_his_receiver_eligibility(self):
        got = dr._merge_across_eligibility(
            self.merger, "Travis Hunter", {"DB", "WR"}, "DB", "JAX")
        self.assertTrue(got.get("matched"), "the live two-way case regressed")
        self.assertEqual(got.get("position"), "WR")
        self.assertIsNotNone(got.get("projection"))

    def test_asking_only_his_primary_bucket_still_misses(self):
        """Non-vacuity: the match above must come from the WIDENING, not from the name simply
        resolving anyway. This is the call the pool made before #172."""
        got = self.merger.merge_player("Travis Hunter", position="DB", team="JAX")
        self.assertFalse(got.get("matched"))

    def test_and_the_bucket_follows_the_price_to_receiver(self):
        got = dr._merge_across_eligibility(
            self.merger, "Travis Hunter", {"DB", "WR"}, "DB", "JAX")
        self.assertEqual(dr._pool_position("DB", {"DB", "WR"}, got), "WR")


# MUTATIONS -- each applied to draft_room.py, this file re-run, the named test observed to
# FAIL, then reverted:
#   1. _merge_across_eligibility: `others` computed but never iterated (return `first`)
#        -> ...test_a_secondary_position_can_supply_a_match_the_primary_missed FAILED
#   2. _merge_across_eligibility: drop the len(found) > 1 decline, return the first found
#        -> ...test_two_DIFFERENT_rows_across_eligibility_decline FAILED
#   3. _merge_across_eligibility: key `found` by identity rather than match_canonical_key, so
#      two positions onto ONE row read as an ambiguity
#        -> ...test_the_primary_is_asked_first_and_wins_when_both_resolve FAILED
#   4. _merge_across_eligibility: record the primary's result AFTER the loop instead of
#      before it, so a secondary position onto the SAME row wins the tie
#        -> ...test_the_primary_is_asked_first_and_wins_when_both_resolve FAILED
#      (a first attempt at this mutation merely reordered two lines with no behavioural
#       effect and survived; that is a badly-built mutation, not a passing one, and it was
#       rebuilt rather than recorded as a gap)
#   5. _pool_position: drop the `priced` condition
#        -> TheBucketMustAgreeWithThePrice.test_a_match_carrying_NO_price_does_not... FAILED
#   6. _pool_position: drop the `matched in eligible` guard
#        -> ...test_a_matched_position_outside_his_eligibility_does_not_move_the_bucket FAILED
#   7. _pool_position: return next(iter(eligible)) unsorted in the fallback
#        -> ...test_the_fallback_is_ordered_so_a_bucket_never_depends_on_set_iteration FAILED
#   8. build_available_pool: filter on `primary not in usable_positions` again
#        -> AdmissionFollowsEligibility.test_an_offence_only_league_admits_a_receiver... FAILED
#      This mutation SURVIVED the first pass. The claim in this comment was that
#      test_pool_admission_boundary covered it; it does not, and the admission half of this
#      repair had no test at all. AdmissionFollowsEligibilityTests exists because a mutation
#      said so, which is the entire point of running them.
if __name__ == "__main__":
    unittest.main()
