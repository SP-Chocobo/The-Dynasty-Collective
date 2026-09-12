# ⛔ "The horizon layer goes dark for the last 6 rounds" — WITHDRAWN AS STATED, AND RELOCATED

**29th withdrawal, 2026-09-12.** I reported that the draft-horizon layer stops producing a
replacement floor after round 10 and framed it as a property of the engine's endgame. It is
not a property of the engine. It is a property of **one pricing path**, and the path that shows
it is the Mock Draft, not the live Draft Room.

Evidence: `carried_rate_probe.py`, artifact `CARRIED_RATE_PROBE.json`.

## The cut

Three cells. **Same league, same 180-pick control board, same code, one process.** The pick
stream is held fixed across all three, so the pricing path is the single variable.

```
12T_ppr_SF   DRAFT ROOM pricing   priced 481 -> 301   3 positions measurable at EVERY sample
                                                      floors placed 4/9 at every sample
12T_ppr_SF   MOCK DRAFT pricing   priced 256 ->  86   measurable 3 -> 2 -> 1 -> 0 by pick 108
                                                      floors placed 0/9 from pick 108 on
```

**Pick 108 of 180 is round 10 of 15 — the last six rounds.** The figure I published reproduces
exactly, and it reproduces only on the Mock Draft's pricing.

## The cause: `#180`'s repair reached one of four live call sites

`sleeper_projections` is the per-player season stat line that lets the league's own scoring
reach a price (`#180`/`#192`). Production builds a board at four live sites and passes it at one:

| site | passes `sleeper_projections` |
|---|---|
| `app.py:5365` — the live Draft Room | **yes** |
| `app.py:5014` — the Mock Draft | no |
| `app.py:4959` — editing an earlier pick | no |
| `draft_room.py:3491` — `simulate_opponent_picks` | no |

`pick_synthesis.build_snapshot`'s own comment records the reasoning: *"Passing None keeps the
previous behaviour exactly, which is what every offline caller and every test does."* Three of
these are not offline callers. They are live surfaces a person drafts against.

The horizon estimator needs `2 x demand` **priced** rows at a position. Dropping from 481 priced
to 256 is what takes it under that bar, and the draft then finishes the job. Nothing about the
estimator's arithmetic is involved.

**The projections are league-independent.** `sleeper_client.get_season_projections(season)`
returns `player_id -> {stat_category: season total}` and takes no league; scoring is applied
separately from `league["scoring_settings"]`. So the dict the Draft Room already holds is valid,
unchanged, at all four sites. The repair is wiring, not a new quantity.

## What SURVIVES the withdrawal

**1. Superflex QB is dark from pick 0, in every cell, on the live Draft Room path.** Demand 22
needs 44 priced rows; the board has 42 with projections and 39 without. QB's bench appetite is
imputed from the RB/TE/WR mean for the entire draft, in production, and nothing records it.
This is untouched by the withdrawal and is the finding worth carrying.

**2. A real dark regime exists, and it is one sample wide.** Fourth and Forever (26 rounds, 312
picks) on Draft Room pricing degrades from 3 measurable positions to 2 at pick 216 and goes
fully dark at pick **312 — the final pick of the draft**. That is the honest scope of "the
horizon goes dark": the last pick of a 26-round league, not the last six rounds of a 15-round one.

**3. What does NOT survive — a claim I made in `93aca83`'s commit message and corrected the
same day, before any code was written.** That message says *"the all-or-nothing collapse: one
measurable position still cannot place its own floor."* **That is false**, and this document's
own artifact is what refutes it:

```
F&F picks 216   live-measurable [TE, WR]   floors placed: RB, TE, WR
F&F picks 240   live-measurable [TE, WR]   floors placed: RB, TE, WR
F&F picks 300   live-measurable [TE, WR]   floors placed: QB, RB, TE, WR
F&F picks 312   live-measurable []         floors placed: none
```

`positional_bench_appetite` already degrades per position: a position that has fallen under its
own bar takes the mean rate of the ones still measurable. The only full collapse is the
`if not rates` branch, which requires ZERO measurable positions — and that branch is `#62`'s
deliberate fix, because with nothing measured there is no mean to impute FROM, and its
predecessor returned `0.0`, asserting "no position is ever benched."

The owner ruled "wiring + per-position degrade" on that false description. With the second half
dissolved, the repair is the wiring alone. The one true collapse state is the final pick of a
26-round draft, and the only thing that would place a floor there is the carried curve.

## The owner's objection, answered on measurement

> *"a locked curve feels like raw BPA with a different name"*

Correct about the thing it describes, and it does not describe the proposal. Three arms were run
so the objection had something to be true or false about:

```
A  STATUS QUO   live measurement only; all-or-nothing collapse to None
B  HYBRID       live per position where available; opening-board rate carried where dark
C  LOCKED       opening-board rates always, never re-measured   <- what the objection describes
```

`|B - C|`, over the position-samples where live measurement exists:

| cell | samples | differ | mean | max |
|---|---|---|---|---|
| 12T_ppr_SF Draft Room | 64 | 56% | 2.59 | **19.73** |
| Fourth and Forever | 80 | 89% | 4.57 | **15.73** |
| 12T_ppr_SF Mock Draft | 36 | 50% | 4.22 | **33.00** |

B and C are different numbers in half to nine-tenths of samples, by as much as 33 points of
horizon floor. **The hybrid is not the locked curve.** Live re-measurement keeps moving the
floor for the whole draft.

**But the better answer is that the carry mostly stops being needed.** With the wiring fixed,
the carry fires on superflex QB and on the final pick of a 26-round draft. There is no long
locked stretch to be BPA-with-a-different-name IN.

## What this does NOT establish

- **That the wiring fix is sufficient for every league.** Three cells were run. A shallower
  player universe, a deeper roster, or a league with more teams can still take a position under
  the bar; the mechanism is `2 x demand` priced rows, and nothing here bounds that in general.
- **Anything about the trending term.** The residual block in the artifact compares observed
  positional picks against the BENCH-appetite share, and most early picks are STARTER picks, so
  it conflates the two halves of remaining demand. Its numbers are recorded and should not be
  read as a signal measurement. The instrument that would answer it compares observed picks
  against `remaining_starter_demand` + `estimated_bench_demand` together.
- **That the control board resembles an engine-driven one.** The stream is control-only by
  design — the question was how the ESTIMATOR responds to a board, not who picked.
