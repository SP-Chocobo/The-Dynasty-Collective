# If the container was reclaimed — how to restart the `#35` C arms

The container is reclaimed on session IDLENESS, and **CPU does not count as activity**. This has
already cost one battery in this repository (the VDS run died at 13 of 36 arms). The scratchpad
does not survive a reclaim, so anything worth keeping has to reach the repo.

## What is running, exactly

Two processes, launched from the repo root at commit `6cd3be0`:

```
python3 evidence/design_35/phantom_cap_experiment.py --season 2024 \
  --arms control capped capped_floor_exempt capped_floor_exempt_no_backstop --out <SCRATCH>/c4_2024
python3 evidence/design_35/phantom_cap_experiment.py --season 2023 \
  --arms control capped capped_floor_exempt capped_floor_exempt_no_backstop --out <SCRATCH>/c4_2023
```

`<SCRATCH>` is this session's scratchpad directory. Each arm writes its own
`<arm>_<season>.json` the moment it finishes; the paired `SUMMARY_<season>.json` is written only
after all four arms complete.

## Where the results are kept so a reclaim cannot take them

`evidence/design_35/runs/` — every completed arm report is copied there and committed as it lands.
**A reclaim therefore costs at most the arm that was mid-flight**, never a finished one.

## To restart after a reclaim

1. `git log --oneline -5` and confirm the working tree is at or after `6cd3be0`.
2. `ls evidence/design_35/runs/` — that is what survived. Each file is
   `<arm>_<season>.json` with the same structure `run_backtest_grade` writes.
3. Relaunch **only the arms that are missing**, from the repo root:

   ```
   python3 evidence/design_35/phantom_cap_experiment.py --season <SEASON> \
     --arms control <the missing arms> --out <NEW SCRATCH>/c4_<SEASON>
   ```

   `control` must be included every time even when its report already exists. Paired deltas are
   taken against the control arm **from the same process** — that is the in-process A/B rule, and
   a control from a different process at a different commit is exactly the "fresh run against a
   saved baseline" comparison the engine-measurement skill forbids. The already-saved control
   report is for cross-checking that the arm reproduced, not for pairing against.
4. If the commit has moved past `6cd3be0` in any file the board touches, **start over**. Battery
   rule 2: never resume onto a report written by different code. `git diff --stat 6cd3be0 -- '*.py'`
   answers it; a change confined to `evidence/` or a document does not count.

## Reading the results

`PREREGISTRATION_C.md` — including its amendment, which moved the reading onto
`capped_floor_exempt` − `control` and added two non-vacuity gates. Read it before the numbers, not
after.

## What was in flight besides the arms

- The full test suite, after the `draft_counterfactual` absence fix. It must be GREEN before that
  fix is pushed; if the container died mid-suite, rerun it (`python3 -m unittest discover -s . -p
  "test_*.py"`, ~800-870s) rather than pushing on the strength of the four targeted files.
- Nothing else. Both Fable passes handed back and their deliverables are committed.
