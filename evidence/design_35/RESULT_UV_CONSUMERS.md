# What C′'s `universal_value` shift does at every consumer that reads it

C′ leaves `team_acquisition_value` identical and raises `universal_value` by `stale(p)` at drained
positions. The draft loop is proven indifferent — identical rosters pick for pick, both seasons. These
are the consumers the draft loop does not exercise.

**The shift, measured:** on a drained 2024 `12T_ppr_K_DEF` board, `uv′ − uv` is **QB +13.33** and
**exactly 0.00 at every other position** — one non-negative per-position constant, which is what makes
the table below predictable.

## The consumers, corrected first

I originally named four. That list was wrong in composition and incomplete:

* **`pick_synthesis` context elevation is not a consumer** — it was retired with its flag at `#25`.
  The live `universal_value` read there is the **`pure_value`** decision-path flag.
* **Two were missing:** `draft_strategy`'s positional-forfeit curves, and `draft_battery`'s pre-draft
  reference ruler.

## Results

| consumer | how it reads `uv` | result | why |
|---|---|---|---|
| `draft_strategy` rival-pool ranking (`:278`) | sorts **within** a position | **unaffected** | a per-position constant cannot reorder rows inside that position |
| `draft_strategy` positional-forfeit curves | within-position decay | **unaffected.** Every curve STEP identical; only QB's curve *level* moves by 13.33 | forfeit reads decay, and a constant cancels in a difference |
| `rival_premium` = `final_score − uv` | cross-term | **shifts DOWN by `stale(p)`.** max unchanged at 8.16, min −86.67 → −96.61. **0 rows exceed the 24.0 saturation in either arm** | TAV is unchanged and uv rises, so the premium can only fall — it cannot breach a bound it already satisfies |
| `draft_counterfactual.bpa_row` | argmax, **cross-position** | **same player** (Loveland, TE, uv 123.84) | the shifted position's best never crossed the global best |
| `roster_diagnostics.replacement_level_surplus` | `Σ(uv − level)`, level = rank over the **same** column | **CANCELS EXACTLY.** −18209.43 in both, difference `+0.0000` | the level shifts by the same 13.33 (measured: QB −231.44 → −218.11), so the subtraction removes it |
| `roster_diagnostics.accumulated_value` | `Σ uv` | **moves: +599.85** | nothing subtracts the shift. 599.85 = 45 QB rows × 13.33, exactly |
| `draft_battery` reference ruler | pre-draft board | **unaffected, max ǀuv′ − uvǀ = 0.0** over 674 rows | nothing is drafted, so nothing is drained, so `stale(p)` is 0 everywhere |
| `pick_synthesis` `pure_value` | **cross-position** max and a 2.0 band | **identical in both arms at every state tested — but see the limit below** | |
| `expected_value_of_waiting`, `opportunity_cost` | `uv × survival` | **move**, by `stale(p) × survival` | derived, not measured separately; they are products of a shifted factor |

## The one consumer this did NOT settle

**`pure_value` is exercised but never on a shifted row.** It fires once at 360-drafted (identically in
both arms) so the flag is not dead, but at every state tested — 168, 240, 360 and 480 drafted — **no
QB row reached the top 20 being compared**, so the specific exposure was never touched: a shifted row
becoming the field's `best_uv` when it was not.

There is a structural reason to expect that exposure to be small, and it is worth stating because it
is the same fact from the other side: the shift exists only at a **drained** position, and under C′ the
best remaining player at a drained position has `uv` of **exactly 0.00** — he *is* the replacement. So
a shifted row can hold the field's best `uv` only when nearly everything else priced is negative too.
Not impossible; not reached here.

## What the table means

Every consumer that compares `uv` **within** a position, or subtracts a level derived from the same
column, is exactly unaffected — and two of those (`replacement_level_surplus`, the forfeit curves)
were things I would have guessed wrong without measuring, because the cancellation is not obvious
from the call site.

Everything that **sums** `uv` or **multiplies** it moves, and `accumulated_value` is the concrete case:
+599.85 on one board. It is an observable in `roster_diagnostics`, not an input to a pick, so nothing
downstream of it changes a decision — but a report that quotes it would change, and anyone comparing a
pre-C′ report against a post-C′ one would be comparing two rulers.

`rival_premium` moving **down** is the load-bearing result: it is what feeds the denial ramp and what
`TEAM_SPECIFIC_CAPS` bounds, and C′ can only reduce it. That is the derivation's promise — the reason
C′ restores the caps' exemption while C destroys it — confirmed on a real board rather than argued.

## Provenance

One drained board pair per measurement, built in one process with `dr.board_slot_alternatives` and the
anchor cap toggled, at commit `11fc59b`, on the **fixed** pool recorder. The pre-draft ruler row is the
measurement that exposed the recorder defect (see `install_pool_recorder`'s docstring); it read 13.33
under the defect and 0.0 after the fix. Every other row was measured on drained boards, where the
defect cannot bite because the drafted set is non-empty on every call.
