# D7 verified on real drafts: the IDP over-accumulation stops happening

`flex_reachable_ceiling_groups` was chosen on the battery's STORED rosters — a static sweep over
948 seat × group observations. That proves the arithmetic separates the populations. It does not
prove the guard changes drafting, because a sort key only matters if it reaches a pick. This is the
dynamic half.

## Arms chosen, and why these

D7's bound can only bind where a FLEX-type slot lets a group saturate, so the run is scoped to every
arm where that is possible plus the hardest false-positive cases:

| arm | rounds | flex slots | dedicated IDP | why |
|---|---|---|---|---|
| `LIGHT_IDP` | 14 | FLEX, IDP_FLEX | 0 | **the exact case 3.2 names** — reach 1, ceiling 4 |
| `CAPTURE_owner_league` (+`_balanced_full`) | 25 | FLEX, SUPER_FLEX, IDP_FLEX | 0 | the owner's real league |
| `CAPTURE_fourth_and_forever` (+`_balanced_full`) | 26 | FLEX, SUPER_FLEX | 0 | deepest offence in the population — the hardest false positive |
| `HEAVY_IDP` (+`_balanced_full`) | 18 | FLEX | 6 | control: the already-certified DEDICATED bound |

## LIGHT_IDP — the over-accumulation is gone, and capped exactly at the bound

IDP held per seat, and the reason this is attributable to D7 specifically: the cap lands on **4**,
which is `reach 1 × FLEX_GROUP_DEPTH_FACTOR 3.0 + 1`, and nothing else in the engine produces that
number.

| seat | before | after | | seat | before | after |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | | 7 | 1 | 4 |
| 2 | **6** | 1 | | 8 | 1 | 4 |
| 3 | **6** | 1 | | 9 | 3 | 3 |
| 4 | **7** | 4 | | 10 | 1 | 4 |
| 5 | **7** | 3 | | 11 | **7** | 4 |
| 6 | 1 | 4 | | 12 | **7** | 4 |

**No seat exceeds 4.** Six seats were over the bound before and none is now. Total IDP drafted fell
48 → 37. The seats that ROSE did so because the hoarders stopped taking them and the bodies were
still on the board — redistribution, and every one of them lands at the ceiling rather than past it.
`unfieldable_depth` reports **0 findings** for this arm, against six rosters over the bound before.

## The whole run

**7 arms, 1824 picks, `complete: true`, every arm produced at commit `7070339`** — one code version,
so no figure here is an average over mixed code.

| arm | picks | findings |
|---|---|---|
| `LIGHT_IDP` | 168 | **0** (was six seats over the bound) |
| `CAPTURE_owner_league` | 300 | **0** |
| `CAPTURE_fourth_and_forever` | 312 | **0** |
| `CAPTURE_owner_league_balanced_full` | 300 | **0** |
| `CAPTURE_fourth_and_forever_balanced_full` | 312 | **0** |
| `HEAVY_IDP` | 216 | 1 — dedicated bound, roster 12, held 8 vs ceiling 7 |
| `HEAVY_IDP_balanced_full` | 216 | 1 — dedicated bound, roster 5, held 9 vs ceiling 7 |

**Zero false positives on the four deepest arms in the population.** `fourth_and_forever` is 26
rounds and 312 picks, and is the arm every additive allowance flagged.

## HEAVY_IDP — the control, and both findings are the known survivors

`unfieldable_depth` reports **1** finding per arm, on the group {DL, LB, DB} against a ceiling of 7
(6 startable + 1 bye). That is the DEDICATED bound, already certified, and 1 per arm is exactly the
post-repair state 3.2 recorded when its repair took those arms from 10 and 11 findings to 1 each.

D7's new bound does not fire on this arm at all, which was checked directly rather than assumed: the
offence group sits at held 8 against a ceiling of 19 on every seat.

## THE COMPARISON IS NOT SINGLE-VARIABLE, AND THAT IS STATED RATHER THAN BURIED

The "before" column comes from the battery at `6ea4f5b`, which predates A1, A2 and A3. So the deltas
above carry D4 (the growth conversion), D5 (the upside tie-break), D8 (the proportional health
discount) AND D7 together. The engine-measurement discipline is explicit that comparing a fresh run
against a baseline from different code is how a repair gets credited with someone else's improvement.

What survives that caveat, and why the LIGHT_IDP result still counts as D7's:

* the cap is at **exactly 4**, D7's ceiling for that league, a number no other change computes;
* the static sweep predicts precisely this bound on precisely these rosters;
* none of D4, D5 or D8 touches `unfieldable_last` or roster-count arithmetic at all.

The `HEAVY_IDP` 9 → 8 shift is NOT attributed to D7. It is a combined effect, and no claim is made
about which change produced it.
