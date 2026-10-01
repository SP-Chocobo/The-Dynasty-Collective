# STOP: the ordering repair loses ~6 points of relative quality in every format

*Measured on the bar the v1 freeze was actually held to, not on the one I had been using.*

## The result

Same harness, same six formats, same field (`adp`, `need_first`, `points_need`), same pool of
481, same rounds, same ADP coverage (840 ranked / 4,506 sentinel-excluded). **The only variable
is the engine.**

### `points` — the INDEPENDENT ruler, the "strong claim"

| format | v1 | v2 | delta | v1 wins | v2 wins |
|---|---:|---:|---:|---:|---:|
| 10T_ppr | +2.018 | −3.495 | **−5.513** | 10/10 | 2/10 |
| 10T_ppr_SF | −0.901 | −4.104 | **−3.203** | 5/10 | 1/10 |
| 12T_ppr | +2.131 | −5.353 | **−7.484** | 11/12 | 2/12 |
| 12T_ppr_SF | +0.505 | −6.563 | **−7.068** | 6/12 | 2/12 |
| 12T_ppr_TEP | +2.632 | −2.663 | **−5.295** | 12/12 | 5/12 |
| 12T_standard | +5.151 | −2.824 | **−7.975** | 12/12 | 5/12 |
| | | | **−6.090 mean** | | |

**v1 won or drew on points in five of six formats. v2 loses in all six**, and the seat win rate
collapses from 10/10, 11/12, 12/12 to 2/10, 2/12, 5/12.

### `cdme` — the engine's own objective, where a win is a tautology

Mean delta **+6.490**. It got *better* at its own scoring function.

**Better on its own objective, worse on the independent one, in every format.** That is the
signature of fitting the objective rather than the task.

## Why my own validation missed it

I measured the repair's cost with a roster A/B: twelve chairs, all running the engine, once
under each ordering. It came back **−0.5%**, and I reported the repair as nearly free.

That design cannot see this failure, and the repository already says so. `draft_battery`'s own
docstring, under DELIBERATELY NOT AUDITED:

> *"Whether the VALUATION is correct. Every chair uses the same engine, so a battery cannot
> detect a systematic mispricing — it would produce twelve consistently wrong rosters and every
> structural check would pass."*

**Self-play hides a systematic mispricing by construction**: when every chair drafts worse in the
same direction, the relative measure barely moves. Against a fixed field of different styles it
shows immediately. I had the warning, applied it to the battery, and then built my own A/B with
the identical flaw.

## The mechanism, and it joins this to `#21`

The repair moved the board's ordering onto `acting_now_value`, which is built from
`positional_forfeit`. The calibration measured that same week shows `expected_taken` — forfeit's
only input — **under-predicts losses at every position, by 1.56x to 4.01x, worst where the pool
is thinnest** (`evidence/blind_pass/TAKE_MASS_BIAS.md`).

So the repair re-anchored every pick on a quantity that is badly calibrated and *differentially*
badly calibrated. A −6% relative loss is what that predicts.

**These are not two findings. They are one:** ordering on forfeit cannot beat ordering on value
while forfeit is this wrong.

## Recommendation

**Do not ship the ordering repair as it stands, and do not cut `v2-freeze`.** The K/DST
placement it produces matches the owner's stated preference, and the measurement that placement
rests on is sound — but placement is not quality, and on the only ruler independent of the
engine's own objective this is a clear regression across every format tested.

Two coherent paths:

1. **Calibrate the take model first (`#21`), then re-measure.** If forfeit becomes accurate, the
   ordering repair may well win rather than lose — its logic is sound where its input is.
2. **Revert the ordering to `final_score` and keep everything else.** 6.1b, the audit fix, the
   pace wiring and every guard stand on their own; the K/DST finding stays recorded and unfixed,
   which is where it was before.

The measurements that survive either way: the curve flatness, the basin analysis, the
calibration ratios, and this file.
