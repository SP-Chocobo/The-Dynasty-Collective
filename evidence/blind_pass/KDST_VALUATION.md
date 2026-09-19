# K and DST are drafted about five rounds too early, and why no existing term can fix it

Found by the `12T_ppr_K_DEF` arm added to close the `has_defense` axis (#52 Phase 8 gate). Before
that arm, `format_axes_exercised` stated outright that *"the battery's results are not evidence
about team-defense drafting."* They now are, and this is the first thing they say.

## The measurement

Drafted the way `run_battery` drafts — `draft_simulation.simulate_full_draft`, `mode="auto"`,
each seat taking `snap.candidates[0]` off the narrowed list:

| pos | taken | first round | median round | last round |
|---|---:|---:|---:|---:|
| RB | 40 | 1 | 5.0 | 16 |
| WR | 51 | 1 | 6.0 | 14 |
| QB | 17 | 4 | 8.0 | 14 |
| **DEF** | 27 | **5** | **10.0** | 14 |
| **K** | 29 | **7** | **10.0** | 13 |

Owner's stated target: the **bottom 25–30% of the draft** — rounds 12–16 of 16. First taken is
about five rounds early; the median is two.

**A METHOD ERROR IS RECORDED HERE because it nearly became the finding.** The first pass drafted
with `compute_draft_board(mode="balanced")` and took `board[0]`. That is not what the battery
does: the real simulator defaults to `mode="auto"` (which falls into upside scoring late) and
picks through `narrow_candidates`/`_board_order`, a second ordering authority. The corrected run
gave the same answer, so the conclusion stands — but it was luck, not method, and the arm was
briefly suspected of being misconfigured on the strength of a probe artifact.

The arm itself is sound: `starter_slot_counts` returns `K 1.0, DEF 1.0`, identical to a
properly-ordered Sleeper roster where the slots precede the bench.

## The mechanism

`bpa` is raw VOR in season points, compared across positions with no normalisation:

| rank | player | pos | proj | bpa |
|---:|---|---|---:|---:|
| 62 | Ladd McConkey | WR | 244.3 | 28.02 |
| 63 | TreVeyon Henderson | RB | 214.6 | 28.96 |
| **65** | **Los Angeles Rams** | **DEF** | **138.4** | **30.47** |

The Rams outrank a starting NFL receiver because DEF1 − DEF12 is **30.5 points** while that
receiver sits **28.0** above his own replacement. Arithmetically correct; football nonsense. A
defense produces a third of a receiver's points and its *spread* is still competitive in
absolute terms, so it prices into round 5.

## Three candidate levers, two measured out

**Forfeiture — ruled out.** `positional_forfeit` occurs **zero times** in `draft_room.py`. It
feeds `pick_necessity` only; the board orders on `final_score`. It cannot move a board rank.

**Horizon — ruled out, and it points the wrong way.** `waiting_cost` is computed and is
deliberately *observable only* (its own docstring: *"Nothing here feeds universal_value,
team_acquisition_value, bpa, or necessity… the raw quantity gets to be measured and argued with
before it is allowed to move a decision"*). Measured, it says deferring the top DEF costs
**35.90** — more than their VOR. Wiring it would push defenses **up**.

The reason is that it measures something else: `bpa` scores against the *demand-rank* player,
`waiting_cost` against the *end-of-draft* floor, so their ratio is how much further a position
drains by the end — RB 1.58 (drains hard), K 1.01 (barely drains). That is drainage, not
streamability.

**Replacement value — the live one, but arithmetically constrained.** Every sane candidate for
"the alternative at DEF" sits in the same six-point band:

| candidate replacement | value | implied VOR for the top DEF |
|---|---:|---:|
| demand rank (DEF12, current) | 108.0 | 30.5 |
| best free agent after the draft (DEF13) | ~106 | ~32 |
| end-of-draft horizon floor | ~102.5 | ~36 |

Changing *which player* is replacement does not fix it.

## Why a discount multiplier cannot substitute

Solved directly: to put the top DEF below the skill player available at the round-13 boundary,
the required factor on its `bpa` is **−1.96**. Negative, because by round 13 the remaining skill
players score **−55.73** (far below their own replacement) while the top DEF is at **+34.47**,
of which only 30.47 is `bpa`. **Zeroing K/DEF `bpa` entirely still leaves them at +4.00**, ahead
of everything from round 8 onward.

That is structural: a deep pool's VOR goes deeply negative late, a shallow pool's cannot. K and
DEF look good late *because* their pool is shallow. Only an arbitrary additive offset would force
the shape, which is more invention than the discount it was meant to avoid.

## What is actually missing

**Every valuation term trusts the projection.** `bpa`, `waiting_cost` and `horizon_replacement`
all agree the Rams are ~30 points better than the alternative *because the projection says so*,
and nothing anywhere asks whether a position's projections come true. That is why none of the
three levers can be tuned into the right answer — they are all downstream of that belief.

Two things follow, and both are measurable rather than arguable:

1. **Predictiveness per position.** Compare a prior season's projections against what was
   actually scored. For K and DST this is not even a proxy: their projections *are*
   Sleeper-seeded (`KDST_SEEDED_SOURCE_FILES`), so measuring Sleeper's predictiveness for them
   measures the exact input the board prices.
2. **Replacement for a streamed position is not a player.** It is the best available *each week*,
   chosen with matchup knowledge nobody has on draft day. That portfolio outscores any single
   defense's season line, so the true replacement is materially higher than DEF12 and the real
   VOR correspondingly smaller. `replacement_levels` cannot express this: it picks one player at
   a rank, by construction.

Both need weekly historical data. `SleeperClient` already carries both endpoints —
`get_weekly_projections(season, week)` and `/stats/nfl/{type}/{season}/{week}` — but nothing
historical is on disk (`data/fixtures/sleeper_capture.json` carries `season_projections` only,
no actuals) and `outcome_record` has nothing captured. The API is **not reachable from the
audit sandbox**, so the measurement has to be run on a networked machine.

## Status for v2

**Recorded, not repaired.** The arm's K/DST timing is a **known defect, not evidence of correct
behaviour**, and the battery's output must not be read as endorsing it. Shipping a forced shape
would have hidden the defect behind a number nobody derived; `#56` forbids exactly that, and the
owner's own instinct on the point — *"we're kind of forcing the shape that we want instead of
letting the math decide"* — is what stopped it.
