# `#52` Wave 1, Pass A — raw report, verbatim

> **Unedited agent output.** Preserved as evidence, not as adjudicated truth. Triage lives in
> `LEDGER.md`; a finding here is a CLAIM until that ledger says otherwise. Fable, worktree
> isolation, mandate in `../MANDATE.md`, target `v1-freeze` (`6599b1e`). Ran 874s, 89 tool uses.

## Adversarial audit of the CDME freeze state (commit 64f0830, tag v1-freeze)

**Scope note.** The worktree I was given sat at cf8fa0c (main), which does not contain `draft_battery.py`, `league_config.py`, `prose_names.py`, `quantity_readers.py` or `evidence/`. The mandate describes the freeze state, so I detached the worktree to 64f0830 (`claude/fantasy-football-control-center-ff6qlu`), audited that, and restored the original branch afterwards. No repository file was modified; line numbers below are for 64f0830.

**Contamination statement.** I did not open `FREEZE_RECORD.md`, `FREEZE_CHECKLIST.md`, `POST_AUDIT_PLAN.md`, `evidence/smoke_seats/` or `evidence/batteries/`. Two `grep -rn ... *.md` commands scanned every markdown file including the forbidden ones, but their matching lines were filtered out (`grep -v POST_AUDIT|FREEZE`) and no line from a forbidden file reached my context. I loaded the `engine-measurement` skill, which mentions `evidence/batteries/` by path but quotes no content from it. I consider this pass uncontaminated.

### 1. HIGH — The pre-draft anchor and roster-points caches are keyed on a fingerprint that omits inputs the pool build reads; stale prices confirmed on real data

`draft_room.py:2384-2405` (`_players_db_fingerprint`), `2407-2431` (`anchor_cache_key`), `2372-2382` (`_merger_content_fingerprint`), consumed by `predraft_replacement_anchor` (2434) and `roster_points_lookup` (2523).

The fingerprint hashes only `id | position | team | fantasy_positions` per player and the four merger frames. `build_available_pool` also reads `injury_status` (the availability haircut, 1339-1359), `status`, `years_exp`, `first_name/last_name` (`_admits_to_pool`, 1119-1132) and `merger.aliases` (`merge_player`, `data_merger.py:2108`). None of these are in the key. Probe: `injury_status None->IR`, `status->Inactive`, `years_exp->0`, name->`Player Invalid`, and an added alias all leave the key UNCHANGED.

Concrete failure, measured: RB pre-draft level = 185.64, held by Chuba Hubbard (gp 17). Flip his `injury_status` to `"IR"` and rebuild: the live pool prices him at 141.96; `roster_points_lookup` returns the cached 185.64; `predraft_replacement_anchor` returns the cached RB level 185.64 where a fresh build gives 176.98. Same mechanism for `save_alias` -> `merger.reload()` (`app.py:3799-3800`).

The docstring (2367-2371) says "The key therefore covers every input the anchor can read ... test_replacement_anchor_boundary asserts, input by input, that changing each one changes the key." `test_a_changed_players_db_changes_the_key` (test_replacement_anchor_boundary.py:413) varies only `position`. The claim is not supported.

### 2. HIGH — `time_horizon_adj` subtracts percentiles taken over two different populations

`draft_room.py:3121` computes `_season_proj_pct` over ALL priced rows; `3141-3144` computes `_proj3yr_pct` over only rows carrying `proj_3yr`; `score_row` (3376) differences them. The comment at 3135-3137 says this is "Provably a no-op ... zero rows in the real baseline carry a points projection WITHOUT a proj_3yr". That was true when only the vendor priced offense; the season-scored Sleeper path (#180) now prices players the vendor does not cover. Measured on the fixture board: 481 priced rows, 225 without `proj_3yr` (WR 96, TE 68, RB 58, QB 3).

Effect vs the same arithmetic over a single population: mean adjustment delta -3.68 (range -6.30 to +0.18), 96 sign flips; mean `time_horizon_adj` by position RB -6.59 / TE -6.31 / WR -2.13 / QB +0.37 shipped, against -2.72 / -1.76 / +1.78 / +2.06 same-population. 19 of the top 60 rows change rank. `d_scale` (3403-3407) and `upside_score`'s `growth` (2142) read the same mismatched pair. The test the comment cites, `test_missing_proj_3yr_is_neutral_not_a_penalty`, exists nowhere in the repository.

### 3. HIGH — Two incompatible take models feed one necessity score

`draft_strategy.py:314-388` (`positional_forfeits`) sums raw `RANK_TAKE_PROBABILITY` capped at 0.90 per position per pick; `estimate_survival` (635) uses the #206 normalised model via `_board_take_probability` (569), whose docstring says "There is exactly ONE take model in production and this is its only home (#126)".

Measured, opening board, seat 1, 22 intervening picks: `expected_taken` = RB 19.8, WR 3.52, TE 0.0, QB 0.0 — sum 23.32 over 22 picks (impossible). The normalised model gives RB 1.03, WR 0.157: the two disagree by ~19x.

Consequences: (a) `forfeit_component` (pick_synthesis.py:761) saturates at `FORFEIT_SCALE_MAX` for every RB while survival says almost nobody is taken; (b) TE and QB get `positional_forfeit == 0.0`, and `pick_debate.py:477-481` renders that as "measured 0 -- expected to be no worse than now" — a manufactured zero of exactly the `#187` class the code claims to forbid.

### 4. HIGH (claim) — `league_config`'s blocking contract blocks nothing

`league_config.py:169-228`: `admits_decision` / `decision_config` / `confirmation_state` / `ambiguities` have NO production caller; `app.py` imports only `describe_config_age` (1682). `FORMAT_DECIDING_KEYS` treats an absent `bonus_rec_te` as ambiguity, but a league with no TE premium simply lacks the key. Probe: the certified fixture league is AMBIGUOUS; every `build_mock_league` output is AMBIGUOUS. Wiring the gate as written would refuse every battery arm and the fixture league.

### 5. MEDIUM — `prose_names` exempts 43% of checked prose via the history shield

`prose_names.py:44-70`. Measured: 718 Python prose blocks carry a backticked name; 311 (43%) are exempt because they contain a marker (`was` alone shields 209). With the shield off, 15 dead names surface, including `test_missing_proj_3yr_is_neutral_not_a_penalty` (draft_room.py:3137), `remaining_league_picks`, `test_the_seam_is_load_bearing`. Of 146 constant quotations, 74 are exempt. `numeric_constants()` admits only literal int/float assignments, so `DEPTH_EXPOSURE_MAX`, `ELIGIBILITY_BONUS_MAX`, `NECESSITY_DENIAL_CEILING`, `CONTEXT_ELEVATED_THRESHOLD`, `CLIFF_MIN_MATERIAL_GAP`, `NECESSITY_DENIAL_SATURATION`, `LATE_ROUND_THRESHOLD` are never checked — the docstring says it "reads every module-level numeric constant".

### 6. MEDIUM — Adjustment constants sized for a 0-100 scale carried onto raw points

`draft_room.py:390-391`, `3042-3043`, `3051`, `pick_synthesis.py:386-391`. `_scale_vor_to_bpa` (2158) is the identity; none of these statements is true of the code. `TIME_HORIZON_CLAMP` +/-10, `RISK_ADJ` -18/-10/-5, `NEED_BONUS_MAX` 12 retain 0-100-era magnitudes where top-40 adjacent gaps run median 1.23 points. Montgomery and Warren sit at the -10.00 clamp.

### 7. MEDIUM — Survival is "withheld" but still drives what people see

`pick_synthesis.py:520-540` withholds the survival family. But `compute_pick_necessity` (689) still adds `(1 - survival) * 20`, and `app.py:_render_pick_metrics` (1484-1550) renders `survival_probability` as a percentage with NO `survival_is_presentable` gate. `grep survival_is_presentable app.py` returns nothing.

### 8. MEDIUM — Docstring asserts the measured flex share is always supplied; the seam returns None

`draft_room.py:762-764` returns `None` by design, yet `starter_slot_counts`' docstring (795-797) says "compute_draft_board always supplies it." `slot_share_basis` (833) is emitted by no production surface.

### 9. LOW-MEDIUM — The day-resolution freshness defect documented as fixed is still computed and shown

`app.py:1681-1684` still emits `(datetime.now().date() - sync_dt.date()).days`; `sleeper_client.players_freshness_entry` (108) same. A 23:59 sync read at 00:01 sorts as "1 day".

### 10. LOW — Two homes for the undrafted-slot vocabulary

`draft_room.py:1776 HORIZON_UNDRAFTED_SLOTS` duplicates `league_config.UNDRAFTED_SLOTS`; `draftable_slots_per_team` re-implements `league_config.draftable_slots`. Code-style opinion.

### 11. Documented contract breach, for the record (absence)

`draft_room.py:1331`: `sleeper_points = scored if scored != 0 else None` collapses a measured 0.0 into "unmeasured" on purpose. A player whose categories net to 0.0 is ordered last with `absence_kind = no_input`.

### Null results

Assertion-free tests: 23 of 3,103 test methods have no direct assert; all 23 delegate to asserting helpers. No vacuous test found by this route. Source-scanning tests: 269 assertIn/NotIn/Regex over ~16 modules; no additional silent-slice failure beyond what `render_trace.py` already records. Absence propagation on the board held on every path traced. `feasibility_first`/`draft_rounds`: the live path does pass it. `_remaining_demand_rank` monotone; `replacement_levels` clamp recorded via `truncated_out`. Battery structural audits read keys the serializer emits.
