# #50 RULING INPUT: what is discarded when a replacement level switches live → PRE-DRAFT

> **SUPERSEDED by `PHASE2_RULING_INPUT_50.md`.** That document answers the
> same question at every pick rather than at four sampled ones, locates the exact
> crossing pick per position, reads production's own selection decision out of
> `_fill_omitted_from_anchor`, and reaches a ruling recommendation. The gaps quoted
> below (+13.97 / +40.53 / +44.84 / +68.81) are correct but were measured at sampled
> picks AFTER the crossing, which mixes the jump at the switch together with how far
> the position had drained since. Read the superseding document instead.

Measured, not argued. `phase3_live_vs_anchor.py`, real rulebook, real universe. Every
capture is TAGGED by which invocation of `replacement_levels` it came from, identified from
the arguments — the instrument rule earned by the sixteenth withdrawal.

**This file makes no recommendation.** It states what the switch costs so the ruling can be
made on the semantics rather than on roster shape.

## The measurement

Where BOTH a live level and the pre-draft anchor exist, the live level is always LOWER, and
the gap widens through the draft:

| pick | position | live | pre-draft anchor | what the switch would add |
|---|---|---|---|---|
| 157 | RB | 156.84 | 170.81 | **+13.97** |
| 157 | TE | 108.64 | 149.17 | **+40.53** |
| 182 | RB | 125.97 | 170.81 | **+44.84** |
| 182 | TE | 80.36 | 149.17 | **+68.81** |

At pick 109 the two agree exactly (delta +0.00 for QB, RB, TE) — early in a draft the pool
has not drained enough to separate them, which is the cancellation `replacement_levels`
documents.

## What the live level knows that the anchor cannot

**A drained pool.** The live level ranks the REMAINING players at live starter demand; the
anchor ranks the FULL pool with nobody drafted. As the good players leave, the live marginal
starter gets worse and the live level falls. The anchor cannot fall — it is a pure function
of (universe, league settings) by construction and by its own docstring.

So the discarded information is precisely: **how much the position has been consumed so far.**

## The mechanical consequence, stated without a verdict

`displacement_adj = level − displaced`. A HIGHER level yields a SMALLER (less negative)
deduction. So at the moment a position's live demand exhausts and the board falls back to
the anchor, **the deduction charged to the next player at that position weakens by the gap
above — 45 to 69 points on this rulebook.**

That is the arithmetic link to the behaviour that started this investigation: at pick 206
tight end's level goes from a live ~80 to the anchor's 149.17, the deduction moves from
−120.54 to −51.73, and tight ends get cheaper at exactly the point a chair already holds
eight of them.

**I am not calling that wrong.** The correlation is real and it is not evidence. The anchor
exists for a stated reason and the board marks every row that uses it.

## A third state, worth naming

QB at picks 182 and 206 is **absent entirely** — no live level, and `_fill_omitted_from_anchor`
correctly refuses to fill it because the `startable_floors` branch declined rather than
exhausting demand. Those rows carry no replacement basis at all. That is the absence contract
working, and it means the vocabulary here has three states, not two: **live**, **pre-draft
anchor**, and **no replacement exists**.

## The ruling, for the owner

**Option A — the anchor is the intended stable definition.** Once live demand is exhausted,
"what a freely available player at this position was worth" is a league-level constant, and
reverting to it is correct. Leave everything alone. The 45–69 point weakening is the price
of a stable definition and is accepted knowingly.

**Option B — late-draft selection needs a different quantity.** If a bench pick in round 18
should be priced against something that still reflects the drained pool, then that quantity
must be **defined explicitly first** — it is not "the anchor, but lower", and it is not the
live level either, since the live level is omitted precisely because its demand basis is
gone. Naming it is the work; wiring it is downstream of naming it.

**What must NOT happen:** modifying the anchor because it correlates with the tight-end
shape. That is the component-presence reasoning this whole investigation has been
eliminating, and it would be the seventeenth withdrawal waiting to happen.

## State of #216 / #222

- B1 dead. B1' dead. Optimizer exonerated. `replacement_levels` correct. Anchor provenance
  legitimate and already observable via `replacement_basis`.
- **No engine source modified anywhere in #222.**
- Flex-anchor candidate still stranded — and now for a third reason: it was derived under
  the assumption that replacement behaviour was malformed, and that assumption is dead.
- Next action is a RULING, not a measurement.
