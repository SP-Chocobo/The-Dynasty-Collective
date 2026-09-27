# Wave 3 — one concept, two homes (`#126` vocabulary sweep)

Reproduced verbatim from the agent's hand-back. Not edited, not corrected.

**One correction of mine, measured against its finding 1.** I re-ran the comparison across
`league_matrix(scoring_settings_from_capture())` and get **35 of 36 arms mismatching, not 36 of 36**
— one arm agrees. The distributions it reports are exactly right: the coverage axis publishes
`{8:19, 9:12, 10:3, 11:1, 13:1}` while the arms actually draft `{8:1, 14:18, 15:12, 16:2, 18:1,
25:1, 26:1}`. The finding stands; the count is off by one.

Its finding 5 is the FOURTH independent arrival at `league_config`'s unwired gate (after the roster
geometry, ingestion and robustness lenses).

---

# Adversarial audit: one concept, two homes

## Setup and disclosures

- The worktree handed to me was stale (`draft_room.py` 2051 lines, no `draft_battery.py`/`league_config.py`/`invariant_registry.py`). I reconstructed `claude/fantasy-football-control-center-ff6qlu` via `git archive` into `/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/tree` (`draft_room.py` 4445 lines, `pick_synthesis.py` 2146) and worked only there. Nothing in the shared checkout was modified. All file:line references below are to that tree (same content as the branch).
- `git log --oneline -1` printed a subject whose first word is "Post"; I read no further and relied on nothing from it.
- No forbidden path was read. Data files read: `data/league_captures/README.md`, `data/baseline/sleeper_projection_provenance.json`, the three `data/league_captures/*.json`, and `data/fixtures/sleeper_capture.json` via the `run_draft_battery` fixture helpers.
- Method: AST enumeration of every literal collection of ≥2 string constants and every dict-key set across all non-test modules (script `scratchpad/enum_literals.py`), grouped by membership; then grep for single-token membership tests (`"SUPER_FLEX" in ...`), each site read by hand; then three measurement scripts (`scratchpad/measure.py`, `measure2.py`, `measure3.py`) run from the tree root on the real capture (`players_db` n=6595, season projections n=5346, scoring keys n=64) and the three captured leagues.
- Instrument caveats: (1) the AST pass cannot see a set built by comprehension or a predicate written as a single-token `in` test; those came from grep + reading, so a docstring match could have been mistaken for code — I read every site cited. (2) The three league captures carry no top-level `scoring_settings` (F&F's README says half PPR; `league_format_summary` says "Standard" on them), so scoring-token comparisons on captures exercise absence handling only. (3) `app.py` constants were read by `ast.literal_eval`, not by importing Streamlit.

---

## Findings that DISAGREE on today's real data

### 1. "Draftable rounds" has two answers in the same module, and the coverage report publishes the wrong one on every arm

- **Home A** — `league_config.py:78-99`: `NON_STARTING_SLOTS={BN,TAXI,IR}` answers Q1 (does this slot start a player); `UNDRAFTED_SLOTS={IR}` / `draftable_slots()` answers Q2 (does the startup draft fill it). The block's own text: "Every instrument ... used len(roster_positions) for the draft's round count, which is Q2 answered with Q1's silence."
- **Home B** — `draft_battery.py:820` `roster_shape_axes()`: `"draftable_rounds": len([s for s in slots if s not in ("BN", "IR", "TAXI")])` — a hand-listed copy of Q1's set, applied to Q2's question, under Q2's name. The module imports `lc` and uses `lc.draftable_slots` five lines earlier for `league["draft_rounds"]` (84, 97, 194, 209, 246).
- **Agreement today: NO.** Measured across `league_matrix(base_scoring=capture)`: **36 of 36 arms** have `league["draft_rounds"] != roster_shape_axes(...)["draftable_rounds"]`. The coverage report (`format_axes_exercised`) advertises `draftable_rounds: {8:19, 9:12, 10:3, 11:1, 13:1}` while the arms actually draft `{8:1, 14:18, 15:12, 16:2, 18:1, 25:1, 26:1}`. On the captured leagues: F&F 26 vs reported 10; GSOP2 29 vs 10; ffcl_group_a 14 vs 9. The reported number is the *starting-slot* count.
- **Consequence:** the instrument built to detect an unexercised axis reports a fictitious axis. Nothing reads `draftable_rounds` except `advertised_format_axes → format_axes_exercised` (grep: no other reader, no test pins the value), so the mislabel is invisible. A test asserting "draftable_rounds varies with roster length" would pass for the wrong reason.
- Related in the same module: `draft_battery.py:129` (custom arms) and `:146` (mode arms) still set `draft_rounds = len(roster_positions)` — the exact expression the league_config docstring names as the defect. Agrees today only because no custom arm carries IR; add IR to one and it drafts too many rounds.

### 2. `feasibility_first`'s fallback is a third home for round count, in the same module as the correct one

- **Home A** — `draft_room.py:2069, 2078-2081`: `HORIZON_UNDRAFTED_SLOTS=("IR",)` and `draftable_slots_per_team()` (identical membership and semantics to `lc.UNDRAFTED_SLOTS`/`lc.draftable_slots` — a duplicate of that home, agrees today).
- **Home B** — `draft_room.py:3432`: `total_picks = draft_rounds if draft_rounds else len(roster_positions)`. The fallback is Q1's silence again, three functions away from `draftable_slots_per_team`. Its comment still claims "draft_battery sets rounds = len(roster_positions) by construction", which is now false for the matrix arms (they use `lc.draftable_slots`).
- **Agreement today:** on the three captured leagues the fallback says 29/33/16 picks where the draft is 26/29/14. Production is protected only because `app.py:5389` hand-carries `draft_rounds=total_rounds` for the live draft and `build_mock_league` never emits IR. Every instrument has to remember to set the key by hand — and `run_roster_proof_ff.py:76-83` records that one didn't ("the first run of this proof drafted 26 rounds while the engine planned for 29"). `draft_simulation.simulate_full_draft` (draft_simulation.py:150-190) does not set it; any caller handing it a real IR-bearing league dict without `draft_rounds` gets a feasibility backstop that binds 3-4 picks late.
- **Splitting input:** any league with IR slots reaching `compute_draft_board` without `draft_rounds` — `roster_diagnostics.py:179` and `draft_counterfactual.py:118` pass the league through unchanged.

### 3. `draft_board_ui` hand-lists the flex view order and omits two of the five flex types — one of the three captured leagues is affected today

- **Home A** — `player_universe.py:19-25` `FLEX_SLOT_POSITIONS` (five keys, including `WRRB_FLEX`, `REC_FLEX`).
- **Home B** — `draft_board_ui.py:309-310` `_POSITION_VIEW_ORDER` lists `FLEX, SUPER_FLEX, IDP_FLEX` only, and `position_view_options()` iterates it. The comment at 379-397 discusses `WRRB_FLEX`/`REC_FLEX` labels at length, and `_flex_label("WRRB_FLEX")` returns "WR/RB" — code that is unreachable through the options list. `app.py:1126-1132` `FA_POSITION_FILTERS` restates `FLEX`, `SUPERFLEX`, `IDP` eligibility literally (members agree with the home today) and also has no entry for the two.
- **Agreement today: NO.** `ffcl_group_a.json` carries `WRRB_FLEX`; `position_view_options(all positions, ffcl roster)` returns `[ALL, QB, RB, WR, TE, FLEX, SUPER_FLEX, K, DEF, DL, LB, DB]` — no WRRB_FLEX view. For a synthetic `REC_FLEX`+`WRRB_FLEX` roster, no flex view at all is offered while `lineup_optimizer` and `starter_slot_counts` price both slots.
- **Consequence:** UI only — a manager in such a league cannot filter the board to the candidates eligible for that slot, though the engine values them. Adding a flex type to the home does not propagate, contrary to the comment "a flex type added there gets a label without anyone editing a list."

### 4. Battery roster shape counts a different position than the engine values (acknowledged in code; measured n=167)

- **Home A** — `player_universe.player_position` (bucket via `fantasy_positions`). **Home B** — `draft_battery._position_of` (raw `position`), used by `roster_shape` / `first_round_taken` (draft_battery.py:276-291, 486-510). The docstring records this deliberately for report comparability.
- **Agreement today: NO** — 167 of 6595 players differ (140 of them season-projected): raw LB→DL n=124, LB→DB n=25, TE→RB n=3, WR→DB n=2 (Travis Hunter class), plus singletons. Every battery `shape` in an IDP arm counts LBs that the engine drafted as DL. Reported so the disclosed divergence has a number; not new.

---

## Duplications that AGREE today, with the input that splits them

### 5. "Is this a superflex league" — two predicates, and the gate that would reconcile them has no production caller

- **Token-or-count**: `sleeper_client.league_format_summary` :857 and `draft_battery.league_format_hint` :271 — `count("SUPER_FLEX")>0 or count("QB")>1`. This is what `app.py:3560` feeds `DataMerger.set_league_format` (file selection; `_rankings_format_match_score` weights superflex 3.0, "can roughly double a startable QB's price").
- **Token-only**: `draft_room.py:3801` (gates `qb_startable_floor`), `pick_synthesis.py:1711` (`_consensus_lookup` returns `{}` unless True), `draft_strategy.py:179` (QB pace), `draft_counterfactual.py:168`, `app.py:5531` (board tag), `draft_battery.py:819` `has_superflex_slot`.
- **Agreement today:** all three captured leagues are 1×QB + SUPER_FLEX; both predicates True; 0 of 36 battery arms split.
- **Splitting input (measured):** `roster_positions=[QB,QB,RB,RB,WR,WR,TE,FLEX,BN,BN]` → hint/summary True, engine False, `has_superflex_slot` False. Consequence: the merger prices QBs off the superflex export while the board applies the 1QB replacement path, no cliff floor, no KTC consensus, no QB pace — two halves of one board on two formats. `league_config.ambiguities` :202 does detect exactly this (`superflex_disagreement`) and `admits_decision`/`decision_config` exist to block it — but grep shows **no production module calls them** (only `test_league_config.py`; `app.py` imports `league_config` for `describe_config_age` alone). Within `draft_battery` the coverage report would advertise `superflex=True` and `has_superflex_slot=False` for the same arm.

### 6. Team count: the header reads `settings.num_teams`, the engine reads `total_rosters`, and the gate protects the key the engine does not read

- `sleeper_client.py:872`: `settings.get("num_teams", len(league.get("roster_positions", []) and [])) or league.get("total_rosters")`. Note `len(X and [])` is always 0 — dead expression; the line is effectively `num_teams or total_rosters`. `app.py:4813` seeds the mock draft's team count from this.
- Engine: `draft_room.py:3691`, `pick_synthesis.py:1678` — `total_rosters or len(distinct roster_ids) or 1`; `pick_synthesis.py:729` `int(total_rosters or 0)`; `config_space.py:154`, `draft_battery.py:130,197`.
- `league_config.FORMAT_DECIDING_KEYS = ("rec","bonus_rec_te","type","num_teams")` :114 — hand-kept "in step with sleeper_client.league_format_summary", i.e. with the *display* function, not with what decides.
- **Agreement today:** all three captures have `settings.num_teams` absent and `total_rosters=12`; both readers say 12.
- **Splitting inputs (measured):** `{settings.num_teams:10, total_rosters:12}` → header 10, engine 12. `{settings.num_teams:12, total_rosters absent}` → `ambiguities()` returns `[]` (passes the gate), header says 12, engine `num_teams=1`: every `num_teams × slot_counts` demand collapses to one team, replacement levels sit at rank ~1, and `current_round = len(picks)//1 + 1` flips auto-upside at pick 15.

### 7. "Which round is it" is derived from three different team counts

- `draft_room.py:3691-3706`: `len(picks) // (total_rosters or distinct roster_ids or 1) + 1` — decides `use_upside`.
- `draft_simulation.py:150,163`: `idx // len(set(pick_order)) + 1` — the pick label and `_picks_by_mode` report.
- `pick_synthesis.py:722-735`: parses `pick_label` first, then `total_rosters`, then distinct roster ids, then `max(round)`.
- **Agreement today:** seats == `total_rosters` in every arm and capture.
- **Splitting input (measured):** `total_rosters=12`, pick order with 10 seats, 140 picks made → labels and the mode report say round 15 (upside), `draft_room` scores as round 12 (balanced); the reported balanced/upside split would not be the one the trajectory used. Reachable via any draft whose order has fewer seats than the league has rosters (orphaned/vacant seat, or a mock with `teams` < `total_rosters`).

### 8. "Is this a starting slot" — three predicates that differ on any token outside `KNOWN_SLOTS`

- `league_config.starting_slots` :89-91 — `s not in {BN,TAXI,IR}` (positive by exclusion).
- `lineup_optimizer.slots_from_roster_positions` :57-64 — `s in FANTASY_POSITIONS or s in FLEX_SLOT_POSITIONS` (positive by inclusion).
- `draft_room.starter_slot_counts` :887-916 — inclusion again, separately written.
- **Agreement today:** all captured slot codes are in `KNOWN_SLOTS`; counts agree.
- **Splitting input (measured):** `[QB,RB,WR,TE,FLEX,DP,BN,IR]` → `lc.starting_slots`=6, `lineup_optimizer`=5, `starter_slot_counts` total=5.0, `roster_shape_axes.draftable_rounds`=6; a lowercase `flex` splits the same way. `league_config.ambiguities` flags `unknown_slot` — but see #5: nothing in production consults it, so `config_space.startable_slots` and the battery's `unfilled_starting_slots` count one more starter than the solver can ever fill. `draft_battery.roster_shape_axes` is also the only reader that upper-cases slots (:812), so it alone would report `has_kicker=True` for a league spelling it `k` that every other reader ignores.

### 9. Injury designation vocabulary — three membership sets

- `player_universe.GAMES_MISSED_FLOOR` keys `{IR, PUP, Out}`, `IMMATERIAL_INJURY_STATUSES=("Questionable",)`.
- `draft_room.RISK_ADJ` :441 keys `{IR, Out, Doubtful}` — hand-listed; read by `health_penalty` :459-461 (returns 0.0 when basis is `rule_floor`, else `RISK_ADJ.get(status, 0.0)`).
- `app.py:1120 INJURY_OK_STATUSES=("Questionable","Doubtful")` — pill colour.
- **Agreement today:** capture statuses: Questionable 290, IR 126, NA 46, PUP 21, Sus 8, DNR 2, Out 1, Doubtful 0. `PUP` (n=21) is recognised by one home and not the other; all 21 have a season line, so `health_penalty` zeroes on `rule_floor` and the two homes coincide by construction. 9 of the 21 PUP lines lack `gp`.
- **Splitting inputs:** a PUP player with a season line but no `gp` → `availability_factor` returns `(1.0, no_games_reported)` and `health_penalty` returns `RISK_ADJ.get("PUP")=0.0` — a man the rulebook says misses ≥4 games priced as fully fit, where an identically-situated IR player takes −18. (Today the 9 gp-less PUP rows are protected only if `sleeper_points` is None, which routes them to the vendor path where RISK_ADJ still has no PUP.) `Doubtful`: RISK_ADJ prices it −5, `availability_factor` calls it `unrecognised_designation`, the app paints it amber ("ok"). n=0 in the capture.

### 10. Two literal copies of the transcribed K/DST file-name set, both claiming a JSON as their source

- `draft_room.py:708 KDST_SEEDED_SOURCE_FILES` and `data_merger.py:1365 _TRANSCRIBED_SOURCE_FILES` — identical two-member sets. The comment at data_merger:1358 says the registry is "PROVENANCE-BACKED, not filename-guessed" and names `sleeper_projection_provenance.json`; the JSON's own README says "Nothing reads this file at runtime." Measured: both sets == the JSON's csv keys (n=2).
- **Splitting input:** a third transcribed CSV registered in the JSON and one module — `measurement_basis` (data_merger:1398) tags it `sleeper_transcribed` (confidence 50) while `draft_room:2694` leaves its `bpa_source` at the Draft Sharks tier (80), or vice versa.

---

## Code-style duplications (agree today; I could not name a realistic input that splits them)

- `FANTASY_POSITIONS` restated as ordered literals: `app.py:3758`, `app.py:5798` (`_position_order`), `data_merger.py:303 POSITION_CODES`, `run_draft_battery.py:35 BATTERY_POSITIONS`, `sleeper_import_report.py:38`. All equal as sets (measured).
- Necessity tier labels: home `pick_synthesis.NECESSITY_LABEL_THRESHOLDS` :667-672; restated as dict keys in `app.py:92-97` (two dicts), `draft_board_ui.py:59-62, 713-714`, `draft_counterfactual.py:47`. All six labels present in each (measured).
- `dr.HORIZON_UNDRAFTED_SLOTS` vs `lc.UNDRAFTED_SLOTS`; `dr.draftable_slots_per_team` vs `lc.draftable_slots` — same membership/semantics; league_config's docstring claims sole ownership.
- `draft_battery.py:79` `("standard","half_ppr","ppr")` hand-lists the keys of `dr.MOCK_SCORING_REC_VALUES`; `app.py:3558, 4808, 4836, 4857` map "Full PPR/Half PPR/Standard" labels to those keys twice, defaulting to "ppr".
- Roster-payload slot vocabulary (`Starter/Bench/TAXI/IR`): `player_universe._roster_slots` and `app.py:3669` implement the identical expression; `app.py:1119`, `screen_context.py:258`, `lineup_readiness.py:47` restate members.
- `unfilled_starting_slots` (draft_battery.py:313-315) builds eligibility with its own expression instead of `player_eligible_positions`; differs on 4 of 6595 players (`{K,P}`→`{K}` ×3, `{OL}`→`{TE}` ×1), none of which changes an assignment.
- Mode names `"balanced"/"upside"/"auto"` are bare literals in six modules; an unknown string silently means balanced everywhere, consistently.
- Dynasty predicate `settings.type == 2` in `draft_room:3679`, `app.py:5532`, `sleeper_client:871`, `build_mock_league`. Consistent; Keeper (type 1) is "not dynasty" everywhere.
- Identity miss-record shape `{matched, match_path, match_candidates, match_verified}` built in both `data_merger.merge_player` :2482 and `draft_room._merge_across_eligibility` :1328.

## Well-supported null results

- **Stat-line scoring has one semantics.** `player_universe.score_projection` and `sleeper_client.compute_points_from_stats` iterate opposite dicts but agree on all 5346 season lines (max |diff| 0.0), both coerce string values, both raise on a `None` weight (none in the 64-key capture rulebook).
- **Slot eligibility has one home and every scoring reader uses it.** `FLEX_SLOT_POSITIONS` is imported, not restated, by `draft_room`, `lineup_optimizer`, `league_config`, `draft_board_ui`; the only restatements are the UI filter list (#3) and instruments.
- **`league_format_hint` and `league_format_summary`** derive scoring/superflex/te_premium by the same rules (checked on captures and synthetic inputs); their only split is the label-vs-token vocabulary, bridged by `app.py`'s map.

## Scripts (in scratchpad, not the repo)
`enum_literals.py` (AST census), `measure.py`, `measure2.py`, `measure3.py` — all run with `PYTHONPATH=.` from the reconstructed tree root.
