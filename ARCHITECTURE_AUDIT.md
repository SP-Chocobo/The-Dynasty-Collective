# CDME + AI Orchestration — Architecture Audit

Structured inventory per the Build Guide v2 §25, kept **revision-comparable**: every item carries
STATUS / LOCATION / EVIDENCE / BOUNDARY / RISK / DEPENDENCIES so a later pass can be diffed
against this one rather than re-argued.

**Relationship to `CDME_CONTRACTS.md`.** That document is the evidence and history record for the
deterministic valuation audit. This one records *architectural* conclusions. Where earlier work
already established a fact, it is **cited, not re-proved** — section, invariant, test, and commit.

**Status vocabulary** — EXISTS / PARTIAL / MISSING / VIOLATED / UNKNOWN, plus NOT APPLICABLE
where the question presupposes a deployment shape this system does not have. Per the guide's own
rule, unknown / unavailable / not-applicable are distinct and do not collapse.

**Boundary vocabulary used throughout** — the distinction this pass was asked to hold:

| kind | meaning |
|---|---|
| **instructional** | a prompt or docstring says not to. No mechanism prevents it. |
| **structural** | the shape of the code makes it impossible or requires a deliberate edit (import graph, type discipline, absent code path). |
| **enforced** | a runtime check or a test fails when it is violated. |

---

## Pass 1 — scope, date, baseline

* Sections audited: **§13 Security, Authority Boundaries & Scraping Resistance**, **§8 Proprietary
  IP Protection, AI Exfiltration & CDME Methodology**.
* Baseline: `6190b19`, 1197 tests green, `main` frozen at `9fb5102`.
* Not audited in this pass, deliberately: §3, §4, §20, and everything downstream of the blocked
  research fixture (task #88). §20 in particular is **blocked on the same fixture**, not skipped.

### Deployment shape — established first, because it decides what "client-facing" means

**STATUS: EXISTS (single-process Streamlit, no separate API tier)**
**LOCATION:** `app.py` (Streamlit entry point); no `fastapi`/`flask`/`uvicorn`/`@app.route`
anywhere in the tree.
**EVIDENCE:** a repository-wide search for web-framework symbols returns nothing. All rendering
is server-side; the browser receives Streamlit's own widget protocol plus one embedded iframe
document (`st.components.v1.html`).
**BOUNDARY:** browser ↔ application layer.
**RISK:** low, and it *removes* a large part of §13's attack surface — there are no bespoke
endpoints to over-expose, no predictable REST IDs, and no client-side calculation to inspect.
**DEPENDENCIES:** every §13 finding below is conditioned on this shape. If an API tier is ever
added, this entire pass must be re-run.

---

## §13 — Security, Authority Boundaries & Scraping Resistance

### 13.1 What the browser actually receives

**STATUS: EXISTS (and is the principal exposure surface)**
**LOCATION:** `draft_board_ui.serialize_candidate` / `serialize_snapshot` →
`render_board_html` (`draft_board_ui.py:718`) → `st.components.v1.html`.
**EVIDENCE:** the payload is injected as JSON into a `<script>` block. Its 22 per-candidate keys
are enumerated in `serialize_candidate` and were independently mapped in
`CDME_CONTRACTS.md` → *"D: the decision-boundary information audit"* (commit `0d572ea`). The
browser receives, per candidate: `uv`, `tav`, `needBonus`, `eligBonus`, `rivalPremium`,
`survival`, `intervening`, `forfeit`, `cliffTier/Gap/Typical`, `necessity`, `forces`,
`contextGap`, `waitNote`.
**BOUNDARY:** application layer → browser. **Structural** (this is a deliberate serialization
boundary with a named function), not merely conventional.
**RISK:** see 8.1 — this is where the *decomposition* of the equation leaves the server.
**DEPENDENCIES:** `PickSnapshot` (D), `design_system`.

### 13.2 Script-injection boundary on that payload

**STATUS: EXISTS — enforced, and the reasoning is recorded at the site**
**LOCATION:** `draft_board_ui.render_board_html:732` — `json.dumps(payload).replace("<", "\\u003c")`.
**EVIDENCE:** the docstring documents that `json.dumps` alone is insufficient inside a `<script>`
block because it does not escape `<`, so a player/team string containing `</script>` would break
out into raw document HTML — and records that this was *confirmed*, not hypothesised.
**BOUNDARY:** untrusted vendor/Sleeper strings → browser DOM. **Enforced** (the escape runs on
every render).
**RISK:** low. Player names are the one genuinely arbitrary input and they are neutralised.
**DEPENDENCIES:** any future payload field carrying free text inherits this protection
automatically, since the escape is applied to the serialized whole.

### 13.3 Can a client-facing surface mutate canonical valuation state?

**STATUS: REPAIRED** (was VIOLATED at pass 1). Repair mandated and applied after the finding
crossed the evidence threshold; see "Repair record" below.
**LOCATION:** `app.py:3246` `save_alias(...)` → `data_merger.save_alias:1636` →
`data/player_aliases.json` → consumed by `DataMerger._resolve`.
**EVIDENCE (the original violation):** an audit of every disk write shows `data_merger` writes
exactly one file, the alias map; every other canonical valuation input is read-only at runtime.
`save_alias` performs **no validation** of the target — arbitrary free text from `st.text_input`,
gated only by a non-empty `.strip()`.

`_resolve`'s docstring states the contract: *"`verified` is True only when exactly one row
survived, so a caller can tell 'this is the player' from 'this is the first of several that
fit'."* Every path in the function computes it that way — `exact` → `len(exact_matches) == 1`,
`key` → `len(key_matches) == 1`, `fuzzy` → `len(survivors) == 1`. **The alias branch returned a
hard-coded `True`**, missed by the R1–R3 repair (#77/#82). Since the alias map is the one
client-writable input to identity resolution, the single client-reachable path was also the one
overstating its own certainty.

Probed on an in-memory table holding two rows sharing a normalized name:

| case | row bound | candidates | verified (before) | contract |
|---|---|---:|---|---|
| alias target does not exist | `None` | 0 | `False` | held — **falls through safely** |
| ambiguous, no team | `J Chase` (CIN, tv 100.0) | 2 | **`True`** | **VIOLATED** |
| ambiguous, team matches neither | `J Chase` (CIN, tv 100.0) | 2 | **`True`** | **VIOLATED** |
| *control:* same name, automatic path | `J Chase` | 2 | `False` | held |

The control is what made it a defect rather than a design choice. The feared case was **not** the
defect: a typo'd alias falls through to normal matching rather than rebinding a player.

**REACH — measured on committed vendor data:**

| table | rows | colliding normalized names | rows affected |
|---|---:|---:|---:|
| `projections` (primary valuation table) | 764 | **19** | **38 (5.0%)** |
| `trade_values` | 215 | 0 | 0 |
| `external_values` | 2600 | 698 | 2206 (84.8%) — expected, multiple vendor rows per player |

Real collisions include `j bates` (ATL/DET, **trade_value 5 vs 14**), `j love` (SEA/ARI — Jordan
vs Julian), `g smith` (LAC/NYJ), `c ward` (IND/TEN). Draft Sharks' first-initial export format
makes these structural. **Residual bound, stated honestly:** the defect additionally required
team disambiguation to fail; that joint rate is **unmeasured**, so 5.0% is an upper bound on the
collision surface, not realized exposure.

### 13.3 Repair record

**THE CHANGE — one line, mirroring the three sibling paths, no new rule:**

```python
-  return exact.iloc[0], "alias", len(exact), True
+  return exact.iloc[0], "alias", len(exact), len(exact) == 1
```

**WHAT PRODUCTION BEHAVIOUR CHANGES — measured in-process against the real committed data by
forcing the old value back and diffing, not inferred from the call graph:**

| surface | before | after |
|---|---|---|
| `merge_player`'s reported flag, aliased ambiguous player | `match_verified: True` | `match_verified: False` |
| **Draft board** (`compute_draft_board`) | 229 rows | **229 rows, 0 differing public fields** |
| Trade Calculator (`app.py:3550`, `:3591`) | priced off an arbitrary `iloc[0]` row as certain | reports ambiguous, refuses a price — same as the automatic paths |

The board is **identical** because `_match_verified` is carried onto the pool row and read by
nothing there; `_drop_contested_identities` keys on `_canonical_key`, not on the flag. So the
blast radius is exactly one surface and exactly one flag.

**WHAT THE REPAIR DOES NOT PROTECT AGAINST — stated so it is not mistaken for more than it is:**
* It does **not** validate the alias target. `save_alias` still accepts arbitrary text; an alias
  onto a name that exists but is the *wrong* player still binds to that player and is correctly
  reported as verified, because it genuinely resolves to one row. Only *ambiguity* is now
  reported honestly.
* It does **not** add position narrowing to the alias branch, which the `exact` and `key` paths
  do have. Deliberate — that would change *which row is selected*, a behaviour change beyond the
  certainty claim and outside the repair mandate. The effect of omitting it is conservative:
  some cases report unverified that position-narrowing could legitimately have verified. Recorded
  as an observation, not a defect.
* It does **not** change anything for a consumer that ignores `match_verified`.

**NO OTHER PRODUCTION BEHAVIOUR WAS ALTERED.** The diff is one return statement plus its comment;
no refactor, no constant touched, no other path in `_resolve` modified.

**ACCEPTANCE:** `test_identity_boundary.ManualAliasBranchContractTests`, 8 tests — safe
fall-through, unambiguous-still-verified (guards over-correction), ambiguous-not-verified,
team-matches-nothing, team-does-disambiguate, alias-agrees-with-automatic-path, a general
contract test asserting **no** `_resolve` path hard-codes `verified=True`, and the committed-data
reach guard. **Non-vacuity: reverting the one line fails 4 of the 8**, and the 4 that still pass
are exactly those the repair should not affect.
**DEPENDENCIES:** `_resolve`, R1–R3 (#77/#82), every consumer of `match_verified`.

### 13.4 Can an AI seat mutate, recompute, or override deterministic values?

**STATUS: EXISTS — structurally prevented by three independent mechanisms**
**LOCATION:** `pick_debate.py` (imports, `parse_caller_verdict:297`, `_match_candidate:322`,
`_best_alternative:341`); `pick_synthesis._board_order:168`.
**EVIDENCE — three mechanisms, none of them a prompt:**
1. **Import graph.** `pick_debate` imports only `llm_engine` and `pick_synthesis` types. It cannot
   reach `data_merger`, `draft_room`, or `draft_strategy`, so it has no means to recompute a
   value. Established in D, **pinned by test**
   (`test_pick_synthesis.DecisionBoundaryIsClosedTests`, commit `0d572ea`) and proved
   non-vacuous by injecting `import data_merger` and observing the failure.
2. **Type discipline.** `parse_caller_verdict` extracts **strings only** — every field is the raw
   text after a label; there is no numeric coercion anywhere in the function. The recommendation
   is resolved by `_match_candidate`, a **name lookup against the snapshot's real candidates**,
   returning the actual `CandidateSnapshot` or `None` — never a fabricated row. `_best_alternative`
   is computed deterministically from `team_acquisition_value`.
3. **Ablation.** Every contextual signal was suppressed at its seam, individually and jointly, and
   changed **0 of 12** real decision states on order, TAV and leader, while a positive control
   that zeroed `bpa` moved **12 of 12**. `CDME_CONTRACTS.md` → *"E: ablation over the decision"*,
   commit `0f348d1`, invariants 157–160.
**BOUNDARY:** AI/debate layer → deterministic engine. **Structural and enforced**, not
instructional. The prompt *also* says "never invent, estimate, or silently recompute" — but that
sentence is now redundant to the architecture rather than load-bearing.
**RISK:** low, and newly pinned by the test added in this pass (13.4a below).
**DEPENDENCIES:** `PickSnapshot` immutability; `narrow_candidates` ordering on `final_score` only.

### 13.4a Contract pinned in this pass

**STATUS: EXISTS (new)** — `test_pick_debate.AIOutputCannotBecomeANumberTests` (5 tests), run
against deliberately adversarial Caller prose containing fabricated figures and a hallucinated
player, because the boundary is only interesting under a model that is wrong or hostile.
It asserts every parsed verdict field is a `str`, that the parser did find those fields (so the
first assertion cannot pass vacuously), that a hallucinated name resolves to `None`, that a real
name resolves to the snapshot's own row with the snapshot's own numbers, and that
`_best_alternative` follows `team_acquisition_value` rather than the model's claim.
**Non-vacuity demonstrated, two probes:** making `parse_caller_verdict` coerce floats failed the
string assertion (`0.999 is not an instance of str`); making `_match_candidate` fall back to the
first candidate failed the hallucination assertion. Both reverted.

### 13.5 Authentication, authorization, and tenancy

**STATUS: NOT APPLICABLE as deployed — and a hard blocker for hosting**
**LOCATION:** `app.py` session bootstrap; `st.session_state.user_id` is populated from
`client.get_user_leagues(user["user_id"])` after a **Sleeper username lookup**.
**EVIDENCE:** there is no login, no password, no session token, and no access-control check
anywhere in the tree. `user_id` is a Sleeper *identifier*, not a credential — it authenticates
nothing.
**BOUNDARY:** none exists. This is an accurate NOT APPLICABLE rather than a VIOLATED, because the
system is a single-process, single-filesystem application with no multi-user surface to isolate.
**RISK:** §12's tenancy questions are unanswerable today because tenancy does not exist. The risk
is entirely **prospective**: hosting this as-is would make every §12 question live at once, and
two stores would be immediately wrong — `league_prefs.py` and `league_format.py` use a
module-level global `PATH` rather than the per-league scoping `decision_log`, `pinned_messages`,
`todo_log` and `attachments` all use.

> **Corrected by §12 — see 12.6.** The last sentence is wrong. Both stores use one shared file
> and are nonetheless **correctly scoped by key inside it**: `league_format` by `league_id`
> (deliberately — a league's format is a property of the league, not of a user), `league_prefs`
> by `user_id`. I read the path constant and not the accessor signatures. Their real hosting
> exposure is concurrent writes to one shared file (#102), not miskeying.
**DEPENDENCIES:** any hosted deployment. Recorded so the gap is a known precondition rather than a
discovery made after launch.

### 13.6 Provider credentials

**STATUS: EXISTS — scoped correctly, with the deployment assumption stated at the code site**
**LOCATION:** `app.py:922` `api_key_for`, `:947` `parse_credentials_blob`, `:713`
`save_parsed_keys_to_env`, consumed at `:2031`.
**EVIDENCE:** keys resolve from environment variables or a `st.session_state` override; session
state is server-side and never enters the browser payload. Pasted or uploaded credentials are
parsed by label and by prefix (`sk-ant-`, `AIza`, `sk-`) and **are persisted** — to `.env`, via
`save_parsed_keys_to_env`, which rewrites only the specific `KEY=` lines involved.
`.env` is the **first line of `.gitignore`** (`git check-ignore -v .env` → `.gitignore:1:.env`);
only `.env.example` is tracked. The function's docstring states the scope explicitly: *"This app
is meant to run locally… where .env is private to you; it's not used for the (unsupported) case of
a shared public deployment."*
**BOUNDARY:** user input → credentials → third-party API calls → local disk.
**RISK:** low as deployed, and the assumption is declared rather than implicit. Minor observation,
not a defect: the paste widget is a plain text area with no `type="password"`, so a key is visible
on screen while being entered — immaterial on a single-user local machine, material if the
deployment assumption in that docstring ever changes.
**DEPENDENCIES:** §13.5. The same single-user premise carries both.

---

## §8 — Proprietary IP Protection, AI Exfiltration & CDME Methodology

The guide's instruction for this section was to be strict about *"the code technically contains X"*
versus *"an external party can actually obtain X."* Every item below is stated in terms of what
leaves the process.

### 8.1 What the browser can reconstruct

**STATUS: PARTIAL — the decomposition leaves; the ruler does not**
**LOCATION:** `draft_board_ui.serialize_candidate`.
**EVIDENCE — what ships:** `uv`, `tav`, `needBonus`, `eligBonus` per candidate, per pick. Since
`team_acquisition_value = universal_value + need_bonus + eligibility_bonus`
(`CDME_CONTRACTS.md` §1), the browser receives enough to confirm the **additive structure of the
equation** and to read the **`need_bonus` ladder** directly off observed values (the discrete
`8.33 / 4.33 / 4.00 / 0.33 / 0.00` set measured in the H1/B appendix).
**EVIDENCE — what does NOT ship:** `bpa`, `bpa_source`, `confidence`, `projected_points`,
`time_horizon_adj`, `risk_adj`. Verified by AST read of `serialize_candidate` in D, not by
searching rendered output. So the **VOR construction, the normalization reference, the dynasty
horizon term and the injury term are not obtainable from the browser** — and those are where
`CDME_CONTRACTS.md` measured 94.5% of BPA's movement to live (#76).
**BOUNDARY:** application → browser. **Structural** (a named serializer with an explicit key list).
**RISK:** a determined customer can recover the *shape* of the acquisition equation and the roster
ladder's step values by inspecting the iframe payload across many picks. They cannot recover the
valuation core. Whether the shape alone is material IP is a **product/legal judgement, not an
engineering finding**, and is deliberately not decided here.
**DEPENDENCIES:** #54 (IP hygiene before any sale process) — this is the concrete input that item
has been missing.

### 8.2 What crosses to third-party model providers

**STATUS: EXISTS (larger than the browser surface, by design)**
**LOCATION:** `pick_debate.format_snapshot_for_llm` / `_format_candidate:225`; transport at
`_call_claude` / `_call_gemini` / `_call_openai` (`pick_debate.py:68–115`).
**EVIDENCE:** the evidence block sent to Anthropic / Google / OpenAI contains everything the
browser gets **plus** `bpa_source`, `confidence`, `projected_points`, `opportunity_cost`,
`expected_value_of_waiting`, `denial_value` and the consensus trio. Mapped in D's boundary-2 table
(`0d572ea`).
**BOUNDARY:** application → external provider. **Structural** (one formatter, one call site per
provider).
**RISK:** more of the engine's output crosses to a third party than to the customer's own browser.
This is a *deliberate* asymmetry — the chair needs the numbers to reason — but it means provider
retention and training policy, not the UI, is the binding control on output exposure.
**DEPENDENCIES:** provider terms; §13.6 credentials.

### 8.3 Does the prompt itself disclose methodology?

**STATUS: PARTIAL — semantics disclosed, implementation withheld**
**LOCATION:** `pick_debate.STRATEGIST_SYSTEM_PROMPT:126`, `SKEPTIC_SYSTEM_PROMPT:162`,
`CALLER_SYSTEM_PROMPT:183`.
**EVIDENCE:** the Strategist prompt states the *structure* in prose — *"team_acquisition_value
(universal_value plus this specific roster's own need and lineup-eligibility bonuses)"* — and
defines what each quantity means. It discloses **no coefficient, no normalization, no replacement-
level construction, and no constant**. A read of the prompt text confirms no numeric parameter of
the engine appears in it.
**BOUNDARY:** methodology → provider. **Instructional only** — nothing prevents a future prompt
edit from adding a coefficient, and no test would catch it.
**RISK:** low today, unbounded over time. This is the clearest instance in the pass of a boundary
that is *conventional rather than enforced*: the guide's mandate is that *"the master CDME
equation, coefficients, normalization and proprietary implementation details must not depend on
prompt compliance for confidentiality"* — and today, their absence from the prompt depends on
nobody adding them.
**DEPENDENCIES:** §8.2; any future prompt or chair added to the debate.

### 8.4 Constants in client-shipped code

**STATUS: EXISTS — clean, and the distinction matters**
**LOCATION:** `draft_board_ui.py:44` imports `SLEEPER_WEEKLY_TO_SEASON_FACTOR` from `draft_room`.
**EVIDENCE:** the constant is used **server-side in Python** (`_waiting_note:118`, `:147`) to
compute a per-week figure; only the computed result enters the payload. The iframe template is
CSS/JS with a single JSON token and contains **no engine constant and no engine logic**. This is
exactly the "code contains X" versus "an external party obtains X" distinction: the import exists,
the exposure does not.
**BOUNDARY:** server computation → serialized result.
**RISK:** low.
**DEPENDENCIES:** the single-payload-token template design.

### 8.5 Repeated-query inference

**STATUS: UNKNOWN — reach not established, and deliberately not guessed**
**EVIDENCE:** 8.1 establishes *what* is obtainable per observation. Whether enough observations
can be accumulated to recover more than the shape — for example regressing the `need_bonus` ladder
or bounding the normalization — is a **reach** question, and this program's standard is that reach
is measured, not asserted. It has not been measured.
**BOUNDARY:** customer-visible payload, accumulated over time.
**RISK:** unquantified. Recorded as UNKNOWN rather than assigned a severity it has not earned.
**DEPENDENCIES:** 8.1; a decision about whether the equation's *shape* is material IP at all
(#54), which should precede spending effort on this.

### 8.6 Can external or user-supplied content influence deterministic calculations?

**STATUS: EXISTS for the AI path; PARTIAL overall**
**EVIDENCE:** the AI path is closed — 13.4's three mechanisms, with E's ablation as the empirical
proof. The **one** open path is 13.3's unvalidated alias write, which is user-supplied content
reaching identity resolution and therefore valuation.
**BOUNDARY:** external content → canonical state.
**RISK:** concentrated entirely in 13.3. Everything else in this class is structurally closed.
**DEPENDENCIES:** 13.3's UNKNOWN sub-question is the gate.

---

## Pass 1 summary

| item | status | boundary kind |
|---|---|---|
| 13.1 browser payload | EXISTS | structural |
| 13.2 script-injection escape | EXISTS | enforced |
| **13.3 alias write → canonical valuation** | **REPAIRED** (was VIOLATED) | **enforced** |
| 13.3a alias repair regression | EXISTS | enforced |
| 13.4 AI cannot mutate/recompute | EXISTS | structural + enforced |
| 13.4a AI-authority contract pinned | EXISTS (new) | enforced |
| 13.5 auth / tenancy | NOT APPLICABLE (blocker for hosting) | absent |
| 13.6 credentials | EXISTS (scoped, assumption declared) | structural |
| 8.1 browser reconstruction | PARTIAL | structural |
| 8.2 provider exposure | EXISTS | structural |
| **8.3 methodology in prompts** | **PARTIAL** → **EXISTS** (Pass 2, 4.6) | **instructional only** → **enforced** |
| 8.4 constants in shipped code | EXISTS | structural |
| 8.5 repeated-query inference | UNKNOWN | — |
| 8.6 external content → deterministic | PARTIAL (closed except 13.3) | — |

### Does anything clear the bar for a production change?

**One item did, and it has now been repaired under an explicit mandate: 13.3.** It was a proven
contract violation with a measured collision surface and a one-line repair that mirrors the
function's three sibling paths. Its blast radius was measured rather than asserted: the draft
board is byte-identical, and exactly one surface (the Trade Calculator's ambiguity gate) changes.

**That distinction is the point, and is meant to persist through the rest of the programme:**
13.3 was never an exploratory observation. It crossed the evidence threshold — proven violation,
control showing the sibling path behaves correctly on identical data, reach measured on committed
data, repair specified by tests before it was written — and was therefore treated as a repair,
not as another queued hypothesis. Nothing else in this pass has crossed that line.

Everything else remains either already protected (13.1, 13.2, 13.4, 13.6, 8.2, 8.4), correctly
scoped as not-applicable (13.5), a product/legal judgement rather than an engineering defect
(8.1), a convention not yet broken (8.3), or an unmeasured reach question that has not earned a
severity (8.5).

### Follow-ups, ranked by evidence then severity

1. **Repair 13.3** — `return exact.iloc[0], "alias", len(exact), len(exact) == 1`. Proven defect,
   known fix, tests already written and shown to fail against the repair. Needs only a mandate.
2. **Enforce 8.3 structurally** — a test asserting no engine constant appears in any prompt
   string would convert the guide's confidentiality mandate from convention to enforcement. Cheap,
   and it is the one place this pass found where IP protection rests on nobody editing a prompt.
3. **13.5 preconditions for hosting** — auth, and per-league scoping for `league_prefs` /
   `league_format`, which use a module-level global `PATH` where four sibling stores are
   per-league. Not a defect today; a named precondition.
4. **8.5 repeated-query inference** — only worth measuring after a decision on whether the
   equation's *shape* is material IP (#54). Measuring first would be effort spent ahead of the
   question it serves.

---

## Pass 2 — §3 + §4

**Scope:** Build Guide v2 §3 (canonical state, decision context, product-surface handoff) and §4
(chair contracts, authority, model interchangeability), with **#90** (prompt-constant
enforcement, deferred out of §8.3) folded into §4 where it belongs — a prompt *is* a chair
contract, so "what a chair may not disclose" is a clause of that contract, not a security
afterthought.

**Baseline:** `755ff68` on `ui-authority-pass`; `main` frozen at `9fb5102`. No production file
was modified in this pass.

**Standing caution honoured:** D and E established that the `PickSnapshot` boundary is closed.
That finding is about *one* boundary — the Draft Room engine into the Draft Room debate. It was
not treated as evidence that the handoff architecture as a whole is sound, and §3 below finds
that it is not uniformly sound.

### 3.1 The canonical representation, per surface

**STATUS: EXISTS — and there are two of them, which is the finding**

| surface | canonical object | crosses to a model as |
|---|---|---|
| Draft Room / Mock Draft | `PickSnapshot` (frozen, 8 fields, 37 per candidate) | `pick_debate.format_snapshot_for_llm` — **full fidelity** |
| Trade Calculator | `ScreenContext` via `build_trade_context` | `to_prompt_seed()` → `question_input` → **reaches the Prytaneum** |
| Matchup, Free Agents, League, Draft Room chip, Mock Draft chips | `ScreenContext` | **nothing — display only** |
| The Prytaneum, on every invocation | *none* — `app.build_context()` re-derives a ~250-line string from `snapshot` / `roster_table` / `player_universe` | the string itself |

**LOCATION:** `screen_context.py`; `pick_synthesis.build_snapshot:897`;
`pick_debate.format_snapshot_for_llm:268`; `app.build_context:1493`; `app.render_debate_chip:1356`.
**EVIDENCE:** measured, not read off the source — `chair_inputs.py` stubbed
`llm_engine.PROVIDER_CALLERS` and recorded the exact `(system, user)` pair each chair received.
**BOUNDARY:** surface → AI seat. **Structural** where it exists.
**DEPENDENCIES:** 3.3, 3.4.

### 3.2 Does an AI seat ever reconstruct information from rendered UI?

**STATUS: EXISTS — no, and structurally so**
**EVIDENCE:** no HTML/DOM parser of this app's own output exists anywhere in the tree (the one
`scrape` reference is an inbound ESPN *article* parser in `data_merger:860`, not a read of our
own UI). `draft_board_ui.render_board_html` is one-way: server → iframe, single JSON token, with
no read-back path (§13.1). Every AI input is assembled from Python values the caller already had.
**BOUNDARY:** rendered surface → AI seat. **Structural** (the mechanism does not exist).
**RISK:** low. This is the §3 question the architecture answers best.

### 3.3 The ScreenContext reach gap — a canonical context that is built, displayed, and dropped

**STATUS: VIOLATED against the dock's own stated contract — display-layer, not engine-layer**

**LOCATION:** `app.py:1356` (`render_debate_chip`), `app.py:5527-5539` (the "Considering" block),
`app.py:5661` (`context = build_context(...)`), `screen_context.to_prompt_seed:58`.

**EVIDENCE.** Seven `render_debate_chip` call sites build a `ScreenContext` through the shared
builders. The chip writes it to `st.session_state.debate_attached_context`. Exactly two reads of
that key exist in the whole tree: the write at `:1371` and a **render** at `:5533`. When the user
then asks a question, `run_debate` / `ask_quant` / `ask_beat` / `ask_moderator_followup` are all
called with `build_context(snapshot, roster_table, player_universe, trigger_question)` — the
attached context is not a parameter of any of them.

`to_prompt_seed()`, the method whose docstring calls it *"the exact text block a Debate control
seeds its conversation with"*, has **one** production caller: `app.py:3939`, the Trade Calculator.

Measured reach for the Draft Room chip specifically — does anything it shows survive into what
the panel is actually given? Sixteen engine field names checked against the full source of
`build_context`:

| field | present in `build_context` |
|---|---|
| `pick_label`, `decision_regime`, `necessity_label`, `team_acquisition_value`, `survival_probability`, `pick_necessity`, `universal_value`, `need_bonus`, `eligibility_bonus`, `opportunity_cost`, `denial_value`, `positional_forfeit`, `consensus_rank`, `reach_label`, `candidates`, `PickSnapshot` | **0 of 16** |

`build_context`'s parameters are `(snapshot, roster_table, player_universe, question,
conversation_window)`. It has no draft argument and no notion of a pick. The scope state the
other builders carry — `focus_position`, `matchup_expanded_position`, `fa_position_filter`,
`fa_search` — is likewise absent. (Two tokens, `team_label` and `surface`, matched as substring
artifacts of unrelated code and prose; both were checked by hand and discarded.)

So a user on the clock in the Draft Room who clicks 💬 Debate and asks a question is told
*"💬 **Considering:** On the clock for pick 4.03."* while the four chairs receive no pick, no
board, no candidate, and no engine number at all.

**Why this is a violation rather than a design choice.** `screen_context.py`'s own module
docstring is accurate and honest: it says the Prytaneum reads a ScreenContext as plain data *"(or,
today, the existing question_input seeding a surface's own escalation buttons write to)"* — an
explicit acknowledgement that only the question_input path is wired. `render_debate_chip`'s
docstring is also accurate: opening and asking are deliberately two separate actions. The
violation is neither of those. It is `app.py:5527`, which states the intended reading of the
"Considering" line: *"This is meant to read as 'Debate already understands what I was looking
at.'"* The panel does not understand it, and cannot — the object never leaves the render path.
Measured against the app's own stated contract, exactly as 13.3 was, that claim is false for six
of the seven chips.

**BOUNDARY:** canonical context → AI seat. **Instructional at best** — nothing enforces the
handoff, and `test_debate_chip_wiring.py` (which exists precisely to protect this contract)
asserts only that each site *builds* via the shared builder and does *not* write `question_input`.
No test asserts the attached context reaches a model, because it does not.

**RISK: moderate, and it is a user-trust risk rather than a correctness one.** No wrong number is
produced; a well-grounded panel answer is simply not given the grounding the screen says it has.
The failure mode is a confidently generic answer that the user reads as context-aware.

**DEPENDENCIES:** 3.1; `build_context`'s parameter list; §4's chair input contract.

### 3.3a Proposed repair and measured blast radius — NOT APPLIED

Per the mandate, this is reported rather than performed.

*Repair (smallest form).* At the single trigger site (`app.py:5659-5661`), prepend the attached
context to the string already being built:

```python
context = build_context(snapshot, roster_table if roster else [], player_universe, trigger_question)
attached = st.session_state.get("debate_attached_context")
if attached is not None:
    context = attached.to_prompt_seed() + "\n\n" + context
```

*Blast radius, measured.* One call site; one added string concatenation; no engine module
touched; no valuation path reachable from it (the ingestion boundary at `draft_room:518` /
`pick_synthesis:413` whitelists `source_name == "keeptradecut"` and is enforced by
`test_cdme_ingestion_boundary.py`, so nothing added to a prompt can re-enter CDME). Context
growth is bounded by construction: `_MAX_CANDIDATES_IN_CONTEXT = 8` caps the two capped builders,
and the largest ScreenContext evidence block measured on a real board was **456 characters**
against a `build_context` body of tens of thousands — under 2%.

*Two open questions the repair does not settle, and why it should not be applied blind.*
1. **Staleness.** Nothing clears `debate_attached_context`; `app.py:5530` says so explicitly
   (*"there's no signal yet for 'the user is done with this'"*). Today that only makes a stale
   line render. Wiring it to the model makes a stale line **argue**. A lifetime rule is a
   prerequisite, not a follow-up.
2. **Which handoff wins.** The Trade Calculator would then carry its context twice — once
   through `question_input`, once through the attachment — because its chip and its escalation
   buttons write the same object by two routes.

*Verdict:* **DEFER to a scoped repair mandate.** The evidence is complete and the contract
violation is proven; the repair is blocked on a lifetime decision that is the owner's to make,
not on more measurement.

### 3.4 One snapshot, three consumer projections — measured

**STATUS: EXISTS (asymmetric by design), with one honest qualification**

**EVIDENCE** (real committed vendor data, 12-team superflex, snapshots at rounds 1/4/8):

| consumer | fields per candidate | rows | fidelity |
|---|---|---|---|
| engine object (`CandidateSnapshot`) | **37** | all | — |
| `pick_debate.format_snapshot_for_llm` | ~20 rendered | all (72/65/40) | **unrounded** — engine TAV `84.44` arrives as `84.44` |
| `draft_board_ui.serialize_candidate` | **22** | all | mixed |
| `screen_context.build_draft_room_context` | **5** | top **8** | TAV `:.0f`, survival to whole % |

This is B2 (decision object → per-consumer projection, lossy and asymmetric), already established
— what is new is the *span*: 37 → 22 → 5, and one of those three consumers is a model.

**Rounding, measured honestly.** Across the whole candidate list the `:.0f` TAV collapses 21–24
values per round into shared display integers. But the chip renders only 8 rows, so the number
that matters is confined to those: **1 of 7** adjacent engine-ordered pairs at round 1, **4 of 7**
at round 4, **2 of 5** at round 8, become the same displayed integer (e.g. `79.07/78.61 → 79`).

**The qualification that keeps this from being a defect:** every collapsed pair measured is
within `NEAR_TIE_BAND = 2.0`. By the engine's own semantics those *are* near-ties, so the display
is not asserting a falsehood — it is declining to draw a distinction the engine itself labels as
not meaningful. **Verdict: DOCUMENT.** No production change.

### 3.5 What is intentionally withheld from each chair

**STATUS: MISSING — nothing is withheld from anyone**

**EVIDENCE (measured).** `ask_quant` and `ask_beat` produced **byte-identical user prompts** on
identical input (`quant user_prompt == beat user_prompt: True`); every chair's prompt contains the
base context block verbatim. Downstream chairs receive the same block plus prior chairs' prose.
`pick_debate` is the same shape: one `evidence` string built once and handed to all three chairs.

There is therefore no per-chair projection of the decision context anywhere in either system.
The Quant is handed the whole news-and-freshness apparatus it is told not to use; the Beat is
handed every projection and VORP figure it is told not to compute with.

**BOUNDARY:** context → chair. **Absent.** The separation of chairs is carried entirely by the
system prompt — see 4.3.
**RISK:** low today, structural over time. **Verdict: DOCUMENT**, and it is the honest answer to
the guide's question rather than a defect: role-appropriate projection is a design the app has
not adopted, not one it has adopted and broken.

### 3.6 Can an invocation record exactly which context it was supplied?

**STATUS: MISSING**
**LOCATION:** `app.append_message:801`; `decision_log.log_decision:36`;
`pick_debate.PickDebateResult:360`.
**EVIDENCE:** `append_message` persists `{role, content, ts, provider, model}`. `log_decision`
persists question, the eight parsed verdict fields, and the Moderator's prose. Neither stores the
`context` string, a hash of it, or any reference to it — the string is built at `app.py:5661`,
passed, and garbage-collected. `PickDebateResult` carries `role_providers` but **not**
`role_models` and **not** the snapshot it ran on.
**BOUNDARY:** invocation → audit record. **Absent.**
**RISK:** moderate for a hosted product, low for single-user desktop use. Causal reconstruction
(§10) rests on this and cannot be answered affirmatively until it exists.

### 3.7 Replay

**STATUS: MISSING**
**EVIDENCE:** replay requires 3.6. Inputs are not recorded, so an operation cannot be re-run
against its own inputs; and there is no flag anywhere distinguishing a replayed run from a fresh
one, because there is no replay path to flag. `st.session_state.draft_room_last_snapshot` keeps
exactly one prior snapshot, for diffing the next pick, and is overwritten each time.
**DEPENDENCIES:** 3.6, 3.9.

### 3.8 Temporal consistency within one deliberation

**STATUS: EXISTS**
**EVIDENCE:** `context` is built once per trigger and the same object is passed to all four
chairs; `run_debate` parallelises Quant and Beat but over that one string. `pick_debate` freezes
harder still — a frozen `PickSnapshot` computed once and handed to all three chairs, with
`diff_snapshots` giving the debate an explicit record of what moved since the previous pick. If
the underlying data changes mid-debate, no chair sees the change.
"What does *current* mean" is also answered per category rather than globally:
`build_freshness_manifest` emits `(label, as-of date, days old)` for every dated source, sorted
freshest-first, with STALE (≥7d) and EGREGIOUSLY OUTDATED (≥30d) flags. That is a real answer to a
question most systems cannot answer at all.
**BOUNDARY:** time → deliberation. **Structural** (single-build, pass-by-reference).

### 3.9 An immutable context that can be *referenced* rather than copied

> **Partially corrected by §11 — see 11.6.** This entry's conclusion was too strong.
> `PickSnapshot` *does* carry an explicit input-state stamp (`picks_consumed` +
> `data_freshest_date`), documented as such, with a `snapshot_is_current` certifier built on it.
> What is genuinely missing is a *unique identifier* and persistence, not provenance. Read the
> paragraphs below with that correction applied.

**STATUS: PARTIAL**
**EVIDENCE:** `PickSnapshot` is frozen and immutable — half the property. The other half is
missing: its fields are `pick_label, round, my_roster_id, candidates, user_selected_player_id,
picks_consumed, data_freshest_date, decision_regime` — **no id, no hash, no computed-at
timestamp**. Consumers therefore hold the object itself, not a reference to it, and nothing
outside the live session can name the snapshot a given verdict was produced against.
`data_freshest_date` is a partial temporal anchor and is the nearest thing to provenance the
object carries. **Verdict: DOCUMENT.** A snapshot identifier is cheap and would unlock 3.6, 3.7
and §10 together — but it is only worth adding *with* the record that would consume it, not
speculatively ahead of one.

---

### 4.1 Is the architecture built on stable chair contracts?

**STATUS: EXISTS — and there are two chair systems, deliberately**

| | The Prytaneum | Draft Room debate |
|---|---|---|
| chairs | Quant, Beat, Contrarian, Moderator | Strategist, Skeptic, Caller |
| prompts | `llm_engine.*_SYSTEM_PROMPT` via `ROLE_SYSTEM_PROMPTS` | `pick_debate.*_SYSTEM_PROMPT` |
| input | `build_context` string + question (+ prior prose) | `format_snapshot_for_llm` + prior prose |
| provider/model routing | per role, user-configurable, persisted (`bot_config`) | fixed `DEFAULT_ROLE_PROVIDERS` |
| live search | yes (Beat, Contrarian) | **no, by design** |

**EVIDENCE:** neither is one continuous conversation. Each chair is a separate call with its own
system prompt and an explicitly-constructed user prompt; nothing carries a chat thread between
chairs. The separation of the two systems is deliberate and named in code
(`screen_context.DRAFT_ROOM_PICK_DEBATE_HELP`, and `debate_pick`'s docstring: *"an orchestration
layer, exposing its own defaults, not a slot in the existing four-role trade-debate roster"*),
and the distinctness of the two Debate-labelled controls on the Draft Room screen is enforced by
`test_screen_context.DebateHelpTextDistinctnessTests`.
**BOUNDARY:** chair → chair. **Structural.**

### 4.2 What prevents Beat from becoming an accidental Quant?

**STATUS: PARTIAL — instructional only, and it is the *only* mechanism**

**EVIDENCE:** the prohibition exists and is explicit in both directions —
`QUANT_SYSTEM_PROMPT`: *"Do not speculate about injuries, depth charts, or locker-room narrative
… that is other analysts' jobs."* `BEAT_SYSTEM_PROMPT`: *"Do not run Draft Sharks' VORP math
yourself — that is the Quant's job."* And per 3.5, both chairs are handed byte-identical context,
so each has in hand everything it is told not to use. Nothing detects a chair that ignores its
prohibition; no output is checked against its chair's remit.
**BOUNDARY:** chair remit. **Instructional.** This is the cleanest example in the programme of
the distinction the vocabulary exists to draw: the boundary is real, stated, and load-bearing —
and rests entirely on model compliance.
**RISK:** low today, and it rises with model substitution rather than with time. A model swapped
into the Beat chair that is stronger at arithmetic than at search will drift toward Quant work,
and nothing in the architecture will notice.
**Verdict: DOCUMENT.** Enforcing role separation means either projecting the context per chair
(3.5) or classifying chair output, and neither has an evidence base yet. Named here so a future
model-substitution pass (§5) starts from a known-unenforced boundary rather than assuming one.

### 4.3 Are chair outputs structured?

**STATUS: PARTIAL — 2 of 7 chairs have a canonical intermediate representation**

| chair | structured output | parser |
|---|---|---|
| Moderator | yes — 11 labelled fields | `parse_moderator_verdict` + `VERDICT_FIELDS` |
| Caller | yes — recommendation/confidence/why/dissent/key factor | `parse_caller_verdict` |
| Quant, Beat, Contrarian, Strategist, Skeptic | **no — free prose only** | — |

**EVIDENCE:** the five prose chairs' output is consumed only as a string, pasted into the next
chair's user prompt. The two structured chairs are both *synthesizers*, and both are parsed
defensively — `parse_caller_verdict` extracts strings with no numeric coercion, and the
recommendation is resolved by name lookup against the snapshot's real candidates (§13.4).
**BOUNDARY:** chair output → downstream. **Structural where it exists** (the parsers cannot
fabricate a row), **absent** for the five prose chairs.
**RISK:** this is the load-bearing constraint on model interchangeability — see 4.4.

### 4.4 Model interchangeability, and what a replacement model actually inherits

**STATUS: PARTIAL**

*What holds.* Chair **inputs** are defined entirely independently of the occupant: every `ask_*`
takes `(context, question, [prior reports])` and receives `provider` / `api_key` / `model` as
parameters. `run_debate` states it has *"no opinion of its own about which provider belongs to
which role."* A model can be swapped per chair from the UI without touching a prompt, and the
`moderator_personality` directive is scoped to tone and to the Moderator alone. Provider and model
are stamped on each persisted message at the time it was written, so an old message keeps showing
what actually answered it.

*What does not hold.* **A replacement model in a downstream chair inherits its predecessor's
prose, not its evidence.** The guide's own test case — *"if Beat Model A found 14 sources and
Model B takes over, can B see the actual evidence package?"* — resolves to **no**: Contrarian and
Moderator receive `result.beat` as an opaque string. There is no per-chair evidence record: no
list of sources consulted, none of accepted-vs-rejected claims, no confidence attached to
anything except the Moderator's own single `CONVICTION` line.

*The partial exception, and its shape.* `bot_research.py` is a real structured evidence store —
`{id, player_name, source, claim, rank, conviction, question, league_id, date}`, deduped
same-day, read back into later contexts. But it is populated by `parse_source_findings` from the
**Moderator's** output, gated on the Moderator's own judgement that the panel did not dispute the
claim. The evidence package is therefore reconstructed from the synthesizer's prose, one chair
removed from the chair that found it, and only for the fraction the synthesizer chose to emit.
**Verdict: DOCUMENT.** Real, and the largest genuine gap in §4 — but a per-chair evidence schema
is a design commitment, not a repair, and belongs to §5's model-substitution work.

### 4.5 Chair contract versioning

**STATUS: MISSING**
**EVIDENCE:** no `CONTRACT_VERSION`, `PROMPT_VERSION`, or equivalent exists anywhere in the tree.
Prompts are edited in place. Consequently: a benchmark cannot be tied to a contract version, a
model change cannot be scoped to "which downstream benchmarks must be re-run," and two runs weeks
apart are indistinguishable in the record even if the chair's instructions changed between them.
**RISK:** low while one person owns every prompt; a precondition for §5's "unknown-model
evaluation" to mean anything.
**Verdict: DOCUMENT** — a named precondition, not a defect.

### 4.6 #90 — what a chair may not disclose, now ENFORCED

**STATUS: REPAIRED at the boundary level — instructional → enforced. No production change.**

**LOCATION:** `test_prompt_constant_boundary.py` (new, 10 tests).

**EVIDENCE — the measurement first.** 56 engine constant names / 101 numeric literals were
discovered by AST across six engine modules, and scanned against all 16 prompt strings a provider
can receive plus the string literals of `app.build_context` and `screen_context`:

| scan | result |
|---|---|
| engine constant **name** in any of the 16 system/personality prompts | **0** — §8.3's finding holds, and now extends to the Prytaneum's four chairs, not just `pick_debate`'s three |
| engine constant **name** in `build_context` prose | **1** — `COMPOSITE_SOURCE_WEIGHTS`, together with `data_merger.py` |
| distinctive coefficient **values** anywhere in the prompt surface | **0** |

**A correction to this pass's own method, recorded.** The first run of that scan reported **0**
hits in `build_context` and was wrong. It walked only `ast.Assign`, and `COMPOSITE_SOURCE_WEIGHTS`
is an `ast.AnnAssign` (`COMPOSITE_SOURCE_WEIGHTS: dict[str, float] = {...}`). A constants scan
blind to annotated constants would have shipped as proof of a property it could not see. The
shipped test handles both forms and pins the specific case by name
(`test_annotated_constants_are_discovered`).

**On the one hit.** `build_context` tells each chair that the composite figure it is handed is a
*weighted* blend and in which direction — Draft Sharks up, KeepTradeCut down, fresher counts more
— so the chair weighs the per-source disagreement beside it instead of treating the blend as
settled. It discloses the weight set's existence and direction, never a weight: 1.3 / 1.0 / 0.7 /
0.5 do not appear, and this is a vendor-blending parameter in `data_merger`, not a term in the
CDME equation. Recorded as `DISCLOSED_BY_DESIGN` with that reasoning, and fenced: a separate test
fails if the values ever join the name.

**Non-vacuity — three probes, each planted in real production text and reverted:**

| probe | result |
|---|---|
| `NEED_BONUS_MAX` planted in `QUANT_SYSTEM_PROMPT` | **FAIL** — caught in both `QUANT_SYSTEM_PROMPT` and `ROLE_SYSTEM_PROMPTS['quant']` |
| `0.55` (a `RANK_TAKE_PROBABILITY` value) planted in `build_context` prose | **FAIL** |
| the composite weights `1.3` / `0.7` planted beside their allowed name | **FAIL** |

The suite also guards its own reach: it fails if constant discovery collapses, if the prompt
surface shrinks below 16 producers, or if any of the seven chairs' prompts stops being scanned —
because a scan that has quietly stopped looking is indistinguishable from a clean result.

**BOUNDARY:** methodology → provider. **Enforced.** §8.3's status moves PARTIAL → EXISTS.
**RISK:** the value scan is deliberately incomplete and says so: a bare `12` or `0.5` cannot be
distinguished from ordinary prose, so only literals with two or more decimals are scanned. The
**name** scan is what holds the boundary; the value scan is a second net with stated holes.

### 4.7 Correction to Pass 1 — the scope of 13.4's "structurally prevented"

13.4 concluded that an AI seat cannot mutate, recompute, or override deterministic values, on
three mechanisms. That conclusion **stands as stated, for the CDME valuation path**, and this
pass found the mechanism that makes it true: `draft_room._rookie_lookup:518` and
`pick_synthesis:413` both filter `merger.external_values` to `source_name == "keeptradecut"`,
which is what keeps `bot_research.json`'s LLM-originated rows out of the engine — documented in
both docstrings and enforced by `test_cdme_ingestion_boundary.py`'s adversarial injection tests.

**But 13.4 as written could be read more broadly than the evidence supports, so:** there *is* one
designed path by which model output becomes a number in a deterministic calculation.
`bot_research` findings that carry a rank are loaded as a synthetic external source
(`data_merger.load_bot_research_as_external:1576`) and enter `composite_player_score` at
`COMPOSITE_SOURCE_WEIGHTS["bot_research"] = 0.5` — the lowest weight of any source, below
KeepTradeCut's crowd average, explicitly *"to reflect that extra layer of uncertainty."* The
composite surfaces in the Trade Calculator (`app.py:3548`) and in `build_context`'s roster table.

This is deliberate, weighted, deduped, gated on the Moderator's non-dispute rule, disclosed to the
chairs in `build_context` itself, and structurally excluded from CDME. It is not a defect.
Recording it because "the AI cannot affect any deterministic number" is a stronger claim than the
architecture makes, and the audit record should carry the accurate one.

---

## Pass 2 summary

| item | status | boundary kind |
|---|---|---|
| 3.1 canonical representation per surface | EXISTS (two systems) | structural |
| 3.2 no reconstruction from rendered UI | EXISTS | structural |
| **3.3 ScreenContext reaches the model** | **VIOLATED** (display-layer) | **instructional** |
| 3.3a repair specified, blast radius measured | DEFERRED to a scoped mandate | — |
| 3.4 one snapshot, three projections | EXISTS (asymmetric by design) | structural |
| 3.5 per-chair withholding | MISSING (nothing withheld) | absent |
| 3.6 invocation records its context | MISSING | absent |
| 3.7 replay | MISSING | absent |
| 3.8 temporal freeze within a run | EXISTS | structural |
| 3.9 immutable context, referenceable | PARTIAL (frozen, unidentified) | structural |
| 4.1 stable chair contracts | EXISTS | structural |
| 4.2 chair remit separation | PARTIAL | **instructional only** |
| 4.3 structured chair outputs | PARTIAL (2 of 7) | structural where present |
| 4.4 model interchangeability | PARTIAL (inputs yes, evidence no) | structural / absent |
| 4.5 chair contract versioning | MISSING | absent |
| **4.6 no engine constant in a prompt (#90)** | **EXISTS (new)** | **enforced** |
| 4.7 correction to 13.4's scope | — | — |

### Does anything clear the bar for a production change?

**One item clears the evidence bar and is being reported rather than applied: 3.3.** It is a
proven violation of the app's own stated contract, measured the same way 13.3 was — 0 of 16
engine fields reach the panel, one production caller of `to_prompt_seed`, two reads of the
session key of which one is a render. The repair is four lines at one call site with a measured
sub-2% context cost and no reachable path into the valuation engine.

It is nonetheless **not** in the same class as 13.3, and the distinction is worth keeping sharp.
13.3 was a wrong answer: an arbitrary row reported as verified, changing a price. 3.3 produces no
wrong number — it withholds grounding the screen says was handed over. And unlike 13.3, whose fix
was fully determined by three sibling code paths, 3.3's fix depends on a decision nobody has made
yet: how long an attached context should live. **DEFER, pending a scoped repair mandate.**

Everything else is EXISTS (3.1, 3.2, 3.4, 3.8, 4.1, 4.6), a design the app has not adopted rather
than one it has broken (3.5, 4.3, 4.4), or a named precondition for later sections (3.6, 3.7,
3.9, 4.5).

### Follow-ups from this pass, ranked by evidence then severity

1. **3.3 — scoped repair mandate for the ScreenContext handoff.** Evidence complete; blocked only
   on the attachment-lifetime decision. Highest-value item in the pass.
2. **3.9 + 3.6 together — a snapshot identifier and a recorded context reference.** One small
   addition unlocks §3's replay questions and §10's causal reconstruction at once. Worth doing
   *with* the record that consumes it, never speculatively.
3. **4.4 — a per-chair evidence schema.** The largest genuine architectural gap found, and the
   right owner is §5 (model selection and substitution), where its value is actually realised.
4. **4.2 / 3.5 — per-chair context projection.** Would convert chair-remit separation from
   instructional to structural. No evidence base yet that drift actually occurs; measure before
   building.
5. **4.5 — chair contract versioning.** Cheap, and a precondition for §5's benchmarking to be
   meaningful. Not worth doing before §5 is scoped.

---

## Pass 3 — §5

**Scope:** Build Guide v2 §5 (model selection, optimization, unknown-model evaluation), whose
mandate is that *"model optimization must be role-specific, empirical, repeatable, versioned,
and downstream-aware. 'Best model' is not a universal property; it is a property of a chair
contract under a defined operating envelope."*

**Baseline:** `84cf154` on `ui-authority-pass`; `main` frozen at `9fb5102`. No production file
was modified. #91–93 remain queued and were not advanced; §4.5 (contract versioning) and §4.4
(per-chair evidence) recur here as §5 questions and are cross-referenced to #93 rather than
built.

**The headline: §5 is the best-served section audited so far.** `bot_benchmark.py` is a real,
working, role-specific, empirical methodology — not a stub and not a plan. The findings below
are about its *envelope*, not its absence.

### 5.1 Does a model-selection methodology exist for each chair?

**STATUS: EXISTS**
**LOCATION:** `bot_benchmark.py` — `BENCHMARK_BATTERY:37`, `RUBRIC:196`, `_judge_response:231`,
`run_benchmark:262`; UI at `app.py:2277-2360`.
**EVIDENCE:** three fixed scenarios per chair, a four-dimension weighted rubric per chair
(weights sum to 100, verified by existing tests), each answer scored by a separate judge call,
weighted average per model, results sorted best-to-worst and persisted. Rubrics are deliberately
**not** shared across chairs — the module's own reasoning is that *"'accuracy' means something
different for a Quant's math than for a Beat Tracker's news reporting."* That is exactly the
guide's "property of a chair contract, not a universal property" framing, implemented.
**BOUNDARY:** reputation → measurement. **Structural** (the battery is the only input to the
ranking).

### 5.2 Testing a never-before-evaluated model without human intervention

**STATUS: EXISTS for testing; human-in-the-loop for selection, by design**
**EVIDENCE:** candidates are `(provider, model)` pairs drawn from a live model-list fetch
(`llm_engine.LIST_MODELS_BY_PROVIDER`), so a model released yesterday can be benchmarked today
with no code change and no per-model configuration. The battery, rubric, and judge are all
model-agnostic.
Applying the result is **not** automatic: `app.py:2354` offers an explicit *"Apply … to …"*
button, and only for the rank-1 candidate. `bot_benchmark` never writes to `bot_config` — the
module docstring states this as a deliberate separation.
**RISK:** low. Autonomous *evaluation* with human *selection* is a defensible reading of the
guide; noted rather than faulted.

### 5.3 Blind judging — the one safeguard that matters, now enforced

**STATUS: EXISTS → ENFORCED (new this pass, test only)**
**EVIDENCE:** `_judge_response` receives `(role, question_prompt, response_text,
judge_provider, judge_api_key, judge_model)` — the candidate's provider and model are not
parameters, so they cannot be leaked. Measured by stubbing the provider caller and capturing the
exact judge prompt: it contains the task, the response, and the rubric, and none of `gemini`,
`openai`, `anthropic`, `claude-opus`, `gpt-4o`.
**Now pinned** by `test_benchmark_contract_coverage.JudgeBlindnessTests`, including a signature
guard so a future parameter carrying candidate identity is a test failure. Non-vacuity: planting
`"MODEL UNDER TEST: gpt-4o"` into the judge prompt **fails** the blindness test; a companion test
asserts the prompt does carry task, response and rubric, so blindness cannot pass by emptiness.
**Residual, stated:** the *response text itself* can still identify its author (a model that
writes "as an AI developed by …"). Nothing scrubs that, and nothing could reliably.
**BOUNDARY:** candidate identity → judge. **Enforced.**

### 5.4 Chair coverage

**STATUS: PARTIAL — 4 of 7 chairs**
**EVIDENCE:** `BENCHMARK_BATTERY` covers exactly the four Prytaneum chairs. The Draft Room's
`strategist` / `skeptic` / `caller` have **no battery, no rubric, and no routing UI** — their
providers come from `pick_debate.DEFAULT_ROLE_PROVIDERS`, and `debate_pick` is never passed
`role_models` from `app.py:4783`. This is documented as deliberate (*"an orchestration layer,
exposing its own defaults, not a slot in the existing four-role trade-debate roster"*), and it is
consistent — but it means the three chairs that reason directly over the CDME snapshot are the
three with no model-selection methodology at all.
**Pinned** by `test_the_draft_room_chairs_have_no_battery_and_that_set_is_pinned`, so adding a
fourth Draft Room chair, or moving one under `bot_config`, becomes visible.
**Verdict: DOCUMENT.** Building a Draft Room battery is real work with a real prerequisite —
it would need snapshot fixtures, which is #88's blocked capture.

### 5.5 The operating envelope — benchmark vs production

**STATUS: PARTIAL — the chair contract is exact; the context schema is not**

**EVIDENCE.** `run_benchmark` uses `llm_engine.ROLE_SYSTEM_PROMPTS[role]` — the *production*
system prompt object, not a copy. That is the strongest possible answer to "does the benchmark
evaluate behavior under the exact chair contract," and it is now pinned by test.

The user half does not match, in two ways:

| | benchmark | production |
|---|---|---|
| shape | the bare scenario string | `f"League/roster context:\n{context}\n\nQuestion: {question}"` |
| size | quant 244–531 · beat 331–428 · contrarian 249–271 · moderator 628–973 chars | `build_context` (roster table, league-wide depth, freshness manifest, conversation memory, to-dos) — the comparable `pick_debate` evidence block measured **29,828–52,766** chars on real boards |

So every model is graded on a message shape it will never receive, at roughly **two orders of
magnitude** less context than production. Two §5 questions fall out of this directly:
*"How are scores made comparable when models have different context capacity?"* — the question
never arises, because no scenario approaches any model's capacity. And *"can a model be
disqualified from a chair because it cannot reliably accommodate that chair's required
context?"* — **no**, structurally: the battery never exercises the context that would disqualify
it.
**RISK:** moderate. A model whose quality degrades over long context ranks identically to one
that does not.
**DEPENDENCIES:** a realistic-envelope battery needs a fixture (#88, blocked). Named, not built.

### 5.6 The Moderator's machine-parsed contract is not benchmarked — the finding

**STATUS: VIOLATED against the guide's own mandate ("under the exact chair contract")**

**LOCATION:** `bot_benchmark.RUBRIC["moderator"]:216`; `BENCHMARK_BATTERY["moderator"]:134`;
`llm_engine.MODERATOR_SYSTEM_PROMPT:151-186`; `app.process_moderator_output:816`.

**EVIDENCE.** The Moderator is the only Prytaneum chair whose output is consumed **by machine**
rather than only read. Its system prompt — the exact one the benchmark runs models under —
requires the response to *"end with this exact structured block — one field per line, using
these exact labels"*, and four production consumers depend on it. Measured:

| check | result |
|---|---|
| block demanded by the system prompt the benchmark uses | **yes** |
| any moderator battery prompt asking for it | **no** |
| any moderator rubric dimension mentioning format / structure / block / field / label / parse | **no** |
| any moderator rubric dimension about accuracy or factual grounding | **no** — dimensions are `synthesis`, `disagreement_handling`, `clarity`, `actionability` (quant and beat both *do* have `accuracy`) |
| `bot_benchmark` referencing any production parser | **no** — none of the four appears anywhere in the module |

A fluent, on-topic Moderator answer that simply omits the block was run through the real
production parsers:

```
parse_moderator_verdict   -> {}
parse_todo_directives     -> {"updates": [], "likely_resolved": []}
parse_source_findings     -> []
parse_source_comparisons  -> []
```

and the same answer *with* a block parses correctly (`recommendation: HOLD`,
`conviction: Majority`) — so the gap is in the benchmark, not in a dead parser.

**What that costs in production, traced.** `log_decision` returns early on `if not league_id or
not verdict` → no decision row. No `ACTION ITEM` → `todo_log.add_todo` never called. No
`SOURCE FINDING` → `bot_research` gains nothing, and its `COMPOSITE_SOURCE_WEIGHTS` entry stays
unfed. `format_agent_content` finds no `^RECOMMENDATION:` → the whole reply renders as prose and
the verdict recap card never appears. None of these raises: `result.errors` only collects
responses prefixed `⚠️`, so a well-formed, block-less answer is not an error. **Four systems
degrade silently.**

**Why this is a violation and not a preference.** The benchmark's entire purpose is to decide
which model holds a chair, and the UI puts an *Apply* button under the winner. A model can
therefore top this rubric on all four dimensions and still fail the chair's non-negotiable
machine contract — and the methodology that recommended it would never have looked.

**BOUNDARY:** chair contract → benchmark. **Instructional** — the prompt asks for the block;
nothing in the selection path checks it.

### 5.6a Proposed repair and blast radius — NOT APPLIED

> **Partially repaired retroactively** — see 5.14. The observability half is done: the
> production parser now runs and the result is recorded and surfaced. The *scoring* half
> stays deferred, because gate-versus-flag changes which model wins.

*Repair.* A **deterministic** pre-judge gate, not a rubric dimension — the check needs no model
and no judgement:

```python
if role == "moderator" and not llm_engine.parse_moderator_verdict(response):
    contract_failed = True     # recorded per question, and surfaced like any_failed
```

Better than adding a rubric line, because it uses the production parser itself rather than
asking a judge to eyeball formatting, and because it can gate rather than merely penalise.

*Blast radius.* `bot_benchmark.py` only: one added check in `run_benchmark`, one extra key per
question, one caption in `app.py`. No engine module, no debate path, no valuation reachable.
Existing tests in `test_bot_benchmark.py` construct reports directly and would need the new key.

*Why it is being reported, not applied.* It changes which model a run recommends, which is a
behavior change in a selection tool, and it raises one design question the mandate reserves for
you: whether a contract failure should **zero** the candidate (disqualification) or merely flag
it (`any_failed`-style). Those give different winners. **DEFER, pending a scoped mandate.**

### 5.7 Per-chair evaluation dimensions against §5's own list

**STATUS: PARTIAL.** §5 names the dimensions each chair should be evaluated on. Mapping the
battery and rubric onto that list — this is my reading of scenario intent against §5's wording,
not a measurement, and is offered as such:

| chair | §5's dimensions | covered | not covered |
|---|---|---|---|
| Beat | discovery, source filtering, freshness, relevance, contradiction detection, actionable extraction | 4 | **discovery, freshness** — every scenario is self-contained, so no lookup is required and no dated source appears |
| Quant | numerical retrieval, projection/ranking verification, arithmetic fidelity, source quality, conflicting numbers | 1 (arithmetic fidelity, via `accuracy`) | **retrieval, verification, source quality, conflicting numbers** — every figure is handed to the model in the prompt, and no scenario presents two sources that disagree |
| Contrarian | meaningful challenge, falsification, evidence quality, resistance to consensus pressure, rejecting insufficient evidence | 2 | **consensus pressure** (all three scenarios present one colleague's claim, never a unanimous panel), **evidence quality**, **rejecting insufficient evidence** |
| Moderator | adjudication, uncertainty handling, role discipline, synthesis, factual grounding, stand-alone answer | 3 | **role discipline** (5.6), **factual grounding** (no accuracy dimension exists) |

The Quant row is the one worth pausing on: production Quant's stated core job is to *"weigh two
independent quantitative sources against each other"* and *"note where they agree or diverge"* —
and no battery scenario gives it two sources. **Verdict: DOCUMENT.** Extending the battery is
cheap and low-risk, but it is battery design work, not a defect repair, and it should be done
once rather than piecemeal.

### 5.8 Score normalization across models

**STATUS: PARTIAL — one axis is normalized well, four are not measured**
**EVIDENCE:** output style is normalized by construction (identical inputs, one rubric, blind
judge). Latency is recorded per question and averaged, but **never enters the ranking** —
`results.sort(key=lambda r: r["score"])`. Cost is **absent entirely**: no token count, no price
field anywhere in the module or the report (grep across the tree returns no pricing model).
Context capacity is untested (5.5). Tool capability is deliberately equalized (5.9).
So §5's *"can routing deterministically combine capability, reliability, context capacity,
latency, tool performance, and cost?"* → **capability yes, reliability partly (`any_failed`),
the rest no.** *"How do pricing changes affect routing?"* → they cannot; price is not an input.

### 5.9 Reasoning ability vs tool-use ability

**STATUS: MISSING — and this corrects a hypothesis of mine, see 5.12**
**EVIDENCE:** all three provider callers grant live web search **unconditionally** —
`web_search_20260209` (Claude), Google Search grounding (Gemini), `web_search` (OpenAI) — with no
role parameter to branch on. `run_benchmark` calls those same callers, so the battery runs
*with* tools. The grant is uniform: the Quant holds live search while its prompt says *"do not
go fetch outside market consensus yourself — that is other analysts' jobs,"* and the Beat holds
it while its prompt says *"Use live search whenever it would sharpen the answer."*
Consequently the evaluation cannot separate the two abilities: every chair has the same grant,
no scenario requires a lookup, and no scenario forbids one. A Beat model that never searches and
a Quant model that always does are both scored purely on prose.
**BOUNDARY:** tool grant → chair. **Absent** (uniform), with the prohibition **instructional** —
the §4.2 finding one level deeper, at capability rather than prose.
**Note in fairness:** the uniformity is deliberate and documented, and it is a *good* answer to
§5's normalization question — *"which provider ends up on the Beat Tracker/Contrarian role is
purely a 'whose answers do you like' choice now, not a capability tradeoff."* It normalizes
capability at the cost of being unable to measure it.

### 5.10 Detecting degradation of an existing model

> **Repaired retroactively** — see 5.14. Reports now keep a capped history, together with
> the fingerprints that make a trend across them honest.

**STATUS: MISSING**
**EVIDENCE:** `save_report` does `all_reports[role] = report` — one report per role, overwritten
on every run. There is no history, so there is no time series, so a model that has got *worse*
cannot be distinguished from one that was always this good. §5 asks for exactly this
("not just superiority of a new model"), and the answer is no.
**Pinned** by `test_saving_a_report_replaces_rather_than_appends`.
**Verdict: DOCUMENT.** Append-with-history is a small change, but it is only worth making
together with 5.11's versioning — a time series of scores against silently-changing batteries
and prompts would be a *misleading* trend, which is worse than none.

### 5.11 Versioning and replay of benchmark results

> **Repaired retroactively** — see 5.14. A report now records the battery, rubric and
> chair-prompt it ran under.

**STATUS: MISSING**
**EVIDENCE:** the report's keys are exactly `{role, ran_at, judge_provider, judge_model,
candidates}` — measured by running a real report through a stubbed caller. It records **no**
battery version, rubric version, chair-contract version, or copy of the system prompt used;
`run_benchmark` reads `llm_engine.ROLE_SYSTEM_PROMPTS[role]` live. Edit a chair prompt or a
rubric weight and every stored report silently becomes incomparable, with nothing in the record
saying so. §5's *"can benchmark results be replayed from fixed inputs, evidence, tool results,
and grading criteria?"* → **no**: the inputs and grading criteria live in code that moves under
the results. Live web search compounds it — two runs of the same battery are not the same
experiment.
This is §4.5 (no `CONTRACT_VERSION` anywhere in the tree) arriving where it actually bites.
Cross-referenced to **#93**, which stays queued.
**Pinned** by `test_the_report_shape_is_pinned_so_absent_fields_stay_visible`, which fails if a
version or cost field is added — so the absence is now a stated fact rather than an assumption.

### 5.12 Model pinning, fallback, and a correction to my own hypothesis

**STATUS: PARTIAL**
**EVIDENCE:** what actually answered is recorded — `append_message` stamps `provider` and
`model` on every persisted message, deliberately, so a later reassignment does not rewrite
history. But the *defaults* are aliases, not pins: `CLAUDE_MODEL = os.getenv("ANTHROPIC_MODEL",
"claude-sonnet-5")`, whose own comment reads *"was a now-retired dated snapshot."* An alias can
change what runs with no diff. And `PickDebateResult` records `role_providers` but **not**
`role_models` (§4), so the Draft Room's three chairs record no model at all.
**Fallback hierarchy: absent.** A failed provider returns a `⚠️` string that is surfaced and
logged; there is no deterministic fall-through to a second provider, in either debate system.

**Correction — a hypothesis of mine that was wrong.** Reading the self-contained battery
scenarios, I formed the view that the benchmark ran with tools disabled while production Beat
had live search, and was about to report that mismatch. It is false: `PROVIDER_CALLERS` grants
search to all three providers unconditionally and the benchmark uses those same callers, so
tools are enabled in both. The real finding is the opposite shape — the grant is uniform across
*chairs*, including one told not to fetch (5.9). Recorded because the wrong version was a
plausible, tidy finding, and the difference was one file read.

**A third substring artifact, recorded.** Checking whether the tool grant was role-conditional,
a naive `"role" in source` returned `True` — matching `messages=[{"role": "user", …}]` and a
comment. Verified properly (no role parameter exists on any caller; the grant is a literal in
the request). Same artifact class as D's `candidate.bpa`/`bpa_source` and Pass 2's
`team_label`/`surface`. Three passes, three occurrences: the lesson is holding.

### 5.13 Downstream-awareness — the chain is never run

**STATUS: MISSING**
**EVIDENCE:** the battery scores each chair **in isolation** against fixed inputs. The
Contrarian's scenarios present a single hand-written colleague's claim; the Moderator's present
three hand-written analyst reports labelled QUANT / BEAT / CONTRARIAN. Those synthetic reports
are what make results comparable and stable rerun-to-rerun — the module says so — and they are
exactly what makes the evaluation downstream-blind. No test anywhere takes model A's *actual*
Beat output into model B's Contrarian.
§5's *"does an optimizer risk selecting a model that scores highly in isolation but degrades
downstream chairs when its output is consumed by another role?"* → **yes, structurally.** A Beat
model that writes beautiful discursive prose may score well and still give the Contrarian a
worse handle than a terser one would. Nothing measures that, and 4.4's absent per-chair evidence
schema is why nothing easily could.
**Verdict: DOCUMENT**, and it is the section's deepest gap. The guide's mandate names
downstream-awareness explicitly, and it is the one word of the five the implementation does not
answer at all. Prerequisite is #93's evidence schema, which stays queued.

---

## Pass 3 summary

| item | status | boundary kind |
|---|---|---|
| 5.1 role-specific empirical methodology exists | EXISTS | structural |
| 5.2 unknown-model evaluation without intervention | EXISTS (selection stays human, by design) | structural |
| **5.3 blind judging** | **EXISTS → ENFORCED (new)** | **enforced** |
| 5.4 chair coverage | PARTIAL — 4 of 7 | pinned |
| 5.5 operating envelope (contract exact, context schema not) | PARTIAL | structural / absent |
| **5.6 Moderator's machine contract not benchmarked** | **VIOLATED → PARTIAL** (measured, not scored — 5.14 R5) | **instructional → enforced (observation only)** |
| 5.6a scoring half (gate vs flag) | still DEFERRED — a selection decision (#94) | — |
| 5.7 per-chair dimension coverage | PARTIAL (Quant 1 of 5) | — |
| 5.8 score normalization (latency unscored, cost absent) | PARTIAL | absent |
| 5.9 reasoning vs tool-use separation | MISSING (uniform grant) | instructional |
| 5.10 degradation detection | **MISSING → EXISTS** (capped history — 5.14 R4) | enforced |
| 5.11 versioning / replay of results | **MISSING → EXISTS** (three run fingerprints — 5.14 R3) | enforced |
| 5.12 pinning and fallback | PARTIAL (recorded, not pinned; no fallback) | structural / absent |
| 5.13 downstream-awareness / full chain | MISSING | absent |

Against the mandate's five words, **as repaired**: **role-specific ✓, empirical ✓, repeatable ✓**
(5.14 R3+R4), **versioned ✓** (5.14 R3), **downstream-aware ✗** (5.13, blocked on #93). At audit
time three of the five were absent; the two that were fixable without a decision have been fixed.

### Does anything clear the bar for a production change?

**One item: 5.6.** It is a proven mismatch between a chair's non-negotiable machine contract and
the methodology that selects who holds that chair, verified end-to-end through the real
production parsers, with the downstream cost traced to four named consumers. The repair is
deterministic, uses the production parser rather than a judge's opinion, and touches one module.

It is **deferred** rather than applied because it changes which model a run recommends — a
behavior change in a selection tool — and because gate-versus-flag is a design decision that
produces different winners and is yours to make. This is the same posture as §3.3: evidence
complete, blocked on a decision rather than on measurement.

Nothing else clears the bar. 5.10 and 5.11 are genuinely small changes that should be made
*together* or not at all, since a score history against silently-changing batteries would be
actively misleading. 5.4, 5.5 and 5.13 all have the same prerequisite — a realistic fixture
(#88, externally blocked) or an evidence schema (#93, queued) — and building any of them now
would mean designing against assumed inputs, which this programme has already declined to do.

### 5.14 Repairs applied retroactively at the §6 boundary

When the standing rule changed to "implement a section's safe, mechanical findings before
advancing," the already-audited sections were re-triaged against it. Two §5 items qualified;
the rest were left, and why is stated below.

**R3 — a benchmark report now records what it was conducted under (§5.11).** Each report carries
`battery_fingerprint`, `rubric_fingerprint` and `chair_prompt_fingerprint` — 12-char content
hashes computed at run time. Deliberately hashes rather than hand-maintained version numbers: a
number has to be remembered and drifts out of sync with the thing it names, while a content hash
cannot disagree with the battery, rubric or prompt it was computed from. This is the difference
between a stored score and a comparable one.

**R4 — `save_report` keeps a capped history instead of overwriting (§5.10).** `HISTORY_LIMIT = 20`
runs per role, newest first, adopting a pre-history store's single report rather than dropping it.
`load_report` still returns the newest, so every existing reader is untouched. `load_history` and
`comparable_history` are new accessors; the latter returns only runs sharing the newest run's
three fingerprints, which is what turns "has this model degraded?" from a trend line across three
different experiments into a real question. **R3 and R4 were done together deliberately** — the
audit's own conclusion was that history over silently-changing batteries is *worse* than none.

**R5 — the Moderator's machine contract is now measured, and still not scored (§5.6, half).**
`run_benchmark` records `contract_ok` per question via `MACHINE_CONTRACT_PARSERS` — the real
production `parse_moderator_verdict`, not a judge's opinion of formatting — plus
`any_contract_failure` per candidate, surfaced in the benchmark UI beside the existing
`any_failed` warning. `None` where a chair has no machine contract, and `None` on a failed call
so a provider error is not double-counted as a contract failure.
**The score is untouched**, and a test pins that a block-less answer and a block-carrying answer
with identical rubric scores rank identically. Gate-versus-flag remains #94's open decision.

**Left alone, and why.** #91 (§3.3) is blocked on the attachment-lifetime rule; #92 (§3.6/3.9)
would add a snapshot identifier ahead of the record that consumes it, contradicting this
programme's own standing rule; #93's per-chair evidence schema is architectural; #96's battery
extension is authoring evaluation content, which is a judgement about what a chair should be good
at. Each is a decision, not a fix.

*Verification:* four non-vacuity probes, each planted in real code and reverted — making
`contract_ok` feed the score, reverting history to overwrite, freezing the battery fingerprint,
and returning `False` instead of `None` for a chair with no machine contract. All four failed the
suite.

### Follow-ups from this pass, ranked by evidence then severity

1. **5.6 — the scoring half only.** The measurement is now in place (5.14 R5); what remains is
   the one decision: does a contract failure zero the candidate or merely flag it? Different
   winners. (#94)
2. ~~5.10 + 5.11~~ — **done** (5.14 R3+R4).
3. **5.7 — extend the Quant battery to include conflicting sources.** The cheapest real coverage
   gain in the pass; production Quant's core stated job is currently untested.
4. **5.13 — chain-level evaluation.** The deepest gap, and correctly blocked behind #93.
5. **5.4 — a Draft Room battery.** Blocked behind #88's fixture; named so it is not forgotten.

---

## Pass 4 — §6

**Scope:** Build Guide v2 §6 (external research, evidence, canonical ingestion).

**Baseline:** `f20da9d` on `ui-authority-pass`; `main` frozen at `9fb5102`. No production file
was modified. #91–96 remain queued/deferred and were not advanced.

**Reach, established first, because it bounds every severity below.** The two research stores —
`data/baseline/bot_research.json` and `bot_comparisons.json` — **do not exist**, are not in
`git ls-files`, and are not gitignored. `load_bot_research_as_external()` returns 0 rows. Nothing
has ever been ingested through this pathway in this repository. Every finding in this pass is
therefore **latent**: the machinery is built, considered, and unexercised.

### 6.1 Is ephemeral research distinguished from canonical ingestion?

**STATUS: EXISTS — and the boundary is layered, not binary, which is the right shape**

**LOCATION:** `bot_research.py`; `data_merger.load_bot_research_as_external:1576`,
`_EXTERNAL_PERCENTILE_RULES:141`, `COMPOSITE_SOURCE_WEIGHTS:104`; `app.process_moderator_output:816`.

**EVIDENCE — four tiers, each with a different admission rule:**

| tier | what reaches it | admission rule |
|---|---|---|
| debate prose | news, injuries, narrative | *"not news/injury, which belongs in your prose, not here"* — an explicit ephemeral carve-out in the Moderator's own instructions |
| research log | any panel-vetted named-source claim | the Moderator emits a `SOURCE FINDING` / `SOURCE COMPARISON` line |
| composite score | **only** findings carrying a number the source itself stated | `rank is not None`, plus a percentile rule keyed `("bot_research", "findings")` |
| CDME valuation | **nothing** | `source_name == "keeptradecut"` whitelist at `draft_room:518` / `pick_synthesis:413`, enforced by `test_cdme_ingestion_boundary.py` |

Comparisons are a deliberately separate store that never reaches the composite at all —
`composite_impact` is the literal string `"none"`, *"an explicit stored fact rather than a silent
omission"*, with the reasoning recorded: a handful of debate-surfaced comparisons is nowhere near
KTC's vote volume, and a Bradley-Terry model on that sample *"would produce noise dressed up as
precision."* That is the guide's question answered before it was asked.
**BOUNDARY:** research → canonical. **Structural at the CDME edge, enforced at the composite edge**
(new tests this pass), **instructional at the log edge** (6.2).

### 6.2 How materiality is determined

**STATUS: PARTIAL — well defined, entirely instructional**
**EVIDENCE:** `MODERATOR_SYSTEM_PROMPT:202-218` states three filters and one exclusion, all in
prose: the claim must be *"specific, checkable … from a named real source about a named player's
current market value, ranking, or status"*; news and injury are excluded by name; the panel —
*"Contrarian very much included"* — must not have disputed it; and *"if the Contrarian challenged
it and nothing rebutted that challenge, don't write the line at all — an unresolved dispute is not
a finding."*
Nothing re-adjudicates. `app.py:836` says so plainly: *"persisting every parsed line here is
trusting the Moderator's own gate, not re-verifying it a second time in code — the actual trust
bar is upstream, in the debate itself."* §6 asks whether discoveries *"enter a server-side
validation queue that independently re-adjudicates facts before canonical inclusion"* — **no.
There is no queue and no second adjudication.** The gate is one paragraph addressed to a model
whose output is then parsed line-by-line.
**RISK:** bounded by 6.4's dampeners rather than by the gate.

### 6.3 What stops a low-confidence finding becoming a durable fact — quantified

**STATUS: EXISTS — three dampeners, and their strength is measurable**

Weight = `COMPOSITE_SOURCE_WEIGHTS[source] × recency × min(1, pool/20)`, and the composite is
`Σ(percentile × weight) / Σweight`, so what matters is *share*. Measured against the real
committed tables (only `(source, file)` pairs carrying a percentile rule contribute):

| contributing source | as-of | rows | w_src | recency | effective |
|---|---|---|---|---|---|
| draftsharks / projections | 2026-08-25 | 764 | 1.30 | 0.933 | **1.213** |
| fantasypros / dynasty_ppr_rankings.csv | 2026-08-20 | 552 | 1.00 | 0.881 | 0.881 |
| dynastyprocess / players.csv | 2026-08-14 | 698 | 1.00 | 0.822 | 0.822 |
| keeptradecut / dynasty_superflex_halfppr.csv | 2026-08-20 | 499 | 0.70 | 0.881 | 0.616 |
| *(loaded but excluded — no percentile rule)* | | | | | `espn/idp_redraft_rankings.csv`, `fantasypros/best_ball_rankings.csv`, `fantasypros/idp_redraft_rankings.csv`, `dynastyprocess/picks.csv` |

Total contributing weight **3.532**. A finding written today:

| finding pool | effective weight | share of the blend |
|---|---|---|
| N = 1 | 0.025 | **0.7%** |
| N = 10 | 0.250 | 6.6% |
| N ≥ 20 | 0.500 | **12.4%** |

**The number that does not depend on today's snapshot.** A finding is always dated the day it is
written, so its recency weight is permanently 1.0; a committed vendor file ages. Days of vendor
staleness before a fresh panel finding outweighs it (`halflife × log₂(w_src / 0.5)`):

| source | days |
|---|---|
| keeptradecut | **29.1** |
| dynastyprocess, fantasypros | 60.0 |
| draftsharks | 82.7 |

So the ordering guarantee "a parsed vendor always outranks an LLM's read" holds **only at equal
freshness**. On a baseline left un-refreshed for a month, a panel finding outweighs KeepTradeCut.
That is arguably correct behaviour — a fresh read *should* beat a stale file, and it is the same
rule every source obeys — but it is a consequence of the weighting rather than a stated intent,
and it is worth naming.
**Verdict: DOCUMENT.** The dampeners work, and the crossover is now recorded rather than implicit.
Enforced this pass: research carries the lowest source weight of any source, the pool floor is
pinned, and an undated source gets 0.5 rather than full trust.

### 6.4 The research frame is not name-injective — KNOWN GAP

**STATUS: PARTIAL (latent) — characterized, not repaired**

**EVIDENCE.** `load_bot_research_as_external` keys `latest` by **(normalized name, cited source)**,
so two findings about one player citing two different sources survive as two rows sharing a
normalized name. Measured with a temporary store holding contradictory findings (ESPN `rank 3`,
FantasyPros `rank 41` for the same player):

```
rows produced                 : 2
norm_name unique              : False
percentiles assigned          : [100.0, 50.0]
_resolve(...)                 : candidates=2, verified=False
_find_match(...) resolves to  : rank 3.0 / ESPN
composite components          : 1   (raw=3.0, pct=100.0, weight=0.0494)
```

The columns the frame emits are `name, norm_name, source_name, source_file, cited_source, claim,
rank, source_date` — **no team, no position.** Passing `position=` and `team=` changes nothing;
all four call shapes resolve to the same arbitrary row. `_compute_percentiles` *does* segment the
research pool by offence/IDP group, but looks that group up externally and never stores it, so it
is available for pooling and not for disambiguation.

Note precisely what is and is not broken: `_resolve` **correctly reports `verified=False`** — the
identity boundary R1–R3 and #89 built is intact and reporting honestly. `composite_player_score`
reaches it through `_find_match`, which is `_resolve(...)[0]`: the row, with the flag discarded.
The newer finding also loses to the older one, because "newest wins" holds *within* a
(player, cited source) key and not across cited sources — which a reader of the docstring's
unqualified *"newest wins"* would not expect.

**Severity, bounded honestly:** store empty (0 findings ever); requires two findings on one player
citing different sources; the losing component is worth at most 12.4% of one player's composite,
and the composite *"does not feed the trade calculator's pricing math"* and never reaches CDME.
**Verdict: DOCUMENT**, pinned by characterization tests that must be inverted when repaired.

### 6.4a A correction — the general version of this finding is wrong

I first framed this as *"`composite_player_score` discards the ambiguity flag, so 19 of 19
colliding names in the committed `projections` table price off an arbitrary row."* The
measurement was right and the conclusion was wrong, because both production call sites already
guard it:

- `data_merger.py:2284` (the roster/board path feeding `build_context`) passes `position=` and
  `team=`, which disambiguates the vendor tables — the frames that *have* those columns.
- `app.py:3548` (Trade Calculator free text) does not, but the block immediately after it drops
  `external` and `composite` outright when `merge_player` reports `match_verified == False`, with
  a comment recording the exact reasoning: *"an ambiguous line still had a specific player's real
  composite score reach the panel's context, undermining the point of flagging it as ambiguous at
  all."*

And of the 19 colliding names, only **4** differ materially on the composite-relevant field —
all four cross-position collisions the roster path resolves by position (`J Jefferson` LB/CLE
trade_value 0.0 vs WR/MIN 82.0; `J Bates` 5 vs 14; `J Brooks` 20 vs 27; `B Young` 13 vs 18).
The surviving finding is narrower and real: **the `bot_research` frame specifically cannot be
disambiguated by either guard**, because it carries no team or position and the Trade Calculator's
guard reads a different table. Recorded because the broad version was a plausible, tidy finding
that two call-site reads disproved.

### 6.5 Lifecycle, evidence snapshot, and the `validated` flag

> **Repaired at this section's boundary** — see 6.9. The flag is now `panel_undisputed`. The
> paragraphs below record the state at audit time.

**STATUS: MISSING**
**EVIDENCE:** §6 asks for `discovered → corroborated → disputed → adjudicated →
canonical/rejected/expired`. A stored finding's fields are `id, ts, date, player_name, source,
claim, rank, composite_impact, conviction, question, league_id`. `composite_impact` is a
**routing label** (`"low-weight input"` / `"none"`), not a lifecycle state. There is no status,
no corroboration count, no dispute state, no retraction, and no expiry — grep across the tree
finds no such mechanism anywhere.
**Evidence snapshot: absent.** No `url`, no `retrieved_at`, no quoted excerpt. The preserved
evidence is a source *name* and the Moderator's own one-line paraphrase. §6's *"what happens when
a source changes or disappears after a review event is created?"* → the claim persists,
unfalsifiable and uncheckable, and continues to carry composite weight.

**The `validated` flag, and why it is DOCUMENT rather than a defect.** Every comparison is written
with `"validated": True`, hard-coded, commented *"only ever created after clearing the Moderator's
panel-scrutiny gate."* The writing path cannot establish that — the gate is a model choosing to
emit a line. The **shape** is identical to §13.3's alias `verified=True`: a certainty claim the
code cannot verify. The **difference**, and the whole reason this is not a repair, is that
**nothing in production reads it** — `grep` finds one write and one test assertion, and no
consumer. §13.3's flag was consumed and changed a price; this one is inert.
Pinned both ways: a test asserts the flag is written unconditionally, and a second fails if
anything ever starts reading it — at which point it has to become honest before it can be trusted.

### 6.6 Deduplication, reuse, and contradiction handling

**STATUS: PARTIAL**
- **Dedup: exists, narrowly.** `add_finding` and `add_comparison` both no-op on an exact
  same-day duplicate `(date, player, source, claim, rank)`, deliberately scoped to one day so a
  genuine re-confirmation weeks later still renews its own recency weight. Cross-day
  near-duplicates and paraphrase variants are not detected. §6's *"the same underlying fact
  discovered by multiple runs deduplicated into one review event"* → there is no *review event*
  concept at all, so dedup is row-level rather than fact-level.
- **Reuse: EXISTS.** `findings_for_context(limit=30)` and `comparisons_for_context(limit=30)`
  feed every subsequent `build_context`, so a finding is paid for once and reused thereafter —
  a direct affirmative answer to §6's cost question.
- **Contradiction vs interpretation: PARTIAL.** The numeric/qualitative split is real (a rank is
  stored *"ONLY if the claim IS literally that specific number"*), and comparisons carry a genuine
  third state `~` for *"the source treats them as roughly equal"* rather than forcing a
  direction. But there is no representation for *two findings that disagree*: within one cited
  source the newer silently supersedes, and across cited sources one silently wins (6.4). A
  disagreement is never stored as a disagreement.

### 6.7 Communicating staleness, and separating established from new

**STATUS: EXISTS — the best-handled part of §6**
**EVIDENCE:** `build_freshness_manifest` gives every dated source an as-of date and an age, sorted
freshest-first, with STALE (≥7d) and EGREGIOUSLY OUTDATED (≥30d) flags and an instruction to *"say
so plainly in your answer, don't use quietly."* Every chair prompt is told to weigh freshness by
claim type — decisively for injury/depth-chart signals, mildly for long-horizon valuations.
Past findings are re-presented to the panel under their own heading, dated, with an explicit
**double-counting warning**: *"The ones with a rank number already feed the composite score above
at a low weight … don't double-count them by also treating this prose as independent
corroboration."* Comparisons get their own heading stating they carry **no** composite weight and
are *"useful as a cross-check on ordering … not a competing number."*
That is §6's *"can Moderator explicitly separate established CDME context from credible new
evidence"* answered affirmatively, and it is answered more carefully than the question asks.

### 6.8 Cross-user sharing

**STATUS: NOT APPLICABLE as deployed**
**EVIDENCE:** single-user desktop Streamlit with no auth and no tenancy (§13.5). Both stores are
global rather than per-league, and `league_id` is recorded on every entry but never filtered on at
read time — so a finding surfaced in one league is reused in all of them. That is a *within-user*
cross-league reuse decision, not a cross-user one. §6's sharing and privacy questions become live
only under 13.5's hosting preconditions, and are queued there rather than answered here.

---

## Pass 4 summary

| item | status | boundary kind |
|---|---|---|
| 6.0 reach — anything ever ingested | **none — 0 findings, stores absent** | — |
| 6.1 ephemeral vs canonical, four tiers | EXISTS | structural + enforced (new) |
| 6.2 materiality determination | PARTIAL | **instructional** |
| 6.2a independent re-adjudication queue | MISSING | absent |
| 6.3 dampeners on low-confidence findings | EXISTS (quantified) | enforced (new) |
| **6.4 research frame not name-injective** | **PARTIAL (latent)** | characterized |
| 6.4a correction — the general version is wrong | — | — |
| 6.5 lifecycle / evidence snapshot | MISSING | absent |
| 6.5a `validated` written unconditionally, read by nothing | DOCUMENT | characterized |
| 6.6 dedup (same-day, row-level) | PARTIAL | enforced |
| 6.6a reuse across future operations | EXISTS | structural |
| 6.6b contradiction vs interpretation | PARTIAL | — |
| 6.7 staleness + established-vs-new separation | EXISTS | instructional, well-specified |
| 6.8 cross-user sharing | NOT APPLICABLE (queued behind 13.5) | — |

### Does anything clear the bar for a production change?

**No — and this is the first pass where nothing does.** 6.4 is a genuine latent defect with a
proven mechanism, but three things keep it below the bar: the store has never held a row, it
requires two findings on one player citing different sources, and the worst case is one arbitrary
component worth ≤12.4% of one player's composite, on a score that reaches neither the trade
calculator's pricing math nor CDME. Repairing it now would mean designing an admission and
conflict-representation scheme against zero observed data — the same error this programme
declined in #88 and #85.

The right response was to **pin the guarantees and characterize the gaps**, which this pass did
without touching production: the dampeners, the qualitative/numeric split, comparisons' exclusion,
and same-day dedup are now enforced, and the non-injective frame, the missing lifecycle, and the
inert `validated` flag are characterized with tests that must be inverted rather than deleted
when repaired.

### 6.9 Repairs applied at this section boundary

Under the standing rule that a section's safe, mechanical findings are implemented before the
next section begins, two were applied. Neither changes any computed value; both correct a
statement the code was making.

**R1 — `add_comparison` no longer claims a verification it cannot perform.**
`"validated": True` was hard-coded on every write, attributed by comment to the Moderator's
panel-scrutiny gate. That gate is a model choosing to emit a line; this code neither observes the
debate nor re-adjudicates the claim, so the field asserted something its writing path cannot
establish — the same shape #89 repaired in the alias branch, under a rule that applies directly:
*a stored field may not claim a certainty its writer cannot verify.* Renamed to
**`panel_undisputed`**, which is exactly what is known, with the reasoning recorded in place. The
information is unchanged; only the claim is corrected. Applied rather than surfaced because it is
the established #89 rule with no new decision in it, and because the store is empty and the field
has no production consumer, so the blast radius is the field name itself.
*Verification:* reverting the rename fails 2 tests; adding a function that reads the new flag
fails the guard that keeps it a provenance record rather than an input.

**R2 — `load_bot_research_as_external`'s docstring no longer says "newest wins" unqualified.**
The rule is per **(player, cited source)** key, not per player, and that difference is the whole
of 6.4: two sources speaking about one player are two keys, both rows survive, and the *older*
one wins the composite component. The docstring now states that, names the non-injectivity,
records that `_resolve` reports the collision correctly while `_find_match` drops the flag, and
points at both the characterization test and 6.4. Documentation only.

**Deliberately not applied, and why.** 6.4's actual repair (representing a disagreement instead of
silently picking one), 6.5's evidence snapshot (needs the Moderator's contract to emit a URL — a
chair-contract change), 6.2a's re-adjudication queue, and 6.3's crossover intent each require a
new product, architectural, or policy decision, so they are surfaced rather than chosen.

*Post-repair state:* composite for a known player unchanged at 99.9; 764 projection rows; research
frame still 0 rows.

### Follow-ups from this pass, ranked by evidence then severity

1. **6.4 + 6.5 together — a finding's identity and its lifecycle.** The frame needs a key that
   can represent "two sources disagree about this player" rather than dropping one, and a finding
   needs somewhere to record corroboration, dispute, and retraction. Same design; doing either
   alone would need redoing. **Prerequisite: real findings.** Not worth designing against an empty
   store.
2. **6.5 — evidence snapshot (URL + retrieved-at + excerpt).** Cheap, additive, and independently
   useful: it makes a stored claim checkable later, which is what §6 is actually protecting.
   The only item here that could sensibly be done before any data exists.
3. **6.2a — an independent re-adjudication step.** The largest conceptual gap, and the one that
   most depends on scale: with one user and a low weight, the Moderator's own gate is a
   defensible trust bar. It stops being one under 13.5's hosting model.
4. **6.3 — decide whether the fresh-finding-beats-stale-vendor crossover is intended.** Now
   measured (29–83 days); it needs a stated intent, not a change.

---

## Pass 5 — §7

**Scope:** Build Guide v2 §7 (source legality, credibility, provenance, prompt-injection
boundary), whose mandate is that *"research may inform adjudication; research does not acquire
authority merely by being retrieved."*

**Baseline:** `4aab2cd` on `ui-authority-pass`; `main` frozen at `9fb5102`. Repairs applied at
this section's boundary are in 7.9. #91–94, #96, #97 remain queued and were not advanced.

### 7.1 Source legality and the product source policy

**STATUS: EXISTS — better than expected, and the mechanism is unusual enough to name**

**LOCATION:** `data/baseline/external/{dynastyprocess,espn,fantasypros,keeptradecut}/ATTRIBUTION.md`.

**EVIDENCE:** each of the four external sources carries a written record of what was taken, how,
when, and under what access posture — and they are not boilerplate. DynastyProcess is recorded as
GPL-3.0 open data pulled from a *"public, unauthenticated, no-login endpoint the repository itself
describes as 'open-data'"*, and is committed as-is **because** of that. FantasyPros and
KeepTradeCut are recorded as sitting *"behind normal site access rather than an open-data
license"*, with a single stated policy applied to both: *"facts-only extraction (rank/name/asset
type/position/tier/value/trend), never the site's own page/branding, attributed here rather than
re-litigating the question each time a new vendor comes up."* KTC's own API is recorded as
**blocked and not circumvented** (`CONNECT tunnel failed, 403`). ESPN is recorded as public
content with the same facts-only posture applied *"for consistency"* even where not required.

That is a real product source policy: stated once, applied per source, with the reasoning kept.
**BOUNDARY:** source → ingestion. **Was instructional (four files and nothing requiring them);
now enforced** — see 7.9 R6.

### 7.2 The app has no fetcher of its own

**STATUS: EXISTS — structural, and it decides several §7 questions at once**
**EVIDENCE:** the only literal outbound host anywhere in the production modules is
**`api.sleeper.app`**. There is no `requests`/`httpx`/`urllib` call to any other host, and no URL
fetcher at all. Every piece of live research runs **provider-side** — Anthropic's
`web_search_20260209`, Gemini's Google Search grounding, OpenAI's `web_search` — executed on the
provider's infrastructure, not this app's.
So §7's questions about robots directives, paywalls and authentication boundaries have a
structural answer rather than a policy one: **this app cannot bypass them, because it never
retrieves anything itself.** Those obligations sit with the provider whose tool runs the search.
**Now pinned** by a test that fails when a new outbound host appears.

### 7.3 Source admissibility is enforced independently of model preference

**STATUS: EXISTS — structural**
**EVIDENCE:** which sources may influence a number is decided by `_EXTERNAL_PERCENTILE_RULES`, a
module-level constant bound exactly once and mutated nowhere (verified by AST: one binding at
column 0, zero subscript assignments, zero `update`/`setdefault`/`pop`/`clear` calls). No model
output can add an entry. And every `bot_research` finding, however it is attributed, is filed
under **one synthetic `("bot_research", "findings")` pair** regardless of the source it cites — so
an unvalidated citation can never create a percentile rule of its own.
This is a clean separation of the two things §7 asks to be separated: a chair may *recommend* a
source; only code decides whether it is *permissible*.

### 7.4 But a cited source name is unvalidated free text — KNOWN GAP

**STATUS: PARTIAL (latent)**
**EVIDENCE:** `parse_source_findings` accepts whatever the Moderator writes in the source field.
Measured against the real parser with deliberately impermissible citations:

```
SOURCE FINDING: Some Player | totally-not-a-real-site.example/paywalled | ... | 1
  -> accepted: source='totally-not-a-real-site.example/paywalled', rank=1
SOURCE COMPARISON: ... | an anonymous forum post | ...
  -> accepted: source='an anonymous forum post'
```

No `SOURCE_ALLOWLIST`, `PERMITTED_SOURCES` or `SOURCE_POLICY` exists in either `llm_engine` or
`data_merger`. So §7's *"can a model introduce an impermissible source merely because it appears
authoritative?"* splits cleanly: **into the composite allowlist, no** (7.3); **into the durable
research record, yes** — attributed to any source at all, including a paywalled one the written
policy would not permit, or one that does not exist.
**Reach, unchanged from §6:** the store is empty; a fabricated rank would enter the composite at
`0.5 × recency × pool_factor`, ≤12.4% of one player's blend, and reaches neither trade pricing nor
CDME.
**Verdict: DOCUMENT.** Deciding *which* sources a citation may name is a product source policy
decision — exactly the thing 7.1's ATTRIBUTION files settle for file sources, and exactly the
thing nobody has settled for model-surfaced ones. Surfaced (#98), not chosen.

### 7.5 The prompt-injection boundary — what a retrieved instruction can actually do

**STATUS: PARTIAL — bounded by real code-level limits, none of them designed for this threat**

**The chain.** Untrusted content (a web result, an uploaded attachment, a stored finding, a prior
turn) enters the model's context → the model emits a directive line → a regex parser acts on it.
Nothing prevents the middle step; the boundary is entirely in what the parsers *allow*. Measured
against deliberately hostile Moderator text:

| directive | what it can actually do | reversible | needs a person |
|---|---|---|---|
| `RECOMMENDATION` / `CONVICTION` / … | writes a decision-log row — **strings only**, every field verified `str` | — | no |
| `ACTION ITEM` | creates a new objective | user dismisses | no |
| `TODO UPDATE: <id> \| <text>` | **rewrites an existing objective's text** | **yes — prior text kept in `revisions`** | no |
| `TODO LIKELY RESOLVED: <id>` | sets a **pending** state | — | **yes — `likely_resolved` is an ACTIVE status; only a person resolves** |
| `SOURCE FINDING: … \| <rank>` | **writes an integer into the composite** at weight 0.5 | append-only, newest-wins | no |
| `SOURCE COMPARISON: …` | writes a record, **no composite impact** | append-only | no |

**The numeric surface is two integers wide** — a to-do id and a rank — and both are `.isdigit()`
gated, so `TODO UPDATE: ../../etc | x | y` parses to nothing. An id naming an objective that does
not exist, or one already archived, is a no-op. Nothing a directive carries can become a
coefficient, a schema, or a deterministic parameter.

**The two genuinely load-bearing protections are that a directive proposes rather than decides:**
a rewritten objective keeps what it said before, and a resolution is a request a person confirms.
Both were designed as UX courtesies rather than as injection defences, and both are now pinned by
test, because they are in fact the strongest boundary in this section.

**What is absent:** the phrase "prompt injection" appears nowhere in the tree — the five matches
for "injection" are all about *script* injection in the iframe payload and *context* injection of
pinned messages. The threat model is not addressed anywhere in the app's own reasoning.
**BOUNDARY:** retrieved content → orchestration authority. **Structural where it exists**
(type discipline, `.isdigit()` gating, no-op on unknown ids, revision history, pending states),
**instructional where it does not** (the Moderator's prompt says *"Never invent a source or a
number that wasn't actually surfaced in this debate"*).

### 7.6 Evidence is not structurally distinct from instructions — KNOWN GAP

**STATUS: MISSING**
**EVIDENCE:** `build_context` assembles **one flat string** from 54 `lines.append(...)` calls and
returns `"\n".join(lines)`. There is no `<untrusted>` fence, no delimiter, no marker of any kind.
Into that same channel go, adjacent to the app's own directives:

| untrusted content | how it arrives |
|---|---|
| chat attachments | raw file text, truncated at 4000 chars, unescaped and unfenced |
| reference-material captions | user free text |
| panel-vetted findings and comparisons | prior model output, re-presented as fact |
| conversation memory | prior model prose replayed verbatim |
| past decision outcomes | user-written notes |

§7 asks *"are evidence packages structurally distinct from instructions?"* — **no.** A model has
nothing but content to distinguish "the app is telling me this" from "an uploaded file is saying
this."
**Verdict: DOCUMENT, surfaced (#98).** The repair is not a fence alone: a delimiter the chair
prompts do not explain is decoration. It is a joint change to `build_context` *and* all seven
chair contracts, which is architectural, and it is the same shape as #93's evidence-package work.

### 7.7 Citations through the chair handoff

**STATUS: PARTIAL — and worse than §4.4's general finding**
**EVIDENCE:** §4.4 established that a downstream chair receives its predecessor's prose, not an
evidence package. §7's version is sharper: the **only structured citation record in the system is
created by the Moderator**, downstream of the chair that actually found the source. A citation the
Beat surfaced and the Moderator did not repeat in a `SOURCE FINDING` line **is not retained
anywhere** — it exists only inside Beat's prose in `chat_history`, unattributed and unqueryable.
Provenance is therefore reconstructed by the synthesizer rather than carried by the discoverer.
**DEPENDENCIES:** #93. Same repair, same prerequisite.

### 7.8 Credentials are not input

**STATUS: EXISTS — measured and now enforced**
**EVIDENCE:** a sentinel key was passed through all four production `ask_*` functions with the
provider caller stubbed and the exact prompts captured. The key appears in **neither** the system
prompt nor the user prompt of any chair, and travels only as its own argument. It does not appear
anywhere in a serialized benchmark report. And structurally, none of `bot_research`,
`decision_log`, `todo_log` or `pinned_messages` mentions `api_key` at all — the stores cannot
write what they are never handed.
**Residual, named and not repaired:** the provider callers return `f"⚠️ … failed: {exc}"`, and
that string is persisted to `chat_history` and replayed into the next `build_context` — so it does
reach providers on a later turn. If an SDK ever put credential material in `str(exc)` it would
land in a store and in a prompt. **Not demonstrated**, and under this programme's own standard an
undemonstrated leak does not clear the bar for a production change. Recorded, not fixed.

### 7.9 Repairs applied at this section boundary

Two, both converting an existing and correct policy from convention into enforcement. No
behaviour changed.

**R6 — the source policy is now required, not merely observed.**
`test_research_authority_boundary` asserts that every file-backed source in
`_EXTERNAL_PERCENTILE_RULES` has an `ATTRIBUTION.md`, that the file is substantial and names its
source, and that it states an access/licensing posture (license / open-data / login / paywall /
subscription / public / terms). Adding a source to the composite without that record is now a
test failure. It also pins by AST that the allowlist is bound exactly once at module level and
never mutated, and that every finding files under the one synthetic source pair.

**R7 — the properties that actually bound retrieved content are now pinned.**
Credentials never reach a prompt or a report; verdict fields are all `str`; the numeric surface is
exactly two `.isdigit()`-gated integers; a non-numeric id is dropped rather than coerced; an
unknown id is a no-op; a rewritten objective keeps its prior text; `likely_resolved` stays an
ACTIVE status awaiting a person; and no second outbound host exists.

*Non-vacuity — five probes planted in real code and reverted, all failing:* a composite source
added without an ATTRIBUTION.md, a function that mutates the allowlist at runtime, a key inlined
into the Quant's prompt, a rewrite that stops preserving prior text, and a second outbound host.

**Deliberately not applied.** A cited-source allowlist (7.4) is a product source policy decision.
Fencing untrusted content (7.6) is a joint change to `build_context` and seven chair contracts.
Writing ATTRIBUTION records for the 11 unattributed baseline CSVs (7.10) asserts a licensing
posture for the user's own paid vendor exports, which is not mine to assert. All surfaced (#98).

### 7.10 Provenance coverage across the committed baseline

**STATUS: PARTIAL — and inverted from what one would expect**
**EVIDENCE:** 20 committed baseline CSVs; **9 carry a provenance record, 11 do not.**

| covered | by |
|---|---|
| the four external sources' files | per-source `ATTRIBUTION.md` |
| `sleeper_kicker_projections.csv`, `sleeper_dst_projections.csv` | `sleeper_projection_provenance.json`, which states its own reason: *"committing the points without the rules that generated them would leave the numbers unfalsifiable"* |

| uncovered |
|---|
| all 10 `data/baseline/rankings/*.csv` Draft Sharks exports |
| `data/baseline/trade_value/dynasty_ppr_trade_value_chart.csv` |

The inversion is the finding: the **secondary** sources are documented; the **primary** valuation
input — the highest-weighted source in the composite (1.3) and the one feeding CDME's `bpa` — is
not. Its provenance exists only as prose in `README.md` and, secondhand, in DynastyProcess's
ATTRIBUTION (*"unlike Draft Sharks' subscription exports"*).
**Verdict: DOCUMENT, surfaced.** The gap is real and the record should exist; writing it means
asserting the terms under which a paid subscription export is retained and redistributed, which
is a decision for the owner.

### 7.11 Cross-section finding — this changes #94's premises

**§7 supplies information §5 did not have, and it bears directly on the parked decision.**

#94 asks what a Moderator contract failure should cost: disqualify the candidate, zero the
question, or flag only. §5 framed that purely as a quality question — a model that does not emit
the structured block leaves four consumers doing nothing.

§7 shows the same block is **the entire channel through which model output acquires authority.**
Every path in 7.5's table runs through it: rewriting an objective, proposing a resolution,
writing a rank into the composite, creating a to-do. A Moderator that fails its machine contract
is therefore *inert on every authority path* — the least dangerous Moderator available. A
contract-**compliant** one is the one that can rewrite a user's objectives and inject numbers.

That does not settle #94, and I am not settling it. It adds a consideration that was not on the
table: **option (a), disqualify, selects for models that exercise more authority**, which is a
different trade-off from the "quality only" framing #94 was parked under. Whichever way it goes,
the reasoning should now account for it. Recorded on #94.

---

## Pass 5 summary

| item | status | boundary kind |
|---|---|---|
| 7.1 written per-source policy | EXISTS | **convention → enforced (R6)** |
| 7.2 no fetcher of its own | EXISTS | structural, now pinned |
| 7.3 admissibility is a code allowlist | EXISTS | structural, now pinned |
| **7.4 cited source name unvalidated** | **PARTIAL (latent)** | absent |
| 7.5 injection boundary / directive authority | PARTIAL | structural where present, now pinned |
| **7.6 evidence vs instructions** | **MISSING** | absent |
| 7.7 citations through the handoff | PARTIAL | absent (→ #93) |
| 7.8 credentials are not input | EXISTS | structural, now pinned |
| 7.10 baseline provenance coverage (9 of 20) | PARTIAL | — |
| 7.11 cross-section effect on #94 | — | — |

### Does anything clear the bar for a production change?

**No new defect did.** §7's genuine finding is the opposite of the previous sections': the
protections here are *better than the code claims for itself*. The app has no fetcher, the
composite allowlist is a true constant, a directive's numeric surface is two gated integers wide,
a rewrite is recoverable, a resolution needs a person, and credentials never touch a prompt —
and none of that was written down as an injection boundary or defended by a test. The right
repair was to make those properties enforced rather than incidental, which R6 and R7 did without
changing behaviour.

The two real gaps — an unvalidated citation and an unfenced context — are both decisions, and
both are now with you.

### Follow-ups from this pass, ranked by evidence then severity

1. **7.4 — a source policy for model-surfaced citations.** The file-source policy already exists
   and is written down; extending it to citations is the smaller half of a job already begun.
2. **7.6 + 7.7 + #93 together — fenced, attributed evidence packages.** One design serves all
   three: if evidence is structurally separate, it can carry its own provenance, and a downstream
   chair inherits sources rather than prose.
3. **7.10 — provenance for the Draft Sharks rankings and the trade-value chart.** The record
   should exist; its content is a statement only the owner can make.
4. **7.8 residual — redact credential-shaped strings from provider error text.** Cheap, but
   currently defending an undemonstrated leak; worth doing when something else touches that path.

---

## Pass 6 — §9

**Scope:** Build Guide v2 §9 (context compaction, handoffs, model-specific budgets), whose
mandate is that *"context limits may reduce supporting information, but may not silently alter,
omit, or distort mandatory deterministic state or authoritative evidence required for the chair's
task."*

**Baseline:** `ccd50a2` on `ui-authority-pass`; `main` frozen at `9fb5102`. §8 was not re-audited
— nothing here changed a §8 premise. #91–94, #96–98 remain queued and were not advanced.

**Headline: the mandate holds, and it holds by proportion rather than by design.** There is no
input-token accounting anywhere in the tree. What protects mandatory state is that mandatory
state is *small* — the entire deterministic portion of a chair's context is roughly **8.4k
tokens**, while the worst case is dominated by replayed model prose.

### 9.1 The full context at invocation, and what it is made of

**STATUS: EXISTS (measurable), with one term dominating**

Upper bound per Prytaneum invocation, derived from the caps themselves rather than sampled:

| term | bound | tokens | kind |
|---|---|---|---|
| conversation memory — raw prior turns | 16 × `MAX_TOKENS` | **65,536** | **prose (model output, replayed verbatim)** |
| compacted memory block | 1 × `MAX_TOKENS` | 4,096 | prose (model-summarized) |
| static instruction prose | — | ~2,800 | instructions |
| panel findings + comparisons | 30 + 30 lines | ~2,550 | prior model output as evidence |
| your roster | uncapped, league-bounded | ~900 | **structured, mandatory** |
| league-wide positional depth | uncapped, league-bounded | ~840 | **structured, mandatory** |
| canonical Sleeper pool | 15 rows | ~375 | structured |
| pinned messages | 5 × 400 chars | ~500 | user/model prose |
| archived objectives + past outcomes | 5 + 5 | ~400 | user prose |
| chat attachments | 4,000 chars each, **count uncapped** | unbounded | **untrusted file text** |
| **total excluding attachments** | | **~78,000** | |

**Conversation memory alone is 84% of that bound.** Every deterministic section combined is
**8,365 tokens** — comfortably inside any model in use.
§9's *"structured data versus prose versus tool results versus source evidence"* answers cleanly:
the context is overwhelmingly **prose**, and specifically **this system's own prior output fed
back to itself**. Tool results never appear as a separate category at all — provider-side search
results are folded into a chair's prose before the app ever sees them (§7.2).

### 9.2 Where compaction occurs

**STATUS: EXISTS — one summarizer, ten deterministic caps**

| mechanism | unit | kind |
|---|---|---|
| `llm_engine.MAX_TOKENS = 4096` | **output** tokens, every chair, every provider | hard cap |
| `RECENT_TURNS_IN_CONTEXT = 16` | raw turns replayed | slice |
| `compact_league_history` | messages older than 30 days → one block | **model call** |
| attachment text `[:4000]` | chars per file | slice |
| reference material `captioned[:20]` | captions | slice |
| `findings_for_context` / `comparisons_for_context` | 30 each | slice |
| pinned messages: 5, truncated `[:400]` | chars | slice |
| archived objectives / past outcomes | 5 each | slice |
| `projected_available[:15]` | pool rows | slice |
| `_MAX_CANDIDATES_IN_CONTEXT = 8`, `DEFAULT_NARROW_COUNT = 5` | rows | slice |

**Everything except history summarization is a deterministic slice**, so §9's *"is compaction
deterministic and reproducible?"* is **yes everywhere but one place** — and that one place is a
model call, so it is neither. Pinned: a test now fails if `build_context` ever calls a model to
shape its own context.

### 9.3 Mandatory versus compactable

**STATUS: EXISTS — and the split is the right one**
**EVIDENCE:** verified by AST that each of these is iterated over a plain name, never a
subscript: `roster_table`, `depth.items()`, `freshness`, `active_todos`. Plus
`format_scoring_settings` emits the league's real per-category weights in full.
So the things a chair cannot do its job without — the roster, the scoring rules, how stale each
source is, what the user is already trying to do — are **never** truncated. Everything capped is
supporting information: how many candidates to show, how many past findings to recall, how much
of a pinned message to quote.
**BOUNDARY:** budget → mandatory state. **Now enforced** (9.7 R8), where before it was an
emergent property of nobody having added a cap.

### 9.4 Compaction is non-destructive

**STATUS: EXISTS — and this corrects a hypothesis of mine, see 9.8**
**EVIDENCE:** `compact_league_history` writes
`{league_id}_history.pre_compact_{timestamp}.json` containing the **full pre-compaction
history**, and does so *before* `save_chat_history` overwrites anything. It aborts entirely —
*"Compaction aborted, history untouched"* — if the summarizer returns a `⚠️`, which it does
rather than raising. A prior summary is merged forward rather than discarded.
So §9's *"is the original uncompacted context preserved for audit/replay?"* is **yes**, which is
notable because §3.6 found no such preservation for the per-invocation context. History is
preserved; the assembled context is not. Ordering and abort are now pinned by test.

### 9.5 Budgets, windows, and what happens when it does not fit

**STATUS: MISSING**
**EVIDENCE:** no `count_tokens`, `tiktoken`, `context_window`, `token_budget` or
`max_input_tokens` anywhere in `llm_engine`, `pick_debate`, `bot_benchmark` or `screen_context`.
`MAX_TOKENS` is an **output** cap only, identical for all seven chairs and all three providers —
so output-token reservation exists in the sense that output is bounded, but nothing reserves it
*against* an input budget, because there is no input budget.

Consequently:
- **Per-model context policy:** none. Every chair receives the same string whatever window its
  model has. §9's *"does each model receive the same canonical package with infrastructure
  compaction, or a model-specific context policy?"* — **neither**.
- **Deterministic retention priority:** none. Sections are emitted in a fixed order, but nothing
  drops one when the whole is too large.
- **When required context cannot fit:** the provider errors, the caller returns a `⚠️` string,
  and that string becomes **that chair's report** — passed on to the Contrarian and Moderator as
  their input. It is collected in `result.errors` and raised as a UI warning, so this is loud
  rather than silent, but there is no graceful degradation and no retry at a smaller size.
- **Automatic disqualification of a smaller-window model:** not possible — and §5.5 already
  established the battery never exercises context capacity, so the benchmark could not detect
  the problem either.

### 9.6 Output truncation is undetected — KNOWN GAP

**STATUS: PARTIAL — the hazard is understood, mitigated by headroom, and has no detector**

**EVIDENCE.** `MAX_TOKENS`' own comment is unusually candid, and it is the strongest evidence in
this section: the Moderator's block *"sits at the END of the response, exactly what a tight token
budget truncates first. Confirmed the old 1024 was genuinely tight for a real multi-line verdict
… which would silently break the TODO tracker, the decision log, and the bot_research feed by
cutting the response off before those lines were even written."*

The fix applied then was **4× headroom**. It was not a detector, and none exists: `stop_reason`,
`finish_reason` and `incomplete_details` appear nowhere in `llm_engine` or `pick_debate`. Every
provider caller joins the text blocks it received and returns them, so a response cut off at the
cap is byte-indistinguishable from a complete one.

**Demonstrated through the real parser:** a verdict truncated mid-`RECOMMEN` and a verdict that
never had a block produce **identical** `parse_moderator_verdict` output — `{}`. So §9's *"can
required information ever be silently dropped?"* is **yes, at the output end**, and the four
consumers §5.6 traced go quiet in exactly the same way for two entirely different reasons.

**Verdict: DOCUMENT, surfaced (#99).** Detection is a few lines per provider. What to *do* with
a truncated response is not: discard it as a failure, annotate it, or warn beside it are three
different behaviours, and the annotation option writes into text that is persisted and replayed
into later contexts. That is a policy choice, so it goes to the owner.

### 9.7 Repairs applied at this section boundary

**R8 — the budget guarantees that were emergent are now enforced.** `test_context_budget_boundary`
(16 tests) pins: the roster, league depth, freshness manifest and active objectives are iterated
whole and never sliced (checked by AST, not string matching); every supporting cap stays ≤ 30;
compaction writes its backup *before* overwriting and aborts on summarizer failure; the summarizer
fails soft so that abort can fire; `build_context` calls no model to shape itself; history
summarization is not routed through configurable roles; and the output cap is shared by all three
providers and is not back at the known-tight 1024.

The known gaps are pinned as characterization: no input-token accounting, no stop-reason
inspection, a truncated verdict indistinguishable from an unformatted one, and no per-model
context policy.

*Non-vacuity — five probes planted in real code and reverted, all failing:* capping the roster,
writing the compaction backup after the overwrite, dropping `MAX_TOKENS` back to 1024, adding a
`stop_reason` check, and making `build_context` call a model.

**Deliberately not applied:** truncation detection (9.6, a policy choice, #99); an input budget
or per-model policy (9.5, architectural); a cap on attachment *count* (9.1 — each file is
individually capped and the count is visible in the UI as `📎N`, so it is user-driven and not
silent).

### 9.8 A correction to a hypothesis of mine

Reading `compact_league_history`'s signature and its *"pruning the raw turns"* docstring, I formed
the view that compaction destroys the original history and was preparing to report it as the
section's defect. It does not: a timestamped backup of the complete pre-compaction file is written
first, and the whole operation aborts if the summarizer fails. Two lines further into the function
disproved it. Recorded because it is the second time this programme's most tempting finding was
one read away from being wrong (the first being §6.4a's composite-ambiguity claim).

### 9.9 Effect on open decisions

**#94's evidence improves, and its premises shift again — surfaced, not resolved.**

§5 established that a Moderator failing its machine contract silently disables four consumers.
§7 established that the same block is the *entire* channel through which model output acquires
authority. §9 now adds a third fact: **a contract failure has two indistinguishable causes.**
One is a model that will not follow the format. The other is *this app's own output cap* cutting
the block off — a documented, previously-observed failure at the old 1024 budget.

That matters for #94 directly. Option (a) — disqualify a candidate on contract failure — would
currently punish a model for a truncation the app caused, and would do so most often for exactly
the models that reason at length. Detecting truncation (#99) would separate the two causes and
make (a) a much more defensible option than it is today.

**Recommendation, not a decision: #99 before #94.** The truncation detector is the cheaper item
and it materially improves the evidence for the policy choice. Both remain yours.

---

## Pass 6 summary

| item | status | boundary kind |
|---|---|---|
| 9.1 full context at invocation (84% replayed prose) | EXISTS (measured) | — |
| 9.2 where compaction occurs (1 model call, 10 slices) | EXISTS | now enforced |
| 9.3 mandatory state never compacted | EXISTS | **emergent → enforced (R8)** |
| 9.4 originals preserved through compaction | EXISTS | **emergent → enforced (R8)** |
| 9.5 input budgets / per-model policy / retention priority | MISSING | absent |
| **9.6 output truncation undetected** | **PARTIAL** | characterized (#99) |
| 9.1a attachment count uncapped | DOCUMENT (user-driven, visible) | — |
| 9.5a handoff = canonical + evidence + prior output | PARTIAL — Draft Room 2 of 3, Prytaneum 1 of 3 | → #93 |

### Does anything clear the bar for a production change?

**No.** §9 is the second section running where the protections are real and simply undefended —
mandatory state is never truncated, compaction is reversible, and every cap but one is
deterministic. The repair was to make those enforced, which R8 did without touching production.

The one genuine gap, undetected output truncation, is a small change wrapped around a real policy
choice, and it is with you as #99.

### Follow-ups from this pass, ranked by evidence then severity

1. **9.6 / #99 — detect provider truncation.** Cheap, and it is the prerequisite that makes #94
   answerable rather than a guess.
2. **9.5 — an input budget and a per-model context policy.** The honest prerequisite for §5.5's
   context-capacity disqualification and for routing a small-window model at all.
3. **9.1a — a cap on attachment count.** Only worth it alongside 9.5; alone it solves nothing.

---

## Pass 7 — §10

**Scope:** Build Guide v2 §10 (auditability, provenance, causal reconstruction), whose mandate is
that *"a material recommendation should be reproducible as a causal artifact, not merely
recoverable as a piece of prose."*

**Baseline:** `cbb4a5a` on `ui-authority-pass`; `main` frozen at `9fb5102`. Two repairs at this
boundary (10.6). #91–94, #96–99 remain queued; #99 stays prioritized ahead of #94.

**Headline: today a recommendation is recoverable as prose and not reproducible as an artifact —
and the surface with the strongest canonical state has the weakest audit trail.**

### 10.1 The record inventory

**STATUS: PARTIAL — 6 of 16 record classes persisted, and the gaps are the causal ones**

| record class | where | lifetime | facing |
|---|---|---|---|
| AI invocations / outputs | `data/chats/<league>_history.json` | persistent | user |
| adjudications (verdicts) | `data/decisions/<league>.json` | persistent | user |
| external research / sources | `data/baseline/bot_research.json` | persistent, global | user (empty today) |
| inputs / settings | `bot_config.json`, `league_prefs`, `league_formats` | persistent, **current values only** | user |
| benchmark runs | `data/benchmark_results.json` | persistent, **now versioned + historied** (§5 R3/R4) | user |
| canonical-data provenance | `ATTRIBUTION.md` ×4, `sleeper_projection_provenance.json` | persistent | internal |
| **deterministic calculations** (board, TAV, VORP, composite) | **nowhere** | — | recomputed every rerun |
| **CDME snapshot / version** | **nowhere** | — | frozen in memory, no id (§3.9) |
| **context passed to each seat** | **nowhere** | — | built, sent, garbage-collected (§3.6) |
| **conflicts** | **nowhere** | — | never stored *as* a disagreement (§6.6b) |
| trade / waiver / lineup evaluations | **nowhere** | — | priced live, discarded |
| player/card selections | `st.session_state` | ephemeral | — |
| operational activity log | `st.session_state.activity_log` | **ephemeral, capped** | user, this session only |
| model / provider / version | on each chat message | persistent | **Prytaneum only until 10.6** |
| draft picks | Sleeper | external | — |

§10 asks to distinguish operational logs from user-facing decision history. **Both exist** —
`notify()` maintains an Activity Log and `decision_log` a decision history — but only the
decision history survives a restart; the operational log is `st.session_state` and dies with the
session.

### 10.2 The causal chain — a Prytaneum verdict

**STATUS: PARTIAL — 4 of 10 links intact, 3 partial, 3 broken**

| link | state | why |
|---|---|---|
| user action | ✅ | the question is on the decision row and in chat history |
| **frozen CDME state** | ❌ | no snapshot is taken for a Prytaneum question at all |
| **inputs** | ❌ | `build_context`'s output is never stored (§3.6) |
| **deterministic calculations** | ❌ | roster/composite/depth recomputed per rerun, never recorded |
| recommendation | ✅ | on the decision row |
| external research | ◐ | only what the Moderator chose to emit |
| evidence | ◐ | a source Beat found and the Moderator omitted is lost (§7.7) |
| chair outputs | ✅ | each chair's prose is a chat message, stamped with provider and model |
| Moderator response | ✅ | `moderator_text` stored in full |
| conflict / adjudication | ◐ | `DISSENT` is one prose line; no structured conflict record |

**Where provenance breaks, precisely:** at the three links between the question and the answer.
Everything the *model* said is retained; nothing the *engine* computed is. A dispute about a
recommendation can be answered with "here is what the panel wrote" and not with "here is what it
was looking at."

### 10.3 The causal chain — a Draft Room pick

**STATUS: MISSING — 1 of 10 links intact, 4 partial, 5 broken**

| link | state | why |
|---|---|---|
| user action | ❌ | "Debate This Pick" is not logged anywhere |
| frozen CDME state | ◐ | the `PickSnapshot` **is** canonical and frozen — and has no id and is never persisted |
| inputs | ◐ | `format_snapshot_for_llm` is deterministic *from the snapshot*, so recomputable only if the snapshot survived |
| deterministic calculations | ◐ | same |
| **recommendation** | ❌ | `PickDebateResult` lives in `st.session_state`; measured — `pick_debate` contains no `write_text`, no `json.dump`, no `open(` |
| external research | ✅ | none by design; `pick_debate` has no live search |
| evidence | ◐ | the snapshot *is* the evidence, and it is not retained |
| chair outputs | ❌ | Strategist/Skeptic/Caller reports are session-only |
| Caller's verdict | ❌ | session-only |
| conflict / adjudication | ❌ | `disagreements[]` session-only |

**This is the section's sharpest finding, and it is an inversion.** The Draft Room is where this
programme has spent most of its effort: a frozen, immutable, canonical `PickSnapshot`, a closed
decision boundary, an enforced ingestion whitelist, structural non-recomputation. All of that
produces the *best* causal object in the system — and it is thrown away when the Streamlit
session ends, while the Prytaneum, which has no canonical object at all, keeps its prose forever.

**Structurally the same inversion §7.10 found in provenance coverage:** the input questioned
least is documented last. Recorded as a pattern, not a coincidence.

### 10.4 Reproducibility and cost attribution

**STATUS: MISSING**
- *"Can every AI conclusion be reconstructed from exact snapshot + evidence + model/version +
  prompt/context?"* — **no.** Model/version yes (and now everywhere, 10.6); snapshot, evidence
  and context, no.
- *"Can every AI expenditure be attributed to user, operation, chair, model, provider, retry and
  tool call?"* — **no.** Verified precisely, after a naive substring scan produced four false
  positives (10.5): no `input_tokens`, no usage object, no cost, no price, no retry counter
  anywhere in `llm_engine`, `pick_debate`, `bot_benchmark` or `decision_log`. Chair, model and
  provider are attributable; the expenditure is not, because it is never measured.
- *"Can marginal cost of Insight versus Debate be determined?"* — **no**, and it is now three
  sections deep: §5.8 found cost absent from routing, §9.5 found no token accounting, §10 finds
  none recorded either. The same missing quantity answers a question in each.
- *"Can a successful chair response be distinguished from one generated but never acknowledged?"*
  — **partially.** A failed call is distinguishable (`⚠️` prefix, `result.errors`). A response
  that was generated, billed, and then discarded — a browser closed mid-`run_benchmark`, a
  Streamlit rerun between the call and the append — leaves no trace at all, because nothing is
  written until the operation completes.

### 10.5 A correction — and the sixth substring artifact

The first cost scan reported `usage`, `output_tokens`, `cost` and `price` as **present**. All
four were prose: "current usage" in a chair prompt, "opportunity cost" in `pick_debate`,
"price ceiling"/"priced" in a docstring — and, most instructively, `output_tokens` matched
`max_output_tokens=MAX_TOKENS`, which is §9's *output cap*, the opposite of usage accounting.
Re-run word-bounded and comment-stripped, all four are genuinely absent.

The same class then recurred inside a test I wrote: `assertNotIn("output_tokens=", source)`
failed against `max_output_tokens=`. Fixed with a word-bounded regex that also excludes the cap
assignment, with the reason recorded in the test.

**Sixth occurrence in this programme** (after D's `candidate.bpa`/`bpa_source`, Pass 2's
`team_label`/`surface`, Pass 3's `"role" in source`, and Pass 6's loop-dict keyed by target).
A second faulty assertion in the same file counted `process_moderator_output(` and matched its
own `def` line. Both were caught before shipping; the rate at which this class recurs is itself
the finding, and it is why every scan in this programme now gets a planted-probe check.

### 10.6 Repairs applied at this section boundary

Two, both applying a rule the codebase had already stated and then applied in only one place.
`app.append_message`'s own comment: *"provider/model (which actually answered) are stamped on the
message itself, not derived from live bot_config at render time — a role can be reassigned to a
different provider or model later, and an old message must keep showing who/what actually
answered it."* That rule was live for chat messages and absent from every other result.

**R9 — every debate result now records the model, not just the provider.**
`llm_engine.DebateResult` carried `role_providers` with a comment explaining precisely why; it
did not carry `role_models`, although `run_debate` already takes them. `pick_debate.PickDebateResult`
carried neither model nor any persistence. Both now record `role_models`. This matters beyond
tidiness: a role can be re-pointed at a *different model of the same provider* — the Moderator on
Opus for synthesis, the Quant on Sonnet for cheaper stat-crunching, which `run_debate`'s own
docstring names as a supported case — and a provider-only record cannot distinguish those at all.
Pinned by a test that runs all four chairs on one provider with two different models.

**R10 — a decision row records what produced the verdict.** `log_decision` gained optional
`provider` / `model`, and both `process_moderator_output` call sites pass them; the values were
already in scope at each. Absent means "not recorded", never "the default model", so rows written
before this remain valid and honest — pinned by a test.

*Non-vacuity — five probes planted in real code and reverted, all failing:* dropping
`role_models` from each result, defaulting an unset model to `CLAUDE_MODEL` rather than leaving
it absent, letting a call site fall back to the blank stamp, and adding a writer to `pick_debate`
(which correctly failed the "never reaches disk" characterization).

**Deliberately not applied.** Persisting `PickDebateResult`, the snapshot, or the assembled
context each means a new store with retention, scope and size decisions — architectural, and
already surfaced as #92. Persisting the activity log is the same. Cost accounting requires
deciding what to meter and where to put it.

### 10.7 Effect on open decisions

No open decision's premises changed. #99 remains ahead of #94, and §10 adds a supporting reason
rather than a new consideration: the Draft Room's chairs also emit a machine-parsed block
(`parse_caller_verdict`), also at the end of their response, under the **same** `MAX_TOKENS` cap
— so #99's truncation detector covers seven chairs, not four. That strengthens #99's priority; it
does not change what #94 is choosing between.

---

## Pass 7 summary

| item | status | boundary kind |
|---|---|---|
| 10.1 record inventory (6 of 16 classes persisted) | PARTIAL | — |
| 10.2 causal chain, Prytaneum (4/10 intact) | PARTIAL | characterized |
| **10.3 causal chain, Draft Room (1/10 intact)** | **MISSING** | characterized |
| 10.4 reproducibility from snapshot + evidence + context | MISSING | absent |
| 10.4a cost / token / retry attribution | MISSING | now pinned absent |
| 10.4b generated-but-unacknowledged responses | PARTIAL | — |
| **10.6 R9 — results record model, not just provider** | **REPAIRED** | enforced |
| **10.6 R10 — decision rows record what answered** | **REPAIRED** | enforced |
| 10.5 sixth substring artifact | correction | — |

### Does anything clear the bar for a production change?

**Two did, and both were applied** — R9 and R10, because each applies a rule this codebase had
already written down and then used in exactly one place. Neither adds a store, changes a
computed value, or needs a decision: they record something the caller already knew and was
discarding.

What did **not** clear the bar is the section's real finding — that the Draft Room's causal chain
is 1 of 10 links. Closing it means persisting a snapshot, a result, and their relationship, which
is a new store with retention and scope decisions attached. That is #92's territory and it stays
there.

### Follow-ups from this pass, ranked by evidence then severity

1. **10.3 + #92 together — persist the Draft Room's causal object.** The system's best causal
   artifact already exists in memory; the gap is entirely that nothing writes it down. A snapshot
   identifier (#92) and a persisted `PickDebateResult` are the same piece of work.
2. **10.4a — meter what a call costs.** One quantity answers §5.8's routing question, §9.5's
   budget question and §10's attribution question. Cheapest place to start is recording the
   provider's own usage object, which every SDK already returns.
3. **10.1 — persist the operational activity log.** Small, and it is the difference between an
   operational record and a toast.

---

## Pass 8 — §11

**Scope:** Build Guide v2 §11 (temporal consistency, concurrency, stale results).

**Baseline:** `edb9af2` on `ui-authority-pass`; `main` frozen at `9fb5102`. One repair at this
boundary (11.5). #91–94, #96–100 remain queued; #99 stays ahead of #94; #100 untouched.

**Headline: this app can tell whether a frozen snapshot is still current — precisely, with a
reason string — and nothing in production asks it.**

### 11.1 The mechanism already exists

**STATUS: EXISTS, and it is better than §3.9 credited**

**LOCATION:** `pick_synthesis.PickSnapshot:870-894` (the stamp), `snapshot_is_current:1018`.

**EVIDENCE:** `PickSnapshot` carries `picks_consumed` and `data_freshest_date` as an explicit
**INPUT-STATE STAMP**, and its own docstring names the consumers it exists for: *"which world
this frozen state was computed from … the stamp is what lets any later consumer (**a debate still
running**, a UI panel held open, a stored decision log) cheaply ask 'is this still the current
state?' via `snapshot_is_current`."* The certifier returns `(is_current, reason)`, checked
*"purely by INPUT IDENTITY … never by recomputing anything"*, and treats an unstamped snapshot as
**not certifiable** rather than silently current — *"'unknown provenance' and 'known current' are
different claims."*

Verified at all four boundaries: unchanged world → `(True, None)`; three new picks → `(False,
"3 new pick(s) made since this snapshot was built")`; changed data date → `(False, "the
underlying player data changed…")`; unstamped → `(False, "snapshot carries no input-state
stamp…")`. It is already covered by four tests in `test_pick_synthesis`.

### 11.2 And it has no production caller — KNOWN GAP

**STATUS: VIOLATED against the mechanism's own stated purpose**

**EVIDENCE.** Every reference to `snapshot_is_current` outside its own module and its tests is a
**comment**. Measured across every non-test module: **zero callers.**

Meanwhile both Draft Room result guards compare `pick_label`:

```
app.py:4805   if debate_result is not None and debate_result.pick_label == pick_label:
app.py:4441   if (mock_debate_result is not None and mock_debate_result.pick_label == mock_pick_label)
```

`pick_label` cannot answer §11's question. A user stays on the clock at one label while other
rosters keep picking, so two materially different boards share a label routinely — measured: a
3-candidate board at `3.05` / `picks_consumed=24` and a 1-candidate board at `3.05` /
`picks_consumed=27` compare **equal** under the guard.

**The sharpest form of the gap.** The snapshot cache key at `app.py:4666` is
`(…, len(draft_picks), merger.freshest_date)` — with a comment saying these are *"the same two
staleness signals `snapshot_is_current` already uses elsewhere in this module — reused here, not
reinvented."* So when the board changes, the app **detects it on exactly the right signals and
rebuilds the snapshot** — and then displays a recommendation computed against the *previous*
snapshot beside the *new* board, with no indication that anything moved.

That is §11's central question answered in the worst way: the result is still presented, and its
snapshot identity is not shown.

### 11.3 The delta is fully describable, by machinery pointed the other way

**STATUS: EXISTS (stranded)**
**EVIDENCE:** `diff_snapshots` produces the structured per-candidate delta — entered, departed,
rank movement, and per-component changes across eleven fields. On the measured pair it correctly
reports two departures and a rank move. It is folded into the **next** debate's evidence via
`debate_pick(previous_snapshot=…)` and is never used to invalidate or annotate the result already
on screen. So the capability to answer *"can the UI detect and communicate that context changed
since analysis began?"* exists in full, and is aimed at a different question.

### 11.3a Repair applied, and the half deliberately not applied

**R11 — a debate result now records the input-state stamp it reasoned over.**
`PickDebateResult` gained `snapshot_picks_consumed` and `snapshot_data_freshest_date`, taken
straight off the snapshot. Same rule as §10's R9/R10: what a result was produced from is part of
the result. Before this, a consumer holding only a result **structurally could not** put it to
`snapshot_is_current` — the stamp was not on it. Now it can, which a test demonstrates by
round-tripping the recorded stamp back through the certifier.

**What was not applied, and why.** Using the stamp to *act* — hide the stale result, annotate it,
or warn beside it — is a product decision with real user cost, not a mechanical fix. Hiding
discards an answer the user waited 30–120 seconds and real API spend for, possibly with seconds
left on a pick clock; annotating writes into displayed output; warning leaves a stale
recommendation on screen. This is the **same discard/annotate/warn trichotomy as #99**, at a more
time-pressured moment. Surfaced as #101.

### 11.4 Concurrency

**STATUS: PARTIAL — serialized by the runtime, unprotected at the store**

- **Within one session:** Streamlit executes one script run at a time and `debate_pick` /
  `run_debate` block inside `st.spinner`, so two AI operations cannot interleave. `run_debate`'s
  internal `ThreadPoolExecutor` parallelises Quant and Beat only, over one immutable context
  string. §11's *"can a chair accidentally mix temporal snapshots?"* → **no** (§3.8, and
  `PickSnapshot`'s tuple-not-list immutability is deliberate for exactly this).
- **Across sessions: a lost update, demonstrated.** Every per-league store does load → mutate →
  `write_text`, with no lock, no atomic replace, and no read-modify-write protection anywhere in
  the tree. Run against the real `todo_log` functions: tab A writes an objective, tab B reads,
  tab A writes a second, tab B saves its stale view — and **tab A's second objective is gone**.
  §11's *"can an older operation overwrite or contaminate a newer one?"* → **yes**.
- **Torn writes:** `write_text` is not atomic and `_load` swallows `JSONDecodeError` by returning
  `[]`, so a partially-written file silently reads as an empty store. **Recorded, not repaired** —
  a torn write is undemonstrated here, and §7.8 already established this programme does not make
  production changes for undemonstrated failures. The lost update *is* demonstrated, but its fix
  (locking, merge-on-write, or single-writer) is a design decision, not a mechanical one.

### 11.5 The remaining §11 questions

| question | answer |
|---|---|
| Are operations isolated, deduplicated, queued, or concurrent? | **Serialized** within a session by the runtime, not by design; deduplicated for the Prytaneum by `_last_submitted`; unprotected across sessions |
| Does every AI response know the operation snapshot it was generated against? | **Now yes for the Draft Room** (R11). The Prytaneum takes no snapshot at all (§10.2) |
| Can an operation be rejected automatically if its source snapshot is no longer current? | The certifier exists; nothing calls it (11.2) |
| Can replay be distinguished from fresh execution? | **No** — there is no replay path to distinguish (§3.7) |
| Clock skew | Not applicable as deployed: every timestamp is local `time.time()`, and the only external clock is Sleeper's `synced_at`, which is displayed rather than compared |

### 11.6 A correction to §3.9 — the third time a finding was one read short

§3.9 concluded that `PickSnapshot` has *"no id, no hash, no computed-at timestamp"* and that
*"consumers hold the object itself, not a reference to it."* The first clause is true of a
**unique identifier**. The framing around it was wrong: the snapshot carries a documented
input-state stamp, and a purpose-built certifier consumes it. Provenance was present; I recorded
it as absent because I read the field list and not the docstring twelve lines above it.

**This changes #92's premises, and shrinks it.** The gap is not "invent a provenance mechanism";
it is "persist and uniquely identify the one that exists." §10's framing of #92 — that the Draft
Room's causal object is strong and simply never written down — survives and is if anything
reinforced: the object is *even better* than recorded, and still discarded.

Third occurrence of this pattern (after §6.4a's composite-ambiguity claim and §9.8's
compaction-is-destructive claim). All three were the most tempting finding available, all three
were disproved by reading further in the same file. The pattern is now explicit enough to state
as a rule: **before reporting an absence, read the docstring of the thing you claim lacks it.**

---

## Pass 8 summary

| item | status | boundary kind |
|---|---|---|
| 11.1 input-state stamp + certifier exist | EXISTS | structural, tested |
| **11.2 certifier has no production caller** | **VIOLATED** | characterized |
| 11.3 `diff_snapshots` exists, aimed elsewhere | EXISTS (stranded) | characterized |
| **11.3a R11 — result records its input-state stamp** | **REPAIRED** | enforced |
| 11.3b acting on the stamp (hide/annotate/warn) | DEFERRED → #101 | — |
| 11.4a within-session isolation | EXISTS | structural (runtime) |
| **11.4b cross-session lost update** | **VIOLATED (demonstrated)** | characterized |
| 11.4c torn writes | DOCUMENT (undemonstrated, §7.8 precedent) | characterized |
| 11.5 replay distinguishable | MISSING | → #92 |
| 11.6 correction to §3.9 | correction | — |

### Does anything clear the bar for a production change?

**One did and was applied** — R11, because it is §10's R9/R10 rule again with no new decision in
it, and because without it no consumer can even ask the staleness question.

The two real gaps are both decisions. Consulting the certifier is a user-cost trade-off at the
most time-pressured moment in the product (#101). Fixing the lost update needs a concurrency
model this app has never had (#102).

### Follow-ups from this pass, ranked by evidence then severity

1. **11.2 / #101 — consult the certifier.** Everything needed now exists: the stamp, the
   certifier, the reason string, and (after R11) the stamp on the result. Only the policy is
   missing, and it is the same trichotomy as #99 — worth settling both together.
2. **11.4b / #102 — a concurrency model for the per-league stores.** Demonstrated data loss,
   bounded to multi-tab or multi-device use.
3. **11.6 / #92 — persist and identify the snapshot.** Smaller than recorded: the provenance
   stamp exists, so this is persistence plus a unique id, not a new mechanism.

---

## Pass 9 — §12

**Scope:** Build Guide v2 §12 (multi-tenant isolation, cache leakage, context pollution).

**Baseline:** `bf8d98b` on `ui-authority-pass`; `main` frozen at `9fb5102`. **No production file
was modified** — §12 found nothing that both clears the bar and is free of a policy decision.
#91–94, #96–102 remain queued; #99 stays ahead of #94; #100 untouched.

**Headline: §12 resolves better than the storage layout suggests, and the reason is reach.**
The one globally-shared, league-derived store withholds its private field from both the prompt
and the UI; the one real scope mechanism is *actually wired into the prompt*; and the only two
cross-session caches hold static images.

### 12.1 Scope key of every store

**STATUS: EXISTS — every store is scoped to the right thing**

| store | location | scoped by |
|---|---|---|
| chats, decisions, todos, pins | `data/<kind>/<league_id>…` | **league, by path** |
| `league_format` | `data/league_formats.json` | **league, by key inside** |
| `league_prefs` | `data/league_prefs.json` | **user, by key inside** |
| attachments | `data/attachments/` | **per-item scope list** (12.2) |
| `bot_research`, `bot_comparisons` | `data/baseline/` | **global** (12.3) |
| `bot_config`, `benchmark_results` | `data/` | global — app settings, not league data |
| `player_aliases` | `data/player_aliases.json` | global — player identity is a global fact |

A league-id in the *path* is the strongest scoping available here: one league's file cannot be
read without naming that league. Verified by exercising `league_format` — an override set for
`LEAGUE_A` returns `None` from `LEAGUE_B`.

### 12.2 The attachment scope mechanism is real, and it is wired

**STATUS: EXISTS — structural, and not stranded**
**LOCATION:** `attachments.set_scope:75`, `list_attachments:84`; consumed at `app.py:1884`.
**EVIDENCE:** attachments carry a per-item `league_ids` list — `None` means global, a list scopes
to those leagues — and `list_attachments(league_id=…)` returns *"global items plus anything
scoped to include it."* Exercised: from league A, `{global.txt, a_only.txt}`; `b_only.txt` is
excluded; unfiltered still returns all three.

**The part that matters is the call site.** `build_context`'s reference-material section calls
`list_attachments(league_id=st.session_state.selected_league_id)`. The three unfiltered call sites
are management and counting views — one carries an explicit comment saying so. So unlike §11's
`snapshot_is_current`, **this protection is not stranded**: the filter runs on the path that
reaches a model. Now pinned, including that `build_context` contains no unfiltered call.

### 12.3 The one global league-derived store — measured by reach

**STATUS: EXISTS, with the private field withheld — narrower than the schema suggests**

`bot_research` is global by design and records `league_id` on every entry. What matters is what
actually travels. Measured field-by-field against `build_context`'s real render lines:

| | reaches another league's prompt | stored but withheld |
|---|---|---|
| finding | `date`, `player_name`, `source`, `rank`, `claim` | **`question`**, **`league_id`**, `conviction`, `id`, `ts`, `composite_impact` |
| comparison | `date`, `subject`, `direction`, `compared_to`, `context`, `source`, `evidence` | **`question`**, **`league_id`**, `panel_undisputed`, `id`, `ts`, `evidence_type` |

**`question` is the private field** — the user's own free text, e.g. *"Should I sell my WR1 given
my 2-6 record?"* — and it reaches neither another league's prompt nor the Bot Research panel,
which renders only Date / Player / Source / Claim / Rank / Composite impact.

So §12's *"can shared research contain hidden private context inherited from the operation that
discovered it?"* → **in the stored object yes, in anything replayed no.** And the sharing is
**disclosed in the UI in words**: *"Everything the panel has vetted across every league."*

**Residual, named and undemonstrable:** `claim` and `evidence` are free text authored by the
Moderator and could themselves embed league context. The store is empty (§6 reach: 0 findings
ever), so this cannot be measured, and the schema cannot prevent it.

### 12.4 Caches

**STATUS: EXISTS — the only cross-session caches hold static images**
**EVIDENCE:** exactly two `@st.cache_resource` functions exist, `_page_icon` and
`_header_banner_data_uri`. Both take **no arguments** — so neither can be keyed by league or user
— and both read only from `ASSETS_DIR`. Neither touches `session_state`, a roster, a league, or a
`user_id`. A no-argument cross-session cache is safe *only* if its contents are tenant-free, which
is exactly the condition here, so that condition is what the test pins.
Everything else is `st.session_state`, which Streamlit scopes per session, or the snapshot cache
keyed on `(draft_id, target_index, roster_id, pool_scope, len(picks), freshest_date)` — league-
specific by construction (§11.2).
No embeddings, no vector index, no shared summary object exists anywhere; `compact_league_history`
summaries are per-league by path.

### 12.5 Research cannot be scoped to its league — KNOWN GAP

**STATUS: PARTIAL (latent)**
**EVIDENCE:** `findings_for_context` and `comparisons_for_context` take **only `limit`** — no
league parameter, so neither can filter. `league_id` is written on every entry and read by
nothing.
§12 asks *"can private evidence be promoted to a global object without an explicit policy
decision?"* The promotion **is** a policy — the Moderator's SOURCE FINDING gate (§6.2) — and it is
disclosed. What is missing is a **per-item** choice: no way to scope a finding to its originating
league even though the field is recorded.
**The precedent exists in the same codebase.** `attachments` already implements exactly this
pattern — a scope list, `None` for global, a filtered read wired into `build_context`. Applying it
to research is a small change with a real policy question in front of it: today's default is
share-everything, disclosed; changing it changes what the panel remembers across leagues.
**Verdict: DOCUMENT, surfaced (#103).** Not chosen.

### 12.6 A correction to §13.5 — the fourth time a finding was one read short

§13.5 recorded that under hosting *"two stores would be immediately wrong — `league_prefs.py` and
`league_format.py` use a module-level global `PATH` rather than the per-league scoping … all use."*

**That is wrong.** Both use one shared file *and are correctly scoped by key inside it*:
`league_format.get_format_override(league_id)` / `set_format_override(league_id, …)`, with a
docstring stating the intent — *"Keyed by league_id (a property of the league itself), not by
Sleeper user"* — and `league_prefs.get_prefs(user_id)`, which is the right key for "which leagues
has this user archived and in what order". I conflated *global file* with *global scope*, having
read the path constant and not the accessor signatures.

Their real hosting exposure is **concurrent writes to one shared file**, which is #102's
territory, not miskeying. §13.5's status (NOT APPLICABLE as deployed, hard blocker for hosting)
is unaffected; only its named example was wrong.

Fourth occurrence of this pattern, after §6.4a, §9.8 and §11.6. The §11 rule — *before reporting
an absence, read the docstring of the thing you claim lacks it* — would have caught this one too,
and did not get applied because §13.5 predates it. Every remaining section now gets that check.

### 12.7 Repairs applied at this section boundary

**None.** §12's protections are real and were undefended; the repair was to enforce them.
`test_tenant_scope_boundary` (13 tests) pins: the four conversation stores keep a league id in
their path; `league_format`/`league_prefs` keep their keys; a format override is not visible from
another league; `build_context` filters attachments by the selected league and contains no
unfiltered call; the filter actually filters; a finding's `question` and `league_id` reach neither
prompt nor UI; the cross-league sharing stays disclosed; and both cross-session caches keep taking
no arguments and touching nothing tenant-specific.

*Non-vacuity — six probes planted in real code and reverted, all failing:* removing the league
filter from `build_context`, removing the filter's body, rendering a finding's `question` into the
prompt, giving a cross-session cache an argument, giving `findings_for_context` a scope parameter
(the known gap, correctly demanding inversion), and removing `league_format`'s league key.

---

## Pass 9 summary

| item | status | boundary kind |
|---|---|---|
| 12.1 every store scoped to the right thing | EXISTS | now enforced |
| 12.2 attachment scope wired into the prompt | EXISTS | now enforced |
| 12.3 private `question` withheld from prompt and UI | EXISTS | now enforced |
| 12.3a `claim`/`evidence` free text could embed context | DOCUMENT (undemonstrable, store empty) | — |
| 12.4 cross-session caches hold static assets only | EXISTS | now enforced |
| **12.5 no per-item league scope for research** | **PARTIAL (latent)** | characterized → #103 |
| 12.6 correction to §13.5's named example | correction | — |
| cross-*user* isolation | NOT APPLICABLE (no tenancy — §13.5) | — |

### Does anything clear the bar for a production change?

**No, and this is the second section where the honest answer is that the protections were already
right.** The only gap — no per-item league scope for research — has a policy question in front of
it: today's default is share-everything-across-leagues, deliberately and visibly. Changing it
changes what the panel remembers, and the field needed to implement either answer is already
recorded.

### Follow-ups from this pass

1. **12.5 / #103 — a scope decision for research findings.** Small, with the pattern already
   implemented next door in `attachments`; blocked only on the default.
2. **12.6 → #102** — the shared-file stores' real hosting exposure is concurrency, not scope.
   Recorded on #102 so the hosting precondition list stays accurate.

---

## Pass 10 — §14

**Scope:** Build Guide v2 §14 (failure modes, partial completion, fallbacks).

**Baseline:** `ed32551` on `ui-authority-pass`; `main` frozen at `9fb5102`. One repair at this
boundary (14.7). #91–94, #96–103 remain queued; #99 stays ahead of #94; #100 and #103 untouched.

**Headline: fail-soft is this app's strongest reliability property and it was undefended — and
underneath it, a failed chair's error string was being handed to the next chair as that chair's
evidence.**

### 14.1 Every call fails soft

**STATUS: EXISTS — structural, now enforced**
**EVIDENCE:** all six provider callers (three in `llm_engine`, three in `pick_debate`) return a
`"⚠️ …"` string and never raise — verified for both the missing-key path and the
`except Exception as exc` path in each. So one dead provider cannot take out the panel:
`run_debate` continues, the surviving chairs still answer, `result.errors` collects every failure,
and `app.py` raises *"Debate finished with issues: …"*. A failed Moderator never reaches the
verdict parser (`if not moderator_text.startswith("⚠️") else {}`).

**Deterministic output is untouched by any AI failure.** `debate_pick`'s first parameter is an
already-built snapshot, and the module contains no call to `compute_draft_board` or
`build_snapshot` — it structurally cannot influence the board it reasons over. §14's *"can it
degrade gracefully while preserving deterministic CDME output?"* is answered by the import graph,
not by a handler.

### 14.2 The failure taxonomy is coarse

**STATUS: PARTIAL**
**EVIDENCE:** nine distinguishable causes collapse into six signals, with one signal carrying
four of them:

| cause | signal |
|---|---|
| provider unavailable / network dead | `⚠️ <provider> request failed: {exc}` |
| authentication failed (bad key) | *same* |
| quota exhausted / 429 rate limit | *same* |
| context exceeds the model limit | *same* |
| no key configured at all | `⚠️ <PROVIDER>_API_KEY not set — …` |
| empty response (Gemini only) | `⚠️ Gemini returned an empty response.` |
| **output truncated at `MAX_TOKENS`** | **no signal at all** (§9.6 / #99) |
| model produced invalid output | no signal — parses to `{}` (§5.6 / #94) |
| evidence unavailable (no data loaded) | prose in DATA AVAILABILITY — correctly *not* a failure |

No `status_code`, `RateLimitError`, `AuthenticationError` or `429` handling exists in either
module. So §14's *"does the system distinguish 'provider unavailable' from 'model produced
invalid output' from 'evidence unavailable'?"* → **the third, yes and deliberately; the first two,
no.** A user seeing *"request failed"* cannot tell a wrong key from an exhausted quota without
reading the exception text.
**Verdict: DOCUMENT.** Classifying provider exceptions means committing to each SDK's error
taxonomy across three providers, which is real work with a maintenance burden, not a mechanical
fix — and it is the same surface as #100's metering, which would consume the same response object.

### 14.3 Retries, resume, and duplicate prevention

**STATUS: MISSING**
**EVIDENCE:** no `retry`, `backoff`, `max_retries`, `resume` or `idempot` anywhere in
`llm_engine` or `pick_debate`. So §14's *"are retries bounded?"* is satisfied trivially — bounded
at zero — and *"can an operation resume without duplicating calls or cost?"* is **no**: a
Moderator that fails after three successful chairs cannot be resumed, and re-running re-pays for
all four. Duplicate prevention is `_last_submitted`, keyed on the **question text** rather than an
operation id, so it deduplicates a repeated question and not a repeated operation.
*"What if a chair succeeds but the connection dies before orchestration receives the response?"* →
the SDK raises, the caller returns `⚠️`, and the call is billed with nothing recorded. Detecting
that requires the usage object nothing reads (#100).

### 14.4 Complete failure state is not recorded

**STATUS: MISSING**
**EVIDENCE:** `log_decision` returns early on a falsy verdict, and a totally failed debate parses
to `{}` — so **a failed operation writes nothing to the decision log**. Demonstrated: logging a
`⚠️` verdict leaves the store empty, while a real verdict writes one row. The only record is
`notify()` → `st.session_state.activity_log`, which §10.1 established is ephemeral.
So the durable record contains every successful decision and no failed one — which makes the
decision log a record of what worked rather than of what was attempted.
**DEPENDENCIES:** #92 / §10.1. Recording failures is a new record type with retention questions;
not repaired here.

### 14.5 A failed chair was handed on as evidence — REPAIRED

**STATUS: VIOLATED → REPAIRED (R12)**

**EVIDENCE, measured before the repair.** With the Quant and Beat both failing, the Contrarian's
prompt contained:

```
--- QUANT / VORP REPORT ---
⚠️ Claude request failed: Connection reset by peer

--- BEAT / NEWS REPORT ---
⚠️ Claude request failed: Connection reset by peer
```

…followed by *"Pressure-test these two reports."* No label anywhere marked either as a failure —
checked for "unavailable", "failed to run", "missing", "could not": **none present**. The
Contrarian, whose entire job is finding what the other chairs missed, was being asked to
pressure-test a connection error as though it were the Quant's analysis.

That answers two of §14's questions at once, both badly: *"do downstream chairs know which
upstream evidence is missing?"* → **no**; *"is missing research ever treated as negative
evidence?"* → **it was structurally invited to be.**

**Why this was repaired rather than surfaced.** It is not a new policy choice; it is this
codebase's own rule, applied at the one place it was broken. *A missing thing is represented as
missing, never as a value* — an unpriced row carries `None` rather than `0.0`; an unstamped
snapshot is *"not certifiable"* rather than current (§11.1); an unrecorded model is `""` rather
than the default (§10 R10); `panel_undisputed` replaced a `validated` the writer could not
establish (§6 R1). A failure occupying the report slot breaks that rule in the one place a model
reads it. The information needed was already present at the moment the prompt is built — the same
`startswith("⚠️")` test that populates `result.errors`.

### 14.6 What R12 does, and what it deliberately does not

Failed upstream reports are replaced, **in the model-facing handoff only**, by:

> *(unavailable — this chair's call did not complete, so no analysis was produced. Treat this as
> MISSING information, never as a finding that there is nothing to report.)*

Three properties, each pinned by test:
- **The second sentence is load-bearing.** A bare "unavailable" invites exactly the negative-
  evidence reading §14 warns about, from the chair most likely to make it.
- **The raw exception is not forwarded.** *"Connection reset by peer"* is not analysis, and
  passing provider A's internal error text into provider B's prompt is a cross-provider
  disclosure with no upside — the residual §7.8 named, here removed at its one live instance.
- **The failure still reaches the user intact.** `result.errors` and `DebateResult.quant` keep the
  real string; only the model-facing copy changes. Real reports pass through untouched.

Applied to all four downstream handoffs: Contrarian and Moderator in `llm_engine`, Skeptic and
Caller in `pick_debate`.

**Not applied — abort versus degrade.** §14 asks *"if an upstream chair is corrupted and fallback
also fails, what deterministic rule governs abort versus degraded operation?"* There is no such
rule: the debate always degrades and never aborts. Whether a Moderator should synthesize from
three unavailable reports at all is a product decision with real cost on both sides — aborting
discards the chairs that did succeed; degrading spends a Moderator call on nothing. Surfaced
(#104), not chosen. R12 makes either choice implementable and makes the current one honest.

### 14.7 Effect on an open decision — #99 sharpens

**Surfaced, not resolved.** R12 labels every failure that announces itself. Truncation is the one
that does not: a response cut off at `MAX_TOKENS` does **not** start with `⚠️`, so
`_report_for_handoff` passes it through as a complete report, and a downstream chair receives a
half-finished analysis presented as a finished one.

So after R12, §14's taxonomy has a sharper shape: **every failure class is now correctly labelled
at the handoff except the one with no signal at all.** That does not change what #99 is choosing
between — discard, annotate, or warn — but it adds a consequence that was not on the table: the
detector would also let `_report_for_handoff` mark a truncated upstream report, which is a
correctness fix for the *downstream chair*, not only a display question for the user. Recorded on
#99.

---

## Pass 10 summary

| item | status | boundary kind |
|---|---|---|
| 14.1 every call fails soft | EXISTS | structural, now enforced |
| 14.1a deterministic output survives AI failure | EXISTS | structural (import graph) |
| 14.2 failure taxonomy (9 causes → 6 signals) | PARTIAL | characterized |
| 14.3 retries / resume / duplicate prevention | MISSING | characterized |
| 14.4 complete failure state recorded | MISSING | characterized (→ #92) |
| **14.5 failed chair handed on as evidence** | **VIOLATED → REPAIRED (R12)** | **enforced** |
| 14.6a abort versus degrade rule | MISSING | → #104 |
| 14.7 truncation is the unlabelled failure class | — | sharpens #99 |

### Does anything clear the bar for a production change?

**One did and was applied.** R12 is this codebase's own absence rule enforced at the one place it
was broken, with the classifying information already computed at that point. It changes no
policy: the debate still degrades rather than aborting, the user still sees the real error, and
only the text a downstream model reads is corrected.

Everything else in §14 is either a genuine design commitment (a provider error taxonomy, retries,
a resume path, an abort rule) or already owned by an open item (#92 for failure records, #99 for
truncation, #100 for the usage object that would detect a billed-but-lost call).

### Follow-ups from this pass

1. **#104 — a deterministic abort-versus-degrade rule.** R12 makes either implementable; the
   choice is a product one.
2. **14.2 + #100 together — classify provider errors while reading the response object.** Both
   consume the same thing, and doing them separately means touching the callers twice.
3. **14.4 → #92 — record failed operations.** The decision log currently records what worked, not
   what was attempted.

---

## Pass 11 — §15

**Scope:** Build Guide v2 §15 (economic and resource exhaustion).

**Baseline:** `c55fdf0` on `ui-authority-pass`; `main` frozen at `9fb5102`. **No production file
was modified** — §15's gaps are all limit-setting decisions, and its strengths were undefended
rather than broken. #91–94, #96–104 remain queued; #99 stays ahead of #94.

**Headline: every AI operation has a deterministic, small, closed-form call envelope — and it is
deterministic by accident of construction rather than by a limiter, which is exactly why it
needed pinning.**

### 15.1 The envelope, counted

**STATUS: EXISTS — now enforced**
Counted by stubbing the real provider callers, not read off the source:

| operation | provider calls | why that number |
|---|---|---|
| `run_debate` (full Prytaneum) | **4** | one per chair in `ROLE_SYSTEM_PROMPTS` |
| `ask_moderator_followup` | **1** | the Moderator alone |
| `debate_pick` (Draft Room) | **3** | one per chair in `DEFAULT_ROLE_PROVIDERS` |
| `run_benchmark` | **candidates × scenarios × 2** | one model call *plus one judge call* per scenario |

Verified at 1, 2 and 3 candidates for the benchmark. The ×2 is the half most easily forgotten
when reasoning about what a run costs: the judge is a billed call too.

### 15.2 Nothing amplifies it

**STATUS: EXISTS — three independent reasons, all now pinned**
- **No retries.** `retry`, `backoff`, `max_retries`, `tenacity` appear nowhere. §15's *"can
  retries exceed a hard operation envelope?"* is satisfied trivially — bounded at zero.
- **No loop around a provider call** in `llm_engine` or `pick_debate`. `bot_benchmark` does loop,
  and its bounds are the two finite lists it iterates (`candidates`, `battery`).
- **No recursion.** `process_moderator_output` is the single place a model's output is acted on,
  and — walked by AST with the docstring removed — it reaches **only** `parse_*` members. Parsing
  a verdict cannot spend money. Reinforced by the call-site census: every provider-spending entry
  point in `app.py` sits behind a button or a submitted question, never behind another model's
  output.

The Moderator's prompt says it *"can recommend /debate in its own reply … but it never triggers
that itself; only the user typing /debate does."* §15 is where that instructional boundary turns
out to be **structural as well** — there is no code path from a parsed verdict to a call.

### 15.3 The one unbounded term — provider-side tool calls

**STATUS: MISSING — and this is the section's genuinely new finding**
**EVIDENCE:** every chair call attaches a server-side web-search tool —
`web_search_20260209` (Claude), `types.Tool(google_search=…)` (Gemini), `{"type": "web_search"}`
(OpenAI) — with **no `max_uses`, no `max_tool_calls`, no `tool_choice`, no search cap of any
kind.** How many searches the provider executes *inside one chair call* is the provider's
decision, is billed, and is invisible here because no usage object is read (#100).

So the envelope splits: **the chair-call count is deterministic; the tool-call count inside each
one is not.** A "4-call debate" is four *app* calls and an unknown number of *billed provider
operations*. §15's *"is there a deterministic maximum call/cost envelope for each operation
type?"* is therefore **yes at the layer this app controls, no at the layer it pays for.**
**Verdict: DOCUMENT.** Capping tool use changes what Beat and Contrarian can actually find —
a capability/cost trade-off, not a mechanical fix. Surfaced (#105).

### 15.4 No budget primitives exist

**STATUS: MISSING**
**EVIDENCE:** no `budget`, `quota`, `cooldown`, `debounce`, `throttle`, `rate_limit`, spend cap
or cost ceiling anywhere — verified word-bounded with comments excluded, after a naive scan
reported three false positives (15.8).
Consequently: no hard server-side resource budget of any kind; no concurrency limiter beyond
`max_workers=2` *within* one debate; nothing stops a runaway or repeated operation; and §15's
*"can the system stop safely when budget is exhausted while preserving state and auditability?"*
has no mechanism to answer — quota exhaustion arrives as a `⚠️` and the operation degrades
(§14.2), which is safe but is not budget-aware.

### 15.5 The largest single-action spend, and its default

**STATUS: PARTIAL — maximal by default, but disclosed**
**EVIDENCE:** the benchmark's candidate multiselect is `options=_p_fetched, default=_p_fetched`
— **every model fetched for every configured provider, pre-selected.** At three scenarios and two
calls each:

| candidates | billed calls from one button press |
|---|---|
| 1 | 6 |
| 5 | 30 |
| 10 | 60 |
| 30 | 180 |

**The mitigation that does exist, and is now pinned:** the caption says *"Real, billed API calls —
nothing runs until you press Run"*, the button label carries the live count
(`{len(_bench_candidates)} model(s) × {…} scenarios`), and the button is disabled at zero
candidates. So the cost is disclosed at the moment of action — it is simply defaulted to maximum.
**Verdict: DOCUMENT.** Changing a default is a product decision. Surfaced (#105).

### 15.6 What §15 asks that this app already does well

- **Reusable research materially reduces repeated cost** — `findings_for_context` /
  `comparisons_for_context` replay past panel-vetted findings into every later context, so a
  finding is paid for once (§6.6a). This is a genuine affirmative answer.
- **Concurrent aggregate spike** — bounded within a debate at two workers; across sessions
  unbounded, but that is #102's multi-writer surface rather than a distinct cost mechanism.
- **Cost-aware routing among qualified models** → **no** (§5.8: price is not an input to
  routing). **Pricing-change detection** → **no** — nothing records or compares provider prices.
  **Per-expenditure attribution** → **no** (#100).

### 15.7 Effect on an open decision — #100 sharpens

**Surfaced, not resolved.** #100 already recorded that one missing quantity answers "no" in three
sections. §15 adds a fourth consequence and a sharper reason: the tool-call term (15.3) is not
merely unmetered, it is **unmeasurable by any other means**. Chair calls can be counted from the
outside — this pass just did it — but searches executed inside a provider's own call can only be
seen in the usage object that nothing reads. So metering is not just the cheapest way to answer
§15's cost questions; for the one genuinely unbounded term it is the *only* way. That strengthens
#100's priority without changing what it is choosing between.

### 15.8 A correction — the seventh substring artifact, caught twice in one probe

My §15 probe reported two things that were false, both caught before they became findings:

1. **"Model output triggers another model call."** A naive `llm_engine\.(\w+)` regex over
   `process_moderator_output` returned `ask_moderator_followup` — which appears **only in that
   function's docstring**, explaining which callers can produce a verdict block. There is no
   recursion. Re-checked by AST with the docstring dropped. The test I shipped uses the AST walk
   and records why in a comment.
2. **"Budget/ceiling/spend primitives exist."** All three were prose: *"a live draft's per-pick
   LLM budget"* in a docstring, `PRICE CEILING` as a verdict field and `Ceiling` as a Draft Sharks
   column, and *"actually spend a full panel run"* inside a prompt.

Seventh occurrence of this class (after D's `candidate.bpa`, Pass 2's `team_label`/`surface`,
Pass 3's `"role" in source`, Pass 6's loop-dict, Pass 10's `max_output_tokens`, and this pass's
two). Both were caught by the standing rule that no scan result is believed before a probe or a
second reading — which is now the only reason the count is seven rather than a list of published
errors.

---

## Pass 11 summary

| item | status | boundary kind |
|---|---|---|
| 15.1 deterministic per-operation call envelope | EXISTS | now enforced |
| 15.2 no retries / loops / recursion amplifying it | EXISTS | structural, now enforced |
| **15.3 provider-side tool calls uncapped** | **MISSING** | characterized → #105 |
| 15.4 budgets / quotas / cooldowns / throttles | MISSING | characterized |
| 15.5 benchmark defaults to every fetched model | PARTIAL (disclosed) | characterized → #105 |
| 15.5a benchmark cost disclosed before running | EXISTS | now enforced |
| 15.6 reusable research reduces repeated cost | EXISTS | → §6.6a |
| 15.6a cost-aware routing / pricing detection / attribution | MISSING | → #100 |
| 15.7 tool-call term is unmeasurable without metering | — | sharpens #100 |
| 15.8 seventh substring artifact, twice | correction | — |

### Does anything clear the bar for a production change?

**No.** Every §15 gap is a limit-setting decision — how many searches a chair may run, what a
benchmark should pre-select, whether a budget ceiling exists and what happens at it. Each trades
capability or cost against safety, and none is resolvable under an already-established rule.

What §15 did produce is worth stating plainly: the cost guarantee this app actually has is real
and was entirely undefended. A single added retry, a chair reacting to another chair, or a
dropped judge call would each change the bill without changing any number a test looked at.
Eleven tests now make those visible.

### Follow-ups from this pass

1. **#105 — the resource-limit family.** Tool-call cap, benchmark default, budget ceiling,
   per-snapshot cooldown. One decision surface, four knobs.
2. **#100 — meter the usage object.** Now the only way to see the one unbounded term.
3. **Pricing-change detection.** Named, unranked: nothing records a provider's price, so nothing
   can notice one changing. Downstream of #100 having anything to compare against.

## Pass 12 — §16

**Scope:** Build Guide v2 §16 (human-in-the-loop override provenance).

**Baseline:** `ff460db` on `ui-authority-pass`; `main` frozen at `9fb5102`. Two production
files modified (`todo_log.py`, `app.py`) — R13 and R14 below. #91–94, #96–105 remain queued;
#99 stays ahead of #94.

**Headline: §16 asks how a manual override of a CDME variable is isolated from canonical
calculation. The measured answer is that no such override surface exists — injury status,
positional need, replacement level and every valuation term are computed and cannot be
user-moved. What the user *can* override is one layer earlier: which vendor row a player is
priced from, which files the vendor pools are built out of, and what the panel is told the
league's format is. All three reach the engine or the verdict; none of them says so.**

### 16.1 The override inventory, measured

Every persisted store a user can write from the UI, and what it reaches:

| store | written by | reaches | when | who | why |
|---|---|---|---|---|---|
| `data/player_aliases.json` | user only | **`bpa` / `universal_value`** | ✗ | ✗ | ✗ |
| `data/projections/**` (uploads) | user only | **`bpa` / `universal_value`** | file mtime | ✗ | note → attachment |
| `data/baseline/external/*/*.csv` | user only | **`composite_player_score`** | file mtime | ✗ | ✗ |
| `data/league_formats.json` | user only | debate context + guidance | ✗ | ✗ | ✗ |
| `data/pins/{league}.json` | user only | debate context (on relevance) | ✗ | ✗ | ✗ |
| `data/bot_config.json` | user only | routing | ✗ | ✗ | ✗ |
| `data/league_prefs.json` | user only | display only | ✗ | keyed by user_id | ✗ |
| `data/attachments/captions.json` | user only | debate context | ✓ `uploaded_at` | implicit | caption |
| `data/todos/{league}.json` | **both** | debate context | ✓ ts/date | ✓ `source` | ✓ reason/notes/revisions |
| `data/decisions/{league}.json` | **both** | debate context | ✓ ts/date | ✓ provider/model (R10) | ✓ reason |
| `data/baseline/bot_research.json` | **both** | **`composite_player_score`** + context | ✓ ts/date | ✗ (see 16.5) | ✓ claim/question |

**The pattern this table shows is the section's real finding, and it is the inverse of the one
§7.10/§10.3 named.** There, provenance coverage was inversely proportional to how much a
source mattered. Here it is proportional to **who wrote the record**: every store the AI
writes into is stamped, sourced and reasoned; every store only the human writes into records
nothing at all. Three of the four unstamped stores feed valuation.

### 16.2 The isolation question answers itself — there is no CDME-variable override

**STATUS: N/A BY CONSTRUCTION — and this is a protection, not a gap**
**EVIDENCE:** `app.py` contains **zero** `st.number_input`, `st.slider` and `st.toggle` calls.
`injury_status` is read at exactly four sites (`draft_room.build_available_pool`,
`player_universe`, `data_merger`, `app`) and in every one of them it comes straight from
Sleeper's `players_db` — `info.get("injury_status")`. `RISK_ADJ` keys off that value and
nothing else. `need_bonus`, `eligibility_bonus`, `replacement_levels` and `time_horizon_adj`
are all computed from roster state and the loaded pools.

So §16's named examples — *"injury status, positional need, VOR baseline, custom value"* — have
no override path at all. Isolation is total because the capability does not exist. This is
worth stating plainly rather than scoring as a pass: the app's answer to "how is a manual
override isolated from canonical calculation" is that it never offered one.

### 16.3 Where user input *does* reach the deterministic engine — three doors

**STATUS: EXISTS, unattributed downstream**

**(a) The manual alias.** Demonstrated on a synthetic two-row pool (and reproduced against the
real committed baseline): aliasing an unmatched Sleeper name onto `J Chase` moved that row's
`trade_value` **41.0 → 100.0** and `projection` **202.0 → 339.0**, and did so *over a correct
automatic match* (`match_path` was `"key"`, `match_verified` True, before the alias existed).
The alias branch deliberately bypasses `_contradicted`'s team/position rejection — overriding
the guards is the point of an override — and it resolved a CLE WR onto a CIN WR row.

`merge_player` reports this honestly: `match_path == "alias"`. `build_available_pool` carries
it onto every pool row as `_match_path`. And then **`compute_draft_board`'s two explicit output
column lists drop it**, in both the upside and balanced branches. Verified by AST over the
board's own subscript lists, not by substring: `bpa_source` and `universal_value` are emitted,
`_match_path` and `_match_verified` are not. Grepped across the whole repo, both fields are
**write-only in production** — nothing reads either one.

Net: a candidate whose price rests on a user override is indistinguishable, at the decision
boundary and in every debate downstream of it, from one the matcher resolved on its own.
**Verdict: SURFACE (#107).** Carrying it through changes the `PickSnapshot` candidate schema —
the frozen decision boundary — which is architectural, not mechanical.

**(b) The external-source refresh.** `external_upload_targets()` deliberately overwrites the
*exact* tracked filename for a source, and its docstring is right about why (any other name
would sit alongside the baseline as a second, separately-percentiled `(source, file)` pair and
double-count that source). The consequence is that after the upload, the user's CSV **is**
DynastyProcess: same `source_name`, same `source_file`, same `COMPOSITE_SOURCE_WEIGHTS["dynastyprocess"] = 1.0`,
and `describe_external_value` renders it to the panel under the vendor's name. Validation is
`"name" in _ext_df.columns` — nothing checks the file came from that vendor. **Verdict: DOCUMENT.**
Refreshing a source *is* the feature; the gap is that the record cannot distinguish a shipped
export from a hand-made one. Folded into #107.

**(c) The rankings upload.** Goes through the app's best human-in-the-loop gate — see 16.6.

### 16.4 Attribution in the AI layer — labelled everywhere but one place

**STATUS: EXISTS — one exception, now repaired (R14)**
`build_context` already announces every user-supplied section, and does it well:
- REFERENCE MATERIAL: *"captioned by hand — you're only given the caption text, not the actual
  file, so treat it as a claim to weigh, not verified fact"*
- PAST DECISION OUTCOMES: *"(user-recorded, not a guess)"*
- PINNED: *"the user manually flagged these … pinning doesn't mean elevated priority — weigh it
  like anything else here, not as a standing instruction or a settled conclusion"*

`pinned_messages.find_relevant` backs the third one structurally, not just instructionally: a
pin is retrieved only on keyword overlap with the current question, never injected by default,
*"so an old, once-useful observation can't quietly bias every future debate forever."* That is
§16's "isolated from canonical" answered at the retrieval layer.

**The one exception was the manual league-format override.** It was appended to the League line
as a bare peer of Sleeper's own fields —
`League: X (2026) — Dynasty, Best Ball, 12 teams, …` — where *Dynasty* is API-detected and
*Best Ball* is a dropdown the user set, and nothing distinguished them. `FORMAT_GUIDANCE` then
followed as unattributed instruction: *"Trades are disabled in this format — never suggest or
evaluate a trade here."* A mis-set toggle would have the panel refuse whole categories of
advice and cite it as league fact. **This is the highest-consequence user override in the app**
and it was the only unlabelled one. **Verdict: REPAIR (R14)** — mechanical under the convention
the same function already applies three times over.

### 16.5 A user's own claim can become a durable numeric input under a third party's name

**STATUS: MISSING**
`MODERATOR_SYSTEM_PROMPT` admits a SOURCE FINDING from either the Beat Tracker's live search
**or the user's own hand-captioned reference material** — and says so explicitly, in one breath:
*"Whichever way it entered the debate…"*. `bot_research.add_finding`'s record has no field for
which. Its keys are exactly `id, ts, date, player_name, source, claim, rank, composite_impact,
conviction, question, league_id` — verified by set comparison, not by eye.

A rank-bearing finding then feeds `composite_player_score` at weight 0.5, and
`data/baseline/bot_research.json` is **not gitignored** (unlike the per-league stores), so a finding written there would be committed. [CORRECTED IN §21.7: I wrote "is git-tracked" here on the strength of `bot_research.py`'s own docstring. The file does not exist, is not tracked, and `git log --all` shows it was never committed. The mechanism is real; the state has never been reached.]
So: user uploads a screenshot, captions it, the panel doesn't dispute it, and the user's own
claim becomes a committed numeric input to the app's blended valuation, attributed to ESPN.

The origin *distinction is deliberately collapsed by the prompt*, which makes this a contract
question rather than a bug: recording it means adding a field to the Moderator's structured
block. **Verdict: SURFACE (#106).** Adjacent to #97, not part of it.

### 16.6 "Can a user correction trigger investigation without directly becoming canonical?" — yes, twice, and one of them erased itself

**STATUS: EXISTS (two mechanisms) — one repaired (R13)**

**The pending-upload gate is the app's best §16 artifact.** A rankings file whose own text says
"Redraft" while parsing as Dynasty is **held**, not merged. The user gets the parser's own
example row (deterministic, no API call), can optionally ask the Moderator, and then chooses
between three fixed buttons. The button wording is pinned neutral *on purpose*, with the
reasoning in the source: *"A parser that silently mislabels a column and a Moderator opinion
that gets rubber-stamped without real scrutiny fail the same way: nothing catches the error."*
An investigation that does not become canonical by itself — exactly what §16 asks for.

**`todo_log` is the second, and it is the app's only place where a human directly overturns an
AI conclusion.** A bot can only propose `likely_resolved` with a reason; the user confirms
(`resolve_todo`) or rejects (`reopen_todo`, the "↩️ Keep Open" button). The module states the
rule: *"Resolved/dismissed items are archived (kept, with a reason and date), never destroyed."*

**It did not hold for the rejection.** Demonstrated before the repair: after
`mark_likely_resolved` → `reopen_todo`, the stored entry was byte-identical to one no bot had
ever spoken about — `status` back to `active`, `resolution_reason` cleared to `""`, nothing
else touched. Neither the claim nor the rejection of it survived. `mark_likely_resolved` also
wrote no timestamp of its own, so even a *surviving* proposal could not say when it was made.
The asymmetry ran exactly backwards: `revise_todo` — **the bot** editing **the user's**
objective text — archives the prior text in `revisions`; the user overruling the bot archived
nothing. **Verdict: REPAIR (R13)** — mechanical under this module's own stated rule.

**Correction to a finding I did not publish:** I first read `resolve_todo`'s
`if reason: entry["resolution_reason"] = reason` as a second erasure — the user's confirmation
note overwriting the bot's proposed reason. It cannot happen. `app.py` calls `resolve_todo`
with a reason only from the `else` branch (`status != "likely_resolved"`), where no proposal
exists; the "✅ Confirm Done" path passes no reason at all, which the docstring already
identifies as the "don't override it" case. The UI wiring disproves the source reading — the
fourth time this audit's most tempting finding has been one read short.

### 16.7 Replay

**STATUS: MISSING**
`decision_log` stores the question, the parsed verdict, the full Moderator text, and (since R10)
the provider and model. It stores **nothing about the state the overrides were in**: which
aliases existed, which format override was set, which external CSVs were loaded, which
attachments were in scope. §16's *"can replay reproduce the decision with the override exactly
as it existed?"* is **no**, and not marginally so — the Prytaneum path has no snapshot at all,
where the Draft Room at least has `PickSnapshot`'s INPUT-STATE STAMP (§11.6).

This **widens #92** rather than adding a new item: what needs identifying is not just the draft
snapshot but the decision context, and the Prytaneum half of it currently has none.

### 16.8 Can the Moderator say its answer depends on a user override?

**STATUS: PARTIAL — channels exist, nothing directs them here**
The structured block has `CONVICTION: Speculative` (*"the underlying evidence is thin"*) and
`RISK`, and REFERENCE MATERIAL already tells the panel a caption is unverified. So the Moderator
*can* express reliance in prose. What does not exist is any instruction to do so specifically
when the answer turns on a user-supplied override, and nothing in the machine-readable block
distinguishes that case — so a downstream consumer of the verdict cannot filter for it.

R14 adds this for the format override only, because that one is a factual claim about the
league presented as detected fact. Generalizing it — a block field, or a standing instruction —
changes the Moderator's contract and its `chair_prompt_fingerprint`. **Verdict: SURFACE (#108).**

### 16.9 Two live items whose premises §16 changes

- **#102 (cross-session lost update) widens.** It was scoped to per-league stores.
  `save_alias`, `remove_alias` and `set_format_override` are the same read-modify-write shape on
  **global** files, and `player_aliases.json` is one of the three that feeds valuation. The
  lost-update window is no longer only "two sessions in one league" but "two sessions at all".
- **#99 (truncation detection) sharpens.** `llm_engine`'s own `MAX_TOKENS` comment already
  notes that truncation silently breaks the TODO tracker, decision log and research feed. §16
  adds *which* lines those are: `TODO LIKELY RESOLVED` and `SOURCE FINDING` sit at the very end
  of the block, so the first thing a truncated Moderator reply loses is precisely the
  human-in-the-loop layer — the proposal the user was supposed to rule on.

#94, #100, #101, #104 and #105 are untouched by §16.

### 16.10 Corrections to my own §16 readings

1. **`resolve_todo` does not lose the bot's reason** — see 16.6. Disproved by the call sites.
2. I expected a numeric override UI (a "custom value" box) somewhere, on the strength of §16's
   own wording. There is none — measured, not assumed: zero `number_input`/`slider`/`toggle`
   calls in the entire app. The section's framing does not match this app's shape, and saying
   so is the honest finding rather than manufacturing an equivalent.
3. I considered labelling to-do origin (`source`: moderator vs manual) in `build_context`,
   which the record already carries and the UI already shows as 🤖/✍️. Rejected as a repair:
   unlike the format override, an objective is not a factual claim about the league, and
   telling the panel which objectives the user wrote would change how it weighs them — a
   behavioural change, not an attribution fix. Folded into #108's decision surface.

## Pass 12 summary

| § | question | status | verdict |
|---|---|---|---|
| 16.2 | CDME-variable override isolated? | **N/A by construction** | no override surface exists |
| 16.3a | alias override attributed downstream? | **MISSING** | SURFACE (#107) |
| 16.3b | user CSV distinguishable from vendor export? | **MISSING** | DOCUMENT / #107 |
| 16.4 | user context distinguished from canonical? | **EXISTS**, 1 exception | **REPAIR (R14)** |
| 16.5 | finding origin (user vs search) recorded? | **MISSING** | SURFACE (#106) |
| 16.6 | correction triggers investigation, not canon? | **EXISTS ×2** | **REPAIR (R13)** |
| 16.7 | replay with the override as it was? | **MISSING** | widens #92 |
| 16.8 | Moderator can flag override dependence? | **PARTIAL** | SURFACE (#108) |

**Does anything clear the bar for a production change?** Two things did.

**R13 — `todo_log`: the rejection survives.** `mark_likely_resolved` now appends the proposal to
a `proposals` history with its own timestamp; `reopen_todo` / `resolve_todo` / `dismiss_todo`
close the pending entry as `rejected` / `accepted` / `superseded_by_dismissal` rather than
clearing it. Legacy entries written before the field existed close cleanly and fabricate
nothing. Justified by the module's own "archived, never destroyed" rule and by `revise_todo`'s
existing implementation of exactly this pattern one function away.

**R14 — `build_context`: the manual format override announces itself.** One guarded paragraph,
emitted only when an override is actually set, placed *before* `FORMAT_GUIDANCE` so the caveat
arrives ahead of the imperatives it qualifies. Justified by the convention the same function
already applies to reference material, past outcomes and pins.

Everything else in §16 needs a decision this audit does not get to make.

**Ranked follow-ups**
1. **#106** — a rank-bearing research finding cannot name its origin, and feeds a would-be-committed
   composite input. Needs a Moderator-contract field, or a rule that a finding whose origin
   can't be named doesn't carry a rank.
2. **#107** — the three doors from user input into valuation (alias, rankings upload, external
   CSV) carry no when/who/why, and the alias marker is dropped before the decision boundary.
   Schema + boundary decision.
3. **#108** — no chair channel for "this answer rests materially on your own override". Contract
   decision; would also settle the to-do-origin question from 16.10.
4. **UI for R13.** The proposal history is recorded and nothing renders it. Follows the same
   record-now-display-later precedent as R9/R10/R11; a "🔎 Proposal history" popover mirroring
   the adjacent revision-history one is the obvious shape when someone wants it.

## Pass 13 — §17

**Scope:** Build Guide v2 §17 (cross-version schema, provider and live-upgrade safety).

**Baseline:** `7908136` on `ui-authority-pass`; `main` frozen at `9fb5102`. One production file
modified (`bot_benchmark.py`) — R15. #91–94, #96–108 remain queued; #99 stays ahead of #94.

**Headline: this system has exactly one artifact that can say what it is — the benchmark report,
via §5's content fingerprints — and nothing else has any identity at all. No stored record
carries a version field, 31 of 31 stored trial records carry no version/commit/date,
`requirements.txt` pins nothing, and all three default model ids are floating aliases whose
served weights the app throws away unread. The absence of `__version__` turned out to be a
considered decision rather than an oversight (see the correction in 17.1), which narrows the
finding without softening it: the repo's own answer to version identity works, and has been
applied once.**

### 17.1 The version inventory, measured

**STATUS: MISSING beyond one artifact — and the shape of the gap is not what it looks like**
AST-walked every production module (excluding `test_`/`run_`/`compare_`/`verify_`/`cdme_`
scripts) for `__version__`, `SCHEMA_VERSION`, `VERSION`, `CDME_VERSION`, `ENGINE_VERSION`:
**zero occurrences.** `requirements.txt` carries exactly one bound in the whole file —
`streamlit>=1.34`, with a comment naming the widget that needs it. `anthropic`, `openai`,
`google-genai`, `pandas`, `scipy` and `pypdf` are unbounded, and there is no lockfile,
`pyproject.toml`, `Pipfile` or constraints file of any kind.

So §17's *"are active operations pinned to CDME/schema/context/provider/model versions?"* is
**no on every axis**, and *"can provider SDK, tokenizer, tool interface, pricing, or model
behavior changes be tied to explicit versioned audit events?"* has no mechanism to answer.

**Correction to this section's own first framing.** I drafted 17.1 as "no version constant
exists, therefore add one." `bot_benchmark._fingerprint`'s docstring disproves the implied
recommendation: a content hash is used *"deliberately … rather than a hand-maintained version
number: a number has to be remembered and drifts out of sync with the thing it names, whereas
this cannot disagree with the battery, rubric, or chair prompt it was computed from."* The
version-number **shape was considered and rejected**, for a good reason, in the one place this
app needed identity. The absence of `__version__` is therefore a decision, not an oversight,
and the test covering it is an enforcement of that decision rather than a characterization of a
gap — a version constant appearing would be a reversal to weigh, not progress.

What survives the correction is narrower and sharper: **the fingerprint approach is the
established answer and has been applied to exactly one artifact.** The CDME coefficient set,
every record schema, and the chair contracts outside the benchmark still have no identity of
any kind — no hash, no number, nothing. **Verdict: SURFACE (#111)**, framed as "extend content
hashing to what else needs identity", not "introduce version numbers". Dependency pinning stays
separate and cannot even be *verified* from this environment — the three provider SDKs are
deliberately not installed here (every provider call in the suite is stubbed), so any pin I
wrote would be untested. Same posture as #88.

### 17.2 What answered is not what was asked for

**STATUS: MISSING — and this is the section's sharpest finding**
All three default model ids are **floating aliases**: `claude-sonnet-5`, `gemini-2.0-flash`,
`gpt-4o`. `CLAUDE_MODEL`'s own comment records that it replaced *"a now-retired dated
snapshot"* — the codebase moved deliberately from a pinned snapshot to an alias, for good
availability reasons, and inherited the alias problem with it.

Every provider's response object carries the model that actually served the call.
**All three callers extract text and discard the object** — verified by AST over
`_call_claude` / `_call_gemini` / `_call_openai`: every `return` in all three is a string
expression; none hands the response out. So §17's last question — *"what happens if a provider
silently aliases a model name to a newer underlying model?"* — has the answer: **nothing
notices, and every audit record reads identically before and after.**

**Correction to my own first reading.** I initially wrote this up as `DebateResult.role_models`
and `decision_log`'s R10 fields *claiming* to record "what actually answered" while recording
the request. Re-reading R9's comment in context, the contrast it draws is
record-at-the-time versus re-derive-from-live-config-later, not
requested-versus-served. The fields are honest; the response object is what is missing. The
finding is a gap in the callers, not a mislabelled field.

**Verdict: SURFACE (#109).** Capturing the served model changes what `PROVIDER_CALLERS`
returns — today a plain `str`, which the entire fail-soft `⚠️` convention (§14) depends on —
and requires verifying three different SDKs' field names against SDKs that are not installed
here. Blocked on the same thing as #88.

### 17.3 An object that outlives its class

**STATUS: EXISTS — it fails loudly, which is the right answer, and it was worth checking**
Streamlit's `LocalSourcesWatcher` **evicts edited local modules from `sys.modules`** so they
re-import on the next rerun — read directly out of the installed streamlit 1.61 source, not
assumed. `st.session_state` survives that. So a `PickSnapshot`, `DataMerger` or
`PickDebateResult` held in session state across a code edit is an instance of a class
definition that no longer exists. Measured: `isinstance(held, ps.PickSnapshot)` is **False**
after a module reload, and `type(held) is ps.PickSnapshot` is **False**.

What happens when such an object reaches a consumer:

| consumer | old-schema snapshot |
|---|---|
| `pick_synthesis.snapshot_is_current` | `AttributeError: 'OldPickSnapshot' object has no attribute 'picks_consumed'` |
| `draft_board_ui.serialize_snapshot` | `AttributeError: ... has no attribute 'decision_regime'` |

**Loud is correct** — the alternative is reading `decision_regime == "contested"` off a
snapshot that never said so. Pinned as an enforcement test rather than left to luck, together
with the fact that both stamp fields default to `None` and never to a value that could pass for
a real one.

**Correction to my own probe.** My first attempt deleted the fields from a *current* instance's
`__dict__` and reported that the consumers returned OK. That was wrong: dataclass fields with
defaults live as **class** attributes, so the deleted instance attributes fell back to the
current class's defaults. A genuinely old instance keeps `__class__` pointing at the old class
object, which has neither the field nor the default. The corrected probe — an actual older
class definition — produced the `AttributeError`s above. Recorded because the first result was
the more alarming one and would have been reported.

### 17.4 Old audit records stay readable — by defensive `.get()`, not by design

**STATUS: EXISTS — undefended until now**
§17's *"can old audit records still be interpreted after schema changes?"* is **yes**, and the
reason is that every store reads with `.get()`: `todo_log` 17, `bot_research` 15, `decision_log`
12, `bot_benchmark` 11, `attachments` 4, `league_prefs` 6. Fed the barest record a much older
version could plausibly have written, `load_todos`, `search_archived`,
`search_decisions_with_outcomes`, `set_outcome`, `findings_for_context`,
`load_bot_research_as_external` and `list_attachments` all cope without raising.

This is a real property held together by a convention that is lost one bracket at a time — a
planted `entry["text"]` in `search_archived` breaks it immediately. Now covered by tests.

### 17.5 An upgrade can silently change what a stored context means — measured twice

**STATUS: MISSING — both instances demonstrated**

**(a) A renamed external export silently re-scores players.** `_EXTERNAL_PERCENTILE_RULES` maps
`(source, file)` → the field to percentile. Nothing reconciles that table against what is on
disk. Renaming one tracked filename — exactly what happens when a vendor renames its export —
**moved 31 of 131 sampled composite scores** (median |Δ| **4.3** on a 0–100 scale, largest
13.6) and made **4 disappear entirely**, with **no exception, warning or log**. The file stays
on disk, still loads into `external_values`, still counts as a loaded source; it simply stops
feeding the composite. 887 of 2,600 external rows already carry no percentile rule today, some
deliberately (ESPN's redraft list, FantasyPros' best-ball list — both documented as excluded on
purpose), which is precisely why an automatic warning is not mechanical: distinguishing a
deliberate exclusion from an accidental orphan is a policy call.
The one unambiguous half — a rule naming a file that is *not there* — is now an enforced test.

**(b) A status the running code does not recognise makes a record invisible everywhere.** All
five production `load_todos` calls pass a status filter. A record whose `status` sits outside
both vocabularies appears in no view at all: not the active list, not the archive, not the
archive search, not the header count, not `build_context`. It is not deleted and raises
nothing. Two upgrades produce it — renaming a status, and reading a file written by a newer
version. This sits directly against `todo_log`'s own stated rule that archived items are *"kept
… never destroyed"*, since a record invisible in every view is functionally destroyed.
**Verdict: SURFACE (#110)** for both — where an unrecognised record should surface is a UI
decision.

### 17.6 The benchmark is the one versioned audit event this app has

**STATUS: PARTIAL — improved (R15)**
§5's R95 gave every report a `battery_fingerprint`, `rubric_fingerprint` and
`chair_prompt_fingerprint`, and `comparable_history` uses them to answer "has this model
degraded?" honestly. That is genuinely the mechanism §17 Q6 and Q7 are asking for, for the one
dimension it covers: **model behaviour under a fixed chair contract**.

What it could not say was what else the run was conducted under. Two things move without a
character of this repo changing, and both change what a candidate can produce:
`llm_engine.MAX_TOKENS` (which decides whether a chair's structured block survives at all —
see the §99 truncation thread) and the installed provider SDK version (defaults, retry
behaviour, tool encoding, response assembly). **Verdict: REPAIR (R15)** — record both, under
R95's own stated rule that a report must say what it "was actually conducted under."

Deliberately **recorded, not gated on**: `comparable_history` still keys off the three
fingerprints alone. Deciding that a token-budget or SDK change makes two runs incomparable is a
judgment about what counts as the same experiment, and that judgment belongs to #96, not to
this pass. The restraint is itself pinned by a test.

### 17.7 The regression corpus cannot say which engine produced it

**STATUS: MISSING**
`data/draft_simulation_trials/` holds **31** stored experiment and trial records — the
deterministic corpus §19 will ask about. Scanned for any top-level key matching
`commit|sha|version|baseline|ran_at|generated|timestamp|date`: **one file matched, and it was a
false positive** — `rookie_roster_context_experiment.json`'s `baseline_gap` / `baseline_top` /
`baseline_second` are that experiment's own measurements, not a version stamp. So **31 of 31
carry no version identifier of any kind.** Eighth occurrence of the substring-artifact class,
caught by reading the hit.

The project does track this, by convention, in analysis-script filenames
(`compare_baseline_pre_post_95d2111.py`, `run_95d2111_effect_report.py`). Folded into #111 —
stamping the trials means calling git from ~20 `run_*.py` scripts and depends on how #111
answers "what is a version".

### 17.8 A third instance of the compute-then-drop class

**STATUS: noted, not repaired**
`DataMerger.reconciliation_conflicts` is populated on every load (it existed to stop 1,084
per-load field conflicts being resolved silently, per #83) and is **read by nothing in
production** — only by `test_reconciliation_boundary.py`. That makes three: `waiting_cost`
(#57), `_match_path`/`_match_verified` (§16.3), and now this. Naming the class matters more
than any one instance: **this codebase reliably computes the diagnostic and reliably fails to
route it anywhere a reader will see it.** It also means "put the percentile-rule drift into
`reconciliation_conflicts`" would have been adding a second unread list, which is why 17.5(a)
is surfaced rather than repaired.

### 17.9 Corrections to my own §17 readings

1. **"No version constant" is not a gap** (17.1) — the biggest of the four, and found last,
   while reviewing the R15 diff. `_fingerprint`'s own docstring records that hand-maintained
   version numbers were considered and rejected in favour of content hashes. The section had
   been written the other way round; the headline, the test's classification and #111's framing
   all changed. Ninth occurrence of the one-read-short pattern, and the first to overturn a
   section headline after it was written.
2. **The stale-class probe** (17.3) — first result was wrong, corrected, both recorded.
3. **`role_models` / R10 are not mislabelled** (17.2) — I nearly reported a contradiction that
   a careful reading of R9's comment disproves.
4. **The trial-corpus scan's single hit was a false positive** (17.7).
5. **§15's appendix conflated two scans** — it described the no-retry guarantee as
   "word-bounded with comments excluded", which is true of the *budget-primitive* scan and not
   of `test_no_retry_or_backoff_exists`, a raw whole-source substring scan. R15's first draft
   said "retry behavior" in a comment and the full suite failed on it. Comment reworded, test
   left as-is with its docstring corrected.
6. **A probe harness's `finally` does not survive an external kill.** The first probe batch hit
   a 2-minute tool timeout mid-run and left P9's mutation (`gpt-4o` → `gpt-4o-20240513`) in
   `llm_engine.py`. Caught by the `git status` check that follows every probe batch, reverted,
   and the remaining probes re-run in the background instead. Recorded because the check is the
   only reason it did not reach a commit.

## Pass 13 summary

| § | question | status | verdict |
|---|---|---|---|
| 17.1 | any version identity at all? | **MISSING** beyond the benchmark's hashes | SURFACE (#111), reframed |
| 17.2 | is the served model knowable? | **MISSING** | SURFACE (#109), blocked |
| 17.3 | object outliving its class | **EXISTS** — fails loudly | **now enforced** |
| 17.4 | old records still interpretable? | **EXISTS** — by `.get()` | **now enforced** |
| 17.5a | renamed export silently re-scores | **MISSING** — 31/131 moved | SURFACE (#110) |
| 17.5b | unknown status invisible everywhere | **MISSING** | SURFACE (#110) |
| 17.6 | benchmark identifies its version? | **PARTIAL** | **REPAIR (R15)** |
| 17.7 | regression corpus versioned? | **MISSING** — 31/31 | folded into #111 |

**Does anything clear the bar for a production change?** One thing did.

**R15 — `bot_benchmark`: a report records the operating envelope it ran under.** Adds
`max_tokens` and `provider_sdk_versions` (via `importlib.metadata`) to every stored report. An
SDK that is not installed is **omitted**, never recorded as a version the run did not have —
the absence contract, and the same rule `decision_log.log_decision` applies to provider/model.
A metadata lookup that raises costs nothing: a benchmark run is not lost to a packaging quirk.
Justified by R95's own words — a report must say what it "was actually conducted under" — and
by §17 Q7 asking for exactly this artifact by name. Not gated on, by design.

Everything else in §17 needs either a decision or an environment this audit does not have.

**Ranked follow-ups**
1. **#111** — content hashing is this repo's own answer to version identity, and it covers one
   artifact. Extend it to the CDME coefficient set, the record schemas and the chair contracts;
   stamp the 31 trial records. Dependency pinning is a separate, environment-blocked question.
   The one that has to be answered before most of the others can be.
2. **#109** — the served model is unrecoverable because the response object is discarded, and
   all three default ids are floating aliases. Blocked on the provider SDKs, like #88.
3. **#110** — two demonstrated silent-meaning-change paths: a renamed export re-scores players,
   an unrecognised status hides a record. Both need a surfacing decision.
4. **The compute-then-drop class** (17.8) — three instances now. Worth one decision about where
   diagnostics go, rather than three separate ones.

## Pass 14 — §18

**Scope:** Build Guide v2 §18 (data semantics — what does the system know?).

**Baseline:** `c045f8e` on `ui-authority-pass`; `main` frozen at `9fb5102`. Two production files
modified (`data_merger.py`, `app.py`) — R16. #91–94, #96–111 remain queued; #99 stays ahead of
#94.

**Headline: the absence contract is one bit deep, and it is excellent at that depth. "This has a
value" versus "this does not" survives every calculation, ordering and consumer, defended by
`test_absence_survives_consumers.py`'s EXCLUDE / PROPAGATE / ORDER LAST rule. §18 asks the second
bit — WHICH absence — and the codebase computes exactly that distinction, on 500 of 764 canonical
rows, in the one place it exists, and then dropped it at its own first consumer.**

### 18.1 The eight states, and which of them this system can express

**STATUS: PARTIAL — measured, not read off names**

| §18 state | representation | reaches a consumer? |
|---|---|---|
| unknown | `proj_3yr_state == "unknown"` + reason; `None` on bpa/waiting_cost; `composite → None` | **now yes** (R16); values yes |
| not applicable | `proj_3yr_state == "not_applicable"` + reason | **now yes** (R16) |
| unavailable | `⚠️` fail-soft strings; `UNAVAILABLE_REPORT` (R12); DATA AVAILABILITY "NOT LOADED" | yes |
| stale | freshness manifest (STALE / EGREGIOUSLY OUTDATED); `_recency_weight`; `snapshot_is_current` | yes, except the certifier (#101) |
| intentionally omitted | `replacement_levels` OMITTED keys; ESPN/best-ball excluded from the composite | yes, as documented absence |
| uncertain | `confidence` (from `bpa_source`); `CONVICTION`; `horizon_sensitivity`; composite `weight`/`pool_size` | yes |
| disputed | resolved or excluded, never carried: `_drop_contested_identities` drops **both**, `match_verified` is dropped at the board (#107), `reconciliation_conflicts` is write-only (§17.8) | **no** |
| never checked | **nothing** — AST scan over every production module for `unchecked`/`not_checked`/`never_checked` string constants returns zero | **no** |

Six of eight are expressible; two are not. "Disputed" is a deliberate architectural choice
(this system resolves or declines rather than carrying a contested value) and is defensible.
"Never checked" is simply absent.

### 18.2 The one place kinds of absence are distinguished — and where it stopped

**STATUS: was MISSING at the boundary — repaired (R16)**
`data_merger._assign_horizon_state` computes three states with a reason on every non-known row,
and states its own purpose plainly: *"Three states because the old two could not distinguish
'this position has no career arc' from 'this player has one and we do not have it' — and that
is exactly the distinction that decides whether restoring the data is even possible."*

Measured on the committed baseline:

| state | rows | share |
|---|---|---|
| `known` | 264 | 34.6% |
| `unknown` | 468 | 61.3% |
| `not_applicable` | 32 (all DEF) | 4.2% |

And the reasons are genuinely discriminating, not boilerplate — K's is *"no multi-year figure on
the **sleeper_transcribed** basis that prices this position"* (the file that prices kickers
publishes none), DB's is *"no multi-year figure from **any source carrying this player**"*. Two
different claims, both true.

**Grepped across the whole repo, `proj_3yr_state` and `proj_3yr_reason` appeared in
`data_merger.py` and in tests, and nowhere else.** `merge_player`'s field whitelist did not carry
them, and it drops `proj_3yr` itself when absent — so both states arrived at every consumer as
the identical missing key. Demonstrated on real rows before the repair:

```
producer state=unknown         -> consumer sees {'proj_3yr': None, 'proj_3yr_state': None, ...}
producer state=not_applicable  -> consumer sees {'proj_3yr': None, 'proj_3yr_state': None, ...}
DEF 'P Eagles' vs DB 'C Conner': keys that could tell them apart -> NONE
```

Two near-opposite claims — *restoring this is impossible* and *restoring this is possible and
worth doing* — were indistinguishable for 100% of the 500 rows the distinction applies to.
**Verdict: REPAIR (R16).** See below on why this one was routed rather than surfaced.

### 18.3 Five of six absence-namers reach a consumer; the sixth was the only one that named a kind

**STATUS: EXISTS — now pinned**
The codebase names absence in six independent places, and it is good at it:
- `UNAVAILABLE_REPORT` / `_report_for_handoff` (R12) — a failed chair's slot is relabelled
  *"MISSING information, never … a finding that there is nothing to report"* for the next chair.
- `replacement_levels` — a position below whole-slot demand has its key **OMITTED**, and the
  docstring says callers must read absence as such, *"never as zero and never as rank 1"*.
- `_attach_waiting_cost` — *"None (not zero) … zero would read as 'waiting is free' — the most
  dangerous possible wrong answer here."*
- `INCOMPLETE_PLAYER_PROFILE` — a named constant for "every loaded source was checked and none
  had a number", explicitly *"a deliberate, honest state, not a blank/missing field."*
- `TeamDiagnostics.replacement_level_unpriced` — a **count of the absent, reported beside the
  value rather than folded into it**. This is the precedent R16 follows.
- `proj_3yr_state` / `proj_3yr_reason` — the only one that says *which kind*, and the only one
  that reached nothing.

### 18.4 An AI-generated claim cannot silently become authoritative — measured

**STATUS: EXISTS — a genuine protection, now pinned**
Planted a finding end to end and reverted it. A panel-vetted claim *does* reach the deterministic
composite, and every step of the way it is labelled and throttled:

```
composite BEFORE the AI claim: 97.8      composite AFTER: 97.8
  dynastyprocess  weight 0.812   pool 698
  fantasypros     weight 0.871   pool 552
  keeptradecut    weight 0.609   pool 463
  bot_research    weight 0.025   pool   1      <- 24x below the smallest structured source
```

The `COMPOSITE_MIN_TRUSTED_POOL_SIZE` guard is doing the work: a one-row pool always ranks its
only member at the 100th percentile, so its weight is scaled by `pool_size / 40`. The claim moved
a real composite by **0.0**. The record says `composite_impact: "low-weight input"` (or `"none"`
for a qualitative claim); the frame labels it `source_name: "bot_research"` with the cited outlet
preserved separately as `cited_source`; `describe_external_value` renders it *"ESPN via panel
research"*. The cited outlet never becomes a composite source in its own name.

So §18's *"can an AI-generated claim ever silently upgrade itself from advisory context to
authoritative data?"* is **no** — it can become an input, never silently and never with force.
Relative comparisons are barred structurally (no `_EXTERNAL_PERCENTILE_RULES` entry at all).

### 18.5 Does every noncanonical fact retain origin, timestamp, confidence, status?

**STATUS: EXISTS — more completely than expected**

| noncanonical fact | origin | timestamp | confidence | status |
|---|---|---|---|---|
| research finding | cited source ✓ (but not user-vs-search — #106) | `ts`/`date` ✓ | `conviction` ✓ | `composite_impact` ✓ |
| composite component | `source` ✓ | `source_date` ✓ | `weight` + `pool_size` ✓ | — |
| board row | `bpa_source` ✓ | — (snapshot-level only) | `confidence` ✓ | — |
| attachment caption | user ✓ | `uploaded_at` ✓ | — | "claim to weigh" ✓ |
| decision verdict | provider/model ✓ (R10) | `ts` ✓ | `conviction` ✓ | `outcome` ✓ |

The one structural gap: a **board row carries no date**. It can say which anchor priced it, not
when that anchor was measured. `PickSnapshot`'s INPUT-STATE STAMP covers freshness at the
snapshot level, which is the right granularity for the decision — noted, not repaired.

### 18.6 What happens when user-provided information contradicts CDME

**STATUS: EXISTS — disagreement is shown, not resolved, which is the right answer**
`build_context` hands the panel every source's own number side by side and instructs it to
*"note where sources disagree on which of two players is worth more, since that's more
informative than any single number alone"*, with each scale's incomparability spelled out.
Cross-source contradiction is therefore surfaced as evidence rather than silently arbitrated.

The asymmetry: **intra-source contradiction is recorded and shown to no one.**
`DataMerger.reconciliation_conflicts` captures every field-level disagreement a load resolves —
1,084 of them per load, per #83 — and §17.8 established it is read by nothing in production.
Same finding, different lens; folded into the compute-then-drop class rather than raised again.

### 18.7 Corrections to my own §18 readings

1. **`_confidence`'s `35.0` fallback is not a defect.** I drafted it as an unknown anchor
   silently collapsing to a known confidence tier. `bpa_source` is assigned unconditionally and
   only ever takes one of the four values `CONFIDENCE_BY_SOURCE` scores, so the fallback is
   unreachable. Checked before reporting; now pinned by a test so it stays unreachable.
2. **I nearly added a fifth unread diagnostic.** The first draft of R16 stopped at carrying the
   state through `merge_player`. That would have moved the drop point one module later and made
   §17.8's compute-then-drop list longer, which is the exact reasoning I had just used to *decline*
   repairing §17.5(a). Caught, and the repair extended to a real consumer before shipping.
3. **The Free-Agent-table test was passing by skipping.** The first version checked the
   "no such column" guard against `merger.free_agents`, which is empty in this baseline, so it
   skipped rather than asserted. Replaced with a hand-built stateless frame that exercises the
   guard for real.

## Pass 14 summary

| § | question | status | verdict |
|---|---|---|---|
| 18.1 | are the eight states expressible? | **6 of 8** | disputed: architectural; unchecked: SURFACE (#112) |
| 18.2 | do kinds of absence survive the producer? | **was MISSING** | **REPAIR (R16)** |
| 18.3 | do absence labels reach consumers? | **EXISTS** (5 of 6) | now pinned |
| 18.4 | can an AI claim silently become authoritative? | **NO — protected** | now pinned |
| 18.5 | origin/timestamp/confidence/status on noncanonical facts | **EXISTS** | board row carries no date — noted |
| 18.6 | user info contradicting CDME | **EXISTS** cross-source | intra-source is §17.8's class |
| 18.7 | does the kind-of-absence reach the board? | **MISSING** | SURFACE (#112) |

**Does anything clear the bar for a production change?** One thing did, and it is the judgment
call of this section — flagged as such.

**R16 — the three horizon states survive their own producer, end to end.**
`merge_player` now carries `proj_3yr_state` and `proj_3yr_reason` (tables with no such column are
untouched by the existing `field in match.index` guard), and a new pure helper
`data_merger.horizon_gap_lines` turns them into context lines that `build_context` emits under the
roster table — counts per state, with the engine's own reason strings **verbatim**, and nothing at
all when nothing is absent. It states which absence each blank is and says nothing about what to
conclude from it.

**Why routed rather than surfaced.** Carrying the field alone would have made a fifth
compute-then-drop instance. Routing it changes what the panel reads, which is a behavioural
change — the reason this is the section's judgment call rather than a mechanical certainty. It
was taken because three established precedents cover the shape exactly:
`replacement_level_unpriced` (a count of the absent, reported beside the value rather than folded
into it), `INCOMPLETE_PLAYER_PROFILE` (build_context already names an honest absence rather than
leaving a blank), and `_assign_horizon_state`'s own stated purpose, which a stranded field
defeats. If that reads as too far, the revert is one line in `build_context` and the carrying
half stands on its own.

**Ranked follow-ups**
1. **#112** — the kind-of-absence stops at the roster context. The board emits `bpa_source` and
   `confidence` but no reason for anything it lacked, so the distinction does not reach the
   PickSnapshot or the Draft Room debate — the same frozen boundary #107 is parked on. Same item
   carries "never checked", the one §18 state with no representation at all.
2. **#106** (unchanged) — a research finding still cannot say whether the user's screenshot or a
   live search produced it, which is the one hole in an otherwise complete provenance record.
3. **The compute-then-drop class** — now four instances (`waiting_cost`, `_match_path`,
   `reconciliation_conflicts`, and until R16 `proj_3yr_state`). R16 is the first one closed;
   the other three still want one decision rather than three.

## Pass 15 — §19

**Scope:** Build Guide v2 §19 (system integrity, dependencies, periodic baseline auditing).

**Baseline:** `694f2e4` on `ui-authority-pass`; `main` frozen at `9fb5102`.
**No production file was modified.** §19 states *"Do not modify production code during the
audit"* and that was treated as binding: mechanically correctable defects found here are
characterized and parked, not repaired.

**No test file was added either, and that is a methodological choice, not an omission.** §19
audits the audit machinery — the suite's size, composition and reproducibility are among the
things being measured. Adding tests mid-section would change the measurement. Everything below
is read-only measurement plus one planted-and-reverted data probe.

**Headline: the integrity story splits cleanly. What this repo checks, it checks unusually well
— 274 boundary tests across 15 files, a real adversarial data-injection test, a committed
engineering doctrine with a six-link audit chain, zero dangerous primitives in production, one
outbound HTTP surface, and a test baseline that is genuinely reproducible and genuinely
clock-independent. What it does not check, it does not check at all: nothing runs any of it
automatically, nothing pins its inputs, nothing hashes anything, and the documented launch path
upgrades every dependency on every start.**

### 19.1 Code integrity of the deterministic layer

**STATUS: EXISTS — stronger than expected**
Grepped across every production module for `eval(`, `exec(`, `pickle`, `subprocess`,
`os.system`, `__import__`, `shell=True`: **zero occurrences.** The only `exec`-shaped hits are
the word "execute" in prose and `concurrent.futures.ThreadPoolExecutor` — checked, not assumed.

Outbound network in production is **one** surface: `sleeper_client`'s `requests.Session`, plus
the three provider SDKs imported inside their own caller functions. No other `requests`,
`urllib`, `httpx` or `socket` use anywhere. §19's *"unexpected API/tool exposure"* is therefore
enumerable in a sentence, which is the precondition for detecting a change to it.

### 19.2 Can a trusted baseline detect unauthorized source or data changes?

**STATUS: MISSING — no integrity primitive exists**
`hashlib` appears **once** in production: `bot_benchmark._fingerprint`, hashing a battery, a
rubric and a chair prompt (§5 R95). There is no checksum, manifest, signature or content hash
over source files, over `data/baseline/`, or over anything else. §19's *"can a trusted baseline
detect unauthorized source changes … schema/data changes"* has no mechanism to answer, and
*"can dependency and code-integrity checks establish whether a deployed build corresponds to an
approved source revision?"* inherits #111 — there is no build, no version, and no lockfile.

Git is the de-facto integrity layer, and it is a real one for tracked files. It is also the
whole of it.

### 19.3 The test baseline is reproducible — measured, and it survived two hypotheses I expected it to fail

**STATUS: EXISTS**

**(a) Inputs are committed.** Enumerated every `.csv`/`.json`/`.pdf` under the three directories
`DataMerger` actually loads and cross-checked each against `git ls-files`: **28 files, 28
tracked, 0 untracked.** A fresh clone at a given commit loads exactly the data that commit
declares. I expected to find drift here and did not.

**(b) Assertions are clock-independent.** Only **5 of 75** test files mention time at all, and
every recency/staleness assertion uses a **fixed** input (`recency_grade(7)`, a hardcoded
`"2026-08-25"`), never the live clock against the live baseline.

**(c) The numbers themselves are time-invariant.** I predicted composite scores would drift as
`_recency_weight` decays. Measured by advancing the clock inside `data_merger` at +0/+30/+90/+365/+1095
days over 90 scored players: **max |Δ| = 0.00 at every horizon.** The decay is a common factor
in a weighted average and cancels. Hypothesis wrong, recorded.

**(d) The test count fully reconciles.** 1,455 `def test_*` declarations + 2 inherited-and-rerun
methods (`SuperflexRookieDraftRosterContextTieredGateTests` subclasses
`RookieDraftRosterContextTieredGateTests` and overrides 1 of its 3) = **1,457**, exactly what the
runner reports. Not a mystery number.

**(e) The suite leaves no residue.** `git status` verified clean after each of five full runs
across §16–§19.

### 19.4 …but its input set is a directory listing, not a manifest

**STATUS: MISSING — demonstrated**
The suite loads *whatever is in* `data/baseline/`, `data/projections/_global/` and
`data/baseline/external/`. `data/projections/**/*.csv` is **gitignored** — it is where the app's
own "External Valuation Sources" and rankings uploaders write. Planted one CSV there and
reverted it:

```
canonical pool rows: before=764  after=766  delta=+2
the planted row is priced by the engine: trade_value=100.0, projection=9999.0
git treats the planted file as: .gitignore:10:data/projections/**/*.csv
a suite class that reads the baseline: OK
```

A fabricated player entered the priced universe, git reported the file as ignored, and the suite
stayed green. **19.3(a) is true today by nobody having uploaded, not by construction.** Two
developers on the same commit — one of whom has used the app — run the same tests against
different data and both see green. **Verdict: SURFACE (#113).**

### 19.5 Nothing runs any of it

**STATUS: MISSING**
There is **no `.github/` directory at all** — no workflow, no CI, no pre-commit, no hook. The
1,457-test suite runs exactly when a human types the command.

The documented launch path is `update_and_run.sh` / `.ps1`, and it is a live drift mechanism:

```
git pull                                  # no signature, no revision pin
pip install -r requirements.txt --quiet   # unbounded versions, no lockfile (§17.1)
streamlit run app.py                      # no test run in between
```

Every launch can silently upgrade `anthropic`, `openai`, `google-genai`, `pandas`, `scipy` and
`pypdf`, and then start the app regardless. §19's *"which checks belong in every deployment
versus periodic deeper audits"* is answered in **prose** (README documents the split between the
fast unittest suite and the by-hand `run_*` drivers) and **nowhere in machinery**.
**Verdict: SURFACE (#113).**

### 19.6 The regression corpus — and a correction to §17.7

**STATUS: EXISTS, differently than §17 recorded it**
§17.7 reported *"31 of 31 stored trial records under `data/draft_simulation_trials/` carry no
version identifier"* and framed them as *"the deterministic corpus §19 will ask about."* The
facts are unchanged; the framing was wrong. `.gitignore` excludes
`data/draft_simulation_trials/*.json` as *"regenerated by run_draft_validation.py /
run_counterfactual_analysis.py, **not source**"*, and README says the same: those drivers are
*"not part of the app or the fast test suite; run by hand, write to
data/draft_simulation_trials/ (gitignored)."* **0 of 31 are tracked.**

So the corpus is not the outputs — it is the **28 committed input files**, and the outputs are
derived on demand. That is a defensible design: `compare_baseline_pre_post_95d2111.py` exists
precisely to regenerate on two revisions and diff. §19's *"can deterministic outputs be compared
against a fixed regression corpus before/after changes?"* is therefore **yes in principle** —
the inputs are fixed and committed, and §17's determinism work (stable sorts, `player_id`
tiebreakers) makes regeneration repeatable — **and unautomated in practice**: nothing runs the
before/after comparison, and nothing pins the inputs it would run against (19.4).

### 19.7 Behavioural baselines for routing, tool use, source selection and chair authority

**STATUS: EXISTS — the strongest artifact in the repository**
**274 tests across 15 `*_boundary.py` files**, 18.8% of the suite:

| file | tests | what it holds |
|---|---|---|
| `test_data_semantics_boundary` | 33 | §18 absence kinds, AI-claim throttling |
| `test_identity_boundary` | 29 | R1–R3 match resolution |
| `test_override_provenance_boundary` | 28 | §16 human-in-the-loop provenance |
| `test_version_boundary` | 26 | §17 envelope, legacy records, class drift |
| `test_reconciliation_boundary` | 23 | §80/#83 field merge |
| `test_research_ingestion_boundary` | 19 | §6 dampeners and admission |
| `test_context_budget_boundary` / `test_research_authority_boundary` | 16 each | §9 / §7 |
| `test_failure_mode_boundary` / `test_temporal_consistency_boundary` | 15 each | §14 / §11 |
| `test_cost_envelope_boundary` / `test_tenant_scope_boundary` | 13 each | §15 / §12 |
| `test_provenance_boundary` / `test_prompt_constant_boundary` | 11 / 10 | §10 / §4+§8 |
| `test_cdme_ingestion_boundary` | 7 | LLM output cannot reach CDME inputs |

`test_cdme_ingestion_boundary` deserves naming: it is a genuine **adversarial data-injection**
test — a deliberately maximally-distorting `bot_research.json` finding is written to disk about
a real baseline player, and CDME's own output for that player is proven **byte-identical**
before and after. That is exactly the control §19 asks for, built before this audit started.

The strongest evidence that this machinery actually detects regression is the audit's own
record: **43 probes planted in real production code across §16–§18 (15 + 13 + 15), every one
failing the intended test and every one reverted.** A guarantee that cannot fail was the thing
this programme kept looking for and did not find here.

### 19.8 What the machinery cannot detect

**STATUS: MISSING**
- **A loosened test.** 7 tests are explicitly named `CHARACTERIZATION` and each carries a
  docstring saying *"delete this test when #N is settled — do not loosen it."* That is human
  discipline. Nothing mechanical distinguishes "the gap was repaired and the test inverted" from
  "the assertion was weakened until it passed."
- **A changed input** (19.4).
- **A changed dependency** (19.5), except by whatever the suite happens to exercise.
- **A vulnerability.** No `pip-audit`, `safety`, Dependabot, SBOM or advisory check of any kind.

**A name trap worth recording**: `run_dependency_audit.py` sounds like a supply-chain check and
is not. It is a **statistical cross-signal correlation audit** — Pearson correlations between
`compute_pick_necessity`'s six components, flagging pairs above 0.5 that might be double-counting
the same scarcity signal. Excellent work, entirely unrelated to packages. A reader auditing this
repo for dependency controls would find the filename and stop.

### 19.9 Doctrine exists, and is not enforced

**STATUS: EXISTS as process**
`ENGINEERING_DOCTRINE.md` (186 lines, committed) is a real periodic-audit mechanism at the
doctrine level: a six-link **required audit chain** (definition → domain of validity → state
transitions → upstream assumptions → downstream consumers → interaction with other quantities),
an **eight-part contract** every load-bearing quantity must answer before entering the engine
(including *"how absence / unknown is represented — and the explicit statement that this is not
the same as zero"*, and *"which consumers are authorized to use it — by name"*), and ten
**standing rules**, two of which this audit has leaned on repeatedly:

> **A test that cannot fail proves nothing.** Assert on behaviour that changes when the code is
> wrong, and prefer a mutation to a re-derivation.
>
> **A docstring can encode a defect.** Several of the findings above were described as correct in
> the docstrings that defined them. Documentation is evidence of intent, never of correctness.

Nothing enforces any of it. `ROADMAP.md` contains no audit cadence, no scheduled re-audit, and
no trigger condition.

### 19.10 Configuration

**STATUS: PARTIAL**
- `.streamlit/config.toml` is theme-only plus `gatherUsageStats = false` — a deliberate privacy
  control, worth crediting.
- `.devcontainer/devcontainer.json` auto-launches with
  `--server.enableCORS false --server.enableXsrfProtection false`. Scoped precisely: that is the
  **Codespaces preview launcher only** — `config.toml` does not set either, and
  `update_and_run.sh` uses Streamlit's defaults. A common Codespaces workaround, committed, and
  worth a deliberate decision rather than inheritance. **Folded into #113.**
- `.env.example` pins the same floating model aliases as production (#109) — consistent, and
  consistently unpinned.
- `.pytest_cache/` exists in a repo whose README says *"no pytest dependency."* It is
  self-ignored (pytest writes its own `.gitignore`), so it is untracked and harmless — noted so
  the next reader does not spend the two minutes I did.

### 19.11 Corrections to my own readings

1. **§17.7's "regression corpus" framing was wrong** (19.6). The trial outputs are gitignored,
   README-documented scratch; the corpus is the committed inputs. Facts unchanged, conclusion
   corrected.
2. **I predicted composite scores drift with the clock. They do not** — max |Δ| 0.00 at three
   years (19.3c). What *does* drift is the baseline's self-described freshness: Recent/Fresh
   today, Aging at +30d, **Stale at +90d and permanently thereafter**, with no refresh path short
   of a code change. A real finding, but not the one I went looking for.
3. **I predicted untracked files were already contaminating the suite. They are not** — 28 of 28
   tracked (19.3a). The hazard is real (19.4) and the current state is clean.
4. **I miscounted the test-file denominator.** Both write-ups first said "5 of 121 test files
   mention time"; the repository has **75** test files. Caught on a verification pass before the
   commit, corrected in both documents. Worth recording because the surrounding claim — that the
   suite is clock-independent — was right, and a wrong denominator inside a correct finding is
   the easiest kind of error to carry forward unchallenged.

## Pass 15 summary

| § | question | status | verdict |
|---|---|---|---|
| 19.1 | code integrity of the deterministic layer | **EXISTS** | zero dangerous primitives |
| 19.2 | trusted baseline detecting unauthorized change | **MISSING** | SURFACE (#113) |
| 19.3 | is the test baseline reproducible? | **EXISTS** | inputs tracked, assertions clock-free |
| 19.4 | is its input set declared? | **MISSING** | SURFACE (#113), demonstrated |
| 19.5 | does anything run the checks? | **MISSING** | SURFACE (#113) |
| 19.6 | fixed regression corpus for before/after | **EXISTS in principle** | corrects §17.7 |
| 19.7 | behavioural baselines | **EXISTS** — 274 tests, 15 files | the repo's strongest artifact |
| 19.8 | can it detect a loosened guarantee? | **MISSING** | SURFACE (#113) |
| 19.9 | periodic re-audit mechanism | **EXISTS as doctrine**, unenforced | SURFACE (#113) |
| 19.10 | configuration controls | **PARTIAL** | devcontainer flags → #113 |

**Does anything clear the bar for a production change?** Several things would have. **None was
made** — §19 forbids it, and that instruction was treated as binding. The three most obviously
mechanical (a checksum manifest over `data/baseline/`, a CI workflow running the suite, upper
bounds in `requirements.txt`) are parked in #113 for the repair pass, not applied here.

**Ranked follow-ups**
1. **#113** — the integrity-and-cadence family: nothing runs the checks, nothing pins their
   inputs, nothing hashes anything, nothing detects a loosened test, and the launch script
   upgrades every dependency on every start. One decision surface, several cheap mechanisms.
2. **#111** (unchanged) — still the prerequisite for tying a deployed build to a source revision.
3. **The baseline's permanent staleness** (19.11.2) — a refresh policy for committed vendor data
   is a product decision, not an integrity one, but §19 is where it becomes visible.

## Pass 16 — §20

**Scope:** Build Guide v2 §20 (live draft validation & behavioral regression).

**Baseline:** `55066fb` on `ui-authority-pass`; `main` frozen at `9fb5102`.
**No production file was modified.** §20 opens *"After the repair sequence and downstream
contract gate…"* — that sequence has not run, so this pass measures the **current** system and
marks which of §20's prescribed validations are blocked on parked work rather than
implementing that work to make them pass.

**Headline: the mechanical layer is flawless across 1,293 production decision points — the
chosen player is `candidates[0]` on 1,293/1,293 picks, zero boards mis-sorted, absence always
ordered last, and three independent OS processes produced byte-identical trajectories. Every
behavioural question §20 asks resolves to the same underlying fact: the pricing signal is
exhausted long before the draft is. Leader TAV falls 187.34 → 0.0 by round 10 of 18, goes
negative at 11, and from round 14 onward every board in every round has zero priced candidates,
so 27.8% of an 18-round draft is decided by a player-id tiebreak.**

### 20.1 Simulations performed

Eight controlled drafts, every pick through the production path
(`pick_synthesis.build_snapshot` → `candidates[0]`, `mode="auto"` — the same contract
`draft_room.simulate_opponent_picks` uses for auto-drafted teams). No provider call occurs
anywhere in this harness; the AI layer is not on the auto-draft path at all.

| trial | league | pool | picks | runtime |
|---|---|---|---|---|
| `kdst_1qb_slot1` | 1QB + K + DEF, half-PPR, 7 bench | 349 | 168 | 904s |
| `kdst_1qb_slot12` | same, first-round order reversed | 349 | 168 | 895s |
| `kdst_superflex` | + SUPER_FLEX | 349 | 168 | 900s |
| `kdst_te_premium` | TE-premium bonus | 349 | 168 | ~890s |
| `kdst_thin_bench` | 2 bench slots instead of 7 | 349 | 168 | 899s |
| `redraft_1qb` | redraft (`settings.type=0`) | 349 | 168 | 881s |
| `idp_league` | DL/DL/LB/LB/DB/DB/IDP_FLEX | 764 | 168 | 1281s |
| `kdst_deep18` | 18 rounds — crosses `UPSIDE_MODE_DEFAULT_ROUND=15` | 349 | 216 | 511s |

**The shipped drivers cannot run §20's first two checks.** `run_draft_validation.py` hardcodes
`POSITIONS = ("QB","RB","WR","TE")` and `run_idp_draft_validation.py` adds DL/LB/DB — **neither
includes K or DEF at all.** §20's opening check is about kickers and defenses. A K/DEF-inclusive
pool had to be built for this pass.

### 20.2 K and DST — measured, then the naive reading disproved

**STATUS: does NOT match §20's expectation — and not for the reason it looks like**
14-round 1QB league: K first taken **round 6** (mean 7.9, **0 of 17** in the last third); DEF
first **round 5** (mean 7.2, 2 of 14 in the last third). Superflex pushes them later (K r8/9.1,
DEF r7/8.4) but still mid-draft. Rounds 11–14 contain no K or DEF at all — they are *finished*
before the late rounds.

I drafted this as "the engine makes K/DST premature priorities." **The margin measurement
disproves that reading.** At the first DEF pick (pick 56):

```
DEF P Eagles   tav=17.0   uv=13.0   need=4.0
QB  J Burrow   tav=16.9   uv=12.9   need=4.0      <- best non-K/DEF, 0.1 behind
K   B Aubrey   tav=15.0   uv=11.0   need=4.0
```

`need_bonus` is **4.0 on all three** — the identical empty-starter-slot lift, no positional
term. The DEF wins by **0.1** because the *offensive* pool's measured value has decayed from
UV 187 at pick 1 to UV ~13 by pick 56. There is no K/DST-specific logic, exactly as
`test_kdst_integration` insists; the timing is a property of the value curve, not of the
positional rules.

**Verdict: BLOCKED, not FAIL.** This check cannot be graded until #58/#74/#75/#76 (bpa unit
drift, TAV saturation) and #49/#50 (real K/DEF/IDP boards, VOR/replacement redefinition) are
settled. §20's own instruction applies: *"Do not rationalize formula changes from anecdotes
alone."*

**The IDP league is the control that proves it.** With a 764-player pool, 168 picks consume 22%
instead of 48%, values stay positive throughout — and **K and DEF are never taken in 168 picks**,
because that league has no K/DEF starter slot. Demand absent → urgency absent. The contract
holds in both directions.

### 20.3 IDP distribution — passes cleanly

**STATUS: PASSES**
76 IDP picks, first at **round 3**, mean **round 8.5**, present in **every round from 3 to 13**.
Longest consecutive same-position run: **5 picks** — against **29** in the offense-only league
(RB, rounds 13–14). The IDP league produces the most balanced draft shape of all eight trials.
§20's *"sprinkled into appropriate later rounds rather than clustering unnaturally"* is met.

### 20.4 Superflex QB — passes cleanly

**STATUS: PASSES**
QB picks by round, superflex: **[7, 8, 4, 3, 3, 0, 1, 0, 1, 0, 1, 0, 0, 0]** — 15 QBs in the
first two rounds, then monotone decay to zero. The 1QB control: **[0, 0, 1, 0, 3, 1, 2, 4, 1, 0,
0, 0, 0, 2]**. Strong first wave, then demand *slows* rather than inflating indefinitely,
exactly as §20 specifies, with the 1QB contrast confirming the effect is the superflex slot and
not the pool.

### 20.5 Depth, balanced pulls, and BPA

**STATUS: PARTIAL — the BPA half passes; the depth half has no input to work from**
Across **1,077 priced decision points**: the pure-UV leader survived as the TAV leader on
**70.3%**, context flipped the leader on **29.7%** (IDP highest at 48.8%, 1QB lowest at 22.7%).
Context participates without dominating — a defensible reading of *"loosely favors balanced
pulls while still allowing clear BPA to win."* The mechanism is separately unit-tested
(`need_bonus`/`eligibility_bonus` capped in bpa scale, with
`test_need_bonus_cannot_flip_a_large_universal_value_gap` and its eligibility mirror).

**But bench capacity is invisible to the engine.** `starter_slot_counts` iterates
`roster_positions` and counts only entries in `FANTASY_POSITIONS` or `FLEX_SLOT_POSITIONS` —
`"BN"` is neither, so it is skipped. Measured: a 7-bench league and a 2-bench league produced
**byte-identical 168-pick drafts**. Depth economics come from pool value decay and round count
alone; how many players a roster can actually hold is not an input. **Verdict: SURFACE (#115).**

### 20.6 Late-draft behaviour — the section's real finding

**STATUS: MISSING — demonstrated at draft scale**
The 18-round trial exists specifically because a 14-round draft cannot reach
`UPSIDE_MODE_DEFAULT_ROUND = 15`. Leader TAV on the first pick of each round:

| rd | 1 | 2 | 3 | 5 | 8 | 10 | 11 | 13 | 14–18 |
|---|---|---|---|---|---|---|---|---|---|
| leader TAV | 187.34 | 99.53 | 73.37 | 25.58 | 6.0 | **0.0** | −3.67 | −8.58 | **None** |

| round | boards with **zero** priced candidates | mean priced / total candidates |
|---|---|---|
| 11 | 0/12 | 5.2 of 9.2 |
| 13 | 2/12 | 4.2 of 10.0 |
| **14–18** | **12/12 every round** | **0.0 of ~9.4** |

**60 of 216 picks (27.8%) are made from boards where nothing can be priced.** The first pick of
round 16, as the board presents it:

```
id=164 WR A Pierce     tav=None uv=None nec="DOESN'T MATTER MUCH" forces=[]
id=165 WR W Robinson   tav=None uv=None ...
id=166 WR K Shakir     tav=None uv=None ...
```

Consecutive ids — the ordering is entirely `_board_order`'s `str(player_id)` tiebreak. In this
harness ids happen to encode trade-value rank within a position block, so the result *looks*
reasonable; in production `players_db` keys are Sleeper ids carrying no value ordering at all.
`_board_order`'s docstring is explicit that it *"does not decide what the board SHOULD do once
nothing on it can be priced; that is an open product decision"* — this is **#61** measured at
draft scale. **Verdict: SURFACE (#114).**

Upside mode does fire and does change behaviour — the position mix flips from RB-dominated
(r13–14) to WR-dominated (r15–18) at exactly the threshold. So §20's *"late-draft behavior
shifts toward upside"* is observably true, and it is operating over rows that carry no price.

**A code-path identity worth stating rather than measuring:**
`use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)`. For every
round below 15, `mode="auto"` and `mode="balanced"` are the **same path** — so the
long-standing "two unreconciled defaults" noted in `draft_simulation.py` diverge *only* at
rounds ≥ 15. Verified directly, not from the docstring: **none of `app.py`'s three
`build_snapshot` call sites passes `mode=`**, so a human's own board is always `"balanced"` and
**never enters upside mode**, while every auto-drafted opponent does. Folded into #115.

### 20.7 TE behaviour

**STATUS: same conditional as 20.2**
TE clusters late (1QB: 5/4/5 across rounds 10–12; superflex: **9 TEs in round 13**). A
nine-in-one-round run looks like scarcity becoming a positional command — but the same pool
decay drives it, and the deeper IDP pool shows a longest run of 5 against 29. Blocked on the
same items as 20.2.

### 20.8 The display contract

**STATUS: holds at the data layer; partial at the presentation layer**
`serialize_candidate` emits an explicit dict containing `uv` and `tav` and **never
`projected_points`** — the board cannot show a fantasy-point total, by construction. (Not
defended by a test: `SerializeCandidateTests` asserts the fields that are present, none that
must be absent.)

Measured over **44,385 board rows**: min **−33.1**, max **190.5**, median **11.0** —
**11.8% negative**, **2.2% ≥ 100**, **11.4% in the 50–400 band** that overlaps a plausible
season fantasy-point total. Two observations follow:

1. **§20's own example does not match the system.** The section says *"displayed values such as
   72 or 91"*; the measured distribution is mostly single-digit, sometimes negative, occasionally
   ~190. The internal scale is not the 0–100 band the check assumes — which is the same
   unit-drift family as #58/#75/#76, seen from the UI.
2. **The board's prose qualifies the unit three times and not twice.** *"universal-value
   points"*, *"-point gap to the next best {pos}"* and *"-point rival premium"* are qualified;
   *"He's X point(s) off the board leader"* and *"about X points of context lift"* are bare. In
   a fantasy app, unqualified "points" is the domain's word for a different quantity, and 1 in 9
   displayed values sits in a range where the two are confusable.

**No repair made.** A two-word copy change has in-file precedent and would be mechanical, but
the substantive half of this finding is the scale itself, which is parked. Fixing the wording
now would tidy the symptom of a parked defect. **Verdict: SURFACE (#116).**

### 20.9 Mechanical layer — flawless

**STATUS: EXISTS**
Across all 1,293 picks in eight trials: `chosen == candidates[0]` on **1,293/1,293**;
**0** boards mis-sorted against `_board_order`'s contract; unpriced rows ordered last in every
case (2,051 unpriced candidate rows observed across the trials). `kdst_1qb_slot1`,
`kdst_1qb_slot12` and `kdst_thin_bench` produced **byte-identical** pick sequences from three
separate OS processes — cross-process determinism, unforced.

### 20.10 Corrections to my own §20 work

1. **The K/DST reading (20.2)** — drafted as an engine fault, disproved by the 0.1-margin
   measurement with identical `need_bonus`. This is the correction that matters most in this
   pass: it is the difference between "tune the formula" and "the input scale is parked."
2. **The reversed-slot config varied nothing.** All twelve chairs start with identical empty
   rosters, so reversing the first-round order is a relabeling, not a different draft position.
   Identical trajectories confirmed it. Varying draft position meaningfully needs an asymmetric
   chair, a different team count, or a different draft type.
3. **The thin-bench config varied a quantity the engine does not read** — which turned out to be
   the finding in 20.5 rather than a wasted trial.
4. **The 14-round wave could not test upside mode at all** (threshold is round 15). Caught after
   the wave launched; the 18-round trial was added for it, and it produced the section's largest
   finding.
5. **I over-stated the display wording at first** — the board qualifies the unit in three of five
   places, not none.
6. **One measurement was abandoned rather than reported.** A direct `balanced` vs `auto`
   divergence probe was killed after ~20 minutes without completing a single board pair; the
   question was then answered exactly by the code-path identity in 20.6, which is stronger than
   the probe would have been. Recorded so the gap is not mistaken for a measurement.

## Pass 16 summary

| §20 check | measured result | verdict |
|---|---|---|
| K/DST land near the end | K r6/mean 7.9, DEF r5/mean 7.2; 0/17 K in last third | **BLOCKED** (#58/#74/#75/#76, #49/#50) |
| IDP sprinkled, not clustered | 76 picks, rounds 3–13, longest run 5 | **PASSES** |
| Superflex QB wave then slowdown | [7,8,4,3,3,0,1,0,1,0,1,0,0,0] | **PASSES** |
| Depth favours balance, BPA still wins | BPA leader survives 70.3% of 1,077 | **PASSES**; depth input missing (#115) |
| Late draft shifts to upside | fires at r15; boards unpriced from r14 | **BLOCKED** (#61 → #114) |
| TE scarcity not an automatic command | 9 TEs in one round (superflex) | **BLOCKED**, same as K/DST |
| Stronger player beats a shallow pool | capped context terms, 70.3% BPA survival | **PASSES** |
| Displayed values are internal-scale | true at the data layer; −33.1…190.5 | **PARTIAL** (#116) |
| Quantified over many decision points | 1,293 picks / 1,077 priced decisions | **done** |
| Build a regression corpus | corpus is gitignored scratch, unversioned | **BLOCKED** (#111, #113) |
| Stability across shapes/formats/depletion | 8 conditions; ordering perfect throughout | **PASSES** mechanically |

**Does anything clear the bar for a production change?** No. Every behavioural finding here
either passes, or is blocked on a parked repair whose premise §20 explicitly says not to
pre-empt. The one mechanically-tempting change (the two unqualified "points" strings) would
tidy the symptom of a parked scale defect and is parked with it.

**Ranked follow-ups**
1. **#114** — the late-draft pricing collapse. 27.8% of an 18-round draft decided by a player-id
   tiebreak, on boards where every candidate is unpriced. #61 left this open as a product
   decision; §20 measures what leaving it open costs.
2. **#115** — two behavioural-coverage gaps: bench capacity is not an engine input, and the
   human's own board never enters upside mode while every simulated opponent does.
3. **#116** — the display contract: the internal scale is not the 0–100 band §20 assumes, and
   the board's prose qualifies its unit in three of five places.
4. **Re-run this entire pass after the repair sequence.** Four of eleven checks are blocked; the
   trials here are the current-state baseline they should be compared against.

## Pass 17 — §21

**Scope:** Build Guide v2 §21 (operational economics, reuse & research memory).

**Baseline:** `af4126d` on `ui-authority-pass`; `main` frozen at `9fb5102`. **No production file
was modified** — every §21 gap is an economics or product decision, and the one thing that
looked like a defect turned out to be a correction to my own earlier record instead.

**Headline: the research memory has the right taxonomy and no mechanism, and the cost half of
"operational economics" does not exist at any layer. Findings carry four of the six reusability
attributes §21 names, nothing consults them before spending a call, nothing expires, and no
price appears anywhere in the codebase — so §21's closing question, whether a more expensive
model earns its cost, is structurally unanswerable by an instrument that measures quality and
latency and never money.**

### 21.1 Reuse: research is reused as context, never as a cache

**STATUS: MISSING as a cost mechanism — EXISTS as context**
`findings_for_context()` and `comparisons_for_context()` are injected into `build_context`, so
the Beat Tracker does start a debate knowing what the panel has already found, each line stamped
with its date. That is real value: the panel is never blind.

But the read sites are exactly four, and **none of them is on the path that decides whether to
spend a call**: `data_merger` (composite input), `app.py:1922/1936` (context prose),
`app.py:5225/5226` (a UI listing). The §15 envelope stands unchanged — four provider calls per
debate whatever the store already holds.

**The only cache in the system is `sleeper_client`'s** (league snapshots and the players DB, with
an age check). Grepped for `cache`/`memo`/`ttl`/`expire`/`expiry`/`reuse` across production: no
hit anywhere on the AI or research path.

**And the prompt argues against reuse, correctly.** `BEAT_SYSTEM_PROMPT`: *"Use live search
whenever it would sharpen the answer — your own live results are, by definition, fresher than any
file-based source in your context."* For the Beat Tracker's actual job — injury designations,
depth charts, practice reports — cached research is *wrong*, and §21's premise ("paying to
rediscover it") does not apply to that half of the work.

**The store already draws the line §21 needs.** A finding with a `rank` is a durable valuation
claim that feeds the composite; one without is qualitative and carries `composite_impact:
"none"`. The taxonomy that would decide what is cacheable already exists in the record. What is
absent is anything that reads it before spending.

### 21.2 The six reusability attributes, measured on a real stored record

**STATUS: PARTIAL — four of six**
Written a finding through the production path and inspected the stored row:

| §21 attribute | present? | as what |
|---|---|---|
| source identity | **yes** | `source` (the cited outlet) |
| freshness | **yes** | `ts` + `date`, and a 60-day recency half-life in the composite |
| topic / entity scope | **yes** | `player_name` |
| validation status | **yes** | `composite_impact`; `panel_undisputed` on comparisons |
| evidence fingerprint | **no** | the `claim` string is the only content; nothing hashed |
| expiration | **no** | nothing ages out anywhere |

Beyond §21's six, three more absences already carry register items: league scope is **recorded
and never read** (#103), origin (search vs the user's own screenshot) is **absent** (#106), and
the cost or latency of the discovery is **absent** (#100).

Stored keys, in full: `claim, composite_impact, conviction, date, id, league_id, player_name,
question, rank, source, ts`.

**On the missing fingerprint**: §17.1 established that this repo's own chosen answer to identity
is a content hash (`bot_benchmark._fingerprint`), deliberately preferred over a maintained
version number. Applying it to an evidence claim is the same mechanism, one artifact further —
folded into #111 rather than raised as a new idea.

### 21.3 Two operations discovering the same fact

**STATUS: PARTIAL — exact repeats deduped, restatements not**
Measured directly:

```
identical wording, same day      -> same id returned, 1 row   DEDUPED
same fact, reworded, same day    -> new id, 2 rows            DUPLICATED
same rank, different source      -> new id, 3 rows            distinct key, correct
```

`add_finding`'s same-day guard keys on the exact tuple (player, source, claim, rank), so
*"ESPN has him WR4"* and *"ESPN ranks him fourth among WRs"* are two findings.

**But the consequence is smaller than the docstring implies.** That guard says it exists to stop
a repeat *"inflating this finding's weight in whatever percentile pool it feeds."* The composite
is already protected independently: `load_bot_research_as_external` keeps only the newest row per
`(player, cited source)`, and the measurement confirms it — **3 stored rows collapsed to 2
reaching the composite.** So the dedup's stated purpose is redundantly covered; its real effect
is on the store's size and on the prose the panel reads, where both restatements appear.

Concurrency is the #102 shape: `add_finding` is load-modify-write on one global file with no
lock, so two simultaneous writers lose one row. Unchanged by §21, restated for completeness.

### 21.4 Sharing across users versus private context

**STATUS: MISSING — the record does not separate the claim from what produced it**
Every finding stores `question` — the user's own typed question, passed straight through from
`process_moderator_output(trigger_question)` — and `league_id`. The shareable artifact (player,
source, claim, rank) and the private context that produced it (which league, what the user
asked) live in the same row with no boundary between them.

Today that is inert: `findings_for_context` renders only date/player/source/rank/claim, so the
question text is stored but never re-injected, and the app is single-tenant (§12). It matters
because `bot_research.json` is **the one research store deliberately left out of `.gitignore`**,
i.e. the one designed to travel — which makes it the first thing that would be shared, carrying
the private fields with it. **Verdict: SURFACE (#117).**

### 21.5 Expiration

**STATUS: MISSING at the context layer, EXISTS at the composite layer**
Measured: a finding aged **400 days** is served to the panel unchanged, inside the newest-30 cap.
Nothing ages out, and no TTL exists anywhere.

The two consumers behave differently, and only one of them is defensible today:
- **Composite**: rank-bearing findings are recency-weighted (`_recency_weight`, 60-day
  half-life), so a 400-day claim contributes about 1% of a same-day one. Handled.
- **Context prose**: no weighting at all. A 400-day-old qualitative claim reaches the panel with
  the same standing as yesterday's — **labelled with its date**, which is honest, but unranked
  against fresher material and competing for the same 30-slot cap.

Folded into #117: an expiry policy is exactly the kind of product decision §21 is asking for, and
"a stale claim is not a false claim" (§22's own later phrasing) is the rule it has to respect.

### 21.6 Cost and latency — the half that does not exist

**STATUS: MISSING**
- **Latency** is measured in exactly one place: `bot_benchmark` times each provider call
  (`t0 = time.time()` around it) and reports `latency` per question and `avg_latency` per
  candidate. `app.py` surfaces it as *"{score}/100, {avg_latency}s avg"*.
- **Production debates measure nothing.** `DebateResult` carries the question, four reports, the
  verdict, errors, `role_providers` and `role_models` — **no timing, no usage, no cost.**
  `run_debate` already runs Quant and Beat inside a `ThreadPoolExecutor`, where wall time is
  trivially available, and does not capture it.
- **No price exists anywhere.** Grepped production for `price_per`, `per_token`, `cost_per`,
  `pricing`, `$0.`, `usd`: every hit is fantasy-football player pricing. Checked by reading, not
  by count.

So §21's *"can the system measure the marginal cost and latency of each operation and chair?"* is
**latency: only in the benchmark, never in production; cost: nowhere, at any layer.** This is
#100 seen from the economics side rather than the provenance side.

**And that decides the section's closing question.** *"Can the platform determine whether a more
expensive model actually improves downstream decision quality enough to justify its cost?"* The
benchmark is the only instrument that could — it already scores quality per candidate model,
records latency, and (since §17 R15) records the token budget and SDK versions it ran under. It
records **no price**, so it can rank models by quality and by speed and **cannot express the
comparison the question asks for at all.** The instrument is one field short of the question.
Folded into #100.

### 21.7 A correction to my own §16 and §18 records

**This is the pass's most important output.**

I wrote, in the §16 appendix and again in §18, that `data/baseline/bot_research.json` is
**git-tracked**, and used it to sharpen #106: a user's own claim becoming *"a committed numeric
input"*. I took it from `bot_research.py`'s own docstring — *"Both are global and git-tracked,
unlike decision_log/todo_log's per-league, gitignored JSON"* — and README repeats it twice.

Checked directly this pass:

```
data/baseline/bot_research.json      does not exist
git check-ignore                     NOT ignored
git log --all -- <path>              (empty: never committed)
```

Both research stores are **absent, untracked, and have never been committed.** The claim is
aspirational rather than false — nothing gitignores them, so a finding *would* be committed the
first time one is written — but the state has never been reached, and **the research memory this
section is auditing has never held a single row in version control.** Every measurement in 21.2
and 21.3 above is against a planted record, and says so.

Two things follow. **#106's severity drops**: a user-supplied claim becoming a committed input is
a live hazard, not an observed state. And I violated the rule I have been citing all programme —
`ENGINEERING_DOCTRINE.md`'s *"A docstring can encode a defect. Documentation is evidence of
intent, never of correctness"* — by carrying a docstring claim into two audit records without
checking it. Both records are corrected in place.

## Pass 17 summary

| §21 question | measured result | verdict |
|---|---|---|
| reuse rather than rediscover | reused as context; no cache, no call suppression | **MISSING** as economics (#117) |
| what makes research reusable | 4 of 6 attributes present | **PARTIAL** (#117, #111) |
| shared across users, private preserved | `question` + `league_id` in the same row as the claim | **MISSING** (#117) |
| two operations discover the same fact | exact repeat deduped; restatement duplicated | **PARTIAL** |
| dedup without inheriting private context | no call dedup exists, so moot | **N/A today** |
| marginal cost and latency per chair | latency in the benchmark only; cost nowhere | **MISSING** (#100) |
| does a costlier model justify its cost | instrument has quality + latency, no price | **unanswerable** (#100) |

**Does anything clear the bar for a production change?** No. Every gap here is an economics or
product decision — what may be cached, for how long, and what a shared record must strip. The
one thing that looked like a defect was my own record, and it is corrected rather than coded
around.

**Ranked follow-ups**
1. **#117** — the research-memory contract: no expiry, no evidence fingerprint, and no boundary
   between a shareable claim and the private question and league that produced it. One decision
   surface; #103 (league scope recorded but unread) and #106 (origin) are the same record's
   other two missing columns.
2. **#100** (sharpened) — the benchmark is one field short of answering §21's closing question.
   Adding a price to a report it already fingerprints is the cheapest path to a
   quality-per-cost comparison this app cannot currently make.
3. **#111** (unchanged) — an evidence fingerprint is this repo's own content-hash mechanism
   applied one artifact further.

## Interlude — a scope fact this audit implied but never stated

Prompted by §21.7's correction, I swept every runtime store the audit has discussed:

| store | state |
|---|---|
| `data/baseline/bot_research.json`, `bot_comparisons.json` | **absent** (never committed) |
| `data/benchmark_results.json` | **absent** |
| `data/bot_config.json` | **absent** |
| `data/player_aliases.json`, `data/league_formats.json`, `data/league_prefs.json` | **absent** |
| `data/last_session.json` | **absent** |
| `data/decisions/`, `data/todos/`, `data/attachments/` | present, **0 files** (created by `mkdir`, untracked) |
| `data/chats/`, `data/sleeper_snapshots/`, `data/projections/` | present, **only a tracked `.gitkeep`** |
| `data/draft_simulation_trials/` | 31 files, **all untracked** regenerated scratch (§19.6) |
| `data/baseline/` (rankings, trade_value, external) | **28 committed files — the only real data** |

**This checkout has never been run as an application.** The only data behind it is the committed
vendor baseline. Every finding across §11–§21 that touched a runtime store — aliases, format
overrides, decisions, to-dos, pins, attachments, benchmark history, research memory — was
measured against a **planted or synthetic record**, which each pass said locally and none said
globally. It should have been stated once, at the top, and is stated here.

What it changes, and what it does not:

- **It does not weaken the mechanism findings.** A code path that loses an update, drops a
  provenance field, or admits an unattributed claim does so whether or not a file exists yet.
- **It does downgrade every "observed state" phrasing to "live hazard."** #106 was corrected
  explicitly for this in §21.7; the same qualifier applies to #102's lost update, #103's
  share-everything default, #107's alias overrides and #110's unrecognised status — all
  demonstrated on planted records, none observed in production data.
- **It strengthens §19.3.** "The test baseline is reproducible because all 28 loaded files are
  committed" is stronger than it read: there is nothing else on disk for the suite to pick up.
- **It sharpens #113(c).** The planted-CSV probe showed an untracked upload silently entering the
  priced pool. That directory is empty today for the same reason everything else is — the app has
  not been run here — which is exactly why "clean by construction" and "clean because nobody has
  used it" needed separating.
- **It is why §20 had to build its own pool.** With no Sleeper snapshot on disk, every draft
  simulation had to synthesise `players_db` from the committed rankings.

Recorded as a scope fact, not a defect. An audit of an unpopulated checkout can establish what
the code will do; it cannot establish what the data has done.

## Pass 18 — §22

**Scope:** Build Guide v2 §22 (cross-cutting questions & failure-propagation tests).

**Baseline:** `60d6097` on `ui-authority-pass`; `main` frozen at `9fb5102`. One production file
modified (`llm_engine.py`) — **R17, a correction to my own §14 repair.**

**Headline: §22's failure-propagation questions are answered better than expected — two
deterministic cascade boundaries exist and one of them is adversarially tested, every chair call
is stateless so a model swap cannot inherit conversational assumptions, and no two components
recompute the same number. The one thing §22 caught is a label I wrote: R12's unavailability
marker asserted that the call "did not complete" and that "no analysis was produced", two claims
a bare `except Exception` cannot support and both false in the timeout case.**

### 22.1 R17 — the marker asserted what the catch cannot know

**STATUS: was WRONG — repaired**
§22 asks: *"If a chair succeeds but its response is lost, can the operation identify the
ambiguity between 'not executed,' 'executed but not received,' and 'executed and stored'?"*

Every provider caller wraps its entire request in `except Exception`, which fires alike for:
a missing key (**never executed**), a connection error (**never executed**), a read timeout after
the provider generated and billed a response (**executed, not received**), and a parse error on
a response that did arrive (**executed, received, dropped locally**).

The marker I wrote in §14's R12 said:

> *"(unavailable — this chair's call **did not complete**, so **no analysis was produced**. …)"*

Both clauses are assertions the catch cannot establish, and in the timeout case both are simply
false — the analysis exists and was paid for (#100). This is precisely the rule **#89** set for
the alias branch and **§6 R1** applied to `"validated"` → `"panel_undisputed"`: *a field may not
claim a certainty its writing path cannot establish.* I applied that rule twice and then broke it
in a repair of my own.

**R17** rewords it to what is known, and names the ambiguity rather than resolving it:

> *"(unavailable — no report from this chair reached the panel. Whether the call never ran, ran
> and was lost, or ran and could not be read is not known here. Treat this as MISSING
> information, never as a finding that there is nothing to report.)"*

Behaviour is unchanged — it is a string — and the two properties R12 existed for survive
(`MISSING`, `never as a finding`). Two tests added to `test_failure_mode_boundary.py`: one
forbidding the overclaiming phrases and requiring the ambiguity be named, and one asserting
**every** caller still catches bare `Exception` — because the marker's caution is only warranted
while the catch really is that broad, and a future narrowing should force the wording to be
revisited rather than silently left over-cautious. Four probes planted and reverted, all failing
as intended.

### 22.2 Cascade boundaries — two, and one is adversarially tested

**STATUS: EXISTS**
§22: *"Can one bad upstream result contaminate an entire chain, and is there a deterministic
boundary that stops the cascade?"* Two boundaries, both structural rather than instructional:

1. **Chair handoff** (R12/R17): a failed upstream report is *replaced*, never forwarded. The raw
   provider exception text never reaches another provider — one of §7's residuals, closed.
2. **CDME ingestion** (`test_cdme_ingestion_boundary`): LLM-originated data reaches exactly one
   consumer, `composite_player_score`, which `draft_room` deliberately removed from its math;
   the two CDME touches of `external_values` hard-filter to `source_name == "keeptradecut"`,
   structurally excluding every `bot_research` row. Proven by **injecting a maximally distorting
   finding on a real baseline player and showing CDME's output byte-identical before and after.**

### 22.3 A model replaced mid-thread cannot inherit conversational assumptions

**STATUS: EXISTS — by construction**
There is no thread. Every chair call is single-shot: `messages=[{"role": "user", "content":
user_prompt}]` with `system=system_prompt` re-sent in full on every request. A chair's contract
travels with each call rather than accumulating in a conversation, so a role re-pointed at a
different model or provider receives the identical contract and evidence and inherits nothing.
`role_providers` / `role_models` (R9/R10) then record which model actually answered, so an old
record shows who answered it rather than whatever is configured now.

The residual is §17's: the *recorded* model is the one requested, and all three defaults are
floating aliases whose served weights the response object would have named had it not been
discarded (#109).

### 22.4 Two components reconstructing the same fact

**STATUS: EXISTS — no independent reconstruction on the draft path**
The engine rounds once, at the source (`.round(2)` on the board's own columns), and
`_records_with_normalized_nan` **normalizes NaN to `None` without recomputing or re-rounding
anything**. `draft_board_ui.serialize_candidate` is a field-for-field read — its own docstring
says the only computed values are two renamings of booleans the engine already produced — and the
board's `.toFixed(1)` is a display re-render of an already-rounded number. No consumer derives
the same quantity by a second route, so §22's disagreement-by-transformation case does not arise
here.

Where it *could* arise is the Prytaneum path, which has no frozen context at all (#92): the
Draft Room hands a `PickSnapshot`, while a chat debate rebuilds `build_context` from live state
on every question.

### 22.5 Two Sleeper clocks, one disclosed

**STATUS: MISSING — disclosure, not caching**
§22: *"Can an older cached evidence package override fresher canonical state?"* The only cache in
the system is `sleeper_client`'s, and its players-database TTL is deliberate and
vendor-requested: `PLAYERS_CACHE_MAX_AGE_SECONDS = 24h`, commented *"Sleeper asks that
/players/nfl be pulled at most once/day."*

But `players_db` is what `app.py:3117` hands the engine, and `injury_status` — read from it at
`build_available_pool` — is **the only Sleeper field that feeds the deterministic valuation**
(`RISK_ADJ`). So a freshly synced league (rosters, who is drafted) can be combined with an
injury designation up to a day old.

`build_freshness_manifest` grades four sources — DS Dynasty Rankings, DS Free Agent Finder, DS
Trade Value Chart, and the Sleeper league sync — with STALE at ≥7d and EGREGIOUSLY OUTDATED at
≥30d. **It has no entry for the players database.** One of the two Sleeper clocks is graded; the
other is invisible.

Not repaired: exposing the cache age needs a new accessor, and the existing 7/30-day scale would
render a 24-hour bound permanently "fresh", so the disclosure needs its own scale — a product
decision. **Verdict: SURFACE (#118).**

### 22.6 History is amended, never rewritten

**STATUS: EXISTS**
§22: *"Can a newer canonical correction be prevented from retroactively rewriting historical
audit records?"* Checked each store's write paths: `decision_log.log_decision` writes
`moderator_text` and the parsed verdict **once**; `set_outcome` adds only `outcome`,
`outcome_note`, `outcome_date` and touches nothing else. `todo_log.revise_todo` archives prior
text in `revisions`; R13 added the same for proposals. `bot_research` is append-only by
construction (its own docstring: *"a later entry … does not overwrite or delete an earlier one,
it just outranks it at READ time"*).

So corrections are **additive everywhere**. The one place a superseded statement was destroyed
rather than kept was `reopen_todo`, which §16's R13 repaired.

### 22.7 Stale versus false

**STATUS: EXISTS as capability, unwired as practice**
`snapshot_is_current` returns `(bool, reason)` where every reason is a **staleness** claim, never
a correctness one — *"N new pick(s) made since this snapshot was built"*, *"the underlying player
data changed"*, *"snapshot carries no input-state stamp"* — and an unstamped snapshot is reported
*not-certifiable* rather than silently current. That is exactly §22's *"marked stale without being
incorrectly marked false"*, and §18's eight-state work is the same distinction one layer down.

§22's closing question — *"can the system tell the user 'this is the answer under the current CDME
snapshot, but research indicates that snapshot may be stale' without conflating the two claims?"*
— has both halves built (the certifier, and the freshness manifest that already tells the panel
which sources are stale and by how much) and **no production caller** joining them. That is
#101, unchanged by §22.

### 22.8 Schema-valid but semantically corrupt

**STATUS: PARTIAL — shape checked, evidence not**
`parse_moderator_verdict` and `bot_benchmark._contract_ok` (§5 R95) detect whether a chair emitted
the structured block it owes. Nothing checks that a verdict's claims are supported by the reports
beneath it — the SOURCE FINDING gate is the Moderator's own assertion that the panel did not
dispute a claim, which `process_moderator_output` persists without re-adjudicating, and says so.
Unchanged by §22; this is #94's territory.

## Pass 18 summary

| §22 question | result | verdict |
|---|---|---|
| authoritative representation | `PickSnapshot` on the draft path; none on the Prytaneum path | #92 |
| independent reconstruction disagreeing | engine rounds once; consumers read, never recompute | **EXISTS** |
| canonical immutable operation context | frozen `PickSnapshot`; Prytaneum rebuilds live | #92 |
| lost-response ambiguity | asserted away; now named | **REPAIRED (R17)** |
| model replaced mid-thread | stateless single-shot calls, contract re-sent | **EXISTS** |
| schema-valid but semantically corrupt | shape checked, evidence not | #94 |
| cascade contamination | two boundaries, one adversarially tested | **EXISTS** |
| older cache over fresher canonical state | 24h players cache, undisclosed | SURFACE (#118) |
| retroactive rewriting of audit records | additive everywhere | **EXISTS** |
| stale without being false | staleness reasons never assert falsity | **EXISTS** |
| "answer under this snapshot, but it may be stale" | both halves built, never joined | #101 |

**Does anything clear the bar for a production change?** One thing, and it was mine.

**R17 — `llm_engine.UNAVAILABLE_REPORT` no longer asserts why a report is missing.** Justified by
the rule this programme established twice (#89, §6 R1) and then broke in R12. Behaviour
unchanged; two enforcement tests added, four probes planted and reverted.

**Ranked follow-ups**
1. **#118** — the players database has a 24-hour vendor-mandated TTL, carries the only Sleeper
   field that feeds the deterministic engine, and appears in no freshness surface. Disclosure
   needs its own scale, since the existing 7/30-day grades would call a 24-hour bound permanently
   fresh.
2. **#101** (unchanged) — the certifier and the freshness manifest are both built and never
   joined; §22 asks for exactly their conjunction.
3. **#92** (unchanged) — the Prytaneum path still has no frozen context to reference instead of
   rebuild, which is where §22's disagreement-by-transformation case would first appear.

## Pass 19 — §23

**Scope:** Build Guide v2 §23 (implied architectural mandates) — twenty-three mandates, scored
against what §1–§22 measured. **No production file modified; no test added.** §23 is a
compliance checklist over work already done, and every verdict below points at the measurement
that supports it rather than restating the argument.

**Headline: 12 met, 9 partial, 2 not met. The mandates about *boundaries* — least privilege,
provider-as-dependency, authority in architecture, failure states, trust classes — are met
structurally rather than by instruction, several with adversarial tests. The mandates about
*identity and reuse* — replayability, version identity, reusable research — are the ones that
are not met, and they are the same four register items in different clothing: #92, #111, #117
and #100.**

### The scorecard

| # | Mandate | Verdict | Evidence |
|---|---|---|---|
| 1 | One frozen decision context per operation | **PARTIAL** | `PickSnapshot` is frozen, immutable and stamped (§11.6) on the Draft Room path; the Prytaneum rebuilds `build_context` live per question — **#92** |
| 2 | Canonical state separated from external evidence, explicit trust classes | **MET** | `bpa_source` (4 anchors) → `CONFIDENCE_BY_SOURCE` {80/60/50/35}; `COMPOSITE_SOURCE_WEIGHTS` {DS 1.3 … bot_research 0.5}; `composite_impact`; the ingestion boundary hard-filters CDME to `keeptradecut` (§18.4, §22.2) |
| 3 | Stable chair contracts independent of model/provider | **MET** | single-shot calls, `system=` re-sent in full, `ROLE_SYSTEM_PROMPTS` keyed by role, `PROVIDER_CALLERS` indifferent to it (§22.3). Residual: the *served* model is unrecorded — **#109** |
| 4 | Evidence travels as evidence; summaries do not replace source packages | **NOT MET** | the Contrarian receives the Quant's **prose report**, not the numbers behind it — **#93**, named in §4/§5 and unchanged since |
| 5 | Authority enforced in architecture, not only in prompts | **MET** | §15: "the Moderator never triggers a debate itself" is *also* structural — no code path from a parsed verdict to a provider call. §22.2: the ingestion boundary is a source filter, not an instruction. Residual: SOURCE FINDING admission is the Moderator's own gate — **#94** |
| 6 | Structured context first; conversation not the sole carrier | **MET** | `build_context` assembles structured sections; the board travels as `PickSnapshot`; conversation is capped at 16 turns and additive |
| 7 | Compaction auditable, cannot alter mandatory meaning | **MET** | §9.8's correction: a timestamped `pre_compact_` backup is written **before** overwriting, and compaction aborts on summarizer failure; mandatory state is uncapped |
| 8 | Failure states cannot masquerade as absent evidence | **MET** | R12 replaces a `⚠️` with an explicit MISSING marker that forbids reading it as a finding; **R17** (§22.1) removed the marker's own overclaim |
| 9 | Contrarian a real challenge function, not a veto | **MET** | it gates *ingestion* — a disputed SOURCE FINDING is not written at all — while the Moderator weighs all three reports (*"None of these sources is the single source of truth"*) and must **name** the dissenter when CONVICTION is Majority |
| 10 | Moderator preserves uncertainty, separates established from contested | **PARTIAL** | CONVICTION/DISSENT/RISK carry uncertainty; context separates canonical from research explicitly. No channel for "this rests on your own override" — **#108** |
| 11 | Model optimization role-specific, empirical, repeatable, versioned, **and evaluated across downstream chair chains** | **PARTIAL** | `bot_benchmark` is all of the first four (R95 fingerprints, R15 envelope, blind judge, capped history). **Nothing measures whether a better Quant produces a better Moderator verdict** — every chair is benchmarked in isolation — **#96** |
| 12 | Validated research becomes reusable knowledge, reducing recurring cost | **NOT MET** | reused as context, never as cost; no cache on the AI path; four read sites, none pre-call — **#117** |
| 13 | Replayability an architectural invariant | **PARTIAL** | the Draft Room can reconstruct a pick (snapshot + stamp + R11's debate stamp); `decision_log` stores a verdict with no record of the override state in effect — **#92**, widened in §16.7 |
| 14 | Every material result has temporal and version identity | **PARTIAL** | benchmark reports: both (R95 + R15). Decisions: temporal only. `PickSnapshot`: an input-state stamp but no identity. Trials: neither — **#111**, **#92** |
| 15 | Tenant isolation includes caches, research objects, intermediate artifacts | **PARTIAL** | per-league stores are scope-keyed and the Sleeper cache is filename-keyed; research objects are global with a `league_id` **recorded and never read** — **#103**, **#117** |
| 16 | Deterministic claims backed by regression diagnostics and simulation | **MET** | 1,457 tests, 274 of them boundary tests across 15 files, plus §20's 8 controlled drafts over 1,293 decision points. Residual: nothing runs them automatically — **#113** |
| 17 | Canonical ingestion gated by evidence, provenance, policy, adjudication — not model confidence | **PARTIAL** | the pending-upload gate is real human adjudication with deliberately neutral button wording (§16.6); SOURCE FINDING is the Moderator's own undisputed-ness assertion, persisted without re-adjudication — **#94**, **#97**, **#98** |
| 18 | AI seats under least privilege | **MET** | R90 / `test_prompt_constant_boundary`: **no engine constant reaches any prompt**, proven not instructed. §3's #91 is *over*-restriction (ScreenContext built and not sent), not leakage |
| 19 | CDME equation's confidentiality must not depend on prompt compliance | **MET** | same test, same mechanism: the constants are structurally absent from prompts rather than protected by an instruction not to reveal them |
| 20 | Retrieved text is data, not instructions | **PARTIAL** | provider-side search results arrive inside the model's own turn with no fencing this app controls; captions and pins are labelled as user claims (§16.4) but web results are not delimited — **#98** |
| 21 | User corrections inform investigation without silently becoming canonical | **PARTIAL** | the pending-upload gate is exactly this mandate, done well. The alias override is silent, immediate, and drops its marker before the decision boundary — **#107** |
| 22 | A provider is an execution dependency, not an authority | **MET** | the ingestion boundary is adversarially tested: a maximally distorting LLM finding injected on a real baseline player leaves CDME's output **byte-identical** (§22.2) |
| 23 | Every recommendation has a causal path back to frozen inputs | **PARTIAL** | Draft Room: yes, end to end. Prytaneum: there are no frozen inputs to trace to — **#92** |

**12 MET · 9 PARTIAL · 2 NOT MET.**

### What the scorecard says that the individual sections did not

**The met mandates cluster.** Nine of the twelve are *boundary* mandates — least privilege,
confidentiality, provider-as-dependency, authority-in-architecture, failure states, trust
classes, chair-contract stability, structured-context-first, compaction. Every one of them is met
**structurally**: a source filter, an absent constant, a replaced string, a re-sent system prompt.
None of them rests on a model behaving as instructed. That is the single strongest architectural
property this audit found, and it was found the same way each time — by planting something and
watching the boundary hold.

**The unmet and partial mandates also cluster, into four items.** Strip the wording and #1, #13,
#14 and #23 are all **#92** (no frozen, identified context outside the Draft Room); #14 is also
**#111** (content-hash identity applied to one artifact); #12 and #15 are **#117** (the
research-memory contract); #11's unmet half and the cost half of #12 are **#100**. **Four register
items account for every mandate this system does not meet.** That is a much smaller repair
surface than 23 mandates suggests, and it is the most useful thing §23 produces.

**One mandate is met better than its own wording asks.** #16 says deterministic claims should be
backed by "regression diagnostics and simulation, not intuition." §20 ran the simulation half and
found the *mechanical* layer perfect across 1,293 decision points — and then found that the
behavioural checks the mandate exists to support are blocked on #58's unit drift. The diagnostics
are real; what they currently prove is that the machinery is sound and the scale is not.

**And one is met in a way worth guarding.** #4's failure (`prose, not evidence` — #93) and #18's
success (`no engine constant reaches a prompt` — R90) are in tension: the same discipline that
keeps proprietary constants out of a chair's context is what leaves the Contrarian arguing with a
summary instead of the numbers. Settling #93 must not be allowed to reopen #18. Recorded here
because the two items have never been read against each other.

## Pass 19 summary

**Does anything clear the bar for a production change?** No. §23 is a scorecard; every gap it
scores is already a register item with its own evidence and its own parked decision.

**Ranked follow-ups** — the four items that account for all nine partials and both misses:
1. **#92** — one frozen, identified decision context outside the Draft Room. Mandates 1, 13, 14
   and 23 are all this.
2. **#117** — the research-memory contract. Mandates 12 and 15.
3. **#111** — content-hash identity beyond the benchmark report. Mandate 14's other half.
4. **#100** — a price on a benchmark report. Mandate 11's downstream-chain half and mandate 12's
   cost half.
Plus **#93**, which is the only NOT MET that is not one of those four — and which must be settled
without reopening #18.

---

# Pass 20 — §24 Recommended Execution Order

**STATUS:** COMPLETE. Two of §24's fifteen steps had never been performed by any earlier pass —
step 3 (the seven-way gap classification) and step 10 (the causal-reconstruction exercise). Both
are performed here. Two more (step 9's second half, step 15) are recorded as **gaps in the audit
itself**, not in the system. One (step 14) is **correctly declined**.

**LOCATION:** the register (all 41 open items), `pick_synthesis.CandidateSnapshot`,
`draft_board_ui.serialize_candidate`, `pick_debate._format_candidate`,
`draft_room.compute_draft_board`.

## 20.1 The audit scored against its own prescribed order

§24 prescribes fifteen steps. Scored against §1–§23 as actually executed:

| # | Step | Result |
|---|------|--------|
| 1 | Finish the repair/test gate; establish a clean baseline | **DONE** — re-established at every section boundary; 1370 → 1459 tests |
| 2 | Architecture audit only; no speculative redesign | **DONE** — 17 repairs, every one mechanical and rule-derived; every new decision parked |
| 3 | Mark every gap by kind (7-way) | **DONE HERE** — §20.2; never applied before this pass |
| 4 | Trace canonical data/context handoff into every AI chair | **DONE** — §3/§4; produced #91 (ScreenContext reaches the model on 1 chip of 7) |
| 5 | Trace chair contracts and authority boundaries, least-privilege | **DONE** — §4/§8; R90 pins it with an adversarial test |
| 6 | **Formalize** evidence states, ingestion boundaries, snapshots, context packages | **PARTIAL BY DESIGN** — all four audited (§6, §7, §12, §16, §18); formalization is the parked half (#92, #97, #98, #106, #112, #117). §24 says formalize; the repair rule says characterize and park. The repair rule wins, and the deviation is deliberate |
| 7 | Objective model-selection methodology, only after chair contracts are explicit | **PARTIAL** — chair contracts are explicit (§4); the harness exists and now fingerprints its runs (R95); the evaluation criteria do not cover the envelope (#96) |
| 8 | Source legality/admissibility and prompt-injection boundaries | **DONE** — §7; produced #98 |
| 9 | IP-exfiltration resistance: seated models, provider/tool exposure, **repeated-query inference, client/API scraping** | **HALF DONE** — the first two are done and tested (R90, §8). **The last two were never performed.** See §20.4 |
| 10 | Take one complete user decision and prove how far causal reconstruction works | **DONE HERE** — §20.3 |
| 11 | Exercise failure, concurrency, stale-result, quota, partial-completion, provider-switch | **DONE** — §11, §14, §22. Quota's result *is* that quota is indistinguishable from three other causes (§14) |
| 12 | Establish cost/resource accounting and research reuse boundaries | **AUDITED, NOT ESTABLISHED** — §21 measured that neither exists anywhere. #100, #117 |
| 13 | Controlled draft simulations; compare draft-shape diagnostics | **DONE** — §20, 1,293 decision points across varied league configurations |
| 14 | *Only then* tune behavioral formulas, on numerical regression evidence | **CORRECTLY DECLINED** — its stated precondition (step 12) is unmet, and #58's unit drift means any tuning would be calibrated against a moving ruler. Not a gap; the step's own guard fired |
| 15 | Rerun the audit against the same checklist so the audit becomes a regression artifact | **NOT POSSIBLE YET** — #113: nothing runs the checks on a cadence, nothing pins their inputs, nothing hashes anything. The audit is currently a document, not an artifact |

**Twelve steps performed, one correctly declined, two are gaps in the audit** (step 9's second
half and step 15). Neither of those two is a defect in the system.

## 20.2 The seven-way gap classification (step 3)

Applied to all 41 open register items — the 39 standing plus #118 and #119 created in this pass.

**MISSING CONTRACT (14)** — a decision nobody has made:
#50, #53, #54, #55, #71, #93, #94, #97, #98, #104, #112, #114, #116, #117

**UNKNOWN BEHAVIOR (8)** — blocked on an input the audit could not obtain:
#49, #51, #52, #86, #87, #88, #109, #115

**MISSING OBSERVABILITY (7)** — the fact exists and is not recorded or not visible:
#96, #99, #100, #106, #107, #118, #119

**MISSING IMPLEMENTATION (5)** — decided, specified, not built:
#36, #48, #91, #108, #111

**MISSING ENFORCEMENT (4)** — the mechanism exists; nothing makes it run or consults it:
#101, #105, #110, #113

**MISSING ISOLATION (2)** — one tenant's writes or reads reach another's:
#102, #103

**MISSING PERSISTENCE (1)** — the object is built, used, and never survives:
#92

### What the shape of that distribution says

**Thirty-four percent of the open register is a decision, not code.** Fourteen items are missing
contracts; only five are missing implementations of something already decided. This audit's
output is overwhelmingly *questions correctly refused* rather than *work correctly deferred* —
which is what the repair rule was written to produce, and the first measurement that shows it did.

**Eight more are unknown behavior, and every one is externally blocked** — no K/DEF/IDP startup
board (#49), no reachable `api.sleeper.app` (#88), no SDK that reports the served model (#109), an
adversarial pass not yet run (#51, #52), a sensitivity not yet measured (#86, #87), a mode the
human's own board never enters (#115). None of the eight is blocked on a choice; all are blocked
on access.

**Only seven items are what a reader would expect an architecture audit to produce most of** —
missing observability. That is because observability is where this codebase is *strong* at
computing and *weak* at routing: every one of the seven is a value that already exists somewhere
in memory and reaches no consumer. That is the compute-then-drop class, and §20.3 adds its fifth
and largest instance.

## 20.3 One complete user decision, traced end to end (step 10)

Taking the single decision point with the richest context from §20's 18-round deep trial — a
contested-regime pick where four forces fired at once:

```
DECISION: pick 37 (round 4, pick 1), roster 12 -- took D Swift (RB)
  regime = contested        tav = 41.56   uv = 37.23
  need_bonus = 4.33         eligibility_bonus = 0.0
  necessity = STRONG ACTION (survival 0.001, 22 intervening picks)
  cliff = HIGH, gap 12.0 against a typical 2.0
  positional_forfeit = 25.38   rival_premium = 4.33 (denial team 11)
  forces = [tie, cliff]     context_gap = None
  runner-up: H Fannin, tav 39.65 -- margin 1.91 over a 69-candidate field
```

**How far reconstruction gets.** The outer layer is exact:
`tav = uv + need_bonus + eligibility_bonus` → `41.56 = 37.23 + 4.33 + 0.0`. Every contextual
term above — necessity, survival, intervening, cliff, forfeit, rival premium, both forces — is
carried on the snapshot, reaches the board UI, and is individually reconstructible. The
**contextual** half of the decision is fully causally traceable, which is more than most systems
of this kind manage.

**Where it stops.** `uv` is a leaf. `universal_value = bpa + time_horizon_adj + risk_adj`
(`draft_room.py:34`), and of those three terms:

* **`time_horizon_adj` and `risk_adj` are emitted on every balanced-mode board row and read by no
  production consumer anywhere in the repository.** Verified by exhaustive grep across all
  non-test, non-`run_*` modules: the only hits outside `draft_room.py` are a passing mention in
  `sleeper_client.py`'s prose. Five test files read them off a board row; nothing else does.
  `build_snapshot` does not carry them onto `CandidateSnapshot` at all — the drop is at the
  snapshot boundary, before any surface.
* **`bpa`, `bpa_source` and `confidence` survive onto `CandidateSnapshot` and then diverge.**
  `pick_debate._format_candidate:231` reports `universal_value` *labelled* with its anchor and
  confidence — so a chair knows which of the three anchors produced the number and how much to
  trust it. `draft_board_ui.serialize_candidate` drops all three: an AST read of its emitted key
  set returns 22 keys, and `bpa`, `bpa_source` and `confidence` are not among them.

**The measured drop set.** Of `CandidateSnapshot`'s 37 fields, 13 are read nowhere in
`draft_board_ui.py` — not by `serialize_candidate` and not by its three helpers:

```
bpa · bpa_source · confidence · opportunity_cost · expected_value_of_waiting ·
denial_value · position_expected_taken · position_run_detected · pick_necessity ·
consensus_rank · consensus_tier · reach_label · rival_premium_take_probability
```

**The finding.** No consumer outside `draft_room.py` — not the board, not the debate, not the
decision log — can reconstruct `universal_value` from its three components, because two of the
three exist only inside the module that computes them. The board UI additionally cannot say what
anchored the number or how confident it is. **§23's mandate 23 — "every recommendation has a
causal path back to its frozen inputs" — is met for the contextual layer and breaks at exactly
one node: the valuation leaf.** Filed as **#119**.

This is the **fifth compute-then-drop instance** and the largest by count. The four the record
already names (`waiting_cost` -- which reaches the board but not the debate prompt, per the §18
correction to #57 -- `_match_path`/`_match_verified`, `reconciliation_conflicts`, and
`proj_3yr_state`, closed by R16) are each a single value; this one is a whole decomposition. It also has the class's usual shape: the
values are correct, the computation is careful, and the routing is absent.

## 20.4 The audit's own gap: two exfiltration surfaces never tested (step 9)

§24 names four IP-exfiltration surfaces. Two were audited hard: **seated models** (R90 —
no engine constant reaches any prompt, pinned by an adversarial test that plants one) and
**provider/tool exposure** (§8 — the trust-class boundary, and §21's finding that no engine
internal crosses into a provider payload).

Two were never examined at all:

* **Repeated-query inference** — whether an adversary with legitimate access to the Draft Room
  can recover the equation's constants by varying inputs and observing outputs. The board emits
  `uv`, `tav`, `needBonus` and `eligBonus` per candidate on every query; the layer identity is
  public in this repository's own documentation. Whether that is sufficient to solve for the
  constants is **unmeasured**, and §20.3's finding cuts both ways: the decomposition terms the
  board *doesn't* emit are the ones an inference attack would need.
* **Client/API scraping** — the board is rendered via `st.components.v1.html`, so the full
  serialized candidate array is present in the client. What §20.3 measured as a provenance loss
  is simultaneously an exfiltration *control* that nobody chose deliberately.

**Recorded as an audit gap, not a system finding.** No claim is made here about the system's
resistance in either direction; the point is that this audit cannot make one. Both belong to a
security pass that has not been run.

## Pass 20 summary

**Does anything clear the bar for a production change?** No. §20.3's finding is a new register
item (#119) whose repair — deciding what provenance the board surface owes, against the
exfiltration surface §20.4 says is unmeasured — is exactly the kind of decision the repair rule
parks. Routing `bpa_source` to the board is mechanically trivial and is **not** obviously safe:
it is the one repair in this audit where the fix and an unmeasured security concern point in
opposite directions.

**Ranked follow-ups:**
1. **#119** — the valuation leaf. Blocked on the same decision as #93 (what evidence may travel)
   and now also on §20.4's unmeasured inference surface.
2. **Step 9's missing half** — a repeated-query-inference and client-scraping pass. It gates #119
   and it is the only step §24 prescribes that this audit simply did not attempt.
3. **Step 15 (#113)** — until something runs these checks on a cadence against pinned inputs, the
   audit is a document and not a regression artifact, and §24's final step cannot execute.
