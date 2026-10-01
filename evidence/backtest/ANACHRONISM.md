# The backtest drafted players who did not exist yet

**Status: found, mechanism traced, guard shipped, every affected number being re-measured.**
Written before the re-runs finished so the thread survives a container reclaim.

## What was wrong

`run_backtest_grade` drafts on a finished season's projections and scores on that season's real
outcomes. Both arms drew from `run_roster_proof.scoreable_pool`. That pool contained, and priced
near the top of the board, **players who were not in the league in the season being drafted.**

Measured in the `12T_ppr_K_DEF` pool:

| season | pool | players with NO projection that season | highest such price |
|---|---:|---:|---:|
| 2023 | 703 | **133** | 340.0 |
| 2024 | 674 | **101** | 319.0 |

The 2023 list, by price: Maye 340, Daniels 334, C. Williams 324, **Dart 319**, Nix 312, Shough
296, Jeanty 293, Ward 264, **Bowers 259**, Hampton 254. Every one a rookie from 2024, 2025 or
2026. Every one realizes exactly **0.0** in 2023, because he has no stat line that year.

The engine's 2023 seat-1 roster spent **round 2 on Brock Bowers and round 8 on Jaxson Dart.**

## The mechanism — a fallback working exactly as designed

`draft_room.build_available_pool` (draft_room.py:1456):

```python
sleeper_points = scored if scored != 0 else None
```

A zero-scoring projection is treated as NO projection — which is correct for a live draft, where
zero means the vendor has nothing to say. A later rookie's row in an earlier season's capture is
all zeros, so it scores to exactly 0.0, so `sleeper_points` goes `None`, so `use_season` does not
fire, and the board prices him from the **2026 Draft Sharks export** instead. That export ranks
him as the prospect he became. He lands at the top of a board for a season he never played in.

Nothing crashed. Nothing logged. The instrument returned a plausible number about a different
question — the exact failure mode `.claude/skills/engine-measurement` says to fear.

## What it invalidates, and what survives

- **INVALID: every absolute engine-vs-field grade from this instrument.** The 2023 holdout's
  "engine loses 0/12 by ~500 points" was measured on rosters carrying two guaranteed zeros.
- **INVALID: my own claim that "2024 is clean and only 2023 is confounded."** It was drawn from
  one seat's roster. 2024 carries 101 ghosts; that seat simply did not draft one.
- **SURVIVES, conditionally: the paired streaming delta.** Same season, same pool, same seats,
  one toggle — the contamination is present identically in both terms. It is the reason the
  direction of the `#30` result was never in doubt. The *magnitude* is still being re-measured,
  because the optimizer is non-linear and identical contamination does not guarantee an
  identical effect on two different rosters.
- **SURVIVES: `#18`.** It never drafted; it measured projection-vs-outcome correlation per
  position on players who had both.

## The guard

`run_backtest_grade.period_correct_pool` drops any pool member whose **drafted-season** projection
scores to zero — exactly the board's own test, so the guard cannot drift from the fallback it
guards. It runs before the draft, applies to every arm and every seat identically, and the run
**refuses to proceed** if it drops nothing (a guard that does not fire on a capture that post-dates
the drafted season is a guard that is not wired in).

**This is not hindsight.** It uses only the drafted season's own published projections, never its
outcomes. A drafter in 2023 could not have drafted Brock Bowers.

Tests: `test_backtest_anachronism.py` (7). One of them pins `draft_room`'s zero test against the
real source, so if that fallback ever changes the guard fails loudly instead of silently
mismatching.

`evidence/kdst_streaming/counterfactual_cost.py` got the narrower version of the same fix: the
counterfactual swap-in is now chosen from period-correct players only. Its own docstring records
the residue it cannot remove.

## Still open

- Re-run of `#30`'s streaming arm on **2024** and on the **2023 holdout**, both under the guard.
- Every number in `STREAMING_ARM_RESULT.md` and `evidence/backtest/README.md` is marked
  superseded until those land.
- `run_smoke_seats` is untouched by this: it drafts and grades on the SAME 2026 capture, so
  "a player the season did not project" is not a category that exists there.

## The residual — WITHDRAWN, it was the second half of the defect

> Everything in this section as first written was a correct measurement used to answer the
> wrong question, and the conclusion drawn from it was wrong. It is kept in full below the
> correction, because the mistake is more instructive than the fix.

I measured the ghosts on the **opening** board (5 of 72 narrowed candidates, first non-ghost at
rank 0) and concluded the board-side contamination was small. It is not small, and the opening
board is the one place it is guaranteed to look harmless.

**Nobody can draft a ghost** — both arms filter on `points` — so a ghost is never removed from
the board. They ACCUMULATE. Measured on a drained round-16 board: **all 26 remaining candidates
were ghosts** (McMillan, Egbuka, Burden, Tate, Concepcion, Jeanty, Hampton, Loveland, Love,
Warren, Skattebo, Judkins). The engine walked past every one and took whatever non-ghost
survived the narrow — which is how a roster already stopped at its DEF ceiling still finished
with a defense in round 16.

**The fix needs no production plumbing.** The grader now builds the board from a period-correct
`players_db`. Measured: that removes exactly the 101 ghosts from the 1181-row 2024 board and
loses **zero** legitimate rows. 435 survivors' `bpa` moves, which is the point and not a side
effect — a replacement level should never have been set by players who did not exist that year.
The realized ruler keeps the FULL db, because eligibility is a fact about the player rather
than about the season being drafted. Two AST tests pin both halves.

**Every guarded number measured before this landed is superseded**, including the base −641.0,
the streaming +258.8, and the fieldability +423.9 / +237.2. They were all measured on an engine
whose late-round candidate window was full of undraftable phantoms.

### The original section, kept

## The residual the guard does NOT remove, measured

`period_correct_pool` filters `points` — the field's pool and ranking, and the legality filter
`run_smoke_seats.draft` applies to the engine's candidates. It does **not** filter the engine's
BOARD. `pick_synthesis.build_snapshot` builds the board from the full universe, so the ghosts are
still present in it, still priced off the 2026 export, and still enter `replacement_levels`'
VOR denominator and the cliff/run/denial context.

**Measured on the opening 2024 board: 5 of 72 narrowed candidates are ghosts (7%), and the first
non-ghost sits at rank 0** — the top of the board is clean, and the engine's own
`if str(c.player_id) in points` filter walks past the rest. So the asymmetry is real but small,
and it is **not** the explanation for the engine's deficit. Stated rather than assumed, because a
7% contamination that happened to sit at the top would have been the whole answer.

Removing it properly needs `demand_picks` threaded through `build_snapshot` to all three of its
picks-consumers (`compute_draft_board`, the `num_teams` derivation, and `replacement_ranks`).
That is production plumbing for a measurement, so it goes to the owner as a decision (`#184`)
rather than into a repair commit. Until then this is a stated limit on the absolute grade, and
it applies IDENTICALLY to every arm, so no paired comparison is affected.

## A THIRD anachronism the guard does not touch, named before anyone quotes a 2023 number

`period_correct_pool` removes players the drafted season never projected. For the players it
KEEPS, one input is still 2026-vintage: `time_horizon_adj` is built from the vendor's THREE-YEAR
outlook, and a player priced through the `trade_value` fallback carries a 2026 composite. So in
a 2023 draft the engine's multi-year opinion is a ranking formed after the season was played.

`bpa` is not affected — it is VOR in the drafted season's own projected points, which is why the
top of the board is period-correct and why the fix above was worth ~540 a seat.

Two things follow, and both are stated rather than assumed:

- **The further back the backtest, the larger this residual.** 2023 is two more years of
  hindsight than 2024, which is a candidate explanation for 2023 grading harder — and only a
  candidate, because it has not been measured on the corrected board.
- **`run_backtest_grade --redraft` neutralises it**, since `time_horizon_adj` is gated on
  `settings.type == 2`. That arm was run once on the CONTAMINATED board and came out worse; it
  has not been re-run since, so no conclusion from it stands.

The residual is identical across arms, so every PAIRED figure survives it. It is the absolute
grades that carry it.
