# RESULT — the aggregate composition is set by one subtraction, before any pick

Pre-registered in `PREREG_aggregate_selection.md`. One opening board, #201/#204 recipe, real
capture universe (6,595), season sums under this league's own scoring, no picks, no engine
source modified. 10.6s. Raw saved before any derivation; universe assertion passed (all 312
drafted ids present on the board).

## The fork read, and why the fork read undersells it

Pre-registered: T = tight ends in the top 312 by raw projected points. **T = 67** — FORK C
(both contribute). But the full table shows the split is extremely lopsided, and shows
something the fork did not ask for.

| ranked by | QB | RB | WR | **TE** | overlap with drafted 312 |
|---|---|---|---|---|---|
| priced pool (481 rows) | 8.7% | 26.2% | 41.2% | 23.9% | — |
| **raw projected_points** | 35 (11.2%) | 79 (25.3%) | 131 (42.0%) | **67 (21.5%)** | 273/312 |
| **bpa = points − level** | 34 (10.9%) | 83 (26.6%) | 94 (30.1%) | **101 (32.4%)** | **310/312** |
| + the six other terms | 34 (10.9%) | 84 (26.9%) | 96 (30.8%) | 98 (31.4%) | 309/312 |
| **ACTUALLY DRAFTED** | 32 (10.3%) | 84 (26.9%) | 95 (30.4%) | **101 (32.4%)** | 312/312 |
| twelve real managers | 20.0% | 27.4% | 37.1% | **15.5%** | — |

**The entire 312-pick draft reproduces a single pre-draft board sort to within three players.**
RB is exactly 84 in both. The full valuation's top 312 overlaps the drafted 312 at 309 of 312.

**And the whole positional movement happens in ONE step.** Ranking by raw points gives 67 tight
ends. Subtracting the replacement level gives **101** — the exact number the draft produced.
The six remaining terms together move TE by −3, RB by +1, WR by +2, QB by 0.

So: raw projections do not produce the excess. Twelve rosters, 26 rounds of accumulated state,
the mode boundary, `narrow_candidates`, and six of the seven score terms do not produce it
either. `points − level`, evaluated on an empty roster before the draft starts, produces all
of it.

## The mechanism, in production's own numbers

Level derived as `projected_points − bpa` from the two emitted columns (one constant per
position, as the contract requires).

| pos | priced | **level** | top pts | median pts | rows above level | taken in the top-312-by-bpa cut | **raw points of the WORST player in that cut** |
|---|---|---|---|---|---|---|---|
| QB | 42 | **243.29** | 406.4 | 330.0 | 31 | 34 of 42 | **111.1** |
| RB | 126 | **170.81** | 429.0 | 58.6 | 36 | 83 of 126 | **29.1** |
| WR | 198 | **217.75** | 407.9 | 69.8 | 36 | 94 of 198 | **75.9** |
| TE | 115 | **149.17** | 328.0 | 45.6 | 24 | **101 of 115** | **7.4** |

The 312 cut is a single global threshold on bpa: −141.66 (RB), −141.86 (WR), −141.76 (TE).
One number, applied to all positions. But the levels subtracted from each position span
**94 points**, so the same bpa threshold means a completely different raw player at each
position:

> **A tight end projecting 7.4 points clears the cut. A receiver needs 75.9.**

The engine takes **101 of the 115 priced tight ends — 88% of the entire priced TE pool** —
against 94 of 198 receivers (47%) and 83 of 126 backs (66%).

Why TE's anchor sits lowest: the level is the projection of the player at the position's
replacement RANK. TE starter demand is 2.05/team (24.6 league-wide) and only 24 tight ends
project above the level at all; the TE curve has collapsed by rank 25. WR demand is 3.05/team
(36.6) drawn from 198 priced bodies with a median of 69.8. Shallow pool, early collapse,
low anchor.

## What this is, and what it is NOT

**It is not a bug report.** `points − level` is value over replacement — the engine's stated,
intended design, doing exactly what it says. Subtracting a positional anchor is the whole
point of VOR. Nothing here shows the subtraction is implemented wrongly; the levels are one
constant per position, derived from this league's own demand and pool, exactly per contract.

**What is established is location, not fault:** the aggregate positional composition is
determined by the cross-position comparability of `points − level` in the deep-bench regime,
at the opening board, and by essentially nothing else. That is register **#155**'s reserved
question ("cross-position VOR comparison is the real question") and **FINDING_02**'s mechanism,
now measured on the real universe in production's own quantities instead of the withdrawn
vendor board.

**Whether comparing a 7.4-point tight end favourably against a 75.9-point receiver — for a
bench seat neither will start from — is the right comparison is a design question, and it is
the owner's.** It is not answered by the fact that it produces 32.4%.

## One thing this does NOT explain, stated as open

The cancellation identity says `bpa + displacement_adj = points − displaced`, so mid-draft,
on a filled roster, the level cancels and the decision is `points − displaced`. Yet the final
composition matches the *opening* bpa ranking, where the level does not cancel, to within
three players. Those two facts are compatible — `displaced >= level` always, so the
displacement term can only lower a candidate below his bpa, and the ordering survives if it
lowers each position by a similar amount — **but that compatibility is an inference and has
not been measured.** Recorded as open, not as explanation.

## Two corrections to earlier documents

**1. `CORRECTION_wrong_universe.md` overstates the priced pool.** It says "The real board
carries **1,119 priced rows**. There is no supply shortfall in this league." 1,119 is the
board's ROW count. The **priced** count is **481** — `bpa_source` is `no_priceable_input` on
638 of 1,119. Its corrected pool table (QB 13.9 / RB 22.9 / WR 40.4 / TE 22.9) is the
composition of the ADMITTED rows, not the priced ones, which are QB 8.7 / RB 26.2 / WR 41.2 /
TE 23.9. The "no supply shortfall" conclusion still holds — 481 > 312 — but the margin is
481 against 312 picks, not 1,119 against 312.

**2. `FINDING_05` quotes the withdrawn vendor pool inside its own table.** Its "priced pool
offers" row (QB 14.3 / RB 28.2 / WR 38.9 / TE 18.6) is the 764-row vendor board, explicitly
retracted. Its headline "from a pool that is 18.6% tight end, it allocates 32.4% — 1.74x the
pool's own share" is therefore computed from a withdrawn number. Against the real priced pool
(23.9% TE) the engine's 32.4% is **1.36x**, not 1.74x. CORRECTION_wrong_universe's line
"FINDING_05 is untouched" is true of its engine-vs-human comparison and false of its pool row.

**FINDING_05's stated mechanism is also superseded.** It attributes the excess to TE's
collapsed level making VOR "stay positive for every remaining body". Two things are wrong with
that as stated: the level cancels wherever displacement is non-zero, and the cut here is at
bpa ≈ −142, so the tight ends being taken are overwhelmingly NEGATIVE-bpa, not positive. The
surviving true statement is narrower and does not need positivity: **the same bpa threshold
admits a far weaker raw player at the position with the lowest anchor.**

## Method

`evidence/roster_shape/ff_rulebook/aggregate_selection_probe.py`, run from the repo root with
`PYTHONPATH=.`, raw at `aggregate_selection_raw.json`.

**A fixture error caught by the doctrine, on this probe.** The first run asked for columns
`_points` and `replacement_level` — internal names taken from memory of `draft_room`'s source,
not from the board. `compute_draft_board` emits neither. Both came back null on all 1,119 rows,
which would have read as "no player in this league has a projection." The raw-first rule (#215)
meant nothing was lost, and the probe now prints the emitted column list and raises if the
column it wants is absent. **Do not name a production column from memory; take the row's own
keys.** That is the seventh fixture error of this family in this repo.
