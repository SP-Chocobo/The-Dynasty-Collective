# PROVENANCE ESTABLISHED. There is no anomaly — and my Phase 2 rank read was of the wrong call.

Interception-artifact check first, as agreed, then the literal
`value → producer → caller → consumer` trace. No engine code modified.

## 1. Interception artifact: RULED OUT

The spy worked. At picks 182 and 206 the LIVE `replacement_levels` genuinely returned `{}`
for every position — exhausted demand — and the board still carried levels. That was a real
observation, not an instrumentation failure.

## 2. The chain, read from source

| step | where |
|---|---|
| **producer** | `replacement_levels(…, remaining_demand=None, …)` — draft_room.py:2359, called inside `predraft_replacement_anchor` over the FULL pool, nobody drafted |
| **cache** | `_ANCHOR_CACHE`, keyed by `anchor_cache_key` (draft_room.py:2265) on merger + players_db fingerprints, usable_positions, roster_positions, num_teams, value_col, sleeper_projections, scoring_settings, pool_scope, startable_floors, sleeper_basis |
| **caller** | `compute_draft_board` line 2920 → `_fill_omitted_from_anchor` (draft_room.py:2390) fills positions the LIVE call omitted **for exhausted demand**, and explicitly never those the `startable_floors` branch declined |
| **consumer** | `displacement_adjustments` (line 3121) receives the merged dict |
| **provenance record** | line 2982 stamps `replacement_basis = 'predraft_anchor'` on every affected row |

**This is documented, intentional, and already observable.** The cache's own docstring calls
it "a pure function of (player universe, league settings) instead of a memo of earlier
calls", and the filler's docstring says it exists "so the board can record that their price
rests on the pre-draft anchor rather than a live one … instead of presenting both as the
same kind of claim."

**The provenance anomaly is dissolved.** Nothing reached valuation from an untraced source.

## 3. What production's own stamp says

| pick | positions on the PRE-DRAFT anchor | positions on a live basis |
|---|---|---|
| 109 | WR | QB, RB, TE |
| 157 | WR | QB, RB, TE |
| 182 | WR | RB, TE |
| **206** | **RB, TE, WR** | **none** |

**By pick 206 every position's replacement level is the pre-draft anchor** — the levels as
they stood with nobody drafted. The late-draft displacement deduction is computed entirely
against them. QB drops out of the table at 182 because the `startable_floors` branch
declined and the filler correctly refuses to revive it.

I am NOT calling this wrong. It is a documented design with a stated rationale, and whether
a pre-draft anchor should price a round-18 bench pick is a question for the owner, not a
defect I found.

## 4. A correction to Phase 2, before it propagates

`PHASE2_RESULT_levels.md` reports the WR level landing at "RANK 37 of 198 remaining
receivers, on Jordan Addison". **That read sampled one of three `replacement_levels` calls
on that board and I did not verify which.** `predraft_replacement_anchor` calls
`replacement_levels` internally, so my spy caught the ANCHOR's own call as well as the live
one — and production's stamp says WR was pre-draft-anchored at pick 109, which means the
call I sampled was most likely the anchor's, over the FULL pool rather than the remaining
one.

**The rank/identity conclusion survives** — a level landing on the demand rank, on a real
named player, is correct behaviour for whichever call produced it. **The label "of 198
REMAINING receivers" does not**, and is withdrawn. Sixteenth withdrawal.

This is the fourth time in this investigation that sampling the wrong call or the wrong
population produced a plausible number about the wrong thing. The doctrine rule needs a
second clause: **when a function is called more than once per operation, an instrument must
identify WHICH call it captured, not merely that it captured one.**

## 5. Status

- Three primitives exonerated (displacement_level, the optimizer, replacement_levels).
- Provenance established; no untraced path; no defect claimed.
- **Open, and now precisely stated:** should a pre-draft replacement anchor price bench
  picks in the last third of a draft? That is a semantics question with a documented
  rationale on one side and no measurement on the other.
- Flex-anchor candidate still stranded. No battery. No engine source modified in #222.
