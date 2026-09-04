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
