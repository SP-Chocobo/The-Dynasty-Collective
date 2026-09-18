# `#52` — the blind adversarial pass mandate, verbatim

> **Committed so the pass is REPRODUCIBLE, not as a record of its results.** Two passes were
> launched concurrently against `v1-freeze` (`6599b1e`) on Fable, each in an isolated worktree.
> They run inside a session container. **If that container is reclaimed mid-flight, their
> findings are lost** — the transcripts live under `/tmp`, not in this repository, and an agent
> cannot be resumed after its container dies.
>
> This file is what makes that recoverable. Re-running is then an exact repeat rather than an
> approximation, which matters because a second pass under a *different* mandate is not a re-run
> of the first — it is a different experiment, and the `#52` protocol turns on both passes having
> received identical instructions.
>
> **Do not read this file to the pass itself.** It is the mandate, not a briefing, but a reader
> who has seen the forbidden-path list knows exactly where the answers are kept.

## Conditions

- **Model:** Fable, per the standing constraint (Opus or Fable exclusively).
- **Isolation:** one git worktree each, which makes read-only structural rather than instructed.
- **Count:** two, concurrent, **identical mandates** — see the `#52` protocol entry in
  `POST_AUDIT_PLAN.md` for why identical rather than split.
- **Target:** `v1-freeze`, `6599b1e`.

## The mandate, as sent to both

```text
You are conducting an independent adversarial audit of a Python codebase at the repository root.
Work from the code itself.

## What the system is

A dynasty fantasy football draft assistant. Its core is a decision engine (the "CDME") that
prices players and recommends draft picks. Entry points worth knowing: app.py (Streamlit UI),
draft_room.py (valuation and board construction), pick_synthesis.py (the recommendation
snapshot), draft_battery.py / run_draft_battery.py (the simulation harness), data_merger.py
(ingestion and player identity), lineup_optimizer.py, league_config.py. There is a large test
suite (test_*.py, ~3100 tests) and a set of instruments that check the repo's own integrity
(prose_names.py, render_trace.py, assertion_floors.py, suite_taxonomy.py, quantity_readers.py).

## Your mandate

Find what is wrong with it. Be adversarial. You are looking for, in rough priority order:

1. Correctness defects in the valuation and decision path — arithmetic that doesn't mean what its
   name says, units that don't compose, clamps that destroy information, constants that are
   asserted rather than derived, branches that are unreachable or always-taken.
2. Measurement and instrument defects — tests that pass vacuously, guards that scan text instead
   of code, fixtures that encode the environment that recorded them, coverage that looks like
   coverage. A test that cannot fail is worse than no test.
3. Claims the code does not support — docstrings, comments and module prose asserting properties
   the implementation does not have.
4. Absence handling — this codebase claims a contract that "unmeasured" and "measured zero" are
   different facts and must never collapse. Find where it breaks that.
5. Anything else that would embarrass the authors.

## Hard constraints

DO NOT READ THESE PATHS. They contain the conclusions of prior audits and reading them destroys
the entire value of your pass:

- FREEZE_RECORD.md
- FREEZE_CHECKLIST.md
- POST_AUDIT_PLAN.md
- evidence/smoke_seats/ (any file)
- evidence/batteries/ (any file)

Be warned: several long-lived documents carry a banner at the top naming FREEZE_CHECKLIST.md and
POST_AUDIT_PLAN.md as "where current state lives". That banner is there for ordinary readers.
Ignore it. It is pointing at exactly the files you must not open.

If you read any forbidden path by accident, say so explicitly and prominently in your report. A
contaminated pass that admits it is useful. One that hides it is worthless. This is not a trap and
there is no penalty — silent contamination is the only failure mode that matters here.

You may read everything else: all source, all tests, README.md, ENGINEERING_DOCTRINE.md,
CDME_CONTRACTS.md, ARCHITECTURE_AUDIT.md, and any other evidence directory.

Do not modify any file. This is a read-and-report pass. Do not fix what you find. Do not run the
full test suite (it takes ~20 minutes); running targeted tests or small probes to confirm a
suspicion is encouraged.

## Reporting

Report findings ranked by severity. For each: the file and line, what is wrong, and a concrete
failure scenario — specific inputs or state that produce a wrong result. A finding without a
failure scenario is a code-style opinion, and you should label it as such.

Do not assign an overall score, grade, or verdict. Do not say whether the system is "ready".
Report what you found and let it stand on its own.

If you find nothing serious in an area you examined carefully, say that plainly — a well-supported
null result is a real contribution and will not be treated as failure.
```

## If the container was reclaimed before results landed

Re-launch two agents on Fable with worktree isolation and **the mandate above, unchanged**. Then
record in `POST_AUDIT_PLAN.md` that the pass was re-run and why, so the register does not imply a
single uninterrupted pass where there were two attempts.
