# CORRECTION: FINDING_01 through FINDING_04 measured the wrong player universe

## What happened

`build_ff_board.py` (as first written) called `rdb.build_players_db(merger)` -- the VENDOR
RECONSTRUCTION: 764 players, id space `"16"`, `"291"`.

`run_ff_draft.py` called `rdb.build_players_db_from_capture()` -- the REAL Sleeper universe:
6,595 players, id space `"13384"`, `"8931"`.

Two different populations. Only 373 ids collide and those collisions are coincidental --
**311 of the draft's 312 picks were not on the board I had been analysing**, which is how
this surfaced. #201 exists precisely because the reconstruction is not what production
drafts from, and made it a raise-on-missing forbidden fallback for the battery. This probe
was still calling the old function.

Sixth fixture error of this kind in this repo, and the engine-measurement skill's own
opening line is that every measurement error here was a fixture error, not a reasoning one.

## The numbers, corrected

| | QB | RB | WR | TE | rows |
|---|---|---|---|---|---|
| WRONG board (vendor, 764) | 14.3% | 28.2% | 38.9% | 18.6% | 280 |
| **REAL board (capture, 6,595)** | **13.9%** | **22.9%** | **40.4%** | **22.9%** | **1,119** |

## What is WITHDRAWN

**FINDING_01's headline is withdrawn twice over.**

1. "280 priced rows for a 312-pick startup, 32 picks with no priced player." **False.** The
   real board carries **1,119 priced rows**. There is no supply shortfall in this league.
2. "The humans drafted approximately the pool (37.1% vs 38.9%), the engine deviates."
   **False.** Against the real pool the humans deviate too -- they take 15.5% TE where the
   pool offers 22.9%, and 20.0% QB where it offers 13.9%. The tidy "humans track the pool"
   story was an artifact of the wrong pool.

**FINDING_02, 03 and 04's numbers are all withdrawn** -- every replacement level, VOR,
displacement adjustment and cancellation test in them was computed over the 764-row vendor
board. The QUALITATIVE mechanisms they describe (VOR flattening where a curve is linear;
the position defining `max(level)` paying nothing; the non-positive rule capping TE's
deduction) may well survive re-measurement, but not one of their figures may be quoted
until they are re-run. They are kept, marked, not deleted.

## What SURVIVES, and it is the important part

**FINDING_05 is untouched.** The 12x26 draft used the real capture universe end to end --
players, season projections, and this league's own scoring -- and its result stands:

| | QB | RB | WR | **TE** |
|---|---|---|---|---|
| twelve real managers, this league | 20.0% | 27.4% | 37.1% | **15.5%** |
| **the engine, same league** | **10.3%** | **26.9%** | **30.4%** | **32.4%** |

**The engine takes more than twice the tight ends a human takes (32.4% against 15.5%), and
half the quarterbacks (10.3% against 20.0%), in a superflex league.** Nine of twelve seats
finish with exactly two quarterbacks -- the starting requirement, with no backup.

That comparison needs no pool at all. It is the engine against twelve real managers on one
rulebook, both measured on the same real universe, and it is the finding to repair against.

## Method note for whoever runs the next probe

The five-line fixture in the engine-measurement skill still names `rdb.build_players_db`.
That was correct when written and was superseded by #201. **Use
`rdb.build_players_db_from_capture()` plus `rdb.season_projections_from_capture()`, and pass
`sleeper_basis=SLEEPER_BASIS_SEASON_SUM`** -- the three things production does and the
battery was fixed to do. A probe that skips them measures a smaller, vendor-shaped
population and will produce plausible numbers about the wrong thing, which is exactly what
happened here.
