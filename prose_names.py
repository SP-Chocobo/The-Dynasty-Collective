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

SECOND CHECK: the VALUES quoted for constants. `#56` says a bound is derived, never calibrated,
and this repository explains most of its constants in prose sitting next to them. Change the
constant and the explanation beside it becomes a confident, specific lie. `misquoted_constants`
reads every module-level numeric constant and every place the prose writes `NAME = <number>` or
`NAME (<number>)`, and requires them to agree.

Only those two forms. A first attempt took the first number within forty characters of a named
constant and reported 76 disagreements, ALL of them false: prose legitimately names a constant
and then an item number, a measured value, or a table cell. An instrument at a 100% false
positive rate is worse than none. The tight form checks 73 real quotations and, as committed,
disagrees with the code nowhere. Scientific notation is part of the number: without the exponent
group, an ablation arm forcing a cap to 1e9 reads as "1" and reports as a contradiction.
"""

from __future__ import annotations

import ast
import functools
import io
import re
import subprocess
import tokenize
from pathlib import Path

#: Words with which this repository marks a statement as NOT A CLAIM ABOUT THE CURRENT CODE.
#: Two jobs, one vocabulary, because both checks ask the same question of a block of prose.
#:
#:   HISTORY  -- "This class was `X`", "renamed to `Y`", "it used to read", "NEVER WRITTEN".
#:               Naming what no longer exists is required by this repo's discipline of striking
#:               a claim in place rather than deleting it.
#:   PROBES   -- "the NEEDCAP arm sets `NEED_BONUS_MAX = 1e9`". An ablation states a value a
#:               constant is forced to for one experiment; it is not asserting what the constant
#:               IS. Two such arms are documented here and both would otherwise read as the
#:               prose contradicting the code.
#:
#: Derived from prose this repository actually writes, not from a general list of English
#: past-tense markers. A false fire costs one word here or one reworded sentence; a missed fire
#: is a document confidently stating a number the code stopped using, which is the whole point.
HISTORICAL_MARKERS = (
    "was ", "were ", "used to", "renamed", "previously", "no longer", "never written",
    "never existed", "has ever existed", "deleted", "removed", "withdrawn", "superseded",
    "replaced", "old version", "predates", "stale",
    "ablation", "arm", "probe", "experiment", "counterfactual",
)

#: THE ONLY TWO FORMS THAT UNAMBIGUOUSLY QUOTE A CONSTANT'S VALUE: `NAME = 12.0` and
#: `NAME (12.0)`, optionally backticked. Scientific notation is part of the number, not a
#: separate one -- without the exponent group, a cap forced to 1e9 in an ablation reads as "1",
#: and every such arm in this repository reports as a contradiction.
NUMBER = r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
QUOTED_VALUE = re.compile(
    rf"`?([A-Z][A-Z0-9_]{{3,}})`?[ \t]*(?:=|is)[ \t]*`?({NUMBER})`?"
    rf"|`?([A-Z][A-Z0-9_]{{3,}})`?[ \t]*\([ \t]*({NUMBER})[ \t]*\)")

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


#: THIS CHECKER'S OWN TEST MODULE IS NOT PART OF THE CORPUS.
#:
#: It exists to NAME things in order to prove they are absent -- `assertIn("SomeDeadName", dead)`
#: -- and a string literal in a tracked .py file is code, not prose, so it lands in the haystack
#: and the name it was quoting stops reading as dead. The guards passed while the file was
#: untracked and went red the moment it was committed.
#:
#: One file, one reason, and its absence fails loudly: remove this and the non-vacuity guards in
#: test_prose_names.py stop being able to plant a dead name at all. It is the same self-reference
#: doc_index hit when it classified its own output.
NOT_ITS_OWN_CORPUS = frozenset({"test_prose_names.py"})


@functools.lru_cache(maxsize=1)
def haystack() -> str:
    """Everything a name could legitimately live in -- with comments and docstrings STRIPPED
    from the Python, so a name that exists only in the prose describing it does not vouch for
    itself, and with this checker's own test module excluded (see NOT_ITS_OWN_CORPUS)."""
    parts = []
    for path in _tracked("*.py"):
        if path.name in NOT_ITS_OWN_CORPUS:
            continue
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


@functools.lru_cache(maxsize=1)
def numeric_constants() -> dict[str, float]:
    """Module-level numeric constants with exactly ONE definition across the repository.

    A name defined twice with different values is not a misquotation problem, it is a #126
    problem -- two homes for one fact -- and this check declines to guess which one the prose
    meant. Measured when this was written: 92 constants, 0 defined with conflicting values.
    """
    seen: dict[str, set[float]] = {}
    for path in _tracked("*.py"):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in tree.body:
            if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                continue
            name = node.targets[0].id
            value = node.value
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{3,}", name):
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)) \
                    and not isinstance(value.value, bool):
                seen.setdefault(name, set()).add(float(value.value))
    return {name: next(iter(vals)) for name, vals in seen.items() if len(vals) == 1}


def misquoted_constants() -> list[tuple[str, str, float, float]]:
    """(site, name, real, quoted) wherever prose states a constant's value and is wrong."""
    real = numeric_constants()
    out = []
    for path, line, text in prose_blocks():
        lowered = text.lower()
        if any(marker in lowered for marker in HISTORICAL_MARKERS):
            continue                       # a value quoted as history is not a claim about now
        for match in QUOTED_VALUE.finditer(text):
            name = match.group(1) or match.group(3)
            quoted = float(match.group(2) or match.group(4))
            if name in real and abs(real[name] - quoted) > 1e-12:
                at = line + (text[:match.start()].count("\n") if len(text.splitlines()) > 1 else 0)
                out.append((f"{path}:{at}", name, real[name], quoted))
    return out


def main() -> int:
    dead = dead_names()
    for name, sites in sorted(dead.items()):
        print(f"{name:44s} {', '.join(sites)}")
    print(f"{len(dead)} backticked name(s) in prose exist nowhere in this repository")
    wrong = misquoted_constants()
    for site, name, real, quoted in wrong:
        print(f"{site:52s} {name} is {real} but the prose says {quoted}")
    print(f"{len(wrong)} constant value(s) quoted wrongly, "
          f"over {len(numeric_constants())} single-homed constants")
    return 1 if (dead or wrong) else 0


if __name__ == "__main__":
    raise SystemExit(main())
