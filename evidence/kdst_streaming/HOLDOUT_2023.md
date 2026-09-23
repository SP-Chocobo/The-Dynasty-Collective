# The 2023 holdout: both fixes transfer, 12 of 12 seats under each

**2023, `12T_ppr_K_DEF`, 12 seats, graded on REALIZED outcomes.** 2023 was never used to derive
anything — not the streaming level, not the ceiling, not a constant. It is the out-of-sample
test.

Derived streaming levels for 2023, from that season's own published weekly projections:
**K 155.76, DEF 158.00.**

| arm | wins | mean vs field | median | first K/DST | roster shape (seat 1) |
|---|---:|---:|---:|---|---|
| base | 0 / 12 | −384.7 | −436.7 | 5, 6 | DEF 5, WR 3, RB 2, TE 2, K 2, QB 2 |
| + fieldability backstop | 1 / 12 | −152.1 | −167.9 | 5, 6 | WR 7, RB 2, K 2, DEF 2, QB 2, TE 1 |
| + `#30` streaming level | 0 / 12 | −299.6 | −329.4 | 7, 8, 9 | **K 5**, WR 4, QB 3, RB 2, TE 1, DEF 1 |
| **both** | **4 / 12** | **−49.9** | **−81.0** | 7, 8, 9 | **WR 7, RB 2, QB 2, K 2, DEF 2, TE 1** |

Paired, per seat, **improved 12 of 12 under each**:

- backstop over base: **+230.0** mean, +245.9 median
- backstop over streaming: **+255.1** mean, +266.6 median

## The two fixes are not equal partners, and the holdout is what showed it

| | 2024 (derived on) | 2023 (holdout) |
|---|---:|---:|
| base | 0/12, −346.9 | 0/12, −384.7 |
| **both fixes** | **11/12, +82.9** | **4/12, −49.9** |
| swing | +429.8 | +334.8 |

**The backstop is the robust half.** It is a COUNT bound — `slots(P) + 1`, from the slot list and
the one bye every team has — with no magnitude to get wrong. It improved **12 of 12 seats in
every arm of both seasons**, worth +230 to +347 depending on the arm.

**`#30`'s streaming level is real but season-dependent.** Worth ~+328 a seat on 2024 and ~+85 on
2023. Still derived rather than chosen, still the correct alternative to price a streamable
position against, and still positive on both seasons — but not the headline it was.

**A note I am deliberately not acting on.** An earlier, buggy run of this holdout used an
inflated level (DEF 172.91 against the correct 158.00) and graded BETTER: −218.9 against −299.6
on the streaming-only arm. A more aggressive floor would score higher here. **Choosing the level
that grades best is calibration, which `#56` forbids, and it is exactly how the first K/DST
repair was brute-forced into shape and had to be unwound.** The derivation stands as derived.

## The streaming-only arm hoards KICKERS

Look at its seat-1 shape: **K 5**, DEF 1. Raising the floor on both positions made DEF expensive
enough to avoid and left K cheap enough to stockpile — the identical flat-position pathology,
relocated. The backstop caps it at 2 because the ceiling is a count and does not care which
position found the loophole.

That is the clearest single piece of evidence for why the two fixes are not redundant: pricing
alone moves the problem, and counting alone leaves it mispriced.

## What this settles and what it does not

**Settles:** both fixes transfer out-of-sample, every seat improves under each, and the engine
goes from losing all twelve seats by 385 to roughly level. The shape is `WR 7, RB 2, QB 2, DEF 2,
K 2, TE 1` with first K/DST at rounds 7–9 — two of every dedicated position, depth in the
flex-reachable ones.

**Does not settle:** why 2023 grades harder than 2024 in absolute terms. Part is measured — the
dynasty premium is worth +102.6 on the same seat (`evidence/backtest/HORIZON.md`) and 2023
carries one more year of 2026-vintage three-year outlook. Neither is a drafting defect, and the
data here cannot separate them.

## Limits, unchanged

Two seasons, one format, self-play against a fixed field, no waivers, and an ORACLE weekly
lineup — which REWARDS hoarding rather than merely tolerating it, so the backstop's measured gain
is a **lower bound** on what it is worth to a real manager.
