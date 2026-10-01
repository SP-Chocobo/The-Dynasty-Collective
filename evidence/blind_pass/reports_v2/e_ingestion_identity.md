# Pass E — ingestion, identity, provenance, vintage (wave 1)

Reproduced verbatim from the agent's hand-back. Not edited, not corrected. Finding 1 (Kyren
Williams) was later NARROWED by the SKEPTIC — mechanism confirmed in all 12 format hints, consequence
measured at ≤0.12 universal-value points with no rank change on the shipped path. Finding 2 (team
defenses) was confirmed but SCOPED to the vendor-only fallback: all 32 price on the shipped
season-sum path. Finding 4 (vintage) is the one that corrected my own published claim. See
`skeptic.md` and `FINDINGS_V2.md`.

---

# Ingestion / identity / provenance / vintage audit — read-only pass

## Contamination and setup statement

- **No forbidden path was opened.** I did not read FREEZE_RECORD.md, FREEZE_RECORD_V2.md, FREEZE_CHECKLIST.md, POST_AUDIT_PLAN.md, DOC_INDEX.md, or anything under evidence/smoke_seats, evidence/batteries, evidence/blind_pass, evidence/design_35, evidence/upside_gap. I also left the evidence/DESIGN_35_*.md files at the evidence root unopened. I read source, tests, data/, data/league_captures, evidence/capture_provenance/README.md, and the three baseline provenance JSONs.
- **Branch note.** The worktree was on `main` (cf8fa0c), which has no draft_battery.py / run_draft_battery.py / league_config.py / data/fixtures. The codebase described lives on `claude/fantasy-football-control-center-ff6qlu` (765 commits ahead). I ran `git checkout --detach` onto that branch in the worktree (8c3ec34) so the audit is of the code the task describes. No file was modified; all probes ran from the repo root with the prescribed fixture.

Every finding below was reproduced with a probe on the committed capture (`data/fixtures/sleeper_capture.json`, captured 2026-09-07, season 2026, 6,595 players, 5,346 stat lines) under the owner's real format (superflex, rec=1.0, no TE premium).

---

## Findings, ranked

### 1. HIGH — `_identity_hint` splits one real player into two canonical records; resolution then picks by frame order, and the owner's league prices Kyren Williams off the worst-matching export
**Where:** `data_merger.py:1283-1284` (hint stamped per file), `data_merger.py:1596-1600` (dedup key = `norm_name|group|hint`), `data_merger.py:2371-2381` (`iloc[0]` on multiple key matches).

**What is wrong:** The hint is stamped per FILE: a name is "contested" only in a file that lists it twice. `te_premium_dynasty_rankings.csv:247` carries a blank "just-missed-the-cut" row `K Williams,NE,WR,,,,` beside the real Kyren `K Williams,LAR,RB` row, so that file's Kyren row gets hint `RB`; the other five files carry him with hint `""`. `_reconcile_rows` therefore builds TWO reconciled rows for one man (`k williams|offense|RB` and `k williams|offense|`), each carrying a different file's numbers. `_resolve` then finds 2 key candidates (both RB, both LAR — team/position narrowing cannot separate them) and returns `iloc[0]`.

**Failure scenario (measured):** owner's SF-PPR format → `merger.merge_player("Kyren Williams", "RB", "LAR")` returns `match_verified=False, match_candidates=2` and the row from `te_premium_dynasty_rankings.csv` (format score 1.0 — 1QB TE-premium): rank 55, trade_value 35, proj 233/458. The correct `dynasty_ppr_superflex_rankings.csv` row (score 6.0) says rank 69, trade_value 30, proj 235/463. Which of the two wins depends on pandas frame index order, not precedence; in 1QB PPR the right one happens to land first. The `match_verified=False` signal is emitted and nothing downstream acts on it. `grep _identity_hint test_*.py` → 0 hits: the mechanism has no test. Any name that is contested in one export and clean in another reproduces this.

### 2. HIGH — 11 of 32 team defenses cannot resolve to their transcribed row (multi-word city names defeat `name_key`)
**Where:** `data_merger.py:250` (`name_key` = first initial + everything after the first token), `data/baseline/rankings/sleeper_dst_projections.csv` (names like `P Eagles`, `G Packers`).

**What is wrong:** Sleeper's DEF name is "Green Bay Packers" → key `("g", "bay packers")`; the CSV row `G Packers` → `("g", "packers")`. Exact and fuzzy paths never fire either (no fuzzy match fires at all on this universe — see nulls). Misses: GB, KC, LAC, LAR, LV, NE, NO, NYG, NYJ, SF, TB.

**Failure scenario (measured, DEF-bearing league):** with `season_projections` the 11 still price via Sleeper points (`points_vor_sleeper_season_scored`) but carry no `trade_value`/`projection`/`source_file`. On the fallback path app.py documents at 5428-5430 ("Absent (no sync, or the fetch failed) … falls back to the vendor total exactly as before"), the board prices 21 defenses `points_vor_sleeper_seeded` and marks the other 11 `no_priceable_input` — including the Los Angeles Rams, the best-projected DEF in the pool (138.4 league points). The "32 defenses seeded from league-scored Sleeper projections" supply is 21 at the identity layer. No test uses a multi-word DEF name (`grep "Green Bay\|Packers\|New York Giants\|Kansas City" test_*.py` → none).

### 3. MEDIUM-HIGH — the league's kicking rules cannot reach Sleeper's stat line: 50+ yard makes and most misses are never scored
**Where:** `player_universe.py:194` (`score_projection` multiplies only keys present in both), capture stat vocabulary vs `league_shape.scoring_settings`.

**What is wrong:** Sleeper's projection carries `fgm` (total makes) and buckets `fgm_0_19/20_29/30_39/40_49` but **no `fgm_50p`**, and `fgmiss_20_29/30_39/40_49` but **no aggregate `fgmiss`**. The owner's league scores by bucket (`fgm_50p: 5`, `fgmiss: -1`) and has no `fgm` key. Measured over 35 kickers: 34 of 35 have `fgm` exceeding the bucket sum by ≥1; 5.5–8.8 projected 50+ makes per kicker (Aubrey 8.8, Cam Little 8.8, Reichard 7.8) are worth 28–44 points each — 25–35% of a kicker's total — and are never scored (973 points across the pool). Projected misses ≈5.4 per kicker, bucketed misses ≈2.0, so ~3.4 misses/kicker go unpenalised. Long-range kickers are systematically underpriced relative to short-range ones, and the K ordering the streaming floor is built on is distorted. DEF has the same shape: `pts_allow_0/1_6/7_13` (10/7/4 points) have no projection key for any of 32 defenses. The #180 comment measured key reachability for the VENDOR total ("57 of 64 keys unreachable") but no census exists for the Sleeper line; `pricing_census` (run_draft_battery.py:160) only asks "does it price > 0". Test fixtures (`test_kdst_integration.py:697,717`, `test_sleeper_client.py:177,187`) all assume `fgm_50p` is present in the stat line, which the real capture contradicts.

### 4. MEDIUM — the battery pairs season sums from 2026-09-07 with weekly lines captured 2026-09-22 and calls it "vintage-matched"
**Where:** `run_draft_battery.py:94-139` (`weekly_projections_from_capture` falls back to `capture_weekly_lines.load_season(season)` keyed on the season label only), `data/fixtures/weekly_projections_2026.json.gz` (`captured_at: 2026-09-22T05:58:05Z`).

**Failure scenario (measured):** scoring each player's 18 weekly lines under the league's rules and comparing with the capture's season sum: 971 of 5,346 players differ by >0.5 points; Jayden Reed 248.2 (season sum) vs 171.0 (weekly, weeks 3-4 now zero); 4,075 players exist only in the weekly file. The K/DEF streaming floor (`draft_room.streaming_replacement_levels`) is therefore derived from a different world than the season totals it is subtracted from — exactly the "two fetches, two seasons' worth of drift for one claim (#79)" the production `sync_league` avoids by keeping both from one fetch. Nothing compares `captured_at` between the two files (`grep captured_at draft_room.py draft_battery.py draft_simulation.py pick_synthesis.py` → none; run_draft_battery only records the capture's). Every battery run since #30 was wired certifies on this mix.

### 5. MEDIUM — cross-format field fill in `_reconcile_rows` is silent, unrecorded, and untraceable for rank/trade_value
**Where:** `data_merger.py:1627-1647` (first non-null per column across precedence order; conflict recorded only when two NON-null values disagree; `_source` companion written for projection/proj_3yr only).

**What is wrong:** The exports contain blank name-only rows ("just missed the cut": 17/5/5/4/17/15 rows in the six offense files, 349 of 425 in each IDP `.corrected` file — the IDP figure is already known, `test_idp_supply_boundary.py:13`). When the best-matching file's row is blank, every field is filled from the next file, which is a different FORMAT. Measured in the owner's SF-PPR format: Alvin Kamara's winner row is the SF-TE-premium blank; rank 241 / trade_value 0.0 / proj 108 / proj_3yr 629 all come from `te_premium_dynasty_rankings.csv` (1QB). 6 rows × 4 fields filled this way, 0 entries in `reconciliation_conflicts`; a further 36 of 285 offense rows come wholesale from a non-matching export (15 SF-standard, 9 1QB-TEP, 7 SF-TEP, 5 1QB-standard) with only `source_file` to say so. Tracing Kamara's rank back from the pool: `source_file` names `dynasty_te_premium_superflex_rankings.csv`, whose row is empty — the hop that the "trace a value to its column" test relies on is broken for rank and trade_value.

### 6. MEDIUM — the season-sum coverage record is written and read by nobody; a partial sum silently outranks a full-season vendor total
**Where:** `sleeper_client.py:395-452` (`_sum_weeks` records `weeks_answered/failed/season`), `sleeper_client.py:597-606` (stored in the snapshot), `draft_room.py:2681-2740` (`_derive_points_and_source`: season-basis Sleeper total wins over the vendor total wherever it exists). `grep season_projection_coverage app.py draft_room.py pick_synthesis.py draft_battery.py` → no reader.

**Failure scenario:** the undocumented projections endpoint (sleeper_client.py:283 says it "could change or disappear without notice") answers weeks 1-11 and fails 12-18. Every player with a stat line is priced from an 11-week sum; players without one (vendor-only) keep 17-week vendor totals; replacement levels and VOR mix the two scales with no marker. The docstring's own contract ("A consumer must read the coverage before trusting a total") is unenforced. Related: the sum includes already-played weeks (it is a season total, not rest-of-season) — fine for a preseason startup, wrong for any in-season use of the same number.

### 7. MEDIUM-LOW — vendor identity is lost to team drift, including one pure vocabulary case in a committed CSV
**Where:** `data_merger.py:2381-2400` (key-path team rejection), `data/baseline/rankings/sleeper_kicker_projections.csv` (carries vendor code `JAC`; `TEAM_ALIASES` at data_merger.py:322 only runs inside the PDF parsers).

**Measured:** 120 Sleeper players at the SAME position have a same-key vendor row on a different team and are rejected; 10 of them carry >50 league points (Boutte 160.8, Grupe 116.8, J. Campbell 116.6). Cam Little (K, JAX, 123.6 pts, top-10 kicker) is rejected because the transcribed row says `JAC` — a code mismatch, not a move. The other cases are real August moves and the rejection is by design, but the cost is not surfaced anywhere ("N players lost their vendor price because the vendor file predates their move").

### 8. LOW — the battery's universe and pricing inputs are outside the hashed input set
**Where:** `baseline_manifest.py:56-59` (`DECLARED_INPUT_DIRS` = data/baseline, data/projections/_global). `python3 baseline_manifest.py` → "matches (22 files)". `data/fixtures/sleeper_capture.json` and `weekly_projections_2026.json.gz` — the universe and projections every battery number rests on — can change without the manifest noticing.

### 9. LOW — the config gate is unwired, and would block every real league if wired
**Where:** `league_config.py:114` (`FORMAT_DECIDING_KEYS` includes `bonus_rec_te`), `admits_decision`/`decision_config`. `grep` shows no production caller (pick_synthesis.py:319 and draft_battery.py:946 mention it in prose only). `ambiguities()` on the capture's real league → `missing_format_keys ['bonus_rec_te', 'num_teams']`; on all 36 battery arms → flagged. Sleeper omits `bonus_rec_te` when no TE bonus is configured, so the gate as written treats every non-TEP league as AMBIGUOUS.

### 10. LOW — sync season is the NFL state's, not the league's, and nothing compares them
**Where:** `sleeper_client.py:546` (`season = nfl_state.get("season") or league.get("season")`). The coverage record carries its own `season` (sleeper_client.py:443) and no consumer reads it. A prior-season league activated from a cached id (`app.py:2482` `load_latest_snapshot(lid)`) is synced against current-season projections and last season's rosters with no marker.

### 11. Code-style observations (no measured failure)
- `reconciliation_conflicts` (3,718 per load in the owner's format) is surfaced nowhere in app/pick_synthesis.
- `load_all` swallows parse exceptions for uploads (`data_merger.py:1212`) and app.py emits no "file skipped" message; a malformed league upload silently leaves the baseline in force.
- `load_projection_file` (`data_merger.py:1074`) takes row 0's `source_date` for the whole file and overwrites every row with it.
- `measurement_basis` (`data_merger.py:1386`) is keyed on two literal filenames; a league-scored file regenerated via `write_baseline_projection_csv` under any other name is labelled `draftsharks_vendor` (confidence 80) — latent, no caller today.
- `league_format_hint` (`draft_battery.py:259`) maps rec=0.75 to "standard" (as does `league_format_summary`).
- `sleeper_import_report.write_fixture` keeps players by RAW `position in FANTASY`, while `player_position()` deliberately reads `fantasy_positions` first because raw position can be a sub-code; any such player is absent from the battery universe. Unmeasurable offline.
- The trade-value chart is a single PPR/1QB file used for every format (pick prices in a superflex league come from a 1QB chart).

---

## Well-supported null results (areas examined carefully)
- **Format hint plumbing app→merger is correct**: app.py:3558 maps "Full PPR"/"Half PPR"/"Standard" to the keys `_rankings_format_match_score` compares; battery uses the same rules.
- **Match paths on the real universe**: 100% of vendor matches are `key` path; 0 `exact`, 0 `fuzzy`, 0 `alias`; exactly one `match_verified=False` (finding 1). The Bijan/Brian Robinson and Josh Allen QB/DL cases resolve correctly.
- **Team-code vocabulary** is otherwise aligned with Sleeper (JAX/LV/LAR/WAS); `JAC` occurs once (finding 7).
- **One-basis-per-position** works as documented: K prices on the 37-row transcribed file, the 13 vendor kicker rows are dropped and recorded as `single_basis_per_position` conflicts.
- **Capture coverage** is complete (18/18 weeks answered) and every projected id exists in `players`.
- **Input manifest** matches disk for the 22 declared files.
- Valuation math, the absence contract's downstream consumers, the test apparatus and roster geometry were not examined (other lenses).

## Probe scripts (scratchpad, not in repo)
`/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/p1_capture.py … p9_fgm.py` — each runs with `PYTHONPATH=. python3 <script>` from the repo root and reproduces the numbers above.
