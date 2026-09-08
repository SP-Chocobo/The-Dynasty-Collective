# Reference roster — a human-drafted roster the owner is satisfied with, in a competitive league

**Why this exists.** Every roster measured in #216 was produced by the engine or by a synthetic
control. This is the only LABELLED POSITIVE EXAMPLE in the repo: a real draft, a competitive
12-team room, and the owner's own verdict that the result is good. It is the sanity oracle the
shape work has been missing — and it is OUT-OF-SAMPLE for every format in the test matrix.

## Format — nothing in the matrix covers this

`QB / 2 WR / 2 RB / 2 W-R-T flex / 1 W-R flex / 1 SUPER_FLEX` = **9 starters, 5 bench, 14 total**
12 teams · PPR · **0.5 TE premium** · **3RR (third-round reversal)** · seat 12 · **REDRAFT**
· **NO TRADING — waivers only**

Five things here are untested elsewhere: no dedicated TE slot; a W-R-only flex; superflex;
a 5-slot bench; 3RR; and trades disabled. Every #216 measurement used plain `"snake"` on a
format with a dedicated TE.

## The picks

| pick | player | pos | note |
|---|---|---|---|
| 1.12 | J. Cook | RB | last of the round-1 RB tier |
| 2.1 | D. Maye | QB | back-to-back at the turn; QB1 tier emptied by 2.12 |
| 3.1 | N. Collins | WR | one of each core position by pick 25 |
| 4.12 | D. Swift | RB | |
| 5.1 | C. Skattebo | RB | RB2/RB3 taken together as the tier broke |
| 6.12 | C. Watson | WR | |
| 7.1 | P. Mahomes | QB | fills SUPER_FLEX |
| 8.12 | K. Pitts | TE | first TE, taken AFTER the TE cliff |
| 9.1 | J. Addison | WR | |
| 10.12 | S. Diggs | WR | |
| 11.1 | J. Brissett | QB | QB insurance behind two starters |
| 12.12 | D. Kincaid | TE | |
| 13.1 | R. Davis | RB | **handcuff to his own Cook (both BUF)** |
| 14.12 | K. Black | RB | **handcuff to McCaffrey — on ANOTHER manager's roster** |

## Composition, and why raw counts mislead

Raw: RB5, WR4, QB3, TE2 — which reads as `RB > WR` and appears to violate the owner's own rule.

**It does not.** Two running backs are CONDITIONAL pieces, not depth. Strip them:

**WR4 >= RB3 > TE2**, with QB3 = two superflex starters plus one backup.

The ordering holds exactly. **Score independent depth; count conditional picks separately.**
An engine scoring raw counts would flag this roster as broken, which is its own defect.

## The turn structure is the strategy

3RR at seat 12 yields pairs — overall **12/13, 48/49, 72/73, 96/97, 120/121, 144/145**, then 168.
Every pair was spent on TWO DIFFERENT needs, never doubling a position out of panic. A turn seat
can let a tier break because it gets two shots when the wheel returns.

`generate_pick_order`'s own docstring warns that treating 3RR as snake "mis-sizes the
round-2-to-3 waits worst of all — a turn-slot team's wait there is 0". Seat 12 IS the turn slot,
and the zero-gap back-to-back has never been exercised by any #216 instrument.

## What the board says about the pool

- **QB compressed hard**: two off in round 1 (1.3, 1.8), three more by 2.12, a second wave
  (Herbert, Daniels, Love, Hurts) all inside round 3. Two tiers, both gone by pick 36.
- **Elite WR went 1.4-1.9**, six straight, then a broad flat second tier running rounds 3-6 —
  which is why Collins at 25 and Watson at 72 are both defensible: waiting costs little on a
  shallow curve.
- **TE was two players and a cliff** (Bowers 2.3, McBride 2.4, then a long gap). Pitts at 96 sits
  AFTER the cliff, which is correct in a format with no TE slot: you are not paying for a
  positional edge that does not exist, you are buying a flex body with 0.5 TEP attached.

## NO TRADING — and what it does to the engine's objective

`universal_value` prices what a player is worth to **own**, which presumes a market. With trades
disabled there is **no realisation mechanism except this manager's own lineup**. A player who
never starts is worth zero here, permanently.

Consequences, recorded because they change what "correct" means:
- **"Trade capital" is not a reason to roster anyone.** The bench taxonomy loses a category:
  a spot earns its place only if it PLAYS, COVERS something that plays, BECOMES something that
  plays later, or INSURES a key piece.
- **The eight-tight-end roster is worse than #216 already said.** In a trading league surplus is
  at least convertible. Here it is inert.
- **G9 becomes conditional.** The fix's ~300 owned-asset points lost on the superflex bench may
  not be a real loss in THIS league, while remaining one in a trading league. Same number,
  different meaning, depending on a setting the engine does not read.
- **Handcuffs are worth MORE**: no trading for a replacement when a starter goes down.
- **Replacement level becomes literally true**: the "freely available alternative" IS the wire.

**THE ENGINE HAS NO TRADES-ENABLED INPUT.** Zero hits across the codebase. `league_format.py:9`
flags the gap in a comment written before today — "(waivers, trades disabled) are a different
matter" — and it never became an input. Meanwhile the LLM chairs are instructed to propose
trades, and a whole Trade Calculator surface exists, in a league where trading is impossible.

## A CORRECTION, recorded rather than quietly dropped

I (Opus) first read K. Black as "a lottery ticket PLUS trade leverage over the McCaffrey owner".
**The leverage half is wrong** — this league has no trading. It is purely the workload bet. I had
imported a mechanic the league does not have.

## What replicating this draft would require, and the state of each

| input | state |
|---|---|
| tier detection | `detect_positional_cliff` exists; **#175** — calls 34% of all rows a material cliff. Noise. |
| turn-aware waiting | `survival_probability` exists; **#206** — reads 0.00 for players who survive 60 picks. Never exercised at a zero-gap back-to-back. |
| handcuff IDENTIFICATION | derivable today from `team` + `position` + known rosters. Not built. |
| handcuff PRICING | **does not exist.** No term can raise a player's value because of a specific teammate. #50. |
| rival roster exposure | **does not exist.** Nothing models another manager's dependency. |
| trades enabled | **does not exist.** |
| contend/rebuild | **does not exist** (#217). |

Three of the four inputs behind this draft are broken or absent. That is a sharper map of what
is missing than anything the roster-shape work has produced.
