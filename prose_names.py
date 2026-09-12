"""Do this repository's own comments and docstrings name things that still exist?

`#182` is a standing order to audit the prose, and prose rots differently from code: a renamed
constant, a deleted class, a guard that was described but never written leave the source green
and the explanation wrong. Nothing in a test suite reads a docstring.

WHAT THIS CHECKS, and why that shape. Only `backticked_identifiers` in comments and docstrings,
and only against whether the name appears ANYWHERE in the repository -- code, data, JSON keys,
markdown. A backtick in this codebase means "this is a name in the system", so a backticked name
that exists nowhere is either a typo, a rename that did not reach its explanation, or a claim
about something that was never built. All three were found on the first run:

  `PANEL_ONLY`                             the constant is ADJUDICATION_PANEL_ONLY (typo)
  `ValidatedFlagIsUnconditional`           named as a characterization guard, NEVER WRITTEN
  `TheConstructionIsStrandedOnPurposeTests` correct -- its own sentence says the class WAS this

The third is why this is not a simple absence check. Renamed and withdrawn things are quoted
here deliberately and constantly; the repo's discipline is to strike a claim in place rather
than delete it, and that discipline REQUIRES naming what no longer exists.

SO THE RULE IS NOT "the name exists" BUT "the name exists, or the prose says it is history."
HISTORICAL_MARKERS is a hand-kept vocabulary, which `#126` is right to be suspicious of. It is
here anyway, because the alternative -- an allow-list of specific dead names -- goes stale
silently the moment one is resurrected, while a marker that stops matching simply starts
failing. Each marker earns its place by appearing in prose this repo actually writes.
"""

from __future__ import annotations

import ast
import functools
import io
import re
import subprocess
import tokenize
from pathlib import Path

#: Words with which this repository marks a name as no longer current. Derived from its own
#: correction style -- "This class was `X`", "renamed to `Y`", "it used to read", "NEVER WRITTEN"
#: -- not from a general list of English past-tense markers.
HISTORICAL_MARKERS = (
    "was ", "were ", "used to", "renamed", "previously", "no longer", "never written",
    "never existed", "has ever existed", "deleted", "removed", "withdrawn", "superseded",
    "replaced", "old version", "predates", "stale",
)

#: A backticked token this short is almost always a word, not a name.
MIN_NAME_LENGTH = 5

#: BOTH WALKS ARE CACHED FOR THE PROCESS. Uncached, the suite paid ~33s for this module
#: because every call re-tokenized every file. Nothing here mutates the tree, and a tool that
#: read it twice in one process would be reading a tree that could not have changed under it.
#:
#: Git object ids are quoted constantly and are not names in the system.
SHA = re.compile(r"^[0-9a-f]{7,40}$")


def _tracked(*globs: str) -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z", *globs],
                         capture_output=True, text=True, check=True)
    return [Path(name) for name in out.stdout.split("\0") if name]


@functools.lru_cache(maxsize=1)
def prose_blocks() -> tuple[tuple[Path, int, str], ...]:
    """Every comment and docstring in this repository's Python, as (path, line, text)."""
    blocks: list[tuple[Path, int, str]] = []
    for path in _tracked("*.py"):
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                if tok.type == tokenize.COMMENT:
                    blocks.append((path, tok.start[0], tok.string))
        except (tokenize.TokenError, IndentationError):
            pass
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                doc = ast.get_docstring(node)
                if doc:
                    blocks.append((path, getattr(node, "lineno", 1), doc))
    return tuple(blocks)


@functools.lru_cache(maxsize=1)
def haystack() -> str:
    """Everything a name could legitimately live in -- with comments and docstrings STRIPPED
    from the Python, so a name that exists only in the prose describing it does not vouch for
    itself."""
    parts = []
    for path in _tracked("*.py"):
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
        except (tokenize.TokenError, IndentationError):
            parts.append(source)
            continue
        for tok in toks:
            if tok.type == tokenize.COMMENT:
                continue
            if tok.type == tokenize.STRING and tok.line.strip().startswith(('"""', "'''")):
                continue
            parts.append(tok.string)
    for path in _tracked("*.js", "*.html", "*.json", "*.md", "*.css", "*.toml", "*.yml", "*.yaml"):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def words(universe: str) -> frozenset[str]:
    """Every word-shaped token in the corpus. A set membership test is exactly `\bname\b` for
    identifier-shaped names, and turns a per-name scan of a multi-megabyte string into a lookup
    -- the difference between this module costing the suite ~22s and ~2s."""
    return frozenset(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", universe))


def dead_names() -> dict[str, list[str]]:
    """Backticked names that exist nowhere and are not marked as history, as {name: [sites]}."""
    universe = words(haystack())
    found: dict[str, list[str]] = {}
    for path, line, text in prose_blocks():
        lowered = text.lower()
        for match in re.finditer(r"`([A-Za-z_][A-Za-z0-9_]*)`", text):
            name = match.group(1)
            if len(name) < MIN_NAME_LENGTH or SHA.match(name):
                continue
            if name in universe:
                continue
            if any(marker in lowered for marker in HISTORICAL_MARKERS):
                continue
            found.setdefault(name, []).append(f"{path}:{line}")
    return found


def main() -> int:
    dead = dead_names()
    for name, sites in sorted(dead.items()):
        print(f"{name:44s} {', '.join(sites)}")
    print(f"{len(dead)} backticked name(s) in prose exist nowhere in this repository")
    return 1 if dead else 0


if __name__ == "__main__":
    raise SystemExit(main())
