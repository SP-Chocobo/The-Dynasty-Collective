# What is left before "how it drafts" is done, and before v1 can freeze

> # STATE AS OF 2026-09-12 — read this first; everything below it predates these runs
>
> Three measurements landed together and they move the picture in both directions.
>
> ## 1. Gate 1 is DELIVERED, and it found a blocker
>
> `BATTERY_2026-09-12_scoring_aware_full_99f9f76`: **33 formats, 32 independent, 5,340 picks,
> complete**, postdating #213/#196/#201/#204/#242. The first battery here that is not withdrawn.
> `constant_axes: []` — nothing advertised is inert.
>
> **Two structural findings, both a chair unable to field a legal lineup** (`8T_standard` seat 5,
> `14T_standard` seat 4 — empty FLEX, full 14-man roster). That is the family #164 called the
> only blocker and this document called dissolved. **It is not dissolved.**
>
> Root cause, exact (`#247`): `feasibility_first` protects DEDICATED slots only, never flex, on
> the stated premise that *"a flex slot is fillable from several positions, so it is not at
> risk"*. True until the roster owns no spare of ANY of them. Seat 5 drafted **eight
> quarterbacks in a one-QB league**; every named slot was filled, so `unfilled == 0` and the
> backstop was a no-op for the entire draft.
>
> **The two findings are a lower bound, not a count.** Measured across all four 1QB standard
> arms, longest same-position run per seat: `8T [8,7,3,3,3,2,2,2]`, `10T [7,6,5,5,4,4,3,3,3,2]`,
> `12T [7,7,5,5,4,4,4,4,3,3,3,2]` — and **10T/12T are flagged zero times**. The hoarding is
> universal; only the flagging is rare, because the audit fires only when the hoarded position is
> flex-INELIGIBLE. A seat taking eight TEs is invisible to it.
>
> ## 2. The headline deficit this document was built around is STALE EVIDENCE
>
> `#205`'s 1-of-68 at −5% to −11% was produced at commit `8cee942` — **190 commits back**,
> including `#216 WIRED: one slot, one alternative reaches the board`. Re-measured on today's
> code, same format, same harness: **4 of 12, −0.28%** (`#248` arm A).
>
> It was never wrong. It describes a different codebase. **Across every shape tested today,
> engine and control sit within ~1% of each other.**
>
> ## 3. ~~The F&F reversal is the ROSTER SHAPE — one flex slot — not the rulebook~~
>
> > ⛔⛔ **WHOLLY WITHDRAWN, 2026-09-12 (28th). IT IS THE RULEBOOK, AND THE ROSTER IS INERT.**
> > Arm B never moved `rec` — `build_mock_league` overwrote it — so the cut that "moved the
> > rulebook alone" left the largest lever at PPR and read the PPR rankings export. Supplied
> > directly, the rulebook inverts the verdict on the FIXTURE roster (3/12 −0.84% → 10/12
> > +1.04%), and the 15-slot fixture roster reproduces the 29-slot F&F roster BIT-FOR-BIT.
> > See `evidence/roster_proof/README_MISSING_CELL.md`. The heading and text below are kept
> > unedited as the record of what was believed.
>
> Pre-registered three-arm cut, one process, one code version, rounds matched (`#248`):
>
> ```
> A  fixture roster + fixture scoring     4 of 12   -0.28%
> B  fixture roster + F&F scoring         4 of 12   -0.61%   <- rulebook moved alone: NO EFFECT
> C  F&F roster     + F&F scoring        10 of 12   +1.04%   <- reproduces #245 to the cent
> ```
>
> The two rosters differ in one startable slot: **FLEX 2 vs FLEX 3.** Everything else identical.
> So the rulebook work (`evidence/rulebook_ground_truth/`, the real +15.7% scoring difference)
> stands as measurement and is **not** what drives the verdict.
>
> > ⛔ **THE FLEX HALF OF THIS IS WITHDRAWN (27th), later the same day.** The rulebook half stands
> > and A/B/C reproduce exactly. But the flex reading was a reading, and the cut it named was run
> > in both directions:
> >
> > ```
> > A2  fixture, FLEX 2   4/12  -0.28%   CONTROL, reproduces arm A with ZERO differing values
> > D   fixture, FLEX 3   3/12  -0.84%   one flex ADDED    -> engine margin -6.99 -> -22.53
> > C2  F&F,     FLEX 3  10/12  +1.04%   CONTROL, reproduces arm C with ZERO differing values
> > E   F&F,     FLEX 2   9/12  +0.84%   one flex REMOVED  -> engine margin +29.43 -> +22.08
> > ```
> >
> > Both cuts hurt, so the slot has no consistent sign. `A2` and `E` have the **same 9 startable
> > slots** and opposite verdicts, so it is not the startable count either. Draft length,
> > rulebook and flex count are now all refuted by measurement.
> >
> > **What remains:** at 15 rounds the fixture roster has **0** spare draftable slots and F&F has
> > **11**. `draftable_slots_per_team` feeds `remaining_league_picks`, so roster capacity reaches
> > the engine independently of flex count and round count. That is the next pre-registered cut.
> > Evidence: `evidence/roster_proof/README_FLEX_CUT.md`.
>
> ## What this does to the gates
>
> - **Gate 1** — done. Re-run required after any repair.
> - **Gate 2 (the objective ruling)** — substantially DEFUSED as posed. It was framed around a
>   5–11% trade that no longer reproduces. The underlying question (present points vs dynasty
>   asset value) is still unratified, but it is no longer being decided against a large measured
>   deficit.
> - **`#247` — REPAIRED at `3e9c074`.** `feasibility_first` now asks the whole starting lineup
>   instead of dedicated slots only. Measured before shipping: both failures fixed, binds 4 times
>   in 644 picks, zero effect on either clean arm. It was the only measured drafting failure.
> - **Gate 1 now needs ONE more run.** The committed battery describes the engine *before* this
>   repair. That re-run is the freeze gate, not a per-repair regression test — deliberately not
>   done per repair.
>
> Sources: `evidence/batteries/README.md`, `evidence/flex_feasibility/README.md`,
> `evidence/roster_proof/README_RULEBOOK_CUT.md`, `evidence/roster_proof/README_FF.md`.

---


Derived from the register and the evidence on disk, not from memory. Every claim below names
where it comes from. Written against HEAD `3d63c36`; corrections since are dated inline.

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

**SUPERSEDED — the engine has now been tested TWICE against a fair control, and the two tests
disagree.** The paragraph this replaces read "tested once, and did not pass". That was true when
written and is now half the evidence.

| run | league | rounds | seats | `points` wins | margin |
|---|---|---:|---:|---:|---:|
| `#205` | fixture, 6 formats | 14–15 | 68 | 1 of 68 | −5% to −11% |
| **`#245`** | **Fourth and Forever** | **26** | **12** | **10 of 12** | **+1.04%** |

Same harness, only the league swapped. Every seat filled 10/10 starting slots in both.

**The sign of the difference is a property of the LEAGUE, not of the engine** — measured, not
inferred. The pre-registered length cut re-ran F&F at 15 rounds and returned `points` identical
to the cent (10 of 12, +1.04%), so at a MATCHED round count the fixture's `12T_ppr_SF` loses
1 of 12 at −5.03% while F&F wins 10 of 12 at +1.04%. Draft length is refuted. Still crossed: the
rulebook, the roster shape, and the superflex × TE-premium combination no fixture format carries.

**What this does NOT say.** `+1.04%` is an order of magnitude smaller than the deficit it
contradicts, and it is one league. "The engine wins" is a much weaker claim than "the engine
loses" was. There is still no established exchange rate between present-season points and dynasty
asset value, so both "correct dynasty construction" and "systematic mispricing" still fit the
fixture result.

**What it does say, for the freeze:** the strong claim holds in the league the owner actually
plays, so the deficit can no longer be stated unqualified as a property of the engine.

Sources: `evidence/roster_proof/README.md` (#205), `evidence/roster_proof/README_FF.md` (#245,
with the length refutation and the next pre-registered cut), and `#246` for the horizon flaw
found in the F&F harness and demonstrated immaterial.

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
points deficit is not established for F&F. ~~**Neither is it refuted.** It is unmeasured.~~
Evidence: `evidence/rulebook_ground_truth/README.md`.

> ✅ **IT IS NOW MEASURED, 2026-09-12, and the suspicion above was right.** Same roster, same
> pool, same rounds, same code, same harness — only the rulebook swapped:
>
> ```
> fixture roster, fixture PPR rulebook      3 of 12   -0.84%   engine BEHIND
> fixture roster, F&F rulebook (the owner's) 10 of 12  +1.04%   engine AHEAD
> ```
>
> **The sign of the verdict is a property of the scoring environment**, and the 15-slot fixture
> roster under F&F's rulebook reproduces the 29-slot F&F roster bit-for-bit — 0 differing values
> across 12 seats × every metric, at both flex counts. The roster shape was never the cause.
>
> So every fixture-measured claim in this document — `#205`'s deficit, all 33 battery arms — was
> taken in a full-PPR environment the owner does not play in. The checkbox below is no longer a
> choice between two defensible unknowns; it is a choice with a measured number attached.
> Evidence: `evidence/roster_proof/README_MISSING_CELL.md`.

**This does not invalidate any existing result.** The battery and the roster proof agree with
each other because they use the same fixture, and the `ff_rulebook/` probes are honestly named
and scoped (#175's scope statement states F&F's `rec` and `bonus_rec_te` explicitly). What was
missing is this note.

- [ ] **Decide whether the freeze's evidence should be re-measured on F&F's rulebook**, or
      whether the freeze deliberately certifies the engine against a generic full-PPR
      environment and records F&F as out of scope. Either is defensible; the current state
      picks neither and says nothing, which is the part that is not defensible.

      **IN FLIGHT — this is being answered by measurement rather than by decision.**
      `run_roster_proof_ff.py` runs the #205 harness unchanged (same `scoreable_pool`,
      `run_one`, `score_roster`, `RULERS`, `COMPARE_ON`) and supplies only the league: F&F's own
      29-slot roster, its 30 observed scoring keys, 26 draftable rounds, 12 seats. It writes
      after every seat, so a container suspend costs one seat rather than the run (an earlier
      attempt was killed at 8/12 and lost everything — the exact defect #213b exists to close,
      rebuilt by me and then closed again).

      **Pre-registered before the result was seen, so it cannot be fitted afterwards:**
      - engine wins or ties `points` on F&F -> the strong claim holds in the league actually
        being played, and Gate 2's ruling drops from *blocking* to *documentation*.
      - engine still loses `points` -> the strong claim genuinely fails, and it must be named in
        the freeze record rather than buried under the 68/68 tautology.

      Either way the result is **one league**, and a reversal between two rulebooks would itself
      be the finding — it would mean the deficit is a property of the scoring environment, not
      of the engine.

## GATE 1 — Evidence that does not currently exist

> ## ⚖️ GATE 1 IS REDEFINED BY THE OWNER'S RULING (`#251`), 2026-09-12
>
> **Do not re-run the 33-arm PPR battery as-is.** `#250` established that a battery in one
> scoring region cannot serve as universal evidence: the same roster under two rulebooks
> reverses the sign of the measured deficit. The correction is NOT to certify F&F instead.
> PPR, half-PPR, TE premium, first downs, roster size, flex count and superflex are
> **configuration dimensions, not foundational assumptions**, and neither captured league is
> canonical.
>
> **What is frozen is not "the engine works for F&F". It is "the engine's behaviour is correctly
> governed by league configuration, and the core invariants survive across the supported
> configuration space."**
>
> Gate 1 therefore becomes: certify **invariants** across **representative configuration
> coverage**, reporting configuration-dependent outcomes per cell without a pass/fail.
>
> - The invariant / configuration-dependent split is DERIVED from the battery's own structure by
>   `config_space.py` and pinned by `test_config_space.py`.
> - Coverage is now MEASURABLE BEFORE A RUN IS SPENT: the committed matrix went from **16 of 91
>   axes varied to 77** by adding one real captured league, which moved more axes than the other
>   33 arms combined.
> - The configuration layer is already DEMONSTRATED to work: across `#250`'s seven arms every
>   invariant held while the dependent outcome reversed sign.
>
> Full statement, with the corrections it produced: `evidence/CERTIFICATION_DESIGN.md`.
> The bullet below is kept unedited as the record of what Gate 1 used to mean.

- [ ] **#150 — re-run the mass battery. Both committed runs are WITHDRAWN.**
      `evidence/batteries/README.md:93` marks both 33-format runs withdrawn: they predate #213
      (every arm scored against a one-key rulebook). They also predate #196 (pool 2041→2105,
      priced 329→371), #201 (real universe) and #204 (production pricing path). **There is
      currently no valid cross-format behavioural evidence for the engine as it stands.**
      Cost ~2.9h. Nothing below can be called verified across formats until this exists.

      **DATED 2026-09-12 — both halves of this bullet are now wrong, in opposite directions.**
      The evidence DOES exist: `BATTERY_2026-09-12_scoring_aware_full_99f9f76`, 33 formats,
      5,340 picks, complete and not withdrawn (see the banner at the top of this file). And the
      cost is not ~2.9h — the scoring-aware battery measured **≈6.5h**. Budget the re-run from
      the larger figure; the ~2.9h above predates `#213`/`#201`/`#204`, which is most of what
      made it slower.
- [x] **#241 — the disclosure is BUILT; the finding that motivated it is WITHDRAWN (26th).**
      The claim recorded here — "all 33 arms resolve `te_premium=True`" — was false. I built the
      matrix from `fourth_and_forever.json` while the battery reads `fixtures/sleeper_capture.json`.
      Against the real source the axis IS varied: `te_premium {False: 30, True: 3}`, and
      `constant_axes = []`. Caught by the instrument built for the finding, on its first real run.
      The disclosure (`format_axes`, derived from `league_format_hint`'s own keys, reported next
      to `independent_formats`) ships anyway, because the run should state the axes it exercised
      whether or not one of them is currently constant.
- [ ] **Do not count 33 arms as 33 independent ones.** Measured this session: league size and
      superflex cannot move a gap-based quantity at all (0 of 41/125/197/114 gaps change while
      the top QB price moves 48.51 → 163.06), because `bpa` is points minus a per-position
      constant. Check which axes the quantity under study can actually see before sizing a run.
- [ ] **#218 — the #222 Phase 0 reproduction was deferred and never re-run** (312 picks).
- [x] **#242 — the round count every instrument used was the wrong question, fixed before the
      re-run.** `len(roster_positions)` is "how many slots are there", not "how many rounds does
      the startup draft run". The two differ by the IR slots, which are never drafted. It was
      invisible because `fixtures/sleeper_capture.json` — the league the battery and the roster
      proof both draft — has no IR at all, so the two agree there. Two real captures disagree:
      F&F 29 slots − 3 IR = 26 (and the real startup ran exactly 26 rounds), GSOP 33 − 4 = 29.
      `league_config.draftable_slots` now answers it, in the one home that already answered
      "does this slot start anybody". **No battery arm's round count changes** — no mock league
      carries IR — and a test pins that rather than my having checked once.

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

The battery (Gate 1) is mechanical — ~~about three hours, and **it is running now**~~.

**DATED 2026-09-12: that run FINISHED**, and nothing is running now. It is the
`BATTERY_2026-09-12_scoring_aware_full_99f9f76` in the banner above, it found `#247`, and `#247`
was repaired at `3e9c074` — so **one more run is owed**, against the repaired engine, at ≈6.5h.
A present-tense "it is running now" left in a checklist is the kind of sentence a reader acts
on; it is struck rather than deleted, per this file's own convention.

Gate 2 is still the real gate, but `#245` narrowed it rather than removing it. The trade the
ruling is about — current-season points for dynasty asset value — is real and still unratified;
what changed is that its PRICE is not a single number. It costs 5–11% on the fixture's formats
and *earns* 1.04% on Fourth and Forever, at a matched round count. So the question is no longer
"is this trade worth it", which had one answer, but "is this trade worth it IN THIS LEAGUE" —
and the engine already comes out on the right side of it in the owner's. Until the next cut
separates rulebook from roster shape, "does it draft well?" answers: **yes, narrowly, in the
league you actually play — and no, in the generic ones we had been certifying against.**

Everything in Gate 3 is either downstream of that ruling or small enough to land in a day.
