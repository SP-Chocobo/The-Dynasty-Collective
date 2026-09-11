# What is left before "how it drafts" is done, and before v1 can freeze

Derived from the register and the evidence on disk, not from memory. Every claim below names
where it comes from. Written against HEAD `3d63c36`.

---

## The headline, stated first

**No measured drafting failure remains.** The #164 freeze triage named exactly one blocker
family — a chair finishing unable to field a legal lineup (#154/#155/#114). All three were
re-measured on the current engine and are gone: 0 of 19 rounds decided by a tiebreak, top-pick
value declining cleanly across all 19 rounds, and **every seat of every format filling its
lineup completely** (8/8 in 1QB, 9/9 in superflex) in the 6-format roster proof.

**What is unresolved is not a defect. It is the objective.** On the real rulebook, across 6
formats and 68 chairs, the engine:

- wins the **asset** ruler **68 of 68 chairs**, roughly doubling the control, and
- loses the **projected-points** ruler **67 of 68**, by **5–11%**.

**CORRECTION — these two are NOT symmetric, and presenting them as a pair was the most
misleading thing in this document.** The proof's own design note settles their status:

> *"A win on `cdme` alone is a tautology and must be reported as one. A win on `points` too is
> the strong claim: the engine beat the control at the control's own game."*
> — `run_roster_proof.py`, RULERS

`cdme` is the engine's own objective, so **68/68 there carries no information by construction**.
`points` is the control's objective, and beating a control someone would actually play is the
only informative test in this repo. Measured, the two rulers correlate at **r = 0.241** — they
are different questions, not two views of one, so a win on either does not imply the other.

**So the honest statement of the result is: the engine has been tested once against a fair
control, and did not pass.** 1 of 68 seats. Every lineup is full, so this is not a failure to
field a team — it is fielding a different one on purpose, and losing on the ruler that says
whether that was worth it.

**There is no established exchange rate between present-season points and dynasty asset value in
this system**, so "correct dynasty construction" and "systematic mispricing" both still fit. But
the burden has moved: the one test that could have discharged it was run and not passed.

Source: `evidence/roster_proof/README.md`, `ROSTER_PROOF_2026-09-08_realrules_COMPLETE_6of6`.

---

## SCOPE LIMIT ON EVERYTHING BELOW — the evidence measures a different league than the owner's

Added after #241's withdrawal exposed it. **Two captured leagues exist and they are not the
same scoring environment:**

| file | read by | `rec` | `bonus_rec_te` | first downs |
|---|---|---|---|---|
| `data/fixtures/sleeper_capture.json` | **`run_draft_battery`**, **`run_roster_proof`** | 1.0 | absent | none |
| `data/league_captures/fourth_and_forever.json` | the `evidence/roster_shape/ff_rulebook/` probes | 0.5 | 0.25 | `rec_fd 0.5`, `rush_fd 0.25` |

The headline result this checklist leans on — the tautology won 68/68, **the strong claim lost 67/68** —
was measured on the **fixture**: full PPR, no TE premium, no first-down scoring. Fourth and
Forever, the league actually being played, is half-PPR with a TE premium and pays receivers
**double** what backs get for the same first down, plus a `pass_cmp 0.1` completion bonus in
superflex.

**Why this matters to the ruling in Gate 2, now with a measured number rather than an argument.**
Four of the owner's real week-1 starters, itemised by the Sleeper app, scored through the
production function against both rulebooks:

| | F&F (played) | fixture (measured) |
|---|---|---|
| McCaffrey | 11.80 | 13.80 |
| Smith-Njigba | 30.20 | 34.20 |
| Stevenson | 13.00 | 14.50 |
| Purdy | 24.60 | 29.60 |
| **total** | **79.60** | **92.10  (+15.7%)** |

The F&F column reproduces the live app **to the cent, 4 of 4**, and its total is the number the
app displayed — so this is ground truth, not a model. Purdy alone swings 5.00.

**The freeze's headline deficit is 5–11%. The rulebook difference is ~16%, and it runs the other
way.** That is larger than the effect being ruled on, so the size and possibly the *sign* of the
points deficit is not established for F&F. **Neither is it refuted.** It is unmeasured.
Evidence: `evidence/rulebook_ground_truth/README.md`.

**This does not invalidate any existing result.** The battery and the roster proof agree with
each other because they use the same fixture, and the `ff_rulebook/` probes are honestly named
and scoped (#175's scope statement states F&F's `rec` and `bonus_rec_te` explicitly). What was
missing is this note.

- [ ] **Decide whether the freeze's evidence should be re-measured on F&F's rulebook**, or
      whether the freeze deliberately certifies the engine against a generic full-PPR
      environment and records F&F as out of scope. Either is defensible; the current state
      picks neither and says nothing, which is the part that is not defensible.

## GATE 1 — Evidence that does not currently exist

- [ ] **#150 — re-run the mass battery. Both committed runs are WITHDRAWN.**
      `evidence/batteries/README.md:93` marks both 33-format runs withdrawn: they predate #213
      (every arm scored against a one-key rulebook). They also predate #196 (pool 2041→2105,
      priced 329→371), #201 (real universe) and #204 (production pricing path). **There is
      currently no valid cross-format behavioural evidence for the engine as it stands.**
      Cost ~2.9h. Nothing below can be called verified across formats until this exists.
- [ ] **#241 — before that run, make the battery report the hint distribution it exercises.**
      All 33 arms currently resolve `te_premium=True`, so one of the four advertised axes is
      constant and nothing notices. Derived, next to `independent_formats`, the way
      `duplicate_arms` already works.
- [ ] **Do not count 33 arms as 33 independent ones.** Measured this session: league size and
      superflex cannot move a gap-based quantity at all (0 of 41/125/197/114 gaps change while
      the top QB price moves 48.51 → 163.06), because `bpa` is points minus a per-position
      constant. Check which axes the quantity under study can actually see before sizing a run.
- [ ] **#218 — the #222 Phase 0 reproduction was deferred and never re-run** (312 picks).

## GATE 2 — The objective ruling (owner; #50 / Phase 3)

This is the decision the points-vs-asset result above forces. It is not code work, and
**everything in this cluster is downstream of it** — none should be repaired independently:

- [ ] **#50** — VOR / replacement / horizon redefinition. The parent.
- [ ] **#74 / #76** — the bpa unit drifts 72× and bundles six quantities; the ruler carries 94.5%
      of its own movement. #155 folded into this: cross-position VOR ranks a 0.00 above a
      −3.86, which is what VOR *means*, and whether it is comparable across positions is the
      open question.
- [ ] **#147** — the valuation anchor has a one-season lifetime in a dynasty engine.
- [ ] **#152** — the `trade_value` fallback's ceiling is a unit artifact, not a demand judgment.
- [ ] **#165 (reserved half)** — contextualizing an unpriced player; material exists, carrying it
      is a valuation-layer change.
- [ ] **#229** — cross-position VOR is authorized; the DEEP-BENCH case is undefined.

## GATE 3 — Open items that can change a pick

These reach `final_score` or the candidate set, so they are drafting behaviour proper.

- [ ] **#231 / #232 / #222 — upside mode implements half its stated intent and inverts the other
      half.** The mode boundary causes 63% of the TE excess, measured and causally active. The
      positional handicap is exact and derived (TE +68.58 at the flex). This is the largest
      unactioned behavioural finding in the register.
- [ ] **#223 / #225** — the mode transition concept is genuinely missing, for lack of a decision.
      The TE decision at the boundary is a real near-tie on (points − displaced).
- [ ] **#153** — two clamps, not one: the 4WR collapse is the flex-share clamp, not `NEED_BONUS_MAX`.
      Measured and understood; not repaired.
- [ ] **#86** — `round(expected_taken)` is a knife-edge feeding `cliff_protection`.
- [ ] **#216 (B4)** — board rank is not pick order: three ordinals, three names. Cross-register
      ordinal confusion has already produced a defect family here (#70).
- [ ] **#167** — `reach_label` changes **0 of 36** engine decisions under ablation. Demote/remove
      is supported for the engine and the recommendation is ready; **ratification is the owner's**.
      (The LLM-debate effect was NOT established either way.)
- [ ] **#235 / #236** — `shared_slot_adj` vs `displacement_adj`: exact decomposition executed as
      vocabulary, deliberately **not wired**. Wiring it is a Gate-2 decision, not a repair.

## GATE 4 — Reaches the human, not the pick

Confirmed this session: `_board_order` sorts on `["_feasible", "final_score", "player_id"]`
only. The items below feed observables and the debate layer, so they degrade what the app
*says*, not what it *picks*. They still gate a shippable v1, because a person reads them.

- [ ] **#206 — `survival_probability` says 0.00 for a player who then survives 60 straight picks.**
      It feeds `opportunity_cost`, `pick_necessity` and `rival_premium`. It is also the stated
      reason the #55 necessity wiring was declined ("a signal is not promoted to decision-maker
      while one of its main inputs is under investigation"). Highest-value item in this gate.
- [ ] **#183** — six defects in the live Debate Dock, including the absence contract broken
      exactly where a person actually reads it.
- [ ] **#112** — kind-of-absence stops at the board; "never checked" has no representation.
- [ ] **#119** — `universal_value`'s decomposition reaches no consumer, so causal reconstruction
      breaks at the valuation leaf.
- [ ] **#211** — `starter_value` ranks positional breadth, not roster quality. Pinned as
      KNOWN-OPEN-ACCEPTABLE; worth re-reading once Gate 2 is ruled, since it is the metric the
      roster proof's asset ruler leans on.

## GATE 5 — Owner decisions for the freeze record (no code)

- [x] **#55** — `pick_necessity` stays OBSERVABLE, no selection authority. Ruled.
- [x] **#184** — documented as a bounded limitation; does not hold the freeze. Ruled.
- [x] **#188** — vocabulary ruling executed and closed.
- [x] **#175** — REJECTED: no derivable threshold; `CLIFF_HIGH_RATIO` unchanged.
- [ ] **#146** — bye week is admissible when the asset horizon is one season (redraft only).
- [ ] **#160** — Decision A, reopened from zero; no constant to be tuned.
- [ ] **#149** — upload storage custody.
- [ ] **#98** — the §7.4 allowlist decision (§7.10 already declined as the owner's).
- [ ] **#158** — confirm the ten ratified decisions are carried verbatim into the freeze record.

## GATE 6 — Blocked external: accept at freeze, or the freeze waits

None are engine defects. Each needs something this machine cannot reach.

- [ ] **#88 / #143** — `api.sleeper.app` is denied by the network policy (403 at CONNECT, evidenced).
- [ ] **#120 / #109** — provider metering and served-model identity need live SDKs.
- [ ] **#49 / #210** — real K/DEF/IDP startup boards, and Sleeper supplying IDP without stat lines.

## Explicitly NOT gating "how it drafts"

Carried so nobody re-litigates them at freeze time: the UI track (**#181**, **#36**, **#137**,
**#173**), the prose audit (**#182**), and the LLM/operations layer (**#91/#93/#96/#97/#100/
#103/#105/#117**). #164 already classified these as a parallel track that does not gate the engine.

## Freeze mechanics, in order

1. Gate 1 (battery re-run) — produces the evidence everything else is judged against.
2. Gate 2 (objective ruling) — owner. Unblocks Gate 3's biggest items.
3. Gates 3 and 4 — repair what the ruling licenses.
4. Re-run Gate 1 once more; suite green; **#53** reconciliation, owner's sole authority.
5. Cut the freeze marker (a branch — tag refs are 403 here, per #135).
6. **#52** — the blind adversarial pass runs **after** the freeze and **stays unbriefed**.
   Briefing it destroys the only unbiased read available.

Per **#162**: evidence before repair, repair before freeze, freeze before blind audit. A clean
bill of health is the gate, not the calendar.

---

## The shortest honest answer

**One ruling and one battery run stand between here and a defensible v1 freeze.**

The battery (Gate 1) is mechanical — about three hours, and it can start now. The ruling
(Gate 2) is the real gate: the engine is trading 5–11% of current-season points for roughly
double the asset value, deliberately, in every seat of every format, and **that trade has never
been ratified or rejected**. Until it is, "does it draft well?" has no defined answer — only
"it drafts consistently, and here is what it optimizes."

Everything in Gate 3 is either downstream of that ruling or small enough to land in a day.
