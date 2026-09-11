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

---

# CORRECTION (23rd, mine): "Sleeper answers and says zero" is the wrong description — and B2 is not its own finding

The verdict above stands: **no ingested source prices these quarterbacks**, and the remedy is a
source, not a wire. Two things in how I described it were wrong, and the second is the important
one.

## 1. The mechanism, stated precisely

I wrote that Sleeper "answers and says zero." It does not. Measured against the real capture
through `season_projections_from_capture()` and `build_players_db_from_capture()`:

```
Jake Haener      QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Stetson Bennett  QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Aidan O'Connell  QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Sean Clifford    QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Tyson Bagent     QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Tommy DeVito     QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Joe Milton       QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY
Sam Hartman      QB  entry: ['adp_dd_ppr']   <-- ADP-ONLY

ADP-only 8 | stat-bearing 0 | no entry 0
```

All eight have an entry, and every entry holds **one key**: `adp_dd_ppr`, the "undrafted"
sentinel (`18000.0`). ADP says where the market drafted a player, not what he is projected to
**do**. There is no stat line, so there is nothing to score — the scoring path reaches him and
finds no quantity, which is why the board says `bpa_source='no_priceable_input'`.

**"Says zero" and "has no stat line" are exactly the distinction this repo's absence contract
exists to enforce** — a measured 0.0 versus a `None` that was never computed. I conflated them in
a finding whose entire subject is absence. That is the error, and it is mine.

Population-wide, the same shape: of 474 QBs in the universe, **355 carry a capture entry and 321
of those (90.4%) are ADP-only**; 34 carry stats.

## 2. B2 is not a separate finding — it is the #212 population

`test_priceable_projection_count.py` already measured and named this mechanism: of 5,346 capture
entries, **4,506 carry only an ADP field and no stat line**, so the real priceable count is 840,
not 5,346 — a 6.4x coverage overstatement. It already folds #209 (Jake Haener, taken at 14.02
with `tav=None`, entry `{'adp_dd_ppr': 18000.0}`) and #210 (1,817 ADP-only entries are IDP — LB
852, DB 723, DL 242) into one finding.

**B2's quarterbacks are that same population**, and Jake Haener is literally the worked example
in both. So the register carries four items for one mechanism:

| item | population | mechanism |
|---|---|---|
| #209 | one QB in 14T_standard | ADP-only entry |
| #210 | HEAVY_IDP's 1,817 defenders | ADP-only entry |
| **B2** | the league pool's deep QBs | **ADP-only entry** |
| #212 | all 4,506 | the mechanism itself |

**One finding, three populations.** The supply verdict is unchanged and the #49/#210 family is
still the right home — what changes is that B2 needed no separate investigation, and the answer
was already committed in a test docstring before I started.

## What survives unchanged

The vendor-baseline half, which is independent of the capture and was measured through
production's own `merge_player`: **39 of 42 priced QBs carry `proj_3yr` (92.9%) against 0 of 113
unpriced (0.0%)**, and the named backups have no baseline row at all. Neither source prices them
— Sleeper because the entry holds no stat line, the vendor because there is no row. #147 is still
**not** the binding constraint: a perfect dynasty anchor would have nothing to anchor on.

## The lesson, which is the same one as the register lag

The answer to B2 was sitting in a test docstring. The reconciliation finding written an hour
earlier says: *before opening an investigation into any item filed open, grep for its repair
first.* B2 was not filed as an item at all, which is how it evaded that rule — so the rule
generalizes: **before investigating a mechanism, grep for the mechanism**, not just the item
number.
