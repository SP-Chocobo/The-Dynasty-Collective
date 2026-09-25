# The ceiling question, answered: A is load-bearing and C does not replace it

The owner's own words: *"I don't love forcing a ceiling. It's not a bad idea, as far as internal
limits, where it should present other positions as depth more. But in deeper leagues, if a qb3 is
there, or dynasty, I dont love the forced hold."* This is the measurement of that discomfort.

A is a **counting** bound (`unfieldable_last`: at most `slots(P) + 1` of a dedicated position). C is
a **pricing** change. So the live question was never only "is C worth its cost" but "would C's
pricing have made A's counting unnecessary". `capped_floor_exempt_no_backstop` is the only arm that
can answer it, and the reading was fixed in advance in two parts, **both required**.

## Part 1 — points. Failed, and not narrowly.

2023, 12 seats, realized ruler, `12T_ppr_K_DEF`:

| arm | wins | mean | median |
|---|---:|---:|---:|
| control (shipped: A on, no C) | 4/12 | −49.9 | −81.0 |
| `capped_floor_exempt` (A on, C on) | 4/12 | **+1.0** | −6.9 |
| `capped_floor_exempt_no_backstop` (A **off**, C on) | 1/12 | **−100.1** | −99.3 |

Paired, no-ceiling minus ceiling: **0 seats improved, 12 worsened**, total −1242.4, **mean −103.5 per
seat**, median −85.6, range −59.8 to −241.1. There is no noise interpretation of a result with no
exceptions in twelve.

Against the shipped engine it is −59.8 per seat. So removing the ceiling is worse than never having
had C at all, by a wide margin.

## Part 2 — roster shape. Failed at every seat, and the failure has a name.

`fieldable_ceiling` for this format is `{QB: 2, K: 2, DEF: 2}`. Seats holding a position past it:

| arm | seats past the ceiling |
|---|---|
| `capped_floor_exempt` (A on) | **0 of 12** |
| `capped_floor_exempt_no_backstop` (A off) | **12 of 12** |

And it is the same position every time — **kickers, in a league with one kicker slot**:

```
no ceiling, 2023:   seat 1  WR5 K4 RB3 QB2 TE1 DEF1
                    seat 5  K5 WR4 RB2 TE2 QB2 DEF1
                    seat 11 WR7 K4 RB2 TE1 QB1 DEF1
                    ... K4 at ten seats, K5 at one, K4 at the twelfth

ceiling on, 2023:   seat 1  WR6 RB3 QB2 K2 DEF2 TE1
                    seat 9  RB5 WR5 K2 DEF2 TE1 QB1
                    ... K2 and DEF2 at all twelve
```

Four or five kickers, at every seat, on a board whose pricing has just been corrected. This is the
`#216` pathology — a position hoarded past any slot that could field it — and it is the SAME shape
`#30`'s streaming floor produced when it shipped without the backstop (measured then at seat 1: K 5,
DEF 1). Two different pricing changes, one made the levels honest and the other capped a stale
phantom, and both relocated the hoard rather than removing it.

**And the cost is not only the wasted kickers.** Without the ceiling those seats fall to **QB1 and
DEF1** at ten of twelve. The picks that would have bought a second quarterback and a second defense
went to third and fourth kickers. So A does not merely cap a count; it redirects picks toward
positions that can actually take the field, which is why its removal costs three figures a seat.

## The answer

**The ceiling is mandatory, not stylistic.** Pricing alone does not produce a fieldable roster — this
is now the second pricing change measured against that question and the second to fail it. The
owner's discomfort is real and the engine cannot honour it for free: what it buys is not "forced
holds", it is the difference between a roster with two quarterbacks and one with four kickers.

What the owner asked for beyond the ceiling — not holding a QB3 in a deep or dynasty league — is a
separate thing and remains available, because it lives in the **preference** layer the owner already
drew the line around, not in the bound. The bound says *at most* `slots(P) + 1`; it never says a
manager must fill that allowance. Worth noting that today the engine does fill it: every seat in
every A-on arm carries exactly K2 and DEF2. Whether a second kicker is wanted is a product question,
and it is the one place a "C later" preference would visibly pay.

## Limits

One season and one format for the shape reading; the 2024 no-backstop arm was still running when
this was written and is reported separately. The ruler is an oracle weekly lineup with no waivers,
which **rewards** hoarding if anything — a bench body can always be started in a week its starter
scored less. So −103.5 per seat is a LOWER bound on what the ceiling is worth, not an upper one.
