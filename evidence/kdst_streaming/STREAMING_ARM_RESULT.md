# `#30`: the derived streaming replacement level is worth **+258.8 realized points a seat**

**2024, `12T_ppr_K_DEF`, 12 seats, graded on realized outcomes, under
`run_backtest_grade.period_correct_pool`.** One process, one code version, one toggle:
`replacement_levels` for K and DEF replaced by the DERIVED streaming baseline.

> These numbers REPLACE the confounded ones this file used to carry (+226.6, base 7/12). That
> run drafted from a pool containing 101 players who were not in the league in 2024, priced
> from the 2026 vendor export. See `evidence/backtest/ANACHRONISM.md`. The direction survived
> the correction; the magnitude and — far more importantly — the absolute grades did not.

| arm | wins | mean delta vs field | median | first K/DST rounds |
|---|---|---:|---:|---|
| base | 0 / 12 | −640.95 | −634.91 | **4, 5** |
| **streaming** | 0 / 12 | **−363.08** | **−372.75** | **7, 8** |

**Paired, per seat (streaming − base): mean +258.83, median +249.09, improved 12 of 12.**

Distinct rosters: the streaming arm produces 11 distinct rosters across 12 seats (seats 3 and 4
collapse), giving mean −353.98 over the independent samples. The base arm produces 12.

## Read this correctly

**The correction works and it is large.** Twelve of twelve seats improve, the shape moves from
rounds 4–5 to rounds 7–8, and the gain is a quarter of a season's worth of points on a ruler the
engine cannot optimise toward. `#16` bought the shape and paid −6.09 on the independent ruler;
this buys the shape and is paid 258.8.

**And the engine still loses every seat.** −363 a seat against a plain `need_first` /
`points_need` field. `#30` is necessary and it is not sufficient. The remaining deficit has a
named cause — `evidence/kdst_streaming/ROOT_CAUSE.md`: under the streaming level the engine
still finished seat 1 with **seven defenses and one receiver.** Raising what a streamable
position is WORTH does not tell a roster how many of it it can USE. That is what
`draft_room.unfieldable_last` was built for, and its own A/B is
`fieldability_arm_experiment.py`.

## Derived, not chosen (`#56`)

The level is: each week, the best wire player by **that week's projection**, summed. Wire =
outside the top (teams × slots) by season-sum projection, which is what a draft removes.

Every input is a league fact (`teams`, `roster_positions`) or a published projection. **No
constant is selected.** Measured for 2024: **K 121.78 → 164.50, DEF 107.95 → 146.05.**

Applied as a **floor only** — the streaming baseline is what you get for free, so it can raise a
replacement level and never lower one. It cannot make a position look scarcer than the draft
already says it is.

**No hindsight.** Weekly projections are published before the games. Realized stats are used
only to SCORE, never to choose.

## Why this works where my earlier reasoning said it would not

1. I measured the correction as "+16 on the board's own 2026 vintage" and called it too small.
   That was the **2026** snapshot; derived on the drafted season it is **+38 for DEF and +43 for
   K**.
2. The saturation curve (5.09 → 7.02 at +30, → 10.01 at +55) was measured under the **projected**
   ruler in self-play. It described where DEF stops being the top board row. It could not say
   what deferring was WORTH — the projected ruler is indifferent to K/DST timing by
   −0.16%/+0.08%. The realized ruler is not.

So "the shape is not reachable by valuation" was wrong in its strong form.

## What is NOT established

- **One season, one format.** The **2023 holdout is running** and is required before this ships.
- **Production plumbing does not exist.** `app.py` passes season sums; weekly projections do not
  reach `replacement_levels`. This experiment wraps the function and restores it.
- **The ruler models no waivers**, so the engine gets no credit for actually streaming the
  defense it deferred. The measured gain is therefore conservative.
- **The absolute grade carries the residual** stated at the end of
  `evidence/backtest/ANACHRONISM.md`: the guard filters the pool, not the board. It is identical
  across arms, so the paired figure above is unaffected.
