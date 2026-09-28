"""Which tests RUN without executing a single assertion (`0.9`).

`assertion_floors.py` counts assertions in SOURCE. That is the right instrument for "did a
guarantee shrink", and it is blind to a different question: a test method can contain no assertion
of its own and still be a real test, because it delegates to a helper that asserts -- and it can
contain one that never executes, because it sits behind a branch the test never takes.

Measured statically, 27 test methods in this repository have no `self.assert*` in their own body.
That number is not the finding: most of those delegate correctly. The finding is whichever tests
REACH THE END having asserted nothing, and only running them answers that.

HOW IT WORKS. Every `assert*` / `fail*` method on `unittest.TestCase` is wrapped with a counter
keyed by the test currently running, and a result class records which tests actually ran. A test
that ran, did not skip, did not error, and whose counter is zero asserted nothing -- it cannot
fail, so it is not evidence.

WHAT IT DELIBERATELY DOES NOT CALL A DEFECT:
  * a skipped test -- it did not run, which is `0.4`'s subject, not this one;
  * a test that errored -- the error is the finding;
  * a test asserting through a helper, which this instrument sees correctly because the helper's
    `self.assert*` call is still a call on the same TestCase.

WHAT IT CANNOT SEE, stated because a check whose limits are unstated gets trusted past them:
an assertion that is not a `self.assert*`/`self.fail*` call at all. `pd.testing.assert_frame_equal`
is a real assertion and this instrument is blind to it, so a test using one is reported as silent
and is a FALSE POSITIVE -- which is why the record is an allowlist with reasons rather than a
verdict. Measured on the first full sweep: 14 silent tests, of which one was this.

Run:  python3 assertion_execution.py [module ...]        (default: every test_*.py)
      python3 assertion_execution.py --check              (fail if the count grew)
"""

from __future__ import annotations

import argparse
import collections
import inspect
import pathlib
import sys
import unittest

import store_io

RECORD_PATH = pathlib.Path("ASSERTION_EXECUTION.json")

_COUNTS: collections.Counter = collections.Counter()
_CURRENT: dict = {"id": None}
_RAN: set = set()
_SKIPPED: set = set()
_BROKEN: set = set()


def _instrument() -> None:
    """Wrap every assertion method on TestCase with a per-test counter.

    Wrapped rather than subclassed: the suite's own classes inherit from `unittest.TestCase`
    directly, and a subclass would only see tests that opted in -- which is the coverage hole this
    file exists to measure.
    """
    for name in dir(unittest.TestCase):
        if not (name.startswith("assert") or name.startswith("fail")):
            continue
        original = getattr(unittest.TestCase, name, None)
        # FUNCTIONS ONLY. unittest's failureException attribute also starts with "fail" and is a CLASS
        # (AssertionError), and `callable()` is true for a class -- so the first version of this
        # replaced it with a function wrapper and unittest's own error path died on
        # `issubclass() arg 2 must be a class`. The instrument broke the framework it measures,
        # which is a fair opening result for a file about instruments that do not check what
        # their names say.
        if not inspect.isfunction(original) or getattr(original, "_counted", False):
            continue

        def wrapper(self, *args, _original=original, **kwargs):
            _COUNTS[_CURRENT["id"]] += 1
            return _original(self, *args, **kwargs)

        wrapper._counted = True          # idempotent under a double call
        setattr(unittest.TestCase, name, wrapper)


class _Result(unittest.TextTestResult):
    def startTest(self, test):
        _CURRENT["id"] = test.id()
        _RAN.add(test.id())
        super().startTest(test)

    def addSkip(self, test, reason):
        _SKIPPED.add(test.id())
        super().addSkip(test, reason)

    def addError(self, test, err):
        _BROKEN.add(test.id())
        super().addError(test, err)

    def addFailure(self, test, err):
        # A FAILURE asserted something -- that is how it failed. Not a candidate here.
        super().addFailure(test, err)


def measure(modules: list[str]) -> list[str]:
    """Test ids that ran, did not skip or error, and executed no assertion."""
    _instrument()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(m) for m in modules)
    runner = unittest.TextTestRunner(resultclass=_Result, verbosity=0,
                                     stream=open("/dev/null", "w"))
    runner.run(suite)
    silent = sorted(t for t in _RAN
                    if t not in _SKIPPED and t not in _BROKEN and _COUNTS[t] == 0)
    return silent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("modules", nargs="*")
    parser.add_argument("--write", action="store_true", help="record the current set")
    parser.add_argument("--check", action="store_true", help="fail if the set grew")
    args = parser.parse_args(argv)

    modules = args.modules or sorted(q.stem for q in pathlib.Path(".").glob("test_*.py"))
    silent = measure(modules)

    if args.write:
        # AN ALLOWLIST WITH REASONS, not a bare list -- the same idiom as
        # `config_space.DEPENDENT_REASONS` and `draft_battery.UNCOVERED_AXES`. A silent test is not
        # automatically wrong: `test_no_scenario_raises`'s entire contract is "this does not raise",
        # and it fails by raising. What must not happen is a silent test appearing without anyone
        # stating which of those two it is, so `--check` refuses an entry whose reason is blank.
        existing = {}
        try:
            existing = dict(store_io.read(RECORD_PATH).get("silent_tests", {}))
        except Exception:
            pass
        store_io.write(RECORD_PATH, {
            "_comment": ("Tests that RAN and executed no assertion, each with why that is "
                         "legitimate. A test whose only failure mode is an exception or an "
                         "explicit self.fail is real; one that simply cannot fail is not "
                         "evidence. See assertion_execution.py. A NEW entry needs a reason "
                         "written by hand -- --write leaves it empty on purpose."),
            "silent_tests": {t: existing.get(t, "") for t in silent},
        })
        blank = [t for t in silent if not existing.get(t)]
        print(f"wrote {RECORD_PATH} -- {len(silent)} silent test(s), "
              f"{len(blank)} awaiting a reason")
        for t in blank:
            print(f"  NEEDS A REASON: {t}")
        return 0

    if args.check:
        try:
            recorded = dict(store_io.read(RECORD_PATH).get("silent_tests", {}))
        except Exception:
            print(f"{RECORD_PATH} is missing or damaged -- this check is holding NOTHING. "
                  f"Run --write.")
            return 2
        grew = sorted(set(silent) - set(recorded))
        unexplained = sorted(t for t in silent if t in recorded and not recorded[t])
        if grew or unexplained:
            for t in grew:
                print(f"NEW SILENT TEST (runs, passes, asserts nothing): {t}")
            for t in unexplained:
                print(f"SILENT WITH NO STATED REASON: {t}")
            return 1
        print(f"no new silent tests ({len(silent)} known, each with a reason)")
        return 0

    for t in silent:
        print(t)
    print(f"\n{len(silent)} of {len(_RAN)} tests that ran executed no assertion "
          f"({len(_SKIPPED)} skipped, {len(_BROKEN)} errored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
