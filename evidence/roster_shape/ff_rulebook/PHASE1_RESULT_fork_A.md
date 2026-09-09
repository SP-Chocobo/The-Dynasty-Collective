# PHASE 1 RESULT: Fork A. `displaced` is exactly correct — and the read found something else.

Pre-registered in `PREREGISTRATION_displaced_contract.md`, committed before this ran.
Probe: `phase1_contract_read.py`. Production path intercepted; the two solves reproduced
with production's own roster, levels and unpriced set; assignment sets diffed.

## The governing question, answered

> What entity does production say it displaced, and is that exactly the entity its contract
> says it displaced?

**Fork A, 4 of 4 states.** At 2, 5, 7 and 8 tight ends held, exactly ONE entity leaves the
optimal lineup — player `7002`, value **200.90** — and the returned `displaced` is
**200.90** at every state. Single entity, exact match, no ambiguity, no cascade to resolve.

**`displacement_level` honours its contract. There is no optimizer defect.** The suspicion
that it was returning "my best tight end instead of the weakest reachable occupant" is
wrong: 200.90 IS what leaves, because that tight end holds `TE_5` and nothing else on the
roster can take that slot. B1' — "`displaced` is invariant to saturation" — is true as an
observation and is NOT a defect: a ninth tight end genuinely must beat the tight end
holding the only slot tight ends can win.

**B1 and B1' are both closed. Fourteenth and fifteenth withdrawals.**

## What the consistency check found instead

I nearly published Fork A without noticing that `base total_value` is **identical at
2864.03 across all four states**, on rosters that grow from 9 to 18 players. That should be
impossible, so I checked rather than reported. The explanation is the actual finding:

**Two starting slots are filled by PHANTOMS at every state, including with eighteen real
players rostered.** `__free_WR_3` and `__free_FLEX_8`, each worth **217.75**.

217.75 is this league's WR replacement level. It is higher than **nine of the ten starters**
on a real, 18-player, mid-draft roster. So the engine's model of "a freely available
receiver" out-starts almost everything a chair has actually drafted, in two slots, all
draft long. The lineup does not change from 9 players to 18 because nothing acquired ever
beats the phantom.

That is why `displaced` never moves, and it is a fact about the LEVELS, not the optimizer.

## Second observation, recorded without interpretation

The per-slot alternatives are not monotone across the draft:

| state | QB_0 | SUPER_FLEX_9 | RB_1/2 | TE_5 | WR/FLEX |
|---|---|---|---|---|---|
| 2 TE held | 243.29 | 243.29 | 170.81 | 149.17 | 217.75 |
| 5 TE held | 243.29 | 243.29 | 156.84 | 108.64 | 217.75 |
| 7 TE held | **80.36** | 217.75 | 125.97 | 80.36 | 217.75 |
| 8 TE held | **149.17** | 217.75 | **170.81** | 149.17 | 217.75 |

`QB_0` falls 243.29 → 80.36 and returns to 149.17. `RB_1/2` falls 170.81 → 125.97 and
returns to exactly 170.81. **I am not claiming why.** The previous write-up's "league demand
thins, the rank walks up a thinning list" was an interpretation and is withdrawn as such.
What is observed is that several levels return to values they held earlier, exactly.

## Where this goes next — and where it does NOT

**Next:** `replacement_levels`. Two questions, in this order:
1. Why is the WR level (217.75) above nine of ten real starters? A replacement level that
   out-starts a drafted roster is either a correct statement about an extremely deep
   receiver pool or a rank/scale defect, and the two are distinguishable by reading the
   rank and the player it lands on.
2. Why do levels return exactly to prior values mid-draft?

**Not next:** the flex-anchor candidate stays stranded. It rests on displacement/replacement
semantics and only half of that is now settled.
**Not next:** no battery. This remains a semantic read.
**Not touched:** no engine source has been modified at any point in #222.

## Method note promoted to doctrine

> **If the system already computes the quantity under test, instrumentation must observe
> that production quantity rather than reconstructing it from downstream artifacts.**

Three probes failed by rebuilding replacement levels from `compute_draft_board`'s output
rows. The broader form also covers the "board rows are not the population that produced the
board" family. It belongs in the engine-measurement skill.
