# RESIDUAL3 RESULT — **FORK B**: the documented open-slot mechanism never fires here

Forks fixed and committed before the run. 144 observations, picks 9–20, all twelve seats.
**No engine source changed.**

## The verdict

**`adjustment == 0.0` occurs ZERO times in 144 observations.** Every seat, every pick from its
9th to its 20th, has its tight-end-reachable slots held. Per-seat rate `0.00` for all twelve.

`displacement_level`'s docstring names a real, unfixed residual bias — *"the ~30-point half of
the bias that survives the displacement term, because the term reports exactly 0.0 whenever the
slot is merely open"* — and that bias is **not operating in this window**. It joins the timing
proxy and the deduction magnitude as an explanation that does not apply here. It is not
withdrawn as a defect; it is simply not this one.

## What the sweep found instead, and it is the sharper fact

The window is the right one: hoarders spent it taking tight ends, starvers did not.

| seat | group | final TE | **TEs taken in picks 9–20** | mean TE adjustment |
|---|---|---|---|---|
| 12 | HOARD | 15 | **8 of 12** | **−94.29** |
| 9 | HOARD | 14 | **8 of 12** | **−109.19** |
| 2 | HOARD | 9 | 6 of 12 | −104.82 |
| 5 | HOARD | 9 | 5 of 12 | −101.36 |
| 7 | mid | 7 | 4 of 12 | −110.49 |
| 10, 11 | STARVE | 2, 2 | 1 of 12 | −111.59 |
| 1, 3, 8 | STARVE | 1, 1, 1 | **0 of 12** | −108.80, −109.15, −109.69 |

**Every seat is carrying a tight-end deduction of roughly −100, and four of them take tight ends
anyway — one of them eight times out of twelve.**

That is the finding. The deduction is not close to zero, is not absent, and is not meaningfully
different between the seats that hoard and the seats that abstain. **Seat 9 takes fourteen tight
ends while carrying −109.19 — a larger deduction than every starver except two.** The same
counterexample that broke RESIDUAL2 breaks this: three hoarders sit above the starver band and
the fourth sits inside it.

## What this rules out, and what it points at

**Ruled out (three now):**
1. the timing proxy — `r = +0.101` (RESIDUAL1)
2. the deduction's magnitude as a pre-divergence predictor — identical at the 5th pick (RESIDUAL2)
3. the documented open-slot mechanism — never fires in the divergence window (here)

**Points at:** whatever selects these tight ends is **outweighing a ~100-point deduction**, not
avoiding one. The deduction is doing its job and losing. So the next question is not "why is the
brake off" — it is measurably on — but **"what is large enough to beat it, and why is it larger
for four seats than for eight?"**

`team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure +
displacement_adj`. The deduction is one of five terms, and it is the only one this investigation
has examined. The remaining four have not been looked at for this at all.

## Honest limits

- The window picks 9–20 **is** the divergence window, so per-seat deduction means here are
  partly downstream of the outcome. That is why the pre-registration made the 0.0 RATE the
  quantity, and the rate is a clean 0/144 regardless of direction.
- Groups were defined by the outcome; n = 4 and 5 seats in one draft.
- Nothing here says the deduction is wrong. It says it is not decisive.
