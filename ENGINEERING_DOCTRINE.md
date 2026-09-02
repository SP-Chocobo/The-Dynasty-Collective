# Engineering Doctrine — semantic integrity

Standing doctrine for this repository. It governs how audits are conducted and how changes are
justified. It was written after an audit that found a class of defect the previous audit could
not have found, and it exists so that class is looked for deliberately rather than stumbled into.

---

## The central principle

> **A variable's definition is not airtight merely because the definition is self-contained. Its
> meaning can be poisoned at the boundary where another component changes the conditions under
> which that definition is consumed.**

And the stronger lesson the audit actually demonstrated:

> **The most dangerous defects may be neither bad formulas nor bad local assumptions. They can be
> correct formulas operating on correctly typed, correctly shaped data whose semantic meaning has
> silently changed upstream.**

Self-contained definitions and locally correct formulas are **not** protection against semantic
drift. A quantity can stay numerically valid, keep its type and shape, and pass every test it
owns, while becoming semantically invalid because an upstream quantity, state, domain, or
assumption changed underneath it.

---

## The proof case: K/DST

The K/DST investigation is the discovery mechanism for this class, and it is recorded here
because *how* it was found matters as much as *what* was found.

The symptom was mundane and easy to dismiss: kickers and defenses were being drafted earlier
than a human would take them. It looked like a tuning complaint. Following it instead of
explaining it away forced the investigation to cross variable boundaries, and every real defect
found afterwards was of the same class:

| what was found | what was locally correct about it |
|---|---|
| Remaining demand computed league-wide instead of per team | The subtraction was arithmetically right; `max(·,0)` simply does not distribute over a sum |
| `replacement_levels`' "dynamic" anchor is algebraically inert | Both halves of the cancellation were correct; the docstring described a mechanism that never moved the number |
| The `>= 1` rank clamp | A clamp is a legitimate guard — against a rank of 0, not against a demand of 0 |
| `positional_bench_appetite` returning `0.0` for every position | The mean-rate fallback was correct per position and undefined for the empty case |
| Observed share as a model of remaining demand | The shares are conserved exactly; a share is simply not a stock |
| `_scale_vor_to_bpa` returning `0.0` for absent VOR | Clipping a negative to zero is defensible; clipping an *absence* to zero is not |
| `replacement_levels` OMITTING a position once its league-wide starter demand is exhausted, composed with `_board_order` sorting unpriced rows last | **Nothing is wrong with either half.** Declining to invent a level the demand model cannot support is correct and is the documented domain. Refusing to substitute `0.0` for an absent score is correct and is the documented intent. Composed, they assert *"every kicker is better than every running back"* |

The last row is the limit case of everything above it, and it was found much later, by a
different route. Each of the first six has *something* locally imperfect — a clamp guarding the
wrong thing, a fallback undefined at its edge, a share standing in for a stock. **The last has
none.** Both components are correct, both are correctly documented, both decline for good
reasons, and the defect exists only in the composition. Measured on a 12-team 1QB board at
round 15: K and DEF 100% priced (37/37 and 32/32), QB/RB/TE/WR 100% unpriced (0 of
15/36/24/9), and the candidate list opening with four defenses and a kicker ahead of every
remaining skill player. Kickers and defenses are drafted last, so they are the last positions
still holding starter demand — which makes the inversion **structural, not incidental.**

Two things that row teaches beyond the six above it:

**Refusing to answer is not neutral. It is an answer, and it propagates.** A layer that
declines hands its consumer a decision, and the consumer's handling of that decline makes a
claim about the declined population. Nobody ever asked what "sort unpriced last" asserts when
everything still priced is a kicker.

**The absence was not a sentinel.** `replacement_levels` did not return `None`; it omitted the
dictionary key. A rule written about "functions returning `None`" walks straight past this. The
class is *any way a layer can decline* — a `None`, a `NaN`, a missing key, an empty list, a
dropped row, or (at the provider boundary) a `⚠️`-prefixed string.

**Not one of these is a bad formula.** Every one is a correct operation on correctly typed,
correctly shaped data whose meaning had changed somewhere upstream. Every one passed its own
tests. Several were *documented as intended behaviour* in the very docstrings that defined them.

**The previous audit did not surface any of them.** That audit verified components. These defects
do not live in components — they live at the boundaries between them, in the conditions under
which a component's output is consumed. Component-level correctness does not establish
system-level semantic integrity, and this repository now treats that as demonstrated rather than
arguable.

---

## The second principle: player properties and decision context must remain distinct

> **Player properties and decision context must remain distinct.**

A **player-level quantity** describes something about the player's modeled profile — projected
production over a defined horizon, age, injury status as a fact about him. A **contextual
quantity** describes the state in which that player is being evaluated: roster need, positional
scarcity, draft state, waiting cost, eligibility, risk/status as it bears on *this* acquisition,
league format, acquisition timing.

Context may change the decision value of acquiring a player **without changing the player's
underlying player-level signal.** Therefore:

> *"What is this player?"* and *"What is this player worth to this team at this moment?"* are
> separate questions, and a single number cannot answer both.

**Every derived quantity declares its category:**

| category | describes | changes when |
|---|---|---|
| **player property** | the player's modeled profile | the projection, the player, or the horizon definition changes |
| **league / format property** | the rules of this league | the league settings change |
| **current-state / context variable** | the situation this evaluation happens in | picks are made, rosters fill, the pool drains |
| **decision output** | what to do, here, now | any of the above changes |

**Crossing those categories requires an explicit reconciliation step** — a named quantity, with
its own contract, that states what was combined and under which rule. A contextual signal must
not become a player property merely because it is convenient to attach it to a player record.

**Scope is part of meaning. A quantity does not become a player property merely because it is
stored on a player's row.** A row is a join, not a claim about ownership: the same row can carry
a projection (player property), a replacement level (league property), a scarcity term (context)
and a recommendation (decision output), and each keeps its own category and its own lifetime.

Applied to this engine's own split: **BPA answers what the player's underlying production/value
signal is. The selection layer answers what that player is worth acquiring here, now, under the
current context.** The moment BPA carries scarcity, waiting cost, or roster fit, it has stopped
answering its own question and no consumer can tell which question it answered.

---

## Required audit chain

Every audit, and every implementation that touches a load-bearing quantity, must walk the full
chain. Stopping at the first link is what the previous audit did.

```
definition → domain of validity → state transitions → upstream assumptions
           → downstream consumers → interaction with other quantities
```

1. **Definition** — what does this quantity claim to mean, in words, in its own units?
2. **Domain of validity** — under what conditions is that claim true? What makes it false?
3. **State transitions** — what happens at the edges of that domain, and is the transition
   continuous, discontinuous, or silent?
4. **Upstream assumptions** — what must be true of its inputs for the claim to hold, and who
   can change that without touching this code?
5. **Downstream consumers** — who reads it, what do they assume it means, and does any of them
   apply an operation that does not preserve that meaning?
6. **Interaction with other quantities** — can another variable change how this one is
   interpreted, without either variable changing?

Link 6 is the one that finds this defect class. Links 1–3 are what a careful author already does.

---

## Required contracts

A load-bearing quantity is not accepted into the engine without written answers to all seven.
"Load-bearing" means: it influences a decision, a ranking, a displayed claim, or another
quantity that does.

1. **What the variable means** — one sentence, in its own units, that a reader could check.
2. **The domain in which that meaning is valid** — stated as a condition, not as prose.
3. **How exhaustion is represented** — what the quantity does when its domain is used up, and
   why that representation is not confusable with a normal value.
4. **How absence / unknown is represented** — and the explicit statement that this is *not* the
   same as zero, one, or the nearest legal value.
5. **Which consumers are authorized to use it** — by name. A consumer not on the list reading it
   is a defect, not a convenience.
6. **Whether downstream operations preserve its semantics** — checked per consumer, including
   sorts, clips, defaults, rescales, and string formatting.
7. **Whether another variable can silently change its interpretation** — named, or explicitly
   asserted to be none.
8. **Which category it belongs to** — player property, league/format property, current-state /
   context variable, or decision output — and, where it combines categories, the named
   reconciliation step that licenses the combination.

---

## Standing rules

These follow from the principle and are not negotiable per change.

- **Absence is not a value.** Never substitute `0`, `1`, an empty collection, or the nearest
  legal value for a quantity that is unknown. If execution cannot continue without one, the
  correct outcome is to decline, not to invent.
- **A clamp is a claim.** `max(x, 1)`, `clip(lower=0)`, `.get(key, default)` and
  `na_position='last'` each assert something about the domain. Every one must be justified
  against the domain, in a comment, or removed.
- **A default in a consumer is a contract change.** `.get(key, default)` converts a producer's
  absence into a consumer's number, and it does so where the producer cannot see it. These are
  the hardest sites to find and the most likely to be silently wrong.
- **Rank is a laundered comparison.** An ordinal is a value comparison already collapsed into an
  integer. Any rule that forbids comparing two quantities also forbids ranking them together.
- **Fused quantities inherit the worst property of each part.** A number combining an exact
  observable with an inferred estimate is neither exact nor honest about its uncertainty. Keep
  epistemic types separate and named.
- **Different horizons are different quantities.** Two numbers that bear on the same decision are
  not the same number. Availability windows that differ are proof they are not.
- **A test that cannot fail proves nothing.** Assert on behaviour that changes when the code is
  wrong, and prefer a mutation to a re-derivation.
- **A row is a join, not an ownership claim.** Storing a contextual quantity on a player's row
  does not make it a property of that player. Scope travels with meaning, not with storage.
- **A docstring can encode a defect.** Several of the findings above were described as correct in
  the docstrings that defined them. Documentation is evidence of intent, never of correctness.
- **A measurement that cannot fail proves nothing either.** The rule above is written about
  tests; it applies unchanged to instruments. Three measurements in the pre-draft-anchor work
  were discarded as vacuous: a sweep where half the scenarios never reached the code under
  test, a probe whose "control" recomputed full demand against a depleted pool, and a battery
  that — once the repair landed — contained the fix in *both* of its arms. **An instrument that
  shares code with its subject has stopped being an instrument.** Every harness needs a control
  arm asserted to actually differ before its numbers are believed.
- **A finished item names the commit that finished it.** A register entry marked done whose
  supporting evidence cannot be located is indistinguishable from one that was never done —
  the audit trail stops being deterministic, and six weeks later the work is re-litigated from
  memory. The chain is *hypothesis → instrument → independent control → observed result →
  decision → durable evidence*, and the last link is a SHA in the record, written at the time
  of the decision rather than reconstructed after it. (Deliberately a convention and not yet a
  test: across all three documents only two sections currently claim completion, so a test
  would pass on a population of two and prove nothing. It becomes worth enforcing once the
  convention has a population — which is itself an application of the rule above.)
- **A retracted justification obliges a re-decision, not an annotation.** When the reason for a
  choice stops being true, the choice must be re-made — writing "the reason for this no longer
  applies" beside it and leaving it standing is worse than saying nothing, because the note makes
  it look handled. Traced across three commits: `d30f50d` made the debate personas
  provider-agnostic *in mechanism* and left a per-role vendor default; `a58a295` responded to the
  defaults being questioned by displaying their rationale **more prominently**; `d871078` gave
  Claude live web search, which destroyed the `beat → gemini` justification, **noticed**, and
  rewrote the shipped string to read *"live search isn't a reason to prefer one provider over
  another for this role anymore"* — while leaving `"recommended": "gemini"` untouched. The app
  then told every user the reason no longer applied while continuing to act on it, for months.
  Each correction landed on the *explanation* instead of on the *value*. The test is mechanical:
  if a `why` can be deleted without changing behaviour, the behaviour was never resting on it.

---

## When a symptom looks like a tuning complaint

The K/DST symptom was, on its face, a request to move a number. It was not. This doctrine
requires that a behavioural complaint be traced to an owning layer before any coefficient is
touched — and that "the output looks wrong" be treated as a claim about *meaning* until the
trace proves it is a claim about *magnitude*.

Tuning a coefficient to remove a symptom whose cause is semantic does not fix the defect. It
hides the evidence that would have found it.

---

## The re-audit cadence

Everything above is a standing rule, and §19.9 found the obvious thing about standing rules:
**nothing ran them.** No schedule, no trigger condition, no re-audit — the checks executed only
when a human happened to push. A doctrine that is enforced by remembering is enforced by nobody.

**The cadence: weekly, Wednesdays, 13:00 UTC.** Chosen against the season rather than the
calendar. The regular-season week of play concludes Monday night, so Wednesday is the first day
the world's numbers have settled — injury designations resolved, waivers run, depth charts
updated. A run that lands mid-week measures a stable week; one that lands Sunday measures a week
in motion.

**What the run does** is the full suite plus `baseline_manifest.py --check` plus
`assertion_floors.py --check` — the same three things CI already does on a pull request, on a
clock rather than on a person. That is deliberately not a new instrument: the point of a cadence
is that the checks you already trust keep running when nobody is looking, not that a scheduled
run gets its own weaker or stronger standard.

**Where it is configured:** `.github/workflows/tests.yml`, the `schedule:` trigger.
`test_audit_cadence.py` holds this paragraph and that cron to each other, because a documented
cadence and a configured one that disagree is worse than either alone — the document is the one
that gets believed, and it is the one that cannot run anything.
