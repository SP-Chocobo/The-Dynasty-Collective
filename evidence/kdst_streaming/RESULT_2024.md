# The engine drafts competitively — 11 of 12 seats, on outcomes it cannot optimise toward

**2024, `12T_ppr_K_DEF`, 12 seats, graded on REALIZED weekly outcomes against a field of
`need_first` / `points_need`.** Instrument: `run_backtest_grade.py` under
`period_correct_pool`, with both the pool and the board period-correct
(`evidence/backtest/ANACHRONISM.md` — two earlier readings of this were invalid and are
withdrawn there).

| arm | wins | mean vs field | median | first K/DST | roster shape (seat 1) |
|---|---:|---:|---:|---|---|
| base | 0 / 12 | −346.9 | −345.8 | 4, 5 | DEF 6, RB 3, WR 3, QB 2, TE 1, K 1 |
| + fieldability backstop | 7 / 12 | +5.0 | +10.6 | 4, 5 | WR 5, RB 4, K 2, DEF 2, QB 2, TE 1 |
| + `#30` streaming level | 3 / 12 | −18.5 | −25.6 | 8, 12 | RB 4, QB 4, DEF 4, WR 2, TE 1, K 1 |
| **both** | **11 / 12** | **+82.9** | **+66.5** | **8, 9, 10, 12** | **RB 6, WR 3, QB 2, DEF 2, K 2, TE 1** |

Paired, per seat, **improved 12 of 12 in both cases**:

- backstop over base: **+347.1** mean, +351.2 median
- backstop over streaming: **+106.0** mean, +121.5 median

## What this says

**The engine drafts well.** Eleven of twelve seats beat a field that ranks by the drafted
season's own projections and covers its starters — the baseline a manager with a projection
sheet actually plays. Not on projections, which the engine optimises toward, but on what really
happened.

**It drafts in a shape a competitive user would recognise.** Two of every dedicated position —
one starter, one bye cover — and the rest of the roster in flex-reachable depth: six running
backs, three receivers, one tight end. First K/DST at rounds 8–12, inside the stated target.
Compare the base arm's six defenses and one kicker.

**Neither fix is sufficient alone, and they are not redundant.** The backstop alone reaches
7/12 but still takes its first K/DST in round 4 — it caps the hoard without repricing the
position. `#30` alone moves the shape to rounds 8–12 but still finishes with four defenses and
four quarterbacks — it prices the position without capping anything. Together: the right price
AND the right count. Every seat improves under each, which is why this reads as two halves of
one defect rather than one fix and one coincidence.

## What this does NOT say

- **One season, one format.** The 2023 holdout is running and is the out-of-sample test. Nothing
  here transfers until it lands.
- **Self-play, against a fixed field.** All twelve chairs share a board; the field is two sane
  styles, not a room of humans.
- **No waivers.** The roster is frozen at the draft, so the engine gets no credit for actually
  streaming the defense it deferred — the measured gain is conservative in that direction.
- **The weekly solve is an ORACLE lineup.** It starts the best actual scorers, not the ones a
  manager would have guessed on Saturday. Every arm gets the same advantage, so the comparison
  survives it; the absolute totals are ceilings and must not be quoted as expected scores. It
  also means hoarding is REWARDED here rather than merely harmless, which makes the backstop's
  measured gain a lower bound on what it is worth to a real manager.
- **`unfieldable_last` is an engine-design change** (`#184`). Built, measured, not ruled. The
  owner decides whether it ships; `#30`'s half is already wired to production.
