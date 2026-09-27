# Wave 2 — the SKEPTIC: adversarial adjudication of the five HIGH claims

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

This pass was given the five HIGH claims from wave 1 with authorship stripped and told to break
them, on the grounds that this repository has withdrawn published findings before after someone
checked the fixture rather than the reasoning. It disclosed an instrument error of its own (a probe
whose arm labels were inverted) and superseded it before reporting.

Its claim-3 refinement is the entry that vindicated investigating everything before consolidating:
the bound wave 1 proposed is valid but too loose to catch the case that motivates the fix.

---

# Skeptic pass — five claims, real-data fixture, commit c638c05 on claude/fantasy-football-control-center-ff6qlu

## Setup disclosure
- The worktree handed to me WAS stale (HEAD cf8fa0c, draft_room.py 2051 lines, draft_battery.py / league_config.py / invariant_registry.py / run_draft_battery.py absent). I did NOT modify it. I reconstructed the correct tree with `git archive claude/fantasy-football-control-center-ff6qlu | tar -x` into `/tmp/claude-0/.../scratchpad/tree` (draft_room.py 4445, pick_synthesis.py 2146, app.py 6924, draft_battery.py 1089) and ran every probe from that root with `PYTHONPATH=.` and `PYTHONDONTWRITEBYTECODE=1`. No `__pycache__` existed in the archived tree.
- I printed `git log --oneline -1` only to read the hash and cut the subject to 12 chars; I did not read or use any commit subject. I did not open any forbidden path.
- The scratchpad is shared and long-lived (files from prior passes, incl. a stale `light_idp_raw.json` dated 17:36). I did not read prior conclusions there; my draft overwrote that file (mtime 23:04, mine).
- Fixture: `rdb.build_players_db_from_capture()` (n=6595), `rdb.season_projections_from_capture()`, `rdb.scoring_settings_from_capture()` -> `db.league_matrix`, `merger.set_league_format(db.league_format_hint(league))` before every board, `sleeper_basis=SEASON_SUM`. All A/Bs are one process, one code version, toggling one thing.
- One instrument error of my own, caught and corrected: probe p5b dropped the iterated vendor row but labelled the arm by that row (labels inverted). The observed pool row (p5c) settles the fact; I report from that.

---

## CLAIM 1 — time_horizon_adj subtracts percentiles over different populations. **Mechanism STANDS; the ordering consequence is OVERSTATED (0 of 16 measured turns changed the pick).**

Code: draft_room.py:3867 `pool.loc[has_proj,"_season_proj_pct"] = _percentile_map(proj_pool["_points"])` (all priced rows); :3888 `_percentile_map(proj_pool.loc[has_3yr,"proj_3yr"])` (3yr rows only); consumed at :4171 `(row["_proj3yr_pct"] - row["_season_proj_pct"]) * 0.20`, clamped ±10, only when `is_dynasty and _has_3yr`. `_percentile_map` (:938) is `rank(pct=True)*100`.

Measured (spy on `dr._percentile_map`, tagged by `Series.name`, both calls captured per build):
- F&F opening board: season population n=481, 3yr population n=259, extra 222 rows have mean `_points` 32.3 vs 186.2 for 3yr rows. Production `time_horizon_adj` (emitted column) over rows with tha≠0: **mean −3.710, n=259** (claim −3.72). Same rows with matched populations: **−0.021** (claim −0.03). 91/259 rows flip sign; max |diff| 6.32.
- LIGHT_IDP opening: 780 vs 259; 12T_ppr_K_DEF: 551 vs 259. Bias persists mid-draft on my LIGHT_IDP trajectory: round 3 −4.017 (n=236), round 6 −3.736 (n=200), round 9 −3.488 (n=176), round 12 −3.302 (n=157), all ≈ −0.03..−0.15 matched.

Consumption / ordering (real A/B through `pick_synthesis.build_snapshot`, i.e. through feasibility/unfieldable backstops AND `narrow_candidates`' `_board_order` re-sort; second arm patches `_percentile_map` so the `_points` call ranks only the 3yr index, 50.0 elsewhere):
- 12 opening states (4 leagues × seats 1/6/12) + 4 mid-draft states (rounds 3/6/9/12): **top-1 candidate identical in 16/16**. Top-5 set identical 15/16 (round 6: Daniels QB fell 3rd→8th, McConkey entered).
- Candidates reordered but by little: F&F 6/48 moved, max shift 1; 12T_ppr 6/48, max 1; LIGHT_IDP 15/60, max 5; K_DEF 23/72, max 3; mid-draft 29/58 (max 4), 11/36 (5), 10/22 (2), 9/20 (3).
- Bias among the ACTUAL candidates is ~1/3 of the population figure: −1.24 (F&F), −1.42 (LIGHT_IDP), −0.94 (K_DEF), mid-draft −1.65/−1.31/−1.15/−0.72 — the rank-percentile shift is smallest at the top of the distribution where picks come from. The relative effect is a penalty on 3yr (offensive) rows vs non-3yr rows (IDP/K/DEF, tha=0.0), visible at round 6 where an LB sat 5th in prod and outside the top 8 matched.

Verdict: the population mismatch and the −3.7 mean are exactly as claimed. The claim overstates if read as changing picks: on 16 production-shaped board states the pick never moved; the effect is a ≤5-place shuffle of the narrowed list.

---

## CLAIM 2 — the recommendation panel renders a withheld quantity. **STANDS, with a reachability qualifier.**

- pick_synthesis.py:597 `SURVIVAL_IS_CALIBRATED = False`; :626 `withheld_fields()` returns {survival_probability, opportunity_cost, expected_value_of_waiting}. `grep withheld_fields\|survival_is_presentable app.py` → 0 hits.
- pick_synthesis.py:1721/1752 copies `survival_probability` unmodified onto every `CandidateSnapshot`; pick_debate.py:799-823 `recommended`/`best_alternative` ARE CandidateSnapshots; app.py:1544-1546 renders `f"{round(rec.survival_probability*100)}%"`, :5660 the same for `alt`, and `_render_pick_metrics` also renders `opportunity_cost` and `expected_value_of_waiting` (the whole withheld family). Called from both the live Draft Room (:5655) and the Mock Draft twin (:5229).
- Populated on the object app renders: F&F opening snapshots, seats 1/12/6: **48/48 candidates carry non-None survival** (bases `measured` w/ 22 or 12 intervening picks; `no_intervening_picks` = 1.0 at seat 12). Line 1545 would print `'55%'`, `'100%'`, `'72%'`; alt line `'71%'`/`'100%'`/`'83%'`; opportunity_cost 119.28 etc.
- Suppression elsewhere: the board component does gate — draft_board_ui.py:258 passes `survivalWithheld`, JS :811-816 and :921 honour it. (Side finding: :788, the `decisive`-regime leader sentence, prints `c.survival` WITHOUT the gate — unreachable today because `decision_regime` never returns "decisive" while uncalibrated, but it is an ungated read.)
- Reachability: RENDER_TRACE.json (619 calls) has 0 survival entries because the default render never reaches this branch. It is reached only after "Debate This Pick" runs with a configured LLM provider AND the Caller names a candidate: with no providers `debate_pick` returned `recommended=None` (3 errors) → app shows a warning and never calls `_render_pick_metrics`. With a key, the leak is live in the shipped app.

---

## CLAIM 3 — flex-reachable exemption; `slots_reachable(P)+1` derivable; 6–7 IDP against ceiling 2 with guards silent. **STANDS; one refinement on the derivation.**

Code: draft_room.py:3442 `fieldable_ceiling` drops any position with flex reach; :3473 `unfieldable_last` returns default if no ceiling; draft_battery.py:394 `unfieldable_depth` `if position in flexible ... continue`. For LIGHT_IDP (`QB RB RB WR WR TE FLEX IDP_FLEX +6 BN`) shipped `fieldable_ceiling` = {'QB': 2}; every other position exempt.

Derivation attack: `slots_reachable(P)+1` IS a valid upper bound — no week can start more P than the slots admitting P, so any excess is provably never fieldable; competition for shared slots only makes it LOOSE, never wrong. Verified with the production optimizer (`lineup_optimizer.optimize_lineup`, LIGHT_IDP slots): 3 DL → 1 startable; 2DL+2LB+2DB → 6 held, **1 startable, 5 permanently unfieldable, yet exceeds NO per-position ceiling** (each exactly at 2). The tighter derivable bound under competition is the joint one: Σ_{P in group} held ≤ |slots admitting any of the group| + 1 (= 2 here). Both are "derived from two league facts", but the per-position form under-counts. (The +1 bye backup is a convention shared with the dedicated case — two starters on the same bye need two backups — so it is no weaker here than there.)

Measurement (my own LIGHT_IDP draft, `simulate_full_draft`, production pricing path, 168 picks, 1258 s — above the skill's 956 s budget, note for scheduling; universe assert passed):
- `structural_findings` n = **0**. `unfieldable_last` cannot fire for IDP/TE/WR/RB here (no ceiling entry).
- Rosters (n=12): IDP totals 1,6,6,7,7,1,1,1,3,1,7,7 (mean 4.00). Per-position slots_reachable+1 = 2 for DL/LB/DB: **6 rosters exceed (LB 5,6,3,7,6,4; DB 3), 20 excess players**. Joint ceiling 2: **7 rosters exceed, 29 excess** (roster 9 = 2 LB + 1 DB is the case the per-position bound misses). Roster 4 holds 7 IDP; optimizer starts 1 → 6 benched forever. 20 IDP picks were made by seats already at/over the per-position ceiling; 29 at/over the joint one. IDP picks by round 6→14: 3,4,5,6,6,5,6,7,6.
- Not IDP-specific: roster 7 holds **7 TE** (slots_reachable(TE)+1 = 3), rosters 1/8/10 hold 7 WR (bound 4). The exemption is silent on all of it.

---

## CLAIM 4 — `name_key` cannot match multi-word city defenses; 11/32 priced `no_priceable_input` on the no-sync fallback. **STANDS (scoped to the fallback path, exactly as claimed).**

- data_merger.py:250 `name_key` → (first initial, everything after token 1): "Los Angeles Rams" → ('l','angeles rams'); the transcribed rows (data/baseline/rankings/sleeper_dst_projections.csv, 32 rows) are "L Rams" → ('l','rams'). Exact path fails (norm names differ), key path fails, fuzzy path returns 0 candidates, no alias. `_resolve(name, position="DEF", team)` over players_db's 32 DEF: **21 resolve via `key`, 11 return (None, 0 candidates)** — exactly GB, KC, LAC, LAR, LV, NE, NO, NYG, NYJ, SF, TB.
- Consequence, 12T_ppr_K_DEF board, `compute_draft_board` with `sleeper_projections=None`: DEF rows n=32; **11 multi-word = `no_priceable_input` / `absence_kind=no_input`, 21 = `points_vor_sleeper_seeded`** (board priced n=313 of 1043).
- Not rescued, but not the shipped default: with season sums (app.py passes `snapshot.get("season_projections") or None` on every rerun), **all 32 price** on `points_vor_sleeper_season_scored` (identity_basis NaN for the 11 — priced by player_id, no name match needed). The fallback is a real degraded production state: sleeper_client.py:593-607 sets `season_projections = {}` on any fetch exception ("degrade, never abort") and pre-#180 snapshots lack the key.

---

## CLAIM 5 — one player splits into two canonical records via per-file `_identity_hint`; `_resolve` picks by frame order. **Mechanism STANDS for exactly one player; the pricing consequence is OVERSTATED (≤0.12 universal-value points, rank_on_board unchanged).**

- data_merger.py:1284 stamps `_identity_hint` from `norm_name.duplicated()` WITHIN one file; :1605/1753 the dedup key is `norm_name|group|hint`. te_premium_dynasty_rankings.csv lists "K Williams RB LAR" and "K Williams WR NE" → hint "RB"; every other offensive export lists only the RB → hint "". Result: two `k williams|offense|LAR` records in **all 12 format hints (n=1 group each; the only same-name/same-team/same-group duplicate in the 775-row table)**. Observed production pool row (`build_available_pool`): Kyren Williams (8150) joined via `key`, `match_candidates=2`, `match_verified=False`, to `iloc[0]` of the frame.
- Which record wins is frame order, and it is the LOWER-precedence file (by the merger's own `_format_match_score`) in 5/12 hints: all three superflex non-TEP hints (te_premium file, score 1.0, beats dynasty_ppr_superflex, score 6.0) and half_ppr/ppr non-SF with te_premium=True (dynasty_ppr, 4.0, beats te_premium, 6.0). In 12T_standard the right file wins.
- Downstream disambiguation: none (`identity_basis` = "ambiguous" is emitted, draft_room.py:3337, and read by nothing else). `_drop_contested_identities` does not apply (one player, not two).
- Consequence on the production (season-sum) board — A/B removing one record at a time, same process: 12T_ppr_SF prod uv 80.06 / tha −6.62 (3yr 458) vs 80.18 / −6.50 with the score-6.0 record (3yr 463); **rank_on_board 51 in all arms**. 12T_standard: right record already wins (uv 75.54, rank 17; the other would give 77.78, rank 16). 12T_ppr, TEP, F&F: both records carry identical projection/proj_3yr → **zero numeric difference** (only trade_value 30 vs 35 differs, unused on the points path). On the vendor-only fallback the `projection` gap is 233 vs 235 (SF) — also small.

---

## Summary table
1. Populations: STANDS (−3.71 vs −0.02, n=259). Ordering: OVERSTATED — pick unchanged 16/16 states.
2. STANDS — 48/48 candidates populated, rendered by app.py:1545/5660 + opportunity_cost/EVoW; reachable only via a provider-backed debate; board component suppresses.
3. STANDS — 6 rosters over per-position bound (20 excess), 7 over joint bound (29), 7 TE / 7 WR rosters too, structural_findings=0. Refinement: per-position `slots_reachable+1` is valid but loose; the joint group bound is the tight derivable one.
4. STANDS — 11/32 unresolved; 11 `no_priceable_input` on vendor-only; all 32 priced on the shipped season-sum path.
5. Mechanism STANDS (Kyren Williams, all 12 hints; wrong file wins in 5). Consequence OVERSTATED: ≤0.12 uv, 0 rank change, "ambiguous" label only.

Probe files (scratchpad): p0_merger.py, p1_claim1.py, p1b_claim1.py, p1c_middraft.py, p2_claim2.py, p3_claim3.py, p3a_synthetic.py, p4_claim4.py, p5_claim5.py, p5b_kyren.py (labels inverted — superseded by p5c_pool.py), draft_light_idp.py → light_idp_raw.json (168 picks).
