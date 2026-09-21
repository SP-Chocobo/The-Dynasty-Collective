"""Every owner ruling is either IMPLEMENTED or STAGED WITH ITS REASON. Nothing is just forgotten.

`#52` produced seven engine-design decisions that `#56` and `#184` put with the owner. They were
ruled, recorded in `CDME_CONTRACTS.md`, and are being implemented one at a time -- and two of
them stopped partway, each because implementing the ruling faithfully turned out to force a
SECOND derivation the ruling did not cover:

  * `6.1b` unify -- NOW IMPLEMENTED (see IMPLEMENTED below). It was its own pass, as staged:
    the retirement moved NECESSITY_DENIAL_SATURATION 36.0 -> 24.0, which is the second
    derivation that stopped it here in the first place.
  * `W1-07` substitute -- implemented and measured at a 62% label-flip rate against a ruling
    made on a 3.1% one, because `intervening_picks` is a property of the turn and
    `(1 - survival)` was a property of the player. It forces re-deriving five label thresholds.

    THAT DIFFERENCE IS NOW MEASURED, not just stated (`evidence/w1_07/`). At five real turns,
    `intervening_picks` takes exactly ONE distinct value across all 46-48 candidates in the
    snapshot, while `survival_probability` takes 6 to 13. So the substitute cannot
    differentiate candidates under ANY scaling: it shifts every candidate's necessity by the
    same amount, which is why labels cross band thresholds in bulk while the ordering is
    untouched. A denominator question is downstream of that, and this is the prior objection.

A markdown note is not a guard. This file is, and it fires in BOTH directions:

  * a staged ruling whose patch has vanished fails here, so the work cannot be quietly dropped;
  * a staged ruling that someone IMPLEMENTS fails here too, so the record cannot silently go out
    of date with the code -- the exact `#166` shape this programme keeps closing.

To close a ruling: implement it, then move its entry from STAGED to IMPLEMENTED below and say
where the evidence lives. The test is what makes that a step rather than an intention.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import ui_source

_HERE = Path(__file__).parent


def _source(module: str) -> str:
    """The text a witness is checked against, from ONE place (#126).

    `app.py` is NOT read off disk. It is a 6,000-line top-level Streamlit script that cannot be
    imported, and `test_ui_source` forbids test modules from reading it directly so that a
    source-scanning contract survives the hull extraction -- a guard pointed at `app.py` after
    its code moves to a view passes forever while guarding nothing. `ui_source.text()` is the
    sanctioned reader and follows the code across that move.

    Caught by the FULL SUITE rather than by a targeted run: the J-12 witness below named
    `app.py`, and the first version of this file read it with `(_HERE / module).read_text()`.
    """
    if module == "app.py":
        return ui_source.text()
    return (_HERE / module).read_text()

#: One entry per ruling that is NOT yet in the engine. `witness` is a fact about the source that
#: is true while the ruling is unimplemented and false once it is -- so this table cannot drift
#: away from the tree it describes. `patch` is the staged work; `why` must be non-trivial,
#: because "staged" without a reason is indistinguishable from "abandoned".
STAGED = {
    "W1-07": {
        "witness": ("pick_synthesis.py", "NECESSITY_SURVIVAL_WEIGHT = 20.0"),
        "patch": "evidence/blind_pass/w1_07_substitute.patch",
        "why": "implementing it flips 62% of labels against a ruling made on 3.1%, because the "
               "substitute is a property of the TURN and the quantity it replaces was a "
               "property of the PLAYER. Forces re-deriving five label thresholds -- a second "
               "#56 exercise the ruling did not cover, and the owner's call.",
    },
}

#: One entry per ruling that IS now in the engine. `witness` here is the INVERSE of STAGED's:
#: a fact about the source that is true only once the ruling has landed. So this table cannot
#: drift either -- a revert, a bad merge, or a cherry-pick that drops the work fails the test
#: below instead of leaving a record claiming something the tree does not do.
IMPLEMENTED = {
    "6.1b": {
        "witness": ("draft_room.py", "TEAM_SPECIFIC_TERMS = (\"need_bonus\", \"depth_exposure\""),
        "landed": "eligibility_bonus retired from the board, the snapshot, the payload and the "
                  "four vocabulary registries. lineup_optimizer.eligibility_bonus -- the "
                  "FUNCTION -- is untouched: the ruling retired a board term, not a calculation.",
        "cost": "NECESSITY_DENIAL_SATURATION moved 36.0 -> 24.0, because eligibility_bonus's cap "
                "was a member of TEAM_SPECIFIC_CAPS. A derivation over a smaller input, not a "
                "chosen constant, so #56 is not engaged -- but a live behaviour change: no row "
                "saturates (max premium 10.32 of 7,595), so what moved is the ramp, and every "
                "row's denial component scales by exactly 1.5x, worst case +2.87 of 100.",
        "evidence": "evidence/blind_pass/KDST_VALUATION.md",
    },
    # THESE TWO WERE IMPLEMENTED AND NEVER RECORDED HERE, which is the gap this file exists to
    # close in the other direction. Both landed with their ruling tag in the source and their
    # own guard test, and both were still listed as pending work in CDME_CONTRACTS' ruling
    # table -- so a reader going to the authority saw seven open rulings when two were done.
    "J-12": {
        "witness": ("app.py", "draft_history.record_snapshot("),
        "landed": "wired NARROWLY, as ruled: a snapshot is recorded only when a debate actually "
                  "ran on that board. Not at every board build -- the Draft Room rebuilds a "
                  "snapshot on every rerun, including reruns caused by an unrelated button, so "
                  "recording each one would fill the store with boards nobody looked at.",
        "cost": "none to any computed value; this only writes. The write is wrapped so a failed "
                "record cannot take down a live draft, which is the module's own contract for a "
                "damaged history file applied to the write path too.",
        "evidence": "test_draft_history_is_wired.py",
    },
    "J-13": {
        "witness": ("sleeper_client.py", "no player universe available"),
        "landed": "get_players() RAISES SleeperAPIError instead of returning {}. An empty dict "
                  "was a player universe indistinguishable from 'there are no players', and "
                  "every caller then built a board, a roster table or a sync against nothing "
                  "and reported the result as an answer.",
        "cost": "the same phase also made the cache write atomic via store_io.replace_atomically "
                "-- write_text TRUNCATES before writing, which is the mechanism behind the "
                "91,956 empty reads of 98,405 this ruling was measured from.",
        "evidence": "test_no_empty_player_universe.py",
    },
}

#: One entry per ruling that is CHARACTERIZED but blocked on a SECOND owner decision -- neither
#: implemented nor staged, because there is no patch to stage until the boundary is ruled. This
#: category did not exist and its absence is what let J-12 and J-13 sit in no table at all while
#: the census below passed: the census only asked whether a ruling was NAMED in the contracts
#: file, which every ruling is by construction. `witness` follows STAGED's sense -- true while
#: the decision is open, false once it lands.
AWAITING_RULING = {
    "6.1d.1": {
        "witness": ("test_threshold_reachability.py", "@unittest.expectedFailure"),
        "why": "the DERIVATION half shipped (CONTEXT_ELEVATED_THRESHOLD = max(TEAM_SPECIFIC_CAPS), "
               "behaviour-free, because the two capped terms are mutually exclusive -- 0 "
               "co-occurrences in 10,887 priced rows). The PRODUCT half is open: the badge fires "
               "on ONE row across all 36 battery formats, so it needs a different quantity or "
               "retirement, and picking a threshold that makes the current one fire is #56.",
        "evidence": "evidence/context_elevated/THE_CEILING_IS_MAX_NOT_SUM.md",
    },
    "I-06/J-06": {
        "witness": ("lineup_optimizer.py", "else EXPOSURE_NO_SURPLUS)"),
        "why": "step 1 as written -- add a token for the measured-uncovered case -- takes "
               "EXPOSURE_NO_SURPLUS's ENTIRE population and leaves it unreachable, the "
               "unreachable-predicate shape basis_semantics.py names as the 18th withdrawal. "
               "Both boundaries that would keep two tokens reachable are ones this repo already "
               "rejected: an eligibility rule (measured WRONG in depth_exposure's own docstring) "
               "and the roster-wide has-any-bench boolean (deleted by this item's own repair).",
        "evidence": "evidence/i06_j06/STEP_ONE_NEEDS_A_BOUNDARY.md",
    },
    "W4-01": {
        "witness": ("draft_room.py", "rookie_by_key.get("),
        "why": "MEASURED AND REJECTED. The ruling's premise is false: years_exp == 0 is not "
               "'this year's rookie class' but 'the feed carries no accrued-seasons value', "
               "which retired players also carry. Promoting it takes a rookie board from 59 to "
               "333 rows, trading 7 rostered+priced players for 281 that are 26% rostered and "
               "6% priced -- including Kurt Warner, age 47. The live question left is narrower "
               "and reverses #193's tested ruling, so it is the owner's.",
        "evidence": "evidence/w4_01/THE_PREMISE_IS_FALSE.md",
    },
}

#: Where a reader goes for the measurement behind each one. Checked for existence, not parsed:
#: this file's job is to make the pin fire, not to restate the evidence.
EVIDENCE = "evidence/blind_pass/RULINGS_EXECUTION.md"


class NoRulingIsSilentlyDroppedTests(unittest.TestCase):

    def test_every_staged_ruling_still_has_its_staged_work(self):
        """A patch that vanished is work lost, and the ruling would then look merely undone
        rather than three-quarters finished."""
        for ruling, entry in STAGED.items():
            with self.subTest(ruling=ruling):
                patch = _HERE / entry["patch"]
                self.assertTrue(patch.exists(), f"{ruling}: staged patch is gone ({patch})")
                self.assertGreater(len(patch.read_text().splitlines()), 20,
                                   f"{ruling}: the staged patch is empty or truncated")

    def test_every_staged_ruling_is_still_actually_unimplemented(self):
        """THE HALF THAT CATCHES THE OPPOSITE MISTAKE. If someone implements one of these, the
        witness disappears from the source and this fails -- which is the prompt to move the
        entry to IMPLEMENTED rather than leave a record that describes a tree that has moved on.
        A record outliving the thing it describes is the #166 shape, and a ruling table is a
        particularly bad place for it."""
        for ruling, entry in STAGED.items():
            module, witness = entry["witness"]
            with self.subTest(ruling=ruling):
                source = _source(module)
                self.assertIn(
                    witness, source,
                    f"{ruling} appears to be IMPLEMENTED -- '{witness}' is gone from {module}. "
                    f"Move it out of STAGED in this file and record where the work landed.")

    def test_every_implemented_ruling_is_still_actually_implemented(self):
        """The mirror of the STAGED half, and the reason IMPLEMENTED carries a witness at all.
        A table that only ever gains rows is a changelog; this one has to keep being TRUE. A
        revert, a bad merge or a cherry-pick that drops the work fails here rather than leaving
        a record asserting the engine does something it no longer does."""
        for ruling, entry in IMPLEMENTED.items():
            module, witness = entry["witness"]
            with self.subTest(ruling=ruling):
                source = _source(module)
                self.assertIn(
                    witness, source,
                    f"{ruling} is recorded as IMPLEMENTED but '{witness}' is missing from "
                    f"{module} -- the work was reverted, or the record is wrong.")

    def test_no_ruling_is_in_both_tables(self):
        """The two witnesses are inverses, so an entry in both would make one of them a lie
        whichever way the tree sits."""
        self.assertEqual(set(STAGED) & set(IMPLEMENTED), set())

    def test_every_implemented_ruling_records_what_it_cost(self):
        """An implemented ruling with no cost recorded reads as free, and none of these were.
        6.1b moved a shipped constant; a reader who meets this table deserves that in the same
        breath as the word IMPLEMENTED."""
        for ruling, entry in IMPLEMENTED.items():
            with self.subTest(ruling=ruling):
                self.assertGreater(len(entry.get("cost", "")), 60,
                                   f"{ruling}: say what it cost, or say plainly that it was free")
                self.assertTrue((_HERE / entry["evidence"]).exists(),
                                f"{ruling}: evidence path does not exist")

    def test_every_staged_ruling_states_why_it_stopped(self):
        """'Staged' with no reason is indistinguishable from 'abandoned' six months later."""
        for ruling, entry in STAGED.items():
            with self.subTest(ruling=ruling):
                self.assertGreater(len(entry["why"]), 60,
                                   f"{ruling}: say what stopped it, in a sentence a stranger "
                                   f"can act on")

    def test_the_rulings_are_recorded_where_a_reader_would_look(self):
        """The decisions live in the contracts file and the measurements in the evidence file.
        Both are checked for existence because this pin is worth nothing if the trail it points
        at has moved."""
        contracts = (_HERE / "CDME_CONTRACTS.md").read_text()
        self.assertIn("Owner rulings", contracts)
        for ruling in STAGED:
            self.assertIn(ruling, contracts, f"{ruling} is not in CDME_CONTRACTS.md")
        self.assertTrue((_HERE / EVIDENCE).exists(), f"{EVIDENCE} is missing")

    #: The seven `#52` engine-design decisions, named once so the two tests below cannot
    #: disagree about the census (#126).
    SEVEN = ("6.1b", "I-06/J-06", "6.1d.1", "W1-07", "W4-01", "J-12", "J-13")

    def test_the_seven_rulings_are_all_named_in_the_contracts_file(self):
        contracts = (_HERE / "CDME_CONTRACTS.md").read_text()
        for ruling in self.SEVEN:
            with self.subTest(ruling=ruling):
                self.assertIn(ruling, contracts)

    def test_every_ruling_sits_in_EXACTLY_ONE_table_here(self):
        """THE HOLE THIS CLOSES, and it was a real one. The census above only asked whether a
        ruling is NAMED in the contracts file -- which every ruling is, by construction, since
        that file is where they were written down. So J-12 and J-13 were implemented in the
        tree, carried their ruling tag in the source, had their own guard tests, and appeared in
        NEITHER table here, while this file's docstring claimed "every owner ruling is either
        IMPLEMENTED or STAGED WITH ITS REASON. Nothing is just forgotten." The census passed
        throughout.

        A guard that asserts less than its docstring claims is worse than no guard, because the
        claim is what a reader trusts. This asserts the claim.
        """
        tables = {"STAGED": STAGED, "IMPLEMENTED": IMPLEMENTED,
                  "AWAITING_RULING": AWAITING_RULING}
        for ruling in self.SEVEN:
            with self.subTest(ruling=ruling):
                holders = [name for name, table in tables.items() if ruling in table]
                self.assertEqual(
                    len(holders), 1,
                    f"{ruling} is in {holders or 'NO table'} -- every ruling must sit in exactly "
                    f"one of {sorted(tables)}. Two tables means the record contradicts itself; "
                    f"none means nobody is tracking it, which is what this test exists to catch.")

    def test_no_table_carries_a_ruling_that_is_not_one_of_the_seven(self):
        """The mirror: a typo'd or invented key would otherwise satisfy the test above for the
        wrong ruling while leaving a real one untracked."""
        for name, table in (("STAGED", STAGED), ("IMPLEMENTED", IMPLEMENTED),
                            ("AWAITING_RULING", AWAITING_RULING)):
            for ruling in table:
                with self.subTest(table=name, ruling=ruling):
                    self.assertIn(ruling, self.SEVEN, f"{name} carries an unknown ruling key")

    def test_every_awaiting_ruling_is_still_actually_awaiting(self):
        """Same shape as the STAGED half: if someone resolves one of these, its witness leaves
        the source and this fires, prompting a move to IMPLEMENTED rather than a record that
        describes a tree which has moved on."""
        for ruling, entry in AWAITING_RULING.items():
            module, witness = entry["witness"]
            with self.subTest(ruling=ruling):
                source = _source(module)
                self.assertIn(
                    witness, source,
                    f"{ruling} appears to be RESOLVED -- '{witness}' is gone from {module}. "
                    f"Move it out of AWAITING_RULING and record where the work landed.")

    def test_every_awaiting_ruling_points_at_evidence_that_exists(self):
        for ruling, entry in AWAITING_RULING.items():
            with self.subTest(ruling=ruling):
                path = _HERE / entry["evidence"]
                self.assertTrue(path.exists(), f"{ruling}: evidence missing ({path})")
                self.assertGreater(len(path.read_text().splitlines()), 20,
                                   f"{ruling}: evidence file is a stub")


if __name__ == "__main__":
    unittest.main()
