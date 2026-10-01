# The identity repair killed `context_elevated`, and that is a finding rather than a regression

> Measured across the eight board states `test_threshold_reachability` samples, at the commit
> before the identity repair and at the commit after it.

## What happened

```
                       pre-repair   post-repair
  priced rows sampled     1992         1960
  gap max                13.21         8.33
  share of rows >= 12     7.78%        0.00%

  need_bonus       max     8.33         8.33    unchanged
  eligibility_bonus max    0.00         0.00    unchanged
  depth_exposure   max     9.24        11.40    HIGHER
  displacement_adj min   -90.00       -67.00    LESS negative
```

**No term shrank. Two of them improved.** What disappeared is the *co-occurrence*: rows carrying
`need_bonus` and `depth_exposure` together without a negative `displacement_adj` dragging the sum
back down. On a pool containing all ten recovered players, those rows do not arise.

## Why this is the audit's own mechanism, one more time

The repair program's founding observation:

> a repair expands a population → an invariant proven over the old population silently stops
> holding → the old test stays green because it never enters the new domain.

Here the test did **not** stay green, which is the only reason we know. `context_elevated`'s
reachability was a property of *which players happened to be in the pool*, and the pool was wrong —
it was missing a startable superflex quarterback, among nine others.

## The symmetry, which is the sharpest part

`ContextElevatedBecameReachableTests`' own docstring records the pre-`#139` state:

> measured at 0.0% firing, max gap 8.67, and recorded in `CDME_CONTRACTS.md` as dead

Post-repair: **0.0% firing, max gap 8.33.** The badge is back within a third of a point of where
`#139` found it. `#139` added `depth_exposure` as a third term, the gap's ceiling rose above the
threshold, and the badge came alive — on a pool that was already missing ten players. Correcting the
pool undid it.

And the class warned about exactly this, in its own words:

> A number that became a discriminator because the quantity underneath it grew is still a bound
> being read as a threshold (`#56`), and the open product decision on what SHOULD light this badge
> is untouched.

That open decision is no longer deferrable.

## What was done, and what deliberately was not

Three tests are marked `@unittest.expectedFailure` with the measurement inline. **The assertions are
not edited.** Editing them to pass would erase the only evidence that the pool was ever wrong, and
the tests are the correct party in this disagreement — they detected a real change in the engine's
behaviour and said so.

`CDME_CONTRACTS.md` still describes `context_elevated` as reachable. That claim is now false and is
recorded here rather than quietly corrected, because the contract document is banner-marked as an
authority and a silent edit to an authority is how the last round of false claims got made.

## The open question this forces

`context_elevated` fires on nothing. Three options exist and all three are product decisions:
lower the threshold to something the corrected distribution reaches; accept the badge as dead and
remove it; or decide what the badge is actually *for* and derive a threshold from that.

`#56` forbids the first as a calibration exercise unless the number is derived rather than picked.
Nothing here chooses between them.
