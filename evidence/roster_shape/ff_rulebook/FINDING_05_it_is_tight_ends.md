> **PARTIALLY CORRECTED — see RESULT_aggregate_selection.md.** Two things in this file are
> withdrawn. (1) The "priced pool offers" row of the table below is the 764-row VENDOR board,
> retracted by CORRECTION_wrong_universe.md; the real priced pool is QB 8.7 / RB 26.2 /
> WR 41.2 / TE 23.9 over 481 priced rows, so the engine's 32.4% is **1.36x** the pool's TE
> share, not the 1.74x claimed here. (2) The MECHANISM paragraph ("VOR measured against a
> collapsed level stays positive for every remaining body") is superseded: the level cancels
> wherever displacement is non-zero, and the tight ends being taken are overwhelmingly
> NEGATIVE-bpa (the 312 cut sits at bpa ≈ −142). The engine-vs-human comparison — 32.4%
> against 15.5%, both on the real universe — is UNAFFECTED and stands.

# THE DEFECT IS TIGHT ENDS, NOT RECEIVERS

A complete 12x26 startup on Fourth and Forever's real rulebook, all twelve chairs driven by
the production engine, real universe (6,595), real season projections (5,346) scored under
this league's own settings. 312 picks, 1,125 seconds. `ff_draft.txt`, `ff_draft.json`.

## The result

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| priced pool offers | 14.3% | 28.2% | 38.9% | **18.6%** |
| twelve real managers | 20.0% | 27.4% | 37.1% | **15.5%** |
| **the engine, this rulebook** | **10.3%** | **26.9%** | **30.4%** | **32.4%** |

**The engine drafts 101 tight ends out of 312 picks.** From a pool that is 18.6% tight end,
it allocates 32.4% -- 1.74x the pool's own share. Every seat finishes with between 5 and 12
tight ends; the median is 8. The twelve humans took 3 to 6.

Running backs are *fine*: 26.9% engine against 27.4% human and 28.2% pool. Receivers are
UNDER-drafted here, not over: 30.4% against 37.1%.

## The drift is unmistakable

| quarter | QB | RB | WR | TE |
|---|---|---|---|---|
| picks 1-78 | 30.8% | 29.5% | 25.6% | 14.1% |
| picks 79-156 | 7.7% | 21.8% | **52.6%** | 17.9% |
| picks 157-234 | 2.6% | 28.2% | 19.2% | **50.0%** |
| picks 235-312 | 0.0% | 28.2% | 24.4% | **47.4%** |

The back half of the draft is HALF tight ends.

## I had the wrong target, and this file says so

Everything before FINDING_05 chased a WR over-allocation, because the 49-seat battery
produced 48.9% WR. **That does not reproduce on the owner's real rulebook.** The battery
formats are mostly 1QB with different rosters and different scoring; the WR figure was a
property of those formats, not of the engine. Thirteenth withdrawal this session.

What survives from the earlier findings is the MECHANISM, which turns out to point at tight
ends once it is run on the right league:

- **FINDING_02** showed VOR stops measuring scarcity once a position's demand is satisfied.
- **FINDING_04** measured the specific consequence for TE and predicted this result before
  the draft landed: at the late drain state, one-slot-one-alternative says a tight end
  projecting 30 against a 95 flex alternative should net **-65**; the engine nets him **-6**.
  A 59-point under-charge, caused by the documented non-positive rule capping the deduction
  at `level_TE - my_own_TE` rather than letting it reach the flex alternative.

TE's own replacement level COLLAPSES (20 at drain 40, against WR's 95) because its pool is
shallow and its demand is satisfied early. VOR measured against a collapsed level stays
positive for every remaining body, and the displacement term -- bounded by my own roster --
cannot claw it back. So tight ends keep pricing positive, forever, and the engine keeps
taking them.

This is #155 ("a replacement-level player prices at 0.00 tautologically") surfacing as a
live selection defect rather than a pricing curiosity.

## The QB ceiling, confirmed on the real rulebook

**Nine of twelve seats take exactly 2 quarterbacks.** In a SUPERFLEX league, where QB and
SUPER_FLEX are both started every week, two quarterbacks is the starting requirement with
zero backup. The engine takes 10.3% QB where twelve humans took 20.0%.

This is Fable's predicted hard ceiling -- "with F_p = 1 a third body can never be promoted
by an absence" -- now observed live, on the owner's own league, rather than inferred. It is
the same defect wearing the other face: a body that cannot improve today's lineup is priced
at nothing, whether it is a backup quarterback or an eighth tight end. One of those two
errors makes the engine take too few; the other makes it take too many.

## Status

NO ENGINE CODE HAS BEEN CHANGED. This is the evidence half of "evidence before repair".
The repair has a target now -- and it is not the one I started the night with.
