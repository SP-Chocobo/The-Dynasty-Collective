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

---

## Mandate drift across waves — what each wave actually received

The header above says a re-run must use "the mandate above, unchanged." That is the rule for
**repeating** a wave. It is not what happened **between** waves, and the difference has to be on
the record or this file overstates the comparability of the six passes.

Waves 2, 3 and 4 are not repeats of Wave 1. They are successive experiments against the same
frozen target, and each one was given a slightly different instruction because the previous wave
had changed what "unexplored" means. Two things drifted:

**1. The forbidden-path list grew, because the cheat-sheet grew.** Every wave's own report and
this ledger become, the moment they are committed, exactly the kind of conclusions document the
`#52` access control exists to keep out of a pass's hands. A pass that reads Wave 2's findings is
not an independent confirmation of them.

| Added at | Path | Why it became forbidden |
|---|---|---|
| Wave 1 | `FREEZE_RECORD.md`, `FREEZE_CHECKLIST.md`, `POST_AUDIT_PLAN.md`, `evidence/smoke_seats/`, `evidence/batteries/` | The original `#52` list — prior-audit conclusions |
| Wave 4 | `evidence/blind_pass/` (all of it, including this file) | Waves 1–3's reports and the triage ledger now live here |
| Wave 4 | `.claude/skills/close-register-item/`, `.claude/blind-pass.settings.json` | The register skill names findings by number; the settings file enumerates the forbidden paths, which is itself a map to the answers |

Waves 2 and 3 ran before `evidence/blind_pass/` was committed, so their smaller list was not a
weaker shield — there was nothing yet at those paths to shield. All six passes declared no
contamination, and passes C–F additionally verified the worktree exclusions before reading.

**2. Wave 4 added a steering paragraph, and Waves 1–3 had none.** By the end of Wave 3, four areas
had been examined by six independent passes: `time_horizon_adj`'s percentile populations, the
anchor cache key's completeness, `prose_names`' history shield, and the `need_bonus` invariant
test. A seventh look at those returns a re-report, not a finding — and a re-report cannot advance
the stopping condition, which counts NEW verified findings. So Wave 4's passes were told those
four are known and to spend their effort on the comparatively unexplored surface instead: the UI
and debate layers, `pick_debate.py`, `draft_board_ui.py`, `data_merger.py`'s ingestion and
reconciliation, `store_io`, the LLM prompt boundary, `league_config`, and end-to-end drafted
rosters.

**What that costs, stated plainly.** Steering makes Wave 4 a weaker test of "is the engine clean"
than Waves 1–3 were, because a steered pass is no longer sampling the whole codebase uniformly —
it has been pushed away from the area that has produced the most convergence. A quiet Wave 4 is
therefore evidence about the *unexplored* surface, not about the engine as a whole, and the
stopping condition must not be read as though it were the latter. The saturated four are not
closed by silence in Wave 4; they are closed, if at all, by the six passes that already examined
them and by the repairs that follow the waves.
