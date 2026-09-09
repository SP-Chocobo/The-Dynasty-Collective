# WITHDRAWAL (17th): "the narrowing selects the tight ends" was a FIXTURE ARTIFACT

And the trace that withdrew it found the boundary the whole shape sits on.

---

## What is withdrawn

`PHASE3_D3_GATE_FAILED.md` closed with:

> *"At picks 193/205/229/241/281 `candidates[0]` reproduces the recorded pick 5 of 5 and is the
> board's top row 0 of 5 ... The tight ends are selected by the narrowing in `pick_synthesis`,
> not by the board's price. That is B4, and it is where the phenomenon lives."*

**Every word of the conclusion is withdrawn.** The `candidates[0]` half was right. The "board's
top row 0 of 5" half was measured against a board production never built.

### The artifact

My probe called `compute_draft_board` with picks shaped `{player_id, roster_id}`. Production
passes `{pick_no, round, roster_id, player_id}`. `mode="auto"` resolves upside-vs-balanced from
the current round, and the round comes off the picks. So my board ran **balanced** while
production's ran **upside**, and the two disagree about the whole top of the board.

Isolated directly, same process, one thing toggled (`phase4_picks_shape_check.py`):

| picks shape | rows | priced | top 5 by final_score |
|---|---|---|---|
| `{player_id, roster_id}` | 915 | 267 | WR −78.71, WR −80.26, WR −85.36, WR −87.27, WR −88.76 |
| `{pick_no, round, roster_id, player_id}` | 915 | 267 | **TE −86.36**, WR −86.57, WR −87.65, TE −88.98, WR −89.31 |

Forcing the mode explicitly gives identical results from both shapes — so the shape matters
*only* through round detection:

```
THIN  mode=balanced  top row = WR -78.71 Makai Lemon      FULL  mode=balanced  top row = WR -78.71
THIN  mode=upside    top row = TE -86.36 Elijah Higgins   FULL  mode=upside    top row = TE -86.36
```

### What is true instead

Traced through production's own `narrow_candidates` (spy on the real call,
`phase4_narrowing_trace.py`): at pick 205 the board hands it 915 rows, `top_n=5`,
`position_depth={...all 1}`, and `fills_required_slot` is **False on every row** — the
feasibility backstop does not bind at any of the five picks. The candidate list is:

| # | pos | final_score | entered via |
|---|---|---|---|
| 1 | **TE** | −86.36 | top_n slice |
| 2 | WR | −86.57 | top_n slice |
| 3 | WR | −87.65 | top_n slice |
| 4 | TE | −88.98 | top_n slice |
| 5 | WR | −89.31 | top_n slice |
| 6 | RB | −105.12 | best-at-position |
| 7 | QB | (unpriced) | best-at-position |

`candidates[0]` **is** the board's top row by `final_score`. `narrow_candidates` is additive by
contract — top_n plus best-at-position plus the user's flagged player — and it removed nothing,
overrode nothing, and promoted nothing. **`narrow_candidates` is exonerated.** So is
`_board_order`, and so is the feasibility backstop.

The owner's distinction holds and lands on the right side: *"board rank isn't selection rank"*
is still true in general (`_board_order` is a second ordering authority), but it **did not fire
here**. *"Selection rank is wrong"* was never earned and is now unnecessary — the board's price
picked the tight end.

### The fixture rule this cost

Added to the engine-measurement skill: **a probe that hand-builds production's inputs must
build them in production's own SHAPE.** A missing key is not a missing value here — it silently
selects a different valuation mode. This is the same family as the wrong-universe error (#201)
and the wrong-call error (#222 clause 2): the instrument was fine, the INPUT was reconstructed.

---

## What the trace found instead: the mode boundary

`UPSIDE_MODE_DEFAULT_ROUND = 15`. `compute_draft_board`'s upside branch is explicit about what
it does, in its own comment:

> *"upside scoring zeroes every team-specific term (see the layer identity above), so this
> branch has no roster awareness of any kind -- and mode='auto' enters it at
> UPSIDE_MODE_DEFAULT_ROUND, which is exactly when the last starting slots are still open."*

`need_bonus`, `eligibility_bonus`, `depth_exposure` and `displacement_adj` are all 0.0 there;
`depth_exposure` is never even computed. Confirmed on the ladder re-run with production-shaped
picks: rungs at rounds 10/11/13 carry a real `displacement_adj` (−51.73, −55.92, −91.92); rungs
at rounds 15/16/18/20 carry **0.00**, with no level consumed at all.

In a 26-round startup, upside mode owns **rounds 15–26 — 144 of 312 picks, 46% of the draft.**

Split the FINDING_05 draft at that boundary — a line taken from the source, not chosen to fit:

| | picks | QB | RB | WR | **TE** |
|---|---|---|---|---|---|
| rounds 1–14, **balanced** | 168 | 19.0% | 26.2% | 39.3% | **15.5%** |
| rounds 15–26, **upside** | 144 | **0.0%** | 27.8% | 20.1% | **52.1%** |
| twelve real managers, whole draft | 312 | 20.0% | 27.4% | 37.1% | **15.5%** |

**In balanced mode the engine draws tight ends at 15.5% — the humans' number, to the tenth.**
The entire deviation lives in the 46% of the draft where every roster-aware term is switched
off by design. The zero QBs in that window are the same fact: QB has a startable floor, the
floor stops clearing, the position goes unpriced, and unpriced rows sort last.

### Stated at the strength it has earned, and no further

This is a **correlation with a documented mechanism**, on **one draft**. It is not proof. The
mechanism is not hidden and not a bug: upside mode is a deliberate, documented alternative
valuation, and `feasibility_first` was added to it precisely because it has no roster awareness
("the battery caught two unfillable rosters in explicit upside mode against zero in balanced").

The test is an ablation, and it is a MEASUREMENT, not an engine change: one arm, `mode="balanced"`
forced for all 26 rounds, everything else identical, same fixture, same universe, same seats.
**Running now** as `run_ff_draft_balanced.py`. Pre-registered here, before the result:

- **If the TE share in rounds 15–26 collapses toward the balanced-mode 15.5%**, the mode boundary
  is causally active and #216 is a question about *when upside mode should engage*, not about
  the anchor, the optimizer, the displacement term, or the narrowing — all four now exonerated.
- **If it does not collapse**, the boundary is a coincidence of this draft and the mode
  hypothesis dies with it, like the four before it.

Either way, **no engine modification.** A live question that follows regardless, and is #56-shaped:
`UPSIDE_MODE_DEFAULT_ROUND` is a fixed ROUND INDEX, so it means 26% of a 19-round draft and 46%
of this 26-round one. The same constant buys a different fraction of the draft in every format.
That is a derivation question whether or not the ablation moves.
