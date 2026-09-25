# `#34` — every remaining superflex QB is unpriced from mid-draft on

**Verdict: (c) correct in the draft loop, a hazard at consumer boundaries — and NOT a new
finding.** The state is already on the register as `#168` (sharpened), pinned by
`test_qb_pricing_cliff.py` against `evidence/take_model/unpriced_block_composition.json`, with
the design question ("startable AS A QB" versus "wins a SUPER_FLEX slot") explicitly deferred to
`#50`/Phase 3. What `#34` adds is (i) a correction to its own framing — the 102 unpriced QBs are
two populations, ~92 never priced by anyone and ~10 de-priced by the floor decline; (ii) a
small scale mismatch in the floor itself; and (iii) three consumer-boundary gaps the existing
absence tests never reach because their populations are opening boards.

Read-only investigation. No engine code edited, nothing committed (`#184`).

## 1. The mechanism — the provisional reading is right, with two additions

Verified in code, three lines:

- `draft_room.replacement_levels`, floor branch:
  `rank = int((at_pos[value_col] >= floor).sum()) or None` — zero remaining QBs at or above the
  floor gives `None`, and `if rank is None: continue` omits QB from `levels`.
- `draft_room._fill_omitted_from_anchor`: `missing = [p ... if p not in levels and
  (startable_floors or {}).get(p) is None]` — QB is excluded from the anchor fill by construction.
- `compute_draft_board`: `startable_floors = {"QB": qb_floor}` iff `"SUPER_FLEX" in
  roster_positions`. This is the ONLY producer of a floor, so the branch can only ever decline
  QB, only in superflex.

Downstream: `_vor` is NaN for every row whose position is not in `point_replacement`, `bpa`,
`universal_value`, `final_score` follow, and `_records_with_normalized_nan` turns them into real
`None` at the board boundary. `pick_synthesis._board_order` sorts `score is None` last.

**Addition A — the floor is on the vendor scale, the comparison is on the league-scored scale.**
`qb_startable_floor` reads `merger.projections["projection"]` (the vendor export selected by
`set_league_format`). Under the production pricing path `_points` is the Sleeper season sum
scored under the league's rules (`_derive_points_and_source`, `points_vor_sleeper_season_scored`
on 34 of the 42 priced QBs). Measured on the opening board, every arm, fixture below:

| arm hint | floor (vendor) | QB12 vendor | QB12 board `projected_points` | QBs clearing floor, vendor col | QBs clearing floor, board col |
|---|---:|---:|---:|---:|---:|
| ppr / half_ppr SF | 163.5 | 327.0 | 328.6 | 29 | **32** |
| standard SF | 162.0 | 324.0 | 328.6 | 29 | **32** |
| CAPTURE_fourth_and_forever | 162.0 | 324.0 | **357.84** | 29 | 32 |

The threshold is a fraction of one source's QB12 applied to a different source's totals. Today
the two scales are close enough that the boundary lands in the same cliff (32 both ways on the
board column), so `QB_STARTABLE_FLOOR_FRACTION`'s stability-basin argument survives — but the
argument was made on the vendor column and is being cashed on the scored column, and under the
F&F rulebook QB12 is 10% higher on the board than on the vendor. Not a defect today; a
derivation whose premise has moved (`#56` is not engaged; no constant is proposed).

**Addition B — the 102 is two populations.** On the opening `12T_ppr_SF` board there are 134 QB
rows; 42 are priced (basis `startable_floor`, live level 207.5 = the 32nd QB) and **92 are
`no_priceable_input` from pick 1** — no projection from either source, `absence_kind =
no_input`. At the round-15 state of a 12-team draft that has taken 32 QBs, 102 QB rows remain;
92 of them were never priceable and at most 10 were de-priced by the decline. The `#168`
record measured the same shape on the real GSOP2 draft: QB unpriced 113 at round 0 -> 123 at
round 12, i.e. the floor moved exactly 10 rows. The headline "102 unpriced QBs" is 90% vendor
coverage and 10% this mechanism.

## 2. Is the behaviour correct? Is it the K/DEF pathology in different clothes?

The two cases are not analogous, and the asymmetry is real rather than rhetorical:

- The K/DEF inversion (`predraft_replacement_anchor`'s docstring) was a position whose players
  still projected ABOVE their own pre-draft level — the demand model had simply run out of slots
  to count. Anchoring restored a comparison that the data supported.
- The floor-declined QBs project BELOW the floor by construction (the 10 rows sit at ~<163.5
  points; the pre-draft QB level is 207.5). Under an anchor fill their `bpa` would be about
  -44 to -80, in the same band as the round-15 WR/RB rows that are priced from the anchor at
  negative VOR. Anchoring would not promote them above the board; it would make them
  COMPARABLE.

So the decline is not "the same defect": it does not invert an order the data supports. What it
does is refuse a comparison the data could support, and refuse it in the format where QB is the
scarcest position. That is the `#50` question in its exact words, already stated in
`unpriced_block_composition.py`: the floor asks "startable as a QB" while the slot that makes a
superflex QB draftable competes against flex-eligible non-QBs. Declining is defensible as a
STATED LIMIT; "correct" overstates it, because the board says nothing at all about a QB2 that a
superflex roster would genuinely field over a WR5, and `_board_order` then sorts him behind
every negative-VOR receiver on the tiebreak. The counterfactual A/B that would measure whether
anchor-filling changes any PICK (one process, `_fill_omitted_from_anchor` patched in memory,
anchor caches reset per arm) is written and not yet run — see §6.

## 3. Breadth — measured where it could be, cited where already pinned

**By construction** the startable-floor branch exists only for QB in superflex. Every other
position, every 1QB format, is filled from the pre-draft anchor once demand is exhausted;
`test_absence_survives_consumers.py` and `CDME_CONTRACTS.md` record 0 unpriced rows at rounds
16/18/20 on 1QB and 11 (all QB) on superflex.

**Opening-board sweep, all 36 matrix arms** (`probe_34_floor.py`, fixture: `DataMerger()` from
repo root, `build_players_db_from_capture` 6,595 players, `season_projections_from_capture`
5,346 rows, `weekly_projections_from_capture`, `scoring_settings_from_capture`,
`set_league_format(league_format_hint(league))` per arm, `reset_anchor_caches()` per arm,
`mode="balanced"`, `replacement_levels` spied and tagged by ARGUMENTS):

- 14 superflex arms (8/10/12/14T x standard/half/ppr, plus both CAPTURE arms): QB priced 42/134,
  basis `startable_floor` 42, live-points QB level 207.5 (243.29 under the F&F rulebook).
- 22 non-superflex arms: QB priced 42/134, basis `live_starter_demand`, level 338.16 (8T),
  334.48 (10T), 328.6 (12T), 315.98 (14T).
- Calls observed per build: `LIVE(points)`, `LIVE(trade_value)`; no anchor call on an opening
  board (nothing omitted, so none built — as `_fill_omitted_from_anchor` promises).

**The round at which QB goes all-unpriced** depends on how many QBs the room drafts against the
32 that clear the floor. Real draft, already pinned (`#168`, GSOP2 12x30 superflex, capture
universe, `_build_opponent_boards` replaying the extracted real picks): 32 QBs drafted by round
12 -> 0 priced QBs from round 12 of 30, never recovering. For the matrix arms QB demand is
`teams x 1.85` = 14.8 / 18.5 / 22.2 / 25.9 (8/10/12/14T) against 32 startable QBs, so a
14-team room reaches the state earliest and an 8-team room may not reach it in 15 rounds; the
five production-shaped arms that measure this (`12T_ppr_SF`, `8T/10T/14T_ppr_SF`, `12T_ppr`
control) were launched but had not finished when this document was due (§6).

## 4. What it costs — every consumer of `final_score` / `team_acquisition_value`, with verdicts

Sweep of production modules (worktrees and tests excluded). Verdict key: **OK** = honours
`is None`; **LABELLED** = substitutes a number but records the substitution; **GAP** = a
boundary where absence loses information or would raise.

| consumer | what it does with `None` | verdict |
|---|---|---|
| `pick_synthesis._board_order` / `narrow_candidates` | sorts `score is None` last, tiebreak on `player_id`; unpriced rows still fill the narrowed top-5 when fewer than 5 priced rows remain | OK — but this is the population an `opponent_noise` rival draws from uniformly, which is exactly how Haener/Bennett were taken |
| `build_snapshot` -> `CandidateSnapshot.team_acquisition_value: Optional` | carries `None`; `near_tie_with_leader` `None`; `acting_now_value` `None`; `position_next_turn_value` `None` | OK |
| `compute_pick_necessity` | unpriced candidate gets standout 0.0 (its own documented neutral) and is excluded from others' fields | LABELLED (documented) |
| `draft_strategy._curves_on`, `_forfeit_scale`, `pick_analysis` | `_is_absent` excludes; `opportunity_cost`, `rival_premium`, `denial_value` `None` with a basis | OK |
| `draft_strategy.estimate_survival` | an unpriced target is on the board but has no rank; it receives the take-table FLOOR probability, row tagged `evidenced: False`, `unpriced_mass_share` reported | LABELLED (owner ruling 2026-09-16) |
| `draft_board_ui.serialize_candidate` / JS | `tav: null`; JS `num()`/`fmt()` render the absence marker; `.absent` class; no `?? 0` (pinned by `test_board_renders_absence`) | OK |
| `draft_board_ui` overview sort | `(tav is None, -tav, id)` | OK |
| `app.py _figure` / `design_system.figure` | `None` in, absence marker out | OK |
| `screen_context` | "unpriced" | OK |
| `pick_debate` | "NOT MEASURED — UNKNOWN, never zero"; `_best_alternative` excludes unpriced | OK, except the `why` clause — see GAP 1 |
| `draft_history` | `getattr` -> JSON `null` | OK |
| `draft_room.simulate_opponent_picks` (Mock Draft) | `board[0]` — pandas sorts NaN `final_score` last, so priced when any priced row exists; a feasibility-backstop row (`_feasible` first) can be unpriced and IS taken | OK by design (the backstop is supposed to win) |
| `draft_battery.unpriced_picks` | flags any `tav=None` pick; "every supported configuration, no precondition" | the audit that fired; correct |
| `draft_battery.roster_strength` | `values.get(pid, 0.0)` — but `reference_values` is the PRE-DRAFT board, on which the 42 QBs are priced, so a floor-declined QB gets his pre-draft value there, not 0.0. Only the 92 never-priced rows land at 0.0 (`#165`, open) | LABELLED |
| `draft_counterfactual.compare_trajectory` | `regret_vs_bpa = round(engine_tav - bpa_tav, 3)` unguarded; `engine_tav: float` typed, populated from the chosen candidate's `tav` | **GAP 2** |
| `roster_diagnostics.replacement_level_surplus` | calls `replacement_levels(..., "universal_value", ...)` with NO floors — a second answer to "superflex QB replacement" (demand rank, not cliff) | **GAP 3** (`#126`) |
| `draft_room.replacement_ranks` / `position_view_depth` | deliberately without the floor; `None` -> depth 1 | OK (documented) |

**GAP 1 — `absence_kind` is never `ABSENCE_NO_REPLACEMENT`.** `ABSENCE_KINDS` carries the token
and `ABSENCE_KIND_LABELS` its sentence ("his position has no replacement level to price against
— a STRUCTURAL absence"), but the only stamp is in `_derive_points_and_source`, which writes
`no_input` and says on the record that the third kind "is decided later against the league's own
demand". Nothing later stamps it. A floor-declined QB therefore reaches the snapshot with
`final_score None` and `absence_kind None`; `pick_debate` prints "NOT PRICED" with no `why`, and
the `#112` invariant "a kind is present EXACTLY when the row has no price"
(`test_absence_kind.TheBoardClassifiesOnlyWhatItActuallyKnows`) holds only because its population
is an OPENING board, where the floor-declined set is empty. On a drained superflex board the
invariant is false for ~10 rows. This is `#187` honoured (the value is `None`) and `#112` not
honoured (the kind that explains the `None` is missing) — the vocabulary exists precisely for
this row and is not applied to it.

**GAP 2 — `draft_counterfactual` raises on an unpriced engine pick.** Reachable whenever a chair
takes an unpriced row: the noise arms (measured, `#34`'s own trigger) and the feasibility
backstop (a seat whose QB or SUPER_FLEX slot is still open after the cliff). A harness, not the
UI, but it is the harness that scores the engine against BPA.

**GAP 3 — two homes for the superflex QB level.** The board prices QB off the cliff;
`roster_diagnostics` prices the same roster's QBs off demand rank (`teams x 1.85`). The
ENGINEERING_DOCTRINE `#184` paragraph already records that the fork "has no join"; this is the
same fork observed from the diagnostics side.

## 5. `#187` — is absence `None` throughout?

Yes on every value path traced: `_vor` NaN -> `bpa`/`universal_value`/`final_score` NaN ->
`None` at `_records_with_normalized_nan` -> `Optional` fields on `CandidateSnapshot` -> JSON
`null` -> absence marker on screen. No consumer coalesces to `0.0`. The three places a NUMBER
stands in for absence are all documented and labelled at the point of substitution
(necessity standout 0.0, survival take floor with `evidenced: False`, `roster_strength` 0.0
under `#165`). The one `#187`-adjacent breach is GAP 1: the value is absent correctly, and the
companion that gives the absence its meaning (`#166`/`#174` shape) is absent incorrectly.

## 6. What I could not determine, and what is ready to run

Five production-shaped drafts were launched (`draft_arm.py`, same fixture as §3, mode `auto`,
sharp rivals) and were still running when this document was due; their raw picks save to
`scratchpad/draft_<arm>.json` on completion. Three probes are written and untested against them:

- `rebuild_rounds.py <draft.json> <out>` — the board at every round boundary from seat 1,
  per-position priced/unpriced/`no_priceable_input`/`absence_kind`, QBs clearing the floor,
  spied QB level by call, unpriced rows in the `_board_order` top-12 and in the narrowed top-5.
  This is the measurement that gives the FIRST ROUND of the all-unpriced state per arm and the
  exact split of the 102.
- `counterfactual_fill.py <draft.json> 10,12,14,15 <out>` — DECLINE vs ANCHOR-FILL, one process,
  one toggle, caches reset per arm: does filling QB from the pre-draft anchor change the top-12
  or the narrowed set at any round? If no pick moves, "stated limit" is the whole story; if a
  QB2 enters the top-5, `#50` has a measured stake.
- A `top_k=8, seed=20260922` noise arm on `12T_ppr_SF` to reproduce the trip and count
  `tav=None` picks; not launched (CPU was saturated by the five sharp arms).

Also not determined: whether any SHARP arm ever takes an unpriced row (the backstop case), which
decides how live GAP 2 is outside the noise arms.

## Fixture and provenance

`probe_34_floor.py`, run 2026-09-25 from the repo root as `PYTHONPATH=. python3 ...`, HEAD
`953d21a`. Universe `data/fixtures/sleeper_capture.json` (6,595 players, 5,346 season rows).
Every number above that is not from this probe cites its own record
(`evidence/take_model/unpriced_block_composition.json`, GSOP2 real draft, capture universe,
floor 162.0 on that league's export). Board ordinals are `rank_among_remaining` via
`_board_order` unless stated otherwise; priced counts are `final_score.notna()`, never row counts.
