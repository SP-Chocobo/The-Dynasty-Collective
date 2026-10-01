# v4 mutation gate — re-run on the REPAIRED engine

**Status: COMPLETE. THE GATE PASSES.** Baseline green on the clean tree and all five arms
`caught`, on the repaired engine at `7e54821`. No arm read `MUTATION IS INERT`,
`ANCHOR FAILED`, `MUTANT CANNOT BUILD A BOARD`, `MUTANT DOES NOT PARSE` or `*** SURVIVED ***`.

Every number here was measured in this run and taken from this run's own stdout
(`v4_rerun_raw.log`, committed beside this file). Nothing is an estimate. This file was written
arm by arm as each verdict landed, not assembled at the end.

## Why this run exists

The gate last passed at `7984b1d` (commit `6860992`, "v4 mutation gate PASSES at 7984b1d:
baseline green, all five arms caught"). **Twelve repairs landed after that**, touching
`draft_room.py`, `pick_synthesis.py`, `pick_debate.py`, `sleeper_client.py`,
`league_config.py` and `invariant_registry.py` — among them the three repair commits
`d6d88ce`, `5eb9662` and `7e54821`. A gate verdict about source that has since been edited
is not evidence about the freeze. `draft_room.py` is the file this harness mutates, so a
verdict on the pre-repair copy of it says nothing about the tree being frozen.

## Commit under test

| | |
|---|---|
| Commit | `7e54821` |
| Subject | Repair seven more review findings; the battery's own evidence now reads 52, not 53 |
| Branch | `claude/v4-verify-mutation-rerun` |
| Tree at launch | clean (`git status --short` empty) |
| Harness | `PYTHONPATH=. python3 invariant_confirmation.py`, run from the repository root |

## Container preparation, and the two hazards that were actually present

Both of the environment hazards the owner flagged were real in this container and are
recorded here because a reader cannot otherwise tell whether the suite that produced the
verdicts below was the whole suite.

**1. No Python dependencies at all.** `import pandas` failed on a fresh container, so
`DataMerger` could not be imported and the harness would have exited at
`REFERENCE BOARD FAILED TO BUILD` without applying a single mutation. `pip install -r
requirements.txt` installed 30 packages (pandas 3.0.6, scipy 1.17.1, playwright 1.63.0,
streamlit 1.64.0, …) and exited 0.

**2. The browser was NOT reachable at first, under the harness's own stripped env.** The
harness runs every suite and fingerprint in a subprocess with
`env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ".", "PATH": "/usr/bin:/bin"}`
(`invariant_confirmation.py:286,319,334`) — note that `PLAYWRIGHT_BROWSERS_PATH` is **not**
passed through. A direct `p.chromium.launch()` under exactly that env fails:

```
playwright._impl._errors.Error: BrowserType.launch: Executable doesn't exist at
/root/.cache/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell
```

Two independent causes: the stripped env loses `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`,
**and** the pip-installed playwright 1.63.0 wants Chromium build **1243** while this
container provisioned build **1194**.

Neither one reaches the suite, and that was verified rather than assumed. Both board-execution
modules pass an explicit `executable_path` instead of letting playwright resolve its bundled
browser — `test_216_room_integrity._find_chrome()` globs
`/opt/pw-browsers/chromium-*/chrome-linux/chrome`, and `test_board_renders_absence` hard-codes
`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. That binary exists
(463 MB, `-rwxr-xr-x`). Run under the harness's exact stripped env:

```
$ env -i PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PATH=/usr/bin:/bin \
      python3 -m unittest test_board_renders_absence test_216_room_integrity -v
Ran 30 tests in 25.487s
OK
```

**30 tests ran and none skipped**, including
`test_python_and_the_browser_round_the_boundary_class_identically`, which can only pass by
actually driving Chromium. The board-execution tests are therefore LIVE in the runs scored
below — this is not the reclaimed-container case that once ran the suite 14 tests lighter and
still reported OK.

## Preflight — the fixture binds, and the upside arms can bind

Printed by the harness before any mutation was applied:

```
reference board: 427c40010c69c32c  feasibility binds on 619 of 964 rows, fieldability on 131
  branch digests: 9f5cc3af014e8e9a 427c40010c69c32c
```

| Quantity | Value |
|---|---|
| Reference board digest (sha256, first 16) | `427c40010c69c32c` |
| Balanced-branch digest | `9f5cc3af014e8e9a` |
| Upside-branch digest | `427c40010c69c32c` |
| Digests differ? | **YES** — no `<-- IDENTICAL, the upside arms cannot bind` warning |
| feasibility (`fills_required_slot`) | 619 of 964 rows |
| fieldability (`cannot_be_fielded`) | 131 of 964 rows |
| Balanced-branch census | feasibility 619 of 964 rows, fieldability 131 of 964 |
| Upside-branch census | feasibility 619 of 964 rows, fieldability 131 of 964 |

The harness prints only ONE census line, because `_digest`, `feas`, `total` and `unfield` leak
out of its `for branch in ("balanced", "upside")` loop and therefore hold the LAST iteration —
the upside board. The per-branch figures above were measured separately, after the run, by
calling the harness's own `_board_fingerprint()` on the restored clean tree (`git diff` on
`draft_room.py` empty, verified in the same breath) and splitting its four-field-per-branch
output. Raw line:

```
9f5cc3af014e8e9afdf7013d851213e65fc2f074c1c1a24066d0ea02fea5f6e9 619 964 131
427c40010c69c32c7ca9c35dc8b5a07c6dc43554251c7432c153a5a6d0d9d423 619 964 131
```

**The two censuses are identical and the two digests differ, and that is the correct result
rather than a surprise.** The harness's own comment says so: `feasibility_first` and
`unfieldable_last` never read `mode`, so each census is identical on both branches *by
construction*, and it is checked per branch anyway against the day a backstop does start
reading the mode. What the second board actually buys is the **digest** — and the digests
differ, which is the only reason arms 4 and 5 can bind at all.

**`FIXTURE NO LONGER BINDS` was NOT emitted.** That check was not relaxed, touched, or
inspected for leniency; it passed on its own terms. It is a four-way check — both censuses on
both branches must satisfy `0 < count < total` — and the harness returns 2 if any of the four
is uniform, so clearing it means all four are non-uniform.

**The digests differing is the load-bearing preflight fact for arms 4 and 5.** Those two arms
mutate the upside branch's own sort line, and they read `MUTATION IS INERT` for their entire
existence until this cycle because the fixture only ever built the balanced board — a mutation
of a branch the fixture never entered returns a byte-identical board, which is in
`INCONCLUSIVE`. Two distinct digests mean the upside branch is genuinely built here, so a
mutation of its sort can move the fingerprint and the arms can reach a real verdict.

## Anchor integrity — the thing most likely to have broken

`draft_room.py` was edited by the repairs, and this harness finds its mutation sites by
matching exact source text. Every anchor was checked against the repaired file **before**
launch, by calling the harness's own `apply_mutation`:

| Arm | Anchor sites matched |
|---|---|
| feasibility_first never binds | 2 |
| board order ignores feasibility | 1 |
| board order ignores fieldability | 1 |
| upside board order ignores feasibility | 1 |
| upside board order ignores fieldability | 1 |

No anchor matched 0 sites, so **no `ANCHOR FAILED` is expected and none was emitted**. The
repairs did not move any anchor text. Both board-sort sites in the file are covered — the
upside sort at `draft_room.py:4781` (five keys) and the balanced sort at `draft_room.py:5052`
(four keys) — and both `fills_required_slot` assignments (`:4749`, `:5044`) are hit by the
2-site arm. `test_invariant_confirmation_anchors` passing on the clean tree is a separate
precondition the harness enforces itself; its result is recorded below.

## Run 1 was ABORTED by the baseline arm, and I caused it

**`SUITE IS ALREADY RED ON THE CLEAN TREE (532.5s)`.** The harness refused to apply a single
mutation and returned 2. Recorded verbatim because it is one of the named findings — but it is
a finding about *this container's run protocol*, not about the engine, and the cause was mine.

The baseline failed on exactly ONE test out of 1421:

```
FAIL: test_doc_index (test_doc_index.TheIndexMatchesTheTree.test_doc_index_is_not_stale)
  File "/home/user/The-Dynasty-Collective/test_doc_index.py", line 21, in test_doc_index_is_not_stale
    self.assertEqual(doc_index.main(["--check"]), 0,
AssertionError: 1 != 0 : DOC_INDEX.md is stale -- run `python3 doc_index.py`

Ran 1421 tests in 528.739s
FAILED (failures=1)
```

`doc_index.py:103` builds the index from **git-tracked** markdown:
`TRACKED_DOCS = ["git", "ls-files", "-z", "*.md"]`. To honour "push often, as each arm reports",
I committed `evidence/mutation_gate/V4_MUTATION_GATE_RERUN.md` *while the baseline was running*.
That commit made the file git-tracked, which put it in the index's input set and made
`DOC_INDEX.md` stale under the suite's own staleness check.

The staleness was measured, not guessed. Regenerating the index and diffing against the
committed copy gives exactly three changes, all of them this one file:

```
< `python3 doc_index.py` regenerates this. 239 markdown documents.
> `python3 doc_index.py` regenerates this. 240 markdown documents.
< | DECLARED | 43 | says what kind of document it is before making claims. |
> | DECLARED | 44 | says what kind of document it is before making claims. |
>  - `evidence/mutation_gate/V4_MUTATION_GATE_RERUN.md`
```

Nothing in that diff touches the engine, `draft_room.py`, or any invariant. 1420 of 1421 tests
passed, with the 30 board-execution tests live.

### Why this is worth more than the 532.5s it cost

Had the same commit landed during a MUTANT arm instead of the baseline, the harness would have
seen `rc != 0` and scored that arm **`caught`** — on a stale generated index that has nothing to
do with the mutation. That is precisely the `#254` failure mode this harness exists to prevent,
and the mechanism it was built around: *"the first run after the anchors module was excluded
scored all three mutations 'caught' on a stale assertion floor ... Three verdicts, none about
the engine, produced by a harness built specifically to stop that happening."* A stale
`DOC_INDEX.md` is the same defect with a different generated file.

**The baseline arm is what caught it**, which is the baseline doing exactly the job its own
comment claims: *"a 'caught' verdict ... says nothing whatever unless the same run is GREEN
without it."* The harness was right to refuse, and the instruction to push often is — applied
naively to this harness — unsafe. The two are reconcilable, and the boundary was measured:

| Action on a tracked `.md` during a run | `doc_index.py --check` |
|---|---|
| **Adding** a new one (what I did) | rc=1 — **stale, poisons the run** |
| **Editing** one already tracked | rc=0 — current, safe |

So run 2 is launched with both evidence files already tracked and `DOC_INDEX.md` regenerated to
match. Verdicts are then written by *editing* those tracked files, which is safe, and no new
`.md` is added until the run is over. Push-often is preserved without putting a verdict at risk.

`python3 doc_index.py` was run to regenerate the index. That is the action the failing test
itself prescribes, it is routine hygiene in this repo (cf. `b0919f2`, "Regenerate DOC_INDEX
after merging the four review branches"), and it is disclosed here rather than folded in
silently. **No engine file, no test, no fixture and no part of the harness was altered.**

## Verdict table

| # | Invariant | Sites | Verdict | Runtime |
|---|---|---|---|---|
| — | `test_invariant_confirmation_anchors` (clean-tree precondition) | — | **passes** | 54.0s (run 2; 52.5s in run 1) |
| — | **baseline** (scored modules, clean tree) | — | **GREEN** | **1351.0s** |
| 1 | feasibility_first never binds | 2 | **caught** | 437.4s |
| 2 | board order ignores feasibility | 1 | **caught** | 440.6s |
| 3 | board order ignores fieldability | 1 | **caught** | 440.5s |
| 4 | upside board order ignores feasibility | 1 | **caught** | 438.9s |
| 5 | upside board order ignores fieldability | 1 | **caught** | 443.7s |

**Harness exit state:** `sources restored cleanly: yes`, and `evidence/invariant_confirmation.json`
records `sources_dirty_after: ""`. All five verdicts are in `CONCLUSIVE`, none in `INCONCLUSIVE`,
and none begins with `***`, so the harness returned **0**.

### Total wall time

| Component | Measured |
|---|---|
| Anchors self-test (clean tree) | 54.0s |
| Baseline (clean tree, green) | 1351.0s |
| Five mutation arms | 437.4 + 440.6 + 440.5 + 438.9 + 443.7 = 2201.1s |
| **Accounted by the harness's own timings** | **3606.1s** |
| **Total wall clock, run 2** | **3627–3683s (60.4–61.4 min)** |

The total is given as a bracket rather than a single figure because I did not timestamp the
launch to the second, and I will not state a precision I did not measure. The bounds are real:
the run ended at `08:11:35.9` (mtime of `v4_rerun_raw.log`), and it started after `07:10:13`
(the commit made once run 1 was confirmed stopped at 0 gate processes) and at or before
`07:11:09` (the keepalive heartbeat sample that already saw 3 gate processes). The ~21–77s
between the bracket and the 3606.1s accounted above is the six `_board_fingerprint()`
subprocesses — one reference board plus one preflight per arm — which the harness does not
time individually.

Run 1, aborted, cost a further 532.5s baseline plus its own 52.5s anchors run.

### Per-arm notes

Every arm was `caught`, so **no invariant is left undefended and there is no "what a reader
should conclude" paragraph to write for a surviving arm.** What each arm establishes:

1. **feasibility_first never binds** — `caught`, 2 sites. The only arm that mutates two sites,
   because `scored["fills_required_slot"] = scored["_feasible"] == 0` appears in both branches
   (`:4749`, `:5044`). Forcing `_feasible = 1` in both means the #164 blocker family's backstop
   can never bind anywhere. Mutating one site only would have broken half the engine while the
   other half went on defending the invariant, and `caught` would then have been a statement
   about half the engine. The live mutant was inspected on disk mid-arm and carried each site's
   own indentation — 8 spaces in the upside branch, 4 in the balanced one.
2. **board order ignores feasibility** — `caught`, balanced sort at `:5052`.
3. **board order ignores fieldability** — `caught`, balanced sort at `:5052`. This arm could
   once only ever read `MUTATION IS INERT`: the old fixture held six RBs, RB is flex-reachable
   and so exempt from any ceiling, `_unfieldable` was uniformly 0, and substituting a constant 0
   gave a byte-identical board. The current fixture holds three QBs against one dedicated QB
   slot, and fieldability was measured binding on 131 of 964 rows, so the column is genuinely
   non-uniform and this verdict is about the suite.
4. **upside board order ignores feasibility** — `caught`, upside sort at `:4781`.
5. **upside board order ignores fieldability** — `caught`, upside sort at `:4781`.

Arms 2–5 all substitute a **constant column** rather than dropping a sort key, keeping keys and
directions at equal length (four each on the balanced branch, five each on the upside branch).
That construction is why the mutants run at all: the first version of arm 2 dropped `_feasible`
from `by` and left `ascending` at three entries, so pandas raised before a board existed and
every board-touching test errored — scored `caught` while testing nothing (`#254`).

### Arms 4 and 5: the headline result

**These are the two arms that read `MUTATION IS INERT` for their entire existence until this
cycle, and they are not inert now. Both are `caught`.**

They mutate the upside branch's own sort line, and the fixture used to build the balanced board
only — so the mutant's board came back byte-identical, which is `MUTATION IS INERT`, which is in
`INCONCLUSIVE`, so `main` returned 2 and the harness reached no verdict at all. Three
independent measurements say that is over:

1. The preflight digests **differ** (`9f5cc3af014e8e9a` balanced, `427c40010c69c32c` upside), so
   the fixture genuinely builds the upside branch and a mutation of its sort moves the
   fingerprint. The harness prints no `<-- IDENTICAL, the upside arms cannot bind` warning.
2. Each arm's own preflight passed — neither `MUTANT CANNOT BUILD A BOARD` nor
   `MUTATION IS INERT` was emitted, so the mutant both ran and changed the board.
3. The live mutants were inspected on disk mid-arm. Arm 4 substituted `_nofeas=1` and arm 5
   `_nofield=0` at `:4781`, at the upside branch's own 8-space indentation, five keys against
   five directions.

So feasibility and fieldability are both defended on the upside branch — the branch `#154`
tier 3 calls the one where it matters most, because upside scoring zeroes every roster-aware
term and there is no other roster awareness to fall back on. Arm 5 in particular is the
nine-defense roster on that branch, and the suite refuses it.

### An operational hazard for whoever re-runs this

`~/.claude/stop-hook-git-check.sh` fired **five times** during this run, each time reporting
uncommitted changes and asking for them to be committed and pushed. On every occasion the sole
uncommitted change was `draft_room.py` holding the live mutant. It was declined every time, and
no commit in this branch contains a mutated `draft_room.py`.

That hook is precisely the automation `invariant_confirmation.py:69` warns against in capitals:
*"DO NOT RUN THIS WITH ANY AUTOMATION THAT COMMITS WHATEVER IS ON DISK ... the result is a
plausible-looking commit that ships a board with no fieldability backstop: the nine-defense
roster, pushed. This happened in the session that added the baseline arm below."* It has now
fired mid-arm in two separate sessions. Evidence was pushed throughout by staging **explicit
paths** (`git add evidence/mutation_gate/...`), never `-A` and never `draft_room.py`, which is
the discipline that file prescribes. `git diff --name-only -- draft_room.py` was checked
immediately before every single commit.

### The baseline, stated plainly

**The baseline arm was GREEN on the clean tree, in 1351.0s.** No mutation had been applied at
that point. This is the precondition every verdict below depends on: a `caught` verdict means
`rc != 0` with a mutant in the tree, which says nothing at all unless the same run is green
without one.

Baseline runtime is **not stable** in this container and that is worth recording against the
~1800s-per-suite budget: run 1's baseline ran all 1421 tests in 528.7s before failing its last
test, while run 2's green baseline took **1351.0s** — a 2.6x spread on the same tree and the
same module list. I did not establish the cause; the honest statement is that it was measured
twice and differed, so a single suite in this container should be budgeted at up to ~1400s
rather than the 528.7s run 1 might suggest. The harness prints no test count for a green
baseline (`main` reports only `base_secs` on success), so 1421 is the count measured in run 1,
not one re-read from run 2.

## Conclusion

**The v4 mutation gate PASSES on the repaired engine at `7e54821`.** Baseline green on the clean
tree in 1351.0s; all five arms `caught`; no inconclusive verdict; sources restored cleanly;
`draft_room.py` verified byte-identical to `HEAD` afterwards (sha256
`76e4e612979ff2d4701a25db740eed32cef51fe102d6c5112e2f773c8e7cbf36` for both the working file and
`git show HEAD:draft_room.py`).

What a reader should conclude, and the limits of it:

- The twelve repairs since `7984b1d` did **not** move any mutation anchor, did **not** break the
  harness's self-test, and did **not** leave the suite red. The previous gate verdict is no
  longer the one the freeze rests on — this one is, and it is about the source actually in the
  tree.
- The four load-bearing board-ordering invariants are defended on **both** branches of
  `compute_draft_board`, which this harness could not previously establish for the upside branch
  at all.
- This remains a gate over **two built targets** (`feasibility_first` and the board sorts), not
  four. `narrow_candidates` and the absence contract still have **no mutation here**; the
  harness's own docstring says so, and this run does not change it. A reader should not take
  "all five arms caught" as mutation coverage of the absence contract.
- `MUTATION IS INERT` is now absent from every arm, but that is a property of the current
  fixture, not a permanent one. It was the fixture that made arms 3, 4 and 5 unjudgeable in the
  past, and `FIXTURE NO LONGER BINDS` plus the differing-digest line are the only things
  standing between a future edit and a silently vacuous gate.

## What counts as a pass

Baseline GREEN on the clean tree, and all five arms `caught`. Every one of
`MUTATION IS INERT`, `INCONCLUSIVE`, `ANCHOR FAILED`, `MUTANT CANNOT BUILD A BOARD`,
`MUTANT DOES NOT PARSE`, `FIXTURE NO LONGER BINDS` and
`SUITE IS ALREADY RED ON THE CLEAN TREE` is a finding, not a pass. Harness exit code: 0 = all
caught, 1 = at least one SURVIVED, 2 = at least one arm reached no verdict.

## A trap worth naming: the stale `evidence/invariant_confirmation.json`

The harness writes `evidence/invariant_confirmation.json` only **after** its arm loop finishes
(`store_io.write` at the end of `main`). So for the entire duration of a run, the copy in the
tree is the **previous** run's. During this run it still held five `caught` rows with runtimes
557.8 / 579.6 / 571.7 / 557.1 / 563.8s — and `git log` confirms those were last written by
commit `6860992`, "v4 mutation gate PASSES at 7984b1d".

Those five rows are **not** results from this run and are not reported as such anywhere in this
document. Reading them as current would have reproduced exactly the error this whole re-run
exists to correct: a gate verdict about code that no longer exists. Every verdict in the table
above is taken from `v4_rerun_raw.log`, which is this run's own stdout, written as each arm
reports. The JSON is quoted only once this run has overwritten it.

Raw log: `evidence/mutation_gate/v4_rerun_raw.log` (committed beside this file).
