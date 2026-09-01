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

---

# Appendix — where TAV saturation actually comes from

Commissioned as a surgical follow-up: *is TAV saturation a truth (the remaining assets really
are equivalent) or an artifact (the machinery destroys differentiation that still exists)?*
Everything in the previous appendix is downstream of this distinction.

**Verdict: artifact.** Normalization artifact, enabled by a replacement-definition artifact.
Upstream equivalence and legitimate saturation are both ruled out by measurement.

### Layer decomposition, candidate-set spreads

| rd | n | proj | replacement | **VOR** | %VOR>0 | maxRemVOR | **bpa** | uv | tav |
|---|---|---|---|---|---|---|---|---|---|
| 8 | 13 | 325.0 | 226.0 | 292.0 | 46% | 1.0 | 100.00 | 100.00 | 104.00 |
| 10 | 9 | 83.0 | 226.0 | **197.0** | 0% | 0.0 | **0.00** | 6.57 | 7.05 |
| 12 | 9 | 162.0 | 226.0 | **151.0** | 0% | 0.0 | **0.00** | 2.99 | 2.99 |
| 18 | 10 | 198.0 | 226.0 | **80.0** | 0% | 0.0 | **0.00** | 0.09 | 0.09 |

Projections and VOR retain **80–197 points of spread through round 18**. `bpa` is exactly
`0.00`. The information is alive at the input to normalization and dead at its output.

### The first collapsing layer

**`_scale_vor_to_bpa`.** Round-12 candidate VORs: `−41, −100, −116, −135, −96, −151, −126, 0,
−7`. A player at −41 is genuinely far closer to his position's best-remaining than one at
−151. All map to `0.00`.

### The enabling cause, one layer up

At round 12 `replacement_ranks` returns **1 for every position** — demand fully exhausted. So
"replacement" silently stops meaning *the freely-available alternative* and starts meaning
*the single best player still on the board*. Every player is then below replacement **by
construction**, `max pool VOR = 0.0`, and the whole field lands in the range where BPA is
*defined* flat — by `clip(lower=0)` and by the `reference <= 0` early return.

### The defect class: semantic drift

`_scale_vor_to_bpa`'s documented rule — *"a player below replacement level clips to 0, not a
negative score: they'd make a roster worse than not drafting anyone there"* — is **correct
under the original meaning of replacement and meaningless under the exhausted-demand
meaning.** The rule never learned that its input changed definition.

Same class as the growth artifact (a neutral default standing on one side of a difference),
the Sanders collision (an identity namespace that outgrew its data domain), and
`NEAR_TIE_BAND` (an absolute constant meeting a collapsed scale).

### Consequences — two prior findings are reclassified as symptoms

1. With `bpa` dead, `universal_value` at round 12 is decided **entirely by
   `time_horizon_adj`** (2.99 / 2.63 / 2.84 / 1.33 / 1.41) — a small bounded dynasty nudge,
   designed to sit *on top of* a value anchor, now serving as the whole decision. Structurally
   identical to the round-5 defense pick and to the growth artifact.
2. `NEAR_TIE_BAND`'s late explosion is a **symptom** of TAV spread collapsing, not an
   independent defect. And `waiting_cost`'s measured late orthogonality to TAV may be
   substantially an artifact of **late TAV being noise rather than signal** — which means the
   selection-bridge case has to be re-evaluated after this is resolved, not before.

**No fix proposed.** Any repair touches the master VOR/BPA equation.

---

# Appendix — replacement at demand exhaustion

Investigation only. **No implementation.** Traces `_remaining_demand_rank → replacement_levels
→ VOR → _scale_vor_to_bpa` and proposes a contract for the boundary. Every number below is
measured with production functions against the completed 12×20 audit board; no math is
reimplemented and nothing is tuned.

## The seven questions

### Q1 — Where exactly does the conflation happen?

`draft_room.py:659–660`, in `_remaining_demand_rank`:

```python
remaining_demand = max(num_teams * slot_counts.get(position, 0) - drafted.get(position, 0), 0)
return max(1, round(remaining_demand))
```

Two clamps in two lines. The first floors a negative surplus at `0`; the second converts that
`0` into `1`. So `remaining_demand = 1` ("one league-wide starter slot is still unfilled") and
`remaining_demand = 0` or `−49` ("no starter slot creates demand here any more") all return
rank `1`. This is a **`None`-encoded-as-a-value collapse** — the same class as the growth
artifact's neutral `50.0` default standing on one side of a subtraction.

### Q2 — What did VOR originally mean, and is the "dynamic" claim real?

`replacement_levels`' docstring claims the remaining-demand subtraction is what makes the
anchor *"genuinely dynamic."* **Measured: it is algebraically inert.**

Replacement level, recomputed at every 12th pick across the whole board, against the *static*
level computed with `drafted={}`:

| pick | 0 | 12 | 24 | … | 144 | 156 | … | 216 |
|---|---|---|---|---|---|---|---|---|
| QB | 324.0 = | 324.0 = | 324.0 = | = | 324.0 = | 324.0 = | = | 324.0 = |
| RB | 178.0 = | 178.0 = | 178.0 = | = | 178.0 = | 178.0 = | = | 178.0 = |
| WR | 210.0 = | 210.0 = | 210.0 = | = | 210.0 = | 210.0 = | = | 210.0 = |
| TE | 187.0 = | 187.0 = | 187.0 = | = | 187.0 = | 187.0 = | = | 187.0 = |
| K  | 105.0 = | 105.0 = | 105.0 = | = | 105.0 = | 103.0 **X** | X | 103.0 **X** |
| DEF| 98.0 = | 98.0 = | 98.0 = | = | 98.0 = | 98.0 = | = | 98.0 = |

19 of 19 sample points identical for five of six positions across all 240 picks. K moved
exactly once, by 2 points.

The identity: with `D` = static demand and `d` already drafted **from above the anchor**, the
rank is `r = D − d`, and the `r`-th best of the *remaining* pool is the `(d + r)`-th best of
the *original* pool — which is the `D`-th best, always. **The subtraction and the pool drain
cancel exactly.** The mechanism only ever moves the number when picks come from *below* the
anchor (K's single 2-point step) or when the clamp fires.

So VOR's original meaning is the classic static one: *points above the `D`-th best player in
the pre-draft field*, `D = num_teams × starter_slot_counts[p]`. The "dynamic" language
describes a no-op.

### Q3 — Where does the rank become a value?

`draft_room.py:647–648`:

```python
idx = min(rank - 1, len(at_pos) - 1)
levels[position] = float(at_pos.iloc[idx][value_col])
```

`at_pos` is the **currently available** pool, sorted descending. So `rank = 1` resolves to *the
best player still on the board*. The demand being ranked against is measured league-wide
(every starter slot, including filled ones); the pool it is ranked into contains only
undrafted players. **The two are on different bases.** The `− drafted` subtraction is what
reconciles them, and it is valid only while the result is `≥ 1`.

### Q4 — Is the collapse documented as intended?

Yes, twice, which is why it survived this long.

- `replacement_levels`' own docstring: *"drain a position past its real demand and the target
  collapses to 1 (replacement = the best player still on the board), correctly driving everyone
  left there toward ~0 VOR."*
- `upside_score`'s guard comment at `draft_room.py:1018` states it as a settled fact:
  *"Because bpa collapses to 0.00 board-wide once positional demand is exhausted (every
  position, not just offense), growth becomes the SOLE ranking term at that point."*

The second is the more serious finding: **the collapse was observed, measured, and worked
around at a neighbouring term, but never traced to its owner.** A guard was added to
`upside_score`'s *other* input instead of the dead one being questioned.

### Q5 — What should replacement mean, economically, once no starter slot creates demand?

Replacement level prices *the alternative you are guaranteed to be able to obtain*. Starter
slots are one source of that guarantee, not the only one; when they are exhausted, demand
passes to bench capacity and then to the waiver wire. Demand exhaustion does not mean
replacement ceases to exist — it means **the starter-slot model has stopped being the right
instrument for measuring it.**

The current answer inverts the economics. At exhaustion the anchor becomes *the best remaining
player at the position*, which asserts that the scarcest thing left there is freely available.
That is precisely backwards, and it is why every player lands below replacement by
construction.

The correct successor question is already named and already implemented in this module:
`horizon_replacement` — *the best player expected to still be undrafted when the draft ends*.
Its basis is the whole draft rather than this instant, so it does not degenerate the way a
"right now" anchor does.

**One case must be preserved, not repaired.** When a position will genuinely lose no further
players, the best available player *is* what waiting gets you, and VOR ≈ 0 there is **correct**.
A contract that manufactured spread in that case would be worse than the current collapse:
confidently wrong instead of visibly dead. This is the floor any repair has to respect, and it
is the reason "restore differentiation" is the wrong objective.

### Q6 — Can that meaning be represented without an absolute positional-consumption prior?

**Partly — and the measurement says the naive version fails.**

Hypothetical, measured but not implemented: hand off to `horizon_replacement`'s anchor *only*
for positions whose remaining starter demand has hit zero, leaving every other position
untouched.

| pick | exhausted | max pool VOR now | max pool VOR w/ handoff | top-8 now | top-8 w/ handoff |
|---|---|---|---|---|---|
| 96 | — | 1.0 | 1.0 | WTQKDWTR | WTQKDWTR |
| 108 | QB,RB,WR | 0.0 | 126.0 | WTRQKKDD | QRRQRRQR |
| 132 | QB,RB,WR,TE | 0.0 | 123.0 | WTRQKKDD | TTTTTRRT |
| 144 | +DEF | 0.0 | 121.0 | WTRQKDDW | **TTTTTTTT** |
| 168 | all six | 0.0 | 71.0 | WTRQKDDW | **RRRRRRRT** |
| 216 | all six | 0.0 | 47.0 | WTRQKDDW | QQRRRRWW |

The scale revives — **without touching `_scale_vor_to_bpa` at all**, which confirms the BPA
collapse is a downstream consequence rather than an independent defect. But the board goes
**degenerate at exactly the failure mode the earlier reverted attempt produced**: all-TE at
pick 144, all-RB at 168.

The cause is one layer further up. `horizon_replacement`'s rank is
`expected_positional_consumption − drafted`, and that estimator is wrong by large,
position-specific margins **on the very board it is watching**:

| at pick 192 (48 picks left) | QB | RB | WR | TE | K | DEF |
|---|---|---|---|---|---|---|
| predicted still to go | 5.3 | 12.1 | 16.1 | 6.8 | **3.7** | **4.1** |
| actually still to go | 10 | 2 | 31 | 5 | **0** | **0** |

K and DEF were *fully consumed* at pick 192; the model asserts 3.7 and 4.1 more. RB: 12.1
predicted against 2 actual. WR is under-predicted by 15 from pick 0 through pick 192 and never
converges. The totals conserve to 240 — the error is entirely in the allocation.

This is not a bad prior. It is **structural**:

```python
observed_share = {p: drafted.get(p, 0) / picks_made for p in FANTASY_POSITIONS}
blended_share  = (1 - w) * prior_share + w * observed_share
```

`observed_share` is strictly positive for any position that has *ever* been drafted, and it is
multiplied by the remaining picks. So even at `w = 1.0` (pure observation, end of draft) the
model **cannot express "this position is finished."** It has no notion of saturation.

That defect is fixable with **no external data**: measure observed share over a *recency
window* rather than the whole draft, so a position that has stopped going reads as finished.
It is position-agnostic, derived from the draft itself, and needs nothing this module does not
already have. The window length is a design choice, which makes it **your call, not mine**.

### Q7 — If not, what external data is required?

For the *split* of bench picks across positions: real completed startup boards in this format.
`positional_bench_appetite`'s docstring already states the bar — one board fixed QB (52.3 vs
52 actual) and broke K and DEF (~15 and ~14 actual, driven to ~25 each), so *"whatever replaces
this has to satisfy both ends, and that needs more than one draft to derive honestly."* That is
task #49 and it stands.

But the **regime that matters most does not need the split to be right.** A position at zero
further consumption is identifiable from the draft's own recent history. So the external-data
dependency is narrower than assumed: it gates *calibrated late-round pricing*, not
*correctness at the exhaustion boundary*.

## The deepest point

**No "best available" anchor can produce VOR at exhaustion — including a correct one.** If
`expected_positional_consumption` were perfect, a truly finished position would return
`still_to_go = 0` → horizon rank 1 → anchor = best available → VOR = 0. Identical collapse.

The collapse is inherent to the question, not to the estimator. Which means the repair is not
a better anchor. It is **admitting that VOR has a domain of validity and declining outside it.**

## Proposed contract — replacement at demand exhaustion

**Domain.** `replacement_levels[p]` is defined only while position `p` has at least one
unfilled league-wide starter slot. Inside that domain it means: *the value of the `D`-th best
player in the pre-draft field*, `D = round(num_teams × starter_slot_counts[p])` — the player a
team is guaranteed to be able to start without spending a premium pick.

**Exhaustion is a state, not a value.** When
`num_teams × starter_slot_counts[p] − drafted[p] < 1`, starter-demand replacement is
**undefined** and must be reported as undefined. Not rank 1. Not `0.0`. Not the best available
player. Both current encodings assert something false: rank 1 claims a slot still needs
filling, and the value it resolves to claims the scarcest remaining player is freely available.

**VOR inherits the domain.** Where replacement is undefined, VOR is undefined for every player
at that position, and `bpa` — a normalization of VOR — inherits it.

**Outside the domain the engine declines and says so.** It must not clamp, must not substitute
a different anchor under the same name, and must not let a downstream term silently become the
whole decision. `universal_value` must not be permitted to reduce to
`time_horizon_adj + risk_adj` without the board declaring that it has.

**The floor is preserved.** A position that will lose no further players has VOR ≈ 0 correctly.
The contract must never manufacture spread there.

## Smallest owner-layer change

Two edits in `draft_room.py` — the layer that owns the definition. Neither touches the VOR
formula, the scarcity curve, positional weighting, `_scale_vor_to_bpa`, or `clip(lower=0)`.

1. **`_remaining_demand_rank` → `Optional[int]`.** Return `None` when remaining demand `< 1`;
   delete the `max(1, …)` clamp. Two call sites: `replacement_levels`, `replacement_ranks`.
2. **`replacement_levels` omits the key on `None`** rather than emitting a value. Every
   consumer must treat a missing key as *no opinion*, never as zero — the same discipline
   `horizon_replacement` already enforces with `value=None, certain=False`.

**Why removing `clip(lower=0)` cannot substitute for this**, mechanically: with the pool max
VOR at exactly `0.0`, `_scale_vor_to_bpa` returns all zeros from its `reference <= 0` early
return — **before the clip is ever reached**. Deleting the clip changes nothing in the dead
regime. The instinct to reject that path was correct.

**And note why max pool VOR sits at exactly `0.0` rather than going negative:** the anchor is
the `D`-th best *original* player, and in this board he is *never drafted*. From pick 108
onward he simply **is** the best player remaining at his position. Max pool VOR reaches `0.0`
at pick 108 — **round 10, with 55% of the draft still to come** — and stays there.

## What this change buys, stated honestly

It converts a silent wrong number into an explicit absence. It does **not** restore late-round
differentiation, and it is not meant to: rounds 10–20 would report *no VOR available* instead
of reporting `0.00`. Strictly more honest, strictly less useful, until a successor anchor
exists. Every downstream consumer then has to declare what it does with the absence, and each
of those declarations is a policy decision.

**Unblocked by it:** `replacement_ranks` stops telling `narrow_candidates` that an exhausted
position has depth 1.

**Not unblocked by it:** a live late-round board. That needs the successor anchor, which needs
`expected_positional_consumption` to be able to say *finished*.

## Decisions for the owner — not taken here

1. **Saturation in `expected_positional_consumption`.** Recency-windowed observed share (no
   external data, window length is a design choice) versus calibrating
   `positional_bench_appetite` against real boards (task #49, needs more than one). The first
   would partially unblock Phase 3 ahead of the data.
2. **What the board does when `bpa` is undefined.** Decline to rank? Rank on a declared
   secondary basis with the regime shown? Today it silently ranks on `time_horizon_adj`.
3. **Whether `horizon_replacement` becomes VOR's anchor outside the starter-demand domain**,
   and if so whether it may act while `certain=False`.

---

# Appendix — can consumption ever reach zero?

Investigation only. **No implementation.** Task #59. Measured across **six completed simulation
boards** (`12x20 final-audit`, `balanced-forced`, `postfix-auto`, `K-DST`, `12x14 K-DST`,
`12x20 IDP`) using production functions. The windowed variants are a replica of
`expected_positional_consumption` whose fidelity is asserted against the production function at
`window=None` before any variant runs, so a window can only differ from production by the window.

## Q1 — What is it trying to represent economically?

Its docstring says *"expected TOTAL players taken at each position across the whole draft."* Its
only consumer is `horizon_replacement`, which converts it to a **rank**:
`still_to_go = consumption − drafted`, `rank = still_to_go + 1`, indexed into the remaining pool.
So a ±4-player error is a ±4-rank displacement of the anchor — and the module's own
`HORIZON_SENSITIVITY_WINDOW` measurement says ±6 ranks moves the floor by 12 points at DEF and
63 at QB.

The intended object is **residual demand**: a stock that gets consumed and can run out. The
implemented object is a **share of the remaining picks**: a flow proportion that conserves the
total and cannot run out. Every share-based estimator in the measurements below returns
`sumErr ≈ 0.0` at every checkpoint on every board — the total is always exactly right and the
split is always wrong. **The economic concept and the implementation are different kinds of
quantity.** That is the whole of #59.

## Q2 — Why lifetime observed share cannot reach zero

```
consumption[p] = drafted[p] + remaining_picks × blended_share[p]
blended_share[p] = (1−w)·prior_share[p] + w·observed_share[p]
```

`prior_share[p] > 0` for any position with a starter slot; `observed_share[p] = drafted[p]/picks_made > 0`
for any position ever drafted. So `blended_share[p]` is **strictly positive**, and

```
still_to_go = consumption − drafted = remaining_picks × blended_share[p] > 0
```

for every position anyone could care about, until `remaining_picks` itself hits zero. The only
reachable zero is a position with no starter slot that has never been drafted — the one case
where the answer does not matter. Measured: at pick 192 of the final-audit board, K and DEF are
**fully consumed** and the model asserts 3.7 and 4.1 more.

## Q3 — Does a recency window solve the semantic problem?

**No. It is worse than neutral, on three measured grounds.**

**(i) It does not improve accuracy.** Mean absolute error against actual final consumption,
across 23 board-rounds spanning all six boards:

| estimator | window=60 | window=48 | window=36 | **current** | window=24 | capacity | window=12 |
|---|---|---|---|---|---|---|---|
| MAE | 10.18 | 10.25 | 10.34 | **10.40** | 10.54 | 10.72 | 11.64 |

The whole spread is 1.5 MAE on a base of ~10, and the best-performing window is the one closest
to lifetime. **Choosing a window here is choosing noise.**

**(ii) It still cannot reach zero.** Same algebra — a windowed `observed_share` is still ≥ 0 and
the prior term keeps the blend strictly positive.

**(iii) It destroys an invariant the current model satisfies.** Controlled test: two 96-pick
sequences with **identical per-team rosters, identical league tallies, and the identical set of
players removed**, differing only in *when* the kickers were taken (all in round 1 vs all in
round 8). True remaining demand is 0 in both.

| estimator | K taken late | K taken early | swing |
|---|---|---|---|
| current | 17.6 | 17.6 | **0.0** |
| window=36 | 29.6 | 10.4 | 19.2 |
| window=24 | 39.2 | 10.4 | 28.8 |
| window=12 | **68.0** | 10.4 | **57.6** |
| capacity | 9.2 | 9.2 | **0.0** |

Remaining demand cannot depend on the order in which past picks arrived. The current model is
correctly order-invariant; **a window removes that property.** It makes the number behave
differently without making it mean anything different.

## Q4 — Windows against the boards

Representative, `12x20 IDP` at round 16 (actual final: K 35, WR 67, RB 31, DEF 32, TE 20):

| estimator | K | WR | RB | DEF | TE | MAE |
|---|---|---|---|---|---|---|
| current | 30.8 | 58.3 | 37.9 | 23.6 | 21.5 | 4.7 |
| window=12 | 45.0 | 48.9 | 31.9 | 39.0 | 18.1 | 4.5 |
| window=24 | 49.8 | 50.5 | 31.9 | 32.6 | 18.1 | 4.1 |
| window=48 | 37.8 | 61.7 | 33.5 | 26.2 | 18.9 | **2.7** |
| capacity | 28.0 | 54.1 | 39.1 | 23.0 | 23.7 | 6.4 |

No window dominates across boards or rounds; the ranking reshuffles at every checkpoint. There is
no window that is *right*, only windows that happen to fit one board-round.

## Q5 — Pathological cases

Predicted **remaining** consumption; true value in the header.

| case | truth | current | win12 | win24 | win36 | capacity |
|---|---|---|---|---|---|---|
| (a) heavy early, then ignored 48 picks — RB | 4.0 | 46.8 | 30.0 | 30.0 | 30.0 | 31.0 |
| (b) untouched 84 picks, then a full-round burst — K | 0 | 17.6 | **68.0** | 39.2 | 29.6 | **9.2** |
| (c) never drafted once in 96 picks — DEF | 12 | 5.8 | 5.8 | 5.8 | 5.8 | **13.9** |
| (d) exactly one per team, genuinely exhausted — K | 0 | 17.6 | 10.4 | 10.4 | 10.4 | 9.2 |

- **(b) is the window's worst case.** A short window sitting on top of a positional run
  extrapolates that run forever: `window=12` forecasts **68 more kickers when the true answer is
  zero**. The shorter the window, the more catastrophic.
- **(c) is the window's blind spot by definition.** Zero picks is zero picks in every window, so
  every windowed variant returns *exactly* the current answer. A window cannot help a position
  that has not been drafted — which is precisely the position whose demand is entirely unmet.
- **(d) confirms Q2**: nothing reaches zero.

## Q6 — Satisfied demand vs. a temporary deviation

**It cannot distinguish them, and the sign is inverted.** Two 96-pick sequences, neither with a
kicker in the last 48 picks. A: all twelve teams already hold a kicker (true remaining 0).
B: no team holds one (true remaining 12).

| estimator | A (satisfied) | B (untouched) | gap | verdict |
|---|---|---|---|---|
| current | 17.6 | 7.1 | **−10.5** | cannot distinguish — inverted |
| window=12 / 24 / 36 | 10.4 | 7.1 | **−3.3** | cannot distinguish — inverted |
| capacity | 9.2 | 15.5 | **+6.3** | distinguishes |

The share model predicts **more** kickers for the league that already has them and **fewer** for
the league that has none. The reason is semantic, not statistical: **an observed-share model
reads a pick as evidence of appetite, when a pick is consumption of demand.** Those have opposite
signs. Recency reweights that evidence; it does not change what the evidence is taken to mean.

And the confound is unidentifiable *in principle* from the pick stream alone — "no recent picks
at p" is produced equally by "demand satisfied" and "the room deviated." The only thing that
separates them is **roster state**, which no share-based estimator ever looks at.

## Q7 — A bounded quantity that actually reaches zero

**Yes — for the half that matters, with no window, no prior, and no external data.**

```
remaining_starter_demand[p] = Σ over teams of max(slots[p] − filled_team[p], 0)
```

Measured properties: bounded in `[0, num_teams × slots[p]]`; reaches **exactly 0.0** when every
team has filled its slots at `p`; **order-invariant** (swing 0.0 in the controlled test); the
**only** estimator that distinguishes satisfied from untouched; and derivable entirely from
`roster_positions` plus observed picks.

The engine already computes something with this name — `num_teams × slot_counts[p] − drafted[p]` —
but **aggregated**, and the aggregate is not the sum of the per-team demands, because
`max(·, 0)` does not distribute over a sum. **One team hoarding at a position cancels another
team's unmet need at the same position.** Measured on the real boards:

| | aggregate | per-team | shift |
|---|---|---|---|
| mean first round declared exhausted (32 board-positions) | rd 10.8 | rd 12.7 | **+2.0 rounds** |
| final-audit TE | rd 10 | rd 16 | +6 |
| final-audit RB | rd 9 | rd 13 | +4 |
| 12x20 K-DST TE, 12x14 K-DST TE, IDP RB, IDP TE | rd 10–12 | **never** | — |

Four board-positions are declared exhausted 8–10 rounds before the end by the aggregate while
**never actually satisfying their starter demand at all**.

The bench half stays a prior — but it too is bounded:
`remaining_bench_capacity = Σ_t max(roster_slots − picks_t − starter_need_t, 0)` reaches zero
exactly when rosters fill. Only the **split of that capacity across positions** is irreducibly a
claim about behaviour.

**So the answer is: stop asking this function to be one number.** It currently fuses an
exactly-derivable bounded stock with an irreducible behavioural prior, and the fused number
inherits the worst property of each — neither exact, nor honest about its uncertainty.

## Two further defects found on the way

**A. `positional_bench_appetite` returns 0.0 for every position once nothing is measurable.**
When no position passes its measurability test, `rates` is empty, `mean_rate` falls back to
`0.0`, and every position gets `demand × 0.0 = 0.0`. Downstream,
`expected_positional_consumption` then drops the **entire bench term** from its prior
(`bench_picks * appetite[p] / appetite_total if appetite_total else 0.0`).

| board | first round with no measurable position |
|---|---|
| 12x20 K-DST | **rd 16** |
| 12x20 balanced-forced | **rd 18** |
| 12x20 IDP | **rd 18** |

On `final-audit` it never fully collapses, but **from round 12 only K is measurable**, so every
other position's bench appetite becomes the kicker's decay rate for the rest of the draft.

The function's own docstring says an unmeasurable position must inherit the mean of the
measurable ones, because a zero *"would assert 'this position is never benched', which is a
claim, not an absence."* The guard handles the per-position case and misses the all-positions
case — producing exactly the outcome it was written to prevent. Same defect class as everything
else in this audit: **a missing-information path that returns a confident zero instead of
declining.**

**B. Latent: `remaining_picks` is overstated in a league that drafts a zero-demand position.**
`picks_made` is summed from the tally *after* the zero-starter-demand filter, while `total_picks`
counts every slot. Those picks happened; excluding them from `picks_made` asserts they did not.
The docstring's own motivating scenario — 36 kicker placeholders in a league rostering no kicker —
would leave the model believing there are 36 more picks to allocate than exist, for the whole
draft, and would also hold `w = picks_made / total_picks` low so it stays on the prior longer.
Does not fire on any of the six measured boards; stated because the trigger condition is exactly
the scenario the surrounding comment was written for.

## Verdict on the abstraction

**Observed share is the wrong abstraction, and no window rescues it.** It answers "what does this
room like?" when the question is "what does this room still need?" Those are different questions
with opposite signs, and the measurements above show the estimator answering the first one while
being read as though it answered the second.

The window was worth testing and it failed on its own terms: it does not improve accuracy, it
cannot reach zero, it is blind to the never-drafted case, it amplifies positional runs, and it
sacrifices order-invariance to buy none of that back.

## The smallest set of design decisions before implementation

1. **Does remaining starter demand become per-team?** A pure correctness fix requiring no prior —
   but it moves the anchor's domain boundary ~2 rounds later and leaves four measured
   board-positions never exhausting, so it is a semantic change, not a bug fix.
2. **Does `expected_positional_consumption` split into three named quantities** —
   `remaining_starter_demand` (exact, bounded, reaches zero), `remaining_bench_capacity` (exact,
   bounded, reaches zero), `bench_split` (the only prior) — or stay one fused number?
3. **What does the bench split do with no evidence?** Today it silently becomes 0.0 and the bench
   term vanishes. Decline and return no opinion (matching `horizon_replacement`), or hold the last
   measurable rate?
4. **Does the successor anchor need the bench half at all?** If the late-draft anchor is permitted
   to answer *no opinion* — as the exhaustion contract already proposes — the bench prior never
   touches valuation, and **task #49's external-data dependency leaves the critical path
   entirely.** If a live late-round board is required instead, the bench prior is load-bearing and
   #49 returns to it. **This decision determines whether #49 blocks Phase 3.**

---

# Appendix — dependency map and the minimal decomposition

Investigation only. **No implementation, pending sign-off.** Traces every producer and consumer
of `expected_positional_consumption`, `positional_bench_appetite`, `horizon_replacement`,
`waiting_cost`, and `replacement_levels` across the production surface (`draft_room.py`,
`pick_synthesis.py`, `draft_board_ui.py`, `roster_diagnostics.py`, `app.py`,
`draft_strategy.py`).

## The dependency chain

```
roster_positions ─┬─> starter_slot_counts ─┬─> _remaining_demand_rank ─┬─> replacement_levels ─> _vor ─> _scale_vor_to_bpa ─> bpa
                  │                        │        [CLAMP >= 1]       │                                       │
                  │                        │                           └─> replacement_ranks                   └─> universal_value ─> TAV
                  │                        │                                    └─> position_view_depth ─> narrow_candidates
                  │                        ├─> positional_bench_appetite ──┐
                  │                        └─> expected_positional_consumption ─> horizon_replacement ─> _attach_waiting_cost
                  └─> draftable_slots_per_team ──────^                                                        │
                                                                          {horizon_floor, horizon_sensitivity, waiting_cost}
picks ─┬─> _drafted_counts_by_position  (LEAGUE-WIDE — feeds everything above)      └─> CandidateSnapshot ─> draft_board_ui._waiting_note
       └─> _team_starters_filled        (PER-TEAM — exists, feeds need_bonus only)

qb_startable_floor ─> startable_floors ─> replacement_levels   [SECOND CLAMP >= 1]

roster_diagnostics ─> compute_draft_board ─> scored_pool ─> replacement_levels("universal_value") ─> replacement_level_surplus
```

**The single most important structural fact:** `positional_bench_appetite` has exactly one
consumer (`expected_positional_consumption`), which has exactly one consumer
(`horizon_replacement`), which has exactly one consumer (`_attach_waiting_cost`), which is
documented and verified observable-only — *"team_acquisition_value is computed and rounded
before this runs and is byte-identical with these columns present or absent."*

**The inferred branch is already fully isolated from valuation.** The decomposition does not need
to create that separation. It needs to avoid breaking it.

## Semantic classification

| Quantity | Semantic type | Honest today? |
|---|---|---|
| `starter_slot_counts` | exact / bounded observable | yes |
| `draftable_slots_per_team` | exact / bounded observable | yes |
| `drafted_counts_by_position` | exact observable, **aggregated** | yes as a count; **no** as a demand input |
| `_team_starters_filled` | exact / bounded, **per-team** | yes — already correct, isolated to `need_bonus` |
| `_remaining_demand_rank` | claims exact; **is clamped** | **no** — 0 and 1 conflated |
| `qb_startable_floor` | exact-ish, honest `None` | yes — but its *count* is clamped |
| `replacement_levels` | **valuation anchor** | **no** — inherits both clamps |
| `replacement_ranks` | contextual / display | **no** — inherits the clamp |
| `positional_bench_appetite` | **inferred behavioural** | **no** — returns `0.0` for "unknown" |
| `expected_positional_consumption` | **fused** exact + inferred | **no** — the fusion *is* the defect |
| `horizon_replacement` | optional / unknown-aware | **yes** — the model the rest should follow |
| `horizon_floor` / `waiting_cost` / `horizon_sensitivity` | contextual / debate | yes — `None` discipline correct |
| `replacement_level_surplus` | contextual / diagnostic | **becomes undefined** under decomposition |

## The six questions

### 1. Can per-team starter demand replace the current component without silently changing meaning?

**Not silently — and one of the two affected consumers is the valuation anchor.**

- `replacement_ranks → position_view_depth`: **safe.** Depth grows and persists later; the
  existing `POSITION_VIEW_DEPTH_CAP` already bounds it. No valuation impact.
- `replacement_levels → _vor → bpa → universal_value → TAV`: **not silent.** Measured, the
  exhaustion boundary moves **+2.0 rounds on average**, TE moves +6 on the final-audit board,
  and four board-positions never exhaust at all. Every affected player's `bpa` changes. That is
  the intent — but it must be declared, not slipped in.

**Migration hazard — `demand_picks`.** That parameter exists *because* the aggregate collapses
when seeded with a prior draft's history (its docstring records a backup-tier rookie QB
outranking a legitimate rookie WR). Per-team demand computed against each team's *true* roster
is correct in that scenario by construction — but `demand_picks` supplies a **scoped** history,
not a per-team one. Fed a rookie-only history, per-team demand sees twelve empty rosters and
claims **full starter demand at every position** — strictly worse than today. This must be
proven out, not assumed away.

### 2. Can `None` propagate safely where the old model emitted a number?

Three sites, three different answers.

- **`horizon_floor` / `waiting_cost` / `_waiting_note`: yes, already correct.** `.map()` on a
  missing key yields NaN, `_records_with_normalized_nan` converts NaN to `None`,
  `CandidateSnapshot` types them `Optional[float]`, `_waiting_note` returns `None`. Built for
  absence.
- **`compute_draft_board`'s VOR: NO — absence is already swallowed.**
  `point_replacement.get(r["position"], r["_points"])` defaults to *the player's own points*,
  giving VOR = 0.0. Omitting the key produces **exactly the dead-zone number the contract exists
  to eliminate**, with no signal. Same at `tv_replacement.get(..., r["trade_value"])`.
  **The "omit the key" proposal from the exhaustion appendix is necessary but not sufficient.**
- **`replacement_ranks → position_view_depth`: hard crash.** `min(None, 12)` raises `TypeError`.
  Loud rather than silent, but `Optional[int]` cannot ship without changing that signature.

### 3. Can the successor anchor operate entirely from exact starter demand?

**Yes, and it already nearly does.** `replacement_levels` reads only `starter_slot_counts`,
`drafted_counts`, and the pool — it never touches `positional_bench_appetite` or
`expected_positional_consumption`. **The valuation anchor has zero dependency on the inferred
branch today**, and the decomposition preserves that rather than establishing it.

Outside its domain, the previous appendix established that no "best available" anchor produces
VOR — *including a perfectly estimated one*. The successor anchor does not want the bench half;
it wants permission to decline.

### 4. Can bench appetite be demoted to contextual without a silent substitution?

**Yes — it is already contextual.** One consumer, three hops, all observable-only.

The one substitution risk is *inside* the branch:
`still_to_go = max(consumption.get(position, 0.0) − drafted, 0.0)` → `rank = 1` →
**anchor = best available, marked `certain=True`.** A missing consumption key does not propagate
as unknown; it propagates as *"this position is finished, and here is a confident floor."* That
must become `certain=False, value=None`.

### 5. Do `waiting_cost` and `horizon_replacement` retain a dependency on the fused semantics?

**Yes — and it is the only one left.** `horizon_replacement`'s rank is
`expected_positional_consumption − drafted`, the fused number. Under the decomposition it must
consume the halves separately: the exact half says how many are *certain* to go, the inferred
half how many *might*. **When the inferred half is `None`, the horizon rank is a lower bound,
not a point estimate**, and `certain` must say so. `horizon_sensitivity` already exists to
qualify a floor sitting on a cliff; an absent bench estimate is the same class of statement and
belongs on the same channel.

### 6. Do #62 and #63 fall out naturally?

- **#62 (appetite all-zero): falls out completely.** Under decision 3, "no measurable position"
  returns `None`, not `0.0`, and the `if appetite_total else 0.0` branch that silently drops the
  bench term disappears because the bench term is `Optional` by construction. No separate
  treatment.
- **#63 (`remaining_picks` overstated): does NOT fall out of a minimal split.** It lives in
  pick-accounting, not demand-modelling. It *does* fall out if the bench half is rebuilt on
  **per-team remaining capacity** (`draftable_slots_per_team − picks_team`), which counts every
  pick a team made regardless of position. **Conditional on decision 2's fuller form.**

## Consumers that become undefined

**1. `roster_diagnostics.replacement_level_surplus` — the headline conflict.**

```python
sum(p["uv"] - repl_levels.get(p["position"], 0.0) for p in players)
```

It defaults a missing replacement level to **`0.0`**, and it runs against the **fully-drafted**
state — past exhaustion for essentially every position. Under the contract every key is omitted,
so:

> `replacement_level_surplus == sum(uv) == accumulated_value`

Two fields on `TeamDiagnostics`, numerically identical, one silently no longer measuring what its
name says. **This is a migration problem, not something to design around.**

The resolution is available and is not a workaround: the inertness finding (#60) established
that the anchor **never moves from the static pre-draft level** anyway. So this metric has always
been *"value above the `D`-th best player in the pre-draft field"* — it can keep exactly that
meaning by naming the pre-draft anchor explicitly. That is not preserving a wrong behaviour; it
is naming what the number actually was.

**2. `pick_synthesis.position_view_depth` — hard break.** `min(None, 12)` raises. Needs an
explicit "no starter demand → depth 1" rule. Depth 1 is *semantically correct* here (a position
with no starter demand should surface its single best player, not a deep board) — but it must be
written down, not inherited from a clamp that means something else.

**3. `compute_draft_board`'s two `.get(pos, own_value)` calls** — silent substitution, above.

**4. `horizon_replacement`'s `consumption.get(position, 0.0)`** — silent substitution, above.

## Newly discovered conflicts

**A. A second, independent 0-vs-1 clamp.** In the `startable_floors` branch:
`rank = max(int((at_pos[value_col] >= floor).sum()), 1)`. When **no** remaining QB clears the
startable floor, this says rank 1 = best available — precisely the defect being fixed, and
**not touched by fixing `_remaining_demand_rank`.** Superflex QB carries its own copy.

**B. The `.get(..., default)` layer is the real barrier.** Three of the four absence sites
convert a missing key into a number before any consumer can notice. **Changing the producer is
not enough; the consumers are where the meaning is lost.**

**C. `demand_picks` may invert under per-team demand** — see Q1.

**D. `roster_diagnostics` runs the anchor at the maximally-exhausted state**, so it is the one
consumer living entirely outside the proposed domain.

## Proposed minimal architecture

Five named quantities replacing two fused ones, all in `draft_room.py`.

**Exact / bounded observable**

```
remaining_starter_demand(roster_positions, num_teams, picks, players_db) -> dict[pos, float]
    = Σ over teams of max(starter_slot_counts[pos] − team_filled[pos], 0)
    Bounded [0, num_teams × slots]. Reaches exactly 0. Order-invariant. No prior.
    Needs a new producer: team_filled_by_position(picks, players_db) — generalises the
    existing _team_starters_filled from one roster to all of them.

remaining_draft_capacity(roster_positions, num_teams, picks) -> float
    = Σ over teams of max(draftable_slots_per_team − picks_team, 0)
    Bounded. Reaches exactly 0. Subsumes #63 by construction.
```

**Inferred behavioural — `Optional`, never fabricated**

```
estimated_bench_demand(pool, value_col, roster_positions, num_teams, picks)
    -> dict[pos, Optional[float]]
    None when no position is measurable (#62 resolved). Never reaches valuation.
```

**Valuation anchor — exact inputs only, with a declared domain**

```
replacement_levels(...) -> dict[pos, float]      # key OMITTED outside the domain
    Domain: remaining_starter_demand[pos] >= 1, or startable-floor count >= 1.
    Reads ONLY exact quantities. Never reads estimated_bench_demand.
```

**Contextual / debate — unknown-aware**

```
horizon_replacement(...) -> dict[pos, {rank, value, pool_depth, certain, sensitivity}]
    certain=False, value=None when the bench half is None OR the rank runs past the pool.
```

**Three consumer changes that are part of this change, not follow-ups**

1. `compute_draft_board`: `_vor` becomes genuinely optional (NaN where the anchor is absent),
   replacing `.get(pos, own_value)`.
2. `position_view_depth`: explicit no-starter-demand rule.
3. `roster_diagnostics.replacement_level_surplus`: declare the pre-draft anchor, or remove.

**Plus:** close the second clamp in the `startable_floors` branch.

## Invariants and tests required before implementation

**Exactness and boundedness**

1. `remaining_starter_demand[p] >= 0` for every position, pick prefix, and board. (The aggregate
   reaches −71.)
2. `remaining_starter_demand[p] == 0` **exactly** when every team has `filled[p] >= slots[p]` —
   asserted in both directions.
3. **Order-invariance**: any reordering of a pick prefix that leaves per-team rosters identical
   produces identical output. This is the invariant the recency window destroyed; pin it.
4. `remaining_starter_demand[p] <= num_teams × slots[p]`, monotone non-increasing over prefixes.
5. `remaining_draft_capacity` falls by exactly 1 per pick and reaches 0 at the final pick.

**Semantic separation**

6. `replacement_levels` output is **byte-identical** whether `estimated_bench_demand` returns
   real numbers or all-`None`. Proves the anchor never reads the inferred branch.
7. `team_acquisition_value` is byte-identical with the horizon/waiting columns present or
   absent. True today; the decomposition touches that branch, so pin it as a regression.
8. Mutating `positional_bench_appetite`'s return to arbitrary values leaves every player's
   `bpa`, `universal_value`, and `team_acquisition_value` unchanged.

**Absence discipline**

9. Where `remaining_starter_demand[p] < 1`, `replacement_levels` omits `p` **and** every player
   at `p` gets `_vor` NaN — asserted at the column, not just the dict.
10. `bpa` for a player with NaN VOR is `None`/NaN, **not `0.0`**. The anti-regression against the
    current dead zone.
11. `estimated_bench_demand` returns `None`, not `0.0`, when no position is measurable —
    reproducible directly at round 16 of the 12x20 K-DST board.
12. `horizon_replacement` returns `certain=False, value=None` when its consumption input is
    absent, and **never** `rank=1, certain=True`.
13. `waiting_cost` is `None` exactly when `horizon_floor` is `None` — extend the existing
    assertion to the new `None` source.

**Anti-conflation — the defect class this whole audit is about**

14. A position at `remaining_starter_demand == 0` and one at `== 1` produce **different**
    replacement levels. Pins the 0-vs-1 collapse directly.
15. The same assertion on the `startable_floors` path: zero remaining QBs above the floor must
    not equal one remaining QB above the floor.
16. The satisfied-vs-untouched pair from #59: league A (every team holds one) and league B (none
    do), with identical recent pick history, yield `remaining_starter_demand` of `0` and
    `num_teams`. Pins the sign every share model got backwards.

**Migration guards**

17. `replacement_level_surplus != accumulated_value` on a fully-drafted board. Fails today under
    a naive decomposition — which is the point of having it.
18. `position_view_depth` handles the no-starter-demand case without raising.
19. The `demand_picks` rookie-draft scenario: per-team demand fed a rookie-only history must not
    claim full starter demand at every position.

---

# Appendix — the decomposition, implemented

Implemented under sign-off. **Stopped short of one thing**, recorded at the end.

## What changed

Five named quantities in `draft_room.py` replace two fused ones.

| | kind | reaches zero | may be unknown |
|---|---|---|---|
| `remaining_starter_demand` | exact, per-team, bounded, order-invariant | yes, exactly | no |
| `remaining_draft_capacity` | exact, bounded | yes, exactly | no |
| `estimated_bench_demand` | inferred behavioural | yes | **yes — `None`** |
| `replacement_levels` | valuation anchor, exact inputs only | key omitted outside its domain | n/a |
| `horizon_replacement` | contextual | n/a | yes — `certain=False, value=None` |

`expected_positional_consumption` is **removed**, not repaired: it fused an exactly-derivable
stock with a behavioural prior into one number that was neither exact nor honest about its
uncertainty. `team_filled_by_position` is the one new producer; `_team_starters_filled` now
delegates to it, so "what has this team taken" has a single definition.

**Both `>= 1` clamps are closed.** The demand branch returns `None` below one whole unfilled
slot; the `startable_floors` branch declines when no remaining player clears the threshold.

**Every `.get(..., default)` absence site is resolved.** `_vor` is NaN where the anchor is
absent instead of the player's own value minus itself; `_scale_vor_to_bpa` keeps NaN as NaN
including on the all-non-positive early return; `bpa`, `universal_value` and `final_score` are
normalised to `None` in the emitted records; `position_view_depth` has an explicit
no-starter-demand rule; `roster_diagnostics` uses the pre-draft anchor and **excludes and
counts** unpriced players rather than defaulting them to `0.0`.

## Measured: old engine vs new, same 240 picks

Replaying the identical board through both engines isolates the valuation change from any
change in what the engine would pick.

**Demand and anchor.** Round 8, RB: old remaining demand `1.0` → rank 1 → level `178.0`; new
`6.3` → rank 6 → level `162.0`. The old model had already cancelled eleven teams' unmet RB
need against a few teams' surplus. Round 10, QB: old `−7.0` → rank 1 → level `324.0`; new
`0.0` → **declined**. Round 20, WR: old `−71.0` → still reporting a level.

**Live valuation window.**

| | `bpa` spread by round | dies at |
|---|---|---|
| old | 100.0 through rd 8, then **0.00 for rounds 9–20** | round 9 |
| new | 100.0 through rd 14, 23 rows at rd 15, 0 rows from rd 16 | round 16 |

Positions decline progressively as they genuinely exhaust — QB at round 10, WR at 11,
RB/K/DEF at 13, TE at 16 — instead of the whole board going flat at once. **The honest window
is longer than the old dishonest one**: correcting the per-team accounting keeps real
differentiation alive for roughly six more rounds, and what follows is reported as absence
rather than as `0.00`.

**A pick change worth naming.** Round 6 top five by `final_score`:

- old: `DEF WR K WR K`
- new: `WR WR RB RB RB`

Economically: the aggregate had already declared RB/WR/TE demand nearly satisfied at round 6
(one team's surplus cancelling another's need), which collapsed their replacement levels
upward and crushed offensive VOR. K and DEF, whose demand the aggregate happened to measure
correctly, were left standing. Fixing the accounting restores the offensive spread and K/DEF
fall back behind it **without any positional rule** — the same defect the K/DST-too-early
complaint was pointing at, arriving from the demand layer rather than from anything about
kickers.

## Finding: fractional flex shares interact with the domain rule

`starter_slot_counts` spreads a FLEX slot fractionally (1/3 each to RB/WR/TE). A single team's
unfilled FLEX therefore contributes only ~0.33 of demand at any one position, so **flex-only
demand never opens the domain by itself** — it takes three such teams to reach one whole slot.
This is a pre-existing property of the fractional model, invisible while every rank was floored
at 1, and now load-bearing. It is why RB sits at `0.7` and TE at `0.3` late on the audit board
and both decline. Correct under the approved contract ("at least one whole starting slot"), and
recorded because it makes the unpriced regime start earlier than a whole-slot reading would.

## #68 resolved: `demand_picks` is a demand-universe override

Traced rather than assumed. Its only production caller passes `demand_picks=[]`, and `picks`
there carries **one** roster. So the two parameters were never the same universe: `picks` is
"my roster and what is gone from the pool", `demand_picks` is "what the league has consumed".

Per-team demand makes a stronger claim than the league-wide subtraction did, so the parameter's
domain is now stated and checked: a history carrying **more distinct rosters than the league has
teams** did not come from this league and is refused. An empty history is well defined and
unchanged — no picks means every team still needs its starters, which is what both models say.

The earlier hazard note said feeding it a rookie-only history would be "strictly worse than
today." **That was wrong and is corrected here:** the aggregate is equally blind to the veteran
rosters, and per-team is strictly better in that regime because it cannot go negative. What
actually changed is sharper and better: fed a real prior-phase history, the model finds every
team's WR slots filled and **declines to price WR** rather than collapsing its anchor to the
best remaining player. `demand_picks=[]` asks the same question of a fresh league and gets a
real, deeper rank — the same thing `remaining_demand=None` now means for `roster_diagnostics`.

## Tests

1021 green (from 989). 31 new invariants in `test_demand_decomposition.py`, written before the
implementation, covering exactness and boundedness, order-invariance, the zero-vs-one
distinction on both branches, absence discipline through `_scale_vor_to_bpa` and
`position_view_depth`, mutation proof that bench appetite cannot reach the anchor, and the
roster-universe refusal.

Test migrations were required where existing tests **encoded the defect as intent**, and are
called out rather than quietly rewritten:

- `test_a_position_with_zero_slot_share_still_returns_the_floor_of_one` asserted rank 1 for a
  position the league cannot start.
- `test_replacement_rises_as_startables_drain_and_collapses_at_exhaustion` asserted the
  best-remaining collapse on the startable-floor branch.
- `SelfCalibrationTests` tested the removed observed-share blend. Two of its cases were
  assertions of the defect: the share's conservation property, and *"a room hammering RBs
  should be expected to keep hammering RBs"* — which reads a pick as evidence of appetite when
  a pick is consumption of demand.

## STOPPED: the decision layer has no defined behaviour on an unpriced board

The valuation layer is complete and correct. The layer below it is not, and fixing it is not
mine to decide.

Walking the real board forward, `pick_synthesis.build_snapshot` **fails from round 11** —
earlier than the board's own round-16 blackout, because `draft_strategy.positional_forfeits`
builds a value curve across the *whole* board, so a single unpriced position poisons it:

```
rd 10: OK     top=T Pollard  RB  uv=90.0  tav=90.33
rd 11: FAILS  TypeError at draft_strategy.py:501  (curve.sort(reverse=True))
```

**The decision stack requires a fully priced board, not a mostly-priced one.** The inventory of
sites that do arithmetic on a board value, each of which needs a *semantic* answer rather than a
guard:

| site | quantity | question it cannot currently answer |
|---|---|---|
| `draft_strategy.py:501` | positional forfeit curve | what curve does an unpriced position have? |
| `draft_strategy.py:514` | `opportunity_cost = tav × (1 − survival)` | cost of losing a player you cannot price? |
| `draft_strategy.py:525` | `final_score × take_probability` | denial weight without a value? |
| `draft_strategy.py:545` | `premium = final_score − universal_value` | context premium over an absent base? |
| `pick_synthesis.py:336` | necessity standout margin | lead over an unpriced field? |
| `pick_synthesis.py:512–530` | decision-path flags, `context_elevated` | |
| `pick_synthesis.py:559–569` | decision regime, near-tie | |

Every one of those is **task #61 — what the board does when `bpa` is undefined** — which was
reserved as an open decision. Answering seven of them to keep the stack running would be
deciding #61 by implementation, so the stack is left as it is and the failure is left loud.

One thing was changed here, because the contract compels it and it decides nothing:
`pick_synthesis.narrow_candidates` now orders rows with an explicit key — **an unpriced row
never outranks a priced one**, ties break on `player_id`. It substitutes no number for an
absent score and takes no position on what the board should do once nothing can be priced. It
also closes the separately-noted determinism gap where that sort dropped the `player_id`
tiebreak and survived only on Python's sort being stable.

**Not attempted, deliberately:** no coefficient was tuned, no fallback value invented, and no
behaviour preserved by retaining a quantity whose meaning this audit established is wrong.

---

# Appendix — #61: what the board does when value is undefined

Investigation only. **No implementation.** Every consumer traced through the production path and
measured on the real 12x20 board.

## The finding that makes a coherent policy possible

CDME's central commitment is `team_acquisition_value = universal_value + need_bonus +
eligibility_bonus` — team-agnostic value plus roster-specific context. Measured across the whole
draft:

| round | rows | `universal_value` live | `need_bonus` live | `eligibility_bonus` live | identity holds | max error |
|---|---|---|---|---|---|---|
| 8 | 232 | 232 | 232 | 232 | yes | 0.0000 |
| 11 | 196 | 117 | 196 | 196 | yes | 0.0000 |
| 13 | 172 | 27 | 172 | 172 | yes | 0.0000 |
| 16 | 136 | **0** | **136** | **136** | yes | 0.0000 |
| 19 | 100 | **0** | **100** | **100** | yes | 0.0000 |

**The contextual layer is fully anchor-independent.** At rounds 16 and 19, where *no* player has
a value, *every* player still has a complete, exact roster-fit reading.

So an unpriced board is not an information-free board. It is a board where **"how good is this
player" is unknown and "how much does this team need him" is fully known** — a different,
well-defined epistemic state, and one CDME's own split already anticipates.

## Two structural facts the policy rests on

**Pricing is homogeneous within a position.** Measured at every round: `mixed-within-a-position:
none`. Because `replacement_levels` omits a whole position's key, every player there gets NaN
VOR together. So every per-position quantity is cleanly all-or-nothing.

**The partial regime is the dominant one, not an edge case:**

| rounds | priced positions | unpriced |
|---|---|---|
| 8–9 | QB RB WR TE K DEF | — |
| 10 | RB WR TE K DEF | QB |
| 11–12 | RB TE K DEF | QB WR |
| 13–15 | **TE only** | QB RB WR K DEF |
| 16–19 | — | all six |

Six of the twelve late rounds are *mixed*. A board-level all-or-nothing rule would be wrong for
most of the span where it matters.

## The classification

| # | site | needs anchor | partial pricing | `None` propagates | valid alternative | class |
|---|---|---|---|---|---|---|
| 1 | forfeit curve `ds:496–501` | within a position | **yes, per position** | yes | no | context — its docstring already says *surfaced signal only* |
| 2 | `opportunity_cost = tav × (1−survival)` `ds:514` | yes | per candidate | yes | no | **decision policy** — `pick_analysis`'s own sort key |
| 3 | `denial_value = opp tav × p_take` `ds:525` | yes | per candidate | yes | no | context |
| 4 | `rival_premium = opp tav − opp uv` `ds:545` | **no** | n/a | **must not** | **yes — it *is* `need_bonus + eligibility_bonus`** | context |
| 5 | necessity standout margin `ps:336` | that term only | 4 of 5 terms anchor-free | term-wise | partial only | **decision policy** |
| 6 | `decision_path_flags` `ps:512–530` | 2 of 4 flags | yes | per flag | `context_elevated` = need+elig ✓ | context — *"never new scoring"* |
| 7 | `decision_regime` / `near_tie_flags` `ps:559–575` | yes | no | yes | **`decision_regime`: yes** | context |
| + | `detect_positional_cliff` | yes (`bpa`) | yes, per position | yes | no | context |
| + | `expected_value_of_waiting` `ps:644` | yes | per candidate | **already correct** | no | context |
| + | `estimate_survival` `ds:341` | **no — rank-based** | n/a | **does not, and that is the hazard** | n/a | **silent** |

### Two quantities are already anchor-free and are only written as if they weren't

`rival_premium` and `context_elevated` are both spelled `tav − uv`. Since
`tav ≡ uv + need_bonus + eligibility_bonus` — verified exact, max error 0.0000 — both are
identically `need_bonus + eligibility_bonus`, which is defined with no anchor at all. Rewriting
them in that form is **not a fallback**; it is the correct expression of the same quantity, and
the subtraction was an implementation detail that accidentally coupled them to valuation.

### `decision_regime` has a mathematically correct answer for the unknown case

It returns `"decisive"` only when margin **and** survival both clear their bars. An unknown
margin cannot clear a bar, so `"contested"` is correct — not a fallback. The function already
returns `"contested"` for the degenerate `len < 2` case by the identical argument.

### The dangerous consumer is the one that never crashed

`estimate_survival` is **purely rank-based** — `rank_by_id` is board position, `i + 1` — and
never reads a value. So it keeps answering on an unpriced board. Measured:

```
rd 13: leader priced=True   survival_probability=0.202  ranks on rival boards [1, 1]
rd 17: leader priced=False  survival_probability=0.202  ranks on rival boards [1, 1]
```

**The same confident number, from an ordering that for unpriced rows is the `player_id`
tiebreak.** The crashing half of the stack is the safe half. This half fabricates.

## Proposed policy for #61 — the two-register board

**A board has two registers, decided per position, and it always says which one it is in.**

**Register 1 — priced.** The position has remaining starter demand. Everything behaves as today.

**Register 2 — unpriced.** It does not. The engine reports **need, not value**, and labels it.

Seven rules:

1. **Absence propagates by quantity, not by board.** A quantity needing an anchor returns `None`
   for the row or position lacking one. Never 0. Never the whole board.
2. **Scope is the position, not the board.** Justified by measurement, not convenience: pricing
   is homogeneous within a position, and the mixed regime spans six of twelve late rounds.
3. **Re-derive the two anchor-free quantities** (`rival_premium`, `context_elevated`) as
   `need_bonus + eligibility_bonus`. They then never go absent.
4. **`decision_regime` → `"contested"` on an unknown margin.** Correct by its own logic.
5. **`near_tie_flags` must be able to say *unknown*.** Its docstring refuses to hand the debate
   layer a false *"these are tied"*; returning `False` for unknown values is a false *"these are
   NOT tied"* by the identical argument. Return type widens to `Optional[bool]`.
6. **The rank-consuming half must stop answering.** `survival_probability` over an unpriced
   opponent board is `None`. This is the most important rule here and it makes the stack **less**
   functional, not more — it removes a number that currently looks real and is not.
7. **`pick_necessity` is not emitted in the unpriced register.** Under rule 6 only three of its
   inputs survive there (denial premium, roster fit, positional run). A score computed from
   three of five terms, on a scale still weighted for five, is *a quantity whose meaning changed
   while its name did not* — the exact defect class this whole audit chased. **A different
   question gets a different name**, so the debate layer surfaces the surviving signals as what
   they are rather than as a diminished urgency score.

## Invariants this would establish

1. No anchor-dependent quantity ever returns `0.0` in place of an absent anchor.
2. `None` in an anchor-dependent field implies the row's position is unpriced, and conversely.
3. Every per-position quantity is computed for priced positions in the same call that declines
   for unpriced ones — a mixed board is never all-or-nothing.
4. `rival_premium == need_bonus + eligibility_bonus` on every row, priced or not.
5. `context_elevated` is computable on every row, priced or not.
6. `survival_probability` is `None` whenever the target is unpriced on every opponent board.
7. `opportunity_cost` is `None` exactly when `tav` or `survival_probability` is.
8. `decision_regime` never returns `"decisive"` from an unknown margin.
9. `near_tie_flags` returns `None`, not `False`, for an unknown comparison.
10. `pick_necessity` is `None` in the unpriced register, never a partial score.
11. The candidate set is non-empty and position-diverse in every register.
12. No consumer reads a rank derived from unpriced rows as evidence of anything.

## Consequences — stated, not softened

**The candidate set survives; the ranking does not.** Measured through `narrow_candidates`:

| round | candidates | priced | composition |
|---|---|---|---|
| 9 | 21 | 21 | all positions |
| 11 | 14 | 12 | TE TE K K DEF DEF DEF RB RB TE K DEF · QB\* WR\* |
| 13 | 10 | 5 | TE TE TE TE TE · RB\* QB\* WR\* K\* DEF\* |
| 17 | 8 | 0 | RB\* QB\* QB\* WR\* WR\* TE\* K\* DEF\* |

The board never blanks. It goes **unranked**. `position_view_depth(None) = 1` keeps one
representative per position, so every position always holds a seat.

**Rounds 16–20 lose valuation, survival, and necessity.** What remains is a need-ranked list
with an explicit label. That is less than the engine appears to offer today, and more than it
actually knows today.

**At round 13 the top five are all TE**, because TE is the only position still carrying starter
demand. That is a real emphasis change, driven by the demand domain rather than by this policy —
but it is where a reader will first notice it.

**`draft_simulation` cannot pick in the unpriced register.** It takes `candidates[0]`, and with
no value and no necessity there is no defensible ordering. **A simulator selection rule for the
unpriced register is a decision this policy names and does not make.**

**One implicit policy claim already shipped and should be made explicit.** `_board_order` sorts
unpriced rows last, so in the mixed regime a priced K outranks the best remaining WR — measured
at round 11, where the top five are TE/K/DEF. Under a starter-demand reading that is right: the
K fills a starting slot and the WR does not. Under a talent reading it is obviously wrong. That
claim entered as a side effect of a mechanical sort fix and deserves an explicit decision.

---

# Appendix — #61's two remaining questions

Investigation only. **No implementation.**

## Q1 — `candidates[0]` is an implicit valuation policy, and it lives in two places

`draft_simulation`'s own module docstring settles the first half:

> *"This module never invents a simulation-specific valuation or selection rule -- the chosen
> player at every pick is `snap.candidates[0]`, the identical **'top team_acquisition_value
> board pick'** contract `draft_room.simulate_opponent_picks` already uses for auto-drafted
> teams."*

So it is **not infrastructure**. It is the engine's own recommendation, defined as
`argmax team_acquisition_value`, deliberately deferring to the valuation layer. (It also
ignores `pick_necessity` entirely — consistent with the separate finding that necessity
reorders nothing.)

**The second site was missed by the earlier trace and matters more.**
`draft_room.simulate_opponent_picks` is called from `app.py:4213` — the **live Mock Draft**, not
a harness — and it takes `board[0]["player_id"]` **raw**, never passing through
`narrow_candidates`. Nothing on that path can decline.

Measured, it does not crash. `compute_draft_board` sorts with pandas, which places NaN last
silently, so the auto-drafter keeps picking:

| round | `board[0]` | pts | best projected on the board |
|---|---|---|---|
| 13 | M Andrews (TE) | 187.0 | C Williams (QB) 324.0 |
| 15 | **D Njoku (TE)** | **52.0** | C Williams (QB) 324.0 |
| 17 | S Tucker (RB) — `final_score = None` | 96.0 | C Williams (QB) 324.0 |
| 19 | C Sutton (WR) — `final_score = None` | 199.0 | C Williams (QB) 324.0 |

From round 17 the live Mock Draft auto-drafts **by `player_id` order**. That is a fourth silent
fabrication site, in production rather than in a harness.

**Can an unpriced candidate ever legitimately be auto-selected?** Only under a rule that does
not claim to be the engine's valuation. Three exist:

| rule | available | honest? |
|---|---|---|
| by `projected_points` | yes — real sourced data, already on the row | yes, **if labelled as not the engine's pick** |
| by `need_bonus + eligibility_bonus` | yes | **no** — measured degenerate (below) |
| decline | yes | yes |

### Proposed policy — auto-selection requires a priced candidate

Auto-selection is the engine asserting a recommendation. Where `team_acquisition_value` is
undefined for every candidate, **the engine has no recommendation**, and picking anyway
substitutes a rule the engine does not have. So the auto-drafter **declines**, and each caller
handles the declination on its own terms:

- **`draft_simulation`** stops the trajectory and records why. A validation harness that keeps
  drafting past the point the engine can value anything is measuring its own tiebreak.
- **`simulate_opponent_picks`** stops early. This is not a new behaviour — the function already
  documents *"stops early (rather than raising) if the available pool ever comes up empty."* An
  **unvaluable** pool is the same class of stop as an **empty** one.

## Q2 — what "unpriced sorts last" actually means

Two separate questions, and they have opposite answers.

### With respect to need: almost provably safe

`need_bonus` has two terms — `NEED_BONUS_PER_DEDICATED_SLOT × dedicated_needed` (4.0 per slot)
and `NEED_BONUS_PER_FLEX_SHARE × min(flex_remaining, 1)` (1.0 per share).

**The dedicated term cannot survive into the unpriced register.** `starter_slot_counts[p] ≥
dedicated_slot_counts[p]` always, since flex only adds. If a team has an unfilled dedicated slot
then `filled ≤ dedicated − 1`, so its demand contribution
`max(starter − filled, 0) ≥ starter − dedicated + 1 ≥ 1`, so league demand ≥ 1 and the position
is priced. **Unfilled dedicated need therefore implies priced.**

Measured across all twelve teams and rounds 13–19: **248 unpriced rows carry `need_bonus > 0`,
and 0 of them carry dedicated need.** Every one is the flex residual, and every one is exactly
**0.33** — against `NEED_BONUS_MAX = 12.0`, i.e. **2.75% of the need scale**. `eligibility_bonus`
was **0 in every single case**.

So "unpriced last" never buries a player a team must start. It buries, at most, a third of a
flex share.

**Correction to the #61 policy as first proposed.** It described register 2 as reporting *"need,
not value"* and the board becoming a *"need-ranked list."* The measurement says that is wrong:
in the unpriced register the need signal is degenerate — `0.33` or `0`, and eligibility always
`0` — so a need ranking there is almost entirely ties, collapsing to the `player_id` tiebreak.
Register 2 cannot be need-ranked.

### With respect to talent: not safe

| round | board's top priced pick | pts | best unpriced | pts | gap |
|---|---|---|---|---|---|
| 10 | T Pollard (RB) | 178.0 | C Williams (QB) | 324.0 | **+146** |
| 12 | C McLaughlin (K) | 105.0 | C Williams (QB) | 324.0 | **+219** |
| 15 | D Njoku (TE) | 52.0 | C Williams (QB) | 324.0 | **+272** |

Worked case, round 15, roster 11: the board ranks **D Njoku (TE, 52 pts, need 0.0) above
T Pollard (RB, 178 pts, need 0.33)**. Six consecutive rounds carry a gap of this shape.

### The reason neither ordering is correct

A priced row's `final_score` and an unpriced row's `projected_points` are **different quantities
in different units answering different questions**. Sorting them into one list does not compare
them — it *invents* a comparison. "Unpriced last" is one invention; "by points throughout" is
another.

### Proposed policy — the board does not produce one list

1. The board is **partitioned by register**, never interleaved.
2. **Priced rows** are ordered by `team_acquisition_value`, exactly as today.
3. **Unpriced rows** are ordered by `projected_points` — real sourced data already on the row,
   and already documented in `compute_draft_board` as answering a legitimately separate
   question (*"who's simply projected to score the most"*). It is a **declared secondary
   ordering for a labelled register**, not a fabricated value: no row receives a `bpa`,
   `universal_value` or `team_acquisition_value` it did not earn.
4. The **relative order of the two partitions is a presentation decision**, stated explicitly
   rather than falling out of a sort key. It is not a valuation claim and must not be written as
   one.
5. Register 2's content is **"real production, unpriced by the engine"** — replacing the
   "need-ranked" description, which the measurement disproved.

## Invariants

**Auto-selection**

1. No auto-selection ever returns a row whose `team_acquisition_value` is `None`.
2. `simulate_opponent_picks` stops rather than picking when no candidate is priced, by the same
   rule it already stops on an empty pool.
3. A stopped trajectory records the reason and the round it stopped at.
4. No auto-selector reads `projected_points`, `need_bonus` or `player_id` as a selection key.

**Board order**

5. Priced and unpriced rows are never interleaved: every priced row precedes every unpriced row,
   or the partitions are surfaced separately — but the order is never decided by comparing a
   `final_score` against a `projected_points`.
6. Within the priced partition the key is `team_acquisition_value`; within the unpriced
   partition it is `projected_points`; neither key is ever applied across the boundary.
7. Ordering never assigns a value to a row that has none.
8. A row's partition membership is derivable from its own fields and is exposed to consumers,
   so no consumer has to infer the register from a missing number.
9. `player_id` remains the final tiebreak within each partition, so ordering stays deterministic.

## Consequence

Both policies make the engine **do less**. The auto-drafter stops rather than filling rosters
with arbitrary players; the board declines to rank talent against slot relevance rather than
silently preferring a 52-point tight end to a 324-point quarterback. Neither adds a fallback,
and neither invents a number.

---

# CDME policy — the two-register board (corrected, for sign-off)

Supersedes the two-register description in the earlier #61 appendices. **No implementation.**

## The central invariant

> **A missing valuation is an absence of knowledge, not a zero valuation and not permission to
> invent a replacement ranking.**

Everything below is a consequence of that sentence.

## Q1 — auto-selection

**Both auto-selection paths are decision policy, not infrastructure.**

- `draft_simulation.simulate_full_draft` → `snap.candidates[0]`
- `draft_room.simulate_opponent_picks` → `board[0]` — **live**, via `app.py`'s Mock Draft, and
  it bypasses `narrow_candidates` entirely

**Rule.** Auto-selection is valid **only when at least one candidate has a defined
`team_acquisition_value`.** Where the candidate pool contains no priced candidate, the engine
**declines to select**. It must not derive an ordering from `player_id`, from NaN placement in a
sort, from `projected_points`, from `need_bonus`/`eligibility_bonus`, or from any other
incidental ordering.

Measured, today it does exactly that: from round 17 of a 12x20 draft the live Mock Draft
auto-drafts by `player_id` order — taking a 96-point running back while a 324-point quarterback
sits available. Declining is not a degradation of that behaviour; it is the removal of a
fabricated one.

## Q2 — the two registers

**Register 1 — Priced.** Candidates with a valid CDME/TAV valuation. Ordered by the established
`team_acquisition_value` contract, unchanged.

**Register 2 — Unpriced.** Candidates whose production/projection data exists but whose CDME
valuation is undefined.

Three rules bind register 2:

1. **It is not a "need-ranked" register.** Measured: in the unpriced register `need_bonus` is
   `0.33` or `0` and `eligibility_bonus` is `0` in every observed case, so a need ordering there
   is almost entirely ties. Need and eligibility **may still be displayed as valid contextual
   information** — they are real, exact, and anchor-independent — but they **must not be used to
   manufacture a cross-register ranking**.
2. **`projected_points` is never compared against `team_acquisition_value`.** They are different
   quantities with different meanings and different units.
3. If `projected_points` orders candidates **within** register 2, that is labelled explicitly as
   a **secondary presentation ordering, not a CDME valuation**.

The relative placement of the two registers is a **presentation decision**, stated as such. It
is not a valuation claim and must never be produced by a sort key that compares a `final_score`
against a `projected_points`.

## Re-check of the downstream decision path

The earlier trace found the sites that do **arithmetic** on a value. Re-running the sweep against
the corrected policy surfaces a **second and larger class: rank and ordinal propagation.** A rank
is a value comparison already collapsed into an integer — it launders exactly the cross-register
comparison rule 2 forbids, and none of these sites were caught by looking for arithmetic.

| # | site | class | why it needs a justification |
|---|---|---|---|
| 11 | `_build_opponent_boards` — `rank_by_id = i + 1` | **cross-register rank** | one ordinal spanning both registers, feeding two consumers |
| 12 | `positional_forfeits` — `expected_taken` | consumes #11 | counts P-players in an opponent's top 5 ranks; not covered by the survival declination |
| 13 | `narrow_candidates` — `ranked[:top_n]` | **cross-register selection** | "the top five" is chosen across registers |
| 14 | `diff_snapshots` — `rank_delta` | **cross-register delta** | a player moving priced→unpriced reads as a value move, not a register change |
| 15 | `draft_board_ui` — `<span class="rank">${i+1}</span>` | **cross-register ordinal, rendered** | the user sees one rank number spanning both registers |
| 16 | `draft_board_ui._overview_for_view` — `overview.sort(key=tav)` | **second ranking authority** | crashes on all-`None`; its own docstring says this module is *"never a second ranking authority"* |
| 17 | `draft_board_ui` — Context Gap glyph + focus sentence | cross-candidate `uv` compare | renders `null` into user-facing prose |
| 18 | `screen_context.py:119` — `TAV {tav:.0f}` | **format spec on `None`** | `TypeError` — a crash site the earlier trace missed entirely |
| 19 | `pick_debate` prompt — `Universal value: {uv}` | **leak into the LLM prompt** | prints `Universal value: None` as a stated fact, with no rule telling the model what that means |
| 20 | `pick_debate:342` — highest TAV other than the recommendation | max over `None` | |
| 21 | `draft_counterfactual:94` — `max(board, key=universal_value)` | argmax over `None` | the harness's whole premise is *"pure BPA argmax"*, which is undefined here |

Confirmed directly: `f"{None:.0f}"` and `f"{None:+}"` both raise `TypeError`; `f"{None}"` prints
the string `"None"`; sorting an all-`None` list raises. So #16, #18, #20 and #21 are **crashes**,
while #19 is **silent** — the most dangerous of the group, because a fabricated fact reaches the
debate layer as text rather than failing.

### What this changes about the shape of the work

The seven original consumers were all inside `draft_strategy` and `pick_synthesis`. These eleven
span the **UI, the screen-reader context, the LLM debate prompt, and the counterfactual
harness** — four surfaces the valuation policy had not been checked against at all. Any
implementation must treat rank propagation as a first-class case rather than a consequence of
fixing the arithmetic.

### Additional invariants this re-check establishes

10. No ordinal, rank, or rank delta is ever computed across the two registers.
11. Any rendered rank states which register it is an ordinal within.
12. No formatted output applies a numeric format spec to a possibly-absent valuation.
13. No absent valuation is rendered into prose or into an LLM prompt as a value —
    absence is stated as absence or the field is omitted.
14. `draft_board_ui` remains a translation layer and performs no sort that could reorder
    the engine's own ranking.
15. `draft_counterfactual`'s BPA argmax is defined only over register 1, and says so when
    register 1 is empty.

**Nothing is implemented.** No fallback, no coefficient, no cross-register ordering, until each
dependency above carries an explicit semantic justification and the policy is signed off.

---

# Appendix — ordering within the unpriced register

Investigation only. **No implementation.**

> **Unknown CDME value does not mean unknown player quality.**

The unpriced register must not be a flat "unknown" bucket. The question is what may order it
without becoming a TAV substitute.

## Q1 — normalization

**League format: already applied, and it must stay.** `_points` is scored under the league's own
`scoring_settings` before anything else touches it.

**Within position: yes — but not by within-position normalization.**

Raw points is unusable. Measured, the top twelve of the unpriced register at round 17 ordered by
raw points:

```
QB QB QB QB QB QB QB QB QB QB QB QB
```

Raw points is a **positional ranking wearing a quality ranking's clothes** — it answers which
position scores most, not which player is better.

But the obvious repair is worse. Normalizing *within* a position — by rank, or as a share of
that position's own best remaining — **creates the boundary failure it was meant to fix**: the
best QB and the best TE both normalize to the top of their own list and become
indistinguishable. Percentile-ranking is separately ruled out by this module's own history
(*"percentile-ranking the VOR anchor was a real bug"*).

**The correct normalization is a common cross-positional reference: each position's own
PRE-DRAFT replacement level** — the D-th best player in the full field, D = this league's
starting slots at that position. Fixed by `roster_positions` alone. Measured:

```
DEF 98   K 105   QB 324   RB 178   TE 187   WR 210
```

Same rule for every position; the position enters only as the identity of its own denominator.

### Why this is not smuggling valuation back in

CDME's anchor is replacement against **remaining demand** — a live claim about scarcity *now*.
This reference is the **pre-draft field at league starting slots** — a fixed structural constant
that never moves during the draft. It makes no claim about scarcity, survival, or roster fit. It
answers only *"is this player starter-quality for this league's shape?"*, which is a production
question. Because it is fixed, it cannot be mistaken for a live valuation.

## The boundary case, resolved by the general rule

| player | pos | pts | pre-draft replacement | production margin |
|---|---|---|---|---|
| C Williams | QB | 324.0 | 324 | **0.0** |
| D Njoku | TE | 52.0 | 187 | **−135.0** |

Caleb ranks 135 points clear of Njoku, and nothing about him was hard-coded — it falls out of
*points minus that position's pre-draft replacement level*. Under the same rule the top twelve
of the unpriced register becomes:

```
WR TE DEF DEF QB RB WR TE K DEF DEF RB      (DEF 4, WR 2, TE 2, RB 2, QB 1, K 1)
```

Genuinely mixed, with no per-position tuning.

## Q2 — bounded, without becoming an implicit TAV

**Yes — and the honest form is deliberately UNBOUNDED, and denominated in points.**

Bounding it to 0–100 would give it `bpa`'s exact shape and invite the substitution this is meant
to prevent. Ordering needs a total order, not a scale; bounds only matter for a quantity that
gets *combined* with others, and this one never may be. **Separation is enforced by unit and
name, not by range** — points is a unit CDME never uses for a score.

Evidence it is not a TAV proxy, measured inside the priced register where both exist:

| round | n | Spearman ρ vs TAV | rows displaced >10% of the board |
|---|---|---|---|
| 4 | 283 | 0.30 | 186 (66%) |
| 8 | 236 | **−0.08** | 190 (81%) |
| 11 | 139 | **0.01** | 106 (76%) |

**The two keys are near-independent.** They carry different information, and neither can stand
in for the other.

## Q3 — should the ordering differ between positions?

**No.** One rule, one formula, every position — the mixed top twelve above is produced without a
single per-position parameter. Any per-position variation would be exactly the positional
special-casing this engine forbids.

## Q4 — how need and eligibility interact

**They do not enter the ordering at all.** Measured in the unpriced register:

| round | production-key spread | max `need + eligibility` available | exact production ties |
|---|---|---|---|
| 13 | 257.0 pts | **0.00** | 18 |
| 15 | 230.0 pts | **0.00** | 17 |
| 17 | 233.0 pts | **0.00** | 20 |

There is nothing there to order with. Across all twelve rosters the maximum ever observed is
`0.33`, against a 230–257 point spread — roughly **0.14%**. Need and eligibility are real, exact,
and worth **displaying** beside a register-2 row; they are not an ordering signal, and using them
as one would blur a production ordering into a roster ordering for no measurable gain.

## Q5 — must the registers stay strictly separated?

**Yes, and now on evidence rather than principle.** The ρ ≈ 0 result above means using the
production key across the priced register would **discard the scarcity, horizon, risk and roster
information CDME actually computed**, and using TAV in register 2 is impossible by definition.
Each register keeps its own key; they are never merged, and no row is ever ordered against a row
in the other register.

## Q6 — when production itself is unavailable

Measured on the full IDP-inclusive pool (404 rows):

| | rows |
|---|---|
| no points projection | 76 |
| no points **and** no trade_value | **0** |
| no points but has trade_value | 76 |

So production is never fully absent in the committed baseline. The **same rule** applies against
the **trade_value** pre-draft level — a level `replacement_levels` already computes and
`compute_draft_board` already derives for exactly those rows.

**But points-derived and trade_value-derived margins are different units and must not be
interleaved either.** That is the same error one layer down. So register 2 orders **within a
measurement basis**, and each row carries which basis produced its margin.

A row carrying neither points nor trade_value has **no ordering position at all** — it is
surfaced as unordered, never appended silently to the end of a list where position implies rank.

## Proposed contract

```
production_margin  = projected_points − pre_draft_replacement[position]      (points basis)
                   = trade_value      − pre_draft_replacement_tv[position]   (trade_value basis)
                   = None                                                    (neither available)

production_basis   ∈ {"points", "trade_value", None}
```

- Computed only for register-2 rows. Never written to `bpa`, `universal_value`,
  `team_acquisition_value`, or any field a valuation consumer reads.
- Unbounded, in its source unit, never rescaled to 0–100.
- Labelled at every surface as a **secondary presentation ordering, not a CDME valuation**.
- The pre-draft reference is computed once from `roster_positions` and the full field, and does
  not move as the draft progresses.

## Invariants

16. `production_margin` is defined only where `team_acquisition_value` is absent, and never
    coexists with it on the same row.
17. It never enters `bpa`, `universal_value`, `team_acquisition_value`, `pick_necessity`, or any
    ordering that also contains a priced row.
18. It is never rescaled, clipped, or bounded to a 0–100 range.
19. Its reference is the pre-draft field and is invariant to draft progress: recomputing it at
    any round yields the same per-position levels.
20. Rows on different `production_basis` values are never ordered against each other.
21. A row with no available production carries `production_margin = None` and is surfaced as
    unordered — never placed at the end of an ordered list.
22. `need_bonus` and `eligibility_bonus` never appear in the register-2 ordering key, at any
    weight, including as a tiebreak.
23. Every surface rendering a register-2 ordering states that it is a production ordering and
    not a CDME valuation.

---

# Appendix — register-2 ordering, corrected

**This corrects the immediately preceding appendix.** Its Spearman figures were an artifact and
its Q5 conclusion was wrong. Investigation only; no implementation.

## The measurement error

The previous appendix reported `rho(production, TAV)` of `0.30 / −0.08 / 0.01` and concluded the
two keys were *"near-independent"*, using that as the evidence for strict register separation.

**That was wrong.** `bpa` is `clip(lower=0, upper=100)`, so late boards carry large blocks of
rows tied at exactly `0.0`, and the untied Spearman formula used is invalid under heavy ties. It
produced numbers near zero, and negative ones, from tie blocks rather than from disagreement.

Two tie-safe tests replace it: a direct inversion count, and pairwise agreement measured **only
on pairs `bpa` materially separates**.

## Q1 — can production order players within a position?

**Yes, exactly, and by construction.** Within a position, VOR is `points − a per-position
constant`, then a shared positive linear scale — so `bpa` is a monotone transform of points.

| test | result |
|---|---|
| `bpa` inversions in points-descending order (RB 45, WR 78, K 28 rows) | **0, 0, 0** |
| within-position pairwise agreement, rd 4 | **100.0%** (2320 pairs) |
| within-position pairwise agreement, rd 8 | **100.0%** (948 pairs) |

## Q2/Q3 — cross-position comparison, and what makes it comparable

Agreement with CDME's own cross-positional ordering, on pairs `bpa` separates by ≥ 5:

| round | pairs | raw points | production margin |
|---|---|---|---|
| 2 | 4363 | 81.6% | **100.0%** |
| 4 | 3202 | 69.0% | **100.0%** |
| 6 | 3534 | 74.5% | **95.1%** |
| 8 | 2463 | 77.7% | **94.1%** |
| 11 | 682 | 75.8% | **99.1%** |

Raw points is wrong about one cross-position pair in four. The **production margin reproduces
CDME's cross-positional ordering at 94–100%.**

**What makes it comparable is exactly what makes VOR comparable: a per-position zero set at
league starter depth.** It is not a new normalization — it is CDME's own one, evaluated against
the fixed pre-draft field instead of the live remaining pool.

## Q5 — does it duplicate what CDME already has?

**Yes — and that is the argument FOR strict separation, not against the measure.**

`production_margin` is CDME's own VOR numerator with the only anchor still defined. Per the
earlier inertness finding, the live anchor *equals* the pre-draft anchor while remaining demand
holds — which is why agreement is 100% at rounds 2, 4 and 11. It falls to 94–95% at rounds 6–8
precisely where the live anchor has moved, i.e. **exactly where CDME knows something the
production margin does not.**

So the rule is not "these are different signals, keep them apart." It is:

> Where CDME has an anchor, its version is strictly better informed and the production margin
> must not be computed at all. Where CDME has no anchor, the production margin is the same
> quantity with the only reference that still exists — carrying no scarcity, horizon, risk or
> roster information, and never to be scaled, combined, or presented as `bpa`.

The previous appendix's separation conclusion stands. Its stated reason does not.

## Q4 — stability, and how fragile it is

Stable **only if the reference is computed from the full pre-draft field**. Measured, the same
formula against the *remaining* pool drifts hard:

| reference | rd 0 | rd 8 | rd 13 | rd 19 |
|---|---|---|---|---|
| QB | 324 | 275 | 264 | **204** |
| RB | 178 | 78 | 66 | **88** |
| TE | 187 | 82 | 60 | **54** |

A 120-point drift at QB and 133 at TE. The pre-draft reference is fixed by construction, but
that is a **contract requirement about which pool is used**, not a property that defends itself —
so it needs an invariant rather than a comment.

## Q6 — coexistence without implying comparable scales

The two registers' keys are the same quantity at different anchors, which makes them *more*
confusable, not less. Separation therefore has to be enforced structurally: different field
name, different unit (points, never a 0–100 scale), never present on the same row, never in one
sorted list, and labelled at every surface.

## Corrected invariants

Invariants 16–23 stand. Two are added and one is restated:

24. `production_margin`'s reference is computed from the **full pre-draft field** — never from
    the remaining pool. A test recomputes it at several draft states and requires identical
    per-position levels.
25. `production_margin` is never computed for a row that has a `team_acquisition_value`. Not
    computed-and-ignored: **not computed**, because where CDME has an anchor its answer is
    strictly better informed.
26. *(restates 17)* It never enters `bpa`, `universal_value`, `team_acquisition_value`,
    `pick_necessity`, or any ordering containing a priced row — enforced because the two are the
    same quantity at different anchors and are therefore easy to confuse, not because they are
    unrelated.

---

# Appendix — what the engine may conclude from 324 vs 52

Investigation only. Answers the intent question directly and **corrects invariant 25**.

## Does the engine have enough evidence to preserve cross-position ordering?

**Yes.** Measured on pairs `bpa` materially separates, the production margin reproduces CDME's
own cross-positional ordering at **94–100%**, against **69–82%** for raw points. The evidence is
sufficient, and raw points is not the thing that carries it.

**The strongest defensible signal** is `projected_points − pre_draft_replacement[position]`.
What makes it cross-positionally valid is the same thing that makes VOR valid: a per-position
zero set at league starter depth. It is not a new normalization — it is CDME's own, evaluated
against the fixed pre-draft field rather than the live pool.

**Its proper scope** is ordering **within register 2 only**, and display everywhere.

## The boundary pair, fully decomposed

| player | pos | pts | position baseline | margin | register | TAV |
|---|---|---|---|---|---|---|
| C Williams | QB | 324.0 | 324 | **+0.0** | **2 — unpriced** | `None` |
| D Njoku | TE | 52.0 | 187 | **−135.0** | **1 — priced** | 1.16 |

The pair is split across registers, and the *worse* producer is the priced one.

### What the engine MAY conclude

- **They are not equivalent, and by how much.** Caleb produces at exactly his position's
  league-starter baseline; Njoku produces 135 points below his. That comparison is sourced,
  scored under this league's own settings, and cross-positionally meaningful.
- **A production ordering between them**, stated as production.
- **That Njoku's TAV of 1.16 is not a claim that he is worth more than Caleb.** It is an answer
  to a question — *what is a TE worth given remaining TE starter demand* — that currently has no
  counterpart for QB.

### What it MAY NOT conclude

- **That Caleb is the better pick.** That needs scarcity, survival, horizon and roster fit —
  none of which exist for him right now.
- **That 135 points is a value gap.** It is a production gap in points. The conversion to value
  is precisely the layer that is unavailable.
- **That a margin of `0.0` means zero value.** It means *at the baseline* — a reference point,
  not a zero. Reading it as zero would be this audit's own recurring defect, one layer over.
- **That the ordering authorizes a selection.** Auto-selection still requires a priced candidate.

## Correction to invariant 25

The previous appendix said `production_margin` is *"never computed for a row that has a
`team_acquisition_value`."* **That is wrong, and this case is why:** Njoku is priced. Withholding
his margin makes the 324-vs-52 comparison impossible to state at all — the opposite of the
intent.

The substitution risk is about the **ordering key**, not the **display**, and the 94–100%
agreement means showing the margin on a priced row is a consistent weaker view of the same
ordering, not a misleading one.

> **25 (corrected).** `production_margin` is computed for **every** row as displayed context. It
> is used as an **ordering key only within register 2**. It never enters `bpa`,
> `universal_value`, `team_acquisition_value`, `pick_necessity`, or any sort that spans both
> registers.

## What separation actually costs — measured

| round | best priced margin | best unpriced margin | unpriced beating the best priced |
|---|---|---|---|
| 11 | 0.0 | 0.0 | **0 of 79** |
| 13 | 0.0 | 0.0 | **0 of 145** |
| 15 | 0.0 | 0.0 | **0 of 125** |

**Register separation withholds no production advantage.** The two registers' production ceilings
are identical at every round measured, and no unpriced player out-produces the best priced one.
Separation costs a single merged ordinal — not information.

## Invariant

27. Both registers are **displayed together and ordered separately**. Every row carries its
    `production_margin` and its register; no surface may present a single ordinal spanning both,
    and no surface may omit an unpriced row's margin on the grounds that it has no valuation.

---

# Appendix — the two costs of waiting

Investigation only. **No implementation.**

## Does the architecture already distinguish them?

**Yes — all five questions already have distinct quantities.** The defect is naming and wiring,
not concept.

| question | quantity | horizon |
|---|---|---|
| How good is this player? | `universal_value`; `production_margin` in register 2 | none — static |
| How important is solving this need? | `need_bonus` + `eligibility_bonus` | none — roster state |
| What alternatives remain **in** the draft? | `survival_probability`, `opportunity_cost` (player); `positional_forfeit`, `positional_cliff` (position) | **my next pick** |
| What alternatives exist **after** the draft? | `horizon_floor`, `waiting_cost` | **end of draft** |
| What do I lose by waiting? | *(no single quantity — and there should not be one)* | — |

`draft_board_ui` already documents the distinction and refuses to reuse the phrase:
*"opportunity_cost and positional_forfeit both answer 'what does deferring cost me by my NEXT
PICK', in universal-value points. This one answers... in season points per week."* The precedent
exists; it is just not carried into the field names.

## `waiting_cost` answers the second question, not the first

`horizon_replacement` returns *the best player expected to be still undrafted when the draft
ends* — which **is the top of the post-draft free-agent pool**. So

```
waiting_cost = my projected points − the best free agent at my position after the draft
```

That is **post-draft substitution cost**, in full. It contains no in-draft loss at all: it never
asks whether anyone takes him before my next pick. The in-draft question is answered by three
*other* quantities, none of which share its units or its horizon.

## They are not two views of one number — measured

Best TE on the board, across the draft:

| round | best TE | in-draft gap (to TE+6) | post-draft cost |
|---|---|---|---|
| 1 | C Loveland 284 | 63 | `None` |
| 3 | S LaPorta 231 | 34 | `None` |
| 7 | B Strange 191 | 14 | **171** |
| 9 | M Andrews 187 | 27 | 133 |
| 13 | M Andrews 187 | 32 | 123 |
| 17 | M Andrews 187 | 34 | **34** |

The in-draft gap stays in a 14–63 band the whole way while the post-draft cost falls **171 → 34**.
They are not proportional and they diverge by roughly **5×** on the same position.

## The boundary case resolves — and the engine already computes it

Round 15:

| player | pts | next best at position | in-draft gap | horizon floor | post-draft cost |
|---|---|---|---|---|---|
| D Njoku (TE) | 52 | 36 | 16 | **67** | **−15** |
| C Williams (QB) | 324 | 319 | 5 | 296 | +28 |

**Njoku's post-draft cost is negative.** The best TE expected to go *undrafted* projects 67 —
better than Njoku's 52. Passing him costs nothing; a better TE is free afterwards.
`draft_board_ui._waiting_note` already has the branch for it: *"Waiting is better than free here
… this pick buys nothing you won't have anyway."*

So the TE case the two-cost model predicts is exactly what the engine measures: **need is real
(the TE slot is unfilled), and both waiting costs say don't** — 16 points of in-draft slide, and
a *better* free agent afterwards.

**And the engine ranks him first anyway.** At round 15 Njoku is the board's top pick, because TE
is the only position still carrying starter demand. `waiting_cost` is `OBSERVABLE ONLY` and feeds
nothing — so the engine computes *"waiting is better than free"* and then does the opposite. That
is task #57, now with a concrete cost attached, and it is precisely the `need → take the
position` rule the two-cost model exists to prevent.

## Their availability windows are complementary — the strongest reason never to fuse them

| rounds | post-draft cost | in-draft curve |
|---|---|---|
| 1–5 | partial (TE, RB missing) | **complete** |
| 7–9 | **complete** | **complete** |
| 11–15 | **complete** | degrading — RB,TE,K,DEF → TE only |
| 17–19 | **complete** | **gone** |

The in-draft question depends on the **live valuation anchor**, which exhausts. The post-draft
question depends on **pool depth past the horizon rank**, which improves as the pool drains. So
each is at its weakest where the other is at its strongest, and rounds 7–9 are the only window
where both answer for every position.

Two consequences:

1. **A single fused "cost of waiting" would silently change meaning as one input dropped out** —
   the same semantic-drift defect this whole audit has chased, rebuilt one layer up.
2. **The unpriced register is where the post-draft cost is at its most reliable.** Register 2 is
   not information-poor about waiting; it holds the *better* of the two waiting signals.

## What must be kept separate, and why

| | in-draft loss | post-draft substitution cost |
|---|---|---|
| question | will someone take him before my next pick? | how hard is this need to solve afterwards? |
| horizon | my next pick | the end of the draft |
| units | universal-value points / probability | season points |
| depends on | live valuation anchor, opponent boards | pool depth past the horizon rank |
| available | early, dies late | patchy early, complete late |
| exists as | `survival_probability`, `opportunity_cost`, `positional_forfeit`, `positional_cliff` | `horizon_floor`, `waiting_cost` |

They are related — both bear on the same decision — and that is not a reason to combine them.
Different horizons, different units, different failure modes, complementary availability.

## Proposed naming and invariants

The concept needs three names where there is currently one overloaded one:

- **in-draft loss** — keep the existing four quantities, and name the family.
- **post-draft substitution cost** — `waiting_cost` renamed for what it measures. The UI already
  says *"replaceability"* and states its horizon in every sentence; the field name should agree.
- **cost of waiting** — retired as a field name. It is the *question*, answered by two numbers.

28. No quantity combines an in-draft horizon with a post-draft horizon.
29. Every waiting-related quantity states its horizon at every surface that renders it.
30. A quantity whose inputs are unavailable is `None` — never substituted by the other horizon's
    answer, which is the specific fusion their complementary windows would otherwise invite.
31. A negative post-draft substitution cost is a first-class result meaning *waiting is better
    than free*, never clipped to zero.
32. Positional need alone never orders the board. Where a position carries unfilled starter
    demand **and** both waiting costs are low, the engine must be able to say so.

---

# Appendix — how positional need actually modifies selection

Investigation only. **No implementation.**

## The premise inverts: need contributes 0.00 to the Njoku/Caleb outcome

Round 15, roster 11, traced term by term:

```
1. remaining starter demand:  QB = 0.00   TE = 1.33
   -> TE >= 1, so TE is PRICED.  QB < 1, so QB is UNPRICED.

2. D Njoku    TE   bpa =  0.0   uv = 1.16   need = 0.0   elig = 0.0   tav = 1.16   waiting = -15.0
   C Williams QB   bpa = None   uv = None   need = 0.0   elig = 0.0   tav = None   waiting = +28.0

3. Njoku board rank 1.        Caleb board rank 123.

4. _board_order = (tav is None, -tav, player_id): every priced row precedes every unpriced row.
```

**Njoku's `need_bonus` is `0.00`.** Across all twelve rosters at round 15 it is `0.0` for eight
and `0.33` for four, and the board's top row is D Njoku for **every one of them**. Need is not
the mechanism.

**And `bpa = 0.0`.** Njoku's entire `tav` of 1.16 is `time_horizon_adj + risk_adj` — a bounded
dynasty nudge. The board's number-one pick at round 15 is a player the valuation layer has
already scored at **exactly zero value above replacement**.

## Is need's effect proportional to the value gap, or absolute?

**Absolute, and measurably weak.**

```
need_bonus = min(4.0 * dedicated_needed + 1.0 * min(flex_remaining, 1), 12.0)
```

It reads **only roster state**. No term involves the candidate's value, the gap to the
alternatives, the in-draft loss, or the post-draft substitution cost. It cannot be proportional
to a gap it never sees.

Measured across 72 roster-rounds:

| | |
|---|---|
| top pick changed by need + eligibility | **3 of 72 (4%)** |
| largest `uv` gap ever overturned | **4.23** |
| the one case | rd 2, roster 2: D London (WR, need 8.33) over B Hall (RB) across a 4.23 gap |
| theoretical ceiling | 24.0 of `bpa`'s 100-point range |

So the failure mode is **not** *need → take the position*. `need_bonus` is close to inert: it
flips one roster-round in twenty-five, and only across gaps of a few points.

## Can need distinguish the two TE cases? No — and something else already does

| | S LaPorta, rd 3 | D Njoku, rd 15 |
|---|---|---|
| projected points | 231 | 52 |
| **`bpa`** | **95.65** | **0.00** |
| `universal_value` | 93.35 | 1.16 |
| `need_bonus` | 4.33 | 0.00 |
| in-draft gap to next TE | **1** | **16** |
| post-draft cost | **`None`** | **−15** |

Three results worth stating plainly:

1. **`need_bonus` is *higher* in the LaPorta case (4.33 vs 0.00)** — but incidentally, from roster
   state, not because it knows anything about LaPorta. It carries zero information about quality
   or replaceability, so it cannot make this distinction in either direction.
2. **The in-draft signal points the wrong way.** LaPorta's gap to the next TE is **1 point**; Njoku's
   is 16. On the in-draft axis LaPorta is the *more* replaceable of the two.
3. **The post-draft signal is unavailable in the LaPorta case** (`None` at round 3, the horizon
   running past the loaded pool).

**What actually separates them is `bpa`: 95.65 versus 0.00.** The valuation layer already makes
the distinction, cleanly, and gets round 3 right for the right reason. LaPorta is worth taking
because he is *worth* 95.65 — his 4.33 of need is immaterial to that.

## Where the conclusion is lost

Not in the need term. At round 15 the engine holds two correct conclusions simultaneously:

- **`bpa = 0.0`** — Njoku adds nothing above replacement.
- **`waiting_cost = −15`** — a better TE is free after the draft.

Then it ranks him **first**, because `1.16 > None`.

The ordering treats **having a number as strictly better than not having one, regardless of what
the number says.** A `bpa` of `0.0` means *at replacement, no value added*. Caleb's production
margin is `0.0` too — *at his position's pre-draft baseline*. Those two are arguably equivalent
claims, and the ordering separates them by **122 places**.

So the loss is at the **valuation → ordering** boundary, and it is a second instance of this
audit's own defect class: **a zero being read as a value rather than as what it says.**

## What the selection layer would need to make the economically correct distinction

Stated as required information, not as a design:

1. **The magnitude of a priced value, not merely its presence.** `bpa = 0.0` outranking a
   demonstrably productive unpriced player by 122 places is the register boundary behaving as an
   unbounded positional override — far stronger than anything `need_bonus` can do at 4%.
2. **Both waiting costs, consumed rather than observed.** The engine computes *"waiting is better
   than free"* and discards it. Consuming it requires them in commensurate form, which their
   different units and complementary availability windows currently prevent.
3. **Need expressed relative to the gap it is asked to overturn** — but the measurement says this
   is *not* where the current failure is. Need is too weak to be the problem, and making it
   proportional would not change the Njoku/Caleb outcome by a single place, because it is `0.00`
   there.

## What the current equations permit the engine to conclude

**Permitted, and already true:** that LaPorta is worth 95.65 and Njoku 0.00; that a better TE is
free after the draft; that Caleb produces at his position's baseline while Njoku sits 135 points
below his.

**Not permitted:** any comparison between a priced zero and an unpriced player, because the two
live in different registers and the only relation defined between them is *priced first*.

That is the boundary. The distinction the two cases require is **already computed** — and lost
one layer later.

---

# Appendix — the selection boundary, mapped

Investigation only. **No implementation, no weighting designed.**

## Where magnitude becomes availability, and availability becomes ordering

**Introduced — correctly.** `_scale_vor_to_bpa` produces the two states on *adjacent branches of
the same line*: `vor.where(vor.isna(), 0.0)` returns `0.0` for a real non-positive VOR and `NaN`
for an absent one. **The distinction is sound at birth.**

**Propagated — correctly.** `universal_value = bpa + time_horizon_adj + risk_adj`. Magnitude-zero
survives as a small number (possibly negative); absent survives as `NaN`. Still distinct.

**Destroyed — at three ordering sites.**

| site | mechanism |
|---|---|
| `draft_room.py:1448` and `:1560` | `sort_values([...], ascending=[False, True])` — pandas' **default `na_position='last'`**. Verified: `[5.0, nan, 0.0, 90.0]` sorts to `[90.0, 5.0, 0.0, nan]`. **Availability becomes the primary key, and nothing in the call says so.** |
| `pick_synthesis._board_order` | `(score is None, -score, player_id)` — the boolean first element **dominates magnitude lexicographically** |
| `draft_board_ui.py:265` | `overview.sort(key=tav)` — a second ranking authority; crashes on all-`None` |

## The collapse, measured — round 15

| group | count | board ranks |
|---|---|---|
| priced rows with `bpa` **exactly 0.0** | 23 | **1 – 23** |
| unpriced rows with production margin **0.0** | 5 | **29 – 128** |

**Both groups assert the same thing** — *at the baseline, nothing added*. They are separated by
up to 127 places, decided entirely by availability.

And sharper still:

| group | count | board ranks |
|---|---|---|
| priced rows with `universal_value` **< 0** | 15 | **9 – 23** |
| unpriced rows | 125 | **24 – 148** |

**Every demonstrated negative outranks every absent one.** The worst priced row is M Andrews at
`uv = −3.61` — a tight end projecting **187 points** whose post-draft cost is **+120**.

## New finding — the domain is open and the answer is degenerate

At round 15, TE remaining starter demand is **1.33**, so the replacement rank is **1**, so
replacement is *the best remaining TE* — Andrews himself. **His VOR is zero by construction.**

> Any demand in **[1, 2)** yields rank 1, so that position's best player always scores exactly 0.

This is why 23 of the 27 priced rows at round 15 carry `bpa = 0.0`: the priced register's top is
a block of structural zeros. **The register split does not by itself resolve the saturation
finding** — it moves the boundary, and a new degenerate band appears just inside it.

## The three-dimension availability surface

| rounds | A — value | B — in-draft loss | C — post-draft cost |
|---|---|---|---|
| 1 | all six | all six | QB WR K DEF |
| 3 – 5 | all six | all six | all but TE |
| **7 – 9** | **all six** | **all six** | **all six** |
| 11 | RB TE K DEF | RB TE K DEF | all six |
| 13 – 15 | **TE only** | **TE only** | all six |
| 17 – 19 | **none** | **none** | all six |

B is built from `universal_value` curves, so its availability *is* A's. **Rounds 7–9 are the only
window in which all three dimensions answer for every position.**

## What each dimension can legitimately say

| | claim | valid when | degenerate when | absent when |
|---|---|---|---|---|
| **A — value** | how much this player adds over the marginal starter, at current remaining demand | demand ≥ 1 | demand ∈ [1, 2) → best player scores 0 | demand < 1 |
| **B — in-draft loss** | whether he survives to my next turn, and how far the position falls by then | the live anchor exists | — | the live anchor is gone |
| **C — post-draft cost** | how much better he is than the free agent after the draft | horizon rank inside the loaded pool | — | horizon runs past the pool |

**When one is unavailable the others do not cover for it in kind** — they answer different
questions. Their *windows*, however, are complementary, so at every round at least one is
answerable, and A and C are never both absent.

## Boundary conditions

**Tight end across the draft — all three dimensions:**

| rd | best TE | `uv` | `bpa` | B: gap to next | C: post-draft |
|---|---|---|---|---|---|
| 1 | C Loveland | 100.2 | 100.0 | 17 | `None` |
| 3 | S LaPorta | 93.35 | 95.7 | **1** | `None` |
| 9 | M Andrews | 64.84 | 69.2 | 1 | 133 |
| 15 | M Andrews | **−3.61** | **0.0** | 1 | **120** |
| 17 | M Andrews | `None` | `None` | 1 | 34 |

**Case 1 — Caleb vs the 52-point TE (round 15).** A is absent for Caleb and degenerate (`0.0`)
for Njoku. B is ~1 point — TE is in-draft replaceable. C is **−15** for Njoku and **+28** for
Caleb. **C is the only dimension that separates them, and it says pass on Njoku.**

**Case 2 — a genuinely strong TE (rounds 7–9).** A is real (29.4 / 69.2), C is large (171 / 133),
B is small (2 / 1). **A and C agree that he is worth taking; B is the lone dissent, saying he
will probably survive one more turn.**

The two cases differ in **which dimensions agree**, not in the magnitude of any single one — and
the dimension that resolves Case 1 (**C**) is the one that is `None` in the LaPorta-shaped early
version of Case 2.

## The decision surface the evidence supports

- **No single dimension is right at every round.** At round 15 Andrews' A says 0, his B says 1
  point, his C says 120 — and all three are true statements about different questions.
- **A dimension being degenerate is not the same as it being absent**, and neither is the same as
  it being small. The current ordering distinguishes none of these three.
- **The only complete regime is rounds 7–9.** Any weighting that assumes all three inputs would
  be undefined for most of the draft.
- **The decision surface is therefore a sequence of regimes, not one function.** What can be
  concluded changes with which dimensions are answerable, and the engine must be able to say
  which regime it is in before it can be asked to weigh anything.

**No weighting is proposed.** The surface above is what the available evidence supports; choosing
how to traverse it is the next decision, and it is not taken here.

## Invariants

33. Valuation **magnitude** and valuation **availability** are distinct facts, and no ordering
    may collapse one into the other.
34. No sort relies on an implicit null-placement default; null handling is written explicitly at
    every ordering site or the site does not order.
35. A demonstrated negative valuation is never ranked above an absent one on the grounds that it
    is a number.
36. A position whose remaining demand lies in [1, 2) is flagged as degenerate — its best player's
    zero is structural, not a measurement.
37. Every decision surface states which of the three dimensions are answerable before any of them
    is weighed.

---

# Appendix — absence, degeneracy, and the three routes to zero

Investigation only. **No implementation, no weighting, no saturation repair.** This closes the
#61 investigation.

## `bpa = 0.0` is three different claims, not one

| route | condition | what it asserts | moves with the player? |
|---|---|---|---|
| **at the boundary** | VOR = 0, rank D ≥ 2 | *he **is** the marginal starter; D−1 better options exist* | yes — a position in a distribution |
| **below replacement** | VOR < 0, then `clip(lower=0)` | *this far below the marginal starter* | yes — **and the clip destroys it** |
| **degenerate** | VOR = 0, rank 1 (demand ∈ [1,2)) | nothing — replacement **is** him | **no — invariant to his quality** |

Measured, every `bpa == 0.0` row decomposed by route:

| round | zeros | at boundary | degenerate | **clipped negative** | positions at demand ∈ [1,2) |
|---|---|---|---|---|---|
| 6 | 218 | 9 | 0 | **209** | — |
| 9 | 205 | 7 | 0 | **198** | — |
| 11 | 109 | 5 | 0 | **104** | — |
| 13 | 26 | 1 | 0 | **25** | — |
| 15 | 23 | 0 | **1** | **22** | TE |

**The clip dominates.** 95%+ of all zeros are real, measured, *negative* VOR flattened by
`clip(lower=0)` — not degeneracy and not the boundary. The degenerate case is **one row**.
This corrects the emphasis of the previous appendix, which treated degeneracy as the main event.

## The Andrews transition — the proof that the degenerate zero is an artifact

Same player. Same projection. Three rounds.

| round | TE demand | rank | replacement | his pts | his VOR | **his `bpa`** | pool max VOR | C: post-draft |
|---|---|---|---|---|---|---|---|---|
| 13 | 2.33 | 2 | 186 | 187 | 1.0 | **100.0** | 1.0 | 123 |
| 14 | 2.00 | 2 | 186 | 187 | 1.0 | **100.0** | 1.0 | 120 |
| 15 | 1.33 | **1** | 187 | 187 | 0.0 | **0.0** | 0.0 | 120 |
| 16 | 0.67 | — | — | 187 | — | **`None`** | — | 47 |

**`100.0 → 0.0 → None`, with nothing about him changing.** The only thing that moved is
league-wide TE demand crossing 2.0 and then 1.0.

**Two compounding failures produce that swing:**
1. **Rank collapse** takes his VOR from `1.0` to `0.0` — a one-point change in the honest
   quantity, caused by *other teams' rosters*, not by him.
2. **The scale reference** turns that one point into a hundred: pool max VOR is `1.0` at rounds
   13–14, so `bpa = 100` is being awarded on the basis of **a single point of real spread**.

**Diagnostic for the degenerate state:** a measurement invariant to the thing it claims to
measure is not measuring it. At rank 1, Andrews at 187 scores 0 — and a hypothetical TE at 500
would also score 0. The boundary zero and the clipped negative both move with the player; the
degenerate zero does not.

**Verdict: the degenerate zero is a semantic failure, not a legitimate economic conclusion.**
The boundary zero *is* legitimate — it states a real position in a real distribution.

## What B and C say in each of A's states — round 15

| A state | rows | exemplar | pts | `bpa` | B: gap to next | C: post-draft |
|---|---|---|---|---|---|---|
| above replacement | **0** | — | | | | |
| at the boundary | **0** | — | | | | |
| degenerate zero | **1** | M Andrews | 187 | 0.0 | 1 | **120** |
| below replacement, clipped | **22** | I Likely | 186 | 0.0 | 8 | **119** |
| undefined | **125** | C Williams | 324 | `None` | 5 | **28** |

**At round 15 not one player on the entire board has positive VOR.** The priced register holds
one degenerate zero and 22 clipped negatives; the split is between 23 rows that say nothing and
125 rows that say nothing.

And note Andrews (187, degenerate) against Likely (186, clipped negative): **one point of
projection apart, semantically different states, identical scores, and C within one point of each
other.** The two states differ in *meaning* while carrying *identical decision information* —
because at this round **C carries the decision and A carries nothing in either state.**

## The two named cases, explained

**M Andrews (187 pts, degenerate zero).** A is uninformative *by construction* — his zero is a
tautology. B says 1 point: the next TE is a point behind, so nothing is lost this turn. **C says
120: he is worth 120 points more than the TE who will be free after the draft.** The coherent
conclusion is *he is genuinely valuable and only C can say so* — and C is stable at 123/120/120
across the transition where A swings 100 → 0 → None. **C is the only dimension that behaves
continuously here.**

**D Njoku (52 pts).** His zero is a **clipped negative**, not degeneracy: VOR = 52 − 187 = −135.
A did measure him — as 135 points below the marginal starter — and the clip erased it. B says 16.
**C says −15: a better TE is free after the draft.** Every dimension that can speak says pass;
the only reason he ranks first is that his flattened zero sits in the priced register.

**So Andrews and Njoku are not the same case at all.** One is a valuable player A cannot price;
the other is a poor player A priced correctly and then flattened.

## Should a zero-by-construction be treated differently from a boundary zero?

**Semantically, yes — they are different claims.** But the measurement says the operative
distinction is not *degenerate vs boundary*. It is:

> **Does A discriminate at all here?**

- A position where **no remaining player has positive VOR** gives A no discriminating power,
  whichever route each row's zero took. That single test catches degeneracy *and* the
  everything-is-clipped case.
- A **row** whose zero is a flattened negative has a real measurement that was destroyed. That is
  a row-level fact, and by count it is the dominant one.

Two separate problems, and only one of them is about degeneracy.

## Should the register architecture distinguish three states?

**Yes — but three is still too coarse.** A has **five** semantic states and the current
architecture represents **two**:

| A state | claim | current representation |
|---|---|---|
| above replacement | adds this much over the marginal starter | positive `bpa` ✓ |
| at the boundary | he **is** the marginal starter | **`0.0`** |
| below replacement | this far below the marginal starter | **`0.0`** ← destroyed |
| degenerate | nothing; replacement is him | **`0.0`** ← meaningless |
| undefined | no anchor exists | `None` ✓ |

**Three semantically distinct states collapse into the single value `0.0`**, and the register
split as currently proposed separates only the fifth. *Priced and meaningful → priced but
degenerate → unpriced* is a real improvement over *numeric → None*, and it still merges the
boundary zero with the clipped negative — the state that accounts for 95% of the zeros.

## Invariants

38. `bpa = 0.0` is never emitted for more than one semantic state; a row's zero carries which of
    the three routes produced it.
39. A below-replacement measurement is preserved as a measurement. Whether it reaches a 0–100
    scale is a separate decision; flattening it at the point of measurement is not.
40. A position where no remaining player has positive VOR is flagged as non-discriminating,
    independently of which zero-route its rows took.
41. A player's own valuation never changes solely because another team's roster changed, without
    the change being attributable and declared.
42. No 0–100 scale is set by a reference smaller than a declared minimum meaningful spread — a
    `bpa` of 100 awarded on a 1-point VOR is a scale failure, not a valuation.
43. Where A does not discriminate, the decision surface states which of B and C is carrying the
    decision.

---

# Appendix — the three mechanisms, and the normalization reference

Investigation only. **No implementation, no tuning, no threshold chosen.**

**Correction accepted:** the dominant zero route is the clipped negative, not degenerate rank-1
VOR. The measurements below are organised around that.

## Information destroyed at normalization — and it starts early

| round | rows with VOR | **distinct VOR** | **distinct `bpa`** | VOR range | negative range | reference (max) |
|---|---|---|---|---|---|---|
| 4 | 280 | **141** | **20** | 351.0 | 323.0 | 27.00 |
| 8 | 232 | 129 | 13 | 325.0 | 308.0 | 16.00 |
| 11 | 117 | 70 | 4 | 167.0 | 157.0 | 9.00 |
| 13 | 27 | 25 | **2** | 167.0 | 158.0 | 1.00 |
| 15 | 23 | 22 | **1** | 167.0 | 166.0 | 0.00 |

**This is not a late-round problem.** At **round 4** — every position priced, the engine at its
healthiest — 141 distinguishable states become 20. Roughly 121 distinct *negative* VOR values,
spanning 323 points, collapse to the single value `0.0`.

## The three mechanisms

### 1. Genuine VOR at the replacement boundary
- **Before normalization:** VOR = 0 at rank D ≥ 2 — a real position in a real distribution:
  *he is the marginal starter, and D−1 better options exist.*
- **Destroyed:** nothing by the clip itself. What is destroyed is its **distinguishability** — it
  emerges from `_scale_vor_to_bpa` as the same `0.0` as mechanisms 2 and 3.
- **Downstream:** nothing can ask "is he at replacement," because three states share the value.
- **Population:** 5–9 rows at every round measured — small, stable, and the only zero that is a
  measurement.

### 2. Negative VOR erased by the clip — the dominant mechanism
- **Before:** the full below-replacement distribution. 323 points of range at round 4, 166 at
  round 15, across 121+ distinct values.
- **Destroyed:** all of it, at every round. 200+ rows early, 22 late, all mapped to one value.
- **Downstream that depends on it, measured:**

  | consumer | round 4 | round 15 |
  |---|---|---|
  | `detect_positional_cliff` tiers over the top 60 | LOW 43, MEDIUM 12, HIGH 5 | LOW 22, **no answer 38** |

  MEDIUM disappears entirely after round 4. By round 15 the cliff detector cannot answer for 38
  of 60 rows, because it reads **`bpa` gaps** and the gaps are all zero. That signal feeds
  `cliff_protection` and necessity's cliff term. Also dependent: `narrow_candidates` ordering,
  necessity's standout margin, `near_tie_flags`, `decision_regime`, `positional_forfeits`
  curves, and `draft_counterfactual`'s argmax.

### 3. Degenerate / no meaningful reference
- **Before:** nothing. At rank 1 the anchor is a player, not a replacement, so the quantity was
  never information.
- **Destroyed:** n/a — but it is **indistinguishable from a real zero**, which is the harm.
- **Population:** 1 row at round 15, 0 at rounds 6–13.

## The normalization reference

`_scale_vor_to_bpa` anchors on `vor.max()` — the top of the distribution, not its spread.

| round | reference (max) | full VOR range | **reference / range** |
|---|---|---|---|
| 4 | 27.00 | 351.0 | 0.077 |
| 8 | 16.00 | 325.0 | 0.049 |
| 13 | **1.00** | 167.0 | **0.006** |
| 15 | **0.00** | 167.0 | **0.000** |

**The scale divides by a quantity between 0.6% and 7.7% of the information present.** At round 13
`bpa = 100` is awarded for sitting **one point** above replacement while 167 points of range exist
below.

And the discriminating population decays smoothly:

| round | 2 | 4 | 6 | 8 | 10 | 11 | 12 | 13 | 14 | 15 |
|---|---|---|---|---|---|---|---|---|---|---|
| **above replacement** | 77 | 55 | 38 | 23 | 11 | 8 | 3 | **1** | **1** | **0** |
| at 0 | 9 | 9 | 9 | 8 | 6 | 5 | 5 | 1 | 1 | 1 |
| below | 218 | 216 | 209 | 201 | 172 | 104 | 104 | 25 | 24 | 22 |

At rounds 13–14 **one** player is above replacement, max VOR `1.0`, second-highest `0.0` — the
entire 0–100 scale spanned by one player one point clear of the next.

### What a minimum-spread threshold would have to be — characterised, not chosen

| family | form | what it needs | what it inherits |
|---|---|---|---|
| **absolute** | reference must exceed **N points** | a constant in league-scored points | points scale with `scoring_settings`, so N is format-dependent and must be re-derived per format — the magic-constant pattern this engine's own history rejects |
| **relative** | reference ≥ **X%** of `max − min` | one dimensionless constant | `min` is the worst *loaded* player, a truncation artifact of the pool — the same defect as reading a replacement level off the bottom of a short list |
| **domain-dependent** | the scale exists only while **≥ K players sit above replacement** | an integer K | keys on the quantity the register split already uses; needs no points constant; K = 1 is degenerate by construction (that player defines the scale himself), so the smallest non-degenerate value is 2 |

The measurement favours the third family as the only one requiring no invented number in points —
but **K is still a choice and is not made here.**

## Is preserving negative VOR sufficient? No — measured longitudinally

Fixed players, whose projections never change, tracked across rounds. `VOR` is unclipped;
`mgn` is `production_margin` against the fixed pre-draft field.

| player | pos | pts | rd 11 | rd 13 | rd 15 | rd 17 |
|---|---|---|---|---|---|---|
| M Andrews | TE | 187 | VOR **+9** · mgn +0 | VOR **+1** · mgn +0 | VOR **+0** · mgn +0 | VOR — · mgn +0 |
| I Likely | TE | 186 | VOR **+8** · mgn −1 | VOR **+0** · mgn −1 | VOR **−1** · mgn −1 | VOR — · mgn −1 |
| C Williams | QB | 324 | VOR — · mgn +0 | VOR — · mgn +0 | VOR — · mgn +0 | VOR — · mgn +0 |
| D Njoku | TE | 52 | VOR **−126** · mgn −135 | VOR **−134** · mgn −135 | VOR **−135** · mgn −135 | gone |

**Un-clipping restores differentiation but not stability.** Every tracked player's unclipped VOR
drifts by ~9 points across the draft while his production never changes — because the anchor
moves, not because he does. `production_margin` is **exactly constant** for all four at every
round.

Two consequences:

1. **Preserving negatives is necessary but not sufficient.** It restores 121+ distinguishable
   states at round 4 and 22 at round 15 — real, decision-relevant information. It does not make
   the quantity comparable across rounds, because its zero point moves.
2. **The anchor must still be declared undefined once its economic domain is exhausted.**
   Un-clipping cannot rescue a quantity that has no anchor at all: past demand < 1 there is
   nothing to preserve, and Andrews' and Likely's VOR simply stop existing at round 17.

**Corroboration:** Njoku's VOR converges toward his margin (−126 → −134 → −135) as the live
anchor converges on the pre-draft level — the inertness finding, visible longitudinally in a
single player.

## Invariants

44. Below-replacement magnitude is preserved through the valuation layer. Whether it reaches a
    presentation scale is a separate, later decision.
45. A quantity whose zero point moves with draft state is never compared across draft states
    without that movement being declared.
46. The normalization reference is validated against the spread it is meant to represent, and a
    scale is not produced when the reference does not span it.
47. Un-clipping is never treated as a substitute for the anchor's domain: the two failures are
    independent and both must be addressed.
48. Every consumer of `bpa` gaps declares what it does when the gaps are uniformly zero, rather
    than returning a tier or a "no answer" that reads as a property of the players.

---

# Appendix — what `bpa` is for, and where the normalization stops serving it

Investigation only. **No threshold chosen, no scale redesigned, nothing implemented.**

## The stated purpose, from the module's own docstring

> *"BPA is Value Over Replacement in raw projected POINTS … scaled **LINEARLY** against the single
> largest VOR gap in the whole remaining pool — **NOT percentile-ranked**. Percentile-ranking VOR
> was the first pass's mistake: it **threw away the actual size of the gap between players**, which
> is the entire reason VOR is the right anchor over a bounded score in the first place. … Linear
> scaling against the pool's own largest gap **keeps a blowout blowout and a toss-up a toss-up**."*

And a second purpose, stated separately:

> *"folded into the **SAME shared linear scale** … not given its own separate 0-100 range … a
> position with almost no real roster demand correctly can't compete … it has to actually clear
> the same bar."*

So `bpa` is **not** absolute production above a baseline, and **not** a bounded rank. Its contract
is:

1. **Preserve the relative size of gaps between players.**
2. **Put every position on one shared bar** so a thin position's best player cannot win on
   renormalization alone.

## Is the 0–100 max-normalization compatible with purpose 1?

**Within one board state, above zero — yes, exactly.** `bpa = vor / ref × 100` is a positive
linear map, so ratios of gaps are preserved perfectly.

**Within one board state, at or below zero — no.** Every gap is erased by the clip. And that is
most of the board:

| round | rows | above 0 — ratios kept | at/below 0 — gaps erased |
|---|---|---|---|
| 4 | 280 | 55 (**20%**) | 225 (**80%**) |
| 8 | 232 | 23 (10%) | 209 (90%) |
| 11 | 117 | 8 (7%) | 109 (93%) |
| 13 | 27 | 1 (**4%**) | 26 (**96%**) |

**The purpose is honoured for a fifth of the board at its best, and a twenty-fifth at round 13.**

**Across board states — no, and this is the sharper failure.** The reference is recomputed every
pick, so the unit is redefined every pick:

| round | reference | 1 bpa point = real points | a **5-point real gap** reads as | `NEED_BONUS_MAX` buys |
|---|---|---|---|---|
| 2 | 72.00 | 0.7200 | **6.9 bpa** | 8.64 real pts |
| 4 | 27.00 | 0.2700 | 18.5 bpa | 3.24 real pts |
| 8 | 16.00 | 0.1600 | 31.2 bpa | 1.92 real pts |
| 11 | 9.00 | 0.0900 | 55.6 bpa | 1.08 real pts |
| 12 | 2.00 | 0.0200 | 250.0 bpa | 0.24 real pts |
| 13 | 1.00 | 0.0100 | **500.0 bpa** | 0.12 real pts |

**The same five-point real gap reads as 6.9 bpa at round 2 and 500 bpa at round 13 — a 72×
swing — and from round 12 it exceeds the 0–100 ceiling entirely, so the scale cannot represent
it at all.**

### The exact inversion

The max-reference was introduced to stop percentile-ranking from **turning a blowout into a
toss-up**. Measured, it **turns a toss-up into a blowout** — same failure, opposite direction,
introduced by the fix for the first one. It stayed invisible because the test that justified it
("does it preserve gap size?") passes *within a single board state*, which is the only frame the
first defect was ever examined in.

### The additive layer inherits the drift

`NEED_BONUS_MAX` is a fixed `12`. In real points it purchases **8.64 → 3.24 → 1.92 → 1.08 → 0.24
→ 0.12** — a **72× drift in what a constant means**, caused entirely by an upstream quantity, with
nothing in `need_bonus` changing. The same applies to `ELIGIBILITY_BONUS_MAX` and `NEAR_TIE_BAND`.

## Is it compatible with purpose 2?

**Yes — but max is not what delivers it.** Purpose 2 is served by the reference being *shared*,
not by it being the *maximum*. Any single shared reference puts every position on one bar.

**So the two purposes are not in conflict.** Purpose 2 requires a **shared** reference; purpose 1
requires a **stable** one. `vor.max()` is shared but not stable, which is why it satisfies exactly
one of the two.

## The failure boundary

Two boundaries, and they are independent:

| boundary | condition | effect | when it fires |
|---|---|---|---|
| **the floor** | VOR ≤ 0 | all gaps erased | **from round 2** — 80% of the pool by round 4 |
| **the unit** | reference changes | the same real gap changes meaning | **every pick** |

Neither is the exhaustion boundary. Both begin operating while the engine is at its healthiest,
which is why neither was visible from the late-round symptom that started this audit.

## `production_margin` and VOR, side by side — and why neither substitutes

| quantity | unit stable? | zero stable? | what it answers |
|---|---|---|---|
| `production_margin` | **yes** — real points | **yes** — the fixed pre-draft field | production against a fixed league-structural baseline |
| `VOR` | **yes** — real points | **no** — the anchor moves | value against the live marginal starter |
| `bpa` | **no** — the unit is `ref/100` | **no** | relative separation, this board state only |

The two are related by an exact identity:

```
VOR = production_margin + (pre_draft_level − live_level)
```

**The difference between them is itself the quantity of interest** — how far the market has moved
the anchor away from the league's structural baseline. Collapsing to either one destroys that
term: keeping only `production_margin` discards all scarcity information; keeping only VOR leaves
a number whose zero drifts under a player who has not changed.

Measured longitudinally, that identity is visible in a single player: Njoku's VOR converges
`−126 → −134 → −135` onto his constant margin of `−135` as the live anchor converges on the
pre-draft level. **The convergence is the scarcity term going to zero**, not the two quantities
becoming interchangeable.

## Contract, as it must be stated before any repair

- **`bpa` preserves relative separation among available players, on one shared cross-position
  bar.** It is not absolute production and not a rank.
- That contract holds **only above the floor and only within one board state.** Outside either,
  `bpa` is not a weaker version of itself — it is answering a different question.
- **A shared reference is required by purpose 2. A stable reference is required by purpose 1.**
  Any repair must supply both; `vor.max()` supplies only the first.
- **`production_margin` and VOR are not alternatives.** Their difference is the scarcity term, and
  the engine currently has no name for it.

## Invariants

49. `bpa` is compared only within the board state that produced it, unless its reference is
    recorded alongside it.
50. Any additive constant on the `bpa` scale states the real-point quantity it is intended to
    purchase, and that quantity is checked against the live reference.
51. The region in which `bpa` preserves gap ratios is reported with the board, not assumed to be
    the whole board.
52. `production_margin` and VOR are both retained where both are defined; the scarcity term
    between them is named rather than implied.

---

# Appendix — four quantities, four contracts

Answers #75. The previous appendix established that `bpa` preserves within-state gap *ratios*
while failing to preserve a stable *unit*, and concluded that "preserves relative gaps" is not a
contract unless the reference itself has a declared stability property. Before any replacement
scale can be proposed, the quantities underneath it have to be separated and each given its own
contract. This appendix does that and stops there. **No reference is chosen, no coefficient is
chosen, no normalization is designed.**

## The decomposition

```
VOR = production_margin + scarcity_movement

production_margin  = projected_points        − pre_draft_level[position]
scarcity_movement  = pre_draft_level[position] − live_level[position]
```

The identity is exact by construction — the `pre_draft_level` term cancels. What the identity
buys is that the two addends have **different stability properties**, and VOR exposes neither.
`production_margin` has a stable unit *and* a stable zero. `scarcity_movement` has a stable unit
and a zero that means "the market has not moved". Their sum has a stable unit and no stable zero
at all, and a consumer holding only the sum cannot tell which addend moved.

## Is the `scarcity_movement` scalar a faithful representation? No.

It is the arithmetic residual of two large, always-opposite-signed effects. Decomposing the live
level against the pre-draft field separates them:

- **demand movement** — the anchor slides *up* the original board because fewer starters are
  still needed: `level_at(rank_t, pre_draft_field) − level_at(D₀, pre_draft_field)`. Always ≥ 0.
- **supply movement** — the anchor slides *down* because the players at that rank have been
  taken: `level_at(rank_t, live_pool) − level_at(rank_t, pre_draft_field)`. Always ≤ 0.

Their sum is exactly `−scarcity_movement`. Measured across the 12×20 audit board:

```
 rd  pos   D  rank_t  preDraft  live  scarcityMove  demandMove  supplyMove
  2   TE  16      12       187   187            +0         +10         -10
  2   RB  28      15       178   178            +0         +62         -62
  5   RB  28       7       178   171            +7         +92         -99
  8   RB  28       6       178   162           +16        +115        -131
 11   RB  28       2       178   176            +2        +168        -170
 13   TE  16       2       187   186            +1        +119        -120
 15   TE  16       1       187   187            +0        +122        -122
```

Every sampled state has the two components opposite in sign, reaching ±170 real points, while the
scalar they produce stays inside 0–16. **The scalar is a near-cancellation of two market facts,
and it reports neither.**

Sweeping every (round, position) with a defined live level, distinct market states collide onto
the same scalar in 5 buckets:

| `scarcity_movement` | distinct states | demand-movement spread | example collision |
|---|---|---|---|
| `+0` | 33 | 147 | rd 1 QB (nothing drafted, `+0/−0`) vs rd 15 TE (`+122/−122`) |
| `+2` | 12 | 161 | rd 9 K (`+7/−9`) vs rd 11 RB (`+168/−170`) |
| `+9` | 6 | 28 | rd 7 WR (`+69/−78`) vs rd 11 TE (`+97/−106`) |
| `+13` | 4 | 23 | rd 6 RB (`+92/−105`) vs rd 10 RB (`+115/−128`) |

The `+0` row is the decisive one. **Zero scarcity movement is produced both by "the draft has not
started" and by "demand has fallen from 16 to 1 and the pool has drained 122 points."** No
consumer reading the scalar can distinguish an untouched market from a fully consumed one.

Verdict: `scarcity_movement = pre_draft_level − live_level` is **adequate as an accounting
identity** — it closes the decomposition exactly — and **inadequate as a representation** of the
information the moving anchor is carrying. Anything that needs to reason about scarcity needs the
two components; the difference is where the information goes to die.

## The structural fact the decomposition exposes

`scarcity_movement` is a **per-position, per-state constant**. Every player at a position receives
exactly the same value. Therefore adding it to `production_margin` **cannot change within-position
ordering at all** — its entire causal power is to shift positions relative to each other.

This is #60's inertness finding restated at the contract level, and it explains it: the anchor's
only lever is cross-position re-ranking, and the two components cancel to a 0–16 point residual
against production margins spanning hundreds. The anchor is not weakly wired. It is doing the only
thing it can do, with a number that has already cancelled itself out.

## Who receives scarcity information, and how

Direct readers of demand or replacement outside `draft_room.py` — **exactly two**:

| Site | What it reads | What it receives |
|---|---|---|
| `pick_synthesis.py:842` → `position_view_depth` | `replacement_ranks` — an integer count | demand movement only. Never a level, never supply movement. Controls how many candidates per position enter the debate; touches no score. |
| `roster_diagnostics.py:119` | `replacement_levels` **with no demand argument** | the *pre-draft* anchor. Deliberately reads `production_margin`'s baseline and receives **no** scarcity information at all. |

**No consumer outside `draft_room.py` reads the live replacement level.** Every other consumer
receives the entire scarcity term only through `bpa`, and through the
`universal_value → team_acquisition_value → final_score` chain built on it:

- `draft_strategy.py` — `opportunity_cost = team_acquisition_value × (1 − survival_probability)`;
  `positional_forfeit` walks per-position `universal_value` curves; denial
  `premium = final_score − universal_value`.
- `pick_synthesis.py` — `expected_value_of_waiting = survival_probability × universal_value`;
  necessity's standout margin over `team_acquisition_value`; cliff detection on within-position
  `bpa` gaps; `NEAR_TIE_BAND`.
- `pick_debate.py` — the LLM prompt receives `universal_value` and `team_acquisition_value` as
  bare numbers **with no anchor attached**; `_runner_up` is `max(team_acquisition_value)`.
- `draft_simulation.py` — `candidates[0]`, i.e. top `team_acquisition_value`.
- `draft_board_ui.py` / `app.py` — display.
- `lineup_optimizer.py` — emits a raw eligibility number that `draft_room` rescales onto the
  `bpa` scale.

Consequence: the scarcity term is squeezed through a single normalization before anyone but two
observers sees it, and that normalization is exactly the step that destroys its unit.

## What the absolute constants purchase, state by state

Every additive or threshold constant in the contextual layer is denominated in `bpa` points.
Because the reference is `max(VOR)` over the live pool, the real-point value of one `bpa` point is
`reference/100`, and it moves:

```
 rd  reference (maxVOR)  NEAR_TIE_BAND=2.0  STANDOUT_GAP=15.0  NEED_BONUS_MAX=12.0
  1                97.0               1.94              14.55                11.64
  2                72.0               1.44              10.80                 8.64
  6                17.0               0.34               2.55                 2.04
 10                13.0               0.26               1.95                 1.56
 13                 1.0               0.02               0.15                 0.12
 15   no positive ref                   --                 --                   --
```

`NEAR_TIE_BAND` buys 1.94 real points at round 1 and 0.02 at round 13 — a 97× drift in the
definition of "these two players are tied". By round 15 the reference is non-positive, every
`bpa` is 0.0, and all three constants purchase nothing whatsoever.

**A constant is scale-bound only if it is absolute.** The cliff detector splits on exactly this
line, inside one function:

- `CLIFF_HIGH_RATIO = 2.5`, `CLIFF_MEDIUM_RATIO = 1.5` compare gap against gap. The reference
  cancels; these are **invariant** under any positive rescale.
- `CLIFF_MIN_MATERIAL_GAP = NEAR_TIE_BAND = 2.0` is the absolute gate that decides which gaps are
  admitted to that ratio test. It **does not cancel.**

So under renormalization the cliff *tiers* stay stable while *which gaps qualify as cliffs at all*
moves. That is a subtler failure than a shifted threshold: the classification is stable, the
population being classified is not.

## What `bpa` actually needs to preserve

Taking the mandate's four candidates and testing each against the consumer map above:

| Candidate property | Required? | By whom, and why |
|---|---|---|
| **Stable cross-player comparison within a state** | **Yes — load-bearing** | Every selection site is an argmax or a sort: `candidates[0]`, `_board_order`, `_runner_up`, necessity's standout margin. If this fails, the engine picks the wrong player. |
| **Shared cross-position comparability** | **Yes** | The board is one list across positions; `_board_order` sorts a QB against a TE. A per-position scale would make the primary artifact unorderable. |
| **Meaningful gap magnitude (stable unit)** | **Yes, for a subset** | `NEAR_TIE_BAND`, `NECESSITY_STANDOUT_REFERENCE_GAP`, `CLIFF_MIN_MATERIAL_GAP`, `NEED_BONUS_*`, `ELIGIBILITY_BONUS_MAX`. These read magnitude, not order, and are the consumers currently broken. |
| **Bounded output (0–100)** | **No — required by nothing measured** | No consumer asserts `bpa ≤ 100`. The additive constants are *sized* as though the scale were 0–100, but that is a design convention, not a consumed invariant. |
| **Cross-state comparison** | Not today | Nothing attempts it — but only because nothing attempts it. `pick_debate`'s prompt hands an LLM bare numbers with no anchor, which is cross-state comparison waiting to happen. |

## The trilemma, and which horn nothing is holding

A normalization can hold any two of these three, never all three:

1. **Bounded output** — `bpa ∈ [0, 100]` for every board state.
2. **Stable unit** — one `bpa` point is a fixed number of real points, in every board state.
3. **No clipping** — no input is compressed or truncated to fit.

- Bounded + no clipping ⇒ the reference must track the state's own range ⇒ **the unit moves.**
  This is today's design, and the 97× drift is the bill for it.
- Bounded + stable ⇒ the reference must be a state-invariant bound on the input domain, and
  anything exceeding it **must clip** — information lost at the top rather than in the unit.
- Stable + no clipping ⇒ **output is unbounded.**

The table above says nothing consumes property 1. **The horn to release is bounded output**, which
is the one the current design protects hardest. Stating this is not choosing a replacement: it
rules out one family and leaves the rest open. The reference, the unit, and every coefficient
remain unchosen and are not proposed here.

Note also that today's design pays the clipping cost *anyway*, at the bottom: negative VOR clips
to 0. It is holding neither 2 nor 3 while protecting a property nothing reads.

## The four contracts

### `production_margin` — the stable observational quantity

- **Unit** real fantasy points. **Zero** the league's structural baseline starter at that
  position, fixed before the draft and never moving.
- **May carry** how much production a player delivers above or below that baseline. Comparable
  across players, across positions, and across draft states.
- **May not carry** anything about what has been drafted. It is deliberately blind to the market,
  and that blindness is precisely what makes it stable.
- **Domain** wherever `projected_points` exists and the position has pre-draft starter demand ≥ 1.
  Independent of live demand — so it survives into the unpriced register, where VOR does not.
- **Sign is meaningful.** Negative means genuinely below the structural baseline. Never clipped.

### `scarcity_movement` — the market quantity, currently unnamed and unfaithful

- **Unit** real fantasy points. **Zero** "the market has not moved."
- **May carry** market consumption at one position.
- **May not carry** anything player-specific. It is a per-position, per-state constant; every
  player at the position gets the same value.
- **Currently inadequate as stated.** As a scalar it is a residual of demand movement and supply
  movement, which are always opposite in sign and up to ±170 points, and distinct market states
  collide onto the same number — including "nothing drafted" and "fully consumed" both reading
  `+0`. It closes the identity and represents nothing.
- **What is required of it** is that the two components be carried separately, or that any
  consumer reasoning about scarcity read the components rather than the residual. Neither is
  designed here.

### `VOR` — the anchor-dependent economic quantity

- **Unit** real fantasy points, stable. **Zero** the live marginal starter — moves every pick.
- **May carry** value against the live marginal starter.
- **May not carry** any cross-state claim unless its anchor travels with it.
- **Domain** narrower than `production_margin`'s: only where the live level is defined (remaining
  demand ≥ 1). That gap between the two domains *is* the unpriced register.
- **Sign is meaningful.** Never silently clipped — clipping is where the three routes to zero
  collapse into one indistinguishable value.
- **Structural defect of the type itself:** it is the sum of two quantities with different
  stability properties and it exposes neither. A consumer holding only VOR cannot tell whether a
  change came from the player or from the market.

### `bpa` — the ordering surface

- **May carry** relative separation among available players, on one shared cross-position bar,
  **within a single board state and above the clip floor.**
- **May not carry** absolute production, a stable unit (today), cross-state comparison, or any
  statement about players at or below the floor.
- **Required to preserve** within-state cross-player order, cross-position comparability, and a
  stable unit for the magnitude-reading consumers. **Not** required to be bounded.
- **Is the sole channel** through which every consumer but two receives any scarcity information
  at all.

## Invariants

53. `production_margin`, `scarcity_movement`, and VOR are three quantities with three different
    stability properties. Any of them may be displayed; none is a substitute for another.
54. A scalar difference of two levels is not a representation of the market unless the components
    that produced it are recoverable or separately carried.
55. `scarcity_movement` cannot reorder players within a position. Any claim that the anchor
    changes intra-positional ordering is false by construction.
56. A constant expressed as a ratio of two `bpa` gaps is invariant under renormalization; a
    constant expressed as an absolute `bpa` quantity is not. Mixing the two inside one decision
    (as `detect_positional_cliff` does) makes half of it move and half of it hold.
57. Bounded output, a stable unit, and no clipping cannot all hold. The property to release is the
    one no consumer reads.
58. `bpa` is the only channel carrying scarcity to the decision layer. Any change to the scarcity
    representation is a change to every consumer downstream of it, whether or not that consumer
    mentions scarcity.

---

# Appendix — what BPA is, once the bundle is opened

Answers #76. The previous appendix separated `production_margin`, `scarcity_movement`, VOR and
`bpa` and stated what each may carry. This one tests `bpa` against the properties the downstream
system actually requires, audits it along the full semantic chain rather than at its formula, and
uses credible external rankings as a **diagnostic** — never as an input. **No normalization is
designed, no reference chosen, no coefficient tuned.**

## The full-chain audit

The doctrine addendum requires evaluating a quantity along
`definition → domain → state transitions → upstream assumptions → downstream consumers →
interactions`. Applied to `bpa`:

| link | finding |
|---|---|
| **definition** | `clip(vor / max(vor) × 100, 0, 100)`. Self-contained, deterministic, correct as written. Nothing in the formula is wrong. |
| **domain** | defined only where the position's live level exists (remaining demand ≥ 1) **and** `max(vor) > 0`. **Two independent domain conditions; only the first is documented anywhere.** The second fires at round 15 on the audit board. |
| **state transitions** | two, both undeclared: the anchor moves every pick (`scarcity_movement`, #75) and the **reference** moves every pick. Measured below: the reference carries **94.5%** of all `bpa` movement. |
| **upstream assumptions** | `_vor` is built from a **single-season** points projection — in dynasty leagues as well as redraft. The multi-year outlook never reaches `bpa`; it enters one layer later as `time_horizon_adj`. **`bpa` silently assumes the production horizon is one season.** |
| **downstream consumers** | nine; all but two receive every piece of scarcity information only through here (#75). Five read *magnitude* against absolute constants that assume a stable unit. |
| **interactions** | `universal_value = bpa + time_horizon_adj + risk_adj` adds two **stable-magnitude** quantities to one **collapsing-magnitude** quantity. Measured below. |

The last row is the new finding, and it is the doctrine's own thesis in miniature: every one of
those three terms is locally correct, and their sum stops meaning what it says.

## The horizon is priced on a ruler that shrinks under it

`TIME_HORIZON_SLOPE = 0.20` on a percentile difference, clamped to `±10.0` **bpa points**;
`RISK_ADJ` is `−1.5 … −18.0` on the same scale. Both are documented as *"small, bounded, additive
nudges … deliberately incapable of overriding a real VOR gap on their own."* Measured over the
priced rows of the audit board:

```
 rd  priced  mean|bpa|  mean|thadj|  nudge share of |uv|   ±10 clamp buys (real pts)
  1     316       8.53         2.15                0.201                        9.70
  4     280       6.60         2.28                0.257                        2.70
  8     232       4.66         2.57                0.355                        1.60
 12     112       2.23         1.88                0.458                        0.20
 13      27       3.70         1.60                0.302                        0.10
 15      23       0.00         1.38                1.000                   no scale
```

Two independent failures, visible together:

1. **The premise inverts.** `mean|bpa|` falls `8.53 → 0.00` while `mean|time_horizon_adj|` holds
   near 1.4–2.6, because it is computed from projection percentiles and is anchor-independent.
   The nudge carries **20% of `universal_value`'s magnitude at round 1, 46% at round 12, and
   100% at round 15** — where every `bpa` is `0.0` and `universal_value` *is* the nudge. Neither
   constant changed. The quantity they were sized against collapsed underneath them.
2. **The dynasty signal is denominated in the drifting unit.** The full `±10` clamp — the entire
   multi-year consideration the engine has — purchases **9.70 real points at round 1 and 0.10 at
   round 13**, and nothing at all at round 15.

(`mean|risk_adj|` is `0.00` throughout this fixture: no injury flags in the pool. With real
injury data the nudge share is strictly higher than measured here.)

So on the horizon principle, the current state is: **`bpa` is redraft-shaped in both league
types**, and the dynasty horizon is a bounded additive nudge on a scale that loses 97× of its
purchasing power over a draft. That arrangement cannot express a dynasty production horizon; it
can only tilt a season number.

## Longitudinal: 94.5% of `bpa` movement is the ruler, not the player

For players whose projection never changes, `Δbpa` decomposes exactly:

```
own effect       = 100 × (vor₂ − vor₁) / ref₁          his value against the anchor moved
reference effect = 100 × vor₂ × (1/ref₂ − 1/ref₁)      the ruler moved under him
own + reference  = Δbpa                                exactly
```

```
    transition    ref₁    ref₂  players  mean|Δbpa|  mean|own|  mean|ref|  ref share
    rd1 → rd2    97.0    72.0      304        21.6        0.0       21.6      1.000
    rd2 → rd4    72.0    27.0      280       141.4        0.7      141.8      0.995
    rd6 → rd8    17.0    16.0      232        22.0       23.5       23.7      0.503
   rd10 → rd11   13.0     9.0      117       204.2       29.7      174.6      0.855
   rd11 → rd12    9.0     2.0      112      2166.3       25.0     2142.0      0.988

 pooled: reference effect 94.5% of all bpa movement, own effect 5.5%
```

`rd1 → rd2` is the cleanest case: mean `|Δbpa|` of **21.6 points with exactly 0.0 attributable to
any player's own change.** The whole movement is the reference.

Concretely, on players whose projections are constant all draft (clipped, as shipped):

```
   player   pts   rd1   rd2   rd4   rd6    rd8   rd10   rd11   rd12
 I Likely   186   0.0   0.0   0.0   0.0   50.0   61.5   88.9    0.0
M Andrews   187   0.0   0.0   3.7   5.9   56.2   69.2  100.0   50.0
```

**Isaiah Likely climbs from 0.0 to 88.9 and falls back to 0.0 without one thing about him
changing.** Answering the question the mandate poses: this movement is **not economically
intended.** The economically real market movement is the *anchor* moving, and #75 measured that
at a 0–16 point per-position residual which cannot reorder within a position at all. The
reference is a property of **one other player** — whoever currently tops the pool, and who is
himself about to be drafted. Every other player's unit is set by that single row.

## Does anything require the 0–100 bound? No.

Searched every consumer of `bpa`, `universal_value`, `team_acquisition_value` and `final_score`:

| site | what it looked like | what it is |
|---|---|---|
| `pick_synthesis.py:369` `min(100.0, raw_score)` | a bpa bound | **`pick_necessity`**, a different 0–100 quantity assembled from weights that sum to ≤ 100 by construction. Reads a bpa *gap*, never a bpa *level*. |
| `pick_debate.py:229` `{pick_necessity}/100` | a bpa bound | same quantity, printed. |
| `data_merger.py:1334` `trade_value.clip(0,100)` | a bpa bound | the composite input scale, **upstream** of `bpa`. |
| `app.py` composite `/100` | a bpa bound | the source-composite score, unrelated. |
| UI bar widths | a bpa bound | none is scaled by a valuation; `width:100%` is CSS layout. |

**Zero consumers require `bpa ≤ 100`. Five require a stable unit and do not have one.** Bounded
output is the property the current design protects hardest and the only one nothing reads. If a
bounded presentation is wanted, it is a rendering concern and can be applied at the surface
without the underlying quantity losing information.

Two constants deserve separating here, because they behave differently under any rescale:

- `denial_component = min(rival_premium / NEED_BONUS_MAX, 1.0)` — a **ratio** of two bpa-scale
  quantities. Scale-invariant; survives renormalization untouched. (Its denominator is
  `NEED_BONUS_MAX` alone while `rival_premium` can reach `NEED_BONUS_MAX + ELIGIBILITY_BONUS_MAX`
  — a separate, pre-existing 2× mismatch, recorded and not fixed here.)
- `standout_component = clip(margin / NECESSITY_STANDOUT_REFERENCE_GAP, 0, 1)` — an **absolute**
  bpa gap against a fixed `15.0`. Drifts with the unit, 14.55 real points down to 0.15.

## External rankings, used as a diagnostic

Role, per the mandate: *external ranking → surprising CDME ordering → investigate → justified
difference or identified defect.* No ordinal is converted to a value; ordinals are used only to
ask whether two sources order the same **pair** the same way. CDME is never asked to reproduce
them.

**Independence check first.** On the audit board every priced row is sourced
`points_vor_draftsharks` (259) or `points_vor_sleeper_seeded` (69); **no row uses the
`position_relative_trade_value_vor` fallback.** FantasyPros, KeepTradeCut and DynastyProcess are
therefore genuinely independent of what `bpa` is built from here. **This is conditional, not
general:** those three sources sit inside `COMPOSITE_SOURCE_WEIGHTS`, so on any board where the
trade_value fallback fires, the diagnostic is circular for those rows and must be declared
invalid for them rather than read as agreement.

**Pairwise ordinal agreement**, restricted to pairs `bpa` materially separates (gap >
`NEAR_TIE_BAND`) and both players externally ranked:

```
  rd   source                within-position        cross-position
   0   FantasyPros            89.9%  ( 4465)         76.3%  (15872)
   0   KeepTradeCut           88.0%  ( 4307)         80.2%  (10797)
   0   DynastyProcess         89.5%  ( 4294)         84.4%  (10728)
   4   FantasyPros            86.6%  ( 1922)         59.5%  ( 9263)
   8   FantasyPros            86.9%  (  826)         73.9%  ( 3069)
   8   DynastyProcess         79.3%  (  799)         76.7%  ( 2171)
```

**Within-position ordering is corroborated at 79–90% by all three sources at every round.** That
is expected and reassuring: `scarcity_movement` is a per-position constant and cannot reorder
within a position (#75), so within-position order is essentially production order — and
production order agrees with independent expert opinion.

**Cross-position ordering — the job `bpa` exists to do — is 5 to 27 points worse, and dips to
59.5% at round 4**, the state where the clipped population peaks at 80% of the board.

### Splitting the disagreements by mechanism

A first pass classified these by "the externally-preferred player has more projected points,"
which **mislabels anchor-driven reversals as clip damage** — a legitimate positional-baseline
reversal is exactly what `bpa` is for. Re-split on the actual mechanism:

| | condition | reading |
|---|---|---|
| **clipped** | the loser's **unclipped** VOR < 0 | CDME measured a difference and printed `0.0`. **Defect.** |
| **anchor** | both have positive VOR; the baseline reversed the points order | `bpa` doing its declared job. **Legitimate** — the source weighs scarcity differently. |
| **horizon** | loser priced positive, ranked better externally on fewer CDME points | the source prices a future a season number cannot carry. **Legitimate.** |

```
 rd          source  disagree  clipped  anchor  horizon
  0     FantasyPros      3769    74.8%   15.9%     9.3%
  0    KeepTradeCut      2140    57.9%   28.1%    14.0%
  0  DynastyProcess      1673    55.2%   25.6%    19.1%
  4     FantasyPros      3751    86.8%   11.5%     1.7%
  8     FantasyPros       801    89.1%    8.5%     2.4%
  8  DynastyProcess       506    85.0%   10.3%     4.7%
```

Three independent sources, three methodologies, the same shape: **the dominant reason CDME
disagrees with credible external opinion cross-positionally is the clip — not a scarcity
philosophy and not a horizon difference.** The clip share *rises* through the draft (55–75% →
85–89%) as the clipped population grows.

Worked examples, round 4, FantasyPros:

```
[clipped] Judkins (RB, 202 pts, vor +26, bpa 96.3) > Tyson    (WR, 145 pts, vor −65, bpa  0.0)   #53 vs #40
[ anchor] Judkins (RB, 202 pts, vor +26, bpa 96.3) > Waddle   (WR, 235 pts, vor +25, bpa 92.6)   #53 vs #45
[horizon] Warren  (RB, 202 pts, vor +26, bpa 96.3) > Kincaid  (TE, 189 pts, vor  +3, bpa 11.1)  #111 vs #89
```

The anchor row is the important one to *not* fix: Judkins beats Waddle on one VOR point despite
33 fewer projected points, because RB's baseline is lower. FantasyPros disagrees. **That is a
defensible divergence CDME can explain from its own inputs, and it must survive any repair.**

### The boundary case, against independent opinion — round 15

| player | pos | pts | bpa | tav | FantasyPros | KeepTradeCut | DynastyProcess |
|---|---|---|---|---|---|---|---|
| C Williams | QB | 324.0 | `None` | `None` | **#47** | **#10** | **#46** |
| D Njoku | TE | 52.0 | 0.0 | **1.16** | #197 | #252 | #208 |
| M Andrews | TE | 187.0 | 0.0 | −3.61 | #130 | #187 | #135 |

Three independent sources place Williams **150 to 242 places above** Njoku. The board puts Njoku
first because he carries a number and Williams carries `None`.

This is not a divergence CDME can justify. **CDME is not making a claim here at all** — the
ordering is a side effect of `na_position='last'`. And every dimension that *can* speak agrees
with the external sources: post-draft substitution cost is **−15 for Njoku and +28 for Williams**,
i.e. *waiting on Njoku is better than free*. The engine computes that and then ranks him first.

The converse the mandate asks for is equally required: **a strong TE must be able to win this
comparison on the record.** Andrews at 187 points has a post-draft substitution cost of **+120**
against Williams' +28 — a real, large, defensible case for the tight end, expressed in a
dimension that is answerable at that round. What is not acceptable is a tight end winning because
"numeric TAV outranks undefined TAV."

## Which dimensions are answerable, by regime

| regime | A — production/value | B — in-draft loss | C — post-draft substitution | D — roster context |
|---|---|---|---|---|
| rounds 1–5 | all six positions | all six | partial (TE absent early) | **all rows** |
| rounds 7–9 | all six | all six | all six | **all rows** |
| round 11 | RB TE K DEF | RB TE K DEF | all six | **all rows** |
| rounds 13–15 | TE only | TE only | all six | **all rows** |
| rounds 17–19 | none | none | all six | **all rows** |

B's window *is* A's — it is built from `universal_value` curves. **A and C are never both absent,
and D is never absent at all** (the contextual layer is fully anchor-independent, verified exact:
`tav ≡ uv + need_bonus + eligibility_bonus`, max error `0.0000`).

What each may legitimately contribute:

- **A — production/value magnitude.** How much a player produces over the appropriate positional
  baseline, on the league's production horizon. It may not carry scarcity movement, roster fit,
  or a claim about who else will pick.
- **B — in-draft loss.** What may be lost before the next pick. Probability × magnitude, horizon
  = my next pick. It may not stand in for A when A is absent — B is *built from* A.
- **C — post-draft substitution cost.** What remains available after the draft. Horizon = end of
  draft. It is most reliable exactly where A is weakest, and its negative values are first-class.
- **D — need / eligibility / fit.** Roster-specific context. Measured ceiling in the unpriced
  register is `0.33` against a 230–257 point production spread — **real, exact, and not an
  ordering signal on its own.**

No weighting is proposed. The precondition the evidence establishes is that **the engine must be
able to state which dimensions are answerable before any of them is weighed**, and no dimension
may be substituted for another when its own inputs are missing.

## Is `bpa` one quantity or several?

The measured semantics say **several**. `bpa` today answers at least four questions, and
`universal_value` folds in two more:

| bundled concept | evidence it is separable |
|---|---|
| production surplus over a positional baseline | the intended core; corroborated within-position at 79–90% by three independent sources |
| scarcity movement | a per-position constant that cannot reorder within a position; two components cancelling to a 0–16 residual (#75) |
| a normalization reference | `max(vor)` — a property of one other player; **94.5% of all `bpa` movement** |
| a floor decision | the clip; merges three semantic states and drives **55–89%** of external cross-position disagreement |
| production horizon | `time_horizon_adj`, `±10` bpa; **100% of `universal_value` by round 15** |
| current-status risk | `risk_adj`, same scale, same drift |

These are six questions in one number, and each has been measured to move independently of the
others. The one thing the evidence says to **keep together** is production surplus and
cross-position comparability: that pairing is `bpa`'s stated purpose, and it is the part
independent expert opinion corroborates. Splitting *that* would be splitting for cleanliness.

Everything else in the list is a separate quantity wearing `bpa`'s name.

## Invariants

59. `bpa` carries production surplus over a positional baseline, on the league's production
    horizon, expressed so that positions are comparable. It carries nothing else.
60. The production horizon is a property of the league, not of the draft state. In a dynasty
    league the horizon reaches `bpa` itself, not a bounded additive nudge applied afterwards.
61. No quantity whose magnitude is stable is added to a quantity whose magnitude collapses,
    unless the ratio between them is itself declared and checked.
62. The draft state contextualizes a valuation; it never redefines the valuation's unit. A
    player's score does not move because a different player was drafted, unless that movement is
    attributable, declared, and economically intended.
63. The normalization reference is never a property of a single other row.
64. A below-baseline measurement is preserved as a signed measurement. Genuine zero, clipped
    negative, degenerate anchor and undefined valuation are four distinct states and are never
    represented by one value.
65. Bounded presentation is a rendering decision. No information is destroyed in an underlying
    quantity to obtain a bounded range.
66. External rankings are diagnostics, never inputs. A divergence is investigated and resolved as
    either justified or a defect; it is never closed by moving CDME toward the ranking.
67. An external source is a valid diagnostic for a row only where it is not already inside that
    row's own valuation path. Where the trade_value composite priced the row, the diagnostic is
    declared invalid for it rather than read as agreement.
68. Every decision states which of A, B, C, D are answerable in the current regime before any is
    weighed, and no dimension substitutes for another whose inputs are absent.

---

# Appendix — the consolidated downstream contract

Answers the consolidation half of #77. The previous appendices each ended in a patch-sized
finding. This replaces that list with one architecture. Nothing here chooses a coefficient, a
reference, or a normalization.

## The seven quantities, and what each is

Categories are the doctrine's: **P** player property · **L** league/format property ·
**C** current-state/context · **D** decision output.

| quantity | cat | answers | unit / zero | may not carry |
|---|---|---|---|---|
| **production** | P | what this player is projected to produce | league scoring points, over the league's horizon | anything about the draft, the roster, or other players |
| **production margin** | P + L | production against the structural baseline for his position | real points; zero = the league's pre-draft marginal starter | live scarcity, need, availability |
| **BPA** | P + L | the cross-positional production/value signal | a **declared, state-invariant** unit | scarcity movement, waiting cost, roster fit, risk |
| **scarcity movement** | C | how the live market has moved this position | real points, per position, per state | anything player-specific — it is constant within a position |
| **in-draft waiting cost** | C | what may be lost before my next pick | probability × magnitude, horizon = next pick | the post-draft question |
| **post-draft substitution cost** | C | what remains available after the draft | real points, horizon = end of draft | the in-draft question; negatives are first-class |
| **need / eligibility / fit** | C | what this roster is missing | bounded roster-fit points | player quality |
| **selection output** | D | what to do, here, now | a recommendation with its inputs named | a claim to be any one of the above |

Crossing P and C requires the named reconciliation step the doctrine demands. The selection layer
**is** that step, and it is the only place the crossing is licensed.

## The ten rules

1. **BPA is the stable, cross-positional production/value signal over the league's horizon.**
   Redraft: the current season. Dynasty: the short- and long-term horizon, combined under the
   dynasty model's own explicit time/aging/uncertainty assumptions — **inside BPA, not as a
   bounded nudge applied to it afterwards.**
2. **Production margin is a stable observational quantity** against the structural baseline. It
   is defined wherever production is, independent of live demand, and never clipped.
3. **Scarcity movement is separate positional-market information.** BPA does not carry it. It is
   a per-position constant and cannot distinguish players within a position, so folding it into a
   per-player score hides it rather than using it.
4. **In-draft waiting cost and post-draft substitution cost are two contextual questions**, with
   different horizons and different availability windows. Neither substitutes for the other, and
   neither is fused into a single "cost of waiting".
5. **Need, eligibility, risk/status, draft state and roster fit are contextual inputs**, not
   intrinsic player properties, regardless of which row they are stored on.
6. **`None`, genuine zero, clipped negative, and degenerate anchor are four distinct states** and
   are never represented by one value. A below-baseline measurement stays a signed measurement.
7. **No consumer may treat "has a number" as inherently superior to "does not have a number."**
   That includes sorts, ranks, ordinals, argmax, null placement, and rendering order.
8. **No normalization may let its unit change because the remaining player pool changed.** The
   reference is never a property of a single other row.
9. **External rankings are independent diagnostic flags**, never numerical ingredients and never
   targets. A divergence resolves as justified or as a defect; it is never closed by moving CDME.
10. **The selection layer may combine player signal and decision context**, and every component
    retains its declared meaning, its category, and its own name inside the combination.

## Consumer census — everything that depends on the quantities being changed

Counted over the production modules (tests, scratch and `run_*` harnesses excluded).

| quantity | sites | modules |
|---|---|---|
| `universal_value` | 79 | `draft_room`, `draft_strategy`, `pick_synthesis`, `pick_debate`, `draft_board_ui`, `draft_counterfactual`, `lineup_optimizer`, `roster_diagnostics`, `app`, `cdme_denial_semantics_audit` |
| `team_acquisition_value` | 63 | the above plus `draft_simulation`, `screen_context`, `cdme_force_ablation` |
| `survival_probability` | 49 | `draft_strategy`, `pick_synthesis`, `pick_debate`, `draft_board_ui`, `screen_context`, `app` |
| `need_bonus` / `eligibility_bonus` | 38 / 36 | `draft_room`, `pick_synthesis`, `pick_debate`, `lineup_optimizer`, `roster_diagnostics`, `draft_board_ui`, `app` |
| `bpa` | 33 | `draft_room`, `draft_strategy`, `pick_synthesis`, `lineup_optimizer`, `draft_board_ui` |
| `final_score` | 23 | `draft_room`, `draft_strategy`, `pick_synthesis`, `draft_counterfactual` |
| `positional_cliff` | 17 | `draft_strategy`, `pick_synthesis`, `pick_debate`, `draft_board_ui`, `app` |
| `projected_points` | 15 | `draft_room`, `pick_synthesis`, `pick_debate`, `draft_board_ui`, `app` |
| `waiting_cost` / `horizon_floor` | 13 / 12 | `draft_room`, `pick_synthesis`, `draft_board_ui` |
| `_vor` | 4 | `draft_room` only |

**Twelve production modules.** `_vor` is the only quantity in the set that never leaves its own
module — which is precisely why the normalization applied to it is invisible to everyone reading
its output.

---

# Appendix — upstream lineage: is the canonical player record a sound boundary?

Answers the lineage half of #77. **The hypothesis under test is not that the data is bad.** It is
whether an incorrect, mismatched, stale or semantically incompatible input is *exposed* by the
ingest/reconciliation layer, or silently converted into a plausible field that survives into
valuation. Nothing was repaired; nothing upstream was changed.

## Result first

| question | verdict |
|---|---|
| **Do the downstream findings (#60–#76) rest on contaminated identity?** | **No.** Measured directly: the universe those probes used resolves **349/349 by the exact path, 0 position mismatches, 0 non-injective mappings.** The observed downstream behaviour is a model/architecture problem, not a data artifact. |
| **Is the canonical record a sound semantic boundary into valuation?** | **No, not yet.** Seven canonical identities are claimed by two different real people; six crossed wires survive under the live team-supplied condition; every one of them comes from a single unguarded code path. |
| **Does one parsed record = one player, one context, one consistent field set?** | **Holds when both PDF blocks are complete and ordered; violated silently otherwise.** Demonstrated against the real parser. |

## The identity boundary

`build_available_pool` calls `merger.merge_player(name, position, team)` for each Sleeper player,
so **the identity layer is on the valuation path**, not only on the display path. It resolves
Sleeper **full** names onto Draft Sharks **first-initial-only** canonical rows (`A Hutchinson`,
`J Daniels`), which means the exact-match path structurally cannot fire in that direction and
everything falls to the `(first-initial, full-remaining-name)` key or the fuzzy fallback.

Canonical identity is `(norm_name, position_group)`, not `norm_name` — `J Sanders` is correctly
two people (Ja'Tavion, TE / Jason, K). Counted on the correct key, over 967 externally-sourced
probes that carry a real team:

**Seven canonical identities are claimed by two different real people:**

```
'A Brown'      (WR/NE,  proj 272, tv 37)  <- A.J. Brown       + Noah Brown
'A Mitchell'   (WR/NYJ, proj 141, tv  4)  <- Adonai Mitchell  + James Mitchell
'A Hutchinson' (DL/DET, proj  --, tv 22)  <- Aidan Hutchinson + Xavier Hutchinson
'B Robinson'   (RB/ATL, proj 346, tv 99)  <- Bijan Robinson   + Brian Robinson Jr.
'J Brooks'     (RB/CAR, proj 176, tv 20)  <- Jonathon Brooks  + Tahj Brooks
'J Daniels'    (QB/WAS, proj 334, tv 40)  <- CJ Daniels       + Jayden Daniels
'J Jefferson'  (WR/MIN, proj 292, tv 82)  <- Justin Jefferson + Van Jefferson
```

### The root cause is one unguarded path

Two independent tests on the returned row — position-family mismatch, and "the canonical name is
not a spelling of the probe" — give:

```
  position-family mismatch : 26   (key 20, fuzzy 6)
  different person         :  9   (key  0, fuzzy 9)
  BOTH -- unambiguous       :  6   (fuzzy 6)
```

**Every "different person" match comes from the fuzzy path. None comes from exact or key.** The
20 key-path position mismatches are all IDP *vocabulary* differences on the same person, same
team (`LB` vs `DL` for edge rushers) — benign taxonomy, not crossed wires.

The six unambiguous crossed wires, with a real team supplied:

```
CJ Daniels        (WR/LAR) -> 'J Daniels'    (QB/WAS)  projection 334  tv 40
James Mitchell    (TE/CAR) -> 'A Mitchell'   (WR/NYJ)  projection 141  tv  4
Jaret Patterson   (RB/LAC) -> 'R Patterson'  ( K/MIA)  projection  37
Xavier Hutchinson (WR/HOU) -> 'A Hutchinson' (DL/DET)                  tv 22
Bo Melton         (WR/GB ) -> 'M Melton'     (DB/ARI)
Skyy Moore        (WR/GB ) -> 'K Moore'      (DB/FA )
```

A practice-squad receiver takes a starting quarterback's 334-point projection. A running back
takes a **kicker's** projection. A tight end takes a receiver's — which also moves TE's own
replacement level.

The cause is exact and local, in `_find_match`'s final fallback:

```python
candidates = difflib.get_close_matches(norm_name, choices, n=3, cutoff=self.match_cutoff)  # 0.82
if position and "position" in table.columns:
    for cand in candidates:                    # best-effort preference only
        ...
return table[table["norm_name"] == candidates[0]].iloc[0]   # no position check, no team check
```

The key path **was** hardened with a team-mismatch rejection — the documented Bijan/Brian Robinson
fix. **That hardening was never applied to the fuzzy path**, and the fuzzy path is where every
demonstrated crossed wire lives. Short abbreviated names make it worse, not better:
`'cj daniels'` against `'j daniels'` clears a 0.82 cutoff easily.

A second, subtler limit: the key path's team guard is only as good as the team field it compares
against. `Brian Robinson Jr.` survives against `B Robinson` because the *external source's own*
team field says ATL. Live, Sleeper supplies current team data and that case would likely be
caught; the fuzzy-path cases cannot be caught by any team data, because nothing compares it.

### Blast radius

`build_available_pool` emits one pool row per **Sleeper player_id** and never dedupes on the
canonical row it matched. So N players resolving to one canonical row produce **N pool rows
carrying identical projections**. Measured on the probe set, keyed correctly on `(norm_name, position_group)`: **11
double-claimed canonical rows, 7 of them by genuinely different people, 6 of which carry a
projection — phantom priced rows at `WR 3, RB 2, QB 1`.** (An earlier count of 13 keyed on
`norm_name` alone and swept in benign suffix/ligature spellings of one person.)

A phantom row is a duplicate of a real player's points at that position. It therefore
**inflates that position's supply and pushes its replacement rank down into a denser part of the
curve** — the same anchor every VOR at that position is measured against. Identity contamination
does not stay local to one row; it moves a positional baseline.

## The parser: does one record mean one player?

`parse_draftsharks_pdf` reads each page as two independent blocks — a stat block
(`RK 1yr 3yr 3D`) and a name block (`Name` / `TEAMPOSn`) — and joins them:

```python
for idx, entry in enumerate(name_rows):
    if idx < len(stat_rows):
        rank, proj_1yr, proj_3yr, value_3d = stat_rows[idx]
```

**Positional index. No shared key, no length assertion, no rank-continuity check.** The
docstring's correctness argument is an assumption about PDF layout, and nothing verifies it.

Driven against the real function with synthetic page text:

| case | result |
|---|---|
| both blocks complete and ordered | **holds** — every record correct |
| more names than stats | **holds** — extras get null numerics (the one case the parser documents) |
| **one player's `TEAM/POS` line absent** | **violated silently.** `C Three` vanishes; `D Four` inherits his rank 3 / proj 260 / 3yr 800 / tv 80; stat row 4 is discarded. The output row is superficially perfect — valid name, valid team, valid position, contiguous rank, plausible numbers. |
| **a stray stat-shaped line interleaved** | **violated.** `C Three` gets rank 2026 / proj 1; `D Four` shifts to rank 3. |

The two failures differ in an important way: the stray-line case leaves a **detectable** artifact
(an out-of-range rank), the dropped-name case leaves **none**.

Scanning the committed baseline CSVs for the detectable signature:

```
 file                                        rows  rank gaps  dup ranks  out of order
 dynasty_ppr_rankings.csv                     250          0          0             0
 dynasty_ppr_superflex_rankings.csv           250          0          0             0
 te_premium_dynasty_rankings.csv              250          7          0             0
 ...  (K/DST/Sleeper files all 0 / 0 / 0)
```

**No duplicate ranks and no out-of-order ranks anywhere** — the stray-line signature is absent
from the committed baseline. `te_premium_dynasty_rankings.csv` carries 7 rank gaps over 250 rows,
which is worth explaining but is not that signature. (The two IDP files' rank column is not a
contiguous 1..N sequence, so this test does not apply to them.) **The dropped-name failure leaves
no trace, so the committed CSVs cannot be cleared of it from their own contents** — that would
require re-parsing the source PDFs.

`_normalize_columns` does raise on a file with no recognisable name column, so a structurally
wrong CSV is surfaced rather than absorbed. `_sniff_pdf_kind` chooses the parser from the PDF's
own text and **falls through to the Draft Sharks rankings parser for anything it does not
recognise** — a mis-sniff is silent.

## What the canonical record does and does not carry

```
canonical columns: name, norm_name, team, position, rank, projection, proj_3yr,
                   trade_value, source_file, source_date, _name_key, _pct, _pool_n
```

| dimension | present? |
|---|---|
| source file | **yes** — `source_file` |
| source date | **yes** — `source_date` |
| **source name / vendor** | **no** — inferable only from the filename |
| **ingest method** (API / PDF / CSV site-rip / screenshot / model-derived) | **no field at all** |
| **confidence** | **no** — assigned later, in `draft_room`, from `bpa_source` |
| **season** | **no column.** Nothing downstream can assert the projection is for this season |
| **scoring format** | **no column** on rankings — it lives in the *filename* (`_detect_rankings_format`). The trade-value chart does carry `source_scoring` / `source_league_type` |

So a screenshot-derived stand-in and an API-derived projection land in the **same `projection`
column with the same shape**, distinguishable only by knowing what each filename was made from.
The one place provenance does reach a decision is `draft_room`'s `CONFIDENCE_BY_SOURCE`, keyed on
`bpa_source` — which is inferred from *which column had a value*, not from how the value was
obtained.

### Genuine zero and unknown share a column

Four canonical rows carry `projection` exactly `0.0` — `J Milroe`, `A Richardson`, `R Pearsall`,
`C Brazzell II` — each alongside a large `proj_3yr` (330–475). The stat regex
`^(\d+) ([\d,]+) ([\d,]+) (\d+)$` matches a literal `0`, so these are **faithful extractions of a
printed zero, not coercions.** But downstream they are indistinguishable from any coerced zero,
and they are not inert: `projection = 0.0` produces a large negative VOR, which the clip flattens
to `bpa = 0.0` — "we are confident he is at replacement". A missing projection is *dropped* from
the pool; a zero is *priced at the floor*. Two very different epistemic states, one of which is
silently the more confident.

Worth recording: the external-ranking diagnostic in the previous appendix independently flagged
`R Pearsall` as a clip-driven disagreement. **The diagnostic found the row whose upstream value is
the hardest to interpret, without being told anything about upstream.**

### Ordinals become magnitudes at the composite

`_EXTERNAL_PERCENTILE_RULES` converts each source to a percentile within its own pool:

```
('dynastyprocess',  'players.csv')                 value_1qb   numeric magnitude
('keeptradecut',    'dynasty_superflex_halfppr.csv') value     numeric magnitude
('fantasypros',     'dynasty_ppr_rankings.csv')     rank       ORDINAL
('bot_research',    'findings')                     rank       ORDINAL
```

Percentiling is the right way to combine incompatible scales, and the module's own docstring says
so. But a percentile **of an ordinal** is a monotone re-expression of that ordinal, not a
magnitude: equal percentile steps are not equal value steps. It is then weight-averaged against
percentiles of true magnitudes. That is a real reconciliation step and it is documented — but the
epistemic type of each input is not carried through it, so the output cannot say how much of it
came from a magnitude and how much from a rank.

### Two projections, one player, different scales

```
sleeper_kicker_projections.csv   B Aubrey  proj 116  proj_3yr  --   tv 18  date 2026-08-25
dynasty_kicker_rankings.csv      B Aubrey  proj 177  proj_3yr 406   tv 18  date 2026-08-25
canonical winner                 B Aubrey  proj 116  proj_3yr NaN   tv 18  <- sleeper_kicker_projections.csv
```

Same player, same date, **two different season projections on two different scales** — one
league-scored from Sleeper stats, one a vendor dynasty number — landing in the same canonical
`projection` field. The winner is chosen by `(source_date, filename)`, and `load_all`'s own
comment states that the filename tiebreak "has NOT become a semantic precedence rule, it is still
an arbitrary string comparison."

The determinism defect here was found and fixed. **The semantic gap was not:** which of two
incompatible scales becomes a kicker's canonical production is currently decided alphabetically.
And because the Sleeper file carries no `proj_3yr`, that choice also silently removes the
kicker's entire dynasty-horizon signal.

## Which downstream conclusions remain trustworthy

- **All of #60–#76 stand.** Verified directly: the universe those probes used resolves 349/349 by
  the exact path with zero collisions and zero position mismatches. None of the identity findings
  above touch them.
- **The external-ranking diagnostic stands**, with one caveat now measurable: it is valid only
  where the source is not already inside the row's own valuation path, and it inherits the
  identity layer's own error rate when matching names into external tables.
- **Nothing here weakens the BPA findings.** If anything it strengthens the separation the
  doctrine asks for: a phantom pool row moves a *replacement level*, which moves *scarcity*, which
  today is inseparable from *production* inside BPA — so an upstream identity error currently
  arrives disguised as a change in player value.

## Invariants

69. The canonical player record's identity key is `(normalized name, position family)`. No
    consumer treats a normalized name alone as an identity.
70. Every identity resolution records the path that produced it, and a path without a rejection
    rule is not used for a valuation-bearing field.
71. A resolution whose returned row disagrees with the query on position family is a failure, not
    a best-effort match.
72. Resolution into the valuation pool is injective. Two distinct players never resolve to one
    canonical row, and a pool never contains two rows sourced from the same canonical row.
73. A parsed record is assembled by a key shared between its fields, or the parse declares itself
    unverified. A positional-index join asserts an ordering invariant and must check it.
74. A parse that cannot verify its own row alignment fails loudly. It never emits a
    superficially valid record.
75. The canonical record carries the ingest method and the vendor, not only the filename. A
    screenshot-derived value and an API-derived value are never indistinguishable in one column.
76. The canonical record carries the season and the scoring format it was produced under. No
    consumer infers either from a filename.
77. A genuine zero and an unknown are distinguishable in every canonical numeric field.
78. Two values on incompatible scales never occupy one canonical field. Where two sources both
    have an opinion, the precedence rule is semantic and stated — never a filename comparison.
79. An epistemic type (magnitude / ordinal / structural / model-derived) travels with the value
    through every reconciliation that consumes it.

---

# Appendix — the upstream boundary, completed

Finishes the map. Three demonstrated failure classes traced to full blast radius, the canonical
ingestion invariant stated, and the repair boundaries identified. **No upstream repair, no
downstream implementation, no normalization or coefficient work.**

## Corrections to the previous appendix

Three, all narrowing claims rather than widening them:

1. **`name_key` is `(first-initial, full remaining name)`, not `(first-initial, last-token)`.**
   The last-token form was the *old* key and was changed precisely because `A.J. Brown`
   (`aj brown`) and `Amon-Ra St. Brown` (`amonra st brown`) collided under it. The current key is
   materially less lossy than described.
2. **Phantom pool rows are 6, not 13.** The earlier count keyed on `norm_name` alone and swept in
   benign suffix/ligature spellings of one person. On the correct key `(norm_name,
   position_group)`: 11 double-claimed rows, 7 by genuinely different people, 6 carrying a
   projection.
3. **The positional-baseline impact is smaller than a first injection suggested.** That run
   duplicated top-of-curve players; the honest figures, using the actually-duplicated rows, are
   below.

## Class 1 — identity resolution, completed

### The three paths and their guards

| path | how it matches | guard on a wrong person | used when |
|---|---|---|---|
| **alias** | exact normalized name from `aliases.json` | manual, by definition correct | a hand-curated player |
| **exact** | `norm_name` equality | narrows on team, then position, when several rows tie | vendors exporting full names |
| **key** | `(first-initial, full remaining name)` | narrows on team, then position — **and rejects outright on a known team mismatch** (the documented Bijan/Brian Robinson fix) | bridging Draft Sharks' abbreviated names |
| **fuzzy** | `difflib.get_close_matches`, cutoff `0.82` | **best-effort position preference only; returns `candidates[0]` regardless, with no team check at all** | everything else |

### Why the fuzzy path can accept a cross-player match

Not an oversight in the matching itself — the rejection rule exists and works. It was added *to
the key path*, in a comment explaining exactly this hazard, and **the same reasoning was never
carried to the fallback below it**. The fuzzy branch tries to prefer a position-matching
candidate; when none of its three candidates matches, it returns the first anyway. Nothing on
that branch reads `team`.

Abbreviated canonical names make it fire more, not less: `'cj daniels'` against `'j daniels'` is
a short-string comparison with heavy overlap and clears `0.82` easily.

### The full at-risk surface, independent of any probe set

Computed over the canonical table against itself:

```
canonical rows                                                   764
name_key groups holding >1 canonical row                          19
  ... spanning >1 position family (position narrowing fixes)      19
  ... same family (position CANNOT disambiguate)                   0
rows with >=1 OTHER canonical row inside the 0.82 cutoff          258   (34%)
  ... with at least one neighbour in a different position family  182
```

Two things follow. **The key path's known ambiguity is fully repairable by position** — every one
of its 19 groups spans a position family, and `build_available_pool` does pass position. That
matches the measurement: zero "different person" matches came from the key path. **The fuzzy
path's neighbourhood is a third of the table**, and 182 rows have a cross-family neighbour
sitting inside the cutoff. Example: `C Dike` (WR) neighbours `c dicker` — a kicker.

### Every canonical identity with multiple real-person claims

```
'J Daniels'    (QB/WAS, proj 334, tv 40)  <- Jayden Daniels   + CJ Daniels
'J Jefferson'  (WR/MIN, proj 292, tv 82)  <- Justin Jefferson + Van Jefferson
'B Robinson'   (RB/ATL, proj 346, tv 99)  <- Bijan Robinson   + Brian Robinson Jr.
'A Brown'      (WR/NE,  proj 272, tv 37)  <- A.J. Brown       + Noah Brown
'J Brooks'     (RB/CAR, proj 176, tv 20)  <- Jonathon Brooks  + Tahj Brooks
'A Mitchell'   (WR/NYJ, proj 141, tv  4)  <- Adonai Mitchell  + James Mitchell
'A Hutchinson' (DL/DET, proj   —, tv 22)  <- Aidan Hutchinson + Xavier Hutchinson
```

### Which downstream records and positional baselines they can alter

`build_available_pool` emits one row per Sleeper `player_id` and never dedupes on the canonical
row it matched, so each of the six projection-carrying collisions becomes a **duplicate priced
pool row**: `WR 3, RB 2, QB 1`. They land high in their own curves — the colliding names are
famous ones — at the 40th to 97th percentile of their position.

Injecting exactly those rows, and bracketing against a top-of-curve upper bound and a
median-placed lower bound:

```
 pos   clean level    measured    upper bound   lower bound        top VOR, measured
  QB        324.0   325.0 (+1)    325.0 (+1)    325.0 (+1)      55.0 -> 54.0   (-2%)
  RB        178.0   182.0 (+4)    182.0 (+4)    178.0 (+0)     181.0 -> 177.0  (-2%)
  WR        210.0   218.0 (+8)    219.0 (+9)    210.0 (+0)     147.0 -> 139.0  (-5%)
  TE        187.0   187.0 (+0)    187.0 (+0)    187.0 (+0)     122.0 -> 122.0   (0%)
```

**+1 to +8 real points of baseline error, cutting top-of-position VOR by 2–5%.** Real and
directional, not catastrophic. The lower bound is exactly zero, which is the point: the size of
the error depends entirely on where in the curve the duplicate lands, and it is unbounded in
principle. A single duplicate of the best player at a thin position would move the anchor much
further than any of these did.

The mechanism matters more than the magnitude: **an identity error at one row produces an error
in a positional baseline — a league-level quantity that every player at that position is measured
against.** It does not stay local.

### Are ambiguous matches surfaced?

**No, at the producer.** `merge_player` returns `{"matched": bool, ...}` — no ambiguity flag, no
candidate count, no path label. Across **28 non-test call sites**, a silent first-candidate pick
is indistinguishable from an unambiguous exact hit.

**Yes, at exactly one consumer.** `app.py`'s trade calculator recomputes `name_key` itself to
count real candidates and marks a query `ambiguous` when several exist. Its own comment states
the producer's behaviour plainly: *"merge_player's own key-match silently picks the first
candidate when several players share a name_key and no position/team was given to disambiguate
(confirmed live: a same-keyed 'Jaylen Allen' resolved to 'Josh Allen's value instead of its
own)"* — and scopes the fix deliberately, *"without touching merge_player's own contract, which
plenty of other call sites already depend on staying as-is."*

Two things about that guard are now measurable:

- Its stated safety premise — *"fine for callers that always have a position in hand (the
  free-agent/roster tables)"* — **holds for the key path and fails for the fuzzy path.** Supplying
  position moved position mismatches from 89 to 88.
- Its comment describes the key as `(first-initial, last-token)`, which has not been true since
  the key changed. The one place documenting the workaround documents the old mechanism.

## Class 2 — parser integrity, completed

Every supported parser, by how it builds a record:

| parser | join strategy | row integrity | provenance kept | failure mode |
|---|---|---|---|---|
| `parse_draftsharks_pdf` | **two blocks, positional index** | **conditional** | file + reviewed date | **silent mis-assignment** |
| `parse_draftsharks_free_agents_pdf` | **two blocks, positional index** | **conditional** | file only (no date) | **silent mis-assignment** |
| `parse_draftsharks_trade_value_chart_pdf` | one line → one record | holds by construction | file, date, scoring, league type | unmatched line skipped |
| `parse_fantasypros_dynasty_pdf` | one line → one record | holds by construction | file, date, tier | unmatched line skipped |
| `parse_fantasypros_bestball_pdf` | one line → one record | holds by construction | file, date, tier | unmatched line skipped |
| `parse_fantasypros_idp_pdf` | one line → one record | holds by construction | file, date, tier | unmatched line skipped |
| `parse_espn_idp_pdf` | one line → one record | holds by construction | file, date | unmatched line skipped |
| `parse_keeptradecut_pdf` | one line → one record, **plus a rank-continuity check** | **holds and is verified** | file, date, source format | truncates; empty table raises |
| CSV / JSON (`load_projection_file`) | the file's own rows | holds by construction | file, date | raises with no name column |

**Six of the eight PDF parsers, and the CSV/JSON path, satisfy the invariant by construction** —
every field in a record comes from one source line, so a shifted or missing line drops a row, it
does not corrupt one. The two Draft Sharks two-block parsers do not.

### The one parser that verifies itself

`parse_keeptradecut_pdf` carries `expected_rank`, requires each row's value blob to end with the
expected rank string, and skips anything that does not fit. A missed row therefore desynchronises
the counter and every later line stops matching — the table **truncates** rather than
mis-assigning. And when `start_rank` cannot be seeded from the page's own range text it defaults
to 1, so a page not starting at rank 1 matches nothing, yields an empty frame, and
`load_projection_file` raises `No table found`. **It fails loudly and safely.** That is the shape
the other two need, and it already exists in this codebase.

### The two that do not

Both build `stat_rows` and `name_rows` independently and join with
`for idx, entry in enumerate(name_rows): stat_rows[idx]` — no shared key, no length assertion, no
rank-continuity check. Demonstrated against the real function:

| case | detectable? | outcome |
|---|---|---|
| both blocks complete and ordered | — | correct |
| more names than stats | yes | extras get null numerics — the one case documented |
| **one player's `TEAM/POS` line absent** | **no** | every later row on the page inherits the previous player's stats; the dropped player vanishes; the surplus stat row is discarded. Output is superficially perfect. |
| stray stat-shaped line interleaved | yes | one row gets an out-of-range rank (`2026`); later rows shift |

`_sniff_pdf_kind` picks the parser from the PDF's own text and **falls through to
`parse_draftsharks_pdf` for anything unrecognised** — a mis-sniff runs the wrong parser silently.

Scanning the committed baseline for the detectable signature: **0 duplicate ranks and 0
out-of-order ranks in every file.** The undetectable failure leaves no trace, so the CSVs cannot
be cleared of it from their own contents.

## Class 3 — canonical schema and provenance, completed

### Which source produced each field

```
       field   non-null   contributing files (top 4)
  projection        328   te_premium_dynasty(231), sleeper_kicker(37), sleeper_dst(32), ff_dynasty(17)
    proj_3yr        259   te_premium_dynasty(231), ff_dynasty(17), dyn_te_prem_sf(10), dyn_sf(1)
 trade_value        361   te_premium_dynasty(231), superflex_idp(76), ff_dynasty(17), sleeper_dst(13)
        rank        404   te_premium_dynasty(231), superflex_idp(76), sleeper_kicker(37), sleeper_dst(32)
        team        760   superflex_idp(415), te_premium_dynasty(242), sleeper_kicker(33), sleeper_dst(32)
    position        764   superflex_idp(415), te_premium_dynasty(242), sleeper_kicker(37), sleeper_dst(32)
```

This map is derivable only because every field on a row comes from **the same winning row**.
There is no per-field provenance: `source_file` describes the row, not the field.

### The mechanism: reconciliation is row replacement, not field merge

```python
combined.assign(_dedup_key=...).drop_duplicates(subset="_dedup_key", keep="last")
```

The winning **row** replaces the loser wholesale. There is no per-field precedence anywhere. Two
consequences, both measured across the baseline files:

```
players appearing in more than one baseline file                      706
fields SILENTLY DROPPED (winner null, a loser had a value)
    proj_3yr 22 · trade_value 10 · rank 10 · projection 9             51
fields IN CONFLICT (two files disagree, one wins, nothing recorded)
    rank 309 · trade_value 304 · projection 244 · proj_3yr 227      1084
```

**1084 field-level disagreements are resolved every load, and not one of them is recorded.** The
merge "succeeded" in all 1084 cases.

### The kicker conflict, fully explained

Both halves of the question have concrete answers.

**Why filename ordering decides.** `load_all` sorts source entries by `(source_date, filename)`.
All four committed K/DST files declare the same `source_date` (`2026-08-25`), so the filename is
the only remaining tiebreak — and `load_all`'s own comment says so: it *"has NOT become a
semantic precedence rule, it is still an arbitrary string comparison."* That comment is accurate,
and it documents a gap rather than a design. The determinism defect it was written for was fixed;
the semantic gap it names was not.

**Why the loser's extra data disappears.** Because the merge replaces rows, not fields.
`sleeper_kicker_projections.csv` sorts after `dynasty_kicker_rankings.csv`, so its row wins
entire — including its *absent* `proj_3yr`.

The consequence is positional, not per-player:

```
 pos   rows   has proj_3yr   share   has projection
  QB     40             38     95%              38
  RB     79             72     91%              72
  WR    109            104     95%             104
  TE     52             45     87%              45
   K     37              0      0%              37
 DEF     32              0      0%              32
  LB     91              0      0%               0     (source never had it)
  DL    171              0      0%               0     (source never had it)
  DB    153              0      0%               0     (source never had it)
```

`time_horizon_adj` — the engine's only dynasty-horizon signal — is gated on `proj_3yr`. **Every
kicker and every defense therefore receives `time_horizon_adj = 0.0` by construction in a dynasty
league, while 87–95% of offensive players receive a real one.** Aubrey lost a 406, Boswell 312,
Dicker 336, Little 285, McLaughlin 348.

No positional rule anywhere in `draft_room` produces that. It is a **systematic positional bias
created entirely at the reconciliation layer** — the K/DST defect class again, one layer further
upstream than the audit that first found it. (For IDP the zero is not a loss: those sources never
carried the column.)

### What can silently become a plausible value

| input condition | current outcome | exposed? |
|---|---|---|
| two sources disagree on a field | one wins by row order | **no** — 1084 cases per load |
| winner lacks a field the loser had | field becomes null | **no** — 51 cases |
| a printed `0` projection | stored as `0.0`, priced at the clip floor | **no** — indistinguishable from a coerced zero |
| a missing projection | row dropped from the pool | yes, by absence |
| a stale row | kept; only whole-table freshness is graded | partially |
| an ambiguous name match | first candidate returned | **no**, except in the trade calculator |
| a mis-sniffed PDF | parsed by the Draft Sharks parser | **no** |
| a CSV with no name column | `ValueError` | **yes** |
| a KTC page that cannot seed its rank | empty frame → `ValueError` | **yes** |

## The canonical ingestion invariant

> **One canonical player record must represent one real player, one intended season/context, and
> an internally consistent set of fields with traceable provenance.**

Reconciliation "succeeding" must mean the record is semantically coherent — not that the merge
completed. Against that standard, each clause and what currently violates it:

| clause | status | violated by |
|---|---|---|
| **one real player** | **not guaranteed** | the fuzzy path's unguarded return; 7 identities with two real claimants |
| **one intended season / context** | **not representable** | no `season` and no `scoring_format` column; format inferred from a filename |
| **internally consistent fields** | **not guaranteed** | row replacement mixes a winner's fields with a loser's absences; 1084 unrecorded conflicts |
| **traceable provenance** | **partial** | `source_file` + `source_date` only; no vendor, ingest method, confidence, or transformation history, and provenance is per-row, not per-field |

**Heterogeneous sources being combined is the intended architecture and is not the problem.** The
problem is that the system cannot currently say *what* it combined or *why* — so a merge that
mixes a league-scored Sleeper projection with a vendor dynasty row is indistinguishable, in the
output, from one that did not.

## Repair boundaries

Which layer owns which fix. Named, not designed, and not implemented.

| # | boundary | owner | scope |
|---|---|---|---|
| R1 | the fuzzy fallback must reject rather than guess | `_find_match` | apply the key path's existing rejection rule to the fallback; return `None` rather than `candidates[0]` |
| R2 | ambiguity must be a return value, not a caller's re-derivation | `merge_player` | carry the path and the candidate count; the trade calculator's local guard then becomes a read, not a re-implementation |
| R3 | pool construction must be injective | `build_available_pool` | one canonical row may back at most one pool row |
| R4 | two-block parsers must verify their own alignment | the two Draft Sharks PDF parsers | the rank-continuity check `parse_keeptradecut_pdf` already implements |
| R5 | an unrecognised PDF must not fall through to a parser | `_sniff_pdf_kind` | refuse rather than default |
| R6 | reconciliation must merge fields, not replace rows, under a stated precedence | `_dedup_by_name_and_position` / `load_all` | and record every conflict it resolves |
| R7 | the canonical schema must carry season, scoring format, vendor, ingest method, and per-field provenance | the schema itself | plus a representation that separates a genuine zero from an unknown |

R1–R3 are the identity boundary, R4–R5 the parse boundary, R6–R7 the schema boundary. **R6 and R7
are prerequisites for the downstream BPA work**, because the horizon term BPA is supposed to carry
does not currently exist for two positions — and that is an upstream fact, not a normalization
choice.

## Upstream and downstream, connected without conflation

> **Upstream integrity determines whether the player-level evidence entering valuation can be
> trusted. Downstream architecture determines whether trusted evidence is transformed and consumed
> correctly. Both boundaries must hold.**

They are independent, and this investigation kept them so:

- **The downstream findings #60–#76 were reproduced against correctly resolved identities** —
  349/349 exact, zero collisions, zero position mismatches — so none of the defects above explains
  them away, and none of them may be used to rewrite those findings.
- **The upstream defects are not downstream symptoms.** A crossed wire, a shifted parse row, and a
  row-replacement field loss are all upstream of every quantity BPA is built from.
- **They meet at exactly one place, and it is worth naming**: an upstream identity error alters a
  *positional replacement level*, which today is inseparable from *production* inside BPA. So an
  upstream error currently arrives downstream **disguised as a change in player value** — which is
  precisely the confusion the BPA contract exists to prevent. Fixing either boundary alone leaves
  that disguise in place.

## Invariants

80. A resolution path without a rejection rule never returns a match for a valuation-bearing
    field. Guessing and declining are different outcomes and only one is acceptable.
81. Ambiguity is a property of the resolution and is returned with it. A consumer never
    re-derives it, and never has to.
82. A parser that joins fields from more than one source line verifies the join against a key or
    a sequence invariant it can check, and fails loudly when it cannot.
83. An unrecognised input format is refused. No parser is a default.
84. Reconciliation merges fields under a stated semantic precedence and records every conflict it
    resolves. A merge that silently discards a value has not succeeded.
85. Precedence between two sources is never decided by a filename.
86. Every canonical field carries the source, ingest method, and transformation that produced
    *that field* — not only the row.
87. The canonical record states the season and scoring format it represents. Neither is inferred
    from a filename.
88. A field that is absent for a whole position because of a merge rule is a declared fact about
    that position, not a silent zero in a downstream adjustment.

---

# Appendix — the dynasty horizon contract

Answers #81. Establishes what `proj_3yr` and the horizon layer are supposed to be, what actually
reaches them, what depends on them, and what the minimum trustworthy input is. **No repair.**

## The two "horizons" are different quantities with the same word

| name | question | horizon | unit | category |
|---|---|---|---|---|
| **production horizon** — `proj_3yr`, `time_horizon_adj` | how much will he produce over the coming years? | multi-season | projected points → percentile → bpa-scale nudge | **player property** |
| **substitution horizon** — `horizon_replacement`, `horizon_floor`, `waiting_cost` | what is still available when the draft ends? | end of this draft | real points | **context** |

They share a word and nothing else. Recording it here because the collision is live in the
codebase and either name read for the other is a category error under the doctrine.

## The intended contract, as the code itself states it

Three deliberate design statements, all already written and all correct:

1. **Absence must not become a signal.** `_proj3yr_pct` defaults to a neutral `50.0`, but *"a
   'neutral' 50.0 standing in on one side of a difference is not neutral — against a genuinely
   low season percentile it reads as 'this player's future is far better than his present,'
   manufacturing a growth signal from missing data."* Neutrality is therefore expressed on the
   **adjustment**, via `_has_3yr`, not on an input.
2. **Some positions legitimately have no horizon dimension.** *"Draft Sharks publishes DST only as
   a redraft table, and a team defense has no career arc to project in the first place"* — so a
   defense *"must neither be penalised for the absence nor rewarded by it."* The parser makes the
   same statement independently: *"inventing one would feed a fabricated number straight into
   dynasty scoring."*
3. **The guard is load-bearing.** Measured before it existed: mean `growth` of **24.22 for K and
   20.11 for DEF** against **0.57–1.63** for positions carrying both numbers — and because `bpa`
   collapses board-wide once demand is exhausted, `growth` becomes the sole ranking term, so
   *"rounds 16 and 17 of a 12x20 draft went 100% K/DEF, and the 22-point kicker sitting last in
   the remaining pool ranked first overall."*

**That is the origin of this entire audit.** The guard was the right fix for the symptom. What
follows is what the guard was compensating for.

## One claim in that comment is now false

The code asserts, as justification: *"Provably a no-op for every source committed at the time of
this change: zero rows in the real baseline carry a points projection WITHOUT a `proj_3yr`
alongside it."*

That was true when written. **It is false now: 37 kickers and 32 defenses carry a points
projection with no `proj_3yr`.** The invariant was invalidated later, by a data change, and
nothing detected it. A dated correctness claim in a comment is not a test.

## What actually reaches the horizon layer

Counted as **unique players**, not row-instances (a first pass compared source rows to canonical
players, which counts dedup as loss):

```
 pos  players  w/3yr@src  canon  canon w/3yr  lost   diagnosis
  QB       41         40     40           38     1   partial reconciliation loss
  RB       81         74     79           72     0   intact
  WR      110        105    109          104     1   partial reconciliation loss
  TE       52         48     52           45     3   partial reconciliation loss
   K       37         13     37            0    13   TOTAL RECONCILIATION LOSS
 DEF       32          0     32            0     0   SOURCE GAP
  LB       93          0     91            0     0   SOURCE GAP
  DL      172          0    171            0     0   SOURCE GAP
  DB      156          0    153            0     0   SOURCE GAP
```

**The question in #81 has a three-way answer, not one answer.**

- **QB/RB/WR/TE — intact.** Between 0 and 3 players lost each. #80 barely touches offense.
- **K — #80, but only for part of it.** All 13 kickers that carry `proj_3yr` at source lose it to
  row-replacement, so the reconciliation defect fully explains the canonical zero. **But only 13
  of 37 kickers have horizon data in any committed file.** A perfect field-merge would take K from
  0% to **35%**, not to the 87–95% offense enjoys. **#80 is necessary and not sufficient for K:
  there is also a real source-coverage gap of 24 players.**
- **DEF and IDP — not #80 at all.** Zero values exist in any source; for IDP the column is absent
  entirely. Reconciliation has nothing to lose. **And for DEF this is the documented intended
  behaviour**, not a defect: the engine is supposed to have no horizon opinion about a team
  defense.

## Everything downstream of the horizon fields

| consumer | reads | effect |
|---|---|---|
| `pool["_has_3yr"]` | `proj_3yr` notna | the gate both consumers use |
| `pool["_proj3yr_pct"]` | `proj_3yr` | pool-wide percentile |
| `time_horizon_adj` | `_proj3yr_pct − _season_proj_pct`, dynasty only | `± TIME_HORIZON_CLAMP` on the bpa scale → **`universal_value`** → all 79 of its sites |
| `risk_adj` dynasty scaling | `time_horizon_adj` | a positive trajectory buys up to 70% relief on an injury penalty |
| `upside_score` → `growth` | `_proj3yr_pct − _season_proj_pct`, floored at 0 | → **`final_score` directly** in upside mode, and **the sole ranking term** once `bpa` collapses |
| `merge_player` whitelist / roster tables / UI | `proj_3yr` | display |

Module counts: `draft_room` 22 sites, `data_merger` 7, `app` 5, `sleeper_client` 4. Two scoring
consumers, one third-order dependent, one display path.

## Is `time_horizon_adj` a player trajectory or a positional scale artifact?

Restoring K's `proj_3yr` in memory and recomputing under the current basis:

```
 pos    n  mean tha   median 3yr/season ratio   ratio rank
  QB   36      1.30                      2.90            3
  RB   72     -3.65                      2.44            5
  WR  102      0.21                      2.99            2
  TE   45     -1.04                      2.81            4
   K   13     -3.29                      3.19            1
```

Variance decomposition over 268 rows: **position explains 29%, within-position 71%.** So the
quantity does carry real player-level signal — a first reading that called it primarily a
positional offset was too strong.

But the position-level component is not small against a `±10` clamp, and **it does not track
trajectory**: if it did, mean `tha` would follow the median 3yr/season ratio. **Pearson r = +0.26**
across positions — essentially uncorrelated. Kickers have the **highest** median ratio of any
position (3.19) and receive the second most **negative** mean adjustment (−3.29). Every one of the
13 restored kickers lands negative, from −0.35 to −5.73.

The cause is that `_percentile_map` ranks **the whole pool**. A pool-wide percentile encodes how a
position's scale sits against every other position, so the difference of two of them conflates
*"his future is better than his present"* with *"his position's multi-year scale sits differently
against the pool than its season scale does."* Under the doctrine that is a **context variable
wearing a player property's name.**

## The naive repair would create a new defect

`proj_3yr` for kickers lives in `dynasty_kicker_rankings.csv`. The season projection that **wins**
the merge comes from `sleeper_kicker_projections.csv`. They are not the same quantity — one is a
vendor dynasty-table projection, the other is scored from Sleeper stats under this league's own
rules. A field-level merge would pair them:

```
kicker            vendor season  vendor 3yr  in-file ratio  merged season  merged ratio  distortion
B Aubrey                    177         406           2.29            116          3.50       1.53x
C Dicker                    170         336           1.98            106          3.17       1.60x
J Elliott                   143         340           2.38             90          3.78       1.59x
...                                                                         median      1.43x
```

**A field merge alone would inflate every kicker's apparent trajectory by a median 1.43×** — an
internally inconsistent record produced *by the repair*, not by the defect. This is the canonical
ingestion invariant's third clause failing in the opposite direction from #80.

**Repair boundary R6 is therefore insufficient as stated.** Merging fields instead of rows is
necessary and, on its own, unsafe: a horizon field must travel with the season field it was
computed against, or carry its own basis label so the ratio is never taken across bases.

## The canonical horizon contract

**Definition.** `proj_3yr` is a **player property**: projected production over the multi-season
horizon, on the same measurement basis as that row's season projection.

**Domain.** Defined only where a source publishes a multi-year figure on a basis matching the
row's season figure. Positions with no multi-year dimension are **outside the domain**, not
missing within it.

**Three states, not two.** The schema currently has `value` and `null`, and `null` carries two
irreconcilable meanings:

| state | meaning | correct treatment |
|---|---|---|
| **present** | a real multi-year figure on a matching basis | compute the adjustment |
| **not applicable** | this position has no career arc (DEF today; IDP as sourced) | **declared**; no adjustment, and never counted as a gap |
| **unknown** | the player has one and we do not have it (24 kickers; 5 offensive players) | no adjustment, **and reported as missing coverage** |

Today `_has_3yr` collapses *not applicable* and *unknown* into one `False`. Both correctly get a
zero adjustment, so no current output is wrong — but the engine cannot say whether a position is
structurally horizon-free or merely unmeasured, which is exactly the distinction needed to decide
whether restoring data is even possible.

**Exhaustion / absence.** Absence never becomes a signal. The `_has_3yr` gate is correct and must
survive any repair.

**Authorized consumers.** `time_horizon_adj`, `upside_score`'s `growth`, and — transitively —
`risk_adj`'s dynasty scaling. No other quantity reads it.

**Interaction.** It is added, via `time_horizon_adj`, to `bpa` — a quantity whose magnitude
collapses across a draft (#76). The horizon term is stable while what it modifies is not, which is
why the nudge reaches 100% of `universal_value` by round 15.

## The minimum trustworthy input for the dynasty horizon layer

Four conditions. The first is data; the other three are semantic and no amount of data satisfies
them.

1. **A multi-year figure for the player** — currently absent for 24 of 37 kickers, all of DEF, and
   all of IDP.
2. **On the same measurement basis as that row's season figure** — otherwise the ratio is taken
   across two scales, at a measured 1.43× distortion for kickers.
3. **A percentile basis that isolates trajectory from positional scale** — otherwise 29% of the
   signal is a scale artifact that points the wrong way for the position with the strongest actual
   trajectory.
4. **An explicit "no horizon dimension" declaration**, distinct from "unknown" — so DEF's zero is
   readable as intended and K's zero is readable as a gap.

**Conditions 2 and 3 are prerequisites for condition 1 to be worth satisfying.** Restoring the
data without them would give kickers a systematically negative dynasty adjustment built on a
1.43×-inflated ratio — worse than the current neutral zero.

## Invariants

89. `proj_3yr` and the substitution-horizon fields are different quantities. Neither name is ever
    read for the other.
90. A horizon figure is only combined with a season figure computed on the same measurement
    basis. A ratio or difference across bases is not defined.
91. "Not applicable" and "unknown" are distinct states of a horizon field. A position with no
    multi-year dimension declares that fact; it does not report a gap.
92. A percentile feeding a trajectory comparison is computed over a population in which the
    comparison is meaningful. A pool-wide percentile across positions with different scales is
    not that population.
93. A correctness claim asserted in a comment ("provably a no-op for every committed source") is
    expressed as a test or it is not relied upon.
94. Horizon coverage is reported per position as a first-class fact, so a position at zero is
    visibly either out of domain or unmeasured.

---

# Appendix — the BPA unit, repaired

The downstream repair phase opened here because every other downstream quantity is denominated
in this one. `universal_value = bpa + time_horizon_adj + risk_adj`;
`team_acquisition_value = universal_value + need_bonus + eligibility_bonus`. If `bpa` has no
fixed unit, none of the additive constants in those two lines has a fixed meaning either.

## What the code did

```python
reference = vor[vor > 0].max()
bpa = (vor / reference * 100).clip(0, 100)
```

Two separate defects, sharing one line.

**The reference was a property of one other row.** `max(VOR)` is whoever happens to be the best
remaining player. He leaves the pool when someone drafts him, and every other player's `bpa`
rescales. Measured across a real 12×20 board, the reference moved 97.0 → 72.0 → 27.0 → 17.0 →
16.0 → 13.0 → 9.0 → 2.0, and a decomposition of every player whose own projection never changed
attributed **94.6% of all `bpa` movement to the reference and 5.4% to the player**. Isaiah
Likely, one fixed projection of 186 points, read 0.0 → 0.0 → 0.0 → 0.0 → 50.0 → 61.5 → 88.9 →
0.0 across rounds 1–12. Nothing about him changed.

**The clip destroyed the below-replacement measurement.** `clip(0, 100)` mapped every negative
VOR onto the same 0.0. Measured, 95%+ of all zeros on a mid-draft board were clipped negatives,
sharing a value with the genuine boundary case (a player who *is* the replacement level) and
with the degenerate anchor case. At round 4 the priced field carried 141 distinguishable states;
by round 12 it carried 20.

## Why the fix removes a coefficient rather than choosing a better one

Four invariants already established in this document jointly determine the answer, so no new
number had to be invented:

* **62** — draft state contextualizes `bpa`; it never redefines its unit.
* **63** — the reference is never a property of a single other row.
* **64** — a below-baseline measurement is preserved as a signed quantity.
* **65** — bounded presentation is a rendering decision, not a property of the measurement.

Invariant 63 rules out *every* candidate reference of the form `max(...)`, `top-N mean`, or
`percentile`, because each is still a property of whichever rows are in the pool. Invariant 65
removes the only motivation for having a reference at all. #76's consumer survey settled the
rest: **zero consumers require `bpa ≤ 100`; five require a stable unit.** One answer survives.

```python
def _scale_vor_to_bpa(vor: pd.Series) -> pd.Series:
    return vor.astype(float)
```

`bpa` **is** VOR: real projected points above this position's replacement level. Absence stays
absent — a row with no anchor returns `NaN`, never `0.0`.

## What the repair does and does not change

`VOR = production_margin + scarcity_movement` remains exact, and **`scarcity_movement` is
supposed to move.** A player's `bpa` still changes when his position's replacement level falls,
because that is the scarcity term reporting real information about the draft. What may never
move is the ruler. The two forms of that contract are pinned separately:

* per-player — a player's entire `bpa` change is accounted for by his anchor's change, to the
  cent (`test_bpa_unit.py`);
* per-pair — two players at the same position share an anchor, so it cancels, and the gap
  between them is their gap in real projected points at **every** board state
  (`test_downstream_contracts.py`).

Measured on the repaired round-0 board: 333 priced rows, 185 distinct values, spanning −324.0 to
+181.0, with exactly 9 rows at 0.0 — and every one of those 9 verified to be a player sitting
exactly at his position's replacement level. Zero has been returned to meaning one thing.

## The consequence this exposes, which is not fixed here

Every absolute constant that reads a `bpa` difference was calibrated against the old rescaled
unit. `NEAR_TIE_BAND = 2.0` was worth **1.94 real points at round 1 and 0.02 by round 13** — a
97× drift. It is now worth exactly 2.0 real points at every board state, which is a strict gain
in well-definedness and *not* a claim that 2.0 is the right number.

The kicker fixture is where this surfaced first: the measured K1-to-K2 step is 3.0 real points
against a 2.0 band, while every other adjacent gap in the field sits at or under it. That is a
genuine disagreement between a constant and the evidence, and it is **finding #56**, not
something the BPA repair may settle. No constant was retuned in this change. Every one of
`NEED_BONUS_MAX`, `ELIGIBILITY_BONUS_MAX`, `NEAR_TIE_BAND`, `NECESSITY_STANDOUT_REFERENCE_GAP`,
`TIME_HORIZON_SLOPE`, `TIME_HORIZON_CLAMP` and `RISK_ADJ` is numerically unchanged.

## What the five suite failures turned out to be

The full-suite gate failed five tests. Every one was a **test defect**, and four of the five were
tests that had been passing *vacuously* behind the clip:

1. `assertEqual(bpa.iloc[0], 100.0)` inside a test about absence — pinning the rescale as a side
   effect. Now asserts pass-through of both measured rows.
2. An eligibility fixture selecting its candidate by a magic `25.0` gap written in the old unit;
   in real points that lands at WR #3, too good for the fixture's own saturation step to work.
   Now selects by the property the scenario requires.
3. A risk_adj gate reading `bpa < -4.6`, unreachable under a `[0,100]` clip — the guarded block
   had never executed. Now states "thin" as `|bpa|`, asserts the formula unconditionally, and
   **skips loudly** when the real pool contains no subject, rather than passing silently.
4. A superflex QB test computing a *within-QB* gap and asserting a *whole-board* ordering — two
   registers, conflated. It survived only because the clip flattened the rookie QB class so the
   gate never opened. The best rookie RB sits 256 points above his replacement and the best
   rookie QB sits exactly *at* his, so the RB leading that board is the engine working.
5. The kicker near-tie test above.

## Invariants

95. `bpa` is VOR in real projected points. It is not rescaled, not referenced against another
    row, and not clipped.
96. Two players at the same position differ in `bpa` by exactly their difference in projected
    points, at every board state.
97. A `bpa` of exactly `0.0` means the player is at his position's replacement level. It is not
    a floor, a default, or a stand-in for absence.
98. A constant expressed as an absolute difference in `bpa` has a fixed meaning in real points.
    Where the right number is unknown, that is recorded as an open decision, not absorbed by a
    rescale.
99. A test that cannot reach its subject reports that fact. Silence is not a pass.

---

# Appendix — the survival layer's ordinal register

## The two registers that share one integer

`_build_opponent_boards` numbered every row on an opponent's board `1..n` and handed that
mapping to two consumers. Both read the integer through `RANK_TAKE_PROBABILITY`, a table whose
keys mean *"the consensus best player available"*, *"the second best"*, and so on:

* `estimate_survival` — `_take_probability(rank, is_run)` per intervening pick;
* `expected_positional_forfeit` — sums the same table over every row inside
  `FORFEIT_OPPONENT_BOARD_DEPTH`.

For a **priced** row that reading is correct: the ordinal came from `team_acquisition_value`.
For an **unpriced** row — one whose position has no replacement level left to measure against,
so the board carries absence — the ordinal came from the deterministic tiebreak that keeps the
board stable. It is not a valuation, and it may not be read as one.

## Measurement

Round 16 of a real 12×20 board carries 63 unpriced rows of 141. Three unpriced targets — a WR at
board ordinal **79**, a WR at **110**, and the very last row on the board, a K at **141 of 141** —
all returned the identical survival probability of **0.641**. All three fell past the table's
five keys onto `RANK_TAKE_PROBABILITY_FLOOR`.

The number was not wrong. The claim to have measured it was: the ordinal contributed nothing,
and nothing in the output said so.

## The defect is live, not latent

`pick_synthesis.narrow_candidates` adds the best remaining player at **every position the board
covers**, unconditionally and by design — that addition exists to stop a scarce position's best
player from being invisible to the strategic layer. So a position with no priced rows left hands
an unpriced candidate straight to `pick_analysis` → `estimate_survival`. Measured: at round 16 at
least one position is entirely unpriced.

The stronger hazard — an unpriced row reaching the top five, where the tiebreak would be read as
`0.55` — was checked across rounds 10–23 and is **not reachable**: at least 30 rows stay priced
at every round. It was reachable before the BPA repair, when the clip left far fewer rows priced.

## What the repair does

`rank_by_id` is built over priced rows only, and the board declares `unpriced_ids` separately.
`estimate_survival` then distinguishes three cases that had been two:

1. **No entry at all** — not in this team's usable-position pool. They cannot take him; no risk.
   Unchanged.
2. **On their board, unpriced** — they *can* take him, but there is no valuation, so there is no
   ordinal to read and no evidence of elevated risk. He gets the floor, and the row is labelled
   `evidenced: False` with `rank_on_their_board: None`.
3. **Priced** — unchanged.

The same change fixes the forfeit consumer without touching it: unpriced rows can no longer
occupy the top-`FORFEIT_OPPONENT_BOARD_DEPTH` window at all.

**No number moves.** The floor is exactly what these rows already received, by a tiebreak ordinal
missing the table. What changes is that the result now follows from a stated rule and carries a
label, so no consumer can present it as a measurement.

## What is deliberately left open

Whether an unpriced-but-draftable player should instead count as **zero** risk is a product
decision. There is no evidence in this repository to settle it, and choosing an answer would be
inventing behaviour. It is recorded, not guessed.

## Invariants

100. An ordinal is only read through a table of valuations if it *is* a valuation ordinal. A
     list that mixes priced and unpriced rows does not produce one.
101. A board declares which of its rows it could price. A consumer that cannot value a player
     says so rather than reading an ordinal that means something else.
102. A probability derived without evidence is labelled as such at the point it is produced, not
     left for a presentation layer to infer.
103. "Not in the pool", "in the pool but unvalued", and "valued" are three distinct states. No
     two of them share a code path.

## The third site: the pace prior's denominator

`_pace_based_take_probability` narrows *"some QB gets taken"* down to *"THIS QB gets taken"* by
dividing the position's pace deficit by the target's rank among remaining players at his
position — computed by sorting `board["by_id"]` on `universal_value`.

An unpriced row's `universal_value` is `NaN`, and every comparison against `NaN` is `False`, so
`list.sort` silently produces a **non-total** order the moment one is present. The result is not
a rank at all: which row lands where depends on the order the rows arrived in.

Demonstrated on a constructed board — three priced QBs among eight unpriced ones — the best QB's
returned probability moved from **1.0 to 0.111**, a 9× swing, purely from reversing the dict's
insertion order.

**Reachability, measured rather than assumed.** The prior returns `None` past 48 picks (the
first four rounds), and the real board's first unpriced row appears in round 15. The two windows
do not overlap, so on today's data this is latent, not live. That is precisely why the test
fixture is **constructed**: a test that can only observe its subject on data that does not exist
would report a pass while proving nothing. The denominator now counts priced peers only, and an
unpriced target gets the function's own `None` — the caller's documented "fall back to the
rank-based estimate" path, not a new behaviour.

## A note on the marker that was hiding a broken test

`KnownGapSurvivalAnswersOnAnUnpricedBoard` had carried `@unittest.expectedFailure` since the
contract phase. Its body called `_build_opponent_boards` with an argument the signature does not
take and passed a list of tuples where a flat list of roster_ids belongs; it raised `TypeError`
on every run. A suite reports that as the expected failure it was told to expect — so the marker
read as *"this contract is not met yet"* for a test that had never once reached its subject.

An `expectedFailure` asserts that a *specific* thing fails. It cannot distinguish that from the
test being broken. Where a known gap is marked, the marked test must be shown to fail **for its
stated reason** before the marker is trusted.

104. An `expectedFailure` is only trusted once the marked test has been observed failing for the
     reason it names. A marker over a test that errors is a marker over nothing.

---

# Appendix — the demand domain boundary was float noise

## What was measured

Auto-drafting a full 12×20 mock through `simulate_opponent_picks` (each pick takes that
roster's own top board row):

| | before | after |
|---|---|---|
| auto-picks made | 240 | 240 |
| decided by an exact tie at the top | 16 (6.7%) | 16 (6.7%) |
| **made from an unpriced top row — no valuation at all** | **102 (42.5%)** | **86 (35.8%)** |
| first round with nothing priced anywhere on the board | **12** | 14 |

From round 12 on, `replacement_levels` returned an **empty dict**. Not "a few positions
omitted" — nothing at all. The board could price no player, so the opponent AI drafted the back
half of the draft on the deterministic `player_id` tiebreak.

## Why

`_remaining_demand_rank` returns `None` below one whole starting slot, and that rule is right:
a demand of 0.7 is not a demand for one more player. It was written as the bare comparison
`demand < 1`.

`remaining_starter_demand` accumulates flex **shares** — 1/3 and 2/3 of a slot per team — so a
demand that is mathematically exactly one whole slot arrives one ULP below it:

```
rd  TE demand (repr)             <1?  rank
 10 2.333333333333333          False     2
 11 0.9999999999999998          True  None
 12 0.9999999999999998          True  None
 ...
```

TE genuinely had one unfilled starting slot league-wide, and by round 11 every other position's
demand is genuinely 0 — so a single position falling out of the domain took the entire board's
valuation with it, and it stayed out for every round after.

**A correction to how that was first written.** The pre-repair trace above shows the state at
rounds 11 through 20 and was described as "ten straight rounds", which reads as ten independent
triggers. It is one trigger with a persistent consequence: once TE fell out at round 11 nothing
on the board could be priced, so the auto-draft's own picks stopped being value-driven and the
demand simply never recovered. Re-running the same auto-draft **after** the repair reproduces
the state exactly **once**, at round 11 — because TE is priced from there on, the draft makes
different picks, and TE's demand then falls below one slot legitimately. Both traces are correct
about their own draft; they are not the same draft.

## The tolerance is derived, not tuned

Remaining demand is a sum of integers and `k/num_teams` flex shares, so two genuinely different
demands differ by at least `1/num_teams` — 0.083 in a 12-team league, no smaller than
`1/32 = 0.031` in the largest league anyone fields. Accumulated double-precision error across a
few dozen such terms is on the order of `1e-15`. `DEMAND_WHOLE_SLOT_TOLERANCE = 1e-9` sits about
six orders of magnitude below the smallest real distinction and six above the largest plausible
error: **every value in that gap gives identical answers**, which is what makes it a derivation
rather than a constant to tune.

## How general is the trigger? Measured, and narrower than first assumed

Three sweeps, in increasing fidelity:

1. **Synthetic round-robin picks**, 24 configurations (6 roster shapes × 8/10/12/14 teams),
   4536 demand readings. 100 readings sat just under a whole number — and **all 100 round to 2
   or more**, so none of them would ever have reached the `< 1` gate. **Zero dangerous
   readings.** Draining every position evenly never lands a demand on exactly one slot.
2. **Real board, best-first pick order**, 5 roster shapes × 10/12 teams. **Zero** dangerous
   readings — including in the exact shape where the defect was originally measured.
3. **Real auto-draft** (`simulate_opponent_picks`, every pick off that roster's own board),
   4 roster shapes at 12 teams. **One** dangerous reading: `1QB 1flex`, TE, round 11. The other
   three shapes — `1QB 2flex`, `superflex`, `te premium` — produced none.

So the trigger is **not** universal across league shapes, and it is not reproducible from pick
composition alone: it needs a real value-driven draft, in a roster shape whose flex-share
arithmetic happens to land a position on exactly one whole slot. The standard 12-team,
single-flex dynasty startup — the app's own default mock — is one such shape.

That narrows the *frequency* claim and not the *severity* one: where it fires it removes every
price on the board for the rest of the draft. The repair is unconditional and costs nothing in
the shapes where the state never arises.

## What was deliberately not touched

The `int(round(demand))` on the following line. Its rounding boundary is a separate question
with its own behaviour; this repair changes only the domain gate, and
`test_the_rounding_above_the_boundary_is_unchanged` pins that it stayed byte-identical.

## What this repair does NOT fix, and why it stops here

86 auto-picks (rounds 14–20) still come from an unpriced board — and there, demand really is
zero at every position, because every starting slot in the league is genuinely filled. The board
reporting absence is the contract working: it has no starter-demand replacement level to measure
bench depth against, and saying so is more honest than inventing one.

**What the engine should order players by once no starter demand exists is an open product
decision** (#45/#69), and it is not settled here:

* raw `projected_points` is defined for every row but is not comparable across positions — a
  QB's 340 against a kicker's 116 — so ordering on it would make the AI take quarterbacks with
  bench picks;
* `trade_value` is a market quantity from a different measurement basis, not this engine's own;
* refusing to order at all leaves the mock draft unable to complete.

None of those follows from evidence in this repository. Recorded, not guessed.

## Invariants

105. A domain boundary compared against a value assembled from fractional shares carries a
     tolerance derived from that value's own granularity. A bare `<` against an integer
     boundary is a defect wherever the quantity is not itself an integer.
106. One position falling out of the valuation domain may not silently remove the whole board's
     ability to price. Coverage collapse is reported, not inferred from an empty result.

---

# Appendix — absence had to survive the consumers, and did not

## The crash

`compute_draft_board` normalizes an unpriced row's `bpa`, `universal_value` and `final_score`
to `None` (`_records_with_normalized_nan`). That is the right contract, chosen deliberately: a
row whose position has no replacement level has no value, and writing `0.0` there would rank it
exactly where *"worth nothing"* ranks, which is a claim rather than an absence.

**The contract stopped at the board.** Every consumer downstream then did arithmetic or ordering
on the field directly. Measured on a real 12-team dynasty startup — unpriced rows first appear at
round 15, and from that round on `pick_synthesis.build_snapshot`, the call the Draft Room makes
to build the Prytaneum's pick debate, raised:

```
TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'
  pick_synthesis.build_snapshot -> draft_strategy.pick_analysis line 558
  curve.sort(reverse=True)
```

Not a wrong number — a hard crash at the application's own entry point, for the last quarter of
every 20-round draft. `position_curves` was built from **every** row on the board, so the crash
did not even require an unpriced *candidate*; one unpriced row anywhere was enough.

## Consumer survey, at real board states

| consumer | rd 8 | rd 13 | rd 14 | rd 16 | rd 18 |
|---|---|---|---|---|---|
| `pick_analysis` | ok | ok | ok | **TypeError** | **TypeError** |
| `decision_regime` | ok | ok | ok | **TypeError** | **TypeError** |
| `near_tie_flags` | ok | ok | ok | **TypeError** | **TypeError** |
| `expected_value_of_waiting` | ok | ok | ok | **TypeError** | **TypeError** |
| `build_snapshot` | ok | ok | ok | **TypeError** | **TypeError** |
| `narrow_candidates` | ok | ok | ok | ok | ok |
| `simulate_opponent_picks` | ok | ok | ok | ok | ok |

Unpriced rows at round 16: **63 of 141**.

## The rule, which is not invented here

All three halves already had precedent in this codebase before the repair:

1. **Exclude.** A row with no value is left out of a computation defined over values — a curve,
   a maximum, a margin, a gap distribution. Being excluded is not the same as scoring low.
2. **Propagate.** A quantity derived from an absent input is itself absent.
   `expected_value_of_waiting` already returned `None` for an absent survival; the repair applies
   the same rule to its other operand.
3. **Order last.** An ordering places absent rows last, deterministically, and never compares
   them as numbers — exactly what `pick_synthesis._board_order` already did for the board itself.

## Eleven sites repaired

`draft_strategy`: `_position_curves` (extracted, excludes unpriced, drops empty positions),
`_opportunity_cost` (absent when either operand is), the denial/rival-premium loop (skips an
opponent whose own board cannot price him), `_opportunity_cost_order` (absent last, `player_id`
tiebreak).
`pick_synthesis`: `near_tie_flags`, `decision_regime`, `compute_pick_necessity`,
`decision_path_flags`, `expected_value_of_waiting`, `detect_positional_cliff`.
`pick_debate._best_alternative`, `draft_board_ui` ALL-view ordering.

`decision_path_flags` was **found by the new tests, not by the survey** — it is reached only
through `build_snapshot`, which the survey could not call until its own signature error was
fixed. Worth recording: the consumer survey was necessary and not sufficient.

## The one place a neutral number is used

`compute_pick_necessity`'s standout component, for a candidate who is himself unpriced, is
`0.0`. That is not a number substituted for absence: the function already assigns exactly `0.0`
for an absent survival, an absent cliff and an absent rival premium, and its own docstring argues
the standout floor is neutral — *"not the single best option on the board right now is neutral,
not itself evidence of low urgency."* His survival, cliff and run components remain real
evidence. What was fixed alongside it is the opposite error: a **sole** unpriced candidate used
to collect the full `NECESSITY_STANDOUT_WEIGHT` under the *"no alternative exists at all"*
branch — treating "nothing measurable" as "he is irreplaceable."

## Invariants

107. A field that can be absent is absent for every consumer, not just its producer. A contract
     that holds only at the layer that writes it is not a contract.
108. A quantity derived from an absent input is absent. It is never zero, and never a partial
     sum presented as a whole one.
109. A row with no value is excluded from computations over values. Exclusion is not a low score.
110. Every ordering over a possibly-absent field places absence last by an explicit key, never by
     comparing it. The result does not depend on input order.
111. A consumer survey is necessary and not sufficient: the entry point must be exercised, since
     a consumer reachable only through it will not appear in a survey of its parts.

---

# Appendix — the two open decisions, quantified

Neither of these is settled here. Both are product judgments; what follows is the evidence a
decision needs, measured on the repaired engine against a real 12-team dynasty startup.

## Decision A (#56) — the absolute constants now have fixed meanings for the first time

`bpa` is real projected points at every board state, so `NEAR_TIE_BAND`,
`NECESSITY_STANDOUT_REFERENCE_GAP` and `NEED_BONUS_MAX` mean the same thing in round 1 and
round 16. They did not before: the band was worth 1.94 real points at round 1 and 0.02 by round
13. Three separate questions fall out, and they do **not** have the same answer.

### A1. `NEAR_TIE_BAND = 2.0` — discriminating per position, meaningless board-wide

Adjacent-gap medians in each position's top 12, opening board:

| position | n | median adjacent gap | max | pairs within 2.0 |
|---|---|---|---|---|
| QB | 12 | 2.36 | 38.95 | 5 / 11 |
| RB | 12 | 5.97 | 28.60 | 3 / 11 |
| WR | 12 | 8.49 | 22.92 | 3 / 11 |
| TE | 12 | 5.74 | 30.39 | 1 / 11 |
| **K** | 12 | **1.00** | 3.00 | **10 / 11** |
| **DEF** | 12 | **1.00** | 4.00 | **10 / 11** |

At the position level the band does exactly what it is for: 1–5 of 11 skill-position pairs are
ties, against 10 of 11 at K and DEF. **That is a working discriminator and an argument for
leaving 2.0 alone.**

Board-wide it is the opposite: the median adjacent gap across all priced rows is 0.34–1.33, so
**80–88% of every adjacent pair on the board falls inside the band** at every round sampled.
Any use of this constant across positions rather than within one calls almost everything a tie.

### A2. `NECESSITY_STANDOUT_REFERENCE_GAP = 15.0` — the "decisive" regime is unreachable

Measured leader-vs-second margin on the narrowed candidate list, and the regime that follows:

| round | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 |
|---|---|---|---|---|---|---|---|---|---|
| margin | 12.69 | 0.14 | 3.07 | 0.00 | 0.00 | 2.39 | 0.01 | 0.35 | 2.88 |
| regime | contested | contested | contested | contested | contested | contested | contested | contested | contested |

**`decision_regime` returned "contested" at all nine sampled states. "decisive" was never
produced.** The same constant also gates `decision_path_flags`' `cliff_protection`.

This is stated carefully, because it would be easy to overclaim. Reconstructing the pre-repair
unit from the same boards, the old margins were 6.87 / 0.76 / **18.71** / 0.00 / 0.00 / 13.47 /
0.01 — "decisive" was reachable, but at 1 of 7 rounds and **erratically**, because the ruler
itself was moving underneath the threshold. The honest summary is not "the repair broke this":
it is that **15.0 was never calibrated against a stable unit, and the repair is what makes the
question answerable.** On the fixed unit the margins are consistent real-point gaps and do not
reach it.

### A3. `NEED_BONUS_MAX = 12.0` — context can reorder almost any adjacent pair

97–98% of adjacent priced pairs sit within 12.0 of each other at every round through 14
(90.9% at round 16). A maximal need bonus is therefore sufficient to reorder nearly any
neighbouring pair on the board. That is not automatically wrong — neighbours are *supposed* to
be close — but it is the number to look at when asking how much authority roster fit holds.

**What is needed:** a decision on each of A1/A2/A3 separately. They are one constant family with
three different verdicts available, and no evidence in this repository picks the numbers.

## Decision B (#45/#69) — ordering when no starter demand exists anywhere

Auto-drafting a full 12×20 mock: **rounds 14–20 price nothing at all — 84 picks, 35% of the
draft.** Every starting slot in the league is genuinely filled by then, so the board correctly
reports absence rather than inventing a replacement level.

What each candidate basis actually selects, first 12 rows off that board:

| basis | top-12 positions |
|---|---|
| `player_id` tiebreak — **today** | RB 10, QB 2 |
| `projected_points` | **QB 12** |
| `trade_value` | WR 9, QB 3 |

`projected_points` is disqualified by measurement, not by argument: it is not comparable across
positions, and ordering on it hands **every one of the first twelve bench picks to a
quarterback.** `trade_value` produces a plausible spread — but it is a dynasty *market* quantity
on a different measurement basis than the engine's own projected points, so adopting it means
the back third of the board is ordered by a different question than the front two-thirds. That
is a real semantic break, and it should be chosen knowingly rather than absorbed.

### B2. It is not only about bench ordering — whole positions vanish from the board

Re-measuring #72 after D1 and D3 turned up the sharper version of this decision. At round 16 of
a real 12-team startup the remaining starter demand is:

```
DEF 1.0   QB 2.0   RB 3.0   TE 4.667   WR 0.667
```

WR sits at two-thirds of a flex slot — genuinely below one whole slot, so this is the domain
rule working exactly as designed, **not** the float defect D3 repaired. The consequence:

| the engine's top-ranked players | | | the best players it will not rank at all | | |
|---|---|---|---|---|---|
| A Barner | TE | **153 pts** | D Samuel | WR | **174 pts** |
| G Helm | TE | 150 | M Lemon | WR | 169 |
| T Ferguson | TE | 140 | A Pierce | WR | 166 |
| M Mayer | TE | 112 | M Golden | WR | 164 |
| E Stowers | TE | 82 | R Shaheed | WR | 159 |

**The board's number-one recommendation projects 153 points while an unranked WR projects 174**,
and seven more unranked WRs match or beat the top-ranked TE. Both would occupy the same bench
slot. Under strict VOR semantics this is correct — with two-thirds of a WR starter slot left
league-wide, a WR's surplus over a *starter* replacement is undefined — but as a recommendation
it is a strong claim made silently.

This also settles #72 in its repaired form: **the register boundary is a positional override of
a kind `need_bonus` never achieves.** Measured across rounds 0–18, need_bonus changes the top-12
positional composition at only two rounds, and by one player each time. The register removes an
entire position — the deepest one on the board — for the last five rounds, totally and without
saying so.

**What is needed:** one decision, now with two parts. (a) Bench-depth ordering uses `trade_value`
(accepting the basis change, ideally labelled), or the engine declines to order and says so, or a
bench-specific value is defined. (b) Whether a position dropping out of the starter-demand domain
should remove it from the board's ranking entirely, as it does today, or whether the board should
surface those rows explicitly as "no starter demand — bench value only". Note that the crash class
this appendix's neighbour documents is fixed either way: nothing raises on these rows any more.

---

# Appendix — the adjacent sweep: what was checked and found sound

Four defects came out of the downstream phase (D1–D4). This records the sweep around them, so
"nothing else found" is a result rather than an absence of looking. Every line below is a check
that was run, with what it returned.

## Order dependence — clean, proved not assumed

The repository has a documented history here (the `players_db` iteration-order bug, which
reordered 37 of ~500 rows). Re-swept: the full board signature — `bpa`, `universal_value`,
`final_score`, `need_bonus`, `eligibility_bonus`, `time_horizon_adj` for every row — was
recomputed against **three shuffled `players_db` orderings and a shuffled picks list**, at rounds
0, 4, 10, 16 and 19, and compared element by element. Identical at every state. `build_snapshot`
candidates and their `pick_necessity` match too. **No order dependence remains.**

## Empty-sequence and division crashes — clean

Every `max()`/`min()` over a possibly-empty sequence in the valuation and strategy modules is
guarded (`if demand_source else 1`, `if picks else 1`, `elif not others`, `if not priced`).
Every division by a variable is guarded (`values[demand - 1] <= 0: continue`, `if total <= 0`,
`if typical_gap > 0`, `if not rates`). Checked, nothing open.

## The float-boundary class — one instance, and it is D3

`positional_bench_appetite`'s `demand < 1` looked like a second instance of D3 and is not:
its `demand = round(num_teams * slot_counts.get(position, 0))` is an **integer** before the
comparison, so no accumulated fraction reaches it. `len(values) < 2 * demand` is integer too.
`_remaining_demand_rank` was the only site where a flex-share-accumulated float met a whole-number
boundary, and `replacement_ranks` inherits the repair because it reuses that helper rather than
restating the rule.

## `waiting_cost` is now commensurable with `bpa` — a consequence worth naming

`waiting_cost = projected_points - horizon_floor` was always in real season points and was never
rescaled. Before D1 that put it on a **different unit** from `bpa` (0–100), which means the
staged work to wire it into the decision layer (#48/#57/#71) had a unit obstacle nobody had
named. After D1 both are real projected points. That work is now expressible; it was not before.

## `upside_score`'s growth term — checked, and sound

`upside_score` is `bpa + UPSIDE_GROWTH_WEIGHT * growth`, where `growth` is a **percentile**
difference and `bpa` is now real points. That is the same additive-unit shape as
`universal_value`, so it was measured rather than assumed:

| round | mean \|bpa\| | mean growth term | growth share | rows reordered vs. pure-`bpa` order | max move |
|---|---|---|---|---|---|
| 0 | 65.34 | 1.68 | 2.5% | 133 | 17 |
| 8 | 63.53 | 2.78 | 4.2% | 141 | 24 |
| 14 | 73.43 | 3.72 | 4.8% | 106 | 17 |
| 16 | 67.04 | 4.02 | 5.7% | 30 | 8 |
| 17 | 68.32 | 4.18 | 5.8% | 26 | 6 |

The growth term's share of *magnitude* is small, but it still does real ordering work at every
round, and the top 12 differs from a pure-`bpa` ordering at all of them — because the median
adjacent gap (0.34–1.33 points) is smaller than the growth term itself. A small share of a score
is not the same as a small influence on its order. **`UPSIDE_GROWTH_WEIGHT` is not on the
open-decisions list.**

## D1 independently killed a previously-documented pathology

`upside_score`'s own comment records a measured failure: *"because bpa collapses to 0.00
board-wide once positional demand is exhausted, growth becomes the SOLE ranking term at that
point, and the artifact took over the board outright: rounds 16 and 17 of a 12x20 draft went
100% K/DEF, and the 22-point kicker sitting last in the remaining pool ranked first overall."*

That collapse was the clip. Measured now, the upside board's top 12 at rounds 16 and 17 is
`{TE 6, RB 3, QB 3}` and `{TE 6, QB 2, RB 4}` — **zero K, zero DEF** — and mean |bpa| is 67–68
rather than 0. The guard added at the time remains and is still right; the underlying mechanism
it was compensating for is gone. This was not a target of D1 and is an independent confirmation
of it.

## Invariants

112. A term added to a score is checked against that score's unit, not against its own history.
     "Small share of magnitude" and "small influence on order" are different claims and are
     measured separately.
113. Where a sweep finds nothing, the sweep itself is recorded. An unwritten check cannot be
     distinguished later from one that was never run.

---

# Appendix — mutation-testing the repairs themselves

Four defects were fixed and roughly 60 tests were added to guard them. A test that passes proves
nothing about whether it would fail if the fix were undone, and this audit has already found
several tests in this repository that passed while never observing their subject. So the
repairs were mutation-tested: each fix was deliberately reverted in the source, the tests meant
to guard it were run, and a mutation that **survived** would mean those tests do not actually
observe the behaviour.

Harness in `scratchpad/mutate.py` — patch, run, restore in a `finally`, and verify at the end
that every source file is byte-identical to where it started (it was).

| mutation | result |
|---|---|
| D1 re-introduce the 0–100 clip | killed |
| D1 re-introduce a max-of-pool rescale | killed |
| D2 rank unpriced rows again | killed |
| D2 drop the unevidenced label | killed |
| D2 let the pace prior rank unpriced peers | killed |
| D3 remove the boundary tolerance | killed |
| D3 widen the tolerance to swallow a real 0.67 | killed |
| D4 put unpriced rows back on the value curve | killed |
| D4 make `opportunity_cost` zero instead of absent | killed |
| D4 order absence first instead of last | killed |
| D4 let absence into the near-tie band | killed |
| D4 let an unpriced sole candidate claim the standout weight | killed |
| D4 count unpriced rows in `decision_regime`'s field | killed |
| D4 give an unpriced target a cliff reading | **survived** |

**13 of 14 killed.** The survivor was then adjudicated rather than assumed to be a test gap,
because a surviving mutant has two possible meanings and only one of them is a problem.

`detect_positional_cliff`'s `if row.get("bpa") is None: return None` is **provably redundant**
given the filter beneath it: an unpriced target is excluded from `same_position`, so `idx` comes
back `None` and the function returns `None` by that route regardless. Verified by running both
variants over every row of real boards at rounds 0, 16 and 18 — of **112 unpriced rows, zero**
would reach the function body without the early return. That is an *equivalent mutant*, not an
unobserved behaviour, and no test could distinguish the two because there is nothing to
distinguish.

The guard is kept, and the redundancy is now recorded in the code itself — otherwise a later
reader could remove the filter believing the guard covers it, which is the one way this pairing
could actually break.

## Invariants

114. A fix is guarded by a test that has been observed to fail when the fix is reverted. Passing
     is not evidence of guarding.
115. A surviving mutant is adjudicated before it is treated as a gap: an equivalent mutant means
     redundant code, and the redundancy is recorded where the code is, not only in the audit.

---

# Appendix — how the vacuity audit was run, so it can be run again

Three of this phase's findings were tests that passed without ever observing their subject. That
is not a class you find by reading; it needs a tool. This records the tool, because the finding
is only durable if the check is repeatable.

`scratchpad/vacuity.py` installs a `sys.settrace` line tracer **scoped to the test files
themselves** (the global tracer returns `None` for every frame outside them, so production code
runs untraced and the overhead stays tolerable), runs the whole suite through
`unittest.TextTestRunner`, and then diffs the set of executed lines against every line
containing `self.assert…`, `self.fail(`, `self.skipTest(` or `assertRaises`. Anything in the
second set and not the first is an assertion that never ran.

**First run: 1127 tests, 27 assertion lines never executed.** Eleven were `skipTest` calls that
correctly never fired — a guard that never triggers is good news, and the tool reports it so the
distinction is made deliberately rather than by eye. The rest were real, and are fixed:

| file | what was wrong |
|---|---|
| `test_downstream_contracts` | `AbsenceIsNotAValueTests` filtered for unpriced rows on the **opening** board, which prices all 333. Three assertions had never run once. |
| `test_cdme_denial_semantics_audit` | `pick_order` was a single round with the user picking first, so `intervening` was `[]` and every audited field was `0.0` / `None` / `1.0`. A whole fidelity class comparing nothing to nothing. |
| `test_pick_synthesis` | `for d in diffs:` over a list that is empty by construction — asserted nothing but "no exception". |
| `test_identity_boundary` | Both assertions sat under conditions that are always false now that all nine cross-person cases are declined. |
| `test_draft_strategy` | The `rival_premium_take_probability is None` branch was never taken. |

One performance test (`test_full_board_stays_fast_…`) can fail **under the tracer** and pass
without it, which is expected: `settrace` inflates wall-clock. Its result is ignored in this
harness rather than being read as a regression.

## Second run, after the fixes: 1158 tests, 19 never-executed lines — and all 19 accounted for

The point of re-running is that a residual count is only meaningful if every entry in it is
explained. It is:

| category | n | why it is correct |
|---|---|---|
| `skipTest` calls that never fire | 10 | the fixture always had its subject; a guard that never triggers is the good outcome |
| `self.fail(...)` guards | 2 | they exist to fire only on a defect (`test_downstream_contracts` 285, `test_parser_integrity` 131) |
| conditional assertions kept beside a stronger sibling | 5 | `test_identity_boundary` asserts both the contract ("if it resolves, not to the other person") and the measured state ("nothing resolves"); `test_pick_synthesis` keeps the per-row loop beneath an explicit `assertEqual(diffs, [])` |
| assertion behind a `skipTest` that does fire | 1 | `test_draft_room` 1114 — the fixture limitation is reported, which is the whole point |
| genuinely dead | **0** | the last one (`test_draft_strategy` 299) now asserts that its own branch is unreachable in that fixture, and points at where the case is really covered |

**Zero unexplained never-executed assertions remain.** The number will not go to zero and should
not: `skipTest` and `self.fail` lines are supposed to sit unexecuted. What matters is that each
one has a reason recorded, so a future run can be diffed against this table rather than
re-litigated.

## Invariants

116. Test vacuity is checked with a tool, not by reading. An assertion that never executes is
     invisible to a green suite and to a careful reviewer alike.
117. A fixture is required to reach the state its tests describe, and that reachability is
     asserted in the test file — not left to be true by luck of the board state or pick order.

---

# Appendix — the constants contract (A / #56)

`bpa` now has a stable real-point unit, so for the first time these constants mean the same
thing in round 1 and round 16. That made it possible to ask what they are each *for*. The answer
is not one contract with four numbers.

## Three constants, nine roles, six quantities

| constant | role | quantity it is compared against |
|---|---|---|
| `NEAR_TIE_BAND` 2.0 | threshold | TAV adjacent gap (`near_tie_flags`) |
| | threshold | UV difference to the leader (`pure_value`) |
| | threshold (aliased as `CLIFF_MIN_MATERIAL_GAP`) | bpa gap **within one position** |
| `NEED_BONUS_MAX` 12.0 | **cap** | `need_bonus` itself |
| | **divisor** | `rival_premium` (necessity's denial term) |
| | threshold | `TAV − UV` (`context_elevated`) |
| `NECESSITY_STANDOUT_REFERENCE_GAP` 15.0 | **divisor** | leader-vs-field TAV margin (necessity's standout term) |
| | threshold | leader−second TAV margin (`decision_regime`) |
| | threshold | `positional_forfeit` (`cliff_protection`) |

Measured distributions, on the repaired unit across eight real board states:

| quantity | n | p50 | p90 | p99 | max | rule fires |
|---|---|---|---|---|---|---|
| TAV adjacent gap | 2061 | 0.54 | 2.88 | 21.67 | 56.85 | 15.7% |
| UV adjacent gap | 2061 | 0.54 | 2.88 | 20.54 | 56.85 | 16.1% |
| bpa gap within a position | 2020 | **2.00** | 10.00 | 34.00 | 71.00 | 58.5% |
| `TAV − UV` | 2070 | 4.00 | 8.33 | 8.33 | **8.33** | **0.0%** |
| leader−second TAV margin | 9 | 0.35 | 4.99 | 11.92 | **12.69** | **0.0%** |
| `positional_forfeit` | 72 | **54.81** | 121.89 | 154.94 | 154.94 | **73.6%** |
| `rival_premium` | 72 | 4.33 | 8.33 | 8.33 | 8.33 | 0.0% |

**The same literal 15.0 gates two quantities whose medians differ by 150×** — one it can never
reach, one it clears three times out of four.

## The root pattern: a bound is not a threshold

Two of the three constants were chosen *correctly*, for a role that is the opposite of a
threshold:

* `NECESSITY_STANDOUT_REFERENCE_GAP` is a **normalizer's reference**. Its own comment states it
  was deliberately placed *"above the largest adjacent gap ever observed (10.6) … since full
  standout credit should demand something rare."* Being hard to reach is the **point**.
* `NEED_BONUS_MAX` is a **cap**: exactly `3 × NEED_BONUS_PER_DEDICATED_SLOT`, the most a roster
  slot can ever contribute. A cap is an upper bound by construction.

Both were then reused as **firing thresholds**, where unreachability is fatal rather than
intended. This is a category error, not a badly chosen number:

> **A bound says "never more than this". A threshold says "meaningful above this."
> A value chosen as one is not automatically valid as the other.**

`cliff_protection` is the mirror image: a threshold sitting far *below* its quantity's median,
so the flag is on for three of every four candidates and carries almost no information.

## What was repaired, and what was not

**Repaired — `decision_regime`'s margin condition.** Its margin half is not a separate concept:
`near_tie_flags` marks the leader exactly when a second candidate sits within `NEAR_TIE_BAND`,
so *"the leader is clear of the field"* and *"the leader is not in a tie group"* are the same
predicate. Measured across 24 real board-state/roster pairs, the two agreed on **every one**.
`decision_regime` now asks `near_tie_flags` rather than re-deriving a margin against a constant
borrowed from a different concept. This introduces no new number — it points an existing rule at
the concept the module already names, and removes a duplicate definition that could drift.

Effect: `decisive` went from **0 of 24** real board states to **8 of 24**. One of the function's
two states now exists. Because `near_tie_with_leader` is already shown in the UI and handed to
the debate layer, the regime and the badge can also no longer disagree.

**Checked and left alone — `CLIFF_MIN_MATERIAL_GAP`.** It is `= NEAR_TIE_BAND`, and gates a
different population (within-position bpa gaps, p50 2.00 against the board-wide 0.54). That
looks like the same coupling defect and is not: the existing comment already says it is *"kept
under its own name because the two express genuinely different concepts … and could legitimately
diverge later."* The concept split is already made explicitly. No change.

**Not repaired — two thresholds that are still bounds.** Choosing what *should* fire them is a
product decision and nothing in this repository determines it. Both are now pinned by tests that
assert the measured state, so the numbers here cannot silently rot:

1. `context_elevated` (`TAV − UV >= NEED_BONUS_MAX`). Unreachable. Max observed `TAV − UV` is
   **8.33** on the standard board and **8.67** across **1020 rows** of a real IDP league with
   genuine multi-eligibility; a deliberately constructed triple-eligible candidate on a
   saturated roster reached only **3.55**. `NEED_BONUS_MAX` is three dedicated slots' worth and
   this roster shape has at most two.
2. `cliff_protection` (`positional_forfeit >= NECESSITY_STANDOUT_REFERENCE_GAP`). Fires 73.6% of
   the time against a quantity whose median is 3.6× the threshold.

## Two corrections to the constants' own documented basis

Recorded rather than quietly fixed, per the standing rule that severity and frequency are
separate claims and a wrong claim is worth keeping visible:

1. `NEAR_TIE_BAND`'s comment states its basis as *"top-40 adjacent tav gaps … median 1.23 / p75
   2.26 / p90 3.53 … 72% measured"* inside the band. Re-measured on the repaired unit, on the
   superflex shape the comment names: **median 1.69, p75 3.05, p90 5.42, and 51% inside** (49%
   on the standard shape). The band is still a working discriminator — arguably a better one at
   ~50% than at 72% — but the stated justification no longer describes the data.
2. `NECESSITY_STANDOUT_REFERENCE_GAP`'s comment justifies 15.0 as sitting *"above the largest
   adjacent gap ever observed (10.6)"*. That reasons about the wrong quantity: the standout term
   divides a **leader-vs-field margin**, not an arbitrary adjacent gap. The largest adjacent gap
   now observed is **18.32** — above 15.0 — while the largest leader−second margin is **12.69**.
   The number still sits above the quantity it actually divides; the reasoning given for it did
   not describe that quantity even when it was written.

## Invariants

118. A constant is declared for one role — bound, divisor, or threshold — and reused in another
     role only after the reuse is measured against that role's own quantity.
119. Every firing threshold is reachable in both directions on real data. A rule that can never
     fire, or that always fires, is asserted as such deliberately or it is a defect.
120. Two rules that are provably the same predicate are expressed once. Where one already has a
     name in the module, the other adopts it rather than restating it against a second constant.
121. A constant's documented basis is a measurement, and a measurement can go stale. When the
     unit beneath it changes, the basis is re-measured and any divergence is recorded, not
     silently inherited.

---

# Appendix — B: the roster-state layer already exists

The hypothesis was that roster-state information might be a **missing contextual layer** in the
decision path, with a state machine like *under-covered → covered → depth +1 → depth +2 →
saturated*. The instruction attached to it was to find out what the architecture already
represents before adding anything, and not to duplicate a concept merely because it is not
obvious from the final ranking.

**It already exists, it reaches the decision layer, and it is doing the job.** This appendix is
the evidence for declining to build a second one.

## Inventory: where each hypothesised concept already lives

| concept | represented in | reaches the draft decision layer? |
|---|---|---|
| starting-slot coverage at the position | `remaining_starter_demand` (league-wide), `need_bonus` (per-roster), `lineup_readiness` (per-team) | **yes**, via `need_bonus` and `replacement_levels` |
| practical simultaneous-start capacity | `lineup_optimizer.slots_from_roster_positions` / `optimize_lineup` | **yes**, as the reachable-slot count `need_bonus` is keyed to; `optimize_lineup` itself only offline |
| positional roster depth (peer-relative) | `depth_ratings.depth_label` — Strong/Average/Weak/None vs the league | **no** — Trade Calculator, League Depth Map, Matchup only |
| how far above coverage the roster is | `need_bonus` decay; `bench_surplus_value` | **partly** — see the saturation gap below |
| remaining bench capacity | `remaining_draft_capacity`, `estimated_bench_demand`, `positional_bench_appetite` | **yes**, through remaining demand |
| remaining draft rounds / picks | `remaining_draft_capacity`, `LATE_ROUND_THRESHOLD`, necessity's `round_num` | **yes** |
| handcuff relationships | **nowhere — zero occurrences in the codebase** | no |
| upside | `growth_signal`, `upside_score`, `time_horizon_adj` | **yes** |
| positional flexibility | `eligibility_bonus`, `lineup_optimizer` | **yes** |
| overall roster imbalance | `roster_diagnostics.structural_holes` / `thin_positions` | **no** — post-draft harness only |

## `need_bonus` IS the ladder, and it is monotone

Measured on real boards, need_bonus by how many of a position the roster already holds:

| position | reachable slots | 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|---|
| QB | 1 | 4.00 | 0.00 | 0.00 | 0.00 | | |
| RB | 3 | **8.33** | 4.33 | 0.33 | **0.00** | 0.00 | 0.00 |
| WR | 3 | **8.33** | 4.33 | 0.33 | **0.00** | 0.00 | 0.00 |
| TE | 2 | 4.33 | 0.33 | 0.00 | 0.00 | 0.00 | |

**Zero monotonicity violations across 288 same-slot-count position pairs.** The step sizes come
from the league's own `roster_positions` — a position reaching three slots starts higher than
one reaching two — not from a table of invented per-position numbers.

That is the hypothesised state machine, already implemented as a continuous decay: *under-covered
→ partially covered → covered → silent*.

## And it is already deciding real ties

Across 84 real board-state/roster pairs:

* **76%** have the leader inside a tie group of 2+ — so a tiebreak layer would engage in three
  of every four picks. "It's only a tiebreak" is not a safety argument here.
* In tie groups where roster coverage differed, `need_bonus` favoured the **least-covered**
  candidate in **19 of 19** — no counterexamples. **Challenged and re-verified**: the strict
  recount (no-information groups separated out, agreement required to be strict) returns 19 of
  19 with zero no-information groups. The claim stands; the self-review that questioned it did
  not. See *"Correction to a correction: the '19 of 19' tie-group tally stands"*.
* It **changed the winner** versus pure `universal_value` in **6 of 52** tie groups, and **fell
  short** of doing so in 10 of 52. Neither inert nor dominant.

The worked case that looks most like the motivating example, and what actually happened:

| roster 10, round 4 | coverage | universal_value | need_bonus | TAV |
|---|---|---|---|---|
| D Montgomery, RB | 3 / 3 — saturated | 29.00 | **0.00** | 29.00 |
| D Adams, WR | 0 / 3 — structural hole | 19.05 | **8.33** | 27.38 |

Roster fit moved the empty-position candidate up by 8.33 points and narrowed a 9.95-point
valuation gap to 1.62. The context layer is not missing or silent — it argued hard and lost to a
real ten-point difference in player value, which is the intended precedence.

## The three genuine gaps

1. **"Covered" and "saturated" are the same state.** A roster with three WRs and one with seven
   both earn `need_bonus = 0.00`. Expressing the difference through this term would require a
   **negative** contribution — charging a player for his position's depth, i.e. putting roster
   state inside player value, which the doctrine forbids. If the distinction is wanted it
   belongs in a tiebreak or presentation signal, never in `team_acquisition_value`. Pinned by
   test so the choice is made deliberately rather than discovered.
2. **Handcuff relationships have no representation at all** — the only hypothesised concept with
   zero footprint anywhere in the codebase. It is also the only one that would need genuinely
   new data (which back-up belongs to which starter), not just wiring.
3. **Peer-relative positional depth is stranded.** `depth_ratings.depth_label` reaches three
   surfaces and not the draft. It answers a *different* question from coverage — "am I thin
   compared to the rest of the league" versus "can I field a lineup" — so its absence from the
   draft path is arguably correct scoping rather than an oversight. Recorded so the choice is
   explicit.

## What is NOT recommended, and why

No new contextual layer, no roster-depth points added to player value, and no
"WRs get −X after six". The measured behaviour is a working, monotone, league-derived ladder
that already reaches the decision layer and already decides ties at a sane rate. The open
question it leaves is **step size** — whether 4.0 per dedicated slot gives roster fit the right
authority, given it fell short in 10 of 52 ties — and that is a calibration decision with a
quantified basis, not a missing feature.

## Invariants

122. Roster state may raise a candidate and may never lower him. `need_bonus` is non-negative at
     every coverage level; charging a player for his position's depth would put decision context
     inside player value.
123. Coverage and need move in opposite directions, always. Holding more of a position never
     buys more contextual credit for it.
124. The ladder's step sizes derive from the league's own `roster_positions`. A position that can
     fill more starting slots starts higher; no per-position constants are introduced.
125. Before a contextual signal is added, the existing representation of that concept is located
     and measured. A signal that is invisible in the final ranking is not thereby absent.

---

# Appendix — three hypotheses, investigated

Each is classified against the four possible conclusions: **already represented and working**,
**represented but stranded**, **represented but miscalibrated**, or **not represented**.

## H1 — is `need_bonus`'s 4.0-per-slot step miscalibrated?

**Conclusion: already represented and working. Pinned, not recalibrated.**

The raw counts (need changed the winner in 6 of 52 tie groups, fell short in 10) are not by
themselves evidence of a wrong coefficient. Classifying all 10 fell-short cases on the two
dimensions that decide whether each was a failure — was roster state **relevant** (do the
candidates differ in coverage at all), and was the player-value gap **material** (bigger than
ordering noise):

| classification | n |
|---|---|
| roster state relevant, player-value gap **material** → need correctly lost | **8** |
| roster state **not relevant** (both candidates equally covered) → need should not decide | 1 |
| roster state relevant, player values **equivalent** → need should have won | **1** |

`need_bonus` recovered a **median 86%** of the underlying valuation gap (min 26%, max 94%),
leaving residuals of 0.27–1.95 — all inside the ordering-noise band.

The one genuine miss: round 6, roster 6 — B Tuten (RB, 3/3 **saturated**, UV 16.00, need 0.00)
beat D Goedert (TE, 1/2, UV 14.75, need 0.33). Value gap 1.25; contextual difference only 0.33.
**That is not a step-size problem.** Raising 4.0 per slot would scale all eight steps that are
currently working correctly in order to move one case whose contextual difference is small
because TE-at-1-of-2 genuinely is a small distinction. No recalibration is indicated.

## H2 — is "covered vs saturated" represented anywhere?

**Conclusion: represented but stranded, with measured independent decision value.**

> **Superseded in part.** The contract work that followed (see *"Appendix — H2 settled"*)
> confirms *represented but stranded* and **withdraws *with measured independent decision
> value***. That phrase rested on a comparator run without a per-candidate gate. Under the
> correct gate the measured decision value is **zero**. Read this section for the inventory and
> the two false starts; read the settled appendix for the conclusion.

`lineup_optimizer.marginal_lineup_value` is *"best lineup with him minus best lineup without
him"* — precisely "incremental roster utility". It is **already computed for every candidate on
every board**, inside `eligibility_bonus`, and returned as
`marginal_value_full_eligibility`. `draft_room`'s call site reads only `eb["eligibility_bonus"]`
— the *difference* between full and primary-only eligibility — and **discards the absolute
marginal value**. The concept is stranded at the last inch, and it is already paid for.

Two false starts are recorded here because each looked like a positive result and was not:

1. A first run showed marginal value as a per-player constant. Cause: **my own probe passed
   `_team_roster_players`' arguments in the wrong order** (`(picks, rid, m, db)` against a
   signature of `(picks, players_db, roster_id, merger)`), so every roster came back empty and
   every marginal equalled the player's own value. Production calls it correctly. Result void.
2. A corrected run showed "19 of 19 tie groups separated — 100% independent information". That
   was a **test-design flaw of mine**: selecting groups where `need_bonus` is identical selects
   mostly *same-position* pairs, where coverage is identical by construction, so the separation
   was `trade_value` variance rather than roster state. Result void.

The controlled experiment — hold the candidate fixed, vary the roster — is what actually answers
it. Marginal value against a roster holding 0…7 players at the candidate's own position, with
every other position at full coverage:

| candidate | tier | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|---|
| J Gibbs | **elite** RB | 95 | 95 | 95 | **48** | **20** | **14** | 14 | 14 |
| D Henry | mid RB | 26 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| J Brooks | depth RB | 20 | 20 | 0 | 0 | 0 | 0 | 0 | 0 |
| P Nacua | **elite** WR | 94 | 94 | 94 | 11 | 5 | 5 | 5 | 5 |
| B Bowers | **elite** TE | 96 | 96 | 13 | 13 | 13 | 13 | 13 | 13 |

It **declines with coverage**, and at four rostered RBs it separates **Gibbs (20 — he would
displace a starter) from Henry and Brooks (0 — they would not)**, where `need_bonus` scores all
three at exactly 0.00. That is the saturated-position distinction, *including* the exemption for
an elite asset who still deserves preference over an ordinary depth piece.

Also measured: the signal is **degenerate before the lineup fills** (100% of candidates have
marginal == their own value at round 2, falling to 0% by round 14), so it only becomes
informative from roughly round 10 — which is exactly when `need_bonus` reaches 0.00 and goes
silent. **The two are complementary in time, not duplicative.**

### Why this is NOT wired yet

It is denominated in **`trade_value`** — Draft Sharks' dynasty market scale — not in the board's
projected points. Consuming it anywhere in the decision path means crossing a measurement basis,
which this engine requires to be explicit (the call site already performs exactly such a rescale
for `eligibility_bonus`, via `ELIGIBILITY_BONUS_MAX / TRADE_VALUE_SCALE_MAX`, after a real units
defect was found there). So the open questions are, in order:

1. Should incremental lineup utility influence a tiebreak at all, given core value and need
   already precede it in the hierarchy?
2. If so, in whose currency — and is a market-value quantity acceptable as a tiebreak on a
   projected-points board?

**Proposed home, not implemented:** surface it as an *observable* on the board record first —
the same treatment `waiting_cost` already has (computed, exposed, deliberately not consumed) —
under a name that states its basis. That changes no decision today and makes the signal
inspectable before it is trusted.

> **Answered.** Both questions above are answered in *"Appendix — H2 settled"*: (1) no, and
> (2) the basis question turns out not to be the binding constraint — the signal fails on
> decision value before the currency question is reached. It stays an observable, and stays
> unwired.

## H3 — handcuff / contingent-role classification

**Conclusion: not represented, and not constructible from data this repository holds.**

Recovery first, as instructed. Searched the working tree and **every branch's history**: the only
occurrence of "handcuff" anywhere is the line written in this document yesterday. No prior
analysis, definitions, fixtures or measurements exist. "Ray Davis" and "Braelon Allen" appear
only as rows inside vendor ranking CSVs.

The concept does exist — **but only as prompt text**. `llm_engine.py`'s Beat Tracker persona is
instructed to web-search depth charts and judge whether a player is *"the unquestioned starter,
in a committee, or buried behind someone"*, and `bot_benchmark.py` poses a workload-inheritance
scenario as a benchmark question. Both delegate the judgement to an LLM at runtime. Neither
computes or stores anything. This is a concept that exists **nominally**.

The five categories proposed (direct handcuff / partial or committee contingent / ambiguous
backup / standalone with contingent upside / no relationship) all require role and workload
evidence. Every canonical table's full field list is:

```
name, team, position, rank, projection, proj_3yr, trade_value, source_date
plus, from external sources: age, rookie, injury_flag, bye_week, ecr_1qb/2qb,
avg/best/worst, std_dev, trend_30d, tier, pos_rank
```

There are **no carries, targets, snaps, touches, games started, depth-chart order, or any
linkage between two players**. A search of `data/` for any usage-shaped file returns nothing.

What *is* constructible is "the Nth-highest-projected player at position P on NFL team T" — 28
RB groups carry 2+ players. That is a projection-order proxy, **not** a role classification: it
cannot separate a true next-man-up from a committee back from a standalone starter, which is the
entire content of the proposed taxonomy. Building the label on it would produce exactly the
`is_handcuff = true` nominal flag that was ruled out.

**This is a data gap, not an architecture gap.** The prerequisite is a usage/role source
(snap share, touch share, or a depth-chart feed). Until one exists, no measurable classification
can be defended, and the concept stays where it is — delegated to the LLM layer, which can at
least go and look.

## Invariants

126. A signal's independent decision value is established by a controlled comparison — hold the
     player fixed and vary the state — not by observing that it separates candidates. Separation
     can come from any correlated quantity, including a different measurement basis.
127. A concept that exists only as instructions to an LLM is not represented in the engine. It is
     recorded as nominal, and is neither cited as coverage nor duplicated by accident.
128. A classification is proposed only when the evidence to compute it exists. Where the required
     data is absent, the gap is reported as a data gap and the label is not invented.

## Sweep: information computed and never read

`marginal_value_full_eligibility` suggested a class worth sweeping mechanically — a function
assembles a dict, a caller reads one key, and the rest is computed work nothing consumes. An AST
pass collected every string key in a dict-literal `return` across the engine modules (71 keys)
and cross-referenced every reader in the repository.

**Result: 12 keys whose only non-producing readers are tests — of which 11 are explained and one
is the H2 finding.** That concentration is itself useful: it says the stranded-signal problem is
rare rather than systemic.

| key(s) | verdict |
|---|---|
| `assignments`, `benched`, `with_candidate`, `without_candidate`, `marginal_value` | **deliberate transparency.** `marginal_lineup_value`'s docstring: *"never just the delta alone, so a caller (or a human auditing a recommendation) can see both lineups' actual totals."* Correct as-is. |
| `growth_signal`, `unevidenced_picks`, `match_candidates` | **deliberate observables**, each documented as computed-and-exposed rather than consumed. |
| `reach_label`, `tier_gap` | **false positives** — consumed in the producing file (`pick_synthesis.py:985`) and onward into `app.py` and `pick_debate.py`. |
| `marginal_value_full_eligibility`, `marginal_value_primary_position_only` | **the H2 stranded signal.** Computed in production on every board row, asserted by tests, read by no production code. |

### Two blind spots in this sweep, recorded so a rerun is not misled

1. **Embedded JavaScript.** `draft_board_ui.py` ships a JS component that reads camelCase keys as
   strings. The Python AST cannot see it, which produced one phantom finding (`waitNote`, in fact
   read at `draft_board_ui.py:535`).
2. **Same-file consumption.** Treating a producing file as ineligible to be its own reader
   flagged `reach_label` and `tier_gap`, both of which are read a few lines below where they are
   built.

## Invariants

129. A "computed and never read" audit accounts for every consumer channel the code actually
     uses, including embedded non-Python and same-file reads. A finding from such a sweep is
     confirmed against the real call path before it is reported as stranded.

---

# Appendix — H2 settled: the contract for `marginal_lineup_value`

**Conclusion: category 2 — represented, stranded, and *correctly* stranded.**

Nothing is wired. `lineup_optimizer.py` is untouched. The deliverable of this pass is the
contract itself, pinned by `test_lineup_marginal_contract.py` (7 tests), so the conclusion can be
re-checked rather than re-derived, and so a future change to the optimizer cannot silently
invalidate it.

The six clauses asked for — what it measures, in what unit, when informative, when degenerate,
how it relates to `need_bonus`, what it may influence — are below in that order.

## 1. What it measures

The best startable lineup **with** this candidate minus the best startable lineup **without**
him: his incremental contribution to the nine players who actually score. Not his value — *the
part of his value the lineup can currently use.*

It is an exact solve, not an estimate: `optimize_lineup` runs
`scipy.optimize.linear_sum_assignment` over a (player × slot) cost matrix, so the two lineups
being differenced are both genuinely optimal. The quantity is therefore well-defined for any
roster, including ones where a flex slot makes the greedy answer wrong.

## 2. What unit it is denominated in

**Whatever currency the caller supplies** — the function's own docstring says so, and it is true
by construction. `draft_room` supplies `trade_value` (see `_team_roster_players`), so the number
reaching `eligibility_bonus` today is denominated in Draft Sharks' dynasty market scale, **not**
the board's projected points.

Two facts about that choice, both measured:

**(a) The market basis has strictly worse coverage than the points basis.** A rostered player the
basis cannot price is *dropped* — and a dropped player takes his lineup **constraint** with him,
so the solve runs against a roster emptier than it really is:

| round | on the roster | priced by `trade_value` | priced by `projection` | dropped (tv) | dropped (proj) |
|---|---|---|---|---|---|
| 4 | 4 | 4 | 4 | 0 | 0 |
| 8 | 8 | 8 | 8 | 0 | 0 |
| 12 | 12 | 12 | 12 | 0 | 0 |
| 16 | 16 | **14** | 16 | **2** | 0 |
| 20 | 20 | **18** | 20 | **2** | 0 |

And per `_team_roster_players`' own comment, **339 of 415 IDP baseline rows carry no trade value
at all** — in an IDP league the market basis would drop most of the roster.

**(b) Currency-agnostic is not the same as basis-invariant.** Scaling every input by *k* scales
the answer by exactly *k* (pinned by test). Substituting a *different valuation* is not a
rescale — it reorders players, and therefore changes which player the optimizer benches. Measured
on the same four candidates against the same roster shape in both bases (columns are how many
players the roster already holds at the candidate's own position, every other position filled to
its reachable slot count):

| candidate | basis | own | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| J Gibbs (elite RB) | `trade_value` | 95 | 95 | 95 | 95 | **48** | **20** | **14** | 14 | 14 |
| J Gibbs (elite RB) | `projection` | 359 | 359 | 359 | 359 | **43** | 43 | 43 | 43 | 43 |
| D Henry (mid RB) | `trade_value` | 26 | 26 | 26 | 0 | 0 | 0 | 0 | 0 | 0 |
| D Henry (mid RB) | `projection` | 262 | 262 | 262 | 0 | 0 | 0 | 0 | 0 | 0 |
| P Nacua (elite WR) | `trade_value` | 94 | 94 | 94 | 94 | **11** | 5 | 5 | 5 | 5 |
| P Nacua (elite WR) | `projection` | 357 | 357 | 357 | 357 | **41** | 41 | 41 | 41 | 41 |
| C Olave (mid WR) | `trade_value` | 52 | 52 | 52 | **0** | 0 | 0 | 0 | 0 | 0 |
| C Olave (mid WR) | `projection` | 256 | 256 | 256 | **256** | **0** | 0 | 0 | 0 | 0 |

The two bases agree on everything qualitative — monotone non-increasing in every row, and elite
(a positive plateau) separating from mid (exactly 0) at every depth past the step. They differ in
two measurable ways:

* **Where the step lands.** Three of the four candidates step at the same depth in both bases.
  **C Olave does not**: under `trade_value` he stops contributing at two rostered WRs, under
  `projection` at three. He loses the contested FLEX slot to the third WR in one basis and wins
  it in the other. That is a different *answer*, not a different unit.
* **Resolution past the step.** The market basis keeps distinguishing depths 3/4/5 (48 → 20 →
  14) where the points basis flattens immediately (43 → 43 → 43). Projected points are compressed
  at the top of a position (359 vs 262 = 1.4×) where dynasty market value is not (95 vs 26 =
  3.7×), so the starter being displaced is nearly as good as the candidate in points and much
  cheaper in market value.

So a projected-points variant is **constructible today** — no change to `lineup_optimizer` is
needed, only a different field at the call site — and it would have better coverage. That does
not make it the right thing to consume, for the reason in clause 5.

## 3. When it is informative, and when it is necessarily degenerate

Two regimes, distinguishable **exactly** — no heuristic, no round threshold — from what
`optimize_lineup` already returns:

| regime | test | his marginal is | informative? |
|---|---|---|---|
| **fills an empty slot** | assignment count **rises** when he is added | his own full value | **no** |
| **displaces a starter** | assignment count **unchanged** | value minus the starter he benches | **yes** |

The degenerate regime is not a rounding artifact; it is the definition. If a slot is empty, the
best lineup with him is the best lineup without him **plus all of him**. Ordering candidates by
that number is ordering them by raw projected points — not comparable across positions, which is
the exact thing VOR exists to correct.

Measured share of candidates sitting in the degenerate regime, by round:

| round | 4 | 8 | 10 | 14 | 16+ |
|---|---|---|---|---|---|
| degenerate | **92%** | 42% | 22% | 15% | **0%** |

**Roster size is not a valid gate.** A roster of 14 was measured using only 8 of its 9 starting
slots — position mix, not headcount, decides whether a slot is still open. The condition is
per-candidate and must be evaluated per-candidate.

## 4. How it relates to `need_bonus`

**Complementary in time, not duplicative** — and the complementarity is exact, not coincidental.

`need_bonus` is keyed to **unfilled reachable slots**. It reaches 0.00 the moment a position is
covered. That is precisely the moment this signal stops being degenerate. Before coverage:
`need_bonus` speaks, marginal is degenerate. After coverage: `need_bonus` is silent, marginal is
informative. They hand off at the same boundary because they are keyed to the same fact.

Where `need_bonus` is silent, marginal separates candidates it cannot: on a roster holding four
RBs, J Gibbs scores **20.0** (he would displace a starter) while D Henry and J Brooks score
**0.0** (they would not), and `need_bonus` scores all three at exactly **0.00**. That separation
is real, and it is the "covered vs saturated" distinction the hypothesis asked about — including
the exemption that matters, that an elite asset at a saturated position still outranks a depth
piece there.

## 5. What decisions it may influence: **none, on this evidence**

The architectural question was whether it could be a **comparator** rather than a coefficient:

* a *coefficient* is `TAV += k * marginal` — it changes the value, requires a constant *k*, and
  mixes units;
* a *comparator* orders candidates **inside** a near-tie group — it introduces no constant, adds
  nothing to any value, and only orders a set the engine has **already declared equivalent**
  (`|ΔTAV| ≤ NEAR_TIE_BAND`).

The comparator is the safe shape, so that is what was measured — in the board's **native**
projected-points basis, on real board states, rounds 10–18, all three gates computed in **one
pass** so the numbers are directly comparable:

| gate | groups evaluable | would change the recommendation | agrees |
|---|---:|---:|---:|
| (1) none | 25 | 2 — **8%** | 23 |
| (2) roster size ≥ slot count | 25 | 2 — **8%** | 23 |
| (3) **per-candidate displacement** (correct) | **14** | **0 — 0%** | 14 |

Three things in that table matter more than the headline zero.

**Gate (2) is inert.** It returns the identical 25 groups and the identical 2 changes as no gate
at all — by round 10 every roster already holds at least the 9 players the lineup needs, so a
headcount test excludes nothing. A gate that never fires is not a conservative version of the
right gate; it is no gate wearing the right gate's name.

**Both ungated "changes" are the artifact, visibly:**

```
 rd ros  current leader   pos   marg  regime      comparator pick   pos    marg  regime
 10  10  J Dart           QB     0.0  displaces   M Pittman Jr.     WR    202.0  FILLS
 12   7  D Schultz        TE     0.0  displaces   J Dobbins         RB    171.0  FILLS
```

In both, the comparator's pick wins on a marginal of 202.0 and 171.0 — **raw projected season
points**, because his slot was empty — against a leader whose 0.0 is a genuine increment. That is
not a close call the comparator resolved; it is two different quantities being sorted in one
column.

**Every apparent change came from the degenerate regime, and none survived the gate.** In the
regime where the signal is informative it never disagrees with `team_acquisition_value`; in the
regime where it disagrees it is not informative.

That is a stronger result than "the effect is small". It says a correctly gated version of this
signal has **nothing to add to the ranking** on the evidence available. Wiring it would import a
second measurement basis into the decision path in exchange for a measured zero.

> **A number from my own earlier notes is withdrawn here.** An intermediate run recorded "38%
> ungated"; the single-pass reproduction above returns 8%, and 38% is not reproducible from any
> script in the record. The gated result (0%) reproduced identically across both runs, so the
> conclusion is unaffected — but the ungated figure published here is the one that came out of a
> run that also produced the other two, and the earlier one should not be cited.

It therefore stays exactly where it is: computed, returned, and read by nobody — the same status
`waiting_cost` holds, and for a better-established reason.

**And "it's only a tiebreak" was never the safety argument.** 76% of real board states have the
leader inside a tie group of 2+, so a tiebreak layer engages in three of every four picks. A
tiebreak here is a decision layer.

## 6. Do `eligibility_bonus` and `marginal_lineup_value` together already express
"covered vs saturated"?

**Yes — and that is the answer to the `roster_surplus_penalty` question.**

`marginal_lineup_value` expresses saturation *directly and correctly*: it goes to zero for a
player the lineup cannot use, stays positive for one it can, and never charges anybody for his
position's depth. It is the better abstraction, exactly as suspected — a real economic quantity
solved from the league's own `roster_positions`, not a decay curve with an invented shape.
`eligibility_bonus` is the same primitive differenced twice, isolating what multi-position
eligibility alone unlocks.

So: **no `roster_surplus_penalty`, no position-count decay, no per-position table.** The concept
is already represented, by better machinery than any of those would be.

But the answer carries the clause 5 limitation with it. The pair expresses covered-vs-saturated
**only in the displacement regime** — and that is precisely the regime in which it agrees with
the ranking the engine already produces. The abstraction is right; there is no decision waiting
for it.

## Correction to a correction: the "19 of 19" tie-group tally stands

This entry records a self-review that was **itself wrong**, because the wrong version was already
circulating in this session's working notes and a record that quietly drops it would be worse
than one that shows the round trip.

**The committed claim** (`fc1c92a`, repeated in `863df6b`): *"In tie groups where roster coverage
differed, `need_bonus` favoured the least-covered candidate in 19 of 19 — no counterexamples."*

**The self-review that flagged it.** Re-reading my own classifier, its tally rule is lenient — it
scores a group as agreement whenever the least-covered and most-needed candidate are tied on
*either* quantity:

```python
if cov[least] == cov[most_need] or tied[least].need_bonus == tied[most_need].need_bonus:
    agree += 1
```

A group where `need_bonus` is identical across every tied candidate says nothing at all, and that
branch would count it as a confirmation. I concluded the tally was inflated and needed
restating.

**Re-measurement, and what it actually showed.** Running the strict recount — no-information
groups separated out, agreement required to be strict — under two different definitions of
"least covered":

| yardstick for "least covered" | groups | favours least-covered | favours better-covered | no information |
|---|---|---:|---:|---:|
| coverage **fraction** (`held / reachable`) | 23 | 15 | **2** | **6** |
| **unfilled slots** (`reachable − held`) — the engine's own, and the one the original script used | **19** | **19** | **0** | **0** |

**The committed claim is exactly right.** 19 groups, 19 strict agreements, no counterexamples, and
— the part that matters — **zero no-information groups**, so the lenient branch never decided an
outcome. The defect in the classifier is real but **latent, not live**: verified by counting, not
assumed.

**My self-review was the error.** It substituted coverage *fraction* for unfilled slots while
claiming to recount the same measurement. That single substitution changed the sample (23 groups
instead of 19), manufactured six no-information groups, and produced two "disagreements" — both
of them the same shape:

```
  B Tuten      RB   held 1/3   fraction 0.33   UNFILLED 2   need 4.33
  D Prescott   QB   held 0/1   fraction 0.00   UNFILLED 1   need 4.00
```

By fraction the QB is less covered (0.00 < 0.33). By unfilled slots the RB has more to fill
(2 > 1). **`need_bonus` is keyed to unfilled reachable slots**, so it prefers the RB — correctly,
by its own contract. The disagreement was in my ruler, not in the engine.

**What this leaves behind that is worth keeping:** coverage-as-fraction and
coverage-as-unfilled-slots are genuinely different orderings, and they disagree on real board
states — a one-slot position at zero looks maximally uncovered by fraction and only moderately
uncovered by slot count. Any future measurement of "coverage" has to use the yardstick the
quantity under test is actually keyed to, or it will manufacture disagreements out of its own
units. That is the same class of error as every unit defect already catalogued here, committed
this time by the audit rather than by the engine.

## Invariants

130. A signal is gated by the condition that makes it meaningful, evaluated where that condition
     actually varies. `marginal_lineup_value` is meaningful only when the candidate displaces a
     starter; that is a per-candidate fact, and a roster-level proxy for it (headcount, round
     number) measures something else.
131. A gate is validated by showing what it excludes. A gate that admits the same population as
     no gate at all is inert — and naming it after the right condition hides that it is.
132. Currency-agnostic is not basis-invariant. Scaling every input by a constant is safe;
     substituting a different valuation is a different problem instance, because it can reorder
     the players and change which one the optimizer benches.
133. A tiebreak is a decision layer wherever ties are common. Its safety is argued from a measured
     engagement rate, never from the word "tiebreak".
134. A signal is wired when it is measured to change a decision for a reason the contract
     endorses. Being real, already computed, and interpretable is not sufficient — those three
     describe a good observable.
135. A quantity's behaviour is measured with the yardstick that quantity is keyed to. Coverage as
     a fraction and coverage as unfilled slots are different orderings, and they disagree on real
     board states.
136. A published number is one a script in the record reproduces. Where a remembered figure and a
     reproduced figure disagree, the reproduced one is published and the other is withdrawn by
     name rather than quietly dropped.

---

# Appendix — sweep 2: stranded at function granularity, and one live lead

Sweep 1 asked which *dict keys* a producer builds and nobody reads. Sweep 2 asks the same
question one level up: which **top-level functions and classes** in the engine modules have no
live product consumer. Same corrected methodology — a name counts as consumed if it is
referenced anywhere at all, including inside the producing module and inside embedded non-Python
text — with consumers bucketed rather than reduced to a yes/no, so the verdict is auditable:

`APP` (app.py or another engine module) · `SELF` (the producing module) · `TEST` · `HARNESS`
(`run_*`, `bot_*`, `*_audit`, ablation/benchmark scripts) · `STRING` (only inside quoted text).

**Result: 20 engine modules, and exactly 6 top-level names with neither an `APP` nor a `SELF`
consumer.** Six out of hundreds is the same shape as sweep 1's finding — stranding here is rare,
not systemic.

| module | name | consumers | verdict |
|---|---|---|---|
| `data_merger.py` | `parse_espn_idp_pdf` | STRING only | **deliberate, and says so.** Its own docstring: *"there's no live upload path for ESPN at all… nothing in the running app currently calls this. Kept to regenerate the baseline CSV."* This is the honest form. |
| `roster_diagnostics.py` | `compute_team_diagnostics` | HARNESS, TEST | offline harness entry point. Already recorded as post-draft-only scoping. |
| `draft_simulation.py` | `run_trials` | HARNESS, TEST | offline harness entry point. |
| `option_set_analysis.py` | `analyze_option_sets` | HARNESS, TEST | offline experiment entry point (its whole module is one). |
| `draft_room.py` | `drafted_counts_by_position` | STRING, TEST | **a false consumer claim — repaired below.** |
| `rookie_draft.py` | `estimate_future_pick_value` | TEST ×8 | **the live lead — investigated below.** |

## The repair: a docstring that named a caller which does not exist

`draft_room.drafted_counts_by_position` is a thin public wrapper over the private
`_drafted_counts_by_position`. Its docstring justified its existence by naming a consumer:
*"for callers outside this module (e.g. `pick_synthesis.narrow_candidates`, via
`replacement_ranks` above)."*

**That path does not exist.** `replacement_ranks` reaches the same counts through
`remaining_starter_demand`, not through this wrapper, and nothing outside `draft_room` calls the
wrapper at all. The function is correct; the sentence about who calls it was false, and a future
reader would have believed those counts flow to `pick_synthesis` when they do not.

The wrapper is kept — it is the intended public spelling of a private helper, and a test pins the
two to each other exactly — and the docstring now states that it is currently unconsumed, the
same honesty `parse_espn_idp_pdf` already applies to itself. **Documentation defect, not a code
defect**, and repaired as one.

## The live lead: every future pick is priced as though nobody owns it

`rookie_draft.estimate_future_pick_value` prices *a specific team's* future pick from that team's
current record instead of one flat number every future pick of that round and year receives. It
is fully implemented, covered by 8 test references, and **called by no production code**. Its own
module docstring states the gap it was written to close:

> *a FUTURE pick … currently prices at one flat, generic number regardless of whose pick it
> actually is — a last-place team's next 1st and a championship team's next 1st get the identical
> value.*

That is still exactly what the product does, at four sites in `app.py` (1875, 3579, 3637, 5062),
all of the form `merger.pick_value(f"{season} Random Rd {round}")`.

### Magnitude — measured, and large in round 1 only

Draft Sharks' per-slot chart is fully loaded: **12 of 12 slots priced in each of rounds 1–4.**

| round | 1st slot | last slot | spread |
|---|---:|---:|---:|
| 1 | **83** | **19** | **64** |
| 2 | 18 | 11 | 7 |
| 3 | 9 | 5 | 4 |
| 4 | 4 | 2 | 2 |

The flat generic price the product uses for a 2027 first is **29**. So the engine holds a 64-point
spread on a 0–100 scale — wider than most players' entire trade value — and prices every team's
future first at the single number 29. Round 2 and beyond, the spread is 7 or less: **this is a
first-round phenomenon almost entirely**, which is itself the scoping fact.

Blended estimate versus the flat 29, by record and by how far out the draft is:

| record | est. slot | 0 yrs out | 1 yr | 2 yrs | 3 yrs |
|---|---:|---:|---:|---:|---:|
| 0–14 | 1.00 | **+54.0** | **+32.4** | +16.2 | +8.1 |
| 3–11 | 3.36 | +5.9 | +3.6 | +1.8 | +0.9 |
| 7–7 | 6.50 | +0.5 | +0.3 | +0.1 | +0.1 |
| 11–3 | 9.64 | −7.6 | −4.6 | −2.3 | −1.1 |
| 14–0 | 12.00 | **−10.0** | **−6.0** | −3.0 | −1.5 |

At one season out — the ordinary dynasty case — the two ends of the standings differ by **38
points around a flat price of 29**.

### The degeneracy check, applied before proposing anything

H2's lesson was to find the degenerate regime *first*. Dynasty trades cluster in the offseason,
when no games have been played:

```
0-0-0  ->  estimated_slot 6.50 (league-average middle)  ->  value 29.3   vs  flat 29
```

**It degrades to the status quo exactly when it has no information.** That is the opposite of
`marginal_lineup_value`, whose degenerate regime produced a confident *wrong* ordering. This
signal's failure mode is to agree with what the product already does.

### Why it is not merely "uncalled" — the representation cannot carry the answer

The reason this is not a one-line wiring job is architectural, and it is deliberate.

`_roster_assets` **does** know whose pick it is: the ledger entry carries `roster_id` (the
original owner), and `snapshot["rosters"]`, `owner_labels` and `league_standings.team_standings`
are all in scope at that exact call site. Every input `estimate_future_pick_value` needs is
available there.

But that value is only displayed. The Trade Calculator's actual pricing runs through
`_price_trade_side(line)`, and `line` is a **string** — `"2027 Random Rd 1"`. The panel's own
comment states the invariant: *"the box (and `_price_trade_side` above) stays the single source
of truth for what's actually in the trade… Nothing here re-implements pricing."* Owner identity is
therefore discarded one step **before** pricing, by design.

So the finding is not "a function isn't called". It is: **the trade's asset representation is a
list of text lines, and a line cannot say whose pick it is.** Consuming this signal means changing
what a trade asset *is*, not adding a call — and the string-keyed design is a documented
invariant with a real purpose (one pricing path, hand-typed and clicked assets treated
identically), not an oversight.

### What is NOT established: reach

Magnitude is not reach, and the two must not be conflated:

* The free-text path has **no owner at all**, and the flat number is **correct** there — a user
  who types `"2027 Random Rd 1"` has not said whose pick they mean.
* Only the enumerated-ledger path knows an owner, and `build_pick_ledger` deliberately lists
  **only picks that have already been traded** — an untouched pick has no entry, by design.
* So even a complete wiring reaches only picks that have already changed hands *and* appear in
  the roster browse panel. **How many that is in a real league is unmeasured**, because this
  repository holds no Sleeper snapshot containing `traded_picks` (the one real league capture is
  a manual capture with no roster or standings block).

**Verdict: category 2 — represented but stranded, magnitude quantified, reach unmeasured, and
structurally out of reach of the current asset representation.** Nothing is implemented. The
prerequisite for deciding is a real league snapshot carrying `traded_picks` and
`roster.settings.wins/losses` — the same shape of prerequisite H3 established, and it lands on
the existing open item for acquiring real league data rather than creating a new one.

## Sweeps 3 and 4: the two remaining blind spots, closed

Sweep 1's recorded blind spots were embedded JavaScript and same-file consumption. Both were
fixed in method. Two *structural* blind spots remained — kinds of write the AST pass could not
see at all — and both are now swept rather than left standing as caveats.

**Sweep 3 — keys written by subscript assignment.** Sweep 1 read string keys out of dict
*literals*. A producer that builds its record with `row["x"] = …`, `.update({…})` or
`.setdefault("x", …)` was invisible to it, and `compute_draft_board` is exactly that shape — so
the board's own rows may never have been swept. Collecting every constant string key written by
those three forms across the engine modules, and cross-referencing readers with the corrected
methodology:

> **40 keys scanned. 0 with no live product reader.**

A clean negative. The blind spot was real and its contents are empty, which is a different and
better outcome than leaving it listed as unknown.

**Sweep 4 — dataclass attributes.** The decision layer's own records are dataclasses, and an
attribute is read as `.name`, which neither earlier sweep could match. Across 23 annotated fields
in the non-test modules, exactly one has no production reader:

| field | verdict |
|---|---|
| `pick_debate.PickDebateResult.recommended_player_id` | **not a finding — a redundant second spelling.** It is set as `recommended.player_id if recommended else None`, and `app.py:4489` reads exactly `mock_current_debate.recommended.player_id` off the sibling field. The information reaches production; only this accessor does not. Recorded so a rerun does not re-raise it. |

Nothing is lost, and nothing is changed. Both sweeps are recorded as run so that the phrase
"computed and never read" now covers dict literals, subscript writes, dataclass attributes,
embedded JavaScript and same-file reads — the five channels this codebase actually uses.

## Sweeps 5 and 6: work discarded before it ever reaches a consumer

Sweeps 1–4 all asked the same question from the consumer's side: who *reads* this. Two shapes of
loss are invisible from there, because the value never becomes a consumable in the first place.

**Sweep 5 — a value computed into a local and never read.** Per function, every plain-name
assignment target never loaded again in that same function, excluding conventional throwaways and
bare-constant right-hand sides. Across every non-test module: **exactly one hit — and it is in
`compute_draft_board`.**

```python
drafted_counts = _drafted_counts_by_position(demand_source, players_db)   # read by nothing
```

Traced: commit `05a4abb` (*"Decompose remaining demand into its exact and inferred halves"*)
removed the `drafted_counts` parameter from `replacement_levels`, `horizon_replacement` and
`_attach_waiting_cost` — **every consumer** — and left the producer standing as an unchanged
context line in the diff. **This is the semantic-drift pattern in its purest form:** a quantity's
role was deleted and a producer that served the old role did not notice.

**It is not a performance finding, and is not reported as one.** Measured: 0.015 ms at round 5,
0.037 ms at round 10, 0.057 ms at round 20, per board build. Irrelevant. The finding is what the
residue did to the *test suite*:

> `test_compute_draft_board_actually_passes_demand_picks_to_drafted_counts` spied on the census
> call and asserted it received `demand_picks` rather than `picks`. It passed. **It was proving
> that the right picks reached a computation whose result was thrown away.**

That is false assurance about the live demand path, which is the thing the test's own comment
says it exists to protect ("the direct wiring proof"). The repair keeps the intent and moves the
proof:

* the dead producer is removed, with a comment recording what happened and when;
* the test is **re-pointed at `remaining_starter_demand`**, which is where `demand_source` is
  actually consumed now, renamed to match, and strengthened — it now asserts over **every** call
  the board makes to the demand model rather than a single one, so an added second call site
  cannot quietly slip `picks` through, and it carries an explicit non-empty guard so it fails
  rather than passing vacuously if the board ever stops consulting the demand model at all;
* a second test pins the removal, so a computed-and-discarded census cannot reappear silently.

Both were verified to fail when they should: re-wiring the demand call to `picks` and
reintroducing the census produced two failures, then the probe was reverted.

The same trace also invalidated the *other* half of `drafted_counts_by_position`'s docstring —
that the counts are *"the same … counts `replacement_levels` itself uses."* `replacement_levels`
stopped taking drafted counts in that same commit; it prices replacement off
`remaining_starter_demand`. Both false claims came from one drift and are corrected together.

**Sweep 6 — a parameter accepted and never read.** Information handed *across* an interface and
dropped: invisible to every consumer-side sweep, because from the caller's side it very much is
consumed. Across every non-test module, **one hit**:

| site | finding |
|---|---|
| `sleeper_client.sync_league(league_id, players_db=None)` | `players_db` is never read — **and never was, in any version of the file.** Not a removed consumer; a parameter that has never done anything. Both callers (`app.py:1015`, `app.py:2978`) pass `client.get_players()` into it, doing real work to supply it. |

**Not repaired beyond the docstring, deliberately.** `client.get_players()` also warms the ~10MB
players cache, so dropping the parameter means deciding what happens to that side effect at two
Streamlit call sites — a UI decision, in ingestion code, during a valuation audit, with a cost
this environment cannot measure (no cached `players_nfl.json` is present). The signature now
carries an explicit note that the argument is ignored, so nobody reads it and concludes the
snapshot is players_db-aware. The removal is left as an owner's call, stated rather than skipped.

**Where the sweep now stands.** "Computed and never read" has been asked at six granularities —
dict literals, subscript writes, dataclass attributes, top-level functions, function-local values,
and function parameters — across five consumer channels including embedded JavaScript and
same-file reads. Total genuine findings: **one stranded signal correctly stranded (H2), one
stranded signal with an unmeasured reach (future picks), one residue of a completed refactor, two
false docstring claims, and one vestigial parameter.** Nothing systemic.

## Sweep 7: information destroyed by an exception handler — clean

The most literal reading of "where does the system silently lose information": an `except` block
that neither re-raises, nor records anything, nor produces a value encoding the failure. Every
handler in every non-test module whose body is a bare `pass`/`continue`/`break`/single `return`,
bucketed by how blind the catch is and whether it carries an explanation.

**36 such handlers. 13 catch broadly (`Exception`). Zero catch broadly without an explanation.**

And the 13 broad ones are not silent at all — the classifier flagged them only because their body
is one statement. Every one converts the exception into a *value* the caller receives:
`return ([], str(exc))` in `llm_engine`, `return f"⚠️ Claude request failed…"` in `pick_debate`.
The failure is carried, not dropped. The rest are narrow catches
(`FileNotFoundError`, `json.JSONDecodeError`, `ValueError`) returning the documented fail-soft
default.

Three `pass`-bodied handlers were read individually because a `pass` cannot encode anything:

| site | verdict |
|---|---|
| `data_merger.position_family:321` · `measurement_basis:1252` | correct. `pd.isna()` raises on array-like input; the fall-through reaches the `str(...)` path, which is the right answer for a non-scalar. |
| `app.py:791` | correct, and the surrounding comment is the reason: a corrupt history file is renamed to a backup before the load returns empty, and a failed *backup* must not break the load. |

**No findings.** Recorded because a clean negative on this particular question is worth having on
the record before a freeze.

## Invariants

137. A docstring that names a consumer is a claim about the call graph, and is checked against it.
     A function's stated reason for existing may not assert a caller that does not exist.
138. An unconsumed function is classified by *why*: deliberate tooling that says so, an offline
     harness entry point, or a stranded signal. The three are recorded differently and only the
     third is a finding.
139. Magnitude and reach are separate claims and are reported separately. A large per-case
     difference over an unmeasured population does not establish decision value, and neither
     number substitutes for the other.
140. A recorded blind spot is closed by sweeping it, not by repeating the caveat. A clean
     negative from a blind spot is a result and is written down as one.
141. A test proves a consequence, not a call. Spying on a function whose result is discarded
     asserts wiring into nothing, and passes forever while the path it claims to protect goes
     unguarded.
142. When a refactor removes a quantity's consumers, the producer is removed with them. A
     producer outliving its role is where semantic drift starts, and it is invisible to every
     consumer-side audit.

---

# Appendix — future-pick valuation (task #85), investigated

**Verdict: REJECT.** Nothing is wired. `rookie_draft.py` keeps its logic unchanged; only its
module docstring gains an audit note, and three characterization tests make the findings
executable. Production behaviour is byte-identical.

The hypothesis was that `rookie_draft.estimate_future_pick_value` — complete, tested, called by
nothing — is a stranded signal worth connecting, because the Trade Calculator prices every future
pick at one flat number. The investigation says the flat number is **already the better answer**,
and that the primitive is measurably wrong in two independent ways.

## 0. A correction to this audit's own framing of #85

The finding as I logged it read: *"Draft Sharks prices 12/12 round-1 slots from 83 down to 19 —
a 64-point spread — and the flat price is 29."* **That compares two different assets.**

* `rookie_pick_slot` rows (`1.01` … `4.12`) price the **current** year's draft, where the slot is
  known. They are priced **exactly**, and the existing flat-lookup path already returns them
  exactly. Nothing is lost there and no estimate is needed.
* `future_pick` rows (`"2027 Random Rd 1"`) price a draft whose slot **nobody knows yet**. That
  is the only place a flat number is used, and the only place this primitive could apply.

The 64-point spread was never being discarded. It belongs to an asset class the engine already
prices correctly. The real question is much narrower, and the rest of this appendix asks it.

## 1. Representation — where owner survives, and where it dies

| layer | carries | owner present? |
|---|---|---|
| Sleeper ingest (`get_traded_picks`) | `season`, `round`, `roster_id` (original owner), `owner_id` (holder) | **yes** |
| Vendor ingest (`parse_draftsharks_trade_value_chart_pdf`) | `asset_type`, `name`, `value` | **no — by the vendor's own design.** `"2027 Random Rd 1"` is ownerless because the slot is unknowable |
| Roster/trade state (`build_pick_ledger`) | the raw Sleeper dicts, as `roster_id → {acquired, given_away}` | **yes** |
| Trade Calculator, browse panel (`_roster_assets`) | builds a display row from the ledger | **yes** — and it computes a value here |
| Trade Calculator, **pricing** (`_price_trade_side`) | a **string**: `"2027 Random Rd 1"` | **no** |
| Draft decision layer (`draft_room`, `draft_strategy`, `pick_synthesis`, `pick_debate`, `screen_context`, `lineup_optimizer`) | — | **picks do not exist here at all** |
| `CandidateSnapshot` | `player_id`, `position`, `projected_points`, … | a candidate is a player; a pick is never a candidate |

Two structural facts fall out.

**The CDME decision layer has no future-pick surface whatsoever.** A grep for pick assets across
all six decision modules returns nothing. So the primitive cannot influence a draft
recommendation even in principle; the only decision surface in the product that prices picks is
the Trade Calculator.

**Owner is destroyed one call before the price is computed, by the widget itself.** Clicking an
asset in the browse panel appends `a["line"]` — the bare string — to a `st.text_area` the user
also types into freely, and `_price_trade_side` re-prices from that text. The text buffer is not
an incidental serialization; it is the two-way-bound source of truth, and the panel's own comment
says so: *"the box … stays the single source of truth for what's actually in the trade … Nothing
here re-implements pricing."* The value shown beside a pick in the browse panel is display only.

## 2. Call graph — the whole module is orphaned

Not "one function disconnected from one surface":

```
grep -rn "import rookie_draft|from rookie_draft" --include=*.py .
  → test_rookie_draft.py:11        (and nothing else)
```

`rookie_draft` is imported by its own test file and by nothing else — not `app.py`, not any
engine module, not even `run_rookie_draft_analysis.py` or `run_rookie_draft_validation.py`, which
despite their names drive `draft_room` with a rookies-only pool scope. There is no partial
wiring anywhere to complete.

Every current consumer of future-pick valuation is `merger.pick_value(...)`, at four sites:
`app.py:1875` (LLM context text), `app.py:3579` (`_price_trade_side` — **the only decision
path**), `app.py:3638` (browse-panel display), `app.py:5062` (League page caption).

## 3. Reachability — measured, not inferred from magnitude

The vendor publishes a flat future-pick row for **exactly two distances**:

| season | seasons_until_draft | Rd 1 | Rd 2 | Rd 3 | Rd 4 |
|---|---:|---:|---:|---:|---:|
| 2026 (current) | 0 | — | — | — | — (priced by exact slot instead) |
| **2027** | **1** | **29** | 14 | 10 | 6 |
| **2028** | **2** | **27** | 13 | 9 | 6 |
| 2029 | 3 | — | — | — | — |

So of `FUTURE_YEAR_RECORD_DISCOUNT = {0: 1.0, 1: 0.6, 2: 0.3}`, **the 1.0 entry is structurally
unreachable** — and it is the entry that produced the headline `+54.0` in the original finding.
Only weights 0.6 and 0.3 can ever apply.

**The existing test suite exercises only the unreachable distances.** Every
`estimate_future_pick_value` test runs at `seasons_until_draft=0` or `3`. The suite's headline
assertion — a 1-11 team's next first must price more than 15.0 above an 11-1 team's — behaves
like this across all four distances:

| seasons out | vendor flat | 1-11 | 11-1 | spread | assertion | reachable? |
|---:|---:|---:|---:|---:|---|---|
| 0 | — | 43.6 | 19.9 | 23.7 | PASS | no |
| **1** | **29** | 37.8 | 23.6 | **14.2** | **FAIL** | **yes** |
| **2** | **27** | 32.0 | 24.9 | **7.1** | **FAIL** | **yes** |
| 3 | — | 43.6 | 19.9 | 23.7 | PASS | no |

**The module's central claim fails its own materiality bar at both distances production can
reach.** The tests are sound unit tests of the function as written; they simply exercise a regime
the product cannot enter.

## 4. Basis

**Coverage.** Complete: 12 of 12 slots priced in each of rounds 1–4, plus flat rows at distances
1 and 2. Coverage is not the problem.

**Semantics — and this is where it breaks.** The flat price is **not a placeholder**. It is
already a well-calibrated central estimate of the slot distribution:

| round | slot mean | mean excl. 1.01 | slot median | flat 2027 | flat 2028 |
|---:|---:|---:|---:|---:|---:|
| 1 | 32.3 | 27.7 | **29.5** | **29** | 27 |
| 2 | 13.8 | 13.5 | 13.5 | **14** | 13 |
| 3 | 6.3 | 6.1 | 6.0 | 10 | 9 |
| 4 | 3.0 | 2.9 | 3.0 | 6 | 6 |

Round 1's flat 29 sits between the distribution's median (29.5) and its mean-excluding-the-
lottery (27.7) — the raw mean of 32.3 is dragged up by a 1-in-12 outcome, and the vendor has
priced below it deliberately. Round 2's 14 against a mean of 13.8 is near-exact. **Beating this
number requires knowing which slot, not knowing the average.**

And the whole prize is one slot:

```
1.01=83  1.02=40  1.03=36  1.04=33  1.05=30  1.06=30  1.07=29  1.08=25  1.09=22  1.10=21  1.11=20  1.12=19
```

1.01 → 1.02 drops **43** points; the entire rest of the round, 1.02 → 1.12, spans **21**.
**67% of round 1's whole spread sits in the single 1.01 slot.**

**The register defect.** A draft slot is **ordinal** — reverse order of finish among *this
league's own twelve teams*, with exactly one 1.01 however the records fall.
`estimate_pick_slot` derives it **cardinally**, from one team's win percentage in isolation:

```python
return 1 + win_pct * (num_teams - 1)
```

No reference to the other eleven rosters. This is the defect class already catalogued here as
**#70, cross-register rank and ordinal propagation**. Measured over 400 simulated 12-team,
14-game seasons (win totals fixed at 84 by construction — a schedule identity, not a model
assumption):

| | |
|---|---|
| mean absolute slot error | **1.89 of 12 — 17% of the whole range** |
| median | 1.71 |
| 90th percentile | 3.14 |
| mean error on the league's **actual worst team** | **3.05 slots** |
| leagues where it placed the worst team within half a slot of 1.01 | **0 of 400** |

It never finds the slot that carries two-thirds of the value. A worked league makes the mechanism
obvious — the worst team finished 5-9, which is unremarkable, and the estimator prices its 1.01
near slot 4.9:

| record | true slot | estimated | error |
|---|---:|---:|---:|
| 5-9 | **1** | 4.93 | 3.93 |
| 5-9 | 2 | 4.93 | 2.93 |
| 7-7 | 5 | 6.50 | 1.50 |
| 10-4 | 11 | 8.86 | 2.14 |
| 10-4 | **12** | 8.86 | 3.14 |

The estimator's outputs span 4.9–8.9 where the truth spans 1–12: in a normal league it is
**compressed toward the middle by construction**, and therefore returns approximately the flat
price it was meant to improve on.

**The sample-size defect.** Apart from the zero-games case, `estimate_pick_slot` ignores how many
games produced the percentage:

| games played | record | est. slot | 2027 value | delta vs flat |
|---:|---|---:|---:|---:|
| 0 | 0-0 | 6.50 | 29.3 | +0.3 |
| **1** | **0-1** | **1.00** | **61.4** | **+32.4** |
| 2 | 0-2 | 1.00 | 61.4 | +32.4 |
| 6 | 1-5 | 2.83 | 33.6 | +4.6 |
| 14 | 3-11 | 3.36 | 32.6 | +3.6 |
| **14** | **0-14** | **1.00** | **61.4** | **+32.4** |

**0-1 after one week and 0-14 after a full season return the identical number**, while a plainly
bad 1-5 team gets a *smaller* adjustment than the 0-1 team. The valuation is at its most extreme
on its thinnest evidence.

**Availability.** Everything a corrected version would need is already in the snapshot:
`snapshot["rosters"]` → `league_standings.team_standings` returns wins/losses/ties for **all**
rosters (the population the register defect needs); `snapshot["nfl_state"]` carries `season` and
`week` (the sample-size and within-season-timing terms). **This is not a data gap** — unlike H3.
It is a primitive that under-specifies its own inputs.

**Invariants.** `FUTURE_YEAR_RECORD_DISCOUNT` is keyed to whole seasons, while the information
about next year's draft accumulates weekly: a 2027 pick is discounted to 0.6 in week 1 (when the
record says nothing) and to 0.6 again in week 17 (when it says almost everything).

## 5. Independent decision value — real, and pointing the wrong way

The one decision surface is the Trade Calculator's verdict, `app.py`'s own four tiers on
`delta_pct = |receive − send| / max(send, receive)`: **<5% Balanced · 5–10% Slight · 10–20%
Meaningful · ≥20% Material**. Pick values are additive contributors to those sums, so a changed
pick price genuinely can change a verdict.

Measured **conditionally** — assuming the architecture change of §6 had already been made — over
real priced player assets (157 of them), trades of the form *send player A, receive player B plus
one 2027 first*, sweeping the pick owner's record:

| record regime | seasons out | pairs | verdict-tier changes |
|---|---:|---:|---:|
| full season (14 games) | 1 | 5175 | 550 — **10.6%** |
| full season (14 games) | 2 | 5175 | 370 — 7.1% |
| **early season (1–3 games)** | 1 | 2070 | 378 — **18.3%** |

**This is not H2's zero.** The signal does move decisions. But it moves them **more often on one
to three games of evidence (18.3%) than on a full season (10.6%)** — because 0-1 and 0-14 produce
the identical extreme, and 3-0 and 14-0 do too. And within the full-season regime the changes
concentrate at the extremes (0-14: 69, 14-0: 57, 13-1: 56) where, per §4, the estimator is
betting on a 1.01 it demonstrably cannot identify.

That is the decisive result. A signal whose influence *rises* as its evidence *falls* is not a
weak signal; it is a miscalibrated one.

## 6. Architectural cost, if one wanted it anyway

Three independent changes, none small:

1. **An owner-carrying asset representation.** Today a trade side is a user-editable newline
   text buffer, and that is deliberate — one pricing path for typed and clicked assets alike.
   Carrying an owner means either a structured asset list running parallel to the text (two
   sources of truth, precisely what the current design refuses) or an owner-bearing string
   grammar a human must type correctly and a parser must disambiguate against display names.
2. **A future-pick inventory model.** `build_pick_ledger` lists only picks that have *already
   been traded*, by explicit design: *"an untouched pick is assumed to still belong to its
   original roster and isn't worth listing… not a full inventory of every hypothetical future
   pick."* Pricing "your own 2027 first" dynamically requires inventing that inventory.
3. **Rewriting the primitive.** The register defect needs the full standings population; the
   sample-size defect needs games played; the timing defect needs the week. The inputs exist,
   but the signature, the mapping, and every constant would change — and re-deriving those
   constants is a calibration exercise, not a wiring one.

That is the price. What it buys, in a normally-distributed league, is a pick price that moves by
a few points around a flat number that already equals the distribution's centre.

## 7. Verdict

**REJECT.**

Not "defer for want of data" — the data is present. Not "too small to matter" — 10.6% of verdict
tiers is not small. The rejection is that **the primitive is measurably less accurate than the
baseline it would replace**: the flat price is the slot distribution's centre, and the estimator
neither identifies the slot that carries the value (0 of 400) nor distinguishes one game of
evidence from fourteen.

What this does **not** claim: that future-pick pricing is a closed question forever. A
league-relative, rank-based, week-aware estimator is a coherent thing to want. It is a different
function from this one, it still faces the §6 architectural cost independently, and neither is in
scope now. The finding is recorded so that work would start from measurement rather than from the
assumption that the flat number was lazy.

## What changed in the repository

Documentation and tests only; **no production behaviour is modified**.

* `rookie_draft.py` — an audit note in the module docstring, so nobody wires it believing it is
  ready. The module previously described itself as the fix for a bug it does not, at reachable
  distances, fix.
* `test_rookie_draft.py` — three characterization tests pinning the sample-size defect, the
  register defect, and the reachability result. Each is labelled as documenting a **defect**, not
  approving one, and instructs whoever fixes it to delete the test and update the module note.
  All three were verified to fail when the behaviour they pin is changed.

## Invariants

143. Two assets priced by different mechanisms are not compared as though one mechanism were
     failing. An exactly-priced current-year slot and a flat future pick answer different
     questions, and the spread of the first is not evidence of loss in the second.
144. A vendor's flat number is checked against the distribution it summarizes before being called
     a placeholder. Here it is the median.
145. A quantity that is ordinal within a population is computed with the population. Deriving it
     from one member's cardinal statistic in isolation is the same defect wherever it appears.
146. An estimator is measured for whether its confidence tracks its evidence. One that produces
     its most extreme output on its thinnest input is miscalibrated, and the size of its effect
     on decisions is an argument against it, not for it.
147. Reachability is established over the regimes production can actually enter. A test suite
     that only exercises unreachable regimes validates the function without validating the
     feature.

---

# Appendix — backlog B: unpriced survival, insertion order, pace probability

**Verdict: ALREADY FIXED**, for everything B named — independently re-verified rather than taken
on trust — **plus one adjacent latent mechanism, DEFERRED.** No production behaviour changed.
Three tests added; `draft_strategy.py` is untouched.

## What B was, reconstructed from the record

B traces to the D2 repair (`cfe2a66`, appendix *"the survival layer's ordinal register"*), which
found `_build_opponent_boards` numbering every row `1..n` and handing that integer to two
consumers that read it through `RANK_TAKE_PROBABILITY` — a table whose keys mean *"the consensus
best available"*. For unpriced rows the integer came from a stability tiebreak, not a valuation.
A third site, `_pace_based_take_probability`, sorted on `universal_value` with `NaN` present,
producing a **non-total order**: the best QB's probability moved **1.0 → 0.111** purely by
reversing the dict's insertion order.

## Part 1 — the named items: all closed, re-verified independently

Controlled fixtures, constructed so each property is observable (real boards do not reach several
of these states):

| # | test | result |
|---|---|---|
| T1 | `rank_by_id` with unpriced rows **interleaved** among priced ones | ranks stay contiguous `1,2,3` over priced rows only; `unpriced_ids = {u1, u2}`; **both** absence spellings (`None` and `NaN`) caught |
| T2 | add 3 unpriced rows to a board, re-measure a **priced** target | survival `0.462 → 0.462`, rank `2 → 2` — **no probability-mass contamination** |
| T3 | unpriced target | survival exactly `(1 − FLOOR)² = 0.96`; `evidenced: False`; `rank_on_their_board: None`; `unevidenced_picks: 2` |
| T4 | target not in the pool at all | survival `1.0`, empty `risk_by_team` — **distinct** from T3's `0.96` |

T1's result is the strongest of these: the ordinal stays a valuation rank **even if the board's
own "unpriced sorts last" invariant were violated upstream**, because `rank_by_id` filters before
it enumerates. The construction is robust, not merely correct-by-coincidence.

**Pace probability, traced source to consumer.** `expected_now` comes from the convention curve;
`actual_now` counts drafted players at the position from `players_db` — deliberately *all* of
them, priced or not, because that quantity is "how many have gone", not a valuation. Only the
**denominator** touches the board, and it now counts priced peers only; an unpriced target gets
the function's own `None`, which is the caller's documented fall-back path. Unpriced players are
therefore **intentionally excluded**, never implicitly zero and never accidentally omitted. The
existing suite covers this on a constructed board (`PacePriorDenominatorTests`), including
insertion-order invariance — the 9× swing is closed and pinned.

## Part 2 — `draft_strategy.py:310`, the site B flagged: clean

The concern was `for player_id, rank in rank_by_id.items()` accumulating into a float. Two
findings, and the site itself is exonerated:

**The iteration order is not a free variable.** `rank_by_id = {r["player_id"]: i + 1 for i, r in
enumerate(priced)}` inserts keys in board order with values `1, 2, 3, …`, so `.items()` yields
ranks in **strictly ascending order, always**. For a given subset of ranks there is exactly one
realizable summation order.

**And even if a caller handed it a permuted dict, nothing would move.** Exhaustively, over every
subset of ranks `1..DEPTH` and every permutation of each:

* 12 of 31 subsets have an order-dependent raw sum — largest spread **2.22 × 10⁻¹⁶**;
* **0 of 31** have an order-dependent `round()`;
* 720 permutations of a constructed board's insertion order → **1 distinct result**.

So within one pick, float noise provably cannot reach the decision.

## Part 3 — the adjacent mechanism: `round(expected_taken)` is a knife-edge

Across picks the accumulation *is* order-sensitive, and the boundary is real. Constructed
adversarially — three opponent boards contributing `0.24 + 0.60 + 0.66`:

```
intervening order (A,B,C): raw sum 1.5                 expected_taken=1.5  forfeit=20.0  cliff_protection=True
intervening order (C,B,A): raw sum 1.4999999999999998  expected_taken=1.5  forfeit=10.0  cliff_protection=False
```

`round(1.5) = 2` but `round(1.5 − 1ulp) = 1`, so `drop` moves one step, `forfeit` doubles, and
**`cliff_protection` flips** — a decision-path flag read by `pick_synthesis.decision_path_flags`
(`forfeit >= NECESSITY_STANDOUT_REFERENCE_GAP`) and surfaced to the debate layer and the UI.
Worse, `expected_taken` reports **1.5 in both cases**, because it is rounded to 2 dp for display:
the surfaced explanation cannot distinguish the two outcomes.

`round()` is also banker's, which for a "how many will be taken" quantity is arbitrary:
`round(0.5)=0`, `round(1.5)=2`, `round(2.5)=2`.

### But the measured impact on real data is zero

Swept over **627** forfeit computations on real 12×20 board states, rounds 3–18, all twelve
rosters:

| | |
|---|---|
| land **exactly** on a `round()` boundary | **2 (0.3%)** |
| of those, where ±1 ulp changes `drop` | 2 |
| of those, where `forfeit` changes | **0** |
| of those, where `cliff_protection` flips | **0** |

| rd | roster | pos | expected_taken | round() | −1ulp | +1ulp | f(round) | f(+1ulp) | flag flips |
|---|---|---|---|---|---|---|---|---|---|
| 9 | 11 | WR | 1.5 | 2 | 1 | 2 | 5.04 | 5.04 | no |
| 12 | 4 | TE | 10.500000000000002 | 11 | 10 | 11 | 83.04 | 83.04 | no |

At both real boundary states the curve is flat enough around that index that a one-step change in
`drop` leaves the forfeit — and the flag — untouched. **The mechanism is real and demonstrable;
it is not currently a live defect.**

### Why this is DEFERRED and not fixed

The correct contract is **not clear**, and inventing one would change live behaviour:

* half-up, floor, or fractional interpolation of the curve are three different product answers;
* whichever is chosen moves 0.3% of forfeit computations by a whole curve step;
* choosing a rounding rule or an epsilon here is exactly the constant-tuning this phase excludes.

Pinned by a characterization test instead, so a future change to the rounding rule, the curve
shapes, or the take-probability table is deliberate and visible.

## Part 4 — `RANK_TAKE_PROBABILITY.get(rank, 0.0)` vs `RANK_TAKE_PROBABILITY_FLOOR`

**Unreachable, and the two differing defaults are both correct.** Ranks are assigned `i + 1` over
priced rows, so `rank ≥ 1`; the loop skips `rank > FORFEIT_OPPONENT_BOARD_DEPTH = 5`; every value
in `[1, 5]` is a table key. The `0.0` never fires.

It is also the *right* default there. `positional_forfeits` cuts at that depth precisely because
*"ranks past it carry only the floor probability, which would add noise, not signal, to a
position-level estimate"* — so `0.0` and `_take_probability`'s `FLOOR` are two functions
legitimately wanting different things, not a discrepancy to harmonize.

**What was missing is enforcement.** The module documents the coupling
(`FORFEIT_OPPONENT_BOARD_DEPTH` *"matches RANK_TAKE_PROBABILITY's own depth"*) and nothing
asserted it. Raise the depth to 8 without extending the table and ranks 6–8 would pass the filter
and contribute a silent `0.0` — an absent value spelled as a number, the one thing this
codebase's absence contract forbids. Now guarded by test.

## A correction to this investigation's own first measurement

My first real-board probe reported *"min distance to boundary 0.0000, and 8.2% of computations
one step from crossing 15.0"*. It re-derived `drop` from `positional_forfeits`' **returned**
`expected_taken`, which is already `round(…, 2)`, rather than from the raw accumulation
production actually rounds. At the round-12 TE state that gave `round(10.5) = 10` where production
computes `round(10.500000000000002) = 11`. The 627-computation sweep above reads the unrounded
value and supersedes it. The 8.2% figure described curve steepness near the operating point, not
boundary incidence, and should not be cited as the latter.

## Classification

| item | class |
|---|---|
| `unpriced_ids`, `evidenced`, `unevidenced_picks` | **already fixed** — re-verified independently |
| unpriced influence on survival, rank, probability mass, ordering | **already fixed** — no contamination measurable |
| pace / take-probability for unpriced players | **already fixed** — intentionally excluded, `None` not zero |
| insertion order at `draft_strategy.py:310`, within a pick | **not an issue** — one realizable order, and order-immune anyway |
| `round(expected_taken)` boundary across picks | **latent** — demonstrable, 0 of 627 real impact, **deferred** |
| `RANK_TAKE_PROBABILITY.get(rank, 0.0)` | **latent/unreachable** — correct default, coupling now enforced |
| my "8.2% one step from crossing" figure | **measurement artifact** — withdrawn above |

## Tests added, and why none is vacuous

Three, in `test_draft_strategy.PositionalForfeitsTests`. Each was verified to **fail** when the
property it pins is broken:

| test | probe that breaks it | result |
|---|---|---|
| `test_within_one_pick_summation_order_cannot_reach_the_decision` | swap in a table where a single-pick sum *does* flip `round()` — the probe searched and found `(0.05, 0.17, 0.28)`, which sums to 0.5 order-dependently | **FAILED** |
| `test_KNOWN_SENSITIVITY_the_round_boundary_is_decided_by_float_noise` | change the table so the fixture no longer lands on 1.5 | **FAILED** |
| `test_the_forfeit_depth_and_the_take_probability_table_stay_coupled` | raise `FORFEIT_OPPONENT_BOARD_DEPTH` to 8 | **FAILED** |

The first probe is itself a finding: a table exists — `(0.05, 0.17, 0.28)` — under which the
single-pick sum flips `round()`. **Today's immunity is a property of the current constants, not a
structural guarantee**, and `RANK_TAKE_PROBABILITY` is documented as a never-backtested starting
point. The test now stands between a future retune and a silent order dependence.

## Invariants

148. A quantity that is rounded for display and rounded again for a decision must not be read
     back from the display value. The two roundings answer different questions and the displayed
     one has already lost the information the decision depends on.
149. Where a hard boundary (`round`, a threshold, an index) sits on a value that a float
     accumulation can reach exactly, the boundary's behaviour is stated or measured — not left
     to the last bit. Measuring it is enough when the measured impact is zero; a rule is required
     before it is not.
150. Two constants that must move together are asserted to move together. A comment describing a
     coupling documents an intention; only a test enforces one.
151. Immunity that follows from the current values of a tunable table is recorded as contingent,
     and pinned, rather than reported as a structural property.

---

# Appendix — D: the decision-boundary information audit

**Verdict: ALREADY REPRESENTED.** No production change. One architectural contract test added,
plus documentation. The engine consumes what its own contracts say it should; what is missing at
the boundary is *explanation*, not *decision input*, and no candidate cleared the bar of a
measurable decision consequence.

## The decision boundary, exactly

`pick_synthesis.build_snapshot(...) → PickSnapshot`. It is **singular and closed**:

| consumer | signature | can it reach the engine? |
|---|---|---|
| `pick_debate.debate_pick` | `(snapshot, *, previous_snapshot, role_providers, api_keys, role_models)` | no — imports only `llm_engine` and `pick_synthesis` types |
| `draft_board_ui.serialize_snapshot` | `(snap, *, pick_header, state_tags)` | no — `design_system`, `player_universe.FLEX_SLOT_POSITIONS`, and **one constant** from `draft_room` |
| `screen_context.build_draft_room_context` | `(snap)` | no — imports only `pick_synthesis.PickSnapshot` |
| `decision_log.log_decision` | `(league_id, question, verdict, moderator_text)` | no |

No consumer imports `data_merger`, `draft_strategy`, `lineup_optimizer`, `rookie_draft`,
`depth_ratings`, `lineup_readiness`, `roster_diagnostics` or `sleeper_client`. That closure is
what makes "which fields cross" a well-posed question, and it is what makes the debate's own
instruction to the models — *"the candidates below are the ONLY real numbers available"* —
structural rather than aspirational. **Now pinned by test.**

There is a **second** boundary worth naming, because it loses far more than the first:
`PickSnapshot → each consumer's own projection of it`.

## Boundary 1: engine → decision object. Near-lossless.

Of 19 board-row fields, **4 do not cross**, and of 13 `pick_analysis` fields, **0 do not cross**:

| field | class |
|---|---|
| `mode` | constant metadata — **redundant (6)** |
| `injury_status` | **discarded (3)** — see below |
| `risk_adj` | **discarded (3)** — the injury term |
| `time_horizon_adj` | **discarded (3)** — the dynasty-age term |

`universal_value = bpa + time_horizon_adj + risk_adj`, and the snapshot carries both
`universal_value` and `bpa`, so the **sum** of the two adjustments is recoverable inside the
object. Only the **split** is lost: an age penalty and an injury penalty are indistinguishable.

## Boundary 2: decision object → consumers. The two see different things.

Read off both formatters by AST, not by matching values in output text (see the self-review):

| | fields |
|---|---|
| **reach neither** | `bpa`, `rival_premium_take_probability` |
| **UI only** | `rival_premium`, `cliff_protection`, `block_opportunity`, `pure_value`, `context_elevated`, `waiting_cost`, `horizon_floor`, `horizon_sensitivity` |
| **debate only** | `bpa_source`, `confidence`, `opportunity_cost`, `expected_value_of_waiting`, `denial_value`, `position_expected_taken`, `position_run_detected`, `pick_necessity`, `consensus_rank`, `consensus_tier`, `reach_label` |

The four **decision-path flags** — the fields literally named for the decision path — reach the
human on the board UI (as `_forces` ticks and the `_context_gap` glyph) and **never reach the LLM
debate that produces the recommendation**. That asymmetry is a real architectural fact and is
recorded here; it is not called a defect, because the flags are derived from numbers the debate
already sees, and re-stating a derived boolean to a reasoner that has the inputs is a
presentation choice, not an information gap.

## The strongest candidate: injury status

**What it is.** Sleeper's `injury_status`, read straight off the players_db onto every board row,
driving `RISK_ADJ = {IR: −18.0, Out: −10.0, Doubtful: −5.0, Questionable: −1.5}` (dynasty-scaled).

**Where it exists / where it is lost.** On the board row at the decision point; neither the status
nor `risk_adj` crosses boundary 1, and neither consumer mentions injury anywhere.

**Controlled experiment** — same board, same candidate set, only `injury_status` varied on the
leader (D Goedert, TE):

| injury_status | universal_value | TAV | rank | moved | any consumer states the reason |
|---|---:|---:|---:|---|---|
| None | 14.75 | 19.08 | 1 | — | NO |
| Questionable | 13.25 | 17.58 | 1 | no | NO |
| Doubtful | 9.75 | 14.08 | **5** | yes | NO |
| Out | 4.75 | 9.08 | **21** | yes | NO |
| IR | −3.25 | 1.08 | **43** | yes | NO |

**Independent decision value: none.** This is the crux. The engine's *ordering is already
correct* — it moves an IR player from first to forty-third. Nothing about adding the label
changes which candidate the engine ranks highest, and `_best_alternative` in the debate is
computed deterministically from TAV, not from prose. What is missing is the **explanation**: a
reasoner told "do not recompute" sees a 4.75 where a 14.75 belongs and cannot recover why.

**Should production change: no.** Under this audit's own standard, an explanation gap with no
measurable decision consequence is documented, not built. Recorded as **category 3 — available
upstream, discarded at the boundary, engine-correct, presentation-incomplete.**

## Negative findings — investigated, and they do not justify a change

* **Role / usage / handcuff data.** Re-confirmed at source: the canonical projections table has
  **19 columns**, none of them snaps, touches, targets, carries, depth-chart order, games
  started, or player-to-player linkage. **Category 4 — unavailable.** Unchanged from H3; nothing
  to manufacture.
* **`pick_analysis` output.** Zero fields lost. The strategy layer's entire product crosses.
* **Future picks.** Picks are not candidates; the six decision modules contain zero pick-asset
  references. Already settled at #85 and not reopened.
* **Lineup marginal.** Settled at H2 and not reopened; D found no dependency requiring it.
* **`horizon_floor` / `horizon_sensitivity`.** Cross boundary 1, reach the UI through
  `_waiting_note`. **Not stranded.**
* **`bpa`.** Reaches neither consumer, but `universal_value` (which contains it), `bpa_source`
  and `confidence` all reach the debate. **Category 6 — redundant** for the consumer's purpose.
* **Consensus / market data.** `consensus_rank`, `consensus_tier`, `reach_label` cross and reach
  the debate — but only in a **superflex** league, since `_consensus_lookup` is gated there. In
  this fixture's non-superflex league they are `None` throughout. Correct by contract
  (**category 5**), and worth knowing when reading any measurement that shows them empty.

## A correction to open item #57

The backlog records *"`waiting_cost` never reaches the debate layer (computed, displayed, not
consumed)."* Measured: `waiting_cost` **crosses boundary 1 and reaches the UI**, where
`draft_board_ui._waiting_note` renders it as the replaceability sentence. The accurate statement
is narrower: it does not reach the **LLM debate prompt**. The item is not wrong about the debate;
it is wrong if read as "reaches nothing".

## Self-review of this investigation's own measurements

Four errors found in my own work, all corrected above rather than quietly dropped:

1. **Fixture artifact.** A first probe reported `injury_status` as **0/237 populated** and
   `risk_adj` as uniformly `0.0`. That was **my synthetic `players_db`**, which never set the
   field — not a production fact. Production reads it straight from Sleeper. Re-run with the
   field populated, and it is the strongest candidate in the audit.
2. **Value-matching artifact.** My first boundary-2 pass detected "does this field reach the
   consumer" by searching for the field's *value* in the output text. It produced false
   negatives (`pick_necessity` prints as `X/100`, `positional_cliff` as a dict, `near_tie` as
   prose) and false positives (a coincidentally matching number). Replaced with an AST read of
   the two formatters, which is what the table above reports.
3. **Substring artifact.** `"candidate.bpa" in pick_debate.py` returned true by matching
   `candidate.bpa_source`; `"injury" in draft_board_ui.py` matched an unrelated docstring. Both
   re-checked by attribute-level AST and corrected.
4. **A voided measurement.** I measured whether `depth_ratings.depth_label` carries information
   `need_bonus` does not, and got "85% independent". **That result is withdrawn.** The output is
   internally contradictory: it pairs `need_bonus = 4.33` (which implies one player already held
   at a three-slot position) with `depth_label = "None — no rostered players here"` (which
   implies zero). My roster reconstruction counts by a player's single `position` while the
   engine's need computation counts by reachable slots, so the two sides were counting different
   things. `depth_label`'s independence from `need_bonus` is therefore **not established either
   way** — it needs a measurement that reads the engine's own positional counting rather than
   rebuilding it. Recorded as open, not as a finding.

## Invariants

152. The decision boundary is closed: `PickSnapshot` is the only object crossing from the engine
     to anything that decides, and no consumer may import a module that could re-derive a value
     the snapshot already fixed.
153. A field's presence in the frozen object is not the same as its arrival at a consumer. Each
     consumer projects the object, and the projections differ; "reaches the decision" is asked
     per consumer.
154. Whether a field reaches a consumer is read from the consumer's own code, never inferred by
     looking for its value in rendered output. Formatted values and prose defeat the inference in
     both directions.
155. A measurement built on a reconstruction of engine state is checked against the engine's own
     state before its result is reported. Where the two count differently, the result is void.
156. Missing *explanation* and missing *decision input* are different findings. The first is
     documented; only the second can justify changing what the engine computes.

---

# Appendix — E: ablation over the decision, not over a label

**Verdict: ALREADY REPRESENTED — the architecture survives ablation.** No production change.
One contract test added (4 tests), plus this appendix. No defect found; the ablations confirm
what the contracts claim, and they upgrade three of those claims from asserted to demonstrated.

## What E is actually testing, and what already existed

`cdme_force_ablation.py` already ablates — but it ablates `compute_pick_necessity`'s six terms
and measures which `necessity_label` bucket a candidate lands in. **`pick_necessity` does not
participate in ranking**: `narrow_candidates` orders by `_board_order → final_score`, and nothing
re-ranks on necessity (that is open item #55, still open). So the existing battery measures
whether a **label** moves, which is precisely what E's mandate says not to settle for.

E therefore ablates the thing that decides: the **ordered candidate list** and every **TAV**.
Ablation is applied through the real pipeline at its seams (monkeypatched in the harness, no
production edit) and — for the scoring terms — at the **board** level, so candidate *selection*
responds too; a post-hoc re-rank of an already-selected set would understate the effect.

## Part 1 — the contextual layer is provably non-scoring

Each contextual signal suppressed at its own seam, then all of them together, across 12 real
decision states (rounds 4/9/14 × 4 rosters):

| ablation | order changed | TAV changed | leader changed |
|---|---:|---:|---:|
| survival + opportunity cost + denial + rival premium | 0/12 | 0/12 | **0/12** |
| positional forfeit | 0/12 | 0/12 | **0/12** |
| positional cliff | 0/12 | 0/12 | **0/12** |
| positional run | 0/12 | 0/12 | **0/12** |
| `pick_necessity` flattened | 0/12 | 0/12 | **0/12** |
| decision-path flags cleared | 0/12 | 0/12 | **0/12** |
| near-tie flags cleared | 0/12 | 0/12 | **0/12** |
| **all of the above at once** | **0/12** | **0/12** | **0/12** |
| *positive control:* `bpa` zeroed | **12/12** | — | — |

The control is the point. A null result from an insensitive harness is worthless; this harness
moves every state when a scoring term is removed, and no state when a contextual one is. **The
separation between the valuation layer and the debate layer is now demonstrated by ablation
rather than asserted by docstring.**

## Part 2 — what actually decides

`TAV = universal_value + need_bonus + eligibility_bonus`, and
`universal_value = bpa + time_horizon_adj + risk_adj`. Ablated at board level:

| component removed | leader changed | top-3 set changed | leader changed, near-tie states |
|---|---:|---:|---:|
| **`bpa`** | **12/12 (100%)** | 12/12 | **8/8** |
| `time_horizon_adj` + `risk_adj` | **6/12 (50%)** | 8/12 | 4/8 |
| `need_bonus` | **4/12 (33%)** | 5/12 | 2/8 |
| both roster terms | 4/12 | 5/12 | 2/8 |
| `eligibility_bonus` | 0/12 — **withdrawn, see self-review** | — | — |

Worked reversals: at round 4 rosters 3 and 4, removing `need_bonus` flips G Kittle → D
Montgomery; removing the dynasty adjustment flips J Johnson → R Dowdle at round 9.

Three things follow. **`bpa` is dominant** — consistent with the earlier finding that the ruler
carries 94.5% of BPA's movement (#76). **The dynasty horizon layer is not decorative**: removing
it changes the recommendation in half of all states and half of the close ones. **`need_bonus`
earns its place**: a third of leaders, without ever dominating a real value gap — the same
picture H1 measured from the other direction.

## Self-review of this investigation's own measurements

**One result withdrawn, for a reason worth recording.** `eligibility_bonus` measured `0/12` on
every axis — order, TAV, leader. Reported as-is that would read "inert". It is not:

1. First check — my synthetic `players_db` sets `fantasy_positions=[position]` for every player,
   and `eligibility_bonus` is **0.0 by construction** for a single-position player. Fixture
   artifact, same class as D's injury-status artifact.
2. Second check, rebuilt with **48 multi-eligible players** — still `0/333` rows. Which looked
   like a real finding, and was also wrong: I measured on the **opening board**, where every
   lineup slot is empty. That is **H2's degenerate regime** — the full-eligibility and
   primary-only solves are the identical problem, so their difference is exactly zero.
3. Third check, at populated rounds, is the honest one:

| round | rows with `eligibility_bonus ≠ 0` | largest |
|---|---|---|
| 0 | 0 / 333 | — (degenerate by construction) |
| 4 | **7 / 285** | J Ferguson (TE) **+2.76** |
| 8 | **13 / 237** | J Croskey-Merritt (RB) +2.04 |
| 14 | 1 / 165 | J Tyson (WR) +1.20 |

So it fires on roughly **2.5–5.5%** of rows, at magnitudes **at or below `NEAR_TIE_BAND = 2.0`**
for all but the largest — far under its own `ELIGIBILITY_BONUS_MAX = 12.0` cap, which is a bound
and not a threshold (#56). Its decision reach is **small but non-zero**; its production frequency
depends on how many real Sleeper rows carry multiple `fantasy_positions`, which this environment
holds no cache to measure — the same honest limit as #85's `traded_picks` and D's injury reach.

Two artifacts in a row on the same term is itself the lesson: **a zero from an ablation is only
evidence if the fixture can exercise the term, and being able to exercise it means avoiding both
an impoverished input and a degenerate regime.**

## Negative findings

* No leakage. Every contextual signal is inert on the ranking, individually and jointly.
* No defect in `cdme_force_ablation.py` — it is accurate about what it computes. What is
  recorded here is the limit of what it can conclude: it measures a label, not a decision.
* H3 / role data stays **parked as data-blocked**, not rejected, and was not touched.
* D's closed `PickSnapshot` boundary held throughout; E produced no dependency contradicting it.

## Tests added

`ContextualSignalsCannotReachTheRankingTests` (4 tests) pins the mechanism rather than re-running
the pipeline — the full ablation is minutes of compute and belongs in the record, not the suite.
It asserts `_board_order` is invariant to 24 contextual fields at once (priced and unpriced rows),
that it still responds to the two things it may read, and that `narrow_candidates` returns a
deliberately mis-ordered board in `final_score` order even when the weakest row carries every
contextual signal at maximum.

**Non-vacuity, demonstrated:** injecting a one-line leak into `_board_order` — adding
`pick_necessity` to the sort key — failed 2 of the 4 tests
(`(False, -42.0, 'p1') != (False, -142.0, 'p1')`, and `'weak' != 'best'`). Probe reverted.

## Invariants

157. The recommendation is the head of a list ordered by `final_score` and `player_id`. A signal
     that is not one of those two cannot change the recommendation, and any claim that it does
     is a claim that the sort key changed.
158. An ablation reporting no change is evidence only alongside a positive control that does
     change. Without one, an insensitive harness and a genuine null are indistinguishable.
159. An ablation of a term is evidence only if the fixture can exercise that term — which
     requires both an input rich enough to trigger it and a state outside its degenerate regime.
160. Ablating a quantity that no consumer ranks on measures the quantity's own label, not the
     decision. The distinction is recorded whenever an ablation battery is cited.

---

# Appendix — the research fixture: contract written, capture BLOCKED

**Status: blocked on an external dependency this session cannot satisfy.** No fixture was
captured, and none was manufactured. What this pass delivers is the fixture *contract* and a
validator that enforces it, so a capture made elsewhere is immediately usable — and so an
inadmissible one is rejected before it produces a number.

## Why a real capture was the right next task

Four investigations in a row terminated at the same step — magnitude measured, reach
unmeasurable:

| investigation | measured | blocked on |
|---|---|---|
| #85 future-pick valuation | 64-point round-1 slot spread; flat price is the distribution's median | `traded_picks` |
| D injury status | rank 1 → 43 across the RISK_ADJ range | real `players_nfl.injury_status` |
| E `eligibility_bonus` | fires on 2.5–5.5% of rows, max +2.76 | real `fantasy_positions` multiplicity |
| #87 peer-relative depth | measurement voided | real rosters + engine slot semantics |

Reach is exactly what separates DOCUMENT from WIRE under this program's standard, so the
binding constraint stopped being analysis and became fixtures.

## The block, characterized precisely

`api.sleeper.app:443` is denied by **organization egress policy** — the gateway answers **403
to CONNECT**, recorded in the proxy's own `recentRelayFailures`. This is not a TLS or trust
problem and not transient: general egress from this session works (`pypi.org` 200,
`raw.githubusercontent.com` 301). The proxy README is explicit that policy denials are to be
reported, not retried.

No prior capture exists to fall back on. `data/sleeper_snapshots/` has carried only a
`.gitkeep` since the initial commit, and no JSON containing `traded_picks` appears anywhere in
any branch's history.

**Nothing was fabricated to fill the gap, and that is a finding, not an omission.** A
hand-built "realistic" fixture would encode this session's own assumptions about precisely the
distributions being measured — injury prevalence, multi-eligibility rate, traded-pick frequency
— and the resulting reach numbers would be invention wearing the costume of evidence. This
audit has already caught itself four times reporting a fixture's property as an engine
property; manufacturing the fixture that answers the reach question would be that same error
committed deliberately.

## The fixture contract

**Must be present and non-normalized** — these *are* the measurement:

| field | unblocks |
|---|---|
| `rosters[].players`, `rosters[].starters`, `league.roster_positions` | #87 peer-relative depth, real slot eligibility |
| `rosters[].settings.wins` / `.losses` / `.ties` | #85 (the record the estimator reads) |
| `traded_picks[].{season, round, roster_id, owner_id}` | #85 reach — which picks are even enumerable |
| `players_nfl[].injury_status` | D reach |
| `players_nfl[].fantasy_positions` | E reach |

**Safe to redact**: `display_name`, `avatar`, `user_id`, league name, free-text `metadata.*`.

**Admissibility is stronger than well-formedness.** A dimension counts only if the fixture can
*exercise* it: a snapshot with zero traded picks cannot answer #85's reach question, a
players payload with no `injury_status` cannot answer D's, and a single-position payload cannot
answer E's — regardless of how complete the schema looks. `run_fixture_validation.py` enforces
exactly this and refuses the fixture otherwise.

Validated in both directions: the synthetic shape that fooled this audit (well-formed, 10
rosters, 40 players, every key present) is **rejected** on all four reach dimensions, and a
shape carrying real variation is **admitted**. The validator has no generation mode by design.

## Invariants

161. A reach question is answered only from a fixture that can exercise the dimension it asks
     about. Schema completeness is not exercisability, and a well-formed fixture that cannot
     vary the quantity under test yields a property of the fixture.
162. Where the data required to answer a question cannot be obtained, the question stays open
     and the blocker is named. Synthesising the input is not a substitute for acquiring it,
     most of all when the synthesis would have to assume the very distribution being measured.

---

# Appendix — §3 + §4: canonical state, decision-context handoff, chair contracts

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 2). This entry records only the
measurements, the corrections, and the invariants they establish.

## What was measured, and how

Chair inputs were measured rather than read: `llm_engine.PROVIDER_CALLERS` was stubbed and the
real `ask_*` functions called, recording the exact `(system_prompt, user_prompt)` each chair
received.

| measurement | result |
|---|---|
| Quant's user prompt vs Beat's, identical input | **byte-identical** |
| chairs receiving the base context block verbatim | 4 of 4 (and 3 of 3 in `pick_debate`) |
| distinct system prompts | 4 of 4 |
| what a downstream chair receives beyond the shared base | prior chairs' **prose only** |

Handoff reach, on a real board (12-team superflex, committed vendor data, rounds 1/4/8):

| measurement | result |
|---|---|
| `render_debate_chip` call sites | 7 |
| reads of `debate_attached_context` in the tree | 2 — one write, one **render** |
| production callers of `ScreenContext.to_prompt_seed` | **1** (Trade Calculator) |
| engine fields from `build_draft_room_context` present in `build_context` | **0 of 16** |
| `build_context` parameters | `snapshot, roster_table, player_universe, question, conversation_window` — no draft argument |
| fields: `CandidateSnapshot` → iframe payload → chip line | **37 → 22 → 5** (chip capped at 8 rows) |
| TAV fidelity: engine → `pick_debate` → chip | `84.44` → `84.44` → `84` |
| adjacent engine-ordered pairs collapsing to one displayed integer, within the 8 rendered rows | 1/7 (rd 1), 4/7 (rd 4), 2/5 (rd 8) — **all within `NEAR_TIE_BAND = 2.0`** |
| `PickSnapshot` identifier field | **none** — no id, hash, or computed-at timestamp |
| context string persisted on any invocation | **none** |

## Two corrections to this pass's own method

**The constants scan was vacuous on its first run and reported a false clean.** It walked only
`ast.Assign`, so `COMPOSITE_SOURCE_WEIGHTS` — an `ast.AnnAssign` — was invisible, and the scan
returned 0 hits in `build_context` where there is 1. A constants scan blind to annotated
constants would have shipped as proof of a property it could not observe. Both forms are handled
now, and `test_annotated_constants_are_discovered` pins the specific case.

**Two "PRESENT" results in the reach scan were substring artifacts.** `team_label` and `surface`
matched inside `build_context` — the first in an unrelated positional-depth loop, the second
inside the word "surfaced" in prose. Both were checked by hand and discarded. The same artifact
class that voided the D measurement (`"candidate.bpa"` matching `bpa_source`), caught earlier
this time because it was looked for.

## A correction to the scope of a Pass 1 conclusion

§13.4 concluded that an AI seat cannot mutate, recompute, or override deterministic values. That
holds **for the CDME valuation path**, and this pass located the mechanism: `draft_room:518` and
`pick_synthesis:413` filter `merger.external_values` to `source_name == "keeptradecut"`, keeping
`bot_research.json`'s LLM-originated rows out of the engine — enforced by
`test_cdme_ingestion_boundary.py`.

There is nonetheless **one designed path** by which model output becomes a number in a
deterministic calculation: ranked `bot_research` findings load as a synthetic external source and
enter `composite_player_score` at weight **0.5**, the lowest of any source. The composite surfaces
in the Trade Calculator and in `build_context`. This is deliberate, weighted, deduped, gated on
the Moderator's non-dispute rule, disclosed to the chairs, and excluded from CDME. It is not a
defect — but "the AI cannot affect any deterministic number" is a stronger claim than the
architecture makes, and the record should carry the accurate one.

## Tests added

`test_prompt_constant_boundary.py` — 10 tests. Discovers 56 engine constants across six modules
by AST and scans them against all 16 provider-reachable prompt strings plus `build_context` and
`screen_context` literals. Non-vacuity demonstrated by planting, in real production text and
reverting: a constant name in `QUANT_SYSTEM_PROMPT` (**FAIL**), a `RANK_TAKE_PROBABILITY` value in
`build_context` (**FAIL**), and the composite weights beside their one allowed name (**FAIL**).
The suite also fails if constant discovery collapses, if the prompt surface shrinks below 16
producers, or if any of the seven chairs stops being scanned.

## Invariants

163. A canonical context object that is built and displayed but not passed is not a handoff. The
     test of a decision-context contract is what the consumer receives, never what the builder
     assembled — and a surface that tells the user its context was handed over has made a claim
     the wiring must satisfy.
164. Chair separation carried only by a system prompt is instructional. Where every chair
     receives byte-identical input, the division of labour is a request to the model, not a
     property of the architecture, and it degrades silently under model substitution.
165. A chair handover that passes prose passes a summary, not evidence. A replacement model
     inherits its predecessor's conclusions and cannot audit them; a per-chair evidence record is
     what makes chairs interchangeable rather than merely re-assignable.
166. An invocation that does not record its input cannot be replayed, and a frozen object without
     an identifier cannot be referenced after the process that made it. Immutability and
     addressability are separate properties, and provenance needs both.
167. A boundary is enforced only by a check that has been shown to fail. A scan whose discovery
     step is incomplete — an AST walk missing an assignment form, a surface enumeration missing a
     producer — reports the absence of what it cannot see, and reads as proof.

---

# Appendix — §5: model selection, optimization, unknown-model evaluation

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 3). This entry records the
measurements, the corrections, and the invariants.

`bot_benchmark.py` is a real methodology, not a stub: fixed per-chair battery, per-chair weighted
rubric, blind judge, persisted report. Everything below is about its *envelope*.

## What was measured

No provider was called. Every figure comes from the real production parsers, a stubbed provider
caller, or source inspection.

| measurement | result |
|---|---|
| chairs with a battery | **4 of 7** (Prytaneum four; Draft Room's strategist/skeptic/caller have none) |
| system prompt the battery runs under | `llm_engine.ROLE_SYSTEM_PROMPTS[role]` — the production object, not a copy |
| benchmark user-prompt size | quant 244–531 · beat 331–428 · contrarian 249–271 · moderator 628–973 chars |
| production comparable | `pick_debate` evidence block **29,828–52,766** chars on real boards |
| benchmark user-prompt shape | the bare scenario string; production always wraps as `"League/roster context:\n…\n\nQuestion: …"` |
| judge prompt contents | task + response + rubric; none of `gemini`, `openai`, `anthropic`, `claude-opus`, `gpt-4o` |
| moderator rubric dimensions | `synthesis`, `disagreement_handling`, `clarity`, `actionability` — no accuracy, no format |
| moderator battery prompts asking for the structured block | **0 of 3** |
| production parsers referenced anywhere in `bot_benchmark` | **0 of 4** |
| report keys | `{role, ran_at, judge_provider, judge_model, candidates}` — no version, no cost |
| `save_report` | `all_reports[role] = report` — overwrite, no history |
| ranking key | `score` only; latency recorded, never scored |
| provider fallback on failure | none |

A fluent, on-topic Moderator answer omitting the structured block, run through the real
production parsers: `parse_moderator_verdict → {}`, `parse_todo_directives → {"updates": [],
"likely_resolved": []}`, `parse_source_findings → []`, `parse_source_comparisons → []`. The same
answer *with* the block parses (`recommendation: HOLD`, `conviction: Majority`), so the gap is in
the benchmark and not in a dead parser. Downstream: `log_decision` returns early on
`if not league_id or not verdict`, `add_todo` is never called, `bot_research` gains nothing, and
`format_agent_content` renders the reply as prose with no verdict card — none of it raising,
because `result.errors` only collects `⚠️`-prefixed responses.

## Corrections

**A hypothesis of mine that was wrong, recorded before it became a finding.** From the
self-contained battery scenarios I concluded the benchmark ran with tools disabled while
production Beat had live search, and was about to report that mismatch. False:
`PROVIDER_CALLERS` grants web search to all three providers unconditionally and the benchmark
uses those same callers. The real finding is the opposite shape — the grant is uniform across
*chairs*, including the Quant, whose prompt forbids fetching. A tidy wrong answer was one file
read away from being published.

**A third substring artifact.** Testing whether the tool grant was role-conditional, a naive
`"role" in source` returned `True`, matching `messages=[{"role": "user", …}]` and a comment.
Verified properly: no caller takes a role parameter and the grant is a literal in the request.
Same class as D's `candidate.bpa` / `bpa_source` and Pass 2's `team_label` / `surface`.

**Two scratch-probe slips, caught before they reached a conclusion.** A line-filter meant to
print `log_decision`'s guard returned `[]` (the guard spans two lines), and a "does the report
record a battery version" check was a docstring substring match that returned `True` when no
such field exists. Both were re-verified by hand; neither reached the record as a finding.

## Tests added

`test_benchmark_contract_coverage.py` — 19 tests, in two deliberately separate postures.

**Enforcement.** `JudgeBlindnessTests` makes the module's own stated key safeguard a property
rather than a convention: the judge prompt carries task, response and rubric and no candidate
identity, and `_judge_response`'s parameter list is pinned so a future argument carrying
identity fails. `BenchmarkCoverageTests` pins chair coverage, that the battery runs under the
production prompt object, the report's exact key set, and the overwrite-not-append behavior.

**Characterization.** `ModeratorContractIsNotBenchmarkedTests` records a KNOWN GAP — today's
behavior, deliberately asserted, to be **inverted rather than deleted** when repaired, the same
posture as the round-boundary characterization in `test_draft_strategy.py`.

Non-vacuity, four probes planted in real production code and reverted: a candidate identifier in
the judge prompt (**FAIL**), a fifth Prytaneum chair with no battery (**FAIL**), a `cost` key on
the report (**FAIL**), and — confirming the characterization behaves as designed — adding a
`format` dimension to the moderator rubric (**FAIL**, demanding inversion).

## Repairs applied retroactively at the §6 boundary

Two §5 items qualified as safe and mechanical once the standing rule changed to implement before
advancing; the rest are decisions and were left.

**R3 + R4, done together.** A report now carries `battery_fingerprint`, `rubric_fingerprint` and
`chair_prompt_fingerprint` (12-char content hashes computed at run time, not hand-maintained
version numbers), and `save_report` keeps `HISTORY_LIMIT = 20` runs per role instead of
overwriting. `load_report` still returns the newest, so no reader changed. `comparable_history`
returns only runs sharing the newest one's three fingerprints. Together these convert "repeatable"
and "versioned" from absent to present; separately, history alone would have been a trend across
different experiments, which is worse than no trend.

**R5, half of §5.6.** `run_benchmark` records `contract_ok` per question using the real
production `parse_moderator_verdict`, and `any_contract_failure` per candidate, surfaced in the
benchmark UI. `None` where a chair has no machine contract, and `None` on a failed call so one
problem is not counted twice. The score is untouched, and a test pins that identical rubric scores
rank identically regardless. Gate-versus-flag stays open: it changes which model wins.

Non-vacuity: four probes planted in real code and reverted -- making `contract_ok` feed the score,
reverting history to overwrite, freezing the battery fingerprint, and returning `False` rather
than `None` for a chair with no machine contract. All four failed.

## Invariants

168. A benchmark measures a chair only to the extent its inputs match that chair's real
     operating envelope. An identical system prompt establishes the contract; a toy user
     message two orders of magnitude smaller than production establishes nothing about
     capacity, and a model cannot be disqualified on a dimension the battery never exercises.
169. Where a chair's output is consumed by machine, the machine contract is part of the job and
     must be checked deterministically, by the production parser, not scored by a judge. A
     selection methodology that ranks only prose can recommend a model that silently breaks
     every downstream consumer.
170. A stored evaluation is comparable only against inputs and grading criteria that are
     recorded with it. Results held against code that moves underneath them cannot be replayed,
     and a score history over unversioned batteries is more misleading than no history at all.
171. Chair-level scores do not compose. A model chosen for its own output can degrade the chair
     that consumes it, and only a chain-level evaluation can see that.
172. Equalizing a capability across chairs normalizes comparison and forfeits measurement of
     that capability. Both are real; which one is wanted is a decision, and it should be
     recorded as one rather than inherited from a convenience.

---

# Appendix — §6: external research, evidence, canonical ingestion

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 4). This entry records the
measurements, the corrections, and the invariants.

**Reach first, because it bounds every severity.** `data/baseline/bot_research.json` and
`bot_comparisons.json` do not exist, are not tracked, and are not gitignored;
`load_bot_research_as_external()` returns 0 rows. Nothing has ever been ingested this way here.
Every §6 finding is latent.

## What was measured

| measurement | result |
|---|---|
| admission tiers, research → CDME | 4 (prose / log / composite / CDME), each with its own rule |
| what reaches the composite | only findings whose `rank is not None` |
| comparisons' composite impact | the literal string `"none"`; no percentile rule exists for them |
| total contributing source weight today | **3.532** across draftsharks 1.213, fantasypros 0.881, dynastyprocess 0.822, keeptradecut 0.616 |
| loaded but excluded (no percentile rule) | `espn/idp_redraft_rankings.csv`, `fantasypros/best_ball_rankings.csv`, `fantasypros/idp_redraft_rankings.csv`, `dynastyprocess/picks.csv` |
| a finding written today, pool N=1 | weight 0.025 → **0.7%** of the blend |
| a finding written today, pool N≥20 | weight 0.500 → **12.4%** of the blend |
| vendor staleness before a fresh finding outweighs it | keeptradecut **29.1d**, dynastyprocess/fantasypros 60.0d, draftsharks 82.7d |
| research frame columns | `name, norm_name, source_name, source_file, cited_source, claim, rank, source_date` — **no team, no position** |
| two findings on one player, two cited sources | 2 rows, `norm_name` not unique, `_resolve` → `candidates=2, verified=False`, `_find_match` → the older ESPN row; the other dropped with no conflict recorded |
| disambiguation by `position=` / `team=` inside that frame | **impossible** — all four call shapes resolve identically |
| lifecycle state on a finding | none — `composite_impact` is a routing label, not a state |
| evidence snapshot fields (url / retrieved_at / excerpt) | **absent**; the evidence is a source name plus the Moderator's paraphrase |
| `validated` on a comparison | hard-coded `True` on every write; **one write, one test read, no production consumer** |

## Corrections

**A finding of mine that was wrong in its general form, caught by two call-site reads.** I
measured that `composite_player_score` resolves every source through `_find_match` — which is
`_resolve(...)[0]`, the row with `verified` discarded — and that 19 of 19 colliding names in the
committed `projections` table still produce a composite. Both measurements are correct; the
conclusion drawn from them was not. Production guards it at both call sites: `data_merger:2284`
passes `position=` and `team=`, and `app.py:3548`'s next block drops `external` and `composite`
outright when `merge_player` reports `match_verified == False`, for exactly this reason. Only
**4** of the 19 differ materially on the composite-relevant field, and all four are
cross-position collisions the roster path resolves by position. The surviving finding is narrower
and real: the `bot_research` frame specifically cannot be disambiguated by either guard, because
it carries no team or position and the Trade Calculator's guard reads a different table.

**A `validated` flag that looks like §13.3 and is not.** `add_comparison` writes
`"validated": True` unconditionally, asserting a panel-scrutiny gate the code cannot verify —
structurally the same shape as the alias `verified=True` that #89 repaired. It is DOCUMENT rather
than a defect for one reason only: §13.3's flag was consumed and changed a price, and this one has
no production consumer at all. Recorded because "same shape as a known defect" is exactly the
inference that needs a reach check before it becomes a finding.

**A weighting table I had to redo.** The first composite-share measurement counted one row per
`source_name`, which wrongly included ESPN (loaded, but with no percentile rule it never becomes
a component) and collapsed multiple files per source. Corrected to `(source_name, source_file)`
pairs present in `_EXTERNAL_PERCENTILE_RULES`; the total moved 4.412 → 3.532 and the fresh-finding
share 10.2% → 12.4%.

## Tests added

`test_research_ingestion_boundary.py` — 19 tests, two postures, every on-disk test redirected to a
temp store so none can leave a research file in `data/baseline/`.

**Enforcement:** research carries the lowest source weight of any source; the pool-size floor
dampens a small pool proportionally; an undated source gets 0.5, never full trust; a qualitative
finding never reaches the composite while a numeric one does; comparisons have no percentile rule
and are excluded from the upload-refresh targets; newest-wins holds within a cited source;
same-day duplicates dedup on write; a blank finding is a no-op.

**Characterization (KNOWN GAPS — invert when repaired, do not delete):** the frame is not
name-injective and carries nothing to disambiguate with; `composite_player_score` reads the row
without the flag while `_resolve` still reports the collision correctly; a finding carries no
lifecycle state and no evidence snapshot; `validated` is written unconditionally, and a companion
test fails the moment anything starts reading it.

Non-vacuity, five probes planted in real production code and reverted: raising the research weight
above KeepTradeCut (**FAIL**), admitting rank-less findings (**FAIL**), giving comparisons a
percentile rule (**FAIL**), adding a `position` column to the frame (**FAIL** — the known gap
closed, demanding inversion), and adding a function that reads `validated` (**FAIL**).

## Repairs applied at the §6 boundary

Two, both correcting a statement rather than a computation.

**R1.** `add_comparison` wrote `"validated": True` on every entry. The writing path cannot
establish that -- the "panel-scrutiny gate" is the Moderator choosing to emit a line, and nothing
here re-adjudicates it. Renamed to `panel_undisputed`, which is what is actually known. This is
#89's rule applied where it next appears, not a new decision. Verified: reverting the rename
fails 2 tests; adding a reader of the new flag fails the guard that keeps it a provenance record.

**R2.** `load_bot_research_as_external`'s docstring said "newest wins" without qualification. The
rule is per (player, cited source) key; across cited sources both rows survive and the OLDER one
wins the composite component. Docstring corrected and pointed at the characterization test.
Documentation only.

Not applied, because each needs a decision rather than a fix: representing a disagreement (6.4),
an evidence snapshot requiring the Moderator's contract to emit a URL (6.5), an independent
re-adjudication queue (6.2a), and a stated intent for the freshness crossover (6.3).

## Invariants

173. Ingestion is a ladder, not a gate. A claim may be good enough to reuse as context, not good
     enough to weight a score, and never good enough to enter the deterministic engine — and each
     rung needs its own admission rule, stated where the rung is.
174. A dampener is only a guarantee at the freshness it was reasoned about. A weight that decays
     with age and a source that is always dated today will cross, and the crossing point is a
     property of the constants that should be measured and stated rather than discovered later.
175. A store keyed by (subject, source) is not keyed by subject. Where two sources can speak about
     one subject, the frame is not name-injective, and a consumer that resolves by name alone
     silently picks one and discards a disagreement that was the most informative thing present.
176. A disagreement must be representable as a disagreement. Superseding, dropping, or averaging
     conflicting claims all destroy the signal that they conflicted, which is what a review
     process would have needed.
177. A claim without a retrievable source is unfalsifiable. Storing a source's name and a
     paraphrase preserves the assertion and discards the ability to ever check it.
178. A field asserting verification is a defect only where something consumes it. The same
     unconditional `True` is inert in one place and a wrong price in another, so reach decides
     the verdict — and an inert one still needs a test that fires the day it gains a consumer.

179. Record what a measurement was taken under, by content rather than by a version number
     somebody has to remember. A hash cannot drift out of sync with the thing it names; a
     version can, and silently.
180. A history of scores is only honest across runs whose inputs and grading criteria match.
     Retaining runs without retaining what they ran under produces a trend line over different
     experiments, which misleads more confidently than having no history at all.
181. Measuring a contract and scoring it are separable, and separating them is often the honest
     move. Recording a failure makes it visible to whoever decides; deciding what it costs is a
     different act, and one that changes outcomes.
182. Absent is not failed. A chair with no machine contract must record "nothing to satisfy",
     never "did not satisfy" -- and a call that errored already has its own signal, so counting
     it a second time as a contract failure overstates one problem as two.

---

# Appendix — §7: source legality, credibility, provenance, prompt-injection

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 5). This entry records the
measurements, the repairs, and the invariants.

The section's overall shape is the opposite of the previous ones: the protections here are
**better than the code claims for itself**, and were undefended by any test. The repair was to
make them enforced rather than incidental.

## What was measured

| measurement | result |
|---|---|
| literal outbound hosts in every production module | **`api.sleeper.app`, and nothing else** — no URL fetcher exists; all live research runs provider-side |
| committed baseline CSVs | 20; **9 carry a provenance record, 11 do not** |
| unattributed | all 10 Draft Sharks `rankings/*.csv` and the trade-value chart — i.e. the *primary* valuation input, while the four secondary sources are documented |
| composite source allowlist | bound **once** at module level (AST), zero subscript assignments, zero `update`/`setdefault`/`pop`/`clear` |
| every finding's filed source pair | one synthetic `("bot_research", "findings")`, whatever it cites |
| a hostile cited source (`an anonymous forum post`, a paywalled URL) | **accepted verbatim**; no `SOURCE_ALLOWLIST` / `PERMITTED_SOURCES` / `SOURCE_POLICY` exists |
| numeric surface of all directives | **two integers** — a to-do id and a rank, both `.isdigit()` gated |
| `TODO UPDATE: ../../etc \| x \| y` | parses to nothing |
| a directive naming an unknown or archived objective | no-op, returns `False` |
| a rewritten objective | prior text preserved in `revisions` |
| `TODO LIKELY RESOLVED` | sets `likely_resolved`, which is an **ACTIVE** status — only a person resolves |
| sentinel API key through all four chairs | in **neither** system nor user prompt; travels as its own argument; absent from a serialized benchmark report; `api_key` appears in none of the four persisting modules |
| `build_context` | one flat string from 54 `lines.append(...)`; **no** `<untrusted>`, `<data>`, fence or delimiter of any kind |
| the phrase "prompt injection" anywhere in the tree | **absent** — the five "injection" matches are script-injection in the iframe and context-injection of pinned messages |

## Repairs applied at the §7 boundary

Both convert an existing, correct policy from convention into enforcement. No behaviour changed.

**R6 — the written source policy is now required.** Every file-backed source in
`_EXTERNAL_PERCENTILE_RULES` must carry an `ATTRIBUTION.md` that names its source and states an
access/licensing posture. The four that exist are substantive records — DynastyProcess as GPL-3.0
open data from an unauthenticated endpoint, KTC and FantasyPros as behind normal site access with
a single stated facts-only-extraction policy, KTC's own API recorded as blocked and not
circumvented, ESPN held to the same posture for consistency. Adding a source without that record
now fails.

**R7 — the properties that actually bound retrieved content are pinned.** Credentials never reach
a prompt or a report; verdict fields are all `str`; the numeric surface is two gated integers; a
non-numeric id is dropped rather than coerced; an unknown id is a no-op; a rewrite preserves prior
text; a resolution stays pending for a person; no second outbound host exists.

Non-vacuity: five probes planted in real code and reverted, all failing -- a composite source
added without an ATTRIBUTION.md, a runtime mutator of the allowlist, a key inlined into the
Quant's prompt, a rewrite that stops preserving prior text, and a second outbound host.

Not applied, each a decision: a cited-source allowlist; fencing untrusted content (a delimiter the
chair prompts do not explain is decoration, so it is a joint change to `build_context` and seven
chair contracts); and writing provenance for the Draft Sharks exports, which asserts terms for a
paid subscription export that only the owner can state.

## A cross-section effect on an open decision

§7 changes the premises of the parked #94 (what a Moderator contract failure should cost). §5
framed it as a quality question. §7 establishes that the structured block is the **entire channel
through which model output acquires authority** -- rewriting an objective, proposing a resolution,
writing a rank into the composite, creating a to-do all run through it. So a Moderator that fails
its machine contract is inert on every authority path, and a compliant one is the one that can
rewrite a user's objectives and inject numbers. Disqualifying block-less models therefore selects
*for* models that exercise more authority. Surfaced, not resolved.

## Invariants

183. Delegating retrieval is an architectural boundary, not an omission. A system with no fetcher
     of its own cannot bypass a paywall, a login, or a robots directive, and that is a stronger
     guarantee than any policy it could write about its own crawling.
184. Naming a source and permitting a source are different acts. A chair may recommend; only code
     decides admissibility -- and a free-text citation that cannot create a percentile rule is
     contained even while it is unvalidated.
185. Where untrusted content and instructions share one channel, the boundary is whatever the
     parsers allow, not whatever the prompt asks for. Bound the numeric surface, gate the types,
     and the worst an injected directive can do is bounded with them.
186. A directive that proposes is safe in a way a directive that decides is not. Preserving what a
     record said before, and leaving a status pending for a person, turn an injected instruction
     into a recoverable suggestion -- protections worth naming as such even when they were built
     for usability.
187. Provenance coverage tends to be inversely proportional to how much a source matters. The
     input that is questioned least is the one documented last, and an audit should check the
     primary source before the secondary ones.
188. An undemonstrated leak is not a defect. Name it, pin what is demonstrated, and repair it when
     something else legitimately touches that path.

---

# Appendix — §9: context compaction, handoffs, model-specific budgets

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 6). This entry records the
measurements, the correction, and the invariants.

The section's mandate -- context limits may reduce supporting information but may not silently
omit mandatory deterministic state -- **holds, by proportion rather than by design.** There is no
input-token accounting anywhere. What protects mandatory state is that mandatory state is small.

## What was measured

Upper bound per Prytaneum invocation, derived from the caps rather than sampled:

| term | tokens | share |
|---|---|---|
| conversation memory (16 raw turns x MAX_TOKENS of replayed model prose) | **65,536** | **84%** |
| compacted memory block | 4,096 | |
| static instruction prose | ~2,800 | |
| panel findings + comparisons (30 + 30) | ~2,550 | |
| **every deterministic section combined** | **8,365** | 11% |
| chat attachments | 4,000 chars each, **count uncapped** | unbounded |

| measurement | result |
|---|---|
| input-token accounting anywhere | **none** -- no count_tokens / tiktoken / context_window / token_budget |
| `MAX_TOKENS = 4096` | **output** cap, identical for all 7 chairs and all 3 providers |
| compaction mechanisms | **1 model call** (history summarization) + **10 deterministic slices** |
| mandatory sections (roster, league depth, freshness, active objectives) | iterated whole -- verified by AST that each iterates a Name, never a Subscript |
| compaction destructiveness | **non-destructive** -- timestamped `pre_compact_` backup written BEFORE the overwrite; aborts entirely if the summarizer returns ⚠️ |
| per-model context policy | **none** -- every chair gets the same string whatever window its model has |
| deterministic retention priority | **none** -- fixed section order, nothing dropped when oversized |
| when context does not fit | provider errors -> `⚠️` string -> becomes that chair's REPORT, passed to Contrarian and Moderator; collected in `result.errors` and surfaced, so loud rather than silent |
| `stop_reason` / `finish_reason` / `incomplete_details` | **absent from `llm_engine` and `pick_debate`** |
| a verdict truncated mid-`RECOMMEN` vs one that never had a block | **identical** `parse_moderator_verdict` output: `{}` |

## A correction

`compact_league_history`'s docstring says "pruning the raw turns", and from that I formed the view
that compaction destroys the original history and was preparing to report it as this section's
defect. It does not: the complete pre-compaction file is written to a timestamped backup *before*
anything is overwritten, and the operation aborts if the summarizer fails. Two lines further into
the function disproved it. Second time in this programme the most tempting finding was one read
from being wrong -- the first was §6.4a's composite-ambiguity claim.

## Tests added

`test_context_budget_boundary.py` -- 16 tests. **Enforcement:** mandatory sections are iterated
whole (AST, not string matching); every supporting cap stays <= 30; the compaction backup is
written before the overwrite and the operation aborts on summarizer failure; the summarizer fails
soft so that abort can fire; `build_context` calls no model to shape itself; history summarization
is not routed through configurable roles; the output cap is shared by all providers and is not
back at the known-tight 1024. **Characterization:** no input-token accounting, no stop-reason
inspection, a truncated verdict indistinguishable from an unformatted one, no per-model policy.

Non-vacuity: five probes planted in real code and reverted, all failing -- capping the roster,
writing the backup after the overwrite, dropping MAX_TOKENS to 1024, adding a stop_reason check,
and making build_context call a model.

Two of my own assertions were wrong before they shipped and were fixed rather than kept: one was
a tautology (`assertEqual(source.count(x), source.count(x))`), and one keyed a dict of loops by
target variable, which silently dropped every loop binding a repeated name like `row` -- the same
class of self-blinding this programme has now caught four times.

## Invariants

189. A budget guarantee that holds by proportion is still a guarantee, and still needs a test.
     Mandatory state survives here because it is small, not because anything protects it -- so
     the thing to pin is that no supporting section grows into the space the mandatory one needs.
190. Compaction is safe when it is reversible and refuses to proceed on failure. A summarizer
     that fails soft plus a backup written before the overwrite turn a lossy operation into a
     recoverable one, which is what makes delegating it to a model acceptable at all.
191. Where a system feeds its own prose back to itself, that prose is the budget. Deterministic
     state was 11% of the worst case here; the dominant term was this system's own output, and
     any budget policy that ignores it is measuring the wrong thing.
192. A cap with no detector converts an error into an absence. Truncation at an output limit and
     a model declining to follow a format are the same downstream event, and no consumer can tell
     them apart until something inspects the provider's stop reason.
193. An unbudgeted overflow becomes a chair's report. Where a failed call returns a string rather
     than raising, that string is passed on as though it were analysis -- acceptable only while
     it is also collected and surfaced as an error, which is the property to keep.

---

# Appendix — §10: auditability, provenance, causal reconstruction

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 7). This entry records the
measurements, the repairs, the correction, and the invariants.

A recommendation here is **recoverable as prose and not reproducible as an artifact**. Everything
the model said is kept; nothing the engine computed is.

## What was measured

| measurement | result |
|---|---|
| record classes §10 names, actually persisted | **6 of 16** |
| never recorded | deterministic calculations, the CDME snapshot, the context given to each seat, conflicts-as-conflicts, trade/waiver/lineup evaluations |
| operational activity log | `st.session_state.activity_log` -- **ephemeral**, capped, dies with the session |
| causal chain, one Prytaneum verdict | **4 of 10 links intact**, 3 partial, 3 broken -- and the three broken ones are frozen state, inputs, and deterministic calculations |
| causal chain, one Draft Room pick | **1 of 10 intact**, 4 partial, 5 broken |
| `pick_debate` writers to disk | **zero** -- no `write_text`, no `json.dump`, no `open(` |
| cost / usage / token / retry accounting | **none**, verified word-bounded after a naive scan gave four false positives |
| distinguishing a failed call from a discarded one | failed yes (`⚠️` + `result.errors`); generated-then-discarded leaves no trace |

**The inversion worth naming.** The Draft Room has the strongest canonical state in the system --
a frozen, immutable, id-less `PickSnapshot`, a closed decision boundary, an enforced ingestion
whitelist -- and the weakest audit trail: all of it is discarded when the session ends. The
Prytaneum has no canonical object and keeps its prose forever. Structurally the same shape as
§7.10's provenance inversion: the input questioned least is documented last.

## Repairs applied at the §10 boundary

Both apply a rule the codebase already stated and then used in exactly one place --
`app.append_message`: *"provider/model (which actually answered) are stamped on the message
itself, not derived from live bot_config at render time."*

**R9.** `llm_engine.DebateResult` and `pick_debate.PickDebateResult` now record `role_models`
alongside `role_providers`. Both already received the models as arguments and discarded them.
This is not tidiness: a role can be re-pointed at a different model of the SAME provider -- the
case `run_debate`'s own docstring names -- and a provider-only record cannot distinguish those at
all. Pinned by a test running all four chairs on one provider with two different models.

**R10.** `log_decision` gained optional `provider`/`model`, and both `process_moderator_output`
call sites pass them; the values were already in scope. Absent means "not recorded", never "the
default model", so pre-existing rows stay valid and honest.

Non-vacuity: five probes planted in real code and reverted, all failing -- dropping role_models
from each result, defaulting an unset model to CLAUDE_MODEL instead of leaving it absent, letting
a call site fall back to the blank stamp, and adding a writer to pick_debate.

Not applied, each needing a new store with retention and scope decisions: persisting the
PickDebateResult, the snapshot, the assembled context, or the activity log; and cost accounting,
which needs a decision about what to meter.

## A correction, and the sixth substring artifact

The first cost scan reported `usage`, `output_tokens`, `cost` and `price` as present. All four
were prose -- "current usage" in a chair prompt, "opportunity cost", "price ceiling" -- and most
instructively `output_tokens` matched `max_output_tokens=MAX_TOKENS`, which is §9's OUTPUT CAP,
the opposite of usage accounting. The same class then recurred inside a test I wrote and had to
be fixed with a word-bounded regex. A second faulty assertion in the same file counted
`process_moderator_output(` and matched its own `def` line.

Sixth occurrence of this class in the programme, after D's `candidate.bpa`/`bpa_source`, Pass 2's
`team_label`/`surface`, Pass 3's `"role" in source`, and Pass 6's loop-dict keyed by target
variable. The recurrence rate is itself the finding: it is why every scan here now carries a
planted-probe check before its result is believed.

## Invariants

194. What answered is part of the answer. A result that records a provider but not a model cannot
     distinguish two chairs sharing a provider, and re-deriving either from live configuration
     re-labels history every time the configuration changes.
195. Absent must mean absent. A provenance field defaulted to the current configuration is worse
     than an empty one, because it converts "we did not record this" into a confident false claim.
196. The strength of a causal object and the strength of its audit trail are independent, and
     tend to be inversely related. The most carefully frozen state in a system is the state
     nobody thought to write down, precisely because it felt safe.
197. A chain is only as reconstructible as its weakest link, and prose is not a link. Retaining
     every word a model said while retaining nothing it was looking at yields a record that can
     restate a decision and never explain it.
198. An unmeasured quantity answers "no" to every question that depends on it. Cost was absent in
     routing (§5.8), in budgeting (§9.5) and in attribution (§10.4) -- one gap presenting as three.

---

# Appendix — §11: temporal consistency, concurrency, stale results

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 8). This entry records the
measurements, the repair, the correction, and the invariants.

**The section's finding: this app can tell whether a frozen snapshot is still current --
precisely, with a reason string -- and nothing in production asks it.**

## What was measured

| measurement | result |
|---|---|
| `PickSnapshot` input-state stamp | `picks_consumed` + `data_freshest_date`, documented as the stamp that lets "a debate still running, a UI panel held open, a stored decision log" ask if state is current |
| `snapshot_is_current` behaviour | unchanged -> `(True, None)`; +3 picks -> `(False, "3 new pick(s)...")`; changed data date -> `(False, "the underlying player data changed...")`; unstamped -> `(False, "no input-state stamp")` |
| production callers of `snapshot_is_current` | **zero** -- every reference outside its own module and tests is a comment |
| what both Draft Room result guards compare | `pick_label` only (live at app.py:4805, mock at :4441) |
| two boards at one pick_label | 3 candidates / `picks_consumed=24` vs 1 candidate / `picks_consumed=27` -- the guard treats them as the same |
| the snapshot CACHE key | `(..., len(draft_picks), merger.freshest_date)` -- with a comment naming these as "the same two staleness signals snapshot_is_current already uses" |
| `diff_snapshots` on that pair | 2 departures + 1 rank move, fully structured -- and used only to inform the NEXT debate |
| cross-session write safety | no lock, no atomic replace, no read-modify-write guard anywhere |
| lost update, real store code | tab A writes, tab B reads, tab A writes again, tab B saves -> **tab A's second objective is gone** |

The sharpest form: when the board changes, the app **detects it on exactly the right signals and
rebuilds the snapshot**, then displays a recommendation computed against the previous snapshot
beside the new board, with no indication anything moved.

## Repair applied at the §11 boundary

**R11.** `PickDebateResult` now records `snapshot_picks_consumed` and
`snapshot_data_freshest_date`, taken straight off the snapshot -- §10's R9/R10 rule again: what a
result was produced from is part of the result. Before this a consumer holding only a result
structurally could not put it to `snapshot_is_current`; a test now demonstrates the round trip.

Not applied: acting on the stamp. Hiding a stale result discards an answer the user waited
30-120s and real API spend for, possibly with seconds on a pick clock; annotating writes into
displayed output; warning leaves the stale recommendation up. Same discard/annotate/warn
trichotomy as #99, at a more time-pressured moment. Also not applied: atomic writes -- a torn
write is undemonstrated, and §7.8 established this programme does not make production changes for
undemonstrated failures. The lost update IS demonstrated, but its fix is a concurrency model.

## A correction to §3.9 -- the third time a finding was one read short

§3.9 concluded `PickSnapshot` has "no id, no hash, no computed-at timestamp" and that "consumers
hold the object itself, not a reference to it." The first clause is true of a UNIQUE IDENTIFIER.
The framing was wrong: the snapshot carries a documented input-state stamp and a purpose-built
certifier consumes it. Provenance was present; I recorded it as absent because I read the field
list and not the docstring twelve lines above it.

Third occurrence, after §6.4a (composite ambiguity, disproved by two call-site reads) and §9.8
(compaction is destructive, disproved two lines further into the function). All three were the
most tempting finding available; all three were disproved by reading further in the same file.
Stated as a rule: **before reporting an absence, read the docstring of the thing you claim lacks
it.**

This shrinks #92 rather than growing it: the gap is not "invent a provenance mechanism" but
"persist and uniquely identify the one that exists."

## Invariants

199. A staleness key must be a property of the state, not of the request. A pick label identifies
     which decision is being made, never which world it is being made in -- and the two diverge
     for as long as the user is on the clock.
200. Detecting a change and acting on it are separate wirings, and a system can do the first
     perfectly while doing nothing with it. Here the same two signals correctly rebuilt the board
     and never re-examined the recommendation displayed beside it.
201. A capability with no caller is not a guarantee. `snapshot_is_current` is implemented,
     documented, tested and stranded -- the same shape as marginal_lineup_value, and a reminder
     that "the mechanism exists" answers a different question from "the mechanism runs".
202. Recording what a result was computed from is the prerequisite for every staleness policy,
     and is itself policy-free. Whether to hide, annotate, or warn is a separate decision that
     cannot even be posed until the stamp travels with the result.
203. Serialization by the runtime is not isolation by design. Single-threaded execution hides a
     concurrency model's absence exactly until a second tab exists, at which point load-mutate-
     write silently loses whichever update lost the race.

---

# Appendix — §12: multi-tenant isolation, cache leakage, context pollution

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 9). This entry records the
measurements, the correction, and the invariants. **No production file was modified.**

Cross-*user* isolation is NOT APPLICABLE as deployed (§13.5: no login, no tenancy). Cross-*league*
isolation is live today, and **resolves better than the storage layout suggests** -- because what
matters is reach, not schema.

## What was measured

| measurement | result |
|---|---|
| chats / decisions / todos / pins | league-scoped **by path** -- a league's file cannot be read without naming it |
| `league_format` / `league_prefs` | one shared file each, correctly scoped **by key inside** (league / user); an override set for LEAGUE_A returns None from LEAGUE_B |
| attachments | per-item `league_ids` scope list; `list_attachments(league_id=...)` returns global items plus those scoped to include it -- exercised: from A, `{global, a_only}`, `b_only` excluded, unfiltered sees all three |
| **where that filter is called** | `app.py:1884`, inside `build_context` -- the path that reaches a model. The three unfiltered calls are management/counting views |
| finding fields reaching another league's prompt | `date`, `player_name`, `source`, `rank`, `claim` |
| finding fields stored but **withheld** | **`question`**, **`league_id`**, `conviction`, `id`, `ts`, `composite_impact` |
| comparison fields withheld | **`question`**, **`league_id`**, `panel_undisputed`, `id`, `ts`, `evidence_type` |
| Bot Research UI columns | Date / Player / Source / Claim / Rank / Composite impact -- no `question`, no `league_id` |
| cross-session caches | exactly two `@st.cache_resource`, both **no-argument**, both reading only `ASSETS_DIR`; neither touches session_state, a roster, a league or a user_id |
| embeddings / vector index / shared summary object | **none exist**; `compact_league_history` summaries are per-league by path |
| `findings_for_context` / `comparisons_for_context` params | `['limit']` -- neither can filter by league |
| `league_id` readers in `bot_research` | **none** -- written on every entry, read by nothing |

The private field is `question` -- the user's own free text -- and it reaches neither another
league's prompt nor the UI. The cross-league sharing that does happen is disclosed in the panel's
own caption: *"Everything the panel has vetted across every league."*

Residual, named and undemonstrable: `claim` and `evidence` are free text authored by the Moderator
and could themselves embed league context. The store is empty (§6 reach: 0 findings ever), so this
cannot be measured, and no schema can prevent it.

## A correction to §13.5 -- the fourth time a finding was one read short

§13.5 recorded that under hosting "two stores would be immediately wrong -- `league_prefs.py` and
`league_format.py` use a module-level global PATH rather than the per-league scoping ... all use."
Wrong. Both use one shared file AND are correctly scoped by key inside it -- `league_format` by
`league_id` (with a docstring stating the intent: "a property of the league itself, not by Sleeper
user"), `league_prefs` by `user_id`. I conflated *global file* with *global scope*, having read
the path constant and not the accessor signatures. Their real hosting exposure is concurrent
writes to one shared file (#102), not miskeying. §13.5's overall status is unaffected; only its
named example was wrong.

Fourth occurrence, after §6.4a, §9.8 and §11.6. The §11 rule -- *before reporting an absence, read
the docstring of the thing you claim lacks it* -- would have caught this one, and did not get
applied because §13.5 predates it.

## Tests added

`test_tenant_scope_boundary.py` -- 13 tests, enforcement of protections that were real and
undefended, plus one characterization (research has no per-item league scope).

Non-vacuity: six probes planted in real code and reverted, all failing -- removing the league
filter from build_context, gutting the filter's body, rendering a finding's `question` into the
prompt, giving a cross-session cache an argument, giving `findings_for_context` a scope parameter,
and removing `league_format`'s league key.

## Invariants

204. A store's scope is where its key lives, not where its file lives. One shared file keyed by
     tenant is correctly scoped; a per-tenant file read without naming the tenant is not.
205. A protection is only as good as its call site. Two mechanisms of equal quality differ
     entirely by whether the path that reaches a model actually invokes them -- `attachments`
     does, `snapshot_is_current` does not.
206. Judge a leak by what travels, not by what is stored. A record may hold private context and
     still be safe to share if the renderer withholds it -- and the renderer, not the schema, is
     then the boundary that must be tested.
207. A no-argument cross-session cache cannot be keyed by tenant, so it is safe only while its
     contents are tenant-free. That is a property to assert, not to assume, because adding one
     argument silently converts it into a shared index.
208. Deliberate sharing disclosed to the user is a different thing from leakage, and the audit
     record should say which it is. What is missing here is not a boundary but a per-item choice.

---

# Appendix — §14: failure modes, partial completion, fallbacks

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 10). This entry records the
measurements, the repair, and the invariants.

**Fail-soft is this app's strongest reliability property and it was undefended -- and underneath
it, a failed chair's error string was being handed to the next chair as that chair's evidence.**

## What was measured

| measurement | result |
|---|---|
| provider callers that return `⚠️` rather than raising | **6 of 6** (3 in llm_engine, 3 in pick_debate), for both the missing-key path and `except Exception` |
| a fully failed debate | 4 errors collected, surfaced as "Debate finished with issues", verdict parses to `{}` |
| `pick_debate`'s access to the engine | **none** -- no `compute_draft_board`, no `build_snapshot`; its first parameter is an already-built snapshot |
| distinguishable causes vs distinct signals | **9 causes -> 6 signals**, one signal carrying four (provider down / bad key / quota-429 / context overflow) |
| provider-error classification (`status_code`, `RateLimitError`, `429`) | **absent from both modules** |
| retry / backoff / max_retries / resume / idempotency | **absent** -- retries bounded at zero, no resume path |
| duplicate prevention | `_last_submitted`, keyed on the QUESTION text, not an operation id |
| a totally failed debate in the decision log | **nothing written** -- `log_decision` returns early on a falsy verdict; only the ephemeral activity log records it |
| **the Contrarian's prompt with both upstream chairs failed (before R12)** | `--- QUANT / VORP REPORT ---\n⚠️ Claude request failed: Connection reset by peer`, then *"Pressure-test these two reports."* -- **no label marking either as a failure** |

## The repair (R12)

A failed upstream report is replaced, in the model-facing handoff only, by an explicit
unavailability marker. Applied to all four downstream handoffs: Contrarian and Moderator in
`llm_engine`, Skeptic and Caller in `pick_debate`.

Repaired rather than surfaced because it is not a new policy -- it is this codebase's own rule
applied where it was broken. *A missing thing is represented as missing, never as a value*: an
unpriced row carries None rather than 0.0; an unstamped snapshot is "not certifiable" rather than
current; an unrecorded model is "" rather than the default; `panel_undisputed` replaced a
`validated` the writer could not establish. A failure occupying the report slot breaks that rule
at the one place a model reads it, and the classifying test (`startswith("⚠️")`) was already being
computed at that exact point to populate `result.errors`.

Three properties, each pinned: the marker's second sentence says absence is not evidence of
absence (a bare "unavailable" invites exactly the negative-evidence reading from the chair most
likely to make it); the raw provider exception is NOT forwarded into another provider's prompt
(removing §7.8's named residual at its one live instance); and the real error still reaches the
user via `result.errors` untouched.

Not applied: an abort-versus-degrade rule. The debate always degrades and never aborts, and
whether a Moderator should synthesize from three unavailable reports is a product decision with
real cost either way. Surfaced as #104. R12 makes either choice implementable and makes the
current one honest.

Non-vacuity: six probes planted in real code and reverted, all failing -- handing the failed
report on raw, over-applying the rewrite to real reports, stripping the marker's second sentence,
making a caller raise instead of failing soft, introducing retries, and writing a decision row for
a total failure.

## Invariants

209. Failing soft is only half a contract. Returning a sentinel instead of raising keeps the
     system alive; what that sentinel is allowed to be mistaken for decides whether it stays
     honest, and a sentinel placed in an evidence slot is read as evidence.
210. A failure signal must not be reused as content. The same string can be a correct error for
     the user and a corrupt input for a model, and the boundary between those two audiences is
     where it has to be translated.
211. Absence of evidence must say so out loud where a reasoner will read it. Telling a chair a
     report is "unavailable" without telling it that means MISSING invites the chair to conclude
     there was nothing to find.
212. One provider's internal error text has no business in another provider's prompt. It carries
     no analytic value and an unbounded amount of incidental detail.
213. A taxonomy collapses at whatever granularity nobody had to act on. Four causes needing four
     different user responses arrive here as one string, because no code path ever branched on
     which one it was.
214. A log of decisions that records only successes is a record of what worked, not of what was
     attempted -- and the difference is invisible precisely when it matters most.

---

# Appendix — §15: economic and resource exhaustion

Structured findings live in `ARCHITECTURE_AUDIT.md` (Pass 11). This entry records the
measurements, the corrections, and the invariants. **No production file was modified.**

**Every AI operation has a deterministic, small, closed-form call envelope -- and it is
deterministic by accident of construction rather than by a limiter, which is exactly why it
needed pinning.**

## What was measured

Counted by stubbing the real provider callers, not read off the source:

| operation | provider calls |
|---|---|
| `run_debate` (full Prytaneum) | **4** -- one per chair in ROLE_SYSTEM_PROMPTS |
| `ask_moderator_followup` | **1** |
| `debate_pick` (Draft Room) | **3** -- one per chair in DEFAULT_ROLE_PROVIDERS |
| `run_benchmark` | **candidates x scenarios x 2** -- verified at 1, 2 and 3 candidates; the judge is a billed call too |

| measurement | result |
|---|---|
| retries / backoff / max_retries / tenacity | **absent** -- bounded at zero |
| loop around a provider call | **none** in llm_engine or pick_debate; bot_benchmark's two loops are over finite lists |
| recursion: does parsing a verdict spend money? | **no** -- `process_moderator_output` reaches only `parse_*` members (AST walk, docstring dropped) |
| provider-spending entry points in app.py | all behind a button or a submitted question, never behind model output |
| **tool calls inside one chair call** | **uncapped** -- no max_uses, max_tool_calls, tool_choice or search cap on any of the three providers' web-search grants |
| budget / quota / cooldown / debounce / throttle / rate_limit / spend cap | **none anywhere** |
| benchmark candidate multiselect | `options=_p_fetched, default=_p_fetched` -- every fetched model of every configured provider, pre-selected |
| one button press at 30 candidates | **180 billed calls** |
| cost disclosure before running | present: "Real, billed API calls -- nothing runs until you press Run", live count in the button label, disabled at zero |
| parallelism | `max_workers=2`, within one debate only |

**The genuinely new finding is that the envelope splits.** The chair-call count is deterministic;
the tool-call count inside each one is not. A "4-call debate" is four APP calls and an unknown
number of billed PROVIDER operations. §15's deterministic-envelope question is therefore yes at
the layer this app controls and no at the layer it pays for.

## Corrections -- the seventh substring artifact, caught twice in one probe

**"Model output triggers another model call."** A naive regex over `process_moderator_output`
returned `ask_moderator_followup`, which appears ONLY in that function's docstring explaining
which callers can produce a verdict block. There is no recursion. Re-checked by AST with the
docstring dropped; the shipped test uses the AST walk and records why.

**"Budget/ceiling/spend primitives exist."** All three were prose: "a live draft's per-pick LLM
budget" in a docstring, PRICE CEILING as a verdict field and Ceiling as a Draft Sharks column,
and "actually spend a full panel run" inside a prompt.

Seventh occurrence of this class, after D's `candidate.bpa`, Pass 2's `team_label`/`surface`,
Pass 3's `"role" in source`, Pass 6's loop-dict keyed by target, Pass 10's `max_output_tokens`,
and this pass's two. The count is seven rather than a list of published errors only because no
scan result here is believed before a probe or a second reading.

## Tests added

`test_cost_envelope_boundary.py` -- 13 tests. Enforcement: the four counted envelopes; no retry
or backoff; no loop around a provider call; parsing output reaches only parsers; the spending
call-site census; bounded parallelism; and the benchmark's cost disclosure. Characterization: no
budget primitives, uncapped tool calls, and the default-to-every-model multiselect.

Non-vacuity: six probes planted in real code and reverted, all failing -- an extra Contrarian
call, the word "retry" appearing, a real recursion path from `process_moderator_output`, dropping
the judge call, capping tool use, and removing the cost disclosure.

## Invariants

215. A cost guarantee that emerges from the absence of loops is still a guarantee, and is the
     easiest kind to lose. Nothing in a retry, a reacting chair, or a second judge call announces
     itself as a cost change, so the envelope has to be counted rather than assumed.
216. Count an envelope, do not read one. The number of calls an operation makes is a property of
     execution; reading the source finds the calls somebody wrote, not the ones a loop produces.
217. An envelope is only deterministic at the layer that controls it. Where a provider decides
     how many tool calls to run inside one request, the caller's call count is exact and its bill
     is not.
218. Defaulting a billed action to its maximum is a product choice, and disclosure is what makes
     it defensible rather than reckless. Both halves are worth pinning -- the default so it is
     deliberate, the disclosure so it cannot quietly vanish.
219. An instructional boundary is worth re-checking structurally at the layer where it costs
     money. "The Moderator never triggers a debate itself" is a prompt sentence; that no code
     path leads from a parsed verdict to a provider call is the thing that makes it true.

---

# Appendix §16 — Human-in-the-Loop Override Provenance

**Baseline entering:** `ff460db` on `ui-authority-pass`, suite 1370 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched.

## What was measured

**The override inventory.** Eleven persisted stores a user can write from the UI, classified by
what each reaches and whether it records when / who / why. Three feed the deterministic engine
(`player_aliases.json`, the rankings uploads under `data/projections/**`, the external-source
CSVs under `data/baseline/external/`); a fourth feeds it through the research path
(`bot_research.json`). Of those four, exactly one records a timestamp.

**The named §16 variables have no override surface.** Zero `st.number_input`, `st.slider` and
`st.toggle` calls exist in `app.py`. `injury_status` reaches `RISK_ADJ` only from Sleeper's
`players_db`; `need_bonus`, `eligibility_bonus`, `replacement_levels` and `time_horizon_adj`
are computed. §16's *"injury status, positional need, VOR baseline, custom value"* is therefore
N/A by construction — not a passing grade, a description of the shape of this app.

**The alias re-price, measured.** On a synthetic two-row pool: aliasing a name onto the higher
row moved `trade_value` **41.0 → 100.0** and `projection` **202.0 → 339.0**, over a
previously-correct automatic match (`match_path == "key"`, `match_verified` True), and across a
team boundary the automatic matcher would have rejected (CLE → CIN). Reproduced against the
committed baseline before being pinned synthetically so the numbers cannot drift with a refresh.

**The dropped marker, by AST.** `merge_player` returns `match_path == "alias"`;
`build_available_pool` carries it as `_match_path`; `compute_draft_board`'s two explicit output
column lists — walked as AST subscript lists, not grepped — emit `bpa_source` and
`universal_value` and **do not** emit `_match_path` or `_match_verified`. Both fields are
write-only across the entire repo, production and tests alike.

**The erased rejection, demonstrated.** `add_todo` → `mark_likely_resolved` → `reopen_todo` left
a stored entry byte-identical to one no bot had ever proposed anything about: `status` back to
`"active"`, `resolution_reason` cleared to `""`, `revisions` and `notes` untouched.
`mark_likely_resolved` wrote no timestamp of its own, so a surviving proposal could not say when
it was made either.

**The finding record's key set.** `add_finding` writes exactly
`{id, ts, date, player_name, source, claim, rank, composite_impact, conviction, question,
league_id}` — asserted by sorted-set comparison. No origin field, while
`MODERATOR_SYSTEM_PROMPT` explicitly admits findings from the user's own captioned reference
material *and* from live search in the same sentence (*"Whichever way it entered the debate"*).
`data/baseline/bot_research.json` is **not gitignored**, so a finding written there would be committed — but see the §21.7 correction: the file has never existed and was never committed. `data/player_aliases.json` and
`data/league_formats.json` are gitignored — confirmed via `git check-ignore`.

## Corrections to my own conclusions

1. **`resolve_todo` does not destroy the bot's proposed reason.** I read the source as a second
   erasure — the user's confirmation note overwriting the panel's reason. The call sites
   disprove it: `app.py` passes a reason only from the branch where `status != "likely_resolved"`
   (so no proposal exists), and "✅ Confirm Done" passes none at all, which the docstring already
   names as the "don't override it" case. Not reported. Fourth occurrence of the one-read-short
   pattern.
2. **My own timestamp test was weaker than its docstring claimed.** `_writes_a_timestamp`
   originally scanned the whole unparsed function for `time.time()` / `datetime.now()`. A probe
   that deleted `add_finding`'s `"ts"` field still passed, because `datetime.now()` remains in
   the function for an unrelated `today`. Rewritten to require a clock call inside a dict value
   or a subscript assignment — i.e. inside a *field of the record* — and re-probed.
3. **No numeric override UI exists.** I expected one on the strength of §16's own wording and
   went looking; measuring found none. Recorded as the honest answer rather than stretching a
   different feature to fit the question.

## Repairs

**R13 — `todo_log.py`: the moment a human overrules the panel now survives.**
`mark_likely_resolved` appends `{ts, date, reason, outcome: "pending"}` to a new `proposals`
list; a new `_close_pending_proposal` helper stamps the open entry with `rejected` (reopen),
`accepted` (resolve) or `superseded_by_dismissal` (dismiss) plus a `closed_date`. `add_todo`
seeds `"proposals": []`. Entries written before the field existed close cleanly and get no
fabricated history — absent means "no bot ever claimed this", never an invented outcome.
Justified by this module's own stated rule (*"archived … never destroyed"*) and by `revise_todo`
implementing exactly this pattern, one function away, for the mirror-image case.

**R14 — `app.py` `build_context`: the manual format override announces itself.** One paragraph,
guarded by `if special_format:` so it is emitted only when an override is actually set, placed
*before* the `FORMAT_GUIDANCE` block so the caveat precedes the imperatives it qualifies. It
states that the label is a manual setting, that every other field on that line is Sleeper's own
data, and asks the panel to say so plainly when an answer turns materially on the format being
right. Justified by the convention `build_context` already applies three times over — reference
material *"captioned by hand … not verified fact"*, past outcomes *"user-recorded, not a guess"*,
pins *"the user manually flagged these … doesn't mean elevated priority"*. `build_context` is not
part of any benchmark fingerprint (`chair_prompt_fingerprint` covers chair system prompts only),
so this does not invalidate stored reports.

No other production file was changed. §16's remaining gaps are contract, schema and boundary
decisions.

## Tests added

`test_override_provenance_boundary.py` — **28 tests**. Enforcement: the proposal record and its
timestamp; user rejection preserved; acceptance distinguishable from rejection; dismissal as its
own outcome; repeated proposals accumulating; nothing fabricated for an item never proposed;
legacy records closing cleanly; revisions never touched by proposal handling; the archived record
answering who/what/when/why; all four user-supplied context sections labelled; the format label
guarded and ordered before its guidance; format-override store scoping; the alias re-price and
its removal; an alias naming a nonexistent row falling through rather than missing; and every
AI-authored record stamping itself. Characterization (pinned, not endorsed, each citing its
register item): the alias marker dropped before the decision boundary (#107) and the finding
record unable to name its origin (#106).

Non-vacuity: **15 probes** planted in real production code and reverted, every one failing the
intended tests — reopen no longer recording the rejection; the MANUAL SETTING label deleted;
the label moved after `FORMAT_GUIDANCE`; pins losing the "not elevated priority" clause;
reference material losing "not verified fact"; `add_finding` losing its `ts`; the board starting
to emit `_match_path`; `save_alias` no-opping; `mark_likely_resolved` dropping its timestamp;
dismissal folded into "accepted"; `log_decision` losing ts/date; `save_attachment` losing
`uploaded_at`; `set_outcome` losing its date.

## Invariants

220. There is no such thing as an override that is only a display. Which vendor row a player is
     priced from is a valuation input; a name-matching alias is therefore an override of the
     engine, not of the UI, and inherits every obligation an engine input carries.
221. An override that bypasses a guard is doing its job; an override that bypasses the *record*
     of having bypassed it is not. The alias branch is right to skip team/position rejection —
     that is what a manual override is for — and the resulting row is wrong to arrive downstream
     looking like an ordinary match.
222. A field computed and then dropped is not provenance. `match_path` reaching the pool and not
     the decision boundary means the information existed at every step except the one where a
     reader could have used it.
223. Provenance tends to be recorded where the machine is the author and omitted where the human
     is, because the human is assumed to remember. They will not, and a second user never could.
     Whose hand wrote a record is a bad predictor of whether the record needs a timestamp.
224. The moment a human overrules the system is the single most important event to keep, and the
     easiest to implement as a reset. Clearing a field back to its default is the natural way to
     express "never mind", and it destroys the only evidence that a disagreement occurred.
225. Overwriting is asymmetric before it is wrong. When the machine's edit to the human's text is
     archived and the human's edit to the machine's claim is not, the asymmetry is the defect,
     independent of which direction anyone would have chosen.
226. A caveat placed after the instruction it qualifies has already been read as fact. Order in a
     prompt is not cosmetic: attribution has to arrive before the imperative it attaches to.
227. Collapsing where a claim came from is a decision, not an omission, when a prompt says so out
     loud. "Whichever way it entered the debate" is a deliberate rule; the cost of it is that the
     stored record can never distinguish a search result from the user's own screenshot.
228. Refreshing a source under the source's own name is correct and unfalsifiable at the same
     time. Overwriting the tracked filename is what stops a double-count; nothing then separates
     the vendor's export from a hand-made file wearing its weight.
229. Replay needs the state of the overrides, not just the answer. A verdict plus its question
     plus the model that produced it still cannot be reproduced if the aliases, the format toggle
     and the loaded files have moved since.
230. A capability that was never built is a real answer to "how is it isolated?". Reporting that
     no override surface exists beats manufacturing an equivalent one so the question has
     something to grade.

---

# Appendix §17 — Cross-Version Schema, Provider & Live-Upgrade Safety

**Baseline entering:** `7908136` on `ui-authority-pass`, suite 1398 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched.

## What was measured

**Version identity: one artifact has it, nothing else does.** AST over every production module
for `__version__`, `SCHEMA_VERSION`, `VERSION`, `CDME_VERSION`, `ENGINE_VERSION` — **zero**,
which is a *decision*: `bot_benchmark._fingerprint` states that a content hash is used
*"deliberately … rather than a hand-maintained version number: a number has to be remembered and
drifts out of sync with the thing it names."* That approach covers the benchmark report and
nothing else. `requirements.txt`
carries one bound in the whole file (`streamlit>=1.34`); `anthropic`, `openai`, `google-genai`,
`pandas`, `scipy`, `pypdf` are unbounded, and there is no lockfile, `pyproject.toml`, `Pipfile`
or constraints file. **31 of 31** stored records under `data/draft_simulation_trials/` carry no
version, commit or date key — the single scan hit was a false positive (`baseline_gap` etc. are
that experiment's own measurements).

**The served model is discarded.** `CLAUDE_MODEL = "claude-sonnet-5"`,
`GEMINI_MODEL = "gemini-2.0-flash"`, `OPENAI_MODEL = "gpt-4o"` — all floating aliases;
`CLAUDE_MODEL`'s comment records that it replaced *"a now-retired dated snapshot"*. AST over
`_call_claude` / `_call_gemini` / `_call_openai`: every `return` in all three is a string
expression, none returns or reads the response object. The three provider SDKs are not
installed in this environment (every provider call in the suite is stubbed), so which field
each one exposes could not be verified here — the finding is stated at the level that *can* be
verified: the object is thrown away, so nothing about it is available to anyone.

**An object outliving its class.** Read out of installed streamlit 1.61's
`LocalSourcesWatcher`: edited local modules are evicted from `sys.modules` and re-imported,
while `st.session_state` survives. Measured on a reloaded module: `isinstance(held, PickSnapshot)`
→ **False**, `type(held) is PickSnapshot` → **False**. An older-schema snapshot handed to the
current consumers raises `AttributeError` in both `snapshot_is_current` (`picks_consumed`) and
`serialize_snapshot` (`decision_regime`).

**Old records stay readable by `.get()`.** Defensive-read counts: `todo_log` 17,
`bot_research` 15, `decision_log` 12, `bot_benchmark` 11, `league_prefs` 6, `attachments` 4.
Minimal legacy records round-trip through every reader without raising.

**A renamed export silently re-scores players.** Removing `("dynastyprocess", "players.csv")`
from `_EXTERNAL_PERCENTILE_RULES` and adding `players_v2.csv` in its place: **31 of 131**
sampled composites moved (median |Δ| **4.3** / 100, largest 13.6), **4** disappeared, **no
exception, warning or log**. 887 of 2,600 external rows already carry no percentile rule, some
deliberately (ESPN redraft, FantasyPros best-ball).

**An unrecognised status hides a record.** All five production `load_todos` call sites pass a
status filter; a record whose `status` is outside both vocabularies is absent from the active
list, the archive, the archive search, the header count and `build_context`, silently.

**`reconciliation_conflicts` is write-only in production** — read only by
`test_reconciliation_boundary.py`. Third instance of the compute-then-drop class, after
`waiting_cost` (#57) and `_match_path` (§16.3).

## Corrections to my own conclusions

1. **The stale-class probe was wrong the first time.** I deleted the newer fields from a
   *current* instance's `__dict__` and reported that the consumers returned OK. Dataclass
   defaults live as class attributes, so the lookup fell through to the current class. A
   genuinely old instance keeps `__class__` pointing at the old class object, which has neither
   the field nor the default — the corrected probe raises `AttributeError`. The first, more
   alarming result would have been reported.
2. **`role_models` and R10 are not mislabelled.** I drafted a finding that they claim to record
   "what actually answered" while recording the request. R9's comment draws a different
   contrast — record-at-the-time versus re-derive-from-live-config-later — and under that
   reading the fields are honest. Withdrawn before publication.
3. **The trial-corpus version scan's one hit was a false positive** — eighth occurrence of the
   substring-artifact class, caught by reading the hit rather than the count.
4. **"No version constant exists" is not the gap I first wrote it as.** §17.1 was drafted as an
   absence to be filled, and `_fingerprint`'s own docstring — found late, while reviewing the
   R15 diff — records that the version-number shape was considered and rejected in favour of
   content hashing, for a reason that holds. The section's headline was rewritten, the test
   reclassified from characterization to enforcement (a version constant appearing is a
   reversal, not progress), and #111 reframed from "introduce versions" to "extend the hashing
   this repo already chose to what still has no identity". Ninth occurrence of the one-read-short
   pattern, and the first to change a section's headline after it was written.
5. **§15's appendix conflated two different scans, and this section's own repair caught it.**
   The §15 record described the no-retry guarantee as *"verified word-bounded with comments
   excluded."* That description belongs to
   `NoBudgetPrimitivesExistTests.test_no_budget_ceiling_quota_cooldown_or_throttle_exists`,
   which really is word-bounded and comment-stripped.
   `test_no_retry_or_backoff_exists` is a much cruder thing: a raw lowercased substring scan
   over the whole of `llm_engine` + `pick_debate` + `bot_benchmark`, docstrings and comments
   included. R15's first draft described an SDK's "retry behavior" in a comment and the full
   suite failed on it. The test is left as-is — being made to re-read the diff and confirm no
   retry semantics were added is worth more than a false positive costs — but its docstring now
   says what it actually is, so the next reader is not misled the way the §15 record was.
6. **A probe harness's `finally` does not survive an external kill.** The first probe batch hit
   a two-minute tool timeout mid-run and left P9's mutation in `llm_engine.py`. The `git status`
   check that follows every probe batch caught it; reverted, remaining probes re-run in the
   background. Recorded because that check is the only reason it did not reach a commit.

## Repairs

**R15 — `bot_benchmark.py`: a stored report records the operating envelope it ran under.**
Adds `max_tokens` (from `llm_engine.MAX_TOKENS`) and `provider_sdk_versions` (from
`importlib.metadata`, over `_PROVIDER_SDK_DISTRIBUTIONS`) to every report, beside the three
R95 fingerprints. A distribution that is not installed is **omitted**, never recorded as a
version the run did not have; a metadata lookup that raises never costs the run. Justified by
R95's own stated rule — a report must say what it "was actually conducted under" — and by
§17's question about tying provider-SDK changes to explicit versioned audit events, which the
benchmark history is the only artifact in this app positioned to answer.

**Deliberately not gated on.** `comparable_history` still keys off the three fingerprints
alone. Whether a token-budget or SDK change makes two runs incomparable is a judgment about
what counts as the same experiment; that belongs to #96. The restraint is pinned by its own
test so a later change has to be a considered edit rather than a drift.

No other production file was changed. §17's remaining gaps need either a product decision
(#110, #111) or an environment with the provider SDKs installed (#109).

## Tests added

Two existing tests needed updating for R15, and both were doing their job:
`test_benchmark_contract_coverage.test_the_report_shape_is_pinned_so_absent_fields_stay_visible`
pins the report's exact top-level key set (updated to include the two new keys, plus a note that
`max_tokens` is a request CEILING and not a usage measurement, so it cannot be mistaken for
closing #100), and `test_cost_envelope_boundary.test_no_retry_or_backoff_exists` caught the word
"retry" in an R15 comment (see correction 5).

`test_version_boundary.py` — **26 tests**. Enforcement: an uninstalled SDK omitted rather than
placeheld; an installed one reporting its real version; a partially-reporting environment;
a metadata explosion costing nothing; the report carrying `max_tokens` and
`provider_sdk_versions`; the envelope surviving save/reload; `comparable_history` still keyed on
three fingerprints only; a pre-fingerprint report retained in history but excluded from
comparable; four stores reading minimal legacy records without raising; an old-schema snapshot
failing loudly in both consumers; the stamp fields defaulting to `None`; every file-backed
percentile rule pointing at a file that exists; the synthetic research pair being the only
ruleless one; upload targets derived from the rules; the two to-do vocabularies not overlapping.
Also enforced: no module declaring a hand-maintained version constant — reclassified from
characterization once `_fingerprint`'s docstring showed the absence to be a decision.
Characterization (pinned, not endorsed, each citing its register item): the provider callers
returning text only (#109), a status outside both vocabularies invisible everywhere (#110), and
dropping a percentile rule moving composites silently (#110).

Non-vacuity: **13 probes** planted in real production code and reverted, all failing the
intended tests — the report dropping `max_tokens`; dropping `provider_sdk_versions`; recording
`"unknown"` for a missing SDK; letting a metadata failure propagate; `comparable_history`
starting to gate on `max_tokens`; `picks_consumed` defaulting to `0`; the certifier
`getattr`-defaulting a field; a percentile rule pointing at a missing file; a default model id
becoming a dated snapshot; a caller handing out the response object; `search_archived`
bracket-reading a legacy field; a production module declaring `SCHEMA_VERSION`; and the two
to-do status vocabularies overlapping.

## Invariants

231. A system with no version cannot be asked what version it is running, and every pinning
     question downstream inherits that. Before "are active operations pinned?" can be answered,
     something has to exist to pin them to.
231a. An absent version number can be a decision. A content hash of the thing itself cannot
     drift out of sync with what it names, which a hand-maintained number always eventually
     does — so "no `__version__` anywhere" is worth reading as a rejected shape before it is
     reported as a missing feature. The real question is then what else deserves the hash.
232. A floating model alias is a dependency you did not declare. The string is stable, the
     weights behind it are not, and nothing in a stored record distinguishes the two.
233. Discarding a response object discards every fact it carried. Reading only the text is a
     decision about provenance, not just about parsing, and it is made once at the caller and
     felt everywhere downstream.
234. An object in session state outlives the class that defined it whenever local modules are
     reloaded. Failing loudly on the mismatch is the correct behaviour; reading a default the
     old object never carried is the failure mode worth testing for.
235. `getattr(obj, "field", default)` on a schema-versioned object converts a detectable
     mismatch into a silent wrong answer. Defensive reads belong on records loaded from disk,
     not on live objects whose class is supposed to match.
236. Forward-compatible reads are a property held together by convention, and conventions are
     lost one bracket at a time. If old records staying readable matters, one planted `[...]`
     should break a test.
237. A lookup table keyed on filenames is a schema, and renaming a file is a schema migration.
     Nothing announces it, the file stays on disk, and the numbers quietly move.
238. Filtering by a closed vocabulary makes every record outside that vocabulary invisible
     rather than invalid. "Kept, never destroyed" is not satisfied by a record no view can
     reach.
239. Record what a run was conducted under; decide separately whether a difference makes two
     runs incomparable. Recording is a fact, comparability is a judgment, and collapsing them
     hides the judgment inside the fact.
240. Absence of a version is absence, not version zero. An SDK that cannot be found is omitted
     from the record; writing "unknown" into the slot makes a missing measurement look like a
     taken one.
241. This codebase computes diagnostics reliably and routes them nowhere reliably —
     `waiting_cost`, `_match_path`, `reconciliation_conflicts`. Adding a fourth unread
     diagnostic is not a repair, which is why a silent-drift signal was surfaced rather than
     stored.

---

# Appendix §18 — Data Semantics: What Does the System Know?

**Baseline entering:** `c045f8e` on `ui-authority-pass`, suite 1424 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched.

## What was measured

**The eight-state inventory.** Six of §18's eight states have a representation; two do not.
"Disputed" is never carried as a value state — the system resolves it (`_dedup_by_name_and_position`),
excludes it (`_drop_contested_identities` drops **both** contested rows), or records it where
nothing reads it (`reconciliation_conflicts`, §17.8). "Never checked" has no representation at
all: an AST scan over every production module for `unchecked` / `not_checked` / `never_checked`
string constants returns **zero**.

**The horizon states, on the committed baseline.** `known` 264, `unknown` 468, `not_applicable`
32 — **500 of 764 rows (65.4%) carry a non-known state**, every one with a reason, and the
reasons are genuinely discriminating rather than boilerplate: K gets *"no multi-year figure on the
sleeper_transcribed basis that prices this position"*, DB gets *"no multi-year figure from any
source carrying this player"*.

**Where the distinction died.** Grepped repo-wide, `proj_3yr_state` / `proj_3yr_reason` appeared
in `data_merger.py` and in tests, nowhere else. `merge_player`'s field whitelist omitted them and
also drops `proj_3yr` itself when absent, so both states reached every consumer as the identical
missing key. Demonstrated on real rows: a DEF (`not_applicable`) and a DB (`unknown`) differed in
**no key** that could tell them apart.

**The AI-claim path, planted end to end and reverted.** A panel-vetted finding reaches the
composite as `bot_research` at **weight 0.025** against 0.609 / 0.812 / 0.871 for the three
structured sources — 24x below the smallest — because `COMPOSITE_MIN_TRUSTED_POOL_SIZE` scales a
one-row pool's weight by `1/40`. It moved a real composite by **0.0** (97.8 → 97.8). The cited
outlet never becomes a composite source in its own name; `composite_impact` states the claim's own
reach on the record; relative comparisons are barred structurally (no percentile rule at all).

**Provenance completeness.** Research findings carry origin / `ts` / `conviction` /
`composite_impact`; composite components carry `source` / `source_date` / `pool_size` / `weight`;
decisions carry provider/model (R10) / `ts` / `conviction` / `outcome`; attachments carry user /
`uploaded_at` / "claim to weigh". The one structural gap: a **board row carries no date** — it can
say which anchor priced it, not when that anchor was measured. `PickSnapshot`'s INPUT-STATE STAMP
covers freshness at the snapshot level, which is the right granularity for a decision. Noted, not
repaired.

## Corrections to my own conclusions

1. **`_confidence`'s `35.0` fallback is not a defect.** I drafted it as an unrecognised anchor
   silently collapsing to a known confidence tier. `bpa_source` is assigned unconditionally and
   only ever takes one of the four values `CONFIDENCE_BY_SOURCE` scores, so the branch is
   unreachable. Checked before reporting, and now pinned by a test so it stays that way.
2. **I nearly added a fifth unread diagnostic.** R16's first draft stopped at carrying the state
   through `merge_player`, which would have moved the drop point one module later and lengthened
   §17.8's compute-then-drop list — the exact reasoning I had just used to *decline* repairing
   §17.5(a). Caught before shipping; the repair was extended to a real consumer.
3. **A test was passing by skipping.** The "a table with no such column gains no invented state"
   check ran against `merger.free_agents`, which is empty in this baseline, so it skipped instead
   of asserting. Replaced with a hand-built stateless frame that exercises the guard for real.
   Tenth occurrence of the one-read-short pattern, and the first found in my own test rather than
   in production.

## Repairs

**R16 — the three horizon states survive their own producer, end to end.** Two halves, one path:
- `data_merger.merge_player` carries `proj_3yr_state` and `proj_3yr_reason`. Tables that have no
  such column (the Free Agent Finder, the Trade Value Chart) are untouched — the existing
  `field in match.index` guard already handles them, verified rather than assumed.
- A new pure helper `data_merger.horizon_gap_lines(rows)` turns those states into context lines,
  and `build_context` emits them under the roster table. Counts per state, the engine's own reason
  strings **verbatim** rather than a paraphrase, and **nothing at all** when nothing is absent.
  It states which absence each blank is, and says nothing about what to conclude from it.

**Why this one was routed rather than surfaced, and why that is the judgment call of the section.**
Carrying the field alone would have made a fifth compute-then-drop instance. Routing it changes
what the panel reads, which is a behavioural change. It was taken because three established
precedents cover the shape exactly: `TeamDiagnostics.replacement_level_unpriced` (a count of the
absent, *"reported rather than folded into the number above"*), `INCOMPLETE_PLAYER_PROFILE`
(build_context already names an honest absence instead of leaving a blank), and
`_assign_horizon_state`'s own stated purpose, which a stranded field defeats. The revert, if this
reads as too far, is one line in `build_context`; the carrying half stands on its own.

No other production file was changed. §18's remaining gaps are boundary and vocabulary decisions.

## Tests added

`test_data_semantics_boundary.py` — **33 tests**. Enforcement: the reporter says nothing when
nothing is absent; counts and labels the two opposite states separately; uses the engine's reason
strings verbatim; keeps two different reasons within one state; de-duplicates a repeated reason
while still counting both players; never counts a row with no state or a `known` row; the indent
is a parameter. On the real baseline: every state reaches a consumer with its reason, the two
opposite absences are distinguishable, a stateless table gains no invented state, the vocabulary
is closed at three, the state never disagrees with the value, every non-known row states why, and
the distinction covers >25% of the pool (non-vacuity for all of the above). `build_context`
consumes the helper. The AI-claim protections: a planted claim arrives labelled as research and
never as the cited outlet, at under a tenth of the smallest structured weight; `composite_impact`
distinguishes rank-bearing from qualitative; a qualitative claim never reaches the composite; a
relative comparison is barred structurally; every component keeps origin/time/trust; no opinion at
all returns `None`. Plus the five absence-namers that already reach a consumer. Characterization
(pinned, not endorsed): the board emits `bpa_source` and `confidence` but no absence reason
(#112), and "unchecked" has no representation anywhere (#112).

Non-vacuity: **15 probes** planted in real production code and reverted, all failing the intended
tests — `merge_player` dropping the state; `build_context` dropping the report; the reporter
re-wording the engine's reason; the two states merged into one bucket; a stateless row counted
anyway; the reporter speaking up when nothing is absent; a `not_applicable` row losing its reason;
the state contradicting the value; the board emitting the state; an `unchecked` constant appearing;
a research finding given full source weight; the pool-size guard removed; `composite_impact`
collapsing to one value; a failed chair report handed on unlabelled; and an unmeasurable waiting
cost documented as zero.

## Invariants

242. A one-bit absence contract is worth having and is not the whole contract. "Has a value" and
     "does not" can be perfectly propagated while every kind of not-knowing collapses into the
     same blank.
243. Two absences can be near-opposites. "No career arc exists to project" and "a career arc
     exists and nothing loaded publishes it" differ on whether the data can ever be recovered,
     which is the only question that decides what to do about it.
244. A field whitelist is a semantic boundary, not a performance detail. Whatever it omits stops
     existing for every consumer downstream, however carefully the producer computed it.
245. Dropping a key when a value is absent destroys more than the value. The reader loses the
     ability to ask why, and cannot tell an unmatched player from a matched one with nothing to
     say.
246. Carrying a diagnostic one module further is not the same as routing it. A field nobody reads
     has moved, not landed, and the count of unread diagnostics is the honest measure of whether
     a repair happened.
247. Report the absence in the producer's own words. A consumer that paraphrases a reason puts its
     summary in front of the reader instead of what was actually determined.
248. Say nothing when there is nothing to say. A data-quality note that fires unconditionally
     trains its reader to skip it, and the one time it matters it reads like the other times.
249. Weight is how an advisory claim stays advisory. A single-source opinion admitted at 1/24th of
     a structured source's weight is an input; the same claim at parity is an assertion.
250. A percentile is a claim about a pool, and a pool of one is not a pool. Scaling weight by pool
     size is what stops "the only thing we found" from reading as "the best thing there is".
251. Surfacing a disagreement is a stronger answer than resolving one. Handing both numbers to the
     reasoner with their scales named beats arbitrating silently, and this codebase does that
     across sources while doing the opposite within one.
252. An unreachable fallback should be checked, not assumed, and then pinned. `get(key, default)`
     on a closed vocabulary is only safe while the vocabulary stays closed.

---

# Appendix §19 — System Integrity, Dependencies & Periodic Baseline Auditing

**Baseline entering:** `694f2e4` on `ui-authority-pass`, suite 1457 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched.

**No production file was modified, and no test file was added.** §19 states "Do not modify
production code during the audit" and that was treated as binding. The no-new-tests decision is
methodological rather than obedient: §19 audits the audit machinery, so the suite's size,
composition and reproducibility are among the measured quantities, and adding to it mid-section
would move the thing being measured. One planted-and-reverted data probe is the only write.

## What was measured

**Code integrity.** Zero occurrences of `eval(`, `exec(`, `pickle`, `subprocess`, `os.system`,
`__import__`, `shell=True` across every production module — the only `exec`-shaped hits are the
word "execute" in prose and `ThreadPoolExecutor`, checked rather than assumed. Exactly **one**
outbound HTTP surface in production (`sleeper_client`'s `requests.Session`) plus the three
provider SDKs imported inside their own callers; no other `requests`/`urllib`/`httpx`/`socket`
use anywhere.

**Integrity primitives.** `hashlib` appears **once** in production (`bot_benchmark._fingerprint`).
No checksum, manifest, signature or content hash over source or over `data/baseline/`.

**Test-baseline reproducibility, four ways.**
- **Inputs:** all `.csv`/`.json`/`.pdf` under the three directories `DataMerger` loads, cross-checked
  against `git ls-files` — **28 files, 28 tracked, 0 untracked.**
- **Assertions:** only **5 of 75** test files mention time, and every recency/staleness assertion
  uses a fixed input (`recency_grade(7)`, a hardcoded `"2026-08-25"`), never the live clock.
- **Numbers:** advancing `data_merger`'s clock +0/+30/+90/+365/+1095 days over 90 scored players
  moved composite scores by **max |Δ| 0.00** at every horizon — the recency decay is a common
  factor in a weighted average and cancels.
- **Count:** 1,455 `def test_*` declarations + 2 inherited-and-rerun methods
  (`SuperflexRookieDraftRosterContextTieredGateTests` subclasses its parent and overrides 1 of 3)
  = **1,457**, exactly the runner's number.
- **Residue:** `git status` verified clean after each of five full runs across §16–§19.

**But the input set is a directory listing.** Planted one CSV in `data/projections/_global/` —
where the app's own uploaders write, and which `.gitignore` excludes — and reverted it: the
canonical pool went **764 → 766**, the fabricated row was **priced by the engine**
(`projection=9999.0`, `trade_value=100.0`), git reported the file as ignored, and a suite class
that reads the baseline still passed.

**Cadence.** No `.github/` directory of any kind — no CI, no workflow, no hook. The documented
launch path (`update_and_run.sh`) is `git pull` → `pip install -r requirements.txt` (unbounded,
no lockfile) → `streamlit run`, with no test run in between and no signature or revision pin.

**Behavioural baselines.** **274 tests across 15 `*_boundary.py` files** — 18.8% of the suite —
covering identity, reconciliation, prompt constants, research ingestion and authority, context
budget, provenance, temporal consistency, tenant scope, failure modes, cost envelope, override
provenance, version, data semantics, and CDME ingestion. `test_cdme_ingestion_boundary.py` is a
real adversarial data-injection control: a deliberately maximally-distorting `bot_research.json`
finding is written to disk about a real baseline player and CDME's output for that player is
proven byte-identical before and after. The evidence that this machinery detects regression is
this audit's own record — **43 probes planted in real production code across §16–§18, every one
failing the intended test, every one reverted.**

**Doctrine.** `ENGINEERING_DOCTRINE.md` (186 lines, committed) carries a six-link required audit
chain, an eight-part contract for load-bearing quantities, and ten standing rules — including
*"A test that cannot fail proves nothing"* and *"A docstring can encode a defect."* Nothing
enforces any of it; `ROADMAP.md` contains no audit cadence or trigger condition.

**Configuration.** `.streamlit/config.toml` is theme-only plus `gatherUsageStats = false`.
`.devcontainer/devcontainer.json` auto-launches with `--server.enableCORS false
--server.enableXsrfProtection false` — scoped to the Codespaces preview launcher only, since
`config.toml` sets neither and `update_and_run.sh` uses defaults. `.env.example` carries the same
floating model aliases as production (#109).

**A name trap.** `run_dependency_audit.py` is a *statistical cross-signal* audit — Pearson
correlations between `compute_pick_necessity`'s six components, flagging pairs above 0.5 that may
double-count the same scarcity signal. It has nothing to do with package dependencies. A reader
auditing this repo for supply-chain controls would find the filename and stop looking.

## Corrections to my own conclusions

1. **§17.7's "regression corpus" framing was wrong.** I reported "31 of 31 stored trial records
   carry no version identifier" and framed `data/draft_simulation_trials/` as the deterministic
   corpus §19 would ask about. The facts hold; the framing does not. `.gitignore` excludes those
   files as *"regenerated … not source"* and README says the same — **0 of 31 are tracked**. The
   corpus is the 28 committed **input** files; the outputs are derived on demand, which is
   defensible and is exactly what `compare_baseline_pre_post_95d2111.py` exists to exploit. The
   real §19 answer is "yes in principle, unautomated in practice", not "no corpus".
2. **I predicted composite scores drift with the clock. They do not** — max |Δ| 0.00 at three
   years. What does drift is the baseline's self-described freshness: Recent/Fresh today, Aging
   at +30 days, **Stale at +90 and permanently after**, with no refresh path short of a code
   change. A real finding, and not the one I went looking for.
3. **I predicted untracked files were already contaminating the suite. They are not** — 28 of 28
   tracked. The hazard is real and demonstrated; the current state is clean. Reporting the
   hypothesis as the finding would have been false.
4. **A wrong denominator inside a correct finding.** Both write-ups first said "5 of 121 test
   files mention time"; there are **75**. The claim built on it — that the suite is
   clock-independent — was right, which is exactly why the bad number would have survived:
   nothing downstream of it looked wrong. Caught on a verification pass before the commit.

## Repairs

**None.** Three findings here are mechanically correctable and were deliberately left alone: a
checksum manifest over `data/baseline/`, a CI workflow running the suite, and upper bounds in
`requirements.txt`. All three are parked in #113 for the repair pass.

## Tests added

**None** — see the methodological note above. The §19 measurements are read-only plus one
planted-and-reverted data probe, so nothing about the suite's own composition moved while it was
being measured.

## Invariants

253. Auditing the audit machinery is not the moment to extend it. Test count, suite composition
     and reproducibility are the measured quantities; adding tests mid-measurement moves them.
254. A checked input set and a declared input set are different guarantees. "Everything the suite
     loads is committed" can be true today and hold nothing tomorrow, because a directory listing
     is not a manifest.
255. Gitignored is not harmless. A path excluded from version control because it holds user data
     is still an input if production code reads it, and the two facts together are how a
     fabricated row gets priced while every status check stays green.
256. A guarantee nobody runs is a document. 1,457 tests that execute only when a human types the
     command protect the commit they were last run against, not the branch.
257. A launcher that installs unpinned dependencies on every start is a drift mechanism, not a
     convenience — and running it before the tests, rather than after, is what makes the drift
     silent.
258. Trust the filename least of all. A file called `run_dependency_audit.py` that computes signal
     correlations is honest work under a name that will stop the next auditor from looking
     further.
259. A characterization test's discipline is a docstring, and a docstring is not a mechanism.
     Nothing distinguishes "the gap was repaired and the test inverted" from "the assertion was
     weakened until it passed."
260. Committed vendor data ages into a permanent warning. Numbers can be perfectly time-stable
     while the freshness label attached to them decays monotonically to its worst value and stays
     there, with no refresh path that isn't a code change.
261. Doctrine is a re-audit mechanism only where something triggers it. A written audit chain and
     a contract checklist are real assets; without a cadence or a gate they describe how an audit
     would go if one happened.

---

# Appendix §20 — Live Draft Validation & Behavioral Regression

**Baseline entering:** `55066fb` on `ui-authority-pass`, suite 1457 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched.

**No production file was modified.** §20 opens *"After the repair sequence and downstream
contract gate…"*, and that sequence has not run. This pass measures the current system and marks
which prescribed validations are blocked on parked work, rather than implementing that work so
the validation can pass.

## What was measured

**Eight controlled drafts, 1,293 production decision points.** Every pick through
`pick_synthesis.build_snapshot` → `candidates[0]` at `mode="auto"` — the same contract
`draft_room.simulate_opponent_picks` uses. No provider call occurs anywhere in the harness.
Conditions varied: 1QB, superflex, TE-premium, IDP, redraft, thin bench, reversed slot order,
and an 18-round trial that crosses `UPSIDE_MODE_DEFAULT_ROUND = 15`. Pools of 349 (offense +
K/DEF) and 764 (all positions). ~2.3 hours of CPU.

**The shipped drivers could not have run §20's first check.** `run_draft_validation.py` is
`("QB","RB","WR","TE")`; `run_idp_draft_validation.py` adds DL/LB/DB. **Neither includes K or
DEF.** A K/DEF-inclusive pool had to be built for this pass.

**K/DST timing.** K first taken round 6 (mean 7.9, **0 of 17** in the last third); DEF first
round 5 (mean 7.2, 2 of 14). Superflex later but still mid-draft. Rounds 11–14 contain no K or
DEF at all.

**The margin that disproves the naive reading.** At the first DEF pick: DEF `tav=17.0 uv=13.0
need=4.0`; best non-K/DEF QB `tav=16.9 uv=12.9 need=4.0`; K `tav=15.0 uv=11.0 need=4.0`. The
empty-starter-slot lift is **identical across positions** — no positional term exists or fires.
The DEF wins by **0.1** because the offensive pool has decayed from UV 187 at pick 1 to UV ~13
by pick 56.

**The IDP control.** 764-player pool, 168 picks consuming 22% instead of 48%: IDP spread across
**every round from 3 to 13** (n=76, mean r8.5), longest same-position run **5** against **29** in
the offense-only league — and **K and DEF never taken in 168 picks**, that league having no
K/DEF starter slot. Demand absent, urgency absent.

**Superflex QB.** [7, 8, 4, 3, 3, 0, 1, 0, 1, 0, 1, 0, 0, 0] against a 1QB control of
[0, 0, 1, 0, 3, 1, 2, 4, 1, 0, 0, 0, 0, 2].

**BPA versus context.** Over 1,077 priced decision points the pure-UV leader survived as TAV
leader on **70.3%**; context flipped it on **29.7%** (IDP 48.8% high, 1QB 22.7% low).

**Bench capacity is invisible.** `starter_slot_counts` counts only `FANTASY_POSITIONS` and
`FLEX_SLOT_POSITIONS` entries; `"BN"` is neither. A 7-bench and a 2-bench league produced
**byte-identical 168-pick drafts**.

**The late-draft pricing collapse.** Leader TAV by round in the 18-round trial: 187.34, 99.53,
73.37, …, 25.58 (r5), 6.0 (r8), **0.0 (r10)**, −3.67 (r11), −8.58 (r13), **None from r14 on**.
From round 14 through 18, **12 of 12 boards every round have zero priced candidates** — **60 of
216 picks, 27.8% of the draft**. The round-16 board presents ids 164/165/166/167/168 in order:
pure `_board_order` `str(player_id)` tiebreak, `necessity = "DOESN'T MATTER MUCH"`, no forces.

**A code-path identity, verified rather than measured.**
`use_upside = mode == "upside" or (mode == "auto" and current_round >= upside_round)` — below
round 15, `"auto"` and `"balanced"` are the same path, so the two unreconciled defaults diverge
only at r ≥ 15. And **none of `app.py`'s three `build_snapshot` call sites passes `mode=`**
(checked directly, not from the docstring), so a human's own board is always `"balanced"` and
never enters upside mode while every auto-drafted opponent does.

**The display contract.** `serialize_candidate` emits an explicit dict with `uv`/`tav` and never
`projected_points` — a fantasy-point total cannot reach the board, by construction, though no
test asserts the absence. Across **44,385 board rows**: min **−33.1**, max **190.5**, median
**11.0**; **11.8% negative, 2.2% ≥ 100, 11.4% in the 50–400 band** that overlaps a plausible
season point total. The board's prose qualifies its unit three times (*"universal-value
points"*, *"-point gap to the next best {pos}"*, *"-point rival premium"*) and leaves it bare
twice (*"X point(s) off the board leader"*, *"about X points of context lift"*).

**The mechanical layer.** `chosen == candidates[0]` on **1,293/1,293** picks; **0** mis-sorted
boards; unpriced rows last in every case. Three configs that differ only in engine-invisible
parameters produced byte-identical sequences from three separate OS processes.

## Corrections to my own conclusions

1. **The K/DST finding was drafted as an engine fault and is not one.** The 0.1-margin
   measurement with identical `need_bonus` across positions disproves the positional reading.
   This is the difference between "tune the formula" and "the input scale is parked", and §20
   says explicitly not to rationalize formula changes from anecdotes.
2. **The reversed-slot config varied nothing.** Twelve chairs start with identical empty rosters,
   so reversing first-round order is a relabeling. Identical trajectories confirmed it.
3. **The thin-bench config varied a quantity the engine does not read** — which became the
   finding rather than a wasted trial.
4. **The 14-round wave could not reach upside mode** (threshold round 15). Caught after launch;
   an 18-round trial was added and produced the section's largest finding.
5. **The display wording was over-stated at first** — three of five prose sites already qualify
   the unit.
6. **One measurement was abandoned, not reported as a result.** A direct `balanced`-vs-`auto`
   divergence probe ran ~20 minutes without completing one board pair and was killed; the
   question is answered exactly by the code-path identity above, which is stronger. Recorded so
   the gap is not mistaken for a measurement.

## Repairs

**None.** Every behavioural finding either passes or is blocked on a parked repair whose premise
§20 says not to pre-empt. The one mechanically tempting change — the two unqualified "points"
strings, which have in-file precedent for the fix — would tidy the symptom of a parked scale
defect, so it is parked with it (#116).

## Tests added

**None.** §20 is a behavioural-validation pass; its instrument is the simulation harness, not
the unit suite. Two test-shaped gaps were noted for the repair pass rather than filled:
`SerializeCandidateTests` asserts which fields are present and none that must be absent (so the
"no fantasy points on the board" contract is held by construction alone), and no test pins the
board's unit wording.

## Invariants

262. A behavioural check is only as good as the pool it runs against. Two shipped validation
     drivers omit K and DEF entirely, and the section's opening question is about K and DEF.
263. Measure the margin before naming the cause. "K goes in round 6" reads as a positional
     defect until the board shows the alternative was 0.1 behind with the identical need bonus.
264. A control that changes the pool changes the verdict. The same engine buries K/DEF for 168
     picks in a 764-player league and takes them in round 5 in a 349-player one; the difference
     is not in the rules.
265. A required roster slot creates demand, not urgency — and the honest test of that is the
     league with no such slot, where the position must never be taken at all.
266. Value that decays to zero mid-draft does not stop the draft. Ordering falls through to
     whatever tiebreak exists, and a tiebreak chosen for determinism is not a valuation.
267. A deterministic tiebreak looks like judgement when the ids happen to be sorted. In a harness
     that numbers players by rank the late rounds look sensible; in production the same code
     orders by an arbitrary vendor id.
268. Vary only what the engine reads. A trial that changes bench depth against an engine that
     never reads bench depth produces an identical draft and no information — until the identity
     itself becomes the finding.
269. Two defaults that agree everywhere except the tail still differ. `auto` and `balanced` are
     the same code path below the upside round, which is why the divergence went unnoticed and
     why it lands exactly where the board has the least signal.
270. A displayed number needs its unit in the same sentence, every time. Qualifying it in three
     places and not in two is how a scale becomes ambiguous in exactly the cases a reader is
     least equipped to catch.
271. When the prescribed validation depends on a parked repair, run it anyway and record the
     dependency. A blocked check with a measured current-state baseline is worth more than a
     deferred one, and far more than one made to pass.

---

# Appendix §21 — Operational Economics, Reuse & Research Memory

**Baseline entering:** `af4126d` on `ui-authority-pass`, suite 1457 OK. `main` frozen at
`9fb5102`, untouched. Defect A1 untouched. **No production file was modified.**

## What was measured

**Reuse.** `findings_for_context` / `comparisons_for_context` reach the panel through
`build_context`, so a debate starts knowing what was already found, each line date-stamped.
Research is read at exactly four production sites — `data_merger` (composite),
`app.py:1922/1936` (context prose), `app.py:5225/5226` (a UI listing) — and **none is on the
path that decides whether to spend a provider call**. Grepped production for
`cache`/`memo`/`ttl`/`expire`/`expiry`/`reuse`: the only cache in the system is
`sleeper_client`'s league-snapshot and players-DB cache. The §15 envelope is unchanged at four
calls per debate regardless of what the store holds. `BEAT_SYSTEM_PROMPT` argues *against* reuse
— *"your own live results are, by definition, fresher than any file-based source in your
context"* — which is correct for injury and depth-chart signal and makes §21's "paying to
rediscover" premise inapplicable to that half of the work.

**The six reusability attributes, on a real stored row.** Present: source identity (`source`),
freshness (`ts`/`date`, plus a 60-day half-life in the composite), topic/entity scope
(`player_name`), validation status (`composite_impact`). Absent: **evidence fingerprint** and
**expiration**. Beyond the six, three more absences already carry items: league scope recorded
and never read (#103), origin (#106), discovery cost/latency (#100). Full key set:
`claim, composite_impact, conviction, date, id, league_id, player_name, question, rank, source, ts`.

**Two operations discovering the same fact.** Measured: identical wording same day → **deduped**
(same id, 1 row); the same fact **reworded** → **duplicated** (2 rows); same rank from a
different source → correctly distinct (3 rows). The composite then collapses 3 stored rows to
**2** via `load_bot_research_as_external`'s newest-per-(player, cited source) rule — so the
dedup's stated purpose (stopping weight inflation in the percentile pool) is already covered
independently, and its real effect is on store size and on the prose both restatements reach.

**Sharing versus private context.** Every finding stores `question` — the user's own typed
question, passed through from `process_moderator_output(trigger_question)` — and `league_id`, in
the same row as the shareable claim, with no boundary between them. Inert today
(`findings_for_context` renders only date/player/source/rank/claim, and the app is
single-tenant), and material because this is the one research store deliberately left out of
`.gitignore`.

**Expiration.** A finding aged **400 days** is served to the panel unchanged inside the
newest-30 cap. The composite recency-weights rank-bearing findings (a 400-day claim contributes
~1% of a same-day one); the context prose applies no weighting at all, only a visible date.

**Cost and latency.** Latency is measured in exactly one place — `bot_benchmark` times each
provider call and reports `latency` per question and `avg_latency` per candidate, surfaced as
*"{score}/100, {avg_latency}s avg"*. `DebateResult` carries question, four reports, verdict,
errors, `role_providers`, `role_models` and **no timing, usage or cost**, even though
`run_debate` already runs two chairs inside a `ThreadPoolExecutor` where wall time is free.
Grepped production for `price_per`, `per_token`, `cost_per`, `pricing`, `$0.`, `usd`: **every hit
is fantasy-football player pricing** — verified by reading, not by count. There is no money
anywhere in this codebase.

## Corrections to my own conclusions

1. **`data/baseline/bot_research.json` is not git-tracked, and never has been.** I wrote that it
   was, in the §16 appendix and again in §18, and used it to sharpen #106 into "a user's own
   claim becomes a committed numeric input". I took it from `bot_research.py`'s own docstring
   (*"Both are global and git-tracked"*), which README repeats twice. Checked this pass: the file
   **does not exist**, `git check-ignore` reports **NOT ignored**, and `git log --all` on the path
   is **empty — never committed**. The claim is aspirational rather than false (nothing gitignores
   it, so a finding would be committed the first time one is written), but the state has never
   been reached: **the research memory has never held a single row in version control**, and every
   measurement above is against a planted record. #106's severity drops from an observed state to
   a live hazard. Both earlier records corrected in place.
   This is a direct violation of the rule I have cited all programme —
   `ENGINEERING_DOCTRINE.md`'s *"A docstring can encode a defect. Documentation is evidence of
   intent, never of correctness"* — committed twice before being caught.
2. **The same-day dedup matters less than its docstring says.** Its stated purpose is preventing
   weight inflation in the composite; the composite's own newest-per-key rule already prevents
   that. Measured, not inferred: 3 stored rows, 2 reaching the composite.

## Repairs

**None.** Every §21 gap is an economics or product decision — what may be cached and for how
long, what a shared record must strip, and whether a price belongs on a benchmark report. The one
thing that looked like a defect was my own record.

## Tests added

**None.** Nothing was repaired, and the two candidate enforcement tests both depend on decisions
that are parked: an expiry rule has no policy to assert against, and a shareable-projection test
has no defined boundary between claim and private context to assert.

## Invariants

272. Context reuse and cost reuse are different mechanisms. Handing a chair what was already
     found makes the answer better; only something that reads the store *before* the call makes
     it cheaper, and this system has the first without the second.
273. Not all research is cacheable, and the store already knows which. A rank-bearing valuation
     claim is durable; an injury or depth-chart read is worth less the moment it is stored, and
     the field that separates them exists before any caching policy does.
274. A dedup key is a definition of sameness. Keying on the exact claim string makes two
     phrasings of one fact two facts, and no amount of downstream collapsing changes what the
     store believes it holds.
275. A guard whose stated purpose is served elsewhere is not thereby useless — but its real
     effect is somewhere its docstring does not mention, and that is where it should be reasoned
     about.
276. A shareable claim and the question that produced it are different objects. Storing them in
     one row costs nothing until the row travels, at which point there is no boundary to enforce.
277. Freshness weighting applied to one consumer and not another is a half-policy. The composite
     decays a 400-day-old finding to a rounding error while the prose hands the same claim to the
     panel at full standing.
278. An instrument that measures quality and speed cannot answer a question about cost, however
     well it measures the other two. One missing field is the difference between "which model is
     better" and "which model is worth it".
279. Aspirational documentation reads exactly like descriptive documentation. "Both are global
     and git-tracked" describes a file that has never existed, and the only way to tell is to
     look at the filesystem instead of the sentence.

---

## Interlude — audit scope: this checkout has never been run as an application

Swept after §21.7's correction. Every runtime store is absent or empty:
`bot_research.json`, `bot_comparisons.json`, `benchmark_results.json`, `bot_config.json`,
`player_aliases.json`, `league_formats.json`, `league_prefs.json` and `last_session.json` do not
exist; `data/decisions/`, `data/todos/` and `data/attachments/` are empty untracked directories;
`data/chats/`, `data/sleeper_snapshots/` and `data/projections/` contain only a tracked
`.gitkeep`; `data/draft_simulation_trials/` holds 31 untracked regenerated files. The only real
data is the **28 committed files under `data/baseline/`**.

Every §11–§21 finding that touched a runtime store was therefore measured against a planted or
synthetic record. Each pass said so locally; none said it globally, and it belongs in the record
once. It does not weaken the mechanism findings — a path that loses an update or drops a
provenance field does so whether or not a file exists — but it downgrades every "observed state"
phrasing to "live hazard" (#102, #103, #106, #107, #110), strengthens §19.3's reproducibility
result (there is nothing else on disk for the suite to pick up), sharpens #113(c) (the upload
directory is empty for the same reason everything else is), and explains why §20 had to
synthesise its own `players_db` from the committed rankings.

**280.** An audit of an unpopulated checkout establishes what the code will do, never what the
data has done — and the difference has to be stated once, at the top, or every finding quietly
inherits the stronger claim.

---

# Appendix §22 — Cross-Cutting Questions & Failure-Propagation Tests

**Baseline entering:** `60d6097` on `ui-authority-pass`, suite 1457 OK. `main` frozen at
`9fb5102`. Defect A1 untouched. One production file modified: **R17**, a correction to my own
§14 repair.

## What was measured

**The lost-response ambiguity.** Every provider caller wraps its whole request in
`except Exception`, which fires alike for a missing key (never executed), a connection error
(never executed), a read timeout after the provider generated and billed a response (executed,
not received), and a parse error on a response that did arrive. R12's marker asserted the call
*"did not complete"* and that *"no analysis was produced"* — neither supportable, both false in
the timeout case.

**Cascade boundaries: two, both structural.** The chair handoff (R12/R17) replaces a failed
upstream report rather than forwarding it, and the raw provider exception never reaches another
provider. The CDME ingestion boundary confines LLM-originated data to `composite_player_score`,
which `draft_room` deliberately removed from its math, and hard-filters CDME's two
`external_values` touches to `source_name == "keeptradecut"` — proven by injecting a maximally
distorting finding on a real baseline player and showing CDME's output byte-identical either way.

**Stateless chairs.** Every call is single-shot — `messages=[{"role": "user", ...}]` with
`system=` re-sent in full — so there is no thread for a replacement model to inherit assumptions
from, and the contract travels with each request.

**No independent reconstruction.** The engine rounds once at the source;
`_records_with_normalized_nan` normalizes NaN to `None` **without recomputing or re-rounding**;
`serialize_candidate` is a field-for-field read whose only computed values are two boolean
renamings; the board's `.toFixed(1)` re-renders an already-rounded number.

**Two Sleeper clocks, one disclosed.** `PLAYERS_CACHE_MAX_AGE_SECONDS = 24h`, deliberate and
vendor-requested. `players_db` (`app.py:3117`) is what feeds the engine, and `injury_status` read
from it is **the only Sleeper field reaching the deterministic valuation** via `RISK_ADJ`.
`build_freshness_manifest` grades four sources — DS Dynasty Rankings, DS Free Agent Finder, DS
Trade Value Chart, Sleeper league sync — and has **no entry for the players database**.

**History is additive.** `log_decision` writes `moderator_text` and the parsed verdict once;
`set_outcome` adds only `outcome`/`outcome_note`/`outcome_date`; `revise_todo` archives prior
text; `bot_research` is append-only by construction. The one destructive path was `reopen_todo`,
repaired in §16 R13.

**Stale is never false.** Every `snapshot_is_current` reason is a staleness claim, and an
unstamped snapshot is reported not-certifiable rather than silently current.

## Corrections to my own conclusions

1. **R12's marker overclaimed, and I wrote it.** It asserted non-completion and non-production of
   analysis from inside a bare `except Exception`. That is the exact rule #89 established for the
   alias branch and §6 R1 applied to `"validated"` — *a field may not claim a certainty its
   writing path cannot establish* — applied twice by me and then broken in my own repair.
   Corrected as R17.

## Repairs

**R17 — `llm_engine.UNAVAILABLE_REPORT` states what is known and names what is not.** New text:
*"(unavailable — no report from this chair reached the panel. Whether the call never ran, ran and
was lost, or ran and could not be read is not known here. Treat this as MISSING information,
never as a finding that there is nothing to report.)"* Behaviour unchanged; R12's two load-bearing
properties (`MISSING`, `never as a finding`) preserved.

## Tests added

Two, into `test_failure_mode_boundary.py` (R12's own file rather than a new one):
`test_the_marker_does_not_assert_why_the_report_is_missing` forbids the overclaiming phrases and
requires the three-way ambiguity be named; `test_every_provider_caller_catches_a_class_that_spans_all_three_outcomes`
asserts every caller still catches bare `Exception`, because the marker's caution is only
warranted while the catch is that broad — a future narrowing should force the wording to be
revisited rather than left silently over-cautious.

Non-vacuity: **4 probes** planted in real production code and reverted, all failing the intended
tests — restoring the old assertion, dropping the not-known clause, narrowing a caller's catch to
`ValueError`, and removing the absence-is-not-evidence clause.

## Invariants

281. A broad catch buys robustness and spends precision. `except Exception` around a whole
     request makes the code fail soft and makes every downstream statement about *why* it failed
     unsupportable.
282. The rule that catches a defect will catch your repair too. #89's "a field may not claim a
     certainty its writing path cannot establish" applied to the alias branch, then to
     `"validated"`, and then to a marker I wrote while applying it.
283. Naming an ambiguity is a stronger claim than resolving it. "Whether it never ran, ran and was
     lost, or ran and could not be read is not known here" tells a reader more than any one of
     the three asserted confidently.
284. A caution is only warranted while its cause holds. If the catch is ever narrowed, the
     over-cautious wording becomes a different kind of wrong — so the test pins the cause, not
     just the wording.
285. Statelessness is a safety property, not just an implementation detail. A chair that receives
     its contract in full on every call cannot inherit anything from the model that answered last.
286. Rounding once at the source is what makes "two components cannot disagree" true. Every
     re-derivation downstream is a new opportunity for the same fact to arrive twice, differently.
287. A cache with a vendor-mandated TTL is defensible; a cache whose age never appears beside the
     sources that are graded is not. The undisclosed clock is the one carrying the field that
     reaches the engine.
288. Amend, never overwrite, and the audit trail survives every correction. This codebase does it
     in four stores out of four — which is why the single exception was worth repairing.
