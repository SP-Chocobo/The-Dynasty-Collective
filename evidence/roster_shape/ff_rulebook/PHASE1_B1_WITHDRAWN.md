# PHASE 1 GATE: B1 as published is WITHDRAWN. The mechanism is real but differently located.

The gate was: *read `displaced` out of `displacement_level` instead of inferring it, and
state the mechanism in one sentence before any repair.* Done. The repair is NOT started,
because what the gate found is not what B1 claimed.

## What B1 claimed (WRONG)

> The deduction rises −51.7 → −120.4 as a seat goes from two to six tight ends, then
> **returns to −51.7 at seven and sticks**. The saturation brake releases exactly when it
> is needed.

## What the production path actually shows

Both earlier probes made the same mistake: they recomputed the replacement level from
`compute_draft_board`'s **output rows** rather than reading the `point_replacement`
production actually uses. Walking the real path — `roster_points_lookup` →
`_team_roster_points_players` → live `point_replacement` → `displacement_adjustments`:

| TE held | pick | level_TE | displaced | adjustment |
|---|---|---|---|---|
| 3 | 110 | 139.44 | 195.36 | −55.92 |
| 4 | 133 | 128.80 | 195.36 | −66.56 |
| 5 | 157 | 103.10 | 195.36 | −92.26 |
| 6 | 181 | 74.99 | 195.36 | −120.37 |
| 7 | 182 | 74.82 | 195.36 | −120.54 |
| 8 | 206 | **143.63** | 195.36 | **−51.73** |

(The 2-held row is omitted: my method recovers `displaced` with a zero-level probe, which
degenerates there. It is an artifact of the recovery, not a measurement.)

**The brake does not release.** The adjustment falls at 8 held because **`level_TE` nearly
doubles**, 74.82 → 143.63, between picks 182 and 206. `displaced` never moves. The
anomaly is in `replacement_levels`, not in `displacement_level`, and a rising level as a
position drains league-wide is the documented, intended behaviour.

## The mechanism, in one sentence — which is the gate's actual deliverable

`displaced` is **pinned at 195.36 from three tight ends held onward** — the weakest
occupant of any slot a tight end can reach — and because the league anchor cancels
(`bpa + displacement_adj = projection − displaced`), **every tight end is priced against
my own third-best tight end, forever, no matter how many I already hold.**

A ninth tight end projecting 120 and a third tight end projecting 120 receive the
identical net price. The engine cannot distinguish them. That is a genuine saturation
failure — the eviction target stops responding once my starters are set — but it is the
opposite shape from what B1 described, and it lives in what `displaced` MEANS rather than
in a brake that releases.

## Status

- **B1 as published: WITHDRAWN.** Fourteenth withdrawal of this pass.
- **B1': SURFACED, not yet repaired.** `displaced` is invariant to bench saturation.
- **No repair written.** The gate exists so a fix is not built on a mis-stated mechanism,
  and it just caught one — for the second time on the same defect.
- **Not yet answered:** why `level_TE` jumps 74.82 → 143.63 across 24 picks. It may be
  correct (league-wide TE scarcity raising the anchor) or it may be a rank-target
  discontinuity. It must be read out before B1' is repaired, for exactly the reason this
  file exists.

## Method note, for the plan

Both bad probes shared one root cause and it is now a rule: **never recompute a quantity
production computes internally.** `replacement_levels(pd.DataFrame(board_rows), …)` is not
`point_replacement`; the board's rows are a filtered, scored projection of a different
population. Read production's value or call production's function — do not rebuild it from
its own output.
