# Wave 5, pass I — preserved verbatim

> **The pass's own words, unedited.** No triage here; the running log is `FINDINGS_LOG.md` and
> verdicts live in `LEDGER.md`.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` with the six forbidden paths excluded.
> Wave 5 mandate — adds the null-result evidentiary standard, a state/persistence/process-boundary
> category, and steering toward the self-integrity instruments.
>
> **Self-reported contamination: none.** Exclusions verified absent after extraction. One grep of
> `ARCHITECTURE_AUDIT.md` (not forbidden).

## Report

**Contamination statement:** No forbidden path was opened. Exclusions verified absent after
extraction (`FREEZE_*.md`, `POST_AUDIT_PLAN.md` missing; `evidence/{smoke_seats,batteries,blind_pass}`
empty). The only prose document touched was `grep -n '206' ARCHITECTURE_AUDIT.md` (one unrelated
line). Nothing in the repository was modified; all probes ran against `/tmp/audit_tree` with scratch
output only.

**Method summary:** Read in full: `lineup_optimizer`, `draft_strategy`, `player_universe`,
`sleeper_client`, `llm_engine`, `pick_debate`, `screen_context`, `roster_diagnostics`,
`draft_history`, `resume_join`, `baseline_manifest`, `corpus_state`, `content_hash`, `attachments`,
`store_io`, `bot_config`, `bot_research`, `bot_benchmark`, `providers`, `untrusted`,
`upload_batches`, `prediction_record`, `outcome_record`, `term_lifetimes`, `panel_independence`,
`ui_source`, `measurement`, `assertion_floors`, `suite_taxonomy`, `quantity_readers`,
`render_trace`, and the tests for those four instruments plus `test_take_model_coherence`,
`test_store_io` (scan part), `test_depth_exposure` (grep). Ran: `assertion_floors --check`,
`baseline_manifest --check`, `render_trace --check` (all exit 0 on the tree), the `quantity_readers`
scanner, a fast-tier timing sweep, and real-data probes on `data/fixtures/sleeper_capture.json` with
`merger.set_league_format(league_format_hint(league))` — a 1.01/1.12 snapshot, a per-rival survival
breakdown, and a 12-round every-seat-takes-its-top-candidate draft of the owner's shape
(`QB RB RB WR WR TE FLEX SUPER_FLEX K IDP_FLEX IDP_FLEX + 14 BN`, 12 teams, 25 rounds).

---

### 1. Two take models answer "will he survive to my next pick" two orders of magnitude apart — `draft_strategy.py`

**Where.** `_take_probability` / `_board_take_probability` (549–590) normalise the rank table over
the whole board's mass (`board_take_mass`, 402). `_pace_based_take_probability` (184–240) is not
normalised at all and wins whenever it exceeds the rank estimate (776:
`pace_driven = pace_p_take > rank_based_p_take`).

**Measured at pick 1.01, seat 1, real capture (2,028-row board: 820 priced, 1,208 unpriced):**

- `board_take_mass`: total 41.67, of which 24.16 (58%) is the 0.02 floor on unpriced rows and most
  of the rest is the floor on the priced tail.
- Christian McCaffrey is rank 1 on **every** rival board; each rival's `take_probability` =
  0.55/41.67 = **0.013**; survival across 22 intervening picks = **0.747**. The sum of a rival's
  take probabilities over their own top 12 is **0.032** — the model says a rival has a 96.8% chance
  of picking outside their top 12 with their one pick.
- Josh Allen is rank 7 on every rival board → rank model gives survival **0.989** (`league=None`).
  With the pace prior on, per-pick p_take climbs 0.083, 0.167, … reaching **1.0 at the 13th
  intervening pick** and staying there for 10 more; survival = **0.0** exactly. Same board, same
  snapshot: RB1 75% safe, QB1 0% safe.
- In the 12-round draft this held throughout: round 2 shows Hurts 0.0 (22 picks), C. Williams 0.001,
  Daniels 0.034, Maye 0.31, while RBs/WRs in the same round sit at 0.92–0.98. `opportunity_cost` for
  every QB equals his full TAV.

**Why the pace prior is internally inconsistent.** `actual_now` (228) counts QBs only in the real
`picks` list, so within one `estimate_survival` call the deficit grows with
`picks_made_now = len(picks)+i` while zero QBs are assumed taken — the prior asserts pick #13 takes
him with certainty on the premise that picks #2–#12, each just assigned 0.08–0.92, took no QB. It
also reintroduces the exact 0.0 that #206's repair ("the reported zero is GONE",
`test_take_model_coherence.py:200`) exists to remove — under `survival_basis == "measured"`.

**Why the normalised model's magnitude is a fixture artefact.** `test_take_model_coherence._boards`
(117–147) uses ~505 floor rows → rank-1 p = 0.064 and the test at 233 asserts this is "within a few
points of the measured 3.0%". The docstring itself says the total "is a FUNCTION OF THE POOL". On
the real universe it is 41.67 → 1.3%, and the pinned turn survival of 0.232 becomes 0.747. The claim
of landing near reality is pinned on a board a quarter the size of the one the owner drafts on.

**Dead code presented as the model.** `board_contention_scale` (465) and `_value_take_weight` (511),
plus the preceding 12-line comment stating the take model "is a VALUE SHARE over the opponent's own
board, not a lookup on the candidate's ordinal", have **no callers anywhere** in the tree (grep: only
their definitions). Production is the rank table. The docstring describes a model that never runs.

**Reach.** Survival is withheld from the board and `pick_debate` (`SURVIVAL_IS_CALIBRATED = False`,
known), but `pick_necessity`/labels still derive from it (known leak) and
`screen_context.build_draft_room_context` (line ~118) still prints "survival NN%" into the Prytaneum
seed — the same number `pick_debate` refuses to show the chairs. This item is adjacent to the known
calibration flag; what is new is the two-model split, the exact-zero path, the pool-size dependence
on the real shape, and the dead value-share code.

### 2. `depth_exposure` is stamped "measured" by roster-wide surplus, not reachable surplus — `lineup_optimizer.py:292`, consumed at `draft_room.py:3457`

`has_surplus = len(roster_players) > len(starting_ids)` is one boolean for the whole roster; every
position with a starter then gets `EXPOSURE_MEASURED` (312). `draft_room.py:3457` prices
`worst_loss` into `team_acquisition_value` **only** under that basis, so the label decides whether a
number enters the price.

**Synthetic probe.** 8 starters, no bench: QB 30 / TE 15 / RB 45 all `no_surplus` (correctly "each
starter's own value wearing a depth-shaped label", per the module's own comment). Add **one bench
kicker**: QB 30, TE 15, RB 45, WR 68 flip to `measured` with identical numbers. The kicker cannot
back up any of them.

**Real draft, pick 141 (round 12, seat 4, 11 priced players):** bases `K ('measured', 14.0)`,
`TE ('measured', 8.0)`, `LB ('measured', 26.0)`, `QB ('measured', 82.0)` — the K/TE numbers are the
lone starter's own trade_value — and the chosen candidate Chris Boswell (K) carries
`depth_exposure = 1.68` as a priced term. On this shape unpriced K/IDP are excluded from
`roster_players` (`_team_roster_players`, 2027), so the flip lands the moment a seat holds its ninth
priced offensive body and then applies to every position.

The only test pinning `EXPOSURE_NO_SURPLUS` (`test_depth_exposure.py:122`) uses the no-bench-at-all
roster — the one shape where the invariant cannot fail.

### 3. `corpus_state` reports "no local data in the mix" while a league-scoped upload moves every price — `baseline_manifest.py:56`, `corpus_state.py:92`, `data_merger.py:1803`

`DECLARED_INPUT_DIRS` covers `data/baseline` and `data/projections/_global`;
`DataMerger(league_dir=league_projections_dir(id))` (`app.py:1103`) also loads
`data/projections/<league_id>/` into `self.projections` via `_merge_rankings`.
`test_baseline_manifest.py:157` pins the league dir as deliberately out of manifest scope — fine for
the manifest, but `corpus_state.assess()` then has no third source of truth.

**Probe.** Planted one rankings CSV (`Zz Planted`, RB, projection 9999) in a temp league dir outside
the repo: priced by the league-scoped merger, top RB projection went 359 → 9999 (a league-level
replacement input), and `corpus_state.assess()` returned `doctrine_only` with the green sentence
"Computing from the shared baseline only — no local data in the mix"; `baseline_manifest.diff()` was
clean. The module docstring's own argument ("an uploaded projections file … changes REPLACEMENT
LEVELS … so it moves prices for players the file never mentions") is exactly the case it cannot see.
(`app.py:2989` routes only `free_agents` uploads there today, but the merger loads *any* rankings
file in that directory.)

### 4. `quantity_readers` verdicts rest on name collisions — `quantity_readers.py:262`, `175`

- `_reads_in` counts **any** `ast.Attribute` load with a matching `.attr` as a read of the quantity.
  Probe over `scan()`: the DECISION verdict for `depth_exposure` rests solely on `draft_room.py`
  containing the **function call** `lo.depth_exposure(` — no scoring module subscripts the board
  column (its only column reader is the `pick_synthesis` relay at 1501).
  `test_quantity_readers.KNOWN["depth_exposure"] = DECISION` therefore "agrees with the scanner" for
  the wrong reason. Same mechanism gives attribute-only DECISION verdicts for `candidates`,
  `data_freshest_date`, `picks_consumed`, and DECISION for `name`, `position`, `team`, `value`,
  `round`, `basis`, `mode`, `starters`, `player_id` on the strength of unrelated dicts/objects in
  `data_merger`, `player_universe`, `depth_ratings` (`.name` on a Path, `.round(` on a Series,
  `settings.get("starters")`). Every KNOWN entry is a distinctively named quantity, so the collision
  is never exercised.
- `_relayed_in` double-counts reads inside nested dict values. Probe: `{'a': row['x']}` → relayed
  `{'x'}`; `{'a': {'b': row['x']}}` → relayed `set()`. A scoring module relaying a quantity inside a
  nested literal is scored as consuming it.

### 5. `assertion_floors` claims "a weakening cannot pass unseen" (docstring line 45); four ways it does — `assertion_floors.py:121–170`

Probed with the module's own `write`/`drops` in a temp dir:

- weaken `assertEqual → assertIsNotNone` in `test_a` **and** add `test_c` with an `assertEqual` in
  the same edit → `drops() == []` (per-name counts net to zero);
- `@unittest.skip` on a test → `[]`;
- move the assertion under `if False:` → `[]` (stated as out of scope, but the CI check still reports
  green);
- floors file reduced to `{}` plus an **empty** test module → `[]`; `--check` prints "no guarantee has
  shrunk (0 modules held to a floor)" and exits 0, because `load()` returns `{}` for a
  missing/damaged file (129, 133). Only
  `test_assertion_floors.test_the_floors_file_covers_this_module_too` notices, and only if the suite
  runs.

Also: `test_override_provenance_boundary.py` and `test_tav_identity_is_stated_once.py` contain bare
`assert` statements, which the instrument does not count.

### 6. `suite_taxonomy` tier detection is a substring, and its numbers are stale — `suite_taxonomy.py:10`, `tier_of`

`tier_of` = `"DataMerger()" in source`. `test_arm_rulebook`, `test_pick_resolution_flags`,
`test_priceable_projection_count` load the 6,595-player capture via `build_players_db_from_capture`
and are classed fast. Measured: fast tier = **123 modules, 201.5 s wall** (docstring: "53 fast
modules, 845 tests, 1.5 seconds. 27 full"); `test_invariant_confirmation_anchors` 57.4 s and
`test_quantity_readers` 31.3 s are both "fast". A module that mentions `DataMerger()` in a docstring
is "full"; one constructing `DataMerger(league_dir=…)` or via a helper is "fast".
`test_suite_taxonomy` pins the rule against two hand-picked modules only.

### 7. #102's "one read-modify-write discipline for every JSON store" has an exemption whose reason is false — `test_store_io.py:286`, `bot_benchmark.py:422–456`, `sleeper_client.py:213, 565–566`

- `bot_benchmark._load_all` swallows `JSONDecodeError → {}` and `save_report` writes `all_reports`
  back with `write_text` — the exact amplifier `store_io`'s docstring measured ("a store holding
  five … holds exactly one after the next add"). The ratchet exempts it as "developer-run measurement
  output, never touched by the app"; `app.py:2689–2695` runs `bot_benchmark.run_benchmark` and
  `bot_benchmark.save_report` from the Configure Bots UI. Scenario: one torn read → next Apply wipes
  every role's 20-run history.
- `sleeper_client.get_players` writes the ~10 MB players cache with `write_text`
  (truncate-then-write) and `_write_snapshot` does the same for `_latest.json`. A second tab reading
  mid-write gets `None` → `get_players` re-fetches `/players/nfl` (Sleeper's once-per-day request)
  and `select_league` (`app.py:1099–1110`) launches a second full `sync_league`. Exempted as "a lost
  write costs one re-fetch"; the torn *read* is the cost.

### 8. Draft Room snapshot cache and `stamp_is_current` cannot see a same-date data change — `app.py:5366`, `pick_synthesis.py:1651–1658`

Both key on `(len(picks), merger.freshest_date)`. Re-uploading a corrected rankings file dated the
same day as the current freshest (or an alias override, or a file dated earlier that wins on basis)
changes prices after `data_merger.reload()`, but the cached `PickSnapshot` is served and
`snapshot_is_current` returns `True`. Same for any pick correction that leaves the count unchanged.

### 9. Claims the code no longer supports (each verified against the implementation)

- `term_lifetimes.py:58` says `bpa` is "scaled linearly against the pool's largest VOR gap";
  `draft_room._scale_vor_to_bpa` (2162) is the identity ("No reference, no rescale, no clip").
- `prediction_record.main()` (213) commits `data/predictions/predictions_2026-09-03.json` for
  "12-team dynasty, 1QB, 2RB/2WR/1TE/2FLEX, 5 bench" with no `set_league_format` call — a shape the
  owner does not play and a merger format chosen by file-sort accident (the defect `app.py:3515`
  documents). The docstring calls it "universal_value's own altitude", but `universal_value` is
  replacement-level (i.e. `roster_positions`) dependent, so the forward record tests a different
  engine configuration than production.
- `roster_diagnostics.compute_team_diagnostics` solves lineups with `eligible={p["position"]}`
  (primary only) while the engine's `eligibility_bonus` premise is full eligibility — two lineup
  models of one roster.
- `draft_history.record_snapshot` docstring: "storing the same snapshot twice writes the same bytes"
  — the payload carries `ts`/`date`, and `_atomic_write` is `os.replace`, so a race is
  last-writer-wins on the timestamp (first-wins guard covers the non-race case).
- `draft_strategy.positional_forfeits` still uses the unnormalised rank table
  (`RANK_TAKE_PROBABILITY.get(rank, 0.0)`, cap 0.9) "same principle as estimate_survival" — no longer
  true after #206; forfeit and survival now disagree about the same rival's next pick.

### 10. Low

- `attachments.save_attachment` (85) joins the client-supplied `uploaded.name` onto
  `ATTACHMENTS_DIR` with no `Path(...).name`; a crafted multipart filename traverses.
  Single-local-user assumption is stated, so low.
- `app.py` `.env` rewrite (`ENV_PATH.write_text`, ~795) is non-atomic.
- `sleeper_client.league_format_summary`: `settings.get("num_teams", len(league.get("roster_positions", []) and []))`
  — `len(x and [])` is always 0; harmless but nonsense.

---

### Null results (with method)

- **`store_io`**: read every function against the docstring's four claims. Lock keys: grep shows all
  twelve production stores build paths as relative `Path("data/…")` literals, so the "two spellings,
  two locks" hole is not reachable in production. `_parse` distinguishes absent/empty (readable) from
  non-empty-unparseable (damaged); `mutate` skips its write on damage; `write` refuses on a marked
  path; the mark clears on a successful parse; the refusal is surfaced by
  `app.py:1338 warn_about_unreadable_stores` (called at 6576). No defect found in the mechanism
  itself.
- **`content_hash`, `resume_join`, `untrusted`, `panel_independence`, `providers`, `bot_config`**:
  read line by line; the NUL-separated hashing, single-process inheritance rule, marker-stripping
  regex (handles `>>`/`>>>`, newlines inside `[^>]*`), four-state relationship, round-robin dealing,
  and saved-choice-wins loading all do what their docstrings state. I found no branch whose behaviour
  contradicts its stated contract.
- **`bot_research` gating**: `feeds_composite` recomputes eligibility from row fields;
  `data_merger.load_bot_research_as_external` filters on it (verified at 1690).
  Retraction/restore/confirm transitions match the docstring.
- **`llm_engine` handoff**: all three downstream prompts substitute `UNAVAILABLE_REPORT` for a failed
  chair; the all-upstream-failed annotation and truncation annotation are present.
- **`ui_source`**: `modules()` returns `['app.py']`, as the docstring claims.
- **`render_trace`**: `--check` exits 0 with the trace unchanged; the stub's `number_input` return
  (`kwargs.get("value", 0)`) is safe for `app.py:4790–4797`, which pass `value=`.
- **`baseline_manifest --check`**: matches (22 files); `bot_research.json` is absent from
  `data/baseline`, so its future presence would surface as "undeclared" (arguably right, though
  `corpus_state` would then call it "a file you added").
- **`draft_history._scope_dir`** sanitisation handles separators, `..`, and dot-only ids.

### Not confident / not examined

`data_merger` reconciliation and identity internals (only the load path and
`load_bot_research_as_external` read), `league_config` (skipped as known), `pick_synthesis` necessity
arithmetic (known leaks), `app.py` beyond the cited sites, `depth_ratings`, `rookie_draft`,
`draft_counterfactual`, `doc_index`, `basis_semantics`, `ordinals`. A full 25-round trajectory was
not run (12 rounds, ~40 min).
