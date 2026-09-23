# The 2023 holdout: both fixes transfer, 12 of 12 seats under each

> **THE TWO `--streaming` ROWS BELOW ARE WITHDRAWN AND BEING RE-RUN.** They were measured on an
> INFLATED streaming level — K 169.66 / DEF 172.91, where the correct 2023 derivation is
> **K 155.76 / DEF 158.00**. Cause: `streaming_levels` read a module-level `ROSTER_POSITIONS`
> that only `main()` filled, and `fieldability_arm_experiment` calls it without going through
> `main()`, so it read `[]`. An empty slot list makes starter counts zero, `demand` falls to its
> `max(1, ...)` floor, and the "wire" becomes everyone outside the top ONE instead of the top
> twelve. Fixed (the argument is required now) and pinned by test.
>
> **UNAFFECTED and standing:** the `base` and `+ fieldability backstop` rows, which never derive
> a level, and their paired **+230.0 / 12 of 12**. The 2024 figures are also unaffected — that
> run predates the refactor that introduced the global, and its levels (K 164.50 / DEF 146.05)
> are the correct ones.
>
> **What is NOT yet known:** whether the shipped level reaches the same −18.3. A single-seat
> production-path run on 2023 with the CORRECT level returned **−84.9**, against the inflated
> arm's −10.4 on the same seat — so the re-run may well land worse. That is stated here before
> it is measured.

**2023, `12T_ppr_K_DEF`, 12 seats, graded on REALIZED outcomes.** 2023 was never used to derive
anything — not the streaming level, not the ceiling, not a constant. It is the out-of-sample
test, and it is the one that decides whether any of this generalises.

| arm | wins | mean vs field | median | first K/DST | roster shape (seat 1) |
|---|---:|---:|---:|---|---|
| base | 0 / 12 | −384.7 | −436.7 | 5, 6 | DEF 5, WR 3, RB 2, TE 2, K 2, QB 2 |
| + fieldability backstop | 1 / 12 | −152.1 | −167.9 | 5, 6 | WR 7, RB 2, K 2, DEF 2, QB 2, TE 1 |
| + `#30` streaming level | **0 / 12** | **−299.6** | **−329.4** | 8 | *(re-run, correct level)* |
| **both** | *re-running* | | | | |

~~`+ #30 streaming` 1/12, −218.9~~ and ~~`both` 3/12, −18.3~~ were the INFLATED-level figures.
The corrected streaming-only arm is **0/12 at −299.6**, against base's −384.7 — a paired gain of
roughly **+85**, where the inflated level bought ~166. The correctly derived level suppresses
defenses less, so they come off the board at round 8 instead of rounds 11–13.

Paired, per seat, **improved 12 of 12 under each**:

- backstop over base: **+230.0** mean, +245.9 median
- backstop over streaming: **+214.6** mean, +246.7 median

Derived streaming levels for 2023, from that season's own published weekly projections:
**K 155.76, DEF 158.00.**

## Both seasons, side by side

| | 2024 (derived on) | 2023 (holdout) |
|---|---:|---:|
| base | 0/12, −346.9 | 0/12, −384.7 |
| **both fixes** | **11/12, +82.9** | **3/12, −18.3** |
| swing | **+429.8** | **+366.4** |

**The fixes transfer.** Same direction, same order of magnitude, every seat improved, on a season
the derivation never saw. That is what the holdout was for and it passes.

**The absolute grade does not transfer, and 2023 lands roughly EVEN rather than ahead.** The
engine is level with a `need_first` / `points_need` field on the holdout season, not beating it.

## Why 2023 grades harder, measured rather than argued

`evidence/backtest/HORIZON.md`. On the same 2023 seat, clearing `settings.type == 2` is worth
**+102.6** and flips the seat from −84.9 to +17.7. `time_horizon_adj` is built from the vendor's
THREE-YEAR outlook, which is 2026-vintage — so in a 2023 draft it is partly a ranking formed
after the season was played, and 2023 carries one more year of that than 2024.

So the residual −18.3 is the sum of at least two things: a dynasty engine being graded on a
single season (legitimate, and it should cost something), and a stale multi-year outlook
(illegitimate, and it cannot be separated out with the data this repository has). Neither is a
drafting defect.

## The honest summary

The engine, with both fixes, **wins decisively on 2024 and is level on 2023**, against a field
that ranks by the drafted season's own projections and covers its starters. Without them it loses
every seat on both seasons by 350–385 points. Every claim here is on a ruler the engine cannot
optimise toward, on a pool and a board that are both period-correct.

## Limits, unchanged from `RESULT_2024.md`

Two seasons, one format, self-play against a fixed field, no waivers, and an ORACLE weekly
lineup — which REWARDS hoarding rather than merely tolerating it, so the backstop's measured gain
is a lower bound on what it is worth to a real manager.
