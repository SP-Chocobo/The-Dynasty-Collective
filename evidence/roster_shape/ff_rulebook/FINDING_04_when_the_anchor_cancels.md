# The anchor cancels sometimes, and the exception is where TE lives

## The identity under test

The #221 memo established, for one measured pair, that with the shared alternative wired
the league anchor CANCELS: `universal_value + displacement_adj == projection - shared_alternative`.
If that held generally, every flex-eligible candidate would be priced against one number,
and the engine's ranking among them would reduce to raw projection.

`cancellation_probe.py` tests the identity directly, on the real rulebook, at three drain
states, with the ten starting slots filled.

| drain | pos | proj | VOR | dispAdj | VOR+adj | proj - flexAlt | identity |
|---|---|---|---|---|---|---|---|
| 0 | RB | 299 | 156 | -163 | -7 | 110 | no |
| 0 | WR | 315 | 126 | -117 | 9 | 126 | no |
| 0 | TE | 284 | 134 | -156 | -22 | 95 | no |
| 20 | RB | 199 | 134 | -103 | 31 | 54 | no |
| 20 | WR | 221 | 76 | -23 | 53 | 76 | no |
| 20 | TE | 164 | 143 | -147 | -4 | 19 | no |
| 40 | RB | 116 | 80 | -59 | 21 | 21 | **YES** |
| 40 | WR | 183 | 88 | 0 | 88 | 88 | **YES** |
| 40 | TE | 30 | 10 | -16 | -6 | -65 | no |

## What it says

**The identity holds only when the free alternative actually binds.** Early (drain 0, 20)
my own starters are stronger than the league's free player, so `displacement_level` returns
one of MY starters and the candidate is priced against my roster, not against the shared
alternative. That is the term behaving exactly as its docstring says it should.

Late (drain 40) the pool is weak enough that the free alternative binds, and RB and WR
both land on the identity exactly -- 21 = 21 and 88 = 88. So in the late bench phase, RB and
WR ARE priced against one shared number, and the ranking between them reduces to projection.

**TE is the exception at every state, and at drain 40 it is a 59-point exception.** The
"one slot, one alternative" logic says a tight end projecting 30 in a flex whose free
alternative is worth 95 should net -65. The engine nets him -6. The cause is the
documented non-positive rule -- a slot held by someone BELOW the league alternative deducts
nothing rather than lifting the candidate -- so when my own tight end is weak, the deduction
is capped at `level_TE - my_TE` rather than reaching `flexAlt - proj`.

That rule is deliberate and its reasoning is sound (lifting a candidate for my own weak
starter would pay twice for one fact). But its consequence is that **TE is systematically
under-charged in a flex relative to RB and WR**, by an amount that grows as my own tight end
gets weaker. It is the mirror image of FINDING_03: WR pays nothing because it DEFINES the
alternative; TE pays less than it should because the deduction is capped by my own roster.

## Where this leaves the two readings

FINDING_03 recorded Reading A (double-count) and Reading B (correct marginal reasoning)
and could not separate them. This probe rules out the simplest version of A: **starter
demand is conserved.** `starter_slot_counts` sums to exactly 10.0 for a ten-starter roster,
so the flex share folded into each position's rank is not additional demand invented on top
of the flex slot. There is no double-count of DEMAND.

What survives is narrower and sharper: the shared alternative is `max(level)`, and the
position holding that max is priced against itself. That is not a demand error. It is a
question about whether a position's own replacement level is still a *freely available*
alternative during the bench phase, when no slot is at stake and eleven other managers are
drawing from the same pool.

That question is not settled by any probe run so far, and the 12x26 draft on the real
rulebook is still the discriminator.
