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
