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
| `test_one_percentile_pair_one_conversion_rate.TheFlatRegionHasAStatedConventionTests.test_an_absent_projection_does_not_jump_the_queue` | a `self.fail` gated on a tied block containing an absent projection. Measured: **98 tied blocks across the boards, 0 of them holding an absent value** — so the sweep is real and the gated subpopulation is empty. Legitimate today; needs a reason in the record, and the asymmetry is worth noting: its **sibling** `test_player_id_remains_the_floor_under_the_convention` carries an explicit `self.assertGreater(checked, 0, "…so the floor beneath the convention is untested")`, while this one has no such floor and so cannot tell "no violation" from "no block to look at". |

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
* **Arms B and C of the silent-test why-probe.** `test_a_poisoned_body_is_never_written_to_the_cache`'s gate is `cache.exists()` and `test_no_row_carries_a_slot_no_league_here_has`'s is a clean sweep — both read from source rather than instrumented, because neither needs a board build to be unambiguous. Arms A and D were measured.
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

---

# ADDENDUM — the two battery report builders, gone after harder

A second pass over `run_draft_battery._battery_report` and `run_vds_battery._report` alone,
field by field, asking of each: can it fire, is its denominator the population under test, does
it mean its name, and does the guard policing it see the shape production produces. Probes:
`probes/probe_battery_duplicate_arms.py`, `probes/probe_battery_report_builder.py`,
`probes/probe_vds_report_builder.py`.

The common root is one change. `audit_trajectory` was repaired to copy the trajectory's whole
config onto each arm as **`provenance`** (mode, pool_scope, opponent_noise, sleeper_basis,
priced_from, upside_rule, upside_from_round, picks_by_mode, pick_order) — the right repair, for
the right reason. Three of the findings below are what that key did on arrival, and two are
fields that still quote a module constant while the per-arm truth now sits on the row.

## A1. PROVED — `duplicate_arms` lost its only live finding when `provenance` joined the arm row, and `BATTERY_REPORT.json` publishes `independent_formats: 53` where the answer is 52

**Instrument** `draft_battery.duplicate_arms` + `_FINGERPRINT_EXCLUDES`, consumed by
`run_draft_battery._battery_report`.

**What it claims.** *"Arms of the matrix whose ENTIRE measured content is identical to another
arm's. … a report claiming N formats of coverage when some of them reproduce another arm byte
for byte … inflates the denominator under every rate this battery produces and makes a
duplicated finding look like independent corroboration."* `_FINGERPRINT_EXCLUDES` exists so a
field describing the **run** rather than the arm's content cannot make two identical arms
fingerprint apart — its comment records both occasions that was learned (`seconds`, then
`produced_at_commit`/`carried_forward`: *"they describe the RUN, not the arm's content"*).

**What it does.** `provenance` is a run descriptor by that same definition and is **not**
excluded.

**The demonstration.** In the committed report, `12T_ppr` and `12T_ppr_mode_balanced` share a
**byte-identical 112-pick sequence**, and:

```
12T_ppr vs 12T_ppr_mode_balanced: the ONLY keys that differ are ['label', 'provenance', 'seconds']
    provenance.mode:              'auto'  vs  'balanced'
    provenance.upside_from_round: 15      vs  None
```

`label` and `seconds` are already excluded. One process, one code version, toggling the single
thing under test:

```
as shipped   excludes=['carried_forward', 'label', 'produced_at_commit', 'seconds']
             duplicate_arms -> []
+ provenance excludes=[... 'provenance' ...]
             duplicate_arms -> [{'label': '12T_ppr_mode_balanced', 'duplicates': '12T_ppr'}]
restored     duplicate_arms -> []
```

**It is a regression, and the record shows the moment.** Every committed report before this one
flagged the pair:

| report | formats / independent | rows with `provenance` | duplicates |
|---|---|---:|---|
| 2026-09-08 vendor_only | 33 / 24 | 0/33 | 9 |
| 2026-09-08 scoring_aware | 33 / 32 | 0/33 | `12T_ppr_mode_balanced == 12T_ppr` |
| 2026-09-12 full | 33 / 32 | 0/33 | `12T_ppr_mode_balanced == 12T_ppr` |
| 2026-09-13 gate1 | 34 / 33 | 0/34 | `12T_ppr_mode_balanced == 12T_ppr` |
| 2026-09-17 gate1 | 34 / 33 | 0/34 | `12T_ppr_mode_balanced == 12T_ppr` |
| **current** | **53 / 53** | **53/53** | **[]** |

The detector's own docstring quotes the 2026-09-12 measurement as the evidence on which a
matrix-trim ruling was **reversed** (`#258`). That measurement can no longer be reproduced by
the instrument that made it.

**Why the guard did not catch it.** `test_report_fields_mean_their_names.DuplicateArmsSurvivesAResume`
is the test written for this exact field, and it hand-builds a **five-key** arm —
`{label, seconds, findings, teams, shape}` — against a real row of **eighteen**. No case in it
carries `provenance`, so both behavioural cases pass whatever `provenance` does:

```
DuplicateArmsSurvivesAResume: ran=3 failures=0 errors=0
...while duplicate_arms over the real 53 rows -> []
```

Its third case, `test_the_run_stamps_are_excluded_from_the_fingerprint`, asserts a **hand-list**
of four field names are in the frozenset. That is `#126` turned on the tooling: "which fields
describe the run" is derivable (they are the keys `audit_trajectory` adds that are not
measurements, plus the two `main` stamps on), and it is typed by hand instead — so a fifth run
descriptor arrives and nothing fails.

## A2. PROVED — `picks_by_mode` is recorded on every arm and read by nothing, and half the `auto` arms never entered the upside branch

**Instrument** `run_draft_battery._battery_report` (the field it does not aggregate) and the
console summary.

`simulate_full_draft` records `picks_by_mode` deliberately: *"WHICH VALUATION produced each
pick, for the same reason priced_from exists (`#222`). mode='auto' is not one valuation:
compute_draft_board's upside branch zeroes every team-specific term, so a trajectory can be half
roster-aware and half roster-blind with nothing in the record saying so."*

Measured on the committed 53-arm run:

```
picks across the run: balanced=8664  upside=672   (report `picks`=9336)
upside share: 7.2%
arms with ANY upside pick: 18 of 53

arms running mode='auto' (the SHIPPED default): 34
of those, arms that made ZERO upside picks     : 17
```

All seventeen for one structural reason — the draft is shorter than the rule's trigger:

```
8T_standard  10T_ppr  12T_ppr  14T_ppr  12T_ppr_TEP_dynasty  12T_ppr_redraft
12T_ppr_TEP_redraft  LIGHT_IDP  … rounds=14, upside_from_round=15  -> unreachable
12T_ppr_SHORT_DRAFT                rounds=8,  upside_from_round=15  -> unreachable
```

`vds_battery.FORMATS` already states this property, for one arm: *"`12T_ppr_SHORT_DRAFT`: 8
rounds, so the round-triggered upside rule NEVER fires."* It holds for every 14-round arm in the
format matrix, which is half the `auto` population, and **no field of the report says so**:

```
report builders that read `picks_by_mode`: NONE
```

This is the `streaming_floor_exercised: false` shape — *"a flag nobody checks is a comment"* —
with the flag correctly written and never aggregated, never printed, never asserted. The one
test that touches `picks_by_mode` checks the **function** (`ds._picks_by_mode`) against the
engine's boundary; nothing reads it across a report.

It is also the mechanism behind A1: `12T_ppr` is a 14-round `auto` arm, so `auto` **is**
`balanced` there, which is why its draft is byte-identical to `12T_ppr_mode_balanced`.

## A3. PROVED — `constant_axes` is structurally blind to the axes `provenance` records, and two of them are constant across all 53 arms

`format_axes_exercised`'s `constant_axes` is `#241`'s repair, and its lesson was *"an axis that
fails to vary is also a coverage hole … a constant axis should announce itself the way a
duplicate arm does."* It ranges over `advertised_format_axes(league)` =
`league_format_hint(league)` + `roster_shape_axes(league)` — **purely league-derived**. The
per-arm parameters `run_battery` forwards are not among them:

```
constant_axes = []   axes_source=arms  arms=53
axes it ranges over (9): draftable_rounds has_defense has_idp_slot has_kicker
                         has_superflex_slot scoring starting_slots superflex te_premium

provenance.mode               {'auto': 34, 'balanced': 18, 'upside': 1}
provenance.upside_rule        {'round': 53}            <-- CONSTANT across every arm
provenance.opponent_noise     {'None': 53}             <-- CONSTANT across every arm
provenance.pool_scope         {'all': 53}              <-- CONSTANT across every arm
provenance.priced_from        {'vendor+sleeper': 53}   <-- CONSTANT (correct, and disclosed in `universe`)
provenance.sleeper_basis      {'season_sum': 53}       <-- CONSTANT (same)
provenance.upside_from_round  {'15': 34, 'None': 18, '1': 1}
```

`upside_rule` and `opponent_noise` are real strategy axes the arm loop forwards and the VDS
battery sweeps; in the format battery they never vary, and the detector built to announce a
constant axis reports `[]`. The data to derive this is on every row — the distribution above was
computed from `provenance` alone.

## A4. PROVED — `formats` and `independent_formats` are arm counts; the run has 53 arms over 34 distinct leagues

```
console: "53 formats (53 independent), 9336 picks, 2 structural findings"

arms in the matrix        : 53
DISTINCT leagues in it    : 34
arms sharing a league with another arm: 36 in 18 groups
    ['12T_ppr', '12T_ppr_mode_balanced', '12T_ppr_mode_upside']
    ['8T_ppr_SF', '8T_ppr_SF_balanced_full']   … (18 groups in all)
```

`_battery_report`'s comment is accurate — *"`formats` is how many arms RAN"* — but the field
name and the console line both read "formats", and that number is the denominator under every
rate the battery produces. A reader taking "53 formats" at face value overstates format coverage
by 56%. The repository already has a module for exactly this (`#222`'s
`test_report_fields_mean_their_names`, *"eight report fields whose values were not the quantity
their names promised"*); `formats` is a ninth and is not in it. Severity: low — the number is
right for what it counts, the name is the defect (`#133`).

## A5. PROVED — `run_vds_battery` reports the absence of a control as the presence of an effect

**Instrument** `run_vds_battery._report`, the `inert` / `controls` block, and `main`'s console
branch.

`controls` is keyed off each format's control arm. A format with no control arm in `results` is
`continue`d, so no arm in it can be judged inert — and `main` then prints the positive claim:

```python
else:
    print("\nNo inert arms: every strategy changed the draft in every format.")
```

Demonstrated on the committed run's own 36 arms:

```
all 36 arms          INERT_ARMS = ['12T_ppr_SHORT_DRAFT__crossing',
                                   '12T_ppr_SHORT_DRAFT__sharp_balanced',
                                   '12T_ppr__crossing', '12T_ppr__sharp_balanced']
                     inert_arm_count=4  effective_arms=32

the SAME arms, controls dropped (30 arms, which still CONTAIN all four inert arms):
                     INERT_ARMS = []
                     inert_arm_count=0  effective_arms=30
-> main() would print: "No inert arms: every strategy changed the draft in every format."
```

The four arms the full run proves inert are still in that set. `--only` is a documented mode
(*"a deliberate partial run to its own file"*) and nothing stops it naming non-control arms; the
same holds for any `results` set a control is missing from. The function went to real trouble to
fix the *denominator* for partial runs (`per_format_ran` replacing `len(STRATEGIES)`, with its
own comment about the mid-run file being *"what a reader usually holds"*) and then let the inert
detector answer "none" where the honest answer is "not determinable for these formats".

Same shape, same block, one level down: with `format`/`strategy` stripped from the rows — the
shape a `--resume` carries from any report written before `audit_trajectory` stamped them — the
label-based readers keep working and the inert detector goes silent:

```
INERT_ARMS                 = []
findings_by_strategy keys  = [crossing, noisy_k3, noisy_k8, sharp_auto, sharp_balanced, sharp_upside]
STRATEGY_SPECIFIC_FINDINGS = {'12T_ppr_K_DEF': ['noisy_k8'], … }
```

Two readers of "which strategy is this arm" inside one function: `inert` reads
`row["strategy"]`/`row["format"]`, every findings block reads `row["label"].partition("__")`.
They agree on today's rows (checked: 0 disagreements) and fail differently when one source is
absent — which is `ONE_QUESTION_TWO_READERS.md`'s class, inside a report builder repaired for a
finding of that class.

## A6. PROVED — `seed`, `top_k_swept`, `strategies` and `formats` in the VDS report describe the code, not the run

```
as shipped: seed=20260922  top_k_swept=[3, 8]
constants changed, THE SAME ARMS re-reported: seed=11111111  top_k_swept=[99, 100]
arms identical? True
```

`strategies` and `formats` are likewise `dict(vds_battery.STRATEGIES)` and
`dict(vds_battery.FORMATS)`. On a resumed run — the documented way a multi-hour battery finishes
— arms produced under an older table are described by today's. `commits_present` is the
disclosure and it is real; but the per-arm truth is now **on the row**:
`provenance.opponent_noise` carries each noisy arm's own `top_k`, `seed` and `sharp_seats`,
because `audit_trajectory` copies the whole config. The report quotes the module constants
instead. (The committed VDS run predates that repair — 0 of 36 rows carry `provenance` — so this
is a claim about the next run, not that one.)

## A7. PROVED (known defect, now also shown untested) — the `sharp_seats` exclusion has no test, and the key it needs is on the row

Finding 4 above established the exclusion cannot fire. Two further facts:

```
test modules mentioning `sharp_seats` at all: NONE
the strategies the exclusion exists for: ['noisy_k3', 'noisy_k8']
the guard's fixture strategies:          ['sharp_auto', 'sharp_upside', 'crossing']
```

`TheVDSReportDoesNotCreditInertArms` — the class written for this block — uses three
non-noisy strategies and a five-key arm, so no case in the suite reaches the noise branch. And
the value the guard wants now exists at `row["provenance"]["opponent_noise"]["sharp_seats"]`.
The data is one path away; the guard reads a top-level key that has never existed.

## What the two builders got right, established the same way

* **The resume join.** `commit`, `commits_present` and `carried_forward` are present in both
  reports under the same three names (`#126`), and `--only` with `--resume` is **refused** in
  both, with the reason stated — *"a resume that DESTROYS results is worse than no resume."*
* **`format_axes_exercised` prefers the arm over the matrix.** `axes_source: "arms"` on the
  committed run, with `arms_whose_league_changed_under_the_same_label: []` reported rather than
  resolved — the right shape, and the reason `12T_ppr_K_DEF` changing under a fixed label is now
  visible.
* **`run_draft_battery` refuses to run** on a rulebook that prices no player at a position with
  stat lines (`#213`), and `build_players_db` raises rather than letting the vendor
  reconstruction become the default (`#222`). Both are loud, both are the right direction.
* **`universe` carries the exercise flags and they are true** on the committed run:
  `streaming_floor_exercised=True`, `weekly_projection_weeks=18`,
  `priced_from=vendor+sleeper`, `sleeper_basis=season_sum`, and
  `season_projections_supplied=5346` travelling beside `season_projections_priceable=840` so the
  6.4× overstatement cannot recur.
* **VDS `findings_total` and `findings_total_effective` are both reported**, neither replacing
  the other, with the reason stated. `by_strategy_effective` is seeded with every strategy that
  ran at zero, because *"an absent key and a zero are different claims"* — the right instinct,
  and the one the console loop then drops by iterating `vds_battery.STRATEGIES` instead of
  `strategies_that_ran`, so a strategy that never ran prints `0` beside one that ran and found
  nothing.
