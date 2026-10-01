# ⛔ It is NOT one flex slot. `#248`'s closing reading is WITHDRAWN (27th).

Four arms, one process, one code version, rounds pinned at 15. Pre-registered at `5936b53`
**before any number existed**; `run_roster_proof_flex_cut.py` carries the registration verbatim.

```
                                        points          cdme (tautology, reported for completeness)
A2  fixture roster, FLEX 2   start  9   4/12  -0.28%     0/12  -14.78%   CONTROL
D   fixture roster, FLEX 3   start 10   3/12  -0.84%     0/12  -17.65%   THE FORWARD CUT
C2  F&F roster,     FLEX 3   start 10  10/12  +1.04%     7/12   +0.76%   CONTROL
E   F&F roster,     FLEX 2   start  9   9/12  +0.84%     8/12   +4.18%   THE MIRROR CUT
```

## The controls reproduced EXACTLY, which is the only reason the cuts can be read

`A2` against `#248`'s arm A and `C2` against its arm C: **0 differing values across 12 seats ×
every metric** — `cdme` and `points`, starter / bench / total, `starters_filled`, `unpriced`.
Not "to the cent"; bit-for-bit identical.

That also settles something `#247` could not settle about itself. Its measured 0.0% bind rate on
12-team formats was a rate over a battery population; this is the same seats, same picks, same
totals across a repair that rewrote `feasibility_first`. **`#247` is provably inert here**, not
merely unobserved.

## Both cuts are null, and — the part that kills the reading — they have no consistent sign

The slot was moved by **exchanging a BN for a FLEX** and back, never appended or deleted, so
`len(roster_positions)` never moves and every code path reading roster LENGTH rather than SHAPE
sees nothing. `swap_one` raises rather than returning an unchanged roster. Rounds pinned at 15.
The startable count is the only thing that moves: 9 ↔ 10.

| | engine − control, `points.starter_value` |
|---|---:|
| A2 fixture FLEX 2 | **−6.99** |
| D fixture FLEX 3 (one flex **added**) | **−22.53** |
| C2 F&F FLEX 3 | **+29.43** |
| E F&F FLEX 2 (one flex **removed**) | **+22.08** |

Adding a flex to the loser made it worse. Removing a flex from the winner also made it worse.
**A slot that hurts in both directions is not the thing that separates the two leagues** — it is
noise of about the same size as the effect it was supposed to explain, with the wrong sign twice.

The between-league gap is **1.32 points of percentage** (−0.28% → +1.04%). The flex slot accounts
for 0.56pp and 0.20pp of movement, both downward. That is the pre-registered `D ≈ A2 AND E ≈ C2`
branch, hit in both directions at once.

## What `#248` claimed, and what is withdrawn

> *"**A single flex slot moves the control-vs-engine verdict from a loss to a win.** … A flex
> slot is where surplus positional depth becomes startable, and depth is exactly what the engine
> buys and the control does not."*
> — `README_RULEBOOK_CUT.md`, now struck

**That is refuted.** The mechanism paragraph was explicitly labelled "a reading, not a
measurement" and it named its own settling cut. The cut was run and the reading did not survive
it. The `#248` document stands unedited beneath a withdrawal banner; only the reading is void —
its measured arms (A/B/C) reproduce exactly and are untouched.

## The comparison that makes the residual unavoidable

`A2` and `E` have the **same number of startable slots (9)**, the same rounds, the same pool, the
same harness — and opposite verdicts: **−6.99** against **+22.08**. So it is neither the flex
count nor the startable count.

And the rulebook was already eliminated: `#248`'s arm B moved half-PPR, the TE premium, first
downs and the completion bonus **alone** and changed the verdict by nothing (4 of 12 either way),
in an environment measured as paying four real starters 15.7% differently.

Three candidates entered this investigation. Two are now refuted by measurement:

| candidate | verdict | evidence |
|---|---|---|
| draft length | REFUTED | `#245` — identical to the cent at 15 and 26 rounds |
| scoring rulebook | REFUTED | `#248` arm A→B — 4/12 either way |
| flex / startable count | **REFUTED** | this run, both directions, no consistent sign |

## What is left, stated as a structure rather than a story

At 15 rounds the two rosters differ in **how much room they have left**:

```
fixture   15 slots   9 startable   15 draftable   -> 15 picks fill it EXACTLY.  0 spare
F&F       29 slots  10 startable   26 draftable   -> 15 picks fill 15 of 26.   11 spare
```

This is not inert, and `#248` was wrong to dismiss it as unable to enter.
`draft_room.draftable_slots_per_team` counts every slot except IR and feeds
`remaining_league_picks` — *"how many draft picks the league still has to spend, summed per
team… EXACT and BOUNDED, reaching exactly zero when every roster is full"* — which in turn feeds
the bench-appetite rates. On the fixture that quantity is driven to zero; on F&F it never falls
below 11 per team. **Roster capacity reaches the engine independently of both flex count and
round count.**

Note that both cuts here held capacity fixed by construction (BN ↔ FLEX preserves the total), so
nothing in this run tests it. That is the next cut, and it is the last of the three structural
differences still standing.

## The pre-registered next cut

The fixture roster with **bench slots padded to F&F's 26 draftable**, nothing else changed:
same 9 startable slots, same PPR rulebook, same 15 rounds, same pool. One variable —
`draftable_slots_per_team` 15 → 26.

- engine moves toward `+1.04%` → **roster capacity is the mechanism**, and every fixture-measured
  verdict in the freeze record was taken in a league whose picks run out exactly when the draft
  does.
- engine stays near `−0.28%` → capacity is refuted too, all three structural candidates are gone,
  and what remains is the only difference left: **TAXI slots**, which the fixture has none of and
  F&F has five.

## What this does NOT establish

- **Anything about which league is "right".** Every arm here sits within ~1% of its control. The
  large deficit that framed this whole question does not reproduce in any arm.
- **`cdme`.** Reported above only because it is in the artifact. It is the engine's own objective
  and a win there is a tautology. It is worth one line that it **loses 0 of 12 on both fixture
  arms** while winning on both F&F arms — `COMPARE_ON["cdme"]` is `total_value`, which carries a
  large negative bench term, and a tautological ruler that loses is its own question. Not this
  one. Nothing here is claimed from it.
