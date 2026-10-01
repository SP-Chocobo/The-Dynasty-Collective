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

## What the waves were ACTUALLY sent, and what the shield ACTUALLY was

**This section replaces an earlier one that was wrong.** That earlier text was written from memory
rather than from the transcripts, and it got three things wrong: it said `evidence/blind_pass/`
was added to the forbidden list at Wave 4 (it has been excluded since Wave 2), it said Waves 2
and 3 ran before that directory was committed (they did not — `MANDATE.md` landed at 01:46 and
Wave 1's two reports at 02:12, and Wave 2 launched at 02:12), and it described the isolation as
structural when it is not. What follows was read off the six agent transcripts, not recalled.

### 1. The mandate above is Wave 1's, not every wave's

From Wave 2 onward the passes received a **rewritten prompt**, not the text in the code block
above. The differences are substantive, not cosmetic:

- a **`## SETUP` block** (see §2) telling the pass which tree to audit and how to build it;
- a pointer to the real-data probe entry points (`build_players_db_from_capture`,
  `season_projections_from_capture`, `set_league_format(league_format_hint(league))`);
- a sixth mandate category, **end-to-end behaviour** — "drafting a full roster on a real league
  shape and looking at what the engine actually produces has been more revealing here than
  reading any single function";
- sharper wording in category 2 (invariants pinned where they cannot fail, a test matrix that
  omits the shape the system is actually used on);
- from Wave 4, a **steering paragraph** naming four saturated areas and pushing effort elsewhere.

So "identical mandates" holds **within** a wave — both passes in a wave get the same text — and
does not hold **between** waves. That is the correct reading of the `#52` protocol, but this file
previously implied the stronger one.

### 2. The target was a MOVING BRANCH HEAD, not the `v1-freeze` tag

The Conditions block above says the target is `v1-freeze`, `6599b1e`. **No wave ever audited that
tag.** Every pass was pointed at `origin/claude/fantasy-football-control-center-ff6qlu`, fetched
fresh, whose head advanced between waves as each wave's evidence was committed.

**This turned out not to matter, and that is a measured claim, not a hope.** Everything committed
between the freeze and now is markdown, `.gitignore`, and the evidence tree:

```
$ git diff --stat 6599b1e..HEAD -- '*.py' '*.json' 'data/'
(empty)
```

Not one line of Python, fixture, or test changed after the freeze. The audited code was
byte-identical across all four waves, so the waves really were attacking the same artifact. The
defect is in this document's description of the target, not in the experiment.

### 3. The isolation is INSTRUCTED, not structural — the worktree shields nothing

The Conditions block says worktree isolation "makes read-only structural rather than instructed."
That is false in a way worth stating precisely, because it is the kind of claim this project
exists to catch.

The worktree an agent is given sits on `main` (`cf8fa0c`, 2026-09-02) — **508 commits divergent
and not an ancestor of the branch**. It is not a stale copy of the work; it is a different line.
It does not contain most of the system, and it contains `POST_AUDIT_PLAN.md`. What it does *not*
contain — `FREEZE_RECORD.md`, `FREEZE_CHECKLIST.md`, `evidence/` — is absent only because those
files **did not exist yet in September**. That is an accident of staleness, not a shield.

So every pass has to leave the worktree to audit anything real, and the SETUP block tells it how:

```
git archive origin/claude/fantasy-football-control-center-ff6qlu | tar -x -C /tmp/audit_tree \
  --exclude='FREEZE_RECORD.md' --exclude='FREEZE_CHECKLIST.md' --exclude='POST_AUDIT_PLAN.md' \
  --exclude='evidence/smoke_seats/*' --exclude='evidence/batteries/*' --exclude='evidence/blind_pass/*'
```

**The pass builds its own shield.** The exclusion is real once applied — but it is applied by the
audited party's own hand, on instruction, which is exactly what "structural rather than
instructed" denies.

| Wave | How the pass reached the real tree | Forbidden paths present in it? |
|---|---|---|
| 1, pass A | `git archive <branch>` with **no `--exclude` flags at all** | **All of them, readable** |
| 1, pass B | `git checkout` of the branch head (`64f0830`) — never used an archive | **All of them, readable** |
| 2, 3, 4 | the `--exclude` recipe above | The six excluded paths absent; `.claude/` paths present |

Wave 1 therefore ran with **no structural shield whatsoever** — instruction only. Both passes
declared clean, and their transcripts support it: pass B's mentions of the forbidden files are its
own mandate, a `git log` line, two `ls` listings that merely show the files exist, and its
contamination statement. Visible is not the same as opened. But Wave 1's independence rests
entirely on two agents' compliance and their own word for it.

`.claude/skills/close-register-item/` and `.claude/blind-pass.settings.json` have **never** been
excluded, in any wave. They are named in the Wave 4 prompt's prose and nothing more. And
`blind-pass.settings.json` is, by its own commit message, "an inert file rather than the project
default" — it enforces nothing. The `#52` access control is, and has always been, a request.

### 4. One pass was launched against the stale tree, and was killed for it

Wave 4's first pass H launch was sent the Wave 1 mandate from the code block above — the SETUP
block was omitted. It ran ~14 minutes inside the worktree, auditing `cf8fa0c`: the 2026-09-02
divergent line, not the system. It was stopped and relaunched with pass G's prompt, verbatim, so
that Wave 4's two passes are mandate-identical as the protocol requires. **Nothing from the first
launch enters the ledger.** The lesson is the one this section exists for: the mandate that
matters is the one actually sent, and the only record of that is the transcript.
