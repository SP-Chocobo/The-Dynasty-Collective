# `#29` — the VDS battery, read

36 arms, 32 effective, **76 findings**, 24166.5s (6h43m), at `04bccb5`.
Report: `evidence/batteries/VDS_2026-09-26_varied_drafting_strategy_04bccb5.json`.
Gate: `GATE_FOR_VDS.md` (+ its amendment). Reading bars: `PREREGISTRATION_VDS_READING.md`,
fixed before either follow-up instrument was built.

**First, the flag that made the previous run worthless was checked before anything was read:**
`weekly_projection_weeks: 18`, `streaming_floor_exercised: true`. `#30` fired.

---

## 1. The findings, once they are counted correctly

73 of the 76 findings are `unfieldable_depth`. **49 of those do not survive a roster-bucket
recount** (`idp_bucket_recount.py`).

`draft_battery._position_of` returns the RAW Sleeper position by deliberate design — its own
docstring records this as a latent issue kept unchanged so five committed batteries stay
comparable. So a player whose `fantasy_positions` are `['DL','LB']` is counted as an LB, while
`player_universe.player_position` buckets him DL, which is the slot family the optimizer actually
fields him in. Recounted through that bucket, **every flagged HEAVY_IDP roster under a sharp
strategy sits at LB 3 against a ceiling of 3.** Roster 11 of `HEAVY_IDP__sharp_auto` went from
"held 5, unfieldable 2" to LB 3 + DL 2 — inside every ceiling, and fieldable in every week.

The audit is therefore a LOWER bound in IDP formats in one direction and an over-count in the
other: a roster holding OLB + ILB + LB + LB counts LB 2 and the sub-positions are skipped
entirely, while four DL/LB duals count as four LBs. **Not changed here**, for the reason its
docstring already gives; recorded, with the recount instrument committed beside it.

| | reported | survives the recount |
|---|---|---|
| `unfieldable_depth` | 73 | **24** |
| of those, under `noisy_k8` | | 17 |
| of those, under a noiseless strategy | | 7, all HEAVY_IDP |

**In the five non-IDP formats the engine exceeds no fieldability ceiling under any noiseless
strategy.**

## 2. The 17 `noisy_k8` survivors are the noise model, not the engine — measured, not argued

`noisy_k8` sets `sharp_seats: []`, so **every** seat draws uniformly from its own top 8; no seat in
that arm is the sharp engine. `snap.candidates` is the engine's own order with surplus bodies sorted
last by `unfieldable_last`, so rank 0 means the engine ranked that player first and rank > 0 means
the draw reached past the engine's choice. `noise_replay.py` replays the arm, asserts the
reproduced `pick_sequence` equals the report's (it does — 192 picks, 192 draws), and records the
drawn rank on every pick:

```
15.08 R15  roster  8 QB   held 3 > ceiling 2   drawn_rank=7  candidates=9
15.10 R15  roster 10 DEF  held 3 > ceiling 2   drawn_rank=6  candidates=9
15.12 R15  roster 12 K    held 3 > ceiling 2   drawn_rank=7  candidates=9
16.01 R16  roster 12 QB   held 3 > ceiling 2   drawn_rank=6  candidates=9
16.10 R16  roster  3 DEF  held 3 > ceiling 2   drawn_rank=6  candidates=7
16.11 R16  roster  2 DEF  held 3 > ceiling 2   drawn_rank=6  candidates=7
16.12 R16  roster  1 K    held 3 > ceiling 2   drawn_rank=5  candidates=7

rank 0 (the ENGINE's own first choice): 0 of 7
```

**Zero of seven at rank 0.** Every one is rank 5–7 out of a list of 7–9, in the last two rounds.
The mechanism is exact: the draw is over `min(top_k, len(candidates))`, so once the candidate list
falls below 8 the draw covers the WHOLE list and reaches the bottom-sorted surplus with probability
1/7. This is positive evidence that the backstop binds — the only way a surplus body was taken is a
random draw over a list shorter than `k`.

## 3. Does it draft well on a varied field

`bpa_projected_ruler.py`, results in `VDS_BPA_PROJECTED_RULER.json`. The ruler is the projected
analogue of the realized one: each week's best legal lineup under `lineup_optimizer`, summed over
the 18 weeks on disk. **The limit, stated rather than buried:** both chairs draft off the same
projections, so this measures STRUCTURE, not forecasting. Value over a best-available chair is what
the 2023/2024 realized work speaks to.

### Against `raw_bpa` — position-blind. Decisive in every format.

| format | engine (sharp_auto) | raw_bpa | delta/seat | seats ahead |
|---|---|---|---|---|
| 12T_ppr_K_DEF | 2510.8 | 2284.5 | **+226.2** | 11/12 |
| 12T_ppr_SF | 2544.2 | 2417.3 | **+127.0** | 9/12 |
| 4WR_TE_PREMIUM | 2600.6 | 2482.5 | **+118.1** | 9/12 |
| HEAVY_IDP | 2755.6 | 2259.5 | **+496.1** | 12/12 |
| 12T_ppr | 2247.4 | 2105.2 | **+142.1** | 12/12 |
| SHORT_DRAFT | 2119.6 | 1729.6 | **+390.0** | 11/12 |

### Against `sane_bpa` — covers its starting slots first. A tie, and THE PRE-REGISTERED BAR IS NOT MET.

| format | sharp_auto | sharp_balanced = crossing | sharp_upside |
|---|---|---|---|
| 12T_ppr_K_DEF | +0.8 (6/12) | −2.4 (6/12) | −32.3 (4/12) |
| 12T_ppr_SF | −5.9 (6/12) | −10.1 (6/12) | −63.4 (2/12) |
| 4WR_TE_PREMIUM | +0.1 (6/12) | −9.3 (6/12) | −76.7 (5/12) |
| HEAVY_IDP | **+23.8 (7/12)** | −30.3 (7/12) | −86.6 (3/12) |
| 12T_ppr | −5.3 (5/12) | −5.3 (5/12) | −30.1 (4/12) |
| SHORT_DRAFT | −1.9 (5/12) | −1.9 (5/12) | −20.8 (5/12) |

The bar was "ahead in aggregate in every format AND ahead on a majority of seats in each". It is
not met, and the bar is not being moved after the fact. What the numbers are: −0.2% to +0.9% of a
~2500-point season, against a chair that fills every starting slot before taking depth.

**What the ruler's own resolution is, from this same run rather than asserted.** It separates the
engine from `raw_bpa` by +118 to +496, and it separates `sharp_upside` from `sharp_auto` in the
same direction in all six formats by 20 to 87. So it resolves differences of roughly 1% and up.
The engine-to-`sane_bpa` gap is 0.2–1.2%, at or under that. A tie here is the ruler declining to
distinguish two need-aware chairs — which is the limitation `realized_ruler.py` was built to escape,
and its docstring already measured the projected ruler as INDIFFERENT to the K/DEF placement this
battery exists to police (−0.16% / +0.08% across drafts placing DEF from round 5 to round 10).

### The one place the engine separates cleanly: roster spots it can actually field

Mean players per roster who never appeared in any week's optimal lineup — the owner's "depth and
bench strength", measured rather than described:

| format | raw_bpa | sane_bpa | **engine** |
|---|---|---|---|
| 12T_ppr_K_DEF | 3.25 | 1.67 | **0.50** |
| HEAVY_IDP | 3.75 | 1.00 | **0.67** |
| 12T_ppr_SF | 2.33 | 1.75 | 1.92 |
| 4WR_TE_PREMIUM | 1.92 | 1.75 | 2.00 |
| 12T_ppr | 2.50 | 1.67 | 2.08 |
| SHORT_DRAFT | 0.42 | 0.00 | 0.00 |

On exactly the two formats carrying dedicated K/DEF/IDP slots — the shape the owner's K/DST concern
is about — the engine carries **a third to a fifth** as many never-fielded bodies as `raw_bpa` and
well under half `sane_bpa`'s, while scoring the same or better. In `12T_ppr_K_DEF` it is +0.8 points
on the ruler with 1.17 fewer wasted roster spots per team: the same season from a better-shaped
roster. On the three plain formats it is level with `sane_bpa` or a touch behind.

## 4. Two coverage findings about the battery itself

- **`crossing` reproduced `sharp_balanced` BYTE-FOR-BYTE in all six formats, and the report says
  why.** `picks_with_growth_measured` — the count of picks whose chosen candidate carried a growth
  signal, which is to say picks made in UPSIDE valuation — is **0 for every `crossing` arm in every
  format**, exactly as it is for `sharp_balanced`. So the `#261` crossing rule **did not reach upside
  mode on a single pick of any of the 36 arms.** `mode="auto"` under a rule that never fires is pure
  balanced, which is why the drafts are identical. (An earlier draft of this file said the two cases
  were indistinguishable from the report and would need a replay. They are not: this field
  distinguishes them, and no replay was needed.)
- **The mode coverage is fully accounted for, which is what makes that a coverage claim rather than a
  guess.** `UPSIDE_MODE_DEFAULT_ROUND` is 15, and every `sharp_auto` count is exactly the picks from
  round 15 on:

  | format | rounds | rounds ≥ 15 | picks | `sharp_auto` growth_measured |
  |---|---|---|---|---|
  | 12T_ppr_K_DEF | 16 | 15–16 | 24 | 24 |
  | 12T_ppr_SF | 15 | 15 | 12 | 12 |
  | 4WR_TE_PREMIUM | 16 | 15–16 | 24 | 24 |
  | HEAVY_IDP | 18 | 15–18 | 48 | 48 |
  | 12T_ppr | 14 | none | 0 | 0 |
  | 12T_ppr_SHORT_DRAFT | 8 | none | 0 | 0 |

  So `sharp_auto` = `sharp_balanced` in exactly the two formats whose draft ends before round 15, and
  `sharp_upside` measures growth on every pick (192/180/192/216/168/96 = every pick of each format).
  Nothing about the mode axis is unexplained.
- **The battery's own `INERT_ARMS` detector cannot see the `crossing` duplication.** It compares each
  arm to the CONTROL (`sharp_auto`) only, so it flagged 4 arms — `sharp_balanced` and `crossing` in
  the two formats where they also match the control — and stayed silent on the pairwise duplication
  in the other four. An inertness test that is not pairwise under-reports by exactly this shape.

Effective strategy count is therefore **5, not 6**: `sharp_auto`, `sharp_balanced` (= `crossing`),
`sharp_upside`, `noisy_k3`, `noisy_k8`. And the `#261` crossing rule is **unexercised** by this
battery — a gap in what the run licenses, not a defect it found.

## 5. What this does and does not license

**Settled.** The engine drafts a fieldable, sanely-shaped roster across six formats and five
distinct strategies. It beats position-blind best-available everywhere by 118–496 points a seat.
It exceeds no fieldability ceiling anywhere under a noiseless strategy in a non-IDP format, and the
ceiling breaches that do exist under an all-noisy field are the draw reaching past the engine's own
ordering, at rank 5–7 of 7–9, measured. `12T_ppr_SHORT_DRAFT` finished with zero findings under all
six strategies. On the K/DEF and IDP shapes it wastes a fraction of the roster spots either chair
does.

**Not settled, and it needs a ruling rather than a caveat.** `sharp_upside` — mode `upside` from
round 1 — is worse than `sharp_auto` on fieldable value in **all six formats**, by 20.8 to 86.6
points a seat, ahead on only 2–5 of 12 seats against `sane_bpa`. Same direction, six formats, no
exceptions. That is an engine-behaviour finding, and by `#184` it goes to the owner rather than into
a repair commit. It is also the first time the upside-mode gap has been measured on roster quality
rather than on a board diff.

**Not answerable here at all.** Whether the engine picks better PLAYERS than a need-aware chair.
Both draft off one set of projections, and the capture has no realized season. That question belongs
to the 2023/2024 realized work, where `#35` as shipped paid +21.70 and +43.69 a seat.
