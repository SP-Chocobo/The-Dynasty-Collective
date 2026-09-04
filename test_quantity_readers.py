"""#141 / #138: every quantity the engine produces, and the guard that stops the family growing.

This codebase kept finding the same defect by hand -- waiting_cost, marginal_value_*, bye_week,
bench depth, trend_30d -- each one costing a session. The scanner finds them in one pass. This
suite is what makes the scanner trustworthy and then keeps it honest.

THE VALIDATION CLASS IS THE IMPORTANT ONE. A classifier with no ground truth is a generator of
confident opinions, and the first two attempts at this scanner proved it: one called
waiting_cost a DECISION input by scanning every dict literal, and the second called it that
again for a subtler reason (pick_synthesis is a scoring module and does read it -- to relay it
onward, never to consume it). Both were wrong in the same place. So the scanner is checked
against quantities whose answers were established independently, by measurement, earlier in
this work.
"""

from __future__ import annotations

import unittest

import quantity_readers as qr

#: Answers established elsewhere, by measurement rather than by this scanner. The scanner is
#: only as good as its agreement with these.
KNOWN = {
    # Wired into team_acquisition_value (#139) and pick_necessity (#48) respectively.
    "depth_exposure": qr.DECISION,
    "positional_forfeit": qr.DECISION,
    "need_bonus": qr.DECISION,
    "eligibility_bonus": qr.DECISION,
    "universal_value": qr.DECISION,
    # Deliberately observable: computed, displayed, never scored.
    "waiting_cost": qr.OBSERVABLE,
    "bye_collision": qr.OBSERVABLE,
    # #84's known case: marginal_lineup_value returns both lineup totals and only their
    # DIFFERENCE is consumed, so the absolute is genuinely read by nothing.
    "without_candidate": qr.WRITE_ONLY,
    # The term does real work as a local; its published column is unread (#119).
    "time_horizon_adj": qr.DECOMPOSITION,
    "risk_adj": qr.DECOMPOSITION,
}

#: The write-only set as it stands. This is a CHARACTERIZATION, not an approval -- most entries
#: are deliberate (sub-keys of dicts a caller stores whole, aggregates documented as returned
#: in pairs), and two are real gaps recorded below. Its job is to fail when the set GROWS.
KNOWN_WRITE_ONLY = {
    # bye_collision / bye_concentration sub-keys. roster_diagnostics stores those dicts whole,
    # so the individual keys await a reader rather than being dropped (#142).
    "bench_used", "bench_value_used", "players_out", "starters_out",
    "lineup_value", "total_loss", "worst_week_loss", "concentration",
    # depth_exposure returns BOTH aggregates on purpose -- "total risk carried" and "what one
    # backup buys" are different questions -- and only worst_loss is consumed (#139).
    "exposure",
    # marginal_lineup_value: only the difference is used (#84).
    "without_candidate",
    #
    # THE TWO REAL GAPS ARE GONE. replacement_basis and growth_signal were here until the
    # commit that carried both from the board row onto CandidateSnapshot, and from there into
    # draft_board_ui.serialize_candidate and draft_simulation.PickRecord. Both now scan as
    # `observable` with two readers each. They are NOT re-listed below as deliberate
    # exclusions, because that would be the "stale inventory describing an engine from months
    # ago" this file's own second test exists to prevent -- see
    # TheTwoRealGapsGainedReadersTests, which pins the new state from the other direction.
}


class TheScannerAgreesWithIndependentlyEstablishedAnswersTests(unittest.TestCase):
    """Non-vacuity for everything else here."""

    @classmethod
    def setUpClass(cls):
        cls.rows = {row["quantity"]: row for row in qr.scan()}

    def test_every_known_quantity_is_still_produced(self):
        """Guards the class below from passing because a quantity vanished from the surfaces."""
        missing = sorted(name for name in KNOWN if name not in self.rows)
        self.assertEqual(missing, [], f"declared known but no longer produced: {missing}")

    def test_each_known_quantity_gets_its_established_verdict(self):
        for quantity, expected in sorted(KNOWN.items()):
            with self.subTest(quantity=quantity):
                self.assertEqual(
                    self.rows[quantity]["verdict"], expected,
                    f"{quantity} was established as {expected} by measurement elsewhere. If the "
                    f"code genuinely changed, update KNOWN with the commit that changed it; if "
                    f"not, the scanner has regressed.")

    def test_a_relay_is_not_counted_as_a_consumer(self):
        """The specific trap that defeated two earlier versions. pick_synthesis IS a scoring
        module and DOES read waiting_cost -- only to copy it into the candidate dict. Its real
        terminus is the UI one hop later."""
        row = self.rows["waiting_cost"]
        self.assertNotIn("pick_synthesis.py", row["scoring_readers"],
                         "pick_synthesis relays waiting_cost; counting that as consumption "
                         "hides the write-only chains this scanner exists to find")

    def test_the_scanner_finds_a_meaningful_number_of_quantities(self):
        """A scanner over an empty surface set passes every other test in this file."""
        self.assertGreater(len(self.rows), 50)


class TheWriteOnlySetMustNotGrowTests(unittest.TestCase):
    """The durable value. Finding today's write-only quantities is worth one session; stopping
    the next one from being added silently is worth every session after."""

    @classmethod
    def setUpClass(cls):
        cls.found = {row["quantity"] for row in qr.write_only()}

    def test_no_new_write_only_quantity_has_appeared(self):
        added = sorted(self.found - KNOWN_WRITE_ONLY)
        self.assertEqual(
            added, [],
            f"new write-only quantities: {added}. Each is computed or carried and read by "
            f"nothing in production (#138). Either give it a reader, or add it to "
            f"KNOWN_WRITE_ONLY with a comment saying why it is deliberately unread.")

    def test_a_write_only_quantity_that_gained_a_reader_is_noticed(self):
        """The other direction, so the list cannot rot into a stale inventory that quietly
        describes an engine from months ago."""
        resolved = sorted(KNOWN_WRITE_ONLY - self.found)
        self.assertEqual(
            resolved, [],
            f"these are no longer write-only: {resolved}. Good -- remove them from "
            f"KNOWN_WRITE_ONLY and note which commit gave them a reader.")

    def test_the_two_real_gaps_gained_readers(self):
        """The inverse of what this test asserted until #138's second half. Both quantities
        were computed by compute_draft_board, placed on every board row, and dropped at
        pick_synthesis's raw_candidates boundary -- so no surface could read them however much
        it wanted to. They now reach CandidateSnapshot, serialize_candidate, and PickRecord.

        Kept as an explicit assertion rather than deleted: "these two are no longer write-only"
        is a claim worth failing on if a future refactor drops the carry again, and a silently
        absent test would not."""
        for quantity in ("replacement_basis", "growth_signal"):
            with self.subTest(quantity=quantity):
                self.assertNotIn(
                    quantity, self.found,
                    f"{quantity} is write-only again -- the raw_candidates carry was dropped")

    def test_both_gained_readers_that_are_not_merely_relays(self):
        """A carry into a dict is not consumption -- that is the trap
        test_a_relay_is_not_counted_as_a_consumer pins for waiting_cost. pick_synthesis is a
        CARRIER for both of these; the terminus has to be somewhere else, and it is."""
        rows = {row["quantity"]: row for row in qr.scan()}
        for quantity in ("replacement_basis", "growth_signal"):
            with self.subTest(quantity=quantity):
                row = rows[quantity]
                self.assertEqual(row["verdict"], qr.OBSERVABLE)
                self.assertIn("pick_synthesis.py", row["carriers"],
                              "pick_synthesis relays these; it is not their consumer")
                self.assertTrue(
                    set(row["observing_readers"]) >= {"draft_board_ui.py", "draft_simulation.py"},
                    f"expected both the serializer and the retained record to read "
                    f"{quantity}, got {row['observing_readers']}")


class TheClassificationIsWellFormedTests(unittest.TestCase):
    def test_every_quantity_gets_exactly_one_verdict(self):
        verdicts = {qr.DECISION, qr.OBSERVABLE, qr.DECOMPOSITION, qr.CARRIED, qr.WRITE_ONLY}
        for row in qr.scan():
            with self.subTest(quantity=row["quantity"]):
                self.assertIn(row["verdict"], verdicts)

    def test_a_decision_quantity_names_the_module_that_consumes_it(self):
        """A verdict with no evidence behind it is an opinion. Every DECISION must be able to
        say which scoring module actually reads it."""
        for row in qr.scan():
            if row["verdict"] == qr.DECISION:
                with self.subTest(quantity=row["quantity"]):
                    self.assertTrue(row["scoring_readers"])

    def test_tests_are_not_counted_as_readers(self):
        """A quantity exercised only by its own test is still write-only in production, and
        counting tests would hide precisely the cases worth finding."""
        modules = {path.name for path in qr._production_modules()}
        self.assertFalse([m for m in modules if m.startswith("test_")])
        self.assertFalse([m for m in modules if m.startswith("run_")],
                         "measurement scripts must not count as readers either -- an instrument "
                         "reading a quantity does not make that quantity load-bearing")


if __name__ == "__main__":
    unittest.main()
