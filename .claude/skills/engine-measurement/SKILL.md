---
name: engine-measurement
description: Stand up a correct real-data measurement against the CDME engine — boards, drafts, batteries, before/after comparisons. Use before writing ANY probe, ablation, A/B, or instrument that reads draft_room / pick_synthesis / draft_battery output, and before claiming any measured result. Encodes the fixture setup that six separate measurement errors in this repo came from getting wrong.
---

# Measuring this engine without fooling yourself

Every measurement error made during the #150 battery pass was a FIXTURE error, not a reasoning
error. The reasoning was checkable; the harness silently produced numbers about the wrong thing.
This file is the checklist that would have caught them.

**The failure mode to fear is not a crash. It is a plausible number about something else.**

## The five-line fixture, and why each line is there

```python
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

merger = dm.DataMerger()                                  # 1. from the REPO ROOT
players_db = rdb.build_players_db(merger)                 # 2. full pool, IDP included
merger.set_league_format(db.league_format_hint(league))   # 3. NEVER SKIP THIS
```

1. **Run from the repo root. Never `cd` first.** `DataMerger()` resolves its baseline paths
   relative to the working directory. Backgrounding a probe with a `cd` into the scratchpad
   produced an empty frame and `KeyError: 'position'` — the merger loaded nothing and said so
   only by crashing three calls later. Put the probe file wherever you like; run it from root.

2. **`rdb.build_players_db`, not a hand-rolled loop.** It reconstructs every baseline player
   Sleeper-shaped, including IDP. A hand-rolled `("QB","RB","WR","TE")` loop silently excludes
   IDP and makes any IDP-format claim vacuous.

3. **`set_league_format` before every format you draft.** THIS IS THE BIG ONE. `rec` and
   `bonus_rec_te` do NOT propagate through `scoring_settings` into offensive valuation — Draft
   Sharks' season projection is a static pre-computed number. They propagate by FILE SELECTION:
   `set_league_format` picks a different rankings export. `app.py` calls it every rerun.
   A battery that never called it drafted all 32 formats from one export, and standard /
   half_ppr / ppr came back **byte-identical**. Nine of thirteen "findings" were artifacts.
   Derive the hint from the league's own settings (`db.league_format_hint`) rather than
   carrying it alongside — a hint that can disagree with its league is a second source of truth.

## Picking a turn to measure

`positional_forfeit`, `survival_probability` and `rival_premium` are all computed over the picks
between this turn and MY NEXT ONE. **The gap that matters is the one AHEAD.**

```python
nxt = next((j for j in range(i + 1, len(pick_order)) if pick_order[j] == me), None)
if nxt is not None and nxt - i > 1:   # real intervening picks
```

Filtering on the gap BEHIND is the same artifact mirrored: it rejects the round-opening turns
that carry ~22 intervening picks and keeps the round-closing ones that carry none. Measured the
wrong way round once: `rival_premium` was **0.00 for 269 of 269 candidates** and the run looked
like a clean null result.

Also: the board state must match the turn. Build `picks` from `opening[:index]` where `index` is
the turn being analysed — not from a round boundary chosen separately.

## Before/after comparisons

**Both arms must run the same code.** The only honest A/B is one process, one code version,
toggling the single thing under test:

```python
real = dr.feasibility_first
dr.feasibility_first = lambda scored, *a, **k: pd.Series(1, index=scored.index, dtype=int)
```

**Never compare a fresh run against a saved baseline from different code.** Tier 3 was reported
as fixing a format 2 findings -> 0; the 2 came from a run predating the scoring repair, and the
improvement was the scoring repair. Save the baseline JSON and record WHICH COMMIT produced it.

## Absence, in your own instrument

`if value:` conflates `None` (never computed) with `0.0` (measured zero). This engine forbids
that everywhere, and a reporting function broke it: an upside pick that legitimately measured
`growth_signal == 0.0` was counted as "no growth measured". Count `is not None` and `> 0`
**separately**, always.

## Runtime budgets — set timeouts from these, not from hope

| what | cost |
|---|---|
| one board build | ~0.3-1.4s |
| full test suite | **~800-870s** (2100+ tests) |
| one 12-team draft (168 picks) | ~300s |
| full 32-format battery | **~2.9 hours** |

A `timeout 580` on the suite kills it mid-run and tells you nothing. Background anything over a
couple of minutes and read the file.

## Two shell hazards that cost real cycles

- **`pkill -f "run_draft_battery"` matches its own launching shell.** The `bash -c` wrapper
  contains the pattern, so it kills the job it is starting. Use a character class that does not
  match itself: `pkill -f "run_draft_batter[y]"`.
- **`unittest` buffers to a file.** `2>&1 | tail -N` discards the failure body. Redirect the
  whole run to a file and grep it: `> suite.txt 2>&1`, then `grep -n "^FAIL:" -A 25 suite.txt`.

## Before you report a number

- Is the population non-vacuous? Print `n`. A rate over an empty set is not a rate.
- Did the thing under test actually fire? If ON and OFF are identical, it did not — find out why
  before concluding it had no effect. (`narrow_candidates` re-sorts every board through its own
  `_board_order` key, so a decision expressed only as ROW ORDER is discarded before the pick.)
- Could this number be about a different question than the one asked? Say what would have to be
  true for it to be an artifact, then check that.
