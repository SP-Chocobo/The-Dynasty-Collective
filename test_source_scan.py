"""#200: a module's CODE, with its prose removed -- because mentioning a name is not calling it.

WHY THIS EXISTS. Two guards in this suite assert that a quantity has no production reader:
`snapshot_is_current` (#92/#101, a certifier deliberately built and deliberately not wired) and
`baseline_provenance` (§7.10, a record that is documentation and must never become an input).
Both proved that claim the cheap way -- search the raw file text for the name and fail if it
appears at all.

That is a strictly stronger claim than the one they mean, and on 2026-09-07 the difference went
red. `sleeper_import_report.py` does not call either of them; its docstring EXPLAINS, in prose,
that the input layer already has machinery for freshness and names the two as examples. A
comment about a rule became indistinguishable from a violation of it, and the suite gained two
permanent failures that no repair could clear -- the corrosive kind, because a suite with
standing red teaches everyone to skim past red.

WHAT IS AND IS NOT REMOVED, and the line matters. Comments and docstrings go. Ordinary string
literals STAY, deliberately: `baseline_provenance` is the stem of a FILENAME, so a real reader
of it looks like `open(BASE / "baseline_provenance.json")` -- a string literal in executing
code. Dropping every string would have made the guard unable to see the one shape it most needs
to catch, which is how a fix for a false alarm turns into a false negative.

Character-exact, not line-exact. A one-line `def f(): "doc"` puts code and docstring on the same
line, so prose is blanked by its own column range and the code around it survives. Blanking is
by SPACE, never by deletion, so every line and column number in the result still matches the
file on disk and a caller can report a real position.
"""
from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path
from typing import Union


def _offsets(source: str) -> list[int]:
    """Absolute offset at which each 1-indexed line starts."""
    starts = [0, 0]
    for line in source.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    return starts


def _blank(chars: list[str], starts: list[int], span) -> None:
    lo_line, lo_col, hi_line, hi_col = span
    if lo_line >= len(starts) or hi_line >= len(starts):
        return
    lo, hi = starts[lo_line] + lo_col, starts[hi_line] + hi_col
    for i in range(max(0, lo), min(len(chars), hi)):
        if chars[i] != "\n":
            chars[i] = " "


def _docstring_spans(source: str) -> list[tuple[int, int, int, int]]:
    spans = []
    for node in ast.walk(ast.parse(source)):
        body = getattr(node, "body", None)
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            spans.append((first.lineno, first.col_offset,
                          first.end_lineno, first.end_col_offset))
    return spans


def code_text(source: Union[str, Path]) -> str:
    """`source` (a path or the text itself) with comments and docstrings blanked out.

    Returns the text unchanged if it cannot be parsed -- a syntax error is not this function's
    to report, and a guard that silently saw an EMPTY file would pass vacuously. Failing toward
    the raw text keeps the guard at least as strong as it was before this module existed.
    """
    text = source.read_text() if isinstance(source, Path) else source
    try:
        spans = _docstring_spans(text)
    except SyntaxError:
        return text
    chars = list(text)
    starts = _offsets(text)
    for span in spans:
        _blank(chars, starts, span)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                _blank(chars, starts, (tok.start[0], tok.start[1], tok.end[0], tok.end[1]))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    return "".join(chars)


# ---------------------------------------------------------------------------------------------
import unittest


class ProseIsNotCodeTests(unittest.TestCase):
    """The distinction this module exists to draw, in both directions."""

    def test_a_module_docstring_mentioning_a_name_does_not_count_as_using_it(self):
        self.assertNotIn("snapshot_is_current",
                         code_text('"""we do not call snapshot_is_current here"""\nx = 1\n'))

    def test_a_comment_mentioning_a_name_does_not_count_either(self):
        self.assertNotIn("snapshot_is_current", code_text("x = 1  # snapshot_is_current\n"))

    def test_a_function_and_class_docstring_go_too(self):
        src = ('class C:\n    """doc snapshot_is_current"""\n'
               '    def m(self):\n        """doc baseline_provenance"""\n        return 1\n')
        out = code_text(src)
        self.assertNotIn("snapshot_is_current", out)
        self.assertNotIn("baseline_provenance", out)
        self.assertIn("def m(self):", out)

    def test_an_ordinary_string_literal_SURVIVES_which_is_the_whole_point(self):
        """The guard that motivated this reads a FILENAME, so its real violation is a string
        literal in executing code. A fix for a false alarm that blinded the guard to its own
        target would be strictly worse than the alarm."""
        self.assertIn("baseline_provenance",
                      code_text('p = open("data/baseline/baseline_provenance.json")\n'))

    def test_a_bare_string_expression_that_is_not_a_docstring_survives(self):
        # Only the FIRST statement of a module, class or function is a docstring. A string
        # sitting anywhere else is an expression that evaluates, so it stays.
        self.assertIn("snapshot_is_current", code_text('y = 1\n"snapshot_is_current"\n'))

    def test_code_sharing_a_line_with_its_docstring_survives(self):
        out = code_text('def f(): "snapshot_is_current"\n')
        self.assertIn("def f():", out)
        self.assertNotIn("snapshot_is_current", out)

    def test_line_and_column_positions_are_preserved(self):
        # Blanking, never deleting: a caller reporting `path:line` must report a real line.
        src = '"""doc"""\nimport os\nx = 1  # tail\n'
        out = code_text(src)
        self.assertEqual(len(out), len(src))
        self.assertEqual(out.splitlines()[1], "import os")

    def test_an_unparseable_file_falls_back_to_the_raw_text(self):
        """Failing toward the RAW text keeps the guard at least as strong as it was. Failing
        toward empty would make every guard using this pass vacuously."""
        broken = "def (:\n"
        self.assertEqual(code_text(broken), broken)

    def test_it_reads_a_path_as_well_as_a_string(self):
        from pathlib import Path
        self.assertIn("def code_text", code_text(Path(__file__)))


if __name__ == "__main__":
    unittest.main()
