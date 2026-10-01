# G9's ruler, re-scored: the reversal is NOT the contamination

`run_216_asset_ruler_probe.py`, run against the ALREADY-RECORDED rosters in
`evidence/roster_shape/fix_216/`. No draft was re-run. The harness proves itself by reproducing
every recorded `cdme_total_value` and `cdme_starter_value` exactly — **12 of 12 arms in each
format, "yes" in every row of the table.** A run that could not reproduce them exits non-zero
and reports nothing.

## The question

G9a is a sign test on `cdme.total_value` — the pre-draft board's `universal_value` summed over
the WHOLE finished roster. `run_roster_proof` names a contamination in that sum
(`CDME_TOTAL_CONTAMINATION`): it counts a below-replacement player as a LIABILITY you carry
rather than as someone you would simply drop. #216's fix changes exactly the population that
contamination is about — the bench goes from surplus scarce-position players (positive
`universal_value`) to near-lineup receivers (negative). So the gate's verdict and the
contamination are not independent, and the obvious hypothesis is that the two superflex
reversals are a statement about the SUM rather than about the fix.

**That hypothesis is wrong, and this is the measurement that kills it.**

## The three sets, same `universal_value`, same rosters

| set | what it sums |
|---|---|
| `total` | every drafted player, negatives included — G9's ruler as pre-registered |
| `floored` | every drafted player, each contribution floored at 0.0 — the reserved reading |
| `starter` | the optimal lineup only — what the roster FIELDS |

Engine seat, BASE_ON -> FIX_ON:

| format | seat | total | floored | starter |
|---|---|---|---|---|
| 12T_ppr | 1 | 408.7 -> 392.1 (−17) | 719.5 -> 634.5 (**−85**) | 333.7 -> 632.4 (**+299**) |
| 12T_ppr | 6 | 307.6 -> 317.0 (+9) | 645.5 -> 580.4 (**−65**) | 238.9 -> 578.9 (**+340**) |
| 12T_ppr | 12 | 209.7 -> 244.2 (+35) | 564.7 -> 526.6 (**−38**) | 191.1 -> 521.8 (**+331**) |
| 12T_ppr_SF | 1 | 858.0 -> 576.5 (−281) | 1046.8 -> 888.6 (**−158**) | 757.2 -> 877.6 (**+120**) |
| 12T_ppr_SF | 6 | 809.4 -> 497.3 (−312) | 990.4 -> 832.6 (**−158**) | 663.5 -> 823.0 (**+160**) |
| 12T_ppr_SF | 12 | 739.0 -> 418.8 (−320) | 930.5 -> 732.5 (**−198**) | 557.7 -> 724.2 (**+167**) |

## What this settles and what it does not

**Settles:** flooring does not rescue the fix. Owned POSITIVE asset falls in 6 of 6 seats,
−38 to −198. The loss is real, not an artifact of negatives being counted as liabilities. My
own hypothesis going in was that it was the artifact; the measurement contradicted it and the
measurement wins. Anyone tempted to re-derive "the ruler is just contaminated" should stop here.

**Sharpens:** the trade is now stated without the confound. The fix exchanges **−38 … −198
owned positive asset for +120 … +340 fielded asset**, in every seat of both formats, with no
seat moving the wrong way on either quantity. The pre-fix engine was accumulating positive-VOR
players it could not start; the fixed engine fields them instead.

**Does not settle:** which of those two an owner should want. That is the exchange rate, it is
#50, and it is the owner's. This instrument deliberately emits no verdict and re-gates nothing —
G9a still reads FAILED on its pre-registered ruler, and this file does not change that.

**A caveat on `starter` that must travel with it.** Summing an asset LEVEL across a starting
lineup is the same category error #211 records in the battery, and `run_roster_proof`'s own
`COMPARE_ON` comment argues against reading `cdme.starter_value` as a virtue (it partly measures
who is forced to start the fewest negatives). It is reported here because the question asked is
where the value went, not which roster is better; the answer "out of the bench and into the
lineup" is visible under every one of the three sets.
