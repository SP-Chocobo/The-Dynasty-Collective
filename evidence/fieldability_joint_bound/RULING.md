# MANDATE 3.2 — the joint fieldability bound, measured before and after

**Status: REPAIRED (derivable half) and verified on a re-drafted arm. The flex-reachable half is
an owner decision, D7.**

## What the battery found

Running the full battery over 2.6 at `360f6ba`: the 24 offence-only arms returned **zero**
structural findings, and `HEAVY_IDP` returned **ten**, all `unfieldable_depth`. Every one was over
the per-position ceiling by exactly its number of MULTI-eligible holdings:

| roster | held | counted by the engine | skipped |
|---|---|---|---|
| 2 | LB 6 | 3 | 3 |
| 8 | LB 5, DB 4 | 3, 3 | 2, 1 |
| 11 | LB 5 | 3 | 2 |

`unfieldable_last` stopped each roster at exactly the ceiling of 3 and was then blind. The skipped
players are edge rushers eligible at `{DL, LB}` and one safety at `{DB, LB}`. `HEAVY_IDP` fields
`DL/DL`, `LB/LB`, `DB/DB` with **no** `IDP_FLEX`, so not one of them reaches a shared slot — the
`len(eligible) == 1` test was standing in for "reaches a shared slot" and is not that question.

## The repair

`draft_room.fieldable_ceiling_groups` bounds the GROUP a roster's own players span:

> held(group) ≤ |slots admitting any member of the group| + 1

Derived from the same two facts as the per-position form (`#56`), and for a one-position group it
IS `slots(P) + 1`, so the count widens and the bar does not move. `draft_battery`'s audit, which
had been re-deriving the ceiling itself and counting by PRIMARY POSITION, now asks the same
function (`#126`) — ten of its findings were the disagreement, not the defect.

## After: the same arm, re-drafted on the repair

Re-run of `HEAVY_IDP` at `c452696`, 216 picks, 1587s:

**10 findings → 1.**

```json
{
  "audit": "unfieldable_depth",
  "roster_id": "12",
  "positions": [
    "DB",
    "DL",
    "LB"
  ],
  "held": 8,
  "startable_per_week": 6,
  "ceiling": 7,
  "unfieldable": 1
}
```

Roster 12 holds 8 players across the merged `{{DB, DL, LB}}` group against 6 slots and one bye, so
it is over by exactly one. That is a real single-player overflow, reported in the shape of the
bound the engine now enforces, and it is what remains after the counting defect is gone.

## What is NOT repaired, and why it is a decision

3.2 also asks for this bound on flex-reachable groups, where one `IDP_FLEX` admitting DL/LB/DB
gives `1 slot + 1 = 2` and nothing catches six. The same arithmetic on the offence group flags
**12 of 12** seats in `12T_ppr` (holding 12–13 players eligible within RB/WR/TE against `7 + 1`)
and 9 of 12 in `HEAVY_IDP`. Those are ordinary rosters. `unfieldable_last`'s own docstring sets the
test that fails: a backstop must not bind on a roster that was never in danger.

The `+ 1` is justified by `#30`'s measured finding that the churn a spare buys is free on the
waiver wire — true of a flat dedicated streamable position, false of RB/WR where bench depth is the
point. So the joint bound is sound about ONE WEEK and needs a depth allowance to be a backstop, and
an allowance is a number somebody chooses. See **D7** in `OWNER_DECISIONS_PENDING.md`.

**So 3.2's item text treats the joint bound as derivable throughout, and the measurement says it is
derivable for dedicated groups and not for flex-reachable ones.**
