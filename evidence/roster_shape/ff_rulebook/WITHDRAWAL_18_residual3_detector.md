# WITHDRAWAL 18 — RESIDUAL3's "the open-slot mechanism fires 0 times" is a detector artifact

**Found by:** the Fable advisory pass, reading `displacement_level`'s contract against the
probe. **Confirmed by me** against `residual3_raw.json` before propagating it.

## What was claimed

RESIDUAL3 pre-registered three forks on the rate at which `displacement_adjustments` returns
`adjustment == 0.0` for tight end — the documented OPEN-SLOT case. It reported Fork B: the
rate is 0.0 for every seat, so the open-slot mechanism does not separate hoarders from
starvers.

## Why that is not a measurement

The detector was `adj == 0.0`. Read from the saved raw:

```
n rows            144
adj == 0.0          0      <- 0 of 144, and NOT because the mechanism is quiet
adj is None         0
adj nonzero       144
distinct displaced: 217.75 (n=103), 213.93 (12), 209.20 (12), 200.90 (12), 212.03 (4), 211.65 (1)
implied level (adj + disp): 144.98, 134.34, 149.17, 100.67, 93.15, 99.36, ...
```

`adjustment` is `free_alternative - displaced`, so `adjustment == 0.0` requires
`displaced == the TE level`. Under `slot_alternatives` (#216) a FLEX phantom is worth the best
free player among every position the slot admits — `max(levels)` = **217.75** — not the
candidate's own level. Every TE level observed here is below that. So after each seat's
dedicated TE slot is filled (pick 9 onward, by construction of the population), the TE probe
can only ever evict a flex phantom or a real starter, and `adjustment == 0.0` is **arithmetically
unreachable**.

0 of 144 measures the detector, not the engine.

## The correct detector

The open-slot case in its flex form is `displaced ∈ values(slot_alternatives)` — the evictee is
a phantom, not one of my players. On this same saved data that fires **103 of 144 times**.

## What survives, and what does not

- **Withdrawn:** "the documented open-slot mechanism never fires in this population."
- **Withdrawn:** Fork B as a selected fork. No fork was legitimately selected; the instrument
  could not distinguish them.
- **Survives:** nothing from RESIDUAL3 is promoted in its place. The re-detection is registered
  as available, not performed — running it is a fresh measurement and needs its own
  pre-registration.

## The lesson, for the doctrine

This is a new shape of the same failure the skill already warns about ("if ON and OFF are
identical, the thing under test did not fire"). The extension: **before reading a rate of
exactly zero as a finding, prove the detector's firing condition is reachable in the population
you measured.** An unreachable predicate returns 0.0 for every input and reads exactly like a
clean null result — which is precisely what it did here, through a pre-registration that was
otherwise correctly run.

Note the near-miss: RESIDUAL3's own docstring says "0.0 is a CONSTRUCTION, not a measured
zero, which is exactly why its RATE is the quantity." That sentence identifies the hazard and
then walks into it.
