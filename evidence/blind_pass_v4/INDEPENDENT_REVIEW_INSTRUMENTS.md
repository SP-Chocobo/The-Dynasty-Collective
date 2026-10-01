# Independent review: can each Tier 0 instrument report success while measuring nothing?

> **STATUS: this document is a live adversarial review of the measuring instruments**, by a
> session given the instrument list and that one question. Every claim is labelled **PROVED** (a
> thing was broken and the instrument's own output is quoted) or **SUSPECTED** (read from the
> code, not demonstrated). Nothing here was repaired — this branch only reports.

The method was not reading. For each instrument: break the thing it claims to catch, read what
it then said, and run a **control** — the same break where the instrument *should* fire — so a
silence can be told from a detector that was never wired. Script:
`probes/decisive_tests.sh` (refuses to start on a dirty tree, runs under
`PYTHONDONTWRITEBYTECODE=1`, clears `__pycache__` between arms, restores with
`git checkout --`). `git status --short` was empty after the run.

## Environment, recorded because it changes how two instruments read

This container started with **no `pandas`, `numpy`, `scipy` or `streamlit`**. In that state
`invariant_registry.py` exits 1 with five `ModuleNotFoundError` rows — it fails loudly, to its
credit. `assertion_execution.py` printed
`9 of 1265 tests that ran executed no assertion (0 skipped, 179 errored)` and **exited 0**.
`requirements.txt` was installed before any measurement below.

---

# FINDINGS, severity order

## 1. PROVED — `invariant_registry._python_rendered_figure_sites` counts the CONFORMING sites, so its census moves when someone complies and cannot move when someone bypasses

**Instrument** `invariant_registry.py` · **identifier** `_python_rendered_figure_sites`, serving
the entry `one engine figure reads the same on every surface` (census 8).

**What it claims.** The entry's `population` field:

> "The Python render sites. **A new one added with a bare f-string is the whole defect
> returning**: Python rounds half-to-even and toFixed rounds half away from zero, so the two
> disagree on any figure landing on .5 above an even floor — one player showed as 16 in one
> panel and 17 in the other."

**What it does.** It walks `ui_source.text()` and counts `ast.Call` nodes whose func is
`ast.Name(id="_figure")`. That is the set of calls to app.py's *conforming* wrapper. A bare
f-string render is not such a call, so it cannot change the count.

**The demonstration.** `probes/decisive_tests.sh` arm B, on the real `app.py`:

```
--- baseline ---
ok     recorded=    8  observed=    8  one engine figure reads the same on every surface

--- BREAK: add ONE bare f-string render of an engine figure to the UI surface ---
    st.caption(f"{rec.team_acquisition_value:.0f} UV pts")
ok     recorded=    8  observed=    8  one engine figure reads the same on every surface
invariant_registry exit=0

--- CONTROL: add ONE CONFORMING _figure(...) render instead ---
MOVED  recorded=    8  observed=    9  one engine figure reads the same on every surface
invariant_registry exit=1
```

The guard is **inverted**: adding a correct render site trips it; adding the exact defect its
own prose names leaves it green. (`probes/probe_invariant_registry_figure_sites.py` shows the
same result by patching `ui_source.text` in memory, for a reading that touches no disk.)

**And the census of 8 is already not the population the sentence describes.**
`app.py`'s `_best_alternative_line` renders `alt.team_acquisition_value` — the very quantity
whose two-surface disagreement the entry recounts — through
`design_system.figure(...)` **directly**, not through `_figure`. It is a real Python render site,
behaviourally correct, and outside the counted 8. So "The Python render sites" is 9; the
enumerator reports 8 and calls it that population.

**Nothing else covers the gap.** The entry's `pinned_by` tests
(`test_216_room_integrity.TheDisplayRoundingRuleTests`,
`test_display_contract_boundary`) check that `design_system.figure` *is* the browser's rule and
that named quantities appear among `_figure`'s arguments. Neither scans for a render site that
bypasses it. `test_invariant_registry` checks that each `population` sentence is longer than 80
characters — not that the enumerator ranges over what the sentence says.

**Why it matters.** The v4 pass recorded, under what it checked and found clean:
*"`invariant_registry`'s nine censuses all match observed and its enumerators are derived, not
hand-listed."* Both halves are true and the guard still cannot fire for its own stated event.

### 1b. SUSPECTED — two sibling enumerators have the same shape

Same instrument, same inversion, not demonstrated:

* `_take_model_consumers` (census 4) counts call sites of `_take_probability` /
  `_board_take_probability`. Its docstring: *"A THIRD consumer is the event to catch. Each one
  either goes through this model or **reimplements it**."* A consumer that reimplements the model
  — which is precisely what `positional_forfeits` did, and what the entry exists to remember —
  adds no call site and moves no census.
* `_vendor_record_resolutions` (census 3) counts call sites of `_merge_across_eligibility`.
  *"A fourth resolution site is the event to catch — each one either honours the refusal or
  quietly reopens it."* A path that resolves a player onto a vendor record without calling that
  function is invisible.

`_surfaces_consulting_the_withholding_policy` (census 11) has the identical construction and
**states the limit in its own docstring** ("It cannot, by construction, see a surface that never
asks at all") — which is why it is not a finding, and is the model the other three should follow.

---

## 2. PROVED — `prose_names.misquoted_constants` still shields on the whole BLOCK; D-F2's paragraph-scoping repair reached one of the module's two checks

**Instrument** `prose_names.py` · **identifiers** `misquoted_constants` (block-scoped) vs
`dead_names` (paragraph-scoped).

**What it claims.** The module's own repair note, in a comment carried between the two functions:

> "PARAGRAPH-SCOPED, NOT BLOCK-SCOPED (D-F2). The rule this module states is 'the name exists, or
> the prose says IT is history' — and 'it' is the name, **so the shield must sit near the name**.
> Applied to the whole block, what the code implemented was 'the block contains a common English
> past-tense word' … The 45% over-shielding was almost entirely DOCSTRINGS, where one 'was' in the
> opening line covered every name in forty lines of unrelated text."

**What it does.** `dead_names` was repaired — it calls
`is_history(_paragraph_around(text, match.start()))`. `misquoted_constants`, four lines further
down the same file, still opens with `if is_history(text): continue` over the entire block. The
argument in that comment is about the distance between a shield and the thing it shields, and a
quoted value is as much "the thing" as a quoted name.

**The demonstration.** `probes/decisive_tests.sh` arm A. The break: a real docstring quotation
is made to state a value the code does not have.

```
--- BREAK 1: the SHIELDED site ---
  test_a_flex_slot_is_not_an_unlimited_bench.py docstring:
  "`FLEX_GROUP_DEPTH_FACTOR` is 3.0"  ->  "`FLEX_GROUP_DEPTH_FACTOR` is 9.0"
  (draft_room.FLEX_GROUP_DEPTH_FACTOR is still 3.0)

0 constant value(s) quoted wrongly, over 112 single-homed constants, ...
exit=0
misquoted_constants reports: NOTHING
```

The control, the same break at a site whose block carries no marker:

```
--- BREAK 2 (the control): the SAME break at an UNSHIELDED site ---
UNSHIELDED site broken: draft_battery.py:135
  'UPSIDE_MODE_DEFAULT_ROUND (15)' -> 'UPSIDE_MODE_DEFAULT_ROUND (99999.0)'

draft_battery.py:135   UPSIDE_MODE_DEFAULT_ROUND is 15.0 but the prose says 99999.0
1 constant value(s) quoted wrongly, ...
exit=1
```

Same instrument, same kind of lie, one reported and one not — the difference being a word in a
different paragraph of the same docstring.

**Size, measured** (`probes/probe_prose_names_scope.py`):

| corpus | blocks | quotations of a single-homed constant | shielded by the block-wide marker | marker also in the OWN paragraph | **marker only ELSEWHERE in the block** |
|---|---:|---:|---:|---:|---:|
| Python comments + docstrings | 18,347 | 30 | 19 | 15 | **4** |
| markdown paragraphs | 14,973 | 118 | 75 | 75 | 0 |

Markdown is unaffected because `markdown_blocks()` already emits paragraphs, and comments are
already line-scoped — exactly as D-F2 found: the over-shielding is a docstring phenomenon. The
four live sites currently unexaminable are `run_216_flex_share_probe.py`
(`SUPER_FLEX_QB_SHARE = 0.85`), `run_risk_adj_experiment_D_comparison.py` (`D_MIN_SCALE = 0.3`),
`test_a_flex_slot_is_not_an_unlimited_bench.py` (`FLEX_GROUP_DEPTH_FACTOR` is 3.0) and
`test_pool_gauge.py` (`SPAN = 16`). All four agree with the code today.

**Secondary, same instrument: the printed denominators are not the checkable population.**
The summary line reads:

```
0 constant value(s) quoted wrongly, over 112 single-homed constants, read from
18347 comments and docstrings and 14973 markdown paragraphs
```

The number actually compared is **148 quotations, of which 54 survive the shield**. 112, 18,347
and 14,973 are the sizes of the things *searched*, and a reader counting "0 over 18,347" is
reading a rate whose denominator is 340× the population under test. The module's own docstring
has the honest figures ("Python prose offers 6 quotations of a known constant to check, the
markdown offers 40") — which are themselves now stale against the measured 30 and 118 — so the
accurate number exists and is not the one printed.

---

## 3. PROVED — `assertion_execution --check` returns the same green line whether 359 tests were measured or none were

**Instrument** `assertion_execution.py` · **identifier** `main`, the `args.check` branch.

**What it claims.** `"--check"  fail if the count grew`. Its docstring: *"WHAT IT DELIBERATELY
DOES NOT CALL A DEFECT: … a test that errored — **the error is the finding**."*

**What it does.** The check branch reads the record, computes
`grew = set(silent) - set(recorded)` and `unexplained`, and if both are empty prints a success
line. `_BROKEN` and `_RAN` are populated by `_Result` and **never consulted in this branch**. A
test that errored contributes to neither `silent` nor `grew`, so the "finding" the docstring
promises is not reported, not counted, and not visible in the exit code.

**The demonstration.** `pandas` and `numpy` were made unimportable by a shim on `PYTHONPATH`
(no file in the tree touched), over five full-tier modules:

```
=== REAL ENV ===
0 of 359 tests that ran executed no assertion (1 skipped, 0 errored)
no new silent tests (0 known, each with a reason)
check exit=0

=== SHIM (pandas/numpy unimportable) ===
0 of 5 tests that ran executed no assertion (0 skipped, 5 errored)
no new silent tests (0 known, each with a reason)
check exit=0
```

359 tests measured and 0 tests measured produce **byte-identical output and the same exit code**.

**And the one number the line does print is mislabelled.** `(0 known, each with a reason)` is
`len(silent)` — the count found in *this* run — under the word "known".
`ASSERTION_EXECUTION.json` holds **14** entries. So the parenthetical reads as a statement about
the record's size and is a statement about the current run's hit count; at full scope it prints
18 and at `--only`-scope it prints 0, for the same record.

**Its sibling closed exactly this hole and said so.** `assertion_floors.main`:

> "AN INTEGRITY CHECK HOLDING NOTHING MUST NOT REPORT SUCCESS. … it meant `--check` printed 'no
> guarantee has shrunk (0 modules held to a floor)' and exited 0 over an empty file and an empty
> tree. Green, holding nothing."

and prints `len(recorded)` — "no guarantee has shrunk (230 modules held to a floor)".
`assertion_execution` has the `return 2` for a missing/damaged record but no floor on the
population it actually swept, and no mention of errors.

**Mitigating:** `assertion_execution --check` is **not** in `.github/workflows/tests.yml` (CI
runs `baseline_manifest`, `assertion_floors` and `render_trace`). The blast radius is a human
running it, which is also how its predecessor defect lived unnoticed for its whole life.

### 3b. PROVED — the first full-tier sweep of this instrument finds four silent tests its record does not hold

The v4 pass recorded this under what it *could not reach*: *"the full tier for
`assertion_execution` (D ran the fast tier, 2582 tests)". Run here over every `test_*.py`:

```
18 of 4128 tests that ran executed no assertion (2 skipped, 0 errored)
```

against a record of **14**. The four the record does not hold, all in full-tier modules — which
is why a fast-tier sweep could not see them:

| test | why it asserts nothing |
|---|---|
| `test_a_roster_the_solver_never_saw_whole.OnRealDataItMovesNoPriceTests.test_the_cells_that_WERE_measured_carried_a_false_label_at_no_point` | its only assertion sits behind `if before["basis"] != EXPOSURE_MEASURED: continue`, and that subpopulation is **empty**. Measured (`probes/probe_silent_tests_why.py`): 31 relabelled cells, previous basis `{'no_surplus': 27, 'vacant': 4}`, **`measured`: 0**. The registered invariant for `EXPOSURE_ROSTER_PARTIAL` states its evidence as *"32 cells relabelled, 26 from `no_surplus` and 4 from `vacant` … and **2 from `measured`**, which withdraws an over-credit of 2.16 and 1.44"* — this is the test that pins those two, it has never examined one, and the census behind the registry's own sentence does not reproduce on this fixture either (31/27/4/0 against 32/26/4/2). Its sibling `test_no_relabelled_cell_ends_up_in_a_state_that_still_claims_a_measurement` is not silent, so the fixture does produce relabelled cells; it produces none of **this** kind. |
| `test_a_source_that_vanishes_says_so.ThePlayerCacheRefusesABodyItCannotBe.test_a_poisoned_body_is_never_written_to_the_cache` | the `assertNotIn` is inside `if cache.exists():`, and the cache file is never created — so "an error-shaped body was cached for 24 hours" has never been checked. The class's other arm (`test_a_good_body_IS_written`) is the non-vacuity guard for caching *working*, not for the refusal. This is precisely the case `assertion_floors` names as outside its reach: *"an assertion moved behind a condition that never holds"*. |
| `test_one_eligibility_reader.TheCaptureIsWhereThisWasMeasuredTests.test_no_row_carries_a_slot_no_league_here_has` | legitimate — a `self.fail` sweep over a non-empty population (the capture) that found nothing. Needs a reason in the record, like the recorded `test_no_scenario_raises` entries. |
| `test_one_percentile_pair_one_conversion_rate.TheFlatRegionHasAStatedConventionTests.test_an_absent_projection_does_not_jump_the_queue` | a `self.fail` gated on a tied block containing an absent projection. Its **sibling** `test_player_id_remains_the_floor_under_the_convention` carries an explicit `self.assertGreater(checked, 0, "…so the floor beneath the convention is untested")`; this one has no such floor, so it cannot tell "no violation" from "no block to look at". |

So the ratchet's baseline was written from a partial sweep, and `--check` at full scope is
currently red with four entries awaiting a judgement. Two of the four are real untested
contracts, not false positives.

---

## 4. PROVED (known defect, confirmed live, with its downstream consequence measured) — `run_vds_battery`'s noise-arm exclusion reads a key no arm carries, and every entry in the report's headline field is the arm it was meant to drop

**Instrument** `run_vds_battery.py` · **identifier** `_report`, the `STRATEGY_SPECIFIC_FINDINGS`
block.

This is the fifth defect named in this review's brief. It is **still on disk**, and what it is
currently producing had not been measured, so it is recorded here with that measurement.

**What it claims.**

> "Also skipped: arms whose `sharp_seats` is empty. `noisy_k3`/`noisy_k8` contain no engine seat
> at all, so a finding there is a property of uniform random draws and belongs on no strategy's
> ledger."

**What it does.** `not row.get("sharp_seats", ["present"])`. `sharp_seats` lives at
`opponent_noise.sharp_seats` inside `vds_battery.STRATEGIES`; the arm row that
`draft_battery.run_battery` produces carries **neither spelling**, so the default is returned,
the default is truthy, and the condition is always False.

**The demonstration** (`probes/probe_vds_sharp_seats_guard.py`) rebuilds the last committed VDS
report from **its own serialized arms** with today's `_report`:

```
arms: 36
keys on an arm row: ['carried_forward', 'findings', 'format', 'label', 'margins',
  'pick_sequence', 'picks', 'produced_at_commit', 'qualifiers', 'regimes', 'rosters',
  'rounds', 'seconds', 'shape', 'strategy', 'strength', 'teams', 'unpriced_at_decision']
rows carrying a top-level 'sharp_seats': 0 of 36
rows carrying 'opponent_noise'        : 0 of 36

STRATEGY_SPECIFIC_FINDINGS : {'12T_ppr_K_DEF': ['noisy_k8'], '12T_ppr_SF': ['noisy_k8'],
                              '4WR_TE_PREMIUM': ['noisy_k8'], '12T_ppr': ['noisy_k8']}

strategies the comment says must be excluded (sharp_seats == []): ['noisy_k3', 'noisy_k8']
strategies STRATEGY_SPECIFIC_FINDINGS actually lists             : ['noisy_k8']
   -> EXCLUSION DID NOT FIRE

same arms, with a top-level sharp_seats copied in from STRATEGIES:
   STRATEGY_SPECIFIC_FINDINGS : {}
```

**4 of 4** entries in the field the report's own `_comment` calls *"what this exists for — the
shape `#22` had"* are `noisy_k8`, the one strategy the exclusion was written to drop. With the
key present the field is empty. The battery's headline product is, as it stands, entirely the
guard not firing.

---

## 5. PROVED — `test_ui_source`'s app.py-read guard carries the module-wide escape that D-F5's repair removed from its twin

**Instrument** `test_ui_source.py` · **identifier**
`NoTestReadsAppPyDirectlyTests.test_no_test_module_reads_app_py_off_disk`.

**What it claims.** *"The guard that keeps the migration from rotting. Twenty-two modules were
moved onto ui_source in one pass. Nothing stops the twenty-third from being written the old way
— `(_HERE / "app.py").read_text()` is still the obvious thing to type, and it would work
perfectly until the day a view moves."*

**What it does.**

```python
if ('"app.py"' in code or "'app.py'" in code) and "ui_source" not in code:
    offenders.append(path.name)
```

The second clause is a module-wide escape: **any** module that mentions `ui_source` anywhere in
its code is skipped whole, including for a direct `app.py` read elsewhere in the same file. D-F5
was the identical construct (`or "CAPTURE_PATH" in src`) in the hand-written-capture-path guard,
and the repair's own comment states the cost: *"ANY module that mentioned the constant anywhere
was skipped whole … so the one real offender was the one module the guard refused to look at,
and it reported zero."* That guard was repaired. This one was not.

**The demonstration.** `probes/decisive_tests.sh` arm C plants the same direct read twice:

```
--- baseline ---                                                      OK
--- BREAK: plant a direct app.py read in a module that ALSO imports ui_source ---
    test_positional_depth_coverage.py += _V4_APP.read_text(...)       OK      <-- not reported
--- CONTROL: the same plant in a module that does NOT mention ui_source ---
    test_bye_collision.py           += _V4_APP.read_text(...)         FAILED (failures=1)
```

**Reach** (`probes/probe_ui_source_guard_escape.py`): **52 of 230** test modules mention
`ui_source` in code and are therefore exempted whole, against **2** named exemptions in
`ALLOWED` (each of which does carry a stated reason — that part of the design is sound).

**No live offender hides there today.** The three modules that name `app.py` in code without
being in `ALLOWED` — `test_live_board_pricing.py`, `test_positional_depth_coverage.py`,
`test_rulings_are_not_silently_dropped.py` — were each read, and all three go through
`ui_source` correctly. So this is latent, which is the only reason it is fifth and not first.
It is latent in the instrument whose entire subject is a guard that keeps passing after losing
its subject.

---

## 6. PROVED — the CI workflow's own header carries the stale tier numbers that `suite_taxonomy` removed from itself

**Instrument** `suite_taxonomy.py` (clean) · **the defect is in** `.github/workflows/tests.yml`,
the file that invokes it.

`suite_taxonomy`'s docstring records why it grew `tier_census()`:

> "`tier_census()` below reports the live counts so no number in this prose can rot again; the
> docstring used to carry '53 fast modules, 845 tests, 1.5 seconds' against a reality of ~124 and
> ~205s."

The number was removed from the docstring. It survives, to the digit, in the workflow header:

```
#   fast  53 modules / 845 tests / ~1.5s   -- every push and PR
#   full  80 modules / 1548 tests / ~17m   -- every PR, and on demand
```

Measured now, from `suite_taxonomy` itself plus an AST count of `def test*`:

| tier | header claims | actual |
|---|---|---|
| fast | 53 modules / 845 tests / ~1.5s | **163 modules / 2,630 tests** (`suite_taxonomy`'s own docstring: ~205s) |
| full | 80 modules / 1,548 tests / ~17m | **67 modules / 1,490 tests** |

Both module counts are wrong, in opposite directions, and the cost figure that justifies the
split's whole design ("17 minutes is not worth spending to learn something 1.5 seconds already
knew") is off by two orders of magnitude on the fast side. This is `#133` — where prose and code
differ, the prose is the defect — in the one file a contributor reads to find out what CI does.
`#126`'s remedy is available and already built: the header could cite `tier_census()`, or the
workflow could print it.

---

# Instruments that came back clean, and what was done to establish it

These are not "read and looked fine". Each was broken.

**`assertion_floors.py` — SOUND.** The netted-out substitution D-F4 reopened is now caught at
the per-method level. Break: weaken the first `self.assertEqual` in `test_bye_collision.py` to
`assertIsNotNone` **and** add an `assertEqual` back in a new class in the same module, so every
module-level count is unchanged.

```
--- baseline ---  no guarantee has shrunk (230 modules held to a floor)
--- BREAK ---     A guarantee got smaller. …
  test_bye_collision.py: ValueLostNotBodiesLostTests.test_a_covered_absence_costs_nothing
                         self.assertEqual 3 -> 2
assertion_floors exit=1
```

It names the class, the method and both sides. Coverage checked independently: **230 of 230**
test modules on disk carry a floor, none floored-but-absent, and **4,093 of 4,120** test methods
carry a per-method floor — the 27 without one being exactly the documented count of methods with
no `self.assert*` in their own body. The damaged-record vacuity is closed and says so out loud.
Its `--check` prints `len(recorded)`, which is the number a reader needs.

**`render_trace.py --check` — SOUND.** 862 calls across 6 passes, population printed. Break: one
`st.caption("v4 probe")` as the first statement of the Matchup view.

```
--- baseline ---  render trace unchanged (862 calls)
--- BREAK ---     render trace CHANGED (862 -> 863 calls):  [unified diff follows]
render_trace exit=1
```

The seeding (`_seeded_session`) is the part that could go vacuous and it is heavily defended:
rosters, starters, a client whose `get_players`/`get_drafts` are stubbed so no pass depends on
network, seeded live picks with a **fixed** fetch stamp, and a mid-draft mock. Calendar-derived
strings are blurred through an explicit list rather than dropped, so removing a freshness strip
is still a diff. The two things it cannot see — anything behind a widget that returns an
interactive value, and any string over 60 characters — are both stated in the docstring.

**`doc_index.py` — SOUND, and one suspected hazard measured to zero.** 235 documents, derived
from `git ls-files`, counts printed per bucket, `--check` wired into
`test_doc_index.test_doc_index_is_not_stale`. The hazard: `classify` calls
`_without_boilerplate(header(path))`, and `header` truncates to `HEADER_LINES = 12` **first** —
so a document carrying the house banner spends part of its budget on the banner, while `body()`
exists specifically because *"frontmatter also eats most of the header budget"*. Measured
(`probes/probe_doc_index_header_budget.py`): 6 documents carry the banner, and reversing the two
steps moves **0** documents in either direction. Latent, not live. Reported as a non-finding.

**`suite_taxonomy.py` — SOUND.** 230 modules, 163 fast / 67 full, 0 resolving to neither, 160
distinct contract markers — all printed. Tier detection is an AST walk, not a substring. The
`_UNMARKED` exemption table (question 5) is guarded on both sides:
`test_the_unmarked_table_carries_no_dead_rows` and
`test_the_unmarked_table_holds_only_modules_that_need_it`, plus tier-collapse floors
(`fast > 20`, `full > 10`) and a non-empty-suite floor. The one thing it cannot see — a fast-tier
module that is slow for a reason other than `DataMerger` — is stated in the docstring with the
measurement behind it.

**`invariant_registry.py` — the census machinery is SOUND; the defect is in one enumerator
(finding 1).** All nine populations are non-empty and printed (3, 178, 9, 31, 5, 8, 11, 4, 3);
the ratchet is pinned in both directions (`test_a_grown_population_fails`,
`test_a_SHRUNK_population_fails_too`), an enumerator that cannot run is a finding rather than a
pass (demonstrated by this container's own missing-pandas start, which produced five `ERROR` rows
and exit 1), and `main` returns 1 on any move. Six of the nine enumerators derive their
population from the thing under test itself (`TEAM_SPECIFIC_TERMS`, `board_emitted_columns()`,
`EXPOSURE_BASIS_LABELS`, `FANTASY_POSITIONS`, the capture) and are sound.

**`run_draft_battery.py`'s report builder — SOUND.** The exercise flags the
`engine-measurement` skill says to grep for are present **and true** in the committed
`BATTERY_REPORT.json`: `streaming_floor_exercised = True`, `weekly_projection_weeks = 18`,
`priced_from = vendor+sleeper`, `sleeper_basis = season_sum`, with
`season_projections_supplied = 5346` travelling beside
`season_projections_priceable = 840` so the 6.4× coverage overstatement cannot recur.
`constant_axes` is `[]` and `te_premium` now varies 47/6, so `#241`'s flattened axis is really
open. `duplicate_arms` excludes `label`, `seconds`, `produced_at_commit` and `carried_forward`
from the fingerprint — the first because including it made the check vacuous, the latter two
because a resumed run is a join across processes — and `format_axes_exercised` prefers what each
arm RECORDED over what the matrix says now and names the disagreement
(`arms_whose_league_changed_under_the_same_label`) instead of resolving it. 53 formats, 53
independent, 9,336 picks, 2 findings.

**`test_ui_source.py` beyond finding 5 — SOUND, and unusually well built.** `SilentVacuityTests`
demonstrates the defect rather than asserting it (it runs the old reading and shows it passing on
nothing). Every scan has an explicit non-vacuity arm: the Streamlit-call scan has
`test_the_scan_can_actually_see_a_streamlit_call` (`> 100` hits in `app.py`), the real-split
simulation has `test_the_seam_this_simulation_uses_still_exists` (`carved > 2000` chars) and
`test_the_suite_really_does_assert_against_the_surface` (`> 40` needles), and the control for
the split deliberately does **not** go through `ui_source` because *"an instrument that shares
code with its subject has stopped being an instrument."* The `TheDerivationRulesPremiseTests`
class enforces the limitation `ui_source`'s docstring merely states.

**`invariant_confirmation.py` — read only, not run** (another session holds it; it writes a
broken `draft_room.py` to disk). The two inert arms named in the brief are addressed by a fixture
guard that now checks **four** quantities — feasibility and fieldability censuses on *both* the
balanced and upside boards — and refuses to run (`return 2`) rather than relaxing, with the
reasoning for each widening recorded. The baseline arm, the anchors self-test on the clean tree,
and the mutant-must-change-the-fingerprint rule are all present. One cosmetic note, not a
finding: the line printed after that guard loop (`reference board: {_digest[:16]} feasibility
binds on {feas} of {total} rows`) uses the loop variables as they were left by the **last**
iteration, so it describes the **upside** board under the label "reference board".

---

# What this review did not reach

* **`invariant_confirmation`'s end-to-end run** — excluded by the brief; another session holds
  it. Read only.
* **The `1b` siblings** (`_take_model_consumers`, `_vendor_record_resolutions`) are argued from
  code, not demonstrated. Demonstrating them needs a second consumer that reimplements the model
  — writing one proves the enumerator blind but proves nothing about today's tree, which is why
  they are labelled SUSPECTED.
* **A full `--check` sweep of `assertion_execution` under a broken environment.** The full sweep
  under the import shim produced one *false* finding
  (`test_harness_league_format_hygiene…test_every_known_harness_module_requires_a_merger_argument`
  goes silent when the modules it iterates cannot be imported) and exited 1 — loud but wrong,
  which is a different failure from the silent-green one proved at five-module scope. Both are
  the same root cause: the branch never looks at `_BROKEN`.
* **`run_vds_battery` end to end.** Finding 4 is measured against the last committed run's own
  serialized arms rather than a fresh 36-arm run (hours).

# Housekeeping

`DOC_INDEX.md` is regenerated in the commit that adds this document, because adding a tracked
`.md` makes the index stale and `test_doc_index.test_doc_index_is_not_stale` reads it. That is
`doc_index`'s own note working as designed: *"a brand-new document is INVISIBLE HERE UNTIL IT IS
STAGED … Regenerate AFTER `git add`, not before."*
