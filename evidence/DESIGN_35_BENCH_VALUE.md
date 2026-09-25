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

---

# Addendum — Formulation C's blast radius, and why it is not a v2 repair

Fable's contemplation (`DESIGN_35_FABLE_CONTEMPLATION.md`) located the dominant term: the 74-point
VOR swing is **64.81 level gap, 9.22 projection**, because WR's starter demand is exhausted and
`_fill_omitted_from_anchor` substitutes the PRE-DRAFT level — 216.25, against a best remaining WR
of 173.00. Independently verified on the seat-5 board at pick 164:

```
WR   level 216.25   basis predraft_anchor       +43.25 ABOVE the best WR left   disp  0.00
TE   level 151.44   basis live_starter_demand   -28.02 below the best TE left   disp -38.83
RB   level 165.82   basis live_starter_demand   -11.16 below the best RB left   disp -50.43
DEF  level 107.95   basis predraft_anchor        +8.72 above the best DEF left  disp -19.12
```

That corrects this document's original framing: the driver is **anchor staleness**, not position
locality. The phantom is a genuine falsehood — the board asserts a free WR worth 216.25 is coming
when the pool's best is 173.00 — and removing it is a real repair.

**It is nonetheless not a v2 repair, for three reasons established by measurement and by reading
the code, not by preference.**

**1. It is not one seam.** `shared_slot_alternatives(levels, roster_positions)` never receives the
pool, so "the best remaining player eligible for that slot" is out of scope where Fable placed the
cap. It would have to be threaded through `displacement_adjustments` as well.

**2. It inverts a REGISTERED invariant, and the invariant is DERIVED rather than asserted.**
Measured on the shipped board: 888 single-position rows, **zero** with positive `displacement_adj`.
`lineup_optimizer.displacement_level`'s own "THE SIGN" section derives that from the cap's premise:

> That function prices a slot at `max(level)` over the positions the slot ADMITS. So every slot a
> SINGLE-position probe can reach admits that position, every such alternative is therefore at or
> above his own level.

Capping at the best remaining player destroys exactly that premise. A slot could then be priced
BELOW the probe's own level, making `displacement_adj` positive — a roster-context **lift**, which
the current design forbids with a stated argument ("lifting him again for my own weak starter would
be paying twice for one fact"). For Shaheed the arithmetic is `216.25 − 197.80 = +18.45`.

**3. Its blast radius reaches two shipped constants.** The same section records that
`pick_synthesis.TEAM_SPECIFIC_CAPS` "hand-exempts this term from the bound two shipped constants
derive from, **citing exactly that premise**."

And this repository has already made this mistake once, in this precise place. From the same
docstring:

> It is false as stated, and it became false when `slot_alternatives` arrived. Not through a bug in
> that change: the change EXPANDED THE POPULATION this function ranges over, and **an invariant
> proven over the old one was never re-checked against the new one.**

Shipping C without re-deriving `TEAM_SPECIFIC_CAPS` and the two constants that cite the premise
would be that same failure a second time, in the same function, at a freeze.

## The ruling this implies

- **v2 freezes on what is measured and green.** The `#30` streaming level and the fieldability
  ceiling were both confirmed on realized outcomes across two seasons, on a period-correct pool and
  board, and the suite is green. Neither depends on C.
- **`#35` stays open and is now well specified**, which is the useful outcome of the contemplation.
  The work order is: bound the phantom (C) → re-derive `TEAM_SPECIFIC_CAPS` and the two constants
  against the new population → only then evaluate the season objective (B), which Fable establishes
  says nothing until the phantom is bounded.
- **Nothing about C is discarded.** It is admissible under `#56` and it removes a real falsehood.
  It is a next-cycle change with a dependency chain, not a patch.
