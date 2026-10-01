# #35 — where this is, what is running, and what would be lost

Written so a container reclaim costs a re-run and not the thread. Update it whenever an arm
finishes or a plan changes.

## The question, in one line

`shared_slot_alternatives` prices a slot at `max(level(p) for p in slot.eligible)`. Late in a
draft that level can be the stale pre-draft anchor, so the slot is priced at a player who is not
there. **Formulation C** caps it at the best player actually remaining for that slot. Everything
about C so far is an argument; nothing about it is a measurement.

## What is DECIDED and what is OPEN

| | state |
|---|---|
| A (hard fieldability ceiling, `unfieldable_last`) | **shipped**, measured, holdout passed |
| B (upgrade exemption) | **built, measured, reverted** — `UPGRADE_EXEMPTION.md` |
| C (cap the slot phantom) | **OPEN.** Coherent, and it inverts a registered invariant |
| E (raw projection as bench value) | **rejected** — the owner's own correction |

## FINISHED. What the overnight run established.

All eight arms complete, full suite green (3496 tests, `OK`, 1 skip, 1 expected failure) at
`1649s`. Every arm report and both paired summaries are committed in `runs/`, so nothing here
depends on the scratchpad surviving.

### The three questions and their answers

| question | answer | where |
|---|---|---|
| Is C **admissible** as specified? | **No.** It inverts a registered invariant and refutes `TEAM_SPECIFIC_CAPS`' exemption over 8,500 rows, and the lift it introduces has no supremum, so no constant can be derived and `#56` forbids choosing one. | `../DESIGN_35_CAPS_REDERIVATION.md` |
| Is there an admissible shape? | **Yes, one.** Cap `bpa`'s anchor with the same quantity. The level cancels between the two terms, so `team_acquisition_value` is algebraically identical (measured 0.00 over 388 rows) and the board drafts the same in balanced mode, with the invariant and the caps intact. Differs in **upside mode**, which is unmeasured. | same |
| Is C **worth** its cost? | **Yes, by the pre-registered reading.** Positive on both seasons: **+21.7/seat** (2024) and **+43.7/seat** (2023), 9 of 12 and 8 of 12 seats improved. 2024's figure sits inside the ±25 band that would have been indeterminate on its own. | `RESULT_C.md` |
| Does C's pricing replace the ceiling? | **No, decisively.** Removing A costs **−103.5/seat** on 2023 (0 of 12 improved) and **−28.3/seat** on 2024, and **12 of 12 seats hoard past the ceiling on both** — kickers in 2023, defenses in 2024. | `RESULT_CEILING.md` |

### The finding neither derivation pass could make

C as specified caps `#30`'s **streaming floors**, from the opening board: DEF 146.05 -> 121.49, K
164.50 -> 159.88. Measured cost **+53 to +54 per seat**, and the signature is first-K/DST placement
collapsing to rounds 6-7 at every seat. The exemption is DERIVED, not chosen -- a streaming floor is
the season sum of each week's best wire option and exceeds any individual's projection on purpose.
Verified exact and narrow: `slots_floor_exempt` is 5,496, precisely the 2,748 K plus 2,748 DEF slots,
and neither exempt arm's cap touches K or DEF.

### `#34` closed, and two repairs shipped

`#34` is a duplicate of `#168`; anchor-filling the declined QBs leaves the top 12 byte-identical, so
declining moves no pick. Two of its three consumer gaps are repaired and pushed: a reachable
`TypeError` in `draft_counterfactual` (reproduced first), and a **registered invariant that was
false** -- `absence_kind` unstamped on 8 to 10 unpriced QB rows, with its guard blind because the
fixture was an opening board in a non-superflex league. The third gap cannot be fixed the obvious way
and is recorded as a limit.

### What the owner still has to rule

1. Whether to implement the anchor-capped reformulation at all, given it moves `universal_value` at
   drained positions (the best remaining receiver's `bpa` becomes 0.00) and changes upside mode.
2. `#29` -- resume or retire the VDS battery, still stopped at 13 of 36.
3. Re-capturing the fixture with weekly lines.
4. Gap 3's limit statement in `roster_diagnostics`.

### Blocked, not forgotten

`#30`'s live-sync verification. `api.sleeper.app` is denied by the environment's network policy
(403 on CONNECT, re-confirmed). Needs a change to Network access in the environment settings.

## Standing constraints that apply here

* `#56` — DERIVED, never calibrated. A bound is not a threshold.
* `#187` — absence is `None`, never `0.0`, in the instrument as well as the engine.
* `#184` — a valuation change goes to the owner, not into a repair commit.
* Both arms must run the same code in one process. Never compare a fresh run against a saved
  baseline from different code.
