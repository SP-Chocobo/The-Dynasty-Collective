# Independent review of the v4 repair set

**Range reviewed:** `eac7491..7984b1d` (`git diff eac7491..HEAD -- '*.py'`), where `eac7491` is
the commit the `v3-freeze` tag dereferences to and `7984b1d` is the v4 freeze candidate.
32 Python files, +1538/−167.

**Stance.** Every docstring, comment, commit message and `evidence/` claim in the range was read
as a claim to be tested, not as information. Where a comment and the code disagree the comment is
reported as the defect (`#133`). Nothing was repaired — this is a review.

**Environment note.** The container had no project dependencies installed; `pip install -r
requirements.txt` was run first. Every probe below was run from the repository root with
`PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1` (the `.pyc` rule from `engine-measurement`).

Probes are committed under `evidence/blind_pass_v4/probes/` and are re-runnable.

---

## Findings, severity order

### 1. HIGH — `E-F5`'s new guard cannot fire on the way the season fetch actually fails

**File / identifier:** `sleeper_client.priceable_season_projections`

**What it claims.** The comment added in the range:

> A FAILED FETCH IS NOT AN ABSENT ONE (E-F5). When the season fetch fails outright the sync
> stores `season_projections = {}` and sets `coverage.error` — and `{} or None` is None, so this
> early return handed the caller no refusal string and the Draft Room rendered NO WARNING while
> the board was vendor-priced.

**What the code does.** The new branch is `if (coverage or {}).get("error"):`. `coverage.error`
is written in exactly one place: `sleeper_client.sync_league`'s `except Exception` around
`self.get_season_projections(...)`. But `get_season_projections` delegates to `_sum_weeks`, which
calls `get_weekly_projections` — and that method's own docstring says it **FAILS SOFT**: it
catches `SleeperAPIError` and returns `{}`. A failed week is appended to `weeks_failed` and the
loop continues. `_sum_weeks` then builds its coverage record, **which has no `error` key at
all** (`season`, `season_type`, `weeks_requested`, `weeks_answered`, `weeks_failed`, `players`,
`weeks_present_by_player`).

So for the ordinary outright failure — Sleeper unreachable, every week erroring — nothing raises,
`coverage["error"]` does not exist, `season_projections` is `{}` → `None`, and the new guard is
skipped. `priceable_season_projections` returns `(None, None)`: no refusal string, no warning,
vendor-priced board. That is the precise defect E-F5 claims to have closed, still reachable
through the sibling branch.

**Input on which they differ.** Any sync in which `_weekly_stat_lines` raises `SleeperAPIError`
for every week (connection failure, non-200, a 200 with an HTML body) rather than
`get_season_projections` itself raising.

**How established.** `evidence/blind_pass_v4/probes/probe_ef5_failed_fetch_is_silent.py`. The
coverage record is produced by `_sum_weeks` itself — not hand-built — by subclassing
`SleeperClient` so `_weekly_stat_lines` raises, then feeding the real `(totals, coverage)` pair
into the production consumer:

```
coverage keys          : ['players', 'season', 'season_type', 'weeks_answered',
                          'weeks_failed', 'weeks_present_by_player', 'weeks_requested']
coverage['error'] ?    : False -> None
weeks_failed (n)       : 18
season_sum_is_complete : False
priceable -> REFUSAL   : None
VERDICT: SILENT (no warning) -- E-F5 guard did not fire
```

The arm the comment describes (an exception out of the fetch, `error` hand-set) does warn, which
is what makes the repair look complete.

**Note on the test.** `test_a_partial_season_is_not_a_season.py` covers this with
`_coverage([], error="ConnectionError: x")` — a hand-built record carrying the key. The fixture
and the defect agree: the test passes whether or not the real producer ever writes that key. The
authority that *is* already correct for this state is `season_sum_is_complete(coverage)`, which
returns `False` for the fail-soft record; the guard was written against a key instead of against
that reader.

---

### 2. MEDIUM — the D10 ambiguity messages state a declared starting-slot count that is wrong whenever an unrecognised label repeats

**File / identifier:** `league_config.ambiguities`

**What it claims.** The `AMBIGUITY_UNKNOWN_SLOT_STARTER` detail tells the manager "the board was
priced on N starting slots where your league declares M"; the `AMBIGUITY_UNKNOWN_SLOT` detail
says "your league has **up to** M". The module docstring presents the bands as "THE MEASURED
IMPACT rather than a judgement about severity", and the loud band as saying "the bound is what is
missing rather than implying a size" — while in fact stating a bound.

**What the code does.** `unknown` is `sorted({slot for slot in slots if slot not in KNOWN_SLOTS})`
— a **set of distinct labels**. `M` is then computed as `parsed_starting + len(starters)` and
`parsed_starting + len(unresolved)`, i.e. distinct-label counts, while `slots` is a list that
preserves duplicates. A league declaring the same unrecognised starting label more than once is
under-reported by (occurrences − 1).

**Input on which they differ.** `roster_positions = [QB, RB, RB, WR, WR, TE, FLEX, K, DEF, BN,
BN, IR, "super-flex", "super-flex", "super-flex"]`. The solver parses 9 starting slots; the league
declares 12 (`league_config.starting_slots` over the list); the message says 10. Same for three
`WIZARD` slots: "has up to 10" where it has up to 12 — so the stated bound is not merely vague, it
is too tight, in the message whose stated purpose is to let the reader size the error.

**How established.** `evidence/blind_pass_v4/probes/probe_cf4_duplicate_unknown_slot.py`, which
compares the number in the rendered detail against `league_config.starting_slots` over the raw
roster list:

```
--- THREE occurrences of the same unrecognised STARTING label
    solver parsed   : 9
    league DECLARES : 12
    MESSAGE CLAIMS  : 10  ->  WRONG, understates by 2
--- THREE occurrences of the same unresolvable label
    MESSAGE CLAIMS  : 10  ->  WRONG, understates by 2
```

**Note on the test.** `test_a_warning_is_as_loud_as_its_consequence.
TheVolumeFollowsTheConsequenceTests.test_the_COUNT_matches_the_SOLVER_and_not_a_literal` is
written exactly as the repo's rule asks — the expectation is derived from
`lo.slots_from_roster_positions`, not from a literal — and it still passes, because every fixture
it iterates (`"Bn"`, `"super-flex"`, `"WIZARD"`) appends the unknown label **once**. It pins the
left-hand number (`parsed_starting`) against its authority and leaves the right-hand number
(`parsed_starting + len(...)`) unpinned against any authority at all. The fixture and the defect
agree.

---

### 3. HIGH — two repairs in this range converge on a false sentence to the chair: the engine *does* price IR and PUP

**Files / identifiers:** `pick_debate._format_candidate` (the new three-way health branch) ×
`draft_room.health_penalty` (the new `return 0.0`)

**What they claim.** `pick_debate`'s new comment: "THREE states, because there are three (`#187`):
already in the projection; charged on top; and **reported but deliberately not priced** — which a
chair instructed never to recompute cannot work out for itself". Its third branch renders:

> NO discount was applied for it — this engine does not price this designation, so his value
> below is the value of a fully fit player

**What the code does.** The branch is selected by `_charged = candidate.risk_adj is not None and
candidate.risk_adj != 0.0`, i.e. by `risk_adj == 0.0`. But `health_penalty` returns `0.0` from
**four** different returns, for four different reasons:

| | cause | is the designation priced? |
|---|---|---|
| A | `availability_basis == RULE_FLOOR` | yes — already inside the projection |
| B | `HEALTH_DISCOUNT_RATE.get(status) is None` | **no** — the only case the sentence describes |
| C | `projected_points` absent → **the new `return 0.0` made in this range** | **yes** |
| D | `rate * projected_points` where the projection is exactly `0.0` | **yes** |

A is caught by the first branch. B, C and D all fall through to the third, so the sentence asserts
"this engine does not price this designation" about designations the engine prices at
`-0.2353` of the projection.

**Input on which they differ.** The two rows `health_penalty`'s own comment names. On a HEAVY_IDP
board built without season projections, Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR, bpa
15.0) are priced on the trade-value fallback, so `_points` is NaN, so the new `return 0.0` fires
(cause C), so `risk_adj == 0.0`, so the chair is told the engine does not price PUP/IR:

```
  DeShon Elliott    IR    bpa=  15.0  risk_adj=0.0  basis=None
     HEALTH_DISCOUNT_RATE[IR] = -0.23529411764705882
     pick_debate says -> IR -- NO discount was applied for it -- this engine does not price
                         this designation, so his value below is the value of a fully fit player
  Harold Landry     PUP   bpa=   2.0  risk_adj=0.0  basis=None
     HEALTH_DISCOUNT_RATE[PUP] = -0.23529411764705882
     pick_debate says -> PUP -- NO discount was applied ... does not price this designation ...
```

Cause D reaches it on the ordinary offensive board too: 2 of 259 `health_penalty` calls on a
12T_ppr board (`IR`, projection exactly 0.0), and 2 of 481 with season projections.

Neither repair is wrong on its own. `health_penalty` returning 0.0 is right — measured below, it
restores `universal_value` and `final_score` on exactly the rows it names. The defect is that
`risk_adj == 0.0` is not a reader for "this designation is unpriced", and the sentence that reads
it as one was written in the same range. The authority that answers the question the sentence asks
is `HEALTH_DISCOUNT_RATE.get(status) is None` — derivable, one line away, and not consulted.

**How established.**
`evidence/blind_pass_v4/probes/probe_risk_adj_zero_has_four_causes.py` spies the production
`health_penalty` and tags every call by its arguments (never by call order), censusing the causes
of each 0.0 on both pricing arms;
`evidence/blind_pass_v4/probes/probe_cf3_eligibility_and_views.py` takes the two named rows' field
values **from the board** onto a `CandidateSnapshot` that `build_snapshot` itself produced, and
reports what the production formatter says about them.

---

### 4. LOW — `health_penalty`'s repair is sound, but its stated reach is not, and a contradicting claim is still live in the same file

**File / identifier:** `draft_room.health_penalty` (the new comment) and
`draft_room.compute_draft_board`'s `#112` absence-kind comment

**Verified sound first.** The repair does what it says. On HEAVY_IDP and LIGHT_IDP boards built
without season projections, the trade-value population is 62 rows, 8 of them carrying a
designation, and Harold Landry (PUP, bpa 2.0) and DeShon Elliott (IR, bpa 15.0) now emit
`universal_value` and `final_score` rather than NaN with `absence_kind` unset — the exact damage
the comment describes, repaired.

**What is overstated.** "reachable from any board built without season projections." It is not. The
population requires a league shape that gives the trade-value positions a replacement level.
Measured on a `build_mock_league(12T_ppr)` board built without season projections: the population
is **0 of 961 rows**, and the repaired branch fired **0 of 259** `health_penalty` calls. It fires
2 of 313 on HEAVY_IDP and LIGHT_IDP.

**And the wide version is still asserted elsewhere, in the opposite direction.**
`compute_draft_board`'s `#112` comment, ~2,500 lines earlier in the same file, says of that same
branch: *"the error was invisible on every board measured because that branch currently has zero
rows (0 of 1,119)"*. That reason is now false — 62 rows on two of the battery's own formats — and
it is the stated ground for a latent absence-contract breach being judged latent. The conclusion
there still holds (no `absence_kind` is assigned on that branch, confirmed: `absence_kind` is NaN
on all 62 rows); only its justification is stale. `#133`.

**How established.** `evidence/blind_pass_v4/probes/probe_a2_trade_value_branch_scope.py`, three
league shapes in one process, with `health_penalty` spied so the branch that fired is observed:

```
12T_ppr   : TRADE-VALUE POPULATION n = 0   branch census {B:251, E:6, D:2}
HEAVY_IDP : TRADE-VALUE POPULATION n = 62  branch census {B:311, E:6, D:2, C:2}
LIGHT_IDP : TRADE-VALUE POPULATION n = 62  branch census {B:311, E:6, D:2, C:2}
```

---

## Attacked and found sound

### `B-F4` — `feasibility_first` reads eligibility, and the repaired path is the one production takes

The repair keeps a `if "player_id" not in scored.columns:` fallback to the old primary-bucket
reading. If production never supplied `player_id`, the repair would be a guard that cannot fire.
It does supply it: spying the production `feasibility_first` across a `build_snapshot` on
HEAVY_IDP recorded **13 calls, every one with `player_id` present** on a 1,850-row frame. The
fallback is the test-only arm, as the comment says. (`probe_cf3_eligibility_and_views.py`.)

### `C-F3` — eligibility crosses the snapshot boundary, and the census is not uniform

A populated-but-uniform `eligible_positions` would make `filter_candidates_by_view` a no-op while
looking repaired. Measured on an 84-candidate HEAVY_IDP snapshot at pick 1.01: **0 candidates fell
back to `{position}`**, set sizes `{1: 73, 2: 11}`. Running both rules in one process over the same
candidate tuple:

```
  view LB   pre-repair  12  post-repair  23  newly visible 11: Will Anderson, Byron Young,
                                             Andrew Van Ginkel, Nik Bonitto, T.J. Watt, ...
  view DL   pre-repair  12  post-repair  12  newly visible 0
  view DB   pre-repair  12  post-repair  12  newly visible 0
```

T.J. Watt appears in the LB view, which is the finding's own example. Non-vacuous and uneven — the
shape a real repair has. (`probe_cf3_eligibility_and_views.py`.)

### 5. MEDIUM — `D-F2`'s own restraint test fails: `dead_names()` now reports **0**, which is the figure the finding was raised to discredit

**File / identifier:** `prose_names.HISTORICAL_MARKERS` (the four markers added in this range) and
`prose_names.SELF_REFERENTIAL`

**What it claims.** The comment justifying the four new markers (`replac`, `there is no`,
`needs no`, `no separate`):

> This is completing the vocabulary for an existing idiom, **not growing it until the report reads
> zero** — the distinction this module's docstring draws, and the reason **the report still stands
> at four rather than nought** after they were added.

And `TRIAGE_V4` on why D-F2 blocks: *"the instrument certifies '0 dead names' **at the freeze**.
The v3 freeze record already quotes that zero and it is wrong."*

**What the code does.** `prose_names.dead_names()` on the freeze candidate returns `{}` — **zero**.
The "four" the comment names are exactly the four that `SELF_REFERENTIAL`, added in the same
change, suppresses: `PANEL_ONLY`, `TheConstructionIsStrandedOnPurposeTests`,
`ValidatedFlagIsUnconditional` and `disarmed`, all four inside `prose_names.py` /
`test_prose_names.py`. So the two halves of one change cancel, and the instrument once again
certifies the zero D-F2 was raised against — by a different route, with nothing in the range
recording that the number went back to zero.

**The substance is sound; the sentence is not.** The three names D-F2 found behind the old shield
are `fgmiss_0_19`, `test_KNOWN_SENSITIVITY_the_round_boundary_is_decided_by_float_noise` and
`test_the_forfeit_depth_and_the_take_probability_table_stay_coupled`. All three sit in prose that
is genuinely historical — `"There is no \`fgmiss_0_19\`"` (`player_universe.py`), `"REPLACES
\`test_…\`, which …"` (`test_draft_strategy.py` ×2) — so the four markers really are completing an
existing idiom, not papering over rot. The defect is the stated evidence for that restraint: the
number offered as proof the vocabulary was not grown until the report read zero is contradicted by
the report, which reads zero. `#133`.

**How established.** `evidence/blind_pass_v4/probes/probe_df2_prose_shield_scope.py` plus a
runtime-only swap of `HISTORICAL_MARKERS` (no file edited; `git status --short` clean throughout):

```
shipped                     : dead_names() = 0  []
without the 4 new markers   : dead_names() = 3  ['fgmiss_0_19',
                              'test_KNOWN_SENSITIVITY_the_round_boundary_is_decided_by_float_noise',
                              'test_the_forfeit_depth_and_the_take_probability_table_stay_coupled']
restored                    : dead_names() = 0

names the SELF_REFERENTIAL exclusion suppresses: 4
  `PANEL_ONLY`, `TheConstructionIsStrandedOnPurposeTests`,
  `ValidatedFlagIsUnconditional`, `disarmed`
```

---

### 6. LOW–MEDIUM — "Paragraphs cut exactly that" overstates: the bare-`was` class survives at paragraph scope

**File / identifier:** `prose_names.dead_names` / `_paragraph_around`

**What it claims.** "MEASURED at the v4 pass: of 1,446 prose blocks naming something, 651 (45.0%)
were never examined at all … and 177 of the shielded blocks carried no marker other than 'was'. …
The 45% over-shielding was almost entirely DOCSTRINGS … **Paragraphs cut exactly that.**"

**What the code does.** Paragraph scoping cuts roughly half the available over-shield and leaves
the named class intact. Measured over the same corpus, excluding the two `SELF_REFERENTIAL` files,
with the module's own `is_history` / `_paragraph_around`:

| scope | name occurrences shielded (of 2,832) | naming blocks with ≥1 name shielded (of 1,538) |
|---|---|---|
| block (pre-repair) | 1,818 (64.2%) | 728 (47.3%) |
| **paragraph (shipped)** | **1,291 (45.6%)** | **620 (40.3%)** |
| sentence | 824 (29.1%) | — |

467 name occurrences are shielded by a marker in the paragraph but not in the sentence naming the
name, and **245 of them are shielded by nothing but a bare "was"/"were"** (a further 39 by nothing
but `arm`, the marker this module's own docstring records as its leakiest). Examples:

```
app.py:1769            `count`, `value`   -- shielded by "was", different sentence
assertion_floors.py:1  `return`, `DISABLERS`, `drops`  -- module docstring, "was" in another
                                                          paragraph-mate sentence
basis_semantics.py:1   `partial`, `rule_floor`
```

This is deliberately **not** reported as a request to narrow to sentence scope: the change's own
reasoning for choosing the paragraph (`ValidatedFlagIsUnconditional`, whose next sentence carries
the marker) is sound, and the mandate's caution about two readers that should stay separate
applies. The defect is the claim's scope: the mechanism the comment names as *the* defect — "one
bare 'was' in an unrelated sentence shielded every name beside it" — is still live on 245 name
occurrences, and the write-up says it was cut exactly.

(Module docstrings specifically: 229 name something; block scope shielded 208 (91%), paragraph
scope still shields ≥1 name in 151 (66%), and only 78 have every name examined. I could not
reproduce the write-up's 1,446 / 499 denominators with `prose_blocks()` + `ast.get_docstring`; mine
are 1,566 naming blocks and 229 module docstrings. **Unverified** which definition produces theirs.)

---

### 7. LOW — inside the consolidated `team_count`, the seats rule normalises roster ids and the picks rule does not

**File / identifier:** `league_config.team_count_with_basis` vs `draft_room.team_slots_filled`

**What it claims.** `team_count`'s docstring: "ONE derivation, in a stated order of authority".
B-F6's comment: "ONE RULE about what a rosterless pick means, in both places (`#126`)". The new
test asserts the census and the count "still read the same history differently" is closed.

**What the code does.** The seats rule coerces (`{str(seat) for seat in seats if seat is not
None}`); the picks rule does not (`{p.get("roster_id") for p in picks if … is not None}`).
`team_slots_filled` keys on `str(pick.get("roster_id"))`. So a history mixing `0` and `"0"` — and
Sleeper's own `roster_id` is an integer, while several app paths stringify it — is **two teams** to
`team_count` and **one roster** to `team_slots_filled`:

```
roster_id 0 vs '0' : team_slots_filled keys = ['0'] (len 1)   team_count = 2   DISAGREE
```

Low because `TEAM_BASIS_DECLARED` outranks the picks rule whenever `total_rosters` is present, so
production boards rarely reach it; and over-counting `num_teams` cannot trip the
foreign-roster-universe guard (which fires on `len(filled) > num_teams`). But it is the same
`#126` split the repair claims to have closed, one rule inward.

**How established.** `evidence/blind_pass_v4/probes/probe_bf6_rosterless_agreement.py`.

---

### 8. LOW — the B-F6 agreement test pins a fixture coincidence, not an invariant

**File / identifier:**
`test_one_league_one_team_count.ARosterlessPickBelongsToNoRosterTests.test_the_two_functions_agree_on_what_a_rosterless_pick_MEANS`

It asserts `len(team_slots_filled(picks, …)) == team_count(picks=picks)` with the message "the
census and the count still read the same history differently". That equality is not a property of
the two functions: `team_slots_filled` also skips any pick whose player the pool cannot resolve to
an eligible position, which `team_count` counts. Measured:

```
a roster whose only pick is a player the pool does not know
   team_slots_filled keys = ['1'] (len 1)   team_count = 2   DISAGREE
```

So the test passes on its own two-pick fixture and would fail for a reason that has nothing to do
with rosterless picks. The repair it guards **is** sound and was verified separately: the phantom
`"None"` roster is gone, `remaining_starter_demand` no longer raises on the mixed history, and a
genuinely foreign history (two real rosters, one team) is still refused with `ValueError`.

---

### 9. LOW — the `ABSENT_FIGURE` "ONE HOME" claim is not kept, and the absence check is string equality on the mark

**File / identifier:** `pick_synthesis.ABSENT_FIGURE` / `pick_synthesis.presentable_text` /
`draft_history_ui.ABSENT`

The repair's claim: *"ONE HOME (`#126`). This was a literal here and `pick_synthesis.
presentable_text` could not read it … Bound from the boundary module rather than spelled twice."*
`app.py` was rebound. `draft_history_ui.ABSENT = "—"` — the other Python surface that calls
`presentable_text`, and the one whose docstring says "the same one the Draft Room's cards use" —
remains an independently-spelled literal. `presentable_text`'s new absence check is
`rendered == ABSENT_FIGURE`, i.e. string equality against the mark, so the replay surface's
absence detection works only because two hand-spelled literals happen to be the same codepoint
today. Verified identical (`'—' == '—'` → True), so this is **currently inert**; it is a #126
claim not kept rather than a live defect.

**Verified sound in the same pass:** the repair's own mechanism fires. `survival_is_presentable()`
is `False` on the freeze candidate, so `withheld_fields()` is non-empty
(`{expected_value_of_waiting, opportunity_cost, survival_probability}`) — the guard is not
vacuous — and `design_system.figure(None)` → `None` → `_figure` → `"—"`, so:

```
presentable_text('opportunity_cost', '—')    -> '—'        (absence wins, as claimed)
presentable_text('opportunity_cost', '0.0')  -> 'withheld' (a measured zero is still withheld)
presentable_text('opportunity_cost', '12.3') -> 'withheld'
```

---

### 10. LOW — the UI arm of the round-arithmetic check uses the instrument the same module rejects five lines earlier

**File / identifier:**
`test_one_league_one_team_count.NoModuleSpellsItsOwnTeamCountTests.test_the_UI_surface_does_not_spell_the_round_arithmetic_either`

Its sibling `test_nothing_but_league_config_spells_the_round_arithmetic` carries the reasoning
explicitly: *"READ AS CODE, NOT AS TEXT. A substring scan … reported offenders that were prose
about the fix. `ast` sees only the arithmetic."* The UI arm then asserts
`assertNotIn('// settings["teams"] + 1', ui_source.text())` — a substring. The same arithmetic
spelled `// settings['teams'] + 1`, or against a local (`// teams + 1`), passes. `ui_source.units()`
returns per-module source, so an `ast.parse` per unit was available, as the sibling does for the
engine modules.

---

### 11. LOW — `EXPOSURE_ROSTER_PARTIAL`'s new label describes "the 0.0 shown here", which the Draft Room board does not show

**File / identifier:** `lineup_optimizer.EXPOSURE_BASIS_LABELS[EXPOSURE_ROSTER_PARTIAL]` and
`draft_board_ui`'s focus-sentence block

The new label reads "… and the exposure it measured is NOT the 0.0 shown here", on the stated
ground that "`score_row` prices `depth_exposure` only under MEASURED, so what a person actually
reads beside this label is 0.0". The first half is confirmed — `score_row` sets
`depth_exposure_value = 0.0` for every non-`EXPOSURE_MEASURED` basis. The claim holds on
`pick_debate._depth_term`, which prints `" + depth_exposure +0.0, which is NOT a measurement:
<label>"`. It does **not** hold on the board the Draft Room renders: the only consumer of
`depthBasisLabels` is inside

```js
if (num(c.depthExposure) && c.depthExposure > 0) { … termBasisLabel("depthBasisLabels", …) … }
```

so at `depthExposure == 0.0` neither the number nor the label is emitted at all. (That gate is
itself the `#187` shape — `> 0` cannot distinguish a measured zero from an absence — but it is
**pre-existing**, not introduced by this range.) The narrowed claim is true of one of the two
surfaces that read this table.

---

## Attacked and found sound (continued)

### `D-F4` — the qualified floor key really does close the collision

Built the collision the repair describes and netted it out so only the per-method level could
catch it: two classes in one module both defining `test_same_name`, the **first** twin losing an
`assertEqual` while `Second.test_other` gains one, so the module total is 4 before and 4 after.

```
by_method keys: 'First.test_same_name' {'assertEqual': 2}
                'Second.test_same_name' {'assertEqual': 1}
                'Second.test_other' {'assertIn': 1}
module TOTAL asserts before/after: 4 / 4
drops() reports: ['test_twins.py: First.test_same_name self.assertEqual 2 -> 1']
VERDICT: COLLISION CLOSED
```

`ASSERTION_FLOORS.json` was regenerated with qualified keys (`test_screen_context.py`: 66 of 66
qualified). Scanning the real tree for shapes the qualified key does not disambiguate: no test
method lives in a nested class, none lives outside its class's `body`, and the only duplicated
class name in any `test_*.py` is `test_version_boundary.py:_Merger` (a fixture, not a test class).

**One gap worth a line, not a finding in itself:** `test_assertion_floors.py` contains no fixture
with two classes sharing a test name. Every module it writes is a single `class T`, and the diff's
change to that file is only re-keying `test_a` → `T.test_a` — which passes under any scheme that
includes a class name, correct or not. The collision this ratchet was repaired to close is not
exercised by the ratchet's own tests. (`probe_df4_floor_key_collision.py` is the missing case.)

### `D-F3` — the self-comparing shield test was genuinely fixed

`_weak_exempt_blocks` now iterates `prose_names.prose_blocks()` instead of raw file text, so
`QUOTED_VALUE` can no longer match a constant's own assignment line and compare it with itself, and
a new `test_the_comparison_ACTUALLY_REACHES_a_prose_quotation` counts comparisons that reach
`getattr` rather than matches — which is the guard whose absence let 18 of 19 be tautologies. The
replacement docstring states its own thin reach (2 checkable quotations) rather than claiming the
old "all 18".

### `E-F5`'s exception arm, and `D-F5`'s widened guard

The exception arm does warn (see finding 1). `D-F5`'s `or "CAPTURE_PATH" in src` module-wide escape
is genuinely removed, so a module that both defines a literal capture path and mentions
`rdb.CAPTURE_PATH` is no longer skipped whole.

### 12. MEDIUM — `A-F1`'s narrowed claim is true, and the wide version is still asserted in two other places, one of them owner-facing

**Files / identifiers:** `draft_room`'s `availability_factor`/`health_penatly` seam comment
(narrowed — correct), versus `test_one_fact_two_paths_one_answer`'s **module docstring** and
`OWNER_DECISIONS_PENDING.md`'s D8 section (both still wide).

**The narrowed claim is sound.** `draft_room` now says "THE TWO PATHS AGREE EXACTLY **AT A FULL
SLATE** (`gp == SEASON_GAMES`)". Measured, the gap at `gp == SEASON_GAMES` is exactly zero for every
priced designation, and the test method was correctly renamed and re-derived from `pu.SEASON_GAMES`
rather than the literal `17.0`:

```
NARROWED CLAIM -- exact agreement at gp == SEASON_GAMES:
   Doubtful   gap = +0.0000000000  HOLDS
   IR         gap = -0.0000000000  HOLDS
   Out        gap = -0.0000000000  HOLDS
   PUP        gap = -0.0000000000  HOLDS
```

**But the wide version survives in two places the repair did not touch.**

1. `test_one_fact_two_paths_one_answer.py`'s **module docstring**: *"THE CHECK THAT SAYS THE
   DERIVATION IS RIGHT AND NOT MERELY TIDIER -- the two paths now agree EXACTLY"*, followed by
   *"gp known — points cut to 13/17"*. The `13/17` is the gp=17 arm specifically. The module whose
   own method was renamed `…_AT_A_FULL_SLATE` to scope this claim still states it unscoped twelve
   lines above, so the module contradicts itself.
2. `OWNER_DECISIONS_PENDING.md` (D8 section): *"**The check that says the derivation is right rather
   than merely tidier: the two paths now agree exactly.**"* followed by a table with `13/17` and
   *"Measured, both arms in one process: gap **0.000** at every designation and projection tested."*
   This is an owner-facing document and `#292` says the record wins.

**Input on which the wide version is false.** `gp = 16`, the value the A-F1 finding says the feed
reports for most IR players. At 173 projected points the two paths differ by **8.27** universal-value
points for IR and PUP, **10.18** for `Out`; at `gp = 13` the haircut path stops cutting entirely
(`availability_factor` → 1.0) and the gap is **40.71**. In fairness, `draft_room`'s own scoped
comment reports the worst case on the real capture as 2.25 points (Jordyn Tyson), which is a smaller
number because real projections at those rows are smaller — the two are not in conflict; what is in
conflict is "gap 0.000 at every designation and projection tested".

**How established.** `evidence/blind_pass_v4/probes/probe_af1_two_paths_scope.py`, which reproduces
the module's own two-path helper and sweeps `gp`. (It also shows `Doubtful` returning
`unrecognised_designation` from `availability_factor` at every `gp` — that is `A-F4`, which
`TRIAGE_V4` records as deliberately not repaired, so it is consistent with the record, not a new
finding.)

---

### 13. LOW — the test added for the new health sentence exercises only the one cause for which it is true

**File / identifier:**
`test_the_discount_arrives_with_its_cause.test_a_designation_this_engine_does_NOT_price_says_so`

The new test asserts the third branch fires with `injury_status="Questionable"`,
`availability_basis=pu.IMMATERIAL`, `risk_adj=0.0`. `Questionable` is cause **B** —
`HEALTH_DISCOUNT_RATE` has no rate for it — which is the only one of the three fall-through causes
the sentence correctly describes (see finding 3). Causes C and D, where the sentence is false about
a designation the engine prices at −0.2353, are not exercised. The sibling fix in the same file is
the right shape — `test_a_designation_priced_by_the_PENALTY_says_the_discount_is_in_the_value` now
supplies `risk_adj=-10.0` because, as its own new comment says, the fixture previously omitted the
quantity the sentence is about — and the same reasoning applied one step further would have caught
this.

### 14. LOW — `invariant_confirmation`'s "four quantities, one pair per branch" is two quantities counted twice

**File / identifier:** `invariant_confirmation.main`'s fixture-binds guard and
`_FINGERPRINT_SCRIPT`

**What it claims.**

> Widening it to both backstops left the SAME hole one axis over — both censuses were checked on
> the default board while two arms mutated the upside branch — **so it is now four quantities, one
> pair per branch. A guard that covers three of four gives false confidence about the fourth.**

**What the code does.** The fixture now builds both boards, which is the necessary half of the
repair and it is correct. But `fills_required_slot` and `cannot_be_fielded` are produced by
`feasibility_first` and `unfieldable_last`, neither of which reads the mode — so both censuses are
identical on the two branches **by construction**. Measured, running the module's own
`_FINGERPRINT_SCRIPT` verbatim:

```
217c138c…  619 964 131   427c4001…  619 964 131
ARG mode= auto    EMITTED mode= balanced   priced= 478
ARG mode= upside  EMITTED mode= upside     priced= 478
```

Two different digests — so a mutation of either branch's sort does move the fingerprint, which is
the real content of the repair — and **the same `619 / 964 / 131` twice**. The second pair restates
the first; it cannot fail while the first passes. The guard is two quantities, not four, and the
"three of four" hazard the comment names is not one this guard can be in.

**Also worth noting, though it is pinned elsewhere:** the loop is
`for mode in ("auto", "upside")` while the guard labels the pair `("balanced", "upside")`. The
upside arm is forced; the balanced arm is **assumed**, since `compute_draft_board` resolves
`mode="auto"` to upside whenever no priced row carries a positive `_vor`. Measured, it holds today
(`EMITTED mode= balanced` above) and nothing in `invariant_confirmation` itself asserts it.

**CORRECTION TO MY OWN FIRST READING, recorded rather than quietly dropped.** I initially filed the
consequence as "if the pool ever flipped, both arms would build the upside board and the guard would
pass". That is wrong, and the thing that makes it wrong is in the range:
`test_invariant_confirmation_anchors.AVerdictIsOnlyAFactAboutTheSuite…` now carries
`test_the_two_branches_are_DIFFERENT_boards`, which asserts `parts[0] != parts[4]` with the message
"the balanced and upside boards fingerprint identically, so a mutation to the upside sort cannot
change anything the harness measures". A both-arms-upside flip fails the suite. What remains is only
the descriptive defect: the comment's count of independent quantities is wrong. `#133`, nothing more.

**How established.** `evidence/blind_pass_v4/probes/probe_invariant_fixture_branches.py`, which runs
the module's own fixture string with one added line printing each board's emitted `mode`.

---

### 15. NOTE (not a finding) — the production guard pairs with a bare `zip`, but the pairing is pinned by a test

`invariant_confirmation.main` reads

```python
boards = [parts[i:i + 4] for i in range(0, len(parts), 4)]
for branch, (_digest, feas, total, unfield) in zip(("balanced", "upside"), boards):
```

`zip` truncates, and the production guard itself never checks `len(boards) == 2`; demonstrated on
the guard's own expression, a one-board fingerprint line leaves the upside pair silently unchecked.
I was going to file that. **It is defended**: the same range added
`self.assertEqual(len(boards), 2, "the fixture no longer fingerprints both branches")` and tightened
the fingerprint regex to `^[0-9a-f]{64} \d+ \d+ \d+ [0-9a-f]{64} \d+ \d+ \d+$` in
`test_invariant_confirmation_anchors.py`, so a regression to one board fails the suite before the
guard is ever reached. Recorded as a shape to know about, not as a defect.

Genuinely cosmetic, and real: the summary line below the loop,
`print(f"reference board: {_digest[:16]} … feasibility binds on {feas} of {total} rows …")`, reads
the loop variables after the loop, so it reports the **upside** board's digest and censuses under
the name "reference board".

---

### 16. LOW (latent) — all three new eligibility call sites resurrect the raw `position` in exactly the case MANDATE 2.6 removed it, and one of them says it does not

**Files / identifiers:** `draft_room.feasibility_first._fills_a_hole`,
`pick_synthesis.build_snapshot._eligibility`, `draft_board_ui.filter_candidates_by_view._startable_at`

**What it claims.** `feasibility_first`'s new comment:

> The primary bucket remains the FALLBACK, for a candidate the pool has no record of: **that is the
> same degradation `player_eligible_positions` already applies**, and an empty eligibility set must
> not silently promote everybody.

**What the code does.** It is not the same degradation. `player_universe.
player_eligible_positions` already applies a primary-bucket fallback, and its own docstring states
exactly when it must not:

> TWO EMPTY SETS THAT MEAN DIFFERENT THINGS. … `fantasy_positions` PRESENT and containing nothing
> startable is an ANSWER — Sleeper saying this player is not startable anywhere — and resurrecting
> the raw `position` overrides it with the very field `#172` says not to trust. Measured on the
> committed capture, this is ONE row of 6,595: Bradley Sowell, `position: TE`,
> `fantasy_positions: ["OL"]`.

All three new sites test `not eligible` / `or`, which cannot tell that empty **answer** from a
missing record — even though each already tested for the missing record separately
(`info = players_db.get(...)`; `eligible = player_eligible_positions(info) if info else None`). So
the `or` arm catches both, and for the `#172` row it reinstates `{position}`. Fed that row
directly:

```
1269  Bradley Sowell  position='TE'  fantasy_positions=['OL']  -> player_eligible_positions set()

site 1  feasibility_first : open slot TE, _feasible = [0]  -> PROMOTED for the TE hole
site 2  _eligibility      : eligible_positions written onto the snapshot = {'TE'}
site 3  the TE view       : shows the row  -> RESURRECTED the raw position
```

**Why LOW, and the measurement that makes it LOW.** The row is filtered out of the pool before any
board is built. Censused over the universe production receives:

```
raw capture rows                                     : 6595, of which startable NOWHERE: 1
build_players_db_from_capture rows                   : 6594, of which startable NOWHERE: 0
raw rows with `fantasy_positions` ABSENT or empty    : 0
```

So on this universe the `or {position}` arm cannot fire for a row that is in `players_db` at all —
every admitted row has a non-empty eligibility set — and the fallback the comment describes ("a
candidate the pool has no record of") is served entirely by the `if info else None` test that
precedes it. This is a latent breach of the same shape `compute_draft_board`'s own `#112` comment
calls out: "A latent breach, not a live one — which is exactly the kind that survives a green
suite." It becomes live the moment the pool admission widens or a second `OL`-style row arrives.

**And a `#126` observation in its own right:** "every position this man can be started at, falling
back to his primary bucket" is now spelled in **three** places, all three added in this range, by a
repair whose stated purpose was that "the two halves of one comparison read two different
vocabularies". They are not byte-identical either — `_eligibility` returns `frozenset()` when
`row["position"]` is missing while `_fills_a_hole` returns `{None}` — though no row in this universe
reaches that difference.

**How established.** `evidence/blind_pass_v4/probes/probe_bf4_cf3_resurrect_the_raw_position.py`,
with the census derived from `FANTASY_POSITIONS` rather than hand-listed.

---

## The suite on the freeze candidate

`python3 -m unittest discover -v`, clean tree at `7984b1d`, whole run redirected to a file and
grepped (not `| tail`):

```
Ran 4128 tests in 1221.133s
FAILED (failures=1, skipped=2, expected failures=1)
FAIL: test_doc_index_is_not_stale (test_doc_index.TheIndexMatchesTheTree)
      AssertionError: 1 != 0 : DOC_INDEX.md is stale -- run `python3 doc_index.py`
```

**That one failure is mine, not the candidate's.** I created
`evidence/blind_pass_v4/INDEPENDENT_REVIEW_REPAIRS.md` while the run was in flight, which is the
hazard `engine-measurement` warns about ("never run a full background suite across a tree you are
mutating"). Checked rather than assumed: a fresh `git worktree` at `7984b1d` runs
`test_doc_index` 10 tests, **OK**, printing `DOC_INDEX.md current`. So the freeze candidate's suite
is green apart from the expected failure, with two honest fixture skips (a thin-bpa trajectory
subject and a projection-only contested row, both of which say so).

### `D-F1` — `assertion_execution` really could not reach a verdict, and now can

Verified by calling both forms rather than by reading the diff. `store_io.read(path, default)` takes
a **required** `default`, so the pre-range one-argument call raised, was swallowed by the bare
`except Exception`, and the two paths degraded silently:

```
pre-range form   store_io.read(path)      -> TypeError: read() missing 1 required
                                            positional argument: 'default'
repaired form    store_io.read(path, {})  -> keys ['_comment', 'silent_tests'],
                                            silent_tests n = 14
```

So `--check` printed "this check is holding NOTHING" and returned 2 on every invocation, and
`--write` reset `existing` to `{}` and dropped every reason already recorded. After the repair the
record reads back with its 14 entries. (I did not run `--check` end to end — it executes the suite
and exceeded a 2-minute budget — so the verification here is of the seam, not of the exit code.)

### `D-F5` — the module-wide escape is gone, and the guard is thin but not vacuous

`test_modules_gate_on_the_harness_constant_rather_than_a_literal_path` no longer skips a module for
mentioning `CAPTURE_PATH`, and `test_battery_pricing_path.py`'s hand-written literal is now
`rdb.CAPTURE_PATH`. Checked that the guard still has something to look at, since a zero over an
empty population is the failure this repo names: **2** test modules' source contains
`sleeper_capture.json` and reach the AST check (`test_241_format_axes.py`,
`test_slot_vocabulary.py`), both mentioning it only in a docstring, so the offender list is
legitimately empty rather than unreachable. Thin, and nothing asserts the subject count.

### `run_roster_proof_capacity_cut`'s corrected citation is correct

`remaining_league_picks` → `remaining_draft_capacity`: the function exists at
`draft_room.py:1287` and does call `draftable_slots_per_team`, so the renamed citation points at
real code.

### 17. LOW–MEDIUM — `ONE_QUESTION_TWO_READERS.md` says "All five repaired in this cycle", and two of the five still have a reader that disagrees

**File:** `evidence/semantic_duplication/ONE_QUESTION_TWO_READERS.md` (installed by `7984b1d`)

The write-up is a good document and its method section is the right method. Three of its claims do
not survive checking, and each is already established above:

1. **`B-F6` — "what does a pick with no roster mean"** is listed as repaired. The two readers now
   agree on `None`, which was the finding. They still disagree on type: `team_count`'s picks rule
   does not coerce while its own seats rule does and `team_slots_filled` does, so `roster_id` `0`
   and `"0"` are two teams to one and one roster to the other (finding 7, measured).

2. **`B-F4` / `C-F3` — "which positions can this candidate start at"** is listed as repaired, and
   the question is now asked of eligibility on both sides, which was the finding. But the composed
   rule — eligibility with a primary-bucket fallback — is now spelled in **three** places, all
   three added by this repair, and all three apply the fallback in the one case
   `player_eligible_positions`' docstring says it must not (finding 16, latent on this universe).
   Step 3 of the document's own method is "decide which reader OWNS the question, and make the
   others call it"; the owning reader exists and all three sites wrap it in a locally re-expressed
   fallback instead.

3. **`D10` is held up as the exemplar** — "found by the test written for D10 itself, which asked
   what the solver means by 'starting slot' instead of asserting a literal … and it would have
   failed on the first run". True of the left-hand number. The same message carries a second number,
   `parsed_starting + len(starters)`, pinned against no authority at all, and it is wrong whenever
   an unrecognised starting label repeats (finding 2, measured: "declares 10" where
   `starting_slots` says 12). The document's transferable lesson — "an expectation derived from the
   authority catches a disagreement between readers; a literal expectation cannot" — is correct, and
   the exemplar it cites applies it to one of the two numbers it reports.

Filed against the document rather than the code because `#292` makes the record the thing that wins,
and this is the file a future reader will consult to decide the class is closed.

### 18. MEDIUM — `risk_adj` has five states, not three, and the other two are the ones that reach a person wrongly

**File / identifier:** `pick_debate._format_candidate`'s health branch

This is finding 3 completed. The repair's comment says "THREE states, because there are three
(`#187`)". `risk_adj` arriving on a `CandidateSnapshot` has five, and the two the enumeration omits
are **absence** states — exactly what `#187` governs:

| state | how it arises | which branch takes it | correct? |
|---|---|---|---|
| a real negative | charged | "already inside the value" | yes |
| `0.0`, basis `RULE_FLOOR` | already in the projection | "already REMOVED" | yes |
| `0.0`, no rate for the status | `#191` immaterial | "does not price it" | yes |
| **`NaN`** | `score_row`: `if pd.isna(bpa): risk_adj = float("nan")` — an **unpriced row** | **"already inside the value"** | **no** |
| **`None`** | **upside mode never emits the column**, by design | **"does not price it"** | **no** |

`_charged = risk_adj is not None and risk_adj != 0.0` puts `NaN` in the charged branch (`NaN is not
None` and `NaN != 0.0` are both true) and `None` in the not-priced branch.

**Both measured on real boards, both person-facing.**

*The `NaN` state.* 75 rows of a 970-row balanced 12T_ppr board are unpriced and carry a designation
(46 `IR`, 20 `Questionable`, 4 `NA`, 2 `PUP`, 2 `Sus`, 1 `DNR`), `risk_adj` NaN on every one.
`pick_synthesis`' own `#183` comment says such a row reaches this formatter. What it is told:

```
Will Mallory  IR  risk_adj=nan  universal_value=nan
  -> IR -- a health discount is already inside the universal value below
```

There is no universal value. (Not a regression — the pre-repair `availability_basis` branch said
the same thing for these rows — but the repair re-derived the sentence from `risk_adj` and declared
the enumeration complete while that authority distinguishes this case perfectly well.)

*The `None` / upside state.* On an upside board the column is absent for every row, so every
designation falls into the not-priced branch. `draft_room` is explicit that this is by design:
"the per-position decomposition terms (time_horizon_adj, risk_adj) stay absent because
`upside_score` genuinely never computes them". That makes "NO discount was applied" true and
"**this engine does not price this designation**" false — the absence is a property of the mode, not
of the designation. The upside board carries 70 rows the engine does price (63 `IR`, 7 `PUP`).
At pick 1.01 the narrowed 48 happened to be all `Questionable`, where the sentence is accidentally
true; on a drained board it is not:

```
drained UPSIDE board, snapshot at 13.01, 6 candidates:
  Jayden Higgins  IR  risk_adj=None  rate=-0.23529411764705882
    -> IR -- NO discount was applied for it -- this engine does not price this designation,
            so his value below is the value of a fully fit player
```

**How established.** `evidence/blind_pass_v4/probes/probe_risk_adj_the_fourth_and_fifth_states.py`.
The picks draining the board are built in production's shape
(`{pick_no, round, roster_id, player_id}`) so round detection and mode resolution are not silently
changed by the input, and `mode` is passed explicitly rather than left to `auto`.

### 19. HIGH — four of the twelve repairs are defended by no test at all: reverting each one leaves the suite green

**Method.** In a separate `git worktree` at `7984b1d`, revert exactly one repair, run the test
modules that ought to notice, restore with `git checkout --`, assert the tracked tree is clean,
repeat. Every arm under `PYTHONDONTWRITEBYTECODE=1` with `__pycache__` cleared first, because a
length-preserving edit inside one mtime second otherwise serves the previous bytecode. Control arm
(clean tree, the union of every module named below): **OK**, so a FAILED in an arm is attributable
to the revert. Probe:
`evidence/blind_pass_v4/probes/probe_mutation_do_tests_defend_the_repairs.py`; raw output:
`evidence/blind_pass_v4/probes/mutation_pass_output.txt`.

| repair | reverted in | verdict |
|---|---|---|
| `A-F2` `health_penalty` returns 0.0 for an absent projection | `draft_room.py` | **DEFENDED** (2 failures) |
| `B-F4` `feasibility_first` reads eligibility on the candidate side | `draft_room.py` | **DEFENDED** (1) |
| `B-F6` a rosterless pick creates no phantom roster | `draft_room.py` | **DEFENDED** (2 + 1 error) |
| `C-F3` `filter_candidates_by_view` filters on eligibility | `draft_board_ui.py` | **DEFENDED** (2) |
| **`C-F3` `eligible_positions` is POPULATED by `build_snapshot`** | `pick_synthesis.py` | **UNDEFENDED — OK** |
| `E-F5` a failed season fetch returns a refusal string | `sleeper_client.py` | **DEFENDED** (1) |
| **`A-F5` the Draft Room puts the draft's seats on the league dict** | `app.py` | **UNDEFENDED — OK** |
| **`A-F1` `presentable_text` checks absence before withholding** | `pick_synthesis.py` | **UNDEFENDED — OK** |
| `D10` `ambiguities` splits the alarm into three bands | `league_config.py` | **DEFENDED** (3) |
| **`D-F2` the history shield is paragraph-scoped, not block-scoped** | `prose_names.py` | **UNDEFENDED — OK** |
| `D-F4` the per-method floor key is qualified `Class.method` | `assertion_floors.py` | **DEFENDED** (4) |
| `A-F5` `_round_being_decided` routes through `team_count`/`round_of` | `pick_synthesis.py` | **DEFENDED** (2) |

**The four undefended ones, and why each matters more than a missing test usually does.**

**(a) `C-F3`: nothing checks that `build_snapshot` populates `eligible_positions`.** Replacing
`_eligibility`'s body with `frozenset()` leaves `test_one_eligibility_vocabulary_everywhere`,
`test_pick_synthesis`, `test_snapshot_identity_boundary` and `test_draft_board_ui` all green. The
UI half **is** defended — the view filter's tests fail when it is reverted — because
`EligibilityCrossesTheSnapshotBoundaryTests` builds its `CandidateSnapshot`s **by hand** with
`eligible_positions=frozenset({"DL", "LB"})`. So the suite pins "a view filters on the field" and
never "production fills the field", which is the finding C-F3 actually was: *"eligibility never
crosses the snapshot boundary"*. Reverted, every board silently returns to showing a dual-eligible
man in exactly one view, and the test named `test_the_snapshot_carries_eligibility_at_all` still
passes, because it checks `dataclasses.fields` — that the field **exists**, not that it is filled.

**(b) `A-F5`: nothing checks that the Draft Room puts the seats on the league dict.** Deleting the
single line `league_config.PICK_ORDER_KEY: round_1_order,` from `app.py` leaves
`test_one_league_one_team_count`, `test_ui_source`, `test_three_derivations_of_one_number`,
`test_mock_draft_wiring` and `test_live_board_pricing` green. `PICK_ORDER_KEY` appears in `app.py`
exactly once, at that line. The new module's tests all call `lc.team_count` with a hand-built
league carrying the key — they prove the function reads it, never that the one production caller
writes it. The module's own docstring says the whole point is "THE SEATS NOW TRAVEL ON THE LEAGUE
DICT … rather than through four call layers, because every layer that has to forward them is a
layer that can forget to"; the layer that must not forget is the only one unpinned. And the idiom
was in hand: the very next test in the same class checks the UI through `ui_source.text()`.

**(c) `A-F1`: nothing checks the new absence-before-withholding order.** Removing
`if rendered is None or rendered == ABSENT_FIGURE: return rendered` leaves
`test_withheld_propagation`, `test_survival_absence_contract`, `test_absence_survives_consumers`,
`test_pick_synthesis` and `test_dock_absence_contract` green. The assertion that looks like the
guard is `assertEqual("—", ps.presentable_text("universal_value", "—"))` — and `universal_value` is
**not** in `withheld_fields()` (`{expected_value_of_waiting, opportunity_cost,
survival_probability}`), so that line never reaches the withheld branch and passes either way. The
repair's own measured case — a **withheld** field holding an absent value, 48 of 48 candidates at
the user's last pick — has no assertion anywhere. This is the mandate's third defect class exactly:
a literal expectation that the fixture and the defect both satisfy.

**(d) `D-F2`: nothing checks that the history shield is paragraph-scoped.** Putting
`is_history(text)` back in place of `is_history(_paragraph_around(text, match.start()))` leaves
`test_prose_names` and `test_source_scan` green. So the scope repair — the thing `TRIAGE_V4` says
blocks the freeze, because "the instrument certifies '0 dead names' at the freeze … and it is
wrong" — can be undone without a word. Read with finding 5 (`dead_names()` now reports 0 anyway),
the Tier 0 instrument's repair is both unprotected and back at the number it was raised against.

**Three of the four are the same shape:** the test exercises the consumer against a hand-built
input and never the producer that fills it. That is the shape `engine-measurement` names as the
dominant fixture error in this repository, applied to tests rather than to probes.

---

*(review in progress — a mutation pass over the repairs is still running; its results and the summary are appended below)*
