# The dynasty premium costs ~100 realized points on a single-season ruler — and that is not a defect

## The measurement

`run_backtest_grade`, **2023**, `12T_ppr_K_DEF`, seat 1, the SHIPPED path (`--streaming`, no
monkey-patching), on a pool and board that are both period-correct:

| horizon | engine | field | delta | first K/DST |
|---|---:|---:|---:|---:|
| dynasty (`settings.type == 2`) | 2656.7 | 2741.6 | **−84.9** | 7 |
| **redraft** | 2750.3 | 2732.5 | **+17.7** | 9 |

**A +102.6 swing from clearing one flag.** The engine goes from losing the seat to winning it.

## What it means

`draft_room` gates `time_horizon_adj` on `settings.type == 2`: in a dynasty league every priced
row carries an adjustment built from the gap between its THREE-YEAR outlook and its season
projection. Measured on the 2024 board, 258 of 1181 rows change.

That is the engine deliberately buying value it will collect in a season this ruler does not
score. Charging it for that and calling the result a defect would be grading a multi-year
objective against a single-year outcome. **The dynasty arm is the shipped configuration and the
redraft arm is the horizon-matched one; neither may be quoted alone.**

There is a second, less flattering half, and it is why this file exists rather than a footnote:
the three-year outlook is the **2026 vendor's**, so in a 2023 draft it is a forward-looking
ranking formed after the season was played. Part of that 102.6 is the engine being paid for
hindsight it should not have, and this measurement cannot separate the two. What it does settle
is the direction and the order of magnitude.

## It also explains why 2023 grades harder than 2024

2023 is one more year of that hindsight than 2024, applied to a season whose outcomes the
outlook partly encodes. Consistent with the measured gap:

| season | base | + `#30` streaming |
|---|---:|---:|
| 2024 | 0/12, −346.9 | 3/12, −18.5 |
| 2023 | 0/12, −384.7 | 1/12, −218.9 |

Named as a candidate in `ANACHRONISM.md` **before** this was run, and now measured at ~100 points
on one seat. Not the whole gap; a real part of it.

## A withdrawal

An earlier run of this same arm found redraft **worse** (−772 vs −689) and I recorded it as
ruling the dynasty horizon out as a cause. That run was on the contaminated board — the one whose
late-round candidate window was entirely undraftable phantoms — and its conclusion is withdrawn.
On the corrected board the sign is the other way.

The lesson is the same one as the ghosts: a null result from a broken instrument is not a null
result. It reads exactly like one.

## What is NOT established

- **One seat, one season, one format.** A 12-seat run of both horizons is the next step.
- **How much of the 102.6 is legitimate dynasty preference and how much is 2026 hindsight.**
  Separating them needs a period-correct three-year outlook, which this repository does not have
  and cannot fabricate.
- Nothing here argues the engine should stop being a dynasty engine. It argues that a
  single-season ruler under-reports a dynasty drafter by roughly this much, and that every
  absolute figure from this instrument should be read with the horizon it was measured under.
