# Phase 5 — units and domains, measured on the owner's own league

> Every number here is from the real board (820 priced rows, post-phase-1/2 pool), not a fixture.

## The domains this engine mixes

| domain | examples | natural range |
|---|---|---|
| **POINTS** | `bpa`, `universal_value`, `final_score`, `projection`, `waiting_cost` | measured below |
| **PERCENTILE** | `_season_proj_pct`, `_proj3yr_pct`, `confidence`, `_pct` | 0–100 |
| **PROBABILITY** | survival, take probabilities | 0–1 |
| **VENDOR** | Draft Sharks `trade_value` | 0–100, position-scarcity adjusted |
| **RANK** | ordinal | 1..n |

## The POINTS domain, as this league actually measures it

```
bpa              min  -225.49   median  -65.64   max  220.56   n=820
universal_value  min  -243.49   median  -65.81   max  220.56
final_score      min  -235.11   median  -83.83   max  228.94

bpa span: 446.05 points
```

Every capped team term is ~2.7% of that span (`NEED_BONUS_MAX`, `ELIGIBILITY_BONUS_MAX`,
`DEPTH_EXPOSURE_MAX` = 12.0; `TIME_HORIZON_CLAMP` = 10.0). That part composes sensibly.

## Defect 1 — `FORFEIT_SCALE_MAX` divides by a number the pool does not contain

`pick_synthesis.FORFEIT_SCALE_MAX = 100.0`, and its own comment says the scale "is CONSTRUCTED so
100 is the largest real VOR gap in the remaining pool."

```
claimed largest real VOR gap: 100
measured largest real VOR gap: 446.05
```

**The construction it cites no longer happens.** `draft_room._scale_vor_to_bpa` is the identity —
"No reference, no rescale, no clip" — so nothing normalises VOR onto a 0–100 band any more. The
divisor is orphaned: not wrong by a chosen amount, but calibrated against a scale that was
removed. Downstream, `forfeit_component` saturates at its ceiling for any scarce position, which
is what `test_threshold_reachability` independently reports as forfeit p50 54.81 / max 154.94.

## Defect 2 — one percentile pair, two bounds, 5× apart

`upside_score` and `time_horizon_adj` read **the same two columns** (`_season_proj_pct`,
`_proj3yr_pct`) and treat their difference completely differently:

```
upside_score:       bpa + 0.5 x (proj3yr_pct - season_pct)     UNCLAMPED  ->  0 .. 50 points
time_horizon_adj:   same percentile pair                       CLAMPED    -> -10 .. +10 points
                                                               ratio: 5x
```

A percentile difference is not points. One of these two converts it at five times the other's
rate, and only one of them admits it needs a bound at all.

## Defect 3 — already repaired in Phase 4, recorded here for completeness

`RUN_TAKE_PROBABILITY_CAP` could be set to 9.0 — a probability cap of nine — with all 51 tests of
its own module passing. Closed by `test_probability_bounds`, which discovers probability constants
by walking the module rather than listing them.

## What is NOT repaired here, and why

Defects 1 and 2 both need a **scale**, and `#56` forbids calibrating one. Replacing `100.0` with
`446.05` hard-codes today's pool; replacing it with a live measurement changes valuation for every
candidate; changing `UPSIDE_GROWTH_WEIGHT` picks a number with nothing to derive it from.

Those are valuation decisions, not unit-conversion bugs, and the ruling pattern is already
established twice in this program: the rookie population change and the recency blending weight
both went to the owner rather than into a repair commit. These go the same way.

**The sweep is the deliverable. The scale is the owner's.**
