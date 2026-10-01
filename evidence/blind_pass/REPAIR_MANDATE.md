# `#52` → v2 repair mandate — ordered so each repair is measured on a tree the previous one corrected

> **Standing rule for this whole program.** The Wave 1–6 corpus is **evidence against v1**, not a
> TODO list. It stays preserved and immutable at `v1-freeze` (`6599b1e`) whatever gets fixed. Every
> repair below is a change to the working tree; none of it edits, re-scopes or "closes" a finding in
> `FINDINGS_LOG.md`, which is append-only by construction.

## Why the order is the deliverable

The recurring failure this audit uncovered is not any one defect. It is:

> **a repair expands a population → an invariant proven over the old population silently stops
> holding → the old test stays green because it never enters the new domain.**

`#172` recovered multi-eligible players and made W1-01 reachable. `#180`/`#192` routed offence through
the scoring-aware path and falsified a comment that was true when written. If the repairs below land
in the wrong order they will do the same thing again, and the next audit will find it.

Two consequences drive everything:

1. **Identity and provenance are upstream of all measurement.** Anything verified before they land is
   verified against inputs that are about to change.
2. **"Suite green" is currently weak evidence.** Both Wave 6 passes independently showed three live
   valuation constants surviving their corpus at absurd values, and a probability cap set to 9.0
   surviving all 51 tests of its own module. A repair cannot be certified by an instrument that
   cannot feel the quantity move.

**Correction to my own first plan, adopted from the owner's mandate:** I had written "every repair
ships with a test that would have failed before it." That is unachievable while the fixture universe
cannot *express* the failing case — thirteen test modules run on a universe with no IDP, no unpriced
rows and `proj_3yr` on every priced row (W2-07). **Fixture repair is therefore its own phase, and it
comes before the invariant repairs, not alongside them.**

---

## PHASE 0 — Preserve, adjudicate, and stop the bleeding in the record

- **0.1** `v1-freeze` stays. No repair commit touches `evidence/blind_pass/`.
- **0.2** **Adjudicate the two live disputes before touching their code.**
  - `assertion_floors`: pass I says defective four ways; pass J says the `skipTest` hole sits inside
    the docstring's declared limit. One of them is repairing a contract, the other is repairing a
    doc. Decide which.
  - `W4-15` cross-format mixing: G measured 18 players drawing from a "standard"-tagged export in a
    PPR league; H measured 0 mixed-source rows. They measured adjacent things. Re-measure once.
- **0.3** Record the latent NaN gap (five team terms absent from `_records_with_normalized_nan`,
  measured 0 NaN today) so it is not rediscovered as a defect.

## PHASE 1 — IDENTITY *(upstream of everything; nothing downstream is trustworthy until this lands)*

- **1.1** **Establish identity before deduplication, not after.** `load_all`'s
  `drop_duplicates(subset="norm_name")` must key on name **and** position group. Measured target: the
  22 same-position drops are the justified case and must survive; the **31 cross-position drops must
  not happen**, recovering **10 real players** including a startable superflex QB.
- **1.2** **Sweep the class, not the instance.** Every grouping, dict, cache, lookup, join and
  identity map keyed on a bare normalized name. Known: the rookie lookup (`draft_room.py:1009`,
  last-row-wins, 6 conflicting keys — this one makes the *wrong survivor inherit metadata*, which is
  worse than deletion), `_compute_percentiles`' `position_by_key` (101 raw / 19 cross-group keys),
  `_resolve`'s exact and alias paths (unguarded against a docstring saying "whatever path it took"),
  and two measurement scripts.
- **1.3** **Make disappearance an invariant, not a hope.** A test that asserts **no player present in
  raw ingestion is absent from the priced universe** without an explicit, recorded reason. Named
  collision families as explicit cases: Jordan Love, Javonte Williams, Malik Washington, Kyle
  Williams, Jeremiyah Love (the metadata-inheritance case), the six IDP casualties, multi-position
  players, and same-name-different-team.

## PHASE 2 — PROVENANCE AND PRECEDENCE *(also upstream)*

- **2.1** **Replace filename-sniffing with a stated contract:**
  **explicit user/league configuration > uploaded data > inferred metadata > committed baseline.**
  Today `league_dir` confers nothing and `_detect_rankings_format` reads the filename only, so an
  upload named the way people name files loses every field to the stale baseline — against a
  docstring promising the opposite.
- **2.2** **Validate declared dates on the same footing as stated ones.** `8/28/26` must not beat
  `2026-08-18`; a blank date column must not become `NaN`-`declared` and outrank an honestly undated
  row.
- **2.3** `_conflict_reason` must name the rule that decided the **chosen field**, not the rule that
  decided the winner row.
- **2.4** Decide whether absence should keep being priced as exactly 60 days old (`_recency_weight`),
  or refuse to compete on recency at all. **Design question — surfaced, not decided here.**
- **2.5 Oracle:** the doubled-value test. A league upload with every value doubled must move the
  price, under an ordinary filename.

> **GATE A.** After Phases 1–2, **every measured number in this repository is stale.** Re-run the
> pricing probes and the smoke seats before any Phase 3+ result is believed. Do not skip this to save
> time; it is the whole reason the phases are ordered.

## PHASE 3 — THE TEST UNIVERSE *(before any invariant repair)*

- **3.1** Fixtures that deliberately exercise: superflex, IDP, TE premium, slot alternatives, base
  and nonstandard scoring, missing projections, unpriced players, multi-eligible players, contested
  identities, roster-side identity resolution, and an ordinary uploaded league file.
- **3.2** **Boundary-generated cases, not hand-built safe ones.** The pattern across four waves is
  invariants pinned exactly where they cannot fail — `superflex=False` with no IDP slot, a roster
  with no bench, a 4×2 fixture where the backstop cannot bind, a board a quarter the real size.
- **3.3** The battery matrix must contain the shape the system is actually used on: K slot,
  SUPER_FLEX **and** IDP together, 25 rounds. And `format_axes_exercised` must be able to see
  roster-slot composition as an axis, which today it cannot.

## PHASE 4 — INSTRUMENTS *(test the tests)*

- **4.1** Give each instrument a test that **plants the defect it claims to detect**: deliberately
  dead prose for `prose_names`; an unconstrained numeric constant for `numeric_constants`; a dead test
  reference behind each supported historical marker; a weakened assertion for `assertion_floors`.
- **4.2** Fix `quantity_readers`' bare-attribute-name collisions and `suite_taxonomy`'s substring tier
  detection (and its stated 53 modules / 1.5 s against a measured 123 / ~205 s).
- **4.3** **Bounds must be invariants, not literals.** The repair for `RUN_TAKE_PROBABILITY_CAP = 9.0`
  is not "change 9 to 1" — it is a test asserting `0 ≤ p ≤ 1` that a mutation can prove meaningful.
  Same for every other stated bound.

## PHASE 5 — UNITS AND DOMAINS

Systematic sweep, not symptom patches: every comparison or sum where the two sides may be vendor
projections, league-scored points, raw stats, ranks, probabilities, normalized values or percentiles.
Known members: `qb_startable_floor` (vendor units vs league-scored), `upside_score` (unclamped ±50
percentile added to raw points), `time_horizon_adj` (same pair, clamped ±10), `FORFEIT_SCALE_MAX`
(orphaned 0–100 divisor), `NEED_BONUS_PER_DEDICATED_SLOT` (flat in points, 32% of a kicker's whole
spread and 1.9% of a top RB's). Hunt variable names that hide their unit.

## PHASE 6 — INVARIANTS AND THE POPULATIONS THEY RANGE OVER

- **6.1** `displacement_adj`'s sign and its empty-roster behaviour; `need_bonus`'s bound and its
  flex-before-dedicated formula; the round-boundary off-by-one; `depth_exposure`'s roster-wide
  surplus flag.
- **6.2** **W4-02 first among these**: two shipped constants derive from a caps tuple that hand-exempts
  the fourth team term on a premise measured false. Fixing the sign without fixing what was derived
  from it leaves the wrong constants shipped.
- **6.3** **An invariant registry.** Not a theorem prover — a maintained list of each stated invariant
  and the population it was proven over, so that a repair which expands a population has something to
  re-check against. This is the process repair for the failure mode at the top of this file.

## PHASE 7 — PROPAGATION, BRANCHES, CACHES

- **7.1** **Survival/refusal propagation.** Trace the withheld quantity through headline →
  `pick_necessity` → `denial_value` → snapshot diff → chair prompts → `screen_context`. Five leak
  paths are known; the repair is the propagation rule, not five patches. And the suite currently
  **pins** one of the leaks.
- **7.2** **Take models.** One normalised model, one consumer set. `expected_taken` summing to 23.3
  over 22 picks is the oracle.
- **7.3** **The `trade_value` branch as a family** — omitted `truncated_out`, the 2-row clamp, the
  stale `live_starter_demand` stamp. Compare structurally against sibling paths rather than patching
  three symptoms.
- **7.4** **Cache keys.** Every key must contain every input that can change the result; then mutate
  one dimension at a time and assert cached and uncached diverge. Members: the Draft Room snapshot
  cache, `stamp_is_current`, the anchor fingerprint, and the cross-league session-state leak.
- **7.5** State and persistence: `store_io`'s bare `except OSError`, `upload_batches.record` returning
  an id for an unpersisted batch, `sleeper_client`'s `write_text`, `outcome_record`'s damaged→absent
  collapse, the 18-second double reload, `draft_history` being wired to nothing.

## PHASE 8 — CERTIFY

Full suite → the mutation battery re-run (the three surviving constants must now be caught) → **one
fresh Fable blind pass against v2**, plus **targeted regression probes for every confirmed v1 defect**
→ cut `v2-freeze`.

The v1 corpus stays. The story that ends this program is
**v1 → six-wave falsification → systemic repair → regression evidence → v2 → fresh blind attack**,
which is a materially stronger claim than "we fixed ninety bugs".
