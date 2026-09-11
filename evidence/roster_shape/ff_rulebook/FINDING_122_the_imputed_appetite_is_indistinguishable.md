# #122 confirmed, and it is a THREE-way collapse, not a two-way one

The register records #122 as "`positional_bench_appetite`'s per-position mean_rate imputation is
unmarked." That is true, and the measurement makes it sharper: **three different epistemic states
return the same shape, and two of them return the identical number.**

## Measured, holding everything else fixed

One league (`["QB","RB","RB","WR","WR","TE","K","BN","BN","BN"]`, 12 teams), one pool, three K
scenarios:

| K's situation | what it means | returned |
|---|---|---|
| deep pool | decay is **measurable** | `1.0359…` |
| 6-player pool | too short to read decay — **imputed** | `8.0526…` |
| **no K rows at all** | **nothing whatsoever to read** — imputed | `8.0526…` |

And the control, the same three against a league that does **not** roster K:

| | returned |
|---|---|
| any K pool, K not in `roster_positions` | `0.0` |

## What this establishes, and what it clears

**#62 is genuinely closed, and its docstring promise holds.** The docstring says a position whose
pool cannot reach 2x starter demand "does NOT get 0.0 — that would assert 'this position is never
benched', which is a claim, not an absence." Confirmed: the short pool returns `8.05`, not `0.0`.
The `0.0`s do appear, but only for positions the league does not roster, where a zero bench
appetite is a **real measured zero** — you cannot bench a position you cannot start. That is
correct and should not be changed.

**#122 is real, and it is worse than one line suggests.** The imputed `8.05` is returned in
exactly the same shape as the measured `1.0359` — a bare float in a `dict[str, Optional[float]]`.
So a consumer cannot distinguish:

1. **measured** — this position's own decay was read, and
2. **imputed from a short pool** — six players of evidence, too few to read, and
3. **imputed from nothing at all** — zero players of evidence,

and states 2 and 3 are not merely the same *shape*, they are the same *number*. The mean rate is
supplied identically whether the position had some evidence or none. On this fixture the imputed
value is roughly **8x** the measured one, so the difference is not cosmetic.

This is the exact family of #166 (`horizon_basis`), #174 (`depth_basis`), #187 (`denial_basis`)
and #207 (`rival_premium_basis`): a number that is right to produce, produced without saying what
kind of number it is.

## The repair, specified but NOT built — and why

The pattern is established four times over: a companion basis alongside the value, with a derived
vocabulary (#126) rather than a hand-list, so a consumer can render absence as absence. Applied
here that is an `appetite_basis` per position over at least `measured` / `imputed_short_pool` /
`imputed_no_pool` / `not_rostered`, and #188's open question — whether the vocabulary needs a
fifth "bounded/partial" state — lands squarely on states 2 vs 3, which is the distinction this
measurement just made concrete.

**Not built here.** It changes `draft_room.py` beyond prose while the #222 standing constraint on
that file is in force, and it widens a function's contract, which touches
`estimated_bench_demand` and `horizon_replacement`. #122 is classified KNOWN-OPEN-ACCEPTABLE,
nothing is failing, and no measurement in flight depends on it — so the right move is to hand the
owner a specified repair rather than take the boundary down on my own judgment. It is ready to
build the moment the constraint lifts.

## What was NOT concluded

Whether the mean-rate imputation is the right *value*. That is the question the docstring already
reserves ("whatever replaces this has to satisfy both ends — cliff positions and flat ones — and
that needs more than one draft to derive honestly"), it is #56 territory, and nothing here bears
on it. This finding is entirely about **disclosure**: the number's provenance, not its size.
