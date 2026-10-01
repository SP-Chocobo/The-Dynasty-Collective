# RESIDUAL2 RESULT — **FORK B**: the deduction does NOT predict which seats hoard

Forks A/B/C were fixed in `RESIDUAL2_PREREGISTRATION.md` and committed before the probe existed.
Every number is `displacement_adjustments`' own returned dict, captured at the call.
**No engine source changed.**

## The verdict

> **FORK B — DEAD.** "No systematic separation between the groups at the early checkpoints, or
> the separation appears only after the seats have already diverged. The hypothesis is a
> consequence, not a cause, and is withdrawn like the timing proxy."

**The displacement-feedback hypothesis is withdrawn.** Three reasons, in order of weight:

**1. At the earliest checkpoint the groups are IDENTICAL.** At each seat's 5th own pick, the
mean non-zero TE adjustment is **−68.58 for hoarders and −68.58 for starvers**. Not close —
the same number. This is where the hypothesis most needed a separation and there is none.

**2. At the 7th, the hoarders are BEHIND on tight ends.** Separation is 1.9 points, and the
tight ends already held run HOARD `[1, 0, 1, 0]` against STARVE `[1, 1, 1, 1, 1]`. Every
starver holds one; half the hoarders hold none. That is the opposite of a spiral already
underway.

**3. At the 9th, the separation is real but does not discriminate.** Group means part by ~5
points (−61.27 vs −66.22), and the per-seat values overlap heavily:

| seat | group | final TE | TE adj at 9th pick | displaced |
|---|---|---|---|---|
| 12 | HOARD | **15** | **−51.73** | 200.90 |
| 5 | HOARD | 9 | −60.03 | 209.20 |
| **8** | **STARVE** | **1** | **−62.48** | 211.65 |
| **3** | **STARVE** | **1** | **−62.86** | 212.03 |
| 2 | HOARD | 9 | −64.76 | 213.93 |
| **9** | **HOARD** | **14** | **−68.58** | 217.75 |
| 1, 10, 11 | STARVE | 1, 2, 2 | −68.58 | 217.75 |

**The second-largest hoarder (seat 9, fourteen tight ends) sits at −68.58 — the most negative
value on the board, identical to three starvers.** Two starvers sit above two hoarders. A
predictor that puts the biggest and the smallest at the same value is not a predictor.

## And the fact that sharpens the question

**At each seat's 9th own pick, all twelve seats hold exactly ONE tight end.**

They finish at 1, 9, 1, 4, 9, 3, 7, 1, 14, 2, 2, 15.

So the divergence happens entirely **after** the ninth pick, from a state where every chair is
positionally identical at tight end. Whatever separates them is not visible in the tight-end
deduction at pick 9, because at pick 9 they are not yet separated by anything this probe
measured.

That is a sharper question than the one this probe was built for, and it is not answered here:
**twelve identical rosters at TE, twelve identical code paths, and a 1-to-15 spread by pick 26.**

## An OBSERVATION, not a finding — `displaced` is 217.75

Across these checkpoints `displaced` for a tight end is repeatedly **217.75**, which is exactly
the **WR pre-draft anchor level** measured in `phase2_crossing.json`, to the hundredth.

A tight end's `displaced` should be what he evicts from this roster's optimal lineup. That a
receiver-position replacement LEVEL appears as the evicted quantity is either
(a) correct — a shared FLEX slot's phantom is worth the best eligible position's level, which
`shared_slot_alternatives` computes as `max(candidates)` — or (b) a leak.

**I am not calling it either.** The last four things in this investigation that looked like
defects were correct, and two of my own probes have already been withdrawn for inferring a
mechanism instead of reading one. It needs its own pre-registered read of
`displacement_level`'s `slot_alternatives` argument, and it is recorded here so it is not lost,
not pursued.

## What is now dead, and what is left

**Dead:** the timing proxy (r = +0.101, RESIDUAL1) and now the deduction itself (Fork B). The
displacement term does not explain the hoard/starve split.

**Left:** the split itself, unexplained, with the new constraint that it begins after every seat
has one tight end and none before. The three remaining roster-aware terms — `need_bonus`,
`eligibility_bonus`, `depth_exposure` — have not been examined for it, and neither has the
possibility that nothing in the per-seat terms is responsible at all.

**Not carried forward:** any suggestion that the deduction is *wrong*. The cancellation result
already settled that the level's basis does not reach the price where the term is non-zero. This
probe asked only whether it *discriminates*, and it does not.
