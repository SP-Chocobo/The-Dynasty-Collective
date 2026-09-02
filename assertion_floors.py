"""#113 / §19.8: a guarantee that got quieter, caught -- not just one that got deleted.

WHAT THE SUITE COULD ALREADY SEE, AND WHAT IT COULD NOT. Deleting a test is loud: the count
drops, `test_suite_taxonomy` notices a module leaving a tier, and a reviewer reading the diff
sees a removed block. **Weakening** one is silent. These two files pass the same checks:

    self.assertEqual(board.iloc[0]["universal_value"], 41.0)     # before
    self.assertIsNotNone(board.iloc[0]["universal_value"])       # after

Same module, same test method, same green run, same test count -- and the second one no longer
holds the engine to a number. This repository's own history is the argument for taking that
seriously: the mutation pass (#38, #41) found tests that could not fail, and every one of them
had been green for months. A test does not have to be removed to stop proving anything.

WHAT THIS RECORDS, AND WHY IT IS A FLOOR RATHER THAN A FINGERPRINT.

The obvious design is a hash over each module's assertions, checked for equality. It was
rejected: an exact fingerprint fails on *every* test edit, including adding a test, so the
regeneration command gets run reflexively -- and a check whose repair is reflexive is not a
check. What is recorded here instead is, per test module:

    test_methods          how many test methods it defines
    asserts               {assertEqual: 41, assertIn: 12, ...} -- counted PER NAME

and `--check` fails only when one of those numbers goes DOWN.

WHY PER-NAME COUNTS, WHICH IS THE PART THAT DOES THE REAL WORK. A single total would miss the
substitution above entirely: assertEqual -> assertIsNotNone leaves the total unchanged. Counting
each assertion method separately means assertEqual dropping 41 -> 40 fails even while
assertIsNotNone rises 3 -> 4.

WHAT THAT COSTS, STATED HONESTLY, because the first draft of this docstring got it wrong and its
own test caught it. Per-name counting has no opinion about which assertions are stronger -- that
ordering would be invented, and wrong for some real pair -- so it cannot tell a weakening from a
STRENGTHENING. Replacing `assertIsNotNone` with `assertEqual` also drops a per-name count, and
also fails. Precisely:

    pure additions          -- a new test, a new assertion, a whole new module   PASS, always
    any substitution        -- one assertion name swapped for another            FAILS, either way

That is not the check being noisy. A substitution is the one edit where a reviewer genuinely has
to look, and the failure output names both sides of it (`assertIsNotNone 1 -> 0` beside
`assertEqual 2 -> 3` in the regenerated diff), which is enough to read the direction in a glance.
The common case -- adding coverage -- never asks for anything. What is bought for that price is
that a weakening cannot pass unseen, and that is the whole point.

WHAT IT CANNOT SEE, stated because a check whose limits are unstated gets trusted past them:

  * a vacuous assertion (`assertEqual(x, x)`) -- the count is identical, and #38's mutation pass
    remains the only instrument that finds those;
  * an assertion moved behind a condition that never holds;
  * a weakened EXPECTED VALUE (`assertEqual(v, 41.0)` -> `assertEqual(v, 0.0)`), which is a
    correctness change a reviewer must catch in the diff, not a loosening;
  * anything in a module that is not discovered as `test_*.py`.

RAISING A FLOOR IS DELIBERATE AND VISIBLE. When a test legitimately goes away -- a
characterization inverted, a module merged -- `--write` records the new floors, and that diff
lands in the same commit as the change that caused it, where a reviewer sees the number go down
and reads why. That is the whole point: not preventing the drop, but making it impossible for
one to happen without anybody noticing.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from pathlib import Path

import store_io

FLOORS_PATH = Path("ASSERTION_FLOORS.json")

#: Discovery's own pattern, so this cannot drift from what actually runs.
TEST_GLOB = "test_*.py"


def _is_assertion(node: ast.AST) -> str | None:
    """The method name of a `self.assert*` / `self.fail*` call, else None.

    Attribute-name based rather than resolved: a test calling `self.assertEqual` and one calling
    a helper that calls it are different things, and only the first is a countable assertion at
    this module's own level. A helper's assertions are counted in the module that defines it.
    """
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return None
    name = node.func.attr
    if not (name.startswith("assert") or name.startswith("fail")):
        return None
    value = node.func.value
    if isinstance(value, ast.Name) and value.id == "self":
        return name
    return None


def scan_module(path: Path) -> dict:
    """{test_methods, asserts} for one test file. A file that will not parse counts as nothing,
    which `--check` then reports as a drop -- the correct outcome, since a module that no longer
    imports is a module whose guarantees are not running."""
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        return {"test_methods": 0, "asserts": {}}
    methods = 0
    asserts: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            methods += 1
        name = _is_assertion(node)
        if name:
            asserts[name] += 1
    return {"test_methods": methods, "asserts": dict(sorted(asserts.items()))}


def scan(root: Path = Path(".")) -> dict[str, dict]:
    return {path.name: scan_module(path) for path in sorted(root.glob(TEST_GLOB))}


def load(path: Path = FLOORS_PATH) -> dict[str, dict]:
    """The recorded floors, or {} when the file is absent or damaged.

    Deliberately NOT store_io.read, for baseline_manifest.load's reason: `--write` is how a
    broken floors file gets fixed, and store_io's do-not-overwrite-damage guard (#102) would
    block the recovery command. This is an integrity artifact, not user data.
    """
    if not path.exists():
        return {}
    try:
        return dict(json.loads(path.read_text())["modules"])
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return {}


def write(root: Path = Path("."), path: Path = FLOORS_PATH) -> dict[str, dict]:
    modules = scan(root)
    store_io.write(path, {
        "_comment": (
            "Per-module assertion FLOORS -- see assertion_floors.py. These are minimums, not "
            "a fingerprint: adding tests needs no regeneration, and only a DROP fails. "
            "Regenerate with `python3 assertion_floors.py --write` and commit the result in "
            "the same commit as the test change that lowered a number, so the drop is "
            "reviewable rather than incidental."
        ),
        "modules": modules,
    })
    return modules


def drops(root: Path = Path("."), path: Path = FLOORS_PATH) -> list[str]:
    """Every recorded guarantee that is smaller now than when it was recorded, as readable lines.

    A module absent from the floors file is NOT reported: a new test file is an addition, and
    demanding a regeneration to add tests is the reflexive-repair trap this design exists to
    avoid.
    """
    recorded, present = load(path), scan(root)
    lines: list[str] = []
    for module in sorted(recorded):
        floor, now = recorded[module], present.get(module)
        if now is None:
            lines.append(f"{module}: module is gone (floor recorded {floor['test_methods']} test methods)")
            continue
        if now["test_methods"] < floor["test_methods"]:
            lines.append(f"{module}: test methods {floor['test_methods']} -> {now['test_methods']}")
        for name, count in sorted(floor.get("asserts", {}).items()):
            have = now.get("asserts", {}).get(name, 0)
            if have < count:
                lines.append(f"{module}: self.{name} {count} -> {have}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true",
                        help="record what is on disk now as the new floors")
    parser.add_argument("--check", action="store_true",
                        help="report every guarantee that shrank; exit 1 if any did")
    args = parser.parse_args(argv)
    if args.write:
        modules = write()
        total = sum(sum(m["asserts"].values()) for m in modules.values())
        print(f"wrote {FLOORS_PATH} -- {len(modules)} modules, {total} assertions")
        return 0
    shrank = drops()
    if not shrank:
        recorded = load()
        print(f"no guarantee has shrunk ({len(recorded)} modules held to a floor)")
        return 0
    print("A guarantee got smaller. If that is deliberate, say why in the commit and rerun with "
          "--write so the drop lands in the diff:\n")
    for line in shrank:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
