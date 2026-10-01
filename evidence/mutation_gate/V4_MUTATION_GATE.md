# V4 mutation gate — `invariant_confirmation.py`

**Status:** complete. The gate passed. Baseline green on the clean tree and all five mutation
arms caught, with no arm reporting an inconclusive state. Every number below is measured;
none is an estimate.

- **Commit under test:** `7984b1d`
- **Branch:** `claude/v4-verify-mutation`
- **Harness:** `PYTHONPATH=. python3 invariant_confirmation.py`, run from the repository root
- **Scored modules:** 229 (`test_*.py` discovered, minus `test_invariant_confirmation_anchors`)
- **Raw log:** `V4_MUTATION_GATE_raw.log`, beside this file

## Verdict table

| # | invariant | branch | verdict | sites mutated | runtime |
|---|---|---|---|---|---|
| 0 | *baseline — no mutation, clean tree* | — | **green** | — | **1718.8s** |
| 1 | `feasibility_first never binds` | both | **caught** | 2 | 557.8s |
| 2 | `board order ignores feasibility` | balanced | **caught** | 1 | 579.6s |
| 3 | `board order ignores fieldability` | balanced | **caught** | 1 | 571.7s |
| 4 | `upside board order ignores feasibility` | upside | **caught** | 1 | 557.1s |
| 5 | `upside board order ignores fieldability` | upside | **caught** | 1 | 563.8s |

No arm reported `MUTATION IS INERT`, `ANCHOR FAILED`, `MUTANT DOES NOT PARSE` or
`MUTANT CANNOT BUILD A BOARD`. No arm survived.

### The baseline, stated plainly

**The baseline arm was GREEN in 1718.8s**, running all 229 scored modules on the unmutated tree
with `--failfast`. This is what makes the five "caught" verdicts mean anything: a caught verdict
is only `rc != 0` with a mutant in the tree, which says nothing unless the identical run is green
without one. It was.

### Site counts are correct, not suspicious

Arm 1 mutated **2** sites and arms 2–5 mutated **1** each. That is the expected post-D5 shape,
not a half-mutated engine. The `fills_required_slot` anchor is still shared by both branches of
`compute_draft_board`, so arm 1 hits both. D5 gave the upside branch a `projected_points`
tie-break, so the two board sorts no longer share a line and each carries its own anchor:
`draft_room.py:4743` (upside, 5 keys) and `draft_room.py:5006` (balanced, 4 keys). Arms 2 and 3
target the balanced site, arms 4 and 5 the upside site; one site each is complete coverage of
that site. `test_invariant_confirmation_anchors` asserts that every board sort in the function is
anchored by some mutation, and it passed.

## The two upside arms are no longer inert

This was the most important thing this run could establish, so it is stated separately.

Arms 4 and 5 mutate the upside branch. Until recently the harness fixture built the balanced
board only, so both arms produced a byte-identical board, both read `MUTATION IS INERT`, `main`
returned 2, and **the gate could not have passed.** Both arms now carry a real verdict:

- The harness runs a mutant's suite only after its preflight confirms the mutant builds a board
  **and** that board differs from the reference. Arms 4 and 5 each ran a full suite, so each had
  already cleared that gate.
- Both came back **caught**, in 557.1s and 563.8s.

The upside branch's feasibility and fieldability backstops are therefore defended by the suite as
it stands, on the branch that `#154` tier 3 called the one where it matters most because upside
scoring zeroes every roster-aware term.

## Preflight

The harness's own printed line, verbatim:

```
reference board: 427c40010c69c32c  feasibility binds on 619 of 964 rows, fieldability on 131
```

That line reports **one branch only**. The four-quantity guard above it loops over both branches
and checks all four correctly, but the `print` that follows reads `_digest`, `feas`, `total` and
`unfield` *after* the loop has ended, so it displays whichever branch iterated last — the upside
one. A reporting defect in the harness, not a verdict-affecting one: the guard did check all four
quantities and all four passed. It is recorded because the printed line is the artifact a reader
would otherwise quote as "the preflight", and on its face it looks like a single-branch check.

Measured per branch directly, via `invariant_confirmation._board_fingerprint()` on the clean tree:

| branch | board digest | feasibility (`fills_required_slot`) | fieldability (`cannot_be_fielded`) | board rows |
|---|---|---|---|---|
| balanced | `217c138c6b0e5d3704b635b435f44d913fb5edeb70c9088551a585e0ddb90dc2` | 619 | 131 | 964 |
| upside | `427c40010c69c32c7ca9c35dc8b5a07c6dc43554251c7432c153a5a6d0d9d423` | 619 | 131 | 964 |

All four censuses are strictly between 0 and 964, so both backstops bind on both branches and
no mutation of either is inert by construction. The two branch digests **differ**, which is the
precondition arms 4 and 5 need. `FIXTURE NO LONGER BINDS` did not fire, and the check was not
relaxed. The same digest and the same four censuses were produced on both runs below, so the
fixture is deterministic.

## Anchor coverage

`test_invariant_confirmation_anchors`: **passes on the clean tree** — 74.0s on run 1, 64.7s on
run 2. It is excluded from the scored mutant runs by construction, because it reads
`draft_room.py` from disk and counts the anchor text a mutation necessarily replaces.

## Wall time

| | |
|---|---|
| run 2 (the scored run) | **4700s** (1h18m), process start to exit |
| &nbsp;&nbsp;of which baseline | 1718.8s |
| &nbsp;&nbsp;of which the five arms | 2830.0s summed |
| &nbsp;&nbsp;of which anchors self-test | 64.7s |
| &nbsp;&nbsp;remainder | 86.5s — six reference/mutant board fingerprint builds and `__pycache__` clearing |
| run 1 (aborted, see below) | anchors 74.0s + baseline 711.6s; exited 2 without applying a mutation |

## Tree integrity after the run

```
$ git status --short
 M evidence/invariant_confirmation.json
$ git diff --quiet draft_room.py && echo IDENTICAL
IDENTICAL
```

`draft_room.py` is byte-identical to `HEAD`. The harness's own check agrees —
`sources restored cleanly: yes`, and `sources_dirty_after` is the empty string in
`evidence/invariant_confirmation.json`. **No mutant was left in the tree.** The only modified
file is `evidence/invariant_confirmation.json`, which is the harness's own output artifact,
written through `store_io` as its last act.

---

# Findings about the run, not about the engine

The gate passed. These three items are operational findings worth recording; none of them
changes a verdict above, and none was worked around by weakening a check.

## 1. The container could not have run this harness as it shipped

This container arrived with **no Python dependencies installed at all**. `import pandas` failed,
so `DataMerger` could not be imported and the reference board could not be built: the harness
would have exited 2 at `REFERENCE BOARD FAILED TO BUILD` without applying a single mutation.

Installed the full `requirements.txt` first. That file carries a warning worth honouring: without
`playwright` the board-execution tests **skip** rather than fail, and a reclaimed container once
ran the suite 14 tests lighter and still reported OK. So the browser was verified reachable
**under the harness's own deliberately stripped subprocess environment** (`PATH=/usr/bin:/bin`,
no `PLAYWRIGHT_BROWSERS_PATH`, no `HOME`):

```
CHROME = /opt/pw-browsers/chromium-1194/chrome-linux/chrome
HAVE_PLAYWRIGHT = True
has_browser = True
```

`test_216_room_integrity._find_chrome()` globs `/opt/pw-browsers/chromium-*` directly rather than
reading the environment variable, so stripping the environment does not cost those tests. They ran.

## 2. Run 1 aborted at the baseline, and the cause was mine

Run 1's baseline came back red after 711.6s:

```
SUITE IS ALREADY RED ON THE CLEAN TREE (711.6s) -- every mutation would score 'caught' on a
failure that has nothing to do with it. Fix the tree first; no mutation is applied.

FAIL: test_doc_index_is_not_stale (test_doc_index.TheIndexMatchesTheTree.test_doc_index_is_not_stale)
AssertionError: 1 != 0 : DOC_INDEX.md is stale -- run `python3 doc_index.py`

Ran 1407 tests in 707.859s
FAILED (failures=1)
```

The harness behaved correctly: it refused to apply any mutation and exited 2. No arm ran.

**Why it was my fault.** `doc_index.py` derives the document set from `git ls-files -z "*.md"`, so
a markdown file is a document of this repository exactly when git tracks it. I committed this
report mid-run; a new tracked `.md` appeared while the baseline was still executing, and
`DOC_INDEX.md` stopped matching the tree.

Verified rather than assumed, in a detached worktree at pristine `7984b1d` without this report:

```
$ git ls-files -z "*.md" | tr '\0' '\n' | grep -c .
235
$ python3 doc_index.py --check
DOC_INDEX.md current
exit=0
```

`DOC_INDEX.md` was **current** at the commit under test. The staleness lived only in my working
tree. The repository was not at fault and `test_doc_index` was right.

**The lesson generalises past the hazard the harness names.** Its docstring warns against
automation that commits whatever is on disk, because the tree holds a broken engine for minutes at
a time. There is a second face it does not name: a commit that is *safe for the engine* can still
be *unsafe for the suite*, because this repository has tests that assert over the **set of tracked
files**. Committing evidence into the tree under test is a perturbation of the thing being
measured. Explicit paths protect `draft_room.py`; they do not protect `DOC_INDEX.md`.

**What was changed.** `DOC_INDEX.md` was regenerated with `python3 doc_index.py`, the documented
procedure — `doc_index.py`'s own comments anticipate this case: *"a brand-new document is INVISIBLE
HERE UNTIL IT IS STAGED … Regenerate AFTER `git add`, not before."* No test, guard, threshold or
engine source was touched.

One further detail, because it would have recurred: this report first classified as `SUPERSEDED`
rather than `DECLARED`, because its header quoted the commit subject of `7984b1d`, which contains
a word that is a SUPERSEDED stem in `doc_index.CLASSES`. A live gate report filed as SUPERSEDED
misleads precisely the cold reader the index exists for, and the bucket would have flipped on any
later header edit, re-breaking the index mid-run. The header now carries a `**Status:**` line and
no stem of that vocabulary, so the classification is `DECLARED` and stable against edits to the
body below it.

## 3. The auto-commit hazard is live, not historical

`invariant_confirmation.py`'s docstring records that an auto-commit prompt once fired mid-arm with
the `_nofield=0` mutant on disk. **It happened again during this run**, by a different mechanism.

A Stop hook (`~/.claude/stop-hook-git-check.sh`) fired repeatedly throughout run 2 — roughly once
per turn across all five arms — reporting uncommitted changes and asking for them to be committed
and pushed. On each firing the only uncommitted change was the live mutant. It was declined every
time, and the diff was re-read on each firing rather than assumed, which is also how a failure of
the harness's `finally` block to restore between arms would have been caught. The mutants it would
have captured, had it been obeyed:

| arm | what a commit would have shipped |
|---|---|
| 1 | `scored["_feasible"] = 1` at both sites — feasibility backstop unconditionally disabled |
| 2 | balanced sort on constant `_nofeas=1` — the `#154` backstop never reaches the pick |
| 3 | balanced sort on constant `_nofield=0` — the nine-defense roster, the exact mutant the docstring names |
| 4 | upside sort on constant `_nofeas=1` |
| 5 | upside sort on constant `_nofield=0` |

The written warning is load-bearing and it is **not sufficient**: the hook fires regardless of what
the docstring says, and it asks for exactly the action that would ship a broken engine. Anyone
running this harness in an environment with a commit-enforcing hook or agent should expect the
prompt and must refuse it for the duration of the run. The harness's own `finally` block plus its
`sources restored cleanly` check are what actually held here.

## What a reader should conclude

The five invariants the gate covers are defended by the suite as it stands, at `7984b1d`:
feasibility_first's binding, and the feasibility and fieldability ordering backstops on **both**
branches of `compute_draft_board`. For the first time in this harness's life, that statement
includes the upside branch rather than silently excluding it.

The gate's own stated limits are unchanged and worth repeating, because a passing gate invites
over-reading: `narrow_candidates`' best-remaining-at-every-position guarantee and the absence
contract (unpriced carries `None`, never `0.0`) have **no mutation in this harness**. They are
named in its docstring as not built, and this run says nothing about either.
