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

## Three things are running concurrently

1. **Fable — the caps re-derivation.** Deliverable `evidence/DESIGN_35_CAPS_REDERIVATION.md`.
   The question: if slot alternatives are capped, `displacement_adj` can go POSITIVE for a
   single-position candidate, which inverts `lineup_optimizer.displacement_level`'s derived
   non-positivity ("THE SIGN") and reaches `pick_synthesis.TEAM_SPECIFIC_CAPS`, which
   hand-exempts that term from a bound two shipped constants derive from, citing exactly the
   premise C destroys. Either a new two-sided bound exists or C costs a CHOSEN constant, which
   `#56` forbids. **This is the GATE on C**, and it is a gate about admissibility, not outcome.
2. **Fable — `#34`.** Deliverable `evidence/DESIGN_34_UNPRICED_SUPERFLEX_QB.md`. In superflex
   from round 15 all 102 remaining QB rows carry `final_score is None` and
   `replacement_basis is None`. `_board_order` sorts them last so a sharp chair never takes one;
   the question is whether declining is right, how wide it is, and what a consumer that does not
   honour `is None` would do with 102 of them.
3. **Opus — does C actually draft better.** `phantom_cap_experiment.py` in this directory.

## The experiment in this directory

`phantom_cap_experiment.py` — an in-process A/B with **no engine edit**. It wraps
`dr.build_available_pool` to remember the board's own remaining pool (the cap needs a pool and
`board_slot_alternatives(levels, roster_positions)` never receives one — that is the first thing
recorded about C), then toggles `dr.board_slot_alternatives` between the shipped function and the
capped one and grades both arms with `run_backtest_grade` on realized weekly outcomes.

Verified before any arm was read:

* the cap reproduces the measured round-14 phantom exactly — both FLEX slots 216.25 -> 173.00,
  a reduction of 43.25, which is the number that motivated C;
* the cap can only LOWER a slot and never changes WHICH slots are priced (so the arm differs in
  one thing, not two);
* with no pool recorded it falls back to the shipped construction **and says so** in
  `cap_stats.pool_missing`, rather than treating absence as a number (`#187`);
* the working directory is asserted to be the repo root before anything is imported, because
  this file sits two directories down and `sys.path[0]` would otherwise not be the root.

### What a result would and would not settle

It settles **whether C is worth its cost**, and nothing about whether C is admissible — that is
Fable's gate. A null or negative result retires C on outcome grounds without anyone having to
re-derive `TEAM_SPECIFIC_CAPS`. A positive result makes the re-derivation a bill worth paying.

### Runs

| season | arm | state | result |
|---|---|---|---|
| 2024 | control / capped, 1 seat (smoke) | launched | — |
| 2024 | control / capped, 12 seats | not launched | — |
| 2023 | control / capped, 12 seats (holdout) | not launched | — |

The 12-seat pair is the answer; the smoke exists only to prove the cap fires on a real board and
that the two arms are not byte-identical. `cap_stats` in every summary says how often the cap bit
and by how much — if it reports zero the arm is vacuous and the numbers mean nothing.

## Standing constraints that apply here

* `#56` — DERIVED, never calibrated. A bound is not a threshold.
* `#187` — absence is `None`, never `0.0`, in the instrument as well as the engine.
* `#184` — a valuation change goes to the owner, not into a repair commit.
* Both arms must run the same code in one process. Never compare a fresh run against a saved
  baseline from different code.
