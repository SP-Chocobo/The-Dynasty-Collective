# `#52` synthesis — six waves, twelve passes, and what actually has to be repaired

> **What this is.** `FINDINGS_LOG.md` is the append-only record of what each pass claimed.
> `LEDGER.md` carries verdicts for waves 1–4. **This file is the first document allowed to
> reclassify and recombine**, because the owner's instruction was to build the whole list before
> doing so, and the list is now built.
>
> Its job is not to re-list findings. It is to say **what is upstream of what**, so repairs land in
> an order where each one is measured on a tree the previous one already corrected.

## The one-paragraph state

Six waves produced no clean wave; the streak for the stopping condition never started. The severity
did not decay across waves — it escalated, ending on a data-identity defect that silently deletes
real, startable players from the pool. **The findings are not ~90 independent bugs. They are eight
clusters, and two of them sit upstream of everything else**, which is why a one-at-a-time repair
pass would have produced numbers that were wrong for reasons already fixed.

---

## MEASURED THIS SESSION — the name-collision class

Pass K found one instance. It is a class, and here is its measured size, re-run from the repo root
on the owner's own league format.

**Instance 1 — `load_all`'s per-file dedup (`data_merger.py:1186`).** `drop_duplicates(subset="norm_name")`
runs on every rankings file *before* `_reconcile_rows` builds its position-aware key:

```
12 rankings files
TOTAL same-position drops (the case the comment justifies): 22
TOTAL CROSS-POSITION drops (never considered):              31
distinct real players deleted from the pool:                10
```

The ten: **Jordan Love** (QB GB, rank 99), **Javonte Williams** (RB DAL, rank 68),
**Malik Washington** (RB LV, rank 192), **Kyle Williams** (WR NE), and six IDP — B Murphy, D Turner II,
J Johnson, J Martin, D Walker, Q Williams.

Verified end to end:

```
Jordan Love      QB GB   matched=False  proj=None tv=None rank=None
Javonte Williams RB DAL  matched=False  proj=None tv=None rank=None
Malik Washington RB LV   matched=False  proj=None tv=None rank=None
Ja'Marr Chase    WR CIN  matched=True   proj=339.0 tv=84.0 rank=5.0   <- control
```

A starting quarterback, in a **superflex** league, has no projection, no trade value and no rank.
The two guards written to protect contested identities — `_dedup_by_name_and_position` and
`_drop_contested_identities` — never fire, because the row they exist to protect was deleted one
stage earlier.

**Instance 2 — `_compute_percentiles`' `position_by_key.setdefault` (`data_merger.py:1882`).**
Measured: **101 of 2,600** external rows carry a `name_key` that maps to more than one raw position;
the cross-*group* subset (the ones that actually change a percentile pool) is pass K's 19. Examples
that cross a group boundary: `('b','allen') → [QB, RB]`, `('c','allen') → [LB, WR]`,
`('b','young') → [DE, DL, QB]`.

**Instance 3 — the rookie lookup (`draft_room.py:1009`).** `dict(zip(_name_key, rookie))` is
last-row-wins. Measured: **6 keys carry conflicting rookie flags** — `j lane`, `j love`, `j taylor`,
`k allen`, `k coleman`, `m washington`. `j love` holds nine rows across RB/QB/S with `True` and
`False` both present.

> **Correction to my own probe.** My pool-side check reported 0 rookie mismatches. That is my probe
> being wrong, not pass K's 58 — I rebuilt the key with `name_key(normalize_name(...))` where the
> pool builds it differently, so my lookup never hit. K's 58 stands; mine is withdrawn.

**Instance 4 — `_resolve`'s exact and alias paths.** Both passes enumerated the branches and agree:
the exact and alias paths apply neither the namespace nor the offence-position rejection the key
path applies, against a docstring saying a crossing resolution "contradicts the merger's own identity
model, **whatever path it took**". Measured **0 of 1,626** today — and both passes said plainly they
are not confident it holds for a different vendor file or the full-name free-agent table.

**Instance 5 (instruments, same class).** `run_asset_character_measurement.py:84` and
`run_age_signal_measurement.py:73` both dedup on a bare name key.

---

## THE EIGHT CLUSTERS

### A. IDENTITY — the pool is missing real players *(upstream of everything)*

Instances 1–5 above. **Blast radius: total.** Every price, every board, every drafted roster, every
battery arm, every smoke seat and every number in `evidence/` was computed over a pool missing ten
players, one of them a startable superflex QB. Nothing downstream can be trusted to the precision of
those ten until this is fixed.

**Ordering consequence: A goes first, and every measured claim in this repository is stale until it
does.**

### B. PRECEDENCE AND PROVENANCE — the wrong file wins *(also upstream)*

- **K-03**: a league-specific upload with an ordinary filename loses every field to the stale
  committed baseline, against a docstring promising the opposite. Format is detected from **filename
  only**; the app saves uploads under the user's own filename. Measured: doubled values ignored until
  renamed.
- **K-04 / L-04**: declared `source_date` is never validated. `8/28/26` beats `2026-08-18`; a blank
  date column becomes `NaN`, is labelled **declared**, and outranks honestly undated rows.
- **L-10 / K-06**: the conflict ledger names the rule that decided the *winner row*, not the rule
  that decided the *chosen field value* — wrong exactly when the winner contributed nothing.
- **L-13**: absence is priced as exactly 60 days old, so an 89-day-old dated source loses to an
  undated upload.
- **W4-15 — DISPUTED**, unresolved: G measured 18 players drawing from a "standard"-tagged export in
  a PPR league; H measured 0 rows with mixed sources and called it a null.

**Blast radius: which numbers enter the pool at all.** Same argument as A — repairing anything
downstream first means measuring it against inputs that are about to change.

### C. TWO MODELS OF ONE QUESTION

The single most-corroborated cluster in the audit; four passes hit it independently.

- **Take models (I-01, J-03, K-02):** `estimate_survival` normalises `RANK_TAKE_PROBABILITY` over the
  board; `positional_forfeits` uses it raw. `#206` was wired into one consumer. Measured:
  `expected_taken` = **23.3 players from 22 picks**, and **0.0 QBs** in a superflex league.
- **The pace prior (J-01, I-02):** produces **survival = 0.0 exactly** — certainty — which its own
  docstring says it never does, reintroducing the zero `#206` exists to remove.
- **The consequence at the chair (J-04):** the debate is told *"Cost of delaying QB entirely:
  measured 0"* while the model saying those QBs are gone with certainty is withheld from it.
- **K-11:** `FORFEIT_SCALE_MAX = 100` is justified by a 0–100 scale `_scale_vor_to_bpa` no longer
  produces, so the forfeit term saturates.
- **L-02:** `pick_analysis` computes forfeits off **upside-mode curves** under `mode="auto"` — the
  guard tests the requested string, not the resolved mode.
- **W4-08:** two health models; **I-15:** `roster_diagnostics` solves lineups with primary-position
  eligibility while the engine assumes full eligibility; **L-03 / K-10:** the counterfactual
  subtracts a vendor-only TAV from a scoring-aware one.

**Depends on A and B** — the take tables are read over the pool A corrupts.

### D. THE ABSENCE CONTRACT, broken in eight places

`W4-07` (unpriced rows carry a `measured` displacement), `W4-21` and **my own finding** (upside mode
omits the five team-term columns entirely, and the same absent fact renders as `need=0.0` but
`disp=None` — a measured zero and an absence for one cause), `L-01` (denial reports a *measured*
zero at a node where nothing was consulted; survival got a fourth state, denial did not), `L-05`
(`outcome_record` collapses damaged into absent and wipes the revision trail), `W4-24` (`store_io`'s
bare `except OSError` against a docstring saying otherwise), `J-14` (`_sum_weeks` conflates an outage
with an empty week), `depth_ratings.depth_label` (returns `None` when every peer measures 0.0),
`measurement.counted` (treats `NaN` as present).

**Latent, not live:** the five team terms are absent from `_records_with_normalized_nan`'s column
list, but measured **0 NaN on every board state I tried**. Record as a gap, not a defect.

### E. THE INSTRUMENTS CANNOT SEE — including the ones that grade the engine

- **Mutation testing, run independently by both Wave 6 passes and agreeing:** three live valuation
  constants survive their own corpus at absurd values (`NEED_BONUS_PER_FLEX_SHARE = 0.0` → 307 green;
  `NECESSITY_RUN_BONUS = 500.0` → 275 green; `TIME_HORIZON_SLOPE = 0.0` → 277, no relevant assertion),
  and **`RUN_TAKE_PROBABILITY_CAP = 9.0` — a probability cap above 1 — survives all 51 tests**. The
  flex-share constant is not dead: **every IDP position's need bonus comes entirely from it.**
- **`assertion_floors` — DISPUTED.** Pass I: defective four ways, including an empty floors file plus
  an empty test module exiting 0 with "no guarantee has shrunk". Pass J: the `skipTest` hole is
  inside the docstring's declared limit. **Both stand; adjudicate before repairing.**
- **`quantity_readers`** grades on bare attribute-name collisions; **`suite_taxonomy`**'s tier is the
  substring `"DataMerger()"` and its stated 53 modules / 1.5 s measures **123 modules / ~205 s**;
  **`format_axes_exercised`** derives axes from three format keys so roster-slot composition is not
  an axis at all; **`doc_index`** files a document reading *"Nothing in this file is withdrawn"* under
  WITHDRAWN; the context-budget test asserts on 5 where the operative count is 84; two more text-scan
  guards where an AST walk exists next door.

### F. THE WITHHELD SURVIVAL NUMBER LEAKS THROUGH FIVE PATHS

`pick_necessity` (W1-07) → `denial_value`, rendered unconditionally (J-02) → the snapshot diff,
printing the raw numbers to chairs *and* to the person (W4-16) → three system prompts offering them
as given inputs with a worked example (W4-04, J-02d) → `screen_context` printing "survival NN%" into
the Prytaneum seed (I-05). **And the suite pins the leak** (W4-17): one test asserts survival is
absent from the candidate block; two more assert a survival-only delta *does* reach the chair.

**Depends on C** — repairing the take models changes what is being leaked.

### G. STATE, CACHE AND PERSISTENCE

`L-06` (Draft Room state leaks **across leagues**; A's debate renders under B's board with no
staleness note), `L-07 / K-08 / I-14` (cache key omits pick contents, season projections and
league format), `W4-24` + `L-11` (a write silently dropped, and `upload_batches.record` returning a
batch id for a batch that was never persisted, losing the user's stated as-of date while the UI
reports success), `J-13 / I-13` (`sleeper_client`'s `write_text` on a 10 MB cache — the pattern
`store_io`'s own docstring measured at 91,956 empty reads of 98,405), `K-07` (**18.0–18.9 s** per
button click in the mock view from a double reload), `J-12` (`draft_history` wired to nothing),
`W4-23` (resume joins arms from different captures under one provenance block).

### H. CLAIMS THE CODE DOES NOT SUPPORT

Cuts across every cluster; the sharpest is **W4-02**: `NECESSITY_DENIAL_SATURATION` and
`CONTEXT_ELEVATED_THRESHOLD` both derive from a caps tuple whose comment hand-exempts the fourth team
term *"deliberately … it is non-positive by construction"* — the premise measured at **+79.44**, with
TAV − UV reaching 87.82 against a claimed bound of 36. The comment's own next sentence says the bound
is derived precisely so a fourth term would move it automatically.

---

## WHAT THE CLUSTERS SAY ABOUT ORDER

1. **A and B are upstream of all measurement.** Any repair validated before they land is validated
   against inputs that are about to change. They go first, and the pricing evidence gets re-measured
   after.
2. **C depends on A/B**; **F depends on C**; **D and G are largely independent** and can land
   wherever they cause least suite churn.
3. **E is not a phase at the end.** The mutation result means the suite cannot currently feel these
   constants move — so a repair "verified green" proves less than it looks. The discipline that
   follows: **every repair in A–G ships with a test that would have failed before it**, and the
   instrument-specific defects (`quantity_readers`, `suite_taxonomy`, `doc_index`) form their own
   phase at the end, because they gate nothing.
4. **Two disputes are adjudicated before, not during, their repairs:** `assertion_floors`
   (defect vs declared limit) and `W4-15` (cross-format mixing).
5. **Anything that is an engine-design change rather than a defect goes to the owner**, not into a
   repair commit. `#184` is the standing precedent.
