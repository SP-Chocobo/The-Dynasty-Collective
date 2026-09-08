# How the #205 roster proof will be read — written BEFORE the run finished

The engine's own result is the one measurement it is easiest to rationalise. This states, in
advance, what each outcome would mean, so the reading is fixed before the number arrives.

**Instrument:** `run_roster_proof.py`, committed at `ba519a4`. Run started at `ba519a4`.
Six boards, every format run once per seat (seat control), full roster depth derived from each
league's own `roster_positions`.

## Honesty about what I had already seen

This is a pre-registration, not a blind prediction, and the difference matters. Before writing
it I had already run two SHORT smoke runs, and they are not clean evidence for the questions
below — both were truncated well short of a full roster:

| run | depth | cdme | points |
|---|---|---|---|
| 12T_ppr | 4 of 14 rounds | engine 12/12, +187.6% | engine 0/12, −33.7% |
| 12T_ppr_SF | 4 of 14 rounds | engine 12/12, +13.4% | engine 5/12, −0.9% |
| 12T_ppr | 8 of 14 rounds | engine 12/12, +176.5% | engine 0/12, −43.2% |

**These numbers do not answer #205 and must not be quoted as if they do.** At 8 of 14 rounds the
engine had filled 5 of 8 starting slots against a control that fills starters by construction.
That comparison measures WHO FRONT-LOADS STARTERS, not who ends up with the better roster — a
control that fills its lineup first is trivially ahead on a season-points ruler at the halfway
point, and would be even if it drafted badly from there on. The full-depth run is the evidence.

What the short runs DO establish, and what I am therefore not treating as an open question:
the two rulers genuinely disagree, and the machinery is not degenerate (the SF arm shows real
per-seat spread; the 4-round 1QB arm's identical-across-all-seats advantage was a truncation
artifact that disappeared at 8 rounds).

## The two rulers

Reported separately, never collapsed. Measured over the 475-player pool,
`corr(projected_points, universal_value) = 0.241` — these are different questions.

- **cdme** — pre-draft `universal_value`. The engine's own objective.
- **points** — projected season points. The control's objective.

## What each outcome means

**1. Engine ahead on `cdme` only.**
A TAUTOLOGY, and it must be written down as one. It says the engine maximises what it maximises.
It is not evidence the engine is good, and on its own it does NOT satisfy the owner's order to
"confirm it's still effectively generating better rosters". Expected magnitude is large.

**2. Engine ahead on BOTH rulers.**
The strong claim: it beat the control at the control's own game while also winning on its own.
This is the only outcome that closes #205 affirmatively without qualification.

**3. Engine ahead on `cdme`, behind on `points`.**
The most likely outcome and the one needing the most care. It is NOT automatically a defect: a
dynasty engine deliberately declines present points for future value, and every board here is
`dynasty=True`. But it is not automatically fine either — it is exactly what a systematically
mispriced engine would also produce. The deciding question is **magnitude and mechanism**:
  - a small, consistent points deficit with a large cdme surplus is the dynasty trade-off,
    reportable as a known and intended cost;
  - a large points deficit (the −43% of the truncated run, if it survives full depth) is NOT a
    trade-off, it is the engine fielding a materially worse team, and it holds the freeze until
    explained.
I am NOT setting a numeric threshold here, because a threshold invented to fit the sample about
to arrive is exactly the #56 error ("a bound is not a threshold"). The mechanism must be read off
`per_seat` — specifically `engine_starters_filled` vs `starting_slots`. If the engine ends the
draft unable to fill its lineup, that is a legality-adjacent defect and outranks any ruler.

**4. Engine behind on both.**
A freeze blocker. No qualification available.

## What this run CANNOT tell us

- Nothing about K/DEF/IDP boards — #49's input gap is untouched, and no IDP format is in the six.
- Nothing about whether `universal_value` is the RIGHT dynasty objective. This measures whether
  the engine achieves its objective and what that costs in present points; whether the objective
  itself is correct is #50/Phase 3.
- Nothing that rescues #177. Its harness is gone (#208); this supersedes it rather than
  confirming it, whichever way it lands.
- Absolute values are FLOORS wherever `values_are_totals` is false — unpriced players enter the
  lineup solve at 0.0 (#168, reserved). Both arms are exposed identically, so the COMPARISON
  survives that; the absolute numbers do not.
