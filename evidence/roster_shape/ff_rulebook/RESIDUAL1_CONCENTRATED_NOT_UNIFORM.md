# The residual is CONCENTRATED, not uniform — and roster AWARENESS is what concentrates it

First characterisation of the one thing #222 left genuinely open: with the mode effect removed,
the engine still drafts 21.8% tight ends against the humans' 15.5%. **Reads of already-saved
drafts only — no new runs, no board builds, no engine calls, no engine source changed.**

The balanced-mode ablation arm is the right dataset: `mode="balanced"` is held for all 26
rounds, so nothing measured here is the mode boundary.

---

## 1. It is concentrated

TE bodies per seat, 26 picks each. **The twelve real managers took 3–6 apiece.**

| arm | per-seat TE counts | min | max | median | stdev | total |
|---|---|---|---|---|---|---|
| AUTO (`mode="auto"`) | 5, 8, 7, 9, 10, 7, 8, 6, 10, 8, 11, 12 | 5 | 12 | 8.0 | **1.98** | 101 |
| **BALANCED ×26** | **1, 9, 1, 4, 9, 3, 7, 1, 14, 2, 2, 15** | **1** | **15** | 3.5 | **4.85** | 68 |

| arm | TEs held by the top-3 seats | by the bottom-3 |
|---|---|---|
| AUTO | 33% | 18% |
| **BALANCED** | **56%** | **4%** |
| *(uniform)* | *25%* | *25%* |

The balanced arm's excess is not a bias every chair shares. **Three seats hold 56% of all the
tight ends; three others hold 4%** — one apiece, in a league with a mandatory TE slot and three
FLEX slots. It is bimodal: hoarders and starvers, and almost nobody in the humans' 3–6 band.

## 2. And the direction is the surprising part

**Roster-AWARE valuation produces MORE positional divergence than roster-BLIND valuation.**

Upside mode zeroes every team-specific term, so it has no way to respond to a seat's own
roster — and it gives every seat a similar tight-end share (5–12, stdev 1.98). Balanced mode has
`need_bonus`, `eligibility_bonus`, `depth_exposure` and `displacement_adj` all live, all reading
the seat's own roster — and the seats bifurcate (1–15, stdev 4.85).

That is backwards from what roster awareness is for. It is also consistent with the earlier
monoculture measurement (largest single-position pile 12 → 19; seats with ≥12 at one position
3 → 7; (seat, position) pairs left at ≤2 bodies across RB/WR/TE 0 → 7).

**Stated at the strength it has: two arms of ONE draft, twelve seats each.** It is a shape, not
an estimate, and it names the next question rather than answering it.

## 3. One hypothesis raised and killed in the same pass

The obvious mechanism for a hoard/starve split is **positive feedback through
`displacement_adj`**: that term is `level − displaced`, and `displaced` is the seat's own best
tight end. A seat whose best TE is weak faces a *smaller* deduction, so tight ends stay cheap
for it, so it takes more — a spiral. A seat with a strong TE1 faces a large deduction and stops.

The cheapest discriminator available without touching projections is **when a seat took its
first tight end** (early ≈ good).

| seat | TE total | first TE at own pick # |
|---|---|---|
| 9 | **14** | **1** |
| 7 | 7 | **1** |
| 12 | **15** | **7** |
| 5 | 9 | **7** |
| 1 | **1** | 4 |
| 3 | **1** | 5 |

**Pearson r(first-TE pick number, total TEs) = +0.101, n = 12.** Nothing. Seats 9 and 7 both
took their first tight end with their first pick and finished on 14 and 7; seats 12 and 5 both
waited until their seventh and finished on 15 and 9.

**Timing does not discriminate hoarders from starvers, so the timing proxy for the feedback
hypothesis is dead.** That does not kill the feedback hypothesis itself — timing is a poor proxy
for TE1 *quality*, which is the quantity the mechanism actually turns on. It does mean the
hypothesis has no support yet and must not be carried forward as though it had.

## What this establishes, and what it does not

**Establishes:** the residual is concentrated and bimodal; it appears when roster awareness is
ON and not when it is off; and the first candidate mechanism has no support from the cheapest
available discriminator.

**Does not establish:** any mechanism at all. There is still no suspect — only a sharper
description of what a suspect has to explain.

**What a suspect must now explain:** not "why does the engine like tight ends" but **"why do
twelve seats running identical code diverge into hoarders and starvers, and only when the
roster-aware terms are live?"** That is a different question from the one #222 started with, and
it is the one the next measurement should be pre-registered against.

## Next step, NOT yet taken

The honest test of the feedback hypothesis reads `displaced` per seat over the draft — the
production quantity, from `displacement_adjustments`' own return, tagged per seat — and asks
whether a seat's tight-end deduction is systematically smaller in the seats that hoard. That is
a probe, it needs pre-registration before it runs, and it has not been written.
