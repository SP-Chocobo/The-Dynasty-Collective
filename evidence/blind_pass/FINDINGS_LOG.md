# `#52` findings log — append-only, in arrival order

> **THIS FILE DOES NOT TRIAGE.** No verdicts, no novelty calls, no clustering, no merging of two
> passes' versions of one thing. Every pass's findings are logged as that pass stated them, in the
> order they arrived, and nothing already written here is edited when a later pass contradicts it.
> That is the point: the log is the record of *what was claimed when*, so the triage in
> `LEDGER.md` can always be checked against what it was built from.
>
> - **Raw text of each pass:** `wave<N>/PASS_*.md` — verbatim, the source of truth.
> - **Verdicts, novelty, clusters, disputes:** `LEDGER.md`.
> - **This file:** the running list, append-only.
>
> Waves 1–4 below are backfilled from the ledger's own enumeration and are marked as such; from
> Wave 5 on, entries are logged from each pass's report as it lands, before any triage.

---

## Wave 1 — passes A and B *(backfilled)*

20 findings logged, W1-01 … W1-20. Not restated here: the ledger's Wave 1 table is itself the
per-finding list as reported, and the verbatim text is in `wave1/PASS_A.md` and `wave1/PASS_B.md`.

Headline claims: `displacement_adj` positive against a non-positive contract; `time_horizon_adj`
percentiles over two populations; anchor cache fingerprint incomplete; the `need_bonus` invariant
test a tautology; the `prose_names` history shield exempting ~40% of prose; a comment citing a test
that does not exist; survival reaching a displayed score through `pick_necessity`; `league_config`'s
blocking gate uncalled.

## Wave 2 — passes C and D *(backfilled)*

10 findings logged, W2-01 … W2-10. Verbatim: `wave2/PASSES_C_AND_D.md`.

Headline claims: contested-identity guard a function of the remaining pool only; `qb_startable_floor`
in vendor units; superflex QBs unpriced with `absence_kind=None`; `block_opportunity` unreachable in
production; the `trade_value` branch clamping to a 2-row list on the owner's own league; TAV below UV
on 246 of 796 priced rows; thirteen test modules on the fixture the repo declares non-production;
`CDME_CONTRACTS.md` false in four places; the `round` off-by-one; `roster_id=None` as a phantom team.

## Wave 3 — passes E and F *(backfilled)*

8 findings logged, W3-01 … W3-08. Verbatim: `wave3/PASSES_E_AND_F.md`.

Headline claims: the engine drafts 4–5 kickers per roster on the owner's league with zero structural
findings; the live-level → pre-draft-anchor discontinuity; `remaining_starter_demand` not reaching
zero; `waiting_cost` None for all 148 superflex QB rows and swinging 7.27 → 116.75 for K; vendor 0.0
admitted while Sleeper 0 becomes None; 216 priced rows violating a "structurally impossible" test.

## Wave 4 — passes G and H *(backfilled; the wave is logged in full in the ledger)*

29 findings logged, W4-01 … W4-30 (W4-05 struck on checking as already-registered `#184`). Verbatim:
`wave4/PASS_G.md`, `wave4/PASS_H.md`. My own re-measurement: `wave4/MY_VERIFICATION.md`.

Headline claims: the flat per-dedicated-slot `need_bonus` worth 32% of a kicker's whole
above-replacement spread; two shipped constants derived from a bound the engine violates by 2.4×;
`_picks_by_mode` asserting what its docstring says it reports; the LLM prompt boundary offering
chairs a withheld number with a worked example; the snapshot diff printing the withheld survival
family in full to chairs and to the person, with the suite pinning that leak; `format_axes_exercised`
unable to see roster-slot composition at all; 51 LB / 51 DB / 16 DL into 24 IDP_FLEX slots;
`growth_signal > 0` on 0 of 131 upside picks; the necessity pill unable to read below CLOSE CALL
before round 15 and above LOW URGENCY after; `store_io` dropping writes after any `OSError`;
`pick_debate` carrying no untrusted fence; the evidence block at 84 candidates against a budget test
asserting on 5.

**Logged separately because it is about the audit, not the engine:** two of pass G's five null
results were wrong, and pass H found real defects in both areas. From Wave 5 the mandate requires a
null to state how it was established.

---

# Wave 5 onward — logged live, before triage

## Wave 5 — passes I and J

*Mandate adds a null-result evidentiary standard, a state/persistence/process-boundary category,
and steers toward the self-integrity instruments. Both passes have reported.*

### Pass I — reported 2026-09-18. Verbatim: `wave5/PASS_I.md`

*Logged as stated by the pass. No verdicts, no novelty calls, no merging with any other pass.*

**I-01.** Two take models answer "will he survive to my next pick" two orders of magnitude apart.
`_take_probability` normalises the rank table over the whole board's mass; `_pace_based_take_probability`
is unnormalised and wins whenever it exceeds the rank estimate. Measured at 1.01 on the real capture:
`board_take_mass` 41.67, of which 24.16 (58%) is the 0.02 floor on unpriced rows. McCaffrey rank 1 on
every rival board → per-rival take 0.013, survival across 22 picks **0.747**; a rival's take
probabilities over their own top 12 sum to **0.032**. Josh Allen rank 7 → rank model survival 0.989;
with the pace prior, per-pick p_take reaches **1.0 at the 13th intervening pick** and survival is
**0.0 exactly**. Same snapshot: RB1 75% safe, QB1 0% safe.

**I-02.** The pace prior is internally inconsistent: `actual_now` counts QBs only in the real `picks`
list, so the deficit grows with `picks_made_now` while zero QBs are assumed taken — it asserts pick
#13 takes him with certainty on the premise that picks #2–#12, each just assigned 0.08–0.92, took
none. Reintroduces the exact 0.0 that `#206`'s repair exists to remove, under
`survival_basis == "measured"`.

**I-03.** The normalised model's magnitude is a fixture artefact. `test_take_model_coherence._boards`
uses ~505 floor rows → rank-1 p = 0.064, and the test asserts this is "within a few points of the
measured 3.0%". On the real universe the mass is 41.67 → 1.3%, and the pinned turn survival of 0.232
becomes 0.747. Pinned on a board a quarter the size of the owner's.

**I-04.** `board_contention_scale` and `_value_take_weight` have **no callers anywhere**, beneath a
12-line comment stating the take model "is a VALUE SHARE over the opponent's own board, not a lookup
on the candidate's ordinal". Production is the rank table. The docstring describes a model that never
runs.

**I-05.** `screen_context.build_draft_room_context` (~118) prints "survival NN%" into the Prytaneum
seed — the same number `pick_debate` refuses to show the chairs.

**I-06.** `depth_exposure` is stamped `measured` from roster-wide surplus, not reachable surplus.
`has_surplus = len(roster_players) > len(starting_ids)` is one boolean for the whole roster, and
`draft_room.py:3457` prices `worst_loss` **only** under that basis. Probe: 8 starters no bench → all
`no_surplus`; add **one bench kicker** → QB/TE/RB/WR flip to `measured` with identical numbers. Real
draft pick 141: `K ('measured', 14.0)`, `TE ('measured', 8.0)`, `QB ('measured', 82.0)` — the K/TE
numbers are the lone starter's own trade_value — and the chosen candidate (a kicker) carries
`depth_exposure = 1.68` as a priced term. The only test pinning `EXPOSURE_NO_SURPLUS` uses the
no-bench roster, the one shape where it cannot fail.

**I-07.** `corpus_state` reports "no local data in the mix" while a league-scoped upload moves every
price. Probe: planted one rankings CSV (projection 9999) in a temp league dir — top RB projection went
359 → 9999, `corpus_state.assess()` returned `doctrine_only` with the green sentence, and
`baseline_manifest.diff()` was clean. The module docstring's own argument about uploads moving
replacement levels is exactly the case it cannot see.

**I-08.** `quantity_readers._reads_in` counts **any** `ast.Attribute` load with a matching `.attr` as
a read. The DECISION verdict for `depth_exposure` rests solely on `draft_room.py` containing the
function call `lo.depth_exposure(`; no scoring module subscripts the board column. Same mechanism
gives DECISION for `name`, `position`, `team`, `value`, `round`, `basis`, `mode`, `starters`,
`player_id` off unrelated objects (`.name` on a Path, `.round(` on a Series). Every `KNOWN` entry is
distinctively named, so the collision is never exercised.

**I-09.** `quantity_readers._relayed_in` double-counts reads inside nested dict values:
`{'a': row['x']}` → relayed `{'x'}`; `{'a': {'b': row['x']}}` → relayed `set()`.

**I-10.** `assertion_floors` claims "a weakening cannot pass unseen"; four ways it does, each probed
with the module's own API: (a) weaken one assertion and add another of the same name in one edit →
`drops() == []`; (b) `@unittest.skip` → `[]`; (c) assertion under `if False:` → `[]`; (d) floors file
`{}` plus an empty test module → `[]`, and `--check` prints "no guarantee has shrunk (0 modules held
to a floor)" and **exits 0**, because `load()` returns `{}` for a missing or damaged file. Also: two
test modules use bare `assert`, which the instrument does not count.

**I-11.** `suite_taxonomy.tier_of` is the substring `"DataMerger()" in source`. Three modules that
load the 6,595-player capture are classed fast. Measured fast tier = **123 modules, 201.5 s**; the
docstring says "53 fast modules, 845 tests, 1.5 seconds". A module mentioning `DataMerger()` in a
docstring is "full"; one constructing `DataMerger(league_dir=…)` is "fast".

**I-12.** `#102`'s store-discipline exemption has a false reason. `bot_benchmark` is exempted as
"developer-run measurement output, never touched by the app"; `app.py:2689–2695` runs
`run_benchmark` and `save_report` from the Configure Bots UI. `_load_all` swallows `JSONDecodeError
→ {}` and `save_report` writes back with `write_text` — one torn read wipes every role's 20-run
history.

**I-13.** `sleeper_client.get_players` writes the ~10 MB players cache with `write_text`
(truncate-then-write); `_write_snapshot` likewise. A second tab reading mid-write gets `None` →
re-fetch of `/players/nfl` plus a second full `sync_league`. Exempted on the cost of a lost write;
the torn *read* is the cost.

**I-14.** Draft Room snapshot cache and `stamp_is_current` both key on
`(len(picks), merger.freshest_date)`, so a same-date re-upload, an alias override, or a pick
correction that leaves the count unchanged serves a stale `PickSnapshot` while
`snapshot_is_current` returns `True`.

**I-15.** Five claims the code no longer supports: `term_lifetimes.py:58` says `bpa` is "scaled
linearly against the pool's largest VOR gap" (`_scale_vor_to_bpa` is the identity);
`prediction_record.main()` commits a forward record for a shape the owner does not play, with no
`set_league_format` call; `roster_diagnostics` solves lineups with primary-position eligibility only
while `eligibility_bonus` assumes full eligibility; `draft_history.record_snapshot`'s "same bytes"
claim fails under a race because the payload carries `ts`/`date`; `positional_forfeits` still says
"same principle as estimate_survival" after `#206` made the two disagree.

**I-16 (low).** `attachments.save_attachment` joins a client-supplied filename onto `ATTACHMENTS_DIR`
with no `Path(...).name`. `app.py`'s `.env` rewrite is non-atomic. `len(x and [])` is always 0.

**Nulls filed by pass I, with method (logged as filed, not adjudicated):** `store_io`,
`content_hash`, `resume_join`, `untrusted`, `panel_independence`, `providers`, `bot_config`,
`bot_research` gating, `llm_engine` handoff, `ui_source`, `render_trace`, `baseline_manifest --check`,
`draft_history._scope_dir`.

**Declared not confident / not examined:** `data_merger` reconciliation and identity internals,
`league_config`, `pick_synthesis` necessity arithmetic, `app.py` beyond cited sites, `depth_ratings`,
`rookie_draft`, `draft_counterfactual`, `doc_index`, `basis_semantics`, `ordinals`. Ran 12 rounds,
not a full 25.

### Pass J — reported 2026-09-18. Verbatim: `wave5/PASS_J.md`

*Logged as stated by the pass. No verdicts, no novelty calls, no merging with pass I's overlapping
entries — where J and I report the same area, both are logged separately and on their own terms.*

**J-01.** The superflex QB pace prior produces **certainty**, which its own docstring says it never
does. `actual_now` counts only REAL picks while `expected_now` advances with each hypothetical
intervening pick, so at 0 real picks `expected_position_pace(QB, 12) = 6.0`, deficit 6.0, `6/6 = 1.0`
— from the 13th intervening pick on, the rank-1 remaining QB has p_take = 1.0, and `pace_driven`
always wins because the rank-based p is ~0.01. Measured at 1.01, 22 intervening picks: Josh Allen
`survival=0.0, opportunity_cost=169.92, denial_value=169.92`; Burrow `0.0`; Lamar `0.002`; Purdy
`0.013`. Docstring `:46-48`: "a confident-sounding single number would misrepresent as certainty".
`:89-90` claims it is "capped, never treated as certainty" and cites `_pace_deficit_boost`, **a
function that no longer exists**.

**J-02.** `denial_value = final_score × take_probability` is the withheld take probability in another
unit, and is rendered to the chairs **unconditionally** — `pick_debate.py:463`: "Denial value: 169.92
(would go to roster 2)".

**J-03.** Two take models, both feeding `pick_necessity`. `positional_forfeits` sums the **raw**
`RANK_TAKE_PROBABILITY` over each rival's top-5, capped 0.9 per position per pick;
`estimate_survival` uses the same table **normalised over the whole board**. `#206` was applied to
one consumer only. Measured: `expected_taken` RB 19.8, WR 3.52, QB 0.0, TE 0.0 over 22 picks — Σ =
**23.32 > 22**, arithmetically impossible. RB forfeit 180.71, **QB forfeit 0.0**.

**J-04.** The consequence of J-03 at the chair: `pick_debate.py:477-481` renders *"Cost of delaying
QB entirely: measured 0 -- the best remaining QB at your next pick is expected to be no worse than
now"* — while survival (which says the same QBs are gone with certainty) is withheld. The chair is
told waiting on QB is free, in a superflex league.

**J-05.** Upside mode is inert on the **production** pricing path. Measured on the full 300-pick
draft: `picks_with_growth_measured: 131, picks_with_growth_above_zero: 0, max_growth: 0.0`. At the
start of round 15, 38 of 1,860 rows have growth > 0 (12 vendor-priced, 637 Sleeper-priced, 1,208
`no_priceable_input`). Every seat-1 pick from R16 shows `need=0.0 disp=None depth=None tav==uv`.
Contradicts `CandidateSnapshot.growth_signal`'s comment ("43-52% of rows carry growth > 0 … by round
15 it changes which player is taken") — those numbers were measured on the vendor-only path;
production is vendor+sleeper.

**J-06.** `depth_exposure`'s `no_surplus` sentinel is roster-level. Measured: roster {QB 30, RB 25,
WR 28, TE 15} → RB `{worst_loss 25, no_surplus}`; add a **bench QB** → RB `{worst_loss 25,
**measured**}`, identical arithmetic, now worth +3.0 TAV on every RB candidate.
`EXPOSURE_NO_SURPLUS`'s own docstring says that number "is NOT depth information".
`test_depth_exposure` pins only the all-no-bench and deep cases, never the mixed shape.

**J-07.** Kicker composition, logged by the pass explicitly as a KNOWN item measured for the record:
31 kickers for 12 K slots, seats 7/11/12 at five each, 28 K taken in rounds 8-14 **before the first
DL** (R15), round 21 twelve DBs in a row, `structural_findings` = 0.

**J-08.** `corpus_state` answers the wrong question **in both directions**, measured. Direction one:
a real per-league upload → state `doctrine_only`, light "🟢 Computing from the shared baseline only —
no local data in the mix". Direction two: `bot_research.FINDINGS_PATH = data/baseline/bot_research.json`
is git-tracked but absent from `INPUT_MANIFEST.json`, so planting an empty one → `includes_local`,
"plus 1 file **you added**. Your uploads change replacement levels…" — LLM-panel output described to
the user as their own upload — **and `baseline_manifest.py --check` exits 1, turning CI red, the
first time a SOURCE FINDING is ever written.**

**J-09.** The committed prediction record was priced from the wrong export **and** the wrong pricing
path. `prediction_record.main()` builds `DataMerger()` with no `set_league_format`, a vendor
reconstruction of `players_db`, a hardcoded 1QB/non-TEP mock league, and calls `compute_draft_board`
with **no** `sleeper_projections`. Measured on the committed file: all 264 rows
`bpa_source == points_vor_draftsharks`; the unformatted merger resolves to
`te_premium_dynasty_rankings.csv`, so B Bowers is 309 in the record vs 259 under the league it claims,
McBride 306 vs 253, Loveland 284 vs 241 — TE values ~20% high for its own stated shape. Write-once by
design, so it cannot be corrected in place.

**J-10.** `quantity_readers` grades by bare key name across unrelated namespaces. `starters` (the
`depth_exposure` key) is DECISION with readers `player_universe.py, app.py` — both of which are
`roster.get("starters")`, Sleeper's roster field; no consumer reads depth_exposure's `starters`.
`value_lost` is DECISION because `bye_concentration` reads it inside the producing module.
`KNOWN_WRITE_ONLY` guards only names that happen to be unique.

**J-11.** `suite_taxonomy`: measured 123 fast modules, **210 s**, against a docstring claiming "53
fast modules, 845 tests, 1.5 seconds". `test_invariant_confirmation_anchors` 57.2 s,
`test_quantity_readers` 32.0 s, `test_board_renders_absence` 11.8 s, `test_render_trace` 10.0 s. The
cost drivers are the self-integrity instruments — AST walks, importing `app.py` five times,
Playwright — none of which the substring detector sees.

**J-12.** `draft_history` is **wired to nothing**. Its docstring calls it "the substrate for all
three (#92)" and "what gives the Prytaneum explicit visibility of which Draft PickSnapshots exist";
`grep -l draft_history *.py` (non-test) returns only itself. `test_cdme_ingestion_boundary._NEVER_IMPORTED`
lists it as a store CDME must never read — trivially true of a store nothing writes.

**J-13.** `sleeper_client` uses the exact write pattern `store_io`'s own docstring measured as
torn-read-prone (91,956 empty reads of 98,405 under one concurrent writer): `write_text` for the
~10 MB players cache and for `_write_snapshot`. `app.py:3607` calls `get_players()` at top level on
every rerun. If Sleeper is down at the moment a torn read forces a refetch, `get_players` returns
`{}` — **an empty player universe indistinguishable from "no players"**.

**J-14.** `_sum_weeks` collapses "week unreachable" with "week empty": `get_weekly_projections`
returns `{}` on `SleeperAPIError` *and* on an empty payload. And `get_season_stats` claims the same
failed-week handling via `_sum_weeks`, but `get_weekly_stats` **raises**, so one failed week aborts
the whole realised-season sum — the two docstrings disagree.

**J-15.** `store_io.write` dropping a write to a marked store has a consequence the disclosure does
not name: `attachments.save_attachment` writes the file bytes **first**, so a corrupt `captions.json`
leaves an orphan file with its caption lost while the call returns success.

**J-16 (low/style).** `build_baseline_projection_rows` extrapolates one week × `season_factor` — the
thing `get_season_projections` argues against — filters on raw `position`, and has no production
caller. The 0.75-PPR → standard branch, and `len(x and [])`, both reported again.

**Nulls filed by pass J, with method (logged as filed, not adjudicated):** LLM→CDME identity/pricing
path (injection tests checked and found non-vacuous); `resume_join`; end-to-end structural (300/300
picks were `candidates[0]`, 0 `tav=None`, `fills_required_slot` never bound, 11 zero-margin picks);
`lineup_optimizer.optimize_lineup`; `render_trace --check`; `assertion_floors --check` — **filed
explicitly as a *limit* rather than a defect**, the pass having found the `skipTest` hole and judged
it inside the docstring's declared scope.

**Declared not confident:** NaN reachability for `need_bonus`, `eligibility_bonus`, `depth_exposure`,
`displacement_adj`, `time_horizon_adj` — not in `_records_with_normalized_nan`'s list, not
established either way. `store_io` cross-process locking — medium confidence only.

**Setup artefact the pass flagged itself:** in a non-git extracted tree,
`test_baseline_manifest`, `test_doc_index`, `test_prose_names`, `test_superseded_proposals` fail on
`git ls-files` exit 128. Not a defect; those four depend on git being present.

## Wave 6 — passes K and L

**VOID ATTEMPT, logged because the log is append-only and a re-run must not read as a single
uninterrupted wave.** Both passes were launched and both died on the account session limit
(resets 14:00 UTC) before either produced a report. **No findings. Nothing from the void attempt
enters this log or the ledger.**

Two things survive it, and only these:

1. **A mandate error, caught by pass K before it died.** The Wave 6 steering list named
   `pick_analysis` and `bye_concentration` as modules to examine. They are not modules — they are
   `draft_strategy.pick_analysis` (line 896) and `lineup_optimizer.bye_concentration` (line 644).
   Verified directly. The relaunched mandate names them correctly. A pass sent to read files that
   do not exist spends its opening minutes on my error.
2. Pass K had a probe (`probe_identity.py`) running against `data_merger`'s identity path when it
   was cut off. Its output was never reported and is not logged.

**Relaunched** with the corrected mandate, otherwise unchanged, after the limit reset. The
relaunch is Wave 6. Both passes have reported.

---

### Pass L — reported 2026-09-18. Verbatim: `wave6/PASS_L.md`

*Logged as stated by the pass. No verdicts, no novelty calls, no merging.*

**L-01.** `pick_analysis` reports a **measured** zero denial where nothing was measured. The
2026-09-16 ruling gave survival a third state (no next pick → `survival_probability=None,
risk_by_team=[]`); `pick_analysis` derives `rivals_considered` from `risk_by_team`, and an empty
list selects `DENIAL_NO_INTERVENING_RIVAL` — whose own comment says "0.0 is a measurement" and
which renders as *"no rival had a pick before your next turn"*. At a no-next-pick node there is no
next turn. Measured at index 299: `survival_basis='no_next_pick', denial_value=0.0,
denial_basis='no_intervening_rival'`. Hits every seat's final pick (12 of 300) and far earlier for
any seat that traded late picks. **Survival got a fourth token; denial did not.**

**L-02.** `pick_analysis` computes positional forfeits off **upside-mode curves** under
`mode="auto"`: the guard is `{} if mode == "upside"`, testing the *requested* string, while
`draft_room` resolves `"auto"` → upside at round ≥ 15 and whenever no measurable VOR > 0. Measured
on a 169-pick drain with `mode="auto"`: `AJ Barner TE forfeit=85.71`, `RJ Harvey RB forfeit=37.98`;
`mode="upside"` at the identical state yields `None` for all. 85.71 becomes 8.6 necessity points.
Upside-score curves fed to a normaliser calibrated on VOR-scale curves. Affects every `"auto"`
trajectory from round 15 pick 2 on; the live UI is unaffected because it defaults to balanced.

**L-03.** `draft_counterfactual.compare_trajectory` prices BPA on a different board than the engine
priced its pick on — `_full_board` calls `compute_draft_board` **vendor-only** while `engine_tav`
comes from a scoring-aware snapshot, so `regret_vs_bpa` subtracts a vendor-only TAV from a
vendor+Sleeper one. `config["priced_from"]` is recorded and never checked. Two "by construction"
claims are also false: `regret_vs_bpa >= 0` fails when the feasibility backstop binds (recorded
binding 2 of 112 and 2 of 196 picks in real arms), and `upside_rule` is not forwarded, so a
CROSSING-rule trajectory is compared against ROUND-rule boards.

**L-04.** A CSV with a `source_date` column that is **blank** is dated `NaN`, labelled **declared**,
and outranks genuinely undated rows. Measured: `source_date repr np.float64(nan) | basis declared`;
`_negated_date('nan') < _negated_date('')` → True. `upload_batches.parse_as_of` protects only the
*stated* path; the *declared* path is unvalidated.

**L-05.** `outcome_record.load` collapses "damaged" into "absent" — `except (JSONDecodeError,
OSError): return None` — so `capture` sees `existing=None` and writes `revisions=[]`, wiping the
trail. Measured on a truncated record: `weeks()` still lists the week,
`store_io.unreadable_stores()` is `{}` because `load` bypasses `store_io.read` so the damage guard
never arms, and `main --list` raises `TypeError: 'NoneType' object is not subscriptable`. The
module's own guarantee is that "a correction is VISIBLE rather than silent". No test exercises a
damaged file.

**L-06.** Draft Room session state leaks **across leagues**. `activate_league` resets chat, snapshot
and merger but none of the `draft_room_*` keys, and nothing ever sets `draft_room_debate_result`,
`draft_room_last_snapshot` or `draft_room_snapshot_cache` back to `None`. `stamp_is_current`
compares only `picks_consumed` and `merger.freshest_date` — no league or draft identity. Scenario:
league A at `2.03` with 14 picks, run the debate, switch to league B also at `2.03` with 14 picks →
**A's debate renders under B's board with no staleness note**, and A's snapshot feeds B's next diff.
Read, not measured (needs Streamlit).

**L-07.** The snapshot cache key omits pick **contents** (a commissioner undo + re-pick keeps `len`
constant), `season_projections` (a re-sync does not invalidate), and any upload dated ≤ the current
max or blank.

**L-08.** **Mutation testing: three live valuation constants survive their own test corpus at absurd
values.**

| mutation | tests run | outcome |
|---|---|---|
| `NEED_BONUS_PER_FLEX_SHARE = 0.0` | 307 | **all pass** |
| `NECESSITY_RUN_BONUS = 500.0` | 275 | **all pass** |
| `TIME_HORIZON_SLOPE = 0.0` | 277 | 1 unrelated `StopIteration` in a fixture search; no assertion about the adjustment fired |

And the flex-share constant is **not dead**: on the real league RB `need_bonus` goes 0.38 → 0.00
after two RB picks, and **every IDP position's need (0.67) comes entirely from it** — IDP_FLEX is
flex-only — so zeroing it removes the whole positional-need signal for LB/DL/DB and nothing notices.
No test file names any of the three constants.

**L-09.** `need_bonus`'s formula contradicts two prose claims: the docstring says "flex demand only
counts once a team's dedicated slots are already filled", but `flex_remaining = flex_share -
max(filled - dedicated, 0)` is positive at `filled=0`. Measured on an empty roster: RB 8.38, WR
8.38, QB 4.85, TE 4.38 against a dedicated-only 8.00/8.00/4.00/4.00.

**L-10.** The reconciliation conflict ledger names the wrong rule: `reason` is computed against
`ordered[0]`, but `chosen_value` may come from a lower-ranked row when the winner's field is null —
which is the point of the field-level merge. Measured: ledger records `reason='format_match'` for
two files with identical format scores, where recency actually decided.

**L-11.** `upload_batches.record` returns a batch id for a batch that was never persisted, because
`store_io.write` returns silently for a store marked unreadable. The user's **stated as-of date is
dropped** while the UI reports success, degrading "stated > declared" to "undated loses every tie".

**L-12.** `doc_index` files a document reading *"Nothing in this file is withdrawn"* under
**WITHDRAWN** — the stem regex `withdraw|retract|⛔` over the first 12 lines, first match wins.
Measured: 25 WITHDRAWN, with false positives including `evidence/roster_proof/README.md` and a file
that says its numbers "are current". No negative-phrasing case in the test.

**L-13.** `_recency_weight` prices "no date" as exactly "60 days old" (0.5), so an 89-day-old source
at 0.36 loses to an undated upload. Pass labelled this opinion-level.

**L-14 (minor/prose).** Stale mtime-fallback prose in two places; `bye_collision`'s `BYE_UNKNOWN`
claim vs a loop that never emits it, and one token carrying three facts; `depth_ratings.depth_label`
returning `None` when every peer measures 0.0; `test_term_lifetimes` matching `"bpa"` and
`"risk_adj"` trivially in raw text; `measurement.counted` treating `NaN` as present; `app.py:1109`
swallowing every `sync_league`/`get_players` exception with a bare `pass` and no notification.

**Nulls filed by pass L, with method (logged as filed, not adjudicated):** `DataMerger._resolve`
identity namespaces — **branches enumerated, the exact and alias paths confirmed unguarded**, and a
real-data measurement of **0 of 1,626** offense queries resolving onto an IDP row, with the pass
stating plainly it is *"not confident it stays null under a different vendor file"*; `_merge_memo`
invalidation; `bye_concentration` ratio bounds via the Hungarian solve; `draft_counterfactual.bpa_row`
`#193` crash genuinely fixed.

### Pass K — reported 2026-09-18. Verbatim: `wave6/PASS_K.md`

*Logged as stated by the pass. One verification of mine is marked inline as mine; everything else is
the pass's own claim, unadjudicated.*

**K-01. `load_all`'s per-file dedup drops real players before the identity model can protect them.**
`df.sort_values("rank").drop_duplicates(subset="norm_name", keep="first")` runs on every rankings
file *before* `_reconcile_rows` builds its `norm_name|position_group` key. The comment justifies it
with the same-position "B Robinson / B Robinson Jr." case, but a first-initial export collides across
positions constantly. Measured by the pass: all five offense files carry `J Love` (RB ARI) **and**
`J Love` (QB GB); also `J Williams` WR DET / RB DAL, `M Washington` WR MIA / RB LV, `K Williams` RB
LAR / WR NE, plus six more in the IDP files. The lower-ranked namesake is dropped from **every** file,
so `_dedup_by_name_and_position` and `_drop_contested_identities` never get a second row to protect.

> **VERIFIED BY THIS SESSION**, not taken on the pass's word — run from the repo root on the owner's
> own league format:
> ```
> Jordan Love      QB GB   matched=False  proj=None tv=None rank=None
> Javonte Williams RB DAL  matched=False  proj=None tv=None rank=None
> Malik Washington RB LV   matched=False  proj=None tv=None rank=None
> Ja'Marr Chase    WR CIN  matched=True   proj=339.0 tv=84.0 rank=5.0
> ```
> A **starting NFL quarterback in a superflex league** has no projection, no trade value and no rank.
> The control matches normally.

**K-02.** `positional_forfeits` uses the unnormalised take table `#206` repaired only for survival.
Measured: rival top-5 = 3 RB + 2 WR, assigned P(RB)=0.90 and P(WR)=0.16 → 1.06 players from one pick;
the same five rows carry **0.029** total mass in the survival model. Over 22 picks `expected_taken` =
RB 19.8, WR 3.52, QB 0.0 — **23.3 players from 22 picks**, and zero QBs in a superflex league whose
own pace prior asserts six go in round 1. The RB curve read at index 19.8 yields forfeits of 100+.
`pick_debate.py:488` renders "~19.8 RB pick(s) expected before then" to the model. And the mutation
`RUN_TAKE_PROBABILITY_CAP = 9.0` — a probability cap above 1 — **survives all 51 tests**.

**K-03.** A league-specific upload with an untagged filename **loses every field to the stale
committed baseline**, while `data_merger.py:1768` claims "a league-specific rankings/trade-value
override … takes priority over the global pool". No such rule exists: precedence is basis →
format-match → date → filename, and `league_dir` confers nothing. `_detect_rankings_format` tags from
**filename only**. Measured: a copy of the baseline with every value doubled and
`source_date=2026-09-15`, dropped in a league dir as `rankings_export.csv` → Chase still returns the
2026-08-18 baseline's 339/84; renamed with format tokens → 678/168. The app stores uploads under
`uploaded.name` unchanged.

**K-04.** Declared `source_date` is never validated — `parse_as_of` guards only the user-*stated*
path. Measured: a frame dated `8/28/26` beats `2026-08-18` on both fields, recorded reason "the newer
source_date wins", because `_negated_date("8/28/26")` = `1/71/73` sorts below `7973-…`. Which
malformed dates win is arbitrary (`1/5/26` loses).

**K-05.** Two rookie definitions. `dict(zip(ktc["_name_key"], ktc["rookie"]))` is last-row-wins;
measured **58 of 787** pool players disagree with `years_exp == 0`. `Jeremiyah Love` (RB ARI,
years_exp 0 — the "J Love" that *survives* K-01) is flagged **not** a rookie because Jordan Love's row
wins the key; Keon Coleman (years_exp 2) is flagged a rookie. "Rookies only" excludes the class's RB1;
"Veterans only" includes him.

**K-06.** `_conflict_reason` is computed against `ordered[0]` even when the chosen value came from a
later candidate — measured to record `format_match` where recency actually decided.

**K-07.** The mock-draft format override reloads the merger **twice per rerun** and wipes
`_merge_memo`. Measured: board build **0.87 s warm, 18.0–18.9 s cold**, paid on every button click in
the mock view.

**K-08.** The Draft Room snapshot cache key omits `season_projections` and `league_format`, and
nothing pops the cache on sync: sync mid-draft with new projections and no new pick → stale snapshot.

**K-09.** `build_roster_table` overwrites Sleeper's own `position`/`team` with the vendor row's.
Measured on 43 matched rows: **4 LB→DL** (Nolan Smith, Byron Young, Nick Herbig, Cam Jones), and the
Matchup view groups by that field, so Sleeper linebackers render under DL. Also two spellings of
"unrostered" (`"FA"` vs `NO_NFL_TEAM`).

**K-10.** `regret_vs_bpa >= 0 "by construction"` is false — `_board_order` sorts `fills_required_slot`
before `final_score`, so the engine is not the TAV-argmax when the backstop binds; the test pins it on
fixtures where the backstop cannot fire.

**K-11.** `FORFEIT_SCALE_MAX = 100` is justified by a scale that no longer exists — the docstring says
universal_value "is CONSTRUCTED so 100 is the largest real VOR gap"; `_scale_vor_to_bpa` now returns
raw points.

**K-12.** The late-round necessity label is a **knife-edge on the clamp**: raw can reach ~177, is
clamped to 100, then ×0.3 from round 15, so exactly 30.0 reads "LOW URGENCY" and anything else reads
"DOESN'T MATTER MUCH". The label is therefore a function of whether the *pre-clamp* sum exceeded 100 —
raw 99.9 → "DOESN'T MATTER", raw 140 → "LOW URGENCY".

**K-13 (low/instrument).** `load_all`'s `except Exception: continue` makes a damaged vendor file vanish
silently; `_compute_percentiles`' `setdefault` gives 19 colliding keys the wrong percentile pool;
`_bye_week_map` raises `KeyError: 'team'` (reproduced) when an external source carries `bye_week`
without `team`; `pick_value` collides `1.03` with `10.3`; and the measured-zero-as-unpriced guard is
recorded as an owner-ruled collapse rather than hidden.

**Mutation battery (K's own, independent of pass L's):** seven constants, one tree copy each.
`RANK_TAKE_PROBABILITY` all 0.99 → 3/167 fail, none a survival *value* test;
`FORFEIT_OPPONENT_BOARD_DEPTH = 0` → 5/167; `NECESSITY_BASELINE = 0.0` → 2/166; fuzzy
`match_cutoff = 0.0` → 2/118; `_STRONG_RATIO = 0.0` → 4/50; `CLIFF_HIGH_RATIO = 1000` → 3/116;
**`RUN_TAKE_PROBABILITY_CAP = 9.0` → 0/51, survives.** K's own summary: "detection exists but is thin
(2-5 tests per absurd constant, typically structural rather than behavioural)".

**Nulls filed by pass K, with method (logged as filed, not adjudicated):** `_resolve`'s four branches
enumerated — exact path applies neither namespace nor offence-position rejection, but no real-data
case found where a single wrong-position exact row was returned as verified; **"not confident this
holds for the free-agent table (full names)"**. Also `outcome_record`, `upload_batches.record/forget`,
`league_prefs`, `decision_log`, `resume_join`, `basis_semantics`, `ordinals`, `measurement` — every
`except` and early return read, each collapsing absent/damaged only where its docstring says so. And
`bye_concentration`'s bounds via the Hungarian solve.

*(Note for triage, not a reclassification: pass K filed `outcome_record` as a null on the same day
pass L filed a measured defect in `outcome_record.load`. Both stand as filed.)*

<!-- APPEND POINT: each pass's findings go below, in arrival order, unedited afterwards. -->
