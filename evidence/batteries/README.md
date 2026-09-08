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
