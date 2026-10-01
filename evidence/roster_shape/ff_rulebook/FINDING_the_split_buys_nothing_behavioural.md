# A roster-blind shared-slot charge is identically zero — the split is descriptive, not behavioural

Measured through the production function and confirmed on a production board. **No engine source
changed.** This retires the path the "split it" ruling was aimed at, and it answers the question
that ruling left open.

---

## What the ruling was aiming at

The owner ruled SPLIT IT, on the reading that `displacement_adj` fuses a **league-structural**
charge (the slot is SHARED with better-supplied positions) with a **roster-specific** one (the
slot is TAKEN by one of my starters) — and that once separated, upside mode's roster-blind rule
would drop only the second and could legitimately keep the first.

**The open question I flagged was: which slot does a candidate reach when the roster is unknown?**

## The answer, and it is stronger than "undecided"

`dr.displacement_adjustments` on the real rulebook's levels, **empty roster** — the only
roster-free assumption available:

```
  QB: adjustment=  0.00   displaced=243.29  (own level 243.29)
  RB: adjustment=  0.00   displaced=170.81  (own level 170.81)
  WR: adjustment=  0.00   displaced=217.75  (own level 217.75)
  TE: adjustment=  0.00   displaced=149.17  (own level 149.17)
```

And the same thing in production, not a fixture — the opening board, all twelve rosters empty:

| board state | rows with a non-zero charge |
|---|---|
| **opening (every roster empty)** | **0 of 481** |
| pick 100 | 221 of 381 |
| pick 150 | 192 of 331 |

**With no roster, every candidate reaches his own dedicated slot**, so `displaced == level_pos` and
the charge is exactly 0.00 for every position. The same roster shape with its six dedicated slots
filled and its flexes open gives RB −46.94 and TE −68.58.

## What follows

**There is nothing for a roster-blind mode to keep.** The shared-slot over-credit exists *only
because roster occupancy closed the candidate's dedicated slot* — a tight end is priced against a
flex phantom instead of his own level precisely because his TE slot is already held. That is a
roster fact by definition, not a league-structural one that happens to be stored in a roster-shaped
box.

**So the dual classification resolves, and it resolves toward reading A.** Both halves are
roster-derived; `displacement_adj` is legitimately a team-specific term in whole; and **upside
mode zeroing it is correct.** Invariant 4b's reason for the term carrying no cap survives intact
— it is about non-positivity (the term only ever removes credit), not about the term being
universal.

**And the chain terminates somewhere a refactor cannot reach.** The engine drafts human-like for
fourteen rounds because the counterweight is live, and then goes roster-blind for twelve at the
point where roster occupancy has become the dominant fact about a pick. No renaming, no
decomposition, and no reallocation of terms changes that. **The live question is whether upside
mode should be roster-blind in the deep bench at all** — which is #223 (the transition concept is
missing) and #229 (the domain of validity is keyed on the anchor, never the candidate), arrived at
for the third time from a third direction.

## The one escape hatch, named and rejected on the project's own rules

A roster-free shared-slot charge could be manufactured from a **prior** — "by round 15 the average
team holds N at each position, so assume the dedicated slot is closed." That is an invented
constant fitted to nothing, which #56 forbids ("a bound is not a threshold"), and
`positional_bench_appetite`'s own history is the precedent: the flat per-team bench-demand term was
tried and reverted for exactly this reason.

## What the split IS still worth, stated without inflation

**Descriptive value, as an observable (#55's pattern — reported, no selection authority).** The
board currently says a tight end is charged 68.58 and does not say why. Split, it can say *"68.58
because the slot you would use is shared with receivers, 0.00 because nothing of yours is in the
way"* — which is the difference between a number and an explanation, and it is what a human in the
Draft Room and the Debate Dock chairs actually need.

**It does not change a single pick**, and this document is the reason to stop expecting it to.

## Correction to my own vocabulary spec

`VOCABULARY_the_two_displacement_charges.md` says `shared_slot_adj`'s *"magnitude comes from league
structure and the live pool … it contains no information about who is on my roster."* **Narrowed:**
that is true *given which phantom is reached*, and which phantom is reached is entirely
roster-determined — so the term as a whole carries only roster-derived information, and is zero
without it. The exact decomposition and the three regimes in that document are unaffected; the
claim about where its information comes from is.
