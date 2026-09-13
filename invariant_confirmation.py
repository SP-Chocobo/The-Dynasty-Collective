"""Does the EXISTING suite actually defend the invariants the freeze rests on?

A test that mentions a mutation is not a mutation-checked test, and a module with an assertion
floor is not a defended module. The only honest answer to "is the older work confirmed?" is to
BREAK THE ENGINE and see whether anything fails.

This harness does that against the load-bearing invariants named in FREEZE_CHECKLIST.md -- the
ones whose failure would make the freeze's claims untrue -- and reports, per invariant, whether
the suite as it stands catches the break.

WHY EACH TARGET IS HERE, rather than a broad sweep:

BUILT (both in MUTATIONS below):

  feasibility_first   The #164 blocker family (#154/#155/#114) was DISSOLVED on the evidence
                      that every seat of every format now fills its lineup. That backstop is
                      what makes it true. If it can be silently disabled, the dissolution is
                      undefended and the freeze rests on nothing.
  _board_order        Sorts on ["_feasible", "final_score", "player_id"]. It decides every
                      pick. Dropping _feasible makes feasibility advisory.

NAMED BUT NOT BUILT -- stated here rather than left as an implied claim:

  narrow_candidates   #55 declined to give pick_necessity selection authority partly BECAUSE
                      narrow_candidates already includes the best remaining player at every
                      position, so a scarce-position leader is never invisible. That argument
                      is only as good as the guarantee. NO MUTATION EXISTS FOR IT HERE.
  absence contract    The repo's central rule (#61/#187/#190/#203): unpriced carries None,
                      never 0.0. A basis asserted where no price exists is the failure mode
                      every absence item in the register exists to prevent. NO MUTATION EXISTS
                      FOR IT HERE either; the contract is defended by its own test modules, not
                      by this harness.

  This list used to read as four covered targets. It was two. An unexecuted harness whose
  docstring overclaims its own coverage is the #133 defect in a new file.

THIS HARNESS HAS NEVER PRODUCED A MEASUREMENT, AND UNTIL 2026-09-12 IT COULD NOT.

Both anchors occur TWICE in draft_room.py -- once in the upside-mode branch of
compute_draft_board and once in the balanced branch -- and the runner refused any anchor whose
count was not exactly 1, so every arm reported ANCHOR FAILED and nothing was ever mutated.
Checked against `e89201a`, the commit that introduced this file: it matched twice there too.
It was born broken, and nothing said so because nothing ran it.

The count is now the point rather than an obstacle: a mutation is applied to EVERY occurrence
and the number replaced is recorded. Breaking one of two branches is not breaking the invariant
-- the other branch still defends it, and a "caught" verdict would be about half the engine.
`test_invariant_confirmation_anchors.py` pins the anchors so they cannot rot again in silence.

HOW IT RUNS, and the two hazards it is built around:

  - PYTHONDONTWRITEBYTECODE=1 and __pycache__ cleared around every arm. A byte-length-
    preserving mutation restored inside one mtime second otherwise leaves the MUTANT
    executing from a .pyc that still validates -- measured in this repo (#240).
  - --failfast. A caught mutation exits at its first failure instead of paying ~1200s.
    A SURVIVOR still costs a full run, which is correct: proving nothing catches it
    requires running everything.

Restores the source in a finally-block, and verifies `git diff` is clean before reporting, so
a crashed arm cannot leave a mutant in the tree.

Run:  PYTHONPATH=. python3 invariant_confirmation.py
"""
import ast
import json
import pathlib
import shutil
import subprocess
import sys

import store_io
import time

# (name, file, anchor, replacement, what breaking it would mean)
#
# ANCHORS AND REPLACEMENTS ARE WRITTEN UNINDENTED, and applied LINE-WISE at each site's own
# indentation. The two sites differ: compute_draft_board's upside-mode branch sits inside an
# `if`, four spaces deeper than the balanced branch. A replacement carrying its own hard-coded
# indent lands a statement at the wrong block level at one of them -- at best an IndentationError,
# at worst a mutation that silently applies OUTSIDE the branch it was written for.
# `{indent}` is substituted with the matched line's own leading whitespace.
MUTATIONS = [
    ("feasibility_first never binds", "draft_room.py",
     'scored["fills_required_slot"] = scored["_feasible"] == 0',
     'scored["fills_required_slot"] = scored["_feasible"] == 0\n{indent}scored["_feasible"] = 1',
     "a chair could finish unable to field a legal lineup and nothing would say so"),

    ("board order ignores feasibility", "draft_room.py",
     'results = scored.sort_values(["_feasible", "final_score", "player_id"],',
     'results = scored.sort_values(["final_score", "player_id"],',
     "feasibility becomes advisory -- the #154 backstop stops reaching the pick"),
]


#: Verdicts that are facts about THE HARNESS rather than about the suite. A run containing any
#: of them confirms nothing, and must not exit 0 -- silently passing on them is how `#254`'s two
#: useless verdicts came to be believed on this harness's first execution.
INCONCLUSIVE = frozenset({
    "ANCHOR FAILED",                 # the source moved; the mutation never applied
    "MUTANT DOES NOT PARSE",         # syntactically broken; every test fails for the wrong reason
    "MUTANT CANNOT BUILD A BOARD",   # runs as Python, raises before a board exists
    "MUTATION IS INERT",             # runs and changes nothing; there is nothing to catch
})

#: The two verdicts that ARE facts about the suite.
CONCLUSIVE = frozenset({"caught", "*** SURVIVED ***"})


def apply_mutation(source: str, anchor: str, replacement: str) -> tuple[str, int]:
    """Replace `anchor` at EVERY line that contains it, preserving that line's indentation.
    Returns the mutated source and the number of sites changed.

    Every occurrence, not the first: both anchors live in `compute_draft_board` twice, and a
    mutation that leaves one branch intact has not broken the invariant -- the other branch goes
    on defending it, and a "caught" verdict would be about half the engine.
    """
    out, sites = [], 0
    for line in source.splitlines(keepends=True):
        if anchor in line:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(line.replace(anchor, replacement.format(indent=indent)))
            sites += 1
        else:
            out.append(line)
    return "".join(out), sites


#: A board built under whatever source is currently on disk, reduced to one hash. Run in a
#: SUBPROCESS so the engine is imported fresh: this harness has already imported draft_room, and
#: a mutant written to disk after that import would otherwise be measured through the module
#: object already in memory (#240's stale-bytecode hazard, one layer up).
_FINGERPRINT_SCRIPT = """
import hashlib, json, sys
sys.path.insert(0, ".")
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
merger = dm.DataMerger()
players_db, _ = rdb.build_players_db_from_capture()
season = rdb.season_projections_from_capture()
league = dr.build_mock_league(teams=12, superflex=True, scoring="ppr", te_premium=False,
                              dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
league["draft_rounds"] = len(league["roster_positions"])
merger.set_league_format(db.league_format_hint(league))
board = dr.compute_draft_board(merger, players_db, [], my_roster_id="1", league=league,
                               sleeper_projections=season,
                               sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
print(hashlib.sha256(json.dumps(board, sort_keys=True, default=str).encode()).hexdigest())
"""


def _board_fingerprint() -> tuple[bool, str, str]:
    """(built_ok, sha256 of the board, stderr tail) for the source currently on disk.

    THE TWO THINGS A VERDICT REQUIRES, AND NEITHER WAS CHECKED BEFORE `#254`.

    1. THE MUTANT MUST RUN. `board order ignores feasibility` was scored "caught" on this:
       `ValueError: Length of ascending (3) != length of by (2)` -- the mutation dropped one
       entry from `sort_values`' `by` and left `ascending` at three, so pandas rejected its own
       arguments before a board existed and EVERY board-touching test errored. That is the
       mutant being unable to run, not the suite detecting anything. `ast.parse` above does not
       catch it: the mutant is valid Python whose defect is argument arity at runtime. A
       necessary guard, recorded as though it were sufficient.

    2. THE MUTATION MUST CHANGE SOMETHING. `feasibility_first never binds` was scored
       "SURVIVED" -- a full 1202.6s suite passed -- on a mutation that writes
       `scored["_feasible"] = 1` into a column measured to be uniformly 1 already: zero rows
       held 0 at any of 8 samples across a full 312-pick board. Sorting by a uniform column is
       a no-op with or without it. The suite did not fail to catch a change; there was no
       change. `#245`: identical numbers are a broken instrument until proven otherwise.

    Comparing whole boards rather than the targeted quantity is deliberate -- it needs no
    per-mutation knowledge, so a mutation added later inherits the guard instead of needing its
    own bespoke check (`#126`).
    """
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}
    proc = subprocess.run([sys.executable, "-c", _FINGERPRINT_SCRIPT],
                          capture_output=True, text=True, env=env)
    if proc.returncode != 0:
        return False, "", (proc.stdout + proc.stderr)[-800:]
    return True, proc.stdout.strip().splitlines()[-1], ""


def _run_suite(failfast=True):
    subprocess.run(["bash", "-c", "find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null"],
                   check=False)
    cmd = [sys.executable, "-m", "unittest", "discover", "-p", "test_*.py"]
    if failfast:
        cmd.append("--failfast")
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}
    t0 = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    subprocess.run(["bash", "-c", "find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null"],
                   check=False)
    return proc.returncode, round(time.time() - t0, 1), (proc.stdout + proc.stderr)[-4000:]


def main():
    results = []
    # The reference board, built ONCE from the unmutated tree. Every mutant is compared against
    # this; without it "the board changed" cannot be distinguished from "the board is what it
    # always was".
    ref_ok, ref_fp, ref_err = _board_fingerprint()
    if not ref_ok:
        print(f"REFERENCE BOARD FAILED TO BUILD -- the harness cannot run:\n{ref_err}")
        return 2
    print(f"reference board fingerprint: {ref_fp[:16]}\n")

    for name, filename, anchor, replacement, consequence in MUTATIONS:
        path = pathlib.Path(filename)
        original = path.read_text()
        # EVERY occurrence, not the first. Both anchors live in compute_draft_board twice --
        # the upside-mode branch and the balanced branch -- and a mutation that leaves one of
        # them intact has not broken the invariant, it has broken half the engine while the
        # other half goes on defending it.
        mutated, count = apply_mutation(original, anchor, replacement)
        if count < 1:
            results.append({"invariant": name, "verdict": "ANCHOR FAILED",
                            "detail": "anchor does not appear; the source moved under this harness"})
            print(f"{name}: ANCHOR FAILED (0 matches) -- the harness is broken, not the engine")
            continue
        # A MUTANT THAT DOES NOT COMPILE FAILS EVERY TEST, AND `rc != 0` WOULD CALL THAT
        # "caught". That is the harness reporting the invariant defended when nothing about the
        # invariant was exercised at all -- the worst outcome available to it. Parse first.
        try:
            ast.parse(mutated, filename=filename)
        except SyntaxError as exc:
            results.append({"invariant": name, "verdict": "MUTANT DOES NOT PARSE",
                            "detail": f"{exc}", "sites_mutated": count})
            print(f"{name}: MUTANT DOES NOT PARSE ({exc}) -- the harness is broken, not the engine")
            continue
        backup = path.with_suffix(path.suffix + ".confirm_backup")
        shutil.copy2(path, backup)
        try:
            path.write_text(mutated)
            # PREFLIGHT. A verdict is only a fact about the SUITE when the mutant runs and
            # changes the board; otherwise it is a fact about the harness. See
            # _board_fingerprint -- both failure modes are real and both were scored as
            # verdicts on this harness's first execution (#254).
            mut_ok, mut_fp, mut_err = _board_fingerprint()
            if not mut_ok:
                results.append({"invariant": name, "file": filename,
                                "verdict": "MUTANT CANNOT BUILD A BOARD", "sites_mutated": count,
                                "detail": mut_err})
                print(f"{name}: MUTANT CANNOT BUILD A BOARD -- no verdict; the harness is "
                      f"broken, not the engine")
                continue
            if mut_fp == ref_fp:
                results.append({"invariant": name, "file": filename,
                                "verdict": "MUTATION IS INERT", "sites_mutated": count,
                                "detail": "the mutated source produces a byte-identical board; "
                                          "the suite has nothing to catch and a SURVIVED "
                                          "verdict would say nothing about it"})
                print(f"{name}: MUTATION IS INERT (board unchanged) -- no verdict possible")
                continue
            rc, secs, tail = _run_suite(failfast=True)
            caught = rc != 0
            verdict = "caught" if caught else "*** SURVIVED ***"
            results.append({"invariant": name, "file": filename, "verdict": verdict,
                            "sites_mutated": count, "seconds": secs, "consequence": consequence,
                            "evidence": tail[-600:] if caught else "full suite passed"})
            print(f"{name}: {verdict}  ({secs}s, {count} site(s) mutated)")
            if not caught:
                print(f"    NOTHING DEFENDS THIS. Consequence: {consequence}")
        finally:
            shutil.copy2(backup, path)
            backup.unlink()
            subprocess.run(["bash", "-c",
                            "find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null"],
                           check=False)

    dirty = subprocess.run(["git", "diff", "--name-only", "--"] + sorted({m[1] for m in MUTATIONS}),
                           capture_output=True, text=True).stdout.strip()
    print(f"\nsources restored cleanly: {'NO -- ' + dirty if dirty else 'yes'}")
    # store_io, not write_text: test_store_io's ratchet caught this file writing a JSON store
    # directly, which is exactly what that guard exists to stop. Atomic replace and the
    # do-not-overwrite-damage rule apply to a harness artifact the same as to any other store.
    out = pathlib.Path("evidence/invariant_confirmation.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    store_io.write(out, {"results": results, "sources_dirty_after": dirty})
    print(f"-> {out}")
    # A run containing any non-verdict is not a clean run. SURVIVED means the suite failed to
    # defend something; the three harness-broken states mean the harness proved nothing at all,
    # and silently exiting 0 on them is how #254's two useless verdicts were first believed.
    if any(r["verdict"] in INCONCLUSIVE for r in results):
        print("\nAT LEAST ONE MUTATION PRODUCED NO VERDICT -- this run does not confirm anything")
        return 2
    return 1 if any(r["verdict"].startswith("***") for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
