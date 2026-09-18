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

## Still open in Phase 7

- **7.2** take models — `expected_taken` summing to 23.32 over 22 picks
- **7.3** the `trade_value` branch family, compared structurally rather than patched three times
- **7.4** cache keys — every key must contain every input that can change the result
- **7.5** state and persistence — `store_io`'s bare `except OSError`, `upload_batches.record`
  returning an id for an unpersisted batch, `outcome_record`'s damaged→absent collapse
- the sixth leak, pinned in Phase 6.2 and belonging here: `_drop_contested_identities` withholds a
  contested price from the **pool**, and `_team_roster_players` re-resolves it from the **merger**
