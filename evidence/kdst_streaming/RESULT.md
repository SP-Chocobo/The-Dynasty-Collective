# `#30` result: the math is found, the engine drafts well, and the shape is NOT reachable by valuation

Three measurements landed together. They fit, and the conclusion is not the one I set out to prove.

## 1. Does it draft well? YES — and this session's repairs cost nothing

`run_smoke_seats` at `a761d1c`, engine seat against a field of sane styles (`adp`, `need_first`,
`points_need`), seat-controlled, six formats. The `points` ruler is the one the engine does not
optimise toward; `cdme` is its own objective and a win there is a tautology.

| format | `points` HEAD | recorded v1 | seats |
|---|---:|---:|---|
| 12T_ppr | **+2.131%** | +2.131 | 11/12 |
| 12T_ppr_SF | **+0.505%** | +0.505 | 6/12 |
| 10T_ppr | **+1.927%** | +2.018 | 10/10 |
| 10T_ppr_SF | **−0.883%** | −0.901 | 5/10 |
| 12T_standard | **+5.151%** | +5.151 | 12/12 |
| 12T_ppr_TEP | **+2.565%** | +2.632 | 12/12 |

**Wins 5 of 6 formats on the independent ruler**, the sixth a −0.88% draw in 10-team superflex.
Three formats reproduce v1 to three decimals, the other three within 0.07. So the `#22` regression
is fully unwound and `#24`/`#25`/`#26`/`#27` moved quality by nothing.

That is the "meet or beat, or at least comparable" bar, met.

## 2. The streaming math — right, and insufficient

Measured (`STREAMING_BASELINE.json`): what drafting the projected #1 buys over streaming, realized,
as a share of WR's edge — WR 1.00/1.00, RB 0.95/0.54, TE 0.33/0.19, **K 0.24/−0.06, DEF
0.12/−0.09**. In 2024 the projection's top defense returned 153.0 while streaming returned 168.0.

So DEF1's real edge is ~0 against a board price of 22–30. A genuine valuation error.

**But correcting it does not deliver the shape.** Two independent tests agree:

| DEF level | DEF1 `bpa` | first DEF |
|---|---:|---|
| base | +30.47 | round **5.09** |
| +30 (bpa ≈ 0) | +0.47 | round **7.02** |
| +55 (bpa ≈ −24.5) | −24.53 | round **10.01** |

(My own probe, reducing DEF's `bpa` to the measured streaming edge, independently moved first DEF
5.08 → 8.04.)

**Placement saturates.** Reaching round 12 needs a level of about DEF12 **+59**. No streaming
construction produces that: the largest measured is DEF12 +40, and on the board's own 2026 vintage
it is **+16** — less than the δ30 arm, so ≈ round 6.

`KDST_VALUATION` had already said this — *"zeroing K/DEF bpa entirely still leaves them at +4.00"*
— and this is the draft-level consequence of that arithmetic, measured: **round 7, not round 12.**

## 3. WHY it cannot get there, and this is the finding that matters

**The binding constraint is the comparator, not DEF's price.** The best remaining skill row falls
from +32 at round 5 to −30 by round 14, because deep pools are priced against a starter-band level
with **zero bench value**. Every point added to DEF's level buys about a fifth of a round after
round 8. DEF's side is exhausted by round 10.

Bench skill players are priced as liabilities (−8 to −30) while in reality they are insurance.
Measured starter-band absence rates, 2023/2024 weeks 1–17:

| | RB | WR | TE | QB | K | DEF |
|---|---|---|---|---|---|---|
| absence rate | 0.14 / 0.12 | 0.11 / 0.14 | 0.15 / 0.16 | 0.08 / 0.07 | 0.06 / 0.06 | 0.06 / 0.06 |

Roughly 15 skill starter-weeks a season are filled from the bench; K/DEF need one bye fill. The
engine cannot see that, and **neither can its ruler**.

## 4. THE GATE CANNOT VALIDATE A FIX — the most important thing here

The points ruler solves one optimal projected lineup, **no absences, no waivers**. Measured across
the three δ arms, the league points total moved **−0.16% / +0.08%** — noise. The ruler is
*indifferent to when DEF is drafted.*

A streaming basis is a claim about in-season transactions. Nothing in the engine's evaluation can
reward or punish it. So the owner's gate — "no quality drop-off" — is satisfiable trivially, and
equally cannot confirm an improvement. **Any K/DST fix is unvalidatable by construction under the
current ruler.**

This also explains, finally, why every projection-side lever "came back clean": under a
projection-only, absence-free, waiver-free ruler, deferring DEF1 to round 13 really does cost ~35
projected points. `waiting_cost` at 35.90 was never pointing the wrong way — it was reporting that
fact correctly.

## 5. A construction problem with the streaming level, for whoever builds it

Applied uniformly it binds HARDER where it should bind less: on a no-bench wire the correction is
**+70 to +140 for WR/RB** against **+16 to +40 for DEF**, because a maximum over 160 noisy
projections exceeds a maximum over 20 (winner's curse). Applied to every position it would push
K/DST *earlier*. Restricting it to K/DEF is an undeclared position rule; making it position-neutral
requires bench-holding assumptions, which is a prior, not a derivation.

## 6. Where this leaves `#30`

**The valuation error is real and worth fixing on its own merits** — DEF1 is worth ~0 over the real
alternative, not 30. It moves placement 5 → 7, which is progress and is not the target.

**The target needs the comparator side**: bench insurance value, derived from measured absence
rates. That is a different term, it attacks the side with leverage, and it is `#50`/`#74`
territory — cross-position comparability, which the owner holds.

**And before either can be certified, the ruler needs to change.** An absence-aware or
realized-outcome ruler is now possible for the first time (`#18` committed both projections and
realized stats for 2023 and 2024). Without it, a K/DST fix cannot be shown to help.

**Recommendation, not yet executed:** do not ship a valuation-only streaming fix to chase the
shape. It buys two rounds and the gate cannot confirm it. Build the realized-outcome ruler first,
then the streaming basis and the insurance term become measurable rather than arguable.

---

# 7. THE COST IS REAL, AND THE PROJECTED RULER COULD NOT SEE IT

`counterfactual_cost.py`, 2024, `12T_ppr_K_DEF`. One draft on 2024 projections, then for each
early K/DEF pick a counterfactual roster identical except that pick is the best skill player still
on that exact board. Both scored on **2024 realized weekly stats** via `realized_ruler`.

**42 early K/DEF picks. Deferring gained a mean of +81.4 realized points, median +95.8, and helped
34 of 42.**

| position | n | mean | median | helped |
|---|---:|---:|---:|---:|
| K | 20 | **+82.9** | +112.8 | 15 / 20 |
| DEF | 22 | **+80.1** | +93.3 | 19 / 22 |

Against the projected ruler's verdict on the same question: **−0.16% / +0.08% — indifferent.**

That is the whole argument in one comparison. The early K/DST pick costs roughly 80–95 real points,
and the instrument the freeze gate uses cannot detect it, because it solves one lineup over season
totals with no absences and therefore cannot price a bench.

## The eight that went the other way, because they matter

Deferring HURT in 8 of 42, worst at **−105.3**: seat 12's round-7 Denver Broncos. Denver was the
best realized defense of 2024 at 190.0 points. So drafting a defense early does pay **when you
pick the right one** — and the projection ranked Denver third, behind a Philadelphia that returned
153.0. That is `#18`'s ordering-skill finding (DEF 0.48 in 2024) showing up as money.

## What this licenses and what it does not

**Licensed:** the early-K/DST behaviour has a measured cost in real points. It is no longer a
convention or an aesthetic preference — it is ~80 points a pick.

**Licensed:** the gate must change. The owner's condition was "no quality drop-off of the kind
`#16` caused", measured on the projected `points` ruler. That ruler is *indifferent* to K/DST
timing, so it can neither catch a regression of this shape nor confirm a fix. **The realized ruler
must be part of the gate, or the gate is blind to the thing being repaired.**

**NOT licensed:** a size for the fix. Two bounds run in opposite directions and neither can be
removed here — the swapped-in player is not taken away from whoever actually drafted him (an
upper bound on the gain), while the vacated K/DEF slot stays empty because there are no waivers
(a lower bound). n = 42 picks from ONE draft of ONE season, sd 83.2.

**NOT licensed:** that the streaming basis is the fix. It saturates at round 10 (§2), and this
measurement says nothing about which lever should close the gap.
