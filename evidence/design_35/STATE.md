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

## Status as of the last update to this file

**Both Fable passes handed back and are committed.**

* `evidence/DESIGN_35_CAPS_REDERIVATION.md` — verdict (b): the registered non-positivity invariant
  does not survive C and has an exact derived replacement; the caps' exemption is REFUTED and no
  constant can be derived for it; **and the same prices are available in the right column** by
  capping `bpa`'s anchor instead, which leaves the invariant and the caps intact. See
  `SYNTHESIS.md` §1.
* `evidence/DESIGN_34_UNPRICED_SUPERFLEX_QB.md` — `#34` closes as a duplicate of `#168`. Declining
  moves NO pick (measured counterfactual, top 12 byte-identical). Three consumer gaps; one was a
  reachable crash and is fixed, one is a false registered invariant, one cannot be fixed the obvious
  way. See `SYNTHESIS.md` §3.
* **My own finding, which neither pass could make:** C's cap binds on `#30`'s streaming floors from
  the opening board. `SYNTHESIS.md` §2.

**Running now** (from the repo root, launched at `6cd3be0`):

| what | state |
|---|---|
| `c4_2024` — four arms, 12 seats | control arm in progress |
| `c4_2023` — four arms, 12 seats | control arm in progress |
| full test suite, after the `draft_counterfactual` fix | ~25% at last check; it LICENSES the push of `8f8ca9e` and everything stacked on it |

Four arms each: `control`, `capped`, `capped_floor_exempt`, `capped_floor_exempt_no_backstop`. What
each pairing answers is in `PREREGISTRATION_C.md`'s amendment. **Read that before the numbers.**

`RESUME.md` says how to restart after a reclaim, and `checkpoint.sh` copies every completed arm
report into `evidence/design_35/runs/` so a reclaim costs at most the arm in flight.

## Not applied, deliberately

The one-line `absence_kind` repair from `evidence/absence_kind/IFF_BREACH_ON_A_DRAINED_BOARD.md`. It
touches `draft_room.py`, and the suite currently running licenses a DIFFERENT change; a second edit
mid-suite would invalidate it. Apply after that suite is green and `8f8ca9e` is pushed, then run the
suite again.

## The experiment in this directory

`phantom_cap_experiment.py` — an in-process A/B with **no engine edit**. It wraps
`dr.build_available_pool` to remember the board's own remaining pool (the cap needs a pool and
`board_slot_alternatives(levels, roster_positions)` never receives one — that is the first thing
recorded about C), wraps `dr.streaming_replacement_levels` so a floor can be told from a pool
reading, and toggles `dr.board_slot_alternatives` (and, for the fourth arm, `dr.unfieldable_last`).

Verified before any arm was read:

* the cap reproduces the measured round-14 phantom exactly — both FLEX slots 216.25 -> 173.00,
  a reduction of 43.25, which is the number that motivated C;
* the cap can only LOWER a slot and never changes WHICH slots are priced (so the arm differs in
  one thing, not two);
* the `#30` floor exemption is exact and NARROW — it restores K and DEF to their floors and moves
  nothing else;
* with no pool recorded it falls back to the shipped construction **and says so** in
  `cap_stats.pool_missing`, rather than treating absence as a number (`#187`);
* the control arm reproduced 2024 seat 1 at **+168.4**, exactly the shipped figure from when `#30`
  closed;
* the cap is not vacuous: 1050 of 2420 priced slots capped on the smoke, `pool_missing` 0;
* the working directory is asserted to be the repo root before anything is imported, because this
  file sits two directories down and `sys.path[0]` would otherwise not be the root.

### What a result would and would not settle

It settles **whether C is worth its cost**, and nothing about whether C is admissible — the
derivation already answered that: **not as specified.** A null or negative result retires C on
outcome grounds. A positive result makes the anchor-capped reformulation the thing to put to the
owner, since it prices identically in balanced mode without inverting anything.

## Standing constraints that apply here

* `#56` — DERIVED, never calibrated. A bound is not a threshold.
* `#187` — absence is `None`, never `0.0`, in the instrument as well as the engine.
* `#184` — a valuation change goes to the owner, not into a repair commit.
* Both arms must run the same code in one process. Never compare a fresh run against a saved
  baseline from different code.
