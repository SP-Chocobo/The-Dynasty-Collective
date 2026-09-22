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

### AMENDMENT (`#285`/`#289`, owner-ruled this session): THE BOUND WAS UNDERSTATED, AND THE ESCAPE HATCH IS CLOSED

**The ruling is UNCHANGED — documented, not repaired, does not hold the freeze, repair is Phase
3.** What changes is the size of the bound this entry commits to, and one of its two defences.

**1. "THE COST IS MEASURED AND SMALL" was understated.** That line rests on `#177`: −1.83% to
−1.97% on one arm of eight. The smoke-seat field measures larger, and the `cdme` half is
**not** confounded by the `adp` mis-specification `#288` records, because `need_first` and
`points_need` never read an ADP table at all:

| arm | ruler | vs `need_first` | vs `points_need` | vs `adp` |
|---|---|---|---|---|
| `12T_ppr_SF` | `cdme` | 2/12, −10.27% (t −2.58) | 1/12, −17.50% (t −4.47) | 11/12, +20.02% |
| `10T_ppr_SF` | `cdme` | **0/10, −26.91% (t −6.92)** | **0/10, −30.39% (t −6.60)** | 6/10, +11.50% |
| `12T_ppr_SF` | `points` | 11/12, +1.66% | 9/12, +1.19% | 4/12, −1.13% (t −2.74) |
| `10T_ppr_SF` | `points` | 6/10, −0.19% | 5/10, −0.06% | 0/10, −2.42% (t −5.86) |

**The engine loses its own objective to the projection-led styles in superflex, decisively and
cleanly** — while beating `adp` on that same ruler. On `points` the picture is milder: it beats
or ties both projection-led styles and loses only to `adp`, which is the mis-specified control.

The shape is coherent with this entry's own mechanism. The projection-led styles open QB at
44–50% in superflex; the engine opens QB at 8% (`12T_ppr_SF`) and 60% (`10T_ppr_SF`). The
startable floor sets the superflex QB level from the cliff without consulting demand, so the
engine underprices QBs as ASSETS while still fielding a comparable lineup. **Asset total suffers,
starting lineup does not.** That is exactly the defect described above, now measured on a field
rather than one arm.

**2. THE `#206` DEPENDENCY NO LONGER OFFERS THIS ITEM COVER.** The clause above says `#177`'s
deficit may be partly a simulation artifact because the simulated chairs "produce twelve straight
QBs in round one." `#285` recorded round-one composition per style and **that premise does not
hold for this field**: `adp` 0% QB, ENGINE 8% / 60%, `need_first` 50% / 33%, `points_need` 44% /
47%. Nothing resembling twelve straight QBs. The field is realistic and **the engine still loses
the asset ruler in it.** The "documenting rather than fixing because the benchmark is under
question" argument is therefore weaker than when written — the benchmark improved and the result
got worse, not better.

**Why the ruling still stands anyway.** The repair still changes what replacement level MEANS in
a superflex league, which is `#50`, which the owner holds, and which is gated on `#49`. Nothing
in `#285` makes that a smaller or differently-owned change. The `points` half — what you actually
field — remains mild. And `#288` establishes that no ruler independent of the engine's own
objective exists here, so a `cdme` deficit cannot be converted into a claim about real-world
cost. **Bound restated at its measured size; disposition unchanged.**

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

### #112 checked and left alone — correctly parked, already guarded

Applying the rule earned from #122 and #188 (*before asserting something is missing, grep for
the mechanism*), #112 was checked rather than investigated. It is **genuinely open, precisely
scoped, and already defended** — no work was warranted.

The kind-of-absence distinction **does** exist upstream: `bot_research.py` carries the
never-checked-versus-checked-and-absent distinction through `_finding_origin_note`, the provider
boundary carries "this provider does not report it" (`test_providers`), and the UI renders it
with a tooltip that states the distinction in words ("never checked, which is not the same as
checked and found none"). What it does **not** do is reach the board: `compute_draft_board`
emits `bpa_source` and `confidence` — where a number came from — and no reason for anything it
did not have.

**Two characterization tests already pin exactly that**, both saying "Pinned, not endorsed …
Delete this test when #112 is settled; do not loosen it", and one of them is an AST scan over
every production module for `unchecked`/`not_checked`/`never_checked` that asserts **zero** hits.

So the item is NEEDS-OWNER, not undone work: its own test states the reason — *"introducing it
means deciding what would ever set it"* — and adding it changes the `PickSnapshot` candidate
schema, the same frozen boundary #107 is parked on. Nothing here to build; recorded so the next
pass does not re-derive it.

### #169-family self-audit: every commit in this stretch stands on its own

#169 records a broken intermediate commit as a process defect — *"staging by filename is not
staging by ownership."* Rather than assert my own stretch is clean, I checked it: all **17
commits** from B2's close to here, at their own trees.

- **Parse-level:** every `.py` at every commit parses. 238→241 files, no syntax break anywhere.
- **#169's actual shape** — a test staged ahead of the module it tests: every `test_*.py`'s
  imports resolve against the modules present *at that same commit*. No test arrived early.

**And the check caught its own instrument error first, which is the third instance of one
pattern this stretch.** My first version hand-listed the standard library, mis-classified
`glob`, `csv`, `tokenize`, `threading`, `multiprocessing` and `tomllib` as unresolved, and
reported the **identical eight "gaps" at all seventeen commits** — including ones whose trees I
never touched. A uniform result across every arm is the signature of a broken instrument, not a
finding, and this repo's own doctrine says so. Rebuilt deriving the set from
`sys.stdlib_module_names` (305 names) instead of guessing it — #126's rule, which I had just
applied to two other problems and then failed to apply to my own tool.

**Three instrument errors in one stretch, all the same shape:** the hint-regex vocabulary scan
that under-counted, the raw-text marker matcher defeated by line wrapping, and this hand-listed
stdlib set. Each was caught by the result looking *too uniform* or *too clean* rather than by
the code looking wrong. That is worth stating as a rule: **when a scan returns the same answer
for every arm, or nothing at all, suspect the scan before believing the result.**

### Second suite gate for this stretch

**2,789 tests, 882.6s, OK (skipped=1), 0 failures, 0 errors** — clean under
`PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared first.

Arithmetic checks out rather than merely looking plausible: **2,783 + 3 + 3**, being
`test_basis_vocabulary_is_one_word` and `test_tav_identity_is_stated_once`. Every commit since
the run launched (`d2788c3..HEAD`) touches markdown only — `git diff --name-only` returns no
`.py` — so the run describes the current code exactly.

Cumulative for the stretch: **14 new tests across three files, mutation-checked 6/6, 3/3 and
2/2**, and no engine source modified anywhere in it. The only non-test, non-documentation edits
were to `README.md`, `ARCHITECTURE_AUDIT.md` and `CDME_CONTRACTS.md` prose.

## #175 REJECTED — no derivable threshold, and the "derivation basis" above it is WITHDRAWN

> **This section replaces one that stood here and was wrong.** It claimed the flagged population
> at 2.5× was *rarer* than a no-cliff null (0.83×), and that real structure lived past 3×,
> reaching 1.21× at 4×. **Both claims are withdrawn** — the 25th correction, mine. The record of
> the error is kept here deliberately rather than quietly overwritten.

**The error was one substitution.** The withdrawn section compared the engine's cliff ratios
against the closed form `P(X >= r × median) = 2^-r`. That is the null for a **plain median of
adjacent gaps**, and `detect_positional_cliff` does not divide by one: its yardstick drops the
zero gaps, drops the target's own gap, and **trims away the largest ~10%**. Each shrinks the
denominator and inflates every ratio, worst in the tail. Simulated on memoryless data, the
engine's **own** estimator gives 0.223 at r=2.5 (not 0.177) and 0.092 at r=4.0 (not 0.062) — a
1.26× and 1.48× understatement, concentrated exactly where the tail claim was made.

Corrected, against the engine's own estimator's null, on `12T_ppr`:

| pos | n | r=1.0 | r=1.5 | r=2.0 | **r=2.5** | r=3.0 | r=4.0 |
|---|---|---|---|---|---|---|---|
| QB | 41 | 0.99 | 1.01 | 0.92 | **1.23** | 1.18 | 1.28 |
| RB | 125 | 1.00 | 1.15 | 1.34 | **1.55** | 1.70 | 2.37 |
| TE | 114 | 1.01 | 1.09 | 1.32 | **1.63** | 1.82 | 2.61 |
| WR | 197 | 1.00 | 1.10 | 1.34 | **1.60** | 1.88 | 2.55 |

The flagged population at 2.5× is **enriched, not rare**, and the enrichment is above 1.0 from
r=1.0 and climbs monotonically with **no inflection anywhere** — so there is no crossing, and
the "null-crossing" derivation basis the withdrawn section offered does not exist. (A heavier
tail than exponential is a goodness-of-fit result; a smooth power-law decay with no tiers at all
would produce it identically.)

**The owner's three questions, answered:**

1. **Stability across formats — structural, and the question partly dissolves.** `bpa` is points
   minus a **per-position replacement level**, and the detector reads only *differences*, so the
   level cancels. Superflex moves the top QB price 48.51 → 163.06 and changes **0 of 41 QB
   gaps**; 10T and 14T likewise, 0 of 125 RB / 197 WR / 114 TE. Only `rec` and `bonus_rec_te`,
   which reshape the curve, move gaps. **Of the eight arms run, three are independent.**
2. **Power — most cells cannot call a departure.** The sizing formula was validated by
   simulating the test it sizes (0.78–0.84 against a 0.80 target), then corrected for the
   **measured design effect** of the shared gap pool, D = 1.22–1.58. WR/TE/RB can reject
   memorylessness; **QB (41 gaps) and every IDP position (12–41) cannot.**
3. **Human recognizability — mixed, and the mixture is the finding.** The largest ratios mix real
   tier breaks (RB3→RB4 McCaffrey→Taylor, WR4→WR5, TE2→TE3) with deep-pool artifacts that score
   **higher** (QB32→QB33 at 30.5×), because a median-gap yardstick collapses where the pool is
   compressed. **The measure is systematically largest where it means least.**

**VERDICT: REJECT.** Per the owner's sequencing — *derive or reject* — no value for
`CLIFF_HIGH_RATIO` is derivable here, and **no constant is changed**. The fallback
("runtime-derived per position") is not thereby recommended: it would inherit the depth artifact
unchanged, so the missing concept is a **depth bound** — *where in the pool the rule applies* —
not a better multiple.

**Not urgent.** `CLIFF_HIGH_RATIO` feeds `NECESSITY_CLIFF_POINTS` → `pick_necessity`, which #55
ruled **OBSERVABLE with no selection authority**. Changing it cannot change a pick today.

**Guards:** `test_cliff_null_estimator.py`, 7 tests, mutation-checked 6 of 7. The survivor
(`CLIFF_HIGH_RATIO` 2.5 → 3.5) survives **by design and must keep surviving** — pinning the
constant would prejudge the ruling #175 asks for, so the tier assertions recompute the boundary
from `ps.CLIFF_HIGH_RATIO` rather than from a literal.

**Also surfaced, not looked for (#241):** all 33 `league_matrix` arms hint `te_premium=True`,
including `12T_ppr_redraft`, which exists to be the non-TEP control — because #213 correctly made
the real (TE-premium) F&F rulebook every arm's base, and `build_mock_league` can add a bonus but
not remove one. The TE-premium *scoring* axis is exercised; the TE-premium *export-selection*
branch never is.

Detail at `evidence/roster_shape/ff_rulebook/FINDING_175_the_ratio_selects_a_quantile_not_a_cliff.md`
and `.../FINDING_the_battery_never_varies_te_premium.md`.

## #241 WITHDRAWN — THE AXIS IS VARIED; I BUILT THE MATRIX FROM THE WRONG LEAGUE (26th)

**The claim, now withdrawn.** That all 33 `league_matrix` arms resolve `te_premium=True` —
including `12T_ppr_redraft`, which exists to be the non-TEP control — because #213 correctly made
the real Fourth & Forever rulebook (`bonus_rec_te = 0.25`) every arm's `base_scoring`, and
`build_mock_league(te_premium=False)` can add a bonus but cannot remove one. It followed that the
TE-premium export-selection branch was never exercised.

**Why it is false.** There are two captured leagues in this repo, and I measured the wrong one:

| file | read by | `rec` | `bonus_rec_te` | roster |
|---|---|---|---|---|
| `data/fixtures/sleeper_capture.json` | **`run_draft_battery`**, `run_roster_proof`, ~10 tests | 1.0 | absent | 12T, SUPER_FLEX, K, 2x IDP_FLEX |
| `data/league_captures/fourth_and_forever.json` | the `evidence/roster_shape/ff_rulebook/` probes | 0.5 | 0.25 | 3x FLEX + SUPER_FLEX, no K, no IDP, IR/TAXI |

`run_draft_battery.scoring_settings_from_capture()` reads the **fixture**. My probe hand-built a
dict from **Fourth & Forever**'s `scoring_settings_observed`. Against the battery's own source:

```
te_premium  {'False': 30, 'True': 3}      constant_axes = []
```

**The axis is varied. No advertised axis is constant.** Measured end-to-end: a real two-arm
battery run printed `CONSTANT AXIS: every arm resolves te_premium=False` for two non-TEP arms —
correct for those two, and the opposite of the filed claim.

**What this rules out, so nobody re-opens it.** The two rulebooks are not a contradiction and
neither is stale. The battery and the roster proof both use the fixture, so they agree with each
other. The `ff_rulebook` probe family deliberately measures the owner's own league and is named
for it; #175's scope statement already says so explicitly (`bonus_rec_te = 0.25, rec = 0.5`).
Nothing else is affected — the error was applying one league's rulebook to a claim about the
other's matrix.

**The error class, and it is one I had already written down.** The engine-measurement doctrine's
first rule is to call the production function rather than hand-roll the fixture
(`rdb.build_players_db`, not a loop). I hand-rolled `base_scoring` instead of calling
`rdb.scoring_settings_from_capture()`, and got a plausible number about a different league —
which is the failure that doctrine exists to prevent, committed by the person who extended it
four rules earlier in this same session.

**WHAT IS KEPT, and why.** `draft_battery.format_axes_exercised` stays, with its docstring
corrected to carry the withdrawal. It is the instrument that **falsified the finding that
motivated it, on its first real run** — the report said `constant_axes` against the true source
and the claim died. The hole it guards is real in KIND even though this instance was not: an
axis can stop varying without any arm becoming a duplicate, and `duplicate_arms` cannot see that
by construction, because it fingerprints measured content and content that differs is never
flagged however constant the axis behind it.

**GUARDS.** `test_241_format_axes.py`, 9 tests, **mutation-checked 7/7** (hand-listed axis
names, `constant_axes` always-empty, names-everything, `labels` ignored, single-arm case, report
drops the disclosure, report uses the whole matrix instead of its own results). Its fixture now
calls `rdb.scoring_settings_from_capture()`, and its witness asserts **no axis is constant
today** — so an axis that later goes constant fails loudly instead of passing in silence.

**A SECOND PROCESS GAP, recorded rather than quietly fixed.** Regenerating `ASSERTION_FLOORS`
for this close added **ten** modules, five of them from earlier closes in this same session
(#188, #175, #224 and the #175 vocabulary tests) — closed without running
`assertion_floors.py --write`, so ten test modules had no floor protecting them. The file
drifted 137 -> 147. No count DROPPED (verified per-module, not just from `--check`'s summary),
so nothing was weakened, but the ratchet was not covering what it was supposed to cover.

## #188 RULED AND EXECUTED: `basis_semantics.py` — one place to ask "is this a bound?", two classes

**The ruling (owner):** adopt `partial` as the shared concept; keep `rule_floor` distinct;
`provider_meter.TRUNCATED` stays out because it describes a payload, not the epistemic status of
a computed quantity. **The condition:** enumerate the actual emitters and make sure the shared
state is *reachable* in each intended vocabulary — do not turn the cleanup into another
unreachable-predicate exercise.

### Reachability, established by EXERCISE rather than by reading

| token | value | how established |
|---|---|---|
| `lineup_optimizer.BYE_PARTIAL` | `partial` | **exercised** — one unknown bye → `partial`; control (all byes known) → `measured` |
| `lineup_optimizer.DISPLACEMENT_ROSTER_PARTIAL` | `roster_partially_priced` | **exercised** — unpriced eligible → that token; control → `measured` |
| `player_universe.RULE_FLOOR` | `rule_floor` | **exercised** — `availability_factor("IR", 17)` → factor 0.7647, basis `rule_floor`; three controls → the absence states |
| `draft_room.REPLACEMENT_BASIS_POOL_TRUNCATED` | `pool_truncated` | **dormant by design** — see below |

**`pool_truncated` is dormant, not dead, and the distinction is the point.** Its clamp binds at
no position on the real rulebook (86 DL, 85 LB, 130 DB price in an IDP league), so behaviour
cannot reach it — and `test_replacement_basis_vocabulary` already guards its wiring **on the
call node**, asserting the `truncated_out` collector is handed over, precisely because no
behavioural test can. A guard that reads as dead is exactly what someone later "cleans up", so
the new test requires that guard to still exist; if it goes, the state becomes genuinely
unreachable and must leave the vocabulary.

### Implemented as a READER, not a rename — and why that is the ruling, not a softening

"Adopt `partial`" could have meant making every bounded-input basis emit the literal string.
**Rejected**, for the reason #187 exists: its repair was *more* tokens, not fewer, because
`denial_value`'s single `0.0` had been three different facts. `roster_partially_priced` and
`pool_truncated` each say **which input** was incomplete; collapsing them to `partial` destroys
exactly what #187 was built to preserve. A rename is also a data-format change — these tokens
are keys in the label maps crossing the Python/JS boundary (#186) and they participate in
snapshot identity (#92) — for no gain a classification cannot deliver.

So `basis_semantics.py` declares no string and moves no constant. It reads the vocabularies that
already exist and answers the one question none of them could alone.

### The axis is behavioural, not taxonomic: *would more evidence sharpen this number?*

- **`BOUNDED_INPUT`** — incomplete inputs, so the result is a bound; more evidence **would**
  sharpen it. A consumer may re-check it; a surface may honestly say "still resolving".
- **`BOUNDED_BY_RULE`** — evidence complete, the *rulebook* yields a bound; more evidence would
  **not** sharpen it. Never re-check hoping for better; the honest surface text is "this is the
  limit of what is knowable".

An IR designation is not partially known. We know it exactly, and the rule says *at least* four
games — a different fact from "some byes are unknown, so this week is a floor", and it changes
what a consumer should **do**.

`would_more_evidence_sharpen()` is **three-state on purpose**: `None` for a non-bound, because
returning `False` there would assert a measured number cannot be improved, which is a stronger
claim than the one being made.

**11 tests, mutation-checked 5/5** — folding `rule_floor` into the partial class, admitting the
payload token, dropping a classified token's reachability record, deleting the dormant member's
wiring guard in `draft_room`, and collapsing the three-state answer to two. No engine source
modified; both files restored byte-identical after the pass.

---

# #242–#246 — the slot vocabulary, the capture leak, the take model, and a reversal

Five items from one pass. They are recorded together because three of them are the same shape:
**a question nobody had asked, sitting behind a question that had been answered.**

## #242 — the slot vocabulary had two questions and one answer

`draft_battery.NON_STARTING_SLOTS` and `league_config.NON_PLAYING_SLOTS` held identical
membership under two names — the duplication #126 forbids. The duplication was not the cost.
The cost was that a SECOND question looked answered when it had never been asked:

| | question | answer |
|---|---|---|
| Q1 | does this slot START a player? | BN, TAXI, IR say no |
| Q2 | is this slot FILLED BY THE DRAFT? | only IR says no |

Every instrument used `len(roster_positions)` as a startup draft's round count. That is Q2
answered with Q1's silence, and it is wrong for any league carrying an IR slot. Invisible
because `data/fixtures/sleeper_capture.json` — the league the battery and roster proof both
draft — has no IR at all, so there the two agree.

Evidence, stated because `{"IR"}` is a vocabulary observation and not a derived magnitude:
F&F 29 slots − 3 IR = 26 **and the real startup ran exactly 26 rounds**; GSOP 33 − 4 = 29.
TAXI is drafted in both, which is what makes the two questions genuinely distinct.
No behaviour changes today (no mock league carries IR) and a test pins that rather than a memory.

## #243 — an engine constant was sitting inside a league capture

`starter_slot_counts` and `league_starters` in both captures are `draft_room.starter_slot_counts()`
output, carrying the hand-set `SUPER_FLEX_QB_SHARE = 0.85`, inside files whose stated
`capture_method` is transcription from screenshots. An instrument validating the engine against
a capture would have been validating the engine against itself, silently.

`draft_math.PROVENANCE` now classifies every field, and `test_capture_provenance` RE-DERIVES the
labels rather than trusting them — `engine_derived` fields are reproduced by calling the engine.
**The sanctioned repair is to DELETE a leaked field, never to refresh it**, and that instruction
is stored in the capture so it reaches whoever meets the red test.

## #244 — the take model says a team drafts 6.23 players

One real opponent board, 256 ranked rows, summed through `_take_probability`: ranks 1–5 give
1.21, the `0.02` floor over the remaining 251 gives 5.02. **6.23 expected picks for a team that
makes one.** 96% of the excess is the FLOOR, not the table — `.get(rank, FLOOR)` has no domain
limit, so row 251 and row 6 are priced identically.

It explains a second symptom already in this document: `survival_probability`'s **d=1** collapse
at exhaustion, "worse than absent: it looks like signal and is not". Same floor, other end.

It does **not** explain #206's 0.00 — floored survival is 0.30 over 60 picks. That needs a high
table rank, which is #206's second half (the boards rank by CDME; rivals do not), and that half
is blocked on an INPUT: the real F&F startup board exists at position-only resolution, no names.
Not repaired — choosing a coherent replacement is a #50 decision, and #56 forbids calibrating
one to this sample.

## #245 — the strong claim WINS on the league actually being played

Same harness as #205, only the league swapped:

| run | league | rounds | seats | `points` wins | margin |
|---|---|---:|---:|---:|---:|
| #205 | fixture, 6 formats | 14–15 | 68 | 1 of 68 | −5% to −11% |
| #245 | Fourth and Forever | 26 | 12 | **10 of 12** | **+1.04%** |

Pre-registered before the numbers existed. **The sign belongs to the LEAGUE, not the engine.**

My explanation for it — draft length — was measured and **refuted**: F&F at 15 rounds returns
`points` identical to the cent, because `starter_value` is settled inside the first fifteen
rounds. At a matched round count the fixture loses 1/12 and F&F wins 10/12. Rulebook, roster
shape and superflex × TE-premium remain crossed; `run_roster_proof_rulebook_cut.py` separates
them, pre-registered.

Scope: one league, and +1.04% is an order of magnitude smaller than the deficit it contradicts.

## #246 — the process finding, and the one worth keeping

The F&F proof never set `league["draft_rounds"]`, so the engine planned for 29 picks while
drafting 26. **It was caught because an experiment returned numbers identical to the cent** —
identical output is a broken instrument, not a result. Re-run correctly: identical, so the flaw
was immaterial, *demonstrated* rather than assumed, which is the only reason #245 stands rather
than being withdrawn.

I also suspected this was a live app defect and **was wrong**: `app.py` sets `draft_rounds` from
Sleeper's own `settings.rounds`, which is better than any derivation from roster shape. Recorded
because a wrong suspicion is worth as much as a right one to whoever retraces this.

---

# #247 / #248 — the freeze picture, re-measured

Two runs landed together and they move the picture in opposite directions. Recorded together
because reading either alone gives the wrong impression of where this engine stands.

## #248 — the deficit that framed everything is STALE, and the reversal is one flex slot

Pre-registered three-arm cut, one process, one code version, rounds matched:

```
A  fixture roster + fixture scoring     4 of 12   -0.28%
B  fixture roster + F&F scoring         4 of 12   -0.61%     rulebook moved alone
C  F&F roster     + F&F scoring        10 of 12   +1.04%     reproduces #245 to the cent
```

**A → B: the rulebook does nothing.** That is the environment `evidence/rulebook_ground_truth/`
measured as paying four real starters 15.7% differently, confirmed to the cent against the live
app. It is a real difference and it does not drive this verdict.

**B → C: the roster shape does all of it.** And the two shapes differ by one startable slot —
`FLEX 2` vs `FLEX 3`, identical at every named position and at superflex. A flex slot is where
surplus positional depth becomes startable, and depth is what the engine buys and the control
does not.

**`#205`'s headline is stale evidence.** Its 1-of-68 at −5% to −11% came from commit `8cee942`,
190 commits back, including `#216` — which changed how flex capacity reaches the board. Arm A is
that same format today: **4 of 12, −0.28%**. It was never wrong; it describes a different
codebase. Across every shape tested, engine and control now sit within ~1%.

My own `expect` string on arm A predicted it would reproduce `1/12, −5.03%`. That expectation was
misconceived before the run started, and the skill rule it violates — *never compare a fresh run
against a saved baseline from different code* — is exactly why arm A was built as a control
rather than trusted as a memory.

## #247 — and the blocker that was called dissolved is not

`BATTERY_2026-09-12_scoring_aware_full_99f9f76` returned two chairs unable to field a legal
lineup. Root cause is exact and is not a bug in the backstop: `feasibility_first` protects
DEDICATED slots only, on the stated premise that *"a flex slot is fillable from several
positions, so it is not at risk"*. True until the roster owns no spare of **any** of them.

Seat 5 of `8T_standard` drafted **eight quarterbacks in a one-QB league**. Every named slot was
filled, so `unfilled == 0` and the backstop was a no-op for the whole draft; then the flex solve
ran out of eligible bodies.

**And the audit is a lower bound by a factor of nine.** Across all four 1QB standard arms:

| | |
|---|---:|
| seats measured | 44 |
| ending with a run of 5+ consecutive same-position picks | **18 (41%)** |
| flagged by the audit | **2** |

10T and 12T hoard as hard as the flagged arms and are flagged zero times, because their seats
hoard onto a flex-ELIGIBLE position. Every run begins the pick after dedicated starters fill.
A seat enters an absorbing state and does not leave it.

## Net effect on the gates

- **Gate 1** — delivered.
- **Gate 2** — substantially defused *as posed*. It was framed around a 5–11% trade that no longer
  reproduces. The underlying question is unchanged and still unratified; what changed is that it
  is no longer being decided against a large measured deficit.
- **`#247` is now the only measured drafting failure**, and the only thing here that blocks a
  freeze on the evidence.

## #247 SHIPPED at `3e9c074` — the line above is superseded

"`#247` is now the only measured drafting failure, and the only thing here that blocks a freeze
on the evidence" was true when written and is not now. `feasibility_first` was rewritten to
solve the WHOLE starting lineup through `lineup_optimizer.optimize_lineup` rather than counting
dedicated slots, so a hole that only a flex can fill now binds.

Measured before shipping (`evidence/flex_feasibility/`), both failures fixed, no collateral:

| arm | unfillable rosters | bind rate | seats whose picks changed |
|---|---:|---:|---:|
| `8T_standard` | 1 → **0** | 2 of 112 (1.8%) | 2 of 8 |
| `14T_standard` | 1 → **0** | 2 of 196 (1.0%) | 2 of 14 |
| `12T_standard` | 0 → 0 | 0 of 168 (0.0%) | 0 of 12 |
| `12T_ppr` | 0 → 0 | 0 of 168 (0.0%) | 0 of 12 |

73 existing tests passed unchanged; 5 added (22 in `test_feasibility_backstop.py`), each with a
non-vacuity companion; mutation pass 4/4 in memory (revert-to-dedicated-only,
solver-fills-everything, solver-fills-nothing, ignore-eligibility). Full suite 2862 tests.

**What is NOT done:** one more 33-arm battery before the freeze. That is the gate, not a
per-repair regression test, and it is the owner's call when to spend it.

**Independently confirmed inert on the reversal question.** The `#248` follow-up re-ran the
fixture arm on post-`#247` code as a reproduction control and it came back **byte-identical to
`#248`'s arm A, seat for seat** (seat 1 `2549.12` vs `2486.24`, `+2.53%`, …). The 0.0% bind rate
measured on 12T formats is not an artifact of the battery's fixtures — nothing about that format
reaches the backstop at all.

## #182 (standing order, prose audit): four stale statements, each of which could have cost a session

A mechanical pass over `README.md`, `CDME_CONTRACTS.md` and `WARPATH.md` — every backticked
filename and identifier checked against the tree and against `git ls-files`.

**`README.md` is clean.** 0 identifiers naming nothing; its 6 unfound files
(`data/last_session.json`, `data/league_prefs.json`, `data/player_aliases.json`,
`data/league_formats.json`, `bot_research.json`, `bot_comparisons.json`) are runtime-written and
correctly described as such. Nothing to fix — recorded so nobody re-runs it.

**The four that were wrong:**

1. **`close-register-item` named a dead branch.** "Branch is `ui-authority-pass`, not the
   harness-designated one." Measured 2026-09-12: `ui-authority-pass` is **191 commits behind**
   and 7 ahead, last touched 2026-09-09 at `70e380c`. A session following that line literally
   would have pushed finished work where nobody reads it — `#239`'s failure mode by a different
   route. Replaced with `git rev-parse --abbrev-ref HEAD`: derived (`#126`), cannot go stale.

2. **The same skill's suite budget said "~800-870s" with no commit attached.** It is 2862 tests
   in ~1170-1210s at `3e9c074`. A figure that grows stale without anything failing is how a
   `timeout` gets set too low and kills a run that was fine.

3. **`CDME_CONTRACTS.md` proposed an interface that was measured and rejected.** "Proposed Phase
   2 interface — for sign-off, not yet implemented" derives
   `WAITING_PRESSURE_REFERENCE = 3.0 × 17 = 51.0` to wire `waiting_cost` into `pick_necessity`.
   `#48`/`#71` measured that and went the other way — **the item named the wrong cost**.
   Necessity reads `positional_forfeit`: the horizon matches (next turn, not end of draft),
   `r(waiting_cost, bpa) = +0.847` would re-add the standout component under a new name against
   `positional_forfeit`'s `+0.364`, and coverage is 100% vs partial. Verifiable today: **neither
   `WAITING_PRESSURE_REFERENCE` nor `NECESSITY_WAITING_WEIGHT` exists anywhere in the codebase.**
   Banner added, section left unedited beneath it.

4. **The same document read as one live contract when it is two things.** §1–§3 are the live
   contracts and are cited as authority; everything from "Appendix — the decision-path
   investigation" (line ~535 of ~9500) is history kept in place, including conclusions later
   refuted. A top banner now says which is which. The original **DRAFT — awaiting sign-off**
   gate is preserved verbatim and **not** lifted: that is the owner's to open, and a test pins
   the exact wording so annotating around it can never look like lifting it.

`test_superseded_proposals.py` (7 tests) makes all of this fail loudly rather than rot: the
absence of both constants, the rejection comment still standing at its site in
`pick_synthesis.py`, the shape banner in the opening lines, and the DRAFT banner unedited. Each
carries a non-vacuity companion — including one that points the same search at
`NECESSITY_SURVIVAL_WEIGHT` to prove the search can find something.

**And the index that was supposed to catch this had three blind spots of its own** (`doc_index`,
`#126`): it counted pytest's generated `.pytest_cache/README.md` as a document of this repo;
it read a skill file's YAML `description:` as the document's own claim, filing a **live**
checklist among the retracted findings for the word "withdrawing"; and it classified **its own
output** as withdrawn, because its rendered legend sits in its own first twelve lines. The
document set is now `git ls-files` — the question git already answers — and the classifier reads
past frontmatter and skips its own output. 5 mutations, 5 caught.

## #248 FOLLOW-UP: it is not one flex slot either — the 27th withdrawal, and it is mine

`evidence/roster_proof/README_RULEBOOK_CUT.md` closed by naming what it had not established —
*"why one flex slot is worth this much; the mechanism above is a reading, not a measurement"* —
and named the cut that would settle it. That cut was pre-registered at `5936b53` before any
number existed, run in **both directions**, and the reading did not survive it.

```
                                       points          engine − control (points.starter_value)
A2  fixture roster, FLEX 2  start  9   4/12  -0.28%      -6.99      CONTROL
D   fixture roster, FLEX 3  start 10   3/12  -0.84%     -22.53      one flex ADDED
C2  F&F roster,     FLEX 3  start 10  10/12  +1.04%     +29.43      CONTROL
E   F&F roster,     FLEX 2  start  9   9/12  +0.84%     +22.08      one flex REMOVED
```

**Adding a flex to the loser made it worse. Removing one from the winner also made it worse.** A
slot that hurts in both directions is not what separates the two leagues — it is movement of
about the size of the effect it was meant to explain, with the wrong sign twice.

### The controls reproduced bit-for-bit, which is the only reason the cuts are readable

`A2` vs `#248` arm A and `C2` vs arm C: **0 differing values across 12 seats × every metric** —
both rulers, starter / bench / total, `starters_filled`, `unpriced`. Not "to the cent".

That also closes something `#247` could not close about itself. Its 0.0% bind rate on 12-team
formats was a rate over a battery population; this is the same seats and the same totals across
a repair that rewrote `feasibility_first`. **`#247` is provably inert on this format.**

### The comparison that leaves no room for the startable count either

`A2` and `E` have the **same 9 startable slots**, the same rounds, the same pool, the same
harness — and opposite verdicts, **−6.99** against **+22.08**.

### Three candidates entered; two were already refuted, and this refutes the third

| candidate | verdict | evidence |
|---|---|---|
| draft length | REFUTED | `#245` — identical to the cent at 15 and 26 rounds |
| scoring rulebook | REFUTED | `#248` arm A→B — 4/12 either way, in an environment measured as paying four real starters 15.7% differently |
| flex / startable count | **REFUTED** | this run, both directions, no consistent sign |

### What is NOT fixed, and what is next

The structural difference still standing, and the one `#248` dismissed as unable to enter:

```
fixture   15 slots   9 startable   15 draftable  ->  15 picks fill it EXACTLY.   0 spare
F&F       29 slots  10 startable   26 draftable  ->  15 picks fill 15 of 26.    11 spare
```

`draft_room.draftable_slots_per_team` counts every slot except IR and feeds
`remaining_league_picks` — its own docstring: *"how many draft picks the league still has to
spend, summed per team… EXACT and BOUNDED, reaching exactly zero when every roster is full"* —
which feeds the bench-appetite rates. On the fixture that quantity is driven to zero; on F&F it
never falls below 11 per team. **Roster capacity reaches the engine independently of flex count
and round count.** Both cuts in this run held it fixed by construction (BN ↔ FLEX preserves the
total), so nothing here tests it.

**Next pre-registered cut:** the fixture roster with bench padded to F&F's 26 draftable slots,
nothing else changed — same 9 startable, same PPR rulebook, same 15 rounds, same pool. If the
engine moves toward `+1.04%`, capacity is the mechanism. If it stays near `−0.28%`, all three
structural candidates are gone and what remains is TAXI, which the fixture has none of and F&F
has five.

### One observation recorded, not claimed

`cdme` — the tautological ruler — **loses 0 of 12 on both fixture arms** (−14.78%, −17.65%) while
winning on both F&F arms (7/12, 8/12). `COMPARE_ON["cdme"]` is `total_value`, which carries a
large negative bench term, and the engine's bench prices below the control's on the asset ruler
in every arm (−65.85, −106.08, −57.14, −29.68). **A tautological ruler that loses is its own
question.** It is not this one, it reproduces `#248`'s arm A exactly, and nothing above is
claimed from it — but it is written down here rather than left in a JSON nobody opens.

## #250 MEASURED: IT IS THE RULEBOOK. The roster was never the cause of anything (28th withdrawal)

The missing cell of a 2×2×2 nobody built on purpose, run with F&F's scoring supplied DIRECTLY
rather than through `build_mock_league`'s overlay. Pre-registered at `18be63b`.

```
D2  fixture roster, FLEX 3, fixture PPR        3/12  -0.84%  margin -22.53   CONTROL
B3  fixture roster, FLEX 2, TRUE F&F scoring   9/12  +0.84%  margin +22.08
G   fixture roster, FLEX 3, TRUE F&F scoring  10/12  +1.04%  margin +29.43
```

**The 15-slot fixture roster under F&F's rulebook reproduces the 29-slot F&F roster
BIT-FOR-BIT.**

| new arm | matched against | differing values, 12 seats × every metric |
|---|---|---:|
| `D2` fixture, FLEX 3, PPR | flex cut `D` | **0** |
| `B3` fixture, FLEX 2, F&F | flex cut `E` — *the F&F roster* | **0** |
| `G` fixture, FLEX 3, F&F | flex cut `C2` — *the F&F roster* | **0** |

A roster with 6 BN, no TAXI and no IR produces the same draft as one with 11 BN, 5 TAXI and 3 IR,
seat for seat, to the last decimal — once the rulebook matches.

### Why the whole thread went the wrong way

`#248`'s only rulebook arm never moved the rulebook. `build_mock_league` overwrites `rec` from
its own `scoring` argument, so arm B ran at `rec = 1.0` and resolved to `hint = ppr` while arm C
resolved to `half_ppr`. `rec` reaches offensive valuation by FILE SELECTION — it picks the
rankings export — so the two arms read **different exports**, and the cut that was supposed to
isolate the rulebook changed everything about it except the part that matters.

Every later cut then inherited the conclusion and searched the roster, which is inert.

### What each factor is worth, now that all four are measured

| factor | effect on the verdict | evidence |
|---|---|---|
| **rulebook** (PPR ↔ half-PPR + TE premium + first downs, and its export) | **3/12 → 10/12; −0.84% → +1.04%** | `D2` → `G` |
| flex / startable count | 9/12 → 10/12; +0.84% → +1.04% | `B3` → `G` |
| roster beyond startable slots (bench, taxi, IR, size) | **nothing** | `B3`≡`E`, `G`≡`C2` |
| draft length | nothing | `#245` |
| roster capacity | nothing — fenced off the pick path | `#249` |

It is coherent rather than surprising: startable structure reaches the pick, `#249` proved
nothing else about the roster does, and the rulebook selects the export. Identical drafts are the
PREDICTION of those two facts.

### What it does to the freeze — the largest consequence in this whole thread

`FREEZE_CHECKLIST.md`'s scope-limit section had the suspicion right and said so honestly:
*"the size and possibly the SIGN of the points deficit is not established for F&F. Neither is it
refuted. It is unmeasured."*

**It is now measured, and the sign really does flip.** Same roster, same pool, same rounds, same
code — only the rulebook:

```
fixture PPR rulebook        3 of 12   -0.84%   engine BEHIND
F&F rulebook (the owner's) 10 of 12   +1.04%   engine AHEAD
```

Every fixture-measured claim in the freeze record — `#205`'s headline deficit, all 33 battery
arms — was taken in a full-PPR environment the owner does not play in. The long-open checkbox
("re-measure the freeze evidence on F&F's rulebook, or certify against a generic environment and
record F&F as out of scope") is no longer a choice between two unknowns. **It is the owner's
call, and it now has a number.**

### What is NOT established

- **That the engine is good.** Every arm sits within ~1% of its control. `+1.04%` is small; it is
  simply no longer negative in the league being played.
- **WHICH PART of the rulebook does it.** `rec` 1.0→0.5, the TE premium, first downs, the
  completion bonus and the export all moved together. `#248` arm B is now useful precisely
  because of its defect: it shows first downs + completion bonus + TE premium, **at PPR reception
  value on the PPR export**, change the verdict by nothing. So the live suspects are `rec` and
  the export it selects, and separating those two is the next cut — a question about one input
  rather than about a league.

## #251 RULED (owner) + EXECUTED: certify invariants across a configuration space, not a league

**The ruling.** PPR, half-PPR, TE premium, first downs, completion bonuses, roster sizes, flex
counts and superflex are **configuration dimensions, not foundational assumptions**. `#250`
showed a 33-arm PPR battery cannot be universal evidence — the same roster under two rulebooks
reverses the sign of the deficit — but the correction is not to crown F&F. What gets frozen is:

> the engine's behaviour is correctly governed by league configuration, and the core invariants
> survive across the supported configuration space.

Stated so the trap is explicit: **do not replace "PPR is representative" with "F&F is canonical."**

### 1. The split, DERIVED rather than declared

`config_space.py` reads it out of `draft_battery`'s own structure — whatever
`structural_findings` aggregates is invariant (*"a finding here is a DEFECT, not an
observation"*), whatever else `audit_trajectory` emits is configuration-dependent (*"no verdict,
because a verdict would need a number I chose"*).

| INVARIANT | domain |
|---|---|
| `duplicate_picks` | every configuration, no precondition |
| `unpriced_picks` | every configuration, no precondition |
| `undraftable_positions` | every configuration, no precondition |
| `unfilled_starting_slots` | every configuration where `rounds >= startable slots` |

Configuration-dependent, reported and never asserted: `shape`, `margins`, `qualifiers`,
`regimes`, `strength`, `unpriced_at_decision`. They all share one shape: **the assertion is
configuration-free while its REFERENT is configuration-derived.**

### 2. Coverage, measured

| matrix | arms | axes | varied | F&F coordinates no arm produces |
|---|---:|---:|---:|---:|
| before | 33 | 91 | **16** | **21** |
| after one capture added | 34 | 91 | **77** | **0** |

One real captured league moves more axes than the other 33 combined, because all 33 are built
from one base rulebook with a `rec`/TE overlay. The fixture's own uncovered count is **0 by
construction** — the matrix is built from it, which is exactly why its coverage was never
evidence about anything else. `CAPTURE_fourth_and_forever` is supplied DIRECTLY, never through
`build_mock_league` — the function whose `rec` overwrite caused `#250`.

### 3. The configuration layer is demonstrated to work, with no new run

Across `#250`'s seven arms — two rulebooks, two flex counts, two roster sizes, 84 seats — **every
invariant held** (every lineup filled, every pick priced) while **the dependent outcome reversed
sign** (margin −22.53 against +29.43). Pinned by
`test_config_space.TheConfigurationLayerIsDemonstratedToWork`, reading committed artifacts.

### 4. What executing the ruling CORRECTED — #242's defect, one layer up

Adding one real league immediately failed two committed tests, both rightly.
`unfilled_starting_slots`' precondition was written and enforced as
`rounds == len(roster_positions)`. The audit asks whether the STARTING lineup can be fielded, so
what it needs is `rounds >= startable slots` — nothing about the bench. Indistinguishable for as
long as every arm was a mock league with no IR; the first real league (29 slots, 26 draftable,
10 startable) failed the equality while satisfying the property comfortably.

**An equality standing in for the question actually being asked** — `#242` exactly, and hidden
for the same reason: no configuration in the matrix could tell the two apart.

### 5. Parked deliberately

`rec` versus export selection. `#248`'s arm B is useful *because* of its defect: first downs +
completion bonus + TE premium, at PPR reception value on the PPR export, change the verdict by
nothing — so the live suspects are `rec` and the export it selects. A question about ONE INPUT,
not about a league. Recorded, not pursued.

### What is NOT done

The certification RUN itself. Which axes deserve coverage at their extremes is a design decision
with a cost attached and it is the owner's. What changed is that a proposed matrix can now be
measured for coverage **before** the hours are spent. Full statement:
`evidence/CERTIFICATION_DESIGN.md`.

## #252 RULED (owner): Gate 2 answered — the exchange rate is configuration-dependent, and there is no canonical one

**The ruling.** Present-season points versus dynasty asset value has **no single exchange rate
across the configuration space**. Outcomes are reported per configuration cell, and **no cell's
number is the engine's verdict**.

### Why this was answerable now and was not before

Gate 2 was framed around a measured 5–11% deficit, and the question was "is that trade worth
it?". Three measurements dissolved the framing rather than answering it:

- `#248` arm A re-measured the deficit on today's code at **−0.28%**, not −5.03%. The headline
  was stale evidence from 190 commits back.
- `#250` swapped only the rulebook on a fixed roster: **−0.84% → +1.04%**. The SIGN is a
  property of the scoring environment.
- `#251` established that such outcomes are configuration-dependent BY CONSTRUCTION — they are
  measured against `reference_values`, which is built from the league's own scoring settings.
  Comparing them across configurations compares two rulers.

So the question "is this trade worth it" had no configuration-free answer to find. Asking for
one was the error, and `#250`'s reversal is what made that visible.

### What the ruling settles

| | |
|---|---|
| **Is there a canonical exchange rate?** | No. Not PPR's, not F&F's. |
| **What does a cell's outcome mean?** | Evidence about THAT configuration. Reported, never asserted against a fixed value. |
| **What does certification assert?** | The invariants (`config_space.classification()`), which hold in every cell. |
| **Is the engine "ahead" or "behind"?** | Neither, as a configuration-free claim. It is ahead in some cells and behind in others, all within ~1% of control. |

### What it unblocks

`#164` recorded these as downstream of the Gate 2 ruling and not to be repaired independently.
They are now released for Phase 3 work, each on its own merits rather than against a deficit:

- `#74` / `#76` — the bpa unit drifts 72× and bundles six quantities
- `#147` — the valuation anchor has a one-season lifetime in a dynasty engine
- `#152` — the `trade_value` fallback's ceiling is a unit artifact
- `#165` (reserved half) — contextualizing an unpriced player
- `#229` — cross-position VOR authorized; the DEEP-BENCH case undefined

### What it does NOT say

- **Not that the engine is good.** Every arm measured sits within ~1% of its control. The
  ruling removes a false question; it does not answer the open one about quality.
- **Not that the deficit never existed.** `#205`'s numbers were real measurements of a real
  codebase in a real configuration. They describe a different commit and a different league.
- **Not that configuration-dependent means unmeasurable.** Each cell's number is a fact about
  that cell, and `config_space` exists so the cells are chosen deliberately.

## #253 WITHDRAWN (29th, mine): the horizon does NOT go dark for the last six rounds — one of four live call sites is unpriced

Gate 4 was ruled "horizon layer goes dark for the last 6 rounds — repair before freeze" on a
measurement I published and got wrong. **The blackout is not a property of the engine's endgame.
It is a property of the Mock Draft's pricing path.** Evidence:
`evidence/horizon_dark/README_HORIZON_DARK.md`, artifact `CARRIED_RATE_PROBE.json`.

### The cut

Three cells, one process, one code version, **the same league and the same 180-pick control
board in all three** — the pick stream is held fixed so the pricing path is the single variable.

```
12T_ppr_SF  DRAFT ROOM pricing  priced 481 -> 301   3 positions measurable at EVERY sample
                                                    floors placed 4/9 at every sample
12T_ppr_SF  MOCK DRAFT pricing  priced 256 ->  86   measurable 3 -> 2 -> 1 -> 0 by pick 108
                                                    floors placed 0/9 from pick 108 on
```

Pick 108 of 180 is round 10 of 15. **My published "dark after round 10, last six rounds"
reproduces to the pick — and only on the Mock Draft's pricing.**

### The cause

`sleeper_projections` is what `#180`/`#192` wired in so the league's own scoring reaches a price.
Production builds a board at four live sites and passes it at one:

| site | passes `sleeper_projections` |
|---|---|
| `app.py:5365` — the live Draft Room | **yes** |
| `app.py:5014` — the Mock Draft | no |
| `app.py:4959` — editing an earlier pick | no |
| `draft_room.py:3491` — `simulate_opponent_picks` | no |

`build_snapshot`'s own comment says passing None "keeps the previous behaviour exactly, which is
what every offline caller and every test does." Three of those four are not offline callers.

The estimator needs `2 × demand` **priced** rows at a position. 481 priced clears that bar for
RB/TE/WR all draft; 256 does not survive ten rounds of drain. No arithmetic in the estimator is
involved, and no carried curve would have addressed the actual cause.

`sleeper_client.get_season_projections(season)` returns `player_id -> {stat: season total}` and
takes no league — scoring is applied separately from `scoring_settings`. So the dict the Draft
Room already holds is valid unchanged at all four sites. **The repair is wiring, not a quantity.**

### What rules OUT

- **A carried/locked appetite curve as the repair.** It was designed for a regime that the
  wiring fix removes. Nobody should re-derive it.
- **"The engine can't compute once the board fills."** On the Draft Room path the fixture board
  never loses a measurable position across a full 15-round draft.

### What SURVIVES

- **Superflex QB is dark from pick 0**, on the live path, in every cell: demand 22 needs 44
  priced rows, the board has 42 (Draft Room) / 39 (Mock). QB's bench appetite is imputed from
  the RB/TE/WR mean for the whole draft, in production, and nothing records that it was. This is
  the finding the owner already ruled "register now, repair with the horizon fix," and it is
  untouched by the withdrawal.
- **A real dark regime, one sample wide.** Fourth and Forever (26 rounds, 312 picks) on Draft
  Room pricing degrades 3 → 2 measurable at pick 216 and goes fully dark at pick **312, the
  final pick**. That is the honest scope.
- **~~The all-or-nothing collapse is still wrong.~~ CORRECTED SAME DAY, BEFORE ANY CODE — the
  claim was false and it is mine.** I wrote that one measurable position cannot place a floor.
  The probe's own artifact says otherwise:

  ```
  F&F picks 216   live-measurable [TE, WR]   floors placed: RB, TE, WR
  F&F picks 240   live-measurable [TE, WR]   floors placed: RB, TE, WR
  F&F picks 300   live-measurable [TE, WR]   floors placed: QB, RB, TE, WR
  F&F picks 312   live-measurable []         floors placed: none
  ```

  `positional_bench_appetite` ALREADY degrades per position: an unmeasurable position takes the
  mean rate of the measurable ones. The only full collapse is the `if not rates` branch, which
  fires when ZERO positions are measurable — and that branch is `#62`'s deliberate fix, because
  with nothing measured there is no mean to impute FROM, and its predecessor returned `0.0`,
  asserting "no position is ever benched." **There is nothing to repair on this half.**

  The owner ruled "wiring + per-position degrade" on the false description. With the second half
  dissolved, Gate 4 reduces to the wiring fix, which is unaffected. The one true collapse state
  is the final pick of a 26-round draft, and the only thing that would place a floor there is
  the carried curve. Owner's follow-up ruling: measure what a person actually sees at that pick
  before deciding.

### The owner's objection, answered on measurement

> *"a locked curve feels like raw BPA with a different name"*

Right about the thing it names, and it does not describe the hybrid. Arms: **A** live-only
(status quo), **B** live-where-measurable + carried-where-dark, **C** opening rates always.
`|B − C|` over position-samples where live measurement exists:

| cell | samples | differ | mean | max |
|---|---|---|---|---|
| 12T_ppr_SF Draft Room | 64 | 56% | 2.59 | **19.73** |
| Fourth and Forever | 80 | 89% | 4.57 | **15.73** |
| 12T_ppr_SF Mock Draft | 36 | 50% | 4.22 | **33.00** |

B and C differ in half to nine-tenths of samples by up to 33 points of horizon floor, so the
hybrid is provably not the locked curve. **The stronger answer is that the carry is nearly
unreachable once the wiring is fixed.**

### What is NOT fixed — owner's call

The wiring repair is **not applied**. Gate 4 was ruled on a premise I have now withdrawn, so
the repair the owner authorized is not the repair the evidence supports. Reshaped decision goes
back to them rather than being swapped in unilaterally.

### The instrument's own limit, stated

The probe's `residual` block compares observed positional picks against the **bench**-appetite
share, and most early picks are **starter** picks, so it conflates the two halves of remaining
demand. Its numbers are recorded and must not be read as a trending signal. The instrument that
would answer the trending question compares observed picks against `remaining_starter_demand`
and `estimated_bench_demand` together.

## #254: `invariant_confirmation`'s first execution produced TWO results and NEITHER is usable — plus the final-pick measurement

The harness ran for the first time (`evidence/invariant_confirmation.json`). It reported one
SURVIVED and one caught. Checked before either was believed, **both verdicts are artifacts.**

### `board order ignores feasibility: caught` — it is a CRASH, not a catch

The recorded evidence is the failure itself:

```
ValueError: Length of ascending (3) != length of by (2)
Ran 14 tests in 13.618s
FAILED (errors=1)
```

The mutation removes `"_feasible"` from `sort_values`' `by` list and leaves `ascending` at three
entries. Pandas rejects its own arguments before any board is built, so **every** test touching
the board errors. That is not the suite detecting a behavioural regression; it is the mutant
being unable to run.

This is the exact false-pass class this file already recorded — *"a non-compiling mutant fails
every test and `rc != 0` would report it as caught"* — and the repair I made for it,
`ast.parse(mutated)` before writing, **does not cover this case**: the mutant is syntactically
valid Python whose defect is argument arity at runtime. The guard was necessary and not
sufficient, and I recorded it as if it were sufficient.

### `feasibility_first never binds: SURVIVED` — the mutated path is INERT on this league

The mutation injects `scored["_feasible"] = 1` at both sites. Whether that changes anything
depends on what `_feasible` already holds. Measured on a full 312-pick Fourth and Forever board,
8 samples spanning the draft:

```
 picks  seat   rows  _feasible==0    ==1   BINDS?
     0     1   1119             0   1119   no (uniform column)
    60    12   1059             0   1059   no (uniform column)
   120     1    999             0    999   no (uniform column)
   180    12    939             0    939   no (uniform column)
   240     1    879             0    879   no (uniform column)
   288     1    831             0    831   no (uniform column)
   300    12    819             0    819   no (uniform column)
   311     1    808             0    808   no (uniform column)
```

**`_feasible == 0` occurs zero times.** The mutation sets a column to the value it already had,
and sorting by a uniform column is a no-op with or without it. The suite did not fail to catch a
change; there was no change. `#245`'s rule is what caught this — an instrument reporting
"NOTHING DEFENDS THIS" about a code path that never executes is a broken instrument.

`fills_required_slot` is defined as `_feasible == 0`, so on this league that observable is
never True either.

### What this actually says, and what it does NOT

- **NOT** that `feasibility_first` is undefended. The mutation never tested it.
- **NOT** that `feasibility_first` never binds anywhere. ONE league, ONE control-driven board.
  F&F is 26 rounds against 10 startable slots plus taxi and IR — enormous slack, and a backstop
  that never binds there is plausibly correct rather than broken. The place it would bind is a
  SHORT draft with tight slots, which this measurement does not cover.
- **It does** mean `#164`'s dissolution of the `#154`/`#155`/`#114` family — which rests on every
  seat filling its lineup — is not evidenced by this backstop on this league. Lineups fill here
  for some other reason. Whether the backstop carries that claim anywhere is unmeasured.

### The repair the harness needs before it is run again

A mutation is only a test of the suite if the mutated path EXECUTES and its output CHANGES.
Neither was checked. The harness must, per mutation: (1) verify the mutant imports and builds a
board without raising, so an arity or type error cannot be scored as a catch; (2) verify the
mutated quantity is non-uniform on the fixture, so an inert path cannot be scored as a survival.
Until both hold, a verdict means nothing.

### The final-pick measurement (owner's ruling), which DID land

`evidence/horizon_dark/final_pick_board.py`, Fourth and Forever, Draft Room pricing:

```
OPENING BOARD    picks made=0    seat 1    1119 rows   floors: RB, TE, WR      basis measured/unavailable
pick 301 of 312  picks made=300  seat 12    819 rows   floors: QB, RB, TE, WR  basis imputed/measured
pick 312 of 312  picks made=311  seat 1     808 rows   floors: NONE            basis unavailable
after the draft  picks made=312  nobody     807 rows   floors: NONE            basis unavailable
```

**The dark state is a REAL TURN, not a phantom.** Pick 312 has seat 1 on the clock and 808 rows
on the board, and `waiting_cost` is absent on every one of them (against 181 of 819 one round
earlier). So it is not the case that darkness only arrives once the draft is over.

It is also exactly ONE pick in 312, in the last round — the owner's reading, that carrying a
curve at round 26 is a far smaller sin than at round 11, is supported: the affected pick is a
handcuff-or-dart slot, and it is one of them. The absence contract is working correctly there
(`basis: unavailable`, `#166`'s conditioning holding); the question is only whether a labelled
carried floor beats an honest absence on that single turn.

## #255 MEASURED: the unpriced carry NO observed dimension — the bracketing question does not apply, and ORDER LAST is correct here

The owner's framing, by example: players grading `70/112/26` and `68/107/24` bracket a third at
`69/109/???`, so the missing metric is constrained rather than unknown — and the engine should
place him on evidence rather than sorting him last because `_priced == False`. The plan was a
bracketing holdout to test whether that generalises across the population.

**Measured first, and it changes the question.** F&F board, Draft Room pricing, 1119 rows:

```
metric            priced (481)   UNPRICED (638)
proj_3yr                   256                0
trade_value                256                0
projection                 256                0
sleeper_points             469                0

unpriced carrying at least one correlate: 0 of 638
```

An unpriced player here is not `69/109/???`. He is `???/???/???`. "Unpriced" in this pool means
**no vendor row AND no Sleeper stat line** — the only two things that can produce any number —
so there is no observed dimension to bracket on. A holdout run on the priced population would
have produced a confident coverage figure about a question the unpriced population cannot ask.

### What this settles

- **ORDER LAST is not an arbitrary 404 for these rows.** The engine is not declining to use
  information it holds; it holds none. The owner's standard — an informed placement rather than
  an error-404 one — is *met* for tier 3, because "no evidence exists" IS the informed answer.
- **What is still wrong is only that the board cannot say so.** "No evidence of any kind exists
  for this player" and "sorts last" are different claims, and only the first points at a remedy.
  That is a vocabulary gap of the `#187`/`#190` family, not an ordering defect.
- **The bracketing holdout is not worth building as designed** and should not be re-proposed.

### The pool is THREE tiers, not two — and the middle one is new

```
256  vendor projection + proj_3yr + trade_value + sleeper_points   fully covered
225  sleeper_points ONLY                                           priced by the league's own scoring
638  nothing                                                       no evidence of any kind
```

The middle tier exists *because of* `#253`'s wiring: those are players the vendor does not cover
whom the league's own scoring can still price. Before the repair they were tier 3 on three of
four live surfaces.

### The actionable remainder: a join gap, not an ordering problem

```
UNPRICED players findable by name in the KeepTradeCut frame:  50 of 638
priced   players findable by name in the KeepTradeCut frame: 379 of 481
KTC rows available: 499
```

**50 of the 638 have material that exists and is not joined** — rank, tier, age, positional rank
sitting in `merger.external_values`. For those 50, and only those, the owner's question becomes
answerable: a single monotone correlate is enough for a *relative* placement even though it is
not a price, which is `#165`'s ordering-vs-pricing distinction applied to a named population.
That is SUPPLY work of the `#210`/`#49` family.

### What this does NOT establish

- **Not that 588 players are worthless.** It establishes that this repository holds no evidence
  about them. A source that covered them would change the answer entirely.
- **Not that the 50 can be placed.** Only that material exists for them. Whether one correlate
  orders them reliably against the priced tail is unmeasured, and is the narrow live question.
- **Nothing about other leagues.** One league, one board. The tier sizes are league-specific;
  the mechanism (no vendor row and no stat line ⇒ no dimensions) is not.

## #256 (step 4): the sweep for findings measured against a board that no longer exists — FOUR, named

`#253` moved the live board from **256 priced rows to 481** on three of four surfaces. A finding
measured against the 256-row board is not wrong; it describes a board this repository no longer
builds, which is the same species as `#248`'s stale `#205` deficit. Found the way that one was:
by asking the instruments, not by remembering. `evidence/pricing_sweep/unpriced_instrument_sweep.py`.

### The result

```
tracked .py files building a board                       86
live surface, DERIVED from app.py's own imports          35 modules

PRODUCTION with an unpriced board                         0     <- #253 closed it
UNIT TESTS with unpriced boards                          22 files, 194 calls   (not step-4 work)
INSTRUMENTS that may rest on the old board               15
  ...of those the register actually CITES                 4
```

**The four to re-measure or annotate:**

| instrument | unpriced calls |
|---|---|
| `run_216_review_probe.py` | 3 of 3 |
| `run_need_bonus_ablation.py` | 2 of 2 |
| `run_risk_adj_softening_measurement.py` | 2 of 2 |
| `run_216_fix_probe.py` | 1 of 2 |

The other 11 suspects are uncited — no published finding rests on them, so there is nothing to
re-measure until one does.

**`PRODUCTION = 0` is an INDEPENDENT confirmation of `#253`.** This sweep and
`test_live_board_pricing` reach the same conclusion by different routes: the test reads `app.py`
for a fixed pair of builder names, this walks every tracked file and derives the live set from
`app.py`'s import list. Two instruments agreeing is worth more than either alone.

### Two defects in this sweep's own first draft, both caught before any number was reported

1. **It hand-listed the live surface and got it wrong** — naming `draft_counterfactual`,
   `roster_diagnostics` and `prediction_record` as production when `app.py` imports none of
   them. That is `#126`'s failure (one home for a vocabulary, derived, never hand-listed)
   committed *inside* an instrument written to audit `#126`-shaped problems. Now derived from
   `app.py`'s own import list, which cannot go stale.
2. **It counted unit tests as suspect findings**, reporting **34** candidates where the real
   number is **15**. A unit test building an unpriced board is usually correct — it exercises a
   function against a synthetic fixture and publishes nothing.

### What this sweep CANNOT see, stated because it bounds every number above

It detects whether `sleeper_projections` is **passed**, not whether the value is non-`None`. A
caller threading a nullable variable reads as priced. Verified: **zero** board-building calls
pass a literal `None`, so the production count is sound today. But a probe whose unpriced arm is
its own experiment (`carried_rate_probe.py`) is invisible to a syntax-tree scan by construction.
An exemption list for that case was written and then **removed** — it stayed empty, and an
exemption nobody needs rots into a false claim about coverage.

### What this does NOT establish

- **Not that the four findings are wrong.** Only that their evidence predates the pricing repair.
  Each needs a re-run or a dated annotation; which, is per finding.
- **Not that the 11 uncited instruments are safe to run.** They are safe to *ignore* until
  something cites them.
- **Nothing about the 194 unpriced test calls.** They were classified, not audited.

## #257 RULED (owner): four Gate-5 answers, and one of them exposed an item with no written basis

### `#98` — RATIFIED (b), as built

Cited sources are allowlisted for **anything that feeds the composite price**; prose citation
stays free. The recorded reasoning holds: *"a rank changes a price, a narrative does not."*
`source_policy.py` already implements this (`#132`), so this ruling records a decision rather
than authorising work. Gate 5 item closed.

### `#146` — RULED admissible in REDRAFT ONLY

A bye week is a real cost when you own the player for one season and meaningless when the asset
outlives the schedule. `bye_week` is currently team-derived at 99.1% coverage, built as an
observable, and read by `roster_diagnostics` — it reaches no price (`#142`).

**The ruling is Gate 5; the wiring is Gate 3 and is NOT done.** It needs the redraft/dynasty
boundary (`league["settings"]["type"]`) to gate admission, a test that fails on the old
behaviour in each mode, and the absence contract honoured for the 0.9% with no bye week — a
missing bye is not a zero cost. Registered as open work, not claimed as complete.

### `#150` matrix — TRIM TO INDEPENDENT FORMATS

The Gate 1 re-run certifies a matrix derived from `config_space` rather than inherited from the
withdrawn runs. The checklist's own warning is the reason: *"do not count 33 arms as 33
independent ones"* — league size and superflex cannot move a gap-based quantity at all (0 of
41/125/197/114 gaps change while the top QB price moves 48.51 → 163.06). Keep both real captured
leagues as anchors, keep every arm that closes a distinct axis, drop arms that can only
re-measure something structurally identical. This executes `#251`'s ruling — representative
coverage plus cross-configuration invariants — instead of re-running a matrix nobody chose.

**Not yet derived.** The trimmed set and its cost are the next work item; the 34-arm figure
(≈6.5h, 77 of 91 axes) is what it will be measured against.

### `#149` — THE ITEM HAS NO WRITTEN BASIS. That is the finding.

Asked to re-read `#149` before ruling, I could not, because there is nothing to read. The
complete record is two lines:

```
FREEZE_CHECKLIST.md:388   - [ ] #149 — upload storage custody.
POST_AUDIT_PLAN.md:4813   ... - #149 (upload storage custody) - ...
```

No section, no measurement, no recommendation. The four sub-decisions I put to the owner
earlier — *client-side custody, extract-vs-artifact, search, use-derived retention* — came from
the task tracker's **title line**, which turns out to be the entire specification. I presented
them as if they were a summary of an entry. They were not.

This is `#37`'s family — a freeze-gating item whose basis cannot be located — and it is worse
here, because `#37` at least knows its evidence is missing while `#149` reads as settled.

**What IS known, from the code rather than the register.** `attachments.py` documents the built
behaviour, and it is narrower than the item's name suggests:

| property | current behaviour |
|---|---|
| where | one shared server-side `data/attachments/`, gitignored |
| parsing | **none** — nothing is parsed or auto-matched to player records |
| what reaches the LLM | the **user-written caption** only; the raw file is stored for viewing |
| scope | chosen by the user at upload, **never inferred**; files never move when scope changes |
| retention | **none — nothing expires anything** |

Uploads are reference material. They reach no price and no pick. So this gates the freeze
RECORD, not the engine.

**Owner's ruling: write the missing entry first, then rule.** The entry must measure what is
actually stored, how much of it, and who can read it — then bring options backed by that rather
than by a title line.

## #258 CORRECTED: the matrix trim was ruled on a stale number — there is almost nothing to trim

`#257` recorded the owner's ruling to TRIM the Gate 1 matrix to independent formats. I put that
option forward citing `duplicate_arms`' own docstring: *"8 of them reproduce another arm byte for
byte."* Measured on the last complete run before deriving anything:

```
BATTERY_2026-09-12_scoring_aware_full_99f9f76
formats: 33    independent: 32    picks: 5340    seconds: 23556.4  (6.54h)

DUPLICATE ARMS: 1
  12T_ppr_mode_balanced   duplicates   12T_ppr

constant axes: []
```

**One duplicate, not eight.** Trimming removes a single arm and saves ~12 minutes of a 6.5-hour
run. The ruling's premise was mine and it was wrong.

### Why the docstring went stale, which is the useful part

The figure was measured when the battery was **vendor-priced**: no half-PPR export exists in the
baseline, so half_ppr leagues drew PPR values and collapsed onto the PPR arms byte for byte.
`#213`/`#201`/`#204` made the battery scoring-aware, and scoring now reaches a price through the
league's own **stat lines** rather than only through export selection — so those arms stopped
being duplicates. **The redundancy the trim existed to remove had already been eliminated by the
scoring repair.** The docstring is corrected in place and no longer carries a count the detector
reports for itself.

### The other warning is a DIFFERENT claim, and I conflated them

`FREEZE_CHECKLIST`'s *"do not count 33 arms as 33 independent ones"* is about what a **particular
quantity** can see: league size and superflex cannot move a gap-based quantity at all (0 of
41/125/197/114 gaps change while the top QB price moves 48.51 → 163.06). Those arms still produce
**different boards** — they are not duplicates. The warning says a gap-based finding must not be
read as independently corroborated across them. It does not license dropping them, and I used it
as though it did.

### Owner's ruling, reversed on the measurement: RUN 34

33 fixture arms + `CAPTURE_fourth_and_forever`, ≈6.5h, 77 of 91 axes, directly comparable to the
withdrawn runs and to `#247`. `#257`'s trim ruling is SUPERSEDED, not deleted — it was correct
given what it was told.

### What this does NOT establish

- **Not that the 32/33 independence figure still holds.** It was measured at `99f9f76`, before
  `#247`'s repair and before `#253`. Independence is reported BY the run, so the next run states
  its own figure rather than inheriting this one.
- **Not that 77 of 91 axes is sufficient coverage.** The 14 uncovered axes are unexamined; no
  argument has been made that any of them is load-bearing.

## #259 (`#158` verification): eight rulings, not ten — and one was carried incompletely

`#158` asked whether the ratified decisions are carried verbatim into the freeze record. Checked
rather than assumed, and it earned its place — the answer is no, in three separate ways.

### 1. There are EIGHT, not ten

`FREEZE_CHECKLIST` said *"the ten ratified decisions"*. This document says **"The eight freeze
rulings"** and lists eight docket cards, ruled 2026-09-06 16:12–16:21 UTC and *"read back from the
artifact store rather than paraphrased from memory"*. Eight is the sourced figure; ten had no
basis. Corrected.

### 2. One ruling lost a clause on the way into the record

```
docket:     #161/#52   Run #52 blind and unbriefed, but UNSCORED
checklist:  #52 — the blind adversarial pass runs after the freeze and stays unbriefed.
```

**`UNSCORED` is absent from `FREEZE_CHECKLIST` entirely** — the word appears nowhere in it. Seven
of eight rulings are carried faithfully; this one is carried two-thirds.

It is not a cosmetic loss. A *scored* blind pass invites tuning toward its rubric, which destroys
the only unbiased read available — the precise reason `#52` is run last and unbriefed at all.
Restored, with the reasoning attached so it cannot be dropped again as redundant.

### 3. `#158` is a number collision, the same defect `#160` exists to void

| where | what `#158` means |
|---|---|
| `POST_AUDIT_PLAN` §3959 | *"an unpriced leader crashes the Draft Room"* — a repaired defect, cited by `#173` |
| `FREEZE_CHECKLIST` / task tracker | *"confirm the ratified decisions are carried verbatim"* |

Two unrelated items under one number, exactly as `CONST-A1/A2/A3` collided with `BLIND-A1`. Both
are recorded rather than renumbered: renumbering breaks every existing citation, and `#173`
already cites the first meaning by number.

### What this does NOT establish

- **Not that the other seven are carried *verbatim*.** They are carried *faithfully* — same
  substance, checklist phrasing. Only `#52`'s was materially incomplete.
- **Not that the docket is the only source of rulings.** Rulings made in session since
  2026-09-06 (`#251`, `#252`, `#257`, `#258`) are recorded here, not on that docket.

## `#149` — THE MISSING ENTRY, WRITTEN FROM MEASUREMENT. Two upload surfaces, opposite custody, neither named as a policy

`#257` found the item had no written basis: a title line and one clause in a NEEDS-OWNER list.
The owner ruled **write the entry from measurement first, then rule** — "what is actually
stored, how much of it, and who can read it." This is that entry. **It rules nothing.** Every
line below was read out of the code in this session, not carried from the earlier audit.

### The finding: the app already contains BOTH answers to "extract vs artifact"

The item's own title names `extract-vs-artifact` as an open question. It is already decided
twice, in opposite directions, in two places, and neither decision is written down as a policy:

| surface | `app.py` | the FILE | what persists |
|---|---|---|---|
| Reference material | `:2795` — `pdf csv json png jpg jpeg webp gif txt` | **kept forever**, raw | the artifact itself; nothing is extracted from it |
| Credentials | `:2341` — `txt env pdf` | **discarded**, never written to disk | only the parsed keys, into `.env` |

`attachments.py:1-6` states the first as a deliberate choice — *"Nothing here is parsed or
auto-matched to player records… the raw file itself is just stored for the user to view."* The
credentials path does the exact inverse at `app.py:2343-2352`: `creds_file.read()` into memory,
`parse_credentials_blob`, then `save_parsed_keys_to_env` (`:770`) writes only `KEY=` lines into
`.env` (gitignored, `.gitignore:1`). **The uploaded credentials file is never persisted.** That
is the stronger custody posture of the two, and it is the one that is undocumented.

### What is actually stored

- `ATTACHMENTS_DIR = Path("data/attachments")` (`attachments.py:33`) — **one flat directory,
  not per-league and not per-user.** Created unconditionally at import (`app.py:103`), whether
  or not anything is ever uploaded.
- `dest.write_bytes(data)` (`attachments.py:58`) — the raw bytes, as uploaded. Name collisions
  rename rather than overwrite. Metadata (caption, `uploaded_at`, `league_ids`) goes to
  `captions.json` through `store_io`'s atomic/locked path (`#102`).
- Gitignored: `data/attachments/*` (`.gitignore:19`).
- **How much, measured on this checkout: zero.** `data/attachments/` holds one file —
  `captions.json.lock`, 0 bytes. There is no `captions.json`. That is a fact about this
  container, not about any deployed instance, because the path is gitignored and cannot be
  observed from the repository.

### Retention: there is none

`grep -niE "retention|expire|ttl|prune|max_age|purge"` across `attachments.py` and `store_io.py`
returns **nothing**. No expiry, no TTL, no size cap, no scheduled cleanup, no age-based
pruning. Deletion happens only on explicit human action — `delete_attachment`
(`attachments.py:116-120`) unlinks the file and drops its caption. "Use-derived retention",
the third clause of the item's title, does not exist to be evaluated; it is a proposal.

### Who can read it

- **There is no authentication.** The whole app greps once for `password|authenticate|login|
  session_token`, and the single hit is a docstring at `app.py:744` explaining why: *"Sleeper
  needs no password, just a username."* Identity is a remembered username string.
- The management view calls `list_attachments()` **unfiltered** (`app.py:4622`), with the
  in-code comment *"this is a management view, show everything regardless of scope"*. Every
  stored file from every league scope is visible, and deletable, to whoever has the app open.
- **The model never receives a file.** `app.py:2184` filters to the selected league, keeps only
  captioned items, caps at 20, and fences them as `untrusted`. The prompt says so in as many
  words: *"you're only given the caption text, not the actual file, so treat it as a claim to
  weigh, not verified fact."* Pinned by `test_tenant_scope_boundary.py:83-92`.

### What the owner is now in a position to rule

1. **Name the extract-vs-artifact policy that already exists in two forms**, and say which
   surface each belongs to — rather than leaving two opposite behaviours undocumented.
2. **Per-league or per-user directories**, or the flat store as intended. The unfiltered
   management view is only defensible under the single-local-user assumption `app.py:775`
   states for `.env` and nothing states for attachments.
3. **Retention**, if any. Today the honest description is "forever, until a human deletes it."
4. **Client-side custody**, the item's first clause, is a change of architecture rather than a
   setting: storage is server-side on the machine running Streamlit.

Gates the freeze RECORD, not the engine: uploads reach no price and no pick, and the only text
that reaches a model is a caption the user typed, fenced as untrusted.

---

## #261 MEASURED — THE NATURAL ZERO EXISTS, AND IT IS SEAT-INDEPENDENT

The owner's rule for when upside mode should begin, in their own words: *"if a league never
pulls from the deep reserves, then I dont necessarily mind it not reaching for upside mode. if
you're still pulling valid decent depth, who cares."* That is a rule about the MARGINAL PICK,
not the calendar. `UPSIDE_MODE_DEFAULT_ROUND = 15` (`draft_room.py:245`) is a calendar.

The standing objection to replacing it was `#56`: any replacement needs a bound nobody invented.
If the candidate observable only ever decays to a handful before the draft ends, the rule needs a
THRESHOLD on that handful — and a threshold is exactly the invented constant `#56` charges
against round 15. So the deciding question was pre-registered before the run: **does the count of
candidates above replacement ever actually reach zero?**

### It reaches zero, exactly, and stays there for eleven rounds

`evidence/mode_boundary/where_would_it_fire.py`, four formats spanning the measured bench-depth
range, seat 1, real simulated drafts (not a synthetic picks array — `#221` was withdrawn because
a fixture-shaped picks list faked the drain). The board is rebuilt from `picks[:i]` at each of
that seat's turns, so board state matches the turn.

```
CAPTURE_fourth_and_forever   rounds=26   round15->15   replacement-crossing->16
    r14  max_bpa=  33.67   above_replacement=  5 of 314
    r15  max_bpa=  33.67   above_replacement=  5 of 303
    r16  max_bpa=    0.0   above_replacement=  0 of 280
    r17  max_bpa=    0.0   above_replacement=  0 of 279
    r18  max_bpa= -96.56   above_replacement=  0 of 256
    r26  max_bpa=-142.65   above_replacement=  0 of 160
```

**"No candidate above replacement" is an attainable state, not a limit the draft never reaches.**
A rule keyed on it therefore carries no invented magnitude.

### Two checks, because 5 -> 0 is a hard edge and `#245` says identical numbers are broken until proven otherwise

- **`bpa` is real points, unscaled.** `_scale_vor_to_bpa` (`draft_room.py:2065`) returns
  `vor.astype(float)` — no reference, no rescale, no clip, per `#74`/`#76`. So `bpa > 0` means
  literally "projected above this position's live replacement level," and `n_above` is a genuine
  observable rather than an artifact of a moving ruler.
- **The two exact `0.0` readings are the `#155` tautology, firing where predicted.** The
  replacement-level player prices at 0.00 by construction; at r16/r17 he IS the best thing left.
  He is then drafted and the reading drops to −96.56. The probe's own docstring pre-registered
  this as the caveat it could not escape, which is why `n_above` was printed separately from
  `max_bpa` — so "nothing above replacement" and "something at exactly 0.00" stay distinguishable.

### The rule is STRICTLY MORE CONSERVATIVE than round 15 — 1 of 4 arms, not 2

| format | rounds | round 15 | replacement-crossing | ends with n_above |
|---|---|---|---|---|
| `8T_standard_SF` | 15 | fires r15 | **never** | 8 |
| `12T_ppr` | 14 | never | never | 5 |
| `14T_ppr` | 14 | never | never | 6 |
| `CAPTURE_fourth_and_forever` | 26 | fires r15 | fires **r16** | 0 |

Adopting it would REMOVE upside mode from `8T_standard_SF` and DELAY it one round in F&F. Under
the owner's stated rule that is correct rather than a miss: `8T_standard_SF` ends with eight
candidates still above replacement, which is "still pulling valid decent depth."

What it buys is the removal of a measured artifact. Across the 34-arm Gate 1 battery, arms where
round 15 fires average **−27.0** bench value per bench seat and arms where it never fires average
**−33.4** — the leagues entering upside mode have SHALLOWER reserves than the ones that do not,
because superflex rosters carry one more starting slot, run 15 rounds where 1QB run 14, and so
round 15 is close to a superflex detector. The crossing has no such coupling: it fires on board
exhaustion, which is the quantity the mode is about.

### CONSEQUENCE THAT CLOSES A SEPARATE OPEN QUESTION: the crossing cannot diverge per seat

The owner authorized pricing per-seat mode divergence: *"I dont think two seats being on
different levels is inherently wrong, as long as the logic guiding if they are or not is sound
for both."* Under THIS observable there is nothing to price.

`replacement_levels(pool, value_col, roster_positions, num_teams, remaining_demand,
startable_floors, truncated_out, flex_occupancy)` (`draft_room.py:1402`) takes no roster
identity, and neither live call site (`:2983`, `:3023`) supplies one — `starter_demand` is
league-wide. **`bpa` is seat-independent, so a crossing rule flips every chair at the same
moment.** It is as global as round 15 is. Per-seat divergence needs an observable keyed on the
chair's own roster, and that is a different build, not a parameter on this one.

### WHAT THIS DOES NOT ESTABLISH

- **n = 4 formats, seat 1 only.** This is a probe, not the battery.
- **Nobody has drafted with the rule in place.** This measures WHERE a boundary would fire, not
  what changes if it moves. `#222` found the mode boundary causes 63% of the TE excess; that
  composition effect is UNMEASURED under the crossing.
- **`max_bpa` is dead as an observable** and is reported only to bound `n_above`. It is
  non-monotonic in every arm (`12T_ppr`: 25.38 -> 28.02 -> 31.35 across r8-r14), because the
  level falls as a position empties. `n_above` is clean and monotone in all four.

### NOT RULED

The transition rule is the owner's call and is not changed here. `UPSIDE_MODE_DEFAULT_ROUND`
stays at 15; nothing in this entry touches engine behaviour. What changed is that the `#56`
objection to replacing it no longer stands: the zero is natural.

---

## #262 RULED (owner, this session) — THE DRAFT-TIME SURFACE: DECISIONS, AND THE ONE MEASUREMENT THAT CANNOT BE TAKEN

Recorded because these are OWNER RULINGS made in conversation and would otherwise survive only
in scrollback. Nothing here is measured unless it says so; nothing here is built yet.

### The stack question, answered by a measurement rather than a preference

Coupling, measured 2026-09-14 by import scan:

```
draft_room.py  pick_synthesis.py  data_merger.py  draft_strategy.py
lineup_optimizer.py  llm_engine.py  pick_debate.py  draft_battery.py
design_system.py  draft_board_ui.py        -> streamlit imports: 0, all ten
```

**No engine module imports Streamlit.** `app.py` is 6822 lines, 898 of which touch `st.`, with 48
distinct `session_state` keys and **77 `st.rerun()` calls** — a hand-wired state machine
compensating for a framework that re-executes the whole script on every interaction. The engine
already returns JSON-able records and `design_system.py` already emits portable CSS text.

So replacing the shell costs nothing in engine terms, and **the freeze is unaffected either way**.

`draft_board_ui.py` had already escaped into `st.components.v1.html` and recorded the wall it hit:
*"st.components.v1.html remounts a fresh iframe on every Streamlit rerun... Worth a real component
(not st.components.v1.html) later if that continuity turns out to matter."* It matters. An iframe
cannot paint outside itself, so a slide-in drawer, a modal that dims the page behind it, page
transitions and global opacity are **structurally impossible** in any Streamlit configuration —
not merely awkward. That is the class of effect the owner asked for.

### RULED: the visual brief

- **Game-like UI** — clean, dense, functional. Every state change animated, because the player
  must see what changed.
- **MOBA draft/champ-select is the structural reference, not a flavour one.** It is the same
  problem with different nouns: timed, turn-based, alternating picks from a shared exhausting
  pool, with rivals' picks visible and changing your evaluation.
- **What is stolen:** the clock as the organising element rather than a corner widget; roster
  needs as SLOTS THAT FILL rather than a table column; rivals on the same screen always;
  hover/inspect and commit as two distinct acts; state-change motion as the primary language.
- **What is NOT stolen:** the esports skin (hexagons, bevels, filigree, particles), and the 5v5
  mirror symmetry — a fantasy draft is asymmetric, one seat against 7-13.
- **The limit that breaks a naive copy:** champ select renders 10 picks. A startup draft is 312.
  The pick MOMENT ports; the draft HISTORY does not.

### RULED: the layout

- **A pick rail across the top**, panning as picks land, dimmed at both edges so only the last few
  and next few are legible. The rail's pan IS the clock tick — on-the-clock is a position, not a
  separate timer. Full history lives behind a tab.
- **The snake turn is the thing champ select never had to solve.** "I pick 3.12 and 4.01 back to
  back" versus "23 picks until I'm up" is the single most valuable fact on that rail, and it is
  what `positional_forfeit` is computed over. It gets a strong accent.
- **Candidates are CARDS.** Click to zoom, opening the context window. Depth lives in the zoom,
  not the row, which is what lets the collapsed board stay dense.
- **The zoom does NOT replace the board** — it sits over a DIMMED board, so "who else was close"
  stays in the periphery. One dimming grammar, two jobs.
- **The clock stays lit above the dim.** A modal that hides the timer during a timed pick is
  actively dangerous.
- Comparison ("these two are tied, which one") is NOT solved by zoom, which is one-at-a-time. A
  pin/compare action is a later step, not the default.

### RULED: the debate layer

1. **The draft room must function fully with NO API.** Verified structurally: zero engine modules
   import `llm_engine`, `pick_debate` or any provider — only `app.py` (the shell being replaced),
   `pick_debate.py` itself, the bot benchmarks and tests. So this is a UI-and-defaults question,
   not a refactor.
2. **Build API-absent FIRST, wire the debate in after.** Building with the panel present designs
   around a region most customers will not have.
3. **The no-API state must not look deprived** — no empty debate pane, no configure-a-key nag in
   the card. Which makes `#119` (universal_value's decomposition reaches no consumer) and `#183`
   (absence contract broken in the live Debate Dock) LOAD-BEARING rather than polish: for most
   customers the engine's own evidence is the whole explanation.
4. **NO AUTOMATIC PINGS, EVER.** Explicit user action only. This voids the author's own
   "auto-start at freeze" proposal in full.
5. **A debate may only be initiated while on the clock** — owner's reason, and it is a
   CORRECTNESS argument rather than a cost one: *"so state change doesn't sweep the rug out from
   the debate context."* It also aligns the debate's lifetime with a window the engine already
   defines, since `PickSnapshot` is frozen at the turn. Gives `#92` a consumer: a transcript
   pinned to a snapshot id is reproducible.
6. **One snapshot, two renderers.** The card renders it for a person; the prompt fences it
   (`#125`) for a model. Never two derivations, or the chairs argue about numbers the human
   cannot see.
7. **Freeze the initiate button when remaining time drops below what a debate needs.**

### The constant NOT invented, and the term that cannot be measured

The owner's first form was *"estimate + 15sec or something"* and flagged its own arbitrariness.
Per `#56` (a bound is not a threshold) the recorded form is: **freeze on the SLOWEST DEBATE
OBSERVED for that configuration** — a real measurement carrying earned margin, self-correcting as
the provider changes, keyed per (chairs x model) so it is not an average over debates nobody runs.
Cold start has no bound and says so; it is not given an invented first estimate. `provider_meter`
exists and `#100` (nothing meters what a call costs) is the blocker.

Three honest outcomes, not two: **arrived and useful / cancelled on expiry / arrived-but-stale.**
A debate must be CANCELLED when the clock expires rather than completing and billing for a dead
verdict, and anything that slips through renders as stale, never as live advice.

**THE TERM THAT CANNOT BE DERIVED.** The owner's sharpest point: the time to switch to Sleeper,
find the player and click is real, and **this application is structurally blind to it** — it
happens outside the app and no instrumentation on our side will ever observe it. It is therefore
the one term a user SETS rather than one we derive; a value the owner declares is an input, not an
invented constant. The better move is to SHRINK it rather than budget for it: carry the player's
name **spelled exactly as Sleeper spells it** (we hold the record), one-click copy, deep link
where one exists.

That reframes the product: **this is a co-pilot beside the draft, not the draft.** The success
metric is time from recommendation to the pick landing in Sleeper — not board density. Analysis
earns its keep only if it survives the handoff.

### MEASURED: player headshots ARE available

Run by the owner on a machine that can reach the CDN; artifact at
`evidence/imagery/headshot_probe_result.json`. Six players x two URL patterns, **12/12 `200
image/jpeg`**, at `sleepercdn.com/content/nfl/players/{id}.jpg` and `.../thumb/{id}.jpg`.

- Attempted from this environment first and it is **BLOCKED-EXTERNAL, not a null result**: 403 at
  CONNECT, 12 fetch_errors and 0 non-200s. The probe's refusal to merge "no headshot" with "fetch
  failed" is what kept that from reading as an answer.
- **Retired players resolve** (Roethlisberger, id 138, 49KB) — relevant for a dynasty app.
- **A WITHDRAWAL, the 27th.** Stafford (id 421) returned byte-identical sizes for full and thumb
  (23994/23994) where every other player differed, and this author called it a likely silhouette
  placeholder, cautioning that `200 image/jpeg` does not prove a real photo. The owner opened both
  URLs: it is a real photo of Stafford, and `thumb` simply falls back to the full asset when no
  thumbnail exists. The hypothesis is WRONG and withdrawn. The narrow true residue: `thumb` is not
  guaranteed smaller, so do not rely on it for bandwidth.
- **The design constraint the image actually revealed**, which is the useful part: the photos are
  ~4:3 landscape, cropped mid-chest, on a **light grey background** — not transparent cutouts. A
  grid of those fights a dark palette. Options are a tight circular crop (what Sleeper does), a
  gradient mask dissolving the grey into the card ground, or OWNING it: the portrait sits on a
  deliberately light PLATE, treated as a physical object on a dark table. The third suits the
  slot-filling rail, where each pick lands as a plate in a slot.

### PINNED, not started: the browser plug-in

DraftSharks ships an extension that injects a collapsible right-side sidebar over the live Sleeper
draft board. That **deletes** the handoff term rather than budgeting for it.

**RULED: the website surface first, the plug-in pinned as the next UI/UX step.** They are two
displays, and the second requires an install.

Notes for when it is picked up:
- **Read draft state from Sleeper's API, never from the DOM.** Take the draft id from the URL and
  poll `/v1/draft/{id}/picks`. Sleeper is a React app with generated class names; DOM scraping
  breaks on any front-end deploy. Inject UI into the DOM; never read state from it.
- An extension cannot run Python, so CDME sits behind a thin server it talks to. **That is the
  same thing a web front end wants** — one server, two clients, not two products. It strengthens
  the engine-behind-an-API step rather than competing with it.
- Scope: draft-time only. Trade calculator, roster diagnostics, matchup and the debate still need
  the main surface.
- Two risks to settle BEFORE building on the assumption: Sleeper's terms of service (a competitor
  doing it is evidence of tolerance, not permission), and Chrome Web Store review plus Manifest V3.

### #262 AMENDED — RULED (owner): the freeze is a USER SETTING with a DERIVED RECOMMENDATION

Supersedes the form recorded above. The owner's final shape, verbatim in effect:

- **The user selects their own freeze timer.** The app does not choose it.
- **A note explains the variance**: different models and internet speeds change how fast results
  come back, so no single number fits everyone.
- **A note explains the stake**: a debate or Insight call that lands later than you can use it is
  wasted money, and the lock exists to prevent that — stated as a preventative measure, not a
  restriction.
- **The RECOMMENDATION is 10-15 seconds longer than the slowest recorded call OF THAT FUNCTION.**
- **Manually editable.**
- **Able to be disabled entirely.**

**WHY THIS SATISFIES `#56` WHERE THE EARLIER FORM DID NOT.** The rule forbids the ENGINE acting on
a magnitude nobody argued for. Here the acting authority is the user's own setting; the `10-15s`
is advice displayed beside it, visible and overridable. A recommendation a person accepts is not a
constant the system invented — the difference is who holds the pen, and it is the user.

Two requirements that follow, recorded so they are not lost as nice-to-haves:

1. **COLD START HAS NO RECOMMENDATION.** The suggestion is *slowest recorded + margin*, so it
   cannot exist before that function has been observed. On a fresh install the lock is OFF and the
   setting says it will offer a recommendation once it has seen the call run. It is NOT pre-filled
   with a guess — that would be the invented constant re-entering through the default.
2. **THE VALUE MUST BE VISIBLE, NOT SILENT.** A recommendation that pre-fills and is never looked
   at is functionally a constant this application chose. The owner's "manually editable, or able
   to be disabled" already implies this; it is written here as a requirement.

**PER FUNCTION, not global** — the owner's "of that function". A three-chair debate and a single
Insight ping have different cost and latency profiles; one bound over both describes a call nobody
makes. Same reasoning as the per-(chairs x model) keying above.

Still required regardless of the setting, because the lock is preventative and not a guarantee:
cancel an in-flight call when the clock expires rather than completing and billing for a dead
verdict, and render anything that slips through as **stale**, never as live advice. `provider_meter`
is the instrument; `#100` (nothing meters what a call costs) is the blocker on all of it.

### #262 EXTENDED — RULED (owner): a debate is an EMBLEM ON A PLAYER, and the rail re-centers

**The emblem.** A debate or Insight result attaches to the player it was about, and is reachable
afterwards from the pick rail, the full draft board, and the roster view.

Two things this fixes that were left open above:

1. **A paid-for debate stops evaporating.** Today its whole life is the seconds you are on the
   clock. As an annotation it becomes a record, which is also the first VISIBLE consumer `#92`
   (persist and uniquely identify the snapshot) has ever had — the emblem is a pointer to a
   stored snapshot id.
2. **It dissolves the staleness problem** recorded above. The rule stands that a late result may
   never render as LIVE ADVICE. But as a timestamped annotation it is entirely legitimate: *what
   the chairs said at 3.05, about the board as it was at 3.05.* Same content, different frame, and
   the emblem is the frame that makes a stale verdict useful instead of dangerous.

**THREE OUTCOMES, distinguishable on the emblem** — debated and TAKEN, debated and PASSED,
debated and SNIPED (passed, then taken by a rival). The third is the one most worth reviewing
afterwards, and together they make a finished draft something a manager can learn from rather
than a list of picks. A debate is scoped per (player, turn), so repeated debates on one player
across turns are separate records with the most recent surfaced.

**The rail re-centers, and the behaviour matters more than the button.**

- The re-center control **appears only when the rail is off-centre**. A permanently visible one is
  dead chrome at every moment you have not scrolled.
- **A pick landing while the user has scrolled away must NOT yank the view back.** Stay put and
  BADGE the control with what was missed ("3 picks since"), the way a chat client handles new
  messages below the fold. Snatching the viewport is the single thing that makes a scrollable
  timeline infuriating.
- **Auto-recentre when it becomes the user's turn**, regardless of scroll position. That is the
  one moment where losing your place is correct, because *now* is the only thing that matters.

### #262 EXTENDED — RULED (owner): rail boxes name the drafting seat, and your own picks are marked

**Every box on the pick rail carries the drafting user's name / team name.** The reason this
matters more than it looks: **a snake reverses seat order every round**, so "whose pick is 4.07"
cannot be read off position — it requires arithmetic, mid-draft, on a clock. A label removes the
ambiguity outright. Champ select solves the same problem with team colour, which works for two
sides and does not for eight to fourteen seats.

**The user's own picks are marked** (owner's word: glowing).

Two constraints recorded because they are easy to get wrong:

1. **DO NOT SPEND GLOW TWICE.** The obvious treatment for "on the clock right now" is also glow.
   If the user's seats glow AND the live pick glows, they collide at precisely the moment the user
   must distinguish *it is my turn* from *that one is mine*. Two facts, two channels: the live
   pick takes the clock treatment (it is already privileged — it is the rail's centre and what the
   pan tracks), and the user's seat takes a persistent ownership marker (band, border, accent)
   that reads as MINE rather than NOW.
2. **MARK UPCOMING PICKS, not only past ones.** This is where it pays. With future turns marked,
   *"I pick 3.12 and 4.01 back to back"* versus *"23 picks until I am up"* becomes something the
   user SEES rather than computes — which is the snake-turn accent called for above, delivered by
   a mechanism that costs nothing extra.

**Two box states, designed separately:**

- **FILLED** — the pick has landed. Portrait and player name lead; the owner is secondary (colour
  band or small label).
- **PENDING** — no player yet, so the owner label IS the content and is the only thing that
  matters.

No new data source: the league's rosters already carry owner display names and team names from
Sleeper.

### #262 CORRECTED — 28TH WITHDRAWAL: the emblem has ONE state, not three

The entry above recorded three emblem outcomes — debated and TAKEN, debated and PASSED, debated
and SNIPED. **That was mine and it is wrong in both halves.** Owner's correction, and the
reasoning is decisive.

**SNIPED IS UNREACHABLE BY CONSTRUCTION.** A debate may only be initiated while on the clock
(ruled above, in this same entry). While you are on the clock nobody else picks. There is
therefore NO WINDOW between debating a player and taking him in which a rival could take him
first. I imported "snipe" from ordinary draft language without checking it against a constraint
set minutes earlier in the same conversation — the same failure shape as several others today:
reasoning from a remembered pattern instead of from the constraints actually in force.

**AND PASSED IS A CATEGORY ERROR.** A debate is not an opinion ABOUT A PLAYER. It is the
reasoning behind ONE PICK, and the snapshot it rests on is only meaningful in the context of who
was actually taken. Hanging a fragment of it on a player who was passed misrepresents what it
was: it would read as *"here is what the chairs thought of this player"* when it was in fact
*"here is a comparison that resolved in favour of someone else."* Same text, false claim — which
is the species of defect this register exists to catch.

**THE CORRECTED FORM.** One emblem, on the player TAKEN, carrying the whole debate including the
alternatives it weighed. Passed candidates appear INSIDE that record as what was considered, not
as annotated entities in their own right.

Everything else in the emblem ruling stands: it persists a paid-for call, it is the first visible
consumer of `#92`'s snapshot identity, and it is the frame that makes a stale verdict legitimate
as a timestamped record rather than dangerous as live advice.

---

## #263 MEASURED — THE MODE SWITCH FIRES ONE PICK LATE, AND THE TEST THAT PINS IT CANNOT SEE THAT

Surfaced by the `#261` depth battery: `12T_ppr_BN10` under the round rule reported its first
upside pick at **round 15, pick 170**. With 12 teams, round 14 ends at pick 168 and round 15
spans picks **169-180**. So the switch fired at the SECOND pick of round 15, not the first.

### Measured, not inferred

```
pick 168 (last of r14)     picks_seen=167   current_round=14   board = balanced
pick 169 (FIRST of r15)    picks_seen=168   current_round=14   board = balanced   <-- here
pick 170 (second of r15)   picks_seen=169   current_round=15   board = upside
```

### The mechanism, and a misnomer

```python
current_round = (max((p.get("round") or 1) for p in demand_source) if demand_source else 1)
use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)
```
(`draft_room.py:2890-2891`)

`demand_source` is the picks ALREADY MADE. At the opening pick of any round, the most recent
pick belongs to the PREVIOUS round. **`current_round` is therefore the round of the last
COMPLETED pick, not the round of the pick being made** — the two differ by exactly one at every
round boundary. The name says the second thing and the code does the first, which is the `#70`
ordinal-vocabulary family in a new place.

The module docstring states the intent plainly: *"'auto' switches to upside scoring once the
current round reaches upside_round."* The first pick of round 15 is in round 15.

### Impact: bounded and small

One seat per draft — whoever picks first in round 15 — receives a balanced board on a turn the
documentation says is upside. Every other seat in that round, and every round after, is
unaffected. It is a knife-edge of the `#86` family (`round(expected_taken)`), not a systemic
mis-scoring.

### THE PART THAT MATTERS MORE: the guard is blind at the boundary it guards

`test_auto_mode_switches_to_upside_exactly_at_the_documented_round` (`test_draft_room.py:2108`)
builds its fixture as:

```python
picks = [... for i, pid in enumerate(list(db)[:8 * round_no])]
```

`8 * round_no` picks is **every round COMPLETE**. The test therefore only ever samples
round-boundary-complete states, and asserts `board_mode(14) == "balanced"` and
`board_mode(15) == "upside"` — both of which hold under the off-by-one, because after round 15 is
finished `max(round)` really is 15.

**The test cannot distinguish "fires at the first pick of round 15" from "fires at the second."**
Its own comment says the thing that must not happen is the boundary "moving without anyone
noticing" — and the boundary is already one pick from where the prose puts it, unnoticed, with
the test green. A guard that cannot see the edge it guards is the `#157`/`#203` shape: it passes
for a reason unrelated to what it claims.

### NOT FIXED, and why

`UPSIDE_MODE_DEFAULT_ROUND`'s own comment calls the boundary a calibration decision, and moving
when the mode turns over changes drafted rosters. Evidence before repair (`#162`): this is
recorded, not changed. Three coherent resolutions exist and the choice is the owner's:

1. **Derive `current_round` from the pick BEING MADE** rather than the last one made, so the
   switch matches the documentation. Changes one seat's board per draft.
2. **Leave the behaviour and fix the PROSE** to say the rule reads completed picks — the honest
   description of what ships today.
3. **Moot it.** `#261`'s crossing rule reads the board rather than the calendar and has no round
   boundary to be off by one at. If the crossing is adopted this defect disappears rather than
   being repaired.

Either way the TEST gap should close independently of the ruling: the fixture must be able to
express a partial round, or it cannot guard this boundary under any rule.

### How it was found, which is the reusable part

Not by reading the code — the code had been read several times. The `#261` depth battery is the
first instrument to run a REAL draft deep enough for the round rule to fire AND to report the
exact `pick_no` it fired at. The finding fell out of a number printed beside an expectation.
Instruments that report WHERE something happened, not merely THAT it happened, find defects that
assertions of the form "it happened" cannot.

### #263b BOUND ON `#261`'s WHOLE MEASUREMENT — every seat is the engine, so every fire-round is a LOWER BOUND

Owner's question: how does rivals taking sub-optimal, below-threshold players affect when the
crossing fires? It bounds the entire depth battery, so it is recorded before any ruling rests on
those numbers.

**FIRST ORDER — sloppiness DELAYS the crossing.** A rival who reaches, or takes a kicker in round
8, leaves an above-replacement player on the board. `n_above` decays more slowly and "nothing left
above replacement" arrives later, or never. That is arguably correct behaviour rather than a
flaw: if the league is leaving value on the table there IS still depth to take, and reaching for
upside would be wrong. **The crossing self-adjusts to the quality of the league.** Round 15
cannot — it fires on the calendar whatever the board looks like, which is the same insensitivity
that produced the measured anti-correlation with bench depth.

**SECOND ORDER — and it cuts the other way.** The replacement level is not fixed. It is the value
of the Nth-best remaining at a position, N being remaining demand. If good players are NOT being
taken, the Nth-best remaining is BETTER, so the level RISES, and a higher level is a higher bar to
clear. Sloppy drafting therefore leaves more good players available AND raises the threshold they
must beat.

**WHICH DOMINATES IS NOT DERIVABLE.** It depends where in the distribution the sloppiness lands.
Demand drains at a fixed rate (one roster slot per pick) while the pool does not, which argues for
first-order winning — but that is a guess and is recorded as one, not as a finding.

**THE BOUND THIS PLACES ON THE RUNNING BATTERY.** Every seat in `simulate_full_draft` is the
production engine taking its own top candidate. That is the MAXIMALLY EFFICIENT drain: the fastest
the board can possibly empty of above-replacement players. Therefore:

> **Every fire-round the depth battery reports is a LOWER BOUND, not an estimate.** A real draft
> containing human noise fires LATER than these numbers, by an amount nobody has measured.

This does not invalidate the battery — a lower bound is exactly what is needed to answer "can the
zero be reached at all," which was `#261`'s question. It DOES mean the numbers may not be quoted
as "the crossing fires at round N in this format." The honest form is "no earlier than round N,
against opponents who never err."

**MEASURABLE, NOT YET MEASURED.** A noisy-opponent arm would settle it: rival seats select
uniformly from their top-k rather than top-1, k as the noise dial. Two cautions if it is built:
`#221` was WITHDRAWN because a fixture-shaped picks list faked the drain, so the noise must be
applied inside a REAL simulated draft, never by synthesising a picks array; and the noise model is
itself a constant nobody has derived, so `k` is a swept axis to report across, never a single
chosen value (`#56`).

---

## #264 QUEUED (owner) — HEAD-TO-HEAD TABLES: 6 engine seats against 6 baseline seats

Owner's request: more of the mixed-table draft trials, to see whether the engine is actually
better. This is `#177`'s family — *"roster proof, valid harness: engine ahead in 7 of 8 arms;
superflex-projection is the one loss"* — and `#208` recorded the uncomfortable half: **that
result stays UNDEFENDED.** A published claim with no guard on it.

**MACHINERY MOSTLY EXISTS.** `#263b` added `opponent_noise` to `simulate_full_draft`, which
already carries `sharp_seats`, so per-seat behaviour is plumbed. A head-to-head generalises that
from *sharp vs noisy* to *strategy per seat*.

### THE REQUIREMENT WITHOUT WHICH THE RESULT IS WORTHLESS: counterbalance the seats

A snake does not treat draft slots equally. If the engine holds seats 1-6 and the baseline holds
7-12, **engine advantage and slot advantage are perfectly confounded** and the number means
nothing. Every matchup therefore runs at minimum TWICE with the assignment mirrored (engine on
1-6, then engine on 7-12), and preferably also interleaved (odds vs evens).

> If the engine wins BOTH halves, it is the engine. If it wins whichever half holds seats 1-6,
> it is the snake.

This is the same class as the `#150` battery's `set_league_format` omission: a harness that
silently varies something other than the thing under test, and produces plausible numbers about
it.

### WHAT A MIXED TABLE CAN AND CANNOT CLAIM

Winning 6v6 shows the engine is **better than those opponents at that table** — partly because
the baseline seats leave value on the board that the engine seats then collect. It does NOT show
the engine is better in a league where everyone drafts well. Both are legitimate questions; they
are different, and `#177`'s claim was never pinned to either. Whichever is measured, the entry
must say which.

### DESIGN NOTES for when it is picked up

- **Baselines to run against, each a real alternative rather than a strawman:** raw projected
  points (no VOR), `trade_value` rank, ADP order, and `opponent_noise` at swept `top_k` as a
  "competent but imperfect human" arm.
- **The scoring question is separate from the drafting question.** "Better" needs a yardstick
  that is not the engine's own objective, or the test is circular — an engine that maximises TAV
  will win a comparison scored on TAV by construction. `#205`'s roster proof (lineup filled,
  asset totals) and season-points-of-optimal-lineup are the two candidates, and they disagree:
  `#177` measured the engine ahead on 7 of 8 arms with superflex-PROJECTION the single loss.
- **Seat-position counterbalancing as above, reported per half**, never pooled into one win rate.
- Every arm keeps `#204`'s pricing path and `#150`'s `set_league_format`, or it measures a
  different engine than the one that ships.

QUEUED behind the `#261` depth battery and the `#263b` noise arm — three simultaneous draft
harnesses on four cores would make all three slower and none sooner.

### #263 PRIORITY RULED (owner): the one-pick boundary error is LOW, and probably moot

> *"I'm not overly concerned on rd 15.2 vs 15.1. It's not static."*

Accepted. The behavioural impact is one seat, one turn, per draft, and if `#261`'s crossing is
adopted the round boundary disappears entirely — `#263`'s option 3 (moot it) rather than a repair.
The entry stays recorded at this priority; it is not queued for work.

The residue is smaller than the original entry framed it: not the one-pick error, but that the
guard **could not see it**. That matters only while a round boundary exists. If the boundary
retires, the test gap retires with it.

### #264 EXTENDED — the baselines are a FACTORIAL, not a ladder, and ADP is not available

**FIRST, A CORRECTION OF MY OWN, made minutes after proposing it.** I proposed deriving opponent
archetypes (QB-early, RB-zero, TE-lean, K/DST-early) from ADP rather than inventing their
constants. **There is no ADP in this system.** This document already said so at the §"ADP is
evidence, never authority" entry — *"Measured: there is no ADP in this system at all"* — and a
live check confirms it: `adp`, `ktc_value` and `rank` are all ABSENT from the pool frame
(`trade_value` 23%, `projection` 26%, `proj_3yr` 21% of 1206 rows). I proposed a solution whose
blocker was already written down, which is the same failure shape as the snipe emblem state and
the `snapshot.mode` detector: reaching for a remembered pattern instead of reading what is here.

**WHAT SURVIVES, and it is better than invented profiles.** `trade_value` is a MARKET signal
that disagrees with points-VOR **positionally**, and that disagreement is measured rather than
chosen. A seat anchored on it produces real positional runs for free — which is the mechanism
archetypes were wanted for — with zero invented constants. Uniform `top_k` noise cannot do this:
it is symmetric, and real drafts are not.

**THE OWNER'S CORRECTION THAT RESHAPES THE BASELINES.**

> *"As real people draft, they're still using context to the player pool as a filter on their
> decisions. So it's not entirely agnostic."*

A seat reading `trade_value` top-to-bottom is not a human — it is a robot with a list, and it
will draft eight WRs. A real drafter using market rankings still notices *"I have no RBs"* and
*"QBs are going."* They carry roster and scarcity awareness; only the VALUATION underneath
differs.

**So a list-reader baseline CONFOUNDS the two things this item exists to separate.** Beating a
robot with a list demonstrates only that roster awareness helps — which nobody disputes and which
is not the claim worth defending. Therefore:

| arm | machinery | valuation | isolates |
|---|---|---|---|
| **value-swap** | full engine | `trade_value` | **the valuation** — a sharp manager on market consensus |
| **awareness-ablation** | `need_bonus`/`depth_exposure`/`displacement_adj` zeroed | points-VOR | **the roster awareness** |
| **naive list** | none | rank order | the FLOOR — included to price it, explicitly NOT a win to claim |

That answers *why* the engine is better rather than only *whether*, and **if the value-swap arm
wins, that is a finding wanted BEFORE the freeze rather than after.**

Encouraging for cost: the machinery may already exist. `replacement_levels` takes a `value_col`,
and `draft_room.py:3023` already calls `replacement_levels(no_proj_pool, "trade_value", ...)` on
the unpriced fallback path — so trade-value-as-anchor is an existing route, not a new one.

**THE ONE HAND-MADE PROFILE THAT IS STILL WORTH IT: kicker and DST taken early.** Nothing in this
system predicts it, it is unmistakably real human behaviour, and it specifically drains positions
the engine barely values — so its effect on `n_above` is not reproducible by any derived
alternative. If it is built it must be labelled an OWNER-DECLARED ASSUMPTION, never presented as
derived.

### #264 EXTENDED — RULED (owner): the opponent profiles are a PRE-REGISTERED hypothesis set, not a clustering

The corpus is real — `evidence/real_drafts/` holds 108 board images recovered from screenshots
of actual human drafts, confirmed by the owner: *"any that show full boards are with real
people."* Two have a KNOWN format and are complete: Fourth and Forever (already hand-transcribed
independently by the owner at `evidence/roster_shape/real_drafts/`) and Greatest Show on Paper 2
(21 images, rulebook captured at `data/league_captures/greatest_show_on_paper_2.json`).

**THE METHOD, and why the owner's framing is stronger than mine.** I proposed deriving profiles
from the boards and worried that ~24 seats — correlated, since twelve people in one league watch
each other — could not support five classes. Unsupervised clustering on that sample would indeed
be unreliable, and the CLUSTER COUNT would itself be a constant nobody derived.

The owner instead NAMED THE PROFILES BEFORE SEEING THE DATA. That converts the task from
discovery to **classification against a pre-registered hypothesis set**, which 24 seats can
support: each seat is assigned to its nearest named profile, the counts per profile are reported,
and **"fits none of them" is a real finding** rather than a modelling failure.

**THE SET IS A 2x3 FACTORIAL ON THE AXES SUPERFLEX ACTUALLY HAS**, not six arbitrary labels:

|  | RB lean | WR lean | BPA |
|---|---|---|---|
| **QB early** | x | x | x |
| **QB not-early** | x | x | x |

In superflex, QB timing IS the strategic axis; after it, which skill position is favoured. The
decomposition is produced by the format rather than chosen, which is the `#56` distinction.

Plus an optional **TE modifier**, probed by where Brock Bowers and Trey McBride go.

**THE CONFOUND ON THE TE MODIFIER, and it may kill it.** GSOP2 is **TE-PREMIUM**. In a TEP
league, taking Bowers or McBride early is the SCORING RULES WORKING, not a personality. TE-lean
is therefore only establishable as a preference in a NON-TEP league. Fourth and Forever's TE
premium status must be checked before that probe means anything there. **If both complete boards
carry a TE premium, the TE profile is unresolvable with this corpus and must be DROPPED rather
than kept on weak evidence.**

**EACH PROFILE IS CHARACTERISED BY PHASE** — positional counts in rounds 1-4, 5-10, 11+ — which
reads directly off a board with no inference. That is also the axis that perturbs `n_above`
differently from uniform `top_k` noise, which is symmetric and cannot produce positional runs.

**WHAT THIS CORPUS CANNOT ANSWER: whether behaviour varies by rules/settings.** Both complete
boards are SUPERFLEX. There is no 1QB board with a verified format — the corpus README says of
the assorted eight that *"format and competition level unverified for most."* So superflex
behaviour can be characterised and cannot be compared against 1QB behaviour. A limit of the
sample, not the method; it closes if 1QB boards with known formats are supplied.

**AND WHY THE MATRIX FRAMING LOWERS THE BAR.** If profiles exist to ASSIGN ROLES ACROSS SEATS,
no single profile needs to be an accurate portrait of a real person — the set needs to SPAN the
observed range. Publishing *"these are the five archetypes of dynasty drafters"* would be
indefensible on this sample; *"these roles cover the observed range, and seats are matrixed
across them"* is fine.

DEFERRED, a design choice to be recorded as one when reached: five roles across twelve seats
cannot run every combination, so the matrix needs a DESIGNED set — homogeneous leagues (one role
in all twelve seats), a balanced mix, and adversarial mixes. That is a choice, never a
derivation.

**Extraction is running now (Fable, background, image reading only — no local CPU).** It was
deliberately NOT told this hypothesis set: a transcription job handed a named expectation is a
transcription that starts finding what it was told to expect.

### #264 EXTENDED — RULED (owner): a profile is a PHASE-VECTOR, and the profile COUNT is an output

> *"then mid could focus on laying a position, or balancing roster slots, or securing qb a bit
> earlier on 2nd slot, or... etc"*

A profile is not one label applied across a whole draft. It is a **triple** — what a seat does
EARLY, then MID, then LATE — and the phases have different vocabularies because they face
different decisions.

**THIS REMOVES THE PROFILE COUNT FROM `#56`'s REACH, which the flat six-label version did not.**
Enumerating the space (roughly 4 early x 4 mid x 4 late) gives ~64 paths and no principled way to
select five. But the space is not enumerated: **the occupied paths are OBSERVED.** Twenty-four
seats will land on perhaps eight to ten distinct triples, several of them repeatedly, and the
profiles are whichever paths are actually occupied. The count is therefore an OUTPUT of the
corpus rather than a number anyone chose — which is exactly the distinction that made round 15
objectionable.

**MID-PHASE VOCABULARY, each measurable off a board with no interpretation:**

- **lay a position** — a third-or-later player at one position while a required starting slot
  elsewhere is still empty.
- **balance slots** — remaining required starters filled before any positional depth is added.
- **QB2 early** — the pick number of the seat's SECOND quarterback. A superflex-specific
  decision, and the cleanest measurable in the whole set: one integer per seat, nothing to judge.
- **BPA** — no positional pattern separable from value order.

`QB2` is the sharpest of the four and is the axis superflex itself creates, the same way QB1
timing is the early-phase axis. Late-phase vocabulary is not yet named and should be read off the
boards rather than guessed at here.

Consistent with the ruling above: the set is PRE-REGISTERED per phase, seats are CLASSIFIED
against it rather than clustered, and "fits none of these" stays a reportable finding.

---

## #265 EXTRACTED — A REAL 360-PICK BOARD, AND IT USES A DRAFT FORMAT THE BATTERY NEVER RUNS

Greatest Show on Paper 2 transcribed from 21 screenshots into
`evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json`. 12-team PPR superflex
TE-premium, rulebook already captured at `data/league_captures/greatest_show_on_paper_2.json`.
Extraction done by a background agent restricted to transcription; **every self-reported check
was re-verified here against the file rather than taken on the agent's word:**

```
1. pick_no 1..360 unique & complete    True
2. 12 per round, 30 rounds             PASS
3. round shapes r1-r6: asc desc desc asc desc asc
   naive snake: False    third-round-reversal: True
4. duplicate player names              0
6. placeholders 48, sequential 1.01 -> 4.12, complete
   illegible 7 (1.9%), 0 names invented
positions excluding placeholders: WR 116, RB 90, QB 54, TE 52
```

### THE FINDING: this league is THIRD-ROUND REVERSAL, and no battery arm ever is

Rounds run `1->12, 12->1, 12->1`, then alternate. `generate_pick_order` has supported `"3rr"`
since M2 and its docstring notes Sleeper exposes it as `settings.reversal_round == 3`. But
**`run_draft_battery.py` and `draft_battery.py` contain zero references to `draft_type`, `3rr` or
`reversal`** — every one of the 34 arms drafts pure snake. Grep across the tree finds exactly one
caller that varies it (`run_216_shared_slot_probe.py:82`); every other instrument passes the
literal `"snake"` or takes the default.

So a REAL captured league uses a format the FINAL GATE (`#150`, which claims coverage across
"sizes/modes/rules") never exercises. This is the second unvaried battery axis found today — the
first was bench depth (`{5:1, 6:32, 11:1}`, `#261`) — and both were found the same way: by
looking at real data rather than at the harness.

**It also nearly corrupted this extraction.** Sleeper prints the `R.P` pick label in each cell.
The agent read pick order off those labels rather than inferring it from column position; an
extractor that assumed snake would have mis-assigned every pick from round 3 onward to the wrong
seat, and nothing downstream would have caught it. Recorded because the profile work in `#264`
depends entirely on picks being attributed to the right seat.

### Two data-shape facts worth carrying

**A traded pick ERASES its own cell contents.** Sleeper renders `->{acquirer}` IN PLACE of
`POS - TEAM (BYE) R.P`, so 84 of 360 board cells carry no position, team, bye or pick label. 82
were recovered from the acquirer's own roster tab; the 2 that were not belong to the single
manager whose roster view was not captured, and are recorded with position (from cell colour) and
`illegible` team/bye. Any future read of a Sleeper board screenshot must expect this.

**The rulebook's `total_picks_if_startup = 348` does not hold.** The board is 360 picks over 30
rounds. It reconciles once placeholders are removed: 360 - 48 kickers = 312 real players = 26 per
team. The rulebook's figure assumes all 29 roster slots are filled with players; the capture's own
`draft_board_observations` already said "~30 rounds". Not a defect in the extraction — a stale
assumption in the rulebook.

The 48 kicker placeholders are confirmed as the 4x12 rookie draft the capture describes, sequential
`1.01 -> 4.12` with no gaps (first K Brandon Aubrey at 2.12 -> rookie 1.01; 13th K Sam Ficken at
10.7 -> 2.01, matching the corpus README). Recording them as literal kicker picks would have made
this league appear to draft kickers from round 3 — exactly the artifact that would have wrecked the
positional-timing signal `#264` needs.

### THE ADP THREAD IS CLOSED, ON EVIDENCE

`evidence/real_drafts/extracted/f_and_f_rookie_adp_panel.json`. The panel exists and is legible,
and it is **three rows**:

```
B. Lance    WR NO   adp 265.2
K. Coleman  WR MIA  adp 275.8
J. Taylor   RB JAX  adp 278.7
```

Sleeper's filter chips read `ALL 3/4` — the entire undrafted pool at capture time was four
players. This is the tail of a finished rookie draft, not a ranking. `projected_points` is clipped
by the screen edge in all three shots and is recorded illegible rather than guessed.

So the corpus README's claim is **accurate in kind and wrong in scale**, and my earlier proposal to
derive opponent archetypes from ADP is dead for a second, stronger reason: not merely that ADP is
absent from the player pool, but that the corpus's ADP is three deep-undrafted values. `#264`'s
`trade_value` route stands as the only market signal available.

---

## #266 PROSE DEFECT — `league_matrix`'s docstring claims coverage the matrix does not have

Found under `#182` (audit the prose when the queue idles), with today's two findings giving it a
test. `draft_battery.league_matrix`'s docstring opens:

> *"Every format the battery drafts, as {label, league, teams, rounds}. **Chosen to span the axes
> a real league varies on** — size, scoring, superflex, TE premium, dynasty vs redraft..."*

**That list is incomplete by its own standard, and two REAL captured leagues prove it:**

| axis | matrix | a real league in this repo |
|---|---|---|
| bench depth | **constant** — `MOCK_BENCH_SLOTS = 6` in 32 of 34 arms (`#261`) | Fourth and Forever: 11 BN + 3 IR + 5 TAXI |
| draft type | **constant** — every arm passes `"snake"`; zero references to `draft_type`/`3rr`/`reversal` in `run_draft_battery.py` or `draft_battery.py` (`#265`) | Greatest Show on Paper 2: **third-round reversal**, measured off its own printed pick labels |

Both are unambiguously "axes a real league varies on" — the docstring's own test — and the repo
holds a captured league varying on each. `generate_pick_order` has supported `"3rr"` since M2, so
the draft-type gap is a matrix omission rather than a missing capability.

**This is the `#133`/`#157` shape: a docstring asserting a property the code does not have.** It
is more than cosmetic here, because `#150` is the FINAL GATE and this docstring is where a reader
goes to learn what the gate covers. Someone trusting it would conclude bench depth and draft type
were exercised.

**NOT EDITED YET, deliberately.** `#162` is evidence before repair, and a docstring is still a
source change that requires its own full suite — which would contend with the depth battery and
the noise arm currently running. Queued behind them.

**The repair is prose, not code**: name the axes the matrix does NOT vary, and why, so the list
reads as a stated scope rather than a claim of completeness. Whether to ADD those axes to the
matrix is a separate and larger question — it would multiply the arm count and lengthen a battery
that already runs 5.34 hours — and it is the owner's call, not a docstring fix.

---

## #267 MEASURED — `setsid` DOES NOT survive a session collapse here; only the checkpoint does

Both background runs died silently during a session collapse. Discovered by an explicit health
check rather than by noticing missing output, which is the point of recording it.

```
processes:        NONE ALIVE
exit-code files:  ABSENT     <- the bash wrapper never reached its `echo $? > ...`
last log writes:  2628s and 2840s ago
tracebacks:       0
```

**The absent `.rc` file is the diagnostic.** Each job was launched as
`setsid nohup bash -c '<python> ...; echo $? > <rc>'`. A python crash would still let the wrapper
write the exit code. No `.rc` at all means **the whole process group was killed**, wrapper
included — reclamation, not failure. `setsid` detaches from the controlling terminal; it does not
survive the container suspending the session.

**This corrects a belief I was operating on.** I launched both runs with `setsid` specifically
"so they survive", said so, and was wrong.

### What actually saved the work

Both instruments checkpoint after every unit and skip completed units on restart. On relaunch:

```
depth battery:  7 [skip] lines -- all seven finished drafts honoured, resumed at arm 4
noise arm:      [skip] k1_seed0 -- resumed at k=3
```

Cost of the collapse: the two drafts that were in flight, nothing else. `#215` is the standing
item — *"the instruments could survive a restart but could not FINISH one"* — and this is the
same lesson from the other side: **the checkpoint is the only survival mechanism that works
here. Process-level detachment is not one.**

### Operating consequence, for every long run after this

1. **Never assume a background job is alive.** Check at the top of every turn:
   `pgrep -af "^python3 -u <script>"` — anchored, and with `-f`, because `pgrep` without `-f`
   matches the process NAME (`python3`) and cannot see arguments at all. That variant cost a
   false "the suite died" call earlier today and a duplicate suite spawned on top of a healthy
   run.
2. **An absent `.rc` with a stale log means KILLED, not running.** A live job advances its log; a
   finished one writes `.rc`. Neither is true for a reclaimed one, and that third state is the
   one that looks like "still going" if only the process list is checked.
3. **Checkpoint every unit, and make resume the default path**, not a `--resume` flag someone has
   to remember. Both of today's instruments did this and both survived intact.
4. **Relaunch is free; re-running is not.** A run that cannot skip finished units turns every
   collapse into a full restart, which for the 5.34-hour battery would mean it never completes at
   all.

---

## #167 EXECUTED: `reach_label` removed everywhere, and the numbers it was derived from kept

The ruling was *"Everywhere"*. This is what "everywhere" turned out to include, and the two
judgment calls inside it that were not in the ruling.

### What went

`consensus_reach` bucketed a **tier gap** — the candidate's KTC tier minus whichever tier the
market normally occupies at the current overall pick — into a three-way verdict: WITHIN
CONSENSUS BAND / MODEST REACH / SIGNIFICANT REACH. The measurement that condemned it: the label
changed **0 of 36 engine decisions** under ablation, while tagging **85%** of candidates as some
flavour of reach. The 85% was not a property of the candidates. It is an artifact of how wide
KTC's early tiers are — the committed export puts its median tier at **18 of 19**, so almost
every candidate sits several tiers below whoever is ranked near an early pick number.

Removed: the two label constants, the `reach_label` field on `CandidateSnapshot` (47 fields →
46), its entry in `draft_history._CANDIDATE_EVIDENCE_FIELDS`, the gated evidence line in
`pick_debate`, three prompt passages that instructed chairs to scale burden of proof by the
label, and both `app.py` render sites.

### Judgment call 1: `tier_gap` went too, and it is not the same kind of removal

`tier_gap` was computed in the same dict and its **only** production reader was the label's own
derivation. It is NOT in `quantity_readers`' closed set — that set is board columns, the two
snapshot dataclasses, `pick_analysis`, `lineup_optimizer`'s dicts and `TeamDiagnostics`, and a
function's own return dict is none of those — so removing the label would NOT have tripped the
write-only pin. It would have left a quantity computed, returned, and read by nothing, sitting
just below the scanner's floor. That is `#138` exactly, and the fact that the guard could not
see it is the interesting half: **the write-only scanner's closed set has a blind spot for
return dicts, and this is the first case to land in it.**

### Judgment call 2: one guard was dropped, and it was MEASURED before it was dropped

`consensus_reach` had two `tier is None` guards. The candidate's own still protects
`int(candidate["tier"])` and stays. The second — *return nothing if the player NEAREST the
current pick has no tier* — existed only to protect the `tier_gap` subtraction, and with the
subtraction gone it would have meant "withhold this player's market data because some other
player's tier is missing," which is unexplainable. Before removing it: **0 of 463 KTC rows lack
a tier**, so the branch is unreachable on the committed baseline and its removal is a no-op on
real data. Measured, not assumed.

### The rename, and why it is part of the same commit

`consensus_reach` no longer computes a reach. Leaving that name is the `#126` failure — a
vocabulary with a second, stale home. It is now `consensus_standing`, and it **no longer takes a
pick number at all**: where the market ranks a player does not depend on where in the draft you
ask. That dropped an unused `current_overall_pick` local in `pick_synthesis` and an unused
parameter from `draft_counterfactual._adp_pick`.

### What deliberately stayed

`consensus_rank` and `consensus_tier` — real sourced KTC data, not a derived verdict. Both
render sites now gate on `consensus_rank is not None` where they gated on the label. The chairs
still see the market's own placement; what they no longer see is this engine's opinion about it.
A test pins the removal (`test_no_verdict_is_returned_alongside_the_numbers`) because a verdict
is easy to re-add by reflex, and a re-added one would put a judgment in front of the debate
layer that nothing has re-measured.

---

## #268 FOUND WHILE EXECUTING #167: the generated mockups had drifted from their generators

`mockups/build.py` regenerates eight pages from their generator modules. Running it after
editing `r_variants.py` and `common.py` rewrote **more than `#167` touched**: the embedded
payload picked up `displacement_adj` (`#216`), and the reworded `universal_value`,
`team_acquisition_value` and `rival_premium` help text (`#187`, `#207`). None of that is
`reach_label`.

So those pages had been stale since those items landed, because **nothing runs `build.py`** — not
a test, not CI, not a hook. A generated artifact that no process regenerates is a generated
artifact that silently becomes a lie about its own source, and these are the pages the owner
reads when judging a design. The `#167` commit carries the catch-up rather than deliberately
re-staling files the build says should be current.

Not fixed here, because the fix is a decision: either a test that regenerates into a temp dir and
diffs against the committed pages (fails the suite when someone edits a generator without
rebuilding), or an explicit ruling that these pages are frozen records like the nine round-1
pages already are, in which case `build.py` should stop rebuilding them. **The nine round-1 pages
are already handled correctly** — `build.py`'s own docstring exempts them as the scored record —
so the precedent for the second answer exists. This is the owner's call.

---

## #269 INSTRUMENT GAP, found while the noise arm was still running

`noise_arm.py` records **whether** the crossing fired and nothing about **why**. Its per-run
record is `{top_k, seed, n_picks, first_upside_pick, elapsed_s, opponent_noise}` — no
`positional_composition`, which the depth battery on the same question DOES record.

That matters now, because at 5 of 8 runs one arm fired and its twin did not:

```
k1_seed0   NEVER      (control -- no noise, same config as 12T_ppr_BN18)
k3_seed11  NEVER
k3_seed22  NEVER
k5_seed11  r17 p195   <- the only crossing this question has produced outside F&F
k5_seed22  NEVER
```

**n = 1 with its matched seed disagreeing, so this is an observation, not a result.** It is
recorded because the direction is counter-intuitive and worth a designed test rather than a
remembered anecdote: noisy opponents take WORSE players, which should leave the pool richer and
DELAY a crossing, not cause one.

A mechanism that would explain the inversion, stated so it can be refuted: replacement level is
**per-position**. Sharp opponents concentrate on whatever is most valuable and leave whole
positions untouched and still stocked above their floors; noisy ones spread consumption across
positions and walk several toward their floors at once. Under that account the crossing does not
detect "the pool is exhausted" at all — it detects **"consumption got spread out"**, which is a
materially different claim about what the rule means and would change whether it should be the
mode switch.

**Not tested here, and deliberately not tested by editing a live instrument.** The run was
mid-flight; changing its record shape would have produced two incompatible record formats in one
checkpoint and risked its resume path (`#215`, `#267`). The measurement is a targeted re-run of
the two `k5` seeds with `positional_composition` recorded, after the arm completes — cheap,
because it is 2 drafts and not 8.

**The general lesson, which is the part worth keeping:** the depth battery and the noise arm
answer the same question and record different things about it. An instrument that captures its
outcome but not the state that produced the outcome can only ever confirm or deny — it can never
explain, and the explaining is what a surprising result needs. Record parity between instruments
aimed at one question should be checked when the second one is written, not when it surprises you.

---

## #270 COMPLETE — the crossing rule fires or not depending on OPPONENT QUALITY, and the depth battery could never have seen it

The noise arm finished. `12T_ppr_BN18` held fixed — the same config the depth battery runs — with
`opponent_noise` making every non-sharp seat pick uniformly from its own top `k` candidates.

```
run          top_k  seed   crossing fires
k1_seed0         1     0   NEVER      <- control: no noise, all seats sharp
k3_seed11        3    11   NEVER
k3_seed22        3    22   NEVER
k5_seed11        5    11   r17 p195
k5_seed22        5    22   NEVER
k10_seed11      10    11   r16 p187
k10_seed22      10    22   r12 p142
```

**Seven runs, not eight, and the count is the instrument being right rather than short.** `k=1`
is the control and is DETERMINISTIC — drawing uniformly from the top 1 is the top 1 whatever the
seed — so a second seed at `k=1` would be a byte-identical re-run, exactly the duplicated arm
`#159` built a detector for. I reported "of 8" repeatedly during the run. That was my arithmetic,
not the script's.

### The result

**A monotone dose-response.** k=1 never; k=3 never in both seeds; k=5 fires in one of two; k=10
fires in both, and earlier. `k10_seed22` at **r12** beats the round rule's r15 — the crossing is
not merely reachable under noise, it can arrive *before* the fixed-round switch it was proposed
to replace.

Set beside the depth battery, which never fires the crossing anywhere from 168 to 360 picks with
every seat sharp, the reading is:

> **The crossing rule's behaviour is a property of the OPPONENTS, not of the league's depth.**

That is a hard limit on what a battery whose every seat is the engine can establish about this
rule, and the depth ladder's five straight `NEVER`s should be read in that light rather than as
"the crossing does not fire."

### CORRECTION — `#263b` has the sign backwards for the crossing

`#263b` recorded that every battery fire-round is a LOWER BOUND, reasoning that all-engine seats
drain the pool maximally efficiently and so would reach exhaustion soonest. **For the crossing
rule that is exactly wrong, and this data refutes it.** Sharp play is the case where the crossing
is LEAST likely, not most: efficient drafting concentrates on the most valuable players and
leaves whole positions still stocked above their own replacement levels, and `n_above` counts
across every position. All-engine is the conservative extreme in the opposite direction from the
one recorded.

`#263b` stands as written for the ROUND rule, which is a pick-count and cannot care how anyone
drafts.

### The mechanism is CONSISTENT with the spread account, and still NOT TESTED

`#269`'s proposal — noise spreads consumption across positions and walks several toward their
floors at once, where sharp play concentrates — predicts exactly this monotone shape. Seven runs
agreeing with a mechanism is not the mechanism measured. The noise arm still records no
`positional_composition` (`#269`), so the direct test remains a targeted re-run of the fired
seeds with composition captured. Cheap now: the arm is done and the question is two drafts wide.

---

## #271 OWNER-RAISED — one global upside switch over pools that drain at different rates

*"would it make more sense to have displayed pools be relative of upside modes specific to each
position, relative to their respective drain rates? not one universal that starts to modulate
some pools that are still deep. or at least separate out offensive upside mode and defensive."*

**The premise checks out in the code.** `use_upside` is a single boolean and `if use_upside:`
(`draft_room.py:3117`) transforms every row at once. But `_vor` is already measured against
PER-POSITION replacement levels, and the crossing test collapses all of it:

```python
not bool((pool.loc[measurable, "_vor"] > 0).any())
```

That `.any()` is a global OR. **One deep pool holds the entire board in balanced mode** — in a
12-team PPR, WR alone can keep QB, TE and the IDP tail balanced long after those are picked over.
The round rule errs from the other end, flipping pools that are still fat. Both current rules are
the same category of mistake: one switch for populations with very different drain rates.

**The per-position form is DERIVED, not invented** — group the `.any()` by position instead of
collapsing it. No new constant, no new threshold, nothing calibrated: it stops discarding
information the engine already computes, which is the `#56`-clean shape.

### Two things to establish before believing it

**It may change what the mode MEANS.** Upside mode is not a display choice: `#231`/`#232` found
it removes the displacement counterweight and hands TE a **+68.58 handicap at the flex**. Per
position, an upside-scored QB and a balanced-scored WR would sit in ONE ranked list — a
cross-mode comparison `universal_value`'s contract has never had to answer, adjacent to `#229`'s
domain ruling (cross-position VOR authorized; the anchor keys the domain). Possibly sound,
possibly a unit collision. Not assumable either way.

**Offence/defence is the safer first cut, on grounds beyond drain rate.** IDP and K/DEF differ
from offence in DATA SUPPLY, not only depth — `#210` (Sleeper supplies IDP with no stat lines),
`#80` (K loses `proj_3yr` entirely). Those pools behave differently because less is known about
them, which justifies a split without first settling the per-position math, and with a far
smaller blast radius.

**Measure it against NOISY opponents.** Per `#270`, a variant judged against all-engine seats
would look inert for the same reason the global crossing looked inert.

---

## #272 CAPTURED — FFCL Group A, the first real league that is not a near-twin of the other two

`data/league_captures/ffcl_group_a.json`. Rulebook only, no draft board — the rulebook is the
half that carries the coverage.

### It breaks five axes that were constant across both existing captures

| axis | Fourth and Forever | Greatest Show on Paper 2 | **FFCL Group A** |
|---|---|---|---|
| horizon | dynasty | dynasty | **redraft** |
| bench | 11 | 14 | **5** |
| taxi | 5 | 5 | **none** |
| dedicated TE slot | yes | yes | **NONE** |
| offbrand flex | no | no | **WRRB_FLEX** |
| trading | yes | yes (82/360 picks moved) | **FORBIDDEN by rule** |

**The two prior captures were near-twins.** Identical starters —
`QB/RB/RB/WR/WR/TE/FLEX×3/SUPER_FLEX` — differing only in bench and IR depth. As evidence about
roster STRUCTURE they were closer to one data point than two. This is the first genuinely
different shape, and it lands on `#261`'s bench-depth concern and `#265`'s draft-type concern
from a direction neither anticipated.

**It also makes `#146` actionable.** That item — *bye week IS admissible when the asset horizon
is one season* — has sat REDRAFT-ONLY with no redraft league to apply it to. Now there is one.

### The no-TE-slot case, which is why it was captured

Starters: `QB · RB · RB · WR · WR · FLEX · FLEX · WRRB_FLEX · SUPER_FLEX`. K Pitts (TE) is
started **in a FLEX**; D Kincaid (TE) sits on the bench. **A startable position with no slot of
its own.** Sleeper's filter-tag rule generates a FLEX tag and no TE tag here; ours
(`position_view_options`) would offer a standalone TE view, because our test is *is this position
present among the candidates* rather than *does this league have a slot for it*. First real
instance of that divergence.

### THE TRADING BAN IS THE FINDING I DID NOT EXPECT

Forbidden for fairness across the six pods. Three consequences:

**It is the control case for a real measurement.** GSOP2: 82 of 360 picks (22.8%) made by
someone other than the slot owner. Here: zero, by rule.

**Pick order is REGULAR.** In GSOP2 one manager's gaps between consecutive picks ran
`16, 10, 2, 24, 7, 17, 7, 10, 9, 1, 21, 7, 1` — chaotic *because picks moved*. A no-trade
12-team snake gives clean alternating ~2 / ~22. **`intervening_picks` is predictable here and
unpredictable there**, and that bounds a UI claim: `DRAFT_ROOM_UI.md` §2 argued the rail's
next-turn marker is load-bearing partly because a person cannot know when their next pick is.
True in a trading league, much weaker here. §2 now carries that bound.

**THE SIMULATOR MATCHES THIS LEAGUE EXACTLY.** `simulate_full_draft` does not trade picks.
Against F&F and GSOP2 that has always been an unstated approximation — both allow trading.
Against FFCL Group A it is not an approximation, it is the rule. **This is the first captured
league the draft simulator represents without that caveat**, which makes it the best available
target for any claim the battery wants to make about a real league.

### What is read, what is inferred, and the one thing that stays unverified

**Read:** all 42 scoring labels and values, across five screenshots with deliberate overlap; the
slot badges and their occupants; the header `2026 12-Team SF PPR TEP`.

**Inferred and then CONFIRMED by the owner:** bench = 5, IR = 2. The screenshot reasoning agreed
independently — Sleeper's TEAM view renders empty slots (both IR rows read "Empty"), so a sixth
bench slot would have shown as an empty BN row, and none does.

**Recorded as absence, not dropped:** `pts_allow_21_27` never appears — the band jumps 14-20 (+1)
to 28-34 (-1). Sleeper omits zero-valued settings from that screen, so it is presumed 0. GSOP2's
capture has the identical gap.

**UNVERIFIED, and flagged in the file:** the mapping from each DISPLAY LABEL to its Sleeper
`scoring_settings` KEY. Keys follow GSOP2's convention. The authoritative source is the league's
own JSON from the API, which this environment cannot reach (`#143`). `#212`/`#213` is the
standing warning — a key-mapping error has already scored an entire battery against a one-key
rulebook.

### A caution about treating these captures as independent

Against GSOP2, this league differs in **exactly two scoring values** — `pass_td` (4 vs 5) and
`bonus_rec_te` (0.50 vs 0.75). The other ~30 are byte-identical, because they are Sleeper's
defaults. **The captures carry almost no independent information about that default block, and
agreement there must never be read as corroboration.** They differ where a commissioner actually
chooses and agree everywhere a commissioner does not.

### Not wired

This is DATA. The battery reads `fixtures/sleeper_capture.json` (`#241`), not
`data/league_captures/`. Adding an arm from this shape is a separate decision, and `#265` already
records that whether to add roster-shape axes to `league_matrix` is the owner's call.

### `#272` addendum — it is 3RR, and that makes `#265` sharper than it was

The owner added the draft type after the capture was written: **third-round reversal.**

**`#265` recorded that the 34-arm battery never varies draft type, on the strength of one real
3RR league. It is now two of two.** Greatest Show on Paper 2 is 3RR (verified against its
transcribed board — round shapes r1-r6 run asc/desc/desc/asc/desc/asc, which naive snake fails
and third-round-reversal passes). FFCL Group A is 3RR by the owner's statement. Fourth and
Forever's draft type is **not recorded anywhere**. So of the real leagues whose draft type we
actually know, **3RR is 2 of 2, while all 34 battery arms run plain snake.**

**A second, smaller finding underneath it: the capture FORMAT was missing the field.** Neither
existing rulebook capture records `draft_type`. GSOP2's 3RR lives in its BOARD EXTRACT, not its
rulebook; F&F's is absent entirely. A rulebook that cannot state its own draft type cannot answer
the question `#265` asks, so `ffcl_group_a.json` is the first capture to carry `draft_type` as a
field — and backfilling the other two is a small, obvious follow-up (GSOP2's answer is already
known; F&F's would need looking up).

**And this one is a REDRAFT using 3RR**, where 3RR is normally a startup/dynasty balancing
convention. Consistent with the same fairness concern that bans trading across the six pods.

`generate_pick_order(round_1_order, total_rounds, draft_type="snake"|"linear"|"3rr")` already
implements it and Sleeper exposes it as `settings.reversal_round == 3`, so the capability is not
the gap — the matrix simply never uses it.

### `#272` CORRECTION — the owner had already given me this league, six days ago

The owner said, of the FFCL Group A material: *"i cant help but think i'd have given this to
you before, though."* **They are right, and I should have checked before writing the entry
above rather than after.**

**Where it was.** `evidence/reference_rosters/OWNER_REDRAFT_2026-09-08.md`, committed
2026-09-08 at `d79ea96` — *"Reference roster: a human-drafted roster the owner is happy with,
and the inputs it proves missing."* The commit message itself reads: *"no dedicated TE slot,
W-R-only flex, superflex, 5-bench, 3RR, seat 12, redraft, NO TRADING."* Every axis the entry
above presents as newly captured.

**Why I did not find it.** That commit is on `ui-authority-pass`. It is **not an ancestor of
this branch and not an ancestor of `main`** (`git merge-base --is-ancestor` says NO to both),
so the file does not exist in this working tree. Every search I ran — the working tree, the
git object grep for "ffcl", the board corpus — was run against a tree the evidence is not in.
The 09-08 document is now restored to this branch with an identification block appended.

**It was never anonymous to the instruments, only to me.** The league is already an arm:
`run_216_bench_probe.py:280`, `OWNER_LEAGUE` / label `OWNER_3RR_SF_noTE`, and
`OWNER_LEAGUE_FIXTURE_WITHDRAWAL.md` — the *twelfth* withdrawal of that session — is the
record of me declaring that same fixture broken by comparing it against the wrong league.
**This is the same error twice, six days apart, on the same artifact.** There: a correct
fixture matched against the wrong reference. Here: the right reference searched for in the
wrong tree. Both times the artifact's own label carried the answer (`OWNER_3RR_SF_noTE`
states three of the eight fields outright).

#### What actually survives, and what does not

**The eight format fields agree exactly** — starters, bench, teams, `rec`, `bonus_rec_te`,
horizon, `draft_type`, trading. Zero conflicts. The capture is corroborated, not contradicted.

**The comparison table above stands as written**, because every claim in it is scoped to
`data/league_captures/` — "no other *capture*", "the first *captured* league". That scoping
happens to be literally true. It was not deliberate, and it reads as a novelty claim about the
repo, which it is not.

**These three claims in the entry above are WITHDRAWN or corrected:**

1. **"THE TRADING BAN IS THE FINDING I DID NOT EXPECT" — withdrawn.** The 09-08 document
   contains a longer and better version of it, under its own heading *"NO TRADING — and what
   it does to the engine's objective"*, including the bench-taxonomy consequence, the
   inert-surplus consequence, the conditional-G9 consequence, handcuffs being worth more,
   replacement level becoming literally true, **and** the codebase finding that
   `league_format.py:9` flagged the missing trades-enabled input in a comment and it never
   became one. I re-derived it and presented it as a surprise. It is a **re-finding**, and the
   09-08 write-up is the better of the two.

2. **"Rulebook only, no draft board" — stale.** The owner supplied the FFCL Group A draft
   board the same day. The 09-08 document additionally carries all fourteen of the owner's own
   picks with round-by-round notes, which no capture has for any league.

3. **The `#146` claim needs one qualifier.** *"has sat REDRAFT-ONLY with no redraft league to
   apply it to"* — there has been a documented redraft league since 09-08. What was missing
   was its **scoring rulebook**, without which bye-week admissibility cannot be evaluated
   against real point values. The capture supplies that; it does not supply the league.

#### `#265` is sharper than the addendum said, in the engine's favour

The addendum wrote *"all 34 battery arms run plain snake"*, which is true, and left the
impression that nothing in the repo exercises 3RR. **One instrument does.**
`run_216_bench_probe.py` drafts this league with `draft_type="3rr"` — `build_league` returns
`OWNER_LEAGUE["draft_type"]` on that branch and the literal `"snake"` on both others. So the
gap is narrower and more specific than recorded: **the 34-arm battery is 3RR-naive; the
flex-share and shared-slot instruments are not.** That also means `OWNER_3RR_SF_noTE`'s
existing results are results about a real, named league drafted under its real draft type —
which raises their standing, not lowers it.

---

## `#273` PROCESS DEFECT — evidence pinned to a branch that never merged is evidence the next session cannot find

`#272`'s correction is not a one-off. It is the failure mode `evidence/real_drafts/README.md`
was written to prevent, in a different medium: *"161 images had been pasted into this session
and were living only inside a 591 MB conversation transcript... Nothing pointed at them."*
Here nothing pointed at a committed, pushed file either, because it was committed to a branch
that never reached `main` or the working branch.

### Measured, not assumed — the orphan set is exactly two files

Swept every branch (`origin/main`, `origin/ui-authority-pass`, `origin/pre-blind-audit`,
`origin/pre-hull-extraction`, `adversary-216-falsification`, both `origin/worktree-agent-*`)
for paths absent from `HEAD`, excluding `.claude/worktrees/`:

| branch | files absent from HEAD |
|---|---|
| `origin/main` | 0 |
| `origin/pre-blind-audit` | 0 |
| `origin/pre-hull-extraction` | 0 |
| `adversary-216-falsification` | 0 |
| `origin/worktree-agent-a0a78a88e2d0163fe` | 0 |
| `origin/worktree-agent-ab5e1af412aeb9182` | 0 |
| **`origin/ui-authority-pass`** | **2** |

The two: `evidence/reference_rosters/OWNER_REDRAFT_2026-09-08.md` and `HANDOFF_216.md`.

**This is a bounded problem, and it is now one file.** The reference roster is restored to
this branch by this commit. `HANDOFF_216.md` is deliberately NOT restored: it is a
present-tense status document from 09-08 (*"#216 BLOCKS THE FREEZE"*, a branch table naming
worktrees that have since been absorbed), and dropping it at the repo root would put stale
current-tense state where a reader would take it as live. It is recorded here instead —
`git show origin/ui-authority-pass:HANDOFF_216.md` — which is the whole point of the entry.

Its opening line, for the record, is *"Everything named here is committed and pushed. Nothing
important lives only in a container."* Both sentences were true. Neither was sufficient.

### The rule this yields

**"Committed and pushed" is not the durability bar. "Reachable from the branch the next
session checks out" is.** A branch that is not an ancestor of `main` is a container with a
longer lifetime, not a different kind of thing. Evidence intended to outlive a session belongs
on a merged line, or it belongs nowhere.

The mechanical check is one command and is cheap enough to run before declaring any search
exhaustive:

```
comm -13 <(git ls-tree -r --name-only HEAD | sort) \
         <(git ls-tree -r --name-only <branch> | sort)
```

**`#161` is the near neighbour**, not a duplicate: there I searched full history and correctly
found that no `BLIND-A1` existed. Here I searched one tree and incorrectly concluded no FFCL
material existed. The difference is entirely which of the two I searched, and I did not notice
I had chosen.

---

## `#274` MECHANISM CLOSED — the global crossing rule is a TIGHT END DETECTOR

`#271` left two things unexplained: bench depth moves the crossing not at all, and team count
moves it non-monotonically. `evidence/mode_boundary/crossing_mechanism.py` replays the exact
pick sequences `#271` recorded and rebuilds the board at every 5th prefix, reading the rule's
own quantity off the exported column.

**Why `bpa` is the rule's quantity and not a proxy for it:** the rule tests
`not (pool.loc[measurable, "_vor"] > 0).any()` (`draft_room.py:3115`) on an internal column,
but `_scale_vor_to_bpa` is the IDENTITY (`return vor.astype(float)`, `draft_room.py:2105`) since
`#74`/`#76` removed the moving ruler. Same values, NaN passed through. Read from source.

**The probe checks itself.** It restates the rule on an exported column; `#271` detected firing
from the engine's own `growth_signal`. They must agree or the probe is wrong:

| arm | `#271` | probe | verdict |
|---|---|---|---|
| 8T_ppr_BN18 | NEVER | NEVER | ok |
| 10T_ppr_BN18 | 231 | 230 | ok (stride 5) |
| 12T_ppr_BN18 | NEVER | NEVER | ok |
| 14T_ppr_BN18 | NEVER | NEVER | ok |

4 of 4. No new drafts were simulated — deliberately, because a fresh simulation is a DIFFERENT
draft (the engine's picks depend on the board it is shown), and "why did THIS draft not fire"
cannot be answered on a draft that is not that one.

### The answer: every position crosses zero early except TE, and the global rule waits for TE

First pick at which each position's own best remaining player falls to or below its replacement
level:

| arm | picks | QB | RB | WR | **TE** | global rule |
|---|---|---|---|---|---|---|
| 8T_ppr_BN18 | 208 | 55 | 75 | 55 | **NEVER** | NEVER |
| 10T_ppr_BN18 | 260 | 70 | 135 | 70 | **230** | **230** |
| 12T_ppr_BN18 | 312 | 85 | 185 | 85 | **NEVER** | NEVER |
| 14T_ppr_BN18 | 364 | 85 | NEVER | 100 | **NEVER** | NEVER |

**The global column is the TE column.** In the one arm that fires, it fires at the pick TE
crosses and not one sample earlier. In the three that never fire, TE is the position that never
crosses. QB and WR were below replacement from picks 55-100 in every arm — a third of the way
in — and the board stayed in balanced mode for the remaining two hundred picks.

So `not (_vor > 0).any()` does not mean *the board is exhausted*. It means **even tight end is
exhausted**, and the whole rule is hostage to the single most anomalous position on it.

### TE's VOR does not decay toward zero. It REBOUNDS, repeatedly

Top remaining TE VOR, sampled every 40 picks:

```
  8T   121 → 27 → 12 →  5 → 18 → 11
 12T   137 → 58 → 17 → 28 → 30 → 13 → 15 →  8
 14T   159 → 75 → 33 → 35 → 47 → 11 → 19 → 11 →  6 → 13
```

It approaches zero and then climbs back, more than once per draft. This is not noise and it is
not a surprise — `replacement_levels`' own docstring predicts it: *"a BENCH pick at a position
drains the pool without reducing any team's starter demand, so it moves the level."* Every
bench-depth TE taken lowers the replacement TE faster than it lowers the best remaining TE, so
the gap between them WIDENS. `#216` measured the same effect from the other side (the WR-TE
level gap opening 43.6 → 59.3 on a TE-hoarding seat).

### Which inverts `#261`'s premise rather than merely nulling it

`#261` reasoned that a deeper bench would reach the crossing. **Extra bench rounds are extra
bench picks, and bench picks are the exact mechanism that pushes TE's VOR back UP.** Depth does
not fail to approach the crossing; it actively defers it. `#271`'s six-arm null had the right
sign all along and nobody could read it.

The non-monotonic team-count result needs no separate explanation once this is in hand: the rule
demands four positions be simultaneously non-positive, one of which oscillates across zero. That
is an alignment coincidence, not a threshold, and coincidences are not ordered in team count. 10T
caught TE on a downswing at pick 230 while the other three had been negative for 95 picks.

### What this does and does not license

**It does NOT license "fix the crossing rule."** The rule faithfully reports the quantity it was
asked about; the quantity is the problem, and repairing it is Phase 3 territory (`#50`,
`#147`), not a mode-switch patch.

**It DOES settle the per-position question the owner raised independently** — see
`DRAFT_ROOM_UI.md` §13. Per-position upside grading is not a refinement of the global switch.
The global switch is a defect, and per-position grading is the repair.

**One thing to test before anyone builds on the TE account:** every arm here is `te_premium=False`
1QB PPR. TE's behaviour is exactly what a TE-premium or no-TE-slot league would change most, and
FFCL Group A is both (0.5 TEP, no dedicated TE slot). That arm is cheap now — the instrument
takes 20s per league — and it is the obvious next measurement, NOT a claim this entry makes.

### `#274` SCOPE CORRECTION (27th withdrawal) — "tight end detector" is WRONG as a general claim

The FFCL Group A arm was named in `#274` as the case that could scope the finding. It did. The
structural half survives; **the attribution to tight end does not, and I am withdrawing it.**

`evidence/mode_boundary/crossing_ffcl.py` — FFCL Group A's real rulebook (12 teams, 9 starters
+ 5 bench = 14 rounds = 168 picks, matching the real board exactly), superflex, **0.5 TE premium,
no dedicated TE slot**, 3RR. Self-check passes: engine `growth_signal` NEVER, probe NEVER.

| league | QB | RB | WR | TE | global |
|---|---|---|---|---|---|
| 12T, dedicated TE slot, 1QB (control) | 85 | 185 | 85 | **never** | never |
| **FFCL Group A**, no TE slot, superflex | **never**\* | **never** | 115 | **90** | never |

> **\* CORRECTED by `#277` (29th withdrawal) — FFCL's QB is NOT a holdout.** It is
> DEMAND-EXHAUSTED: by the final pick QB has `measurable=0`, `top=None`,
> `remaining_starter_demand=0.0`. Once all 24 QB slots (12 teams x QB + SUPER_FLEX) are filled,
> the position leaves `replacement_levels`' domain, no VOR is computed, and its rows drop out of
> the `measurable` mask entirely. RB is FFCL's only genuine holdout (`measurable=82`,
> `top=20.9`, `demand=3.08`). **Rendering both as "never" collapsed two different absences into
> one token — the exact failure this engine's absence contract exists to prevent, committed by
> me in the correction that was supposed to be the careful one.** The sentence below overstates
> it the same way and is left standing with this banner rather than edited away.

**The holdout position inverts completely.** In the control TE is the one position that never
crosses. In FFCL tight end is the FIRST to cross — at pick 90 of 168, barely past halfway — and
**quarterback and running back are the positions that never cross at all.**

Trajectories, every 20 picks:

```
 QB  148 → 123 →  98 →  91 →  80 →  63 →  39 →   8 →   --
 TE  113 → 113 →  54 →  32 →   9 → -30 → -39 → -68 → -108
```

QB never goes negative; TE is deeply negative from pick 100 on. That is the mirror image of the
four arms `#274` was written from.

**Why, and it is the same mechanism pointing the other way.** The rank target is league starter
demand. Superflex doubles QB demand, so QB's replacement sits far deeper down the curve and the
gap above it stays large. No dedicated TE slot means TE demand arrives only through the flex, so
TE's replacement is shallow and the gap closes early. **The holdout is whichever position the
ROSTER SHAPE starves of demand relative to its supply — and roster shape decides which one.**
The four arms that produced the TE account all shared one roster shape; TE was a property of
that shape, not of the position.

#### What survives, and is stronger for the correction

**The structural finding is confirmed twice, on opposite shapes.** Per-position crossings are
widely separated, the global `.any()` collapses them into one bit, and the board stays in
balanced mode long after most positions are drained. In the control, QB and WR were done at 85 of
312. In FFCL, TE was done at 90 and WR at 115 of 168 — and the global rule never fired in either.

**The `#261` inversion survives.** Bench picks still move the level in the hoarded position's
favour; that is a property of `replacement_levels`, not of TE.

**The per-position case (`DRAFT_ROOM_UI.md` §13) gets STRONGER, not weaker.** If the holdout
were always TE, a single special case would do. It is not: **which position is starved is a
per-league fact**, so nothing short of reading the per-position levels can tell a drafter what is
actually exhausted. The mixer's channel strips are not a nicer rendering of a global number —
they are the only correct instrument, and the §13 TE-meter warning must be reworded as *the
holdout channel*, whichever it is in this league.

**One observation NOT claimed as a finding:** FFCL's QB column reads `--` (nothing measurable) by
pick 160 — every remaining QB unpriced rather than below replacement. That is the `#171`
floor-clearing regime and it is why the rule's two-zeros guard exists. Noted, not interpreted.

---

## `#275` PROCESS DEFECT — I pushed `9ae95a1` citing a suite that finished BEFORE the file it added

`test_doc_index_is_not_stale` failed in this pass. The stale entry was
`evidence/reference_rosters/OWNER_REDRAFT_2026-09-08.md`, restored in `9ae95a1` — **two commits
before the work that surfaced the failure.** `DOC_INDEX.md` indexes markdown, so adding a `.md`
file is a change the suite covers, and adding one invalidates the index.

`9ae95a1`'s message says *"Docs only, no code touched. Full suite green at this code state: 2924
tests, OK (skipped=1)."* Both halves are individually true and the conclusion is still wrong:
**that suite finished before the commit added its file.** I treated "no code touched" as meaning
"the suite cannot be affected", and `doc_index` is the counterexample sitting in the suite for
exactly this reason.

So `9ae95a1` was pushed red and nobody would have known until the next full run. The standing
rule — *the full suite licenses a push* — was followed in letter and broken in substance, because
the suite I cited was not a suite OF that commit.

**The rule this sharpens:** a green suite licenses the tree that PRODUCED it, not the tree as it
stands when you push. If the working tree changed after the run — including by adding a markdown
file — the licence has lapsed. "Docs only" is not an exemption; this repository deliberately has
tests that read documents (`doc_index`, `assertion_floors`, the no-reader guards).

Related to `#169`, and the same family: both are cases of a commit being blessed by a check that
was not actually about it.

---

## `#276` CORRECTION TO `#271` (28th withdrawal) — ladder A is ONE draft truncated six ways, not six arms

Extending `#274`'s probe to all ten recorded drafts produced a result that looked like a clean
confirmation and is actually a deflation of the evidence underneath it. Caught before it was
published, which is the only reason it is a withdrawn PREDICTION rather than a withdrawn claim.

### What it looked like

Six 12-team leagues differing only in bench depth, probed per position:

| arm | picks | QB | RB | WR | TE |
|---|---|---|---|---|---|
| 12T_ppr_BN6 | 168 | 85 | never | 85 | never |
| 12T_ppr_BN10 | 216 | 85 | 185 | 85 | never |
| 12T_ppr_BN14 | 264 | 85 | 185 | 85 | never |
| 12T_ppr_BN18 | 312 | 85 | 185 | 85 | never |
| 12T_ppr_BN22 | 360 | 85 | 185 | 85 | never |
| 12T_ppr_BN26 | 408 | 85 | 185 | 85 | never |

QB at 85 and WR at 85 in all six; TE never in all six; RB at 185 in five. I had pre-registered
this in `crossing_mechanism.py`: *"six leagues that differ only in bench depth must all share
one holdout, and that is a real prediction."*

### `#245` says identical numbers are a broken instrument until proven otherwise, so I checked

**The six drafts are byte-identical over their entire overlap.** BN6's 168 picks are a strict
prefix of BN10's 216, which is a prefix of BN14's, and so on to BN26's 408. Divergence pick:
**none, in any pair.** Verified separately that the six leagues differ ONLY in `BN` count —
identical starters (`QB RB RB WR WR TE FLEX FLEX`), scoring, team count and every other key.

So the six arms are **one 408-pick draft, sampled at six lengths.**

### Three consequences, in increasing order of importance

**1. My prediction was untestable.** On nested prefixes it cannot fail — the arms are reading
the same draft. A confirmation that could not have come out any other way is not evidence, and
I would have reported it as the decisive one. WITHDRAWN before publication.

**2. `#271`'s ladder-A null is ONE observation, not six.** That entry says *"Bench 6 to bench 26
— 168 to 408 picks, a 2.4x span on the one axis `#261` predicted would matter — and the crossing
fires in none of the six."* The span is real; **"none of the six" overstates the evidence
sixfold.** It is one draft that never fires, checked at six lengths. `#271`'s CONCLUSION survives
— bench depth does not move the crossing — but it rests on one arm, and the entry should be read
that way. The `#274` mechanism is unaffected: it rests on ladder B (four genuinely different
leagues) and FFCL, none of which are prefix-nested.

**3. THE POSITIVE FINDING, which is bigger than the correction.** Adding twenty bench slots
changed **zero of 408 picks**. Not "little": zero. That is a direct empirical confirmation of
`#115` — *bench capacity is not an engine input* — which `#115` recorded as a behavioural
coverage gap with no measurement behind it. There is now one, on real drafts, and it is total.
It also explains `#271`'s null completely and trivially: bench depth cannot move the crossing
because bench depth moves nothing at all.

### A THIRD HOLE IN THE DUPLICATE-ARM DETECTOR FAMILY, and it is the same kind

`draft_battery` already carries two derived self-checks, and this slipped past both:

- `duplicate_arms` compares each arm's ENTIRE measured body for byte identity. These arms have
  different lengths and different totals, so **nothing is flagged.**
- `format_axes_exercised` catches an axis that stops varying. The bench axis genuinely varies
  (6→26), so **nothing is flagged.**

**Neither can see NESTED PREFIXES** — an arm whose entire measured content is a prefix of
another's. That is `#159`'s defect class in a shape its detector cannot express, and
`format_axes_exercised`' own docstring already frames the family correctly: *"an axis can stop
varying without any arm becoming a duplicate, and nothing else in the report would say so."*
Here an axis varies, no arm is a duplicate, and the arms are still not independent evidence.

`depth_battery.py` does not call either detector, which is the proximate reason this reached a
published entry. The remedy is a prefix detector in the same derived style — compare recorded
pick sequences, flag any arm that is a prefix of another — plus having the depth battery run the
detectors it already has. Filed as work, not done in this entry: **evidence before repair**
(`#162`).

### Why bench depth changes nothing, stated as a question rather than an answer

`build_mock_league` appends `BN` slots and `draftable_slots` turns them into rounds, so the
DRAFT gets longer while every scoring input stays fixed. Whether that is correct is a real
question — a 26-slot bench plausibly SHOULD change how a manager values depth, and `#224`
characterised two `bench_capacity` quantities that exist. Whether either reaches a pick is not
measured here and is not claimed.

---

## `#277` AXIS DECOMPOSITION — the dedicated TE slot is the whole story, and slots beat scoring

`evidence/mode_boundary/crossing_matrix.py`, six arms simulated and probed under the crossing
rule, against the pre-registered predictions committed at `45bcbeb` BEFORE the run finished.
All six self-check ok (engine `growth_signal` and probe agree).

| arm | picks | SF | TE slot | tep | QB | RB | WR | TE | holdout(s) | global |
|---|---|---|---|---|---|---|---|---|---|---|
| `12T_ppr` (control) | 168 | 0 | yes | 0 | 85 | never | 85 | never | RB, TE | NEVER |
| `12T_ppr_SF` | 180 | 1 | yes | 0 | **160** | 165 | 95 | never | TE | NEVER |
| `12T_ppr_TEP_dynasty` | 168 | 0 | yes | 0.5 | 85 | never | 90 | never | RB, TE | NEVER |
| `4WR_TE_PREMIUM` | 192 | 0 | yes | 0.5 | 110 | 125 | **135** | never | TE | NEVER |
| `LIGHT_IDP` | 168 | 0 | yes | 0 | 75 | never | 90 | never | DB, DL, RB, TE | NEVER |
| `HEAVY_IDP` | 216 | 0 | yes | 0 | 135 | never | 155 | never | RB, TE | NEVER |

### TE is the holdout in 16 of 16 leagues that have a TE slot

Six arms here plus the ten in `crossing_mechanism.json`. **Every one.** And every "never" was
audited to distinguish a real holdout from an absent measurement — all sixteen are genuine
(measurable rows, positive top, demand above 1). **The only league where TE is not the holdout
is FFCL Group A, the only one with no dedicated TE slot**, where TE crosses FIRST at pick 90.

Five axes were tested against it and **none moves TE off holdout**: superflex, TE premium, a
fourth WR slot, light IDP, heavy IDP — and bench depth from `#276`. `#274`'s "roster shape"
account is therefore correct but far too broad. The operative axis is one thing: **whether the
league has a dedicated TE slot.**

### THE MECHANISM, now isolated: STARTER SLOTS set the crossing order; SCORING does not

Each slot change moves its own position later and the others earlier, exactly as league starter
demand predicts:

- **+SUPER_FLEX** (QB demand x2): QB `85 -> 160`, nearly doubled.
- **+a fourth WR slot**: WR `85 -> 135`.
- **+0.5 TE premium** (scoring only, no slot change): QB `85 -> 85`, WR `85 -> 90`. **Inert.**

A scoring bonus raises a position's points AND its replacement's points together, so the gap
barely moves. A slot raises demand, which pushes the replacement RANK deeper down the curve,
which is what actually holds the gap open. That is why a TE slot — 12 units of demand against a
"two players and a cliff" supply curve — keeps TE above replacement for an entire draft, and why
removing it collapses TE immediately.

### The three pre-registered predictions: 1 REFUTED, 1 CONFIRMED WEAKLY, 1 REFUTED

**1. REFUTED.** *"12T_ppr_SF's holdout is QB; if superflex alone flips it, the no-TE-slot axis is
not needed to explain FFCL."* It does not flip. QB moves 85 -> 160 — the predicted direction, and
a large effect — but still crosses. Superflex is a large contributor and NOT a sufficient cause.

**2. CONFIRMED, but weaker than stated.** TE stays the holdout under a premium. The prediction
added "possibly harder"; the measurement shows the premium does essentially nothing to any
crossing. Recorded as near-inert rather than dressed up as a confirmation.

**3. REFUTED, and this is good news.** I predicted IDP rows might be UNPRICEABLE rather than
above replacement, on the strength of `#210` (Sleeper supplies IDP without stat lines). Both IDP
arms report **`never-priceable (none)`** — every IDP position is priced, and DB/DL/LB cross
normally (140/145/145 in HEAVY, LB at 90 in LIGHT). **This does NOT close `#210`**: it says the
supply defect does not manifest as unpriceable rows in these arms, not that it is gone.

### `#277a` (29th withdrawal) — FFCL's QB is DEMAND-EXHAUSTED, not a holdout

Auditing every "never" for the difference between *held above replacement* and *no measurement
exists* caught my own `#274` correction rendering two different absences as one token:

```
FFCL final state   QB: measurable=0   top=None   demand=0.0     <- left the domain
                   RB: measurable=82  top=20.9   demand=3.08    <- genuine holdout
```

Once all 24 QB slots (12 teams x QB + SUPER_FLEX) fill, QB's remaining starter demand reaches
zero, the position is OMITTED from `replacement_levels` by its documented domain rule, no VOR is
computed, and its rows leave the `measurable` mask. **FFCL has one holdout, not two.** The
`#274` table and `DRAFT_ROOM_UI` §13 are both corrected in place with banners rather than edited
away. This is the absence contract — EXCLUDE / PROPAGATE / ORDER LAST, `None` never `0.0` —
broken by me in the entry that existed to be the careful correction.

**It also explains FFCL's QB without appeal to superflex holding out**: superflex does not keep
QB above replacement forever, it fills QB demand twice as fast and the position simply runs out.

### `#277b` — the matrix CONTROL duplicates a depth arm, caught by `#276`'s own lesson

`12T_ppr` (matrix) and `12T_ppr_BN6` (depth) are the same league: 168 picks, identical crossings,
and **all 34 sampled boards byte-identical**. So this run has **5 independent arms, not 6**, and
the control is a re-derivation rather than a new observation. It costs nothing here — the control
is meant to reproduce the baseline and did — but it is the same class `#276` registered, found
one run later, and it is named rather than left for a reader to notice.

### What this leaves open

The FFCL inversion is now attributed to the TE slot by ELIMINATION across five other axes, not by
a direct test. The direct test is a mock league identical to the control with the TE slot removed
and nothing else changed. `build_mock_league` does not expose that, so it needs a small arm of its
own — named as the next measurement, not assumed.

---

## `#278` DIRECT TEST — remove the TE slot and the crossing rule FIRES. `#277` survives its own strongest test

`#277` closed by naming its own weakness: the TE-slot attribution came from ELIMINATING five
axes, never from removing the slot and watching. `evidence/mode_boundary/crossing_matrix.py`
arm `12T_ppr_NO_TE_SLOT`, with the prediction committed at `d69cd11` BEFORE the run finished.

### The arm: one slot changed, everything else held byte-identical

```
control : QB RB RB WR WR TE   FLEX FLEX
arm     : QB RB RB WR WR FLEX FLEX FLEX
verified before running: rounds 14 = 14 · bench identical · scoring identical · slot count identical
```

**TE → FLEX, not TE → nothing.** Deleting the slot would move the starter count 8 → 7 and with
it rounds, pick total, and every other position's share — four axes to test one, the exact
confound `#277` existed to escape. The swap moves only where tight-end demand LIVES: out of a
dedicated slot and into the shared pool. It is also not an invented shape; FFCL Group A is
`FLEX FLEX WRRB_FLEX SUPER_FLEX` with no TE, so this is that league's distinguishing feature in
isolation.

### The result

| arm | picks | QB | RB | WR | TE | holdout | **global rule** |
|---|---|---|---|---|---|---|---|
| `12T_ppr` (TE slot) | 168 | 85 | never | 85 | never | RB, TE | **NEVER** |
| `12T_ppr_NO_TE_SLOT` | 168 | 80 | 155 | 85 | **120** | **none** | **FIRES at 155** |

**Prediction confirmed, and more strongly than it was stated.** TE stops holding out — it crosses
at 120. So does RB. **No position holds out at all, and the global crossing rule fires at pick
155 of 168.** Self-check agrees independently: the engine's own `growth_signal` detector reports
round 13 / pick 152 against the probe's 155 on a stride of 5.

### The mechanism, visible in one trajectory

Top remaining TE VOR, every 20 picks:

```
with TE slot   137 → 93 → 58 → 24 → 17 → 22 → 28 → 20 → 30     bottoms out, REBOUNDS, never dies
no TE slot     120 → 120 → 75 → 41 → 26 →  7 →  0 →  0 →  0     decays to zero and PINS there
```

With a dedicated slot, TE's headroom bottoms near 17 and climbs back — the bench-pick effect
`#276` identified, where a bench TE drops the replacement faster than the best-remaining and
WIDENS the gap. Move that demand into the shared flex pool and the rebound vanishes entirely.

### What this upgrades

**`#277`'s conclusion is no longer by elimination.** The dedicated TE slot is now directly
demonstrated as the operative axis, on a controlled A/B rather than a five-way exclusion.

**And it is bigger than `#277` claimed.** `#277` said the TE slot decides WHICH position holds
out. This says the TE slot is **the single reason the crossing rule never fires at all**. This is
the first SYNTHETIC arm in the whole investigation to fire other than `10T_ppr_BN18` (pick 231),
and unlike that one it is a controlled comparison, not an unexplained coincidence.

**It also retro-explains FFCL without a second story.** FFCL has no TE slot and its TE crossed
first, at 90 — the same signature. Its global rule still did not fire, but now for an IDENTIFIED
reason (`#277a`: QB demand-exhausting out of the measurable set), not an unexplained holdout.

### What it does NOT establish

The arm is 12-team, 1QB, PPR, no premium. It shows the TE slot is SUFFICIENT to prevent firing
in that shape; it does not show it is the only such mechanism, and the interaction with superflex
(which moved QB 85 → 160 on its own) is untested in combination. Named, not assumed.

**Nothing here licenses changing the rule.** The crossing test faithfully reports the quantity it
is given; that the quantity is hostage to one roster slot is a property of `replacement_levels`'
starter-demand model, and repairing it is Phase 3 (`#50`, `#147`).

---

## `#279` PROCESS NOTE — I killed my own analysis with a self-matching `pkill`

Running `pkill -f "crossing_matri[x]"` to clear what I thought was a stale process killed the
shell running the command, because the pattern appears in that shell's own command line. The
character class defeats a `pgrep` self-match, NOT a `pkill` whose pattern is IN the argument
being matched.

**This is documented in the engine-measurement skill in as many words** — *"`pkill -f
"run_draft_battery"` matches its own launching shell"* — and I hit it anyway, one turn after
hitting the `pgrep`-in-an-`until`-loop version of the same thing.

No data was lost: the run had already completed and written its file; only my analysis command
died. Recorded because the near-miss is the useful part — had the run still been going, that
would have destroyed 820 seconds of compute and I would have had no checkpoint for the final arm.

**The rule:** do not `pkill` by pattern from a shell whose own command line contains the pattern.
Kill by PID read from a separate `pgrep`, or do not kill at all — a finished process needs no
killing, and checking `ps -o etime=` first would have shown it had already exited.

---

## `#281` THE RAMIFICATION — the mode rule re-composes 45% of the draft and changes the starting lineup by ZERO

`#261` asked it in as many words — *"nobody has drafted with the rule in place"* — and `#271`,
`#274`, `#276`, `#277`, `#278` all measured WHEN the rule fires without ever asking what the
teams look like afterwards. The depth battery drafted all ten arms under BOTH rules and recorded
every pick; the comparison was simply never run.
`evidence/mode_boundary/mode_outcomes.py`. No new drafts.

### First: the rule changes an enormous number of picks

| arm | picks | round fires | crossing fires | picks differing | first divergence |
|---|---|---|---|---|---|
| 12T_ppr_BN6 | 168 | NEVER | NEVER | **0** | — |
| 12T_ppr_BN18 | 312 | 170 | NEVER | 141 (45%) | 171 |
| 12T_ppr_BN26 | 408 | 170 | NEVER | 237 (58%) | 171 |
| 8T_ppr_BN18 | 208 | 114 | NEVER | 93 | 115 |
| 10T_ppr_BN18 | 260 | 142 | 231 | 116 | 142 |
| 14T_ppr_BN18 | 364 | 198 | NEVER | 167 | 198 |
| F&F capture | 312 | 170 | NEVER | 142 | 171 |

Divergence begins on the pick AFTER the round rule fires, and never recovers — the switch
changes every subsequent pick. `12T_ppr_BN6` is a natural control: 14 rounds, so neither rule
fires, and **0 picks differ.**

**The substitution has a signature.** Composition shift (crossing minus round) — i.e. what
turning upside mode OFF does:

```
 F&F capture   WR +36  TE −33  RB −4   QB +0
 14T_ppr_BN18  WR +38  TE −24  RB −14  QB +0
 12T_ppr_BN22  WR +33  TE −30  RB −3   QB +0
```

**Upside mode buys tight ends and sells receivers, at scale, and leaves QB untouched.** That is
`#222`'s TE excess as a draft-wide outcome rather than a per-pick effect.

### Then: it changes the starting lineup by exactly nothing

Optimal legal lineup by season PROJECTED POINTS — not `starter_value`, which `#211` established
is a category error (asset levels summed over a started subset rank positional breadth, and 83.8%
of pool values are negative so thin rosters are forced to start deep negatives).

| arm | round pts | crossing pts | delta | latest starter pick | first divergence |
|---|---|---|---|---|---|
| 12T_ppr_BN18 | 26250.1 | 26250.1 | **+0.00** | 99 | 171 |
| 8T_ppr_BN18 | 18960.8 | 18960.8 | **+0.00** | 85 | 115 |
| 10T_ppr_BN18 | 22732.5 | 22732.5 | **+0.00** | 82 | 142 |
| 14T_ppr_BN18 | 29492.3 | 29492.3 | **+0.00** | 170 | 198 |
| F&F capture | 33998.7 | 33998.7 | **+0.00** | 127 | 171 |

**`#245` says identical numbers are a broken instrument until proven otherwise, so the zero was
interrogated rather than reported.** The explanation is in the last two columns and is now
computed BY the instrument: in all ten arms the latest pick that reaches any starting lineup is
EARLIER than the first pick on which the rules disagree. **The mode switch only ever touches
bench picks.** `switch_touches_a_starter` is False in 10 of 10.

So the TE-for-WR substitution is real, large, and **entirely a bench phenomenon.** It changes who
sits, never who plays.

### WHAT THIS DOES AND DOES NOT LICENSE

**It does NOT say the bench is irrelevant.** The measure is a static, healthy, full-season
projection. A bench exists for option value — injury, bye, breakout — and none of that is visible
to this number. The finding is *no first-order starting-lineup effect*, NOT *the bench does not
matter*. Anyone quoting this as "the mode rule has no consequences" is quoting it wrong.

**It DOES sharpen the no-trading case, and it is the owner's own league.** The 2026-09-08
reference roster (`#272`) records that with trades disabled *"a player who never starts is worth
zero here, permanently"*. Under that rule a bench full of surplus tight ends is inert by
construction — so in FFCL Group A specifically, the substitution is not neutral, it is a cost.

**It reframes the whole crossing investigation's stakes.** `#278` showed one roster slot decides
whether the rule ever fires. `#281` shows that decision reaches no starter in any measured arm.
Both are true, and together they say the mode boundary is a **bench-composition policy** that has
been discussed as though it were a valuation policy.

### Two instrument failures caught on the way, both worth keeping

**1. The first run reported `+0.00` across all ten arms with the control PASSING — while measuring
nothing.** `season` maps a player to Sleeper's raw SEASON STAT LINE; there is no precomputed
`pts` field. `season[pid].get("pts")` returned `None` for all 2,872 picks, every roster scored
0.0, and the control self-check said "ok" because zero equals zero. Points are now scored against
each league's own rulebook via `score_projection` (`#213`).

**2. The control could not catch it, so a NON-VACUITY GATE now runs first.** A control comparing
0.0 to 0.0 is vacuous. The instrument now refuses to report at all — `VOID` — if no arm scored
points or if more than half of picks are unpriced. The population line (`picks=2872 unpriced=0
(0.0%)`) prints unconditionally so a reader sees the denominator before the result.

### `#281b` CROSS-CHECK AT THE OWNER'S PROMPT — are the swapped picks real players, by a basis other than projection?

The owner raised two objections to `#281` in sequence, and both changed the answer.

**First: "third string players and rookies that aren't touching the field really wouldn't have
much by way of projection."** Measured on the picks the switch actually changes:

| arm | divergent picks | zero proj | under 10 pts | median |
|---|---|---|---|---|
| 12T ladder @ BN10 | 92 | 0 | 0 | 96.4 |
| 12T ladder @ BN18 | 284 | 2 | 2 | 63.2 |
| 12T ladder @ BN26 | 476 | 3 | 80 | 40.0 |
| 8T_ppr_BN18 | 188 | 2 | 2 | 141.4 |
| 14T_ppr_BN18 | 334 | 2 | 32 | 41.4 |
| CAPTURE_f&f | 284 | 2 | 11 | 62.8 |

Not scrubs in the shallow arms (median 63-141, almost no sub-10 bodies); the concern bites in
the deepest, where a sixth of divergent picks fall under 10 points. **The BN10-BN26 rows are one
prefix-nested draft (`#276`) sampled at five depths, not five observations.**

**Second: "check them against ranking, listings or other established valuations that don't relate
to projections."** The right check, and running it caught a confound in my own first answer.

**A CORRECTION I MADE BEFORE PUBLISHING, recorded because I reported the wrong version in
conversation first.** My first pass said roughly half the swapped picks have no independent
valuation. That counted the vendor table's 745 indexed rows as the relevant denominator. It is
not: the table includes KICKERS, TEAM DEFENCES and IDP, which these leagues have no slots for and
correctly never draft — and its `rank` column is POSITIONAL, not overall, which is why the
"never taken" list led with four different `#1`s (`B Aubrey` K, `P Eagles` DEF, `C Schwesinger`
LB). Restricted to positions the league can actually start, derived from its own slots:

**264 ranked startable players. The draft takes 312 picks.**

| pick block | ranked | unranked |
|---|---|---|
| 1-100 | 100 | **0** |
| 101-150 | 48 | 2 |
| 151-200 | 40 | 10 |
| 201-250 | 30 | 20 |
| 251-300 | 24 | 26 |
| 301-312 | 2 | 10 |

**The draft is DEEPER THAN THE RANKED UNIVERSE.** Running past the end of the list is arithmetic,
not a defect. And the engine is not passing over good players to get there: only **27 of 264**
ranked startable players go undrafted, the best being `QB99 S Sanders`, `QB114 M Penix Jr.`,
`WR159 R Pearsall` — marginal by the vendor's own positional rank.

The owner's framing — *"this should be firing well before the 760 players deep mark"* — is
CORRECT: at the pick the switch fires (170), 40 of every 50 picks are still vendor-ranked.
Coverage only collapses past ~250, where the ranked list has run out.

**What survives, in its honest size:** in deep-bench formats the last ~15% of picks necessarily
happen past the end of any established ranking, and some of the mode switch's work lands there.
That bounds how much ANY bench-quality comparison could prove — a real limit, and a much smaller
one than the figure I first reported.

**The knockout test is therefore NOT RUN.** The owner proposed simulating the whole first string
unavailable and re-optimising from the bench, which is the right shape for measuring option
value. It is declined on the instrument, not on the idea: for the tail of the population the
only available number is an uncorroborated projection, and a backup's projection already embeds
an assumption about playing time he does not have — so a knockout scored on static projections
systematically understates exactly the thing it is meant to measure. Named as needing a
different input (usage/depth-chart data, `#49`/`#88`), not as answered.

---

## `#280` COMPLETE — the full permutation grid, and the TE slot is the only switch

Nine arms, each with predictions committed BEFORE the run (`45bcbeb`, `d69cd11`). All self-check
ok against the engine's own `growth_signal` detector.

| league shape | TE slot | superflex | TE premium | **global rule** |
|---|---|---|---|---|
| `12T_ppr` (control) | yes | — | — | **NEVER** |
| `12T_ppr_SF` | yes | yes | — | **NEVER** |
| `12T_ppr_TEP_dynasty` | yes | — | 0.5 | **NEVER** |
| `4WR_TE_PREMIUM` | yes | — | 0.5 | **NEVER** |
| `LIGHT_IDP` / `HEAVY_IDP` | yes | — | — | **NEVER** |
| `12T_ppr_NO_TE_SLOT` | **no** | — | — | **FIRES 155/168** |
| `12T_ppr_TEP_NO_TE_SLOT` | **no** | — | 0.5 | **FIRES 165/168** |
| `12T_ppr_SF_NO_TE_SLOT` | **no** | yes | — | **FIRES 175/180** |

**One binary decides it: does the league have a dedicated TE slot.** Six shapes with one never
fire; three shapes without one always do. Superflex, a TE premium, a fourth WR slot, light IDP
and heavy IDP all fail to move that binary — they only shift WHERE inside the tail it lands.

### The three pre-registered predictions, settled

**1 — REFUTED then RESOLVED.** Superflex alone does NOT flip the holdout to QB (`#277`); the fork
committed for `SF_NO_TE_SLOT` resolves to its first branch — TE-slot removal dominates, and
superflex does not defeat it.

**2 — CONFIRMED, with an honest qualification.** A TE premium does not rescue a position that has
lost its slot: `TEP_NO_TE_SLOT` still fires, holdout none. But it is **not perfectly inert** — it
delays firing 155 → 165. `#277`'s "scoring does not set the crossing order" holds in the sense
that matters (it never converts NEVER into FIRES, or the reverse) and is **too absolute as
phrased**: scoring moves the firing pick by ~10, slots decide whether there is one at all.

**3 — REFUTED.** IDP rows are priceable in both IDP arms; the `#210` supply defect does not
surface as unpriceable rows here. Does NOT close `#210`.

### The recommendation this evidence supports — NOT WORTH INCORPORATING AS DESIGNED

Recorded as a recommendation to the owner, not a ruling.

1. **It is not a transition rule, it is an accidental off-switch.** 16 of 16 TE-slot leagues never
   fire. Adopting it silently means *upside mode is disabled* in most leagues — a large
   behavioural change delivered as a subtle one. If that is the right outcome it should be a
   stated decision, not an emergent property of a VOR comparison.

2. **Its trigger is an accident of roster shape.** `#278` flipped it with one slot swap. No
   account makes "does this league have a TE slot" the right criterion for "has the draft reached
   its upside phase". That is `#56`'s concern in a worse form — an unintended dependency rather
   than a calibrated constant.

3. **Where it fires, it fires too late to be a phase.** 155/168, 165/168, 175/180 — 92-97%
   through. And `#280`'s FFCL correction shows it is sensitive to DRAFT LENGTH as well: FFCL
   matches the firing cell exactly but ends at 168, before RB crosses. A rule whose answer depends
   on whether the league runs 14 or 15 rounds is reading the roster sheet, not the draft.

4. **The measured benefit is zero where it can be measured.** `#281`: up to 58% of picks change,
   starting-lineup points change by 0.00 in 10 of 10. The whole effect is bench composition, and
   the bench question is blocked on inputs this repo does not have.

**WHAT IS WORTH INCORPORATING, on the same evidence:** the per-position levels as a DISPLAYED
OBSERVABLE (`DRAFT_ROOM_UI.md` §13). The engine computes them and `.any()` discards them. They
would tell a drafter something true and checkable mid-draft — *quarterbacks and receivers ran dry
at pick 85* — with no selection authority, which is exactly the `#55` precedent for
`pick_necessity`.

**AND THE FINDING WORTH MORE THAN EITHER RULE:** upside mode is a **bench-composition policy**
that has been argued about as a valuation policy. It buys tight ends and sells receivers at
scale, entirely below the starting lineup. In FFCL Group A — no trading, where the owner's own
09-08 record says a player who never starts is worth zero permanently — that substitution is a
cost rather than a wash. That is a Phase 3 question about `replacement_levels` (`#50`, `#147`),
not a mode-switch patch.

---

## `#282` THE POOL GAUGE — a per-position tank that only ever drains, banded ELITE/MID/DEPTH/MEH

**OWNER'S RULING, and it closes a thread rather than opening one: THERE WILL BE NO UPSIDE MODE.**
Verbatim — *"So there will be no upside mode. Just this visual to give the drafter information on
the pool. Still available."* This supersedes the toggle half of `DRAFT_ROOM_UI.md` §11 (the
depletion notice carrying a default-on per-position switch) and §12's per-position mode arming.
The notice pattern's reasoning survives and is worth keeping — a setting reachable only through
the evidence that produced it is still the right shape for any future switch — but no switch is
being built. `#230`-`#233` measured what upside mode actually does; `#280` recommended against the
rule that would have armed it; this closes the question by removing the mode, not by tuning it.

The gauge is therefore the WHOLE deliverable, and it has no functionality side: it changes no
valuation, gates no candidate, and arms nothing. `#55`'s precedent exactly — the engine shows,
the human decides.

### The quantity, and why it depletes where the crossing rule did not

Fix the bar ONCE, at draft open, at each position's own replacement level; count the survivors
above it. Players only ever leave the pool, so the gauge is **monotone non-increasing by
construction** — a property of the definition, not a hope about the data. Asserted anyway, and
green on every position in both leagues.

This is the whole reason it exists. The crossing rule's quantity was top-minus-replacement, where
BOTH ends move, and `#276`/`#277` measured a tight end's headroom **rebounding 137 → 24 → 17 → 22
→ 30** as the pool emptied — bench picks lower the replacement faster than they lower the best
remaining. A gauge built on that number would read *refilling* at the exact moment the position
ran dry.

The bar is read back out of the engine's own two columns (`projected_points - bpa`), exact and
unique per position. Nothing here picks a cutoff (`#56`).

### The bands, and TWO REJECTED DEFINITIONS — both mine, both measured

The owner's vocabulary: **ELITE / MID / DEPTH / MEH**, at most three marks per tank, because
*"if we're only using 2 or 3 of these per position, they need to be significant signals of the
strength of the players above and below them."* That criterion IS the placement rule — marks go
where they most divide strength. Two other rules were built first and both lost, graded on
**projected points, a column that did not place the cuts**:

| rule | result |
|---|---|
| biggest raw gap (`detect_positional_cliff`'s notion) | 66-96%; behind banding in all 8 position/league cells, by 25 points at superflex QB |
| steepest slope change | **returned nothing at all** for TE and WR in both leagues; 32-38% at RB |

The second failure is the informative one, and it corrects a shared mental model. The owner's
framing was *"when the production begins to dip faster, that is a cliff."* Above the replacement
bar these curves are **CONCAVE** — they fall fastest at the very top and flatten from there — so
*where does the decline accelerate* has no answer, because it never does. The bands are real; the
bend that was supposed to find them is not.

### THE EVIDENCE IS THE MARGIN, NEVER THE LEVEL (`#245`)

Banding scores 91.0-96.5% on points. **That number alone proves nothing**: any monotone cut of an
already-sorted list explains most of its own variance, and arbitrary equal quarters already score
82-96%. Only the margin over that control is earned.

| | bands | equal slices | margin |
|---|---|---|---|
| TE (F&F) | 95.3% | 83.2% | **+12.1** |
| RB (F&F) | 92.8% | 84.0% | **+8.8** |
| QB (F&F) | 91.0% | 84.7% | +6.3 |
| WR (F&F) | 93.9% | 88.2% | +5.7 |
| TE (12T) | 96.5% | 81.7% | **+14.8** |
| RB (12T) | 94.2% | 82.0% | **+12.2** |
| WR (12T) | 94.2% | 86.5% | +7.7 |
| **QB (12T)** | 96.0% | 95.9% | **+0.1** |

**QB in the 12-team 1QB league is the honest null, and it inverts an intuition stated in the same
exchange** (*"a slow decline in every position except for maybe qb"*). Above the bar, QB is the
FLATTEST position, not the steepest: the 11 quarterbacks clearing replacement run 369 / 350 / 343
/ 334, a 10% spread, against RB's 426 → 194. There is no elite/meh structure there to draw. The
gauge draws the marks anyway and does not pretend — bands sitting near even thirds is itself the
true statement that the position is evenly graded. **No suppression rule was added**, because
"suppress when the margin is small" is a threshold, and a bound is not a threshold (`#56`).

### The DARK pick — the owner's inference, measured

*"When you are pulling a player from beneath that already having been depleted, then you're in,
these are just random shots in the dark mode."* Now a counted state, and kept strictly apart from
its neighbour:

- **ABOVE** — still above the opening bar. Measured production, taken.
- **REACH** — below the bar while the tank still held someone above it. A CHOICE, and the gauge is
  not entitled to call it wrong.
- **DARK** — below the bar with the tank ALREADY EMPTY. Nothing measured remained to pass over.

REACH and DARK are the same observable pick and opposite epistemic situations. Merging them is
precisely the defect `#277a`/`#280` cost us twice — a choice rendered as an absence. The gauge
reports DARK only, because DARK is the state the tank actually knows.

Fourth and Forever: **184 of 312 gauged picks are dark (59%)**, 127 above the bar, and exactly
**one** reach in the entire draft. WR goes dark at pick 99 of 312; QB never does.

### The display contract, tightened

| | |
|---|---|
| **SHOW** | segments; the band marks; optionally a percentage of the position's own full pool |
| **NEVER** | raw counts, point values, band sizes, or any engine-internal population |

Counts are required to compute the fraction and are never surfaced — the owner's standing
objection (*"2 left above replacement feels obscure... too technical"*) plus a second reason: a
count invites reasoning about WHICH two players, which a gauge is not entitled to imply. A mark
says WHERE a boundary is, never how far the drop is. `pool_gauge.py` prints what a reader would
SEE, so the evidence and the surface cannot drift; the JSON keeps the counts for audit only.

**Instrument:** `evidence/mode_boundary/pool_gauge.py` → `pool_gauge.json`. **Surface spec:**
`DRAFT_ROOM_UI.md` §14.

### `#282b` THE TANK IS FOUR TANKS — per-band draining, and two of my own recommendations reversed

**OWNER'S BUILD SPEC**, and it corrects a defect in `#282`'s rendering rather than adding a
feature: *"if a player takes someone that is in say, the mid grade while an elite is still there,
I want it to shrink that mid band, not from the top... let the bands be static, almost assigning
each player a spot in the spectrum upon build of the roster pool, based on the scoring settings"*
— and *"if someone else takes an inferior player, that doesn't diminish the upper range's pool. so
shouldn't on our gas tank. granted, I'd still want the total strength showed to dip by the player
being taken, just change where in the total representation that lessening comes from."*

**THE DEFECT THIS FIXES.** `#282` drew one fill edge over a COUNT of survivors, which silently
assumes the players who left were the ones at the front of the pool. Drawn per band, nothing has
to be assumed: each departure is recorded in the band it came from, so the display cannot make a
claim that could be false. The total still shortens by exactly one player — only the location of
the loss changes.

**A VACUOUS MEASUREMENT, CAUGHT BY `#245`.** Asked whether picks actually come out of band order,
the instrument returned **0 of 219, every position, both leagues** — identical, which `#245` says
is a broken instrument until proven otherwise. It is. Every recorded draft in this repo was made
by the ENGINE, which takes the best available within a position by construction, so a zero
out-of-order rate is the engine's own signature and says nothing about drafters. The one real
human draft on hand (`OWNER_REDRAFT_2026-09-08.md`) is a single seat's 14 picks, so availability
at each pick cannot be reconstructed. **No data in this repo can validate or refute the case.**
The design is adopted on the argument, not on a measurement, and that is recorded as such: the
per-band rendering is strictly safer because it makes no ordering claim at all.

**MEMBERSHIP IS DERIVED FROM THE SCORING SYSTEM, never a set share** (owner: *"do not have each
band be a static percentage, or count of players... TE may only have like 4-6 elite. that's
valid"*). Measured, the same position changes shape entirely with the rulebook:

| | ELITE / MID / DEPTH / MEH | share |
|---|---|---|
| TE, 12-team PPR | 2/2/5/10 | 11/11/26/53 |
| TE, Fourth and Forever | 3/6/11/4 | 12/25/46/17 |
| RB, Fourth and Forever | 4/13/9/10 | 11/36/25/28 |
| QB, Fourth and Forever | 9/9/9/4 | 29/29/29/13 |

ELITE spans 11%-29% across eight position/league cells. Nothing is set.

**TWO OF MY OWN RECOMMENDATIONS REVERSED IN THIS PASS, both on the rendering:**

1. **Travelling marks — withdrawn.** `#282` drew three band edges that slid toward the front of
   the tank as players ahead of them left. Per-band slices supersede the whole mechanism; the
   code is deleted rather than left as a second way to draw the same thing (`#126`).
2. **Proportional band width — withdrawn, one hour after I recommended it.** I argued the band
   sizes were the most useful un-numbered fact the gauge could carry. Rendered side by side, it
   fails: a small ELITE band draws one or two segments — two or three states in total, unable to
   express *"two of the four elite remain"*, the most decision-relevant fact at the position —
   while the widest band takes the most room. It inverts attention toward the band that matters
   least, in every position measured. **Equal slices**, with the cost stated in
   `DRAFT_ROOM_UI.md` §14: they do not show how many players a band holds, and a reader could
   take four equal slices as four equal groups. The table above is why they are not.

**`#282c` THE GREEDY SPLITTER WAS WRONG AT RB — caught by the owner reading the sizes.**

*"is it really 3 and 4 only for elite and decent rb? I'd think solid would be deeper than that."*
It is, and the objection located a real defect in the algorithm rather than in the data.

Greedy adds one cut at a time and never revisits. A steep head captures its first cut, and the
second is then stranded inside a flat run. Fourth and Forever RB drops **47.2 points from RB3 to
RB4** and then runs shallow — 15, 9, 3, 0.6, 5, 4, 1, 2, 3 — all the way to RB17, where it steps
14.6 again. Greedy answered **3/4/18/11**, cutting at RB7 in the middle of that shallow run. The
exact partition answers **4/13/9/10**, cutting at RB17 where the next real step is.

| | greedy (shipped in `#282`) | exact | separation on points |
|---|---|---|---|
| RB | 3 / **4** / 18 / 11 | 4 / **13** / 9 / 10 | 92.8% → **93.7%** |
| WR | 4 / 7 / 10 / 15 | 4 / 6 / 11 / 15 | 93.9% → 93.9% |
| TE | 3 / 6 / 11 / 4 | 3 / 6 / 11 / 4 | identical |

WR and TE were unaffected, and that is the tell: the defect only bites where the head is steep
enough to capture the first cut. `band_cuts` is now the Fisher/Jenks dynamic program — minimum
total within-band squared deviation for exactly k+1 bands, O(k·n²) on a pool of a few dozen, so
there is no reason to approximate. Still parameter-free; still no constant anywhere.

**The margins all held or improved** under the exact cuts, and QB in `12T_ppr_BN18` remains the
honest null at +0.3 over arbitrary equal slices. Every band table published in `#282b` and
`DRAFT_ROOM_UI.md` §14 was regenerated — the first printing of them carried greedy's numbers.

### `#282d` THE TANK SPANS THE WHOLE POOL — and `#282`'s "dark" wording is CORRECTED

**OWNER'S OBJECTION, and it was right:** *"that leaves no room for anything outside of starters."*

`#282` gated tank membership on `bpa > 0`, so the tank held only players above replacement:
**92 of 312 picks** in `12T_ppr_BN18`, **127 of 312** in Fourth and Forever. That population is
the league's STARTING SLOTS almost exactly — 8 starters × 12 = **96** against 92 above the bar;
10 × 12 = **120** against 127 — which is not a coincidence, because replacement level IS the last
startable player. The gauge therefore went fully dark at pick 130 of 312 and said nothing about
the half of the draft where the calls are hardest.

**AND THE BAR WAS NEVER FORCED — that boundary was mine, not the engine's.** Below it the
projection keeps falling hard:

- WR `216 → 204 → 188 → 149 → 98 → 62 → 35 → 0`
- RB `186 → 142 → 89 → 64 → 32 → 9 → 0`

Several of those steps are steeper than the ones just above the bar. The deep pool is cleanly
ordered, so it is gradeable.

**CORRECTION TO A PUBLISHED CLAIM (`#282`, and I stated it twice in conversation).** That entry
said a pick below the bar had *"no measured production remaining to pass over"* and called the
region DARK. **Wrong as stated.** What is absent below the line is **surplus over replacement**,
not production. Production separates those players cleanly; VOR merely cannot express it, being
defined against the level they sit under. The census vocabulary is now STARTER / BENCH, and the
bar survives as a **marker inside the tank** rather than its edge — it still answers "where do
the starters end", which is worth drawing.

Result: **every one of the 312 picks now lands in a band**, 131 at or above the starter line and
181 below it, all graded. The owner's estimate that roughly two thirds of the draft should be at
least depth-grade is borne out.

### `#282e` THE QB SHAPE DOES NOT FALL OUT OF THE MATH, AND IS NOT BEING SET BY HAND

The owner sketched a QB shape (*"top6ish, next 10ish, next 12ish, fluff"*) while stating the
governing constraint plainly: *"this isn't supposed to me just manually setting the levels
arbitrarily."* Correct, and `#56` says the same. The sketch was tested, not fitted.

**The QB curve is flat and then falls off a table.** 12-team, season points:
`QB1 372 · QB7 341 · QB13 317 · QB19 306 · QB22 300 · QB25 282 · QB28 256 · QB31 215` — then
`QB34 95 · QB37 31 · QB40 15`. A **19% spread across the top 22 players**, then a cliff at ~QB32.
There is no six-player elite tier to find. This is the same null measured three ways now: QB bands
beat arbitrary equal slices by **+0.1** (above-bar, 12T), **+1.0** and **+1.2** (full pool) — the
weakest margin of any position in either league.

**Two derived alternatives were built and both rejected:**

| | QB | RB | TE | WR |
|---|---|---|---|---|
| linear points (kept) | 24/8/2/8 | 7/21/25/73 | 9/17/26/63 | 16/44/46/92 |
| log points | 32/3/5/2 | 46/37/21/22 | 36/43/29/7 | 76/65/39/18 |
| roster-capacity trim | 12/13/7/3 | 4/22/20/33 | 9/17/19/20 | 16/38/32/47 |

*Log* is an unmotivated transform and is worse at QB. *Roster-capacity* is genuinely derived —
league capacity is 12 × 26 = 312, exactly the draft size — and its QB shape is much the closest to
the sketch, **which is precisely why it must be rejected**: ranking across positions by raw points
over-retains QBs because QBs score more, keeping **83% of the QB pool against 63% of RB and 67% of
WR**. That is the cross-position unit problem `#75`/`#76` found in `bpa` and `#229` left undefined
below replacement. Adopting it would smuggle an invalid comparison in as a pool boundary.

**Best hypothesis for the disagreement, offered as a hypothesis and NOT measured:** the sketch is
dynasty- and superflex-flavoured, where a young franchise quarterback's value is longevity and
scarcity. The ruler is one season of points, which prices a 30-year-old and a 23-year-old with the
same projection identically. `#147`, and the dynasty columns reach **0 of 36** board rows, so the
gauge structurally cannot see it.

What the marker does give QB: **the starter line sits inside the ELITE band** (rank 12 of 42 in
the 1QB arm). The tank says "this band already holds more quarterbacks than the league starts",
which is the honest form of the flatness rather than an invented tier break.

### `#282f` THE DEAD TAIL EATS THE CUT BUDGET — and at exactly one position it eats all of it

Squared-deviation cutting chases the largest gulf, which in every pool is the drop from real
players to roster filler projecting ~20 points. Where the live portion is large relative to that
tail the cuts still land inside it. **QB is the position where it does not.**

| | top band | as % of pool | cliffs hidden inside it |
|---|---|---|---|
| **QB** | **24** | **57%** | **QB3 (12.4 pts, 3.8x median) and QB12 (11.2, 3.5x)** |
| RB | 7 | 6% | ranks 3, 4 |
| TE | 9 | 8% | rank 2 |
| WR | 16 | 8% | rank 4 |

One-stage cutting answers QB **24/8/2/8** — two cuts spent on tail structure, and a **two-player
band drawn across four segments**. Inside the 24 it never looked at, `pick_synthesis.
detect_positional_cliff` independently calls exactly QB3 and QB12 HIGH, by an unrelated rule.

**TWO-STAGE WAS TESTED AS A GENERAL REPLACEMENT AND LOST**, which is the useful half of this:

| | one-stage | two-stage |
|---|---|---|
| TE | 94.3% | **87.4%** |
| WR | 93.9% | **87.2%** |
| RB | 93.7% | **91.7%** |
| QB | 96.5% | 96.3% *(wash — but shape 24/8/2/8 → **12/13/7/10**)* |

So it is **not** the default. It is a fallback, reached by a rule with **no valuation threshold in
it**: take the two-stage cutting when one-stage produces a band holding fewer players than the
segments allotted to draw it. A band that cannot show partial drain is a DISPLAY CAPACITY defect,
the same class as `SPAN` and the mark cap, and this repo already treats display capacity as a
legitimate non-threshold (`#56`). On every arm measured the rule fires for QB and only QB —
`staged_cuts` reports which positions took it, so the claim cannot rot silently.

Two-stage's first QB cut lands on **QB12**, which in a 12-team 1QB league is also the starter
line. That coincidence is a property of this league's size, not of quarterbacks — projections do
not know how many teams you have — and it is not being read as more than that.

**AND THE SHAPE IS NOT A CONSTANT.** The same 42 quarterbacks under Fourth and Forever's rulebook
cut at [9, 17], not [4, 12]. Scoring-derived bands moving with scoring is the design working; it
also means no QB tier shape may ever be published as a fact about the position.

### `#282g` THE GAUGE PRICES A MINORITY OF THE BOARD, AND NOW SAYS SO

| board | rows shown | rows priced | |
|---|---|---|---|
| QB (12-team) | 155 | 42 | **27%** |
| WR | 452 | 198 | 44% |
| TE | 256 | 115 | 45% |
| RB | 256 | 126 | 49% |
| DB (HEAVY_IDP) | 394 | 130 | 33% |
| LB | 298 | 83 | 28% |
| DL | 219 | 86 | 39% |

**STRUCTURALLY CERTAIN:** the tank is assembled from priced players only, so it reaches EMPTY when
the priced ones are gone, however many unpriced rows sit beside them. An empty tank is therefore
the statement *"nothing priced remains here"* and never *"nothing remains here"* — and without
disclosure a reader cannot tell those apart. That is the absence contract at the one place a
person actually reads it, and `coverage()` now reports the fraction per position.

**NOT ESTABLISHED, and recorded as such rather than asserted:** whether any real draft reaches
that point. Unpriced offensive rows are overwhelmingly third-stringers the absence contract
correctly excludes and orders last, and no draft measured here has exhausted a position's priced
pool. **My first framing of this was wrong in two ways** — I called it an IDP problem when it is
universal, and I described a DB tank draining "while 264 defensive backs sit on the board
untouched", which is a hypothetical I have not demonstrated.

**IDP is the case to WATCH, not the case proven.** An IDP league starts six defenders per team, so
demand sits far closer to priced supply than offence does. No IDP draft has been run to check.
Separately, IDP bands are near-vacuous where they can be computed — DB **+0.5**, LB +1.8, DL +2.0
over arbitrary equal slices, against +4.6 to +6.9 for the skill positions — because the band means
decline almost linearly (DB 117/94/68/43). Tackle accumulation is smooth, so there is no tier
structure to find. **Recommendation: do not band IDP until the supply gap is closed** (`#210`,
`#49`); banding an unpriced two-thirds would dress a supply defect as a grade.

### `#282h` THE REALIZED SEASON — built, tested, and still uncaptured

**IDP HAS NO VENDOR PRICING AT ALL.** Not thin — absent. The valuation table carries **0 of 91
LB, 0 of 153 DB, 0 of 171 DL** with a projection or a `proj_3yr`, against 39/40 QB, 72/79 RB,
105/109 WR, 48/52 TE. Every IDP number in this session came from Sleeper stat lines scored
through the rulebook, with nothing to check them against. Offence carries two independent
sources; **IDP carries one**, in a system whose stated first principle is that no single source
is ground truth.

That is the real case against banding IDP, and it is firmer than either argument offered before
it: not that the curve is linear (it is — DB means run 117/94/68/43) and not that production is
volatile (**believed, and NOT measurable here** — no week-level data, no `std_dev` column
anywhere). Fine-grained grades published off one unverified source is the objection that stands.

**WHAT IS ALREADY BUILT, AND WHAT HAS NEVER RUN:**

| piece | state |
|---|---|
| `sleeper_client.get_weekly_stats()` | built, tested, used by `outcome_record` |
| `outcome_record.capture()` — the store writer | built, tested |
| `data/…/outcomes_*_wk*.json` | **no file exists** |
| `data/fixtures/sleeper_capture.json` | projections only, 5,346 rows, no actuals |

Everything is plumbed; nothing has flowed through it (`#97`: *"BLOCKED on real findings — store
empty"*). **This entry closes the last missing piece rather than the blocker.**

**ADDED HERE:** `get_season_stats()`, the realized counterpart to `get_season_projections()`,
sharing one summing construction via `_sum_weeks` (`#126` — a copied loop means two places to fix
the next time one of its properties is wrong). And `write_fixture(..., prior_season=)`, which
captures a completed season's production **beside** the projections under **its own year label**.

Three properties, each mutation-checked:

- **THE YEAR IS EXPLICIT.** A projection for 2026 and what happened in 2025 are different years
  by definition; `#79` is what it cost when a canonical record did not carry its own season. The
  fixture now stores `prior_season_production: {season, totals, coverage, error}`.
- **AN ABSENT PRIOR SEASON IS NOT A ZERO.** **Every rookie lands here**, as does anyone who
  missed the year. A zero row would make each incoming rookie the worst player at his position
  instantly — the defect class `#174` and `#187` were opened for. No key, never zeros.
- **A FAILED STATS FETCH DOES NOT COST THE CAPTURE.** The projections still write and the
  failure is recorded, so a reader can tell *"we did not ask"* from *"we asked and got nothing"*.

**PROVENANCE IS CLEANER THAN THE PROJECTIONS', not a new exception.** What a player actually did
is a public NFL fact, the same class as his name, team and position — all admitted verbatim under
the standing input policy, which excludes a vendor's own model output, layout and branding.

**STILL BLOCKED, and the blocker is unchanged:** `api.sleeper.app` is denied by this environment
(403 at CONNECT, `#143`/`#88`). One run on a Sleeper-reachable machine fills it.

**NO READER WAS BUILT.** Nothing consumes `prior_season_production` yet, and adding a reader for
data that does not exist would create exactly the write-only quantity `#138`/`#141` spent a pass
eliminating. The consumer arrives with the data.

**WHAT IT WILL BUY, AND THE LIMIT.** A second independent anchor for IDP, and projection error by
position — the only way to settle whether IDP production is noisier than offence rather than
asserting it. But **one prior season measures BIAS, not variance**: a single observation per
player. True week-to-week variance needs the weekly rows kept unaggregated, which
`get_weekly_stats` supplies and this summing deliberately discards.

---

## #206 — the 0.00 is 2.3e-8, and the two causes are not two routes to one answer

`survival_probability` reports 0.00 for a player who then survives sixty straight picks. #244
ruled out the floor as the explanation and left the rest as a hypothesis in one clause: *"the
boards rank by CDME; rivals do not."* Both halves are now measured
(`evidence/survival_mechanism/`), and the second one is not what I expected it to be.

**THE MECHANISM, CONFIRMED.** Every opponent board is built by the same valuation, so the
player the engine likes best is rank 1 on all of them simultaneously. Of the top ten on one
board, **ten carry an identical rank on all twelve**; across the twelve boards there is
**exactly one distinct rank-1 player**. Through `estimate_survival` itself at seat 1's opening
turn — 22 intervening picks — `take_probability` is **0.55 on 22 of 22**, one distinct value,
no spread anywhere.

**IT IS NOT A ROUNDING ARTIFACT.** Reported 0.0; unrounded **2.3e-8**, log10 −7.63. Seven
orders below the 0.0005 that would round there. "0.00" reads as *small but measured*; this is
the model being unable to express anything else.

**THE MASS FIGURE IS NOT A CONSTANT — IT SCALES WITH THE POOL.** #244 measured 6.23 expected
picks for a team that makes one, on a 256-row board. Fourth and Forever's own board holds **481
priced rows → 10.73**. Neither number is wrong; the total is a *function of the pool*
(2.11 / 3.67 / 6.23 / 11.11 at 50 / 128 / 256 / 500), because `.get(rank, FLOOR)` has no domain
limit. A repair aimed at "the 6.23" would be aimed at a sample, not at the defect.

**THE TWO CANDIDATE REPAIRS, ON ONE SCALE.** Renormalising by the realised sum is arithmetic
forced by *one team, one pick* — no constant is chosen, so it is a bound and not a threshold
(#56). On this turn it lifts survival to **0.314** in a single step. Agreement cannot be moved
to the same place from either side:

| rivals ranking him first (of 11) | picks affected | survival |
|---:|---:|---:|
| 0 | 0 | 0.641 |
| 1 | 2 | 0.135 |
| 2 | 4 | 0.029 |
| 3 | 6 | 0.006 |
| 11 | 22 | 0.000 |

**27th WITHDRAWAL, and it is mine.** Commit `4ffafb3`'s message states that *"letting a SINGLE
rival disagree gives 0.294."* **That is wrong and is withdrawn.** I read my own probe's `k` —
boards ranking him *first* — as its complement. One dissenter does not move the reported number
off 0.0; reaching 0.294 would need nineteen of twenty-two, which the shipped granularity cannot
even produce. The test that now pins this is the test that caught it: I wrote the assertion from
the false reading and it went red. The corrected statement is *sharper*, not softer — agreement
is **superlinear**, so a single shared valuation supplies far more of it than the collapse
requires, and three agreeing rivals already force 0.006.

**WHAT THAT CHANGES ABOUT THE REPAIR.** #244 ruled the fix a #50 decision and that stands, with
a better reason than "choose a coherent table". The two causes are **independent defects with
different remedies**, and only one of them is arithmetic:

- The **mass** half is a bound the model already violates and could be made to respect without
  choosing anything. It is the cheaper half and it is not blocked on an input.
- The **agreement** half is not repairable by consulting fewer boards or by trimming the table.
  It is the statement that twelve rivals share one opinion because they share one valuation, and
  giving them different opinions means modelling rival behaviour — which needs the real startup
  board that exists here only at position-only resolution (#49/#88).

**NOT REPAIRED, AND DELIBERATELY SO.** Wiring the mass half alone would move every consumer of
`survival_probability` — `opportunity_cost`, `pick_necessity`, `rival_premium` — on the eve of a
freeze, on the strength of one turn in one league. Evidence before repair, repair before freeze
(#162); this pass is the evidence, and the register now says what a repair would have to be
rather than leaving a mystery.

**PINNED, NOT LEFT TO PROSE.** `test_take_model_coherence.py` gains the agreement half beside
the mass half it already held (#126 — one home for the subject). 14 tests, mutation-checked
4/4. Its fixture keys boards **per distinct rival, never per pick**: a snake turn is 22 picks
but only 11 rivals, each consulted twice, and a per-pick fixture would build boards under ids
nobody looks up and answer a different question — which is exactly the error my first draft of
it made.

---

## #183 — six absence breaks in the Dock, found by rendering rather than by reading

The freeze checklist carries `#183` as *"six defects in the live Debate Dock"* and **never
enumerated them**. Like `B4`, the substance had to be re-derived. The method matters: a sweep of
absent-field scenarios through `_format_candidate` itself, not a reading of the source. Six broke.
**No claim is made that these are the original six** — that list is lost, and inventing a
correspondence would be the kind of tidy story this register exists to prevent.

**WHY THIS IS LOAD-BEARING AND NOT POLISH.** The owner ruled the Draft Room must work fully with
no API, and that the no-API state must not look deprived. For a customer without a key, the
engine's own evidence **is the whole explanation**. A `None` rendered there is not a cosmetic
blemish; it is the entire account of a pick, with a hole in it, in the one place nobody can check
it against the board.

| # | state | what the reader saw |
|---|---|---|
| 1 | unpriced row | `Universal value: None` |
| 2 | unpriced row | `(universal_value None + need_bonus +6.0 …)` — a sum with a hole |
| 3 | survival measured, price absent | `Opportunity cost of waiting: None` |
| 4 | survival measured, count absent | `(None intervening pick(s))` |
| 5 | cliff tier real, magnitudes absent | `gap to next at position: None` |
| 6 | `need_bonus` None | **TypeError — the Dock does not misreport, it dies** |

**REACHABILITY IS PART OF THE FINDING**, because this codebase does not spend repairs on
hypotheticals. Five are reachable by declared type *and* by path: the board's absence convention
gives an unpriced row `final_score = None`, which becomes a `None` team-acquisition value, while
`estimate_survival` **deliberately still answers for that player** — he is on a rival's board and
can be taken, so he receives the module's floor. That combination is what produced the worst of
them: a real percentage on one line and the literal string `None` on the next, where it reads as a
quantity. `#168` already established that unpriced rows occur.

**The sixth is a CALLER CONTRACT VIOLATION, guarded but not claimed live.** `need_bonus` and
`eligibility_bonus` are typed non-Optional and reach the snapshot through `.get(key, 0.0)` — which
substitutes the default for a *missing* key but passes an explicit `None` straight through, where
the `:+` format raises. It is guarded defensively and labelled as such rather than dressed up as a
live defect.

**THE REPAIR PRESERVES THE OTHER HALF OF THE CONTRACT.** Not leaking `None` is the floor, not the
goal: a chair that reads a missing line as *"the engine had nothing to say"* reaches the same
false conclusion by a quieter route. So each absence states what was not measured and denies the
reading it invites — *"NOT PRICED … never as low"*, *"UNKNOWN, never zero"*, *"Not 'waiting is
free'"*. And a **measured 0.0 is still reported as a measurement**, which is the property a
careless absence fix destroys; `test_a_measured_zero_is_still_reported_as_a_measurement` exists
precisely to fail if the repair ever starts swallowing real zeros.

One judgment worth naming: when a term of the team-value sum is absent, the **whole is still
reported** — it is a real number — but the arithmetic sentence is withheld. A sum missing an
addend, shown to a model instructed never to recompute, is worse than no sum at all.

**PINNED:** `test_dock_absence_contract.py`, 9 tests, mutation-checked 4/4. Full suite **2972,
OK**.

---

## #119 — the price is explained now, and half the item was stale

`universal_value` **is** `bpa + time_horizon_adj + risk_adj` — draft_room's own header line. The
board computed all three, and `quantity_readers.scan()` classified the two adjustments as
`decomposition` with **empty scoring_readers, empty observing_readers and empty carriers**.
Nothing read either. So the price crossed into the snapshot as a bare number, and a chair asking
*why is he worth that* hit a dead end at the exact leaf where the answer lives.

**HALF THE ITEM WAS ALREADY STALE**, which is now the third time this pass (`#86`, `#183`, this).
`#119` reads *"`time_horizon_adj`/`risk_adj` reach no production consumer; **board drops
`bpa_source`/`confidence`**"*. The second clause is false: `bpa_source` reaches `draft_room` and
`pick_debate`, `confidence` reaches `app.py` and `pick_debate`. Only the first clause was live.

**The repair DISCLOSES; it does not wire.** Both terms are carried to `CandidateSnapshot` and
rendered beside the team-value decomposition that already sat there. `quantity_readers` — an
AST-derived instrument, not a hand list — independently confirms the move from `decomposition`
to **`observable`**, with `scoring_readers` still empty. Promoting a decomposition term into a
scoring input would be a valuation change and a `#50` decision; a test asserts it has not
happened.

**Absence semantics were already correct upstream and are preserved.** Upside mode genuinely
never computes these two and the board omits rather than zeroes them, so the sum is withheld and
**named** — *"read that as UNKNOWN, never as 'no horizon or risk adjustment applied'"*. Same rule
`#183` set for the team-value sum: a sum missing an addend, shown to a model instructed never to
recompute, is worse than no sum.

**MY OWN FIRST DRAFT OF THE GUARDS WAS VACUOUS, and mutation found it.** Severing the carry —
`row.get("time_horizon_adj")` → literal `None` — left every test green, because they all built
`CandidateSnapshot` by hand and the `quantity_readers` checks still saw the NAME in the source.
An AST reference is not a value. A real merger, board and snapshot now exercise the wire, and
that mutation fails 48 tests.

**A SECOND MUTATION SURVIVES, CORRECTLY, and the reason is a finding.** Faking `risk_adj` as
`0.0` is undetectable on the fixture population — every top-20-by-trade-value player is healthy,
so the true value **is** 0.0 for all 48. Measured on a full board: **256 rows carry the term, 249
at 0.0 and 7 nonzero, every one an IR player, spanning −5.4 to −18.0.** The term does vary; that
population simply has none of it. Recorded rather than papered over, and a board-level test now
covers the variation the snapshot fixture cannot.

**THREE RATCHETS FIRED AND WERE UPDATED DELIBERATELY, not silenced:** the snapshot schema pin
(46 → 48, with both of its questions answered), `test_quantity_readers`' independently-established
verdicts (`decomposition` → `observable` — changed by hand, because a table that followed the
scanner automatically would make the check circular), and the display-contract AST scan.

**That last one is worth its own note.** The scan flagged my guard twice, and was right twice. It
recognises two shapes — an early-`return`, or a ternary whose test names the attribute. I first
wrote `all(t is not None for t in uv_terms)` (correct Python, invisible: the test names a tuple),
then a plain `if/else` (also correct, also invisible: no return). **A guard an instrument cannot
see is a guard that silently stops protecting the moment someone edits near it.** The shipped form
is a ternary naming all three fields.

**One stale term of my own**, caught by `test_prytaneum_terminology`: I wrote *"Debate Dock"* in a
comment. It is retired vocabulary — the surface is the **Prytaneum**. The freeze checklist and
this register still carry it in prose, where only `#182`'s audit will reach them, because the
terminology guard scans `*.py` only.

**PINNED:** `test_valuation_leaf_explains_itself.py`, 12 tests, mutation-checked 4/4. Full suite
**2984, OK**.

## #112 — the kinds are three, the population is one, and my first fix broke the contract it wrote

`#112` says a row's absence carried ONE token, `bpa_source = "no_priceable_input"`, for three
situations the register gives three different answers to: no replacement level (structural,
*unknown not bad*), no projection from any source (a coverage gap, *unknown not bad*), and below
every source's cutoff (*weak evidence of genuinely low value*). **Only the third justifies ORDER
LAST on its own merits**, and one token for all three asserts the strongest of them about every
unpriced row.

**THE GAP IS REAL AND THE POPULATION IS NOT.** Measured on a real board built from the capture
(12-team PPR dynasty, 1,119 rows): **638 unpriced, every one of them the coverage gap** — no
source put a number on him at all. Zero rows of the one kind that would justify the ordering the
engine applies. That is the finding, and it is sharper than the item: ORDER LAST is currently
applied to a population containing **none** of the evidence for it.

**TWO OF THE THREE KINDS ARE NAMED AND PRODUCED BY NOBODY, deliberately.** "Below every source's
cutoff" needs evidence the pool does not carry — that a source *lists* a player while declining
to price him. Admission and pricing are separate questions here (`#193`), but a board row records
only the outcome, not which sources were consulted, so the two cannot be told apart from it.
Producing that kind needs a new **input**, not a new predicate. "No replacement level" is not a
property of the pool at all. Both are kept in the vocabulary: deleting an unpopulated kind makes
the vocabulary describe this dataset rather than the domain, and the next league with an
unpriceable position has nowhere to land — which is how the collapse happened the first time.

**MY FIRST IMPLEMENTATION PUT AN ABSENCE KIND ON PRICED ROWS.** It assigned the cutoff kind on
`no_points & trade_value.notna()`, reading that as *carried but unpriced*. That predicate is the
**trade-value fallback** — `position_relative_trade_value_vor`, confidence **35.0** in
`CONFIDENCE_BY_SOURCE`, a pricing source. Only `no_priceable_input` has confidence `None`. The
field would have contradicted its own stated contract on every such row.

**No test could have caught it, and no measurement did.** That branch has **zero rows** on every
board measured (0 of 1,119), so the cross-tab I ran to look for exactly this breach came back
`0 breaches, 0 unclassified` — a clean result about an unreachable branch. Only reading the
branch found it. **A latent contract breach is the shape that survives a green suite**, and it
survives a green measurement too when the population cannot reach it. The classification is now
derived from the **source label** rather than from a second reading of the same two columns, so
*has a kind* and *has no price* are one question asked once (`#126`).

**THE DECISION BOUNDARY CAUGHT MY SECOND MISTAKE, as a red control rather than a surviving
mutant.** To render the kinds I first wrote `import draft_room as dr` into `pick_debate` —
and `test_pick_synthesis.DecisionBoundaryIsClosedTests` failed immediately, correctly. A snapshot
consumer that can import `draft_room` acquires `compute_draft_board` along with the vocabulary,
and the debate's own instruction to the models — *do not recompute* — stops being structural.
The guard's docstring had predicted this exact slip: *"naming it here means a future import of
the board builder itself fails this test instead of slipping in beside it."* The vocabulary now
crosses the way the other four do (`DENIAL_BASIS_LABELS`, `EXPOSURE_BASIS_LABELS`,
`EXPOSURE_MEASURED`, `DISPLACEMENT_BASIS_LABELS`): **re-exported by `pick_synthesis`, which IS
the boundary rather than a consumer of it.** One home in `draft_room`, one crossing, no copy.

**THE KIND HAS A READER, because the suite refused the version where it did not.** Recording it
on the board and stopping there made it a write-only quantity, and
`test_quantity_readers.TheWriteOnlySetMustNotGrowTests` failed on it inside the same pass —
`#119`'s lesson arriving one item later. It is carried to `CandidateSnapshot` and rendered in the
one place a person reads it: the NOT PRICED line now says *which* absence, and the coverage-gap
phrasing denies the inference it invites — *"a COVERAGE GAP, not a low grade"*. A board that
recorded no kind renders **nothing**; the kind is never guessed downstream.

**A `#245` NEAR-MISS, kept because the control is the whole lesson.** The first version of the
population measurement matched board names against the projections table with a hand-rolled
normaliser and reported **0 of 643** rows present — clean, tidy, completely false. The control
caught it: the same matcher found **0 of 475 PRICED** rows too, because `norm_name` abbreviates
first names (`a adebawore`) while board rows carry full ones. The measurement above uses only
fields the row already carries, so no matcher is involved at all.

**WHAT THIS DOES NOT DO.** It does not change any ordering. `absence_kind` is an **observable**:
nothing sorts, scores or ranks by it, and the question the finding actually raises — whether ORDER
LAST is right for a population that is entirely *unknown, not bad* — is a `#50` valuation
decision, not a disclosure one. The repair makes that question askable at the surface where it
would be answered.

**THE SCHEMA RATCHET FIRED, and its second question got a SPLIT answer.** `CandidateSnapshot`
went 48 → 49, and the pin refuses a bare number bump: it demands whether the field implies a
scale the card cannot support, and whether the card should render it. Scale: no — a categorical
token from a closed vocabulary, the same answer `denial_basis` and `depth_basis` got, and it is
spelled as a string precisely so nothing can order by it. Render: **the Prytaneum yes and it
does; the board card NOT SETTLED BY THIS PASS.** That half is named rather than quietly closed,
because this field differs from its three predecessors in a way that matters — they qualify a
number the card either shows or does not show at all, while this one qualifies an **absence the
card already displays as a dash**, and an unexplained dash invites exactly the "he's bad" reading
the item exists to refuse. The case for a marker is real; I did not build or measure one, and a
ruling I did not do the work for is worse than an open question with its reasoning attached. It
routes to the UI passes (`#181`, `#36`) with a binding condition recorded at the pin.

**PINNED:** `test_absence_kind.py`, 23 tests, **mutation-checked 7/7** — collapse two kinds to one
phrase; sever the snapshot carry; remove the prose lookup; classify every row (the latent breach
made live); drop the field from one of the two serializations; re-import `draft_room` into
`pick_debate`; re-derive the predicate instead of reading the source label. The board and
boundary tests run against a **real 81-row board containing one genuinely unpriced row**, not a
hand-built snapshot — that distinction is why two of these seven are caught at all. Evidence:
`evidence/absence_kind/kind_vs_priced.py`.

## #211 — the re-read trigger fired, and Gate 2's ruling reinforces the pin

`#211` was pinned **KNOWN-OPEN-ACCEPTABLE** with a stated trigger: *worth re-reading once Gate 2
is ruled, since it is the metric the roster proof's asset ruler leans on.* Gate 2 was ruled
(`#252`, 2026-09-12). The trigger has fired; this is the discharge.

**The finding stands, unchanged.** `starter_value` sums an asset LEVEL over a starting lineup, so
what it ranks is **positional breadth** — who is forced to start the shallowest player — not
roster quality. `draft_battery.py` says so in its own docstring rather than in a comment
elsewhere.

**Gate 2's ruling does not reopen it; it reinforces the pin.** `#252` holds that the exchange
rate is CONFIGURATION-DEPENDENT and that **no cell's number is the engine's verdict**. A metric
that is reported rather than asserted is exactly what that ruling authorises. The two agree.

**Re-verified, not recalled: `starter_value` has no production reader.** It reaches
`draft_battery.py` (where it is defined and documented), `run_draft_battery.py`'s status line, and
seven `run_*` probes. Nothing in the engine sorts, ranks, maximises or gates on it. The one
production module that could be confused for a reader, `roster_diagnostics.py`, computes its own
`starting_lineup_value` through `lineup_optimizer.optimize_lineup` and merely *cites* the
battery's quantity to explain that both make the same exclusion — a cross-reference, not a wire.

**Verdict: KNOWN-OPEN-ACCEPTABLE, pin retained, trigger discharged.** No code change. It is a
reported line in an instrument, and both the instrument and the ruling say so.

## #216 B4 — the register test called itself "a real producer" and tested a dict literal

`ordinals.py` and `test_ordinal_registers.py` were built earlier this session to give B4's three
registers — `VALUATION_RANK` (the pool), `DRAFT_POSITION` (the clock), `VENDOR_RANK` (the vendor)
— one home instead of eleven docstrings. Returning to close the checklist entry, the artifact did
not survive its own re-reading.

**THE CLASS NAMED `ARealProducerMatchesItsDeclaredDomain` BUILT `rank_by_id` FROM A DICT
LITERAL.** Its fixture enumerated `i + 1` and then asserted the result was one-based and
contiguous — so it tested the fixture's own arithmetic and nothing whatever about the engine.
`rank_by_id` is produced by `draft_strategy._build_opponent_boards`, and the test never called
it. The name is what made this hard to see: a class that says *a real producer* reads as already
having answered the question.

**THE CONTROL, because the claim is otherwise just my reading.** With the producer mutated to
emit **0-based** ranks — precisely the category error the register exists to forbid — the old
test passes **11 of 11**. The rewritten test fails **6**. That is the whole difference between a
guard and a decoration, measured rather than argued.

**The repair is the one #119 and #112 already taught twice this session**: drive the check with a
real value. `setUpClass` now builds a small real pool through the real merger (top-20 by trade
value at four positions) and boards it for three rosters through `_build_opponent_boards`, then
holds what the engine actually emits to the declared domain. Cost: 0.8s, which is cheaper than
the fixture version deserved to be.

**Three tests, three properties, deliberately separate.** A vacuity guard (the producer really
emitted ranks — a domain check over an empty set passes and means nothing); the domain check
itself; and **contiguity, which the domain check does NOT imply** — the domain only rejects
`< 1`, so a producer that skipped or repeated a rank would still price everyone and would simply
stop meaning "the Nth best available", which is what every consumer reads it as.
Mutation-checked 3/3: zero-based, gapped, and empty are each caught by the test written for them.

**WHAT B4 IS, AND IS NOT.** It was never a live defect: `#70` found and repaired the eleven real
crossings by READING, and this pass found no twelfth. What was missing is that nothing held the
distinction in place afterwards. It does now — for one producer, which is stated at the pin
rather than implied. Python still permits any int anywhere; this narrows the blast radius of the
next crossing, it does not abolish it.

**A STANDING NOTE ON THIS SESSION'S PATTERN.** Three items in a row — `#119`, `#112`, `#216 B4` —
had guards that passed while constraining nothing, each because the test constructed the value it
was meant to observe. Two of the three were my own work from earlier the same day. The
distinguishing question is cheap and should be asked of every new guard: **does a mutation to the
PRODUCER fail this test?** If the test never calls the producer, the answer is no, and the green
run is measuring the fixture.

## #206 MEASURED AGAINST REAL DRAFTERS — and my own recommendation is the 30th withdrawal

The owner ruled the take model should be DERIVED from real drafts rather than chosen between two
normalisations. It now has been, and the answer is not the one I argued for.

**THE FORK, as I put it to the owner.** A team picks once, so the take-probability mass over its
board must be 1. It measures **10.73**, and grows with pool size. Two repairs:

| repair | rank-1 `p_take` | survival over 22 picks |
|---|---:|---|
| normalise the FULL mass (head 1.21 + floor tail 9.52) | 0.051 | 0.314 |
| drop the floor, normalise the head only | 0.455 | ≈ 0.00 |

I recommended the second and warned against the first, on the grounds that a model asserting a
team takes its own best player 5% of the time and a tail player 89% of the time is *"arguably a
worse model of drafting than the one it replaces"*.

**MEASURED ON 270 REAL HUMAN PICKS, and the warning was wrong.**

| | rank-1 take |
|---|---:|
| the model today | 0.550 |
| head-only (my recommendation) | 0.455 |
| full mass (what I warned against) | 0.051 |
| **OBSERVED** | **0.030** |

Full-mass lands within two points of reality. **My recommendation is off by a factor of fifteen,
and it is withdrawn in full — the 30th.** The reasoning that produced it ("teams take good
players, so rank-1 must be high") sounds obvious and is simply false about this engine's ranking.

**THE DISTRIBUTION IS NEARLY FLAT, which is the larger finding.** Share of real picks by the rank
the taken player held on the picking team's engine board: **1–5: 13.7% · 6–20: 24.8% · 21–50:
22.6% · 51–100: 18.5% · 101+: 20.4%.** The **median rank taken is 32**; the maximum is 327. So
86% of real picks land outside the five keys `RANK_TAKE_PROBABILITY` is defined over, and the
table's shape — a steep 0.55 → 0.06 decay — describes almost nothing that happens.

**THIS EXPLAINS `#206`'s SYMPTOM EXACTLY, with no constant touched.** Survival multiplies
`(1 − p_take)` over intervening picks. At the model's 0.55 that is 2.3e-8 over 22 picks — the
0.00 the item was filed for. **At the observed 0.030 it is 0.512.** The player survives, which is
what the draft actually did. The defect was never the arithmetic of the mass; it is that the
model's per-pick probability is ~18× too high at rank 1.

**THE INSTRUMENT IS CONTROLLED, because "rank carries no signal" is what a broken rank lookup
also reports.** A synthetic seat that always takes the 3rd-best priced player comes back as
**48 of 48 at rank 3** (`instrument_control.py`). Not circular: taking `board[0]` and asserting
rank 1 would only prove a list can be indexed; rank 3 forces the lookup to agree with the
producer on the order AND on the priced-only filter `rank_by_id` uses.

**THE JOIN IS EVIDENCED SEPARATELY** (`join_decomposition.py`): 301 of 305 real picks resolve,
round-1 control 12/12, ambiguity rejected rather than guessed (`#82`). 31 taken players were not
on the picking team's priced board at all and are excluded from the 270 — reported, not silently
dropped.

**WHAT THIS MAY NOT DO.** The capture's own LIMITS bind: *"ONE league … a data point for testing,
NOT a benchmark. No engine constant may be calibrated to it."* So this does **not** set
`RANK_TAKE_PROBABILITY`. It establishes a DIRECTION with a controlled measurement behind it, and
it is evidence for `#50`, not a patch. A second real board would make it a claim; one makes it a
finding.

**WHAT IT CHANGES ABOUT THE ITEM.** `#206`'s two causes were "take-probability mass" and "rival
agreement". The mass half now has a measured answer and it is bigger than a renormalisation: the
take model's PREMISE — that a rival's board rank predicts their pick — is weakly supported at
best on the one real draft available. Whether to keep a rank-keyed model at all is a `#50`
question this measurement now puts on the table.

---

## `#182` (prose audit, first pass): the terminology guard's protected population was ZERO

The standing order is to audit the prose whenever the queue goes idle. After the checklist
reconciliation the queue *is* idle of anything that is mine — everything still open in Gates 1–6
is either an owner's ruling or blocked on something this machine cannot reach — so this is that
pass. Its first finding is not prose. It is the guard that is supposed to protect the prose.

**WHAT IT CLAIMED.** `test_prytaneum_terminology.py`'s module docstring says it exists to catch
*"a future edit that reintroduces stale pre-Prytaneum product terminology"* — Debate Slab, Debate
Dock, Full Squad Debate, and the rest of `_STALE_TERMS`.

**WHAT IT LOOKED AT.** `Path(__file__).parent.glob("*.py")`. Top level only, non-recursive,
Python only. Not `mockups/`, not any `.html`, not any `.md` but the README.

**THE MEASUREMENT.** Sixteen committed files carry a retired term. **Exactly one is inside that
scan, and it is the guard's own definition file, which the guard explicitly exempts.** So the
live population it protected was **zero**: fifteen of fifteen real occurrences were out of range.

**IT WAS NOT VACUOUS, AND THAT DISTINCTION IS THE POINT.** Control: appending `# Debate Slab` to
`screen_context.py` fails the old test. The guard could fire perfectly well — there was simply
nothing in front of it. This is a different defect from a test that asserts its own fixture
(`#216 B4`), and it fails differently: that one is caught by mutating the producer, this one only
by asking *what population does this actually range over*, and counting it.

**THE REPAIR, AND THE TWO THINGS IT DELIBERATELY DOES NOT DO.**
One scanner (`_stale_carriers`) over the whole repository, across the file types that carry copy
a person reads (`.py .md .html .js .css`); data files are out by rule, because a retired name
inside a captured league is a fact about that capture, not a use of the name.

1. **It does not rewrite the record.** Audit documents and everything under `evidence/` are
   exempt **by rule**, not by a filename list that would quietly grow. These files record what
   was believed when they were written — `FREEZE_CHECKLIST.md` strikes through its own false
   headlines rather than deleting them for exactly this reason. Editing "Debate Dock" out of a
   finding written when the surface was called that would be destroying evidence to satisfy a
   linter.
2. **It does not rename the product.** All thirteen remaining carriers are under `mockups/` — the
   design workspace for the very surface that was renamed. That copy belongs to `#181`, the
   owner's standing UI pass, not to a test. It is pinned as `_MOCKUP_DEBT`, a **count**, so it
   cannot grow unanswered and falls on its own as `#181` works through it.

**A DEFECT IN MY OWN RATCHET, CAUGHT BY MUTATING IT.** The count was first written over FILES.
M1 — appending `Debate Slab` to `mockups/dock_index.html`, which already said `Debate Dock` —
**survived**: the file was already counted, so the total stayed 13 and the guard said nothing. A
term reintroduced into an already-dirty file was invisible, which is most of what a reintroduction
looks like. The ratchet now counts distinct **(file, term) pairs**: reintroduction moves it, a
second copy of a term the file already carries does not. Same population today (13 files × 1 term
each), strictly more sensitive.

**MUTATIONS, 6 of 6 caught after that repair, plus a control.** New term in an already-dirty
mockup (the one that survived) · stale term in a clean mockup · stale term in live product copy
outside `mockups/` · scanner narrowed back to top-level · exemption widened to everything · bare
`"dock"` added to the stale list. CONTROL: a stale term appended to an `evidence/` record leaves
the suite green, which is the exemption working rather than the guard sleeping.

**ONE NAMING FACT THE GUARD NOW PINS.** `"Debate Dock"` is retired; the surface it named is now
**"Debate My Pick"** (README, and `pick_debate.py`'s Strategist/Skeptic/Caller are explicitly NOT
part of The Prytaneum). The bare word *Dock* survives as working shorthand — `#183`'s checklist
line and `test_dock_absence_contract.py` both use it. A guard that flagged the shorthand would be
switched off within a day, so the distinction is now asserted rather than left to whoever edits
`_STALE_TERMS` next.

---

## OWNER RULINGS, 2026-09-16 — the freeze decision set

Eight rulings taken in one sitting, ordered so that anything modifying a later decision was
answered first. The ordering was the point, so it is recorded rather than just the answers:
**what could change engine behaviour was settled before what certifies engine behaviour.** Two
rulings below are recorded as PENDING WORK rather than done, and say so.

### The dependency, stated before the questions were asked

`#150` (what battery evidence the freeze needs) sits downstream of everything that could change
drafting behaviour or change which rulebook must be covered. So `#206`, `#223`/`#225`, the F&F
scope question and `#86` were put first, and `#150` second. `#149` and `#160` are record-only and
depend on nothing, so they came last.

One fact reshaped the first batch and is worth repeating because it was VERIFIED rather than
assumed: `survival_probability` reaches observables, not the pick. `draft_strategy.pick_analysis`
does sort by `opportunity_cost`, but `pick_synthesis` iterates `for row in narrowed` and uses the
analysis only as a lookup keyed by `player_id`, so that sort order is discarded before any
consumer sees it. A `#206` repair therefore does NOT invalidate the existing battery.

### The rulings

1. **`#206` — fix the MASS violation only; the rate is deferred to `#50`.** The five keys of
   `RANK_TAKE_PROBABILITY` sum to 1.21 of a mass that must be ≤ 1.00, which is provable from
   arithmetic alone and so satisfies `#56` (derived, never calibrated). The RATE — model 55% at
   rank 1 against a measured 3.0% over 270 real human picks — is calibration, and the capture's
   LIMITS forbid setting a constant from one league. My own head-only repair stays withdrawn
   (30th). *Pending work at time of writing.*
2. **`#223` / `#225` — documented as known-open, not wired.** No behaviour change.
3. **F&F scope — generic is the certification basis; F&F is corroboration.** Certifying against
   one owner's rulebook would overfit a record for an engine that ships to many leagues; the
   complete 12-seat F&F proof (points 10 of 12, +1.04%) is carried as named evidence beside it.
4. **`#86` — RATIFIED, subject to independent review.** The owner ratified the fractional-curve
   repair and additionally directed a Fable review of it, with anything it finds to be fixed. The
   procedural fault is recorded rather than excused: the repair overrode a standing deferral
   (CDME_CONTRACTS Part 3 and the characterization test both said *open product question*) and
   should have been asked first. *Review pending at time of writing.*
5. **`#150` — the full 34-arm run is the FINAL PRE-FREEZE GREENLIGHT, not an intermediate
   spend.** In the owner's words: *"as the final greenlight before freeze i don't mind a full-arm
   run. just not wantonly in intermediate steps before we think its ready."* This SUPERSEDES my
   recommendation to widen the carry-forward to five axis-spanning arms now — that was precisely
   the intermediate spend being forbidden, and the recommendation is withdrawn. **The binding
   consequence: the run certifies the tree that produced it, so every behaviour-changing change
   must land BEFORE it and only prose and tests may follow.**
6. **`#149` — write down what exists; decline the architecture change.** Executed in
   `attachments.py`'s module docstring, which is where the store lives.
7. **`#160` — VOID the `CONST-A*` prefix entirely.** See below.
8. **Tonight's sequencing — land the work, then run the battery, gated.** Abort conditions
   accepted in advance: if the `#86` review finds anything substantive, or the full suite is not
   green, the battery is HELD and reported rather than run.

### `#160` executed: the prefix is void

The collision was with a ghost. `#161` established by full-history search that **no `BLIND-A1`
has ever existed** — the phrase entered the record once and propagated through seven appendix
headers by copy-paste, each instance drawing authority from the previous one. And `CONST-A1/A2/A3`
appear only in this document's prose, with no constant behind them; the one constant ever named,
`NEAR_TIE_BAND`, belongs to `#56`'s constants contract and is untouched because Decision A is
reopened with nothing to tune.

So there is nothing to rename around, and the prefix is retired rather than re-scoped. **Each
constants question is referred to by the item that owns it.** A numbering scheme whose only
purpose was to disambiguate itself from something that does not exist is worse than no scheme at
all — it implies a second namespace a reader will go looking for.

The prose above that uses `CONST-A1` is NOT rewritten. It is the record of how the collision was
found, and editing the old wording out would destroy the evidence for the ruling — the same
principle FREEZE_CHECKLIST follows when it strikes through its own false headlines instead of
deleting them.

---

## `#206` MASS HALF — MEASURED: one opponent's one pick carries 23.49 of probability mass

The owner ruled (2026-09-16) that `#206`'s MASS half is repaired before freeze and its RATE half
deferred to `#50`. Evidence before repair (`#162`), so this is the measurement; the repair is a
separate commit and is not claimed here.

### The constraint needs no league data

`estimate_survival` asks, for each intervening opponent, *"what is the chance THIS team takes
THIS player at their next pick?"* and answers `_take_probability(rank_on_their_board)`. **A team
makes exactly one pick.** "They take the rank-1 player", "they take the rank-2 player", … are
therefore MUTUALLY EXCLUSIVE, so summed over that team's whole board the probabilities must be
≤ 1.0. Nothing about any league is needed to say that, which is why the repair satisfies `#56`:
it is derived, not calibrated.

### Measured on Fourth and Forever's real captured universe, 12 opponent boards

```
total mass per opponent pick = 23.49          the constraint says <= 1.0

   named keys (ranks 1-5)      1.21     5%
   tail       (476 priced)     9.52    41%
   unpriced floor (638 rows)  12.76    54%
```

**95% of the violation is the FLOOR, not the head — and that reframes the repair.** The obvious
reading of "make the keys sum to 1.0" is to renormalise the five named keys; that moves 1.21 to
1.00 and leaves **22.28 of the 23.49 untouched**. The actual defect is that every one of ~1,100
rows carries a floor probability, so modelled mass grows with the size of the pool. This is
`#244`'s finding reached from the other end: *"the per-opponent take model says a team drafts
6.23 players; a team drafts 1."*

### Two controls, because a confident number here would otherwise be unfalsifiable

**Construction control.** A synthetic board of exactly five priced rows and no tail must report
exactly the sum of the named keys. It reports **1.2100 against an expected 1.2100**. An
instrument that could not reproduce that is summing something other than what it claims.

**Depth control, which exists because all 12 boards report the SAME total** — and `#245` says
identical numbers are a broken instrument until proven otherwise. Here it is derivable: mass
depends only on row COUNTS, and at an empty board every opponent draws from the same pool, so
counts coincide while their ORDERINGS differ by roster need. The proof that the instrument is
live is that draining the pool moves it, by exactly the predicted amount:

```
    0 picks -> priced 481  unpriced 638  mass 23.49
   40 picks -> priced 441  unpriced 638  mass 22.69      40 x 0.02 = 0.80   observed 0.80
   80 picks -> priced 401  unpriced 638  mass 21.89                        observed 0.80
  120 picks -> priced 361  unpriced 638  mass 21.09                        observed 0.80
```

**`unpriced` holds at 638 for the whole drain.** Unpriced rows sort last and are never taken, so
the 12.76 of floor mass they carry NEVER DECAYS. The violation does not wash out as a draft
progresses — it asymptotes toward the unpriced floor, so even at the end of a draft the model
still says one opponent takes about thirteen players with one pick. That is an argument about the
SHAPE of the repair: a fix keyed on the priced board alone would leave the term that does not
move.

### What the derived form predicts, recorded BEFORE it is built

Normalising `P(rank r) = w(r) / Σw` over the board actually present conserves mass by
construction at any depth and introduces no constant. On this board it puts rank-1 at
`0.55 / 23.49 = 2.3%`, against the **3.0% measured from 270 real human picks**. The derived
constraint lands near the measurement WITHOUT being fitted to it — the opposite of my withdrawn
head-only patch (30th), which was off by 15x.

### Two entry-point guards caught me writing the probe against the wrong universe

`build_players_db` refused outright (`#201`: it is the 764-row vendor reconstruction and the real
capture exists), and the F&F league is built exactly as `draft_battery` builds its own CAPTURE arm
rather than reconstructed by hand — `#248` is what happens when a capture is rebuilt:
`build_mock_league` overwrote `rec`, and `rec` selects the rankings EXPORT, so an arm silently read
a different file than it reported.

### CORRECTION to commit `0018729`'s own message

That commit says *"A depth arm … is in flight; this commit does not claim it, and the JSON
carries no depth_arm key yet."* **That is false about its own content.** The depth run finished
moments before staging, so the committed JSON does carry `depth_arm` with all four rows. The
evidence is correct; the sentence describing it is not. Recorded here rather than by rewriting a
pushed commit.

## #206 CALIBRATION: `survival_probability` fails the owner's contract, measured

The owner stated the contract on 2026-09-16: *"survival percentage needs to be a mathematical
representation of what are the chances this player makes it back to my next selection."* That
makes the quantity falsifiable, and `evidence/survival_calibration/calibrate.py` falsifies it.

SMOKE arm, Fourth and Forever rulebook, 12 seats, 10 rounds, 120 picks, **4,503 scored pairs**,
**0 excluded as unmeasured**. Twelve seats drafting under five different but sane policies
(`cdme`, `bpa`, `need_first`, `run_follower`, `mild_reach`), all reading the engine's own
valuations and differing only in the CHOICE rule — the owner's request for variety in selection
that is still good draft behaviour.

```
base rate (actually survived) : 0.7377
engine Brier                  : 0.22480
constant-predictor Brier      : 0.19348   <- the score to beat
oracle Brier                  : 0.00000   <- scorer proven sound
BEATS CONSTANT                : NO
```

**The engine carries less information than predicting the base rate for every player.** This is
not "miscalibrated but directionally useful". It loses to a constant.

### The failure is FLATNESS, on both axes — not the inversion first reported

| gap | predicted | observed | | board rank | n | predicted | observed |
|---|---|---|---|---|---|---|---|
| 0 | 1.000 | 1.000 | | 0 | 55 | 0.842 | **0.091** |
| 4 | 0.977 | 0.903 | | 1-2 | 193 | 0.877 | 0.202 |
| 8 | 0.951 | 0.808 | | 3-4 | 215 | 0.888 | 0.279 |
| 12 | 0.922 | 0.714 | | 5-9 | 532 | 0.919 | 0.457 |
| 16 | 0.908 | 0.618 | | 10-19 | 1070 | 0.912 | 0.706 |
| 22 | 0.885 | **0.491** | | 20+ | 2438 | 0.961 | 0.911 |

Across the full gap range the model moves 1.00 -> 0.89 while reality moves 1.00 -> 0.49. Across
the full rank range it moves 0.84 -> 0.96 while reality moves 0.09 -> 0.91. **Sign right
everywhere, magnitude wrong everywhere.** That is the signature of normalising by a board mass
that is 94.8% unpriced floor: it crushes rank-1's per-opponent take probability to 0.064, and
0.936^22 = 0.23 where the answer needs to be near zero.

The pooled reliability curve first reported a mid-range INVERSION (0.8-0.9 predicting 0.855 and
observing 0.143). Decomposing by gap shows every bucket is monotone, so that inversion was
largely a mixture of short-gap and long-gap turns — a Simpson's-paradox artifact of pooling two
different questions. The claim was held back pending that split, and the split retired it.

### Two controls, one of which caught a real defect in the instrument

**ARITHMETIC CEILING.** At most `gap` of a turn's scored candidates can be taken, because
exactly `gap` picks intervene. On its first run it failed **102 of 108 turns, every one by
exactly +1** — the drafter's own pick. The collector snapshotted seat S's candidates, S took one
of them, and S's own player was then scored as having failed to survive. He never had to survive;
he is S's. The confound landed almost entirely on `board[0]`, which `cdme`, `run_follower` and a
third of `mild_reach` all take, and so on the top rank band the whole result turns on. Excluding
the drafter's own pick moved `rank 0-0` from 0.046 to 0.091 over n=55 rather than n=108, and the
ceiling now holds 108/108. **The pooled curve gave no hint of this.** Write the
impossible-by-arithmetic check before trusting a plausible number.

**gap=0 arrives free and exact.** A turn with no intervening picks must have every candidate
survive. It reports predicted 1.000, observed 1.000, Brier 0.000 — a degenerate case the
instrument now gets exactly right, which it did not before the own-pick fix.

### The LIMITS hold (#56, and the capture's own caveat)

Every number here is a DIAGNOSTIC. None may be written back into the engine as a constant. The
prohibition is not softened by the error being measured rather than guessed: deriving a mechanism
from constraints and reporting how far it lands from reality is validation; picking whichever
mechanism fits one league best is what the LIMITS forbid.

### Consequences

1. **`DECISIVE_SURVIVAL_THRESHOLD` must not be set now**, at 0.5 or any value. A threshold on a
   quantity that loses to a constant is a threshold on noise. The 0.5 recommendation stays
   WITHDRAWN (31st).
2. **The cluster-consumption redesign is strengthened.** The current model asks "what is the
   chance each individual rival takes this specific player" and demonstrably cannot tell. The
   owner's framing — three equally-valued players into a curve, seat 11, at worst 1/3 each — is a
   CLUSTER question, and this is what a model that never asks it looks like.
3. **Freeze scope is now a real decision**, not a formality: v1 either freezes with survival
   mass-correct and shape-wrong and says so in the freeze record, or the redesign lands first.

### Draft Sharks' next-pick odds: verified absent from every input we hold

The owner noted that Draft Sharks models next-pick odds. Checked against every CSV header under
`data/baseline`: **no ingested export carries availability odds, and none carries ADP.** The
columns we hold are rank / projection / proj_3yr / trade_value / ecr / value / tier / std_dev.
Their odds live in the live draft war room, not the ranking exports taken here, so the number
cannot enter the harness as a third scored comparator arm. Supply gap, #49/#88/#143 family.

The structural point survives the absence, and it is the same one the cluster argument makes: an
odds model of that kind rests on a PER-PLAYER empirical distribution of when that player actually
goes. Ours is a RANK CURVE — identical for every player who lands at that rank. FantasyPros'
`best` / `worst` / `std_dev` columns are the shape of the missing input; they are ingested and
read by nothing. Recorded as a candidate input for the redesign, NOT wired.

## #206 RULINGS EXECUTED (owner delegated: "Whatever you need/decide, just make it work")

### DECISIVE_SURVIVAL_THRESHOLD: no value chosen, and the state is dark for a reason that is
### NOT the one I first wrote down

The threshold stays at its declared 0.15 and is now INERT. `SURVIVAL_IS_CALIBRATED = False`
gates `decision_regime` so "decisive" cannot be returned, and the flag is checked against the
committed calibration evidence by `test_survival_calibration_declaration` — the prose cannot
drift from the files it cites, and flipping the flag without the evidence fails the suite.

**Why no value**: both arms measured the engine losing to a constant predictor (SMOKE 0.22480
vs 0.19348; REAL 0.16127 vs 0.14224, oracle 0.0 on both), and it loses WORST in exactly the
band this threshold reads — the 0.0-0.1 bucket on real picks is n=74, predicted 0.028, observed
0.500. Any value there wires a UI state to a coin flip. #56 and the capture's LIMITS forbid
fitting one.

**THE CORRECTION THAT MATTERS, and I nearly shipped the wrong story.** I wrote that the
calibration gate was why "decisive" is unreachable. My own vacuity check — the one this
repo keeps learning to write — disproved it: lift the gate and the state STILL never fires on a
real board. Measured across 8 real board states:

    leader survival            min 0.212, max 0.925
    DECISIVE_SURVIVAL_THRESHOLD              0.15
    boards clearing the tie band             2 of 8    <- not the blocker
    boards with survival <= threshold        0 of 8    <- THE blocker

The real cause is **#206's own mass-conservation repair** (`364042a`). Survival used to be far
too LOW — the symptom that opened #206 was 0.00 for a player who then survived 60 picks —
and normalising each opponent's take mass to 1.0 raised the leader's floor above the threshold.
The test that failed was not reporting a calibration problem; it was reporting the downstream
consequence of an earlier fix. The freeze record must not say calibration darkened the state.

The characterization was INVERTED, not deleted (repo doctrine): the reachability test now pins
unreachability AND FAILS if either cause goes away, so a future repair is forced to re-answer
the question instead of inheriting a threshold nobody re-examined.

### The unpriced floor: DECLINED, with the arithmetic for why

"One block instead of 340 rows" is the obvious structural fix and it OVERCORRECTS badly: one
floor weight (0.02) against a priced mass of 5.27 gives the unpriced block ~0.4% of take mass,
against a measured real rate of 10.3%. That turns a 6.9x overshoot into a ~25x undershoot —
trading a wrong number for a differently wrong number and calling it structure.

The aggregate needs a number we do not have. The only number available is 10.3% from ONE
league, which the LIMITS bar from setting an engine constant. So it stays open, and the
`unpriced_mass_share` disclosure already added to `estimate_survival` keeps it visible rather
than silent. This is a decision NOT to act, recorded as one.

### Carried forward, unchanged by any of this

The value-share take model (`board_contention_scale` / `_value_take_weight`, `ebdbc12`) remains
BUILT AND UNWIRED. It fixes the cluster shape the owner specified and does not fix the
magnitude, both measured. Wiring it is a Phase 3 decision that needs a rerun of both arms
against the post-wiring engine — the current evidence records the pre-repair file hashes
precisely so the two cannot be confused.

---

## #206 / #168 — THE UNPRICED BLOCK IS 82% VENDOR COVERAGE, AND THE ENGINE PRICES NO QB AFTER ROUND 12 OF 30

Two findings from one measurement, plus a correction to a claim published earlier the same day.

### The value-share model was measured, and is NOT wired

Three arms on the real Greatest Show on Paper 2 board, **6,277 pairs, identical population**,
only the take model differing (`evidence/survival_calibration/value_model_arm.py`):

| arm | engine Brier | constant | beats constant |
|---|---|---|---|
| `rank` (production) | 0.16127 | 0.14224 | no (−13.4%) |
| `value_floor` | 0.15050 | 0.14224 | no (−5.8%) |
| `value_zero` *(bound, not a candidate)* | 0.13755 | 0.14224 | yes (+3.3%) |

The `rank` arm reproduces the published 0.16127 **digit for digit**, which is what licenses the
other two — the `_board_take_probability` seam is inert when not substituted. n-weighted mean
reliability error across board-rank bands: 0.1162 → 0.0954 → 0.0448. Production's worst band is
its own top candidate: 0.809 predicted against 0.451 observed.

`value_floor` is the honest straight wiring and still loses, so **nothing was wired**.

### RULED OUT: the unpriced share cannot be derived from roster state (27th withdrawal)

The recommendation — unpriced rows sit at positions whose starter demand is met, so a rival
takes one when drafting depth — was tested before being built and is **withdrawn**
(`evidence/take_model/unpriced_pick_drivers.py`, 301 resolved picks):

| stratum (rounds 14–30) | n | unpriced | mean demand diff | permutation p |
|---|---|---|---|---|
| all positions | 166 | 31 | −0.474 | **0.0158** |
| QB only | 24 | 17 | −0.207 | 0.1310 |
| non-QB only | 142 | 14 | −0.349 | 0.1759 |

Simpson's paradox: the pooled effect is the position mix. Building on it would have put a
derived-*looking* constant into the engine on an artifact. **Nobody needs to re-run this.**

### CORRECTION IN FULL: "the block is the shadow of a pricing gap" was too strong

`VALUE_MODEL_RESULT.md` concluded that from the 31 picks — evidence about which unpriced players
are TAKEN, used to characterise what the block IS. Measured directly
(`evidence/take_model/unpriced_block_composition.py`), the block is **two** populations:

| depth | priced | unpriced | WR | TE | RB | QB |
|---|---|---|---|---|---|---|
| round 0 | 481 | 638 | 254 | 141 | 130 | 113 |
| round 14 | 303 | 648 | 254 | 141 | 130 | 123 |
| round 26 | 161 | 646 | 254 | 141 | 130 | 121 |

The non-QB core (525 rows) is **constant at every depth** — never-priced, a vendor COVERAGE gap
the startable floor never touches, and **82% of the block**. The block's SIZE is coverage; its
TAKE RATE is QB (~5× per row). Both true, different facts, and the original sentence merged them.
The take-model conclusion is unaffected; the attribution was wrong.

### #168 SHARPENED: "bounded to superflex QB tails" understates it

| round | picks | QB priced | QB unpriced | QB drafted |
|---|---|---|---|---|
| 0 | 0 | 42 | 113 | 0 |
| 10 | 120 | 12 | 113 | 30 |
| **12** | 144 | **0** | 123 | 32 |
| 26 | 312 | 0 | 121 | 34 |

**From round 12 of 30, the engine can price ZERO quarterbacks** — 60% of a superflex draft, at
the position the format makes most valuable, and it never recovers. The mechanism is exact: 39
projected QBs, 28 clear the floor (0.5 × QB12 = 162.00), 32 drafted by round 12. Every priced QB
carries `startable_floor` as its basis throughout; **no row is mislabelled** and #185 holds.

### NOT FIXED, and why

The floor's constant is **not** under suspicion — `QB_STARTABLE_FLOOR_FRACTION` has a documented
stability-basin derivation and #56 is not engaged. The open question is a DESIGN one: the floor
asks *"is this QB startable AS A QB"*, while the slot that makes a superflex QB draftable is
SUPER_FLEX, whose occupant competes against flex-eligible non-QBs. That is the cross-position
comparison #229 authorises in principle and #50 owns. **Owner's call, Phase 3.** Sizing a repair
here without that decision would mean inventing a magnitude nobody has argued for (#56).

Production unchanged throughout. `SURVIVAL_IS_CALIBRATED` stays False.

---

## #273 — SLEEPER'S OWN PLACEHOLDER ROWS REACHED THE DRAFT BOARD, ADMITTED BY THE ROOKIE CLAUSE

The captured universe carries **59 rows named literally "Player Invalid"** — Sleeper's sentinel
for an id it will not resolve — with `status=Inactive`, `team=None`, `age=None` and no season
projection. **53 of them were on the board.**

### The cause is ORDER, not a missing rule

`_admits_to_pool` is a union, and its ROOKIE clause returns True *unconditionally*:

```
if sleeper_points is not None:     return True
if years_exp == ROOKIE_YEARS_EXP:  return True     <-- 56 of the 59 exit here
if team:                           return True
if status in NOT_CURRENTLY_PLAYING: return False   <-- never reached
```

56 of 59 carry `years_exp == 0`, so they exit before the status gate that would have rejected
them. The other **3 are correctly rejected** — which is what shows the gate itself is sound.
The rookie clause is unconditional by design ("a rookie cut to a practice squad has no NFL team
listed and no projection"), so a placeholder passes by resembling exactly the case it exists to
admit.

### RULED OUT: there is no structural discriminator in this capture

| candidate signal | rows it matches | verdict |
|---|---|---|
| `active is None` | 6595 of 6595 | separates nothing |
| `search_rank is None` | 6595 of 6595 | separates nothing |
| `active` + `search_rank` + `age` + `team` all None | 564 | catches real players |
| rookie + Inactive + no team + no projection | 146, **90 ordinarily named** | would delete 90 real rows |

The 90 include "Tony Johnson (K), age 25". **A rule that removes 90 real players to catch 56
placeholders is worse than the defect.** Nobody needs to re-derive this.

So the check reads the FEED'S OWN VOCABULARY — the same move `#202` made for PUP/NA/Sus/DNR.
The sentinel is Sleeper's, verbatim in the raw capture, not a list of players this engine
dislikes. If Sleeper changes it, the rows return and the guard says so: the correct failure
direction, since admitting a placeholder is visible while silently dropping real players is not.

### BLAST RADIUS, measured (both arms one process, toggling only this rule)

```
board rows    1119 -> 1066   (53 removed, ALL placeholders)
rows ADDED                0
priced rows    481 ->  481   (unchanged)
surviving rows whose final_score MOVED:  0
```

Surgical. Pool composition feeds replacement levels, so "no price moved" was measured, not
assumed.

### Bounded honestly: this was never a decision defect

`narrow_candidates` was checked at rounds 0/14/22/28 — **zero placeholders ever reached a
candidate list**, because they always sort behind something real. The harm was a human scrolling
the board seeing "Player Invalid" as a draftable row, plus 8.3% of the unpriced block being junk.
Cosmetic and mass-inflating, not a recommendation error.

`test_placeholder_admission`: 9 tests, mutation-checked 4/4 — reverting the rejection, moving it
after the rookie clause (the original bug), matching on surname only, and substituting the
over-reaching shape rule are each caught.

**Register hygiene:** first drafted as `#246`, which is already in use (`run_roster_proof_*.py`)
with the register running to `#272`. Renumbered before commit — `#160` is the standing record of
what a collided namespace costs.

---

## #274 — A PICK WAS DISCARDED OVER A FIELD ITS RESOLVER NEVER READS, AND SIX FAMOUS PLAYERS HAUNTED EVERY LATER BOARD

`observed_take_distribution.resolve_picks` skipped any pick flagged `illegible`. The board's own
provenance says what that flag means:

> "All illegible cells are in slot 12 (MatttyyIce), the one column with no roster view. **Names
> are legible in all but one** (10.12, UI-truncated 'Jacory Croskey-M…'); what is missing is
> **nfl_team/bye**."

It marks a missing BYE WEEK. The resolver matches on `(normalized name, position)` and reads
neither field. So it discarded six legible picks — **Patrick Mahomes, Bucky Irving, Mark Andrews,
James Conner, DJ Giddens, Darren Waller** — and because an unresolved pick never reaches
`engine_picks`, each of those players then sat on **every later board as a phantom**.

### The contamination was not slight, and the prose is why nobody checked

| round | measured picks | max phantoms ahead | mean |
|---|---|---|---|
| 1 | 12 | 0 | 0.0 |
| 10 | 8 | 3 | 3.0 |
| 20 | 9 | 9 | 9.0 |
| 30 | 11 | 10 | 10.0 |

Mean rank inflation **5.56**, max **10**, against a priced pool falling to ~160 rows by round 30.
The instrument's own docstring described this as the board being *"very slightly too full"* — an
adjective where a measurement belonged, wrong by an order of magnitude, and the reason a material
defect read as a rounding note. That sentence is now replaced by the numbers.

### What moved

| figure | contaminated | repaired |
|---|---|---|
| resolved picks | 301 | **307** |
| picks measured (take distribution) | 270 | **276** |
| **top-5 share** | 11.5% | **14.9%** |
| rank-1 share | 2.2% | 2.2% |
| calibration pairs | 6,277 | **6,616** |
| `unknowable` exclusions | 226 *by turn 144* | **152 across all 360** |

Rank-1 is unchanged because rank-1 picks happen early, where no phantom is yet ahead — the
bias was strictly a late-draft effect, exactly as the inflation table predicts.

**All three calibration arms were re-run**; `VALUE_MODEL_RESULT.md` carries the restated figures
with the superseded ones kept beside them. `value_floor`'s gap to the constant HALVED
(−5.8% → −3.1%): phantoms inflate board rank, and board rank is the register the value model is
scored on, so the contamination was suppressing the very quantity under test.

### Three sites, not one — and one of them stated the wrong reason

`join_decomposition.py` and `identity_join.py` carried the same filter. `identity_join`'s comment
asserted the cells *"carry no name to resolve"*, a claim about the data the data denies. Both
repaired and re-derived. Zero `not p.get("illegible")` filters remain in `evidence/take_model/`.

`calibrate.py`'s report also listed every flagged cell under `picks_unresolved.illegible`; with
six of seven now resolving, that would have the report contradict its own `picks_resolved` count.
Fixed to report the outcome, not the flag. **Deliberately held until the arms finished** — editing
the module three arms import, mid-sequence, would have meant they ran different code.

### RULED OUT

`#245` on the identical `unknowable == ghost == 152`: the non-ghost branch is **live**, proven by
the previous run's 226 vs 203 on the same code path. A non-ghost needs the unresolved pick to fall
in the narrow gap between a turn and that seat's next turn AND the player to be nominated at
exactly that turn; with the earliest survivor now at pick 72, that window never lands. Explicable,
not collapsed.

`test_pick_resolution_flags`: 6 tests, mutation-checked 4/4 — restoring the skip, dropping the
placeholder skip, resolving truncated names by prefix (the guessing `#82` forbids), and dropping
the `unmatched` accounting are each caught.

---

## #275 — THE RANK TABLE'S ERROR IS ITS PEAKEDNESS, AND THE TOP OF THE BOARD IS INDISTINGUISHABLE FROM UNIFORM

Visible only once `#274`'s phantoms were removed. Over the 276 measured real picks:

```
rank  1:  6      rank  5: 11
rank  2:  8      rank  6: 10
rank  3:  8      rank  7:  8
rank  4:  8      rank  8:  9
```

χ² = **1.88** on 7 df, permutation **p = 0.966**. Ranks 1–8 are indistinguishable from uniform —
rank 1 is not even the mode.

**NOT a pooling artifact**, which is the check that matters after this session already produced one
Simpson's-paradox withdrawal:

| band | n | χ² | p |
|---|---|---|---|
| rounds 1–5 | 29 | 6.03 | 0.556 |
| rounds 6–12 | 18 | 7.78 | 0.374 |
| rounds 13–20 | 14 | 4.29 | 0.843 |

No stratum is peaked. Small n each, so individually weak — but the pooled uniformity is not being
manufactured by mixing, which is what would have voided it.

### The error is monotone in how much the table peaks

| rank | model | observed | overstated |
|---|---|---|---|
| 1 | 0.55 | 0.0217 | **25×** |
| 2 | 0.20 | 0.0290 | 7× |
| 3 | 0.12 | 0.0290 | 4× |
| 4 | 0.08 | 0.0290 | 3× |
| 5 | 0.05 | 0.0399 | **1× (right)** |

At rank 5, where the table is nearly flat, it is correct. **Its error IS its peak.**

And rank-1 taking decays to exactly zero:

| rounds | rank-1 takes | share |
|---|---|---|
| 1–5 | 5/56 | 0.089 |
| 6–12 | 1/71 | 0.014 |
| 13–20 | **0/75** | 0.000 |
| 21–30 | **0/74** | 0.000 |

**Zero of 149 picks after round 12 took the picking team's own top-ranked player.**

### What this establishes, and what it does not

It corroborates the value-share model's shape from independent data: that model measured 6.6–10.6
effective contenders per board; the real picks say the taken player is uniform across roughly the
top 8. Two different measurements, same answer, and neither was tuned to the other.

It does NOT set a constant (LIMITS: one league, n=68 in the head). It does NOT establish a link
between rank-1 hitting zero at round 12 and `#273`'s QB pricing dying at round 12 — the
coincidence is noted and untested. Nobody should read one into the other without measuring it.

## `#283` (`#182` prose sweep) — THE SHIELD OPENED ON THE SPELLING OF "SPEARMAN", AND THE DOCUMENTS WERE NEVER CHECKED FOR CONSTANTS AT ALL

`#182` is a standing order to audit the prose when the queue idles. Most of the code half is
already mechanised: `prose_names.py` reads every comment and docstring, asks whether each
backticked name still exists, and checks every place the prose states a constant's value. It was
green. **Two things it was doing were wrong, and one thing it was not doing was the larger half
of the job.**

### 1. A HISTORICAL MARKER WAS MATCHED AS A BARE SUBSTRING

The vocabulary that lets prose say *"this is history, not a claim about the current code"* was
tested with `marker in text.lower()`. `arm` is in that vocabulary — for ablation arms — and `arm`
is also spelled inside **Spearman, harmless, harmonize, harmful, alarming** and **disarmed**;
`were` is spelled inside **lowered** and **powered**. Seven blocks across the tree were shielded
by the letters of unrelated words, which means seven blocks of prose were silently exempt from
the check and nothing said which. One was in the live Python corpus
(`test_kdst_integration.py:908`, via *harmless*).

The obvious repair, `\bmarker\b`, breaks it the other way and by more: it stops shielding
`staleness` (49 blocks), `ablations`, `probes`, `counterfactuals`, and identifier-shaped mentions
like `noise_arm`, where `_` is a word character and leaves no boundary at all.

**A marker must BEGIN a word** — `(?<![A-Za-z])` — which keeps all of the morphology and drops
all six leaks, because every leak carries the marker inside a word and every real form carries it
at the front. The hand-kept trailing spaces on `"was "` / `"were "` were the same instinct done
by hand and are now gone; the boundary does that job for all 23 markers from one place (`#126`).

| | shielded, python | shielded, markdown | dead names exposed |
|---|---|---|---|
| substring (as shipped) | 293 | 950 | — |
| word-start (now) | 295 | 966 | **0** |

It moves in both directions, which is the point: this is a repair, not a loosening. **No verdict
changes.** The instrument simply stops being wrong about why it is green.

### 2. MARKDOWN PROSE WAS IN THE HAYSTACK, SO A DOCUMENT COULD VOUCH FOR A NAME

`haystack()` read `*.md` **whole**. The module is built around the rule that prose must not
vouch for itself — it strips comments and docstrings out of the Python for exactly that reason —
and then read every memo in full. The hole that leaves is one this repository is precisely the
shape to fall into: rename a constant, leave one document still naming the old one, and that
document puts the old name in the universe, so **every docstring that also still names it goes on
passing**.

Markdown now contributes its **fenced code** and nothing else, which is the same rule already
applied to Python: code vouches, prose does not. Measured before closing it, the hole was costing
nothing — **0** names in Python prose were vouched for by markdown alone — and the universe falls
31,714 words to 25,189 with no change of verdict. Closed while it was free to close.

### 3. THE CONSTANT CHECK NEVER READ THE DOCUMENTS — WHERE 85% OF THE QUOTATIONS LIVE

`#56` says a constant is derived, never calibrated, and this repository explains its constants at
length in prose sitting beside them. The check for *"the prose states this constant's value and
the code disagrees"* ran over Python comments and docstrings only, which offer **6** quotations of
a known constant. The tracked markdown offers **40**, over 14 distinct constants — 34 in
paragraphs and 6 in headings. The check was reading the smaller population and skipping the
larger one.

Extended. It comes back **0 wrong over 100 single-homed constants**, from 12,762 comments and
docstrings and 7,122 markdown paragraphs — but only after one addition to the vocabulary, and
that addition is load-bearing rather than decorative:

> `POST_AUDIT_PLAN.md:5518` — *"I first registered the acceptance test for
> `SUPER_FLEX_QB_SHARE = 1.0`"*. The constant is **0.85**. The prose is correct and the check
> was right to look: this is `#178`'s pre-registration, a value the constant would have been
> MOVED to had its gate passed. It did not pass; 1.000 was committed at `605e0cb` and reverted.

That is the same speech act as the `NEED_BONUS_MAX = 1e9` ablation arm the vocabulary already
covers — a value named for an experiment, not asserted as current — so `registered` joins the
PROBES half. `doc_index` already carries `pre-?registrat` as one of its own vocabulary words, so
this is a gap in a vocabulary the repository already writes, not a marker invented to make one
site pass. Mutation M6 confirms it: remove `registered` and that site goes red.

### 4. THE DEAD-NAME CHECK WAS MEASURED OVER THE MARKDOWN AND **DECLINED**

`#182` says *every document*, so this was run before being turned down, and the numbers are in a
comment beside `dead_names()` so nobody re-runs it:

```
3,416 backticked-name occurrences (979 distinct) survive the marker filter and are tested
   69 exist nowhere -- but only once markdown prose is out of the haystack, which it now is;
      against the old haystack the answer was a self-vouching 0
   50 survive a shape filter for names shaped like this system's (an underscore, or ALL_CAPS)
    0 of the 50, read at their sites, are defects
```

Every one is a legitimate speech act that Python prose does not perform. A **proposal** naming
words that do not exist yet (`DRAFT_ROOM_UI.md` argues that the curated lens and the full board
need separate names, and names them). An **asserted absence** — `ARCHITECTURE_AUDIT.md` §4.5 is
headed **STATUS: MISSING** and its evidence line is *"no `CONTRACT_VERSION`, `PROMPT_VERSION`, or
equivalent exists anywhere in the tree"*, which **is** the finding. An **experiment label** in a
results table (`kdst_1qb_slot1`, `kdst_deep18` — trial names, never identifiers). Or a register
entry about something long dead.

Making those pass means growing the marker vocabulary until the report reaches zero, which is
calibration to this corpus rather than derivation from it — and this module's own docstring
already records that an instrument at a high false-positive rate is worse than none. **Declined,
with the measurement kept.** A test pins the reasoning in place so the corpus cannot be widened
silently.

### The live documents are clean, and that is now checked rather than asserted

The live half of `CDME_CONTRACTS.md` is §1–§572; every dead name it carries is in the appendix,
which the document's own banner marks as history. `README.md` was already clean from `#182`'s
first pass. The two hits in genuinely live documents were both read at their sites and both are
correct prose.

**AND THE CHECKER CAUGHT ME WHILE I WAS WRITING THIS.** The first draft of the comment explaining
finding 4 quoted its examples properly — `` `httpx` ``, `` `pkill` ``, `` `CONTRACT_VERSION` `` —
and `prose_names.py` reported nine dead names, all mine. A backtick here means *"this is a name
in the system"*, and every one of those is cited **precisely because it is not**. The names in
that comment are now unquoted. It is the smallest possible demonstration that the instrument is
live rather than decorative.

**AND THE MARKDOWN WALK EXEMPTED SIX QUOTATIONS ON ITS FIRST DRAFT.** Deciding that a heading
TERMINATES a paragraph was right — letting it supply marker context to what follows costs 4 of 35
checkable quotations and does not shield the case that motivated trying it. Discarding the
heading was not. Six real quotations live inside one: `NEAR_TIE_BAND = 2.0`,
`NECESSITY_STANDOUT_REFERENCE_GAP = 15.0` and `NEED_BONUS_MAX = 12.0`, each written into an
`### A1`/`A2`/`A3` heading in both `CDME_CONTRACTS.md` and this register. **All six agree with the
code, which is exactly why dropping them would never have been noticed** — a silent exemption in
a brand-new check, found only by asking what the walk was throwing away. A heading is now its own
one-line block: it governs itself, joins nothing, and is checked like any other claim.

**22 tests** (was 11), **7 mutations, 7 caught**, source restored byte-identical each time.
Production behaviour is unchanged — nothing here is on the engine path.

### 5. THREE UNDATED COUNTS, STATED IN THE PRESENT TENSE, ALL DRIFTED

Neither instrument reaches a number written as English rather than as `NAME = value`, so the rest
of the sweep was done by hand against the things this repository can count. Three sites stated a
figure as a current fact with no date and no commit — the shape `#182` already named as *"a figure
that grows stale without anything failing"*:

| site | said | actual | |
|---|---|---|---|
| `engine-measurement/SKILL.md` runtime table | full suite **~800-870s (2100+ tests)** | ~840s, **3,080 tests** | the only row in that table with no date |
| `ENGINEERING_DOCTRINE.md` §the instrument standard | *"the engine is held to **2267 tests**"* | **3,081** ratcheted methods | present tense, undated, in a doctrine |
| `engine-measurement/SKILL.md` §transcribed input | *"the other **2,800 tests**"* | — | a bare count used comparatively |

**The first one is the sharp one, because `#182` had already fixed it once.** The same figure —
literally "~800-870s" — was found stale in `close-register-item` and corrected there, and that
file now says *"This file previously said ~800-870s"* while its sibling went on saying it. One
fact, two homes, and the corrected home was not the one a reader reaches first (`#126`).

Repaired by removing the second home rather than updating it. The runtime table's suite row now
points at `close-register-item`, which keeps a dated history with commits attached; the doctrine
sentence no longer states a count at all, because `ASSERTION_FLOORS.json` is that count's one
home, is regenerated on every close, and has a test that fails when it is stale; the third is
reworded to say what it actually meant — that a box score checked against Sleeper's own published
total is a different KIND of evidence from a suite that checks this repository against itself.

**Checked and CORRECT, recorded so nobody re-runs them:** `README.md` (clean on `#182`'s first
pass and still clean); the live half of `CDME_CONTRACTS.md` (§1–§572 — every dead name it carries
sits in the appendix its own banner marks as history); `engine-measurement`'s five-line fixture,
including the `build_players_db_from_capture` pool size, which measures **6,595** exactly as
written; and every other row of that runtime table, all of which carry the date they were taken.

## `#284` — GATE 1 RE-RUN COMPLETE AND CLEAN: 34 ARMS, 5,652 PICKS, **0 STRUCTURAL FINDINGS**

`FREEZE_CHECKLIST.md` carried one unambiguous open instruction: *"**Gate 1 now needs ONE more
run.** The committed battery describes the engine BEFORE this repair. That re-run is the freeze
gate."* That was written about `#247`. By the time it was picked up, the committed battery
(`1770ef2`/`466c010`, 2026-09-13) was **120 commits** behind HEAD, including `draft_strategy.py`
+374 lines, `pick_synthesis.py` +218 and `draft_room.py` +153. Its clean verdict described a
materially different engine.

### The result

| | committed run | this run |
|---|---|---|
| arms | 34 (33 independent) | 34 (33 independent) |
| picks | 5,652 | **5,652** |
| structural findings | 0 | **0** |
| wall clock | 19,220.8s | **14,460.7s** |
| `commits_present` | `1770ef2`, `466c010` | **`15fcf2c` only** |
| `carried_forward` | `8T_standard`, `8T_standard_SF` | **none** |

The last two rows are the provenance improvement and they matter more than the speed. The
committed run **spans two commits and carries two arms forward** from an earlier one, so two of
its 34 arms were never drafted by the engine it claims to measure. This run is **one commit, zero
carried arms** — every arm drafted fresh by `15fcf2c`.

### What the re-run establishes, stated as a measurement

**Drafting behaviour did not change across 120 commits. At all.** Compared field by field —
`picks`, `findings`, `margins`, `rosters`, `shape`, `strength`, `qualifiers`, `rounds`, `teams`,
`unpriced_at_decision` — **34 of 34 arms are identical to the committed run**, and no arm label
appeared or disappeared, so the format matrix itself has not drifted either.

**Exactly one thing changed, and it changed everywhere: `decisive` is gone.**

```
decisive calls   1,654  ->  0      across all 34 arms
```

This is not a regression, and chasing it at arm 1 rather than hour 5 is what established that.
`#206` measured that survival cannot carry the weight `decision_regime` puts on it — engine Brier
0.16127 against a constant predictor's 0.14224 on real picks, worst exactly where the 0.15
threshold reads (predicted 0.028, observed 0.500) — and the refusal is **enforced in code**, not
merely documented: `decision_regime` will not return `"decisive"` while `SURVIVAL_IS_CALIBRATED`
is False. That enforcement landed at `364042a` on **2026-09-16**; the committed battery ran at
`1770ef2` on **2026-09-13**, three days earlier. So the old run's 1,654 `decisive` calls come from
an engine that could still produce the state, and this run's zero is the refusal working.

**That is also the re-run justifying itself.** The committed Gate 1 battery advertises a decision
regime the engine no longer produces — precisely the staleness the gate exists to catch, and now
demonstrated rather than argued.

### Three things the run confirms without contradicting

- **The unpriced regime stays bounded and never wins.** Only superflex arms reach it at all
  (`12T_half_ppr_SF` 1/180, `12T_ppr_SF` 2/180, `14T_standard_SF` 43/210, `14T_half_ppr_SF`
  42/210, `14T_ppr_SF` 47/210, and the real league 144/312), and **an unpriced candidate won 0
  picks in 0 of 34 arms.** Consistent with `#168`'s KNOWN-OPEN-ACCEPTABLE bound, reproducing the
  committed run's counters exactly.
- **`HEAVY_IDP` and `4WR_TE_PREMIUM` are clean in both runs**, with identical rosters — so
  `#154`'s old "chair cannot field a legal lineup" failure on `HEAVY_IDP` was fixed before the
  committed battery, not by anything since.
- **The real-league arm's negative worth values are `#155`'s tautology, not a defect.** Values are
  measured against the pre-draft replacement ruler and a 26-round draft goes far below it. The
  arm reproduces to the cent: 7 zero-margin picks in rounds 8, 16 and 23, median margin 1.04.

### How it survived a 4-hour run in a container reclaimed on idleness

`BATTERY_REPORT.json` is gitignored and dies with the machine, so it is not a survival plan by
itself. The live report was checkpointed to a tracked path and **pushed** on a timer — eleven
checkpoints, 3/34 through 32/34 — because the git remote is the only store that outlives the
container. Each checkpoint was **validated as parseable JSON before being committed** (the runner
rewrites the report between arms; a mid-write copy is truncated, and a corrupt checkpoint is worse
than none because it looks like protection). The restore procedure was committed BEFORE the first
checkpoint, at `c74efa9`, so it too would survive. No force-push and no amend at any point:
unattended history rewriting on the working branch could drop a real commit, and a dozen
checkpoint commits is the cheaper failure.

**The stale report was moved aside before launch rather than resumed onto.** `--resume` against a
report written by the pre-repair engine is the exact hazard the runner's own comment names — a
run whose arms come from two engines measures neither. That discipline is why `commits_present` is
a single commit.

## `#285` — SMOKE SEATS: THE ENGINE BEATS THE NAIVE DRAFTERS AND **DOES NOT BEAT THE MARKET**

The owner asked for a quality pass distinct from Gate 1's legality pass — *"a pass over with
smoke seats, to determine if it's **good** at drafting"* — against *"several non-engine seats for
variety of various styles"*. Pre-registered at `9273a2c` in
`evidence/smoke_seats/PREREGISTRATION.md`, **before the runner existed**; full numbers in
`evidence/smoke_seats/RESULT.md`.

6 formats, 68 seat runs, pool 481, 2,720.3s. `run_follower` failed the mechanical admission gate
(could not fill 100% of its starting slots) in all six formats and never sat; the field was
`adp`, `need_first` and `points_need`.

### The aggregate says one thing and the per-style breakdown says the opposite

Pooled, the engine wins the `points` ruler in five of six formats (+0.51% to +5.15%). Split by
style — which criterion 4 required **in advance**, on the grounds that *"an aggregate that hides
a loss to one style is the result hiding its own most interesting part"*:

| format | vs `adp` (market) | vs `need_first` | vs `points_need` |
|---|---|---|---|
| `12T_ppr` | **5/12, −0.35%** | 12/12, +3.63% | 12/12, +3.56% |
| `12T_ppr_SF` | **4/12, −1.13%** | 11/12, +1.66% | 9/12, +1.19% |
| `10T_ppr` | **2/10, −0.63%** | 10/10, +3.31% | 10/10, +3.48% |
| `10T_ppr_SF` | **0/10, −2.42%** | 6/10, −0.19% | 5/10, −0.06% |
| `12T_standard` | 12/12, +1.79% | 12/12, +7.09% | 12/12, +7.28% |
| `12T_ppr_TEP` | 7/12, +0.51% | 12/12, +3.73% | 12/12, +4.08% |

**Against market-consensus ADP the engine is behind in four of six formats, level in a fifth, and
ahead only in standard scoring.** It beats both projection-led styles nearly everywhere. Eight of
eleven field seats are projection-led, so the pooled margin is carried by the styles a human
would not play. That is RULE 6 in a subtler form than the one it was written for: nothing here is
as crude as 24 consecutive QBs — every admitted style fields a legal lineup — but `adp` is the
only style encoding what humans actually do, and it is the only one the engine cannot beat.

### The round-one attribution settles the strawman question with data

`composition_by_style` was added mid-item because the pooled counter could not answer it, and the
run was repeated (all six formats **byte-identical** on both rulers — deterministic instrument,
recording-only change). Round-one QB rate by style:

| format | `adp` | ENGINE | `need_first` | `points_need` |
|---|---|---|---|---|
| `12T_ppr` | 0% | 0% | 50% | 47% |
| `12T_ppr_SF` | 0% | 8% | 50% | 44% |
| `10T_ppr` | 0% | 0% | 33% | 50% |
| `10T_ppr_SF` | 0% | **60%** | 33% | 47% |
| `12T_standard` | 0% | 0% | **100%** | **100%** |
| `12T_ppr_TEP` | 0% | 0% | 38% | 33% |

**`12T_standard` is a proven strawman, not a suspected one.** `need_first` opens QB 48/48 and
`points_need` 36/36 — 100%, in a **one-QB league**, which is RULE 6's original failure mode
reproduced by two of three styles. The engine opens RB 12/12. Its margins there measure the gap
between a sane drafter and a broken one.

**`adp` IS PPR-ONLY — CORRECTION, 27th, MINE.** The table is built from one field,
`adp_dd_ppr`. No superflex variant and **no standard variant**. This entry as first written
flagged only the superflex arms; it should also have flagged `12T_standard`, where the control
drafts a PPR-ordered board in a standard league and over-weights receptions worth nothing there.
That is the sole format where the engine beats `adp`, so **that win is against a mis-specified
control too**. The consequence, stated plainly: **the engine does not cleanly beat a
correctly-specified market control in any format measured here.**

On the superflex half: `adp` takes 0% round-one QB in every format including both SF arms, while
the engine goes 6/10 in `10T_ppr_SF` — **the engine responds to superflex and the control does
not.** The SF losses stand as results but against a mis-specified control.

**That leaves three clean comparisons** — the 1QB PPR formats: 5/12 (−0.35%), 2/10 (−0.63%),
7/12 (+0.51%). Against market consensus on its own ground the engine is **at parity**, neither
ahead nor behind by a margin this run resolves. That is the honest answer to *is it good at
drafting*, and it is weaker than the pooled table implies and stronger than the standard-scoring
arm would flatter.

**AND PARITY HERE IS NOT A NULL RESULT THAT MORE SAMPLING FIXES.** It is ambiguous between the
engine correctly trading present-season points for future asset value — what a dynasty engine is
*supposed* to do — and the engine having no edge. The two rulers cannot separate them: `points`
is where the tie sits, and `cdme` is the engine's own objective, where a win is a tautology.
`FREEZE_CHECKLIST.md` already names the reason — no established exchange rate between
present-season points and dynasty asset value. Running more formats or more leagues produces more
samples of the same ambiguous quantity. **Separating the readings requires a ruler on a dynasty
horizon; see `#288`.**

### Two results that cut against the engine

**`12T_standard`'s +5.15% is the weakest number in the set, not the strongest.** Its field
collapses — `need_first` averages 10.94 on `cdme`, `points_need` averages **−2.90** — because
standard scoring inverts the projection-led ordering, and the league takes **7 QBs in round one
of a one-QB league**. The largest margin is measured against the most broken field. Uninformative.

**The engine loses on `cdme`, its own objective, in both superflex formats** — 4/12 at −3.56% and
1/10 at −18.75%, including 0/10 against `need_first` (−26.91%) and 0/10 against `points_need`
(−30.39%) in `10T_ppr_SF`. A `cdme` win is a tautology; a `cdme` **loss** is not. This is the
region `#184` documents as a bounded limitation and where `#177`'s single loss lived — **and this
run makes it larger and better evidenced than `#184` currently records.**

### Instrument defects found and repaired during the run

1. **The admission gate was computed and not enforced.** `style_by_seat` dealt from the full
   `STYLES` table, so `run_follower` — excluded for failing to field a lineup — sat in the field
   anyway. A measured 8/12 was really 11/12. Fixed with an `admitted` parameter and a refusal to
   run on an empty field.
2. **Two guards scanned raw text and matched their own docstrings** — the exact `#200` mistake,
   repeated. Rewritten to walk the AST.
3. **A mutation escaped**: `test_the_floor_never_empties_the_pool` passed `slots=[]`, so the early
   return fired and the guarded line never executed. Replaced with a non-empty unfillable slot
   list plus a companion asserting the floor DOES restrict.
4. **The report recorded a pooled round-one counter and no attribution**, so *"7 QBs in round one"*
   could not be resolved into engine-versus-field — the one question that separates a real win
   from a strawman. `composition_by_style` now records what each style drafted; 5 tests,
   mutation-checked 3/3.

### Pre-registered refusal, kept

**No engine constant is calibrated to this result.** One capture, simulated fields, and the
owner's standing caveat applies: league settings vary enormously and this is a data point, not a
benchmark. `adp` is a static consensus table, not live drafters reacting to a board — the loss to
it is evidence about the engine, not a measurement of the market.

## `#286` — THE PROSE CHECKER COULD NOT SEE ITS OWN MODULE NAME

`prose_names` was reported as a backticked name existing nowhere, cited from a comment in
`run_smoke_seats.py` that was explaining the checker. The name is real; the instrument was blind.

`NOT_ITS_OWN_CORPUS` removes `test_prose_names.py` from the haystack so the checker cannot vouch
for names it mentions only in order to prove them absent. That test module is also the **only**
code-level importer of `prose_names`, so the exclusion that protects the checker erased the
checker's own name from the universe. **72 other tracked module stems were in the same state** —
every one a one-shot probe script, every one a latent false positive waiting for the first
sentence to mention it.

Repaired by deriving the stems from `git ls-files`: a tracked `.py` file's stem is an importable
name in the system whether or not any code spells it out, and it drops out of the universe the
moment the file is deleted — exactly when prose still naming it should go red. Three tests,
mutation-checked 2/2 on the real guards with a negative control that rejects a module-**shaped**
word no file provides.

## `#287` — THE `#205`/`#245` DISAGREEMENT IS THE ENGINE, AND `#205`'s DESIGN NO LONGER REPRODUCES IT

`FREEZE_CHECKLIST.md` carried the two quality results as an open contradiction: `#205` had the
engine losing **67 of 68** seats on `points` against `rp.control_pick`; `#245` had it winning
10 of 12 on the owner's own league. `#285` made this settleable, because its `points_need` style
**delegates to `rp.control_pick`** rather than reimplementing it — so the engine had just been
measured against `#205`'s exact control and had **won**.

Two differences were confounded in that comparison: the field around the control was mixed rather
than uniform, and ~190 commits of engine change sat between the runs. Separated by running
`#205`'s own design at HEAD — one process, one code version, toggling only the field:

| arm on `12T_ppr` | whole field, `points` | vs `control_pick` alone |
|---|---|---|
| **UNIFORM `control_pick`** = `#205`'s design | **12/12, +3.67%** | 12/12, +3.67% |
| MIXED field = `#285`'s design | 11/12, +2.13% | 12/12, +3.56% |

**The engine wins the uniform arm 12 of 12.** Field homogeneity is not the explanation: +3.67%
uniform against +3.56% mixed is the same number. **`#205`'s deficit is a property of commit
`8cee942` and does not reproduce at HEAD.** The contradiction resolves in `#245`'s direction, by
measurement on `#205`'s own terms rather than by argument.

The mixed field is the harder of the two — 11/12 against 12/12 — because it contains `adp`. That
is `#285`'s finding restated from the other side: what the engine cannot beat is the market, not
the incumbent control.

**Scope, stated so it is not over-read.** One format, 12 seats, uniform arm only. The other five
`PROOF_FORMATS` were not re-run uniform. `#285` covers all six mixed, where the engine wins
`points` in five; `10T_ppr_SF` is the exception under both designs and remains the live question
alongside the `cdme` superflex losses.

## `#288` — THERE IS NO RULER LEFT TO BUILD: EVERY DYNASTY QUANTITY IS ALREADY AN ENGINE INPUT

`#285` left the headline finding unresolvable rather than merely unresolved: the engine ties
market consensus on `points`, and that tie is ambiguous between *correctly trading present-season
points for future asset value* — what a dynasty engine is supposed to do — and *having no edge*.
The two existing rulers cannot separate those. `points` is where the tie sits. `cdme` is the
engine's own objective, where a win is a tautology by construction.

The obvious remedy is a **third ruler on a dynasty horizon**. This entry establishes that it
**cannot be built from anything currently in the tree**, so that nobody spends a week discovering
it the hard way.

### Every multi-season quantity is already an input to `cdme`

| quantity | already read by the engine? | where |
|---|---|---|
| `proj_3yr` | **yes** | `time_horizon_adj` is computed purely from `proj_3yr`/points percentiles, and scales `RISK_ADJ` per player |
| `trade_value` | **yes** | it is a `bpa_source` — `position_relative_trade_value_vor` |
| `rank` | **collinear** | `#165` measured rho of .92 to .99 in magnitude across `proj_3yr`, `trade_value` and `rank` |

A ruler built from any of them is not independent of the thing it would be judging. It
**recreates the tautology** rather than escaping it — the engine would be scored on a
transformation of its own input. That is on top of the defects already registered against the
material: `#147` (the anchor has a one-season lifetime and fails invariant 5) and `#179`
(`proj_3yr`'s RB penalty is age-conditioned and the engine sees only the collapsed point
estimate).

### What an independent ruler would actually require

**Realized outcomes the engine has never seen** — actual subsequent-season results for the
drafted players, scored under each league's rulebook. That is not a code change and not a
modelling choice; it is an input the repository does not have. **Same blocker class as `#49`.**

A second, smaller input is needed for the same finding: **a correctly-specified market control.**
The ADP table is built from one field, `adp_dd_ppr` — PPR only, no superflex variant and no
standard variant — so the only market-like style in the field is mis-specified in three of the
six formats measured (both superflex arms and `12T_standard`). Also external data.

### The consequence for the freeze, stated so it cannot be softened later

**The engine has no demonstrated edge on any ruler independent of its own objective, and that
cannot be resolved with the data in this repository.** This is not a gap that more formats, more
leagues, or a better harness closes. `#285` and `#287` are the end of what the current inputs can
say about draft quality.

This does not by itself decide the freeze — a documented "no demonstrated edge" is a legitimate
thing to freeze against, and `#284` (legality, 34 arms, 0 findings) is unaffected. It does mean
the freeze record must say it plainly rather than resting on the `cdme` margins, which are
tautological, or on the pooled `points` margins, which `#285` showed are carried by beating
styles nobody would play.

## `#289` — THE FREEZE CONDITION, TESTED: `adp` IS THE STRONGEST SEAT, AND THE CLEAN LOSSES ARE ~0.6%

**OWNER'S CONDITION (this session), verbatim in effect:** *"If you can support the position that
adp-smoke draft a strong board as well, so some losses, as long as not aggregious, still reflect
us drafting strongly, then freeze, option 1. Otherwise, option 3."*

Tested rather than asserted, against the committed `#285` artifact.

### `adp` is a strong board, on four independent grounds

1. **It ranks first of all styles in all six formats**, on the `points` ruler.
2. **It beats the greedy points-maximiser on that maximiser's own ruler**, by +2.34% to +5.39%.
   `points_need` takes the highest-projected player at a position it still needs to start — greedy
   maximisation of exactly what `points` scores — and `adp` beats it anyway, in every format. A
   market ordering therefore carries real information about scarcity and lineup shape that the
   projection sheet does not. **This is the load-bearing fact: `adp` is not a baseline, it is a
   good strategy.**
3. **Its behaviour is realistic** — 0% round-one QB in the 1QB formats, WR/RB-heavy (`WR`:29 /
   `RB`:19 in `12T_ppr`), which is what human drafts look like.
4. **It fills 100% of starting slots**, so it clears the same admission gate every style faced.

### The clean losses are small, and two of three are not distinguishable from zero

Seat control makes this a PAIRED comparison — in each run the engine and the `adp` seats draft the
same board from the same pool, differing only in chair — so the per-run difference is the unit and
its own spread is the noise scale.

| clean format | engine − `adp` | t | reading |
|---|---|---:|---|
| `12T_ppr` | −7.73 (−0.35%) | −0.74 | indistinguishable from zero |
| `10T_ppr` | −14.64 (−0.63%) | **−2.45** | small but systematic |
| `12T_ppr_TEP` | +11.70 (+0.51%) | +1.31 | indistinguishable, leaning ahead |

The single genuine deficit is **−0.63%**, roughly 0.9 points per week across a season, while the
engine beats both other styles by 3.3–4.1% in the same arms.

### Verdict, and what it does NOT say

**The condition is met.** The engine drafts at the level of the strongest realistic opponent in
the field and clearly above the projection-led ones. Losses at this magnitude reflect drafting
strongly. **Freeze proceeds (`#53`).**

This does **not** overturn `#288`. "Drafts as well as the market" and "has no demonstrated edge
over the market" are the same result read from two sides, and the freeze record states the second
one. Nothing here is an edge claim.

### Carried to `#184`: the superflex deficits are NOT borderline

The same paired test, run on the superflex arms, returns `12T_ppr_SF` t = **−2.74** and
`10T_ppr_SF` t = **−5.86** at 0/10. Those are against the PPR-only, mis-specified `adp` control
(`#288`), so they are confounded and cannot be read as clean magnitudes — but they are
systematic, not chair luck, and they sit on top of the `cdme` losses in the same two arms. This
strengthens the case for restating `#184`'s bound at its measured size.

## `#290` — BRANCH HYGIENE: TWO WORKTREE BRANCHES DELETED, TWO FREEZE MARKERS DELIBERATELY KEPT

Owner asked whether the remote tree could be reduced to main plus the UI branch. It cannot, and
the reason is worth recording because **two of the branches that look like cruft are not**.

### ~~Deleted~~ ~~BLOCKED-EXTERNAL~~ **DONE BY THE OWNER — both branches deleted, verified gone**

**FINAL STATE (third disposition on this entry, and the last).** The owner deleted both from the
GitHub branches page. Verified from this side by `git fetch --all --prune`: `origin` now carries
exactly five refs — `main`, the working branch, `ui-authority-pass`, and the two freeze markers.
Neither worktree branch resolves any more.

**The `#239` footgun is retired**, not merely documented: there is no longer a worktree-shaped
remote branch for a local worktree of the same name to bind to.

**The ordering lesson from the correction below was applied here** — the deletion was verified
against the remote BEFORE this line was written, rather than the other way round.

The two subsections that follow are kept as the reasoning that licensed the deletion, and as the
record of how the entry got its disposition wrong in between.

### ~~Deleted~~ ~~BLOCKED-EXTERNAL~~ **DONE BY THE OWNER — verified gone**

**FINAL STATE, third and last disposition on this entry.** The owner deleted both from the GitHub
branches page. Verified from this side with `git fetch --all --prune` **before this line was
written**: `origin` now carries exactly five refs — `main`, the working branch,
`ui-authority-pass`, `pre-blind-audit`, `pre-hull-extraction`. Neither worktree branch resolves.

**The `#239` footgun is retired rather than merely documented**: no worktree-shaped remote branch
survives for a local worktree of the same name to bind to.

The ordering lesson from the correction below was applied here — the outcome was confirmed
against the remote first, then recorded. The two subsections that follow are kept as the
reasoning that licensed the deletion, and as the record of how this entry's disposition was
wrong in between.

### ~~Deleted~~ **BLOCKED-EXTERNAL — identified as deletable, and the delete is REFUSED**

**CORRECTION (28th, mine), struck in place rather than edited away.** This section as first
written said these branches were deleted. **They were not.** `git push origin --delete` returns
**HTTP 403** on both, three attempts each, and the GitHub MCP server exposes `create_branch` with
**no delete-ref counterpart**. The entry was written and pushed before the deletion was attempted
— the SHAs were recorded first precisely so the deletion would be recoverable, and that ordering
is right, but it let a claim of completion reach the register ahead of the act.

**This is the same refusal `#135` hit**, and the source is now pinned down, which that entry
never did. `#135` recorded the freeze marker being a BRANCH "because tag refs are 403" without
saying whose 403 it was.

**It is GitHub's, not the sandbox's.** The agent proxy logged no rejection for the delete, and it
demonstrably does log them — it reported a `connect_rejected` for an unrelated host in the same
session. So the refusal is the **scope of the GitHub credential this session runs on**: it may
create and fast-forward refs, and may not delete them.

That matters for where a future reader goes to fix it. Not the proxy, not the network policy —
**the repository owner's own access is not scoped this way, and can delete these in two clicks
from the GitHub branches page or with `git push origin --delete` from a local checkout.** The
constraint is on the agent, not on the repository. Registered BLOCKED-EXTERNAL alongside `#143`,
with the remedy being a human with ordinary push access rather than any change here.

The analysis below stands; only the disposition changes from *done* to *blocked*. Deleting these
two needs someone with direct repository access, and the SHAs are recorded here for exactly that.

### Identified as deletable — verified to carry no unique work

| branch | tip SHA | contained in |
|---|---|---|
| `worktree-agent-a0a78a88e2d0163fe` | `cf8fa0ced8de41dc9ff8e0d84d061c9142a83744` | `main` (0 commits ahead of it) |
| `worktree-agent-ab5e1af412aeb9182` | `b5d00e7df895bbc90158fc5b11f2892ae0b1b788` | the working branch (0 commits not already in it) |

**SHAs recorded here on purpose**: a deleted remote branch is recoverable by SHA while the object
survives, and a deletion whose only record is a chat message is not a record. (In the event the
delete was refused — see the correction above — so the SHAs now serve as the work order rather
than the undo.) The second one
looked like the risky delete — it is **317 commits ahead of `main`** and tipped at `#247` — but
every one of those commits is already reachable from the working branch, so nothing is lost.

Deleting these **would** remove a live footgun, and that remains the reason to want it: `#239`
was caused by a worktree branch sharing a name with a stray remote of its own name, which sent
bare pushes to the wrong branch. **That footgun is still loaded**, because the delete is refused.

### KEPT — these are freeze markers, not leftovers

`pre-blind-audit` (`#135`) and `pre-hull-extraction` (`#136`) exist **because tag refs return 403
in this environment**. They are branches standing in for tags. They are 0 and 1 commits ahead of
`main` respectively, so they read exactly like stale branches, and deleting them would destroy
freeze history that **cannot be recreated as a tag here**. Anyone tidying this remote in future
should read this paragraph first.

`ui-authority-pass` is kept as live work (137 commits ahead of `main`).

### Merge state, verified the same day

A trial merge of the working branch into `main` is **clean**, and the resulting tree is
byte-identical to the working branch's own tree (`336f865635a85c2df7a1f5c3273286d57cb986c0`). So
`main` contributes no content; the working branch's "50 behind" is history shape from the PR #2
merge commit, not missing work. **Merging is lossless whenever it is wanted** — deferred until
`#53` is written, per the owner, so the evidence and the conclusion land together.

## `#291` — CI HAS BEEN STRUCTURALLY RED FOR WEEKS, AND THE RENDER TRACE WAS BLIND TO THE VIEW IT GUARDED

Found while tidying the branch list, not by looking for it: every branch on the GitHub branches
page showed `0/2` checks with a red X, **including freeze markers two weeks old**. A failure that
old and that uniform is not a commit's fault.

### It never reached the tests

The `fast` tier dies at step 5 of 7, on `render_trace.py --check`:

```
render trace CHANGED (607 -> 619 calls)
```

### The mechanism, established by contradiction rather than guessed

The same commit **passed locally and failed in CI**. That rules out a code change outright, and
the UI being flagged (`fa_sort_header`) landed 2026-09-01, six days BEFORE the trace was last
recorded — so it was never an un-regenerated change either.

The variable is the network, reached through a second seed nobody seeded:

| | `api.sleeper.app` | `get_players()` | free-agent view | calls |
|---|---|---|---|---|
| this sandbox | **403** (`#143`) | **0 players** | empty — falls to the "no free agents" caption | **607** |
| GitHub Actions | reachable | the real player database | sort header + debate chip render | **619** |

Measured, not inferred: `get_players()` returns 0 here, `curl` to Sleeper gives
`CONNECT tunnel failed, response 403`, and no player cache is committed.

`_seeded_session()` seeds `league_snapshot`, which gets the trace past the sync screen. It did not
seed `st.session_state.sleeper_client`, and app.py builds its player universe from that client
independently. **So the fixture only ever matched the environment that recorded it.**

### Two failures, and the quieter one is worse

1. **CI could not pass.** A fixture recorded without a network cannot be reproduced by a runner
   that has one. `#113` records CI as a shipped guarantee at `850b8b5`; it has been guarding
   nothing since at least `main`'s own run on 2026-09-02. **Every push in that window, including
   all of this session's, went unverified by the automated gate.**
2. **The instrument was blind to the view it exists to protect.** The recording was made with an
   EMPTY free-agent pool, so the twelve calls that render the sort header and its debate chip
   were never covered. A UI refactor could have deleted that whole block and the trace would
   have stayed green. That is this repository's recurring failure shape — coverage that looks
   like coverage — inside the instrument built to catch it.

### The repair

`_seeded_session()` now seeds the client, overriding **only** `get_players`, from
`rdb.build_players_db_from_capture()` — the same committed universe the draft battery certifies
against (`#126`: one home, derived rather than a second hand-built pool). That builder **raises**
on a missing capture instead of falling back, so the seed cannot silently revert to a live call.
Everything else on the client stays real, because app.py also reads `cache_dir` off it.

**Verified by reproducing CI's failure locally first.** With the seed in place this sandbox
produces 619 calls — CI's number, not its own — and the same twelve lines in the same order. Only
then was the fixture regenerated: **13 insertions, 1 deletion**, the empty-state caption replaced
by the twelve real calls, no other view touched. Two consecutive checks agree at 619.

The regeneration is repairing a fixture that was wrong, not moving a goalpost to meet a result —
and the distinction is checkable, because the new number was predicted from CI's logs before the
file was rewritten.

### The FULL suite has now run in CI, with a network, for the first time

Fixing the fast tier exposed a second hole rather than closing the question. The `full` job is
gated `if: github.event_name != 'push'`, so **only 845 of 3,111 tests ever run on a push** — and
with `needs: fast` failing, the full tier had been skipped entirely for as long as the fast tier
was red. **Every full-suite run this project has on record was executed in a network-DENIED
environment**, which is precisely the condition that hid this defect.

That is a bad thing to discover during a freeze merge, so it was flushed out deliberately:
`workflow_dispatch` on `2da0b0e` (run 539), which is not a push and therefore runs both tiers.

**Both jobs green. The whole suite — 3,111 tests — passed in CI with network reachable**, in 9m
49s. No further network-dependent behaviour exists in the suite; this defect was the only one of
its kind. `#53` can state that the full suite is verified in both conditions rather than only the
denied one.

## `#292` — THE TASK LIST IS NOT THE RECORD, AND SAYS SO BEFORE THE BLIND PASS READS BOTH

The session task list and this register disagree, in ways that are obvious on inspection and
would be actively misleading to a reader who did not know which one to trust:

- entries sitting at `in_progress` whose own text records a completed outcome (`#173`, `#215`);
- entries sitting at `pending` whose text begins "DONE at `<sha>`" (`#242`, `#243`, and others);
- **numbering drift** — one entry reads literally *"task id 212 — ids drifted, code/commits say
  213"*, so the same item has two numbers depending on where it is read.

**RULING: `POST_AUDIT_PLAN.md` is the record. The task list is a working view and is not
authoritative.** Where they disagree, this file wins, and a commit SHA in an entry beats any
status flag anywhere.

**Why this is written down rather than fixed.** Reconciling ~245 task entries against the
register would mean inferring the state of items nobody is presently working on, and a
wrong-but-confident status is worse than a visibly stale one — that is `#37`'s whole lesson, an
item reopened purely because its completion evidence could not be located. Guessing at those
states to make two lists agree would manufacture exactly that class of defect at scale.

**CONFIRMED THE HARD WAY, hours after this was written.** The container was reclaimed and the
session task list came back **empty** — the next task created was numbered 1. The ~245 entries
were never in the repository at all; they lived in session state and did not survive it. This
register did, because it is committed. The precedence ruling above was argued on consistency
grounds and turns out to rest on something blunter: **one of these two artifacts is durable and
the other is not.** The live path was re-created as three dependency-linked tasks (`#53` → cut
the marker → `#52`); everything else that mattered was already here.

**The trigger for writing it now is `#52`.** The blind adversarial pass reads this repository
without the conversation around it. A reader encountering both artifacts would either waste the
pass reconciling bookkeeping, or file findings against statuses that were never the record. This
paragraph is what stops that, and it costs nothing but its own honesty about the drift.

## `#53` — THE FREEZE RECORD IS WRITTEN: `FREEZE_RECORD.md`, candidate `b6748f8`

Reconciliation and freeze candidate, the last item before `#52`. The record is a separate
document because `FREEZE_CHECKLIST.md` answers a different question — *what is left before the
freeze* — and conflating the two is how a checklist becomes a claim.

### What it says, in the order it says it

It **opens** with the ceiling rather than burying it: *the engine has no demonstrated edge over
market consensus on any ruler independent of its own objective, and the data in this repository
cannot establish one.* Everything else in the document is bounded by that sentence, and it is
first so that no reader can quote a margin without it.

Then: what IS established (legality across 34 arms, `#284`; quality at parity with a strong
market control and clearly above naive ones, `#285`/`#289`; the `#205`/`#245` contradiction
resolved by measurement, `#287`). Then what is NOT (the `#288` ceiling and why no third ruler can
be built; the ADP control mis-specified in three of six formats; `12T_standard` a proven
strawman). Then the limitations carried IN — `#184` at its restated size, `#206`'s enforced
refusal, the undefined mode transition, `#146` un-wired — each with its reason.

### Two things it refuses to round off

**The CI caveat.** `#291` restored the gate at `2da0b0e`; it was not continuous, and the record
says so in the section that licenses the freeze rather than in a footnote. Every commit between
2026-09-02 and that repair was verified by local runs only. And until run 539 every full-suite
execution on record was network-DENIED — the same condition that hid the defect — so that hole
was closed deliberately before a merge could find it.

**The reconciliation table.** `#53` is a reconciliation, so the nine places the documents
disagreed are listed with which way each resolved, rather than silently harmonised. Two of the
rows are my own published errors, struck in place: the 27th (ADP's mis-specification was
narrower than reported, which weakened the engine's case) and the 28th (a deletion recorded
before it was attempted).

### What it explicitly does not license

An edge claim; calibrating any constant to this evidence (`#56`); superflex confidence (`#184`);
the UI track; or pre-empting `#52`, which stays unbriefed and unscored.

**Next: cut the marker as a TAG (`#290` — the 403 was the agent's credential, not the
repository), then `#52`.**

## `#293` — THE FREEZE IS CUT: tag `v1-freeze` at `6599b1e`, and it is this repository's FIRST TAG

Published by the owner as a GitHub **pre-release**, deliberately rather than as a normal release.
Three reasons, and the third is the load-bearing one: the repository is public and a normal
release is auto-labelled "latest", which reads as production-ready; `FREEZE_RECORD.md` declines
to license an edge claim and carries `#184` un-repaired; and **`#52` has not run.** `#162`'s
order is *freeze before blind audit*, so this marker exists precisely to be audited — calling it
production before that inverts the sequence it was built to respect.

### The marker is a TAG, which has never happened here before

Every prior freeze marker is a BRANCH — `pre-blind-audit` (`#135`), `pre-hull-extraction`
(`#136`) — and `#135` recorded the reason as *"tag refs are 403"* without ever establishing whose
403 it was. `#290` established it: **the agent credential, not the repository and not the network.
Re-verified this session** — a tag push fails the same way a branch delete does. The owner's
access has no such limit, and this tag is the demonstration.

**Consequence for `#135` and `#136`:** their markers can now be re-cut as real tags and the
branches retired. Not done, and not urgent — recorded so the next reader knows it is possible
rather than inheriting the old "tags are impossible here" belief, which was never true of the
repository itself.

### The tag is three commits past the commit the record names, and that is fine

`FREEZE_RECORD.md` names `b6748f8` as the candidate; the tag sits at `6599b1e`. **No engine or
test code differs between them** — `git diff --name-only b6748f8 v1-freeze` returns no `.py` file,
only the record itself, `FREEZE_CHECKLIST.md`, this register, `DOC_INDEX.md`, and one inert
config (`.claude/blind-pass.settings.json`). The tree frozen is the tree measured; the extra
commits are the act of writing the freeze down.

Both numbers are kept rather than one being quietly rewritten to match the other: **`6599b1e` is
the freeze, `b6748f8` is what every measurement was taken against.** Collapsing them would lose
the distinction, and this register's whole habit is that a dated measurement keeps its own commit.

### What remains

**`#52` alone.** Deny rules are committed at `.claude/blind-pass.settings.json`, inert until
copied over `.claude/settings.local.json`, with the verification step written into the file
because a denial that silently failed to apply would be believed.

## `#52` PROTOCOL — PRE-REGISTERED BEFORE ANY FINDING ARRIVED

Two blind passes launched concurrently against `v1-freeze` (`6599b1e`), on Fable, each in its own
isolated git worktree. **This entry was written while they were still running**, so the conditions
cannot be fitted to whatever comes back — the same discipline `evidence/smoke_seats/PREREGISTRATION.md`
applied to the quality pass.

### Why TWO, and why IDENTICAL mandates

Splitting the two by territory — one on the engine, one on the instruments — would cover more
ground. It was **rejected**, because choosing where each one looks is a soft form of steering, and
because it destroys the property that makes two runs worth more than one:

**With identical open mandates, a finding both reach independently is stronger evidence than
either reaching it alone.** Convergence becomes signal. Divergence still yields the extra coverage,
because the search space here is far too large for two passes to land in the same places. Split
mandates give up the first to buy the second; identical mandates get both.

### The denial is INSTRUCTIONAL, not enforced — stated plainly because it is the weaker option

`.claude/blind-pass.settings.json` denies the cheat-sheet paths at the permission layer, and
**that is not what is protecting these two passes.** Subagents inherit the launching session's
tool access, so the deny rules could not be applied to them. The denial is therefore an
instruction naming each forbidden path, which this register already recorded as the weaker
mechanism.

Three things compensate, and they are recorded so a reader can discount the result appropriately:

1. **Every forbidden path is named explicitly** — `FREEZE_RECORD.md`, `FREEZE_CHECKLIST.md`,
   `POST_AUDIT_PLAN.md`, `evidence/smoke_seats/`, `evidence/batteries/`. A vague instruction would
   have been undone by the first file opened.
2. **The pointer hazard is named in the mandate itself.** Every long-lived document now carries a
   banner saying where current state lives, which for a blind reader is a signpost to the answers.
   Both passes were told the banner exists and to ignore it.
3. **Contamination is SELF-REPORTING.** Each was told that accidentally reading a forbidden path
   must be declared prominently, that a contaminated pass which admits it is still useful, and
   that there is no penalty. This converts the failure mode from silent to visible, which is the
   only property that actually matters — an undetected contamination would be believed.

### Conditions carried from the docket

UNBRIEFED (no finding, no history, no prior conclusion in the mandate) and **UNSCORED** — both
were explicitly told not to assign a grade, verdict, or readiness judgement, because a scored
pass invites tuning toward its rubric. They were also told a well-supported null result is a real
contribution, so that "found nothing here" is available to them as an honest answer rather than
something to avoid.

Read-only: neither may modify a file, and the worktree isolation makes that structural rather
than merely instructed.

### What this entry does NOT do

It does not predict the findings, and it takes no position on whether any will be material. That
is the point of running it.

---

## `#52` PHASE 8 — K AND DST PRICED FIVE ROUNDS EARLY BECAUSE THE BOARD RANKS ON WORTH, NOT ON URGENCY

The defect is not in what K and DST are valued at. It is that the engine computes the quantity
that answers "take him now or later", renders it to the user, folds it into `pick_necessity` —
and lets neither ordering authority read it.

### The measurement that names it

The first defense of a 16-round `12T_ppr_K_DEF` draft, pick **5.09**, from the snapshot the
engine itself stored:

| field | value |
|---|---:|
| `tav` | **34.47** |
| `uv` | 30.47 |
| `forfeit` | **0.13** |
| `necessity` | **CLOSE CALL** |

**34.47 of value bought for 0.13 of urgency, in round 5, rendered as a CLOSE CALL.** Both numbers
sit in the same snapshot on the same board. `positional_forfeit` occurs zero times in
`draft_room.py`; `pick_synthesis._board_order` keys on `(fills_required_slot, final_score,
unpriced, player_id)`; `team_acquisition_value` has no forfeit term. Across the draft the board's
chosen position was not the one forfeit ranked most urgent on **137 of 192 picks**.

### What it rules OUT — four candidates, all killed before the real one

Recorded so nobody re-runs them. Each was a substitute for the number already on the board.

- **A discount multiplier on K/DST `bpa`** needs factor **−1.96**. Zeroing their `bpa` entirely
  still leaves the top DEF at +4.00, ahead of everything from round 8 on. Scaling a term that
  measures value cannot express a fact about timing.
- **Widening the replacement band** moves nothing: −1.05 at DEF (the *wrong* way), +0.89 at K,
  5.15 at TE at the widest. A symmetric window on a locally straight curve returns its own
  centre. See the band section below.
- **`waiting_cost`** points the wrong way (35.90 for the top DEF) because it measures drainage to
  the end-of-draft floor, not the cost of waiting one turn.
- **ADP** carries no signal here. Every DEF is `16983` and every K `~18000` — the vendor's
  *undrafted sentinels*. That is absence, and reading it as "the market takes them late" is the
  `#187` defect this repo forbids.

### The band question, answered and withdrawn

The owner challenged the claim that three candidate replacements sitting in a six-point band
proved replacement was well-determined. The challenge was right twice over: the three candidates
are adjacent ranks on one curve (DEF12, DEF13, ~DEF14-15), and six points is tight only against
the values at the position that produced it. Converted to the unit the board resolves in, a
six-point band spans **1.4 ranks at WR, 1.7 at RB, 2.0 at QB, 2.1 at TE — and 5.1 at DEF, 13.4 at
K.**

Per-position bands were then measured properly, using the closed form of the stability-basin test
`QB_STARTABLE_FLOOR_FRACTION` already states (the basin of rank r IS the marginal gap
`s[r-1] - s[r]`; the instrument reproduces the documented QB cliff unpointed). Result: **K and DST
are not a clean exception class.** By basin/median at each position's own demand rank, RB 3.48 and
QB 3.44 are cliffs, TE 2.84 and DEF 2.14 are edges, and **WR 0.45 is smoother than DEF**. K at
0.10 is alone.

**No ruling is requested on band width, because the null check withdrew the question.**

### The repair

`build_snapshot` re-orders its narrowed candidates on

    acting_now_value = team_acquisition_value - position_next_turn_value

the subtrahend being the position's own curve walked down by the same `expected_taken`, through
the same `_curve_at`, that produces `forfeit`. **No constant is introduced — `#56` is not
engaged.** Both operands are numbers the engine already computes; what changed is which one the
order reads.

The first implementation was wrong and the measurement caught it: subtracting forfeit's
team-AGNOSTIC curve from a team-relative candidate ADDS the team terms instead of cancelling
them, leaving every K and DEF holding a flat **+4.00 `need_bonus`** for a slot still empty at the
next turn — the same defect in a different term. Building the alternative on the `final_score`
curve makes both operands describe a player landing on the same roster, and for the best player
at a position `acting_now_value` now equals `forfeit` exactly.

### Measured, one process, one code version, toggling only the key

| pos | first rd before | after | median before | after | taken before | after |
|---|---:|---:|---:|---:|---:|---:|
| DEF | 5 | **7** | 10.0 | **15.0** | 27 | **13** |
| K | 7 | **10** | 10.0 | **14.5** | 29 | **14** |
| TE | 1 | 1 | 13.5 | 10.0 | 28 | 40 |
| RB | 1 | 1 | 4.5 | 6.0 | 40 | 49 |

Authority disagreement falls from **137 of 192 to 7**. And the cost, on the rosters produced —
best legal lineup via the engine's own `lineup_optimizer` over projected POINTS (a rate, not the
asset LEVEL `roster_strength`'s docstring warns against), one shared ruler, 100% coverage checked:

    before   mean 2429.1   median 2418.0
    after    mean 2417.8   median 2422.7      -11.4 points, -0.5%, 6 of 12 chairs improved

**35 tav a pick surrendered for half a percent of realised starting points.** That is itself
evidence for the predictiveness thesis: if `tav` differences of that size were real, giving up
~6,700 of them across a draft would have cost far more than eleven points of lineup.

### What is NOT fixed, and why

- **Turn-ending picks — 15 of 192 (8%) — keep the old behaviour, and must.** At 7.12 there are no
  intervening picks, so `positional_forfeits` correctly returns nothing and the row falls to the
  unmeasured block. "What does waiting cost" has no answer when you are not waiting. Whether such
  a pick should weigh deferral to the round AFTER next is a different quantity; **owner's call**.
- **Upside mode is untouched.** `draft_strategy` builds no curves there, so every forfeit is
  legitimately absent and so is this. The open question of whether upside curves should feed
  forfeits at all stays where that module already records it.
- **Predictiveness is still unmeasured.** K and DST now draft where they should; nothing here
  makes their projections more predictive. `measure_projection_accuracy.py` needs a networked run.

### Corrections to published claims

- **"The first defense goes in round 8" was wrong — it is round 5.** The earlier figure came from
  a `compute_draft_board` + `board[0]` probe; the battery's own path
  (`build_snapshot` + `candidates[0]`) puts it three rounds earlier. The defect was worse than
  reported.
- **A reported mutation "survivor" was a no-op.** The mutation string carried the wrong
  indentation, so `.replace()` changed nothing and the arm ran against unmutated code.
- **A reported "regression after restore" was stale bytecode.** A same-length substitution
  (`1`->`0`) left a `.pyc` outliving its source; `co_consts` still held the mutant while the file
  matched HEAD. Every arm now purges `__pycache__` and verifies the mutant is loaded.
- **"The six-point band shows replacement is well-determined" was wrong**, for both reasons above.

### Suite measurement, with its commit

**3333 tests in 1038.7s**, `__pycache__` cleared first per `#240`, at the commit this entry lands
on. The previous recorded figure was 3091 tests in 860.9s at `#283` (2026-09-17): the suite grew
by 242 tests and got 21% slower, with per-test cost roughly flat (0.279s -> 0.312s). Growth, not
regression.

---

## `6.1b` CLOSED — THE TERM WAS INERT, ITS CAP WAS NOT

`eligibility_bonus` is retired from the board. The ruling was made on a measured population:
across 36 board states and 46,020 rows the term was nonzero on **five**, at a maximum of 0.84
against a bound of 12.00, while `displacement_adj` on the same lifted rows averaged 118.31 —
so it was pricing **0.24%** of the multi-eligibility credit it claimed to own. Every
OFFENCE-ONLY multi-eligible player in the capture is retired, so the WR/TE case the term was
built for had no living members.

### What it cost, which is not nothing

| | before | after |
|---|---:|---:|
| `NECESSITY_DENIAL_SATURATION` | 36.0 | **24.0** |
| `CONTEXT_ELEVATED_THRESHOLD` | 12.0 | 12.0 |

`eligibility_bonus`'s cap was a member of `TEAM_SPECIFIC_CAPS`, so the SUM lost a 12.0 member
while the MEAN of equal caps did not move. **This is a derivation, not a calibration, and `#56`
is not engaged**: nobody chose a new saturation point, the formula is untouched, and its input
lost a member because a term retired. A constant that held at 36.0 across that change would be
the hand-maintained number `#56` actually prohibits.

Measured over 7,595 rows carrying a `rival_premium`, the **clamp is a red herring** — the
maximum premium observed is 10.32 against a mean of 1.77, so no row saturates at either point.
Saturation is a *divisor*, so what moved is the ramp: every row's denial component scales by
exactly **1.5×** (mean 0.984 → 1.475, max 5.733 → 8.600), worst single-row shift **+2.87** on a
100-point necessity score.

### What it rules OUT

- **The blast radius was half what the grep said.** `lineup_optimizer.eligibility_bonus` is a
  FUNCTION and it survives untouched with its own suite. 6.1b retired a board term, not a
  calculation, and any future reader grepping the name will over-count the same way.
- **`CONTEXT_ELEVATED_THRESHOLD` needs no ruling.** It is a mean over equal caps and is
  invariant to a member leaving.

### THE FINDING, which is about the guards and not about the term

260 suite errors followed the retirement. Roughly 250 were mechanical. The other ten were
**eight separate guards that failed for the wrong reason**, every one the same shape: each
hand-listed a population instead of deriving it.

| guard | what it hand-listed |
|---|---|
| `test_probability_bounds` | `3 == len(TEAM_SPECIFIC_CAPS)`, then each cap by name |
| `test_term_lifetimes` | three term names |
| `test_depth_exposure` | the layer-identity sum |
| `test_216_displacement` | the layer-identity sum |
| `test_downstream_contracts` | the layer-identity sum |
| `test_pick_synthesis` | the layer-identity sum, twice |
| `test_216_room_integrity` | the identity-term set as a literal |
| `test_threshold_reachability` | the three caps the saturation sums |

None had stopped being true. Each fired because its private copy of a list went stale. **A test
that counts a population cannot tell a legitimate removal from a defect** — it fires on both and
means neither. All eight now derive from `draft_room.TEAM_SPECIFIC_TERMS` or from
`TEAM_SPECIFIC_CAPS`.

The last one is the sharpest. `test_the_saturation_point_is_derived_from_every_term_it_sums`
exists *because* `#139` added a third term and the constant did not follow; its docstring calls
that "the whole mechanism of the original defect". And it hand-listed three caps, so it only
ever watched the ADDITION direction. A term leaving failed it while the saturation it guards had
tracked the removal correctly. **The guard was wrong and the engine was right.**

That is the generalisable lesson of this pass: **this repository's guards notice additions and
are blind to removals**, because a hand-written list grows by hand and shrinks in silence. The
invariant registry is the one piece of machinery built for the shrinking direction, and it was
the only thing that caught the absence-contract population going 30 → 29.

### Deletions, recorded because `assertion_floors` must not absorb them silently

`EligibilityBonusWiringTests` (**6 tests**, 267 lines) and
`test_eligibility_flexibility_alone_changes_the_score`. Their subject no longer exists, so there
is no weaker version to keep — the same reasoning by which the eligibility INVARIANT is KEPT:
that invariant is the standing record of the population the removal was ruled against, and a
vendor refresh restoring active offence dual-eligibility moves its census and reopens the
ruling. Retiring the watch with the term would delete the only thing that can say the ruling has
expired.

One of the six was **not** a term test. `test_full_board_stays_fast_even_when_most_candidates_
are_multi_eligible` was a PERFORMANCE guard, existing because pricing the term called
`lineup_optimizer` once per multi-eligible candidate. Retiring the term removes those calls, so
the cost it watched cannot be incurred — which implies 6.1b makes boards slightly FASTER in
IDP-heavy formats. **That is unmeasured and now untested in either direction**, stated here
rather than left as an assumption.

### Corrections

- "Both constants are unmoved, the gate resolves" — **WRONG**, stated mid-session. It read the
  post-stash working tree as though it were the baseline instead of diffing HEAD. The same error
  class as the stale-`.pyc` earlier the same day: comparing against the wrong "before".
- "8 tests deleted" — **it is 6.** The AST count included `setUpClass` and a helper.

### Registry censuses moved by hand, not by `--write`

`team-specific terms` 4 → 3, and `an absent quantity reaches a caller as None, never as NaN`
30 → 29 (`eligibility_bonus` was an emitted column). Nothing is weakened by the second — a
column that no longer exists cannot carry a NaN — but unsigned shrinkage is precisely what that
registry exists to catch, so both moved with their reasoning attached.

---

## `#52` PHASE 8 — THE SUPERFLEX QB REGRESSION WAS A WIRING DEFECT, AND THE SECOND OF ITS KIND

The `acting_now` ordering repair cost **2.4% of lineup points in superflex** against 0.5% in
standard formats, and left rosters holding **one quarterback in a format that starts two**. The
cause was not the ordering. It was `expected_taken`, and the correction for it already existed.

### The measurement that found it

Superflex, 18 intervening picks ahead, league-wide QB starter demand **18.5**, and **ten
quarterbacks already gone in the first twenty picks**:

| pos | `expected_taken` | `forfeit` | `acting_now` |
|---|---:|---:|---:|
| **QB** | **0.84** | **0.43** | **0.43** |
| RB | 2.75 | 23.42 | 23.35 |
| WR | 3.20 | 19.36 | 19.39 |

The fastest-moving position on the board, predicted to lose fewer than one player in eighteen
picks.

### The correction was already written, for exactly this case

`_pace_based_take_probability`'s own docstring:

> *"built for exactly the case a rank-based estimate structurally cannot handle. Confirmed
> directly: an elite QB can rank outside `RANK_TAKE_PROBABILITY`'s top-5 keys on EVERY
> intervening team's own board … at which point the rank-based estimate floors out at
> `RANK_TAKE_PROBABILITY_FLOOR` (0.02) regardless of position."*

It had **one** consumer: `estimate_survival`. `positional_forfeits` — which asks the
position-level question that function answers in its first step — never saw it.

**This is the second divergence between the same two functions.** `positional_forfeits`' own
docstring records the first, verbatim: `#206` normalised the take model, applied it to
`estimate_survival`, and *"THIS CONSUMER WAS NOT CONVERTED."* Two occurrences with one shape is
a structural pull, not bad luck: the functions answer adjacent questions off one model, and the
position-level half had no name of its own to reach for.

### The repair

Step 1 lifted out as `position_pace_probability`, read by both consumers (`#126`). The
convention only ever RAISES the rank estimate, resolved exactly as `estimate_survival` resolves
the same disagreement. **No new constant, so `#56` is not engaged** — `SUPERFLEX_QB_PACE_ANCHORS`
and `PACE_CATCH_UP_WINDOW` already shipped and were already trusted by survival; what changed is
which consumers can see them.

| `10T_ppr_SF` | QB mean | QB min | starters | worst chair |
|---|---:|---:|---:|---:|
| control (tav order) | 3.20 | 2 | 2583.6 | 2544.1 |
| before the fix | 2.40 | **1** | 2522.3 | 2404.2 |
| **after** | **3.20** | **2** | **2555.0** | 2469.7 |

Roster shape recovers **exactly** to the control. The points gap halves, −2.4% → −1.1%, which is
the same kind of cost the ordering repair pays in standard formats rather than a different
failure.

**It fires selectively, which is the evidence it is reading something true.** At round 3 it moves
QB from 0.43 to 10.64. At rounds 5 and 7 it does nothing, because seventeen and twenty QBs are
gone against a documented pace of ~12.8 — the market is AHEAD of convention and there is no
catch-up deficit to price.

### What it does NOT fix

The row-count bias behind it is real and untouched for every position with **no documented pace
convention**, which today is all of them except superflex QB (see
`evidence/blind_pass/TAKE_MASS_BIAS.md`). What changed is that it no longer has a known live
victim. A fourth option is now visible that was not before: document pace anchors for a second
position, rather than reshape the distribution at all — which needs real market data instead of
a chosen curve.

### A mutant survived the first pass, and the reason generalises

*"The convention REPLACES the rank estimate"* instead of raising it passed every test, because
the ahead-of-pace assertion ran against an **empty** opponent board: the rank model scored 0.0,
the convention scored 0.0, and `max()` versus replacement are indistinguishable when the loser is
zero. **The test was vacuous on precisely the arm it was written for.** Rewritten over a board
the rank model actually scores, and it now asserts the loser is non-zero first so the fixture
cannot drift back to proving nothing.

The wiring guard is the file's real deliverable: it parses the AST and asserts BOTH consumers
reach the shared step, so a third divergence fails loudly rather than surfacing months later as
a roster that quietly stopped drafting quarterbacks.

---

## #23 WITHDRAWN — THE SUPERFLEX QB "ANOMALY" WAS MY INSTRUMENT, NOT THE ENGINE

`#23` was raised on the strength of one cell in one table and is closed as NOT A DEFECT. There
is no engine question here for the owner. The defect was in `evidence/smoke_seats/probes/
horizon_collapse.py`, which I wrote, and in section 5a of `V2_MECHANISM.md`, which I published.

### What I published, and it is wrong

> `F(k_exhaust) = +82.28` and `U(k_exhaust) = +77.43` for superflex QB -- nowhere near zero,
> where every other cell is. The superflex QB replacement level does not sit at the
> starters-exhausted index.

The headline "eleven of twelve cells land within `[-6.61, +4.31]` of zero" was also wrong, and
wrong in the direction that understates the result.

### What is true

`replacement_levels` has TWO arms. For a position carrying a `startable_floor` -- today only QB
in a superflex league -- the replacement rank is the count of REMAINING players projecting at or
above an absolute points threshold, NOT the `teams x slots` demand headcount. The board reports
which arm priced each row, per row, in `replacement_basis`.

```
12T_ppr      replacement_basis=live_starter_demand   bpa crosses 0 at rank 11  (demand 12.0)
12T_ppr_SF   replacement_basis=startable_floor       bpa crosses 0 at rank 28  (demand 22.2)
             QB startable floor = 163.50 points; 29 QBs clear it
```

`horizon_collapse.py` computed `teams x slots(P)` for every position and never read
`replacement_basis`. On superflex QB that reads the curve six players early, where bpa is
legitimately `+79.00` on a scale anchored at rank 28. The `+82.28` is my probe's error reported
as the engine's.

Re-measured against each position's OWN basis, 4 formats x 4 positions:

```
worst |bpa| at any position's own replacement rank: 0.00   (16 of 16 cells, exactly zero)
```

### What this rules OUT, so nobody re-runs it

- **NOT a disagreement between `SUPER_FLEX_QB_SHARE` and the starter-demand path.** That was
  the second disjunct of my own guess and it is false. Both paths are consistent; they are
  simply not both used for this position.
- **NOT a truncation, a clamp, or a `#214/F3` pool-exhaustion case.** `truncated_out` does not
  fire here; the floor branch is chosen on purpose and the pool is deep enough.
- **NOT a `#56` violation.** The flat per-team "bench QB demand" constant WAS the `#56`
  violation, was tried, and was reverted -- real QB projections have a cliff at rank ~27-30 and
  a fixed constant either landed short of it or overshot past it (measured: 0.3 vs 0.4 extra
  demand moved one quarterback from 7th to 4th overall). The floor keys off the projection
  curve's own discontinuity instead. I flagged the correct repair as the suspected defect.

### What it does NOT change

Section 4 stands unaltered. Superflex reaching the board as a LEVEL shift of +127.14 per
quarterback against +0.08 of slope is measured on the shipped board with whichever arm priced
it, and the reverted `acting_now` ordering could not see a level shift either way. `#20`'s
diagnosis is unaffected.

Section 5's conclusion stands and is STRONGER: the collapse of long-horizon regret onto the
value key is universal (16/16) rather than 11 of 12. `bpa` is anchored at the replacement rank
whichever arm chose it, so `F(i) - F(replacement_rank)` is the value key by definition. There is
no longer-horizon formulation left to look for.

### The guard that would have caught it

`test_replacement_basis_vocabulary.OnTheRealBoardTests.
test_bpa_is_zero_at_the_replacement_rank_WHICHEVER_BRANCH_SET_IT`, with a non-vacuity companion
pinning that the two arms really do pick different ranks (28 against 22.2) -- without that, the
invariant could hold for a reason unrelated to `replacement_basis`.

Mutation-checked **1/10**:

| mutant | fires |
|---|---|
| `floor = None` (disable the startable-floor arm) | 1 -- the non-vacuity guard only. The anchoring invariant correctly still holds, because bpa is 0 wherever the level lands regardless of which arm put it there. |
| `levels[position] = ... - 12.0` (unanchor the scale) | 10, including the invariant on 7 of 8 position-league cells. |

That the first mutant fires ONE test and not the other is the point: the two guards are
measuring different things and neither is a restatement of the other.

### The lesson, since this is the third instrument error in this lineage

An instrument that RECOMPUTES a quantity the engine already publishes will eventually disagree
with it, and the disagreement reads as an engine defect. `replacement_basis` was on every row
the entire time. The probe asked the pool a question instead of asking the board its answer.
The `engine-measurement` rule this earns: **before recomputing an engine quantity in a probe,
grep the board row for a field that already states it.**

---

## W1-07 BLOCKED ON A SECOND RULING — `intervening_picks` CARRIES NO USABLE BOUND

`CDME_CONTRACTS.md` rules `NECESSITY_SURVIVAL_WEIGHT` should be replaced with
`intervening_picks`, and states the blocker exactly: the substitute is a COUNT, so it needs a
0-20 mapping, and the mapping must be DERIVED from the quantity's own bounds rather than chosen
to reproduce today's labels (`#56`).

This went looking for those bounds and **they do not exist in a usable form.** Characterized,
not built. Evidence and probes: `evidence/w1_07/`.

`(1 - survival)` is bounded `[0,1]` BECAUSE IT IS A PROBABILITY. That is the entire source of
the incumbent's scale, and a count has no equivalent property.

### The three normalisations, measured

| candidate | bounded? | defect |
|---|---|---|
| A: `/ (2 x (teams-1))` | **NO** | a snake-shape assumption. On a traded order the gap hits **46** against a "bound" of 22, so the ratio exceeds 1 and the 20-point term pays 41. |
| B: `/ this seat's longest wait` | yes, any order | informativeness is a function of SEAT. Turn seats swing the full 20 points (B alternates 1.000/0.000); middle seats sit at ~0.92 with sd 0.083 and total range 0.167 -- a 20-point term that moves **3.3**. |
| C: `/ picks remaining` | yes, any order | the same 11-pick wait scores **0.059 in round 1 and 0.571 in round 15**, so the term is muted (~1.2 of 100) through the rounds that decide the draft, and it rises late against `LATE_ROUND_NECESSITY_CAP`. |
| D: remove, substitute nothing | n/a | already measured in `CDME_CONTRACTS`: 12 of 384 labels flip (3.1%), max move 8.50, 2x `MUST TAKE -> STRONG ACTION`. |

```
12T x16 snake        n= 180  min=  0  max= 22   2*(T-1)= 22
12T x16 traded(135)  n= 180  min=  0  max= 46   2*(T-1)= 22
```

The traded case is not hypothetical: the `#52` pass that verified `intervening_picks` against
the engine at 5,567 candidates did so on a real draft with **135 traded seats**.

B's degeneracy is the same shape this repository already flagged on the necessity tag, which
spends five bands to put 95.4% of its mass in two -- B would reproduce that inside the score
rather than beside it.

### What this rules OUT

- Not a missing formula; all three normalisations were tried and the problem is the quantity.
- Not fixable with a different snake constant -- A fails on the very draft shape that validated
  the substitute.
- Not resolvable by measuring more drafts. A, B and C are structural properties of the pick
  order; more seats reproduce them rather than discriminating.
- Not blocked on `#21`. The take model's calibration is a separate defect; `W1-07` removes the
  term that reads it, and fixing the model would not supply a bound.

### Not fixed, and why

This is `#184`: the ruling as written is executable only after a SECOND ruling on which
denominator, and that is an engine-design choice with no derived answer. My recommendation, as a
recommendation: **D, then C if the term is missed** -- D is measured, is honest about the
absence, and matches the posture the rest of the engine takes under `#187`.

**What must not happen** is choosing among A/B/C/D by which best reproduces today's labels. The
12-of-384 figure is the *before* measurement, not the target.

---

## 6.1d·1 PARTLY EXECUTED — THE CEILING IS `max`, NOT `sum`, AND THE BADGE MEANS "MULTI-ELIGIBLE"

The ruling is *derive a threshold from the sum's own ceiling*. The derivation is done and
**shipped behaviour-free**; the product half is raised, not closed. Evidence and probes:
`evidence/context_elevated/`.

### The structural fact the derivation rests on

`context_elevated` fires on `tav − uv` = `need_bonus + depth_exposure + displacement_adj`.
`need_bonus` is large when a slot is EMPTY; `depth_exposure` requires SURPLUS. Opposite roster
states. Measured across **4 formats x 8 in-draft board states, 10,887 priced rows**, of which
**9,793** carry a nonzero value on at least one:

```
rows where need_bonus AND depth_exposure are both nonzero:   0 of 10,887
```

So the two capped terms contribute at most ONE cap between them. With
`displacement_adj <= 0` for a single-position probe (`lineup_optimizer`, THE SIGN, 0 of 120),
the gap's ceiling over that population is exactly `max(TEAM_SPECIFIC_CAPS)`.

### What shipped

`CONTEXT_ELEVATED_THRESHOLD = max(TEAM_SPECIFIC_CAPS)`, replacing
`sum(...) / len(...)`. **Still 12.0, so no behaviour changed.** The old comment claimed the mean
form made the relationship "stop being a coincidence"; it did not — mean equals max here ONLY
because the two surviving caps are equal, and a change to either would have moved the threshold
somewhere the quantity cannot reach with nothing to catch it.

Mutation-checked **1/2**:

| mutant | fires |
|---|---|
| floor `need_bonus` above zero so the two terms co-occur | 1 — the mutual-exclusion guard |
| set the caps unequal (12.0, 8.0) AND revert the formula to the mean | 2 — the form guard, plus the guard that exists to announce the coincidence has ended |

The second mutant is the point: with equal caps the form assertion is vacuous, so a third test
pins that the caps ARE equal and fails loudly the day they stop being.

### The finding: the badge is dead, and a better derivation makes that clearer

```
ALL 10,887 priced rows:  gap min -122.00, max 8.72, MEAN -3.46
share >= CONTEXT_ELEVATED_THRESHOLD (12.0): 0.00%
```

The gap's mean is NEGATIVE, because `displacement_adj` only subtracts over this population — a
flag meaning "ranked highly substantially because of fit" is reading a quantity that is usually
a penalty.

Across **all 36 battery formats** it fires on exactly ONE row in the whole corpus:

```
CAPTURE_owner_league  n=820  max gap 87.82  fired 1 (0.12%)
    Travis Hunter  gap 87.82  pos WR  fantasy_positions ['DB','WR']  disp +79.44
```

Every other format, IDP rulebooks included, fires 0.00% with the gap topping out at 8.33–9.00.
**In practice `context_elevated` means "multi-eligible with a cheap second slot", not "fit".**

### What this rules OUT

- Not fixable by lowering the threshold to the observed max — that is `#56`, fitting a number
  to make a badge fire.
- Not fixed by `6.1b`. That moved `NECESSITY_DENIAL_SATURATION` 36.0 -> 24.0, but the gap's
  ceiling was never the sum, so the deadness is untouched.
- Not an IDP-supply artifact. Both IDP rulebooks fire 0.00%; the one firing row is a
  multi-eligible probe in the owner's own capture.
- Not caused by the `6.1d` roster-wide repair. That pulled max gap 13.21 -> 8.33; even at 13.21
  the badge fired 7.72%, which the owning test class already warned was a bound read as a
  threshold.

### NOT fixed, and why — `#184`

A flag that fires on one row of one league across 36 formats needs a different quantity or
retirement. That is a product/valuation call and it is the owner's. The two `expectedFailure`s
in `test_threshold_reachability.py` stay as the executable statement of what must become true
once a ruling lands. `DRAFT_ROOM_UI` U24 is the same shape one flag over.

---

## W4-01 MEASURED AND REJECTED — `years_exp == 0` IS NOT THE ROOKIE CLASS

`CDME_CONTRACTS.md` rules the rookie population should **promote `years_exp`**. The ruling
rests on `ROOKIE_YEARS_EXP`'s own comment — *"a player with zero completed NFL seasons, this
year's rookie class"* — and that premise is false. Evidence and probes: `evidence/w4_01/`.

`years_exp == 0` means the feed carries no accrued-seasons value. Sleeper's historical rows for
long-retired players carry exactly that.

### Measured

```
                             n     age median   age max   >=25    on an NFL team
years_exp == 0             661         23         62      22.4%       41.6%
KTC rookie == True          72         23         31      17.4%       79.2%
```

The rookie BOARD, 12T_ppr offence-only, after `_admits_to_pool` and eligibility:

```
KTC flag       :  59 rows
years_exp == 0 : 333 rows      enter 281, leave 7

ENTRANTS n=281  on an NFL team 26%,  carrying a projection  6%,  max age 47
LEAVERS  n=7    on an NFL team 100%, carrying a projection 71%
```

It trades 7 rostered, priced players for 281 mostly unrostered, unpriced ones — including
**Kurt Warner (47), Byron Leftwich (40), Sean Ryan (40), Cedric Benson (37)**, all `team=None`,
all `status=Inactive`. The ruling as written puts a quarterback who retired in 2010 into a
rookie draft.

(`CDME_CONTRACTS` records 654/31 and 95 -> 718 on a different rulebook. The figures above are
12T_ppr offence-only; the entrants are the same people either way.)

### The same premise is already live — and it is a RULING, not a hole

`_admits_to_pool` admits on `years_exp == 0` unconditionally, so 241 board rows are admitted
ONLY by that clause (no projection, no team), 96 of them `Inactive`, 15 aged 27+, max 47.
Kurt Warner is on the NORMAL board of a 12-team PPR dynasty league today.

**I implemented the obvious fix and reverted it.** Making the rookie clause yield to
`NOT_CURRENTLY_PLAYING` removes exactly those 96 rows (board 1065 -> 969; the remaining 145
clause-only rows all `Active`, max age 34) and preserves the clause's stated purpose, since
Practice Squad is deliberately outside `NOT_CURRENTLY_PLAYING`.

It also reverses a tested owner ruling. `test_pool_admission_boundary.
StatusIsAFreshnessRuleNotAGateTests` is titled *"The owner's re-entry case: a retired player
un-retires and must be able to come back"*, and `test_a_rookie_beats_a_stale_not_playing_status`
pins the exact behaviour the fix removes. The status check used to run before any evidence was
read -- the `#180` defect, vetoing 304 players carrying a positive signal -- and `#193` moved it
on purpose. Reverted under `#184`; no engine code changed by this entry.

### The tension worth ruling on

| row | clause | admitted? |
|---|---|---|
| retired RB, `years_exp 11`, `trade_value 9.0`, no team | stale VENDOR number | **rejected** |
| Kurt Warner, `years_exp 0`, no number, no team | stale YEARS_EXP | **admitted** |

The first is rejected because *"without it losing here, a genuinely retired player would sit in
the pool forever on the strength of a trade value nobody has revisited."* The second lets a
genuinely retired player sit in the pool forever on the strength of an accrued-seasons field
nobody has revisited. And the re-entry case does not need the rookie clause: a player who
un-retires gets signed, which sets `team`, which the clause below admits on its own.

### What this rules OUT

- Not a name-collision problem. `#52` phase 1.2 already fixed `_rookie_lookup`'s key (58 of 788
  wrong before). KTC is the ACCURATE definition here; it is merely narrow.
- Not fixable by promoting `years_exp` with an age filter -- an age cut is a chosen number
  (`#56`), and 259 of 661 carry no age to filter on.
- Not an artifact of unpriced rows sorting last. They are unpriced and do sort last, so they
  distort no valuation -- but a rookie draft FILTERS on this flag rather than ranking by it,
  which is why the rookie-draft consequence is the severe one.

### Recommendation

**Do not promote `years_exp` as the rookie-draft filter.** If the two-definitions finding still
deserves a repair, the live question is the narrower one above -- whether the freshness rule
should treat a stale `years_exp` as it already treats a stale vendor number. One condition,
measured (1065 -> 969), and the owner's because it reverses `#193`.

---

## I-06/J-06 BLOCKED ON A BOUNDARY — STEP 1 RECREATES AN UNREACHABLE PREDICATE

`CDME_CONTRACTS.md` rules **separate basis token with its own scale**, executed as
*"introduce the basis token carrying the measured uncovered quantity, price nothing."* I went
to write that token. The obvious form of it recreates a failure mode this repository has
already ruled against. Characterized, not built. Evidence: `evidence/i06_j06/`.

### The defect is real, and larger than it reads

Measured over 8 in-draft board states, 12T PPR dynasty, real capture, production's own
`_team_roster_players`:

```
cells by basis                    worst_loss by basis
   not_applicable  40 (55.6%)        no_surplus  n=8  min 10.00  median 62.00  max 82.00
   vacant          18 (25.0%)        measured    n=6  min 27.00  median 42.00  max 61.00
   no_surplus       8 (11.1%)
   measured         6 ( 8.3%)

no_surplus cells carrying a NON-ZERO worst_loss: 8 of 8
```

**The UNPRICED state carries the LARGER measured loss** -- median 62.00 against `measured`'s
42.00 -- and is priced at exactly what a perfectly covered position with no marginal loss is
priced at, `0.0`. `#187`'s shape, as the contract already says: "zero is a NUMBER, not an
absence."

### Why step 1 cannot ship as written

`basis` is returned from ONE site: `MEASURED if all(covered) else NO_SURPLUS`. Adding
`EXPOSURE_UNCOVERED` for `not all(covered)` therefore takes the ENTIRE current population of
`NO_SURPLUS`, leaving it unreachable. `basis_semantics.py` rules that out by name:

> REACHABILITY IS PART OF THE DECLARATION... A vocabulary does not get a state it cannot emit;
> that is the unreachable-predicate shape the 18th withdrawal was.

and `test_depth_exposure.TheFourStatesOfKnowingTests.
test_a_roster_with_no_bench_reports_no_surplus` pins a live population for it.

### Both available boundaries are ones this repo already rejected

(a) **An eligibility rule.** `depth_exposure`'s own docstring measured and threw it out: "a
bench RB can play FLEX, and a tight end can also reach FLEX, so the rule called TE covered. It
is not."

(b) **The roster-wide has-any-bench boolean.** That is precisely the sentinel `#52` phase 6 --
this item's own repair -- deleted: "one roster-wide boolean stamped onto every position alike...
one irrelevant bench body switched pricing on for every position at once."

The two obvious boundaries are the two this item's repair already removed.

### What this rules OUT

- Not a renaming exercise. `#188` already rejected collapsing these tokens: a rename is a
  data-format change, since they are keys in the label maps shipped across the Python/JS
  boundary (`#186`) and participate in snapshot identity (`#92`). Any new token must also be
  declared in `basis_semantics.REACHABILITY` with how reachability was established.
- Not solvable by pricing it -- that is step 2 by the contract's own sequencing and needs a
  scale nobody has argued for (`#56`).
- Not a fixture artifact: 8 of 8 cells across 8 board states. (A first attempt at the probe
  hand-rolled the roster builder and produced n=0; caught by the engine-measurement rule about
  printing n, and it now calls `dr._team_roster_players`.)

### What the owner has to rule

1. **Accept one token, fix the LABEL.** It is plainly false today -- "not measured -- you hold
   no backup here, so there is no surplus to value" sits on a cell carrying a measured 82.00.
   Cheapest and honest; does not deliver the "separate token" the ruling names.
2. **Ask the solve a second question** -- derived, and with its own evidence that it is not (b)
   in disguise.
3. **Declare `no_surplus` `dormant_by_design`** and add the new token, registering it in
   `basis_semantics.REACHABILITY` as `pool_truncated` already is. The only path that adds a
   token without an unreachable predicate -- but `pool_truncated` is dormant because today's
   DATA never reaches it, while `no_surplus` would be dormant BY CONSTRUCTION, a weaker claim.

Recommendation: (1) now; (3) only if the second token is wanted badly enough to accept a
by-construction-dormant member.

---

## J-12 AND J-13 WERE DONE AND UNRECORDED — AND MY OWN W1-07 ENTRY ASKED THE WRONG QUESTION

Two corrections and one guard repair. No engine behaviour changed.

### J-12 and J-13 are IMPLEMENTED, and were in no table

Both landed with their ruling tag in the source and their own guard test, and both were still
sitting in `CDME_CONTRACTS.md`'s ruling table as pending work:

| ruling | where it landed | guard |
|---|---|---|
| `J-12` | `app.py` calls `draft_history.record_snapshot(...)` only when a debate actually ran on the board, wrapped so a failed write cannot take down a live draft | `test_draft_history_is_wired.py` |
| `J-13` | `sleeper_client.get_players()` RAISES `SleeperAPIError` instead of returning `{}`; the same phase made the cache write atomic via `store_io.replace_atomically`, since `write_text` truncates before writing -- the mechanism behind the 91,956 empty reads of 98,405 | `test_no_empty_player_universe.py` |

So a reader going to the authority saw seven open rulings when two were finished.

### THE GUARD THAT SHOULD HAVE CAUGHT THAT ASSERTED LESS THAN ITS DOCSTRING CLAIMED

`test_rulings_are_not_silently_dropped.py` opens with *"Every owner ruling is either IMPLEMENTED
or STAGED WITH ITS REASON. Nothing is just forgotten."* Its census only asserted that each of
the seven is **named in `CDME_CONTRACTS.md`** -- which every ruling is by construction, since
that file is where they were written down. J-12 and J-13 were in NEITHER table and the census
passed throughout.

A guard that asserts less than its docstring claims is worse than no guard, because the claim is
what a reader trusts. Repaired:

- `AWAITING_RULING` added as a third table, for rulings CHARACTERIZED but blocked on a second
  owner decision -- neither implemented nor staged, because there is no patch to stage until the
  boundary is ruled. `6.1d.1`, `I-06/J-06` and `W4-01` now sit there with their witness and
  their evidence path.
- `test_every_ruling_sits_in_EXACTLY_ONE_table_here` -- the assertion the docstring always
  claimed. Mutation-checked both ways: removing J-12 from IMPLEMENTED fires it (the exact
  omission that went unnoticed), and placing J-13 in two tables fires it too.
- `test_no_table_carries_a_ruling_that_is_not_one_of_the_seven`, so a typo'd key cannot satisfy
  the census for the wrong ruling.
- `test_every_awaiting_ruling_is_still_actually_awaiting` and `..._points_at_evidence_that_exists`,
  mirroring the STAGED half so a resolved item cannot leave a stale record behind.

The seven are now named once in `SEVEN` and read by every census test (`#126`).

### CORRECTION: my W1-07 entry asked a question downstream of the real blocker

The `W1-07` entry above measured three denominators and concluded the quantity has no usable
bound. That analysis stands, but it **missed the prior objection already recorded in the tree**,
along with a staged patch at `evidence/blind_pass/w1_07_substitute.patch` (129 lines):

> implementing it flips **62% of labels** against a ruling made on 3.1%, because
> `intervening_picks` is a property of the **TURN** and the quantity it replaces was a property
> of the **PLAYER**.

Now measured rather than asserted. At five real turns, `intervening_picks` takes exactly ONE
distinct value across all 46-48 candidates in the snapshot, while `survival_probability` takes
6 to 13:

```
 turn seat  cands   distinct intervening_picks   distinct survival
    0    1     48                        [22]                   6
    5    6     48                        [12]                   7
   13   11     47                        [20]                   9
   25    2     47                        [20]                  11
   37   11     46                        [20]                  13
```

**The substitute cannot differentiate candidates under ANY denominator.** It shifts every
candidate's necessity by the same amount, so it never re-ranks; the 62% label flip is
band-crossing, not re-ranking. A denominator question is downstream of that.

Nothing in the denominator analysis is withdrawn as false -- it remains the answer if the term
is ever made per-candidate. What is withdrawn is my framing of the decision. The live question
is the register's: whether re-deriving five label thresholds is worth it for a term that cannot
re-rank anything.

The lesson, and it is the same one twice in two days: **before measuring a quantity, grep the
tree for what it already says about it.** `#23` was a probe recomputing a value the board
already published; this was an analysis re-deriving a blocker the register already recorded.

---

## OWNER RULINGS RECEIVED 2026-09-21 — ALL SIX OPEN ITEMS DECIDED

Recorded before implementation so the decisions are durable, and so each following commit can
cite the ruling it executes rather than restating it. **No code changed by this entry.**

| item | ruling | shape of the work |
|---|---|---|
| `#24` `W1-07` | **Remove the term, substitute nothing.** | Drop necessity's survival component. Measured before: 12 of 384 labels flip (3.1%), max move 8.50, 2x `MUST TAKE -> STRONG ACTION`. The freed 20 of 100 has to be accounted for -- redistribute or shrink the scale -- and that is its own derivation. |
| `#25` `context_elevated` | **Retire the badge.** | Remove from the flags, the payload and the label registries, as `6.1b` retired `eligibility_bonus`. Its quantity's mean is **-3.46**: "ranked highly because of fit" reads what is usually a penalty. `CONTEXT_ELEVATED_THRESHOLD` and its `max()` derivation go with it. |
| `#26` `W4-01` | **Yes -- a stale `years_exp` gets the stale-vendor treatment.** | One condition: the rookie clause yields to `NOT_CURRENTLY_PLAYING`. Measured: board 1065 -> 969, the 96 removed all `Inactive`, the 145 clause-only rows that remain all `Active`, max age 34. Practice Squad is outside that tuple so taxi-relevant rookies are untouched. **Reverses `#193`'s tested re-entry case for this clause**, so `test_a_rookie_beats_a_stale_not_playing_status` is rewritten with the ruling as its reason. |
| `#27` `I-06/J-06` | **One token; fix the false label.** | Keep a single unpriced state. Correct the label, which is false today: *"not measured -- you hold no backup here, so there is no surplus to value"* sits on cells carrying a measured 82.00, median 62.00 against the priced state's 42.00. No new vocabulary member, so no unreachable predicate. |
| `#21` take model | **BLOCKED ON `#50`, and this row's own numbers were stale -- see `evidence/take_model/FLOOR_DERIVATION.md`.** | Re-measured on HEAD: 489 unpriced rows (not 638 -- `#26` narrowed admission at `264e063`), mass 20.51 (not 23.49), share 0.477 (not 0.543). This row read as an instruction to rescale `0.02` by `1/0.55`; measured, that takes the block's share of a pick from 0.650 to **0.772** -- worse. The drift is the TAIL collapsing under exponential decay, not the leader. And the real blocker is that the board makes two incompatible claims about those 489 rows: ORDER LAST says unpriced is WORST (floor ~2e-06, 'unpriced means safe', ruled against), while `ABSENCE_NO_INPUT` says unpriced is UNKNOWN (floor `P/n_p` = 0.010948). `draft_room.py:632-637` already names that as a `#50` valuation question. Deriving the floor now means picking one convention by arithmetic -- choosing, not deriving. |
| `#17` turn-ending | **Re-measure against the reverted engine first.** | Its evidence cites `_acting_now_order`, deleted at `#22`, and was measured under the v2 ordering. Post-revert every pick uses the tav order, so the *differential* it describes may not exist. Re-run `turn_ending_leak.py` on current HEAD; if the 3x K/DEF clustering survives, the pair-aware mechanism is still live and gets ruled on fresh numbers. |

### Implementation order, by dependency and blast radius

1. `#17` re-measure -- no code change, and it either closes the item or produces the numbers a
   later ruling needs.
2. `#27` label -- one string and its test.
3. `#26` admission -- one condition, already measured; rewrites a `#193` contract test.
4. `#25` retire -- vocabulary removal across several registries.
5. `#24` remove the survival term -- changes necessity's 100-point scale, so it lands after the
   smaller ones and carries the redistribute-or-shrink derivation.
6. `#21` floor + value model -- largest, and the only one needing a fresh derivation.

Each lands as its own commit with its own mutation battery, per `CDME_CONTRACTS`' standing rule.

**`#18` remains blocked** on `api.sleeper.app` egress and is unaffected by any of the above. It
is still the only route to the round-5 defense, which none of these six rulings addresses.

---

## RULINGS EXECUTED: `#27` LABEL, `#26` ADMISSION, `#17` RE-MEASURED

Three of the six rulings of 2026-09-21. Combined into one commit rather than three: one full
suite licenses all of them, the modules are disjoint (`lineup_optimizer` / `draft_room` /
evidence only), and `#169` makes path-selective staging the riskier option -- `git add -A` with
`git status --short` read is the rule that exists because naming files broke three commits.

### `#27` I-06/J-06 — one token, and the label was the false part

`EXPOSURE_NO_SURPLUS`'s label read *"**not measured** -- you hold no backup here, so there is no
surplus to value."* The first half is untrue: every one of the 8 cells in this state carries a
non-zero `worst_loss`, median **62.00** against `EXPOSURE_MEASURED`'s **42.00**, max 82.00.
Telling a reader nothing was measured, on the cell carrying the biggest measurement, is `#187`'s
shape in prose.

Now: *"measured, but it is a starter's whole value rather than a backup's job -- some starter
here has no cover, so this is not a depth price and is not charged as one."* Token unchanged, no
new vocabulary member, four labels still. Pricing is untouched: `draft_room` still charges
`worst_loss` only under `EXPOSURE_MEASURED`, because the number is a starter's whole value on a
different scale.

Mutation-checked 1/1: restoring the old label fires two of the four new guards -- one for the
false "not measured", one for the half that keeps it from reading as priced.

### `#26` W4-01 — a stale `years_exp` gets the stale-vendor treatment

The rookie clause now yields to `NOT_CURRENTLY_PLAYING`. Measured, exactly as predicted:

```
board rows: 1065 -> 969         retired players still on the board: NONE
```

Behaviour, asserted in full: Inactive rookie with no team -> **rejected**; Practice Squad,
IR, PUP and status-None rookies -> admitted (the population the clause exists for, and Practice
Squad is deliberately outside that tuple); Active rookie with nothing else -> admitted; Inactive
rookie WITH a team or WITH a projection -> admitted by the clauses below, untouched.

This **reverses `#193`'s tested re-entry case for this one clause**, so
`test_a_rookie_beats_a_stale_not_playing_status` became
`test_a_rookie_does_NOT_beat_a_stale_not_playing_status`, carrying the ruling and the reasoning
rather than being edited away. Re-entry still works without the clause: a player who un-retires
gets signed, which sets `team`.

**A SECOND CONTRACT TEST HAD TO MOVE, AND THE FULL SUITE IS WHAT FOUND IT.**
`test_placeholder_admission.test_a_real_rookie_with_the_same_shape_is_still_admitted` used an
`Inactive` lookalike to prove `#273`'s rule is keyed on the NAME and not on the SHAPE. After this
ruling that row is rejected by the STATUS gate, so the test would have passed or failed for a
reason unrelated to the sentinel -- a placeholder guard quietly converted into a status guard.
The fixture is now `Active`, which isolates the original question, plus a non-vacuity companion
pinning that the sentinel still decides on a row the status gate would pass.

Mutation-checked 1/1: restoring the unconditional clause fires the ruling's test.

### `#17` turn-ending picks — re-measured, and the mechanism is withdrawn

Ruled: re-measure before ruling. Rulebook `12T_ppr_K_DEF`, 192 picks, self-play on HEAD:

```
pos     all  turn-ending  expected   ratio        first K   : pick 46 (4.10)
WR       65            0      5.08    0.00        first DEF : pick 33 (3.09)
RB       42            4      3.28    1.22
K        26            1      2.03    0.49        K/DEF by round 12: 37,
TE       23            3      1.80    1.67        of which turn-ending: 6 (16%)
DEF      21            6      1.64    3.66
QB       15            1      1.17    0.85
```

**The clustering survives for DEF (3.66x, up from 2.95x) and VANISHED for K (0.49x, from
2.74x).** Not an artifact -- but not the K-and-DEF finding the file described either.

**The proposed mechanism can no longer work.** It was "point `positional_forfeits` at the gap
after *N+1*", and post-`#22` that quantity has NO selection authority: the board ranks on
`team_acquisition_value` and the forfeit reaches only necessity's display term. Whatever drives
the 3.66x is not the forfeit. Mechanism withdrawn.

**And the framing is probably wrong regardless.** The first defense now lands at **round 3.09**,
two rounds earlier than the 7.12 recorded and earlier than `KDST_VALUATION`'s round 5, because
`#16` is what `#22` reverted. Arguing where *within a round* defenses cluster is arguing about the
distribution of an already-wrong behaviour. `#18` is the fix and will likely dissolve the question.

**A FIRST RUN OF THIS RE-MEASUREMENT WAS VACUOUS**, and is recorded rather than discarded: it used
`build_mock_league`, whose starters carry **no K and no DEF slot**, so it reported "K and DEF never
taken" -- measuring the format, not the engine, with `n=0` for the population the item is about.
Caught by the engine-measurement rule on printing `n`. Third instrument error in three days, all
three caught by that rule.

---

## `#25` EXECUTED — `context_elevated` RETIRED FROM THE BOARD

Ruled 2026-09-21: **retire the badge.** It fired on ONE row across all 36 battery formats -- a
multi-eligible WR/DB lifted +79.44 by `displacement_adj` -- while the quantity it read has a
**mean of -3.46** across 10,887 priced rows, so "ranked highly substantially because of fit" was
reading what is usually a PENALTY. Retired rather than repointed, the way `6.1b` retired
`eligibility_bonus`: the population was not there.

### What came out

| surface | change |
|---|---|
| `pick_synthesis.decision_path_flags` | the `context_elevated` key is GONE from the dict -- absent, not False, because a flag reading False forever is the dead-signal shape this programme keeps finding |
| `pick_synthesis.CandidateSnapshot` | field removed; **52 -> 51**, so `snapshot_identity` hashes change BY DESIGN (that function's docstring already rules removal the same class as addition) |
| `CONTEXT_ELEVATED_THRESHOLD` | removed with its flag. A bound left in place with nothing reading it is `#56`'s companion problem -- the next reader takes it for a live threshold |
| `draft_board_ui._context_gap` | the "elevated" direction is gone; the Context Gap is one-directional. It had PRESENTATION PRECEDENCE over `pure_value`, so a glyph firing on one row in one league was outranking one that fires on real populations |
| `draft_history._CANDIDATE_EVIDENCE_FIELDS` | column dropped, `EVIDENCE_SCHEMA_VERSION` **1 -> 2**. Records written under 1 keep their number and stay readable; the store is append-only and never regenerates |
| `invariant_registry` | `NECESSITY_DENIAL_SATURATION` is now the ONLY shipped constant deriving from `TEAM_SPECIFIC_CAPS` |

`pure_value` is untouched. It is a cross-candidate comparison answering a different question, and
it no longer has to win a coin toss against a dead flag.

### Three guards had to be told, and each records why

- **`test_snapshot_identity_boundary`'s recorded floor** on the stored evidence columns. Its own
  docstring says a removal must "edit this literal in the same commit as the removal, where a
  reviewer sees the name go and reads why" -- second use of that mechanism after
  `eligibility_bonus`, and it worked exactly as designed.
- **`test_display_contract_boundary`'s field-count pin**, 52 -> 51. The note there used to argue
  for finding the badge a slot on the card once the UI passes decided where. **The question is
  answered by removal: there is nothing to place.**
- **`test_probability_bounds`' wiring assertion**, which pinned that BOTH derived constants still
  read the tuple. Now one, plus an assertion that `CONTEXT_ELEVATED_THRESHOLD` has NOT come back.

Retired tests are replaced by guards asserting the retirement rather than deleted: `assertNotIn`
on the flags dict, `assertFalse(hasattr(...))` on the constant, and in `test_draft_board_ui` a
test that records the *precedence* that used to exist, since that is the part worth remembering.

### TWO GUARDS CAUGHT ME, AND ONE OF THEM WAS MY OWN, WRITTEN YESTERDAY

**`test_prose_names`** failed on `` `ContextElevatedBecameReachableTests` `` in my own retirement
comment: backticks in this repo assert a LIVE identifier, and I had backticked the class I had
just deleted. A retired name is prose, not a reference.

**The ruling register did NOT catch what it was built to catch.** `6.1d.1`'s `AWAITING_RULING`
witness was the bare string `@unittest.expectedFailure` in `test_threshold_reachability.py`. When
the ruling landed and that class was retired, a THIRD expectedFailure in the same file -- an
unrelated `rival_premium` test -- kept the witness satisfied, so the register went on claiming the
decision was open after it had been executed. **Caught by reading, not by the guard.** `6.1d.1` is
moved to `IMPLEMENTED` with a witness only its own landing can produce, and the lesson is written
at `AWAITING_RULING`'s definition: *a witness a neighbouring test can satisfy is not a witness.*

That is the second time in two days that a guard I wrote asserted less than I believed. The first
was the census only checking a ruling was NAMED in the contracts file.

---

## `#18` UNBLOCKED THE WRONG WALL — THE STATS ENDPOINT URL HAS ALWAYS BEEN 404

The owner added `api.sleeper.app` to the egress allowlist and ran
`measure_projection_accuracy` on a networked machine. It printed **"9421 projected, 0 actual"**
for all 36 weeks of 2023 and 2024, then refused to write anything. The network was never the
only wall.

### Measured, on the owner's machine

```
/stats/nfl/regular/2024/5               404   0 rows      <- what shipped
/stats/nfl/2024/5?season_type=regular   200   list, 2074  <- live
/stats/nfl/2024/5                       400   bad-request
```

**Both weekly endpoints take `season_type` in the QUERY STRING.** The projections side already
knew and said so in a comment. The stats side had it in the PATH.

### The belief was documented AND tested, which is why it lasted

`SleeperClient.get_weekly_stats` carried this:

> NOTE THE URL SHAPE. season_type goes in the PATH here, not the query string -- the opposite of
> get_weekly_projections ... **mirrored from that hard-won note rather than re-derived.**

That was inferred from an offhand parenthetical in the projections comment -- *"(as its stats
endpoint does)"* -- and written up as settled fact. Then
`test_outcome_record.test_season_type_goes_in_the_PATH_here` **pinned it**, with a docstring
saying it "pins the shape rather than leaving it to be re-guessed."

A guess with a test around it reads exactly like a verified fact. The test asserted the string
the client builds, and the client builds whatever it was told to -- nothing in it contacts
Sleeper, and every consumer of the endpoint needs a host the sandbox denies. **The path had never
once executed against the real API.**

### Blast radius: wider than `#18`

`get_weekly_stats` already existed with real consumers. All of them have been fetching nothing:

| consumer | what it could not do |
|---|---|
| `outcome_record.py` | fetch what actually happened -- the whole OUTCOME half of the forward test. `prediction_record` writes what the engine believed; nothing could write what the world did. |
| `get_season_stats` (via `_sum_weeks`) | any season-level actuals |
| `measure_projection_accuracy` | `#18`, which is how it was finally found |

`measure_projection_accuracy` additionally hand-rolled its OWN copy of the bad URL rather than
calling the client, so there were two wrong copies of the same guess.

### The repair

`SleeperClient._weekly_stat_lines(kind, ...)` is now the one home for the URL shape and the
response normalisation, shared by `get_weekly_projections` and `get_weekly_stats`.

**The error postures are deliberately NOT shared**, and a first version of this repair got that
wrong. Projections FAIL SOFT (a missing projection degrades a board gracefully); stats RAISE (an
empty result is indistinguishable from "nobody scored", and a validation record built on that
would report the engine as catastrophically wrong about a week that never downloaded). So the
helper does not catch, and each caller applies its own contract. Merging them would have looked
tidier and destroyed a documented difference -- caught by a test, not by review.

Both response shapes are handled because Sleeper serves both: projections as a dict keyed by
player_id, stats as a **LIST** of records. `measure_projection_accuracy` called `.items()` on the
raw payload, so the list form would have raised the moment the URL was right -- a second defect
hidden behind the first.

### Guards

`test_sleeper_client.TheTwoWeeklyEndpointsShareOneImplementationTests` -- the query-string shape
for both, the two URLs differing ONLY by endpoint name, list and dict normalisation, the two
error postures, and an AST guard that the instrument never hand-rolls a Sleeper URL again.
`test_outcome_record`'s pinning test is REVERSED rather than deleted, carrying its own
post-mortem.

### What this does NOT establish

No accuracy ratio yet. The measurement still has to be re-run. What is fixed is the instrument
that produces it -- and the forward test's outcome half, which nobody had noticed was dead.

The lesson, and it is a new one rather than a repeat: **a test that asserts what our own code
constructs is not evidence about a system we do not control.** Every guard in this repository
that checks a URL, a payload shape or a third-party contract has this shape, and none of them
can see a 404.

---

## #18 MEASURED, AND THE RULING IT WAS BLOCKING IS SUPERSEDED BY THE MEASUREMENT

`measure_projection_accuracy` ran to completion against the live API for the first time, on the
owner's machine, after the URL repair above. All 36 weeks returned actuals and
`PROJECTION_ACCURACY.json` was written. Full table, both arms of the objection, and the probe that
produced the offline half: **`evidence/w18_instrument/INSTRUMENT.md`**.

**The ruling recorded earlier in this plan -- "a per-position forecast-reliability shrink on `bpa`,
DERIVED from `measure_projection_accuracy` (#18), fixes K/DEF under a plain value sort" -- cannot
be executed, and must not be executed from these numbers.** DEF's realised share of its projected
gap came back at **1.81 (2023) and 5.26 (2024)**: above 1.0 in both seasons, the opposite of the
direction the ruling assumed. A shrink derived from the measurement it named would raise DEF.

The reason is the estimator, not the sport. It is a **two-player difference** -- the player
projected at rank 1 against the player projected at replacement rank -- so n = 1 pair per position
per season, and at the two positions this work exists to fix that resolution is coarser than the
effect:

- **K 2024 = 0.00** because kicker season totals are integers and **three kickers tie at exactly
  133.0** at the replacement rank. Which of the three the projection ranked 12th decides the whole
  ratio.
- **DEF 2024 = 5.26** because the projected DEF gap is **6.7 points across eighteen weeks** -- a
  third of a point a week. It is a division by approximately zero, printed to two decimals.

More seasons cannot repair this; each season adds one more pair.

### What the season does support, measured offline from the committed actuals

The board believes a defense's rank-1-to-replacement spread is **69%** of a quarterback's
(`evidence/blind_pass/KDST_VALUATION.md`: QB 43.9, DEF 30.5). The 2024 season paid **23%**. The
overstatement is **3.1x**, and it is a FLOOR rather than an estimate: hindsight-ranking inflates
every position, and K and DEF carry `sd/gap` of 0.38 and 0.39 against QB's 0.17, so hindsight
inflates them more than QB and the true share is below 0.23. The original complaint -- defenses
taken about five rounds early -- is confirmed as a RELATIVE SPREAD error.

`sd/gap ~ 0.4` is the plainer version: about two fifths of the DEF gap the board is paying for is
next season's coin flips.

### CORRECTED, same session: the 3.1x was measured against a stale board

The paragraph above quotes QB 43.9 / DEF 30.5 from `KDST_VALUATION.md`. Those predate changes to
both the seed CSVs and the engine. Measured on the board the code builds TODAY, DEF's overstatement
relative to QB is **1.3x (2023) and 1.5x (2024)**, not 3.1x -- and on that same board K and DEF are
the two BEST-scaled positions, while RB, WR and TE are overstated relative to QB by 2.1x to 3.6x.

That table is contaminated too, and so was mine: hindsight inflation is not uniform, and measured
`sd/gap` runs in three tiers (RB/WR/TE 0.08-0.09, QB 0.17, K/DEF 0.38-0.39, spanning nearly 5x), so
normalising to QB imports QB's inflation into every row. The clean estimator is the regression
slope of realized on projected over the whole pool, which never ranks by outcome:

| pos | slope 2023 | slope 2024 |
|---|---|---|
| QB | 1.00 | 1.05 |
| RB | 1.05 | 1.07 |
| WR | 1.01 | 1.01 |
| TE | 0.99 | 1.00 |
| K | 1.00 | 1.03 |
| DEF | **1.80** | **2.84** |

Five of six positions have nothing to shrink. DEF is COMPRESSED by a factor of nearly three, so the
ruled shrink would have pushed it the way the data says it is already wrong.

And the structural finding that supersedes all of it: **the board does not price K and DEF from the
projections this instrument measures.** It prices them from two committed CSVs
(`draft_room.KDST_SEEDED_SOURCE_FILES`), and `measure_projection_accuracy`'s docstring claims those
are "exactly the source this reads". Measured, K's CSV pool is 37 players with a top of 116.0
against the weekly sum's 153 and ~157 -- a different artifact. For one of the two positions #18
exists to fix, the instrument has been measuring something else the whole time, and a docstring
asserted otherwise as fact. Same failure as the URL bug in `29ab259`, one level up: there the wrong
belief was about a system we do not control, here it is about our own data lineage.

Full write-up, both passes and every objection: **`evidence/w18_instrument/INSTRUMENT.md`**, which
is the authority over this section.

### LINEAGE SETTLED on the 2026 capture, and #18's PREMISE does not survive it

Neither CSV is the weekly projection, and the pass above had the two positions BACKWARDS. Joined
player by player on 2026: DEF top-12 r = **-0.226** (se 0.33, levels agree at 1.081 while ordering
does not), K top-12 r = **0.708** at a scale of 1.284 +- 0.034. K is the closer match; DEF is the
looser one, in exactly the band a draft discriminates in. The backwards call came from treating a
POOL-SIZE difference as evidence about lineage -- a difference in what a file contains is not
evidence about where its numbers came from.

And the engine question, asked properly at last -- does a projection predict ORDERING inside the
starting band, measured against seasons that finished (Spearman, se ~ 0.33 at a 12-player band):

| pos | 2023 | 2024 |
|---|---|---|
| QB | 0.52 | 0.74 |
| RB | 0.68 | 0.87 |
| WR | 0.64 | 0.69 |
| TE | 0.92 | 0.63 |
| **K** | **0.41** | **0.20** |
| **DEF** | **0.75** | **0.48** |

**DEF ranks about as well as QB. K is the weak one.** #18 was opened to find a DEF reliability
defect and three passes of measurement do not find one. No constant is derivable (#56): four
numbers across two seasons at se 0.33 is not a population.

### Register

- **#18: the ruled shrink is dead three times over** -- the estimator was n=1, the population slope
  says five of six positions have nothing to shrink and DEF is COMPRESSED, and the ordering
  measurement says DEF is not the unreliable position at all.
- **The board's actual K/DEF input has NEVER been validated against a result, and cannot be from
  data that exists.** That needs a seed CSV of 2023 or 2024 vintage; none was kept.
- **CANDIDATE, owner's call (#184):** the weekly projections the app already fetches have measured
  DEF ordering skill (0.75/0.48); the CSV's has never been measured and cannot be. Pricing DEF off
  the measured source is a change with an argument behind it. NOT established as better.
- **#28 is now the strongest remaining explanation** for defenses going five rounds early: two
  vendors on one `bpa` scale with nothing establishing their point scales agree.
- Three passes, three confident conclusions from a quantity ADJACENT to the question -- a
  two-player ratio for a population question, a stale document for a live board, pool sizes for a
  lineage question. Every number was arithmetically right. The failure is **answering with the
  nearest available measurement instead of the one the question asks for**, and the tell is always
  that the quantity is cheap and the question is not.
- **NEW OWNER QUESTION (#184: engine design, not a repair).** The board puts
  `points_vor_draftsharks` (QB/RB/WR/TE) and `points_vor_sleeper_seeded` (K/DEF) on ONE `bpa` scale
  and compares them directly. Two vendors, one number, and nothing establishes their point scales
  agree. That is upstream of every reliability question asked so far and is the standing structural
  candidate for the K/DEF mispricing.
- **No constant is derived, and none may be** (#56). A floor on a relative overstatement is not a
  shrink factor.
- The population estimator that could produce one needs the PROJECTIONS arm offline.
  `capture_weekly_lines.py` is that: one command on a networked machine, one committed file, and
  the instrument repair iterates without a round trip through the owner per hypothesis.
- **#17 stays parked behind #18.**

The sibling of the lesson banked just above: **a ratio computed over two data points is not a
rate, however many decimal places it is printed to.** The engine-measurement checklist already
says to print `n`. Here `n` was 1, and the instrument never printed it.


---

## #28 WITHDRAWN, AND MY CORRECTION OF THE 3.1x WAS ITSELF WRONG

Both errors came from ONE bad measurement: a board built with no `sleeper_projections` argument,
which I then described as "the live board". No caller builds it -- not `app.py` (4927, 5006, 5066,
5431), not `run_draft_battery` (425). Full write-up: **`evidence/w18_instrument/CONFIGURATION.md`**.

**#28 is withdrawn.** Measured on the starting band of every position, in both configurations that
exist in practice, every row prices from ONE source, `points_vor_sleeper_season_scored`. The
two-vendor comparison #28 described happens only on the un-synced fallback. That path is real and
nothing establishes its two vendors' scales agree -- worth a line in the module, not a ruling.

**KDST_VALUATION.md was never stale.** Rebuilt in the BATTERY configuration its numbers reproduce
exactly: QB 43.9, K 12.6, DEF 30.5. The QB 55.0 / K 13.0 / DEF 18.0 I replaced them with came from
the same phantom board. The 3.1x was arithmetically right and is reinstated as such.

**It still must not be used**, for the reason the pass before it gave: it is QB-normalised, and
QB-normalisation manufactures it. The hindsight-free slope disagrees outright -- DEF 1.80/2.84 over
the pool, 3.11/6.36 in the band. DEF's projected spread UNDER-states what the season paid.

### AND A FOURTH REASON THE K/DEF DEFECT IS NOT AN ENGINE DEFECT

DEF's price relative to QB swings **2.2x** -- 0.69 against 0.32 -- purely by changing which season
projections feed the board. Same engine, same league, same code path, same source label. Not a
coverage difference (priced share is near-identical, QB 31% vs 36%, DEF 100% vs 100%): the numbers
themselves differ, and QB's band gap moves 43.9 -> 69.7 while DEF's moves 30.5 -> 22.0.

So "defenses are priced 0.69 of a quarterback" is a fact about a SNAPSHOT, not about the engine.
Under the app-shaped input the same board prices DEF at 0.32 of QB, against the 0.26 and 0.23 the
seasons actually paid.

### Register

- **#28: WITHDRAWN** (was: owner ruling). Characterised and pinned by
  `test_which_call_prices_the_board.py` rather than deleted, so the withdrawal rests on WHERE the
  mixing happens.
- **The 3.1x is un-corrected**, and separately still unusable. Both statements are needed; the
  second is not a hedge on the first.
- **No repair to valuation follows from any of this.** What follows is that a board number is not
  reportable without the call that produced it -- the #166/#174 rule (a quantity travels with the
  basis that gives it meaning) applied to configurations.
- Running tally of withdrawn or corrected conclusions in this thread: the cliff-steepness
  hypothesis, #23, the 3.1x (corrected then un-corrected), #28. Every one was MEASURED rather than
  guessed, and measured on the wrong object -- a league with no K slot, the wrong replacement arm,
  a document assumed stale, a board with no caller. **The configuration is part of the
  measurement**, and this codebase has configurations that differ silently.


---

## #21 IS BLOCKED ON #50, AND ITS OWN BLOCKER NUMBERS WERE STALE

Full study, every figure re-measured on HEAD through the recorded path:
**`evidence/take_model/FLOOR_DERIVATION.md`**.

Three things, in order of how much they change the item.

**1. The stale figures.** `#26` narrowed pool admission at `264e063` after the take-mass evidence
was recorded. Priced rows are unchanged at 481; unpriced fell 638 -> 489, mass 23.49 -> 20.51,
unpriced share 0.543 -> 0.477. Every citation of "638" or "2.0-3.4x" describes a board that no
longer exists. The live source comment in `draft_room.py` and the prose in `test_absence_kind.py`
and `test_take_model_coherence.py` now carry BOTH measurements -- the old one is not overwritten,
because a re-measured number that silently replaces its predecessor makes the older evidence look
wrong rather than dated.

**2. The row's implied remedy makes the defect worse.** "0.02 was derived against a leader of 0.55
while the value model's leader weighs 1.0" reads as "rescale by 1/0.55". Measured: block share of
one pick goes 0.650 -> **0.772**. The drift is not in the leader. It is in the TAIL -- 476 priced
rows that were flat at 0.02 under the rank model decay exponentially over a 13.1-sigma board under
the value model and collapse to ~2.13. The block never moved; everything under it shrank.

**3. THE ACTUAL BLOCKER, and it is not arithmetic.** `0.02` was never a level under the rank model;
it was an EQUALITY -- the same weight 476 of 481 priced rows got, so "unpriced" and "priced but
undiscriminated" were indistinguishable states getting indistinguishable numbers. Under the value
model every priced row IS discriminated, and **only 36 of 481 weigh >= 0.02**. Wiring the value
model unchanged would assert that a row nobody could price is likelier to be taken than the
37th-best player on the board, 445 times over. So the `#187` breach is CREATED BY THE WIRING, and
it sits in two lines (`draft_strategy.py:646-647`) where `None` becomes `0.02` with no label
travelling beside it -- in a module whose `board_contention_scale` answers the same absence thirty
lines earlier with *"None -- not a substituted default"*.

And the floor cannot be derived, because the board asserts two incompatible things about those 489
rows: **ORDER LAST** (unpriced is worst -> floor ~2e-06 -> "unpriced means safe", which the owner
ruled against on 31-of-301 evidence) and **`ABSENCE_NO_INPUT`** (unpriced is unknown-not-bad ->
indifference -> `P/n_p` = 0.010948, share 0.504). `draft_room.py:632-637` already records this as a
`#50` valuation question. **Picking one by arithmetic is choosing, not deriving (#56).**

### Register

- **#21 is BLOCKED ON #50.** Not on measurement, and not on a derivation I can supply.
- The indifference candidate `w = P/n_p` is recorded as the one that survives -- no constant, a
  per-board runtime statistic in the shape `board_contention_scale` already argues for -- and
  explicitly NOT recommended yet: it is a maximum-entropy UPPER BOUND (0.504 against 0.112
  measured), and a bound is not a threshold.
- Do not wire the value model behind a flag; `test_take_model_seam.py:87` forbids a second take
  model and the seam's docstring says so (`#126`).


---

## #24 / W1-07 EXECUTED: necessity's survival term is retired, and the ruling's premise was wrong

**The premise first, because it is the part that would have caused damage.** The ruling row reads:
*"The freed 20 of 100 has to be accounted for -- redistribute or shrink the scale -- and that is
its own derivation."* **There is no 100-point budget.** Measured off the live constants:

| component | max |
|---|---|
| `NECESSITY_BASELINE` | 50.0 |
| standout | 30.0 |
| survival | 20.0 |
| cliff | 12.0 |
| run | 6.0 |
| denial | 20.0 |
| forfeit | 10.0 |
| roster_fit | 9.6 |
| **sum** | **157.6** |

against `raw_score = max(0.0, min(100.0, raw_score))` -- a **CLAMP, not a partition**. Removing 20
leaves 137.6, and `MUST TAKE` (98.0) stays reachable with room to spare. So no redistribution
derivation was owed, and performing one would have been #56's exact prohibition: choosing weights
for a distribution nobody has argued for. Precedent agrees -- **6.1b** retired `eligibility_bonus`
without reweighting its survivor, and **#25** deleted `CONTEXT_ELEVATED_THRESHOLD` outright rather
than repurposing its points.

**The substitute was NOT taken.** The staged patch replaced survival with `intervening_picks`,
which is a property of the TURN: it takes ONE value across every candidate in a snapshot, so it
cannot re-rank anything. That is W1-07's own finding, and it is the reason the term is removed
rather than replaced.

**Cost, re-measured on HEAD** -- one process, one toggle, identical inputs captured by spying on
`compute_pick_necessity` through a real 12-team 16-round draft (`evidence/w1_07/`):

- 8,312 necessity rows scored; 83.2% of scores moved at all; mean 0.42, max 9.80
- **112 label flips (1.35%)**: 99 `PREFERRED -> CLOSE CALL`, 10 `STRONG ACTION -> PREFERRED`,
  3 `MUST TAKE -> STRONG ACTION`
- no constant moved, no label threshold moved

**THE CONSEQUENCE NOBODY HAD WRITTEN DOWN.** `decision_regime` already returns `"contested"`
unconditionally while `SURVIVAL_IS_CALIBRATED` is False, and `withheld_fields()` suppresses the
whole survival family from every surface. With the necessity term gone, **`survival_probability`
now influences no shipped number and no shipped string at all** -- it is computed, carried on the
snapshot, and read by nothing in production. That is a #166-shaped condition and it is stated here
rather than discovered later. The FIELD is deliberately kept: it stays on the snapshot and in the
withholding contract, and retiring that vocabulary would be a far larger ruling than #24.

**Also corrected while in the file:** `cdme_force_ablation` advertises itself as a faithful mirror
of the formula and was **two terms out of date** -- it still summed `eligibility_bonus` (retired at
6.1b) and has never had a `forfeit` component at all. The `eligibility_bonus` drift is fixed here.
The missing `forfeit` is RECORDED, not fixed: adding a seventh component changes `COMPONENTS`'
census and every consumer that iterates it. Its fidelity test passes only because the fixture builds
candidates without `positional_forfeit`, so both sides read `None -> 0.0` and agree on a case that
cannot distinguish them -- a vacuous fixture.

### Register

- **#24 / W1-07: DONE.** Moved `STAGED` -> `IMPLEMENTED` in
  `test_rulings_are_not_silently_dropped` with an inverse witness. `STAGED` is now empty.
- **The "freed 20 of 100" framing is retracted** in `CDME_CONTRACTS.md` and here. It rested on a
  budget that never existed.
- **`CDME_CONTRACTS.md`'s authority bound lost its anchor.** `NECESSITY_WAITING_WEIGHT <=
  NECESSITY_SURVIVAL_WEIGHT (20.0)` names a constant that no longer exists. That weight is pinned
  NEVER IMPLEMENTED, so nothing is unbounded today, but a future proposal needs a new anchor.
- **NEW, recorded not fixed:** `cdme_force_ablation` has no `forfeit` component, and its fidelity
  test cannot see that because its fixture omits the field.


---

## #17 UNPARKED, AND MY OWN HYPOTHESIS ABOUT IT FALSIFIED

`#17` was parked behind `#18` on the reasoning *"#18 is the fix and will likely dissolve the
question."* `#18`'s premise is falsified and no fix is coming from it, so that parking rationale is
gone and `#17` has to stand on its own.

**The hypothesis I formed and then killed.** Given that DEF prices at 0.69 of a quarterback under
the battery snapshot and 0.32 under the app-shaped one, the K/DST complaint looked like it might be
a battery-fixture artifact. Drafted both, one process, snapshot the only difference:

| | battery capture | app-shaped 2026 |
|---|---|---|
| first K | 7.00 | 6.08 |
| first DEF | 5.08 | 6.05 |
| K+DEF by round 12 | 47 | 48 |

**Placement does not move.** A 2.2x change in DEF's relative price moves its first selection by
less than a round. Hypothesis dead.

**What survives is better than what I was looking for:** a FIFTH independent confirmation that
`bpa` magnitude is not what puts defenses in round five. Four earlier measurements said so from
inside; this says it from outside, by MOVING the price rather than zeroing it, and the draft barely
notices. `KDST_VALUATION.md` already recorded the same fact -- *"Zeroing K/DEF bpa entirely still
leaves them at +4.00"*. Whatever selects a defense in round five is reading something other than
how many points it is worth.

**And #17's own numbers are stale.** It records `first DEF 3.09`, `first K 4.10`, `K/DEF by round
12: 37`. On HEAD in the same rulebook with the same snapshot: **5.08**, **7.00**, **47**. Not
explained by `#24` -- necessity has no selection authority (`#55`) and this draft takes
`candidates[0]` off a `team_acquisition_value` ordering.

### Register

- **#17 is UNPARKED and NOT closeable on its current figures.** They do not reproduce. Re-running
  it is a prerequisite to ruling, not a formality.
- **The mechanism stays withdrawn** -- `positional_forfeits` has no selection authority post-`#22`,
  which is unchanged.
- **Standing conclusion across five measurements: `bpa` is not the K/DST driver.** Every remaining
  candidate is downstream of it.


---

## #17 CLOSED BY WITHDRAWAL, and my "no longer reproduce" claim is CORRECTED

The entry above said `#17`'s figures no longer reproduce. **They reproduce exactly** -- first DEF
3.09, first K 4.10, K/DEF by round 12: 37, DEF ratio 3.66, every one as recorded. What differed was
MY probe, and the reason is the finding.

`evidence/blind_pass/turn_ending_remeasured.py` passes
`merger.base_scoring_settings() if hasattr(...) else None` to `league_matrix`. `DataMerger` has no
such attribute, so it always passes `None`, and `league_matrix(None)` returns a rulebook whose
entire scoring is **`{'rec': 1.0}`**. Its `12T_ppr_K_DEF` arm has a K slot and a DEF slot and
**none of the 22 K/DEF scoring keys**. `#17` measured where the engine puts kickers and defenses in
a league where kickers and defenses cannot score.

The probe already carried a correction for this class: its FIRST run used `build_mock_league`, with
no K or DEF slot. That fix supplied the slots and left the scoring vacuous -- half a fix, missing
the half that prices the positions the item is about.

**Re-measured on the 64-key capture rulebook** (`evidence/w18_instrument/`, and the new probe
REFUSES to run if the rulebook has no K/DEF scoring keys):

| pos | ratio, real rulebook | ratio under `{'rec': 1.0}` |
|---|---|---|
| DEF | **1.60** | 3.66 |
| K | **1.24** | 0.49 |
| TE | **1.92** | 1.67 |
| WR | 0.47 | 0.00 |

DEF's 3.66x becomes 1.60x, K's "vanished" 0.49x reverses to 1.24x, and the highest clustering is
now TE. **And at 15 turn-ending picks total, no position's |z| exceeds 2** -- DEF's 1.60x is four
observations against an expectation of 2.50.

### Register

- **#17: CLOSED BY WITHDRAWAL.** The motivating 3.66x was a fixture artifact; corrected it is
  1.60x, below TE's, and indistinguishable from chance. The mechanism was already withdrawn.
- **My previous entry's explanation is corrected here** -- the figures were never stale, the
  rulebook was wrong, and I attributed the difference to drift without checking which league each
  probe had built. The configuration lesson, applied to me, one commit after I wrote it down.
- **Instrument rule earned:** a rulebook needs the SLOTS *and* the SCORING for the positions under
  test. Three vacuity failures in one probe's lifetime -- no slot, then no scoring, plus a sys.path
  break that stopped it running -- each caught only by re-running it for an unrelated reason.


---

# PHASE 8: THE REPAIR MANDATE IS DISPOSED OF IN FULL

Certification: **`evidence/PHASE_8_CERTIFICATION.md`**.

Twelve items (`#16`-`#28`): **seven done, four withdrawn, one blocked on `#50`**. `STAGED` in
`test_rulings_are_not_silently_dropped` is now EMPTY. Every item is disposed of -- nothing
half-done, nothing silently dropped, and the one blocked item names its blocker.

**What a v2 freeze may claim:** seven ruled repairs landed with measured costs and a full green
suite each; the forward test's outcome half works for the first time (the stats endpoint had always
404'd); the measurement re-runs offline from four committed captures; and `bpa` magnitude is not
what puts defenses in round five -- five independent measurements, the last by MOVING the price 2.2x
and watching placement not move.

**What it must NOT claim:** that K/DST pricing is fixed. It is not. What is established is that the
cause is neither `bpa` nor projection reliability, and that every remaining candidate is downstream
of `bpa`. Also not: any per-position reliability constant (`#56` -- four numbers across two seasons
at se ~ 0.33 is not a population), and not that `#21` is resolved.

## The instrument record, which is the honest headline

**Eight conclusions were withdrawn or corrected during this mandate**, every one MEASURED rather
than guessed, and every one measuring the wrong object. Three are the same failure -- a fixture
describing a league nobody plays -- and two are the same phantom board built with an argument no
caller passes.

Four rules are now written into the probes themselves rather than into a document nobody reruns:

1. **The configuration is part of the measurement.** A board number is not reportable without the
   call that produced it (`#166`/`#174` applied to configurations).
2. **A rulebook needs the SLOTS *and* the SCORING for the positions under test.** The new #17 probe
   refuses to run without both.
3. **A test that asserts what our own code constructs is not evidence about a system we do not
   control** (banked at `29ab259`).
4. **A ratio over two data points is not a rate.** The instrument now prints `pairs`, the
   replacement-rank tie count, and a caveat beside any ratio resting on a tie or a near-zero
   denominator.

The most valuable output of this mandate is not a repair. It is a much shorter list of places the
K/DST cause can be, plus four instrument rules that would have prevented most of the eight
withdrawals.
