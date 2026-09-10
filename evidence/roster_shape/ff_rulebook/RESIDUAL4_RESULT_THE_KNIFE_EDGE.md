# RESIDUAL4 — **FORK A**, and the decision is a difference of two nearly-cancelling quantities

Forks fixed and committed before the run. Both arms read production board rows. **No engine
source changed.**

## Fork C first: the selection path stays exonerated

At all **27 of 27** hoarder picks where a tight end was taken, the chosen player **was the
board's top row by `final_score`**, and that top row **was a tight end**. `narrow_candidates`
picked what the board ranked first. Nothing downstream overrode anything. That is now 32 picks
of evidence, not 5.

## Fork A: it wins on `bpa` — but the interesting part is what the control shows

Per-term margin, the chosen tight end minus the best NON-tight-end row on the same board.
Positive means the term favoured the tight end.

| arm | n | **bpa** | need | elig | depth | **displacement_adj** | net final margin |
|---|---|---|---|---|---|---|---|
| HOARDERS, at picks where they TOOK a TE | 27 | **+76.21** | +0.15 | +0.00 | −0.38 | **−71.40** | **+0.01 … +13.45** |
| STARVERS, at picks where they did NOT | 40 | **+77.17** | +0.61 | +0.00 | −2.57 | **−83.54** | **−4 … −19** |

**`need_bonus`, `eligibility_bonus` and `depth_exposure` are noise.** Their largest group mean
is 2.57 points against terms worth seventy to a hundred and sixty. Fork B is dead: no
unexamined term is responsible.

## What the numbers actually say

**The bpa margin is the same for both groups — +76.21 against +77.17.** Every seat is handed
essentially the identical tight-end advantage, and it is the anchor gap: WR's level 217.75 minus
TE's 149.17 is **68.58**, and a same-points tight end gets exactly that. The first row of the
table is `bpa +68.59` against `displacement −68.95`, net **+0.07**.

**What differs between the groups is only the deduction: −71.40 against −83.54.** Twelve points.

So the engine's tight-end-versus-receiver decision is:

```
(a level gap of ~+77)  +  (a deduction of ~−71 to −84)  =  a residual of a few points
```

**and the residual decides the pick.** Observed net margins include **+0.07, +0.01, +0.22** — a
tight end taken over a receiver by one hundredth of a point, out of two terms each worth
seventy-plus.

## This is a knife-edge, and it explains the bimodality without any new mechanism

When an outcome is the small remainder of two large, nearly-equal, oppositely-signed quantities,
tiny differences in roster state flip its sign. A twelve-point difference in the deduction — well
inside the range roster composition produces — is more than enough to move a residual that is
routinely under a point.

That accounts for what RESIDUAL1 found and RESIDUAL2 and RESIDUAL3 could not explain: **twelve
seats running identical code, positionally identical at tight end through pick 9, diverging to
1-versus-15 by pick 26.** They are not following different rules. They are landing on opposite
sides of a near-tie, repeatedly.

It also explains why every earlier probe failed. RESIDUAL2 asked whether the deduction's
*absolute magnitude* predicts hoarding and found overlap — correctly, because magnitude is not
what matters. What matters is the deduction *relative to the alternative's*, against a bpa
margin that is constant across seats. Nobody was going to see that by looking at one term alone.

## What is NOT claimed

- **Not that any term is wrong.** bpa is `points − level` and the level is the anchor the #50
  work already ruled correct for this consumer. The deduction is measured and, per the
  cancellation result, does not carry the level's staleness into the price. Each term is behaving
  as specified.
- **Not a feedback loop.** That a seat's own choices change its next deduction is arithmetically
  true and I have not measured that it compounds. The knife-edge explains divergence without
  needing it.
- **Not that the near-tie is a defect.** Two competing valuations landing within a point of each
  other may be the honest answer — the players may genuinely be that close. What it means is that
  the OUTCOME is not robust, and a system whose positional allocation is decided by hundredths is
  one where any small change anywhere moves the roster shape a lot.

## Artifact risks, stated

- Both arms select on the outcome (took / did not take a tight end). **The robust half is the bpa
  margin**, which is a property of the board and comes out the same in both arms; the deduction
  margins are the outcome-dependent half.
- One draft, twelve seats, 67 picks total across the two arms.
- "Best non-TE alternative" is a chosen comparator — the top non-TE row by `final_score`.

## What this makes next

The question is no longer "which term is wrong". It is **"is a positional decision settled by a
sub-point residual of two seventy-point terms an acceptable design?"** — which is a modelling
question of the same family as the #50 ruling, and the owner's, not mine.
