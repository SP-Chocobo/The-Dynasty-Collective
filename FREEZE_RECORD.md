# v1 Freeze Record — what was frozen, on what evidence, and what it does not claim

> **`#53`, reconciliation and freeze candidate.** This is the record, not the checklist.
> `FREEZE_CHECKLIST.md` is what was left *before* the freeze; this is what the freeze rests on.
> `POST_AUDIT_PLAN.md` remains the numbered record and wins over any status flag anywhere
> (`#292`).
>
> Written to be read cold, by someone who was not in the room — including `#52`'s blind
> adversarial pass, which reads this repository unbriefed.

**Candidate commit:** `b6748f8` on `claude/fantasy-football-control-center-ff6qlu`.

**FROZEN AND MARKED 2026-09-18: tag `v1-freeze` at `6599b1e`**, published as a GitHub
**pre-release** — deliberately, because `#52` has not run and `#162`'s order is *freeze before
blind audit*; labelling this production-ready before the adversarial pass would invert the
sequence, and the repository is public.

The tag is three commits past the candidate named above. **No engine or test code differs
between them** — `git diff --name-only b6748f8 v1-freeze` returns no `.py` file at all, only this
record, `FREEZE_CHECKLIST.md`, `POST_AUDIT_PLAN.md`, `DOC_INDEX.md` and one inert config
(`.claude/blind-pass.settings.json`). So the tree frozen is the tree measured; the extra commits
are the act of writing this down. **Quote `6599b1e` as the freeze, and `b6748f8` as the commit
every measurement in §2 was taken against.**

**This is the first real tag this repository has ever had.** Every prior freeze marker is a
BRANCH, because the agent credential cannot create tags — re-verified this session, a tag push
fails the same way a branch delete does. The owner's access has no such limit, which `#290`
established and this tag demonstrates.

---

## 1. The one sentence this record exists to prevent anyone skipping

**The engine has no demonstrated edge over market consensus on any ruler independent of its own
objective, and the data in this repository cannot establish one** (`#288`).

That is not a hedge and it is not a failure. It is the honest ceiling of what was measurable here,
and everything below is bounded by it. Anyone quoting a margin out of this repository — including
the large ones — is quoting something this sentence qualifies.

## 2. What IS established

### Legality, across the whole format matrix (`#284`)

`BATTERY_2026-09-17_gate1_15fcf2c`: **34 arms (33 independent), 5,652 picks, 0 structural
findings**, 14,460.7s. `commits_present: ['15fcf2c']`, `carried_forward: []` — one commit, zero
arms inherited from an earlier run, so every arm was drafted by the engine it claims to describe.
The committed predecessor could say neither.

Compared field by field against that predecessor, **34 of 34 arms are identical**. The `#247`
unfillable-flex family, which `FREEZE_CHECKLIST` called the only blocker, **did not reproduce**.

**What this establishes:** the engine never produces a structurally invalid draft across the
matrix. **What it does not:** anything about quality. A draft can be perfectly legal and badly
played, which is why `#285` exists.

### Quality, against a mixed field of named styles (`#285`, `#289`)

`evidence/smoke_seats/` — pre-registered at `9273a2c` **before the runner existed**, so the
acceptance criteria could not be fitted to the result. 6 formats, 68 seat runs, priced pool 481.

Against **market-consensus ADP**, on the three formats where that control is correctly specified:

| format | engine − `adp` | paired t | reading |
|---|---|---:|---|
| `12T_ppr` | −7.73 (−0.35%) | −0.74 | indistinguishable from zero |
| `10T_ppr` | −14.64 (−0.63%) | −2.45 | small but systematic |
| `12T_ppr_TEP` | +11.70 (+0.51%) | +1.31 | indistinguishable, leaning ahead |

Against the two **projection-led** styles, in the same arms: **+3.3% to +4.1%**, nearly everywhere.

**`adp` is a strong opponent, not a baseline** — first of all styles in all six formats, and it
beats the greedy points-maximiser **on that maximiser's own ruler** by 2.34–5.39%. A market
ordering carries scarcity and lineup-shape information a projection sheet does not. The owner's
freeze condition was that losses only count as good drafting if the opponent is strong; it is,
and the worst clean deficit is **−0.63%, about 0.9 points per week**.

**What this establishes:** the engine drafts at the level of the strongest realistic opponent
available here, and clearly above naive projection-led drafters. **What it does not:** an edge —
see §1.

### The prior contradiction, resolved by measurement (`#287`)

`FREEZE_CHECKLIST` carried `#205` (engine loses 67 of 68 on `points`) and `#245` (engine wins 10
of 12) as an open contradiction. Settled by re-running **`#205`'s own design** at HEAD — uniform
`control_pick` field, one process, one code version, toggling only the field:

- **UNIFORM** (`#205`'s design): engine wins **12/12, +3.67%**
- MIXED (`#285`'s design): engine wins 11/12, +2.13%
- against `control_pick` alone: +3.67% uniform vs +3.56% mixed — the same number

Field homogeneity is not the explanation. **`#205`'s deficit is a property of commit `8cee942`
and does not reproduce at HEAD.** The contradiction resolves in `#245`'s direction, on `#205`'s
own terms rather than by argument.

## 3. What is NOT established, stated as plainly as the wins

### The ceiling (`#288`) — why §1 cannot be resolved by more work here

Two rulers exist. `points` is what you FIELD, and it is where the tie with the market sits.
`cdme` is what you OWN — **the engine's own objective**, where a win is a tautology by
construction. They correlate at r=0.241, so they are different questions, not two views of one.

A tie on `points` is therefore ambiguous between two readings this instrument cannot separate:
the engine correctly trading present-season points for future asset value — **which is what a
dynasty engine is supposed to do** — and the engine having no edge at all.

Separating them needs a third ruler on a dynasty horizon. **It cannot be built from anything in
this tree**, because every multi-season quantity is already an engine input:

| quantity | already read by the engine | where |
|---|---|---|
| `proj_3yr` | yes | `time_horizon_adj`, which scales `RISK_ADJ` per player |
| `trade_value` | yes | a `bpa_source` — `position_relative_trade_value_vor` |
| `rank` | collinear with both | `#165` |

A ruler built from any of them scores the engine on a transformation of its own input. An
independent ruler requires **realized subsequent-season outcomes the engine has never seen** —
external data, the same blocker class as `#49`.

### The market control is mis-specified in half the formats (`#288`)

The ADP table is built from one field, `adp_dd_ppr`: **PPR only, no superflex variant and no
standard variant.** So in both superflex arms and in `12T_standard`, the only market-like style
in the field is playing the wrong board. `12T_standard` is the one format where the engine beats
`adp`, and that win is against a PPR-ordered board in a standard league.

**Consequence: the engine does not cleanly beat a correctly-specified market control in any
format measured here.** The three 1QB PPR arms are the only clean comparisons, and they are the
parity table in §2.

### One arm is a proven strawman (`#285`)

In `12T_standard`, `need_first` opens with a QB **48 times out of 48** and `points_need` **36 of
36** — 100% of round-one picks, in a **one-QB league**. That is RULE 6's original failure mode,
reproduced by two of three styles. The engine opens RB 12/12. Its +7.09% and +7.28% margins there
measure the gap between a sane drafter and a broken one, and nothing else. **Treat
`12T_standard` as uninformative about quality.**

## 4. Known limitations carried INTO the freeze

Each is documented rather than repaired, with a stated reason. None is hidden.

### `#184` — superflex QB pricing (bound restated at its measured size)

`compute_draft_board` passes `startable_floors={"QB": ...}` in every superflex league, and that
branch sets the QB level from the CLIFF, unconditionally, without consulting demand. Two
constants answer one question and the floor wins every time.

**The engine loses `cdme` — its own objective — to both projection-led styles in both superflex
arms**: `12T_ppr_SF` 2/12 (−10.27%) and 1/12 (−17.50%); `10T_ppr_SF` **0/10 at −26.91% and
−30.39%**. That half is **not** confounded by the ADP mis-specification, because neither style
reads an ADP table. The `points` half is mild — it beats or ties both projection-led styles and
loses only to the mis-specified `adp`.

Mechanism, consistent with the above: those styles open QB at 44–50% in superflex, the engine at
8% and 60%. **The engine underprices QBs as assets while still fielding a comparable lineup** —
asset total suffers, starting lineup does not.

`#206`'s escape hatch is closed: that clause held the deficit might be a simulation artifact
because the chairs "produce twelve straight QBs in round one." Round-one QB rates measured per
style are 0–60%. The field is realistic and the engine still loses the asset ruler in it. **The
benchmark improved and the result got worse.**

**Why it still does not hold the freeze:** the repair changes what replacement level MEANS in a
superflex league — that is `#50`, owner-held and gated on `#49`. And per §3, a `cdme` deficit
cannot be converted into a claim about real-world cost.

### `#206` — `survival_probability` is not calibrated, and the engine REFUSES rather than pretends

Engine Brier 0.16127 against a constant predictor's 0.14224 on real picks, worst exactly where
the threshold reads. The response is **enforced in code, not documented**: `decision_regime`
cannot return `"decisive"` while `SURVIVAL_IS_CALIBRATED` is False (landed `364042a`). Across all
34 Gate 1 arms, `decisive` calls went **1,654 → 0**. A miscalibrated confidence signal that
refuses to speak is a different object from one that speaks wrongly.

### `#223` / `#225` / `#231` / `#232` — the mode transition concept is undefined

Ruled KNOWN-OPEN, not wired. Wiring an undefined concept before a freeze invents a decision
rather than repairing a defect, and `#233` measured that the repair buys little: the counterweight
only DEFERS, 8 of 8 deferred players harvested by the upside half, composition conserved 101=101.
Round 15 remaining a global calendar index where a per-seat roster state is measurable is carried
as a named limitation.

### `#146` — bye week is admissible in REDRAFT ONLY, and the wiring is NOT done

Ruled (`#257`); the wiring needs the dynasty/redraft boundary, a test that fails on the old
behaviour in each mode, and absence honoured for the 0.9% with no bye week. **Carried as
un-wired**, not as done.

## 5. Accepted as blocked-external (`GATE 6`)

None is an engine defect. Each needs something this machine cannot reach, and each is accepted at
freeze rather than holding it.

- **`#88` / `#143`** — `api.sleeper.app` is denied by the network policy, 403 at CONNECT,
  evidenced. This is not cosmetic: it is the same condition that produced `#291` below.
- **`#120` / `#109`** — provider metering and served-model identity need live SDKs.
- **`#49` / `#210`** — real K/DEF/IDP startup boards; Sleeper supplies IDP without stat lines.

`#49` is load-bearing beyond its own scope: it gates `#50` (the `#184` repair) **and** it is the
class of input §3 says an independent ruler would need.

## 6. What licenses this freeze

| gate | state |
|---|---|
| Full suite | **3,111 tests, `OK (skipped=1)`** at `c073f66`, re-verified on every commit since |
| Suite in CI, **with network** | **3,111 passing**, run 539, 9m49s — see the caveat below |
| Gate 1 | `#284`, 34 arms, 0 structural findings, one commit, zero carried arms |
| Gate 2 | ruled 2026-09-12 (`#252`) |
| Gate 5 | all owner decisions ruled |
| Prose/doc guards | `prose_names`, `doc_index`, `suite_taxonomy`, `assertion_floors`, `render_trace` all green |

### The CI caveat, which must not be rounded off (`#291`)

**The automated gate was restored at `2da0b0e` on 2026-09-17. It was not continuous.**

`render_trace.py --check` had been comparing against a fixture recorded where Sleeper is 403, so
it could never be reproduced by a runner that has network. Every branch showed `0/2` red,
including freeze markers two weeks old. `#113` listed CI as a shipped guarantee at `850b8b5`
while it guarded nothing, since **at least 2026-09-02**.

Worse than the red X: the fixture was recorded with an **empty** free-agent pool, so the twelve
calls rendering that view were never covered — the instrument built to catch coverage-that-looks-
like-coverage had exactly that defect inside it.

Two things follow, and both belong in this record rather than in a footnote:

1. **Every commit between 2026-09-02 and `2da0b0e` was verified by local suite runs only.** Those
   runs were real and are cited above, but the automated gate was not a second opinion during the
   period this evidence was gathered.
2. **Until run 539, every full-suite execution on record was network-DENIED** — the exact
   condition that hid the defect. The `full` job is gated `if: github.event_name != 'push'`, so
   pushes run 845 of 3,111 tests, and with the fast tier red the full tier was skipped entirely.
   Run 539 was dispatched deliberately to close that hole **before** a freeze merge could discover
   it. It passed. No other network-dependent behaviour exists in the suite.

## 7. What this freeze does NOT license

- **It does not license an edge claim.** See §1. Marketing, a sale process (`#54`), or any
  outward-facing description must not convert "drafts as well as the market" into "beats the
  market."
- **It does not license calibrating any constant to the evidence here.** Pre-registered and kept:
  one capture, simulated fields, and the owner's standing caveat that league settings vary
  enormously. `#56` governs — constants are DERIVED, and a bound is not a threshold.
- **It does not license superflex confidence.** `#184` is a named, measured, un-repaired
  limitation, larger than previously recorded.
- **It does not freeze the UI track.** `#181`, `#36`, `#137`, `#173` are a parallel track that
  `#164` already classified as not gating the engine.
- **It does not pre-empt `#52`.** The blind pass runs after this record, unbriefed and unscored
  (`#161`/`#52`, confirmed `#259`).

### `#52` ACCESS CONTROL — this document is the cheat sheet, and must be withheld from it

**Owner instruction, 2026-09-18.** Whoever steers the blind pass must **deny it read access** to
the briefing material, or failing that instruct it by name not to open these files. Denial is
preferred; an instruction is only as good as compliance.

| withhold | why |
|---|---|
| `FREEZE_RECORD.md` | this file — states every finding, every limitation, and exactly where the engine is weak |
| `FREEZE_CHECKLIST.md` | its top block is a complete current-state briefing |
| `POST_AUDIT_PLAN.md` | the numbered register — every measurement, withdrawal and correction |
| `evidence/smoke_seats/` | the pre-registration and result state the quality finding and its weaknesses outright |

**A hazard introduced on 2026-09-17 makes "just tell it not to look" insufficient by itself.**
Every long-lived document in this repository now carries a top-of-file pointer naming
`FREEZE_CHECKLIST.md` and `POST_AUDIT_PLAN.md` as where current state lives. That pointer was
added for ordinary readers — and for a blind reader it is a signpost to the answers: whichever
file it opens first will tell it where the cheat sheet is. **An instruction that does not name
these paths explicitly will be undone by the first document Fable opens.** Access denial at the
tool layer does not have this failure mode, which is why it is preferred.

The point is not secrecy. A blind pass exists to produce the one read of this repository that was
not shaped by the people who built it, and every sentence above is shaped by exactly that.

## 8. Reconciliation — where the documents disagreed, and which way each resolved

`#53` is a reconciliation, so the disagreements are listed rather than silently harmonised.

| disagreement | resolution |
|---|---|
| `#205` (67/68 loss) vs `#245` (10/12 win) | `#245`'s direction — `#205` does not reproduce at HEAD (`#287`) |
| `FREEZE_CHECKLIST` said `#247`'s family "is not dissolved" | dissolved — `#284` reproduced none of it |
| `FREEZE_CHECKLIST` said "one more battery run is owed" | discharged by `#284`; struck in place |
| `FREEZE_CHECKLIST` said "one ruling and one battery run stand between here and a freeze" | both spent; `#53` was the only item left |
| `#184` bound stated as −1.83% to −1.97% on one arm | restated at measured size; disposition unchanged |
| `#135` said tag refs "are 403 here" | it is the AGENT's credential scope, not the repo or network (`#290`) |
| Session task list vs `POST_AUDIT_PLAN` | register is authoritative (`#292`) — and the task list did not survive a container reclaim, while the register did |
| `#285` said `adp` "has no superflex variant" | narrower and worse: PPR-only, so `12T_standard` is mis-specified too (27th correction) |
| `#290` claimed two branches deleted | they were not, then they were; three dispositions, struck in place (28th correction) |

### Corrections made during this pass, counted

Two published claims of mine were wrong and were struck in place rather than edited away: the
**27th** (`adp`'s mis-specification was narrower than reported, which *weakened* the engine's
case) and the **28th** (a branch deletion recorded before it was attempted, and refused). Both
are in `POST_AUDIT_PLAN` at their original entries.

---

## The shortest honest summary

**The engine is legal everywhere it was tested, drafts at the level of the best realistic
opponent available, and has no demonstrated edge over that opponent — and no instrument in this
repository can settle whether that is correct dynasty behaviour or an absence of skill.**

Everything else in this record is either evidence for that sentence or a named exception to it.
