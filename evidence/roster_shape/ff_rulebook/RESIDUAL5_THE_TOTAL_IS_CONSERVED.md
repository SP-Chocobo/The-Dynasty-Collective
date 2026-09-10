# RESIDUAL 5 — the symmetry break redistributes; it does not create

**Invocation:** none. Every number below is read from artifacts already on disk
(`ff_draft.json`, `ff_draft_revseat.json`, `ff_draft_3rr.json`, `ff_draft_balanced.json`),
produced by `run_ff_draft*.py` under the #201/#204 recipe. No engine was run for this.

**Basis tag:** ARTIFACT-READ. Nothing here is a fresh measurement; the reproduction gate at
#218 is untouched by this document.

---

## Why this exists

The standing open question was framed as a symmetry break:

> Twelve seats, byte-identical code, all holding exactly ONE tight end at their 9th own
> pick, finishing 1, 9, 1, 4, 9, 3, 7, 1, 14, 2, 2, 15.

The proposed attack was to find the symmetry-breaking variable. Before spending a draft
(~640-1125s per arm) on a new permutation, I read the permutations that were already run.

**Two of them were already the permutation test.** `ff_draft_revseat` reverses the seat
labels. `ff_draft_3rr` reverses pick order from round 3 onward. Both were run months of
session-time ago for a different purpose and never analysed for this question.

---

## Result 1 — seat labels are inert (a determinism check, and it passes)

`base` vs `revseat`: the same player at **312 of 312 overall picks**. Not the same set —
the same sequence. The TE-by-slot vector is byte-identical: `[5,8,7,9,10,7,8,6,10,8,11,12]`.

So "seat 9 is tight-end hungry" is not a statement about roster 9. It is a statement about
**slot 9** — the draft position, not the identity. Reversing the labels moved the behaviour
with the slot, exactly. Any hypothesis that reads `roster_id` is dead.

This is also the cleanest determinism evidence in the file: a full 312-pick draft, relabelled,
reproduces itself exactly.

## Result 2 — order permutation scrambles the recipients and conserves the composition

`base` vs `3rr` — a real perturbation, first divergence at overall 25, and only 183 of 312
overalls carry the same player:

| | base | revseat | 3rr | balanced |
|---|---|---|---|---|
| QB | 32 | 32 | 32 | 32 |
| RB | 84 | 84 | 84 | 80 |
| **TE** | **101** | **101** | **101** | **68** |
| WR | 95 | 95 | 95 | 131 |
| DB | 0 | 0 | 0 | 1 |

- The **set of 312 drafted players is identical** between base and 3rr. Zero players in one
  and not the other.
- Yet only **32 of 312 (10.3%)** go to the same seat.
- For tight ends specifically: the 101-TE set is identical; **7 of 101** land on the same seat.

Seat assignment is ~90% scrambled. League composition does not move by one player.

## Result 3 — the mode boundary is the one thing that DOES move the composition

`base` vs `balanced` (the #222 ablation arm, `mode="balanced"`): the drafted set differs by
37 players, first divergence at overall 171, and the composition moves hard — TE 101 → 68,
WR 95 → 131. Per-round TE counts for rounds 1-14 are identical (2,1,1,2,3,1,2,0,1,3,5,1,3,1);
every unit of the difference is in rounds 15-26. This restates PHASE4_ABLATION_RESULT from
the artifact side and agrees with it.

---

## What this changes

**The bifurcation is a distribution, not a cause.** Under a genuine pick-order permutation the
engine drafts exactly the same 101 tight ends, in a different order, to almost entirely
different seats. The hoarder/starver split has **zero aggregate authority**: all four
team-specific terms together (`need_bonus`, `eligibility_bonus`, `depth_exposure`,
`displacement_adj`) decide *who receives* a player and never *whether the league takes him*.

So the 32.4%-vs-15.5% gap cannot be explained by finding the symmetry-breaking variable.
Whatever that variable is, permuting it leaves the number at 32.4%.

This does not make the bifurcation uninteresting — a chair finishing with 15 tight ends is a
bad roster whatever the league total is — but it demotes it from *the culprit* to *a second,
smaller defect*. It is a fairness/roster-quality problem downstream of a pricing problem.

**The culprit for the total is upstream of any seat.** A composition invariant under order
permutation and variant under mode is a property of (pool x valuation ordering x mode
boundary), not of team state. That is the same place FINDING_01 ("the pool is the shape") and
PHASE4 (the mode boundary, 63% of the gap) already pointed. This is independent corroboration
from an artifact neither of them used.

## Registered caveat

3RR is a **mild** permutation: it preserves each seat's pick count and each seat's approximate
depth in the order. It is a real test — 129 of 312 overalls change hands — but it is not a
random reseating. A composition that survives 3RR has not been shown to survive an arbitrary
permutation. The claim registered here is exactly what was measured: *under third-round
reversal, composition is conserved to the player.* Not more.

Second caveat: n = 1 league, 1 rulebook, 1 pool. Conservation across three arms of the same
pool is not conservation as a law.

---

# Part 2 — the neighbour test (added after Fable's advisory)

**Invocation:** none. Same ARTIFACT-READ basis. The statistic and its direction were specified
by the advisory BEFORE I computed it; I ran exactly the named statistic in the named direction.
That is the pre-registration, and it is why this is a test rather than a search.

## The hypothesis

Snake neighbours contend for the same near-tied players. At a near-tie the seat that picks
first takes the top remaining tight end; its neighbour's tight-end alternative is now one rung
worse, loses the tie, and takes the receiver. Next round the roles invert. Two seats running
byte-identical code, each depleting exactly the position the other would have taken.

Three hypotheses, one discriminator:

| hypothesis | predicts lag-1 neighbour autocorrelation |
|---|---|
| twelve independent coin flips at a common p | ~0 |
| a fixed per-seat trait | ~0 |
| **between-seat pool contention** | **negative** |

Snake adjacency is the linear lattice 1..12 with no wraparound (slot 12 picks twice at the
turn), so lag-1 on the slot vector is the right statistic. Null distribution by exact-form
Monte Carlo over seat-label permutations, 200,000 draws, seed 20260910.

## Result

| arm | TE by slot | lag-1 r | null mean (sd) | P(r_perm <= r_obs) |
|---|---|---|---|---|
| balanced (where the bimodality lives) | 1,9,1,4,9,3,7,1,14,2,2,15 | **−0.487** | −0.083 (0.257) | **0.0495** |
| base (auto) | 5,8,7,9,10,7,8,6,10,8,11,12 | +0.110 | −0.083 (0.257) | 0.762 |
| 3rr (auto) | 10,11,9,9,5,6,9,8,11,7,8,8 | +0.178 | −0.083 (0.254) | 0.840 |

Negative and marginally significant in the arm that has the phenomenon; absent — in fact
mildly positive — in both arms that do not. The advisory predicted exactly that pattern, on
the grounds that only the balanced arm sustains the near-tie for 26 rounds.

## How much this is worth

It is one pre-specified statistic, in one direction, on **one draft of one league**, and
p = 0.0495 sits on the line. n = 12 seats. This is **suggestive and consistent**, not
established. What makes it worth recording is not the p-value but that it converges with a
result derived from different artifacts by a different route: contention predicts conservation
(the same 101 tight ends leave the board; only the recipients change), and Part 1 measured
exactly that, to the player, with 90% of recipients scrambled.

Three observations, one mechanism:

1. composition invariant under order permutation (Part 1),
2. recipient assignment ~90% scrambled by the same permutation (Part 1),
3. neighbours anti-correlated in the arm that bifurcates (Part 2).

Nothing else currently on the table predicts all three. A fixed per-seat trait predicts (1)
and fails (3). Independent flips predict (1) and fail (3). A roster-state mechanism acting on
`displaced` predicts (3) only through a channel Part 1 shows has no aggregate authority.

## What it would take to establish it

The advisory's butterfly test, pre-registered here and NOT run: force one hoarder's near-tie
pick (margin +0.01) the other way, re-run untouched, and read three counts. Independent flips
move the perturbed seat by one. Contention moves that seat by several **and moves both
neighbours in the opposite direction**. Signs stated before reading. Cost ~1,016s for one arm.

This is not authorized and not run. It is registered so that if it is ever run, the prediction
is on record first.
