# `#30`'s root cause: the engine drafted **nine defenses** in a one-DEF league

Found by `evidence/backtest/roster_diff.py` on the first guarded 2024 backtest seat. Not
predicted — the pre-registration said "the round-4 K/DEF pick". That was the symptom. This is the
disease, and it is much larger.

## The roster

`12T_ppr_K_DEF`, 16 rounds, roster `QB RB RB WR WR TE FLEX FLEX BN×6 K DEF`. **One DEF slot.**

| | engine seat 1 | best field seat |
|---|---|---|
| WR | **1** | 7 |
| RB | **2** | 3 |
| QB | 2 | 2 |
| TE | 1 | 1 |
| K | 1 | 2 |
| **DEF** | **9** | **1** |

```
rd  1 RB   Bijan Robinson         proj 331.7   real 343.7
rd  2 TE   Brock Bowers           proj 249.9   real 273.7
rd  3 RB   Kyren Williams         proj 275.0   real 273.1
rd  4 K    Justin Tucker          proj 159.9   real 133.0
rd  5 WR   Ladd McConkey          proj 220.0   real 264.9
rd  6 DEF  Philadelphia Eagles    proj 121.5   real 153.0
rd  7 QB   Brock Purdy            proj 332.3   real 318.9
rd  8 DEF  Kansas City Chiefs     proj 120.4   real 119.0
rd  9 DEF  Denver Broncos         proj 119.9   real 190.0
rd 10 QB   Jordan Love            proj 328.8   real 321.7
rd 11 DEF  Cincinnati Bengals     proj 112.3   real 115.0
rd 12 DEF  Washington Commanders  proj 112.2   real 104.0
rd 13 DEF  Detroit Lions          proj 112.1   real 136.0
rd 14 DEF  New York Jets          proj 111.3   real 108.0
rd 15 DEF  San Francisco 49ers    proj 109.3   real  96.0
rd 16 DEF  Chicago Bears          proj 109.1   real 137.0
```

Eight of those nine defenses cannot be fielded **in any given week** — the roster has one DEF
slot. The deficit decomposes as **WR −1331 and K −192** against **DEF +994**, which is nine
defenses' worth of realized points of which at most one defense's worth reaches a lineup in any
week.

**A correction to how I first wrote this.** I said the eight "can never be fielded". That is too
strong, and the ruler is the reason: `realized_ruler` solves an ORACLE lineup, so a roster
holding nine defenses starts the best of the nine *each week*. Hoarding is therefore not purely
wasted under this ruler — it is rewarded, by roughly the max-of-nine over max-of-one spread. The
true statement is narrower and still sufficient: at most `slots(P)` of them start in any week,
so the surplus buys only week-to-week matchup churn — which is exactly what the waiver wire
gives away for free, and exactly what `#30`'s streaming baseline measures the price of. The
deficit is not that the defenses scored nothing; it is that the roster spots did not go to
receivers.

## Why VOR does this, and why it is a flat-position pathology

`bpa` is Value Over Replacement. In 2024 the thirty-two defenses project in a band of roughly
**109 to 121** — a spread of twelve points across the entire position — against a derived
replacement level of **107.95**.

So **every defense in the league has positive VOR**, from +1 to +13, and the thirty-second-best
defense is worth nearly as much as the best. Meanwhile a round-14 wide receiver sits deep in a
long tail and prices out *negative* against the WR replacement level. Once the roster's starting
slots are covered, `need_bonus` is zero everywhere and the board is pure VOR — so a flat,
shallow position outranks the real tail of a deep one, at every remaining pick, forever.

**This is not a bug in the ranking. It is the correct answer to the wrong question.** VOR against
a rank-based replacement level asks "how much better is he than the player I could roster
instead at this position". For a position you can only ever START ONE of, and whose worst member
is 90% of its best, that question has no useful answer — the alternative is not the 13th defense,
it is *the best defense on the wire that week*, which is what `#30`'s derived streaming level
measures.

## Why no existing instrument caught it

- **The projected ruler cannot see it.** `roster_strength` solves ONE lineup over season totals
  with no absences. Eight unfieldable defenses sit on the bench, contribute nothing, and cost
  nothing. The roster scores identically with them and without them.
- **The battery does not audit it.** `structural_findings` runs four audits — unfilled starting
  slots, unpriced picks, undraftable positions, duplicate picks. Nine defenses trips none of
  them: every starting slot IS filled, every pick IS priced, DEF IS a draftable position, and no
  player is duplicated. `roster_shape` and `mean_position_count` record the shape but return no
  verdict, on the stated grounds that "a verdict would need a number I chose."
- **Self-play hid it.** Every chair in the format battery runs the same engine, so all twelve
  chairs hoard defenses together and no chair is punished relative to the others.

The realized ruler sees it immediately, because a roster spot spent on an unfieldable defense is
a roster spot that never covers a real absence.

## What this does to `#30`

It promotes it. `#30` was filed as a **placement** problem — K and DST coming off the board too
early. Placement is the visible half. The other half is **quantity**, and the two have one cause:
a replacement level that prices a streamable position against the wrong alternative.

The derived streaming level should fix both, and the arithmetic says so before the arm reports:
raising the DEF level from **107.95 to 146.05** puts every defense in the league at VOR **−25 to
−37**. There is then no round at which a second defense outranks a live skill player, and the
first one is taken by `need_bonus` when the slot demands it. That is the mechanism behind the
confounded run's +226.6, and it is why the correction is not a nudge.

**A verdict IS derivable here, without choosing a number.** A position with no FLEX eligibility
can start exactly as many players a week as it has slots. `#18` measured DEF's starter-band
absence rate at 0.06 — the bye alone. So the useful ceiling is `slots + 1`, derived from
`roster_positions` and the bye, not selected. Anything above it is a roster spot that provably
cannot be fielded. That audit is proposed, not shipped — see the working log.
