# #224 characterized and pinned — and the mutation pass found a hole in mutation testing itself

Two results. The second is worth more than the first.

## 1. #224: `bench_capacity` names two quantities, and neither is wrong

The register said "names two different quantities" and parked it. Here is what they are.

| | `lineup_optimizer.bench_capacity(roster_positions)` | `draft_room.estimated_bench_demand`'s local |
|---|---|---|
| what | BN slots this league gives **each team** | further **picks** the whole draft can still spend on bench |
| computed | `sum(1 for slot in roster_positions if slot == "BN")` | `max(remaining_draft_capacity(…) − Σ remaining_starter_demand(…), 0.0)` |
| unit | slots | picks |
| scope | per-team | league-wide |
| type | `int` | `float` |
| in time | **static** — takes no picks argument, so it cannot change during a draft | **draining** — falls to 0.0 as picks land |
| on the shared fixture | **3** | **36.0** at the opening board |

A 12x gap, and only one of them moves.

**There is no live crossed wire.** `draft_room` imports `lineup_optimizer as lo`, so the module
function is only reachable as `lo.bench_capacity` and the local never shadows it. Both are
correct where they stand. Renaming either is cosmetic and touches constrained source, so
neither was renamed.

**What was built instead.** `test_224_bench_capacity_vocabulary.py`, 8 tests, pinning the two
properties that make the tempting "deduplication" impossible to perform quietly: the magnitudes
differ, and only the demand quantity responds to the draft. The hazard is specific — a future
refactor sees a bare `bench_capacity` computed by hand, notices a function of that exact name
one attribute access away, and merges them. That substitution type-checks and reads as a
cleanup.

**Mutation-checked 6/6** (substitute the slot count · drop the `max()` floor · drop the starter
subtraction · floor at 1.0 · double the budget · invert the subtraction), control green, source
byte-identical before and after.

**Two things found on the way:**

- **`estimated_bench_demand` had ZERO direct tests.** A function on the demand path, replacing
  `expected_positional_consumption` under #59, with nothing asserting its output.
- **The `max(…, 0.0)` floor is load-bearing and reachable by ordinary means.** At 64+ picks the
  raw difference goes to −4, −8, −12: capacity exhausts while another position's starters are
  still owed. Without the floor every position's share goes **negative**, since the shares are
  `budget × appetite / total` and the sign propagates to all of them. A negative count of
  expected further picks is not a quantity this engine can mean.

## 2. The hole: a stale `.pyc` served mutated code after the source was restored

**My first mutation pass reported M2 (drop the floor) as SURVIVED. It was a vacuous test of my
own** — the floor assertion called the test file's local `_bench_budget` helper, which
re-implements the floor, so it passed against a mutated engine and caught nothing. That is the
failure this repo mutation-checks for, committed by me, and caught by the mutation pass working
as designed.

Repairing it exposed something worse. Measuring the exhausted state, `estimated_bench_demand`
returned a total of **1.0** where `bench_capacity` provably floors to `0.0` — and `0.0 ×
anything` cannot be `0.97`.

Four independent checks said the source was innocent:

- `git status` clean, `git diff draft_room.py` empty
- the line read `max(capacity - sum(starter.values()), 0.0)`
- `inspect.getsourcelines` on the **bound function object** showed the correct body
- a spy on both helpers confirmed `capacity=0.0`, `starter=12.0` **inside the call**

Deleting `__pycache__` produced `0.0` immediately.

**The mechanism.** CPython validates a cached `.pyc` against the source's **mtime and size**.
The M4 mutation was `0.0` → `1.0` — byte-identical in length — and the mutate/run/restore cycle
completed inside one mtime second. The `.pyc` still looked valid, so every later import got the
**mutant**, from a file that reads correctly and diffs clean. `inspect` reads the source file,
not the bytecode executing, so it cannot see this.

**Why this matters beyond one test.** It is aimed squarely at the instrument this project
relies on to know its tests are not vacuous. A mutation pass corrupted this way reports whatever
the stale cache holds: a mutation can read as "caught" when the tests never saw it, or as
"survived" when they did. Every same-length mutation in this repo's history is in scope —
`>`/`<`, `+`/`-`, `0.0`/`1.0`, same-length identifier swaps.

**The fix, now doctrine:** run every mutation arm under `PYTHONDONTWRITEBYTECODE=1`, control arm
included. The pass above was redone that way from scratch; M4 was confirmed a **genuine**
survivor rather than a cache artifact, and a test was added for it — a finished draft must
report exactly `0.0`, which is #59's whole point.

**The generalized rule:** when a measured number contradicts arithmetic you can do on paper,
suspect the instrument before the arithmetic. Re-deriving the same wrong number from the same
poisoned process confirms nothing.

## Not done, and deliberately

The full suite was running in the background across the tree while these mutations were applied,
so its result describes neither the clean tree nor any mutant. It is discarded rather than
quoted, and re-run clean afterwards.
