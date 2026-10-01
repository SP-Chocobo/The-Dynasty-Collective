# Pass A — valuation arithmetic, units, constants (wave 1)

Reproduced verbatim from the agent's hand-back. Not edited, not corrected. Finding 1 was later
adjudicated by the SKEPTIC: the population mismatch and the −3.71 mean STAND exactly, but the
ordering consequence is OVERSTATED — the top candidate was identical in 16 of 16 production-shaped
states. See `skeptic.md`.

**Contamination note of mine, not the pass's:** this pass disclosed seeing a commit subject through
`git log --oneline` that stated a conclusion ("upside gap RESULT: the differentiator does not
participate -- 2 of 87 picks"). My own commit subjects leaked it. Its finding 2 reaches that same
conclusion, so that convergence is NOT independent evidence and is not counted as such.

---

# Valuation arithmetic audit — draft_room.py pricing path (commit 9076e88, `claude/fantasy-football-control-center-ff6qlu`)

## Contamination statement
I did not open any forbidden path (FREEZE_RECORD*.md, FREEZE_CHECKLIST.md, POST_AUDIT_PLAN.md, DOC_INDEX.md, evidence/{smoke_seats,batteries,blind_pass,design_35,upside_gap}). Two near-misses to disclose: (1) `git log --oneline` printed commit subjects, one of which read "upside gap RESULT: the differentiator does not participate -- 2 of 87 picks"; I did not open the underlying evidence, and my upside-mode numbers below are my own measurement. (2) The scratchpad directory listing showed files from earlier sessions (e.g. V2_REGRESSION_BRIEFING.md); I did not open any of them. I read draft_room.py, lineup_optimizer.py, pick_synthesis.py, draft_strategy.py (parts), player_universe.py (parts), draft_battery.py, run_draft_battery.py, draft_simulation.py, a few tests, and the repo's `engine-measurement` skill.

Note: my worktree was on `main` (cf8fa0c), which lacks draft_battery.py/league_config.py; I detached to 9076e88 (tip of the named branch) so the code audited is the system the task describes. No file was modified.

Fixture for every probe: repo root, `build_players_db_from_capture` (6,595), `season_projections_from_capture`, `weekly_projections_from_capture`, `set_league_format(league_format_hint(league))`, `SLEEPER_BASIS_SEASON_SUM`, real capture scoring (64 keys, pass_td=6). Drained states come from one production-path draft (build_snapshot → candidates[0], 12T_ppr dynasty, 14 rounds, 168 picks, 792 s), replayed at seats 1/6/12, rounds 2–14 (24 board states). "Top-1" below means the board's own ordering key (fills_required_slot, cannot_be_fielded, final_score, player_id) — the same key `_board_order` re-sorts on, so it is the pick modulo backstops.

---

## 1. HIGH — `time_horizon_adj` subtracts two percentiles computed over different populations; the result is a systematic negative bias that the code's own comments say must not exist
**Where:** draft_room.py ~3878 (`pool.loc[has_proj, "_season_proj_pct"] = _percentile_map(proj_pool["_points"])` — over ALL priced rows) vs ~3898 (`_proj3yr_pct` = `_percentile_map(proj_pool.loc[has_3yr, "proj_3yr"])` — over only rows with a 3yr outlook). Consumed at `score_row` ~4168 (`(row["_proj3yr_pct"] - row["_season_proj_pct"]) * TIME_HORIZON_SLOPE`), `upside_score` ~2483 (`growth = max(0, proj3yr_pct - season_pct)`), and the dynasty risk relief `d_scale` ~4207, which reads the biased value.

**What is wrong:** On the real 12T_ppr board 481 rows are priced but only 259 carry `proj_3yr`; the 222 without one have median 15.9 projected points (75th pct 40.3), i.e. they sit at the bottom. So a mid-tier player's season percentile is inflated by ~222/481 of the scale relative to his 3yr percentile even when his rank is identical in both. Under matched populations the bias is (for matched pct p) ≈ 0.538p + 46.2 − p, largest mid-tier, zero only at the very top.

**Measured (opening 12T_ppr dynasty board):** mean `time_horizon_adj` over the 259 rows with a 3yr outlook is −3.72 in production vs −0.03 with both percentiles taken over the same 259 rows; 190/259 rows move by >2 points, 133/259 by >4; 101 rows flip sign. Players whose season rank equals their 3yr rank among the matched population — the definition of "no trajectory opinion" — are penalised: Sam Darnold (rank 33 both) −1.10, Luther Burden (67/67) −2.27, Theo Johnson (205/205) −6.15, Braelon Allen (212/213) −6.31. By position the production means are RB −3.68, TE −2.58, WR −1.09, QB +0.32, so the bias is cross-positionally uneven.

**Ordering effect:** opening-board universal_value order: top-20 order changes, 51 pairwise inversions among the top 100 (prod vs matched). Across the 24 drained states, removing `time_horizon_adj` entirely changes the board top-1 in 8 of 24 (margins between top-1 and top-2 are 0.13–5.98 in 20 of 24 states, so a ±4-point bias is decision-sized). In upside mode at round 14, the matched population would make 43 rows carry growth > 0 instead of 20 and changes the top-5 set (Alvin Kamara enters at +4.42).

**Failure scenario:** a dynasty league; any priced player with `proj_3yr` whose 3yr rank equals his season rank among players that have both numbers. Expected adjustment 0.0; production returns between −1 and −6.3 depending on tier, and the K/DEF-style comment at ~3880 ("a 'neutral' 50.0 standing in on one side of a difference is not neutral") describes exactly this class of defect, fixed for rows WITHOUT a 3yr number and left in place for rows WITH one.

---

## 2. MEDIUM — the bounded additive terms are still defined on a 0–100 bpa unit that `_scale_vor_to_bpa` abolished; their magnitudes were chosen for that unit and never re-derived
**Where:** draft_room.py 413–416 (comment: "small, bounded, additive nudges on the same linear 0-100 BPA scale"), `RISK_ADJ` 441, `NEED_BONUS_*` 518–520, `TRADE_VALUE_SCALE_MAX`/`DEPTH_EXPOSURE_MAX` 526–577 with the conversion at 4252 (`worst_loss * (DEPTH_EXPOSURE_MAX / TRADE_VALUE_SCALE_MAX)`, justified by "mean |bpa − trade_value| = 11.7" measured when bpa was 0–100), `UPSIDE_GROWTH_WEIGHT`/`TIME_HORIZON_CLAMP` at 589 and ~2500; `_scale_vor_to_bpa` 2508 is now `return vor.astype(float)`. pick_synthesis.py 306 `NECESSITY_STANDOUT_REFERENCE_GAP = 15.0` ("an ABSOLUTE reference" in TAV units) sits beside `_forfeit_scale` (683), which was re-derived for precisely this reason and says so.

**Measured consequences (real data):** bpa span on the opening board is −328.6..+227.6 (556 points; 12T_ppr_SF −215..+236).
- Upside mode is decorative: `growth_points` is clamped to ≤10 on a 556-point axis; on the opening board its mean is 0.33 with the 75th percentile at 0.0; the upside top-25 order is identical to a pure-bpa sort (12T_ppr) and top-10 identical (SF); at the round-14 drained state it is nonzero on 20/314 rows and the top-25 order is again identical to bpa. `mode="upside"` is therefore "balanced minus the team terms", not a different valuation.
- `depth_exposure` converts trade_value into a unit that no longer exists: max observed value across 24 drained states is 9.36; it changes the board top-1 in 2/24 states, `need_bonus` in 3/24, `risk_adj` in 1/24, while `displacement_adj` (derived, uncapped, −30 to −110) changes it in 15/24.
- `RISK_ADJ` −18 is now "18 projected points": Jayden Higgins (WR, IR, vendor-priced, 173 pts) is docked 10.4%; a 400-point player would be docked 4.5%.
- `test_need_bonus_cannot_flip_a_large_universal_value_gap` (test_draft_room.py 1288) compares the top and bottom priced rows of the board (gap ≈556 vs cap 12), so the invariant it guards is vacuous on the current unit.

**Failure scenario:** two same-projection IR receivers, one vendor-priced and one Sleeper-season-scored: the first loses a flat 18 (health_penalty 443–461), the second loses 23.5% via `availability_factor` (player_universe.py 119–160, RULE_FLOOR 13/17) and 0 from RISK_ADJ. Measured on the SF opening board: Higgins (IR, no Sleeper line) −18 of 173; Jordyn Tyson (IR, rule_floor) haircut to 125.30 with risk_adj 0. Which model applies is decided by vendor coverage, not by the designation; and the dynasty trajectory relief (4197–4209) scales only the flat form. Label: the individual constants are "chosen then justified" (their own comments say so); the unit drift is the arithmetic fact.

---

## 3. MEDIUM — `need_bonus` on an empty roster is a per-position constant carrying no roster information, and it reorders the opening board against `universal_value`
**Where:** draft_room.py 4213–4228 (`4.0 * dedicated_needed + 1.0 * min(flex_remaining, 1)`), constants 518–520.

**What is wrong:** With nothing drafted, every RB/WR gets +8.67, every TE +4.67, every QB +4.0 (SF: 8.72/4.72/4.85). The replacement rank already prices two RB slots per team (demand 32 vs 12); the dedicated-slot count is charged a second time as a flat cross-positional offset. The comment at 526–545 says both terms "fire on an empty roster" by design, so the arithmetic is intended; what it does is not "need".

**Measured:** opening 12T_ppr board, top 60 by final_score: 21 cross-position pairs where the higher-ranked row has the LOWER universal_value — Ashton Jeanty RB (UV 87.72) above Colston Loveland TE (91.47); Terry McLaurin WR (41.70) above Josh Allen QB (44.11); Quinshon Judkins RB (43.23) above Kittle, Kelce and Allen. Opening top-50 adjacent final_score gaps have median 2.09 (36 of 49 under 4), so a 4.0-point positional offset is decision-sized in rounds 1–3. In drained states the term is 0–0.67 on most rows and flips top-1 in 3/24.

**Failure scenario:** round 1, empty roster, TE with UV 91 vs RB with UV 88: the board recommends the RB solely because RB has two named slots.

---

## 4. MEDIUM-LOW — the superflex QB startable floor is derived in vendor points and applied to league-scored points (and to a mixed-source list)
**Where:** `qb_startable_floor` 1682–1699 reads `merger.projections` (Draft Sharks) → 0.5 × vendor QB12 = 163.5; `replacement_levels` 1826–1832 applies it to `at_pos["_points"]`, which after #180 are Sleeper season sums scored under the league's rules (469 of 481 rows) mixed with vendor rows (Michael Penix, 129.0, `points_vor_draftsharks`, unchanged under every scoring variant). The "48-point stability basin" (351–352 comment) was measured on the vendor curve.

**Measured:** base capture (pass_td=6): 32 QBs clear the floor, level = Fernando Mendoza 207.5 (QB32, 24 starting slots in the league), basis `startable_floor`. pass_td=4 (the most common real setting): still 32, level 172.58. pass_td=3/pass_yd=0.03/int=−3: 19 clear, level = QB19 170.54 still labelled `startable_floor`; QB1 bpa falls to 70.35 vs RB1 236.26 and no QB appears in the top 12 of a SUPERFLEX board. The floor holds in the common cases because both the vendor and scored cliffs happen to straddle 163.5, not because the guarantee was derived for the population it cuts. The floor-overrides-demand interaction is already flagged in the SUPER_FLEX_QB_SHARE comment (#184).

## 5. LOW — two units on one number line (trade_value VOR beside points VOR), now unscaled
**Where:** 3897–3913 (`trade_value − tv_replacement` written into the same `_vor` column as points). Since the scale step was removed, a 0–100-unit VOR and a ±300-point VOR share a sort key with no conversion. Latent: 0 rows on 1QB boards, 2 LB rows on IDP per the code's own census; the module docstring (86–94, #152) acknowledges it. No new failure beyond what is documented.

## 6. LOW — `mode="auto"`'s upside switch is effectively unreachable in the battery's core formats
**Where:** `UPSIDE_MODE_DEFAULT_ROUND = 15` (245); `compute_draft_board` 3702–3706; draft_battery.league_matrix sets rounds = draftable slots = 14 (SF 15). In 24 of 27 core arms auto never enters upside; in SF arms only the last round does. My 168-pick production-path draft ran every pick balanced. Given finding 2 (upside ≈ bpa order) the practical impact is small, but any claim about auto-mode upside behaviour from those arms is vacuous.

## 7. Code-style opinions (no failure scenario)
- `board_flex_share` (740) unconditionally returns None — a documented seam (#50) — but `starter_slot_counts` (860–870, "compute_draft_board always supplies it") and `fielded_flex_occupancy`'s docstring describe the measured branch as live; `SUPER_FLEX_QB_SHARE = 0.85` is therefore consulted on every SF board while its own comment says the derived value is 1.0.
- `_remaining_demand_rank` uses Python `round()` (half-to-even): in a 9-team league with a 2-way flex, RB demand 22.5 → 22 while TE 13.5 → 14 — opposite rounding directions between positions. Hand-computed; no matrix arm has an odd team count.
- The two board column lists are named inversely to the branches that return them (2545–2582); the code says so.
- The trajectory relief `d_scale` (4207) is a function of the biased term in finding 1, so relief is withheld more often than intended.

## Null results (examined carefully, nothing found)
- `replacement_levels` rank selection, domain omission instead of clamp, `truncated_out` recording; `remaining_starter_demand` per-team `max(.,0)`; `DEMAND_WHOLE_SLOT_TOLERANCE` derivation — arithmetic matches its docstrings.
- `cap_levels_at_best_remaining`, `_fill_omitted_from_anchor`, `predraft_replacement_anchor` cache keying — consistent; measured `replacement_level_capped` on 145–188 rows at rounds 8–14 with `predraft_anchor` basis on 152 rows, as designed.
- `displacement_level` / `shared_slot_alternatives`: the cancellation `bpa + displacement_adj = points − displaced` holds structurally; magnitudes are derived, not chosen; it is the only team term that actually decides drained-board picks (15/24), which is the intended counterweight.
- Streaming floor (raise-only, cap-exempt), `horizon_replacement`/`waiting_cost` (points minus points, observable-only), `feasibility_first`/`unfieldable_last` (sort keys, no constants), `_records_with_normalized_nan`, absence_kind/replacement_basis stamping — no unit or branch defects found.
- risk_adj: only 3–4 nonzero rows per board; no sign violations.

## Unfinished
- I measured board top-1 flips, not `narrow_candidates` picks with backstops applied (same key, so should coincide, but not separately verified).
- Finding 1's effect on full-draft outcomes (lineup points) was not run; the ordering deltas above are per-board.
- Probe scripts and raw outputs are in the session scratchpad (`probe1_opening.py` … `probe5b.py`, `probe3.out`, `draft_12T_ppr_picks.json`).
