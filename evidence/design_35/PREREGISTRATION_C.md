# Pre-registration — #35 Formulation C on realized outcomes

Written and committed BEFORE the 12-seat arms were launched, and the reading below is fixed here
so it cannot be chosen after the numbers land.

**Commit the runs start at: `d580c91`.** Instrument:
`evidence/design_35/phantom_cap_experiment.py`. Ruler: `realized_ruler` — the sum of each week's
best legal lineup over that season's actual stats. Format `12T_ppr_K_DEF` (the only backtest
format with K and DEF slots and the 64-key rulebook that prices them). Field: `need_first` and
`points_need`, both derived from the drafted season's own projections. `--streaming` on, so the
arms sit in the configuration C would ship into.

## What was already read, and declared as such

A **1-seat smoke** ran first, at the previous commit, and its purpose was instrument validity,
not an answer. It returned:

* control, 2024 seat 1: engine 2907.5, **+168.4** vs field — which is EXACTLY the figure the
  shipped configuration produced when `#30` was closed, so the baseline reproduces;
* capped, 2024 seat 1: engine 2920.6, **+198.6** vs field; paired engine delta **+13.1**;
* cap fired on **1050 of 2420** priced slots, mean reduction 41.0, max reduction 225.49,
  `pool_missing` 0 and `no_reach` 0 — so the arm is not vacuous and the recorder is wired.

One seat is one draft. It is recorded here because it was seen before the pre-registration, and
pretending otherwise would be the thing pre-registration exists to prevent.

## The arms

| arm | `board_slot_alternatives` | `unfieldable_last` |
|---|---|---|
| `control` (baseline) | shipped | shipped |
| `capped` | **capped at best remaining** | shipped |
| `capped_no_backstop` | **capped at best remaining** | **all-zero no-op** |

Seasons: **2024** and **2023**, 12 seats each. 2023 is the holdout — it is the season where
`#30`'s floor was worth +85 rather than +328, so it is where a pricing change has the least help
from elsewhere.

## Non-vacuity, asserted before the results are read

* `cap_stats.slots_capped` must be > 0 in both capped arms, or those arms are the control.
* `cap_stats.pool_missing` must be 0, or the cap was falling back and measuring nothing.
* `cap_stats.backstop_suppressed_calls` must be > 0 in `capped_no_backstop`, or that arm is
  `capped` under another name.
* The three arms must not produce identical engine totals across all 12 seats.

## The reading, fixed in advance

**On `capped` vs `control` (is C worth its cost):**

* **C is worth the bill** if the paired engine delta is positive on BOTH seasons, with a clear
  majority of seats improved on each. Then the `TEAM_SPECIFIC_CAPS` re-derivation is a bill worth
  paying and C goes to the owner as a proposal.
* **C is retired on outcome grounds** if the paired delta is negative on either season, or if it
  is positive on one and negative on the other. A change that inverts a registered invariant and
  reaches two derived constants has to pay for itself on both seasons, not on the one that
  flatters it. This is the outcome that would let C be closed without anyone re-deriving a bound.
* **C is indeterminate** if both seasons come back inside ±25 points per seat on the paired mean,
  which is roughly the noise this instrument has shown between configurations that differ in
  nothing that matters. An indeterminate result is NOT a licence to ship: a change with a known
  cost and an unmeasurable benefit is retired, and the reason recorded is "no measured benefit",
  not "no measured harm".

**On `capped_no_backstop` vs `control` (would C have made A unnecessary):**

* **A stays** if this arm is materially worse than `control` — which is what the prior says,
  because `#30`'s pricing floor without the backstop relocated hoarding from defenses to kickers
  rather than removing it. The owner's discomfort with the ceiling is then a preference the
  engine cannot honour for free, and that is the answer to give.
* **A becomes reconsiderable** only if this arm is within noise of `capped` AND its rosters show
  no position held past `slots(P) + 1`. Both conditions, not either: matching on points while
  still hoarding would mean the ruler cannot see the defect, which is the exact blind spot the
  oracle lineup has.

## What this cannot settle, stated now

Whether C is **admissible**. Capping inverts `lineup_optimizer.displacement_level`'s derived
non-positivity for a single-position candidate, and that premise is what
`pick_synthesis.TEAM_SPECIFIC_CAPS` cites when it exempts the term from a bound two shipped
constants derive from. A positive outcome here does not create a bound that does not exist; it
only decides whether the derivation is worth attempting. That question is being answered
separately and neither answer overrides the other.
