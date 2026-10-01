# Wave 2 — application layer: Streamlit state, caching, what the user sees

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

I verified two of these myself by grep before relaying them: `get_draft_picks` has exactly one call
site in `app.py` (finding 1), and `debate_attached_context` is written at 1484, read at 6531, and
absent from `build_context`'s signature (finding 4). See `FINDINGS_V2.md`.

---

# Adversarial audit — application layer (Streamlit state, caching, what the user sees)

## Setup disclosure
- The assigned worktree was STALE: HEAD cf8fa0c, `draft_room.py` 2051 lines, `draft_battery.py` / `league_config.py` / `invariant_registry.py` missing.
- I reconstructed the correct tree with `git archive c638c05a2ec97789e83c3e62e236c6a9098b9c1f` (`claude/fantasy-football-control-center-ff6qlu`) into `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/repo/` (`draft_room.py` 4445 lines, `app.py` 6924 lines, all three files present). All line numbers below refer to that tree. The shared checkout was not modified; no files were written outside the scratchpad (one probe script).
- I did not open any forbidden path (FREEZE_*, POST_AUDIT_PLAN, DOC_INDEX, evidence/*). I printed no commit subjects (used `--format='%H %D'`).
- One probe ran: `scratchpad/probe_fp.py` (players_db fingerprint equality). No test suite run.

## Findings, ranked

### 1. Live Draft Room picks are never fetched automatically; the board renders the pre-draft world as "ON THE CLOCK" until the user clicks Refresh Picks — MEDIUM-HIGH
- `app.py:5327` is the only call to `get_draft_picks` in the app (behind the `↻ Refresh Picks` button). `app.py:5349` `draft_picks = st.session_state.draft_room_picks_by_draft.get(draft_id, [])`; `:5351` `current_index = len(draft_picks)`; `:5372-5376` derive `pick_label`/`is_live`; `:5533` header says `ON THE CLOCK — {pick_label}`.
- `draft_room_picks_by_draft` is (correctly) wiped on every league switch by `draft_state.clear_league_derived`, so the reset to zero picks recurs on each switch back.
- The draft picker (`:5286`) shows Sleeper's `status` in its label only; nothing gates on it.
- Failure scenario: a live draft is in round 4; user opens Draft Room (or switches back to this league). Board shows "ON THE CLOCK — 1.0X", every drafted player still a candidate, tag "0 pick(s) made". Nothing on screen says picks were never pulled. Same for a completed draft: it renders as live round 1. A failed Refresh (`SleeperAPIError`, `:5330`) leaves the previous picks in force with only a toast + activity-log line; no "picks as of" stamp exists anywhere on the board.

### 2. Snapshot cache and anchor caches ignore `injury_status`, `status`, `years_exp` in `players_db`, all of which the board reads — MEDIUM
- `draft_room.py:2815-2822` `_players_db_fingerprint` hashes only `position|team|fantasy_positions`. It is the fingerprint used by both the module-level `_ANCHOR_CACHE`/`_ROSTER_POINTS_CACHE` (`anchor_cache_key`, `:2825+`) and the session `draft_room_snapshot_cache` (`pick_synthesis.py:1915-1918` `_INPUT_FINGERPRINTERS`).
- But the pool build reads `info.get("injury_status")` (`draft_room.py:1493`, `:1512`, then `health_penalty` at `:4193`) and `_admits_to_pool` reads `status` and `years_exp` (`:1269-1275`). Probe confirmed: two players_db dicts differing only in status/injury_status/years_exp produce identical fingerprints.
- `app.py:3642` calls `get_players()` on every rerun; `sleeper_client.py:204-210` refetches once the daily cache ages out, so the dict genuinely changes underneath a running session.
- Failure scenario (slow/dynasty draft, hours per pick): user sits at pick 2.03; players cache rolls over and a candidate's `injury_status` flips to "Out" (or `status` to Inactive/Retired). Every rerun hits `draft_room_snapshot_cache` (`app.py:5455-5457`) because no key input changed; the board keeps the pre-injury price, while the freshness manifest (`app.py:1716`, `players_freshness_entry`) reports the players database as fresh. The stale board persists until the next pick lands (picks are in the key). The module-level anchor caches (8 entries, process lifetime) likewise keep pre-change replacement levels across every league in the process.

### 3. A debate result and its `previous_snapshot` survive pool-scope and draft-picker changes; the only gate is `pick_label`, and the staleness note cannot see either change — MEDIUM
- Gate: `app.py:5620-5621` `debate_result.pick_label == pick_label`. Staleness: `pick_debate.staleness_note` → `pick_synthesis.stamp_is_current` (`:2040-2062`) compares only `len(picks)` and `merger.freshest_date`.
- Pool scope changes at `app.py:5345` and draft selection at `:5286` touch neither `draft_room_debate_result` nor `draft_room_last_snapshot`. The snapshot cache is correctly keyed by scope and draft_id; the debate state is not.
- `pick_debate.py:771` diffs `previous_snapshot` unconditionally.
- Failure scenario A: at 2.03 with "All players", run debate → "Recommendation: Bijan Robinson". Switch pool to "Rookies only". Board rebuilds (Bijan absent); directly under it "## Recommendation: Bijan Robinson" renders with NO staleness warning (same pick count, same data date). Clicking Debate again feeds the all-players snapshot as `previous_snapshot`, so "What changed since your last debate?" lists every veteran as "no longer a live candidate".
- Failure scenario B: league with two drafts (last year's completed startup + this year's rookie draft, both unfetched → both at 1.0X). Debate on one, pick the other in the draft selector: the first draft's recommendation renders under the second draft's board, unannotated.
- Mock Draft has the identical shape: gate `:5182-5187`, scope control `:4905` clears nothing.

### 4. The "💬 Debate" chip's attached ScreenContext is displayed but never sent to the panel — MEDIUM
- `app.py:1469-1487` stores `debate_attached_context`; `:6531-6537` renders "💬 **Considering:** …" plus a "Full evidence" expander. That is the ONLY consumer in the codebase (grep across all non-test .py). `build_context` (`:1784`) does not take it; the prompt assembly at `:6663-6730` passes `build_context(snapshot, roster_table, player_universe, trigger_question)` only.
- The dock's own comment (`:6525-6530`) says the line should read as "Debate already understands what I was looking at".
- Failure scenario: user clicks the chip on the Draft Room board ("Considering: On the clock for pick 2.03"), types "who should I take here?". The panel receives roster/league context with no board, no candidates, no pick position, and answers from general data — potentially naming a player already drafted. The UI text asserts the opposite. (If the chip is intended as a doorway only, the "Considering" line and expander are the misstatement.)

### 5. Season-projection coverage is recorded but no consumer reads it; partial or failed projection fetches silently reprice the board — MEDIUM
- `sleeper_client.py:598-608` records `season_projection_coverage` (`weeks_failed`, `error`) and degrades on any exception. The snapshot comment (`:619-622`) says "A consumer must read the coverage before trusting a total". grep: no non-test module outside sleeper_client/sleeper_import_report reads `season_projection_coverage` or `weeks_failed`; `app.py` never references it.
- `app.py:5441` passes `snapshot.get("season_projections") or None`: an empty dict silently flips the whole board to the vendor basis.
- Failure scenario: user hits Refresh (`app.py:3535`); the reverse-engineered projections endpoint answers 11 of 18 weeks. Every season sum is ~60% of true, replacement levels and prices shift, header says "synced just now", and nothing on the Draft Room indicates reduced coverage or a basis change.

### 6. `import_audit` result persists across league switches under a header naming the new league — LOW
- `app.py:6003` prints "League under audit: `<current selected_league_id>`"; `:6016/:6020` store the result in `import_audit`, which `activate_league` (`:1097-1110`) never clears (not under a `draft_room_`/`mock_draft` prefix). Scrubbing is on by default so the report body can't reveal which league it describes.
- Scenario: run audit on league A, switch to B, open Maintenance: A's report renders labelled as B.

### 7. `debate_attached_context` is not cleared on league switch — LOW (display-only given #4)
- Not in `activate_league` and not covered by `draft_state` prefixes. Scenario: attach from league A's board, switch to league B; dock shows "Considering: On the clock for pick 2.03" under league B's chat.

### 8. `activate_league` first-sync failure is silent — LOW
- `app.py:1112-1116` `except Exception: pass`; the user then sees the generic "Sync a Sleeper username and select a league" empty state (`:3541-3544`) for a league they just selected, with no error and no activity-log entry.

### Code-style / UX observations (no wrong-data scenario)
- `app.py:6656` `_last_submitted != question` dedupe on a persistent `text_area`: re-asking the identical text (e.g. after a re-sync) is silently ignored until the text is edited.
- Mock Draft re-points the shared merger (`app.py:4913`) after the top-level `set_league_format` (`:3560`) reasserted the real one, so a mock with a different format performs two full `reload()`s per rerun. I checked the code that runs after the mock section (`build_context` at `:1790` reads only `is_*_loaded` flags and freshness; `roster_table`/`player_universe` are built before the re-point) and found no value leak — performance only.

## Areas examined with no finding
- `snapshot_input_key` (`pick_synthesis.py:1961-2003`): bound to `build_snapshot`'s signature, content-fingerprints merger frames and picks, refuses uncanonicalizable inputs; the one gap is #2 above. A re-sync, an upload (`reload()` changes frame content), a commissioner re-pick, and a scope change all correctly miss the cache.
- League-switch sweep (`draft_state.clear_league_derived`, `app.py:1110`): prefix-based, covers the draft picker widget key, picks cache, debate result, snapshot cache and mock state; the preference allowlist holds only display preferences. `draft_room_position_view` is re-validated against the new league's options (`:5486-5489`); `league_selected_team` (`:5859`) and `fa_sort` (`:3977`) are validated before use.
- Duplicate widget key `dock_expand` (`:6478`, `:6516`) lives in mutually exclusive branches; no collision.
- Board iframe payload escapes `<` in the JSON (`draft_board_ui.py:1011`).
- League Refresh (`:3535`) writes the new snapshot before `snapshot = st.session_state.league_snapshot` (`:3540`), so the same run uses it; `sync_league` writes atomically and a corrupt latest-file is treated as a miss.
- Attachment scope changes (`set_scope`, `attachments.py:110`) affect reference material only; the merger does not read them, so no reload is needed.
- Header freshness manifest (`:1688-1717`) shows sync age and players-DB state; the gap is that #2 makes the manifest and the cached board disagree.
