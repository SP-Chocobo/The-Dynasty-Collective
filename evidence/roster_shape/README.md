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

## Hypothesis, stated as a hypothesis

The counts are suspiciously exact — **exactly** the number of WR starting slots, never one more.
That is the signature of a positional-need signal that saturates at the slot count and then
stops making receivers competitive at all, combined with a replacement level that makes tight
ends look enormously valuable: TE#24 at 148 sits far below WR#24 at 245, so value-over-
replacement flatters every tight end and starves every receiver. That is exactly the
cross-position VOR question already registered in #155, #74 and #76 — but this is the first time
it has been demonstrated end-to-end on a full draft rather than inferred from a board.

NOT ESTABLISHED. The mechanism above is a reading of the numbers, not a traced cause. Nothing
here identifies the line of code.
