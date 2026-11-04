"""#298 / §19.8: a guarantee that could not RUN, caught -- not one that got quieter.

WHAT THE SUITE COULD ALREADY SEE, AND WHAT IT COULD NOT. `assertion_floors` catches a
guarantee that got weaker, and `test_suite_taxonomy` catches one that left its tier. Both
read SOURCE -- `assertion_floors.scan` is `ast.parse` over `root.glob(TEST_GLOB)` and never
imports anything. So both are blind, by construction, to a test module that is present,
unweakened, correctly tiered, and **cannot be imported at all**. The same shape as
`ui_explore/round2/fableA/_domdiff.py` hashing markup and therefore being blind to CSS: not a
bug in either instrument, a boundary that has to be named or it gets trusted past.

THE MEASUREMENT THAT MOTIVATED THIS (2026-11-04, this container, 238 root test modules):

    interpreter                          collected   modules that fail to import
    /usr/local/bin/python3  3.11.17          1,059         180 of 238
    /usr/bin/python3        3.13.17          4,235           0 of 238

`python3` resolves to the FIRST of those on PATH. It carries 1 of the 11 distributions
`requirements.txt` declares; the second carries 9. Every certified suite figure in this
repository -- including the 4,235/1,276.5s budget `close-register-item` keeps -- was measured
on the second. The first cannot import `pandas`.

WHY THE OUTPUT OF THE BROKEN RUN DOES NOT LOOK BROKEN, which is the whole reason this file
exists. A test module whose import dies does not vanish from the report; `unittest` replaces
it with a single synthetic `unittest.loader._FailedTest`. So 180 dead modules read as:

    Ran 1059 tests ... FAILED (errors=180)

`failures=0`. A reader who greps `^FAIL:` -- as the close procedure's own transcript does --
finds nothing, and 3,176 test cases that never ran are reported as 180 lines of a different
word. This is the #201 family exactly: not a crash, a plausible number about something else.

AND THE RATCHETS AGREE WITH IT. Measured on 3.11.17 at the same tree:

    $ python3 assertion_floors.py --check
    no guarantee has shrunk (238 modules held to a floor)
    exit=0

238 modules held to a floor, 180 of them unreachable, exit 0. The floors are not wrong -- they
are answering a question about the source tree, and reachability is a different question. This
file asks the different question.

WHAT IT CHECKS, AND WHY THERE IS NO NUMBER TO MAINTAIN. Every module in
`assertion_floors.TEST_GLOB`'s population must be importable, with zero tolerance. The
expectation is DERIVED from the tree rather than recorded beside it, so there is no floor file
to regenerate, nothing to go stale, and no second source of truth for the population (#126 --
the glob itself is imported from `assertion_floors`, not restated here). A new test module
raises the population and asks nothing of anybody; a module that stops importing fails.

The collected-case count is REPORTED and never asserted on. It is the figure a reader wants
("4,235, the number the budget was measured at"), and it is also the figure that legitimately
moves every time anyone writes a test, so holding it to a floor would be the reflexive-repair
trap `assertion_floors`' own docstring rejects.

WHAT IT CANNOT SEE, stated because a check whose limits are unstated gets trusted past them:

  * A module that imports and then SKIPS everything. `requirements.txt` already carries this
    warning for `playwright`: without it 14 board-execution tests skip with an honest message
    that is still easy to miss, and a reclaimed container ran the suite 14 tests lighter and
    reported OK. Importability does not catch that; nothing here claims to.
  * A dependency that is present at a version the code cannot use.
  * IMPORT ORDER. This imports the population in sorted order in ONE process. A module that
    only imports because an earlier one put something in `sys.modules` passes here and can
    still fail under `unittest`'s own discovery order.
  * Anything about the modules a test module imports at CALL time rather than module scope.

WHY IT IS A TEST AND NOT ONLY A PREFLIGHT. Both are offered, and the test is the one that
matters: a preflight is a step in a procedure, and the one process failure this repository has
actually recorded was a procedure step getting skipped (`close-register-item`, step 4). This
module imports nothing but the standard library and `assertion_floors`, neither of which needs
a declared requirement -- so it survives, and fails loudly, under precisely the interpreter it
exists to detect. A check that dies with the thing it is checking is not a check.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from assertion_floors import TEST_GLOB


def population(root: Path = Path(".")) -> list[str]:
    """The module names this suite is made of -- the same population the floors hold.

    Derived from `assertion_floors.TEST_GLOB` rather than a second glob of its own, so the two
    instruments cannot disagree about what the suite is (#126).
    """
    return sorted(p.stem for p in root.glob(TEST_GLOB))


def unreachable(root: Path = Path(".")) -> dict[str, str]:
    """{module name: one-line reason} for every test module this interpreter cannot import.

    An already-imported module is re-reported as reachable without re-executing it, which is
    what makes this cheap inside the full suite: `importlib.import_module` returns the cached
    module. A FAILED import is never cached, so a dead module is re-attempted and caught even
    when discovery has already tried it.

    `root` is put on `sys.path` for the duration, and taken off again. The first draft did not
    do that, and it was wrong in the way this repository keeps finding: `population(root)`
    globbed `root` while `import_module` resolved against `sys.path`, so every `root` except
    `.` silently answered about a DIFFERENT population than the one it had just listed -- a
    parameter half-honoured is worse than one not offered, because the caller is told it was
    read. Caught by writing the test that passes a temporary directory.

    Anything raised at import is caught, not just `Exception`. A test module is ordinary
    module-scope code: `SystemExit` from a mis-run argparse, and an interrupt from a blocking
    read, are both things it can raise, and either one escaping here would take down the check
    that exists to report it. (The interrupt is deliberately not named in backticks: it is a
    builtin, and `test_prose_names` holds backticked names to things that exist in THIS
    repository. It caught the first draft of this very sentence.)
    """
    out: dict[str, str] = {}
    here = str(root.resolve())
    sys.path.insert(0, here)
    try:
        for name in population(root):
            try:
                importlib.import_module(name)
            except BaseException as exc:  # module-scope code can raise anything
                out[name] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            sys.path.remove(here)
        except ValueError:  # something else removed it; not this function's business
            pass
    return out


def collected(root: Path = Path(".")) -> int:
    """How many test cases this interpreter actually collects, counting a dead module as 0.

    Reported, never asserted on -- see the module docstring on why this is not a floor.
    """
    import unittest

    def walk(suite):
        for item in suite:
            if isinstance(item, unittest.TestSuite):
                yield from walk(item)
            else:
                yield item

    found = unittest.TestLoader().discover(str(root), pattern=TEST_GLOB, top_level_dir=str(root))
    return sum(1 for t in walk(found) if type(t).__module__ != "unittest.loader")


def interpreter() -> str:
    """The thing a failure here is almost always actually about."""
    return f"{sys.executable} ({sys.version.split()[0]})"


def report(dead: dict[str, str], root: Path = Path("."), *, count_cases: bool = True) -> str:
    """Rendered from a dead-module mapping the CALLER measured, never re-measured here.

    Two calls to `unreachable` in one run could disagree -- an import that failed the first
    time can succeed the second once a sibling has populated `sys.modules` -- and a report
    that disagrees with the exit code it accompanies is worse than either alone.
    """
    total = len(population(root))
    lines = [f"interpreter: {interpreter()}", f"test modules: {total}"]
    if count_cases:
        lines.append(f"collected test cases: {collected(root)}")
    if not dead:
        lines.append(f"every one of the {total} test modules imports")
        return "\n".join(lines)
    lines.append(f"{len(dead)} of {total} test modules CANNOT BE IMPORTED -- every test in "
                 f"each of them is reported as one 'error' and does not run:")
    lines += [f"    {name}: {why}" for name, why in sorted(dead.items())]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero when any test module cannot be imported")
    parser.add_argument("--no-count", action="store_true",
                        help="skip the collected-case count, which costs a full discovery")
    args = parser.parse_args(argv)
    dead = unreachable()
    print(report(dead, count_cases=not args.no_count))
    return 1 if (args.check and dead) else 0


if __name__ == "__main__":
    raise SystemExit(main())
