"""D-F4: the per-method floor key. Does the qualified key close the collision, and does anything
in the suite exercise the collision at all?

TRIAGE_V4 calls this "the ratchet every future certification in this repo rests on". The repair
keys `by_method` on `Class.method`. This probe:

  1. builds the exact collision the repair describes -- two classes in one module sharing a test
     name -- records floors, weakens the FIRST twin and adds an assertion elsewhere so the module
     total nets out, and asks `drops()`;
  2. scans the repository for key shapes the qualified key does NOT disambiguate.

Run from the repo root:
    PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 \
        evidence/blind_pass_v4/probes/probe_df4_floor_key_collision.py
"""
import ast
import collections
import json
import pathlib
import tempfile

import assertion_floors as af

TWINS_STRONG = '''
import unittest


class First(unittest.TestCase):
    def test_same_name(self):
        self.assertEqual(1, 1)
        self.assertEqual(2, 2)


class Second(unittest.TestCase):
    def test_same_name(self):
        self.assertEqual(3, 3)

    def test_other(self):
        self.assertIn(1, [1])
'''

# The FIRST twin loses an assertEqual; `test_other` gains one. Module total unchanged.
TWINS_WEAKENED = '''
import unittest


class First(unittest.TestCase):
    def test_same_name(self):
        self.assertEqual(1, 1)


class Second(unittest.TestCase):
    def test_same_name(self):
        self.assertEqual(3, 3)

    def test_other(self):
        self.assertIn(1, [1])
        self.assertEqual(9, 9)
'''

with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    mod = root / "test_twins.py"
    floors = root / "FLOORS.json"

    mod.write_text(TWINS_STRONG)
    scan = af.scan_module(mod)
    print("by_method keys recorded for the twin module:")
    for k, v in sorted(scan["by_method"].items()):
        print(f"    {k!r:<30} {v}")
    print("  -> both twins recorded separately:",
          sum(1 for k in scan["by_method"] if k.endswith(".test_same_name")) == 2)

    floors.write_text(json.dumps({"modules": {"test_twins.py": scan}}))
    mod.write_text(TWINS_WEAKENED)
    after = af.scan_module(mod)
    print("  module TOTAL asserts before/after:",
          sum(scan["asserts"].values()), "/", sum(after["asserts"].values()),
          "(unchanged -> only the per-method level can catch this)")
    found = af.drops(root, floors)
    print("  drops() reports:", found)
    print("  VERDICT:", "COLLISION CLOSED" if any("First.test_same_name" in f for f in found)
          else "NOT CAUGHT")

print()
print("--- key shapes the qualified key does NOT disambiguate, scanned over the real tree ---")
dup_class, nested, nonbody = [], [], []
for path in sorted(pathlib.Path(".").glob("test_*.py")):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        continue
    names = collections.Counter(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    for name, count in names.items():
        if count > 1:
            dup_class.append(f"{path}:{name} x{count}")
    # a ClassDef that is not a direct child of the module -> `Inner.method`, outer lost
    top = {id(n) for n in tree.body if isinstance(n, ast.ClassDef)}
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef) and id(n) not in top:
            if any(isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and f.name.startswith("test") for f in n.body):
                nested.append(f"{path}:{n.lineno}:{n.name}")
    # a test def inside a class but NOT in cls.body -> falls through to the BARE-name path
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        direct = {id(f) for f in cls.body}
        for n in ast.walk(cls):
            if (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name.startswith("test") and id(n) not in direct and n is not cls):
                nonbody.append(f"{path}:{n.lineno}:{cls.name}.{n.name}")
print("  two classes with the SAME NAME in one module (still collide):", dup_class or "none")
print("  test methods in a NESTED class (keyed Inner.method, outer dropped):", nested or "none")
print("  test defs inside a class but not in cls.body (fall to the BARE-name path):",
      nonbody[:8] or "none", f"... n={len(nonbody)}" if len(nonbody) > 8 else "")
