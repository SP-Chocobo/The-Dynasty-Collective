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
**These are pass claims, not measurements I made**, except for the eleven I verified myself, which
are marked **[VERIFIED]** below. One pass — the SKEPTIC — was given the five HIGH claims with
authorship stripped and told to break them; it narrowed two and corrected the derivation behind a
third.

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

## 0.3 Every substantive view is traced in its empty state

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

## 0.4 `assertion_floors` cannot see any silent way a test stops running

Missed: `@unittest.skip`, `@expectedFailure`, `self.skipTest()`, `return` before the assertion,
`if False:`, a loop over `[]`, `try/except AssertionError: pass`, a class that stops inheriting
`TestCase`. Nothing in CI counts skips, and one test skips on the committed baseline today.

**Repair:** count skips and expected failures in CI and ratchet them; extend the scanner; correct the
docstring's stated limits, which omit all of the above.

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

## 0.7 Report fields that do not mean their names

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

## 1.6 The candidate matcher returns the highest-ranked name *mentioned*

`pick_debate.py:626-629`: after an exact-match miss it returns the first candidate in board order
whose name appears anywhere in the RECOMMENDATION text. Measured against a real board —
`"RECOMMENDATION: Nico Collins over CeeDee Lamb"` → **CeeDee Lamb**, with Collins as "best
alternative" and the argument for Collins printed underneath. `"Not CeeDee Lamb"` → CeeDee Lamb. A
one-character fragment `"D"` → CeeDee Lamb. The docstring claims it "returns None (never a guess) if
nothing lines up"; it guesses whenever two things line up.

**Repair:** require an unambiguous match — fail to `None` when two candidate names appear — and let
the existing `recommended=None` path handle it.

---

# TIER 2 — silent wrong answers from inputs that arrive from outside

The pattern one pass named, and it is the right frame for this whole tier:

> The absence contract is honoured rigorously INSIDE the board, but the two inputs that arrive from
> outside — the season-projection sum and the league config — cross into it with no companion stating
> their completeness, and the one companion that does exist is written to disk and read by nothing
> that prices.

## 2.1 A partial projection sum is priced as complete — *three lenses* **[VERIFIED]**

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

## 2.3 Identity and reach into the stat line

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

## 2.4 Sources that vanish quietly

`load_all` swallows every unparsable file and keeps no record — 5 files in, 2 loaded, 3 skipped,
`is_loaded=True`, no signal. Mitigated for user uploads, not for a committed baseline file that stops
parsing after a library upgrade. `get_players` caches any truthy 200 body, so an error-shaped JSON
poisons the daily cache and every page load then raises for 24 hours with no in-app refetch. A 200
with a non-JSON body escapes as `JSONDecodeError`, not `SleeperAPIError`, so the methods documented
to fail soft do not.

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

## 3.3 Constants sized for a scale that no longer exists

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

## 3.4 Terms that are dead or describe the wrong roster

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

# TIER 4 — one concept, two homes (`#126`)

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
- **It does not treat a pass claim as a measurement.** Eleven items are marked **[VERIFIED]** because
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

## Still unverified by me, and what that means for the repair

- **2.1's QB collapse.** I verified the root cause (no pricing consumer reads
  `season_projection_coverage`; `grep -c` in `app.py` returns 0) but not the 39-of-40 reordering,
  which needs the weekly lines re-summed over a partial week set. The mechanism is confirmed and the
  repair — refuse to price from an incomplete sum — does not depend on the magnitude.
- **0.1's −23.66 / −15.94 K and DEF shift.** I verified the wiring gap itself, which is what the
  repair fixes.
- **0.2's 482-test result** was produced by a dedicated pass with a baseline arm; I verified the
  committed evidence holds exactly two `"caught"` results against a harness defining three mutations.
- **0.3, 0.4, 0.7's duplicate_arms, 2.4, 3.1's ordering claim, 3.3, and all of Tier 4** rest on pass
  measurement. Each carries its own method in the verbatim reports.
