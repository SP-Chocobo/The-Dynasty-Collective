# `sharp_upside` — what the −20.8 to −86.6 actually represents

Bars fixed in `PREREGISTRATION.md` before either measurement was built. Order of record in
`CHRONOLOGY.md`, written while M1 was still running. Investigated against the frozen candidate;
**no production code was modified.**

## The answer in one line

**`sharp_upside`'s differentiator does not participate.** The growth tilt is positive on 2.9% of
board rows, reaches 1 point on 2.2%, never changes the top of the board, and was non-zero on **2 of
87** real chosen picks. The strategy is season-VOR drafting with roster awareness removed, and the
VDS loss is the cost of the removal — not the price of future value, because M2 shows it does not
buy any.

## M2 — the multi-year ruler (measured and recorded FIRST, `46b1439`)

`proj_3yr` is the vendor quantity `upside_score`'s growth term is a percentile difference OF. Best
legal starting lineup under it, paired per seat against `sharp_auto`:

| format | 3yr lineup | seats ahead | 3yr roster total | seats ahead |
|---|---|---|---|---|
| 12T_ppr_K_DEF | −141.2 | 5/12 | −22.4 | 5/12 |
| 12T_ppr_SF | −190.7 | 3/12 | −212.7 | 4/12 |
| 4WR_TE_PREMIUM | −126.3 | 6/12 | −125.8 | 4/12 |
| HEAVY_IDP | −174.4 | 5/12 | **+173.2** | 6/12 |
| 12T_ppr | −108.6 | 4/12 | −360.9 | 4/12 |
| 12T_ppr_SHORT_DRAFT | −224.6 | 5/12 | −224.6 | 5/12 |

**0 of 6 ahead** on the pre-registered primary measure, 1 of 6 on the secondary. H1 refuted. Not a
coverage artifact against upside either: it drafted MORE `proj_3yr`-covered players than
`sharp_auto` in two formats (12.42 vs 12.17; 10.83 vs 9.50) and still scored lower. And
`sharp_balanced` beats `sharp_auto` on 3yr roster value in SF (+173.1) and 4WR (+147.1) — staying
balanced holds more three-year value than switching to upside at round 15.

Limits, from the instrument's own docstring rather than added later: one solve, not weekly, so blind
to absences and unable to reward depth; only 259 pool rows carry `proj_3yr` and the vendor covers no
K, DEF or IDP, so on those formats it is the offensive core. Both arms graded identically.

## M1 — the growth tilt on real drained boards (87 states, 0 pick mismatches)

Every state reconstructed from the committed arm's own `pick_sequence` and CHECKED: the upside
snapshot's `candidates[0]` was the player the arm actually took at **all 87**.

**Pool-wide, across the six pick-1 boards — 6794 rows:**

| | |
|---|---|
| `growth_signal > 0` | **200 rows, 2.9%** |
| tilt ≥ 1 point | **149 rows, 2.2%** |
| max tilt | 10.0 — the clamp IS reached, by a handful |
| top row by `final_score` vs by `bpa` alone | **the same player in all six formats** |
| `growth_signal` absent (None, not 0.0) | 0 — the distinction was counted, and it is clean |

**Among the 87 real chosen picks: `growth_signal > 0` on 2.** So the term is not merely small in
aggregate; it is absent from essentially every decision the strategy makes.

That settles the mechanism question the owner posed. This is **not** a growth signal that fires
substantially and chooses badly. It is a growth signal that barely fires. So the VDS result cannot
be read as evidence against the growth MODEL — the model was not participating. What it is evidence
against is the composition: `mode="upside"` discards `need_bonus`, `eligibility_bonus`,
`depth_exposure`, `displacement_adj`, `time_horizon_adj` and `risk_adj` in exchange for a term worth
≤10 points that is zero for the players its own `bpa` ranks first.

Why it cannot fire: `growth_points = clamp(0.5 × (proj3yr_pct − season_pct), ±10)` against a `bpa`
span in the hundreds. Even at the clamp it is a 10-point nudge, and it is ADDED to `bpa` rather than
replacing it. A ±10 tilt cannot reorder a board whose top rows are tens of points apart — which is
exactly what "top by `final_score` == top by `bpa`" measures.

## The one engine-level thing found, and its blast radius

**The upside board goes flat in the late rounds and falls back to `player_id`.** 8 of 87 states had
the top candidate tied on value with others; **0 of 87 in balanced mode at the identical states.**
All 8 are rounds 12–16, and every tie is at value exactly 0.00.

What is tied is not equivalent (`m1b`, `12T_ppr_K_DEF` R12, 25 candidates, four tied at 0.00):

```
  player_id name              pos     bpa  upside_tav   balanced_tav  bal_rank
       4943 Sam Darnold        QB     0.0         0.0         -41.22        21
       8172 Greg Dulcich       TE     0.0         0.0         -85.65        22
       9511 Keaton Mitchell    RB     0.0         0.0         -87.51        23
       9754 Quentin Johnston   WR     0.0         0.0           None  not in top
  balanced mode's own pick at this state: Denver Broncos (DEF) tav=+1.90
```

One best-remaining player per position, each at `bpa` exactly 0.00 because the replacement level is
a rank SELECTED within the remaining pool, so the player at that rank prices at exactly zero. The
upside board takes the lowest `player_id` of the four. Balanced mode ranks the same four 21st, 22nd,
23rd and off-board, and prefers a positive-value DEF that upside mode does not surface at all.

**Blast radius: production cannot reach this.** All three `build_snapshot` call sites in `app.py`
omit `mode`, the `**snapshot_inputs` dict carries no `mode` key, and `build_snapshot` threads its
`"balanced"` default into `compute_draft_board` and into `pick_analysis` → `_build_opponent_boards`,
so the rival boards are balanced too. `detect_positional_run` takes no mode and builds no board, and
`app.py` does not call `roster_diagnostics` at all. AST-audited over the call sites rather than
grepped for the word "upside".

## A prediction of mine that was wrong, twice, and how it ended

I predicted in `m1c`'s own docstring that the 0.00 tie was a consequence of `#35` — that before the
cap, an exhausted position's stale anchor sat above the remaining pool so everything priced negative
and no tie could form.

1. `m1c` ran the cap-on/cap-off A/B at `12T_ppr_K_DEF` R12 and came back **identical**, and I took
   that as a refutation.
2. The recording wrapper in the same run then showed the cap was **called 13 times and capped
   nothing** at that state. So the arm was vacuous — an identical board because the thing under test
   never fired — and the refutation was worth nothing.
3. `m1d` therefore ran it at **all eight** flat-board states:

| format | R | cap fired on | tie, cap on | tie, cap off | same pick |
|---|---|---|---|---|---|
| 12T_ppr | 13 | NONE | 4 | 4 | yes |
| 12T_ppr | 14 | RB, WR | 4 | 2 | **no** |
| 12T_ppr_K_DEF | 12 | NONE | 4 | 4 | yes |
| 12T_ppr_K_DEF | 13 | QB, TE | 4 | 2 | **no** |
| 12T_ppr_K_DEF | 14 | QB, TE | 4 | 2 | **no** |
| 12T_ppr_K_DEF | 15 | QB, TE | 4 | 2 | **no** |
| 4WR_TE_PREMIUM | 15 | WR | 4 | 3 | **no** |
| 4WR_TE_PREMIUM | 16 | TE, WR | 4 | 2 | **no** |

So the answer is neither of my two versions. **`#35` does not create the degeneracy** — two states
show a four-way tie with the cap firing on nothing — but where it does fire, in 6 of 8 states, it
**enlarges the tie from 2–3 to 4 and changes which player the upside board takes.** Recorded because
the alternative is a clean story that is not what the measurements say, and because I published a
refutation off a vacuous arm and should not have.

This does not disturb `#35`'s own certification, which was measured on realized outcomes in
balanced/auto mode (+21.70 and +43.69 a seat) on a path production does use.

## Diagnosis, against the three readings the owner named

- **A broken implementation?** No. `upside_score` computes what its docstring says, the `_has_3yr`
  guard works as designed (it is what keeps K and DEF out of the growth artifact), and the clamp is
  applied as specified. No arithmetic defect was found.
- **A differentiator that is effectively inert?** **Yes, decisively.** 2 of 87 chosen picks, 2.9% of
  rows, argmax unchanged in all six formats.
- **A legitimate tradeoff the VDS ruler cannot reward?** No. M2 refutes it on the strategy's own
  horizon, 0 of 6 formats.

## Recommendation

**No production change before the freeze**, and the reasons are not "it is only a simulation mode":

1. There is no defect to repair in the upside branch's arithmetic.
2. The finding is that a non-production strategy's differentiator is inert — a strategy-design
   question, and by `#184` the owner's.
3. The flat-board tiebreak is real and is an expressive failure, but it is confined to a branch
   `app.py` cannot reach, and no measurement here licenses a replacement behaviour. Changing the
   ordering of a branch the app does not use, days before a freeze, on the strength of a result
   measured on that same branch, is tuning toward the result.

Two items for the register after the freeze:

- **The growth term as formulated cannot express an upside preference.** ±10 against a
  hundreds-wide `bpa` span, positive on 2.9% of rows, argmax-neutral. If upside mode is ever to be a
  real strategy, that is the work — and it needs a derived conversion from percentile to points,
  which `#56` says is real work and was explicitly not done when the clamp was borrowed from
  `time_horizon_adj`.
- **The upside board's flat region.** Value ties at exactly 0.00 among one best-remaining player per
  position, resolved by `player_id`, with the `#35` interaction measured above.
