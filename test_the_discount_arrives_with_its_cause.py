"""MANDATE 2.5 / `#166`: the injury DISCOUNT crossed the snapshot boundary and the DESIGNATION did not.

`risk_adj` is carried into `CandidateSnapshot` (`#119`, so a price can be explained rather than only
asserted) and part of what it is made of is `draft_room.health_penalty` — a cut taken for a
designation Sleeper reported. The designation itself, and `availability_basis` beside it, stayed on
the board. So a chair received the penalty with nothing to attribute it to.

AND THE SKEPTIC WAS TOLD THE ENGINE IS BLIND TO IT. Its instructions said "these numbers don't know
about bye weeks, a player's specific injury history, or a personality clash" — true of history and
prognosis, false of the CURRENT designation, which the engine holds and has already priced. A prompt
that tells a model to distrust a figure the engine actually computed invites exactly the
second-guessing the same prompt forbids two paragraphs later ("these numbers are the only numbers
that exist. Never invent or recompute a figure of your own").

THE BASIS TRAVELS WITH THE STATUS, and that is not decoration. `health_penalty` returns 0.0 when
`availability_basis` is `RULE_FLOOR`, because the games the designation costs are already out of the
projection and charging a penalty on top would double-count them. A chair told only "Out" would make
that same double-count in its own reasoning.
"""
from __future__ import annotations

import ast
import dataclasses
import unittest
from pathlib import Path

import draft_history
import draft_history_ui as dhui
import draft_room as dr
import pick_debate as pd
import pick_synthesis as ps
import player_universe as pu
from test_pick_debate import _candidate, _snapshot


def _with(**over):
    candidate = _candidate("1", "A Player")
    for field, value in over.items():
        object.__setattr__(candidate, field, value)
    return candidate


class TheBoundaryCarriesBoth(unittest.TestCase):
    """The snapshot is where the drop happened, so this is where the repair has to be."""

    def test_the_snapshot_declares_both_fields(self):
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("injury_status", names)
        self.assertIn("availability_basis", names)

    def test_both_are_optional_so_an_ABSENT_status_stays_absent(self):
        """`#187`: an unreported designation must not arrive as a healthy one. The default is None
        and None means "nothing was reported", which is not a claim about the player."""
        hints = {f.name: f for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIsNone(hints["injury_status"].default)
        self.assertIsNone(hints["availability_basis"].default)

    def test_the_board_has_emitted_both_all_along(self):
        """Non-vacuity: if the board did not carry these, the repair would be inventing data rather
        than forwarding it, and that is a different and much weaker claim."""
        self.assertIn("injury_status", dr.BALANCED_BOARD_COLUMNS)
        self.assertIn("availability_basis", dr.BALANCED_BOARD_COLUMNS)

    def test_the_term_they_explain_is_carried_too(self):
        """The pairing is the point. `risk_adj` without the designation is a penalty with no cause;
        the designation without `risk_adj` is a cause with no effect."""
        names = {f.name for f in dataclasses.fields(ps.CandidateSnapshot)}
        self.assertIn("risk_adj", names)


class TheChairsAreToldTheCauseOfTheDiscount(unittest.TestCase):
    """And told which of the two health regimes applies, because they price differently."""

    def test_a_designation_priced_by_the_RULE_FLOOR_says_no_penalty_was_added(self):
        text = pd._format_candidate(
            _with(injury_status="Out", availability_basis=pu.RULE_FLOOR), None)
        self.assertIn("Out", text)
        self.assertIn("ALREADY REMOVED", text)

    def test_a_designation_priced_by_the_PENALTY_says_the_discount_is_in_the_value(self):
        text = pd._format_candidate(
            _with(injury_status="Out", availability_basis=pu.NO_DESIGNATION), None)
        self.assertIn("Out", text)
        self.assertIn("health discount is already inside", text)

    def test_the_two_regimes_do_not_read_the_same(self):
        """They are different claims about the same designation, and `health_penalty` really does
        branch on exactly this — so the prose has to branch with it or it misdescribes one arm."""
        floored = pd._format_candidate(
            _with(injury_status="Out", availability_basis=pu.RULE_FLOOR), None)
        penalised = pd._format_candidate(
            _with(injury_status="Out", availability_basis=pu.NO_DESIGNATION), None)
        self.assertNotEqual(floored, penalised)
        self.assertEqual(dr.health_penalty("Out", pu.RULE_FLOOR), 0.0)
        self.assertNotEqual(dr.health_penalty("Out", pu.NO_DESIGNATION), 0.0)

    def test_an_unreported_designation_says_NOTHING_rather_than_healthy(self):
        text = pd._format_candidate(_with(injury_status=None), None)
        self.assertNotIn("Injury designation", text)
        self.assertNotIn("healthy", text.lower())

    def test_an_empty_string_is_treated_as_unreported_too(self):
        """Sleeper sends "" for a player with no designation, and a truthiness test is what keeps
        that from rendering as a designation named nothing."""
        self.assertNotIn("Injury designation", pd._format_candidate(_with(injury_status=""), None))


class TheSkepticsClaimIsNoLongerFalse(unittest.TestCase):
    """The prompt is the other half. Carrying the field and leaving the instruction in place would
    have left a chair told to distrust a number the engine had just handed it."""

    def _skeptic_text(self):
        """The Skeptic's instructions, found by their own content rather than by a constant name --
        read as PARSED STRINGS (`#200`), so reflowing the prompt is not a pass and a comment that
        happens to quote it is not a match."""
        tree = ast.parse(Path("pick_debate.py").read_text(encoding="utf-8"))
        return "\n".join(
            node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            and "pressure-test that case" in node.value)

    def test_it_no_longer_claims_the_numbers_do_not_know_about_injuries(self):
        text = self._skeptic_text()
        self.assertTrue(text, "the Skeptic's instructions were not found, so this proves nothing")
        self.assertNotIn("a player's specific injury history, or a personality clash", text,
                         "the false half of the claim is still in the prompt")

    def test_it_says_the_CURRENT_designation_is_given_and_already_priced(self):
        text = self._skeptic_text()
        self.assertIn("designation IS given", text)
        self.assertIn("already inside the universal value", text)

    def test_it_still_names_the_gap_that_is_REAL(self):
        """The correction must not overshoot into "the engine knows about injuries". It knows a
        current designation; it does not know a history or a prognosis, and that gap was worth
        telling the Skeptic about in the first place."""
        text = self._skeptic_text()
        self.assertIn("HISTORY", text)
        self.assertIn("prognosis", text)
        self.assertIn("bye weeks", text, "an unrelated real gap was dropped by the edit")


class TheBOARDToSNAPSHOTCarryIsRealAndNotJustDeclared(unittest.TestCase):
    """A field on the dataclass that `build_snapshot` never populates is a hole that reads as a
    healthy player on every board. Read off the PARSED source of `build_snapshot` (`#200`), because
    what matters is that the key is read from the row and not defaulted."""

    def _build_snapshot_source(self):
        tree = ast.parse(Path("pick_synthesis.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "build_snapshot":
                return ast.unparse(node)
        self.fail("build_snapshot was not found in pick_synthesis")

    def test_it_reads_both_keys_off_the_board_row(self):
        source = self._build_snapshot_source()
        self.assertIn("row.get('injury_status')", source)
        self.assertIn("row.get('availability_basis')", source)

    def test_NEITHER_is_read_with_a_default(self):
        """`row.get(key, anything)` is the fabrication this whole mandate item is about -- it is how
        `need_bonus` became a measured zero one commit earlier."""
        source = self._build_snapshot_source()
        for key in ("injury_status", "availability_basis"):
            self.assertNotIn(f"row.get('{key}',", source,
                             f"{key} is read with a default, so an absence becomes a value")


class TheStoredRecordCarriesItToo(unittest.TestCase):
    """The other half of the same mandate item: a persisted board shipping a number without the
    companion its own contract requires. A record with a health-adjusted price and no designation
    beside it cannot be read back."""

    def test_the_projection_records_both(self):
        self.assertIn("injury_status", draft_history._CANDIDATE_EVIDENCE_FIELDS)
        self.assertIn("availability_basis", draft_history._CANDIDATE_EVIDENCE_FIELDS)

    def test_the_schema_version_moved_for_the_shape_change(self):
        """Append-only store: a shape change gets a new number and older records keep theirs."""
        self.assertGreaterEqual(draft_history.EVIDENCE_SCHEMA_VERSION, 4)

    def test_a_recorded_candidate_really_carries_the_designation(self):
        snap = _snapshot([_with(injury_status="IR", availability_basis=pu.RULE_FLOOR)])
        row = draft_history.evidence_projection(snap, "x")["candidates"][0]
        self.assertEqual(row["injury_status"], "IR")
        self.assertEqual(row["availability_basis"], pu.RULE_FLOOR)

    def test_an_absent_designation_is_stored_as_null_not_as_healthy(self):
        snap = _snapshot([_with(injury_status=None)])
        row = draft_history.evidence_projection(snap, "x")["candidates"][0]
        self.assertIsNone(row["injury_status"])

    def test_the_reader_shows_it_and_marks_an_absent_one_absent(self):
        record = {"evidence": {"candidates": [
            {name: None for name in draft_history._CANDIDATE_EVIDENCE_FIELDS}]}}
        record["evidence"]["candidates"][0].update({"name": "A Player", "injury_status": "IR"})
        self.assertEqual(dhui.stored_candidate_rows(record)[0]["Injury"], "IR")
        record["evidence"]["candidates"][0]["injury_status"] = None
        self.assertEqual(dhui.stored_candidate_rows(record)[0]["Injury"], dhui.ABSENT)


if __name__ == "__main__":
    unittest.main()
