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

---

## The replacement band is tight in POINTS and loose in RANKS

*Owner challenge: "Could the tightness of the band on replacement value be suspect, relative to
the values involved?"*

**Yes, and the argument above is the thing it breaks.** Three candidate replacements for DEF
were reported as sitting inside a six-point band, and that band was read as evidence that which
player is replacement does not matter. It is not evidence. Two separate defects:

1. The three candidates are not independent constructions. Demand rank is DEF12, best free agent
   is DEF13, the horizon floor lands around DEF14-15 -- **adjacent ranks on one curve.** Three
   points a few ranks apart on a flat curve are close for the same reason any three adjacent
   points are close. That was a measurement of *which player*, reported as though it were a
   measurement of *what kind of quantity*.
2. Six points is tight only against values at the position that produced it. The unit the board
   resolves replacement in is RANK, not points, so the band has to be read in ranks.

Measured on a real `12T_ppr_K_DEF` board (1,153 rows, `projected_points`, probe
`band_curve.py`):

| pos | r1 | r5 | r12 | r20 | r32 | last | r1-r12 gap | slope r10-r20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| RB | 413.2 | 318.2 | 274.6 | 245.7 | 185.6 | 0.2 | 138.6 | 3.48 |
| WR | 395.7 | 327.9 | 288.4 | 254.3 | 216.2 | 0.0 | 107.3 | 4.40 |
| TE | 310.2 | 231.2 | 190.3 | 172.7 | 90.9 | 0.7 | 119.9 | 2.85 |
| QB | 372.5 | 347.8 | 328.6 | 304.6 | 207.5 | 0.0 | 43.9 | 2.99 |
| K | 134.3 | 130.7 | 121.8 | 119.1 | 61.3 | 7.3 | 12.6 | 0.45 |
| DEF | 138.4 | 121.8 | 108.0 | 100.3 | 72.5 | 72.5 | 30.5 | 1.17 |

Converting the band into its own unit:

| pos | ranks covered by a 6-point band | pool |
|---|---:|---:|
| WR | **1.4** | 197 |
| RB | **1.7** | 126 |
| QB | **2.0** | 42 |
| TE | **2.1** | 115 |
| DEF | **5.1** | 32 |
| K | **13.4** | 38 |

**The same six points that pins replacement to within two ranks at every skill position pins it
to within five at DEF and thirteen at K.** Thirteen ranks is a third of the kicker pool. The
band was never tight; it was reported in the one unit that made it look tight.

Two consequences that follow directly:

- The band's width is **within the plausible error of the projection it is drawn from.** The
  whole rosterable DEF pool spans 65.9 points (r1 138.4 to r32 72.5) -- less than half the
  138.6-point gap between RB1 and RB12 *alone*. At K the startable spread (r1 to r20) is 15.2
  points. A valuation that resolves a position to within 6 points on a curve that flat is
  asserting a precision the input does not carry.
- This **supports** the predictiveness diagnosis rather than competing with it. If ranks 10
  through 23 at K are indistinguishable within projection error, then K's `bpa` is not measuring
  a real edge over replacement -- it is measuring where the vendor happened to break a tie. The
  engine then prices that tie-break at full face value because nothing anywhere measures whether
  a projected gap at K has ever been realised.

**Not repaired here, and deliberately.** Correcting this means changing what "replacement" means
per position -- widening the band where the curve is flat, or scaling `bpa` by how determinate
the position's curve is. Both are engine-design changes under `#184`, and both would be
calibration under `#56` unless the width is DERIVED from the curve rather than chosen. The
derivation is available -- slope is measured above and `measure_projection_accuracy.py` supplies
the realised side -- but it is the owner's ruling to make, not a repair to slip into a
certification pass. Recorded, with the instrument, so the ruling has numbers under it.

---

# `K-07` — the mock draft reloads the merger twice per rerun *(pinned, not repaired)*

Ruled a `v2-freeze` gate as a **pin**: convert a known defect into a guarded one, rather than
repair it blind.

`DataMerger.set_league_format` is a no-op on an unchanged format and a full `reload()` on any
change. The UI asserts a format at two places — once unconditionally at the top of every rerun
with the live league's format, and once inside the Mock Draft view with the mock's own. Those
differ whenever the mock is configured differently from the live league, which is the ordinary
case, since configuring a different format is what the mock is *for*.

Measured on the committed baseline:

| | |
|---|---:|
| unchanged format (the no-op) | **0.0 ms** |
| format change → `reload()` | 333.2 ms |
| change back → `reload()` | 319.3 ms |
| **one mock-view rerun** | **652.5 ms** |
| the same rerun anywhere else | 0.0 ms |

And the reload is only the visible half. `_load()` reinstates an **empty `_merge_memo`** —
verified here rather than inferred — so every merged row computed for the previous board is
discarded and the next board is built cold. The original finding measured that downstream cost
at **0.87 s warm against 18.0–18.9 s cold**, paid on every button click in the view.

**Why pinned rather than fixed.** It is latency, not a truth defect: no number the engine
reports is wrong because of it. The fix lives in Streamlit rerun sequencing, which cannot be
executed or verified from the audit sandbox, and a wrong fix silently breaks the mock draft — a
real regression traded for a speedup.

`test_mock_draft_reload_cost.py` names its own exit: assert the mock's format once and let the
top-of-rerun assertion see it (or scope a second merger to the mock view), so a rerun performs
at most one reload. Four mutants, all killed — including **the repair itself**, which fails the
characterization and is exactly the signal it exists to give.

