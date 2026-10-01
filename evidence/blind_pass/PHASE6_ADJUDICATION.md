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

## 6.1d — `depth_exposure`'s surplus flag was roster-wide *(closed; two owner decisions raised)*

Found independently by two passes (**I-06** and **J-06**), which is the strongest signal in the
whole log — and both were right.

`EXPOSURE_NO_SURPLUS`'s own label reads *"not measured — you hold no backup **here**, so there is
no surplus to value"*. That is a per-position claim. The computation was
`has_surplus = len(roster_players) > len(starting_ids)` — **one boolean for the whole roster**,
stamped onto every position alike. `draft_room` prices `worst_loss` **only** under
`EXPOSURE_MEASURED`, so a single irrelevant bench body switched pricing on everywhere.

Reproduced: 8 starters and no bench → every position `no_surplus`, correctly. Add **one bench
kicker** → QB/RB/WR/TE all flip to `measured` with identical arithmetic, and the number they are
now stamped as measuring is the lone starter's own whole value.

**Asked of the solve, not of a rule.** A first attempt *did* state it as a rule — "a bench player
who can occupy a slot this position can reach" — and it was wrong in a way that looks right: a
bench RB can play FLEX, and a tight end can also reach FLEX, so the rule called TE covered. It is
not; if the tight end starts in the dedicated TE slot, losing him empties a slot no running back
may fill, and the measured loss came back as his entire value — the number saying plainly that
nothing covered him while the basis claimed depth. The re-solve already answers this exactly:
cover existed for a starter iff removing him drew a **non-starting** player into the lineup.

`all`, not `any`: a position is `no_surplus` when **any** of its starters cannot be covered. The
distinction is reachable, not theoretical — a search of 4000 random roster/league shapes found 3
mixed positions, every one involving a multi-eligible player, and one is pinned as a fixture.
Stated as the judgement it is, not dressed as a derivation.

**Effect, measured on a real 10-round 12-team draft: 22 of 48 (seat, position) cells change from
`measured` to `no_surplus` — 45.8%**, every one in the direction of refusing to call something
depth evidence that it is not.

### The consequence, and why it is NOT the mistake of §6.2

Two `ContextElevatedBecameReachableTests` assertions — the very ones §6.2 un-marked — fail again.
They are re-marked, and this time with the discriminating A/B that was missing before, run in one
process with the single basis rule toggled:

| | per-position | roster-wide |
|---|---:|---:|
| `depth_exposure` max | 9.24 | 9.24 |
| `depth_exposure` nonzero rows | **588** | **898** |
| `need_bonus` max | 8.33 | 8.33 |
| `displacement_adj` min | −90.00 | −90.00 |
| gap max | 8.33 | 13.21 |
| share ≥ 12 | 0.00% | 7.72% |

**Every number is unchanged.** What changed is which rows carry the term *as a price*: 310 stop,
and they are exactly the rows whose position has no backup. Last time the tell was that **no term
shrank at all** — the co-occurrence vanished because four players had been withheld by a defect.
That tell is what a bare "the population changed" lacks, and it is why marking a test on that
alone resolves the ambiguity by assertion rather than by evidence.

It lands where this class's own docstring predicted: the badge became reachable when `#139` added
`depth_exposure` and *"the gap's ceiling tripled, the constant did not move"*. Pricing that term
only where it is evidence puts the ceiling back — max gap **8.33**, against the **8.67** the class
records for the pre-`#139` state.

### OPEN OWNER DECISIONS (`#184`, `#56`)

1. **What should light `context_elevated`.** Its threshold is `NEED_BONUS_MAX`, a cap on one term,
   read as a threshold on the sum of four. The class filed that warning against itself; it is now
   demonstrated rather than argued.
2. **Should a `no_surplus` position be priced for depth at all?** It is the *most* exposed a
   roster can be, and it is currently priced at nothing. `draft_room`'s rule (price `worst_loss`
   only under `measured`) predates this repair and is untouched by it — this repair only made the
   basis truthful. Whether that rule is right is a valuation question.

---

## 6.1c — `need_bonus`'s flex share: the prose was wrong, not the formula *(closed)*

**W-L09.** Three comments in `draft_room` said *"flex demand only counts once a team's dedicated
slots are already filled"*. The formula has never done that — the two terms are **additive**, and
both fire at `filled == 0`. Measured on an empty roster, 12-team PPR: **RB 8.67** against a
dedicated-only **8.00**.

**The claim is withdrawn rather than implemented**, because the formula is the better of the two.
A position with two empty dedicated slots *and* flex capacity genuinely carries more demand than
one with two empty dedicated slots and no flex eligibility; the additive form says so, and a gate
would erase the difference. What the prose was reaching for is delivered by the **ratio**, and
that is enforceable: the flex term is capped at one share, so it contributes at most **1.0**
against a dedicated slot's **4.0** — one unfilled dedicated slot outweighs the entire flex demand
of any position, in every format. Now pinned as an invariant derived from the two constants.

**And the constant was load-bearing and completely unnamed.** `NEED_BONUS_PER_DEDICATED_SLOT`
appears in five test files; `NEED_BONUS_PER_FLEX_SHARE` appeared in **none**, and zeroing it passed
the entire suite. It is not a rounding term — for any position with **no dedicated slot** in a
format it is the *whole* positional-need signal:

| format | position | with the term | zeroed |
|---|---|---:|---:|
| `IDP_FLEX`-only | DL / LB / DB | 0.67 | **0.00** |
| no TE slot | TE | 1.00 | **0.00** |

Mutants killed: zeroing the constant (2 failures, previously green across the whole suite), and
implementing the gate the prose described (1 failure).

---

## 6.3 — the invariant registry *(built)*

The process repair for the failure mode at the top of this file, and this session earned it six
times over. `invariant_registry.py` records, per invariant: the claim, **the population it was
proven over**, a callable that enumerates that population, the size it had when last verified, and
the tests that pin it. `test_invariant_registry.py` re-counts and fails when a number moves.

A failure there is not a bug report — it is the notification this audit never got. The stated
response is: re-verify the claim over the new population, **then** update the census, in that
order, because updating the number first is how a registry becomes a rubber stamp.

Seeded with five invariants, all measured in this audit rather than added for completeness:

| invariant | population | census |
|---|---|---:|
| `TEAM_SPECIFIC_CAPS` bounds the capped terms, not TAV − UV | team-specific terms | 4 |
| `displacement_adj ≤ 0` for a single-position candidate | priced positions | 9 |
| an absent quantity reaches a caller as `None`, never `NaN` | emitted board columns | 30 |
| depth numbers are evidence only under `EXPOSURE_MEASURED` | basis vocabulary | 4 |
| one engine figure reads the same on every surface | Python render sites | 8 |

Two vocabularies got a home so they could be counted: `draft_room.TEAM_SPECIFIC_TERMS`, and
`BALANCED_BOARD_COLUMNS` / `UPSIDE_BOARD_COLUMNS` (previously two inline lists at the two return
sites, which is how the absence contract came to be enforced over a hand-picked subset).

### The registry caught three things on its first run, two of them mine

1. It named a test class that **does not exist** — I had invented the name. The guard that checks
   `pinned_by` resolves is there because a registry claiming coverage that is not there is worse
   than no registry, and it fired immediately.
2. Two censuses were **guesses** rather than measurements (8 vs 9 positions, 9 vs 8 render sites).
3. Worst: `_tav_team_specific_terms` **intersected with a hard-coded set**, so a fifth term could
   arrive and the count could not move. That is the exact tautology this module's own docstring
   warns against, committed *inside* the guard against it — and a mutation found it, not review.

Mutants killed after the fix: a fifth team-specific term (4→5), a genuinely new board column
(30→31), a fifth exposure basis token (4→5), and **one Streamlit render site reverted to a bare
f-string** (8→7) — the last being precisely the regression §6.1e repaired.

Also converted: two `CHARACTERIZATION` tests that AST-walked `compute_draft_board` for a
`results[[...]]` literal. Giving the columns one home made the slice a `Name`, the walk matched
nothing, and `emitted` came back an **empty set** — caught by their own non-vacuity guards, doing
exactly the job they were put there for. Both now read `board_emitted_columns()`, which is simpler
and stronger than re-deriving names from the syntax that happens to spell them today.

---

## Still open in Phase 6

- **6.1c** `need_bonus`'s bound and its flex-before-dedicated formula
- **6.1d** `depth_exposure`'s roster-wide surplus flag
- **6.3** the invariant registry — a maintained list of each stated invariant **and the
  population it was proven over**, so a repair that expands a population has something to
  re-check against. 6.1b is the case for it: four documents carried one invariant, and the
  population that broke it was introduced by a change none of them mention.
