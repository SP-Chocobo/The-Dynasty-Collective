# Phase 8 — certifying the post-`#52` repair mandate, and what v2 can honestly claim

Twelve register items (`#16`–`#28`) opened out of the blind adversarial pass. This is where each
one landed and what a v2 freeze may and may not assert.

## Disposition

| item | outcome | shipped |
|---|---|---|
| `#16` K/DST ordering | superseded by `#22`'s revert | — |
| `#17` turn-ending clustering | **WITHDRAWN** — measured where defenses cannot score | `85cc0fc` |
| `#18` projection reliability | **CLOSED, measured** — no DEF defect exists | `2840c94` |
| `#19` 6.1b eligibility_bonus | **DONE** | earlier |
| `#20` superflex QB regression | **DONE** (caused `#22`) | earlier |
| `#21` take-model floor | **BLOCKED ON `#50`** | `27c54ee` |
| `#22` acting_now ordering | **REVERTED**, number kept as an observable | earlier |
| `#23` superflex QB anomaly | **WITHDRAWN** — my own probe's error | earlier |
| `#24` / W1-07 survival term | **DONE** — retired, no redistribution | `27c54ee` |
| `#25` context_elevated | **DONE** | `4e1d4ea` |
| `#26` W4-01 rookie population | **DONE** | `264e063` |
| `#27` I-06/J-06 label | **DONE** | `264e063` |
| `#28` two vendors on one scale | **WITHDRAWN** — the board has no caller | `f0c1f32` |

Seven done, four withdrawn, one blocked. `STAGED` in
`test_rulings_are_not_silently_dropped` is now **empty**.

## What v2 may claim

- **Seven ruled repairs landed**, each with a measured cost recorded in the register and each
  licensed by a full green suite (3,399 tests at the last run).
- **The forward test's outcome half works for the first time.** The Sleeper stats endpoint had
  always 404'd; `29ab259` fixed the URL, and 36 weeks of real actuals now return.
- **The measurement can be re-run offline.** Four committed season captures plus
  `measure_projection_accuracy --from-captures`, which reproduces the live run on 83 of 84 fields.
- **`bpa` magnitude is not what puts defenses in round five.** Five independent measurements, the
  last by *moving* the price 2.2x rather than zeroing it and watching placement not move.

## What v2 must NOT claim

- **That K/DST pricing is fixed.** It is not. What is established is that the cause is not `bpa`
  and not projection reliability. The cause is unidentified and every remaining candidate is
  downstream of `bpa`.
- **That `#21` is resolved.** It is blocked on `#50`, which is a Gate 2 item.
- **Any per-position reliability constant.** None is derivable: four numbers across two seasons at
  se ≈ 0.33 is not a population (`#56`).

## The instrument record, which is the honest headline

**Eight conclusions were withdrawn or corrected during this mandate.** Every one was *measured*
rather than guessed, and every one measured the wrong object:

| withdrawn | the wrong object |
|---|---|
| cliff-steepness hypothesis | falsified by my own follow-up probe |
| `#23` superflex QB | my probe computed the wrong replacement arm |
| `#17` first run | a league with no K/DEF **slot** |
| `#17` second run | a league with no K/DEF **scoring** |
| the 3.1x | a document assumed stale that was not |
| the un-correction of the 3.1x | a board built with an argument no caller passes |
| `#28` | the same phantom board |
| "`#17`'s figures no longer reproduce" | attributed to drift without checking which league each probe built |

Three of those eight are the *same* failure — a fixture describing a league nobody plays — and two
are the *same* phantom board. The generalisable rules, now written into the probes themselves:

1. **The configuration is part of the measurement.** `compute_draft_board` returns a perfectly good
   board with no Sleeper argument and nothing says no caller builds it. A board number is not
   reportable without the call that produced it.
2. **A rulebook needs the SLOTS *and* the SCORING for the positions under test.**
   `t17_turn_ending_real_rulebook.py` now refuses to run without both.
3. **A test that asserts what our own code constructs is not evidence about a system we do not
   control.** (Banked at `29ab259`; the stats URL had a passing test pinning a 404.)
4. **A ratio over two data points is not a rate.** `measure_projection_accuracy` now prints
   `pairs`, the tie count at the replacement rank, and a caveat on the same line as any ratio
   resting on a tie or a negligible denominator.

## Freeze readiness

The repair mandate is **complete** in the sense that every item is disposed of: nothing is
half-done, nothing is silently dropped, and the one blocked item names its blocker. A v2 freeze can
be cut on that basis.

What it cannot be cut on is a claim that the engine now drafts K and DST correctly. It does not,
the cause is unidentified, and the most valuable output of this mandate is a much shorter list of
places it can be — plus four instrument rules that would have saved most of the eight withdrawals.


---

# SUPERSEDED IN PART: v2 DOES NOT FREEZE (owner ruling, 2026-09-23)

The "Freeze readiness" section above concluded a v2 freeze could be cut on the basis that every
repair-mandate item is disposed of. **That remains true and is no longer sufficient.**

The owner has ruled **`#30` -- the math behind streaming pick placement for K and DST -- a BLOCKING
item on v2**, conditioned on a gate: no production/draft quality drop-off of the kind the
brute-forced `#16` caused. The `v2-freeze` tag cut earlier was never pushed and has been deleted.

This certification's own words already pointed here -- *"What it cannot be cut on is a claim that
the engine now drafts K and DST correctly. It does not, the cause is unidentified"* -- and the
ruling makes that a blocker rather than a documented limitation.

See `evidence/kdst_streaming/PROBLEM.md` and the `#30` entry in `POST_AUDIT_PLAN.md`.
