"""MANDATE 2.5 / `#187`: the snapshot boundary fabricated a measured zero out of an absent term.

`#187`'s rule is that `None` never becomes `0.0`. The board honours it: in upside mode
`compute_draft_board` OMITS `need_bonus` entirely, which is the honest way to say "this valuation has
no separated need term". `build_snapshot` then read it as `row.get("need_bonus", 0.0)` and every
consumer downstream saw a roster-fit measurement of zero.

The file stated the rule it was breaking, four lines below the line that broke it — the comment on
`time_horizon_adj` and `risk_adj` reads "Carried, never defaulted: upside mode genuinely does not
compute them and a 0.0 here would fabricate a measurement". And `pick_debate` had already found the
consequence and guarded it, saying so in `#183`'s note: "typed non-Optional and reach this via
`.get(key, 0.0)` … That is a contract violation rather than a live path, so it is guarded rather than
repaired upstream, and saying so is the point of this note." This is that upstream.

MEASURED on the committed capture, 12T_ppr_SF at 2.02 with 13 real picks on the board: all 48
candidates carried `need_bonus = 0.0` in upside mode before, and carry `None` after. In balanced mode
they carry real numbers (4.72 to 8.72), so the absence is mode-specific rather than everywhere.
"""
from __future__ import annotations

import unittest
from pathlib import Path

import draft_room as dr
import pick_synthesis as ps


class TheFieldIsTypedForAbsenceTests(unittest.TestCase):
    def test_need_bonus_is_optional_on_the_candidate(self):
        import typing
        hints = typing.get_type_hints(ps.CandidateSnapshot)
        self.assertEqual(typing.Optional[float], hints["need_bonus"],
                         "a non-Optional float here forces every consumer to read a fabricated zero")

    def test_no_call_anywhere_defaults_it_to_zero(self):
        """READ THE CODE, NOT THE TEXT OF IT (`#200`), and I needed the lesson twice: my first
        version grepped for the retired string and flagged the COMMENT that documents it, in the
        very repair that removed it. Parsed instead, so prose about the old shape is prose and a
        call is a call."""
        import ast
        offenders = []
        for name in ("pick_synthesis.py", "draft_strategy.py", "pick_debate.py"):
            for node in ast.walk(ast.parse(Path(name).read_text())):
                if not (isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "get"):
                    continue
                if len(node.args) != 2:
                    continue
                key, default = node.args
                if (isinstance(key, ast.Constant) and key.value == "need_bonus"
                        and isinstance(default, ast.Constant) and default.value == 0.0):
                    offenders.append(f"{name}:{node.lineno}")
        self.assertEqual([], offenders,
                         f"an absent need_bonus is being defaulted to a measured zero at {offenders}")

    def test_it_is_one_of_the_terms_whose_absence_the_identity_already_tolerates(self):
        """NON-VACUITY for the change: `team_acquisition_value == universal_value + terms` holds
        with an absent term contributing nothing, which is why typing it Optional does not break the
        contract every consumer reads."""
        self.assertIn("need_bonus", dr.TEAM_SPECIFIC_TERMS)


class NoConsumerTurnsTheAbsenceBackIntoAZeroTests(unittest.TestCase):
    def test_necessity_reads_it_without_a_default(self):
        """A `.get(key, 0.0)` here would put the fabrication back one layer down, where it would be
        harder to find: the score would be identical and its meaning would not."""
        source = Path("pick_synthesis.py").read_text()
        fn = source[source.index("def compute_pick_necessity("):]
        fn = fn[:fn.index("\ndef ")]
        self.assertIn('need_bonus = c.get("need_bonus")', fn)
        self.assertIn("if need_bonus is not None else 0.0", fn)

    def test_the_score_itself_does_not_move(self):
        """What changes is what the number MEANS, not the number. A missing term and a term worth
        0.0 add the same amount to a sum, so this repair is about the claim rather than the value --
        and pinning that keeps anyone from reading it as a scoring change."""
        rows = [{"player_id": "1", "name": "A", "position": "RB", "team_acquisition_value": 50.0,
                 "universal_value": 50.0, "bpa": 50.0, "confidence": 80.0}]
        absent = ps.compute_pick_necessity([dict(rows[0])], round_num=1)
        measured_zero = ps.compute_pick_necessity([dict(rows[0], need_bonus=0.0)], round_num=1)
        self.assertEqual(absent, measured_zero)

    def test_a_real_need_bonus_still_raises_the_score(self):
        """NON-VACUITY: if the term were being dropped rather than read, this would not move."""
        base = {"player_id": "1", "name": "A", "position": "RB", "team_acquisition_value": 50.0,
                "universal_value": 50.0, "bpa": 50.0, "confidence": 80.0}
        absent = ps.compute_pick_necessity([dict(base)], round_num=1)[0][0]
        with_fit = ps.compute_pick_necessity([dict(base, need_bonus=8.0)], round_num=1)[0][0]
        self.assertGreater(with_fit, absent)


class WhatThisItemDeliberatelyDidNotChangeTests(unittest.TestCase):
    """`rival_premium` reads 0.0 with basis `measured` on every candidate in upside mode, and the
    mandate lists that beside the `need_bonus` fabrication. It is NOT repaired here, because the code
    carries a reasoned rebuttal at the computation and I could not overturn it by measurement:

        "No mode guard: upside boards now carry universal_value too, and there it equals final_score
        exactly (upside_score reads nothing off the roster), so this subtraction is 0.0 for every
        player -- the true answer in that mode, not a missing one."

    `rival_premium` is a rival's own team-specific premium. In upside mode there are no team-specific
    terms, so the premium genuinely is zero under that valuation — a measured zero, not an absence.

    What remains arguable is narrower and is a semantics question, not an arithmetic one: a reader
    cannot tell "no rival gains anything" from "this valuation has no notion of a rival gaining
    anything". Changing it would mean giving `rival_premium` its own basis vocabulary instead of
    borrowing `denial_basis`, which is a decision about what the field claims. It belongs to the owner.

    Pinned so the reasoning is findable and so a later change has to answer it."""

    def test_the_rebuttal_is_still_in_the_code_where_a_reader_will_find_it(self):
        # assertTrue over a containment check rather than assertIn against the file: assertIn's
        # failure message prints the whole haystack, and the haystack here is a 4,000-line module.
        source = Path("draft_strategy.py").read_text()
        self.assertTrue("the true answer in that mode, not a" in source,
                        "draft_strategy no longer carries the reasoning this item defers to")

    def test_rival_premium_still_borrows_the_denial_basis(self):
        """The characterization: one companion serving two quantities that can be absent for
        different reasons. Invert when the owner rules on it."""
        source = Path("draft_strategy.py").read_text()
        self.assertTrue('"rival_premium_basis": denial_basis,' in source,
                        "rival_premium got its own basis -- the owner ruled; invert this test")


if __name__ == "__main__":
    unittest.main()
