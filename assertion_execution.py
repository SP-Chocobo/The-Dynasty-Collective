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
      python3 assertion_execution.py --check              (see below)
      python3 assertion_execution.py --write              (full suite only)

WHAT `--check` REFUSES, which is more than "the count grew" -- that was the whole description
once, and it was the defect: a verdict reached over nothing passed. It fails on a test that is
newly silent, on a recorded entry with no reason, on ANY test that errored (the sweep did not
measure those, and the docstring above promises the error is the finding), and on a full sweep
running fewer tests than the one the record was written over. It exits 2 rather than 1 when the
record is missing or damaged, because then it is holding nothing and has judged nothing.
"""

from __future__ import annotations

import argparse
import collections
import inspect
import pathlib
import sys
import typing
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


class Sweep(typing.NamedTuple):
    """A verdict AND the population it was reached over (`#245`).

    `measure` used to return the silent list alone, and `--check` compared that list against the
    record without ever asking how many tests had been measured to produce it. 359 tests measured
    and 5 tests errored out of 5 gave byte-identical output and the same exit code -- proved by
    making `pandas` unimportable, which turns every test into an error, which removes every test
    from the silent list, which reads as "nothing new is silent". A verdict carried without its
    denominator cannot be checked for vacuity by its caller, so the denominator travels with it.
    """

    silent: tuple[str, ...]
    ran: int
    skipped: int
    errored: int
    modules: int


def measure(modules: list[str]) -> Sweep:
    """Which tests ran, skipped, errored, and which reached the end having asserted nothing."""
    _instrument()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(loader.loadTestsFromName(m) for m in modules)
    runner = unittest.TextTestRunner(resultclass=_Result, verbosity=0,
                                     stream=open("/dev/null", "w"))
    runner.run(suite)
    silent = tuple(sorted(t for t in _RAN
                          if t not in _SKIPPED and t not in _BROKEN and _COUNTS[t] == 0))
    return Sweep(silent, len(_RAN), len(_SKIPPED), len(_BROKEN), len(modules))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("modules", nargs="*")
    parser.add_argument("--write", action="store_true", help="record the current set")
    parser.add_argument("--check", action="store_true", help="fail if the set grew")
    args = parser.parse_args(argv)

    full_scope = not args.modules
    modules = args.modules or sorted(q.stem for q in pathlib.Path(".").glob("test_*.py"))
    sweep = measure(modules)
    silent = list(sweep.silent)

    if args.write:
        # AN ALLOWLIST WITH REASONS, not a bare list -- the same idiom as
        # `config_space.DEPENDENT_REASONS` and `draft_battery.UNCOVERED_AXES`. A silent test is not
        # automatically wrong: `test_no_scenario_raises`'s entire contract is "this does not raise",
        # and it fails by raising. What must not happen is a silent test appearing without anyone
        # stating which of those two it is, so `--check` refuses an entry whose reason is blank.
        existing = {}
        try:
            existing = dict(store_io.read(RECORD_PATH, {}).get("silent_tests", {}))
        except Exception:
            pass
        if not full_scope:
            # A RECORD WRITTEN AT REDUCED SCOPE WOULD BE A SMALLER RECORD, NOT A CORRECTED ONE.
            # Every test outside the named modules is absent from `silent`, so writing would drop
            # its entry and the reason someone wrote by hand, and would record a population floor
            # a full sweep then clears trivially. The flag combination has no honest meaning.
            print(f"--write records the whole suite's verdict and refuses a partial sweep "
                  f"({len(modules)} module(s) named). Rerun without naming modules.")
            return 2
        record = {
            "_comment": ("Tests that RAN and executed no assertion, each with why that is "
                         "legitimate. A test whose only failure mode is an exception or an "
                         "explicit self.fail is real; one that simply cannot fail is not "
                         "evidence. See assertion_execution.py. A NEW entry needs a reason "
                         "written by hand -- --write leaves it empty on purpose."),
            "silent_tests": {t: existing.get(t, "") for t in silent},
            "population": {
                "_comment": ("The sweep this verdict was reached over, so --check can tell a "
                             "measurement from a collapse. tests_ran is a FLOOR in the sense "
                             "assertion_floors uses: fewer tests running than when the verdict "
                             "was recorded means the verdict covers less, whatever its content."),
                "tests_ran": sweep.ran,
                "modules_swept": sweep.modules,
            },
        }
        store_io.write(RECORD_PATH, record)
        blank = [t for t in silent if not existing.get(t)]
        print(f"wrote {RECORD_PATH} -- {len(silent)} silent test(s), "
              f"{len(blank)} awaiting a reason, over {sweep.ran} tests that ran "
              f"({sweep.skipped} skipped, {sweep.errored} errored)")
        for t in blank:
            print(f"  NEEDS A REASON: {t}")
        return 0

    if args.check:
        # `read_state`, NOT `read`. `store_io.read` is fail-soft by design and returns the
        # default for a file that is missing OR unparseable, so the `try/except` that used to
        # stand here could not fire and a damaged record read as an empty one -- which this branch
        # would then treat as "no silent tests recorded". `read_state` returns the one bit that
        # separates the two (`#187`: absence is not a value).
        stored, readable = store_io.read_state(RECORD_PATH, {})
        if not readable:
            print(f"{RECORD_PATH} is missing or damaged -- this check is holding NOTHING, which "
                  f"is not the same as nothing having gone silent. Run --write.")
            return 2
        recorded = dict(stored.get("silent_tests", {}))
        population = dict(stored.get("population", {}))

        # THE ERRORS ARE THE FINDING, AND THIS BRANCH USED TO DROP THEM. The module docstring
        # promises "a test that errored -- the error is the finding", and the check reported it
        # nowhere: an errored test is in neither `silent` nor `grew`, so a sweep where every test
        # blew up printed the same green line as a clean one. Errors are failed measurements, so
        # they are reported here before the comparison rather than inside it -- the verdict below
        # is about tests that RAN, and it does not become true by the rest having died.
        complaints = []
        if sweep.errored:
            complaints.append(f"{sweep.errored} of {sweep.ran + sweep.errored} test(s) ERRORED -- "
                              f"this sweep did not measure them, and a test that cannot be run "
                              f"cannot be cleared. Fix the errors, then rerun.")

        # A FLOOR ON THE POPULATION, which is what `assertion_floors` has and this did not. Its
        # absence is the whole of the defect proved at `I3`: with `pandas` made unimportable,
        # "0 of 5 tests ran, 5 errored" and "0 of 359 tests ran, 0 errored" were byte-identical.
        # Growth is fine and needs no regeneration -- new tests are an addition, exactly as
        # `assertion_floors.drops` treats a new module.
        floor = population.get("tests_ran")
        if floor is None:
            complaints.append(f"{RECORD_PATH} records no population, so this check cannot tell "
                              f"a sweep from a collapse. Run --write.")
        elif full_scope and sweep.ran < floor:
            complaints.append(f"only {sweep.ran} test(s) ran where the record was written over "
                              f"{floor}. The verdict below covers less than the one on file; "
                              f"that is a shrunken measurement, not a clean result.")

        grew = sorted(set(silent) - set(recorded))
        unexplained = sorted(t for t in silent if t in recorded and not recorded[t])
        for t in grew:
            complaints.append(f"NEW SILENT TEST (runs, passes, asserts nothing): {t}")
        for t in unexplained:
            complaints.append(f"SILENT WITH NO STATED REASON: {t}")
        if complaints:
            for line in complaints:
                print(line)
            return 1

        # `len(recorded)` -- THE RECORD'S SIZE, which is what the sentence says. It printed
        # `len(silent)`, this run's hit count, under the word "known": 18 at full scope and 0 at
        # reduced scope for the same 14-entry record (`#174`, the number crossed while its label
        # did not). The scope is named too, because the floor only binds on a full sweep.
        scope = (f"over {sweep.ran} tests that ran" if full_scope
                 else f"over {sweep.ran} tests in {sweep.modules} named module(s), "
                      f"so the population floor does not bind")
        print(f"no new silent tests ({len(recorded)} known, each with a reason) {scope}")
        return 0

    for t in silent:
        print(t)
    print(f"\n{len(silent)} of {sweep.ran} tests that ran executed no assertion "
          f"({sweep.skipped} skipped, {sweep.errored} errored)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
