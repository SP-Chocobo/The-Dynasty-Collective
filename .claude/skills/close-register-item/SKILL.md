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
**the full suite is what licenses a push.** ~800-870s. Background it and wait.

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

```bash
for i in 1 2 3 4; do git push -u origin ui-authority-pass && break || sleep $((2**i)); done
```

Branch is **`ui-authority-pass`**, not the harness-designated one. No PRs unless asked.

## What a close may NOT do

- **Never weaken a test to make a ratchet green.** The ratchet is the point.
- **Never mark an item DONE on a subset run.**
- **Never claim a fix verified against a baseline built by different code.** State which commit
  produced the baseline.
- **Never invent a constant to size a repair to a sample.** #56: a bound is not a threshold. If a
  repair needs a magnitude nobody has argued for, that is the finding — say so and stop.
