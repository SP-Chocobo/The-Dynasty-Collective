# Backtest grade — the engine judged on what actually happened

> **SUPERSEDED IN PART.** Absolute engine-vs-field grades from this instrument were measured on
> a pool containing players who did not exist in the drafted season (133 in 2023, 101 in
> 2024), priced from the 2026 vendor export. Guard shipped, re-runs in flight — see
> `evidence/backtest/ANACHRONISM.md`. Projected-ruler figures quoted here are unaffected.

`run_backtest_grade.py`. Engine seat against a field of sane styles, seat-controlled, drafted on a
**finished** season's projections and scored on that season's **realized** weekly outcomes via
`realized_ruler`. The first grade in this repository the engine cannot optimise toward (`#288`
concluded none existed; `#18` committed both arms for 2023 and 2024).

Naming follows `evidence/batteries/README`: `BACKTEST_<season>_<format>_<commit>.json`, the commit
being the one the run started at.

## BACKTEST_2024_12T_ppr_K_DEF_3cdaca7 — 12 seats, 2024

```
engine wins 7 of 12 seats | mean -15.4 | median +10.8
11 DISTINCT rosters (seats 2 and 3 collapse) | wins 7 of 11 | mean -5.6 | median +14.1
```

**Roughly EVEN with the field on real outcomes**: a positive median, a mean dragged negative by one
seat at −503.3. Read against the projected ruler on the same engine — **wins 11 of 12 at +2.131%**
— the advantage largely does not survive contact with the season.

That is the expected direction and worth stating plainly: the engine maximises a
projection-derived quantity, and `#18` measured how far projections actually order a season
(Spearman 0.48–0.92 by position). Grading it on projections grades it partly on its own homework.

### Seats 2 and 3 collapse, and it is not a bug

Both returned 2439.56. The engine and the neighbouring style want **disjoint** players, so swapping
which of them picks second merely swaps who takes whom — the engine's own roster is unchanged. 32
picks of the draft do differ; the engine's sixteen do not. Verified by diffing both drafts pick by
pick.

`#246` says identical output is usually a broken instrument, so the case where it is NOT has to be
**shown**. It also means the twelve seats are not twelve independent samples, and the runner now
derives and prints `distinct_engine_rosters` rather than leaving a reader to notice.

### Where the headroom is

Every seat took its first K or DST in **round 4 or 5**. Counterfactual surgery on the same season
prices each early K/DST pick at **+81.4 realized points** if deferred (42 picks, helped 34 of 42).
At roughly 3.5 such picks a seat that is **~285 points** of headroom against a field mean of
~2,555 — an order of magnitude larger than the engine's current margin either way.

**So K/DST placement is plausibly the single biggest available improvement**, worth more than the
engine's entire present edge over the field. That is the quantitative case for `#30` being a
blocker.

### Depth is being used

`players_who_never_started` is 0 for ten of twelve seats and 1–2 for the other two. The engine's
bench is not dead weight — it plays, which is what the weekly solve rewards and the season-total
solve cannot see.

### Limits

No waivers or trades (every arm denied streaming equally, so this is a LOWER bound on any
transaction-based strategy). The weekly lineup is an ORACLE — it starts the best actual scorers, so
totals are ceilings, not expected scores; every arm gets that equally. One season, one format,
n = 11 distinct seats. `adp` is excluded from the field because it is a 2026-vintage export and
cannot order K or DST at all (32 defenses share one value).
