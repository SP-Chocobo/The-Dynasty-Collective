# Pass B — absence semantics, boundaries, and prose claims (wave 1)

Reproduced verbatim from the agent's hand-back. Not edited, not corrected. Finding 1 was later
confirmed and WIDENED by the SKEPTIC (the panel renders all three withheld quantities, and there is
an additional ungated read at draft_board_ui.py:788) — see `skeptic.md`.

---

## Audit report — absence semantics, boundaries, and prose claims

### Process notes (read first)

- **Contamination statement: I did not open any forbidden path.** I never read FREEZE_RECORD.md, FREEZE_RECORD_V2.md, FREEZE_CHECKLIST.md, POST_AUDIT_PLAN.md, DOC_INDEX.md, or anything under evidence/smoke_seats, evidence/batteries, evidence/blind_pass, evidence/design_35, evidence/upside_gap. Code comments in pick_synthesis.py / draft_board_ui.py cite files in evidence/smoke_seats by name; I saw the citations, not the files.
- **Which code I audited.** The assigned worktree (`.claude/worktrees/agent-a65c10e3bce55300f`) is on `main` at cf8fa0c, which does NOT contain draft_battery.py, run_draft_battery.py, league_config.py, invariant_registry.py, prose_names.py, quantity_readers.py, or basis_semantics.py, and its draft_room.py is 2051 lines. The main checkout at /home/user/The-Dynasty-Collective is on `claude/fantasy-football-control-center-ff6qlu` (draft_room.py 4445 lines, pick_synthesis.py 2146) and matches the task description. I audited that branch. To honour "run from the repo root" without `cd`-ing into the shared checkout, I copied its working tree (verified identical to the branch HEAD for draft_room.py) into my scratchpad with tar, **excluding every forbidden file and directory**, and ran all probes from that copy with `PYTHONPATH=.`. All line numbers below refer to that branch.
- Real-data fixture used exactly as specified (build_players_db_from_capture tuple, season_projections_from_capture, set_league_format(league_format_hint(league))). Probe scripts are in the scratchpad (probe1–4.py); nothing in the repo was modified.

---

### 1. HIGH — The recommendation panel renders the withheld survival family without asking the withholding policy

**Where:** app.py `_render_pick_metrics`, lines 1543–1546 (`f"{round(rec.survival_probability * 100)}%" if rec.survival_probability is not None else "—"`), 1565–1577 (opportunity_cost and expected_value_of_waiting cards via `_figure`), and 5660–5661 (`alt_survival` caption "Survival: NN%" for the best alternative). `grep withheld_fields\|survival_is_presentable app.py` returns nothing.

**The claim it breaks:** pick_synthesis.py:626–657 `withheld_fields()` — "A quantity withheld from presentation must not reach a person, on any surface, under any name, as itself or as a delta of itself." SURVIVAL_IS_CALIBRATED is False (line 597), so the family is withheld everywhere else: the board JS redacts on `survivalWithheld`, pick_debate skips the lines, screen_context substitutes the pick count, diff_snapshots filters. test_withheld_propagation.py covers those five surfaces and not this one; invariant_registry.py:121–133 concedes the census "cannot, by construction, see a surface that never asks at all".

**Failure scenario:** run a debate in the Draft Room (or Mock Draft). `debate_result.recommended` is a CandidateSnapshot whose `survival_probability` is populated (probe1: leader carried 0.827). The card labelled "Survival to Next Pick (%)" (design_system.py:291–297, help text: "Chance he is still on the board at your next turn, compounded across every intervening pick…") renders "83%", the Opportunity cost and Expected value if you wait cards render the derived numbers, and the runner-up caption prints "Survival: NN%". The board directly above the panel shows the same candidate with survival redacted as "not shown". The design_system help text makes no mention of withholding.

---

### 2. HIGH/MEDIUM — `need_bonus` is fabricated as 0.0 at the snapshot boundary in upside mode; every other absent term crosses as None

**Where:** pick_synthesis.py:1739 `"need_bonus": row.get("need_bonus", 0.0)` inside build_snapshot; CandidateSnapshot.need_bonus annotated `float` (line 1436), not Optional. The upside board emits the column list named BALANCED_BOARD_COLUMNS (draft_room.py:2545–2564, names inverted as the comment admits), which has no need_bonus / depth_exposure / displacement_adj / time_horizon_adj / risk_adj. build_snapshot carries the other four as None with explicit "never 0.0" comments (lines 1745, 1750, 1753); need_bonus alone is defaulted.

**Measured (probe1, 8T_standard, real capture, mode="upside"):** leader Jahmyr Gibbs: `need_bonus 0.0`, `depth_exposure None`, `displacement_adj None`, `time_horizon_adj None`, `risk_adj None`. It then reaches every serialization:
- pick_debate `_format_candidate` (pick_debate.py:400–405) prints to the chairs: `Team acquisition value: 149.53 (universal_value 149.53 + need_bonus +0.0; depth_exposure not computed for this board; displacement_adj not computed for this board)` — need_bonus stated as a measured term beside two honestly-withheld ones.
- draft_board_ui.serialize_candidate → `needBonus: 0.0` (line 283).
- draft_history.candidate_evidence → `need_bonus: 0.0` persisted.
- compute_pick_necessity roster_fit_component (pick_synthesis.py:~812) reads it as 0.

**Who reaches upside mode:** draft_simulation.simulate_full_draft defaults `mode="auto"` (every battery arm; every pick from round 15), the `12T_ppr_mode_upside` arm, and `upside_rule=CROSSING`. The human Draft Room path passes no mode and stays balanced.

---

### 3. MEDIUM — In upside mode `rival_premium` is a "measured" 0.0 on every candidate, and it is not a measurement

**Where:** draft_strategy.pick_analysis (lines ~1140–1160) computes `premium = opp_row["final_score"] - opp_row["universal_value"]` and sets `rival_premium_basis = DENIAL_MEASURED`. The upside branch sets `universal_value = final_score` (draft_room.py:3895) and computes no team terms, so the difference is identically 0 by construction.

**Measured (probe4, 12T_ppr, 96 picks made, pick 9.01):** mode="upside": `rival_premium/basis = (0.0, 'measured') × 21`, block_opportunity False × 21. mode="balanced" at the identical state: premiums 4.67 (×14), 4.0 (×4), 11.28 (×3).

**Consequence:** basis says "measured, no rival gains" where nothing was computed; `block_opportunity` can never fire; `denial_component` is always 0; the snapshot's "measured zero vs unmeasured" distinction (the #187 vocabulary) is collapsed for the whole upside regime. Affects every auto-mode battery pick after round 15 and the upside arm.

---

### 4. MEDIUM — `depth_exposure` and its basis describe a roster the optimizer never saw; the basis vocabulary has no "partial" state

**Where:** draft_room.py:2344–2436 `_team_roster_players` drops any rostered player with no vendor trade_value (`if value is None: continue`); lineup_optimizer.depth_exposure (249–375) then labels the result EXPOSURE_VACANT / NO_SURPLUS / MEASURED. The displacement term got DISPLACEMENT_ROSTER_PARTIAL for exactly this hole (`_team_roster_points_players`, 3099–3125); depth got nothing.

**Measured (probe2/probe3, HEAVY_IDP arm, real capture; 58 of 85 priced LBs carry no trade value):**
- Roster 1 drafts one LB with no trade value (Drue Tranquill, 146 projected pts). Every LB candidate then carries `depth_exposure 0.0, basis vacant`, whose label (lineup_optimizer.py:221) is "not measured -- you hold no starter at this position to insure". The roster holds one. Drafting Jack Campbell (tv 33) instead yields `no_surplus`.
- Roster 1 holds LB A (tv 33), LB B (tv 14), bench LB C. With C = Zack Baun (tv 35): every LB candidate `depth_exposure 2.52, basis measured`, top LB TAV 1.89. With C = Tranquill (no tv): `0.0, no_surplus` ("some starter here has no cover" — false, LB3 exists), top LB TAV −0.63. Same roster shape, TAV of every LB candidate moves 2.52 purely on whether the vendor priced the bench body, and the basis token claims a full measurement either way.

The `_team_roster_players` docstring records the hole and the two candidate repairs; the basis that crosses the boundary does not.

---

### 5. MEDIUM — The staleness stamp cannot see most of the inputs that change a board; a stale debate is presented as current

**Where:** pick_synthesis.py:2040–2087 `stamp_is_current` checks only `len(picks) == picks_consumed` and `merger.freshest_date` (data_merger.py:2131 → max source_date of the vendor projections CSV). pool_scope, league roster/scoring config, sleeper_projections, weekly_projections, mode, user_selected_player_id are outside it. Compare `snapshot_input_key` (1961–2004), which fingerprints all fifteen build_snapshot inputs and whose docstring uses "turning season_projections on … the leader changes from Tyler Warren to Bijan Robinson" as its example — the stamp cannot detect that change.

**Measured (probe4):** three snapshots at the same 96-pick state — pool_scope "all", "veterans_only", and vendor-only (no season_projections) — have leaders Tony Pollard 14.16 / Tony Pollard 21.56 / Jadarian Price 17.29, different candidate sets, different `snapshot_identity`, and **identical stamps** `(96, '2026-08-25')`; `stamp_is_current` returns `(True, None)` for all.

**Failure scenario in app.py:** the Draft Room debate result is gated only by `pick_label` (5619) and `pick_debate.staleness_note` (5625). Changing `draft_room_pool_scope` (5340–5345) does not reset `draft_room_debate_result` (the resets at 4895/4993/5049/5257 are Mock Draft only), nor does a "Refresh This League" that brings new season projections. The panel then shows the earlier debate with no staleness warning over a board with a different leader. staleness_note's docstring (pick_debate.py:686–730) says the reader "cannot afford … not KNOWING" — this is the case where they are not told.

---

### 6. MEDIUM-LOW — `diff_snapshots` silently drops measured↔unmeasured transitions

**Where:** pick_synthesis.py:2118–2119 `if prev_val is None or curr_val is None: continue`; a candidate with no numeric deltas and unchanged rank is omitted entirely (2124). Docstring (2099–2108): "exactly which underlying terms moved and by how much".

**Failure scenario:** between two debates a candidate's `denial_value` goes 4.04 → None (basis measured → no_rival_priced), or `universal_value` goes 41.5 → None (replacement level declined), or `positional_forfeit` appears from None. No delta is emitted; if rank is unchanged, the candidate does not appear in WHAT CHANGED at all, and format_snapshot_for_llm reports nothing. The absence transition is itself the most important "why did he move" fact and is the one the diff cannot express.

---

### 7. MEDIUM-LOW — The persisted draft_history record carries numbers without the companions the snapshot says they need

**Where:** draft_history.py:57–68 `_CANDIDATE_EVIDENCE_FIELDS`. Probe1 record (upside mode) shows exactly what is stored: `need_bonus: 0.0` (fabricated, see #2); `survival_probability: 0.827` (withheld — the module docstring calls this "a record of what the Draft Room actually showed", and the Draft Room did not show it); `waiting_cost: 237.89` with no `horizon_basis`/`horizon_sensitivity` (CandidateSnapshot docstring 1558–1566: "Consumers must not state a waiting cost more confidently than this allows"); `rival_premium: 0.0` with no `rival_premium_basis`; `denial_team: '2'` with no `denial_value`/`denial_basis`; `universal_value`/`team_acquisition_value` with no `absence_kind`, `replacement_basis`, `depth_exposure`, `displacement_adj` — so the stored TAV−UV residual is unexplained. test_snapshot_identity_boundary pins field names exist and a floor, not companion coverage. Currently write-only (only app.py:5607 writes; no production reader), so impact is latent until the Prytaneum reads it as the module intends.

---

### 8. LOW — Board payload ships the number without two of its companions

draft_board_ui.serialize_candidate (219–307): `uv: null` crosses with no `absence_kind` (the kind reaches only pick_debate), and `cannot_be_fielded` is not shipped at all although CandidateSnapshot's own comment (1594–1597) says "the card must be able to say so" and `_board_order` orders on it; `fillsRequiredSlot` is shipped. The board can show an unpriced or demoted row but not why.

---

### 9. LOW — Prose asserting properties the code does not have (checked against the code beneath)

- draft_room.py:35 module identity `team_acquisition_value = universal_value + need_bonus + eligibility_bonus + depth_exposure + displacement_adj`; draft_room.py:3636 "need_bonus, eligibility_bonus, depth_exposure and displacement_adj (the four team-specific terms…)". Code: TEAM_SPECIFIC_TERMS (516) has three names; score_row (4218–4219) sums `universal_value + need_bonus + depth_exposure_value + displacement_adj`. `lineup_optimizer.eligibility_bonus` has no production caller (grep). Same stale term in draft_room.py:2349, 3065; pick_synthesis.py:85, 142, 149, 740 ("Each entry … needs … eligibility_bonus"); README.md:82–93 ("Three bounded nudges — need_bonus, eligibility_bonus and …").
- pick_synthesis.py:1657–1661 build_snapshot docstring: "upside-mode scoring drops universal_value/need_bonus/eligibility_bonus entirely … this snapshot's whole shape depends on those fields existing." False on both counts: the upside board emits universal_value (draft_room.py:3895) and build_snapshot runs in upside mode by defaulting need_bonus (#2). draft_simulation calls it with mode="auto"/"upside" routinely.
- draft_room.py:3744 and 3753 (inside compute_draft_board): "scaled LINEARLY … against the largest VOR gap actually present" / "folded into the SAME shared linear scale". `_scale_vor_to_bpa` is the identity (2508–2542) and the module docstring at lines 38–43 already retracts this; the inline comment still asserts it.
- pick_synthesis.py:1885 `_canonical`: "measured, all 37 fields are builtins today" — CandidateSnapshot has 52 fields (probe1).
- draft_simulation.py:87–100 / 216–218: `upside_from_round` and `picks_by_mode` are computed from UPSIDE_MODE_DEFAULT_ROUND regardless of `upside_rule`; under UPSIDE_RULE_CROSSING the flip is data-driven, so the trajectory config would record a split the trajectory did not produce — the exact defect the #52 phase-6 comment describes fixing. Latent: draft_battery forwards `entry.get("upside_rule")` (1068) but no matrix entry sets it today.

---

### 10. LOW, documented — deliberate collapses in the other direction

- draft_room.py:1466 `sleeper_points = scored if scored != 0 else None`: a measured league-scored season total of exactly 0 becomes absence, and `availability_basis` is then None for that row (1477). `_admits_to_pool` clause 1 (1163–1166) depends on this. Documented in place as a stat-gap guard; it is still the contract's one sanctioned zero→None collapse, and a K/DEF whose stat line legitimately scores 0 under a league's rulebook falls to the vendor or to NO_INPUT rather than to a measured zero.
- draft_battery.roster_strength `values.get(str(pid), 0.0)` (line ~660) enters unpriced players at 0.0 into total/bench/lineup solves; the docstring records it as open #168. Not new.

---

### Null results (examined carefully, nothing serious found)

- `_records_with_normalized_nan` (2589–2621): on a 970-row real board in both modes, zero NaN, zero numpy scalars, zero pd.NA in any column (probe1 leak census `{}`). The `hasattr(value, "shape")` short-circuit would skip an np.float64 NaN inside an object column, but no column produced one.
- absence_kind is present iff bpa is None (489/489 no_input on 8T_standard); confidence is None exactly for NO_PRICEABLE_INPUT; replacement_basis is None on every unpriced row; horizon_basis is conditioned on a floor existing (970/970 measured-with-floor).
- `_board_order`, `near_tie_flags`, `decision_regime`, `compute_pick_necessity`, `detect_positional_cliff`, `_best_alternative`, `expected_value_of_waiting`, `acting_now_value`, `_opportunity_cost`, draft_strategy `_is_absent`/opponent-board unpriced handling, `health_penalty`, `_confidence` — all propagate None without substituting a number, consistent with their docstrings and test_absence_survives_consumers.
- `snapshot_input_key` genuinely derives from build_snapshot's signature and refuses uncanonicalizable inputs; the Draft Room cache key is sound (the gap is the *stamp*, #5, not the cache).
- app.py `_figure`/design_system.figure: None→dash, measured 0.0→"0", NaN refused — as claimed.
