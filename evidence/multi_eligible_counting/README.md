# 2.6's counting half, sized — and why it is a ruling and not a repair

`team_filled_by_position` counts a roster's picks by `player_position(info)`, the PRIMARY label, and
it is the single home everything counts through: `_team_starters_filled` → `my_filled` → `need_bonus`,
and `remaining_starter_demand` → `replacement_levels` → every price on the board.

## Where multi-eligibility actually lives

- **178** players in the capture universe are eligible at more than one position.
- **66** of them reach a real board; the earliest sits at **row 199**.
- Every one is an IDP dual — `DL/LB` or `DB/LB`. Offensive dual-eligibility is essentially absent
  from Sleeper's `fantasy_positions`.

So this bites IDP leagues, from roughly round 17 of a 12-team draft down, and not at all in the first
three rounds of any arm measured (`CAPTURE_owner_league`, `12T_ppr_SF`, `HEAVY_IDP`: **0** multi-eligible
picks in 36).

## The difference, isolated

`HEAVY_IDP`, one played draft, the SAME formula both ways — sum over teams of
`max(slots[pos] − that team's count at pos, 0)` — with only the count changing:

| after | multi-eligible held | LB demand by label | by eligibility | difference |
|---|---|---|---|---|
| round 5 (60 picks) | 7 | 20.0 | 13.0 | **−7.0 of 20 slots** |
| round 10 (120 picks) | 15 | 3.0 | 0.0 | −3.0 |
| round 15 (180 picks) | 26 | — | — | none; demand already satisfied |

Every other position is identical at every round. The whole effect is LB, because LB is the position
the duals can also reach.

## Why neither reading is correct

- **By primary label** (today): LB demand is overstated — up to 7 of 20 slots, 35% — because a
  `DL/LB` dual is counted at DL only. Demand feeds the replacement level, so LBs are priced as if
  more LB slots still need filling than do.
- **By eligibility**: reduces demand at BOTH of a dual's positions, which claims one player fills two
  slots. That understates total demand, which is the same error inverted.
- **By assignment** (solve each roster's lineup, count the slots actually filled): correct, and it
  redefines demand as a SOLVED quantity. `remaining_starter_demand`'s own docstring rests on being
  "EXACT and BOUNDED... carries no prior, no estimate and no behavioural claim", and says those
  properties "are what make it usable as the domain test for a valuation anchor". An assignment-based
  demand is still bounded, but it is no longer a per-position subtraction, and it changes
  `replacement_levels` — and therefore every price — on every IDP board.

That is an engine-design decision about the definition of demand (`#184`), so it goes to the owner
rather than into a commit.

## One measurement error of mine, recorded

My first probe compared `team_filled_by_position` (a RAW pick census, bench included) against
slots-filled-by-assignment (capped at capacity) and reported differences at every position — WR 48 vs
24, DL 43 vs 24. Those are two different quantities and the gap was mostly capacity, not
multi-eligibility. The engine-measurement skill's warning is exactly this: the failure mode is not a
crash, it is a plausible number about something else. The table above changes only the count, which is
the one thing the ruling is about.
