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

Seat 1's **four quarterbacks** survive every arm — SHARED, ND and NE are byte-identical there. So
the QB over-accumulation is not any of the three capped terms either. It is the SUPER_FLEX
phantom: `max` over the positions that slot admits, where QB's level comes from the startable-floor
model and every other position's from the demand-rank model. **Mixing two anchor models inside one
`max` is not comparing like with like** — the same two-homes-for-one-vocabulary shape this
repository keeps finding. Named as the next thing to measure; NOT diagnosed, and nothing is wired
on it.

## A probe defect caught before it became a finding

The first version of this ablation zeroed a key called `exposure` in `depth_exposure`'s return.
**Nothing reads that key** — the board reads `worst_loss` — so `SHARED_ND` came back byte-identical
to `SHARED` and would have been published as "depth_exposure is not the cause". An unapplied
mutation reads exactly like a survivor. The `eligibility_bonus` patch returned a bare float where
the caller subscripts a dict, so that arm crashed instead of lying — the luckier of the two
failures. Both were found by reading what `draft_room` actually subscripts before trusting either
arm.
