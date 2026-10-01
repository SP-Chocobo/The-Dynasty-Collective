# Wave 2 — failure paths: bad inputs, dependency failures, degenerate state

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

Its findings 1 and 2 are the third independent arrival at the unread `season_projection_coverage`
record — the ingestion lens found the record, the UI lens found the stale-header symptom, and this
pass measured the consequence. I verified the root cause myself: no module that prices reads it, and
`grep -c season_projection_coverage app.py` returns 0. Its finding 3 is the third independent
arrival at the unwired `league_config` gate.

---

# Adversarial audit — failure paths (bad inputs, dependency failures, degenerate state)

## Setup disclosures
- The worktree handed to me was STALE (`draft_room.py` 2051 lines; `draft_battery.py`, `league_config.py`, `invariant_registry.py`, `run_draft_battery.py` absent). I reconstructed the correct tree with `git archive claude/fantasy-football-control-center-ff6qlu` (commit `c638c05`, `draft_room.py` 4445 lines) into my scratchpad at `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/repo` and worked entirely there. The shared checkout was not modified. Line numbers below refer to that tree.
- `git log -1` on the stale branch printed a truncated commit-subject fragment ("Post"); I did not use it or any other subject line as evidence.
- No forbidden path was read (FREEZE_*, POST_AUDIT_PLAN, DOC_INDEX, the listed `evidence/` subdirectories). An `ls` of the repo root showed their names only.
- No network calls: every client probe monkeypatched `SleeperClient._get` / `session.get`. Probes ran against the real fixture (`data/fixtures/sleeper_capture.json`, 2026 weekly lines via `capture_weekly_lines.load_season`). Probe scripts: `/tmp/claude-0/.../scratchpad/probes/probe{1..4}_*.py`.

Fixture note for reproduction: board = `compute_draft_board(merger, players_db, [], "1", league, mode="balanced", sleeper_projections=..., sleeper_basis=SLEEPER_BASIS_SEASON_SUM)` with `league = capture["league_shape"] + {"settings": {"type": 2}}` (12-team superflex + IDP_FLEX). Both "full" and "partial" arms were re-summed from the same weekly lines so they differ only in which weeks are summed.

---

## Findings, ranked by severity

### 1. HIGH / SILENT — A partially-summed season projection is priced as a complete one, and in a superflex league it deletes every quarterback from the board.
**Where.** `sleeper_client.py:474-520` (`_sum_weeks`: a week that fails is appended to `coverage["weeks_failed"]` and the sum continues); `sleeper_client.py:343-350` (`get_weekly_projections` fails soft to `{}`); no retry, backoff or request spacing exists anywhere in `sleeper_client.py` (grep for sleep/retry/backoff: none), so `sync_league` fires 18 back-to-back requests at an endpoint the file itself calls undocumented. The coverage record is consumed only by `sleeper_import_report.py:775-810` (a CLI). `app.py:4925-4932, 5010-5015, 5074-5077, 5441-5444` pass `snapshot.get("season_projections") or None` straight into the board and never read `season_projection_coverage`. `draft_room.py:2734-2745` (`_derive_points_and_source`) then promotes the Sleeper season sum OVER the vendor's full-season total for every row ("basis-first"), so a truncated sum replaces a complete number.

**Mechanism of the QB collapse.** `draft_room.py:1682-1699` `qb_startable_floor` is an ABSOLUTE points threshold derived from the vendor's projection table (163.5 on the fixture). `draft_room.py:1836-1842` counts how many remaining QBs' `_points` (now the Sleeper sum) clear it and uses that count as the replacement rank. Fewer answered weeks → fewer QBs clear a full-season threshold → replacement rank shrinks to near the top → every QB's VOR goes negative.

**Measured (probe1/probe4).**
- Weeks 10-18 failed (a sustained 429 after the burst): 39 of the top-40 rows move ≥3 places. Jayden Daniels 31→321 (universal_value 107.34 → −38.42), Kyler Murray 27→299, Patrick Mahomes 14→163, Trevor Lawrence 5→96. QBs clearing the floor: 31 of 355 → 10 of 355. New top-10 contains zero quarterbacks in a superflex league. `bpa_source` stays `points_vor_sleeper_season_scored` on 1055 rows, `replacement_basis` stays `startable_floor`, `absence_kind` stays None — nothing on the row says anything happened.
- Weeks 1-15 (three failed): best QB falls from #1 to #3; Lamar Jackson 218 → 141.
- A single failed week (7): 9 of the top-40 move ≥3 places (players on a week-7 bye gain: Trevor Lawrence 5→2, James Cook 33→23; others lose).
- Side effect: the IR availability haircut silently disappears under partial coverage — `player_universe.py:153-160` compares summed `gp` against `SEASON_GAMES - missed`; with ≤13 answered weeks the factor is 1.0 while `availability_basis` still reads `rule_floor`.

**Failure scenario.** User clicks Refresh This League; Sleeper rate-limits requests 10-18 of the projection loop; the snapshot is written; the user drafts a superflex league off a board that says every QB is worth less than replacement. No banner, no label, no row-level marker.

### 2. HIGH / SILENT — A sync whose projection fetch fails entirely overwrites a good snapshot with a projection-less one, and nothing in the UI says so.
**Where.** `sleeper_client.py:594-610` catches `Exception` around `get_season_projections` and stores the error string in `season_projection_coverage["error"]`; `sleeper_client.py:644-650` `_write_snapshot` unconditionally replaces `{league_id}_latest.json`. `app.py:1685-1720` `build_freshness_manifest` has no row for projection coverage; grep of `app.py` for `weeks_failed|season_projection_coverage|projection_attempts` finds nothing. `app.py:1090-1116` reuses whatever `_latest.json` exists on every later activation.

**Measured (probe1, "VENDOR-ONLY").** With `season_projections` empty the app passes `None`; 1050 of 1906 rows change `bpa_source`; 31 of the top-40 move ≥3 places; Bijan Robinson goes from #6 to #1895 `no_priceable_input` (contested-identity rule on the vendor row, which the Sleeper path had bypassed); Malik Willis 17→42, Jayden Daniels 31→7. The freshness manifest reports "Sleeper league sync … 2 minutes ago" — i.e. it reads as the FRESHEST input on the page.

**Failure scenario.** Yesterday's good sync (18 weeks) is replaced by today's failed one (0 weeks, `error: "SleeperAPIError: 429"` buried in the JSON). Every board until the next successful refresh is vendor-only, while the only visible freshness signal says the sync is minutes old. The `bpa_source` column that would reveal it is, per `draft_history.py:58-63`'s own note, dropped by the board UI.

### 3. HIGH / SILENT — The league-config ambiguity gate exists but is wired to nothing; boards are built on configs the gate would refuse, and a missing `scoring_settings` silently reverts the whole league-scored pricing path.
**Where.** `league_config.py:234-259` (`admits_decision`, `decision_config` — "Never a degraded fallback", "Raises rather than returning something usable-looking"). Callers outside tests: none (`grep league_config\.\(admits_decision\|decision_config\|confirmation_state\|ambiguities\)` over non-test modules → only comments in `draft_battery.py:946` and `pick_synthesis.py:319`). `draft_room.py:3673-3680` reads `league.get("scoring_settings")` and `build_available_pool` (`draft_room.py:1455`) skips Sleeper scoring whenever it is `None`; `player_universe.py:28-50` turns an empty `roster_positions` into "every position".

**Measured (probe3, probe1-D).**
- `roster_positions = []` → 1944 rows, 0 priced, no reason on any row. `admits_decision` says False ("carries no roster_positions"); the board was built anyway.
- `roster_positions = ["BN"]*15` → same all-unpriced board.
- `roster_positions + ["OP"]` (a slot code Sleeper could add) → 820 priced rows, OP silently ignored by the lineup solver.
- `scoring_settings = None` → board is byte-for-byte the vendor-only board of finding 2 (1050 source flips, Bijan unpriced).
- Collateral defect in the gate itself: `league_config.py:204-212` requires `bonus_rec_te` and `num_teams` in `scoring_settings`/`settings`; the REAL capture league lacks both (Sleeper omits zero-valued scoring keys; the capture's `league_shape` has no `settings`), so `admits_decision` returns False on the real league. Wiring the gate as written would refuse legitimate leagues; as unwired, it protects nothing.

**Failure scenario.** Schema drift (Sleeper renames or nests `scoring_settings`) or a stale `_latest.json` from before a key existed → the board quietly prices from the vendor total with the freshness row saying the sync is fresh.

### 4. MEDIUM / SILENT — `load_all` swallows every unparsable source file and keeps no record; the merger cannot say "file present but not loaded".
**Where.** `data_merger.py:1210-1214` (`except Exception: continue`), `data_merger.py:1803-1806` (`load_external_values`, same). `DataMerger` exposes `is_loaded` (`data_merger.py:2119`) but no skipped-file list; `dir(merger)` has no attribute mentioning skip/unreadable/fail (probe3).

**Measured (probe3).** Directory of 5 files (good CSV, aliased-header CSV, fake PDF, binary bytes named `.csv`, empty CSV) → 2 loaded, 3 skipped, `is_loaded=True`, no signal anywhere. `pypdf` prints "EOF marker not found" to stderr only.

**Mitigation present.** The upload form (`app.py:2896-2899`, `3016-3020`) parses each file first and reports a parse error at upload time, so a user-dropped file does get a message once. Not covered: committed `data/baseline/**` or `data/projections/_global/**` files that stop parsing after a pandas/pypdf upgrade, a file copied in by hand, or a file corrupted on disk — each silently removes a whole source (and possibly a whole position's vendor pricing) with the freshness manifest unchanged.

### 5. MEDIUM / LOUD but STICKY (24h) — `get_players` caches any truthy 200 body; an error-shaped JSON object poisons the daily cache and the app then crashes on every rerun with no in-app way to refetch.
**Where.** `sleeper_client.py:217` (`if players:` — no shape check) then `replace_atomically` at `:229`; `:201-208` serves the cache while `age < 24h`. `app.py:3642` calls `get_players()` at top level outside any handler; grep of `app.py` for `force_refresh` finds no caller.

**Measured (probe2-A).** `_get` returning `{"error": "rate limited, try later"}` → cached; a fresh client with the network disabled returns the same dict, basis `within_window`; `player_eligible_positions` on the entry raises `AttributeError: 'str' object has no attribute 'get'`.

**Failure scenario.** One 200-with-error-body response from `/players/nfl` (a proxy or CDN error page in JSON, or Sleeper's own error envelope) → every page load fails for 24 hours until someone deletes `data/sleeper_snapshots/players_nfl.json` by hand. Loud, but not self-healing and not recoverable from the UI.

### 6. MEDIUM-LOW / LOUD (contract violation) — A 200 response with a non-JSON body escapes as `JSONDecodeError`, not `SleeperAPIError`, so the "fail soft" methods do not fail soft and the app's handlers miss it.
**Where.** `sleeper_client.py:129-142` `_get` calls `resp.json()` unguarded. `get_nfl_state` (`:322-327`) and `get_weekly_projections` (`:343-350`) catch only `SleeperAPIError` despite docstrings promising `{}`/`None`. `sync_league` (`:560`) calls `get_nfl_state()` with no guard; `app.py:2283, 2310, 2454, 3537, 5268, 5330` catch only `SleeperAPIError`.

**Measured (probe2-B).** HTML body with 200: `get_rosters`, `get_weekly_projections`, `get_nfl_state`, `get_season_projections` all raise `JSONDecodeError` (`isinstance(e, SleeperAPIError)` → False). In `sync_league` the `get_season_projections` call is caught by the broad `except Exception` (coverage error recorded — feeds finding 2); the `get_nfl_state` call is not, so the Streamlit page shows a traceback. Inside `activate_league` (`app.py:1115`) it is swallowed silently (see finding 10).

### 7. MEDIUM-LOW / SILENT (instrument) — The battery fixture reader returns `{}` for a capture without season projections despite documenting raise-on-missing, and neither it nor the battery reads the capture's own coverage record.
**Where.** `run_draft_battery.py:278-302` `season_projections_from_capture` ends `return capture.get("season_projections") or {}` (docstring: "same raise-on-missing contract as build_players_db_from_capture" — that contract covers only the file's existence). `sleeper_import_report.py:775-779` writes `season_projection_coverage` into the fixture; `run_draft_battery.py:397-500` never reads it, and `_battery_report` carries `season_projections_supplied/priceable` but not weeks answered.

**Failure scenario.** A re-capture taken during a Sleeper hiccup records `weeks_failed: [12..18]`; the battery certifies 36 arms against half-season sums (finding 1's QB collapse would then be certified as engine behaviour), reporting `priced_from: vendor+sleeper` and a plausible `season_projections_priceable`. A capture with the key absent runs `vendor_only` — that one IS labelled in the report, so it is disclosed downstream even though the function's own contract is not honoured.

### 8. LOW / LOUD, transient — `replace_atomically` uses one temp name per PID, so two threads in one Streamlit process writing the same cache collide and the loser raises `FileNotFoundError`.
**Where.** `store_io.py:245-250` (`tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")`, no lock by design); callers `sleeper_client.py:229` (players cache — two tabs both past the 24h window refetch concurrently), `:648-649` (snapshots); same pattern in `draft_history.py:102-108` `_atomic_write` (guarded by `try` at `app.py:5607-5617`, surfaces as a warning).

**Measured (probe2-D).** Two writer threads × 15 writes: 9 `FileNotFoundError`s; concurrent readers saw 0 corrupt reads of 17 (the `os.replace` guarantee holds). Readers are safe; the writing rerun errors out. `get_players` at `app.py:3642` is unguarded, so the losing tab gets a traceback for that rerun; the next rerun reads the winner's file. Self-healing, hence low.

### 9. LOW-MEDIUM / SILENT reason — First activation of a league swallows every exception and the user sees the generic empty state.
**Where.** `app.py:1111-1116` `except Exception: pass` around `client.sync_league(...)`; `app.py:3540-3544` then renders "Sync a Sleeper username and select a league in the sidebar to get started." and `st.stop()`. The absence is visible; the cause (429, non-JSON, `get_league` 404 → "League not found", disk full) is not, and the user's natural reaction — re-selecting the league — re-enters the same path.

### 10. LOW / LOUD (schema drift) — Weekly stat lines that fall back to the entry itself feed metadata strings into `float()`.
**Where.** `sleeper_client.py:334` `stats = entry.get("stats", entry)`; consumers `player_universe.py:194-205` `score_projection` and `sleeper_client.py:684-694` `compute_points_from_stats` call `float(value)` on any truthy value. If the dict-shaped projections payload ever lacks a nested `stats`, the roster screen (`app.py:3647, 3665-3672`) crashes on `float("KC")`. The season-sum path is unaffected (`_sum_weeks` skips non-numeric per category, `:496-500`). Loud; only reachable on schema drift.

### Code-style opinions (no concrete failure scenario)
- `league_format_summary` (`sleeper_client.py:851`) `settings.get("num_teams", len(league.get("roster_positions", []) and []))` — the default expression always evaluates to 0; harmless because of the trailing `or league.get("total_rosters")`.
- `get_user_leagues` falls back to a hardcoded `DEFAULT_SEASON = "2026"` only when `/state/nfl` is unreachable; correct today, wrong next year on an offline day, and the symptom would be "No leagues found" (disclosed in comments at `:24-28`).

---

## Examined and found sound
- `store_io.py`: `_parse` separates absent/empty/damaged; `write`/`mutate` refuse to overwrite a damaged store and record it in `unreadable_stores()` (surfaced by `app.py:1344-1360`); lock nesting via per-thread depth count is correct; `os.replace` semantics confirmed by probe (no torn reads under contention).
- `draft_history.py`: file-per-record, content-addressed, `record_snapshot` idempotent; damaged records skipped on read; the only weakness is the shared temp name (finding 8).
- `lineup_optimizer.py`: empty players/slots handled (`:88-89`); forced ineligible pairings filtered (`:98-99`); `bye_concentration` guards `total > 0`; NaN cannot reach the cost matrix from either producer (`_team_roster_players` drops `None` values, `roster_points_lookup` selects `has_proj` rows only). Solver would raise loudly on NaN if it ever did.
- `replacement_levels` (`draft_room.py:1701-1889`): filters to rows carrying the value column, omits rather than clamps out-of-domain positions, records truncation; `_bench_appetite_rates` guards the zero denominator (`:2105`); `starter_slot_counts` divisions guarded (`:904-915`); `remaining_starter_demand` raises on a foreign roster universe (`:1019-1023`); `_remaining_demand_rank` tolerance is principled.
- `pick_synthesis._board_order` (`:221-262`) is None-safe (unpriced last, player_id tiebreak); `_records_with_normalized_nan` normalises every column.
- Upload path (`app.py:2818-3060`, `upload_batches.py`): parse errors reported at upload; malformed/future as-of dates refused rather than guessed (`parse_as_of`); a declined batch-store write is reported, not silently dropped.
- `write_baseline_projection_csv` refuses an empty file; `capture_weekly_lines.capture_season` raises on an empty season; `get_players` raises rather than returning `{}` when nothing is available.
- Degenerate leagues: one-team league and `total_rosters=None` fall back to `num_teams=1` and build a board without error (519 priced rows); `simulate_opponent_picks` (`draft_room.py:4436`) and `simulate_full_draft` (`draft_simulation.py:177`) stop on an empty board rather than raising or looping; `remaining_draft_capacity` handles more rounds than players.
- Data-merger reconciliation (`_reconcile_rows`, `_precedence_sort_key`, `_negated_date`) handles None/NaN and undated rows without mixed-type sort errors.

## Summary of the pattern
The engine's absence contract is honoured rigorously INSIDE the board (None never becomes 0.0), but the two inputs that arrive from outside — the season-projection sum and the league config — cross into it with no companion stating their completeness, and the one companion that does exist (`season_projection_coverage`) is written to disk and read by nothing that prices. The consequence is the worst shape the brief asked about: a plausible board, correctly labelled row by row, computed from a number that was never complete.
