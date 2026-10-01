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

- **6.03 s/pick is the SUM OF SIX SHARD PROCESSES' WALL CLOCKS divided by all 9,336 picks.** The
  v4 candidate's battery ran **three shards concurrently** on a 4-core box, in two phases. The
  sum of per-process wall clock is ~2.9x the elapsed time, and each of those wall clocks was
  itself inflated by the other two shards contending for the box.
- **1.12 s/pick cannot be re-derived from the repository** — the v3 report JSON is gitignored and
  was never committed. What *is* committed about that run states 51 of its 53 arms were
  **carried forward**, which means its `seconds` covers the 2 arms that process actually drafted.

Measured directly, on identical fixtures and run alone on the box, **`eac7491` and HEAD build the
same board in the same time, through the same call counts, function for function.**

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

*Sections 4 (per-pick cost over a full draft, v3 vs v4), 5 (the inherent/accidental split) and 6
(what could not be attributed) land as the serial full-draft A/B completes.*
