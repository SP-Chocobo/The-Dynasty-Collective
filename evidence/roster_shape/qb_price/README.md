# #216 defect (b), measured at last: the quarterback is priced by `need_bonus` and nothing else

`run_216_qb_price_probe.py`. One draft per format, engine seat 1 against `run_roster_proof`'s
control, the board exactly as shipped. **Nothing is toggled and nothing is patched** — this is a
description of the engine, not an ablation.

Defect (b) has been named in every report on #216 and measured by none of them. Here is the whole
chain, at every turn: league starter demand at QB -> the rank it produces -> the replacement LEVEL
actually subtracted -> `bpa` for the best quarterback left, beside every term that could price him
instead.

## 1QB (12T_ppr): seven consecutive turns at a number that never moves

| rnd | QB demand | LEVEL USED | best QB | proj | **bpa** | need | **waiting_cost** | final |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 328.6 | Josh Allen | 372.5 | **43.86** | 4.00 | 57.31 | 48.11 |
| 2 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 46.71 | **4.00** |
| 3 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 63.58 | **4.00** |
| 4 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 46.71 | **4.00** |
| 5 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 46.71 | **4.00** |
| 6 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 38.96 | **4.00** |
| 7 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 38.96 | **4.00** |
| 8 | 1 | 328.6 | Patrick Mahomes | 328.6 | **0.00** | 4.00 | 34.14 | **4.00** — taken here |

**The level never moves: 328.6 at every one of the fourteen rounds.** That part is correct and
documented — while picks come off the top, rank shrinkage and pool drain cancel exactly. What
happens instead is that the best remaining quarterback CATCHES DOWN to that fixed level: once
league demand falls to 1, the rank is 1, and the replacement at rank 1 is the best remaining
quarterback himself. `bpa = 328.6 - 328.6 = 0.00`, by construction, for as long as the slot stays
open.

So from round 2 to round 8 the engine's price for the best quarterback alive is **4.00 at every
single state** — that is `need_bonus` for one unfilled dedicated slot and nothing else. Patrick
Mahomes and a replacement-level quarterback carry the identical number. He is drafted at round 8
not because anything valued him but because the rest of the board finally fell below 4.00 (DK
Metcalf was 5.46 at round 7).

**And a quantity the engine already computes disagrees, at exactly those states.**
`waiting_cost` — his projection over the end-of-draft free alternative — reads **34 to 64 points**
across the same seven turns. It is not zero, it is not flat, and it is not consulted:
`waiting_cost` is observable-only under #48's ruling.

## Superflex: the defect DOES NOT OCCUR, and the reason is already in this codebase

| rnd | QB demand | LEVEL USED | best QB | proj | bpa | final |
|---|---|---|---|---|---|---|
| 1 | 22.2 | **207.5** | Josh Allen | 372.5 | 164.96 | 170.02 |
| 4 | 2.7 | **207.5** | Tyler Shough | 299.7 | 92.17 | 96.55 |
| 6 | 1.85 | **207.5** | C.J. Stroud | 294.5 | 86.96 | 91.39 |
| 8 | 0 | **207.5** | Daniel Jones | 281.9 | 74.39 | −8.36 |

In superflex the QB level is **207.5 at every round**, and it comes from `startable_floors` —
`qb_startable_floor`'s cliff-anchored count of remaining quarterbacks projecting above a
stability-basin threshold — NOT from the demand rank. The demand rank falls to 2, then to None,
and the level does not care. Quarterbacks stay priced the whole way down. Same in the owner's
league (level 207.5, bpa 164.96 -> 74.39).

**The cure for defect (b) already exists, is already derived rather than invented, and is applied
to exactly one case.** `replacement_levels`' own docstring says so: startable floors are
"currently only QB in a superflex league". Wherever they apply, the rank-1 degeneracy cannot
happen, because a cliff in the projection curve — not a headcount — defines the boundary.

## Two things that are NOT established, stated so nobody re-derives them

1. **The seven-round duration is partly the control's.** League QB demand collapses 12 -> 1
   between round 1 and round 2, which means all eleven control seats took a quarterback with
   their first pick. That is `run_roster_proof.control_pick` doing what it does — fill an unmet
   slot with the best raw projection, and quarterbacks project highest in raw points. A real
   12-team 1QB room does not do that. **The MECHANISM and the 0.00 belong to the engine; the
   TIMING belongs to the control.** In a real draft the collapse arrives later — around the
   rounds a manager actually wants a quarterback, which is the window that matters.
2. **Extending the startable floor to 1QB has NOT been measured.** It is the obvious candidate and
   it would be the third change to the replacement anchor in this pass; the flex share was the
   second and it failed four of nine gates. Nothing gets wired here without its own
   pre-registration and its own ablation. The anchor is #50 and the owner's.

## An instrument defect caught before publishing

The first version of this probe printed "the rank-th best remaining QB" as the replacement level.
That is right on the demand-rank branch and **WRONG on every superflex row**, where the level
comes from the startable floor — it would have reported 299.7 where the engine used 207.5, and the
superflex half of this finding would have been nonsense. The column now recovers the level from
the row itself (`level = projected_points - bpa`), which is true on both branches because it is
read from the answer rather than from a model of the answer.

## The obvious remedy, REJECTED ON DERIVATION before spending a measurement on it

Superflex avoids defect (b) because `startable_floors` sets the QB level. So: extend the startable
floor to 1QB. It is the natural next move, the mechanism already exists, and its constants were
derived by stability basin rather than invented (#56-clean). **It is still wrong, and the
arithmetic says so without a draft:**

| format | QB pool | floor (0.5 x QB12 = 164.3) | QBs ABOVE floor | league QB demand | level under the FLOOR rule | level under the DEMAND rule | QB1 bpa: floor vs demand |
|---|---|---|---|---|---|---|---|
| 12T_ppr | 42 | 164.3 | **32** | **12.00** | 207.5 | 328.6 | **164.96** vs 43.86 |
| 12T_ppr_SF | 42 | 164.3 | **32** | **22.20** | 207.5 | 299.7 | 164.96 vs 72.79 |

The startable floor answers **"how many quarterbacks in this pool are startable at all"** — 32, a
property of the projection curve. That is the right question in superflex, where 22 of them are
actually started and the two numbers are close. In a 1QB league only **12** are started, and the
floor would price every quarterback against QB32 instead of QB12: Josh Allen's `bpa` goes
**43.86 -> 164.96, a 3.8x inflation**, in a format that fields one quarterback per team. The
engine would open the draft with a quarterback. That is the over-correction, the same shape as
#219's four-tight-end seat, and it is visible on paper.

## So what defect (b) actually is

Not a badly chosen replacement level. **VOR is a model of a market for N starting slots, and at
N = 1 with only me still bidding there is no market to model.** The rank-1 level resolving to the
best remaining player is not a bug in the arithmetic; it is the arithmetic correctly reporting
that a competitive-alternative model has nothing left to say.

What prices the last slot is not a better alternative — it is the **cost of waiting**, and this
engine already computes two of those: `waiting_cost` (against the end-of-draft free alternative,
34-64 points at exactly the states where `bpa` reads 0.00) and `positional_forfeit` (against the
next turn). `replacement_levels`' own docstring reaches the same conclusion from the other
direction: "the quantity that would price it is horizon_replacement's floor, observable-only by
#48's ruling."

**Defect (b) is therefore not an implementation gap. It is #48's ruling meeting a state where the
observable-only quantity is the ONLY quantity with anything to say**, and admitting it into
selection is #50 and the owner's. Recorded here so the next pass does not spend itself
re-deriving a better anchor for a slot that does not have one.
