# `#30`: the derived streaming replacement level works — +226.6 realized points a seat

**2024, `12T_ppr_K_DEF`, 12 seats, graded on realized outcomes.** One process, one code version,
one toggle: `replacement_levels` for K and DEF replaced by the DERIVED streaming baseline.

| arm | wins | mean delta vs field | median | first K/DST rounds |
|---|---|---:|---:|---|
| base | 7 / 12 | −15.4 | +10.8 | **4, 5** |
| **streaming** | **11 / 12** | **+191.4** | **+196.7** | **8, 9, 13** |

**Paired, per seat (streaming − base): mean +226.6, median +236.1, improved 11 of 12.**

## Both of the owner's conditions, met

- **The shape.** First K/DST moves from rounds 4–5 to **8–13**. Seven of twelve seats now take
  their first at **round 13**, inside the stated target of 12–16.
- **The gate.** Not merely "no quality drop-off" — a large quality **gain**, and measured on the
  one ruler the engine cannot optimise toward. `#16` bought the shape and paid −6.09 on the
  independent ruler; this buys the shape and gains +226.6 realized points a seat.

## Derived, not chosen (`#56`)

The level is: each week, the best wire player by **that week's projection**, summed. Wire = outside
the top (teams × slots) by season-sum projection, which is what a draft removes.

Every input is a league fact (`teams`, `roster_positions`) or a published projection. **No constant
is selected.** Measured for 2024: **K 121.78 → 164.5, DEF 107.95 → 146.05.**

It is applied as a **floor only** — the streaming baseline is what you get for free, so it can
raise a replacement level and never lower one. It cannot make a position look scarcer than the
draft already says it is.

**No hindsight.** Weekly projections are published before the games. Realized stats are used only
to SCORE, never to choose.

## Why this works where the earlier reasoning said it would not

Two of my own conclusions were too pessimistic, and the difference is worth recording.

1. I measured the correction as "+16 on the board's own 2026 vintage" and concluded it was too
   small. That was the **2026** snapshot; derived on the drafted season it is **+38 for DEF and
   +43 for K** — inside the range the saturation curve says moves the first DEF to round 7–8, and
   the observed rounds are 8–13.
2. The saturation curve itself (5.09 → 7.02 at +30, → 10.01 at +55) was measured under the
   **projected** ruler in self-play. It described where DEF stops being the top board row. It did
   not, and could not, say what deferring was WORTH — the projected ruler is indifferent to K/DST
   timing by −0.16%/+0.08%. The realized ruler is not.

So "the shape is not reachable by valuation" was wrong in its strong form. A *correct* valuation
reaches round 8–13 and pays.

## What is NOT established

- **One season, one format.** n = 12 seats (11 distinct — seats 2 and 3 collapse, see
  `evidence/backtest/README.md`). A 2023 holdout is the next step and is required before this
  ships.
- **The level is derived from the drafted season's own weekly projections.** That is what a live
  implementation would also do, so it is fair rather than circular — but it has not been shown to
  transfer to a season the derivation did not see.
- **Production plumbing does not exist.** `app.py` passes season sums; weekly projections do not
  currently reach `replacement_levels`. This experiment wraps the function and restores it.
- **The ruler models no waivers**, so the engine gets no credit for actually streaming the
  defense it deferred. The measured gain is therefore **conservative** — it is what deferring buys
  even when you never work the wire.
