# Which term decides, once the shared alternative is on? THERE IS NO DOUBLE COUNT.

Owner's league, three seats, five arms, one process, one thing toggled each. The probe lives in
this directory (`term_ablation/run_shared_terms_probe.py`) and was RUN FROM OUTSIDE THE TREE while
the full suite was in flight, because editing the tree during a measurement is the oldest rule in
the engine-measurement checklist and I had already broken it once in this pass.

| arm | lineup total (3 seats) | vs SELF | compositions (QB/RB/WR/TE) |
|---|---|---|---|
| SELF (shipped) | 7651.1 | — | 2/6/6/0 · 2/6/6/0 · 2/6/6/0 |
| SHARED | 7571.9 | −79.1 | 4/6/3/1 · 3/5/4/2 · 3/6/4/1 |
| SHARED, `depth_exposure` zeroed | **7571.9** | −79.1 | 4/6/3/1 · **3/4/4/3** · **3/5/5/1** |
| SHARED, `eligibility_bonus` zeroed | **7571.9** | −79.1 | 4/6/3/1 · 3/5/4/2 · 3/6/4/1 |
| SHARED, `need_bonus` zeroed | 7543.0 | −108.1 | 2/7/2/3 · 3/7/2/2 · 3/6/4/1 |

## 1. There is no double count. The lineup cost is the price of the shape.

**Zeroing `depth_exposure` and zeroing `eligibility_bonus` each leave the lineup total at exactly
7571.9 — not one point of the −79 belongs to either.** Together with `need_bonus`'s own arithmetic
(its flex term is capped at 1.0 point against a 118-point swing), all three capped terms are
excluded as the cause.

So the −118 across all nine seats is **intrinsic to the shared alternative**. It is not a bug
downstream; it is what pricing every flex candidate against one alternative costs in expected
season points. **0.5% of lineup value for the roster shape.** That is the trade, stated in its
own units at last, and it is #217's question — the objective — not a defect.

## 2. `depth_exposure` moves the roster AWAY from the band and buys nothing

Same lineup value to the point, materially better compositions:

| seat | SHARED | SHARED with `depth_exposure` off | band target |
|---|---|---|---|
| 6 | 3/5/4/2, ordering **fails** | **3/4/4/3, ordering passes** | QB 3.11 RB 3.76 WR 5.06 TE 2.07 |
| 12 | 3/6/4/1, ordering **fails** | **3/5/5/1, ordering passes** | same |

Strict ordering goes **0 of 3 → 2 of 3** while the lineup total does not move at all. A term that
carries selection authority and changes which players are taken WITHOUT changing what the roster
is worth is the exact shape #55 ruled on for `pick_necessity`: **observable, not authority.** This
is evidence for that ruling applied to `depth_exposure` (#139), and it is a finding, not a change
— nothing here is wired.

## 3. `need_bonus` is load-bearing, confirmed again

Zeroing it gives RB 7 / WR 2 in two of three seats and costs a further 29 lineup points. #87's
ablation result holds: it is a positional GATE, not a nudge.

## 4. What does NOT come out of this

Seat 1's **four quarterbacks** are byte-identical under SHARED, SHARED_ND and SHARED_NE, so
neither `depth_exposure` nor `eligibility_bonus` explains them.

**CORRECTION, made before this file was read by anyone.** My first draft of this paragraph went on
to assert "it is the SUPER_FLEX phantom", on the reasoning that `max` over that slot mixes QB's
startable-floor level with everyone else's demand-rank level. **The table on this page contradicts
that in the very next row**: SHARED_NN — `need_bonus` zeroed — comes back with **QB 2**, so
`need_bonus` is implicated somewhere in the sequence and "not any of the three capped terms" was
false as I wrote it. Zeroing `need_bonus` is not a remedy either: the same arm gives RB 7 / WR 2
and costs a further 29 lineup points, which is #87's gate result holding.

**So the mechanism behind the fourth quarterback is NOT established.** Two facts are: it is
untouched by two of the three capped terms, and it disappears when the third is removed at a price
that is worse elsewhere. The mixed-anchor observation about SUPER_FLEX remains worth measuring —
`max` really does compare a startable-floor level against demand-rank levels — but it is a
hypothesis with a mechanism, not a diagnosis, and it now has a measurement standing against the
sentence I nearly published. Sixth withdrawal on this item; recorded, not deleted.

## A probe defect caught before it became a finding

The first version of this ablation zeroed a key called `exposure` in `depth_exposure`'s return.
**Nothing reads that key** — the board reads `worst_loss` — so `SHARED_ND` came back byte-identical
to `SHARED` and would have been published as "depth_exposure is not the cause". An unapplied
mutation reads exactly like a survivor. The `eligibility_bonus` patch returned a bare float where
the caller subscripts a dict, so that arm crashed instead of lying — the luckier of the two
failures. Both were found by reading what `draft_room` actually subscripts before trusting either
arm.

## All three formats, all nine seats (`term_ablation_all_formats/`)

| arm | lineup total | band distance | strict ordering | owner's reading | legal | new asset reversals |
|---|---|---|---|---|---|---|
| SELF (shipped) | 21949.5 | 47.45 | 6/9 | 6/9 | **9/9** | — |
| SHARED | 21832.0 (−0.53%) | 39.41 | 6/9 | 7/9 | **9/9** | **2** |
| SHARED + `depth_exposure` demoted | 21832.0 (−0.53%) | **37.33** | **8/9** | **8/9** | **9/9** | **2** |

`SHARED_ND` is the best configuration measured in this whole pass on every shape ruler there is,
at an identical lineup cost to `SHARED` — the demotion is free in points and worth two seats of
ordering. It is **still not shipped**, for one reason that is not about aggregates:

**it produces a four-quarterback roster in a league with two quarterback-capable slots.** That is
a bad roster, not a trade, and it is the same standard that rejected the flex share's
four-tight-end seat. Applying that standard to somebody else's change and not to my own is the one
failure mode this whole pass exists to avoid.

## Where this leaves the decision

Three things are now measured rather than argued:

1. **The shape costs 0.53% of expected season points.** Not a defect, not a double count — the
   price of pricing every flex candidate against one alternative. The owner's stated objective is
   "within a competitive band", not point-maximal, and 0.53% is inside any band; but the engine
   does not encode an objective at all, which is #217.
2. **`depth_exposure` has selection authority it is not paying for** — same lineup value to the
   point, two seats of ordering worse. That is #55's ruling shape applied to #139.
3. **The four-quarterback seat blocks it**, and its mechanism is not known.

## The four quarterbacks: diagnosed, and it is not the shared alternative's defect

Owner's league, seat 1, `SHARED_ND`, the picks the engine actually made:

| rnd | pick | my QBs before | best-row `bpa` |
|---|---|---|---|
| 3 | QB Sam Darnold 307.21 | 0 | 99.71 |
| 5 | QB Malik Willis 289.64 | 1 | 82.14 |
| 9 | QB Daniel Jones 281.89 | **2** | **74.39** |
| 10 | QB Bryce Young 265.02 | **3** | **57.52** |

**Every one of those is `projection − 207.5`, exactly.** 281.89 − 207.5 = 74.39. 265.02 − 207.5 =
57.52. That 207.5 is the **startable floor** — `qb_startable_floor`'s cliff-anchored count — and
`run_216_qb_price_probe` already measured it as the QB level at EVERY round of this format.

That is the whole mechanism. Every other position's anchor is a demand rank that moves as the
league's starting slots fill; **QB's is a count of quarterbacks still above a projection
threshold, and with 32 of 42 above it, drafting a few barely moves it.** So a fourth quarterback
still prices at +57 of raw `bpa` while a fourth running back's anchor has long since caught up
with him. `displacement_adj` deducts −82 for having to displace my own QB2, which lands him near
zero — close enough that ±36 of capped team terms decides the pick.

**This is not a defect the shared alternative introduces.** The shipped engine takes only two
quarterbacks in that seat because every OTHER position keeps its inflated own-anchor `bpa` and
outranks them. Remove that inflation — which is what the shared alternative correctly does — and
what is left standing is the quarterback anchor, on a different and more generous scale than
everything it is being compared against.

**So the blocker is a pre-existing one the repair exposed: two anchor models, one board.** That is
the same finding #185/#186 recorded from the labelling side, and it is #50 — the exchange rate
between a startable-floor level and a demand-rank level, which nothing in this engine has ever
had to state because until now nothing forced the comparison.

Arithmetically verified, not inferred: the four `bpa` values above are `projection − 207.5` to the
cent, and 207.5 is the level `run_216_qb_price_probe` independently measured for this format.
