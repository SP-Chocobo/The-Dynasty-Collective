# #154's residue: the backstop cannot see a FLEX hole, by design

## The finding

The #150 gate run (33 formats, 5,340 picks, `BATTERY_2026-09-12_scoring_aware_full_99f9f76`)
returned two structural findings, both a chair finishing unable to field a legal lineup:

```
8T_standard    roster 5   filled 7 of 8   empty FLEX   roster_size 14
14T_standard   roster 4   filled 7 of 8   empty FLEX   roster_size 14
```

Reproduced, seat 5 of `8T_standard` in pick order:

```
1. WR  2. TE  3. RB  4. WR  5. RB  6. RB
7. QB  8. QB  9. QB 10. QB 11. QB 12. QB 13. QB 14. QB
```

**Eight quarterbacks in a one-QB league.**

## Root cause: `feasibility_first` is scoped to DEDICATED slots, and the hole is FLEX

`feasibility_first` is the #154 backstop, and it works. Its own docstring records what it was
built for — the previous battery's *"13 rosters finished unfillable, every one a positional
monoculture — nine RBs and no TE, ten WRs and one RB, seven TEs and no QB"* — and those were all
**named-slot** holes. That population is now zero.

What remains is precisely its documented exclusion:

> *"Deliberately DEDICATED slots only, never flex. A flex slot is fillable from several
> positions, so it is not at risk in the way a named slot is, and counting it would let this bind
> on a roster that was never actually in danger — turning a backstop into a preference, which is
> exactly what this must not become."*

`dedicated_slot_counts` counts only literal position labels (`QB`/`RB`/`WR`/`TE`), never `FLEX`.
So for the failing seat:

| dedicated slot | need | owned | |
|---|---:|---:|---|
| QB | 1 | 8 | filled |
| RB | 2 | 3 | filled |
| WR | 2 | 2 | filled |
| TE | 1 | 1 | filled |

`unfilled == 0` → `feasibility_first` returns its no-op default on every pick of the draft. The
backstop never binds, because by its own definition this roster was never in danger. Then the two
FLEX slots are solved: the spare RB fills one, and **nothing flex-eligible is left** for the
second.

## The exclusion's reasoning is sound and has an uncovered boundary

*"A flex slot is fillable from several positions, so it is not at risk"* is true — right up until
the roster owns no spare of **any** of those positions. That state is reachable, it was reached
twice in 5,340 picks, and the only way to reach it is to spend the back half of a draft on a
position with no remaining slot.

So this is not a bug in `feasibility_first`. It is the exact case its scope was drawn to exclude,
and the scope was drawn on a premise that holds in every case but this one.

## It is broader than the audit reports — the two findings are a LOWER BOUND

Same draft, other seats:

```
seat 1: QB 4, RB 4, TE 3, WR 3
seat 4: QB 4, RB 4, TE 1, WR 5
seat 7: QB 1, RB 2, TE 8, WR 3      <-- eight TEs, NOT flagged
```

Seat 7 hoards as hard as seat 5 and escapes the audit only because TE is FLEX-eligible, so its
surplus tight ends keep filling the flex. **The audit fires when the hoarded position happens to
be flex-INELIGIBLE.** Counting findings therefore counts the intersection of two things —
hoarding, and hoarding the one position that cannot backfill a flex — not the behaviour itself.

## MEASURED: the hoarding is universal, the flagging is rare

All four 1QB standard arms, longest run of consecutive same-position picks per seat:

```
8T_standard    [8, 7, 3, 3, 3, 2, 2, 2]                    flagged: seat 5
10T_standard   [7, 6, 5, 5, 4, 4, 3, 3, 3, 2]              flagged: none
12T_standard   [7, 7, 5, 5, 4, 4, 4, 4, 3, 3, 3, 2]        flagged: none
14T_standard   [8, 7, 6, 6, 6, 6, 5, 5, 4, 3, 3, 3, 1, 1]  flagged: seat 4
```

| | |
|---|---:|
| seats measured | 44 |
| seats ending with a run of **5 or more** consecutive same-position picks | **18 (41%)** |
| seats the audit flagged | **2** |

**10T and 12T hoard exactly as hard as the arms that were flagged and are flagged zero times.**
14T has eight seats with a run of five or more and flags one. The audit fires only where hoarding
coincides with the hoarded position being flex-INELIGIBLE, so it reports the intersection of two
independent things and is read as a count of one of them.

Every long run begins immediately after the seat's dedicated starters fill — pick 7 or 8 in a
14-round draft. The behaviour is not gradual drift; a seat enters an absorbing state and does not
leave it.

**This is why the two structural findings must never be quoted as "two rosters were affected".**
Two rosters were *unable to field a lineup*. Eighteen drafted a monoculture.

## What is NOT established

- ~~Why 10T_standard and 12T_standard are clean.~~ **MEASURED — they are not clean, they are
  unflagged.** See below.
- **The proposed repair.** The narrow fix that preserves the #56 admissibility argument is to ask
  the same feasibility question of a flex slot rather than treating it as never-at-risk: a flex
  slot is at risk exactly when the roster's flex-eligible surplus is zero. That stays arithmetic,
  invents no constant, and binds only when the slot is genuinely unfillable. **Not implemented.**
  It changes the selection path, and the docstring's warning — that counting flex naively turns a
  backstop into a preference — is the thing any implementation has to keep being true.
