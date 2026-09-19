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

## What per-position bands actually look like — and why none of them is the lever

*Owner: "We should at least look at what per position bands would look like… I don't
necessarily think we have to tweak the others if they're functional, considering kickers and
defenses are kind of their own animal, so it could be exceptions to how we structure them.
I'm not saying they have to be exceptions, but it's valid if that's what we land on."*

Looked. Three results, and the third cancels the first two.

### The instrument is calibrated against a boundary this repo already accepts

`QB_STARTABLE_FLOOR_FRACTION`'s comment states this repo's own test for a legitimate constant:
it must sit in a **stability basin** — *"a 48-point-wide band of threshold values all producing
the same replacement rank"* — as opposed to the reverted flat bench-demand constant, whose
plausible range straddled the cliff and swung QB1's VOR from 132 to 351.

That test has a closed form. The floor model sets `boundary(t) = #{players ≥ t}`, so
`boundary(t) == r` exactly when `s[r] < t ≤ s[r-1]`. **The stability basin of rank r IS the
marginal gap `s[r-1] − s[r]`.** No sweep, no grid, no chosen constant.

Run against the committed baseline it reproduces the documented cliff without being pointed at
it: the fraction range 0.45–0.60 spans 48.6 points and identifies rank **29 uniquely**; the
basin at rank 29 is **69.0 points** against neighbouring gaps of 3, 14, 13, 27, 9, 15, 4, 3.
The instrument finds real boundaries.

### Result 1 — the demand rank is a cliff at some positions and a smooth stretch at others

Live `12T_ppr_K_DEF` board, each position at its own league demand rank (probe
`band_basins.py`):

| pos | demand | value | basin at demand | median gap | basin / median | reading |
|---|---:|---:|---:|---:|---:|---|
| RB | 32 | 185.6 | 8.66 | 2.49 | **3.48** | cliff |
| QB | 12 | 328.6 | 11.24 | 3.27 | **3.44** | cliff |
| TE | 20 | 172.7 | 10.04 | 3.54 | 2.84 | edge |
| DEF | 12 | 108.0 | 2.34 | 1.09 | 2.14 | edge |
| WR | 32 | 216.2 | 1.20 | 2.67 | **0.45** | smooth — no boundary here |
| K | 12 | 121.8 | 0.09 | 0.87 | **0.10** | smooth — no boundary here |

**K and DST are not a clean exception class.** WR's replacement rank is *less* determinate than
DEF's — 0.45 against 2.14 — and WR is a position nobody had flagged. RB and QB sit on genuine
cliffs, which is real reassurance that those levels are well founded. The honest grouping is
`{RB, QB}` determinate, `{TE, DEF}` marginal, `{WR, K}` undetermined. DEF travels with the
skill positions; **K is alone.**

### Result 2 — band width, for any error bar you care to believe

The projection's real error bar is the one number this repo does not have yet
(`measure_projection_accuracy.py`, pending a networked run), so the band is reported as a
function of it rather than resting on a number invented here (probe `band_shape.py`):

| pos | demand | SE=1 | SE=2 | SE=5 | SE=10 | SE=15 | SE=20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| RB | 32 | 2 | 2 | 2 | 5 | 6 | 9 |
| TE | 20 | 1 | 2 | 3 | 4 | 9 | 11 |
| QB | 12 | 2 | 2 | 2 | 5 | 9 | 12 |
| WR | 32 | 2 | 4 | 7 | 13 | 16 | 21 |
| DEF | 12 | 2 | 2 | 5 | 16 | 19 | 23 |
| K | 12 | **8** | **9** | **14** | **22** | 28 | 28 |

K is the outlier at every error bar, including one point: **even a ±1-point error bar leaves
eight kickers indistinguishable at replacement.** DEF is unremarkable until SE≈10, where it
joins WR.

### Result 3 — THE NULL CHECK, which kills the lever

If replacement became the band **mean** instead of the band **point**, how far does each
position's level actually move?

| pos | point | ΔSE=1 | ΔSE=2 | ΔSE=5 | ΔSE=10 | ΔSE=15 | ΔSE=20 |
|---|---:|---:|---:|---:|---:|---:|---:|
| RB | 185.6 | +0.32 | +0.32 | +0.32 | +1.07 | −1.54 | +0.38 |
| WR | 216.2 | +0.40 | −0.48 | −1.51 | −1.94 | −2.34 | −4.26 |
| TE | 172.7 | +0.00 | +0.83 | +2.18 | +3.33 | +2.49 | +5.15 |
| QB | 328.6 | +0.20 | +0.20 | +0.20 | +4.55 | −0.21 | +1.32 |
| K | 121.8 | −0.17 | +0.06 | +0.03 | **+0.89** | −0.12 | −0.12 |
| DEF | 108.0 | +0.05 | +0.05 | −0.45 | **−1.05** | −1.23 | −2.37 |

**Nothing moves.** The largest shift anywhere is 5.15 points at TE. At K it is **0.89**, and at
DEF it is **−1.05 — the wrong direction**, making the top defense look *better* by 1.05 VOR.

The reason is arithmetic and should have been obvious before the measurement: a band centred on
the demand rank is symmetric, and the curve through it is locally straight, so the mean of the
band is the point at its centre. Widening a symmetric window on a straight line returns the
same number. **Band width is the wrong lever.** Under `#56` it would also have been a constant
chosen to produce an outcome, and it does not even produce the outcome.

### What this settles

- **No, the functional positions do not need tweaking** — but not because K and DST are
  exceptions. Because *no* position moves under this change, including K and DST. There is
  nothing to make an exception to.
- **An exception class would have been the wrong shape anyway.** The basin test puts DEF with
  TE and WR, not with K. A rule keyed on "K and DST" would have been keyed on the position
  names rather than on any measured property — hand-listing a vocabulary, which is `#126`.
- **The lever is not where replacement sits. It is whether the points above it are real.** Every
  path out of this section arrives back at predictiveness: `bpa` at K prices a 12.6-point edge
  over replacement drawn from a curve whose ranks are indistinguishable within a single point.
  Whether that edge has ever been realised is what `measure_projection_accuracy.py` answers, and
  it is the only outstanding input that changes any of these numbers.

Recorded with both probes. No ruling is requested on band width, because the measurement
withdraws the question.

## Located: the engine computes the right number and orders on a different one

*Owner: "So how do we fix their placements?"*

Everything ruled out so far was ruled out because it measured the wrong quantity. The RIGHT
quantity exists, is computed on every board, is displayed to the user — and reaches neither
ordering authority.

`positional_forfeits`' own docstring states the question K/DST placement turns on:

> *"if I take the other position now and come back to this one next turn, how much worse is the
> best player I'll realistically find there?"*

That is precisely the streaming question. Measured at a real round-9 turn with 22 intervening
picks ahead (probe `forfeit_reaches_nothing.py`):

| pos | forfeit | survival | top candidate |
|---|---:|---:|---|
| RB | **21.52** | 96% | TreVeyon Henderson |
| TE | 6.58 | 98% | Juwan Johnson |
| WR | 4.40 | 74% | Jalen Coker |
| DEF | **1.16** | 93% | Pittsburgh Steelers |
| K | **1.00** | 85% | Cam Little |
| QB | 0.30 | 89% | Patrick Mahomes |

The board at that same turn ranks **Pittsburgh DEF 4th** (`final_score` −0.10) above TreVeyon
Henderson (−1.23). Deferring the defense costs 1.16. Deferring the running back costs 21.52.
The engine takes the defense.

### The circularity check, which the model passes

`estimate_survival` and `positional_forfeits` both read the intervening opponents' **own
boards, built by this same engine**. If the engine overvalues defenses then every rival board
does too, the model predicts the defense will be taken, forfeit comes back high, and the
machinery confirms the error it was meant to correct. The run above cannot rule that out: 11 of
32 defenses were already gone, so league demand was nearly exhausted and low forfeit might only
mean "nobody needs one any more."

So the same turn was measured from a state where **no kicker or defense has been taken** — all
32 defenses on the board, all 12 teams still needing one (probe `forfeit_counterfactual.py`):

| pos | forfeit | survival | top candidate |
|---|---:|---:|---|
| WR | **7.46** | 97% | Courtland Sutton |
| RB | **7.24** | 98% | Rhamondre Stevenson |
| TE | 4.28 | 98% | Dallas Goedert |
| DEF | **1.05** | 60% | Los Angeles Rams |
| K | **0.85** | 98% | Cameron Dicker |
| QB | 0.80 | 98% | Jordan Love |

**The model is not circular.** With every defense available and every team still needing one, it
still says deferring the position costs 1.05 points. It gets that right *because* of the
flatness measured in the section above: `forfeit = best_now − curve_at(expected_taken)`, and on
a curve where DEF13 ≈ DEF1 the subtraction is small no matter who wants them. The same flatness
that inflates DEF's VOR deflates DEF's forfeit. One of those two numbers reaches the ordering.

And here is what the ordering does with it — at that turn the **top fourteen candidates are all
kickers and defenses**, the Rams at `final_score` **+34.47**, with the best running back not in
the top fourteen at all. Forfeit says the Rams are worth 1.05 of urgency; the board says 34.47
of value; the board wins, because:

- `positional_forfeit` occurs **zero times** in `draft_room.py`;
- `pick_synthesis._board_order` — the second ordering authority (`#155`), which re-sorts every
  board so `compute_draft_board`'s own order never survives to the pick — keys on
  `(fills_required_slot, final_score, unpriced, player_id)`. No forfeit term;
- `team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure +
  displacement_adj`. No forfeit term.

Forfeit reaches `pick_necessity` (the words shown beside the pick) and the board UI. It never
reaches the decision. **The engine has been explaining a choice it did not make.**

### Why every earlier candidate failed, in one line each

Each one was an attempt to fix the ordering without letting the deferral cost into it:

- **A discount multiplier** needed factor −1.96 — because scaling a term that measures value
  cannot express a fact about timing.
- **Replacement-band widening** moved nothing (−1.05 at DEF, the wrong way) — because where
  replacement sits is not what is wrong.
- **`waiting_cost`** pointed the wrong way (35.90) — because it measures drainage to the
  end-of-draft floor, not the cost of waiting one turn.
- **ADP** carries no signal here: every DEF is `16983` and every K `~18000`, the vendor's
  *undrafted sentinels*. That is absence, and reading a sentinel as "the market drafts them
  late" is the `#187` defect this repo forbids.

All four were substitutes for the number already on the board.

### The shape of the fix — for owner ruling under `#184`

The classical formulation of "take him now or later" is *value now minus the value of what I
would get at this position next turn*. Both halves are already computed:

    ordering key  =  final_score  −  curve_at(expected_taken)
                  =  final_score  −  (best_now − forfeit)

At the counterfactual turn that makes the Rams' advantage-of-acting-now **1.05** against
Courtland Sutton's **7.46**, and K/DEF sort to the back without a single new constant — the
term is one the engine already produces, moved from the explanation into the decision.

Two properties worth stating before any ruling:

- **It introduces no constant, so `#56` is not engaged.** It is a re-use of an existing
  computed quantity, not a calibration.
- **It self-corrects the obvious objection.** "This would take an urgent mediocre RB over a
  generational TE" — no: `forfeit` is `best_now − curve_at(expected_taken)`, so a generational
  TE whose position falls off a cliff behind him carries a *large* forfeit of his own. The rule
  under-weights elite talent only where the position genuinely replaces him cheaply, which is
  the case it exists to catch.

**Not implemented here.** It changes what the board ranks on, at both ordering authorities
(`#155` requires they agree), which is an engine-design change and the owner's call under
`#184`. The next step that does not require a ruling is an A/B: one process, one code version,
toggling only the ordering key, reporting where K and DEF land in each arm.

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

