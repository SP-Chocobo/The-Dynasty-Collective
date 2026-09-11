# B2 CLOSED: no ingested source carries a number for these quarterbacks — sourcing, not wiring

Measured through production's own `merge_player` (name + position + team), the same call
`build_roster_table` makes. No engine source changed.

## The question

B2's chain had reached: the engine takes 76.2% of every quarterback it can price, and cannot reach
the human 20% because only 42 of 155 admitted QBs are priceable. Sleeper answered for them and
projected **zero** (18/18 weeks captured, README: trimmed to non-zero categories). The open
question was whether **dynasty** material exists for them — which decides whether #147 (the
one-season anchor) is a **wiring** problem or a **sourcing** one.

## The answer: sourcing

| population | matched a baseline row | `proj_3yr` | `trade_value` | `projection` |
|---|---|---|---|---|
| **PRICED QBs** (42) | 39 | **39 (92.9%)** | 39 (92.9%) | 39 (92.9%) |
| **UNPRICED QBs** (113) | **1** | **0 (0.0%)** | **0** | **0** |

92.9% against 0.9% is not an instrument failure — a broken merge would miss both populations.

They are real, recognisable NFL backups, and the baseline simply has no row for them:

```
   Jake Haener        NYG  exp=3   no baseline match   proj_3yr=None
   Stetson Bennett    LAR  exp=3   no baseline match   proj_3yr=None
   Aidan O'Connell    LV   exp=3   no baseline match   proj_3yr=None
   Sean Clifford      SF   exp=3   no baseline match   proj_3yr=None
   Tyson Bagent       CHI  exp=3   no baseline match   proj_3yr=None
   Tommy DeVito       NE   exp=3   no baseline match   proj_3yr=None
   Joe Milton         DAL  exp=2   no baseline match   proj_3yr=None
   Sam Hartman        WAS  exp=2   no baseline match   proj_3yr=None
```

## Verdict

**Neither source prices them.** Sleeper answers and says zero; the vendor baseline has no row at
all. **#147 is NOT the binding constraint here** — a perfect dynasty anchor would have nothing to
anchor on for these 113 players. You cannot demonstrate that a one-season horizon is the problem
in a population with no multi-season input either.

**B2 is a SUPPLY gap, in the #49 / #210 family** — *"nothing we ingest prices these players, not
just the vendor"*, which is the same sentence #210 already carries for IDP. The remedy is a source
that covers deep quarterbacks (the repo already has `parse_keeptradecut_pdf` and
`parse_fantasypros_dynasty_pdf` parsers; whether either is loaded and how deep it runs is the next
question, and it is an ingestion question, not an engine one).

**My own verdict flip-flopped once and this settles it, on both sides.** I first called it supply,
then corrected to #147 on the strength of Sleeper's zeros, and that correction over-reached: it was
right that Sleeper is complete and wrong to conclude the horizon was the binding constraint. Now
both sides are measured — no current-season projection AND no dynasty material — and supply is the
answer.

## What this does NOT establish

**Not that #147 is wrong.** The one-season anchor is a real, registered concern and this population
simply cannot test it. **Not that the engine should draft these players** — a quarterback nobody
publishes a number for may be correctly unpriceable. **And not that 20% QB is right**; that remains
one league's startup and the humans may be following convention.

## Method note

The first attempt at this used a guessed `DataMerger` API (`load_baseline`), returned 0 of 155 for
BOTH populations, and was discarded rather than reported — a uniform zero is the signature of a
broken instrument, not a finding. The measurement above uses `merge_player`, which is what
production calls, and the 92.9%-vs-0.9% split is what a working instrument looks like.
