# Wave 4 — what I re-measured myself, and what I could not

> Pass G's report is a CLAIM. This file is what survived my own checking, run from the repo root
> against the capture's own `league_shape`. Probes: `k_asym.py`, `k_round8.py` (scratchpad).

## REPRODUCED — the round-8 kicker mechanism, to the decimal

G claimed: at 8.04, `Cameron Dicker bpa 12.57 + need_bonus 4.00 = 16.57` ranks a kicker top of
the board, because `NEED_BONUS_PER_DEDICATED_SLOT = 4.0` is applied to a position whose entire
above-replacement spread is about the same size.

Built a drained board (84 players gone, my seven starters filled, **K slot open**) and got the
same three numbers:

```
NEED_BONUS_PER_DEDICATED_SLOT = 4.0

need_bonus by position, K slot open:
  K 4.00 | QB 0.85 | DB/DL/LB 0.67 | TE/WR 0.38 | RB 0.00

Cameron Dicker  K  bpa=12.57  need=4.00  final=16.57   -> rank 10 of 1944
```

`bpa 12.57 / need 4.00 / final 16.57` is G's triple exactly. Mine ranks 10th rather than 1st
because my rivals drain the board greedily instead of running the engine per seat — the
approximation moves the rank, not the mechanism.

**The mechanism, stated as a ratio rather than a rank:** the K slot's `need_bonus` is 4.00
against a best-kicker VOR of 12.57 — **32% of the whole distance from the best kicker to
replacement**. The same 4.00 would be 1.9% of Bijan Robinson's 212.57. A flat per-slot bonus is
only flat in points; in *fraction of the position's own spread* it is worth sixteen times more to
a kicker than to a running back. `#56` forbids a calibrated constant, and this is what an
underived one costs.

**One correction to G.** G wrote "the whole K1–K12 spread is ~12 points". The whole *position*
spans 127.08 points across 55 kickers. The ~12 figure is the best kicker's VOR above replacement,
which is the number that matters here — so G's argument holds, but the sentence as written
understates the position's range by tenfold.

## REPRODUCED — `displacement_adj` is positive, and non-zero on an empty roster

Third independent reproduction of W1-01, plus W2-06, on one board:

```
EMPTY ROSTER, displacement_adj by position:
  DB  -28.28 (393 rows)   DL  -32.87 (219 rows)   WR  0.00 .. +79.44 (433 rows)
  K / LB / QB / RB / TE   0.00
```

`displacement_adjustments`' docstring says "`<= 0.0, never positive`" and "Zero on an empty
roster". Both false on the owner's own shape, on a board with no picks in it at all.

## REPRODUCED — the deduction asymmetry, at a full pool

With my slots filled, the per-position deduction is a constant per position:

```
K -12.57 | QB -17.99 | DB -28.28 | RB -32.81 | DL -32.87 | TE -46.03 | LB 0.00 | WR 0.00..+79.44
```

K is deducted the least of any filled position — a quarter of what a tight end loses. At a full
pool this is invisible, because `bpa` still spans ±200 and dominates. **It becomes the ranking
signal only once `bpa` collapses board-wide**, which is the drained-board state G measured at
pick 125 of 300 and which my cheap probe does not create. So: the asymmetry is confirmed, the
takeover that follows from it is **G's measurement, not yet mine**. Confirming it needs the
1008-second full draft, which is the honest next step and is not run here.

## CONFIRMED by reading — four structural claims

1. **Two engine constants are derived from a bound the engine violates.**
   `TEAM_SPECIFIC_CAPS = (NEED_BONUS_MAX, ELIGIBILITY_BONUS_MAX, DEPTH_EXPOSURE_MAX)` = (12,12,12);
   `NECESSITY_DENIAL_SATURATION = 36`, `CONTEXT_ELEVATED_THRESHOLD = 12`,
   `NECESSITY_DENIAL_CEILING = 36 × (10/12)`. The comment above the tuple says `#216`'s fourth
   term is **"deliberately NOT here: it is non-positive by construction … so it cannot raise the
   sum these caps bound."** That premise is the one measured at +79.44, and TAV − UV reaches
   87.82 — 2.4× the bound. The same comment block says the tuple exists precisely "so a fourth
   team-specific term moves it automatically instead of silently re-flattening the ramp the way
   the third did." The mechanism built to prevent this was hand-exempted on the false premise.

2. **The chairs are told they have a number the evidence block refuses them.** All three system
   prompts (`pick_debate.py` L176–177, L232–233) list `survival_probability`, `opportunity_cost`
   and `expected_value_of_waiting` among "real, already-computed numbers"; L252's worked example
   is `"19% survival with a QB run detected"`. L444–445 tells the same model the survival "is
   WITHHELD … do not estimate one yourself." An invitation to fabricate, with a template.

3. **`_picks_by_mode` asserts what its docstring says it reports.** `draft_simulation.py:87` —
   "How many picks of this trajectory each valuation **actually produced** … **Reported rather
   than assumed**" — computes `(UPSIDE_MODE_DEFAULT_ROUND − 1) × num_teams` and never inspects a
   pick. It is stamped into every trajectory's config at L212. And it is wrong for the reason it
   cannot see: the round off-by-one moves the real flip one pick later, so an instrument that
   asserts instead of counting cannot detect the defect that falsifies its assertion.

4. **Neither production surface passes `mode`.** `app.py:5024` (Mock Draft) and `app.py:5381`
   (Draft Room) both call `build_snapshot` without it. `draft_battery.py:140` already records
   that "a human board never reaches [upside] — which makes the simulation the ONLY place its
   behaviour is observable at all." The inverse is the finding: the battery's arms run
   `mode="auto"`, so a large share of the certification evidence is about a mode production never
   runs, while the late-round *balanced* rounds production does run are covered by no arm
   (`12T_ppr_mode_balanced` is `len(roster_positions)` rounds — 14, not 25).

5. `UPSIDE_GROWTH_WEIGHT = 0.5` and `TIME_HORIZON_CLAMP = (-10.0, 10.0)` confirmed:
   `upside_score` adds `0.5 × (proj3yr_pct − season_pct)` — a **percentile** difference, up to
   ±50 — to `bpa`, raw points, **unclamped**, where `time_horizon_adj` reads the same percentile
   pair and clamps to ±10.
