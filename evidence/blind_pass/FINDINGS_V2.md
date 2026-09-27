# v2 blind pass — what the five lenses found

Five Fable passes against `v2-freeze` (`a8d1627`), concurrent, split mandates
(`MANDATE_V2.md`). **Nothing here is adjudicated.** This file exists so the findings survive the
container; the transcripts do not live in this repository. Each entry is the pass's claim plus
whatever I verified myself, marked as such.

All five reported. All five gave a contamination statement. **None reported opening a forbidden
path**, with three disclosed near-misses recorded under "how the shield leaked" below.

## THE TWO FINDINGS TWO LENSES REACHED INDEPENDENTLY

These are the strongest signals in the haul, because the passes could not see each other.

1. **`league_config`'s blocking state has zero production callers.** Found by the roster-geometry
   lens and the ingestion lens separately. `ambiguities` / `confirmation_state` / `admits_decision` /
   `decision_config` are never called; `app.py` imports the module only for `describe_config_age`.
   The geometry pass measured a league with unknown `DE`/`CB` slots pricing a 970-row board on a
   silently smaller lineup, and a two-literal-`QB` league selecting the superflex rankings *file*
   while pricing QBs under the 1QB regime (Josh Allen 91.03 against 170.02 in the equivalent
   `SUPER_FLEX` league). The ingestion pass added that the gate **would block every real league if it
   were wired**: Sleeper omits `bonus_rec_te` when no TE bonus is set, so `ambiguities()` flags the
   capture's own league and all 36 battery arms as AMBIGUOUS.

2. **The battery's universe is outside the hashed input set.** `baseline_manifest.DECLARED_INPUT_DIRS`
   is `data/baseline` and `data/projections/_global`; `data/fixtures/sleeper_capture.json` — the
   universe every battery number, the render trace and the invariant census rest on — is hashed by
   nothing. Edit one `injury_status` or `fantasy_positions` in it and the manifest still reports
   "input set matches". The instrument pass added `data/player_aliases.json` (gitignored, loaded at
   `DataMerger._load`, consulted in matching): a local alias reroutes one player onto another
   vendor row and the suite's numbers diverge from CI's with the manifest green.

## Lens A — valuation arithmetic

1. **HIGH. `time_horizon_adj` subtracts two percentiles computed over different populations.**
   `_season_proj_pct` is a percentile over ALL priced rows; `_proj3yr_pct` over only rows carrying
   `proj_3yr`. **I verified the populations myself on a real `12T_ppr` board: 481 priced, 259 with
   `proj_3yr`, 222 without** (median 15.9 points, so they sit at the bottom) — and the comment
   directly above that code asserts *"zero rows in the real baseline carry a points projection
   WITHOUT a proj_3yr alongside it"*, which is **no longer true**. Pass measured mean
   `time_horizon_adj` −3.72 in production against −0.03 with matched populations; 190 of 259 rows
   move more than 2 points, 101 flip sign, players whose season rank equals their 3yr rank are
   penalised anyway (Darnold 33/33 → −1.10, Braelon Allen 212/213 → −6.31), and removing the term
   changes board top-1 in 8 of 24 drained states. **Balanced mode, dynasty horizon — the production
   path.** The same comment documents fixing this defect class for rows WITHOUT a 3yr number; the
   residual lands on the rows that have one.
2. **MEDIUM. The bounded additive constants were sized for a 0–100 `bpa` scale that
   `_scale_vor_to_bpa` abolished** (it is now the identity). Real span is −328.6 to +227.6.
   `RISK_ADJ` −18 is now "18 projected points" — 10.4% of a 173-point player, 4.5% of a 400-point
   one. `depth_exposure` converts trade_value into a unit that no longer exists (max observed 9.36).
   `test_need_bonus_cannot_flip_a_large_universal_value_gap` compares the top and bottom priced rows
   (gap ≈556 against a cap of 12), so the invariant it guards is vacuous on the current unit.
3. **MEDIUM. `need_bonus` on an empty roster is a flat per-position constant**: every RB/WR +8.67,
   TE +4.67, QB +4.0, carrying no roster information while the replacement rank already prices the
   slot count. Opening board, top 60: 21 cross-position pairs where the higher-ranked row has the
   LOWER `universal_value` — Jeanty (UV 87.72) above Loveland (91.47), McLaurin (41.70) above Josh
   Allen (44.11). Adjacent gaps in the top 50 have median 2.09, so a 4.0 offset is decision-sized.
4. **MEDIUM-LOW.** The superflex QB startable floor is derived in vendor points and applied to
   league-scored points. Under `pass_td=3` only 19 QBs clear it and the level is QB19 while still
   labelled `startable_floor`.

## Lens B — absence semantics and boundaries

1. **HIGH. The recommendation panel renders a withheld quantity to a human.**
   `SURVIVAL_IS_CALIBRATED = False`, and `withheld_fields()` states the rule: *"A quantity withheld
   from presentation must not reach a person, on any surface, under any name, as itself or as a
   delta of itself."* **I verified both halves: `grep withheld_fields\|SURVIVAL_IS_CALIBRATED app.py`
   returns nothing, and `app.py:1545` renders `round(rec.survival_probability * 100)` under a card
   labelled "Survival to Next Pick (%)", with `app.py:5660` printing "Survival: NN%" for the
   runner-up.** Five other surfaces honour the rule and `test_withheld_propagation.py` covers those
   five. `invariant_registry.py` already concedes the census "cannot, by construction, see a surface
   that never asks at all".
2. **HIGH/MEDIUM.** `need_bonus` is fabricated as `0.0` at the snapshot boundary in upside mode
   while the other four absent team terms cross as `None` with explicit "never 0.0" comments — then
   printed to the chairs by `pick_debate` as a measured term beside two honestly-withheld ones, and
   persisted to `draft_history`.
3. **MEDIUM.** `rival_premium` is a "measured" 0.0 on every upside candidate by construction
   (`universal_value = final_score`, so the difference is identically zero), so `block_opportunity`
   can never fire and `denial_component` is always 0.
4. **MEDIUM.** `depth_exposure` describes a roster the optimizer never saw: rostered players with no
   vendor trade_value are dropped, and every LB candidate's TAV moves 2.52 purely on whether the
   vendor priced a bench body, with the basis token claiming a full measurement either way. The
   displacement term got a `ROSTER_PARTIAL` basis for exactly this hole; depth got nothing.
5. **MEDIUM.** The staleness stamp checks only pick count and the vendor's freshest date. Three
   snapshots at the same 96-pick state with different `pool_scope` have leaders Tony Pollard /
   Tony Pollard / Jadarian Price and **identical stamps**, with `stamp_is_current` returning True.
6. **LOW.** Stale `eligibility_bonus` in the module identity prose, the README and four other
   places, against a `TEAM_SPECIFIC_TERMS` that has three names.

## Lens C — the measurement apparatus

1. **HIGH. Every substantive view is traced in its EMPTY state.** `render_trace.py` seeds the
   snapshot with `"rosters": [], "users": []`, so the Draft Room's 117 recorded calls are the
   sidebar prefix plus `st.info("No roster found for your account in this league yet…")` — **zero
   board, pick-synthesis or mock-draft calls.** The non-vacuity guards are satisfied by the shared
   prefix and by a radio that renders before the roster guard. Break the live-draft board and the
   trace is byte-identical.
2. **HIGH (for the instrument's credibility). `RENDER_TRACE.json` is calendar-dependent**: it
   records `Data Freshness: Aging`, which is `recency_grade(now − committed baseline dates)`. It
   already churned once (`Recent` at `2da0b0e`, `Aging` at `1003ef4`, regenerated inside an
   unrelated commit) and **flips to `Stale` on 2026-11-19** with no UI change.
3. **HIGH. Both committed "caught" verdicts in `invariant_confirmation.json` were produced by the
   harness's own self-test**, not by any engine test: under `--failfast` the first failure is
   `test_invariant_confirmation_anchors.py` asserting the anchor TEXT is present, and applying the
   mutation removes the anchor — so every mutant is "caught" by construction before any engine
   behaviour runs.
4. **MEDIUM-HIGH. `assertion_floors` cannot see any silent way a test stops running**:
   `@unittest.skip`, `@expectedFailure`, `self.skipTest()`, `return` before the assertion,
   `if False:`, a loop over `[]`, `try/except AssertionError: pass`, a class that stops inheriting
   `TestCase`. Nothing in CI counts skips, and one test skips on the committed baseline today.
5. **MEDIUM.** `prose_names`' history shield exempts 2,515 of 15,613 prose blocks and **1,253 of
   2,006 backticked names (62%)**; 1,062 blocks are shielded by the word "was" alone. `haystack()`
   includes every tracked JSON and probe script, so a retired term stays "alive" while the evidence
   tree remembers it.
6. **MEDIUM.** Tests passing with zero executed assertions, measured under an instrumented
   `TestCase` — notably `test_the_anchor_adds_idp_prices_without_changing_any_other`, whose control
   board has **0 priced rows of 514**, so "without changing any other" is proven over nothing.
7. **MEDIUM.** The manifest gap (see convergences).
8. **MEDIUM-LOW.** `test_audit_cadence` counts a substring, so commenting out both
   `assertion_floors --check` steps leaves the count at 2 and the test green.

## Lens D — roster geometry

1. **HIGH.** The fieldability backstop exempts every flex-reachable position although
   `slots_reachable(P) + 1` is as derivable as the dedicated case. Measured on a real 12-team draft
   with one `IDP_FLEX`: six of twelve rosters finished holding 6–7 IDP against a derivable ceiling
   of 2, every roster reporting 8/8 starting slots filled, all three guards silent.
2. **HIGH.** Roster fill is counted by primary label while the bonus is subtracted against the pool
   bucket, so a four-DL/LB roster gets `need_bonus` 8.0 on all 286 LB rows while the optimizer says
   both LB slots are already covered; Travis Hunter (`["DB","WR"]`) drafted in an offence-only league
   registers as filling a DB slot.
3. **HIGH.** `league_config`'s blocking state (see convergences).
4. **MEDIUM.** `roster_diagnostics` solves lineups from a single label while the battery's audit uses
   full `fantasy_positions` — the same roster fills 4 slots under one and 2 under the other.
5. **MEDIUM.** Three different eligibility readers that disagree on real rows.
6. **MEDIUM.** `feasibility_first`'s round-count fallback counts IR slots, and the Mock Draft never
   supplies the round count.

## Lens E — ingestion, identity, provenance, vintage

1. **HIGH.** `_identity_hint` is stamped per FILE, so a blank "just missed the cut" row for
   `K Williams` in one export splits Kyren Williams into two canonical records; `_resolve` finds two
   candidates it cannot separate and returns `iloc[0]`. In the owner's superflex format he prices off
   the **1QB TE-premium** file. `match_verified=False` is emitted and nothing acts on it;
   `grep _identity_hint test_*.py` → 0 hits.
2. **HIGH.** `name_key` takes the first initial plus everything after the first token, so
   "Green Bay Packers" → `("g","bay packers")` never matches the CSV's `G Packers`. **11 of 32
   defenses** miss (GB, KC, LAC, LAR, LV, NE, NO, NYG, NYJ, SF, TB); on the documented no-sync
   fallback the Los Angeles Rams — the best-projected DEF in the pool — price as
   `no_priceable_input`.
3. **MEDIUM-HIGH.** The league's kicking rules cannot reach Sleeper's stat line: there is no
   `fgm_50p` key, so 5.5–8.8 projected 50+ makes per kicker (28–44 points, 25–35% of a kicker's
   total, 973 across the pool) are never scored and ~3.4 misses per kicker go unpenalised. DEF has
   the same shape for `pts_allow_*`. **This distorts the K ordering `#30`'s streaming floor is built
   on.**
4. **MEDIUM.** The vintage gap — corrected in `evidence/design_35/GATE_FOR_VDS.md`, see below.
5. **MEDIUM.** Cross-format field fill in `_reconcile_rows` is silent and untraceable for
   rank/trade_value: Alvin Kamara's rank, trade_value, projection and proj_3yr all come from the
   1QB TE-premium export via a blank winner row, with 0 entries in `reconciliation_conflicts`.
6. **MEDIUM.** The season-sum coverage record is written by `sleeper_client` and read by nobody,
   so an 11-week partial sum silently outranks a 17-week vendor total.
7. **MEDIUM-LOW.** 120 Sleeper players are rejected for a same-key vendor row on a different team;
   Cam Little (top-10 kicker) is rejected over the vendor code `JAC` versus `JAX`.

## WHAT I CORRECTED IN MY OWN WORK

Lens E's vintage finding is against me. `GATE_FOR_VDS.md` said the `#30` wiring fix was
"vintage-matched"; the capture is `2026-09-07` and the weekly lines `2026-09-22`, **fifteen days
apart**, and nothing compares `captured_at` between them. Corrected in place at that file with the
measurement, rather than quietly edited away. It does not change that `#30` fired; it does withdraw
any claim resting on the two being one vintage.

## HOW THE SHIELD LEAKED — protocol findings for the next pass

1. **Commit subjects are not shielded, and mine leaked conclusions.** Lens A disclosed seeing
   `git log --oneline` print *"upside gap RESULT: the differentiator does not participate -- 2 of 87
   picks"*. Its upside-mode numbers are its own measurement and it said so, but its conclusion there
   converges with a subject line it had read, so **that convergence is not independent evidence and
   is not counted as such.** Next pass: shield the log, or write neutral subjects during the work a
   pass will audit.
2. **An instrument that walks the tree defeats a read-deny.** Lens C ran `prose_names.py` as-is,
   which tokenises every tracked `*.md` and `*.py` including the forbidden ones, and a regex probe
   printed forbidden PATHS. Contents were not viewed. A deny rule cannot stop a program the pass is
   auditing from reading what the pass may not.
3. **`isolation: "worktree"` did not hand any pass the tree under audit** — recorded in
   `MANDATE_V2.md` with the SETUP lines a re-run should carry.
4. **I cancelled work mid-flight and it cost a result.** I messaged the two stalled passes to hand
   back early. Lens C's finding 3 was mid-probe: whether either committed mutation SURVIVES the
   engine suites once the self-referential anchors module is excluded is **untested**, and it is
   untested because I interrupted it. The design defect stands; the survival verdict does not exist.
