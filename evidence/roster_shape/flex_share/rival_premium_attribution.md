# rival_premium stopped clearing one team-term's cap — attributed, and a probe artifact caught

`test_threshold_reachability.TheDenialNormalizerSaturatesAtItsOwnBoundTests
.test_the_premium_still_exceeds_one_terms_cap` is #144's NON-VACUITY canary. Its own docstring
says failing is the point: if `rival_premium` stops clearing `NEED_BONUS_MAX`, the old divisor
would be an upper bound again and #144's repair would be untestable. **It is now red.**

## The attribution, and the artifact that nearly wrote the wrong one

Four arms, same fixture, same 96 candidates, one process each:

| arm | max rival_premium | mean |
|---|---|---|
| measured share + displacement | **9.25** | 6.88 |
| measured share, displacement OFF | 16.21 | 9.10 |
| even split + displacement | **14.29** | 4.16 |
| even split, displacement OFF | 16.21 | 9.56 |

The even-split + displacement arm reproduces the pre-change commit (86efdce) exactly at 14.29,
which is what makes the table trustworthy. **Both terms contribute; the flex share is what
pushes the maximum under 12.**

**THE FIRST RUN OF THIS TABLE WAS WRONG AND SAID 9.25 FOR THE EVEN-SPLIT ARM TOO.** The cause:
`predraft_replacement_anchor` remembers its levels under `anchor_cache_key`, which names every
INPUT the levels depend on — so in production a board never depends on which boards came before
it. An ABLATION breaks that from outside: patching `fielded_flex_occupancy` changes the answer
without changing any input the key names, and the fixture's `setUpClass` builds a board BEFORE
the patch goes on. Every "even split" board then read the measured arm's cached levels. Five
points of a five-point finding were one board built in the wrong order.

Two things came out of that: the patch now goes on before any board is built, and
`draft_room.reset_anchor_caches()` exists so every arm boundary in
`run_216_flexshare_draft_probe` drops both caches. An ablation that has to be right about which
half caused what cannot afford to skip this.

## CORRECTION -- my first reading of the cause was wrong

I first wrote that `pick_synthesis.TEAM_SPECIFIC_CAPS` had silently stopped enumerating the terms
it names, and filed it as an unhandled missing-companion defect. **Withdrawn.** Fable handled it
explicitly, in a note attached to the tuple: #216's fourth term is deliberately excluded because
`displacement_adj` is non-positive by construction and cannot raise the sum the caps bound, so
`sum(TEAM_SPECIFIC_CAPS)` remains the correct UPPER bound; the LOWER bound is now open, and both
consumers already guard one-sidedly. I read one stale half-sentence three paragraphs above that
note and diagnosed from it.

## What actually remains

`rival_premium` is `rival team_acquisition_value - rival universal_value`, the sum of the
team-specific terms on a rival's board. #216's fix added a fourth, `displacement_adj`, uncapped
and never positive -- so the sum's LOWER end moved while its upper bound did not, which is
precisely what that note records. `TEAM_SPECIFIC_CAPS` names the three CAPPED terms, correctly
and on purpose, and `NECESSITY_DENIAL_SATURATION` is still a sound upper bound.

The only prose defect was one half-sentence of #144's older comment still claiming the terms were
"each independently capped". It is repaired in place, with the correction beside it rather than
three paragraphs below.

## What I am NOT doing

Editing the canary so it passes. Its threshold is not arbitrary and its message is correct:
on this fixture, #144's repair is currently dormant. Whether the right answer is to widen the
fixture to states where the ramp is actually stressed, to re-derive the saturation point over
four terms, or to accept the repair as dormant, is a decision about #144's constant — and
choosing it AFTER seeing which choice makes my own change look better is exactly the move #56
exists to forbid. It is recorded here, red, for the owner.
