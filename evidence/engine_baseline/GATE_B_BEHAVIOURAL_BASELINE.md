# Gate B — the behavioural baseline for `v4-freeze`

**Status: complete. The baseline is recorded, it agrees with its own tree, and it catches a
planted change.** Every number here was measured in this run.

- **Captured at:** `946fcc8`, tree `ed044dc96136e18d23d1dac040046b894dc5a560` — the tree
  `v4-freeze` certifies
- **Instrument:** `engine_baseline.py` (`--write` / `--check`)
- **Record:** `ENGINE_BASELINE.json`, beside this file
- **Cost:** ~155s to capture, ~150s to check

## Why this exists

`v4-freeze` certifies that the engine was correct **in its current shape**: 4,166 tests, 8 of 8
mutation arms, a 53-arm battery and the full 36-arm VDS. None of that survives an architectural
move on its own. The suites prove the code is self-consistent, and a refactored engine can be
self-consistent too — extracting a service layer, generating a thin runtime and rerouting a
client all change shape, and every existing gate would stay green across a change that quietly
moved an answer.

So this is a **camera, not a laboratory**. It photographs what the engine answers and diffs the
photograph. It contains no judgement about whether the answers are right; that is what the suite
and the batteries are for, and duplicating it here would be a second source of truth (`#126`).

## What "the boundary" is, derived rather than assumed

`app.py` reaches the engine through `pick_synthesis.build_snapshot` and essentially nothing else
— 3 calls, against 1 each for `draft_room.simulate_opponent_picks` and `build_mock_league`. So
the snapshot **is** the contract a service layer would expose, and capturing it captures the
thing that must not move. `PickSnapshot` carries 11 fields; each `CandidateSnapshot` carries 57.

## Three states per format, because the opening board alone would have proven nothing

Measured on the first exploration run, at `12T_ppr_K_DEF` pick 1.01 over 72 candidates:

| term | present | nonzero |
|---|---|---|
| `displacement_adj` | 72/72 | **0** |
| `depth_exposure` | 72/72 | **0** |
| `risk_adj` | 72/72 | **0** |
| `need_bonus` | 72/72 | 72 |

Those three are not quiet, they are **structurally** zero: with every dedicated slot open each
position's probe evicts its own phantom, so `displacement_adj` is identically zero for every
position at once; `depth_exposure` is not measured until a bench exists; `risk_adj` needs a
designation to price. A baseline taken only at the opening board would pin all three at a value
the state cannot produce, and **a refactor that broke all three would diff clean.**

So each format is captured at `opening`, `mid` (round 9 or later) and `late` (a drained board),
with the indices derived from each format's own length — `12T_ppr_SHORT_DRAFT` drafts 8 rounds
and `HEAVY_IDP` drafts 18, so a hardcoded index would photograph incomparable depths and call
them the same state. Mid and late prefer a turn with real picks **ahead** of it, because
`survival_probability`, `positional_forfeit` and `rival_premium` are computed over the gap to the
next own-turn; a turn without one reports them as a clean null.

The histories are production's, not invented: each format replays the `sharp_auto` arm's own
`pick_sequence` from the committed VDS run, so every state is one the engine really reached.

## What was captured

| format | rounds | opening | mid | late |
|---|---|---|---|---|
| `12T_ppr_K_DEF` | 16 | 72 candidates | 26 | 7 |
| `12T_ppr_SF` | 15 | 48 | 14 | 6 |
| `4WR_TE_PREMIUM` | 16 | 48 | 24 | 5 |
| `HEAVY_IDP` | 18 | 84 | 57 | 8 |
| `12T_ppr` | 14 | 48 | 7 | 7 |
| `12T_ppr_SHORT_DRAFT` | 8 | 48 | 46 | 7 |

**6 formats, 18 states, 562 candidate records.** The drain is the point: a pool defect that does
not remove itself looks harmless at the open and dominates by the end.

## The two verifications, and why both are needed

**1. It agrees with its own tree.** Re-capturing `946fcc8` and diffing against the record:
`IDENTICAL — 6 formats, 18 states, 562 candidate records, every field.` A non-deterministic
baseline reports noise as regression forever.

**2. It can fail.** `draft_room.NEED_BONUS_PER_DEDICATED_SLOT` was moved from `4.0` to `4.5` in
memory — a real mutation, since the engine reads the module global at call time, with no
`__pycache__` hazard and no window where the repo sits broken. Result: **3,855 behavioural
differences, caught and named.**

```
candidates[0].need_bonus:              8.67   -> 9.67
candidates[0].team_acquisition_value:  232.91 -> 233.91
candidates[0].rival_premium:           8.67   -> 9.67
candidates[0].pick_necessity:          83.7   -> 85.3
candidates[0].necessity_label:         'PREFERRED' -> 'STRONG ACTION'
```

One constant moved by 0.5 reaches 3,855 fields, including a label a person reads on screen.
Without this second arm, "identical" could mean the comparison is vacuous — which is precisely
the defect repaired in `assertion_execution` this cycle, where `--check` returned the same green
line whether 359 tests were measured or none were.

## Three defects this instrument had, all found by running it

Recorded because the pattern is the point: none would have been found by reading the code.

1. **`--check` captured before looking for the baseline**, so a missing record cost a 150-second
   sweep to discover instead of 0.04s. The test now pins the ordering by bounding the time, not
   merely the verdict.
2. **The verdict branched on the unfiltered diff list.** A clean tree's only differences are the
   18 per-state wall-clock timings, so it fell past the success path and printed the regression
   prose over `0 behavioural difference(s)`, returning 1 on a run that had just proven the engine
   unchanged. A check that reports failure on a passing run is the same defect as one that
   reports success on a failing run — and it was the second time in one session that a verifier
   printed its failure branch on the pass path.
3. **It wrote its own JSON store**, bypassing `store_io`. Caught by
   `test_store_io.test_no_module_writes_a_json_store_outside_store_io` in the certifying suite —
   the repo's own guard, doing exactly its job. Repaired by routing both directions through
   `store_io` rather than taking an exemption: the baseline IS a store by that module's own
   distinction, since it is not re-fetchable and the damaged bytes would be the only copy. The
   write's **return value is checked**, because `store_io.write` can decline to overwrite a store
   it has found unparseable.

## How to use it

```
python3 engine_baseline.py --check     # does this tree answer as the frozen engine does?
python3 engine_baseline.py --write     # record a NEW baseline (declare the version first)
```

`--check` exits 0 for identical, 1 for a behavioural difference, 2 when it is holding nothing.

**What a difference means.** Either the change was intended — in which case declare a new engine
version, enumerate the deltas, and re-run `--write` — or it was not, and this is the regression
the baseline exists to catch. That is the Phase 5 contract in roadmap v3: `v4-freeze` is the
permanent oracle, and production may evolve only by demonstrating equivalence or declaring a
version.

**What it does not cover.** The pool is pinned to one committed capture, so this says nothing
about behaviour under a different vendor universe; `--check` reports a pool-size change and warns
that differences may be about the data rather than the engine. It also covers the Draft Room's
boundary only — the LLM surfaces (`pick_debate`, `llm_engine`) are not captured, because their
answers are not deterministic and a golden master over them would be noise.
