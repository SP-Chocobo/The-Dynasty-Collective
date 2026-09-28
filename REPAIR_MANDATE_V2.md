# v2 repair mandate — what the audit found, and the order it has to be fixed in

Built from thirteen blind adversarial passes across three waves, recorded verbatim in
`evidence/blind_pass/reports_v2/` and condensed in `evidence/blind_pass/FINDINGS_V2.md`. The freeze
(`a8d1627`, tag `v2-freeze`) stands: it records what was certified when it was cut, and this audit
came after it. Nothing here has been repaired yet.

> **THE ORDERING IS NOT BY SEVERITY.** It is by **what must be true before the next repair can be
> verified.** Several of the most serious findings are in the apparatus that would be used to check
> every engine repair below them. Fixing the fieldability ceiling first and then "confirming" it with
> a battery whose K/DEF pricing is wrong, whose mutations all survive, and whose trace records an
> empty page, would produce a green result that means nothing. That is the failure this repository
> has already had once, when a battery certified 36 arms with `#30` dormant and said so in a field
> nobody read.

## What the audit is, so the numbers are not over-read

Thirteen passes, each given one lens and denied every document holding prior conclusions
(`FREEZE_RECORD*`, `FREEZE_CHECKLIST`, `POST_AUDIT_PLAN`, `DOC_INDEX`, and five `evidence/`
directories). All thirteen gave a contamination statement; none reported opening a forbidden path.
**These are pass claims, not measurements I made**, except where I verified them myself. I then went
back and verified every item: **all twenty-one original items carry a [VERIFIED] marker below**,
several qualified
(`[VERIFIED: root cause only]`, `[VERIFIED, in part]`) where I reached the mechanism but not the
magnitude. The qualifiers are load-bearing — read them, not just the word. One pass — the SKEPTIC — was
given the five HIGH claims with authorship stripped and told to break them; it narrowed two and
corrected the derivation behind a third.

Compiling the coverage map at the end of this document then showed five clusters of pass findings with
no home in those twenty-one. Rather than drop them, they are now items **0.8, 0.9, 1.7, 2.5 and 2.6** —
twenty-six in total. They carry no `[VERIFIED]` marker: each is a faithful consolidation of the passes'
own measurements, cited in the map, and the mechanism of every one is visible in the source. They were
added last, so they are the least adjudicated part of this document — treat them accordingly.

Three protocol failures are recorded in `FINDINGS_V2.md`, two of them mine: my commit subjects
leaked a conclusion to a wave-1 pass, and I interrupted a pass mid-probe and cost it a verdict
(later recovered). The third is structural: `isolation: "worktree"` handed every pass a stale branch,
and all thirteen caught it themselves.

---

# TIER 0 — the apparatus, first, because everything below is validated with it

## 0.1 The format battery drafts every arm with `#30`'s streaming floor inert **[VERIFIED]**

`run_draft_battery.py:470-473` calls `run_battery(...)` with `sleeper_projections` and
`sleeper_basis` only. `weekly_projections_from_capture` appears in that file exactly once — at its
own `def` on line 94 — and is never called there. `run_vds_battery.py:130` does call it.

**This is a hole in my own repair.** When I wired `#30` at `04bccb5` I fixed the loader and wired
only the VDS battery. Measured by the pass: with the weekly lines versus without, **every one of 38
K rows moves −23.66 universal value and every one of 32 DEF rows −15.94**, no other position moving;
the best kicker goes from overall rank 75 to rank 114.

So every format-battery statement about K/DEF draft position, K/DEF roster counts,
`first_round_taken("K")`, or "0 structural findings on `12T_ppr_K_DEF`" describes a board that ranks
kickers about forty slots higher than the shipped engine does. `run_smoke_seats` and
`run_roster_proof` omit it too.

**Repair:** pass `weekly_projections` from `main` in all three drivers, **and** add
`streaming_floor_exercised` to the format battery's `universe` block — the VDS battery has that key,
and it is the field whose `false` value caught this exact defect there. A test that pins only the two
sleeper keywords is why this survived; pin the third.

## 0.2 The suite does not defend the two backstops, and the committed evidence says it does **[VERIFIED]**

`evidence/invariant_confirmation.json` holds exactly two results, both `"caught"`. The harness
defines **three** mutations; the third has no verdict. A dedicated pass applied each mutation with
the harness's own `apply_mutation` and ran 482 tests over fifteen board- and backstop-touching
modules with the self-referential anchors module excluded and no `--failfast`:

| tree | result |
|---|---|
| baseline | OK |
| `feasibility_first never binds` | **OK — SURVIVED** |
| `board order ignores feasibility` | **OK — SURVIVED** |
| `board order ignores fieldability` | **OK — SURVIVED** |

Both recorded "caught" verdicts came from `test_invariant_confirmation_anchors.py` failing on its own
missing anchor text under `--failfast`, before any engine behaviour ran.

Why nothing catches them: `test_feasibility_backstop.py` calls `feasibility_first` directly and then
does **its own** sort; `test_unfieldable_backstop.py` tests `pick_synthesis._board_order` on plain
dicts; **`test_draft_room.py` has 98 tests and zero references to `_feasible`,
`fills_required_slot`, `_unfieldable` or `cannot_be_fielded`**; and **nothing asserts on the board's
own row order.**

**Repair:** exclude the anchors module from the scored run (or score it separately), give the third
mutation a verdict, and add the missing assertion — a test that reads `compute_draft_board`'s row
order directly. Do this **before** Tier 3, since two Tier 3 items change that ordering.

## 0.3 Every substantive view is traced in its empty state **[VERIFIED]**

`render_trace.py` seeds the snapshot with `"rosters": [], "users": []`, so the Draft Room's 117
recorded calls are a shared sidebar prefix plus `st.info("No roster found for your account in this
league yet…")` — **zero board, pick-synthesis or mock-draft calls.** The non-vacuity guards are
satisfied by the shared prefix and a radio that renders before the roster guard. Break the live board
and the trace is byte-identical.

Related: `RENDER_TRACE.json` records a freshness grade computed from `datetime.now()`, has already
churned once inside an unrelated commit, and **goes red on 2026-11-19** with no UI change.

**Repair:** seed a roster into the trace fixture so the substantive branches render; blur or exclude
the freshness string. An instrument that emits a scheduled false diff trains reviewers to regenerate
without looking.

## 0.4 `assertion_floors` cannot see any silent way a test stops running **[VERIFIED: four vectors]**

Missed: `@unittest.skip`, `@expectedFailure`, `self.skipTest()`, `return` before the assertion,
`if False:`, a loop over `[]`, `try/except AssertionError: pass`, a class that stops inheriting
`TestCase`. Nothing in CI counts skips, and one test skips on the committed baseline today.

**Repair:** count skips and expected failures in CI and ratchet them; extend the scanner; correct the
docstring's stated limits, which omit all of the above.

**Scope this one fairly.** The ratchet is *not* holding nothing in general: a damaged or empty
`ASSERTION_FLOORS.json` is already caught — `--check` refuses to report success over it, and
`test_assertion_floors.py` pins that refusal. (The suite prints that refusal's message on every run,
which is the test working, not a failure.) What is missed is narrower and more specific: the scanner
counts `def test_` occurrences and `assert*` call sites **from source text**, so any change that stops
a test *running* while leaving its text in place is invisible. That is the repair's target.

## 0.5 The battery's chairs never exercise the valuation a human is shown **[VERIFIED, in part]**

Chairs run `mode="auto"`; `app.py` passes no `mode=` at any call site, so the human board is always
`balanced`. On every arm past 14 rounds, picks from round 15 on use upside scoring — which zeroes
every team-specific term. The "mode axis" arm is 14 rounds, so `auto` never reaches the switch there
and it is byte-identical to its sibling. **No format-battery arm exercises the human-turn valuation
past round 14.**

Also: `CAPTURE_owner_league` — "the league this system is actually used on" — is built from
`league_shape`, which carries no `settings`, so `is_dynasty` is False and `time_horizon_adj` is never
applied to it.

**Repair:** run the matrix in `balanced` (or add balanced arms at full length) and carry `settings`
into the capture arms. Until then, no owner-league arm supports a claim about multi-year valuation.

## 0.6 The battery's universe is outside the hashed input set — *two lenses* **[VERIFIED]**

`baseline_manifest.DECLARED_INPUT_DIRS` covers `data/baseline` and `data/projections/_global`;
`data/fixtures/sleeper_capture.json` is hashed by nothing, and `data/player_aliases.json`
(gitignored, consulted in matching) can reroute a player with the manifest still reporting "input set
matches".

**Repair:** declare both. This is small and it protects every number below.

## 0.7 Report fields that do not mean their names **[VERIFIED: `draftable_rounds` only]**

- `roster_shape_axes["draftable_rounds"]` is the **starting-slot count**. **[VERIFIED]** I measure
  **35 of 36 arms** disagreeing with the arm's own `draft_rounds` (the pass said 36; it is 35). The
  coverage axis publishes `{8:19, 9:12, 10:3, 11:1, 13:1}` while the arms draft
  `{8:1, 14:18, 15:12, 16:2, 18:1, 25:1, 26:1}`.
- `duplicate_arms` misses identical arms on a **resumed** run, because `produced_at_commit` is
  stamped before the fingerprint is taken — so `independent_formats` is overstated exactly when
  `--resume` is used, which is the documented normal path.
- The VDS report sums findings over **inert** arms and uses the full strategy count as denominator
  regardless of how many ran, so a mid-run file — the file a reader usually holds — misclassifies.
- Trajectory provenance (`mode`, `opponent_noise`, `priced_from`, seed) never reaches any report;
  `audit_trajectory` copies only the label.
- `picks_by_mode` and `upside_from_round` are computed from the round rule regardless of
  `upside_rule`, so the crossing arm's trajectory states a split it did not produce.

**Repair:** rename or recompute `draftable_rounds`; fingerprint before stamping; denominate by arms
actually run and exclude inert arms; copy the trajectory config into the report.


## 0.8 Prose that asserts properties the code does not have, and the instruments that were supposed to catch it

Two lenses arrived here independently. Pass B collected docstrings and comments asserting behaviour the
code beneath them does not implement; pass C then measured the instrument meant to police exactly that:
**`prose_names.py`'s history shield exempts most of what it claims to check.** The stale claims found
include `compute_draft_board`'s reference to an `app.py` mode toggle that does not exist, the
`reference_values` docstring's "identical contract" with a call that raises, and `assertion_floors`'
own stated limits (0.4).

**Repair:** narrow the shield to what it can actually defend, then fix the claims it then surfaces.
Do it in Tier 0 — every tier below is read through this prose.

## 0.9 Instruments that count instead of check, and graders that price off the production path

Six findings, one shape: an instrument reports a number that is not about the thing its name says.

- **Tests that pass while executing zero `unittest` assertions** — measured by running the 274
  statically-flagged tests under an instrumented `TestCase`.
- **`test_audit_cadence.py`** checks the CI file by substring count, so a commented-out step counts.
- **`quantity_readers.py`** rests on hand-maintained module lists, one naming a file that does not exist.
- **`suite_taxonomy`** contract markers admit `gap #1`.
- **`draft_counterfactual._full_board`** prices vendor-only with no `sleeper_projections`,
  `sleeper_basis`, `weekly_projections` or `upside_rule`, while `engine_tav` is read off the trajectory
  snapshot — so `regret_vs_bpa` is a difference of two pricings whenever the trajectory came from the
  battery. Its consumers are internally consistent only because both sides use the vendor
  reconstruction, i.e. a universe production never prices.
- **`realized_ruler.DEFAULT_WEEKS = range(1, 19)`** scores week 18, which most leagues do not.
- **The battery fixture reader** returns `{}` for a capture without season projections while
  documenting raise-on-missing.

**Repair:** these are the ruler, not the engine. Fix them before reading any number they produce.

---

# TIER 1 — production defects that crash, or put a false number in front of a person

## 1.1 A `TypeError` in the shipped Mock Draft **[VERIFIED]**

`app.py:4921` calls `draft_room.simulate_opponent_picks(...)` with
`['pool_scope', 'sleeper_basis', 'sleeper_projections', 'weekly_projections']`. The function accepts
`['league', 'merger', 'my_roster_id', 'num_teams', 'pick_order', 'picks', 'players_db', 'pool_scope',
'sleeper_basis', 'sleeper_projections']`. **`weekly_projections` is not a parameter — that call
raises at runtime.** Confirmed by AST over `app.py` against `inspect.signature`.

The harness pass flagged it as *outside its lens* while chasing something else. It is the most
concrete defect in the audit: not a mispricing, an exception.

**Repair:** add the parameter and thread it to the board, or drop the argument. Then ask why no test
and no render trace reaches that path — 0.3 is the answer, and it is why this is Tier 1 and not
Tier 0.

## 1.2 The recommendation panel renders the withheld family to a person — *three lenses* **[VERIFIED]**

`SURVIVAL_IS_CALIBRATED = False`; `withheld_fields()` names **three** quantities —
`survival_probability`, `opportunity_cost`, `expected_value_of_waiting` — under the rule *"A quantity
withheld from presentation must not reach a person, on any surface, under any name, as itself or as a
delta of itself."* `grep withheld_fields\|SURVIVAL_IS_CALIBRATED app.py` returns **nothing**, and
`_render_pick_metrics` renders all three, with `app.py:5660` printing "Survival: NN%" for the
runner-up. On a real board **48 of 48 candidates carry a non-None survival**.

Five other surfaces honour the rule and `test_withheld_propagation.py` covers those five.
`invariant_registry.py` already concedes the census "cannot, by construction, see a surface that
never asks at all."

Reachability: only after a debate runs **with a configured LLM provider**. With a key, it is live.
Also `draft_board_ui.py:788` prints `c.survival` without the gate that lines 811-816 honour —
unreachable today only because `decision_regime` never returns "decisive" while uncalibrated.

**Repair:** make the panel ask `withheld_fields()`; add it to `test_withheld_propagation`'s surface
list; gate line 788.

## 1.3 `positional_forfeits` sums a conditional hazard as an expected count **[VERIFIED]**

`position_pace_probability` advances the expected cumulative count with each hypothetical intervening
pick while `actual_now` is read off a fixed list, so the deficit grows every step. Defensible inside
`estimate_survival`'s per-player product; **not** defensible summed across the gap and called the
expected number taken.

| state | gap | QB `expected_taken` | convention's own bound | actually taken | all-position total |
|---|---|---|---|---|---|
| 1.01 | 22 | **15.54** | 8.92 | 5 | **26.15 / 22 picks** |
| 2.12 | 14 | **10.28** | 5.67 | 6 | **16.76 / 14 picks** |

The total exceeds the picks in the gap. **The `#206` docstring on that very function lists
"expected_taken exceeds the picks available" as the arithmetic impossibility it repaired** — the
pace max-in re-broke it. Survival is withheld; `positional_forfeit`, `position_next_turn_value` and
`acting_now_value` are **not**, and reach the board and the sentence "Waiting on him costs about 58.5
universal-value points by your next turn."

**Repair:** bound the summed pace mass by the convention's own increment over the gap, or compute the
expectation from the hazards properly. **Not** a per-position cap — that is a constant, and `#56`
forbids it.

## 1.4 The Live Draft Room never fetches picks on its own **[VERIFIED]**

`get_draft_picks` has **exactly one call site** in `app.py` (line 5327), behind the `↻ Refresh Picks`
button. A live draft in round 4 opens showing **"ON THE CLOCK — 1.0X"**, every drafted player still a
candidate, "0 pick(s) made", and nothing saying the picks were never pulled. A completed draft renders
as live round 1. It recurs on every league switch, because the picks cache is correctly cleared and
never refilled.

**Repair:** fetch on load, or show a "picks as of" stamp and refuse to label the board live without
one. The second is smaller and removes the false claim even if the fetch stays manual.

## 1.5 The Debate chip's context is displayed and never sent — *two lenses* **[VERIFIED]**

`debate_attached_context` is written at `app.py:1484`, read at `app.py:6531`, and that read is its
only consumer. `build_context(snapshot, roster_table, player_universe, question, conversation_window)`
has no parameter for it. The panel prints *"💬 Considering: On the clock for pick 2.03"* with a "Full
evidence" expander, then answers with no board, no candidates and no pick position — it can name a
player already drafted. The dock's own comment says the line should read as *"Debate already
understands what I was looking at."*

**Repair:** pass it, or remove the claim. Passing it is the one the comment intends.

## 1.6 The candidate matcher returns the highest-ranked name *mentioned* **[VERIFIED]**

`pick_debate.py:626-629`: after an exact-match miss it returns the first candidate in board order
whose name appears anywhere in the RECOMMENDATION text. Measured against a real board —
`"RECOMMENDATION: Nico Collins over CeeDee Lamb"` → **CeeDee Lamb**, with Collins as "best
alternative" and the argument for Collins printed underneath. `"Not CeeDee Lamb"` → CeeDee Lamb. A
one-character fragment `"D"` → CeeDee Lamb. The docstring claims it "returns None (never a guess) if
nothing lines up"; it guesses whenever two things line up.

**Repair:** require an unambiguous match — fail to `None` when two candidate names appear — and let
the existing `recommended=None` path handle it.


## 1.7 Context that is stale, unanchored, or unrecoverable, presented as current

Four lenses hit this from four directions, and it is one defect family: **what the person is looking at
can be older or other than what the label says, and nothing in the apparatus can tell.**

- The **staleness stamp cannot see most of the inputs that change a board**; a stale debate is presented
  as current. The snapshot and anchor caches **ignore `injury_status`, `status` and `years_exp`**, all of
  which the board reads.
- A debate result and its `previous_snapshot` **survive pool-scope and draft-picker changes** — the only
  gate is `pick_label`.
- **"WHAT CHANGED SINCE THE LAST SNAPSHOT" has no anchor**, so the user's own picks read as board movement.
- **`import_audit` results persist across league switches** under a header naming the new league, and
  `debate_attached_context` is not cleared either.
- **Failed or cut-off chairs** are reported only as a one-rerun toast while the persistent panel shows a
  clean recommendation; `CONFIDENCE` is unvalidated, and failed-chair error strings are replayed into
  conversation memory.
- **`draft_history` cannot reproduce what was shown** — write-only today.

**Repair:** one anchor, keyed on everything the board reads, cleared on every scope change. The
individual fixes are small; the reason they are one item is that repairing any one of them alone leaves
the person with the same wrong impression by a different route.

---

# TIER 2 — silent wrong answers from inputs that arrive from outside

The pattern one pass named, and it is the right frame for this whole tier:

> The absence contract is honoured rigorously INSIDE the board, but the two inputs that arrive from
> outside — the season-projection sum and the league config — cross into it with no companion stating
> their completeness, and the one companion that does exist is written to disk and read by nothing
> that prices.

## 2.1 A partial projection sum is priced as complete — *three lenses* **[VERIFIED: root cause only]**

`season_projection_coverage` is written by `sleeper_client` and read by **no module that prices**.
The only consumers are in `sleeper_import_report.py`, a CLI; `grep -c season_projection_coverage
app.py` returns **0**. `_sum_weeks` records a failed week and keeps summing; there is no retry,
backoff or spacing, so `sync_league` fires 18 back-to-back requests at an endpoint its own comments
call undocumented. `_derive_points_and_source` then promotes the truncated sum **over** the vendor's
complete total.

With weeks 10–18 failing: **39 of the top 40 rows move 3+ places**, Jayden Daniels 31 → 321
(`universal_value` 107.34 → **−38.42**), QBs clearing the startable floor **31/355 → 10/355**, and the
top ten of a **superflex** board contains **zero quarterbacks** — with `bpa_source`,
`replacement_basis` and `absence_kind` unchanged on every row.

And a failed fetch **overwrites a good snapshot**: `_write_snapshot` replaces `_latest.json`
unconditionally, so an 18-week sync becomes a 0-week one with the error buried in JSON, while the
freshness manifest reports that sync as the freshest input on the page.

**Repair, in this order:** (a) make the board refuse to price from an incomplete sum, or mark every
row that rests on one; (b) do not let a failed fetch replace a good snapshot; (c) surface coverage in
the freshness manifest. (a) is the one that stops a wrong board.

## 2.2 The league-config gate is unwired — *four lenses* **[VERIFIED]**

`ambiguities` / `confirmation_state` / `admits_decision` / `decision_config` have **zero production
callers**. Measured consequences: empty `roster_positions` → 1944 rows, **0 priced, no reason on any
row**; an unknown `OP` slot → silently ignored by the solver; `scoring_settings = None` →
byte-for-byte the vendor-only board; a two-literal-`QB` league selects the superflex rankings *file*
while pricing QBs under the 1QB regime (Josh Allen 91.03 against 170.02).

**And the gate as written would refuse legitimate leagues** — it requires `bonus_rec_te` and
`num_teams`, which the real capture league lacks, because Sleeper omits zero-valued scoring keys.

**This is not a straightforward repair and it is partly a design question — see Owner Decisions.**
What is not a design question: a board built on a config the gate would refuse should not be silently
priced.

## 2.3 Identity and reach into the stat line **[VERIFIED: the 11 defenses only]**

- **11 of 32 team defenses cannot resolve** to their transcribed row — `name_key` takes the first
  initial plus everything after the first token, so "Green Bay Packers" never matches "G Packers".
  On the vendor-only fallback they price `no_priceable_input`, including the best-projected DEF in
  the pool. **Scoped:** all 32 price on the shipped season-sum path, so this bites only in 2.1's
  degraded state — which is another reason 2.1 leads this tier.
- **The league's kicking rules cannot reach Sleeper's stat line.** There is no `fgm_50p` key, so
  5.5–8.8 projected 50+ makes per kicker (25–35% of a kicker's total, 973 points across the pool) are
  never scored, and ~3.4 misses per kicker go unpenalised. This distorts the K ordering `#30`'s floor
  is built on — so it interacts with 0.1, and both should be re-measured together.
- **One player splits into two canonical records** (`_identity_hint` is stamped per file). Mechanism
  confirmed in all 12 format hints, wrong file wins in 5 — **consequence measured at ≤0.12
  universal-value points and zero rank change.** Repair the mechanism cheaply; do not justify it with
  a cost it does not have.

## 2.4 Sources that vanish quietly **[VERIFIED]**

`load_all` swallows every unparsable file and keeps no record — 5 files in, 2 loaded, 3 skipped,
`is_loaded=True`, no signal. Mitigated for user uploads, not for a committed baseline file that stops
parsing after a library upgrade. `get_players` caches any truthy 200 body, so an error-shaped JSON
poisons the daily cache and every page load then raises for 24 hours with no in-app refetch. A 200
with a non-JSON body escapes as `JSONDecodeError`, not `SleeperAPIError`, so the methods documented
to fail soft do not.


## 2.5 The absence contract breaks at the snapshot boundary (`#187`)

`#187` says `None` never becomes `0.0`. At the snapshot boundary it does:

- **`need_bonus` is fabricated as `0.0` in upside mode**, while every other absent term crosses as
  `None`.
- **`rival_premium` is a "measured" `0.0` on every candidate** in upside mode, and it is not a
  measurement.
- **`diff_snapshots` silently drops measured↔unmeasured transitions** — the one comparison that exists
  to catch this cannot see it.
- The persisted **`draft_history` record and the board payload ship numbers without the companions the
  snapshot's own contract says they require.**
- **Injury status never crosses the boundary at all**, and the Skeptic prompt then asserts the engine
  does not know it — which is true only because of this gap.
- **`build_context` truncates silently**, and the Draft Room seed hands the panel undefined units.

**Repair:** this is a contract, so it is repaired as one — at the boundary, not at seven call sites.
Note the ordering dependency: 1.2 (rendering a withheld family) and 2.5 are the same boundary seen from
the two sides, and 1.2's repair should land first so the boundary has a stated policy to enforce.

## 2.6 Multi-eligible players are counted by their primary label (`#172`)

**Roster fill is counted by primary label**, so `need_bonus` and league-wide starter demand mis-read
every multi-eligible player; `roster_diagnostics` solves lineups with a single label, contradicting the
battery's own legality audit **on the same roster**; and there are **three different eligibility
readers that disagree on real rows.** `#172` already says eligibility comes from `fantasy_positions`,
not the primary `position` — this is that rule, unenforced in the places that count rather than the
places that value.

**Repair:** one eligibility reader (Tier 4 removes the other two), then count against it. 3.2's joint
bound depends on this being right, so it lands first.

---

# TIER 3 — engine-internal, real, and narrower than they first read

Every item here was narrowed or refined by a later pass. **Do not repair from the wave-1 text.**

## 3.1 `time_horizon_adj` subtracts percentiles over different populations **[VERIFIED]**

`_season_proj_pct` is a percentile over **all priced rows**; `_proj3yr_pct` over **only rows carrying
`proj_3yr`**. I measured the populations: **481 priced, 259 with `proj_3yr`, 222 without** (median
15.9 points, so they sit at the bottom) — against a comment directly above asserting *"zero rows in
the real baseline carry a points projection WITHOUT a proj_3yr alongside it"*, which is no longer
true and was probably falsified by `#180` routing K/DEF/IDP through league-scored points.

Bias: **−3.710** production against **−0.021** matched, 91 of 259 rows flipping sign.

**But the SKEPTIC ran it through `build_snapshot` with the backstops and `narrow_candidates`' re-sort
and the top candidate was identical in 16 of 16 states.** Candidates move at most 5 places. The bias
among actual candidates is a third of the population figure, because a rank-percentile shift is
smallest at the top — which is where picks come from.

**Repair:** compute both percentiles over the same population. It is a small, clearly-correct change
whose measured effect on picks is zero — which makes it safe, and also means **no repair here should
be justified by a claim that it changes recommendations.**

## 3.2 The fieldability ceiling — and the bound the fix must use **[VERIFIED]**

The exemption is real: a flex-reachable position gets no ceiling at all, and a real draft left six of
twelve rosters holding 6–7 IDP against a derivable bound of 2, with every guard silent.

**The bound wave 1 proposed is valid but too loose to catch the case that motivates the fix.** The
SKEPTIC verified against the production optimizer: a roster at **exactly** `slots_reachable(P) + 1`
for DL, LB *and* DB holds six and the optimizer starts **one**. The tight derivable bound is the
**joint** one:

> Σ over the group of `held` ≤ |slots admitting any member of the group| + 1

Seven rosters exceed the joint bound against six for the per-position form. **And it is not
IDP-specific** — one roster holds **7 TE** against a bound of 3, three hold 7 WR against 4.

**Repair:** implement the joint bound. Consolidating after wave 1 would have shipped the per-position
form and missed the case.

## 3.3 Constants sized for a scale that no longer exists **[VERIFIED: the scale and the constants]**

`_scale_vor_to_bpa` is now the identity; the `bpa` span is **−328.6 to +227.6**. The bounded additive
terms were sized for a 0–100 scale: `RISK_ADJ` −18 is now "18 projected points" (10.4% of a
173-point player, 4.5% of a 400-point one); `depth_exposure` converts trade value into a unit that no
longer exists; `test_need_bonus_cannot_flip_a_large_universal_value_gap` compares the top and bottom
priced rows (gap ≈556 against a cap of 12), so the invariant it guards is **vacuous**.

`need_bonus` on an empty roster is a flat per-position constant carrying no roster information:
21 cross-position pairs in the opening top 60 where the higher-ranked row has the **lower**
`universal_value`.

**These are `#56` territory — a re-derivation, not a re-tuning — and re-deriving a conversion is real
work. See Owner Decisions.** The vacuous test should be fixed regardless, in Tier 0.

## 3.4 Terms that are dead or describe the wrong roster **[VERIFIED: `block_opportunity` only]**

- **`block_opportunity` has been dead since the `#206` normalisation.** Its 0.10 threshold means
  "rank-4-or-better" on the raw table; normalised over ~960 rows rank-1 is 0.025. Measured: 4,812
  take probabilities, max 0.032, **zero** above threshold, `block_opportunity` True on **0 of 369**
  candidates while `rival_premium ≥ 8` fired on 184. The flag reaches the UI as "Denies {team}…".
- **`depth_exposure` describes a roster the optimizer never saw** — rostered players with no vendor
  trade value are dropped, and every LB candidate's TAV moves 2.52 purely on whether the vendor
  priced a bench body, with the basis token claiming a full measurement either way. The displacement
  term got a `ROSTER_PARTIAL` basis for this exact hole; depth got nothing.
- **`need_bonus` is fabricated as `0.0`** at the snapshot boundary in upside mode while the other four
  absent team terms cross as `None` with explicit "never 0.0" comments — then printed to the chairs as
  a measured term beside two honestly-withheld ones.

---

# TIER 4 — one concept, two homes (`#126`) **[VERIFIED: every second home exists]**

Found incidentally by five separate lenses before a dedicated sweep confirmed them. Each is small;
together they are the mechanism by which the tiers above drifted apart.

**Disagree on today's data:** `draftable_rounds` (0.7); the battery's raw-position roster shape versus
the engine's bucket (167 of 6595 players); `draft_board_ui`'s hand-listed flex views, which omit two
of five flex types and affect one captured league today.

**Agree today, with the input that splits them:** three "is this a starting slot" predicates; three
team-count readers; three round-number derivations; two superflex predicates; three injury-status
vocabularies (a PUP player with a season line but no `gp` is priced fully fit where an identical IR
player takes −18); two literal copies of the transcribed-file set.

**Repair:** each is a delete-and-import. Do them **after** Tiers 0–2, because several of them are
load-bearing for repairs above and changing a vocabulary under an unrepaired instrument is how the
next drift starts.

**What I verified, site by site.** Each row is the second home, named, at today's HEAD:

| vocabulary | the homes | state today |
|---|---|---|
| flex slot types | `draft_board_ui._POSITION_VIEW_ORDER` hand-lists `FLEX, SUPER_FLEX, IDP_FLEX`; the core modules spell **six**: `FLEX, SUPER_FLEX, SUPERFLEX, IDP_FLEX, REC_FLEX, WRRB_FLEX` | **omits `REC_FLEX` and `WRRB_FLEX`** — exactly the two the pass named, and the two `draft_board_ui.py:382` names in its own comment. A fourth hand-list, `app.FA_POSITION_FILTERS`, omits them too |
| the superflex slot's spelling | `SUPER_FLEX` (14× `draft_room`, 4× `draft_board_ui`) vs `SUPERFLEX` (1× `app.FA_POSITION_FILTERS`) | the odd one out is a display label, so it is harmless **today** — and it is the shape the next reader copies |
| starting-slot predicate | `league_config.starting_slots` / `draftable_slots`; `draft_room.starter_slot_counts` / `dedicated_slot_counts` / `draftable_slots_per_team`; `draft_battery.unfilled_starting_slots` | **three homes**, as claimed |
| team count | `app.py:5351` `len(round_1_order)`; `app.py:5383` `league.get("total_rosters")`; `draft_room.py:3691` `league.get("total_rosters") or len({roster_id…}) or 1` | **three derivations**, only one of which has a fallback |
| round number | `app.py:5374` `target_index // num_teams + 1`; `draft_room.py:3704` `len(demand_source) // num_teams + 1`; `draft_room.py:4442` `idx // num_teams + 1` | **three**, agreeing today |
| transcribed-file set | `draft_room.KDST_SEEDED_SOURCE_FILES`; `data_merger._TRANSCRIBED_SOURCE_FILES` | **byte-identical today** — `{sleeper_dst_projections.csv, sleeper_kicker_projections.csv}` in both. The input that splits them is a third transcribed file |
| injury status | `player_universe.IMMATERIAL_INJURY_STATUSES = {Questionable}`; `app.INJURY_OK_STATUSES = (Questionable, Doubtful)`; `draft_room.RISK_ADJ = {IR: −18, Out: −10, Doubtful: −5}` | **they already disagree.** `app` paints `Doubtful` amber as an OK status while the engine docks it 5 points for the same player on the same screen. This one is not "agrees today" — correct its placement above |


---

# OWNER DECISIONS — not repairs (`#184`)

1. **The upside growth term is inert.** Positive on 2.9% of board rows, argmax unchanged in all six
   formats, positive on 2 of 87 real picks — and it loses to `sharp_auto` on `proj_3yr`, the horizon
   it targets, in all six formats. The work is a **derived** percentile-to-points conversion; the ±10
   clamp was borrowed from `time_horizon_adj` precisely because `#56` forbids calibrating one. *(task #36)*
2. **The upside board's flat region** and its `player_id` tiebreak. *(task #37)*
3. **Whether to wire the league-config gate at all**, given it would refuse every real league as
   written. The repair is not "call it" — it is deciding what the gate should demand.
4. **`RANK_TAKE_PROBABILITY` against observed behaviour.** The repo's own data: 276 measured human
   picks, rank-1 share **0.022** against a model rank-1 of 0.55; calibration Brier 0.161 against a
   constant-base-rate 0.145, `beats_constant: false`. Survival is already withheld on this basis; the
   question is whether the model should be re-derived or retired.
5. **The positional-run detector** fired at 29% of real states and was anti-predictive for QB and RB
   on the one real draft available. Its live effect is +6 necessity points.
6. **Constant re-derivation under the current `bpa` scale** (3.3) — how much of this to do at all.

---

# WHAT THIS MANDATE DOES NOT DO

- **It does not revoke the freeze.** `v2-freeze` at `a8d1627` records what was certified when it was
  cut; this audit came after. Repairs go on a new line, and a v3 freeze is a later question.
- **It does not tune toward any finding.** Several items below Tier 2 have a real mechanism and a
  measured consequence near zero (3.1's pick-identical result, 2.3's ≤0.12 points). Those get fixed
  because they are wrong, not because they cost something, and the repair note should say so.
- **It does not treat a pass claim as a measurement.** Every item is marked **[VERIFIED]** because
  I checked them myself. The rest are claims with evidence attached, and the verbatim reports are in
  `evidence/blind_pass/reports_v2/` so the next reader can check my condensation rather than trust it.

## Corrections I owe, recorded here rather than buried

1. **"Vintage-matched" was wrong.** The capture is `2026-09-07`, the weekly lines `2026-09-22` —
   fifteen days apart, nothing compares `captured_at`. Corrected in place at `GATE_FOR_VDS.md`.
2. **My `#30` wiring fix did half the job** (0.1). I wired the VDS battery and left the format
   battery inert, and then wrote a measurement-skill lesson telling a future reader to check the
   exercise flags — while leaving the other battery without one.
3. **`draftable_rounds` mismatches on 35 of 36 arms, not 36.** One arm agrees.


---

# VERIFICATION LOG — what I checked myself, and two errors of my own

Run against the frozen engine with the real capture, from the repository root. **Two of my own
measurements initially appeared to contradict a pass, and both were my error, not theirs.** They are
recorded here because the engine-measurement skill's whole warning is that the failure mode is not a
crash but a plausible number about something else — and I produced two.

## Confirmed exactly

| item | what I measured |
|---|---|
| **3.2 joint bound** | `optimize_lineup` on `QB RB RB WR WR TE FLEX IDP_FLEX` with 2 DL + 2 LB + 2 DB held: **starts 1 of 6**. Per-position `slots_reachable+1` is **2 for each of DL, LB, DB — none exceeded**; the joint bound is also 2 and IS exceeded. The repair must use the joint form. |
| **1.3 forfeit** | On `12T_ppr_SF` at 1.01, gap 22: **QB `expected_taken` = 15.54**, total across positions **26.15 against 22 picks** — exceeds the gap. QB forfeit 63.1. |
| **2.2 gate** | Two non-test hits for `ambiguities`/`admits_decision`/`decision_config`/`confirmation_state`, and **both are prose in comments**, not calls. Zero production callers. |
| **2.3 defenses** | On the **vendor-only fallback**: 32 DEF rows, **11 unpriced — GB, KC, LAC, LAR, LV, NE, NO, NYG, NYJ, SF, TB**, the exact eleven named. On the shipped season-sum path: **0 unpriced**. Scoping confirmed in both directions. |
| **3.4 dead gate** | Real 1.01 board: 72 candidates, all carrying a take probability, **max 0.0250** against a threshold of **0.10**, **n ≥ threshold = 0**, `block_opportunity` **True on 0 of 72** while `rival_premium ≥ 8` fired on 24. |
| **0.5 owner league** | `CAPTURE_owner_league` keys are `draft_rounds, roster_positions, scoring_settings, total_rosters` — **`settings` is absent, so `is_dynasty` is False**. Note the asymmetry the pass did not mention: `CAPTURE_fourth_and_forever` DOES carry `settings={'type': 2}` and is dynasty. The defect is specific to the owner-league arm. |
| **0.6 manifest** | `DECLARED_INPUT_DIRS = ('data/baseline', 'data/projections/_global')` — the capture is not declared. |
| **0.3 empty-state trace** | `render_trace.py`'s seed line is literally `"rosters": [], "users": [],`. `RENDER_TRACE.json` holds **620 recorded strings**, of which **3 are empty-state guards** (`Couldn't find a roster owned by this user in this league.`, `No teams found in this league's synced data.`, `Nothing rostered here yet.`) and **0 are board, candidate or pick-synthesis strings**. The calendar dependency is present as recorded text: `[🏈 Matchup] st.markdown(str:<span class="status-bad">⚠️ Data Freshness: Aging</span>…)`. |
| **0.4 ratchet blindness** | Mutated the first `test_` method of a scratch copy of `test_league_config.py` four ways and re-scanned. `@unittest.skip('flaky on CI')`, `@unittest.expectedFailure`, a leading `self.skipTest('no')`, and a leading `return` each produced a scan **byte-identical to baseline** — `test_methods` 19→19, `asserts` dict unchanged. The reason is structural: `scan_module` returns `{test_methods, asserts, by_method}` counted from **source text**, and none of the four vectors removes a `def test_` or an `assert` call. (A fifth mutation, an empty `if False:` body, did change the scan — to `test_methods=0`, i.e. a parse failure, which is a crash signature, not detection.) |
| **2.4 silent sources** | `DataMerger` has **no attribute whose name mentions skip, fail, or unreadable** — there is nowhere for a swallowed file to be recorded. `get_players` caches on a bare `if players:` → **True**; it validates the body's shape → **False**. |
| **3.3 the dead scale** | Priced n=481: `bpa` runs **−328.6 to +227.6, span 556.2**; `_scale_vor_to_bpa` is the **identity**. Against that span: `RISK_ADJ = {'IR': -18.0, 'Out': -10.0, 'Doubtful': -5.0}`, `NEED_BONUS_MAX = 12.0`, `DEPTH_EXPOSURE_MAX = 12.0`, `TIME_HORIZON_CLAMP = (-10.0, 10.0)` — all sized against `TRADE_VALUE_SCALE_MAX = 100.0`, a scale the board no longer uses. |

## My two errors

1. **I first measured the forfeit on a non-superflex format and got a clean result.** On
   `12T_ppr_K_DEF` the total was 12.03 against a 22-pick gap — no impossibility, QB `expected_taken`
   0.83, QB forfeit 3.09. I briefly had that as a contradiction of the pass. It is not: the pass
   stated plainly that the defect rides on superflex QB pace, and `12T_ppr_K_DEF` is not superflex.
   Re-run on `12T_ppr_SF`, the pass's numbers reproduce to the digit (15.54). **Testing a
   format-specific claim on the wrong format is not a refutation.**

2. **I first counted defense resolution through `merge_player` and got 30 of 32.** The pass and the
   SKEPTIC both counted through `_resolve` and got 21 of 32. I nearly recorded that as a
   discrepancy. The question that matters is neither: it is what the **board** does. Built both ways,
   the board answers it — 0 unpriced on the shipped path, exactly 11 on the fallback. **I was
   measuring a different function than the one whose output reaches a price.**

## Added after the first pass over this log

**1.6 the candidate matcher — VERIFIED.** Driven directly against `_match_candidate` with a
three-candidate snapshot:

```
'Nico Collins over CeeDee Lamb'       -> 'CeeDee Lamb'
'Nico Collins, not CeeDee Lamb'       -> 'CeeDee Lamb'
'Not CeeDee Lamb'                     -> 'CeeDee Lamb'
'Either Nico Collins or CeeDee Lamb'  -> 'CeeDee Lamb'
'CeeDee Lamb - no wait, Nico Collins' -> 'CeeDee Lamb'
'D'                                   -> 'CeeDee Lamb'
'Nico Collins'                        -> 'Nico Collins'   (exact match, correct)
```

Its own docstring: *"returns None (never a guess) if nothing lines up"*. It guesses whenever two
things line up, and a single character is enough.

**The three injury vocabularies already disagree.** Tier 4 filed them under "agree today, with the
input that splits them." That was wrong, and it is my error, not a pass's: `app.INJURY_OK_STATUSES`
treats `Doubtful` as an OK status and paints it amber, while `draft_room.RISK_ADJ` docks the same
player 5 points, and `player_universe.IMMATERIAL_INJURY_STATUSES` holds only `Questionable`. No input
is needed to split them — they are split now, on screen, for any Doubtful player. Corrected in the
Tier 4 table.

**Marker corrections in this document.** Four headings under-stated what I had checked (0.7's
`draftable_rounds`, 1.6, 2.3's eleven defenses, 3.4's `block_opportunity`) and one over-stated it:
**2.1 is verified at the ROOT CAUSE only** — no pricing consumer reads the coverage record — not at
the 39-of-40 reordering. Corrected in place.

## Still unverified by me, and what that means for the repair

Twenty-one of twenty-one items now carry a marker. What remains unverified is never a mechanism —
it is a **magnitude** attached to a mechanism I did check, or a Tier 4 duplication confirmed by
grep rather than by execution. The repair never depends on the part I could not reach.

- **2.1's QB collapse.** Root cause verified (no pricing consumer reads `season_projection_coverage`;
  `grep -c` in `app.py` returns 0). The 39-of-40 reordering is not verified — it needs the weekly
  lines re-summed over a partial week set. The repair — refuse to price from an incomplete sum — does
  not depend on the magnitude.
- **0.1's −23.66 / −15.94 K and DEF shift.** The wiring gap itself is verified, and that is what the
  repair fixes. The size of the shift it causes is the pass's number.
- **0.2's 482-test result** came from a dedicated pass with a baseline arm. I verified the committed
  evidence holds exactly two `"caught"` results against a harness defining three mutations, and I
  reproduced all three survivals.
- **0.7's `duplicate_arms`** and **3.1's ordering claim** rest on pass measurement; both mechanisms
  are visible in the source and each pass's method is in its verbatim report.
- **Tier 4** is verified as duplication (the second home exists, and the two disagree or agree as
  stated). What is not verified is the live consequence of each one, which is the point: they are
  `#126` cleanups, not behaviour repairs.

Every number above that I did not produce myself is traceable to the pass that produced it, in
`evidence/blind_pass/reports_v2/`, unedited. Where a pass and I disagreed, my measurement is recorded
above and the pass's text is left standing — the disagreements are the most useful thing in the file.

---

# COVERAGE MAP — every numbered pass finding, and where it went

The owner's standing requirement is that nothing from the waves is quietly dropped. This table is the
audit of this document: each of the 13 passes' own numbering, mapped to the mandate item that carries
it. **Verbatim text for every row is in `evidence/blind_pass/reports_v2/`, unedited.** Where a row
lands in "not carried", the reason is stated — that is the only honest way to drop something.

| pass | finding | lands in |
|---|---|---|
| **A** valuation arithmetic | 1 `time_horizon_adj` percentiles | **3.1** |
| | 2 bounded terms on the abolished 0–100 unit | **3.3** |
| | 3 `need_bonus` flat constant reorders the board | **3.3** |
| | 4 superflex QB startable floor: vendor points applied to league-scored points | **open register `#21`**, blocked on `#50` — the floor cannot be derived while the board asserts two conventions. This audit is a second, independent reason `#50` comes first |
| | 5 two units on one number line | **3.3** |
| | 6 `mode="auto"`'s upside switch unreachable | **0.5** + **Owner Decision 1** |
| | 7 code-style opinions | not carried — the pass itself states no failure scenario |
| **B** absence & contracts | 1 withheld survival family rendered | **1.2** |
| | 2 `need_bonus` fabricated as `0.0` | **2.5** |
| | 3 `rival_premium` a "measured" `0.0` | **2.5** |
| | 4 `depth_exposure` describes a roster never solved | **3.4** |
| | 5 staleness stamp blind to most inputs | **1.7** |
| | 6 `diff_snapshots` drops measured↔unmeasured | **2.5** |
| | 7 `draft_history` numbers without companions | **2.5** |
| | 8 board payload missing two companions | **2.5** |
| | 9 prose asserting properties the code lacks | **0.8** |
| | 10 documented deliberate collapses | not carried — the pass filed these as correct and documented; I agree |
| **C** measurement apparatus | 1 empty-state render trace | **0.3** |
| | 2 `RENDER_TRACE.json` calendar dependency | **0.3** |
| | 3 both "caught" verdicts are the harness's self-test | **0.2** |
| | 4 `assertion_floors` blindness | **0.4** |
| | 5 `prose_names` shield exempts what it checks | **0.8** |
| | 6 tests passing with zero assertions | **0.9** |
| | 7 `baseline_manifest` declares two directories | **0.6** |
| | 8 `test_audit_cadence` substring count | **0.9** |
| | 9 `format_axes_exercised` blind to `mode` | **0.5** |
| | 10 `quantity_readers` hand lists, one file absent | **0.9** + Tier 4 |
| | 11 `suite_taxonomy` admits `gap #1` | **0.9** |
| **D** roster geometry | 1 no bound for shared-slot positions | **3.2** |
| | 2 roster fill counted by primary label | **2.6** |
| | 3 `league_config` blocking state unconsulted | **2.2** |
| | 4 `roster_diagnostics` single-label lineups | **2.6** |
| | 5 three eligibility readers disagree | **2.6** + Tier 4 |
| | 6 `feasibility_first` round fallback counts IR; UI supplies no round count | **1.1** + Tier 4 (round count) |
| | 7 `draftable_rounds` misnamed | **0.7** |
| **E** ingestion & identity | 1 `_identity_hint` splits one player | **2.3** |
| | 2 11 of 32 defenses cannot resolve | **2.3** |
| | 3 kicking rules cannot reach the stat line | **2.3** |
| | 4 season sums paired with 15-days-later weekly lines, called "vintage-matched" | **Corrections I owe** — withdrawn in place in `evidence/design_35/GATE_FOR_VDS.md`; the phrase was mine |
| | 5 cross-format field fill silent in `_reconcile_rows` | **2.4** |
| | 6 coverage record written and read by nobody | **2.1** |
| | 7 vendor identity lost to team drift | **2.3** |
| | 8 battery universe outside the hashed set | **0.6** |
| | 9 config gate unwired | **2.2** |
| | 10 sync season is the NFL state's, not the league's | **2.4** |
| | 11 code-style observations | not carried — no measured failure |
| **F** mutation survival | all three committed mutations survive | **0.2** |
| **G** UI state | 1 picks never fetched | **1.4** |
| | 2 caches ignore `injury_status`/`status`/`years_exp` | **1.7** |
| | 3 debate survives scope and picker changes | **1.7** |
| | 4 Debate chip context never sent | **1.5** |
| | 5 coverage recorded, no consumer | **2.1** |
| | 6 `import_audit` persists across league switch | **1.7** |
| | 7 `debate_attached_context` not cleared | **1.7** |
| | 8 `activate_league` first-sync failure silent | **2.4** |
| **H** robustness | 1 partial sum priced as complete | **2.1** |
| | 2 failed projection fetch overwrites a good snapshot | **2.4** |
| | 3 config gate wired to nothing | **2.2** |
| | 4 `load_all` swallows unparsable files | **2.4** |
| | 5 `get_players` caches an error body for 24h | **2.4** |
| | 6 non-JSON 200 escapes as `JSONDecodeError` | **2.4** |
| | 7 fixture reader returns `{}` despite documenting a raise | **0.9** |
| | 8 `replace_atomically` one temp name per PID | **2.4** |
| | 9 first activation swallows every exception | **2.4** |
| | 10 metadata strings into `float()` | **2.4** |
| **I** vocabulary | 1 two answers for "draftable rounds" | **0.7** + Tier 4 |
| | 2 third home for round count | Tier 4 |
| | 3 flex view order omits two of five | Tier 4 |
| | 4 battery roster shape counts a different position (n=167) | Tier 4 |
| | 5 two superflex predicates | Tier 4 |
| | 6 header reads `num_teams`, engine reads `total_rosters` | Tier 4 |
| | 7 three team counts behind "which round is it" | Tier 4 |
| | 8 three starting-slot predicates | Tier 4 |
| | 9 three injury vocabularies | Tier 4 — **and they already disagree**, see the correction |
| | 10 two copies of the transcribed-file set | Tier 4 |
| **J** LLM panel | 1 Debate chip context never reaches the model | **1.5** |
| | 2 `_match_candidate` substring fallback inverts "X over Y" | **1.6** |
| | 3 withheld survival family rendered | **1.2** |
| | 4 Strategist told to argue from odds it is not given | **1.2** |
| | 5 injury status never crosses the boundary | **2.5** + Tier 4 |
| | 6 failed chairs shown as a clean recommendation | **1.7** |
| | 7 "what changed" has no anchor | **1.7** |
| | 8 Prytaneum handed undefined units | **2.5** |
| | 9 silent truncations in `build_context` | **2.5** |
| | 10 `draft_history` write-only | **1.7** |
| | 11 error strings replayed into memory | **1.7** |
| **K** opponent model | 1 `positional_forfeits` sums a hazard as a count | **1.3** |
| | 2 `block_opportunity` gate unreachable | **3.4** |
| | 3 preview computes the gap on the wrong side of the turn | **1.3** — same convention, read from the wrong side; repaired together |
| | 4 run detector fires on 29%, anti-predictive | **Owner Decision 5** |
| | 5 `_full_board` prices vendor-only | **0.9** |
| | 6 survival model describes rivals the simulation lacks | **0.9** + **Owner Decision 4** |
| | 7 take-model calibration vs observed behaviour | **Owner Decision 4** |
| **L** battery harness | H1 `weekly_projections` omitted; K −23.66, DEF −15.94 | **0.1** |
| | H2 no arm exercises the human valuation past round 14 | **0.5** |
| | H3 owner league drafted as non-dynasty | **0.5** |
| | (H2's aside) `simulate_opponent_picks` `TypeError` | **1.1** |
| | M1 `duplicate_arms` blind on a resumed run | **0.7** |
| | M2 ruler and draft priced differently | **0.1** |
| | M3 trajectory provenance never reaches a report | **0.7** |
| | M4 `picks_by_mode`/`upside_from_round` false under the crossing rule | **0.7** |
| | M5 VDS fields count the control's findings | **0.7** |
| | M6 no join disclosure | **0.7** |
| | M7 `format_axes` from the current matrix | **0.7** |
| | M8 counterfactual compares two pricings | **0.9** |
| | L1 `draftable_rounds` | **0.7** |
| | L2 `tav_margin_profile` mislabelled | **0.7** |
| | L3 `DEFAULT_WEEKS` scores week 18 | **0.9** |
| **SKEPTIC** | claim 1 `time_horizon_adj` — mechanism stands, ordering overstated | **3.1**, with the qualifier |
| | claim 2 withheld quantity — stands, reachability qualifier | **1.2** |
| | claim 3 flex bound — stands, one refinement | **3.2**, using the refined joint bound |
| | claim 4 defenses — stands, scoped to the fallback | **2.3**, scoped |
| | claim 5 identity split — mechanism stands, consequence ≤0.12 pts | **2.3**, with the magnitude |

**Count:** 26 mandate items, 6 owner decisions, 1 reopened register item (`#21`/`#50`), 4 rows not
carried with the reason given, and every null result left in the verbatim reports where it belongs.

**One protocol item, closed while compiling this.** `.claude/settings.local.json` — the wave-2 deny-rule
shield — was still present **and committed to the branch**, so it was blinding every ordinary checkout,
not just the pass sessions. Deleted in the same commit as this document. The reusable template
(`.claude/blind-pass.settings.json`) stays. `#52`'s protocol already said to delete the copy when the
pass ends; this is the second time that step has been missed, so it now belongs in the skill, not in a
reader's memory.
