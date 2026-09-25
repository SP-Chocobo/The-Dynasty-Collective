# `#35` Formulation C on realized outcomes — the result

Read `PREREGISTRATION_C.md`, including its amendment, before these numbers. The reading below is
the one fixed in advance; nothing here was chosen after the fact.

Instrument `evidence/design_35/phantom_cap_experiment.py`, four arms in one process per season, no
engine edit, commit `6cd3be0`. Ruler: `realized_ruler` — the sum of each week's best legal lineup
over that season's actual stats. Format `12T_ppr_K_DEF`, 12 seats, `--streaming` on.

## The three arms that have landed

| | wins | mean | median | first K/DST rounds |
|---|---:|---:|---:|---|
| **2024** control (shipped) | 11/12 | +82.9 | +66.5 | 8 8 8 8 8 9 9 10 12 12 12 12 |
| 2024 `capped` (C as specified) | 9/12 | +45.8 | +26.2 | 6 7 7 7 7 7 7 7 7 7 7 7 |
| 2024 `capped_floor_exempt` | 10/12 | **+97.7** | **+104.4** | 8 8 8 8 8 12 12 12 12 13 13 13 |
| **2023** control (shipped) | 4/12 | −49.9 | −81.0 | 7 8 8 8 8 8 8 8 8 8 8 9 |
| 2023 `capped` (C as specified) | 2/12 | −55.8 | −61.2 | 6 7 7 7 7 7 7 7 7 7 7 8 |
| 2023 `capped_floor_exempt` | 4/12 | **+1.0** | −6.9 | 7 8 8 8 8 8 8 8 8 8 8 9 |

Paired by seat, which is the measurement — every arm drafts the same seat against the same field, so
a seat is its own control:

| pairing | 2024 | 2023 |
|---|---|---|
| `capped_floor_exempt` − control | **+21.7/seat**, 9 up 3 down, total +260.4, median +12.8 | **+43.7/seat**, 8 up 3 down, total +524.0, median +60.7 |
| `capped` − control | −31.6/seat, 3 up 9 down | −10.4/seat, 9 up 3 down |
| `capped_floor_exempt` − `capped` | **+53.3/seat** | **+54.0/seat** |

## What the pre-registered reading says

> **C is worth the bill** if the paired engine delta is positive on BOTH seasons, with a clear
> majority of seats improved on each.

Positive on both (+21.7, +43.7) with 9 of 12 and 8 of 12 improved. **So by the reading fixed in
advance, C is worth the bill.**

**And the honest qualification, which the same document requires me to state.** The indeterminacy
band was "both seasons inside ±25 points per seat". 2024 came in at **+21.7, which is inside that
band**; 2023 at +43.7, which is not. So the result is not indeterminate by the letter — the clause
needs both — but 2024 on its own would have been. The effect is real and it is larger on the holdout
than on the season the engine already wins.

## The `#30` revert is the whole of C-as-specified's damage, and it is measured

`capped` − control is negative on both seasons; `capped_floor_exempt` − `capped` is **+53.3 and
+54.0 per seat**. So the entire deficit of C as specified, and more, is the streaming-floor revert
that the derived exemption removes.

The behavioural signature is cleaner than the points. First-K/DST placement:

* **2023:** `capped_floor_exempt` is **identical to control, seat for seat** — 7, 8 × 10, 9. The
  exemption restores placement exactly.
* **2024:** control spreads 8→12; `capped` collapses to 6–7 at every seat; `capped_floor_exempt`
  spreads **8→13**, i.e. later than control rather than earlier.

That last row is a real shape change and is not a restoration. It is the direction the anchor
correction predicts: capping a stale flex phantom lets receivers who were being priced against a
player who is not there rise, and they displace a kicker or defense from the pick. Pushing K/DST
later is what `#30` was pressing toward, so the direction is not alarming — but it is a change, and
it is reported as one rather than folded into "restores control".

## Non-vacuity, as pre-registered

| gate | result |
|---|---|
| `slots_capped` > 0 in both capped arms | 2024: 11,960 / 7,200. 2023: 11,902 / 6,598 |
| `pool_missing` = 0 | 0 everywhere |
| `slots_floor_exempt` = 0 in `capped` | 0 |
| `slots_floor_exempt` > 0 in the exempt arms | **5,496 = exactly 2,748 K + 2,748 DEF** |
| the cap bites beyond K and DEF | `capped`: WR, flex, QB, RB. exempt arms: **no K, no DEF** |
| arms not identical across seats | every arm differs from every other |

The exemption is exactly as narrow as it was derived to be: it restores the two floored positions and
touches nothing else.

## Two limits that bound what this licenses

**1. This measured C, and C is NOT the admissible form.** The derivation
(`evidence/DESIGN_35_CAPS_REDERIVATION.md`) establishes that C as specified inverts a registered
invariant and refutes `TEAM_SPECIFIC_CAPS`' exemption, with no constant available to re-derive — so C
cannot ship. The admissible form caps **`bpa`'s anchor** with the same quantity, which is
algebraically identical in `team_acquisition_value` (the level cancels between the two terms;
measured 0.00 across 388 rows) and therefore drafts identically **in balanced mode**. It differs in
**upside mode**, which scores on `bpa` alone — and in this 16-round format the last rounds are upside
mode. So this result transfers to the admissible form for most of the draft and not all of it. That
gap is unmeasured.

**2. The ruler's own limits stand.** No waivers or trades, and the weekly lineup is an ORACLE — it
starts the best actual scorers, not the ones a manager would have guessed. Every arm gets the same
advantage so the comparison survives it, but the absolute totals are ceilings.

## What is still running

`capped_floor_exempt_no_backstop` on both seasons — the owner's own question, whether C's pricing
makes the fieldability ceiling unnecessary. Its reading is also pre-registered and has two parts: A
becomes reconsiderable only if that arm is within noise of `capped_floor_exempt` **and** its rosters
hold no position past `slots(P) + 1`. Matching on points while still hoarding would mean the oracle
ruler cannot see the defect, which is its known blind spot.
