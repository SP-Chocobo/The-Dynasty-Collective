# PRE-REGISTRATION — does the tight-end deduction PREDICT which seats hoard?

Written and committed **before the probe exists and before any result is read.**

## The question

`RESIDUAL1` established that the balanced arm's tight-end excess is bimodal: four seats finish
with 9–15, five finish with 1–2. The surviving hypothesis is positive feedback through

```
displacement_adj[TE] = level[TE] − displaced[TE]        displaced = this seat's own best TE
```

A seat whose best tight end is weak faces a *smaller* deduction, so tight ends stay cheap for
it, so it takes more, so its best tight end stays weak. A spiral.

**The timing proxy for this already died (r = +0.101).** This is the direct test.

## The trap this must avoid, stated first

A seat that has finished with 14 tight ends will of course show a different tight-end
deduction than one that finished with 1. **That is downstream of the outcome and proves
nothing.** The hypothesis is causal, so the predictor must be measured **before the seats have
diverged**, and whether they have already diverged at the measurement point is itself measured
and reported, not assumed.

## Population and measurement

- **Draft:** the balanced ablation arm (`ff_draft_balanced.json`), because that is where the
  divergence lives and the mode boundary cannot contribute.
- **Checkpoints:** the board each seat faces when on the clock for its **5th, 7th and 9th**
  own pick — early, and reported alongside how many tight ends that seat already holds there.
- **Measured quantity:** `displacement_adjustments`' own returned `{"adjustment", "displaced",
  "basis"}` for TE, captured by wrapping the production function. Not reconstructed, not
  inverted from the board row. The level it consumed is captured from the same call.
- **Fixture:** production-shaped picks (`pick_no`, `round`, `roster_id`, `player_id`) and
  `mode="balanced"`, matching the arm. A schema assertion runs before the first board.
- **Groups, fixed now from the already-published RESIDUAL1 counts:**
  - HOARDERS (final TE ≥ 9): seats **2, 5, 9, 12**
  - STARVERS (final TE ≤ 2): seats **1, 3, 8, 10, 11**
  - middle (3–7): seats 4, 6, 7 — reported, not used to decide the fork

## The forks, fixed before reading

**FORK A — SUPPORTED.** At the early checkpoints, hoarder seats show a systematically smaller
(less negative) TE `adjustment` and/or a lower `displaced` than starver seats, **and** the seats
have not yet materially diverged in tight ends held. The feedback hypothesis survives and earns
a mechanism write-up.

**FORK B — DEAD.** No systematic separation between the groups at the early checkpoints, or the
separation appears only after the seats have already diverged in TEs held. The hypothesis is a
consequence, not a cause, and is withdrawn like the timing proxy.

**FORK C — INVERTED.** The separation exists and runs the other way (hoarders face a *larger*
deduction and hoard anyway). The hypothesis is dead in its stated form and the finding is that
the deduction is not what governs the choice at all.

## What would make any of this an artifact

- **The groups were defined by the outcome.** With n = 4 and n = 5 seats in one draft, a
  separation could be noise. Report the per-seat values, not just group means, so a reader can
  see the overlap.
- **`displaced` is only meaningful where the term is non-zero.** A seat with an open TE-reachable
  slot gets `adjustment == 0.0` by construction. Those states must be counted and reported
  separately, never averaged in as if they were measurements of the same thing.
- **One draft, twelve seats.** Whatever this shows is a shape, not an estimate.

## What this does NOT do

No engine change. No tuning. It does not test whether the deduction is *correct* — the
cancellation result already settled that the level's basis does not reach the price where the
term is non-zero — only whether the deduction **discriminates** the seats that hoard.
