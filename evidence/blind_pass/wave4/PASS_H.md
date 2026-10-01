# Wave 4, pass H — preserved verbatim

> **The pass's own words, unedited.** Verdicts and novelty live in `LEDGER.md`.
>
> Conditions: Fable, worktree isolation, `/tmp/audit_tree` with the six forbidden paths excluded,
> the Wave 4 mandate identical to pass G's. **This is its third launch** — the first went out
> carrying the Wave 1 mandate with no SETUP block and audited a 508-commit-divergent tree before
> being killed; the second died on an account rate limit mid-run. Nothing from either enters the
> ledger. See `MANDATE.md` §4.
>
> **Self-reported contamination: none.** Verified the exclusions before reading; did not open the
> two `.claude/` paths. Read `.claude/skills/engine-measurement/SKILL.md`, which is not on the
> list. Every number re-measured on the capture's own `league_shape`.

## Report

**Contamination statement:** none. The tree was extracted with the three freeze documents and
three evidence directories excluded; I verified they were absent (`ls` failed / dirs empty) before
reading anything. I did not open `.claude/skills/close-register-item/` or
`.claude/blind-pass.settings.json`. I read `.claude/skills/engine-measurement/SKILL.md`, which is
not on the forbidden list. No repository file was modified; all probes live in the session
scratchpad. Every number below was re-measured in this session on
`data/fixtures/sleeper_capture.json` and its own `league_shape` (12 teams: QB, 2RB, 2WR, TE, FLEX,
SUPER_FLEX, K, 2×IDP_FLEX, 14 BN; full PPR, no `bonus_rec_te`; 25 draftable rounds), with
`merger.set_league_format(league_format_hint(league))` applied and `sleeper_projections` +
`SLEEPER_BASIS_SEASON_SUM` passed.

Findings are ranked by severity. Each has a concrete failure scenario; the few that are code-style
opinions are labelled.

---

### 1. The withheld survival estimate reaches the person and the chairs through three unguarded paths

`pick_synthesis.SURVIVAL_IS_CALIBRATED = False` (pick_synthesis.py:527) withholds
`survival_probability`, `opportunity_cost` and `expected_value_of_waiting` from `_format_candidate`
and from the board's SURV chip. The withholding is incomplete in three places, and the test suite
pins one of the leaks.

**(a) `pick_necessity` is a function of survival and is not in `SURVIVAL_DERIVED_FIELDS`.**
pick_synthesis.py:620: `survival_component = (1 - survival) * NECESSITY_SURVIVAL_WEIGHT` (weight
20.0, line 289) is summed into the 0–100 score behind the necessity pill on every board row and the
`Pick necessity: N/100 -- LABEL` line every chair reads first. `SURVIVAL_DERIVED_FIELDS` (line 536)
claims to name "every quantity that is a function of survival_probability" and omits it. Measured
at pick 1.01, seat 1, 84 candidates: removing the survival term changes the rendered label on 12 of
84 candidates — every quarterback. Josh Allen 77.9 PREFERRED → 57.9 CLOSE CALL; Joe Burrow the
same; Lamar Jackson 89.9 STRONG ACTION → 69.9 PREFERRED; Mahomes STRONG ACTION → PREFERRED;
Purdy/Hurts/Prescott/Daniels/Maye/Goff/Dart all PREFERRED → CLOSE CALL. These labels rest on
survival estimates of 0.000–0.26 for the QBs, and the module's own calibration note
(pick_synthesis.py:500-503) says the 0.0–0.1 bucket was observed at 0.500 on real picks. By the
module's own criterion at line 535 ("showing them while hiding survival would be suppression in
name only") the pill is suppression in name only.

**(b) `diff_snapshots` still diffs the survival family and both consumers print it.** `_DIFF_FIELDS`
(pick_synthesis.py:1674-1679) includes all three withheld fields. `pick_debate.format_snapshot_for_llm`
(pick_debate.py:514-523) prints every delta into the "WHAT CHANGED SINCE THE LAST SNAPSHOT" block,
and `app.py` passes `previous_snapshot` in both the Draft Room (app.py:5507) and the Mock Draft
(app.py:5129). Measured with two consecutive real boards (1.01 → 1.02): the chairs receive
`Christian McCaffrey: rank moved by -1 (... survival_probability: -0.08, opportunity_cost: +17.22,
expected_value_of_waiting: -16.52 ...)` and `Bijan Robinson: (survival_probability: -0.05,
opportunity_cost: +11.49, ...)` directly beneath candidate blocks that say the estimate is WITHHELD
and instruct the model not to reconstruct it. The Draft Room's own diff drawer (app.py:5587-5596)
prints the same deltas to the person, labelled "Survival probability" / "Opportunity cost" /
"Value of waiting" via `_DRAFT_ROOM_DIFF_LABELS` (app.py:77-78).

**(c) The suite pins the leak.** `test_pick_debate.py:57-62` asserts "Survival probability" is
absent from the candidate block; the same file at :88-90 feeds `deltas: {"survival_probability":
-0.2}` into the diff block and asserts "WHAT CHANGED" renders, and at :234-239 builds two snapshots
differing *only* in survival and asserts a non-empty diff reaches the chair prompt. Two
contradictory contracts in one file; the second one is what production does.

**(d) Prompt boundary primes the withheld number.** `STRATEGIST_SYSTEM_PROMPT`,
`SKEPTIC_SYSTEM_PROMPT` and `CALLER_SYSTEM_PROMPT` (pick_debate.py:173-265) all describe
`survival_probability`, `opportunity_cost` and `expected_value_of_waiting` as given inputs, tell the
Strategist to argue from "a low survival probability", and give `"19% survival with a QB run
detected and a HIGH positional cliff"` as the model KEY FACTOR. The evidence block then contains
none of those numbers. A chair told the numbers exist, told to use them, and handed only an
intervening-pick count is being invited to produce exactly the estimate #206 withheld.

### 2. The battery matrix does not contain the league the system is used on, and a full draft on it stacks kickers with zero structural findings

`draft_room.build_mock_league` (draft_room.py:3583-3620) emits no `K`, `DEF` or IDP slot, so the 30
base arms and the three TE-premium/redraft arms have no kicker anywhere. The three custom arms
(draft_battery.py:126-155) have no K either; HEAVY_IDP/LIGHT_IDP are 1QB. The three captured
leagues in `data/league_captures/` carry K=0 and IDP=0. So **no arm in the matrix drafts a kicker**,
and no arm carries the capture's own shape (superflex + K + 2×IDP_FLEX + 14 BN).
`format_axes_exercised` (draft_battery.py:637-687) derives its axes from `league_format_hint`'s keys
— `scoring`, `superflex`, `te_premium` only — so roster-slot composition is not an axis and the
instrument reports "no constant axis" over a kicker-free matrix.

Full 300-pick draft on the capture's shape, every seat the production engine, `mode="auto"`,
`audit_trajectory` with `audit_roster_fill=True`: **`findings: []`**, every roster fills its 11
starting slots — and:

- **31 kickers drafted for 12 K slots.** First kicker at pick 88 (round 8); six kickers in round 8,
  six in round 9, then 16 more across rounds 11–14. Rosters 7, 11 and 12 hold **five kickers each**;
  rosters 6 and 10 hold four. There is no K-eligible flex.
- 51 LB, 51 DB, 16 DL for 24 IDP_FLEX slots; **round 21 was twelve consecutive DBs**.
- Roster 7 spent 15 of 25 picks on K/IDP (WR 3, TE 1); roster 11 has RB 2, WR 3, K 5, LB 6.

Mechanism, measured at round 11 (seat 1, 12 K already gone): the 13th kicker (Butker) is priced
`uv -0.09, tav -6.32, replacement_basis=predraft_anchor` against a best-available RB at `tav -1.41`
and WRs at `-2.8`. Once live K demand is exhausted, kickers fall to the pre-draft anchor and keep a
near-zero-to-positive price relative to the pre-draft K12, while the league's K scoring (3–5 pts per
FG; K projections ~100–134 season points) puts them within a few points of the bench offence. A
kicker nobody in the league can ever start has zero marginal value; the anchor prices him as "points
above pre-draft K12". At 1.01 the top kicker already carries `bpa 12.57` and `need_bonus +4.0` (a
full dedicated-slot bonus) against `+0.67` for an LB competing for two IDP_FLEX slots.

None of the battery's audits can see this: the findings are legality checks, and `roster_shape` is a
distribution nobody thresholds. The report a reader receives says "0 structural findings".

### 3. Upside mode is roster-blind for 44% of the owner's draft and its growth term is inert there; the mode switch is off by one pick

- `draft_room.py:3003`: `current_round = max(p["round"] for p in demand_source)` — the round of the
  last pick **made**, not the pick being made. At the first pick of round 15 (`picks[:168]` has max
  round 14) balanced mode still applies; upside starts at 15.02. `draft_simulation._picks_by_mode`
  (draft_simulation.py:99) records `balanced = 14*12 = 168, upside = 132`; the e2e trajectory
  actually produced **131** upside picks (`picks_with_growth_measured: 131`). The recorded split is
  wrong by one pick per draft, and the first pick of every round after the switch is valued under
  the other regime.
- On the owner's league `growth_signal > 0` on **0 of 131** upside picks. Board-level: 32 of 2,028
  rows pre-draft and 33 of 1,828 rows at pick 200 carry any growth; all K/IDP/most offence rows
  carry none. So for rounds 15–25 (132 of 300 picks) the valuation is `bpa` alone with every team
  term zeroed and essentially no growth term — the two rounds after the switch drafted 6 QBs
  (round 15, into rosters already holding 2–4) and 6 TEs (round 17).
- **Absence collapse in the engine's own output:** `upside_score` (draft_room.py:2133-2160)
  initialises `growth = 0.0` and only overwrites it when `_has_3yr`; rows with no 3-year source at
  all (every K, DL, LB, DB, and 1,996 of 2,028 rows here) return `growth_signal: 0.0`,
  indistinguishable from a measured flat trajectory. `draft_board_ui` renders it as `GROWTH 0.0`
  (`num(c.growthSignal)` is true for 0.0). At pick 200 the top five rows are DL/TE/DB showing a
  measured-looking 0.0. `bpa = row.get("bpa") or 0.0` on the same line is a latent None→0.0 collapse
  (inert today only because pandas NaN is truthy).

### 4. The necessity label vocabulary is round-determined, not pick-determined

Every component of `compute_pick_necessity` is non-negative (standout floored at 0 at
pick_synthesis.py:~612, forfeit `max(forfeit, 0.0)`, survival `(1-s)≥0`, cliff/run/denial ≥0, roster
fit = need+eligibility ≥0) on top of `NECESSITY_BASELINE = 50.0` (line 278). Thresholds (lines
563-570): ≥50 CLOSE CALL, ≥30 LOW URGENCY, else DOESN'T MATTER MUCH. Therefore before
`LATE_ROUND_THRESHOLD` (=15, line 412) no candidate can read below CLOSE CALL, and from round 15 the
×0.3 cap (line 413) makes anything above LOW URGENCY unreachable (score 30.0 needs raw exactly 100).
Measured: round 1.01 → {STRONG ACTION 9, PREFERRED 36, CLOSE CALL 39} across 84 candidates including
all 12 kickers; round 11 → 29/32 CLOSE CALL; round 15 → 27/28 CLOSE CALL; round 17 → **17/17
"DOESN'T MATTER MUCH"**. Two of six labels are unreachable early, four are unreachable late; the
pill mostly tells the reader what round it is.

### 5. `league_config`'s blocking state is dead code, and would refuse the owner's own league if wired

`admits_decision`, `decision_config` and `confirmation_state` (league_config.py:221-260) have no
caller outside tests; `app.py` imports the module only for `describe_config_age` (app.py:1682). The
docstring's "AMBIGUOUS -- The only blocking state" and `decision_config`'s "Raises rather than
returning something usable-looking" describe a gate nothing passes through. Measured on the
capture's `league_shape`: `ambiguities()` returns `missing_format_keys: ['bonus_rec_te', 'type',
'num_teams']`, and still `['bonus_rec_te']` after a `settings` block is added — because
`FORMAT_DECIDING_KEYS` (line 113) requires `bonus_rec_te` to be *present*, and a non-TE-premium
Sleeper league simply omits it. So the owner's real league is AMBIGUOUS by this rule. The fixture in
`test_league_config.py:30` carries `"bonus_rec_te": 0.5`, i.e. the one shape on which the check
cannot fire spuriously. A claim (blocking) the code does not support, and a rule whose first real
input it would block.

### 6. Resume joins arms from different captures under one `universe` block

`resume_join.carry_forward` (resume_join.py:57-92) admits a prior arm on `label` match alone and
stamps only `produced_at` (a commit). `run_draft_battery._battery_report`
(run_draft_battery.py:139-172) places capture provenance (`captured_at`, pool sizes,
`pricing_census`) at report level only, computed from the capture on disk *now*. Scenario: run six
arms, re-capture Sleeper (new `captured_at`, different injury statuses, different projections),
`--resume`. The report says one `captured_at` and one census while six arms were drafted from
another universe; `commits_present` can be a single commit throughout, so the reader's only cue
("more than one commit → check") never fires. `test_battery_universe_boundary.py:154` pins the
report-level fields only.

### 7. `store_io` silently discards writes after any `OSError` on read

`_parse` (store_io.py:167-188) returns `readable=False` on **any** `OSError`, not only on a
non-empty unparseable file as its docstring states. `read()` then marks the path in `_unreadable`,
and `write()` (lines 208-222) returns silently for a marked path until a later `read()` succeeds.
Scenario: one transient `EACCES`/`EIO`/network-FS hiccup on a `read()` of a per-league store → every
subsequent `write()` to it in that process is dropped with no exception; the only signal is
`warn_about_unreadable_stores()`, which app.py calls at one site (app.py:6576, inside the Prytaneum
path), so a Draft Room session can lose every write for the rest of the process without being told.
The battery's `store_io.write(args.out, ...)` has no `read()` on that path, so it is not exposed —
but `draft_history._atomic_write` (draft_history.py:98) is a second, lock-free write implementation
beside store_io (style: two homes for one discipline).

### 8. The LLM boundary in `pick_debate` has no fence and no contract

`untrusted.CONTRACT` is appended to every Prytaneum system prompt
(llm_engine.py:102,122,141,265,281,832,884) and prior conversation is fenced (llm_engine.py:955-959).
`pick_debate` uses none of it: the three system prompts carry no contract, and `debate_pick`
(pick_debate.py:729-734) concatenates the Strategist's and Skeptic's raw prose into the next chair's
user prompt via `_report_for_handoff` (llm_engine.py:707-710), which only substitutes a placeholder
for a failed call. The app's own contract text says model-written prior verdicts are exactly what
must be fenced. `test_untrusted_fence.py` exercises the primitives only; no test names a
`pick_debate` call site.

### 9. The evidence block is ~90 KB per chair on the owner's league; the budget test measures a constant the live path does not use

`build_snapshot` narrows to `top_n=5` **plus** `position_view_depth = min(replacement_rank,
POSITION_VIEW_DEPTH_CAP=12)` per position (pick_synthesis.py:212,1433-1445). On the capture league
that is **84 candidates at 1.01** (12 each of RB/WR/QB/TE/K, 8 each of LB/DB/DL), a 90,514-character,
807-line block (~22.6k tokens) sent three times per debate — with twelve kicker blocks in it.
`test_context_budget_boundary.py:85-99` ("stays small enough to never be the problem") checks
`DEFAULT_NARROW_COUNT = 5 ≤ 30`; the operative count is 84. The guarantee is asserted on a number the
path does not bound on.

Related, same block: the universal-value decomposition prints an unrounded addend against a rounded
sum — `Universal value: 12.57 = bpa 12.569999999999993 + horizon +0.0 + risk +0.0`
(pick_debate.py:349-358) — an arithmetic sentence handed to a model told never to recompute, in
which the two sides visibly differ.

### 10. `parse_caller_verdict` / `_match_candidate` (LLM output boundary)

- `parse_caller_verdict` (pick_debate.py:530-552) strips leading `-*# ` but not the bold closer, so
  `**RECOMMENDATION:** Josh Allen` / `**CONFIDENCE:** Lean` parse to `'** Josh Allen'` and
  `'** Lean'` (measured). `app.py:5164,5532` render `f"Confidence: {debate_result.confidence}"`
  verbatim, so the caption reads "Confidence: ** Lean". The recommendation still resolves only
  because of the substring fallback.
- `_match_candidate`'s fallback (pick_debate.py:567-570) is bidirectional containment in candidate
  order. The capture has 23 substring name pairs and 78 exact duplicate names; e.g. "Ian Thomas"
  (TE, LV) ⊂ "Brian Thomas" (WR, JAX). If both are candidates and the Caller writes
  `RECOMMENDATION: Brian Thomas Jr.` (exact match fails on the suffix), the first candidate in board
  order whose name is contained in the text wins — Ian Thomas if he sorts earlier — and the
  displayed decomposition is the wrong player's. Low likelihood, but the function's docstring says it
  returns "None (never a guess)".

### 11. Two scoring-label models, and `rec` values outside {0, 0.5, 1}

`draft_battery.league_format_hint` (draft_battery.py:204-218) and
`sleeper_client.league_format_summary` (sleeper_client.py:775-777) both map `rec >= 1 → ppr`,
`rec == 0.5 → half_ppr`, else `standard`. A league at `rec = 0.75` or `0.25` (both real Sleeper
settings) is labelled "Standard" in the header and selects the **standard** rankings export.
`app.py:3523` translates the summary's label back with a `.get(..., "ppr")` default, so the two
models agree today; the agreement is by translation table, not by one definition. Label as moderate:
no capture in the repo uses such a value, so this is unmeasured on real data.

### 12. Minor / code-style

- `sleeper_client.league_format_summary` line 789: `settings.get("num_teams",
  len(league.get("roster_positions", []) and []))` — the default expression is always `len([])` = 0.
  Harmless (falls through to `total_rosters`), but it is a computed default that cannot mean what it
  looks like.
- `unfilled_starting_slots`/`roster_strength` (draft_battery.py:246-249, 528-533) build eligibility
  from raw `fantasy_positions` rather than `player_eligible_positions` (which filters to
  `FANTASY_POSITIONS`); no observed consequence.
- `draft_history._atomic_write` duplicates `store_io._write_unlocked` without the lock (see 7).

### Null results (examined carefully, nothing serious found)

- **Identity resolution across position namespaces** (`data_merger._resolve`, 2079-2234): the
  exact-name path skips the namespace/offence rejections the key path applies, but measured over all
  6,595 capture players with the SF/PPR format applied: 755 key matches, 22 fuzzy, **0 cross-group
  resolutions, 0 exact-path offence-position disagreements** — the vendor table is
  first-initial-only, so the exact path never fires against it.
- **Cross-format field mixing in `_reconcile_rows`** (data_merger.py:1398-1494): first-non-null-per-field
  could splice `proj_3yr` from a TE-premium file onto a PPR-superflex row, but measured: **0 rows**
  with `projection_source ≠ proj_3yr_source`. The 34 offence rows sourced from non-matching exports
  are tail players (A. Richardson tv 1.0, deep RBs/TEs), not a valuation hazard. `trade_value`'s
  source is not recorded on the row, so this could only be confirmed by the conflicts list (1,042
  `trade_value` format_match conflicts recorded there).
- **Injury double-count** between Sleeper's weekly zeroing and `availability_factor`
  (player_universe.py:119-160): the factor is anchored to `SEASON_GAMES - missed` over Sleeper's own
  `gp` and is self-limiting; the capture's coverage record shows all 18 weeks answered. No defect.
- **`_merge_memo` across format switches**: `_load` (data_merger.py:1791) resets the memo, so
  `set_league_format` cannot serve stale resolutions.
- **JS `decisive` branch prints survival without the `survivalWithheld` guard**
  (draft_board_ui.py:757): latent only — `decision_regime` cannot return "decisive" while the same
  flag is False (pick_synthesis.py:996-1007), and if the flag flips the number is presentable anyway.
- **Slot-vocabulary claims** in league_config.py:73-80 (F&F 29−3 IR = 26; GSOP 33−4 IR = 29)
  re-derived from the captures: correct.
- `assertion_floors.py` and `quantity_readers.py` are AST-based; no text-scan-where-AST-exists found
  in the instruments I read.
