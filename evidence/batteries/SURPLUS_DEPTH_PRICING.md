# VOR's zero point misprices bench bodies across positions — BLOCKING

Supersedes `SUPERFLEX_QB4.md`, whose conclusion was wrong. Found by the owner pushing back on a
raw-projection comparison I should not have made.

## The withdrawal first

I wrote that the fourth quarterbacks in `12T_ppr_SF__sharp_auto` were "the highest-projecting
player available by sixty to seventy-three points" and concluded the valuation system was working
and a tighter ceiling "would be a mistake."

**That comparison was raw projected points.** It is the exact category error VOR exists to
correct, and it is the one this whole session has been about — I made it one message after writing
a document about it. Three claims are withdrawn:

- "+60 to +73 better" — meaningless.
- "the valuation system working, not junk accumulating" — false where it matters, see below.
- "the flex exemption's looseness is load-bearing" — the exemption is what hides the defect.

## What the board actually says about those QBs

Rebuilt at the frozen pick state, `final_score` (team_acquisition_value), not raw points:

| pick | QB4 raw | QB4 `bpa` | QB4 TAV | best skill alt TAV | margin |
|---|---:|---:|---:|---:|---:|
| seat 7 r13 Geno Smith | 239.1 | +31.6 | −64.09 | Nailor −64.49 | **+0.40** |
| seat 8 r11 Cam Ward | 256.5 | +49.0 | −33.22 | Pollard −38.77 | **+5.55** |
| seat 9 r14 Watson | 215.4 | +7.9 | −74.26 | Spears −76.44 | **+2.18** |

Not 60. **0.40 to 5.55** — seat 7's is a coin flip. The machinery does neutralise most of the
positional-scoring artifact (Geno's `bpa` is +31.6 against Nailor's −59.29, a 91-point gap, and
their TAVs land 0.40 apart). It lands at "effectively tied", which is a very different finding
from the one I reported, and it means a ceiling that broke those ties toward the player with more
fielding pathways would cost approximately nothing.

## The real defect, at TIGHT END

`12T_ppr_K_DEF__sharp_auto`, roster `QB RB RB WR WR TE FLEX FLEX BN×6 K DEF` — **one** dedicated
TE slot. **Five of twelve chairs finished with three or more tight ends. Seat 5 took five.** This
is the sharp control arm, not a noisy one.

Seat 5's fourth TE, round 14:

| | raw proj | `bpa` (VOR) | TAV |
|---|---:|---:|---:|
| AJ Barner (TE4) | 179.5 | **+28.02** | **−20.21** |
| Rashid Shaheed (best WR) | 170.2 | **−46.01** | −38.28 |

**Nine points apart on raw projection; a 74-point swing in VOR.** Entirely because the TE pool is
shallow and the WR pool is deep. The team-specific terms claw some back and still leave a
provably-surplus tight end **18 points ahead** of a receiver with real fielding pathways.

Seat 5's fifth TE came in at +2.55, seat 1's fourth at +0.00.

## Why the flex exemption does not save it, and why a ceiling would not either

TE reaches the TE slot plus two FLEX, so a naive capacity count says three. **That count assumes
both FLEX go to tight ends**, and those slots are contested — a TE in a FLEX displaces the WR or
RB who would otherwise hold it. Three is a loose upper bound on fielding capacity, not a target.

But the count is not the problem. A flex-inclusive ceiling would be `1 + 2 + 1 = 4`, which
**permits seat 5's TE4 — the +18 pick, the damaging one** — and stops only the fifth. The
instrument does not reach the defect.

## The diagnosis

This is the **nine-defense pathology, relocated to tight end and still live.** `bpa` prices a
player against HIS OWN POSITION's replacement level. That is right for a starter and wrong for a
bench body, because fielding pathways differ by position and VOR's per-position zero point does
not know that. A shallow position makes a mediocre player look good; a deep one makes a comparable
player look bad; and the difference is pure positional depth, not worth.

The fieldability backstop closed the case where a position has NO flex reach. It cannot close this
one, and it was never designed to.

## Status

**BLOCKING a freeze.** No core change made and none proposed — this needs a decision about VOR's
zero point for non-starting bodies, not another backstop, and that is an engine-design question
for the owner (`#184`).

Measured, not inferred: every number here comes from rebuilding the board at the frozen pick state
from the battery's own recorded pick sequence.
