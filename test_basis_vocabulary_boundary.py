"""#122/#110: a basis state that gates behaviour must be referenced by NAME, never by literal.

WHAT WAS DEMONSTRATED, at full-suite strength. Renaming `draft_room.APPETITE_IMPUTED` from
"imputed" to anything else passed the ENTIRE 2209-test suite. Three independent copies of that
string existed -- the producer's constant, a bare literal in draft_board_ui's comparison, and
the tests' own fixture value -- with nothing linking them, so the consumer and the tests agreed
with each other while the producer drifted away from both. The Draft Room's disclosure sentence
("That floor is an estimate: this position's remaining pool is too thin to measure its own depth
decay") silently stopped rendering, and the board went on asserting an ASSUMED horizon floor
with exactly the confidence of a measured one. That sentence exists to prevent precisely that.

WHY IT SURVIVED WHEN ITS SIBLING DID NOT. The same mutation applied to lineup_optimizer's
"measured" was caught by two tests immediately. The difference is what the state gates: depth's
basis gates a NUMBER (depth_exposure into team_acquisition_value), so value regressions catch
any drift; horizon's basis gates only PROSE, and nothing regresses prose against its producer.
A codebase that tests its arithmetic hard and its disclosures loosely will lose disclosures
first, and lose them quietly.

THE ASYMMETRY THIS CLOSES, which turned out to be structural rather than a one-off. Across
three basis vocabularies, every state meaning "no information" had been given a constant --
EXPOSURE_NO_SURPLUS, EXPOSURE_VACANT, EXPOSURE_NOT_APPLICABLE, BYE_PARTIAL, BYE_UNKNOWN,
APPETITE_IMPUTED, APPETITE_UNAVAILABLE -- while the state meaning "this is real evidence" was
left as a bare literal in two of the three. That is backwards: the named states cannot be
mistyped at a call site without raising NameError, and the unnamed one, which is the one that
actually gates behaviour, could drift in silence.

WHAT THIS SCANS, and what it deliberately does not. AST, never text: a docstring that spells a
state in quotes is prose describing the vocabulary and is not a use of it, and a regex over
source could not tell those apart. Only real comparisons and real dict values are offences.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve().parent

#: Test modules are exempt: a test may legitimately construct an out-of-vocabulary value to
#: prove a consumer rejects it. Production code has no such reason.
_PRODUCTION = sorted(
    p for p in _HERE.glob("*.py")
    if not p.name.startswith("test_") and p.name != Path(__file__).name
)


def _mentions_basis(node: ast.AST) -> bool:
    """True for an expression whose name is about a basis -- `horizon_basis`, `c.depth_basis`,
    `depth["basis"]`. Name-shaped rather than type-shaped, because the vocabulary is a naming
    convention and that is exactly what a new site would follow."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and "basis" in sub.id:
            return True
        if isinstance(sub, ast.Attribute) and "basis" in sub.attr:
            return True
        if isinstance(sub, ast.Constant) and sub.value == "basis":
            return True
    return False


def _string_literals(node: ast.AST) -> list[str]:
    """The string constants an expression can evaluate to -- following a conditional into both
    of its arms, because `X if flag else "measured"` is exactly the shape both offences took."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, ast.IfExp):
        return _string_literals(node.body) + _string_literals(node.orelse)
    return []


def offences(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        return []
    found: list[str] = []
    for node in ast.walk(tree):
        # `some_basis == "measured"`
        if isinstance(node, ast.Compare) and _mentions_basis(node.left):
            for comparator in node.comparators:
                for literal in _string_literals(comparator):
                    found.append(f"{path.name}:{node.lineno} compares a basis to {literal!r}")
        # `{"basis": "measured"}` / `{"basis": X if f else "measured"}`
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Constant) and key.value == "basis":
                    for literal in _string_literals(value):
                        found.append(f"{path.name}:{node.lineno} stores basis as {literal!r}")
    return found


class ABasisStateIsReferencedByNameNotByLiteralTests(unittest.TestCase):

    def test_no_production_module_compares_or_stores_a_basis_as_a_bare_literal(self):
        found = [line for path in _PRODUCTION for line in offences(path)]
        self.assertEqual(
            found, [],
            "a basis state written as a literal drifts silently when its constant is renamed -- "
            "import the constant from the module that defines the vocabulary",
        )

    def test_the_scanner_actually_catches_both_offence_shapes(self):
        """Non-vacuity, and the reason it is written against synthetic source rather than by
        mutating the repository: a scanner that silently matched nothing would pass the test
        above forever, and the two shapes below are verbatim the two that were really found."""
        import tempfile
        for source, why in (
            ('if depth_basis == "measured":\n    pass\n', "the draft_room comparison"),
            ('d = {"basis": "measured" if flag else NO_SURPLUS}\n', "the lineup_optimizer store"),
            ('d = {"basis": PARTIAL if unknown else "measured"}\n', "the bye-week store"),
            ('if c.horizon_basis == "imputed":\n    pass\n', "the draft_board_ui comparison"),
        ):
            with self.subTest(shape=why):
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
                    fh.write(source)
                self.assertTrue(offences(Path(fh.name)), f"scanner missed {why}")

    def test_the_scanner_does_not_fire_on_prose_or_on_a_named_constant(self):
        """The other half of non-vacuity: a scanner that flagged everything would also pass the
        shapes test while making the guard unusable, and docstrings legitimately spell these
        states out when describing the vocabulary."""
        import tempfile
        for source, why in (
            ('"""basis -- "measured", or NO_SURPLUS."""\nx = 1\n', "a docstring naming the states"),
            ('if depth_basis == lo.EXPOSURE_MEASURED:\n    pass\n', "a comparison via the constant"),
            ('d = {"basis": MEASURED if flag else NO_SURPLUS}\n', "a store via the constants"),
            ('if name == "measured":\n    pass\n', "an unrelated variable"),
        ):
            with self.subTest(shape=why):
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
                    fh.write(source)
                self.assertEqual(offences(Path(fh.name)), [], f"scanner false-fired on {why}")

    def test_the_re_exported_vocabulary_is_BOUND_to_its_definer_not_copied(self):
        """pick_synthesis re-exports the horizon-basis vocabulary so a snapshot consumer has a
        legal way to name these values -- consumers may not import from draft_room at all (that
        boundary is pinned separately, and this pass tripped it). A re-export written as
        `HORIZON_BASIS_IMPUTED = "imputed"` would satisfy every other test here while quietly
        restoring the exact defect: two definitions of one value, drifting apart on the next
        rename. Found by mutating the binding into a copy and watching everything stay green.

        The RHS must be an attribute of the defining module. Checked in source rather than by
        comparing values, because equal strings prove nothing -- a copy and a binding compare
        equal right up until the moment one of them changes."""
        tree = ast.parse((_HERE / "pick_synthesis.py").read_text())
        checked = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not (isinstance(target, ast.Name) and target.id.startswith("HORIZON_BASIS_")):
                    continue
                checked += 1
                self.assertIsInstance(
                    node.value, ast.Attribute,
                    f"{target.id} is assigned a literal; bind it to the module that defines the "
                    "vocabulary so a rename there cannot leave this copy behind",
                )
        self.assertGreaterEqual(checked, 3, "the re-exported vocabulary went missing entirely")

    def test_it_is_scanning_a_real_and_non_trivial_set_of_modules(self):
        """A glob that silently matched nothing would make every assertion above vacuous."""
        names = {p.name for p in _PRODUCTION}
        self.assertGreater(len(_PRODUCTION), 20)
        for expected in ("draft_room.py", "lineup_optimizer.py", "draft_board_ui.py"):
            self.assertIn(expected, names)


if __name__ == "__main__":
    unittest.main()
