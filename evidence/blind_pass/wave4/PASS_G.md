# Wave 4, pass G — preserved verbatim

> **The pass's own words, unedited.** Verdicts and novelty live in `LEDGER.md`, not here. A
> finding below is a CLAIM until that file says otherwise.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` built from the branch with the six
> forbidden paths excluded. Mandate: the Wave 4 text (SETUP block, six categories, steering
> paragraph) — see `MANDATE.md` §1 for how that differs from the Wave 1 mandate preserved there.
> Its twin, pass H, was launched from the wrong mandate, killed, and relaunched; see `MANDATE.md` §4.
>
> **Self-reported contamination: none of the six forbidden paths**, verified absent from the
> audit tree before reading. It reports reading `.claude/skills/engine-measurement/SKILL.md`
> (the fixture recipe), which is not on the list and is a measurement aid, not a conclusions
> document. It saw forbidden FILENAMES in code comments without opening the files.

## Report

**Method:** real-data probes on the capture's own `league_shape` (12 teams,
QB/RB/RB/WR/WR/TE/FLEX/SUPER_FLEX/K/IDP_FLEX×2, 14 BN, 25 draftable rounds),
`build_players_db_from_capture()` + `season_projections_from_capture()`,
`set_league_format(league_format_hint(league))`, `SLEEPER_BASIS_SEASON_SUM`, plus one full
300-pick `simulate_full_draft` (mode="auto", 1008 s) audited with `draft_battery.audit_trajectory`.

---

### 1. On the owner's own shape the engine drafts 31 kickers for 12 one-K rosters, and the battery audit passes it with 0 findings

**Measured (full draft, capture shape):** league totals `K=31` (seats 7, 11, 12 took **five**
kickers each; seats 6 and 10 four). First K taken at 8.04; **all twelve seats took a kicker in
rounds 8–9**; 19 non-first kicker picks, **16 of them in balanced-mode rounds (<15)**.
`audit_trajectory` → `findings: 0`, `forced_negative_starters: 7`.

**Mechanism, reconstructed at the actual picks (`draft_room.compute_draft_board`, balanced mode):**

- 8.04 (first K): Dicker `bpa 12.57 + need_bonus 4.00 = 16.57` ranks #1 over Davante Adams
  (`bpa 13.45`, 230 proj pts, final 12.43). Five of the top six rows are kickers. The
  dedicated-slot `need_bonus` (`draft_room.py` ~L3395, `NEED_BONUS_PER_DEDICATED_SLOT=4.0`)
  applied to a position whose whole K1–K12 spread is ~12 points buys a kicker a round-8 pick at
  every seat.
- 11.06 (seat 6's **second** K, balanced): top six rows are all kickers at final ≈ −5.0
  (`bpa −0.09`, `displacement_adj −4.93`, basis `predraft_anchor`). Best remaining RB, Stevenson
  (202 pts, **bpa +10.38, above replacement**) sits at rank 68 with final −32.75 because
  `displacement_adj = −33.51`; best TE Juwan Johnson (bpa +9.85) rank 100 after −46.03; a QB
  projected 282 pts (bpa +74.39) rank 49 after −99.71. Only **32 of ~690 priced rows** carry
  non-negative VOR at pick 125 of 300.

So `displacement_adj` (`#216`, built to stop TE hoarding) deducts 33–100 points from every
RB/TE/QB whose slots the roster has filled, while a spare kicker is deducted the K1–K12 spread
(≈5). A second, third, fourth kicker therefore out-ranks an above-replacement running back by
~28 points, in the mode production actually runs. Files: `draft_room.py:2631`
(`displacement_adjustments`), `score_row` ~L3400–3480, `lineup_optimizer.py:354`.

**Why nothing caught it:** `draft_battery.league_matrix` (`draft_battery.py:58–200`) has **0 of 34
arms with a K slot and 0 arms combining SUPER_FLEX with any IDP slot** (verified
programmatically); `build_mock_league` (`draft_room.py:3583`) never emits K/DEF/IDP.
`structural_findings` (`draft_battery.py:310`) checks only legality
(unfilled/unpriced/undraftable/duplicate), so a legal roster with five kickers is a clean arm.
Only 5 test modules touch the capture's `league_shape`, and those build pre-draft boards, never a
draft.

### 2. `displacement_adj` is positive on the real shape; four docstrings and the necessity layer's bound say it cannot be

**Measured (pre-draft, empty roster, capture shape):** Travis Hunter (WR primary, WR/DB eligible)
`displacement_adj = +79.44`, basis `measured`; UV −158.05 → TAV −70.23; UV rank 630 → TAV rank
350. Single-position WR peers at the same UV (Turpin −157.30) have TAV −148.92. **TAV − UV =
87.82** against the claimed cap of 36.0. Still +79.44 after the roster holds 2 WR + 2 DB.

**Claims contradicted:** `draft_room.py:2631` ("`<= 0.0, never positive`", "non-positive by
construction"); module docstring ~L40 ("the only one that can be negative … Zero wherever a slot
he can reach is open"); `lineup_optimizer.py:354` return docstring ("`adjustment` is
free_alternative − displaced (<= 0.0)"); `pick_synthesis.py` ~L330–345 (`TEAM_SPECIFIC_CAPS`:
"sum … remains the UPPER bound on team_acquisition_value − universal_value", which derives
`NECESSITY_DENIAL_SATURATION` and `CONTEXT_ELEVATED_THRESHOLD`); `pick_synthesis.py:805`
`decision_path_flags` docstring ("TAV can never fall below UV … structurally impossible" — also
false: every DL row on the empty-roster board has TAV − UV = −32.87).

**The code does it on purpose:** `lineup_optimizer.py` ~L500 clamps
`displaced = max(displaced, min(alt_of[reachable]))` with a comment that a multi-eligible probe
"is not silently clamped up to that anchor". Mechanism: primary-position level (WR, high) minus
the IDP_FLEX shared alternative (LB level, low). This is exactly the uncapped multi-eligibility
lift that `ELIGIBILITY_BONUS_MAX` was introduced to prevent (docstring: "the Travis-Hunter case
this module was built for"), reintroduced through the fourth term with no cap.

**Instruments pinned where it cannot fail:** `test_216_displacement.py:75` uses single-position
probes and no `slot_alternatives`; `:190` asserts `<= 0` "on the real rulebook" but `_rulebook()`
(`:143`) builds `build_mock_league(superflex=False, …)` — no IDP slot, so no lower-alternative
slot is reachable. `test_draft_room.py:1872` (eligibility cannot flip a gap) runs vendor-only, so
IDP has no points level and `shared_slot_alternatives` carries no IDP_FLEX entry.

### 3. Round is off by one at every round-opening pick

`pick_synthesis.build_snapshot` L1545: `round_num = max(p["round"] for p in picks)` — the round of
the **last completed** pick. Same at `draft_room.compute_draft_board` ~L2985 (`current_round`).
**Measured:** pick `15.01` → `snapshot.round = 14`, leader necessity 68.5 "PREFERRED", no growth
signal (balanced); pick `15.02` → round 15, necessity capped to 21.0, upside. Consequences:
`format_snapshot_for_llm` prints "PICK 15.01 (round 14)"; `LATE_ROUND_NECESSITY_CAP` (×0.3) skips
the first pick of every late round; `draft_simulation._picks_by_mode` (L87) reports 168/132 but
the trajectory has 169 balanced / 131 upside picks (chosen `growth_signal` None at 15.01). Live
Sleeper picks carry `round` the same way, so production is affected identically.

### 4. Survival is "withheld as uncalibrated" from people and chairs, but still drives `pick_necessity` and the MUST TAKE label they do see

`pick_synthesis.py:527` `SURVIVAL_IS_CALIBRATED = False`; `decision_regime` (L1003) is gated on
it; `draft_board_ui.py:254` and `pick_debate.py:428` suppress the number. But
`compute_pick_necessity` L619 `survival_component = (1 − survival) × 20` is **not gated**. The
calibration note itself (pick_synthesis ~L505) says the 0.0–0.1 predicted bucket is observed
0.500 — that bucket gets the maximum +19.4 boost. **Measured on the draft:** 288 of 300 leaders
carry `survivalWithheld=True` with a survival value present; leader labels included 6 MUST TAKE /
19 STRONG ACTION.

**Prompt boundary (`pick_debate.py` ~L170–260):** all three system prompts still tell the chairs
they are given `survival_probability`, `opportunity_cost`, `expected_value_of_waiting`; the Caller
prompt's KEY FACTOR example is `"19% survival with a QB run detected"`. The evidence block says
the survival "is WITHHELD … do not estimate one yourself", so the model is instructed to cite a
number the same conversation says it must not have — an invitation to fabricate exactly what the
module docstring forbids.

### 5. `league_config`'s "only blocking state" blocks nothing — the gate has no production caller

`league_config.py:213–261` (`admits_decision`, `decision_config`, `confirmation_state`, AMBIGUOUS
"the only blocking state", "Never a degraded fallback") — grep: no caller outside tests. `app.py`
imports it only for `describe_config_age` (L63, L1682). An unknown roster slot (docstring: "a slot
whose players the lineup solver will silently fail to place") passes straight through:
`slots_from_roster_positions` (`lineup_optimizer.py:50`) silently drops it. Worse if it were
wired: `FORMAT_DECIDING_KEYS` (L117) includes `bonus_rec_te`, which the capture's own
`scoring_settings` lacks → the owner's real league would be AMBIGUOUS and refused (`ambiguities`
L182).

### 6. Flex-slot demand is always the even split; docstrings claim it is measured and that the basis is reported

`draft_room.py:673` `board_flex_share` unconditionally `return None` (documented seam, "MEASURED,
NOT WIRED"). But `starter_slot_counts` docstring (L782+) says "MEASURED … This is the answer
whenever a pool exists, and compute_draft_board always supplies it"; `compute_draft_board` L3023
says "slot_share_basis says so" — `slot_share_basis` is called nowhere in production, so no row
ever states `even_flex_split`; `SUPER_FLEX_QB_SHARE` (L337) comment says "Under the measured
branch the constant is not consulted at all" while the measurement it cites returns QB 1.00 — the
hand-set 0.85 is live for every superflex league. `roster_points_lookup` is still evaluated at
L3025 to feed the argument that is discarded.

### 7. Team-term constants were derived on a 0–100 bpa scale that no longer exists

`_scale_vor_to_bpa` (`draft_room.py:2162`) is now the identity. **Measured pre-draft board:** `bpa`
min −225.49 / p10 −189 / median −65.6 / max +220.6. Against that: `NEED_BONUS_MAX=12`,
`ELIGIBILITY_BONUS_MAX=12` via ratio `12/100` (L510–535, comment still says
"team_acquisition_value is a bpa-scale sum … Nabers bpa 18.0 vs trade_value 81.0" — old-scale
numbers), `DEPTH_EXPOSURE_MAX=12`, `RISK_ADJ IR −18` (L419), `TIME_HORIZON_CLAMP ±10`. Module
docstring L100–115 still says eligibility "IS now rescaled into universal_value's own bpa scale".
`pick_synthesis.py` ~L370 (`FORFEIT_SCALE_MAX`) says "that scale is CONSTRUCTED so 100 is the
largest real VOR gap in the remaining pool" — stale. `test_draft_room.py:1288` (`need_bonus cannot
flip a large gap`) is algebraically trivial: it asserts `top−bottom > NEED_BONUS_MAX` as a
precondition and then `top−bottom−NEED_BONUS_MAX > 0` — the same inequality. (Sibling:
`upside_score` L2123 adds a 0–100 percentile difference ×0.5, unclamped, to raw-point bpa — same
units class as the known `time_horizon_adj` issue, larger weight.)

### 8. Absence handling: unpriced rows carry a "measured" displacement and a need_bonus

Empty-roster board: **612 rows** carry `displacement_adj −28.28/−32.87` with basis `measured`,
including ~400 DB/DL rows with `bpa = NaN` (e.g. Cam Lampkin, Von Miller). This is the `#203`
shape ("no price, nothing to adjust") that was repaired for `risk_adj` (score_row ~L3440) and not
for the fourth term or `need_bonus` (0.67 on unpriced rows). `pick_debate._displacement_term` will
print "+ displacement_adj −28.28" as a measurement beside "Universal value: NOT PRICED".

### 9. Two health models answer the same question with different magnitudes depending on which source priced the row

Same status, different penalty by pricing path: Jayden Higgins (WR, IR, vendor-priced 173 pts)
`risk_adj −18.0`, `availability_basis` None; Jordyn Tyson (WR, IR, Sleeper-priced 125 pts)
`risk_adj 0.0`, basis `rule_floor` (4/17 games ≈ 23.5% of points, `player_universe.py:102`). For a
173-pt player the two models say −18 vs −40.7. `health_penalty` (`draft_room.py:421`) documents the
split but not that the magnitudes disagree.

### 10. Mock Draft never sets `draft_rounds`; the `#161` backstop repair is inert there

`app.py:4824` builds `mock_league` via `build_mock_league` and never assigns `draft_rounds` (only
the live path does, `app.py:5344`); `cfg_rounds` is 1–30. `feasibility_first`
(`draft_room.py:2916`) falls back to `len(roster_positions)` (14/15), so the sandbox backstop
counts the wrong number of picks left for any configured round count ≠ roster size.

### 11. Certification battery drafts a mode production never runs

`app.py:5381` calls `build_snapshot` without `mode` → "balanced" for all 25 rounds (documented
`#115`). The battery runs `mode="auto"` → on the owner's shape 131 of 300 picks (44%) are
upside-mode picks with all team terms zeroed. The late-round behaviour actually shipped (balanced,
rounds 15–25) is exercised by no arm (`12T_ppr_mode_balanced` is 14 rounds).

### 12. Smaller items

- `pick_debate._match_candidate` (~L560): substring fallback returns the **first candidate in
  snapshot order** whose name is contained in the text; "RECOMMENDATION: Josh Allen over Jalen
  Hurts" resolves to whichever of the two sorts first, and "Michael Carter II (DB)" resolves to RB
  Michael Carter. Docstring: "never a guess".
- `draft_board_ui.filter_candidates_by_view` (L336) comment claims candidates are "already sorted
  by team_acquisition_value descending", but `_board_order` puts `fills_required_slot` rows first,
  so the ALL overview's top slice is not the top-N by value when the backstop binds.
- `draft_board_ui` JS interpolates `c.name`/`pickHeader`/tag labels into `innerHTML` unescaped;
  only `<` is escaped in the JSON. Names come from Sleeper, so low risk; noted as a boundary.
- Text-scanning guards where an AST walk exists in the same suite: `test_depth_basis_boundary.py:45`
  asserts the literal `'"depth_basis": row.get("depth_basis")'` in source (defeated by a whitespace
  change, satisfied by a comment); `test_tenant_scope_boundary.py:56` `assertIn("league_id", source)`
  on `_path` bodies (a comment satisfies it while the return drops the key).
- `pick_debate` system prompts describe TAV as three terms (need, eligibility, depth); the evidence
  sum has four.
- `league_format_hint`/`league_format_summary`: `rec ≥ 1` → ppr, `== 0.5` → half, else standard; a
  0.75-PPR league selects the standard export.
- Data: under the capture hint, 18 players' vendor `projection` and 15 winning rows come from
  `dynasty_superflex_rankings.csv`, which `_detect_rankings_format` tags "standard" scoring, in a
  PPR league (field-level merge, `data_merger.py:1398`). Small (vendor points are overridden by
  Sleeper sums for 803/820 rows) but the format axis is not airtight.

### Null results (examined, nothing serious found)

- `store_io.py`: atomic replace, sidecar lock, refuse-to-overwrite-damaged-store, lock depth
  counting all hold up; the only observation is that `write()` silently drops data for a store
  marked unreadable, which is documented.
- `DataMerger.merge_player` memo is cleared in `_load`, so `set_league_format` cannot serve a stale
  export (checked because the battery depends on it).
- `_reconcile_rows`: 0 of 264 rows mix `projection` and `proj_3yr` across files on the capture hint.
- `untrusted.fence`/`_report_for_handoff`/`annotate_if_incomplete`: consistent; truncation notice is
  appended, not prepended, so a truncated chair is not misread as a failed one.
- `estimate_survival` three-state contract and `pick_analysis` denial/rival-premium basis handling
  are internally consistent with their docstrings.
