# What the engine says about per-position doors, and the fixture shape that settles the rest

Investigated 2026-10-04 to answer a UI question: in a league with no dedicated TE slot, does
tight end still earn its own door? The answer is yes, and the engine's own evidence makes it
urgent rather than stylistic.

## 1. The finding: the board is already blind to TE in a slotless league

`starter_slot_counts` splits every flex slot across the positions eligible for it. Observed:

```
no TE slot  (QB/RB/RB/WR/WR/FLEX/FLEX/FLEX)   QB 1.0  RB 3.0  WR 3.0  TE 1.0
with TE slot (QB/RB/RB/WR/WR/TE/FLEX/FLEX)    QB 1.0  RB 2.667 WR 2.667 TE 1.667
```

So TE does get demand without a dedicated slot -- an even 1/3 of each flex. **That even split is
measurably false.** `starter_slot_counts`' own docstring records the measurement: 24 FLEX slots
go `WR 20 / RB 4 / TE 0` in a league WITH a dedicated TE slot, and **`TE 18 / WR 5 / RB 1` in one
without**. `evidence/roster_shape/flex_share/RESULT_flex_share.md` puts the optimal fielding of
the owner's slotless league at **1.5 tight ends per team** against the assumed 1.0.

The consequence is not subtle. In that evidence's 18-draft probe, the owner's league drafts
**zero tight ends in three of three seats** under the shipped even split, while his own roster
carries two. His words, recorded before the measurement: *"with no TE slot, but flex that can
field them, the TE act as de-facto WR."*

**The fix was built, pre-registered and REJECTED** -- four of nine gates failed, including a
four-tight-end seat the pre-registration named as over-correction. `board_flex_share` returns
`None` so every board stays byte-identical to the even split, pending `#50`.

## 2. What that settles for the UI

**TE keeps its own door in every format, and it is not a close call.** The format where folding
TE into a generic FLEX feels most natural is exactly the format where the engine most
under-serves it. Hiding the position in the UI would make a known engine gap invisible.

The general rule, since "named slot -> door" is too simple: **a position earns a door when it has
distinct demand OR distinct scarcity.**

| case | demand | scarcity | door? |
|---|---|---|---|
| TE, no TE slot | shared via flex | sharply distinct | **yes** |
| DL/LB/DB, named slots | distinct (2 each) | deep pools | **yes** |
| DL/LB/DB, only `IDP_FLEX` | one shared slot | deep pools, no meaningful drain (`§14`) | **compound** |

## 3. A contract the prototypes currently break

`slot_share_basis()` returns `SLOT_SHARE_FIELDED` or `SLOT_SHARE_EVEN_SPLIT`, labelled "measured
from this pool" and "assumed even split". The vocabulary's own comment is binding:

> A share that was MEASURED and a share that was ASSUMED are different facts, and the assumed
> one must never be able to pass for the measured one.

**Every production board today is on `even_flex_split`**, because `compute_draft_board` calls
`board_flex_share`, which returns `None`. No variant in either set renders this basis anywhere.
That is the same defect class as rendering a measured zero as an absence (`#187`) -- an assumed
quantity presented with the authority of a measured one.

So: any surface showing a flex-influenced number must name its basis, exactly as it already names
`depth_basis` and `denial_basis`.

## 4. One code fix that follows

`_src/shared.js` carries `const FLEXIBLE = new Set(["RB", "WR", "TE"])`. That is a hand-written
copy of eligibility the engine already derives from `FLEX_SLOT_POSITIONS` plus the league's own
`roster_positions` (`slot_share_by_position`). It is wrong in superflex, where QB is flex
eligible, and wrong again for `IDP_FLEX`. One home for the vocabulary (`#126`) -- consume the
engine's, do not restate it.

## 5. A documentation defect found in passing

`starter_slot_counts` says the measured branch is "the answer whenever a pool exists, and
compute_draft_board always supplies it." It does not: the seam returns `None`, so the measured
branch never runs on a board. The docstring claims coverage the code does not have (`#133`).

## 6. THE FIXTURE SHAPE

Three captured states from one 1QB offense-only draft cannot answer any of this. The capture run
needs four formats x three states (early / mid / late), carrying the same payload as
`states.json`:

| # | format | roster_positions | what it settles |
|---|---|---|---|
| 1 | control | `QB RB RB WR WR TE FLEX FLEX` | the existing board, unchanged |
| 2 | **superflex** | `QB RB RB WR WR TE FLEX SUPER_FLEX` | the format actually played; QB-in-flex; `SUPER_FLEX_QB_SHARE`; breaks `FLEXIBLE` |
| 3 | **no TE slot** | `QB RB RB WR WR FLEX FLEX FLEX` | TE door with assumed demand 1.0 vs optimal 1.5; the zero-TE behaviour |
| 4 | **heavy IDP** | `QB RB RB WR WR TE FLEX DL DL LB LB DB DB` | 9 doors, 5 surfaced; compound-vs-split; no tanks on defense |

Add `K` and `DEF` to at least one roster so the late-round door slide can be rendered rather than
argued about.

Every one of these questions stops being a debate the moment those exist.

---

## 7. The maximal fixture, measured

Owner's request: every position type at once, so each ambiguity fires in the same board.

`QB RB RB WR WR TE FLEX SUPER_FLEX DL LB DB K DEF IDP_FLEX` -- 14 starters, 9 distinct positions,
three overlapping flex labels, and named IDP slots sitting alongside an `IDP_FLEX`.

The engine takes it without complaint. All nine positions are in `FANTASY_POSITIONS`
(`DB DEF DL K LB QB RB TE WR`) and it knows five flex labels
(`FLEX IDP_FLEX REC_FLEX SUPER_FLEX WRRB_FLEX`). Each resolves:

```
FLEX        -> TE .333  WR .333  RB .333
SUPER_FLEX  -> QB .850  TE .050  WR .050  RB .050
IDP_FLEX    -> DL .333  LB .333  DB .333
```

Resulting per-team demand, which is what nine doors would be built on:

```
WR  2.383    RB  2.383    QB  1.850    TE  1.383    DL 1.333
DB  1.333    LB  1.333    K   1.000    DEF 1.000
                                   total 14.000 vs 14 slots
```

Conservation holds exactly -- no leakage across three overlapping flex types.

**The finding that matters for the doors: demand does not separate these positions.** The whole
spread is 1.00 to 2.38, and `TE 1.383` sits a rounding error from `LB 1.333`. On demand alone a
tight end and a linebacker are the same object. What actually separates them is pool depth -- TE's
is thin, LB's is enormous -- which is the scarcity axis, and precisely why `§14` excludes IDP from
the gauge: an LB tank would never visibly drain.

So the maximal case confirms the design rather than straining it. **Doors must rank on the board's
value order, not on demand**, which is what they already do; and the tank is what makes the
distinction legible, which is why it is offense-only. Nine doors with five surfaced is a sound
model at full roster complexity.

**And a second instance of the assumed-share defect, in the format the owner actually plays.**
`SUPER_FLEX_QB_SHARE = 0.85` is hand-set, and `starter_slot_counts`' own docstring concedes the
measurement "returns QB 1.00 of every SUPER_FLEX at every league size from 8 to 16". So superflex
QB demand renders as **1.850 where the measurement says 2.000** -- the same shape as TE's 1.0
against an optimal 1.5, smaller in size, and live on his own league's board.

| # | format | roster_positions | what it settles |
|---|---|---|---|
| 5 | **maximal** | `QB RB RB WR WR TE FLEX SUPER_FLEX DL LB DB K DEF IDP_FLEX` | nine doors at once; three flex types overlapping; named IDP beside `IDP_FLEX`; K/DEF slide |

