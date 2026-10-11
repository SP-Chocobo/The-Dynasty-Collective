# `positional_forfeit` has no calibration of its own, and now it has a measurement

**Question.** The forfeit is shown on every door: *"If you wait, the best left at #67 nets about
39.5, which is 6.0 less than taking one now."* Its cousin `survival_probability` was measured,
failed, and is withheld on every surface. The forfeit had never been asked anything.

**What existed before.** `evidence/forfeit_knife_edge/` is a QUANTISATION probe — `#86`, whether
`round(expected_taken)` sits on a knife-edge. It is not a calibration and never asks whether the
prediction matched what happened. So the number was drawn with nothing behind it.

## What was measured

`expected_taken` — "how many players at position P go between this turn and my next one" —
because the forfeit is that position's value curve walked down by `round(expected_taken)`, and
because that quantity is roster-independent. The value terms are not: my own roster changes
between the two turns, so a difference between the predicted and actual next-turn value would
confound the model with my own pick.

**416 (turn, position) pairs, six formats, real replayed drafts, turns chosen on the gap ahead.**

| predictor | MAE | bias |
|---|---|---|
| **model `expected_taken`** | 1.459 | **−1.075** |
| per-position constant | **1.388** | 0.000 |
| gap × prior share | **1.365** | 0.000 |
| nothing gets taken | 2.077 | −2.077 |

It loses to both naive baselines pooled, and beats its own per-position constant in only **2 of
6 formats**. The reliability curve is off by roughly 2× and monotonically, which makes this a
bias rather than noise:

```
predict 0.56  ->  actual 1.32
predict 1.37  ->  actual 2.60
predict 2.36  ->  actual 4.68
predict 3.84  ->  actual 7.33
```

So on this instrument it fails the same bar survival failed, in the same direction: it loses to
a constant.

## What follows, and what does not

**The bias runs one way.** Under-counting takes walks the curve down too few players, so the
next-turn value is overstated and the displayed cost of waiting is *understated*. The door's
number is a floor, not an estimate. That is a conservative aid, which is categorically different
from survival's "62% he lasts" — a per-player probability a reader leans on directly.

**It is therefore labelled, not withheld.** The basis line in the numbers panel now says the
expected takes measured about one player per position low and that the figure reads as a floor.
Withholding it would be the wrong instrument for this failure: `#187` exists because a reader
shown nothing assumes the data was missing and reasons around the gap, and unlike the survival
family this number is already framed as an aid beside the rank rather than a claim.

**The door headline was deliberately left alone.** Writing "at least 6.0 less" onto the main
surface would promote one measurement against engine-driven drafters into a claim about every
draft. The limit belongs in the panel until it has been checked against human ones.

## The confound that was ruled out, and the one that was not

**Ruled out, non-vacuously.** If `expected_taken` only claims to predict takes from the PRICED
pool while the instrument counts every body drafted, the model would look systematically low for
free. Both populations are recorded per row. The restriction is not vacuous — the priced filter
excludes **489 of 970** board rows on an opening `12T_ppr` board — and it changed nothing: every
intervening pick in every replay was already priced, so both counts are identical to three
decimals.

**Not ruled out.** Takes are attributed by `players_db` position, so a multi-eligible player
taken into a flex counts under his listed position. If the engine counts by the opponent board
row's position instead, some of the gap is attribution rather than prediction. WR carries the
largest bias (−2.04), which is where that would bite hardest.

**Scope limit.** The replays are engine-driven drafters (VDS `sharp_auto`), not humans. It cuts
both ways: failing to predict its own kin is not a weaker indictment than failing to predict a
stranger.

## `#56`, held

This measures. It tunes nothing, and no number here may be written back into the engine as a
constant — the capture's LIMITS forbid calibrating against one league, and that prohibition does
not soften because the error was measured rather than guessed.
