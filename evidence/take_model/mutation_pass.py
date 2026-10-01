"""In-memory mutation pass for test_take_model_coherence.

Patches draft_strategy's module attributes rather than rewriting the file, so it is safe to run
while a long measurement holds that module. The test reads those attributes at call time, so an
attribute patch is a real mutation of what the test sees.
"""
import unittest, importlib, sys
import draft_strategy as ds
import test_take_model_coherence as t

ORIG = {"tbl": dict(ds.RANK_TAKE_PROBABILITY),
        "floor": ds.RANK_TAKE_PROBABILITY_FLOOR,
        "fn": ds._take_probability}

def run():
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(t)
    res = unittest.TextTestRunner(verbosity=0, stream=open("/dev/null", "w")).run(suite)
    return len(res.failures) + len(res.errors)

def restore():
    ds.RANK_TAKE_PROBABILITY = dict(ORIG["tbl"])
    ds.RANK_TAKE_PROBABILITY_FLOOR = ORIG["floor"]
    ds._take_probability = ORIG["fn"]

def mut(name, apply_fn, expect):
    restore()
    apply_fn()
    bad = run()
    got = "pass" if bad == 0 else f"fail({bad})"
    ok = (got == "pass") == (expect == "pass")
    print(f"{name:52s} {got:9s} {'as designed' if ok else '<-- WRONG, wanted ' + expect}")
    restore()

restore()
assert run() == 0, "baseline must be green"
print("baseline: green\n")

mut("M1 floor -> 0.0 (model becomes near-coherent)",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY_FLOOR", 0.0), "fail")
mut("M2 floor -> 0.004 (excess shrinks 5x)",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY_FLOOR", 0.004), "fail")
mut("M3 table truncated to rank 1 only",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY", {1: 0.55}), "fail")
mut("M4 table inflated (1.21 -> 3.0)",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY", {k: v * 2.48 for k, v in ORIG["tbl"].items()}), "fail")
mut("M5 floor -> 0.5 (floor WOULD explain #206)",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY_FLOOR", 0.5), "fail")
mut("M6 rank-1 take drops 0.55 -> 0.05",
    lambda: setattr(ds, "RANK_TAKE_PROBABILITY", {**ORIG["tbl"], 1: 0.05}), "fail")
mut("M7 deep ranks decay instead of flooring",
    lambda: setattr(ds, "_take_probability",
                    lambda rank, run_: ORIG["tbl"].get(rank, ORIG["floor"] / rank)), "fail")
mut("M8 domain limit: rank>5 contributes nothing (a real fix)",
    lambda: setattr(ds, "_take_probability",
                    lambda rank, run_: ORIG["tbl"].get(rank, 0.0)), "fail")
restore()
print("\nrestored; baseline re-check:", "green" if run() == 0 else "RED")
