# Mutation results for the rewritten over-correction guards (#221)

Five mutations, one at a time, each in the OVER-CORRECTED direction the guards exist to catch.
Harness: `run.py` + `mutations.json` — backup named after its target, pattern verified present
BEFORE, file compared byte-for-byte AFTER, patterns in JSON and never in a shell heredoc (#215).

| # | mutation | verdict | caught by |
|---|---|---|---|
| M1 | blanket anti-tight-end rule (`TE` adjustment forced to −200) | **CAUGHT** | surplus ordering (399/8255 inverted) + named McBride case (rank 137 vs 34 contenders) |
| M2b | `depth_exposure` made per-CANDIDATE | **CAUGHT** | same-position roster terms (38 distinct sums at QB, must be 1) |
| M2c | `need_bonus` made per-CANDIDATE | **CAUGHT** | same-position roster terms (38 distinct sums at QB) |
| M3 | "drafts strictly to slot counts": refuse anyone whose dedicated slots are full | **CAUGHT** | all three, plus the pre-existing elite-flex guard |
| M4 | the anchor correction never reaches the board | **CAUGHT** | surplus ordering — **in the opposite direction**: CeeDee Lamb (surplus 111.7) below Trey McBride (84.6), which is #216's original defect |

M4 is the one worth reading twice. The same guard that would fail on a blanket anti-TE rule also
fails when the correction is switched OFF, and names the receiver-below-tight-end inversion that
opened the item. A guard that only failed in one direction would be a positional rule wearing a
test's clothing.

## A no-op mutation, recorded rather than quietly fixed

M2b and M2c first read `row.get("projected_points")` inside `score_row` and both SURVIVED. The
column does not exist there: `projected_points` is assigned to `scored` AFTER `pool.apply(score_row)`
returns, and the column score_row sees is `_points`. `float(None or 0.0) % 7.0` is `0.0`, so both
mutations added exactly nothing and reported OK.

That is the second no-op patch of this pass (the first zeroed a key nothing read), and it is the
same lesson both times: **a mutation that does not change the answer proves nothing about the test,
and it does not announce itself.** The check that caught it was dumping the board's own values
under the mutation and finding them byte-identical to the clean run — not reading the diff.
