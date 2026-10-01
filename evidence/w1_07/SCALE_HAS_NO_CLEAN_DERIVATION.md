# W1-07: the substitute has no clean derivation, and here is the measurement

> **CORRECTED 2026-09-21. THIS FILE ASKED A QUESTION THAT IS DOWNSTREAM OF THE REAL BLOCKER,
> and did not cite the blocker that was already recorded in the tree.**
>
> What this file published: *"the scale must be derived from the quantity's own bounds ... They
> do not exist in a usable form"*, with three denominators measured and rejected. That analysis
> is correct as far as it goes. What it MISSED is that `test_rulings_are_not_silently_dropped.py`
> already carried the prior objection, along with a STAGED PATCH at
> `evidence/blind_pass/w1_07_substitute.patch`:
>
> > implementing it flips **62% of labels** against a ruling made on 3.1%, because
> > `intervening_picks` is a property of the **TURN** and the quantity it replaces was a property
> > of the **PLAYER**. Forces re-deriving five label thresholds.
>
> That difference is now MEASURED rather than asserted (`w107_per_turn.py`). At five real turns:
>
> ```
>  turn seat  cands   distinct intervening_picks   distinct survival
>     0    1     48                        [22]                   6
>     5    6     48                        [12]                   7
>    13   11     47                        [20]                   9
>    25    2     47                        [20]                  11
>    37   11     46                        [20]                  13
> ```
>
> **`intervening_picks` takes exactly ONE value across every candidate in a snapshot.**
> `survival_probability` takes 6 to 13. So the substitute cannot differentiate candidates under
> ANY denominator: it shifts every candidate's necessity by the same amount, never reorders
> them, and the 62% label flip is band-crossing rather than re-ranking.
>
> **So "which denominator?" is the wrong first question, and §§2-5 below are downstream of a
> settled one.** They are kept unedited because they remain the answer IF the term is ever made
> per-candidate — and because a bound analysis that turns out to be moot is still the record of
> how it was established. The live question is the one the register already states: whether
> re-deriving five label thresholds is worth it for a term that cannot re-rank anything.
>
> Nothing in §§2-5 is withdrawn as false. What is withdrawn is this file's framing of the
> decision.

---


**CHARACTERIZED, NOT BUILT.** `CDME_CONTRACTS.md` rules `NECESSITY_SURVIVAL_WEIGHT` should be
**replaced with `intervening_picks`**, and records the blocker precisely:

> `intervening_picks` is a COUNT, not a probability: it has no natural 0-20 mapping, and
> choosing one by looking at which mapping reproduces today's labels is precisely `#56`'s
> prohibition. The scale must be derived from the quantity's own bounds.

This went looking for those bounds. **They do not exist in a usable form.** Every candidate is
either not a bound at all, or bounded but uninformative. That is the finding, and the choice
among the remaining options is the owner's (`#184`), not a repair commit's.

Probes in this directory, all structural -- they read the pick order only, no engine, no network.

## The incumbent, and what the substitute has to match

```python
survival_component = (1 - survival) * NECESSITY_SURVIVAL_WEIGHT   # 20.0 of a 100-point scale
```

`(1 - survival)` is bounded `[0,1]` **because it is a probability**. That is the entire source
of its scale. A count has no such property, so the substitute needs a denominator, and the
denominator is the whole question.

## Candidate A -- `intervening / (2 x (teams - 1))`. NOT A BOUND.

The obvious one: in a snake, a seat waits at most `2(T-1)` picks. Measured, it holds exactly --
and only for a snake:

```
12T x16 snake        n= 180  min=  0  max= 22   2*(T-1)= 22
12T x16 traded(135)  n= 180  min=  0  max= 46   2*(T-1)= 22
10T x16 snake        n= 150  min=  0  max= 18   2*(T-1)= 18
10T x16 traded(135)  n= 150  min=  0  max= 37   2*(T-1)= 18
```

**On a traded order the gap reaches 46, more than double the "bound".** The ratio exceeds 1 and
the 20-point term pays out 41. This is not a pedantic case: the `#52` evidence that verified
`intervening_picks` against the engine did so on a real draft with **135 traded seats**, which
is exactly the shape simulated above.

A is a LEAGUE-SHAPE ASSUMPTION wearing a bound's clothes -- `#56`'s failure mode, reached by
geometry instead of by tuning. **Rejected.**

## Candidate B -- `intervening / this seat's own longest wait`. BOUNDED, BUT IT MEASURES THE SEAT.

Bounded `[0,1]` by construction for any order, traded included, because the denominator is read
off the order the engine was already handed. It also keeps a flat profile across the draft
(mean 0.675 in every round). But:

```
 seat            gaps (first 6)  seat max   B mean    B sd   B range
    1     [22, 0, 22, 0, 22, 0]        22    0.533   0.499     1.000
    4     [16, 6, 16, 6, 16, 6]        16    0.708   0.312     0.625
    6  [12, 10, 12, 10, 12, 10]        12    0.922   0.083     0.167
    7  [10, 12, 10, 12, 10, 12]        12    0.911   0.083     0.167
   12     [0, 22, 0, 22, 0, 22]        22    0.467   0.499     1.000
```

**The term's informativeness is a function of where you sit.** At the turn (seats 1 and 12) B
alternates 1.000 / 0.000 and swings the full 20 points. In the middle (seats 6 and 7) it sits at
~0.92 with a standard deviation of 0.083 and a total range of 0.167 -- a 20-point term that
moves **3.3 points**, near-constant, for the whole draft.

A term that barely moves cannot differentiate, and this repository has already named that shape:
the necessity tag spends five bands to put 95.4% of its mass in two. B would reproduce it inside
the score. Same result at 10 teams (seats 5 and 6, sd 0.100).

B is not a scale. It is a seat-position volume knob. **Rejected as specified.**

## Candidate C -- `intervening / picks remaining in the draft`. BOUNDED, BUT MUTED WHERE IT MATTERS.

Also bounded `[0,1]` by construction for any order, and with no seat asymmetry. Its defect is
the profile:

```
 round   n  intervening   C mean   C max
     1  12         11.0    0.059   0.115
     2  12         11.0    0.063   0.123
     4  12         11.0    0.073   0.142
     8  12         11.0    0.106   0.206
    12  12         11.0    0.198   0.373
    15  12         11.0    0.571   0.957
```

The identical 11-pick wait scores **0.059 in round 1 and 0.571 in round 15**. So a 20-point term
contributes ~1.2 points through the early rounds -- where the draft is actually decided -- and
reaches full voice only once the pool is picked over. It also rises late, which runs against
`LATE_ROUND_NECESSITY_CAP`, a mechanism that exists to hold necessity DOWN in exactly those
rounds. Shipping both means one term climbing while another caps it.

There is a real argument for C's direction (the same wait IS more dangerous when the pool is
thin), but its magnitude is set by draft length rather than by urgency, and it fights an
existing mechanism. **Not rejected outright; it is a design choice with a stated cost, and that
makes it the owner's.**

## Candidate D -- remove the term, substitute nothing

`CDME_CONTRACTS` already measured this arm: **12 of 384 labels flip (3.1%), max necessity move
8.50, including 2x `MUST TAKE -> STRONG ACTION`.** It is the option consistent with this
repository's own absence posture (`#187`): if no scale can be derived, a fabricated one is worse
than none, and the 20 points either redistribute across the surviving terms or the scale shrinks
to 80. Which of those two, and what it does to `necessity_label`'s bands, is unmeasured here.

## What this rules OUT, so nobody re-runs it

- **Not a missing formula.** All three normalisations were tried; the problem is the quantity,
  not the arithmetic.
- **Not fixable by picking a different snake constant.** A fails on traded orders, which are
  real in the very evidence that validated `intervening_picks`.
- **Not resolvable by measuring more drafts.** A, B and C are structural properties of the pick
  order; more seats reproduce them rather than discriminating between them.
- **Not blocked on `#21`.** The take model's calibration is a separate defect. `W1-07` removes
  the term that reads it; it does not need it fixed first, and fixing it would not supply a
  bound.

## Recommendation to the owner

The ruling "replace with `intervening_picks`" is executable only after a second ruling on which
denominator, because the quantity does not carry one. My reading, stated as a recommendation
and not as a decision:

**D, then C if the term is missed.** D is measured, honest about the absence, and matches the
posture the rest of the engine already takes. C is defensible but buys a shape argument and a
collision with `LATE_ROUND_NECESSITY_CAP` in exchange for keeping a term whose contribution in
the rounds that matter would be ~1.2 of 100.

**What must not happen:** choosing among A/B/C/D by which one best reproduces today's labels.
The 12-of-384 figure is the *before* measurement, not the target.
