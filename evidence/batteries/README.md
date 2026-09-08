# Battery evidence — why these are committed

A battery run is hours of measurement whose output lived only in an ephemeral scratchpad. The
container that produces it is reclaimed after inactivity, so an uncommitted report is one
reclamation away from gone, and the freeze rests on exactly these numbers. Committing them makes
the evidence durable independently of the session that produced it.

Each run is stored twice: the JSON the driver writes, and the per-arm console log, which carries
the running commentary (duplicate-arm detection, per-arm timings) the JSON does not.

## Naming

    BATTERY_<date>_<what-it-measures>_<commit>.json

The commit is the one the run STARTED at, and it is part of the name rather than a note, because
a battery compared against a report from different code is the single most expensive measurement
error this project has made.

## Runs

### BATTERY_2026-09-08_baseline_vendor_only_1e869ce

33 formats, 24 independent, 5,340 picks, 18 structural findings, 14,081s.

THE VENDOR-ONLY ARM. Started before #204, so the simulation never received
`sleeper_projections` and every board it built was priced from the vendor export alone —
`universe.priced_from` is ABSENT in this file, and that absence is the marker: the field did not
exist yet. The scoring-aware path (#180/#192) and the availability haircut (#191/#202) are both
inert here.

Findings, all one shape — a single unpriced player winning a single pick at the deep end of a
draft, plus IDP supply exhaustion:

    14T_standard        1
    14T_half_ppr_SF     1
    14T_ppr_SF          1
    4WR_TE_PREMIUM      1
    HEAVY_IDP          14

That is #49's input gap (per #51's conclusion), not an arithmetic defect: the pool runs out
before the draft does. `14T_ppr_SF` reproducing `14T_half_ppr_SF` exactly is the known
half-PPR/PPR export collapse, not independent evidence — the report names all nine duplicate
arms itself.

---

## PRE-REGISTRATION: BATTERY_2026-09-08_scoring_aware_5a53057

**Written while the run was still executing, before any arm's result was read.** #178 is the
precedent: an acceptance criterion invented after the numbers exist is not a criterion, and the
owner's own amendment there ("or a degrade elsewhere") is what turned a one-sided confirmation
into a real test. The same discipline applies to reading a result as to accepting one.

### What changes between the arms

EXACTLY ONE THING IS INTENDED TO: the simulation now receives `sleeper_projections` and
`SLEEPER_BASIS_SEASON_SUM`, so every board is priced the way production prices it (#204).

Six commits separate the two runs (#203, #185+#186, #187, #174). None touches pricing or
ordering -- all four are absence-companion work: a term made absent instead of a confident
number, basis vocabularies given one home, a companion carried across a boundary. **That is a
claim, not an axiom.** If an arm moves in a way the pricing path cannot explain, one of those
four reached further than intended, and that is a finding rather than a footnote.

### Predictions, each falsifiable

1. **Unpriced-player findings DROP.** Sleeper points give a price to players the vendor export
   never covered, so the 4 single-unpriced-player arms (14T_standard, 14T_half_ppr_SF,
   14T_ppr_SF, 4WR_TE_PREMIUM) should lose their finding. If they DON'T, the scoring path is
   not reaching the players it was supposed to reach.

2. **HEAVY_IDP's 14 findings SHRINK BUT DO NOT VANISH.** It is IDP supply exhaustion (#49/#51),
   and Sleeper prices IDP where the vendor does not -- but a 216-pick draft against a thin IDP
   pool runs out regardless. A drop to zero would mean the pool was never the constraint and
   #51's conclusion needs re-opening.

3. **Trajectories are NOT byte-identical to the baseline.** If they are, the scoring path is
   inert in simulation despite production shipping it, and #204's repair bought nothing.

4. **`universe.priced_from` reads `vendor+sleeper`** and `season_projections_supplied` is
   ~5,346. The baseline has neither field at all. If this run also lacks them, it ran old code.

5. **The 9 duplicate arms stay duplicated.** They collapse because half-PPR and PPR resolve to
   the same rankings export -- a vendor-side property the Sleeper path does not touch. If the
   count changes, the duplicate detector is measuring something other than what it claims.

### What a clean result does and does not license

A clean run is the #150 gate and nothing more. It says the engine does not break its league's
rules on the path production runs. It says NOTHING about whether the engine drafts WELL -- that
is #205's control-vs-engine proof -- and nothing about #206 or #184.

### ⛔ WITHDRAWN — BOTH RUNS BELOW PREDATE #213

**Read nothing below as a measurement of this engine until it is re-run.**

`build_mock_league` emitted a ONE-KEY scoring dict, `{"rec": <0.0|0.5|1.0>}`. That was inert
while scoring propagated only by file selection; #204 made the battery pass
`sleeper_projections`, and from that moment `score_projection` scored every stat line against
that single key. The real league carries **64** scoring keys.

| player | real rulebook | `{"rec": 1.0}` | `{"rec": 0.0}` |
|---|---|---|---|
| Josh Allen (QB) | 372.46 | **0.0** | 0.0 |
| Christian McCaffrey (RB) | 413.24 | **86.22** — his reception count | 0.0 |
| Jaxon Smith-Njigba (WR) | 395.69 | **123.88** — his reception count | 0.0 |
| Jack Campbell (LB) | 171.88 | **0.0** | 0.0 |
| **players priced** | **835** | 431 | **0** |
| **IDP priced** | **299** | 1 | 0 |

So 27 of 33 arms drafted a league in which quarterbacks score nothing and receivers are paid one
point per catch — RB/WR/TE priced in RECEPTION COUNTS while QB/K/DEF stayed in vendor fantasy
points, on one shared replacement number line. The standard arms priced nobody at all.

**The baseline (vendor-only) run is NOT affected by the mechanism** — it never passed
`sleeper_projections`, so nothing scored stat lines. It is superseded only because the engine
has moved on.

**Withdrawn specifically:** #209's reading ("the scoring path is not reaching that player" — in
the standard arm it reached nobody), #210's conclusion ("nothing we ingest prices these players"
— false; 299 IDP lines price), prediction 3's "CONFIRMED, strongly" (the 8T_half_ppr collapse
327→42 I read as the path working was the unit error arriving), and the "What this licenses"
paragraph at the end of the RESULT section.

**Not withdrawn:** the duplicate-arm collapse 9→1 is real but its *explanation* is now partly
wrong — I attributed it to `score_projection` differentiating PPR from half-PPR, which is true,
but under a rulebook where that differentiation was reception-counting. It must be re-derived.

Found by an advisory review, verified independently before acting. Fixed in `028b574`: every
arm now carries the capture's real `scoring_settings` with its own rec/TE-premium overlaid, and
`run_draft_battery` **refuses to start** when a position holds stat lines its rulebook prices
none of. Re-run in flight.

---

### RESULT: BATTERY_2026-09-08_scoring_aware_5a53057

33 formats, **32 independent** (was 24), 5,340 picks, **15 structural findings** (was 18),
14,512s. `universe.priced_from = "vendor+sleeper"`, `sleeper_basis = "season_sum"`,
`season_projections_supplied = 5346`.

Scored against the five predictions **as written**, including the two that failed.

**1. Unpriced-player findings drop — PARTIALLY CONFIRMED, 3 of 4.**

    14T_half_ppr_SF   1 -> 0
    14T_ppr_SF        1 -> 0
    4WR_TE_PREMIUM    1 -> 0
    14T_standard      1 -> 1     <-- did NOT drop

The prediction's own falsifier applies to the survivor: "if they DON'T, the scoring path is not
reaching the players it was supposed to reach." For 14T_standard it did not. One player, in the
standard-scoring 14-team arm, is still unpriced with 5,346 Sleeper season projections supplied.
That is a residual with a named location, not a rounding error. Registered as **#209**.

**2. HEAVY_IDP shrinks but does not vanish — FAILED. It did not shrink at all.**

14 findings before, 14 after. Unpriced candidates REACHING a decision rose 164 -> 189. So
Sleeper prices no additional IDP player in this arm: the coverage gap is not vendor-specific,
it is in both sources. #51's conclusion (a SUPPLY defect, remedied by an input) survives — the
findings did not vanish, which was the condition that would have reopened it — but the specific
quantitative claim I registered was wrong, and #49's input gap is BROADER than assumed: it is
not "the vendor lacks IDP", it is "nothing we ingest prices these players." Registered as **#210**.

**3. Trajectories are not byte-identical — CONFIRMED, strongly.** Every scoring-sensitive arm
moved, several enormously (8T_half_ppr starters 327.9–377.02 -> 42.36–137.94). The scoring path
is live in simulation; #204 bought exactly what it was meant to.

**4. priced_from / season_projections_supplied — CONFIRMED exactly.** Both fields present with
the predicted values; the baseline has neither.

**5. The 9 duplicate arms stay duplicated — FAILED, 9 -> 1, and my falsifier was wrong too.**

I predicted the duplicates would persist because "half-PPR and PPR resolve to the same rankings
export — a vendor-side property the Sleeper path does not touch", and stated that a change in
the count would mean "the duplicate detector is measuring something other than what it claims."

Both halves were wrong. The detector is fine. **Scoring propagates by TWO routes, not one:**
FILE SELECTION (`set_league_format` picks a rankings export) *and* `score_projection` applying
the league's own scoring settings to Sleeper stat lines. Post-#204 the second route is live, so
PPR and half-PPR now price differently even off one shared export. The only surviving duplicate
is `12T_ppr_mode_balanced ≡ 12T_ppr`, which is correct — balanced *is* the default mode.

This corrects a claim in the `engine-measurement` skill, which states scoring propagates by file
selection. That was true before #204 and is now half the story.

**AN UNPREDICTED FINDING: a NEGATIVE starter value.** `12T_ppr_mode_upside` reports starters
**−205.4** to 127.46. This is the same category error found independently in #205's roster
proof: `roster_strength` sums `universal_value` across a STARTING LINEUP, 83.8% of pool values
are negative, and `lineup_optimizer` has no "leave the slot empty" move — so a thin roster is
forced to start deep negatives and the lineup total goes negative. `universal_value` is an asset
LEVEL, not a rate a lineup realises. This does **not** affect the battery's FINDINGS, which are
legality checks and never read `starter_value` — but the "starters X–Y (spread Z)" line is not a
roster-quality measure and must not be read as one. Registered as **#211**.

**What this licenses.** The #150 legality gate is clean apart from two named, understood arms
(14T_standard's single unpriced player, HEAVY_IDP's supply exhaustion). It says nothing about
whether the engine drafts WELL — that is #205 — and nothing about #206 or #184.

### #211 applied — what changed in the reported line, and what did NOT

Fixed in `draft_battery.roster_strength` and `run_draft_battery`'s console line:

- **`total_value_*` is now the roster-worth line**, named by `ROSTER_WORTH_BASIS`. It answers
  "what is this chair worth", which is the question `universal_value` — an asset LEVEL — can
  actually carry.
- **`starter_value_*` is retained, not deleted.** It answers a real and different question: can
  this roster field a legal lineup, and what does the forced assignment cost.
- **`forced_negative_starters` now travels with it**, per roster and in aggregate, and the
  console line prints `[N started below replacement, forced -- see #211]`. Absence and zero stay
  separate: an unmeasured count says so, a measured zero prints nothing.
- The `roster_strength` docstring called `starter_value` "the roster-quality number: it is what
  the team actually fields". That sentence is corrected. A docstring asserting the opposite of
  its code is what let #168 survive a reader who was specifically checking for that defect.

**NO FINDING CHANGES, AND NO COMMITTED NUMBER IS REWRITTEN.** The battery's findings are legality
checks and none has ever read `starter_value`. The figures in both committed evidence files were
produced by the code as it stood; they are left exactly as generated. What this changes is their
READING — where those files say `starters X-Y`, that is a lineup total contaminated by forced
below-replacement assignment, not a roster-worth measure. `12T_ppr_mode_upside starters -205.4`
is the clearest case and is now explicable rather than alarming.
