# WR's displacement adjustment is exactly 0.00, and every other position pays

## Measurement

FINDING_02 measured raw VOR. The engine does not rank on raw VOR: `displacement_adj`
(#216, wired at #221) deducts what the league anchor over-credits a candidate whose slots
this roster already holds. So the question is whether the WR flatness survives the
correction that already exists.

`displacement_probe.py`. Roster: all ten starting slots filled from the top of the board,
which is what a roster looks like when bench picks begin.

| drained each | QB net | RB net | **WR net** | TE net |
|---|---|---|---|---|
| 0 | 0 | -7 | 9 | -22 |
| 10 | -5 | 53 | 47 | -6 |
| 20 | -11 | 31 | 53 | -4 |
| 30 | -52 | 41 | **84** | -21 |
| 40 | -- | 21 | **88** | -6 |

The adjustment column is the tell. **WR's `displacement_adj` is exactly 0.00 at drain 30
and 40**, while RB carries -72 / -59 and TE -83 / -16 at the same states.

Zero means `displacement_level == replacement_level`: the optimizer found this candidate
an OPEN slot whose free alternative is his own position's level. He is priced against
himself, so the anchor cancels and nothing is deducted.

## Why WR and not the others

`shared_slot_alternatives` prices a slot as `max(level(p) for p in slot.eligible)` -- one
slot, one alternative, which is the #216 correction and is right as far as it goes. In
this league the FLEX admits RB/WR/TE, and the levels at drain 30 are RB 46, WR 124, TE 20.
So the flex alternative IS the WR level, always.

The position that DEFINES the shared alternative is priced against itself and pays nothing.
Every other position eligible for that slot pays the difference. Since the alternative is
`max`, the definer is whichever position has the highest replacement level -- and by
FINDING_02 that is the position whose curve is flattest at its demand rank, which is the
deepest pool, which is always WR.

Same shape at SUPER_FLEX, where QB's level (275 at drain 0) is the max and QB defines it.

## What I am NOT claiming

I argued this two ways before writing it down, so both readings are recorded rather than
one being presented as settled:

**Reading A -- this is a defect.** The flex share is already inside every eligible
position's own demand rank (`starter_slot_counts` gives RB 3.05, not 2.0, precisely
because flex demand is distributed into it). Pricing the flex AGAIN as a shared maximum
charges every non-definer a second time for the same slot, and the charge always points at
the deepest pool.

**Reading B -- this is correct marginal reasoning.** If a freely available WR is worth 196
in that flex, then an RB projecting 200 genuinely adds 4, and deducting 45 from him is what
"one slot, one alternative" MEANS. Under this reading the engine is right and the twelve
managers are leaving points on the table.

I cannot separate A from B from this probe, because both predict the numbers above. What
separates them is whether the level at a position's demand rank is still a *free*
alternative during the bench phase -- under A it is not, because no slot is at stake and
eleven other managers are drafting the same pool.

**The full 12x26 draft on this rulebook is the discriminator and it is still running.**
Nothing should be changed in the engine until it lands.

## Fixture honesty

The roster here is CONSTRUCTED -- two QB, three RB, three WR, two TE taken off the top and
assigned by the shipped optimizer. It is a plausible ten-starter roster, not an observed
one. A different construction could move these numbers. The real draft does not have this
weakness, which is another reason to wait for it.
