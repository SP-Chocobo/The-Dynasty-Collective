# Phase 6 — invariants and the populations they range over

Ordered as the repair mandate orders it. Each item records what was **measured**, what was
**changed**, and what was deliberately **not** changed.

---

## 6.1a — the round-boundary off-by-one *(closed, commit `e18731c`)*

**Two independent derivations of "what round is it" both read the count of COMPLETED picks as
the current round.** Off by one at every round boundary, correct everywhere else — which is why
both survived every suite.

| site | consumed by | effect |
|---|---|---|
| `draft_room.compute_draft_board` | `use_upside` | `mode="auto"` entered upside scoring one pick LATE; the first pick of each round from the boundary on was valued under the other regime |
| `pick_synthesis.build_snapshot` | `compute_pick_necessity` | `LATE_ROUND_NECESSITY_CAP` skipped the first pick of every late round — necessity **68.5 "PREFERRED" at 15.01**, capped to **21.0 at 15.02**, nothing changing between them but the arithmetic |

**The corroboration neither module could supply alone.** `draft_simulation._picks_by_mode`
already computed the same boundary the other way — `(UPSIDE_MODE_DEFAULT_ROUND - 1) * num_teams`.
It was right and the board was the outlier: the artifact reported **168/132** on a 12×25 while
the trajectory produced **169/131**. Nothing in the suite had ever asked the two the same
question, so the disagreement was invisible for the whole life of the defect.

**The test pinned the bug in its fixture.** `test_draft_room`'s boundary test built
`8 * round_no` picks and called that `round_no`. Its *claim* — auto flips at exactly round 15 —
was correct and is unchanged; its *encoding of which round it is* was the same off-by-one. Both
corrected together. New `ReportedModeSplitMatchesTheBoardTests` ties `_picks_by_mode` to the
board it describes, so the two derivations cannot drift apart again; `_picks_by_mode` had **no
coverage at all** despite being reported into the artifact.

Both tests verified to kill the off-by-one mutant.

---

## 6.1b — `displacement_adj`'s sign *(closed as a CONTRACT repair; the valuation question is open)*

**The code is correct. Four documents and two tests stated an invariant the code deliberately
violates.**

### The mechanism, measured

`shared_slot_alternatives` prices a slot at `max(level)` over the positions the slot **admits**.
Therefore:

- a **single-position** probe reaches only slots that admit his position, so every reachable
  alternative is at or above his own anchor, and `adjustment <= 0.0` — *provably*, not by
  observation;
- a **multi-eligible** probe is anchored on his PRIMARY level but reaches slots through a second
  eligibility that need not admit the primary at all. Those may be priced below the anchor, and
  the term then **lifts**.

One bound covers both, and it is derived rather than chosen:

```
adjustment <= free_alternative - min(alternative over reachable slots)
```

which *is* `0.0` in the single-position case.

**Grid: 960 probes, five rulebooks, three roster depths.**

| population | n | `adjustment > 0` |
|---|---:|---:|
| single-position | 120 | **0** |
| multi-eligible | 840 | **144** — every one inside the bound |

Live cases: Travis Hunter (WR primary, WR/DB) at **+79.44** on the owner's IDP board, TAV − UV
at **87.82** against a claimed ceiling of 36.0. **Not IDP-only** — on a plain one-TE rulebook
with the owner's pool shape an RB/TE anchored on TE is lifted **+158.0** with his own TE slot
standing open, and three RB/TE players are in the real capture.

### Why it went unseen — the audit's central mechanism, exactly

`#216`'s second half added per-slot alternatives. That change **expanded the population** the
term ranges over; the "never positive" invariant, proven over the old population, silently
stopped holding; and the tests stayed green **because they never entered the new domain**:

- `test_the_adjustment_is_never_positive` passed **no `slot_alternatives`** in every case and
  used **single-position** probes only — the two conditions required for the failure, both
  absent.
- `test_an_open_dedicated_slot_deducts_exactly_nothing_on_any_roster` ranged over single
  positions only.
- The real-rulebook pin holds over **477 priced rows containing exactly ONE multi-eligible row**
  (Hunter), whose DB half reaches nothing in a non-IDP league and so reports exactly `+0.00`.

### Changed

Contract corrected in all four places it was stated — `lineup_optimizer.displacement_level`
(source), `draft_room.displacement_adjustments`, `pick_synthesis.TEAM_SPECIFIC_CAPS`,
`CDME_CONTRACTS.md` §4b. Tests split into their two populations, with the positive branch
exercised on exact hand-checkable numbers and the grid's size pinned by derivation rather than
by a floor.

Mutation results:

| mutant | outcome |
|---|---|
| clamp `adjustment` back to `min(0.0, …)` | **killed** (2 failures) |
| floor `displaced` at the anchor — the case the clamp's own comment defends against | **killed** (2 failures) |
| remove the reachable-floor clamp entirely | **survived** — and correctly so: measured across 642 probes the clamp **never binds**. It is a float-error guard against a 1e6 probe, by its own statement, not a behavioural claim. Recorded rather than chased with a manufactured test. |

### NOT changed, and deliberately

**No value moved.** Whether the lift is the right price is genuinely arguable in both
directions — the candidate really can take the cheap slot while the free alternative still fills
his primary's (phantoms are pinned per slot precisely so that is the lineup solved), and equally
it may be double payment, since `eligibility_bonus` already prices multi-eligibility and is
CAPPED for that reason.

That is a valuation change under `#56`, not a repair. **Open owner decision**, recorded at
`CDME_CONTRACTS.md` §4b. `NECESSITY_DENIAL_SATURATION` and `CONTEXT_ELEVATED_THRESHOLD` are now
known to rest on the false premise; **re-deriving them waits on the same ruling**, because
choosing a new saturation point and a new threshold for a distribution nobody has argued for is
`#56`'s exact prohibition.

---

## 6.1e — one number, two surfaces, two answers *(found BY this phase's re-suite; closed)*

Not from a Fable pass — surfaced when `test_216_room_integrity` went red after the earlier
identity repairs, and **it is the audit's central mechanism running in the other direction**.
Every other instance was a repair expanding a *population of inputs*. This one expanded a
**population of VALUES**: an invariant that held over the old numbers stopped holding over the
new ones.

**The defect.** Streamlit renders engine figures through Python f-strings; the Draft Room board
renders the same figures through the browser's `toFixed`. Nothing in the repository stated a
rounding rule, so each surface took its language's default — and they differ:

| | `16.5` | `-16.5` | `13.5` |
|---|---|---|---|
| Python `format`, half-to-**even** | `16` | `-16` | `14` |
| `toFixed`, half-**away from zero** | `17` | `-17` | `14` |

They disagree by a whole unit on any figure landing exactly on `.5` above an **even** floor —
half of all half-values, in both signs.

**Measured, in the shipped app.** Caleb Williams' `team_acquisition_value` is exactly `16.5`.
`app.py` showed him as **16** in the metric row; the Draft Room showed **17**. One number, one
session, two answers. It was green at `v1-freeze` and went red only because an identity repair
moved a value onto the boundary — verified by running the test against `v1-freeze`'s engine
(green) and against pre-round-fix `HEAD` (red), so the exposure is dated precisely.

**The repair.** `design_system.figure` states the screen's rule **once** (`#126`), and both
surfaces call it — nine `app.py` render sites, and the test, which had been *re-implementing*
the formatting it was checking and so disagreed with it exactly where the two implementations
differ. `figure` returns `None` for absent and non-finite input rather than putting the string
`"NaN"` on screen (`#187`).

Verified against **real Chromium**, not against the specification: 50 values × 3 digit settings,
**0 mismatches**, covering both parities of floor, both signs, and the float-representation
cases (`1.005`, `2.675`, `8.575`) that defeat naive implementations. The one genuine divergence
found was **negative zero** — `toFixed` prepends `-` only when `x < 0`, which `-0` is not — and
it was found *by the new test*, not reasoned about; `-0.004`, which must keep its sign, is
pinned beside it so neither half can regress.

---

## 6.1f — the misquote guard was reporting the audit's own mutation tables *(closed)*

Also surfaced by the re-suite, also pre-existing at `HEAD`. `test_prose_names` checks that prose
quoting a constant's value agrees with the code, and reported **18 contradictions**. Every one
was a **mutation-battery row** — ``NECESSITY_RUN_BONUS = 500.0` | 275 | all pass` — where the
quoted value is deliberately, definitionally *not* the constant's value.

`HISTORICAL_MARKERS` already carried `ablation`, `probe`, `experiment`, `counterfactual`. Mutation
testing is the same category and was simply missing from the vocabulary — and this repository
records mutation batteries by standing convention at the bottom of test modules, plus every
battery in the preserved `#52` log. So the check that exists to catch **one** stale number was
drowning in its own evidence, which is how a guard stops being read.

Markers added: `mutat`, `mutant`, `planted`. **18 → 0.** Both halves pinned by a new test — a
mutation row is shielded, the *same* misquote in ordinary explanatory prose is still caught —
and the word-start anchoring re-checked, since widening an allowance is how a guard quietly stops
guarding. Two self-inflicted errors were caught by that test rather than by review: the marker
comment initially *committed* the misquote it was describing (the checker reads its own source),
and `mutant` does not share the `mutat-` stem.

**No value changed in either item.**

---

## 6.2 — THE FULL SUITE, and seventeen failures it had been hiding

**Running the full suite for the first time since Phase 1 found 20 failures. Three belonged to
that day's work. Seventeen were mine, from Phases 1–5, and had been red for five phases.** They
reproduce at `HEAD` with the day's work stashed and are **green at `v1-freeze`**, verified in a
clean worktree — so they were introduced by the repairs, not inherited.

The cause is not subtle: between phases I ran the modules I judged affected. That is the same
mistake the audit's own record shows me making once before, and it hid seventeen failures across
nine modules.

### The root defect behind most of them

`merge_player`'s canonical key was `(norm_name, position GROUP)`. `draft_room`'s contested-identity
guard reads that key as *"these two rows were priced off ONE vendor record"* and withholds the
price from both — which is right, and is what stops Bijan and Brian Robinson (both RB ATL, one
published row between them) from each claiming a value belonging to one of them.

But the group is **coarse**: QB and RB are both `offense`. So two players `_resolve` had correctly
matched to two *different* vendor rows collided anyway, and both were refused. Phase 1.1 recovered
those players from the loader and this key threw four of them straight back out — which is exactly
why the damage looked like a *consequence* of the recovery.

Keying on the **raw position** repairs it. The Robinson case is untouched: same name, same
position, same single record, so they still collide and are still both refused.

| | |
|---|---|
| **Recovered** | J Love (the GB QB *and* the ARI RB), J Williams, M Washington — 6 pool rows, priced again |
| **Still refused** | K Williams — two rows at the **same** position on the **same** club, which no name/position/team test can split. Correct. |

### Three `@unittest.expectedFailure` marks, withdrawn

I had marked three tests expected-to-fail with a confident decomposition of why the population had
legitimately changed. **The decomposition was real and the diagnosis was wrong** — it described the
wrong cause. I bisected to the Phase 1 commit and stopped, which found the commit and not the
defect inside it. All three pass untouched once the key names the record.

> The lesson: *"a repair changed the population, so the invariant legitimately stopped holding"*
> and *"a repair broke something"* are the same shape, and this audit exists because the two are
> hard to tell apart. Marking a test `expectedFailure` resolves that ambiguity **by assertion**.
> What was missing was one check: were the players the repair recovered still priced afterwards?

### The other three genuine defects

1. **58 positionless assets collapsed to one.** The within-file identity key is
   `norm_name + "|" + position`; `position` arrives as pandas' `str` dtype, where `astype(str)`
   leaves a missing value as NA rather than `"nan"`. NA propagates through `+`, and
   `drop_duplicates` treats nulls as **equal** — so 48 rookie pick slots and 10 future picks got
   one identical null key. `pick_value("1.01")` survived only because the single surviving row
   happened to be a rookie slot; every future-pick price returned `None`. It reproduces *only*
   through the real loader — a bare `pd.read_csv` gives object dtype and the keys stay distinct,
   so a probe built that way reports the code is fine.
2. **The absence contract broken by the container.** `identity_basis` returns a real `None` for a
   row whose provenance was never recorded, and the column handed it back as `nan`. Cause:
   `_records_with_normalized_nan` took its columns as arguments, and the two callers between them
   selected 29 columns while naming 11. Now derived from the values (`#126`).
3. **A refusal that does not propagate** *(pinned, not repaired)*. `_drop_contested_identities`
   withholds a contested price from the **pool**; `_team_roster_players` re-resolves each rostered
   player through the **merger**, where that price still sits. Of 45 projection-only rows, 43 drop
   and 2 do not — and those 2 are exactly the contested pair. This belongs with the other
   refusal-propagation paths in Phase 7.1, which is a propagation *rule*, not five patches.

### Re-baselined, each with its reason

IDP universe 415 → **421** and matched-but-numberless 339 → **345** (the six recovered IDP
namesakes); offense supply 264 → **266** (+4 recovered, −2 correctly refused); QB counts 39 → **40**
and 28 → **29**, with `qb_startable_floor` **unchanged** at 162.0. `has_defense` is genuinely
constant across all 35 arms, so it is now **registered** in `draft_battery.UNCOVERED_AXES` with what
would close it — a ratchet that fails both when an unregistered axis goes constant *and* when a
registered one starts varying.

**Full suite: 3174 tests, green.** First clean run since before Phase 1.

---

## Still open in Phase 6

- **6.1c** `need_bonus`'s bound and its flex-before-dedicated formula
- **6.1d** `depth_exposure`'s roster-wide surplus flag
- **6.3** the invariant registry — a maintained list of each stated invariant **and the
  population it was proven over**, so a repair that expands a population has something to
  re-check against. 6.1b is the case for it: four documents carried one invariant, and the
  population that broke it was introduced by a change none of them mention.
