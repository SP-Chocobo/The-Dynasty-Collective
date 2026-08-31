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

**STATUS: VIOLATED — one client-reachable write path, and it breaks its own function's contract**
**LOCATION:** `app.py:3246` `save_alias(...)` → `data_merger.save_alias:1636` →
`data/player_aliases.json` → consumed by `DataMerger._resolve:1945`.
**EVIDENCE:** an audit of every disk write shows `data_merger` writes exactly one file, the alias
map; every other canonical valuation input is read-only at runtime, loaded from committed CSVs.
`save_alias` performs **no validation** of the target — it stores arbitrary free text from
`st.text_input`, gated only by a non-empty `.strip()` at the call site.

`_resolve`'s own docstring states the contract: *"`verified` is True only when exactly one row
survived, so a caller can tell 'this is the player' from 'this is the first of several that
fit'."* The R1–R3 identity repair (#77/#82) made the automatic paths honour it. **The manual
alias branch was not repaired with them** — it returns `exact.iloc[0], "alias", len(exact), True`,
with `True` hard-coded irrespective of how many rows survived.

Probed directly on an in-memory table holding two rows that share a normalized name:

| case | row bound | candidates | verified | contract |
|---|---|---:|---|---|
| alias target does not exist | `None` | 0 | `False` | held — **falls through safely** |
| alias target is ambiguous, no team | `J Chase` (CIN, tv 100.0) | 2 | **`True`** | **VIOLATED** |
| ambiguous, team matches neither row | `J Chase` (CIN, tv 100.0) | 2 | **`True`** | **VIOLATED** |
| *control:* same name, automatic path | `J Chase` | 2 | `False` | held |

The control is what makes this a defect rather than a design choice: **the repaired path returns
`verified=False` on identical data; the alias path returns `True`.**

The reassuring half is worth stating too — a **typo does not silently rebind a player**. A
non-existent target empties the filter and falls through to normal matching, so the feared
"mis-typed alias binds you to someone else" case is *not* the defect. The real defect is narrower
and sharper: an **ambiguous** alias binds to an arbitrary row (`iloc[0]`) and is reported as
verified.

**REACH — measured on the committed vendor tables, not assumed:**

| table | rows | colliding normalized names | rows affected |
|---|---:|---:|---:|
| `projections` (primary valuation table) | 764 | **19** | **38 (5.0%)** |
| `trade_values` | 215 | 0 | 0 |
| `external_values` | 2600 | 698 | 2206 (84.8%) — expected by design, multiple vendor rows per player |

Real collisions in the primary table include `j bates` (ATL/DET, **trade_value 5 vs 14**),
`j love` (SEA/ARI — Jordan vs Julian Love), `g smith` (LAC/NYJ), `c ward` (IND/TEN). Draft Sharks'
first-initial export format makes such collisions structural, not incidental.

**Residual bound, stated honestly:** the defect additionally requires that team disambiguation
fails — no team supplied, or a team matching none of the colliding rows. On the ordinary roster
path Sleeper supplies a real team, which usually disambiguates. **The joint rate is not
measured**, so 5.0% is an upper bound on the collision surface, not the realized exposure.
**BOUNDARY:** browser input → canonical identity resolution → deterministic valuation.
**Unenforced** — the enforced identity boundary has an unenforced side door.
**RISK:** a downstream consumer that trusts `match_verified` (the flag R2 added precisely so
callers could distinguish certainty from a first-of-several pick) is told an arbitrary choice is
certain. Consequence is a wrong `trade_value`/`projection` → `bpa` → `universal_value` → TAV.
**REPAIR IS KNOWN AND ONE LINE**, and deliberately **not applied in this pass** — the task is an
inventory and explicitly forbids production changes absent a repair mandate. Demonstrated: changing
`True` to `len(exact) == 1` makes both characterization tests below fail, i.e. the tests already
specify the fix.
**DEPENDENCIES:** `_find_match`/`_resolve`, R1–R3 (#77/#82), the absence contract, every consumer
of `match_verified`.

### 13.3a Contract pinned in this pass

**STATUS: EXISTS (new)** — `test_identity_boundary.ManualAliasBranchContractTests` (5 tests):
the safe fall-through, the two DEFECT characterizations, the automatic-path control, and a
reach guard asserting the collision surface still exists in committed data.
**Non-vacuity demonstrated:** applying the one-line repair failed exactly the two DEFECT tests
and left the other three green. Probe reverted.

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
| **13.3 alias write → canonical valuation** | **VIOLATED** | **unenforced** |
| 13.3a alias contract pinned | EXISTS (new) | enforced |
| 13.4 AI cannot mutate/recompute | EXISTS | structural + enforced |
| 13.4a AI-authority contract pinned | EXISTS (new) | enforced |
| 13.5 auth / tenancy | NOT APPLICABLE (blocker for hosting) | absent |
| 13.6 credentials | EXISTS (scoped, assumption declared) | structural |
| 8.1 browser reconstruction | PARTIAL | structural |
| 8.2 provider exposure | EXISTS | structural |
| **8.3 methodology in prompts** | **PARTIAL** | **instructional only** |
| 8.4 constants in shipped code | EXISTS | structural |
| 8.5 repeated-query inference | UNKNOWN | — |
| 8.6 external content → deterministic | PARTIAL (closed except 13.3) | — |

### Does anything clear the bar for a production change?

**One item does, and it was still not changed in this pass.** 13.3 is a *proven* contract
violation with a *measured* collision surface and a *known one-line repair* — it meets the
evidentiary bar this program sets. It does not meet the *mandate* bar: this task is an inventory
and explicitly forbids production changes absent a repair instruction. The finding is therefore
recorded, pinned by tests that already specify the fix, and queued.

Everything else is either already protected (13.1, 13.2, 13.4, 13.6, 8.2, 8.4), correctly scoped
as not-applicable (13.5), a product/legal judgement rather than an engineering defect (8.1), a
convention that has not yet been broken (8.3), or an unmeasured reach question that has not
earned a severity (8.5).

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
