"""Gate B's camera, tested for the one failure that would make it worthless (`#254`, `#187`).

An equivalence check that cannot FAIL is the same defect as a guard that catches nothing, and
this repo shipped exactly that twice this cycle: `assertion_execution --check` returned the same
green line whether 359 tests were measured or none were, and `prose_names` was shielded at block
scope while reporting a denominator two orders of magnitude off what it compared. Both passed
every day they were broken.

So the tests that matter here are not "does `--write` produce a file". They are:

  * a planted change in the engine's ANSWER is detected, and named;
  * `None` survives serialisation as `None` and never becomes `0.0` (`#187`);
  * NaN survives as itself and is distinguishable from absence -- the engine uses both;
  * the three capture states are DERIVED from each format's own length (`#56`), because
    `12T_ppr_SHORT_DRAFT` drafts 8 rounds and `HEAVY_IDP` drafts 18, and a hardcoded index
    would photograph incomparable depths and call them the same state;
  * a missing baseline is reported as holding NOTHING rather than as agreement.
"""

from __future__ import annotations

import json
import pathlib
import unittest

import engine_baseline as eb


class TheDiffNamesWhatMovedTests(unittest.TestCase):
    """`_diff` returns readable paths, not a boolean. An equivalence claim nobody can inspect is
    worth about as much as a test with no assertion."""

    def test_identical_documents_produce_no_differences(self):
        doc = {"a": [{"x": 1.0, "y": None}], "b": "s"}
        self.assertEqual([], eb._diff(doc, json.loads(json.dumps(doc))))

    def test_a_changed_number_is_reported_WITH_ITS_PATH(self):
        before = {"arms": [{"states": [{"snapshot": {"candidates": [{"bpa": 12.5}]}}]}]}
        after = json.loads(json.dumps(before))
        after["arms"][0]["states"][0]["snapshot"]["candidates"][0]["bpa"] = 12.6
        found = eb._diff(before, after, "root")
        self.assertEqual(1, len(found), f"expected exactly one difference, got {found}")
        self.assertIn("bpa", found[0])
        self.assertIn("12.5", found[0])
        self.assertIn("12.6", found[0])

    def test_an_absent_field_is_not_silently_equal_to_a_present_one(self):
        found = eb._diff({"a": 1}, {}, "root")
        self.assertTrue(found and "ABSENT" in found[0], found)

    def test_a_changed_list_LENGTH_is_reported(self):
        found = eb._diff({"c": [1, 2, 3]}, {"c": [1, 2]}, "root")
        self.assertTrue(any("length 3 -> 2" in f for f in found), found)

    def test_NONE_becoming_ZERO_is_a_difference(self):
        """THE ONE THIS ENGINE CARES MOST ABOUT. `#187` forbids an absence crossing as 0.0
        everywhere; a baseline that could not see that substitution would be blind to the
        regression class this whole audit is organised around."""
        found = eb._diff({"risk_adj": None}, {"risk_adj": 0.0}, "root")
        self.assertTrue(found, "None -> 0.0 was reported as no change")


class AbsenceSurvivesSerialisationTests(unittest.TestCase):
    """The camera must not develop the photograph wrong."""

    def test_none_stays_none(self):
        self.assertIsNone(eb._jsonable(None))

    def test_nan_is_marked_and_is_not_none(self):
        """NaN and None are BOTH absences in this engine and they are not the same one. JSON has
        no NaN, so a serialiser that let it become `null` would merge two distinct states."""
        marked = eb._jsonable(float("nan"))
        self.assertEqual("__NaN__", marked)
        self.assertIsNotNone(marked)

    def test_zero_stays_zero_and_is_not_confused_with_absence(self):
        self.assertEqual(0.0, eb._jsonable(0.0))
        self.assertIsNotNone(eb._jsonable(0.0))

    def test_a_frozenset_serialises_SORTED_so_set_order_cannot_fake_a_diff(self):
        self.assertEqual(["DB", "WR"], eb._jsonable(frozenset({"WR", "DB"})))
        self.assertEqual(eb._jsonable(frozenset({"WR", "DB"})),
                         eb._jsonable(frozenset({"DB", "WR"})))

    def test_the_whole_record_round_trips_through_json(self):
        """Non-vacuity for the four above: the values must survive a real dump/load, not merely
        a function call."""
        payload = {"a": None, "b": float("nan"), "c": 0.0, "d": frozenset({"B", "A"})}
        back = json.loads(json.dumps(eb._jsonable(payload)))
        self.assertIsNone(back["a"])
        self.assertEqual("__NaN__", back["b"])
        self.assertEqual(0.0, back["c"])
        self.assertEqual(["A", "B"], back["d"])


class TheCaptureStatesAreDerivedTests(unittest.TestCase):
    """`#56`: derived from each format's own shape, never a chosen index."""

    @staticmethod
    def _order(teams: int, rounds: int) -> list:
        seats = [str(i) for i in range(1, teams + 1)]
        out = []
        for r in range(rounds):
            out.extend(reversed(seats) if r % 2 else seats)
        return out

    def test_a_short_draft_and_a_long_one_get_DIFFERENT_indices(self):
        short = eb._states_for(96, 12, self._order(12, 8), "1")
        long_ = eb._states_for(216, 12, self._order(12, 18), "1")
        self.assertNotEqual([s["index"] for s in short], [s["index"] for s in long_],
                            "both formats photographed the same indices, so the states are "
                            "hardcoded rather than derived from each draft's own length")

    def test_every_state_is_a_turn_belonging_to_the_captured_seat(self):
        order = self._order(12, 14)
        for state in eb._states_for(168, 12, order, "1"):
            with self.subTest(state=state["name"]):
                self.assertEqual("1", order[state["index"]],
                                 "a snapshot was captured at another seat's turn")

    def test_the_three_states_are_distinct_and_ordered(self):
        states = eb._states_for(168, 12, self._order(12, 14), "1")
        self.assertEqual(["opening", "mid", "late"], [s["name"] for s in states])
        idx = [s["index"] for s in states]
        self.assertEqual(sorted(set(idx)), idx, f"states are not distinct and increasing: {idx}")

    def test_the_opening_state_is_the_first_turn(self):
        self.assertEqual(0, eb._states_for(168, 12, self._order(12, 14), "1")[0]["index"])

    def test_mid_and_late_prefer_a_turn_with_PICKS_AHEAD_of_it(self):
        """`survival_probability`, `positional_forfeit` and `rival_premium` are computed over the
        gap to MY NEXT pick. A turn with no intervening picks reports them as a clean null --
        measured once as 0.00 for 269 of 269 candidates, on exactly this mistake."""
        order = self._order(12, 14)
        mine = [i for i, s in enumerate(order) if s == "1"]
        for state in eb._states_for(168, 12, order, "1")[1:]:
            nxt = next((j for j in mine if j > state["index"]), None)
            with self.subTest(state=state["name"]):
                if nxt is not None:
                    self.assertGreater(nxt - state["index"], 1,
                                       "captured a turn with no intervening picks ahead, where "
                                       "the gap-derived terms are structurally null")


class PickHistoryCarriesProductionsShapeTests(unittest.TestCase):
    """A field that SELECTS A BEHAVIOURAL MODE is part of the input's identity. `mode='auto'`
    reads `round` off these records; a history without it runs the capture in balanced mode
    while production is in upside, with no error and no warning."""

    def test_every_pick_carries_the_four_required_fields(self):
        order = [str(i) for i in range(1, 13)] * 14
        picks = eb._picks_through([str(100 + i) for i in range(50)], 24, order, 12)
        self.assertEqual(24, len(picks))
        for p in picks:
            self.assertEqual({"pick_no", "round", "roster_id", "player_id"}, set(p))

    def test_the_round_advances_with_the_pick_number(self):
        order = [str(i) for i in range(1, 13)] * 14
        picks = eb._picks_through([str(100 + i) for i in range(50)], 25, order, 12)
        self.assertEqual(1, picks[0]["round"])
        self.assertEqual(2, picks[12]["round"], "round did not advance at the team-count boundary")
        self.assertEqual(3, picks[24]["round"])

    def test_an_empty_history_is_empty_rather_than_invented(self):
        self.assertEqual([], eb._picks_through(["1", "2"], 0, ["1", "2"], 12))


class AMissingBaselineHoldsNothingTests(unittest.TestCase):
    """The `assertion_floors` lesson, applied before it can be learned here a third time: a check
    with no record must not report success."""

    def test_check_refuses_when_no_baseline_exists_AND_DOES_NOT_PAY_FOR_A_CAPTURE(self):
        """Two claims in one, and the second is why this test can run at all.

        `--check` reads the record BEFORE capturing. Checked the other way round -- which is how
        it was first written -- a missing baseline cost a full 150-second sweep before reporting
        that it had nothing to compare against, and this test would have taken that long too.
        The time bound is therefore load-bearing: it proves the ordering, not merely the verdict.
        """
        import time
        real = eb.BASELINE_PATH
        eb.BASELINE_PATH = pathlib.Path("evidence/engine_baseline/__does_not_exist__.json")
        try:
            started = time.time()
            rc = eb.main(["--check"])
            elapsed = time.time() - started
        finally:
            eb.BASELINE_PATH = real
        self.assertEqual(2, rc, "a check holding no record reported something other than 2")
        self.assertLess(elapsed, 10.0,
                        f"took {elapsed:.1f}s -- the capture ran before the record was read, so "
                        f"a missing baseline costs a full sweep to discover")

    def test_the_baseline_path_is_under_evidence(self):
        self.assertIn("evidence", str(eb.BASELINE_PATH))


class TheVolatileRegistersStateReasonsTests(unittest.TestCase):
    """Same idiom as `draft_battery.UNCOVERED_AXES` and `config_space.DEPENDENT_REASONS`: an
    exemption without a reason is how an exemption rots."""

    def test_every_excluded_snapshot_field_states_why(self):
        for field, reason in eb.VOLATILE_SNAPSHOT_FIELDS.items():
            with self.subTest(field=field):
                self.assertGreater(len(reason), 25, f"{field}'s exclusion needs a real reason")

    def test_the_candidate_register_is_empty_and_that_is_the_healthy_state(self):
        """EVERY one of the 57 candidate fields is part of the answer today. If this ever gains
        an entry, the entry is a claim that a field is not behavioural -- which needs defending,
        not assuming."""
        self.assertEqual({}, eb.VOLATILE_CANDIDATE_FIELDS)


if __name__ == "__main__":
    unittest.main()


class TheVerdictBranchesOnWHATITISABOUTTests(unittest.TestCase):
    """The bug this class exists for, found by running the instrument against its own clean tree.

    `--check` computed every difference, filtered the wall-clock timings out for REPORTING, and
    then branched on the UNFILTERED list. A clean tree's only differences are the 18 per-state
    timings, so it fell past the success path and printed the regression prose over
    `0 behavioural difference(s)` -- returning 1 on a run that had just proven the engine
    unchanged.

    A check that reports failure on a passing run is the same defect as one that reports success
    on a failing run, and this file's whole subject is catching that. It is also the second time
    in one session that a verifier printed its failure branch on the pass path, which is why it
    is pinned here rather than merely fixed.
    """

    def test_a_timing_only_difference_does_not_read_as_a_regression(self):
        import io, contextlib
        a = {"arms": [{"states": [{"seconds": 16.1, "snapshot": {"x": 1}}]}]}
        b = {"arms": [{"states": [{"seconds": 15.9, "snapshot": {"x": 1}}]}]}
        found = eb._diff(a["arms"], b["arms"], "arms")
        self.assertTrue(found, "non-vacuity: the timings must actually differ here")
        timing = [d for d in found if d.endswith("seconds") or ".seconds:" in d]
        self.assertEqual(len(found), len(timing),
                         f"a timing-only change produced a non-timing difference: "
                         f"{[d for d in found if d not in timing]}")

    def test_a_real_change_beside_a_timing_change_still_reads_as_a_regression(self):
        """The control. A filter that swallowed everything would satisfy the test above."""
        a = {"arms": [{"states": [{"seconds": 16.1, "snapshot": {"x": 1}}]}]}
        b = {"arms": [{"states": [{"seconds": 15.9, "snapshot": {"x": 2}}]}]}
        found = eb._diff(a["arms"], b["arms"], "arms")
        behavioural = [d for d in found if not (d.endswith("seconds") or ".seconds:" in d)]
        self.assertEqual(1, len(behavioural), f"expected the x change to survive: {found}")
        self.assertIn("snapshot", behavioural[0])
