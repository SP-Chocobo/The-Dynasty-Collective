# Post-Audit Execution Plan — reconciled

**Status: planning document. No production code has been written for this phase.**

> **Rulings recorded 2026-09-01.** Four decisions settled by the operator and folded in below:
> the Insight Foundation is **promoted ahead of Insight**; Insight scope stays at **Top 5** as
> Plan v2 specified; **#114 and #116 move into the Foundation**; the **Master Manual is retained**
> before freeze. Marked **[RULED]** at each point. Remaining open: **D4, D5, D7, D8**, plus the
> two policy halves that arrived with #114 and #116 (**D9, D10**).

Inputs reconciled here:
1. the completed 25-section architecture audit (`ARCHITECTURE_AUDIT.md`, Passes 1–21) and its
   41 open register items;
2. **Post-Audit Plan of Attack v2** (Phases 1–11);
3. the operator's revised 12-step sequence.

`main` stays frozen at `9fb5102`. All work continues on `ui-authority-pass`.
Baseline entering this phase: **`d7902ac`, 1459 tests OK (1 skip), clean tree.**

---

## Part 1 — Where the three inputs disagree

Four genuine conflicts. None is silently resolved here.

### 1.1 Insight scope: Top 5, or Top-N?   **[RULED — D1: Top 5.]**

Plan v2 is explicit and repeated: *"exactly the Top 5 eligible deterministic candidates"*,
*"Insight remains fixed at Top 5 scope."* The revised sequence says *"a fixed number of the
highest-ranked candidates"* and lists **"exact Top-N scope"** as a contract item still to be
settled. The revised sequence reopened a decision Plan v2 had closed; **the operator has re-closed
it at Top 5** (fewer if fewer than five eligible candidates exist). The board may display 7, 8, 10
or more; Insight's scope stays fixed at 5 regardless.

### 1.2 The targeted delta audit moves from before implementation to after

* **Plan v2:** Phase 3 design contract → **Phase 4 targeted delta audit** → Phase 5 implement.
* **Revised sequence:** step 3 contract → **step 4 implement and test** → step 5 delta audit.

This is not cosmetic. Plan v2 audits a *design*; the revised order audits *running code*. This
audit's entire method argues for the revised order — twelve of my own findings this audit were
wrong until measured, and a boundary that does not exist yet cannot be probed. But part of Phase 4
genuinely belongs at design time: anything whose answer would *change the contract* is cheaper to
find before the contract is written.

**Recommendation: split it.** A short design-time review against the boundaries the audit already
established (authority, least-privilege, snapshot provenance, truncation, prompt injection), then
the real measured delta audit after implementation. Recorded as decision **D2** — still open,
though the reconciled sequence below is written assuming the split.

### 1.3 The Master Manual is absent from the revised sequence

Plan v2 **Phase 9** requires a human-readable "dummy manual" for a non-programmer maintainer
*before* v0.1 is declared, and Phase 10's freeze checklist includes *"Verify the Master Manual
describes the actual system."* The revised 12-step sequence has no manual step: it runs smoke-out
(9) → full Opus audit (10) → freeze (11) → Fable blind audit (12).

Dropping it also removes a freeze criterion, and Phase 11 explicitly hands the blind auditor *"the
system and documentation."*

**[RULED — D3: retained.]** The Master Manual is restored to the sequence before freeze (Step 10),
and Plan v2's Phase 10 verification item stays in the freeze checklist.

### 1.4 Phase 8 splits into two steps

Plan v2 bundles the aggressive Opus audit and ~20 varied draft simulations into one phase. The
revised sequence separates them (step 9 smoke-out, step 10 cross-discipline audit) and drops the
"~20" figure. **No conflict** — the split is an improvement, since the smoke-out should *feed* the
audit rather than run beside it. Adopting the revised split, and keeping Plan v2's ~20-draft
figure as the smoke-out's floor.

---

## Part 2 — The register, triaged

The audit's own §24 seven-way classification maps almost exactly onto the three buckets requested.
41 open items.

### A. Mandatory — demonstrated defects or structural gaps (13)

Not policy. Each is either a measured defect or a mechanism that exists and is not wired.

| Item | What is actually wrong | Evidence |
|---|---|---|
| **#92** | `PickSnapshot` carries **no identity field** at all | 8 fields, none an id/hash/version |
| **#101** | `snapshot_is_current` exists, works, and has **zero production callers** | 4 references repo-wide: 3 docstrings + 1 comment |
| **#102** | Cross-session lost update in every per-league store | demonstrated §11.4b |
| **#99** | Provider output truncation undetectable | §9.6 |
| **#100** | Nothing meters tokens, cost, or latency anywhere | §10.4a |
| **#104** | No deterministic abort-vs-degrade rule on upstream failure | §14.6a |
| **#105** | Four resource knobs, no enforcement surface | §15.3–15.5 |
| **#107** | User overrides reach valuation unattributed | §16.3 |
| **#110** | Two demonstrated silent-meaning-change paths | §17.5 |
| **#113** | Nothing runs the checks, pins inputs, or hashes anything | §19 |
| **#114** | Late-draft pricing collapse: 27.8% of an 18-round draft decided by a player-id tiebreak | §20.6, 1,293 decision points |
| **#118** | Players-DB 24h cache undisclosed in the freshness manifest | §22 |
| **#119** | `time_horizon_adj`/`risk_adj` reach no production consumer; board drops `bpa_source`/`confidence` | §24, AST + exhaustive grep |

### B. Policy decisions — surfaced, never chosen here (14)

The §24 "missing contract" class, verbatim: **#50, #53, #54, #55, #71, #93, #94, #97, #98, #104\*,
#112, #114\*, #116, #117.**

(\* #104 and #114 appear in both buckets: each has a mechanical half and a policy half. #114's
defect is measured; *what the board should do when pricing information is exhausted* is a decision.)

### C. Needs evidence before it can be actioned (8)

**#49, #51, #52, #86, #87, #88, #109, #115** — every one blocked on *access* (a K/DEF/IDP board, a
reachable `api.sleeper.app`, an SDK that reports the served model, an unrun pass), not on a choice.
Do not schedule these as work; schedule *acquiring the input*.

### D. Optional / deferrable polish (6)

**#36, #48, #91, #96, #103, #106, #108, #111** — real, none blocking.

---

## Part 3 — The finding that changes the sequence

**Insight, as specified, cannot be built on the current foundation.** This is not a style
objection; it is measured.

The operator's own Insight requirements include:

> *"Insight results should become part of the reviewable record for that draft, **bound to the
> exact PickSnapshot** that generated them."*
> *"Historical Insight results must remain readable against the snapshot they were generated from
> and **must never silently regenerate against a later board state**."*
> *"Prytaneum should have explicit visibility of **available Draft PickSnapshots** as context."*

Measured state of the foundation those three sentences require:

* **`PickSnapshot` has no identity.** Its 8 fields are `pick_label, round, my_roster_id,
  candidates, user_selected_player_id, picks_consumed, data_freshest_date, decision_regime`.
  There is no id, hash, or version. **You cannot bind a record to an object that cannot be named.**
* **`PickSnapshot` does not persist.** It is built per-rerun and lives in session state. There is
  no "available Draft PickSnapshots" for Prytaneum to see, because there is no store.
* **`snapshot_is_current` — the exact staleness check "never silently regenerate" needs — exists,
  is correct, and is called by nothing in production.**

Nine further contract clauses the operator requires map one-to-one onto open register items:

| Required Insight contract clause | Blocked on |
|---|---|
| snapshot identity & stale-result invalidation | **#92**, **#101** |
| in-flight cancellation / obsolete-result discard | **#92**, **#101** |
| persistence and retention | **#92** |
| multi-tab / multi-client synchronization | **#102** |
| cost / token metering | **#100** |
| maximum output length + truncation behavior | **#99** |
| API failure behavior + deterministic fallback | **#104** |
| strict input/token budget, timeout, cooldown/debounce | **#105** |
| provider/model attribution | **#109** *(externally blocked — the contract must state what is actually recordable, not what is wished for)* |
| exact deterministic context envelope | **#119**, **#93** *(and must not reopen #18/R90)* |

**Both Plan v2 and the revised sequence schedule this foundation *after* Insight** — the revised
sequence puts #114/#115/#116/#118/#119 at step 6, and the persistence/metering family is unscheduled
in both. That is the building before the foundation.

**Two further couplings, from measurement rather than principle:**

* **#114 → Insight will confabulate.** In the late draft, 27.8% of picks are decided by a
  player-id tiebreak — i.e. the ordering among those candidates carries *no information*. Insight's
  stated job is "comparing them against one another and explaining the important differences."
  Asked to explain a difference that does not exist, a language model will produce one. Insight must
  either be told when it is in that regime, or be withheld there. **This is the sharpest
  ENGINE OWNS TRUTH / AI EXPLAINS TRUTH violation available**, and it is reachable on the very
  first draft.
* **#116 → Insight will speak an ambiguous unit.** The internal scale is not the 0–100 band, and
  the board's own prose qualifies its unit correctly only 3 times in 5. Insight puts numbers into
  fluent prose, where a wrong unit is far harder to spot and correct than on a label.

---

## Part 4 — The reconciled sequence

Renumbered. Deltas from the operator's 12 steps are marked **[CHANGED]** with the reason.

**Step 0 — Consolidate and triage the register.** *(operator step 1)* — **done above.**

**Step 1 — Insight Foundation. [CHANGED: promoted ahead of Insight — RULED]**
The mandatory subset that Insight's own contract clauses require, **plus the two items whose
defects would corrupt Insight's output**:

*1a — substrate (gates every later clause):* **#92** snapshot identity + store, **#101** wire
`snapshot_is_current`. Gated on **D4** (retention/storage policy) before the store lands; the
identity work itself is not.
*1b — operational envelope:* **#102** per-league store lost update, **#100** metering, **#99**
truncation detection, **#104** abort-vs-degrade, **#105** resource limits. #104 and #105 each carry
a policy half that comes back as a decision with measured options attached.
*1c — output integrity:* **#114** (Insight must never be asked to explain an ordering that carries
no information) and **#116** (Insight must not state an ambiguous unit in prose). Both moved here by
ruling. Both have a policy half — **D9** and **D10** — which I will bring with evidence rather than
ask blind.

Nothing in 1a/1b is a new product decision beyond D4. This unblocks ten contract clauses.

**Step 2 — Settle the Insight contract.** *(operator step 3)* — all 18 clauses, now answerable
because step 1 made the substrate real. Decisions **D1, D5–D8** below.

**Step 2a — Design-time boundary review. [CHANGED: split from operator step 5]**
The subset of the delta audit that could change the contract: authority, least-privilege
(must not reopen R90/#18), snapshot provenance, prompt injection, deterministic/AI separation.
Cheap; runs against the contract, not code.

**Step 3 — Implement Insight minimally, test thoroughly.** *(operator step 4)*

**Step 4 — Measured delta audit.** *(operator step 5)* — the rest of Plan v2 Phase 4, now against
running code: truncation, staleness, persistence, replayability, cost, provider attribution,
concurrency.

**Step 5 — Remaining deterministic work.** *(operator step 6)* — **#115**, **#118**, **#119**,
**#107**, **#110**, **#113**. *(#114 and #116 moved to Step 1c by ruling D6.)*

**Step 6 — Gold Wyrm identity / UI rebuild.** *(operator step 7)* — including establishing how I
can inspect the live site or a local preview **before** substantial UI work. That access question
is worth resolving early since it has a lead time; raised as **D7**.

**Step 7 — Provider/league integration matrix.** *(operator step 8)* — map, rank, recommend for
v0.1. No blind implementation.

**Step 8 — Full-system smoke-out.** *(operator step 9)* — ~20 varied drafts as the floor, plus
adversarial configs, malformed data, provider failures, stale snapshots, concurrent clients.

**Step 9 — Cross-discipline Opus audit.** *(operator step 10)*

**Step 10 — Master Manual. [CHANGED: restored from Plan v2 Phase 9 — RULED D3]**

**Step 11 — v0.1 freeze candidate.** *(operator step 11)*

**Step 12 — Fable-tier blind full-spectrum audit.** *(operator step 12)*

---

## Part 5 — Decisions required before work starts

| # | Decision | Blocks | State |
|---|---|---|---|
| **D1** | Insight scope | Step 2 | **RULED — Top 5** (v2's original; fewer if fewer exist) |
| **D2** | Split the delta audit, or keep it whole? | Step 2a | open *(sequence below assumes the split)* |
| **D3** | Master Manual before freeze? | Step 10 | **RULED — retained** |
| **D6** | Do #114/#116 move into the Foundation? | Step 1c | **RULED — both moved** |
| **D4** | Insight storage/retention: where records live, what evidence projection is kept with the prose, what is cleared at draft conclusion | **Step 1a** | **OPEN — gates the first work item** |
| **D5** | Does Insight receive research/external findings at all? (safe default: no) | Step 2 | open |
| **D7** | How I reach the Gold Wyrm visual reference — live URL, local build, exported assets | Step 6 | open *(long lead time; worth settling early)* |
| **D8** | Is historical Insight prose admissible as Prytaneum context? (already ruled: never engine truth; labelled if admitted) | Step 2 | open |
| **D9** | #114's policy half: what the board does when pricing information is exhausted and ordering is arbitrary | Step 1c | open — evidence first |
| **D10** | #116's policy half: what the display contract declares the internal scale to be | Step 1c | open — evidence first |

---

## The first concrete work item

**#92 — give `PickSnapshot` an identity and a store**, scoped to exactly what Insight's contract
requires and no further:

1. a deterministic content-derived identity on `PickSnapshot` (extending the mechanism **#111**
   notes already exists for one artifact, rather than inventing a second one);
2. a persisted, append-only per-draft snapshot store;
3. **wire `snapshot_is_current`** — the function is already written and correct; #101 is one call
   site plus the discard/annotate/warn decision, which is the *same* choice #99 and #101 were both
   parked on.

It is the keystone: **§23** named #92 the root of 4 of its 23 architectural mandates; **§25** ranked
it #1; and it is the only "missing persistence" item in the register. Three of Insight's stated
requirements are unbuildable without it.

**Gated on D4** (retention/storage policy) before the store lands. The identity half — deriving a
content hash over the frozen snapshot and pinning it with a test — is not gated and is where work
begins on greenlight.

### What #92 must not do

Recorded now so the implementation cannot quietly drift into them:

* **It must not extend `PickSnapshot`'s meaning.** Identity is derived *from* the frozen fields;
  it adds no new decision input. `team_acquisition_value` must be byte-identical before and after,
  proven the way §25 proved the ingestion boundary — plant, then measure that nothing moved.
* **It must not invent a second identity mechanism.** #111 records that content-hash identity
  already exists for exactly one artifact (the benchmark report fingerprint). Extend that, don't
  fork it.
* **It must not become engine truth.** The store is a record of what was shown, never an input to
  what is computed. No CDME module may import it — enforceable the same way
  `test_cdme_ingestion_boundary.py` enforces the research boundary today.
* **It must not silently trust an unstamped snapshot.** `snapshot_is_current` already reports an
  unstamped snapshot as *not* current rather than assuming; wiring it must preserve that posture.

---

# Step 1a — delivered

**Commit `76be588`. Suite 1459 → 1489, no regressions. No valuation number changed.**

| Piece | State |
|---|---|
| `content_hash.fingerprint` | **done** — one shared primitive, byte-identical to the `_fingerprint` it replaces (#111) |
| `pick_synthesis.snapshot_identity` | **done** — pure, total, 1.36 ms / 72 candidates |
| `pick_synthesis.stamp_is_current` | **done** — the staleness rule, now askable of a restored record (#101) |
| `draft_history` store | **done** — per-league, append-only, content-addressed; #102 structurally impossible |
| Evidence projection | **done** — carries the policy's required fields, plus the anchor provenance the board drops |
| Import boundary | **done** — CDME may never import `draft_history`, enforced |
| **Production call site** | **NOT done — deliberately. See D11.** |

## Why there is no call site yet, and the decision that decides it

The substrate is complete and proven, but nothing in production records a snapshot, because
**what should trigger a recording is a product decision I should not make silently.** Two
readings of the policy give materially different stores:

* **Record every board built.** A complete history of everything the Draft Room showed —
  including boards for other managers' picks and every pool-scope toggle. Largest store, and
  it captures decision points that never got an Insight.
* **Record on binding only** — when an Insight (or a debate) is actually generated against a
  board. Closest to the policy's own wording, *"Insight records and their associated
  PickSnapshots"*, and much leaner. But since Insight does not exist yet, wiring this today
  would be a no-op, and building its plumbing ahead of the contract is exactly what the
  greenlight said not to do.

A third reading sits between them: record the user's **own** picks always, and other boards
only on binding — the draft's real decision history without the noise.

**Recorded as D11.** It belongs in the Insight contract (Step 2), not in the substrate.

**Consequence to state plainly:** #92, #101 and #102 are **not closed** by this commit. Their
mechanisms exist, are tested, and are unblocked; they acquire their first production consumer
when D11 is settled. #111 *is* effectively closed — the content-hash mechanism now covers two
artifacts through one implementation.

## What Step 1a bought

Ten Insight contract clauses that were previously unbuildable now have a substrate:
snapshot identity, stale-result invalidation, in-flight obsolete-result rejection, persistence,
retention, per-league scoping, historical readability, Prytaneum snapshot visibility, and the
`#102`-free store the multi-tab clause needs. None of them is *implemented* — they are simply
no longer blocked on a missing foundation.

## D11 — ruled: deferred to the Insight contract

The substrate stays **trigger-agnostic**. No production recording trigger is added in 1a.

**Stated preference for the eventual contract**, to be written into it at Step 2 rather than
implemented now: *record the user's own picks always, plus any PickSnapshot that becomes bound
to an Insight, debate or research result.* Explicitly NOT: every board reconstruction, and not
other managers' picks merely because a board was rendered.

Two consequences the contract must carry, recorded now so they are not rediscovered later:

* "My own picks always" needs a definition of *when* a pick is the user's own and final — a
  board is rendered while the user is on the clock and again after they pick. The recorded
  snapshot should be the one the decision was made against, which is not automatically the last
  one rendered.
* "Plus bindings" means the binder is the trigger, so every future binder (Insight, debate,
  research) must record through the same path or history acquires holes silently.
