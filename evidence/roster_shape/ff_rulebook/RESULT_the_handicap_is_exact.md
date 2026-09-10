# The mechanism, closed: upside mode hands each position an exact, derived handicap

Derived from production's own quantities. **No constant chosen, no threshold tuned, no engine
source changed.** Three independent measurements already on disk cross-check it.

---

## The identity

At a flex slot, `displacement_level` fills the phantom with the best free player among the
positions that slot admits: `phantom = max(level over admitted positions)`. For a candidate whose
reachable slots are all held — so the probe evicts that phantom — `displaced == phantom`, and the
board's own composition gives:

```
BALANCED:  bpa + displacement_adj = (points − level_pos) + (level_pos − phantom) = points − phantom
UPSIDE:    bpa alone              =  points − level_pos
```

**In balanced mode the candidate's own positional level cancels EXACTLY.** Every flex-reachable
candidate is compared on raw projected points against one common bar. That is "one slot, one
alternative" doing precisely what its contract says.

**Upside mode zeroes the team-specific terms, so `displacement_adj` goes and the level stops
cancelling.** Relative to the balanced comparison each position gains exactly `phantom − level_pos`.

## The numbers, for this league

Production levels (derived as `projected_points − bpa`, both emitted columns):
QB 243.29 · RB 170.81 · **WR 217.75** · TE 149.17. The FLEX admits {RB, WR, TE}, so
`phantom = 217.75`.

| position | `phantom − level` | what upside mode hands it, at the flex |
|---|---|---|
| WR | 217.75 − 217.75 | **+0.00** — WR defines the phantom, so it gains nothing |
| RB | 217.75 − 170.81 | **+46.94** |
| **TE** | 217.75 − 149.17 | **+68.58** |

**Upside mode gives every tight end a flat +68.58 points over an otherwise identical receiver,
at a flex slot.** That is a derived difference of two production quantities, not a fitted one.

## Three independent cross-checks, all from artifacts already on disk

1. **RESIDUAL2** measured `−68.58` at every seat's 5th pick and recorded it as an uninformative
   constant that "carries zero information" because it was identical across groups. It is
   identical across groups because it is a **structural constant of the league**, and it is this
   handicap. The observation was right; the reading of it was incomplete.
2. **`residual3_raw.json`**: `displaced == 217.75` on **103 of 144** tight-end observations — the
   phantom case is the dominant one, so the exact handicap is the usual case rather than a corner.
3. **Fork Q**: `displacement_adj` is `0.00` on **160 of 160** and **139 of 139** receiver rows, at
   two independent board states. WR pays nothing, as the identity requires.

## Is "WR defines the phantom" a property of this league or of the engine?

**The structure is format-independent, by construction.** The highest-level position admitted by a
slot always pays exactly zero for that slot, because its own level *is* the phantom. Which position
that is depends on the league.

Measured by calling production's `starter_slot_counts` + `replacement_levels` on the real priced
pool under seven roster shapes:

| roster shape | tops the FLEX | tops SUPER_FLEX |
|---|---|---|
| Fourth and Forever | **WR (218)** | QB |
| classic 1QB redraft | **WR (212)** | — |
| superflex, 2 flex | **WR (223)** | QB |
| TE-premium 2TE | **WR (237)** | — |
| RB-heavy 3RB | **WR (237)** | — |
| REC_FLEX league | **WR (220)** (REC_FLEX) | — |

WR tops the FLEX in every shape that has one. QB tops SUPER_FLEX. So the tight-end handicap is not
an artifact of this rulebook — though its SIZE is league-specific, since it is a difference of that
league's own levels.

**Caveat on the QB column, stated because the number is wrong for production:** this scope check
passes `startable_floors=None`, so its QB levels (329.0) are the plain demand-rank model, not
production's, which uses `qb_startable_floor` in a superflex league and yields 243.29. The FLEX
conclusion is unaffected — FLEX does not admit QB — and the SUPER_FLEX conclusion holds under
either number, since both exceed WR's 217.75.

## Scope of the exact figure

The `+68.58` applies to a candidate whose reachable slots are **all held**, so the probe evicts
the phantom — 103 of 144 tight-end observations in the measured window. Two other cases exist and
carry a different number: a candidate with an **open dedicated slot** has `displaced == his own
level`, so the adjustment is 0.0 and there is no handicap to remove; a candidate evicting **one of
my own starters** has `displaced > phantom` and therefore a larger charge, so upside mode hands
him more than `phantom − level_pos`.

## What this settles, and what it does not

**Settles the mechanism.** PHASE4 measured that the mode boundary carries 63% of the excess and had
no account of why. Fork Q showed the zeroed term was the counterweight. This closes it: the
counterweight is *exactly* the term that makes the positional level cancel, and removing it hands
each position a computable constant. The chain from constant to outcome is now complete and
arithmetic.

**Does NOT say the handicap is wrong.** Per the standing prohibition, the observed roster shape is
not evidence about whether the normalization is desirable. What has changed is only that the
question can now be asked against an exact number instead of a rate: *should a tight end receive
+68.58 points over an identical receiver for a deep-bench flex seat?* That is the owner's
question, and it is the same one `CONTRACT_deep_bench_cross_position.md` found the contract does
not answer.

**Proposes nothing.** No level tuned, no penalty added, no threshold moved, no normalization
altered, and specifically not "force balanced" — already measured and rejected by PHASE4.
