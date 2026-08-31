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
| **5.6 Moderator's machine contract not benchmarked** | **VIOLATED** | **instructional** |
| 5.6a repair specified, blast radius measured | DEFERRED to a scoped mandate | — |
| 5.7 per-chair dimension coverage | PARTIAL (Quant 1 of 5) | — |
| 5.8 score normalization (latency unscored, cost absent) | PARTIAL | absent |
| 5.9 reasoning vs tool-use separation | MISSING (uniform grant) | instructional |
| 5.10 degradation detection | MISSING (report overwritten) | pinned |
| 5.11 versioning / replay of results | MISSING | absent |
| 5.12 pinning and fallback | PARTIAL (recorded, not pinned; no fallback) | structural / absent |
| 5.13 downstream-awareness / full chain | MISSING | absent |

Against the mandate's five words: **role-specific ✓, empirical ✓, repeatable ✗** (5.11),
**versioned ✗** (5.11), **downstream-aware ✗** (5.13).

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

### Follow-ups from this pass, ranked by evidence then severity

1. **5.6 — scoped repair mandate for the Moderator contract gate.** Evidence complete; one
   design decision (gate vs flag) outstanding.
2. **5.10 + 5.11 together — report history plus battery/rubric/prompt versioning.** Small,
   mutually dependent, and the pair converts "repeatable" and "versioned" from ✗ to ✓.
3. **5.7 — extend the Quant battery to include conflicting sources.** The cheapest real coverage
   gain in the pass; production Quant's core stated job is currently untested.
4. **5.13 — chain-level evaluation.** The deepest gap, and correctly blocked behind #93.
5. **5.4 — a Draft Room battery.** Blocked behind #88's fixture; named so it is not forgotten.
