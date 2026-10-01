# v4 mutation gate — re-run on the REPAIRED engine

**Status: IN PROGRESS.** This file is written as each arm reports, not at the end, so a
container reclamation cannot take an established verdict with it. Any row below reading
`pending` has not been measured yet; no row is written from an estimate.

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
| Per-branch censuses | pending — measured on the restored clean tree after the run |

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

## Verdict table

| # | Invariant | Sites | Verdict | Runtime |
|---|---|---|---|---|
| — | `test_invariant_confirmation_anchors` (clean-tree precondition) | — | **passes** | 52.5s |
| — | **baseline** (scored modules, clean tree) | — | pending | pending |
| 1 | feasibility_first never binds | 2 | pending | pending |
| 2 | board order ignores feasibility | 1 | pending | pending |
| 3 | board order ignores fieldability | 1 | pending | pending |
| 4 | upside board order ignores feasibility | 1 | pending | pending |
| 5 | upside board order ignores fieldability | 1 | pending | pending |

Total wall time: pending.

## What counts as a pass

Baseline GREEN on the clean tree, and all five arms `caught`. Every one of
`MUTATION IS INERT`, `INCONCLUSIVE`, `ANCHOR FAILED`, `MUTANT CANNOT BUILD A BOARD`,
`MUTANT DOES NOT PARSE`, `FIXTURE NO LONGER BINDS` and
`SUITE IS ALREADY RED ON THE CLEAN TREE` is a finding, not a pass. Harness exit code: 0 = all
caught, 1 = at least one SURVIVED, 2 = at least one arm reached no verdict.

Raw log: `evidence/mutation_gate/v4_rerun_raw.log` (committed beside this file).
