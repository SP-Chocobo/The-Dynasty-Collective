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

- [x] **RULED 2026-09-16 (owner): GENERIC IS THE CERTIFICATION BASIS; F&F IS RECORDED AS
      CORROBORATION.** The engine ships to many leagues, so certifying against one owner's
      rulebook would overfit the freeze record. F&F's complete 12-seat proof agrees with the
      generic result (points 10 of 12, +1.04%) and is therefore carried in the record as
      named, evidenced corroboration — not as the basis. This answers the item's own
      complaint that the previous state *"picks neither and says nothing"*.
- [x] ~~**Decide whether the freeze's evidence should be re-measured on F&F's rulebook**~~, or
      whether the freeze deliberately certifies the engine against a generic full-PPR
      environment and records F&F as out of scope. Either is defensible; the current state
      picks neither and says nothing, which is the part that is not defensible.

      **ANSWERED BY MEASUREMENT, AND THE RUN IS COMPLETE (reconciled 2026-09-16).** This
      line said *"IN FLIGHT"* for two days after the run finished, while the same document
      reported its result four times (the headline table, the `#245` row, arm `C`, arm `C2`).
      `evidence/roster_proof/ROSTER_PROOF_FF_fourth_and_forever.json` is `complete: true`,
      12 of 12 seats: **points 10 of 12, +1.04%** (engine mean 2860.82 against control
      2831.39), asset 12 of 12. **The first pre-registered branch below is the one that
      fired**, so on the evidence the strong claim holds in the league actually being
      played. What remains open is only the SCOPE half of this item's own question — whether
      the freeze record certifies against F&F's rulebook or names it out of scope — and that
      is an owner's call, not a missing measurement.

      ~~**IN FLIGHT — this is being answered by measurement rather than by decision.**~~
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

- [ ] **#150 — RULED 2026-09-16 (owner): THE FULL 34-ARM RUN IS THE FINAL PRE-FREEZE
      GREENLIGHT, AND IS NOT TO BE SPENT ON INTERMEDIATE STEPS** *("just not wantonly in
      intermediate steps before we think its ready for the freeze unless there is a very
      good reason")*. This SUPERSEDES my recommendation to widen the carry-forward to five
      axis-spanning arms now — that was exactly the intermediate spend the ruling forbids.
      The 3-arm carry-forward therefore STANDS as the interim position, with its scope
      stated rather than dressed up. **The binding consequence: the full run certifies the
      tree that produced it, so every behaviour-changing change must land BEFORE it, and
      only prose and tests may follow it.** Ruling `#251` (do not re-run the 33-arm battery
      as-is) is not reversed — a deliberate final greenlight is a different act from a
      re-run, and the freeze record should say which one it is.
- [ ] **#150 — THE HEADLINE BELOW IS FALSE AND IS KEPT ONLY AS THE RECORD.** Two runs exist and
      neither is withdrawn: `BATTERY_2026-09-12_scoring_aware_full_99f9f76` (33 formats, 5,340
      picks) and `BATTERY_2026-09-13_gate1_1770ef2` (**34 formats, 5,652 picks, complete,
      `total_findings: 0`, `constant_axes: []`**). Both certification columns are satisfied: zero
      invariant findings in all 34 cells, and all six dependent sections present per cell.
      **Measured 2026-09-16: that evidence CARRIES FORWARD to the current tree.** Three arms
      re-drafted on `db3cecb` — `8T_standard` (112), `8T_standard_SF` (120),
      `CAPTURE_fourth_and_forever` (312), 544 picks — are identical on all eleven comparable
      fields, so the five post-battery engine commits (**#86 included**) move nothing. Comparator
      validated first: 8/11, 9/11, 10/11 differences against other arms, 0 against itself. Scope
      stated: **3 of 34 arms**, chosen for the regimes most likely to expose `#86`, not a claim
      about all 34. What remains genuinely open here is the owner's call on whether a further run
      is wanted before freeze — the evidence itself is not missing.
- [ ] ~~**#150 — re-run the mass battery. Both committed runs are WITHDRAWN.**~~
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
- [x] **#218 — CLOSED at `35ac788`, and this line was stale for two days.** The reproduction ran
      and is EXACT: **312 of 312 picks match** the committed baseline (`9b01a52`) on
      (overall, roster_id, player_id) — the same players in the same slots, not merely the same
      composition. Discriminating, not a coincidence any draft would produce: the other `#222`
      arms differ from this draft in 36-37 of 48 per-seat composition cells. It also fired under
      the condition that made it mandatory (`PHASE0_COMPLETE.md:126` deferred it *"until the first
      change to the pricing path"*).
- [x] **#242 — the round count every instrument used was the wrong question, fixed before the
      re-run.** `len(roster_positions)` is "how many slots are there", not "how many rounds does
      the startup draft run". The two differ by the IR slots, which are never drafted. It was
      invisible because `fixtures/sleeper_capture.json` — the league the battery and the roster
      proof both draft — has no IR at all, so the two agree there. Two real captures disagree:
      F&F 29 slots − 3 IR = 26 (and the real startup ran exactly 26 rounds), GSOP 33 − 4 = 29.
      `league_config.draftable_slots` now answers it, in the one home that already answered
      "does this slot start anybody". **No battery arm's round count changes** — no mock league
      carries IR — and a test pins that rather than my having checked once.

## GATE 2 — ✅ RULED 2026-09-12 (#252, owner)

> **The exchange rate is CONFIGURATION-DEPENDENT and there is no canonical one.** Present-season
> points versus dynasty asset value has no single rate across the configuration space; outcomes
> are reported per cell and no cell's number is the engine's verdict.
>
> Answerable now because the framing dissolved rather than the question being answered: `#248`
> re-measured the headline deficit at −0.28% (the −5.03% was 190 commits stale), `#250` swapped
> only the rulebook and the sign flipped (−0.84% → +1.04%), and `#251` established such outcomes
> are configuration-dependent by construction — they are measured against a ruler built from the
> league's own scoring settings.
>
> **This releases the cluster below.** Each item is now worked on its own merits rather than
> against a deficit. Full ruling: `POST_AUDIT_PLAN.md` (#252).

## GATE 2 — the cluster it released (#50 / Phase 3)

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

- [ ] **#231 / #232 / #222 — the mode boundary re-prices the flex, and what a repair would buy is
      SMALLER than this line used to claim.** Three corrections, all from POST_AUDIT_PLAN, all of
      which this line carried in their superseded form until `#260` checked it:
      - ~~"upside mode implements half its stated intent and inverts the other half"~~ — **20th
        withdrawal** (`POST_AUDIT_PLAN` §6714). The facts stand; the framing weighed one
        uncommitted comment against the founding architecture, four contract statements and a
        pinned test. The code was not violating an intent — the constant's comment described the
        code wrongly, and the comment has since been corrected in place.
      - ~~"TE +68.58 at the flex"~~ as a flat figure — **21st withdrawal** (§6644). The charge is
        recomputed at every board state because the levels drain: TE **68.58 opening / 60.03 at
        pick 100 / 89.14 at pick 150**; WR **0.00 at every state measured**. 68.58 was the
        opening-board value, and the boundary sits nowhere near the opening board.
      - ~~"the largest unactioned behavioural finding"~~ — §6764 rules the opposite: **"The TE
        excess is not removable by restoring roster awareness in the back half."** `#233` measured
        that the counterweight only DEFERS — 8 of 8 players it defers are harvested by the upside
        half, composition conserved 101 = 101. Both roster-aware arms overshoot WR to 42.0 against
        a human 37.1. **"The live question is #229's — cross-position comparability below starter
        depth — not the mode switch."**
      What remains genuinely open is the DECISION beneath it, not the repair: the transition
      concept is undefined (`#223`/`#225` below), and round 15 is a global calendar index standing
      in for a per-seat roster state the engine can measure and never has.
- [x] **#223 / #225 — RULED 2026-09-16 (owner): DOCUMENTED AS KNOWN-OPEN, NOT WIRED.**
      Wiring an undefined transition concept before freeze would invent a decision rather
      than repair a defect, and the measurement says the repair buys little: `#233` found the
      counterweight only DEFERS (8 of 8 deferred players harvested by the upside half,
      composition conserved 101 = 101), and POST_AUDIT_PLAN §6764 rules the TE excess is not
      removable by restoring roster awareness. **No behaviour change, so this does not gate
      the greenlight battery.** The live question stays `#229`'s cross-position
      comparability, not the mode switch. Round 15 remaining a global calendar index where a
      per-seat roster state is measurable is carried as a named limitation.
- [ ] ~~**#223 / #225** — the mode transition concept is genuinely missing, for lack of a decision.~~
      The TE decision at the boundary is a real near-tie on (points − displaced).
- [ ] **#153** — two clamps, not one: the 4WR collapse is the flex-share clamp, not `NEED_BONUS_MAX`.
      Measured and understood; not repaired. **Located on re-verification (2026-09-16)**: the
      clamp is `NEED_BONUS_PER_FLEX_SHARE * min(flex_remaining, 1)` at `draft_room.py:3380`, so
      a position owed three flex shares is charged for one. Still live, still unrepaired — the
      line is open for the right reason.
- [x] **#86** — `round(expected_taken)` **REPAIRED**: the curve is read at a fractional index.
      This item's own wording was **stale** — `cliff_protection` stopped reading
      `positional_forfeit` at `#160`, so the knife-edge never reached that flag. The real defect
      was an absence-contract one: rounding sent every expectation below 0.5 to `drop=0`, so the
      forfeit read **exactly 0.00 while a fraction of a player was expected to go** (4 of 44
      observations, all WR; 0.48 → 0.00 and 0.60 → 9.44). **NOTE FOR THE OWNER: this overrode a
      standing deferral** (CDME_CONTRACTS Part 3 and the characterization test both said *open
      product question*); the evidence is recorded there and reverting is a one-line change.
- [x] **#216 (B4)** — **PINNED, and NOT a live defect.** `#70` found and repaired the eleven real
      crossings by reading; this pass found no twelfth. What was missing is that nothing held the
      distinction afterwards. `ordinals.py` gives the three registers one home —
      `VALUATION_RANK` (the pool), `DRAFT_POSITION` (the clock), `VENDOR_RANK` (the vendor),
      separated by what RECOMPUTES them — and `test_ordinal_registers.py` holds the registry to
      the codebase and one real producer to its declared domain. **The first version of that test
      was a decoration**: a class named `ARealProducerMatchesItsDeclaredDomain` built `rank_by_id`
      from a dict literal, so it tested its own fixture's arithmetic. Control: against a producer
      mutated to emit 0-based ranks, the old test passed 11/11 and the rewritten one fails 6. Now
      driven by `_build_opponent_boards` on a real pool; 13 tests, mutation-checked 3/3
      (zero-based, gapped, empty). Python still permits any int anywhere — this narrows the next
      crossing's blast radius, it does not abolish it, and the pin says so.
- [x] **#167 — CLOSED at `0bc75a9` + `574db9c`; this line was stale, and its framing was wrong
      twice over.** The ruling already existed (*"out of engine math, stays in the debate prompt"*),
      and establishing what engine math `reach_label` was in turned out to be the whole answer:
      **none**. `quantity_readers.scan()` gave it `verdict=observable, scoring_readers=[]`, and all
      eleven non-test references were docstrings, display f-strings, a dataclass field, a snapshot
      carrier or a history column. `574db9c` then removed it everywhere; today only a historical
      docstring mention and a test asserting its ABSENCE remain. **The "0 of 36" phrasing is also
      withdrawn** — it reads as an effect too small to matter, when there was never a wire: the
      ablation toggled a quantity no scoring path reads. A null about a wire that does not exist
      closes the question; a weak null about one that does invites a re-measurement.
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
      **MEASURED, NOT REPAIRED** (register entry + `evidence/survival_mechanism/`). The 0.00 is
      2.3e-8, not a rounding artifact, and it has TWO independent causes with different
      remedies: take-probability mass (a bound the model violates, repairable as arithmetic,
      lifts survival to 0.314 in one step) and rival agreement (every board built by one
      valuation, so the engine's own #1 is rank 1 on all of them — needs rival modelling, and
      that is blocked on #49/#88). Both halves pinned by `test_take_model_coherence.py`.
      **MEASURED AGAINST REAL DRAFTERS (owner-ruled, 2026-09-16).** 270 human picks from a
      complete 12-team superflex startup: the rank-1 player on the picking team's engine board is
      taken **3.0%** of the time against the model's **55%**. Median rank taken is **32**; 86% of
      picks fall outside the table's five keys. At the observed rate survival over this item's 22
      intervening picks is **0.512** — the player survives, which is what the draft did. So the
      0.00 is not mass arithmetic; the per-pick probability is ~18x too high at rank 1. Instrument
      controlled: a synthetic rank-3 drafter recovers **48/48**. **My own recommended repair
      (head-only normalisation, rank-1 0.455) is WITHDRAWN — 30th — off by 15x, while the
      full-mass answer I warned against lands within two points of reality.** **NOT CALIBRATED**:
      the capture's LIMITS forbid setting a constant from one league, so this is a direction and
      evidence for **#50**, not a patch. `evidence/take_model/`.
      **What this gate still needs is the OWNER's call on whether the arithmetic half is wired
      before the freeze or deferred to #50** — the measurement no longer blocks the decision.
- [x] **#183** — **REPAIRED**: six absence breaks in the Dock, found by rendering absent-field
      scenarios through `_format_candidate` rather than by reading it. Five reachable (an unpriced
      row carries no price while `estimate_survival` still answers for him, so a real percentage
      sat above the literal string `None`); the sixth, a `need_bonus` of None, raised TypeError —
      the Dock died rather than misreported. Each absence now denies the reading it invites, and a
      measured 0.0 is still reported as a measurement. **The original six were never enumerated,
      so no claim is made that these are the same six.** `test_dock_absence_contract.py`, 9 tests,
      mutation-checked 4/4.
- [x] **#112** — **REPAIRED**: `absence_kind` names WHICH absence left a row unpriced, carried on
      both board serializations, into `CandidateSnapshot`, and rendered on the NOT PRICED line
      where a person reads it. **Measured: of 1,119 rows, 638 are unpriced and every one is the
      coverage gap** — zero rows of the one kind that would justify ORDER LAST. The gap is real;
      the population is not. **My first implementation put an absence kind on PRICED rows** (it
      keyed on the trade-value fallback branch, confidence 35.0) — a latent breach invisible to
      every test and to the cross-tab written to find it, because that branch has zero rows; the
      classification is now derived from the source label. **The decision boundary caught my
      second mistake**: importing `draft_room` into `pick_debate` would hand the debate layer
      `compute_draft_board`, so the vocabulary crosses via `pick_synthesis`' re-export like the
      four before it. Whether ORDER LAST is right for an entirely *unknown-not-bad* population is
      a **#50** question this makes askable, not one it answers. `test_absence_kind.py`, 23 tests,
      mutation-checked 7/7.
- [x] **#119** — **REPAIRED**: `time_horizon_adj` and `risk_adj` are carried to the snapshot and
      rendered beside the team-value decomposition, so `universal_value = bpa + horizon + risk` is
      explained where a person reads it. `quantity_readers` independently confirms both moved from
      `decomposition` (zero readers) to `observable`, `scoring_readers` still empty — it discloses,
      it does not wire. **This item's second clause was stale**: the board does NOT drop
      `bpa_source`/`confidence`; both reach `pick_debate`. 12 tests, mutation-checked 4/4.
- [x] **#211** — **TRIGGER DISCHARGED, pin retained.** Gate 2 was ruled (`#252`), which is the
      re-read condition this item carried. The finding stands — `starter_value` sums an asset
      LEVEL over a lineup, so it ranks positional breadth — and Gate 2's ruling *reinforces* the
      pin rather than reopening it: "no cell's number is the engine's verdict" is exactly the
      status a reported metric has. Re-verified rather than recalled: no production module reads
      it (`roster_diagnostics` computes its own `starting_lineup_value` and merely cites this one
      to explain a shared exclusion). Stays **KNOWN-OPEN-ACCEPTABLE**. No code change.

## GATE 5 — Owner decisions for the freeze record (no code)

- [x] **#55** — `pick_necessity` stays OBSERVABLE, no selection authority. Ruled.
- [x] **#184** — documented as a bounded limitation; does not hold the freeze. Ruled.
- [x] **#188** — vocabulary ruling executed and closed.
- [x] **#175** — REJECTED: no derivable threshold; `CLIFF_HIGH_RATIO` unchanged.
- [x] **#146** — RULED admissible in REDRAFT ONLY (`#257`). **The wiring is Gate 3 and is
      NOT done**: it needs the dynasty/redraft boundary, a test that fails on the old
      behaviour in each mode, and absence honoured for the 0.9% with no bye week.
- [x] **#160 — RULED 2026-09-16 (owner): VOID THE `CONST-A*` PREFIX ENTIRELY.** The collision
      was with a ghost: `#161`'s full-history search established that **no `BLIND-A1` has ever
      existed**, and `CONST-A1/A2/A3` appear only in POST_AUDIT_PLAN prose with no constant
      behind them. So there is nothing to rename around. The prefix is retired and each
      constants question is referred to by the item that owns it (`#56`'s constants
      contract). Prose only, no code. A numbering scheme whose only job was to disambiguate
      from something that does not exist is worse than no scheme.
- [x] **#149 — RULED 2026-09-16 (owner): WRITE DOWN WHAT ALREADY EXISTS; DECLINE THE
      ARCHITECTURE CHANGE.** The policy is now stated where the store lives
      (`attachments.py`'s module docstring) rather than inferred from a neighbouring module:
      reference material keeps the **artifact**, credentials **extract and discard**, and the
      rule separating them is whether a human will look at the thing again (a secret has no
      viewing value). Retention stays *"until a human deletes it"* but as a **choice** —
      curated reference material has no natural expiry, so a timer would delete what the user
      still wants. The **single-local-user assumption is now stated for attachments**, which
      is the only thing that makes the unfiltered management view defensible; `app.py:775`
      had stated it for `.env` and nothing had stated it here. **Client-side custody is
      DECLINED** as an architecture change, not a freeze setting. Gates the freeze RECORD
      only — uploads reach no price and no pick.
- [x] ~~**#149** — **THE PREREQUISITE IS DISCHARGED; ONLY THE RULING IS OPEN.**~~ ~~THE ITEM HAS
      NO WRITTEN BASIS~~ — that headline (`#257`) was true when written and is now false. The
      owner's ruling was *write the missing entry from measurement first, then rule*, and
      `498884b` wrote it: `POST_AUDIT_PLAN.md:8540+`, every fact read out of the code rather
      than carried from an earlier audit, with **four ruling questions named at `:8594`**. The
      entry's own finding is one the item's title did not anticipate: the app already answers
      *extract vs artifact* TWICE in opposite directions (reference material keeps the raw file
      forever and extracts nothing; credentials parse in memory and never persist the upload),
      and neither is written down as a policy. So what blocks this item is a decision, not a
      missing basis. Gates the freeze RECORD, not the engine — uploads reach no price and no
      pick.
- [x] **#98** — RATIFIED (b): allowlist what feeds the composite, prose stays free.
      `source_policy.py` already implements it (`#132`); the ruling is recorded, not built. (`#257`)
- [x] **#158** — DONE (`#259`), and it found a dropped ruling. There are **EIGHT** docket
      rulings, not ten (POST_AUDIT_PLAN: *"The eight freeze rulings"*, read back from the
      artifact store). Seven were carried; `#161/#52`'s **UNSCORED** was not, and is now
      restored above. **This item's number also COLLIDES**: POST_AUDIT_PLAN's `#158` is
      *"an unpriced leader crashes the Draft Room"*, a repaired defect cited by `#173` —
      the same two-namespaces-one-number defect `#160` exists to void.

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
6. **#52** — the blind adversarial pass runs **after** the freeze, **stays unbriefed**, and
   is **UNSCORED**. The docket ruled all three (`#161/#52`, 2026-09-06); this line carried
   only the first two until `#259` checked it. Unscored is not a detail: a scored blind
   pass invites tuning toward its rubric, which is the one thing an unbiased read cannot
   survive.
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
