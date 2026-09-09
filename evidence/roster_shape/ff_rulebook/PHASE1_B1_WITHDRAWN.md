# PHASE 1 GATE: B1 as published is WITHDRAWN. The mechanism is real but differently located.

The gate was: *read `displaced` out of `displacement_level` instead of inferring it, and
state the mechanism in one sentence before any repair.* Done. The repair is NOT started,
because what the gate found is not what B1 claimed.

## What B1 claimed (WRONG)

> The deduction rises −51.7 → −120.4 as a seat goes from two to six tight ends, then
> **returns to −51.7 at seven and sticks**. The saturation brake releases exactly when it
> is needed.

## What production actually does — INTERCEPTED, not reconstructed

Three probes in a row got this wrong the same way, by rebuilding a quantity production
computes internally. The authoritative method is to wrap `draft_room.displacement_adjustments`
and record the arguments production hands it. `phase1_intercept.py`:

| TE held | pick | level_TE | displaced | adjustment |
|---|---|---|---|---|
| 2 | 109 | **149.17** | 200.90 | −51.73 |
| 3 | 110 | 144.98 | 200.90 | −55.92 |
| 4 | 133 | 134.34 | 200.90 | −66.56 |
| 5 | 157 | 108.64 | 200.90 | −92.26 |
| 6 | 181 | 80.53 | 200.90 | −120.37 |
| 7 | 182 | 80.36 | 200.90 | −120.54 |
| 8 | 206 | **149.17** | 200.90 | **−51.73** |

Roster fully priced at every state (0 unpriced), so no absence path is involved.

**Two facts, both read rather than inferred:**

1. **`displaced` is CONSTANT at 200.90 — my single best tight end — across the whole
   ladder.** It does not move from two held to eight held. Every variation in the
   adjustment comes from the league level; **my own saturation contributes nothing at all.**
2. **`level_TE` returns to exactly 149.17 at eight held, the identical value it had at
   two held.** It falls 149.17 → 80.36 over picks 109–182 and then jumps back. An exact
   return to the hundredth is a rank landing on the same player: as tight ends are taken
   league-wide, remaining demand shrinks, the rank walks UP the thinning list, and it
   arrives back at the player who sat at that rank when the pool was full.

So the "reset" is real, and it lives in **`replacement_levels`**, not `displacement_level`.

## Two candidate sites, neither yet confirmed

- **The level's round trip.** Rising replacement as a position drains is documented and
  intended; returning to its starting value mid-draft may still be correct. Not yet read out.
- **`displaced` = my BEST tight end, not my weakest startable one.** `displacement_level`
  is documented to measure what the probe EVICTS, and an overwhelming probe should evict
  the weakest occupant of a reachable slot, with the cascade handled by the solve. Getting
  the strongest instead suggests the cascade is not happening. **This is the more suspicious
  of the two and is where Phase 1 resumes.**

## Status

- **B1 as published: WITHDRAWN.** Fourteenth withdrawal of this pass.
- **B1': SURFACED, not yet repaired.** `displaced` is invariant to bench saturation.
- **No repair written.** The gate exists so a fix is not built on a mis-stated mechanism,
  and it just caught one — for the second time on the same defect.
- **Not yet answered:** why `level_TE` jumps 74.82 → 143.63 across 24 picks. It may be
  correct (league-wide TE scarcity raising the anchor) or it may be a rank-target
  discontinuity. It must be read out before B1' is repaired, for exactly the reason this
  file exists.

## Method note, for the plan

Both bad probes shared one root cause and it is now a rule: **never recompute a quantity
production computes internally.** `replacement_levels(pd.DataFrame(board_rows), …)` is not
`point_replacement`; the board's rows are a filtered, scored projection of a different
population. Read production's value or call production's function — do not rebuild it from
its own output.
