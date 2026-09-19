# Executing the seven owner rulings

One file per ruling as it is worked, with the measurement taken BEFORE the change. The rulings
themselves and the measurements they were made against are in `CDME_CONTRACTS.md`; this is the
record of carrying them out.

---

## `6.1b` — unify the multi-eligibility price *(measurement complete; removal pending)*

The ruling: **unify** `displacement_adj`'s lift and `eligibility_bonus` into one derived price.
Before designing anything, the premise was measured, because *"these two may both be pricing
multi-eligibility"* is a claim and not an observation.

### What the two terms actually are

The code already states the division of labour, at the call site:

> *"the open slot is his, and `eligibility_bonus` prices what that flexibility GAINS him; this
> term must not take it away."*

So `displacement_adj` is meant to be a **deduction** (the league anchor's over-credit) and
`eligibility_bonus` the **lift**. W1-01 found that on a multi-eligible row `displacement_adj`
goes **positive** — at which point it has stopped removing over-credit and started paying for
flexibility, which is what the other term already pays for.

The lift is not arbitrary. `test_216_displacement` argues it well: a WR/DB anchored on a WR
level of 216 whose cheapest reachable slot is worth 104 was **over-penalised** by his own
anchor, *"so passing on him costs 104, not 216 — and the term says so with a LIFT."* It is the
anchor correction running in the other direction.

### Measured — 36 board states, 3 rulebooks, 4 roster depths, 3 seats, 46,020 rows

| | |
|---|---:|
| single-position rows with `displacement_adj > 0` | **0 of 45,255** |
| multi-eligible rows with `displacement_adj > 0` | 12 of 765 |
| distinct players lifted | **1** (Travis Hunter, IDP only) |
| lift — mean / max | 118.31 / **129.40** |
| `eligibility_bonus` on those same rows — mean / max | 0.28 / 0.84 |
| `eligibility_bonus`'s share of the multi-eligibility credit | **0.24%** |
| lifted rows exceeding `ELIGIBILITY_BONUS_MAX` (12.00) | **12 of 12** |
| rows where `eligibility_bonus` pays and the lift does not | **1**, at 0.24 |

The stated non-positive contract holds perfectly over the population it was written for, and
the lift does essentially all of the multi-eligibility pricing where both terms fire.

### The non-vacuity check that changed the conclusion

The first reading of those numbers was *"`eligibility_bonus` is a vestigial term"*. That would
have been wrong, and the check that caught it is the one this programme keeps relearning:
**print the population.**

Broken down by rulebook, the multi-eligible population on a board is **2 rows** in both
non-IDP leagues — both `DB/WR`. So the measurement said nothing at all about those formats.
And `draft_room`'s own comment names the case the term was built for: *"WR/TE dual eligibility,
a common real Sleeper listing"*, once measured at an 82.00 bonus.

Counted over the capture rather than over a board:

| | |
|---|---:|
| players carrying more than one fantasy position | **178** |
| of those, offence-only (the term's intended population) | **8** |
| of those 8, reaching a board | **0 — every one is retired** |

Kelvin Benjamin, Vince Mayle, Marcus and Tyler Thigpen, B.J. Daniels, Richie Brockel, Will
Johnson, David Johnson. The live population is IDP cross-family — `DL/LB` 127, `DB/LB` 37 —
plus Travis Hunter at `DB/WR`, and flexibility between two IDP slots at similar levels rarely
moves an optimal lineup.

**So the term is inert because its population is empty, not because the term is wrong.** That
distinction decides how it is retired: the ruling was made against an empty population, and a
vendor refresh could refill it.

### Registered before anything is removed

`invariant_registry` gains a ninth entry counting that population, with the census at **178**.
This is the registry watching a population **shrink** — the direction nobody checks. Every
other entry guards against a population growing past a claim proven over a smaller one; this
one fires if an active offence dual-eligibility listing ever returns, because the ruling that
retired the term was made against a population that has none.

That guard is the thing whose absence let the term go inert unnoticed in the first place.

### Still to do

Retire `eligibility_bonus` from `team_acquisition_value`, `TEAM_SPECIFIC_TERMS` (census 4 → 3),
`TEAM_SPECIFIC_CAPS`, and `ELIGIBILITY_BONUS_MAX`. It is named in **31 test files**, so the
removal is its own pass rather than a tail on this one. `lineup_optimizer.eligibility_bonus`
itself stays — it is a correct, general-purpose function with a second consumer; what is
retired is its wiring into the board's sum.

Expected effect on today's boards, stated in advance so it can be checked rather than asserted:
**five rows change by at most 0.84**, and no row changes by more than that.
