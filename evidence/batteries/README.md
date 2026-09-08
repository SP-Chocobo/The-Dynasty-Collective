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
