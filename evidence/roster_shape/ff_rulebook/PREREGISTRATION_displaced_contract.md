# PRE-REGISTERED before running: what does `displaced` actually equal?

Written and committed BEFORE the probe runs. The governing question, and nothing else:

> **What entity does production say it displaced, and is that exactly the entity its
> contract says it displaced?**

## The contract, quoted from the source

`lineup_optimizer.displacement_level` (lineup_optimizer.py:376-390):

> "Every starting slot is pre-filled with a phantom worth exactly `free_alternative` …
> Then a probe at `position` with an overwhelming value is added and the lineup re-solved:
> the probe is always assigned, and **the total rises by the probe's value MINUS the value
> of whoever it evicted** — a phantom (the slot was effectively open: displaced ==
> free_alternative) or one of my own starters (displaced > free_alternative). **Chains
> through multi-eligible players are handled by the solve itself** rather than by a rule."

Implementation (lineup_optimizer.py:468):
`displaced = base.total_value + PROBE_VALUE − with_probe.total_value`, then floored at
`min(alt_of[s] for s in reachable)`.

So the contract promises: **`displaced` is the value of the entity that is in the optimal
lineup BEFORE the probe and not in it AFTER.**

## The test

Solve `base` and `with_probe` independently, diff the two assignment sets, and identify by
id and value every entity that left. Compare against the returned `displaced`. Production
path only — `roster_points_lookup` → `_team_roster_points_players` → the live
`point_replacement` — captured by intercepting `displacement_adjustments`, nothing rebuilt.

States: **2, 5, 7 and 8 tight ends held.** Four reads, not a battery. The ladder is already
known; this is a semantic read, not an outcome experiment.

## The fork, fixed in advance

**A — `displaced` == the value of the entity that left.**
Contract satisfied. `displaced` = 200.90 is then CORRECT and means: my best tight end is the
only tight end in the lineup, holding the only slot tight ends can win, so any new tight end
must beat *him* to start. **B1' dies too.** The investigation moves to `replacement_levels`
and the 149.17 → 80.36 → 149.17 round trip.

**B — `displaced` ≠ the value of the entity that left.**
Real optimizer/displacement defect. Stop, characterize it, change nothing else.

**C — more than one entity leaves, or none does, or the diff is not well defined.**
The contract's "whoever it evicted" is ambiguous for cascades. **Resolve the contract before
touching any implementation.**

## What this probe will NOT do

- Not touch the flex-anchor candidate. It stays stranded until displacement and replacement
  semantics are settled.
- Not investigate `replacement_levels` yet. One thing at a time.
- Not run a battery. Four states.

## A correction carried in from the last write-up

I described the 149.17 return as "league demand thins, the rank walks up a thinning list."
**That is an interpretation, not an observation.** What is known is only that the production
replacement level landed on the same value at two states. Why it landed there is a separate
read and is not claimed here.
