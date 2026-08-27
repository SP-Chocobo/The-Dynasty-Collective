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
