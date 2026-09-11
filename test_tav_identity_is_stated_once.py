"""#182 + #126: the TAV identity is one fact with nine homes, and nothing noticed when it moved.

`team_acquisition_value`'s term list grew twice -- `depth_exposure` in #139, `displacement_adj`
in #216 -- and each time the authoritative statement was updated while the other statements of
the same fact were not. Two of them drifted into outright misstatement before #182's prose pass
caught them: `ARCHITECTURE_AUDIT.md` stated the three-term form while CITING the contract
section that by then said five, and `CDME_CONTRACTS.md` opened "CDME's central commitment is"
with the superseded arity in the present tense.

WHAT IS AND IS NOT A DEFECT HERE. A dated measurement or a landing record that states the arity
correct at ITS OWN time is legitimate and must stay -- rewriting history to match the present is
worse than leaving it, and `CDME_CONTRACTS` invariant 1 says so explicitly ("every earlier
measurement in this document that states the two- or three-term form was correct when taken and
is marked where it is load-bearing"). So the rule this file enforces is not "every statement
must list five terms". It is:

    every statement of the identity either matches the CODE's current term list,
    or carries a scope marker saying which moment it describes.

DERIVED FROM THE CODE (#126), NOT HAND-LISTED. The expected term set is parsed out of
`draft_room.py`'s own module docstring at runtime, so adding a sixth term to the identity makes
this test fail everywhere the docs still say five -- which is exactly the notification that was
missing both times the sum grew.
"""
from __future__ import annotations

import pathlib
import re
import unittest

REPO = pathlib.Path(__file__).resolve().parent

#: Phrases that scope a statement to a moment rather than asserting it of the present. Kept
#: short and explicit: a loose matcher here would let a genuine misstatement pass by accident,
#: which is the failure this file exists to prevent.
SCOPE_MARKERS = (
    "as it read", "at that time", "correct when taken", "when this was written",
    "this measurement was taken against", "as it stood", "at the time",
    "landed as ruled", "since grown", "has since",
)

IDENTITY_RE = re.compile(
    r"(?:team_acquisition_value|TAV)\s*={1,2}\s*`?universal_value(?P<terms>[^.\n]*(?:\n[^.\n#|]*)?)")


def _terms_in(blob: str) -> set[str]:
    """The named addends in an identity statement, `universal_value` included."""
    return {"universal_value"} | set(re.findall(r"\+\s*`?([a-z_]+)`?", blob))


def code_identity_terms() -> set[str]:
    """The live term list, read out of draft_room.py's own module docstring."""
    source = (REPO / "draft_room.py").read_text()
    match = IDENTITY_RE.search(source)
    assert match, "draft_room.py no longer states the identity in a form this test can read"
    return _terms_in(match.group("terms"))


def doc_statements() -> list[tuple[str, int, set[str], str]]:
    """(file, line number, terms stated, surrounding text) for every identity statement."""
    out = []
    for path in sorted(REPO.glob("*.md")):
        lines = path.read_text().splitlines()
        for i, line in enumerate(lines):
            match = IDENTITY_RE.search("\n".join(lines[i:i + 2]))
            if match and "universal_value" in line:
                # Whitespace-NORMALISED: these documents are hard-wrapped, so a scope
                # marker routinely straddles a line break ("**as\nit stood**"). Matching raw
                # text would miss it and report a correctly-marked historical statement as a
                # misstatement -- which this test did on its first run.
                window = " ".join(lines[max(0, i - 4):i + 6])
                context = re.sub(r"\s+", " ", window).lower()
                out.append((path.name, i + 1, _terms_in(match.group("terms")), context))
    return out


class EveryStatementOfTheIdentityMatchesTheCodeOrIsScoped(unittest.TestCase):

    def test_the_code_still_states_a_readable_identity(self):
        terms = code_identity_terms()
        self.assertIn("universal_value", terms)
        self.assertGreaterEqual(len(terms), 3, f"implausibly short term list: {terms}")

    def test_the_docs_state_the_identity_somewhere(self):
        """Non-vacuity: if the regex stops matching, every assertion below passes trivially."""
        found = doc_statements()
        self.assertGreaterEqual(len(found), 5,
                                f"expected the identity in several docs, found {len(found)}")

    def test_each_statement_matches_the_code_or_says_which_moment_it_describes(self):
        live = code_identity_terms()
        unscoped_mismatches = []
        for name, lineno, terms, context in doc_statements():
            if terms == live:
                continue
            if any(marker in context for marker in SCOPE_MARKERS):
                continue
            unscoped_mismatches.append(
                f"{name}:{lineno} states {sorted(terms)}, code says {sorted(live)}")
        self.assertEqual(
            unscoped_mismatches, [],
            "these state the TAV identity with a term list that is neither the code's current "
            "one nor scoped to a moment. Either update them, or -- if they are describing a "
            "past measurement correctly -- add a scope marker saying so:\n  "
            + "\n  ".join(unscoped_mismatches))


if __name__ == "__main__":
    unittest.main()
