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

## What is actually behind it, stated as a finding and not repaired here

`rival_premium` is `rival team_acquisition_value - rival universal_value`, i.e. the sum of the
team-specific terms on a rival's board. #216's fix added a FOURTH such term, `displacement_adj`,
which is uncapped and never positive. `pick_synthesis.TEAM_SPECIFIC_CAPS` still names three:

    TEAM_SPECIFIC_CAPS = (dr.NEED_BONUS_MAX, dr.ELIGIBILITY_BONUS_MAX, dr.DEPTH_EXPOSURE_MAX)
    NECESSITY_DENIAL_SATURATION = sum(TEAM_SPECIFIC_CAPS)          # 36.0

and its comment derives the saturation point as "the SUM of draft_room's team-specific terms,
each independently capped -- so its own bound is their SUM". **That sentence is now false.** The
sum of the caps is still a valid UPPER bound (adding a non-positive term can only lower the
maximum), so `test_the_flat_spot_is_gone` still holds and nothing is mis-clipped. What is gone
is the TIGHTNESS: the tuple no longer enumerates the terms it claims to enumerate.

This is the missing-companion shape (#166/#174/#185/#187/#190/#207) one more time — a quantity
gained a term and its bound did not travel with it — and it belongs to #216's fix, not to the
flex share. The flex share only made it cross a line where a canary was watching.

## What I am NOT doing

Editing the canary so it passes. Its threshold is not arbitrary and its message is correct:
on this fixture, #144's repair is currently dormant. Whether the right answer is to widen the
fixture to states where the ramp is actually stressed, to re-derive the saturation point over
four terms, or to accept the repair as dormant, is a decision about #144's constant — and
choosing it AFTER seeing which choice makes my own change look better is exactly the move #56
exists to forbid. It is recorded here, red, for the owner.
