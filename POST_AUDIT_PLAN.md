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

---

# Step 1b — the operational envelope

**No Insight code. No valuation change. Six provider callers wired; every `⚠️` string byte-identical.**

## The structural finding that shapes all four items

`#100`, the recoverable half of `#99`, and part of `#109` are **one gap, not three**: every provider
caller returns a bare `str`, so the response object — which carries token usage, the stop reason
and the served model id — is discarded inside the function.

The obvious repair is a richer return type. **Rejected on measurement:** that value is passed
straight through by **12 call sites** up into `app.py`, and §14 established the strongest property
this app has — every caller returns a `⚠️ …` string rather than raising, so one dead provider
cannot take out the panel. Rebuilding that chain to carry a new type would risk that property to
gain bookkeeping. The metadata is recorded **beside** the call instead, in `provider_meter`, and
nothing there can alter what a caller returns.

## Delivered

| Item | State |
|---|---|
| **#100** metering | **done** — per-call provider, model requested *and reported*, tokens, latency, outcome; `mark()`/`since()` scopes one operation's calls; ring-buffered at 500 |
| **#99** truncation | **done (detection)** — four states: complete / truncated / blocked / **unknown**. A provider that did not say is never recorded as having said "complete" |
| **#105** limits | **partly done** — a request timeout now exists where none did; the retry knob is explicit and deliberately **off** |
| **#104** abort-vs-degrade | **characterized, not changed** — as scoped |

**Truncation has four states, not two**, for the same reason §18/#112 gave: collapsing "did not
report" into "complete" is the reading that does damage, and it is exactly what an SDK shape change
(#110's class) would produce.

**A never-attempted call is now separable from a failed one.** §14 recorded that four distinct
causes collapse into one signal. The half that *can* be separated with certainty now is: no API
key, or the SDK absent — the request never left the machine, so it cost nothing and could not have
been truncated. Measured working: 6 of 6 calls recorded as `not_attempted` with their own reasons.
§22's marker still stays agnostic about a call that *did* run; that ambiguity was always real.

## #104, measured

All eight failure combinations of the three upstream chairs, and the behaviour is **identical in
every one**: 4 calls made, Moderator always runs, always returns a real verdict. `abort`,
`degrade`, `minimum`, `quorum`, `threshold` — **zero occurrences** across both modules.

**The policy is "always degrade, never abort", and it was never chosen** — it is what falls out of
calling four chairs in sequence. The edge worth deciding: **with all three upstream chairs failed,
the Moderator still synthesizes a verdict from three unavailability markers.** R12/R17 make those
markers say *treat as MISSING, never as a finding that there is nothing to report*, so the chair is
told it has nothing — but nothing stops a confident verdict, and it renders beside the error count
rather than instead of it. Pinned as a characterization test to invert on repair.

## A premise this step corrected

§14/§15 concluded *"this app performs no retries."* What was actually established is narrower:
**this repo contains no retry code.** Whether retries *happen* was never measured — the provider
SDKs carry their own defaults that this app never set. The old claim was a property of the source
text rather than of the running system, which is the trap this audit named repeatedly and then fell
into. Both characterization tests are corrected rather than loosened, and the guards still hold:
the limit logic was moved into `provider_meter` so the crude substring scan over `llm_engine` /
`pick_debate` keeps its full value.

## The honest limit on this step's evidence

**None of the three provider SDKs is installed in this environment.** So every response shape here
is a stand-in: the tests prove `provider_meter` *reads* a given shape correctly, and cannot prove
what a live provider returns. Two consequences, both designed for rather than hoped past:

* Limits are applied through `supported_kwargs`, which **asks the SDK** rather than assuming a
  kwarg name. A wrong name would raise, be caught by the caller's own handler, and silently
  disable that provider outright — so an unaccepted knob is **dropped and recorded** in
  `applied_limits`, never guessed at. A limit that silently fails to apply is worse than none.
* `#109` moves from *blocked* to *capture wired, verification outstanding*: the served-model echo
  is recorded where present, but whether a given SDK resolves a floating alias there is unverified.

**New task: verify the metering and limit surfaces against live SDKs** on a machine where they are
installed — usage field names, stop-reason vocabularies, timeout kwarg names and units, and whether
`model` echoes a resolved id. Until then the ledger may under-report, and it reports absence as
absence, which is the correct failure direction.

## Decisions surfaced (none taken)

| # | Decision |
|---|---|
| **D12** | `REQUEST_TIMEOUT_SECONDS` — 180 s is provisional. Every caller enables server-side web search, so a search-and-synthesize turn is legitimately slow |
| **D13** | `CLIENT_MAX_RETRIES` — today the SDK defaults apply and the app's "no retries" claim is unverified. Set 0 to make the claim true, set a value deliberately, or leave SDK behaviour alone |
| **D14** | #104's floor — is there a level of upstream failure below which the panel should decline to synthesize rather than degrade? |
| **D15** | What the app *does* on a detected truncation, now that it can detect one — discard, annotate, or warn. Same choice shape as #99/#101, and it should be settled once for all three |

---

# Step 1c — #114 and #116, measured

**Characterization only. No production code changed, no copy renamed, no scale normalized.**
Two test files added (19 tests), both written to be inverted on repair.

## #114 — where pricing dies, and what the board does next

Measured on one 12-team × 18-round draft against the committed baseline, 216 picks.

### Where it becomes exhausted — exactly

| | |
|---|---|
| Unpriced rows first appear | long before they matter — **139 of a 203-row pool by pick 131**, correctly ordered last, changing nothing |
| A position's demand hits zero | stepwise: 139 unpriced holds through pick 142, jumps to **153 at pick 143** |
| **Pricing dies completely** | **pick 155 (round 13): 0 priced rows of 179** |
| After that | **every remaining pick in the draft** is decided by the tiebreak alone |
| Picks with a tied top score | **78 of 216 (36.1%)** |

**Two regimes hide under that one percentage**, and conflating them would misdirect the repair:

* **Rounds 6–9 — genuine score collisions.** Tie groups of 2–4, mostly DEF/K/QB, carrying
  **real** `final_score` values. Ordinary rounding ties.
* **Rounds 13–18 — total exhaustion.** Tie group = the entire remaining pool, `final_score` is
  `None`. Not a tie at all: an absence.

*(§20 recorded 27.8% and `_board_order`'s own docstring records 42.5% on a 12×20 mock. All three
are the same phenomenon at different draft lengths; the collapse point depends on how fast
starter demand is consumed, so the percentage is a property of the configuration, not a constant.)*

### What the engine does after that point — and why

`replacement_levels` omits a position once its remaining starter demand is exhausted.
`compute_draft_board` then leaves `_vor` as NaN for every player at that position, so
`bpa → universal_value → final_score` are all `None`. **This is correct and deliberate**: the
engine refuses to price a player against a replacement level that no longer exists, which is
this module's own don't-fabricate rule working exactly as intended.

`_board_order` then sorts `(score is None, -score, str(player_id))`. Its docstring already says
what is missing, in as many words:

> *"it does not decide what the board SHOULD do once nothing on it can be priced; that is an
> open product decision."*

**#114 is that named-but-unmade decision.** The design is right; the terminal case was never
specified.

### The ordering, characterized explicitly

It is **deterministic and carries no information**. Measured board order on the exhausted board:

```
['100','101','102','103','104','105','106','107','108','109','110','112','12','13','144']
```

**A lexicographic sort on the player-id string** — `'12'` ranks below `'110'`. Not numeric, and
nothing about an id is a statement about a player.

### What information remains — measured, not invented

**A great deal.** Every row on the fully-unpriced board still carries a real, *differing*
`projected_points`, plus `confidence` and `bpa_source`. Their projections in board order:

```
64, 52, 43, 43, 53, 46, 54, 47, 66, 38, 36,  96,  319, 312, 169
                                              ^^^  ^^^  ^^^
```

**The board recommends a 36-point player over a 319-point player** — while carrying both numbers
on the very rows it is ordering. And it compounds: the board stops recommending the better
players, so they stay in the pool, so it keeps not recommending them.

The board is **not** choosing between indistinguishable players. It is choosing between
distinguishable players using none of what distinguishes them.

### A contract inconsistency found while measuring

`CandidateSnapshot.bpa`, `.universal_value` and `.team_acquisition_value` are annotated **`float`**,
never `Optional[float]` — yet all three are genuinely `None` in the exhausted regime (a probe
crashed on exactly that). The **behaviour is correct** — the absence contract working as designed.
The **annotations** are wrong, which is the §17.5/#110 class in a type hint. Not repaired: it
touches the same fields #119 is parked on.

## #116 — what the numbers are, and what the UI implies

Measured over **33,417 real board rows** and **48,708** `projected_points` readings.

| Quantity | Population | min | median | max | negative |
|---|---|---|---|---|---|
| `universal_value` | all board rows | −319.2 | −42.6 | 178.9 | **83.9%** |
| `team_acquisition_value` | **narrowed candidates** — what a user is shown | −16.1 | **10.8** | 187.3 | **10.9%** |
| `projected_points` | all rows | 0.0 | 99.0 | 379.0 | **0.0%** |

The two populations are different and must not be conflated. §20.8's earlier figures (median
11.0, 11.8% negative) match the **candidate** row — the one the metric cards actually render.

**The mechanical fact that settles the unit question:** an acquisition value can be negative
(10.9% of shown candidates are); a season fantasy-point total never is (0 of 48,708). They are
different quantities on different scales, and no clamp or rescale stands between the engine and
the card.

### What the UI implies

`app.py`'s `metric_row1` places, in one row of six cards:

```
[0] "Universal Value"        <- universal_value        f"{...:.0f}"
[1] "Projected Points"       <- projected_points       f"{...:.0f}"
[2] "Your Acquisition Value" <- team_acquisition_value f"{...:.0f}"
```

**Two different units, adjacent, identically formatted, and only the middle card names its own
unit.** In a fantasy app "points" is the domain's word for the quantity in card [1], so [0] and
[2] borrow a meaning they do not have.

### The corrected count

§20.8's *"qualifies its unit three times and not twice"* covered **only the board's JS prose**.
Across every surface that renders a universal-value-scale number:

| Surface | Sites | Unit stated |
|---|---|---|
| `draft_board_ui` prose | 5 | 1 full (*"universal-value points"*), 2 partial (*"-point gap"*, *"-point rival premium"*), **2 bare** |
| `app.py` metric cards (5 labels × 2 panels) | 10 | **0** |
| `app.py` "Best alternative … acquisition value" | 2 | **0** |
| **Total** | **17** | **1 fully qualified** |

The Draft Room panel and its Mock Draft twin are **separate code carrying identical copy** — a
repair that fixed one and not the other would be worse than neither. Pinned by a test.

Also in the same panel: `_waiting_note` renders `projected_points` and `horizon_floor` — genuinely
season points — beside the universal-value phrases. **Both units appear in one surface**, which is
what makes the bare "points" ambiguous rather than merely imprecise.

## A correction to my own 1c work

My first #116 distribution reconstructed `picks` from board rows instead of real draft history,
which corrupted replacement levels and produced figures (min −371.2, 76.6% negative) that
contradicted §20.8. **Those numbers are discarded.** Everything above is from a properly
sequential draft.

---

# D9 and D10 — the two decisions 1c produces

**Not taken. Both need your ruling before any 1c implementation.**

## D9 — what the board does once nothing on it can be priced

The engine correctly refuses to invent a price. The question is only what it presents instead.

| Option | What it does | Cost |
|---|---|---|
| **A. Order by `projected_points`, labelled as a different basis** | Uses the signal that demonstrably survives. Ends the 36-over-319 inversion immediately. | Season points are **not comparable across positions** the way VOR is — a 319-point QB and a 96-point RB are not ranked by the same yardstick. The board would be ordering by a measure it elsewhere refuses to treat as value. Must be labelled, not silently substituted. |
| **B. Stop ranking and say so** | Present the exhausted pool as explicitly unranked — a flat list, an honest "no basis to rank these" state. | Least invention, most consistent with the existing absence contract. But an auto-draft still has to pick *something*, so a sub-rule is still needed underneath. |
| **C. Extend pricing past starter demand** | Give `replacement_levels` a defined behaviour below zero demand so a price exists all the way down. | The largest change, overlaps **#50** (VOR/replacement/horizon redefinition) and **#58**'s parked unit work. Probably belongs there, not here. |
| **D. Leave it, document it** | Keep the id sort; state plainly in the UI that late-draft ordering is arbitrary. | Cheapest and honest, but the board keeps actively recommending worse players over better ones. |

**Interaction you should know about:** this is a **hard prerequisite for Insight**. Under the
current behaviour Insight would be handed a Top 5 whose ordering carries no information and asked
to "explain the important differences" — it will produce differences, because that is what it is
asked for. Whatever D9 settles, Insight must be able to tell whether the ordering it is
explaining is real.

## D10 — what the display contract declares

| Option | What it does | Cost |
|---|---|---|
| **A. Name the unit everywhere** | *"Universal Value (UV)"*, *"Acquisition Value (UV)"*, and finish the two bare board phrases. ~17 sites, two of them duplicated panels. | Purely additive copy; no number changes. Does **not** address that the scale is unintuitive — it makes it honest, not friendly. |
| **B. Rescale to a stated band** | Normalise the displayed number into an explicit 0–100 (or similar) band. | Substantive. Depends on **#58** (BPA normalization / the ruler that drifts 72×) which is parked, and on **#75/#76**. Doing it before #58 would calibrate a display against a moving scale. |
| **C. Show fewer numbers** | Drop raw UV from the cards; keep ranking, deltas and the qualified prose. | Removes the confusion by removing the confusable value. Loses information some users want. |
| **D. Leave it, document it** | Record the scale in the manual and change nothing. | Keeps a 10.9%-negative number on a card next to a never-negative one, both `.0f`, neither labelled. |

**My reading, for what it is worth and not acted on:** A is mechanical, safe, and independent of
every parked item — it is the only one of the four that does not wait on #58. B is the one that
actually fixes the reader's experience and should not be attempted before #58.

## State

**1c is complete as scoped.** Nothing normalized, nothing renamed, behaviour preserved and pinned.
**D9 and D10 are open and blocking 1c implementation.** D9 additionally blocks the Insight
contract (Step 2), because Insight cannot honestly compare candidates whose ordering may carry no
information without being told so.


---

# D9 — REVISED by the operator. Now a measured design task, not an A/B/C/D choice.

The four options as I wrote them were too narrow, and option A was wrong in a way worth stating
plainly: **"pricing is exhausted" does not mean "the engine has no information."** It means one
particular VOR-style economic model has run out of a valid replacement-level comparison. Falling
back to raw projected points would swap a correct refusal for cross-position nonsense.

The operator's framing, which is the one to build against:

> A WR8 is not worth its raw projection to a roster that already has seven usable WRs and three
> QBs in superflex. The question is not "who projects highest" but **"where does another player
> provide the most useful insulation against future uncertainty?"**

## The revised decision

**When the canonical acquisition-value calculation becomes non-certifiable because replacement
demand is exhausted, the engine must not fabricate a universal value and must not substitute
projected points as a cross-position stand-in for VOR.** It should instead enter an explicitly
distinct **deep-draft / contextual selection regime**, considering at minimum:

player rank/tier · projected production · positional depth remaining on the board · the user's
current roster construction · positional insulation and vulnerability · league starting
requirements · bench capacity · remaining draft length · scarcity of alternatives · likely
availability of comparable players later · upside vs floor where appropriate · roster-specific
contingency value

That regime **still produces an ordered recommendation**, but the ordering must **carry an
explicit basis** — not a fabricated `Universal Value: 0`, and not a silent re-sort. Something
shaped like:

```
Contextual Priority
  QB — Tier 2, 1 remaining
  WR — Tier 3, 7 remaining
  RB — Tier 4, 3 remaining
Recommendation: QB — sufficient WR insulation; QB is a materially thinner remaining tier.
```

## Two architectural rules this settles

**1. ADP is evidence, never authority.** It can answer *"what does the market expect?"* It must
never answer *"what should this roster do?"* — the market's roster context is not the user's, and
in deep dynasty/SF/IDP configurations that gap is where ADP is most confidently wrong.

*Measured:* **there is no ADP in this system at all.** No column in `projections`, `trade_values`
or `external_values`; the only occurrences anywhere are in `run_idp_counterfactual_analysis.py`,
which tracks `adp_available` as a comparison baseline and records it as unavailable. So this rule
constrains future ingestion rather than correcting present behaviour — but it should be written
into the contract before any ADP source is ever added, not after.

**2. The deterministic engine owns the reason, not just the pick.** This is the part that makes
the whole architecture hold:

```
canonical valuation valid      -> use it
canonical valuation invalid    -> do NOT fake it
contextual selection layer     -> tier + projected value + roster need + depth/insulation
                                  + future availability, with an explicit stated basis
AI Insight                     -> renders that deterministic reason in human language
```

Insight never has to invent a rationale for why A beats B after VOR collapses, because the engine
already produced one. **Engine owns truth; AI explains truth** — including in the regime where the
canonical number does not exist.

## How D9 gets resolved

**Not by picking an option.** By measurement:

1. inventory which contextual inputs the engine already has, and **which survive into the
   exhausted regime** (in progress — most exist; several derive from the very value curves that
   ran out, so availability is not the same as usability);
2. formulate candidate contextual-priority rules;
3. **measure each against controlled drafts** — the same harness §20 used;
4. bring the measured comparison back before any contract is written.

**Acceptance-test question, in the operator's words:** *"Do I really need WR8 when I don't have
QB4?"* That is not an edge case. It is the problem the feature exists to solve, and any candidate
formulation that cannot answer it is not a candidate.

## Status

**D9 is open and is now a measured design task.** D10 remains as previously written and is
unaffected. No implementation until the measured comparison is delivered and a contract is agreed.

## D9 — measurement round 1: what the contextual regime would actually have to work with

Read-only. Three measurements, one of which substantially changes the design space.

### 1. Which inputs survive the exhausted regime

Snapshot candidates at three points of one 12×18 draft. `d` = distinct values among the
candidates; **`d=1` means the field is present but carries no discriminating information at all.**

| Field | pick 1 (healthy) | pick 121 (partly) | **pick 155 (exhausted)** |
|---|---|---|---|
| `projected_points` | 72/72 d=53 | 10/10 d=10 | **10/10 d=8** |
| `waiting_cost` | 48/72 d=35 | 10/10 d=9 | **9/10 d=8** |
| `horizon_floor` | 48/72 d=5 | 10/10 d=6 | **9/10 d=6** |
| `horizon_sensitivity` | 48/72 d=5 | 10/10 d=6 | **9/10 d=6** |
| `need_bonus` | 72/72 d=3 | 10/10 d=2 | 10/10 d=2 |
| `pick_necessity` | 72/72 d=14 | 10/10 d=8 | 10/10 d=2 |
| `position_run_detected` | 72/72 d=1 | 10/10 d=1 | 10/10 d=2 |
| `positional_cliff` | 72/72 d=36 | 6/10 d=7 | **0/10 — gone** |
| `positional_forfeit` | 72/72 d=3 | 6/10 d=3 | **0/10 — gone** |
| `position_expected_taken` | 72/72 d=3 | 6/10 d=3 | **0/10 — gone** |
| `universal_value` / `tav` | 72/72 d=59 | 6/10 d=7 | **0/10 — gone** |
| `survival_probability` | 72/72 d=5 | 10/10 d=7 | 10/10 **d=1 — no signal** |
| `consensus_rank` / `consensus_tier` / `reach_label` | **0/72** | **0/10** | **0/10** |

**Everything derived from a value curve dies with the value curve** — cliff, forfeit, expected-taken
all go to zero coverage, as they must. `survival_probability` survives as a number but collapses
to a single value, which is worse than absent: it looks like signal and is not.

**The two strongest survivors are `projected_points` and `waiting_cost`, both d=8 of 10.** That
second one is worth pausing on: `waiting_cost` measures replaceability **against the draft
horizon** ("what is the best player at this position still likely to be undrafted when the draft
ends"), not against starter demand — which is exactly why it survives when VOR does not. It is
already computed, already on the snapshot, and is precisely two of the twelve inputs the revised
D9 names: *positional insulation* and *likely availability of comparable players later*. It is
also parked under **#57 / #48 / #71**.

### 2. The tier data the proposed display needs does not reach the board in 1QB leagues

`consensus_rank`, `consensus_tier` and `reach_label` are `None` on **every candidate at every
point of the draft** — not exhausted, never populated. The cause is not missing data:

* **KeepTradeCut carries `rank` and `tier`, 499/499 populated.**
* `pick_synthesis._consensus_lookup` filters to `source_name == "keeptradecut"` and returns `{}`
  unless the league is superflex — deliberately, because the committed KTC export is
  `dynasty_superflex_halfppr.csv` and superflex-inflated QB consensus would misrepresent a 1QB
  market.
* Measured: `is_superflex=False → 0 entries`; `is_superflex=True → 448 entries`, and a superflex
  snapshot populates 48 of 72 candidates with tiers spanning 1–18.

**So the tier-based display is already buildable in superflex and unbuildable in 1QB — from a
wiring gap, not a data gap.**

### 3. The non-projecting benchmark sources are already ingested, and CDME reads none of them

Prompted by the operator's note that rankings/tier lists from non-projecting sources should be a
gauge of who is the better asset in a vacuum — evidence, not law:

| Source | Rows | Carries | Format scope | Reaches the board's ranking? |
|---|---|---|---|---|
| **fantasypros** | 1198 | `rank`, `tier` (1198/1198), `pos_rank`, `age`, **`best`/`worst`/`avg`/`std_dev`** | `dynasty_ppr_rankings.csv` (**1QB**), best-ball, IDP redraft | **No** |
| keeptradecut | 499 | `rank`, `tier`, `value`, `trend_30d` | superflex half-PPR only | Only via `_consensus_lookup`, superflex only |
| dynastyprocess | 783 | **`ecr_1qb` and `ecr_2qb`**, `value_1qb`, `value_2qb` | both formats | **No** |
| espn | 120 | `rank`, `analyst_avg` | IDP redraft | **No** |

Two things follow.

**FantasyPros fills the exact gap the superflex gate creates** — it publishes a dynasty **PPR
(1QB)** ranking with tiers, 1198 rows, already loaded into `merger.external_values`. Today it
reaches only the composite percentile that feeds the trade-value surface; it never reaches the
board's consensus lookup. DynastyProcess's `ecr_1qb`/`ecr_2qb` is a second, format-aware benchmark
in the same position.

**FantasyPros also carries `best` / `worst` / `std_dev`** — a real measure of how much the experts
disagree about a player. That is a genuine uncertainty signal, and it maps onto two more of the
twelve inputs (*upside vs floor*, and how to express uncertainty honestly) without inventing
anything.

### The implementation constraint this creates, recorded now

`_consensus_lookup`'s `source_name == "keeptradecut"` filter is **also the CDME ingestion
boundary** — it is what keeps `bot_research`'s LLM-authored rows out of the engine, proven by
`test_cdme_ingestion_boundary.py` and re-proven behaviourally in §25 (30 planted findings, 0 of
333 board rows moved). Widening it to admit FantasyPros or DynastyProcess must be done as an
**explicit allowlist of deterministic sources**, never by relaxing the filter. Removing it would
reopen the boundary. This is the single most dangerous edit in the D9 space and it is worth
saying before anyone writes it.

### What this changes about D9

The revised D9 is **more buildable than it looked**, and the reason is that most of what it needs
is already computed and simply unrouted — the same pattern this audit found five times over as the
compute-then-drop class. But it now has a **source-precedence decision inside it** that did not
exist before: *which non-projecting benchmark provides tier/rank per league format, and with what
authority relative to the projection-based engine.* That is a policy question, it is adjacent to
**#43** (deterministic source precedence, already settled once for projections), and it should be
settled before any candidate formulation is measured.

**Still open. Next measurement round:** formulate candidate contextual-priority rules over the
surviving inputs, and measure each against controlled drafts — with *"do I really need WR8 when I
don't have QB4?"* as the acceptance test.

## D9 — measurement round 2: consensus as a TIEBREAKER

The operator's recollection — that the consensus/tier data was always meant to be *glanced at for
tiebreakers*, for exactly the case where there is not enough other context to distinguish — is
confirmed by the code's own stated intent, with one nuance that matters.

### What the current contract actually says

`consensus_reach`'s docstring: *"it's informational evidence for the debate layer, **never a block
or a penalty applied here**."* Measured consumers: the debate prompt
(`pick_debate._format_candidate`), both `app.py` panels, `draft_counterfactual` (as an ADP-proxy
baseline), and now the 1a evidence projection. **It is consulted for ordering by nothing.**

So consensus-as-tiebreaker would be the **first time this data touches engine output**. That is a
small, bounded step — but it is a step across the line that docstring draws, so it is a policy
decision rather than a mechanical repair. What does *not* change is the authority claim: a
tiebreaker fires only where the engine has no signal of its own, and never moves a price.

### Does it actually work? Measured in superflex (the only format where it populates today)

| pick | rd | pool | priced | unpriced | with consensus | coverage |
|---:|---:|---:|---:|---:|---:|---:|
| 133 | 12 | 201 | 190 | 11 | 11 | **100%** |
| 145 | 13 | 189 | 145 | 44 | 11 | 25% |
| 157 | 14 | 177 | 41 | 136 | 101 | **74%** |
| 169 | 15 | 165 | 0 | 165 | 130 | **79%** |
| 193 | 17 | 141 | 0 | 141 | 106 | **75%** |
| 205 | 18 | 129 | 0 | 129 | 94 | **73%** |

**My worry was wrong in the good direction.** I expected consensus to be least available exactly
where it is most needed — deep-bench players the source does not cover. Coverage instead holds at
**73–79%** once pricing has collapsed. (The 25% dip at pick 145 is the transition: the *first*
rows to go unpriced are the genuinely obscure ones; the well-covered players join the unpriced set
as their positions' demand runs out.)

**Discrimination is total among covered rows: 82 covered rows, 82 distinct consensus ranks.**

### The sample that settles it

The final board's first ten rows, in the order the board currently presents them:

| board order (id string sort) | player | consensus rank | tier | proj |
|---|---|---:|---:|---:|
| 1st | K Boutte | 199 | 18 | 115 |
| 2nd | J Bech | 234 | 18 | 87 |
| 4th | J Jeudy | 225 | 18 | 136 |
| **5th** | **Z Branch** | **168** ← best | 18 | 113 |
| 10th | R Flournoy | 278 ← worst | 18 | 115 |

### Two findings that change the proposed design

**1. Tier does not discriminate at the tail; rank does.** All ten of those players are **tier 18**.
The *"QB — Tier 2, 1 remaining"* display works in the mid-draft, where tiers are meaningful, but
deep in a draft everyone collapses into the last tier. A tail tiebreaker has to key on **rank**,
and any tier-based presentation needs a defined behaviour for "everyone left is the same tier."

**2. Consensus and projection disagree, and cover different things.** `C Brazzell II` carries
`proj = 0.0` and `consensus_rank = 230` — the market has an opinion where the projection has
none. That is the strongest argument for the operator's framing: consensus is a **second,
independent read** on who is the better asset in a vacuum, not a substitute ranking.

### The design constraint this leaves

A tiebreaker with ~75% coverage produces a **two-tier ordering**, and the uncovered quarter needs a
defined home. Putting all uncovered rows below all covered ones is itself a claim — *"unknown to
this source = worse"* — which may be false for exactly the populations a source under-covers
(deep IDP, rookies, recent signings). Whatever is chosen there must be stated, not defaulted into.

**Still open. Next: candidate formulations, measured against controlled drafts.** Consensus-as-
tiebreaker is now the strongest and smallest of them — it changes nothing while the engine has
signal, and replaces a zero-information string sort with a sourced one where it does not.

---

# D9 — REFRAMED AGAIN by the operator, and a correction to my own recommendation

My round-2 close said consensus-as-tiebreaker was *"the strongest and smallest of the candidate
formulations."* **That ordering was wrong**, and the operator has corrected it: define the decision
calculus that consumes the context the engine already has **first**, then consider external
evidence as one input to it. Reaching for the external source first is how a fallback quietly
becomes an authority.

## The distinction that reframes the whole item

> **The engine running out of player valuation information does not mean the engine has run out of
> decision information. Those are two completely different failures.**

When `universal_value` becomes `None`, exactly one thing has become invalid: *"how much better is
Player A than the appropriate replacement player?"* Everything else the system knows is untouched —
roster construction, positional requirements, remaining starting and bench slots, depth by
position, insulation needs, **what opponents have and need**, who is likely to be available later,
tiers and rankings, projections, the remaining pool, positional scarcity, the consequences of
waiting, and whether the roster is already over-concentrated somewhere.

**One dimension is exhausted. The decision is not.**

## The architectural principle

> **The system should degrade in precision, not in intelligence.**

```
normal:     economic valuation -> contextual roster calculus -> external evidence -> decision
exhausted:  (valuation absent) -> contextual roster calculus -> external evidence -> decision
NOT:        (valuation absent) -> sort by projected points
```

## The six rules this settles

1. **Engine economics stay authoritative wherever they exist.** VOR / universal value / team
   acquisition value are never overridden.
2. **Only where the engine genuinely cannot distinguish** — pricing exhausted, or no valid
   comparison — may an external deterministic ranking act as a *tiebreaker*.
3. **Absence from a source is not negative information.** Unknown must stay unknown, never ranked
   below covered. *(This directly answers the two-tier-ordering constraint round 2 left open.)*
4. **Deterministic, non-LLM sources only**, via an **explicit allowlist** with documented
   precedence. **The `bot_research` ingestion boundary is not to be weakened.**
5. **Consensus rank must never become a universal ranking of the board.** It exists only to break
   an otherwise unresolved engine tie.
6. **The tiebreaker still passes through roster/contextual need.** The deep-draft question is not
   *"who has the highest projection?"* but *"which available asset provides the most useful next
   layer of insulation for this roster?"*

## Explicitly NOT to be done yet

* **Do not implement the consensus tiebreaker.**
* **Do not solve the 1QB gap by adding FantasyPros into `_consensus_lookup`.** In the operator's
  words, that is *"exactly the kind of seemingly tiny change that can accidentally turn a carefully
  protected ingestion boundary into 'whatever data happens to be available gets to influence the
  engine.'"* Round 2 already recorded that this filter **is** the CDME ingestion boundary; this
  makes the prohibition explicit rather than merely advisory.

## The risk that makes this worth doing carefully

Fixing the 36-vs-319 inversion with a projection or consensus sort would stop the board making
*obviously* stupid choices and start it making **plausible-looking, contextually stupid ones** —
and those are far harder to detect. A WR8 outranking a QB4 on raw projection looks entirely
reasonable on screen and is close to indefensible in a superflex dynasty draft where the roster
already holds seven WRs and three QBs.

## The acceptance tests

**Primary — "Do I really need WR8 when I don't have QB4?"** Roster holds QB1–QB3 and WR1–WR7;
the board offers a WR8 (proj ~180) and a QB4 (proj ~150); VOR is exhausted for both. A
projection-only fallback takes the WR. The system must be *capable* of preferring the QB.

**Reverse — the calculus must invert.** Strong QB depth, dangerously thin at WR, and the same
machinery should prefer the WR. A rule that only ever favours QBs has encoded a positional bias,
not a roster calculus. *(This is why the reverse case is mandatory, not optional: it is the
non-vacuity test for the whole feature.)*

## What the next measurement must demonstrate

Five behaviours, each shown as an exact pick-level difference between formulations:

1. engine signal available → **engine wins**;
2. engine unavailable + deterministic consensus available → **consensus may break the tie**;
3. consensus unavailable → **no penalty for being unknown**;
4. roster-depth pressure → **materially changes the choice**;
5. raw projected points alone → **demonstrably does not become the fallback**.

## Status

**Source precedence and the exact roster-depth formulation are policy questions.** Measure the
mechanical options, show where each changes the pick, bring the choices back. **No implementation.**

---

# D9 — the three-layer model, and what measurement says about each

The operator's tightened framing. Three layers of information, with distinct lifetimes:

| Layer | What it answers | Lifetime |
|---|---|---|
| **1. Player valuation** — VOR / BPA / universal value / acquisition value | *How valuable is this player relative to replacement?* | **Legitimately becomes undefined** when replacement demand is exhausted |
| **2. External player-quality evidence** — FantasyPros, KTC, DynastyProcess, projections | *If I must distinguish these as assets, what does the broader information ecosystem think?* | **Secondary always.** Never overrides layer 1 where layer 1 is valid |
| **3. Draft-state / roster-context calculus** — my roster, opponents' rosters, positional requirements, remaining demand, available pool, scarcity, insulation, consequences of passing | *Given all of it, which pick improves my roster most?* | **Never disappears** |

> **The engine should never confuse "I cannot assign a valid VOR number" with "I cannot determine
> what pick is best." Those are not equivalent.**

And the property that makes it right: **the engine does not surrender when one model runs out of
runway — it changes what evidence it trusts.**

## Measured: layer 3's raw inputs survive completely

At the exhausted pick (SF 12×18, pick 165, round 14), every layer-3 input is intact:

* **my roster** — `{RB:3, TE:2, QB:2, WR:3, DEF:1, K:2}`
* **starting requirements** — `{QB:1.85, RB:2.38, WR:2.38, TE:1.38, K:1.0, DEF:1.0}`
* **all 11 opponent rosters** — fully countable
* **remaining pool by position** — `{WR:68, RB:33, TE:24, DEF:20, K:13, QB:11}`

That last line is the acceptance test appearing spontaneously in a real draft: **68 WRs left
against 11 QBs, on a roster holding 3 WRs and 2 QBs.** The scarcity signal the WR8/QB4 case needs
is fully present at exactly the moment the valuation is gone.

## Measured: but layer 3's existing COMPUTATION does not survive

This is the correction that matters, and it changes the size of the work.

**`need_bonus` is `0.0` for every candidate at exhaustion** — present, but flat. Not because the
`None` valuation destroyed it; it is already zero before it reaches anything.

The cause is that `need_bonus` and `replacement_levels` are **the same underlying quantity**:
remaining *starter* demand. When starters are filled, both die together, by construction.

Measured directly:

```
remaining starter demand   pick 1                      pick 165
  WR                        28.60                        0.77
  RB                        28.60                        0.77
  QB                        22.20                        0.85
  TE                        16.60                        0.77
  K / DEF                   12.00                        0.00
```

**Pricing dies when remaining demand falls below 1.0 per position — not when it reaches zero.**
The 0.77–0.85 residue is real unfilled demand that `replacement_levels`' own domain guard cannot
use (its docstring records the same effect: *"TE demand from round 11 onward is
0.9999999999999998 … so replacement_levels returned an empty dict and the board could price
nothing at all"*).

**So the honest statement of the work is:** the raw context is all there, and *none of the engine's
existing derived need machinery survives to consume it*, because every piece of it is keyed to
starter demand. A contextual regime therefore needs a notion of need that is meaningful **after
starters are filled** — depth, insulation, concentration — which is a **new deterministic
computation over existing inputs**, not a rewiring of something already computed.

That is more work than "route what already exists," and less than "invent a new valuation." It is
also exactly what `positional_bench_appetite` was reaching for, and #62 records that it returns
0.0 for every position when none is measurable — the same failure, from the same cause. *(My
attempt to re-verify #62's state at exhaustion failed for a harness reason — `build_available_pool`
does not create the `_points` column `compute_draft_board` adds — so that check is outstanding,
not a finding.)*

## On the ramp: measure it, do not assume round 13

The operator's hypothesis — that this should already be happening by ~round 15, and could ramp in
from ~13 — is a good one and is being tested rather than adopted. Two reasons not to hard-code a
round:

**It already varies across configurations in the data I have.** Full collapse: **round 13** (1QB
12×18), **round 14** (SF 12×18), **round 11** (the 12×20 mock recorded in `_board_order`'s own
docstring). The collapse point is a function of how fast a league consumes starter demand — roster
template, team count, draft length — not of the calendar.

**And presence is the wrong variable anyway.** The operator's sharper framing is *loss of
discriminatory power*, which happens **earlier** than loss of presence: §20 measured genuine score
collisions in rounds 6–9 with real, non-`None` values. A valuation can be fully present and still
unable to separate two candidates.

So discriminatory power is being measured against **the engine's own yardstick**, not one I invent:
`NEAR_TIE_BAND = 2.0` universal-value points, the band inside which `near_tie_flags` already
refuses to present its ordering as a real preference. Per pick, over the candidate set the decision
actually sees: how many candidates sit inside that band of the leader (1 = clean standout), the
leader-to-runner-up margin, distinct values, and how many carry a price at all — against round and
against minimum remaining demand.

**Candidate ramp variables under test:** round number · fraction of board unpriced · fraction of
the top-12 unpriced · minimum remaining starter demand · candidates-in-band. The last two are the
causal quantities; the first is the one most likely to be wrong across configurations.

**Deliverable:** a measured degradation curve per configuration, and a proposed calibrated
influence curve keyed to whichever variable actually tracks it — with the explicit expectation
that a continuous blend beats a threshold, since the underlying signal degrades continuously.

## D9 — measurement round 4: is there a ramp, and what should key it?

Four configurations, full drafts, measuring per pick: round, % of board unpriced, % of the top-12
unpriced, and minimum remaining starter demand.

| Config | Collapse round | Transition band | min_demand at collapse |
|---|---:|---:|---:|
| 1QB 12×18 | **13** | **0 picks** | **0.67** |
| 1QB 12×22 | **13** | **0 picks** | **0.67** |
| SF 12×18 | **14** | **0 picks** | **0.77** |
| SF 10×16 | **14** | **0 picks** | **0.77** |

### Finding 1 — at the presence level there is no ramp at all. It is a cliff.

**The transition band is zero picks wide in every configuration.** The board goes from every row
priced to every row unpriced between one pick and the next. There is no gradual thinning of
pricing to blend against, so **any ramp keyed to "% unpriced" would be useless** — that variable
reads 0% and then 100%.

This is a direct answer to the ramp hypothesis, and it is the opposite of what a "signal weakens
with depth" intuition predicts. It also explains why the phenomenon was recorded three times at
three different magnitudes: what varies between configs is *when* the cliff falls, not how steep
it is.

### Finding 2 — the round is stable within a roster template, and the demand is stable *exactly*

Round 13 for 1QB in **both** an 18-round and a **22**-round draft. Round 14 for superflex in both
a 12-team×18 and a **10**-team×16 draft. And the demand at collapse is not merely similar but
**identical within a template**: 0.67 for both 1QB configs, 0.77 for both superflex ones.

The mechanism explains the invariance. Remaining starter demand scales with team count, and so does
consumption — one pick per team per round — so **the round at which per-position demand crosses
below 1.0 depends only on the roster template's own flex arithmetic**, not on how many teams play
or how long the draft runs. `0.67 = 2/3` and `0.77 = 23/30` are the residues those two templates
leave when their flex shares are divided out.

### What this means for the operator's hypothesis

The instinct — *"if it's consistent after ~15 rounds, hard-code where it begins"* — is **more right
than I expected**: it *is* consistent, and stable enough to hard-code **within a roster template**.

But the round is a *symptom*, and the template is the variable it is stable against. A 2QB league,
a TE-premium template, an IDP template or any roster with different flex arithmetic moves the
round, and neither of the two templates measured here would predict it. **Keying on minimum
remaining starter demand crossing `replacement_levels`' own `< 1.0` domain guard gives the same
answer for the tested templates and generalises to untested ones — at no extra cost, since the
quantity is already computed on every board.**

So: **do not hard-code round 13.** Key on the causal quantity, which is directly observable and
already in hand.

### What is still being measured

Presence is a cliff — but the operator's sharper framing was **discriminatory power**, which §20
already showed degrades *earlier* (genuine score collisions in rounds 6–9, with real non-`None`
values). A valuation can be fully present and unable to separate two candidates.

That is being measured against the engine's own yardstick — `NEAR_TIE_BAND = 2.0`, the band inside
which `near_tie_flags` already refuses to call its own ordering a preference — as candidates-in-band
per pick, against round and against demand. **If a real ramp exists anywhere, it is there and not
in presence.** Result pending.

## D9 — measurement round 5: the ramp exists, and it is in discriminatory power

Measured against the engine's own yardstick — `NEAR_TIE_BAND = 2.0`, the band inside which
`near_tie_flags` already refuses to present its ordering as a real preference. Reported as the
**fraction of the priced candidate field sitting inside that band of the leader**: 2% means a clean
standout, 60% means most of the field is indistinguishable from the leader.

| round | 1QB 12×18 | SF 12×18 | | round | 1QB | SF |
|---:|---:|---:|---|---:|---:|---:|
| 1 | 2% | 2% | | 10 | 41% | 30% |
| 2 | 3% | 4% | | 11 | 26% | 37% |
| 3 | 2% | 3% | | 12 | 31% | **58%** |
| 4 | 2% | 3% | | 13 | **68%** | 42% |
| 5 | **5%** | 3% | | 14 | 100% | *(artifact)* |
| 6 | 10% | 3% | | 15 | 100% | 100% |
| 7 | 12% | **6%** | | 16–18 | 100% | 100% |
| 8 | 21% | 14% | | | | |
| 9 | 38% | 17% | | | | |

*(SF round 14 reads 132% — an artifact of my harness averaging picks where pricing still existed
with picks where it did not. Not a finding.)*

Leader-to-runner-up margin tells the same story from the other side: **7.14 → 0.57** points in 1QB
by round 9; **0.15** in SF at round 12.

### Finding: the ramp is real, roughly monotonic, and starts SIX TO EIGHT ROUNDS before the cliff

The primary valuation holds a flat ~2–3% baseline for the first four to six rounds — the leader is
genuinely alone. It then departs that baseline at **round 5 (1QB)** and **round 7 (SF)** and climbs
continuously to 40–68% before pricing disappears at all.

**So the operator's hypothesis was right in kind and conservative in timing.** The guess was "start
looking around round 13, ramp it up." The measurement says **start around round 5–7** — because
that is when the engine actually begins failing to separate candidates, a full six to eight rounds
before it stops producing numbers. Round 13 is where the *last* signal dies, not where the first
one weakens.

### Finding: min remaining demand predicts the CLIFF but NOT the ramp

This is the measurement that decides what the influence curve should key on.

In superflex, `min_demand` **flattens at 0.85 from round 6 onward** — and stays there — while the
in-band fraction continues climbing from 3% to 58%. The causal variable that predicts the cliff
exactly (round 4's finding) carries **no information at all** about the ramp that precedes it.

Two different phenomena, two different variables:

| | Predicted by |
|---|---|
| **The cliff** (pricing disappears) | `min_demand` crossing `< 1.0` — exact, template-invariant |
| **The ramp** (pricing stops discriminating) | **not** `min_demand`, and **not** round number |

### Recommendation: key the influence curve on the engine's own measure of its own discrimination

The in-band fraction is the best candidate found, and it has properties nothing else does:

* **It is the thing being measured.** It does not *predict* discriminatory power; it *is*
  discriminatory power, so it cannot drift away from what it stands for.
* **It is already computed.** `near_tie_flags` runs on every snapshot today; the fraction is a
  count over its output. No new constant, no new model.
* **It self-calibrates across configurations.** No round threshold, no template dependence, no
  need to re-derive anything for 2QB / TE-premium / IDP templates.
* **It degrades continuously**, which is what a blend needs — unlike presence, which is a step.

This is the same principle the audit kept arriving at: prefer the quantity the system already
computes over a proxy that has to be maintained in agreement with it.

### What this does NOT settle

The *shape* of the blend (linear in the fraction? thresholded? capped?), what the secondary signals
are, and how roster context enters remain open — those are the candidate formulations, and they are
the next measurement, not this one. **Still no implementation.**

## D9 — measurement round 6: the knife edge, with both failure modes made visible

> *"Can we construct a contextual score that produces sensible decisions when raw valuation is
> weak, without allowing roster need to overwhelm genuinely meaningful player quality?"*

**Controlled experiment.** Superflex 12-team, driven to full pricing exhaustion (**0 of 117 rows
priced**). Identical opponents, identical draft state, and my roster **identical except that seven
WRs and three QBs are swapped for seven QBs and three WRs**. Everything else — 4 RB, 2 TE, 1 DEF,
1 K — is held equal and adequate, so the answer cannot be dominated by some third position.

Five formulations, two of them deliberately bad controls, all scratchpad functions. **No
production code.**

| | QB-STARVED (7 WR / 3 QB) | WR-STARVED (7 QB / 3 WR) |
|---|---|---|
| **F0** current (id sort) | T Benson · RB · proj 64 · cons 271 | **T Benson · RB · proj 64 · cons 271** |
| **F1** projected points | D Schultz · TE · proj 178 | S Diggs · WR · proj 184 |
| **F2** pure need *(control)* | T Tagovailoa · QB · proj 114 | D Schultz · TE · proj 178 |
| **F3** band → context | **T Tagovailoa · QB** ✅ | P Freiermuth · **TE** ❌ |
| **F4** band → quality first | C Bell · **WR** ❌ | T Hunter · WR |
| **F5** F3 + scale guard | **T Tagovailoa · QB** ✅ | P Freiermuth · **TE** ❌ |

### What is now demonstrated rather than asserted

**F0 is provably inert to roster context.** It returns **the same player in both scenarios** — and
that player is the worst available by *both* independent quality measures (projection 64, consensus
rank 271). The current behaviour is not merely arbitrary; on this state it is anti-correlated with
every quality signal present.

**F1 is inert too, and its apparent responsiveness is an artifact.** It answers differently across
the two scenarios only because the two pools differ slightly. It reads no roster information at all.

**F4 fails the primary acceptance test.** Quality-first inside the band picks a **WR for a roster
already holding seven of them**, while three QBs remain in a 3-deep QB pool. That is failure mode
B, reproduced on demand.

**F3/F5 pass the primary test.** QB-starved → a QB. This is the WR8-vs-QB4 case answered correctly
by a deterministic rule, with the valuation absent.

### And the reverse test earned its keep immediately

**F3/F5 fail the reverse case — and the reason is the formula, not the architecture.** WR-starved
returns a **TE**, not a WR, because my crude deficit blended shortfall and pool scarcity
*multiplicatively*: TE's small remaining pool (13) outweighed WR's larger roster shortfall
(3 held against a 2.38 per-team requirement, 36 remaining).

**So pool thinness swamped roster need** — the same knife edge, tipping the other way. Exactly the
class of "plausible-looking, contextually stupid" answer the operator warned about: a TE for a
2-TE roster is not obviously wrong on screen, and it is wrong.

The mandatory reverse case caught it on its first run. That is precisely why it was made mandatory.

### One structural insight worth keeping

**At full exhaustion, F3 and F2 are the same function.** Band-scoping has nothing to scope when no
row is priced, so the entire value of the band-scoped design lives in the **ramp** — rounds 5–13,
where 5–68% of the field is inside the band and the rest is still meaningfully separated. At the
cliff itself, any band-scoped rule degenerates to whatever its context ordering is.

That reframes what the contextual layer is *for*: it is not primarily a late-draft rescue. It is
the thing that should be gaining influence through the middle rounds, where the valuation is
present but increasingly unable to separate candidates.

### State: no formulation passes both tests

The **architecture** survives — valuation authoritative where it separates, context ordering inside
the band, quality never inert to roster. The **deficit formulation does not**, and the next
measurement is the combination rule, not the framework:

* additive rather than multiplicative shortfall/scarcity;
* scarcity measured against *comparable-quality* remaining players rather than raw pool count
  (36 WRs is not 36 usable WRs);
* a floor on quality so need cannot promote a genuinely bad player — the F2 control shows what
  happens without one.

**Still no implementation. Still no tiebreaker wired. `_consensus_lookup` untouched.**

## D9 — measurement round 7: the double-dip check (and it indicts my own F3)

The operator's warning — *"don't overinflate the effect of this new signalling if it is already
included elsewhere; be cognisant of what information feeds what variables before double dipping"* —
lands directly on the F3 candidate from round 6.

### What `team_acquisition_value` already contains

```
tav = uv + need_bonus + eligibility_bonus
uv  = bpa + time_horizon_adj + risk_adj
bpa = scale(_vor)      _vor = _points − replacement[pos]   (or trade_value − replacement[pos])
replacement[pos] = the player sitting at REMAINING STARTER DEMAND rank
```

| Contextual input | Already inside `tav`? | Entering via |
|---|---|---|
| projected points | **yes** | `_points` in `_vor` |
| my roster construction | **yes — twice** | `need_bonus`, **and** remaining demand inside `replacement[]` |
| positional scarcity (starter demand) | **yes — twice** | the same two paths |
| slot eligibility | **yes** | `eligibility_bonus` |
| multi-year outlook | **yes** | `time_horizon_adj` |
| injury status | **yes** | `risk_adj` |
| **consensus rank / tier** | **no** | reaches `reach_label` and the trade composite only |
| **per-opponent roster composition** | **no** | `replacement[]` uses *aggregate* league demand |

And four sibling fields already encode things a contextual layer would otherwise re-derive:
`positional_forfeit` / `positional_cliff` (cost of deferring this position), `rival_premium` /
`denial_value` (opponent need), `survival_probability` (future availability), `waiting_cost` /
`horizon_floor` (replaceability against the draft horizon).

### The finding: F3's deficit term was a THIRD counting of roster need

`replacement[]` uses remaining starter demand. `need_bonus` adds roster shortfall again. My round-6
deficit multiplied it in a third time — and multiplicatively, which is also how pool scarcity came
to swamp roster shortfall in the reverse test. **The two round-6 failures share one cause.**

### One clean answer already measured

**`trade_value` comes from Draft Sharks exports** (`superflex_idp_rankings`,
`te_premium_dynasty_rankings`, `sleeper_*`), **not from KTC or FantasyPros**. So the trade-value
branch of `bpa` does **not** smuggle consensus into the valuation, and consensus rank remains
genuinely uncounted on the board path. That was worth checking rather than assuming — had
`trade_value` been consensus-derived, consensus-as-tiebreaker would have been a double-dip from
the start.

### The timing implication, which reverses the design

Every double-counted signal above is **live during the ramp and dead at exhaustion**:

* **During the ramp (rounds ~5–13)** — `need_bonus`, `replacement[]`, `positional_forfeit`,
  `rival_premium`, `survival_probability` are all still carrying information. Roster need, scarcity,
  opponent demand and projection are therefore **already counted**. The one genuinely uncounted
  signal here is **consensus rank/tier**.
* **At exhaustion (round 14+)** — `need_bonus` is flat at 0.0, `replacement[]` is gone, and
  forfeit/rival/survival have gone to zero coverage or a single distinct value. Nothing counts
  roster context any more, so roster context is **free to use**.

**This inverts what I proposed in round 2 and again in round 6.** The natural instinct — lean on
roster context during the ramp, and on external rankings at the cliff — is backwards on the
evidence:

| Regime | Already counted | Safe to add |
|---|---|---|
| Ramp (valuation present, discriminating poorly) | roster need, scarcity, opponent demand, projection | **consensus rank/tier** |
| Exhausted (valuation absent) | nothing | **roster context** (and consensus) |

That is a sharper design constraint than anything the previous six rounds produced, and it came
from the operator's warning rather than from my own measurement plan.

**Still no implementation.** The next formulation must be built against this table, not against the
round-6 deficit, which is now known to triple-count.

## D9 — round 8: when a signal fails, should the others take over in equal weights?

**Measured answer: no, and the data says so rather than intuition.**

### Equal weights would give a zero-information signal full influence

From round 3, the surviving signals at exhaustion, scored by distinct values across 10 candidates
(`d` = how many different answers the signal gives — `d=1` means it says the same thing about
everyone, i.e. carries no discriminating information at all):

| Surviving signal | d | Discriminating power |
|---|---:|---|
| consensus rank *(where covered)* | 82/82 distinct | **perfect** |
| `projected_points` | 8/10 | strong |
| `waiting_cost` | 8/10 | strong |
| `horizon_floor` / `horizon_sensitivity` | 6/10 | moderate |
| `need_bonus` | 2/10 | weak |
| `pick_necessity` | 2/10 | weak |
| **`survival_probability`** | **1/10** | **none — same value for every candidate** |

Equal redistribution would hand `survival_probability` — which at exhaustion literally cannot tell
two candidates apart — **the same influence as consensus rank, which separates all 82 covered
players.** That is not a judgement call; it is measurably wrong.

It is also worse than useless: a signal with `d=1` contributes a constant to every candidate, so it
adds nothing to the ordering while *diluting* the signals that do discriminate. Equal weights would
actively degrade the decision.

### Why "just renormalise the survivors" is also wrong here

Proportional redistribution (drop the failed signal, rescale the rest to sum to 1) is the usual
default. It fails for a reason specific to this system: **round 7 showed the signals are not
independent.** Roster need is already counted twice inside `tav`. When `tav` dies, its *components*
do not become newly available — they died with it. There is no clean "remaining share" to
redistribute, because the shares overlap.

### The third option, which fits this architecture better

Redistributing weight to keep a total at 1.0 asserts that the decision is as well-founded as it was
before. **It isn't.** Topping the weights back up to full confidence is a quiet fabrication — the
same class of error as substituting `0.0` for an absent price, which this engine already refuses to
do everywhere else.

The consistent posture is: **let the total shrink, and say so.**

* Rank on the surviving signals, weighted by their **measured** discrimination at that pick — not
  by fixed constants, and not equally.
* Let the aggregate evidence shrink as signals fail, and **carry that shrinkage as a stated
  confidence** rather than hiding it behind renormalisation.

This introduces **no tunable constant**, which matters in a codebase that has already been bitten by
unproven ones (#56: *a bound is not a threshold*; #58/#75: the ruler that drifts 72×). Discrimination
is computed per pick from the candidate set in hand — the same self-calibrating principle that round
5 recommended for the ramp variable, applied to weights instead of to the blend.

It also connects two parked items rather than adding a ninth: the shrinking total is exactly the
*"this ordering rests on less"* statement that **#112** (kind-of-absence has no representation) and
**#116** (the display contract) are both about.

### Status

A proposal grounded in measurements already taken, **not yet tested against the acceptance cases**.
The next formulation round should compare, on the same WR8/QB4 fixtures: equal weights ·
proportional renormalisation · discrimination-weighted with a shrinking total. Equal weights is
worth running **as a control**, precisely because it is expected to fail — a formulation set with no
losing entry is not measuring anything.

## D9 — round 7b: *when* each double-counted signal is actually live

Round 7 said "roster need is already counted during the ramp." Measured per round (SF 12×18),
`d` = distinct values among candidates, `need_max` = the largest `need_bonus` on the board:

| round | priced | `need_bonus` d | **`need_max`** | `elig` d | `forfeit` d | `rival` d |
|---:|---:|---:|---:|---:|---:|---:|
| 1–7 | 72 → 48 | 4.0 | **8.4 → 4.4** | 1.0 | 3.3–3.9 | 3.2–3.8 |
| 8–9 | 37 → 26 | 3.2–3.4 | 4.2 → 4.1 | 1.0 | 3.2–3.5 | 3.2 |
| **10–12** | 17 → 11 | 2.2–2.5 | **1.6 → 1.3** | 1.0 | 3.3–3.8 | 2.7–3.8 |
| 13 | 6.4 | 2.0 | **0.4** | 1.0 | 2.4 | 1.9 |
| 14+ | 3.3 → 0 | 1.2–1.8 | **0.3 → 0.1** | 1.0 | 0.7 → 0.0 | 1.7 → 1.0 |

### The finding: roster need goes *impotent* four rounds before it goes absent

**From round 10, `need_bonus`'s maximum value on the whole board (1.6) is below `NEAR_TIE_BAND`
(2.0).** Even at full strength it can no longer move a candidate across the engine's own threshold
for a meaningful difference. It is **present but unable to act** — which is a different state from
both "live" and "dead", and neither of the two I used in round 7.

So the double-dip boundary is not two-phase. It is three:

| Phase | Valuation | `need_bonus` | Adding roster context would be |
|---|---|---|---|
| **Rounds 1–9** | discriminating (2–38% in band) | real (max 8.4 → 4.1) | **a genuine double-dip** |
| **Rounds 10–13** | poor (26–68% in band) | **sub-threshold** (max 1.6 → 0.4) | **not a meaningful double-dip** — it supplies what the existing term is too weak to carry |
| **Round 14+** | absent | dead (max 0.1) | the only thing left |

### The two curves cross at round 10, and they were measured independently

Round 5 found the valuation's discrimination departing its baseline at rounds 5–7 and reaching
38–41% in-band by rounds 9–10. This measurement finds `need_bonus` dropping below the near-tie band
at round 10. **The point where the existing need signal becomes too weak to act is essentially the
point where the valuation stops discriminating** — from two separate measurements that were not
designed to agree.

That gives the contextual layer a **natural handover point that nobody has to choose**, and it is
observable per-pick rather than being a constant: *roster context may act once `need_bonus`'s own
range can no longer cross the band the engine uses to judge meaningfulness.* No new threshold, no
round number, no tunable — the same self-calibrating principle as rounds 5 and 8.

### A separate observation worth recording

**`eligibility_bonus` has `d = 1.0` in every round of the draft** — it is a constant across
candidates from round 1 to round 18, contributing nothing to any ordering while occupying a term in
`tav = uv + need_bonus + eligibility_bonus`. Whether that is correct for this superflex template
(where most positions are broadly eligible) or is the same latent failure as **#62**
(`positional_bench_appetite` returning 0.0 for every position when none is measurable) is **not
established here** — it is one configuration, and it needs a second template before it is a finding
rather than an observation. Flagged, not claimed.

---

# D9 — the consolidation

Nine measurement rounds converge on one shape. It is **not** a new layer blended alongside the
valuation; it is a **second phase of a term the engine already has**.

## The insight the measurements forced

`need_bonus` and `replacement_levels` die together because **they are the same quantity** —
remaining *starter* demand (round 3). The engine already has the right slot for roster need: an
additive term, in universal-value points, applied in the right place. What it lacks is the
continuation of that term once starters are filled.

**"What does my roster need next" does not become zero when starters fill. It becomes depth.**

That framing dissolves the double-dip problem by construction rather than by scheduling: starter
need is non-zero only while starters are unfilled, depth need only once they are. The measured
decay of `need_max` from 8.4 to 0.1 (round 7b) *is* that handover.

## The consolidated form

```
need(pos) = starter_need(pos)                          # existing need_bonus, unchanged
          + depth_need(pos)

depth_need(pos) = NEAR_TIE_BAND
                × shortfall(pos)                       # GATE   — no shortfall, no need
                × (0.5 + 0.5 · scarcity(pos))          # MODULATE — bounded 0.5–1.0
                × bench_appetite(pos)                  # WEIGHT  — the position's own value decay
```

Each factor is there because a measured failure put it there:

| Factor | Fixes | Evidence |
|---|---|---|
| **Bounded by `NEAR_TIE_BAND`** | need promoting a bad player | Structural quality floor: depth need can break a near-tie but **can never overturn a gap the engine itself calls meaningful**. "I need a QB" can only decide among candidates already indistinguishable |
| **shortfall as a GATE** | scarcity inventing need | Round 9: additive scarcity gave QB **1.0 with seven QBs rostered**, purely because the QB pool was empty |
| **scarcity MODULATES, in [0.5, 1.0]** | pool thinness swamping roster need | Round 6: multiplying let a 13-deep TE pool beat a real WR shortfall |
| **`bench_appetite` as the weight** | uniform depth targets | Round 9: a 2× depth target scored **K at 0.500 against WR at 0.371** — nobody rosters two kickers |

## Why `bench_appetite`, and why it is not a positional special case

The standing rule forbids K/DST special-casing. `bench_appetite` obeys it: it measures **how much
value a position loses across the tier past starter demand**, from that position's own curve. A
backup kicker is worth nearly what the starter is (flat curve → appetite ≈ 0, depth buys nothing);
a backup at a steep position is worth a pick. **K and DEF fall out of the depth calculation on
their own arithmetic**, with no rule naming them.

**This puts #62 on D9's critical path.** `positional_bench_appetite` currently returns 0.0 for every
position when none is measurable — the same failure class as `need_bonus` going flat, from the same
cause. It must be repaired, and repaired **over projections rather than over VOR**, so it survives
where VOR does not. That is a scheduling finding: an item parked as low-priority polish turns out to
be the missing multiplier.

## The three rules that sit around it

1. **Consensus is a tiebreaker inside the band only** — never a term in `need` or `tav`, so it can
   never move a price. Genuinely uncounted elsewhere (round 7: `trade_value` is Draft Sharks, not
   KTC/FantasyPros), so admitting it here is not a double-dip.
2. **Absence is never penalised.** A player uncovered by a ranking source orders on his own merits,
   not below everyone who happens to be covered.
3. **Weights follow measured discrimination, and the total is allowed to shrink** (round 8).
   Renormalising to full confidence asserts a decision is as well-founded as before when it is not.

## The handover point nobody has to choose

**Roster context may act once `need_bonus`'s own range can no longer cross `NEAR_TIE_BAND`** —
measured at round 10, and confirmed by two independent measurements that were not designed to agree
(round 7b). No constant, no round number, no template dependence.

## Honest status

**The primary acceptance test passes** — QB-starved returns a QB. **The reverse case has failed
three times**, each time on the combination rule rather than the architecture, and each failure has
been diagnostic: multiplicative swamping (r6), scarcity inventing need (r9a), uniform depth targets
(r9b). The current form addresses all three but **has not yet been run** — it needs `bench_appetite`
repaired first, which is why #62 moved onto the critical path.

**Nothing is implemented. `_consensus_lookup` is untouched. No production file has changed since 1c.**

## D9 — round 10: the band must NOT become adaptive, and why that is bigger than a formula choice

The question was whether `NEAR_TIE_BAND` should tighten as player quality declines, so that thirty
players stop being lumped into one level. **The answer is no — and the reason is not conservatism,
it is circularity.**

### The feedback loop an adaptive band would create

`NEAR_TIE_BAND` is currently a **fixed measuring instrument**: *"these are close enough that the
valuation cannot meaningfully distinguish them."* Make it a gradient on quality and it stops being
an instrument and becomes part of the thing being measured. Everything downstream moves with it:

* `near_tie_flags` → which players are reported as tied
* the **in-band fraction** → my round-5 measure of discriminatory power
* → the **ramp variable** I recommended keying the influence curve on
* → **when contextual need is permitted to act** (the round-7b handover)
* → how much of the field receives contextual influence
* → and therefore the *apparent* point at which the valuation loses discrimination

**The fix would change the diagnostic that decides how strongly the fix is applied.**

This is worse than a design smell. Rounds 5, 7b and 8 all rest on the in-band fraction being a
*measurement* of the valuation's own resolving power against a fixed yardstick. If the yardstick
moves with the intervention, **those three measurement rounds stop being evidence for anything** —
the ramp curve, the round-10 handover, and the discrimination weighting would all need re-deriving
against a ruler that is itself a function of the answer.

An adaptive band is not a tuning choice. It is an intervention that retroactively invalidates the
measurements used to justify it.

### The right decomposition: separate measurement from interpretation

The band stays **immutable, as the permission boundary**. The open question is a different one:

```
OUTSIDE the band :  valuation wins. Untouched, unconditional.
INSIDE  the band :  secondary information is PERMITTED to differentiate.
WITHIN that layer:  quality / context / need may vary continuously.
```

The band decides **who may be re-ordered**. It never decides **how**. Nothing about the gradient
inside the band touches the statistics of the boundary itself, so every measurement taken so far
keeps its meaning.

### The question this reframes into — and it is not the one I was about to ask

Not: *"should the band be 2.0 → 1.7 → 1.4 as quality falls?"*

But: **"when thirty players fall inside the existing band, is there a secondary signal that
consistently separates them WITHOUT contradicting the primary valuation?"**

Those are different claims. The first assumes the thirty are distinguishable and blames the ruler.
The second tests it. And the two possible readings are genuinely different problems:

* *"These thirty really are equivalent"* → nothing to reveal; a tighter band would resolve noise.
* *"The macro-scale valuation compresses them into one economic tier, but their relative quality
  still has structure"* → a within-band gradient is warranted.

**Only the second justifies anything, and it has not been established.**

### And a confound I had not separated

The instruction to *test whether the engine's ability to discriminate actually changes as quality
declines* catches a real gap in rounds 5 and 7b: **I measured discrimination against draft
progression, and in a draft, later and lower-quality are confounded.** I never established which
one drives it.

Separable cleanly: on a **single** board, compare discrimination among the top-N candidates against
a lower-quality slice of that **same** board. If the low-quality slice discriminates worse *at round
1*, the driver is quality. If it discriminates the same, the driver is draft progression — and the
late-draft compression is about the pool thinning, not about bad players being harder to price.

That distinction changes what the within-band gradient would even be for, and it is measured next.

**Nothing implemented. The band is not being touched.**

## D9 — round 11: it is QUALITY, not draft progression. And that reframes rounds 5 and 7b.

Measured on a **single fresh board** — nothing drafted, so draft progression is held at zero and
only quality varies. Adjacent-gap structure by rank slice:

| slice (rank) | gap median | **% gaps ≤ 2.0** | spread |
|---|---:|---:|---:|
| 1–40 | 1.69 | 51% | 104.6 |
| 41–80 | 0.94 | 69% | 60.9 |
| **81–120** | **0.22** | **97%** | 17.8 |
| **121–160** | **0.10** | **100%** | 11.0 |
| 161–220 | 0.57 | 93% | 44.9 |
| 221–300 | 0.70 | 89% | 71.1 |

### The answer

**Compression is a property of where you are on the quality curve, not of how deep the draft is.**
At ranks 81–160, on a board where *nothing has been drafted*, 97–100% of adjacent gaps already sit
inside the band — the same compression I attributed to rounds 8–12.

**This reframes rounds 5 and 7b.** What I measured as "the valuation's discrimination degrading
with draft depth" is really **the visible candidate set walking down the board's own quality curve
into a region that was always compressed.** As the top 80 come off the board, the candidates a
manager sees simply *become* the 81–160 slice. The engine's ability to discriminate did not
deteriorate; the population it was asked to discriminate changed.

That is a better explanation and it costs nothing — every number from rounds 5 and 7b stands, only
the causal reading changes. It also means the compression is **predictable from the pool alone**,
without waiting for a draft to reach a round.

### The finding I did not expect: compression is NOT monotonic in quality

Ranks 121–160 are the most compressed region on the board (median gap **0.10**, 100% in band), and
then it **partially decompresses** below that — 161–220 at 0.57, 221–300 at 0.70. So it is not
"worse players are harder to tell apart." There is a specific **compressed zone** around ranks
80–160, with more spread both above and below it.

A saturating transform produces exactly that shape. **This is very likely #58 — *"TAV saturation is
information destruction at the BPA normalization layer"* — visible from a new direction**, and it
suggests the compressed zone is an artifact of the normalization rather than a fact about players.
Recorded as a strong lead, **not** a confirmed identification: #58's own diagnosis would have to be
re-read against this before the two are declared the same thing.

### Two corrections to my own work in this round

**The band is not being touched, and this measurement does not argue for touching it.** If the
compressed zone is a normalization artifact, then tightening the band there would be *resolving an
artifact more finely* — the worst of both worlds.

**And I nearly compared two different metrics.** This slice measurement uses the board's
`final_score`; the round-10 percentile measurement used `team_acquisition_value` off the snapshot.
Its 51% for ranks 1–40 is therefore **not** comparable to the constant's stated 72% calibration —
round 10's 66% at round 1, measured on `tav`, is the right comparison, and it is consistent with
the documented figure. The slice comparison above is internally valid because every row uses the
same metric at the same moment; it says nothing about whether the constant is correctly calibrated.

### Where this leaves the within-band question

Round 10 measured the in-band internal structure: with 5–6 players inside the band, the median gap
*between* them runs **0.19–0.56**. Numerically non-zero — but the band exists precisely because the
engine has declared gaps of that size to be *"field noise, not ordering signal."*

**So there is no finer tav resolution to recover.** Any within-band gradient must come from a
**secondary, independent signal** — consensus rank, depth need, projection — and not from reading
`tav` more closely. That is exactly the decomposition the operator specified, and it is now
measured rather than assumed.

## D9 — round 12: the compressed zone is not a scale effect. Ordering information is lost there.

Round 12a's first instrument failed and is discarded: normalising median gap by each slice's own
spread is dominated by outliers differently in each signal, so the three columns were never
comparable. Replaced with **rank correlation**, which cares only about ordering and is
distribution-free.

Fresh board. Within each quality slice, does the engine's ordering agree with two independent
orderings?

| slice | n | engine vs **projection** | engine vs consensus | (consensus pairs) |
|---|---:|---:|---:|---:|
| 1–40 | 40 | **+0.949** | +0.494 | 40 |
| 41–80 | 40 | **+0.831** | +0.275 | 40 |
| 81–120 | 40 | **+0.438** | +0.328 | 19 |
| 121–160 | 40 | **+0.325** | −0.165 | *14 — too few* |
| 161–220 | 60 | **+0.124** | −0.080 | 43 |
| 221–300 | 80 | **+0.640** | +0.363 | 75 |

### The finding

**Agreement with projections collapses from +0.949 to +0.124 through the middle of the board, then
partially recovers.** That column is fully sampled (n=40–80 every row) and the effect is large.

So the compressed zone is **not merely a display or scale problem**. In ranks 161–220 the engine's
ordering is essentially *unrelated* to the projections — and projections are an **input** to that
ordering, via `_vor = _points − replacement[pos]`. Something between the input and the output is
dissolving the ordering.

**Some divergence there is by design** — subtracting a per-position replacement level is exactly
what VOR is for, and it *should* reorder players relative to raw points. So this is not
automatically a defect. What is hard to read as intended is the magnitude: at +0.124 the
relationship is gone, not adjusted.

This is a strong lead on **#58** (*TAV saturation is information destruction at the BPA
normalization layer*) and **#76** (*the ruler carries 94.5% of BPA's movement*), now visible from a
third direction. **Recorded as a lead, not an identification** — #58's own diagnosis has to be
re-read against these numbers before they are called the same thing.

**The consensus column is NOT load-bearing here** and I am not leaning on it: coverage falls to
**14 pairs** at ranks 121–160, so its −0.165 is noise, not an inversion. Only the projection column
supports the finding.

### Which answers the tier-decay question — in the negative

The proposal was that a sharper, non-linear tightening rate could be derived from tier decay. Two
measurements say that cannot be done on this signal:

1. **Round 11: the decay is not monotonic.** Compression peaks at ranks 121–160 and *loosens*
   below. A tightening curve would have to tighten and then un-tighten — a shape with no
   justification in tier structure.
2. **Round 12: in the zone where it matters, the engine's ordering does not track the underlying
   quality signals at all.** Fitting a rate to that curve would be fitting **the transform's
   behaviour**, not the players' tier decay.

**You cannot calibrate against a curve that is mostly the instrument.** The sharper math is the
right instinct applied to the wrong layer — the thing to fix is the layer producing the curve
(#58), not the band reading it.

### What this does to D9's ordering

**#58 moves ahead of the contextual layer**, not behind it. Both #62 (round 9's missing multiplier)
and now #58 are prerequisites rather than adjacent work — and #58 was already blocking formula
tuning under §24 step 14 and blocking D10(B)'s rescale. Three separate lines of work now converge
on the same parked item.

**Still nothing implemented. The band is untouched. No production file has changed since 1c.**

## D9 — rounds 13–14: the middle of the board is GENUINELY ambiguous. My #58 lead was wrong.

### Round 13 — the ceiling on any tiebreaker

Do the two **independent** quality signals agree with each other, by board region?

| slice | pairs | projection vs consensus |
|---|---:|---:|
| 1–40 | 40 | **+0.511** |
| 41–80 | 40 | +0.357 |
| 81–120 | 19 | +0.505 |
| 121–160 | *14 — thin* | +0.160 |
| 161–220 | 43 | **+0.237** |
| 221–300 | 75 | +0.380 |

**This is the ceiling on any within-band tiebreaker: it cannot recover more structure than the
independent signals themselves agree on.** In the middle-late board that ceiling is **+0.16 to
+0.24** — weak.

### Round 14 — production cliffs, and the correction they force

Production cliffs are computed from projected points *within* a position, upstream of the BPA
normalization entirely — a domain-truthful landmark for where tiers actually break.

| slice | **production cliffs** | engine % gaps ≤ band |
|---|---:|---:|
| 1–40 | 11 | 51% |
| 41–80 | **18** | 69% |
| 81–120 | 6 | 97% |
| **121–160** | **1** | **100%** |
| 161–220 | 9 | 93% |
| 221+ | 25 | 89% |

**I expected this to show the compression was manufactured. It shows the opposite.**

Ranks 121–160 contain **exactly one** production cliff — the flattest region of real production on
the board — and that is precisely where the engine compresses hardest. Ranks 41–80 are the most
cliff-dense region below the top, and the engine compresses *least* there.

**The compression tracks real production flatness.** It is not an artifact.

### Correcting round 12

Round 12 recorded the compressed zone as a *"strong lead"* on **#58** (TAV saturation as
information destruction). **That reading is undercut and I am withdrawing it as a lead.**

The simpler explanation covers all three measurements at once. If production is genuinely flat
through ranks 121–220, then:

* **spacing** is genuinely small there → compression is real, not manufactured *(round 14)*;
* **ordering** is easily reshuffled by a legitimate per-position replacement subtraction, because
  the underlying differences are tiny → rho with raw projections falls to +0.124 *(round 12)*;
* **independent signals have little to agree about** → projection-vs-consensus falls to +0.16–0.24
  *(round 13)*.

No normalization defect is required to explain any of it. #58 may still be real on its own
evidence — this simply is not evidence for it, and I should not have called it a lead before
checking the production curve. **The instrument that caught it was the operator's suggestion to
benchmark against production cliffs.**

### And this is the strongest justification the contextual layer has

The consequence is better than the finding I was chasing. If the middle-late board is **genuinely
ambiguous on player quality** — not broken, not compressed by a bug, just genuinely flat — then:

> **Roster context is not a fallback for a failed valuation. It is the legitimate differentiator
> precisely where player quality genuinely does not differentiate.**

That reframes the whole D9 case. "The engine broke, so use context" was always a weak argument.
"These players really are near-equivalent in production, so the right question becomes *which one
does this roster need*" is a strong one — and it is now measured rather than asserted.

It also sets the honest expectations the display must carry: in that zone the system should say
*"these are genuinely close; here is the roster reason to prefer one"* — not present a confident
ordering. Which is exactly round 8's "let the total shrink and say so", arrived at from a
completely different direction.

### What this does NOT license

A more nuanced tiebreaker in that zone is still bounded by round 13's ceiling. **You cannot recover
structure that is not there.** Any formulation claiming sharper discrimination among ranks 121–220
than +0.24 is manufacturing confidence, and the reverse-case test should be extended to catch that.

## D9 — round 15: the engine already has the cliff variables, and it has already ruled on this zone

The reminder that cliff signals are already looked at applies to my own round-14 *instrument*, not
just to the design. Checked, and it cuts both ways.

### My instrument was independent — but only by luck of choosing the right input

`detect_positional_cliff` measures gaps **in `bpa`** — *"A cliff is a drop measured in bpa against
that position's own gap distribution."* It is **downstream of the normalization**, i.e. the very
transform round 12 was trying to check. Had I used the engine's cliff detector as my benchmark, I
would have been checking the transform against itself.

Round 14 used **`projected_points`**, upstream of it. So the conclusion stands — but it stands
because the instrument happened to be the independent one, and that deserved saying out loud rather
than being discovered later.

### The engine's cliff signal is scale-invariant — and then deliberately gated by an absolute floor

`ratio = this_gap / typical_gap`, against a **trimmed** median of the position's own gaps, so the
cliff *tier* is scale-free and survives compression. That is a genuinely well-built signal, and it
explains round 3's measurement: `positional_cliff` still had **7 distinct values among 6 present**
at pick 121, deep in the compressed zone, while coarser signals had faded.

But the ratio is not the last word:

```python
if this_gap < CLIFF_MIN_MATERIAL_GAP:      #  == NEAR_TIE_BAND
    tier = "LOW"
```

> *"A drop smaller than the band this app already calls ordering noise cannot be a tier break,
> however unusual it looks against an essentially flat position's own neighbours."*

**So in the compressed zone the engine's cliff detector deliberately goes quiet** — by an explicit
design decision, with the reasoning written down, validated against three named cases including a
suppressed 0.1-point kicker cliff.

### Which settles the production-cliff idea, in the engine's favour

Round 14's numbers said the compressed zone is genuinely flat production. This says **the engine
already knows that and already refuses to call cliffs there, on purpose.**

So adding a production-cliff term to the contextual layer would do two bad things at once:

1. **Double-dip** with `positional_cliff`, `positional_forfeit` and `cliff_protection`, which are
   live throughout the ramp (round 3: `forfeit` d≈3–4 through round 13); and
2. **Contradict a deliberate, documented decision** — manufacturing cliff signal exactly where the
   engine has ruled, with stated reasoning and validation cases, that there is none.

The second is worse than the first. A double-dip inflates a signal; this would *reverse* a
considered judgement while looking like an improvement.

**Verdict: production cliffs are a legitimate measurement instrument and must not become an input.**
That is the correct use of the operator's suggestion — it told me where to check, and the check
says the engine's existing answer is right.

### The consolidation, updated

The contextual layer takes **no cliff term of its own**. Where cliff structure matters it is already
carried by `positional_forfeit` and `cliff_protection`; where those go quiet, they go quiet
*because the engine has judged there is nothing there* — and rounds 13 and 14 independently agree
with that judgement.

That leaves the within-band differentiator resting on exactly what rounds 7 and 13 said it could:
**roster context (uncounted once `need_bonus` goes sub-threshold at round 10) and consensus rank
(never counted on the board path at all)** — bounded by round 13's ceiling of +0.16 to +0.24
agreement in the middle-late board, which is the honest limit of how confident any ordering there
may claim to be.

---

# D9 — VERDICT. The evidence chain is closed.

Three formulations tested against real board data. **Two killed, one supported with a caveat.**

## What was killed, and why

**1. Band-scoped consolidation — KILLED.** The safety test is decisive: driving a full draft and
comparing top picks against the current engine on identical states,

| rounds | picks | changed |
|---|---:|---:|
| **1–9** (valuation strong, §20-validated) | 108 | **39 — 36%** |
| 10–18 | 108 | 85 |

50% of round 2, 67% of rounds 8–9. **Not a bounded change.** `avg in-band` is already 2.7 by round
2, so band-scoped reordering acts throughout the draft, not where the valuation failed. It would
have altered behaviour validated across §20's 1,293 decision points. Killed on the evidence, not
negotiated down.

**2. `need_bonus` as the within-band key — KILLED.** Measured at exhaustion, `need_bonus` is
**0.0 for every position in 3 of 4 scenarios** (it fires only for TE-starved, where a starter slot
is literally unfilled). With all-zero needs the ordering falls through to consensus, which is
roster-blind, and **QB-starved returns a WR for a seven-WR roster.**

*This also corrects my own Q1 reading.* I measured `rho(depth_need, need_bonus) = 0.82–0.99` and
called depth_need a duplicate. That rho was **Spearman over a mostly-tied vector** — measuring
ties, not agreement. I nearly killed a working term on an invalid statistic.

## What survives — the minimal rule

```
if ANY row on the board carries a price:   return the current ordering, untouched
otherwise:                                  order by depth need, then consensus, then projection
```

| rounds | picks | changed |
|---|---:|---:|
| **1–13** | 156 | **0 — provably inert** |
| 14 | 12 | 4 *(only the picks whose own board had nothing priced)* |
| 15–18 | 48 | 46 |

**Inert by construction wherever the valuation exists**, and it acts only where the current
behaviour is a `player_id` string sort carrying no information at all.

## The caveat: the constants are load-bearing after all

I tried a constant-free `depth_need` — shortfall measured against **the room's own median holding**
rather than a multiple of the starting requirement — to avoid introducing unproven constants (#56:
*a bound is not a threshold*).

**It produced an identical change-count and a different answer.** Acceptance:

| | QB-STARVED | WR-STARVED |
|---|---|---|
| `2× starter requirement` | **QB** ✅ | **WR** ✅ |
| room-relative (constant-free) | **TE** ❌ | WR ✅ |

Room medians are `{QB: 3, WR: 6, TE: 3}` — my roster holds 3 QBs and *so does everyone else*, so
room-relative shortfall reads zero. It measures **"am I behind the room"**, not **"do I have enough
to field a lineup."** In superflex those diverge exactly where it matters.

**A methodological correction I owe:** I declared the two versions equivalent from the safety table,
which counts *how many* picks changed — not *whether they changed correctly*. **Change-count is not
correctness.** The acceptance tests caught what the safety table could not.

So `DEPTH_MULTIPLE = 2.0` is not decoration; it encodes *"carry roughly twice your starting
requirement"*, and removing it silently changes the question being asked. **It remains an unproven
constant under #56 and needs a ruling before this ships** — that is the one open item between here
and implementation.

## On a pacing formula (`2.0 − 0.0025 × next_pick_count`)

**Not recommended, and the measurements say why rather than taste.**

* It would make the **band** a function of draft position, which is precisely the circularity of
  round 10 — the band feeds `near_tie_flags` → the in-band fraction → the ramp variable → the
  handover point. A pacing formula on the band contaminates the diagnostics that judge it.
* Round 4 measured the collapse at **round 13 (1QB)**, **round 14 (SF)**, **round 11 (12×20)** —
  the pacing varies by roster template, so any pick-count coefficient would need re-deriving per
  template and would be wrong on the first untested one.
* And it is unnecessary. **The minimal rule keys on an observable state — "can anything be priced"
  — not on a schedule.** A pacing formula is a proxy for a condition already measurable exactly.

The instinct is sound: influence should follow the signal. The evidence says read the signal
directly rather than modelling its timetable.

---

# #56 isolated: DEPTH_MULTIPLE swept. **2.0 loses.**

Treated as the only unresolved parameter and swept against the acceptance tests across two roster
templates. **Evidence for a threshold, not a defence of 2.0** — and the evidence rejects it.

## Structural finding first: M is a cutoff, not a scale

`shortfall = 1 − (have/req)/M`. M is a **common divisor**, so among positions not clamped to zero
the ordering is *independent of M*. M only decides **which positions count as satisfied**
(`h = have/req ≥ M` → no depth claim).

Confirmed by the sweep: the answers are **piecewise-constant with a handful of breakpoints**, not a
smooth response. Nothing else is "scaled to" 2.0 — `NEAR_TIE_BAND`, appetite share and scarcity are
all independent of it.

## Superflex 12-team

| M | QB-STARVED | WR-STARVED | BALANCED | |
|---|---|---|---|---|
| < 1.90 | K / WR ✗ | | | **fails acceptance** |
| 1.90 – 2.05 | QB ✓ | WR ✓ | **K ✗** | recommends a *second kicker* |
| **2.10 – 4.00** | **QB ✓** | **WR ✓** | **RB ✓** | **all pass** |
| ≥ 5.00 | QB ✓ | **RB ✗** | QB | shortfall saturates at 1 → **roster ignored** |

Both edges are measured failures, not extrapolations.

## 1QB 12-team — the plateau moves

| | lower edge | upper edge |
|---|---|---|
| Superflex | **2.10** | ~5.00 |
| 1QB | **2.20** | ~4.80 |

*(The "QB-STARVED" scenario correctly returns no QB under 1QB: with a 1.0 requirement, 3 QBs is
`h = 3.0` — genuinely not starved. The label is a superflex concept; the formula is right to refuse
a 4th QB in a 1QB league. That is the term behaving correctly, not a failure.)*

**Intersection of the two safe regions: [2.20, 4.00].**

## Verdict

**2.0 is outside the valid region in BOTH templates.** It sits below the lower edge (2.10 SF,
2.20 1QB) and produces the double-kicker answer on a balanced roster in each. It was never
measured — it was assumed, and it is wrong.

**Recommended: `DEPTH_MULTIPLE = 3.0`** — inside [2.20, 4.00], roughly central, maximally distant
from both measured failure edges in both templates.

## Answering the second question directly

**Is 2.0 correct, or is everything else scaled to it?** Neither. M is an independent cutoff; nothing
is calibrated against it. And 2.0 is not correct — it is 0.10–0.20 below the boundary of the region
that passes.

**Does it matter?** **Yes, but only once.** Crossing from 2.0 to anywhere in [2.20, 4.00] changes
a wrong answer into a right one. *Within* the plateau the precise value is irrelevant — 2.20, 2.5,
3.0 and 4.0 give **identical answers on every scenario in both templates.** So the parameter needs
to be on the right side of a boundary; it does not need to be tuned.

That is the strongest possible outcome for #56's *"a bound is not a threshold"* discipline: the
constant is not a dial to be calibrated, it is a **region to be inside**, and the region is now
measured on both ends.

## Residual risk, stated

**Two templates, not all of them.** The plateau edges are template-dependent (`h = have/req`, and
`req` comes from the roster template), so a third template — 2QB, TE-premium, IDP, deep-bench —
could narrow the intersection further. **3.0 is defensible on the evidence in hand and should be
re-checked when a materially different template is first supported**, not treated as universal.
This is exactly the kind of claim #56 exists to keep honest.

---

# D9 CORRECTION — the #56 sweep was partially vacuous; its recommendation is WITHDRAWN

The sweep recorded immediately above (commit `c8bed44`) was instrumented for reachability
before extending it to more templates. **Three of its six scenarios never executed the code
under test.**

`top_pick` orders on the priced branch and only falls through to the depth-need key when
**no** row carries a `final_score`. Measuring the board each scenario actually evaluated:

| scenario | board | priced | fallback |
|---|---|---|---|
| QB-STARVED 7WR/3QB | 117 | **0** | REACHED — valid |
| WR-STARVED 7QB/3WR | 118 | **0** | REACHED — valid |
| BALANCED | 119 | **0** | REACHED — valid |
| QB-ZERO 8WR/0QB | 117 | 6 | **DEAD — priced branch won** |
| TE-ZERO 7WR/3QB | 119 | 15 | **DEAD** |
| RB-STARVED 7WR/3QB/1RB | 118 | 27 | **DEAD** |

A scenario on the priced branch returns the same position at every M. In the segment table
that is indistinguishable from *"passes at every M"* — so three scenarios that **could not
fail** were read as three scenarios that **passed everywhere**, and the safe region was
widened by exactly the constraints they should have imposed.

**What survives:** roster-responsiveness (QB-STARVED vs WR-STARVED) and the BALANCED
double-kicker lower edge were genuinely exercised. **What does not:** the width of
`[2.20, 4.00]`, and therefore `DEPTH_MULTIPLE = 3.0`. **The recommendation is withdrawn.**

This is the same class the audit named in §17.5 and the same one that voided the first
knife-edge run: an instrument that cannot fail proves nothing, and a *silently* inert
instrument is worse than a broken one because it still prints a table.

## Collateral check on the constant (does anything else move?)

- **`DEPTH_MULTIPLE` has no production consumers.** `grep` across the tree returns nothing
  outside scratchpad. Introducing it breaks no existing caller.
- **`NEAR_TIE_BAND = 2.0` (`pick_synthesis.py:266`) is a different 2.0** with real consumers:
  `CLIFF_MIN_MATERIAL_GAP` (derived from it), `decision_regime`, `near_tie_flags`, and 7 test
  modules. It degrades correctly in the depth rule's own regime — `near_tie_flags` returns
  all-`False` when nothing is priced rather than raising or inventing a leader.
- **DEFECT in the proposed formula: it multiplies `dneed` by `BAND = NEAR_TIE_BAND`.** In the
  fallback nothing is compared against `tav`, so as a pure sort key that factor does no
  ordering work — *except* that the key is `-round(dneed, 4)`, and a positive scale factor
  changes which values collapse into ties at 4 dp. `NEAR_TIE_BAND` would therefore silently
  govern depth-rule tie granularity, so retuning the near-tie band (or `CLIFF_MIN_MATERIAL_GAP`
  with it) would quietly reorder late-draft picks through a path no one would think to check.
  **The factor is removed:** the depth term carries its own intrinsic scale.

## The structural edge model (what M_low and M_high are made of)

Ruling taken: `M := (M_high + M_low)/2`, derived per league rather than swept per format.
Both edges fall out of the algebra rather than a fit.

Let `r_p = mine_p / req_p` — bodies held per starting slot. Then
`shortfall_p = max(0, 1 - r_p/M)`.

**Lower edge — annihilation.** `shortfall_p` hits 0 exactly when `r_p >= M`, and a zero
shortfall is *absorbing*: no scarcity or appetite weight can revive it. On a roster filled in
proportion to `req`, `mine_p = R·req_p/Σreq`, so `r_p = R/Σreq` **for every position at once** —
position-independent. Call it the depth ratio `D`. Below `M = D` a proportionally-filled
roster goes globally dark and only quantization survivors (low-`req` slots like K) still
register need. That is precisely the observed BALANCED double-kicker failure.

    M_low ≈ D = len(roster_positions) / Σ starter_slot_counts

`Σ starter_slot_counts` is exactly the count of starting slots — every slot, flex or named,
contributes total 1.0 (`FLEX`: 1/n × n; `SUPER_FLEX`: 0.85 + 0.15); `BN`/`IR`/`TAXI`
contribute 0. So **D is literally total roster spots per starting spot.**

**Upper edge — loss of authority.** `shortfall` ranges over `[1 - D/M, 1]`, so the roster's
share of the signal is `D/M` and decays as `1/M`; once it falls below the spread contributed
by scarcity × appetite, ordering is context-only and the roster is ignored (the observed
"WR-STARVED answers RB" saturation). Requiring the roster to retain at least half the signal:

    D/M >= 1/2   ->   M_high ≈ 2D        =>   M = (M_low + M_high)/2 = 1.5·D

`f = 1/2` is the **one** dimensionless, format-independent constant in the model, and it
replaces a depth multiple that was format-dependent. It is the only fitted quantity and must
be reported per template so it can be checked rather than trusted.

**Provisional corroboration** (against the two edges that were genuinely measured):

| template | R | starting slots | D | measured M_low |
|---|---|---|---|---|
| 1QB 12 | 20 | 9.0 | **2.222** | **2.20** |
| SUPERFLEX 12 | 20 | 10.0 | **2.000** | 1.90 accept / 2.10 kicker-free |

Both templates' lower edges land on `D`. Upper edges (4.80 / 4.00 measured vs 4.44 / 4.00
predicted) are consistent, superflex exactly. **This is corroboration, not validation** — two
points, and the upper edges came from the run whose width is now withdrawn.

## BLOCKER — the rule's live domain is far narrower than assumed

The corpus sweep could not run: every template aborted on its own non-vacuity guards
(`appetite vacuous`, `pool exhausted`, `board still has N priced rows`). Diagnosing that is
the more important result. A realistic 12-team 1QB draft where every team drafts a roster
shaped like its own starting requirement:

| round | picks | board | priced | unpriced |
|---|---|---|---|---|
| 3 | 36 | 297 | 228 | 69 |
| 9 | 108 | 225 | 117 | 108 |
| 13 | 156 | 177 | 69 | 108 |
| 18 | 216 | 117 | 69 | 48 |
| 19 (K) | 228 | 105 | 32 | 73 |
| **20 (DEF)** | **240** | **93** | **0** | **93** |

Pricing decays in **plateaus and cliffs**, not smoothly — and reaches zero only in the
**final round**. Positional bench appetite stays live throughout, so the window where the
rule can fire *and* has its inputs is real but is **one round wide out of twenty**.

Because `_board_order` sorts every priced row ahead of every unpriced one, the top of the
board is a priced row whenever any priced row exists. So the minimal rule — inert unless
*nothing* is priced — governs roughly **5% of picks in this draft, all of them in the last
round**. It does **not** touch the mixed regime (rounds 3–19), where 48–108 unpriced rows are
already being ordered among themselves by `str(player_id)`. **The minimal rule as scoped does
not address #114**, which lives in that mixed regime.

Note the tension with §20.6's "27.8% of an 18-round draft": that measurement and this one
differ in draft construction (here all twelve teams draft identical proportional rosters,
which spreads consumption and keeps pricing alive longer). Window width is
construction-dependent and only one point has been measured. **Recorded as a discrepancy to
resolve, not as a correction to §20.6.**

## What this means for the sequence

Settling `M` is downstream of a question that is now open: **what regime should the rule
govern — only the all-unpriced board, or the mixed board where the unpriced tail is already
being ordered by player-id?** The answer changes how much `M` matters, and possibly whether
`M` is the right parameter at all. That is a scope decision, not a measurement.

---

# D9 SCOPE — what #114 is actually asking, read off the record

## §20.6 measured the all-unpriced board, not the mixed one

> **"60 of 216 picks (27.8%) are made from boards where nothing can be priced."**
> — ARCHITECTURE_AUDIT.md §20.6

`boards with zero priced candidates`: 0/12 at round 11, 2/12 at round 13, **12/12 every round
14–18**. So #114 as *measured* is regime (a) below. The discrepancy flagged in the previous
section is resolved and was not a contradiction: both measurements are of the all-unpriced
regime, and they differ only in **when** it begins — round 14 of 18 there, round 20 of 20 in
the diag2 construction. §20.6's boards carry ~9.4 candidates; diag2 read the whole pool
(93–321 rows). **§20.6 stands; the earlier note is withdrawn as a false alarm.**

## The mixed board is structurally guaranteed, and here is the mechanism

`select_candidates` (`pick_synthesis.py:785`) does not take a single top-N slice:

```python
ranked = sorted(board, key=_board_order)
candidates = list(ranked[:top_n])            # priced-first, so all-priced while any exist
for position, rows_at_position in by_position.items():
    for row in rows_at_position[:depth]:     # BEST-AT-POSITION injection
        if row["player_id"] not in included_ids:
            candidates.append(row)           # <-- an UNPRICED row enters here
candidates.sort(key=_board_order)            # and is tie-broken by str(player_id)
```

Once **any** position has no priced rows left, its best-at-position row is unpriced and is
appended anyway. That is exactly §20.6's *"5.2 priced of 9.2 candidates"* at round 11 — about
five priced from the top-N slice and about four unpriced injected by position. **The mixed
board is not an edge case; it is produced deliberately, from early rounds, by the
best-at-position rule.**

## Two concepts that have been conflated — named separately

**(a) Whole-board fallback.** *When should the entire board stop being ordered by price?*
Fires only when nothing is priced. Decides the actual recommendation. 27.8% of the audited
18-round draft; ~5% of the diag2 20-round draft. This is what §20.6 measured and what the
"minimal rule" addresses.

**(b) Unpriced-tail ordering.** *Among candidates that share the property of having no
measured value, what determines their relative order?* Does **not** decide the recommendation
— `_board_order` puts every priced row first — but it does decide the order the **debate
layer and the UI** receive, which is the confabulation risk recorded at
POST_AUDIT_PLAN.md:163. Present from early rounds via best-at-position.

These are different questions with different blast radii and they need separate acceptance
criteria. `DEPTH_MULTIPLE` is a parameter of the ordering rule and is therefore downstream of
both — **no value is selected here, and 1.5·D is explicitly NOT adopted.** `D` and `2D` stand
as structural reference points only: `D` is where a proportionally-filled roster is
annihilated, `2D` is where the roster retains half the raw depth signal. The midpoint between
them is a design hypothesis, not a discovered constant.

## OPEN QUESTION (surfaced, not decided): may an unvalued row outrank a valued one?

`_board_order` answers this today, silently, with an unconditional **no**. Its docstring
defends only half of that:

> *"it does not substitute a number for an absent score — ... treating that as 0.0 would rank
> it exactly where 'worth nothing' ranks, which is a claim."*

That defends **not fabricating 0.0**. It does not defend ORDER LAST, which is also a claim —
and §20.6 shows precisely where that claim gets hard to hold. Leader TAV by round:

| rd | 8 | 10 | 11 | 13 | 14–18 |
|---|---|---|---|---|---|
| leader TAV | 6.0 | **0.0** | **−3.67** | **−8.58** | None |

**Priced values go negative before pricing collapses.** From round 11 on, `_board_order`
ranks a row *measured at −8.58* above a row with **no measurement at all** — asserting
`unknown < known-bad`, which is a strictly stronger claim than the 0.0 substitution the
docstring rejects. At tav ≥ 0 the current rule is easy to defend; below 0 it is not.

This cannot be answered by loosening the rule, because *why* a row is unpriced is not
currently representable — **#112**, "kind-of-absence stops at the board, and 'never checked'
has no representation." The three kinds have different answers:

1. **no replacement level for the position** — structural absence; unknown, not bad.
2. **no projection from any source** — coverage gap; unknown, not bad.
3. **below every source's cutoff** — weak evidence of genuinely low value; ORDER LAST is fair.

Only (3) justifies the current behaviour, and today all three are the same `None`. **#112 is
therefore a prerequisite for answering this, and the instrumentation below must record the
kind of absence per row rather than assume it.**

## Instrumentation plan (no production change, no value selected)

Architecture to be *tested*, not adopted: priced population keeps its existing ordering
completely untouched; the fallback orders **only within the unpriced tail**.

1. Instrument a realistic draft for regime (b): per round, how many candidates are unpriced,
   how they entered (top-N vs best-at-position), and the **kind of absence** for each.
2. Acceptance-test the tail ordering independently, with the invariant that **no priced pick
   changes** as the pass/fail gate.
3. Only then sweep `M` inside that architecture, reporting results against `D` and `2D`.

---

# D9 RESOLVED BY REDIRECTION — #114 is not an ordering defect, it is a pricing-domain defect

## What the instrumentation found

Instrumenting the mixed board (regime (b)) on the real `narrow_candidates` path, 12-team,
18 rounds, both templates:

* **MIXED is the dominant regime: 16 of 18 rounds.** ALL-UNPRICED never occurred at all in
  this construction. Restricting a rule to `priced == 0` would have addressed a case that
  barely happens here.
* **100% of unpriced candidates entered via best-at-position.** Not one arrived through the
  `top_n` slice — confirming from measurement what the code read said.
* Then the per-position breakdown showed the actual defect, and it is not about tiebreaks.

Whole board, 12-team 1QB, after round 15:

| position | priced | unpriced |
|---|---|---|
| DEF | **32** | 0 |
| K | **37** | 0 |
| QB | 0 | **15** |
| RB | 0 | **36** |
| TE | 0 | **24** |
| WR | 0 | **9** |

`narrow_candidates` →
`[('DEF', 17.0), ('K', 15.0), ('DEF', 15.0), ('DEF', 14.0), ('DEF', 14.0), ('RB', None),
('WR', None), ('QB', None), ('TE', None)]`

**Four defenses and a kicker, ahead of every remaining running back, receiver, quarterback and
tight end.** Positions do not degrade gradually — they flip to wholly unpriced.

## The mechanism, and why it is structural

`replacement_levels`' own docstring states the domain: *"defined only while a position has at
least one whole starting slot still unfilled ... the position's key is OMITTED."* That is
correct and stays. The failure is what happens downstream:

1. Every team fills its RB starters → RB league-wide demand < 1 → RB omitted. **Correct.**
2. Every remaining RB gets `_vor = NaN` → `bpa` NaN → `final_score = None`. **Defensible** —
   the module refuses to fabricate a number.
3. `_board_order` sorts `None` last → every RB below every priced K. **This is the defect.**
4. **K and DEF are drafted last, so they are the last positions still carrying demand.** The
   inversion is therefore guaranteed rather than incidental — it is the K/DST explosion (#37)
   arriving through a different door.

So #114's headline ("decided by a player-id tiebreak") describes a symptom. Ordering the
unpriced tail perfectly — by depth need, consensus, anything — **would not have moved a single
one of these picks**, because the whole tail sits beneath five kickers either way. The
depth-need fallback was aimed at the wrong defect, and no value of `DEPTH_MULTIPLE` would have
mattered. **D9's minimal rule is not implemented, and #56 stays open and unneeded for now.**

## The repair: `predraft_replacement_anchor`

When a position's level is omitted **for exhausted demand**, price its rows against the
position's **pre-draft** level instead of dropping them off the board.

Why that anchor, and why computed rather than remembered: `replacement_levels` already records
that while demand stays positive, rank shrinkage and pool drain cancel exactly, so the live
level is algebraically identical to the static pre-draft one. The last live level therefore
*is* the pre-draft level — **verified directly, not assumed**: across 1QB-12, superflex-12 and
1QB-14 full drafts, every position's first observed live level equals its pre-draft level to
within 1e-9. That equality is what lets the anchor be a pure function of (player universe,
league settings) rather than a memo of earlier calls. A memo was the first implementation and
was **rejected**: it would have made a board's answer depend on which boards were built before
it, breaking `replacement_levels`' own "never cached across picks" contract.

**Never applied to the `startable_floors` branch.** That branch declines because no remaining
player clears the startability threshold — a different fact from "demand is filled" — and
reviving a stale anchor there would assert a startable replacement exists where the
measurement says none does. Measured cost of that restriction: **zero.** Superflex still
repairs 7 of 7 affected rounds with 9 floor-declines left standing.

**Provenance recorded (#112).** Every board row now carries `replacement_basis` —
`live_starter_demand` or `predraft_anchor`. A price resting on the pre-draft anchor is a
weaker claim than one resting on live demand, and the board now says which it is instead of
presenting both as the same number. Carried on both the balanced and upside serializations,
since `upside_score` reads the same `bpa` the anchor feeds.

## Evidence: HEAD vs working tree, identical draft states

| invariant | result |
|---|---|
| **INV1** every player priced before keeps the **identical** `final_score` | holds in every template |
| **INV2** the priced set only ever grows | holds |
| **INV3** no newly-priced score exceeds that position's round-1 board maximum | holds |
| **INV5** `replacement_basis` present and always one of the two legal values | holds |

Two probes were **discarded as invalid before these numbers**, and both are worth recording:

1. A "static pre-draft" arm that recomputed full demand against the **depleted** pool. It
   inflated a round-15 QB to `271.0` — higher than anything on the round-1 board. An
   implementation bug in the probe, not a property of the idea, but it would have been
   reported as one had the absurd number not been visible.
2. The monkeypatching battery, once the repair landed in production: both of its arms then
   contained the fix, so it silently began comparing the change against itself. Replaced with
   a true `git show HEAD:draft_room.py` before/after. **This is the same vacuity class as the
   #56 sweep** — the third instance this phase — and the lesson is now explicit: an
   instrument that shares code with the thing under test stops being an instrument.

## What this does NOT settle

* **The trade_value branch is unmeasured.** The synthetic universe is built from the
  projection set, so every row took the points path and `_points` was the only `value_col`
  ever observed. The same fill is wired on the trade_value branch for consistency — the same
  defect through the same mechanism — but it is **untested**, and that is a real gap, not a
  claim of coverage.
* **The unvalued-vs-valued question is narrowed, not answered.** With skill positions priced
  again, the crossing case gets rarer, but `_board_order` still asserts `unknown < known-bad`
  wherever a row remains unpriced. #112's three kinds of absence still collapse to one `None`.
* **1QB-14 keeps K/DEF on top and that is correct.** Revived skill players score −2 to +12.7
  against kickers at 15–19, so `K 19.0` genuinely beats `RB −1.0`. The change is not that
  skill players win; it is that the comparison now happens **on evidence instead of on missing
  data**. Across the battery, 51 K/DEF-on-top rounds: 44 flip to a skill player, 7 stay.

## Does fuller Sleeper coverage make this obsolete? Measured: no.

The repair would be a stopgap only if the absence were a **data gap**. It is not. On the
pre-repair board at the state where four skill positions are wholly unpriced:

| position | unpriced **with** a points projection | unpriced with **no** projection |
|---|---|---|
| QB | 15 | 0 |
| RB | 36 | 0 |
| TE | 24 | 0 |
| WR | 9 | 0 |

**84 of 84 unpriced rows already carry a points projection.** Not one of them is missing data.
They are unpriced because their position has no unfilled starting slot left in the league, so
`replacement_levels` correctly declines to produce a level — a **domain boundary in the demand
model**, which no amount of additional source coverage can close. A perfect projection for
every player in the NFL would leave all 84 rows exactly as unpriced as they are now.

What fuller coverage *would* change, none of which touches this mechanism:

* **It shrinks the untested surface.** The `~has_proj` trade_value fallback is the branch this
  phase could not exercise; better coverage moves rows off it onto the points path.
* **IDP moves onto the points path.** Sleeper covers IDP where Draft Sharks does not, so IDP
  positions currently lean on the trade_value fallback.
* **The affected row count grows.** A deeper priced pool means more rows sitting at a position
  whose demand has expired — the defect gets *bigger*, not smaller.
* **The measurements here age, the mechanism does not.** Board sizes, the round at which each
  position flips, and the 42/34 unpriced counts all come from the current projection set and
  will move. The domain boundary that produces them will not.

---

# ANCHOR REPAIR — VERIFICATION RESULT AND DISPOSITION

*Written before the remediation edits, so the record exists at the moment of the decision
rather than being reconstructed after it. See #37 for why that ordering is now the rule.*

## State of play

* `cf06959` — the `predraft_replacement_anchor` repair, on `ui-authority-pass`. `main` frozen.
* `8344714` — doctrine + README updates (records the FINDING, independent of the repair).
* **The full suite does not pass on this branch right now**: `Ran 1548 tests ... FAILED
  (failures=14, errors=1, skipped=1)`. `cf06959` was committed with that verification still
  running, because a stop hook required a commit. That was disclosed in its message.

## Evidence gathered

**Instrument 1 — full suite, complete capture.** All 15 failures fall in three modules and
share one root cause: fixtures assert their late board carries unpriced rows, and in a 1QB
league it no longer does.

| module | failures |
|---|---|
| `test_survival_evidence` | 7 |
| `test_absence_survives_consumers` | 4 (1 as ERROR) |
| `test_downstream_contracts` | 4 |

**Four of the fifteen are explicit non-vacuity guards** — `test_the_fixture_reaches_a_board_
that_cannot_price_everything`, `test_the_late_board_actually_contains_absence`,
`test_the_late_board_really_does_carry_unpriced_rows`, `test_a_whole_position_can_be_unpriced_
which_is_how_one_reaches_the_layer`. Those guards are the reason this class failed **loudly**
instead of going quiet. The discipline worked, and it was already here before this phase.

**Instrument 2 — vacuity sweep** (`scratchpad/vacuity_sweep.py`). Nine absence-related modules
run twice, anchor disabled then live, tallying unpriced rows per test. The control arm is the
anchor-disabled run, and it is asserted to differ before anything is concluded.

```
tests that never build a board (unaffected):        236
tests still exercising unpriced rows AFTER:           0
tests that LOST THEIR SUBJECT:                       10   (5 loud, 5 silent)
```

The five silent ones, graded rather than lumped:

| test | unpriced before | verdict |
|---|---|---|
| `test_a_priced_targets_survival_is_still_reported_as_measured` | 819/1833 | **hollowed** — control arm of a two-sided contrast whose other side now fails |
| `test_build_snapshot_survives_every_late_round` | 2407/7683 | **hollowed** — "survives" meant "survives absence" |
| `test_the_snapshot_is_identical_across_repeated_builds` | 1701/3807 | partial — determinism still tested, absence-determinism not |
| `test_bpa_is_identical_for_every_team_at_the_same_board_state` | 63/474 | incidental — team-agnosticism is a property of priced values |
| `test_universal_value_is_also_team_agnostic` | 63/474 | incidental — same |

## The decision, and the gate that governed it

Stated in advance: **if the sweep showed a large silently-disarmed population, revert
`cf06959`** rather than adapt tests around it. A change that quietly neutralises dozens of
assertions is worse than the defect it fixes, even when the defect is real.

**Gate not met.** Two tests materially hollowed, one partial, two incidental. Proceeding with
remediation rather than revert. Recording the gate here because a threshold declared before
the measurement is worth more than one justified after it.

## Why not simply weaken the failing tests

They are good tests. They pin the absence contract's foundational claim — that a priced `0.0`
and an absence are different things — and `test_a_priced_zero_and_an_unpriced_row_are_
distinguishable` guards **both** sides of its own pair. The repair does not violate that
contract. It removes the population in which the contract can be **demonstrated** in a 1QB
league, which is a subtler cost than a regression: *a contract you cannot exercise is a
contract you cannot defend six weeks from now.*

## Remediation: move the fixtures to superflex

Measured reachability after the repair:

| league | round 16 | round 18 | round 20 |
|---|---|---|---|
| 1QB 12 | **0 unpriced** | 0 | 0 |
| SUPERFLEX 12 | **11 unpriced (all QB)** | 11 | 9 |

The surviving unpriced state is the `startable_floors` decline the repair deliberately does
NOT revive — no remaining QB clears the startability threshold. So the fixtures keep every
assertion, and their subject improves: the row is unpriced for a **measured** reason rather
than a demand-domain artifact. `test_survival_evidence` already carries a superflex `ROSTER`
at line 218, so there is in-module precedent for the shape.

Known consequence, accepted and recorded: **the absence contract will be exercised only in
superflex.** If the startability floor is ever changed, these fixtures lose their subject
again — but loudly, because their non-vacuity guards remain.

## Picking this up cold

Open, in priority order: (1) apply the superflex fixture move to the three modules and re-run
them, then the full suite; (2) `#123` — the `trade_value` branch is wired but untested;
(3) the anchor roughly doubles board-build time (0.52s -> 0.98s), fixable by content-keyed
caching since it does not depend on picks; (4) `#122` — the unmarked `mean_rate` imputation;
(5) `#61` re-scope, now settled by measurement rather than argument; (6) `#37` evidence
discipline. `DEPTH_MULTIPLE`, D9's minimal rule and Register 2 remain parked with no reason
to exist.

## VERIFICATION RESULT — both instruments pass

| instrument | before remediation | after |
|---|---|---|
| full suite | `FAILED (failures=14, errors=1)` | **`Ran 1548 tests ... OK (skipped=1)`** |
| tests still exercising unpriced rows | **0** | **10** |
| tests that lost their subject | 10 (5 loud, 5 silent) | **0** |

Passing was never the claim. A suite that goes green by removing what a test observes is worse
than one that fails, so the gating number is the second row, not the first.

**Recorded honestly: the restored population is narrower, not equal.** The largest fixtures
carry **143** unpriced rows where they previously carried **910** — superflex strands only QBs
below the startability floor, where 1QB previously stranded four whole positions. The
demand-exhausted rows are correctly priced now, so the reduction is the intended effect, but
it is a genuine loss of coverage breadth and belongs in the record as a cost rather than a
footnote.

---

# SUITE-LEVEL RESULT OF THE ANCHOR CACHE, AND #61 RE-SCOPED

## The cache is worth more than the per-board measurement showed

| | before the cache | after |
|---|---|---|
| full suite | `Ran 1548 tests in 1011.5s` | **`Ran 1575 tests in 573.8s`** |
| single board, anchor firing | 0.602s | **0.260s** |
| single board, anchor not needed | 0.512s | **0.336s** (nothing is built at all) |

**43% off total suite runtime**, and green at 1575 tests. The per-board figure understated it
because a large share of the suite builds boards. The laziness repair is the half that matters
when no position is exhausted; the cache is the half that matters when one is.

## #61 — re-scoped in CDME_CONTRACTS.md rather than built

The two-register policy is preserved as written, with a re-scope section appended. Its rule 2
justifies its own scope on *"the mixed regime spans six of twelve late rounds"*, and that is
no longer true: a 1QB board now carries **zero** unpriced rows at rounds 16, 18 and 20, and
superflex retains **11**, all QBs, from the `startable_floors` decline the anchor deliberately
does not revive.

**Build nothing yet.** Seven rules and twelve invariants for eleven rows in one format is
apparatus looking for a job. **Keep rules 5, 6 and 12** as correctness debt — they argue from
correctness rather than volume, so rarity lowers their priority without making them wrong.
**Delete rules 3 and 7 and the "report need, not value" apparatus** — all sized for the old
population. **Keep the semantic distinction** (value / need / unknown), which is what the
engine reasons with; the register was only ever one implementation of it.

**#112 is downgraded, not closed** — kind-of-absence now serves ~11 rows in one format.

**What would reverse it:** a format whose demand exhausts while its pool stays deep, or a
source thin enough that rows carry neither projection nor trade value. Both are now
*observable* rather than assumed — `replacement_basis` and the unpriced count sit on every
board row, so this population can be re-measured at any time instead of re-argued.

---

# #51 — THE IDP ADVERSARIAL PASS: A SUPPLY DEFECT, NOT AN ARITHMETIC ONE

IDP was chosen as the hostile domain because it is the one position family where this app's data
sources behave differently from everywhere else, and every valuation decision in the engine was
designed against offense. The pass found **no arithmetic defect**. The trade-value pricing branch
does the right thing with what it is given, labels itself honestly (`bpa_source ==
"position_relative_trade_value_vor"`, `confidence == 35.0` against offense's `80.0`), and prices
every row it admits.

The defect is upstream of all of that, and it is structural.

## What was measured

Against the committed baseline and the repo's own realistic IDP league shape
(`run_idp_draft_validation.IDP_LEAGUE` — `DL,DL,LB,LB,DB,DB,IDP_FLEX` over 12 teams):

| | IDP | offense | K/DEF |
|---|---|---|---|
| players in the universe | 415 | 280 | 69 |
| carry a season projection | **0** | 264 (94%) | 69 (100%) |
| carry a 3-year projection | **0** | 264 | 0 |
| carry a trade value | **76 (18%)** | 264 (94%) | 26 (38%) |
| **admitted to the pool** | **76** | 264 | — |

Zero is the number that matters, and it is zero rather than few: Draft Sharks projects **no IDP
player at all**, for `projection` and `proj_3yr` alike. So `build_available_pool`'s admission
rule — *"a real number means a season points projection OR a trade value"* — has only one live
branch at IDP, and that branch covers 18% of the position family.

**The drop is not an identity failure.** All 415 match a canonical record; 339 match a record that
is empty of numbers. That distinction decides the remedy: a matching gap is repaired at the name
boundary (#82's territory), a coverage gap is repaired by acquiring data.

## The consequence: supply below the league's own starting lineup

League-wide IDP **starter** demand in that shape is **84** — 24 DL + 24 LB + 24 DB + 12 IDP_FLEX,
which draws on the same three positions. Admitted supply is **76**.

* **DL: 24 supply against 24 demand.** Zero margin.
* **DB: 23 supply against 24 demand.** Below its own slot demand, before a single bench spot.
* Offense, on the identical board and call, clears its own starter demand **2.75x** (264 against
  96). The pool is not globally thin; it is thin at exactly the family nothing projects.

## And it is not a paper shortfall — the draft actually runs out

Simulated: 12 teams, engine-selected picks (each team takes its own board's top row), 20 rounds
against a 23-round league (15 starting slots + 8 bench).

```
r 8: DL= 12 LB= 15 DB= 18      r13: DL=  3 LB=  6 DB=  3
r 9: DL= 12 LB= 13 DB= 14      r14: DL=  1 LB=  5 DB=  0   <- DB exhausted
r10: DL=  9 LB= 12 DB= 12      r15: DL=  0 LB=  0 DB=  0   <- DL and LB exhausted
```

**Every position exhausts outright** — DB in round 14, DL and LB in round 15, with a third of the
draft still to run. All 76 admitted IDP players are drafted and **8 of the league's 84 IDP starter
slots can never be filled by anyone**.

`unpriced` was **0 at every round**, so this is emphatically not #114's unpriced-tail phenomenon
wearing a different hat. The board does not run out of *prices*; it runs out of *rows*.

This is the same shape as the K/DEF supply defect `build_available_pool`'s own docstring records
(*"supply capped at 13 of 37 kickers … drafting them emptied the position to zero"*). That one was
repaired by widening admission from *trade value* to *points OR trade value*. **The same fix does
nothing here, because the widened half is empty.**

## Why external_values is not the fix, and must not be made one

The one remaining offline source with IDP rows is `external_values` — 324 of them, from
FantasyPros and ESPN, and 124 of the 339 dropped players have a row there. It is not a latent
value source:

1. Those 324 rows carry `value_1qb` and `value_2qb` for **exactly zero** of them. They carry a
   **rank**.
2. Admitting a rank as a value is the cross-register laundering #61 and #70 spent the whole audit
   removing — a rank is a value comparison already collapsed into an integer.
3. That filter **is** the CDME ingestion boundary, the same standing rule that forbids solving the
   1QB consensus gap by adding FantasyPros to `_consensus_lookup`.

## The remedy is an input, not a code change

Live Sleeper IDP projections, scored through this league's own `scoring_settings`.
`build_available_pool` **already has that wiring** (`sleeper_projections` + `scoring_settings` →
`score_projection` → `sleeper_points`), and its docstring already names IDP as the case it exists
for — *"this DB is projected for 7 sacks, and this league gives 8 points per sack"*. It is
unreachable from this environment (#88 and #120, both blocked on network access).

**So: schedule acquiring the input, not designing around its absence.** This is the same
disposition #49 already carries for real K/DEF/IDP boards, and it is now measured rather than
assumed.

## What was built

`test_idp_supply_boundary.py` — nine tests pinning every number above, in the direction that
matters: **they fail if IDP supply changes in either direction.** A source landing real IDP points
is good news that should still stop the build and be read, not absorbed silently; the shortfall
getting quietly worse should do the same. Non-vacuity is explicit throughout — offense and K/DEF
coverage is asserted in the same calls, so "zero IDP projections" can never be a broken column
read, and the supply shortfall can never be a pool-wide thinness.

No production code changed.

---

# #97 / #98 — RESEARCH INGESTION: ONE ITEM BUILT, ONE BLOCKED, FIVE DECISIONS

Seven items were carried across §6 and §7 as *"each needs a decision, not a fix."* Sorted by what
they are actually waiting on, rather than by section, the seven fall into three groups — and the
sorting is the useful part, because two of them turned out not to be waiting on a decision at all.

## Built: §6.5's evidence snapshot — and it is also #106

§6 asked that a stored finding carry a URL, a retrieved-at, and an excerpt, so a claim stays
checkable after its source changes or disappears. **The obvious implementation is the wrong one**,
and the reason is the section's own mandate: adding a URL field to the Moderator's `SOURCE
FINDING` line asks a model for a citation, and **a model asked for a citation produces one whether
or not it has one.** That manufactures provenance rather than recording it, in a store whose ranks
feed the composite valuation score at a low weight.

What was built instead reads what the **provider responses themselves report retrieving** — all
three providers run live web search server-side and all three report grounding in their own shape
(`web_search_tool_result` blocks, `grounding_metadata.grounding_chunks`, `url_citation`
annotations). `provider_meter.sources` normalises them, `sources_since` reads one debate's own
ledger window, and `bot_research.add_finding` stores it.

**This closes #106 as the same mechanism, not a second one.** §16.5 recorded that a finding could
not name its origin — bot search versus the user's own captioned upload — and `build_context`'s
own prose said so, hedging every finding with *"whether that was a bot's live search or the user's
own reference material."* That sentence is gone; each finding now carries its own tag.

Two properties are load-bearing and are pinned by tests:

* **The scope is the DEBATE, never the claim.** Which page backs a given `SOURCE FINDING` line is
  a join nothing in this system can make — the line carries no citation. The stored field is named
  `debate_sources` and the prompt says *"DEBATE-level, not this claim's own citation"* in the
  model's own reading order.
* **Three states, not two.** `panel_retrieved` / `unattributed` / *no tag at all*. A row written
  before the snapshot existed **never checked**; a row that recorded no sources **checked and
  found none**. Stamping the first with the second's label is a provenance claim about rows that
  predate the mechanism — the never-checked-versus-checked-and-absent distinction #112 left open
  at the board, applied here where it is cheap and the rows are few.

`unattributed` is not a failure state. It covers a chair reasoning from its given context, a chair
reasoning from its training, a grounding shape this app could not read, and a call that never
searched. Four different things, and nothing separates them — so the field says UNKNOWN rather
than picking one.

**Honesty bound, same as the completion extractors beside it:** the tests prove *this code reads a
given shape correctly*, against stand-in objects. What a live provider actually returns is still
unverified from this environment — no provider SDK is even installed here — and stays recorded
under **#120**.

## Blocked, with the prerequisite already named: §6.4 + §6.5's lifecycle half

A finding's identity (representing *"two sources disagree about this player"* instead of silently
dropping one) and its lifecycle (corroborated / disputed / retracted / expired) are one design;
doing either alone would need redoing.

**Measured: the store is empty.** `bot_research.load_findings()` returns `[]` and
`data/baseline/bot_research.json` does not exist. Designing a disagreement key and a five-state
lifecycle against zero rows is machinery looking for a job — the identical mistake the **#61**
re-scope exists to prevent. **Prerequisite: real findings.** Not a decision.

## Five decisions, each stated as a choice rather than a to-do

| # | The question | Options | Recommendation |
|---|---|---|---|
| §6.3 | Is it *intended* that a fresh panel finding outweighs a stale vendor number? The crossover is now measured at **29–83 days**. | (a) yes, state it as policy; (b) no, cap a finding's recency weight below the vendor's; (c) make the crossover a setting | **(a)** — it is what the code already does and the measurement supports it; what is missing is a stated intent, not a change. |
| §6.2a | Does a finding need re-adjudication by something other than the Moderator that wrote it? | (a) no, the panel's own gate is the bar; (b) a second independent pass; (c) a human confirm step | **(a) for now, with a named trigger.** With one user and a low composite weight the panel gate is a defensible bar. It stops being one under §13.5's hosting model — that is the trigger, not a date. |
| §7.4 | Should cited sources be restricted to an allowlist? | (a) no allowlist; (b) allowlist for anything that feeds the composite, free for prose; (c) full allowlist | **(b)** — it splits along the line that already matters: a rank changes a price, a narrative does not. |
| §7.6 | Should retrieved content be fenced as untrusted in the chairs' prompts? | (a) fence it; (b) leave it | **(a) — BUILT, see below.** It was the largest item here and it has its own verification. |
| §7.10 | Should the 11 unattributed baseline CSVs get provenance records? | (a) write them; (b) leave them | **Not mine to answer.** Writing one asserts the terms under which a *paid subscription export* is retained and redistributed. That is the owner's call, and it is the one item here I decline rather than defer. |

**The inversion §7.10 found is worth restating, because it is the opposite of what one expects:**
the *secondary* sources are documented and the **primary valuation input is not** — the
highest-weighted source in the composite (1.3), the one feeding CDME's `bpa`, has provenance only
as prose in `README.md`.


---

# §7.6 — THE FENCE: WHAT THE APP IS SAYING VS WHAT IT IS SHOWING

`build_context` returned one flat string. Into that single channel, adjacent to the app's own
directives, went raw uploaded file text, user-written captions, prior model prose replayed as
memory, past verdicts re-presented as fact, and user notes. A chair had nothing but content to
tell "the app is telling me this" from "an uploaded file is saying this."

## What was built

**Nine fenced spans**, eight inside `build_context` and one at the chat call site:
conversation memory, open to-do text, past objectives and their resolution notes, past decision
outcomes, pinned messages, user-typed captions, panel findings, panel comparisons, and — the
rawest of them — chat-scoped attachment bytes. Two more inputs never went through
`build_context` and are fenced at their own call sites: `classify_unknown_upload`'s file excerpt
and `summarize_history`'s transcript.

**Not fenced:** anything the app, Sleeper, or a vendor file authored — the league line, roster
tables, freshness, pick values, board numbers. That is the distinction §7 asked for: *what the
app is saying stays outside; what it is showing goes inside.*

## Three design decisions worth stating

**1. The markers are stripped from the body, and that — not the tokens — is the mechanism.** A
delimiter content can contain is not a delimiter: an uploaded file that writes the closing token
ends the fence early, and everything after it reads in the app's own voice. `fence()` removes
every marker-shaped run from the body before wrapping it. Deliberately *not* a per-call random
nonce: a nonce has to appear in the system prompt too, which changes the cached prefix on every
call, and stripping closes the same hole without that cost.

**2. Stripping removes punctuation, never evidence.** The quieter failure is over-stripping —
silently editing the user's own material while claiming only to remove markers. `>>>`, `>`, `<`,
`</div>` and the bare word "untrusted" are all normal in this domain and all survive untouched;
a removed marker leaves a space rather than joining the words either side of it. Both directions
are pinned by tests.

**3. The contract says fencing is about AUTHORSHIP, not credibility** — and this is the part
easiest to leave out. A chair told only "this is untrusted" starts quietly discounting the user's
own notes and the panel's own findings, which are among the best evidence it has. That failure is
silent and looks like caution. The contract says so explicitly, and a test asserts the sentence
is there.

## Why it is a joint change, and where the fence stops

*"A delimiter the chair prompts do not explain is decoration"* — the audit's own words, and the
reason this was never a one-line fix. The contract is defined once in `untrusted.CONTRACT` and
appended to all **seven** prompts that can now receive a fence (Quant, Beat, Contrarian,
Moderator, Summarizer, Upload-classify, Condense-to-objective), so the fence and its explanation
cannot drift apart. A test fails if any of the seven loses it.

`pick_debate`'s three chairs are **deliberately not fenced**, recorded so the omission is a
decision rather than an oversight: they never receive `build_context`: they read
`format_snapshot_for_llm`, which renders a `PickSnapshot` the engine computed. The only
externally-sourced strings in it are player names out of Sleeper's own database. Fencing a
computed board would teach those chairs to discount the one thing in their context that is not
authored at all. A test inverts if `build_context`, chat history, attachments or stored findings
ever reach that path.

## Verification

`test_untrusted_fence.py` (16 tests) pins the primitive; `test_research_authority_boundary`
carries the wiring, with its own §7.6 characterization **inverted** — it used to assert that
`"<untrusted"`, `"BEGIN UNTRUSTED"` and friends appeared nowhere in `build_context`.

Three planted mutations, each reverted, each producing a failure: removing the fence from the
attachment append, making `fence()` stop stripping forged markers, and dropping the contract from
one prompt.

---

# #102 — THE STORE CONCURRENCY MODEL: ONE FAILURE WAS RECORDED, TWO WERE REAL

§11.4b recorded a lost update as demonstrated and a torn write as **undemonstrated**, with §7.8's
rule attached: this programme does not make production changes for undemonstrated failures. So
both were demonstrated first, on real files, through the real functions.

## What the measurement actually found

**The lost update is not an edge case under contention — it is near-total loss.** The audit's
scenario interleaved `_load`/`_save` by hand, which was a fair model of the old code. Re-measured
on the **production call path** instead — 8 concurrent processes calling the real public
functions 25 times each:

| store | expected | survived (before) | survived (after) |
|---|---|---|---|
| `todo_log.add_todo` | 200 | **6** | 200 |
| `data_merger.save_alias` (global; feeds valuation, §16.9) | 200 | **9** | 200 |

97% and 95% loss.

**The torn write reproduces, and it is the worse half.** One process rewriting a 718 KB store
while three read it, through the same `Path.write_text`/`read_text` calls every store used:

```
98,405 reads | 3,920 clean | 2,529 JSONDecodeError | 91,956 read an EMPTY file
```

`write_text` truncates before it writes. And every `_load` in the tree had this shape:

```python
except (json.JSONDecodeError, OSError):
    return []
```

**A transient read error became an empty store, and the next ordinary write persisted it.**
Measured end to end: a store holding five objectives, given one torn read, held exactly **one**
after the next `add_todo` — the new one. Four gone, silently, **with no race between two writers
required.** One writer mid-write and one reader is enough.

## The mechanism, and why it is one rather than two

`os.replace` is atomic: a reader sees the complete old file or the complete new file, never a
prefix. That removes the torn read *at its source* rather than teaching every reader to cope. The
lock then removes the lost update by making load-and-write one indivisible step — which is why
`store_io.mutate` **loads for you**. The lost update was never a missing lock so much as *a load
that happened outside one*; a caller that cannot read separately cannot reintroduce it.

Two lock layers, covering different cases: a process-wide `RLock`, because Streamlit serves many
browser tabs from **one process** so the common multi-tab case is threads and not processes at
all; and an OS file lock on a **sidecar** `.lock` file for genuinely separate processes. The
sidecar is not incidental — the data file's inode is replaced on every write, so a lock held on it
would protect a file that no longer exists. Both are reentrant by depth count, because these
stores nest.

## The third piece: a damaged store is not overwritten

`store_io` refuses to write over a file it could not parse, and clears that refusal as soon as the
file parses again. Losing the one item being added beats losing everything already there, and the
bytes stay recoverable rather than being replaced by a one-element store.

That guard has a cost — the app then runs with an empty view of that store and silently drops
writes to it — so it is **surfaced**: `warn_about_unreadable_stores()` tells the user the file was
left alone, that the view is empty, and that changes are not being saved. A guard nobody is told
about is the same "looks handled" failure as an annotation nothing reads.

## Coverage, and what is deliberately exempt

Nine modules were converted. A test **scans** rather than enumerates — a hand-kept list of
protected stores is a list someone has to remember to extend, which is the same failure one level
up — and fails if any module writes JSON outside `store_io`. Four exemptions, each with a stated
reason the test also checks is a real one: `store_io` itself, `draft_history` (already atomic, and
write-if-absent means it never read-modify-writes), `sleeper_client` (a replaceable cache of a
remote API), and `bot_benchmark` (developer-run measurement output).

**One thing is explicitly not fixed, and a lock would not fix it.** `save_chat_history` replaces
the file with the whole history held in `st.session_state`, so its read-modify-write spans the
user's entire session rather than the function. Two tabs will still clobber each other's history.
That is a session-model question, not a file-locking one; the write is now atomic and the rest is
recorded rather than papered over.

---

# #113 — THE INTEGRITY FAMILY: WHAT LANDED, AND WHAT IS A DECISION OR A BLOCKER

§19 named five things under one number. Sorted by what each is actually waiting on:

## Landed

**§19.5 — nothing runs the checks.** Already closed earlier in this pass: `.github/workflows/
tests.yml` runs a fast tier (~1.5s, no data load) on every push and the full suite on every PR,
with tiers detected by `suite_taxonomy` rather than hand-listed. Extended here: both tiers now
check the declared input set *before* running anything, and print `pip freeze`.

**§19.5, the launch path.** `update_and_run.sh` / `.ps1` did `git pull` → `pip install` →
`streamlit run` with nothing checked in between, so a pull that broke the engine reached the
user's live draft board first. Both now run the fast tier and **warn rather than block** — this
is somebody's own copy of their own app, and refusing to start it mid-draft is a worse failure
than starting it with a problem they were told about.

**§19.4 — the input set is a directory listing, not a manifest.** The one that was *demonstrated*,
and re-demonstrated before building:

```
canonical pool rows: before=764  after=765  delta=+1
the planted row is priced: trade_value=100.0, projection=9999.0
git treats the planted file as: .gitignore:10:data/projections/**/*.csv
suite (test_data_merger): OK
```

A fabricated player with a 9999-point projection entered the priced universe from a **gitignored**
directory — the one the app's own uploaders write to — and the suite stayed green. §19.3(a) had
measured 28 of 28 inputs tracked and read that as reproducibility; it was true by nobody having
uploaded, not by construction.

`baseline_manifest.py` declares the set with **sha256 per file**, and three tests fail on the
three distinct disagreements: `missing`, `changed`, `undeclared`.

Three design points worth stating:

* **Hashes, not a file list.** A listing catches the planted file and misses the worse case — an
  *edit* to a tracked baseline file, which moves every price the engine computes while the
  listing stays byte-identical. §19.2 recorded that `hashlib` appeared exactly once in this
  production tree.
* **It is not a lock on the data directories.** Uploading rankings *is* the product. The rule is
  not "no extra files" but "a run is only reproducible if the loaded set equals the declared
  set" — and a run that is not reproducible must say so instead of reporting green. Exactly one
  test fails, it names the files, and it says how to get a clean run.
* **The directory list is a literal, not an import from `data_merger`.** A manifest that followed
  the code it checks would agree with a bug. A test fails if the two ever disagree.

**#102's coverage guard caught this module on its first full-suite run**, which is the guard
working rather than a nuisance: `baseline_manifest` was writing JSON outside `store_io`. It now
writes through it — an interrupted `--write` would otherwise leave a truncated manifest, and
every run afterwards would report every declared file as undeclared, a broken check wearing the
costume of a catastrophic integrity failure. Its `load()` deliberately does **not** read through
`store_io`: that marks an unparseable file and refuses to write over it, which is right for a
data store and exactly wrong here, because `--write` is how a broken manifest gets fixed. A guard
that blocked the recovery command would be a trap.

## Blocked, and inventing a number would be worse than the gap

**Upper bounds in `requirements.txt`.** The audit called this "obviously mechanical". It is not.
Writing `anthropic>=0.40,<1.0` asserts that this app works across a range nothing here has run —
a certainty claim the writing path cannot establish, which is the defect class this whole
programme chases (§13.3, #89). And a lockfile cannot be produced honestly from this environment:
measured, **3 of 10 declared dependencies are not installed here** — `anthropic`, `openai` and
`google-genai`, the three the entire AI layer runs on.

That measurement is itself the sharper finding: **the 1,697-test suite passes without a single
provider SDK present.** The provider layer is exercised only through stand-ins, which
`provider_meter`'s own docstrings already say. `pip freeze` in CI now makes the versions a green
run corresponds to a matter of record rather than assumption — the honest half of what a lockfile
would give, available today. The rest waits on the same prerequisite as **#120**.

## Still open, and each is a decision

| item | the question | recommendation |
|---|---|---|
| §19.8 | Can the suite detect a *loosened guarantee* — a test quietly weakened rather than deleted? | Worth building: a fingerprint over assertion counts per module, so a weakened test shows as a diff. Not built here; it wants its own verification pass. |
| §19.9 | `ENGINEERING_DOCTRINE.md` states a re-audit cadence and nothing enforces it. | A scheduled full-suite + manifest run is cheap now that CI exists. Needs a cadence *you* pick, not one I invent. |
| §19.10 | `.devcontainer/devcontainer.json` launches with `--server.enableCORS false --server.enableXsrfProtection false`. | Scoped to the Codespaces preview only, and a common workaround — but it should be a **deliberate** decision rather than an inherited one. Yours to make. |
| §19.11.2 | The committed baseline is Recent/Fresh today, **Stale at +90d and permanently after**, with no refresh path short of a code change. | A refresh policy for paid vendor data is a product decision, same family as §7.10. |

---

# #126 / #127 — PROVIDER NEUTRALITY: THE ROUTING WAS ALREADY NEUTRAL, THE *SET* WAS NOT

Raised as a question, not a bug: *"Wasn't it discussed that API integration needs be source and
model agnostic? Having specific tags to anthropic, openai, and google-genai feels like a step
backwards."* Measuring it split the concern cleanly in two, and only one half was what the
question was aiming at.

## What the measurement found

**The three SDK imports are not the problem, and removing them would make the app worse.** They
are adapters, one per response shape, and `provider_meter`'s own docstring already argues why a
single "find the tokens" heuristic would be guessing. You cannot read Gemini's
`grounding_metadata` with Anthropic's `web_search_tool_result` shape. A lowest-common-denominator
wrapper would fabricate exactly the class of number this audit spent twenty sections removing.

**Two other things, neither of them the SDK imports, were real:**

| what | measured |
|---|---|
| The shipped per-chair vendor defaults | Exactly a round-robin over the declaration order, justified after the fact. 3 of 4 `why` strings did not support their own recommendation. |
| Single-key coverage | With one key, a user got **2 of 4** chairs (Anthropic), or **1 of 4** with the Moderator dead (Gemini, OpenAI). |
| The Draft Room's override path | **Did not exist.** Neither `debate_pick` call site passed `role_providers`, so the panel's own routing config could not reach it. |

The vendor picks came from an off-the-cuff remark early in the SaaS discussion — *"who it thought
may have been decent in each chair"* — and calcified. They had been called out once already, in an
earlier UI, and survived: traced across `d30f50d` → `a58a295` → `d871078`, where each rewrite
carried the strings forward as content rather than re-deciding them. That produced a doctrine rule:

> **A retracted justification obliges a re-decision, not an annotation.**

## What landed (#126, `5859ea5`)

- Chairs are dealt round-robin across **whichever providers you have a key for**, in declaration
  order — and `bot_config.ASSIGNMENT_RULE` states in the config file that the order is arbitrary
  and nothing has measured it. With one key, all four chairs run on it.
- Both Draft Room `debate_pick` call sites now pass `role_providers`, so the override path exists.
- `ROLE_INFO` no longer carries `recommended` or `why`. The caption shows what the chair **does**.

A *measured* recommendation is a different thing and is welcome later — that is what the benchmark
harness is for. The bar is that it ships with the run behind it.

## What landed (#127, the socket)

Adding a fourth provider meant editing six files, with nothing anywhere declaring that six was the
list. `providers.py` is that declaration: a frozen `Provider` dataclass, a registry, and every
per-provider table in `llm_engine`, `bot_config` and `app` **derived** from it rather than
hand-kept beside it.

The part that is not just plumbing: a `Provider` declares what its responses can actually
**report** — completion state (#99), usage (#100), served model (#109), retrieved sources (#97) —
and `capability_gaps()` turns the absences into a sentence the config screen shows. A generic
adapter that reports none of them still works; the machinery already degrades correctly. What was
missing is that nothing *said so*, so a user plugging in a local model could not tell *"this
provider does not report that"* from *"this provider reported nothing this time"*. That is #112's
never-checked-versus-checked-and-absent distinction, arriving at the provider boundary.

The flags are checkable, not editorial: `test_providers.py` asserts a provider claiming truncation
detection actually has a reader in `provider_meter`. A flag that could disagree with reality would
be a claim the writing path cannot establish — and worse than no flag, because the UI would print
a capability the app does not have.

---

# THE WARPATH — SEVEN RULINGS BUILT, ONE PINNED, ONE UNTOUCHED

Nine decisions were put up as card pickers and ruled in one sitting. This is what each turned
into, and the two places where building them found something the ruling did not anticipate.

## What landed

| # | item | ruling | built |
|---|---|---|---|
| 1 | the socket | *"true neutrality, infrastructure that plays nicely with whatever they shove into it"* | `providers.py` — registry, derived tables, declared capability gaps (`9f9b737`) |
| 2 | §19.10 devcontainer | **PIN** | recorded as a choice with a stated trigger; **no code** (`5154ee9`) |
| 3 | §7.10 provenance | state origins where not pay-locked; vendor unnamed | `baseline_provenance.json`, 20/20 covered (`5154ee9`) |
| 4 | §19.9 cadence | weekly, Wednesdays | `schedule:` cron + doctrine paragraph, held together by a test (`a1409f2`) |
| 5 | #94 contract failure | **flag only** | ruled, and the flag now survives to Apply |
| 6 | §7.4 allowlist | allowlist what feeds the composite; prose stays free | `source_policy.py` |
| 7 | §19.8 fingerprint | build it, failing not warn-only | `assertion_floors.py` — per-name FLOORS (`a1409f2`) |
| 8 | §6.2a re-adjudication | gate behind a second pass, human eye | `adjudication` state + queue + transition |
| 9 | §6.3 crossover | **HOLD** | **untouched** |

## Two things worth flagging back

**Items 6 and 8 are one boundary, and together they are a real behaviour change.** They land on
the same function and the same downstream consumer because they are the same question asked
twice — *which sources may move a number*, and *who has to agree before one does*. The
consequence: **a panel-vetted finding no longer feeds `composite_player_score` on the
Moderator's own say-so.** It needs an allowlisted cited source AND a second adjudication.

Nothing observable changes on this repository — the store has never held a row — but it is the
first time the app declines to use something the panel approved. That is the ruling's own logic
rather than caution added on top: under a shared deployment an accepted finding reaches
everybody. Neither gate assumes that deployment, per the standing rule; both behave identically
local or hosted, and `test_composite_admission_gate` fails if an automatic confirmer appears.

**Building #94 and §19.8 each found a claim that could not be established.** §19.8's module
docstring asserted that strengthening a test passes untouched; its own test proved otherwise, and
the docstring was corrected rather than the test relaxed — per-name counting cannot tell a
strengthening from a weakening without an invented strength ordering, so any *substitution*
surfaces and only pure additions are free. And §7.10's first draft named the paid vendor through
a parser function name in its ingest description; the test written to enforce the ruling caught
it. Both are the same shape as the defect class this audit exists for: a description that was
believed because nothing checked it.

## What each check cannot do, collected

Stated together because a check whose limits are unstated gets trusted past them:

| check | cannot |
|---|---|
| `source_policy` | tell whether a citation is *truthful* — `ESPN (fabricated)` is admitted |
| `assertion_floors` | see a vacuous assertion (`assertEqual(x, x)`), or tell a strengthening from a weakening |
| `confirm_finding` | verify the claim; it records that a second party looked, not that the source says it |
| `baseline_provenance` | verify the numbers in the CSVs — only that the record still matches them |

---

# THE TWO PREREQUISITES FOR TIERED ACCEPTANCE

Built after a design conversation that settled the shape of the shared-substrate question, and
they are the two pieces every version of that shape needs. Neither commits to a deployment.

## The design they serve, in the owner's own framing

> *"They get live data, we get data poisoning control."*

Users can act on an unconfirmed finding **provisionally** — recalculate assuming it is right, for
their next pick — and simultaneously request that it be considered for universal inclusion.
Acceptance for everyone stays behind an admin-gated confirmation pass on the server.

**This dissolves ROADMAP's "single biggest unresolved tension" rather than picking a side.** Local
sovereignty stays the default: nothing leaves the machine. Sharing becomes a **per-item,
user-initiated export of one claim** — a sentence about a player — not a sync of the user's data.
That is a categorically different act from a shared substrate, and it is why the contradiction the
roadmap declared unresolvable stops being one.

**The governing rule that falls out of it, and it is checkable in a way "is this true" never is:**

> **The gate is on blast radius, not on truth.** A provisional acceptance is safe to leave
> ungated not because the claim is good but because it is scoped to one install and one moment —
> poisoning it costs that user their next pick, not the watering hole. Tier 2 is gated because
> its blast radius is N.

## 1. Retraction (§6 lifecycle) — the floor

6.2a's gate is safe because its default is to **withhold**. The provisional path flips that
default to **admit**, and a system that can admit without a person and cannot un-admit has no
floor. So retraction ships first. Detail in `ARCHITECTURE_AUDIT.md` §6.2a; the short version is
that retraction is orthogonal to adjudication (so "confirmed then rejected" stays distinguishable
from "never confirmed"), the claim survives while only the number leaves, restore is not a grant,
and the recompute path is the ordinary one because nothing caches an accepted finding.

## 2. Panel independence (§6.2b) — what makes a second opinion second

Measured, not assumed: **the shipped one-key default is 1 distinct voice across all four chairs.**
"The Contrarian didn't dispute it" can therefore mean one model declined to argue with itself —
and that sentence is the Moderator's own bar for writing a durable finding.

Four states rather than a boolean, because a provider default is a floating alias (#109) and
"not knowably distinct" is not "distinct". The module reports; the caller supplies the bar, with
no default, because the two real bars differ by blast radius rather than by model quality.

## What this makes safe to build next, and in what order

| step | unblocked by |
|---|---|
| provisional "assume accurate for my next pick" | retraction — a provisional acceptance must be revocable when the verdict lands |
| "request universal inclusion" queue | nothing new; it is a per-item export, and the privacy story is already the strongest part of the design |
| server-side confirmation panel | independence — server-side is the only place cross-family composition can be *enforced*, which is the real argument for putting tier 2 there |
| capability-threshold auto-acceptance | **still blocked**, and not by these. The benchmark rubric has no accuracy dimension for the Moderator (§5.7), and its judge is itself an unmeasured model — a threshold on that score would grant fact-acceptance authority on a number that never scored facts |

## The open question these do not answer

Findings do not record **which panel produced them** — `evidence` carries the debate's retrieved
pages, not its `role_providers`/`role_models`. So `panel_independence` can tell a user their
CURRENT panel is one voice, but cannot tell them that a finding *already in the store* was
produced by one. Recorded rather than built: it is a schema addition to a store that is still
empty, and §6.5's own rule was not to invent structure against an empty store.

---

# #123 CLOSED — THE THIRD ANCHOR NOW HAS TESTS, AND ITS CEILING HAS A NAME (#152)

`compute_draft_board` has three anchors. Two were tested directly. The third — the
`trade_value` branch under `if (~has_proj).any()` — was wired identically to the points branch
above it and read by nothing in the suite, because **every synthetic universe in this repo is
built from the projection set**, so no fixture ever entered it on purpose.
`RealBaselineIDPBugRegressionTests` exercised its *consequences* (rank order, differentiation)
without ever naming the branch or checking a single number it produces.

## It was testable on committed data all along

| | |
|---|---|
| baseline rows with a `trade_value` and **no** projection of any kind | **76** (DL 24, LB 29, DB 23) |
| `bpa_source` on those rows | `position_relative_trade_value_vor`, 76/76 |
| `projected_points` on those rows | `None`, 76/76 — never fabricated |
| baseline IDP rows with **neither** number | **339** (DL 147, LB 62, DB 130) |
| of those, rows reaching the board | **0** — `build_available_pool`'s EXCLUDE arm |

`TradeValueAnchorBranchTests`, 8 tests. The one that matters most is the arithmetic, which
nothing in the suite had ever read: `bpa` is unscaled VOR, so `trade_value − bpa` must recover
**one** replacement level per position. Measured on the light-IDP board: DB 11.0, DL 22.0,
LB 27.0 — a single value each, 76/76 rows.

## Mutation-checked rather than assumed

| mutation | tests that fired |
|---|---|
| drop the replacement subtraction (`trade_value` raw) | 3 |
| clip the branch at zero (the pre-#74 defect) | 2 |
| remove `_fill_omitted_from_anchor` from this path | 2 |

## What is deliberately NOT tested, and why that is not a gap

The branch's own NaN arm — `if r["position"] in tv_replacement else float("nan")` — **is
unreachable.** `_fill_omitted_from_anchor` fills every position `replacement_levels` omits from
the PRE-DRAFT pool, and the pre-draft pool is a superset of the live one, so any position that
reaches this branch has a level by the time the lambda runs. Measured across four demand
states (0 / 4 / 10 / 20 IDP taken per position): **0 unpriced rows in every one**, with
`replacement_basis` moving `live_starter_demand` → `predraft_anchor` at 10. Asserted as a
negative rather than assumed, so a future repair that makes it reachable fails loudly here
instead of quietly widening the branch's domain.

The absence contract is exercised on this path at `build_available_pool` instead — the EXCLUDE
arm, 339 rows, measured above.

**One measurement artifact worth recording**, because it nearly became a finding: matching
those excluded rows against the board **by name alone** reports 13 false hits. The baseline
abbreviates to a first initial, so `j smith` (DB) matches `j smith` (LB). Matching on
`(name, position)` gives 0. The 13 were an artifact of my join, not of the pool.

---

# #152 — THE FALLBACK'S CEILING IS PARTLY A UNIT ARTIFACT, AND THE PROSE CLAIMED OTHERWISE

Writing the shared-scale test forced the question the old prose answered too confidently.

`draft_room`'s docstring said the fallback *"correctly can't compete"* with a well-projected
player because the two anchors share one scale. **They share a number line, not a unit.**

| | points anchor | trade_value fallback |
|---|---|---|
| unit | projected season points | Draft Sharks' 0-100 trade scale |
| real max in the baseline | 379 (QB) | 100 (WR) |
| real max at the positions that actually use it | — | **DL 30, LB 35, DB 15** |

So the fallback is compressed twice over: once by the scale, once again by where IDP sits
within it. Measured on the same pool under two leagues:

| league | IDP starters/team | best fallback `bpa` | best points `bpa` | fallback rows in top 25 |
|---|---|---|---|---|
| LIGHT (one shared `IDP_FLEX`) | 0.33 | 8.0 | 194.0 | 0 |
| HEAVY (`DL DL LB LB DB DB`) | 6 | 34.0 | 160.0 | **0** |

**In the light league the ceiling is a demand judgment and the right one.** In the heavy league
— 72 IDP starters wanted against 76 priceable IDP players, so essentially the whole position
goes — zero IDP inside the top 25 is not a demand judgment at all. It is the unit.

**This is #51's supply defect seen from the arithmetic side, not a new one.** #51 ruled the IDP
remedy is an input (#49), not code, and that ruling stands: with no IDP points source, there is
no honest way to price IDP in points, and substituting a compressed proxy is better than
fabricating one. What was wrong was the *prose* — "correctly" asserted a judgment the mechanism
does not make.

Three changes, no arithmetic touched:
1. `draft_room`'s docstring now states the unit split explicitly and withdraws "correctly".
2. The inline comment at the scale site points at it rather than repeating the old claim.
3. `CDME_CONTRACTS.md`'s appendix quote of that docstring is dated, since it quotes prose that
   no longer exists in the code and reasons about a 0-100 scale #74/#75 removed.

**#150 inherits this as a known-expected behaviour.** A mass draft battery run over heavy-IDP
formats will produce boards where IDP is taken late relative to its real roster demand. That is
this, it is expected, and it must not be re-reported as a fresh anomaly.

---

# #144 CLOSED — AND THE ITEM'S OWN PROPOSED REPAIR WAS THE WRONG ONE

`pick_necessity`'s denial term normalised `rival_premium` — `(rival TAV − rival UV)`, the SUM of
`draft_room`'s team-specific terms — by `NEED_BONUS_MAX`, the cap on **one** of them. That was an
upper bound on the quantity until `#139` added a third term, after which it clipped, and a
clipped normaliser is the same number for every candidate above the bar.

The item proposed divisor → the sum of all three caps, and held it back because it *"changes
every round's denial contribution by 3x to fix a tail"*. **Right instinct, wrong diagnosis.**
The code's own comment named the missing evidence: *"Choosing between them needs a measurement
of necessity ordering that nothing in this repository has yet made."*

## The measurement, six real turns, 272 candidates

| form | inversions | label flips | mean necessity | rows changed |
|---|---|---|---|---|
| divisor 36, weight held (**the proposal**) | 478/7046 | 54/272 | −3 to −4.5 | — |
| **both scaled (shipped)** | **7**/7046 | **1**/272 | unchanged | **== rows clipped, every turn** |

**The decisive row is round 4: 259 of those 2080 inversions occur where NOTHING CLIPS.** If the
divisor governed only saturation, changing it could move only the clipped tail. It moves the
whole field, because below saturation the term is `premium × (WEIGHT / DIVISOR)` — **the divisor
and the weight are one slope, not two knobs.** Moving the divisor alone is not a saturation
repair; it is a 3× de-weighting of denial wearing one's clothes.

There is no third option: hold the slope and the ceiling must rise 10 → 30; hold the ceiling and
the slope must fall 0.833 → 0.278. So the choice is explicit, and holding the calibrated rate is
the one that changes only what the defect broke.

## What shipped

```
NECESSITY_DENIAL_SATURATION = NEED_BONUS_MAX + ELIGIBILITY_BONUS_MAX + DEPTH_EXPOSURE_MAX  # 36.0
NECESSITY_DENIAL_CEILING    = SATURATION × (NECESSITY_DENIAL_WEIGHT / NEED_BONUS_MAX)      # 30.0
```

Both **derived**, neither written as a literal (#56). Deriving the saturation point from the sum
rather than hardcoding `3 ×` is the part that matters: **a fourth team-specific term now moves it
automatically**, which is exactly what failed to happen when `#139` added the third and is the
entire mechanism of the original defect. Slope before `0.8333333333333334`, after
`0.8333333333333334`.

`cdme_force_ablation.py` reproduces this formula independently and moved in lockstep — left
alone it would have silently measured an engine version that no longer exists.

## Two tests rewritten, not left to pass

`TheDenialNormalizerNowSaturatesTests` asserted **that it clips**, which is what the repair
removes; it would have gone vacuous rather than red. Replaced by
`TheDenialNormalizerSaturatesAtItsOwnBoundTests`, pinning **both** halves — the flat spot is gone
**and** the rate did not move — because either alone is a way to get this wrong.

## The half the item never named, found by the same probe

`need_bonus`'s own cap. Raising `NEED_BONUS_MAX` out of reach so the real code path emits the raw
value, across 30,324 candidate rows per league:

| league | raw > 12.0 | distinct raw states collapsed onto 12.0 | discarded |
|---|---|---|---|
| 1QB 3WR | 6.6% | **1** (12.33) | 0.33 |
| SUPERFLEX | 11.2% | **1** (12.38) | 0.38 |
| 3RB 3WR | 12.6% | **1** (12.33) | 0.33 |
| **4WR TE-premium** | 18.2% | **2** (12.33, 16.33) | **4.33 (36% of the cap)** |

In three shapes the clip is order-preserving — one state maps onto the cap, nothing is destroyed,
the bound is genuinely defensive. In a 4WR format it collapses **"zero of my four WRs" and "one
of my four WRs"** onto the same 12.0. That is a flattened form of the exact defect the
`need_bonus` docstring says it fixed. **NOT repaired here** — it is a second, independent
decision about `need_bonus`'s own magnitude, and bundling it into a denial-normaliser fix is how
#139's third term got missed in the first place. Registered as **#153**.

Also cleared by measurement rather than assertion, and worth recording because both docstrings
*asserted* it: `eligibility_bonus`'s `min()` fires **0.0%** and `depth_exposure`'s **0.0–0.4%**.
Their "a defensive guard for out-of-scale source data, not the bounding mechanism" is now true by
measurement.

## One consequence flagged rather than buried

The ceiling rising 10 → 30 is exercised only in an unobserved regime — real premiums max at
13.09, so denial contributes ≤10.9 in practice. If premiums ever reach ~24+, denial could push
`raw_score` into the existing `[0,100]` clamp more often, trading this flat spot for that one.
`test_the_flat_spot_is_gone` fires if premiums approach the new saturation point, so that regime
cannot arrive unnoticed.

**Population note:** this run measures 8.5% clipping where `test_threshold_reachability` recorded
21.9%. Different populations, both real — that test samples the top 12 priced rows via
`pick_analysis` over eight board states; this samples `DEFAULT_NARROW_COUNT` via `build_snapshot`
over six turns with genuine forward gaps. Neither number is a correction of the other.

**Two harness errors made reaching this, recorded because both produced confident wrong output.**
First run: `rival_premium` was 0.00 for 269 of 269 candidates. `rival_premium` is computed over
the picks **ahead** of a turn, and I filtered on the gap **behind** it — rejecting exactly the
round-opening turns carrying ~22 intervening picks and keeping the round-closing ones carrying
none. Second run: backgrounded with a `cd` into a scratch directory, so `DataMerger` loaded from
the wrong working directory and returned a frame with no `position` column. A vacuous measurement
that *looks* like a clean null result is the more dangerous of the two.

---

# #144 CLOSED — AND THE ITEM'S OWN PROPOSED FIX WAS THE WRONG ONE

`pick_necessity`'s denial ramp divided `rival_premium` by `NEED_BONUS_MAX`. That was an upper
bound on the quantity until #139 added a third team-specific term, after which the ramp clipped
and every candidate above the bar received an identical denial contribution.

The register's proposed repair — *"the structurally matching divisor is the sum of all three
caps"* — was held back because it *"changes every round's denial contribution by 3x to fix a
tail"*. **Right instinct, wrong diagnosis.** The code's own comment named the missing evidence:
*"Choosing between them needs a measurement of necessity ordering that nothing in this
repository has yet made."* It has now been made.

## The measurement, six real turns, 272 candidates

Below saturation the term is `premium × (WEIGHT / DIVISOR)` — so **the divisor and the weight
are one slope, not two knobs.**

| form | inversions | label flips | mean necessity |
|---|---|---|---|
| divisor 36, weight held at 10 | **478**/7046 | **54**/272 | −3 to −4.5 |
| both scaled (shipped) | **7**/7046 | **1**/272 | unchanged |

**The decisive row is round 4: 259 of those 478 inversions occur where NOTHING CLIPS.** A
saturation repair cannot reorder a population that never reached saturation. Moving the divisor
alone is a 3× de-weighting of denial wearing a saturation repair's clothes.

The shipped form holds the calibrated rate (`10/12 = 0.8333` necessity points per premium
point, bit-identical before and after) and moves only the flat spot. `rows changed` equals
`rows clipped` on every single turn — the signature of a change that touched only what it
claimed to.

Both constants are **derived, never written as literals**, so a fourth team-specific term moves
them automatically instead of silently re-flattening the ramp the way the third did:

```
NECESSITY_DENIAL_SATURATION = NEED_BONUS_MAX + ELIGIBILITY_BONUS_MAX + DEPTH_EXPOSURE_MAX
NECESSITY_DENIAL_CEILING    = SATURATION × (NECESSITY_DENIAL_WEIGHT / NEED_BONUS_MAX)
```

`cdme_force_ablation.py` reproduces this formula independently and moved in lockstep; left
alone it would have silently measured an engine version that no longer exists.

## What the floors ratchet caught, and why it was right to

The full suite failed on `assertion_floors`: `test_threshold_reachability.py: self.assertLess
2 -> 1`. Not a regression — the rewrite replaced a two-sided band (`0 < share < 0.5`, "it clips
but not for most") with an exact `assertEqual([], clipped)` ("it must not clip at all"), and
test methods went 12 → 14. A **strengthening**, which the counter cannot distinguish from a
weakening by design (§19.8: it "cannot see a vacuous assertion, or tell a strengthening from a
weakening"). Floors regenerated deliberately, which is the workflow the instrument exists to
force.

**Process note, recorded because it cost a cycle:** #144 was pushed after six targeted modules
passed but before the full suite finished. The targeted set was 530 tests across every
denial-touching module and all of them passed — the failure was in an instrument none of them
exercised. A behaviour change to the equation earns the whole suite, not a subset chosen by the
person who wrote the change.

## Two things measured here that were NOT the item

- `eligibility_bonus`'s `min()` fires **0.0%** and `depth_exposure`'s **0.0–0.4%** across
  30,324 candidate rows per league. Their docstrings' claim to be "a defensive guard for
  out-of-scale source data, not the bounding mechanism" is now measured rather than asserted.
- `need_bonus`'s own cap is a separate defect — **#153**.

---

# #138 SECOND HALF — THE TWO REAL GAPS NOW HAVE READERS

`replacement_basis` and `growth_signal` were produced by `compute_draft_board`, placed on every
board row, and **dropped at `pick_synthesis`'s `raw_candidates` boundary**. Nothing downstream
could read them however much it wanted to — including the retained decision record that exists
to answer "why this player".

Both now reach `CandidateSnapshot` → `draft_board_ui.serialize_candidate` →
`draft_simulation.PickRecord`. The scanner moves both `write_only` → `observable`, with
`pick_synthesis` correctly classified a **carrier** rather than a consumer (the same relay trap
`test_a_relay_is_not_counted_as_a_consumer` already pins for `waiting_cost`).

They are not the same kind of quantity:

| | why it matters | measured |
|---|---|---|
| `replacement_basis` | `live_starter_demand` and `predraft_anchor` are two different **strengths of claim** about one number; a consumer rendering both identically states a live measurement it does not have | both states reachable through the snapshot layer — the anchor appears by round 15, once a position's live demand drains |
| `growth_signal` | upside mode's whole distinguishing output: `final_score = bpa + UPSIDE_GROWTH_WEIGHT × growth` | 43–52% of upside rows carry growth > 0 (mean 11.1 early, 25.5 as the pool drains), and **by round 15 it changes which player is taken** |

`growth_signal` is `None` in balanced mode, never `0.0` — the absence contract at the one
boundary where it is easy to get wrong, since a zero would read as "measured, and this player
has no trajectory".

**The reconstruction test is the one that matters.** The scanner proves a reader exists; it
cannot prove the value arriving is the right one, and a carry that always delivered `None`
would satisfy it while telling a reader nothing. So `growth_signal` is checked against the
identity it decomposes — `final_score = bpa + UPSIDE_GROWTH_WEIGHT × growth_signal` closes to
one decimal on every candidate.

Ten tests in `test_decision_qualifiers.py`, mutation-checked **4 / 2 / 37** against dropping
the carry, faking absence as zero, and severing the record's read.

`test_the_two_real_gaps_are_still_recorded_as_gaps` was **inverted rather than deleted** — it
now asserts they are *not* write-only, so a refactor that drops the carry fails loudly instead
of vanishing quietly.

---

# #151 CLOSED — AND THE OPTION EVERYONE REACHES FOR FIRST IS IMPOSSIBLE HERE

`render_trace` recorded long strings as `str[97]` -- a length. A length is a VALUE, which
contradicts the module's own rule that argument values are blurred so the trace records
STRUCTURE. The committed reference went stale overnight on a single diff, `str[97]` ->
`str[98]`, because the Data Sources caption ticks from "(9d ago)" to "(10d ago)". No UI changed.

The register named two options. One of them is not available, and that is now measured rather
than suspected.

## Freezing the clock cannot work in this process

Both seams fail identically:

```
RuntimeWarning: datetime.datetime size changed, may indicate binary incompatibility.
                Expected 48 from C header, got 56 from PyObject
```

Any C extension imported during a capture runs `PyDateTime_IMPORT`, which validates
`datetime`'s binary layout. A `datetime` subclass is a different size, so it trips whether the
class is installed at the source (`datetime.datetime = Frozen`) or hidden behind a
`sys.modules` shim -- and `app.py`'s import graph pulls C extensions in on every capture, since
`capture()` pops and re-imports `app` each time.

**This is a better explanation than the original note's.** "Patching datetime across
already-imported modules did swap the class but `now()` still returned real time" described a
symptom; the type-layout check is the cause, and it rules out the whole approach rather than
one implementation of it. Freezing the clock here needs a third-party dependency (blocked
behind #120's pinning) or an injectable clock seam through `app.py` and `data_merger`'s six
`datetime.now()` call sites -- the hull pass's territory (#137), not a patch.

## So: stop recording the length

`str[long]`, which is what the module's own contract already promised.

**The cost, stated rather than buried:** 147 of 491 calls (30%) carried a length. Dropping it
loses the ability to notice a refactor that swaps two same-shaped adjacent calls without
changing path or order. Position in the sequence still separates everything else, and "is the
copy identical" was never a question this trace answered -- its docstring disclaims it.

An instrument that emits a false diff every time a day counter ticks is worth less than one
that is slightly less sensitive and never lies, because the first teaches its reader to
regenerate without looking, and a trace regenerated without looking is evidence of nothing.

## The guard is the flaw's own signature

`_shape("x" * 97) == _shape("x" * 98)`, asserted directly on `_shape` rather than by faking a
clock -- because a clock cannot be faked here, per above. Two companions keep it honest: a
non-vacuity test (blurring EVERYTHING would pass while destroying the labels and keys that are
the trace's actual structure -- the 60-character boundary is still a boundary), and a test that
the rejected option's REASON stays in the source, since the next person will reach for a clock
freeze first and the failure is not guessable from the code.

## The display-contract ratchet fired too, and it asks a question rather than for a bump

`CandidateSnapshot` 39 -> 41. Its own message: *"confirm the new field does not imply a scale
the card cannot support, decide whether the card should render it, then update this number."*
Both answered in place:

| field | scale | render on the card? |
|---|---|---|
| `replacement_basis` | string enum -- implies no unit at all | no; it is a qualifier on a price, belongs with `horizon_basis` in the explanation drawer (#36/#137) |
| `growth_signal` | **the wrong one.** A percentile difference (0-87.5 measured), living on exactly the 0-100 band this file exists to say the engine's values do NOT live on | no -- and currently MOOT: all three `build_snapshot` call sites omit `mode`, `build_snapshot` forces `"balanced"`, and growth_signal is always `None` there |

Recorded as a precondition rather than a preference: if #115 ever routes upside mode to a human
board, `growth_signal`'s scale hazard must be settled BEFORE it reaches a metric row. Rendering
a 0-100 percentile difference beside raw-points `universal_value` in matching formatting is the
unit-borrowing this module documents, made worse by the fact that the borrowed unit really is
0-100 and would look authoritative.

---

# #154 / #55 — THE OPPORTUNITY-COST FRAME, AND TWO CORRECTIONS THE MEASUREMENT FORCED

The owner's framing, which is the right one and reframes the repair away from where #154 first
pointed:

> *"don't draft a TE because you're missing a TE; draft the TE when the cost of not drafting
> him exceeds the value of taking the stud."*

Not a bigger positional bonus. The **marginal cost of leaving a need unresolved**, integrating
temporal urgency, positional forfeit, remaining alternatives, and the waiver/replacement level.
Three tiers: BPA by default, opportunity-cost necessity as the draft closes, hard feasibility
when the alternative is a roster that cannot be fielded.

## Most of it already exists, measured and unplugged

| input | quantity | state |
|---|---|---|
| waiver / replacement level | `horizon_replacement` — best at this position expected STILL UNDRAFTED when the draft ends | built; this IS the waiver replacement |
| cost of not solving it | `waiting_cost` = this player's points − that floor | computed per player per board, **scored by nothing** |
| cost to the next turn | `positional_forfeit` | wired to `pick_necessity`, not to selection |
| temporal urgency | `intervening_picks`, `survival_probability` | present |

The correlation trap is real -- `r(waiting_cost, bpa) = +0.847`, which is why #48 refused it as
an additive necessity term. The owner's form avoids it by **comparing** rather than summing:
cost-of-not-solving against the uv GAP surrendered. Both sides are raw season points, so no
constant is required, which matters because every failed repair in this codebase has been a
magnitude somebody picked.

## CORRECTION 1: `waiting_cost` is the wrong quantity for most of the draft

Measured on the real 10T_standard_SF board, roster 1, every turn:

```
 2.10  chosen_uv  99.51 | best TE uv 67.14  wait 88.00  measured | GAP 32.37  FIRES
 7.01  chosen_uv  29.43 | best TE uv 29.43  wait 53.00  measured | GAP  0.00  FIRES
11.01  chosen_uv  -0.98 | best TE uv -0.79  wait 22.00  measured | GAP -0.19  FIRES
```

**The rule fires in ROUND 2** and stays on for ten rounds. It would take a TE over a player
worth 32 more universal_value.

The counterfactual is wrong. `waiting_cost` prices deferral to the END OF THE DRAFT -- "this TE
is 88 points better than the one I get if I never take a TE." But declining now does not mean
never; it means taking one at the NEXT turn. That is exactly the distinction #48/#71 established
and then only half-wired: `positional_forfeit` is the next-turn cost, `waiting_cost` the
draft-end cost, and they correlate at only r=+0.569, so they are genuinely different questions.

**So the rule needs `positional_forfeit` for most of the draft, and `waiting_cost` only as the
remaining opportunities at that position collapse toward one.** The two are not
interchangeable, and the draft-end cost is what makes the rule fire absurdly early.

## CORRECTION 2: the `horizon_basis` guard has the wrong sign

My proposed guard was "fire only on a `measured` floor", since an imputed floor driving a
positional override is fabricated urgency (#62/#122's defect class). The measurement inverts it:

```
11.01  measured   fires
12.10  imputed    silent
15.01  imputed    silent
```

The floor goes `imputed` from round 12 -- so that guard switches the rule OFF exactly in the
endgame where the need is real and the pool is thinnest. The guard is still correct in what it
refuses to claim; what is wrong is expecting tier 2 to cover the endgame at all. **Tier 3's
pure arithmetic (`picks_remaining == unfilled_dedicated_slots`) has to carry it**, and it needs
no evidence about the pool, which is why it still holds when the evidence runs out.

## CORRECTION 3: the case I was designing against no longer exists

That trace ran with `set_league_format` wired (the harness repair). Roster 1 **took a TE at
7.01** and the 9-RB/0-TE roster did not reproduce. The first battery's incidence table is void:
on the corrected run, 10T_standard_SF went 2 findings -> 0, while 10T_half_ppr and 10T_ppr went
0 -> 1. Starter values now separate by scoring (10T standard 221-293 vs half_ppr 332-402) where
before all three were byte-identical.

**Nothing about #154's mechanism changes** -- need_bonus is still flat across the draft, upside
mode still zeroes every team-specific term, and rosters still finish unfillable. What changes is
WHICH formats and chairs, so sizing the repair against the old trace would have fitted it to a
draft the fixed harness no longer produces.

Sequence, therefore: corrected battery completes -> real incidence -> then build, with
`positional_forfeit` as tier 2's cost and tier 3 carrying the endgame.

---

# #154 TIER 3 IS NECESSARY AND NOT SUFFICIENT, AND #155 IS WHY IT LOOKED LIKE IT WORKED

## The claim I made and then disproved

I reported "tier 3 fixed 12T_ppr_mode_upside: 2 findings -> 0". **That was wrong.** The
2-findings figure came from the FIRST battery, before `set_league_format` was wired; the
corrected battery had not reached that format. The improvement was the scoring repair, not the
backstop. I verified against a stale baseline -- the exact error I had flagged one message
earlier and then committed anyway.

The honest A/B, same code both arms, feasibility ON vs OFF:

```
12T_ppr_mode_upside   OFF findings=0  starters 194.24 / 353.16 / 430.97   league_total 4065.26
                      ON  findings=0  starters 194.24 / 353.16 / 430.97   league_total 4065.26
10T_ppr               OFF findings=1  starters 331.89 / 365.01 / 402.30   league_total 3669.16
                      ON  findings=1  starters 331.89 / 365.01 / 402.30   league_total 3669.16
```

Byte-identical. Tier 3 changed nothing at all.

## #155: compute_draft_board's ordering is NOT authoritative

`pick_synthesis.narrow_candidates` re-sorts every board it receives through its own
`_board_order` key. **Any decision expressed only as row order is silently discarded before it
reaches a pick.** Tier 3 was measured promoting a QB correctly on the board while the chair
took its seventh RB.

Repaired by making the backstop travel as DATA rather than as order: `compute_draft_board`
emits `fills_required_slot`, and `_board_order` leads with it. The one authority that decides
it stays the one authority wherever the rows are re-sorted. This is a general hazard, not a
tier-3 one -- a second ordering authority will discard the next such decision too.

## Tier 3 still does not fix 10T_ppr, and the reason matters

With the flag honoured end to end, chair 2 still finishes with no QB. Instrumented at its last
pick:

```
chair2 picks before last: 13    rounds: 14
board rows: 126    flagged: 0    QBs on board: 0
```

**The backstop bound correctly and had nothing to promote.** Every QB was gone:

| | |
|---|---|
| QBs in the universe (with a number) | 39 |
| QBs drafted, 1QB 10-team league | **39** |
| per chair | 1, 0, 3, 4, 5, 5, 5, 6, 4, 6 |
| QB picks by round 12/13/14 | 7 / 8 / 6 -- 21 of 39 |

A ten-team league needing ten quarterbacks consumed forty.

**So tier 3 is necessary and not sufficient, by construction.** A feasibility backstop can only
promote a position that still has supply. Preventing the state where supply is gone is tier 2's
job -- which is exactly the owner's framing: the cost of leaving a need unresolved rises as the
alternatives disappear, and that has to bite BEFORE the last pick.

## A hypothesis I checked and disproved, recorded so nobody re-runs it

I expected the pile-in to be the pre-draft anchor: demand exhausts, `_fill_omitted_from_anchor`
prices the rest against a much lower pre-draft bar, and the position looks artificially good.
**Measured: every late QB pick carries `replacement_basis == "live_starter_demand"`.** Not one
`predraft_anchor`. The anchor is not the mechanism.

The root cause of the QB consumption is therefore OPEN. It resembles #114's late-draft pricing
collapse (value-flat boards where near-arbitrary tiebreaks decide, 21 of 30 picks in rounds
12-14 going to one position), but that is a resemblance, not a finding, and this file has
already carried one wrong explanation today.

---

# #156 — ROOT CAUSE OF THE MONOCULTURES: AN EXHAUSTED POSITION PRICES AT ZERO AND WINS

## The corrected baseline first

With `set_league_format` wired, the battery's real incidence is **4 findings across 32 formats
and 5,244 picks** -- not 13. Nine of the thirteen were artifacts of every format drafting from
one ranking export.

| format | chair | shape | unfillable |
|---|---|---|---|
| 10T_half_ppr / 10T_ppr | 2 | RB 7, WR 6, TE 1 | **QB** |
| 12T_ppr_redraft | 7 | RB 8, WR 3, TE 3 | **QB** |
| HEAVY_IDP | 5 | one DB | DB |

`12T_ppr_mode_upside` is now CLEAN (0 findings), so "upside mode has no positional gate" does
not by itself break rosters once scoring is correct. `4WR_TE_PREMIUM` is clean too -- #153's
cap collapse does not produce an unfillable roster.

**Three of the four are QB, all one mechanism.**

## The mechanism, measured

10T_ppr, board entering round 12:

```
QB  uv=  0.00  bpa=  0.00  need=0.00  basis=live_starter_demand   <- top of board
TE  uv= -6.01  bpa=  1.00  need=0.67  basis=live_starter_demand
RB  uv= -9.48  bpa=  0.00  need=0.00  basis=live_starter_demand
WR  uv=-15.79  bpa=-13.00  need=0.00  basis=predraft_anchor
```

Once a position's league-wide starter demand is met, `replacement_levels` collapses its target
rank to 1 -- replacement becomes THE BEST PLAYER STILL ON THE BOARD -- so that player's VOR is
his own points minus his own points, **exactly 0.00**. A position with live demand still
measures against a real demand rank, so its remaining players price NEGATIVE.

**Zero beats negative.** The engine takes the exhausted position's best player on every
subsequent pick until that position is empty, then moves to the next-exhausted position and
drains that one. Hence 39 of 39 priceable QBs consumed by a ten-team 1QB league, 21 of them in
rounds 12-14, and a chair left with none.

## Why the docstring is right and the behaviour is still wrong

`replacement_levels` calls the collapse correct, and **in isolation it is** -- nobody left at
that position is above replacement, so ~0 is the honest within-position answer. The defect is
cross-positional:

> **VOR is comparable across positions only while every position's replacement level is the
> same KIND of claim.** Once one bar is a self-reference ("the best still here") and another is
> a demand rank ("the 10th best"), a 0.00 from the first is not the same quantity as a 0.00
> from the second -- and it outranks every honest negative on the board.

This is the same category error #56 keeps catching, one level up: not a bound reused as a
threshold, but two different MEASUREMENTS reported in one column as though interchangeable.

## What this reframes

#59, #60, #114, #147 and #50 all named this pricing. **None of them measured that it makes the
engine systematically drain exhausted positions**, because none of them ran a full draft and
looked at the resulting rosters. That is what the battery was for.

## What it means for the repair

**Tier 3 cannot fix this and never could.** By the time a feasibility backstop binds, the
position it needs to promote has been drained to zero -- measured directly: at chair 2's last
pick the backstop bound correctly and found **zero QBs on the board**.

**Tier 2 is now the load-bearing half**, and #156 may make even that insufficient: an
opportunity-cost rule reads `positional_forfeit`, which is computed from the same replacement
model. A rule fed by a broken comparison inherits the break.

So the order is: **#156 first, then tier 2.** Two candidate repairs, neither chosen:
  1. Price an exhausted position against its PRE-DRAFT anchor. Already partly present via
     `_fill_omitted_from_anchor` -- but measured NOT to be the current mechanism (every late QB
     pick carries `live_starter_demand`, not one `predraft_anchor`), so this would be a change
     in when the anchor applies, not a new idea.
  2. Make "no remaining demand" produce an ABSENT price rather than a zero. This is the absence
     contract's own answer -- an unpriced row is ordered last (#61), which takes drained
     positions OUT of contention instead of putting them on top. It also makes the claim
     honest: with demand met, this engine has no basis for saying what another one is worth.

Both are #50/Phase 3 redefinitions, not patches, and the owner owns the equation.

---

# #156 CORRECTED — IT IS A SIGNAL-PRECEDENCE PROBLEM, NOT A REPLACEMENT-LEVEL ONE

The mechanism I published one commit ago was **partly wrong**, and the correction is sharper
than the original. Decomposing the same round-12 board instead of reading only `uv`:

```
QB  uv=  0.00 = bpa  0.00 + horizon  0.00 + risk 0.00   <- top of board
TE  uv= -6.49 = bpa  0.00 + horizon -6.49 + risk 0.00
RB  uv= -9.48 = bpa  0.00 + horizon -9.48 + risk 0.00
```

**THREE positions collapse to bpa == 0.00, not one.** So "an exhausted position outranks a live
one" is wrong: the collapsed positions all TIE at zero, and what separates them is
`time_horizon_adj` -- QB 0.00, TE -6.49, RB -9.48.

Two statements, both true, replacing the one that was not:

1. `bpa` collapses to exactly 0.00 for the best remaining player at EVERY position whose
   demand rank has reached 1. That is #73's `demand in [1,2)` degeneracy, observed live.
2. Once several positions sit at 0.00, the pick is decided ENTIRELY by the dynasty aging
   adjustment -- which answers a different question ("who ages best") and systematically
   favours QBs, who have the longest careers and flattest decline.

**When the primary signal goes flat, a secondary signal silently becomes the primary one, and
nothing declares that it happened.** That is the defect. It is worse than a mispriced anchor
because the engine is not wrong about anything locally -- `bpa` is right, `time_horizon_adj` is
right, and the composition is nonsense.

## What this rules OUT

The demand model is **sound**, and I nearly blamed it twice. `remaining_starter_demand` is
summed per team, never league-wide, and its docstring records the measurement that forced that:
the league-wide form *"declared a position exhausted 2.0 rounds early on average, ran as far as
-71, and one team taking twelve quarterbacks reads as 12 - 12 = 0, 'QB satisfied', while eleven
teams still have none."* That defect was already found and fixed. This is not it.

The pre-draft anchor is also ruled out by measurement -- every late QB pick carries
`replacement_basis == "live_starter_demand"`, not one `predraft_anchor`.

## What it means for the repair, and the coupling nobody should miss

The ABSENCE option is stronger than I first credited: if `bpa` cannot distinguish, "no claim" is
the honest answer, and an unpriced row drops out of contention instead of being ranked by a
question it was not asked.

**But absence and the feasibility backstop become COUPLED, not independent.** Unpriced rows sort
LAST (#61). If every QB goes unpriced while a roster still needs one, that roster never takes a
QB -- catastrophic in the other direction, and worse than the defect being repaired. Tier 3
would have to rescue it, which means the two mechanisms can no longer be reasoned about
separately. That is a real architectural cost and it belongs in the decision, not in a
footnote.

Still #50/Phase 3, still the owner's call.

---

# #150 — THE GATE'S OWN RESULT: 4 -> 3, AND ZERO COLLATERAL

Full matrix before and after tier 3 + #155, identical configs:

| | before | after |
|---|---|---|
| structural findings | 4 | **3** |
| `12T_ppr_redraft` chair 7 (RB 8, WR 3, TE 3, no QB) | illegal | **legal** |
| 10T_half_ppr / 10T_ppr / HEAVY_IDP | 1 each | 1 each |
| **formats whose `starter_value_max` changed** | -- | **0 of 32** |

32 formats, 5,244 picks, ~2.9 hours per run.

**The backstop fixed the one roster that ran out of PICKS and left the three that ran out of
PLAYERS**, which is exactly what its own docstring says it can do. And it did so without moving
the top-end starter value of a single format -- a true no-op wherever it does not bind, which is
the property that separates a backstop from a positional preference.

The three survivors are #156's supply exhaustion. No feasibility rule can reach them: at chair
2's last pick the backstop binds correctly and finds zero QBs on the board.


## #157 — the Gold Wyrm repaint, and what measuring a palette found

DONE at 26b8db8. The brand asset the old palette derived from is a cold blue football macro;
the identity that replaces it is warm near-black under metallic gold. The accents deliberately
did NOT follow the brand: they encode meaning (chair identity, necessity tier, the four
decision-path forces), so unifying them toward gold would destroy information. Emerald / ruby /
amethyst / sapphire / topaz already are a hoard, which is how both were served at once.

Measured on the two properties that can regress:
  - CONTRAST. Every foreground token improved or held; all clear WCAG AA on `surface`. `dim`
    stays deliberately below AA (3.22 -> 3.39) as the one recede role, bounded at AA-large.
  - SEPARATION. Worst pair between the meaning-bearing accents, CIE Lab dE 16.4 -> 35.2.

INSTRUMENT REJECTED, and recording this matters more than the result: raw hue-degree
separation was tried first and called gold-vs-tie a collision at 2.9 degrees apart. `tie` is a
near-neutral at saturation 0.28; nobody could mistake it for the brand gold. Hue degrees
over-penalise low-chroma colors. dE accounts for lightness and chroma together and judged the
OLD palette by the same rule -- which is the only reason the swap is not self-serving.

THREE DRIFTS THE MEASUREMENT FOUND, none of which was the repaint:

  1. design_system.py had drifted internally -- the module whose whole purpose is preventing
     that. Two badges tinted with #38bdf8 while bordering with the sky token (dE 10.6, two
     skies in one badge); "notice" used an amber in no token at all, landing dE 9.6 from
     gold-b. Both badge blocks are now DERIVED from TOKENS under one rule.
  2. app.py carried 82 hex literals across 31 distinct values, 66 of them exact OLD token
     values, while draft_board_ui.py was clean. Repainting TOKENS alone would have shipped
     warm gold inside the embedded board and cold blue in every surface around it. Now 0.
     Four rgba() tints still carried the old sky, invisible to a search for the token's name;
     __RGBA_<token>_<pct>__ markers close that.
  3. The position pills claimed to "stay clear of hues this app already uses to MEAN
     something" while RB was cliff-b verbatim and TE was block-b verbatim. The claim was never
     tested, so it was free to be false. Narrowed to the real co-occurrence (a pill shares a
     table row with an injury pill) and tested.

## #158 — an unpriced leader crashes the Draft Room, and the annotation is why

DONE. `metric_row1` formatted `universal_value` and `team_acquisition_value` with `:.0f` and
no guard. Both are None when a position has no replacement level, so the render raises
TypeError and takes the whole panel with it. Six sites: two metric cards x two panels, plus
the "Best alternative" line in each -- the last two found by the ratchet, not by reading.

THE PATTERN IS THE FINDING. In the SAME six-card row, `projected_points` and
`survival_probability` WERE guarded. The guard was applied to the fields that rarely need it
and skipped on the two the absence contract explicitly names. Cause: `CandidateSnapshot`
annotated `bpa`, `universal_value` and `team_acquisition_value` as `float`, never
`Optional[float]`. The annotation lied, and whoever wrote the card believed it. This exact
inconsistency was already recorded ("a probe crashed on exactly that") and deferred as
touching #119's fields; the deferral is what let it reach a render path.

REACHABILITY IS OURS. `_board_order` sorts None-scored rows last, so a None leader looks
impossible. #154's feasibility backstop sorts `_feasible` AHEAD of `final_score`, so an
unpriced candidate filling a REQUIRED slot is promoted over priced candidates that do not --
measured as `unpriced QB, feasibility BINDING -> ['qb1','qb2','rb1','wr1']`. Tier 3 made this
reachable. Each layer was correct alone; the composition was not.

Repaired: annotations corrected, six sites guarded, and a CLASS test that derives the Optional
fields from the dataclass and AST-scans for a format spec with no matching `is not None`.

## #159 — the panel was told an identity the engine does not compute

DONE. `depth_exposure` joined the team_acquisition_value sum at #139 and neither the
Strategist prompt's definition of TAV nor the per-candidate evidence line was updated. The
panel was handed a whole and two of its three parts -- an arithmetic contradiction shown to a
model instructed never to recompute, which is the one thing the snapshot exists to prevent.

Also repaired at the same boundary, same contract: `if candidate.denial_value:` swallowed a
MEASURED 0.0 ("no intervening rival gains from him" -- an argument for waiting, reading to the
panel as "never computed"), and `positional_forfeit > 0` did the same despite carrying an
`is not None` beside it.

Ratchet: the summed terms are extracted from draft_room's own assignment by AST, so a fourth
term fails the test the day it is added rather than silently making the prompt wrong again.

## #156 — Q3 answered: the modifier decides, and there is a second road in

71 board states, 5 formats.
  - >=1 position at demand rank 1:            20 / 71  (28.2%)
  - >=2 positions simultaneously at rank 1:   12 / 71  (16.9%)   <- Q3's literal question
  - top two board rows share a bpa:           12 / 71  (16.9%)
  - of those, a modifier decides the order:   12 / 12  (100%)

The spine/modifier interpretation is CONFIRMED and stronger than posed: not that modifiers can
take over, but that whenever the spine stops discriminating, `time_horizon_adj + risk_adj`
breaks the tie every time. No counterexample in 71 states.

CORRECTION TO MY OWN CHARACTERIZATION: the rank-1 identity is not the only road to a flat
spine. Per format, spine_flat and rank1>=2 diverge (8T: 2 vs 3; superflex: 1 vs 4); the totals
coincide at 12 by accident. In superflex the flattening is mostly NOT #156's mechanism.
Claiming #156 explains the collapse would be an overclaim. Classification of the second road
is measuring now.

---


---

# #156 — THE CONTRACT BOUNDARY, CHARACTERIZED. NO REPAIR PROPOSED.

Requested as a semantic-contract question, not a coefficient exercise. Five questions, answered
against the code and against real boards. **Nothing here is implemented.**

## Q1 — what is `bpa == 0.00` asserting at demand rank 1?

`replacement_levels` ends with:

```python
idx = min(rank - 1, len(at_pos) - 1)
levels[position] = float(at_pos.iloc[idx][value_col])
```

At `rank == 1`, `idx == 0`: the replacement level IS the best remaining player at that position.
His VOR is therefore `x - x`. **Exactly 0.00, by identity, for any x.**

**This is a fourth category, and none of the three proposed in the framing question fits it.**

| candidate reading | verdict |
|---|---|
| "genuinely zero value" | NO. It says nothing about the player. Swap in a 400-point QB and it is still 0.00. |
| "unable to discriminate" | NO. Inability implies a comparison was attempted and came back flat. |
| "numerical zero granting permission" | That is the CONSEQUENCE, not the assertion. |
| **a tautology reported as a measurement** | **YES.** Arithmetically valid, semantically vacuous. |

Is it comparable across positions? **No, and that is the whole defect.** A position at rank 4
reports "this player is N points better than the 4th-best remaining, who is what you get if you
wait." A position at rank 1 reports "this player equals himself." Those are not two values of one
quantity; they are two different sentences sharing a column. The rank-1 sentence contains no
information about the player, and it outranks every honest negative on the board.

## Q2 — is `time_horizon_adj` intended to discriminate when `bpa` cannot?

**No, and the repository says so explicitly, in two independent places.**

`TIME_HORIZON_CLAMP = (-10.0, 10.0)`, and CDME_CONTRACTS calls it *"a small bounded dynasty
nudge"* measured at 2.99 / 2.63 / 2.84 / 1.33 / 1.41. It is designed and sized as a MODIFIER.

More decisively, the contract already states the exact rule this violates:

> *"Outside the domain the engine declines and says so. It must not clamp, must not substitute a
> different anchor under the same name, **and must not let a downstream term silently become the
> whole decision.** `universal_value` must not be permitted to reduce to
> `time_horizon_adj + risk_adj` without the board declaring that it has."*

**So the semantic contract is not missing. It is written and partially unimplemented.** The
domain repair it authorises was applied to `demand < 1` (the key is omitted, and
`_remaining_demand_rank` returns `None`). Rank 1 sits INSIDE that domain and reproduces the same
prohibited outcome.

The owner's spine/modifier interpretation is therefore **confirmed, and it is not novel** -- it
is the contract's own words. What is new is that the boundary is drawn in the wrong place:

> The domain gate asks **"is at least one whole slot still unfilled?"**
> The semantic requirement is **"is the replacement someone OTHER than the player being priced?"**
> Those differ exactly on rank 1.

`_remaining_demand_rank`'s own docstring flags the gap in advance: *"The `int(round(...))` below
is deliberately untouched: its rounding boundary is a separate question with its own behaviour,
and this repair changes only the domain gate."* #156 IS that deferred question, observed live.

## Q2b — the feedback loop, which no prior item names

`remaining_starter_demand` is summed PER TEAM (correctly -- its docstring records the measurement
that forced that, including the twelve-QB hoarding case). So demand of exactly 1.00 means **one
team still needs one**.

In the failing draft, QB demand is **1.00 from round 10 to the end and never moves.** That 1.00
is chair 2's own unmet need. Which produces:

> **One team's unmet need makes the position price at 0.00 -- the best number on a board where
> everything else is negative -- so the OTHER nine teams drain it.** The need advertises the
> position to everyone except the team that has it, and cannot resolve, because the team that
> needs it is one of ten competing for a supply its own need created demand-signal for.

39 of 39 priceable QBs consumed by a ten-team 1QB league; 21 in rounds 12-14; chair 2 finished
with none.

## Q3 — reachable states where positions collapse together

**MEASURED.** 71 board states, 5 formats (10T / 12T / 8T / 12T superflex / 14T), every round,
one chair, real boards.

| | count | share |
|---|---|---|
| at least one position at demand rank 1 | 20 / 71 | 28.2% |
| **two or more positions simultaneously at rank 1** | 12 / 71 | **16.9%** |
| top two board rows carry the same `bpa` (spine flat) | 12 / 71 | 16.9% |
| **of those, the two rows differ in `universal_value`** | **12 / 12** | **100%** |

The last row is the answer to the framing question, and it is unconditional. Whenever the
spine stopped discriminating, `time_horizon_adj + risk_adj` decided the order — every time, no
counterexample in 71 states. The transition from modifier to primary ranking signal is not a
tendency that shows up under some conditions; it is what always happens once `bpa` goes flat,
because nothing else in the ordering is capable of breaking the tie.

Concretely, at round 12 of 10T_ppr: QB (demand 1.00) and RB (demand 1.33) are simultaneously
rank 1, both price at exactly 0.00, and `time_horizon_adj` (0.00 vs −9.48) chooses.

**A CORRECTION TO MY OWN CHARACTERIZATION, and it narrows what #156 explains.** The rank-1
identity is *not* the only way the spine goes flat. Per format the two counts diverge — 8T has
2 multi-rank-1 states against 3 flat spines, superflex has 1 against 4 — and the totals
coincide at 12 only by accident. In superflex, most flat spines are NOT this mechanism.

So: the *consequence* (a modifier decides) is universal, but the *cause* is at least two
distinct things, and repairing #156 would fix only one of them. Saying "#156 causes the
collapse" would be an overclaim. The second road is being classified now — the live hypothesis
is same-position ties from coarse or identical projections, which would be an honest INPUT tie
rather than an engine tautology, and would deserve disclosure rather than repair. Those are
different defects and must not receive the same fix.

## Q4/Q5 — the options, their architecture, and their opposite failures

**No option is chosen. The equation is the owner's.**

### Option 1 — pre-draft anchor continuation
Price a rank-1 position against its PRE-DRAFT replacement level instead of the live one.

*Architecture:* machinery already exists (`_fill_omitted_from_anchor`, `predraft_replacement_anchor`,
and `replacement_basis` already distinguishes the two claims on every row). Smallest change.
*Interaction:* Tier 2 and Tier 3 both unaffected -- the number stays a number.
*OPPOSITE FAILURE:* **it makes the problem worse, not better.** The pre-draft anchor is a LOWER
bar than the live one, so a drained position's remaining players price HIGHER, not lower. This
would accelerate the drain it is meant to stop. It also revives the exact claim
`replacement_levels`' docstring says was wrong -- asserting a scarcity number for a position
whose scarcity is no longer being measured.
*Status: I believe this is disqualified on its own mechanism, not on taste.*

### Option 2 — semantic absence
At rank 1, the comparison is degenerate, so decline: no VOR, no `bpa`, `None`.

*Architecture:* the absence contract's own answer, and the same move `replacement_levels`
already makes for `demand < 1`. It draws the domain gate at "is the comparison non-degenerate"
rather than "is a slot unfilled" -- one predicate, consistently applied.
*Interaction with Tier 3:* **TESTED, and it works.** `_board_order` leads with
`fills_required_slot`, so an unpriced-but-required row is promoted to the top while an
unpriced-but-not-required row correctly falls last:
```
unpriced QB, feasibility BINDING     -> ['qb1','qb2','rb1','wr1']   reachable
unpriced QB, feasibility NOT binding -> ['rb1','wr1','qb1','qb2']   unpriced last
```
That coupling exists by accident -- the flag leads the sort because of #155, for an unrelated
reason -- but it holds.
*Interaction with Tier 2:* Tier 2 reads `positional_forfeit`, which is a difference of
`universal_value`s. If those become `None`, forfeit becomes `None` and Tier 2 goes SILENT at
exactly the positions in the collapsed state. **Tier 2 must be designed knowing this**, and it
is a real constraint on its design, not a footnote.
*PREDICTED second-order property, NOT MEASURED:* if absence applies league-wide, nobody drafts
the position while it is unpriced, so the supply #156 currently drains is PRESERVED until a
team's feasibility binds. The one team that needs it takes it; the other nine do not spend picks
on it. That is the exact inverse of today's pathology from the same mechanism -- and it needs a
full-draft test before anyone believes it.
*OPPOSITE FAILURE to hunt for:* every team defers the position to its final picks, so the
position is allocated by feasibility ordering rather than by value -- "everyone gets a QB, all of
them replacement-level, and which one you get is arbitrary." Whether that is a pathology or the
CORRECT answer depends on whether QB VOR above replacement is genuinely ~0 at that point. If it
is, arbitrary allocation is honest. If it is not, absence has thrown away real information.
**That question is unmeasured and is the one I would want answered before choosing option 2.**

### Option 3 — principled cross-positional treatment
Keep pricing rank-1 positions, but make the comparison legitimate -- e.g. price against a
common cross-positional reference so that a rank-1 zero and a rank-4 zero mean the same thing.

*Architecture:* the largest change, and the only one that addresses the stated defect DIRECTLY
(comparability) rather than by removing one side of the comparison. It is also #50/Phase 3's
actual subject.
*Interaction:* Tier 2 keeps a working `positional_forfeit` (unlike option 2). Tier 3 unchanged.
*OPPOSITE FAILURE:* a cross-positional reference is a new ruler, and #74/#75/#76 measured what
happens when this engine's ruler moves -- the reference carried 94.5% of all `bpa` movement, and
a 5-point real gap read as 6.9 bpa at round 2 and 500 at round 13. **Any new shared reference
must be shown NOT to reintroduce that**, and that is a substantial measurement, not an argument.

### Option 4 — declare the transition (the contract's literal text)
Keep the number, but make the board SAY that `universal_value` has reduced to
`time_horizon_adj + risk_adj`, and let consumers decide.

*Architecture:* smallest possible. A new basis field alongside `replacement_basis` /
`horizon_basis` -- the idiom already exists six times over.
*Interaction:* none forced. Tier 2/Tier 3 unchanged.
*OPPOSITE FAILURE:* **it changes no behaviour.** The engine would still drain the position; it
would merely annotate that it was doing so. That is honest, and it is not a repair. Worth having
REGARDLESS of which repair is chosen, because it makes the state observable -- but it must not
be mistaken for fixing anything.

## What I would want measured before the choice is made

1. Q3's frequency (running) -- is the collapsed state routine or marginal?
2. Under option 2, is QB VOR above replacement genuinely ~0 at rank 1, or is real information
   being discarded? This decides whether option 2's "arbitrary allocation" is honest or lossy.
3. For option 3, whether any candidate shared reference survives #74/#75's ruler-drift test.

## The rule this establishes regardless of the choice

> **A number may only be compared against another number produced by the same kind of claim.**
> `bpa` at rank 1 and `bpa` at rank 4 are different sentences. Whatever repair is chosen must
> make them either the same sentence, or not comparable at all -- never silently both.

---

## The policy choice, after Q3

**The equation stays the owner's. This is a recommendation with its reasoning exposed, not a
decision.**

Q3 changed which option I would argue for, and the reason is the second road. Before Q3 the
problem looked like one mechanism with one repair. It is not: the *consequence* (a modifier
decides) is universal at 12/12, but the *cause* is at least two different things, and only one
of them is #156's rank-1 tautology. **A repair aimed at the tautology fixes one road and leaves
the board silently doing the same thing by the other.** That asymmetry is the whole argument
below.

**RECOMMENDED FIRST MOVE: Option 4 — declare the transition.** Three reasons, in order of
weight:

1. **It is road-agnostic.** Declaring "the spine is flat here; a modifier is deciding" is true
   whether the flatness came from the rank-1 identity, a same-position projection tie, or a
   road not yet classified. Every other option is mechanism-specific and therefore partial.
2. **It is the contract's own remedy, already written.** *"must not let a downstream term
   silently become the whole decision"* — the operative word is **silently**. The contract does
   not prohibit the modifier deciding; it prohibits the board not saying so. On that reading
   the engine is not currently wrong about the number, it is wrong about the disclosure.
3. **It changes no behaviour**, so it cannot introduce an opposite failure — the one option in
   the set with nothing to trade. Under the audit rule, an option whose adversarial case is
   empty because it alters no output is the cheapest thing on the table.

Its honest weakness: it does not make the ordering better. A user told "a modifier decided
this" still gets the modifier's answer. It converts a hidden defect into a visible limitation.
That is a real improvement in a tool whose entire premise is a defensible decision record, and
it is not the same as fixing it.

**AND IT IS NOW CHEAP.** The board already carries `replacement_basis`, and the pass in flight
is putting the decomposition on screen. A "spine flat — ordered by trajectory/risk" marker is
the same surface, the same commit, and it is the first thing that would have made #156 visible
to a human watching a draft rather than to a probe run afterwards.

**WHAT I WOULD NOT DO YET.** Option 3 (a common cross-positional reference) is the only option
that addresses comparability directly and is the real fix, but it is #50/Phase 3's subject and
it introduces a new ruler — and #74/#75/#76 measured what happens when this engine's ruler
moves (the reference carried 94.5% of all `bpa` movement; a 5-point real gap read as 6.9 at
round 2 and 500 at round 13). Shipping a new shared reference without that measurement would
trade a disclosed local defect for an undisclosed global one.

**SEQUENCING.** Declare now (road-agnostic, no behaviour change, already on the surface being
built); classify the second road (measuring); then decide the pricing question with Phase 3,
where the ruler can be measured properly rather than argued.



## #160 — in a rookie draft the spine is an affine function of projection

SURFACED by the briefed adversarial pass, then INDEPENDENTLY RE-MEASURED here before being
believed, because it reorders priorities if true. It is true, and by a wider margin than the
pass reported.

12-team PPR dynasty, `picks=[]`, one board per scope, same engine, same call:

  pool_scope       QB min    RB min    WR min    TE min   negatives
  rookies_only       0.00      0.00      0.00      0.00     0 of 48
  all             -324.00   -129.00   -202.00   -127.00   168 of 264

Every position's minimum bpa in rookie scope is EXACTLY 0.00 and not one row is negative.

MECHANISM, four layers each correct alone. `build_available_pool(pool_scope="rookies_only")`
filters to rookies (correct). `remaining_starter_demand` with an empty history counts every
team as needing all its starters -- documented, and correct for a startup. `replacement_levels`
clamps `idx = min(rank - 1, len(at_pos) - 1)`, so a rank of 12 against a 5-deep rookie QB pool
lands on the LAST rookie (documented behaviour). And `compute_draft_board`'s own `demand_picks`
docstring says a rookie draft must pass full roster history as `picks` with `demand_picks`
scoped to the rookie draft's own picks -- but `build_snapshot` has no `demand_picks` parameter,
so the live path cannot express the split its own contract mandates.

WHY IT MATTERS MORE THAN IT LOOKS. Within a position nothing is wrong: subtracting a constant
preserves order. The damage is CROSS-POSITIONAL, which is the one job the spine exists to do.
A WR at 201 and a QB at 183 are each measured above a DIFFERENT baseline -- the worst remaining
rookie at their own position -- and those baselines have no common meaning, so the comparison
between them is not a comparison of anything. `bpa` has become projection minus a per-position
constant: a monotone transform of a single input, wearing the name of a value-over-replacement.

RELATION TO #156, and this is the useful part. #156 is the spine going FLAT (zero spread, so a
modifier inherits the decision). This is the spine going AFFINE (full spread, but the spread is
just the input's own). Both are the same failure at the contract level -- the primary
cross-positional signal no longer carries the information its name asserts -- and neither is
visible from the number alone, because in both cases bpa looks like a perfectly ordinary float.
That is the argument for instrumenting the SPINE'S DOMAIN rather than patching either symptom.

NOT REPAIRED. Recording only. The repair interacts with #50/Phase 3 (the replacement/horizon
redefinition) and with the `demand_picks` plumbing gap, and picking a rookie-specific baseline
here would be exactly the "tune around a broken ruler" move the standing review warns against.


## #161 — tier 3 assumes rounds == roster slots, and the battery could not have caught it

MINE. `feasibility_first` (the #154 backstop) computes "picks left" as
`len(roster_positions) - mine`. Roster size is not round count: Sleeper carries `settings.rounds`
separately, benches are routinely filled from waivers rather than drafted, and the two numbers
are equal only by coincidence.

VERIFIED by execution. 14-slot roster, 10-round draft, chair has made 9 picks and has no TE,
one pick left:
    ACTUAL picks remaining      = 1
    what feasibility_first uses = 5
    feasibility_first ->        [1, 1]      (0 = promoted, 1 = not)
    BINDS? NO -- the roster finishes illegal and tier 3 stays silent.
On the repo's one real league (33 roster_positions, 29 draftable) the arithmetic makes it
UNABLE TO BIND AT ANY POINT of a 29-round startup.

WHY #150 MISSED IT, which is the more useful half. `draft_battery.py` sets
`rounds = len(roster_positions)` by construction, so every one of the 5,244 picks in the final
gate satisfied the assumption under test. The instrument and the code shared a premise, so the
battery was structurally incapable of falsifying it -- 32 formats of evidence that could only
ever confirm. A harness that fixes a variable cannot test a defect in that variable, and the
right response is not a bigger battery but a battery whose rounds and roster size are allowed
to differ.

SAME SHAPE AS EVERYTHING ELSE FOUND TODAY. The adversarial pass's own closing observation was
that every contract that broke involved a quantity crossing a layer WITHOUT a companion it
needs to be read correctly -- a value without its basis, a pool without the demand it should be
measured against, a pick number without the draft it belongs to. This is that shape again: a
pick count without the round count that gives it meaning. `app.py` HAS `total_rounds` and uses
it only to build the pick order; `league_for_engine` never carries it.

NOT YET REPAIRED (suite mid-run when found). The repair is to give the engine the companion --
an explicit rounds input, defaulting to the current assumption with that default NAMED as an
assumption rather than left implicit -- plus a battery arm where rounds != slots, without which
the fix would be as untestable as the defect.

## #162 — reach_label is saturated where it exists and absent where it does not

SURFACED by the adversarial pass as a rookie-draft defect; MEASURED here and found broader.

  format / scope              SIGNIFICANT REACH
  superflex, rookies_only     35 / 35   (100%)
  superflex, all              41 / 48   ( 85%)
  1QB, either scope           reach_label is None on every candidate

TWO DIFFERENT SITUATIONS, and only one is a defect.

The 1QB None is EXPECTED and stays. `_consensus_lookup` filters `source_name == "keeptradecut"`,
and that filter IS the CDME ingestion boundary (test_cdme_ingestion_boundary.py proves it with
adversarial injection). The consensus corpus is superflex-shaped; 1QB simply has no consensus
row. Closing that gap by admitting another vendor into the lookup is explicitly forbidden and
remains so. The honest statement is that the feature does not exist in 1QB -- which is fine,
provided the UI says so rather than rendering an empty space that reads as "no reach".

The superflex saturation IS a defect. A label whose top severity fires on 85% of a normal board
and 100% of a rookie board is not classifying anything: it partitions the population into
"nearly all" and "a rounding error". That is the #56 shape in a categorical rather than a
numeric guise -- a boundary that does not sit where the data's structure changes, so it carries
no information while presenting as a judgment. It is also self-reinforcing in rookie scope,
where every candidate is compared against the tier of the #1 overall dynasty asset because a
rookie draft's 1.01 is overall pick 1 -- the pick number crossing into the consensus layer
WITHOUT the companion that says which draft it belongs to. The same missing-companion shape as
#160 and #161.

NOT REPAIRED. Recalibrating a band is exactly the kind of change that must not be made to fit a
fixture; the band needs a derived basis (where does the tier-gap distribution actually change
shape?) before any boundary is moved, and that measurement is not done.

## #163 — the basis idiom has the defect it was built to prevent, and that changes the #156 fix

SURFACED by the adversarial pass; MECHANISM confirmed here by reading, and it is structural
rather than incidental.

  draft_room.py:1791   pool["replacement_basis"] = "live_starter_demand"   <- EVERY row
  draft_room.py:1886   relabel to "predraft_anchor"                        <- only _anchored
  _fill_omitted_from_anchor (:1577-1596) EXCLUDES positions the startable-floor branch declined

A floor-declined position is in neither set: no replacement level, so no price, and not in
`_anchored`, so never relabelled. It keeps the default. The column therefore asserts "this
price rests on live starter demand" about a row that HAS NO PRICE. Three real states --
priced live, priced from the anchor, declined and unpriced -- carried by two labels.

THE PATTERN IS THE DEFECT, not this instance of it. `initialize to the common case, then
relabel the exceptions` guarantees that any state the author did not enumerate silently
inherits the common-case label, and inherits it INVISIBLY, because the field is populated and
well-formed. That is the same failure as `depth_exposure = 0.0` standing for four states and
the same as `float` standing for an Optional: a well-formed value that lies. The safe shape is
the opposite -- initialise to UNSET and require every branch to write it, so an unenumerated
state is detectable rather than plausible.

WHY THIS OUTRANKS ITS OWN SIZE. The recommended #156 first move is to INSTRUMENT the spine's
domain -- to add a state saying "the ruler is not ruling here, and this is why". That
instrument is a basis field. Built the way the existing basis fields are built, it would
inherit this exact hole: a spine state nobody enumerated would arrive labelled "normal", which
is precisely the silent authority transfer the instrument exists to expose. So the fix to #156
now has a prerequisite it did not have this morning:

  The spine state must be UNSET by construction and set explicitly on every path, and the
  measurement already says there are at least four paths, not one -- rank-1 tautology (41.7%),
  same-position projection tie (41.7%), cross-position coincidence (8.3%), anchor-priced tie
  (the two rank=None rows). A boolean SPINE_FLAT would merge them and recreate the collapse.

This is the strongest argument yet for the standing review's warning about absence: the repo
already HAS the vocabulary for this and still got it wrong at three separate sites, which
means the idiom needs an enforcement mechanism, not another instance of itself written
carefully.

## What #160-#163 converge on, and the ONE mechanism worth building

Four findings, four different files, one shape. Every contract that broke today involves a
quantity crossing a layer WITHOUT a companion that gives it meaning:

  #160  a rookie pool without the demand it should be measured against
  #161  a pick count without the round count that bounds it
  #162  a pick number without the draft it belongs to
  #163  a price without the basis it rests on -- and the basis field itself mislabelled

The repo's existing answer to this shape is the `*_basis` companion column. #163 shows that
answer is not sufficient AS BUILT, because a companion written by "default to the common case,
relabel the exceptions" silently absorbs every state its author did not enumerate.

THE STRUCTURAL FIX would be to make the companion part of the TYPE -- a value that cannot be
constructed in a self-contradicting state (priced-but-no-basis, basis-but-no-price) rather than
two parallel fields trusted to agree. That is the correct long-term shape and it is also a
large refactor of the exact code that is about to be frozen, so it is NOT proposed now. The
standing sequence (freeze, then refactor) is right, and this belongs after it.

WHAT IS WORTH BUILDING NOW is the one invariant that would have caught all three basis
instances, and it meets the bar the standing review sets -- it prevents a DEMONSTRATED class of
failure at a load-bearing boundary, rather than encoding a preference:

  No board row may carry a basis label while the quantity that basis describes is absent,
  and no row may carry that quantity while its basis is absent.

That is checkable over a real board in one pass, it is falsifiable, and it fails today on
floor-declined rows. It is also the prerequisite for the #156 spine instrument: the instrument
is a basis field, and there is no point adding a fourth companion column to a codebase where
three of the existing ones can lie.

NOT a new ratchet for its own sake -- explicitly contrast this with the WCAG contrast floor
added earlier today, which protects no demonstrated failure and is documentation wearing a
ratchet's clothes. That one should be kept only as a labelled exception or dropped. This one
has three live instances.

## #164 — FORFEIT_SCALE_MAX is a divisor left over from a scale that no longer exists

SURFACED by the adversarial pass; MEASURED here, and my own first measurement OVERSTATED it,
so both the finding and the correction are recorded.

`FORFEIT_SCALE_MAX = 100.0` divides positional_forfeit before it enters pick_necessity. Its
stated justification, in the comment above it, is that "a forfeit expressed as a fraction of
100 is already a meaningful fraction of the biggest gap actually out there -- see draft_room's
ARCHITECTURE section on linear scaling". That linear scaling is GONE: `_scale_vor_to_bpa` is
now the identity and bpa is raw signed points. The constant's basis was invalidated when the
unit beneath it changed, which is invariant 121's exact subject. The same comment already
records a measured max of 117.39 -- above its own divisor -- and kept 100.

MEASURED at the 1.01 of a 12-team PPR draft, the pick with the longest wait in the draft and
therefore where the cost of waiting matters most:

    QB 0.0   RB 155.03   TE 0.0   WR 54.60      (one distinct value per position)

MY FIRST READING WAS WRONG and is corrected here. I reported "12 of 48 candidates clipped,
erasing a spread of 55.03 points". The 12 are every RB, and positional_forfeit is a PER-POSITION
quantity -- all of them already carried the identical 155.03 -- so the clip erases nothing
between them. Recording the error because the shape of it matters: a per-position quantity
counted per candidate looks like a distribution and is not one.

WHAT THE CLIP ACTUALLY COSTS is the CROSS-POSITION ratio, which is the only thing this term is
for. True RB:WR urgency at that board is 155.03 : 54.60 = 2.84x. After the divisor clips RB to
1.0, necessity sees 1.0 : 0.546 = 1.83x. The term does not lose the ordering -- RB still leads
-- it understates by how much, at exactly the state where the answer is least ambiguous.

NOT REPAIRED. Raising the divisor to fit 155 would be fitting a fixture, which is the move #56
exists to forbid. The honest repair is to derive the divisor from the same distribution the
comment already half-measured, or to stop dividing by a constant at all and normalise against
the board's own observed forfeit range -- and that choice belongs with #50/Phase 3, where the
ruler question is already open.


## #165 — the measurement harness crashes on the state the engine is designed to produce

CONFIRMED by reading the producing chain. `roster_diagnostics.compute_team_diagnostics` reads
`p["uv"]` unguarded at three sites -- `:168` (`cell["value"] += p["uv"]`), `:175` (fed to
lineup_optimizer as `value`), `:183` (`sum(...)` for accumulated_value). `uv` arrives from
`cand["uv"]` (`:130`) <- draft_simulation's serialize_snapshot <- `draft_board_ui.py:204`
`"uv": c.universal_value`, which is Optional and is None exactly when a position has no
replacement level. Any trajectory containing one unpriced pick raises TypeError on the first
`+=`.

THE MODULE ALREADY KNOWS HOW. `:204` filters to `priced` and reports `replacement_level_unpriced`
as a SEPARATE COUNT rather than folding absence into the sum -- the correct treatment, present
in one of four places. Same asymmetry as the Draft Room metric cards, where two fields were
guarded and the two the contract names were not.

WHY IT MATTERS MORE THAN "HARNESS-ONLY": app.py never imports roster_diagnostics, so this is
not a user-facing crash. It is worse in one specific way -- this module is how the BATTERY
measures roster quality, and the battery is the instrument behind #150 and behind most findings
recorded today. An instrument that dies on the exact board state the engine is contractually
required to produce cannot measure the regime it most needs to measure. Combined with #161
(the battery's rounds == slots assumption), that is two independent blind spots in the same
harness, both discovered from outside it.

REPAIR, when made, is to apply the module's OWN existing idiom to the other three sites -- skip
unpriced and carry the count -- not to coerce None to 0.0, which would silently understate
every roster containing an unpriced pick and would be the absence contract broken inside the
tool that exists to check it.

### Refinement: the repair is two-thirds mechanical and one-third a decision

`:204`'s filter is `p["position"] in repl_levels` -- it excludes on the REASON (the position has
no replacement level), not on the symptom (`uv is None`). Its comment states the rule this
module already holds itself to: "Unpriced players are excluded and COUNTED, so the number states
its own coverage instead of quietly absorbing the gap."

That rule transfers cleanly to two of the three unguarded sites and NOT to the third:

  :168  per-position depth sum        MECHANICAL. Exclude, carry the count.
  :183  accumulated_value             MECHANICAL. Exclude, carry the count.
  :175  rows fed to lineup_optimizer  A DECISION, not a guard.

At :175 the rows become `value` in the lineup solve. Dropping an unpriced player does not merely
understate a total -- it removes him from the optimisation, so the "optimal" lineup can come back
SHORT A STARTER and `starting_lineup_value` changes meaning without saying so. The alternatives
each assert something:

  exclude          -> the roster is treated as though the player does not exist; a legal lineup
                      may be reported as unfillable.
  value at 0.0     -> he is startable but worthless; breaks the absence contract inside the tool
                      that exists to check it, and he still occupies the slot.
  value = replacement level -> asserts a price the engine explicitly declined to give.

There is no neutral option, which is the tell that this is a semantic question about what an
unpriced asset is WORTH IN A LINEUP, not a missing null check. Recorded and left to the owner;
fixing :168 and :183 does not depend on it and can proceed first.

### REPAIRED, and the repair's own test found a fourth site I had asserted was safe

Two turns before writing the fix I stated that `:204` "already does it correctly". It does not,
and the regression test caught me: its filter is `p["position"] in repl_levels`, which is a
PROXY for what the arithmetic needs (`p["uv"] is not None`). I had even noted the two were
different predicates in the same breath as assuming they coincide -- the implicit-invariant
trap this register keeps recording, walked into while documenting it.

Repaired at all four sites using the module's own stated rule (exclude and COUNT, never coerce
to 0.0), plus a new `unpriced_players` field so every value on the record states its own
coverage: greater than zero means accumulated / starting-lineup / bench-surplus / depth are
FLOORS, not totals. Distinct from `replacement_level_unpriced`, which counts the narrower thing.

The `:175` decision is taken and named in the code rather than left implicit: unpriced players
are excluded from the lineup solve, because it is the only option that asserts nothing about
their VALUE -- 0.0 would say startable-and-worthless, and a replacement level would assert a
price the engine declined to give. The cost is real and recorded: a legally fillable lineup can
come back short a starter, so starting_lineup_value with unpriced_players > 0 is a floor.

Honest limit of the test: it blanks a uv without removing the position's replacement level, so
for the three sums it reproduces a reachable crash and for the surplus it pins robustness
against a coincidence. Stated in the test rather than glossed.

### #161, sharpened: a TEST enforced the assumption the battery could not falsify

The first write-up said the battery "happened to share" feasibility_first's
`rounds == len(roster_positions)` premise. That was too kind. `test_draft_battery` carried
`test_every_format_drafts_a_full_roster`, which ASSERTED that equality for every format in the
matrix. So #150 could not falsify #161 because a guard existed against the only configuration
that would have.

The guard's reasoning was correct for what it protected: a draft shorter than its roster cannot
fill every slot, so auditing it for unfilled starters reports arithmetic as an engine defect.
What went wrong is scope -- protecting ONE audit was expressed as a constraint on the WHOLE
instrument, and nothing distinguished "this audit needs equal rounds and slots" from "the
battery may only ever contain formats with equal rounds and slots".

Resolved by narrowing rather than deleting. The equality still holds wherever the fill audit
runs; `structural_findings` gained `audit_roster_fill`, and the short-draft arm opts out of that
ONE audit while still being checked for unpriced picks, undraftable positions and duplicates --
all of which remain defects at any draft length. Two new pins: the matrix must contain a format
where rounds differ from slots, and every league must tell the engine its round count (without
which the battery measures the fallback rather than the repair).

GENERAL FORM, worth carrying: when a test encodes a precondition of one audit as a property of
the whole fixture, it stops being a check and becomes a limit on what can be observed. That is
the same shape as the ui_source scope (a class test scoped by which framework a file imports)
found earlier today -- a guard whose reach was decided by something incidental to what it guards.

### #165, the reserved half: CAN an unpriced player be contextualized without inventing a value?

The owner reserved this and named the test: "Explore whether an unpriced player can be
legitimately contextualized using existing rankings, relative ordering, positional/tier
information, etc., without inventing a numeric value. Only fall back to exclude + report count
if that investigation fails."

ANSWER: the investigation does NOT fail. Contextualizing material exists, it is not a price,
and it is already in this repo. It just does not reach the board. But acting on it is a
valuation-layer change, not a null-handling one, and that boundary is the whole result.

**First: the population, which is far narrower than every prior write-up assumed.**

I measured before theorising, and the first two measurements were about the wrong thing. On the
OPENING board of HEAVY_IDP, LIGHT_IDP, 10T_ppr and 12T_ppr there are ZERO unpriced rows. Walking
a full draft's worth of consumption in HEAVY_IDP (216 picks) and 10T_ppr (132 picks), still zero
at every depth. `universal_value is None` simply does not occur in those regimes.

The reason is `_fill_omitted_from_anchor`, which fills any position `replacement_levels` omitted
for EXHAUSTED DEMAND from the pre-draft anchor -- and pointedly refuses to fill the ones the
`startable_floors` branch declined. `startable_floors` is set in exactly one place: QB, when
`SUPER_FLEX` is in roster_positions. So the unpriced state is reachable at ONE position in ONE
league shape, and nowhere else.

Confirmed on a knife-edge rather than by reading. `qb_startable_floor` is 163.5 and 28 of 39 QBs
clear it in 12T_ppr_SF. Drain 27 -> 0 unpriced. Drain 28 -> 11 unpriced QBs. Drain 31 -> 8. The
transition lands exactly where the chain says it must.

That knife-edge doubles as the mutation check on my own instrument: the probe that returned zero
for HEAVY_IDP and 10T_ppr DOES report unpriced rows when they exist, so those zeros are a real
negative result and not a broken predicate.

CORRECTION, made the same day I wrote it. I first cited the battery as independent corroboration
here -- its per-format line reads "every player priced, so the values are totals" across all 33
arms. That is NOT independent evidence and I should not have offered it as such. See #170 below:
the number behind that sentence is structurally incapable of being anything but zero. The
knife-edge above stands on its own; the battery adds nothing to it.

Note what this costs #168 and #165's own framing: a 12-team superflex has 24 QB starter slots,
and the state needs 28 QBs gone. It is reachable, not typical. Every prior sentence in this
register implying unpriced players are ordinary in IDP formats was wrong about WHERE the
absence lives -- IDP rows are priced through the trade_value fallback, which is #152's unit
problem, a different finding.

**Second: what survives on an unpriced row, and what does not.**

Present: `projected_points`, `replacement_basis`, `confidence`, `bpa_source`.
Absent: `bpa`, `final_score`, `universal_value` -- all None, correctly.

The board row does NOT carry `proj_3yr`, `trade_value`, or the vendor's `rank`. All three exist
in the merger for the same players. That is the missing-companion shape this register keeps
recording, in its inverse form: the quantity (points) crosses the layer, and the companions that
would let a consumer place the player on a dynasty horizon do not.

On the 11-row tail, the merger holds `proj_3yr`, `trade_value` and `rank` for 10 of 11, and the
three agree with each other strongly (|rho| 0.92, 0.92, 0.99). None of them is a price: they are
a vendor ranking and two relative orderings -- exactly the material the owner authorised.

The eleventh row is why any such scheme must be THREE-state and not two. M Penix carries a
season projection (129.0, the best in the tail) and none of the three dynasty signals. So the
states are: priced / contextualizable / neither -- and collapsing the last two would re-commit
the absence-is-a-value error one layer up.

**Third, and this is where I corrected myself: the ordering disagreement is NOT established.**

On the 11-row tail the surviving signal disagrees with the dynasty signals (rho 0.644 against
proj_3yr), and one player inverts hard: T Simpson is 7th of 11 by projected_points and 1st by
all three dynasty signals (proj_3yr 752, trade_value 23, vendor rank 81 -- best in the tail on
each). I was ready to write that the surviving signal is the wrong one.

The full pool says otherwise. Across all 264 rows carrying both numbers, season projection and
proj_3yr agree at +0.824, and WITHIN QB at +0.940. Per-position: RB +0.872, TE +0.920, WR +0.892.
The lower tail figure is n=11 with severe range restriction, which attenuates a correlation on
its own -- reading it as "disagreement widens in the tail" would be exactly the artifact this
project's measurement discipline exists to catch.

So: Simpson is a real individual counterexample, not a demonstrated systematic inversion. The
claim that survives is the weaker and true one -- the contextualizing material exists and is
concordant; whether it would ORDER the tail differently enough to matter is not established at
n=11 and would need the population widened before anyone acts on it.

**Fourth: a suspicion I chased and had to drop.**

Two QBs in the unpriced tail (J Milroe, A Richardson) carry `projected_points == 0.0` with
`bpa_source: points_vor_draftsharks` and `confidence: 80`. That reads like absence coded as a
measured zero on the valuation path, which would be a serious finding. It is not one.

The raw exports distinguish the two cases, and so does the engine. Every ranking file that
contains a 0.0 also contains blanks, and the two row shapes are different: a BLANK row is blank
in every column (no rank, no proj_3yr, no trade_value -- an unrated player), while a 0.0 row is
fully populated except the season number (rank 124-244, proj_3yr 283-475, trade_value 1-13). The
vendor is saying "rated, and projected not to play this season", which is coherent for these
four players and internally consistent with a real multi-year number. `_derive_points_and_source`
routes blank -> NaN -> the trade_value fallback and 0.0 -> the points path, which is correct
treatment of two genuinely different claims. No defect. Recorded because the negative result is
worth as much as the positive one, and because the next reader will have the same suspicion.

**Disposition, and the line I am not crossing.**

The exclude-and-count fallback is NOT forced -- the investigation the owner ordered found real
material. But the repair that material implies is "carry proj_3yr / trade_value / rank onto the
board row so a consumer can place an unpriced player on a dynasty horizon," and that is a
change to what the valuation layer publishes, in the same territory as #147 (the anchor's
one-season lifetime) and #50 (Phase 3, VOR/replacement/horizon redefinition, which the owner
holds). #164 is already deferred to "after Phase 3 establishes the new scaling/unit". Making it
here, under a null-handling ticket, would be answering a reserved question by implementation --
the exact thing #168's docstring repair refused to do.

So the standing behaviour is unchanged and stays unchanged deliberately: `roster_diagnostics`
excludes unpriced players from the lineup solve and counts them, because exclusion asserts
nothing. `roster_strength` still admits them at 0.0 (#168's behaviour half), which asserts
something false -- and that is now the narrower, cleaner defect, because we know the population
it can bite: superflex QB tails only.

PHASE 3 INPUT, not a repair to make now.

## #161 (identity), resolved as far as evidence allows: there is no BLIND-A1 to preserve

The owner's instruction was explicit: "Separately, resolve the identity of 'Defect A1' before
freeze/#52 ... If no canonical definition exists anywhere in the project/audit record, register
that as a documentation/gradeability finding rather than inventing the target."

Searched, and the answer is the second branch. Evidence, full-history rather than working-tree:

1. `git grep` for `\bA1\b` across EVERY commit reachable from every ref, over `*.md` and `*.py`,
   returns exactly one definition-shaped line, and it is the same line in every commit that has
   one: `CDME_CONTRACTS.md:### A1. NEAR_TIE_BAND = 2.0 -- discriminating per position,
   meaningless board-wide`. That is CONST-A1 -- the constants-calibration item, Decision A, which
   the owner VOIDED this session and renamed out of this namespace precisely because the two
   collided.

2. The frozen baseline itself contains NO mention of A1. `9fb5102` -- the commit every audit
   appendix names as "`main` frozen at `9fb5102`, untouched. Defect A1 untouched." -- has zero
   occurrences of the token. The artifact the phrase asserts something about does not contain
   the thing asserted.

3. The phrase enters the record at `7908136` (Audit §16) and is thereafter copied verbatim into
   the baseline header of §17, §18, §19, §20, §21 and §22 -- seven occurrences, all of them the
   same boilerplate line, none of them a definition. Every commit before §16 that mentions A1 at
   all mentions only CONST-A1, twice, in the constants section.

4. The README's own "Known Limitations & Audit History" -- the prose record of the adversarial
   cycle that `9fb5102` closed -- names the defect that pass "caught and fixed" as the
   eligibility-bonus unit defect. FIXED, not preserved. It names no retained planted defect.

CONCLUSION: "Defect A1" as a preserved blind-audit target does not exist as a defined thing. It
exists as a sentence that was written once and then propagated by copy-paste through seven
appendix headers, each new instance drawing its authority from the previous one. Nothing it
points at was ever written down.

CONSEQUENCE FOR #52, stated plainly rather than worked around: #52 is not gradeable against
BLIND-A1, because there is no BLIND-A1 to grade against. A blind audit can still be run and is
still worth running -- it just cannot be scored on "did the auditor find the planted defect",
because no defect was planted, or if one was, the record of it did not survive.

WHAT I AM NOT DOING, per the owner's instruction and #56's discipline: not inventing a target.
Not nominating some existing open finding as "the" A1 so the exercise has a scoreboard, and not
planting a fresh defect now to give #52 something to find. Either would manufacture the evidence
the audit is supposed to produce. The preservation constraint on "BLIND-A1" is hereby understood
to constrain nothing, because it names nothing; the CONST-A1 constant (`NEAR_TIE_BAND`) remains
untouched for its own reason -- Decision A is reopened and no constant is to be tuned.

This is a gradeability finding about the audit record, not about the engine. The engine is
unaffected. What is affected is the claim, repeated seven times, that a known defect was being
deliberately preserved -- a claim this project could not have substantiated if asked.

## #164 — FREEZE-READINESS TRIAGE: one blocker family, and it is the owner's to rule on

The target is a clean bill of health, freezable. This classifies every open item against that
gate. The headline first, because it is the whole answer:

**The engine is ONE architectural ruling away from freezable, and I cannot make that ruling.**

The full battery over 33 formats and ~5,000 picks produces exactly THREE findings, and all three
are the same audit -- `unfilled_starting_slots`: 10T_half_ppr roster 2 (QB, 7 of 8), 10T_ppr
roster 2 (QB, 7 of 8), HEAVY_IDP roster 5 (DB, 12 of 13). One finding class, in 3 of 33 formats.
Everything else the register holds is a decision, a documented acceptable limit, or blocked on
something outside this machine.

### BLOCKER -- exactly one family (#154 / #155 / #114, with #121 superseding)

A chair finishes a draft unable to field a legal starting lineup. That is user-visible
wrongness, and it is the only thing in the register that is.

MECHANISM, established rather than assumed. In a 10-team 1QB league, 39 QB picks are made
against 10 starting slots; by round 9 every row on the board prices negative, and the
least-negative row is an unstartable backup QB (QB -0.56 against RB -1.45). `feasibility_first`
binds correctly, at exactly the last pick, with zero QBs left on the board -- so the backstop is
not failing. It is being handed a shortage that the pricing layer manufactured upstream. #155 is
the root cause in one line: an exhausted position prices at 0.00 and outranks every live
position's honest negative.

WHY I AM NOT FIXING IT. Every available repair is a change to what the valuation layer means:

  - re-anchor an exhausted position so 0.00 stops beating a live negative -> changes the VOR
    reference, which is #50 Phase 3, which the owner holds ("Opus owns the math" was scoped to
    Phase 3 and Phase 3 has not run).
  - let feasibility_first bind earlier -> makes the backstop compensate for a pricing defect,
    which is the shape #154's recharacterization exists to reject.
  - clamp or floor the negative -> inventing a constant to make an observed regime behave, which
    is exactly what #56 forbids and what the owner voided Decision A over.

There is no version of this that is a null-check. It is the engine's central question, and it
is reserved. NEEDS-OWNER, and it is the single item standing between here and a clean bill.

### NEEDS-OWNER -- decisions, not defects

#50 (Phase 3: VOR/replacement/horizon redefinition -- parent of the blocker) - #147 (the anchor
has a one-season lifetime in a dynasty engine; Phase 3 input) - #152 (the trade_value fallback's
ceiling is a unit artifact; Phase 3 input) - #165's reserved half (contextualizing an unpriced
player: material EXISTS, carrying it is a valuation-layer change; Phase 3 input -- see the
section above) - #160 (Decision A, reopened from zero; no constant to be tuned) - #164 as
originally filed (runtime normalization invariant; deferred behind Phase 3) - #55 (does
pick_necessity participate in candidate selection) - #167 (reach_label: 0 of 36 board states
changed under ablation; demote/remove supported for the engine, LLM-debate effect NOT
established -- recommendation ready, ratification is the owner's) - #146 (bye week is admissible
when the asset horizon is one season) - #149 (upload storage custody) - #98 (the §7.4 allowlist
decision; §7.10 already declined as the owner's call).

### KNOWN-OPEN-ACCEPTABLE -- real, bounded, documented, does not invalidate the engine

#168's behaviour half is now the clean example of this category rather than a loose end: it is
bounded to superflex QB tails (see the #165 section), the docstring no longer asserts the
opposite of its code, and the running battery reports "every player priced, so the values are
totals" for every format -- the population is empty in all 33 arms.

Also here: #153 (need_bonus's cap collapses two roster states in 4WR) - #148 (trend_30d loses
its sign; the quantity is an unwired orphan) - #163 (the H2 comparator changes 2 of 55 evaluable
groups, insufficient in both regimes; #84 already pinned marginal_lineup_value as correctly
stranded) - #122 - #112 - #116 - #119 - #86 - #107/#108 - #110/#111 - #115 - #91/#92/#93/#96/
#97/#100/#103/#105/#117 (the LLM and operations layer) - #37 - #161 (gradeability, recorded
above and deliberately not repaired by inventing a target) - #169 (a broken intermediate commit;
the tree is correct at HEAD and every commit since is clean).

### BLOCKED-EXTERNAL -- cannot be closed on this machine, and no amount of session time changes that

#88 (needs api.sleeper.app reachable) - #120 and #109 (need live provider SDKs) - #49 (needs
real K/DEF/IDP startup boards the owner supplies). These must be either accepted at freeze or
the freeze waits on the owner's inputs. They are not engine defects.

### SEQUENCING -- not gates on correctness

#52 (blind audit, after freeze, stays unbriefed) - #53 (reconciliation and freeze, owner's sole
authority) - #150 (the final-gate battery, running) - #143 - #162 - #158 - #54 - #36/#137 (UI
and hull extraction, a parallel track that does not gate the engine).

### What this means for the standing order

"Repeat the cycle until the batteries and the audit stop producing meaningful defects" has, on
this evidence, converged: the batteries now produce ONE finding class, its mechanism is
established to the pick, and its repair is reserved. Continuing to iterate would not surface
more -- it would re-measure the same three rows.

So the honest state is not "not yet clean". It is: clean except for one named family, whose fix
is a decision the owner reserved and #56 forbids me from guessing at. That is a freezable state
IF the owner is willing to freeze with #154 recorded as a known limitation; it is not one if the
lineup-legality guarantee is meant to hold. That choice is the ruling I need.

## #170 — the battery's reassuring coverage number cannot come out any other way

`roster_strength` reports `unpriced_players` per roster, and every format's summary line says
"every player priced, so the values are totals." Across all 33 arms and ~5,000 picks the total is
**0**. I cited that as corroboration for #165. It corroborates nothing, and the reason is
structural rather than a bug in the counting.

`reference_values` builds the ruler from the PRE-DRAFT board:

    board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None, ...)
    return {str(row["player_id"]): row["universal_value"] for row in board
            if row.get("universal_value") is not None}

Two facts close the loop. The opening board prices every row -- measured, in every format. And
every drafted player is on the opening board, because the pool is "every undrafted valued
player" and mid-draft pools are that same set minus the drafted. So every drafted id is a key in
`values`, `values.get(str(pid), 0.0)` never reaches its fallback, and `unpriced_players` is 0 by
construction rather than by measurement.

WHAT THE SENTENCE ACTUALLY MEANS, versus what it reads as. It reads as "the engine priced
everyone in this draft." It means "every drafted player had a PRE-DRAFT price." Those come apart
exactly where #165 lives: a superflex QB tail can be unpriced on the live board at pick 200 and
still carry a pre-draft price from pick 0, so the roster number is computed against a value the
engine would no longer stand behind, and the coverage line says everything is fine.

SAME SHAPE AS #161, which is why it is worth a number of its own. There the battery could not
falsify a `rounds == slots` assumption because a test enforced it. Here the battery cannot report
a coverage gap because the reference it measures coverage against is taken at the one moment when
coverage is total. In both cases an instrument reports a reassuring number that could not have
come out otherwise, and in both cases the discovery came from outside the instrument.

NOT REPAIRED YET, and the repair is not obvious, which is why it is registered rather than fixed.
The pre-draft ruler is deliberate and correct -- #75/#76 found the moving-ruler defect where the
reference carried 94.5% of all bpa movement, and `reference_values`' own docstring is right that
summing across fifteen board states would measure the draft's progress as much as the roster. So
the fix is NOT "price each player at the moment he was taken". The honest minimum is to stop the
sentence claiming more than it knows: report coverage against the pre-draft ruler explicitly, and
separately count players who were unpriced ON THE BOARD AT THE PICK THAT TOOK THEM, which is the
quantity #165 and #168 are actually about. That second counter does not exist today.

## #171 — QB consumption in superflex is set by the startability floor, not by roster demand

Found while checking whether any battery arm reaches the unpriced regime. It does not, and the
reason turned out to be more interesting than the question.

Every superflex arm drafts **exactly 28 quarterbacks**. Not approximately: exactly, in all twelve.

    league size      8      10      12      14
    QB starters     16      20      24      28
    QB drafted      28      28      28      28

And 28 is not a coincidence. It is the number of QBs that clear `qb_startable_floor`, measured
per format -- the floor itself differs (162.0 in the standard arms, 163.5 in half-PPR and PPR)
and the clearing count is 28 under both, out of 39 QBs in the pool.

So across a range where starter demand nearly doubles (16 -> 28), consumption does not move at
all. The draft takes every QB above the startability floor and then stops, because the ones below
it lose their replacement anchor, go unpriced, and can no longer compete for a pick. In the
8-team league that is 28 quarterbacks drafted for 16 starting slots -- 75% over-selection -- and
in the 14-team league the same 28 happens to match demand exactly.

WHY IT MATTERS FOR THE BLOCKER. #155 says an exhausted position prices at 0.00 and outranks every
live position's honest negative; #154 says the 1QB shortage is manufactured upstream of the
backstop. This is the same claim from the opposite direction and in a different league shape: the
PRICING layer decides how much of a position gets consumed, and roster demand -- the thing a
human would say governs it -- does not enter. A 1QB league over-selects QBs into a shortage; a
superflex league consumes a fixed 28 regardless of whether it needs 16 or 28. One mechanism,
two symptoms.

It also means the battery cannot presently observe the unpriced regime at all, in any arm,
because the draft halts exactly at the boundary that would produce it. That is a real coverage
gap -- but the fix is NOT a new format, because no ordinary league shape crosses the line. It is
whatever falls out of the #154 ruling, since the same pricing behaviour is what stops the draft
there. Registered, not built.

## Battery re-run at HEAD, post-#166: nothing moved, and the new reporting works live

The loop requires a re-run of the affected battery after a repair lands. #166 changed a LABEL
(`horizon_basis` stopped claiming "imputed" beside a floor that was never produced), so the
prediction was that no pick, no roster and no finding would move. Verified rather than assumed.

    formats                 prior 33      post-166 33      labels identical
    findings                prior  3      post-166  3      IDENTICAL
    formats whose content changed, ignoring wall-clock:  0

The three findings are the same three rows, unchanged:

    10T_half_ppr   unfilled_starting_slots   roster 2   empty QB
    10T_ppr        unfilled_starting_slots   roster 2   empty QB
    HEAVY_IDP      unfilled_starting_slots   roster 5   empty DB

So the #166 repair is confirmed behaviour-free on 33 formats and ~5,000 picks, which is what a
label-only fix should be and what nothing had yet demonstrated.

SECOND THING THIS RUN CONFIRMS, and it is the first live exercise of it: #159's reporting fields
came back **24 independent formats and 9 duplicate arms** out of 33 -- exactly the numbers
predicted from the derived detector before the run. The prior report predates both fields, so
this is their first appearance on a real matrix rather than on a fixture.

The runner exited 1. That is `return 1 if total_findings else 0` doing its job, not a crash --
zero tracebacks in a 33-format log. Worth stating because a nonzero exit on a clean run is
exactly the kind of thing that gets read as a failure later.

NOT IN THIS REPORT, deliberately: `unpriced_at_decision` (#170). This battery ran in a worktree
pinned at `ce9d631`, before that counter existed, so its absence here is the pin and not a gap.
It arrives on the next full run, where it is expected to read "no unpriced candidate reached any
of the N decisions" in every arm -- for the reason #171 gives, that the draft halts at exactly
the boundary that would produce one.

## The eight freeze rulings, and the three clarifications that shape #160

All eight docket cards were ruled by the owner (2026-09-06, 16:12-16:21 UTC), read back from
the artifact store rather than paraphrased from memory:

    #154/#155/#114   Phase 3 scope -- re-anchor an exhausted position
    #160             Commission a derivation for each constant, BEFORE FREEZE
    #161/#52         Run #52 blind and unbriefed, but UNSCORED
    #165             Phase 3 -- carry it when the horizon layer is redefined
    #167             Demote reach_label to display-only
    #49/#88/#109/#120  Accept all four as known-open at freeze
    #53/#36/#137     Freeze the ENGINE ONLY; the interface track continues
    #55              Defer until after the #154 ruling lands

TWO CONSEQUENCES that reshape the path rather than just filling blanks:

**#55 resolved itself the moment #154 did.** Necessity-in-selection was deferred until the #154
ruling landed; #154 landed as Phase 3, so #55 follows it there rather than holding its own queue
slot. No separate decision is owed.

**The freeze blocker moved.** #154 was the blocker; ruling it Phase 3 takes it OFF the freeze
path and puts #160 there instead -- it is now the only ruling carrying "before freeze". The
critical path is therefore: derive the three constants -> demote reach_label -> freeze the
engine -> run #52 blind and unscored.

### The three clarifications, and the reading where two of them interact

Asked before starting, because each would have changed the work:

1. **What a derivation may conclude:** it may conclude RESTRUCTURE -- "this constant is
   structurally wrong" or "it should not exist" -- and that verdict returns to the owner. It
   does not land as a diff on my own authority.
2. **What "before freeze" means:** FULLY IMPLEMENTED pre-freeze, restructures included.
3. **#167's boundary:** out of engine math, but it STAYS in the debate prompt.

(1) and (2) are compatible, and the way they compose is worth stating because it is not the
obvious reading of either alone: a structural conclusion goes to the owner as a VERDICT, and
once ruled it is implemented BEFORE the freeze rather than deferred to Phase 3. **So the freeze
waits on those rulings.** The engine does not freeze while a derivation's structural verdict is
outstanding. That is a stronger pre-freeze bar than #160 carried on the docket, and it is the
owner's call, so it is recorded here rather than negotiated.

(3) is the conservative half of #167 and deliberately so. The ablation I ran measured the ENGINE
path -- 0 of 36 board states changed. It measured nothing about what `reach_label` does inside a
debate prompt. Removing it from the prompt would be acting where nothing was established, which
is the exact error class this pass exists to catch, so the prompt keeps it and the prompt effect
is registered as explicitly UNMEASURED rather than silently assumed absent.

## #160 -- the three constants, derived against the populations they actually gate

The docket ruled: commission a derivation for each constant, before freeze; a derivation MAY
conclude "restructure", and that verdict returns to the owner rather than landing as a diff.

### Why the existing measurement was not already the answer

`test_threshold_reachability.py` holds a five-row table and already names the root pattern --
A BOUND SAYS "NEVER MORE THAN THIS", A THRESHOLD SAYS "MEANINGFUL ABOVE THIS". That table is
SINGLE-FORMAT, and its fixture never calls `set_league_format`, so every row of it comes from
one rankings export on one roster shape. A constant's derivation cannot be settled on one board
shape, so the probe re-measured all of it across five formats chosen to differ in team count,
scoring, superflex and IDP (`scratchpad/probe_const.py`, output `probe_const.json`).

Percentages are the share of each population the constant actually splits off:

    population / rule                    10T_ppr  12T_half  12T_SF  14T_std  HEAVY_IDP   max
    P1 leader gap, narrowed  <= 2.0        22.5%    21.1%   11.1%     7.7%     15.3%   161.36
    P2 leader-second margin  >= 2.0        28.6%    57.1%   57.1%    85.7%     28.6%    12.66
    P3 best_uv - leader_uv   >  2.0         0.0%     0.0%   28.6%    14.3%     42.9%     6.03
    P4 within-pos bpa gap    >= 2.0        62.2%    61.7%   60.7%    56.2%     54.7%    71.00
    P5 positional_forfeit    >= 15.0       53.2%    60.0%   72.1%    65.2%     39.4%   248.00
    P6 TAV - UV (context)    >= 12.0        0.0%     4.4%    0.0%     0.0%      0.0%    16.07
    P7a need_bonus           >= 12.0        0.0%     0.0%    0.0%     0.0%      0.0%     8.72
    P7b eligibility_bonus    >= 12.0        VACUOUS -- see the coverage finding below
    P7c depth_exposure       >= 12.0        0.0%     0.0%    0.0%     0.0%      0.0%    11.40

### A1 -- NEAR_TIE_BAND = 2.0. VALUE STANDS; ITS DERIVATION OF RECORD DOES NOT.

The band gates four rules, and it splits all four populations on all five formats: 8-23%,
29-86%, 0-43%, 55-62%. Nothing here is degenerate. **The number survives contact with the
populations it governs, and no re-value is supported.**

What does not survive is the justification written beside it. The comment derives 2.0 from
ADJACENT tav gaps in the TOP 40 of ONE 12-team superflex board. Three of the four rules it
gates are LEADER-RELATIVE on the NARROWED CANDIDATE LIST, and the fourth is a WITHIN-POSITION
bpa gap -- three different populations, none of them the one the derivation cites. That the
value happens to work on all of them is luck the record should not keep claiming as design.
This is a documentation repair with no behaviour change, and it is the honest form of "derived":
say which population it was checked against, and that it was checked against the rest after.

One caveat kept rather than smoothed: P3 (`pure_value`) fires 0.0% on two of five formats. It is
not dead overall (42.9% on IDP) but it is format-dependent, which nothing previously recorded.

### A2 -- NECESSITY_STANDOUT_REFERENCE_GAP = 15.0. CORRECT AS A REFERENCE, WRONG AS A THRESHOLD.

As the standout normalizer's reference it is **correct, and confirmed correct across formats**:
the largest leader-second margin anywhere in five formats is 12.66, so 15.0 still sits above the
distribution, which is the POINT of a normalizer reference.

As `cliff_protection`'s firing threshold on `positional_forfeit` it fires on 39-72% of
candidates -- a badge that lights for most of the field carries almost no information. The two
quantities are not commensurable: leader-second margin has a max of 12.66, forfeit a max of
248.0, a 20x difference in range gated by one literal.

**VERDICT: RESTRUCTURE. Returns to the owner.**

### A3 -- NEED_BONUS_MAX = 12.0. ONE VALUE DOING FOUR JOBS, THREE OF WHICH DISAGREE.

  * As `DEPTH_EXPOSURE_MAX` it is **exactly right and well derived**: depth_exposure rescales
    trade_value by TRADE_VALUE_SCALE_MAX, so its structural maximum IS 12.0, and the measured
    max is 11.40 -- the bound is attained to within 5%. Nothing to change.
  * As `need_bonus`'s own cap it **never binds on any format** (max 8.72, 38% below the cap).
    That is legitimate for a bound under #56 -- a cap is allowed to be slack -- but it means no
    measurement supports 12.0 over any other number above 8.72. It is inert, not wrong.
  * As `ELIGIBILITY_BONUS_MAX` it is **UNMEASURED**, for a fixture reason, not an engine one.
  * As `context_elevated`'s firing threshold it fires **0.0% on four of five formats and 4.4%
    on the fifth**. The in-code comment records "~7.8% of priced rows"; that figure is from a
    sixth, different single format and it does not generalize. Not a wrong measurement -- a
    measurement whose scope was never stated.

**VERDICT: RESTRUCTURE for the context_elevated reuse. Returns to the owner.** The other three
uses stand as they are.

### The coverage finding, which is about the battery rather than the constant

`eligibility_bonus` measured 0.0 at every percentile on every format. That is NOT an engine
property. `run_draft_battery.build_players_db` gives every player exactly one entry in
`fantasy_positions`, so the dual-eligibility term is **structurally zero in this probe and in
all 33 battery arms**. The WR/TE and WR/DB cases the term was built for -- the Travis-Hunter
case named in draft_room's own comment -- are exercised by unit tests and by nothing else.
Registered as #172 rather than reported as a result, because a number measured on a population
that cannot produce it is not evidence about anything.

### What this means for the freeze

Two restructure verdicts, and they are THE SAME DEFECT #144 ALREADY REPAIRED ONCE: a value
chosen as a bound or a reference, reused as a firing threshold. #144 fixed that for the denial
normalizer. `cliff_protection` and `context_elevated` are the two remaining instances, and the
constants contract test already names the second one as an open product decision.

## #172 -- two engine terms are inert in every automated arm, and it is one cause, already ruled

#160's probe found `eligibility_bonus` reading 0.0 at every percentile on every format. Rather
than report that, I asked whether it was a one-off or a class, by sweeping every numeric column
a board row carries across the same five formats and reporting which never vary.

**It is a class of exactly two.** Across 4,144 board rows in five formats:

    eligibility_bonus   1 distinct value   == 0.0
    risk_adj            1 distinct value   == 0.0

Every other numeric column varies (`need_bonus` 13 distinct, `depth_exposure` 24, `bpa` 386,
`final_score` 3,529).

ONE CAUSE, confirmed rather than inferred. `run_draft_battery.build_players_db` synthesizes its
player universe from the projections frame, and that frame carries neither field:

    injury_status        None for all 764 players      -> risk_adj is structurally 0.0
    fantasy_positions    exactly 1 entry for all 764   -> eligibility_bonus is structurally 0.0

Both fields come from Sleeper's players API in production. So this is not a valuation defect and
not a battery-design defect: it is the SAME missing input as #88 (capture the real Sleeper
research fixture), showing up in a second place. The dual-eligibility case draft_room's own
comment was built for -- the WR/DB one -- and the entire injury-penalty path are exercised by
unit tests and by nothing else.

**WHY THIS DOES NOT REOPEN THE FREEZE.** The remedy is a real Sleeper fixture, which is
BLOCKED-EXTERNAL on this machine (no route to api.sleeper.app). That is precisely the family the
owner ruled on this session -- "#49/#88/#109/#120: accept all four as known-open at freeze". So
#172 does not add a new decision; it makes an accepted known-open item PRICED, by naming exactly
what the battery cannot see: two of the engine's terms, one of them a whole scoring path.

What it does change is a claim I should now state more carefully. The battery's clean bill of
health covers what the battery can vary, and these two terms are outside that. Any statement
that "33 formats found one finding class" must carry this caveat, and the #52 blind pass should
be run knowing it -- not because #52 is briefed (it is not), but because a blind pass that
happens to probe injury handling would be probing a path no arm has ever moved.

## #167 -- the demotion was already the state of the code, and my characterization was wrong

The ruling was: take `reach_label` out of engine math, leave it in the debate prompt. Doing that
required first establishing what engine math it was in. It is in none.

The repo's own derived tool answers this without my judgement -- `quantity_readers.scan()`
classifies every surfaced quantity by who reads it:

    reach_label       verdict=observable   scoring_readers=[]   observing=[app.py, pick_debate.py]
    consensus_rank    verdict=observable   scoring_readers=[]   observing=[app.py, pick_debate.py]
    consensus_tier    verdict=observable   scoring_readers=[]   observing=[app.py, pick_debate.py]

Confirmed independently of the tool rather than trusted: every one of the eleven `reach_label`
references in non-test code is a docstring, an f-string for display or the prompt, a dataclass
field declaration, a snapshot carrier, or a history column name. **There is no arithmetic
consumer anywhere.**

SO THE RULING IS ALREADY SATISFIED AND NO CODE CHANGES. What needs correcting is the record --
mine. I wrote #167 up as "reach_label changes 0 of 36 engine decisions under ablation ...
demote/remove supported for the engine", which reads as though there were an engine effect too
small to matter. There was never an engine effect at all. The ablation returned 0/36 because it
was toggling a quantity that no scoring path reads -- a null result about a wire that does not
exist, not a weak result about a wire that does.

That distinction matters for the freeze: "we measured it and it did nothing" invites someone
later to re-measure more sensitively. "It is not connected" closes it.

The prompt half stands untouched per the ruling, and the 85% prevalence figure remains what it
always was -- a statement about a DISPLAY label's distribution, with its LLM-debate effect still
unmeasured and now explicitly registered as such.

## #160 implemented: both restructures landed, and what each one did and did not fix

Ruled by the owner: `cliff_protection` -> gate on the cliff machinery it is named for;
`context_elevated` -> anchor to the sum's own bound, as #144 did.

### A2 -- cliff_protection now asks the cliff machinery

`CLIFF_PROTECTION_TIERS` is DERIVED from `NECESSITY_CLIFF_POINTS` -- the tiers the engine
already prices into necessity -- rather than hand-listing "HIGH"/"MEDIUM" a second time where
the two lists could silently drift apart.

The tier set was MEASURED BEFORE IT WAS CHOSEN, across five formats:

    HIGH + MEDIUM   49.0% pooled   (43.5 - 55.3%)   <- chosen
    HIGH alone      37.3% pooled   (34.8 - 40.4%)
    old rule        (39 - 72%)     forfeit >= 15.0

HIGH-alone was REJECTED DELIBERATELY. It reads better, and that is the entire argument for it;
picking a bar because its percentage is more flattering is the exact move #56 forbids. HIGH and
MEDIUM are the tiers this engine has already ratified as material, so reusing that split is
derivation and inventing a tighter one is not.

**WHAT THIS DOES NOT FIX, stated because the temptation is to claim both:** the badge is still
not rare -- one candidate in two. What changed is that the rate is now produced by a real
detected cliff carrying its own derived materiality gate, and that it is STABLE across formats:
a 12-point spread, against the old rule's 33. A flag whose meaning holds steady across league
shapes is a better flag even when it is not a rarer one.

Absence stays False rather than None, and that is not a shortcut: `detect_positional_cliff`
returns None when the player is last at his position or the pool is too small for a typical
gap, and in both of those cases there is genuinely no cliff to be protected from.

### A3 -- context_elevated anchored to the bound of the quantity it reads

`TEAM_SPECIFIC_CAPS` is now named once, and BOTH consumers derive from it: the denial ramp's
saturation (#144) and this threshold (#160). A fourth team-specific term added to draft_room
now moves both automatically, where before it would have re-broken the second the way #139
broke the first.

`CONTEXT_ELEVATED_THRESHOLD` is the MEAN of those caps -- one term's worth of lift on a quantity
that can hold three. **At today's values this is 12.0, so it changes no behaviour today**
(measured: 0.8% pooled, unchanged), and that is said plainly rather than dressed up as a repair.
What changed is that the relationship stopped being a coincidence and started being maintained.

The orphaned `forfeit` local was removed with it. A local left behind after its only consumer
moves implies a dependency that no longer exists, and this file has already been bitten once by
a comment asserting the opposite of its own code (#168).

### The gate earned its keep: #160's first suite run was RED

`test_cliff_protection_at_the_standout_gap_boundary` failed, and correctly -- it pinned the rule
#160 deliberately removed. This is exactly why the push is armed behind the suite rather than
fired on a comment-only-looking diff: the change was small, well-reasoned, measured on five
formats, and still broke a real test.

REPLACED, NOT DELETED. Dropping that test would have removed cliff_protection's only behavioural
coverage while calling the change "done". The boundary moved instead:

    fires on the material tiers and no others   HIGH/MEDIUM yes, LOW no, absent no
    forfeit alone no longer lights the flag     the exact regression #160 repaired
    the tier set is DERIVED from the points table   so the two cannot drift apart

Mutation-checked 4/4, each turning the suite red: widening the tier set to include LOW; reverting
the flag to the old forfeit rule; narrowing to HIGH only; and replacing the context threshold's
mean with the full sum. The second is the one that matters -- without it, a revert to the old
rule would still have passed the tier test.

### A side effect of #160's A2 worth recording: a live UI contradiction is gone

Checked whether the restructure left any surface describing the OLD rule. It did not -- the board
renders `cliff_protection` as a bare "cliff" force token, and both `pick_debate` and `app.py`
speak about `positional_cliff` (the dict) rather than the flag. No prose needed correcting.

But asking that question surfaced something better. Under the old rule the two were DIFFERENT
QUANTITIES sharing one visual story, so they could disagree on screen. Measured on real boards:

    10T_ppr        3 of 20 candidates
    12T_half_ppr   7 of 20 candidates
    POOLED        10 of 40 = 25.0%

-- a quarter of candidates had the board ticking its "cliff" force while the SAME screen's
Positional Cliff metric read LOW or an em-dash. The force said "there is a cliff here"; the
metric said there is not. Both were honest about their own input, and together they were
incoherent, because `cliff_protection` measured positional_forfeit while the metric measured the
cliff.

Now they read the same quantity and cannot contradict each other. This was not the argument for
the change and is not claimed as one -- the change was ruled on the category error. It is
recorded because it is a real user-visible defect that closed silently, and a defect that closes
without being written down is one nobody can be sure stayed closed.

## #173 -- the absence contract stops at a LANGUAGE boundary, and #158 never crossed it

Found by the adversarial UI critic, verified here against the file rather than taken on report.

#158 repaired the absence contract at six Python sites so an unpriced candidate could not be
misreported. The board's JAVASCRIPT does the same work over the same payload, and it was never
in that scan. Confirmed live in `draft_board_ui.py`:

    :643  const leaderUv = ordered[0].uv;            unguarded
    :698  (c.cliffTypical || 0).toFixed(1)           the `|| 0` idiom the contract forbids
    :704  ${c.uv}                                    raw, unformatted, unguarded
    :710  (ordered[0].tav - c.tav).toFixed(1)        arithmetic on a possible null -> NaN
    :716  ${c.uv} ... (${ordered[0].uv})             two more unguarded

WHY THIS IS NOT THEORETICAL. The leader can legitimately be unpriced: narrow_candidates always
includes each position's best remaining player whether or not it is priced, and the #154
feasibility backstop can promote exactly such a row to the top. That is the state #158 existed
to handle. At it, a person mid-draft reads a sentence explaining their pick that says `null`, or
"about NaN acquisition-value points off the board leader".

THE SHAPE, and it is the third instance today: a repair that stops at a boundary. #166 was a
label outliving its quantity; #172 was a term inert because its input never crossed the fixture
boundary; this is a contract enforced on one side of a language boundary inside a single file.
The Python sites were enumerable by an AST scan, and the JS in a string literal was not, so the
scan silently reported full coverage of a partial surface.

Repair is assigned to the UI agent that owns this file. Not repaired here, deliberately: two
writers in one file is defect #169, which this session has already committed twice.

### The critic's calibration point, worth keeping

Scoring the CURRENT board against the rubric written for the new variants, it fails its own
house rules -- force ticks at 1.65-2.13:1 (readable only on hover, when the README says the four
forces are "surfaced directly rather than left to infer"), the unit-disclosure line below AA,
and the JS absence sites above. Three of the four force glyphs are colour emoji, so `color:`
never applies and the semantic force channel does not reach the screen at all.

So **"no worse than today" is not the bar.** A variant that merely matches the incumbent inherits
a failing grade. That framing is more useful than any individual finding in the list.

### Auditing the ratchet itself, prompted by its own false alarm

The floors failed the UI gate on `test_display_contract_boundary.py` (assertRegex 1 -> 0), and
the sensible next question was whether the instrument is grading the other 107 modules any
better. Checked, and the answer is that it is sound WITHIN ITS DOCUMENTED LIMITS -- which are
already stated correctly in its own docstring, more precisely than my repair commit gave it
credit for:

    "per-name counting has no opinion about which assertions are stronger ... it cannot tell a
     weakening from a STRENGTHENING. pure additions PASS always; any substitution FAILS, either
     way."

So it is a SUBSTITUTION DETECTOR, not a coverage meter, and it says so. My case was a
substitution (one regex -> three named assertIns) and it fired exactly as designed. Worth
recording that the module it blocked had simultaneously gone 13 -> 21 test methods and assertIn
13 -> 35: **a module can nearly double its coverage and still trip this ratchet on a single
substitution.** That is a real friction cost, it is inherent to the design, and the design
accepted it deliberately over a fingerprint (whose repair would be reflexive, and "a check whose
repair is reflexive is not a check").

TWO THINGS CHECKED BEYOND THAT, both clean:

  * **Thinnest floor in the repo**: `test_scoring_functions_parity.py`, 11 test methods against
    3 assertions (0.27/test), which is the vacuous-test silhouette #38/#41 hunted. It is not
    one -- the assertions live in a shared parity helper each test calls. And deleting tests to
    exploit that would drop `test_methods` 11 -> 4, which is floored too. The two counts cover
    each other.
  * **Modules floored at zero assertions**: none. 108 modules, median 1.64 asserts/test.

THE RESIDUAL GAP, stated because no instrument here closes it: a WITHIN-NAME weakening is
invisible to both counts. `assertEqual(x, 5)` -> `assertEqual(x, x)` holds every number
constant and passes. The floors do not claim to catch it; MUTATION TESTING (#38, #41, #157) is
the instrument for that, and it is the one that has actually found vacuous tests here. Two
instruments, two jobs -- which is coherent, and worth writing down so the floors are not
mistaken for a coverage guarantee they never claimed to be.

## #176 [WITHDRAWN -- see #177 at the end of this file] -- THE ROSTER PROOF: the engine
## loses to a constrained naive baseline, 48 of 48 drafts

The question the battery could never answer -- "does the decision architecture actually build
stronger teams, or only defensible picks?" -- now has a measured answer, and it is negative.

    48 drafts. 4 formats. Every seat an engine chair in exactly half the runs.
    ENGINE WIN RATE: 0.0%.  On both yardsticks. In every format. In every run.

                      year 1 (projection)        three-year (proj_3yr)
    10T_ppr           -10.3%  worst -12.0%       -11.1%  worst -13.7%
    12T_half_ppr      -12.8%  worst -17.9%       -12.7%  worst -15.6%
    12T_ppr_SF        -13.7%  worst -15.6%       -13.2%  worst -18.0%
    14T_standard       -9.5%  worst -12.3%        -6.0%  worst -10.9%

THE METHODOLOGY HELD, which is why the result has to be taken seriously:
  * The SEAT-CONTROLLED estimate (each seat against ITSELF as an engine chair vs a baseline
    chair) matches the run-level number to three decimals -- -10.271 vs -10.26 on 10T_ppr. Draft
    position is not doing the work.
  * The STABILITY LADDER is flat: the conclusion at 25% of runs equals the conclusion at 100%.
    More runs will not move it.
  * Both arms drew from the SAME 235-player pool, restricted to what both yardsticks can price,
    after the first attempt's -10% turned out to be a scoring artifact (61% of the full pool is
    unpriced by `projection`, and only the engine drafts those).

### The mechanism, and it is a defect we already have a number for

    format          required slots   ENGINE unfilled   BASELINE unfilled
    10T_ppr              400          25   6.2%            0   0.0%
    12T_half_ppr         576          45   7.8%            0   0.0%
    12T_ppr_SF           648          50   7.7%            0   0.0%
    14T_standard         784          54   6.9%            0   0.0%

**The engine finishes 6-8% of required starting slots EMPTY. The baseline finishes 0%.** That is
#154/#155 -- and the battery had it as three formats with one empty slot each. It is not an edge
case. Under pool pressure it is roughly one starting slot in fourteen, in every format.

### What is inflated here, stated so the number is not quoted naked

1. **The baseline is structurally immune to the failure being measured.** Its rule IS "fill
   starters first", so 0.0% is guaranteed by construction rather than earned. A fair reading is
   "the engine loses to a drafter that cannot make this mistake", not "the engine is 12% worse
   than a human".
2. **The restricted pool is scarcer than a real board** -- 235 players against 140-196 picks,
   where production sees 764. Scarcity is what converts the #155 pricing collapse into an empty
   slot, so the RATE here is an upper bound.
3. **The metric counts starters only**, so every pick the engine spent on bench or dynasty
   horizon scores zero. That is defensible for year 1 and arguably unfair over three.

None of that rescues the direction. A dynasty engine may legitimately trade present value for
future value; it may not fail to field a legal lineup, and it loses the three-year yardstick
too. The owner's instruction on this was explicit and is honoured here: a year-1 deficit is a
finding, not something to wave through as "well, dynasty".

### What this changes

#154 was ruled Phase 3 scope on evidence of three formats with one empty slot each. This
experiment did not find a new defect -- it PRICED the known one, and the price is roughly a
tenth of the roster. That is a materially different input to the freeze decision than the one
the docket carried, and it belongs in front of the owner before #52 rather than after.

## #176 SUSPENDED -- the roster proof does not currently reproduce

Posted #176 as a finding. It is now suspended, and this correction sits directly under it rather
than somewhere a reader will not look.

**The contradiction.** Run 0's seat partition is chairs 1-6. The stored experiment reports its
engine chairs filled `[7, 7, 8, 8, 8, 7]` -- three required slots short. TWO independent
reproductions of that identical configuration, same 235-player pool, same functions, report
`[8, 8, 8, 8, 8, 8]`. Deterministic code does not answer the same question two ways.

**Four causes tested, four dead:**

    draft terminated early          168 of 168 picks made -- no
    scarcity detection failed       supply healthy all draft, no slot ever hit zero -- no
    feasibility model lied          never entered an unrecoverable state -- no
    format sequence contaminated    fresh and after-10T both give 8/8 -- no

**What is still true regardless.** Every trace shows the engine holding available players,
picks remaining, and no dead slot at any point. Nothing measured supports "contextual reasoning
produces worse decisions". What is under suspicion is the INSTRUMENT, not the engine.

**The tally that matters.** This experiment has now produced three measurement failures: a
scoring artifact (61% of the pool unpriced by `projection`, and only the engine drafts those,
which manufactured a -10% deficit before either drafter did anything); a crash that discarded
seven completed runs because the report only wrote per-format; and now a result that does not
reproduce. Two of the three I caught only because I went looking. That is the honest reason
#176 is suspended rather than defended: an instrument wrong twice has not earned the benefit of
the doubt on the third.

A full 12-partition re-run against the stored JSON is in flight. If it reproduces, the finding
stands and my single-run probes were unrepresentative. If it does not, #176 is withdrawn and the
engine's roster behaviour returns to UNMEASURED -- which is a worse position than we thought we
were in this morning, and the correct one.

## #177 -- THE ROSTER PROOF, RESOLVED: #176 was a dead process's output, and the sign was backwards

The re-run answered it. #176 is **withdrawn**, and the mechanism is not a subtle one.

**What happened.** A pre-fix run of the proof -- the one whose pool was never restricted, so the
engine drafted players `score_roster` then excluded while the baseline drafted only players it
could score -- was diagnosed mid-flight as invalid. I renamed its log to `..._INVALID_run1.log`
and moved on. **I never killed the process.** Both runs wrote to the same `ROSTER_PROOF.json`
and the same per-format `.part` paths. The corrected run finished at 21:00 and wrote the valid
result. The invalid run finished at 21:13 and overwrote it -- the aggregate, and one of the four
`.part` files. I then read the aggregate, found 48/48, and filed #176 from a run I had already
declared invalid three hours earlier.

**How it is provable rather than merely plausible.** `pool: len(scoreable)` is unconditional in
the current harness; every format block it writes carries an integer. The clobbered aggregate
carries `pool: None` in all four formats and `engine_unpriced` of 15-18, which the restriction
makes impossible. Three of the four `.part` files -- 10T_ppr, 12T_half_ppr, 12T_ppr_SF -- still
carry `pool: 235` and `engine_unpriced: 0`. The valid run's own log survived intact under its own
name. An independent re-run, launched fresh in its own process, reproduces the valid `.part`
byte-for-byte: 6 of the first 6 runs identical in every field, the rest still in flight.
The harness is deterministic and the valid numbers are the ones it produces.
Everything is preserved under `scratchpad/proof_valid/`.

**The actual result, 48 runs.** Engine advantage over a rank-by-projection baseline. Both arms
draft the same 235-player pool priceable by both yardsticks; `engine_unpriced` and
`baseline_unpriced` are 0 in every arm; `runs_per_format = teams`, so every seat is an engine
chair in exactly half the runs of its format.

| format | yardstick | n | engine win rate | mean adv | worst | unfilled eng starters |
|---|---|---|---|---|---|---|
| 10T_ppr | projection | 10 | 60.0% | +0.86% | -2.34% | 0 |
| 10T_ppr | proj_3yr | 10 | 70.0% | +1.37% | -1.66% | 0 |
| 12T_half_ppr | projection | 12 | 75.0% | +1.25% | -1.26% | 1 |
| 12T_half_ppr | proj_3yr | 12 | 58.3% | +0.70% | -1.59% | 1 |
| **12T_ppr_SF** | **projection** | **12** | **8.3%** | **-1.83%** | **-4.61%** | **0** |
| 12T_ppr_SF | proj_3yr | 12 | 58.3% | +0.32% | -3.80% | 0 |
| 14T_standard | projection | 14 | 100.0% | +3.32% | +0.71% | 8 |
| 14T_standard | proj_3yr | 14 | 100.0% | +6.20% | +0.74% | 8 |

The seat-controlled estimate -- each seat compared with itself across runs rather than against
the other arm's average -- lands within 0.02pp of the raw mean in all eight arms. Chair position
is not carrying these numbers.

**Two things this leaves on the table.**

*The superflex loss is real and it is localized.* 12T_ppr_SF on `projection` wins 1 of 12, and it
loses on the baseline's own objective. The same format on `proj_3yr` is +0.32%. So the engine's
superflex QB behaviour costs current-season starter points and is about neutral across three
years. That is the #154/#155/#165/#171 family -- the halt at exactly 28 QBs, the count that
clears the floor -- appearing for the first time as a measured roster-quality cost rather than a
structural description. The owner's standing instruction applies directly: we do not assume or
aim to lose year 1. This is a finding to act on, not a dynasty trade-off to wave through.

*14T_standard wins 100% while leaving 8 starter slots empty* across 98 engine rosters. An
unfilled slot contributes 0 to `starter_value`, so the engine is beating the baseline while
carrying a self-imposed hole. The hole is the #154 family again, and it is a second, independent
sighting of it.

**What I will not claim, and the wrong fix for it.** The SF projection arm's cumulative mean runs
-0.11 -> -1.55 -> -2.09 -> -1.83 across its 12 runs, which looks like an unsettled magnitude. It
is not, and reading it that way produces the wrong remedy. `seat_partitions(teams, runs)` selects
engine seats by `(s - k) mod teams`, so for a 12-team league the 12 partitions ARE the complete
enumeration of the contiguous-rotation family -- run 12 would be byte-identical to run 0. The
trace is a cumulative mean over an ordered enumeration, not a convergence diagnostic over random
draws, and -1.83% is exact over that family. **More runs would add nothing but duplicate rows.**

What is genuinely untested is whether the result generalizes beyond this one SF configuration.
Three things vary and none of them is `runs`: a different partition SHAPE (contiguous blocks is
one family; interleaved seats is another, and would separate "the engine is worse in superflex"
from "the engine is worse when its chairs are adjacent"), a second superflex league with a
different roster shape, and a baseline that is not deterministic rank-by-projection. Until at
least the first two are run, "-1.8% in superflex" is a direction measured exactly on one
configuration, not a property of superflex.

**The rule this bought.** Doctrine M7b: *an invalidated run is not invalidated until it is dead.*
Renaming a log does not stop a writer. Kill the process, move its output paths aside, and give
the corrected run a different path. This experiment has now produced four measurement failures --
a scoring artifact, a crash that discarded seven runs, a non-reproducing result, and a
write race between two code versions -- against zero engine defects of its own discovery. The
instrument standard (M1-M9) was written from the first three. The fourth was already in the
tree while I was writing it.

## #178 PRE-REGISTRATION, AMENDED: a one-sided criterion is not a criterion

I first registered the acceptance test for `SUPER_FLEX_QB_SHARE = 1.0` as: *re-run the 12
superflex roster-proof partitions and see whether #177's -2% to -4% deficit closes.* The owner
caught that this is one-sided -- **"or a degrade elsewhere"** -- and they are right. As written
it would accept a change that buys superflex points by quietly costing something else, because
it never looks anywhere else. A criterion that can only confirm is not a criterion.

**The blast radius, proven rather than asserted.** `SUPER_FLEX_QB_SHARE` is read in exactly one
branch of `starter_slot_counts`, the one guarded by `slot == "SUPER_FLEX"`. So a format with no
such slot cannot see this change at all. Checked by holding the roster shape fixed and toggling
the constant between 0.85 and 1.0:

    12 of 33 battery formats have a SUPER_FLEX slot -- these may move
    21 of 33 do not -- 12T_ppr, 12T_standard, 10T_ppr, 14T_standard, HEAVY_IDP and 16 others
    all five spot-checked non-SF formats: starter_slot_counts IDENTICAL at 0.85 and at 1.0

That turns "don't degrade anything else" from a vague hope into a hard invariant.

**The amended gate. All four must hold, or the commit is reverted.**

    1. 12T_ppr_SF's projection deficit closes materially.        (the thing being bought)
    2. The three NON-superflex roster-proof formats -- 10T_ppr, 12T_half_ppr, 14T_standard --
       come back BYTE-IDENTICAL. Not "no worse". Identical. The constant cannot reach them.
    3. The 21 non-superflex battery formats report the same findings as before. Any
       difference is an unexpected coupling and is itself a finding, investigated before
       anything is kept.
    4. No superflex format GAINS a finding. Buying starter value while breaking something
       else in the same format is the trade this gate exists to refuse.

Condition 2 is the sharp one, and it is the owner's amendment doing the work: it is a
falsifiable prediction rather than a comparison. A change that is supposed to be inert in 21 of
33 formats and is not inert has done something I did not understand, and no improvement in the
twelfth format would make that acceptable.

**Recorded before the results exist.** The suite gate was still running when this was written.



## #191 RETRACTED AND INVERTED -- THERE IS NO DOUBLE-COUNT; SLEEPER PROJECTS INJURED PLAYERS
## FOR A FULL SEASON, AND "QUESTIONABLE" IS NOT AN INJURY STATUS AT ALL

**A published claim of mine was wrong and is withdrawn in full.** I reported that Sleeper's
season projection already degrades with `injury_status` -- "10-23% in every band", controlling
on the vendor trade value -- and that `risk_adj` therefore counted the same fact twice, live,
since #192/#193 made `sleeper_points` a pricing input. I recommended dropping `risk_adj` where
that basis prices the row. Every part of that is wrong.

**Why it was wrong.** The four trade-value bands were coarse and the injured sample was 97/145
`Questionable`. Re-measured per status against each player's 15 nearest-trade-value HEALTHY
peers, the estimator's own noise floor swallows the effect:

    group            n     median ratio    p25     p75
    (healthy ctrl)  188        1.01        0.82    1.47   <- the noise floor
    Questionable     52        0.85        0.74    1.04
    IR                3        0.56        0.10    0.94   <- n=3
    PUP               1        0.24         -       -

`Questionable`'s 0.85 sits inside the healthy control's own IQR. `IR` had n=3.

**What actually settled it was not a ratio.** Sleeper publishes a projected GAMES PLAYED:

    status          n     gp
    (none)        700     overwhelmingly 17
    Questionable  100     95 x gp=17,  5 x gp=16
    IR             23     20 x gp=16,  3 x gp=17
    PUP            12      4 x gp=16,  8 x gp=17
    Sus             2      1 x gp=16,  1 x gp=17

**Sleeper projects injured players for a full season.** There is no degradation to double-count
and there never was; the entire apparent effect is a one-game 17->16 shift, about 6%.

**So the real finding is the opposite of the one I filed.** `risk_adj` is the ONLY place health
enters the valuation, and -18 does not come close to offsetting a full-season projection for a
man who will not play. On the real capture the board ranks **James Conner (IR) 32nd** with
`universal_value` 616, **Luke Musgrave (PUP) 62nd**, **Savion Williams (IR) 71st**.

### The ablation (one process, one code version, toggling only RISK_ADJ)

Board 2084 rows off the committed Sleeper capture; statuses present: Questionable 172, IR 120,
NA 26, PUP 21, Sus 5, DNR 1.

    arm                    top10   top25   top50    moved   max move
    B drop entirely        same    same    CHANGED    253      -34 (Ty Chandler, IR)
    C Questionable -> 0    same    same    same        99       -6 (John Bates)
    D halve everything     same    same    CHANGED    153      -22
    E IR/Out only          same    same    same        99       -6

Answering the three options the owner put: **drop** is actively harmful (it raises men who are
already too high); **downtick** is the same direction with no double-count left to justify it;
**prose-only** is right for `Questionable` and wrong for `IR`.

**What this rules OUT, so nobody re-runs it.** Arm E is bit-identical to arm C. "Doubtful" never
occurs in the capture and "Out" occurs exactly once in the whole player universe, so the only
live statuses the table prices are `Questionable` and `IR`. Two of the four configured
magnitudes are dead letters.

### The ruling, and what shipped

**Owner's ruling: `Questionable` is out of the valuation entirely, and out of the prose too,**
unless historical backing makes it case-specific. Two independent reasons that agree -- the
owner's, which is about football (anything can inspire a Questionable tag; its use around the
league is close to strategic, so it is not a report on a player's health), and the engine's own
(its -1.5 moved 99 of 2084 rows by at most six ranks and never touched the top 50 -- priced
precision on a signal that is not there).

`player_universe.IMMATERIAL_INJURY_STATUSES` states it once and four modules read it:
`RISK_ADJ` no longer prices it; `lineup_readiness` no longer raises a Questionable starter as a
lineup problem; all three of `screen_context`'s evidence builders stop handing it to a chair.
Verified after shipping, same harness: **99 moved, max -6, top-50 unchanged** -- identical to
arm C, as predicted before the change.

**The half-measure was considered and ruled against.** Stop pricing it, keep mentioning it, was
the obvious compromise. Raising a designation to a person asserts that it matters, and repeating
one the engine has just measured as meaningless spends the reader's attention on noise -- the
same defect #200 closed this same day, where two guards that could never go green were teaching
everyone that some red is normal.

**PASSIVE DISPLAY IS DELIBERATELY UNTOUCHED.** A roster table showing what Sleeper says about a
player is reporting the feed, not the engine speaking. The amber pill still renders.

**The one cost, stated rather than glossed.** A person asking the chairs a start/sit question no
longer sees the tag in the evidence handed over, and there is a real argument that a human
deliberating a lineup wants to know a tag exists so they can go check the beat reports
themselves. The mitigation is the pill above. If that trade is judged wrong, restoring it is one
line in `screen_context` and the valuation half stands alone.

**The condition for its return is recorded in the code, not just here:** historical backing,
applied case-specifically to a player whose own record supports it. What may never come back is
the blanket league-wide magnitude (#56 -- a bound is not a threshold).

### What is NOT fixed

- **The IR/PUP half is the owner's call and is untouched** (still #191, open). It needs MORE
  weight, not less -- but the honest repair is at the INPUT (`gp=16` for a player who will not
  play), not a larger hand-set constant. Sizing a repair by inventing a magnitude to fit a
  sample is exactly what #56 forbids.
- **#201 (new):** the draft battery has NEVER exercised `risk_adj`. `run_draft_battery.
  build_players_db` reconstructs players from the VENDOR baseline, which carries no
  `injury_status` at all -- the first ablation returned "0 moved" in all four arms and the
  reason was an empty status Counter, not a null result. Every certification claim to date
  describes a health-free board.
- **#202 (new):** `RISK_ADJ` has no entry for PUP, NA, Sus or DNR, all of which occur in the
  real feed, while "Doubtful" (which never occurs) has one. The recognised vocabulary was set
  without reference to the emitted vocabulary. Deriving it (#126) is structural; choosing the
  magnitudes is a valuation decision and the owner's.

Tests: `test_injury_status_materiality.py`, 9 tests, mutation-checked 9/9 (including reverting
each of `screen_context`'s three emission sites separately -- patching two of them left the
third live, and a test caught it). Four pre-existing tests were INVERTED rather than deleted,
and one -- `test_injury_still_never_increases_universal_value_under_d` -- was switched from
`Questionable` to `Out`, because with the penalty removed it would have compared a player
against himself and passed vacuously.


## #201 -- THE BATTERY NEVER SAW A SICK PLAYER, AND FIXING THAT EXPOSED A 22x COST NOBODY HAD PAID

**The instrument was measuring a universe nobody chose.** `run_draft_battery.build_players_db`
reconstructed every player from the VENDOR projections table -- first initial, surname, position,
team. That table has no health column, so every player carried `injury_status: None`, `risk_adj`
was 0.00 for all of them, and every arm the battery has ever certified described a board with no
health signal on it.

**How it was found, because the shape matters.** A four-arm `risk_adj` ablation returned "0
players moved" in every arm -- a clean, plausible null result. It was not one:

    injury_status present on the board: Counter()

Nothing had been ablated because nothing was there. A null finding and an unexercised instrument
are indistinguishable from the outside.

**What else was unexercised**, not just `risk_adj`: `fantasy_positions` was a one-element list
per player, so #172's multi-position eligibility could not fire; `years_exp` and `status` were
absent entirely, so #193's rookie and not-currently-playing admission clauses were never reached.

### What the real universe costs, measured rather than assumed

| pool | players | board rows | first build | warm build |
|---|---|---|---|---|
| vendor reconstruction | 764 | 280 | 0.60s | 0.18s |
| real Sleeper capture | 6595 | 1111 | **13.19s** | **0.49s** |

**A CORRECTION TO A NUMBER I GAVE VERBALLY MID-RUN.** I reported "one arm has been running 40+
minutes against ~300s before" while the probe was still going. That was not measured: the probe
ran both arms in one process with buffered stdout, so no per-arm number existed at the time. The
table above is the real measurement, taken unbuffered with each stage printed as it finished.

**13.55s per board x 168 picks x 33 arms is roughly 21 hours** -- the difference between a gate
that gets run and one that does not.

### The repair: resolution is a pure function, and it was being recomputed 168 times

`build_available_pool` calls `merge_player` for every player on EVERY board build. Nothing about
a draft in progress can change that answer -- the vendor table is fixed and a player's name,
position and team do not move between picks -- and a MISS runs difflib's fuzzy search over the
whole table before concluding nothing fits. Memoized on `(name, position, team)`, cleared in
`_load` (the one place the tables are rebuilt; `reload()` and `set_league_format()` both route
through it).

**After: 13.19s -> 0.49s warm, a 26x improvement, and the vendor path improved too (0.60 ->
0.18s), which speeds the existing suite.** One arm goes from ~38 minutes to ~97s; the battery
lands at roughly 3x its old cost rather than 22x, which is the honest price of certifying
against the universe the app actually receives.

Three deliberate limits, each with a test: a caller-supplied `df` is never cached; the cached
dict is COPIED OUT (`build_roster_table` does `row.update()` straight onto its result); misses
are cached too, since the miss is the expensive path.

### Collateral from #191, fixed here, and the gap that let it through

Removing `Questionable` from `RISK_ADJ` broke three measurement scripts that subscripted
`dr.RISK_ADJ[status]` live. **Breaking was the lucky outcome** -- had the ruling changed a VALUE
rather than removing a key, they would have re-run silently over different magnitudes and
reported the result under the same name as the recorded one. Each now pins
`RISK_ADJ_AS_MEASURED`.

Nothing in the suite covered the `run_*` scripts at all. Adding that guard found a second defect:
`run_need_bonus_ablation.py` executed its ENTIRE ablation at import -- two full 15-round drafts
and a printed report, on nothing more than an `import`. Found by importing all 26 to check they
still loaded, and watching an experiment run instead. It was the only one of 26 without a
`__main__` guard, which is exactly why it had never bitten.

### What it rules OUT, so nobody re-checks it

**The RISK_ADJ calibration (experiments A and D) is NOT invalidated.** Those scripts INJECT
`injury_status` deliberately (`run_risk_adj_softening_measurement.py:107`, and D's own
`STATUSES` tuple), so they measured real players under synthetic designations. The claims in
`draft_room`'s docstring stand. Only the BATTERY was health-blind.

### What is NOT fixed

- The battery has not yet been RE-RUN on the real universe. #150 remains open and is now the
  gate that matters: a full battery on a correct instrument, producing no new finding class.
- #202 (PUP/NA/Sus/DNR have no `RISK_ADJ` entry) is now measurable for the first time, because
  the battery pool finally contains those designations. Still the owner's ruling.
- #191's IR/PUP half is ruled (fix the input) and unstarted.

Tests: `test_battery_universe_boundary.py` (9), `test_resolution_memo.py` (9),
`test_measurement_script_boundary.py` (6). Mutation-checked 15/15 -- one of which,
"return the cached dict without copying on read", SURVIVED the first version of the memo tests
and is recorded there rather than quietly patched: every test then mutated the FIRST result,
which is a fresh dict either way, so a copy on one side only was invisible.


## #191 IR/PUP + #202 -- THE PROJECTION SAID SIXTEEN GAMES FOR A MAN WHO WILL NOT PLAY THEM

**Ruled by the owner: fix the INPUT, not the penalty.** A wrong number penalised by a hand-set
constant is still a wrong number, and everything reading `projected_points` directly -- the
board's own "who scores most" column -- would go on showing the full season.

### The evidence, and the whole emitted vocabulary

    injury_status   players   with a projection   games played
    (none)             6101              4882     gp16=61  gp17=628
    Questionable        290               286     gp16=5   gp17=95
    IR                  126               126     gp16=20  gp17=3
    NA                   46                22     gp16=1   gp17=2
    PUP                  21                21     gp16=4   gp17=8
    Sus                   8                 7     gp16=1   gp17=1
    DNR                   2                 2
    Out                   1                 0

`RISK_ADJ` recognised `IR`, `Out` and `Doubtful`. **"Doubtful" never occurs once. "Out" occurs
once in the entire universe. PUP, NA, Sus and DNR all occur and had no entry at all** -- so the
designations that ARE season-affecting were priced as fully fit, which is #202.

### The factor is derived from the rulebook, not fitted to the sample

`GAMES_MISSED_FLOOR = {"IR": 4, "PUP": 4, "Out": 1}` -- a regular-season PUP player must miss at
least the first four games; IR with a designation to return, at least four; "Out" is one week.
**The omissions are as deliberate as the entries** (#56): Questionable and Doubtful are
game-time calls with no rule floor, `Sus` depends on a suspension length the feed does not
carry, and `NA`/`DNR` are not health designations. A number for any of them would be invented.

**IT IS A BOUND, NOT AN ESTIMATE, AND THE BASIS SAYS SO.** We know a man on IR misses AT LEAST
four games; we do not know he misses only four. Cutting by the floor removes what is certain and
fabricates nothing. This is exactly the state #188 says the absence vocabulary still lacks a
name for, and `availability_basis` carries it in the meantime:
`rule_floor` / `no_designation` / `immaterial_designation` / `unrecognised_designation` /
`no_games_reported`.

`no_games_reported` is split from `unrecognised_designation` on purpose. "We do not know what
this designation means" and "we know exactly what it means and lack the denominator" are
different absences with different remedies, and collapsing them is the defect this item exists
to correct.

### Measured on the real board

| player | before | after | universal_value |
|---|---|---|---|
| James Conner (IR) | 32 | **41** | 616 -> 404 |
| Luke Musgrave (PUP) | 62 | **161** | -> -13.4 |
| Savion Williams (IR) | 71 | **172** | -> -23.0 |
| Joe Royer (PUP) | 119 | **255** | -> -157 |

34 rows take the cut; 4 carry `unrecognised_designation` and are visible rather than silently
healthy.

**Conner staying 41st is correct, not timid.** Asserting a season-ending absence would invent
the very number this repair refuses to invent. The board now says what is known and labels it.

### The penalty is not charged twice

`health_penalty(status, availability_basis)` returns 0.0 where the input already carries the
cut, and the full `RISK_ADJ` everywhere else. **A split, not a blanket removal**: a row priced
off the vendor's projection has no games-played figure to cut against, so `risk_adj` is still
the only place health enters for it. This is the REAL double-count, as against the one I claimed
on different evidence earlier and retracted in full.

### What is NOT fixed

- **The magnitudes are untouched.** `RISK_ADJ` still holds -18/-10/-5 and "Doubtful" still has
  an entry it will never use. Whether those numbers are right is a separate question and the
  owner's; this repair only stops them from being the ONLY health signal.
- **The battery has still not been re-run** on the real universe. #150.
- **#143 is blocked**: `api.sleeper.app` is denied by this environment's network policy (403 at
  CONNECT, from the proxy's own status endpoint -- not inferred from a failed call). The
  Questionable reintroduction condition therefore stays unreachable.

Tests: `test_availability_haircut.py`, 18 tests, mutation-checked 10/10. **Two mutations
survived the first version and are recorded there rather than patched over**: `health_penalty`
was originally a branch restated inside the test body -- a tautology, the same mistake caught in
#195 the same day, fixed by extracting the function; and DELETING `availability_basis` from the
pool row broke nothing, because every reader uses `.get()` so the companion's absence degrades
silently to None and the rank assertions still hold. That is #166's defect inside the repair for
#166's cousin.


## #191 CORRECTION, AND #180 CLOSED: THE RANKS I PUBLISHED WERE MEASURED ON A BOARD PRODUCTION
## DOES NOT BUILD

**The correction, in full, because it was published in a commit and in the entry above.** The
#191 entry states "the board ranks James Conner 32nd" and gives a before/after table --
32 -> 41, Musgrave 62 -> 161, Savion Williams 71 -> 172, Joe Royer 119 -> 255. **Every one of
those numbers came from a board built with `sleeper_basis` left at its WEEKLY default.**
`app.py:5303` passes `SLEEPER_BASIS_SEASON_SUM`, and the committed capture holds season
projections, so the weekly board is not one this app ever builds.

On the production-shaped board, before the haircut runs at all:

    James Conner    (IR)   rank ~607
    Luke Musgrave   (PUP)  rank ~580
    Savion Williams (IR)   rank ~732
    Joe Royer       (PUP)  rank ~608

**Conner was never 32nd.** The urgency framing was an artifact of my own probe's default
argument -- the fourth instrument error of this session, and precisely what the
engine-measurement skill's fixture checklist exists to prevent. I did not run its checklist
against my own probe.

### What the repair actually does, re-measured correctly

A/B in one process, one code version, toggling only `GAMES_MISSED_FLOOR`, on the production
basis:

    top10 same | top25 same | top50 same
    players moved: 547        max move: +90
    statuses of movers: None 444, Questionable 63, IR 25, PUP 12, Sus 2, NA 1

    biggest drops:  Harold Landry  (PUP)  200 -> 290  (+90)
                    Kyler Gordon   (PUP)  295 -> 373  (+78)
                    Kerby Joseph   (PUP)  319 -> 388  (+69)
                    Micah Parsons  (PUP)  294 -> 361  (+67)
                    Jordyn Tyson   (IR)   479 -> 525  (+46)

**The repair is correct and lands where intended -- the designated players fall, healthy ones
rise past them -- but its effect is entirely BELOW the top 50.** It is a mid-board correction,
not the top-of-board rescue the entry above implied. The 444 unlabelled movers are healthy
players displaced upward, not a side effect on them.

`test_availability_haircut` now builds its board with `sleeper_basis=SEASON_SUM` and asserts the
MOVE rather than an absolute rank, so this specific mistake cannot be made again silently.

### #180 IS ALREADY REPAIRED, and my contrary finding was the same artifact

I measured `bpa_source` per position and reported offence split roughly half-and-half between
the scoring-aware path and the vendor -- QB 39 vendor vs 3 sleeper, WR 102 vs 96. **Same cause:
the weekly default.** `_derive_points_and_source`'s precedence is basis-first and gates on
`SLEEPER_BASIS_SEASON_SUM`; under the weekly basis a league-scored number only fills where the
vendor is silent, which is the OLD rule the #180 comment in that function says was replaced.

Re-measured on the production basis, every position resolves to
`points_vor_sleeper_season_scored`; the vendor retains 12 rows in total across the whole board
(QB 8, WR 3, RB 1). **Offence routes through the scoring-aware path.** #180's premise no longer
holds, and it closes as ALREADY REPAIRED -- by #192's work, not by anything in this pass.

### The standing lesson, stated because it has now cost four measurements in one day

`sleeper_basis` is a fixture parameter that silently changes the ANSWER, and it defaults to the
value production does not use. Every probe against `compute_draft_board` must pass
`SLEEPER_BASIS_SEASON_SUM` explicitly. This belongs in the engine-measurement checklist beside
`set_league_format`, which is the same class of error and already has a warning there.

### Also fixed here

`availability_basis` was emitted but not in `_records_with_normalized_nan`'s list, so unpriced
rows crossed the board boundary carrying `nan` instead of `None` -- the absence contract broken
by the very field added to describe an absence.

### THE FORMULA WAS CORRECTED BY A LIVE OBSERVATION, AND THE CORRECTION REMOVES A LATENT
### DOUBLE-COUNT

The owner checked James Conner against the running Sleeper app and reported two things the
committed capture alone could not show:

  1. **"He currently still shows ~3 points projected in weeks 2, 3, and 4. Not zeroed out yet."**
  2. **"His projection seasonally will drop by at least 9ish once it does."**

Both are decisive, and the second is a prediction the derived formula can be checked against.

**The first invalidated the shape of the original factor.** It was `(gp - missed) / gp`, which
removes four games from whatever the feed reports -- FOREVER. Sleeper has not yet zeroed those
weeks and eventually will; the moment it did and `gp` fell, the engine would have charged the
same absence a second time. That is exactly the defect this item exists to prevent, reintroduced
one layer down.

**Anchored to the season instead -- `(SEASON_GAMES - missed) / gp`, capped at 1.0 -- the cut is
self-limiting.** The numerator is what he can PLAY; the denominator is what the feed COUNTED;
only the gap between them is fabricated:

    gp=17  (nothing removed yet)     -> 13/17 = 0.765   the full correction
    gp=16  (one game already gone)   -> 13/16 = 0.813   correspondingly smaller
    gp=13  (the feed has caught up)  -> 1.000           no cut at all
    gp<13                            -> 1.000           capped; never amplifies

**And the second confirmed the magnitude independently.** Conner in the capture: `gp=16`,
`pts_ppr=48.94`, which is **3.06 points per game** -- and the app's own weekly cards read 3.16
and 3.07. The corrected factor takes 48.94 to 39.76, a cut of **9.18 points**, against an
estimate of "at least 9ish" made from watching the app. Two independent routes to the same
number.

**It also sharpens the finding's wording, which was imprecise in the entry above.** "Sleeper
projects injured players for a full season" is not right. Sleeper applies the ROLE discount and
not the AVAILABILITY discount: Conner's total is low because 3.06/game is low, not because
games were removed. Jonathan Taylor is 19.44/game over 17, Bijan Robinson 21.95/game over 17.
The defect is a per-game rate multiplied by a game count that has not yet been corrected.

**The news item states the rule floor verbatim** -- "Conner will miss at least the first four
games of the season" -- and the player card reads "injured reserve/designated to return". The
four-game figure taken from the NFL rulebook is confirmed by the feed's own reporting, which is
the strongest form this constant's derivation could take.


## #114 RESOLVED, #154 DISSOLVED, #155 RECHARACTERIZED -- THE BLOCKER FAMILY RE-MEASURED ON THE
## CURRENT ENGINE

All three were measured before #193 widened the pool, #196 recovered 56 priced players, #201
gave the harness the real universe, and #191 corrected the availability input. Re-measured on a
full 12-team, 19-round draft against the real capture, with `set_league_format` and
`sleeper_basis=SEASON_SUM` both explicit.

### #114 -- RESOLVED

The claim: 27.8% of an 18-round draft decided by a player-id tiebreak, because so many
candidates shared an identical `final_score`.

**Measured now: 0 of 19 rounds.** No round's top pick ties its runner-up on `final_score`. The
pool widening gave the engine enough genuinely priced players that the degenerate tie regime is
not entered at all. Nothing to repair.

### #154 -- DISSOLVED

The claim: an upstream relative-value collapse manufactures the shortage the backstop then
correctly detects.

The top pick's `universal_value` now declines cleanly across the whole draft, every one priced
through the scoring-aware path:

    r1  Jahmyr Gibbs    RB   217.28
    r5  Saquon Barkley  RB    78.80
    r10 Tony Pollard    RB    12.46
    r15 Jared Verse     DL    11.07
    r19 Travon Walker   DL     2.22

There is no collapse to a degenerate regime. The premise no longer holds.

### #155 -- RECHARACTERIZED, AND MY FIRST DETECTOR WAS WRONG

The claim: "an exhausted position prices at 0.00 and outranks every live position's honest
negative."

**My first detector reported 7 of 19 rounds and did not check the POSITION.** Inspecting round
7, the offending rows were Andy Borregales (K) at 0.00 above Harrison Butker (K) at -0.09,
Tyler Bass (K) at -0.13, and so on -- **all kickers, correctly ordered among themselves.** A
player sitting exactly at his own position's replacement level has a VOR of 0.00 by definition.
That is the arithmetic working, not failing.

Re-run with the position compared: **21 same-position pairs (correct) and 70 cross-position
pairs.** The cross-position cases are real and look like this:

    r7  Dallas Turner    DL  0.00  outranks  Dallas Goedert  TE  -3.86
    r9  Nick Emmanwori   DB  0.00  outranks  Stefon Diggs    WR  -5.43

**But the mechanism is not the one the item names.** Nothing is exhausted -- DL has 219 rows.
Dallas Turner, Nick Emmanwori and Keyshaun Elliott recur because each IS his position's
replacement-level player, and such a player prices at exactly 0.00 tautologically. So the
finding is not "a degenerate zero from an empty position", it is **"cross-position VOR
comparison ranks a zero above a negative"** -- which is what VOR means, and whether VOR is
comparable across positions at all is #74/#76's open question about the bpa unit, not a
late-draft defect.

**NOT REPAIRED, and deliberately not.** Making the engine prefer the -3.86 TE to the 0.00 DL
would require a cross-position comparability rule nobody has derived, which is #56's
prohibition exactly. The honest output is the recharacterization: #155 folds into the bpa-unit
question (#74/#76) and stops being a member of the late-draft blocker family, because the
late-draft collapse it was grouped with no longer exists.

## OWNER RULINGS, this session: #55 stays observable, #184 is documented not fixed

Both were put to the owner with a measurement and a recommendation. Both were ruled "proceed
per your recommendations." Recorded here rather than only in the register, because these are
the two entries the freeze record has to carry.

### #55 -- pick_necessity keeps ZERO selection authority

No code change. What changes is that the current state is now a ruling instead of an accident.

Necessity is computed over the narrowed set and attached to every candidate, but the pick is
`candidates[0]` and that order is `_board_order`. Measured over 60 decisions of a 12-team
superflex dynasty PPR draft on the real capture and the production pricing path (#204):

    necessity agrees with the board's pick : 12 (20.0%)
    necessity would pick someone else     : 48 (80.0%)

**The 80% does not survive inspection.** Seven distinct players were ever nominated, and 42 of
the 48 come from three of them -- McCaffrey 24x, Jonathan Taylor 10x, James Cook 8x, with 46 of
48 at RB. That is three standing objections restated every turn, not 48 independent judgements.

The drivers say why:

    1.02  McCaffrey  nec=100.0  surv=0.00  cliff=HIGH  forfeit=148.67  denial=57.91  tav=60.84
          board took Lamar Jackson  nec=78.1  tav=147.79

Necessity is SATURATED at its own 100.0 cap, so it cannot distinguish "urgent" from "urgent
enough to give up 87 points of value." It is a RATE; `team_acquisition_value` is a LEVEL.
Giving a saturated rate authority over an unsaturated level does not add a signal -- it
replaces the objective with one that cannot express magnitude. This independently reproduces
the level/rate ruling that reverted the earlier wiring at #139, on fresh data, after #196,
#172, #191 and #204.

**The deciding reason is new.** Necessity's loudest disagreements are driven by
`survival_probability`, and #206 records that this input may be miscalibrated: McCaffrey carries
survival 0.00 across 24 consecutive turns and is never taken. A signal is not promoted to
decision-maker while one of its main inputs is under investigation.

**Offered and not taken, recorded so it is not lost:** necessity as a tiebreaker INSIDE the
near-tie band only. `near_tie_with_leader` already exists as a three-state (#195), and that band
is defined as measured noise -- the one region where TAV differences are explicitly not
meaningful and a rate is the right tiebreaker. The measurement is small if the owner ever wants
the option on the table.

The blind spot #55 was originally filed against is separately already closed:
`narrow_candidates` includes the best remaining player at every position precisely so a
scarce-position leader is never invisible to the strategic layer.

### #184 -- KNOWN-OPEN-ACCEPTABLE: the floor and the demand model both answer one question

`compute_draft_board` passes `startable_floors={"QB": ...}` in every superflex league, and that
branch of `replacement_levels` sets the QB level from the CLIFF, unconditionally, without
consulting demand. Two constants answer "what is QB replacement level in superflex" and the
floor wins every time. Measured on 12T_ppr_SF, empty board, one process, both arms, anchor cache
cleared between them (the cache key does not include this constant, so an uncleared in-process
A/B silently serves arm 2 the anchor arm 1 built -- checked for and excluded):

    pos   replacement 0.85 -> 1.00   moved   mean board bpa            delta    rows moved
    QB    200.0 -> 200.0             NO      33.205 -> 33.205          +0.000   0 / 39
    RB    162.0 -> 165.0             yes     -3.819 -> -6.819          -3.000   72 / 72
    TE    143.0 -> 147.0             yes    -22.104 -> -26.104         -4.000   48 / 48
    WR    201.0 -> 202.0             yes    -39.676 -> -40.676         -1.000   105 / 105

So `SUPER_FLEX_QB_SHARE` cannot make a QB more valuable. Its whole realized effect is to remove
0.15 of a slot from RB/WR/TE, raising their replacement level and making all 225 of them
cheaper. 0.85 is not thereby vindicated either: it feeds RB/WR/TE a share of a slot the
optimizer says they never win. Both values are wrong in the same place.

**Why this is documented rather than repaired before the freeze.**

  - BOUNDED, AND PROVEN RATHER THAN ASSERTED. 12 of 33 battery formats have a SUPER_FLEX slot;
    21 provably cannot see the constant at all. Blast radius measured by holding roster shape
    fixed and toggling, with five non-superflex formats confirmed byte-identical.
  - NOW DISCLOSED ON THE BOARD. #185 (shipped at 735c972) makes those 39 QB rows say
    `startable_floor` instead of falsely claiming `live_starter_demand`. The engine states the
    thing it gets wrong rather than hiding it behind a confident wrong label, which is what
    makes "documented limitation" a real category here rather than a euphemism.
  - THE REPAIR IS PHASE 3 BY DEFINITION. Making the floor and the demand model compose into one
    statement changes what replacement level MEANS in a superflex league -- #50, which the owner
    holds. The precedent is the owner's own docket ruling `d154-pricing-collapse = phase3`.
  - THE COST IS MEASURED AND SMALL. #177 puts it at -1.83% to -1.97% on one arm of eight, with
    the engine still ahead in 7 of 8.

**The dependency, named here rather than left to surface later.** #206 MAY PARTIALLY DISSOLVE
THIS ITEM'S PREMISE. #177's superflex deficit is measured on simulated drafts, and those
simulations produce twelve straight QBs in round one. If #206 establishes that the simulated
chairs behave unrealistically, that deficit is partly a simulation artifact rather than an
engine weakness -- which would make #184 less urgent, not more. That is NOT established; it is a
dependency. It is also an argument for documenting rather than fixing, because repairing #184
now would be tuning against a benchmark whose validity is currently under question.

**Reopen triggers, explicit:** Phase 3 (#50) running, OR #206 resolving in a way that changes
#177's numbers.

## #205 ANSWERED, AND #215 -- THE INSTRUMENTS COULD SURVIVE A RESTART BUT COULD NOT FINISH ONE

### #205, complete: six boards, 68 seats, on the real rulebook

`evidence/roster_proof/ROSTER_PROOF_2026-09-08_realrules_COMPLETE_6of6.json`.

| format | asset ruler | mean advantage | points ruler | points gap | starters filled |
|---|---|---|---|---|---|
| `12T_ppr` | 12/12 | +78.2% | 0/12 | -11.2% | 8/8 every seat |
| `12T_ppr_SF` | 12/12 | +61.8% | 1/12 | -5.0% | 9/9 every seat |
| `10T_ppr` | 10/10 | +93.2% | 0/10 | -9.7% | 8/8 every seat |
| `10T_ppr_SF` | 10/10 | +60.5% | 0/10 | -11.1% | 9/9 every seat |
| `12T_standard` | 12/12 | +217.9% | 0/12 | -9.8% | 8/8 every seat |
| `12T_ppr_TEP` | 12/12 | +54.1% | 0/12 | -10.6% | 8/8 every seat |

**Asset ruler 68/68. Points ruler 1/68.** The sixth format adds no format-specific effect; it
lands inside the band the first five described.

ESTABLISHED: the engine builds materially higher-asset rosters in every seat of every format;
it fields 5-11% fewer projected points; and that deficit is NOT a lineup artifact, because every
seat fills every starting slot.

KILLED: the "much worse in 1QB than superflex" pattern does not survive the real rulebook -- the
SF arms straddle the 1QB ones. It was manufactured by #213's rulebook, in which quarterbacks
scored zero, which is precisely where such a difference would be invented.

VOID: the -27% figure. It came from the withdrawn stub-rulebook run.

NOT ESTABLISHED, and stated as a limit of the instrument rather than a hedge: **whether the
trade is correct.** No exchange rate exists in this system between present-season points and
dynasty asset value, so "good dynasty construction" and "systematic mispricing" both fit these
numbers equally well. That is #50/Phase 3 and it is the owner's.

TWO THINGS THE POINTS RULER IS NOT, recorded because the number reads stronger than it is:
  1. **It is not a win rate.** It is the projected points of the draft-day starting lineup.
     Nothing here measures what a 10% projected-points gap does to games won; that mapping is
     nonlinear and UNMEASURED.
  2. **The control is the ceiling on that ruler by construction.** It drafts nothing but "best
     projected points at an unfilled starting slot", so -10% is the gap to a theoretical maximum
     this-season roster, not the gap to a league of ordinary drafters. Measuring the engine
     against an ADP-drafting field, scored by simulated head-to-head, is a DIFFERENT and more
     answerable question, and it is not answered here.

### #215: writing after every unit made the output survivable, not the run finishable

**MEASURED THREE TIMES on 2026-09-08.** The container is reclaimed on OPERATOR inactivity, not
on the job's -- a backgrounded run does not hold it open. Two full-depth roster proofs were
killed 67s and 45s into their SIXTH format, having spent 45 and 30 minutes on the first five.
The 33-arm battery was killed twice, most recently 8 arms in. #213b's incremental write saved
the partial results every time and did not once let a run finish, because the next process
started again at unit one. A ~3-hour battery cannot fit inside the reclaim window at all, so
without a join it can never complete no matter how many times it is launched.

BUILT: `resume_join.py`, one home for the join, used by both instruments via `--resume`.

  - Every unit carries `produced_at_commit`; the document declares `commits_present` and
    `carried_forward`. A single top-level commit on a joined document would be a false claim
    about every unit the last process did not compute.
  - A pre-#215 report MAY lend its own commit to its units, because nothing could resume into it
    and it is therefore single-process by construction. A JOINED report may not -- there the
    report-level commit describes the last process only. Recognised by the absence of this
    module's own keys, never assumed.
  - `--only` together with `--resume` is REFUSED, before any write. `--resume` rewrites `--out`
    from the current matrix, so filtering the matrix would delete every carried arm outside the
    filter. A resume that destroys results is worse than no resume.
  - A carried unit prints through the SAME console builder as a fresh one, with a marker (#126).

**THE JOIN IS LEGITIMATE ONLY BECAUSE THE INSTRUMENT IS DETERMINISTIC, AND THAT IS MEASURED.**
The two 5-of-6 runs above ran at DIFFERENT COMMITS (ef98dd9, cf0b283) and produced byte-identical
numbers for all five shared formats, down to per-seat detail: zero non-timing differences.
`test_resume_join.py` reads both committed evidence files and fails if that ever stops holding.
It also incidentally establishes that #214/F2+F5+#207 changed no roster-proof number.

29 tests, 12 mutations, 12 caught, 0 survivors.

### The process defect this pass produced, recorded because it nearly shipped silently

Two mutation batches ran CONCURRENTLY sharing one backup path. Batch A backed up
`run_roster_proof.py` to it; batch B then "restored" `run_draft_battery.py` FROM it. **The
battery's entire source was replaced with the roster proof's**, and a leftover `if False:` was
left disabling the proof's resume branch. Neither failure announced itself -- the battery still
imported, because it was valid Python, merely the wrong module.

Separately, three mutation scripts died with a `SyntaxError` and never applied. **An unapplied
mutation reads exactly like a surviving one**, and one of them was reported as OK before the
pattern was checked by hand.

Three rules, now recorded in `resume_join.py` beside the code they nearly destroyed:
  1. One backup path PER TARGET FILE, never one shared path.
  2. Verify the pattern is PRESENT before mutating and the file BYTE-IDENTICAL after restoring.
  3. Never run two mutation batches at once, and read the batch's FULL output -- grepping only
     for OK/FAILED hides the SyntaxError that means nothing was tested.

## #216 — THE ENGINE CANNOT DRAFT A RECEIVER OR A QUARTERBACK; THE BACKSTOP HAS BEEN DOING IT

Freeze-blocker candidate. Traced but NOT repaired, and deliberately not patched: no weights
tuned, no constants introduced, nothing merged. Evidence: `evidence/roster_shape/`, reviewer's
report at `REVIEW_216_fable.md` (authoritative), instruments `run_roster_shape_probe.py` and
`run_216_review_probe.py`.

### What it is

Six seats, two formats, real rulebook: every engine seat ends with exactly two wide receivers;
two end with EIGHT tight ends in a one-TE league. Confounds killed first — the pool is WR-RICH
(WR 197 of 481, the deepest position), the passed-over receivers were better (WR#24 at 245
against TE#24 at 148), and the probe reads the real engine (`build_snapshot`'s top candidate
matched `compute_draft_board`'s first row in 6/6 seats, 87/87 picks under a replay gate).

**The receivers and the quarterback are not the board's choice at all.** `feasibility_first` is
a 0/1 sort key (`_feasible` -> `fills_required_slot`) leading the sort in `compute_draft_board`
and `_board_order`. It filters and substitutes nothing — it PARTITIONS, and binds only when
`picks_remaining <= unfilled dedicated slots`: pick 12 of a 14-round roster, exactly where every
published roster's receivers appear. Disabled, seats 1 and 6 end **TE11 RB3 — zero WR, zero
QB**. Unforced at pick 14 the board still takes Dulcich (TE, 124.3) over Concepcion (WR, 165.1).
The board is INERT for those positions; nothing "falls through".

### Two distinct defects, not one

**(a) The stack.** `bpa = projected_points - replacement_level(position)`, with no normalisation
(`_scale_vor_to_bpa` is identity; #75's 72x drift was the removed max-scaler). Replacement is
constant per position at a board state. A tight end therefore starts 43.5 bpa ahead of an
identically-projected receiver — Kittle (TE, 224 proj) scores 55.53 where Coker (WR, 223) scores
11.24. **Multiple legitimate-looking terms push the same way**: `depth_exposure` (a fourth term
in `final_score`, draft_room.py:2698) adds +6.24 to a FOURTH tight end and is 0.0 wherever the
roster is vacant. No single-term patch can fix this.

**(b) The quarterback, which is a different failure.** `remaining_starter_demand` collapses to
1.0 — the drafter's own unfilled slot — once the other seats have taken theirs. Rank 1 makes
replacement THE BEST REMAINING QB HIMSELF, so bpa is EXACTLY 0.00 for thirteen consecutive
rounds and every other quarterback prices negative. This is **cannot value**, not under-value,
and no roster-relative term downstream repairs it: the marginal-lineup arms still take Penix at
r14 under force, because their phantom quarterback IS the best remaining quarterback.

### The historical finding, which is the cleanest part

#84 stranded `marginal_lineup_value` on the claim that *"in the displacement regime it agrees
with the ranking the engine already produces"*. **Measured false on the roster this engine
actually builds**: at CURRENT's own states the top row agrees in only 4/14, 5/14 and 6/14 states
(1QB) and 5-7/15 (SF), with 8-10 of the top ten reordering through rounds 5-11. That ruling was
taken against a SANE roster; the engine subsequently drifted into a regime where its premise
stopped holding. This is not "somebody forgot to wire a feature" — it is an assumption that
expired without anyone noticing.

### Options, measured, none complete

- **Replacement-filled MLV** (phantoms at each slot's replacement level; an empty slot reduces
  exactly to VOR): fixes STARTERS, +137..+165 lineup points in 6/6 seats. Does NOT fix roster
  shape — once eight starters clear replacement every marginal is 0 and the fallback is
  `universal_value`, the same ordering that hoards (bench ends RB9/RB10/TE9). Does NOT fix QB.
  Blast radius: breaks the `TAV = UV + need + elig + depth` identity and ~115 test references,
  `test_need_bonus_cannot_flip_*` by design, `TEAM_SPECIFIC_CAPS` in pick_synthesis, and
  `rival_premium`'s meaning.
- **RAW-MLV (#84 as built)**: best lineup totals of any arm, for an ACCIDENTAL reason — with an
  empty roster a player's marginal lineup value is just his own points, so its early order is
  raw points (Purdy at r1), the only route past a replacement pricing QBs at 0.00. Bench still
  TE7/TE9/TE7. **An instructive control, not a fix.**
- **Scaling the roster term**: no derivation exists, and the derivable proxy does nothing.
- Horizon-floor replacement, and a bench ruler (#62/#115): both belong with #50.

### Three corrections I published and then had to withdraw

Recorded because the pattern matters more than any one of them.
1. "Exactly the WR slot count — a need signal saturating." Wrong; receivers arrive at r12-13.
2. "Receivers arrive once every other tail falls through." Wrong; they are the backstop firing.
3. "`NEED_BONUS_MAX = 12` caps the roster term below the bias." Wrong, and refuted by direct
   ablation: setting the cap to 1e9 is PICK-FOR-PICK IDENTICAL in 6/6 seats, and zero rows sit
   at the cap across 87 states. The cap never binds; `need_bonus`'s own formula tops out at 8.67.
   The conclusion (the roster term is too small) survives; the named mechanism does not.

Also corrected: "pool-derived and roster-blind" is wrong — replacement ranks by
`remaining_starter_demand` across every roster and moves only on BENCH picks. Seat 12 hoards
running backs and the TE gap SHRINKS 43.6 -> -2.3. Same arithmetic as #60, opposite regime.

### Post-fix invariants, for whoever repairs this

1. With `feasibility_first` disabled, compositions equal those with it enabled;
   `fills_required_slot` True on ZERO picks.
2. While the QB slot is unfilled in 1QB, the best remaining QB carries a POSITIVE price, falling
   to <=0 once filled.
3. A candidate the lineup cannot use never outranks one filling an empty slot at positive VOR.
4. A drafter's own bench picks never improve their selection signal at that position.
5. The most-drafted bench position count, backstop off, reported against that position's
   replacement gap — today they move together under every arm.
6. Replay gate at every state.

**Freeze status: OWNER DECISION.** My reading is that an engine which cannot draft a receiver or
a quarterback without a legality backstop is not shippable, whatever the dynasty philosophy. The
call is #53's and the owner's.

**FREEZE STATUS — RULED (owner): #216 BLOCKS THE FREEZE.** No freeze until it is addressed.
This supersedes the "owner decision" line above and the #164 triage, which listed one blocker
family (#154/#155/#114) — all three of those are closed, and #216 is now the blocker in their
place. #53 does not proceed while the board is inert for WR and QB and `feasibility_first` is
the only thing making a roster legal.

## #216 FIX BUILT AND MEASURED — THE BACKSTOP NO LONGER BINDS AND THE LINEUP IMPROVES 6/6; THE OWNER'S ASSET GATE FAILS IN SUPERFLEX (2 REVERSALS, ALL ON THE BENCH); THE QUARTERBACK'S OWN PRICE IS STILL 0.00 — NOT CLOSED, OWNER'S CALL ON #50

**Status: NOT CLOSED.** G1-G8 pass. G9 — added by the owner mid-run, before it was measured —
fails in superflex on the pre-registered sign test. The code is on the implementer's branch
with both numbers and the trade stated (§ "G9" below); it is not merged and the exchange rate
between lineup points and owned-asset points is #50's, not mine.

Implementer: Fable, on `worktree-agent-ab5e1af412aeb9182` (branched from 2f5f304). Full report
`evidence/roster_shape/FIX_216_fable.md`; pre-registration written before any measurement at
`evidence/roster_shape/PREREGISTRATION_216_fix.md`; instrument `run_216_fix_probe.py`; result
sets `evidence/roster_shape/fix_216/`. The adversary's blind battery (b66c051) taken verbatim.

### The change

    displacement_adj(position) = replacement_level(position) − displacement_level(position)  ≤ 0
    team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure
                             + displacement_adj

`displacement_level` (lineup_optimizer): every starting slot pre-filled with a phantom at the
league replacement level for the position, the roster solved against them, a probe at the
position added and the lineup re-solved; what the probe evicts is the level. Equal to the
league level wherever a slot the position can reach is open (so the board is byte-identical to
today's there — an empty roster, every open slot, the E-class guards' own fixtures), equal to my
weakest reachable starter otherwise. No constant, no cap (its magnitude is the measured
over-credit), non-positive by construction (so `TEAM_SPECIFIC_CAPS` keeps bounding the sum),
per position at a board state, `universal_value` untouched. Rostered players are priced in
projected points through a cached full-pool lookup (`roster_points_lookup`) — the lookup #84
said was missing.

### Measured, one process, one code version (6 seats × 2 formats; BASE = term switched off)

| | BASE, backstop ON | BASE, backstop OFF | FIX, backstop ON | FIX, backstop OFF |
|---|---|---|---|---|
| 1QB seat 1 | TE8 RB3 WR2 QB1 · 1987 · forced 3 | TE11 RB3 · 1528 · illegal | WR7 TE3 RB2 QB2 · 2296 · forced 0 | same · 2296 |
| 1QB seat 6 | TE8 RB3 WR2 QB1 · 1899 · forced 3 | TE11 RB3 · 1465 · illegal | WR8 TE3 RB2 QB1 · 2239 · forced 0 | same · 2239 |
| 1QB seat 12 | RB9 TE2 WR2 QB1 · 1884 · forced 3 | RB9 TE3 WR1 QB1 · 1704 · illegal | WR8 RB4 TE1 QB1 · 2209 · forced 0 | same · 2209 |
| SF seat 1 | TE6 QB4 RB3 WR2 · 2469 · forced 1 | TE7 QB4 RB3 WR1 · 2335 · illegal | WR8 RB3 TE2 QB2 · 2592 · forced 0 | same · 2592 |
| SF seat 6 | TE7 QB4 RB2 WR2 · 2357 · forced 2 | TE9 QB4 RB2 · 2097 · illegal | WR8 TE3 RB2 QB2 · 2520 · forced 0 | same · 2520 |
| SF seat 12 | TE5 QB5 RB3 WR2 · 2277 · forced 1 | TE6 QB5 RB3 WR1 · 2158 · illegal | WR7 RB4 TE2 QB2 · 2442 · forced 0 | same · 2442 |

Replay gate: the term-off arm reproduces the recorded #216 sequences pick-for-pick, 6/6; the
instrument's pick equals `compute_draft_board`'s first row after `_board_order` at every one
of 348 states. Lineup points up in 6/6 seats (+123 … +340); pure-argmax overridden 0 times;
`fills_required_slot` True on 0 picks; OFF == ON in 6/6. The QB arrives at r8 unforced in 3/3
1QB seats (r6/r7, r6/r7, r2/r6 in SF). Battery: `test_216_value_board_falsification` 19/19,
`test_216_room_integrity` 20/20 executed in Chromium, `test_216_displacement` 18/18. Mutations:
9 applied (term always zero; term dropped from the sum; adjustments never computed;
multi-eligible probe stripped to its primary; sign flipped; partial basis never stamped; room
sentence removed; a literal constant in the value path; term not serialized), **9 killed, 0
survivors**, every file restored byte-identical — `evidence/roster_shape/fix_216/mutations/`.

### The six invariants

1. backstop never binds — 0/6 seats. 2. QB priced > 0 while open, ≤ 0 once filled — on
`final_score`, every turn, 3/3 seats (caveat below). 3. unusable never outranks an open slot —
battery C 2/2, D 6/6 pairs (LaPorta −35.6 under Adams 21.0). 4. my bench picks never improve my
signal — the ledger gap (`universal_value + displacement_adj`, WR−TE) is FLAT across every
bench pick in every seat (−28.02 × 6 in seat 1) while the league gap the old board ordered on
widens 53.6 → 94.0; one bounded residual on `final_score` from `depth_exposure` (+3.72 at the
pick a bench first exists), pinned as a residual. 5. below. 6. 6/6 and 348/348.

### G9 — the owner's gate: the asset result does NOT survive in superflex

Sign test on `run_roster_proof`'s `cdme` ruler (pre-draft `universal_value` summed over the
finished roster, the engine's own objective; the control's known bench defect stated, not
excused) plus reported age/horizon deltas, term ON vs OFF, engine vs the same control seat:

| | engine cdme total BASE → FIX | vs control BASE → FIX | cdme STARTERS BASE → FIX | mean age | pre-draft horizon adj |
|---|---|---|---|---|---|
| 1QB seat 1 | 408.7 → 392.1 | WIN +98 → WIN +115 | 334 → 632 | 25.4 → 25.5 | −3.14 → −1.44 |
| 1QB seat 6 | 307.6 → 317.0 | WIN +151 → WIN +135 | 239 → 579 | 25.1 → 25.9 | −3.34 → −1.43 |
| 1QB seat 12 | 209.7 → 244.2 | LOSS −78 → LOSS −13 | 191 → 522 | 25.1 → 25.8 | −4.03 → −1.83 |
| SF seat 1 | 858.0 → 576.5 | WIN +412 → WIN +115 | 757 → 878 | 25.7 → 24.3 | −3.08 → −1.15 |
| SF seat 6 | 809.4 → 497.3 | WIN +371 → **LOSS −15 (REVERSAL)** | 663 → 823 | 25.9 → 25.1 | −2.63 → −1.10 |
| SF seat 12 | 738.9 → 418.8 | WIN +266 → **LOSS −57 (REVERSAL)** | 558 → 724 | 28.3 → 26.3 | −2.76 → −2.95 |

Two reversals → G9a fails as pre-registered. Every point of the loss is on the BENCH: what the
engine FIELDS is worth more on the asset ruler in 6/6 seats (+120 … +340); the pre-fix
superflex bench was surplus QB/TE backups with POSITIVE pre-draft `universal_value` (QB4 +55,
TE +13 — scarce league-wide), the fixed bench is receivers priced "nearest to my lineup", every
one below the WR anchor (−12 … −101), summed as liabilities by a ruler whose negatives are
#155/#165-reserved (`CDME_TOTAL_CONTAMINATION`). In 1QB the pre-fix bench was already negative
(TE8 at −4, the r14 QB at −197), so nothing reverses. **The trade for the owner (#50): in
superflex, +123 … +165 lineup points and +120 … +167 fielded-asset points against −281 … −320
owned-asset points, all on the bench.** G9b: horizon adj is BETTER (less negative) under the fix
in 5/6 seats (+1.5 … +2.2); age is +0.1 … +0.9 years older in 1QB and 0.8 … 1.9 years younger
in SF — no win-now creep on horizon, under a year of age creep in 1QB. The stated expectation
("largely preserved, the term is ≤ 0 and `universal_value` is untouched") was wrong: the prices
did not move, the bench's membership did. Decomposition per player in
`evidence/roster_shape/FIX_216_fable.md` §2.3.

### What this rules out

- A bigger `need_bonus`: not derivable and not needed — the bias was on the tight end's side
  of the ledger, and pricing him against MY starter removes it without a scale.
- The lexicographic sort key the review measured as RFMLV_LEX: a key that is not a number would
  make the room display one order and rank another (the C-class guard names this).
- Replacing `bpa` with a lineup marginal: eight consumers read `universal_value` as
  team-agnostic; the roster-relative half belongs in the team layer, and that is where it is.

### What is NOT fixed

- **(b) the quarterback's OWN price.** Taken at r8 unforced — because every surplus row is now
  priced below `need_bonus`'s 4.0, not because he is priced: his bpa is 0.00 at every open turn
  from r2/r3 (rank 1 = himself). In a room with a positive late upgrade at RB/WR he waits, and
  the backstop can still bind at the last pick. The quantity that would price him is
  `horizon_replacement`'s floor (observable-only, #48) or an off-by-one replacement (rank
  demand+1; moves every level for QB1−QB2 ≈ 11 here). Both with #50. `replacement_levels`'
  docstring now states the limitation rather than the cancellation claim.
- **The bench.** Starters fixed; the bench is ordered by "nearest to cracking my lineup", and
  on this pool that is receivers: bench picks backstop-OFF went TE6 / RB3 TE1 WR1 QB1 / TE4 QB1
  WR1 → WR5 QB1 / WR6 / WR5 RB1. A hoard the board reinforced became a hoard it does not
  (invariant 5's observable: count rises, the ledger it orders on is flat) — not a balanced
  bench. A bench ruler is #62/#115, open.
- A second QB in 1QB seat 1 at r9 (Love, −11.2): the exhausted-demand pre-draft anchor
  (#165/#155), not this term.
- `depth_exposure`'s direction (the adversary's B-class finding): ≤ 12 at a stacked position,
  0 where vacant, survives at its bounded size.

### Corrections to the published record

- `replacement_levels`' docstring: "rank shrinkage and pool drain cancel exactly … 19 of 19"
  holds for STARTER-FILLING picks only; bench picks move the level (43.6 → 59.3 with seven
  TEs; 43.6 → −2.3 on an RB hoard). Corrected in place.
- #84's ruling ("correctly stranded — in the displacement regime it agrees with the ranking the
  engine already produces"): withdrawn in `test_lineup_marginal_contract`'s docstring and
  CDME_CONTRACTS' H2 appendix; the premise expired with the roster it was measured on.
- The "scaled against the largest gap left in the pool" prose (metric help, legend tooltip,
  design_system, draft_room's ARCHITECTURE): the pricing layer is the identity; corrected.
- `cliff_protection` "fires 73.6% of the time": 35.4% (17/48) on the same states after the
  top six rows stopped being a hoarded position's tail; the constant is as borrowed as before.
- The adversary's `test_the_board_is_not_the_projection_control`, reported FAILING on unfixed
  code: it PASSES on the unfixed engine (zero engine changes between f580c11 and 2f5f304) and
  after the fix; the report belonged to one of the two vacuous earlier drafts its own
  docstring records. An over-correction guard, correctly in class E.

### Second pass — roster shape: measured against the owner's criterion, NOT shipped

Criterion (owner): `WR >= RB > TE` as a tendency over the full roster, a QB ceiling, and a
per-league band derived from bench width, starting requirements, league size and pool depth,
computed on FIELDED load. The band was derived (roster size × the league's fielded-load share
from every roster's optimal lineup, minus the seat's own load; no literal) and it AGREES with
the owner's ordering in all three formats: 1QB `WR 6.1 RB 4.1 TE 2.0 QB 1.75`, SF
`WR 5.7 RB 4.1 QB 3.3 TE 1.9`, the owner's league `WR 5.3 RB 3.6 QB 3.1 TE 1.9` — and it
reproduces the owner's oracle roster's independent depth (WR4 RB3 QB3 TE2) within one at WR.

The mechanism hypothesis ("the bench falls back to raw VOR, favouring TE") is refuted: the
shipped bench regime orders by distance to my lineup and takes RECEIVERS (zero bench TEs in
6/6); the `RB2 < TE3` failures are STARTER picks (a third TE at the second FLEX out-projects the
best receiver by 23, correct by lineup points). Meeting the rule needs two bench RBs over two
bench WRs, and the lineup objective is symmetric between them (coverage 5/8 each); only late
RB scarcity breaks it, and its price is an injury rate (#56).

Arms measured (`run_216_bench_probe.py`, pure-bench regime detected exactly by the raw
optimizer): coverage count 4/6 but TE4-5 in seat 6 and two G9 reversals; horizon
(`waiting_cost`) RB6-9 everywhere; coverage gain-sum strict 2/6; **usage deficits (the derived
band, live) 6/6 strict on raw counts, G1/G3 intact, G9 improved 5/6 — and 3/6 on INDEPENDENT
depth, the same as the shipped fix, because the running backs it adds are workload lotteries
behind other managers' starters (Croskey-Merritt, Mitchell, Marks); and it fails the owner's
own league 3/3 (trades a WR for a TE by usage) where the shipped fix passes 3/3.** Not shipped.
The roster-shape half is not derivable as a price; the one derivable ordering meets the letter
with conditional pieces the rule exempts.

Handcuffs: **no existing term can raise a player's value on the basis of a specific teammate**
(checked in code: `team` is read for identity only; lineup rows carry no team; every
team-specific term is agnostic, positional or a deduction). Identification is derivable and is
now an observable (same NFL team + position + the team's top-projected player owned; RB/QB
only — on WR it labels every NFL WR2). The shipped fix caps nothing and cannot suppress one;
the usage-deficit ordering would whenever RB's deficit trails another position's. The engine
has no trades-enabled input (0 hits; `league_format.py:9`).

Out of sample — the owner's league (no TE slot, 3 flex, SF, 5 bench, 3RR, seat 12): backstop
bound 2 → 0, lineup +119 (+111, +121 in seats 1, 6), ordering passes 3/3, asset ruler won
before and after (no reversal) — and **zero tight ends** against the oracle's two: the engine
fills all three flexes with RBs; at an open flex each position is priced against its own
anchor (TE-rank 8, RB-rank ~39), not the flex's real alternative — not blind to the format,
but not re-anchored either, by the E-guards' design. The QB's own 0.00 bpa is untouched by
any of this. Report: `evidence/roster_shape/FIX_216_fable.md` §10; sets in
`evidence/roster_shape/fix_216/second_pass/`.

**Freeze status: the board is no longer inert for WR and QB and the backstop never binds on
the measured seats — and the fix fails the owner's asset gate in superflex. Three things are
the owner's call, not mine: the #50 exchange rate G9 exposes, (b)'s open half, and whether a
bench ruler (#62/#115) must land before #53. The branch is not merged.**


## #219 — THE EVEN FLEX SPLIT IS FALSE, AND CORRECTING IT NAIVELY IS NOT THE REPAIR

Opus, taking over implementation from Fable at the owner's instruction. Branch
`worktree-agent-ab5e1af412aeb9182`. Evidence: `evidence/roster_shape/flex_share/` (README,
PREREGISTRATION, RESULT, rival_premium_attribution, `drafts/`), instruments
`run_216_flex_share_probe.py` and `run_216_flexshare_draft_probe.py`. This entry lives on the
branch; `ui-authority-pass` carries a pointer to it.

**The finding, and it is solid.** `starter_slot_counts` splits a flex slot's capacity EVENLY
across the positions it admits and defended that in its own docstring with a claim about the
world: those slots "genuinely do get filled by whichever eligible position is best roughly
interchangeably in real drafting behavior". Asked of the data -- field the whole league optimally
out of the whole pool through the existing lineup optimizer, which never looks at a drafter and
so cannot be circular -- the claim is FALSE in every format tried:

| format | FLEX (24 slots) | even split assumes | SUPER_FLEX | assumes |
|---|---|---|---|---|
| 12T_ppr / 12T_ppr_SF | **WR 20, RB 4, TE 0** | 8 / 8 / 8 | **QB 12 of 12** | 3 each |
| owner's league | **TE 18, WR 5, RB 1** | 8 / 8 / 8 | **QB 12 of 12** | 3 each |

Those counts set every replacement RANK, and the rank picks the LEVEL `bpa` subtracts. So the
error lands on every price, in a direction the FORMAT decides -- and ONE derivation explains #216
in BOTH of its observed directions. With a dedicated TE slot the even split inflates TE demand to
1.667 and pushes the rank from TE12 out to TE20: a far worse free alternative, a far lower level,
tight ends priced far too high. That is the 43.5-point bias. Without one, tight ends are
unconsumed inventory that WIN the flexes (TE18 211.6 beats WR44 200.6), yet the even split hands
TE 0.717 of a slot at rank 9 and prices them at nothing while handing RB rank 39 and enough price
to take all three flexes. That is the zero-tight-ends result. **A knob tuned to fix the first
would have made the second worse.** Direction stable at every league size 8-16; the solve costs
0.007s. `SUPER_FLEX_QB_SHARE = 0.85` measures 1.00 at every size -- a hand-set constant standing
in for a derivable quantity, which is what #56 exists to prevent.

**The repair was measured against nine gates pre-registered before it existed, and FAILED four.**
18 drafts, one variable toggled, both anchor caches dropped at every arm boundary:

- **PASS** H4 legality (backstop binds 0 picks, no unfillable starting slot, 18 of 18), H1, H6, H7.
- **FAIL H2's ceiling.** The owner's league goes from ZERO tight ends to 2 / 4 / 1 where his own
  roster carries two -- and one seat with FOUR is what the pre-registration named as the
  over-correction and a failure. The gate was written two-sided on purpose and caught what it was
  written to catch.
- **FAIL H3.** Lineup falls in 4 of 9 seats (-11, -27, -30, -38).
- **FAIL H9.** One new asset reversal (12T_ppr seat 12, +2.9 -> -27.8).
- **FAIL H5 as written**, on an instrument that rewards the defect -- see below.

**Two instrument defects the run exposed, both recorded:**

1. **The ordering verdict preferred a roster with no tight ends -- REPAIRED.** `WR >= RB > TE`
   is trivially satisfied at TE 0, so in the owner's TE-slotless league the unfixed arm scored
   3/3 by drafting none -- against his own roster's two, and against an optimal fielding that
   uses 1.5 per team. He gave the rule for that case himself, before any of this was measured:
   *"with no TE slot, but flex that can field them, the TE act as de-facto WR."*
   `ordering_verdict` now takes the league's `roster_positions` and, when the rulebook says there
   is no dedicated TE slot, adds `(WR + TE) >= RB` beside the original keys rather than replacing
   them (so recorded verdicts stay comparable). 7 tests, 4 of 4 mutations caught. Re-scored: the
   owner's league goes 1/3 -> **3/3** under the reading he described, and the EVEN arm's 3/3 is
   revealed as the artifact it was. **H5's failure there was the instrument; what survives of H5
   is 12T_ppr_SF alone**, where tight ends do have a dedicated slot.
2. **My H3 was one-sided for a two-sided defect.** It required the TE count never to RISE; in
   12T_ppr seat 12 it rose 1 -> 2, toward a band target of 1.90. That is my error at
   pre-registration time, not a result.

**Fable's derived band, the better instrument, says the opposite of the ordering verdict:** the
fielded arm is CLOSER to the band in **7 of 9 seats**, both misses in 12T_ppr_SF.

**Disposition: MEASURED, NOT WIRED**, the standing #84 gives `marginal_lineup_value`.
`fielded_flex_occupancy` and `starter_slot_counts`' measured branch ship as tested code;
`board_flex_share` is the seam and returns None, so every board is byte-identical to the even
split. Three tests pin it: that it returns nothing, that the two consumers ask IT and never the
measurement directly (or the ablation would silently be one arm twice), and that patching it moves
the demand -- stranded code, not dead code.

**Why not just ship the better-looking arm.** The measurement's counterfactual is a league that
fields perfectly; the draft it has to price is one where rivals do not, so it can over-state how
deep a position will really be consumed -- the most plausible reading of the four-tight-end seat.
Choosing between two unvalidated anchors after seeing which flatters the result is the move #56
forbids. **The anchor is #50 and the owner's.**

**POST HOC, unmeasured, for whoever continues:** every seat that got worse is superflex, and
superflex is the one format where the measurement also overrides `SUPER_FLEX_QB_SHARE`. Whether
the non-SUPER_FLEX half passes on its own has NOT been run and would need its own pre-registration
written first.

## #220 — the rival_premium canary is CONDITIONAL on the anchor, and my first diagnosis of it was wrong

`test_the_premium_still_exceeds_one_terms_cap` -- #144's non-vacuity canary, whose docstring says
failing is the point -- goes RED under the fielded anchor and is NOT edited. Attribution, four
arms, one process each (`rival_premium_attribution.md`): even split + displacement reproduces the
pre-change commit exactly at 14.29; measured share + displacement gives 9.25; either arm without
displacement gives 16.21.

**CORRECTION, published before I had read far enough.** My first write-up said
`pick_synthesis.TEAM_SPECIFIC_CAPS` "no longer enumerates the terms it claims to" and filed it as
an unhandled missing-companion defect. **That was wrong and I withdraw it.** Fable handled it
explicitly, in a note attached to the tuple: #216's fourth term is deliberately excluded because
`displacement_adj` is non-positive by construction and so cannot raise the sum the caps bound,
`sum(TEAM_SPECIFIC_CAPS)` therefore remains the correct UPPER bound, and the LOWER bound is now
open -- with both consumers named and their one-sided guards checked. I read one stale
half-sentence three paragraphs ABOVE that note and diagnosed from it without reading on. That is
the fifth confident single-sentence diagnosis on this item to be withdrawn, and it is recorded
rather than deleted for exactly that reason.

**What actually remained, which is much smaller.** One sentence of #144's prose still said the
team-specific terms were "each independently capped", which stopped being true when the fourth
arrived. Repaired in place: the correction now sits with the sentence instead of three paragraphs
below it. Nothing on the value path changes; `sum(TEAM_SPECIFIC_CAPS)` was and remains right.

**The canary is real but conditional.** It is red ONLY under the fielded anchor. With the flex
share stranded behind `board_flex_share` it is green and #144's ramp is exercised exactly as
before. If the owner ever wires the anchor it comes back, and the decision then is: widen the
fixture to states where the ramp is actually stressed, re-derive the saturation point over four
terms, or accept #144's repair as dormant. Not a decision to make while the anchor is unwired,
and not one to make by choosing whichever answer flatters the anchor.

## A process note: an ablation defeats a fingerprinted cache from outside

The first attribution table was WRONG and reported the even-split arm at 9.25 instead of 14.29.
`predraft_replacement_anchor` remembers levels under `anchor_cache_key`, which names every INPUT
they depend on -- precisely why a board never depends on which boards came before it in
production, and precisely why an ablation defeats it: patching a function changes the answer
without changing any input the key names, and the fixture built a board before the patch went on.
Five points of a five-point finding were one board built in the wrong order.
`draft_room.reset_anchor_caches()` exists now and every arm boundary calls it. Any future A/B in
this repository that patches a function inside the board must do the same.

### #222: the engine drafts like a human until round 15, and the chain from constant to outcome is now arithmetic

**THE PHENOMENON.** On the owner's real rulebook the engine takes 32.4% tight ends against twelve
real managers' 15.5%, and 10.3% quarterbacks against 20.0%, in a superflex league. Measured on the
real capture universe on both sides (#201/#204), 312 picks, 1,125s.

**THE ANSWER, in five steps.**

1. **The engine drafts like a human until round 15.** Rounds 1–14: QB 19.0 / RB 26.2 / WR 39.3 /
   **TE 15.5**. Twelve real managers, whole draft: QB 20.0 / RB 27.4 / WR 37.1 / **TE 15.5**. The
   entire divergence is the 144 upside picks, which run TE 52.1%.

2. **Why balanced works.** At a flex slot the phantom is `max(level over admitted positions)`, so
   for a candidate whose reachable slots are held,
   `bpa + displacement_adj = (points − level) + (level − phantom) = points − phantom`. **The
   positional level cancels exactly** and every flex-reachable candidate is compared on raw points
   against one common bar. "One slot, one alternative" doing what its contract says.

3. **Why upside does not.** The upside branch zeroes every team-specific term, which removes
   `displacement_adj`. The level stops cancelling and each position gains exactly
   `phantom − level_pos` — derived differences of this league's own replacement levels, nothing
   fitted, and **recomputed at each board state because the levels drain**: WR **0.00 at every
   state measured**, TE **68.58 opening / 60.03 at pick 100 / 89.14 at pick 150**. (The single
   flat figure first recorded here was the opening-board value; corrected, 21st withdrawal.) Cross-checked three ways: RESIDUAL2's measured −68.58 at
   every seat; `displaced == 217.75` on 103 of 144 tight-end observations; `displacement_adj ==
   0.00` on 160/160 and 139/139 receiver rows at two board states.

4. **Why nobody had stated it.** `UPSIDE_MODE_DEFAULT_ROUND`'s comment says upside mode stops
   "filling a need **or** respecting positional scarcity". It implements the first and keeps the
   second at full weight as the base of `upside_score` (`bpa + 0.5·growth`). **Half the stated
   intent is implemented, and the retained half is the one the dropped half was holding in check.**

5. **Why no contract catches it.** `replacement_levels` has an explicit domain of validity and the
   doctrine rules that VOR must be DECLINED outside it — but the domain is keyed on **the anchor**
   ("does this position still have an unfilled league starter slot?"), never on **the candidate**
   ("is this player a plausible starter?"). At the opening board demand is maximal so the rule
   cannot fire, and 192 of 312 picks in this league are bench/IR/taxi seats priced against a bar
   whose stated meaning is *"the player a team is guaranteed to be able to start"*.

**AND THE COUNTERWEIGHT ONLY DEFERS.** Of the players in `bpa` ranks 1–168 that rounds 1–14
declined — TE 6, RB 2 — **all eight were taken in rounds 15–26. None went undrafted.** The term
changes WHEN a tight end is taken, not WHETHER; composition is conserved because 312 of 481 priced
rows are consumed, so a deferred player is still inside the draft's reach. This is why PHASE4's
"force balanced" did not reproduce the human numbers either (TE 21.8%, not 15.5%): a term that
defers is not a term that fixes.

**NOT A DEFECT FINDING, and deliberately so.** Every citation says the current behaviour follows
the design. `points − level` IS value over replacement; cross-position comparison is explicitly
authorized and evidenced (94–100% agreement against 69–82% for raw points); zeroing team terms is
upside mode's documented behaviour. What is established is LOCATION and MECHANISM, not fault.

**THE OWNER'S QUESTION, now askable against an exact number.** *Should a tight end receive +68.58
points over an otherwise identical receiver for a deep-bench flex seat?* Not "is 32.4% too many" —
that was never the right question. Two sub-questions, neither taken here: is upside mode meant to
drop roster fit ONLY, or roster fit AND the positional anchor; and should the domain of validity be
keyed on the candidate as well as the anchor.

**PINNED.** `test_222_cancellation_and_the_mode_asymmetry.py` — 12 tests over the cancellation
identity, the exact handicap, and the mode asymmetry, mutation-checked 5/5. **Full suite green:
2,772 tests in 729.5s, OK (skipped=1).** Also pins the latent
hazard in `upside_score`'s `row.get("bpa") or 0.0`: safe only because absence in a float column is
`NaN` and `bool(NaN)` is `True`, so a literal `None` there would rank an unpriced player above most
of the priced board.

**THREE WITHDRAWALS this pass**, the third mine. 17th: `narrow_candidates`, a picks-shape fixture
artifact. 18th: RESIDUAL3's zero-rate, an arithmetically unreachable predicate. 19th: *"the
aggregate is set by one subtraction before any pick"* — every number stands, the causal reading
does not, and it was caught by a pre-registered test of my own flagged inference.

**STILL SEPARATE, deliberately not merged.** The 1-vs-15 tight-end allocation across seats is a
roster-DISTRIBUTION phenomenon: under third-round reversal the engine drafts the identical 312
players with identical positional totals while only 32 of 312 land on the same seat. It cannot be
the cause of the aggregate, and nothing above depends on it.

**FIVE DOCTRINE CLAUSES** added to the engine-measurement skill this pass: behavioural inputs need
schema validation, not value validation; a rate of exactly zero needs its detector's firing
condition shown reachable; never name a production column from memory; a board ROW count is not a
PRICED count; and an empty roster is not a neutral roster — it switches half the valuation off.

#### #222 addendum — the semantic question, answered from the contract

**Is upside mode meant to remove roster-fit pressure only, or roster fit AND positional scarcity?**
**The contract answers it: roster fit only, and the positional anchor is retained by design.**
The founding architecture (module docstring, commit `44ef3c6`) splits the score on
team-agnostic vs team-specific and defines `universal_value` as *"what any manager at the draft
would compute — **league-wide scarcity**, market read, …"*. Scarcity is in the team-agnostic half
by definition, so upside mode retaining it is the architecture working. Corroborated by
`CDME_CONTRACTS` measuring upside against *"pure-`bpa` order"* and ruling `UPSIDE_GROWTH_WEIGHT`
closed, by `growth_signal` being called *"upside mode's whole distinguishing output"*, by a pinned
identity in `test_decision_qualifiers`, and by the repo's own phrase *"upside mode has no positional
**gate**"* — the gate being `need_bonus` (#87), never the anchor. `git log -S` shows `upside_score`
and `UPSIDE_GROWTH_WEIGHT` touched by exactly one commit ever: the founding engine.

**20th withdrawal, mine.** `FINDING_upside_intent_inversion.md`'s framing — *"half the stated
intent implemented, the other half inverted"* — is withdrawn. Its facts stand; the framing weighed
one uncommitted comment against the founding architecture, four contract statements and a pinned
test. The code is not violating an intent; `UPSIDE_MODE_DEFAULT_ROUND`'s comment describes the code
wrongly.

**THE MISSING DESIGN DECISION, and it is narrower and sharper.** `displacement_adj` is classified
two ways in the same docstring: as *"the FOURTH team-specific term"* — which puts it under upside
mode's zeroing rule — and as a correction to the universal anchor, *"only ever removes credit the
league anchor gave for a slot the roster cannot offer — the reason `TEAM_SPECIFIC_CAPS` remains an
upper bound … with **no fourth cap**"* — which is why it alone is uncapped. **The cap exemption is
granted on the second reading; the exposure to upside's rule follows from the first, and nothing
reconciles them.** The founding commit records `need_bonus` as *"the ONLY team-specific term,
capped low enough to nudge a close call but never flip a large universal-value gap"* — so *"zero
every team-specific term"* was authored when that class held one capped nudge. The class grew to
four across #139 and #216; the fourth is by its own docstring not a nudge; the rule was never
re-examined.

**Two invariants are stale and this is where it shows.** Invariant 1 still states the three-term
`team_acquisition_value` identity, annotating #139's expansion and missing #216's, while
`draft_room.py`'s own docstring carries `+ displacement_adj`. Invariant 4 — *"none of the **three**
team-specific terms may flip a large `universal_value` gap; each is capped"* — names a class that
now has four members, the fourth uncapped by design and existing precisely because *"no bounded
nudge could span the 43-60 point bias"*. The capping mechanism still bounds what it was built to
bound; the invariant's statement is false of the class it names. Restating, not enforcing, is what
that needs — #216's derivation for having no cap is on the record and is not reopened here.

#### #222 addendum — the narrow ablation, and both candidate repairs rejected

**FORK B.** Pre-registered at `086939f`, run at `11fdd59`, control 168/168, no engine source
modified. Upside mode keeping `displacement_adj` and nothing else: TE rounds 15–26 fell 52.1% →
29.9% and **all four pre-registered guardrails breached** — whole-draft WR 42.0% (bar < 40.0),
largest pile 17 (≤12), seats holding ≥12 at one position **11** (≤3), thin pairs 4 (≤0).

**What the arm isolates, which is the yield.** Restoring the counterweight alone reproduces
force-balanced's positional composition almost exactly (WR 42.0 vs 42.0, TE within 0.3). The only
difference between those arms is `need_bonus`, `eligibility_bonus`, `depth_exposure` — so those
three contribute **essentially nothing to composition**, and `displacement_adj` carries the whole
mode-boundary effect on its own.

**A second matched pair.** The three terms carry the SHAPE protection instead: without them, seats
with a 12-plus pile go 3 → 11 and per-seat TE reaches 17. That is **#87's positional-gate ruling
confirmed from the opposite direction** — leaving `need_bonus` out while restoring a large
positional push reproduces the failure mode that removing it produced. `displacement_adj` and
`need_bonus` are a pair, as `bpa` and `displacement_adj` are; restoring either member of either
pair alone makes the engine worse.

**Both candidate repairs are now measured and rejected**, and no configuration tested reaches the
human distribution: humans take 15.5% TE against AUTO 32.4, force-balanced 21.8, narrow 22.1, and
both roster-aware arms overshoot WR to 42.0 against a human 37.1. **The TE excess is not removable
by restoring roster awareness in the back half.** AUTO's TE overshoot and the roster-aware arms'
WR overshoot are two faces of one pricing fact; the mode boundary chooses which. The live question
is #229's — cross-position comparability below starter depth — not the mode switch.

## #148 NARROWED — the whole in-repo chain is sign-capable, and it still produced 499 unsigned rows

`term_lifetimes.UNSIGNED_TREND` recorded the missing sign's cause as a hypothesis, stated as one
because it "cannot be confirmed from here." Half of it can be, and now is. #148 does not close;
what changes is that it is blocked on a measured finding rather than an untested guess.

Two candidates could each produce the observed all-positive column: the instrument dropping a
`-` that WAS present, or no `-` ever being present. They have different remedies — the first is
an in-repo bug, re-parseable today from PDFs the owner still holds. **The first is falsified,
twice over, and a third fact rules out the remaining in-repo path.**

- **The parser was sign-capable AT INGEST, not merely today.** `_KTC_ROW_RE` captures the trend
  as `(-?\d+)`; `parse_keeptradecut_pdf` converts with a bare `int()`. Exactly one commit has
  ever touched that pattern, and the identical regex sits at **both** commits that produced the
  committed CSV (`32e6991`, `98e2df1`). No window exists in which a sign-blind parser read these
  PDFs.
- **pypdf round-trips the minus** at the version the parser uses, through a hand-assembled PDF
  (`ktc_sign_probe.py`; reportlab is absent here, so the content stream is written out in the
  probe and nothing is trusted to a generator). Prediction pre-registered in its own docstring,
  with its falsifier, before running.
- **No row was silently skipped.** The parser anchors the trend at `$` and advances
  `expected_rank` only on an accepted row, so a single unmatched tail cascades every later row
  into rejection. The CSV holds 499 rows at ranks 1–499, consecutive, no gaps; the one absent
  row (rank 500) is ATTRIBUTION.md's documented digit-splitting ambiguity. Every row ended in a
  bare integer in the extracted text.

**How far from a real trend this is, quantified rather than asserted.** 471 positive, 28 zero,
**0 negative**. At an even split that is `P = 2^-471 ≈ 10^-142`; for the column to be plausible
at even 1-in-20, KTC's 30-day market would have to have risen for **≥99.37%** of assets — fewer
than 3 expected decliners in 471. A magnitude with its direction stripped, not a rising market.

**What stays a guess** is the vendor's own rendering (ATTRIBUTION.md suspects a coloured arrow
glyph; KTC's API is 403 from here). What is established is that the character never reached the
extracted text and **nothing in this repo removed it**.

**The regression this invites, guarded.** `(-?\d+)` → `(\d+)` reads as tidying, breaks no
existing test — no committed fixture carries a negative trend — and would silently discard the
sign on the first re-scrape that finally carries one, restoring the defect with no failure
anywhere. `TheTrendSignSurvivesTheParserTests` pins the capability and the current
all-non-negative state *together*; the second fails the day a signed capture lands, which is the
right moment to retire the record rather than loosen the assertion. Mutation-checked 3/3.

Result at `evidence/roster_shape/ff_rulebook/RESULT_148_the_parser_is_exonerated.md`.
Classification unchanged: KNOWN-OPEN-ACCEPTABLE, blocker now confirmed external.

## THE REGISTER LAGGED THE REPAIRS — six items were closed and still filed open

Found by nearly redoing closed work. #187 (`denial_value` emits an unmeasured 0.0 while the
tooltip promises it was measured) was picked off the open list; the first grep found the repair
already shipped — the derived `DENIAL_MEASURED` / `DENIAL_NO_INTERVENING_RIVAL` /
`DENIAL_NO_RIVAL_PRICED` vocabulary, `denial_value = None` where nothing was measured, and a
`test_denial_basis.py` that additionally forbids reconstructing the basis from
`denial_value == 0`. Same for #190 and #207. All green. All filed open.

**Nothing fails when this happens.** The item reads open, the investigation starts, and the only
thing that stops it is a grep landing on the repair.

**Screened all 52 open items** for a test naming them: **30 have one.** That is a screen, not a
verdict — and the counterexample was made this session. `TheTrendSignSurvivesTheParserTests`
names #148 and is green, and **#148 is open and stays open**: the test is a *guard on an open
condition*, pinning the export as all-non-negative so it fails the day a signed capture lands.
A green test naming an item means "repaired and pinned" OR "open and guarded", and only the
item's own verdict separates them.

**Flipped to done — six, each confirmed three ways** (repair visible in source, dedicated test
green, verdict in the register or the task's own title): **#185** (superflex QB rows say
`startable_floor`, confirmed at `735c972` at line 6096 above), **#187**, **#190**, **#192** (also
independently confirmed by #180 closing as ALREADY REPAIRED *by* #192's work), **#193**, **#207**.
120 tests green across the verification runs.

**NOT flipped: #208, #209, #210, #211** — each has a green dedicated test and **no recorded
verdict anywhere in this register**; their status lives only in task titles and evidence files.
Two are supply gaps, the shape most likely to be open-with-a-guard. They need adjudication
against their own evidence, not a status flip on a grep.

**The structural defect, in this repo's own terms.** Completion state lives in three places that
can disagree — the task status field, the task's title prose, and this file's verdict sections —
and for items above ~205 the section here was never written, leaving title prose as the only
record. Three sources of truth for one fact is what #126 exists to forbid.

**The operating rule that follows:** before opening an investigation into any item filed open,
grep for its repair first. One command; it would have saved this session an entire investigation.

Detail at `evidence/roster_shape/ff_rulebook/FINDING_the_register_lagged_the_repairs.md`.

## #212 IS THE PARENT — B2, #209 and #210 are three populations of ONE mechanism (23rd correction, mine)

B2's supply verdict stands: **no ingested source prices these quarterbacks**, remedy is a source,
not a wire. Two things in how I described it were wrong, and the second matters more.

**1. The mechanism.** I wrote that Sleeper "answers and says zero." It does not. Measured through
`season_projections_from_capture()` against the real capture, all eight named backups have an
entry and every entry holds **one key** — `adp_dd_ppr`, the "undrafted" sentinel (`18000.0`):

```
Haener / Bennett / O'Connell / Clifford / Bagent / DeVito / Milton / Hartman
ADP-only 8 | stat-bearing 0 | no entry 0
```

ADP says where the market drafted a player, not what he is projected to **do**. There is no stat
line, so the scoring path reaches him and finds no quantity — hence
`bpa_source='no_priceable_input'`. **"Says zero" and "has no stat line" are precisely the
distinction the absence contract exists to enforce**, and I conflated them in a finding whose
whole subject is absence. Population-wide: of 474 QBs, 355 carry an entry and **321 (90.4%) are
ADP-only**; 34 carry stats.

**2. B2 is not a separate finding.** `test_priceable_projection_count.py` had already measured
and named this: of 5,346 capture entries, **4,506 are ADP-only**, so the priceable count is 840
— a 6.4x coverage overstatement — and it already folds in #209 (Jake Haener, `tav=None`, entry
`{'adp_dd_ppr': 18000.0}`) and #210 (1,817 ADP-only entries are IDP: LB 852, DB 723, DL 242).
B2's quarterbacks are that same population, and **Haener is the worked example in both.**

| item | population | mechanism |
|---|---|---|
| #209 | one QB in 14T_standard | ADP-only entry |
| #210 | HEAVY_IDP's 1,817 defenders | ADP-only entry |
| B2 | the league pool's deep QBs | ADP-only entry |
| **#212** | **all 4,506** | **the mechanism itself** |

**What survives unchanged:** the vendor-baseline half, measured through production's own
`merge_player` and independent of the capture — 39 of 42 priced QBs carry `proj_3yr` (92.9%)
versus 0 of 113 unpriced (0.0%), and the named backups have no baseline row at all. Neither
source prices them. #147 is still NOT the binding constraint.

**Adjudicating the four items I declined to flip on a grep, now that their verdicts are read:**

- **#209 — CLOSED.** Explained by #212; the absence contract worked (`no_priceable_input`). Its
  own test records a correction: the pre-registered falsifier said the scoring path had not
  reached him, and was wrong.
- **#210 — EXPLAINED, still OPEN as supply.** HEAVY_IDP did not shrink because Sleeper supplies
  those players without stats, not because it lacks them. Mechanism answered; the input gap is
  the #49 family and stays open.
- **#211 — KNOWN-OPEN-ACCEPTABLE, pinned.** Its own tests say it plainly: "No finding changes.
  This is a reported line, not a verdict." `starter_value` sums an asset LEVEL across a starting
  lineup and so ranks positional breadth, not roster quality — a reported number, not a
  selection authority.
- **#208 — CLOSED.** The #205 instrument now carries mutation-checked guards against both of its
  first draft's defects (a control that took 24 consecutive QBs; a ruler that was the engine's
  own objective). #177's harness had neither tests nor a commit, so its result stays undefended.

**The generalized rule.** The register-lag finding said: before investigating an item filed open,
grep for its repair. B2 was never filed as an item, which is how it slipped that rule. So:
**before investigating a mechanism, grep for the mechanism** — not just for its number.

## #224 PINNED — and the mutation pass found a hole in mutation testing itself

### #224: two `bench_capacity` quantities, neither wrong

The register said "names two different quantities" and parked it. What they are:

| | `lineup_optimizer.bench_capacity(roster_positions)` | `draft_room.estimated_bench_demand`'s local |
|---|---|---|
| what | BN slots this league gives **each team** | further **picks** the draft can still spend on bench |
| unit / scope | slots, per-team | picks, league-wide |
| type | `int` | `float` |
| in time | **static** — takes no `picks`, so it cannot change mid-draft | **draining** — falls to 0.0 as picks land |
| on the fixture | **3** | **36.0** at the opening board |

**No live crossed wire:** `draft_room` imports `lineup_optimizer as lo`, so the function is only
reachable as `lo.bench_capacity` and the local never shadows it. Both correct where they stand;
renaming either is cosmetic and touches constrained source, so neither was renamed.

Built instead: `test_224_bench_capacity_vocabulary.py`, **8 tests, mutation-checked 6/6**,
pinning the two properties that make the tempting deduplication impossible to do quietly — the
magnitudes differ, and only the demand quantity responds to the draft.

Two things found on the way: **`estimated_bench_demand` had ZERO direct tests**, and its
`max(…, 0.0)` floor is **load-bearing and reachable** — at 64+ picks the raw difference goes to
−4, −8, −12 (capacity exhausts while another position's starters are still owed), and without
the floor every position's share goes negative, since shares are `budget × appetite / total`.

### The hole: a stale `.pyc` served mutated code after the source was restored

The first pass reported M2 (drop the floor) as SURVIVED — **a vacuous test of mine**, asserting
through the test file's own `_bench_budget` helper, which re-implements the floor.

Repairing it exposed worse. `estimated_bench_demand` returned a total of **1.0** where
`bench_capacity` provably floors to **0.0**, and `0.0 × anything` cannot be `0.97`. Four checks
said the source was innocent: `git status` clean, `git diff` empty, the line read `max(…, 0.0)`,
and `inspect.getsourcelines` **on the bound function** showed the correct body. Deleting
`__pycache__` produced `0.0` immediately.

**Mechanism.** CPython validates a `.pyc` against the source's **mtime and size**. The mutation
was `0.0` → `1.0` — byte-identical in length — and mutate/run/restore completed inside one mtime
second, so the cache still looked valid and every later import got the **mutant**. `inspect`
reads the source file, not the executing bytecode, so it cannot see this.

**Why it matters beyond one test.** It is aimed at the instrument this project relies on to know
its tests are not vacuous: a corrupted pass reports whatever the stale cache holds — a mutation
reading as "caught" when the tests never saw it, or "survived" when they did. Every same-length
mutation in this repo's history is in scope (`>`/`<`, `+`/`-`, `0.0`/`1.0`, identifier swaps).

**Fix, now doctrine in the engine-measurement skill:** run every mutation arm under
`PYTHONDONTWRITEBYTECODE=1`, control included. The pass was redone that way from scratch; M4
(floor at 1.0) was confirmed a **genuine** survivor rather than a cache artifact, and a test
added for it — a finished draft must report exactly `0.0`, which is #59's whole point.

**Generalized rule:** when a measured number contradicts arithmetic you can do on paper, suspect
the instrument before the arithmetic. Re-deriving the same wrong number from the same poisoned
process confirms nothing.

Detail at `evidence/roster_shape/ff_rulebook/FINDING_224_two_bench_capacities_and_a_poisoned_cache.md`.

## #122 CONFIRMED — the imputed appetite is a THREE-way collapse, and #62 is cleanly closed

Measured on one league (`["QB","RB","RB","WR","WR","TE","K","BN","BN","BN"]`, 12 teams), one
pool, three K scenarios:

| K's situation | returned |
|---|---|
| deep pool — decay **measurable** | `1.0359…` |
| 6-player pool — too short to read, **imputed** | `8.0526…` |
| **no K rows at all** — nothing to read, imputed | `8.0526…` |
| control: K not in `roster_positions` at all | `0.0` |

**#62 is genuinely closed and its docstring promise holds.** The promise — a position whose pool
cannot reach 2x starter demand "does NOT get 0.0 ... that would assert 'this position is never
benched', which is a claim, not an absence" — is kept: the short pool returns `8.05`. The `0.0`s
appear only for positions the league does not roster, where zero bench appetite is a **real
measured zero**. Correct, and not to be changed.

**#122 is real and worse than one line suggests.** The imputed `8.05` comes back in exactly the
same shape as the measured `1.0359` — a bare float — so a consumer cannot separate (1) measured,
(2) imputed from six players of evidence, (3) imputed from none. States 2 and 3 are not merely
the same shape, they are **the same number**: the mean rate is supplied identically whether the
position had partial evidence or no evidence at all. Here the imputed value is ~**8x** the
measured one, so the collapse is not cosmetic.

Same family as #166 (`horizon_basis`), #174 (`depth_basis`), #187 (`denial_basis`), #207
(`rival_premium_basis`): a number right to produce, produced without saying what kind it is.

**Repair specified, deliberately NOT built.** The established pattern is a companion basis with a
derived vocabulary (#126) — here `appetite_basis` over at least `measured` /
`imputed_short_pool` / `imputed_no_pool` / `not_rostered`. **#188's open question, whether the
vocabulary needs a fifth "bounded/partial" state, lands exactly on states 2 vs 3** — this
measurement makes that abstract question concrete.

Not built because it changes `draft_room.py` beyond prose while the #222 constraint on that file
is in force, and it widens a contract two callers read (`estimated_bench_demand`,
`horizon_replacement`). #122 is KNOWN-OPEN-ACCEPTABLE, nothing is failing, and no measurement in
flight depends on it — so the owner gets a specified repair rather than a boundary taken down on
my judgment.

**NOT concluded:** whether the mean rate is the right *value*. That is the docstring's own
reserved question and #56 territory. This finding is about **disclosure** only — the number's
provenance, not its size.

Detail at `evidence/roster_shape/ff_rulebook/FINDING_122_the_imputed_appetite_is_indistinguishable.md`.

## #153 SHARPENED — two clamps, not one, and the register names the wrong one

`need_bonus = round(min(4.0*dedicated_needed + 1.0*min(flex_remaining, 1), NEED_BONUS_MAX), 2)`.

**Clamp A — `min(flex_remaining, 1)`.** With `dedicated_needed = 0`: flex_remaining of 1, 1.5, 2,
3 and 5 all return **1.00**. **This is the 4WR case** — a 4WR format gives WR four dedicated slots
*plus* a large share of the FLEX slots, so `flex_remaining` routinely exceeds 1 and every roster
above that threshold is priced identically. It is a clamp on the flex **share**, not the cap.

**Clamp B — `NEED_BONUS_MAX = 12.0`.** With `flex_remaining = 0`: dedicated_needed of 3, 4, 5 and
8 all return **12.00**. The register does not mention this one, and a 4WR roster reaches
`dedicated_needed = 4` from empty — so it saturates in round one of exactly the format #153 names.

**The qualification that resolves the item.** `estimated_bench_demand`'s docstring says "the whole
reachable need_bonus is 8.67 and its cap never binds (NEED_BONUS_MAX at 1e9 is pick-for-pick
identical)." That is **not** contradicted here, because the two statements are about different
things: arithmetically the cap binds (`need_bonus(3, 0) = 12.00` exactly), while behaviourally
raising it changed no pick. Both are true — the states collapse, and the other terms dominate by
enough that un-collapsing them moves nothing in the arms measured. **That is why
KNOWN-OPEN-ACCEPTABLE is the right classification**: a real loss of distinction with measured-zero
decision authority, which is #55's OBSERVABLE-vs-AUTHORITY line in different dress.

**NOT established, and not to be assumed:** whether that ablation covered `4WR_TE_PREMIUM`. The
8.67 figure is quoted while discussing a **one-TE league**, and `4.0x2 + 1.0x0.67 = 8.67` — i.e.
`dedicated_needed = 2`, a two-slot position. A 4WR format reaches 4 and saturates where that
measurement never went. So the cap's inertness is **evidenced for the arms measured and assumed
for 4WR**, which is the arm #153 exists to question. Settling it is one battery arm — the `1e9`
ablation re-run on `4WR_TE_PREMIUM` — not a full battery.

**No constant changed and none should be.** Widening either clamp is calibration against an
observed regime, which #56 forbids without a derivation. The open question is a measurement, not
a tuning.

**Prose note (#182 family):** "its cap never binds" is true behaviourally and false
arithmetically, and the sentence does not say which. A reader checking the formula will find the
cap binding at `dedicated_needed >= 3` and reasonably call the comment stale. One qualifying
clause when that file is next open for prose — not touched here, `draft_room.py` being under the
#222 constraint.

Detail at `evidence/roster_shape/ff_rulebook/FINDING_153_two_clamps_not_one.md`.

### Suite gate for this stretch

**2,783 tests, 890.6s, OK (skipped=1), 0 failures, 0 errors** — run clean under
`PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared first, after the stale-bytecode hazard
above made the earlier run untrustworthy.

The count checks out rather than merely looking plausible: **2,772 + 11**, being the 8 new
`test_224_bench_capacity_vocabulary` tests and the 3 new `TheTrendSignSurvivesTheParserTests`.

And the run describes the **current** code: every commit since it launched (`68a93df..HEAD`)
touches markdown only — `git diff --name-only` returns no `.py` at all. The first attempt at this
suite was discarded rather than quoted, because it was launched across a tree that was being
mutated underneath it.

## #122 WITHDRAWN IN FULL (24th correction, mine) — the repair was already built

**The #122 section above is wrong and should not be cited.**
`draft_room.positional_bench_appetite_basis()` exists, ships the derived vocabulary
`APPETITE_MEASURED` / `APPETITE_IMPUTED` / `APPETITE_UNAVAILABLE`, is read by `pick_synthesis`
(`HORIZON_BASIS_MEASURED = dr.APPETITE_MEASURED`), and is pinned by tests in `test_draft_horizon`
and `test_draft_room`. Measured directly:

```
K DEEP  (measurable)   appetite 1.0360   basis 'measured'
K SHORT (6 players)    appetite 8.0527   basis 'imputed'
K EMPTY (no rows)      appetite 8.0527   basis 'imputed'
```

**The sub-claim is wrong too.** I called short-pool vs empty-pool a third collapsed state. It is
not a state: the basis names the **rule applied** ("no evidence this one decays differently from
average"), and that rule is identical whether the evidence was six players or none — so the same
token and the same number are **correct**, not a loss of information. Two epistemic states exist
here, measurable and not, and the basis separates them exactly.

The existing docstring already states everything I thought I was finding, including an
adversarial bound I never computed: truncating only RB below 2x demand moved it from 20.29
measured to 3.37 imputed (−83%), and its bench-capacity share from 63.5% to 22.5%; it names the
silent window as rounds 3–15.

**Root cause, and it is not subtle.** The rule *"before investigating a mechanism, grep for the
mechanism, not just its number"* was written into this register an hour earlier, by me, after B2.
I then investigated #122 by grepping `#122` and `bench_capacity`, never `appetite_basis` — and
wrote "the established pattern is a companion basis, applied four times over" without checking
whether the companion existed here. Enumerating the pattern's four other instances and still not
looking for the fifth makes this worse, not better.

**What survives:** only the #62 half. Not-rostered returns `0.0` (a real measured zero — you
cannot bench a position you cannot start) while a short pool returns the imputed value, so #62's
docstring promise holds. Unaffected, and still worth having measured.

**#122 is therefore CLOSED, not open** — and the register's own description of it ("the
per-position mean_rate imputation is unmarked") was already stale before I started.

## #188 DESIGN EVIDENCE: the "bounded/partial" state is not missing — it was invented FIVE times

#188 records the absence vocabulary as needing a fifth state, "bounded/partial", and two places
in the code point at it in those words. **The framing is inverted.** A complete AST derivation
(all 144 module-level UPPER string constants in non-test modules, grouped into families, each
candidate's definition then read) finds the state already implemented independently five times:

| module | token | value | declares |
|---|---|---|---|
| `lineup_optimizer` | `BYE_PARTIAL` | `'partial'` | byes unknown → the week's numbers are **a FLOOR, not the cost** |
| `lineup_optimizer` | `DISPLACEMENT_ROSTER_PARTIAL` | `'roster_partially_priced'` | roster only partly priced |
| `player_universe` | `RULE_FLOOR` | `'rule_floor'` | a rulebook **floor**, not a point estimate |
| `draft_room` | `REPLACEMENT_BASIS_POOL_TRUNCATED` | `'pool_truncated'` | pool ran out before the anchor |
| `provider_meter` | `TRUNCATED` | `'truncated'` | output cut short |

Excluded after checking rather than pattern-matched in: `REPLACEMENT_BASIS_STARTABLE_FLOOR`
names **which anchor** was used, not that the value is a bound; `INCOMPLETE_PLAYER_PROFILE` is a
UI display string.

**Every independent author reached for the same semantics** — some evidence existed, the
computation ran on it, the result is a bound rather than the quantity — and invented a different
**name**. So the owner's decision is not "should a fifth state exist" (the corpus settled that
empirically) but **"which name becomes shared, and which vocabularies adopt it"**: a refactor
rather than a design commitment.

**#126's landmine at the vocabulary layer**, and the same shape as the five separate constants
all equal to `'measured'` (`APPETITE_`/`DENIAL_`/`EXPOSURE_`/`DISPLACEMENT_`/`BYE_MEASURED` —
verified identical, five definition sites, nothing enforcing they stay so).

**Method note.** A first scan used a hint regex of guessed keywords, returned 25 tokens, and
under-counted — it caught `APPETITE_MEASURED` and missed `APPETITE_IMPUTED`/`UNAVAILABLE`. It
was discarded, not reported. This was written straight after my #122 finding was withdrawn in
full for asserting a missing repair that existed; #188's own premise is a third instance of the
same shape. **In a codebase this disciplined, "X is missing" is the claim most likely to be
wrong, and cheap to check before it is expensive to publish.**

Detail at `evidence/roster_shape/ff_rulebook/FINDING_188_the_fifth_state_exists_five_times.md`.

### #126 at the vocabulary layer, guarded: five constants, one word

Five modules each define their own "this number was really measured" token and all five are the
string `'measured'` — `draft_room.APPETITE_MEASURED`, `draft_strategy.DENIAL_MEASURED`,
`lineup_optimizer.EXPOSURE_MEASURED` / `DISPLACEMENT_MEASURED` / `BYE_MEASURED`. That they agree
is a coincidence of five separate typings, not a property anything enforced.

**The hazard is concrete, not hypothetical.** `pick_synthesis` binds
`HORIZON_BASIS_MEASURED = dr.APPETITE_MEASURED` and reasons with it about a *different*
quantity's basis. The day one module renames its token, every cross-quantity comparison silently
starts answering "these bases differ" for two numbers that were both measured. Nothing fails.

`test_basis_vocabulary_is_one_word.py` pins it — **3 tests, mutation-checked 3/3** (drift one
value, drift another, rename a token out of the population). The set is **derived by suffix at
runtime**, so a sixth `*_MEASURED` token joins the invariant automatically rather than sitting
outside a hand-list. A non-vacuity test asserts the population is non-empty and spans all three
modules first, so a rename cannot make the invariant pass by emptying it.

**Deliberately does NOT merge the five into one constant.** Whether the vocabulary gets a single
shared home is #188's live question, and collapsing them here would decide it. This makes drift
loud and leaves the naming decision where it belongs.

## #182 (prose audit): the README stated the TAV identity with four terms and claimed all were bounded

The front-door document was three days behind the engine, and the gap was substantive rather
than cosmetic.

**What it said** (quoting the README **as it read** before this repair, not a live claim).
TAV = `universal_value + need_bonus + eligibility_bonus + depth_exposure`, and
"**All four terms** are unit-matched to the same bpa-anchored scale and individually **bounded**
… specifically so neither roster-fit term can override a genuine talent gap on its own."

**What the code says.** Five terms — the identity in `draft_room.py`'s own module docstring adds
`+ displacement_adj` — and the fifth is **uncapped by design**. It is non-positive by
construction, so it can only remove credit, which is exactly why it needs no cap and is absent
from `TEAM_SPECIFIC_CAPS`; it exists because *no bounded nudge could span* the 43–60 point bias
a surplus tight end was handed in a one-TE league.

**So the README's reassurance was false in the direction that matters**: it told a reader no
roster-fit term can override a talent gap, while the term added precisely to move large gaps
went unmentioned. This is the same defect corrected in `CDME_CONTRACTS.md` earlier this session
(Invariant 1's three-term identity, and Invariant 4 split into 4a/4b) — the README simply never
got the same pass.

**Repaired** to state the five-term identity and the two classes explicitly, mirroring 4a/4b so
the two documents use one vocabulary (#126) and naming `CDME_CONTRACTS.md` as the authority. A
second passage describing the historical eligibility-bonus unit defect said "a sum whose other
**two** terms live on a different scale" — accurate when written, a false present-tense arity
now; it is re-scoped to "at that time" with a note that TAV has since grown to five.

Documentation only; no code touched, and no test reads README.md (checked).

### #182 continued: the identity is one fact with nine homes, and two of them were load-bearing-stale

Grepping every `.md` for the TAV identity found it stated **nine times**. Most are legitimate
historical narrative — a measurement or a landing record stating the arity correct at its own
date — which Invariant 1 explicitly permits ("every earlier measurement in this document that
states the two- or three-term form was correct when taken and is marked where it is
load-bearing"). Two were not covered by that:

- **`ARCHITECTURE_AUDIT.md:266`** stated the three-term form **and cited `CDME_CONTRACTS.md §1`
  as its authority**. §1 now states five terms, so the citation misrepresented its source — the
  sharpest kind of prose rot, because a reader checking the reference finds a different claim.
  Scoped to "§1 **as it read when this was written**", with the later terms named and a note
  that the surrounding reasoning is unaffected (it concerns whether the browser can see the
  additive structure at all, not the arity).
- **`CDME_CONTRACTS.md:1680`** opened "CDME's **central commitment** is …" with the three-term
  form — normative phrasing, present tense, unmarked, immediately above a three-column
  measurement table. Marked as the form that measurement was taken against, pointing at §1 for
  the live invariant.

Left alone deliberately: `CDME_CONTRACTS.md:4797` and `:7232` (both inside dated measurement
narratives, past tense), and `ENGINE_WIRING_PASS.md:223` ("the term landed as ruled" — a record
of #139's landing, correct at that moment).

**The structural point, which is #126 again:** one fact, nine homes, and no mechanism to notice
when the fact changes. Invariant 1 was corrected in #222 and eight other statements did not
move; two of them drifted into misstatement. A derived check — the identity's arity read from
`draft_room.py` and compared against every doc that states it — would make this self-policing,
and is the same shape as the `'measured'` guard added above. Not built here; recorded as the
natural next step for #182.

### #182 made self-policing for the identity: `test_tav_identity_is_stated_once.py`

The natural next step named above is now built. The expected term list is **parsed out of
`draft_room.py`'s own module docstring at runtime** (#126 — derived, never hand-listed), and
every statement of the identity across every `.md` must either match it or carry a scope marker
saying which moment it describes.

**The rule is deliberately not "every statement must list five terms."** Rewriting a dated
measurement to match the present is worse than leaving it, and Invariant 1 already says so. What
the test forbids is an **unscoped** statement of a superseded arity — a present-tense claim that
is no longer true, with nothing telling the reader it is history.

**It failed on its first run, correctly, and on me.** Four unscoped mismatches: the two
`CDME_CONTRACTS` passages I had judged "left alone deliberately, dated measurement narratives"
— right about their nature, wrong that they needed no marker — and my own register quotation of
the README's superseded text. All four now carry markers.

**It also found a defect in itself.** The first matcher compared markers against raw text, and
these documents are hard-wrapped, so `**as\nit stood**` straddled a line break and a correctly
marked statement was reported as a misstatement. Fixed by whitespace-normalising the window
before matching — a marker split by a line break is still a marker.

**Mutation-checked 2/2**, and the first mutation is the scenario this exists for: adding a sixth
term to the identity in `draft_room.py` now fails everywhere the docs still say five. That is
precisely the notification that was missing both times the sum actually grew (#139, #216).
Non-vacuity is asserted first — if the regex ever stops matching, the population test fails
rather than every assertion passing trivially.
