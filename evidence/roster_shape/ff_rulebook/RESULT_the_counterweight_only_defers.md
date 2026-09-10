# The counterweight defers; it does not decide — and that closes the "unexplained" item

Pure reads of artifacts already on disk (`aggregate_selection_raw.json`, `ff_draft.json`). No
engine run, no board built, no engine source changed. Basis: ARTIFACT-READ.

This closes the one item `RESULT_displacement_is_the_counterweight.md` left explicitly open:

> The finished total (101) matches the opening `bpa` top-312 (101) closely on every position …
> that match is either a coincidence of the mixture or a constraint of the pool's structure.
> **I do not know which.**

I know now. It is neither, exactly — it is a **deferral**, and it is visible player by player.

---

## 1. Why the opening board could never show the counterweight

`displacement_adj` is **0.00 on all 481 priced rows of the opening board.**

That is structural, not a finding about receivers: with an empty roster every dedicated slot is
open, so each position's probe evicts its own position's phantom, `displaced == level`, and
`adjustment = level − displaced = 0` for every position at once.

**So the opening board IS the `bpa` sort, by construction.** My original probe measured a state in
which the counterweight cannot exist, and read the result as though it governed a draft in which
it does. That is the mechanical reason the 19th withdrawal was necessary, and it is worth stating
plainly: *the board built for an empty roster is not a preview of the draft; it is the one state
where half the valuation is switched off.*

## 2. The two regimes disagree with the sort — in opposite directions, by the same amount

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| opening `bpa` ranks 1–168 | 32 | 46 | 58 | **32** |
| draft rounds 1–14 (balanced) | 32 | 44 | 66 | **26** |
| opening `bpa` ranks 169–312 | 2 | 37 | 36 | **69** |
| draft rounds 15–26 (upside) | 0 | 40 | 29 | **75** |

The balanced half takes **6 fewer** tight ends than the sort would; the upside half takes **6
more**. Net zero. The totals coincide (101 = 101) while neither half matches.

## 3. The deferral, confirmed player by player

Of the players in `bpa` ranks 1–168 that rounds 1–14 declined:

```
declined by the balanced half : TE 6, RB 2   (8 players)
taken in rounds 15-26 instead : TE 6, RB 2   (8 players)
never taken at all            : 0
```

**Every single player the counterweight pushed out of the early rounds was harvested by the
upside rounds.** Not a similar number — the same players.

## The statement

**The displacement counterweight, applied for only 54% of the draft, changes WHEN a tight end is
taken, not WHETHER.** The tight ends it defers are still in the pool when it is switched off at
round 15, and they go then. Composition is conserved because the deferral has nowhere to leak to:
312 of 481 priced rows are consumed, so a player deferred past round 14 is still comfortably
inside the draft's reach.

This is the same conservation RESIDUAL5 measured under pick-order permutation, arriving from a
different direction, and it now has a mechanism rather than an observation.

## What it explains that was previously loose

- **Why the composition matched the opening sort.** Not causation, and not coincidence: the sort
  is the counterweight-free ordering, and the draft spends 46% of itself in exactly that regime
  while the other 54% only postpones.
- **Why PHASE4's "force balanced" did not reproduce the human numbers either.** Forcing balanced
  for all 26 rounds gave TE 21.8% overall, not the 15.5% the balanced rounds produce. The
  counterweight's magnitude depends on the roster it is measured against, and by round 15 that
  roster is not the round-1–14 roster. A term that defers is not a term that fixes.
- **Why the balanced half looks human.** It is not that balanced mode "gets the answer right"; it
  is that in rounds 1–14 the counterweight is large enough to hold tight ends back. Whether it
  would still do so if it ran the whole draft is answered above, and the answer is no.

## What this does NOT establish

Not that deferral is wrong — a valuation that ranks a player highly and a draft that takes him
late are not in conflict, and no contract says otherwise. Not that the counterweight should run
longer, or the anchor differently. **Per the standing prohibition, none of this is evidence about
whether the normalization is desirable.** It is an account of what the current one does.

And one honest limit: this is one draft, one league, one pool. The deferral is exact here (8 of 8);
it is not shown to be a law.

---

## Addendum — the regime split survives a pick-order permutation

The "balanced rounds look human" result rests on one draft, which is thin. `ff_draft_3rr.json` is
the same league and pool under **third-round reversal** — a genuine perturbation that changes 129
of 312 overall picks and scrambles ~90% of seat assignments (RESIDUAL5).

| arm | | QB | RB | WR | **TE** |
|---|---|---|---|---|---|
| base | rounds 1–14 | 32 (19.0%) | 44 (26.2%) | 66 (39.3%) | **26 (15.5%)** |
| **3RR** | rounds 1–14 | 31 (18.5%) | 43 (25.6%) | 68 (40.5%) | **26 (15.5%)** |
| base | rounds 15–26 | 0 | 40 (27.8%) | 29 (20.1%) | **75 (52.1%)** |
| **3RR** | rounds 15–26 | 1 (0.7%) | 41 (28.5%) | 27 (18.8%) | **75 (52.1%)** |
| twelve real managers | whole draft | (20.0%) | (27.4%) | (37.1%) | **(15.5%)** |

**Identical tight-end counts in both regimes — 26 and 75 — under a permutation that changes who
picks when from round 3 onward.** Every other position moves by at most 2. So the regime split is
a property of the two valuations, not of this particular pick order, and the balanced half's
agreement with the humans is not an artifact of one draft's sequence.

Still one league, one rulebook, one pool. Two arms is not a population.
