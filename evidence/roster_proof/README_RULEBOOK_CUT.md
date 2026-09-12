# #248: it is not the rulebook. ~~It is ONE FLEX SLOT.~~

> ⛔ **THE FLEX READING IS WITHDRAWN (27th), 2026-09-12.** The closing section below named the cut
> that would settle it — "the fixture roster with a third FLEX added and nothing else changed."
> That cut was run in BOTH directions and the reading did not survive it: adding a flex to the
> fixture moved the engine−control margin from −6.99 to **−22.53**, and removing one from F&F
> moved it from +29.43 to **+22.08**. Both cuts hurt. A slot with no consistent sign is not the
> thing separating the two leagues.
>
> **What is withdrawn is exactly one paragraph: the mechanism reading.** Arms A, B and C below
> are measurements and they REPRODUCE — A and C were re-run and came back with zero differing
> values across 12 seats × every metric. The rulebook result stands. So does the dating of #205.
>
> Nothing below is edited. See `README_FLEX_CUT.md` for the four arms, and for the one structural
> difference still standing: at 15 rounds the fixture roster has ZERO spare draftable slots and
> F&F has ELEVEN — which this document dismissed as unable to enter, and which
> `draftable_slots_per_team` feeds straight into `remaining_league_picks`.


Three arms, one process, one code version, matched at 15 rounds — the only honest A/B this
repository allows. `run_roster_proof_rulebook_cut.py`, pre-registered at `1c6611c` before any
number existed.

```
A  fixture roster + fixture scoring    points  4 of 12   -0.28%
B  fixture roster + F&F scoring        points  4 of 12   -0.61%     <- THE CUT
C  F&F roster     + F&F scoring        points 10 of 12   +1.04%
```

> ⛔ **ARM B IS NOT IN THE CELL IT IS LABELLED WITH. CORRECTED 2026-09-12, before any follow-up
> run was read.** Arm B was built as `build_mock_league(scoring="ppr", te_premium=False,
> base_scoring=<F&F's 30 observed keys>)`. `build_mock_league` OVERWRITES `rec` from its own
> `scoring` argument — that is its documented job — so **arm B ran at `rec = 1.0`, not F&F's
> 0.5**. And `te_premium=False` does not REMOVE a `bonus_rec_te` already present in
> `base_scoring`, so the arm carried a TE premium it was told not to have. Measured from the
> committed arm: `rec 1.0, bonus_rec_te 0.25, rec_fd 0.5, pass_cmp 0.1`, resolving to
> `hint = {"scoring": "ppr", "te_premium": True}` — **a format that exists in neither league.**
>
> This is not a mislabel only. `rec` does not reach offensive valuation through
> `scoring_settings`; it reaches it by FILE SELECTION, because `set_league_format` picks a
> different rankings export per hint. Arm B's hint says `ppr` and arm C's says `half_ppr`, so
> **the two arms drew from different exports.**
>
> **What arm B actually establishes:** first downs + completion bonus + TE premium, at PPR
> reception value and on the PPR export, change the verdict by nothing. That is a real result
> about PART of the rulebook. It is not a result about the rulebook, and the line below
> overstates it. The fixture-roster-with-true-F&F-scoring cell was never occupied at either
> flex count; `run_roster_proof_missing_cell.py` runs both.

**C reproduces `#245` to the cent** (10/12, +1.04%), which is what licenses reading A and B at
all. The control validated the harness before the cut was interpreted.

## The pre-registered answer: the roster shape, not the rulebook

- **A → B moves the rulebook alone.** Half-PPR, TE premium, first downs, completion bonus — the
  environment `evidence/rulebook_ground_truth/` measured as paying four real starters **15.7%
  differently**, confirmed to the cent against the live app. Effect on the verdict: **none.**
  4 of 12 either way.
- **B → C moves the roster shape alone.** The verdict flips: 4 of 12 → 10 of 12, −0.61% → +1.04%.

## And the roster shapes differ by exactly one slot

```
fixture 12T_ppr_SF   QB 1  RB 2  WR 2  TE 1  SUPER_FLEX 1  FLEX 2   =  9 startable
Fourth and Forever   QB 1  RB 2  WR 2  TE 1  SUPER_FLEX 1  FLEX 3   = 10 startable
```

Identical at every named position. Identical superflex. **One extra FLEX.** Bench, taxi and IR
differ too but cannot enter: `slots_from_roster_positions` never returns them, rounds were
matched at 15, and `starter_value` reads only the solved lineup.

**A single flex slot moves the control-vs-engine verdict from a loss to a win.**

That is coherent rather than surprising. A flex slot is where surplus positional depth becomes
startable, and depth is exactly what the engine buys and the control does not. With two flex
slots the engine's extra bodies sit on the bench and `starter_value` never sees them; with three,
one more converts. It is also the same slot type `#247` found the feasibility backstop refuses to
protect — flex is where this engine's behaviour concentrates, in both directions.

## This also dates `#205`

Arm A is the fixture format measured on TODAY's code: **4 of 12, −0.28%.** The committed `#205`
figure for the same format is **1 of 12, −5.03%**, produced at commit `8cee942` — **190 commits
back**, including `#216 WIRED: one slot, one alternative reaches the board`, which changes
precisely how flex capacity reaches the board.

So `#205`'s headline deficit is **stale evidence, not a live property of the engine**. It was
never wrong; it describes a different codebase. The skill's own rule — *never compare a fresh run
against a saved baseline from different code* — is why arm A exists, and it earned its place: my
own `expect` string on that arm said "reproduces 1/12, −5.03%", and that expectation was
misconceived before the run started.

## What this does NOT establish

- **Why one flex slot is worth this much.** The mechanism above is a reading, not a measurement.
  The cut that would settle it: the fixture roster with a third FLEX added and nothing else
  changed.
- **That the engine is better.** +1.04% is small, and the honest summary across all three arms is
  that engine and control are within ~1% of each other in every shape tested. The large deficit
  that framed this whole question no longer reproduces on current code in any arm.
- **Anything about `cdme`.** It remains the tautological ruler and is not reported here.
