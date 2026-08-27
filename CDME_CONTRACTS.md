# CDME Semantic Contracts

What each load-bearing quantity in the Contextual Decision Matrix Engine **means** — stated
before it is read, combined, or wired into anything new.

This document exists because of a measured pattern, not as process decoration. Every genuine
defect found in this engine's adversarial audit was the same shape: a quantity whose meaning
had drifted from what the code assumed about it, with nothing written down to catch the drift.

- A growth signal was manufactured out of missing data, because nothing stated that a
  trajectory comparison requires *both* of its inputs to be real measurements.
- A real NFL tight end was silently deleted from the pool, because nothing stated which
  position families can and cannot be the same person.
- Two of `pick_necessity`'s five terms could be deleted outright with 963 tests passing,
  because nothing stated that each term must be individually reachable.

Each contract below answers the same eight questions. A quantity without answers to all eight
is not ready to be consumed by anything.

> **Status: DRAFT — awaiting sign-off.** No Phase 2 code is written against these until the
> project owner approves them.
>
> **Revision 2** tightened the admission rule after measurement: completeness alone proved
> insufficient (see "The admission invariant"), a scope correction was found (necessity does
> not reorder candidates — Phase 2 changes labels, not picks), and one claim in revision 1 was
> refuted by measurement and is corrected in place (survival stays live late; necessity does
> not run out of signal).

---

## 1. `universal_value`

**Represents** — the team-agnostic value of one player: how good he is, full stop, identically
for every team watching the draft. It is the number that answers "is this a better player,"
never "is this a better player *for me*."

**Units** — a bpa-anchored 0–100-ish scale. `bpa` itself is VOR in raw projected season points,
linearly rescaled against the single largest VOR gap in the remaining pool, so 100 is "the
biggest value-over-replacement gap currently on the board" and the scale is **re-derived on
every board**. It is an *ordinal-with-meaningful-spacing* scale within one board, not a fixed
unit comparable across boards, drafts, or modes.

**Valid domain** — measured on the real committed baseline: **−9.12 to 97.90**. Note it goes
**negative**: `bpa` clips at 0, but `universal_value = bpa + time_horizon_adj + risk_adj`, and
a player with a declining dynasty trajectory and an injury flag lands below zero. Any consumer
assuming non-negativity is wrong.

**What `None` means** — never `None` on a well-formed board. It is emitted in both balanced and
upside mode (see the board-shape contract fix); its absence is a schema violation, not a
"no opinion" signal.

**What `0` means** — a player whose VOR is at or below replacement, with no trajectory or risk
adjustment moving him off it. Genuinely common and genuinely meaningful late in a draft: **by
round 11 on a real 12×20 simulation, every position's best-remaining VOR is 0.00**, so `bpa` —
and with it most of `universal_value`'s spread — collapses board-wide. This is a real property
of the current architecture, not a bug in this quantity, and is tracked separately.

**May influence** — `team_acquisition_value` (as the base it is added to). Display. Any
consumer asking a team-agnostic question: `draft_counterfactual.bpa_row`'s BPA argmax,
`roster_diagnostics`' replacement levels, `draft_strategy`'s opponent-board ranking.

**Must NEVER influence, or be influenced by** — anything roster-specific. `need_bonus` and
`eligibility_bonus` are added *on top of* it to make `team_acquisition_value`; they must never
be folded *into* it. This split is the engine's central architectural commitment: conflating
"how good is this player" with "how good is this player for this roster" is the specific
failure the additive layering exists to prevent.

**Invariants**
1. `team_acquisition_value == universal_value + need_bonus + eligibility_bonus`, in every mode.
2. Identical for a given player across every roster on the same board, by construction.
3. In upside mode it equals `final_score` — the *role* is filled, but by a different formula.
   **Cross-mode comparison of this number is meaningless** and must never be done.
4. Neither `need_bonus` nor `eligibility_bonus` may flip a large `universal_value` gap; both
   are capped for exactly this reason (`NEED_BONUS_MAX`, `ELIGIBILITY_BONUS_MAX`).

**Boundary cases that are legitimate, not bugs**
- Negative, for a declining player with an injury flag.
- Exactly 0 for large swathes of the board late in a draft.
- Many players tied at exactly 100.00 — measured at **six players across five positions by
  round 5**, because their VOR gaps converge. The anchor stops discriminating; downstream
  consumers must not read a tie as a considered judgment.

**Known contamination**
- Mixed scoring basis across positions: offense is Draft Sharks-scored, K/DST is scored by two
  unrelated Sleeper leagues. Cross-positional VOR crosses a scoring boundary by construction.
- Within TE specifically, a scale discontinuity at merged rank ~29 (see §4).

---

## 2. `waiting_cost`

**Represents** — the cost, in real production, of *not* taking this player's position now:
his own projected points minus the points of the best player at his position expected to still
be undrafted when the draft ends.

It is a **pressure/urgency signal, not a player value.** It says "how much do you give up by
deferring," never "how good is this player." A great player at a deep position and a mediocre
player at a barren one can legitimately carry the same `waiting_cost`, and that is the signal
working correctly, not a collision to be resolved.

**Units** — **raw projected season points.** Not a 0–100 scale, not normalized, not bounded.
Divide by `SLEEPER_WEEKLY_TO_SEASON_FACTOR` (17) for the per-week figure the UI displays.
**This is the single most dangerous fact in this document.** Measured among real narrowed
candidates its range is **−285 to +211**, while `team_acquisition_value`'s entire range on the
same board is **4.0 to 106.2**. Adding raw `waiting_cost` to any bounded score does not nudge
it — it overwhelms it. This is precisely the `eligibility_bonus` bug that already happened
once here: a term in different units with a wider range, added into a bpa-scale sum, overrode
real value gaps until it was rescaled and capped.

**Valid domain** — **−299 to +294** board-wide; **−285 to +211** among narrowed candidates.
**Negative is common and meaningful** — 62 of 289 sampled candidates, and roughly half the full
board. Negative means this player is *worse* than what the position will hand you for free
later: waiting is not merely cheap, it is strictly better.

**What `None` means** — **"no opinion," never zero.** It is `None` exactly when
`projected_points` is `None` **or** `horizon_floor` is `None` (verified: zero mismatches
across two league shapes). `horizon_floor` is `None` when the horizon rank falls past the end
of the loaded pool, which `horizon_replacement` deliberately reports as unknown rather than
answering with the worst row it happens to have. Substituting 0 for `None` asserts "waiting is
free," which is the most dangerous possible wrong answer here.

**What `0` means** — this player is worth *exactly* what the free end-of-draft alternative is
worth. Real, measurable indifference. **It must never be confused with `None`.** This is the
same measured-zero-versus-absent-zero distinction that the growth artifact turned on, and it
is already pinned by test for that quantity.

**May influence** — display and the debate layer, today. **Nothing in the valuation path.**
`team_acquisition_value` is computed and rounded *before* `_attach_waiting_cost` runs and is
byte-identical with these columns present or absent.

**What admitting it to `pick_necessity` would and would not do** — `pick_necessity` does **not
reorder candidates**. Verified: nothing in the codebase sorts or selects by it;
`candidates[0]` is the top `team_acquisition_value`, and necessity is zipped in afterwards as
a per-candidate label consumed by display and the debate layer. Admitting `waiting_cost` to
necessity therefore makes the **urgency label** honest; it does **not** change which player
the engine recommends. Any change to *which player is picked* requires touching the valuation
layer, which this contract forbids for this quantity in its current form.

**Must NEVER influence** — `bpa`, `universal_value`, `team_acquisition_value`, or any
replacement-level computation. If it is ever admitted to the contextual layer (Phase 2), it
must arrive **normalized and bounded**, on the same terms as every other necessity term, and
must still never reach the valuation layer.

**Invariants**
1. `waiting_cost = projected_points − horizon_floor`, or `None` if either input is `None`.
2. Observable-only: a board is byte-identical in `bpa`/`universal_value`/`team_acquisition_value`
   whether or not this column is computed.
3. `None` is never coerced to a number by any consumer.
4. Its sign is meaningful. Magnitude alone is not the signal.

**Boundary cases that are legitimate, not bugs**
- Large negative for most of the board — most players are worse than their position's floor.
- Systematic sign flip with draft depth: median **+12 in round 1, −47.5 by round 14**.
- `None` for an entire position at once (see the blocking finding below).

**Known contamination — material, and it lands hardest here**
`horizon_replacement` reads the TE points curve, which has a scoring-basis discontinuity at
merged rank ~29 (see §4). Measured across league shapes, TE's horizon rank lands at **39–51** —
**deep inside the contaminated zone in every shape tested**, where projections are understated
by a median factor of **1.98×**. A floor that is roughly half what it should be makes deferring
TE look roughly twice as cheap as it really is. Of the two consumers of that curve, the live
VOR anchor is only boundary-exposed; **this one is reliably and severely exposed.**

---

## 3. `pick_necessity`

**Represents** — how urgent it is to take **this** candidate **right now**, given the whole
narrowed field. Explicitly *not* "how good is this player" — that is
`team_acquisition_value`'s job, and a worse player facing real scarcity pressure is supposed
to be able to outscore a better player sitting in an uncontested deep position.

**Units** — a bounded 0–100 urgency score anchored at `NECESSITY_BASELINE = 50.0` ("close
call, multiple legitimate paths"). Every term is a bounded additive contribution to that
baseline.

**Valid domain** — `[0, 100]`, hard-clipped. From `LATE_ROUND_THRESHOLD` (round 15) onward the
result is scaled by `LATE_ROUND_NECESSITY_CAP / 100`, so the effective late-draft domain is
`[0, 30]` — a deliberate statement that late picks are not urgent in the same sense.

**What `None` means** — never `None`. Always a real number.

**What `0` means** — no urgency whatsoever. Reachable only by every pressure term being absent
*and* the candidate trailing the field badly enough to zero the baseline.

**Composition** — `BASELINE + standout + survival + cliff + run + denial + roster_fit`,
clipped, then late-round scaled. Each term is bounded and independently reachable.

**May influence** — the recommendation, the displayed urgency label, the debate layer's
framing, `decision_regime`.

**Must NEVER influence, or be influenced by** — `universal_value`, `bpa`, or
`team_acquisition_value`. Necessity is computed *from* those; feeding it back is circular.
It must also never become a second, disguised valuation: every term must answer a
*pressure* question ("will he be gone," "does the curve fall off," "is there a run," "does a
rival want him," "does he fill a hole"), not a *quality* question.

**Invariants**
1. Every term must be **individually reachable** — varying exactly one input away from an
   otherwise-identical candidate must move the score. Pinned by test, after mutation testing
   proved two terms could be zeroed with the whole suite green.
2. Bounded: no term may push the score outside `[0, 100]` before clipping, and no single term
   may dominate the sum.
3. The standout term measures a margin against an **absolute** reference gap
   (`NECESSITY_STANDOUT_REFERENCE_GAP = 15.0`), never against the observed field's own range —
   a relative anchor stretches a trivial gap to fill the whole swing.
4. Order-independent: the same candidate set in any order yields the same scores.
5. No term may double-count another's evidence. `rival_premium` is deliberately
   probability-free because `survival_probability` already carries that same take-probability;
   counting both measured r = +0.82 between the components.

**Boundary cases that are legitimate, not bugs**
- A single candidate with no alternatives gets full standout credit — there is genuinely no
  other path.
- A tightly-bunched field all landing near 50 — correctly reporting "this is a close call."
- Late-round scores capped at 30 even with real pressure present.

---

## Admitting a new term to `pick_necessity`

Any term added to this sum — `waiting_cost` included — must satisfy all of the following
**before** it is written:

1. **It answers a pressure question, not a quality question.**
2. **It is normalized into necessity's own bounded scale**, with an explicit weight constant,
   and cannot dominate the sum. Raw units are never admitted. (`eligibility_bonus` already
   taught this lesson the expensive way.)
3. **Its missing-data behavior is stated and is not a silent default.** "Absent" must not be
   representable as a number that means something else.
4. **Its absence is not systematically correlated with position, source, or any other
   structural property** — or, if it is, that asymmetry is measured, stated, and accepted
   deliberately.
5. **It is individually reachable**, with a regression test that fails if the term is zeroed.
6. **It does not double-count evidence** already carried by an existing term.
7. **It never reaches the valuation layer.**

---

## The admission invariant for `waiting_cost`

Completeness alone is **necessary but not sufficient**. A decision in which every candidate
carries a number, but those numbers come from incompatible scales, produces *complete data +
a correctly functioning calculation + semantically wrong urgency* — every null check passes
and the answer is still wrong. That is the worst failure class this engine can have, and it is
exactly what the TE curve would deliver today.

The invariant therefore has two clauses, and both must hold.

**Clause 1 — per-position basis coherence.** `waiting_cost` is a *difference*:
`projected_points − horizon_floor`. A difference is only meaningful when both endpoints are
measured on the same scale. A position is **basis-coherent** when every row spanning rank 1
through that position's horizon rank derives from a single points-affecting scoring basis.

> A position that is not basis-coherent is not eligible to contribute waiting-cost pressure,
> regardless of whether its numbers are present.

This is deliberately general and names no position. It is the same rule the growth artifact
taught, applied to subtraction instead of comparison: **both endpoints of a difference must be
real measurements on one scale.**

Measured today, superflex + TE-premium, one board:

| Position | Top-of-curve basis | Horizon rank | Floor basis | Coherent |
|---|---|---|---|---|
| WR | te_premium_superflex | 50 | te_premium_superflex | ✅ |
| K | sleeper_kicker | 17 | sleeper_kicker | ✅ |
| DEF | sleeper_dst | 15 | sleeper_dst | ✅ |
| TE | te_premium_superflex | 45 | **dynasty_superflex** | ❌ |
| QB | te_premium_superflex | 43 | *no confident floor* | n/a |
| RB | te_premium_superflex | 75 | *no confident floor* | n/a |

TE is the only position that fails, and it fails **structurally**, not marginally: its floor is
drawn from a file that scores tight ends without the premium, understating them by a measured
median **1.98×**.

Note also that the floor-less positions here are **QB and RB** — where the K/DST league shape
gave **RB and TE**. The missing set is **league-shape-dependent**, so this cannot be reasoned
about as a fixed positional quirk, and any gate must be evaluated per board, not assumed.

**Clause 2 — decision-level completeness.** Per-position eligibility alone would still produce
the asymmetry it exists to prevent (eligible positions get pressure, ineligible ones get
silence). So the gate is evaluated over the whole decision:

> `waiting_cost` may contribute to `pick_necessity` only when, for the **complete narrowed
> candidate set of a single decision**, every candidate has a non-`None` `waiting_cost` **and**
> belongs to a basis-coherent position. If any candidate fails either test, the waiting-cost
> contribution is **exactly 0.0 for every candidate in that decision** — not for some of them.

Partial availability produces no contribution for anyone. There is no partial-credit mode.

---

## Signal magnitude vs decision authority

These are different things and the contract must bound the second, not the first.

- **Signal magnitude** — how large the raw quantity is. `waiting_cost`: −299 to +294 season
  points, unbounded by construction.
- **Decision authority** — how much the term can actually move the outcome, which is its
  **spread relative to the other terms that are live in the same regime**.

The critical consequence: **authority is not controlled by choosing a small weight.** A term
with a tiny weight has *total* authority in any regime where every other term has collapsed to
zero spread. Bounding authority requires knowing which terms are live when.

Measured spread (max − min across candidates) by round, on a real 12×20 draft:

| Round | standout | survival | cliff | run | denial | fit | live terms |
|---|---|---|---|---|---|---|---|
| 1 | 13.74 | 12.82 | 12.00 | 0.00 | 3.61 | 3.46 | 5 |
| 6 | **0.00** | 16.00 | 12.00 | 0.00 | 3.61 | 3.46 | 4 |
| 10 | 0.24 | 15.90 | **0.00** | 0.00 | 3.61 | 3.46 | 4 |
| 16 | 0.84 | 16.02 | 0.00 | 6.00 | 0.00 | 0.00 | 3 |
| 18 | 0.18 | 16.02 | 0.00 | 0.00 | 0.00 | 0.00 | 2 |
| 20 | 0.00 | **0.00** | 0.00 | 6.00 | 0.00 | 0.00 | **1** |

**This corrects an earlier claim in this document's first draft.** It is *not* true that
necessity "has least to work with" late. `standout` dies at round 6 (the VOR saturation) and
`cliff` at round 10, but **`survival` stays strongly live at ~16 spread all the way to round
18**. A new term would be entering a contested field, not a vacuum — except at round 20, where
only `run` survives and any admitted term would dominate outright.

**Authority bound.** `NECESSITY_WAITING_WEIGHT` must not exceed `NECESSITY_SURVIVAL_WEIGHT`
(20.0), so the term can at most tie the strongest live pressure and never exceed it in any
regime where survival is live. Its dominance at round 20 is accepted and stated rather than
engineered away — at the final pick there is genuinely nothing else to differentiate on.

---

## Scope correction — what Phase 2 can and cannot do

**`pick_necessity` does not reorder candidates.** Verified directly: nothing sorts or selects
by it, `candidates[0]` is the top `team_acquisition_value`, and necessity is zipped in
afterwards as a per-candidate label consumed by display and the debate layer.

Therefore admitting `waiting_cost` to necessity:

- ✅ makes the **urgency label** honest — the board can say "this costs 0.47 pts/week to defer"
- ❌ does **not** change which player is recommended
- ❌ does **not** address the original K/DST timing complaint

That complaint requires the **valuation** layer, which every contract here forbids for this
quantity in its present form. This correction matters because Phase 2 was described earlier in
planning as directly attacking the timing problem; it does not, and the two should not be
conflated when deciding whether Phase 2 is worth doing.

Phase 2 is still worth considering on its own merits — an honest urgency label feeding the
debate layer is real user-facing value — but it must be chosen for that reason, not for a
timing fix it cannot deliver.

---

## Proposed Phase 2 interface — for sign-off, not yet implemented

```text
ELIGIBILITY  (per position P, evaluated per board)
    floor_known(P)     = horizon_replacement[P].certain
    basis_coherent(P)  = all rows of P from rank 1 .. horizon_rank(P)
                         share one points-affecting scoring basis
    eligible(P)        = floor_known(P) AND basis_coherent(P)

GATE  (per decision, over the complete narrowed candidate set C)
    admitted = for every c in C:  eligible(position(c)) AND c.waiting_cost is not None
    if not admitted:  waiting_component = 0.0  for EVERY c in C

CONTRIBUTION  (only when admitted)
    normalized        = clamp(c.waiting_cost / WAITING_PRESSURE_REFERENCE, LO, +1.0)
    waiting_component = normalized * NECESSITY_WAITING_WEIGHT

CONSTANTS
    WAITING_PRESSURE_REFERENCE = WAITING_STEEP_PER_WEEK * SLEEPER_WEEKLY_TO_SEASON_FACTOR
                               = 3.0 * 17 = 51.0 season points
    NECESSITY_WAITING_WEIGHT  <= NECESSITY_SURVIVAL_WEIGHT (20.0)     [authority bound]
    LO                         = 0.0  or  -1.0                        [OPEN — see below]
```

**Why 51.0 and not an invented number.** It is not new. `WAITING_STEEP_PER_WEEK` (3.0 pts/week)
is the already-declared, already-documented boundary at which the UI tells the user "waiting is
expensive." Converting it to season points via the existing factor means the necessity term
saturates *exactly* where the interface already says the cost became real — and the two cannot
drift apart, because they are the same constant. Measured against real candidates in the
regime where the term would be active: median |waiting_cost| is 16.5, and 28% of candidates
reach full weight. Sensitive enough to register, not so sensitive that everything saturates.

**The one genuinely open sub-decision: `LO`.**

- `LO = 0.0` — negative `waiting_cost` contributes nothing. Preserves the existing property
  that *every* necessity term is ≥ 0 and the score never falls below `NECESSITY_BASELINE`.
  Follows the `standout` precedent, which is explicitly floored at 0 on the reasoning that
  "not the best option" is neutral rather than evidence of low urgency.
- `LO = −1.0` — "waiting is strictly better than taking him" actively *reduces* urgency.
  Uses information that roughly half the board carries, and is the more honest reading of a
  quantity whose sign is explicitly meaningful. But it introduces the **first negative term in
  the sum**, a change in kind that deserves its own decision rather than arriving as a
  side effect of admitting the quantity.

**Recommendation:** `LO = 0.0` for the first implementation. It admits the quantity without
simultaneously changing necessity's shape, and `LO = −1.0` remains available as a separate,
individually testable follow-up once the term's behavior has been observed in real drafts.

---

## Remaining open decisions

### B — TE basis incoherence  🚫 **prerequisite to Phase 2**

Under the invariant above TE is simply ineligible today, which is the correct and safe outcome
— but under Clause 2 an ineligible TE makes the **entire decision** ineligible in every round
where a TE is narrowed, which is most of them. So the term would be near-permanently inert
until TE's basis coherence is resolved (task #46's decision: restrict, flag, rescale, or
accept). **This is a general architectural rule, not a TE-specific patch** — any position
failing coherence for any reason is handled identically.

### C — Late-draft authority

Settled in principle by the authority bound above, with one accepted exception: at round 20
`waiting_cost` would be the only live differentiator. Accepted deliberately, stated here rather
than discovered later.

### D — Is Phase 2 worth doing at all?

Given the scope correction, this is now a genuine question rather than a formality. Phase 2
buys an honest urgency label and a better debate layer; it does not buy a timing fix. If the
priority is the timing complaint, Phase 3 is the only path, and it is blocked on real draft
data.

---

# Appendix — the decision-path investigation

Commissioned as a specific question: *is `pick_necessity` architecturally intended to
participate in candidate selection, or is it correctly an interpretive label?* Answered below
from repository evidence and measured runtime behaviour. Where the architecture does not
establish an answer, it is marked **unknown** rather than inferred.

### 1. What determines the final candidate ordering?

**`team_acquisition_value`, descending.** Traced end to end:
`compute_draft_board` sorts by `["final_score", "player_id"]` (stable) →
`narrow_candidates` re-sorts by `final_score` alone at line 694 →
`raw_candidates` preserves that order → `candidates` zips necessity in **without re-sorting**
→ `draft_simulation` takes `candidates[0]`.

Determinism survives the second sort only because Python's sort is stable and the incoming
order already carried the `player_id` tiebreak. That is a real, undocumented dependency: the
`narrow_candidates` sort would become non-deterministic on exact ties if its input were ever
reordered upstream.

### 2. Is `pick_necessity` intended to influence that ordering?

**No — on the documented architecture.** Evidence:

- README calls TAV *"CDME's principal quantitative output"*, and the UI a *"translation
  layer"* rendering *"already-decided ranking"* that *"must never independently re-rank"*.
- `pick_synthesis.py`'s module docstring frames the module as *"Deterministic synthesis layer
  for 'Debate My Pick'"* — it exists to feed the debate layer.
- Necessity is explicitly *"NOT another player-value score"* and *"deliberately kept
  value-orthogonal"*.
- `decision_regime` does its **own** ranking by TAV and is explicitly about *"which register a
  decision surface's explanatory prose should use"* — presentation, not selection.
- No ROADMAP entry describes a selection or decision score.

Confirmed by consumption census: `pick_necessity` appears in display and debate paths only;
`necessity_label` has **zero** engine consumption.

**Therefore: making necessity selection-driving is an architectural EXTENSION, not repair of
an oversight.** That does not make it wrong — a *Decision* engine that measures decision
pressure and never lets it reach the decision is arguably incomplete — but it must be chosen
as an extension, with the constraints below.

### 3. What does `NEAR_TIE_BAND` authorize or trigger?

**Nothing. It is label-only.** Every consumer is presentational: a UI badge
(`draft_board_ui.py:63`), a line in the debate prompt (`pick_debate.py:234`), and
classification in `draft_counterfactual`. It authorizes no branch, gates no logic, and
triggers no alternative path. There is **no existing bridge that is merely mis-wired** — there
is no bridge.

It is also **defective in the transition regime** — see the appendix defect below.

### 4. Are the necessity components independent, or partially redundant?

**Mostly independent, with one undocumented redundancy.** From the project's own stored
dependency audit (`dependency_audit_summary.json`, n≈950 candidates per league type):

| pair | 1QB | superflex |
|---|---|---|
| `denial` ↔ `roster_fit` | **0.690** | **0.657** |
| `survival` ↔ `denial` | 0.448 | 0.462 |
| `cliff` ↔ `roster_fit` | 0.417 | 0.214 |
| `cliff` ↔ `denial` | 0.412 | 0.236 |
| everything else | ≤ 0.24 | ≤ 0.24 |

`survival ↔ denial` is documented and accepted in the module docstring (shared cause, not
shared measurement). **`denial ↔ roster_fit` at r ≈ 0.66–0.69 is the highest pair and is
undocumented.** Mechanically unsurprising — `denial` is a *rival's* need+eligibility premium
and `roster_fit` is *mine*; same formula shape, both driven by league-wide positional demand.
Tolerable while necessity is a label. **Would become a genuine double-count if necessity ever
drives selection.**

### 5. Is `waiting_cost` orthogonal where TAV saturates?

**Yes — and only there.** Measured ρ(`waiting_cost`, TAV) by round:

| rd | 1 | 2 | 4 | 6 | 8 | 10 | 12 | 14 |
|---|---|---|---|---|---|---|---|---|
| ρ | 0.665 | 0.849 | 0.844 | 0.670 | 0.401 | −0.283 | 0.017 | −0.370 |

It **largely restates TAV early** and becomes **genuinely independent late** — precisely as
TAV's spread collapses. `waiting_cost` is not a co-input to TAV; it is a **successor** to it.

### 6. Anything computed but never consumed?

Yes, one that matters: **`waiting_cost`, `horizon_floor` and `horizon_sensitivity` never reach
the debate layer** — zero occurrences in `pick_debate.py`. The debate layer receives 18
candidate fields, including both *overlapping* cost-of-waiting concepts (`opportunity_cost`,
`positional_forfeit`), but not the one that actually answers the question. Given the README's
rule that the debate layer may never compute a number CDME did not provide, this is a gap, not
a choice.

`rival_premium_take_probability` is engine-internal only (feeds `block_opportunity`) — correct
and by design.

### 7. Anything crossing a semantic or scale boundary before consumption?

Three, all measured: the TE within-position basis incoherence (§ admission invariant), the
cross-positional scoring basis inherited from the baseline (§1), and `NEAR_TIE_BAND` below.

---

## Appendix defect — `NEAR_TIE_BAND` is absolute against a collapsing scale

`NEAR_TIE_BAND = 2.0` is an absolute TAV threshold, documented as derived from a **fresh**
board (adjacent gaps median 1.23 / p75 2.26). Applied unchanged to every round:

| round | TAV spread | band as % of field | flagged near-tie |
|---|---|---|---|
| 1 | 102.23 | 2.0% | 0 / 72 |
| 8 | 104.00 | 1.9% | 2 / 13 |
| 12 | 2.99 | **66.9%** | 7 / 9 |
| 16 | 1.67 | **119.8%** | 8 / 8 |
| 18 | 0.09 | **2222.2%** | 10 / 10 |

Not uniformly wrong: at round 18 (spread 0.09) flagging everything as tied is arguably
*correct*. The genuine defect zone is the **transition, roughly rounds 10–16**, where the band
exceeds most of the field spread while the field still has real relative structure — at round
12 a gap of 1.88, **63% of the entire field range**, is labelled "field noise, not ordering
signal."

This is live user-facing behaviour (a Decision Force badge and a debate-prompt line), and it
is the same absolute-constant-meets-collapsed-scale class as every other defect this audit
found. **It must not be fixed by tuning 2.0** — the issue is absolute vs relative, and any fix
interacts with the selection-bridge question.

## What a selection bridge would have to satisfy

If the extension in §2 is chosen, three measured constraints bind it:

1. **Current necessity is the wrong input.** ρ(necessity, TAV) = 0.315–0.879; its `standout`
   term *is* a TAV margin and its `roster_fit` term *is* `need_bonus + eligibility_bonus`,
   both already inside TAV. Reordering by it would re-amplify TAV and double-count roster fit.
2. **`NEAR_TIE_BAND` is not a safe gate.** A complete-group `waiting_cost` tiebreak over
   near-tie groups would change the pick in **29 of 43** such decisions (67%) — that is a
   re-ranking, not a tiebreak.
3. **The signal is regime-dependent**, so any bridge is a *handoff*, not a constant blend.

**The idea is nonetheless empirically motivated.** At 7.05 the mechanism does exactly what is
wanted, with no positional rule anywhere: `DEF G Packers` (TAV 104.00, waiting 12) vs
`QB J Hurts` (TAV 104.00, waiting 70) — identical acquisition value, and the tiebreak
correctly prefers the quarterback. *"This value isn't going anywhere"* expressed as a
**decision**, not as a valuation adjustment.
