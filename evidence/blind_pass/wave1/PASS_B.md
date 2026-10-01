# `#52` Wave 1, Pass B — raw report, verbatim

> **Unedited agent output.** Preserved as evidence, not as adjudicated truth. Triage lives in
> `LEDGER.md`; a finding here is a CLAIM until that ledger says otherwise. Fable, worktree
> isolation, mandate in `../MANDATE.md`, target `v1-freeze` (`6599b1e`). Ran 1,077s, 108 tool uses.

## Scope, provenance and contamination statement

The worktree I was given sits on `main` (cf8fa0c), which does not contain `draft_battery.py`, `run_draft_battery.py`, `prose_names.py`, `quantity_readers.py`, `evidence/`, or the ~3100-test suite. I audited `origin/claude/fantasy-football-control-center-ff6qlu` (head c8b737f), **exported read-only via `git archive` into the scratchpad with the five forbidden paths EXCLUDED from the export**, so they could not be opened by accident.

**Forbidden paths: none opened.** I also deliberately did not open `evidence/blind_pass/` (not forbidden, but it looked like prior-audit output). I loaded the repo's `engine-measurement` skill; it references register item numbers and repair history in passing but is not a forbidden file.

Real-data probes: `DataMerger()`, `build_players_db_from_capture()` (6,595 players), the capture's own `league_shape` (12-team, SUPER_FLEX, K, 2x IDP_FLEX). Empty-roster board: 2,028 rows, 820 priced.

## HIGH

### 1. `displacement_adj` is POSITIVE on the real board, violating the documented "non-positive by construction" invariant

**Where:** `draft_room.py:3483-3499` (multi-eligible branch of `score_row`) -> `lineup_optimizer.py:467-510` (`displacement_level`, `displaced = max(displaced, min(alt_of[s] for s in reachable))` at 503, `adjustment = free - displaced` at 510).

**Claim it breaks:** `draft_room.py:51-56, 2638` ("<= 0.0, never positive"); `CDME_CONTRACTS.md:114-118` (invariant 4b: "non-positive by construction ... that is why TEAM_SPECIFIC_CAPS needs no fourth entry"); `README.md:100-104`; `pick_synthesis.py:335-342`.

**Mechanism:** for a multi-eligible candidate the probe is given `eligible | {position}` but `free_alternative` stays the PRIMARY position's level. Any reachable slot whose alternative is below that level (an IDP_FLEX phantom for a WR-primary player) becomes the cheapest eviction, so `displaced < free` and the adjustment is `+ (level_primary - level_reachable_slot)`, uncapped.

**Measured:** Travis Hunter, `pos=WR elig=['DB','WR']`, `bpa -157.11`, `displacement_adj = +79.44` (WR level 225.49 - IDP_FLEX alternative 146.05), `basis=measured`, TAV rank moves 630 -> 350. `tav - uv = 79.44`, 2.2x the documented 36.0 ceiling.

**Why the suite does not see it:** `test_216_displacement.py:148,190` asserts `displacement_adj <= 0.0` over a league built by `build_mock_league(superflex=False, ...)` — a roster with NO IDP slot, so no WR/DB row can reach a cheaper phantom. **The invariant is pinned on the one league shape where it cannot fail.**

### 2. `time_horizon_adj` (and upside `growth`) subtracts two percentiles over DIFFERENT populations

`draft_room.py:3122` (over all 818 priced rows) vs `3141-3145` (over the 256 with `proj_3yr`); consumed at `3358-3359` and `upside_score` `2156-2157`.

**Measured:** production adjustment over the 256 rows: mean -4.09 (224 negative vs 32 positive). Recomputing the season percentile over the SAME 256-row population: mean -0.02. Per-row artifact -7.85 to +0.27; by position RB -3.78, TE -4.92, WR -4.66, QB -2.01. **101 rows are penalised whose corrected adjustment is >= 0.** 9 of the top 60 change rank; McCaffrey (bpa 220.56, adj -5.47) is ordered below Gibbs (bpa 219.21, adj -1.93).

**Why:** K/DEF/IDP rows (339 of 818) have season points but no `proj_3yr`, so they sit in the season-percentile denominator and not the 3yr one.

### 3. The anchor caches are keyed on a fingerprint that misses inputs the pool build reads

`draft_room.py:2398-2405`, `2377` (`_ANCHOR_FRAMES` excludes `merger.aliases`), used by `predraft_replacement_anchor` and `roster_points_lookup`.

Missing from the key: `injury_status`, `years_exp`, `status`, names, and the alias table.

**Measured:** putting the six RBs ranked just above RB replacement rank on IR: fresh RB level 192.68 -> 171.04; cache key UNCHANGED; a warm cache serves 192.68. Keys also unchanged when the alias table changes, when 717 rookies' `years_exp` changes, and when every `first_name` changes.

**Production path:** `app.py:3799-3802` `save_alias` -> `merger.reload()` -> `st.rerun()`. Nothing in `app.py` calls `reset_anchor_caches()` (grep: zero hits).

### 4. The cited "invariant test" for `need_bonus` is a tautology and cannot fail

`test_draft_room.py:1288-1300` asserts `top_uv - bottom_uv > NEED_BONUS_MAX`, then asserts `top_uv - (bottom_uv + NEED_BONUS_MAX) > 0` — algebraically the same inequality. It never reads any row's `need_bonus` or `final_score`.

**Demonstrated:** with `compute_draft_board` wrapped to give a player 66 points behind the leader a `need_bonus` of 500 and promote him to #1 by `final_score`, the test PASSES. This test is named as the enforcement of the need-bonus bound in `draft_room.py:121-124`, `:155` and README.

## MEDIUM

### 5. `feasibility_first` counts picks remaining with the wrong roster size in two real paths

`draft_room.py:2920-2925` — `total_picks = draft_rounds if draft_rounds else len(roster_positions)`; `draftable_slots_per_team` excludes IR. **Path A (IR slots, no draft_rounds):** probe returns all-1 (no-op) without `draft_rounds`, `[1,0]` with it. `simulate_opponent_picks`, `draft_strategy._build_opponent_boards` and `draft_battery.reference_values` do not pass it. **Path B (Mock Draft):** `build_mock_league` emits no `draft_rounds`; the mock's round count defaults to the REAL league's roster size and is user-settable 1-30. The exact failure mode #154 was built to stop is reachable in the sandbox.

### 6. A measured zero at the pricing input is collapsed into "unmeasured" and relabelled a coverage gap

`draft_room.py:1343` then `_derive_points_and_source` `2328-2329, 2356-2357` labels the row `no_priceable_input`, whose human label reads "no source carried a projection ... a COVERAGE GAP". A league with no kicking categories, or an IDP league scoring only sacks, makes this false for every such player.

### 7. Survival withheld, but `pick_necessity` (20% survival weight) still shown

`pick_synthesis.py:527-553`, `620`, `655-659`; rendered at `app.py:5174, 5543`, `draft_board_ui.py:230`, and handed to the LLM in `pick_debate.py:180`. The `SURVIVAL_DERIVED_FIELDS` claim ("every quantity that is a function of survival_probability") does not include `pick_necessity`/`necessity_label`, which are.

### 8. Two integrity instruments give wrong verdicts about load-bearing code

**`quantity_readers.py`:** an observer read anywhere outranks "used as a local in the producer". `displacement_adj`, `time_horizon_adj`, `risk_adj` are all classified OBSERVABLE although each is an addend of `universal_value`/`team_acquisition_value`. The docstring's own example is the case it gets wrong one level up.

**`prose_names.py`:** 39.5% of prose blocks containing a backticked name are exempt (373/944), 257 by "was" alone. Shield on: 1 dead name. Shield off: 19 (`rank1_share`, `top5_share`, `remaining_league_picks`, `test_the_seam_is_load_bearing`). `misquoted_constants` only matches `NAME = number` / `NAME (number)`.

### 9. Unit claims that survived the bpa-unit repair and are now false

`bpa` is raw signed points; measured board -225.49 to +220.56, 40.6% with |bpa| > 100, 82% negative. Stale: `draft_room.py:390-392`, `3040-3042`, `483-484`, `3438-3446/3458-3461` (rescale by `ELIGIBILITY_BONUS_MAX / TRADE_VALUE_SCALE_MAX = 12/100`, a ratio derived for a unit that no longer exists), `README.md:84-85`. `pick_synthesis.py:387-395`: `FORFEIT_SCALE_MAX = 100` justified as "a defensive clip" now routinely binds.

## LOW

10. **Banker's rounding in `_remaining_demand_rank`** (`1686`): 1.5->2, 2.5->2, 3.5->4, 4.5->4. Python's round-half-even, not a derived rule.
11. **`replacement_levels` clamp** (`1637-1640`): 12 K slots demanded, 8 priced kickers -> level = worst kicker, his VOR 0.0, though four teams get no kicker.
12. **`draft_strategy.py:451-462`** describes a value-share take model; production is the rank table. Wording only.
13. **Multi-eligible bucket inconsistency:** priced at the vendor row's position (Hunter -> WR) but counted for demand at `player_position` (-> DB). Population today: one player.
14. **`test_one_pricing_universe.py:45-54`** asserts a literal source string; a correct `**pricing` forwarding fails it, a comment passes it.
15. **`need_bonus` emitted on unpriced rows** (documented as a decision), then `compute_pick_necessity` adds `0.8 x need_bonus` to an unpriced candidate's necessity.

## Null results

`remaining_starter_demand`/`remaining_draft_capacity` bounded and order-invariant. `optimize_lineup`, `eligibility_bonus`, `depth_exposure`, `bye_collision` sound apart from the displacement case above. `near_tie_flags`, `decision_regime`, `detect_positional_cliff`, `_board_order` three-state absence consistent; unpriced rows never become leaders. `estimate_survival` mass normalisation consistent with docstrings. `_drop_contested_identities`, `_merge_across_eligibility`, `NO_NFL_TEAM` spot-read consistent. `assertion_floors.py --check` and `suite_taxonomy.py` run clean. `availability_factor` bounded, basis travels with the number.
