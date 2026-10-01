# Wave 3 — the measurement harness, audited as code

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

**Two of its claims I verified myself, and one of them is against my own repair:**

1. **H1 CONFIRMED.** `run_draft_battery.py:470-473` calls `draft_battery.run_battery(...)` with
   `sleeper_projections` and `sleeper_basis` only — no `weekly_projections`. And
   `weekly_projections_from_capture` appears in that file exactly once, at its own `def` on line 94;
   it is never called there. `run_vds_battery.py:130` does call it. **So the `#30` wiring fix I made
   at `04bccb5` repaired the loader and wired only the VDS battery. The FORMAT battery still drafts
   every arm with the streaming floor inert**, including the K/DEF arm added to close `has_defense`.
   I did not notice that when I made the fix, and nothing in the format battery's report says so —
   its `universe` block has no `streaming_floor_exercised` key, which is the very field whose `false`
   value caught the same defect in the VDS battery.

2. **The `TypeError` is real and production-reachable.** AST over `app.py`: the single
   `simulate_opponent_picks` call, at **line 4921**, passes
   `['pool_scope', 'sleeper_basis', 'sleeper_projections', 'weekly_projections']`. The function's
   accepted parameters are `['league', 'merger', 'my_roster_id', 'num_teams', 'pick_order', 'picks',
   'players_db', 'pool_scope', 'sleeper_basis', 'sleeper_projections']`. **`weekly_projections` is
   not among them, so that call raises `TypeError` at runtime** — the Mock Draft's opponent
   simulation. The pass flagged it as out of its lens; it is the most concrete production defect in
   the audit.

---

## Measurement-harness audit — tree `72af7bf` (branch `claude/fantasy-football-control-center-ff6qlu`)

**Setup disclosure.** The worktree was stale (draft_room.py 2051 lines, no draft_battery.py). I reconstructed the branch with `git archive` into my scratchpad and worked there; the shared checkout was not modified. No forbidden path was read. I did not read `git log`; the only commit text I saw was the stale worktree's one-line `git log -1` output ("cf8fa0c Post"), which I did not use. All probes ran from the reconstructed tree root with `PYTHONPATH` set to it; scripts are in `scratchpad/probes/` (`dupes.py`, `ruler_weekly.py`, `determinism.py`). I ran no full draft; the longest probe was 24 production-priced picks, run four times (~90 s each).

Line numbers below refer to the reconstructed tree.

---

### HIGH

**H1. The format battery — "the final acceptance gate" — omits `weekly_projections`, so the #30 streaming floor is inert on every arm, including the K/DEF arm added to close `has_defense`; the report has no field that says so.**
`run_draft_battery.py main()` (the `draft_battery.run_battery(...)` call, ~line 447) forwards `sleeper_projections` and `sleeper_basis` only. `weekly_projections_from_capture()` is defined in the same file (~line 95) and is never called from `main`. Production passes `weekly_projections` at all three `build_snapshot` call sites (`app.py` 5015, 5077, 5444); `run_vds_battery.py` 291 and `run_backtest_grade.py --streaming` pass it. `run_smoke_seats.main` (~line 415) and `run_roster_proof.py` (no `weekly` reference at all) also omit it. The `universe` block written by `_battery_report` has `priced_from`/`sleeper_basis` but no `streaming_floor_exercised` key (the VDS universe has one), so a reader cannot tell. `test_battery_pricing_path.test_run_battery_prices_the_ruler_the_same_way_as_the_draft` pins only the two sleeper keywords.
Measured on the `12T_ppr_K_DEF` opening board (`probes/ruler_weekly.py`, 18 weekly weeks available on disk): with vs without weekly lines, every one of 38 K rows moves −23.66 universal_value and every one of 32 DEF rows −15.94; no other position moves. Best K goes from +12.6 (overall rank 75) to −11.1 (rank 114); best DEF from 30.5 (rank 59) to 14.5 (rank 70).
*Conclusion the harness does not support:* any statement from a format-battery report about K/DEF draft position, K/DEF roster counts, `first_round_taken("K"/"DEF")`, or "0 structural findings on 12T_ppr_K_DEF" describes a board that ranks kickers ~40 slots higher than the shipped engine does. The same applies to `run_smoke_seats`/`run_roster_proof` win rates on any K/DEF-bearing format.

**H2. The battery's chairs use `mode="auto"`, but no production human pick is ever made under `auto`; on every arm longer than 14 rounds the late rounds are drafted under a valuation the live Draft Room never shows.**
`draft_simulation.simulate_full_draft` defaults `mode="auto"` (line 105) and `run_battery` forwards it (1067). `app.py` passes no `mode=` to any `build_snapshot` call and contains no "upside"/"balanced" toggle (grep: none), so the human's board is always `balanced`; `compute_draft_board`'s docstring reference to "the toggle … see app.py's Draft Room view" is stale. `auto` is the production path only for Mock-Draft rivals via `simulate_opponent_picks`. On `CAPTURE_owner_league` (25 rounds), `CAPTURE_fourth_and_forever` (26), `HEAVY_IDP` (18), `12T_ppr_K_DEF` (16), `4WR_TE_PREMIUM` (16), all picks from round 15 on (44%/46%/22%/12%/12%) use upside scoring, which zeroes every team-specific term. The matrix's "mode axis" cannot compensate: `12T_ppr_mode_balanced` is 14 rounds (`league_matrix` 144-149; base roster = 14 slots), and auto never reaches round 15 there, so it is byte-identical to `12T_ppr` — the docstring's own `duplicate_arms` measurement admits this. Result: **no format-battery arm exercises the human-turn valuation past round 14**. (VDS `sharp_balanced` on the 16/18-round formats does, partially.)
*Conclusion not supported:* "the owner's league drafts a legal, sensible roster across 25 rounds" as evidence about the engine the owner uses — 11 of those rounds were drafted by a roster-blind valuation the owner's board never displays.
Related, out of my lens but load-bearing for the docstring's claim of an "identical contract" with `simulate_opponent_picks`: `app.py` 4932 passes `weekly_projections=` to `draft_room.simulate_opponent_picks`, whose signature (`draft_room.py` 4407-4412; verified via `inspect.signature`) does not accept it. That call raises `TypeError`, so the one production path that does use `auto` currently cannot execute.

**H3. `CAPTURE_owner_league` — "THE LEAGUE THIS SYSTEM IS ACTUALLY USED ON" — is drafted as a non-dynasty league.**
`league_matrix` 188-198 builds the arm from `league_shape`, whose keys are exactly `roster_positions, scoring_settings, total_rosters` (no `settings`). `compute_draft_board` reads `is_dynasty = (league.get("settings") or {}).get("type") == 2` (draft_room.py 3679), so `time_horizon_adj` is never applied (4170) and `risk_adj`'s trajectory scaling is off (4194). Production's `league_for_engine` carries `settings` from Sleeper (`app.py` 5384). `format_axes_exercised` cannot see this: `advertised_format_axes` has no dynasty axis, although arm labels advertise `_dynasty`/`_redraft`.
*Conclusion not supported:* anything the owner-league arm says about multi-year valuation, rookie/age handling, or the health signal's scaling.

---

### MEDIUM

**M1. `duplicate_arms` misses byte-identical arms on a resumed run, so `independent_formats` is overstated exactly when `--resume` is used.**
`_FINGERPRINT_EXCLUDES = {"label","seconds"}` (draft_battery.py 789), but `run_draft_battery.main` stamps every arm with `produced_at_commit` and `carried_forward` before `_battery_report` calls `duplicate_arms(results)`. Demonstrated (`probes/dupes.py`): two content-identical arms with different `produced_at_commit` → `[]`; same commit → flagged. The resume path is the documented normal way a full run completes (container reclaim), so a report where `12T_ppr` is carried and `12T_ppr_mode_balanced` is fresh reports "33 independent" with the duplicate counted as independent evidence.

**M2. The ruler and the draft are priced differently in the VDS battery — the asymmetry `reference_values`' own docstring calls "worse than consistent-but-wrong".**
`run_battery` passes `weekly_projections` to `simulate_full_draft` (1071) but not to `reference_values` (1072-1074; the function has no such parameter, 569-571). On VDS `12T_ppr_K_DEF` arms, every K on a roster is credited +23.66 and every DEF +15.94 relative to the board the chairs drafted from (measurement in H1). `roster_strength.total_value`/`starter_value` and their spreads on those arms compare a streaming-floored draft against an unfloored ruler.

**M3. Trajectory provenance never reaches any report.** `simulate_full_draft` records `priced_from, sleeper_basis, mode, pool_scope, opponent_noise, upside_from_round, picks_by_mode` in `DraftTrajectory.config` "so two trajectories are not mistaken as comparable" (197-218), but `audit_trajectory` reads only `config["label"]` (draft_battery.py 767) and nothing else copies the config. Per-arm entries in BATTERY/VDS reports therefore carry no mode, no noise seed, no pricing path. A carried VDS arm produced under a different `VDS_SEED`/`top_k` is indistinguishable from a fresh one, while `_report["strategies"]`/`["seed"]` print the *current* code's constants (run_vds_battery.py 213-217).

**M4. `picks_by_mode` / `upside_from_round` are false under the crossing rule.** `_picks_by_mode` (draft_simulation.py 87-100) computes the split from `UPSIDE_MODE_DEFAULT_ROUND` regardless of `upside_rule`, and `upside_rule` is not recorded in the config (verified: config keys lack it). The VDS `crossing` arm's trajectory therefore states `upside_from_round: 15` and a round-15 split, while the board flipped wherever `_vor` was exhausted. `test_draft_simulation` pins only the round rule. (`qualifier_profile.picks_with_growth_measured` happens to be the true upside count, but nothing says the two should agree.)

**M5. VDS report fields count the control's findings under strategies that exercised nothing, and misclassify on partial/mid-run files.** `run_vds_battery._report` 155-161 sums findings over all arms including `INERT_ARMS`; 195-203 uses `len(vds_battery.STRATEGIES)` as the denominator regardless of how many strategies are in `results`. Demonstrated (`probes/dupes.py`): three arms run, two inert copies of the control, each with the control's one finding → `findings_by_strategy` 1/1/1, `findings_total 3`, and `STRATEGY_SPECIFIC_FINDINGS` lists all three strategies (the report's stated "shape #22 had"). The file is rewritten after every arm and runs are routinely killed, so the mid-run file is what a reader often holds. Also, `noisy_k3`/`noisy_k8` set `sharp_seats: []` (vds_battery.py 187-189): there is no engine seat in those arms, so a finding there is a property of uniform draws, yet it enters `STRATEGY_SPECIFIC_FINDINGS` on equal footing with `sharp_upside`.

**M6. VDS report has no join disclosure.** `_report`'s top-level keys (probe output) include no `commit`, `commits_present` or `carried_forward`; `resume_join.carry_forward` treats every VDS file as single-process. A resumed VDS run can mix arms from two commits, and `INERT_ARMS` — "the single most important line" — compares a carried control's `pick_sequence` with a fresh arm's, so an engine change between commits reads as a strategy effect (or hides one).

**M7. `format_axes` is computed from the current matrix, not from what carried arms drafted.** `_battery_report` calls `format_axes_exercised(matrix, labels)` (run_draft_battery.py ~300) with the live `league_matrix()`; a carried arm is matched by label only (`resume_join.carry_forward`). If an arm's league definition changes under the same label (as `12T_ppr_K_DEF` did when K/DEF were appended), a resumed report advertises axis coverage the carried numbers were not produced under.

**M8. `draft_counterfactual` compares the engine's scoring-aware pick against a vendor-only BPA.** `_full_board` (draft_counterfactual.py ~141) calls `compute_draft_board` without `sleeper_projections`, `sleeper_basis`, `weekly_projections` or `upside_rule`, while `engine_tav` is read off the trajectory snapshot. `regret_vs_bpa = engine_tav − bpa_tav` is then a difference of two pricings if the trajectory came from the battery. Its actual drivers (`run_counterfactual_analysis.py`, `run_draft_validation.py`) are internally consistent only because both use the vendor reconstruction (`_build_pool_players_db`, synthetic ids, no injury status) and `run_trials` without projections — i.e. the counterfactual "equals BPA / deviation supported" rates describe a universe production never prices.

---

### LOW

**L1. `roster_shape_axes["draftable_rounds"]` is the starting-slot count, not the draftable round count.** draft_battery.py 820 excludes `BN` as well as `IR`/`TAXI`, contradicting `league_config.draftable_slots` (excludes only `IR`). Measured over the whole matrix: axis says 8 where the arm drafts 14, 10 where it drafts 26 (F&F), 11 where it drafts 25 (owner). Only `12T_ppr_SHORT_DRAFT` coincidentally agrees. The `format_axes.axes.draftable_rounds` histogram in every report is therefore a histogram of a different quantity than its name.

**L2. `tav_margin_profile` is not "the gap between the chosen candidate and the runner-up".** draft_battery.py 526-535 takes top-two `tav` over the narrowed set regardless of who was chosen; under the feasibility/fieldability backstops or `opponent_noise` the chosen player is not the top-tav row, so `zero_margin_share` does not measure how decisively *the pick* was made. Code-style/labelling opinion unless a report quotes it as such.

**L3. `realized_ruler.DEFAULT_WEEKS = range(1, 19)`** scores week 18 (line 50), while the module's own absence measurements and most leagues' seasons stop at 17; an oracle lineup over week-18 rest patterns rewards bench depth beyond anything a league would have scored. Definitional; both arms of `run_backtest_grade` share it.

---

### Null results (checked, hold)

- **Determinism / run-order independence:** 24 production-priced picks of `12T_ppr_K_DEF`, drafted twice in one process and again in a second process after first drafting 12 picks of `12T_ppr_SF` through the same `DataMerger`: pick sequences and SHA-256 of all serialized snapshots identical across all four runs. `anchor_cache_key` includes `streaming_floors` and `sleeper_basis`; `_board_take_mass_cached` is per-board-dict.
- **Realized ruler inputs:** 2023 and 2024 stat captures carry 32 DEF and 36 K lines per week; 29-30 DEF and 31 K score > 0 under the capture's 64-key rulebook, so the K/DST claim is not hollow for want of data. Absent-week players are excluded from the solve, not zeroed.
- **`league_format_hint`** derives the same `{scoring, superflex, te_premium}` triple `app.py` 3550-3561 builds from `league_format_summary`.
- **`candidates[0]`** ordering (`pick_synthesis._board_order`) uses the same tuple as `compute_draft_board`'s sort (`_feasible, _unfieldable, −score, player_id`).
- `lineup_optimizer.optimize_lineup` is an exact Hungarian solve, so `unfilled_starting_slots`' FLEX-chain reasoning is sound.
- `store_io.write` is atomic-replace; `--only` + `--resume` refusal is real in both drivers.

### Instrument caveats of my own
H1's "rank 75 → 114" is an opening-board measurement; I did not run a full draft under both pricings, so the size of the K/DEF *draft-position* shift is inferred, not measured. H2 percentages are arithmetic from arm round counts and `UPSIDE_MODE_DEFAULT_ROUND = 15`, not from a run.
