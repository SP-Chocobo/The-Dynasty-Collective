# Where this investigation stands — resume here

Written for a cold start. Everything below is measured unless marked as a plan.

## The question

"Does this engine draft well, competitively, in a shape a competitive user would recognise?"
The instrument that can answer it is `run_backtest_grade.py`: draft a FINISHED season's
projections, score the roster on that season's REAL weekly outcomes (`realized_ruler`), against
a field of `need_first` / `points_need` seats. It is the only ruler the engine cannot optimise
toward.

## Two instrument defects found today, both in the same place

1. **The pool contained players who did not exist in the drafted season** — 133 in 2023, 101 in
   2024, priced from the 2026 vendor export at the top of the board, realizing 0.0. Mechanism
   and guard: `ANACHRONISM.md`.
2. **Filtering the pool was not enough.** Nobody can draft a ghost, so ghosts are never removed
   from the board — they ACCUMULATE. On a drained round-16 board, all 26 remaining candidates
   were ghosts. Fixed by building the board from a period-correct `players_db`.

I dismissed (2) once, on an opening-board measurement, and had to withdraw that. **Every number
measured between those two fixes is superseded.** The general lesson, which belongs in the
engine-measurement skill: *a contamination that accumulates must be measured on a DRAINED board,
because the opening board is where it is guaranteed to look harmless.*

## The engine defect found today

`ROOT_CAUSE.md`. The engine drafted **nine defenses and one receiver** in a league with one DEF
slot. The 32 defenses project 109–121 against a replacement level of 107.95, so every one of
them carries positive VOR while the real tail of a deep position prices negative. Once the
starting slots are covered the board is pure VOR, so a flat shallow position outranks the tail
of a deep one at every remaining pick.

Nothing caught it: the projected ruler solves one lineup with no absences (bench is free), the
four structural audits all pass on that roster, and self-play means every chair hoards together.

## What was built in response

| thing | what it is |
|---|---|
| `run_backtest_grade.period_correct_pool` | the guard; refuses to run if it drops nothing |
| `draftable_db` in the grader | the board half of the guard |
| `evidence/backtest/roster_diff.py` | reads a deficit out of a saved report by position, round, and the early bill — no re-draft |
| `draft_battery.unfieldable_depth` | a fifth structural audit; the four that existed pass on the nine-defense roster |
| `draft_room.fieldable_ceiling` / `unfieldable_last` | the engine backstop: demote a position this roster has saturated beyond `slots(P) + 1` |
| `evidence/kdst_streaming/fieldability_arm_experiment.py` | its A/B, with `--streaming` so `#30` and the backstop are measured together |

## THE ANSWER (2024, 12 seats, realized outcomes)

`evidence/kdst_streaming/RESULT_2024.md` has the full table and the limits. In one line: with
both fixes the engine **wins 11 of 12 seats at +82.9 a seat**, first K/DST at rounds 8–12, and
a roster shape of RB 6 / WR 3 / QB 2 / DEF 2 / K 2 / TE 1 — two of every dedicated position and
depth in the flex-reachable ones. Base is 0 of 12 at −346.9 with six defenses and one receiver.

Each fix alone improves **12 of 12 seats** and neither is sufficient: the backstop caps the
hoard without repricing (still opens K/DST in round 4), `#30` reprices without capping (still
finishes with four defenses and four quarterbacks).

`#30` is now WIRED TO PRODUCTION: `sleeper_client` keeps the per-week lines it already fetched,
the snapshot carries them, `compute_draft_board` takes `weekly_projections`, and
`replacement_levels` takes a raise-only `streaming_floors`. `app.py` passes it at all four board
call sites. `STREAMABLE_POSITIONS = ("K", "DEF")` is a named scope decision with the RB/WR
falsification recorded beside it and QB deliberately left out.

## Superseded numbers, kept for their direction

Recorded so the direction is not lost. Guarded-pool-only (board still contaminated), 2024,
`12T_ppr_K_DEF`:

| arm | mean delta vs field |
|---|---:|
| base | −640.95 (0/12) |
| `#30` streaming level | −363.08 (0/12), paired **+258.8**, improved 12 of 12 |
| fieldability backstop (seat 1) | −252.5, paired **+423.9** |
| both (seat 1) | −85.4, paired **+237.2** over streaming alone |

Direction: both fixes are large and they compose. Magnitudes must be re-measured.

**A second finding from those rosters, not yet addressed:** with the backstop on, the hoard
MOVED — seat 1 finished with six tight ends, because TE is FLEX-reachable and therefore exempt
from the ceiling. A uniform ceiling of "slots whose eligible set contains P, plus the bye" is
derivable (TE 3+1, RB 4+1, WR 4+1) and would close that, at the risk of binding on legitimate
depth. **Not built. Measure before building.**

## Plan, in order

1. ~~Seat-1 A/Bs under the corrected grader~~ — DONE.
2. ~~Full 12-seat runs on 2024~~ — DONE, see above.
3. The **2023 holdout** — RUNNING (`fieldability_arm_experiment --season 2023` and
   `--season 2023 --streaming`). This is the out-of-sample test and nothing generalises without
   it.
4. The **VDS battery** — RUNNING, fresh from `3a23c94`, writing to the scratchpad. The old
   3-arm checkpoint at `dace907` is UNUSABLE: the battery README forbids `--resume` onto a
   report written by different code, and the engine has changed substantially. This run is the
   "ensure nothing breaks" check across six formats and six strategies, and it exercises the
   backstop in every one of them.
5. **Full suite** — running; it licenses the next push.
6. `unfieldable_last` is an ENGINE-DESIGN change (`#184`). It is built and measured, not ruled.
   The owner decides whether it ships. `#30`'s half is already wired to production.
7. Not addressed: whether QB belongs in `STREAMABLE_POSITIONS`, and whether a uniform
   fieldability ceiling over flex-reachable positions would help or bind on real depth. Both
   are measurable; neither is measured.

## Standing hazards

- Container reclaim kills background runs; CPU does not count as activity. Checkpoint often.
- Never point a live run's `--out` at a tracked path.
- The full suite licenses a push, never a subset. (Violated once today and corrected.)
