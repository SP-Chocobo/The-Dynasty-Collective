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
4. **FULL SUITE. Not a subset.** ← the step that has already been skipped once
5. `python3 assertion_floors.py --write && python3 assertion_floors.py --check`
6. `POST_AUDIT_PLAN.md` entry, task update, commit, push.

**Step 4 is where the one real process failure happened.** `#144` was committed and pushed after
verifying six targeted modules (183 tests, all green). The full suite then failed on
`test_assertion_floors` — a file I had not thought to run. Targeted runs are for iterating;
**the full suite is what licenses a push.** Background it and wait.

**Budget it from a measurement that carries its own date.** The last one: **2862 tests in
~1170-1210s** at `3e9c074` (2026-09-12). This file previously said "~800-870s" with no commit
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
