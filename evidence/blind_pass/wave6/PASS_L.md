# Wave 6, pass L — preserved verbatim

> **The pass's own words, unedited.** Running log: `FINDINGS_LOG.md`. Verdicts: `LEDGER.md`.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` with the six forbidden paths excluded.
> Wave 6 mandate — null standard naming the docstring-restatement failure mode, the determinism
> steer on end-to-end drafts, and steering toward the test suite as a corpus.
> **This is Wave 6's relaunch**; the first attempt died on the account session limit with no report.
>
> **Self-reported contamination: none.** Exclusions verified absent before reading.

## Report

Setup: tree extracted to `/tmp/audit_tree` with the mandated exclusions; verified `FREEZE_RECORD.md`,
`FREEZE_CHECKLIST.md`, `POST_AUDIT_PLAN.md` absent and `evidence/{smoke_seats,batteries,blind_pass}`
empty before reading. **No forbidden path was read.** Nothing in the repository was modified; probes
live in the session scratchpad. All probes ran from the tree root with
`build_players_db_from_capture()`, `season_projections_from_capture()`, the capture's `league_shape`,
and `merger.set_league_format(db.league_format_hint(league))`. I did not run the full suite or an
end-to-end draft.

Findings are ranked by severity. Each has a concrete scenario; measured ones say so. Items adjacent
to "known" areas are flagged.

---

### 1. `pick_analysis` reports a *measured* zero denial at a node where nothing was measured (absence collapse)

**Where:** `draft_strategy.py:636-690` (`estimate_survival`), `draft_strategy.py:1016-1035`
(`pick_analysis` basis selection), `draft_strategy.py:889-897` (`DENIAL_BASIS_LABELS`).

**What:** The 2026-09-16 ruling added a third survival state: no next pick → `survival_probability=None,
risk_by_team=[]`. `pick_analysis` derives `rivals_considered` by iterating `risk_by_team`; an empty
list selects `DENIAL_NO_INTERVENING_RIVAL`, which the code's own comment defines as "'no rival was
positioned to gain' is TRUE and 0.0 is a measurement", and which renders as *"no rival had a pick
before your next turn"*. At a no-next-pick node there is no next turn; every rival picks after you;
nothing was consulted. `rival_premium_basis` gets the same token.

**Measured (real league, empty draft, final pick index 299, seat holding it):**
```
survival_basis='no_next_pick', denial_value=0.0, denial_basis='no_intervening_rival',
rival_premium=None, rival_premium_basis='no_intervening_rival'
label shown: "no rival had a pick before your next turn"
```
Every seat's final pick hits this (12 of 300 picks in the owner's shape), and any seat that has traded
away late picks hits it far earlier (the module's own comment names TAmedic27 at 308/360).
`pick_debate.py:459` prints the label into the debate evidence. **Adjacent to the known `denial_value`
work (#187):** what is new is the seam with the survival third state — survival got a fourth token,
denial did not.

### 2. `pick_analysis` computes positional forfeits off upside-mode curves under `mode="auto"` — the guard tests the requested string, not the resolved mode

**Where:** `draft_strategy.py:967` — `position_curves = {} if mode == "upside" else _position_curves(my_board)`.
`draft_room.py:3005` resolves `"auto"` to upside at `current_round >= 15`; `draft_room.py:3228-3229`
resolves it to upside whenever no measurable VOR > 0. Both produce boards whose rows carry
`mode == "upside"` and `universal_value == final_score`.

**What:** The comment above the guard says forfeits are "skipped entirely in upside mode" and that
"the existing behavior is preserved here explicitly". Under `"auto"` — the mode the simulation and
every battery arm run — they are not skipped once the board resolves to upside. The curves are then
upside-score curves fed into a normaliser (`FORFEIT_SCALE_MAX = 100`) calibrated on VOR-scale curves.

**Measured (real league, synthetic 169-pick drain so the board's `mode` column reads `upside`,
`pick_analysis(mode="auto")`):**
```
AJ Barner   TE  positional_forfeit=85.71  position_expected_taken=14.2
RJ Harvey   RB  positional_forfeit=37.98  position_expected_taken=10.0
```
`mode="upside"` at the identical state yields `None` for all. Downstream, `pick_synthesis.py:655-659`
turns 85.71 into `0.857 × NECESSITY_FORFEIT_WEIGHT = 8.6` necessity points (3.8 for RB). Necessity has
no selection authority (#55) but drives the MUST TAKE / STRONG ACTION labels that
`draft_counterfactual.classify_deviation` counts as "supported" deviations and that battery qualifier
profiles report. Live UI (`build_snapshot` default `"balanced"`) is unaffected; every `"auto"`
trajectory from round 15 pick 2 onward is affected. Adjacent to the known upside-mode work; the defect
is in `pick_analysis`, which was flagged unexplored.

### 3. `draft_counterfactual.compare_trajectory` prices BPA on a different board than the engine priced its pick on, and two of its "by construction" claims are false

**Where:** `draft_counterfactual.py:92-93` (`_full_board`), `:137-201`, `:77`.

(a) **No pricing path.** `compare_trajectory` takes no `sleeper_projections`/`sleeper_basis`;
`_full_board` calls `compute_draft_board` vendor-only. `engine_tav` is read off the trajectory's
snapshot, which since #204 is built scoring-aware (`draft_simulation.py:199-201` records
`priced_from="vendor+sleeper"`). `regret_vs_bpa = engine_tav - bpa_tav` therefore subtracts a
vendor-only TAV from a vendor+Sleeper TAV — the #214/F2 "two prices for one candidate" defect, in an
instrument. `config["priced_from"]` is recorded and never checked. Scenario: feed any battery
trajectory to `run_counterfactual_analysis.py`; it will run and report regret numbers that mix two
pricings. (Not measured: no trajectories are committed under `data/draft_simulation_trials/`; the test
fixture is vendor-only, so it cannot see this.)

(b) **`regret_vs_bpa >= 0 by construction (engine always TAV-argmax)`** (`:77`) is false.
`pick_synthesis._board_order` (`:239-241`) sorts `fills_required_slot` ahead of `final_score`; when the
feasibility backstop binds the engine takes a non-argmax candidate. `draft_room.py:2866-2868` records
it binding 2 of 112 and 2 of 196 picks in real arms. `test_regret_vs_bpa_is_never_negative` passes on a
4-team × 2-round fixture where the backstop cannot bind. Not measured by me.

(c) `upside_rule` (#261) is not forwarded by `_full_board`; a CROSSING-rule trajectory is compared
against ROUND-rule boards.

### 4. A CSV whose `source_date` column exists but is blank is dated `NaN`, labelled *declared*, and outranks genuinely undated rows

**Where:** `data_merger.py:1039` (`iloc[0]` → `np.float64(nan)`), `:1084-1086`
(`resolve_source_date(None, nan)` returns `nan`, which is truthy; `nan or ""` keeps `nan`; `date_basis`
returns `DATE_DECLARED`), `:1210` stringifies it to `"nan"`, `:1363-1366` `_negated_date("nan") == "nan"`
which sorts before the undated sentinel `"~"`.

**Measured:** `source_date repr np.float64(nan) | basis declared`; `_negated_date('nan') < _negated_date('')`
→ True. So a template-style export with an empty date column wins a precedence tie against a file the
user honestly left undated, and its basis says a date was declared. `_recency_weight("nan")` falls to
0.5 via the `except ValueError`; `composite_player_score`'s age loop also catches it — so no crash, just
a wrong basis and a wrong tiebreak. (Against a genuinely dated row the dated row still wins — also
measured.) `upload_batches.parse_as_of` protects only the *stated* path; the *declared* path is
unvalidated.

### 5. `outcome_record.load` collapses "damaged" into "absent"; the revision trail is silently wiped and `--list` crashes

**Where:** `outcome_record.py:294-301` — `except (json.JSONDecodeError, OSError): return None`;
`:265-272` `capture` then sees `existing=None` → `revisions=[]`; `:346-350` `main --list` does
`record['revisions']` on the `None`.

**Measured:** after truncating a valid record file, `load()` → `None`; `weeks()` still lists the week;
re-`capture` writes `revisions=[]` (the prior fingerprint is gone); `store_io.unreadable_stores()` is
`{}` because `load` bypasses `store_io.read`, so the damage guard that `store_io.write` relies on never
arms; the `--list` path raises `TypeError: 'NoneType' object is not subscriptable`. The module's own
guarantee — "a correction is VISIBLE rather than silent … `n_players` moving without a revisions entry
would mean something rewrote the file outside this function" — is violated by the function itself. No
test exercises a damaged file (checked `test_outcome_record.py` names/keywords).

### 6. Draft Room session state leaks across leagues; the staleness stamp carries no league or draft identity

**Where:** `app.py:1084-1110` (`activate_league` resets chat/snapshot/merger but none of the
`draft_room_*` keys); `app.py:4682-4684`, `5513-5519`; `pick_synthesis.py:1633-1658` (`stamp_is_current`
compares only `picks_consumed` and `merger.freshest_date`). Grep confirms nothing ever sets
`draft_room_debate_result`, `draft_room_last_snapshot` or `draft_room_snapshot_cache` back to `None`.

**Scenario:** two leagues mid-startup (common). In league A at pick label `2.03` with 14 picks made, run
the Prytaneum debate. Switch to league B, whose draft is also at your `2.03` with 14 picks made.
`debate_result.pick_label == pick_label` passes; `stamp_is_current` sees 14 == 14 and the same
`freshest_date` (the rankings pool is shared unless B has league-specific uploads) → league A's debate —
A's candidates, A's recommendation — renders under B's board with **no staleness note**.
`draft_room_last_snapshot` from A is also passed as `previous_snapshot` into B's next debate diff. Not
measured (requires Streamlit); every branch was read.

### 7. The Draft Room snapshot cache key omits inputs that change the board

**Where:** `app.py:5366-5369` — key is `(draft_id, target_index, my_roster_id, pool_scope,
len(draft_picks), merger.freshest_date)`.

Missing: pick **contents** (a commissioner undo + re-pick keeps `len` constant → stale board after
"Refresh Picks"); `snapshot["season_projections"]` (a re-sync changing Sleeper's projections does not
invalidate); and any upload whose `source_date` is ≤ the current max or blank (`freshest_date` is
`max()` over parseable dates, `data_merger.py:1618-1627`) — e.g. uploading a corrected file dated the
same day as the existing freshest keeps serving the old board until a pick lands. Same weakness in the
debate stamp (item 6).

### 8. Test corpus: three live valuation constants can be set to absurd values with the relevant tests green (measured by in-process mutation, ~275–307 tests each)

| mutation | tests run | outcome |
|---|---|---|
| `draft_room.NEED_BONUS_PER_FLEX_SHARE = 0.0` | test_draft_room, test_demand_decomposition, test_pick_synthesis, test_216_displacement, test_216_flex_share, test_cdme_metamorphic (307) | **all pass** |
| `pick_synthesis.NECESSITY_RUN_BONUS = 500.0` | test_pick_synthesis, test_draft_strategy, test_pick_debate, test_draft_board_ui, test_threshold_reachability (275) | **all pass** |
| `draft_room.TIME_HORIZON_SLOPE = 0.0` | test_draft_horizon, test_draft_room, test_pick_synthesis, test_bpa_unit, test_valuation_leaf_explains_itself, test_cdme_metamorphic (277) | 1 *error*: `StopIteration` at `test_draft_room.py:1461` in a fixture search for a "young rising" player. No assertion about the adjustment fired; `test_draft_horizon` passed entirely. |

The flex-share constant is not dead: on the real league, RB `need_bonus` goes 0.38 → 0.00 after my two
RB picks, and **every IDP position's need (0.67) comes entirely from it** — IDP_FLEX is flex-only — so
zeroing it removes the whole positional-need signal for LB/DL/DB and nothing notices.
`NECESSITY_RUN_BONUS` is reachable whenever 3 of the last 4 picks share a position
(`detect_positional_run`), which real drafts produce routinely. No test file names
`NEED_BONUS_PER_FLEX_SHARE`, `TIME_HORIZON_SLOPE`, or `NECESSITY_RUN_BONUS` (grep over `test_*.py`).

### 9. `need_bonus` docstring vs formula: flex demand is counted before dedicated slots are filled

**Where:** `draft_room.py:119-120` ("flex demand only counts once a team's dedicated slots are already
filled"), `:472-474` (same claim), vs `:3403-3413` — `flex_remaining = flex_share - max(filled -
dedicated, 0)` is positive at `filled=0`, so the share is added immediately.

**Measured:** empty roster → RB 8.38, WR 8.38, QB 4.85, TE 4.38 (dedicated-only would be 8.00 / 8.00 /
4.00 / 4.00). Small magnitude; direct contradiction of two prose claims.

### 10. The reconciliation conflict ledger names the wrong rule

**Where:** `data_merger.py:1466-1476` — `reason = _conflict_reason(winner, candidate)` where
`winner = ordered[0]`, but `chosen_value` may come from a lower-ranked row when the winner's field is
null (that is the whole point of the field-level merge).

**Measured** (three one-row frames, same basis): winner has best format score and a null `trade_value`;
two others share format 0.5 and differ only in date. Ledger records `chosen_source=second_newer.csv,
discarded_source=third_older.csv, reason='format_match'` — the two files in conflict have identical
format scores; recency decided. "Naming it is the point" (`:1379-1382`) — and the name is wrong exactly
when the winner contributed nothing.

### 11. `upload_batches.record` returns a batch id for a batch that was never persisted

**Where:** `upload_batches.py:108-131` calls `store_io.write`, which (`store_io.py:208-222`) returns
silently when the store is marked unreadable; `record` still returns `batch_id`. `app.py:3021` proceeds
as if recorded.

**Scenario:** `data/projections/_uploads.json` is torn by a crash. Every subsequent upload moves its
files into the pool, the UI reports success, and the user's **stated as-of date is dropped** —
`stated_as_of()` returns `None` for those files, so the "stated > declared" precedence the module exists
to provide silently degrades to "undated loses every tie". `store_io` itself is known; the unmet
contract is `record`'s. Not measured.

### 12. `doc_index` files a document that says "Nothing in this file is withdrawn" under WITHDRAWN

**Where:** `doc_index.py:36-45` — stem regex `withdraw|retract|⛔` over the first 12 lines, first match
wins.

**Measured** (tree walk, `classify()` directly): 25 WITHDRAWN; false positives include
`evidence/roster_proof/README.md` (banner: *"Nothing in this file is withdrawn. Every number below was
correctly measured and reproduces."*), `evidence/roster_shape/ff_rulebook/ADVISORY_fable_symmetry_break.md`
and `PHASE4_ABLATION_RESULT.md` (they cite a WITHDRAWAL file by name), and
`evidence/survival_calibration/VALUE_MODEL_RESULT.md` (says its numbers "are current").
`test_doc_index.py` has no negative-phrasing case.

### 13. `_recency_weight` prices "no date" as exactly "60 days old" (design, with numbers)

`data_merger.py:168-178`: undated → 0.5; dated → `0.5 ** (age/60)`. An 89-day-old source (grade "Aging")
weighs 0.36 and loses to an undated upload at 0.5. The docstring's "neither trusted as fresh nor
discarded" hides that absence is being assigned a specific age. Opinion-level; no failure scenario beyond
the ordering above.

### 14. Lower-severity / prose-vs-code

- `data_merger.py:1191-1194` and `:1782` still describe an mtime fallback ("an mtime-derived fallback
  otherwise", "mtime keeps winning") that `load_projection_file` removed (`:1069-1083`; pinned by
  `test_mtime_is_no_longer_consulted_anywhere_in_the_loader`).
- `lineup_optimizer.bye_collision` docstring (`:575`) says a week's basis may be `BYE_UNKNOWN`; the loop
  (`:640`) emits only `BYE_PARTIAL`/`BYE_MEASURED`. Only `bye_concentration`'s empty branch produces
  `BYE_UNKNOWN`, and it also produces it for an empty roster or a league with no slots — three facts, one
  token.
- `depth_ratings.depth_label:59` — value basis with every peer at a measured 0.0 returns `None` ("cannot
  be measured"), collapsing measured zero into absence; the module's own comment says `None` must never be
  read as a rating.
- `test_term_lifetimes.py:77-83` `test_the_registry_describes_no_term_that_does_not_exist` is
  `assertIn(name, source)` over raw text; `"bpa"` and `"risk_adj"` match trivially.
- `measurement.counted` treats `NaN` as present.
- `app.py:1109` swallows every exception from `sync_league`/`get_players` with `pass` and no
  notification; the user sees the "sync a league" empty state with no indication that a sync was
  attempted and failed.

---

## Nulls, with method

- **`DataMerger._resolve` exact path and identity namespaces.** Branches enumerated: alias
  (`:2135-2151`, no namespace check), exact (`:2166-2178`, narrows by team then position, **no
  `_different_identity_namespace` / `_different_offense_position` call**), key (`:2180-2224`, both checks
  present), fuzzy (`:2235-2247`, `_contradicted` only). The docstring at `:2027-2029` ("A resolution that
  crosses that boundary therefore contradicts the merger's own identity model, whatever path it took") is
  not true of the exact or alias paths in code. **Real-data measurement: 0 of 1,626 offense-player queries
  against the two IDP-scoped external files resolved onto an IDP row**, and Josh Allen QB/BUF's composite
  draws only QB rows. So: an unguarded branch, no instance in today's universe. Not confident it stays
  null under a different vendor file.
- **`_merge_memo` invalidation on `set_league_format`/`reload`:** the memo is rebuilt inside `_load()`
  (`data_merger.py:1791`), so a format change cannot serve stale resolutions. Fine.
- **`bye_concentration` ratio well-definedness:** `optimize_lineup` is an exact Hungarian solve
  (`lineup_optimizer.py:67-105`), so removing players cannot raise lineup value and `value_lost ≥ 0`; the
  ratio cannot exceed 1. Fine.
- **`draft_counterfactual.bpa_row`** filters `None` before `max` — the #193 crash is genuinely fixed.
