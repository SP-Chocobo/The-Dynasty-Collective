# `#29` VDS battery — what is running overnight, and how to pick it up cold

The container is reclaimed on session **idleness**, and **CPU does not count as activity**. This
battery has already been killed that way once, at 13 of 36 arms. This file plus
`evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json` are what survive it.

## What is running

```
python3 run_vds_battery.py --out <SCRATCH>/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json
```

Launched from the repo root at commit **`04bccb5`**, **36 arms, no `--resume`**, all arms fresh.

**Liveness check — use the right script name.** The running process is `run_vds_battery.py`, *not*
`run_draft_battery.py`. Checking with `pgrep -f "run_draft_batter[y]"` returns nothing and reads
exactly like a dead battery; it is a pattern error, not a death. The check is:

```
pgrep -f "run_vds_batter[y]"        # or: ps aux --sort=-%cpu | head -3
```

Two corroborating signals before ever concluding the run died: the log's mtime (it is appended once
per arm, so up to ~20 minutes stale is normal) and `uptime` (a container restart resets it; a steady
load average of ~1.0 means something is still burning a core).

**Measured runtime, not estimated:** the first arm did 192 picks in **774.2s = 4.03 s/pick**. The six
formats total 1,044 picks per strategy sweep, × 6 strategies = **6,264 picks ≈ 7.0 hours**. An earlier
estimate of "2.5–3 hours" in this session was wrong — it came from the old 32-format battery, which is
a different shape.

| format | teams | rounds | picks |
|---|---:|---:|---:|
| `12T_ppr_K_DEF` | 12 | 16 | 192 |
| `12T_ppr_SF` | 12 | 15 | 180 |
| `4WR_TE_PREMIUM` | 12 | 16 | 192 |
| `HEAVY_IDP` | 12 | 18 | 216 |
| `12T_ppr` | 12 | 14 | 168 |
| `12T_ppr_SHORT_DRAFT` | 12 | 8 | 96 |

Strategies: `sharp_auto`, `sharp_balanced`, `sharp_upside`, `crossing`, `noisy_k3`, `noisy_k8`.

## Why this run and not the one before it

The battery was launched once at the frozen candidate `43c8188` and **stopped at ~20 minutes**, because
`streaming_floor_exercised` was **False** — `#30`'s streaming floor was derived for NONE of the 36 arms,
so the run was grading the engine with its own K/DST repair missing. That was a **wiring** gap, not a
data gap: the per-week lines for the capture's own season (2026) were already on disk. Fixed at
`04bccb5`, vintage-matched.

**Confirmed live in this run's own universe block:** `weekly_projection_weeks: 18`,
`streaming_floor_exercised: true`. `12T_ppr_K_DEF` is the only one of the six formats with K and DEF
roster slots, so **6 of 36 arms exercise `#30`**; the other 30 have no such slots and the floor
correctly does not bite.

## Checkpointing

`run_vds_battery` writes the **whole report after every arm** (`complete=False` until the last), so the
live file is always a valid checkpoint of everything finished. `vds_checkpoint.sh` copies it into
`evidence/batteries/` after validating it as JSON, and it is committed as arms land. **A reclaim costs
at most the arm in flight.**

```
sh evidence/design_35/vds_checkpoint.sh <SCRATCH>
```

## To pick it up cold after a reclaim

1. `git log --oneline -3` — confirm the tree is at or after `04bccb5`.
2. `python3 -c "import json;d=json.load(open('evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json'));print(len(d['results']),'arms',[r['label'] for r in d['results']])"`
   — that is what survived.
3. **Check the commit before resuming.** `git diff --name-only 04bccb5 HEAD -- '*.py'` must be empty of
   engine files. If any engine or scoring file moved, **start over** rather than resume: battery rule 2,
   never resume onto a report written by different code.
4. Copy the checkpoint back into a fresh scratchpad path and relaunch with `--resume` pointed at it, so
   finished arms are reused rather than re-drafted. Never point `--out` at the tracked copy for a live
   run — that is battery rule 1.

## How to read it when it lands

**Strategy-wise, which is the whole point.** A finding under EVERY strategy in a format is a FORMAT
finding and the other battery would have caught it. **A finding under ONE strategy is what this battery
exists for** — that is the shape `#22` had, and the shape the format matrix cannot see because it holds
strategy at `mode="auto"`.

The bar is the owner's: **meet or beat, no draft-quality drop-off** of the kind the first brute-forced
K/DST attempt produced. `#16` is the counter-example and the standard — it bought the shape and paid
−6.09 on the independent ruler, seat wins 11/12 → 2/12.

## What this gates

**The v2 freeze**, which is not cut. Owner's ordering: *"freeze is the last item before audit. if we
find more tinkering to do, that happens before freeze."* So a finding here is work to do BEFORE the
freeze. `FREEZE_RECORD_V2.md` is a freeze CANDIDATE and says so; no tag exists (a premature `v2-freeze`
at `43c8188` was cut and deleted).
