# ⛔ It IS the rulebook. `#248`'s other half is withdrawn too (28th) — and the roster never mattered.

Three arms, one process, one code version, rounds pinned at 15. Pre-registered at `18be63b`
together with the harness defect that made this run necessary.

```
D2  fixture roster, FLEX 3, fixture PPR        3/12  -0.84%  margin -22.53   CONTROL
B3  fixture roster, FLEX 2, TRUE F&F scoring   9/12  +0.84%  margin +22.08
G   fixture roster, FLEX 3, TRUE F&F scoring  10/12  +1.04%  margin +29.43
```

## The result, in one line

**The 15-slot fixture roster under Fourth and Forever's rulebook reproduces the 29-slot F&F
roster BIT-FOR-BIT.**

| new arm | matched against | differing values, 12 seats × every metric |
|---|---|---:|
| `D2` fixture, FLEX 3, PPR | flex cut `D` | **0** |
| `B3` fixture, FLEX 2, F&F | flex cut `E` — *the F&F roster* | **0** |
| `G` fixture, FLEX 3, F&F | flex cut `C2` — *the F&F roster* | **0** |

A 15-slot roster (6 BN, no TAXI, no IR) and a 29-slot roster (11 BN, 5 TAXI, 3 IR) produce the
same draft, seat for seat, to the last decimal — **once the rulebook matches.**

## Why `#248` got the opposite answer

Its only rulebook arm never moved the rulebook. Arm B was built through
`build_mock_league(scoring="ppr", …, base_scoring=<F&F's keys>)`, which **overwrites `rec` from
its own `scoring` argument**, so it ran at `rec = 1.0` and resolved to `hint = ppr`. Arm C
resolved to `half_ppr`. Since `rec` reaches offensive valuation by FILE SELECTION — it picks the
rankings export — arms B and C were reading different exports, and the one cut that was supposed
to isolate the rulebook changed everything about it except the part that matters.

Supply the rulebook directly and the answer inverts. `#248`'s headline is wrong in both halves:

> ~~*"#248: it is not the rulebook. It is ONE FLEX SLOT."*~~

Neither. **It is the rulebook, and the roster is inert.**

## What each factor is actually worth

| factor | effect on the verdict | evidence |
|---|---|---|
| **rulebook** (PPR ↔ half-PPR + TE premium + first downs, and its export) | **3/12 → 10/12, −0.84% → +1.04%** | `D2` → `G`, one factor moved |
| flex / startable count | 9/12 → 10/12, +0.84% → +1.04% | `B3` → `G`, one factor moved |
| roster shape beyond startable slots (bench, taxi, IR, total size) | **exactly nothing** | `B3`≡`E`, `G`≡`C2`, 0 differing values |
| draft length | nothing | `#245` |
| roster capacity | nothing — fenced off the pick path by design | the capacity cut |

The flex effect is real but small, and it is the SAME small effect measured in the flex cut —
which is why that cut could not find the reversal: it was varying the minor factor.

## This is coherent, and it explains the whole thread

Three facts fit together exactly:

1. **Startable slot structure reaches the pick.** Flex count changes the lineup solve, so it
   moves the verdict a little.
2. **Nothing else about the roster reaches the pick.** The capacity cut proved the fence:
   `draftable_slots_per_team` terminates in observables, never in `final_score`.
3. **The rulebook reaches the pick enormously**, because it selects the rankings export.

`B3` and `G` have the same startable structure as `E` and `C2` (9 and 10 slots respectively).
Everything else differs, and nothing else mattered. Identical drafts are the *prediction* of
(1)+(2), not a coincidence.

## What this does to the freeze record

`FREEZE_CHECKLIST.md` already carried the right suspicion and said, correctly, that it was
unproven:

> *"The freeze's headline deficit is 5–11%. The rulebook difference is ~16%, and it runs the
> other way. That is larger than the effect being ruled on, so the size and possibly the SIGN of
> the points deficit is not established for F&F. **Neither is it refuted. It is unmeasured.**"*

**It is now measured.** Same roster, same pool, same rounds, same code, same harness — only the
rulebook swapped:

```
fixture PPR rulebook      3 of 12   -0.84%     engine behind
F&F rulebook (the owner's) 10 of 12   +1.04%   engine ahead
```

The sign of the verdict is a property of **the scoring environment**, and every fixture-measured
claim in the freeze record — `#205`'s headline deficit, all 33 battery arms — was taken in a
full-PPR environment the owner does not play in.

## What this does NOT establish

- **That the engine is good.** Every arm still sits within ~1% of its control. `+1.04%` is small;
  it is simply no longer negative in the league being played.
- **Which rulebook is "right" to certify against.** That is the open decision this hands back:
  certify against the generic PPR environment and record F&F as out of scope, or re-measure the
  freeze evidence on the owner's rulebook. `FREEZE_CHECKLIST.md` has carried that unanswered
  checkbox for some time; it now has a measured number attached instead of an argument.
- **Which part of the rulebook does it.** `rec` 1.0→0.5, the TE premium, first downs, the
  completion bonus and the export selection all moved together. `#248`'s arm B shows that first
  downs + completion bonus + TE premium *at PPR reception value on the PPR export* do nothing —
  so the live suspects are `rec` and the export it selects. Separating those two is the next cut,
  and unlike every cut before it, it is a question about one input rather than about the league.
