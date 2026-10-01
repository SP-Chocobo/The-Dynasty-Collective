# The strong claim, measured on the league actually being played

`run_roster_proof_ff.py`, 12 seats, complete. Same harness as `#205` — same `scoreable_pool`,
`run_one`, `score_roster`, `RULERS`, `COMPARE_ON` — with only the LEAGUE swapped for Fourth and
Forever's own: 29 roster slots, 26 draftable rounds, 12 teams, and its 30 observed scoring keys
(half-PPR, TE premium, receiving and rushing first downs, `pass_cmp`, `pass_int −2`).

```
ruler cdme    on total_value  : engine ahead 12 of 12   -377.93 vs -712.07   TAUTOLOGY
ruler points  on starter_value: engine ahead 10 of 12   2860.82 vs 2831.39   +1.04%   STRONG CLAIM
```

Every seat filled 10 of 10 starting slots with 0 unpriced rows, both arms.

**Pre-registered before the numbers were seen** (FREEZE_CHECKLIST, commit `62eee6d`): *engine
wins or ties `points` → the strong claim holds in the league actually being played.* It won.

## This reverses the committed fixture result, and that is the finding

| | league | rounds | seats | `points` wins | margin |
|---|---|---:|---:|---:|---:|
| `#205` committed | fixture, 6 formats | 14–15 | 68 | **1 of 68** | **−5% to −11%** |
| this run | Fourth and Forever | 26 | 12 | **10 of 12** | **+1.04%** |

Two runs of the same harness, opposite verdicts. So the deficit is **not a fixed property of the
engine**. Something about the environment decides its sign.

## It is almost certainly NOT the rulebook, which is what I expected to find

The rulebook was the reason this run existed (`evidence/rulebook_ground_truth/`: four real box
scores, +15.7% between the two scoring environments). But laying the runs side by side, F&F
differs from every fixture format on **three** axes at once, and the largest is not scoring:

| format | teams | SF | TE prem | **rounds** | points wins | margin |
|---|---:|:--:|:--:|---:|---:|---:|
| 12T_ppr | 12 | F | F | 14 | 0/12 | −11.21% |
| 12T_ppr_SF | 12 | **T** | F | 15 | 1/12 | −5.03% |
| 10T_ppr | 10 | F | F | 14 | 0/10 | −9.74% |
| 10T_ppr_SF | 10 | **T** | F | 15 | 0/10 | −11.13% |
| 12T_standard | 12 | F | F | 14 | 0/12 | −9.81% |
| 12T_ppr_TEP | 12 | F | **T** | 14 | 0/12 | −10.56% |
| **Fourth and Forever** | 12 | **T** | **T** | **26** | **10/12** | **+1.04%** |

**No fixture format runs more than 15 rounds; F&F runs 26.** That is the axis with the biggest
gap, and it has a mechanism that the rulebook does not: `points` scores `starter_value`, the best
legal lineup. The engine's whole deficit in a 14-round draft is that it spends early picks on
asset value instead of starters and then runs out of draft. At 26 rounds there is room to do
both, and the control — which chases starters first — has nothing left to gain after its lineup
is full while the engine keeps converting depth into startable upside.

**This is a hypothesis with a mechanism, not a measurement.** Superflex × TE-premium together
(untested in the fixture) and the rulebook itself remain live. The one-variable cut that
separates them is stated below.

Note the round count is exactly what `#242` repaired: 26 is `draftable_slots(roster_positions)`,
not `len(roster_positions)` = 29. Had that gone unfixed, this run would have drafted 29 rounds
of a 26-round league and the reversal would have been partly an artifact of my own harness.

## The margin has structure, and it points the same way

| seats | mean margin |
|---|---:|
| 1, 2, 3, 8, 9, 10, 11, 12 | **+1.59%** |
| 4, 5, 6, 7 (middle) | **−0.07%** |

Both losses (6, 7) and both near-ties (4, 5) are the middle seats; the eight outer seats all win
by ~1.1–1.8%. Middle seats in a snake have the most even pick spacing; the turn seats have the
most uneven. The engine's advantage concentrates where the gaps between turns are most uneven,
which is where deferring a pick costs or earns the most — consistent with the length story, and
worth its own cut later.

## What this does and does not license

**Does:** the strong claim holds in the league the owner actually plays. `#205`'s 1-of-68 can no
longer be stated unqualified as "the engine was tested against a fair control and did not pass";
it was tested twice and the results disagree.

**Does not:** it is ONE league and ONE format. `+1.04%` is also an order of magnitude smaller
than the `−5%` to `−11%` it contradicts, so "the engine wins" is much weaker than "the engine
loses" was. Nothing here says the engine is better; it says the sign of the difference depends on
the draft, and the fixture's 14-round drafts were not the owner's.

## THE LENGTH HYPOTHESIS IS REFUTED — the cut was run and my explanation was wrong

Everything above from "It is almost certainly NOT the rulebook" down was a hypothesis with a
mechanism, labelled as such. It has now been measured and **it is wrong.**

Same league, same 30 scoring keys, same pool, same seats, same harness, `--rounds 15`, with the
engine's own horizon set to 15 as well (see `#246` — the first attempt set only the pick order,
and returning identical numbers is how the omission was caught):

```
26 rounds :  points  10 of 12   2860.82 vs 2831.39   +1.04%
15 rounds :  points  10 of 12   2860.82 vs 2831.39   +1.04%      IDENTICAL, to the cent
```

`starter_value` scores the best legal lineup, and both arms settle their ten starters well
inside the first fifteen rounds. Rounds 16–26 add only bench, which that ruler does not read.
So draft length cannot be the explanation — and the comparison it enables is decisive:

| at **15 rounds** | points wins | margin |
|---|---:|---:|
| fixture, 12T_ppr_SF | 1 of 12 | **−5.03%** |
| **Fourth and Forever** | **10 of 12** | **+1.04%** |

**Same round count. Opposite verdict.** The reversal belongs to the LEAGUE, not the schedule:
the rulebook, the roster shape, or the superflex × TE-premium combination that no fixture format
carries. Those three are still crossed and still need separating.

(`cdme` does move with length — 12/12 at 26 rounds, 7/12 at 15 — because `total_value` sums
bench too, and a shorter draft has less bench to sum. That is the tautological ruler behaving
tautologically, and it is the control that shows `points` was genuinely unmoved rather than
accidentally unchanged.)

## The next one-variable cut

With length eliminated, three candidates remain crossed. Separate them by running the FIXTURE
league (12T_ppr_SF, 15 rounds) with F&F's 30 scoring keys substituted and nothing else changed.
That moves the rulebook alone.

  - advantage appears -> the RULEBOOK owns the reversal, and every fixture-measured result in
    the freeze record needs re-measuring on F&F's scoring.
  - advantage does not appear -> the roster shape or the superflex x TE-premium combination owns
    it, and the next cut is F&F's roster with the fixture's scoring.

Pre-registered, so neither outcome can be fitted afterwards.
