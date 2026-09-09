# The ten receivers: my recorded mechanism was wrong, and the real one is arithmetic

*#216 / #221. Measured after DIALLED_IN.md §4 named the ten-receiver seat as the last blocker.*

## The ninth withdrawal

DIALLED_IN.md §4 recorded this, in bold, as the thing that had to be understood before the
shared-slot alternative could ship:

> The position whose replacement level is the maximum is NEVER deducted at a shared slot, on
> any roster state, no matter how many of that position are already held. Every other position
> is. So that position accumulates without limit. This is structural in `max`.

**It is false, and the measurement that produced it did not saturate.** It read four receivers
against five WR-reachable slots (`WR_3`, `WR_4`, `FLEX_6`, `FLEX_7`, `SUPER_FLEX_8`) and found
`+0.00`. Of course it did — a slot was still open. `sat_probe.py` adds receivers until every one
of those five is held by a real player who beats the alternative:

```
#WR held |   WR adj  WR disp |   RB adj |   TE adj
       0 |     0.00   215.10 |   -38.10 |   -52.40
       3 |     0.00   215.10 |   -38.10 |   -52.40
       4 |   -54.90   270.00 |   -93.00 |  -107.30
      10 |   -54.90   270.00 |   -93.00 |  -107.30
```

The max-level position IS deducted, from the moment its slots fill. `max` is not the mechanism
and there is nothing structural to repair in `shared_slot_alternatives`.

## What the table actually says, which is a different and sharper thing

Read the row at 4 held across, not down. Every position moved by **exactly the same 54.90**.
`displaced` is 270.00 for RB, WR and TE alike — they share the marginal slot, so the weakest
starter any of them would evict is the same player. `sat_probe2.py` confirms it is the shared
slot doing this and not a coincidence of one roster: hold the flexes with running backs and
`displaced` is 268.00 for all three; hold them with tight ends and it is 272.00 for all three.

So at any state where the shared slots are the marginal ones:

    bpa + displacement_adj  =  (proj - level_pos) + (level_pos - displaced)  =  proj - displaced

and `displaced` is **common to every position that reaches the slot**. The last column of
`sat_probe2.txt` prices a 250.0-point player at RB, WR and TE and gets -20.00, -20.00, -20.00.

**The league anchor cancels exactly.** That is not a bug — it is what "one slot, one
alternative" MEANS, and it is the correct arithmetic for a slot three positions compete for.
The tight-end bias #216 opened with is gone because the anchor that carried it is gone.

But it is also the whole story of the ten receivers, and it holds from round 2, not only at
saturation. The round-6 dump in DIALLED_IN.md §3 shows it unsaturated: Garrett Wilson's
`bpa 30.7 + disp 0.0` and Quinshon Judkins' `bpa 62.2 + disp -43.0` are 244.7 - 215.1 and
233.2 - 215.1. Two positions, one ruler, raw projection deciding. **Under the shared
alternative the board prices every flex-eligible candidate on projection minus one common
number, so position is factored out of the anchor entirely.** In a PPR format the deepest tail
of high raw projections is WR. A position-blind board takes receivers until the tail runs out.
Ten of fifteen.

## The second thing the table says, which is the one that needs a decision

From 4 held to 10 held, `displaced` does not move. It is 270.00 at every step.

`displacement_level` answers "what must I beat to START here", and the weakest starter is
unaffected by anything on the bench. So the fifth receiver and the eleventh receiver are
priced **identically**. The term prices each bench candidate as though he alone gets the seat
he would displace into; six of them cannot all have it. The displaced starter is a finite
resource and this construction never spends it.

That is not a defect in the shared alternative either — it is equally true of the shipped
per-position phantom, which also holds `displaced` flat across the bench. The shared
alternative did not introduce it. It made it VISIBLE, by removing the positional anchor that
was previously masking it with a 38-52 point per-position offset.

## Where this leaves the shipping decision

The shared-slot alternative is correct where it is used and it removes a real bias. What it
also removes is the only thing in the anchor that distinguished positions once a flex was in
play. Positional differentiation after it must come from terms that know about BODIES rather
than about levels, and the board has exactly two: `need_bonus` (whole reachable magnitude
8.67, against a 30-60 point projection spread) and `depth_exposure` — which the term-ablation
pass measured as pushing the WRONG WAY, gaining an ordering seat when it was zeroed.

So the open question is no longer "why do receivers accumulate" (arithmetic, above). It is
whether a DERIVED differentiation term exists at the right magnitude, and that is #217's
question, not a repair to this one.

Both constructions remain stranded behind their seams. Nothing in this memo changes a board.
