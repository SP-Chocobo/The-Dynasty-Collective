# The mode transition is not derived from anything — and no existing observable IS it

The question, as the owner framed it and deliberately NOT as "what should 15 be":

> *"Is the transition from roster-aware valuation to roster-blind upside valuation derived from
> draft state, or is the fixed round-15 threshold an unjustified global constant?"*

And the prior step before any replacement rule: **establish whether an invariant or observable
state corresponding to the intended transition already exists.** If none does, that is a design
gap, not a bad constant.

Measured with five candidates, every one of them an existing production quantity. No new
quantity invented, nothing tuned. `phase5_is_the_transition_derivable.py`.

---

## The five candidates and where each one lands

`UPSIDE_MODE_DEFAULT_ROUND = 15` → upside begins at overall pick 169 of 312, **46% of the draft**.

| | candidate observable | production source | lands at | vs the constant |
|---|---|---|---|---|
| **A** | league-wide remaining starter demand reaches zero | `remaining_starter_demand` | **round 23** (pick 276) | **+8 rounds** |
| **B** | a seat's DEDICATED starting slots are full | `_team_starters_filled` + `dedicated_slot_counts` | **round 7** (all 12 seats) | **−8 rounds** |
| **B2** | a seat can field a COMPLETE legal lineup | `lineup_optimizer.optimize_lineup` | **rounds 10–11** | **−4 rounds** |
| **D** | every position has left `replacement_levels`' domain | `replacement_ranks` → None | **~round 17–20** (TE pick 192, RB pick 204) | +2 to +5 |
| | the shipped behaviour | `UPSIDE_MODE_DEFAULT_ROUND` | round 15 | — |

**The five span rounds 7 to 23 — a 16-round spread — and not one of them equals 15.**

At the boundary itself the state is unambiguous and nobody's definition of "late":

```
after 168 picks:  total starter demand = 7.75   QB 0.00  RB 2.25  WR 0.05  TE 5.45
                  positions still inside replacement_levels' domain: ['RB', 'TE']
```

The engine stops being roster-aware while **7.75 starting slots are still unfilled across the
league** and two positions still carry live starter demand.

## The finding

**Round 15 is not an approximation of a defined concept. It is a stand-in for an undefined one.**

Both halves matter and they are separate:

1. **It is not derived.** Nothing in the architecture computes 15, and no observable the
   architecture does compute agrees with it. Under #56 that makes it an invented constant
   sitting on a behavioural switch — not a bound, a threshold, and the strongest form of what
   #56 forbids, because it does not merely scale a term, it selects a different valuation for
   46% of the draft.

2. **And the derivation is NOT sitting there waiting to be wired.** The five candidates
   disagree by sixteen rounds because they answer five different questions. "The league has no
   unfilled starting slots" (A), "I can field a lineup" (B2) and "no position has demand left"
   (D) are not approximations of each other. The system has never said which one it means by
   *"late enough to stop caring about my roster."*

That is a **design gap**: the concept the constant stands for has no definition anywhere in the
engine, so there is nothing to derive it from.

## The trap this closes

The tempting next move is "derive it from lineup completion and the numbers improve." Measured,
that inference is backwards:

- **B2 (complete lineup, rounds 10–11) is EARLIER than 15.** Wiring it makes the engine go
  roster-blind *sooner* — more upside picks, and on the ablation's own evidence, **more** tight
  ends, not fewer.
- **A (demand exhausted, round 23) is LATER than 15**, and would cut the roster-blind window
  from 144 picks to 36.

So the choice of observable decides the direction of the effect. Any selection made while the
concept is undefined would be selection on the outcome — fitting the transition to this
league's tight-end share, which is the same failure mode as tuning the integer, wearing a
derivation as a disguise.

**Which is why this stops here.** Defining what the transition means is a modelling decision and
it is the owner's. Two candidate readings, stated so they can be chosen between rather than
blended:

- **"Roster-blind once the roster is SAFE"** — the transition is about *this seat*: it can field
  a legal lineup, so further picks are depth and lottery tickets. Observable exists (B2), fires
  rounds 10–11 here, and is per-seat rather than global — which the current constant is not.
- **"Roster-blind once the LEAGUE has no starter demand left"** — the transition is about the
  market: nobody is competing for starters any more, so relative scarcity has stopped meaning
  anything. Observable exists (A), fires round 23 here.

They are different claims about what upside mode is *for*, and the engine currently makes
neither.

## What is NOT claimed

- Not that round 15 is "wrong" in outcome. The ablation showed forcing balanced everywhere is
  worse on WR allocation and worse on monocultures.
- Not that any of the five candidates should be wired. None is authorised and none is
  recommended on the numbers.
- Not that this explains the residual. It does not — 29.2% TE survived the ablation and remains
  unattributed.
