# The v2 blind adversarial pass — mandate and conditions, verbatim

> **Committed so the pass is REPRODUCIBLE, not as a record of its results.** Five passes were
> launched concurrently against `v2-freeze` (`a8d1627`) on Fable, each in an isolated git worktree.
> They run inside a session container. **If that container is reclaimed mid-flight, their findings
> are lost** — the transcripts live under `/tmp`, not in this repository, and an agent cannot be
> resumed after its container dies.
>
> **Do not read this file to the pass itself.** It is the mandate, not a briefing, and a reader who
> has seen the forbidden-path list knows exactly where the answers are kept. It lives under
> `evidence/blind_pass/`, which is denied.

## Conditions

- **Model:** Fable, per the standing constraint (Opus or Fable exclusively).
- **Isolation:** one git worktree each. Note, as `MANDATE.md` had to correct for v1: this makes the
  passes independent of each other, it does **not** make them read-only or blind by itself.
- **Count:** five, concurrent.
- **Target:** `v2-freeze`, `a8d1627`.

## SPLIT MANDATES, and why — the one deliberate break from v1

v1's `#52` protocol ran **identical** mandates precisely so that two passes could be compared. That
comparison has already been made. Running five identical mandates now would buy far less than it
costs, and for a specific reason this repository has measured before: **this codebase is
deterministic, and so is an audit of it.** Five readers given one lens converge on one region of the
code and re-find one another's findings — the same failure the VDS battery's own `INERT_ARMS`
detector exists to name, where a listed axis turns out to cover nothing.

So each pass received the SAME preamble, SAME setup block, SAME hard constraints and SAME reporting
rules, and a **different `## YOUR LENS` section**. Each lens also states that other auditors are
covering the other areas, so a pass does not spend its budget re-deriving a neighbour's ground.

| pass | lens |
|---|---|
| A | Valuation arithmetic, units and constants — the pricing path, every clamp, weight and derived-vs-chosen constant. |
| B | Absence semantics, boundaries, and claims the prose makes that the code does not support. |
| C | The measurement apparatus itself — vacuous tests, text-scanning guards, ratchets, coverage theatre, and the integrity instruments audited as code rather than as authority. |
| D | Roster geometry and lineup legality — eligibility sources, flex and shared slots, unusual league shapes, the feasibility and fieldability backstops. |
| E | Ingestion, identity, provenance and vintage — everything upstream of valuation, traced backwards from a board value to the file and column it came from. |

**This is a different experiment from v1's, and the register must not imply otherwise.** A split
pass answers "what is wrong across these five areas"; an identical pass answers "do two independent
readers agree". Both are worth running; they are not substitutes.

## The shield

`.claude/blind-pass.settings.json` copied over `.claude/settings.local.json` and **extended** — the
v1 list predates the documents that now hold the v2 conclusions:

```
Read(./FREEZE_RECORD.md)            Read(./evidence/smoke_seats/**)
Read(./FREEZE_RECORD_V2.md)         Read(./evidence/batteries/**)
Read(./FREEZE_CHECKLIST.md)         Read(./evidence/blind_pass/**)
Read(./POST_AUDIT_PLAN.md)          Read(./evidence/design_35/**)
Read(./DOC_INDEX.md)                Read(./evidence/upside_gap/**)
                                    Read(./.claude/skills/close-register-item/**)
                                    Read(./.claude/blind-pass.settings.json)
```

`DOC_INDEX.md` is denied for v2 and was not for v1: it is a status map of every document in the repo
(WITHDRAWN / SUPERSEDED / DECLARED), which is a signpost to exactly what was already settled.

**DELETE `.claude/settings.local.json` when the pass is over.** Committing those rules as the project
default would blind every ordinary session, including the ones that need the register constantly.

## The mandate, as sent to all five

```text
You are conducting an independent adversarial audit of a Python codebase at the repository root.
Work from the code itself.

## What the system is

A dynasty fantasy football draft assistant. Its core is a decision engine (the "CDME") that
prices players and recommends draft picks. Entry points worth knowing: app.py (Streamlit UI),
draft_room.py (valuation and board construction), pick_synthesis.py (the recommendation
snapshot), draft_battery.py / run_draft_battery.py (the simulation harness), data_merger.py
(ingestion and player identity), lineup_optimizer.py, league_config.py. There is a large test
suite (test_*.py, ~3500 tests) and a set of instruments that check the repo's own integrity
(prose_names.py, render_trace.py, assertion_floors.py, suite_taxonomy.py, quantity_readers.py).

## SETUP for real-data probes

Run every probe FROM THE REPOSITORY ROOT -- never `cd` elsewhere first; DataMerger resolves its
baseline paths relative to the working directory and silently loads nothing otherwise. The
real-data fixture is:

    import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb
    players_db, provenance = rdb.build_players_db_from_capture()   # returns a TUPLE
    season_projections = rdb.season_projections_from_capture()
    merger = dm.DataMerger()
    merger.set_league_format(db.league_format_hint(league))        # before drafting ANY format

Do not run the full test suite (~18 minutes). Targeted tests and small probes to confirm a
suspicion are encouraged.

## YOUR LENS

<<one of the five in the table above; each also says that other auditors cover the other areas>>

## Hard constraints

DO NOT READ THESE PATHS. They contain the conclusions of prior audits and reading them destroys
the entire value of your pass:

- FREEZE_RECORD.md, FREEZE_RECORD_V2.md, FREEZE_CHECKLIST.md, POST_AUDIT_PLAN.md, DOC_INDEX.md
- evidence/smoke_seats/, evidence/batteries/, evidence/blind_pass/, evidence/design_35/,
  evidence/upside_gap/ (any file in any of these)

Be warned: several long-lived documents carry a banner at the top naming FREEZE_CHECKLIST.md and
POST_AUDIT_PLAN.md as "where current state lives". That banner is there for ordinary readers.
Ignore it. It is pointing at exactly the files you must not open.

If you read any forbidden path by accident, say so explicitly and prominently in your report. A
contaminated pass that admits it is useful. One that hides it is worthless. This is not a trap and
there is no penalty -- silent contamination is the only failure mode that matters here.

You may read everything else: all source, all tests, README.md, ENGINEERING_DOCTRINE.md,
CDME_CONTRACTS.md, ARCHITECTURE_AUDIT.md, invariant_registry.py, and any evidence directory not
listed above.

Do not modify any file. This is a read-and-report pass. Do not fix what you find.

## Reporting

Report findings ranked by severity. For each: the file and line, what is wrong, and a concrete
failure scenario -- specific inputs or state that produce a wrong result. A finding without a
failure scenario is a code-style opinion, and you should label it as such.

Do not assign an overall score, grade, or verdict. Do not say whether the system is "ready".
Report what you found and let it stand on its own.

If you find nothing serious in an area you examined carefully, say that plainly -- a well-supported
null result is a real contribution and will not be treated as failure.
```

## THE ISOLATION DID NOT HAND THE PASSES THE FROZEN TREE — record this before re-running

Reported independently by two passes and recorded here because it would otherwise be rediscovered
every time:

**`isolation: "worktree"` did not check out the branch under audit.** One pass found its worktree on
`main` at `cf8fa0c`, with a **2051-line `draft_room.py`** against the real 4445, and without
`draft_battery.py`, `run_draft_battery.py`, `league_config.py`, `invariant_registry.py`,
`prose_names.py`, `quantity_readers.py` or `basis_semantics.py`. Another found the same files
missing and rebuilt a view at the branch tip.

Both detected it themselves, reconstructed a correct tree, and verified byte-identity of every
module they audited against the real checkout before reporting — one by creating a local branch at
the tip, the other by copying the working tree into its scratchpad **excluding every forbidden path**
and running with `PYTHONPATH=.`. So their findings are about the frozen engine. But this was luck of
the draw in how carefully each pass checked, not a property of the setup.

**On a re-run, state the commit in the mandate and require the pass to verify it first.** Add to the
SETUP block:

```
Before auditing anything, confirm you are reading the tree under audit:
    git log --oneline -1
    wc -l draft_room.py pick_synthesis.py
Expected: a8d1627 or a descendant whose only differences are documents, draft_room.py ~4445 lines.
If your checkout disagrees, say so in your report and reconstruct a correct view before proceeding
-- and if you copy the tree, exclude every forbidden path from the copy.
```

Note what this does NOT do: it does not name the forbidden files a second time, and it does not
describe where conclusions live. A line count and a commit are not a signpost.

## If the container was reclaimed before results landed

Re-launch five agents on Fable with worktree isolation and the mandate above, unchanged, one lens
each. Then record that the pass was re-run and why, so the register does not imply a single
uninterrupted pass where there were two attempts.
