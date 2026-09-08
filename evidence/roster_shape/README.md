# #216 — the engine drafts exactly TWO wide receivers, in every seat, in every format

## What was measured

`run_roster_shape_probe.py`, six seats across a 1QB and a superflex format, on the real
rulebook, from the shared pool both arms can price.

| | engine roster | control roster |
|---|---|---|
| `12T_ppr` seat 1 | 8 TE, 3 RB, **2 WR**, 1 QB | 6 RB, 5 WR, 2 QB, 1 TE |
| `12T_ppr` seat 6 | 8 TE, 3 RB, **2 WR**, 1 QB | 6 WR, 3 RB, 3 QB, 2 TE |
| `12T_ppr` seat 12 | 9 RB, 2 TE, **2 WR**, 1 QB | 7 WR, 4 RB, 2 QB, 1 TE |
| `12T_ppr_SF` seat 1 | 6 TE, 4 QB, 3 RB, **2 WR** | 9 WR, 3 RB, 2 QB, 1 TE |
| `12T_ppr_SF` seat 6 | 7 TE, 4 QB, 2 RB, **2 WR** | 6 WR, 4 RB, 3 QB, 2 TE |
| `12T_ppr_SF` seat 12 | 5 QB, 5 TE, 3 RB, **2 WR** | 9 WR, 3 RB, 2 QB, 1 TE |

**Exactly two wide receivers. Six seats out of six. Both formats.** The league starts two WRs.

## The three confounds, killed before the finding was written

1. **Is the pool WR-poor?** No — it is WR-RICH. `WR 197, RB 126, TE 115, QB 42` of 481. Wide
   receiver is the DEEPEST position in the pool.
2. **Are the receivers worse than what it took?** No. WR#24 projects **245** points; TE#24
   projects **148**. The engine repeatedly took the tight end.
3. **Is the probe reading the engine, or something adjacent?** Both. At a mid-draft state in
   every seat, `build_snapshot`'s top candidate was compared against `compute_draft_board`'s own
   first row. **6 of 6 agree** (Tyler Warren / Quinshon Judkins / Colston Loveland / Javonte
   Williams). The instrument voids itself if they ever disagree.

## What this does to #205

#205 reported "every seat fills every starting slot" and read that as evidence the points
deficit was NOT a lineup artifact. **Filling a slot and filling it well are different questions,
and #205 only asked the first.** A seat with two receivers fills its two WR slots and reports
8/8, identically to a sane roster. The 5-11% points deficit is therefore NOT established as the
price of dynasty asset accumulation; a large part of it is the cost of fielding WR2 at 165
points instead of 245.

The asset-ruler result (68/68) is not overturned, but it now carries a question: the asset ruler
is rewarding a roster nobody would field, which is the cross-position comparability question in
#155/#74/#76.

## ROOT CAUSE — traced, and my first hypothesis was WRONG

**CORRECTION, recorded rather than quietly replaced.** The first version of this file said the
count of two receivers was "exactly the number of WR starting slots" and read that as a
positional-need signal saturating at the slot count. **That is wrong.** The seat-1 pick sequence
is `RB TE TE RB TE TE TE RB TE TE TE WR WR QB` — the two receivers arrive at rounds 12 and 13,
after every other position's tail has fallen through. The "2" is a consequence of a 14-round
roster, not a slot cap. Nothing saturates at the slot count.

### What the board actually computes

Read off real rows: `final_score = universal_value + need_bonus + eligibility_bonus`, and
`universal_value = bpa + time_horizon_adj + risk_adj`, where
**`bpa = projected_points − replacement_level(position)`**.

Verified on Jahmyr Gibbs at round 1: bpa 226.25, horizon −1.99 → universal_value 224.26;
need 8.67 → final 232.93. Exact.

### The replacement levels, and the gap they hand out for free

Implied replacement (`projected_points − bpa`) is **constant across every row of a position** at
a given board state — min = max = median over 40 rows each:

| | QB | WR | RB | TE |
|---|---|---|---|---|
| round 1 | 328.6 | **216.2** | 185.6 | **172.7** |

A tight end therefore starts every comparison **43.5 points of bpa ahead** of a receiver with
identical projected points. Measured directly at round 6: George Kittle (TE, 224 proj) scores
**55.53**; Jalen Coker (WR, 223 proj) scores **11.24**. One point of projection apart, five
times the score.

### Why it PROPAGATES — the gap widens as you feed it

Replacement level is derived from the POOL, not from your roster. As the league consumes tight
ends the TE level falls faster than the WR level, so the bias **grows**:

| | TE replacement | WR replacement | gap favouring TE |
|---|---|---|---|
| round 1, I own 0 TEs | 172.7 | 216.2 | **43.5** |
| round 6, I own 3 TEs | 162.6 | 213.7 | **51.1** |
| round 10, I own 6 TEs | 148.4 | 200.6 | **52.2** |

**Drafting six tight ends made the next tight end look better, not worse.** That is a positive
feedback loop, and it is the propagation mechanism the item was asked about.

### Why nothing stops it

`need_bonus` is the only roster-aware term, and it behaves correctly — it reads **0.00** for TE
once the tight-end slot is filled. It simply cannot matter: `NEED_BONUS_MAX = 12.0`, and
`ELIGIBILITY_BONUS_MAX` is deliberately set equal to it. **12 is smaller than 43.5, and smaller
still than 52.2.** The counterweight is capped below the bias it would have to overcome, at
every point in the draft, so roster state can never reorder the board.

That cap is not an oversight — draft_room.py's own header explains it was bounded precisely so
need could not flip a large universal-value gap (#87: need_bonus is a positional GATE, not a
value override). The bound is defensible. The consequence is that **nothing in the system is
able to say "you already own six tight ends."**

### This is what a user sees

Not a simulation artifact. `final_score` IS the presented board order. At round 6 the top four
rows are all tight ends, and the best available receiver sits at **rank 14**.
