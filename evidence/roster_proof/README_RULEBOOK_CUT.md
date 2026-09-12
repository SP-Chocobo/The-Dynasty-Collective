# #248: it is not the rulebook. It is ONE FLEX SLOT.

Three arms, one process, one code version, matched at 15 rounds — the only honest A/B this
repository allows. `run_roster_proof_rulebook_cut.py`, pre-registered at `1c6611c` before any
number existed.

```
A  fixture roster + fixture scoring    points  4 of 12   -0.28%
B  fixture roster + F&F scoring        points  4 of 12   -0.61%     <- THE CUT
C  F&F roster     + F&F scoring        points 10 of 12   +1.04%
```

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
