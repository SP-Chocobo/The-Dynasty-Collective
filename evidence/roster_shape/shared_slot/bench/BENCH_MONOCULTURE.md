# The bench is 46 receivers out of 48 — and that is the SHIPPED engine

*#216 / #221. Read off the recorded drafts, `bench_composition.py` / `.txt`.*

## What was actually being blamed on the change

DIALLED_IN.md §4 blocked shipping on "12T_ppr_SF seat 1 goes 2/3/8/2 → 2/2/10/1 — ten of
fifteen roster spots are receivers." That count is a FULL-ROSTER count. Split it at the
probe's own `pure_bench` flag — the states where every starting slot was already filled, so
the pick is depth and nothing else — and the ten decomposes into **four starters and six
bench receivers, and the shipped engine takes the SAME SIX, in the same order, at that seat.**

```
12T_ppr_SF seat 1
  SELF    WR:Courtland Sutton WR:Marvin Harrison WR:Devaughn Vele WR:KC Concepcion WR:De'Zhaun Stribling WR:Makai Lemon
  SHARED  WR:Courtland Sutton WR:Marvin Harrison WR:Devaughn Vele WR:KC Concepcion WR:De'Zhaun Stribling WR:Makai Lemon
```

Six of six identical. The change did not produce that bench and cannot be charged for it.

## The measurement that inverts the conclusion

Counting every pure-bench pick across all nine seats and all three formats:

| format | arm | bench composition | WR share |
|---|---|---|---|
| 12T_ppr | SELF (shipped) | QB 1, **WR 17** | **17/18** |
| 12T_ppr | SHARED | QB 1, WR 13, TE 2, RB 2 | 13/18 |
| 12T_ppr_SF | SELF (shipped) | RB 1, **WR 17** | **17/18** |
| 12T_ppr_SF | SHARED | WR 13, TE 2, RB 3 | 13/18 |
| **OWNER_3RR_SF_noTE** | SELF (shipped) | **WR 12** | **12/12** |
| **OWNER_3RR_SF_noTE** | SHARED | RB 9, WR 2 | **2/11** |

**The shipped engine benches 46 receivers out of 48, and in the owner's own league it benches
twelve receivers out of twelve — not one running back, not one tight end, at any of three
seats.** That is a monoculture, and it is the behaviour that ships today.

(The owner's league totals 12 against 11 because one SHARED seat still had a starting slot to
fill at the round where the other arm had gone pure-bench; the count is picks, not rounds.)

## Why this is the same defect #216 opened with, pointed the other way

The owner's league has two dedicated RB slots and three flexes. A bench of four receivers
carries **zero** running-back insurance: lose either starter and a dedicated RB slot cannot be
filled from the roster at all. #216 opened on "eight tight ends in a one-TE league" — a
position hoarded past any slot that could field it. Twelve bench receivers behind two RB slots
is the identical failure with the positions exchanged, and the shared alternative is what
breaks it: nine of eleven bench picks become running backs.

## What survives as a real limitation, honestly stated

In 12T_ppr_SF the tail of the pool at rounds 10-15 is receivers under BOTH arms, so neither
construction diversifies there. Whether that is the pool or the pricing is the question
`bench_probe.py` was written to answer, and it is a property of the format, not of the change.
The band instrument counts full-roster composition, so it charges every arm for that tail
identically — which is why the "+4 over ceiling" reading at that one seat was never evidence
about the change.

**The blocker recorded in DIALLED_IN.md §4 is withdrawn.** It was a full-roster count standing
in for a bench the shipped engine also takes.
