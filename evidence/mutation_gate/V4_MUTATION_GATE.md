# V4 mutation gate — `invariant_confirmation.py`

**STATUS: RUN IN PROGRESS.** This file is being committed incrementally as each arm
establishes a result. Nothing below is an estimate; every number is measured. The
verdict table is incomplete until the status line above says the run finished.

- **Commit under test:** `7984b1d` ("Reconcile the record: scope stale citations, install the defect-class write-up")
- **Branch:** `claude/v4-verify-mutation`
- **Harness:** `PYTHONPATH=. python3 invariant_confirmation.py`, run from the repo root
- **Started:** 2026-10-01T03:10:27Z
- **Scored modules:** 229 (`test_*.py` discovered, minus `test_invariant_confirmation_anchors`,
  which the harness excludes by construction because it reads `draft_room.py` from disk and
  counts the very anchor text a mutation replaces)

## Container preparation — the harness could not have run as the container shipped

This container had **no Python dependencies installed at all**. `import pandas` failed, so
`DataMerger` could not be imported and the reference board could not be built: the harness
would have exited 2 at `REFERENCE BOARD FAILED TO BUILD` without applying a single mutation.

Installed the full `requirements.txt` before starting. That file carries an explicit warning
worth honouring: without `playwright`, the board-execution tests **skip** rather than fail, and
a reclaimed container once ran the suite 14 tests lighter and still reported OK. So I verified
the browser is reachable **under the harness's own deliberately stripped subprocess
environment** (`PATH=/usr/bin:/bin`, no `PLAYWRIGHT_BROWSERS_PATH`, no `HOME`):

```
CHROME = /opt/pw-browsers/chromium-1194/chrome-linux/chrome
HAVE_PLAYWRIGHT = True
has_browser = True
```

`test_216_room_integrity._find_chrome()` globs `/opt/pw-browsers/chromium-*` directly rather
than reading the env var, so stripping the environment does not cost those tests. They run.

## Preflight — `FIXTURE NO LONGER BINDS` did not fire

The harness's own printed line:

```
reference board: 427c40010c69c32c  feasibility binds on 619 of 964 rows, fieldability on 131
```

That line reports **one branch only**. The four-quantity guard above it loops over both
branches and checks all four correctly, but the `print` that follows reads `_digest`, `feas`,
`total` and `unfield` *after* the loop has ended, so it displays whichever branch iterated
last — the upside one. This is a reporting defect in the harness, not a verdict-affecting one:
the guard itself did check all four quantities, and all four passed. Recorded here because the
printed line is the artifact a reader would otherwise quote as "the preflight".

Measured per branch directly, via `invariant_confirmation._board_fingerprint()` on the clean
tree:

| branch | board digest | feasibility (`fills_required_slot`) | fieldability (`cannot_be_fielded`) | board rows |
|---|---|---|---|---|
| balanced | `217c138c6b0e5d3704b635b435f44d913fb5edeb70c9088551a585e0ddb90dc2` | 619 | 131 | 964 |
| upside | `427c40010c69c32c7ca9c35dc8b5a07c6dc43554251c7432c153a5a6d0d9d423` | 619 | 131 | 964 |

All four censuses are strictly between 0 and 964, so both backstops bind on both branches and
no mutation of either is inert by construction. **The two branch digests differ**, which is the
specific precondition the two upside arms need: the fixture genuinely enters the upside branch
and produces a different board there, so a mutation confined to that branch has something to
change. (Until recently the fixture built the balanced board only, both upside arms read
`MUTATION IS INERT` forever, and the gate could not have passed.)

## Anchor coverage

`test_invariant_confirmation_anchors`: **passes on the clean tree (74.0s)**.

The two board sorts it pins are both present and distinct, confirming the post-D5 split that
each arm pair targets:

- `draft_room.py:4743` — upside branch, 5 sort keys (`_feasible`, `_unfieldable`, `final_score`, `projected_points`, `player_id`)
- `draft_room.py:5006` — balanced branch, 4 sort keys (`_feasible`, `_unfieldable`, `final_score`, `player_id`)

## Baseline arm

Running. A "caught" verdict on any arm is meaningless unless this is green, so it is reported
here before any mutation result.

| | |
|---|---|
| verdict | *pending* |
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
