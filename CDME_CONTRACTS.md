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
> project owner approves them. See "Open decisions" at the end; two of them block work that
> is already scheduled.

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

## Open decisions — these block scheduled work

### A. `waiting_cost` is missing for entire positions, systematically  🚫 **blocks Phase 2**

Measured on real narrowed candidate sets:

| Round | QB | RB | WR | TE | K | DEF |
|---|---|---|---|---|---|---|
| 1 | 12 / 0 | **0 / 12** | 12 / 0 | **0 / 12** | 12 / 0 | 12 / 0 |
| 2 | 12 / 0 | **0 / 12** | 12 / 0 | **0 / 12** | 12 / 0 | 12 / 0 |
| 6 | 7 / 0 | **0 / 3** | 4 / 0 | **0 / 4** | 11 / 0 | 8 / 0 |

*(has `waiting_cost` / missing it)*

**100% of RB and 100% of TE candidates have no `waiting_cost` in early rounds.** Not sporadic —
total, and by position.

Root cause is known and already documented: `expected_positional_consumption` predicts 83.8 RBs
from a 72-deep pool and 50.3 TEs from a 45-deep pool. Both exceed their pools, so
`horizon_replacement` correctly reports "unknown." That defect was previously assessed as
*contained*, because its only consumer reported the unknown honestly.

**Wiring `waiting_cost` into `pick_necessity` un-contains it.** Four positions would receive a
real urgency signal and two would receive none — and the two are RB and TE, which dominate
early-round drafting. This violates admission criterion 4 above, and it is the same
missing-data-becomes-a-systematic-signal shape as the growth artifact.

From roughly round 8 onward every candidate has a `waiting_cost` (RB/TE floors become
computable once enough of them are drafted), which is also precisely the regime where
`team_acquisition_value` has collapsed toward 0 and necessity has least to work with.

**Options:**
- **A1 — Gate the term on completeness.** Admit `waiting_cost` to necessity only when *every*
  narrowed candidate has one; otherwise the term is absent for everyone. Self-activating around
  round 8; automatically inert while the data is asymmetric; and it activates *earlier*, not
  differently, if the consumption prior is later fixed. No positional bias at any point.
- **A2 — Fix the consumption prior first.** Correct, but blocked on real external draft data
  (self-play calibration would be circular) — the same prerequisite as Phase 3.
- **A3 — Admit it with a stated per-position asymmetry.** Not recommended; it is the failure
  mode this document exists to prevent.
- **A4 — Leave observable-only.** Defer Phase 2 entirely.

**Recommendation: A1.** It is the only option that both delivers the signal where it is most
needed and cannot introduce positional bias, and it degrades gracefully in both directions.

### B. TE horizon floors are contaminated where they are most used

Independent of A. TE's horizon rank lands at 39–51 — inside the scoring-basis discontinuity —
so TE `waiting_cost` is understated roughly 2×. Even under A1, TE would carry a systematically
wrong urgency value once the term activates. Resolving this is task #46's decision; it should
be settled before or alongside Phase 2, not after.

### C. Late-draft regime

From round ~11 `team_acquisition_value` collapses to a near-constant 0, so any term still
varying becomes the entire decision. Under A1, `waiting_cost` activates at round ~8 — meaning
it would become the dominant late-draft differentiator almost immediately. That may be exactly
right, since it is a real signal replacing a dead one. It is stated here because it is a
consequence worth choosing deliberately rather than discovering afterward.
