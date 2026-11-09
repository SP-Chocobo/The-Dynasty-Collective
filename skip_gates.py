"""#303: every place the suite is ALLOWED to decline, registered so a new one cannot appear quietly.

WHAT #299 COST, AND WHY A LIST WOULD NOT HAVE PREVENTED IT. Fifteen board-executing tests skipped
for an unknown number of runs because a glob went stale. Nothing noticed, because a skip is not a
failure and `skipped=N` is the one number in the summary line that no instrument held. The suite
said `skipped=17` and meant two different things at once:

    15  MISSING INFRASTRUCTURE -- nothing about the subject changed; the harness could not reach
        it. This is silent coverage loss.
     2  A DATA CONDITION -- the real pool contains no instance of the case, so the test declines
        rather than fabricating a fixture that would make its own assertion vacuous. This is the
        absence contract (`#187`) applied to coverage, and it is correct behaviour.

Those are indistinguishable in the summary line, and `#299` left the general case open.

WHY THIS COUNTS GATES AND NOT SKIPS. The obvious instrument records the runtime skip count and
fails when it rises. Rejected: measuring it needs a full 28-minute run, so the recorded number
could only be refreshed at enormous cost, and it is environment-dependent by nature -- a developer
without a browser would see the ratchet fail for a reason that is not a code change. What IS
cheap, static and environment-independent is the set of PLACES a skip can happen. A gate is a
deliberate decision to allow declining; a new one should be argued for.

So this is `boundary_census`'s shape, not `assertion_floors`': growth is the regression, and the
fix for a legitimate new gate is to register it here WITH A REASON -- the same bargain that file
strikes ("the fix is either to route it through the engine or to register it with a reason").
That bargain is the point: it converts a skip gate from something that appears in a diff nobody
reads into something that cannot appear without a sentence explaining itself.

WHAT IT CANNOT SEE, stated because a check whose limits are unstated gets trusted past them:

  * Whether a registered gate FIRES. A gate that is always-true and a gate that is always-false
    look identical here. `#299`'s was always-false for an unknown period and this file would not
    have said so -- it would only have required that the gate be registered in the first place,
    which is a weaker and cheaper guarantee, honestly stated.
  * A skip raised from a helper rather than written at the test. `self.skipTest` inside a
    non-test method, or a decorator built at runtime, is not matched.
  * `unittest.expectedFailure`, which is a different mechanism with a different meaning.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import sys

import store_io
from assertion_floors import TEST_GLOB

GATES_PATH = pathlib.Path("SKIP_GATES.json")

#: The three spellings a skip can take. `skipTest` is the runtime form and the one `#299`'s AST
#: census missed, which is exactly how a decorator count got mistaken for a skip measurement.
GATE_CALLS = frozenset({"skipUnless", "skipIf", "skipTest"})


def gates_in(path: pathlib.Path) -> list[tuple[int, str]]:
    """(line, the gate's condition or reason as written) for one module, in line order."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", getattr(node.func, "id", ""))
        if name not in GATE_CALLS or not node.args:
            continue
        out.append((node.lineno, f"{name}({ast.unparse(node.args[0])[:90]})"))
    return sorted(out)


def scan(root: pathlib.Path = pathlib.Path(".")) -> dict[str, int]:
    """{module: how many skip gates it carries}. Modules with none are omitted."""
    found = {}
    for path in sorted(root.glob(TEST_GLOB)):
        n = len(gates_in(path))
        if n:
            found[path.name] = n
    return found


def load(path: pathlib.Path = GATES_PATH) -> dict[str, int]:
    """The registry, or {} when absent or damaged -- `--write` is how a broken one is repaired."""
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text())["modules"])
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return {}


def write(root: pathlib.Path = pathlib.Path("."), path: pathlib.Path = GATES_PATH) -> dict[str, int]:
    modules = scan(root)
    store_io.write(path, {
        "_comment": (
            "Registered skip GATES per test module -- see skip_gates.py. A gate is a place the "
            "suite is allowed to decline to prove something. GROWTH is the regression: a new "
            "gate must be registered here, in the same commit, with the reason in the commit "
            "message. Shrinkage is free. Regenerate with `python3 skip_gates.py --write`."
        ),
        "total": sum(modules.values()),
        "modules": modules,
    })
    return modules


def widened(root: pathlib.Path = pathlib.Path("."), path: pathlib.Path = GATES_PATH) -> list[str]:
    """Modules carrying MORE gates than registered, as readable lines. Shrinkage is not reported."""
    recorded, present = load(path), scan(root)
    out = []
    for module in sorted(present):
        was, now = recorded.get(module, 0), present[module]
        if now > was:
            out.append(f"{module}: {was} registered, {now} present")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="record the current gates")
    parser.add_argument("--check", action="store_true", help="exit non-zero if any module gained one")
    parser.add_argument("--list", action="store_true", help="print every gate with its condition")
    args = parser.parse_args(argv)

    if args.list:
        for path in sorted(pathlib.Path(".").glob(TEST_GLOB)):
            rows = gates_in(path)
            if rows:
                print(f"--- {path.name}")
                for ln, what in rows:
                    print(f"    :{ln}  {what}")
    if args.write:
        modules = write()
        print(f"wrote {GATES_PATH} -- {len(modules)} modules, {sum(modules.values())} skip gates")
    if args.check:
        recorded = load()
        if not recorded:
            print(f"{GATES_PATH} registers no gates (missing or damaged). This check is holding "
                  f"NOTHING, which is not the same as no gate having appeared. Run --write.")
            return 1
        grew = widened()
        if grew:
            print("A new place to decline appeared. If that is deliberate, say why in the commit "
                  "and rerun with --write so it lands in the diff:\n")
            for line in grew:
                print(f"  {line}")
            return 1
        present = scan()
        print(f"no module gained a skip gate ({sum(present.values())} registered across "
              f"{len(present)} modules)")
    if not (args.write or args.check or args.list):
        # NO FLAG RUNS THE CHECK. This branch used to `parser.print_help()` and return 0, which
        # at the call site is indistinguishable from a pass -- and that is exactly how "all 8
        # ratchets PASS" came to be published about a ratchet that had examined nothing. A
        # verification tool must have no zero-exit path that verifies nothing (`#352`).
        return main(["--check"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
