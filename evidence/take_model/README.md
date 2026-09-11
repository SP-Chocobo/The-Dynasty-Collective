# The per-opponent take model is not a probability distribution

**Measured, not argued.** One opponent board built through the production path
(`draft_strategy._build_opponent_boards`, 12-team superflex dynasty PPR, real capture universe,
`league_format_hint` set). Every player on that board carries a rank, and `_take_probability`
maps every rank to a number. Summing those numbers over the board asks the model a question it
has never been asked: **how many players does it think this team will draft?**

```
board size (players carrying a rank)                 256
sum of RANK_TAKE_PROBABILITY over ranks 1-5         1.21
floor contribution, 0.02 x 251 remaining rows       5.02
----------------------------------------------------------
EXPECTED PICKS BY ONE TEAM                          6.23
a team actually makes                                  1
```

Identical on all 12 boards, which is expected — same pool, same valuation, so this is a property
of the model, not of a seat.

A team takes exactly one player, so these numbers must sum to at most 1. They sum to **6.23**.
Survival is `prod(1 - p_take)` over the intervening opponents, so every `p_take` being too high
makes every survival number too low. That is the direction of `#206`'s symptom.

## Where the incoherence lives — and it is NOT the headline table

**96% of the excess is the floor**, not the five-rank table:

| | contributes | note |
|---|---:|---|
| ranks 1-5 | 1.21 | over 1 already, but only just — near-coherent on its own |
| ranks 6-256, all at `RANK_TAKE_PROBABILITY_FLOOR` | 5.02 | **the defect** |

`_take_probability` is `RANK_TAKE_PROBABILITY.get(rank, FLOOR)`. There is no domain limit, so a
board's 251st-ranked player and its 6th-ranked player are assigned the same 0.02. The table is
documented as a deliberately-uncertain, never-backtested prior and it behaves like one. The
floor is a fallback that silently became the answer for 98% of the board.

## This explains a SECOND symptom already in the register, which is what makes it load-bearing

`POST_AUDIT_PLAN` records that under exhaustion `survival_probability` "survives as a number but
collapses to a single value — **d=1, no signal**", the only surviving quantity with zero
discriminating power, and notes it is *"worse than absent: it looks like signal and is not."*

That is this floor, seen from the other end. Every candidate past rank 5 receives the same 0.02
from every opponent, so every candidate receives the same survival. The register recorded the
symptom in one place and `#206` recorded a different symptom in another; they are one mechanism.

## What this does NOT explain, stated so it cannot be overclaimed

**The floor alone cannot produce `#206`'s 0.00.** By the module's own arithmetic:

| the player is... | p per opponent | survival over 11 | over 60 |
|---|---:|---:|---:|
| rank 6+ on every board (floor) | 0.02 | 0.80 | **0.30** |
| rank 3 on every board | 0.18 | 0.11 | ~0 |
| rank 1 on every board | 0.55 | **0.00015** | ~0 |

A player who reads 0.00 and then survives 60 picks was ranked HIGH on many boards, not floored.
For him the model is doing exactly what it claims — and it is the BOARDS that disagree with what
the drafters did. So `#206` has two halves and this finding is only the first:

1. **the model is incoherent** (this document) — measured, mechanical, fixable in arithmetic;
2. **the opponent boards rank by the engine's own valuation**, so "rank 1 on their board" means
   "rank 1 by CDME", and real rivals do not draft by CDME. That half is `#206` proper and is
   NOT addressed here.

Fixing the floor would raise every deep-bench survival and restore discrimination among them.
It would not move the 0.00 cases at all.

## Not repaired here, deliberately

Choosing a coherent replacement is a modelling decision, not a bug fix. The obvious candidates —
normalise `p_take` across the board so it sums to 1, or cut the floor off past a rank the board
itself implies — are different claims about how rivals behave, and **#56** forbids picking one by
calibrating it to this sample. The measurement is recorded; the choice belongs with `#50`/Phase 3,
alongside the second half above.

Reproduce: the probe is arithmetic over `RANK_TAKE_PROBABILITY`, `RANK_TAKE_PROBABILITY_FLOOR`
and one board's rank count. `test_take_model_coherence.py` re-derives it without building a board.
