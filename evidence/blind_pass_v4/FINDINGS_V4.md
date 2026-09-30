# v4 blind pass — every finding, all five lenses

Five Fable passes against `v3-freeze` (`eac7491`), worktree-isolated, split lenses, mandate in
`MANDATE_V4.md`. **26 findings: 1 HIGH, 11 MEDIUM, 14 LOW.**

**Every pass reported opening none of the denied files.** Three noted the same near-miss —
`git diff --stat` and `git log --oneline` print evidence/ path names and commit subjects that name
repairs. Two disclosed it unprompted as a partial contamination of the blind condition. That is the
honour condition working as designed.

**A FIXTURE ERROR HIT FOUR OF FIVE PASSES AND EVERY ONE CAUGHT IT THEMSELVES.** The worktrees were
created at `cf8fa0c`, a divergent lineage 860 commits from `v3-freeze` where `league_config.py`
does not exist. Lens A was corrected by the coordinator; B, C, D and E each noticed independently and
ran `git checkout --detach v3-freeze` before reading. Every report states it. Had any pass not
noticed, it would have produced a fluent report about a different codebase.

---

## THE CONVERGENCES — found independently by lenses that could not see each other

Convergence is the strongest evidence available here: these were reached from different territory by
readers with different mandates.

| finding | lenses | what it is |
|---|---|---|
| `health_penalty` returns NaN for a priced row | **A F2, B F1** | a priced player silently becomes unpriced |
| the chair is told a discount exists when it does not | **C F1, E F1** | false statement to the one consumer that cannot check |
| "a ceiling" labelling a 0.0 | **A F3, B F2, E F4** | the label describes a number that did not cross |
| `team_count`'s two callers pass different authorities | **A F5, C F2** | the consolidation's own motivating case still splits |
| `Doubtful` recognised and unrecognised at once | **A F4, C F5** | two vocabularies claiming to agree, disagreeing |

---

## HIGH

### D-F1 — `assertion_execution.py` has never been able to reach a verdict, and its `--write` destroys the record

**WHERE** `assertion_execution.py:131,151`; `store_io.py:215`; `ASSERTION_EXECUTION.json`

**CLAIM** "Run: `python3 assertion_execution.py --check` (fail if the count grew)"; `--write`'s
comment: "A NEW entry needs a reason written by hand -- `--write` leaves it empty on purpose", i.e.
existing reasons are preserved via `existing.get(t, "")`.

**ACTUAL** `store_io.read` has required two positional arguments (`path, default`) since before
`v2-freeze`. `assertion_execution` calls it with one. So:

* `--check` **always** exits 2 with "ASSERTION_EXECUTION.json is missing or damaged -- this check is
  holding NOTHING", whatever the file's state. It has never once compared a run to the record.
* `--write` swallows the TypeError (`except Exception: pass`), so `existing` is always `{}` and
  **every previously recorded reason is written back as `""`**. Reason-preservation is dead code.
* Nothing runs `--check` anyway — absent from the CI workflow and from the doctrine's cadence.
* The three tests that purport to guard it never call it: two assert substrings are present in the
  source; the third reads the JSON with `json.loads`, not through the instrument. All three pass
  with the instrument broken.
* **The record has already drifted inside the range**: running it over the fast tier (2582 tests)
  reports 12 silent tests, one of which is not in the record —
  `test_one_eligibility_reader.TheCaptureIsWhereThisWasMeasuredTests.test_no_row_carries_a_slot_no_league_here_has`,
  a module NEW in this range. Nothing noticed.

**EVIDENCE** `python3 assertion_execution.py --check test_one_eligibility_reader` → "holding
NOTHING" with the file present and valid. `store_io.read(Path('ASSERTION_EXECUTION.json'))` →
`TypeError: read() missing 1 required positional argument: 'default'`. Sandbox `--write` run
rewrote a committed reason to `""`. Instrument and record were added in one commit (`b14d7e1`)
**after** `store_io.read` already took `default` — born broken.

**WHY IT MATTERS** An instrument shipped to police the author's own work cannot produce a verdict,
and regenerating its record erases the content that gives it meaning. Anyone reading "14 silent
tests, each with a reason" is reading a number the apparatus cannot currently produce. This is
precisely the class Lens D was commissioned to find, and it is the second time this repository has
found a self-certifying instrument reporting strength it does not have.

---

## MEDIUM

### A-F2 / B-F1 — an injury designation now UNPRICES a trade-value-priced row (regression introduced by D8)

**WHERE** `draft_room.py:531-541` (`health_penalty`), consumed at `draft_room.py:4774-4785`
(`score_row`). Introduced by D8, commit `40cee06`.

**CLAIM** `health_penalty` docstring: "NaN and not 0.0 (`#187`) ... **The one production caller
already returns NaN for an unpriced row, so this is the same verdict reached one layer in rather
than a new state.**"

**ACTUAL** A row priced on the **trade-value branch** has a real `bpa` and `_points` = NaN.
`score_row`'s gate is `if pd.isna(bpa)` — `bpa` is not NaN — so it calls `health_penalty(status,
basis, NaN)`. `availability_basis` is None on such a row (it is stamped only when `sleeper_points`
exists), so the RULE_FLOOR stand-down does not fire; the status is in `HEALTH_DISCOUNT_RATE`;
`projected_points` is NaN; the function returns NaN. `universal_value` and `final_score` become NaN →
None, while `bpa` stays a number, **`absence_kind` stays None**, and `confidence` is 35.0. The row is
dropped from every rival's `rank_by_id`, so it also vanishes from survival and denial.

At v2 this line was `RISK_ADJ.get(status, 0.0)` and never produced NaN for a priced row. **This is a
new state created by D8, not "the same verdict".**

**EVIDENCE** (B) HEAVY_IDP shape, no Sleeper projections, real capture: 62 trade-value rows, 2
injured — Harold Landry (DL, PUP, bpa 2.0) and DeShon Elliott (DB, IR, bpa 15.0): `risk_adj` NaN,
`universal_value` None, `final_score` None, `absence_kind` **None**, `confidence` 35.0. Unit:
`health_penalty("IR", None, float("nan"))` → `nan`; `health_penalty("IR", None, 100.0)` → `-23.53`.
(A) reproduced the same two rows independently and noted `replacement_basis` is still stamped —
explaining a price that is not shown.

**Reachability** `app.py:3723` passes `priceable_season_projections(snapshot)`, which returns `None`
when the snapshot carries no season projections. Any board built that way routes every IDP row and
every unprojected offensive row through the trade-value branch, where this fires on every injured
player.

**WHY IT MATTERS** A person sees a blank price with 35.0 confidence and no absence reason; the mock
draft's auto-pickers cannot see the player at all; `pick_debate` prints "NOT PRICED -- the engine
could not value this player at all" for a row the engine valued at `bpa` 15.0. The absence-contract
test cannot see it, because it asserts `absence_kind is not None iff bpa is None` and `bpa` is
present here.

### C-F1 / E-F1 — the chair is told a health discount was applied when none was

**WHERE** `pick_debate.py:414-422` (`_format_candidate`, new in range)

**CLAIM** The line exists so the chair can attribute "THE DESIGNATION THAT MOVED `risk_adj`".
`IMMATERIAL_INJURY_STATUSES` ruling (`#191`): Questionable is "OUT OF THE ARITHMETIC AND OUT OF THE
PROSE ... the engine neither prices it nor says it."

**ACTUAL** The branch keys on `availability_basis == RULE_FLOOR` — the basis of the *projection
haircut* — not on whether `risk_adj` is non-zero. For every designation outside
`HEALTH_DISCOUNT_RATE` (Questionable → `immaterial_designation`; NA/Sus/DNR →
`unrecognised_designation`; any status on a vendor-priced row → basis None), `health_penalty` returns
exactly 0.0 and `availability_factor` returns 1.0 — **no discount of any kind exists** — yet the
chair is told one is "already inside the universal value below". The snapshot's own `risk_adj` (0.0)
is on the same object and is not consulted.

**EVIDENCE** (E) 12T_ppr opening board: of 481 priced rows, **65 are Questionable/immaterial with
`risk_adj == 0`**, plus 1 NA and 1 basis-None. In the narrowed 48-candidate snapshot at pick 1.01,
**10 of 48** candidates — McCaffrey, Nacua, Chase, Jeanty, Mahomes, Kittle, LaPorta, Warren, Kraft,
Love — emit the false sentence. (C) independently: 99 Questionable/immaterial rows plus 2 NA and 2
Sus on the owner-league arm. The pinning test exercises only `Out` + `NO_DESIGNATION`, so it cannot
see the immaterial or unrecognised arms. `test_injury_status_materiality` names "all THREE emission
sites"; `_format_candidate` is a **fourth** it does not cover.

**WHY IT MATTERS** A designation the owner ruled meaningless, plus a fabricated claim that it was
priced, reaches the one consumer that argues the pick and is instructed never to recompute. It is
the most common designation on the board.

### A-F1 — D8's "the two paths agree exactly" holds only at `gp=17`, and the feed usually reports 16

**WHERE** `draft_room.py:486-494`; `CDME_CONTRACTS.md:3805`; `test_one_fact_two_paths_one_answer.py:141`

**CLAIM** "AND THE TWO PATHS NOW AGREE EXACTLY, which is the check that says the derivation is the
right one rather than merely a tidier one." Contract: "give the SAME `universal_value` for one fact,
to 6 decimal places."

**ACTUAL** `availability_factor` is `(SEASON_GAMES - missed) / gp` — self-limiting in `gp`;
`HEALTH_DISCOUNT_RATE` is `-(missed / SEASON_GAMES)` — independent of `gp`. At `gp=16`, which the
feed actually reports for IR players, the haircut removes 18.75% (13/16) and the penalty removes
23.5% (4/17). **On the real board, 0 of the 13 rule-floor IR rows satisfy the claimed equality.**
The test that pins the claim only ever calls the helper with `17.0`, and the helper is a hand
formula, not a board.

**EVIDENCE** gp among priced injured: IR/None 103, **IR/16 20**, PUP/None 9, PUP/17 8, PUP/16 4,
IR/17 3. `availability_factor("IR",16)=0.8125` vs `1+HEALTH_DISCOUNT_RATE["IR"]=0.7647`. Jordyn
Tyson: uv −31.30 (haircut) vs −33.55 (penalty), delta −2.25. In dynasty a **second** disagreement
appears: `time_horizon_adj` differs between paths (6.18 vs 4.48) because `_season_proj_pct` is a
percentile of cut vs uncut points, and only the penalty path is then scaled by `d_scale`.

**WHY IT MATTERS** The derivation's sole stated validation is true on the minority `gp` value and
false on the feed's usual one. Magnitude is small (≤2.25 pts) but the "one fact, one answer" (`#126`)
property the item claims to restore does not hold for the population it was measured on.

### B-F2 / A-F3 / E-F4 — "a ceiling" is the label on a 0.0

**WHERE** `lineup_optimizer.py:321-325` (label), `:474-498` (`_stamp_roster_partial`),
`draft_room.py:4800-4806`, rendered at `draft_board_ui.py:896` and `pick_debate.py:376-380`

**CLAIM** The label: "a ceiling -- a player you drafted could not be priced, so a spare who may cover
this position was left out of the solve". The docstring measures the partial state at
`depth_exposure 3.36`.

**ACTUAL** `_stamp_roster_partial` overwrites the basis on every position the unpriced man could
cover, including positions that were MEASURED. `score_row` prices `depth_exposure` **only** under
MEASURED, so the board emits exactly **0.0** — not the over-counting ceiling the docstring measured,
the opposite extreme. The UI then reads: "Depth insurance: +0.0 pts -- what a hole at LB would cost
your lineup, a ceiling -- ...". **A ceiling of 0.0 asserts no exposure at all** — the strongest
possible claim — on the position the engine knows least about. `invariant_registry` itself records
the quantity as "no longer identifiable" under this token.

**EVIDENCE** (B) HEAVY_IDP, roster with one unpriced LB: optimizer cell `{'exposure': 47.0,
'worst_loss': 33.0, 'basis': 'roster_partially_priced'}`; board `depth_exposure {0.0: 82}`. Control
with all three LB priced: `{'measured': 82}`, `depth_exposure {3.72: 82}`. (E) same shape
independently: worst_loss 20.0 withheld behind a 0.0, TAV 46.97 → 44.57. The mandate's own figure —
48 of 216 rostered players dropped this way on a HEAVY_IDP draft — means **every IDP position's
depth term is switched off for the rest of the draft after the first unpriced IDP is rostered.**

**WHY IT MATTERS** The number crossing to the person is not the number the label describes; the true
exposure (33.0) is strictly above the 0.0 shown. The sibling NO_SURPLUS label was rewritten to say
what its withheld number IS; this one was not.

### A-F5 / C-F2 — `team_count`'s two callers still pass different authorities

**WHERE** `app.py:5590`, `draft_room.py:4210`, `pick_synthesis.py:1806`, `:780-788`;
definition `league_config.py:170-208`

**CLAIM** "ONE derivation, in a stated order of authority ... the input that splits them is a draft
with fewer seats than the league has rosters -- at which point the screen and the engine would price
the same board against different team counts, and every replacement level with it." And: "The engine
reads the same function, so a draft with fewer seats than the league has rosters can no longer give
the two different counts."

**ACTUAL** The screen calls `team_count(pick_order=round_1_order)`; the engine calls
`team_count(league, picks=picks)` with **no** `pick_order` — the seats are not in
`league_for_engine`. Same function, different inputs, different rule fires. Worse,
`pick_synthesis.py:1806` **still spells the pre-consolidation derivation inline**
(`league.get("total_rosters") or len({roster_id}) or 1`), feeding `replacement_ranks` →
`position_depth` → `narrow_candidates`, without `team_count`'s `None` filter; and
`_round_being_decided` keeps a **third** derivation with its own `len(picks) // teams + 1`.

**EVIDENCE** 10-seat draft in a 12-roster league: screen → **10**, engine → **12**, pick_synthesis
inline → **12**. With a pick lacking `roster_id`: `team_count` → 2, inline → 3.

**WHY IT MATTERS** The exact case the consolidation names as its purpose still produces two counts —
the caption on one, **every replacement level** on the other — while the comment asserts it cannot.
`num_teams` is the denominator of every slot share and the multiplier of `remaining_starter_demand`'s
bound.

### C-F3 — the board's position views filter on the primary bucket, not eligibility

**WHERE** `draft_board_ui.py:342-353`, `:402-405`; `pick_synthesis.py:1493-1520`
(`CandidateSnapshot.position: str`, no eligibility field)

**CLAIM** `filter_candidates_by_view`: "a flex-slot view reuses that slot's own real
eligible-position set ... the same semantics `draft_room.py`'s own `need_bonus` math already keys
off of, never a display-only reinterpretation."

**ACTUAL** The view filters on `c.position` — the single primary bucket — because **eligibility never
crosses the snapshot boundary**. A dual-eligible candidate appears in exactly one single-position
view.

**EVIDENCE** Owner-league pick 1.01, 94-candidate snapshot: `view LB: 8 eligible candidates not
shown` — Van Ginkel, Chinn, Byron Young, Will Anderson, **T.J. Watt**, Tuipulotu, Reese, Turner.
Every one has `player_eligible_positions ⊇ {LB}` and the engine priced his `need_bonus` with LB slots
in the assignment.

**WHY IT MATTERS** A manager with an open LB slot opens the LB view and does not see T.J. Watt, while
the board's own `need_bonus` already credited him for that slot. The `#174` shape: the number
crossed, its companion did not.

### C-F4 — the config gate's refusal machinery has no production caller

**WHERE** `league_config.py:41-45, 107-111, 335-371`; only production reader is
`pick_synthesis.py:2026`

**CLAIM** "AMBIGUOUS -- something did not parse cleanly. The only blocking state." `admits_decision`:
"Only AMBIGUOUS blocks ... Age is reported; ambiguity is enforced." `decision_config`: "The config,
or a refusal. Never a degraded fallback." `KNOWN_SLOTS`: an unknown label "makes the config
AMBIGUOUS".

**ACTUAL** `decision_config`, `admits_decision` and `confirmation_state` have **zero production
callers**. Only `ambiguities()` is read, stored as `config_ambiguities`, and rendered as a warning
whose own text says "The board below was priced anyway". An unknown slot code is silently dropped by
`slots_from_roster_positions` exactly as the KNOWN_SLOTS comment warns, and nothing refuses.

**WHY IT MATTERS** Prices reach a person on a config the module's contract says must be refused;
"enforced" describes nothing that runs.

### E-F2 — an absent number is displayed as "withheld"

**WHERE** `pick_synthesis.py:701-716` (`presentable_text`); `app.py:1627-1636`;
`draft_history_ui.py:171-178`

**CLAIM** "The panel already uses `--` for the absence contract: not measured, no value exists. A
withheld number is the opposite case -- it exists and is not trusted -- and `#187` is about never
collapsing the two." `WITHHELD_REASON`: "Withheld, not missing: this number is computed".

**ACTUAL** `presentable_text(field, rendered)` returns `WITHHELD_CARD_TEXT` whenever `field` is in
the withheld set, **ignoring `rendered` entirely** — so an ABSENT value renders as "withheld", i.e.
"computed and not trusted", when it was never computed.

**EVIDENCE** At the user's last pick, `estimate_survival` returns `survival_probability=None` with
basis `no_next_pick`, so `opportunity_cost` and `expected_value_of_waiting` are None for **all 48**
candidates. The survival card correctly says "no next pick"; the two cards beside it say "withheld".
Round trip: the stored-board table renders the same.

**WHY IT MATTERS** A person reads "withheld" as "there is a number and the engine is hiding it" — the
docstring says so in as many words — at exactly the moment the engine's ruling is that the question
does not arise. The two absence states this repair was built to keep apart are collapsed.

### D-F2 — `prose_names`' history shield exempts 45% of the corpus, and three dead names hide behind it

**WHERE** `prose_names.py:69-120` (`HISTORICAL_MARKERS` / `is_history`), `:371-385`

**CLAIM** "SO THE RULE IS NOT 'the name exists' BUT 'the name exists, or the prose says it is
history.'" The instrument reports "0 backticked name(s) in prose exist nowhere".

**ACTUAL** A block is exempted when **any** marker appears anywhere in it, and the vocabulary
includes "was", "were", "arm". A bare "was" in an unrelated sentence shields every name in the block.
Measured: of 1,446 prose blocks naming something, **651 (45.0%) are never examined**; **374 of 499
module docstrings (75%)** are shielded; 177 shielded blocks carry no marker other than "was". Three
dead names hide there:

* `test_identity_reaches_the_stat_line.py:16` — **NEW in this range** — "See
  `TheFiftyPlusBucketIsNotDerivableAndSaysSo`." No such class exists; the content lives in
  `TheMandatesOwnClaimForThisItemIsCorrected`. A rename that did not reach its explanation — exactly
  the defect the instrument exists for. Shielded solely by "was".
* `test_take_model_seam.py:11` — `test_the_seam_is_load_bearing` (actual name ends
  `_not_decorative`). Shielded by "arm"/"no longer"/"was".
* `run_roster_proof_capacity_cut.py:17` — `remaining_league_picks` exists nowhere.

**WHY IT MATTERS** The instrument certifies "0 dead names" at the freeze and the number is wrong. The
docstring's stated rule is not what `is_history` implements — it implements "the block contains a
common English past-tense word".

### D-F3 — the test measuring that shield's reach compares constants to their own definitions

**WHERE** `test_prose_names.py:377-447`, `TheHistoryShieldsReachIsMeasuredNotAssumed` (added in range)

**CLAIM** "this class makes its reach a checked quantity instead of an unexamined one"; "Of the 18
weak-exempt blocks that name a live constant, all 18 quote the value the code actually has."

**ACTUAL** `_weak_exempt_blocks` scans **raw file text**, not comments and docstrings, so the regex
matches the constants' own assignment lines. It then compares `getattr(module, name)` to the parsed
value — **for an assignment line, that is a value compared against itself**. Of 28 matches: 20 are
code assignments, 8 are prose; 19 reach the comparison, **18 of them tautologies**; exactly **one**
prose quotation is ever compared. Four prose quotations are silently skipped by `if not
hasattr(module, name): continue` because they quote another module's constant. The non-vacuity guard
is satisfied by the 20 code lines, so it cannot detect the check going vacuous over prose.

**WHY IT MATTERS** The freeze record states the shield's over-breadth "currently costs nothing" on
the strength of this check. The check examines one prose quotation.

---

## LOW

**B-F3** — the fieldability exemption conflates "no ceiling because flex-reachable" with "no ceiling
because the league starts nobody there". A player eligible at {ceilinged P} ∪ {unstarted Q} is never
counted against P and never demoted at P, though Q gives him no slot anywhere. Measured: a 3-WR
roster does not demote a WR/DB dual as the 4th WR body; a 2-QB roster does not demote a QB/TE dual as
the 3rd QB. Real capture, partial-IDP league: 2 of 173 priced DL/LB rows affected; 37 players in the
capture are {LB,DB}-eligible. The docstring's justification ("reaches a shared slot somewhere") is
false for this class.

**B-F4** — `feasibility_first` still promotes by PRIMARY bucket while its mirror `unfieldable_last`
reads eligibility, and its own docstring promises eligibility ("whichever hole that is"). A DL/LB
dual labelled DL gets `_feasible = 1` when the only open slot is LB; a pure LB gets 0. The roster side
was moved to `player_eligible_positions` in this range; the candidate side was not.

**B-F5** — stale invariant comment in `unfieldable_last.demoted`: "A flex-reachable position never
enters `saturated`". Since D7 it does. No numeric consequence, but it is the comment that justifies
the subset test.

**B-F6** — `team_count` excludes a `None` roster id that `team_slots_filled` keys as the string
`"None"`. One null-roster pick makes `len(filled) = num_teams + 1` and the board build raises.

**A-F4 / C-F5** — `Doubtful` is in `RECOGNISED_DESIGNATIONS` and priced by `HEALTH_DISCOUNT_RATE`,
but `availability_factor` returns `unrecognised_designation` for it (it consults
`GAMES_MISSED_FLOOR`, not `GAMES_MISSED_PRICED`). The basis says "never seen" about a priced
designation. Dormant — Doubtful does not occur in the feed.

**A-F6** — `upside_score` claims "DERIVED, NOT CHOSEN (`#56`) ... no new number is introduced", but
`TIME_HORIZON_SLOPE = 0.20` is itself a chosen constant whose stated unit premise is stale: its
comment says it is a nudge "on the same linear 0-100 BPA scale", and `bpa` has been raw points since
before v2. D8 applied exactly this argument to `RISK_ADJ` and re-derived it; D4 reused the
un-re-derived slope and called the result derived. **The contract itself says `TIME_HORIZON_CLAMP`
"inherited a SCALE" and is "NOT resolved".** Also: the lower clamp is unreachable by construction
(`growth = max(0.0, ...)`), a guard doing nothing.

**C-F6** — `health_penalty`'s `rate is None → 0.0` check precedes the projection check, so an
unrecognised designation with no projection returns 0.0, not NaN, contradicting the function's own
absence contract. Bounded because `pd.isna(bpa)` is checked first.

**C-F7** — `superflex_disagreement`'s user-facing text says "every consumer keying off SUPER_FLEX will
score it as 1QB", but `league_format_hint` and `league_format_summary` both treat `count("QB") > 1` as
superflex and `starter_slot_counts` gives QB demand 2.0. The sentence is false in the direction of
alarm.

**C-F8** — `GAME_TIME_CALL_DESIGNATIONS`' docstring says "anything outside both sets is unrecognised
in both", but the injury pill has two colours and paints every non-member crimson = "unavailable" —
the stronger claim.

**D-F4** — `assertion_floors`' per-method floor is keyed on the bare method name, so two classes in
one module sharing a test name collide and only the last is recorded. Five such names exist
(`test_screen_context.py` 4, `test_decision_qualifiers.py` 1). Weakening the unrecorded one, netted
against an addition elsewhere, passes `drops()`. This reopens exactly the hole the range's repair
claims to close.

**D-F5** — the guard against hand-written capture paths exempts any module mentioning
"CAPTURE_PATH" anywhere. `test_battery_pricing_path.py` defines a literal path at line 31 and gates
four real-board tests on it, but mentions `rdb.CAPTURE_PATH` in an unrelated assertion, so the guard
skips it and reports zero offenders while one exists.

**D-F6** — `test_the_magnitudes_are_unchanged_by_this_experiment` (rewritten in this range at A2)
iterates `GAMES_MISSED_PRICED` and asserts `HEALTH_DISCOUNT_RATE[d] == -(games / SEASON_GAMES)` —
**it recomputes the definition and compares the value to itself.** Changing IR from 4 to 8 games
passes. Coverage is not lost (two sibling tests pin literal counts), but the test's stated claim is
not what it checks. Same shape in `test_one_injury_vocabulary_not_two`'s
`test_equal_floors_carry_equal_penalties` and `test_a_steeper_floor_never_costs_less`, tautological
after D8.

**D-F7** — `tav_margin_profile` counts `margin <= 0` as `zero_margin_picks`, so a pick a backstop
**deliberately demoted** (chosen 10 vs runner-up 100, margin −90) is counted under a name meaning
"the ordering stopped carrying information" — the opposite of what happened. In the module repaired so
that "report fields mean their names".

**E-F3** — for columns added at schema 4, a record written before the key existed and one that
captured the value as absent both render "—", and the picker label does not show the schema version.
The `unanswerable` mechanism covers only the four stamp fields.

**E-F5** — when the season fetch fails outright the sync stores `season_projections = {}` with
`coverage.error` set; `priceable_season_projections` takes the `is None` branch and returns no
refusal string, so **the Draft Room renders no warning while the board is vendor-priced**. The
manifest row naming the failure reaches only the LLM context, and the sidebar grade skips it because
its age is None by design. This is the very "silent fallback to vendor-only" the prose names as the
defect.

**E-F6** — the universe stamp hashes **every** field of every row, including `search_rank`, which
churns between syncs and which this repo reads elsewhere as a popularity signal. The third consumer
of the hash is not a cache but a person-facing staleness verdict that names a cause — "an injury
status, a roster move" — the hash cannot attribute. Argued from code; the committed capture is
trimmed to 10 fields so the churn rate cannot be measured offline.

**E-F7** — `unanswerable` is computed from `evidence.get(field) is None`, conflating "key absent" with
"captured as None". A schema-5 record whose merger had no dated projections yields a staleness reason
AND `unanswerable: ['whether the data has moved since']` in the same row — the verdict answers a
question the row says cannot be asked.

---

## WHAT THE PASSES CHECKED AND FOUND CLEAN

Recorded because it says what the gate actually covered, which a findings list alone does not.

**Lens A** — the `HEALTH_DISCOUNT_RATE` derivation itself (proportional to `_points`, not `bpa`,
correctly avoiding a bonus for below-replacement players; PUP now priced identically to IR; the
0.0-projection IR rows now get −0.0 instead of −18). 3.1's percentile population: both percentiles now
ranked over `paired`, both readers gate on `_has_3yr`, no other production reader exists. `need_bonus`
under 2.6 (the flex-remaining identity holds; `slot_coverage` fills dedicated before FLEX; SUPER_FLEX
split sums to 1; order-invariance holds). `derive_kicking_categories` never overwrites a vendor
`fgmiss`; no battery arm double-counts. `CREDIBLE_RIVAL_PATH_MAX_RANK = 4` is a genuine unit
restoration — rank 4's entry was exactly 0.10.

**Lens B** — both board sorts have matching key and direction lists with each direction correct, and
the backstop keys reach every rival's rank ordinal. `slot_coverage`'s coverage weight dominates every
tie-break term; restrictiveness sign is right. `fieldable_ceiling_groups` reduces to `slots+1` for
singletons and gets the 2DL+1LB+dual case right where a by-eligibility count would wrongly saturate.
`flex_reachable_ceiling_groups` reach arithmetic verified across FLEX, SUPER_FLEX, and dedicated-IDP
shapes. `positional_forfeits` per-pick scaling: `expected_taken` totals exactly 5.00 over a 5-pick gap
and 11.00 over 11 — never exceeding the picks in the gap. The `ambiguities` gate passes
`build_mock_league` and refuses unknown slot labels.

**Lens C** — every member of `FANTASY_POSITIONS` / `FLEX_SLOT_POSITIONS` is handled by every consumer,
including all five flex types and the SUPER_FLEX QB-share branch. Slot vocabulary aliases bind the
same objects. The injury consolidation holds on the production path: 22 IR + 12 PUP rows at RULE_FLOOR
with `risk_adj` 0.0, vendor-priced IR rows carrying the proportional penalty. All six `bpa_source`
strings are keys of `CONFIDENCE_BY_SOURCE`. Every basis token crossing the JS boundary has a label,
with raw-token fallback. `draft_history`'s schema round trip: every evidence field exists on the
snapshot, and `config_ambiguities`' three states are distinguished by both readers.

**Lens D** — `assertion_floors --check` is sound and its damaged-file vacuity is closed; all 22 floors
that fell between v2 and v3 were read and every one is an assertEqual→assertAlmostEqual substitution,
a rename, or a rewrite — **none is an emptied test**. `render_trace --check` passes, and an
in-process experiment (empty board → Live 132→121, Mock 142→131) confirms the substance of its claim.
`invariant_registry`'s nine censuses all match observed and its enumerators are derived, not
hand-listed. **`invariant_confirmation`'s false-"caught" mechanisms are genuinely closed** — mutants
are parsed, must build a board in a fresh subprocess, must change its fingerprint, and a baseline arm
runs first. `doc_index --check` current. `baseline_manifest --check` matches 23 files.
`test_snapshot_input_key`'s coverage claim is enumerated from the real signature.

**Lens E** — `player_eligible_positions`' absent-vs-empty split matches its docstring.
`compute_pick_necessity` adds 0.0 for a None `need_bonus` with no fabricated field. `diff_snapshots`
transitions: absent-both skipped, one-sided reported as words not deltas. `config_ambiguities`' three
states survive snapshot → projection → summary → app. `stamp_is_current`'s optional-pair semantics
hold at all four call sites. `positional_forfeits` reaches the chair as a count with the position
named, with no `or 0` coercions. `cut_note`/`cut_body` None for no cut, real remainder counts at all
five call sites.

## WHAT THE PASSES COULD NOT REACH

Full drafts on odd shapes (B, A); how often A-F2/B-F2 fire across a whole trajectory rather than an
opening board; `invariant_confirmation` executed (D — multi-arm, ~20 min/arm); the full tier for
`assertion_execution` (D ran the fast tier, 2582 tests); `data_merger`'s identity/dedup vocabularies
traced consumer-by-consumer (C); `replacement_levels`' demand→rank→level chain end-to-end (A);
E-F6's churn rate (needs a live fetch); the upside-mode chair path on real data (E);
`term_lifetimes` (D, outside range — noted that its `risk_adj` entry still describes "RISK_ADJ
magnitudes" and "Questionable", both removed).
