# Steps 2–4, and the deliverable answer

**Reads and arithmetic only. No engine source changed. Nothing wired, nothing tuned.**

Step 1 (`STEP1_WHAT_UPSIDE_MODE_IS_FOR.md`) established the target these steps measure against:

> the engine's own words for the trigger state — **"a deep bench / waiver-fringe pick"** —
> which is **per-seat** and **roster-depth relative**.

---

## Step 2 — the enumeration, derived from two closed sets

Not grepped by intuition. Two sources, both the repo's own:

1. **`quantity_readers.scan()`** — the engine's declared output surfaces, **97 quantities**
   (38 decision / 35 observable / 13 decomposition / 10 write-only / 1 carried).
2. **The engine's own draft-state functions** in `draft_room.py` and `lineup_optimizer.py`,
   reached by following what `positional_bench_appetite` actually calls.

The enumeration is **still not closed** — but it is now seven, not five.

### Ruled OUT, with the reason

| quantity | why it is not a candidate |
|---|---|
| `picks_consumed` (decision, PickSnapshot) | an **input-state stamp** — "which world this frozen state was computed from", explicitly "an identity check, not a change-magnitude model". Not a progress measure. |
| `bench_used`, `bench_value_used`, `exposure` | **write-only**, and scoped to `bye_collision` / `depth_exposure` — bench usage in a bye week, not draft depth. |
| `depth_exposure` | per-position **insurance value**, not a draft-progress state. |
| `decision_regime` | a **prose-register** classifier, not a valuation mode. But see step 4 — its contract matters. |

### The candidates (5 inherited + 2 new)

| # | quantity | source |
|---|---|---|
| 1 | dedicated slots full | `_team_starters_filled` + `dedicated_slot_counts` |
| 2 | complete legal lineup fieldable | `lineup_optimizer.optimize_lineup` |
| 3 | positions leave the replacement domain | `replacement_ranks` |
| 4 | league starter demand reaches zero | `remaining_starter_demand` |
| **5** | **bench capacity in slots** | **`lineup_optimizer.bench_capacity`** — NEW |
| **6** | **picks the league still has to spend** | **`draft_room.remaining_draft_capacity`** — NEW |
| **7** | **bench-bound remainder** (`capacity − starter demand`) | **a LOCAL inside `positional_bench_appetite`** — NEW |
| — | *the shipped behaviour* | `UPSIDE_MODE_DEFAULT_ROUND` |

## Step 3 — what each answers, its scope, and whether it matches

| # | the question it answers | scope | matches "a deep bench pick for THIS seat"? |
|---|---|---|---|
| 1 | are my named starting slots covered? | **per-seat** | partial — ignores flex, so it fires with 4 of 10 starters still empty (round 7) |
| 2 | can I field a legal lineup at all? | **per-seat** | this is "my roster is SAFE", not "this pick is fringe". Fires rounds 10–11 |
| 3 | does this position still carry starter demand? | **global, per-position** | a market question, not a roster-depth one |
| 4 | does the LEAGUE still need starters anywhere? | **global** | a market question. Fires round 23 |
| 5 | how many bench slots does this league give me? | **per-league** | **the denominator the phrase needs** — and nothing more. Supplies no threshold |
| 6 | how many picks does the league still have? | **global** (per-team summed) | a budget, not a depth |
| 7 | how many remaining picks are bench-bound? | **global** | the closest structural match, and still global |

### The constant, measured against the concept its own comment names

`lineup_optimizer.bench_capacity` is the denominator "deep bench" requires. Asked of the three
leagues that actually exist in this repo (`step2_bench_depth_arithmetic.py`, pure arithmetic
over `roster_positions`):

| league | starting | bench | rounds | bench spans | **round 15 is** |
|---|---|---|---|---|---|
| Fourth and Forever | 10 | 11 | 26 | rounds 11–21 | **bench body 5 of 11 — 45% in** |
| the repo's own upside-mode test league | 7 | 13 | 20 | rounds 8–20 | **bench body 8 of 13 — 62% in** |
| battery `12T_ppr` | 8 | 6 | 14 | rounds 9–14 | **never reached** |

**By the engine's own denominator, round 15 is the MIDDLE of the bench in Fourth and Forever,
not the deep bench.** It lands at three different depths across three leagues, one of which is
nowhere. The constant does not identify the state its own comment names, in any league this
repo contains.

## Step 4 — existing doctrine that constrains the answer

Two contracts already imply the SHAPE of an answer, without defining this transition.

**1. A regime should be decided by measurable state, not by the calendar.** `decision_regime`'s
own docstring:

> Reads only whether the leader is clear of the field and the leader's own
> `survival_probability` — **deliberately NOT round number or pick label**. A leader clearing
> both bars gets read as conviction-first regardless of whether that happens in round 1 or
> round 8.

The engine already has a regime classifier that refuses to key on the round, on principle. The
mode switch is the same shape of decision and does the opposite.

**2. A behavioural PRIOR may inform the debate layer; it may not inform the anchor.**
`positional_bench_appetite`'s docstring:

> **NEVER REACHES VALUATION.** Nothing on the replacement_levels / VOR / bpa path reads this,
> by design and by test.

This is a real constraint on the answer space, and it discriminates between the candidates.
Candidates 4, 6 and 7 are built from `remaining_starter_demand` and `remaining_draft_capacity`,
both stamped **"EXACT and BOUNDED […] carries no prior, no estimate and no behavioural claim."**
Those are admissible on the valuation path. A transition built on inferred/behavioural
quantities (bench *appetite*, rival take-probability) would collide with this doctrine, because
the mode switch changes the valuation itself.

**3. And the test that pins the constant declines to pin its meaning** — "the boundary itself is
a calibration decision" (step 1). It is a change-detector, not a contract.

---

## THE DELIVERABLE

> **Does the existing architecture already define what should trigger the balanced→upside
> transition, or is that concept genuinely missing?**

### GENUINELY MISSING — and missing for lack of a decision, not for lack of material.

That distinction is the finding, and it is sharper than "no observable means this."

**Every INGREDIENT of the stated concept exists in production, exact and bounded:**

- the per-team pick budget — `draftable_slots_per_team`
- picks the league still has to spend — `remaining_draft_capacity` (exact, bounded, reaches
  exactly zero when every roster is full)
- starter obligation still outstanding — `remaining_starter_demand` (exact, bounded, per-team
  summed, order-invariant)
- the bench-bound remainder — already computed, as `capacity − sum(starter demand)`
- bench capacity in slots — `lineup_optimizer.bench_capacity`

**What does not exist, anywhere:**

1. **A definition of "deep."** No quantity, constant, contract, test or comment says how far
   into a bench the waiver-fringe begins. The concept is named in one comment and defined
   nowhere.
2. **A per-seat assembly of the ingredients.** Every wired quantity above is global or
   per-league. The stated concept is a property of *this pick on my roster*. The parts for a
   per-seat version exist (`draftable_slots_per_team − my picks so far` is one line of
   `remaining_draft_capacity`'s own body) but no production quantity assembles them.
3. **Any connection between those ingredients and the switch.** `lineup_optimizer.bench_capacity`
   has **zero production callers** — verified: the only non-test mentions in the tree are its own
   `def` and an unrelated local of the same name in `draft_room.positional_bench_appetite`
   (a #126 name collision worth its own item). Register **#115** already records this as "bench
   capacity is not an engine input."

**So the switch does not approximate a defined concept badly. It substitutes a different kind
of quantity — a global calendar index, borrowed from an external product reference — for a
per-seat roster-depth state that the engine can measure and never has.**

### Per the brief: STOPPING HERE.

The design question — what "deep bench / waiver-fringe" should mean, and whether the transition
is per-seat or global — is not answered here and must not be. Choosing among the seven now
would be selection on the outcome, and step 1 already showed the direction of the effect follows
from that choice.

Two things recorded for whoever takes the design question, neither of them a recommendation:

- The doctrine in step 4 **narrows** the answer space without choosing within it: exact,
  non-behavioural quantities are admissible on the valuation path; inferred ones are not.
- The stated purpose is **per-seat**, while the current switch is **global**. Whichever
  definition is chosen, that scope mismatch is a separate decision and should be made
  deliberately rather than inherited.

## Also surfaced, not pursued

- **A #126 name collision.** `lineup_optimizer.bench_capacity` (BN slots in this league) and
  `draft_room.positional_bench_appetite`'s local `bench_capacity` (remaining picks minus
  remaining starter demand) are two different quantities sharing one name. Neither reads the
  other. Not part of this brief.
- The residual 29.2% TE and B2 were kept out of this investigation, as instructed. The
  architecture trace showed no direct causal connection to them.
