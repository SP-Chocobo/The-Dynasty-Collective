# `#34` — every remaining superflex QB is unpriced from mid-draft on

**Verdict: (c) correct in the draft loop, a hazard at consumer boundaries — and NOT a new
finding.** The state is already on the register as `#168` (sharpened), pinned by
`test_qb_pricing_cliff.py` against `evidence/take_model/unpriced_block_composition.json`, with
the design question ("startable AS A QB" versus "wins a SUPER_FLEX slot") explicitly deferred to
`#50`/Phase 3. What `#34` adds: (i) a correction to its own framing — the 102 unpriced QBs are
two populations, 92 never priced by anyone and 10 de-priced by the floor decline; (ii) a
measured counterfactual showing that anchoring those 10 instead of declining moves NO pick;
(iii) a scale mismatch in the floor's derivation; and (iv) three consumer-boundary gaps the
existing absence tests never reach because their populations are opening boards.

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

Downstream: `_vor` is NaN for every row whose position is not in `point_replacement`; `bpa`,
`universal_value`, `final_score` follow; `_records_with_normalized_nan` turns them into real
`None` at the board boundary; `pick_synthesis._board_order` sorts `score is None` last.

Measured live (`rebuild_rounds.py`, `10T_ppr_SF`, spied `replacement_levels` tagged by
arguments): the `LIVE(points)` call returns QB = 207.5 (`startable_floor`, 13 QBs priced) at
round 14 and returns **no QB key at all** at round 15, where 0 of 102 remaining QBs clear
163.5; no anchor call fires for QB; every QB row goes out `final_score None`,
`replacement_basis None`.

**Addition A — the floor is on the vendor scale, the comparison is on the league-scored scale.**
`qb_startable_floor` reads `merger.projections["projection"]` (the vendor export selected by
`set_league_format`). Under the production pricing path `_points` is the Sleeper season sum
scored under the league's rules (`_derive_points_and_source`; `points_vor_sleeper_season_scored`
on 34 of the 42 priced QBs). Opening board, every arm:

| arm hint | floor (vendor) | QB12 vendor | QB12 board `projected_points` | clear floor, vendor col | clear floor, board col |
|---|---:|---:|---:|---:|---:|
| ppr / half_ppr SF | 163.5 | 327.0 | 328.6 | 29 | **32** |
| standard SF | 162.0 | 324.0 | 328.6 | 29 | **32** |
| CAPTURE_fourth_and_forever | 162.0 | 324.0 | **357.84** | 29 | 32 |

A fraction of one source's QB12, applied to a different source's totals. Today both land in
the same cliff (32 on the board column either way), so `QB_STARTABLE_FLOOR_FRACTION`'s
stability-basin argument survives — but that argument was made on the vendor column and is
cashed on the scored one, and under the F&F rulebook QB12 is 10% higher on the board than on
the vendor. A derivation whose premise has moved; `#56` is not engaged, no constant proposed.

**Addition B — the 102 is two populations.** Opening `12T_ppr_SF` board: 134 QB rows, 42
priced (basis `startable_floor`, level 207.5 = the 32nd QB), **92 `no_priceable_input` from
pick 1** (no projection from either source, `absence_kind = no_input`). At the `10T_ppr_SF`
final board, 32 QBs drafted: 102 QB rows, 102 unpriced — **92 never priceable, 10 de-priced by
the decline** (`unpriced_with_points = 10`). The `#168` record measured the same split on the
real GSOP2 draft (unpriced QB 113 -> 123 across the cliff). The headline is 90% vendor coverage
and 10% this mechanism.

## 2. Is the behaviour correct? Is it the K/DEF pathology in different clothes?

Not analogous, and now measured rather than argued. `counterfactual_fill.py`, one process, one
code version, one toggle (`_fill_omitted_from_anchor` patched in memory to ignore the floor
exclusion; `reset_anchor_caches()` between arms), `10T_ppr_SF` final board, seat 1:

| | DECLINE (production) | ANCHOR-FILL (counterfactual) |
|---|---|---|
| priced rows | 321 / 820 | 331 / 820 |
| QB priced | 0 | 10 (basis `startable_floor`, level 207.5) |
| top-12 by `_board_order` | 12 WR/RB, all `predraft_anchor`, −67.4 … −92.9 | **byte-identical** |
| unpriced rows in top-12 | 0 | 0 |
| unpriced rows in narrowed top-5 (+best-at-position) | 1 | 0 |
| best QB `rank_among_remaining` | none | **108** (Penix, 129 pts, final_score −173.4) |

The ten de-priced QBs are Michael Penix 129.0, Shedeur Sanders 95.2, Carson Beck 56.0,
J.J. McCarthy 34.0, Kirk Cousins 31.3, Ty Simpson 30.0, Cade Klubnik 28.0, Drew Allar 15.0,
Jalen Milroe 0.0, Anthony Richardson 0.0 projected points. Anchored, they price at −173 to −294
and rank 108th to 331st among 820 remaining rows.

So the K/DEF inversion — a position whose players projected ABOVE their own pre-draft level and
were sorted below everything — does not recur here. These rows project far below the level;
pricing them changes no ordering a chair acts on. Declining is a STATED LIMIT that costs no
pick on this data. It is not the same defect. What it is: a refusal to state a number the data
could state, at the one position the format makes scarcest, which is `#50`'s question exactly
as `unpriced_block_composition.py` frames it (the floor asks "startable as a QB"; the slot that
makes a superflex QB draftable competes against flex-eligible non-QBs). The measured stake of
that question, on this universe, is the ordering of a 129-point backup against 140-point
receivers — real for a roster with an open SUPER_FLEX, and nil for the board's top.

The one live effect of declining: `narrow_candidates` always includes each position's best
remaining player, priced or not, so from the cliff on the candidate set carries exactly one
unpriced QB. A sharp chair never takes him (`_board_order`); an `opponent_noise` rival drawing
uniformly from top-k can, which is how Haener and Bennett were taken and why `unpriced_picks`
fired. That audit is doing its job; the row it flags is a limit, not a mis-ordering.

## 3. Breadth — measured

**By construction** the startable-floor branch exists only for QB in superflex. Every other
position, every 1QB format, is filled from the pre-draft anchor once demand is exhausted;
measured here at every round of both completed arms: no position other than QB is ever
all-unpriced (`all_unpriced_positions == []` at rounds 0-14 of 10T and 0-15 of 8T; `['QB']` at
10T round 15).

**Opening-board sweep, all 36 matrix arms** (`probe_34_floor.py`; fixture in §7):
14 superflex arms price QB 42/134 at `startable_floor`, live level 207.5 (243.29 under the F&F
rulebook); 22 non-superflex arms price the same 42 at `live_starter_demand`, level 338.16 /
334.48 / 328.6 / 315.98 for 8/10/12/14 teams. Calls per opening build: `LIVE(points)`,
`LIVE(trade_value)`; no anchor built (nothing omitted).

**When the state arrives** depends on QBs drafted against the 32 that clear the floor; QB
starter demand is `teams × 1.85` = 14.8 / 18.5 / 22.2 / 25.9 (8/10/12/14T), and every superflex
matrix arm is `QB RB RB WR WR TE FLEX FLEX SUPER_FLEX + 6 BN`, 15 rounds, no K/DEF.

| arm | source | QBs drafted by end | first board with 0 priced QBs | QB priced at last board |
|---|---|---:|---|---:|
| 8T_ppr_SF | sharp sim, 120 picks, 917.6 s | 31 | never (1 QB still clears at R15) | 11 (rank 1: level = best remaining QB) |
| 10T_ppr_SF | sharp sim, 150 picks, 1334.8 s | 32 (last at 15.10) | round 15 = after the final pick | 0 of 102 (10 with points) |
| 12T_ppr_SF | the finding's arm; my run was killed (§6) | — | finding: ~round 15 | finding: 0 of 102 |
| GSOP2 12x30 real draft | `#168` record, capture universe | 34 | round 12 of 30 | 0 |

The state is reached inside a 15-round draft only from 12 teams up; at 10 teams it arrives with
the last pick; at 8 teams it does not arrive. The real 30-round draft reaches it at round 12 and
never recovers. Both sharp arms: **0 picks with `tav=None`, 0 picks whose narrowed set carried
an unpriced candidate** — in these room sizes the decision surface never sees the state before
the draft ends; a longer draft (26-30 rounds, both CAPTURE arms) or a 12-14 team room does.

The transition is abrupt: 10T round 14 prices 13 QBs (`startable_floor`, 3 clearing the floor);
round 15 prices 0. At 8T round 15 exactly one QB clears, rank 1, so the level IS the best
remaining QB and the other ten priced QBs carry negative VOR against him — the documented
rank-1 edge of the domain, reachable on the floor branch too.

## 4. What it costs — every consumer of `final_score` / `team_acquisition_value`

Sweep of production modules (worktrees and tests excluded). **OK** = honours `is None`;
**LABELLED** = substitutes a number and records it; **GAP** = absence loses information or
would raise.

| consumer | behaviour on `None` | verdict |
|---|---|---|
| `pick_synthesis._board_order` / `narrow_candidates` | sorts `score is None` last, `player_id` tiebreak; best-at-position rule admits one unpriced QB to the candidate set from the cliff on (measured: 1 at 10T R15) | OK — but this row is what a noise rival draws |
| `build_snapshot` -> `CandidateSnapshot` | `team_acquisition_value`, `near_tie_with_leader`, `acting_now_value`, `position_next_turn_value` all `Optional`, carried as `None` | OK |
| `compute_pick_necessity` | unpriced candidate: standout 0.0 (its own neutral), excluded from others' fields | LABELLED |
| `draft_strategy._curves_on`, `_forfeit_scale`, `pick_analysis` | `_is_absent` excludes; `opportunity_cost`, `rival_premium`, `denial_value` `None` with a basis | OK |
| `draft_strategy.estimate_survival` | unpriced target gets the take-table FLOOR probability, row `evidenced: False`, `unpriced_mass_share` reported | LABELLED (owner ruling 2026-09-16) |
| `draft_board_ui.serialize_candidate` / JS | `tav: null`; `num()`/`fmt()` render the absence marker; no `?? 0` (pinned by `test_board_renders_absence`) | OK |
| `draft_board_ui` overview sort | `(tav is None, -tav, id)` | OK |
| `app.py _figure` / `design_system.figure` | `None` in, marker out | OK |
| `screen_context` | "unpriced" | OK |
| `pick_debate` | "NOT PRICED — UNKNOWN, never zero"; `_best_alternative` excludes unpriced | OK except the `why` clause — GAP 1 |
| `draft_history` | `getattr` -> JSON `null` | OK |
| `draft_room.simulate_opponent_picks` (Mock Draft) | `board[0]`; pandas sorts NaN last, so priced when any priced row exists; a feasibility-backstop row (`_feasible` leads) can be unpriced and IS taken | OK by design |
| `draft_battery.unpriced_picks` | flags any `tav=None` pick, no precondition | the audit that fired; correct |
| `draft_battery.roster_strength` | `values.get(pid, 0.0)` — `reference_values` is the PRE-DRAFT board, on which all 42 QBs are priced, so a floor-declined QB keeps his pre-draft value; only the 92 never-priced rows land at 0.0 (`#165`, open) | LABELLED |
| `draft_counterfactual.compare_trajectory` | `regret_vs_bpa = round(engine_tav - bpa_tav, 3)` unguarded; `engine_tav: float` typed, populated from the chosen candidate's `tav` | **GAP 2** |
| `roster_diagnostics.replacement_level_surplus` | `replacement_levels(..., "universal_value", ...)` with NO floors — a second answer to "superflex QB replacement" (demand rank, not cliff) | **GAP 3** (`#126`) |
| `draft_room.replacement_ranks` / `position_view_depth` | deliberately floor-free; `None` -> depth 1 | OK (documented) |

**GAP 1 — `absence_kind` is never `ABSENCE_NO_REPLACEMENT`, and the invariant test cannot see
it.** `ABSENCE_KINDS` carries the token and `ABSENCE_KIND_LABELS` its sentence ("his position
has no replacement level to price against — a STRUCTURAL absence"), but the only stamp is in
`_derive_points_and_source`, which writes `no_input` and says on the record that the third kind
"is decided later against the league's own demand". Nothing later stamps it. Measured on the
10T final board: **10 unpriced QB rows with `absence_kind None`** (0 on every board before the
cliff; the 92 coverage-gap rows are correctly `no_input`). `pick_debate` therefore prints "NOT
PRICED" with no `why` for exactly the rows the third kind was written for, and `#112`'s
invariant "a kind is present EXACTLY when the row has no price"
(`test_absence_kind.TheBoardClassifiesOnlyWhatItActuallyKnows`) holds only because its population
is an opening board. `#187` is honoured (the value is `None`); `#112`'s companion is not.

**GAP 2 — `draft_counterfactual` raises on an unpriced engine pick.** Reachable whenever a chair
takes an unpriced row: the noise arms (`#34`'s own trigger) and the feasibility backstop (a seat
whose QB or SUPER_FLEX slot is still open after the cliff). A harness, not the UI, but the one
that scores the engine against BPA. Not reached by either sharp arm here (0 such picks).

**GAP 3 — two homes for the superflex QB level.** The board prices QB off the cliff;
`roster_diagnostics` prices the same roster's QBs off demand rank. ENGINEERING_DOCTRINE's `#184`
paragraph already records that the fork "has no join"; this is the same fork seen from the
diagnostics side.

## 5. `#187` — is absence `None` throughout?

Yes on every value path traced: `_vor` NaN -> `bpa`/`universal_value`/`final_score` NaN ->
`None` at `_records_with_normalized_nan` -> `Optional` on `CandidateSnapshot` -> JSON `null` ->
absence marker on screen. No consumer coalesces to `0.0`. The three places a NUMBER stands in
for absence are documented and labelled at the point of substitution (necessity standout 0.0;
survival take floor with `evidenced: False`; `roster_strength` 0.0 under `#165`). The one
`#187`-adjacent breach is GAP 1: the value is absent correctly and the companion that gives the
absence its meaning (`#166`/`#174` shape) is absent incorrectly.

## 6. What I could not determine

- The finding's own arm, `12T_ppr_SF`, plus `14T_ppr_SF` and the `12T_ppr` 1QB control, were
  launched alongside the two arms above and were killed externally mid-draft (empty logs, no
  traceback, no output; the five-way CPU contention is the likely cause). `12T_ppr_SF` was
  relaunched alone at the end of this session; if `scratchpad/draft_12T_ppr_SF.json` exists,
  `rebuild_rounds.py` and `counterfactual_fill.py` run against it unchanged and give the
  first-blind-round and the counterfactual on the finding's exact fixture.
- A `top_k=8, seed=20260922` noise arm reproducing the trip was not run (CPU).
- Whether any SHARP arm in a 12-14 team room ever takes an unpriced QB through the feasibility
  backstop (which decides how live GAP 2 is outside the noise arms). Not reached at 8 or 10 teams.

## 7. Fixture and provenance

All probes in the session scratchpad, run 2026-09-25 from the repo root as
`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3 ...`, HEAD `953d21a`. `DataMerger()` from root;
`build_players_db_from_capture` (6,595 players) and `season_projections_from_capture`
(5,346 rows), `weekly_projections_from_capture`, `scoring_settings_from_capture`, all from
`data/fixtures/sleeper_capture.json`; `set_league_format(league_format_hint(league))` before
every arm; `reset_anchor_caches()` between arms; boards built `mode="balanced"` with
`sleeper_basis=SEASON_SUM` and weekly projections; drafts via `simulate_full_draft` in
production shape (`mode="auto"`, `UPSIDE_RULE_ROUND`, sharp rivals; 8T split 112 balanced / 8
upside, 10T 140 / 10); board-and-draft universe asserted shared (`set(board ids) >= drafted`);
`replacement_levels` spied and tagged by ARGUMENTS, never by call order. Ordinals are
`rank_among_remaining` via `_board_order` unless stated; priced counts are
`final_score.notna()`, never row counts. Numbers not from these probes cite their own record
(`evidence/take_model/unpriced_block_composition.json`: GSOP2 real draft, capture universe,
floor 162.0 on that league's export).
