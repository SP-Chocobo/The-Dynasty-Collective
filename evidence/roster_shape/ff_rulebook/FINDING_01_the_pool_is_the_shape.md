> **CORRECTED -- DO NOT QUOTE THE NUMBERS IN THIS FILE.** Every figure here was
> computed over the 764-row VENDOR RECONSTRUCTION, not the 6,595-player real
> capture the engine actually drafts from. See CORRECTION_wrong_universe.md.
> The described mechanism may survive re-measurement; none of these numbers do.

# The engine's WR share is a deviation FROM the pool, not a copy of it

First board ever built on Fourth and Forever's real rulebook (half PPR, TE 0.75/rec,
superflex, first-down scoring, 12 teams, the real 29-slot roster). Opening board, no
picks made.

## The number that matters

| | WR share |
|---|---|
| the priced pool this league actually offers | **38.9%** (109 of 280) |
| twelve real managers, this league's startup | **37.1%** |
| the engine, 49 battery seats | **48.9%** |

Full priced pool: QB 40 (14.3%), RB 79 (28.2%), WR 109 (38.9%), TE 52 (18.6%).

**The humans drafted approximately the pool.** Within 1.8 points of it. That is not a
strategy I fitted to them -- the pool composition is an observable, computed from the
merger's own priced rows before any pick is made, and it lands on the number twelve
independent managers produced.

The engine does not. It sits +10 points of share above the pool it is drafting from.

This is the first framing of the roster-shape problem that needs no constant. "Does the
engine's output composition track the composition of the pool it draws from?" is a
question with a derived answer on every rulebook, and #56 has nothing to object to.

## What the opening board actually looks like

Mean `universal_value` over the whole priced board, by position:

| pos | n | proj_pts | universal_value | bpa |
|---|---|---|---|---|
| QB | 40 | 230.62 | **+34.69** | +32.62 |
| RB | 79 | 157.29 | **+3.45** | +6.29 |
| WR | 109 | 161.32 | **-33.40** | -34.68 |
| TE | 52 | 141.50 | **-13.87** | -13.50 |

Top of board by `final_score`: top 24 is QB 12 / RB 6 / WR 3 / TE 3; top 100 is RB 30 /
QB 26 / WR 26 / TE 18. **The opening board is not WR-heavy at all** -- WR carries the most
negative mean value of any position, because the WR pool is the deepest (109 rows) and its
tail prices far below replacement.

So the engine's WR-heavy FINISHED rosters cannot be coming from the top of the board.
They come from later, and the mechanism has to be found in how the board evolves as the
pool drains -- not in the opening ranking. That is the next measurement, and it is now
possible for the first time because the rulebook exists.

Note this also means the two claims are not in contradiction: RB and WR carry IDENTICAL
starter demand here (3.05 each, `draft_room.starter_slot_counts`), so nothing on the
demand side prefers receivers. Whatever produces the +10 is not demand.

## A hard supply defect, found on the way

**280 priced rows for a 312-pick startup.** Thirty-two picks in this league have no priced
player available at all -- the board is exhausted before the draft is. That is a supply
gap in the #193/#209 family, on the owner's own league, and it bounds what any composition
measurement here can mean: the last ~10% of the draft cannot be a valuation decision
because there is nothing left to value.

Pool admitted: 764. Priced: 280. The other 484 are admitted but unpriced.

## Method

`evidence/roster_shape/ff_rulebook/build_ff_board.py`, run from the repo root, five-line
fixture per the engine-measurement skill: `DataMerger()` -> `build_players_db` ->
`league_format_hint` -> `set_league_format` (hint derived from the league, never carried
alongside it) -> `compute_draft_board`. Format hint resolved to
`{scoring: half_ppr, superflex: True, te_premium: True}`, which is correct for this league.
