"""`test_ui_source`'s app.py-read guard has the module-wide escape that D-F5 removed from its twin.

The guard (`NoTestReadsAppPyDirectlyTests.test_no_test_module_reads_app_py_off_disk`) is:

    if ('"app.py"' in code or "'app.py'" in code) and "ui_source" not in code:
        offenders.append(path.name)

The second clause is a MODULE-WIDE ESCAPE. D-F5 was the identical construct in the
hand-written-capture-path guard (`or "CAPTURE_PATH" in src`), and the repair's own comment says
why it had to go: "ANY module that mentioned the constant anywhere was skipped whole -- and the
one real offender was the one module the guard refused to look at, and it reported zero."
The capture-path guard was repaired. This one was not.

This probe uses the instrument's OWN helper, `_offends` -- the test class states that helper is
"the same expression the scan below uses, so this cannot drift away from what it is checking",
so whatever `_offends` says about a body is what the real scan says about a module with that
body. No file on disk is touched.

Run from the repo root:
  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_ui_source_guard_escape.py
"""
import pathlib

from test_source_scan import code_text
import test_ui_source as t

G = t.NoTestReadsAppPyDirectlyTests

PLAIN_OFFENDER = (
    'from pathlib import Path\n'
    'APP = Path(__file__).with_name("app.py")\n'
    'def f():\n    return APP.read_text(encoding="utf-8")\n'
)

#: THE SAME OFFENCE, in a module that also uses ui_source for something else. This is not a
#: contrived shape: the migration moved 22 modules onto ui_source, so "imports ui_source AND
#: also reads app.py" is the shape a half-migrated module has.
OFFENDER_THAT_ALSO_USES_UI_SOURCE = (
    'import ui_source\n'
    'from pathlib import Path\n'
    'APP = Path(__file__).with_name("app.py")\n'
    'def surface():\n    return ui_source.text()\n'
    'def f():\n    return APP.read_text(encoding="utf-8")\n'
)


def main() -> None:
    print(f"plain direct read of app.py                     -> offends={G._offends(PLAIN_OFFENDER)}")
    print(f"same read, in a module that also uses ui_source -> "
          f"offends={G._offends(OFFENDER_THAT_ALSO_USES_UI_SOURCE)}")

    # How many real test modules the escape currently covers: each is a module in which a direct
    # app.py read would be invisible to the guard.
    covered, named_app = [], []
    for p in sorted(pathlib.Path(".").glob("test_*.py")):
        code = code_text(p)
        if "ui_source" in code:
            covered.append(p.name)
        if '"app.py"' in code or "'app.py'" in code:
            named_app.append(p.name)
    print(f"\ntest modules on disk                            : "
          f"{len(list(pathlib.Path('.').glob('test_*.py')))}")
    print(f"modules the escape exempts WHOLE (mention ui_source in code): {len(covered)}")
    print(f"modules naming app.py in code at all            : {len(named_app)}  {named_app}")
    print(f"ALLOWED (named exemptions, with reasons)        : {sorted(G.ALLOWED)}")
    print("\n-> inside any of the exempted modules, a direct app.py read is not reported, and\n"
          "   the guard prints zero offenders. That is the D-F5 shape, in the instrument whose\n"
          "   whole subject is a guard that keeps passing after losing its subject.")


if __name__ == "__main__":
    main()
