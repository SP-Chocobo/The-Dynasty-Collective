# `#35` — VOR is position-local; bench value is roster-global

**A design problem, not a bug report.** Opened because a freeze on the current ruler risks
optimising around the wrong thing.

## The defect, in one example

`12T_ppr_K_DEF__sharp_auto`, seat 5, round 14. One dedicated TE slot on the roster.

| | raw proj | `bpa` (VOR) | TAV |
|---|---:|---:|---:|
| AJ Barner — the **fourth** tight end | 179.5 | **+28.02** | **−20.21** |
| Rashid Shaheed — best available WR | 170.2 | **−46.01** | −38.28 |

**9.3 points apart on projection. A 74-point swing in VOR. The engine takes the fourth TE by 18.**

Position scarcity manufactured value for a player with almost no additional fielding capacity.
Five of twelve chairs on the sharp control arm finished with 3+ tight ends; one took five.

## Why this is not a ceiling problem

A ceiling would conceal the symptom — *"don't draft TE5"* — while leaving the real question
unanswered: **why does TE4 look this valuable in the first place?**

And a ceiling cannot reach it anyway. The flex-inclusive form would be `1 TE + 2 FLEX + 1 bye = 4`,
which permits seat 5's TE4 — the +18 pick, the damaging one — and stops only the fifth.

Granting that FLEX can field a tight end does not rescue the count either, and this is the
sharpest form of the point:

> **Eligibility is not capacity.** Two FLEX slots are not two additional TE slots. They are
> contested by the entire RB/WR/TE pool. To get TE4 into a lineup you need TE1 at the TE slot,
> then TE2 and/or TE3 to beat the best RB/WR alternatives for a FLEX, and then enough of those
> alternatives displaced that the fourth creates incremental value.

So a position's roster ceiling **cannot be derived from the number of lineup slots it is eligible
for.** It has to account for competition for those slots.

## The conceptual question, which comes before any fix

**What is the replacement unit for a BENCH player's value?**

For a starter, positional replacement is obviously right:

> How much better is this TE than the TE I could otherwise start?

For a bench body that is the wrong comparison. The relevant alternative is:

> How much additional lineup value does owning this player give me, compared with spending this
> roster slot on the best available alternative at ANY position?

That is a **roster-slot opportunity-cost** problem, not a positional-replacement problem. And it
may admit a principled answer that introduces no new constant — which is the reason to ask it
before reaching for a threshold.

## The unifying claim, and what it would explain

> **VOR is position-local. Bench value is roster-global.**

If that is the root, these are all one defect rather than four:

- **surplus defenses** — the nine-defense roster (`evidence/kdst_streaming/ROOT_CAUSE.md`);
- **TE hoarding** — this document;
- **QB3/QB4 in superflex** — measured at +0.40 to +5.55 TAV over the best alternative, which is
  "effectively tied" and therefore unresolved rather than fine;
- **possible RB/WR depth distortions** — unmeasured, predicted by the same mechanism.

## What this implies about what was shipped today

`draft_room.unfieldable_last` — the fieldability backstop — is then a **symptom-level fix that
happens to catch the cases where a position has no flex reach.** It is measured and it works
(+230 to +347 a seat, 12 of 12 seats, both seasons), so it stays. But the design work on `#35`
should check whether a correct roster-global bench valuation makes it redundant, and it should
not assume the backstop's shape is evidence for anything about the right answer.

## Explicit non-goals

- **Do not hunt the threshold that makes Barner disappear.** That is calibration (`#56`) and it
  is how the first K/DST repair was brute-forced into shape and unwound.
- **Do not jump to "change VOR's replacement level for bench players."** That might be the
  answer. It is not yet established as the right frame, and the conceptual question above is what
  decides.
- **Do not add a third backstop.**

## Status

Production code is FROZEN as it stands. **The brain is not frozen as complete** — that
distinction is the point of opening this. There is a clean blocking finding with a reproducible
pathological example, which is exactly the state you want before a core change, and exactly the
state in which further optimisation against the current ruler measures the wrong thing.

The VDS battery was stopped at 13 of 36 arms for the same reason.
