# Phase 7 — propagation, branches, caches

## 7.1 — the refusal propagation rule *(closed; one owner decision raised)*

`survival_is_presentable()` is False: the survival estimate lost to a constant predictor on two
independent arms (SMOKE 0.22480 vs 0.19348; REAL 0.16127 vs 0.14224 over 6,277 real-draft pairs),
and it is worst where a reader would lean hardest — the board's own top row predicted **0.810**,
observed **0.451**. What is withheld is the *claim*, not the computation.

`SURVIVAL_DERIVED_FIELDS` has always been the vocabulary, and its docstring already said it exists
*"so a surface cannot suppress the headline number and keep its derivatives."* **Nothing made a
surface ask.**

### Measured, not taken from the ledger

Every presentation boundary was rendered and searched. One was already right; four leaked.

| boundary | before | after |
|---|---|---|
| `draft_board_ui` | **correct** — asks, keeps the family together, ships the policy beside the value, redacts at render | unchanged, now pinned |
| `diff_snapshots` | all three emitted as deltas | filtered |
| `format_snapshot_for_llm` | those deltas printed under human labels, beneath the withholding notice | clean |
| three system prompts | family listed among *"real, already-computed numbers"*; `"19% survival with a QB run detected"` as a worked KEY FACTOR; `"survival_probability for Player X"` as a worked DISAGREE | derived from the policy |
| `screen_context` seed | `survival 31%`, unconditionally | the measured pick count |

A prompt that names a number, demonstrates citing it, then refuses to supply it is not a guard —
it is an invitation to fabricate, aimed at the one participant that cannot check.

### The rule

> One function names what is withheld. Every surface that presents to a person — or to a chair
> that speaks to one — redacts through it. A guard enumerates the surfaces; the registry counts
> them.

`withheld_fields()` returns the family, or the **empty set** when presentable, so every call site
keeps one shape and the day calibration flips the numbers return with no edit. The prompts are
*templated* from it rather than hand-corrected, for the same reason. `_DIFF_FIELDS` now derives its
team-terms half from `TEAM_SPECIFIC_TERMS` and filters at diff time — the list names what a diff
*can* report, which does not change when a calibration verdict does.

Mutants killed, one per arm: the diff stops filtering, `withheld_fields()` always empty, the seed
prints the estimate again, the prompts revert to naming the family.

### Two guards that were wrong, and how each was caught

- **My own probe reported a leak that was not one.** A label search matched *"The survival
  probability is WITHHELD, not missing… do not estimate one yourself"* — the refusal itself, which
  must stay. The guard is now **value-based**: each field gets a distinctive sentinel and every
  boundary is searched for every plausible rendering of it. Every assertion carries a non-vacuity
  arm that renders the same boundary *presentable* and requires the number to appear, because a
  surface that renders nothing passes an absence check trivially.
- **The suite pinned the leak** (W4-17). `test_pick_debate` asserted survival is absent from the
  candidate block at `:57-62` and that a **survival-only** delta reaches the chair prompt at
  `:234-239`. Two contradictory contracts in one file; production implemented the second. The
  *claim* — a real change propagates into the evidence — is correct and kept; only the carrier
  changed to a presentable field, and the withheld case is now its own contract.

A third, mine: the replacement test filtered `result.diff` through a comprehension, which on an
empty diff never evaluates its own condition — so it passed while `ps` was not even imported, and
would have passed just as happily with the rule removed.

---

## OPEN OWNER DECISION — `NECESSITY_SURVIVAL_WEIGHT`

**W1-07.** A fifth of the displayed necessity score is a function of the withheld estimate:
`NECESSITY_SURVIVAL_WEIGHT = 20.0` of a 0–100 score, carried as `(1 − survival) × 20`. Under the
rule as stated this is a violation — a withheld quantity feeding something presented. Removing it
is a valuation change under `#56`, so **nothing was touched**.

Measured, one process, one toggle, 384 candidates across 8 real board states:

| | |
|---|---:|
| necessity delta | min 0.00, **max 8.50**, mean 0.40 |
| **label flips** | **12 of 384 (3.1%)** |
| | `PREFERRED → CLOSE CALL` ×7 |
| | `STRONG ACTION → PREFERRED` ×3 |
| | `MUST TAKE → STRONG ACTION` ×2 |

The mean is small because most candidates survive, so `(1 − survival)` is small; the tail is where
it bites, and the flips land on the labels a person acts on.

Three readings, none of them mine to pick:

1. **Remove it.** The rule is the rule: a number we refuse to show must not move a number we do.
2. **Keep it and say so.** The estimate is withheld from *display* because a reader cannot judge
   it; the engine can still weigh it internally, and necessity is the engine's own judgement.
3. **Replace it with the measured substitute** — `intervening_picks`, which is what every surface
   now shows in its place. This is a re-derivation, not a deletion, and would need its own scale.

---

## 7.2 — one normalised take model, one consumer set *(closed)*

**J-03 and K-02, found independently.** `#206` established the conservation law — an opponent
makes ONE pick, so their take probabilities are mutually exclusive and must sum to ≤ 1.0 across
their board — called it *"arithmetic, not a tuned number"*, and normalised the model. **It was
applied to one of two consumers.**

`positional_forfeits` went on summing the RAW table over each opponent's top five, capped at
`RUN_TAKE_PROBABILITY_CAP` **per position**. Capping per position conserves nothing: four
positions each capped at 0.90 permit **3.6 players from a single pick**.

Measured on a real superflex board, five consecutive turns:

| turn | expected takes / picks | |
|---|---:|---|
| 0 | 22.00 / 22 | conserves **by coincidence** — RB saturating at 0.90 × 22 = 19.80 |
| 1 | 22.80 / 20 | **impossible** |
| 2 | 21.78 / 18 | **impossible** |
| 3 | 19.36 / 16 | **impossible** |
| 4 | 16.94 / 14 | **impossible** |

The same run assigned **TE 0.00 on every turn** and QB 0.00 on two, in a superflex league — and
`pick_debate` renders an exactly-zero forfeit as *"Cost of delaying QB entirely: measured 0"*, the
strongest evidence for waiting, while survival (which says those QBs are gone) is withheld (J-04).

### Four variants measured, not argued

| | turn 0 | QB | RB | WR | TE |
|---|---:|---:|---:|---:|---:|
| **A** raw, top-5, capped *(shipped)* | 22.00 / 22 | 0.00 | 19.80 | 2.20 | 0.00 |
| **B** normalised, top-5 | 1.19 / 22 | 0.00 | 1.09 | 0.10 | 0.00 |
| **C** normalised, all priced ✅ | 10.52 / 22 | 0.82 | 3.48 | 3.96 | 2.26 |
| **D** normalised, all + unpriced | 22.00 / 22 | 2.90 | 5.68 | 8.59 | 4.83 |

**B** is the same defect inverted — `#206` measured the five named keys at 1.21 of a 23.49 board
total, so the floor-weighted tail *is* the signal, and keeping the cut reports barely one take
across 22 picks. **D** conserves with equality because it counts every take, but over half a
board's mass sits on unpriced rows and step 2 walks the **priced** curve; counting an unpriced
take against it claims a priced player was removed when none was.

**C ships.** The shortfall from the pick count is the expected number of unpriced takes — which is
information, not error. Verified on the shipped function across **27 turns: zero conservation
violations, and no zero-take position anywhere** — J-04 closed as a consequence.

`FORFEIT_OPPONENT_BOARD_DEPTH` is **deleted**, not left unreferenced: a constant nothing reads is
a claim nothing checks.

### The tests that were about the old model

- `test_the_forfeit_depth_and_the_take_probability_table_stay_coupled` guarded a divergence
  between two `.get()` defaults (`0.0` vs the floor). Unification **removes** that divergence
  rather than checking it, so the replacement pins the unification — strictly stronger, since
  there is no second default left to drift.
- `test_forfeit_board_depth_matches_the_take_probability_table` asserted the cut matches the
  table's depth, because *"ranks past it carry only the flat floor and would add noise, not
  signal"*. True of the raw table, false of the normalised one. Inverted to the measurement that
  made the cut indefensible.
- The round-boundary test's fixture sat on the raw sum of 1.5; under normalisation it reports
  1.24. Its **claim** — accumulation order does not move the answer — is untouched and kept, and
  the ulp-stability property moved onto `_curve_at` directly, where it lives and where it will
  survive the next model change.
- `test_survival_evidence`'s depth-window assertion restated without the window: `rank_by_id` is
  a valuation ordinal over priced rows, so an unpriced row must not appear in it **at all**.

### Two of my own errors, both caught by the tests I was writing

1. A guessed "40-row tail" in the replacement assertion failed — 40 × 0.02 = 0.80 is *less* than
   the named keys' 1.21. Replaced with the derived **crossover** (`named / floor` ≈ 61 rows),
   which is checkable and needs no invented row count.
2. The conservation test failed at `3.01 > 3`. Not the law — the per-position `round(…, 2)`, which
   over P positions can inflate the sum by `P × 0.005`. The tolerance is now that quantity,
   derived and stated, rather than a fudge.

Mutants killed: revert to the raw table with the per-position cap, drop the normaliser, and
**restore the top-5 window**. The third survived the first round — an upper bound is satisfied by
any model that undercounts — until the **equality** case was added: on a fully priced board the
takes sum to *exactly* the pick count, which no window can pass.

Registered as the seventh invariant, population = take-model call sites (4).

---

## Still open in Phase 7

- **7.3** the `trade_value` branch family, compared structurally rather than patched three times
- **7.4** cache keys — every key must contain every input that can change the result
- **7.5** state and persistence — `store_io`'s bare `except OSError`, `upload_batches.record`
  returning an id for an unpersisted batch, `outcome_record`'s damaged→absent collapse
- the sixth leak, pinned in Phase 6.2 and belonging here: `_drop_contested_identities` withholds a
  contested price from the **pool**, and `_team_roster_players` re-resolves it from the **merger**
