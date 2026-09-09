# Fourth and Forever — a real, complete, twelve-seat startup draft

The first real post-draft population this project has had. Every prior claim about
"what a roster looks like" was measured against the engine's own drafts or against
a mid-season roster that had been traded, waivered and IR'd since.

## Provenance

- 12 teams, dynasty, superflex, half-PPR, TE premium. 26 rounds.
- **Veteran startup opened 9 August 2026** (slow clock, ran several days), followed by a
  **4-round rookie draft on 14 August** (board also captured, below). Both are from-zero
  builds with no games played and no in-season churn -- the population the engine models.
  Picks were traded between the two boards, so the rookie draft is a separate decision
  environment downstream of the startup, not a continuation of the same sitting.
- Supplied by the owner, one manager per message, in pick order. Owner's own seat
  (SPChocobo) came from the board rather than a typed pick order, so it carries
  no sequence and is excluded from the order-sensitive cuts below.
- Two name reads were ambiguous and are recorded as such: `jettas` (alamosplash,
  pick 4) counted RB; `ARich` (RTG67, pick 20) read as Anthony Richardson, QB —
  the latter is confirmed by the seat totalling 26 either way only under QB.
  `malik` (solomongrundy, pick 4) read as Nabers; Washington and Willis were
  already off the board, and every remaining candidate is a WR, so the column
  does not move.

## The distribution

| manager | QB | RB | WR | TE | picks | WR:RB |
|---|---|---|---|---|---|---|
| SPChocobo | 3 | 9 | 8 | 4 | 24 | 0.89 |
| alamosplash | 4 | 9 | 9 | 6 | 28 | 1.00 |
| noonelikesme | 9 | 6 | 6 | 4 | 25 | 1.00 |
| easyymoneyyyy | 3 | 9 | 9 | 5 | 26 | 1.00 |
| TDjer6 | 6 | 8 | 9 | 3 | 26 | 1.12 |
| maxinumum | 4 | 7 | 10 | 5 | 26 | 1.43 |
| archerpayne | 6 | 6 | 9 | 5 | 26 | 1.50 |
| adamstachecki | 5 | 7 | 11 | 3 | 26 | 1.57 |
| vizz01 | 7 | 6 | 10 | 3 | 26 | 1.67 |
| patrick32466 | 5 | 6 | 10 | 4 | 25 | 1.67 |
| RTG67 | 5 | 6 | 12 | 3 | 26 | 2.00 |
| solomongrundy | 5 | 6 | 12 | 3 | 26 | 2.00 |
| **TOTAL** | **62** | **85** | **115** | **48** | **310** | **1.35** |
| share | 20.0% | 27.4% | 37.1% | 15.5% | | |

Per-seat ranges: QB 3-9, RB 6-9, WR 6-12, TE 3-6.
WR:RB — min 0.89, median 1.46, max 2.00. **Two of twelve seats exceed 1.75. None exceeds 2.00.**

## The tail does not carry the shape

The owner's caution — "the last 3-4 of each are suspect" — is correct about intent and
irrelevant to the result. Trimming the tail off all eleven ordered seats:

| cut | picks | QB | RB | WR | TE | league WR:RB | seat median | max | >1.75 |
|---|---|---|---|---|---|---|---|---|---|
| full | 286 | 20.6% | 26.6% | 37.4% | 15.4% | 1.41 | 1.50 | 2.00 | 2/11 |
| −3 | 253 | 18.2% | 28.5% | 37.2% | 16.2% | 1.31 | 1.29 | 1.80 | 1/11 |
| −4 | 242 | 18.2% | 28.1% | 37.6% | 16.1% | 1.34 | 1.50 | 2.00 | 2/11 |
| −6 | 220 | 17.7% | 27.7% | 38.2% | 16.4% | 1.38 | 1.33 | 2.25 | 2/11 |

WR share moves 37.2%-38.2% across every cut. **No cutoff has to be chosen**, which is
the point: a hand-placed "caring stops at round 22" would have been a fitted constant
(#56), and it is not needed. The same holds for the surplus measure that replaces
headcount — a pick at or under the free alternative contributes ~0 by construction.

## The rookie draft is a SECOND population, and it does not agree with the first

The same twelve managers, hours later, over four rounds and 48 picks — with five
seats trading into or out of the round (noonelikesme finished with 7 picks,
alamosplash with 2).

| | startup (310 picks) | rookie (48 picks) | engine SHARED (687 picks) |
|---|---|---|---|
| QB | 20.0% | 14.6% | 13.2% |
| RB | 27.4% | 22.9% | 25.0% |
| WR | **37.1%** | **45.8%** | **48.9%** |
| TE | 15.5% | 16.7% | 12.8% |
| WR:RB | 1.35 | **2.00** | **1.95** |

**On the rookie board these managers allocate almost exactly the way the engine does.**
That reframes the whole finding. The engine's shape is not "wrong about receivers" as a
general matter — the same shape is what twelve humans produce when the pool is a rookie
class. What the engine appears to be doing is applying rookie-draft allocation to a
startup draft.

The obvious confound is stated and NOT corrected here: the rookie POOL's own position
mix is unknown to this measurement. If the 2026 class is WR-dense, 45.8% is a supply
fact and not a choice. Separating those needs the rookie board's available-pool
composition, which is the next capture to take. Until then this is a hypothesis with
one supporting table, not a result.

What differs between the two boards is exactly what a startup has and a rookie draft
does not: an established veteran supply, where quarterback and running back scarcity
is immediate rather than speculative. That is also where the engine's two largest gaps
sit (QB -5.4 points of share, RB -2.4 against the startup board).

### Combined, startup + rookie (final post-draft rosters, 358 picks)

| manager | QB | RB | WR | TE | picks | WR:RB |
|---|---|---|---|---|---|---|
| SPChocobo | 4 | 10 | 9 | 4 | 27 | 0.90 |
| maxinumum | 5 | 10 | 10 | 5 | 30 | 1.00 |
| alamosplash | 5 | 9 | 10 | 6 | 30 | 1.11 |
| easyymoneyyyy | 4 | 9 | 11 | 5 | 29 | 1.22 |
| patrick32466 | 5 | 8 | 10 | 6 | 29 | 1.25 |
| archerpayne | 7 | 7 | 10 | 6 | 30 | 1.43 |
| TDjer6 | 7 | 8 | 12 | 3 | 30 | 1.50 |
| noonelikesme | 9 | 7 | 11 | 5 | 32 | 1.57 |
| vizz01 | 7 | 7 | 11 | 5 | 30 | 1.57 |
| RTG67 | 5 | 7 | 14 | 4 | 30 | 2.00 |
| adamstachecki | 6 | 7 | 14 | 3 | 30 | 2.00 |
| solomongrundy | 5 | 7 | 15 | 4 | 31 | 2.14 |
| **TOTAL** | **69** | **96** | **137** | **56** | **358** | **1.43** |
| share | 19.3% | 26.8% | 38.3% | 15.6% | | |

Seat WR:RB — min 0.90, median 1.46, max 2.14, three of twelve above 1.75. The engine's
five-receiver-per-back seat still has no counterpart anywhere at this table.

## Against the engine

Engine population: the 49 SELF-seat drafts of the #221 wave battery, SHARED arm
(= the wired, shipping ruler after #216), 34 formats, 14-18 rounds.
Real rosters truncated to their first 15 picks so the horizons match.

| | real, first 15 (11 seats) | engine SHARED (49 seats) | engine, SF only (19 seats) |
|---|---|---|---|
| QB | 19.4% (2-4, mean 2.9) | 13.2% (1-3, mean 1.9) | 14.2% (2-3, mean 2.1) |
| RB | 29.7% (3-6, mean 4.5) | 25.0% (2-6, mean 3.5) | 23.8% |
| WR | **37.0%** (4-8, mean 5.5) | **48.9%** (4-10, mean 6.9) | **50.9%** |
| TE | 13.9% (1-3, mean 2.1) | 12.8% (1-4, mean 1.8) | 11.0% |
| WR:RB league | 1.24 | 1.95 | 2.13 |
| WR:RB median seat | 1.25 | 1.75 | 1.75 |
| WR:RB max seat | 2.67 | **5.00** | **5.00** |
| seats >1.75 | 1/11 | 22/49 (45%) | 9/19 |

**The engine allocates ~13 points of share to WR that no human in this league
allocates**, taken roughly evenly out of QB (−5), RB (−6) and TE (−3). Real WR share
is 37.0% at fifteen picks, 37.4% at twenty-six, and 37.6% with the tail trimmed —
it is the most stable number in the dataset, and it is not the engine's number.

The QB half is separately damning in superflex: the engine's SF seats never exceed
**3** quarterbacks and average 2.1 — that is the starting requirement with no backup.
Every human seat carries 3-9, and by pick fifteen already averages 2.9.

## What this does and does not establish

- It does NOT establish that the humans are right. They are twelve money-league
  managers in one league, not an optimum.
- It DOES establish that the engine's allocation rule sits outside the entire observed
  human range on WR, rather than at one edge of it. Fable's memo named the suspect
  before this data arrived: the band's supply side is derived, but its allocation
  rule `R x share` is an assumption. This is that assumption disagreeing with every
  seat at the table.
- The comparison is confounded three ways and each is stated rather than corrected:
  the engine seats span 34 rulebooks against this one; the engine drafts are one seat
  per format so seat position and format are entangled; and a 15-pick prefix of a
  26-round draft is a different budgeting regime from a complete 15-round draft.
  All three are reasons to re-run the battery ON THIS RULEBOOK before repairing
  anything. None of them plausibly manufactures a 13-point share gap.

## Next, in order

0. Capture the rookie board's AVAILABLE POOL composition. The rookie-vs-startup split
   above is the sharpest lead in this file and it rests on one uncontrolled table.
1. Capture the Fourth and Forever rulebook the way `greatest_show_on_paper_2.json`
   was captured. The exact starting lineup is not yet known here, and the free
   alternative — hence any surplus measure — depends on it.
2. Re-run the wave battery on that one rulebook, twelve seats, 26 rounds.
3. Only then recompute shape in summed surplus over the band-consistent free
   alternative, and only then compare allocation rules.

Do not fit a receiver penalty to this table. It is one league.
