# v4 production gate — criteria, written BEFORE the gate runs

> **THE DATE ON THIS FILE IS THE POINT OF IT.** These criteria are committed before any gate
> instrument is built or run. That ordering is the single mechanism protecting the gate from the
> person operating it, and it is not a formality: **every one of the 97 commits between `v2-freeze`
> and `v3-freeze` was written by me**, and the only things that have read them are instruments I
> also wrote. A bar I can move after seeing results is not a bar.
>
> **Structure and §5, §7 and §10 come from the owner's own draft** and are kept close to as written.
> What is added here is repo-specific: mutation VALIDITY rules, defect classes drawn from this
> repository's documented failures rather than from a generic list, the independence mitigations,
> the split-lens requirement, and a concrete out-of-scope list. Each addition names the incident
> that earned it.

---

## Purpose

`v3-freeze` (`eac7491`) is the frozen validation candidate: every known finding repaired, all seven
owner decisions resolved. It claims completeness of KNOWN work and explicitly does not claim
correctness under an adversary.

**v4 is the final engine version upon which the production implementation may be built.** Its
purpose is not to establish that the engine is mathematically perfect or that no future defect can
exist. It is to establish, through independent and measurable evidence, that the frozen state has
survived a final adversarial examination and that all in-scope findings have been resolved without
introducing regressions.

### The blocking question, and it follows from that purpose

Because production gets built ON v4 rather than beside it, the test that decides whether a finding
blocks the gate is not "is this a defect" but:

> **Would repairing this later force a change to something a production build already rests on?**

A defect in a number's value is repairable later without disturbing anything above it. A defect in
the SHAPE of what the engine promises — a row schema, an absence convention, a basis pairing, a
module boundary — is not, because production will have been written against it. The first is
recorded; the second blocks. §5 and §9 apply this test, and §11 states exactly what production is
being invited to rest on.

---

## 1. Gate structure

Three instruments with three different jobs. **They may not be substituted for one another**, and
the reason is measured rather than stylistic: at v2 a "the suite is green" claim coexisted with three
invariant mutations surviving that suite (`dbc4d4a`).

| instrument | job | what a pass proves | what it CANNOT prove |
|---|---|---|---|
| **fresh blind adversarial pass** | discovery | an independent reader found nothing blocking | nothing about anything they did not read |
| **full battery re-run** | regression | no established contract broke | **nothing about undiscovered defects** — it is deterministic over fixed fixtures |
| **mutation gate** | detection power | the verification layer can actually see corruption | nothing about defects of a class not injected |

The battery is **confirmatory only**. Its result may never be reported as evidence that no
undiscovered defect exists, and may never substitute for the blind pass.

---

## 2. Fresh blind adversarial pass

### Territory, fixed before the pass begins

Recorded here so it cannot be narrowed afterwards. The scope is `v2-freeze..v3-freeze`:

| | |
|---|---|
| commits | **97** |
| files changed | **160** (+36,001 / −5,522) |
| production modules touched | **36** |
| new test modules | **31** |
| core decision surface | `draft_room.py` +714/−112, `pick_synthesis.py` +306/−16, `data_merger.py` +151/−12, `lineup_optimizer.py` +132/−2, `draft_strategy.py` +131/−43, `player_universe.py` +126/−5, `league_config.py` +119/−9 |

Particular attention to code that changes prices or valuation; changes demand or replacement;
changes positional or eligibility treatment; changes roster reachability or capacity; gates
candidates or valuation components; changes risk adjustment; changes the SEMANTICS of an existing
output; or translates engine state into a downstream-facing value.

### Blind to conclusions, not to territory

The pass **may** be given the frozen commit, the diff range, repository structure, documentation,
and this scope. The pass **may not** be given expected findings, proposed repairs, prior Fable
conclusions, assertions about which areas are safe, a list of suspected defects, or any desired
conclusion. `evidence/blind_pass/` stays denied — a reader who has seen the forbidden-path list
knows where the answers are kept.

Bounding territory is itself a mild briefing, and that cost is accepted and recorded rather than
denied.

### SPLIT LENSES, not one mandate repeated

`evidence/blind_pass/MANDATE_V2.md` established this and the reason is measured: *"this codebase is
deterministic, and so is an audit of it."* Readers given one lens converge on one region and re-find
each other's findings. So each pass gets the same preamble, constraints and reporting rules, and a
**different lens**, each told that others cover the rest.

**The lenses are derived from the diff's own structure, not from my sense of risk** — which is a
deliberate constraint on the one person who should not be choosing where an auditor looks:

| lens | territory, taken from what actually changed |
|---|---|
| A | the repriced paths — 3.1's percentile population, 2.6's demand solve, 2.3's kicker/DEF repricing, D8's proportional health discount, D4's growth conversion |
| B | the gates and backstops — 2.2's config gate, 3.2's dedicated groups, D7's flex-reachable groups, `feasibility_first`, `unfieldable_last` |
| C | the consolidated vocabularies — every Tier 4 `#126` merge, and whether a single home now hides a disagreement the two homes made visible |
| D | **the instruments themselves** — `prose_names`, `assertion_floors`, `suite_taxonomy`, `invariant_registry`, `render_trace`, `doc_index`, `invariant_confirmation`, audited as code rather than as authority |
| E | the absence contract's new sites — 2.5's repairs, `config_ambiguities`, `rival_premium_basis`, and every number added since v2 that travels with a basis |

Lens D matters most and is the one an author would least naturally commission: those instruments are
what certified the other four lenses' territory, and at v2 exactly that class of instrument was found
reporting false positives about its own detection power.

### What counts as a finding

Actionable only when the reviewer identifies: the affected behaviour; the concrete code path
producing it; why it contradicts an existing requirement, invariant, contract or documented intent;
and a reproducible case. Speculation without a demonstrated contradiction is not a failure. A
finding that merely proposes different product behaviour is not a failure unless that behaviour is
already a defined requirement — it is disposition **E** (§5).

---

## 3. Battery gate

One identified commit, recording exact commit, arm count, pick count, findings, known certified
survivors, and any deviation from the previous certified result.

**Passes when** every previously certified contract holds; no new unexplained finding appears; known
intentional survivors remain correctly classified; and no finding requires an unrecorded repair.

A known survivor must be reconciled against its documented contract, not auto-treated as a defect.
As of `v3-freeze` the known survivors are the two `HEAVY_IDP` arms' dedicated-bound findings — one
roster per arm above `slots + 1` — recorded at 3.2 and confirmed again in
`evidence/d7_flex_depth/`.

**The result may not be described as proving general correctness.**

---

## 4. Mutation gate

The primary quantitative check on detection power, and the only gate instrument whose value does not
depend on who designed it.

### Defect classes, drawn from this repository's own history

A generic mutation list measures a generic test suite. These eight classes are the defects that
have ACTUALLY occurred here, each with its register item, so the gate measures whether the layer
catches the failures this engine really produces:

| # | class | the incident that earned it |
|---|---|---|
| 1 | **absence contract broken** — `None` becomes `0.0` | `#187`, `#193`, `#203`; PUP priced fully fit |
| 2 | **basis severed from its number** | `#166` — a quantity crossing a layer without the thing that gives it meaning |
| 3 | **one concept, two homes, allowed to diverge** | `#126` — the whole of Tier 4; PUP in one vocabulary and not the other |
| 4 | **a backstop made advisory** | `#154`/`#155`, `#30` — nine defenses on a one-DEF roster |
| 5 | **a constant applied in the wrong unit** | D8 — `RISK_ADJ` meaning 18% of a bounded scale, then 18 points |
| 6 | **vocabulary membership gap** | PUP recognised by `GAMES_MISSED_FLOOR` and unknown to `RISK_ADJ` |
| 7 | **a guard made vacuous** — threshold outside its quantity's reachable range | 3.4 — a bar above every value it could be handed |
| 8 | **counting-rule error** — subset vs intersection, primary bucket vs eligibility | `#172`, 3.2 — multi-eligible players counted at no position at all |

At least **two mutants per class, at different sites**, on the surface changed since `v2-freeze`.
The exact mutation set is recorded before execution.

### VALIDITY — the rule this repository paid for

**A mutant that fails everything has not been caught; it has measured nothing.** `dbc4d4a` recorded
the v2 pass finding all three invariant mutations SURVIVING the engine suite while two committed
verdicts claimed they were caught — the verdicts came from an unrelated module failing under
`--failfast`. `#254` records the mirror: a mutation that dropped a sort key and left `ascending` at
the old arity, so pandas raised before a board existed and every board-touching test errored, scored
as "caught" while testing nothing.

So every mutant must first be shown VALID, reusing `invariant_confirmation.INCONCLUSIVE`. A mutant
returning any of these is **replaced, never counted**:

* `ANCHOR FAILED` — the source moved; the mutation never applied
* `MUTANT DOES NOT PARSE` — every test fails for the wrong reason
* `MUTANT CANNOT BUILD A BOARD` — runs as Python, raises before a board exists
* `MUTATION IS INERT` — runs, changes nothing, there is nothing to catch

A mutant is valid only when it parses, builds a board, changes observable behaviour, and the
baseline is green. **Detection must be attributed**: the specific test or invariant that failed is
recorded, and "the suite went red" is not an attribution.

### Pass condition

**Classes 1, 2 and 4 — absence contract, basis pairing, backstops — admit no survivors. One survivor
is a gate failure.** These three are the failure modes that put a false number in front of a person,
which is this repository's own definition of the catastrophic case, and all three are part of what
production is invited to rest on (§11).

**Classes 3, 5, 6, 7 and 8 report a measured catch rate, not a pass mark.** No percentage threshold
is set, deliberately: an invented "≥80%" would be exactly the chosen constant `#56` forbids. Each
survivor is instead triaged individually by the blocking question in §5, and each is recorded with
the test that SHOULD have caught it named.

Results are reported as measured detection behaviour. **Test count is not evidence.** "4,076 tests"
is a number; "caught 9 of 12 injected defects, and here is which three survived" is evidence.

---

## 5. Finding classification

Every finding receives one disposition, **assigned before deciding whether code changes are
required**:

**A — Confirmed defect.** Violates an established requirement, invariant, contract or intended
behaviour. → Repair before v4 **if** it also fails the blocking question (§Purpose): would repairing
it later force a change to something production rests on? If it would not, it may be recorded as
**B** with that reasoning stated.

**B — Valid but out of scope.** A real issue outside the predeclared territory or the product's
requirements. → Record. Do not repair before v4.

**C — Expected behaviour.** Intentional and supported by an existing contract or certified rule. →
Document or reconcile. No repair.

**D — Instrument error.** Produced by an incorrect probe, fixture, interpretation or measurement
method. → Correct the instrument. **Do not change production behaviour on the strength of an
erroneous finding.** This category is not hypothetical here: during the v3 cycle alone, a sweep read
a report field that was an integer rather than rosters, a separability test compared against the
wrong population's minimum, and a sampling artifact produced "0 of 7" where the true figure was 5 of
39.

**E — Product decision.** No established requirement exists and several behaviours could reasonably
be intended. → **Do not silently choose during the gate.** Escalate to the owner. `#56` routes chosen
magnitudes here and the gate does not repeal it.

---

## 6. Repair rules

A confirmed in-scope defect may be repaired during the v4 cycle. Every repair is followed by:
targeted verification of the motivating defect; regression verification of adjacent behaviour;
mutation verification where the repair changes a detectable contract; and applicable battery
verification. A repair that creates a new finding reopens that surface.

**No repair may be justified solely by making a test green.**

**Measurement outranks a ruling when measurement shows the ruling cannot produce the required
behaviour** — the owner's standing rule, recorded in full with its limits at the head of
`OWNER_DECISIONS_PENDING.md`. Its bar is a recorded measurement, not a preference; a ruling merely
disagreed with stands; and every exercise is logged in the ruling's entry, the commit, and a test.

### The bar does not move

If, after seeing results, I believe a criterion here is wrong, that is a **rule change**: it requires
the owner, is recorded with its reasons, and **does not apply retroactively to the run in progress**.
A dispute of a finding must be made with a MEASUREMENT recorded in `evidence/`, never with an
argument. If the measurement does not support the dispute, the finding stands.

---

## 7. Reopening conditions

The gate reopens after apparent completion only if: a required criterion was not actually satisfied;
a confirmed in-scope defect remains unresolved; a repair produced a regression; a required mutation
survived; the production-facing engine contract differs from the validated one; or a finding
classified **C** is later demonstrated to violate an established requirement.

**The following do NOT reopen it** — this list is the anti-v5 clause and is as binding as the rest:

* a hypothetical edge case without demonstrated impact
* a new product preference
* an alternative implementation that is merely different
* a finding explicitly classified **B**
* a future enhancement
* a desire to improve an already-certified behaviour with no evidence of failure

---

## 8. Out of scope, named now rather than argued later

Predeclared so a gate finding touching them is disposition **B** on arrival. Each already carries its
reasoning in `OWNER_DECISIONS_PENDING.md`; none is a silent debt.

| item | why it is out of scope |
|---|---|
| **D9 / `#50`** — the replacement equation | the owner's call; both of the item's own premises now corrected. Blocks `#21` and D7(a) |
| **D1(b)** — `rival_premium`'s own basis vocabulary | the borrow is pinned; divergence fails loudly |
| **D2(c)** — per-term config refusal | the eventual shape; Tier 3-sized |
| **D4(b)** — a conversion derived from first principles | the current one is derived from the engine's own rate for that input |
| **D7(a)** — the depth factor from `#30`'s baseline | blocked behind D9 |
| **D8(a)** — re-deriving the bounded caps | needs a "which spread" decision; a measurement campaign, not a gate item |
| **`#21`** | blocked behind D9 |
| **the 16 board inversions** | pinned as a watched figure; team terms are SUPPOSED to be able to reorder a board |
| **every chosen magnitude** (`#56`) | `FLEX_GROUP_DEPTH_FACTOR`, `Doubtful`'s assumed half-game, 1.3's tie-break — disposition **E**, owner's call |
| **performance** | no stated requirement exists |
| **vendor or season data changes** | the "new inputs" clause of the stopping rule, not a defect |

---

## 9. Freeze condition

v4 is complete only when **all** of: the blind pass is complete across every lens; every finding has
a recorded disposition; every confirmed in-scope defect is repaired; the regression battery passes;
the mutation gate passes on classes 1, 2 and 4 with survivors elsewhere triaged and recorded; the
full suite passes **at the exact candidate commit**; documentation and indexes are current
(`doc_index --check`, `assertion_floors --check`); the final commit is uniquely identified; and the
production-facing outputs are unchanged in meaning from the validated contract except where a gate
repair explicitly required it.

`FREEZE_RECORD_V4.md` records what it rests on, what it does NOT claim, and what was left open —
v2's three headings, kept because they are what made the v2/v3 numbering error correctable at all.

---

## 10. What v4 claims, and does not

**Claims:** the findings identified through the v3 validation cycle are dispositioned; confirmed
in-scope defects are repaired; the repaired system passed the defined regression battery and
mutation gate; the candidate satisfies this predefined gate.

**Does not claim:** mathematical perfection; absence of undiscovered defects; correctness for
requirements never defined; that the battery is a discovery instrument; that the mutation suite
proves absence of defects; that future use cannot expose new edge cases.

---

## 11. The stability contract — what production may build on

The point of the blocking question, made concrete. v4 promises these are stable; production may be
written against them, and a later change to any of them is a breaking change rather than a repair:

1. **The absence contract.** An unpriced quantity is `None`, never `0.0`. A measured zero is a
   finding; an absent one is silence. (`#187`, `#61`, `#203`)
2. **Number and basis travel together.** Any quantity with a companion basis is emitted with it, and
   the basis describes THAT quantity. (`#166`, `#193`, D1)
3. **The board row schema.** `BALANCED_BOARD_COLUMNS` and the upside branch's row shape, including
   which terms are absent rather than zero in each mode.
4. **The decision boundary.** What a `PickSnapshot` freezes, and that consumers read the snapshot
   rather than recomputing. A consumer that recomputes can disagree with the board on screen.
5. **The backstop ordering.** Feasibility outranks fieldability outranks value, and neither backstop
   is a value term — they reorder selection and move no price.
6. **Named conventions are labelled.** A constant that was chosen rather than derived says so at its
   definition. Production may rely on being able to tell the difference.

Anything NOT on this list — a specific number's value, a term's weight, an ordering inside a tier —
may change in a later development cycle without breaking the contract.

---

## 12. After v4

The engine becomes the accepted production baseline. The verification apparatus stays in the
development repository; the production artifact may be built from the validated state without
shipping it.

Defects found through actual use become production issues, accumulate, and **do not automatically
invalidate v4**. A future development cycle begins when accumulated evidence or a material new
requirement justifies reopening the engine.

The objective is not to establish that the engine can never be improved. It is to establish a
sufficiently strong, measured and reproducible boundary at which further improvement becomes future
development rather than unfinished release work.
