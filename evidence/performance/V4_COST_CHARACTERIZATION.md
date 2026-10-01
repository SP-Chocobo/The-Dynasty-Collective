# The 5.4x, measured

**Status: IN PROGRESS.** Provenance and the board-build A/B are measured and stated below. The
serial full-draft A/B is running; this file is updated as each number lands.

## The question

The 53-arm format battery was run at two freezes, same matrix, same 9,336 picks, and recorded
**1.12 s/pick at `v3-freeze` (`eac7491`)** against **6.03 s/pick at the v4 candidate**. A 5.4x
figure, carrying no performance requirement, recorded as a figure. The standing attribution was
to `depth_exposure`'s per-position lineup re-solve (`#139`) and MANDATE 2.6's assignment-based
positional demand — **reasoned, not measured**. This pass measures it.

## Finding, up front

The 5.4x is **not a property of the engine**. The two figures are per-pick rates computed over
**two different quantities**:

1. **1.12 s/pick cannot be re-derived from the repository, and the committed record for that run
   says it was truncated by a resume.** The v3 report JSON is gitignored and was never committed.
   `V2_REPAIRS_BATTERY.md`, describing that exact run, states **51 of its 53 arms were carried
   forward** — so its `seconds` field covers the 2 arms that process actually drafted while its
   `picks` counts all 9,336. The same artifact is recoverable with its numbers intact in
   `v2_acting_now.json`: **0.52 s/pick reported against 2.34 actually measured**, a 4.5x
   understatement from 29 of 36 arms carried forward.
2. **6.03 s/pick is a valid per-pick figure for its run — on a host roughly 2x slower per pick
   than this one.** For the **same arm at the same commit**, the battery's own per-arm record and
   this pass disagree by a near-constant factor: `12T_ppr` 5.638 against 2.798 s/pick (2.02x),
   `CAPTURE_fourth_and_forever` 4.521 against 2.221 (2.04x). Two very different arms, one ratio.
3. **The v3→v4 code change, measured directly, is 0.99x.** On identical fixtures, run alone and
   back to back, across two arms and 480 picks: v3 2.4449 s/pick, v4 2.4225 s/pick. Both commits
   drafted identical trajectories. The board build is identical **call-for-call**.
4. **The two features the 5.4x was attributed to are not in the diff, and cost ~0.1% where they
   are live.** At a round-13 board where `depth_exposure` is `measured` on 3 of 7 candidates and
   `displacement_adj` is non-zero on 7 of 7: `depth_exposure` 0.004 s and
   `displacement_adjustments` 0.006 s of a 7.631 s board.

**So none of the 5.4x is the engine.** It is one unrecoverable, resume-truncated baseline measured
against a figure from a different and slower host.

What the pass *did* find is a genuine accidental cost — present equally at both commits, so not a
regression — worth **25.9% of a warm board**: see §5.

---

## Method, common to every number below

Built to `.claude/skills/engine-measurement`, whose fixture rules are the reason the numbers
below are about the thing in question:

- **`run_draft_battery.build_players_db_from_capture`, NOT `build_players_db`.** The brief for
  this pass named `build_players_db`. That is the **vendor reconstruction** — 764 rows, no
  `injury_status`, no `fantasy_positions` — and the skill names using it the sixth fixture error
  of its class, hard to see because the wrong universe produces a complete, plausible board. The
  battery whose figures are under investigation calls `build_players_db_from_capture`, so that is
  the only population whose cost is the cost in dispute. Both arms report their own `n`.
- **Run from the repo root, never `cd` first.** `DataMerger()` resolves `data/baseline` relative
  to cwd. Probes live under `evidence/performance/probes/` and are invoked
  `PYTHONPATH=.:evidence/performance/probes python3 evidence/performance/probes/<probe>.py` from
  the root. The v3 arm runs from the root **of its own worktree**, which has its own `data/`.
- **`season_projections_from_capture` + `SLEEPER_BASIS_SEASON_SUM`**, and
  **`set_league_format(league_format_hint(league))`** before every format — both because the
  battery passes them and the scoring-aware path is not free.
- **Arms come from `draft_battery.league_matrix(scoring_settings_from_capture())` by label**,
  never hand-built, and pick records carry `{pick_no, round, roster_id, player_id}` because
  `mode="auto"` reads `round`.
- **Both arms of every comparison run ALONE on the box, one after another, never concurrently.**
  The figure under investigation is itself a contention artifact; measuring under contention
  would reproduce it rather than explain it.
- `PYTHONDONTWRITEBYTECODE=1` throughout.

Both trees were verified to present an **identical fixture** before anything was timed:

| | `eac7491` (v3) | HEAD (v4) |
|---|---|---|
| capture | `data/fixtures/sleeper_capture.json`, `2026-09-07T08:14:10Z` | same |
| `n` players in capture | 6,595 | 6,595 |
| `n` players in pool | 6,594 | 6,594 |
| `n` season projections | 5,346 | 5,346 |
| `n` priceable projections | 840 | 840 |
| `n` vendor rankings rows in merger | 774 | 774 |
| matrix | 53 arms, 9,336 picks | 53 arms, 9,336 picks |

**Environment caveat, stated because it bounds every absolute number here and none of the
relative ones.** This container had no Python dependencies installed; the measurements below ran
against **pandas 3.0.6 / numpy 2.4.6 / scipy 1.17.1**, which are almost certainly not the
versions the 1.12 and 6.03 figures were produced under, and `data/projections/` is empty in both
trees (no paid vendor CSVs), so the merger carries the 774-row committed baseline only. Absolute
seconds here are therefore **not comparable** to the historical figures. Every v3-vs-v4 claim is a
comparison of two arms measured minutes apart in the same container against the same data, which
is the only comparison this pass makes.

---

## 1. Where 6.03 comes from — arithmetic over committed artifacts

Probe: `probes/figure_provenance.py`. No engine runs; it reads the six shard reports the v4
battery force-added under `evidence/batteries/shards/` and recomputes each report's own rates.

`run_draft_battery._battery_report` sets `"seconds": round(time.time() - started, 1)` — **one
process's wall clock for its own arm loop** — and `"picks": sum(r["picks"] for r in results)`.

| shard | arms | picks | report wall clock (s) | sum of arm seconds (s) | s/pick |
|---|---:|---:|---:|---:|---:|
| `shard_0.json` | 12 | 2,116 | 10,855.3 | 10,855.4 | 5.13 |
| `shard_0b.json` | 6 | 1,152 | 8,464.1 | 8,464.0 | 7.35 |
| `shard_1.json` | 11 | 1,828 | 10,391.5 | 10,391.4 | 5.68 |
| `shard_1b.json` | 7 | 1,260 | 8,416.2 | 8,416.2 | 6.68 |
| `shard_2.json` | 11 | 1,912 | 10,600.1 | 10,600.0 | 5.54 |
| `shard_2b.json` | 6 | 1,068 | 7,570.7 | 7,570.7 | 7.09 |
| **sum** | **53** | **9,336** | **56,297.9** | **56,297.7** | **6.030** |

`n_shard_files=6`, `n_arms=53`, `n_picks=9336`. **56,297.9 / 9,336 = 6.030 s/pick** — the figure,
reproduced exactly. `BATTERY_REPORT.json`'s own `seconds` field reads **56,297.7**.

The six files are **three shards in two phases** (`shard_N` then `shard_Nb`). Taking each phase's
three shards as concurrent:

```
elapsed = max(phase a) + max(phase b) = 10855.3 + 8464.1 = 19,319.4 s
19,319.4 / 9,336 picks = 2.069 s/pick of ELAPSED time
ratio sum-of-process-wall-clock : elapsed = 2.91x
```

So 6.03 is not a rate of anything a single draft experiences. It is **three processes' wall
clocks added together**, each already slowed by the other two. Measured as elapsed time, the v4
candidate's battery ran at **2.07 s/pick**, which is **faster per pick than every serial battery
in the committed record**:

| committed report | arms | picks | report s | sum arm s | s/pick (report) | s/pick (arms) | arms carried fwd |
|---|---:|---:|---:|---:|---:|---:|---:|
| `BATTERY_2026-09-08_baseline_vendor_only_1e869ce` | 33 | 5,340 | 14,081.2 | 14,081.5 | 2.64 | 2.64 | 0 |
| `BATTERY_2026-09-08_scoring_aware_5a53057` | 33 | 5,340 | 14,512.3 | 14,512.4 | 2.72 | 2.72 | 0 |
| `BATTERY_2026-09-12_scoring_aware_full_99f9f76` | 33 | 5,340 | 23,556.4 | 23,555.9 | 4.41 | 4.41 | 0 |
| `BATTERY_2026-09-13_gate1_1770ef2` | 34 | 5,652 | 19,220.8 | 19,857.6 | 3.40 | 3.51 | 2 |
| `BATTERY_2026-09-17_gate1_15fcf2c` | 34 | 5,652 | 14,460.7 | 14,460.7 | 2.56 | 2.56 | 0 |
| `SMOKE_capture_ff` | 1 | 312 | 1,109.1 | 1,109.1 | 3.56 | 3.56 | 0 |
| `v2_acting_now` | 36 | 6,144 | 3,222.3 | 14,404.2 | **0.52** | **2.34** | **29** |
| `v2_pace_wired` | 24 | 3,828 | 8,842.4 | 8,841.9 | 2.31 | 2.31 | 0 |

`n_committed_reports=8`, `n_with_no_carried_forward_arms=6`. Across those six: **min 2.31, median
2.72, max 4.41 s/pick**. Neither 1.12 nor 6.03 is inside that range, in either direction.

### 1b. What summing concurrent shards does to the rate — measured, and it is not what I first assumed

Adding three concurrent processes' wall clocks *looks* like triple-counting, and an earlier draft
of this document said so. **It is not, and the probe that says so is
`probes/contention_factor.py`.** Each shard's wall clock covers only *its own* picks, so
`sum(wall clocks) / sum(picks)` is a weighted mean of the processes' per-pick costs — a
**process-time** rate, which is the same quantity a serial run's `seconds/picks` reports.

The same arm, run alone and then as three identical concurrent processes on this 4-core box —
first at **24 picks** per process:

```
n_cores=4   arm=12T_ppr   n_picks_per_process=24
ALONE        wall clocks [51.19]                  51.2s   2.133 s/pick
CONCURRENT   wall clocks [50.72, 50.72, 50.72]    50.7s   2.113 s/pick   n=3
CONTENTION FACTOR (per process) = 0.99x
sum of the 3 wall clocks = 152.2s over 72 picks = 2.113 s/pick
elapsed for the same 72 picks = 50.7s = 0.704 s/pick
```

Repeated at a scale where the mid-round picks (the expensive population) dominate rather than
the cheap opening ones, **84 picks per process**:

```
ALONE        wall clocks [219.81]                     219.8s   2.617 s/pick
CONCURRENT   wall clocks [216.85, 218.21, 218.21]     218.2s   2.592 s/pick   n=3
CONTENTION FACTOR (per process) = 0.99x
sum of the 3 wall clocks = 653.3s over 252 picks = 2.592 s/pick
elapsed for the same 252 picks = 218.2s = 0.866 s/pick
```

**The same 0.99x at both scales.** Each draft process is single-threaded (observed at 100–101%
CPU), so three of them on four cores do not compete.

**Three concurrent single-threaded processes on four cores cost each other nothing (0.99x).** So
6.03 is not inflated by the sharding, in either direction: it is what each shard process really
spent per pick. The elapsed-time rate (2.07 s/pick over ~19,319 s) answers a different question —
*how long did the battery take* — and the two should not be compared across a serial run and a
sharded one without saying which is which.

This correction matters for the conclusion: **the v4 side of the 5.4x is sound arithmetic. The v3
side is the broken one.**

### 2. Where 1.12 probably comes from — and why "probably" is the honest word

**The v3-freeze 53-arm report JSON is not in the repository.** `BATTERY_REPORT.json` is
gitignored, and only the v4 candidate's shards were ever force-added. So 1.12 **cannot be
re-derived**, and this pass does not claim to have reproduced it.

What is committed is `evidence/batteries/V2_REPAIRS_BATTERY.md`, describing that exact run — 53
arms, 9,336 picks, complete. It records **"2920.2s of drafting"** (= **0.313 s/pick**) and states
its own provenance plainly:

> 51 arms were drafted at `360f6ba` [...] and are carried forward. The container was recycled at
> 51 arms and the run resumed, so the last 2 arms were drafted at `6ea4f5b`.
> `carried_forward: 51 True, 2 False`

With `--resume`, `started` is reset to the resumed process's start, so `report["seconds"]` covers
**only the arms that process drafted** while `picks` counts all 53. **`v2_acting_now` is the same
artifact with its numbers intact and both rates recoverable: 0.52 s/pick reported against 2.34
s/pick actually measured, a 4.5x understatement from 29 of 36 arms carried forward.**

So the v3 side of the 5.4x is a figure from a report whose `seconds` field is known to have been
truncated by a resume. Whether 1.12 is that report's `seconds/picks`, its `sum(arm
seconds)/picks`, or a third derivation **cannot be settled from the repository** and is recorded
below as unattributed.

---

## 3. The board build, v3 against v4 — measured, not reasoned

### 3a. The engine diff contains no new board-path computation

`git diff eac7491 HEAD` touches **three engine modules, 146 insertions, 20 deletions**:

| module | what changed | board-path cost |
|---|---|---|
| `lineup_optimizer.py` | one basis **label** string (`EXPOSURE_ROSTER_PARTIAL` wording) | none |
| `draft_room.py` | `health_penalty` returns `0.0` instead of `NaN`; a `roster_id is None` guard in `team_slots_filled`; `feasibility_first` reads eligibility (B-F4) | B-F4 only, already measured at 1.78ms vs 0.36ms per 900-row board |
| `pick_synthesis.py` | `ABSENT_FIGURE` check in `presentable_text`; `team_count`/`round_of` consolidation; `eligible_positions` on `CandidateSnapshot` (one dict lookup per candidate) | one dict lookup × ~48 candidates |

**Neither `depth_exposure` nor MANDATE 2.6 appears in this diff.** `lineup_optimizer.depth_exposure`
changed only a label string, and its `draft_room` call site is unchanged — it already ran, in the
same place and the same way, at `eac7491`. MANDATE 2.6 predates the tag: HEAD's own B-F4 comment
describes it in the past tense ("The roster side was moved to eligibility at MANDATE 2.6 and the
candidate side was not"). **The standing attribution names two features that are identical on both
sides of the comparison.**

Also worth stating: `depth_exposure` is computed **once per board, per position** —
`draft_room.py:4790`, beside the roster it reads, outside `score_row` — not per candidate row.

### 3b. Both commits build the same board in the same time

Probe: `probes/profile_draft.py`, arm `12T_ppr`, opening board, one process each, run
sequentially and alone.

| | v3 (`eac7491`) | v4 (HEAD) |
|---|---:|---:|
| opening board, unprofiled | **11.410 s** | **11.324 s** |
| opening board, under `cProfile` | 34.580 s | 34.126 s |
| `n_candidates` | 48 | 48 |

HEAD is **0.8% faster** unprofiled and 1.3% faster profiled — noise, and in the wrong direction
for a regression.

### 3c. The two profiles are identical call-for-call

`cProfile` cumulative time, same arm, same state. Every hot function has the **same number of
calls on both sides**:

| function | v3 cumul (s) | v4 cumul (s) | `ncalls` v3 | `ncalls` v4 |
|---|---:|---:|---:|---:|
| `pick_synthesis.build_snapshot` | 34.579 | 34.125 | 1 | 1 |
| `draft_room.compute_draft_board` | 34.381 | 33.931 | **13** | **13** |
| `draft_room.build_available_pool` | 22.362 | 22.182 | **14** | **14** |
| `draft_room._merge_across_eligibility` | 21.143 | 21.009 | 56,546 | 56,546 |
| `data_merger.merge_player` | 21.033 | 20.904 | 56,742 | 56,742 |
| `data_merger._resolve` | 20.828 | 20.708 | 3,980 | 3,980 |
| `difflib.get_close_matches` | 12.119 | 12.196 | 3,376 | 3,376 |
| `draft_strategy.pick_analysis` | 12.307 | 11.984 | 1 | 1 |
| `draft_strategy._build_opponent_boards` | 11.222 | 10.859 | 1 | 1 |
| `difflib.quick_ratio` | 6.679 | 6.809 | 1,030,451 | 1,030,451 |
| `draft_room.score_row` | — | 3.534 | 12,610 | 12,610 |

A regression that changes no call count and no cumulative time on any hot function is not a
regression in this code path. **This retires the engine as the explanation for the board build.**

---

## 4. The whole draft, v3 against v4 — the quantity actually in dispute

A board build is not a per-pick cost: `DataMerger.merge_player` is memoized per merger instance,
so the first board of an arm pays a cold name resolution every later board gets free. The 1.12
and 6.03 figures are both per-pick rates over whole arms, so this is measured the same way.

Probe: `probes/draft_cost_curve.py`, arm **`12T_ppr`** (12 teams, 14 rounds, 168 picks) taken
from the battery's own matrix by label. The two arms ran **back to back, alone on the box**, one
process each, 03:25:45→03:33:36 then 03:33:36→03:41:25 UTC. Every pick is timed by wrapping the
production `pick_synthesis.build_snapshot`, never by reconstructing what it ought to cost.

| | v3 (`eac7491`) | v4 (HEAD) | v4 / v3 |
|---|---:|---:|---:|
| `n` picks | 168 | 168 | — |
| total seconds | **467.1** | **470.0** | — |
| **s/pick** | **2.7804** | **2.7976** | **1.0062x** |
| first board (cold merge memo) | 11.404 | 11.001 | 0.96x |
| `n` warm picks | 167 | 167 | — |
| warm mean | 2.7285 | 2.7481 | 1.007x |
| warm median | 2.706 | 2.667 | 0.986x |
| warm min / max | 0.712 / 5.370 | 0.716 / 5.483 | — |
| first-quarter mean | 2.906 | 2.906 | 1.000x |
| last-quarter mean | 2.180 | 2.212 | 1.015x |

**The measured v3→v4 change is 1.0062x — 0.6%. The figure under investigation is 5.4x.**

Paired per-pick comparison, `n_paired_warm_picks=167`:

```
picks where v4 is slower than v3      104 / 167  (62.3%)
paired delta (v4 - v3)  mean  +0.0196 s/pick
                        median +0.0243 s/pick
                        stdev   0.0994 s/pick
```

On this arm alone that reads like a small real regression of +0.020 s/pick. **It is not, and the
second arm is what says so** — see §4b. The sign flips.

**Both commits drafted the identical trajectory** — `n_picks_differing = 0 of 168`. That is worth
stating because `health_penalty` returning `0.0` instead of `NaN` is a behaviour change in this
diff; on this arm it moved no pick, so the timing comparison is between two runs doing the same
work, not two different drafts.

### 4b. A second arm, and why one arm was not enough

Scale and shape matter, so the longest arm in the matrix was run the same way:
**`CAPTURE_fourth_and_forever`**, 12 teams, 26 rounds, **312 picks** — a startup draft, the arm
the skill's budget table costs at ~887 s.

| | v3 (`eac7491`) | v4 (HEAD) | v4 / v3 |
|---|---:|---:|---:|
| `n` picks | 312 | 312 | — |
| total seconds | **706.4** | **692.8** | — |
| **s/pick** | **2.2642** | **2.2206** | **0.9807x** |
| warm mean | 2.2355 | 2.1926 | — |
| warm median | 2.038 | 1.998 | — |
| last-quarter mean | 1.351 | 1.308 | — |
| `n` picks differing | — | **0 of 312** | — |

Paired over 311 warm picks the delta is **mean −0.0430 s, median −0.0295 s, stdev 0.1086 s**, and
v4 is slower on only **92 of 311**.

**The sign flips between the two arms** — `12T_ppr` +0.7%, `CAPTURE_fourth_and_forever` −1.9%.
That is the finding, and it is why one arm would have been a trap: a consistent-looking per-pick
bias on a single arm became noise the moment a second arm was measured. The right statement is
that the v3→v4 delta is **inside ±2% with no stable sign — below this instrument's resolution**.

Combined, the honest denominator:

| | `n` picks | total s | s/pick |
|---|---:|---:|---:|
| v3 (`eac7491`) | 480 | 1,173.6 | **2.4449** |
| v4 (HEAD) | 480 | 1,162.8 | **2.4225** |
| **v4 / v3** | | | **0.9908** |

**0.99x, against a figure of 5.38x.** Both arms drafted bit-identical trajectories at both
commits (0 of 168 and 0 of 312).

### 4c. The battery's own per-arm record, against this pass, for the same arm at the same commit

The shard reports record `seconds` per arm. That makes a direct comparison possible, and it is the
one that locates the 5.4x:

| arm | `n` picks | battery (v4 cand.) | this pass, HEAD | this pass, `eac7491` | battery / this pass |
|---|---:|---:|---:|---:|---:|
| `12T_ppr` | 168 | 947.2 s = **5.638** s/pick | 470.0 s = **2.798** | 467.1 s = **2.780** | **2.02x** |
| `CAPTURE_fourth_and_forever` | 312 | 1,410.7 s = **4.521** s/pick | 692.8 s = **2.221** | 706.4 s = **2.264** | **2.04x** |

**Same code, same arm, same fixture, a near-constant 2.0x apart on two arms whose own per-pick
costs differ by 25%.** A uniform ratio across different workloads is the signature of a host
factor, not a code factor and not an arm-mix factor. The battery's box spent about twice as long
per pick as this container does, and `probes/contention_factor.py` rules out the sharding as the
cause of that on a 4-core box — 0.99x at both 24 and 84 picks per process (§1b).

Spread across the matrix, from the battery's own record (`n_arms=53`): per-arm cost ranges
**4.258 s/pick** (`8T_ppr_SF`) to **9.344 s/pick** (`CAPTURE_owner_league_balanced_full`), a 2.2x
spread at the same commit on the same host. The two arms measured here sit at the cheap end of
that distribution, which is why a 53-arm mean is not reconstructible from them (§6).

### What a pick actually costs, and why the spread is bimodal

Of v4's 167 warm picks: **43 cost under 1.5 s (mean 1.011 s)** and **124 cost 1.5 s or more
(mean 3.351 s)**. The split is structural, not noise. `draft_strategy._build_opponent_boards`
runs one `compute_draft_board` per unique roster_id — 12 extra boards — and the survival,
forfeit and rival-premium machinery that needs them is computed over the picks between this turn
and MY NEXT ONE. At a snake turn boundary a seat picks twice in a row, the gap ahead is zero, and
that whole apparatus short-circuits. **The cheap picks are the turn-boundary ones.** A per-pick
average over an arm is therefore an average over two populations, and the mix depends on team
count and round count — which is one reason per-arm cost varies 5x at the same pick count.

---

## 5. Where the time goes in one pick — and the inherent/accidental split

### 5a. The state these numbers are taken at, and why not the opening board

An opening board is the one state where the attributed terms **cannot** cost anything:
`depth_exposure` is only `measured` once a bench exists (round 9) and `displacement_adj` is
identically 0.00 on every priced row of a board built with an empty roster. Timing them there
would be the "rate of exactly zero over an unreachable predicate" error.

So the attribution below is taken at **round 13 of 14**, pick `13.07`, replayed from the real
`12T_ppr` trajectory (`probes/profile_middraft.py`, 150 picks replayed,
`n_replayed_ids_not_in_pool = 0`). At that state, confirmed from the snapshot itself:

```
n_candidates=7   depth_basis_measured=3 (of 7)   displacement_nonzero=7 (of 7)
```

**Both attributed terms are live.** The same trajectory file is used for both commits, so both
price the identical board.

And the board is profiled **warm** (`--warm`): one throwaway build first, so the profiled build
sees `DataMerger._merge_memo` the way picks 2…168 of an arm see it. A single cold board attributes
~21 s to `_resolve`/`difflib` that no pick but the first ever pays — the figure that would have
been reported had this been profiled once in a fresh process.

### 5b. The table

Warm round-13 board, `cProfile` cumulative, **both commits**. cProfile inflates call-heavy code,
so shares are given from the profile and the absolute saving from the unprofiled ablation:

| component | v3 cumul | v4 cumul | % of board | `ncalls` | verdict |
|---|---:|---:|---:|---:|---|
| `pick_synthesis.build_snapshot` (whole pick) | 7.534 | 7.631 | 100% | 1 | — |
| `draft_room.compute_draft_board` | 7.396 | 7.491 | 98.2% | **7** | — |
| └ `draft_strategy.pick_analysis` | 6.389 | 6.397 | 83.8% | 1 | inherent |
| &nbsp;&nbsp;&nbsp;└ `_build_opponent_boards` | 5.311 | 5.291 | **69.3%** | 1 (→6 boards) | **inherent** |
| `draft_room.anchor_cache_key` | 2.842 | 2.859 | 37.5% | 21 | mixed |
| └ **`_players_db_fingerprint`** | 2.300 | 2.308 | **30.2%** | **22** | **ACCIDENTAL** |
| `draft_room.roster_points_lookup` | 1.887 | 1.910 | 25.0% | 14 | unattributed |
| `draft_room.score_row` | 1.614 | 1.654 | 21.7% | 5,740 | inherent |
| **`draft_room.build_available_pool`** | 0.614 | 0.592 | **7.8%** | **7** (1 distinct) | **ACCIDENTAL** |
| `draft_room.replacement_levels` | 0.287 | 0.282 | 3.7% | 14 | inherent |
| `draft_room.estimated_bench_demand` | 0.040 | 0.041 | 0.5% | 7 | inherent |
| `data_merger.merge_player` | 0.033 | 0.033 | 0.4% | 29,505 | inherent (memo hits) |
| `lineup_optimizer.slot_coverage` | 0.023 | 0.024 | 0.3% | 348 | inherent |
| `lineup_optimizer.displacement_level` | 0.007 | 0.007 | 0.1% | 35 | inherent |
| `draft_room.displacement_adjustments` | 0.006 | 0.006 | **0.08%** | 7 | inherent |
| **`lineup_optimizer.depth_exposure`** | 0.004 | 0.004 | **0.05%** | 7 | **inherent** |
| `draft_room.feasibility_first` (B-F4) | 0.002 | 0.002 | 0.03% | 7 | inherent |
| `scipy linear_sum_assignment` | 0.002 | 0.002 | 0.03% | 488 | inherent |
| `draft_strategy.estimate_survival` | 0.001 | 0.001 | 0.01% | 7 | inherent |

### 5c. INHERENT — real work for features that were deliberately added

**Record these so nobody rediscovers them as a mystery.**

1. **`_build_opponent_boards` — one full `compute_draft_board` per rival, 69.3% of a pick.**
   `draft_strategy.py:792`. A snapshot builds **13 boards on an opening pick** (mine + one per
   unique roster_id in a 12-team league) and 7 at round 13, where the gap ahead is shorter. This
   is survival, positional forfeit and rival premium — each needs *that* roster's own board,
   priced the same way mine is (#214/F2). It has **already been optimised once**: its docstring
   records that it replaced per-pick-position, per-candidate recomputation and is now shared by
   every caller in one analysis pass. **Nothing to fix. This is the dominant cost of the engine
   and it is the feature working.**

2. **The bimodal per-pick cost is this feature, seen from outside.** Of v4's 167 warm picks on
   `12T_ppr`, **43 cost under 1.5 s (mean 1.011 s) and 124 cost ≥1.5 s (mean 3.351 s)**. At a
   snake turn boundary a seat picks twice running, the gap ahead is zero, and the whole
   opponent-board apparatus short-circuits. A per-pick average over an arm is an average over two
   populations whose mix depends on team count and round count — **which is a sufficient
   explanation for "per-arm cost varies 5x at the same pick count" without any defect.**

3. **The cold `_merge_memo` fill — ~9–11 s once per arm.** 3,980 `DataMerger._resolve` calls, of
   which 3,376 reach `difflib.get_close_matches` (1,030,451 `quick_ratio` + 2,613,024
   `real_quick_ratio`). `merge_player` is **already memoized** and gets a 93.0% hit rate
   (56,742 calls, 3,980 distinct). The memo must be refilled per format because
   `set_league_format` selects a different rankings export. **Already fixed; the residue is the
   one unavoidable fill.** Over a 168-pick arm it is ~2% of the arm.

4. **`depth_exposure` (#139) and MANDATE 2.6's assignment-based demand — the attributed culprits —
   are 0.05% and ~0.5%.** `depth_exposure` is **0.004 s of a 7.631 s board**, measured at a state
   where it is `measured` on 3 of 7 candidates. All 488 `scipy.linear_sum_assignment` calls in a
   board total **0.002 s**. And `depth_exposure` is computed **once per position per board**
   (`draft_room.py:4790`, beside the roster it reads, outside `score_row`) — not per candidate
   row, which is what "per-position lineup re-solve" invites a reader to assume. **Inherent,
   deliberate, and far too small to appear in any per-pick figure.**

### 5d. ACCIDENTAL — and present *identically* at both commits, so not a regression

Both are **standing** costs, not v4 costs. They are worth recording before a freeze because they
are cheap to fix and cost nothing in behaviour — **and they are deliberately not fixed here.**

#### A1. `_players_db_fingerprint` recomputes the whole-universe hash 22 times per pick

- **Call site:** `draft_room.py:3120` `_players_db_fingerprint`, reached from
  `anchor_cache_key` (`draft_room.py:3189`) — which **every board calls twice**, once for
  `_points` and once for `trade_value` — plus `snapshot_input_key`. **22 calls at round 13, 27 on
  an opening board.**
- **What it does each time:** hashes every field of all **6,594** player rows. Per board that is
  **145,090 outer generator calls, 1,450,680 `_canonical_player_value` calls and 290,136
  `str.join` calls**.
- **Why it is accidental:** it is a pure function of `players_db`, and `players_db` is read-only
  for the life of a draft — `simulate_full_draft`'s own docstring: *"Reads merger/players_db/league
  only; never mutates them."* The same hash is recomputed 21 redundant times for one answer.
- **Its own docstring costs it as one call.** It measures "a median 30.5 ms over five runs" and
  weighs that against "a snapshot key that cost 60 ms in total, against a board build of 870 ms
  warm", concluding "~3% of the warm case". **That reasoning is right and the call count is 22.**
  The design decision (hash everything rather than maintain a field list) is correct and is not
  what is being questioned; only the number of times the answer is recomputed.
- **Measured saving (in-process ablation, unprofiled, `n=3` per arm, round-13 board):**

  | | v3 (`eac7491`) | v4 (HEAD) |
  |---|---:|---:|
  | baseline, warm | 2.766 s | 2.770 s |
  | fingerprint memoized | 2.194 s | 2.195 s |
  | **saving** | **0.572 s (20.7%)** | **0.575 s (20.7%)** |

  With the memo on, `fp_calls=22` and `fp_computes=1`.
- **Behaviour:** `n_distinct_top5_across_13_builds = 1`, `n_distinct_candidate_counts = 1`. The
  ablation is a **no-op in output**, which is what makes the timing comparison legitimate rather
  than "disabling it made it faster".
- **Proposed fix — NOT IMPLEMENTED:** memoize `_players_db_fingerprint` on the identity of its
  argument (or compute it once in `build_snapshot` and pass it down to `anchor_cache_key` and
  `snapshot_input_key`). An identity key is sound precisely because the mapping is never mutated
  during a draft; if that is thought too strong a bet, a one-entry cache keyed on
  `(id(players_db), len(players_db))` is strictly cheaper than 22 full hashes and no weaker than
  the current key's own assumptions. **Either way, it changes no answer — the cache key is
  identical, it is simply computed once.**

#### A2. `build_available_pool` rebuilds the identical pool once per board

- **Call site:** `draft_room.py:1622` `build_available_pool`, called from `compute_draft_board`
  (`draft_room.py:4190`) — once per board, and a snapshot builds 13 boards (7 at round 13).
- **Measured repeat (`probes/repeat_work.py`, keyed on arguments, never on call order):**

  ```
  build_available_pool: n_calls=14  n_distinct_arg_tuples=1  n_repeat_calls=13
                        repeat_share=92.9%  max_calls_for_one_tuple=14
    x14  ((), ('QB','RB','TE','WR'), 'all', 'season_sum')
  ```
- **Why it is accidental:** the pool's contents are a function of `(drafted_player_ids,
  usable_positions, pool_scope, sleeper_basis)` and the loaded projections. **`my_roster_id` is
  not among them** — it steers the scoring that happens *after* the pool exists. All 13 boards in
  one snapshot therefore ask for the same pool.
- **Measured saving (same ablation, `n=3`):** **0.177 s (6.4%) at v3, 0.200 s (7.2%) at v4.** This
  is a **lower bound**: the ablation returns a `.copy()` of the cached frame on all 13 repeats,
  because callers own what they receive, so the copy cost is still paid.
- **Proposed fix — NOT IMPLEMENTED:** build the pool once per snapshot, above the
  opponent-board loop, and pass it in; or memoize on the key above for the life of one snapshot.
  The `.copy()` question (which callers mutate their frame) is the only real design work.

#### The two together

| | v3 (`eac7491`) | v4 (HEAD) |
|---|---:|---:|
| baseline, warm round-13 board | 2.766 s | 2.770 s |
| both memoized | 2.048 s | 2.052 s |
| **saving** | **0.718 s — 25.9%** | **0.718 s — 25.9%** |

**25.9% of a warm pick, identical at both commits, with a bit-identical board on all 13 builds.**
On the opening board (largest pool, so the pool share is at its upper bound) the same ablation
reads 23.5%.

**Not implemented, deliberately.** A performance change landing unreviewed during a freeze is
exactly what this project's process exists to prevent, and neither of these is a defect — no
answer is wrong, nothing is mis-measured, and there is no stated performance requirement for them
to violate. They are register items for after the freeze.

---

## 6. What could not be attributed — stated as unattributed, not guessed

1. **The exact derivation of 1.12 s/pick. Unrecoverable.** `BATTERY_REPORT.json` is gitignored and
   the v3-freeze 53-arm report was never committed; only the v4 candidate's shards were
   force-added. Whether 1.12 is that report's `seconds/picks`, its `sum(arm seconds)/picks`, or a
   third derivation cannot be settled from this repository. What *is* committed — 51 of 53 arms
   carried forward, and 2920.2 s recorded for all 9,336 picks (0.313 s/pick) — says the figure
   came from a resume-truncated `seconds` field, but **this pass did not reproduce 1.12 and does
   not claim to.**

2. **The cause of the 2.0x host factor.** Measured as a ratio, twice, on two arms (2.02x, 2.04x).
   **The cause is not established.** Candidates not investigated: CPU model, effective core count
   on that container, pandas/numpy version, or unrelated load on the host. Settling it needs the
   battery's own host, which this session does not have. It is a *measured* factor with an
   *unattributed* cause.

3. **A 53-arm mean on this box.** Not measured — the brief rules out re-running the battery, and
   rightly. The battery's own per-arm record spans **4.258 to 9.344 s/pick** at one commit on one
   host, and the two arms measured here sit near the cheap end. So **the 53-arm figure cannot be
   reconstructed from two arms**, and no attempt is made to divide 6.03 by anything to produce
   one. What is established is the v3→v4 ratio on matched arms (0.99x), which is the quantity the
   5.4x claims to be about.

4. **~74% of a warm pick beyond the two accidental repeats.** Attributed *by function* in §5b but
   **not ablated**, so its reducibility is unknown. The two largest unexamined pieces are
   `roster_points_lookup` (25.0%, 14 calls) and the non-fingerprint remainder of
   `anchor_cache_key` (37.5% total, 30.2% of which is the fingerprint). Neither was tested for
   repeat structure. Calling them inherent would be a guess; they are listed as unattributed.

5. **Whether `health_penalty`'s `NaN` → `0.0` change moves any trajectory.** It is a behaviour
   change in this diff and it moved **0 of 480 picks** across the two arms measured. That is
   evidence for these two arms, not a general result — in particular, the rows it reaches are
   trade-value-priced rows with no projection, and an arm that drafts more of them could differ.

6. **Absolute seconds are not comparable to the historical record.** This container had no Python
   dependencies installed; everything here ran against **pandas 3.0.6 / numpy 2.4.6 / scipy
   1.17.1**, and `data/projections/` is empty in both trees so the merger carries only the
   774-row committed baseline. Every v3-vs-v4 claim is a ratio between two arms measured minutes
   apart in one container against identical data, which is sound. **No absolute figure here
   should be quoted against a number from another host or another dependency set** — which is,
   recursively, the whole lesson of this pass.

---

## 7. The one-line answer

> The 5.4x is not in the engine. Measured on matched arms, run alone and back to back,
> `eac7491` → HEAD is **0.99x over 480 picks**, with bit-identical trajectories and a board build
> that is identical call-for-call. The v3 baseline of 1.12 s/pick came from a report whose
> `seconds` field covered 2 of its 53 arms, and the 6.03 s/pick figure came from a host that
> spends **2.0x longer per pick than this one on the same arm at the same commit**. The two
> features the slowdown was attributed to, `depth_exposure` and MANDATE 2.6's demand, are **not in
> the diff at all** and cost **0.004 s and 0.006 s of a 7.6 s board** at a state where both are
> live.
>
> Separately, and at **both** commits equally: **25.9% of every warm pick** is two computations
> repeated for one answer — the whole-universe hash recomputed 22 times (20.7%) and the available
> pool rebuilt once per rival board (7.2%). Not a regression, not a defect, not fixed here.

## Reproducing any number above

```bash
# from the repo root, ALONE on the box, one at a time
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:evidence/performance/probes \
  python3 evidence/performance/probes/<probe>.py ...

figure_provenance.py                                  # §1, §2 -- arithmetic, no engine run
profile_draft.py      12T_ppr <tag> --board-only [--profile]      # §3
draft_cost_curve.py   12T_ppr <tag> [--picks N]                   # §4
repeat_work.py        12T_ppr <tag>                               # §5d call counts
profile_middraft.py   12T_ppr <tag> <CURVE_v4_12T_ppr.json> 150 --warm   # §5b
ablate_repeats.py     12T_ppr <tag> <CURVE_v4_12T_ppr.json> 150   # §5d savings
contention_factor.py  12T_ppr 24 3                                # §1b
```

The v3 arm of every comparison runs the same probe from the root of a
`git worktree add --detach eac7491` checkout, which has its own `data/`.
