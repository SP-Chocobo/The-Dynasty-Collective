# Dialling it in: two of my own claims withdrawn, and the real remaining blocker

Three measurements, each of which corrected something I had already published.

## 1. WITHDRAWN — "the QB anchor is constant while every other position's moves"

I said the four-quarterback seat came from QB's level sitting at 207.5 all draft while other
positions' anchors moved. **Measured, every position's level per round, owner's league seat 1
(`levels_probe.py`, level recovered as `projection − bpa` from the row itself so it is true on
both the demand-rank and startable-floor branches):**

| rnd | QB | RB | WR | TE |
|---|---|---|---|---|
| 1 | 207.5 | 154.7 | 209.9 | 254.1 |
| 5 | 207.5 | 154.7 | 209.9 | 229.3 |
| 9 | 207.5 | 147.8 | 200.6 | 254.1 |
| 14 | — | 141.5 | 209.9 | 254.1 |

**Nothing moves much.** RB drifts 13 points across fourteen rounds; WR and TE wander and come
back. That is `replacement_levels`' own documented property — rank shrinkage and pool drain cancel
while picks come off the top — holding for every position, QB included. **My asymmetry claim was
wrong.**

The real asymmetry is in the LEVELS THEMSELVES, and it is the flex-share finding again:
**RB 154.7, QB 207.5, WR 209.9, TE 254.1.** A running back needs to beat 154.7 to price
positively; a tight end needs to beat 254.1. That is a 99-point head start for running backs in a
league whose own optimal fielding uses 3.76 of them and 5.06 receivers.

## 2. WITHDRAWN — "a four-quarterback roster is a bad roster, so this cannot ship"

I blocked shipping on it. **The derived band says QB 3.11 for the owner's league, so its integer
neighbourhood ceiling is 4.** And he said it himself, before any of this was measured: *"usually
2-3-4 qb at most."* **QB 4 is at the ceiling, not past it.**

The distinction from the flex share's four-tight-end seat is real and not special pleading: TE's
target there was 2.07, ceiling **2**, so TE 4 was **+2 OVER** — the largest single breach in the
whole table. QB 4 against a ceiling of 4 is **+0**.

**So I blocked on the wrong seat.** Withdrawn.

## 3. The instrument that should have been used all along: band breaches

Counting positions outside `[floor(target), ceil(target)]` across all nine seats:

| arm | breaches | worst single breach | band distance | strict ordering | owner's reading | legal |
|---|---|---|---|---|---|---|
| SELF (shipped) | **24** | +2 | 47.45 | 6/9 | 6/9 | 9/9 |
| SHARED | 19 | **+4** | 39.41 | 6/9 | 7/9 | 9/9 |
| SHARED + `depth_exposure` demoted | **18** | **+4** | **37.33** | **8/9** | **8/9** | 9/9 |

The owner's league is where it shows most: all three seats go from three breaches each
(QB −1, RB +2, TE −2) to one or two, and seat 6 lands on **QB3 / RB4 / WR4 / TE3** against a band
of 3.11 / 3.76 / 5.06 / 2.07 — one breach, of one.

## 4. THE REAL REMAINING BLOCKER: ten receivers

**12T_ppr_SF seat 1 goes 2/3/8/2 → 2/2/10/1.** WR's band target there is 5.69, ceiling 6. **Ten
of fifteen roster spots are receivers — +4 over the ceiling, the largest breach anywhere in the
table, and worse than the shipped engine's +2 in the same seat.**

That is a degenerate roster of exactly the KIND that opened #216 — eight tight ends in a one-TE
league. Shipping a positional-hoarding repair that produces a ten-receiver seat, while calling it
a repair, would fail the test the item exists for. **Same standard, applied to my own change.**

## 5. The asset ruler cannot arbitrate this change

Re-scored on all three sets (`asset_sets/`, harness reproducing every recorded number):

| format | seat | floored SELF → SHARED | starter SELF → SHARED |
|---|---|---|---|
| 12T_ppr | 1 | 634.5 → 633.7 | 632.4 → 633.7 |
| 12T_ppr | 6 | 580.4 → 493.5 | 578.9 → 484.9 |
| 12T_ppr_SF | 1 | 888.6 → 751.5 | 877.6 → 744.4 |
| 12T_ppr_SF | 6 | 832.6 → 684.8 | 823.0 → 680.0 |

Down on every reading in five of six seats — and **this cannot decide the question.** The ruler is
`universal_value` summed over a roster, and `universal_value` contains `bpa`, which is
**each player's value over HIS OWN position's replacement level.** A roster of running backs
(anchor 154.7) sums higher than a roster of receivers (anchor 209.9) at equal projections, purely
from the anchors. The change exists to stop the board chasing that same head start.

So the asset ruler and the change disagree about whether the per-position anchor is right — which
is #211 and #155 — and a ruler that shares a defect cannot referee its repair. `universal_value`
is byte-identical in both arms; what differs is which players were taken. The one anchor-free
ruler here is **lineup points**, and it says **−0.53%**.

## Where this leaves it

The repair is right about the comparison and is measurably better on every shape ruler derived
from the owner's own stated rules. It costs half a percent of expected points, which is inside any
competitive band. Two of my three objections to it were my own errors and are withdrawn.

**The one that survives is the ten-receiver seat**, and it survives on the same arithmetic that
rejected the four-tight-end seat. That is what has to be understood before this ships — not the
quarterbacks, and not the asset ruler.
