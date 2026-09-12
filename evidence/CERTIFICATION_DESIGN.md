# What certification certifies: invariants across a configuration space, not one league

> **Status: ARCHITECTURAL COMMITMENT (owner's ruling, `#251`).** This supersedes the working
> assumption that a 33-arm PPR battery is universal evidence about the engine. It does NOT
> replace it with the assumption that Fourth and Forever is canonical.

## The ruling, in the owner's terms

PPR, half-PPR, TE premium, first-down bonuses, completion bonuses, roster sizes, flex counts,
superflex and dynasty-vs-redraft are **configuration dimensions**, not foundational assumptions.
The architectural requirement is that the engine **ingests arbitrary supported league settings
and reasons correctly over them**. So the thing to freeze is not *"the engine works for F&F"* —
it is:

> **the engine's behaviour is correctly governed by league configuration, and the core
> invariants survive across the supported configuration space.**

The trap this exists to avoid is named explicitly: *do not replace one stale foundational
assumption ("PPR is representative") with a new one ("F&F is the canonical rulebook")*.

## 1. Which assertions are configuration-invariant, and which are not

**Derived, not declared.** `config_space.py` reads the split out of `draft_battery`'s own
structure: whatever `structural_findings` aggregates is the invariant set, because that
function's contract is *"a finding here is a DEFECT, not an observation"*; whatever else
`audit_trajectory` emits is configuration-dependent, because that section says *"no verdict,
because a verdict would need a number I chose."* Add an audit to either half and the
classification follows it. Declare it in neither and `test_config_space` fails.

**INVARIANT — must hold in every supported configuration. These are what certification certifies.**

| audit | domain |
|---|---|
| `duplicate_picks` | Every configuration, no precondition. The only one that never consults the league. |
| `unpriced_picks` | Every configuration, no precondition. No rulebook makes it acceptable to spend a pick on a player the engine could not price. |
| `undraftable_positions` | Every configuration, no precondition. Holding a position the league offers no slot for is a pool filter that leaked. |
| `unfilled_starting_slots` | Every configuration **where `rounds >= startable slots`**. See the correction below — this precondition was wrong until a real league entered the matrix. |

Note the shape they share: **the assertion is configuration-free while its REFERENT is
configuration-derived.** "Which positions are startable" comes from the league; "it must be able
to field them" does not.

**CONFIGURATION-DEPENDENT — expected to move with the settings. Reported, never asserted against
a fixed value.** `shape`, `margins`, `qualifiers`, `regimes`, `strength`, `unpriced_at_decision`.
A different number in a different league is the configuration layer working, not a regression.

## 2. PPR and F&F are both configuration points. Neither is canonical.

`config_space.coverage` measures a matrix against real captured leagues and separates two
questions that look alike:

- `varied` — an axis the matrix actually moves. Anything held constant is an axis the run cannot
  say a word about, however many arms it has.
- `value_never_produced` — a coordinate a REAL league carries that no arm emits.

Measured on the committed matrix:

| matrix | arms | axes | varied | F&F coordinates never produced |
|---|---:|---:|---:|---:|
| before (`#250`) | 33 | 91 | **16** | **21** |
| after, one capture added | 34 | 91 | **77** | **0** |

**One real captured league moves more axes than the other thirty-three arms combined**, because
all thirty-three are built from a single base rulebook with a `rec`/TE overlay. The fixture's own
uncovered count is **0 — by construction**, since the matrix is built from it. That tautology is
precisely why its coverage was never evidence about anything else.

The capture enters as `CAPTURE_fourth_and_forever`, supplied **directly** and never through
`build_mock_league`, which overwrites `rec` and caused `#250`'s original error. A captured league
enters as itself or not at all.

## 3. Certifying deliberately

The instrument makes a proposed matrix's coverage measurable **before** the run is spent, which
is what makes "deliberate" possible rather than aspirational:

```
python3 config_space.py      # classification + coverage of the committed matrix
```

The principle for a certification set: cover each varied axis at its extremes, plus every real
captured league as its own point. Which axes deserve extremes is a design decision with a cost
attached, and it is the owner's — not something to settle by widening the matrix until the run
stops fitting in a night.

**What a certification run then proves, and in two separate columns:** zero invariant findings in
every cell, and a *report* of the dependent outcomes per cell with no pass/fail attached.

## 4. The configuration layer is demonstrated to work — already, with no new run

`#250`'s arms are the first evidence in this repository of the two halves behaving differently in
one measurement. Across seven arms spanning two rulebooks, two flex counts and two roster sizes:

- **every invariant held** — every lineup filled, every pick priced, in all 84 seats;
- **the dependent outcome legitimately reversed sign** — margin `−22.53` under PPR against
  `+29.43` under F&F's rulebook, on the same roster.

That is the configuration layer doing its job. It is pinned by
`test_config_space.TheConfigurationLayerIsDemonstratedToWork`, which reads the committed
artifacts rather than re-running anything.

## 5. Parked, narrow, separate

**`rec` versus export selection.** The rulebook moved several things at once: `rec` 1.0→0.5, the
TE premium, first downs, the completion bonus, and — because `set_league_format` picks a rankings
file per format hint — the export itself. `#248`'s arm B is useful precisely because of its
defect: it shows first downs + completion bonus + TE premium, *at PPR reception value on the PPR
export*, change the verdict by nothing. So the live suspects are `rec` and its export.

Separating them is a question about **one input**, not about a league, and it only matters if the
architecture needs to know. Recorded here so it is not lost, and deliberately not pursued.

## What this run of work CORRECTED, found by doing it

Adding one real captured league to the matrix immediately failed two committed tests, and both
were right to fail:

`unfilled_starting_slots`' precondition was written and enforced as **`rounds == len(roster_positions)`**.
The audit asks whether the STARTING lineup can be fielded, so what it needs is
**`rounds >= startable slots`** — nothing about the bench. The two were indistinguishable for as
long as every arm was a mock league with no IR. The first real league (29 slots, 26 draftable,
10 startable) failed the equality while satisfying the property comfortably.

That is `#242`'s defect — an equality standing in for the question actually being asked — one
layer up, and it stayed hidden for the same reason: **no configuration in the matrix could tell
the two apart.** Which is the whole argument for this document.
