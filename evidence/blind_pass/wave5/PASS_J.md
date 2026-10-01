# Wave 5, pass J — preserved verbatim

> **The pass's own words, unedited.** Running log: `FINDINGS_LOG.md`. Verdicts: `LEDGER.md`.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` with the six forbidden paths excluded,
> the Wave 5 mandate identical to pass I's.
>
> **Self-reported contamination: none.** Read `.claude/skills/engine-measurement/SKILL.md` (not on
> the list) and did not open other work's scratchpad probes.

## Report

Tree audited: `/tmp/audit_tree` (git archive of the branch, forbidden paths excluded and verified
absent). Contamination: none of `FREEZE_RECORD.md`, `FREEZE_CHECKLIST.md`, `POST_AUDIT_PLAN.md`,
`evidence/{smoke_seats,batteries,blind_pass}` were read. I did read
`.claude/skills/engine-measurement/SKILL.md` (fixture rules; not on the forbidden list). Other-work
probe files in the scratchpad were not opened.

All measurements below used the production pricing path on the owner's real `league_shape` from
`data/fixtures/sleeper_capture.json` (12 teams; QB,RB,RB,WR,WR,TE,FLEX,SUPER_FLEX,K,IDP_FLEX×2,BN×14;
25 draftable rounds; hint `{ppr, superflex=True, te_premium=False}`), with `set_league_format` called
before every board.

---

## A. Correctness defects in the valuation / decision path

### A1. The superflex QB "pace prior" produces certainty (survival = 0.0), which its own docstring says it never does

`draft_strategy.py:184-253` (`_pace_based_take_probability`) and `:221-230` (`estimate_survival`
passes `picks_made_now = len(picks) + i`). `any_pick_probability = min(deficit/PACE_CATCH_UP_WINDOW,
1.0)` then `/ target_rank`. `actual_now` counts only REAL picks, while `expected_now` advances with
each hypothetical intervening pick `i`. At 0 real picks, `expected_position_pace(QB, 12) = 6.0`,
deficit 6.0, `6/6 = 1.0`, so from the 13th intervening pick onward the rank-1 remaining QB has
p_take = 1.0 — a certainty — and `pace_driven` always wins because the normalised rank-based p is
~0.01.

**Measured (probe, owner's league, seat 1 at pick 1.01, 22 intervening picks):** Josh Allen
`survival=0.0, opportunity_cost=169.92, denial_value=169.92`; Joe Burrow `0.0`; Lamar Jackson
`0.002`; Brock Purdy `0.013`. Any seat whose round-1 gap reaches 13 picks sees this on an empty
board.

Claims contradicted: module docstring `:46-48` ("A rank-1 take-probability of 55%, not 95% … a
confident-sounding single number would misrepresent as certainty"); `:89-90` ("this is capped, never
treated as certainty" — which also cites a function `_pace_deficit_boost` that no longer exists).
`test_survival_evidence` pins the ordering pathology of this function, not its magnitude.

**Leak:** `SURVIVAL_DERIVED_FIELDS` (`pick_synthesis.py:536`) withholds
survival/opportunity_cost/EVW from people and chairs, but `denial_value = final_score ×
take_probability` (`draft_strategy.py:462`) is the same take probability in another unit and is
rendered unconditionally to the chairs (`pick_debate.py:463`: "Denial value: 169.92 (would go to
roster 2)"). If "necessity/prompt survival leaks" on the known list already covers denial_value,
treat this paragraph as confirmation; the certainty defect above is independent of it.

### A2. Two take models answer "will a rival take this" with incompatible numbers, and both feed `pick_necessity`

`positional_forfeits` (`draft_strategy.py:361-387`) sums the RAW `RANK_TAKE_PROBABILITY` table over
each rival's top-5 (`:375-381`), capped at 0.9 **per position per pick**. `estimate_survival`
(`:533-560`, `_board_take_probability`) uses the same table **normalised over the whole board**
(#206). The #206 repair was applied to one consumer only.

**Measured (same probe):** `expected_taken` RB = 19.8, WR = 3.52, QB = 0.0, TE = 0.0 over 22
intervening picks; Σ across positions = **23.32 > 22 picks** (arithmetically impossible). RB forfeit
= 180.71; QB forfeit = **0.0**. So on the same rival boards, at the same moment: survival says the
top QBs are gone with certainty (A1), forfeit says zero QBs will be taken. `pick_debate.py:477-481`
then renders the QB forfeit as *"Cost of delaying QB entirely: measured 0 -- the best remaining QB at
your next pick is expected to be no worse than now"* — while survival is withheld — so the chair is
told waiting on QB is free in the owner's superflex league. Both terms enter `compute_pick_necessity`
(`pick_synthesis.py:640-650` forfeit, `:611` survival).

### A3. Upside mode is inert on the production pricing path; 44% of the owner's draft is drafted roster-blind with no growth term

`draft_room.py:2156-2158` (`upside_score` gates growth on `_has_3yr`), `:2123-2160`. Rows priced from
Sleeper season sums (`points_vor_sleeper_season_scored`) carry no `proj_3yr`, so growth is 0.0 for
them; the upside branch also zeroes need/eligibility/depth/displacement.

**Measured (full 300-pick draft, `e2e_owner_draft_audit.json`):** `picks_with_growth_measured: 131,
picks_with_growth_above_zero: 0, max_growth: 0.0`. Board at the start of round 15 (production path):
38 of 1,860 rows have growth > 0 (12 rows are vendor-priced; 637 Sleeper-priced; 1,208
`no_priceable_input`). Every seat-1 pick from R16 on shows `need=0.0 disp=None depth=None tav==uv`.

Claims contradicted: `pick_synthesis.py` `CandidateSnapshot.growth_signal` comment ("43-52% of rows
carry growth > 0, mean 11.1 rising to 25.5 … by round 15 it changes which player is taken");
`draft_battery.league_matrix` ("upside is the one that matters: it is the only path that computes
growth_signal"). Those numbers were measured on the vendor-only path (`bpa_source ==
points_vor_draftsharks`); production is `vendor+sleeper`. Net effect: rounds 15-25 of the owner's
draft = pure `bpa`, roster-blind.

### A4. `depth_exposure`'s "no_surplus" sentinel is roster-level, so a position's basis flips on an unrelated position's bench — and the un-measured number then enters `team_acquisition_value`

`lineup_optimizer.py:358-362` (`has_surplus = len(roster_players) > len(starting_ids)`), `:375`
(basis per position from that one flag). `draft_room.py:3455-3462` adds `worst_loss × 12/100`
whenever basis == measured.

**Measured:** roster {QB 30, RB 25, WR 28, TE 15} vs slots QB/RB/WR/TE → RB `{worst_loss 25, basis
no_surplus}`. Add a bench QB (10) → RB `{worst_loss 25, basis **measured**}` — identical arithmetic
(RB1's own value, which `EXPOSURE_NO_SURPLUS`'s own docstring says "is NOT depth information"), now
labelled evidence, now worth +3.0 TAV on every RB candidate. `test_depth_exposure` pins only the
all-no-bench and deep cases (`:122-140`), never the mixed shape. This is the unmeasured/measured-zero
collapse the codebase says it never allows.

### A5. Kicker composition on the owner's real shape (KNOWN item; measured here for the record)

31 kickers drafted for 12 K slots; seats 7, 11, 12 hold 5 K each; 28 K taken in rounds 8-14 before
the first DL (R15). Round 21 was 12 DBs in a row. `structural_findings` = 0 because the battery
checks legality, not sanity. Listed only because it is what the engine actually produces on the
owner's league.

---

## B. Instrument and measurement defects

### B1. `corpus_state` answers the wrong question in both directions (measured)

`corpus_state.py:63-79` borrows `baseline_manifest.diff`, whose scope is `DECLARED_INPUT_DIRS =
(data/baseline, data/projections/_global)` (`baseline_manifest.py:68-71`);
`test_baseline_manifest.py:156-163` pins that the per-league upload dir is *deliberately out of
scope*. But `app.py:1103` builds `DataMerger(league_dir=data/projections/<league_id>)`, and
`app.py:4721` shows the corpus light from `corpus_state.assess()`.

**Measured (temp root):** copy of `data/baseline` + a
`data/projections/123456789/dynasty_rankings.csv` upload → state `doctrine_only`, light "🟢 Computing
from the shared baseline only — no local data in the mix." Meanwhile `bot_research.FINDINGS_PATH =
data/baseline/bot_research.json` (`bot_research.py:54-55`, git-tracked per its docstring, not in
`INPUT_MANIFEST.json`): planting an empty one → `includes_local`, "plus 1 file **you added**. Your
uploads change replacement levels…" — LLM-panel output described as a user upload, and
`baseline_manifest.py --check` exits 1 (CI red) after the first SOURCE FINDING is ever written. The
module docstring's "the question is always 'is anything local in the mix'" is exactly what it cannot
answer.

### B2. The committed prediction record was priced from the wrong export and the wrong pricing path

`prediction_record.py:200-230` (`main`): `dm.DataMerger()` with **no** `set_league_format`, a vendor
reconstruction of `players_db`, a hardcoded 1QB/non-TEP mock league, and `build()` (`:73-84`) calls
`compute_draft_board` with **no** `sleeper_projections`.

**Measured:** `data/predictions/predictions_2026-09-03.json` (264 rows, `league_shape: "12-team
dynasty, 1QB, …"`): all 264 rows `bpa_source == points_vor_draftsharks`; the unformatted merger
resolves to `te_premium_dynasty_rankings.csv`, so every TE in the record carries TE-premium points —
B Bowers 309 (record) vs 259 under the league it claims (`dynasty_ppr_rankings.csv`), T McBride 306
vs 253, C Loveland 284 vs 241. The record is "what this engine predicted" for a pricing path
production does not use, for a league the owner does not play, with TE values ~20% high for its own
stated shape. It is write-once by design, so this cannot be corrected in place.

### B3. `quantity_readers` grades by bare key name across unrelated namespaces, so its WRITE_ONLY guard cannot fire for colliding names

`quantity_readers.py:226-247` (`_reads_in` counts any `x["name"]`/`.get("name")`/`.name` in any
production module), `:262-290` (verdict). Run output: `starters` (the `depth_exposure` key) =
DECISION with readers `player_universe.py, app.py` — those are `roster.get("starters")` (Sleeper's
roster field, `player_universe.py:199`, `app.py:3621`); no consumer reads depth_exposure's
`starters`. `value_lost` = DECISION because `bye_concentration` reads it inside the producing module
(a relay to a quantity the same scan calls OBSERVABLE/WRITE_ONLY); `basis`, `value`, `mode`, `round`,
`name`, `team` are DECISION for the same reason. `test_quantity_readers.KNOWN_WRITE_ONLY` therefore
guards only names that happen to be unique.

### B4. `suite_taxonomy`'s tier claim is stale and the detector does not detect cost

`suite_taxonomy.py:8-12` ("53 fast modules, 845 tests, 1.5 seconds … everything else costs
milliseconds"); `:92-94` (`tier_of` = substring `"DataMerger()"`). **Measured (every fast module run
individually):** 123 fast modules, 210 s total; `test_invariant_confirmation_anchors` 57.2 s,
`test_quantity_readers` 32.0 s, `test_board_renders_absence` 11.8 s, `test_render_trace` 10.0 s. The
cost drivers are the self-integrity instruments (AST walks of the tree, importing `app.py` five
times, Playwright), none of which the detector sees.

Null on the other direction, with method: AST-checked every full-tier module for a real zero-arg
`DataMerger()` call in code — all 49 have one; regex-checked every fast module for `DataMerger(` with
args or an import of a module that constructs one at import time — none construct one at import.
Note: in my extracted tree (not a git repo) `test_baseline_manifest`, `test_doc_index`,
`test_prose_names`, `test_superseded_proposals` fail on `git ls-files` exit 128 — an artefact of my
setup, not a defect, but those four depend on git being present.

### B5. `draft_history` is wired to nothing

`draft_history.py` docstring: "This module is the substrate for all three (#92)", "what gives the
Prytaneum explicit visibility of which Draft PickSnapshots exist". `grep -l draft_history *.py`
(non-test) returns only `draft_history.py`; `record_snapshot`/`list_snapshot_records` have no
production caller (`app.py`, `pick_debate.py`, `draft_board_ui.py` checked).
`test_cdme_ingestion_boundary._NEVER_IMPORTED` lists it as a store CDME must never read — trivially
true of a store nothing writes. Secondary: its "two sessions storing the SAME snapshot write the same
bytes" claim is false (payload includes `ts`/`date`, `:138-143`), and `_atomic_write`'s tmp name
(`.{name}.{pid}.tmp`) collides across threads in one Streamlit process — both moot while unwired.

### B6. Dead take model with prose claiming it is the production shape

`draft_strategy.py:451-462` ("The take model's shape is a VALUE SHARE over the opponent's own board,
not a lookup on the candidate's ordinal") sits above `board_contention_scale` (`:465-508`) and
`_value_take_weight` (`:511-530`). Neither is referenced by any production, test or `run_*` module;
the production seam `_board_take_probability` (`:549-560`) is the rank lookup. Code-style unless
someone reads the prose as the model.

### B7. `render_trace` / `assertion_floors` — null results, with method

`render_trace.py --check` reproduced the committed 619-call trace byte-identically on the clean tree;
read `_Stub`/`_seeded_session`; the stated blind spot (default render path only, every widget
False/first option) is real and stated. `assertion_floors.py --check`: no drops on the clean tree;
read `_is_assertion`/`scan_module`/`drops`; the defect I looked for (counts preserved by
`@skipUnless`/`skipTest`) exists — 7 fixture-dependent `skipTest` calls in `test_draft_room.py` and
CAPTURE-gated classes in `test_216_*` — but falls inside the docstring's own declared limit ("an
assertion moved behind a condition that never holds"), so it is a limit, not a defect.

---

## C. State, persistence, process boundaries

### C1. `sleeper_client` still uses the exact write pattern `store_io` measured as torn-read-prone

`sleeper_client.py:206` (`cache_path.write_text(json.dumps(players))`, ~10 MB, non-atomic),
`:505-509` (`_write_snapshot` writes `<league>_<ts>.json` and `<league>_latest.json` with
`write_text`). `store_io.py`'s docstring documents that `write_text` truncates first and measured
91,956 empty reads of 98,405 under one concurrent writer. `app.py:3607` calls `get_players()` at top
level on every rerun; two tabs past the 24 h window both fetch and both `write_text` the same file; a
third tab's `_read_players_cache` returns None → live refetch, and if Sleeper is down at that instant
`get_players` returns `{}` — an empty player universe for that rerun with nothing distinguishing it
from "no players".

### C2. `_sum_weeks` collapses "week unreachable" with "week empty" (absence contract)

`sleeper_client.py:251-256` (`get_weekly_projections` returns `{}` on `SleeperAPIError` **and** on an
empty payload); `:315-350` records both as `weeks_failed`. The coverage record's "a week that errors
is recorded as a failed week … never silently treated as zeros" is true, but it cannot tell an outage
from a bye-shaped empty week. `get_season_stats` claims the same failed-week handling via
`_sum_weeks`, yet `get_weekly_stats` raises, so one failed week aborts the whole realised-season sum
(docstrings of the two disagree).

### C3. `store_io.write` silently drops writes to a store marked unreadable (low; disclosed)

`store_io.py:196-206`: returns None without writing. `attachments.save_attachment`
(`attachments.py:96-105`) writes the file bytes first, so a corrupt `captions.json` yields an orphan
file with its caption lost while the call returns success; `bot_config.set_role_provider` returns
True. Mitigated by `app.warn_about_unreadable_stores` (`app.py:1338`), so low.

---

## D. Lower-severity / style

- `draft_battery.league_format_hint` (`:204-218`) and `sleeper_client.league_format_summary`
  (`:726-746`) both map `rec >= 1 → ppr, rec == 0.5 → half_ppr, else standard`: a 0.75-PPR league
  selects the standard export. Two hand-kept copies of one rule (plus
  `league_config.FORMAT_DECIDING_KEYS`).
- `league_format_summary`: `settings.get("num_teams", len(league.get("roster_positions", []) and []))`
  — the default is always 0.
- `build_baseline_projection_rows` (`sleeper_client.py:565-640`): one week × `season_factor` (the
  extrapolation `get_season_projections` argues against), filters on raw `position` rather than
  `player_position`; no production caller found.
- `draft_strategy.py:89` cites `_pace_deficit_boost`, which does not exist.
- Take-mass normalisation (KNOWN via `SURVIVAL_IS_CALIBRATED`): measured rank-1 p_take = 0.013 on
  rival 2's board (58% of mass on 1,208 unpriced rows), so the consensus #1 player "survives" 22 picks
  at 0.747.

---

## E. Null results, with what was checked

- **LLM → CDME identity/pricing path.** Read `DataMerger._load` (`data_merger.py:1787-1835`),
  `_resolve`/`merge_player` (`:2079-2300`; default table is `self.projections`, never
  `external_values`), the two CDME readers of `external_values` (`draft_room._rookie_lookup:996-1008`,
  `pick_synthesis._consensus_lookup`) both hard-filtered to `keeptradecut`, and the injection tests
  (`test_cdme_ingestion_boundary.py:205-270`) which rebuild a fresh `DataMerger` after planting a
  confirmed, allow-listed finding — not vacuous. No path found by which `bot_research.json` reaches a
  price.
- **NaN reaching `pick_analysis`/`compute_pick_necessity`.** Hypothesis: `min(1.0, nan)` returns 1.0,
  which would give an unpriced candidate a full standout term. Not reachable:
  `_records_with_normalized_nan` (`draft_room.py:2194-2205`, called at `:3560-3573`) converts
  `final_score`, `universal_value`, `bpa`, `confidence`, etc. to None at the board edge. Not covered
  by that list: `need_bonus`, `eligibility_bonus`, `depth_exposure`, `displacement_adj`,
  `time_horizon_adj` — I did not establish they can never be NaN; not confident.
- **`store_io` locking.** Read every branch (RLock registry, per-thread depth for the sidecar flock,
  `mutate`/`atomic`); consistent with its contract in-process. Cross-process behaviour not exercised;
  medium confidence.
- **`resume_join`.** Both writers (`run_draft_battery.py:156-158, 429-430`;
  `run_roster_proof.py:351-359`) stamp every unit and write `commits_present`, so the
  report-level-commit inheritance is reachable only for pre-#215 files, as documented.
- **End-to-end structural.** 300/300 picks were `candidates[0]`, 0 picks took `tav=None`,
  `fills_required_slot` never bound, 0 duplicate/undraftable findings, 11 zero-margin picks (7 in R20).
- `lineup_optimizer.optimize_lineup` matrix construction and the ineligible-pair filter read line by
  line; no defect found beyond the known displacement clamp and the documented forced-negative-starter
  behaviour (7 forced negatives in the owner draft, reported by the battery).
