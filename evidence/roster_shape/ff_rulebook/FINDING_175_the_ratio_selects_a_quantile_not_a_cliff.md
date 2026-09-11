# #175: `CLIFF_HIGH_RATIO` does not detect structure — it selects a quantile, and the null says so

#175 asks for a **derivation, not a tightening**, and #56 forbids calibrating a constant to an
observed outcome. This supplies the derivation basis without proposing a value.

## The null model, stated before looking at data

`detect_positional_cliff` flags when a player's `bpa` gap to the next player at his position
exceeds `CLIFF_HIGH_RATIO` × that position's **typical** (trimmed-median) adjacent gap.

If adjacent gaps were **memoryless** — exponential, i.e. the position has no cliffs at all, just
smooth decay — the ratio `gap / median` has a closed form:

```
P(X >= r * median) = exp(-r * ln 2) = 2^-r
```

| r | 1.0 | 1.5 | **2.5** | 3.0 | 4.0 |
|---|---|---|---|---|---|
| flagged **by chance, no cliff present** | 50.0% | 35.4% | **17.7%** | 12.5% | 6.2% |

So `2.5` is, before any data, **the ~82nd percentile of a smooth decay**. A fixed multiple of a
median is a quantile selector, not a rarity test.

## Measured, using the engine's own detector

12-team standard, opening board, real capture universe: 1,111 rows, **256 bpa-priced**.
`detect_positional_cliff` called on every priced row — the production function, not a
reimplementation of it.

| tier | count | share of bpa-priced |
|---|---|---|
| HIGH | 37 | **14.5%** |
| MEDIUM | 39 | 15.2% |
| LOW | 176 | 68.8% |
| (none) | 4 | 1.6% |

**HIGH + MEDIUM = 29.7%**, which broadly **reproduces #175's 34%** rather than contradicting it
— #175's "material cliff" figure appears to be the union of both tiers, and the small
difference is consistent with a different arm or board state.

And the ratio distribution, `gap / typical_gap`, n = 252:

| r | empirical | exponential null | empirical ÷ null |
|---|---|---|---|
| 1.0 | 47.2% | 50.0% | **0.94×** |
| 1.5 | 30.2% | 35.4% | **0.85×** |
| 2.0 | 22.2% | 25.0% | **0.89×** |
| **2.5** | **14.7%** | **17.7%** | **0.83×** |
| 3.0 | 12.3% | 12.5% | 0.98× |
| 4.0 | 7.5% | 6.2% | **1.21×** |

## What this establishes

**At 2.5×, the flagged population is not merely unremarkable — it is slightly RARER than a
no-cliff null predicts (0.83×).** The detector is not finding structure there. It is returning
roughly the top sixth of an ordinary decay curve, which is what a fixed multiple of a median
does by construction.

**Real structure does exist, and it lives further out.** The enrichment is flat-to-below-null
through the body and crosses 1.0 only past 3×, reaching **1.21× at 4×**. That crossing point is
the first place the pool looks different from memoryless decay — and it is a **derived** feature
of the distribution, not a number anyone chose.

**So #175's framing is confirmed and sharpened.** "A third of the population cannot all be
cliffs" is right, and the reason is not that `2.5` is merely *loose*: it is that a multiple of a
median cannot express rarity at all. Changing `2.5` to `3.5` would move the quantile, not fix the
category error.

**The derivation #56 requires is now available in two forms**, neither of which is a tuned
constant:
1. **Quantile-based** — flag at a stated exceedance probability against the position's own
   empirical gap distribution. The bound then comes from the data, and the *stated probability*
   is the honest design decision, not a magic multiplier.
2. **Null-crossing** — flag where the empirical distribution first departs from the memoryless
   null by a stated margin. On this board that is somewhere past 3×.

**No value is proposed here, and none should be read in.** Which basis to adopt, and what
exceedance probability counts as "unusual", is the owner's decision; #56's point is that
whichever is chosen must be derived, and now it can be.

## Scope, stated rather than implied

**One board, one format, one state** — 12T_standard, opening board, 252 usable ratios. The
enrichment curve's *shape* is the claim; the exact crossing point is not established across
formats or mid-draft states, and a mid-draft board with a drained pool could differ materially.
Reproducing this across the battery's arms is the obvious next step and was not done.

## Method note — I measured the wrong column first

The first pass computed gaps in `universal_value` and would have published a framing built on
it. `detect_positional_cliff` works on **`bpa`**, uses a **trimmed** median rather than a plain
one, and carries a `CLIFF_MIN_MATERIAL_GAP` floor. Reading the function before believing the
number caught it. The rewritten measurement calls the production detector directly rather than
reimplementing its rule — which is the only version that can be said to measure the engine.
