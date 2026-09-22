# The board prices from a different source depending on how it is CALLED — and that explains three findings

`compute_draft_board` takes `sleeper_projections` and `sleeper_basis`. What those arguments carry
decides which vendor prices every row, and three separate conclusions in this repository turn out
to hinge on which call was measured. Measured on `12T_ppr_K_DEF`, no picks, reading `bpa_source`
off the starting band of each position:

| call | QB/RB/WR/TE | K/DEF |
|---|---|---|
| no `sleeper_projections` | `points_vor_draftsharks` | `points_vor_sleeper_seeded` (the CSVs) |
| `season_projections_from_capture()` — **what the battery does** | `points_vor_sleeper_season_scored` | `points_vor_sleeper_season_scored` |
| full Sleeper season sums — **what `app.py` does** | `points_vor_sleeper_season_scored` | `points_vor_sleeper_season_scored` |

Every position in the starting band, in both configurations anything actually runs, prices from
**one source**. The two-vendor split exists only in a board built with no Sleeper argument at all,
which neither `app.py` (lines 4927, 5006, 5066, 5431) nor `run_draft_battery` (line 425) does.

## #28 IS WITHDRAWN

`#28` said the board compares `points_vor_draftsharks` against `points_vor_sleeper_seeded` on one
`bpa` scale, with nothing establishing the two vendors' point scales agree, and called that the
strongest remaining explanation for defenses going five rounds early.

**Measured, that comparison never happens.** I raised it from a board I built myself without the
Sleeper argument, and then described it as "the live board". It was not a live board; it was a
configuration with no caller. The finding is withdrawn, not downgraded.

What remains true and much smaller: the un-synced fallback path *does* mix two vendors, and nothing
establishes their scales agree. It is reachable only if a live sync returns nothing, and on that
path the board is already degraded in ways it announces. Worth a line in the module, not a ruling.

## AND MY CORRECTION OF THE 3.1x WAS ITSELF WRONG

The previous pass "corrected" `KDST_VALUATION.md`'s QB 43.9 / K 12.6 / DEF 30.5 as stale numbers
from a board that no longer exists, and replaced them with QB 55.0 / K 13.0 / DEF 18.0 measured on
what it called the live board.

Rebuilt in the **battery** configuration, the original numbers reproduce exactly:

| pos | KDST_VALUATION | rebuilt today |
|---|---|---|
| QB | 43.9 | **43.9** |
| K | 12.6 | **12.6** |
| DEF | 30.5 | **30.5** |

`KDST_VALUATION.md` was never stale. The 55.0 / 13.0 / 18.0 I replaced it with came from the
un-synced board — the same phantom configuration that produced `#28`. **One wrong measurement
produced two published errors: a withdrawn finding and a correction of a finding that was right.**

The un-correction, stated plainly: **the 3.1x was arithmetically right.** Board DEF/QB is 0.69,
realized DEF/QB is 0.26 (2023) and 0.23 (2024) — an overstatement of 2.7x and 3.0x.

## But the 3.1x still must not be used, for the reason the pass BEFORE that one gave

It is a QB-normalised number, and QB-normalisation is what manufactures it. Hindsight-ranking
inflates the realized gap of every position, unequally: measured `sd/gap` is 0.08–0.09 for RB/WR/TE,
0.17 for QB, 0.38–0.39 for K/DEF. QB's own realized gap is inflated 5.9x over its board gap while
DEF's is inflated 1.9x, so dividing one by the other reports the difference in inflation as a
difference in pricing.

The hindsight-free estimator disagrees outright. Slope of realized on projected, which never ranks
by outcome:

| pos | whole pool 2023 / 2024 | starting band 2023 / 2024 |
|---|---|---|
| QB | 1.00 / 1.05 | 0.56 / 2.59 |
| RB | 1.05 / 1.07 | 0.89 / 1.13 |
| WR | 1.01 / 1.01 | 0.96 / 1.13 |
| TE | 0.99 / 1.00 | 0.92 / 0.96 |
| K | 1.00 / 1.03 | 0.88 / 0.28 |
| **DEF** | **1.80 / 2.84** | **3.11 / 6.36** |

DEF's projected spread **under**-states what the season paid, in the band and over the pool, in
both seasons. Read the band column with its own warning attached — QB swings 0.56 to 2.59 across
two seasons, so a twelve-player band is not a population and only the pool column is stable.

**There is no DEF over-pricing defect in the projections.** Three passes looked for one from three
directions and the only estimator without hindsight in it says the spread is too small, not too
large. Whatever puts defenses five rounds early, it is not `bpa` being too big — which
`KDST_VALUATION.md` itself already found by a different route: *"Zeroing K/DEF `bpa` entirely still
leaves them at +4.00"*.

## What this costs, honestly

Four published conclusions from this thread have now been withdrawn or corrected: the cliff-steepness
hypothesis, `#23`, the 3.1x (corrected, then un-corrected), and `#28`. Every one of them was
measured rather than guessed, and the measurement was on the wrong object each time — a probe whose
league had no K slot, a probe that computed the wrong replacement arm, a document assumed stale, a
board built with an argument no caller passes.

The pattern is narrower than "be careful". It is: **the configuration is part of the measurement,
and this codebase has configurations that differ silently.** `compute_draft_board` returns a
perfectly good board with no Sleeper argument; nothing warns that it is a board no caller builds.
The engine-measurement checklist says to ask what would have to be true for a number to be an
artifact. For this engine the first question is now *which call produced this*, and the answer
belongs beside every board number anyone reports.

---

## A fourth reason the K/DEF "defect" is not an engine defect: it moves with the SNAPSHOT

The two configurations that exist in practice do not agree about how DEF is priced relative to
offence, and the disagreement is larger than the effect anyone has been hunting:

| pos | band | battery `bpa` gap | /QB | app-shaped `bpa` gap | /QB |
|---|---|---|---|---|---|
| QB | 12 | 43.9 | 1.00 | 69.7 | 1.00 |
| RB | 32 | 227.6 | 5.19 | 218.8 | 3.14 |
| WR | 32 | 179.4 | 4.09 | 175.1 | 2.51 |
| TE | 20 | 137.5 | 3.13 | 150.4 | 2.16 |
| K | 12 | 12.6 | 0.29 | 18.7 | 0.27 |
| **DEF** | 12 | **30.5** | **0.69** | **22.0** | **0.32** |

**DEF's price relative to QB swings by a factor of 2.2** — 0.69 against 0.32 — purely by changing
which set of season projections feeds the board. Same engine, same league, same code path, same
source label on every row.

It is not a coverage difference. Priced share per position is near-identical across the two:

| pos | battery | app-shaped |
|---|---|---|
| QB | 31% | 36% |
| RB | 58% | 53% |
| WR | 51% | 49% |
| TE | 50% | 50% |
| K | 75% | 74% |
| DEF | 100% | 100% |

The difference is in the numbers themselves. The battery's `season_projections_from_capture()`
draws on a stored live-sync snapshot — 5,346 entries of which 4,506 carry only an ADP field — while
the app-shaped arm sums Sleeper's weekly projections for a season. Both are legitimate inputs;
they are not the same numbers, and QB's rank-1-to-replacement gap differs by 59% between them
(43.9 against 69.7) while DEF's differs by 39% the other way.

**So "defenses are priced 0.69 of a quarterback" is a fact about a snapshot, not about the
engine.** `KDST_VALUATION.md` measured the battery snapshot, correctly, and every downstream
conclusion about DEF being over-priced relative to offence inherits that snapshot without saying
so. Under the app-shaped input the same board prices DEF at 0.32 of QB — close to the 0.26 and 0.23
the seasons actually paid.

That is the fourth independent reason, from a fourth direction, that the reliability hunt has not
found an engine defect:

1. the two-player estimator could not resolve one;
2. the hindsight-free slope says DEF's spread is *compressed*, not inflated;
3. DEF's ordering skill (0.75 / 0.48) is about QB's;
4. and the relative price it is accused of having is a property of the input snapshot.

## What actually needs doing, and it is small

Nothing here is a repair to the valuation. What it argues for is that **a board number is not
reportable without the call that produced it**, the same way `#166` and `#174` established that a
quantity travels with the basis that gives it meaning. The battery already records
`priced_from` and `sleeper_basis` in its universe block. The gap is that a board row does not, and
an evidence file quoting `bpa` gaps therefore cannot be checked against the configuration it came
from — which is exactly how two wrong conclusions got published.

`which_call_prices_the_board.py` prints the comparison, and
`test_which_call_prices_the_board.py` pins both halves: that the synced configurations price every
starting-band row from one source, and that the un-synced path really does mix vendors, so the
withdrawal of `#28` rests on WHERE the mixing happens rather than on a claim that it never does.

---

## The snapshot does NOT drive K/DST placement — hypothesis falsified, and that is the useful result

The obvious next step from the 2.2x price swing above was: if DEF is priced 0.69 of a quarterback
under the battery snapshot and 0.32 under the app-shaped one, the whole "defenses go five rounds
too early" complaint might be an artifact of the battery's fixture. Drafted, same format, same
commit, same process, changing **only** the projection snapshot
(`kdst_placement_by_snapshot.py`, 12 teams x 16 rounds, self-play):

| | battery capture | app-shaped 2026 |
|---|---|---|
| first K | 7.00 | 6.08 |
| first DEF | **5.08** | **6.05** |
| first QB | 4.09 | 3.07 |
| first TE | 1.08 | 1.07 |
| K+DEF taken by round 12 | **47** | **48** |

**It does not move.** DEF's relative price changes by a factor of 2.2 and its first selection moves
by less than a round — in the *later* direction for the arm that prices it lower, which is the
right sign but nowhere near the size of the price change. K+DEF taken by round 12 is 47 against 48.

So the hypothesis is dead, and what it leaves behind is a fifth independent confirmation of the
thing four other measurements already said: **`bpa` magnitude is not what puts defenses in round
five.** Halve DEF's price relative to every other position and the draft barely notices.
`KDST_VALUATION.md` reached the same place by a different route and recorded it plainly —
*"Zeroing K/DEF `bpa` entirely still leaves them at +4.00"* — and this is that sentence confirmed
from the outside, by moving the price rather than by removing it.

Which also means the remaining candidates are all downstream of `bpa`: whatever selects a defense
in round five is reading something other than how many points it is worth.

### And #17's recorded numbers no longer reproduce

`#17`'s re-measurement records `first DEF : pick 33 (3.09)`, `first K : pick 46 (4.10)`, and
`K/DEF by round 12: 37`. On HEAD, in the same rulebook with the same battery snapshot, it is
**5.08**, **7.00** and **47**. Placement has moved roughly two rounds later for DEF since that run,
and one and a half for K, while K/DEF volume by round 12 rose 37 -> 47.

That is not explained by `#24`: necessity has no selection authority (`#55`), the board orders on
`team_acquisition_value`, and this draft takes `candidates[0]`. Something between the two runs
moved it and the item's numbers are stale either way — so `#17` cannot be closed on the figures it
currently carries, and re-running it is a prerequisite to ruling on it rather than a formality.
