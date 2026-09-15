"""#216 B4 / #70 -- board rank is not pick order, and a test says so.

`ordinals.py` names three registers that are all small positive integers and all print alike.
This file does two jobs that prose cannot: it holds the registry to the CODEBASE (a carrier it
claims must really exist; a register must really be consumed), and it holds a real producer to
its DECLARED DOMAIN, so a shape change fails here rather than being read as a different quantity
three call sites away.

WHAT IT DOES NOT DO, stated so nobody reads more into a green run. It cannot prove that no site
passes a VALUATION_RANK where a DRAFT_POSITION belongs -- Python has no such guarantee to offer,
and `#70` found those eleven crossings by reading, not by testing. This narrows the blast radius
of the next one; it does not abolish it.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import draft_strategy as ds
import ordinals


SELF = Path(__file__).name


def repo_python() -> list[Path]:
    """This repository's own Python, asked of git rather than walked -- caches and worktree
    checkouts are not this repo. Same rule `doc_index` and `test_superseded_proposals` use."""
    out = subprocess.run(["git", "ls-files", "-z", "*.py"],
                         capture_output=True, text=True, check=True)
    return [Path(n) for n in out.stdout.split("\0") if n and Path(n).name != SELF]


class TheRegistryDescribesThisCodebase(unittest.TestCase):
    def test_every_claimed_carrier_really_appears_in_the_code(self):
        """A registry naming fields nobody writes is documentation of an imagined system."""
        blob = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                         for p in repo_python() if p.name != "ordinals.py")
        for carrier, register in ordinals.carriers().items():
            self.assertIn(carrier, blob,
                          f"ordinals.py claims {carrier!r} carries {register}, but no module "
                          f"outside ordinals.py mentions it -- drop it or fix the name")

    def test_the_inverse_map_is_derived_not_restated(self):
        """#126: one home for a vocabulary. `carriers()` must be reproducible from ORDINALS
        alone, so a carrier added in one place cannot go missing in the other."""
        rebuilt = {c: name for name, spec in ordinals.ORDINALS.items() for c in spec["carriers"]}
        self.assertEqual(ordinals.carriers(), rebuilt)

    def test_no_carrier_is_claimed_by_two_registers(self):
        """The whole point is that these are DISTINCT. A name in two registers means the
        distinction failed at the registry itself."""
        seen: dict[str, str] = {}
        for name, spec in ordinals.ORDINALS.items():
            for c in spec["carriers"]:
                self.assertNotIn(c, seen,
                                 f"{c!r} claimed by both {seen.get(c)} and {name}")
                seen[c] = name

    def test_an_unknown_name_gets_None_rather_than_a_guess(self):
        """Substituting a plausible register for an unrecognised name is precisely the defect
        class this module exists to prevent, so the lookup must decline."""
        self.assertIsNone(ordinals.register_of("universal_value"))
        self.assertIsNone(ordinals.register_of(""))


class DomainsAreCheckedNotAssumed(unittest.TestCase):
    def test_zero_and_negative_are_violations_in_every_register(self):
        for register in ordinals.ORDINALS:
            self.assertEqual(ordinals.domain_violations(register, [0, -1]), [0, -1], register)

    def test_absence_is_not_a_domain_violation(self):
        """None means "not measured" and is legal everywhere -- the absence contract outranks
        the domain check. A register that rejected None would push callers toward substituting
        a 0, which is the defect the contract exists to stop."""
        for register in ordinals.ORDINALS:
            self.assertEqual(ordinals.domain_violations(register, [None, 1, 2]), [], register)

    def test_a_bool_is_not_an_ordinal(self):
        """True == 1 in Python, so a bool passes a naive `>= 1` check and reads as rank one."""
        self.assertEqual(ordinals.domain_violations("VALUATION_RANK", [True]), [True])

    def test_no_upper_bound_is_invented(self):
        """Each register's ceiling is a different runtime fact. A shared one would be a
        constant chosen rather than derived (#56)."""
        huge = [10 ** 6]
        for register in ordinals.ORDINALS:
            self.assertEqual(ordinals.domain_violations(register, huge), [], register)


class ARealProducerMatchesItsDeclaredDomain(unittest.TestCase):
    """The registry is only worth something if a real emitter is held to it. `rank_by_id` is
    built by `_build_opponent_boards` and is the carrier every take-probability read goes
    through, so it is the one to pin."""

    def _board(self, priced: int) -> dict:
        rows = [{"player_id": str(i), "final_score": float(100 - i), "position": "RB"}
                for i in range(priced)]
        return {"by_id": {r["player_id"]: r for r in rows},
                "rank_by_id": {r["player_id"]: i + 1 for i, r in enumerate(rows)},
                "unpriced_ids": set()}

    def test_rank_by_id_is_one_based_and_contiguous(self):
        ranks = sorted(self._board(25)["rank_by_id"].values())
        self.assertEqual(ranks, list(range(1, 26)))
        self.assertEqual(ordinals.domain_violations("VALUATION_RANK", ranks), [])

    def test_the_take_table_is_read_with_a_VALUATION_RANK_and_nothing_else(self):
        """`RANK_TAKE_PROBABILITY`'s keys mean "the best available, the second best, ...". Feeding
        it a DRAFT_POSITION would be silently accepted and silently wrong -- pick 3 of a draft is
        not the third-best player. The registry cannot stop that; what it can do is record that
        the table's domain IS this register, so the next reader knows which integer to hand it."""
        self.assertEqual(ordinals.register_of("rank_by_id"), "VALUATION_RANK")
        self.assertIn("RANK_TAKE_PROBABILITY",
                      ordinals.ORDINALS["VALUATION_RANK"]["consumers"])
        self.assertEqual(sorted(ds.RANK_TAKE_PROBABILITY), [1, 2, 3, 4, 5])
        self.assertEqual(ordinals.domain_violations(
            "VALUATION_RANK", list(ds.RANK_TAKE_PROBABILITY)), [])

    def test_draft_position_and_valuation_rank_are_different_registers(self):
        """The sentence B4 is named for, as an assertion."""
        self.assertEqual(ordinals.register_of("pick_no"), "DRAFT_POSITION")
        self.assertNotEqual(ordinals.register_of("pick_no"),
                            ordinals.register_of("rank_by_id"))


if __name__ == "__main__":
    unittest.main()
