# The v4 blind adversarial pass — mandate and conditions, verbatim

> **Committed so the pass is REPRODUCIBLE, not as a record of its results.** Five passes launched
> concurrently against `v3-freeze` (`eac7491`) on Fable, each in an isolated git worktree.
>
> **Do not read this file to the pass itself.** It is the mandate, not a briefing. It lives under
> `evidence/`, which the mandate denies.

## Conditions

- **Model:** Fable, per the standing constraint.
- **Isolation:** one git worktree each — which makes the passes independent of one another and does
  NOT by itself make them read-only or blind. Blindness is carried by the mandate below.
- **Count:** five, concurrent.
- **Target:** `v3-freeze`, `eac7491`. Territory `v2-freeze^{}..v3-freeze^{}`.
- **Lenses chosen by:** Claude, at the owner's explicit instruction. This is the gate's known
  independence weakness, recorded in `V4_GATE_CRITERIA.md` §2 rather than hidden: the author of the
  97 commits also chose where the auditors look. Mitigated by deriving lenses from the diff's own
  structure, by including Lens D (the instruments audited as code rather than as authority), and by
  the criteria having been committed before any of this ran.

## THE ONE DELIBERATE INHERITANCE FROM v2

`MANDATE_V2.md` established split lenses on a measured ground: *"this codebase is deterministic, and
so is an audit of it."* Five readers given one lens converge on one region and re-find one another's
findings. So each pass receives the SAME preamble, constraints and reporting rules, and a DIFFERENT
`## YOUR LENS`, and each is told the others cover the rest.

## WHAT CHANGED FROM v2's MANDATE

* **The denied list is explicit and broader** — `evidence/`, the register, the decisions file, the
  repair mandate, the roadmap, the gate criteria, the freeze records, the doc index. v2 denied
  `evidence/blind_pass/`; this denies everything carrying a prior conclusion.
* **The honour condition is named as one.** Nothing enforces the denials, so each pass is required
  to list every file it opened, and told that admitting an accidental read is far cheaper than a
  silently contaminated pass.
* **Non-findings are requested explicitly** — "WHAT I CHECKED AND FOUND CLEAN" — so the report says
  what the pass actually covered rather than only where it stopped.
* **Lens descriptions name TERRITORY, never repairs.** The first draft of these lenses named the
  mandate items ("3.1's percentile population", "D8's health discount") and was rewritten: naming
  the repairs points an auditor straight at the answers, which is the briefing this pass exists to
  avoid.

---

## THE SHARED PREAMBLE, verbatim

```
You are auditing a Python fantasy-football draft engine adversarially. You are one of five
independent auditors, each given a different lens; the others cover the rest, so do not spend
your budget on territory outside yours.

## WHAT YOU ARE LOOKING FOR

Defects. Places where the code does something other than what it claims, or where a number
reaches a person carrying a meaning it has not earned. This codebase's docstrings are unusually
detailed and state intent at length -- treat them as the contract, and treat a mismatch between a
docstring's claim and its code's behaviour as a first-class finding.

## TERRITORY

The engine was frozen, audited, repaired over 97 commits, and frozen again. Your territory is
what changed:

    git diff v2-freeze^{}..v3-freeze^{}
    git log --oneline v2-freeze^{}..v3-freeze^{}

160 files, +36001/-5522, 36 production modules, 31 new test modules. Start from your lens's
surface within that range. You may read anything outside the range for CONTEXT (to understand how
a thing is used), but findings should concern the changed surface.

## BLIND CONDITIONS -- READ THIS TWICE

You have NOT been told what the previous audit found, what was repaired, what anyone considers
risky, or what conclusion is wanted. That is deliberate. Your value is entirely in finding what
nobody anticipated, and a briefed auditor re-finds the briefing.

DO NOT OPEN THESE. They contain prior conclusions and would destroy the point of your pass:

    evidence/                     (all of it -- prior findings and measurements)
    POST_AUDIT_PLAN.md            (the numbered findings register)
    OWNER_DECISIONS_PENDING.md
    REPAIR_MANDATE_V2.md
    ROADMAP_TO_FREEZE.md
    V4_GATE_CRITERIA.md
    FREEZE_RECORD*.md
    DOC_INDEX.md

You MAY read: all source, all tests, all docstrings, CDME_CONTRACTS.md, README, and the diff.

This is an honour condition -- nothing enforces it. In your report, list every file you opened.
If you open a denied file by accident, say so plainly; that is a far smaller problem than a
silently contaminated pass.

## CONSTRAINTS

- MODIFY NOTHING. You are reading. Do not repair, do not "fix while you're there".
- You may RUN things to test a hypothesis: targeted `python3 -m unittest test_x`, or a scratch
  script. Do NOT run the full suite; it takes ~40 minutes.
- Run from the repository root. A `DataMerger()` built from elsewhere silently loads nothing.
- If you want to measure the engine, note that `run_draft_battery.build_players_db_from_capture()`
  returns a (players_db, provenance) tuple, and `draft_room.compute_draft_board(merger, players_db,
  picks, my_roster_id=..., league=..., mode="balanced")` is the main entry point.

## WHAT COUNTS AS A FINDING

Actionable only if you can state all four:
  1. the affected behaviour;
  2. the concrete code path producing it (file:line);
  3. why it contradicts a requirement, invariant, contract, or documented intent -- quote the
     docstring or contract line it contradicts;
  4. reproducible evidence: a case, a measurement, a test you ran, or an argument from the code
     that a reader can check.

Speculation without a demonstrated contradiction is NOT a finding. "This could be clearer" is not
a finding. A proposal for different product behaviour is not a finding unless the current
behaviour contradicts something already stated.

## REPORTING

Return your findings IN FULL in your final report -- not a summary, not a count. Nobody can see
your working; your report is the only artifact that survives.

For each finding:

    SEVERITY: HIGH | MEDIUM | LOW
    WHERE:    file:line
    CLAIM:    what the code/docstring says it does
    ACTUAL:   what it does
    EVIDENCE: what you ran or read that shows it
    WHY IT MATTERS: the consequence to a number a person reads, or to a contract

Then:
  - FILES READ: every file you opened.
  - WHAT I CHECKED AND FOUND CLEAN: the specific things you examined that turned out sound. This
    is as valuable as the findings and tells the reader what your pass actually covered.
  - WHAT I COULD NOT REACH: anything in your lens you ran out of room for.

A pass that finds nothing and says so precisely is a GOOD result. Do not manufacture findings to
look productive. Do not inflate severity.
```

---

## THE FIVE LENSES, verbatim

### Lens A — valuation arithmetic, units, and populations

Every place a player's value is computed, scaled, clamped, converted or combined. **Units:** every
addition or comparison between two quantities — are they the same unit? A constant whose surrounding
scale changed while the constant did not is the archetype. **Populations:** every percentile, rank,
mean or normalisation — over WHICH rows? Two statistics compared must come from one population.
**Derived versus chosen:** for each constant, is it derived, and does the derivation hold? Do two
constants pricing the same input disagree on rate? **Clamps:** can the quantity reach the bound at
all, in both directions?

### Lens B — gates, backstops, and roster geometry

Every place the engine admits, excludes, demotes or promotes a candidate, and every place it reasons
about roster legality. **Does the guard bind?** Construct the input that should trip it and the
ordinary input that should not. **Sort keys:** does a decision expressed as row ORDER survive to the
pick? Are key and direction lists the same length? **Roster geometry:** subset versus intersection,
primary position versus full eligibility, per-position versus per-group; try league shapes the tests
do not use. **Capacity arithmetic:** where does N come from, and does it hold for a legal but
unusual roster? **Thresholds:** is the bar inside the range its quantity can actually take, after
every transformation applied to it?

### Lens C — shared definitions and the seams between modules

Any vocabulary read from more than one place. **Membership:** enumerate members, find every consumer,
look for one falling through. **Consolidation that hides a disagreement:** when two definitions
merged, did they genuinely mean the same thing, or does one caller now silently get the other's
reading? — the harder failure to see. **Aliases and survivors:** is the old name gone, or are there
two spellings that could drift? **Derived versus listed membership:** what happens to a value in
neither set, or to a new value nobody listed? **Schema seams:** does every field survive a round
trip, and can a reader tell "never asked" from "asked and empty"?

### Lens D — the verification apparatus, audited as code rather than as authority

The instruments that police the author's own mistakes. Everyone else treats their verdicts as
authority; this lens does not. **Can the check fail?** Construct the defect it exists to catch.
Text-scanning checks pass the moment the text is reworded. **Does green mean anything?** Empty
populations, filters excluding everything, swallowed exceptions, a value compared against itself, a
fixture whose premise no longer holds. **Non-vacuity guards:** is the guard itself reachable and
correct? **Self-certification:** can a harness report "caught" when the modified code merely failed
for an unrelated reason — did not parse, or crashed before reaching the thing under test? *"That
failure mode makes an instrument report strength it does not have, and it is the most valuable thing
you could find."* **Ratchets:** can a floor rise without a real improvement; can a guarantee be lost
while the number goes up? **Coverage claims:** enumerated from the real source, or a drifted list?

> Closing instruction: *"Assume the instruments are the least-audited code in the repository, because
> everything else was checked using them."*

### Lens E — absence, provenance, and what the prose promises

Every optional value on the decision path. **None versus zero:** `or 0`, `get(k, 0)`, truthiness
tests on a number, `sum()` skipping Nones, aggregations turning an absent input into a present
output — and the reverse, a measured zero reported as absent, which discards a finding. **The
companion:** does the basis describe THAT number or a neighbouring one; can the pair be made
inconsistent; when the number is absent what does the basis say? **Prose against behaviour:** find a
sentence promising more than the code delivers; can a person distinguish absent from zero on screen?
**Aggregation:** is a mean quietly computed over a different population? **Round trips:** does an
absence survive persistence, and does a record written before a field existed read back as absent?
