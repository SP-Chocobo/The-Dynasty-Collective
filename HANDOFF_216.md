# HANDOFF — where #216 stands, and what to do next

Written 2026-09-08 for whoever picks this up: a future session, another agent, or the owner.
Everything named here is committed and pushed. Nothing important lives only in a container.

## The one-line state

**#216 BLOCKS THE FREEZE (owner ruling).** It is TRACED and NOT REPAIRED. A fix is being
implemented by a Fable agent in a worktree, under strict orders: no tuned weights, no invented
constants, no merge without owner sign-off.

## Branches

| branch | what it holds |
|---|---|
| `ui-authority-pass` | the working branch. All evidence, instruments, register entries. |
| `worktree-agent-a0a78a88e2d0163fe` | commit `b66c051` — the blind falsification battery. **DO NOT MERGE AS-IS**: its tests are designed to FAIL on unfixed code. They land with the fix. |
| a new `worktree-agent-*` | the current implementer. Snapshotted automatically (see below). |

## What #216 actually is

Two distinct defects, not one.

**(a) The stack.** `bpa = projected_points - replacement_level(position)`. A tight end starts
~43.5 bpa ahead of an identically-projected receiver. `depth_exposure` adds +6.24 to a FOURTH
tight end and is 0.0 where the roster is vacant — it REINFORCES the stack. Multiple
legitimate-looking terms push the same way, so no single-term patch will do.

**(b) The quarterback — a different failure.** `remaining_starter_demand` collapses to 1.0 (the
drafter's own unfilled slot); rank 1 makes replacement THE BEST REMAINING QB HIMSELF; bpa is
EXACTLY 0.00 for thirteen consecutive rounds. **Cannot value, not under-value.** No
roster-relative term downstream repairs it.

**`feasibility_first` has been the only thing making any roster legal.** It is a 0/1 sort key
that PARTITIONS the board, binding only when `picks_remaining <= unfilled dedicated slots`
(pick 12 of 14). Disabled, seats end TE11 RB3 — zero WR, zero QB. Confirmed independently by
two instruments, one written blind.

**The historical finding.** #84 stranded `marginal_lineup_value` on "in the displacement regime
it agrees with the ranking the engine already produces". Measured FALSE on the roster this
engine builds (top row agrees in 4/14, 5/14, 6/14 states). The assumption expired when the
engine drifted. Not a forgotten wiring.

## Do NOT do these

- **Do not ship RAW-MLV.** Best lineup totals, accidental mechanism: with an empty roster a
  player's marginal lineup value is just his own points, so its early order is raw points.
  A diagnostic control, not a fix.
- **Do not touch `NEED_BONUS_MAX`.** Ablation at 1e9 is pick-for-pick identical, 6/6 seats;
  zero rows ever sit at the cap. That knob does nothing.
- **Do not merge the battery branch before the fix.** Its tests fail on purpose.
- **Do not trust commit `2393b73`'s MESSAGE.** It was written by Opus over the reviewer's files
  and misrepresents them. `4b30cd4` is the correction. The authoritative document is
  `evidence/roster_shape/REVIEW_216_fable.md`.

## Open threads

1. **The implementer's report** — the fix it converged on, its pre-registered gate, honest
   result against it.
2. **The unresolved guard.** `test_216_value_board_falsification.py` has a "board is not the
   projection control" guard that FAILED on unfixed code; its author was killed before reading
   the failure body. Must be classified as (a) a real third finding, (b) a bug in the guard, or
   (c) the defect it was written to detect. **A fix making it pass does not discharge it.**
3. **Composition after any fix.** Replacement-filled MLV fixes STARTERS (+137..+165 lineup
   points, 6/6 seats) and NOT roster shape (bench ends RB9/RB10/TE9) and NOT the quarterback.
   Anyone claiming a complete fix must show all three.

## Six invariants any fix must satisfy

1. With `feasibility_first` disabled, compositions equal those with it enabled;
   `fills_required_slot` True on ZERO picks.
2. While the QB slot is unfilled in 1QB, the best remaining QB carries a POSITIVE price,
   falling to <=0 once filled.
3. A candidate the lineup cannot use never outranks one filling an empty slot at positive VOR.
4. A drafter's own bench picks never improve their selection signal at that position.
5. Most-drafted bench position count, backstop off, reported against that position's
   replacement gap.
6. Replay gate at every state.

Over-correction is FAILURE, not partial success: an engine that refuses a second tight end, or
drafts strictly to slot counts, or degenerates to raw projected points, has replaced one defect
with another.

## Environmental facts that have already cost real work

- **The container is reclaimed on OPERATOR inactivity, not the job's.** A backgrounded run does
  not hold it open. Three long runs died this way before `resume_join.py` (#215) made the
  instruments resumable. Anything long must write incrementally and support `--resume`.
- **Session rate limits kill subagents mid-flight.** Two died this way with work uncommitted;
  one was rescued by hand, one produced nothing. Hence the snapshot daemon.
- **Python puts the SCRIPT's directory first on `sys.path`, not the cwd.** Set `PYTHONPATH`
  when running a probe from a worktree. This killed one agent outright.
- Foreground `sleep` is blocked. Background with `nohup setsid`.
- Full suite: `python3 -m unittest discover -p "test_*.py"`, ~2650 tests, ~900s.

## Three of my own published explanations were withdrawn on this item

Recorded because the pattern matters more than any one of them: (1) "exactly the WR slot count,
a need signal saturating"; (2) "receivers arrive once every other tail falls through"; (3)
"`NEED_BONUS_MAX` caps the roster term below the bias". All three were measured false. Treat any
confident single-sentence explanation of #216 — including one of mine — as a hypothesis until
an instrument says otherwise.

## WHERE THE WORK ACTUALLY IS, as of the implementation pass

**Branch `worktree-agent-ab5e1af412aeb9182` @ `7efb423`. NOT merged.** It carries
`displacement_adj` (a fourth team-specific term, `replacement_level - displacement_level <= 0`,
no new constant), the blind falsification battery and room-integrity guards taken verbatim from
`b66c051`, and the second-pass shape instruments. Suite 2710 OK; 9/9 mutations killed. Fetch it
before doing anything on this item — re-deriving it would waste a full pass.

Full record: `POST_AUDIT_PLAN.md` -> #216 -> "THE IMPLEMENTATION PASS". Evidence on that branch:
`evidence/roster_shape/FIX_216_fable.md`, `PREREGISTRATION_216_fix.md`,
`evidence/roster_shape/fix_216/second_pass/`.

**Two open halves, both #50 and both the OWNER'S, not an implementer's:**
1. Two superflex seats reverse on the asset ruler under the term (both on bench rows) — a
   lineup-vs-asset exchange rate.
2. At an open FLEX every position is priced against its own positional anchor, never against the
   flex's real alternative. This is why the fixed engine fields zero tight ends in the owner's
   no-TE-slot league where his own roster carries two. Same class as #216, one layer up.

**A fourth withdrawn explanation, added to the three above:** "the bench regime falls back to raw
VOR." It does not. It orders by distance to my lineup and takes receivers (zero bench TEs in
6/6); the `RB2 < TE3` failures are STARTER picks, and correct by lineup points.
