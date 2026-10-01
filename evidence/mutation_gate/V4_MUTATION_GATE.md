# V4 mutation gate — `invariant_confirmation.py`

**Status:** run in progress. This file is committed incrementally as each arm establishes a
result. Every number in it is measured, never estimated. The verdict table is incomplete
until this line says the run has finished.

- **Commit under test:** `7984b1d`
- **Branch:** `claude/v4-verify-mutation`
- **Harness:** `PYTHONPATH=. python3 invariant_confirmation.py`, run from the repository root
- **Scored modules:** 229
- **Raw log:** `V4_MUTATION_GATE_raw.log`, beside this file

## What this gate is

The harness mutates `draft_room.py` on disk one mutation at a time, runs the full suite against
each mutant, and restores the file in a `finally` block. A pass is: the baseline arm green on
the clean tree, and all five mutation arms reporting the mutation was CAUGHT. Any arm reading
`MUTATION IS INERT`, `INCONCLUSIVE`, `ANCHOR FAILED`, `MUTANT CANNOT BUILD A BOARD` or
`MUTANT DOES NOT PARSE` is a finding about the harness, not a pass.

## Container preparation — the harness could not have run as the container shipped

This container had **no Python dependencies installed at all**. `import pandas` failed, so
`DataMerger` could not be imported and the reference board could not be built: the harness
would have exited 2 at `REFERENCE BOARD FAILED TO BUILD` without applying a single mutation.

Installed the full `requirements.txt` before starting. That file carries a warning worth
honouring: without `playwright` the board-execution tests **skip** rather than fail, and a
reclaimed container once ran the suite 14 tests lighter and still reported OK. So the browser
was verified reachable **under the harness's own deliberately stripped subprocess environment**
(`PATH=/usr/bin:/bin`, no `PLAYWRIGHT_BROWSERS_PATH`, no `HOME`):

```
CHROME = /opt/pw-browsers/chromium-1194/chrome-linux/chrome
HAVE_PLAYWRIGHT = True
has_browser = True
```

`test_216_room_integrity._find_chrome()` globs `/opt/pw-browsers/chromium-*` directly rather
than reading the environment variable, so stripping the environment does not cost those tests.
They run.

## Preflight — `FIXTURE NO LONGER BINDS` did not fire

The harness's own printed line, verbatim:

```
reference board: 427c40010c69c32c  feasibility binds on 619 of 964 rows, fieldability on 131
```

That line reports **one branch only**. The four-quantity guard above it loops over both
branches and checks all four correctly, but the `print` that follows reads `_digest`, `feas`,
`total` and `unfield` *after* the loop has ended, so it displays whichever branch iterated
last — the upside one. This is a reporting defect in the harness, not a verdict-affecting one:
the guard itself did check all four quantities and all four passed. It is recorded because the
printed line is the artifact a reader would otherwise quote as "the preflight".

Measured per branch directly, via `invariant_confirmation._board_fingerprint()` on the clean
tree:

| branch | board digest | feasibility (`fills_required_slot`) | fieldability (`cannot_be_fielded`) | board rows |
|---|---|---|---|---|
| balanced | `217c138c6b0e5d3704b635b435f44d913fb5edeb70c9088551a585e0ddb90dc2` | 619 | 131 | 964 |
| upside | `427c40010c69c32c7ca9c35dc8b5a07c6dc43554251c7432c153a5a6d0d9d423` | 619 | 131 | 964 |

All four censuses are strictly between 0 and 964, so both backstops bind on both branches and
no mutation of either is inert by construction. **The two branch digests differ**, which is the
precondition the two upside arms need: the fixture genuinely enters the upside branch and
produces a different board there, so a mutation confined to that branch has something to
change. (Until recently the fixture built the balanced board only, both upside arms read
`MUTATION IS INERT` forever, and the gate could not have passed.)

## Anchor coverage

`test_invariant_confirmation_anchors`: **passes on the clean tree (74.0s)**.

The two board sorts it pins are both present and distinct, confirming the post-D5 split that
each arm pair targets:

- `draft_room.py:4743` — upside branch, 5 sort keys (`_feasible`, `_unfieldable`, `final_score`, `projected_points`, `player_id`)
- `draft_room.py:5006` — balanced branch, 4 sort keys (`_feasible`, `_unfieldable`, `final_score`, `player_id`)

## Run 1 — aborted at the baseline, by contamination I introduced

**Run 1 did not produce a verdict, and the cause was mine, not the repository's.**

The baseline arm came back red after 711.6s:

```
SUITE IS ALREADY RED ON THE CLEAN TREE (711.6s) -- every mutation would score 'caught' on a
failure that has nothing to do with it. Fix the tree first; no mutation is applied.

FAIL: test_doc_index_is_not_stale (test_doc_index.TheIndexMatchesTheTree.test_doc_index_is_not_stale)
AssertionError: 1 != 0 : DOC_INDEX.md is stale -- run `python3 doc_index.py`

Ran 1407 tests in 707.859s
FAILED (failures=1)
```

The harness behaved correctly: it refused to apply any mutation and exited 2. No arm ran.

**Why it was my fault.** `doc_index.py` derives the document set from
`git ls-files -z "*.md"` — a markdown file is a document of this repository exactly when git
tracks it. I committed this report mid-run, which made a new tracked `.md` appear while the
baseline suite was still executing, and `DOC_INDEX.md` no longer matched the tree.

Verified rather than assumed. A detached worktree at pristine `7984b1d`, without this report:

```
$ git ls-files -z "*.md" | tr '\0' '\n' | grep -c .
235
$ python3 doc_index.py --check
DOC_INDEX.md current
exit=0
```

So `DOC_INDEX.md` was **current** at the commit under test. The staleness existed only in my
working tree, and only because I added a tracked document to it while the suite was running.

**The lesson, which is a real one.** `invariant_confirmation.py`'s docstring warns against
automation that commits whatever is on disk, because the tree holds a broken engine for minutes
at a time. The hazard has a second face it does not name: a commit that is *safe for the engine*
can still be *unsafe for the suite*, because this repository has tests that assert over the set
of tracked files. Committing evidence into the tree under test is itself a perturbation of the
thing being measured. Explicit paths protect `draft_room.py`; they do not protect `DOC_INDEX.md`.

**What was changed, and what was not.** `DOC_INDEX.md` was regenerated with `python3
doc_index.py`, which is the repository's documented procedure — `doc_index.py`'s own comments
anticipate this exact case: *"a brand-new document is INVISIBLE HERE UNTIL IT IS STAGED …
Regenerate AFTER `git add`, not before."* No test, guard, threshold or engine source was
touched. The failing check was left exactly as it is; it was right, and it caught me.

One further detail, because it would have bitten the next run: this report first classified as
`SUPERSEDED` rather than `DECLARED`, because its header quoted the commit subject of `7984b1d`,
which contains a word that is a SUPERSEDED stem in `doc_index.CLASSES`. A live gate report filed
as SUPERSEDED misleads precisely the cold reader the index exists for, and the bucket would flip
on any later header edit, re-staleing the index mid-run. The header now carries a `**Status:**`
line and no stem of that vocabulary, so the classification is `DECLARED` and stable against edits
to the body below it.

## Baseline arm

| | |
|---|---|
| verdict | *pending — run 2* |
| runtime | *pending* |

## Verdict table

| # | invariant | branch | verdict | sites mutated | runtime |
|---|---|---|---|---|---|
| 0 | *baseline (clean tree)* | — | *pending* | — | *pending* |
| 1 | `feasibility_first never binds` | both | *pending* | | |
| 2 | `board order ignores feasibility` | balanced | *pending* | | |
| 3 | `board order ignores fieldability` | balanced | *pending* | | |
| 4 | `upside board order ignores feasibility` | upside | *pending* | | |
| 5 | `upside board order ignores fieldability` | upside | *pending* | | |

## Tree integrity after the run

*pending* — `git status --short` and `git diff --stat` are checked once the harness exits. The
harness restores `draft_room.py` in a `finally` block and prints its own
`sources restored cleanly:` line; both are reported.
