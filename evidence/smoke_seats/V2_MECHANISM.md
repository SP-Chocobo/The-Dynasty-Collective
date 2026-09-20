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

The proposed salvage is a longer horizon: baseline at the starters-exhausted index
`k_exhaust` rather than at the next turn. But `replacement_levels` sets the replacement rank
to exactly the league's remaining starter demand -- `teams x slots(P)` -- which IS
`k_exhaust`, and `BPA` is DEFINED as `points - replacement_level(P)`. So `BPA(k_exhaust) = 0`
by construction and

```
regret_longhorizon(i) = F(i) - F(k_exhaust) ~= F(i) - 0 = F(i)
```

which is v1's key. Measured -- `F` at the starters-exhausted index:

```
format        pos   slots/tm  k_exh   F(0)    F(k_exh)   U(k_exh)
12T_ppr       QB        1.00     12   59.00      -2.50      -6.50
12T_ppr       RB        2.67     32   60.60       1.43      -7.24
12T_ppr       WR        2.67     32   87.75       3.94      -4.73
12T_ppr       TE        1.67     20   59.12      -6.61     -11.28
12T_ppr_SF    QB        1.85     22  186.81     +82.28     +77.43   <-- EXCEPTION
12T_ppr_SF    RB        2.72     33   60.84       1.47      -7.25
12T_ppr_SF    WR        2.72     33   87.99       4.07      -4.65
12T_ppr_SF    TE        1.72     21   60.79      -5.16      -9.88
10T_ppr       QB        1.00     10   58.00       2.73      -1.27
10T_ppr       RB        2.67     27   55.39       4.31      -4.36
10T_ppr       WR        2.67     27   82.08       1.77      -6.90
10T_ppr       TE        1.67     17   55.85      -5.25      -9.92
```

Eleven of twelve cells land within `[-6.61, +4.31]` of zero. **There is no new formulation to
find at the long horizon: v1 IS regret evaluated at the full horizon, and v2 is its one-gap
truncation.** The correct rule is the one that was already shipping.

### 5a. OPEN QUESTION: superflex QB does not obey this

`F(k_exhaust) = +82.28` and `U(k_exhaust) = +77.43` for superflex QB -- nowhere near zero,
where every other cell is. The superflex QB replacement level does not sit at the
starters-exhausted index. Either a startability floor truncates the demand rank, or the
`SUPER_FLEX_QB_SHARE` path and the starter-demand path disagree about how many quarterbacks
a superflex league starts.

Not diagnosed here, and NOT repaired here (`#184`: this is engine design, and it goes to the
owner). Recorded because it is the one position-format cell where the collapse fails, and it
is the same cell where v2's damage was worst.

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

1. **Revert the selection authority.** `pick_synthesis.py:1794` back to `_board_order`.
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

4. **`5a` goes to the owner** as an engine-design question.
