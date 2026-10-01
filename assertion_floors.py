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

WHAT IT CAN NOW SEE, AND COULD NOT UNTIL THIS WAS ADDED. The list above once ended there, and the
omission was load-bearing: a test does not have to lose an assertion to stop running. Measured on a
scratch copy of test_league_config.py, four edits each produced a scan BYTE-IDENTICAL to baseline
-- `@unittest.skip`, `@unittest.expectedFailure`, a leading `self.skipTest()`, and a leading
`return`. Nineteen test methods, every assert count unchanged, nothing to report. `DISABLERS` now
counts all four and `drops` treats an INCREASE as the loss, which is the one place in this file
where growth is the failure. Two remain genuinely unseen and are named rather than implied: a
`for` loop over an empty sequence, and `try/except AssertionError: pass`.

A SKIP IS NOT FORBIDDEN. `skipUnless(CAPTURE.exists(), ...)` is the honest way to say a test needs
the real capture. The floor is the current count, not zero, and `--write` raises it the same way it
lowers an assertion floor -- deliberately, in the diff, next to the reason.

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


#: The ways a test stops running while its text stays in place. Counted per module and ratcheted
#: UPWARD-IS-A-DROP (see `drops`), because every one of them removes coverage without removing a
#: `def test_` or an `assert`, which is all the counts above can see.
#:
#: MEASURED, not imagined. Four mutations were applied to the first test method of a scratch copy
#: of test_league_config.py and the module re-scanned: `@unittest.skip('flaky on CI')`,
#: `@unittest.expectedFailure`, a leading `self.skipTest('no')`, and a leading `return` each
#: produced a scan BYTE-IDENTICAL to baseline -- test_methods 19 -> 19, every assert count
#: unchanged. The reason is structural rather than an oversight: the counts are taken from source
#: text, and none of the four edits touches a `def test_` or an `assert*` call.
#:
#: NOT FORBIDDEN, RATCHETED. `skipUnless(CAPTURE.exists(), ...)` is the honest way to say a test
#: needs the real capture, and several modules here use it correctly. A floor of zero would be
#: wrong and would be worked around. What must not happen quietly is the number GROWING.
DISABLERS = ("skip_decorators", "expected_failures", "skipTest_calls", "early_returns")

#: unittest's own spellings. `skip`, `skipIf`, `skipUnless` all disable; `expectedFailure` inverts.
_SKIP_DECORATORS = frozenset({"skip", "skipIf", "skipUnless"})


def _decorator_names(node: ast.AST):
    """Every decorator on a def/class as a bare final name: `unittest.skip(...)` -> 'skip'."""
    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute):
            yield target.attr
        elif isinstance(target, ast.Name):
            yield target.id


def _disablers_in(tree: ast.AST) -> dict:
    """Count the four silent-disable vectors over a parsed module.

    A CLASS-LEVEL skip counts once per test method it disables, not once: `@unittest.skip` on a
    TestCase with nineteen tests silences nineteen guarantees, and counting it as one would let a
    reviewer read a +1 where the loss is nineteen.
    """
    counts = dict.fromkeys(DISABLERS, 0)

    def is_test(node) -> bool:
        return (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test"))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            names = set(_decorator_names(node))
            tests_inside = sum(1 for child in ast.walk(node) if is_test(child))
            if names & _SKIP_DECORATORS:
                counts["skip_decorators"] += tests_inside
            if "expectedFailure" in names:
                counts["expected_failures"] += tests_inside
        if not is_test(node):
            continue
        names = set(_decorator_names(node))
        if names & _SKIP_DECORATORS:
            counts["skip_decorators"] += 1
        if "expectedFailure" in names:
            counts["expected_failures"] += 1
        # `self.skipTest(...)` anywhere in the body -- a runtime skip reads as a pass.
        for child in ast.walk(node):
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "skipTest"):
                counts["skipTest_calls"] += 1
        # A `return` in the method's OWN top-level body, before any assertion in that body. A
        # return inside an `if` or a loop is ordinary control flow and is not counted -- counting
        # it would flood the floors with false positives and the check would stop being read.
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                counts["early_returns"] += 1
                break
            if any(_is_assertion(c) for c in ast.walk(stmt)):
                break
    return counts


def scan_module(path: Path) -> dict:
    """{test_methods, asserts} for one test file. A file that will not parse counts as nothing,
    which `--check` then reports as a drop -- the correct outcome, since a module that no longer
    imports is a module whose guarantees are not running."""
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, OSError):
        return {"test_methods": 0, "asserts": {}, "disabled": dict.fromkeys(DISABLERS, 0)}
    methods = 0
    asserts: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            methods += 1
        name = _is_assertion(node)
        if name:
            asserts[name] += 1

    # PER-METHOD COUNTS, because the module-level ones cannot see a substitution that nets out.
    #
    # The docstring above promises "any substitution -- one assertion name swapped for another --
    # FAILS, either way". Measured against that promise, it did not: weakening assertEqual to
    # assertIsNotNone in one test while adding an assertEqual to another test IN THE SAME EDIT
    # leaves every module-level count unchanged, and `drops()` returned []. The guarantee was
    # stated without qualification and the check could not keep it.
    #
    # A method rename now surfaces as a drop, and that is the intended behaviour rather than a
    # side effect: a rename IS a substitution of names, the remedy is `--write`, and this
    # module's stated stance is that a floor moving is deliberate and visible in the diff.
    # KEYED ON Class.method, NOT THE BARE METHOD NAME (D-F4). Two classes in one module sharing a
    # test name -- `test_screen_context.py` has four such names, `test_decision_qualifiers.py` one
    # -- collided here, and only the LAST one walked survived into the record. So weakening the
    # unrecorded twin, netted against an addition anywhere else in the module, passed `drops()`:
    # precisely the hole this per-method level was added to close. A qualified key cannot collide,
    # and a module-level test function keeps its bare name because nothing can collide with it.
    by_method: dict[str, dict[str, int]] = {}

    def _counts(fn) -> Counter:
        inner: Counter[str] = Counter()
        for child in ast.walk(fn):
            name = _is_assertion(child)
            if name:
                inner[name] += 1
        return inner

    def _is_test(node) -> bool:
        return (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test"))

    _owned = set()
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        for fn in cls.body:
            if _is_test(fn):
                _owned.add(id(fn))
                inner = _counts(fn)
                if inner:
                    by_method[f"{cls.name}.{fn.name}"] = dict(sorted(inner.items()))
    for node in ast.walk(tree):
        if _is_test(node) and id(node) not in _owned:
            inner = _counts(node)
            if inner:
                by_method[node.name] = dict(sorted(inner.items()))
    return {"test_methods": methods, "asserts": dict(sorted(asserts.items())),
            "by_method": {k: by_method[k] for k in sorted(by_method)},
            "disabled": _disablers_in(tree)}


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
        # The same comparison one level down, which is where a netting-out substitution shows.
        present_methods = now.get("by_method", {})
        for method, recorded_asserts in sorted(floor.get("by_method", {}).items()):
            if method not in present_methods:
                lines.append(f"{module}: test method {method} is gone")
                continue
            for name, count in sorted(recorded_asserts.items()):
                have = present_methods[method].get(name, 0)
                if have < count:
                    lines.append(f"{module}: {method} self.{name} {count} -> {have}")
        # THE ONE QUANTITY WHERE GROWTH IS THE DROP. Every count above is a guarantee and shrinking
        # it is the loss. These are the opposite: each is a test that no longer runs, so MORE of
        # them is less coverage, and the comparison inverts. Reported in the same list and through
        # the same `--write` remedy, because a deliberate new skip should land in the diff beside
        # the reason for it exactly as a removed assertion does.
        floor_disabled = floor.get("disabled", {})
        now_disabled = now.get("disabled", {})
        for name in DISABLERS:
            was, have = floor_disabled.get(name, 0), now_disabled.get(name, 0)
            if have > was:
                lines.append(f"{module}: {name} {was} -> {have} "
                             f"({have - was} more test(s) no longer run)")
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
    recorded = load()
    if not recorded:
        # AN INTEGRITY CHECK HOLDING NOTHING MUST NOT REPORT SUCCESS. `load()` returns {} for a
        # missing OR DAMAGED floors file -- deliberately, so `--write` can repair one without
        # store_io's do-not-overwrite guard blocking the recovery. That is right for `load`, and
        # it meant `--check` printed "no guarantee has shrunk (0 modules held to a floor)" and
        # exited 0 over an empty file and an empty tree. Green, holding nothing.
        print(f"{FLOORS_PATH} records no floors (missing or damaged). This check is holding "
              "NOTHING, which is not the same as nothing having shrunk. Run --write to "
              "record the current guarantees.")
        return 1
    if not shrank:
        print(f"no guarantee has shrunk ({len(recorded)} modules held to a floor)")
        return 0
    print("A guarantee got smaller. If that is deliberate, say why in the commit and rerun with "
          "--write so the drop lands in the diff:\n")
    for line in shrank:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
