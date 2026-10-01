# V4-I1 (`run_vds_battery.py`) — review requested, NOT performed. Why, and the baseline for it.

## Status: not reviewed

The review was asked for against commit `6e8c1e2`. **That commit is not in this repository.**
Checked at 2026-10-01 04:22 UTC, one minute after `git fetch --all --prune`:

* no object with prefix `6e8c` among the 574 reachable commits — checked with
  `git cat-file --batch-all-objects`, so unreachable and dangling objects too;
* the newest commit touching `run_vds_battery.py` or `test_vds_battery.py` on **any** ref is
  `dc2de79` (2026-09-29, "Repair 2.4"), two days before this work;
* no commit message or tree on any ref mentions `V4-I1`.

The author's own note, in the transcript the request came with, says why: the push was gated on a
green suite and had not landed. Nothing is wrong with the fix; it simply was not fetchable.

This file exists so the next session starts from a verified baseline instead of re-deriving one.

## The defect V4-I1 repairs is REAL, and its consequence is total

Established here, against the code on disk at `7984b1d`, by running the instruments session's own
probe — `evidence/blind_pass_v4/probes/probe_vds_sharp_seats_guard.py` on
`origin/claude/v4-verify-instruments`, cited rather than copied so there is one home for it — over
the real serialized arms of the last committed VDS run
(`evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json`):

```
arms: 36
keys on an arm row: carried_forward findings format label margins pick_sequence picks
                    produced_at_commit qualifiers regimes rosters rounds seconds shape
                    strategy strength teams unpriced_at_decision
rows carrying a top-level 'sharp_seats': 0 of 36
rows carrying 'opponent_noise'        : 0 of 36

STRATEGY_SPECIFIC_FINDINGS : {'12T_ppr_K_DEF': ['noisy_k8'], '12T_ppr_SF': ['noisy_k8'],
                              '4WR_TE_PREMIUM': ['noisy_k8'], '12T_ppr': ['noisy_k8']}
   -> EXCLUSION DID NOT FIRE
same arms, with sharp_seats copied in from STRATEGIES: {}
```

`run_vds_battery._report`'s guard is
`if row["label"] in inert_labels or not row.get("sharp_seats", ["present"])`. The arm row carries
no such key, so the `.get` always returns the truthy default and `not [...]` is always `False`.
**Every entry in `STRATEGY_SPECIFIC_FINDINGS` on the last committed run is `noisy_k8`** — a noise
arm the guard's own comment says "belongs on no strategy's ledger".

## What the review must test when the commit lands

1. **Does the repaired guard fire on PRODUCTION'S OWN arm rows** — rebuilt through `rvb._report`
   over the committed run, never a hand-built dict (`engine-measurement`: build production's inputs
   in production's shape).
2. **Does the fix keep a `.get(..., <truthy default>)`?** If so, every already-committed VDS JSON
   replays with the exclusion silently off — the original defect's own shape, one layer back. The
   arm row already carries `strategy`, so deriving the answer from `vds_battery.STRATEGIES` needs no
   new key on the row and cannot go stale against an old file.
3. **Does the new test bind?** Revert the fix and confirm the test fails. Check specifically whether
   its fixture supplies the `sharp_seats` key that the real arm row lacks — a fixture that does is
   the "expectation agrees with the bug" class, and it is what let this guard ship.
4. **Check the commit message against the code.** One claim is already checkable: `test_vds_battery.py`
   exists today (140 lines, last changed by `dc2de79`), so "its new test module" is either an
   additional module or a loose description.

## Scope note

`run_vds_battery.py` is not part of the nine repairs reviewed in
`INDEPENDENT_REVIEW_REPAIRS.md`; it is outside the `eac7491..7984b1d` range on every ref. Nothing in
that review covers it, and nothing here should be read as covering it either.
