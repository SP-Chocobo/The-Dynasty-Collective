# The even flex split is measured FALSE, and it is #216 in both of its directions

`run_216_flex_share_probe.py`. Instrument only: it changes no engine behaviour and no constant.

## The claim under test

`draft_room.starter_slot_counts` splits a flex slot's capacity EVENLY across the positions it
admits — a WR/RB/TE `FLEX` counts +1/3 toward each — and justifies it in its own docstring with
a claim about the world:

> Every other flex type (FLEX, WRRB_FLEX, REC_FLEX, IDP_FLEX) keeps the even split — those
> genuinely do get filled by whichever eligible position is best roughly interchangeably in
> real drafting behavior, unlike SUPER_FLEX's real-world QB dominance.

Those counts are the demand that sets every replacement RANK, and the rank picks the replacement
LEVEL that `bpa` subtracts. If the split is wrong, every price at every position is wrong by a
fixed amount whose direction the FORMAT decides.

## How it is measured without circularity

Looking at finished rosters would be worthless: they were drafted BY the anchor under test. A
board that prices tight ends high produces tight-end-heavy rosters, which would then "confirm" a
high tight-end flex share.

So the measurement never looks at a drafter. Who wins a flex is a property of the PROJECTION
CURVE and the RULEBOOK: field the whole league optimally out of the whole scoreable pool —
`num_teams` copies of every starting slot, one exact maximum-total-points assignment through the
lineup optimizer this repo already has (#126, no second solver), eligibility from
`fantasy_positions` (#172). Every league starting slot is fillable in every format measured
(96/96, 108/108, 108/108), so the population is not vacuous.

## Result — 12 teams, pool 481

| format | FLEX (24 slots) | even split assumes | SUPER_FLEX | assumes |
|---|---|---|---|---|
| 12T_ppr | **WR 20, RB 4, TE 0** | RB 8, TE 8, WR 8 | — | — |
| 12T_ppr_SF | **WR 20, RB 4, TE 0** | RB 8, TE 8, WR 8 | **QB 12** | QB 3, RB 3, TE 3, WR 3 |
| owner's league | **TE 18, WR 5, RB 1** | RB 8, TE 8, WR 8 | **QB 12** | QB 3, RB 3, TE 3, WR 3 |

(owner's league also has a `WRRB_FLEX`: **WR 11, RB 1** against an assumed 6/6.)

Per-position starting demand and the replacement RANK it produces:

| format | position | assumed | DERIVED | assumed rank | DERIVED rank |
|---|---|---|---|---|---|
| 12T_ppr | TE | 1.667 | **1.000** | 20 | **12** |
| 12T_ppr | WR | 2.667 | **3.667** | 32 | **44** |
| 12T_ppr | RB | 2.667 | 2.333 | 32 | 28 |
| owner's | TE | 0.717 | **1.500** | 9 | **18** |
| owner's | RB | 3.217 | **2.167** | 39 | **26** |
| owner's | WR | 3.217 | 3.333 | 39 | 40 |

## Why this is #216, in both directions, from one derivation

- **12T_ppr (a dedicated TE slot).** The top 12 tight ends are consumed by the dedicated slots.
  TE13 and below then lose every flex to WR25-WR48 (TE18 177.6 against WR44 200.6). TE's true
  demand is its dedicated slot and nothing more. The assumed split inflates it to 1.667, pushing
  the replacement rank from 12 out to 20 — the 20th tight end, a much worse player, a much lower
  level, and therefore a much HIGHER `bpa` for every tight end on the board. **That is defect
  (a): the ~43.5-point tight-end bias.** The derived rank moves the anchor back to TE12.
- **The owner's league (NO dedicated TE slot, three flexes, a 0.5 TE premium).** Nothing consumes
  tight ends, so they are unconsumed inventory and they WIN the flexes: TE18 211.6 beats WR44
  200.6. The assumed split hands TE only 0.717 of a slot — rank 9, the 9th-best tight end as the
  free alternative, a very high level, and tight ends priced at nearly nothing. Meanwhile RB is
  handed 3.217, rank 39, a bottom-of-the-barrel free alternative, and running backs price high
  enough to win all three flexes. **That is the zero-tight-ends result**, and the derived ranks
  (TE 9 -> 18, RB 39 -> 26) move both anchors the other way.

The owner said this before it was measured: *"with no TE slot, but flex that can field them, the
TE act as de-facto WR."* The derivation reproduces it from the rulebook and the projection curve
alone, with nothing about tight ends written anywhere.

**One derivation moves the anchor in OPPOSITE directions in the two formats, each time toward
the roster a person would actually build.** A knob tuned to fix the lab would have made the
owner's league worse.

## Stability — the direction does not turn over

Per-team flex occupancy at league sizes 8, 10, 12, 14, 16 (same pool, same rulebook):

| format | slot | 8 | 10 | 12 | 14 | 16 | even split |
|---|---|---|---|---|---|---|---|
| 12T_ppr | FLEX WR | 1.25 | 1.40 | 1.67 | 1.71 | 1.56 | 0.67 |
| 12T_ppr | FLEX TE | 0.00 | 0.00 | 0.00 | 0.00 | 0.25 | 0.67 |
| owner's | FLEX TE | 1.25 | 1.50 | 1.50 | 1.50 | 1.50 | 0.67 |
| owner's | FLEX WR | 0.38 | 0.20 | 0.42 | 0.50 | 0.44 | 0.67 |
| owner's | SUPER_FLEX QB | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.25 |

Magnitudes move with league size — correctly, since a deeper league drains the pool differently,
and being league-specific is exactly what `starter_slot_counts` claims to be and is not. The
DIRECTION never turns over at any size.

**`SUPER_FLEX_QB_SHARE = 0.85` measures 1.00 at every league size tested.** It is a hand-set
constant standing in for a quantity that can be derived, which is what #56 exists to prevent.

## Cost

The whole league-wide solve is **0.01–0.02s** on a 481-player pool. It is not a performance
question.

## What this does NOT establish

That an optimal league-wide fielding is what real managers achieve. It is not — it is the
counterfactual the replacement level is DEFINED against ("the freely available alternative for a
starting slot"), and stating it is the point. Nothing here has been wired into the engine yet,
and no number in this file was produced by a board.
