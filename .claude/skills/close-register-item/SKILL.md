---
name: close-register-item
description: Close a numbered register item (#NNN) in this repo — POST_AUDIT_PLAN entry, task update, assertion floors, full suite, commit, push. Use when finishing any tracked item, surfacing a new one, or correcting a published finding. Encodes the ratchets that fail loudly and the one ordering mistake that has already let a failure through.
---

# Closing an item without leaving a hole behind

This repo's value is its record. An item closed without its evidence is worth less than one left
open, because the next reader believes it.

## The order, and the one step that is not negotiable

1. **Make the change.** Code, docs, or a recorded decision — "characterized, not built" and
   "measured and rejected" are legitimate closes. `#144`'s close was *rejecting* the fix the item
   itself proposed.
2. **Tests that fail on the old behaviour.** A test that passes before and after guards nothing.
3. **Mutation-check them.** Break the code the test defends and confirm the test fires. Record
   the counts (`3/2/2`, `4/2/37`). This is what keeps the suite honest.
4. **`git add -A`, then read `git status --short`** — BEFORE the suite, not beside the commit.
   Nine test modules read `git ls-files`, so an unstaged new file is invisible to them: three new
   modules once sailed through a full suite with `test_prose_names` reporting OK having read none
   of them, and it failed the moment they were staged (`#299`). Staging is a change the suite can
   observe. The rules in "Staging" below apply here, just earlier.
5. **FULL SUITE. Not a subset.** ← the step that has already been skipped once,
   **and run it with the interpreter `suite_reach.py --check` passes on** — see below; `python3`
   is not necessarily that interpreter and in this container it is not. Do not touch the tree
   OR the index while it runs; both void it, and nothing in the output will say so.
6. `$PY suite_reach.py --check && $PY assertion_floors.py --write && $PY assertion_floors.py --check`
   then `$PY skip_gates.py --check` — and `--write` it in the SAME commit if a new gate is
   deliberate, with the reason in the message (`#303`). It is the third ratchet and it
   rations the one number the summary line gives you for two different things.
7. `POST_AUDIT_PLAN.md` entry, task update, commit, push.

**Step 4 is where the one real process failure happened.** `#144` was committed and pushed after
verifying six targeted modules (183 tests, all green). The full suite then failed on
`test_assertion_floors` — a file I had not thought to run. Targeted runs are for iterating;
**the full suite is what licenses a push.** Background it and wait.

**ESTABLISH THE INTERPRETER BEFORE YOU SPEND 21 MINUTES (`#298`).** This is step 0 and it
costs two seconds. A container can carry more than one python, and the one `python3` resolves to
is not necessarily the one that can run this repo. Measured 2026-11-04, same tree, same moment:

    interpreter                          collects   test modules that fail to import
    /usr/local/bin/python3  3.11.17         1,059          180 of 238
    /usr/bin/python3        3.13.17         4,235            0 of 238

`python3` resolved to the FIRST of those. It carries 1 of the 11 distributions
`requirements.txt` declares, so 180 modules die on `import pandas` — and the run does not look
broken, because `unittest` replaces each dead module with one synthetic `_FailedTest`:

    Ran 1059 tests ... FAILED (errors=180)

`failures=0`. Grepping `^FAIL:` — which is what the "two shell hazards" section of
`engine-measurement` tells you to do — finds **nothing**, and 3,176 test cases that never ran are
reported as 180 lines of a different word. Worse, `assertion_floors --check` printed
`no guarantee has shrunk (238 modules held to a floor)` and exited 0 on that same interpreter,
because it is `ast.parse` over the source and reachability is not a question it asks.

So derive the interpreter rather than trusting `python3`, and never hardcode a version here — a
path with `3.13` in it is the `ui-authority-pass` mistake in a new costume:

```bash
for cand in /usr/bin/python3 /usr/local/bin/python3 python3; do
  command -v "$cand" >/dev/null 2>&1 || continue
  "$cand" suite_reach.py --check --no-count >/dev/null 2>&1 && { PY=$cand; break; }
done
echo "${PY:?no interpreter on this box can import all 238 test modules -- run suite_reach.py to see why}"
```

Then use `$PY` for the suite, the floors, and every probe. `suite_reach.py --check` is also a
test (`test_suite_reach.py`), so a wrong-interpreter run fails loudly from inside the suite even
if this step gets skipped — which is the point, since step-skipping is this file's one recorded
process failure.

**BEFORE LIFTING ANYTHING OUT OF `app.py`, RUN THE TESTS THAT READ ITS SOURCE (`#300`).** A
test does not have to name the function you moved to depend on where it lives. `#300` moved
`build_freshness_manifest` out of the hull; I grepped the suite for that NAME, found three
modules, fixed the one that failed, and pushed. Two others failed the full suite — both scan
`app.py`'s source for a STRING INSIDE the moved span (a call site, an assignment), and the
function's name appears in neither assertion. The pre-flight that actually covers it is
mechanical:

```bash
mods=$(grep -ln 'ui_source\.\|Path("app.py")\|open("app.py"' test_*.py | sed 's/\.py$//')
$PY -m unittest $mods          # 54 modules, 1082 tests, 104 seconds
```

That is the whole risk class for any `#137` extraction at one seventeenth of a full suite's cost.
Grepping for the symbol you moved is NOT this check and is not a substitute for it.

**Budget it from a measurement that carries its own date.** The last one: **4311 tests in
1968.7s** at `b4dbffb` (2026-11-04), measured with `__pycache__` cleared first per `#240`.
**Size a timeout from 1968.7s.**

Four measurements the same day, which is more useful than any one of them:

| tests | seconds | per test | commit |
|---|---|---|---|
| 4235 | 1276.5 | 301ms | `dbae709` |
| 4248 | 1682.7 | 396ms | `96bb4a8` |
| 4276 | 1976.7 | 462ms | `029b31e` |
| 4311 | 1968.7 | 457ms | `b4dbffb` |

The per-test cost rose 301 -> 396 -> 462ms and then stopped; the last run added 35 tests and got
8s FASTER. So the thing to carry forward is that **the suite got ~50% more expensive per test over
one day and has now plateaued**, not that it is still climbing. Part of the rise is accounted for
-- `#299` un-skipped 15 browser-executing tests, and `#308` made 34 more reachable -- but those
modules cost 30.2s, 1.8s and ~0.2s standalone, nowhere near the ~660s of total growth. **The
remainder is unattributed and is not claimed.** Do not extrapolate from the trend; re-measure.

The `dbae709` entry is in turn the one that proves this paragraph's point. The figure before IT said **3347 tests in
878.3s** at `3bb81a7` (2026-09-20) and had gone six weeks without a re-measure: the suite grew by
888 tests and 398s in that time, so a `timeout` sized from the old number would have killed a
healthy run at 70% complete. Note the per-test cost barely moved (262ms -> 301ms) while the total
grew 45%: growth, not regression, and the total is what a timeout has to clear. The run before it
was **3091 tests in 860.9s** at `#283` (2026-09-17), same method. The
one before it: **3091 tests in 860.9s** at `#283` (2026-09-17), same method -- so in three days
the suite grew by 256 tests and got 2% slower, i.e. the per-test cost FELL while the total
barely moved. Growth, not regression; budget from the total. Before it,
**2925 tests in 670.0s** at `3599422` (2026-09-14) — so in three days the suite grew by 166 tests
and got 28% SLOWER, undoing most of `#201`'s speedup in wall-clock terms while the per-test cost
stayed flat. Growth, not regression; budget from the total, not the trend. The
entry before it said 2918 tests in 921.6s at `be84fee` (2026-09-13) — so in one day the suite
GREW by 7 tests and got 27% FASTER. That speedup is not noise and not this skill's doing: it is
`#201`'s resolution memo, the same repair that took the `#218` reproduction from 1125.0s to
562.4s on byte-identical output. A budget that only ever ratchets upward would have hidden it.
The entry before THAT said 2862 tests in ~1170-1210s at
`3e9c074` (2026-09-12), so the suite GREW and got FASTER in a day. Neither direction is safe to
extrapolate; re-measure rather than scaling the old figure. This file previously said "~800-870s" with no commit
attached; the suite grew past it and the figure went stale without anything failing, which is
how a `timeout` gets set too low and kills a run that was fine. If the number here is older than
your work, re-measure it rather than trusting it — and write the new one down with its commit.

## The two ratchets, and why they fire

Both are working as designed when they fail. Neither is noise to route around.

**`assertion_floors`** — per-module counts of `self.assert*` by name. It fires when a count
DROPS. Its own docstring says it "cannot see a vacuous assertion, or tell a strengthening from a
weakening" — so a genuine strengthening trips it too. Replacing two loose bound-checks with one
exact `assertEqual` moved `assertLess 2 -> 1` and failed the build. **Correct response: confirm
the drop is real and intended, then regenerate in the same commit** so the drop is reviewable
rather than incidental.

**The `CandidateSnapshot` field-count pin** (`test_display_contract_boundary`) — fires on any
new field, and its message asks two questions rather than a number. **Answer both in the comment,
then bump.** For `growth_signal` the honest answer was that it implies a 0-100 percentile scale —
exactly the band that file exists to say the engine's values do NOT live on — so it must not be
rendered beside raw-points `universal_value`.

## Writing the POST_AUDIT_PLAN entry

House style, in order:

- **A heading that states the finding**, not the topic. `#156 CORRECTED — IT IS A
  SIGNAL-PRECEDENCE PROBLEM, NOT A REPLACEMENT-LEVEL ONE` beats `#156 notes`.
- **The measurement, as a table or a code block.** Real numbers with their `n`.
- **What it rules OUT.** Hypotheses checked and killed belong in the record so nobody re-runs
  them. "Every late QB pick carries `live_starter_demand`, not one `predraft_anchor`" saved the
  next reader a day.
- **What is NOT fixed, and why** — blocked, deferred, or the owner's call. Say which.
- **Corrections in full.** If a published claim was wrong, restate it, say it was wrong, and give
  the evidence. Do not quietly edit it.

## Commit messages

Subject states the finding. Body carries the measurement and the reasoning. End with:

```
Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: <session url>
```

Never put a model identifier anywhere else in a pushed artifact.

## Push

Push the branch you are ON. Do not name one here.

```bash
BR=$(git rev-parse --abbrev-ref HEAD)
for i in 1 2 3 4; do git push -u origin "$BR" && break || sleep $((2**i)); done
```

No PRs unless asked.

**This file used to say "Branch is `ui-authority-pass`, not the harness-designated one."** That
was true when it was written and is now wrong, which is exactly why no branch name belongs in a
skill file. Measured 2026-09-12: `ui-authority-pass` is **191 commits behind** the harness's
designated branch and 7 ahead of it, last touched 2026-09-09 at `70e380c`. A session that had
followed the old line literally would have pushed finished work onto a branch nobody reads —
the `#239` failure mode with a different cause.

The harness names the branch for a session in its own instructions, and the session is already
standing on it. `git rev-parse --abbrev-ref HEAD` is that name, derived rather than restated
(`#126`), and it cannot go stale. If the harness's branch and your intent ever disagree, that is
a question for the owner, not a default to hardcode.

## Staging: never name files, and never silence `git add`

This has now produced a broken commit **three times** (`#169`, twice, and again on 2026-09-12).
The shape is always the same: `git add a.py b.py c.json` with one name wrong — a case-mismatched
`assertion_floors.json` against the real `ASSERTION_FLOORS.json`. **`git add` fails the WHOLE
command on a pathspec that matches nothing and stages nothing at all.** With `2>/dev/null` on the
line, it fails in silence, and the commit that follows carries a message describing work it does
not contain.

```bash
git add -A                 # or: git add -u, for tracked files only
git status --short         # READ IT. staged entries are column 1; ` M` is NOT staged
git commit -F - <<'EOF'
...
EOF
git show --stat HEAD       # the file list must match what the message claims
```

Never redirect `git add`'s stderr. Never trust `git add`'s exit status by inference — read
`git status --short`, where an unstaged modification (` M`, space first) looks almost exactly
like a staged one (`M `), which is how it gets past you.

A broken commit that is already pushed is not amended into silence. Add the missing files in a
NEW commit whose message opens by saying what happened — the record is the point.

## What a close may NOT do

- **Never weaken a test to make a ratchet green.** The ratchet is the point.
- **Never mark an item DONE on a subset run.**
- **Never claim a fix verified against a baseline built by different code.** State which commit
  produced the baseline.
- **Never invent a constant to size a repair to a sample.** #56: a bound is not a threshold. If a
  repair needs a magnitude nobody has argued for, that is the finding — say so and stop.
