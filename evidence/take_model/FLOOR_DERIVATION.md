# #21: the floor cannot be derived while #50 is open, and the ruling's own remedy makes it worse

All figures re-measured on HEAD through the exact path `evidence/take_mass/mass_per_opponent.py`
uses — the real Fourth-and-Forever capture, season sums, `SLEEPER_BASIS_SEASON_SUM`.

## The register's blocker numbers are stale, and its implied fix points the wrong way

`#26` narrowed pool admission at `264e063`, after the take-mass evidence was recorded.

| | recorded 2026-09-16 | HEAD |
|---|---|---|
| board rows | 1,119 | **970** |
| priced rows | 481 | **481** (unchanged) |
| unpriced rows | **638** | **489** |
| unpriced floor mass | 12.76 | **9.78** |
| rank-model total mass | 23.49 | **20.51** |
| unpriced share | 0.543 | **0.477** |

The register row reads: *"`0.02` was derived against a rank table whose leader was 0.55 while the
value model's leader weighs 1.0 (`#75` unit drift)."* That is true, and it reads as an instruction
to rescale by `1/0.55`. **Measured, that makes the defect worse:**

| candidate | per-row `w` | block | block ÷ P | block's share of one pick |
|---|---|---|---|---|
| today | 0.020000 | 9.780 | 1.857 | 0.650 |
| **rescale to the leader** (0.02 ÷ 0.55) | 0.036364 | 17.782 | **3.377** | **0.772** |
| indifference (`P / n_priced`) | 0.010948 | 5.354 | 1.017 | 0.504 |

with `P = 5.2660` (value-model priced mass), `n_priced = 481`, `n_unpriced = 489`, leader
`final_score` 265.06, `board_contention_scale` σ = 38.0899.

**The drift is in the tail, not the leader.** Under the rank model the priced tail past rank 5 is
476 rows × 0.02 = 9.52, flat. Under the value model the same rows decay exponentially over a board
13.1σ wide and collapse to ≈2.13. The block never moved; everything under it shrank.

## What `0.02` actually meant, and what it would come to mean

**Under the rank model it was an EQUALITY, not a level.** `RANK_TAKE_PROBABILITY` names five ranks;
`.get(rank, FLOOR)` gives every other priced row exactly 0.02. So an unpriced row weighed precisely
what a priced row the model also could not discriminate weighed — 476 of 481 of them. "Unpriced"
and "priced but undiscriminated" were indistinguishable states getting indistinguishable numbers.

**Under the value model every priced row IS discriminated**, and the same literal 0.02 becomes a
ranked claim. Measured: **only 36 of 481 priced rows weigh ≥ 0.02.** Wiring the value model without
touching the floor asserts that a row nobody could price is likelier to be taken than the 37th-best
player on the opponent's board, 445 times over.

So the `#187` breach is *created by wiring the value model*, not by the floor as it stands. That is
the strongest reason the floor cannot ride along unchanged — and it is visible in two lines,
`draft_strategy.py:646-647`:

```python
    if score is None:
        return RANK_TAKE_PROBABILITY_FLOOR
```

A function whose docstring begins "One priced row's…" handling an unpriced row by returning a
rank-model constant, and turning `None` into `0.02` at a seam where no label travels with it. The
same module answers the same absence correctly thirty lines earlier — `board_contention_scale`
returns *"None -- not a substituted default"*, citing `#187` by name.

## THE BLOCKER: the board makes two incompatible claims about these 489 rows

- **ORDER LAST** — `compute_draft_board` sorts unpriced rows last. If the take model is to agree
  with the board's own ordering (`#126`), an unpriced row cannot outweigh the worst priced row.
  That bound evaluates to `exp((−233.87 − 265.06)/38.09) ≈ 2.05e-06` — a block share of 0.0002,
  i.e. *"unpriced means safe"*, which the owner ruled against on evidence (31 of 301 resolved picks
  took a player off the picking team's priced board).
- **`ABSENCE_NO_INPUT`** — `draft_room.py` classifies all 489 as *unknown, not bad*, and sets their
  confidence to `None` rather than 0 because *"no anchor produced anything, so there is no number
  to grade"*. That reading gives indifference, `w = P / n_priced`.

`draft_room.py:632-637` already names this, in the code:

> *"SO THE FINDING OUTLIVES THE REPAIR: ORDER LAST is applied to a population that is entirely
> 'unknown, not bad', containing none of the evidence that would justify it. Whether that is the
> right ordering is a valuation question (#50), not a disclosure one."*

**Deriving the floor while #50 is open means picking one of two contradictory board conventions by
arithmetic — which is choosing, not deriving, and `#56` forbids exactly that.** #21 is downstream
of #50. That is the finding.

## The candidate that survives, recorded but NOT recommended yet

**Indifference over the board**, `w = P / n_priced`. An unpriced row carries no valuation, so the
model has no basis for ranking it above or below the average row; the least-committal assignment
gives every row `1/N`, and solving `w/(P + n_u·w) = 1/N` gives `w = P/n_priced` exactly. Measured:
0.010948, block share 0.504.

Its virtues: it introduces **no constant** — it is a per-board runtime statistic, the same species
of object `board_contention_scale` already argues for in this module — and it never reads a league
outcome, so it cannot be a calibration.

Its honest limit, stated first: it still puts **half** a pick on rows the engine could not price,
against 11.2% measured in real drafts (31 of 276). **It is a maximum-entropy upper bound, and a
bound is not a threshold (#56).** It is not ready to wire, and it cannot be until #50 settles
whether ORDER LAST is right.

## What must NOT be done

- **Do not rescale to the leader.** Measured: 0.650 → 0.772.
- **Do not collapse the block to one row.** Already declined with arithmetic at
  `POST_AUDIT_PLAN.md:11858`: *"turns a 6.9x overshoot into a ~25x undershoot"*.
- **Do not wire the value model behind a flag.** `test_take_model_seam.py:87` forbids it, and the
  seam's own docstring says *"There is exactly ONE take model in production and this is its only
  home (#126)"*. The value model replaces the body or it does not land.
- **Do not cite the 638 / 23.49 / 2.0–3.4× figures again.** They describe a board that `#26`
  retired. Re-measure first; `mass_per_opponent.py` regenerates them.
