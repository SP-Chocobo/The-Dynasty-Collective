#!/usr/bin/env bash
# THE DECISIVE TESTS: break the thing each instrument claims to catch, read what it says, restore.
#
# Run from the repo root, with NOTHING ELSE RUNNING against this tree -- each arm edits a tracked
# .py file and `git checkout --` restores it, and a suite importing that file mid-cycle would
# measure neither the clean tree nor the mutant (engine-measurement: "Never mutate a source file
# while a long measurement is in flight").
#
# PYTHONDONTWRITEBYTECODE=1 throughout and __pycache__ cleared between arms: a length-preserving
# mutate/restore inside one mtime second otherwise leaves a .pyc serving the MUTATED bytecode from
# a source file that reads correctly on disk (#240).
#
#   bash evidence/blind_pass_v4/probes/decisive_tests.sh
set -u
export PYTHONDONTWRITEBYTECODE=1
cd "$(git rev-parse --show-toplevel)"

banner() { echo; echo "=============================================================="; echo "$1"; echo "=============================================================="; }
clean()  { find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null; }
restore(){ git checkout -- "$@"; clean; }

if [ -n "$(git status --short)" ]; then
  echo "REFUSING: the tree is not clean; a restore could not be verified."; git status --short; exit 2
fi

# ---------------------------------------------------------------------------------------------
banner "A. prose_names.misquoted_constants -- is the history shield PARAGRAPH-scoped?"
# The site: test_a_flex_slot_is_not_an_unlimited_bench.py's module docstring quotes
# `FLEX_GROUP_DEPTH_FACTOR` is 3.0 in a paragraph carrying NO marker, inside a docstring whose
# OTHER paragraphs carry one. The CONTROL site carries no marker anywhere in its block.
echo "--- baseline ---"; python3 prose_names.py | tail -2; echo "baseline exit=$?"

echo
echo "--- BREAK 1: the SHIELDED site. Prose now states a value the code does not have. ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("test_a_flex_slot_is_not_an_unlimited_bench.py")
t = p.read_text()
assert "`FLEX_GROUP_DEPTH_FACTOR` is 3.0" in t, "the quotation moved; pick a new site"
p.write_text(t.replace("`FLEX_GROUP_DEPTH_FACTOR` is 3.0", "`FLEX_GROUP_DEPTH_FACTOR` is 9.0", 1))
print("prose now says 9.0; draft_room.FLEX_GROUP_DEPTH_FACTOR is still 3.0")
PY
clean; python3 prose_names.py | tail -2; echo "exit=${PIPESTATUS[0]}"
python3 -c "
import prose_names as pn
print('misquoted_constants reports:', pn.misquoted_constants() or 'NOTHING')"
restore test_a_flex_slot_is_not_an_unlimited_bench.py

echo
echo "--- BREAK 2 (the control): the SAME break at an UNSHIELDED site ---"
python3 - <<'PY'
import pathlib, re, prose_names as pn
real = pn.numeric_constants()
# Find a python prose quotation whose own BLOCK carries no marker at all.
for path, line, text in pn.prose_blocks():
    if pn.is_history(text):
        continue
    for m in pn.QUOTED_VALUE.finditer(text):
        name = m.group(1) or m.group(3)
        if name not in real:
            continue
        form = m.group(0)
        p = pathlib.Path(path)
        src = p.read_text()
        if src.count(form) != 1:
            continue
        num = m.group(2) or m.group(4)
        bad = form.replace(num, "99999.0")
        p.write_text(src.replace(form, bad, 1))
        print(f"UNSHIELDED site broken: {path}:{line}  {form!r} -> {bad!r}")
        pathlib.Path("/tmp/_unshielded_site").write_text(str(path))
        raise SystemExit(0)
raise SystemExit("no unshielded python quotation found")
PY
clean; python3 prose_names.py | tail -3; echo "exit=${PIPESTATUS[0]}"
restore "$(cat /tmp/_unshielded_site)"; rm -f /tmp/_unshielded_site

# ---------------------------------------------------------------------------------------------
banner "B. invariant_registry -- can the figure-site census see a bare f-string render?"
echo "--- baseline ---"; python3 invariant_registry.py | grep "one engine figure"; echo
echo "--- BREAK: add ONE bare f-string render of an engine figure to the UI surface ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("app.py")
p.write_text(p.read_text() + '\n\ndef _v4_probe_render(rec):\n'
             '    st.caption(f"{rec.team_acquisition_value:.0f} UV pts")\n')
print("app.py now renders an engine figure with a bare f-string (Python half-to-even,")
print("toFixed half-away-from-zero -- the defect the entry's population field names).")
PY
clean; python3 invariant_registry.py | grep "one engine figure"; python3 invariant_registry.py >/dev/null; echo "invariant_registry exit=$?"
restore app.py

echo
echo "--- CONTROL: add ONE CONFORMING _figure(...) render instead ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("app.py")
p.write_text(p.read_text() + '\n\ndef _v4_probe_render_ok(rec):\n'
             '    st.caption(_figure(rec.team_acquisition_value))\n')
PY
clean; python3 invariant_registry.py | grep "one engine figure"; python3 invariant_registry.py >/dev/null; echo "invariant_registry exit=$?"
restore app.py

# ---------------------------------------------------------------------------------------------
banner "C. test_ui_source -- does the app.py-read guard fire inside a ui_source module?"
echo "--- baseline ---"
python3 -m unittest -q test_ui_source.NoTestReadsAppPyDirectlyTests.test_no_test_module_reads_app_py_off_disk 2>&1 | tail -3
echo
echo "--- BREAK: plant a direct app.py read in a module that ALSO imports ui_source ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("test_positional_depth_coverage.py")
t = p.read_text()
assert "import ui_source" in t
p.write_text(t + '\n\nfrom pathlib import Path as _P\n'
             '_V4_APP = _P(__file__).with_name("app.py")\n'
             'def _v4_read_app_directly():\n'
             '    return _V4_APP.read_text(encoding="utf-8")\n')
print("test_positional_depth_coverage.py now reads app.py off disk, in code, not prose.")
PY
clean
python3 -m unittest -q test_ui_source.NoTestReadsAppPyDirectlyTests.test_no_test_module_reads_app_py_off_disk 2>&1 | tail -3
echo
echo "--- CONTROL: the same plant in a module that does NOT mention ui_source ---"
restore test_positional_depth_coverage.py
python3 - <<'PY'
import pathlib
p = pathlib.Path("test_bye_collision.py")
t = p.read_text()
assert "ui_source" not in t, "pick a module that does not mention ui_source"
p.write_text(t + '\n\nfrom pathlib import Path as _P\n'
             '_V4_APP = _P(__file__).with_name("app.py")\n'
             'def _v4_read_app_directly():\n'
             '    return _V4_APP.read_text(encoding="utf-8")\n')
PY
clean
python3 -m unittest -q test_ui_source.NoTestReadsAppPyDirectlyTests.test_no_test_module_reads_app_py_off_disk 2>&1 | tail -4
restore test_bye_collision.py

# ---------------------------------------------------------------------------------------------
banner "D. assertion_floors --check -- does it still catch a weakening? (the control instrument)"
echo "--- baseline ---"; python3 assertion_floors.py --check
echo "--- BREAK: weaken one assertEqual to assertIsNotNone AND add an assertEqual elsewhere ---"
python3 - <<'PY2'
import pathlib
p = pathlib.Path("test_bye_collision.py")
t = p.read_text()
assert "self.assertEqual(" in t
# assertion_floors is a STATIC scan, so the file only has to parse: an extra positional on
# assertIsNotNone is irrelevant to it and keeps the edit a one-token substitution.
t = t.replace("self.assertEqual(", "self.assertIsNotNone(", 1)
# ...and net it out with an addition elsewhere in the SAME module, which is the edit that
# defeated the module-level counts before the per-method level was added.
t += ('\n\nclass _V4Netting(unittest.TestCase):\n'
      '    def test_netting(self):\n        self.assertEqual(1, 1)\n')
p.write_text(t)
print("weakened the first assertEqual in test_bye_collision.py and added one back elsewhere")
PY2
clean; python3 assertion_floors.py --check; echo "assertion_floors exit=$?"
restore test_bye_collision.py

# ---------------------------------------------------------------------------------------------
banner "E. render_trace --check -- does it still catch a UI change? (the control instrument)"
echo "--- baseline ---"; python3 render_trace.py --check
echo "--- BREAK: add one st.caption to the Matchup view ---"
python3 - <<'PY'
import pathlib
p = pathlib.Path("app.py")
t = p.read_text()
anchor = "if main_view == MATCHUP_VIEW:"
i = t.index(anchor) + len(anchor)
p.write_text(t[:i] + '\n    st.caption("v4 probe")' + t[i:])
PY
clean; python3 render_trace.py --check | head -8; echo "render_trace exit=${PIPESTATUS[0]}"
restore app.py

banner "RESTORED?"
git status --short && echo "(empty above means the tree is clean)"
