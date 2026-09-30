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

AND ON 2026-09-30 THE PREFLIGHT WAS EXECUTED FOR EVERY ARM FOR THE FIRST TIME. Three arms cleared
it; the two upside arms read MUTATION IS INERT, because this file's fixture built the default
board only and they mutate the upside branch. `MUTATION IS INERT` is in `INCONCLUSIVE`, so `main`
would have returned 2 and the run would have confirmed nothing -- the harness unable to reach a
verdict, again, for the third distinct reason in its life, and again in work that was reasoned
about but never run. The fixture now builds both branches. The lesson is not about upside mode:
it is that reading this harness cannot establish that it works, and only the four preflight
states can.

HOW IT RUNS, and the two hazards it is built around:

  - PYTHONDONTWRITEBYTECODE=1 and __pycache__ cleared around every arm. A byte-length-
    preserving mutation restored inside one mtime second otherwise leaves the MUTANT
    executing from a .pyc that still validates -- measured in this repo (#240).
  - --failfast. A caught mutation exits at its first failure instead of paying ~1200s.
    A SURVIVOR still costs a full run, which is correct: proving nothing catches it
    requires running everything.

Restores the source in a finally-block, and verifies `git diff` is clean before reporting, so
a crashed arm cannot leave a mutant in the tree.

DO NOT RUN THIS WITH ANY AUTOMATION THAT COMMITS WHATEVER IS ON DISK. For minutes at a time this
harness deliberately holds a BROKEN ENGINE in the working tree -- `git status` shows draft_room.py
modified and `git diff` shows the backstop disabled. A hook or agent that stages everything and
commits will eventually capture one, and the result is a plausible-looking commit that ships a
board with no fieldability backstop: the nine-defense roster, pushed. This happened in the session
that added the baseline arm below -- an auto-commit prompt fired mid-arm with the
`_nofield=0` mutant on disk. Commit with explicit paths while this runs, or do not commit at all.

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

    # ARITY-PRESERVING BY CONSTRUCTION. The first version of this dropped "_feasible" from `by`
    # and left `ascending` at three entries, so pandas raised before a board existed and every
    # board-touching test errored -- scored "caught" while testing nothing (#254). Substituting a
    # CONSTANT column keeps three keys and three directions, changes nothing but whether
    # feasibility participates in the ordering, and leaves final_score's own direction alone.
    ("board order ignores feasibility", "draft_room.py",
     'results = scored.sort_values(["_feasible", "_unfieldable", "final_score", "player_id"],',
     'results = scored.assign(_nofeas=1).sort_values('
     '["_nofeas", "_unfieldable", "final_score", "player_id"],',
     "feasibility becomes advisory -- the #154 backstop stops reaching the pick"),
    # The SECOND backstop, mutated the same arity-preserving way and for the same reason: a
    # constant column keeps four keys against four directions, so the mutant runs and the only
    # thing that changes is whether fieldability participates in the ordering. 0, not 1, so the
    # substituted column reads as "nothing is demoted" rather than "everything is".
    ("board order ignores fieldability", "draft_room.py",
     'results = scored.sort_values(["_feasible", "_unfieldable", "final_score", "player_id"],',
     'results = scored.assign(_nofield=0).sort_values('
     '["_feasible", "_nofield", "final_score", "player_id"],',
     "the #30 fieldability backstop becomes advisory -- a roster resumes hoarding a position "
     "it cannot field, which is the nine-defense roster"),

    # THE TWO BRANCHES STOPPED SHARING ONE SORT LINE AT D5, so they stopped sharing one anchor.
    #
    # The two entries above used to match TWICE each -- once per branch of compute_draft_board --
    # which is the fact this file's docstring and test_invariant_confirmation_anchors were built
    # around. D5 gave the upside branch a `projected_points` tie-break, so its sort now carries
    # five keys against the balanced branch's four and the shared anchor matches only the balanced
    # site. Left there, the harness would have gone on reporting `caught` while mutating HALF the
    # engine -- the #254 failure mode, and precisely what `test_each_mutation_changes_every_site`
    # exists to refuse.
    #
    # RE-DERIVED FROM THE SOURCE rather than by editing the expected count to match: each branch
    # now carries its own anchor, and the coverage test asks whether every board-sort SITE is
    # anchored instead of whether one string appears twice. Both replacements stay
    # arity-preserving by the same construction as the four-key pair above -- five keys against
    # five directions, one of them a constant column -- so the mutant runs and the only thing that
    # changes is whether that backstop participates in the ordering.
    #
    # The upside sort is written on ONE LINE for the same reason every anchor here is: this file's
    # `apply_mutation` replaces per line, to preserve each site's indentation. A sort wrapped across
    # two lines cannot be anchored at all, so the harness would silently skip it -- which is how
    # this pair came to be needed rather than merely tidy.
    ("upside board order ignores feasibility", "draft_room.py",
     'results = scored.sort_values(["_feasible", "_unfieldable", "final_score", '
     '"projected_points", "player_id"],',
     'results = scored.assign(_nofeas=1).sort_values(["_nofeas", "_unfieldable", "final_score", '
     '"projected_points", "player_id"],',
     "feasibility becomes advisory in upside mode -- the branch #154 tier 3 called the one where "
     "it matters most, because upside scoring zeroes every roster-aware term"),

    ("upside board order ignores fieldability", "draft_room.py",
     'results = scored.sort_values(["_feasible", "_unfieldable", "final_score", '
     '"projected_points", "player_id"],',
     'results = scored.assign(_nofield=0).sort_values(["_feasible", "_nofield", "final_score", '
     '"projected_points", "player_id"],',
     "the fieldability backstop becomes advisory in upside mode -- the nine-defense roster, on "
     "the branch that has no other roster awareness to fall back on"),
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
# A SHORT draft with NO SLACK: rounds == startable slots. feasibility_first binds when
# `picks_remaining <= unfilled`, which is a property of a ROSTER STATE, not of a league -- so
# the fixture starves one.
ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX"]
league = {"roster_positions": ROSTER, "total_rosters": 12, "settings": {"type": 2},
          "scoring_settings": rdb.scoring_settings_from_capture(), "draft_rounds": len(ROSTER)}
merger.set_league_format(db.league_format_hint(league))
pool = dr.build_available_pool(merger, players_db, set(), dr.league_usable_positions(ROSTER),
                               sleeper_projections=season,
                               scoring_settings=league["scoring_settings"],
                               pool_scope="all", sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
dr._derive_points_and_source(pool)
# THREE QUARTERBACKS AND THREE RUNNING BACKS, six of seven picks spent. Both halves matter and
# the previous fixture had only one:
#   feasibility   six picks spent against seven slots leaves fewer picks than unfilled named
#                 slots, so feasibility_first binds and the board reorders around it.
#   fieldability  RB IS FLEX-REACHABLE AND THEREFORE EXEMPT FROM ANY CEILING, so the old
#                 six-RB fixture left `_unfieldable` uniformly 0 -- and the third mutation,
#                 which substitutes a constant 0 for that column, produced a BYTE-IDENTICAL
#                 board and could only ever read MUTATION IS INERT. It had no verdict for that
#                 reason, not because the run was cut short. QB is dedicated here (one slot, no
#                 SUPER_FLEX), so `fieldable_ceiling` is {'QB': 2} and holding three puts every
#                 remaining QB over it.
qbs = [str(x) for x in pool.loc[pool["position"] == "QB", "player_id"].head(3)]
rbs = [str(x) for x in pool.loc[pool["position"] == "RB", "player_id"].head(3)]
picks = [{"pick_no": i + 1, "round": i + 1, "roster_id": "1", "player_id": pid}
         for i, pid in enumerate(qbs + rbs)]
left = pool[~pool["player_id"].astype(str).isin({p["player_id"] for p in picks})].copy()
# BOTH BRANCHES OF compute_draft_board, because since D5 each has its OWN board sort and
# therefore its own anchor. This fixture built the default board only, so the two upside arms
# mutated a branch it never entered: the mutant's board came back byte-identical and both arms
# read MUTATION IS INERT -- which is in INCONCLUSIVE, so `main` returned 2 and the harness could
# reach no verdict at all. MEASURED 2026-09-30, on arms added by the same hand six days earlier
# and never executed. The upside branch is forced rather than reached by round, because
# `mode="auto"` picks it off `current_round >= upside_round` (15) and this fixture is a
# seven-round draft by construction -- it must stay short for feasibility_first to bind.
fields = []
for mode in ("auto", "upside"):
    board = dr.compute_draft_board(merger, players_db, picks, my_roster_id="1", league=league,
                                   mode=mode, sleeper_projections=season,
                                   sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    digest = hashlib.sha256(json.dumps(board, sort_keys=True, default=str).encode()).hexdigest()
    # BOTH CENSUSES, read off the board's own emitted flags rather than recomputed, and now per
    # branch. `main` refuses to judge any mutation unless all four are non-uniform: a uniform
    # column makes its mutation inert and a verdict about it meaningless, which is how the
    # third mutation went unjudged and then how both upside arms did.
    feas = sum(1 for row in board if row.get("fills_required_slot"))
    unfield = sum(1 for row in board if row.get("cannot_be_fielded"))
    fields.append(f"{digest} {feas} {len(board)} {unfield}")
print(" ".join(fields))
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


#: The harness's own self-test. Excluded from every scored run, because it reads draft_room.py
#: from disk and counts the anchor text that a mutation necessarily replaces -- so it fails under
#: EVERY mutant regardless of the engine, and `rc != 0` then reads as "caught". That is not a
#: hypothesis: both verdicts in this harness's first committed evidence were this module failing,
#: one on `assertEqual(0, 2)` over a mutated anchor. It runs on the CLEAN tree in `main` instead,
#: as a precondition, so nothing is untested -- the coverage moved, it did not disappear.
ANCHORS_MODULE = "test_invariant_confirmation_anchors"
EXCLUDED_FROM_MUTANT_RUN = frozenset({ANCHORS_MODULE})


def _discovered_modules() -> list[str]:
    """Every `test_*.py` in the tree as a module name, minus EXCLUDED_FROM_MUTANT_RUN.

    An EXPLICIT LIST rather than a skip inside the module. `unittest discover` has no exclusion
    flag, and the alternative -- having the anchors module skip itself when a mutant is on disk --
    would be a test that silently stops running, which is the defect `0.4` is about. Naming the
    modules on the command line keeps the exclusion visible in this file and in the run's own
    output, where a reader can see what was and was not scored.
    """
    names = sorted(q.stem for q in pathlib.Path(".").glob("test_*.py"))
    return [n for n in names if n not in EXCLUDED_FROM_MUTANT_RUN]


def _run_module(module: str):
    """One test module, for the clean-tree precondition. Same env discipline as `_run_suite`."""
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}
    subprocess.run(["bash", "-c", "find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null"],
                   check=False)
    t0 = time.time()
    proc = subprocess.run([sys.executable, "-m", "unittest", module],
                          capture_output=True, text=True, env=env)
    return proc.returncode, round(time.time() - t0, 1), (proc.stdout + proc.stderr)


def _run_suite(failfast=True):
    subprocess.run(["bash", "-c", "find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null"],
                   check=False)
    cmd = [sys.executable, "-m", "unittest"] + _discovered_modules()
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
    # THE FIXTURE MUST ACTUALLY EXERCISE THE INVARIANT. The fingerprint line carries the
    # feasibility census; if it is uniform, feasibility_first is a no-op on this board and every
    # mutation of it would read INERT forever -- the harness passing itself while testing
    # nothing, one level up from #254. Fail loudly rather than drift back into that.
    # BOTH BACKSTOPS ON BOTH BRANCHES. The guard checked feasibility alone once, so the
    # fieldability mutation sat behind an unchecked assumption: its column was uniformly 0 on the
    # fixture, the mutation substituting a constant 0 was therefore a no-op, and the arm could
    # only ever read MUTATION IS INERT. Widening it to both backstops left the SAME hole one axis
    # over -- both censuses were checked on the default board while two arms mutated the upside
    # branch -- so it is now four quantities, one pair per branch. A guard that covers three of
    # four gives false confidence about the fourth, which is the shape of every defect this file
    # exists for.
    parts = ref_fp.split()
    boards = [parts[i:i + 4] for i in range(0, len(parts), 4)]
    for branch, (_digest, feas, total, unfield) in zip(("balanced", "upside"), boards):
        for label, count in (("feasibility (fills_required_slot)", feas),
                             ("fieldability (cannot_be_fielded)", unfield)):
            if not 0 < int(count) < int(total):
                print(f"FIXTURE NO LONGER BINDS: on the {branch} board, {label} is uniform at "
                      f"{count} of {total} rows. That backstop is a no-op there, so no mutation "
                      f"of it can be judged. Re-derive the roster state; do not relax this check.")
                return 2
    print(f"reference board: {_digest[:16]}  feasibility binds on {feas} of {total} rows, "
          f"fieldability on {unfield}\n")

    # THE HARNESS'S OWN SELF-TEST RUNS HERE, ON THE CLEAN TREE, AND NOWHERE ELSE.
    # `test_invariant_confirmation_anchors.py` reads draft_room.py FROM DISK and counts anchor
    # text. A mutation REPLACES that text, so under any mutant the module fails by construction --
    # `assertEqual(0, 2)` on the anchor count. Both "caught" verdicts in the first committed
    # evidence were exactly that: the harness's self-test failing on its own missing anchor,
    # scored as the suite defending the engine. The module is excluded from the scored runs below
    # (see EXCLUDED_FROM_MUTANT_RUN) and its coverage is not lost but RELOCATED to here, where a
    # failure means the harness is broken and refuses to report anything.
    anchors_rc, anchors_secs, anchors_tail = _run_module(ANCHORS_MODULE)
    if anchors_rc != 0:
        print(f"{ANCHORS_MODULE} FAILS ON THE CLEAN TREE -- the harness is broken, not the "
              f"engine. No mutation is applied.\n{anchors_tail[-1500:]}")
        return 2
    print(f"{ANCHORS_MODULE}: passes on the clean tree ({anchors_secs}s)")

    # THE BASELINE ARM. A "caught" verdict means `rc != 0` WITH the mutant in the tree, which says
    # nothing whatever unless the same run is GREEN WITHOUT it. This harness had no baseline, and
    # the cost was immediate: the first run after the anchors module was excluded scored all three
    # mutations "caught" on a stale assertion floor -- a test method renamed in the same commit, so
    # `assertion_floors.drops()` was non-empty on the CLEAN tree and every arm inherited that one
    # failure under --failfast. Three verdicts, none about the engine, produced by a harness built
    # specifically to stop that happening. It happens once per run, not once per arm.
    print("baseline: running the scored modules on the clean tree "
          "(a verdict is meaningless unless this is green)...", flush=True)
    base_rc, base_secs, base_tail = _run_suite(failfast=True)
    if base_rc != 0:
        print(f"SUITE IS ALREADY RED ON THE CLEAN TREE ({base_secs}s) -- every mutation would "
              f"score 'caught' on a failure that has nothing to do with it. Fix the tree first; "
              f"no mutation is applied.\n{base_tail[-2000:]}")
        return 2
    print(f"baseline: green ({base_secs}s)\n")

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
