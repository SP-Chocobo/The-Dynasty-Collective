# Why the acting_now ordering lost 6% — the mechanism, measured

Companion to `V2_REGRESSION.md`, which established THAT v2 lost. This establishes WHY, and
it changes the recommendation from "revert on the evidence" to "revert, because the rule is
provably the wrong shape."

Arms: v1 `9273a2c` (sort on `final_score`) against v2 `4640f25` (sort on `acting_now_value`).
Probes: `probes/curve_shape.py`, `probes/curve_depth.py`, `probes/sf_level_shift.py`,
`probes/horizon_collapse.py` in this directory. Every table below is reproducible from the
capture with no network.

## 1. The cdme "win" was entirely bench

Mean change v1 -> v2, engine seat, across all six formats:

```
cdme starter_value   -58.38      cdme bench_value   +70.56
points starter_value -137.45     points bench_value   +9.57
```

`cdme` starter value is DOWN in five of six formats. The whole `+6.490` advantage on the
engine's own scale is bench. `run_roster_proof.COMPARE_ON` compares `cdme` on `total_value`
(whole roster) and `points` on `starter_value` (optimal lineup), and 83.8% of the pool's
`universal_value` is negative, so `total_value` is an ASSET-STOCK quantity: "how many
positive-VOR players do I own." v2 optimised stock and paid for it in lineup.

This is not a leak. `reference_values` is computed with `picks=[]` and `my_roster_id=None`,
so the ordering key is not in the score. The ruler is measuring the wrong thing for this
question, and must not be read as evidence that v2 is directionally right.

## 2. Composition inverted

Engine picks by position, all six formats summed, v1 -> v2:

```
QB 105 -> 79      RB 234 -> 249      WR 494 -> 264      TE 141 -> 382
```

In `12T_ppr` that is ~6.2 tight ends and ~3.7 wide receivers per roster, against v1's
WR 7.25 / TE 2.0, in a league with one TE slot and three WR slots.

## 3. The key is a GRADIENT, and it discards the curve's HEIGHT

A first hypothesis -- "TE has a steeper top-of-curve cliff, so regret takes TE" -- was
MEASURED AND IS FALSE. `12T_ppr` pre-draft, decay from the top of the `final_score` curve:

```
pos    rows     best     n=1     n=2     n=3     n=4     n=6     n=8
QB       40    59.00   39.09   39.17   42.18   44.91   50.67   53.40
RB      123    60.60    6.88   12.47   14.78   16.68   24.07   25.10
WR      198    87.75   23.72   24.01   27.48   35.75   48.43   52.32
TE      115    59.12    1.16   30.38   36.40   42.47   45.52   47.47
```

At n=1 TE decays LEAST. At the measured `expected_taken` (QB 0.82 / RB 3.48 / WR 3.96 /
TE 2.26) top-of-board regrets are QB ~32.0 / RB ~15.7 / WR ~35.4 / TE ~31.9, predicting WR
should lead. The engine does the opposite, so the top-of-curve story is not the mechanism.

What is: `acting_now(i) = F(i) - F(i + expected_taken)` is a numerical derivative. Measuring
value and regret together DOWN the curve, `expected_taken` held at the measured values:

```
12T_ppr  --  value vs regret at depth k
  k    QB val    QB reg    RB val    RB reg    WR val    WR reg    TE val    TE reg
  0     59.00     32.05     60.60     15.69     87.75     35.42     59.12     31.95
  2     19.83      2.47     48.13     10.47     63.74     24.22     28.74     12.37
  4     14.09      2.74     43.92      7.90     52.00     16.50     16.65      3.40
  6      8.33      2.05     36.53      9.83     39.32      6.45     13.60      2.12
  8      5.60      1.27     35.50     14.11     35.43      7.06     11.65      2.45
 12     -2.50      5.17     21.14      4.57     28.35      8.12      2.86      1.78
 16    -22.18      1.90     15.98      2.14     20.17      4.77     -1.16      1.09
 20    -45.17      0.41     13.81      1.26     15.38      5.44     -6.61      4.21
 30   -208.35      3.81      4.68      3.58      4.96      1.60    -23.08      3.03
```

Bottom row: a quarterback worth **-208.35** generates more regret (3.81) than a running back
worth **+4.68** (3.58), so under `_acting_now_order` he outranks him. `team_acquisition_value`
breaks only EXACT float ties, which do not occur. `expected_taken` sets the step length, so
correcting it moves WHERE the slope is read; it can never reintroduce HEIGHT as a term.

`need_bonus` cancels in the subtraction, so "I already hold five tight ends" cannot suppress
a sixth either -- the suppression term is present in both operands and vanishes.

## 4. SUPERFLEX IS A PURE LEVEL SHIFT, AND v2 CANNOT SEE IT

`SUPER_FLEX_QB_SHARE` reaches the board through `starter_slot_counts` -> `replacement_levels`,
and `BPA = projected_points - replacement_level(P)`. Moving a replacement level subtracts the
same amount from every player at that position. A level shift is invisible to a difference.

QB `final_score` curve, `12T_ppr` against `12T_ppr_SF`, same pool, same everything else:

```
  k    1QB val     SF val  LEVEL diff   1QB reg    SF reg  SLOPE diff
  0      59.00     186.81      127.81     39.09     39.05       -0.04
  4      14.09     142.98      128.89      3.34      3.38        0.04
 12      -2.50     125.23      127.73      6.31      6.07       -0.24
 30    -208.35     -82.54      125.81      4.65      5.61        0.96

40 rows compared
LEVEL shift  mean +127.14   min +124.73   max +129.00
SLOPE change mean   +0.08   min   -2.12   max   +3.00
```

**The entire superflex revaluation of the quarterback position -- +127.14 points per player --
produces a mean slope change of +0.08.** v2's ordering key cannot distinguish a superflex
league from a 1QB league.

That is the measured cause of `#20`: QB 105 -> 79 overall, worst in the superflex formats
(`12T_ppr_SF` 31 -> 13, `10T_ppr_SF` 25 -> 16). The pace convention was the ONLY channel left
through which superflex could reach the order, which is why wiring it raised the QB minimum
from 1 to 2 and could not restore the count, and why it stops mattering past pick 48
(`SUPERFLEX_QB_PACE_ANCHORS`' last anchor).

Generalised: `replacement_levels` does two jobs -- it sets absolute value AND it encodes
positional scarcity. `acting_now_value` cancels it exactly, so it discards the second job
while keeping the engine's dependence on it everywhere else.

## 5. LONG-HORIZON REGRET COLLAPSES TO v1

**CORRECTED 2026-09-20 (`#23`). The conclusion stands and is STRONGER than first published;
the evidence offered for it was partly wrong. Both are restated in full below.**

The proposed salvage is a longer horizon: baseline at the point where the position's startable
supply is exhausted rather than at the next turn. But `bpa` is DEFINED as
`projected_points - replacement_level(P)`, so `bpa` is exactly 0 at whatever rank the board's
own replacement sits at, and therefore

```
regret_longhorizon(i) = F(i) - F(replacement_rank) ~= F(i) - 0 = F(i)
```

which is v1's key. Measured against each position's OWN replacement basis, four formats x four
positions:

```
format      pos  basis                  repl rank  bpa@rank   U@rank   F@rank
12T_ppr     QB   live_starter_demand           11      0.00    -0.27     3.73
12T_ppr     RB   live_starter_demand           31      0.00    -7.56     1.11
12T_ppr     WR   live_starter_demand           31      0.00    -3.71     4.96
12T_ppr     TE   live_starter_demand           19      0.00    -5.83    -1.16
12T_ppr_SF  QB   startable_floor               28      0.00    -1.18     3.67
12T_ppr_SF  RB   live_starter_demand           32      0.00    -7.25     1.47
12T_ppr_SF  WR   live_starter_demand           32      0.00    -2.55     6.17
12T_ppr_SF  TE   live_starter_demand           20      0.00    -9.36    -4.64
10T_ppr     QB   live_starter_demand            9      0.00    -0.95     3.05
10T_ppr     RB   live_starter_demand           26      0.00     1.03     9.70
10T_ppr     WR   live_starter_demand           26      0.00    -6.30     2.37
10T_ppr     TE   live_starter_demand           16      0.00   -10.00    -5.33
10T_ppr_SF  QB   startable_floor               28      0.00    -1.18     3.67
10T_ppr_SF  RB   live_starter_demand           26      0.00     1.03     9.75
10T_ppr_SF  WR   live_starter_demand           26      0.00    -6.49     2.23
10T_ppr_SF  TE   live_starter_demand           16      0.00   -10.00    -5.28

worst |bpa| at any position's own replacement rank: 0.00
```

**Sixteen of sixteen, exactly 0.00.** `bpa` is anchored at the replacement rank whichever arm
of `replacement_levels` chose that rank. **There is no new formulation to find at the long
horizon: v1 IS regret evaluated at the full horizon, and v2 is its one-gap truncation.** The
correct rule is the one that was already shipping.

### 5a. WITHDRAWN — the "superflex QB anomaly" was MY INSTRUMENT, not the engine

**What this section published, and it is wrong:**

> `F(k_exhaust) = +82.28` and `U(k_exhaust) = +77.43` for superflex QB -- nowhere near zero,
> where every other cell is. The superflex QB replacement level does not sit at the
> starters-exhausted index. Either a startability floor truncates the demand rank, or the
> `SUPER_FLEX_QB_SHARE` path and the starter-demand path disagree about how many quarterbacks
> a superflex league starts.

It also published the headline "eleven of twelve cells land within `[-6.61, +4.31]` of zero",
which understated the result: it is sixteen of sixteen at exactly zero.

**What is actually true.** `replacement_levels` has TWO arms, and the first disjunct of that
guess is the answer -- but it is a DESIGN, not a truncation. For a position carrying a
`startable_floor` (today only QB in a superflex league), the replacement rank is the count of
REMAINING players projecting at or above an absolute threshold, NOT the `teams x slots` demand
headcount. The board reports which arm priced each row, per row, in `replacement_basis`.
Measured on this fixture:

```
12T_ppr      replacement_basis=live_starter_demand   bpa crosses 0 at rank 11  (demand 12.0)
12T_ppr_SF   replacement_basis=startable_floor       bpa crosses 0 at rank 28  (demand 22.2)
             QB startable floor = 163.50 points; 29 QBs clear it
```

`probes/horizon_collapse.py` computed `teams x slots(P)` for every position and never read
`replacement_basis`. On superflex QB that reads the curve six players early, where bpa is
legitimately `+79.00` on a scale anchored at 28. The +82.28 is the probe's error, reported as
the engine's.

**Why it is a design and not an oversight**, from `replacement_levels`' own docstring: a flat
per-team "bench QB demand" constant for superflex was tried and REVERTED, because real QB
projections have a genuine cliff around rank ~27-30 and any fixed constant either landed short
of it or overshot past it -- measured, 0.3 vs 0.4 extra demand moved one quarterback from 7th
to 4th overall. The floor keys off the projection curve's own discontinuity instead, which is
why it is stable where the constant was not. That is `#56` reasoning applied correctly, and my
section flagged it as a suspected defect.

**Consequences, stated so nobody has to re-derive them:**

- `#23` is CLOSED as NOT A DEFECT. There is no engine question here for the owner.
- Section 5's conclusion is unaffected and strengthened: the collapse is universal.
- It does NOT change section 4. Superflex reaching the board as a LEVEL shift of +127.14 per
  quarterback against +0.08 of slope is measured on the shipped board with whichever arm
  priced it, and the reverted ordering could not see it either way.
- The guard that would have caught this now exists: `test_replacement_basis_vocabulary.
  OnTheRealBoardTests.test_bpa_is_zero_at_the_replacement_rank_WHICHEVER_BRANCH_SET_IT`,
  with a non-vacuity companion pinning that the two arms really do pick different ranks.
  Mutation-checked 1/10: disabling the floor arm fires only the non-vacuity guard (correct --
  the anchoring still holds), and shifting the level off the replacement rank fires the
  invariant on 7 of 8 cells.

**The lesson, since it is the third instrument error in this file's lineage.** An instrument
that recomputes a quantity the engine already publishes will eventually disagree with it, and
the disagreement will read as an engine defect. `replacement_basis` existed on every row the
whole time. The probe asked the pool a question instead of asking the board its answer.

## 6. What this rules out

- **Ratio forms** -- the curve reaches -208.35; ratios across zero and across negatives are
  not defined in any useful way here.
- **Regret as a multiplier on value** -- requires a conversion between value-points and
  regret-points. That is a calibration, and `#56` forbids it.
- **A demotion threshold** -- the motivating defense had forfeit `0.13`, strictly positive, so
  no `> 0` test catches it and any band is tuned on that one case.
- **Position special-cases for K/DEF** -- forbidden by stated principle
  (`draft_room.py:1199-1201`).

## 7. The remaining live proposal, and where it now ranks

The two-position swap algebra IS correct: for "fill P now and Q next turn" against "Q now and
P next turn",

```
plan_A - plan_B = [F(i_P) - next(P)] - [F(j_Q) - next(Q)] = acting_now(P) - acting_now(Q)
```

exactly as `positional_forfeits` derives it. Its PRECONDITION is that the roster is committed
to acquiring BOTH positions. v2 applies it to every candidate, including ones the roster will
never roster -- which is what makes the -208.35 quarterback sortable at all.

The precondition-restoring form -- give regret authority only ACROSS POSITIONS WITH AN UNMET
REQUIREMENT this roster will fill -- introduces no constant, hand-lists nothing, and is not a
position special-case. It remains the one salvage worth testing.

But section 5 demotes it: if v1 already is the full-horizon rule, the swap correction is a
refinement of a rule that is already right, not a repair of one that is wrong. It belongs
after the valuation fix, not instead of it.

## 8. Recommendation

**STATUS 2026-09-20: item 1 is DONE (`ea697f7`), item 4 is WITHDRAWN, items 2 and 3 are open.**

1. **DONE.** **Revert the selection authority.** `pick_synthesis.py:1794` back to `_board_order`.
   KEEP computing `acting_now_value` and `position_next_turn_value` as carried observables --
   the `final_score`-curve fix and the `need_bonus` cancellation are correct, and the numbers
   belong on the card and in the debate. Correct the now-false "NO SELECTION AUTHORITY"
   paragraph at `draft_strategy.py:427-433` in whichever direction the freeze lands.

2. **Fix K/DEF where the defect is: valuation.** A defense at `team_acquisition_value 34.47`
   claims a ~34-point DEF1-DEF12 projected spread is bankable. A per-position
   forecast-reliability shrink on `bpa`, DERIVED from `measure_projection_accuracy` (`#18`),
   fixes K/DEF under a plain value sort without touching QB/RB/WR ordering. Blocked on `#18`'s
   network access.

3. **The take model (`#21`) is a separate bug.** 60.4 predicted takes against 132 actual, and
   a 0.02 floor across ~1,100 rows that leaves an opponent's own rank-1 player 97.6% safe from
   them. Real, but it cannot rescue v2 -- section 3 -- and after the revert it carries no
   selection authority again.

4. **WITHDRAWN.** This read *"`5a` goes to the owner as an engine-design question."* There is
   no question: `5a` was an error in my own probe, not a defect in the engine, and `#23` is
   closed as NOT A DEFECT. See `5a` for the correction and for the guard that now holds it.
