# W4-01: `years_exp == 0` is not the rookie class — and promoting it drafts Kurt Warner

**Measured and rejected.** `CDME_CONTRACTS.md` rules the rookie population should **promote
`years_exp`**, preferring `_admits_to_pool`'s `years_exp == ROOKIE_YEARS_EXP` over
`_rookie_lookup`'s KeepTradeCut flag. The ruling rests on a premise this measures and falsifies.

Probes here. Run from the repo root.

## 1. The premise

`ROOKIE_YEARS_EXP`'s own comment states it:

> A player with zero completed NFL seasons — **this year's rookie class**.

It is not. `years_exp == 0` means the feed carries no accrued-seasons value, and Sleeper's
historical rows for long-retired players carry exactly that.

## 2. The two populations, measured on the capture

```
                             n     age median   age max   >=25    on an NFL team
years_exp == 0             661         23         62      22.4%       41.6%
KTC rookie == True          72         23         31      17.4%       79.2%

in BOTH: 58        years_exp-only: 603        KTC-only: 14
```

Median age agrees. **The tail does not.** Age 62 in a rookie class is not a rounding error,
and 259 of the 661 carry no age at all.

## 3. What promoting it does to a rookie draft

12-team PPR dynasty, offence-only, real capture, after `_admits_to_pool` and eligibility —
i.e. the board a person running a rookie draft actually sees:

```
rookie board, KTC flag      :  59
rookie board, years_exp == 0: 333        enter 281, leave 7

ENTRANTS  n=281   age median 24, max 47, >=25: 57
                  on an NFL team  73 (26%)      carrying a projection  17 (6%)
LEAVERS   n=7     age median 22, max 28
                  on an NFL team   7 (100%)     carrying a projection   5 (71%)
```

The seven players it *removes* are 100% rostered and 71% priced. The 281 it *adds* are 26%
rostered and 6% priced. The oldest entrants:

```
age 47  Kurt Warner      (QB, team=None)
age 40  Byron Leftwich   (QB, team=None)
age 40  Sean Ryan        (TE, team=None)
age 37  Cedric Benson    (RB, team=None)
age 34  Kevin O'Connell  (QB, team=None)
```

**The ruling as written puts a Hall of Fame quarterback who retired in 2010 into a rookie
draft.** (`CDME_CONTRACTS` records 654/31 and 95 → 718 for this change; those were measured on
a different rulebook. The figures above are 12T_ppr offence-only. The qualitative result is
format-independent — the entrants are the same people.)

## 4. The same premise is ALREADY live — and it is a RULING, not a hole

`_admits_to_pool` admits on `years_exp == 0` unconditionally, so those players are on the
**normal** board today:

```
normal board (pool_scope='all'): 1065 rows

  ON THE BOARD: Kurt Warner      QB  age 47  years_exp 0  team None  status Inactive  proj None
  ON THE BOARD: Byron Leftwich   QB  age 40  years_exp 0  team None  status Inactive  proj None
  ON THE BOARD: Cedric Benson    RB  age 37  years_exp 0  team None  status Inactive  proj None

rows admitted ONLY by that clause (no projection, no team): 241
   96 carry status Inactive;  15 are aged 27+;  max age 47
```

**I implemented the obvious fix and reverted it.** Making the rookie clause yield to
`NOT_CURRENTLY_PLAYING` removes exactly those 96 rows (board 1065 → 969, the remaining 145
clause-only rows all `Active`, max age 34) and preserves the clause's documented purpose, since
Practice Squad is deliberately not in `NOT_CURRENTLY_PLAYING`.

It also **reverses a tested owner ruling**. `test_pool_admission_boundary.
StatusIsAFreshnessRuleNotAGateTests` is titled *"The owner's re-entry case: a retired player
un-retires and must be able to come back"*, and
`test_a_rookie_beats_a_stale_not_playing_status` pins the exact behaviour the fix removes. The
status check used to run before any evidence was read — that was the `#180` defect, vetoing 304
players carrying a positive signal — and `#193` moved it on purpose.

So this is not an unnoticed hole. It is the five-clause union working as ruled, and changing it
is `#184`.

## 5. The tension worth ruling on

The freshness rule is not applied evenly, and the two tests sit beside each other:

| row | clause | admitted? |
|---|---|---|
| retired RB, `years_exp 11`, `trade_value 9.0`, no team | stale VENDOR number | **rejected** |
| Kurt Warner, `years_exp 0`, no number, no team | stale YEARS_EXP | **admitted** |

Both are old statements from a file nobody has revisited. The first is rejected precisely
because *"without it losing here, a genuinely retired player would sit in the pool forever on
the strength of a trade value nobody has revisited."* The second lets a genuinely retired
player sit in the pool forever on the strength of an accrued-seasons field nobody has revisited.

And the re-entry justification does not require the rookie clause: a player who un-retires gets
signed, which sets `team`, which the clause below admits on its own.

## 6. What this rules OUT

- **Not a name-collision problem.** `#52` phase 1.2 already fixed `_rookie_lookup`'s key
  (58 of 788 wrong before). The KTC definition is the *accurate* one here; it is merely narrow.
- **Not fixable by promoting `years_exp` with an age filter.** An age cut is a chosen number
  (`#56`), and 259 of 661 carry no age to filter on.
- **Not an artifact of unpriced rows sorting last.** They are unpriced and do sort last, so
  they distort no valuation — but a rookie draft *filters* on this flag rather than ranking by
  it, which is why the rookie-draft consequence is the severe one.

## 7. Recommendation to the owner

**Do not promote `years_exp` as the rookie-draft filter.** It is a worse definition than the
one it would replace: it trades 7 rostered, priced players for 281 mostly unrostered, unpriced
ones including retired players.

If the two-definitions finding still deserves a repair, the live question is the narrower one in
§5 — whether the freshness rule should treat a stale `years_exp` the way it already treats a
stale vendor number. That is a one-condition change, measured above (1065 → 969), and it is
the owner's because it reverses `#193`'s tested ruling.
